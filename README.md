# BarBot4
Collects all the data needed to run a bar bot of version 4.X  
This includes:
* __HTTP server__: Written in Python controlling the communication to the database that contains the recipes and the connection to the mainboard.
* __GUI__: A html file styled with css powered by javascript
* __Mainboard firmware__: Firmware the ESP32 type board that controlls the x stepper motor, the pumps, the LEDs and that communicates to the other boards via I2C
* __Balance board firmware__: Firmware that controlls the ATMEGA8 on the balance board. It reads the balance, smooths the data and controls RGB LEDS on the board 
