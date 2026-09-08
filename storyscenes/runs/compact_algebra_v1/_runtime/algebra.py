"""Compact, data-only authoring over the existing offline Storyscenes runtime.

Pattern + Pattern combines opportunities, not completed prose or a fixed route.
Pattern / n attenuates search attention; it never changes facts or legal moves.
Definitions are immutable; each build creates fresh state on physical carriers.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import itertools
import json
import math
import random
import re

from runtime import (Condition, Effect, Scene, Rule, WorldSpec, StoryError,
                     observe, tell, transfer, scene, validate_spec)

IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
STATE_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")
REF = re.compile(r"\$([A-Za-z][A-Za-z0-9_]*)")
BUILTINS = {"Observe", "Tell", "Transfer", "Lend", "Return", "Move", "Act"}


def fields(value, allowed, required=(), where="object"):
    if not isinstance(value, dict):
        raise StoryError(f"{where}: expected an object")
    extra, missing = set(value) - set(allowed), set(required) - set(value)
    if extra or missing:
        raise StoryError(f"{where}: unknown fields {sorted(extra)}, missing {sorted(missing)}")


def scalar(value):
    if value is not None and type(value) not in (str, bool, int, float):
        raise StoryError(f"Expected scalar, got {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise StoryError("Nonfinite scalar")
    return value


def conditions(value):
    """{key: scalar} means equality; {key: [op, scalar]} is an explicit test.

    A list of [key, op, scalar] triples also preserves repeated guards on one key.
    """
    if isinstance(value, dict):
        triples = [(k, *(v if isinstance(v, list) else ["eq", v])) for k, v in value.items()]
    elif isinstance(value, list):
        triples = value
    else:
        raise StoryError("Conditions require a map or a list of triples")
    result = []
    for triple in triples:
        if len(triple) != 3:
            raise StoryError(f"Invalid condition: {triple}")
        key, op, val = triple
        if not isinstance(key, str) or not STATE_KEY.fullmatch(key):
            raise StoryError(f"Invalid state key in condition: {key}")
        if op not in {"eq", "ne", "lt", "le", "gt", "ge"}:
            raise StoryError(f"Unsupported condition operation {op}")
        result.append(Condition(key, op, scalar(val)))
    return tuple(result)


@dataclass(frozen=True)
class Pattern:
    scenes: tuple[Scene, ...] = ()
    defaults: tuple[tuple[str, object], ...] = ()

    def __add__(self, other):
        if not isinstance(other, Pattern):
            return NotImplemented
        scenes = self.scenes + other.scenes
        if len({s.id for s in scenes}) != len(scenes):
            raise StoryError("Composition has duplicate scene IDs; bind a different instance name")
        defaults = dict(self.defaults)
        for key, value in other.defaults:
            if key in defaults and defaults[key] != value:
                raise StoryError(f"Conflicting kernel defaults: {key}")
            defaults[key] = value
        return Pattern(scenes, tuple(defaults.items()))

    def __truediv__(self, divisor):
        if type(divisor) not in (int, float) or not math.isfinite(divisor) or divisor <= 0:
            raise StoryError("Attention divisor must be finite and positive")
        return Pattern(tuple(replace(s, weight=s.weight / divisor) for s in self.scenes), self.defaults)


@dataclass(frozen=True)
class Kernel:
    """Serialized body avoids mutable definition dictionaries leaking across bindings."""
    roles: tuple[str, ...]
    body_json: str

    @classmethod
    def define(cls, roles, body):
        if not isinstance(roles, list) or any(not isinstance(r, str) or not IDENT.fullmatch(r) for r in roles):
            raise StoryError("Kernel roles must be identifier strings")
        if len(set(roles)) != len(roles):
            raise StoryError("Duplicate kernel roles")
        if not isinstance(body, dict) or not body:
            raise StoryError("A kernel body needs named opportunities")
        return cls(tuple(roles), json.dumps(body, ensure_ascii=False, allow_nan=False))

    def bind(self, args, namespace, library, stack=()):
        if len(args) != len(self.roles):
            raise StoryError(f"Expected roles {self.roles}, got {args}")
        values = dict(zip(self.roles, args))

        def substitute(value):
            if isinstance(value, str):
                if value.startswith("$") and value[1:] in values:
                    return deepcopy(values[value[1:]])
                def one(match):
                    if match[1] not in values:
                        raise StoryError(f"Unbound role {match[0]}")
                    if not isinstance(values[match[1]], str):
                        raise StoryError("Only string roles can be embedded in keys/text")
                    return values[match[1]]
                return REF.sub(one, value)
            if isinstance(value, list):
                return [substitute(v) for v in value]
            if isinstance(value, dict):
                result = {}
                for k, v in value.items():
                    key = substitute(k)
                    if not isinstance(key, str) or key in result:
                        raise StoryError("Role binding created a duplicate or non-string key")
                    result[key] = substitute(v)
                return result
            return value
        return compose(substitute(json.loads(self.body_json)), library, namespace, stack)


def compose(body, library=None, namespace="", stack=()):
    library = SHARED_KERNELS if library is None else library
    if not isinstance(body, dict):
        raise StoryError("compose/body must map instance IDs to opportunities")
    result = Pattern()
    for name, node in body.items():
        if not isinstance(name, str) or not IDENT.fullmatch(name):
            raise StoryError(f"Invalid instance ID {name!r}")
        sid = f"{namespace}.{name}" if namespace else name
        fields(node, ("op", "args", "actors", "when", "set", "inc", "copy", "summary",
                      "pivotal", "weight", "max_uses", "divide", "label"), ("op",), sid)
        op = node["op"]
        args = node.get("args", [])
        if not isinstance(args, list):
            raise StoryError(f"{sid}: args must be a list")
        if op in library:
            extra = set(node) - {"op", "args", "divide"}
            if extra:
                raise StoryError(f"{sid}: composite calls support op/args/divide only, got {extra}")
            if op in stack or len(stack) >= 12:
                raise StoryError(f"Recursive kernel expansion: {stack + (op,)}")
            pattern = library[op].bind(args, sid, library, stack + (op,))
        else:
            if op not in BUILTINS:
                raise StoryError(f"Unknown kernel {op} in {sid}")
            guards = conditions(node.get("when", {}))
            defaults = []
            kw = dict(summary=node.get("summary", ""), pivotal=node.get("pivotal", False),
                      weight=node.get("weight", 1.0))
            if type(kw['pivotal']) is not bool or not isinstance(kw['summary'], str):
                raise StoryError(f"{sid}: pivotal must be boolean and summary must be text")
            arity = {"Observe": 2, "Tell": 3, "Transfer": 3, "Lend": 3, "Return": 3, "Move": 3, "Act": 0}[op]
            if len(args) != arity or any(not isinstance(a, str) for a in args):
                raise StoryError(f"{sid}: {op} expects {arity} string args")
            if op != "Act" and set(node).intersection({"actors", "set", "inc", "copy", "label"}):
                raise StoryError(f"{sid}: use a separate Act for custom effects/actors")
            if op == "Observe":
                s = observe(sid, *args, when=guards, **kw)
                defaults = [(f"{args[0]}.knows.{args[1]}", None)]
            elif op == "Tell":
                s = tell(sid, *args, when=guards, **kw)
                defaults = [(f"{a}.knows.{args[2]}", None) for a in args[:2]]
            elif op == "Transfer":
                s = transfer(sid, *args, when=guards, **kw)
            elif op in {"Lend", "Return"}:
                giver, recipient, prop = args
                loan = f"{prop}.loaned_by"
                lender = giver if op == "Lend" else recipient
                s = transfer(sid, giver, recipient, prop,
                             when=(Condition(loan, "eq", None if op == "Lend" else lender),) + guards, **kw)
                s = replace(s, effects=s.effects + (Effect(loan, lender if op == "Lend" else None),))
                defaults = [(loan, None)]
            elif op == "Move":
                actor, prop, destination = args
                s = scene(sid, "Move", (actor, destination),
                          when=(Condition(f"{prop}.owner", "eq", actor),) + guards,
                          set_values={f"{prop}.location": destination}, **kw)
            else:
                actors = node.get('actors', [])
                if not isinstance(actors,list) or not actors or any(not isinstance(x,str) for x in actors):
                    raise StoryError(f'{sid}: Act needs a nonempty list of actor IDs')
                for key in ("set", "inc", "copy"):
                    if not isinstance(node.get(key, {}), dict):
                        raise StoryError(f"{sid}: {key} requires a state map")
                    for val in node.get(key, {}).values(): scalar(val)
                s = scene(sid, node.get("label", "Act"), actors, when=guards,
                          set_values=node.get("set"), increments=node.get("inc"), copies=node.get("copy"), **kw)
            uses = node.get("max_uses", 1)
            if type(uses) is not int or uses < 1:
                raise StoryError(f"{sid}: max_uses must be a positive integer")
            pattern = Pattern((replace(s, max_uses=uses),), tuple(defaults))
        result = result + pattern / node.get("divide", 1)
        if len(result.scenes) > 100:
            raise StoryError("Expanded pattern exceeds 100 scene opportunities")
    return result


def variations(document):
    vary = document.get("vary", {})
    if not isinstance(vary, dict):
        raise StoryError("vary maps dimension IDs to lists of state overrides")
    written = set()
    for name, cases in vary.items():
        if not IDENT.fullmatch(name) or not isinstance(cases, list) or not cases:
            raise StoryError(f"Invalid variation dimension {name}")
        keys = set()
        for case in cases:
            if not isinstance(case, dict): raise StoryError("Variation cases must be state maps")
            for val in case.values(): scalar(val)
            keys.update(case)
        if written.intersection(keys):
            raise StoryError("Independent variation dimensions cannot overwrite the same state key")
        written.update(keys)
    if math.prod(len(c) for c in vary.values()) > 64:
        raise StoryError("Prototype supports at most 64 initial configurations")
    return vary


def configurations(document):
    """Exhaustive finite premise space; seeds need not happen to cover every case."""
    vary = variations(document)
    return [dict(zip(vary, indexes)) for indexes in itertools.product(*(range(len(v)) for v in vary.values()))]


def build(document, seed=0, *, choices=None):
    fields(document, ("title", "premise", "entities", "vary", "kernels", "compose", "goal",
                      "rules", "premises", "outcomes", "labels", "prune"),
           ("title", "entities", "compose", "goal", "outcomes"), "world")
    if not isinstance(document['title'], str) or not document['title'].strip():
        raise StoryError("World title must be text")
    if not isinstance(document['entities'],dict) or not document['entities']:
        raise StoryError('World needs a map of physical entities')
    if not isinstance(document['outcomes'],list) or not document['outcomes'] or any(not isinstance(k,str) for k in document['outcomes']):
        raise StoryError('outcomes must be a nonempty list of state keys')
    if type(document.get('prune', True)) is not bool:
        raise StoryError('prune must be boolean')
    entities, initial = {}, {}
    for eid, ent in document["entities"].items():
        if not IDENT.fullmatch(eid): raise StoryError(f"Invalid carrier ID {eid}")
        fields(ent, ("name", "kind", "state"), ("name", "kind"), eid)
        if any(not isinstance(ent[k], str) or not ent[k] for k in ("name", "kind")):
            raise StoryError(f"{eid}: name and kind must be text")
        entities[eid] = {k: ent[k] for k in ("name", "kind")}
        for key, value in ent.get("state", {}).items():
            if not STATE_KEY.fullmatch(f'{eid}.{key}'):
                raise StoryError(f'Invalid embedded state field {eid}.{key}')
            initial[f"{eid}.{key}"] = scalar(value)
    library = dict(SHARED_KERNELS)
    for name, definition in document.get("kernels", {}).items():
        if not IDENT.fullmatch(name) or name in BUILTINS or name in SHARED_KERNELS:
            raise StoryError(f"Invalid or reserved kernel name {name}")
        fields(definition, ("roles", "body"), ("roles", "body"), name)
        library[name] = Kernel.define(definition["roles"], definition["body"])
    pattern = compose(document["compose"], library)
    for key, value in pattern.defaults:
        if not STATE_KEY.fullmatch(key): raise StoryError(f'Invalid automatic state slot {key}')
        initial.setdefault(key, value)  # explicit beliefs/loans always win
    rng = random.Random(seed)
    vary = variations(document)
    if choices is not None and set(choices) != set(vary):
        raise StoryError("Explicit choices must cover exactly the variation dimensions")
    for name, cases in vary.items():
        index = rng.randrange(len(cases)) if choices is None else choices[name]
        if type(index) is not int or not 0 <= index < len(cases):
            raise StoryError(f"Invalid case index for {name}")
        for case in cases:
            if set(case) - set(initial):
                raise StoryError(f"{name}: undeclared variation state {set(case) - set(initial)}")
        initial.update(cases[index])
    rules = []
    for name, rule in document.get("rules", {}).items():
        fields(rule, ("when", "must"), ("must",), name)
        rules.append(Rule(name, conditions(rule["must"]), conditions(rule.get("when", {}))))
    premises = document.get("premises", list(dict.fromkeys(k for cases in vary.values() for case in cases for k in case)))
    spec = WorldSpec(document['title'], deepcopy(entities), deepcopy(initial), pattern.scenes,
                     conditions(document['goal']), tuple(rules), deepcopy(document.get('labels')),
                     document.get('prune', True), tuple(premises), tuple(document['outcomes']))
    validate_spec(spec)
    # Runtime's prefix check is supplemented for built-in ownership/location semantics.
    for key, value in initial.items():
        if key.endswith((".owner", ".location", ".loaned_by")) and value is not None and value not in entities:
            raise StoryError(f"{key} must reference an existing physical carrier, got {value}")
    for s in spec.scenes:
        for effect in s.effects:
            if effect.op == 'set' and effect.key.endswith((".owner", ".location", ".loaned_by")) and effect.value is not None and effect.value not in entities:
                raise StoryError(f"{s.id}: invalid physical target {effect.value}")
    return spec


def compile_source(document):
    """Only trusted compiler code is executable; model output is a literal value."""
    return ("from algebra import build as build_world\n\nWORLD = " + repr(document)
            + "\n\ndef build(seed):\n    return build_world(WORLD, seed)\n")


def patch_world(document, patch):
    """Bounded named replacements; no positional array edits or whole-document writes."""
    fields(patch, ('edits',), ('edits',), 'world patch')
    edits = patch['edits']
    if not isinstance(edits, list) or not 1 <= len(edits) <= 8 or len(json.dumps(patch)) > 16000:
        raise StoryError("World patch exceeds bounded edit budget")
    updated = deepcopy(document)
    seen = set()
    for edit in edits:
        fields(edit, ('section', 'id', 'value'), ('section', 'id', 'value'), 'edit')
        section, key = edit['section'], edit['id']
        if (section, key) in seen: raise StoryError("Duplicate patch target")
        seen.add((section, key))
        if section in {'entities', 'kernels', 'compose', 'vary', 'rules'}:
            if not IDENT.fullmatch(key): raise StoryError("Invalid named patch target")
            updated.setdefault(section, {})[key] = deepcopy(edit['value'])
        elif section in {'goal', 'premises', 'outcomes'} and key == section:
            updated[section] = deepcopy(edit['value'])
        else:
            raise StoryError(f"Unsupported world patch target {section}/{key}")
    return updated


SHARED_KERNELS = {
    'DiscoverAndShare': Kernel.define(['observer','listener','fact'], {
        'notice': {'op':'Observe','args':['$observer','$fact']},
        'share': {'op':'Tell','args':['$observer','$listener','$fact']},
    }),
}
