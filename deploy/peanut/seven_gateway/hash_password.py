from __future__ import annotations

import getpass

from .security import hash_password


def main() -> int:
    first = getpass.getpass("New Seven owner password: ")
    second = getpass.getpass("Confirm password: ")
    if first != second:
        print("Passwords do not match.")
        return 1
    try:
        print(hash_password(first))
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
