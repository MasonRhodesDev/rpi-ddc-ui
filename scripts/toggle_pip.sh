#!/bin/bash

. "$(dirname "${BASH_SOURCE[0]}")/_monitors.sh"
MONITOR="$DESK_PRIMARY_SN"

STATE_FILE=~/.pip_state_${MONITOR}

enable_pip() {
    echo "Enabling PBP mode (split screen)"
    sudo ddcutil --sn $MONITOR setvcp 0xE9 0x24
    
    echo "Setting left side to personal input (DisplayPort)"
    sudo ddcutil --sn $MONITOR setvcp 0xE8 0x0F
    
    echo "Setting right side to work input (HDMI)"
    sudo ddcutil --sn $MONITOR setvcp 0x60 0x11
    
    echo "PBP mode enabled: Left side (personal) - Right side (work)"
    
    echo "enabled" > $STATE_FILE
}

disable_pip() {
    echo "Disabling PIP/PBP mode"
    sudo ddcutil --sn $MONITOR setvcp 0xE9 0x00
    
    echo "Setting monitor to work input"
    sudo ddcutil --sn $MONITOR setvcp 0x60 0x11
    
    echo "PIP/PBP mode disabled: Monitor set to work input"
    
    echo "disabled" > $STATE_FILE
}

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

if [ -f "$STATE_FILE" ]; then
    saved_state=$(cat $STATE_FILE)
else
    saved_state="disabled"
fi

if [ "$saved_state" == "disabled" ]; then
    enable_pip
else
    disable_pip
fi

echo "Toggle complete" 