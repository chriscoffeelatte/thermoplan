import copy
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QSplitter, QListWidget,
    QListWidgetItem, QFrame, QScrollArea, QGroupBox, QCheckBox,
    QMessageBox, QMenu, QAbstractItemView,
)
from PySide6.QtCore import Qt, QMimeData, QTimer
from PySide6.QtGui import QAction, QDrag, QMouseEvent, QPalette, QColor


class ProductItem(QFrame):
    """Ein einzelner Slot im Grid – per Drag & Drop befüllbar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 100)
        self.setFrameStyle(QFrame.Raised)
        self.setLineWidth(1)
        self.setAcceptDrops(True)

        self.label = QLabel("Leer")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 11px; color: #888;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.label)

        self.product_id: str = ""

    def set_product(self, product_id: str, name: str):
        self.product_id = product_id
        self.label.setText(name)
        self.label.setStyleSheet("font-size: 11px; color: #222; font-weight: bold;")
        self.setStyleSheet("QFrame { background-color: #e8f5e9; border: 1px solid #4caf50; }")

    def clear(self):
        self.product_id = ""
        self.label.setText("Leer")
        self.label.setStyleSheet("font-size: 11px; color: #888;")
        self.setStyleSheet("")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        product_id = event.mimeData().text()
        if product_id:
            # Find name from parent
            editor = self.parentWidget()
            while editor and not hasattr(editor, "products"):
                editor = editor.parentWidget()
            if editor:
                for p in editor.products:
                    if p["ID"] == product_id:
                        self.set_product(product_id, p["Name"])
                        break

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        if self.product_id:
            act_clear = QAction("Entfernen", self)
            act_clear.triggered.connect(self.clear)
            menu.addAction(act_clear)
        menu.exec(event.globalPos())


class ProductSourceItem(QListWidgetItem):
    """Draggbarer Eintrag in der Produkt-Liste links."""

    def __init__(self, product_id: str, name: str, category: str):
        super().__init__(f"{name}  [{category}]")
        self.setData(Qt.UserRole, product_id)
        self.setFlags(self.flags() | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)

class DraggableProductList(QListWidget):
    """QListWidget, das die product_id als Text in die MimeData schreibt."""

    def mimeData(self, items):
        mime = super().mimeData(items)
        if items:
            product_id = items[0].data(Qt.UserRole)
            mime.setText(product_id)
        return mime

class ViewEditor(QWidget):
    """Tab-Widget für den View-Editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.products: list[dict] = []
        self.views: list[dict] = []
        self.current_view_idx: int = 0

        layout = QVBoxLayout(self)

        # ─── Top: View-Auswahl ────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        top_row.addWidget(self.view_combo)

        top_row.addSpacing(20)
        top_row.addWidget(QLabel("Aktiv:"))
        self.active_check = QCheckBox()
        self.active_check.toggled.connect(self._on_active_toggled)
        top_row.addWidget(self.active_check)

        top_row.addSpacing(20)
        top_row.addWidget(QLabel("Spalten:"))
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 8)
        self.cols_spin.valueChanged.connect(self._rebuild_grid)
        top_row.addWidget(self.cols_spin)

        top_row.addWidget(QLabel("Zeilen:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 6)
        self.rows_spin.valueChanged.connect(self._rebuild_grid)
        top_row.addWidget(self.rows_spin)

        top_row.addStretch()

        btn_new_view = QPushButton("+ Neue View")
        btn_new_view.clicked.connect(self._add_view)
        top_row.addWidget(btn_new_view)

        btn_del_view = QPushButton("− View löschen")
        btn_del_view.clicked.connect(self._delete_view)
        top_row.addWidget(btn_del_view)

        layout.addLayout(top_row)

        # ─── Splitter: Links Produkte, Rechts Grid ────────────────────
        splitter = QSplitter(Qt.Horizontal)

        # Linke Seite: Produkt-Liste
        left_panel = QGroupBox("Verfügbare Produkte")
        left_layout = QVBoxLayout(left_panel)

        self.product_list = DraggableProductList()
        self.product_list.setDragEnabled(True)
        self.product_list.setDragDropMode(QAbstractItemView.DragOnly)
        self.product_list.setSelectionMode(QAbstractItemView.SingleSelection)
        left_layout.addWidget(self.product_list)
        splitter.addWidget(left_panel)

        # Rechte Seite: Grid
        right_panel = QGroupBox("Display-Layout")
        right_layout = QVBoxLayout(right_panel)

        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_scroll.setWidget(self.grid_container)
        right_layout.addWidget(self.grid_scroll)

        # User / ViewName
        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("User:"))
        self.user_combo = QComboBox()
        self.user_combo.addItems(["SelfService", "Barista", "Admin"])
        meta_row.addWidget(self.user_combo)
        meta_row.addSpacing(20)
        meta_row.addWidget(QLabel("Name:"))
        from PySide6.QtWidgets import QLineEdit
        self.view_name_edit = QLineEdit()
        meta_row.addWidget(self.view_name_edit)
        right_layout.addLayout(meta_row)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        # ─── Grid-Items ───────────────────────────────────────────────
        self.grid_items: list[ProductItem] = []

    # ─── Public API ───────────────────────────────────────────────────
    def set_data(self, products: list[dict], views: list[dict]):
        self.products = products
        self.views = views
        self._populate_product_list()
        self._populate_view_combo()
        if self.views:
            self._load_view(0)

    def get_views(self) -> list[dict]:
        """Gibt die aktuell bearbeiteten Views zurück."""
        self._save_current_grid_to_view()
        return self.views

    # ─── Product List ─────────────────────────────────────────────────
    def _populate_product_list(self):
        self.product_list.clear()
        for p in self.products:
            item = ProductSourceItem(p["ID"], p["Name"], p.get("Category", ""))
            self.product_list.addItem(item)

    # ─── View Combo ───────────────────────────────────────────────────
    def _populate_view_combo(self):
        self.view_combo.blockSignals(True)
        self.view_combo.clear()
        for i, v in enumerate(self.views):
            self.view_combo.addItem(f"{v.get('ViewName', f'View {i+1}')} ({v.get('User', '')})")
        self.view_combo.blockSignals(False)
        if self.views:
            self.view_combo.setCurrentIndex(0)

    def _on_view_changed(self, idx: int):
        if idx >= 0 and idx < len(self.views):
            self._save_current_grid_to_view()
            self._load_view(idx)

    def _on_active_toggled(self, checked: bool):
        if self.current_view_idx < len(self.views):
            self.views[self.current_view_idx]["Active"] = checked

    # ─── Grid ─────────────────────────────────────────────────────────
    def _rebuild_grid(self):
        # Alte Items entfernen
        for item in self.grid_items:
            self.grid_layout.removeWidget(item)
            item.deleteLater()
        self.grid_items.clear()

        cols = self.cols_spin.value()
        rows = self.rows_spin.value()
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setHorizontalSpacing(6)
        self.grid_layout.setVerticalSpacing(6)

        for r in range(rows):
            for c in range(cols):
                slot = ProductItem()
                self.grid_layout.addWidget(slot, r, c)
                self.grid_items.append(slot)

        # Bestehende Daten laden
        self._load_grid_from_view()

    def _load_grid_from_view(self):
        if self.current_view_idx >= len(self.views):
            return
        view = self.views[self.current_view_idx]
        children = view.get("ProductView", {}).get("children", [])

        for i, slot in enumerate(self.grid_items):
            if i < len(children):
                child = children[i]
                if child.get("type") == "Product":
                    pid = child.get("productId", "")
                    name = self._find_product_name(pid)
                    slot.set_product(pid, name)
                else:
                    slot.clear()
            else:
                slot.clear()

    def _load_view(self, idx: int):
        self.current_view_idx = idx
        if idx >= len(self.views):
            return
        view = self.views[idx]
        layout = view.get("Layout", {})
        self.cols_spin.blockSignals(True)
        self.rows_spin.blockSignals(True)
        self.cols_spin.setValue(layout.get("Columns", 3))
        self.rows_spin.setValue(layout.get("Rows", 3))
        self.cols_spin.blockSignals(False)
        self.rows_spin.blockSignals(False)

        self.active_check.blockSignals(True)
        self.active_check.setChecked(view.get("Active", False))
        self.active_check.blockSignals(False)

        self.user_combo.setCurrentText(view.get("User", "Barista"))
        self.view_name_edit.setText(view.get("ViewName", ""))

        self._rebuild_grid()

    def _save_current_grid_to_view(self):
        if self.current_view_idx >= len(self.views):
            return
        view = self.views[self.current_view_idx]
        view["ViewName"] = self.view_name_edit.text()
        view["User"] = self.user_combo.currentText()
        view["Active"] = self.active_check.isChecked()
        view["Layout"]["Columns"] = self.cols_spin.value()
        view["Layout"]["Rows"] = self.rows_spin.value()

        children = []
        for slot in self.grid_items:
            if slot.product_id:
                children.append({
                    "label": slot.product_id,
                    "productId": slot.product_id,
                    "type": "Product",
                })
            else:
                children.append({"type": "Empty"})
        view["ProductView"]["children"] = children

    # ─── Views Add/Delete ─────────────────────────────────────────────
    def _add_view(self):
        new_view = {
            "Active": False,
            "Layout": {"Columns": 3, "Rows": 3, "OrderMode": ""},
            "ProductView": {
                "children": [{"type": "Empty"} for _ in range(9)],
                "iconPath": "",
                "label": "",
                "type": "Group",
            },
            "User": "Barista",
            "ViewName": f"View {len(self.views) + 1}",
        }
        self.views.append(new_view)
        self._populate_view_combo()
        self.view_combo.setCurrentIndex(len(self.views) - 1)
        self._load_view(len(self.views) - 1)

    def _delete_view(self):
        if len(self.views) <= 1:
            QMessageBox.warning(self, "Hinweis", "Mindestens eine View muss vorhanden sein.")
            return
        idx = self.current_view_idx
        self.views.pop(idx)
        self._populate_view_combo()
        new_idx = min(idx, len(self.views) - 1)
        self.view_combo.setCurrentIndex(new_idx)
        self._load_view(new_idx)

    # ─── Helper ───────────────────────────────────────────────────────
    def _find_product_name(self, product_id: str) -> str:
        for p in self.products:
            if p["ID"] == product_id:
                return p["Name"]
        return product_id
