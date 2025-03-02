#!/bin/bash

echo "Uninstalling Desk Controller..."

# Remove desktop entries
echo "Removing desktop entries..."
rm -f ~/.local/share/applications/desk-controller.desktop
rm -f ~/.config/autostart/desk-controller.desktop

# Remove generated desktop file in current directory
rm -f desk-controller.desktop

# Ask if user wants to remove virtual environment
read -p "Do you want to remove the virtual environment? (y/n): " remove_venv
if [[ $remove_venv == "y" || $remove_venv == "Y" ]]; then
    echo "Removing virtual environment..."
    rm -rf venv
fi

echo "Uninstallation complete!"
echo "Note: The application files remain in this directory."
echo "You can delete this directory manually if you no longer need it."
echo ""
echo "To completely remove all files, run:"
echo "  rm -rf $(pwd)" 