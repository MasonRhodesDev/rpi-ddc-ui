#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./setup_kiosk.sh)"
  exit 1
fi

echo "Setting up kiosk mode for Desk Controller..."

# Define service user and paths
SERVICE_USER="deskcontroller"
APP_DIR="/opt/desk-controller"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Detect display manager
if [ -f /etc/systemd/system/display-manager.service ]; then
    DISPLAY_MANAGER=$(basename $(readlink /etc/systemd/system/display-manager.service) .service)
    echo "Detected display manager: $DISPLAY_MANAGER"
    
    # Disable the display manager
    echo "Disabling display manager: $DISPLAY_MANAGER"
    systemctl disable $DISPLAY_MANAGER
else
    echo "No display manager detected."
fi

# Install required packages for kiosk mode
echo "Installing required packages for kiosk mode..."
apt-get update
apt-get install -y unclutter x11-xserver-utils python3-pyqt5 python3-json5 openbox jq

# Verify application directory and config.json
echo "Verifying application directory and config.json..."
if [ ! -d "$APP_DIR" ]; then
    echo "Error: Application directory $APP_DIR does not exist"
    exit 1
fi

if [ ! -f "$APP_DIR/config.json" ]; then
    echo "Error: config.json not found in $APP_DIR"
    exit 1
fi

if [ ! -f "$APP_DIR/main.py" ]; then
    echo "Error: main.py not found in $APP_DIR"
    exit 1
fi

# Ensure correct permissions
chmod 644 $APP_DIR/config.json
chmod +x $APP_DIR/main.py
echo "Verified application files exist and have correct permissions"

# Copy test script and run it
cp test_config.py $APP_DIR/ 2>/dev/null || true
chmod +x $APP_DIR/test_config.py
echo "Running configuration test..."
cd $APP_DIR
python3 $APP_DIR/test_config.py
if [ $? -ne 0 ]; then
    echo "Configuration test failed! Please check the config.json file."
    exit 1
fi
echo "Configuration test passed!"

# Extract display configuration from config.json
echo "Extracting display configuration from config.json..."
if command -v jq >/dev/null; then
    # Use jq to extract display configuration
    DISPLAY_MODE=$(jq -r '.display.mode // "single"' $APP_DIR/config.json)
    PRIMARY_DISPLAY=$(jq -r '.display.primary_display // ""' $APP_DIR/config.json)
    echo "Display mode: $DISPLAY_MODE"
    echo "Primary display: $PRIMARY_DISPLAY"
else
    # Fallback to default values if jq is not available
    echo "jq not found, using default display configuration"
    DISPLAY_MODE="single"
    PRIMARY_DISPLAY="DSI-1"
fi

# Save display configuration for future use (for backward compatibility)
echo "Saving display configuration..."
mkdir -p $APP_DIR/config
cat > $APP_DIR/config/display.conf << EOL
# Display configuration saved on $(date)
DISPLAY_MODE="$DISPLAY_MODE"
PRIMARY_DISPLAY="$PRIMARY_DISPLAY"
EOL
chmod 644 $APP_DIR/config/display.conf
chown $SERVICE_USER:$SERVICE_USER $APP_DIR/config/display.conf
echo "Display configuration saved to $APP_DIR/config/display.conf"

# Create the display configuration script
echo "Creating display configuration script..."
mkdir -p $APP_DIR
cat > $APP_DIR/configure_displays.sh << 'EOL'
#!/bin/bash

# This script configures displays for kiosk mode
# It can either mirror displays, extend across all monitors, or use a single display

# Load saved configuration if available
if [ -f "/opt/desk-controller/config/display.conf" ]; then
    source "/opt/desk-controller/config/display.conf"
fi

# Configuration mode: "mirror", "extend", or "single"
MODE="${DISPLAY_MODE:-mirror}"

# If single mode, specify which display to use
PRIMARY_DISPLAY="${PRIMARY_DISPLAY:-}"

# Wait for X server to be fully initialized
sleep 5

# Get list of connected displays
DISPLAYS=$(xrandr | grep " connected" | awk '{print $1}')
DISPLAY_COUNT=$(echo "$DISPLAYS" | wc -l)

# Log file for debugging
LOG_FILE="/home/deskcontroller/display_config.log"

# Log the connected displays
echo "Display configuration started at $(date)" > $LOG_FILE
echo "Connected displays:" >> $LOG_FILE
xrandr | grep " connected" >> $LOG_FILE
echo "Display count: $DISPLAY_COUNT" >> $LOG_FILE
echo "Mode: $MODE" >> $LOG_FILE
if [ "$MODE" = "single" ]; then
    echo "Primary display: $PRIMARY_DISPLAY" >> $LOG_FILE
fi

# Function to get display resolution
get_resolution() {
    xrandr | grep "^$1" -A1 | grep -oP '\d+x\d+' | head -1
}

