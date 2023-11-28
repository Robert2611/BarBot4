#!/bin/bash

INSTALL_FOLDER=~/barbot
DATA_FOLDER=~/.barbot
# get the folder of the currently running file 
SCRIPT_FOLDER=$(readlink -f "$0"|xargs dirname)


# if we are not in the install folder...
if [ ! $SCRIPT_FOLDER -ef $INSTALL_FOLDER ]; then
	echo "Not in install dir (~/barbot), copying files..."
	mkdir -p $INSTALL_FOLDER
	# ...copy the the content of this folder to the install folder
	cp -a $SCRIPT_FOLDER/. $INSTALL_FOLDER/
else
	echo "We are in the install dir (~/barbot)."
fi

#create data folders if not exist
mkdir -p $DATA_FOLDER/log
mkdir -p $DATA_FOLDER/recipes
#copy recipes
rsync --ignore-existing $INSTALL_FOLDER/data/recipes/* $DATA_FOLDER/recipes

#make main program executable
sudo chmod +x "$INSTALL_FOLDER/python/main.py"

sudo apt-get -y -q install bluetooth bluez libbluetooth-dev
sudo apt-get -y -q install python3-pyqt5
sudo apt-get -y -q install python3-pip
# better use "pip3 install pyqt5 --config-settings --confirm-license= --verbose"??
pip3 install -r "$INSTALL_FOLDER/python/requirements.txt"
# to check startup logs use:
# nano ~/.cache/lxsession/LXDE-pi/run.log

#enable bluetooth
sudo systemctl start hciuart

# Check if we are on a raspbian system
if [[ $(cat /etc/os-release|grep -i "pretty") = *"aspbian"* ]]; then
	#make touch rotate executable
	sudo chmod +x "$INSTALL_FOLDER/touch_rotate.sh"

	#add gui to x-servers startup if not yet so
	X_AUTOSTART_PATH="$HOME/.config/lxsession/LXDE-pi/"
	#create path if not exist
	mkdir -p $X_AUTOSTART_PATH
	X_AUTOSTART_FILE="$X_AUTOSTART_PATH/autostart"
	# write links to the autostart file
cat > $X_AUTOSTART_FILE << EOL
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash
point-rpi
@$INSTALL_FOLDER/touch_rotate.sh
@$INSTALL_FOLDER/python/main.py
EOL

	#create desktop shortcut and make it executable
cat > ~/Desktop/barbot.desktop << EOL
[Desktop Entry]
Name=BarBot
Comment=Starte BarBot
Exec=$INSTALL_FOLDER/python/main.py
Type=Application
Encoding=UTF-8
Terminal=false
EOL
	# make it executable 
	sudo chmod +x "$DESKTOP_SHORTCUT"
else
	echo "Not on a raspbian system."
fi