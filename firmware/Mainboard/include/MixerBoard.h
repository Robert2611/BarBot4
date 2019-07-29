#ifndef MIXER_BOARD_H
#define MIXER_BOARD_H
#include "Shared.h"
#include "WireProtocol.h"

class MixerBoard
{
public:
  MixerBoard();
  void StartMoveTop();
  void StartMoveBottom();
  bool IsAtTop();
  bool IsAtBottom();
  bool IsMixing();
  void StartMixing();
  void StopMixing();
  byte GetTargetPosition();

private:
  void StartMove(byte pos);
  byte GetPosition();
  byte _targetPosition;
  bool _isMixing;
};
#endif