# Configure displays based on mode
if [ "$MODE" = "mirror" ]; then
    echo "Configuring displays in mirror mode" >> $LOG_FILE
    
    # Find the first display as primary
    PRIMARY=$(echo "$DISPLAYS" | head -1)
    echo "Primary display: $PRIMARY" >> $LOG_FILE
    
    # Get the resolution of the primary display
    PRIMARY_RES=$(get_resolution $PRIMARY)
    echo "Primary resolution: $PRIMARY_RES" >> $LOG_FILE
    
    # Set up mirroring for all displays
    for DISPLAY in $DISPLAYS; do
        if [ "$DISPLAY" != "$PRIMARY" ]; then
            echo "Mirroring $DISPLAY to match $PRIMARY" >> $LOG_FILE
            xrandr --output $DISPLAY --same-as $PRIMARY --mode $PRIMARY_RES
        fi
    done
    
    # Ensure primary is set
    xrandr --output $PRIMARY --primary --mode $PRIMARY_RES
    
elif [ "$MODE" = "extend" ]; then
    echo "Configuring displays in extend mode" >> $LOG_FILE
    
    # Find the first display as primary
    PRIMARY=$(echo "$DISPLAYS" | head -1)
    echo "Primary display: $PRIMARY" >> $LOG_FILE
    
    # Get the resolution of the primary display
    PRIMARY_RES=$(get_resolution $PRIMARY)
    echo "Primary resolution: $PRIMARY_RES" >> $LOG_FILE
    
    # Set primary display
    xrandr --output $PRIMARY --primary --mode $PRIMARY_RES
    
    # Position is used to place displays side by side
    POSITION=0
    
    # Configure each additional display
    for DISPLAY in $DISPLAYS; do
        if [ "$DISPLAY" != "$PRIMARY" ]; then
            # Get this display's resolution
            DISPLAY_RES=$(get_resolution $DISPLAY)
            echo "Configuring $DISPLAY with resolution $DISPLAY_RES" >> $LOG_FILE
            
            # Position this display to the right of the previous one
            xrandr --output $DISPLAY --mode $DISPLAY_RES --pos ${POSITION}x0 --rotate normal
            
            # Update position for next display
            WIDTH=$(echo $DISPLAY_RES | cut -d'x' -f1)
            POSITION=$((POSITION + WIDTH))
        fi
    done
elif [ "$MODE" = "single" ]; then
    echo "Configuring to use only $PRIMARY_DISPLAY" >> $LOG_FILE
    
    # If PRIMARY_DISPLAY is not set, use the first detected display
    if [ -z "$PRIMARY_DISPLAY" ]; then
        PRIMARY_DISPLAY=$(echo "$DISPLAYS" | head -1)
        echo "No primary display specified, using first detected: $PRIMARY_DISPLAY" >> $LOG_FILE
    fi
    
    # Turn off all displays except the primary one
    for DISPLAY in $DISPLAYS; do
        if [ "$DISPLAY" = "$PRIMARY_DISPLAY" ]; then
            echo "Setting $DISPLAY as primary" >> $LOG_FILE
            xrandr --output "$DISPLAY" --auto --primary
        else
            echo "Turning off $DISPLAY" >> $LOG_FILE
            xrandr --output "$DISPLAY" --off
        fi
    done
fi

echo "Display configuration completed at $(date)" >> $LOG_FILE
exit 0
EOL
chmod +x $APP_DIR/configure_displays.sh
chown $SERVICE_USER:$SERVICE_USER $APP_DIR/configure_displays.sh

# Create kiosk session
echo "Creating kiosk session..."
mkdir -p /usr/share/xsessions/
cat > /usr/share/xsessions/kiosk.desktop << EOL
[Desktop Entry]
Name=Kiosk
Comment=Kiosk session for Desk Controller
Exec=/etc/X11/Xsession
Type=Application
EOL
chmod 644 /usr/share/xsessions/kiosk.desktop

# Create .xsession file for the service user
echo "Creating .xsession file for $SERVICE_USER..."
mkdir -p /home/$SERVICE_USER
cat > /home/$SERVICE_USER/.xsession << 'EOL'
#!/bin/sh
# Log file for debugging
XSESSION_LOG="/home/deskcontroller/xsession.log"
echo "X session started at $(date)" > $XSESSION_LOG

# Disable screen saver and energy saving
echo "Disabling screen saver and energy saving" >> $XSESSION_LOG
xset s off
xset s noblank
xset -dpms

# Configure displays
echo "Configuring displays" >> $XSESSION_LOG
/opt/desk-controller/configure_displays.sh >> $XSESSION_LOG 2>&1

# Hide cursor after 5 seconds of inactivity
echo "Setting up cursor auto-hide" >> $XSESSION_LOG
unclutter -idle 5 &

