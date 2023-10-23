#!/bin/sh
INSTALL_FOLDER=~/barbot
DATA_FOLDER=~/.barbot

#create data folders if not exist
mkdir -p $DATA_FOLDER/log
mkdir -p $DATA_FOLDER/recipes
#copy recipes
rsync -a $INSTALL_FOLDER/data/recipes/. $DATA_FOLDER/recipes

#make main program executable
sudo chmod +x "$INSTALL_FOLDER/python/main.py"
#make touch rotate executable
sudo chmod +x "$INSTALL_FOLDER/touch_rotate.sh"

#add gui to x-servers startup if not yet so
X_AUTOSTART_PATH="$HOME/.config/lxsession/LXDE-pi/"
X_AUTOSTART_FILE="$X_AUTOSTART_PATH/autostart"
#create path if not exist
mkdir -p $X_AUTOSTART_PATH
#clear autostart file
> $X_AUTOSTART_FILE
#add correct links to the autostart file
echo "@lxpanel --profile LXDE-pi" >> $X_AUTOSTART_FILE
echo "@pcmanfm --desktop --profile LXDE-pi" >> $X_AUTOSTART_FILE
echo "@xscreensaver -no-splash" >> $X_AUTOSTART_FILE
echo "point-rpi" >> $X_AUTOSTART_FILE
echo "@$INSTALL_FOLDER/touch_rotate.sh" >> $X_AUTOSTART_FILE
echo "@$INSTALL_FOLDER/python/main.py" >> $X_AUTOSTART_FILE

#enable bluetooth
systemctl start hciuart

#rotate the display, only on pi 3
RASPBERRY_PI_VERSION=$(cat /proc/cpuinfo | grep 'Model' | awk '{print $5}')
echo "Raspberry Pi Version is $RASPBERRY_PI_VERSION"
if [ $RASPBERRY_PI_VERSION = "3" ]; then
	if ! grep -q 'display_rotate' "/boot/config.txt"; then
		echo 'display_rotate=3' >> "/boot/config.txt"
		echo "Display rotate set"
	else
		echo "Display rotate was allready set"
	fi
else
	echo "Cannot set display rotate automatically, please set it in raspberry pi 4 settings manually"
fi
sudo apt-get install bluetooth bluez libbluetooth-dev -y
sudo apt-get install python3-pyqt5 -y
# better use "pip3 install pyqt5 --config-settings --confirm-license= --verbose"??
pip3 install -r "$INSTALL_FOLDER/python/requirements.txt"
# to check startup logs use:
# nano ~/.cache/lxsession/LXDE-pi/run.log

#create desktop shortcut and make it executable
DESKTOP_SHORTCUT=~/Desktop/barbot.desktop
#clear desktop shurtcut  
> $DESKTOP_SHORTCUT
echo "[Desktop Entry]" >> $DESKTOP_SHORTCUT
echo "Name=BarBot" >> $DESKTOP_SHORTCUT
echo "Comment=Starte BarBot" >> $DESKTOP_SHORTCUT
echo "Exec=$INSTALL_FOLDER/python/main.py" >> $DESKTOP_SHORTCUT
echo "Type=Application" >> $DESKTOP_SHORTCUT
echo "Encoding=UTF-8" >> $DESKTOP_SHORTCUT
echo "Terminal=false" >> $DESKTOP_SHORTCUT
echo "" >> $DESKTOP_SHORTCUT
sudo chmod +x "$DESKTOP_SHORTCUT"