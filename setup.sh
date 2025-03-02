#!/bin/bash

# Make scripts executable
chmod +x main.py
chmod +x config_validator.py

# Get absolute paths
WORKSPACE_DIR=$(pwd)
VENV_PYTHON="$WORKSPACE_DIR/venv/bin/python"

# Create desktop entry
cat > desk-controller.desktop << EOL
[Desktop Entry]
Name=Desk Controller
Comment=Button dashboard for Raspberry Pi
Exec=$VENV_PYTHON $WORKSPACE_DIR/main.py
Icon=$WORKSPACE_DIR/icons/app-icon.png
Terminal=false
Type=Application
Categories=Utility;
X-KeepTerminal=false
EOL

# Copy desktop entry to applications directory
mkdir -p ~/.local/share/applications/
cp desk-controller.desktop ~/.local/share/applications/

# Create autostart entry
mkdir -p ~/.config/autostart/
cp desk-controller.desktop ~/.config/autostart/

echo "Setup complete!"
echo "To start the application, run:"
echo "  source venv/bin/activate && ./main.py"
echo "The application will start automatically on boot." 