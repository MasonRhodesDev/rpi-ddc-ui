#!/bin/bash

# Monitor serial number
MONITOR=HSRTS63

# State file to track PIP mode status
STATE_FILE=~/.pip_state_${MONITOR}

# Function to enable PIP mode
enable_pip() {
    echo "Enabling PBP mode (split screen)"
    sudo ddcutil --sn $MONITOR setvcp 0xE9 0x24
    
    # Set left input source to personal (DisplayPort - 0x0F)
    echo "Setting left side to personal input (DisplayPort)"
    sudo ddcutil --sn $MONITOR setvcp 0xE8 0x0F
    
    # Set right input source to work (HDMI - 0x11)
    echo "Setting right side to work input (HDMI)"
    sudo ddcutil --sn $MONITOR setvcp 0x60 0x11
    
    echo "PBP mode enabled: Left side (personal) - Right side (work)"
    
    # Save state
    echo "enabled" > $STATE_FILE
}

# Function to disable PIP mode
disable_pip() {
    echo "Disabling PIP/PBP mode"
    sudo ddcutil --sn $MONITOR setvcp 0xE9 0x00
    
    # Set monitor to work input
    echo "Setting monitor to work input"
    sudo ddcutil --sn $MONITOR setvcp 0x60 0x11
    
    echo "PIP/PBP mode disabled: Monitor set to work input"
    
    # Save state
    echo "disabled" > $STATE_FILE
}

# Check if we need to verify the current state from the monitor
if [ "$1" == "--force-check" ] || [ ! -f "$STATE_FILE" ]; then
    echo "Checking current PIP/PBP state from monitor..."
    current_state=$(sudo ddcutil --sn $MONITOR getvcp 0xE9 2>/dev/null | grep -o "current value = *[0-9]*" | awk '{print $4}')
    
    if [ "$current_state" = "0" ] || [ -z "$current_state" ]; then
        echo "PIP is currently disabled"
        echo "disabled" > $STATE_FILE
    else
        echo "PIP is currently enabled"
        echo "enabled" > $STATE_FILE
    fi
fi

# Read the saved state
if [ -f "$STATE_FILE" ]; then
    saved_state=$(cat $STATE_FILE)
else
    # Default to disabled if state file doesn't exist
    saved_state="disabled"
fi

# Toggle the state
if [ "$saved_state" == "disabled" ]; then
    enable_pip
else
    disable_pip
fi

echo "Toggle complete" 