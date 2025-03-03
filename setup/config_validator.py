#!/usr/bin/env python3
import json
import os
import sys
import re

class ConfigValidator:
    def __init__(self, config_path=None):
        if config_path is None:
            # If running from installed location, use that path
            if os.path.exists('/opt/desk-controller/config.json'):
                self.config_path = '/opt/desk-controller/config.json'
            else:
                # Otherwise use the current directory (for development)
                self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.json')
        else:
            self.config_path = config_path
            
        self.errors = []
        self.warnings = []
    
    def validate_config(self):
        """Validate the configuration file"""
        return self.validate()
        
    def validate(self):
        """Validate the configuration file"""
        # Check if config file exists
        if not os.path.exists(self.config_path):
            self.errors.append(f"Configuration file '{self.config_path}' not found")
            return False
            
        # Load config
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading configuration file: {e}")
            return False
            
        # Check required sections
        required_sections = ['layout', 'buttons']
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Missing required section '{section}' in configuration")
                return False
                
        # Validate layout
        self._validate_layout(config.get('layout', {}))
        
        # Validate display if present
        if 'display' in config:
            self._validate_display(config.get('display', {}))
            
        # Validate buttons
        self._validate_buttons(config.get('buttons', []), config.get('layout', {}))
        
        # Return validation result
        return len(self.errors) == 0
        
    def _validate_layout(self, layout):
        """Validate layout configuration"""
        # Check required fields
        if 'rows' not in layout:
            self.errors.append("Missing 'rows' in layout configuration")
        elif not isinstance(layout['rows'], int) or layout['rows'] < 1:
            self.errors.append("'rows' must be a positive integer")
            
        if 'columns' not in layout:
            self.errors.append("Missing 'columns' in layout configuration")
        elif not isinstance(layout['columns'], int) or layout['columns'] < 1:
            self.errors.append("'columns' must be a positive integer")
            
        # Check optional fields
        if 'fullscreen' in layout and not isinstance(layout['fullscreen'], bool):
            self.errors.append("'fullscreen' must be a boolean")
            
        if 'hide_cursor' in layout and not isinstance(layout['hide_cursor'], bool):
            self.errors.append("'hide_cursor' must be a boolean")
            
        if 'background_color' in layout and not self._is_valid_color(layout['background_color']):
            self.errors.append("'background_color' must be a valid color code (e.g., '#RRGGBB')")
            
    def _validate_display(self, display):
        """Validate display configuration"""
        # Check mode
        if 'mode' in display:
            valid_modes = ['single', 'multi']
            if display['mode'] not in valid_modes:
                self.errors.append(f"Invalid display mode '{display['mode']}'. Must be one of: {', '.join(valid_modes)}")
                
        # Check kiosk mode
        if 'kiosk_mode' in display and not isinstance(display['kiosk_mode'], bool):
            self.errors.append("'kiosk_mode' must be a boolean")
            
        # Check auto start
        if 'auto_start' in display and not isinstance(display['auto_start'], bool):
            self.errors.append("'auto_start' must be a boolean")
            
        # Check primary display
        if 'primary_display' in display and not isinstance(display['primary_display'], str):
            self.errors.append("'primary_display' must be a string")
            
    def _validate_buttons(self, buttons, layout):
        """Validate buttons configuration"""
        if not isinstance(buttons, list):
            self.errors.append("'buttons' must be a list")
            return
            
        # Check if we have layout information
        max_buttons = 0
        if 'rows' in layout and 'columns' in layout:
            max_buttons = layout['rows'] * layout['columns']
            
        # Check number of buttons
        if max_buttons > 0 and len(buttons) > max_buttons:
            self.warnings.append(f"Number of buttons ({len(buttons)}) exceeds grid capacity ({max_buttons})")
            
        # Validate each button
        for i, button in enumerate(buttons):
            # Check required fields
            if 'label' not in button:
                self.errors.append(f"Button {i+1} is missing 'label'")
                
            if 'action' not in button:
                self.errors.append(f"Button {i+1} is missing 'action'")
            else:
                # Check action type
                valid_actions = ['command', 'url', 'script', 'shutdown', 'reboot']
                if button['action'] not in valid_actions:
                    self.errors.append(f"Button {i+1} has invalid action '{button['action']}'. Must be one of: {', '.join(valid_actions)}")
                    
                # Check command for command action (not needed for shutdown/reboot)
                if button['action'] == 'command' and 'command' not in button:
                    self.errors.append(f"Button {i+1} with 'command' action is missing 'command' field")
                    
                # Check url for url action
                if button['action'] == 'url' and 'url' not in button:
                    self.errors.append(f"Button {i+1} with 'url' action is missing 'url' field")
                    
                # Check script for script action
                if button['action'] == 'script' and 'script' not in button:
                    self.errors.append(f"Button {i+1} with 'script' action is missing 'script' field")
                    
            # Check optional fields
            if 'icon' in button and not isinstance(button['icon'], str):
                self.errors.append(f"Button {i+1} 'icon' must be a string")
                
            if 'color' in button and not self._is_valid_color(button['color']):
                self.errors.append(f"Button {i+1} 'color' must be a valid color code (e.g., '#RRGGBB')")
                
            if 'confirm' in button and not isinstance(button['confirm'], bool):
                self.errors.append(f"Button {i+1} 'confirm' must be a boolean")
                
    def _is_valid_color(self, color):
        """Check if a color code is valid"""
        return isinstance(color, str) and re.match(r'^#[0-9A-Fa-f]{6}$', color) is not None
        
    def print_report(self):
        """Print validation report"""
        if self.errors:
            print("Configuration errors:")
            for error in self.errors:
                print(f"  - {error}")
                
        if self.warnings:
            print("Configuration warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        if not self.errors and not self.warnings:
            print("Configuration is valid.")

def main():
    """Main function for command-line usage"""
    validator = ConfigValidator()
    if validator.validate_config():
        print("Configuration is valid.")
        return 0
    else:
        validator.print_report()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 