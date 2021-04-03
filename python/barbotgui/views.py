from PyQt5 import QtWidgets, Qt, QtCore, QtGui
import barbotgui
import barbotgui.plot
import barbot
import os
from enum import Enum, auto


class BusyView(barbotgui.View):
    _mixing_progress_trigger = QtCore.pyqtSignal()
    _message_trigger = QtCore.pyqtSignal()
    _message = None

    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)

        # forward message changed
        self._message_trigger.connect(lambda: self._update_message())
        self.bot.on_message_changed = lambda: self._message_trigger.emit()

        self.setLayout(QtWidgets.QGridLayout())
        barbotgui.set_no_spacing(self.layout())

        centered = QtWidgets.QFrame()
        centered.setLayout(QtWidgets.QVBoxLayout())
        centered.setProperty("class", "CenteredContent")
        self.layout().addWidget(centered, 0, 0, QtCore.Qt.AlignCenter)

        self._title_label = QtWidgets.QLabel("")
        self._title_label.setAlignment(QtCore.Qt.AlignCenter)
        self._title_label.setProperty("class", "Headline")
        centered.layout().addWidget(self._title_label)

        self._content_container = QtWidgets.QWidget()
        self._content_container.setLayout(QtWidgets.QVBoxLayout())
        centered.layout().addWidget(self._content_container)

        self._message_container = QtWidgets.QWidget()
        self._message_container.setLayout(QtWidgets.QGridLayout())
        self._message_container.setVisible(False)
        centered.layout().addWidget(self._message_container)

        self._init_by_status()

        self._update_message()

    def _update_message(self):
        # delete old message
        if self._message is not None:
            self._message.setParent(None)

        # if message is none show the content again
        if self.bot.message is None:
            self._message_container.setVisible(False)
            self._content_container.setVisible(True)
            self._title_label.setVisible(True)
            return

        self._message = QtWidgets.QWidget()
        self._message.setLayout(QtWidgets.QVBoxLayout())
        self._message_container.layout().addWidget(self._message)

        message_label = QtWidgets.QLabel()
        self._message.layout().addWidget(message_label)

        buttons_container = QtWidgets.QWidget()
        buttons_container.setLayout(QtWidgets.QHBoxLayout())
        self._message.layout().addWidget(buttons_container)

        def add_button(text, result):
            button = QtWidgets.QPushButton(text)
            def callback(): return self.bot.set_user_input(result)
            button.clicked.connect(callback)
            buttons_container.layout().addWidget(button)

        if self.bot.message == barbot.UserMessages.ingredient_empty:
            message_string = "Die Zutat '%s' ist leer.\n" % self.bot.current_recipe_item.name
            message_string = message_string + "Bitte neue Flasche anschließen."
            message_label.setText(message_string)

            add_button("Cocktail abbrechen", False)
            add_button("Erneut versuchen", True)

        elif self.bot.message == barbot.UserMessages.place_glas:
            message_label.setText("Bitte ein Glas auf die Plattform stellen.")

        elif self.bot.message == barbot.UserMessages.mixing_done_remove_glas:
            message_label.setText(
                "Der Cocktail ist fertig gemischt.\n" +
                "Du kannst ihn von der Platform nehmen."
            )

            if self.bot.current_recipe.instruction:
                label = QtWidgets.QLabel("Zusätzliche Informationen:")
                self._message.layout().addWidget(label)

                instruction = QtWidgets.QLabel(
                    self.bot.current_recipe.instruction)
                self._message.layout().addWidget(instruction)

        elif self.bot.message == barbot.UserMessages.ask_for_straw:
            message_label.setText(
                "Möchtest du einen Strohhalm haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif self.bot.message == barbot.UserMessages.ask_for_ice:
            message_label.setText(
                "Möchtest du Eis in deinem Cocktail haben?")

            add_button("Ja", True)
            add_button("Nein", False)

        elif self.bot.message == barbot.UserMessages.straws_empty:
            message_label.setText("Strohhalm konnte nicht hinzugefügt werden.")

            add_button("Egal", False)
            add_button("Erneut versuchen", True)

        elif self.bot.message == barbot.UserMessages.ice_empty:
            message_label.setText("Eis konnte nicht hinzugefügt werden.")

            add_button("Egal", False)
            add_button("Erneut versuchen", True)

        elif self.bot.message == barbot.UserMessages.cleaning_adapter:
            text = "Für die Reinigung muss der Reinigungsadapter angeschlossen sein.\n"
            text = text + "Ist der Adapter angeschlossen?"
            message_label.setText(text)

            add_button("Ja", True)
            add_button("Abbrechen", False)

        self._message_container.setVisible(True)
        self._content_container.setVisible(False)
        self._title_label.setVisible(False)

    def _init_by_status(self):
        # content
        if self.bot.state == barbot.State.mixing:

            # spinner
            label = QtWidgets.QLabel()
            movie = QtGui.QMovie(os.path.join(
                barbotgui.css_path(), "Blocks.gif"))
            label.setMovie(movie)
            movie.start()
            self._content_container.layout().addWidget(label)

            # progressbar
            self._progress_bar = QtWidgets.QProgressBar()
            self._progress_bar.setMinimum(0)
            self._progress_bar.setMaximum(100)
            self._content_container.layout().addWidget(self._progress_bar)
            self._content_container.layout().setAlignment(
                self._progress_bar, QtCore.Qt.AlignCenter)

            # forward mixing progress changed
            self._mixing_progress_trigger.connect(
                lambda: self._progress_bar.setValue(int(self.bot.progress * 100)))
            self.bot.on_mixing_progress_changed = lambda: self._mixing_progress_trigger.emit()

            # buttons
            button = QtWidgets.QPushButton("Abbrechen")
            button.clicked.connect(lambda: self.bot.set_user_input(False))
            self._content_container.layout().addWidget(button)

            self._title_label.setText(
                "Cocktail\n'%s'\nwird gemischt." % self.bot.current_recipe.name)

        elif self.bot.state == barbot.State.cleaning:
            self._title_label.setText("Reinigung")
        elif self.bot.state == barbot.State.connecting:
            self._title_label.setText("Stelle Verbindung her")
        elif self.bot.state == barbot.State.searching:
            self._title_label.setText("Suche nach BarBots in der Nähe")
        elif self.bot.state == barbot.State.cleaning_cycle:
            self._title_label.setText("Reinigung (Zyklus)")
        elif self.bot.state == barbot.State.single_ingredient:
            self._title_label.setText("Dein Nachschlag wird hinzugefügt")
        elif self.bot.state == barbot.State.startup:
            self._title_label.setText("Starte BarBot, bitte warten")
        elif self.bot.state == barbot.State.crushing:
            self._title_label.setText("Eis wird hinzugefügt")
        else:
            self._title_label.setText("Unknown status: %s" % self.bot.state)


class IdleView(barbotgui.View):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self.navigation_items = [
            ["Liste", ListRecipes],
            ["Neu", RecipeNewOrEdit],
            ["Nachschlag", SingleIngredient],
            ["Statistik", Statistics],
        ]
        self.setLayout(QtWidgets.QVBoxLayout())
        barbotgui.set_no_spacing(self.layout())

        self.header = QtWidgets.QWidget()
        self.layout().addWidget(self.header)

        # navigation
        self.navigation = QtWidgets.QWidget()
        self.layout().addWidget(self.navigation)
        self.navigation.setLayout(QtWidgets.QHBoxLayout())

        for text, _class in self.navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(checked, c=_class): return self.window.set_view(
                c(self.window))
            button.clicked.connect(btn_click)
            self.navigation.layout().addWidget(button, 1)

        # content
        content_wrapper = QtWidgets.QWidget()
        self.layout().addWidget(content_wrapper, 1)
        content_wrapper.setLayout(QtWidgets.QGridLayout())
        barbotgui.set_no_spacing(content_wrapper.layout())

        # fixed content
        self._fixed_content = QtWidgets.QWidget()
        content_wrapper.layout().addWidget(self._fixed_content)

        scroller = QtWidgets.QScrollArea()
        scroller.setProperty("class", "ContentScroller")
        scroller.setWidgetResizable(True)
        scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        content_wrapper.layout().addWidget(scroller)

        QtWidgets.QScroller.grabGesture(
            scroller.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture
        )

        self._content = QtWidgets.QWidget()
        self._content.setProperty("class", "IdleContent")
        scroller.setWidget(self._content)


class ListRecipes(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
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
                    filling = barbotgui.GlasFilling(item.color, relative, )
                    fillings.append(filling)
            indicator = barbotgui.GlasIndicator(fillings)
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
    def __init__(self, window: barbotgui.MainWindow, recipe_id=None):
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

    def __init__(self, window: barbotgui.MainWindow):
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

    def __init__(self, window: barbotgui.MainWindow):
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
        chart = barbotgui.plot.BarChart(data)
        container.layout().addWidget(chart)

        # total liters
        total_amount = sum([amount["liters"] for amount in ingredients_amount])
        label = QtWidgets.QLabel("Verbrauchte Zutaten (%i l)" % total_amount)
        container.layout().addWidget(label)
        # ingrediends
        data = [(c["ingredient"], c["liters"])
                for c in reversed(ingredients_amount)]
        chart = barbotgui.plot.BarChart(data)
        container.layout().addWidget(chart)

        # label
        label = QtWidgets.QLabel("Bestellungen")
        container.layout().addWidget(label)
        # cocktails vs. time chart
        data = [(c["hour"], c["count"]) for c in reversed(cocktails_by_time)]
        chart = barbotgui.plot.BarChart(data)
        container.layout().addWidget(chart)

        # set content
        if self.content is not None:
            # setting the parent of the previos content to None will destroy it
            self.content.setParent(None)
        self.content = container
        self._content_wrapper.layout().addWidget(container)


class AdminLogin(IdleView):
    _entered_password = ""

    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("Admin Login")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # edit
        self.password_widget = QtWidgets.QLabel()
        self.password_widget.setProperty("class", "PasswordBox")
        self.password_widget.setText(" ")
        self._content.layout().addWidget(self.password_widget)

        # numpad
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        self._content.layout().setAlignment(numpad, QtCore.Qt.AlignCenter)
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.setProperty("class", "NumpadButton")
                button.clicked.connect(
                    lambda checked, value=num: self.numpad_button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # clear
        button = QtWidgets.QPushButton("Clear")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.clear_password())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.numpad_button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("Enter")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.check_password())
        numpad.layout().addWidget(button, 3, 2)

        self._content.layout().addWidget(numpad, 1)
        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _update(self):
        self.password_widget.setText(
            "".join("*" for letter in self._entered_password))

    def numpad_button_clicked(self, value):
        self._entered_password = self._entered_password + str(value)
        self._update()

    def clear_password(self):
        self._entered_password = ""
        self._update()

    def check_password(self):
        if self._entered_password == self.bot.config.admin_password:
            self.window.is_admin = True
            self.window.set_view(AdminOverview(self.window))
        self.clear_password()


class AdminOverview(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QVBoxLayout())

        # title
        title = QtWidgets.QLabel("Übersicht")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # admin navigation
        self.admin_navigation = QtWidgets.QWidget()
        self.admin_navigation.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(self.admin_navigation)

        admin_navigation_items = [
            ["Positionen", Ports],
            ["Reinigung", Cleaning],
            ["System", System],
            ["Löschen", RemoveRecipe],
            ["Kalibrierung", BalanceCalibration],
            ["Einstellungen", Settings]
        ]
        for text, _class in admin_navigation_items:
            button = QtWidgets.QPushButton(text)
            def btn_click(checked, c=_class): return self.window.set_view(
                c(self.window))
            button.clicked.connect(btn_click)
            self.admin_navigation.layout().addWidget(button, 1)

        # table
        table = QtWidgets.QWidget()
        table.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(table)

        # fill table
        ingredients = self.db.list_ingredients(True)
        ports = self.db.ingredient_of_port()
        for i in range(12):
            label = QtWidgets.QLabel("Position %i" % (i+1))
            table.layout().addWidget(label, i, 0)
            if i in ports.keys() and ports[i] in ingredients.keys():
                ingredient = ingredients[ports[i]]
                label = QtWidgets.QLabel(ingredient["name"])
                table.layout().addWidget(label, i, 1)
                label = QtWidgets.QLabel(str(ingredient["calibration"]))
                table.layout().addWidget(label, i, 2)
                # calibrate button
                button = QtWidgets.QPushButton(
                    barbotgui.qt_icon_from_file_name("calibrate.png"), "")
                button.clicked.connect(
                    lambda checked, portId=i: self._open_ingredient_calibration(portId))
                table.layout().addWidget(button, i, 3, QtCore.Qt.AlignLeft)

        # weight label
        self._weight_label = QtWidgets.QLabel()
        self._content.layout().addWidget(self._weight_label)

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

        self._update_weight()

        self._update_timer = QtCore.QTimer(self)
        self._update_timer.timeout.connect(self._update_weight)
        self._update_timer.start(500)

    def _open_ingredient_calibration(self, id):
        self.window.set_view(IngredientCalibration(self.window, id))

    def _update_weight(self):
        res = self.window.bot.get_weight()
        weight = res if res is not None else "-"
        text = "Gewicht: {} g".format(weight)
        self._weight_label.setText(text)


class Ports(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Positionen")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(AdminOverview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # table
        table = QtWidgets.QWidget()
        table.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(table)
        # fill table
        ports = self.db.ingredient_of_port()
        self._ingredient_widgets = dict()
        for i in range(12):
            label = QtWidgets.QLabel("Position %i" % (i+1))
            table.layout().addWidget(label, i, 0)
            selectedPort = ports[i] if i in ports.keys() else 0
            cbPort = self.window.combobox_ingredients(selectedPort)
            self._ingredient_widgets[i] = cbPort
            table.layout().addWidget(cbPort, i, 1)

        # save button
        button = QtWidgets.QPushButton("Speichern")
        button.clicked.connect(lambda: self._save())
        self._content.layout().addWidget(button)
        self._content.layout().setAlignment(button, QtCore.Qt.AlignCenter)

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _save(self):
        ports = dict()
        for port, cb in self._ingredient_widgets.items():
            ingredient = cb.currentData()
            if ingredient not in ports.values():
                ports[port] = ingredient
            else:
                self.window.show_message(
                    "Jede Zutat darf nur einer\nPosition zugewiesen werden!")
                return
        self.window.show_message("Positionen wurden gespeichert.")
        self.db.update_ports(ports)


class IngredientCalibration(IdleView):
    def __init__(self, window: barbotgui.MainWindow, portId=-1):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        self._fixed_content.layout().addWidget(QtWidgets.QLabel("Zutat kalibrieren"))

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(AdminOverview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)


class BalanceCalibration(IdleView):
    _tare_and_calibrate = False
    _entered_weight = 0

    def __init__(self, window: barbotgui.MainWindow, portId=-1):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Kalibrierung")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(AdminOverview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # normal buttons to be shown in the beginning
        self._add_calibration_buttons()

        # dialog to remove glas
        self._add_dialog_remove_glas()

        # dialog to enter the weight on the platform
        self._add_dialog_enter_weight()

        self._show_calibration_buttons()

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _add_dialog_remove_glas(self):
        self._dialog_remove_glas = QtWidgets.QWidget()
        self._dialog_remove_glas.setLayout(QtWidgets.QGridLayout())
        self._dialog_remove_glas.setVisible(False)
        self._content.layout().addWidget(self._dialog_remove_glas, 1)

        center_box = QtWidgets.QFrame()
        center_box.setLayout(QtWidgets.QVBoxLayout())
        self._dialog_remove_glas.layout().addWidget(
            center_box, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel("Bitte alles von der Platform entfernen.")
        center_box.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        center_box.layout().addWidget(row)

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(lambda: self._tare())
        row.layout().addWidget(ok_button)

        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(lambda: self._show_calibration_buttons())
        row.layout().addWidget(cancel_button)

    def _add_dialog_enter_weight(self):
        self._dialog_enter_weight = QtWidgets.QWidget()
        self._dialog_enter_weight.setLayout(QtWidgets.QGridLayout())
        self._dialog_enter_weight.setVisible(False)
        self._content.layout().addWidget(self._dialog_enter_weight, 1)

        center_box = QtWidgets.QFrame()
        center_box.setLayout(QtWidgets.QVBoxLayout())
        self._dialog_enter_weight.layout().addWidget(
            center_box, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel(
            "Bitte aktuelles Gewicht\nauf der Platorm angeben.")
        center_box.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        center_box.layout().addWidget(row)

        # edit
        self.weight_widget = QtWidgets.QLabel()
        center_box.layout().addWidget(self.weight_widget)

        # numpad
        numpad = QtWidgets.QWidget()
        numpad.setLayout(QtWidgets.QGridLayout())
        for y in range(0, 3):
            for x in range(0, 3):
                num = y * 3 + x + 1
                button = QtWidgets.QPushButton(str(num))
                button.setProperty("class", "NumpadButton")
                button.clicked.connect(
                    lambda checked, value=num: self.numpad_button_clicked(value))
                numpad.layout().addWidget(button, y, x)
        # cancel
        button = QtWidgets.QPushButton("Abbrechen")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(
            lambda checked: self._show_calibration_buttons())
        numpad.layout().addWidget(button, 3, 0)
        # zero
        button = QtWidgets.QPushButton("0")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self.numpad_button_clicked(0))
        numpad.layout().addWidget(button, 3, 1)
        # enter
        button = QtWidgets.QPushButton("OK")
        button.setProperty("class", "NumpadButton")
        button.clicked.connect(lambda checked: self._calibrate())
        numpad.layout().addWidget(button, 3, 2)

        center_box.layout().addWidget(numpad)

    def _update_weight(self):
        self.weight_widget.setText(str(self._entered_weight))

    def numpad_button_clicked(self, value):
        self._entered_weight = self._entered_weight * 10 + value
        self._update_weight()

    def _add_calibration_buttons(self):
        self._calibration_buttons = QtWidgets.QWidget()
        self._calibration_buttons.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(self._calibration_buttons, 1)

        # Tare
        button = QtWidgets.QPushButton("Tara")
        button.clicked.connect(lambda: self._start_calibration(False))
        self._calibration_buttons.layout().addWidget(button)

        # Calibrate
        button = QtWidgets.QPushButton("Kalibrieren")
        button.clicked.connect(lambda: self._start_calibration(True))
        self._calibration_buttons.layout().addWidget(button)

    def _tare(self):
        self.tare_weight = self.bot.get_weight()
        self.new_offset = self.bot.config.balance_offset + \
            self.tare_weight * self.bot.config.balance_calibration
        if self._tare_and_calibrate:
            # continue with clibration
            self._show_dialog_enter_weight()
        else:
            # tare only: set offset, keep calibration
            self.bot.set_balance_calibration(
                self.new_offset, self.bot.balance_calibration)
            self._show_calibration_buttons()

    def _calibrate(self):
        if self._entered_weight > 0:
            self.balance_calibration = (self.bot.get_weight(
            )-self.tare_weight) * self.bot.config.balance_calibration/self._entered_weight
            self.bot.config.set_balance_calibration(
                self.new_offset, self.balance_calibration)
        self._show_calibration_buttons()

    def _start_calibration(self, tare_and_calibrate):
        self._tare_and_calibrate = tare_and_calibrate
        self._show_dialog_remove_glas()

    def _show_dialog_remove_glas(self):
        self._calibration_buttons.setVisible(False)
        self._dialog_remove_glas.setVisible(True)
        self._dialog_enter_weight.setVisible(False)

    def _show_calibration_buttons(self):
        self._dialog_remove_glas.setVisible(False)
        self._calibration_buttons.setVisible(True)
        self._dialog_enter_weight.setVisible(False)

    def _show_dialog_enter_weight(self):
        self._entered_weight = 0
        self.update()
        self._dialog_remove_glas.setVisible(False)
        self._calibration_buttons.setVisible(False)
        self._dialog_enter_weight.setVisible(True)


class Cleaning(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())
        self.amount = 50
        # assume calibration value of water
        self.calibration = 1000

        # title
        title = QtWidgets.QLabel("Reinigung")
        title.setProperty("class", "Headline")
        self._content.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(AdminOverview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # clean left
        button = QtWidgets.QPushButton("Reinigen linke Hälfte")
        button.clicked.connect(lambda: self._clean_left())
        self._content.layout().addWidget(button)

        # clean right
        button = QtWidgets.QPushButton("Reinigen rechte Hälfte")
        button.clicked.connect(lambda: self._clean_right())
        self._content.layout().addWidget(button)

        # grid
        grid = QtWidgets.QWidget()
        grid.setLayout(QtWidgets.QGridLayout())
        self._content.layout().addWidget(grid)
        # fill with buttons
        for column in range(6):
            for row in range(2):
                port = row * 6 + column
                button = QtWidgets.QPushButton(str(port + 1))
                button.clicked.connect(
                    lambda checked, pid=port: self._clean_single(pid))
                grid.layout().addWidget(button, row, column)

        # dummy
        self._content.layout().addWidget(QtWidgets.QWidget(), 1)

    def _clean_left(self):
        data = range(0, 6)
        self.bot.start_cleaning_cycle(data)

    def _clean_right(self):
        data = range(6, 12)
        self.bot.start_cleaning_cycle(data)

    def _clean_single(self, port):
        self.bot.start_cleaning(port)


class Settings(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Einstellungen")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(AdminOverview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # clean left
        button = QtWidgets.QPushButton("Reinigen linke Hälfte")
        button.clicked.connect(lambda: self._clean_left())
        self._content.layout().addWidget(button)


class System(IdleView):
    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("System")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(AdminOverview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # add actual content
        self.window.add_system_view(self._content)


class RemoveRecipe(IdleView):
    _list = None

    def __init__(self, window: barbotgui.MainWindow):
        super().__init__(window)
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._fixed_content.setLayout(QtWidgets.QHBoxLayout())

        # title
        title = QtWidgets.QLabel("Positionen")
        title.setProperty("class", "Headline")
        self._fixed_content.layout().setAlignment(title, QtCore.Qt.AlignTop)
        self._fixed_content.layout().addWidget(title)

        # back button
        back_button = QtWidgets.QPushButton("Übersicht")
        def btn_click(): return self.window.set_view(AdminOverview(self.window))
        back_button.clicked.connect(btn_click)
        self._fixed_content.layout().addWidget(back_button)

        # confirmationDialog
        self._add_confirmation_dialog()
        # list
        self.add_list()

    def _add_confirmation_dialog(self):
        self._confirmation_dialog = QtWidgets.QWidget()
        self._confirmation_dialog.setLayout(QtWidgets.QGridLayout())
        self._confirmation_dialog.setVisible(False)
        self._content.layout().addWidget(self._confirmation_dialog, 1)

        center_box = QtWidgets.QFrame()
        center_box.setLayout(QtWidgets.QVBoxLayout())
        self._confirmation_dialog.layout().addWidget(
            center_box, 0, 0, QtCore.Qt.AlignCenter)

        label = QtWidgets.QLabel("Wirklich löschen?")
        center_box.layout().addWidget(label)

        row = QtWidgets.QWidget()
        row.setLayout(QtWidgets.QHBoxLayout())
        center_box.layout().addWidget(row)

        ok_button = QtWidgets.QPushButton("Löschen")
        ok_button.clicked.connect(lambda: self._remove())
        row.layout().addWidget(ok_button)

        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(lambda: self._hide_confirmation())
        row.layout().addWidget(cancel_button)

    def add_list(self):
        if self._list is not None:
            self._list.setParent(None)

        self._list = QtWidgets.QWidget()
        self._list.setLayout(QtWidgets.QVBoxLayout())
        self._content.layout().addWidget(self._list, 1)

        recipes = self.db.list_recipes(self.window.recipe_filter)
        for recipe in recipes:
            # box to hold the recipe
            recipe_box = QtWidgets.QWidget()
            recipe_box.setLayout(QtWidgets.QHBoxLayout())
            self._list.layout().addWidget(recipe_box)

            # title
            recipe_title = QtWidgets.QLabel(recipe.name)
            recipe_title.setProperty("class", "RecipeTitle")
            recipe_box.layout().addWidget(recipe_title, 1)

            # remove button
            icon = barbotgui.qt_icon_from_file_name("remove.png")
            remove_button = QtWidgets.QPushButton(icon, "")
            remove_button.clicked.connect(
                lambda checked, rid=recipe.id: self._show_confirmation(rid))
            recipe_box.layout().addWidget(remove_button, 0)

    def _show_confirmation(self, id):
        self._id = id
        self._list.setVisible(False)
        self._confirmation_dialog.setVisible(True)

    def _hide_confirmation(self):
        self._confirmation_dialog.setVisible(False)
        self._list.setVisible(True)

    def _remove(self):
        self.db.remove_recipe(self._id)
        self.add_list()
