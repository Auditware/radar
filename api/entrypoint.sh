#!/bin/bash

# This runs as root to fix permissions first
# Fix permissions on mounted volumes for Foundry operations
if [ -d "/radar_data" ]; then
    echo "[i] Fixing /radar_data permissions for Foundry operations..."
    find /radar_data -type d -exec chmod 777 {} \; 2>/dev/null || true
fi

# Now switch to radar user and run the app
exec gosu radar /api/app-entrypoint.sh
