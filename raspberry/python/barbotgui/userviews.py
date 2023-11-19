
from datetime import datetime
from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from enum import Enum, auto
import barbotgui
from barbotgui import IdleView, MainWindow
import barbot
from barbot import recipes as bbrecipes
from barbot import botconfig
from barbot import recipes
from barbot import orders
from barbot import ports
from barbot import ingredients
from barbot import statemachine


class ListRecipes(IdleView):
    def __init__(self, window: MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # filter: alcoholic
        self._cb_alcoholic = QtWidgets.QCheckBox("Alkoholisch")
        self._fixed_content.layout().addWidget(self._cb_alcoholic)
        self._cb_alcoholic.setChecked(self.window.recipe_filter.Alcoholic)

        def cb_alcoholic_toggled(s):
            self.window.recipe_filter.Alcoholic = self._cb_alcoholic.isChecked()
            self._update_list()
        self._cb_alcoholic.toggled.connect(cb_alcoholic_toggled)

        # filter: available
        self._cb_available = QtWidgets.QCheckBox("Nur verfügbare")
        self._fixed_content.layout().addWidget(self._cb_available)
        self._cb_available.setChecked(self.window.recipe_filter.AvailableOnly)

        def cb_available_toggled(s):
            self.window.recipe_filter.AvailableOnly = self._cb_available.isChecked()
            self._update_list()
        self._cb_available.toggled.connect(cb_available_toggled)

        self._listbox = QtWidgets.QWidget()
        self._listbox.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(self._listbox)

        barbotgui.set_no_spacing(self._listbox.layout())

        self._update_list()

    def _update_list(self):
        from barbotgui.controls import GlasFilling, GlasIndicator
        recipes = bbrecipes.filter(self.window.recipe_filter)
        # clear the list
        while self._listbox.layout().count():
            item = self._listbox.layout().takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        # fill it with the recipes
        for recipe in recipes:
            # box to hold the recipe
            recipe_box = QtWidgets.QWidget()
            recipe_box.setLayout(QtWidgets.QHBoxLayout())
            self._listbox.layout().addWidget(recipe_box)

            # left column
            left_column = QtWidgets.QWidget()
            left_column.setLayout(QtWidgets.QVBoxLayout())
            recipe_box.layout().addWidget(left_column)

            # title with buttons
            recipe_title_container = QtWidgets.QWidget()
            recipe_title_container.setLayout(QtWidgets.QHBoxLayout())
            left_column.layout().addWidget(recipe_title_container)

            # edit button
            if not recipe.is_fixed:
                icon = barbotgui.qt_icon_from_file_name("edit.png")
                edit_button = QtWidgets.QPushButton(icon, "")
                edit_button.setProperty("class", "BtnEdit")
                edit_button.clicked.connect(
                    lambda checked, r=recipe: self._open_edit(r))
                recipe_title_container.layout().addWidget(edit_button, 0)

            # title
            recipe_title = QtWidgets.QLabel(recipe.name)
            recipe_title.setProperty("class", "RecipeTitle")
            recipe_title_container.layout().addWidget(recipe_title, 1)

            # items container for holding the recipe items
            recipe_items_container = QtWidgets.QWidget()
            recipe_items_container.setLayout(QtWidgets.QVBoxLayout())
            left_column.layout().addWidget(recipe_items_container, 1)

            # add items
            item: bbrecipes.RecipeItem
            for item in recipe.items:
                label = QtWidgets.QLabel()
                if item.ingredient.type == ingredients.IngredientType.Stirr:
                    label.setText(f"-{item.ingredient.name}-")
                elif item.ingredient.type == ingredients.IngredientType.Sugar:
                    label.setText(f"{item.amount:.0f} TL {item.ingredient.name}")
                else:
                    label.setText(f"{item.amount:.0f} cl {item.ingredient.name}")
                recipe_items_container.layout().addWidget(label)

            # right column
            right_column = QtWidgets.QWidget()
            right_column.setLayout(QtWidgets.QVBoxLayout())
            recipe_box.layout().addWidget(right_column)

            fillings = []
            for item in recipe.items:
                if item.ingredient.type != ingredients.IngredientType.Stirr:
                    relative = item.amount / botconfig.max_cocktail_size
                    filling = GlasFilling(item.ingredient.color, relative)
                    fillings.append(filling)
            indicator = GlasIndicator(fillings)
            right_column.layout().addWidget(indicator)
            right_column.layout().setAlignment(indicator, QtCore.Qt.AlignRight)

            # instruction
            if recipe.post_instruction:
                instruction = QtWidgets.QLabel(recipe.post_instruction)
                instruction.setWordWrap(True)
                right_column.layout().addWidget(instruction)

            # order button
            if recipe.available():
                icon = barbotgui.qt_icon_from_file_name("order.png")
                order_button = QtWidgets.QPushButton(icon, "")
                order_button.setProperty("class", "BtnOrder")
                order_button.clicked.connect(
                    lambda _, r=recipe: self._order(r))
                right_column.layout().addWidget(order_button, 0)
                right_column.layout().setAlignment(order_button, QtCore.Qt.AlignRight)

        self._listbox.layout().addWidget(QtWidgets.QWidget(), 1)

    def _open_edit(self, recipe: recipes.Recipe):
        self.window.set_view(RecipeNewOrEdit(self.window, recipe))

    def _order(self, recipe):
        if statemachine.is_busy():
            self.window.show_message(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        if recipe == None:
            self.window.show_message("Rezept nicht gefunden")
            return
        self.window.set_view(OrderRecipe(self.window, recipe))


class RecipeNewOrEdit(IdleView):
    def __init__(self, window: MainWindow, recipe: recipes.Recipe = None):
        super().__init__(window)

        if recipe is not None:
            self._original_recipe = recipe
            self._recipe = recipe.copy()
            self._new = False
        else:
            self._recipe = recipes.Recipe()
            self._original_recipe = None
            self._new = True
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel(
            "Neues Rezept" if self._new else "Rezept bearbeiten")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # wrapper for name and instruction
        wrapper = QtWidgets.QWidget()
        wrapper.setLayout(QtWidgets.QFormLayout())
        wrapper.layout().setContentsMargins(0, 0, 0, 0)
        self._content.layout().addWidget(wrapper)

        # name
        self._name_widget = QtWidgets.QLineEdit(self._recipe.name)

        def open_keyboard_for_name(event):
            self.window.open_keyboard(self._name_widget)
        self._name_widget.mousePressEvent = open_keyboard_for_name
        label = QtWidgets.QLabel("Name:")
        wrapper.layout().addRow(label, self._name_widget)

        # pre instruction
        self._pre_instruction_widget = QtWidgets.QLineEdit()
        self._pre_instruction_widget.setText(self._recipe.pre_instruction)

        def open_keyboard_for_pre_instruction(event):
            self.window.open_keyboard(self._pre_instruction_widget)
        self._pre_instruction_widget.mousePressEvent = open_keyboard_for_pre_instruction
        label = QtWidgets.QLabel("Vorher:")
        wrapper.layout().addRow(label, self._pre_instruction_widget)

        # post instruction
        self._post_instruction_widget = QtWidgets.QLineEdit()
        self._post_instruction_widget.setText(self._recipe.post_instruction)

        def open_keyboard_for_post_instruction(event):
            self.window.open_keyboard(self._post_instruction_widget)
        self._post_instruction_widget.mousePressEvent = open_keyboard_for_post_instruction
        label = QtWidgets.QLabel("Nachher:")
        wrapper.layout().addRow(label, self._post_instruction_widget)

        # ingredients
        self._content.layout().addWidget(QtWidgets.QLabel("Zutaten:"))
        ingredients_container = QtWidgets.QWidget()
        ingredients_container.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(ingredients_container, 1)
        # fill grid
        self._ingredient_widgets = []
        for i in range(10):
            # get selected checkbox entry or default
            if not self._new and i < len(self._recipe.items):
                selected_amount = self._recipe.items[i].amount
                selected_ingredient = self._recipe.items[i].ingredient
            else:
                selected_amount = 0
                selected_ingredient = None
            # add ingredient name
            ingredient_widget = self.window.combobox_ingredients(
                selected_ingredient)
            ingredient_widget.currentIndexChanged.connect(
                lambda: self._update_table())
            ingredients_container.layout().addWidget(ingredient_widget, i, 0)
            # add ingredient amount
            amount_widget = self.window.combobox_amounts(selected_amount)
            amount_widget.currentIndexChanged.connect(
                lambda: self._update_table())
            if(i >= len(self._recipe.items) or self._recipe.items[i].ingredient.type == ingredients.IngredientType.Stirr):
                amount_widget.setVisible(False)
            ingredients_container.layout().addWidget(amount_widget, i, 1)

            # safe references for later
            self._ingredient_widgets.append([ingredient_widget, amount_widget])

        # row for label and button
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        self._content.layout().addWidget(row)
        # label
        self._filling_label = QtWidgets.QLabel()
        row.layout().addWidget(self._filling_label)
        # save button
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(lambda: self._save())
        row.layout().addWidget(button)
        row.layout().setAlignment(button, QtCore.Qt.AlignCenter)

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

        self._update_table()

    def _get_cocktail_size(self):
        size = 0
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            amount = int(amount_widget.currentData())
            # ignore the stirring when accumulating size
            if ingredient is None:
                continue
            if ingredient.type == ingredients.IngredientType.Stirr:
                continue
            if amount < 0:
                continue
            size = size + amount
        return size

    def _force_redraw(self, element):
        element.style().unpolish(element)
        element.style().polish(element)

    def _update_table(self):
        # cocktail size
        size = self._get_cocktail_size()
        max_size = botconfig.max_cocktail_size
        label = self._filling_label
        label.setText("%i von %i cl" % (size, max_size))
        if size > max_size:
            label.setProperty("class", "HasError")
        else:
            label.setProperty("class", "")
        self._force_redraw(label)
        # visibility
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = ingredient_widget.currentData()
            should_be_visible = ingredient is not None and ingredient.type != ingredients.IngredientType.Stirr
            if(amount_widget.isVisible() != should_be_visible):
                amount_widget.setVisible(should_be_visible)

    def _save(self):
        # check data
        self._recipe.name = self._name_widget.text()
        if self._recipe.name == None or self._recipe.name == "":
            self.window.show_message("Bitte einen Namen eingeben")
            return
        if self._new or self._recipe.name != self._original_recipe.name:
            # name changed or new recipe
            if self._recipe.name in [recipe.name for recipe in bbrecipes.filter(None)]:
                self.window.show_message(
                    "Ein Cocktail mit diesem Namen existiert bereits")
                return
        size = self._get_cocktail_size()
        if size > botconfig.max_cocktail_size:
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
            if amount == 0 and ingredient.type != ingredients.IngredientType.Stirr:
                continue

            if ingredient.type == ingredients.IngredientType.Stirr:
                item = recipes.RecipeItem(ingredient, 2000)
            else:
                item = recipes.RecipeItem(ingredient, amount)
            self._recipe.items.append(item)
        if not self._new and self._recipe.equal_to(self._original_recipe):
            self.window.show_message("Rezept wurde nicht verändert")
            return
        # save copy or new recipe
        if not self._new:
            bbrecipes.remove(self._original_recipe)
        bbrecipes.add(self._recipe)
        if self._new:
            self._reload_with_message("Neues Rezept gespeichert")
        else:
            self._reload_with_message("Rezept gespeichert")

    def _reload_with_message(self, message):
        self.window.set_view(RecipeNewOrEdit(self.window, self._recipe))
        self.window.show_message(message)


class SingleIngredient(IdleView):
    _ice_index = -2

    class ActionType(Enum):
        ingredient = auto()
        stir = auto()
        straw = auto()
        ice = auto()

    def __init__(self, window: MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("Nachschlag")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # text
        text = QtWidgets.QLabel(
            "Ist dein Cocktail noch nicht perfekt?\nHier kannst du nachhelfen.")
        self._content.layout().addWidget(text)

        # selectors
        panel = QtWidgets.QWidget()
        panel.setProperty("class", "CenterPanel")
        panel.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(panel)
        self._content.layout().setAlignment(panel, QtCore.Qt.AlignCenter)

        # ingredient selector
        self._ingredient_widget = self.window.combobox_ingredients(
            only_available=True, only_weighed=True)
        panel.layout().addWidget(self._ingredient_widget)

        # amount selector
        self._amount_widget = self.window.combobox_amounts()
        panel.layout().addWidget(self._amount_widget)

        # start button
        start_button = QtWidgets.QPushButton("Los")
        start_button.clicked.connect(
            lambda: self._start(self.ActionType.ingredient))
        panel.layout().addWidget(start_button)

        if botconfig.straw_dispenser_connected:
            # straw button
            icon = barbotgui.qt_icon_from_file_name("straw.png")
            straw_button = QtWidgets.QPushButton(icon, "")
            straw_button.setProperty("class", "IconButton")
            straw_button.clicked.connect(
                lambda: self._start(self.ActionType.straw))
            self._content.layout().addWidget(straw_button)
            self._content.layout().setAlignment(straw_button, QtCore.Qt.AlignCenter)

        if botconfig.stirrer_connected:
            # stir button
            icon = barbotgui.qt_icon_from_file_name("stir.png")
            stir_button = QtWidgets.QPushButton(icon, "")
            stir_button.setProperty("class", "IconButton")
            stir_button.clicked.connect(
                lambda: self._start(self.ActionType.stir))
            self._content.layout().addWidget(stir_button)
            self._content.layout().setAlignment(stir_button, QtCore.Qt.AlignCenter)

        if botconfig.ice_crusher_connected:
            # ice button
            icon = barbotgui.qt_icon_from_file_name("ice.png")
            ice_button = QtWidgets.QPushButton(icon, "")
            ice_button.setProperty("class", "IconButton")
            ice_button.clicked.connect(
                lambda: self._start(self.ActionType.ice))
            self._content.layout().addWidget(ice_button)
            self._content.layout().setAlignment(ice_button, QtCore.Qt.AlignCenter)

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _start(self, action_type):
        if statemachine.is_busy():
            self.window.show_message(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        if action_type == self.ActionType.ingredient:
            ingredient = self._ingredient_widget.currentData()
            amount = self._amount_widget.currentData()
            if ingredient is not None and amount > 0:
                item = recipes.RecipeItem(ingredient, amount)
                if item.ingredient.type == ingredients.IngredientType.Sugar:
                    pass
                else:
                    # normal ingredient
                    port = ports.port_of_ingredient(ingredient)
                    if port is None:
                        self.window.show_message(
                            "Diese Zutat ist nicht anschlossen")
                        return
                item.amount = amount
                item.ingredient = ingredient
                statemachine.start_single_ingredient(item)
                self.window.show_message("Zutat wird hinzugefügt")
            else:
                self.window.show_message(
                    "Bitte eine Zutat und\neine Menge auswählen")
        elif action_type == self.ActionType.stir and botconfig.stirrer_connected:
            item = recipes.RecipeItem(ingredients.Stir, 0)
            statemachine.start_single_ingredient(item)
            self.window.show_message("Cocktail wird gerührt")
        elif action_type == self.ActionType.ice and botconfig.ice_crusher_connected:
            statemachine.start_crushing()
            self.window.show_message("Eis wird hinzugefügt")
        elif action_type == self.ActionType.straw and botconfig.straw_dispenser_connected:
            statemachine.start_straw()
            self.window.show_message("Strohhalm wird hinzugefügt")


class Statistics(IdleView):
    content = None

    def __init__(self, window: MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("Statistik")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # date selector
        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        self._content.layout().addWidget(row)
        # - label
        label = QtWidgets.QLabel("Datum")
        row.layout().addWidget(label)
        # - dropdown
        self.parties = orders.get_parties()
        dates_widget = QtWidgets.QComboBox()
        for party in self.parties:
            dates_widget.addItem(party.start.strftime("%Y-%m-%d"), party)
        dates_widget.currentIndexChanged.connect(
            lambda newDate: self._update(dates_widget.currentData()))
        row.layout().addWidget(dates_widget)
        
        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

        self._content_wrapper = QtWidgets.QWidget()
        self._content_wrapper.setLayout(QtWidgets.QGridLayout())
        barbotgui.set_no_spacing(self._content_wrapper.layout())
        self._content.layout().addWidget(self._content_wrapper)

        # initialize with date of last party
        self._update(self.parties[0] if self.parties else None)

    def _update(self, party: orders.Party):
        if party is None:
            return
        from barbotgui.controls import BarChart

        statistics = orders.get_statistics(party)

        # create container
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QVBoxLayout())

        # total ordered cocktails
        label = QtWidgets.QLabel("Bestellte Cocktails (%i)" %
                                 statistics["total_cocktails"])
        container.layout().addWidget(label)
        # ordered cocktails by name
        data = statistics["cocktail_count"].items()
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # total liters
        total_amount = sum(statistics["ingredients_amount"].values()) / 100.0
        label = QtWidgets.QLabel(
            "Verbrauchte Zutaten ({0:.2g} l)".format(total_amount))
        container.layout().addWidget(label)
        # ingrediends
        data = [(ingr.name, amount / 100.0)
                for ingr, amount in statistics["ingredients_amount"].items()
                if ingr.type != ingredients.IngredientType.Stirr]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # label
        label = QtWidgets.QLabel("Bestellungen")
        container.layout().addWidget(label)
        # cocktails vs. time chart
        data = [(f"{dt.hour} bis {dt.hour+1} Uhr", count)
                for dt, count in statistics["cocktails_by_time"].items()]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # set content
        if self.content is not None:
            # setting the parent of the previos content to None will destroy it
            self.content.setParent(None)
        self.content = container
        self._content_wrapper.layout().addWidget(container)


class OrderRecipe(IdleView):
    def __init__(self, window: MainWindow, recipe: recipes.Recipe):
        super().__init__(window)
        self.recipe = recipe
        self._content.setLayout(QtWidgets.QGridLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("Cocktail mischen")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        centered = QtWidgets.QWidget()
        centered.setLayout(QtWidgets.QVBoxLayout())
        centered.setProperty("class", "CenteredContent")
        self._content.layout().addWidget(centered, 0, 0, QtCore.Qt.AlignCenter)

        # cocktail name
        label = QtWidgets.QLabel(recipe.name)
        label.setProperty("class", "Headline")
        centered.layout().addWidget(label)

        # container
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QHBoxLayout())
        centered.layout().addWidget(container)

        # ask for ice if module is connected
        if botconfig.ice_crusher_connected:
            icon = barbotgui.qt_icon_from_file_name("ice.png")
            ice_button = QtWidgets.QPushButton(icon, "")
            ice_button.setCheckable(True)
            ice_button.setProperty("class", "IconCheckButton")
            container.layout().addWidget(ice_button)
            container.layout().setAlignment(ice_button, QtCore.Qt.AlignCenter)
            self._cb_ice = ice_button
        else:
            self._cb_ice = None

        # ask for straw if module is connected
        if botconfig.straw_dispenser_connected:
            icon = barbotgui.qt_icon_from_file_name("straw.png")
            straw_button = QtWidgets.QPushButton(icon, "")
            straw_button.setCheckable(True)
            straw_button.setProperty("class", "IconCheckButton")
            container.layout().addWidget(straw_button)
            container.layout().setAlignment(straw_button, QtCore.Qt.AlignCenter)
            self._cb_straw = straw_button
        else:
            self._cb_straw = None

        if recipe.pre_instruction:
            text = "Bitte Glas vorbereiten:\n" + recipe.pre_instruction
            label = QtWidgets.QLabel(text)
            centered.layout().addWidget(label)

        # order and cancel button
        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(QtWidgets.QHBoxLayout())
        centered.layout().addWidget(buttons_container)
        # cancel
        button = QtWidgets.QPushButton("Abbrechen")

        def show_list():
            self.window.set_view(ListRecipes(self.window))
        button.clicked.connect(show_list)
        buttons_container.layout().addWidget(button)
        # order
        button = QtWidgets.QPushButton("Los!")
        button.clicked.connect(lambda _: self.order())
        buttons_container.layout().addWidget(button)

    def order(self):
        statemachine.add_ice = False
        if self._cb_ice is not None:
            statemachine.add_ice = self._cb_ice.isChecked()
        statemachine.add_straw = False
        if self._cb_straw is not None:
            statemachine.add_straw = self._cb_straw.isChecked()
        statemachine.start_mixing(self.recipe)
