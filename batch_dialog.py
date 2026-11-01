from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QDoubleSpinBox, QPushButton, QLabel, QGroupBox,
)


FIELD_OPTIONS = [
    ("Kaffee-Menge (g)", "Ingredients.Coffee.CoffeeAmountsGrams[0]"),
    ("Kaffee-Wasser (ml)", "Ingredients.Coffee.TotalAmountMilliliters"),
    ("Vorbrühen (ml)", "Ingredients.Coffee.PreBrewMilliliters"),
    ("Nachpressen (mm)", "Ingredients.Coffee.PostPressMillimeters"),
    ("Press-Faktor", "Ingredients.Coffee.PressFactor"),
    ("Relax-Zeit (s)", "Ingredients.Coffee.RelaxTimeSeconds"),
    ("Max. Extraktion (s)", "Ingredients.Coffee.MaxExtractionTimeSeconds"),
    ("Mahlwerk (0/1)", "Ingredients.Coffee.GrinderIndices[0]"),
    ("Milch-Flüssig (s)", "Ingredients.Milk.ProductDurationsSeconds[0]"),
    ("Milch-Schaum (s)", "Ingredients.Milk.ProductDurationsSeconds[1]"),
    ("Milch-Temperatur (°C)", "Ingredients.Milk.Temperatures[0]"),
    ("Milch-Luft", "Ingredients.Milk.AirAmounts[1]"),
    ("Wasser-Menge (ml)", "Ingredients.Water.AmountMilliliters"),
    ("Preis (€)", "PaymentInfo.Price"),
    ("Artikel-Nr.", "PaymentInfo.ArticleNo"),
]

OPERATORS = [
    ("Setzen (=)", "set"),
    ("Zusammenfügen (+)", "add"),
    ("Subtrahieren (−)", "sub"),
    ("Multiplizieren (×)", "mul"),
]


class BatchDialog(QDialog):
    """Dialog für Batch-Operationen auf mehreren Rezepten."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch-Operation")
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Feld wählen:"))
        self.field_combo = QComboBox()
        for label, _ in FIELD_OPTIONS:
            self.field_combo.addItem(label)
        layout.addWidget(self.field_combo)

        layout.addWidget(QLabel("Operation:"))
        self.op_combo = QComboBox()
        for label, _ in OPERATORS:
            self.op_combo.addItem(label)
        layout.addWidget(self.op_combo)

        layout.addWidget(QLabel("Wert:"))
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(-999, 999)
        self.value_spin.setSingleStep(0.5)
        self.value_spin.setDecimals(2)
        self.value_spin.setValue(0)
        layout.addWidget(self.value_spin)

        self.preview_label = QLabel("")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_ok = QPushButton("Anwenden")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def get_operation(self) -> tuple[str, str, float]:
        """Gibt (field_path, operator, value) zurück."""
        field_path = FIELD_OPTIONS[self.field_combo.currentIndex()][1]
        op = OPERATORS[self.op_combo.currentIndex()][1]
        val = self.value_spin.value()
        return field_path, op, val
