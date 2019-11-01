#define PIXEL_COUNT                         60
#define DRAFT_PORTS_COUNT                   12

#define PUMP_POWER_PWM                      900
#define PLATFORM_MOTOR_HOMING_SPEED         10000

#define HOME_DISTANCE                       55
#define PUMP_DISTANCE                       50
#define FIRST_PUMP_POSITION                 65
#define STIRRING_POSITION                   855//(FIRST_PUMP_POSITION + 11 * PUMP_DISTANCE + 75)
#define PLATFORM_MOTOR_MAXPOS_MM            900

#define PLATFORM_MOTOR_MICROSTEPS           4
#define PLATFORM_MOTOR_FULLSTEPS_PER_MM     200.0 / ( 20.0 * 2.0 )

// PINS //
#define PIN_NEOPIXEL                        23

#define PIN_PLATFORM_MOTOR_HOME             18
#define PIN_PLATFORM_MOTOR_DIR              16 //RX2
#define PIN_PLATFORM_MOTOR_STEP             17 //TX2
#define PIN_PLATFORM_MOTOR_EN               4

#define PIN_IO_RESET                        32
#define PIN_IO_CS                           15
#define PIN_BUTTON                          19
#define PIN_CRUSHER_SENSE                   25
#define PIN_SERVO                           26
#define PIN_LED                             27
// PINS END //

#define BALANCE_OFFSET                      -92690
#define BALANCE_CALIBRATION                 -1075
#define GLASS_WEIGHT_MIN                    300
#define TOTAL_WEIGHT_MAX                    800

#define LEDC_CHANNEL_PUMP                   0

//timeout if weight did not increase by a certain amount in the specified time
#define DRAFT_TIMOUT_MILLIS                 2000
#define DRAFT_TIMOUT_WEIGHT                 20