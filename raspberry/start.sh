#!/bin/sh
# set display, only necessary if called from remote
[ -z $DISPLAY ] && export DISPLAY=:0
# get the folder of the currently running file 
SCRIPT_FOLDER=$(dirname "$0")
# start the barbot and forward all arguments 
python3 $SCRIPT_FOLDER/python/main.py $@