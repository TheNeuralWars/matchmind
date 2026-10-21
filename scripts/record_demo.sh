#!/usr/bin/env bash
# Record demo clips of the MatchMind UI on a private virtual display (Xvfb + Chrome kiosk + ffmpeg x11grab).
# Output: media/*.mp4 (gitignored). Usage: scripts/record_demo.sh [seconds_per_clip]
set -euo pipefail
cd "$(dirname "$0")/.."
SECS=${1:-60}; DISP=:77
PORT=${PORT:-$(python3 -c "import socket;s=socket.socket();s.bind(('127.0.0.1',0));print(s.getsockname()[1])")}; W=1920; H=1080
mkdir -p media
Xvfb $DISP -screen 0 ${W}x${H}x24 -nolisten tcp >/dev/null 2>&1 & XPID=$!
PORT=$PORT python3 -m matchmind.server >/dev/null 2>&1 & SPID=$!
trap 'kill $XPID $SPID 2>/dev/null || true' EXIT
for _ in $(seq 50); do curl -sf "localhost:$PORT/health" >/dev/null && break; sleep 0.2; done
curl -sf "localhost:$PORT/health" >/dev/null || { echo "server failed on :$PORT" >&2; exit 1; }
SPEED=$(( 5600 / (SECS - 3) ))
record () {  # name, query-or-url [secs]
  local prof; prof=$(mktemp -d); local scale=1; local ws="$W,$H"
  [[ $2 == file://* ]] && { scale=1.5; ws="$((W*2/3)),$((H*2/3))"; }   # terminal pages: 1.5x; UI: page zoom instead
  DISPLAY=$DISP google-chrome --no-sandbox --no-first-run --disable-gpu --user-data-dir="$prof" --kiosk --window-size=$ws \
      --window-position=0,0 --force-device-scale-factor=$scale "$( [[ $2 == file://* ]] && echo "$2" || echo "http://localhost:$PORT/?autostart=1&zoom=1.45&speed=$SPEED&$2" )" >/dev/null 2>&1 & local CPID=$!
  sleep 1.2
  ffmpeg -y -loglevel error -f x11grab -draw_mouse 0 -video_size ${W}x${H} -framerate 30 -i $DISP -t "${3:-$SECS}" \
      -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p "media/$1.mp4"
  kill $CPID 2>/dev/null || true; wait $CPID 2>/dev/null || true; rm -rf "$prof" 2>/dev/null || true
  echo "media/$1.mp4"
}
if [[ "${ONLY_UI:-0}" != 1 ]]; then
python3 scripts/make_terminal_pages.py >/dev/null
record term-dataset "file://$PWD/media/term-dataset.html" 17
record term-mcp "file://$PWD/media/term-mcp.html" 16
fi
record split-analyst-en_casual-it "view=split&seed=8&lang=en&lang2=it"
record analyst-es "seed=8&persona=analyst&lang=es"
record casual-it-NOR "seed=8&persona=casual&club=NOR&lang=it"
