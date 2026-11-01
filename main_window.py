import json
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QFileDialog, QVBoxLayout, QWidget, QLabel,
    QMessageBox, QComboBox, QSpinBox, QFormLayout, QGroupBox,
    QHeaderView, QAbstractItemView, QSplitter, QListWidget,
    QListWidgetItem, QHBoxLayout, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

import thermoplan_io
from variant_engine import generate_variants, VariantConfig
from models import PROFILES, SIZE_LABELS
from ui.recipe_editor import RecipeEditor
from ui.view_editor import ViewEditor
from ui.batch_dialog import BatchDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermoplan Menu Builder – BW4C / BW4")
        self.resize(1200, 800)

        # State
        self.products: list[dict] = []
        self.views: list[dict] = []
        self.settings: dict = {}
        self.serial_number: str = ""

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Maschine:"))
        self.machine_combo = QComboBox()
        self.machine_combo.addItems(list(PROFILES.keys()))
        top_bar.addWidget(self.machine_combo)
        top_bar.addSpacing(20)
        top_bar.addWidget(QLabel("Serial:"))
        self.serial_spin = QSpinBox()
        self.serial_spin.setRange(0, 999999999)
        self.serial_spin.setValue(200147531)
        top_bar.addWidget(self.serial_spin)
        top_bar.addSpacing(20)
        btn_import = QPushButton("📂 Paket Importieren")
        btn_import.clicked.connect(self.import_package)
        top_bar.addWidget(btn_import)
        btn_export = QPushButton("💾 Paket Exportieren")
        btn_export.clicked.connect(self.export_package)
        top_bar.addWidget(btn_export)
        layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Rezepte
        self.products_table = self._build_products_table()
        self.tabs.addTab(self.products_table, "Rezepte")

        # Tab 2: Varianten
        self.tabs.addTab(self._build_variant_tab(), "Varianten generieren")

        # Tab 3: Views
        self.view_editor = ViewEditor()
        self.tabs.addTab(self.view_editor, "Views (Display)")

        # Tab 4: Settings
        self.tabs.addTab(self._build_settings_tab(), "Einstellungen")

    # ─── Products Table ───────────────────────────────────────────────
    def _build_products_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["ID", "Name", "Kategorie", "Kaffee (g)", "Wasser (ml)", "Milch (s)"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.itemDoubleClicked.connect(self._edit_recipe)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_context_menu)
        return table

    def _refresh_products_table(self):
        self.products_table.setRowCount(len(self.products))
        for row, p in enumerate(self.products):
            ing = p.get("Ingredients", {})
            coffee_g = ing.get("Coffee", {}).get("CoffeeAmountsGrams", [0])[0] if "Coffee" in ing else "–"
            water_ml = ing.get("Coffee", {}).get("TotalAmountMilliliters", "–") if "Coffee" in ing else \
                       ing.get("Water", {}).get("AmountMilliliters", "–")
            milk_s = ing.get("Milk", {}).get("ProductDurationsSeconds", ["–"]) if "Milk" in ing else "–"
            milk_str = f"{milk_s[0]}+{milk_s[1]}" if isinstance(milk_s, list) and len(milk_s) == 2 else milk_s

            values = [p["ID"], p["Name"], p.get("Category", ""), str(coffee_g), str(water_ml), str(milk_str)]
            for col, val in enumerate(values):
                self.products_table.setItem(row, col, QTableWidgetItem(str(val)))

    def _edit_recipe(self, item: QTableWidgetItem):
            row = item.row()
            recipe = self.products[row]
            editor = RecipeEditor(recipe, self)
            if editor.exec() == QDialog.Accepted:
                self._refresh_products_table()
                self.variant_base_combo.clear()
                self.variant_base_combo.addItems([p["Name"] for p in self.products])
    

    # ─── Variant Tab ──────────────────────────────────────────────────
    def _build_variant_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        layout.addWidget(QLabel("Basis-Rezept wählen:"))
        self.variant_base_combo = QComboBox()
        self.variant_base_combo.addItems([p["Name"] for p in self.products])
        layout.addWidget(self.variant_base_combo)

        # Size checkboxes
        size_group = QGroupBox("Größen")
        size_layout = QHBoxLayout()
        self.size_checks: dict[str, QCheckBox] = {}
        for size in ("cup0", "cup1", "cup2"):
            cb = QCheckBox(SIZE_LABELS[size])
            cb.setChecked(size == "cup1")
            self.size_checks[size] = cb
            size_layout.addWidget(cb)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # Milk
        milk_group = QGroupBox("Milch-Typ")
        milk_layout = QHBoxLayout()
        self.milk_checks: dict[str, QCheckBox] = {}
        for milk in ("Kuhmilch", "Oat", "Soja", "Reis"):
            cb = QCheckBox(milk)
            cb.setChecked(milk == "Kuhmilch")
            self.milk_checks[milk] = cb
            milk_layout.addWidget(cb)
        milk_group.setLayout(milk_layout)
        layout.addWidget(milk_group)

        # Portions
        port_group = QGroupBox("Portionen")
        port_layout = QHBoxLayout()
        self.portion_checks: dict[int, QCheckBox] = {}
        for p in (1, 2):
            cb = QCheckBox(f"{p}×" if p == 1 else "2× (Doppelt)")
            cb.setChecked(True)
            self.portion_checks[p] = cb
            port_layout.addWidget(cb)
        port_group.setLayout(port_layout)
        layout.addWidget(port_group)

        btn_gen = QPushButton("⚡ Varianten generieren")
        btn_gen.clicked.connect(self._generate_variants)
        layout.addWidget(btn_gen)

        self.variant_result_label = QLabel("")
        layout.addWidget(self.variant_result_label)
        layout.addStretch()
        return w

    def _generate_variants(self):
        if not self.products:
            QMessageBox.warning(self, "Fehler", "Keine Rezepte importiert.")
            return

        base_idx = self.variant_base_combo.currentIndex()
        base = self.products[base_idx]

        sizes = [s for s, cb in self.size_checks.items() if cb.isChecked()]
        milks = [m for m, cb in self.milk_checks.items() if cb.isChecked()]
        portions = [p for p, cb in self.portion_checks.items() if cb.isChecked()]

        if not sizes or not milks or not portions:
            QMessageBox.warning(self, "Fehler", "Mindestens je eine Größe, Milch und Portion wählen.")
            return

        config = VariantConfig(sizes=sizes, milk_types=milks, portions=portions)
        existing_ids = {p["ID"] for p in self.products}
        variants = generate_variants(base, config, existing_ids)

        # Add to products
        self.products.extend(variants)
        self._refresh_products_table()
        self.variant_result_label.setText(f"✅ {len(variants)} Varianten generiert und hinzugefügt.")

    # ─── Views Tab ────────────────────────────────────────────────────
    def _build_views_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Views (Display-Anordnung) – in Arbeit!"))
        layout.addStretch()
        return w

    # ─── Settings Tab ─────────────────────────────────────────────────
    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        form = QFormLayout()
        form.addRow(QLabel("<b>CupTypes</b>"))
        self.cup_types_label = QLabel(str(self.settings.get("CupTypes", "–")))
        form.addRow(self.cup_types_label)

        form.addRow(QLabel("<b>GrinderTypes</b>"))
        self.grinder_label = QLabel(str(self.settings.get("GrinderTypes", "–")))
        form.addRow(self.grinder_label)

        form.addRow(QLabel("<b>ISQ</b>"))
        self.isq_label = QLabel(str(self.settings.get("IsqTypes", "–")))
        form.addRow(self.isq_label)

        layout.addLayout(form)
        layout.addStretch()
        return w

    # ─── Import / Export ──────────────────────────────────────────────
    def import_package(self):
        path, _ = QFileDialog.getOpenFileName(self, "Paket importieren", "", "JSON Files (*.json);;Alle Dateien (*)")
        if not path:
            return
        path = Path(path)

        if path.name == "Products.json":
            # Single file
            self.products = thermoplan_io.load_single_products(path)
            self.views = []
            self.settings = {}
            self.serial_number = ""
        else:
            # Try as folder
            folder = path.parent if path.is_file() else path
            try:
                data = thermoplan_io.load_package(folder)
                self.products = data["Products"]
                self.views = data["ProductViews"]
                self.settings = data["ProductSettings"]
                self.serial_number = data.get("Manifest", {}).get("SerialNumber", "")
            except FileNotFoundError:
                QMessageBox.warning(self, "Fehler", "Unvollständiges Paket. Bitte Products.json wählen.")
                return

        self._refresh_products_table()
        self.variant_base_combo.clear()
        self.variant_base_combo.addItems([p["Name"] for p in self.products])
        self.cup_types_label.setText(str(self.settings.get("CupTypes", "–")))
        self.grinder_label.setText(str(self.settings.get("GrinderTypes", "–")))
        self.isq_label.setText(str(self.settings.get("IsqTypes", "–")))
        self.view_editor.set_data(self.products, self.views)

    def export_package(self):
        if not self.products:
            QMessageBox.warning(self, "Fehler", "Keine Rezepte vorhanden.")
            return
        folder, _ = QFileDialog.getExistingDirectory(self, "Export-Ziel wählen")
        if not folder:
            return

        self.views = self.view_editor.get_views()

        serial = str(self.serial_spin.value())
        out = thermoplan_io.save_package(
            products=self.products,
            views=self.views if self.views else [],
            settings=self.settings if self.settings else {},
            serial_number=serial,
            output_folder=folder,
        )
        QMessageBox.information(self, "Exportiert", f"Paket gespeichert in:\n{out}")


    def _show_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction

        selected_rows = sorted(set(idx.row() for idx in self.products_table.selectedIndexes()))
        if not selected_rows:
            return

        menu = QMenu(self)

        if len(selected_rows) == 1:
            act_edit = QAction("✏️ Bearbeiten", self)
            act_edit.triggered.connect(lambda: self._edit_recipe(
                self.products_table.item(selected_rows[0], 1)
            ))
            menu.addAction(act_edit)
            menu.addSeparator()

        act_batch = QAction(f"⚡ Batch-Operation ({len(selected_rows)} ausgewählt)", self)
        act_batch.triggered.connect(self._batch_operation)
        menu.addAction(act_batch)

        act_dup = QAction("📋 Duplizieren", self)
        act_dup.triggered.connect(self._duplicate_recipes)
        menu.addAction(act_dup)

        menu.addSeparator()
        act_del = QAction("🗑️ Löschen", self)
        act_del.triggered.connect(self._delete_recipes)
        menu.addAction(act_del)

        menu.exec(self.products_table.viewport().mapToGlobal(pos))

    def _batch_operation(self):
        selected_rows = sorted(set(idx.row() for idx in self.products_table.selectedIndexes()))
        if not selected_rows:
            return

        dialog = BatchDialog(self)
        if dialog.exec() == QDialog.Accepted:
            field_path, op, value = dialog.get_operation()
            count = 0
            for row in selected_rows:
                recipe = self.products[row]
                if self._apply_field(recipe, field_path, op, value):
                    count += 1
            self._refresh_products_table()

        # Refresh selection visual
        self.products_table.clearSelection()

    def _duplicate_recipes(self):
        import copy
        selected_rows = sorted(set(idx.row() for idx in self.products_table.selectedIndexes()), reverse=True)
        existing_ids = {p["ID"] for p in self.products}
        for row in selected_rows:
            new = copy.deepcopy(self.products[row])
            new["Name"] = new["Name"] + " (Kopie)"
            base = new["ID"]
            counter = 2
            while new["ID"] in existing_ids:
                new["ID"] = f"{base}_{counter}"
                counter += 1
            existing_ids.add(new["ID"])
            self.products.insert(row + 1, new)
        self._refresh_products_table()
        self.variant_base_combo.clear()
        self.variant_base_combo.addItems([p["Name"] for p in self.products])

    def _delete_recipes(self):
        from PySide6.QtWidgets import QMessageBox
        selected_rows = sorted(set(idx.row() for idx in self.products_table.selectedIndexes()), reverse=True)
        if not selected_rows:
            return
        reply = QMessageBox.question(
            self, "Löschen", f"{len(selected_rows)} Rezept(e) wirklich löschen?"
        )
        if reply == QMessageBox.Yes:
            for row in selected_rows:
                del self.products[row]
            self._refresh_products_table()
            self.variant_base_combo.clear()
            self.variant_base_combo.addItems([p["Name"] for p in self.products])

    def _apply_field(self, recipe: dict, field_path: str, op: str, value: float) -> bool:
        parts = field_path.split(".")
        obj = recipe
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            if "[" in part:
                key, idx_str = part.split("[")
                idx = int(idx_str.rstrip("]"))
                if key not in obj:
                    return False
                obj = obj[key]
                if not isinstance(obj, list) or idx >= len(obj):
                    return False
                if is_last:
                    current = obj[idx]
                    obj[idx] = self._compute(current, op, value)
                    return True
                obj = obj[idx]
            else:
                if part not in obj:
                    return False
                if is_last:
                    current = obj[part]
                    obj[part] = self._compute(current, op, value)
                    return True
                obj = obj[part]
        return False

    def _compute(self, current: float, op: str, value: float) -> float:
        if op == "set":
            return value
        elif op == "add":
            return round(current + value, 2)
        elif op == "sub":
            return round(current - value, 2)
        elif op == "mul":
            return round(current * value, 2)
        return current
