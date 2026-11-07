import copy
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QSplitter, QListWidget,
    QListWidgetItem, QFrame, QScrollArea, QGroupBox, QCheckBox,
    QMessageBox, QMenu, QAbstractItemView, QDialog, QLineEdit,
    QInputDialog,
)
from PySide6.QtCore import Qt, QMimeData, QTimer
from PySide6.QtGui import QAction, QDrag, QMouseEvent, QPalette, QColor


# ─── ProductItem ─────────────────────────────────────────────────────────────
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
        self.item_type: str = "Empty"  # "Empty" | "Product" | "Group"
        self.group_data: dict = {}

    def set_product(self, product_id: str, name: str):
        self.product_id = product_id
        self.item_type = "Product"
        self.group_data = {}
        self.label.setText(name)
        self.label.setStyleSheet("font-size: 11px; color: #222; font-weight: bold;")
        self.setStyleSheet("QFrame { background-color: #e8f5e9; border: 1px solid #4caf50; }")

    def set_group(self, group_dict: dict):
        self.product_id = ""
        self.item_type = "Group"
        self.group_data = group_dict
        self.label.setText(f"📁 {group_dict.get('label', 'Gruppe')}")
        self.label.setStyleSheet("font-size: 11px; color: #1565c0; font-weight: bold;")
        self.setStyleSheet("QFrame { background-color: #e3f2fd; border: 2px solid #1565c0; }")

    def clear(self):
        self.product_id = ""
        self.item_type = "Empty"
        self.group_data = {}
        self.label.setText("Leer")
        self.label.setStyleSheet("font-size: 11px; color: #888;")
        self.setStyleSheet("")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        product_id = event.mimeData().text()
        if product_id:
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
        if self.item_type == "Product":
            act_clear = QAction("Entfernen", self)
            act_clear.triggered.connect(self.clear)
            menu.addAction(act_clear)
        elif self.item_type == "Group":
            act_edit = QAction("Gruppe bearbeiten…", self)
            act_edit.triggered.connect(self._edit_group)
            menu.addAction(act_edit)
            menu.addSeparator()
            act_clear = QAction("Entfernen", self)
            act_clear.triggered.connect(self.clear)
            menu.addAction(act_clear)
        else:
            act_add_product = QAction("Produkt einfügen…", self)
            act_add_product.triggered.connect(self._prompt_product)
            menu.addAction(act_add_product)
            act_add_group = QAction("Gruppe einfügen…", self)
            act_add_group.triggered.connect(self._prompt_group)
            menu.addAction(act_add_group)
        menu.exec(event.globalPos())

    def _edit_group(self):
        dlg = GroupEditor(copy.deepcopy(self.group_data), self._find_products(), self)
        if dlg.exec() == QDialog.Accepted:
            self.set_group(dlg.get_group_dict())

    def _prompt_group(self):
        dlg = GroupEditor({}, self._find_products(), self)
        if dlg.exec() == QDialog.Accepted:
            self.set_group(dlg.get_group_dict())

    def _prompt_product(self):
        products = self._find_products()
        if not products:
            return
        names = [f"{p['Name']}  [{p.get('Category', '')}]" for p in products]
        text, ok = QInputDialog.getItem(self, "Produkt wählen", "Produkt:", names, 0, False)
        if ok:
            idx = names.index(text)
            p = products[idx]
            self.set_product(p["ID"], p["Name"])

    def _find_products(self) -> list[dict]:
        w = self.parentWidget()
        while w and not hasattr(w, "products"):
            w = w.parentWidget()
        return w.products if w else []


