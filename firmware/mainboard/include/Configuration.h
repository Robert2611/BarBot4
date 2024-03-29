#define LED_STRIPE_PIXELS 60
#define LED_STRIPE_LENGTH_MM 1000
#define DRAFT_PORTS_COUNT 12

#define PUMP_POWER_FREQUENCY 10000
#define PLATFORM_MOTOR_HOMING_SPEED 10000

//Distance of platform center to left corner when homed
#define HOME_DISTANCE 97
#define PUMP_DISTANCE 50
//subtract home distance, so you can set distances from the left corner
#define FIRST_PUMP_POSITION (165 - HOME_DISTANCE)
#define MIXING_POSITION (780 - HOME_DISTANCE)
#define CRUSHER_POSITION (900 - HOME_DISTANCE)
#define SUGAR_POSITION (0 - HOME_DISTANCE)
// the crusher is the last position on the reck
#define PLATFORM_MOTOR_MAXPOS_MM CRUSHER_POSITION

#define PLATFORM_MOTOR_MICROSTEPS 4
#define PLATFORM_MOTOR_FULLSTEPS_PER_MM 200.0 / (20.0 * 2.0)

// PINS //
#define PIN_NEOPIXEL 23

#define PIN_PLATFORM_MOTOR_HOME 18
#define PIN_PLATFORM_MOTOR_DIR 16  //RX2
#define PIN_PLATFORM_MOTOR_STEP 17 //TX2
#define PIN_PLATFORM_MOTOR_EN 4

#define PIN_PUMP_ENABLED 33

#define PIN_IO_RESET 32
#define PIN_IO_CS 15
#define PIN_BUTTON 19
#define PIN_CRUSHER_SENSE 33
#define PIN_SERVO 26
#define PIN_LED 27
// PINS END //

#define GLASS_WEIGHT_MIN 300
#define TOTAL_WEIGHT_MAX 800

#define LEDC_CHANNEL_PUMP 0

//timeout if weight did not increase by a certain amount in the specified time
#define DRAFT_TIMEOUT_MILLIS 3000
#define DRAFT_TIMEOUT_WEIGHT 20

#define ICE_TIMEOUT_MILLIS 5000
#define ICE_TIMEOUT_WEIGHT 10

#define SUGAR_TIMEOUT_MILLIS 3000
#define SUGAR_TIMEOUT_WEIGHT 5

#define CHILD_UPDATE_PERIOD 100