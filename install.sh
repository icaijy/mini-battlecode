#!/usr/bin/env bash
# Local Linux / WSL install; no root, pip or third-party packages needed.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
command -v python3 >/dev/null || { echo 'ERROR: python3 is required.' >&2; exit 1; }
command -v g++ >/dev/null || { echo 'ERROR: g++ is required (sudo apt install g++).' >&2; exit 1; }
python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit('ERROR: Python >= 3.10 required')
PY
mkdir -p "$HOME/.local/bin"
ln -sfn "$ROOT/scripts/mbc" "$HOME/.local/bin/mbc"
chmod +x "$ROOT/scripts/mbc"
printf '\nInstalled: %s\n' "$HOME/.local/bin/mbc"
printf 'Add to PATH if needed: export PATH="$HOME/.local/bin:$PATH"\n'
"$HOME/.local/bin/mbc" doctor
