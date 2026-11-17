#!/usr/bin/env python3
import os
import json
import sys
import traceback
import re

def get_config_path():
    env_path = os.environ.get('DESK_CONTROLLER_CONFIG')
    if env_path:
        return os.path.expanduser(env_path)
    installed = '/opt/desk-controller/config.json'
    if os.path.exists(installed):
        return installed
    return os.path.join(_source_dir(), 'config.json')

def _source_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_base_dir():
    if os.path.exists('/opt/desk-controller/config.json'):
        return '/opt/desk-controller'
    return _source_dir()

def _missing_config_message(config_path):
    return (f"Error: config file not found at {config_path}\n"
            f"Copy config.example.json to config.json and edit it, or point to one with "
            f"--config PATH or the DESK_CONTROLLER_CONFIG environment variable.")

def load_config():
    config_path = get_config_path()
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(_missing_config_message(config_path), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

class ConfigValidator:
    def __init__(self, config_path=None):
        self.config_path = config_path if config_path is not None else get_config_path()

        self.errors = []
        self.warnings = []
    
    def validate_config(self):
        return self.validate()
        
    def validate(self):
        if not os.path.exists(self.config_path):
            self.errors.append(_missing_config_message(self.config_path))
            return False
            
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading configuration file: {e}")
            return False
            
        required_sections = ['layout', 'buttons']
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Missing required section '{section}' in configuration")
                return False
                
        self._validate_layout(config.get('layout', {}))
        
        if 'display' in config:
            self._validate_display(config.get('display', {}))
            
        self._validate_buttons(config.get('buttons', []), config.get('layout', {}))
        
        return len(self.errors) == 0
        
    def _validate_layout(self, layout):
        if 'rows' not in layout:
            self.errors.append("Missing 'rows' in layout configuration")
        elif not isinstance(layout['rows'], int) or layout['rows'] < 1:
            self.errors.append("'rows' must be a positive integer")
            
        if 'columns' not in layout:
            self.errors.append("Missing 'columns' in layout configuration")
        elif not isinstance(layout['columns'], int) or layout['columns'] < 1:
            self.errors.append("'columns' must be a positive integer")
            
        if 'fullscreen' in layout and not isinstance(layout['fullscreen'], bool):
            self.errors.append("'fullscreen' must be a boolean")
            
        if 'hide_cursor' in layout and not isinstance(layout['hide_cursor'], bool):
            self.errors.append("'hide_cursor' must be a boolean")
            
        if 'background_color' in layout and not self._is_valid_color(layout['background_color']):
            self.errors.append("'background_color' must be a valid color code (e.g., '#RRGGBB')")
            
    def _validate_display(self, display):
        if 'mode' in display:
            valid_modes = ['single', 'multi']
            if display['mode'] not in valid_modes:
                self.errors.append(f"Invalid display mode '{display['mode']}'. Must be one of: {', '.join(valid_modes)}")
                
        if 'kiosk_mode' in display and not isinstance(display['kiosk_mode'], bool):
            self.errors.append("'kiosk_mode' must be a boolean")
            
        if 'auto_start' in display and not isinstance(display['auto_start'], bool):
            self.errors.append("'auto_start' must be a boolean")
            
        if 'primary_display' in display and not isinstance(display['primary_display'], str):
            self.errors.append("'primary_display' must be a string")
            
    def _validate_buttons(self, buttons, layout):
        if not isinstance(buttons, list):
            self.errors.append("'buttons' must be a list")
            return
            
        max_buttons = 0
        if 'rows' in layout and 'columns' in layout:
            max_buttons = layout['rows'] * layout['columns']
            
        if max_buttons > 0 and len(buttons) > max_buttons:
            self.warnings.append(f"Number of buttons ({len(buttons)}) exceeds grid capacity ({max_buttons})")
            
        for i, button in enumerate(buttons):
            if 'name' not in button and 'label' not in button:
                self.errors.append(f"Button {i+1} is missing 'name' or 'label'")
            
            if 'command' not in button:
                self.errors.append(f"Button {i+1} is missing 'command'")
                
            if 'icon' in button and not isinstance(button['icon'], str):
                self.errors.append(f"Button {i+1} 'icon' must be a string")
                
            if 'color' in button and not self._is_valid_color(button['color']):
                self.errors.append(f"Button {i+1} 'color' must be a valid color code (e.g., '#RRGGBB')")
                
            if 'position' in button:
                if not isinstance(button['position'], list) or len(button['position']) != 2:
                    self.errors.append(f"Button {i+1} 'position' must be a list of two integers [row, column]")
                elif not all(isinstance(pos, int) for pos in button['position']):
                    self.errors.append(f"Button {i+1} 'position' values must be integers")
                elif not (0 <= button['position'][0] < layout.get('rows', 0)) or not (0 <= button['position'][1] < layout.get('columns', 0)):
                    self.warnings.append(f"Button {i+1} position {button['position']} is outside the grid bounds")
                
    def _is_valid_color(self, color):
        return isinstance(color, str) and re.match(r'^#[0-9A-Fa-f]{6}$', color) is not None
        
    def print_report(self):
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