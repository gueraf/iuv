#!/usr/bin/env bash
set -euo pipefail

# Simple integration test for iuv run ...
# Verifies: initial run executes and a subsequent file change triggers a rerun.

LOG=test_output.log
rm -f "$LOG"
: > "$LOG"

# Create a simple target script
TARGET=watch_target.py
cat > "$TARGET" <<'PY'
print('HELLO')
PY

# Start watcher (background)
uv run iuv.py run "$TARGET" > "$LOG" 2>&1 &
PID=$!

echo "Started iuv watcher PID=$PID"
trap 'echo "Cleaning up"; pkill -f "iuv.py run $TARGET" || true' EXIT

# Wait for first occurrence
TIMEOUT=20
start=$(date +%s)
while true; do
  if grep -q HELLO "$LOG"; then
    echo "Initial run detected"
    break
  fi
  now=$(date +%s)
  if (( now - start > TIMEOUT )); then
    echo "FAIL: did not see initial HELLO within $TIMEOUT s" >&2
    exit 1
  fi
  sleep 0.5
done

# Trigger a change
sleep 1
# Touch a new file to trigger watch
echo '# change' > trigger_file.py

echo "Waiting for rerun after change..."
# Wait for at least 2 HELLO lines
start=$(date +%s)
while true; do
  count=$(grep -c HELLO "$LOG" || true)
  if (( count >= 2 )); then
    echo "Rerun detected (HELLO count=$count)"
    break
  fi
  now=$(date +%s)
  if (( now - start > TIMEOUT )); then
    echo "FAIL: no rerun detected within $TIMEOUT s" >&2
    echo "--- LOG ---"; cat "$LOG"; echo "-----------"
    exit 1
  fi
  sleep 0.5
done

# Success
pkill -f "iuv.py run $TARGET" || true
echo "Test passed"
