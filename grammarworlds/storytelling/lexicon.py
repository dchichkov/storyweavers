"""Shared lexical entries; packs retain explicit overrides for conflicting senses."""
from copy import deepcopy
import json
from pathlib import Path

SHARED = json.loads(Path(__file__).with_name("shared_lexicon.json").read_text())


def with_shared(local):
    result = deepcopy(SHARED)
    for category, entries in local.items():
        result.setdefault(category, {}).update(deepcopy(entries))
    return result
