@ECHO OFF
ECHO.
ECHO.
ECHO B - Balance
ECHO C - Crusher
ECHO M - Mainboard
ECHO S - Straw
ECHO X - Mixer
ECHO.

SET /P M=Buchstaben eingeben und ENTER druecken:
IF %M%==B SET folder=balance
IF %M%==C SET folder=crusher
IF %M%==S SET folder=straw
IF %M%==X SET folder=mixer

ECHO %folder% wurde gewaehlt
ECHO.
ECHO.
ECHO.
ECHO.
ECHO.

SET batch_path=%~dp0
SET dude_path="%batch_path%\tool-avrdude\avrdude.exe"
SET hex_path=%batch_path%\%folder%\.pio\build\atmega_usbasp\firmware.hex

"%dude_path%" -c usbasp -p m328p -U hfuse:w:0xDE:m -U lfuse:w:0xFF:m -U efuse:w:0xFD:m -U flash:w:%hex_path%:a

PAUSE