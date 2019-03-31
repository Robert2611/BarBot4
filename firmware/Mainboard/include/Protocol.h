#include "Arduino.h"

#define MAX_MSG_SIZE    60

class Protocol{
public:
    Protocol(Stream * str);
    void update();

private:
    Stream * stream;
    uint8_t msg[MAX_MSG_SIZE];
    uint8_t *msg_ptr;
    void process();
    void onCommand(char * command, int param_c, char ** param_v);
    void sendNAK(char * command);
    void sendACK(char * command);
    void sendDone(char * command);
};