# Set window manager to openbox if available
if command -v openbox >/dev/null; then
    echo "Starting openbox window manager" >> $XSESSION_LOG
    # Create a minimal openbox configuration
    mkdir -p /home/deskcontroller/.config/openbox
    cat > /home/deskcontroller/.config/openbox/rc.xml << OPENBOX_CONFIG
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <resistance>
    <strength>10</strength>
    <screen_edge_strength>20</screen_edge_strength>
  </resistance>
  <focus>
    <focusNew>yes</focusNew>
    <followMouse>no</followMouse>
  </focus>
  <placement>
    <policy>Smart</policy>
  </placement>
  <theme>
    <name>Clearlooks</name>
    <keepBorder>yes</keepBorder>
    <animateIconify>yes</animateIconify>
  </theme>
  <keyboard>
    <keybind key="A-F4">
      <action name="Close"/>
    </keybind>
  </keyboard>
  <mouse>
    <dragThreshold>1</dragThreshold>
    <doubleClickTime>500</doubleClickTime>
  </mouse>
  <applications>
  </applications>
</openbox_config>
OPENBOX_CONFIG
    chown -R deskcontroller:deskcontroller /home/deskcontroller/.config
    
    # Start openbox
    openbox-session &
fi

# Wait for window manager to initialize
sleep 2

# Start the Python Qt application in fullscreen mode
echo "Starting desk controller application in kiosk mode" >> $XSESSION_LOG
cd /opt/desk-controller
python3 /opt/desk-controller/main.py --kiosk >> $XSESSION_LOG 2>&1
APP_EXIT_CODE=$?

# Log the exit code
echo "Application exited with code $APP_EXIT_CODE at $(date)" >> $XSESSION_LOG

# If the application crashed, wait before restarting to avoid rapid restart loops
if [ $APP_EXIT_CODE -ne 0 ]; then
    echo "Application crashed, waiting 10 seconds before allowing restart" >> $XSESSION_LOG
    sleep 10
fi

# Keep the session alive with a simple loop to prevent rapid restarts
while true; do
    echo "X session waiting at $(date)" >> $XSESSION_LOG
    sleep 60
done
EOL
chmod +x /home/$SERVICE_USER/.xsession
chown $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER/.xsession

# Set up sudoers file for the service user
echo "Setting up sudoers file for $SERVICE_USER..."
cat > /etc/sudoers.d/deskcontroller << EOL
# Desk Controller permissions
# Allow deskcontroller user to run necessary commands without password
deskcontroller ALL=(ALL) NOPASSWD: /usr/bin/chvt
deskcontroller ALL=(ALL) NOPASSWD: /usr/bin/xrandr
deskcontroller ALL=(ALL) NOPASSWD: /sbin/reboot
deskcontroller ALL=(ALL) NOPASSWD: /sbin/shutdown
deskcontroller ALL=(ALL) NOPASSWD: /sbin/poweroff
deskcontroller ALL=(ALL) NOPASSWD: /sbin/halt
EOL
chmod 440 /etc/sudoers.d/deskcontroller

# Install systemd service
echo "Installing systemd service..."
cat > /etc/systemd/system/kiosk.service << EOL
[Unit]
Description=Kiosk Mode Service for Desk Controller
After=network.target
Wants=graphical.target
After=graphical.target

[Service]
User=deskcontroller
WorkingDirectory=/home/deskcontroller
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/deskcontroller/.Xauthority
ExecStartPre=/usr/bin/sudo /usr/bin/chvt 7
ExecStart=/usr/bin/xinit /home/deskcontroller/.xsession -- :0 -nolisten tcp vt7
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOL
systemctl daemon-reload
systemctl enable kiosk.service

# Set up autologin for the service user
echo "Setting up autologin for $SERVICE_USER..."
mkdir -p /etc/systemd/system/getty@tty1.service.d/
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOL'
# Autologin configuration for deskcontroller user

[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin deskcontroller --noclear %I $TERM
EOL
chmod 644 /etc/systemd/system/getty@tty1.service.d/override.conf

# Create .xinitrc file to automatically start X on login
echo "Creating .bash_profile for $SERVICE_USER to auto-start X..."
cat > /home/$SERVICE_USER/.bash_profile << 'EOL'
# Auto-start X on login to tty1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec startx
fi
EOL
chmod +x /home/$SERVICE_USER/.bash_profile
chown $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER/.bash_profile

# Modify service user to allow X11 login
echo "Configuring service user for X11 login..."
usermod -s /bin/bash $SERVICE_USER

# Add user to necessary groups
echo "Adding $SERVICE_USER to necessary groups..."
usermod -a -G video,audio,input,tty,dialout,gpio $SERVICE_USER

echo "Kiosk mode setup complete!"
echo "The system will now boot directly into the Desk Controller application."
echo "Reboot the system to apply changes: sudo reboot" 