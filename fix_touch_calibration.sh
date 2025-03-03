#!/bin/bash

# This script maps the touch screen to the DSI-1 display

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./fix_touch_calibration.sh)"
  exit 1
fi

echo "Mapping touch screen to DSI-1 display..."

# Get the touch screen device ID
TOUCH_DEVICE_ID=$(sudo -u deskcontroller DISPLAY=:0 xinput list | grep -i "ft5x06" | grep -o "id=[0-9]*" | grep -o "[0-9]*")

if [ -z "$TOUCH_DEVICE_ID" ]; then
  echo "Error: Touch screen device not found"
  exit 1
fi

echo "Found touch screen device with ID: $TOUCH_DEVICE_ID"

# Get the DSI-1 display dimensions and position
DSI_INFO=$(sudo -u deskcontroller DISPLAY=:0 xrandr | grep "DSI-1" | grep -o "[0-9]*x[0-9]*+[0-9]*+[0-9]*")
DSI_WIDTH=$(echo $DSI_INFO | cut -d'x' -f1)
DSI_HEIGHT=$(echo $DSI_INFO | cut -d'x' -f2 | cut -d'+' -f1)
DSI_X=$(echo $DSI_INFO | cut -d'+' -f2)
DSI_Y=$(echo $DSI_INFO | cut -d'+' -f3)

if [ -z "$DSI_INFO" ]; then
  echo "Error: DSI-1 display not found or not properly configured"
  exit 1
fi

echo "DSI-1 display dimensions: ${DSI_WIDTH}x${DSI_HEIGHT} at position +${DSI_X}+${DSI_Y}"

# Get the total screen dimensions
SCREEN_INFO=$(sudo -u deskcontroller DISPLAY=:0 xrandr | grep "Screen 0" | grep -o "current [0-9]* x [0-9]*" | grep -o "[0-9]* x [0-9]*")
SCREEN_WIDTH=$(echo $SCREEN_INFO | cut -d' ' -f1)
SCREEN_HEIGHT=$(echo $SCREEN_INFO | cut -d' ' -f3)

echo "Total screen dimensions: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}"

# Calculate the transformation matrix
# The matrix maps from the full screen to the DSI display area
# [ width_scale   0            x_offset ]
# [ 0             height_scale y_offset ]
# [ 0             0            1        ]

WIDTH_SCALE=$(echo "scale=6; $DSI_WIDTH / $SCREEN_WIDTH" | bc)
HEIGHT_SCALE=$(echo "scale=6; $DSI_HEIGHT / $SCREEN_HEIGHT" | bc)
X_OFFSET=$(echo "scale=6; $DSI_X / $SCREEN_WIDTH" | bc)
Y_OFFSET=$(echo "scale=6; $DSI_Y / $SCREEN_HEIGHT" | bc)

echo "Transformation matrix:"
echo "[ $WIDTH_SCALE 0 $X_OFFSET ]"
echo "[ 0 $HEIGHT_SCALE $Y_OFFSET ]"
echo "[ 0 0 1 ]"

# Apply the transformation matrix to the touch screen
sudo -u deskcontroller DISPLAY=:0 xinput set-prop $TOUCH_DEVICE_ID "Coordinate Transformation Matrix" $WIDTH_SCALE 0 $X_OFFSET 0 $HEIGHT_SCALE $Y_OFFSET 0 0 1

echo "Touch screen calibration applied!"

# Create a systemd service to apply this on boot
cat > /etc/systemd/system/touch-calibration.service << EOL
[Unit]
Description=Touch Screen Calibration Service
After=kiosk.service
Wants=kiosk.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'sleep 10 && /opt/desk-controller/fix_touch_calibration.sh'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOL

# Make the script executable
chmod +x /etc/systemd/system/touch-calibration.service

# Enable the service
systemctl daemon-reload
systemctl enable touch-calibration.service

echo "Touch calibration service installed and enabled!"
echo "The touch screen will be automatically calibrated on boot."
echo "To apply the calibration now, reboot the system or restart the kiosk service." 