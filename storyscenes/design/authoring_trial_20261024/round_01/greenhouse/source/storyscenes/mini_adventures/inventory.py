"""Discover authored packs without importing their simulators at listing time."""
from importlib import import_module
import json
from pathlib import Path


ROOT = Path(__file__).parent
PACKS = {
    "bakery": {"seed": 757654805, "setting": "village bakery", "prop": "a borrowed lantern",
               "want": "to keep a surprise secret"},
    "greenhouse": {"seed": 822263077, "setting": "allotment greenhouse", "prop": "a waxed paper parcel",
                   "want": "to win back a friend's trust"},
}


def load(pack):
    if pack not in PACKS:
        raise ValueError(f"Unknown pack: {pack}")
    return import_module(f"storyscenes.mini_adventures.{pack}.world")


def catalogue(pack):
    if pack not in PACKS:
        raise ValueError(f"Unknown pack: {pack}")
    path = ROOT / pack / "scene_inventory.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["scenes"]
    ids = [entry["id"] for entry in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate reference scene IDs")
    for entry in entries:
        if not isinstance(entry.get("implemented_ids"), list):
            raise ValueError(f"Missing implementation mapping: {entry['id']}")
    return {"pack": pack, **PACKS[pack], "reference": str(ROOT / pack / "reference_story.md"),
            "scenes": entries}


def check_inventory(pack, module):
    data = catalogue(pack)
    scene_ids = tuple(module.SCENES)
    if len(set(scene_ids)) != len(scene_ids):
        raise ValueError("Duplicate executable scene IDs")
    mapped = {scene for entry in data["scenes"] for scene in entry["implemented_ids"]}
    if mapped != set(scene_ids):
        raise ValueError(f"Inventory mismatch: missing={set(scene_ids) - mapped}; unknown={mapped - set(scene_ids)}")
    return data
