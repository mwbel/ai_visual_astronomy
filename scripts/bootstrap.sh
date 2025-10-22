#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 选取真实解释器（按优先级）
REAL_PY="${REAL_PY:-}"
try() { command -v "$1" >/dev/null 2>&1 && echo "$1"; }
if [[ -z "$REAL_PY" ]]; then
  REAL_PY="$(try /usr/local/bin/python3 || true)"
  [[ -z "$REAL_PY" ]] && REAL_PY="$(try /opt/homebrew/bin/python3 || true)"
  [[ -z "$REAL_PY" ]] && REAL_PY="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
fi
"$REAL_PY" --version >/dev/null

# 建 venv（若不存在）
if [[ ! -d ".venv" ]]; then
  echo "→ Creating venv with $REAL_PY"
  "$REAL_PY" -m venv .venv
fi

# 统一软链：.venv/bin/python → .venv/bin/python3 → 真实解释器
rm -f .venv/bin/python .venv/bin/python3 .venv/bin/python3.11 || true
ln -s "$REAL_PY"       .venv/bin/python3.11
ln -s python3.11       .venv/bin/python3
ln -s python3          .venv/bin/python

# 激活并安装依赖
source .venv/bin/activate
.venv/bin/python --version
.venv/bin/python -m pip --version
if [[ -f requirements.txt ]]; then
  echo "→ Installing from requirements.txt"
  .venv/bin/python -m pip install -r requirements.txt
fi

echo "✅ bootstrap done. VIRTUAL_ENV=$VIRTUAL_ENV"
