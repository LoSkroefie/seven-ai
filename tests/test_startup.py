from pathlib import Path

from seven.runtime.startup import install_startup, remove_startup, startup_status


def test_windows_startup_install_and_remove(tmp_path, monkeypatch):
    appdata = tmp_path / "Roaming"
    monkeypatch.setenv("APPDATA", str(appdata))
    result = install_startup(
        platform_name="win32",
        home=tmp_path,
        python_exe=r"C:\Program Files\Python\python.exe",
        environment={
            "SEVEN_DATA_DIR": r"D:\SevenLocal\data",
            "SEVEN_WORKSPACE": r"D:\SevenLocal\workspace",
            "SEVEN_PROJECT_ROOTS": r"C:\Projects;D:\Work",
            "SEVEN_TOOL_SCHEMA_MODE": "dispatcher",
            "SEVEN_SMTP_HOST": "mail.example.com",
            "SEVEN_EMAIL_CREDENTIAL_FILE": r"D:\SevenLocal\data\email-credential.json",
            "IGNORED_SECRET": "not-written",
        },
    )
    target = Path(result["path"])
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "-m seven --talk" in text
    assert 'set "SEVEN_DATA_DIR=D:\\SevenLocal\\data"' in text
    assert 'set "SEVEN_WORKSPACE=D:\\SevenLocal\\workspace"' in text
    assert 'set "SEVEN_PROJECT_ROOTS=C:\\Projects;D:\\Work"' in text
    assert 'set "SEVEN_TOOL_SCHEMA_MODE=dispatcher"' in text
    assert 'set "SEVEN_VOICE=1"' in text
    assert 'set "SEVEN_QUIET=0"' in text
    assert 'set "SEVEN_SMTP_HOST=mail.example.com"' in text
    assert (
        'set "SEVEN_EMAIL_CREDENTIAL_FILE=D:\\SevenLocal\\data\\email-credential.json"'
        in text
    )
    assert "IGNORED_SECRET" not in text
    assert result["environment_keys"] == [
        "SEVEN_DATA_DIR",
        "SEVEN_EMAIL_CREDENTIAL_FILE",
        "SEVEN_PROJECT_ROOTS",
        "SEVEN_QUIET",
        "SEVEN_SMTP_HOST",
        "SEVEN_TOOL_SCHEMA_MODE",
        "SEVEN_VOICE",
        "SEVEN_WORKSPACE",
    ]
    assert startup_status("win32", tmp_path)["installed"] is True
    assert remove_startup("win32", tmp_path)["removed"] is True


def test_windows_quiet_startup_is_explicitly_text_only(tmp_path, monkeypatch):
    appdata = tmp_path / "Roaming"
    monkeypatch.setenv("APPDATA", str(appdata))

    result = install_startup(
        quiet=True,
        platform_name="win32",
        home=tmp_path,
        python_exe=r"C:\Python\python.exe",
    )

    text = Path(result["path"]).read_text(encoding="utf-8")
    assert "-m seven --quiet" in text
    assert "--avatar" not in text
    assert 'set "SEVEN_VOICE=0"' in text
    assert 'set "SEVEN_QUIET=1"' in text
    assert result["mode"] == "quiet"


def test_linux_startup_is_talk_by_default(tmp_path):
    result = install_startup(
        platform_name="linux",
        home=tmp_path,
        python_exe="/usr/bin/python3",
        environment={"SEVEN_DATA_DIR": "/srv/seven data"},
    )
    target = Path(result["path"])
    text = target.read_text(encoding="utf-8")
    assert (
        "Exec=/usr/bin/env SEVEN_DATA_DIR='/srv/seven data' SEVEN_VOICE=1 "
        "SEVEN_QUIET=0 /usr/bin/python3 -m seven --talk"
    ) in text
    assert "X-GNOME-Autostart-enabled=true" in text


def test_macos_startup_quiet(tmp_path):
    result = install_startup(
        quiet=True,
        platform_name="darwin",
        home=tmp_path,
        python_exe="/usr/bin/python3",
        environment={"SEVEN_TOOL_TIER": "full"},
    )
    data = Path(result["path"]).read_bytes()
    assert b"--quiet" in data
    assert b"RunAtLoad" in data
    assert b"SEVEN_TOOL_TIER" in data
