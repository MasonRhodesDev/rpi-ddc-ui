#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "Installing Desk Controller..."

# Define service user
SERVICE_USER="deskcontroller"
APP_DIR="/opt/desk-controller"

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

# Create virtual environment if it doesn't exist
if [ ! -d "$APP_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python -m venv $APP_DIR/venv
fi

# Install dependencies
echo "Installing dependencies..."
$APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Generate icons
echo "Generating sample icons..."
$APP_DIR/venv/bin/python $APP_DIR/create_icons.py

# Make scripts executable
echo "Making scripts executable..."
chmod +x $APP_DIR/main.py
chmod +x $APP_DIR/config_validator.py
chmod +x $APP_DIR/create_icons.py
chmod +x $APP_DIR/setup.sh
chmod +x $APP_DIR/uninstall.sh
chmod +x $APP_DIR/update_config.sh
chmod +x $APP_DIR/setup_kiosk.sh
chmod +x $APP_DIR/test_config.py

# Set ownership
echo "Setting ownership..."
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

# Test configuration
echo "Testing configuration..."
cd $APP_DIR
python3 $APP_DIR/test_config.py
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
    $APP_DIR/setup_kiosk.sh
    
    # Since we're using kiosk mode, we don't need the systemd service
    echo "Kiosk mode will handle application startup"
else
    # Run setup script for normal mode (systemd service)
    echo "Kiosk mode is not enabled in config.json"
    echo "Running setup script for normal mode..."
    $APP_DIR/setup.sh
fi

# Run update_config.sh to set up permissions
echo "Setting up permissions for service user..."
$APP_DIR/update_config.sh

echo "Installation complete!"
if [ "$KIOSK_MODE" = "true" ]; then
    echo "The application will start automatically on boot in kiosk mode."
    echo "Please reboot the system to apply changes: sudo reboot"
else
    echo "The application will start automatically on boot as a service."
fi
echo "Configuration file is located at $APP_DIR/config.json" 