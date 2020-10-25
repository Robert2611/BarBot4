#!/bin/sh
#get absolute path of this script
SCRIPT=`realpath $0`
#remove the filename
SETUP_FOLDER=`dirname $SCRIPT`
PYTHON_FOLDER="$SETUP_FOLDER/python"

#make main program executable
sudo chmod +x "$PYTHON_FOLDER/main.py"
#make touch rotate executable
sudo chmod +x "$SETUP_FOLDER/touch_rotate.sh"

#add gui to x-servers startup if not yet so
X_AUTOSTART_PATH="$HOME/.config/lxsession/LXDE-pi/"
X_AUTOSTART_FILE="$X_AUTOSTART_PATH/autostart"
#create path if not exist
[ -d $X_AUTOSTART_PATH ]||mkdir --parent "$X_AUTOSTART_PATH"
#clear autostart file
> $X_AUTOSTART_FILE
#add correct links to the autostart file
echo "@lxpanel --profile LXDE-pi" >> $X_AUTOSTART_FILE
echo "@pcmanfm --desktop --profile LXDE-pi" >> $X_AUTOSTART_FILE
echo "@xscreensaver -no-splash" >> $X_AUTOSTART_FILE
echo "point-rpi" >> $X_AUTOSTART_FILE
echo "@$SETUP_FOLDER/touch_rotate.sh" >> $X_AUTOSTART_FILE
echo "@$PYTHON_FOLDER/main.py" >> $X_AUTOSTART_FILE

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
	echo "Cannot set display rotate"
fi
sudo apt-get install python3-pyqt5 -y
pip3 install -r "$PYTHON_FOLDER/requirements.txt"
#nano /home/pi/.cache/lxsession/LXDE-pi/run.log