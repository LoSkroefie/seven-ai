"""Safe, non-destructive setup and onboarding for Seven.

The setup engine deliberately separates planning from mutation.  It never
accepts or persists API keys, never removes user data, and never pipes remote
content into a shell.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Callable, Sequence
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SETTINGS_FILE = "settings.json"
SETTINGS_FORMAT = 1
OLLAMA_DOWNLOAD_URL = "https://ollama.com/download"
MIN_MODEL_FREE_BYTES = 10 * 1024**3
RECOMMENDED_RAM_BYTES = 8 * 1024**3
_MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}$")
_VOICE_ENGINES = {"auto", "edge", "pyttsx3", "none"}
_CAMERA_MODES = {"off", "webcam", "screen", "both"}
_STARTUP_MODES = {"unchanged", "talk", "quiet", "none"}
_SECRET_FIELDS = {
    "api_key",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "private_key",
}


@dataclass(frozen=True)
class SetupOptions:
    assistant_name: str = "Seven"
    user_name: str = "User"
    workspace: Path = Path.home() / ".seven" / "workspace"
    text_model: str = "qwen2.5:7b"
    vision_model: str = "llama3.2-vision"
    voice_engine: str = "edge"
    camera_mode: str = "off"
    startup_mode: str = "unchanged"
    data_dir: Path = Path.home() / ".seven"
    ollama_url: str = "http://127.0.0.1:11434"
    install_ollama: bool = False
    pull_models: bool = False
    dry_run: bool = False
    noninteractive: bool = False


def settings_path(data_dir: Path | None = None) -> Path:
    root = Path(
        data_dir
        or os.getenv("SEVEN_DATA_DIR")
        or (Path.home() / ".seven")
    ).expanduser()
    return root / SETTINGS_FILE


def load_settings(data_dir: Path | None = None) -> dict[str, Any]:
    path = settings_path(data_dir)
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Seven settings file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"invalid Seven settings file {path}: expected an object")
    return value


def saved_environment(data_dir: Path | None = None) -> dict[str, str]:
    """Return the non-secret environment represented by saved setup choices."""
    settings = load_settings(data_dir)
    identity = settings.get("identity") or {}
    models = settings.get("models") or {}
    voice = settings.get("voice") or {}
    camera = settings.get("camera") or {}
    workspace = settings.get("workspace")
    values = {
        "SEVEN_NAME": identity.get("assistant_name"),
        "SEVEN_USER_NAME": identity.get("user_name"),
        "SEVEN_WORKSPACE": workspace,
        "OLLAMA_MODEL": models.get("text"),
        "OLLAMA_VISION_MODEL": models.get("vision"),
        "SEVEN_TTS": voice.get("engine"),
        "SEVEN_CAMERA": "1" if camera.get("mode") in {"webcam", "both"} else "0",
        "SEVEN_CAPTURE_MODE": camera.get("mode"),
    }
    return {key: str(value) for key, value in values.items() if value not in (None, "")}


def apply_saved_environment(
    data_dir: Path | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    """Apply saved non-secret defaults without overriding explicit environment."""
    target = environ if environ is not None else os.environ
    values = saved_environment(data_dir)
    for key, value in values.items():
        if key in target:
            continue
        target[key] = value
        if key == "OLLAMA_MODEL":
            # Model lifecycle must distinguish a saved setup default from a
            # real operator environment override. A benchmarked activation is
            # allowed to supersede the saved default on future restarts.
            target["SEVEN_OLLAMA_MODEL_SOURCE"] = "saved"
    return values


def _validate_name(value: str, label: str) -> str:
    value = str(value).strip()
    if not value or len(value) > 80 or any(ord(char) < 32 for char in value):
        raise ValueError(f"{label} must contain 1-80 printable characters")
    return value


def _validate_model(value: str, label: str) -> str:
    value = str(value).strip()
    if not _MODEL_NAME.fullmatch(value):
        raise ValueError(
            f"{label} must be an Ollama model name containing only "
            "letters, numbers, '.', '_', ':', '/', '+', or '-'"
        )
    return value


def validate_options(options: SetupOptions) -> SetupOptions:
    assistant_name = _validate_name(options.assistant_name, "assistant name")
    user_name = _validate_name(options.user_name, "user name")
    text_model = _validate_model(options.text_model, "text model")
    vision_model = _validate_model(options.vision_model, "vision model")
    voice_engine = str(options.voice_engine).strip().lower()
    camera_mode = str(options.camera_mode).strip().lower()
    startup_mode = str(options.startup_mode).strip().lower()
    if voice_engine not in _VOICE_ENGINES:
        raise ValueError(f"voice engine must be one of {sorted(_VOICE_ENGINES)}")
    if camera_mode not in _CAMERA_MODES:
        raise ValueError(f"camera mode must be one of {sorted(_CAMERA_MODES)}")
    if startup_mode not in _STARTUP_MODES:
        raise ValueError(f"startup mode must be one of {sorted(_STARTUP_MODES)}")

    workspace = Path(options.workspace).expanduser().resolve()
    data_dir = Path(options.data_dir).expanduser().resolve()
    parsed = urlparse(str(options.ollama_url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Ollama URL must be an absolute http:// or https:// URL")
    return SetupOptions(
        assistant_name=assistant_name,
        user_name=user_name,
        workspace=workspace,
        text_model=text_model,
        vision_model=vision_model,
        voice_engine=voice_engine,
        camera_mode=camera_mode,
        startup_mode=startup_mode,
        data_dir=data_dir,
        ollama_url=str(options.ollama_url).rstrip("/"),
        install_ollama=bool(options.install_ollama),
        pull_models=bool(options.pull_models),
        dry_run=bool(options.dry_run),
        noninteractive=bool(options.noninteractive),
    )


def _ram_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.virtual_memory().total)
    except (ImportError, AttributeError):
        return None


def _disk_free(path: Path) -> int | None:
    probe = path
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        return int(shutil.disk_usage(probe).free)
    except OSError:
        return None


def _json_request(url: str, path: str, timeout: float = 3) -> Any:
    request = Request(url.rstrip("/") + path, headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def official_ollama_install(platform_name: str | None = None) -> dict[str, Any]:
    """Return the explicit official install action; never a remote shell pipe."""
    platform_name = platform_name or sys.platform
    if platform_name == "win32":
        return {
            "supported": True,
            "command": [
                "winget",
                "install",
                "--exact",
                "--id",
                "Ollama.Ollama",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            "manual_url": OLLAMA_DOWNLOAD_URL,
        }
    return {
        "supported": False,
        "command": None,
        "manual_url": OLLAMA_DOWNLOAD_URL,
        "reason": (
            "Automatic Ollama installation is disabled on this platform. "
            "Use the official download instructions; Seven will not execute curl|sh."
        ),
    }


def doctor(
    *,
    data_dir: Path | None = None,
    workspace: Path | None = None,
    ollama_url: str = "http://127.0.0.1:11434",
) -> dict[str, Any]:
    data_dir = Path(data_dir or settings_path().parent).expanduser().resolve()
    workspace = Path(workspace or data_dir / "workspace").expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    python_ok = sys.version_info >= (3, 11)
    if not python_ok:
        errors.append("Seven requires Python 3.11 or newer.")
    try:
        existing_settings = load_settings(data_dir)
        _reject_secret_fields(existing_settings)
    except ValueError as exc:
        errors.append(str(exc))

    disk_free = _disk_free(data_dir)
    ram = _ram_bytes()
    if disk_free is not None and disk_free < MIN_MODEL_FREE_BYTES:
        warnings.append("Less than 10 GiB is free; model downloads may fail.")
    if ram is not None and ram < RECOMMENDED_RAM_BYTES:
        warnings.append("Less than 8 GiB RAM is available; use a smaller model.")

    ollama_exe = shutil.which("ollama")
    ollama_version = None
    models: list[str] = []
    ollama_error = None
    try:
        version = _json_request(ollama_url, "/api/version")
        ollama_version = version.get("version") if isinstance(version, dict) else None
        tags = _json_request(ollama_url, "/api/tags")
        if isinstance(tags, dict):
            models = sorted(
                str(item.get("name"))
                for item in tags.get("models", [])
                if isinstance(item, dict) and item.get("name")
            )
    except (OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        ollama_error = str(exc)
        warnings.append(
            "Ollama is not responding. Seven can save setup choices, but local "
            "model chat will remain unavailable until Ollama is started."
        )

    return {
        "ok": not errors,
        "ready": not errors and ollama_error is None,
        "python": {
            "ok": python_ok,
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
        },
        "paths": {
            "data_dir": str(data_dir),
            "settings": str(data_dir / SETTINGS_FILE),
            "workspace": str(workspace),
        },
        "resources": {
            "ram_bytes": ram,
            "disk_free_bytes": disk_free,
            "model_download_warning": (
                "Text and vision models can require several GiB each. "
                "Keep at least 10 GiB free and avoid loading both on low-RAM hosts."
            ),
        },
        "ollama": {
            "ready": ollama_error is None,
            "executable": ollama_exe,
            "url": ollama_url.rstrip("/"),
            "version": ollama_version,
            "models": models,
            "error": ollama_error,
            "install": official_ollama_install(),
        },
        "package_install": {
            "source": 'python -m pip install -e ".[voice,tray]"',
            "wheel": 'python -m pip install "seven-ai[voice,tray]"',
            "note": "Use an isolated virtual environment; setup never modifies unrelated Python installations.",
        },
        "errors": errors,
        "warnings": warnings,
    }


def _settings_document(options: SetupOptions, previous: dict[str, Any]) -> dict[str, Any]:
    document = dict(previous)
    prior_identity = previous.get("identity")
    prior_models = previous.get("models")
    prior_voice = previous.get("voice")
    prior_camera = previous.get("camera")
    prior_startup = previous.get("startup")
    document.update(
        {
            "format": SETTINGS_FORMAT,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "identity": {
                **(prior_identity if isinstance(prior_identity, dict) else {}),
                "assistant_name": options.assistant_name,
                "user_name": options.user_name,
            },
            "workspace": str(options.workspace),
            "models": {
                **(prior_models if isinstance(prior_models, dict) else {}),
                "text": options.text_model,
                "vision": options.vision_model,
            },
            "voice": {
                **(prior_voice if isinstance(prior_voice, dict) else {}),
                "engine": options.voice_engine,
            },
            "camera": {
                **(prior_camera if isinstance(prior_camera, dict) else {}),
                "mode": options.camera_mode,
            },
            "startup": {
                **(prior_startup if isinstance(prior_startup, dict) else {}),
                "mode": options.startup_mode,
            },
        }
    )
    return document


def _reject_secret_fields(value: Any, prefix: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            location = f"{prefix}.{key}" if prefix else str(key)
            if normalized in _SECRET_FIELDS:
                raise ValueError(
                    f"refusing to persist credential-like setup field: {location}"
                )
            _reject_secret_fields(child, location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_fields(child, f"{prefix}[{index}]")


def write_settings(options: SetupOptions) -> Path:
    """Atomically merge setup choices while preserving unknown future fields."""
    path = settings_path(options.data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = load_settings(options.data_dir)
    document = _settings_document(options, previous)
    _reject_secret_fields(document)
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".settings-", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            temporary.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        os.replace(temporary, path)
        try:
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _run_visible(
    command: Sequence[str],
    *,
    timeout: float = 1800,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    try:
        result = runner(
            list(command),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "command": list(command), "error": str(exc)}
    return {
        "ok": result.returncode == 0,
        "command": list(command),
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def install_ollama_official(
    *,
    platform_name: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    plan = official_ollama_install(platform_name)
    if not plan["supported"]:
        return {"ok": False, **plan}
    if shutil.which(str(plan["command"][0])) is None:
        return {
            "ok": False,
            **plan,
            "error": "winget is not available; use the official Ollama download page.",
        }
    return {**plan, **_run_visible(plan["command"], timeout=900, runner=runner)}


def pull_model(
    model: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    model = _validate_model(model, "model")
    executable = shutil.which("ollama")
    if not executable:
        return {
            "ok": False,
            "model": model,
            "error": "Ollama executable was not found. Install/start Ollama first.",
        }
    return {
        "model": model,
        **_run_visible([executable, "pull", model], runner=runner),
    }


def _configure_startup(mode: str) -> dict[str, Any]:
    from seven.runtime.startup import install_startup, remove_startup

    if mode == "unchanged":
        return {"ok": True, "changed": False, "mode": mode}
    if mode == "none":
        return {"changed": True, "mode": mode, **remove_startup()}
    return {
        "changed": True,
        "mode": mode,
        **install_startup(quiet=mode == "quiet"),
    }


def run_setup(options: SetupOptions) -> dict[str, Any]:
    """Plan or apply setup. Existing data is merged/preserved, never removed."""
    try:
        options = validate_options(options)
    except (TypeError, ValueError) as exc:
        return {"ok": False, "status": "invalid", "errors": [str(exc)]}

    preflight = doctor(
        data_dir=options.data_dir,
        workspace=options.workspace,
        ollama_url=options.ollama_url,
    )
    plan = {
        "settings": str(settings_path(options.data_dir)),
        "workspace": str(options.workspace),
        "preserve_existing_data": True,
        "install_ollama": options.install_ollama,
        "pull_models": (
            [options.text_model, options.vision_model] if options.pull_models else []
        ),
        "startup": options.startup_mode,
        "ollama_install": official_ollama_install(),
    }
    if not preflight["ok"]:
        return {
            "ok": False,
            "status": "preflight_failed",
            "doctor": preflight,
            "plan": plan,
            "errors": preflight["errors"],
        }
    if options.dry_run:
        return {
            "ok": True,
            "status": "planned",
            "dry_run": True,
            "doctor": preflight,
            "plan": plan,
            "settings": asdict(options),
            "warnings": preflight["warnings"],
        }

    actions: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings = list(preflight["warnings"])
    if options.install_ollama:
        install = install_ollama_official()
        actions.append({"name": "install_ollama", **install})
        if not install.get("ok"):
            errors.append(str(install.get("error") or install.get("reason")))

    if options.pull_models:
        # Pull is explicit and each failure is visible; never delete another model.
        for model in (options.text_model, options.vision_model):
            result = pull_model(model)
            actions.append({"name": "pull_model", **result})
            if not result.get("ok"):
                errors.append(f"Could not pull {model}: {result.get('error') or result.get('stderr')}")

    if errors:
        return {
            "ok": False,
            "status": "external_action_failed",
            "doctor": preflight,
            "plan": plan,
            "actions": actions,
            "errors": errors,
            "warnings": warnings,
        }

    try:
        options.workspace.mkdir(parents=True, exist_ok=True)
        path = write_settings(options)
        actions.append({"name": "write_settings", "ok": True, "path": str(path)})
        startup = _configure_startup(options.startup_mode)
        actions.append({"name": "configure_startup", **startup})
        if not startup.get("ok"):
            errors.append(str(startup.get("error") or "startup configuration failed"))
    except (OSError, ValueError) as exc:
        errors.append(str(exc))

    return {
        "ok": not errors,
        "status": "configured" if not errors else "configuration_failed",
        "doctor": preflight,
        "plan": plan,
        "actions": actions,
        "settings_path": str(settings_path(options.data_dir)),
        "preserved_existing_data": True,
        "errors": errors,
        "warnings": warnings,
    }


def interactive_options(defaults: SetupOptions) -> SetupOptions:
    """Collect only documented, non-secret choices from a terminal."""

    def ask(label: str, default: str) -> str:
        value = input(f"{label} [{default}]: ").strip()
        return value or default

    assistant = ask("Assistant name", defaults.assistant_name)
    user = ask("Your name", defaults.user_name)
    workspace = Path(ask("Workspace", str(defaults.workspace)))
    text_model = ask("Ollama text model", defaults.text_model)
    vision_model = ask("Ollama vision model", defaults.vision_model)
    voice = ask("Voice engine (auto/edge/pyttsx3/none)", defaults.voice_engine)
    camera = ask("Camera mode (off/webcam/screen/both)", defaults.camera_mode)
    startup = ask("Login startup (unchanged/talk/quiet/none)", defaults.startup_mode)
    install = ask("Install Ollama with official command? (yes/no)", "no").lower() in {
        "y",
        "yes",
    }
    pull = ask("Pull selected models? (yes/no)", "no").lower() in {"y", "yes"}
    return SetupOptions(
        **{
            **asdict(defaults),
            "assistant_name": assistant,
            "user_name": user,
            "workspace": workspace,
            "text_model": text_model,
            "vision_model": vision_model,
            "voice_engine": voice,
            "camera_mode": camera,
            "startup_mode": startup,
            "install_ollama": install,
            "pull_models": pull,
        }
    )
