#!/bin/bash
set -e

echo ""
echo "── M&A Dashboard Setup ────────────────────────────"
echo ""

# 1. Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "  ✓ Dependencies installed"

# 2. Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo ""
  echo "  ⚠️  ANTHROPIC_API_KEY is not set."
  echo "  Add this line to your ~/.zshrc:"
  echo "    export ANTHROPIC_API_KEY='sk-ant-...'"
  echo "  Then run: source ~/.zshrc"
else
  echo "  ✓ ANTHROPIC_API_KEY is set"
fi

echo ""
echo "── Done! Next steps ───────────────────────────────"
echo ""
echo "  1. Generate your first dashboard:"
echo "       python dashboard.py update"
echo ""
echo "  2. Set up automatic Thursday-night updates:"
echo "       bash cron_setup.sh"
echo ""
echo "  3. (Optional) Publish to GitHub Pages for remote access:"
echo "       bash github_setup.sh"
echo ""
