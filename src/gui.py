#!/usr/bin/env python3
import os
import subprocess
from PyQt5.QtWidgets import (QMainWindow, QGridLayout, QPushButton, QWidget, 
                            QSizePolicy, QMessageBox, QScrollArea, QApplication, QLabel, QVBoxLayout)
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, QSize, QEvent

from src.config import get_base_dir
from src.system import get_screen_resolution, get_display_position

def lighten_color(hex_color, amount=20):
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

def darken_color(hex_color, amount=20):
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

class WrappingButton(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        
        # Create the actual push button that will be the background
        self.button = QPushButton(self)
        
        # Create content widget and its layout
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(8)  # Spacing between icon and text
        
        # Create icon label
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.hide()
        
        # Create text label
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to content layout
        content_layout.addStretch()
        content_layout.addWidget(self.icon_label)
        content_layout.addWidget(self.label)
        content_layout.addStretch()
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.button)
        
        # Add content widget on top of button
        content_layout = QVBoxLayout(self.button)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.content)
        
        # Forward the clicked signal
        self.clicked = self.button.clicked
    
    def setText(self, text):
        self.label.setText(text)
    
    def text(self):
        return self.label.text()
    
    def setIcon(self, icon):
        if not icon.isNull():
            pixmap = icon.pixmap(self.iconSize())
            self.icon_label.setPixmap(pixmap)
            self.icon_label.show()
        else:
            self.icon_label.hide()
    
    def setIconSize(self, size):
        self._icon_size = size
        self.icon_label.setFixedSize(size)
        if self.icon_label.pixmap():
            scaled_pixmap = self.icon_label.pixmap().scaled(
                size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
    
    def iconSize(self):
        return getattr(self, '_icon_size', QSize(32, 32))
    
    def setStyleSheet(self, style):
        self.button.setStyleSheet(style)
        super().setStyleSheet("background: transparent;")
    
    def setSizePolicy(self, *args, **kwargs):
        self.button.setSizePolicy(*args, **kwargs)

class DeskControllerUI(QMainWindow):
    def __init__(self, config, kiosk_mode=False, has_touch_screen=False):
        super().__init__()
        self.base_dir = get_base_dir()
        self.config = config
        self.kiosk_mode = kiosk_mode
        self.has_touch_screen = has_touch_screen
        
        # Get screen resolution
        target_display = self.config.get('display', {}).get('primary_display', '')
        self.screen_resolution = get_screen_resolution(target_display)
        print(f"Screen resolution: {self.screen_resolution}")
        
        self.init_ui()
    
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
            target_display = self.config.get('display', {}).get('primary_display', '')
            target_geometry = get_display_position(target_display)
            
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
        
        # Adjust for touch screen if detected
        if self.has_touch_screen:
            # Increase button size for better touch targets
            padding = max(padding, 10)  # Minimum 10px padding for touch
            font_size = max(font_size, 14)  # Minimum 14px font for touch
            
            # Increase spacing between buttons for touch
            grid.setSpacing(max(grid.spacing(), 15))
        
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
            button = WrappingButton(name)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Set button style
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: {border_radius}px;
                    padding: {padding}px;
                    min-height: {button_height * 0.8}px;
                    min-width: {button_width * 0.8}px;
                }}
                QPushButton:hover {{
                    background-color: {lighten_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {darken_color(color)};
                }}
                QLabel {{
                    color: {text_color};
                    font-size: {font_size}px;
                    font-weight: bold;
                    background-color: transparent;
                }}
            """)
            
            # Set icon if provided in config
            if icon_path:  # This will be falsy if icon is not in config or is empty string
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
    
    def eventFilter(self, obj, event):
        """Filter events at the application level"""
        if event.type() == QEvent.KeyPress:
            # Check for Ctrl+C keyboard combination
            if (event.key() == Qt.Key_C and 
                event.modifiers() & Qt.ControlModifier):
                print("\nCtrl+C pressed. Shutting down...")
                QApplication.quit()
                return True
                
            # Exit fullscreen with Escape key
            if event.key() == Qt.Key_Escape:
                if self.isFullScreen():
                    self.showNormal()
                    return True
                
            # Toggle fullscreen with F11
            elif event.key() == Qt.Key_F11:
                if self.isFullScreen():
                    self.showNormal()
                else:
                    self.showFullScreen()
                return True
                
        # Pass the event on to the parent class
        return super().eventFilter(obj, event) 