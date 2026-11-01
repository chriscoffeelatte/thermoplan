import copy
from models import VariantConfig, SIZE_SCALES, SIZE_LABELS


def generate_variants(
    base_recipe: dict,
    config: VariantConfig,
    existing_ids: set[str] | None = None,
) -> list[dict]:
    """
    Erzeugt aus einem Basis-Rezept alle Varianten.
    """
    existing_ids = existing_ids or set()
    variants: list[dict] = []

    for size in config.sizes:
        scale = SIZE_SCALES.get(size, 1.0)
        for milk in config.milk_types:
            for portion in config.portions:
                v = copy.deepcopy(base_recipe)
                _apply_scale(v, scale, portion)
                _apply_size(v, size)
                _set_milk_type(v, milk)
                _update_name(v, size, milk, portion)
                _update_id(v, existing_ids)
                existing_ids.add(v["ID"])
                variants.append(v)
    return variants


def _apply_scale(recipe: dict, scale: float, portion: int) -> None:
    factor = scale * portion
    ing = recipe.get("Ingredients", {})

    if "Coffee" in ing:
        c = ing["Coffee"]
        c["CoffeeAmountsGrams"] = [round(g * factor, 1) for g in c.get("CoffeeAmountsGrams", [])]
        c["TotalAmountMilliliters"] = round(c.get("TotalAmountMilliliters", 0) * factor, 1)
        c["PreBrewMilliliters"] = round(c.get("PreBrewMilliliters", 0) * factor, 1)

    if "Milk" in ing:
        m = ing["Milk"]
        m["ProductDurationsSeconds"] = [round(d * factor, 1) for d in m.get("ProductDurationsSeconds", [])]

    if "Water" in ing:
        ing["Water"]["AmountMilliliters"] = round(ing["Water"].get("AmountMilliliters", 0) * factor, 1)


def _apply_size(recipe: dict, size: str) -> None:
    recipe["CupType"] = size


def _set_milk_type(recipe: dict, milk_type: str) -> None:
    ing = recipe.get("Ingredients", {})
    if "Milk" in ing:
        if milk_type.lower() in ("oat", "soja", "reis", "alternative", "pflanzlich"):
            ing["Milk"]["Temperatures"] = [72.0, 72.0]


def _update_name(recipe: dict, size: str, milk: str, portion: int) -> None:
    base = recipe["Name"].rstrip(".")
    # Entferne bereits vorhandene Suffixe
    for suffix in ("Klein", "Groß", "Normal", "(Alt. Milch)", "(Pflanzlich)"):
        base = base.replace(f" {suffix}", "").replace(suffix, "")
    base = base.rstrip(" .")

    parts = [base]
    if portion > 1:
        parts.insert(0, f"{portion}x")
    if size != "cup1":
        parts.append(SIZE_LABELS[size])
    if milk.lower() not in ("kuhmilch", "milk"):
        parts.append(f"({milk.capitalize()})")
    recipe["Name"] = " ".join(parts)


def _update_id(recipe: dict, existing_ids: set[str]) -> None:
    base_id = recipe["ID"].split("_")[0] if "_" in recipe["ID"] else recipe["ID"]
    # Entferne alte Suffixe
    for suffix in ("_Klein", "_Groß", "_Normal", "_Alt", "_2x", "_1x"):
        base_id = base_id.replace(suffix, "")
    base_id = base_id.rstrip("_")

    size_tag = {"cup0": "_Klein", "cup1": "", "cup2": "_Groß"}.get(recipe.get("CupType", "cup1"), "")
    milk = recipe.get("Ingredients", {}).get("Milk")
    milk_tag = ""
    if milk and milk.get("Temperatures", [70])[0] > 71:
        milk_tag = "_Pflanzlich"

    portion = 1
    if "Coffee" in recipe.get("Ingredients", {}):
        grams = recipe["Ingredients"]["Coffee"].get("CoffeeAmountsGrams", [0])[0]
        if grams > 12:
            portion = 2
    portion_tag = f"_{portion}x" if portion > 1 else ""

    new_id = f"{base_id}{size_tag}{milk_tag}{portion_tag}"
    # Ensure uniqueness
    counter = 1
    while new_id in existing_ids:
        new_id = f"{base_id}{size_tag}{milk_tag}{portion_tag}_{counter}"
        counter += 1
    recipe["ID"] = new_id
