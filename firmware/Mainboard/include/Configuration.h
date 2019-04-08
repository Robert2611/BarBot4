

#define PIXEL_COUNT 60

#define PUMP_POWER_PWM           255
#define HOME_SPEED               10000
#define FULLSTEPS_PER_MM         5.01 * 29 / 11.0 // gear ratio
#define PUMP_DISTANCE            50
#define FIRST_PUMP_POSITION      50
#define STIRRING_POSITION        (FIRST_PUMP_POSITION + 11 * PUMP_DISTANCE + 75)
#define MAX_X_POS_MM             1200

#define MAX_ENTRIES_PER_RECIPE   16
#define PORTS_COUNT              12

#define MICROSTEPS               2

// PINS //

#define PIN_NEOPIXEL        (12)

#define X_MOTOR_HOME        (25)
#define X_MOTOR_DIR         (26)
#define X_MOTOR_STEP        (27)

#define PUMP_SERIAL_DATA    (32)
#define PUMP_NOT_ENABLED    (33)
#define PUMP_SERIAL_RCLK    (34)
#define PUMP_SERIAL_SCLK    (35)

// PINS END //