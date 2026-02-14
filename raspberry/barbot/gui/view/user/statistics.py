from PyQt5 import QtWidgets, QtCore
from barbot.logic.recipes import PartyStatistics, Party
from barbot.logic import RecipeCollection, BarBot
from ...controls import BarChartRow, BarChart, set_no_spacing
from ...controls.list_selector import SelectorButton
from .base import UserView

class Statistics(UserView):
    """View that shows statistics of a party"""
    def __init__(self, barbot: BarBot, recipes: RecipeCollection):
        super().__init__(barbot, recipes)
        self._statistics_widget = None
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        self._add_title_to_fixed_content("Statistik")
        self._add_date_selector()
        self._add_dummy_widget_to_content()
        self._add_statisctics_container()

        # initialize with date of last party
        self._update_view(self.barbot_.parties.current_party)

    def _add_date_selector(self):
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        self._content.layout().addWidget(row)
        # - label
        label = QtWidgets.QLabel("Datum")
        row.layout().addWidget(label)
        # - dropdown
        
        def get_items():
            return [(party.start.strftime("%Y-%m-%d"), party) for party in self.barbot_.parties]

        initial_party = self.barbot_.parties.current_party
        initial_text = initial_party.start.strftime("%Y-%m-%d") if initial_party else "-"
        
        dates_widget = SelectorButton(initial_text, get_items, self.styles if hasattr(self, "styles") else None, initial_party)
        dates_widget.selection_changed.connect(self._update_view)
        row.layout().addWidget(dates_widget)

    def _add_statisctics_container(self):
        self._statistics_container = QtWidgets.QWidget()
        self._statistics_container.setLayout(QtWidgets.QGridLayout())
        set_no_spacing(self._statistics_container.layout())
        self._content.layout().addWidget(self._statistics_container)

    def _update_view(self, party: Party):
        self._remove_old_statistics_widget()
        if party is None or len(party.orders) == 0:
            return
        statistics = party.get_statistics()
        self._statistics_widget = self._create_statistics_widget(statistics)
        self._statistics_container.layout().addWidget(self._statistics_widget)

    def _create_statistics_widget(self, statistics : PartyStatistics):
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QVBoxLayout())

        # total ordered cocktails
        label = QtWidgets.QLabel(f"Bestellte Cocktails ({statistics.total_cocktails})")
        container.layout().addWidget(label)
        # ordered cocktails by name
        data = [
            BarChartRow(name, count)
            for name, count
            in statistics.cocktail_count.items()
        ]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # total liters
        total_amount = sum(statistics.ingredients_amount.values()) / 100.0
        label = QtWidgets.QLabel(f"Verbrauchte Zutaten ({total_amount:.2g} l)")
        container.layout().addWidget(label)
        # ingrediends
        data = [
            BarChartRow(ingr, amount / 100.0)
            for ingr, amount
            in statistics.ingredients_amount.items()
        ]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # label
        label = QtWidgets.QLabel("Bestellungen")
        container.layout().addWidget(label)
        # cocktails vs. time chart
        data = [
            BarChartRow(f"{dt.hour} bis {dt.hour+1} Uhr", count)
            for dt, count
            in statistics.cocktails_by_time.items()
        ]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        return container

    def _remove_old_statistics_widget(self):
        if self._statistics_widget is not None:
            # setting the parent of the previos content to None will destroy it
            self._statistics_widget.setParent(None)
            self._statistics_widget = None
