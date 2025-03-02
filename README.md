# Desk Controller

A configurable button dashboard for Raspberry Pi that runs fullscreen and executes apps or scripts when buttons are pressed.

## Features

- JSON configuration for button layout and actions
- Customizable icons for each button
- Dynamic grid layout with configurable rows and columns
- Fullscreen operation optimized for small displays
- Lightweight and performant for Raspberry Pi 4

## Installation

### Automatic Installation (Recommended)

Use the installation script for a complete setup:
```
./install.sh
```

This will:
1. Create a Python virtual environment
2. Install all dependencies
3. Generate sample icons
4. Set up desktop entries and autostart

### Manual Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Generate icons:
   ```
   python create_icons.py
   ```
5. Configure your buttons in `config.json`
6. Run the application:
   ```
   python main.py
   ```

## Running the Application

After installation, you can run the application with:
```
source venv/bin/activate && ./main.py
```

Or use the desktop entry created during installation.

## Configuration

Edit the `config.json` file to configure your buttons. Example configuration:

```json
{
  "layout": {
    "rows": 2,
    "columns": 3
  },
  "buttons": [
    {
      "name": "Terminal",
      "icon": "icons/terminal.png",
      "command": "lxterminal"
    },
    {
      "name": "Web Browser",
      "icon": "icons/browser.png",
      "command": "chromium-browser"
    }
  ]
}
```

For detailed configuration options, see the [CONFIG.md](CONFIG.md) file.

## Auto-start on boot

The installation script sets up the application to start automatically when your Raspberry Pi boots.

If you need to set this up manually:

1. Edit `/etc/xdg/lxsession/LXDE-pi/autostart`
2. Add the following line:
   ```
   @/path/to/venv/bin/python /path/to/desk-controller/main.py
   ```

## Uninstallation

To uninstall the application, run:
```
./uninstall.sh
```

This will:
1. Remove desktop entries and autostart configuration
2. Optionally remove the virtual environment
3. Keep your configuration files intact

## License

MIT 