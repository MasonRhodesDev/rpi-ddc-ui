#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./update_kiosk_service.sh)"
  exit 1
fi

echo "Updating kiosk service configuration..."

# Create kiosk service file
cat > /etc/systemd/system/kiosk.service << EOF
[Unit]
Description=Kiosk Mode Service for Desk Controller
After=network.target

[Service]
User=deskcontroller
Group=deskcontroller
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/deskcontroller/.Xauthority
WorkingDirectory=/home/deskcontroller
ExecStartPre=/usr/bin/sudo /usr/bin/chvt 7
ExecStart=/usr/bin/xinit /home/deskcontroller/.xsession -- :0 -nolisten tcp vt7
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# Create .xsession file for deskcontroller user
if [ -f "xsession_template" ]; then
    cp xsession_template /home/deskcontroller/.xsession
    chmod +x /home/deskcontroller/.xsession
    chown deskcontroller:deskcontroller /home/deskcontroller/.xsession
    echo "Created .xsession file for deskcontroller user"
fi

# Allow deskcontroller to use sudo for chvt without password
if ! grep -q "deskcontroller ALL=(ALL) NOPASSWD: /usr/bin/chvt" /etc/sudoers.d/deskcontroller 2>/dev/null; then
    echo "deskcontroller ALL=(ALL) NOPASSWD: /usr/bin/chvt" > /etc/sudoers.d/deskcontroller
    chmod 440 /etc/sudoers.d/deskcontroller
    echo "Added sudo permission for deskcontroller to use chvt"
fi

# Reload systemd configuration
systemctl daemon-reload
echo "Reloaded systemd configuration"

# Enable and restart kiosk service
systemctl enable kiosk.service
systemctl restart kiosk.service
echo "Enabled and restarted kiosk service"

echo "Kiosk service configuration updated successfully!" 