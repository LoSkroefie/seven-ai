import json
import sys

import pytest

from seven.security.credentials import read_credential, store_credential


@pytest.mark.skipif(sys.platform != "win32", reason="Windows DPAPI only")
def test_windows_dpapi_credential_round_trip(tmp_path):
    destination = tmp_path / "credential.json"
    store_credential(destination, "test-only-secret")

    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["provider"] == "windows-dpapi-current-user"
    assert "test-only-secret" not in destination.read_text(encoding="utf-8")
    assert read_credential(destination) == "test-only-secret"