# ─── GroupEditor ─────────────────────────────────────────────────────────────
class GroupEditor(QDialog):
    """Dialog zum Bearbeiten einer Gruppe (Name, Icon, Kinder – rekursiv)."""

    def __init__(self, group_dict: dict, products: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gruppe bearbeiten")
        self.resize(520, 420)
        self._products = products
        self._children: list[dict] = group_dict.get("children", [])

        layout = QVBoxLayout(self)

        # Name + Icon
        row = QHBoxLayout()
        row.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(group_dict.get("label", ""))
        row.addWidget(self.name_edit)
        row.addWidget(QLabel("Icon:"))
        self.icon_edit = QLineEdit(group_dict.get("iconPath", ""))
        row.addWidget(self.icon_edit)
        layout.addLayout(row)

        # Kinder-Liste
        layout.addWidget(QLabel("Inhalte:"))
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._refresh_list()
        layout.addWidget(self.list)

        # Buttons
        btn_row = QHBoxLayout()
        btn_add_product = QPushButton("+ Produkt")
        btn_add_product.clicked.connect(self._add_product)
        btn_row.addWidget(btn_add_product)

        btn_add_group = QPushButton("+ Untergruppe")
        btn_add_group.clicked.connect(self._add_subgroup)
        btn_row.addWidget(btn_add_group)

        btn_remove = QPushButton("− Entfernen")
        btn_remove.clicked.connect(self._remove_selected)
        btn_row.addWidget(btn_remove)

        btn_up = QPushButton("↑")
        btn_up.clicked.connect(self._move_up)
        btn_row.addWidget(btn_up)

        btn_down = QPushButton("↓")
        btn_down.clicked.connect(self._move_down)
        btn_row.addWidget(btn_down)

        btn_row.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _refresh_list(self):
        self.list.clear()
        for c in self._children:
            if c["type"] == "Product":
                self.list.addItem(f"☕  {c.get('label', c.get('productId', ''))}")
            elif c["type"] == "Group":
                self.list.addItem(f"📁  {c.get('label', 'Gruppe')}")
            else:
                self.list.addItem("— Leer —")

    def _add_product(self):
        if not self._products:
            return
        names = [p["Name"] for p in self._products]
        text, ok = QInputDialog.getItem(self, "Produkt", "Wähle:", names, 0, False)
        if ok:
            p = self._products[names.index(text)]
            self._children.append({"type": "Product", "label": p["Name"], "productId": p["ID"]})
            self._refresh_list()

    def _add_subgroup(self):
        name, ok = QInputDialog.getText(self, "Untergruppe", "Name:")
        if ok and name.strip():
            self._children.append({
                "type": "Group", "label": name.strip(),
                "iconPath": "", "selectedIndex": 0, "children": []
            })
            self._refresh_list()

    def _remove_selected(self):
        row = self.list.currentRow()
        if 0 <= row < len(self._children):
            self._children.pop(row)
            self._refresh_list()

    def _move_up(self):
        row = self.list.currentRow()
        if row > 0:
            self._children[row - 1], self._children[row] = self._children[row], self._children[row - 1]
            self._refresh_list()
            self.list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.list.currentRow()
        if 0 <= row < len(self._children) - 1:
            self._children[row], self._children[row + 1] = self._children[row + 1], self._children[row]
            self._refresh_list()
            self.list.setCurrentRow(row + 1)

    def get_group_dict(self) -> dict:
        return {
            "type": "Group",
            "label": self.name_edit.text(),
            "iconPath": self.icon_edit.text(),
            "selectedIndex": 0,
            "children": self._children,
        }


# ─── ProductSourceItem / DraggableProductList ────────────────────────────────
class ProductSourceItem(QListWidgetItem):
    def __init__(self, product_id: str, name: str, category: str):
        super().__init__(f"{name}  [{category}]")
        self.setData(Qt.UserRole, product_id)
        self.setFlags(self.flags() | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)


class DraggableProductList(QListWidget):
    def mimeData(self, items):
        mime = super().mimeData(items)
        if items:
            product_id = items[0].data(Qt.UserRole)
            mime.setText(product_id)
        return mime


# ─── ViewEditor ──────────────────────────────────────────────────────────────
class ViewEditor(QWidget):
    """Tab-Widget für den View-Editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.products: list[dict] = []
        self.views: list[dict] = []
        self.current_view_idx: int = 0
        self.grid_items: list[ProductItem] = []

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

        # Linke Seite
        left_panel = QGroupBox("Verfügbare Produkte")
        left_layout = QVBoxLayout(left_panel)
        self.product_list = DraggableProductList()
        self.product_list.setDragEnabled(True)
        self.product_list.setDragDropMode(QAbstractItemView.DragOnly)
        self.product_list.setSelectionMode(QAbstractItemView.SingleSelection)
        left_layout.addWidget(self.product_list)
        splitter.addWidget(left_panel)

        # Rechte Seite
        right_panel = QGroupBox("Display-Layout")
        right_layout = QVBoxLayout(right_panel)

        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_scroll.setWidget(self.grid_container)
        right_layout.addWidget(self.grid_scroll)

        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("User:"))
        self.user_combo = QComboBox()
        self.user_combo.addItems(["SelfService", "Barista", "Admin"])
        meta_row.addWidget(self.user_combo)
        meta_row.addSpacing(20)
        meta_row.addWidget(QLabel("Name:"))
        self.view_name_edit = QLineEdit()
        meta_row.addWidget(self.view_name_edit)
        right_layout.addLayout(meta_row)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    # ─── Public API ───────────────────────────────────────────────────
    def set_data(self, products: list[dict], views: list[dict]):
        self.products = products
        self.views = views
        self._populate_product_list()
        self._populate_view_combo()
        if self.views:
            self._load_view(0)

    def get_views(self) -> list[dict]:
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

        self._load_grid_from_view()

    def _load_grid_from_view(self):
        if self.current_view_idx >= len(self.views):
            return
        view = self.views[self.current_view_idx]
        children = view.get("OrderView", {}).get("children", [])

        for i, slot in enumerate(self.grid_items):
            if i < len(children):
                child = children[i]
                if child.get("type") == "Product":
                    pid = child.get("productId", "")
                    name = self._find_product_name(pid)
                    slot.set_product(pid, name)
                elif child.get("type") == "Group":
                    slot.set_group(child)
                else:
                    slot.clear()
            else:
                slot.clear()

    def _save_current_grid_to_view(self):
        if self.current_view_idx >= len(self.views):
            return
        view = self.views[self.current_view_idx]
        view["ViewName"] = self.view_name_edit.text()
        view["User"] = self.user_combo.currentText()
        view["Active"] = self.active_check.isChecked()
        view["Dimensions"]["Columns"] = self.cols_spin.value()
        view["Dimensions"]["Rows"] = self.rows_spin.value()

        children = []
        for slot in self.grid_items:
            if slot.item_type == "Product":
                children.append({
                    "label": slot.product_id,
                    "productId": slot.product_id,
                    "type": "Product",
                })
            elif slot.item_type == "Group":
                children.append(slot.group_data)
            else:
                children.append({"type": "Empty"})
        view["OrderView"]["children"] = children

    def _load_view(self, idx: int):
        self.current_view_idx = idx
        if idx >= len(self.views):
            return
        view = self.views[idx]
        dims = view.get("Dimensions", {})
        self.cols_spin.blockSignals(True)
        self.rows_spin.blockSignals(True)
        self.cols_spin.setValue(dims.get("Columns", 3))
        self.rows_spin.setValue(dims.get("Rows", 3))
        self.cols_spin.blockSignals(False)
        self.rows_spin.blockSignals(False)

        self.active_check.blockSignals(True)
        self.active_check.setChecked(view.get("Active", False))
        self.active_check.blockSignals(False)

        self.user_combo.setCurrentText(view.get("User", "Barista"))
        self.view_name_edit.setText(view.get("ViewName", ""))

        self._rebuild_grid()

    # ─── Views Add/Delete ─────────────────────────────────────────────
    def _add_view(self):
        new_view = {
            "Active": False,
            "Design": "ProductsAndGroups",
            "Dimensions": {"Columns": 3, "Rows": 3},
            "OrderView": {
                "children": [{"type": "Empty"} for _ in range(9)],
                "iconPath": "",
                "label": "HEAD",
                "type": "Group",
            },
            "Queued": False,
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
