from pathlib import Path

from seven.runtime.startup import install_startup, remove_startup, startup_status


def test_windows_startup_install_and_remove(tmp_path, monkeypatch):
    appdata = tmp_path / "Roaming"
    monkeypatch.setenv("APPDATA", str(appdata))
    result = install_startup(platform_name="win32", home=tmp_path, python_exe=r"C:\Program Files\Python\python.exe")
    target = Path(result["path"])
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "-m seven --talk" in text
    assert startup_status("win32", tmp_path)["installed"] is True
    assert remove_startup("win32", tmp_path)["removed"] is True


def test_linux_startup_is_talk_by_default(tmp_path):
    result = install_startup(platform_name="linux", home=tmp_path, python_exe="/usr/bin/python3")
    target = Path(result["path"])
    text = target.read_text(encoding="utf-8")
    assert "Exec=/usr/bin/python3 -m seven --talk" in text
    assert "X-GNOME-Autostart-enabled=true" in text


def test_macos_startup_quiet(tmp_path):
    result = install_startup(quiet=True, platform_name="darwin", home=tmp_path, python_exe="/usr/bin/python3")
    data = Path(result["path"]).read_bytes()
    assert b"--quiet" in data
    assert b"RunAtLoad" in data
