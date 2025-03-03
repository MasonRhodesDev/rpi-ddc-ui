#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./uninstall.sh)"
  exit 1
fi

# Execute the uninstall script from the setup directory
echo "Starting Desk Controller uninstallation..."
./setup/uninstall.sh

exit $? 