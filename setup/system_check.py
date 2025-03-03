#!/usr/bin/env python3
import os
import subprocess
import sys
import re
import json

def is_raspberry_pi():
    """
    Check if the current system is a Raspberry Pi.
    Returns True if it is, False otherwise.
    """
    # Method 1: Check for Raspberry Pi model file
    if os.path.exists('/proc/device-tree/model'):
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                return True
    
    # Method 2: Check CPU info
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM2708' in cpuinfo or 'BCM2709' in cpuinfo or 'BCM2711' in cpuinfo or 'BCM2835' in cpuinfo:
                return True
    except:
        pass
    
    # Method 3: Check for Raspberry Pi specific hardware
    try:
        output = subprocess.check_output(['grep', '-q', 'Raspberry Pi', '/proc/device-tree/model'], stderr=subprocess.STDOUT)
        return True
    except:
        pass
    
    return False

def is_dsi_display_connected():
    """
    Check if a DSI-1 display is connected.
    Returns True if it is, False otherwise.
    Also checks if DISPLAY environment variable is set, and attempts to attach to one if not.
    """
    # First check if DISPLAY environment variable is set
    if 'DISPLAY' not in os.environ:
        print("DISPLAY environment variable not set. Attempting to attach to a display...")
        try:
            # Try to set DISPLAY to the default X server
            os.environ['DISPLAY'] = ':0'
            print(f"Set DISPLAY environment variable to {os.environ['DISPLAY']}")
        except Exception as e:
            print(f"Failed to set DISPLAY environment variable: {e}")
            return False
    
    try:
        # Use xrandr to check for connected displays
        output = subprocess.check_output(['xrandr', '--query'], stderr=subprocess.STDOUT, universal_newlines=True)
        
        # Check if DSI-1 is in the output and connected
        if 'DSI-1 connected' in output:
            return True
        
        # Alternative check for Raspberry Pi specific DSI display
        if 'DSI connected' in output:
            return True
    except Exception as e:
        print(f"Error checking for DSI display with xrandr: {e}")
        # If xrandr is not available or fails, try another method
        try:
            # Check if the DSI interface is enabled in config.txt
            with open('/boot/config.txt', 'r') as f:
                config = f.read()
                if 'dtoverlay=vc4-kms-v3d' in config and not 'disable_display_dsi=1' in config:
                    # If the DSI interface is enabled, assume it's connected
                    # This is not a perfect check but a reasonable fallback
                    return True
        except Exception as config_e:
            print(f"Error checking config.txt: {config_e}")
            pass
    
    return False

def scan_scripts_for_sudo_commands(scripts_dir, config_file=None):
    """
    Scan scripts directory and config file for commands that need sudo privileges.
    Returns a list of commands that need to be added to the sudoers file.
    """
    sudo_commands = []
    
    # Check if scripts directory exists
    if not os.path.isdir(scripts_dir):
        print(f"Warning: Scripts directory '{scripts_dir}' not found.")
        return sudo_commands
    
    # Scan all script files in the scripts directory
    for filename in os.listdir(scripts_dir):
        filepath = os.path.join(scripts_dir, filename)
        if os.path.isfile(filepath) and (filepath.endswith('.sh') or filepath.endswith('.py') or os.access(filepath, os.X_OK)):
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                    # Look for sudo commands in the script
                    sudo_pattern = r'sudo\s+([^;&|<>\n]+)'
                    matches = re.findall(sudo_pattern, content)
                    
                    for match in matches:
                        # Extract the command (first word after sudo)
                        command = match.strip().split()[0]
                        
                        # Get the full path of the command
                        try:
                            full_path = subprocess.check_output(['which', command], universal_newlines=True).strip()
                            if full_path and full_path not in sudo_commands:
                                sudo_commands.append(full_path)
                        except:
                            # If 'which' fails, use the command as is
                            if command not in sudo_commands:
                                sudo_commands.append(command)
            except Exception as e:
                print(f"Warning: Could not scan script '{filepath}': {e}")
    
    # Also scan config.json for commands that might need sudo
    if config_file and os.path.isfile(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
                # Look for commands in buttons
                if 'buttons' in config:
                    for button in config['buttons']:
                        if 'command' in button:
                            cmd = button['command']
                            
                            # Check if it's a script reference
                            if cmd.startswith('@/'):
                                script_name = cmd[2:]  # Remove @/ prefix
                                script_path = os.path.join(scripts_dir, script_name)
                                
                                # If the script exists, scan it for sudo commands
                                if os.path.isfile(script_path):
                                    try:
                                        with open(script_path, 'r') as sf:
                                            script_content = sf.read()
                                            
                                            # Look for sudo commands in the script
                                            sudo_pattern = r'sudo\s+([^;&|<>\n]+)'
                                            matches = re.findall(sudo_pattern, script_content)
                                            
                                            for match in matches:
                                                # Extract the command (first word after sudo)
                                                command = match.strip().split()[0]
                                                
                                                # Get the full path of the command
                                                try:
                                                    full_path = subprocess.check_output(['which', command], universal_newlines=True).strip()
                                                    if full_path and full_path not in sudo_commands:
                                                        sudo_commands.append(full_path)
                                                except:
                                                    # If 'which' fails, use the command as is
                                                    if command not in sudo_commands:
                                                        sudo_commands.append(command)
                                    except Exception as e:
                                        print(f"Warning: Could not scan script '{script_path}': {e}")
        except Exception as e:
            print(f"Warning: Could not scan config file '{config_file}': {e}")
    
    return sudo_commands

def generate_sudoers_entry(username, commands):
    """
    Generate a sudoers entry for the given username and commands.
    """
    if not commands:
        return ""
    
    # Create the sudoers entry
    entry = f"{username} ALL=(ALL) NOPASSWD: "
    entry += ", ".join(commands)
    
    return entry

def check_system_requirements():
    """
    Check if the system meets the requirements.
    Exits with an error message if not.
    """
    # Check if running on a Raspberry Pi
    if not is_raspberry_pi():
        print("Error: This application is designed to run on a Raspberry Pi.")
        print("Current system is not detected as a Raspberry Pi.")
        sys.exit(1)
    
    # DSI display check removed
    
    print("System check passed: Running on Raspberry Pi.")
    return True

if __name__ == "__main__":
    check_system_requirements() 