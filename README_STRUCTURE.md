# BarBot4 Project Structure

This file provides an overview of the folder organization for the BarBot4 project.

## Root Directory
- `/CAD`: 3D models and mechanical designs for the bar bot's physical structure.
- `/elektronik`: PCB designs, schematics, and other electronic documentation.
- `/firmware`: Source code for all microcontroller-based components.
    - `/mainboard`: Primary controller firmware (PlatformIO project).
    - `/balance`: Firmware for the integrated scale/balance.
    - `/shared`: Common code and headers shared across multiple firmware projects.
    - `/mixer`, `/crusher`, `/straw`, `/sugar`: Firmware for specialized peripheral modules.
- `/raspberry`: Main application and control software running on a Raspberry Pi.
    - `/recipe-collections`: Organized recipe sets (e.g., `standard`, `party-set`).
    - `/barbot`: The core Python source code.
        - `/gui`: PyQt5-based user interface components.
        - `/logic`: Core business logic, hardware interaction, and cocktail preparation flows.
        - `/test`: Unit tests and integration tests for the Python application.
    - `install.sh`: Automated setup script for initializing the Raspberry Pi environment.
- `/info`: General project documentation, build guides, and auxiliary information.

## Technology Stack
- **Firmware**: C++ (ESP32 for the Mainboard, AVR/Arduino for sub-modules) managed via PlatformIO.
- **Pi App**: Python 3 with PyQt5 for the GUI.
- **Hardware Communication**: Serial/Bluetooth-based protocols between the Raspberry Pi and sub-modules.
