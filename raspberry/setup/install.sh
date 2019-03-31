#!/bin/sh

BIN_FOLDER=$(dirname "$0")
PYTHON_FOLDER="$BIN_FOLDER/../python"

#copy server deamon
sudo cp $BIN_FOLDER/bar_bot_server.sh /etc/init.d/
#make it executable
sudo chmod +x /etc/init.d/bar_bot_server.sh
#make webserver and main program executable
sudo chmod +x $PYTHON_FOLDER/webserver.py
sudo chmod +x $PYTHON_FOLDER/main.py

#add bar_bot_server to the autostart deamons
sudo update-rc.d bar_bot_server.sh defaults

#add gui to x-servers startup if not yet so
X_AUTOSTART_PATH="$HOME_FOLDER/.config/lxsession/LXDE-pi/"
#create path if not exist
[ -d "$X_AUTOSTART_PATH" ]||mkdir --parent "$X_AUTOSTART_PATH"
#copy autostart file
cp $BIN_FOLDER/autostart $X_AUTOSTART_PATH
#make rotation script executable
sudo chmod +x $BIN_FOLDER/touch_rotate.sh

#enable bluetooth
systemctl start hciuart
#sudo nano /etc/systemd/system/dbus-org.bluez.service

#rotate the display
if ! grep -q 'display_rotate' "/boot/config.txt"; then
	echo 'display_rotate=3' >> "/boot/config.txt"
fi

#hide cursor
sudo apt-get install unclutter

#remove startup messages
cp $BIN_FOLDER/cmdline.txt /boot/cmdline.txt


#to connect to a device with password:
#	bluetoothctl
#	agent on
#	pair 20:16:04:14:60:60
#it should now prompt for the password
