#!/bin/sh
sleep 3
# 6th coordinate offsets touch in y direction for better usage with touch display
xinput --set-prop 'raspberrypi-ts' 'Coordinate Transformation Matrix'  0 -1 1 1 0 -0.02 0 0 1
xrandr --output DSI-1 --rotate left