#!/usr/bin/env python3
import json
import os
import sys
from config_validator import ConfigValidator

def test_config():
    """Test the configuration file"""
    # Validate configuration
    validator = ConfigValidator()
    is_valid = validator.validate()
    validator.print_report()
    
    if not is_valid:
        print("Configuration validation failed!")
        sys.exit(1)
    
    # Load config for additional tests
    try:
        with open(validator.config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    # Check display configuration if present
    if 'display' in config:
        display = config['display']
        print("\nDisplay configuration:")
        
        # Check mode
        mode = display.get('mode', 'single')
        print(f"  Mode: {mode}")
        
        # Check primary display
        primary_display = display.get('primary_display', '')
        if mode == 'single' and not primary_display:
            print("  Warning: Single display mode is set but no primary display is specified")
        else:
            print(f"  Primary display: {primary_display or 'Auto-detect'}")
        
        # Check kiosk mode
        kiosk_mode = display.get('kiosk_mode', False)
        print(f"  Kiosk mode: {'Enabled' if kiosk_mode else 'Disabled'}")
        
        # Check auto start
        auto_start = display.get('auto_start', False)
        print(f"  Auto start: {'Enabled' if auto_start else 'Disabled'}")
    
    # Check layout configuration
    layout = config['layout']
    print("\nLayout configuration:")
    print(f"  Grid: {layout.get('rows', 2)}x{layout.get('columns', 3)}")
    print(f"  Fullscreen: {'Yes' if layout.get('fullscreen', False) else 'No'}")
    print(f"  Hide cursor: {'Yes' if layout.get('hide_cursor', False) else 'No'}")
    
    # Check buttons
    buttons = config['buttons']
    print(f"\nButtons: {len(buttons)}")
    
    # All tests passed
    print("\nConfiguration test passed!")
    return True

if __name__ == "__main__":
    test_config() 