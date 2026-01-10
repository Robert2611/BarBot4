import logging
from typing import Callable
from .idle_task import IdleTask
from .common import MixingOptions, UserInputType, UserMessageType
from ..recipes.party import PartyCollection
from ..recipes.recipe import Recipe, RecipeItem


class BarBotContext:
    """The main class containing the statemachine of the barbot"""

    def __init__(self):
        self.should_stop_statemachine = False
        self.should_abort_mixing = False
        self.user_input: UserInputType = UserInputType.UNDEFINED
        self.weight_timeout = 1
        self.weight = None
        self.pumps_to_clean = []
        self.connected_boards = []
        self._message: UserMessageType = None
        self._progress = 0
        self.idle_tasks: list[IdleTask] = []
        self.current_mixing_options: MixingOptions = None
        self.current_recipe_item: RecipeItem = None
        self.parties = PartyCollection()
        self.state_changed: bool = False
        self.should_reconnect: bool = True

        # callbacks
        self.on_mixing_finished: Callable[[Recipe], None] = lambda current_recipe: None
        self.on_mixing_progress_changed: Callable[[int], None] = lambda progress: None
        self.on_message_changed: Callable[[UserMessageType], None] = (
            lambda message: None
        )

    def get_next_idle_task(self) -> IdleTask:
        """Get the next idle task to be executed, or None if there is none"""
        if self.idle_tasks:
            return self.idle_tasks.pop(0)
        return None

    def reset_user_input(self):
        """Reset the user input to UserInput.UNDEFINED"""
        self.user_input = UserInputType.UNDEFINED

    @property
    def mixing_progress(self) -> int:
        """Get the current mixing progress as index of total steps"""
        return self._progress

    @mixing_progress.setter
    def mixing_progress(self, progress: int):
        """Set the current mixing progress as index of total steps"""
        self._progress = progress
        if self.on_mixing_progress_changed is not None:
            self.on_mixing_progress_changed(progress)

    def remove_message(self):
        """Remove the current user message"""
        self.message = None

    @property
    def message(self):
        """Message to the user, None if there isn't any"""
        return self._message

    @message.setter
    def message(self, message: UserMessageType):
        """Set a message to the user, or None to remove it"""
        if message is None or message == UserMessageType.NONE:
            message = UserMessageType.NONE
            logging.debug("Remove user message")
        else:
            logging.debug("Show user message: %s", message)
        self._message = message
        if self.on_message_changed is not None:
            self.on_message_changed(message)
