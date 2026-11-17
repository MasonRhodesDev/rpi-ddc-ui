#!/bin/bash

REMOTE="${DESK_REMOTE:?Set DESK_REMOTE to the ssh destination of the Pi}"

ssh $REMOTE "sudo apt-get install -y python3-pip python3-venv python3-pyqt5"

ssh $REMOTE "rm -rf ~/desk-controller/*"

ssh $REMOTE "mkdir -p ~/desk-controller/src"

scp main.py $REMOTE:~/desk-controller/

scp src/*.py $REMOTE:~/desk-controller/src/

scp src/__init__.py $REMOTE:~/desk-controller/src/

[ -f config.json ] || { echo "config.json not found; copy config.example.json to config.json and edit it" >&2; exit 1; }
scp config.json $REMOTE:~/desk-controller/

scp -r icons $REMOTE:~/desk-controller/

scp -r scripts $REMOTE:~/desk-controller/

ssh $REMOTE "~/desk-controller/main.py --install-service"

