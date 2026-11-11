"""Readable, bounded grammar proposals and a shared typed feature vocabulary."""

from copy import deepcopy
import re

from .grammar import GrammarNeuron, Lookup, OneOf, Pattern, Present, Ref, Rule, canonical
from .transformer import PROTECTED, SEMANTIC_FIELDS


TYPES = {"boolean", "string", "number", "array", "object", "entity_ref", "json"}


def value_type(value):
    if type(value) is bool:
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "json"


def check_value(value, definition):
    canonical(value)
    kind = definition["type"]
    if value is None or kind == "json":
        return
    if kind == "entity_ref":
        if not isinstance(value, str) or not re.fullmatch(r"e[1-9]\d*", value):
            raise ValueError("entity_ref requires a span/ordinal eN ID")
    elif value_type(value) != kind:
        raise ValueError(f"expected {kind}, received {value_type(value)}")


def neurons(model):
    """Yield unique objects, preserving intentionally shared neurons."""
    seen = set()
    for neuron in [*(head.neuron for layer in model.layers for head in layer.heads if head),
                   *model.projection.neurons.values()]:
        if id(neuron) not in seen:
            seen.add(id(neuron))
            yield neuron


def registry_for(model, documents=()):
    registry = {name: dict(type="string", description=name.replace("_", " "), origin="schema")
                for name in ("token", *SEMANTIC_FIELDS, "lemma", "entity_name", "event_id", "event_type",
                             "actor", "factuality", "surface", "kind")}
    for name in ("entity_id", "actor_id", "recipient_id"):
        registry[name] = dict(type="entity_ref", description=name.replace("_", " "), origin="schema")
    for name, kind in (("patients", "array"), ("instruments", "array"), ("attributes", "array"),
                       ("position", "object"), ("index", "number"), ("start", "number"), ("end", "number")):
        registry[name] = dict(type=kind, description=name, origin="schema")
    registry.update(deepcopy(model.features))
    for document in documents:
        for record in document:
            for name, value in record.items():
                if name not in registry:
                    registry[name] = dict(type=value_type(value), description=name, origin="observed")
                if value is not None:
                    if registry[name]["type"] == "json" and registry[name]["origin"] == "observed":
                        registry[name]["type"] = value_type(value)
                    check_value(value, registry[name])
    for neuron in neurons(model):
        for rule in neuron.rules:
            for name, value in rule.emit.items():
                if name not in registry:
                    kind = "json" if isinstance(value, (Ref, Lookup)) else value_type(value)
                    registry[name] = dict(type=kind, description=f"Projected by {neuron.name}", origin="learned")
    return registry


def encode(value):
    if isinstance(value, Ref):
        return {"$ref": value.path}
    if isinstance(value, Lookup):
        return {"$lookup": dict(table=value.table, key=encode(value.key))}
    if isinstance(value, Present):
        return {"$present": True}
    if isinstance(value, OneOf):
        return {"$one_of": [encode(item) for item in value.values]}
    if isinstance(value, Pattern):
        result = dict(kind=value.kind)
        if value.kind == "token":
            result["tests"] = encode(value.tests)
            if value.bind:
                result["bind"] = value.bind
        else:
            result["children"] = [encode(child) for child in value.children]
        if value.kind == "alt":
            result["weights"] = list(value.weights)
        if value.kind == "repeat":
            result.update(minimum=value.minimum, maximum=value.maximum)
        return result
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(item) for item in value]
    return value


def neuron_spec(neuron):
    return dict(name=neuron.name, rules=[dict(pattern=encode(rule.pattern), emit=encode(rule.emit), weight=rule.weight)
                                        for rule in neuron.rules], tables=deepcopy(neuron.tables),
                max_states=neuron.max_states)


