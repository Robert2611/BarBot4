#!/bin/sh
sleep 3
xinput --set-prop 'raspberrypi-ts' 'Coordinate Transformation Matrix'  0 -1 1 1 0 0 0 0 1
xrandr --output DSI-1 --rotate left