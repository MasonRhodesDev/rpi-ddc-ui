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
                self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
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
        
        # Validate structure
        if not isinstance(config, dict):
            self.errors.append("Configuration must be a JSON object")
            return False
        
        # Check required sections
        if 'layout' not in config:
            self.errors.append("Missing 'layout' section in configuration")
            return False
        
        if 'buttons' not in config:
            self.errors.append("Missing 'buttons' section in configuration")
            return False
        
        # Validate layout
        self._validate_layout(config['layout'])
        
        # Validate display configuration if present
        if 'display' in config:
            self._validate_display(config['display'])
        
        # Validate buttons
        self._validate_buttons(config['buttons'], config['layout'])
        
        # Return validation result
        return len(self.errors) == 0
    
    def _validate_layout(self, layout):
        """Validate the layout section"""
        if not isinstance(layout, dict):
            self.errors.append("'layout' must be a JSON object")
            return
        
        # Check required fields
        if 'rows' not in layout:
            self.errors.append("Missing 'rows' in layout configuration")
        elif not isinstance(layout['rows'], int) or layout['rows'] <= 0:
            self.errors.append("'rows' must be a positive integer")
        
        if 'columns' not in layout:
            self.errors.append("Missing 'columns' in layout configuration")
        elif not isinstance(layout['columns'], int) or layout['columns'] <= 0:
            self.errors.append("'columns' must be a positive integer")
        
        # Check optional fields
        if 'button_spacing' in layout and not isinstance(layout['button_spacing'], int):
            self.errors.append("'button_spacing' must be an integer")
        
        if 'background_color' in layout and not self._is_valid_color(layout['background_color']):
            self.errors.append("'background_color' must be a valid hex color (e.g., '#RRGGBB')")
        
        if 'fullscreen' in layout and not isinstance(layout['fullscreen'], bool):
            self.errors.append("'fullscreen' must be a boolean")
            
        if 'hide_cursor' in layout and not isinstance(layout['hide_cursor'], bool):
            self.errors.append("'hide_cursor' must be a boolean")
    
    def _validate_display(self, display):
        """Validate the display configuration section"""
        if not isinstance(display, dict):
            self.errors.append("'display' must be a JSON object")
            return
        
        # Check mode field
        if 'mode' in display:
            valid_modes = ['mirror', 'extend', 'single']
            if display['mode'] not in valid_modes:
                self.errors.append(f"'mode' must be one of: {', '.join(valid_modes)}")
        
        # Check primary_display field
        if 'primary_display' in display and not isinstance(display['primary_display'], str):
            self.errors.append("'primary_display' must be a string")
        
        # Check kiosk_mode field
        if 'kiosk_mode' in display and not isinstance(display['kiosk_mode'], bool):
            self.errors.append("'kiosk_mode' must be a boolean")
        
        # Check auto_start field
        if 'auto_start' in display and not isinstance(display['auto_start'], bool):
            self.errors.append("'auto_start' must be a boolean")
    
    def _validate_buttons(self, buttons, layout):
        """Validate the buttons section"""
        if not isinstance(buttons, list):
            self.errors.append("'buttons' must be a JSON array")
            return
        
        if not buttons:
            self.warnings.append("No buttons defined in configuration")
            return
        
        # Get layout dimensions
        rows = layout.get('rows', 0)
        columns = layout.get('columns', 0)
        
        # Track positions to check for duplicates
        positions = set()
        
        # Validate each button
        for i, button in enumerate(buttons):
            if not isinstance(button, dict):
                self.errors.append(f"Button {i+1} must be a JSON object")
                continue
            
            # Check required fields
            if 'name' not in button:
                self.errors.append(f"Button {i+1} is missing 'name'")
            
            if 'command' not in button:
                self.errors.append(f"Button {i+1} is missing 'command'")
            
            # Check position
            if 'position' in button:
                if not isinstance(button['position'], list) or len(button['position']) != 2:
                    self.errors.append(f"Button {i+1} 'position' must be an array [row, column]")
                else:
                    row, col = button['position']
                    if not isinstance(row, int) or not isinstance(col, int):
                        self.errors.append(f"Button {i+1} position values must be integers")
                    elif row < 0 or row >= rows or col < 0 or col >= columns:
                        self.errors.append(f"Button {i+1} position [{row}, {col}] is outside the grid ({rows}x{columns})")
                    else:
                        pos_key = (row, col)
                        if pos_key in positions:
                            self.errors.append(f"Button {i+1} has the same position [{row}, {col}] as another button")
                        positions.add(pos_key)
            
            # Check icon
            if 'icon' in button and button['icon']:
                icon_path = button['icon']
                # Handle relative paths
                if not os.path.isabs(icon_path):
                    base_dir = os.path.dirname(self.config_path)
                    icon_path = os.path.join(base_dir, icon_path)
                
                if not os.path.exists(icon_path):
                    self.warnings.append(f"Icon file '{icon_path}' for button '{button.get('name', i+1)}' not found")
            
            # Check colors
            if 'color' in button and not self._is_valid_color(button['color']):
                self.errors.append(f"Button {i+1} 'color' must be a valid hex color (e.g., '#RRGGBB')")
            
            if 'text_color' in button and not self._is_valid_color(button['text_color']):
                self.errors.append(f"Button {i+1} 'text_color' must be a valid hex color (e.g., '#RRGGBB')")
    
    def _is_valid_color(self, color):
        """Check if a string is a valid hex color"""
        return isinstance(color, str) and re.match(r'^#[0-9A-Fa-f]{6}$', color) is not None
    
    def print_report(self):
        """Print validation errors and warnings"""
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
    validator = ConfigValidator()
    is_valid = validator.validate()
    validator.print_report()
    
    if not is_valid:
        sys.exit(1)

if __name__ == '__main__':
    main() 