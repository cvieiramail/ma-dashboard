#!/bin/bash
# Sets up a cron job to run the dashboard update every Thursday at 22:00

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"
LOG="$SCRIPT_DIR/cron.log"

# Cron expression: minute hour day-of-month month day-of-week
# 0 22 * * 4  →  22:00 every Thursday (4 = Thursday)
CRON_LINE="0 22 * * 4 cd \"$SCRIPT_DIR\" && $PYTHON dashboard.py update >> \"$LOG\" 2>&1"

echo ""
echo "── Cron Job Setup ─────────────────────────────────"
echo ""
echo "  Schedule: Every Thursday at 22:00"
echo "  Script:   $SCRIPT_DIR/dashboard.py"
echo "  Log:      $LOG"
echo ""

# Add to crontab (preserving existing entries, removing old dashboard lines)
(crontab -l 2>/dev/null | grep -v "dashboard.py"; echo "$CRON_LINE") | crontab -

echo "  ✓ Cron job installed."
echo ""
echo "  Verify with:   crontab -l"
echo "  View logs:     tail -f $LOG"
echo "  Remove job:    crontab -e  (then delete the dashboard.py line)"
echo ""
