#!/usr/bin/env bash
# staleness_watchdog — dumb scheduled watchdog for an orchestration pack.
#
# A script, not an agent: it detects orchestrator death by something the
# orchestrator does not have to be alive to run. Schedule it (cron, launchd,
# CI cron) on the pack's status cadence; the OPERATOR wires the alert channel
# (cron mail, a notify hook, a messaging webhook) to a non-zero exit.
#
# Behavior: reads the modification time of the heartbeat/status artifact and
# exits 1 with a message on stdout when it is older than the cadence (or
# missing). Exits 0 when fresh.
#
# Configure via environment (or edit the defaults):
HEARTBEAT_FILE="${HEARTBEAT_FILE:-PROGRESS.md}"   # heartbeat / status artifact
MAX_AGE_MINUTES="${MAX_AGE_MINUTES:-120}"         # the declared status cadence
LABEL="${LABEL:-orchestrator}"                    # names the watched session

set -u

if [ ! -e "$HEARTBEAT_FILE" ]; then
  echo "STALE [$LABEL]: heartbeat file '$HEARTBEAT_FILE' does not exist"
  exit 1
fi

# File mtime, portable across GNU (stat -c) and BSD/macOS (stat -f).
if ! mtime=$(stat -c %Y "$HEARTBEAT_FILE" 2>/dev/null); then
  mtime=$(stat -f %m "$HEARTBEAT_FILE")
fi

now=$(date +%s)
age_minutes=$(( (now - mtime) / 60 ))

if [ "$age_minutes" -gt "$MAX_AGE_MINUTES" ]; then
  echo "STALE [$LABEL]: '$HEARTBEAT_FILE' last updated ${age_minutes}m ago" \
       "(cadence ${MAX_AGE_MINUTES}m). Check the status artifact; follow the" \
       "stand-down handshake before relaunching a presumed-dead session."
  exit 1
fi

echo "OK [$LABEL]: '$HEARTBEAT_FILE' updated ${age_minutes}m ago (within ${MAX_AGE_MINUTES}m)"
exit 0
