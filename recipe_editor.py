from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QCheckBox, QPushButton, QTabWidget, QMessageBox, QGridLayout,
)
from PySide6.QtCore import Qt


class RecipeEditor(QDialog):
    """Dialog zum Bearbeiten eines einzelnen Thermoplan-Rezepts."""

    def __init__(self, recipe: dict, parent=None):
        super().__init__(parent)
        self.recipe = recipe
        self.setWindowTitle(f"Rezept bearbeiten: {recipe.get('Name', '')}")
        self.resize(700, 650)

        layout = QVBoxLayout(self)

        # ─── Basis-Info ───────────────────────────────────────────────
        base_group = QGroupBox("Basis")
        base_form = QFormLayout()
        self.name_edit = QLineEdit(recipe.get("Name", ""))
        self.category_edit = QLineEdit(recipe.get("Category", ""))
        self.id_edit = QLineEdit(recipe.get("ID", ""))
        self.cup_combo = QComboBox()
        self.cup_combo.addItems(["cup0 (Small)", "cup1 (Medium)", "cup2 (Large)"])
        self.cup_combo.setCurrentIndex(
            ["cup0", "cup1", "cup2"].index(recipe.get("CupType", "cup0"))
        )
        self.icon_edit = QLineEdit(recipe.get("IconPath", ""))

        base_form.addRow("Name:", self.name_edit)
        base_form.addRow("Kategorie:", self.category_edit)
        base_form.addRow("ID:", self.id_edit)
        base_form.addRow("Tasse:", self.cup_combo)
        base_form.addRow("Icon:", self.icon_edit)
        base_group.setLayout(base_form)
        layout.addWidget(base_group)

        # ─── Tabs für Zutaten ─────────────────────────────────────────
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_coffee_tab(), "Kaffee")
        self.tabs.addTab(self._build_milk_tab(), "Milch")
        self.tabs.addTab(self._build_water_tab(), "Wasser")
        self.tabs.addTab(self._build_misc_tab(), "Sonstiges")

        # ─── Buttons ──────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_save = QPushButton("Speichern")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    # ─── Kaffee-Tab ───────────────────────────────────────────────────
    def _build_coffee_tab(self):
        w = self._make_scrollable()
        form = QFormLayout()

        ing = self.recipe.get("Ingredients", {})
        coffee = ing.get("Coffee", {})

        self.coffee_active = QCheckBox("Kaffee aktiv")
        self.coffee_active.setChecked("Coffee" in ing)
        form.addRow(self.coffee_active)

        self.coffee_grams = self._dspin(0, 50, 0.5, coffee.get("CoffeeAmountsGrams", [0])[0])
        form.addRow("Kaffee (g):", self.coffee_grams)

        self.coffee_water = self._dspin(0, 500, 5, coffee.get("TotalAmountMilliliters", 0))
        form.addRow("Wasser (ml):", self.coffee_water)

        self.grinder_combo = QComboBox()
        self.grinder_combo.addItems(["Mahlwerk 1 (Links)", "Mahlwerk 2 (Rechts)"])
        idx = coffee.get("GrinderIndices", [0])[0]
        self.grinder_combo.setCurrentIndex(idx if idx in (0, 1) else 0)
        form.addRow("Mahlwerk:", self.grinder_combo)

        self.pre_brew = self._dspin(0, 50, 0.5, coffee.get("PreBrewMilliliters", 0))
        form.addRow("Vorbrühen (ml):", self.pre_brew)

        self.post_press = self._dspin(0, 10, 0.5, coffee.get("PostPressMillimeters", 0))
        form.addRow("Nachpressen (mm):", self.post_press)

        self.press_factor = self._dspin(0.5, 2.0, 0.01, coffee.get("PressFactor", 1.0))
        form.addRow("Press-Faktor:", self.press_factor)

        self.relax_time = self._dspin(0, 30, 0.1, coffee.get("RelaxTimeSeconds", 0))
        form.addRow("Relax-Zeit (s):", self.relax_time)

        self.max_extract = self._dspin(-1, 120, 0.5, coffee.get("MaxExtractionTimeSeconds", -1))
        form.addRow("Max. Extraktion (s):", self.max_extract)

        self.num_cycles = QSpinBox()
        self.num_cycles.setRange(1, 4)
        self.num_cycles.setValue(coffee.get("NumBrewCycles", 1))
        form.addRow("Brühzyklen:", self.num_cycles)

        self.use_expansion = QCheckBox("Expansionskammer")
        self.use_expansion.setChecked(coffee.get("UseExpansionChamber", False))
        form.addRow(self.use_expansion)

        self.use_isq = QCheckBox("ISQ nutzen")
        self.use_isq.setChecked(coffee.get("UseForISQ", False))
        form.addRow(self.use_isq)

        w.layout().addLayout(form)
        w.layout().addStretch()
        return w

    # ─── Milch-Tab ────────────────────────────────────────────────────
    def _build_milk_tab(self):
        w = self._make_scrollable()
        form = QFormLayout()

        ing = self.recipe.get("Ingredients", {})
        milk = ing.get("Milk", {})

        self.milk_active = QCheckBox("Milch aktiv")
        self.milk_active.setChecked("Milk" in ing)
        form.addRow(self.milk_active)

        self.milk_liq = self._dspin(0, 120, 0.5, milk.get("ProductDurationsSeconds", [0, 0])[0])
        form.addRow("Flüssig (s):", self.milk_liq)

        self.milk_foam = self._dspin(0, 120, 0.5, milk.get("ProductDurationsSeconds", [0, 0])[1])
        form.addRow("Schaum (s):", self.milk_foam)

        self.milk_temp = self._dspin(40, 90, 0.5, milk.get("Temperatures", [70, 70])[0])
        form.addRow("Temperatur (°C):", self.milk_temp)

        self.milk_air = self._dspin(0, 10, 0.1, milk.get("AirAmounts", [0, 1])[1])
        form.addRow("Luft (Schaum):", self.milk_air)

        self.milk_pure_foam = QCheckBox("Reiner Schaum (Pure Foam)")
        self.milk_pure_foam.setChecked(milk.get("PureFoam", False))
        form.addRow(self.milk_pure_foam)

        self.milk_module_combo = QComboBox()
        self.milk_module_combo.addItems(["MilkModule", "MilkModule2"])
        self.milk_module_combo.setCurrentText(milk.get("Module", "MilkModule"))
        form.addRow("Modul:", self.milk_module_combo)

        # Latte Macchiato Wait Time
        self.lm_wait_valid = QCheckBox("Wartezeit aktiv")
        self.lm_wait_valid.setChecked(milk.get("LatteMacchiatoWaitTimeIsValid", False))
        form.addRow(self.lm_wait_valid)

        self.lm_wait_sec = self._dspin(0, 30, 0.5, milk.get("LatteMacchiatoWaitTimeSec", 0))
        form.addRow("Wartezeit (s):", self.lm_wait_sec)

        w.layout().addLayout(form)
        w.layout().addStretch()
        return w

    # ─── Wasser-Tab ───────────────────────────────────────────────────
    def _build_water_tab(self):
        w = self._make_scrollable()
        form = QFormLayout()

        ing = self.recipe.get("Ingredients", {})
        water = ing.get("Water", {})

        self.water_active = QCheckBox("Wasser aktiv")
        self.water_active.setChecked("Water" in ing)
        form.addRow(self.water_active)

        self.water_amount = self._dspin(0, 1000, 10, water.get("AmountMilliliters", 0))
        form.addRow("Menge (ml):", self.water_amount)

        self.water_module_combo = QComboBox()
        self.water_module_combo.addItems(["TeaModule", "WaterModule"])
        self.water_module_combo.setCurrentText(water.get("Module", "TeaModule"))
        form.addRow("Modul:", self.water_module_combo)

        w.layout().addLayout(form)
        w.layout().addStretch()
        return w

    # ─── Sonstiges-Tab ────────────────────────────────────────────────
    def _build_misc_tab(self):
        w = self._make_scrollable()
        form = QFormLayout()

        ing = self.recipe.get("Ingredients", {})

        # AutoOutlet
        outlet = ing.get("AutoOutletMove", {})
        self.outlet_active = QCheckBox("Auto-Auslauf aktiv")
        self.outlet_active.setChecked("AutoOutletMove" in ing)
        form.addRow(self.outlet_active)

        self.outlet_height = QSpinBox()
        self.outlet_height.setRange(0, 200)
        self.outlet_height.setValue(outlet.get("CupHeightMillimeters", 0))
        form.addRow("Tassenhöhe (mm):", self.outlet_height)

        # Rinse
        rinse = ing.get("IngredientParametersRinseCoffeeModule", {})
        self.rinse_active = QCheckBox("Spülen aktiv")
        self.rinse_active.setChecked("IngredientParametersRinseCoffeeModule" in ing)
        form.addRow(self.rinse_active)

        self.rinse_mode_combo = QComboBox()
        self.rinse_mode_combo.addItems(["PreHeat", "Full", "None"])
        self.rinse_mode_combo.setCurrentText(rinse.get("RinseMode", "PreHeat"))
        form.addRow("Spül-Modus:", self.rinse_mode_combo)

        # Payment
        payment = self.recipe.get("PaymentInfo", {})
        self.article_no = QSpinBox()
        self.article_no.setRange(0, 999)
        self.article_no.setValue(payment.get("ArticleNo", 0))
        form.addRow("Artikel-Nr.:", self.article_no)

        self.price = self._dspin(0, 99, 0.05, payment.get("Price", 0))
        form.addRow("Preis (€):", self.price)

        # Adjustments
        adj = self.recipe.get("Adjustments", {})
        form.addRow(QLabel("<b>Adjustments (Skalierung)</b>"))
        self.adj_coffee = self._dspin(0.5, 1.5, 0.05, adj.get("CoffeeAmountAdjustment", 1.0))
        form.addRow("Kaffee-Menge:", self.adj_coffee)
        self.adj_coffee_water = self._dspin(0.5, 1.5, 0.05, adj.get("CoffeeWaterAdjustment", 1.0))
        form.addRow("Kaffee-Wasser:", self.adj_coffee_water)
        self.adj_milk = self._dspin(0.5, 1.5, 0.05, adj.get("MilkAmountAdjustment", 1.0))
        form.addRow("Milch-Menge:", self.adj_milk)
        self.adj_milk_foam = self._dspin(0.5, 1.5, 0.05, adj.get("MilkFoamAdjustment", 1.0))
        form.addRow("Milch-Schaum:", self.adj_milk_foam)
        self.adj_milk_dur = self._dspin(0.5, 1.5, 0.05, adj.get("MilkProductDurationAdjustment", 1.0))
        form.addRow("Milch-Dauer:", self.adj_milk_dur)
        self.adj_water = self._dspin(0.5, 1.5, 0.05, adj.get("WaterAmountAdjustment", 1.0))
        form.addRow("Wasser-Menge:", self.adj_water)

        w.layout().addLayout(form)
        w.layout().addStretch()
        return w

    # ─── Save ─────────────────────────────────────────────────────────
    def _save(self):
        r = self.recipe

        # Basis
        r["Name"] = self.name_edit.text()
        r["Category"] = self.category_edit.text()
        r["ID"] = self.id_edit.text()
        r["CupType"] = ["cup0", "cup1", "cup2"][self.cup_combo.currentIndex()]
        r["IconPath"] = self.icon_edit.text()

        ing = r.setdefault("Ingredients", {})

        # Coffee
        if self.coffee_active.isChecked():
            ing["Coffee"] = {
                **ing.get("Coffee", {}),
                "CoffeeAmountsGrams": [self.coffee_grams.value()],
                "GrinderIndices": [self.grinder_combo.currentIndex()],
                "TotalAmountMilliliters": self.coffee_water.value(),
                "PreBrewMilliliters": self.pre_brew.value(),
                "PostPressMillimeters": self.post_press.value(),
                "PressFactor": self.press_factor.value(),
                "RelaxTimeSeconds": self.relax_time.value(),
                "MaxExtractionTimeSeconds": self.max_extract.value(),
                "NumBrewCycles": self.num_cycles.value(),
                "UseExpansionChamber": self.use_expansion.isChecked(),
                "UseForISQ": self.use_isq.isChecked(),
                "Type": "IngredientParametersCoffee",
            }
        else:
            ing.pop("Coffee", None)

        # Milk
        if self.milk_active.isChecked():
            ing["Milk"] = {
                **ing.get("Milk", {}),
                "ProductDurationsSeconds": [self.milk_liq.value(), self.milk_foam.value()],
                "Temperatures": [self.milk_temp.value(), self.milk_temp.value()],
                "AirAmounts": [0.0, self.milk_air.value()],
                "PureFoam": self.milk_pure_foam.isChecked(),
                "Module": self.milk_module_combo.currentText(),
                "Type": "IngredientParametersMilk",
            }
            if self.lm_wait_valid.isChecked():
                ing["Milk"]["LatteMacchiatoWaitTimeIsValid"] = True
                ing["Milk"]["LatteMacchiatoWaitTimeSec"] = self.lm_wait_sec.value()
            else:
                ing["Milk"].pop("LatteMacchiatoWaitTimeIsValid", None)
                ing["Milk"].pop("LatteMacchiatoWaitTimeSec", None)
        else:
            ing.pop("Milk", None)

        # Water
        if self.water_active.isChecked():
            ing["Water"] = {
                "AmountMilliliters": self.water_amount.value(),
                "Module": self.water_module_combo.currentText(),
                "TargetTemperatureDegreesCelsius": -1.0,
                "Type": "IngredientParametersAmount",
            }
        else:
            ing.pop("Water", None)

        # AutoOutlet
        if self.outlet_active.isChecked():
            ing["AutoOutletMove"] = {
                "CupHeightMillimeters": self.outlet_height.value(),
                "CupIdentifier": r["CupType"],
                "Module": "AutoOutlet",
                "Type": "IngredientParametersAutoOutlet",
            }
        else:
            ing.pop("AutoOutletMove", None)

        # Rinse
        if self.rinse_active.isChecked():
            ing["IngredientParametersRinseCoffeeModule"] = {
                "Module": "CoffeeModule",
                "RinseMode": self.rinse_mode_combo.currentText(),
                "Type": "IngredientParametersRinse",
            }
        else:
            ing.pop("IngredientParametersRinseCoffeeModule", None)

        # Payment
        r["PaymentInfo"] = {
            "ArticleNo": self.article_no.value(),
            "Price": self.price.value(),
        }

        # Adjustments
        r["Adjustments"] = {
            "CoffeeAmountAdjustment": self.adj_coffee.value(),
            "CoffeeWaterAdjustment": self.adj_coffee_water.value(),
            "MilkAmountAdjustment": self.adj_milk.value(),
            "MilkFoamAdjustment": self.adj_milk_foam.value(),
            "MilkProductDurationAdjustment": self.adj_milk_dur.value(),
            "WaterAmountAdjustment": self.adj_water.value(),
        }

        self.accept()

    # ─── Helpers ──────────────────────────────────────────────────────
    def _dspin(self, lo: float, hi: float, step: float, val: float) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setSingleStep(step)
        s.setDecimals(2 if step < 0.1 else 1)
        s.setValue(val)
        return s

    def _make_scrollable(self):
        from PySide6.QtWidgets import QScrollArea
        from PySide6.QtCore import Qt
        area = QScrollArea()
        area.setWidgetResizable(True)
        inner = QWidget()
        area.setWidget(inner)
        from PySide6.QtWidgets import QVBoxLayout
        inner.setLayout(QVBoxLayout())
        return area
