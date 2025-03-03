#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./update_app.sh)"
  exit 1
fi

echo "Updating Desk Controller application..."

# Check if PIL/Pillow is installed, install if missing using apt
echo "Checking for required dependencies..."
if ! python3 -c "import PIL" &>/dev/null; then
  echo "PIL/Pillow not found. Installing using apt..."
  apt-get update
  apt-get install -y python3-pil
  if [ $? -ne 0 ]; then
    echo "Failed to install python3-pil. Icon generation will be skipped."
    SKIP_ICON_GEN=true
  else
    echo "python3-pil installed successfully."
  fi
else
  echo "PIL/Pillow is already installed."
fi

# Run the icon generation script first
if [ "$SKIP_ICON_GEN" != "true" ]; then
  echo "Generating icons..."
  if python3 create_icons.py; then
    echo "Icons generated successfully!"
  else
    echo "Icon generation failed. Continuing with update..."
  fi
else
  echo "Skipping icon generation due to missing dependencies."
fi

# Copy the updated main.py file
cp main.py /opt/desk-controller/
chmod +x /opt/desk-controller/main.py
chown deskcontroller:deskcontroller /opt/desk-controller/main.py

# Copy the config.json file if it exists
if [ -f "config.json" ]; then
  echo "Updating configuration file..."
  
  # Create a backup of the original config
  cp config.json config.json.bak
  
  # Temporarily modify the config to enable cursor for debugging touch issues
  if command -v jq &> /dev/null; then
    echo "Temporarily enabling cursor for touch debugging..."
    jq '.layout.hide_cursor = false' config.json > config.json.tmp && mv config.json.tmp config.json
  else
    echo "jq not found, installing..."
    apt-get update
    apt-get install -y jq
    echo "Temporarily enabling cursor for touch debugging..."
    jq '.layout.hide_cursor = false' config.json > config.json.tmp && mv config.json.tmp config.json
  fi
  
  cp config.json /opt/desk-controller/
  chown deskcontroller:deskcontroller /opt/desk-controller/config.json
  echo "Configuration file updated!"
  
  # Restore the original config for future updates
  mv config.json.bak config.json
fi

# Update scripts directory if it exists
if [ -d "scripts" ]; then
  echo "Updating scripts directory..."
  # Create scripts directory if it doesn't exist in the destination
  mkdir -p /opt/desk-controller/scripts
  # Copy all scripts to the installation directory
  cp -r scripts/* /opt/desk-controller/scripts/ 2>/dev/null || true
  # Make all scripts executable
  chmod +x /opt/desk-controller/scripts/*.sh 2>/dev/null || true
  # Set ownership
  chown -R deskcontroller:deskcontroller /opt/desk-controller/scripts
  echo "Scripts directory updated!"
fi

# Copy the generated icons to the installation directory
if [ -d "icons" ]; then
  echo "Updating icons directory..."
  # Create icons directory if it doesn't exist in the destination
  mkdir -p /opt/desk-controller/icons
  # Copy all icons to the installation directory
  cp -r icons/* /opt/desk-controller/icons/ 2>/dev/null || true
  # Set ownership
  chown -R deskcontroller:deskcontroller /opt/desk-controller/icons
  echo "Icons directory updated!"
fi

# Find the current Python process
PID=$(ps aux | grep python | grep main.py | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
  echo "Killing current process (PID: $PID)..."
  kill -9 $PID
  sleep 2
fi

# Ensure DISPLAY environment variable is set
export DISPLAY=:0

# Install required packages for touch input
echo "Installing required packages for touch input..."
apt-get update
apt-get install -y xinput x11-xserver-utils xserver-xorg-input-libinput evtest

# Configure touch input
echo "Configuring touch input..."

# Create a comprehensive touch setup script
cat > /tmp/setup_touch.sh << 'EOL'
#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/deskcontroller/.Xauthority

echo "===== DISPLAY INFORMATION ====="
xrandr --verbose

echo "===== INPUT DEVICES ====="
xinput list

echo "===== TOUCH DEVICE DETECTION ====="
# Look for touch devices with a broader search
TOUCH_DEVICES=$(xinput list | grep -i -E 'touch|FTSC|ELAN|FTS|Goodix|hid|usb' | grep -i -E 'pointer|touchscreen' | sed -n 's/.*id=\([0-9]*\).*/\1/p')

