@ECHO OFF
SET batch_path=%~dp0

:start
ECHO -------------
ECHO B - Balance
ECHO C - Crusher
ECHO M - Mainboard
ECHO S - Straw
ECHO X - Mixer
ECHO -------------

SET /P M=Buchstaben eingeben und ENTER druecken:
IF %M%==M SET folder=mainboard
IF %M%==B SET folder=balance
IF %M%==C SET folder=crusher
IF %M%==S SET folder=straw
IF %M%==X SET folder=mixer

ECHO %folder% wurde gewaehlt
ECHO.

IF %M%==M GOTO mainboard

:atmega
SET dude_path="%batch_path%\tool-avrdude\avrdude.exe"
SET hex_path=%batch_path%\%folder%.hex
%dude_path% -c usbasp -p m328p -U hfuse:w:0xDE:m -U lfuse:w:0xFF:m -U efuse:w:0xFD:m -U flash:w:%hex_path%:a
GOTO start

:mainboard
SET /P port=Bitte den COM-Port angeben, an dem der ESP32 angeschlossen ist:
SET esptool_path="%batch_path%esptool\esptool.exe"
SET bin_path="%batch_path%mainboard.bin"
%esptool_path% --port "%port%" --chip esp32 write_flash -fs 1MB -fm dout 0x0 "%bin_path%"
GOTO start

PAUSE
