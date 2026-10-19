#!/bin/bash
. "$(dirname "${BASH_SOURCE[0]}")/_monitors.sh"
require_secondary

echo "W / P"
sudo ddcutil --sn "$DESK_PRIMARY_SN" setvcp 0x60 0x11 > /dev/null
sudo ddcutil --sn "$DESK_SECONDARY_SN" setvcp 0x60 0x0f > /dev/null
