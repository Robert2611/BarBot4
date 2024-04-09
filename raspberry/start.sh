#!/bin/sh
# set display, only necessary if called from remote
[ -z $DISPLAY ] && export DISPLAY=:0
# get the folder of the currently running file 
SCRIPT_FOLDER=$(readlink -f "$0"|xargs dirname)
python3 $SCRIPT_FOLDER/python/main.py