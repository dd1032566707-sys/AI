#!/usr/bin/env bash
# 启动 Live2D 语音对话页（含免费 Edge 神经语音 TTS 代理）
# 用法: bash start.sh [端口]   (默认 8123)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT="${1:-8123}"

# 选一个能跑 edge_tts 的 python（优先本机已有的 venv，其次系统 python3）
PY=""
for cand in \
  "/Users/jeremy/.workbuddy/binaries/python/envs/default/bin/python" \
  "$(command -v python3)" ; do
  if [ -n "$cand" ] && [ -x "$cand" ] && "$cand" -c "import edge_tts" >/dev/null 2>&1; then
    PY="$cand"; break
  fi
done

# 都没有就建一个 .venv 并安装依赖
if [ -z "$PY" ]; then
  echo "未找到含 edge-tts 的环境，正在创建 .venv 并安装依赖…"
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
  PY="$(command -v python)"
fi

echo "用 $PY 在端口 $PORT 启动服务…"
exec "$PY" serve.py "$PORT"
