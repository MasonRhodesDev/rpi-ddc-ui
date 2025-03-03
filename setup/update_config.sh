#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./update_config.sh)"
  exit 1
fi

# Define service user and paths
SERVICE_USER="deskcontroller"
APP_DIR="/opt/desk-controller"
CONFIG_FILE="$APP_DIR/config.json"
SCRIPTS_DIR="$APP_DIR/scripts"
SUDOERS_FILE="/etc/sudoers.d/deskcontroller"

echo "Updating permissions for $SERVICE_USER based on config..."

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Create temporary file for sudoers
TMP_SUDOERS=$(mktemp)

# Start with header
cat > $TMP_SUDOERS << EOL
# Desk Controller permissions
# AUTOMATICALLY GENERATED - DO NOT EDIT MANUALLY
# Generated on $(date)

# Allow $SERVICE_USER to run specific commands without password
Defaults:$SERVICE_USER !requiretty

# Standard permissions for kiosk mode
$SERVICE_USER ALL=(ALL) NOPASSWD: /usr/bin/chvt
$SERVICE_USER ALL=(ALL) NOPASSWD: /usr/bin/xrandr
$SERVICE_USER ALL=(ALL) NOPASSWD: /sbin/reboot
$SERVICE_USER ALL=(ALL) NOPASSWD: /sbin/shutdown
$SERVICE_USER ALL=(ALL) NOPASSWD: /sbin/poweroff
$SERVICE_USER ALL=(ALL) NOPASSWD: /sbin/halt
$SERVICE_USER ALL=(ALL) NOPASSWD: /sbin/shutdown -h now
EOL

# Scan scripts directory for commands that need sudo privileges
echo "Scanning scripts directory for commands that need sudo privileges..."
SUDO_COMMANDS=$($APP_DIR/venv/bin/python3 -c "
import sys
sys.path.append('$APP_DIR/setup')
from system_check import scan_scripts_for_sudo_commands, generate_sudoers_entry
commands = scan_scripts_for_sudo_commands('$SCRIPTS_DIR', '$CONFIG_FILE')
if commands:
    print(generate_sudoers_entry('$SERVICE_USER', commands))
")

# Add the sudo commands to the sudoers file if any were found
if [ ! -z "$SUDO_COMMANDS" ]; then
    echo "" >> $TMP_SUDOERS
    echo "# Commands from scripts directory" >> $TMP_SUDOERS
    echo "$SUDO_COMMANDS" >> $TMP_SUDOERS
    echo "Found sudo commands in scripts: $SUDO_COMMANDS"
else
    echo "No sudo commands found in scripts directory."
fi

# Check if sudoers syntax is valid
visudo -c -f $TMP_SUDOERS
if [ $? -ne 0 ]; then
    echo "Error: Invalid sudoers syntax. Aborting."
    rm $TMP_SUDOERS
    exit 1
fi

# Move to final location
mv $TMP_SUDOERS $SUDOERS_FILE
chmod 440 $SUDOERS_FILE

echo "Permissions updated successfully!"
echo "Service user $SERVICE_USER can now execute the necessary commands" 