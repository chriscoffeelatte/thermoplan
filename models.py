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
