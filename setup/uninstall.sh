#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./uninstall.sh)"
  exit 1
fi

echo "Uninstalling Desk Controller..."

# Define service user and paths
SERVICE_USER="deskcontroller"
APP_DIR="/opt/desk-controller"

# Stop and disable the service if it exists
if [ -f /etc/systemd/system/desk-controller.service ]; then
    echo "Stopping and disabling desk-controller service..."
    systemctl stop desk-controller.service
    systemctl disable desk-controller.service
    rm -f /etc/systemd/system/desk-controller.service
    systemctl daemon-reload
fi

# Stop and disable the kiosk service if it exists
if [ -f /etc/systemd/system/kiosk.service ]; then
    echo "Stopping and disabling kiosk service..."
    systemctl stop kiosk.service
    systemctl disable kiosk.service
    rm -f /etc/systemd/system/kiosk.service
    systemctl daemon-reload
fi

# Remove desktop entry
echo "Removing desktop entry..."
rm -f /usr/share/applications/desk-controller.desktop

# Check for kiosk mode and remove configurations
if [ -f /usr/share/xsessions/kiosk.desktop ]; then
    echo "Removing kiosk mode configurations..."
    rm -f /usr/share/xsessions/kiosk.desktop
    
    # Remove autologin configuration
    if [ -d /etc/systemd/system/getty@tty1.service.d ]; then
        echo "Removing autologin configuration..."
        rm -f /etc/systemd/system/getty@tty1.service.d/override.conf
        rmdir --ignore-fail-on-non-empty /etc/systemd/system/getty@tty1.service.d
    fi
    
    # Restore display manager configurations
    if [ -f /etc/lightdm/lightdm.conf.backup ]; then
        mv /etc/lightdm/lightdm.conf.backup /etc/lightdm/lightdm.conf
        echo "Restored original lightdm configuration"
    fi
    
    if [ -f /etc/gdm3/custom.conf.backup ]; then
        mv /etc/gdm3/custom.conf.backup /etc/gdm3/custom.conf
        echo "Restored original gdm3 configuration"
    fi
fi

# Remove sudoers file
if [ -f /etc/sudoers.d/deskcontroller ]; then
    echo "Removing sudoers configuration..."
    rm -f /etc/sudoers.d/deskcontroller
fi

# Ask if user wants to remove the service user
read -p "Do you want to remove the service user '$SERVICE_USER'? (y/n): " remove_user
if [[ $remove_user == "y" || $remove_user == "Y" ]]; then
    echo "Removing service user $SERVICE_USER..."
    userdel -r $SERVICE_USER 2>/dev/null || echo "User $SERVICE_USER could not be removed completely"
fi

# Ask if user wants to remove the application directory
read -p "Do you want to remove the application directory '$APP_DIR'? (y/n): " remove_dir
if [[ $remove_dir == "y" || $remove_dir == "Y" ]]; then
    echo "Removing application directory..."
    rm -rf $APP_DIR
fi

echo "Uninstallation complete!"
echo "You may need to reboot the system to complete the process: sudo reboot" 