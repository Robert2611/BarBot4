#include "Protocol.h"

Protocol::Protocol(Stream *str)
{
    stream = str;
    // init the msg ptr
    msg_ptr = msg;
}

void Protocol::update()
{
    if (running_command != 0)
    {
        if (running_command->done_condition())
        {
            sendDone(running_command->name);
            running_command = 0;
        }
    }
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

void Protocol::onCommand(char *command, int param_c, char **param_v)
{
    Command_t *cmd = first_command;
    while (cmd != 0)
    {
        if (!strcmp(command, cmd->name))
        {
            bool success = cmd->command_start(param_c, param_v);
            if (success)
            {
                sendACK(command);
                //start check for done if it is a long running command
                if (cmd->done_condition != 0)
                {
                    running_command = cmd;
                }
                return;
            }
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

void Protocol::addCommand(const char *_name, CommandStart_t _command_start)
{
    Command_t *cmd = new Command_t();
    cmd->name = _name;
    cmd->command_start = _command_start;
    addCommand(cmd);
}

void Protocol::addCommand(const char *_name, CommandStart_t _command_start, CommandDoneCondition_t _done_condition)
{
    Command_t *cmd = new Command_t();
    cmd->name = _name;
    cmd->command_start = _command_start;
    cmd->done_condition = _done_condition;
    addCommand(cmd);
}

void Protocol::sendNAK(char *command)
{
    stream->print("NAK ");
    stream->println(command);
}

void Protocol::sendACK(char *command)
{
    stream->print("ACK ");
    stream->println(command);
}

void Protocol::sendDone(const char *command)
{
    stream->print("DONE ");
    stream->println(command);
}

void Protocol::sendLink()
{
    stream->println("LINK");
}