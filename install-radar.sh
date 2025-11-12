#!/bin/bash
set -e

echo "Installing radar.."

BASE_DIR="${XDG_CONFIG_HOME:-$HOME}"
RADAR_DIR="${RADAR_DIR-"$BASE_DIR/.radar"}"
REPO_URL="https://github.com/auditware/radar.git"
SCRIPT_PATH="$RADAR_DIR/radar"
LINK_PATH="/usr/local/bin/radar"

echo "$SCRIPT_PATH"

mkdir -p "$RADAR_DIR"

if [ ! -d "$RADAR_DIR/.git" ]; then
    git clone "$REPO_URL" "$RADAR_DIR"
else
    echo "radar repository already exists. Pulling the latest changes.."
    git -C "$RADAR_DIR" clean -fd
    git -C "$RADAR_DIR" reset --hard HEAD
    git -C "$RADAR_DIR" pull
fi

chmod +x "$SCRIPT_PATH"

if ln -sf "$SCRIPT_PATH" "$LINK_PATH" 2>/dev/null; then
    chmod +x "$LINK_PATH" 2>/dev/null || true
    echo "radar installed. You can run it by typing 'radar' in your terminal."
else
    echo "Adding radar directory to PATH."

    case $SHELL in
        */zsh)
            PROFILE="${ZDOTDIR:-"$HOME"}/.zshenv"
            ;;
        */bash)
            PROFILE="$HOME/.bashrc"
            ;;
        */fish)
            PROFILE="$HOME/.config/fish/config.fish"
            ;;
        */ash)
            PROFILE="$HOME/.profile"
            ;;
        *)
            echo "Could not detect shell, please manually add ${RADAR_DIR} to your PATH before running radar."
            exit 1
            ;;
    esac

    if [[ ":$PATH:" != *":$RADAR_DIR:"* ]]; then
        if [[ "$SHELL" == */fish ]]; then
            echo "set -Ux fish_user_paths $RADAR_DIR \$fish_user_paths" >> "$PROFILE"
        else
            echo "export PATH=\"$RADAR_DIR:\$PATH\"" >> "$PROFILE"
        fi
    fi

    echo "radar installed. Please run 'source $PROFILE' or restart your terminal session before running radar."
fi