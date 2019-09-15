#!/bin/sh

BIN_FOLDER=$(dirname "$0")
PYTHON_FOLDER="$BIN_FOLDER/../server"

#make main program executable
sudo chmod +x $PYTHON_FOLDER/main.py

#add gui to x-servers startup if not yet so
X_AUTOSTART_PATH="$HOME/.config/lxsession/LXDE-pi/"
#create path if not exist
[ -d "$X_AUTOSTART_PATH" ]||mkdir --parent "$X_AUTOSTART_PATH"
#copy autostart file
cp $BIN_FOLDER/autostart $X_AUTOSTART_PATH

#enable bluetooth
systemctl start hciuart
#sudo nano /etc/systemd/system/dbus-org.bluez.service

#rotate the display
if ! grep -q 'display_rotate' "/boot/config.txt"; then
	echo 'display_rotate=3' >> "/boot/config.txt"
fi

sudo apt-get install python3-pyqt5 -y
pip3 install qdarkstyle


#remove startup messages
cp $BIN_FOLDER/cmdline.txt /boot/cmdline.txt


#to connect to a device with password:
#	bluetoothctl
#	agent on
#	pair 20:16:04:14:60:60
#it should now prompt for the password