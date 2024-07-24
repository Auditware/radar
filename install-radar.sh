#!/bin/bash
set -e

echo "Installing radar.."

BASE_DIR="${XDG_CONFIG_HOME:-$HOME}"
RADAR_DIR="${RADAR_DIR-"$BASE_DIR/.radar"}"

REPO_URL="https://github.com/Auditware/radar.git"
SCRIPT_PATH="$RADAR_DIR/radar/radar.sh"
LINK_PATH="/usr/local/bin/radar"

mkdir -p "$RADAR_DIR"

if [ ! -d "$RADAR_DIR/radar" ]; then
    git clone "$REPO_URL" "$RADAR_DIR/radar"
else
    echo "Radar repository already exists. Pulling the latest changes.."
    git -C "$RADAR_DIR/radar" pull
fi

ln -sf "$SCRIPT_PATH" "$LINK_PATH"
chmod +x "$SCRIPT_PATH"
chmod +x "$LINK_PATH"

echo "Radar installed. You can run it by typing 'radar' in your terminal."