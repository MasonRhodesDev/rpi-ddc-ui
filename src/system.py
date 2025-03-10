#!/usr/bin/env python3
import os
import subprocess
from PyQt5.QtWidgets import QDesktopWidget

def is_raspberry_pi():
    """Check if the system is a Raspberry Pi"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            return 'Raspberry Pi' in model
    except:
        # Try alternative method
        try:
            output = subprocess.check_output(['cat', '/proc/cpuinfo'], text=True)
            return 'Raspberry' in output
        except:
            return False

def is_dsi_display_connected():
    """Check if a DSI display is connected"""
    try:
        # Check if DSI display is connected using tvservice
        output = subprocess.check_output(['tvservice', '-l'], text=True)
        return 'DSI' in output
    except:
        return False

def detect_touch_screen():
    """Detect if a touch screen is connected to the system"""
    try:
        # Method 1: Check xinput list for touch devices
        xinput_output = subprocess.check_output(['xinput', 'list'], text=True)
        touch_keywords = ['touch', 'TOUCH', 'Touch', 'touchscreen', 'Touchscreen']
        
        for line in xinput_output.splitlines():
            if any(keyword in line for keyword in touch_keywords):
                print(f"Touch screen detected via xinput: {line.strip()}")
                return True
        
        # Method 2: Check if evdev touch devices exist
        if os.path.exists('/dev/input/'):
            # Try to use evtest to check for touch devices
            try:
                evtest_output = subprocess.check_output(['evtest', '--query', '/dev/input/event*', 'EV_KEY', 'BTN_TOUCH'], 
                                                       stderr=subprocess.STDOUT, text=True, shell=True)
                if "supported" in evtest_output:
                    print("Touch screen detected via evtest")
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                # evtest might not be installed or might return non-zero exit code
                pass
            
            # Fallback: Check input device names directly
            try:
                for device in os.listdir('/dev/input/'):
                    if device.startswith('event'):
                        device_path = f'/dev/input/{device}'
                        try:
                            device_info = subprocess.check_output(['udevadm', 'info', '--query=property', device_path], 
                                                                 text=True, stderr=subprocess.DEVNULL)
                            if any(keyword.lower() in device_info.lower() for keyword in touch_keywords):
                                print(f"Touch screen detected via udevadm: {device_path}")
                                return True
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            pass
            except Exception as e:
                print(f"Error checking input devices: {e}")
        
        print("No touch screen detected")
        return False
    except Exception as e:
        print(f"Error in touch screen detection: {e}")
        return False

def get_screen_resolution(target_display=None):
    """Get the resolution of the target display"""
    try:
        if target_display and target_display != "":
            # Use xrandr to get the resolution of the target display
            print(f"Getting resolution for display: {target_display}")
            try:
                xrandr_output = subprocess.check_output(['xrandr'], text=True)
                for line in xrandr_output.splitlines():
                    if target_display in line and " connected" in line:
                        # Find the current resolution
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and '+' in part:
                                resolution = part.split('+')[0]
                                width, height = map(int, resolution.split('x'))
                                print(f"Found resolution for {target_display}: {width}x{height}")
                                return (width, height)
                        
                        # If we didn't find the resolution in the same line, check the next line
                        next_line_index = xrandr_output.splitlines().index(line) + 1
                        if next_line_index < len(xrandr_output.splitlines()):
                            next_line = xrandr_output.splitlines()[next_line_index]
                            if '*' in next_line:  # Current mode is marked with an asterisk
                                resolution = next_line.strip().split()[0]
                                width, height = map(int, resolution.split('x'))
                                print(f"Found resolution for {target_display} in next line: {width}x{height}")
                                return (width, height)
            except Exception as e:
                print(f"Error getting resolution from xrandr: {e}")
                # Fall back to default method
        
        # If we couldn't get the resolution from xrandr, fall back to Qt's method
        print("Falling back to Qt's screen resolution detection")
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        return (screen.width(), screen.height())
    except Exception as e:
        print(f"Error in get_screen_resolution: {e}")
        # Fall back to Qt's method in case of any error
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        return (screen.width(), screen.height())

def get_display_position(target_display):
    """Get the position and dimensions of the target display"""
    try:
        if target_display and target_display != "":
            # Use xrandr to get the position of the target display
            xrandr_output = subprocess.check_output(['xrandr'], text=True)
            for line in xrandr_output.splitlines():
                if target_display in line and " connected" in line:
                    # Format is typically: "DSI-1 connected primary 800x480+0+0 ..."
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and '+' in part:
                            # Extract resolution and position
                            resolution_pos = part
                            resolution = resolution_pos.split('+')[0]
                            pos_x = int(resolution_pos.split('+')[1])
                            pos_y = int(resolution_pos.split('+')[2])
                            width, height = map(int, resolution.split('x'))
                            return (pos_x, pos_y, width, height)
    except Exception as e:
        print(f"Error getting display position: {e}")
    
    return None 