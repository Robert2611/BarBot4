from enum import Enum, auto
from typing import Callable

from barbot.logic.communication.communication import CommunicationResult, Mainboard


class IdleTaskType(Enum):
    """Enumeration of the possible idle task types"""

    GET = auto()
    SET = auto()
    DO = auto()


class IdleTask:
    """Defines a task to be executed on barbot idle"""

    def __init__(
        self,
        task_type: IdleTaskType,
        callback: Callable[[CommunicationResult], None],
        command: str,
        *parameters: str
    ):
        self._task_type = task_type
        self._callback = callback
        self._parameters = parameters
        self._command = command

    def execute(self, mainboard: Mainboard):
        """Call this in idle of barbot"""
        result = {
            IdleTaskType.DO: mainboard.do,
            IdleTaskType.GET: mainboard.get,
            IdleTaskType.SET: mainboard.set,
        }.get(self._task_type)(self._command, *self._parameters)
        if self._callback is not None:
            self._callback(result)
