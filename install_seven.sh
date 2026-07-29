#!/usr/bin/env sh
set -eu

repo=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
install_root="${XDG_DATA_HOME:-$HOME/.local/share}/seven-ai"
venv="$install_root/venv"
dry_run=0
setup_args="--setup"

for argument in "$@"; do
    case "$argument" in
        --dry-run) dry_run=1; setup_args="$setup_args --setup-dry-run" ;;
        --noninteractive) setup_args="$setup_args --setup-noninteractive" ;;
        --install-ollama) setup_args="$setup_args --setup-install-ollama" ;;
        --pull-models) setup_args="$setup_args --setup-pull-models" ;;
        *) echo "Unknown option: $argument" >&2; exit 2 ;;
    esac
done

python_bin=${PYTHON:-python3}
"$python_bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' ||
    { echo "Python 3.11 or newer is required." >&2; exit 1; }

if [ "$dry_run" -eq 1 ]; then
    echo "DRY RUN: would create isolated environment at $venv"
    echo "DRY RUN: would install $repo with voice and tray extras"
    # shellcheck disable=SC2086
    (cd "$repo" && "$python_bin" -m seven $setup_args)
    exit $?
fi

if [ -e "$venv" ] && [ ! -f "$venv/pyvenv.cfg" ]; then
    echo "Refusing to reuse non-venv path: $venv" >&2
    exit 1
fi
mkdir -p "$install_root"
if [ ! -d "$venv" ]; then
    "$python_bin" -m venv "$venv"
fi
"$venv/bin/python" -m pip install --upgrade pip
"$venv/bin/python" -m pip install --upgrade "$repo[voice,tray]"
# shellcheck disable=SC2086
"$venv/bin/python" -m seven $setup_args
