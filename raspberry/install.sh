#!/bin/bash
set -e

# --- Configuration ---
GIT_REPO="Robert2611/BarBot4"
PYTHON_PACKAGE_DIR="raspberry"
VENV_PATH="$HOME/barbot-venv"
VERBOSE=false

# --- Argument Parsing ---
for arg in "$@"; do
    case $arg in
        -v|--verbose)
        VERBOSE=true
        shift
        ;;
    esac
done

if [ "$VERBOSE" = true ]; then
    REDIRECT="/dev/stdout"
else
    REDIRECT="/dev/null"
fi

# --- Helper Functions ---
log() {
    echo "$1"
}

error() {
    echo "❌ $1" >&2
    exit 1
}

# --- Installation Steps ---

check_requirements() {
    # 1. Root check
    if [[ $EUID -eq 0 ]]; then
        error "Do NOT run this script as root or with sudo. Please run it as a normal user."
    fi

    # 2. OS check
    if [ ! -f /etc/os-release ]; then
        error "Could not detect OS. This script only supports modern Raspberry Pi OS."
    fi
    
    OS_CODENAME=$(grep "VERSION_CODENAME=" /etc/os-release | cut -d= -f2)
    if [[ "$OS_CODENAME" != "bookworm" && "$OS_CODENAME" != "trixie" ]]; then
        error "This script only supports modern Raspberry Pi OS (Bookworm or Trixie). Detected: $OS_CODENAME"
    fi
    
    log "  - Modern Raspberry Pi OS detected ($OS_CODENAME)."
}

install_dependencies() {
    sudo apt-get update > "$REDIRECT" 2>&1
    sudo apt-get -y -q install \
        bluetooth bluez \
        python3-pyqt5 python3-pip python3-venv \
        pi-bluetooth wlr-randr > "$REDIRECT" 2>&1
    
    log "  - Enabling Bluetooth services..."
    sudo systemctl start hciuart > "$REDIRECT" 2>&1 || log "  ⚠️  Failed to start hciuart, continuing..."
}

setup_python() {
    python3 -m venv --system-site-packages "$VENV_PATH"
}

install_barbot() {
    # Detect if we are in the BarBot repository
    if [ -f "pyproject.toml" ] && grep -q 'name = "barbot"' pyproject.toml && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        log "  - Development mode detected: Installing from local source..."
        "$VENV_PATH/bin/pip" install -e . > "$REDIRECT" 2>&1
    else
        log "  - Release mode: Installing latest release from GitHub..."
        LATEST_TAG=$(curl -s "https://api.github.com/repos/$GIT_REPO/releases/latest" | grep -Po '"tag_name": "\K.*?(?=")')
        [ -z "$LATEST_TAG" ] && LATEST_TAG="master"
        
        log "  - Installing version $LATEST_TAG..."
        "$VENV_PATH/bin/pip" install --upgrade "git+https://github.com/$GIT_REPO.git@$LATEST_TAG#subdirectory=$PYTHON_PACKAGE_DIR" > "$REDIRECT" 2>&1
    fi
}

configure_system() {
    # 1. Labwc (Wayland - Trixie)
    if [ "$OS_CODENAME" = "trixie" ]; then
        log "  - Configuring Labwc autostart..."
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
            log "  - Configuring Wayfire rotation..."
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
        else
            log "  ⚠️  Wayfire config not found at $WAYFIRE_CONFIG, skipping rotation config."
        fi
    fi
}

run_setup() {
    "$VENV_PATH/bin/python3" -m barbot.setup
}

# --- Main Execution ---
main() {
    log "🔍 Checking system requirements..."
    check_requirements
    
    log "📦 Installing system dependencies (apt)..."
    install_dependencies
    
    log "🐍 Setting up Python virtual environment..."
    setup_python
    
    log "🛠️  Installing BarBot package..."
    install_barbot
    
    log "🖥️  Configuring system (rotation & autostart)..."
    configure_system
    
    log "⚙️  Running initial setup..."
    run_setup
    
    log "✅ BarBot installation/update complete!"
}

# Run the script
main "$@"