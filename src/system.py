#!/usr/bin/env python3
import os
import subprocess
from PyQt5.QtWidgets import QDesktopWidget

def is_raspberry_pi():
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            return 'Raspberry Pi' in model
    except:
        try:
            output = subprocess.check_output(['cat', '/proc/cpuinfo'], text=True)
            return 'Raspberry' in output
        except:
            return False

def is_dsi_display_connected():
    try:
        output = subprocess.check_output(['tvservice', '-l'], text=True)
        return 'DSI' in output
    except:
        return False

def detect_touch_screen():
    try:
        xinput_output = subprocess.check_output(['xinput', 'list'], text=True)
        touch_keywords = ['touch', 'TOUCH', 'Touch', 'touchscreen', 'Touchscreen']
        
        for line in xinput_output.splitlines():
            if any(keyword in line for keyword in touch_keywords):
                print(f"Touch screen detected via xinput: {line.strip()}")
                return True
        
        if os.path.exists('/dev/input/'):
            try:
                evtest_output = subprocess.check_output(['evtest', '--query', '/dev/input/event*', 'EV_KEY', 'BTN_TOUCH'], 
                                                       stderr=subprocess.STDOUT, text=True, shell=True)
                if "supported" in evtest_output:
                    print("Touch screen detected via evtest")
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
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
    try:
        if target_display and target_display != "":
            print(f"Getting resolution for display: {target_display}")
            try:
                xrandr_output = subprocess.check_output(['xrandr'], text=True)
                for line in xrandr_output.splitlines():
                    if target_display in line and " connected" in line:
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and '+' in part:
                                resolution = part.split('+')[0]
                                width, height = map(int, resolution.split('x'))
                                print(f"Found resolution for {target_display}: {width}x{height}")
                                return (width, height)
                        
                        next_line_index = xrandr_output.splitlines().index(line) + 1
                        if next_line_index < len(xrandr_output.splitlines()):
                            next_line = xrandr_output.splitlines()[next_line_index]
                            if '*' in next_line:
                                resolution = next_line.strip().split()[0]
                                width, height = map(int, resolution.split('x'))
                                print(f"Found resolution for {target_display} in next line: {width}x{height}")
                                return (width, height)
            except Exception as e:
                print(f"Error getting resolution from xrandr: {e}")
        
        print("Falling back to Qt's screen resolution detection")
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        return (screen.width(), screen.height())
    except Exception as e:
        print(f"Error in get_screen_resolution: {e}")
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        return (screen.width(), screen.height())

def get_display_position(target_display):
    try:
        if target_display and target_display != "":
            xrandr_output = subprocess.check_output(['xrandr'], text=True)
            for line in xrandr_output.splitlines():
                if target_display in line and " connected" in line:
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and '+' in part:
                            resolution_pos = part
                            resolution = resolution_pos.split('+')[0]
                            pos_x = int(resolution_pos.split('+')[1])
                            pos_y = int(resolution_pos.split('+')[2])
                            width, height = map(int, resolution.split('x'))
                            return (pos_x, pos_y, width, height)
    except Exception as e:
        print(f"Error getting display position: {e}")
    
    return None 