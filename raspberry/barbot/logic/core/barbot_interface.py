from barbot.logic.core.barbot import MixingOptions
from barbot.logic.core.constants import UserInputType, UserMessageType
from barbot.logic.recipes.party import PartyCollection
from barbot.logic.recipes.recipe import RecipeItem


class BarBotInterface:
    """Interface for BarBot core logic to interact with other components"""
    @property
    def was_aborted(self) -> bool:
        """Whether the mixing was aborted"""

    def set_message(self, message: UserMessageType):
        """Set the current user message"""

    @property
    def user_input(self) -> UserInputType:
        """Get the current user input"""

    def reset_user_input(self):
        """Reset the user input to UserInput.UNDEFINED"""

    @property
    def parties(self) -> PartyCollection:
        """Get the parties collection"""

    @property
    def current_mixing_options(self) -> MixingOptions:
        """Get the mixing options for what is being mixed"""

    @property
    def current_recipe_item(self) -> RecipeItem:
        """Get the ricipe item that is being drafted"""

    def set_mixing_progress(self, progress : int):
        """Set the current mixing progress as index of total steps"""

    def mixing_progress(self) -> int:
        """Get the current mixing progress as index of total steps"""

    def has_glas(self) -> bool:
        """Check if there is a glas present"""
