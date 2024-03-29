#include "Arduino.h"

#define PROTOCOL_MAX_MSG_SIZE 60
#define PROTOCOL_LINK_TIME 300
#define PROTOCOL_CMD_STR_ABORT "ABORT"
#define PROTOCOL_PARAMETER_BUFFER_SIZE 32

enum class CommandType_t
{
    Set,
    Do,
    Get,
};

enum class CommandStatus_t
{
    Running,
    Done,
    Error
};

typedef bool (*CommandStart_t)(int param_c, char **param_v, long *result);
typedef CommandStatus_t (*CommandUpdate_t)(int *error_code, long *parameter);
struct Command_t
{
    const char *name;
    CommandStart_t command_start;
    CommandUpdate_t command_update;
    CommandType_t type;
    Command_t *next;
};

class Protocol
{
public:
    Protocol(Stream *str);
    void update();
    void addCommand(Command_t *command);
    void addSetCommand(const char *name, CommandStart_t command_start);
    void addGetCommand(const char *name, CommandStart_t command_start);
    void addDoCommand(const char *name, CommandStart_t command_start, CommandUpdate_t command_update);
    bool acceptsCommands();
    void setAcceptsCommand(bool accept);
    bool abortRequested();

private:
    Stream *stream;
    uint8_t msg[PROTOCOL_MAX_MSG_SIZE];
    uint8_t *msg_ptr;
    Command_t *first_command;
    bool abort;
    void process();
    void sendNAK(const char *command);
    void sendACK(const char *command);
    void sendDone(const char *command);
    void sendResult(const char *command, long value);
    void sendError(const char *command, int error_code, long parameter);
    void sendLink();
    void onCommand(const char *command, int param_c, char **param_v);
    Command_t *running_command;
    unsigned long last_send_millis;
    bool accepts_commands = false;
};
