# Configuration Guide

The Desk Controller application is configured using a JSON file named `config.json`. This document explains all the available configuration options.

## Configuration Structure

The configuration file has two main sections:

1. `layout` - Controls the overall layout of the application
2. `buttons` - Defines the buttons that appear in the application

Example:

```json
{
  "layout": {
    "rows": 2,
    "columns": 3,
    "button_spacing": 10,
    "background_color": "#2E3440",
    "fullscreen": true
  },
  "buttons": [
    {
      "name": "Terminal",
      "icon": "icons/terminal.png",
      "command": "lxterminal",
      "color": "#88C0D0",
      "text_color": "#ECEFF4",
      "position": [0, 0]
    },
    // More buttons...
  ]
}
```

## Layout Options

The `layout` section supports the following options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `rows` | Integer | 2 | Number of rows in the button grid |
| `columns` | Integer | 3 | Number of columns in the button grid |
| `button_spacing` | Integer | 10 | Spacing between buttons in pixels |
| `background_color` | String | "#2E3440" | Background color of the application (hex format) |
| `fullscreen` | Boolean | true | Whether to start the application in fullscreen mode |

## Button Options

Each button in the `buttons` array supports the following options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | String | "Button" | The text displayed on the button |
| `icon` | String | "" | Path to the icon image (relative to the application directory) |
| `command` | String | "" | The command to execute when the button is clicked. Can use `@/script.sh` format to reference scripts in the `scripts/` directory |
| `color` | String | "#88C0D0" | Background color of the button (hex format) |
| `text_color` | String | "#ECEFF4" | Text color of the button (hex format) |
| `position` | Array | [0, 0] | Position of the button in the grid as [row, column] |

## Custom Scripts

You can include custom scripts with your application by placing them in the `scripts/` directory and referencing them with the `@/` prefix in your button commands.

For example:
```json
{
  "name": "Custom Script",
  "icon": "icons/script.png",
  "command": "@/hello.sh"
}
```

This will execute the script at `scripts/hello.sh` relative to the application directory. All scripts in the `scripts/` directory will be copied to the installation location during installation.

## Command Examples

Here are some example commands you can use:

- Launch applications: `"command": "chromium-browser"`
- Run scripts: `"command": "/path/to/script.sh"`
- System commands: `"command": "sudo reboot"`
- Open files: `"command": "xdg-open /path/to/file"`
- Run with arguments: `"command": "python3 /path/to/script.py --arg value"`

## Dynamic Layout

You can dynamically change the layout by editing the `config.json` file and restarting the application. The buttons will automatically adjust to the new layout.

To add a new row or column:
1. Increase the `rows` or `columns` value in the `layout` section
2. Add new buttons with positions in the new row/column

To remove a row or column:
1. Remove any buttons positioned in that row/column
2. Decrease the `rows` or `columns` value in the `layout` section

## Validation

The application includes a configuration validator that checks for common errors. You can run it manually with:

```
python config_validator.py
```

This will check for issues such as:
- Missing required fields
- Invalid color formats
- Button positions outside the grid
- Duplicate button positions
- Missing icon files 