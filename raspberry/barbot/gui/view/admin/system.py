from barbot.logic import RecipeCollection, BarBot
from .base import AdminView
from ..base import View

class System(AdminView):
    """Control the whole barbot system"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)

        self._add_title_to_fixed_content("System")
        self._add_back_button_to_fixed_content()
        View.set_system_view(self._content)
