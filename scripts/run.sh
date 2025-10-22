#!/usr/bin/env bash
set -euo pipefail

# 保证在项目根目录执行
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 确保虚拟环境存在
if [[ ! -x ".venv/bin/python" ]]; then
  echo "❌ No .venv found, please run bootstrap.sh first!"
  exit 1
fi

# 使用 .venv/bin/python 运行传入的参数
exec .venv/bin/python "$@"
