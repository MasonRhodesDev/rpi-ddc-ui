# Desk Controller Kiosk Mode

This document explains how to set up and use the Desk Controller application in kiosk mode.

## What is Kiosk Mode?

Kiosk mode is a configuration that turns your Raspberry Pi into a dedicated Desk Controller device. When in kiosk mode:

- The system boots directly into the Desk Controller application
- No desktop environment is shown
- The application runs in fullscreen mode
- The cursor is hidden after a few seconds of inactivity
- Screen savers and power management are disabled

## Installation

To install the Desk Controller in kiosk mode:

1. Run the installation script as root:
   ```
   sudo ./install.sh
   ```

2. When prompted, choose "y" to set up kiosk mode:
   ```
   Do you want to set up kiosk mode (removes existing desktop environments)? (y/n): y
   ```

3. The script will:
   - Create a dedicated service user
   - Install the application
   - Configure the system to auto-start the application
   - Set up a kiosk session
   - Configure permissions based on your config.json

4. Reboot your system to apply the changes:
   ```
   sudo reboot
   ```

## How It Works

The kiosk mode setup:

1. Creates a dedicated user account (`deskcontroller`) with limited permissions
2. Disables any existing display manager
3. Uses a systemd service to start X directly with the Desk Controller application
4. Creates a custom X session that launches only the Desk Controller application
5. Disables screen savers and power management
6. Hides the cursor after 5 seconds of inactivity
7. Grants the service user permission to run only the commands specified in your config.json

## Display Configuration

The kiosk mode supports two display modes:

1. **Mirror Mode** (default): Mirrors the display across all connected monitors
2. **Single Display Mode**: Shows only on a specified monitor

To switch between these modes:

1. Edit the display configuration file:
   ```
   sudo nano /opt/desk-controller/configure_displays.sh
   ```

2. Change the `MODE` variable:
   - For mirroring across all displays: `MODE="mirror"`
   - For showing only on one display: `MODE="single"`

3. If using single mode, set the correct display name:
   ```
   PRIMARY_DISPLAY="HDMI-1"  # Change to match your small monitor
   ```
   
   You can find the correct display name by running `xrandr` when logged in as a regular user.

4. Save the file and reboot:
   ```
   sudo reboot
   ```

## Customization

You can customize the Desk Controller by editing the config.json file:

```
sudo nano /opt/desk-controller/config.json
```

After making changes, update the permissions:

```
sudo /opt/desk-controller/update_config.sh
```

## Troubleshooting

If the kiosk mode doesn't start properly:

1. Check the systemd service status:
   ```
   sudo systemctl status kiosk.service
   ```

2. Check the X session logs:
   ```
   sudo cat /home/deskcontroller/xsession.log
   ```

3. Check the display configuration logs:
   ```
   sudo cat /home/deskcontroller/display_config.log
   ```

4. Check the system journal for X server errors:
   ```
   sudo journalctl -xe
   ```

## Uninstallation

To uninstall and remove kiosk mode:

```
sudo /opt/desk-controller/uninstall.sh
```

This will remove the kiosk service and configuration files. 