def parse_neuron(spec, *, context_size=256, max_states=20000):
    """Decode data only; forbid extra operations and bound the proposed syntax."""
    if not isinstance(spec, dict) or set(spec) != {"name", "rules", "tables", "max_states"}:
        raise ValueError("neuron needs name, rules, tables and max_states")
    if not isinstance(spec["name"], str) or not spec["name"].strip() or len(spec["name"]) > 100:
        raise ValueError("invalid neuron name")
    if not isinstance(spec["rules"], list) or len(spec["rules"]) > 64 or not isinstance(spec["tables"], dict):
        raise ValueError("a neuron needs at most 64 rules and declared KV tables")
    if any(not isinstance(table, dict) for table in spec["tables"].values()):
        raise ValueError("KV tables must be objects")
    if type(spec["max_states"]) is not int or not 1 <= spec["max_states"] <= max_states:
        raise ValueError("proposal cannot increase the matching budget")
    budget = 512

    def decode(value, depth=0):
        nonlocal budget
        budget -= 1
        if budget < 0 or depth > 24:
            raise ValueError("proposal syntax budget exceeded")
        if isinstance(value, list):
            return [decode(item, depth + 1) for item in value]
        if not isinstance(value, dict):
            canonical(value)
            return value
        if set(value) == {"$ref"}:
            path = value["$ref"]
            if not isinstance(path, str) or not re.fullmatch(r"[A-Za-z_][\w]*(?:\.[A-Za-z_0-9][\w]*)+", path):
                raise ValueError("invalid capture reference")
            return Ref(path)
        if set(value) == {"$present"} and value["$present"] is True:
            return Present()
        if set(value) == {"$one_of"} and isinstance(value["$one_of"], list):
            return OneOf(tuple(decode(item, depth + 1) for item in value["$one_of"]))
        if set(value) == {"$lookup"}:
            lookup = value["$lookup"]
            if not isinstance(lookup, dict) or set(lookup) != {"table", "key"} or lookup["table"] not in spec["tables"]:
                raise ValueError("lookup requires a declared table and key")
            return Lookup(lookup["table"], decode(lookup["key"], depth + 1))
        if any(key.startswith("$") for key in value):
            raise ValueError("unknown grammar operand")
        return {key: decode(item, depth + 1) for key, item in value.items()}

    def pattern(value, depth=0):
        nonlocal budget
        budget -= 1
        if budget < 0 or depth > 16 or not isinstance(value, dict):
            raise ValueError("invalid or excessive pattern")
        kind = value.get("kind")
        allowed = {"token": {"kind", "tests", "bind"}, "seq": {"kind", "children"},
                   "alt": {"kind", "children", "weights"},
                   "repeat": {"kind", "children", "minimum", "maximum"}}
        if kind not in allowed or set(value) - allowed[kind]:
            raise ValueError("unknown pattern operation or field")
        if kind == "token":
            tests = value.get("tests", {})
            bind = value.get("bind")
            if not isinstance(tests, dict) or (bind is not None and
                    (not isinstance(bind, str) or not re.fullmatch(r"[A-Za-z_]\w*", bind))):
                raise ValueError("invalid token tests or capture")
            return Pattern(kind, tests=decode(tests), bind=bind)
        children = value.get("children")
        if not isinstance(children, list) or len(children) > 64:
            raise ValueError("pattern children must be a bounded list")
        children = tuple(pattern(child, depth + 1) for child in children)
        if kind == "repeat":
            low, high = value.get("minimum"), value.get("maximum")
            if type(low) is not int or type(high) is not int or not 0 <= low <= high <= context_size:
                raise ValueError("repeat must be bounded by the context size")
            return Pattern(kind, children=children, minimum=low, maximum=high)
        return Pattern(kind, children=children, weights=tuple(value.get("weights", ())))

    rules = []
    for rule in spec["rules"]:
        if not isinstance(rule, dict) or set(rule) != {"pattern", "emit", "weight"}:
            raise ValueError("rule needs pattern, emit and positive weight")
        rules.append(Rule(pattern(rule["pattern"]), decode(rule["emit"]), rule["weight"]))
    canonical(spec["tables"])
    return GrammarNeuron(spec["name"], tuple(rules), deepcopy(spec["tables"]), spec["max_states"])


def rebind_feature(model, source, target, value, registry):
    """Atomically rewire positive boolean detectors, including every consumer.

    A binding to pos='v' reuses an existing categorical feature; a binding to a
    new boolean=True names the detector. General value transformations abstain.
    """
    if source == target or source not in registry or target not in registry:
        raise ValueError("binding requires distinct declared source and target features")
    if registry[source]["type"] != "boolean" or registry[source]["origin"] != "learned" or source in PROTECTED:
        raise ValueError("only learned boolean detectors can be rebound")
    check_value(value, registry[target])
    if value is None or target in PROTECTED:
        raise ValueError("cannot bind a detector to an unknown or protected value")

    def transform(item):
        if isinstance(item, Ref):
            parts = item.path.split(".")
            if len(parts) > 1 and parts[1] == source:
                if registry[target]["type"] != "boolean" or value is not True:
                    raise ValueError("categorical rebinding cannot rewrite a value-copy reference")
                parts[1] = target
            return Ref(".".join(parts))
        if isinstance(item, Lookup):
            return Lookup(item.table, transform(item.key))
        if isinstance(item, dict):
            return {key: transform(part) for key, part in item.items()}
        if isinstance(item, (tuple, list)):
            return [transform(part) for part in item]
        return item

    def fields(items):
        result = {key: transform(part) for key, part in items.items() if key != source}
        if source in items:
            if items[source] is not True:
                raise ValueError("rebinding supports positive boolean writes/tests only")
            if target in result and canonical(result[target]) != canonical(value):
                raise ValueError("feature rebinding would merge conflicting tests or writes")
            result[target] = deepcopy(value)
        return result

    def pattern(item):
        return Pattern(item.kind, children=tuple(pattern(child) for child in item.children),
                       tests=fields(item.tests), bind=item.bind, weights=item.weights,
                       minimum=item.minimum, maximum=item.maximum)

    for neuron in neurons(model):
        for rule in neuron.rules:
            rule.pattern, rule.emit = pattern(rule.pattern), fields(rule.emit)
    registry[source]["binding"] = dict(feature=target, value=deepcopy(value))
