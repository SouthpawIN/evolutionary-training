#!/bin/bash
# Discord Bot Permission Fix
# Run this to authorize Anser with ADMINISTRATOR permissions on Senter Dev guild
#
# Usage: bash discord-auth-fix.sh

BOT_ID="1466875910199443791"
GUILD_ID="1413569163200434248"
PERMISSIONS="8"  # ADMINISTRATOR

AUTH_URL="https://discord.com/oauth2/authorize?client_id=${BOT_ID}&permissions=${PERMISSIONS}&guild_id=${GUILD_ID}&scope=bot"

echo "=== Discord Bot Permission Fix ==="
echo ""
echo "This will open the Discord authorization page in your browser."
echo "Click 'Authorize' to grant Anser ADMINISTRATOR permissions."
echo ""
echo "URL: $AUTH_URL"
echo ""

# Try to open in browser
if command -v xdg-open &>/dev/null; then
    xdg-open "$AUTH_URL"
elif command -v open &>/dev/null; then
    open "$AUTH_URL"
else
    echo "Open this URL manually: $AUTH_URL"
fi

echo ""
echo "After authorizing, verify with:"
echo "  curl -s -X POST -H 'Authorization: Bot \$DISCORD_TOKEN' -H 'Content-Type: application/json' \\"
echo "    -d '{\"name\":\"test\",\"type\":0}' \\"
echo "    'https://discord.com/api/v10/guilds/${GUILD_ID}/channels'"
