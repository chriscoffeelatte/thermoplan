import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _dump(obj: Any) -> str:
    return json.dumps(obj, indent="\t", ensure_ascii=False)


def load_package(folder: str | Path) -> dict:
    """Lädt ein komplettes Thermoplan-Paket (3 JSON + Manifest)."""
    folder = Path(folder)
    data = {
        "Products": json.loads((folder / "Products.json").read_text("utf-8")),
        "ProductViews": json.loads((folder / "ProductViews.json").read_text("utf-8")),
        "ProductSettings": json.loads((folder / "ProductSettings.json").read_text("utf-8")),
    }
    manifest_file = folder / "manifest.json"
    if manifest_file.exists():
        data["Manifest"] = json.loads(manifest_file.read_text("utf-8"))
    return data


def save_package(
    products: list[dict],
    views: list[dict],
    settings: dict,
    serial_number: str,
    output_folder: str | Path,
) -> Path:
    """
    Schreibt ein komplettes, validierbares Thermoplan-Paket.
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    files_content = {
        "Products.json": _dump(products),
        "ProductViews.json": _dump(views),
        "ProductSettings.json": _dump(settings),
    }

    file_hashes = []
    for fname, content in files_content.items():
        (output_folder / fname).write_text(content, encoding="utf-8")
        file_hashes.append({"file": fname, "hash": _sha256(content)})

    manifest = {
        "ApplicationVersion": "1.15",
        "CreationTimestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "Files": file_hashes,
        "SerialNumber": serial_number,
    }
    (output_folder / "manifest.json").write_text(_dump(manifest), encoding="utf-8")
    return output_folder


def load_single_products(file_path: str | Path) -> list[dict]:
    """Lädt nur die Products.json (falls kein komplettes Paket vorliegt)."""
    return json.loads(Path(file_path).read_text("utf-8"))   