"""All views that are openly accessible"""
from enum import Enum, auto
from typing import Optional
from PyQt5 import QtWidgets, QtCore

from barbot import MixingOptions
from barbot.recipes import PartyStatistics, RecipeItem, Recipe, Party
from barbot.config import IngredientType, Stir as StirIngredient

from barbotgui.core import BarBotWindow, View, qt_icon_from_file_name
from barbotgui.controls import BarChartRow, GlasFilling, GlasIndicator, BarChart, set_no_spacing


class UserView(View):
    """Base class for all user views"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self.navigation_items = [
            ["Liste", ListRecipes],
            ["Neu", RecipeNewOrEdit],
            ["Nachschlag", SingleIngredient],
            ["Statistik", Statistics],
        ]
        box_layout = QtWidgets.QVBoxLayout()
        self.setLayout(box_layout)
        set_no_spacing(box_layout)

        self.__add_header()
        self.__add_navigation()

        content_wrapper = QtWidgets.QWidget()
        box_layout.addWidget(content_wrapper, 1)
        content_wrapper.setLayout(QtWidgets.QGridLayout())
        set_no_spacing(content_wrapper.layout())

        self.__add_fixed_content_to(content_wrapper)
        self.__add_scroller_and_content_to(content_wrapper)

    def __add_scroller_and_content_to(self, content_wrapper):
        scroller = QtWidgets.QScrollArea()
        scroller.setProperty("class", "ContentScroller")
        scroller.setWidgetResizable(True)
        # pylint: disable-next=no-member
        scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content_wrapper.layout().addWidget(scroller)

        QtWidgets.QScroller.grabGesture(
            scroller.viewport(),
            # pylint: disable-next=no-member
            QtWidgets.QScroller.ScrollerGestureType.LeftMouseButtonGesture
        )

        self._content = QtWidgets.QWidget()
        self._content.setProperty("class", "IdleContent")
        scroller.setWidget(self._content)

    def __add_fixed_content_to(self, content_wrapper):
        self._fixed_content = QtWidgets.QWidget()
        content_wrapper.layout().addWidget(self._fixed_content)

    def __add_header(self):
        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

    def __add_navigation(self):
        self.navigation = QtWidgets.QWidget()
        self.layout().addWidget(self.navigation)
        navigation_layout = QtWidgets.QHBoxLayout()
        self.navigation.setLayout(navigation_layout)

        for text, _class in self.navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(_, c=_class):
                return self.window.set_view(c(self.window))
            button.clicked.connect(btn_click)
            navigation_layout.addWidget(button, 1)

    def _add_title_to_fixed_content(self, title_name):
        title = QtWidgets.QLabel(title_name)
        title.setProperty("class", "Headline")
        # pylint: disable-next=no-member
        self._fixed_content.layout().setAlignment(title, QtCore.Qt.AlignmentFlag.AlignTop)
        self._fixed_content.layout().addWidget(title)

    def _add_dummy_widget_to_content(self):
        layout = self._content.layout()
        if layout is QtWidgets.QBoxLayout:
            # we can only make the widget stretch, if it is a QBoxLayout
            layout.addWidget(QtWidgets.QWidget(), 1)
        else:
            layout.addWidget(QtWidgets.QWidget())

class ListRecipes(UserView):
    """List of known recipes"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        self._add_filter_alcoholic()
        self._add_filter_available()
        self._add_recipe_list_container()
        self._add_dummy_widget_to_content()

        self._update_recipe_list()

    def _add_filter_alcoholic(self):
        self._cb_alcoholic = QtWidgets.QCheckBox("Alkoholisch")
        self._fixed_content.layout().addWidget(self._cb_alcoholic)
        self._cb_alcoholic.setChecked(self.window.recipe_filter.show_alcoholic)
        self._cb_alcoholic.toggled.connect(self._update_recipe_list)

    def _add_filter_available(self):
        self._cb_available = QtWidgets.QCheckBox("Nur verfügbare")
        self._fixed_content.layout().addWidget(self._cb_available)
        self._cb_available.setChecked(self.window.recipe_filter.only_available)
        self._cb_available.toggled.connect(self._update_recipe_list)

    def _add_recipe_list_container(self):
        self._recipe_list_container = QtWidgets.QWidget()
        self._recipe_list_container_layout = QtWidgets.QVBoxLayout()
        self._recipe_list_container.setLayout(self._recipe_list_container_layout)
        self._content.layout().addWidget(self._recipe_list_container)
        set_no_spacing(self._recipe_list_container_layout)

    def _update_recipe_list(self):
        recipe_filter = self.window.recipe_filter
        recipe_filter.only_available = self._cb_available.isChecked()
        recipe_filter.show_alcoholic = self._cb_alcoholic.isChecked()
        recipe_filter.show_non_acloholic = not self._cb_alcoholic.isChecked()
        recipes = self.window.recipes.get_filtered( \
            recipe_filter, self.barbot_.ports, self.barbot_.config)

        self._clear_recipe_list_container()
        for recipe in recipes:
            self._add_recipe_to_list_container(recipe)

        # dummy element
        self._recipe_list_container_layout.addWidget(QtWidgets.QWidget(), 1)

    def _clear_recipe_list_container(self):
        while self._recipe_list_container_layout.count():
            item = self._recipe_list_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # pylint: disable-next=no-member
                widget.setParent(None) # type: ignore

    def _add_recipe_to_list_container(self, recipe):
        # box to hold the recipe
        recipe_widget = QtWidgets.QWidget()
        recipe_widget.setLayout(QtWidgets.QHBoxLayout())
        self._recipe_list_container_layout.addWidget(recipe_widget)

        self._add_left_column_to_recipe_widget(recipe_widget, recipe)
        self._add_right_column_to_recipe_widget(recipe_widget, recipe)

    def _add_left_column_to_recipe_widget(self, recipe_widget, recipe):
        # container
        left_column = QtWidgets.QWidget()
        left_column_layout = QtWidgets.QVBoxLayout()
        left_column.setLayout(left_column_layout)
        recipe_widget.layout().addWidget(left_column)

        # title with buttons
        recipe_title_container = QtWidgets.QWidget()
        recipe_title_container_layout = QtWidgets.QHBoxLayout()
        recipe_title_container.setLayout(recipe_title_container_layout)
        left_column_layout.addWidget(recipe_title_container)

        # edit button
        if not recipe.is_fixed:
            icon = qt_icon_from_file_name("edit.png")
            edit_button = QtWidgets.QPushButton(icon, "")
            edit_button.setProperty("class", "BtnEdit")
            edit_button.clicked.connect(
                lambda checked, r=recipe: self._open_edit(r))
            recipe_title_container_layout.addWidget(edit_button, 0)

        # title
        recipe_title = QtWidgets.QLabel(recipe.name)
        recipe_title.setProperty("class", "RecipeTitle")
        recipe_title_container_layout.addWidget(recipe_title, 1)

        # items container for holding the recipe items
        recipe_items_container = QtWidgets.QWidget()
        recipe_items_container.setLayout(QtWidgets.QVBoxLayout())
        left_column_layout.addWidget(recipe_items_container, 1)

        # add items
        item: RecipeItem
        for item in recipe.items:
            label = QtWidgets.QLabel()
            if item.ingredient.type == IngredientType.STIRR:
                label.setText(f"-{item.ingredient.name}-")
            elif item.ingredient.type == IngredientType.SUGAR:
                label.setText(f"{item.amount:.0f} TL {item.ingredient.name}")
            else:
                label.setText(f"{item.amount:.0f} cl {item.ingredient.name}")
            recipe_items_container.layout().addWidget(label)

    def _add_right_column_to_recipe_widget(self, recipe_widget, recipe):
        # container
        right_column = QtWidgets.QWidget()
        right_column_layout = QtWidgets.QVBoxLayout()
        right_column.setLayout(right_column_layout)
        recipe_widget.layout().addWidget(right_column)

        fillings = []
        for item in recipe.items:
            if item.ingredient.type != IngredientType.STIRR:
                relative = item.amount / self.barbot_.config.max_cocktail_size
                filling = GlasFilling(item.ingredient.color, relative)
                fillings.append(filling)
        indicator = GlasIndicator(fillings)
        right_column_layout.addWidget(indicator)
        # pylint: disable-next=no-member
        right_column_layout.setAlignment(indicator, QtCore.Qt.AlignmentFlag.AlignRight)

        # instruction
        if recipe.post_instruction:
            instruction = QtWidgets.QLabel(recipe.post_instruction)
            instruction.setWordWrap(True)
            right_column_layout.addWidget(instruction)

        # order button
        if recipe.is_available(self.barbot_.ports, self.barbot_.config):
            icon = qt_icon_from_file_name("order.png")
            order_button = QtWidgets.QPushButton(icon, "")
            order_button.setProperty("class", "BtnOrder")
            order_button.clicked.connect(
                lambda _, r=recipe: self._order(r))
            right_column_layout.addWidget(order_button, 0)
            # pylint: disable-next=no-member
            right_column_layout.setAlignment(order_button, QtCore.Qt.AlignmentFlag.AlignRight)

    def _open_edit(self, recipe: Recipe):
        self.window.set_view(RecipeNewOrEdit(self.window, recipe))

    def _order(self, recipe):
        if self.barbot_.is_busy:
            self.window.show_message(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        if recipe is None:
            self.window.show_message("Rezept nicht gefunden")
            return
        self.window.set_view(OrderRecipe(self.window, recipe))


class RecipeNewOrEdit(UserView):
    """View for editing existing recpies and creating new ones"""
    def __init__(self, window: BarBotWindow, recipe: Optional[Recipe] = None):
        super().__init__(window)

        if recipe is None:
            self._recipe = Recipe()
            self._original_recipe = None
        else:
            self._original_recipe = recipe
            self._recipe = recipe.copy()

        self._content_layout = QtWidgets.QVBoxLayout()
        self._content.setLayout(self._content_layout)
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        title = "Neues Rezept" if self._original_recipe is None else "Rezept bearbeiten"
        self._add_title_to_fixed_content(title)

        self._add_name_and_instruction()
        self._add_ingredients(10)
        self._add_filling_and_save_button()

        self._add_dummy_widget_to_content()

        self._update_view()

    def _add_name_and_instruction(self):
        # wrapper for name and instruction
        wrapper = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout()
        wrapper.setLayout(form_layout)
        form_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.addWidget(wrapper)

        # name
        self._name_widget = QtWidgets.QLineEdit(self._recipe.name)
        self._name_widget.mousePressEvent = self._open_keyboard_for_name_widget
        label = QtWidgets.QLabel("Name:")
        form_layout.addRow(label, self._name_widget)

        # pre instruction
        self._pre_instruction_widget = QtWidgets.QLineEdit()
        self._pre_instruction_widget.setText(self._recipe.pre_instruction)
        self._pre_instruction_widget.mousePressEvent = self._open_keyboard_for_pre_instruction
        label = QtWidgets.QLabel("Vorher:")
        form_layout.addRow(label, self._pre_instruction_widget)

        # post instruction
        widget  = QtWidgets.QLineEdit()
        widget.setText(self._recipe.post_instruction)
        widget.mousePressEvent = self._open_keyboard_for_post_instruction_widget
        self._post_instruction_widget = widget
        label = QtWidgets.QLabel("Nachher:")
        form_layout.addRow(label, self._post_instruction_widget)

    # pylint: disable-next=unused-argument
    def _open_keyboard_for_name_widget(self, a0):
        self.window.open_keyboard(self._name_widget)

    # pylint: disable-next=unused-argument
    def _open_keyboard_for_pre_instruction(self, a0):
        self.window.open_keyboard(self._pre_instruction_widget)

    # pylint: disable-next=unused-argument
    def _open_keyboard_for_post_instruction_widget(self, a0):
        self.window.open_keyboard(self._post_instruction_widget)

    def _add_ingredients(self, max_count):
        self._content_layout.addWidget(QtWidgets.QLabel("Zutaten:"))
        ingredients_container = QtWidgets.QWidget()
        ingredients_container_layout = QtWidgets.QGridLayout()
        ingredients_container.setLayout(ingredients_container_layout)
        self._content_layout.addWidget(ingredients_container, 1)
        # fill grid
        self._ingredient_widgets = []
        for i in range(max_count):
            # get selected checkbox entry or default
            if not self._is_new_cocktail and i < len(self._recipe.items):
                selected_amount = self._recipe.items[i].amount
                selected_ingredient = self._recipe.items[i].ingredient
            else:
                selected_amount = 0
                selected_ingredient = None
            # add ingredient name
            ingredient_widget = self.window.combobox_ingredients(selected_ingredient)
            ingredient_widget.currentIndexChanged.connect(self._update_view)
            ingredients_container_layout.addWidget(ingredient_widget, i, 0)
            # add ingredient amount
            amount_widget = self.window.combobox_amounts(selected_amount)
            amount_widget.currentIndexChanged.connect(self._update_view)
            if(i >= len(self._recipe.items) \
               or self._recipe.items[i].ingredient.type == IngredientType.STIRR):
                amount_widget.setVisible(False)
            ingredients_container_layout.addWidget(amount_widget, i, 1)

            # safe references for later
            self._ingredient_widgets.append([ingredient_widget, amount_widget])

    def _add_filling_and_save_button(self):
        # row for label and button
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        self._content_layout.addWidget(row)
        # label
        self._filling_label = QtWidgets.QLabel()
        row.layout().addWidget(self._filling_label)
        # save button
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(self._save)
        row.layout().addWidget(button)
        # pylint: disable-next=no-member
        row.layout().setAlignment(button, QtCore.Qt.AlignmentFlag.AlignCenter)

    def _get_cocktail_size(self):
        size = 0
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            amount = int(amount_widget.currentData())
            # ignore the stirring when accumulating size
            if ingredient is None:
                continue
            if ingredient.type == IngredientType.STIRR:
                continue
            if amount < 0:
                continue
            size = size + amount
        return size

    def _force_redraw(self, element):
        element.style().unpolish(element)
        element.style().polish(element)

    def _update_view(self):
        # cocktail size
        size = self._get_cocktail_size()
        max_size = self.barbot_.config.max_cocktail_size
        label = self._filling_label
        label.setText(f"{size} von {max_size} cl")
        has_error = size > max_size
        label.setProperty("class", "HasError" if has_error else "")
        self._force_redraw(label)
        # visibility
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            should_be_visible = ingredient is not None and ingredient.type != IngredientType.STIRR
            if amount_widget.isVisible() != should_be_visible:
                amount_widget.setVisible(should_be_visible)

    def _save(self):
        # check data
        self._recipe.name = self._name_widget.text()
        if self._recipe.name is None or self._recipe.name == "":
            self.window.show_message("Bitte einen Namen eingeben")
            return
        if self._original_recipe is None or self._recipe.name != self._original_recipe.name:
            # name changed or new recipe
            names = [
                recipe.name
                for recipe
                in self.window.recipes.get_filtered(None, self.barbot_.ports, self.barbot_.config)
            ]
            if self._recipe.name in names:
                self.window.show_message("Ein Cocktail mit diesem Namen existiert bereits")
                return
        size = self._get_cocktail_size()
        if size > self.barbot_.config.max_cocktail_size:
            self.window.show_message("Dein Cocktail ist zu groß.")
            return
        if size == 0:
            self.window.show_message("Der Cocktail ist leer.")
            return
        self._recipe.pre_instruction = self._pre_instruction_widget.text()
        self._recipe.post_instruction = self._post_instruction_widget.text()
        # prepare data
        self._recipe.items = []
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            amount = int(amount_widget.currentData())
            if ingredient is None:
                continue
            if amount == 0 and ingredient.type != IngredientType.STIRR:
                continue

            if ingredient.type == IngredientType.STIRR:
                item = RecipeItem(ingredient, 2000)
            else:
                item = RecipeItem(ingredient, amount)
            self._recipe.items.append(item)
        if not self._is_new_cocktail and self._recipe.equal_to(self._original_recipe):
            self.window.show_message("Rezept wurde nicht verändert")
            return
        # save copy or new recipe
        if self._original_recipe is not None:
            self.window.recipes.remove(self._original_recipe)
        self.window.recipes.add(self._recipe)
        if self._is_new_cocktail:
            self._reload_with_message("Neues Rezept gespeichert")
        else:
            self._reload_with_message("Rezept gespeichert")

    def _reload_with_message(self, message):
        self.window.set_view(RecipeNewOrEdit(self.window, self._recipe))
        self.window.show_message(message)


class SingleIngredient(UserView):
    """View for adding single ingredients"""
    class ActionType(Enum):
        """The type of ingredient that should be added"""
        INGREDIENT = auto()
        STIR = auto()
        STRAW = auto()
        ICE = auto()

    def __init__(self, window: BarBotWindow):
        super().__init__(window)

        self._ice_index = -2
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        self._add_title_to_fixed_content("Nachschlag")
        self._add_info_text()
        self._add_ingredient_section()

        if self.barbot_.config.straw_dispenser_connected:
            self._add_straw_button()
        if self.barbot_.config.stirrer_connected:
            self._add_stir_button()
        if self.barbot_.config.ice_crusher_connected:
            self._add_crusher_button()

        self._add_dummy_widget_to_content()

    def _add_info_text(self):
        text = QtWidgets.QLabel(
            "Ist dein Cocktail noch nicht perfekt?\nHier kannst du nachhelfen.")
        self._content.layout().addWidget(text)

    def _add_ingredient_section(self):
        panel = QtWidgets.QWidget()
        panel.setProperty("class", "CenterPanel")
        panel.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(panel)
        # pylint: disable-next=no-member
        self._content.layout().setAlignment(panel, QtCore.Qt.AlignmentFlag.AlignCenter)

        # ingredient selector
        self._ingredient_widget = self.window.combobox_ingredients(
            only_available=True,
            only_weighed=True
        )
        panel.layout().addWidget(self._ingredient_widget)

        # amount selector
        self._amount_widget = self.window.combobox_amounts()
        panel.layout().addWidget(self._amount_widget)

        # start button
        self._start_button = QtWidgets.QPushButton("Los")
        self._start_button.clicked.connect(
            lambda: self._start(self.ActionType.INGREDIENT)
        )
        panel.layout().addWidget(self._start_button)

    def _add_stir_button(self):
        icon = qt_icon_from_file_name("stir.png")
        stir_button = QtWidgets.QPushButton(icon, "")
        stir_button.setProperty("class", "IconButton")
        stir_button.clicked.connect(
            lambda: self._start(self.ActionType.STIR)
        )
        self._content.layout().addWidget(stir_button)
        # pylint: disable-next=no-member
        self._content.layout().setAlignment(stir_button, QtCore.Qt.AlignmentFlag.AlignCenter)

    def _add_straw_button(self):
        icon = qt_icon_from_file_name("straw.png")
        straw_button = QtWidgets.QPushButton(icon, "")
        straw_button.setProperty("class", "IconButton")
        straw_button.clicked.connect(
            lambda: self._start(self.ActionType.STRAW)
        )
        self._content.layout().addWidget(straw_button)
        # pylint: disable-next=no-member
        self._content.layout().setAlignment(straw_button, QtCore.Qt.AlignmentFlag.AlignCenter)

    def _add_crusher_button(self):
        icon = qt_icon_from_file_name("ice.png")
        ice_button = QtWidgets.QPushButton(icon, "")
        ice_button.setProperty("class", "IconButton")
        ice_button.clicked.connect(
            lambda: self._start(self.ActionType.ICE)
        )
        self._content.layout().addWidget(ice_button)
        # pylint: disable-next=no-member
        self._content.layout().setAlignment(ice_button, QtCore.Qt.AlignmentFlag.AlignCenter)

    def _start(self, action_type: ActionType):
        if self.barbot_.is_busy:
            self.window.show_message(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        config = self.barbot_.config
        if action_type == self.ActionType.INGREDIENT:
            ingredient = self._ingredient_widget.currentData()
            amount = self._amount_widget.currentData()
            if ingredient is not None and amount > 0:
                item = RecipeItem(ingredient, amount)
                if item.ingredient.type == IngredientType.SUGAR:
                    pass
                else:
                    # normal ingredient
                    port = self.barbot_.ports.port_of_ingredient(ingredient)
                    if port is None:
                        self.window.show_message(
                            "Diese Zutat ist nicht anschlossen")
                        return
                item.amount = amount
                item.ingredient = ingredient
                self.barbot_.start_single_ingredient(item)
                self.window.show_message("Zutat wird hinzugefügt")
            else:
                self.window.show_message(
                    "Bitte eine Zutat und\neine Menge auswählen")
        elif action_type == self.ActionType.STIR and config.stirrer_connected:
            item = RecipeItem(StirIngredient, 0)
            self.barbot_.start_single_ingredient(item)
            self.window.show_message("Cocktail wird gerührt")
        elif action_type == self.ActionType.ICE and config.ice_crusher_connected:
            self.barbot_.start_crushing()
            self.window.show_message("Eis wird hinzugefügt")
        elif action_type == self.ActionType.STRAW and config.straw_dispenser_connected:
            self.barbot_.start_straw()
            self.window.show_message("Strohhalm wird hinzugefügt")


class Statistics(UserView):
    """View that shows statistics of a party"""
    def __init__(self, window: BarBotWindow):
        super().__init__(window)
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
        dates_widget = QtWidgets.QComboBox()
        selected_party_index = 0
        for index, party in enumerate(self.barbot_.parties):
            dates_widget.addItem(party.start.strftime("%Y-%m-%d"), party)
            if party == self.barbot_.parties.current_party:
                selected_party_index = index
        dates_widget.setCurrentIndex(selected_party_index)
        dates_widget.currentIndexChanged.connect(
            lambda _: self._update_view(dates_widget.currentData())
        )
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
            # pylint: disable-next=no-member
            self._statistics_widget.setParent(None) # type: ignore
            self._statistics_widget = None

class OrderRecipe(UserView):
    """Shown when the order button is clicked for a recipe"""
    def __init__(self, window: BarBotWindow, recipe: Recipe):
        super().__init__(window)

        self._recipe = recipe
        self._cb_ice = None
        self._cb_straw = None

        self._content_layout = QtWidgets.QGridLayout()
        self._content.setLayout(self._content_layout)
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        self._add_title_to_fixed_content("Cocktail mischen")
        self._add_centered_content_to_content()
        self._add_cocktail_name_to_centered_content()
        self._add_special_ingredient_buttons()
        if recipe.pre_instruction:
            self._add_pre_instruction_to_centered_content()
        self._add_order_and_cancel_button_to_centered_content()

    def _add_order_and_cancel_button_to_centered_content(self):
        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self._centered_content.layout().addWidget(buttons_container)

        # cancel
        button = QtWidgets.QPushButton("Abbrechen")

        def show_list():
            self.window.set_view(ListRecipes(self.window))
        button.clicked.connect(show_list)
        buttons_container.layout().addWidget(button)
        # order
        button = QtWidgets.QPushButton("Los!")
        button.clicked.connect(self._order)
        buttons_container.layout().addWidget(button)

    def _add_cocktail_name_to_centered_content(self):
        label = QtWidgets.QLabel(self._recipe.name)
        label.setProperty("class", "Headline")
        self._centered_content.layout().addWidget(label)

    def _add_pre_instruction_to_centered_content(self):
        text = "Bitte Glas vorbereiten:\n" + self._recipe.pre_instruction
        label = QtWidgets.QLabel(text)
        self._centered_content.layout().addWidget(label)

    def _add_centered_content_to_content(self):
        self._centered_content = QtWidgets.QWidget()
        self._centered_content.setLayout(QtWidgets.QVBoxLayout())
        self._centered_content.setProperty("class", "CenteredContent")
        # pylint: disable-next=no-member
        self._content_layout.addWidget(self._centered_content, 0, 0, QtCore.Qt.AlignmentFlag.AlignCenter)

    def _add_special_ingredient_buttons(self):
        # container
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QHBoxLayout())
        self._centered_content.layout().addWidget(container)

        # ask for ice if module is connected
        if self.barbot_.config.ice_crusher_connected:
            self._add_ice_button_to(container)

        # ask for straw if module is connected
        if self.barbot_.config.straw_dispenser_connected:
            self._add_straw_button_to(container)

    def _add_ice_button_to(self, container):
        icon = qt_icon_from_file_name("ice.png")
        ice_button = QtWidgets.QPushButton(icon, "")
        ice_button.setCheckable(True)
        ice_button.setProperty("class", "IconCheckButton")
        container.layout().addWidget(ice_button)
        # pylint: disable-next=no-member
        container.layout().setAlignment(ice_button, QtCore.Qt.AlignmentFlag.AlignCenter)
        self._cb_ice = ice_button

    def _add_straw_button_to(self, container):
        icon = qt_icon_from_file_name("straw.png")
        straw_button = QtWidgets.QPushButton(icon, "")
        straw_button.setCheckable(True)
        straw_button.setProperty("class", "IconCheckButton")
        container.layout().addWidget(straw_button)
        # pylint: disable-next=no-member
        container.layout().setAlignment(straw_button, QtCore.Qt.AlignmentFlag.AlignCenter)
        self._cb_straw = straw_button

    def _order(self):
        add_ice = self._cb_ice.isChecked() if self._cb_ice is not None else False
        add_straw = self._cb_straw.isChecked() if self._cb_straw is not None else False
        self.barbot_.start_mixing(
            MixingOptions(
                self._recipe,
                add_straw=add_straw,
                add_ice=add_ice
            )
        )
