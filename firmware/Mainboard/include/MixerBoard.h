#ifndef MIXER_BOARD_H
#define MIXER_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

#define MIXER_SEND_RETRIES 15

class MixerBoard
{
public:
  MixerBoard();
  bool StartMoveTop();
  bool StartMoveBottom();
  bool IsAtTop();
  bool IsAtBottom();
  bool IsMixing();
  void StartMixing();
  void StopMixing();
  byte GetTargetPosition();

private:
  bool StartMove(byte pos);
  byte GetPosition();
  byte _targetPosition;
  bool _isMixing;
};
#endif