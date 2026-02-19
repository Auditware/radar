#!/bin/bash

# Run as root - needed for Foundry operations on mounted volumes
# Fix permissions on mounted volumes
if [ -d "/radar_data" ]; then
    echo "[i] Fixing /radar_data permissions for Foundry operations..."
    chmod -R 777 /radar_data 2>/dev/null || true
fi

# Run the app as root (Foundry needs write access to mounted volumes)
exec /api/app-entrypoint.sh
