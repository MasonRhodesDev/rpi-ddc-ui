#!/bin/bash
Primary=HSRTS63
Secondary=6VSGM43

echo "P / W"
sudo ddcutil --sn $Primary setvcp 0x60 0x0f > /dev/null
sudo ddcutil --sn $Secondary setvcp 0x60 0x11 > /dev/null