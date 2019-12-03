#!/bin/sh
#get absolute path of this script
SCRIPT=`realpath $0`
#remove the filename
SETUP_FOLDER=`dirname $SCRIPT`
PYTHON_FOLDER="$SETUP_FOLDER/../server"

#make main program executable
sudo chmod +x "$PYTHON_FOLDER/main.py"

#make touch rotate executable
sudo chmod +x "$SETUP_FOLDER/touch_rotate.sh"

#add gui to x-servers startup if not yet so
X_AUTOSTART_PATH="$HOME/.config/lxsession/LXDE-pi/"
#create path if not exist
[ -d "$X_AUTOSTART_PATH" ]||mkdir --parent "$X_AUTOSTART_PATH"
#copy autostart file
cp $SETUP_FOLDER/autostart $X_AUTOSTART_PATH
#add correct links to the autostart file
echo "@lxpanel --profile LXDE-pi" >> $X_AUTOSTART_PATH/autostart
echo "@pcmanfm --desktop --profile LXDE-pi" >> $X_AUTOSTART_PATH/autostart
echo "@xscreensaver -no-splash" >> $X_AUTOSTART_PATH/autostart
echo "point-rpi" >> $X_AUTOSTART_PATH/autostart
echo "@$SETUP_FOLDER/touch_rotate.sh" >> $X_AUTOSTART_PATH/autostart
echo "@$SETUP_FOLDER/../server/main.py" >> $X_AUTOSTART_PATH/autostart

#enable bluetooth
systemctl start hciuart
#sudo nano /etc/systemd/system/dbus-org.bluez.service

#rotate the display
if ! grep -q 'display_rotate' "/boot/config.txt"; then
	echo 'display_rotate=3' >> "/boot/config.txt"
fi

sudo apt-get install python3-pyqt5 -y
pip3 install qdarkstyle