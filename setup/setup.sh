#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./setup.sh)"
  exit 1
fi

# Define service user and paths
SERVICE_USER="deskcontroller"
APP_DIR="/opt/desk-controller"

# Make scripts executable
chmod +x $APP_DIR/main.py
chmod +x $APP_DIR/config_validator.py

# Get absolute paths
VENV_PYTHON="$APP_DIR/venv/bin/python"

# Create desktop entry directly in the system applications directory
cat > /usr/share/applications/desk-controller.desktop << EOL
[Desktop Entry]
Name=Desk Controller
Comment=Button dashboard for Raspberry Pi
Exec=$VENV_PYTHON $APP_DIR/main.py
Icon=$APP_DIR/icons/app-icon.png
Terminal=false
Type=Application
Categories=Utility;
X-KeepTerminal=false
EOL

# Create systemd service file
cat > /etc/systemd/system/desk-controller.service << EOL
[Unit]
Description=Desk Controller Service
After=network.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_PYTHON $APP_DIR/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
systemctl daemon-reload
systemctl enable desk-controller.service
systemctl start desk-controller.service

echo "Setup complete!"
echo "The application is now running as service user $SERVICE_USER"
echo "To check status: sudo systemctl status desk-controller" 