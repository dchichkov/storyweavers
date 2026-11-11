"""Build and audit the three linked research catalogs without model/API calls."""

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import re

from .schema import EXTERNAL_FIELDS, VERSION
from ..grammar import canonical
from ..neuron_spec import check_value, parse_neuron
from ..positions import add_positions
from ..transformer import GrammarHead, PROTECTED, Residual, StoryformerBlock


ROOT = Path(__file__).resolve().parent
KINDS = ("attributes", "heads", "grammars")
SHARDS = ("core", "linguistic", "world", "mind")
ANNOTATION_VALUES = {
    "pos": ["n", "v", "adj", "adv", "pron", "det", "adp", "conj", "num", "part", "intj", "unknown", "space", "punct"],
    "event_type": ["obtain", "transfer", "repair", "move", "perceive", "speak", "feel", "state", "other"],
    "factuality": ["asserted", "negated", "desired", "hypothetical", "reported"],
}


def assemble():
    result = {kind: [] for kind in KINDS}
    for shard in SHARDS:
        records = importlib.import_module(f"{__package__}.sources.{shard}").build()
        if any(len(records[kind]) != 256 for kind in KINDS):
            raise ValueError(f"{shard}: expected 256 records of each kind")
        for kind in KINDS:
            result[kind].extend(records[kind])
    # Associations are not a false one-to-one neuron/feature identity. Some heads
    # consume their associated field to suppress a different field's evidence.
    producers, inhibitors, consumers = defaultdict(list), defaultdict(list), defaultdict(list)
    grammars = {row["id"]: row for row in result["grammars"]}
    for head in result["heads"]:
        for field in head["writes"]:
            (inhibitors if head["operation"] == "suppress" else producers)[field].append(head["id"])
        for field in head["reads"]:
            consumers[field].append(head["id"])
        head["key"] = {"match_grammar_ids": head["grammar_ids"], "read_fields": head["reads"]}
        head["value_projection"] = {"defined_by": head["grammar_ids"], "write_fields": head["writes"]}
        head["initial_strength"] = head.get("initial_strength", 1.0)
        head["initial_null_mass"] = 1.0
        head["weight_status"] = "untrained_seed"
        for gid in head["grammar_ids"]:
            grammars[gid]["residual_operation"] = head["operation"]
    for attribute in result["attributes"]:
        key = attribute["key"]
        attribute["producer_head_ids"] = sorted(producers[key])
        attribute["suppressor_head_ids"] = sorted(inhibitors[key])
        attribute["consumer_head_ids"] = sorted(consumers[key])
        attribute["input_policy"] = "May be supplied by causal annotation or a separately evaluated producer. No source is assumed correct merely because a field exists."
        if key in ANNOTATION_VALUES:
            attribute["values"] = ANNOTATION_VALUES[key]
    for kind in KINDS:
        result[kind].sort(key=lambda row: row["id"])
    return result


