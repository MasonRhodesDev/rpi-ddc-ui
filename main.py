#!/usr/bin/env python3
import sys
import json
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGridLayout, 
                             QPushButton, QWidget, QSizePolicy, QMessageBox)
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize

from config_validator import ConfigValidator

class DeskController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.init_ui()
        
    def load_config(self):
        """Load the configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: config.json not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in config.json")
            sys.exit(1)
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle('Desk Controller')
        
        # Set background color
        bg_color = self.config['layout'].get('background_color', '#2E3440')
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(bg_color))
        self.setPalette(palette)
        
        # Create central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Create grid layout
        grid = QGridLayout(central_widget)
        grid.setSpacing(self.config['layout'].get('button_spacing', 10))
        
        # Create buttons from config
        self.create_buttons(grid)
        
        # Set fullscreen if configured
        if self.config['layout'].get('fullscreen', True):
            self.showFullScreen()
        else:
            self.show()
    
    def create_buttons(self, grid):
        """Create buttons based on configuration"""
        rows = self.config['layout'].get('rows', 2)
        columns = self.config['layout'].get('columns', 3)
        
        # Create a button for each entry in the config
        for button_config in self.config['buttons']:
            name = button_config.get('name', 'Button')
            icon_path = button_config.get('icon', '')
            command = button_config.get('command', '')
            color = button_config.get('color', '#88C0D0')
            text_color = button_config.get('text_color', '#ECEFF4')
            position = button_config.get('position', [0, 0])
            
            # Create button
            button = QPushButton(name)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Set button style
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {text_color};
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 15px;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            
            # Set icon if provided
            if icon_path and os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(48, 48))
            
            # Connect button to command
            button.clicked.connect(lambda checked, cmd=command: self.execute_command(cmd))
            
            # Add button to grid at specified position
            row, col = position
            if 0 <= row < rows and 0 <= col < columns:
                grid.addWidget(button, row, col)
    
    def execute_command(self, command):
        """Execute the command associated with a button"""
        try:
            subprocess.Popen(command, shell=True)
        except Exception as e:
            print(f"Error executing command: {e}")
            QMessageBox.critical(self, "Command Error", f"Error executing command: {e}")
    
    def lighten_color(self, hex_color, amount=20):
        """Lighten a hex color by the specified amount"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Lighten
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def darken_color(self, hex_color, amount=20):
        """Darken a hex color by the specified amount"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Darken
        r = max(0, r - amount)
        g = max(0, g - amount)
        b = max(0, b - amount)
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Exit fullscreen with Escape key
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()
        # Toggle fullscreen with F11
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

def main():
    # Validate configuration before starting
    validator = ConfigValidator()
    is_valid = validator.validate()
    validator.print_report()
    
    if not is_valid:
        print("Configuration errors found. Please fix the issues and try again.")
        sys.exit(1)
    
    # Start application
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Sans Serif", 12)
    app.setFont(font)
    
    window = DeskController()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 