if [ -z "$TOUCH_DEVICES" ]; then
  echo "No touch devices found with standard search, trying broader search..."
  # Try a broader search for any pointer device
  TOUCH_DEVICES=$(xinput list | grep -i pointer | sed -n 's/.*id=\([0-9]*\).*/\1/p')
fi

if [ -n "$TOUCH_DEVICES" ]; then
  echo "Found touch/pointer devices: $TOUCH_DEVICES"
  
  # Always use DSI-1 as the target display regardless of primary status
  TARGET_DISPLAY="DSI-1"
  
  # Check if DSI-1 is connected
  if ! xrandr | grep -q "^$TARGET_DISPLAY connected"; then
    echo "WARNING: $TARGET_DISPLAY not found in connected displays!"
    echo "Available displays:"
    xrandr | grep " connected"
    
    # Fallback to primary display if DSI-1 not found
    PRIMARY_DISPLAY=$(xrandr | grep -w connected | grep primary | cut -d' ' -f1)
    if [ -n "$PRIMARY_DISPLAY" ]; then
      echo "Falling back to primary display: $PRIMARY_DISPLAY"
      TARGET_DISPLAY=$PRIMARY_DISPLAY
    else
      # Last resort: use first connected display
      FIRST_DISPLAY=$(xrandr | grep -w connected | head -n 1 | cut -d' ' -f1)
      if [ -n "$FIRST_DISPLAY" ]; then
        echo "Falling back to first connected display: $FIRST_DISPLAY"
        TARGET_DISPLAY=$FIRST_DISPLAY
      fi
    fi
  fi
  
  echo "Using target display for touch input: $TARGET_DISPLAY"
  
  # Get the geometry of the target display
  DISPLAY_INFO=$(xrandr | grep "^$TARGET_DISPLAY" -A1 | grep -oP '\d+x\d+\+\d+\+\d+')
  if [ -n "$DISPLAY_INFO" ]; then
    echo "Display geometry: $DISPLAY_INFO"
    
    # Extract width, height, x offset, y offset
    WIDTH=$(echo $DISPLAY_INFO | grep -oP '\d+x' | grep -oP '\d+')
    HEIGHT=$(echo $DISPLAY_INFO | grep -oP 'x\d+' | grep -oP '\d+')
    X_OFFSET=$(echo $DISPLAY_INFO | grep -oP '\+\d+\+' | grep -oP '\d+')
    Y_OFFSET=$(echo $DISPLAY_INFO | grep -oP '\+\d+$' | grep -oP '\d+')
    
    echo "Width: $WIDTH, Height: $HEIGHT, X offset: $X_OFFSET, Y offset: $Y_OFFSET"
  else
    echo "Could not determine display geometry for $TARGET_DISPLAY"
  fi
  
  for DEVICE_ID in $TOUCH_DEVICES; do
    echo "===== CONFIGURING DEVICE ID: $DEVICE_ID ====="
    
    # Get device name
    DEVICE_NAME=$(xinput list --name $DEVICE_ID)
    echo "Device name: $DEVICE_NAME"
    
    # Enable the device
    xinput enable $DEVICE_ID
    echo "Device enabled"
    
    # List device properties
    echo "Device properties:"
    xinput list-props $DEVICE_ID
    
    # Try to set common touch properties
    echo "Setting touch properties..."
    xinput set-prop $DEVICE_ID "libinput Tapping Enabled" 1 2>/dev/null || echo "Failed to set Tapping Enabled"
    xinput set-prop $DEVICE_ID "libinput Touch Drag Enabled" 1 2>/dev/null || echo "Failed to set Touch Drag Enabled"
    xinput set-prop $DEVICE_ID "libinput Disable While Typing Enabled" 0 2>/dev/null || echo "Failed to set Disable While Typing"
    
    # Map to target display (DSI-1)
    echo "Mapping to display: $TARGET_DISPLAY"
    
    # Try multiple mapping methods in order of preference
    
    # Method 1: Direct mapping to output (most reliable when it works)
    echo "Trying direct output mapping..."
    xinput map-to-output $DEVICE_ID $TARGET_DISPLAY 2>/dev/null
    MAP_RESULT=$?
    
    if [ $MAP_RESULT -ne 0 ]; then
      echo "Direct mapping failed, trying coordinate transformation matrix..."
      
      # Method 2: Calculate transformation matrix if we have display geometry
      if [ -n "$DISPLAY_INFO" ]; then
        # Get total screen dimensions
        SCREEN_INFO=$(xrandr | grep "Screen 0" | grep -oP 'current \d+ x \d+' | grep -oP '\d+ x \d+')
        SCREEN_WIDTH=$(echo $SCREEN_INFO | cut -d' ' -f1)
        SCREEN_HEIGHT=$(echo $SCREEN_INFO | cut -d' ' -f3)
        
        echo "Screen dimensions: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}"
        
        # Calculate transformation matrix
        # Formula: [width_scale, 0, x_offset, 0, height_scale, y_offset, 0, 0, 1]
        # where width_scale = display_width / screen_width
        #       height_scale = display_height / screen_height
        #       x_offset = display_x_offset / screen_width
        #       y_offset = display_y_offset / screen_height
        
        WIDTH_SCALE=$(echo "scale=6; $WIDTH / $SCREEN_WIDTH" | bc)
        HEIGHT_SCALE=$(echo "scale=6; $HEIGHT / $SCREEN_HEIGHT" | bc)
        X_OFFSET_SCALE=$(echo "scale=6; $X_OFFSET / $SCREEN_WIDTH" | bc)
        Y_OFFSET_SCALE=$(echo "scale=6; $Y_OFFSET / $SCREEN_HEIGHT" | bc)
        
        echo "Transformation matrix values:"
        echo "Width scale: $WIDTH_SCALE"
        echo "Height scale: $HEIGHT_SCALE"
        echo "X offset scale: $X_OFFSET_SCALE"
        echo "Y offset scale: $Y_OFFSET_SCALE"
        
        # Apply the transformation matrix
        xinput set-prop $DEVICE_ID "Coordinate Transformation Matrix" \
          $WIDTH_SCALE 0 $X_OFFSET_SCALE 0 $HEIGHT_SCALE $Y_OFFSET_SCALE 0 0 1 2>/dev/null
        
        if [ $? -eq 0 ]; then
          echo "Applied coordinate transformation matrix successfully"
        else
          echo "Failed to apply coordinate transformation matrix"
          
          # Method 3: Last resort - try a simple 1:1 mapping
          echo "Trying simple 1:1 mapping..."
          xinput set-prop $DEVICE_ID "Coordinate Transformation Matrix" 1 0 0 0 1 0 0 0 1 2>/dev/null
          if [ $? -eq 0 ]; then
            echo "Applied simple 1:1 mapping"
          else
            echo "All mapping methods failed for device $DEVICE_ID"
          fi
        fi
      else
        # Method 3: Last resort - try a simple 1:1 mapping
        echo "No display geometry available, trying simple 1:1 mapping..."
        xinput set-prop $DEVICE_ID "Coordinate Transformation Matrix" 1 0 0 0 1 0 0 0 1 2>/dev/null
        if [ $? -eq 0 ]; then
          echo "Applied simple 1:1 mapping"
        else
          echo "All mapping methods failed for device $DEVICE_ID"
        fi
      fi
    else
      echo "Direct mapping to $TARGET_DISPLAY successful"
    fi
  done
else
  echo "ERROR: No touch devices found!"
fi

# Make sure cursor is visible
echo "Setting cursor to visible..."
xsetroot -cursor_name left_ptr

# Disable DPMS (Display Power Management Signaling)
echo "Disabling DPMS..."
xset -dpms
xset s off
xset s noblank

echo "Touch setup completed"
EOL

chmod +x /tmp/setup_touch.sh
chown deskcontroller:deskcontroller /tmp/setup_touch.sh

# Run the touch configuration script as the deskcontroller user
echo "Running touch configuration as deskcontroller user..."
sudo -u deskcontroller /tmp/setup_touch.sh > /tmp/touch_setup.log 2>&1
echo "Touch setup log saved to /tmp/touch_setup.log"

# Start the application on the correct display with debugging
echo "Starting application on DSI-1 display..."
sudo -u deskcontroller DISPLAY=:0 PYTHONUNBUFFERED=1 QT_DEBUG_PLUGINS=1 python3 /opt/desk-controller/main.py --kiosk > /tmp/app.log 2>&1 &

# Clean up
rm -f /tmp/setup_touch.sh

echo "Application updated and restarted!"
echo "Check /tmp/touch_setup.log and /tmp/app.log for debugging information" 