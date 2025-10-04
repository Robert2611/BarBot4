# BarBot4
Der BarBot4 ist eine automatische Cocktail Maschine.

## Installation

### Raspberry Pi OS installieren
Das [Raspberry Pi OS](https://www.raspberrypi.org/downloads/) herunter laden und nach der Anleitung auf der Seite auf eine SD-Karte installieren.
### Verbindung mit dem Pi herstellen
Hier gibt es zwei Möglichkeiten:
1. Mit Tastatur
Einfach eine Tastatur per USB an den Pi anschließen und die Befehle eingeben
2. Über SSH im Netzwerk
Am einfachsten ist es sich direkt über SSH mit dem Pi zu verbinden.
Dazu direkt nach dem Erstellen der SD-Karte im "Boot" Ordner eine Datei mit dem Namen "wpa_supplicant.conf" anlegen und mit folgendem Inhalt füllen:
```text
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="YOUR_SSID"
    psk="YOUR_WIFI_PASSWORD"
    key_mgmt=WPA-PSK
}
```
Hier einfach die SSID und das Passwort eures WLAN Netzwerks eintragen.
Um SSH zu erlauben, muss im "Boot" Ordner noch eine leere Datei mit dem Namen "ssh" angelegt werden.
Nun könnt ihr euch z.B. mit [Putty](https://www.putty.org/) unter Windows direkt über das Netzwerk auf den Pi aufschalten.
### BarBot4 installieren
War noch kein Barbot bisher installiert, so muss das System erst vorbereitet werden.
Dazu zuerst den Inhalt von [install.sh](raspberry/install.sh) ausführen oder die Datei herunterladen und dann ausführen.
### BarBot4 updaten
```bash
LATEST_TAG=$(curl -s https://api.github.com/repos/Robert2611/BarBot4/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
python3 -m pip install "git+https://github.com/Robert2611/BarBot4.git@$LATEST_TAG#subdirectory=raspberry"
barbot-setup
```
## License
[MIT](https://choosealicense.com/licenses/mit/)
