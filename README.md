# Desk Controller

A configurable button dashboard for Raspberry Pi that runs fullscreen and executes apps or scripts when buttons are pressed.

## Features

- JSON configuration for button layout and actions
- Customizable icons for each button
- Dynamic grid layout with configurable rows and columns
- Fullscreen operation optimized for small displays
- Lightweight and performant for Raspberry Pi 4
- Automatic sudo permissions for scripts that require elevated privileges

## System Requirements

- Raspberry Pi (any model)
- DSI display connected
- Raspberry Pi OS or compatible Linux distribution
- Python 3.6 or higher

The application will automatically check if it's running on a Raspberry Pi and if a DSI display is connected. If either check fails, the application will not start.

## Installation

### Automatic Installation (Recommended)

Use the installation script for a complete setup:
```
sudo ./install.sh
```

This will:
1. Check if the system meets the requirements
2. Create a Python virtual environment
3. Install all dependencies
4. Generate sample icons
5. Set up desktop entries and autostart
6. Configure sudo permissions for scripts that need elevated privileges

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
   python setup/create_icons.py
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
    },
    {
      "name": "Custom Script",
      "icon": "icons/script.png",
      "command": "@/hello.sh"
    }
  ]
}
```

For detailed configuration options, see the [CONFIG.md](CONFIG.md) file.

## Custom Scripts

You can include custom scripts with your application by placing them in the `scripts/` directory and referencing them with the `@/` prefix in your button commands.

For example:
```
"command": "@/hello.sh"
```

This will execute the script at `scripts/hello.sh` relative to the application directory. All scripts in the `scripts/` directory will be copied to the installation location during installation.

### Scripts with Sudo Commands

If your scripts contain commands that require sudo privileges, the installation process will automatically detect these and configure the necessary permissions. This allows your scripts to run sudo commands without requiring a password.

For example, if your script contains:
```bash
sudo shutdown -h now
```

The installation will automatically add the necessary permissions to the sudoers file.

## Project Structure

The project is organized as follows:

- `main.py` - The main application
- `config.json` - Configuration file
- `setup/` - Setup and installation scripts
  - `install.sh` - Main installation script
  - `uninstall.sh` - Uninstallation script
  - `setup.sh` - Service setup script
  - `setup_kiosk.sh` - Kiosk mode setup script
  - `update_config.sh` - Configuration update script
  - `create_icons.py` - Icon generation script
  - `config_validator.py` - Configuration validation script
  - `test_config.py` - Configuration testing script
  - `system_check.py` - System requirements check script
- `scripts/` - Directory for custom scripts
- `icons/` - Directory for button icons

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
sudo ./uninstall.sh
```

This will:
1. Remove desktop entries and autostart configuration
2. Optionally remove the virtual environment
3. Keep your configuration files intact

## License

MIT 