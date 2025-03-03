#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install_modified.sh)"
  exit 1
fi

# Define variables
SERVICE_USER="deskcontroller"
APP_DIR="/opt/desk-controller"
BYPASS_DSI_CHECK=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --bypass-dsi-check)
      BYPASS_DSI_CHECK=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: sudo ./install_modified.sh [--bypass-dsi-check]"
      exit 1
      ;;
  esac
done

echo "Starting Desk Controller installation..."
echo "Installing Desk Controller..."

# Check if running on a Raspberry Pi
if [ ! -f "/proc/device-tree/model" ] || ! grep -q "Raspberry Pi" "/proc/device-tree/model"; then
    echo "Error: This application is designed to run on a Raspberry Pi."
    echo "Current system is not detected as a Raspberry Pi."
    exit 1
fi

# Check if DSI display is connected (will be verified more thoroughly later)
echo "Checking for DSI display..."
if [ "$BYPASS_DSI_CHECK" = "true" ]; then
    echo "DSI display check bypassed as requested."
else
    echo "DSI display check will be performed during system check."
fi

# Check if user exists, create if not
if id "$SERVICE_USER" &>/dev/null; then
    echo "Service user $SERVICE_USER already exists"
else
    echo "Creating service user $SERVICE_USER..."
    useradd -m -s /bin/bash $SERVICE_USER
fi

# Create application directory
echo "Creating application directory..."
mkdir -p $APP_DIR

# Copy all files to application directory
echo "Copying files to $APP_DIR..."
cp -r *.py *.sh *.md *.json *.txt $APP_DIR/ 2>/dev/null || true
cp -r icons $APP_DIR/ 2>/dev/null || true
cp -r scripts $APP_DIR/ 2>/dev/null || true
cp -r setup $APP_DIR/ 2>/dev/null || true
cp -r .git $APP_DIR/ 2>/dev/null || true

# Create scripts directory if it doesn't exist
if [ ! -d "$APP_DIR/scripts" ]; then
    echo "Creating scripts directory..."
    mkdir -p $APP_DIR/scripts
    chmod 755 $APP_DIR/scripts
fi

# Ensure config.json exists and has correct permissions
if [ ! -f "$APP_DIR/config.json" ]; then
    echo "Error: config.json not found in $APP_DIR"
    exit 1
fi
chmod 644 $APP_DIR/config.json
echo "Verified config.json exists and has correct permissions"

# Install system dependencies using apt instead of pip for PyQt5
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3-pyqt5 python3-pip python3-venv python3-pillow

