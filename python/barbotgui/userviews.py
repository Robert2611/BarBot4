from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import barbotgui
import barbot
from barbotgui import IdleView, MainWindow
from enum import Enum, auto


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
        recipes = self.db.list_recipes(self.window.recipe_filter)
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
            icon = barbotgui.qt_icon_from_file_name("edit.png")
            edit_button = QtWidgets.QPushButton(icon, "")
            edit_button.setProperty("class", "BtnEdit")
            edit_button.clicked.connect(
                lambda checked, rid=recipe.id: self._open_edit(rid))
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
            item: barbot.RecipeItem
            for item in recipe.items:
                label = QtWidgets.QLabel()
                if item.isStirringItem():
                    label.setText("-%s-" % (item.name))
                else:
                    label.setText("%i cl %s" % (item.amount, item.name))
                recipe_items_container.layout().addWidget(label)

            # right column
            right_column = QtWidgets.QWidget()
            right_column.setLayout(QtWidgets.QVBoxLayout())
            recipe_box.layout().addWidget(right_column)

            fillings = []
            for item in recipe.items:
                if not item.isStirringItem():
                    relative = item.amount / self.bot.config.max_cocktail_size
                    filling = GlasFilling(item.color, relative, )
                    fillings.append(filling)
            indicator = GlasIndicator(fillings)
            right_column.layout().addWidget(indicator)
            right_column.layout().setAlignment(indicator, QtCore.Qt.AlignRight)

            # instruction
            if recipe.instruction:
                instruction = QtWidgets.QLabel(recipe.instruction)
                instruction.setWordWrap(True)
                right_column.layout().addWidget(instruction)

            # order button
            if recipe.available:
                icon = barbotgui.qt_icon_from_file_name("order.png")
                order_button = QtWidgets.QPushButton(icon, "")
                order_button.setProperty("class", "BtnOrder")
                order_button.clicked.connect(
                    lambda checked, rid=recipe.id: self._order(rid))
                right_column.layout().addWidget(order_button, 0)
                right_column.layout().setAlignment(order_button, QtCore.Qt.AlignRight)

        self._listbox.layout().addWidget(QtWidgets.QWidget(), 1)

    def _open_edit(self, id):
        self.window.set_view(RecipeNewOrEdit(self.window, id))

    def _order(self, id):
        if self.bot.is_busy():
            self.window.show_message(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        recipe = self.db.recipe(id)
        if recipe == None:
            self.window.show_message("Rezept nicht gefunden")
            return
        self.db.start_order(recipe.id)
        self.bot.start_mixing(recipe)


class RecipeNewOrEdit(IdleView):
    def __init__(self, window: MainWindow, recipe_id=None):
        super().__init__(window)
        self._id = recipe_id
        if self._id is not None:
            self._recipe = self.db.recipe(self._id)
        else:
            self._recipe = barbot.Recipe("", -1, "", True)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel(
            "Neues Rezept" if self._id is None else "Rezept bearbeiten")
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
        # instruction
        self._instruction_widget = QtWidgets.QLineEdit()
        self._instruction_widget.setText(self._recipe.instruction)

        def open_keyboard_for_instruction(event):
            self.window.open_keyboard(self._instruction_widget)
        self._instruction_widget.mousePressEvent = open_keyboard_for_instruction
        label = QtWidgets.QLabel("Zusatzinfo:")
        wrapper.layout().addRow(label, self._instruction_widget)

        # ingredients
        self._content.layout().addWidget(QtWidgets.QLabel("Zutaten:"))
        ingredients_container = QtWidgets.QWidget()
        ingredients_container.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(ingredients_container, 1)
        # fill grid
        self._ingredient_widgets = []
        for i in range(10):
            # get selected checkbox entry or default
            if self._id is not None and i < len(self._recipe.items):
                selected_amount = self._recipe.items[i].amount
                selected_ingredient = self._recipe.items[i].ingredient_id
            else:
                selected_amount = 0
                selected_ingredient = 0
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
            if(i >= len(self._recipe.items) or self._recipe.items[i].isStirringItem()):
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
            ingredient = int(ingredient_widget.currentData())
            amount = int(amount_widget.currentData())
            # ignore the stirring when accumulating size
            if ingredient >= 0 and ingredient != barbot.ingredient_id_stirring and amount >= 0:
                size = size + amount
        return size

    def _force_redraw(self, element):
        element.style().unpolish(element)
        element.style().polish(element)

    def _update_table(self):
        # cocktail size
        size = self._get_cocktail_size()
        max_size = self.window.bot.config.max_cocktail_size
        label = self._filling_label
        label.setText("%i von %i cl" % (size, max_size))
        if size > max_size:
            label.setProperty("class", "HasError")
        else:
            label.setProperty("class", "")
        self._force_redraw(label)
        # visibility
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient = int(ingredient_widget.currentData())
            should_be_visible = ingredient > 0 and ingredient != barbot.ingredient_id_stirring
            if(amount_widget.isVisible() != should_be_visible):
                amount_widget.setVisible(should_be_visible)

    def _save(self):
        # check data
        name = self._name_widget.text()
        if name == None or name == "":
            self.window.show_message("Bitte einen Namen eingeben")
            return
        if self._get_cocktail_size() > self.window.bot.config.max_cocktail_size:
            self.window.show_message("Dein Cocktail ist zu groß.")
            return
        instruction = self._instruction_widget.text()
        # prepare data
        items = []
        for ingredient_widget, amount_widget in self._ingredient_widgets:
            ingredient_id = int(ingredient_widget.currentData())
            amount = int(amount_widget.currentData())
            if ingredient_id >= 0 and (amount >= 0 or ingredient_id == barbot.ingredient_id_stirring):
                item = barbot.RecipeItem()
                item.ingredient_id = ingredient_id
                if ingredient_id == barbot.ingredient_id_stirring:
                    item.amount = 2000
                else:
                    item.amount = amount
                items.append(item)
        if self._id is not None and not self.db.has_recipe_changed(self._id, name, items, instruction):
            self.window.show_message("Rezept wurde nicht verändert")
            return
        # update Database
        new_id = self.db.create_or_update_recipe(name, instruction, self._id)
        self.db._insert_recipe_items(new_id, items)
        self._id = new_id
        if self._id == None:
            self._reload_with_message("Neues Rezept gespeichert")
        else:
            self._reload_with_message("Rezept gespeichert")

    def _reload_with_message(self, message):
        self.window.set_view(RecipeNewOrEdit(self.window, self._id))
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
            only_available=True, special_ingredients=False)
        panel.layout().addWidget(self._ingredient_widget)

        # amount selector
        self._amount_widget = self.window.combobox_amounts()
        panel.layout().addWidget(self._amount_widget)

        # start button
        start_button = QtWidgets.QPushButton("Los")
        start_button.clicked.connect(
            lambda: self._start(self.ActionType.ingredient))
        panel.layout().addWidget(start_button)

        if self.bot.config.straw_dispenser_connected:
            # straw button
            icon = barbotgui.qt_icon_from_file_name("straw.png")
            straw_button = QtWidgets.QPushButton(icon, "")
            straw_button.setProperty("class", "IconButton")
            straw_button.clicked.connect(
                lambda: self._start(self.ActionType.straw))
            self._content.layout().addWidget(straw_button)
            self._content.layout().setAlignment(straw_button, QtCore.Qt.AlignCenter)

        if self.bot.config.stirrer_connected:
            # stir button
            icon = barbotgui.qt_icon_from_file_name("stir.png")
            stir_button = QtWidgets.QPushButton(icon, "")
            stir_button.setProperty("class", "IconButton")
            stir_button.clicked.connect(
                lambda: self._start(self.ActionType.stir))
            self._content.layout().addWidget(stir_button)
            self._content.layout().setAlignment(stir_button, QtCore.Qt.AlignCenter)

        if self.bot.config.ice_crusher_connected:
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
        if self.bot.is_busy():
            self.window.show_message(
                "Bitte warten bis die laufende\nAktion abgeschlossen ist.")
            return
        if action_type == self.ActionType.ingredient:
            ingredient_id = self._ingredient_widget.currentData()
            amount = self._amount_widget.currentData()
            item = barbot.RecipeItem()
            if ingredient_id >= 0 and amount > 0:
                port_cal = self.db.port_and_calibration(ingredient_id)
                if port_cal == None:
                    self.window.show_message(
                        "Diese Zutat ist nicht anschlossen")
                    return
                item.port = port_cal["port"]
                item.calibration = port_cal["calibration"]
                item.name = port_cal["name"]
                item.amount = amount
                item.ingredient_id = ingredient_id
                self.bot.start_single_ingredient(item)
                self.window.show_message("Zutat wird hinzugefügt")
            else:
                self.window.show_message(
                    "Bitte eine Zutat und\neine Menge auswählen")
        elif action_type == self.ActionType.stir and self.bot.config.stirrer_connected:
            item = barbot.RecipeItem()
            item.ingredient_id = barbot.ingredient_id_stirring
            self.bot.start_single_ingredient(item)
            self.window.show_message("Cocktail wird gerührt")
        elif action_type == self.ActionType.ice and self.bot.config.ice_crusher_connected:
            self.bot.start_crushing()
            self.window.show_message("Eis wird hinzugefügt")
        elif action_type == self.ActionType.straw and self.bot.config.straw_dispenser_connected:
            self.bot.start_straw()
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

        label = QtWidgets.QLabel("Datum")
        row.layout().addWidget(label)

        self.parties = self.db.list_parties()
        dates_widget = QtWidgets.QComboBox()
        for party in self.parties:
            dates_widget.addItem(party["partydate"])
        dates_widget.currentTextChanged.connect(
            lambda newDate: self._update(newDate))
        row.layout().addWidget(dates_widget)

        self._content_wrapper = QtWidgets.QWidget()
        self._content_wrapper.setLayout(QtWidgets.QGridLayout())
        barbotgui.set_no_spacing(self._content_wrapper.layout())
        self._content.layout().addWidget(self._content_wrapper)

        # initialize with date of last party
        self._update(self.parties[0]["partydate"] if self.parties else None)

    def _update(self, date):
        if not date:
            return
        # self.total_count = self.parties[0]["ordercount"]
        from barbotgui.controls import BarChart

        # get data from database
        cocktail_count = self.db.ordered_cocktails_count(date)
        ingredients_amount = self.db.ordered_ingredients_amount(date)
        cocktails_by_time = self.db.ordered_cocktails_by_time(date)
        # create container
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QVBoxLayout())

        # total ordered cocktails
        total_cocktails = sum(c["count"] for c in cocktail_count)
        label = QtWidgets.QLabel("Bestellte Cocktails (%i)" % total_cocktails)
        container.layout().addWidget(label)
        # ordered cocktails by name
        data = [(c["name"], c["count"]) for c in reversed(cocktail_count)]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # total liters
        total_amount = sum([amount["liters"] for amount in ingredients_amount])
        label = QtWidgets.QLabel("Verbrauchte Zutaten (%i l)" % total_amount)
        container.layout().addWidget(label)
        # ingrediends
        data = [(c["ingredient"], c["liters"])
                for c in reversed(ingredients_amount)]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # label
        label = QtWidgets.QLabel("Bestellungen")
        container.layout().addWidget(label)
        # cocktails vs. time chart
        data = [(c["hour"], c["count"]) for c in reversed(cocktails_by_time)]
        chart = BarChart(data)
        container.layout().addWidget(chart)

        # set content
        if self.content is not None:
            # setting the parent of the previos content to None will destroy it
            self.content.setParent(None)
        self.content = container
        self._content_wrapper.layout().addWidget(container)
