#!/bin/bash
set -e

RADAR_BASE_DIR="${XDG_CONFIG_HOME:-$HOME}/.radar"

arm_specific_flag=""
if [[ "$(uname -m)" == "arm64" ]] || [[ "$(uname -m)" == "aarch64" ]]; then
    arm_specific_flag="--platform linux/amd64"
fi

check_docker() {
    local timeout_duration=5

    docker compose version &> /dev/null &
    pid=$!

    ( sleep $timeout_duration && kill -0 "$pid" 2>/dev/null && kill -9 "$pid" && echo "[w] Docker availability check timed out" && exit 1 ) &

    wait $pid

    local status=$?

    if [ $status -ne 0 ]; then
        echo "[e] Docker is not available. Please ensure Docker is installed and running. If further problems arise consider restarting the Docker service."
        exit 1
    fi
}

check_image_update() {
    local image="$1"
    local registry="$2"
    local registry_digest

    registry_digest=$(docker pull $arm_specific_flag "$registry" > /dev/null && docker inspect --format="{{index .RepoDigests 0}}" "$registry")

    if [ -z "$registry_digest" ]; then
        echo "[e] Could not retrieve the digest for $registry. Skipping update check."
        return 1
    fi

    local local_digest
    local_digest=$(docker images --format "{{.Repository}}@{{.Digest}}" "$image" | head -n 1)

    if [ "$local_digest" != "$registry_digest" ]; then
        echo "[i] Updating $image to $registry_digest"
        docker pull $arm_specific_flag "$registry"
        docker compose up -d
    else
        echo "[i] $image is up to date."
    fi
}

check_docker

cd "$RADAR_BASE_DIR"

check_image_update "controller" "ghcr.io/auditware/radar-controller:main"
check_image_update "api" "ghcr.io/auditware/radar-api:main"

cd "$INITIAL_DIR"

exec curl -L https://raw.githubusercontent.com/auditware/radar/main/install-radar.sh | bash