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

# Detect Raspberry Pi (Raspbian, Bookworm, Trixie, etc.)
if grep -qi "ID=raspbian" /etc/os-release || [ -f /etc/rpi-issue ] || ([ -f /proc/device-tree/model ] && grep -qi "Raspberry Pi" /proc/device-tree/model); then
    echo "🖥️  Raspberry Pi detected. Configuring autostart..."
    
    # Touch and screen rotation script
    echo "🌀 Creating touch_rotate.sh..."
    sudo tee "$TOUCH_SCRIPT" > /dev/null << 'EOF'
#!/bin/sh
# Wait for display server to start (if run during boot)
sleep 3

# Detect session type (robustly, for SSH sessions)
SESSION_TYPE="$XDG_SESSION_TYPE"
if [ "$SESSION_TYPE" != "wayland" ] && [ "$SESSION_TYPE" != "x11" ]; then
    # Find any graphical session for the current user
    GUISESSION=$(loginctl list-sessions --no-legend | grep "$(whoami)" | awk '{print $1}')
    for sid in $GUISESSION; do
        stype=$(loginctl show-session "$sid" -p Type --value)
        if [ "$stype" = "wayland" ] || [ "$stype" = "x11" ]; then
            SESSION_TYPE="$stype"
            break
        fi
    done
fi

if [ "$SESSION_TYPE" = "wayland" ]; then
    echo "🖥️  Wayland session detected. Using wlr-randr..."
    # Set defaults if run from SSH
    export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
    wlr-randr --output DSI-1 --transform 90
elif [ "$SESSION_TYPE" = "x11" ]; then
    echo "🖥️  X11 session detected. Using xrandr..."
    # Note: touch is handled via udev for both but we keep xinput as fallback if udev fails
    xinput --set-prop '10-0038 generic ft5x06 (79)' 'Coordinate Transformation Matrix' 0 -1 1 1 0 -0.02 0 0 1 || true
    xrandr --output DSI-1 --rotate left
else
    echo "⚠️  Could not detect graphical session type ($SESSION_TYPE). Skipping rotation."
fi
EOF
    sudo chmod +x "$TOUCH_SCRIPT"

    # Persistent touch rotation via udev (works for both X11 and Wayland)
    echo "👆 Creating udev rule for touch rotation..."
    sudo tee /etc/udev/rules.d/99-barbot-touch.rules > /dev/null << 'EOF'
ENV{ID_INPUT_TOUCHSCREEN}=="1", ENV{LIBINPUT_CALIBRATION_MATRIX}="0 -1 1 1 0 -0.02 0 0 1"
EOF
    sudo udevadm control --reload-rules
    sudo udevadm trigger --subsystem-match=input

    # Autostart configuration for different environments
    
    # 1. LXDE (X11)
    echo "  - Configuring LXDE autostart..."
    mkdir -p "$AUTOSTART_PATH"
    cat > "$AUTOSTART_FILE" << EOL
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
point-rpi
@$TOUCH_SCRIPT
@$VENV_PATH/bin/barbot
EOL

    # 2. Labwc (Wayland - Trixie)
    echo "  - Configuring Labwc autostart..."
    LABWC_AUTOSTART_DIR="$HOME/.config/labwc"
    mkdir -p "$LABWC_AUTOSTART_DIR"
    {
        echo "$TOUCH_SCRIPT &"
        echo "$VENV_PATH/bin/barbot &"
    } > "$LABWC_AUTOSTART_DIR/autostart"
    chmod +x "$LABWC_AUTOSTART_DIR/autostart"

    # 3. Wayfire (Wayland - Bookworm)
    WAYFIRE_CONFIG="$HOME/.config/wayfire.ini"
    if [ -f "$WAYFIRE_CONFIG" ]; then
        echo "  - Configuring Wayfire autostart..."
        # Add to [autostart] section if not already there
        if ! grep -q "barbot=" "$WAYFIRE_CONFIG"; then
            sed -i '/\[autostart\]/a barbot = '"$VENV_PATH"'/bin/barbot\ntouch_rotate = '"$TOUCH_SCRIPT"'' "$WAYFIRE_CONFIG"
        fi
    fi

else
    echo "❌ Not a Raspberry Pi system. Skipping autostart config."
fi

# Run initial setup
echo "⚙️  Running initial setup..."
"$VENV_PATH/bin/python3" -m barbot.setup

echo "✅ BarBot installation/update complete!"