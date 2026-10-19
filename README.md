# desk-controller

A touch-screen button panel for a Raspberry Pi. Each button runs a command; the bundled scripts use DDC/CI (`ddcutil`) to switch monitor inputs and toggle picture-by-picture mode. It is built with PyQt5 and can install itself as an auto-starting kiosk.

## Hardware and software it expects

- A Raspberry Pi (or any Debian-like Linux box) with a touch display. The kiosk installer targets Raspberry Pi OS and a DSI or HDMI touch screen.
- For the monitor scripts: one or two DDC/CI capable monitors reachable over the Pi's I2C bus, plus `ddcutil` and passwordless `sudo` for it.
- Python 3 and PyQt5 (`sudo apt-get install python3-pyqt5`).

The input codes in the scripts (`0x0f` for DisplayPort, `0x11` for HDMI, `0xE9`/`0xE8` for PBP) are for one monitor family. Check yours with `ddcutil capabilities` and edit `scripts/` to match.

## Configure

1. `cp config.example.json config.json` and edit it. Options are described in [CONFIG.md](CONFIG.md). `config.json` is gitignored.
2. `cp scripts/monitors.env.example scripts/monitors.env` and put your monitor serial numbers in it (`sudo ddcutil detect` lists them). This file is gitignored too. You can instead export `DESK_PRIMARY_SN` and `DESK_SECONDARY_SN`, or point `DESK_MONITORS_ENV` at another file.

The config file is looked up in this order: `--config PATH`, the `DESK_CONTROLLER_CONFIG` environment variable, `/opt/desk-controller/config.json`, then `config.json` next to `main.py`. If none exists the program exits with an error naming the path it tried.

## Run

```
python3 main.py            # windowed
python3 main.py --kiosk    # fullscreen kiosk
python3 main.py --config /path/to/config.json
```

## Install as a kiosk on the Pi

`DESK_REMOTE=user@host ./setup-remote.sh` copies the app (including your local `config.json` and `scripts/monitors.env`) to the Pi over ssh and runs `main.py --install-service`, which installs packages, writes `~/.xinitrc`, sets up TTY1 autologin and enables I2C. It changes system configuration, so read `install_service()` in `main.py` first. The kiosk log goes to `~/.xinitrc.log`.

## License

MIT, see [LICENSE](LICENSE).
