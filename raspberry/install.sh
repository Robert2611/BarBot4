#!/bin/bash
set -e

INSTALL_BIN="/usr/local/bin"
AUTOSTART_PATH="$HOME/.config/lxsession/LXDE-pi"
AUTOSTART_FILE="$AUTOSTART_PATH/autostart"
TOUCH_SCRIPT="$INSTALL_BIN/touch_rotate.sh"
GIT_REPO="Robert2611/BarBot4"
PYTHON_PACKAGE_DIR="raspberry"
VENV_PATH="$HOME/barbot-venv"

# Do NOT run this script as root or with sudo.
# It will use sudo internally for system commands when needed.
if [[ $EUID -eq 0 ]]; then
    echo "❌ Do NOT run this script as root or with sudo."
    echo "Please run it as a normal user. It will ask for your password when needed."
    exit 1
fi

echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get -y -q install \
    bluetooth bluez libbluetooth-dev \
    python3-pyqt5 python3-pip python3-venv \
    pi-bluetooth

echo "🔧 Enabling Bluetooth..."
sudo systemctl start hciuart || echo "⚠️  Failed to start hciuart, continuing..."

echo "🐍 Setting up Python virtual environment..."
python3 -m venv --system-site-packages "$VENV_PATH"

# Detect if we are in the BarBot repository
if [ -f "pyproject.toml" ] && grep -q 'name = "barbot"' pyproject.toml && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "🛠️  Development mode detected: Installing from local source..."
    "$VENV_PATH/bin/pip" install -e .
else
    echo "📦 Release mode: Installing latest release from GitHub..."
    LATEST_TAG=$(curl -s "https://api.github.com/repos/$GIT_REPO/releases/latest" | grep -Po '"tag_name": "\K.*?(?=")')
    # Fallback to master if tag cannot be determined
    [ -z "$LATEST_TAG" ] && LATEST_TAG="master"
    echo "🔗 Installing version $LATEST_TAG..."
    "$VENV_PATH/bin/pip" install --upgrade "git+https://github.com/$GIT_REPO.git@$LATEST_TAG#subdirectory=$PYTHON_PACKAGE_DIR"
fi

# Detect Raspberry Pi (Raspbian, Bookworm, Trixie, etc.)
if grep -qi "ID=raspbian" /etc/os-release || [ -f /etc/rpi-issue ] || ([ -f /proc/device-tree/model ] && grep -qi "Raspberry Pi" /proc/device-tree/model); then
    echo "🖥️  Raspberry Pi detected. Configuring LXDE autostart..."
    mkdir -p "$AUTOSTART_PATH"

    cat > "$AUTOSTART_FILE" << EOL
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
point-rpi
@$TOUCH_SCRIPT
@$VENV_PATH/bin/barbot
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
    echo "❌ Not a Raspberry Pi system. Skipping autostart config."
fi

# Run initial setup
echo "⚙️  Running initial setup..."
"$VENV_PATH/bin/python3" -m barbot.setup

echo "✅ BarBot installation/update complete!"