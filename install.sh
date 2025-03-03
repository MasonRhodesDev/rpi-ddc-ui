#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

# Execute the setup script from the setup directory
echo "Starting Desk Controller installation..."
./setup/install.sh

exit $? 