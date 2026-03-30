# BarBot4

BarBot4 is a high-end, automated cocktail-mixing machine designed for precision and ease of use. It combines a Raspberry Pi-powered touch interface with modular microcontroller-based hardware to deliver perfectly mixed drinks every time.

## ✨ Features

- **Automated Mixing**: Precise control over ingredient dispensing and sequence.
- **Modular Design**: Support for peripheral modules like mixers, crushers, and straw dispensers.
- **Smart Scale Integration**: Real-time weight tracking for accurate pours.
- **Touchscreen GUI**: Modern, user-friendly interface built with PyQt5.
- **Customizable Recipes**: Easily create and manage your own cocktail database.
- **Wireless Communication**: Bluetooth-based control between the Pi and hardware sub-modules.

## 🛠️ Hardware Requirements

To build a BarBot4, you will need:
- **Main Controller**: Raspberry Pi (Bookworm or Trixie recommended) with a touchscreen.
- **Mainboard**: ESP32-based controller for motor and pump management.
- **Balance Board (Mandatory)**: An Atmega328p-based module for accurate weight sensing.
    - **Sensor**: HX711 Load Cell amplifier for weight measurement.
- **Optional Sub-modules**: AVR (Arduino) based modules for specific functions (e.g., Ice Crusher, Mixer, Straw Dispenser).
- **Firmware**: Pre-compiled binaries for all modules are available in the [GitHub Releases](https://github.com/Robert2611/BarBot4/releases).

## 🚀 Quick Start

### 1. Firmware Installation
For ease of setup, pre-compiled firmware binaries are automatically generated and attached to each [GitHub Release](https://github.com/Robert2611/BarBot4/releases).

1. Download the `firmware.zip` from the latest release.
2. Extract the archive on a Windows PC.
3. Run `flash.bat` and follow the on-screen instructions to flash your Mainboard (ESP32) or sub-modules (Atmega328p).
   - *Note: Flashing scripts for Linux/macOS users can be found in the `/firmware` directory.*

### 2. Pi Software Installation
The easiest way to set up the BarBot software on a fresh Raspberry Pi OS is to use the automated install script:

```bash
curl -sSL https://raw.githubusercontent.com/Robert2611/BarBot4/master/raspberry/install.sh | bash
```

This script handles dependencies, virtual environment setup, and system configuration. **It also configures the application to start automatically on boot**, so there is no need to run it manually after the initial setup.

## 🛠️ Development

If you are developing for BarBot4 or need to run it manually for testing, you can use the following commands:

### Running BarBot Manually
- `barbot`: Start the standard interface.
- `barbot-demo`: Start in demo mode (uses mockup hardware for testing).
- `barbot-with-log`: Start with console logging enabled.

### Local Installation
To install the package in editable mode from the repository:
```bash
cd raspberry
pip install -e .
```

## 📂 Project Structure

The project is organized to separate physical design, electronics, and software:
- `/CAD`: 3D models for the chassis and components.
- `/elektronik`: PCB designs and schematics.
- `/firmware`: Microcontroller source code (C++/PlatformIO).
- `/raspberry`: Main Python application logic and GUI.

For a detailed breakdown of all directories, please refer to [README_STRUCTURE.md](./README_STRUCTURE.md).

## 🤝 Contributing

Contributions are welcome! Whether it's a new recipe, a bug fix, or a feature request, feel free to open an issue or submit a pull request.

## 📜 License
[MIT](https://choosealicense.com/licenses/mit/)
