#!/bin/bash
# OmniSenter Stage-1 SFT training launcher.
# Designed to survive parent-shell death (pts disconnect, herm pause, etc.)
#
# Usage:  ./run_omnisenter_sft.sh
# Detaches via setsid + nohup, writes to logs/, registers a PID file,
# redirects all I/O so nothing can be tied to a closed TTY.
#
# Stop with:  kill $(cat /home/sovthpaw/projects/evolutionary-training/.run/sft.pid)

set -euo pipefail

REPO_DIR="/home/sovthpaw/projects/evolutionary-training"
RUN_DIR="${REPO_DIR}/training-output/omnisenter-sft-20260606_213858"
LOG_DIR="${REPO_DIR}/logs"
RUN_STATE_DIR="${REPO_DIR}/.run"
PID_FILE="${RUN_STATE_DIR}/sftresume.pid"
LOG_FILE="${LOG_DIR}/training_sft_$(date -u +%Y%m%d_%H%M%SZ).log"
LATEST_LOG_LINK="${LOG_DIR}/training_sft_latest.log"

mkdir -p "${RUN_STATE_DIR}" "${LOG_DIR}"

# Don't double-launch
if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "Training already running, PID=$(cat "${PID_FILE}"). Not relaunching."
  echo "  Tail log:   tail -f ${LATEST_LOG_LINK}"
  echo "  Stop:       kill \$(cat ${PID_FILE})"
  exit 1
fi

# Snapshot env so the detached child can reproduce it
SNAP_ENV="${RUN_STATE_DIR}/env.$(date -u +%Y%m%d_%H%M%SZ).sh"
{
  echo "# Snapshot of env at launch $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"
  echo "export PATH=\"${PATH}\""
  echo "export HOME=\"${HOME}\""
  echo "export USER=\"${USER}\""
  echo "export XDG_RUNTIME_DIR=\"${XDG_RUNTIME_DIR:-/run/user/1000}\""
} > "${SNAP_ENV}"
ln -sfn "$(basename "${SNAP_ENV}")" "${RUN_STATE_DIR}/env.latest.sh"

echo "============================================================"
echo "OMNISENTER SFT RESUME — launched $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  PID file:   ${PID_FILE}"
echo "  Log file:   ${LOG_FILE}"
echo "  Resume dir: ${RUN_DIR} (checkpoint-1000)"
echo "  Env snap:   ${SNAP_ENV}"
echo "============================================================"
echo "[launcher] parent PID $$" > "${LOG_FILE}"

# Detach hard: setsid -> new session, nohup -> ignore SIGHUP, & -> background.
# Redirect every FD so nothing inherits the agent's TTY.
setsid nohup bash -c "
  set -e
  source '${SNAP_ENV}'
  cd '${REPO_DIR}'
  printf '[child] detached, starting python at %s\n' \"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\" >> '${LOG_FILE}'
  exec python3 scripts/train_omnisenter_sft_fixed.py \
      --epochs 2 --batch-size 2 --gradient-accum 8 --lr 1e-4 \
      --max-seq-len 4096 --verbose \
      --output-dir '${RUN_DIR}' \
      --resume \
      >> '${LOG_FILE}' 2>&1
" </dev/null >/dev/null 2>&1 &

CHILD_PID=$!
disown ${CHILD_PID} 2>/dev/null || true
echo "${CHILD_PID}" > "${PID_FILE}"
ln -sfn "$(basename "${LOG_FILE}")" "${LATEST_LOG_LINK}"

echo "[launcher] detached python PID=${CHILD_PID} — written to ${PID_FILE}"
echo "[launcher] tail:   tail -f ${LATEST_LOG_LINK}"
echo "[launcher] status: cat ${PID_FILE} && ps -p \$(cat ${PID_FILE}) -o pid,etime,pcpu,pmem,stat,cmd"
