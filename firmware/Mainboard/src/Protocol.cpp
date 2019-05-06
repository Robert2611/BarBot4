#include "Protocol.h"

Protocol::Protocol(Stream *str)
{
    stream = str;
    // init the msg ptr
    msg_ptr = msg;
}

void Protocol::update()
{
    //a long running command is being executed 
    if (running_command != 0)
    {        
        int error_code;
        long parameter;
        //check if command is done or has an error. If so, notify master and stop the command
        switch(running_command->command_update(&error_code,&parameter))
        {
            case CommandStatus_t::Done:
                sendDone(running_command->name);
                running_command = 0;
                break;
            case CommandStatus_t::Error:
                sendError(running_command->name, error_code, parameter);
                running_command = 0;
                break;
            case CommandStatus_t::Running:
                //nothing to do here
                break;
        }
    }
    //handle incomming characters
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
    char *input = (char *)msg;
    uint8_t param_c = 0;
    char *param_v[30];
    char *command;

    //fflush(stdout);

    command = strtok(input, " ");
    if (command == NULL)
        return;
    bool stop = false;
    do
    {
        param_v[param_c] = strtok(NULL, " ");
        if (param_v[param_c] != NULL)
        {
            param_c++;
        }
        else
        {
            stop = true;
        }
    } while ((param_c < 30) && !stop);

    onCommand(command, param_c, param_v);
}

void Protocol::onCommand(const char *command, int param_c, char **param_v)
{
    Command_t *cmd = first_command;
    //find command with the right name
    while (cmd != 0)
    {
        if (!strcmp(command, cmd->name))
        {
            long result;
            //start command using the passed function
            bool success = cmd->command_start(param_c, param_v, &result);
            //start command ran sucessfully
            if (success)
            {
                switch(cmd->type)
                {
                    case CommandType_t::Get:
                        sendResult(cmd->name, result);
                        return;
                    case CommandType_t::Set:
                        sendACK(command);
                        return;
                    case CommandType_t::Do:
                        sendACK(command);
                        //tell main loop that it has to look for stop condition
                        if (cmd->command_update != 0)
                            running_command = cmd;
                        return;
                    default:
                        return;
                }
            }
            //some problem in the command start 
            else
            {
                sendNAK(command);
                return;
            }
        }
        cmd = cmd->next;
    }
    //not a valid command
    sendNAK(command);
}

void Protocol::addCommand(Command_t *command)
{
    if (first_command == 0)
    {
        first_command = command;
    }
    else
    {
        Command_t *cmd = first_command;
        while (cmd->next != 0)
        {
            cmd = cmd->next;
        }
        cmd->next = command;
    }
}

void Protocol::addSetCommand(const char *_name, CommandStart_t _command_start)
{
    Command_t *cmd = new Command_t();
    cmd->name = _name;
    cmd->command_start = _command_start;
    cmd->type = CommandType_t::Set;
    addCommand(cmd);
}

void Protocol::addGetCommand(const char *_name, CommandStart_t _command_start)
{
    Command_t *cmd = new Command_t();
    cmd->name = _name;
    cmd->command_start = _command_start;
    cmd->type = CommandType_t::Get;
    addCommand(cmd);
}

void Protocol::addDoCommand(const char *_name, CommandStart_t _command_start, CommandUpdate_t _command_update)
{
    Command_t *cmd = new Command_t();
    cmd->name = _name;
    cmd->command_start = _command_start;
    cmd->command_update = _command_update;
    cmd->type = CommandType_t::Do;
    addCommand(cmd);
}



//Communication

void Protocol::sendNAK(const char *command)
{
    stream->print("NAK ");
    stream->println(command);
}

void Protocol::sendACK(const char *command)
{
    stream->print("ACK ");
    stream->println(command);
}

void Protocol::sendDone(const char *command)
{
    stream->print("DONE ");
    stream->println(command);
}

void Protocol::sendResult(const char * command, long value){
    stream->print("ACK ");
    stream->print(command);
    stream->print(" ");
    stream->println(value);
}

void Protocol::sendError(const char *command, int error_code, long parameter = 0)
{
    stream->print("ERROR ");
    stream->print(command);
    stream->print(" ");
    stream->print(error_code);
    stream->print(" ");
    stream->println(parameter);
}

void Protocol::sendLink()
{
    stream->println("LINK");
}

