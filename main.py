#!/usr/bin/env python3
import sys
import json
import os
import subprocess
import argparse
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGridLayout, 
                             QPushButton, QWidget, QSizePolicy, QMessageBox,
                             QDesktopWidget, QScrollArea)
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize

# Import ConfigValidator from setup directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'setup'))
from config_validator import ConfigValidator
from system_check import is_raspberry_pi, is_dsi_display_connected

class DeskController(QMainWindow):
    def __init__(self, kiosk_mode=False):
        super().__init__()
        self.base_dir = self.get_base_dir()
        self.config = self.load_config()
        self.kiosk_mode = kiosk_mode
        
        # Get screen resolution
        self.screen_resolution = self.get_screen_resolution()
        print(f"Screen resolution: {self.screen_resolution}")
        
        self.init_ui()
        
    def get_base_dir(self):
        """Get the base directory of the application"""
        # If running from installed location, use that path
        if os.path.exists('/opt/desk-controller/config.json'):
            return '/opt/desk-controller'
        # Otherwise use the current directory (for development)
        return os.path.dirname(os.path.abspath(__file__))
        
    def load_config(self):
        """Load the configuration from config.json"""
        config_path = os.path.join(self.base_dir, 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: config.json not found at {config_path}")
            print(f"Current directory: {os.getcwd()}")
            print(f"Directory contents: {os.listdir(self.base_dir)}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {config_path}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading config: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    def get_screen_resolution(self):
        """Get the resolution of the target display from display configuration"""
        try:
            # Get the target display from config.json
            target_display = self.config.get('display', {}).get('primary_display', '')
            
            if target_display and target_display != "":
                # Use xrandr to get the resolution of the target display
                print(f"Getting resolution for display: {target_display}")
                try:
                    xrandr_output = subprocess.check_output(['xrandr'], text=True)
                    for line in xrandr_output.splitlines():
                        if target_display in line and " connected" in line:
                            # Find the current resolution
                            # Look for the line with the display name and the resolution
                            # Format is typically: "DSI-1 connected primary 800x480+0+0 ..."
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '+' in part:
                                    resolution = part.split('+')[0]
                                    width, height = map(int, resolution.split('x'))
                                    print(f"Found resolution for {target_display}: {width}x{height}")
                                    return (width, height)
                            
                            # If we didn't find the resolution in the same line, check the next line
                            # Sometimes xrandr formats the output differently
                            next_line_index = xrandr_output.splitlines().index(line) + 1
                            if next_line_index < len(xrandr_output.splitlines()):
                                next_line = xrandr_output.splitlines()[next_line_index]
                                if '*' in next_line:  # Current mode is marked with an asterisk
                                    resolution = next_line.strip().split()[0]
                                    width, height = map(int, resolution.split('x'))
                                    print(f"Found resolution for {target_display} in next line: {width}x{height}")
                                    return (width, height)
                except Exception as e:
                    print(f"Error getting resolution from xrandr: {e}")
                    # Fall back to default method
            
            # If we couldn't get the resolution from xrandr, fall back to Qt's method
            print("Falling back to Qt's screen resolution detection")
            desktop = QDesktopWidget()
            screen = desktop.screenGeometry()
            return (screen.width(), screen.height())
        except Exception as e:
            print(f"Error in get_screen_resolution: {e}")
            # Fall back to Qt's method in case of any error
            desktop = QDesktopWidget()
            screen = desktop.screenGeometry()
            return (screen.width(), screen.height())
    
    def center_window(self):
        """Center the window on the screen"""
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle('Desk Controller')
        
        # Set background color
        bg_color = self.config['layout'].get('background_color', '#2E3440')
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(bg_color))
        self.setPalette(palette)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create scroll area to ensure all buttons are visible
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        # Create grid layout
        grid = QGridLayout(content_widget)
        
        # Calculate appropriate spacing and margins based on screen size
        screen_width, screen_height = self.screen_resolution
        
        # Calculate spacing as a percentage of screen size
        spacing_percent = 0.01  # 1% of screen size
        button_spacing = max(int(min(screen_width, screen_height) * spacing_percent), 2)
        
        # Calculate margins as a percentage of screen size
        margin_percent = 0.02  # 2% of screen size
        margin = max(int(min(screen_width, screen_height) * margin_percent), 5)
        
        # Set grid spacing and margins
        grid.setSpacing(button_spacing)
        grid.setContentsMargins(margin, margin, margin, margin)
        
        # Create buttons
        self.create_buttons(grid)
        
        # Set the central widget to the scroll area
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        
        # Set window size or fullscreen
        if not self.kiosk_mode:
            # Use a percentage of screen size for window
            width = min(int(screen_width * 0.8), 800)
            height = min(int(screen_height * 0.8), 600)
            self.resize(width, height)
            self.center_window()
            self.show()
        else:
            # In kiosk mode, find the specific display and position the window there
            desktop = QDesktopWidget()
            target_display = self.config.get('display', {}).get('primary_display', '')
            target_geometry = None
            
            # If we have a target display, try to find its geometry
            if target_display and target_display != "":
                try:
                    # Use xrandr to get the position of the target display
                    xrandr_output = subprocess.check_output(['xrandr'], text=True)
                    for line in xrandr_output.splitlines():
                        if target_display in line and " connected" in line:
                            # Format is typically: "DSI-1 connected primary 800x480+0+0 ..."
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '+' in part:
                                    # Extract resolution and position
                                    resolution_pos = part
                                    resolution = resolution_pos.split('+')[0]
                                    pos_x = int(resolution_pos.split('+')[1])
                                    pos_y = int(resolution_pos.split('+')[2])
                                    width, height = map(int, resolution.split('x'))
                                    target_geometry = (pos_x, pos_y, width, height)
                                    print(f"Found geometry for {target_display}: {target_geometry}")
                                    break
                except Exception as e:
                    print(f"Error getting display position from xrandr: {e}")
            
            # If we found the target display's geometry, position the window there
            if target_geometry:
                pos_x, pos_y, width, height = target_geometry
                print(f"Setting window geometry to match {target_display}: {pos_x}, {pos_y}, {width}, {height}")
                
                # Set window flags to remove window decorations
                self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
                
                # Set window geometry to match the target display
                self.setGeometry(pos_x, pos_y, width, height)
                
                # Show the window
                self.show()
                
                # Hide cursor if specified in config
                if self.config['layout'].get('hide_cursor', False):
                    QApplication.setOverrideCursor(Qt.BlankCursor)
            else:
                # Fallback to fullscreen if we couldn't find the target display
                print("Could not find target display geometry, falling back to fullscreen")
                self.showFullScreen()
                # Hide cursor if specified in config
                if self.config['layout'].get('hide_cursor', False):
                    QApplication.setOverrideCursor(Qt.BlankCursor)
    
    def create_buttons(self, grid):
        """Create buttons based on configuration"""
        rows = self.config['layout'].get('rows', 2)
        columns = self.config['layout'].get('columns', 3)
        
        # Calculate button size based on screen resolution
        screen_width, screen_height = self.screen_resolution
        
        # Calculate available space for buttons
        available_width = screen_width * 0.9  # 90% of screen width
        available_height = screen_height * 0.9  # 90% of screen height
        
        # Calculate button dimensions
        button_width = int(available_width / columns)
        button_height = int(available_height / rows)
        
        # Calculate font size based on button size
        font_size = max(int(min(button_width, button_height) * 0.1), 8)
        
        # Calculate padding and border radius
        padding = max(int(min(button_width, button_height) * 0.05), 3)
        border_radius = max(int(min(button_width, button_height) * 0.05), 3)
        
        # Calculate icon size
        icon_size = max(int(min(button_width, button_height) * 0.3), 16)
        
        print(f"Button dimensions: {button_width}x{button_height}")
        print(f"Font size: {font_size}, Padding: {padding}, Icon size: {icon_size}")
        
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
                    border-radius: {border_radius}px;
                    font-size: {font_size}px;
                    font-weight: bold;
                    padding: {padding}px;
                    min-height: {button_height * 0.8}px;
                    min-width: {button_width * 0.8}px;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            
            # Set icon if provided
            if icon_path:
                # Handle relative paths
                if not os.path.isabs(icon_path):
                    icon_path = os.path.join(self.base_dir, icon_path)
                
                if os.path.exists(icon_path):
                    button.setIcon(QIcon(icon_path))
                    button.setIconSize(QSize(icon_size, icon_size))
            
            # Connect button to command
            button.clicked.connect(lambda checked, cmd=command: self.execute_command(cmd))
            
            # Add button to grid at specified position
            row, col = position
            if 0 <= row < rows and 0 <= col < columns:
                grid.addWidget(button, row, col)
    
    def execute_command(self, command):
        """Execute the command associated with a button"""
        try:
            # Handle @/ prefix for commands (relative to scripts directory)
            if command.startswith('@/'):
                # Remove the @/ prefix
                script_path = command[2:]
                # Get the scripts directory path
                scripts_dir = os.path.join(self.base_dir, 'scripts')
                # Create the full path to the script
                full_script_path = os.path.join(scripts_dir, script_path)
                # Check if the script exists
                if os.path.exists(full_script_path):
                    # Make sure the script is executable
                    if not os.access(full_script_path, os.X_OK):
                        os.chmod(full_script_path, os.stat(full_script_path).st_mode | 0o111)
                    # Execute the script
                    command = full_script_path
                else:
                    print(f"Error: Script not found: {full_script_path}")
                    QMessageBox.critical(self, "Script Error", f"Script not found: {script_path}")
                    return
            
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
    try:
        # Check if running on a Raspberry Pi
        if not is_raspberry_pi():
            print("Error: This application is designed to run on a Raspberry Pi.")
            print("Current system is not detected as a Raspberry Pi.")
            sys.exit(1)
        
        # DSI display check removed
        
        # Validate configuration before starting
        validator = ConfigValidator()
        if not validator.validate_config():
            print("Configuration validation failed. Please check your config.json file.")
            validator.print_report()
            sys.exit(1)
        
        # Create application
        app = QApplication(sys.argv)
        
        # Set application font
        font_family = "Arial"
        font_size = 12
        font = QFont(font_family, font_size)
        app.setFont(font)
        
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description='Desk Controller')
        parser.add_argument('--kiosk', action='store_true', help='Run in kiosk mode')
        args = parser.parse_args()
        
        # Load config to check if kiosk mode is enabled in config
        config_path = '/opt/desk-controller/config.json'
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Use kiosk mode from config if not specified in command line
                kiosk_mode = args.kiosk or config.get('display', {}).get('kiosk_mode', False)
        except Exception as e:
            print(f"Error loading config for kiosk mode check: {e}")
            kiosk_mode = args.kiosk
        
        window = DeskController(kiosk_mode=kiosk_mode)
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 