# Create virtual environment if it doesn't exist
if [ ! -d "$APP_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $APP_DIR/venv
fi

# Install remaining Python dependencies (excluding PyQt5)
echo "Installing Python dependencies..."
$APP_DIR/venv/bin/pip install json5>=0.9.0 Pillow>=9.0.0

# Create a modified system_check.py if bypassing DSI check
if [ "$BYPASS_DSI_CHECK" = "true" ]; then
    echo "Creating modified system check script..."
    cat > $APP_DIR/setup/system_check_modified.py << 'EOF'
#!/usr/bin/env python3
import os
import subprocess
import sys
import re
import json

def is_raspberry_pi():
    """
    Check if the current system is a Raspberry Pi.
    Returns True if it is, False otherwise.
    """
    # Method 1: Check for Raspberry Pi model file
    if os.path.exists('/proc/device-tree/model'):
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                return True
    
    # Method 2: Check CPU info
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM2708' in cpuinfo or 'BCM2709' in cpuinfo or 'BCM2711' in cpuinfo or 'BCM2835' in cpuinfo:
                return True
    except:
        pass
    
    # Method 3: Check for Raspberry Pi specific hardware
    try:
        output = subprocess.check_output(['grep', '-q', 'Raspberry Pi', '/proc/device-tree/model'], stderr=subprocess.STDOUT)
        return True
    except:
        pass
    
    return False

def is_dsi_display_connected():
    """
    This is a modified version that always returns True to bypass the DSI check.
    """
    print("DSI display check bypassed as requested.")
    return True

def check_system_requirements():
    """
    Check if the system meets the requirements.
    Exits with an error message if not.
    """
    # Check if running on a Raspberry Pi
    if not is_raspberry_pi():
        print("Error: This application is designed to run on a Raspberry Pi.")
        print("Current system is not detected as a Raspberry Pi.")
        sys.exit(1)
    
    # DSI display check is bypassed
    print("System check passed: Running on Raspberry Pi (DSI display check bypassed).")
    return True

if __name__ == "__main__":
    check_system_requirements()
EOF
    chmod +x $APP_DIR/setup/system_check_modified.py
    
    # Run the modified system check
    echo "Running modified system check..."
    $APP_DIR/venv/bin/python $APP_DIR/setup/system_check_modified.py
else
    # Run the original system check
    echo "Running system check..."
    $APP_DIR/venv/bin/python $APP_DIR/setup/system_check.py
fi

if [ $? -ne 0 ]; then
    echo "System requirements check failed!"
    echo "If you're sure you have a DSI display connected, try running with --bypass-dsi-check"
    exit 1
fi
echo "System requirements check passed!"

# Generate icons
echo "Generating sample icons..."
$APP_DIR/venv/bin/python $APP_DIR/setup/create_icons.py

# Make scripts executable
echo "Making scripts executable..."
chmod +x $APP_DIR/main.py
chmod +x $APP_DIR/setup/config_validator.py
chmod +x $APP_DIR/setup/create_icons.py
chmod +x $APP_DIR/setup/setup.sh
chmod +x $APP_DIR/setup/uninstall.sh
chmod +x $APP_DIR/setup/update_config.sh
chmod +x $APP_DIR/setup/setup_kiosk.sh
chmod +x $APP_DIR/setup/test_config.py
chmod +x $APP_DIR/setup/system_check.py
if [ "$BYPASS_DSI_CHECK" = "true" ]; then
    chmod +x $APP_DIR/setup/system_check_modified.py
fi

# Set ownership
echo "Setting ownership..."
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

# Test configuration
echo "Testing configuration..."
cd $APP_DIR
python3 $APP_DIR/setup/test_config.py
if [ $? -ne 0 ]; then
    echo "Configuration test failed! Please check the config.json file."
    exit 1
fi
echo "Configuration test passed!"

# Check if kiosk mode is enabled in config.json
KIOSK_MODE=false
if command -v jq >/dev/null; then
    # Use jq to check if kiosk mode is enabled
    KIOSK_MODE=$(jq -r '.display.kiosk_mode // false' $APP_DIR/config.json)
    AUTO_START=$(jq -r '.display.auto_start // false' $APP_DIR/config.json)
else
    # Try to parse with grep if jq is not available
    if grep -q '"kiosk_mode":\s*true' $APP_DIR/config.json; then
        KIOSK_MODE=true
    fi
    if grep -q '"auto_start":\s*true' $APP_DIR/config.json; then
        AUTO_START=true
    fi
fi

# Set up based on configuration
if [ "$KIOSK_MODE" = "true" ]; then
    echo "Kiosk mode is enabled in config.json"
    echo "Setting up kiosk mode..."
    $APP_DIR/setup/setup_kiosk.sh
    
    # Since we're using kiosk mode, we don't need the systemd service
    echo "Kiosk mode will handle application startup"
else
    # Run setup script for normal mode (systemd service)
    echo "Kiosk mode is not enabled in config.json"
    echo "Running setup script for normal mode..."
    $APP_DIR/setup/setup.sh
fi

# Run update_config.sh to set up permissions
echo "Setting up permissions for service user..."
$APP_DIR/setup/update_config.sh

echo "Installation complete!"
if [ "$KIOSK_MODE" = "true" ]; then
    echo "The application will start automatically on boot in kiosk mode."
    echo "Please reboot the system to apply changes: sudo reboot"
else
    echo "The application will start automatically on boot as a service."
fi
echo "Configuration file is located at $APP_DIR/config.json" 