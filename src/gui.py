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
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    r = min(255, r + amount)
    g = min(255, g + amount)
    b = min(255, b + amount)
    
    return f"#{r:02x}{g:02x}{b:02x}"

def darken_color(hex_color, amount=20):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    r = max(0, r - amount)
    g = max(0, g - amount)
    b = max(0, b - amount)
    
    return f"#{r:02x}{g:02x}{b:02x}"

class WrappingButton(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        
        self.button = QPushButton(self)
        
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(8)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.hide()
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        
        content_layout.addStretch()
        content_layout.addWidget(self.icon_label)
        content_layout.addWidget(self.label)
        content_layout.addStretch()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.button)
        
        content_layout = QVBoxLayout(self.button)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.content)
        
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
        
        target_display = self.config.get('display', {}).get('primary_display', '')
        self.screen_resolution = get_screen_resolution(target_display)
        print(f"Screen resolution: {self.screen_resolution}")
        
        self.init_ui()
    
    def center_window(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
    
    def init_ui(self):
        self.setWindowTitle('Desk Controller')
        
        bg_color = self.config['layout'].get('background_color', '#2E3440')
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(bg_color))
        self.setPalette(palette)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        grid = QGridLayout(content_widget)
        
        screen_width, screen_height = self.screen_resolution
        
        spacing_percent = 0.01
        button_spacing = max(int(min(screen_width, screen_height) * spacing_percent), 2)
        
        margin_percent = 0.02
        margin = max(int(min(screen_width, screen_height) * margin_percent), 5)
        
        grid.setSpacing(button_spacing)
        grid.setContentsMargins(margin, margin, margin, margin)
        
        self.create_buttons(grid)
        
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        
        if not self.kiosk_mode:
            width = min(int(screen_width * 0.8), 800)
            height = min(int(screen_height * 0.8), 600)
            self.resize(width, height)
            self.center_window()
            self.show()
        else:
            target_display = self.config.get('display', {}).get('primary_display', '')
            target_geometry = get_display_position(target_display)
            
            if target_geometry:
                pos_x, pos_y, width, height = target_geometry
                print(f"Setting window geometry to match {target_display}: {pos_x}, {pos_y}, {width}, {height}")
                
                self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
                
                self.setGeometry(pos_x, pos_y, width, height)
                
                self.show()
                
                if self.config['layout'].get('hide_cursor', False):
                    QApplication.setOverrideCursor(Qt.BlankCursor)
            else:
                print("Could not find target display geometry, falling back to fullscreen")
                self.showFullScreen()
                if self.config['layout'].get('hide_cursor', False):
                    QApplication.setOverrideCursor(Qt.BlankCursor)
    
    def create_buttons(self, grid):
        rows = self.config['layout'].get('rows', 2)
        columns = self.config['layout'].get('columns', 3)
        
        screen_width, screen_height = self.screen_resolution
        
        available_width = screen_width * 0.9
        available_height = screen_height * 0.9
        
        button_width = int(available_width / columns)
        button_height = int(available_height / rows)
        
        font_size = max(int(min(button_width, button_height) * 0.1), 8)
        
        padding = max(int(min(button_width, button_height) * 0.05), 3)
        border_radius = max(int(min(button_width, button_height) * 0.05), 3)
        
        icon_size = max(int(min(button_width, button_height) * 0.3), 16)
        
        if self.has_touch_screen:
            padding = max(padding, 10)
            font_size = max(font_size, 14)
            
            grid.setSpacing(max(grid.spacing(), 15))
        
        print(f"Button dimensions: {button_width}x{button_height}")
        print(f"Font size: {font_size}, Padding: {padding}, Icon size: {icon_size}")
        
        for button_config in self.config['buttons']:
            name = button_config.get('name', 'Button')
            icon_path = button_config.get('icon', '')
            command = button_config.get('command', '')
            color = button_config.get('color', '#88C0D0')
            text_color = button_config.get('text_color', '#ECEFF4')
            position = button_config.get('position', [0, 0])
            
            button = WrappingButton(name)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
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
            
            if icon_path:
                if not os.path.isabs(icon_path):
                    icon_path = os.path.join(self.base_dir, icon_path)
                
                if os.path.exists(icon_path):
                    button.setIcon(QIcon(icon_path))
                    button.setIconSize(QSize(icon_size, icon_size))
            
            button.clicked.connect(lambda checked, cmd=command: self.execute_command(cmd))
            
            row, col = position
            if 0 <= row < rows and 0 <= col < columns:
                grid.addWidget(button, row, col)
    
    def execute_command(self, command):
        try:
            if command.startswith('@/'):
                script_path = command[2:]
                scripts_dir = os.path.join(self.base_dir, 'scripts')
                full_script_path = os.path.join(scripts_dir, script_path)
                if os.path.exists(full_script_path):
                    if not os.access(full_script_path, os.X_OK):
                        os.chmod(full_script_path, os.stat(full_script_path).st_mode | 0o111)
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
        if event.type() == QEvent.KeyPress:
            if (event.key() == Qt.Key_C and 
                event.modifiers() & Qt.ControlModifier):
                print("\nCtrl+C pressed. Shutting down...")
                QApplication.quit()
                return True
                
            if event.key() == Qt.Key_Escape:
                if self.isFullScreen():
                    self.showNormal()
                    return True
                
            elif event.key() == Qt.Key_F11:
                if self.isFullScreen():
                    self.showNormal()
                else:
                    self.showFullScreen()
                return True
                
        return super().eventFilter(obj, event) 