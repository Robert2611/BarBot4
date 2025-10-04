#!/bin/bash
set -e

INSTALL_BIN="/usr/local/bin"
AUTOSTART_PATH="$HOME/.config/lxsession/LXDE-pi"
AUTOSTART_FILE="$AUTOSTART_PATH/autostart"
TOUCH_SCRIPT="$INSTALL_BIN/touch_rotate.sh"
GIT_REPO="Robert2611/BarBot4"
PYTHON_PACKAGE_DIR="raspberry"

# Warn if not running as root
if [[ $EUID -ne 0 ]]; then
    echo "⚠️  Some commands require root. Consider running with sudo."
fi

echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get -y -q install \
    bluetooth bluez libbluetooth-dev \
    python3-pyqt5 python3-pip

echo "🔧 Enabling Bluetooth..."
sudo systemctl start hciuart || echo "⚠️  Failed to start hciuart, continuing..."

# Detect Raspbian
if grep -qi "ID=raspbian" /etc/os-release; then
    echo "🖥️  Configuring LXDE autostart..."

    mkdir -p "$AUTOSTART_PATH"

    cat > "$AUTOSTART_FILE" << EOL
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
point-rpi
@$TOUCH_SCRIPT
@python3 -m barbot
EOL

    echo "🌀 Creating touch_rotate.sh..."
    sudo tee "$TOUCH_SCRIPT" > /dev/null << 'EOF'
#!/bin/sh
sleep 3
xinput --set-prop 'raspberrypi-ts' 'Coordinate Transformation Matrix' 0 -1 1 1 0 -0.02 0 0 1
xrandr --output DSI-1 --rotate left
EOF

    sudo chmod +x "$TOUCH_SCRIPT"
else
    echo "❌ Not a Raspbian system. Skipping autostart config."
fi

echo "📦 Fetching latest BarBot release tag from GitHub..."
LATEST_TAG=$(curl -s "https://api.github.com/repos/$GIT_REPO/releases/latest" | grep -Po '"tag_name": "\K.*?(?=")')
LATEST_TAG=python_project
echo "🔗 Installing $GIT_REPO@$LATEST_TAG via pip..."
python3 -m pip install "git+https://github.com/$GIT_REPO.git@$LATEST_TAG#subdirectory=$PYTHON_PACKAGE_DIR"

# echo and run initial setup	
python3 -m barbot.setup