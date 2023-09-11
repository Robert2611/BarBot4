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
SET esptool_path="%batch_path%esptool\esptool.exe"
SET bin_path="%batch_path%mainboard.bin"
%esptool_path% --chip esp32 --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x10000 "%bin_path%"
GOTO start

PAUSE
