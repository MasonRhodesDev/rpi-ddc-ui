#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./fix_xorg_permissions.sh)"
  exit 1
fi

echo "Configuring X server permissions..."

# Backup the original file
if [ -f "/etc/X11/Xwrapper.config" ]; then
    cp /etc/X11/Xwrapper.config /etc/X11/Xwrapper.config.bak
    echo "Backed up original Xwrapper.config"
fi

# Create or modify Xwrapper.config
cat > /etc/X11/Xwrapper.config << EOF
# Xwrapper.config (modified for desk-controller)
allowed_users=anybody
needs_root_rights=yes
EOF

echo "Updated Xwrapper.config to allow any user to start the X server"

# Copy Xorg configuration if it exists
if [ -f "xorg.conf" ]; then
    mkdir -p /etc/X11/xorg.conf.d/
    cp xorg.conf /etc/X11/xorg.conf.d/99-desk-controller.conf
    echo "Installed Xorg configuration"
fi

# Add deskcontroller user to video and input groups
usermod -a -G video,input deskcontroller
echo "Added deskcontroller user to video and input groups"

# Restart the kiosk service
systemctl restart kiosk.service
echo "Restarted kiosk service"

echo "X server permissions configured successfully!" 