from PyQt5 import QtWidgets
from barbot.logic import RecipeCollection, BarBot
from ..base import View

class SystemBusyView(View):
    """View to access system (eg. restart) when the mainboard is busy"""

    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes, is_idle_view=False)

        self.setLayout(QtWidgets.QVBoxLayout())
        from ...common import qt_icon_from_file_name, set_no_spacing
        set_no_spacing(self.layout())

        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

        self._content = QtWidgets.QWidget()
        self.layout().addWidget(self._content)

        # add actual content
        View.set_system_view(self._content, self.barbot_)
