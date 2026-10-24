"""Strict JSON boundary for typed capability worlds; never execute source strings."""
from dataclasses import fields, is_dataclass, replace
import json
import types
from typing import Union, get_args, get_origin, get_type_hints

from .core import Action, CapabilityError, Query, SCHEMA, WorldSpec, plain


def decode_type(annotation, value):
    origin, args = get_origin(annotation), get_args(annotation)
    if annotation is object:
        json.dumps(value, allow_nan=False)
        return value
    if origin in (Union, types.UnionType):
        for option in args:
            try:
                return decode_type(option, value)
            except (CapabilityError, TypeError, ValueError):
                pass
        raise CapabilityError("Value does not match any declared type")
    if annotation is type(None):
        if value is not None:
            raise CapabilityError("Expected null")
        return None
    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise CapabilityError("Expected array")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(decode_type(args[0], item) for item in value)
        if len(args) != len(value):
            raise CapabilityError("Tuple arity mismatch")
        return tuple(decode_type(t, v) for t, v in zip(args, value))
    if origin is dict or annotation is dict:
        if not isinstance(value, dict):
            raise CapabilityError("Expected object")
        key_type, value_type = args or (str, object)
        return {decode_type(key_type, k): decode_type(value_type, v) for k, v in value.items()}
    if origin is list:
        if not isinstance(value, list):
            raise CapabilityError("Expected array")
        return [decode_type(args[0], v) for v in value]
    if is_dataclass(annotation):
        if not isinstance(value, dict) or set(value) - {f.name for f in fields(annotation)}:
            raise CapabilityError(f"Unknown fields in {annotation.__name__}")
        hints = get_type_hints(annotation)
        try:
            return annotation(**{k: decode_type(hints[k], v) for k, v in value.items()})
        except TypeError as exc:
            raise CapabilityError(f"Missing/invalid fields in {annotation.__name__}") from exc
    if annotation is float and type(value) in (float, int):
        return float(value)
    if type(value) is not annotation:
        raise CapabilityError(f"Expected {annotation}, got {type(value).__name__}")
    return value


def world_from_data(registry, document):
    if not isinstance(document, dict) or set(document) - {f.name for f in fields(WorldSpec)}:
        raise CapabilityError("Unknown world fields")
    if document.get("schema") != SCHEMA:
        raise CapabilityError("An explicit capability schema field is required")
    data = dict(document)
    records = data.pop("records", None)
    if not isinstance(records, dict) or set(records) - set(registry.tables):
        raise CapabilityError("Unknown or missing record tables")
    typed = {}
    for table, rows in records.items():
        if not isinstance(rows, list):
            raise CapabilityError("Each table must be an array of records")
        typed[table] = tuple(decode_type(registry.tables[table], row) for row in rows)
    for key, cls in (("actions", Action), ("goal", Query)):
        if not isinstance(data.get(key), list):
            raise CapabilityError(f"Missing {key} array")
        data[key] = tuple(decode_type(cls, row) for row in data[key])
    # Query.value is deliberately generic; recover structured values from the
    # queried table's type so a saved measurement guard remains executable.
    def typed_query(query):
        record = registry.tables.get(query.table)
        annotation = get_type_hints(record).get(query.field) if record else None
        if is_dataclass(annotation) and query.value is not None:
            value = (tuple(decode_type(annotation, v) for v in query.value) if query.op == "in"
                     else decode_type(annotation, query.value))
            return replace(query, value=value)
        return query

    data["goal"] = tuple(typed_query(q) for q in data["goal"])
    data["actions"] = tuple(replace(a, requires=tuple(typed_query(q) for q in a.requires),
                                    intent=tuple(typed_query(q) for q in a.intent)) for a in data["actions"])
    try:
        spec = WorldSpec(records=typed, **data)
        registry.initial(spec)
    except TypeError as exc:
        raise CapabilityError("Invalid world fields") from exc
    return spec


def dumps(spec):
    return json.dumps(plain(spec), sort_keys=True, indent=2, allow_nan=False) + "\n"


def loads(registry, source):
    def reject_constant(value):
        raise CapabilityError(f"Nonfinite JSON constant: {value}")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise CapabilityError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result
    return world_from_data(registry, json.loads(source, parse_constant=reject_constant, object_pairs_hook=pairs))
