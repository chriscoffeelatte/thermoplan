from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MachineProfile:
    name: str
    grinders: int = 2
    cup_types: list[str] = field(default_factory=lambda: ["cup0", "cup1", "cup2"])
    max_recipes: int = 24
    milk_modules: list[str] = field(default_factory=lambda: ["MilkModule"])
    application_version: str = "1.15"


PROFILES: dict[str, MachineProfile] = {
    "BW4C": MachineProfile("BW4C", grinders=2, max_recipes=24),
    "BW4": MachineProfile("BW4", grinders=2, max_recipes=50),
}


@dataclass
class VariantConfig:
    sizes: list[str] = field(default_factory=lambda: ["cup0", "cup1", "cup2"])
    milk_types: list[str] = field(default_factory=lambda: ["Kuhmilch"])
    portions: list[int] = field(default_factory=lambda: [1, 2])


SIZE_LABELS = {"cup0": "Klein", "cup1": "Normal", "cup2": "Groß"}
SIZE_SCALES = {"cup0": 0.7, "cup1": 1.0, "cup2": 1.3}


@dataclass
class ViewItem:
    type: str
    label: str = ""
    productId: str = ""
    iconPath: str = ""
    selectedIndex: int = 0
    children: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, d):
        if d["type"] == "Group":
            return cls(
                type="Group", label=d.get("label", ""),
                iconPath=d.get("iconPath", ""),
                selectedIndex=d.get("selectedIndex", 0),
                children=[cls.from_dict(c) for c in d.get("children", [])]
            )
        return cls(type=d["type"], label=d.get("label", ""),
                   productId=d.get("productId", ""))

    def to_dict(self):
        if self.type == "Group":
            return {
                "type": "Group", "label": self.label,
                "iconPath": self.iconPath, "selectedIndex": self.selectedIndex,
                "children": [c.to_dict() for c in self.children]
            }
        if self.type == "Product":
            return {"type": "Product", "label": self.label, "productId": self.productId}
        return {"type": "Empty"}
