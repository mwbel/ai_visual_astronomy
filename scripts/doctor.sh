#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== Doctor check for project: $(basename "$ROOT") =="

# 查看真实 Python 解释器
echo "-- System python candidates --"
command -v /usr/local/bin/python3 || true
command -v /opt/homebrew/bin/python3 || true
[ -e /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 ] && \
  echo "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 (exists)"

# 检查 venv
echo "-- venv python --"
if [[ -x ".venv/bin/python" ]]; then
  echo "python: $(readlink .venv/bin/python || echo '.venv/bin/python')"
  echo "python3: $(readlink .venv/bin/python3 || echo '.venv/bin/python3')"
  echo "python3.11: $(readlink .venv/bin/python3.11 || echo '.venv/bin/python3.11')"

  .venv/bin/python --version || true
  .venv/bin/python -m pip --version || true

  # 测试核心库
  .venv/bin/python -c "import numpy, plotly, pytz; print('✅ core imports OK')" \
    2>/dev/null || echo "⚠️ Some libraries missing"
else
  echo "❌ No .venv/bin/python found. Run: bash scripts/bootstrap.sh"
fi
