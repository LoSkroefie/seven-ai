"""Windows DPAPI-backed secret storage.

The encrypted document is portable only within the Windows user profile that
created it.  Plaintext is never accepted as a command-line argument.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
from ctypes import wintypes
import getpass
import json
import os
from pathlib import Path
import sys
import tempfile


class CredentialUnavailable(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _blob(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    return (
        _DataBlob(
            len(data),
            ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)),
        ),
        buffer,
    )


def _dpapi(data: bytes, *, protect: bool) -> bytes:
    if sys.platform != "win32":
        raise CredentialUnavailable("Windows DPAPI is unavailable on this platform")
    source, source_buffer = _blob(data)
    output = _DataBlob()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if protect:
        crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DataBlob),
            wintypes.LPCWSTR,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        ]
        crypt32.CryptProtectData.restype = wintypes.BOOL
        ok = crypt32.CryptProtectData(
            ctypes.byref(source),
            "Seven local credential",
            None,
            None,
            None,
            0x01,  # CRYPTPROTECT_UI_FORBIDDEN
            ctypes.byref(output),
        )
    else:
        description = wintypes.LPWSTR()
        crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DataBlob),
            ctypes.POINTER(wintypes.LPWSTR),
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        ]
        crypt32.CryptUnprotectData.restype = wintypes.BOOL
        ok = crypt32.CryptUnprotectData(
            ctypes.byref(source),
            ctypes.byref(description),
            None,
            None,
            None,
            0x01,
            ctypes.byref(output),
        )
        if description:
            kernel32.LocalFree(description)
    # Keep the source buffer alive for the duration of the Win32 call.
    del source_buffer
    if not ok:
        raise CredentialUnavailable(
            f"Windows DPAPI operation failed with {ctypes.get_last_error()}"
        )
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(output.pbData)


def protect_for_current_user(secret: str) -> str:
    if not isinstance(secret, str) or not secret:
        raise ValueError("credential cannot be empty")
    return base64.b64encode(_dpapi(secret.encode("utf-8"), protect=True)).decode(
        "ascii"
    )


def unprotect_for_current_user(ciphertext: str) -> str:
    try:
        encrypted = base64.b64decode(ciphertext, validate=True)
    except (ValueError, TypeError) as exc:
        raise CredentialUnavailable("credential ciphertext is invalid") from exc
    try:
        return _dpapi(encrypted, protect=False).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CredentialUnavailable("credential plaintext is invalid") from exc


def store_credential(path: str | os.PathLike[str], secret: str) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": 1,
        "provider": "windows-dpapi-current-user",
        "ciphertext": protect_for_current_user(secret),
    }
    fd, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=str(destination.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return destination


def read_credential(path: str | os.PathLike[str]) -> str:
    document = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or document.get("format") != 1
        or document.get("provider") != "windows-dpapi-current-user"
        or not isinstance(document.get("ciphertext"), str)
    ):
        raise CredentialUnavailable("credential document has an unsupported format")
    return unprotect_for_current_user(document["ciphertext"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Store a Seven credential using Windows DPAPI."
    )
    parser.add_argument("--store", required=True, metavar="PATH")
    args = parser.parse_args(argv)
    secret = getpass.getpass("Credential: ")
    destination = store_credential(args.store, secret)
    print(json.dumps({"ok": True, "path": str(destination), "provider": "DPAPI"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
