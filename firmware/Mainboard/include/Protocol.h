#include "Arduino.h"

#define MAX_MSG_SIZE    60

typedef bool (*CommandStart_t)(int param_c, char** param_v);
typedef bool (*CommandDoneCondition_t)();
struct Command_t{
    const char* name;
    CommandStart_t command_start;
    CommandDoneCondition_t done_condition;
    Command_t* next;
};

class Protocol{
public:
    Protocol(Stream * str);
    void update();
    void addCommand(Command_t* command);
    void addCommand(const char* name, CommandStart_t command_start);
    void addCommand(const char* name, CommandStart_t command_start, CommandDoneCondition_t done_condition);
private:
    Stream * stream;
    uint8_t msg[MAX_MSG_SIZE];
    uint8_t *msg_ptr;
    Command_t* first_command;
    void process();
    void onCommand(char * command, int param_c, char ** param_v);
    void sendNAK(char * command);
    void sendACK(char * command);
    void sendDone(const char * command);
    void sendLink();
    Command_t* running_command;
};

