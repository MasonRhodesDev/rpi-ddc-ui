#!/usr/bin/env python3
import sys
import os
import argparse
import traceback
import signal
import subprocess
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QGuiApplication, QCursor
from PyQt5.QtCore import QTimer, QPoint, QEvent

# Force the use of X11 instead of Wayland
os.environ["QT_QPA_PLATFORM"] = "xcb"

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from src.config import load_config, get_config_path, ConfigValidator
from src.system import detect_touch_screen
from src.gui import DeskControllerUI

# Global application reference
app = None
window = None

def signal_handler(sig, frame):
    """Handle keyboard interrupts gracefully"""
    print("\nKeyboard interrupt received. Shutting down...")
    if app:
        app.quit()
    else:
        sys.exit(0)

def install_service():
    """Install the application as a kiosk service with auto-start on boot"""
    try:
        print("Installing desk-controller as a kiosk service with auto-start on boot...")
        
        # Get the current script's absolute path
        script_path = os.path.abspath(__file__)
        base_dir = os.path.dirname(script_path)
        current_user = os.getenv('USER', 'pi')
        
        # Install dependencies for kiosk mode
        print("Installing dependencies for kiosk mode...")
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'xserver-xorg', 'x11-xserver-utils', 
                          'xinit', 'matchbox-window-manager', 'unclutter', 'xserver-xorg-legacy',
                          'udev', 'ddcutil', 'i2c-tools', 'i2c-dev'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not install all dependencies: {e}")
            print("You may need to manually install the required packages")

        # Create udev rule for TTY devices
        print("Creating udev rules for TTY devices...")
        udev_rule = 'KERNEL=="tty[0-9]*", MODE="0666"\n'
        udev_file = '/etc/udev/rules.d/99-tty.rules'
        
        with open('/tmp/99-tty.rules', 'w') as f:
            f.write(udev_rule)
        subprocess.run(['sudo', 'cp', '/tmp/99-tty.rules', udev_file], check=True)
        
        # Create udev rule for DRM devices
        drm_rule = 'SUBSYSTEM=="drm", MODE="0666"\n'
        with open('/tmp/99-drm.rules', 'w') as f:
            f.write(drm_rule)
        subprocess.run(['sudo', 'cp', '/tmp/99-drm.rules', '/etc/udev/rules.d/99-drm.rules'], check=True)
        
        # Reload udev rules
        subprocess.run(['sudo', 'udevadm', 'control', '--reload'], check=True)
        subprocess.run(['sudo', 'udevadm', 'trigger'], check=True)

        # Add user to required groups
        print("Adding user to required groups...")
        groups = ['tty', 'video', 'input', 'render', 'dialout']
        for group in groups:
            try:
                subprocess.run(['sudo', 'usermod', '-a', '-G', group, current_user], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not add user to group {group}: {e}")

        # Check available video drivers
        try:
            print("Checking available video drivers...")
            drivers = subprocess.check_output(['find', '/usr/lib/xorg/modules/drivers/', '-name', '*.so'])
            print(f"Available video drivers: {drivers.decode()}")
            
            # Try to detect the graphics hardware
            lspci = subprocess.run(['lspci'], capture_output=True, text=True)
            print(f"Graphics hardware:\n{lspci.stdout}")
        except Exception as e:
            print(f"Warning: Could not check video drivers: {e}")

        # Install additional video drivers
        try:
            print("Installing additional video drivers...")
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 
                          'xserver-xorg-video-fbdev',
                          'xserver-xorg-video-modesetting'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not install video drivers: {e}")

        # Updated X server configuration for Raspberry Pi
        xorg_conf = """Section "ServerFlags"
    Option "DontVTSwitch" "true"
    Option "DontZap"      "true"
EndSection

Section "ServerLayout"
    Identifier "Layout0"
    Screen 0 "Screen0"
EndSection

Section "Monitor"
    Identifier "Monitor0"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "Card0"
    Monitor "Monitor0"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
    EndSubSection
EndSection

Section "Device"
    Identifier "Card0"
    Driver "modesetting"
EndSection
"""
        
        # Create X configuration directory
        subprocess.run(['sudo', 'mkdir', '-p', '/etc/X11/xorg.conf.d'], check=True)
        
        # Write X configuration
        with open('/tmp/99-kiosk.conf', 'w') as f:
            f.write(xorg_conf)
        subprocess.run(['sudo', 'cp', '/tmp/99-kiosk.conf', '/etc/X11/xorg.conf.d/99-kiosk.conf'], check=True)

        # Configure X wrapper
        xwrapper_content = """allowed_users=anybody
needs_root_rights=no"""
        with open('/tmp/Xwrapper.config', 'w') as f:
            f.write(xwrapper_content)
        subprocess.run(['sudo', 'cp', '/tmp/Xwrapper.config', '/etc/X11/Xwrapper.config'], check=True)
        
        # Updated .xinitrc content with touch screen resolution handling
        xinitrc_content = f"""#!/bin/sh

# Debug logging
exec 1> /home/mason/.xinitrc.log 2>&1

echo "Starting .xinitrc at $(date)"

# Error handling
set -x

# Wait for X server to be ready
sleep 3

# Export display explicitly
export DISPLAY=:0

# Basic X configuration
echo "Configuring X server settings..."
xset s off || echo "Warning: could not disable screen saver"
xset -dpms || echo "Warning: could not disable DPMS"

# Try alternative screen blanking prevention
xset s noblank || echo "Warning: could not set noblank"

# Get display information for debugging
echo "Display information:"
xrandr || echo "Warning: xrandr failed"

# Configure touch screen resolution
echo "Configuring touch screen resolution..."
# First try to find DSI display
TOUCH_SCREEN=$(xrandr | grep -w connected | grep -i 'DSI' | head -n 1 | cut -d ' ' -f 1)
if [ -z "$TOUCH_SCREEN" ]; then
    # If no DSI display, try HDMI
    TOUCH_SCREEN=$(xrandr | grep -w connected | grep -i 'HDMI' | head -n 1 | cut -d ' ' -f 1)
fi

if [ ! -z "$TOUCH_SCREEN" ]; then
    # Get the preferred resolution of the touch screen
    PREFERRED_MODE=$(xrandr | grep -A 1 "^$TOUCH_SCREEN connected" | grep -oP '\\d+x\\d+' | head -n 1)
    if [ ! -z "$PREFERRED_MODE" ]; then
        echo "Setting $TOUCH_SCREEN to $PREFERRED_MODE"
        xrandr --output $TOUCH_SCREEN --mode $PREFERRED_MODE --primary
        
        # Turn off only HDMI displays if we're using DSI
        if echo "$TOUCH_SCREEN" | grep -qi "DSI"; then
            for display in $(xrandr | grep -w connected | grep -i "HDMI" | cut -d ' ' -f 1); do
                echo "Turning off HDMI display $display"
                xrandr --output $display --off
            done
        fi
    else
        echo "Warning: Could not determine preferred mode for $TOUCH_SCREEN"
    fi
else
    echo "Warning: Could not identify touch screen display"
fi

# Start the window manager
echo "Starting window manager..."
matchbox-window-manager -use_titlebar no -use_cursor no &

# Wait for window manager
sleep 2

# Hide cursor only if not using touch screen
if ! python3 -c "from src.system import detect_touch_screen; exit(0 if detect_touch_screen() else 1)"; then
    if command -v unclutter >/dev/null 2>&1; then
        echo "Starting unclutter..."
        unclutter -idle 0 -root &
    else
        echo "Warning: unclutter not found"
    fi
fi

# Start the application
echo "Starting desk-controller application..."
cd {base_dir}
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version)"
echo "DISPLAY: $DISPLAY"
echo "Running: python3 {script_path} --kiosk"

# Run the application with error handling and restart on crash
while true; do
    python3 {script_path} --kiosk
    EXIT_CODE=$?
    echo "Application exited with code $EXIT_CODE at $(date)" >> /tmp/app-crashes.log
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Clean exit, shutting down..."
        break
    fi
    
    echo "Application crashed, restarting in 5 seconds..."
    sleep 5
done
"""
        xinitrc_file = os.path.expanduser('~/.xinitrc')
        with open(xinitrc_file, 'w') as f:
            f.write(xinitrc_content)
        os.chmod(xinitrc_file, 0o755)
        
        # Add to .bashrc
        bashrc_content = """
# Auto-start X on TTY1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    echo "Starting X server on TTY1 at $(date)" >> /tmp/startup.log
    exec startx -- vt1 -keeptty >> /tmp/startup.log 2>&1
fi
"""
        with open(os.path.expanduser('~/.bashrc'), 'a') as f:
            f.write(bashrc_content)
        
        # Set up auto-login
        print("Setting up auto-login on TTY1...")
        getty_override_dir = '/etc/systemd/system/getty@tty1.service.d'
        subprocess.run(['sudo', 'mkdir', '-p', getty_override_dir], check=True)
        
        autologin_content = f"""[Service]
ExecStart=
ExecStart=-/sbin/agetty --skip-login --nonewline --noissue --autologin {current_user} --noclear %I $TERM
Type=idle
"""
        with open('/tmp/override.conf', 'w') as f:
            f.write(autologin_content)
        subprocess.run(['sudo', 'cp', '/tmp/override.conf', f'{getty_override_dir}/override.conf'], check=True)

        # Enable I2C interface
        print("Enabling I2C interface...")
        try:
            # Add i2c-dev to /etc/modules
            if not os.path.exists('/etc/modules-load.d'):
                subprocess.run(['sudo', 'mkdir', '-p', '/etc/modules-load.d'], check=True)
            
            with open('/tmp/i2c.conf', 'w') as f:
                f.write('i2c-dev\n')
            subprocess.run(['sudo', 'cp', '/tmp/i2c.conf', '/etc/modules-load.d/i2c.conf'], check=True)
            
            # Enable I2C in raspi-config
            subprocess.run(['sudo', 'raspi-config', 'nonint', 'do_i2c', '0'], check=True)
            
            # Add i2c to bootconfig
            with open('/boot/config.txt', 'r') as f:
                bootconfig = f.read()
            
            if 'dtparam=i2c_arm=on' not in bootconfig:
                with open('/tmp/config.txt', 'w') as f:
                    f.write(bootconfig.strip() + '\ndtparam=i2c_arm=on\n')
                subprocess.run(['sudo', 'cp', '/tmp/config.txt', '/boot/config.txt'], check=True)
            
            print("I2C interface enabled. A reboot will be required.")
            
        except Exception as e:
            print(f"Warning: Could not enable I2C interface: {e}")
            print("You may need to manually enable I2C using 'sudo raspi-config'")

        print("\nKiosk mode installation complete!")
        print("\nNOTE: You need to log out and back in for the group changes to take effect.")
        print("      After that, reboot the system to start in kiosk mode.")
        
        # Ask if the user wants to log out now
        try:
            response = input("Would you like to reboot now to apply the changes? (y/n): ")
            if response.lower() in ['y', 'yes']:
                print("Rebooting...")
                subprocess.run(['sudo', 'reboot'], check=True)
            else:
                print("Please log out manually when convenient.")
        except:
            pass
        
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Error installing kiosk mode: {e}")
        print(f"Command output: {e.output if hasattr(e, 'output') else 'No output'}")
        return False
    except Exception as e:
        print(f"Error installing kiosk mode: {e}")
        return False

def main():
    global app, window
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Desk Controller')
    parser.add_argument('--kiosk', action='store_true', help='Run in kiosk mode')
    parser.add_argument('--touch', action='store_true', help='Force touch screen mode')
    parser.add_argument('--no-display-check', action='store_true', help='Skip display server check')
    parser.add_argument('--install-service', action='store_true', help='Install as kiosk service')
    parser.add_argument('--dev', action='store_true', help='Run in development mode (equivalent to --no-service-check)')
    args = parser.parse_args()
    
    # Development mode is equivalent to --no-service-check
    if args.dev:
        args.no_service_check = True
    
    # Check if we should install the service
    if args.install_service:
        install_service()
        return 0
    
    # Set up signal handler for keyboard interrupts (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:        
        # Debug: Print which platform we're using
        print(f"Using platform: {QGuiApplication.platformName()}")
        
        # Validate configuration before starting
        validator = ConfigValidator()
        if not validator.validate_config():
            print("Configuration validation failed. Please check your config.json file.")
            validator.print_report()
            return 1
        
        # Create application
        app = QApplication(sys.argv)
        
        # Set up a timer to process Python events, including signals
        # This ensures that SIGINT can be caught even when Qt's event loop is running
        timer = QTimer()
        timer.start(500)  # Check every 500ms
        timer.timeout.connect(lambda: None)  # Just wake up the event loop
        
        # Set application font
        font_family = "Arial"
        font_size = 12
        font = QFont(font_family, font_size)
        app.setFont(font)
        
        # Load config
        config = load_config()
        
        # Check if kiosk mode is enabled in config or command line
        kiosk_mode = args.kiosk or config.get('display', {}).get('kiosk_mode', False)
        
        # Detect touch screen or use command line flag
        has_touch_screen = args.touch or detect_touch_screen()
        
        # Create and show the UI
        window = DeskControllerUI(config, kiosk_mode=kiosk_mode, has_touch_screen=has_touch_screen)
        
        # Configure cursor confinement for touch screen mode
        if has_touch_screen:
            # Remove unclutter if running (we want to show and confine cursor)
            try:
                subprocess.run(['pkill', 'unclutter'], check=True)
            except subprocess.CalledProcessError:
                pass  # unclutter wasn't running
            
            # Ensure cursor is visible
            window.setCursor(Qt.ArrowCursor)
            
            # Confine cursor to window
            window.setMouseTracking(True)
            window.grabMouse()
            
            # Prevent cursor from leaving the window
            def confine_cursor(event):
                if event.type() == QEvent.MouseMove:
                    pos = event.pos()
                    if not window.rect().contains(pos):
                        new_pos = QPoint(
                            max(0, min(pos.x(), window.width())),
                            max(0, min(pos.y(), window.height()))
                        )
                        QCursor.setPos(window.mapToGlobal(new_pos))
                return False
            
            window.installEventFilter(window)
            window.event_filters = [confine_cursor]  # Store filter to prevent garbage collection
        
        # Start the application event loop
        print("Application started. Press Ctrl+C to exit.")
        
        # Install event filter to catch keyboard events at application level
        app.installEventFilter(window)
        
        # Run the application
        return app.exec_()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down...")
        if app:
            app.quit()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Use the return value from main() as the exit code
    sys.exit(main()) 