#define PIXEL_COUNT                         60
#define DRAFT_PORTS_COUNT                   12

#define PUMP_POWER_PWM                      700
#define PLATFORM_MOTOR_HOMING_SPEED         10000

#define PUMP_DISTANCE                       50
#define FIRST_PUMP_POSITION                 50
#define STIRRING_POSITION                   (FIRST_PUMP_POSITION + 11 * PUMP_DISTANCE + 75)
#define PLATFORM_MOTOR_MAXPOS_MM            1200

#define PLATFORM_MOTOR_MICROSTEPS           2
#define PLATFORM_MOTOR_FULLSTEPS_PER_MM     5.01 * 29 / 11.0 // gear ratio

// PINS //
#define PIN_NEOPIXEL                        (12)

#define PIN_PLATFORM_MOTOR_HOME             (25)
#define PIN_PLATFORM_MOTOR_DIR              (26)
#define PIN_PLATFORM_MOTOR_STEP             (27)

#define PIN_PUMP_SERIAL_DATA                (32)
#define PIN_PUMP_NOT_ENABLED                (33)
#define PIN_PUMP_SERIAL_RCLK                (34)
#define PIN_PUMP_SERIAL_SCLK                (35)
// PINS END //

#define PUMP_OFFSET                         -62421.115
#define PUMP_CALIBRATION                    -0.000929969633927
#define GLASS_WEIGHT_MIN                    300
#define GLASS_WEIGHT_MAX                    500
#define TOTAL_WEIGHT_MAX                    800

#define LEDC_CHANNEL_PUMP                   0