#include "Protocol.h"

Protocol::Protocol(Stream * str){
    stream = str;
    // init the msg ptr
    msg_ptr = msg;
}

void Protocol::update(){
    while (stream->available())
    {
        char c = stream->read();
        switch (c)
        {
        case '.':
        case '\r':
            // terminate the msg and reset the msg ptr. then send
            // it to the handler for processing.
            *msg_ptr = '\0';
            process();
            msg_ptr = msg;
            break;

        case '\n':
            // ignore newline characters. they usually come in pairs
            // with the \r characters we use for newline detection.
            break;

        case '\b':
            // backspace
            if (msg_ptr > msg)
            {
                msg_ptr--;
            }
            break;

        default:
            // normal character entered. add it to the buffer
            *msg_ptr++ = c;
            break;
        }
    }
}

void Protocol::process()
{
    char *input = (char*) msg;
    uint8_t param_c = 0;
    char *param_v[30];
    char *command;

    //fflush(stdout);
    
    command = strtok(input, " ");
    if( command == NULL )
        return;
    bool stop = false;
    do
    {
        param_v[param_c] = strtok(NULL, " ");
        if( param_v[param_c] != NULL ){
            param_c++;
        }else{
            stop = true;
        }
    } while ((param_c < 30) && !stop);

    onCommand(command, param_c, param_v);
}

void Protocol::onCommand(char * command, int param_c, char ** param_v){
    if (!strcmp(command, "Test"))
    {
        sendACK(command);
        return;
    }
    else if (!strcmp(command, "Wait"))
    {
        if(param_c == 1){
            int t = atoi(param_v[0]);
            if( t > 0 && t <= 5000 ){
                sendACK(command);
                delay(t);
                sendDone(command);
                return;
            }
        }
    }
    //no acceptable path was taken i.e. no return was triggered 
    sendNAK(command);
}

void Protocol::sendNAK(char* command){
    stream->print("NAK ");
    stream->println(command);
}

void Protocol::sendACK(char* command){
    stream->print("ACK ");
    stream->println(command);
}

void Protocol::sendDone(char* command){
    stream->print("DONE ");
    stream->println(command);
}