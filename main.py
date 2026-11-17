#!/usr/bin/env python3
import sys
import os
import argparse
import traceback
import signal
import subprocess
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QFont, QGuiApplication, QCursor
from PyQt5.QtCore import QTimer, QPoint, QEvent

os.environ["QT_QPA_PLATFORM"] = "xcb"

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import load_config, get_config_path, ConfigValidator
from src.system import detect_touch_screen
from src.gui import DeskControllerUI

app = None
window = None

def signal_handler(sig, frame):
    print("\nKeyboard interrupt received. Shutting down...")
    if app:
        app.quit()
    else:
        sys.exit(0)

def install_service():
    try:
        print("Installing desk-controller as a kiosk service with auto-start on boot...")
        
        script_path = os.path.abspath(__file__)
        base_dir = os.path.dirname(script_path)
        current_user = os.getenv('USER', 'pi')
        
        print("Installing dependencies for kiosk mode...")
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'xserver-xorg', 'x11-xserver-utils', 
                          'xinit', 'matchbox-window-manager', 'unclutter', 'xserver-xorg-legacy',
                          'udev', 'ddcutil', 'i2c-tools'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not install all dependencies: {e}")
            print("You may need to manually install the required packages")

        print("Creating udev rules for TTY devices...")
        udev_rule = 'KERNEL=="tty[0-9]*", MODE="0666"\n'
        udev_file = '/etc/udev/rules.d/99-tty.rules'
        
        with open('/tmp/99-tty.rules', 'w') as f:
            f.write(udev_rule)
        subprocess.run(['sudo', 'cp', '/tmp/99-tty.rules', udev_file], check=True)
        
        drm_rule = 'SUBSYSTEM=="drm", MODE="0666"\n'
        with open('/tmp/99-drm.rules', 'w') as f:
            f.write(drm_rule)
        subprocess.run(['sudo', 'cp', '/tmp/99-drm.rules', '/etc/udev/rules.d/99-drm.rules'], check=True)
        
        subprocess.run(['sudo', 'udevadm', 'control', '--reload'], check=True)
        subprocess.run(['sudo', 'udevadm', 'trigger'], check=True)

        print("Adding user to required groups...")
        groups = ['tty', 'video', 'input', 'render', 'dialout']
        for group in groups:
            try:
                subprocess.run(['sudo', 'usermod', '-a', '-G', group, current_user], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not add user to group {group}: {e}")

        try:
            print("Checking available video drivers...")
            drivers = subprocess.check_output(['find', '/usr/lib/xorg/modules/drivers/', '-name', '*.so'])
            print(f"Available video drivers: {drivers.decode()}")
            
            lspci = subprocess.run(['lspci'], capture_output=True, text=True)
            print(f"Graphics hardware:\n{lspci.stdout}")
        except Exception as e:
            print(f"Warning: Could not check video drivers: {e}")

        try:
            print("Installing additional video drivers...")
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 
                          'xserver-xorg-video-fbdev',
                          'xserver-xorg-video-modesetting'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not install video drivers: {e}")

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
        
        subprocess.run(['sudo', 'mkdir', '-p', '/etc/X11/xorg.conf.d'], check=True)
        
        with open('/tmp/99-kiosk.conf', 'w') as f:
            f.write(xorg_conf)
        subprocess.run(['sudo', 'cp', '/tmp/99-kiosk.conf', '/etc/X11/xorg.conf.d/99-kiosk.conf'], check=True)

        xwrapper_content = """allowed_users=anybody
needs_root_rights=no"""
        with open('/tmp/Xwrapper.config', 'w') as f:
            f.write(xwrapper_content)
        subprocess.run(['sudo', 'cp', '/tmp/Xwrapper.config', '/etc/X11/Xwrapper.config'], check=True)
        
        xinitrc_content = f"""#!/bin/sh

# Debug logging
exec 1> "$HOME/.xinitrc.log" 2>&1

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
        
        bashrc_content = """
# Auto-start X on TTY1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    echo "Starting X server on TTY1 at $(date)" >> /tmp/startup.log
    exec startx -- vt1 -keeptty >> /tmp/startup.log 2>&1
fi
"""
        with open(os.path.expanduser('~/.bashrc'), 'a') as f:
            f.write(bashrc_content)
        
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

        print("Enabling I2C interface...")
        try:
            if not os.path.exists('/etc/modules-load.d'):
                subprocess.run(['sudo', 'mkdir', '-p', '/etc/modules-load.d'], check=True)
            
            with open('/tmp/i2c.conf', 'w') as f:
                f.write('i2c-dev\n')
            subprocess.run(['sudo', 'cp', '/tmp/i2c.conf', '/etc/modules-load.d/i2c.conf'], check=True)
            
            subprocess.run(['sudo', 'raspi-config', 'nonint', 'do_i2c', '0'], check=True)
            
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
        
        try:
            response = input("Would you like to reboot now to apply the changes? (y/n): ")
            if response.lower() in ['y', 'yes']:
                print("Rebooting...")
                subprocess.run(['sudo', 'reboot'], check=True)
            else:
                print("Logging out to apply group changes...")
                try:
                    display = os.environ.get('DISPLAY', ':0')
                    subprocess.run(['sudo', 'pkill', '-f', f'xinit.*{display}'], check=True)
                except subprocess.CalledProcessError:
                    print("Could not automatically log out. Please log out manually.")
                print("Please remember to reboot when convenient to apply all changes.")
                print("You can reboot later using 'sudo reboot'")
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
    
    parser = argparse.ArgumentParser(description='Desk Controller')
    parser.add_argument('--kiosk', action='store_true', help='Run in kiosk mode')
    parser.add_argument('--touch', action='store_true', help='Force touch screen mode')
    parser.add_argument('--no-display-check', action='store_true', help='Skip display server check')
    parser.add_argument('--install-service', action='store_true', help='Install as kiosk service')
    parser.add_argument('--config', metavar='PATH', help='Path to config.json (default: $DESK_CONTROLLER_CONFIG, then /opt/desk-controller/config.json, then ./config.json)')
    parser.add_argument('--dev', action='store_true', help='Run in development mode (equivalent to --no-service-check)')
    args = parser.parse_args()
    
    if args.config:
        os.environ['DESK_CONTROLLER_CONFIG'] = os.path.abspath(args.config)

    if args.dev:
        args.no_service_check = True
    
    if args.install_service:
        install_service()
        return 0
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:        
        print(f"Using platform: {QGuiApplication.platformName()}")
        
        validator = ConfigValidator()
        if not validator.validate_config():
            print("Configuration validation failed. Please check your config file (see config.example.json).")
            validator.print_report()
            return 1
        
        app = QApplication(sys.argv)
        
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)
        
        font_family = "Arial"
        font_size = 12
        font = QFont(font_family, font_size)
        app.setFont(font)
        
        config = load_config()
        
        kiosk_mode = args.kiosk or config.get('display', {}).get('kiosk_mode', False)
        
        has_touch_screen = args.touch or detect_touch_screen()
        
        window = DeskControllerUI(config, kiosk_mode=kiosk_mode, has_touch_screen=has_touch_screen)
        
        if has_touch_screen:
            try:
                subprocess.run(['pkill', 'unclutter'], check=True)
            except subprocess.CalledProcessError:
                pass
            
            window.setCursor(Qt.ArrowCursor)
            
            window.setMouseTracking(True)
            window.grabMouse()
            
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
            window.event_filters = [confine_cursor]
        
        print("Application started. Press Ctrl+C to exit.")
        
        app.installEventFilter(window)
        
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
    sys.exit(main()) 