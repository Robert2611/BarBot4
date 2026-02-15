#!/bin/bash
set -e

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
    pi-bluetooth wlr-randr

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

# Detect modern Raspberry Pi OS (Bookworm, Trixie, etc.)
OS_CODENAME=$(grep "VERSION_CODENAME=" /etc/os-release | cut -d= -f2)
if [[ "$OS_CODENAME" != "bookworm" && "$OS_CODENAME" != "trixie" ]]; then
    echo "❌ This script only supports modern Raspberry Pi OS (Bookworm or Trixie)."
    echo "Detected OS: $OS_CODENAME. Aborting."
    exit 1
fi

echo "🖥️  Modern Raspberry Pi OS detected ($OS_CODENAME). Configuring autostart..."
    
# 1. Labwc (Wayland - Trixie)
if [ "$OS_CODENAME" = "trixie" ]; then
    echo "  - Configuring Labwc autostart..."
    LABWC_AUTOSTART_DIR="$HOME/.config/labwc"
    mkdir -p "$LABWC_AUTOSTART_DIR"
    {
        echo "wlr-randr --output DSI-1 --transform 90"
        echo "$VENV_PATH/bin/barbot &"
    } > "$LABWC_AUTOSTART_DIR/autostart"
    chmod +x "$LABWC_AUTOSTART_DIR/autostart"
fi

# 2. Wayfire (Wayland - Bookworm)
if [ "$OS_CODENAME" = "bookworm" ]; then
    WAYFIRE_CONFIG="$HOME/.config/wayfire.ini"
    if [ -f "$WAYFIRE_CONFIG" ]; then
        echo "  - Configuring Wayfire rotation..."
        # Add to [output:DSI-1] section
        if ! grep -q "\[output:DSI-1\]" "$WAYFIRE_CONFIG"; then
            cat >> "$WAYFIRE_CONFIG" << EOL

[output:DSI-1]
transform = 90
EOL
        fi
        # Add to [autostart] section
        if ! grep -q "barbot=" "$WAYFIRE_CONFIG"; then
            sed -i '/\[autostart\]/a barbot = '"$VENV_PATH"'/bin/barbot' "$WAYFIRE_CONFIG"
        fi
    fi
fi

# Run initial setup
echo "⚙️  Running initial setup..."
"$VENV_PATH/bin/python3" -m barbot.setup

echo "✅ BarBot installation/update complete!"