def validate(records, *, source_ids=None, execute=True):
    """Check all records and execute all native witnesses, never adapter prose."""
    errors = []
    def require(condition, message):
        if not condition:
            errors.append(message)

    maps = {}
    for kind, letter in zip(KINDS, "AHG"):
        rows = records[kind]
        maps[kind] = {row["id"]: row for row in rows}
        require(len(rows) == 1024, f"{kind}: expected 1024 rows")
        require(set(maps[kind]) == {f"{letter}{i:04d}" for i in range(1, 1025)}, f"{kind}: missing or duplicate IDs")
        for row in rows:
            require(row["schema_version"] == VERSION, f"{row['id']}: schema version")
            require(row["source_ids"], f"{row['id']}: no provenance")
            if source_ids is not None:
                require(set(row["source_ids"]) <= source_ids, f"{row['id']}: unknown sources {set(row['source_ids']) - source_ids}")
    attributes = {row["key"]: row for row in records["attributes"]}
    require(len(attributes) == 1024, "attribute keys are not unique")
    registry = {**{name: {"type": typ} for name, typ in EXTERNAL_FIELDS.items()}, **attributes}
    signatures = defaultdict(list)
    for attr in records["attributes"]:
        label = attr["id"]
        require(bool(re.fullmatch(r"[a-z][a-z0-9_]*", attr["key"])), f"{label}: invalid key")
        require(len(attr["description"]) >= 30, f"{label}: underspecified definition")
        require(attr["missing_means"] == "unknown" and attr["nullable"], f"{label}: missing-value semantics")
        try:
            check_value(attr["example_value"], attr)
        except (ValueError, KeyError) as exc:
            errors.append(f"{label}: {exc}")
        for field in ("producer_head_ids", "consumer_head_ids", "suppressor_head_ids"):
            require(set(attr[field]) <= set(maps["heads"]), f"{label}: invalid {field}")
        require(set(attr["grammar_ids"]) <= set(maps["grammars"]), f"{label}: invalid grammar association")
    executed, causal_checks, suppression_checks = 0, 0, 0
    adapter_seeds, seed_examples = 0, 0
    for grammar in records["grammars"]:
        gid = grammar["id"]
        require(set(grammar["attribute_ids"]) <= set(maps["attributes"]), f"{gid}: attribute reference")
        require(set(grammar["head_ids"]) <= set(maps["heads"]), f"{gid}: head reference")
        require(set(grammar["reads"] + grammar["writes"]) <= set(registry), f"{gid}: unknown fields {set(grammar['reads'] + grammar['writes']) - set(registry)}")
        require(not set(grammar["writes"]) & PROTECTED, f"{gid}: writes protected fields")
        require(len(grammar["examples"]) >= 2, f"{gid}: needs a positive and a contrast")
        require({ex["polarity"] for ex in grammar["examples"]} >= {"positive", "contrastive"}, f"{gid}: example polarity")
        for ex in grammar["examples"]:
            require(bool(ex["context"]), f"{gid}: empty example context")
            require(bool(ex["why"]), f"{gid}: missing example rationale")
            require(set(ex["expect"]) <= set(grammar["writes"]), f"{gid}: expected undeclared output")
            for record in [*ex["context"], ex["expect"]]:
                for key, value in record.items():
                    if key not in registry:
                        errors.append(f"{gid}: example uses unknown field {key}")
                        continue
                    try:
                        check_value(value, registry[key])
                        if value is not None and "values" in registry[key]:
                            require(value in registry[key]["values"], f"{gid}/{key}: unsupported annotation value {value!r}")
                    except (ValueError, KeyError) as exc:
                        errors.append(f"{gid}/{key}: {exc}")
        if grammar["runtime_support"] == "adapter_required":
            require(bool(grammar["requires"]) and "contract" in grammar and "neuron" not in grammar, f"{gid}: adapter status")
            require(set(grammar["contract"]) >= {"match", "guards", "emit"}, f"{gid}: missing contract components")
            require(bool(grammar["contract"]["guards"]), f"{gid}: unguarded contract")
            # A reusable finite seed does not implement the contract's routing,
            # scope or semantic guards. Audit it separately from complete heads.
            if "seed_matcher" in grammar["contract"]:
                adapter_seeds += 1
                try:
                    seed = parse_neuron(grammar["contract"]["seed_matcher"])
                    require({key for rule in seed.rules for key in rule.emit} == set(grammar["writes"]), f"{gid}: seed writes differ")
                    if execute:
                        for ex in grammar["examples"]:
                            acts = seed.activate(ex["context"])
                            require(bool(acts) == bool(ex["expect"]), f"{gid}: seed activation mismatch")
                            require(all(canonical(act.value) == canonical(ex["expect"]) for act in acts), f"{gid}: seed projection mismatch")
                            seed_examples += 1
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    errors.append(f"{gid}: seed execution error {exc}")
            continue
        require(grammar["runtime_support"] == "native", f"{gid}: unsupported status label")
        require(not grammar["requires"] and "neuron" in grammar, f"{gid}: native grammar hides adapter requirements")
        require(not set(grammar["writes"]) & PROTECTED, f"{gid}: writes protected fields")
        normalized = deepcopy(grammar["neuron"])
        normalized.pop("name", None)
        signatures[canonical(normalized)].append(gid)
        try:
            neuron = parse_neuron(grammar["neuron"])
            require({key for rule in neuron.rules for key in rule.emit} == set(grammar["writes"]), f"{gid}: declared/native writes differ")
            if not execute:
                continue
            for ex in grammar["examples"]:
                acts = neuron.activate(ex["context"])
                require(bool(acts) == bool(ex["expect"]), f"{gid}: {ex['polarity']} activation mismatch")
                require(all(canonical(act.value) == canonical(ex["expect"]) for act in acts), f"{gid}: {ex['polarity']} projection mismatch")
                executed += 1
            positive = next(ex for ex in grammar["examples"] if ex["polarity"] == "positive")
            head_spec = maps["heads"][grammar["head_ids"][0]]
            head = GrammarHead(neuron, operation=head_spec["operation"], strength=head_spec["initial_strength"])
            block = StoryformerBlock((head,), num_heads=1)
            original, _ = block.forward([Residual(row) for row in add_positions(positive["context"])])
            longer, _ = block.forward([Residual(row) for row in add_positions([*positive["context"], {"token": "UNSEEN_FUTURE"}])])
            require([row.view() for row in original] == [row.view() for row in longer[:len(original)]], f"{gid}: future changed prefix residuals")
            causal_checks += 1
            if head.operation == "suppress":
                _, trace = block.forward([Residual(row) for row in add_positions(positive["context"])])
                require(bool(trace) and all(item["delta"] < 0 for item in trace), f"{gid}: suppression did not subtract evidence")
                suppression_checks += 1
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            errors.append(f"{gid}: execution error {type(exc).__name__}: {exc}")
    for head in records["heads"]:
        require(head["operation"] in {"add", "suppress"}, f"{head['id']}: unsupported operation")
        require(set(head["attribute_ids"]) <= set(maps["attributes"]), f"{head['id']}: attribute reference")
        require(set(head["grammar_ids"]) <= set(maps["grammars"]), f"{head['id']}: grammar reference")
        for gid in head["grammar_ids"]:
            g = maps["grammars"][gid]
            require(head["reads"] == g["reads"] and head["writes"] == g["writes"], f"{head['id']}: grammar I/O mismatch")
            require(head["runtime_support"] == g["runtime_support"] and head["requires"] == g["requires"], f"{head['id']}: grammar capability mismatch")
    duplicate_neurons = [ids for ids in signatures.values() if len(ids) > 1]
    require(not duplicate_neurons, f"duplicate native neuron definitions: {duplicate_neurons}")
    return dict(valid=not errors, errors=errors, counts={kind: len(records[kind]) for kind in KINDS},
                native_examples_executed=executed, causal_prefix_checks=causal_checks,
                native_suppression_checks=suppression_checks,
                adapter_seed_matchers=adapter_seeds, adapter_seed_examples_executed=seed_examples,
                runtime_support=dict(Counter(g["runtime_support"] for g in records["grammars"])),
                required_capabilities=dict(Counter(req for g in records["grammars"] for req in g["requires"]).most_common()),
                operations=dict(Counter(h["operation"] for h in records["heads"])),
                attribute_types=dict(Counter(a["type"] for a in records["attributes"])),
                families=dict(sorted(Counter(a["family"] for a in records["attributes"]).items())),
                native_duplicate_definitions=duplicate_neurons,
                limits=["Native fixtures validate bounded seed behavior, not linguistic coverage or learned quality.",
                        "Adapter contracts are inspected data, not executed parsers or proven inference algorithms.",
                        "Adapter seed checks do not test the unsupported semantic guards or correlated routing.",
                        "Causal masking does not prove upstream annotations were created without hindsight."])


def encode_rows(rows):
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated files to sources without rewriting")
    parser.add_argument("--no-execute", action="store_true")
    args = parser.parse_args(argv)
    records = assemble()
    sources = json.loads((ROOT / "sources.json").read_text())
    report = validate(records, source_ids={row["id"] for row in sources}, execute=not args.no_execute)
    if not report["valid"]:
        print(json.dumps(report, indent=2))
        raise SystemExit(1)
    hashes = {}
    for kind in KINDS:
        content = encode_rows(records[kind])
        path = ROOT / f"{kind}.jsonl"
        hashes[path.name] = hashlib.sha256(content.encode()).hexdigest()
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"stale generated file: {path}")
        else:
            path.write_text(content)
    report["sha256"] = hashes
    if not args.check:
        (ROOT / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("valid", "counts", "runtime_support", "operations", "native_examples_executed", "causal_prefix_checks")}, indent=2))


if __name__ == "__main__":
    main()
