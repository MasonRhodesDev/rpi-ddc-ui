#!/bin/bash

# Target host (ssh destination) is required, e.g. DESK_REMOTE=pi@raspberrypi.local ./setup-remote.sh
REMOTE="${DESK_REMOTE:?Set DESK_REMOTE to the ssh destination of the Pi}"

# Install dependencies all at once
ssh $REMOTE "sudo apt-get install -y python3-pip python3-venv python3-pyqt5"

ssh $REMOTE "rm -rf ~/desk-controller/*"

# Create src directory on remote if it doesn't exist
ssh $REMOTE "mkdir -p ~/desk-controller/src"

# Copy main.py to the remote server
scp main.py $REMOTE:~/desk-controller/

# Copy Python files from src directory to the remote server
scp src/*.py $REMOTE:~/desk-controller/src/

# Copy the __init__.py file specifically
scp src/__init__.py $REMOTE:~/desk-controller/src/

# Copy the local config.json (copy config.example.json first) to the remote server
[ -f config.json ] || { echo "config.json not found; copy config.example.json to config.json and edit it" >&2; exit 1; }
scp config.json $REMOTE:~/desk-controller/

# Copy the icons directory to the remote server
scp -r icons $REMOTE:~/desk-controller/

# Copy the scripts directory to the remote server
scp -r scripts $REMOTE:~/desk-controller/

# Install the service
ssh $REMOTE "~/desk-controller/main.py --install-service"

