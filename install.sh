#!/bin/bash

echo "Installing Desk Controller..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate icons
echo "Generating sample icons..."
python create_icons.py

# Make scripts executable
echo "Making scripts executable..."
chmod +x main.py
chmod +x config_validator.py
chmod +x create_icons.py
chmod +x setup.sh
chmod +x uninstall.sh

# Run setup script
echo "Running setup script..."
./setup.sh

echo "Installation complete!"
echo "You can now run the application with:"
echo "  source venv/bin/activate && ./main.py"
echo "The application will start automatically on boot." 