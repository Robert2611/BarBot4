#define PIXEL_COUNT                         60
#define DRAFT_PORTS_COUNT                   12

#define PUMP_POWER_PWM                      900
#define PLATFORM_MOTOR_HOMING_SPEED         10000

#define HOME_DISTANCE                       65
#define PUMP_DISTANCE                       50
#define FIRST_PUMP_POSITION                 75
#define STIRRING_POSITION                   (FIRST_PUMP_POSITION + 11 * PUMP_DISTANCE + 75)
#define PLATFORM_MOTOR_MAXPOS_MM            900

#define PLATFORM_MOTOR_MICROSTEPS           4
#define PLATFORM_MOTOR_FULLSTEPS_PER_MM     200.0 / ( 20.0 * 2.0 )

// PINS //
#define PIN_NEOPIXEL                        5

#define PIN_PLATFORM_MOTOR_HOME             19
#define PIN_PLATFORM_MOTOR_DIR              14
#define PIN_PLATFORM_MOTOR_STEP             13
#define PIN_PLATFORM_MOTOR_EN               27

#define PIN_PUMP_SERIAL_DATA                26
#define PIN_PUMP_NOT_ENABLED                25
#define PIN_PUMP_SERIAL_RCLK                32
#define PIN_PUMP_SERIAL_SCLK                33
// PINS END //

#define BALANCE_OFFSET                      -92690
#define BALANCE_CALIBRATION                 -1075
#define GLASS_WEIGHT_MIN                    300
#define TOTAL_WEIGHT_MAX                    800

#define LEDC_CHANNEL_PUMP                   0

//timeout if weight did not increase by a certain amount in the specified time
#define DRAFT_TIMOUT_MILLIS                 2000
#define DRAFT_TIMOUT_WEIGHT                 20