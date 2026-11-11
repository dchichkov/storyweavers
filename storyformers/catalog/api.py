"""Explicit, opt-in access to catalog data and its native grammar subset."""

from copy import deepcopy
import json
from pathlib import Path

from ..neuron_spec import parse_neuron
from ..positions import add_positions
from ..transformer import GrammarHead, StoryformerBlock


ROOT = Path(__file__).resolve().parent


class AdapterRequired(ValueError):
    """The selected research contract is not an executable Storyformer head."""


class CatalogIndex:
    def __init__(self, directory=ROOT):
        directory = Path(directory)
        self.attributes, self.heads, self.grammars = (
            {row["id"]: row for row in (json.loads(line) for line in (directory / f"{kind}.jsonl").read_text().splitlines())}
            for kind in ("attributes", "heads", "grammars")
        )
        self.by_key = {row["key"]: row for row in self.attributes.values()}

    def feature_registry(self, keys=None):
        """Metadata only: a catalog name does not create training supervision."""
        result = {}
        for key in (self.by_key if keys is None else keys):
            attribute = self.by_key[key]
            result[key] = {name: deepcopy(attribute[name]) for name in
                           ("type", "description", "scope", "availability", "nullable",
                            "missing_means", "values", "aliases") if name in attribute}
            result[key].update(origin="catalog_candidate", catalog_id=attribute["id"])
        return result

    def neuron(self, grammar_id):
        record = self.grammars[grammar_id]
        if record["runtime_support"] != "native":
            raise AdapterRequired(f"{grammar_id} requires: {', '.join(record['requires'])}")
        return parse_neuron(deepcopy(record["neuron"]))

    def head(self, head_id, *, strength=None):
        record = self.heads[head_id]
        if len(record["grammar_ids"]) != 1:
            raise ValueError("multi-neuron routing needs an explicit adapter")
        return GrammarHead(self.neuron(record["grammar_ids"][0]), operation=record["operation"],
                           strength=record["initial_strength"] if strength is None else strength,
                           null_mass=record["initial_null_mass"])

    def block(self, head_ids, *, num_heads=16):
        """Install only explicitly selected native heads; remaining slots are NOOP."""
        return StoryformerBlock(tuple(self.head(hid) for hid in head_ids), num_heads=num_heads)


def prepare_context(records):
    """Explicit word/punctuation adapter, preserving original positions and IDs.

    Catalog fixtures omit spaces. Position supplied by the original lossless
    annotation wins; if missing, compute it before removing whitespace records.
    Never renumber entity/event IDs or source `index` fields here.
    """
    records = list(records)
    positioned = add_positions(records)
    result = []
    for original, computed in zip(records, positioned):
        if original.get("kind") == "space" or original["token"].isspace():
            continue
        row = deepcopy(original)
        row.setdefault("position", computed["position"])
        result.append(row)
    return result
