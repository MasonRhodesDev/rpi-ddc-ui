#!/bin/bash

# This script configures the DSI-1 display for the kiosk application

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./fix_display_config.sh)"
  exit 1
fi

echo "Configuring displays for kiosk mode..."

# Get the primary display from config.json
PRIMARY_DISPLAY=$(grep -o '"primary_display":\s*"[^"]*"' /opt/desk-controller/config.json | cut -d'"' -f4)

if [ -z "$PRIMARY_DISPLAY" ]; then
  PRIMARY_DISPLAY="DSI-1"
  echo "No primary display specified in config.json, using default: $PRIMARY_DISPLAY"
else
  echo "Using primary display from config.json: $PRIMARY_DISPLAY"
fi

# Configure the displays
echo "Configuring displays..."
sudo -u deskcontroller DISPLAY=:0 xrandr --output $PRIMARY_DISPLAY --auto --primary

# Turn off other displays if needed
# Uncomment these lines if you want to turn off other displays
# sudo -u deskcontroller DISPLAY=:0 xrandr --output HDMI-1 --off
# sudo -u deskcontroller DISPLAY=:0 xrandr --output HDMI-2 --off

echo "Display configuration applied!"

# Create a systemd service to apply this on boot
cat > /etc/systemd/system/display-config.service << EOL
[Unit]
Description=Display Configuration Service for Kiosk Mode
After=kiosk.service
Wants=kiosk.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'sleep 5 && /opt/desk-controller/fix_display_config.sh'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOL

# Make the service executable
chmod +x /etc/systemd/system/display-config.service

# Enable the service
systemctl daemon-reload
systemctl enable display-config.service

echo "Display configuration service installed and enabled!"
echo "The display will be automatically configured on boot."
echo "To apply the configuration now, reboot the system or restart the kiosk service." 