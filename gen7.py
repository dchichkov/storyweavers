#!/usr/bin/env python3
"""
gen7.py - MUD-like StoryWorld prototype.

gen7 is intentionally separate from gen6. It parses the existing kernel AST
format into structured story frames, applies those frames to a small persistent
world model, then renders prose from the event history. Kernels are treated as
world-level commands / memeplex annotations first, not as prose templates.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


CHARACTER_MARKERS = {"Character", "CharacterGroup", "Group"}
CHARACTER_TYPES = {
    "adult", "animal", "baby", "bear", "bee", "bird", "boy", "bunny",
    "cat", "child", "children", "dad", "dog", "duck", "father", "fish",
    "friend", "frog", "girl", "group", "man", "mom", "mommy", "mother",
    "mouse", "parent", "person", "rabbit", "turkey", "twin", "woman",
    "bees", "tree",
}
GENERIC_TYPES = {"animal", "bird", "group", "person"}
COMPOUNDS = {
    "secretroom": "secret room",
    "warmplace": "warm place",
    "whenalone": "when alone",
    "why sad": "why she was sad",
    "playground": "playground",
    "schoolyard": "school yard",
    "backyard": "backyard",
    "bedroom": "bedroom",
    "bathroom": "bathroom",
    "everyday": "every day",
}
PHASE_KEYS = (
    "state", "setup", "catalyst", "trigger", "problem", "conflict",
    "desire", "goal", "plan", "promise", "process", "action", "event",
    "reaction", "help", "solution", "result", "outcome", "insight",
    "moral", "lesson", "resolution", "transformation", "ending",
    "setting", "destination", "encounter", "twist",
)
STRUCTURE_CALLS = {
    "Quest", "Journey", "Cautionary", "Resolution", "Response",
    "Transformation", "Routine", "Story", "Adventure",
}
OBJECT_KEYS = {"object", "item", "thing", "target", "content", "gift"}
GOAL_OBJECT_KEYS = {"goal", "into", "to", "result", "outcome", "destination", "setting"}
PERSON_KEYS = {
    "hero", "protagonist", "rescuer", "rescued", "receiver", "recipient",
    "to", "from", "helper", "speaker", "listener", "owner", "patient",
}
EMOTION_MEMES = {
    "Joy", "Happy", "Happiness", "Sad", "Sadness", "Fear", "Scared",
    "Angry", "Anger", "Relief", "Lonely", "Kind", "Greed", "Guilt",
    "Trust", "Love", "Friendship", "Worried", "Proud", "Sorry", "Rested",
}
LOW_STATE_CALLS = {"lost", "broken", "stuck", "trapped", "hurt", "sad"}
BARE_NOUNS = {
    "inside", "outside", "home", "downstairs", "upstairs", "eyes", "hands",
    "feet", "hair", "teeth", "underground",
}


def words(name: Any) -> str:
    text = str(name or "")
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = text.replace("_", " ")
    text = " ".join(text.lower().split())
    return COMPOUNDS.get(text, text)


def cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def article(noun: str) -> str:
    n = noun.strip().lower()
    if not n:
        return "a"
    if n[0] in "aeiou":
        return "an"
    return "a"


def is_plural(noun: str) -> bool:
    head = noun.strip().split()[-1:] or [""]
    word = head[0].lower()
    return word in {"children", "people"} or (word.endswith("s") and not word.endswith("ss"))


def join(items: Iterable[str], conj: str = "and") -> str:
    vals = [i for i in items if i]
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0]
    if len(vals) == 2:
        return f"{vals[0]} {conj} {vals[1]}"
    return ", ".join(vals[:-1]) + f", {conj} {vals[-1]}"


def flatten(values: Iterable[Any]) -> list[Any]:
    out: list[Any] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, EvalResult):
            out.extend(value.values)
        elif isinstance(value, (list, tuple)):
            out.extend(flatten(value))
        else:
            out.append(value)
    return out


@dataclass
class Memeplex:
    name: str
    weight: float = 1.0
    parts: list["Memeplex"] = field(default_factory=list)

    def __add__(self, other: Any) -> "Memeplex":
        rhs = other if isinstance(other, Memeplex) else Memeplex(str(other))
        return Memeplex("+", self.weight + rhs.weight, [self, rhs])

    def __iadd__(self, other: Any) -> "Memeplex":
        rhs = other if isinstance(other, Memeplex) else Memeplex(str(other))
        self.parts.append(rhs)
        self.weight += rhs.weight
        return self

    def __truediv__(self, divisor: float) -> "Memeplex":
        d = float(divisor or 1.0)
        return Memeplex(self.name, self.weight / d, list(self.parts))

    def labels(self) -> list[str]:
        if self.parts:
            out: list[str] = []
            for part in self.parts:
                out.extend(part.labels())
            return out
        return [self.name]


@dataclass
class Entity:
    id: str
    kind: str = "physical"
    type: str = "thing"
    traits: list[str] = field(default_factory=list)
    location: str | None = None
    owner: str | None = None
    state: set[str] = field(default_factory=set)
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    relations: dict[str, dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(float)))

    def add_meme(self, name: str, amount: float) -> None:
        self.memes[name] += amount

    def add_relation(self, kind: str, other: "Entity", amount: float) -> None:
        self.relations[kind][other.id] += amount

    def pronoun(self, case: str = "subject") -> str:
        t = self.type.lower()
        if t in {"girl", "woman", "mother", "mom", "mommy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if t in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if t in {"group", "children", "people", "bees"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if t in {"bird", "dog", "cat", "mouse", "turkey", "bear", "bee", "fish", "frog", "rabbit", "bunny", "duck", "barrel", "tree"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class LowerExpr:
    name: str
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, list[Any]] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class Frame:
    kind: str
    actor: Entity | None = None
    patient: Entity | None = None
    objects: list[Entity] = field(default_factory=list)
    location: Entity | None = None
    cause: Any = None
    goal: Any = None
    result: Any = None
    concepts: list[Memeplex] = field(default_factory=list)
    meme_delta: dict[str, float] = field(default_factory=dict)
    salience: float = 1.0
    source: str = ""
    children: list["Frame"] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def scaled(self, factor: float) -> "Frame":
        self.salience *= factor
        for child in self.children:
            child.scaled(factor)
        return self


@dataclass
class EvalResult:
    frames: list[Frame] = field(default_factory=list)
    values: list[Any] = field(default_factory=list)

    def extend(self, other: "EvalResult") -> "EvalResult":
        self.frames.extend(other.frames)
        self.values.extend(other.values)
        return self


class StoryWorld:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.declarations: list[Entity] = []
        self.history: list[Frame] = []
        self.current_actor: Entity | None = None
        self.scene: Entity | None = None

    def entity(self, ent: Entity) -> Entity:
        existing = self.entities.get(ent.id)
        if existing is None:
            self.entities[ent.id] = ent
            existing = ent
            if ent.kind == "character":
                self.declarations.append(ent)
        else:
            if ent.traits:
                for trait in ent.traits:
                    if trait not in existing.traits:
                        existing.traits.append(trait)
            if existing.type == "thing" and ent.type != "thing":
                existing.type = ent.type
            if existing.kind != "character" and ent.kind == "character":
                existing.kind = "character"
                self.declarations.append(existing)
        return existing

    def physical(self, name: str, traits: Iterable[str] = ()) -> Entity:
        ent = Entity(words(name).replace(" ", "_"), "physical", words(name) or "thing", [words(t) for t in traits if words(t)])
        return self.entity(ent)

    def character(self, name: str, type_name: str, traits: Iterable[str] = ()) -> Entity:
        ent = Entity(name, "character", type_name or infer_type(name, ""), [words(t) for t in traits if words(t)])
        return self.entity(ent)

    def resolve(self, ent: Entity | None) -> Entity | None:
        if ent is None:
            return None
        return self.entity(ent)

    def apply(self, frame: Frame) -> None:
        frame.actor = self.resolve(frame.actor)
        frame.patient = self.resolve(frame.patient)
        frame.objects = [self.entity(o) for o in frame.objects]
        frame.location = self.resolve(frame.location)

        if frame.kind == "declare":
            if frame.actor is not None:
                self.current_actor = frame.actor
            return

        actor = frame.actor or self.current_actor
        frame.actor = actor
        if actor is not None:
            self.current_actor = actor

        for obj in frame.objects:
            frame.meta.setdefault("object_state", {})[obj.id] = sorted(obj.state)

        if frame.kind in {"find", "discover"}:
            for obj in frame.objects:
                obj.state.discard("lost")
                obj.state.discard("missing")
                obj.state.add("known")
                if actor is not None:
                    obj.owner = actor.id
                    actor.add_meme("Joy", 0.2)
        elif frame.kind in {"lose", "lost"}:
            for obj in frame.objects:
                obj.state.add("lost")
                if actor is not None:
                    obj.owner = actor.id
                    actor.add_meme("Sadness", 0.6)
        elif frame.kind in {"break", "broken"}:
            for obj in frame.objects:
                obj.state.add("broken")
            if actor is not None:
                actor.add_meme("Guilt", 0.2)
        elif frame.kind == "fix":
            for obj in frame.objects:
                obj.state.discard("broken")
                obj.state.add("fixed")
            if actor is not None:
                actor.add_meme("Joy", 0.3)
        elif frame.kind == "give":
            if frame.patient is not None:
                for obj in frame.objects:
                    obj.owner = frame.patient.id
                frame.patient.add_meme("Joy", 0.3)
        elif frame.kind in {"help", "rescue"} and actor is not None and frame.patient is not None:
            actor.add_relation("Help", frame.patient, 1.0)
            frame.patient.add_meme("Relief", 0.5)
        elif frame.kind == "friendship" and actor is not None and frame.patient is not None:
            actor.add_relation("Friendship", frame.patient, 1.0)
            frame.patient.add_relation("Friendship", actor, 1.0)
            actor.add_meme("Love", 0.4)
            frame.patient.add_meme("Love", 0.4)
        elif frame.kind == "emotion" and actor is not None:
            for concept in frame.concepts:
                for label in concept.labels():
                    actor.add_meme(normalize_meme(label), 0.6 * concept.weight)
        elif frame.kind == "fear" and actor is not None:
            actor.add_meme("Fear", 0.8)
        elif frame.kind in {"play", "hug"} and actor is not None:
            actor.add_meme("Joy", 0.4)
            if frame.patient is not None:
                actor.add_relation("Friendship", frame.patient, 0.2)

        self.history.append(frame)

    def apply_all(self, frames: Iterable[Frame]) -> "StoryWorld":
        for frame in frames:
            self.apply(frame)
        return self

    def object_phrase(self, obj: Entity, *, status: list[str] | None = None) -> str:
        status = status if status is not None else sorted(obj.state)
        noun = display_type(obj)
        if noun in BARE_NOUNS:
            return noun
        adj = ""
        if "lost" in status:
            adj = "lost "
        elif "broken" in status:
            adj = "broken "
        if obj.owner and obj.owner in self.entities:
            owner = self.entities[obj.owner]
            return f"{owner.pronoun('possessive')} {adj}{noun}"
        return f"the {adj}{noun}"


def normalize_meme(name: str) -> str:
    mapping = {
        "Happy": "Joy", "Happiness": "Joy", "Sad": "Sadness",
        "Scared": "Fear", "Angry": "Anger", "Sorry": "Guilt",
        "Worried": "Fear", "Rested": "Relief",
    }
    return mapping.get(name, cap(words(name)).replace(" ", ""))


def infer_type(name: str, explicit: str) -> str:
    if explicit:
        return words(explicit)
    n = words(name)
    aliases = {
        "mom": "mother", "mommy": "mother", "dad": "father",
        "daddy": "father", "old lady": "old lady", "baby bird": "bird",
    }
    if n in aliases:
        return aliases[n]
    if n in {"girl", "boy", "bird", "mouse", "turkey", "dog", "cat", "barrel", "bunny", "rabbit", "bee", "bees", "duck", "frog", "tree"}:
        return n
    return "person"


def display_type(ent: Entity) -> str:
    n = words(ent.id)
    if ent.kind == "physical":
        return words(ent.type or n)
    if ent.type in GENERIC_TYPES and n and n not in {"girl", "boy", "mom", "dad"}:
        return n
    return words(ent.type or "person")


def trait_text(ent: Entity) -> str:
    traits = [t for t in ent.traits if t and t not in {ent.type, display_type(ent)}]
    return " ".join(traits[:2])


def describe_character(ent: Entity, first: bool) -> str:
    typ = display_type(ent)
    traits = trait_text(ent)
    desc = f"{traits} {typ}".strip()
    plural = is_plural(desc)
    lead = (
        "Once upon a time, there were" if first and plural
        else "There were also" if plural
        else "Once upon a time, there was" if first
        else "There was also"
    )
    if ent.id.lower() == typ.lower() or ent.id in {"Girl", "Boy", "Mom", "Dad"}:
        return f"{lead} {desc}." if plural else f"{lead} {article(desc)} {desc}."
    little = "little " if typ in {"girl", "boy", "child"} else ""
    desc = f"{little}{desc}".strip()
    return f"{lead} {desc} named {ent.id}." if plural else f"{lead} {article(desc)} {desc} named {ent.id}."


class Parser:
    def __init__(self) -> None:
        self.world = StoryWorld()
        self.frames: list[Frame] = []
        self.current_actor: Entity | None = None

    def parse(self, source: str) -> list[Frame]:
        tree = ast.parse(source)
        for stmt in tree.body:
            res = self.eval_stmt(stmt)
            self.frames.extend(res.frames)
        return self.frames

    def eval_stmt(self, stmt: ast.stmt) -> EvalResult:
        if isinstance(stmt, ast.Expr):
            return self.eval_expr(stmt.value, context="top")
        return EvalResult()

    def eval_expr(self, node: ast.AST, context: str = "value", role: str = "") -> EvalResult:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self.eval_expr(node.left, context=context, role=role)
            right = self.eval_expr(node.right, context=context, role=role)
            return left.extend(right)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left = self.eval_expr(node.left, context=context, role=role)
            divisor = self.scalar(node.right)
            factor = 1.0 / divisor if divisor else 1.0
            for frame in left.frames:
                frame.scaled(factor)
            for value in left.values:
                if isinstance(value, Memeplex):
                    value.weight *= factor
                if isinstance(value, LowerExpr):
                    value.weight *= factor
            return left
        if isinstance(node, ast.Call):
            return self.eval_call(node, context=context, role=role)
        if isinstance(node, ast.Name):
            return EvalResult(values=[self.name_value(node.id, role=role)])
        if isinstance(node, ast.Constant):
            return EvalResult(values=[node.value])
        if isinstance(node, (ast.List, ast.Tuple)):
            out = EvalResult()
            for elt in node.elts:
                out.extend(self.eval_expr(elt, context=context, role=role))
            return out
        return EvalResult(values=[words(ast.unparse(node))])

    def scalar(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        return 1.0

    def name_value(self, name: str, role: str = "") -> Any:
        if name in self.world.entities:
            return self.world.entities[name]
        if name[:1].isupper():
            if role in OBJECT_KEYS or role in GOAL_OBJECT_KEYS:
                return self.world.physical(name)
            return Memeplex(name)
        return self.world.physical(name)

    def eval_call(self, node: ast.Call, context: str = "value", role: str = "") -> EvalResult:
        if not isinstance(node.func, ast.Name):
            return EvalResult()
        name = node.func.id

        if self.is_character_decl(node):
            ent = self.declare_character(node)
            frame = Frame("declare", actor=ent, source=name)
            self.current_actor = ent
            return EvalResult(frames=[frame], values=[ent])

        if name[:1].islower():
            return self.lower_call(node)

        arg_results = [self.eval_expr(arg, context=context, role=role) for arg in node.args]
        kw_results = {
            kw.arg: self.eval_expr(
                kw.value,
                context="phase" if kw.arg in PHASE_KEYS else "value",
                role=kw.arg or "",
            )
            for kw in node.keywords
            if kw.arg
        }
        child_frames = [f for r in arg_results for f in r.frames]
        for r in kw_results.values():
            child_frames.extend(r.frames)
        values = flatten([r.values for r in arg_results])
        kw_values = {k: flatten([r.values]) for k, r in kw_results.items()}

        if role == "goal" and name in {"Find", "Search", "Rescue", "Fix", "Return"}:
            return EvalResult(frames=child_frames, values=[LowerExpr(words(name), values, kw_values)])

        direct = self.direct_call(name, values, kw_values, child_frames, context=context, role=role)
        if direct is not None and name not in STRUCTURE_CALLS:
            return direct

        if self.has_meta_kwargs(kw_values) or name in STRUCTURE_CALLS:
            return self.structure_call(name, values, kw_values, child_frames)

        if context == "value" or role in OBJECT_KEYS or role in GOAL_OBJECT_KEYS:
            ent = self.world.physical(name, concept_labels(values))
            return EvalResult(frames=child_frames, values=[ent])
        return EvalResult(frames=child_frames, values=[Memeplex(name)])

    def is_character_decl(self, node: ast.Call) -> bool:
        return bool(
            isinstance(node.func, ast.Name)
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in CHARACTER_MARKERS
        )

    def declare_character(self, node: ast.Call) -> Entity:
        name = node.func.id
        marker = node.args[0].id if isinstance(node.args[0], ast.Name) else "Character"
        rest = list(node.args[1:])
        explicit_type = ""
        traits: list[str] = []
        if rest and isinstance(rest[0], ast.Name) and rest[0].id[:1].islower() and rest[0].id in CHARACTER_TYPES:
            explicit_type = rest.pop(0).id
        for arg in rest:
            traits.extend(node_labels(arg))
        type_name = "group" if marker in {"CharacterGroup", "Group"} else infer_type(name, explicit_type)
        ent = self.world.character(name, type_name, traits)
        for trait in traits:
            ent.add_meme(normalize_meme(trait), 0.4)
        return ent

    def lower_call(self, node: ast.Call) -> EvalResult:
        name = node.func.id
        args = [self.eval_expr(arg, role="object") for arg in node.args]
        kwargs = {kw.arg: self.eval_expr(kw.value, role=kw.arg or "") for kw in node.keywords if kw.arg}
        values = flatten([r.values for r in args])
        kw_values = {k: flatten([r.values]) for k, r in kwargs.items()}
        frames = [f for r in args for f in r.frames]
        for r in kwargs.values():
            frames.extend(r.frames)
        expr = LowerExpr(name, values, kw_values)
        return EvalResult(frames=frames, values=[expr])

    def has_meta_kwargs(self, kw_values: dict[str, list[Any]]) -> bool:
        return any(k in kw_values for k in PHASE_KEYS)

    def structure_call(self, name: str, values: list[Any], kw_values: dict[str, list[Any]], child_frames: list[Frame]) -> EvalResult:
        chars = [v for v in values if is_character(v)]
        participant_chars = [v for v in flatten(kw_values.get("participants", [])) if is_character(v)]
        actor = (
            chars[0] if chars
            else first_character(flatten(kw_values.get("hero", []) + kw_values.get("protagonist", [])))
            or (participant_chars[0] if participant_chars else None)
            or self.current_actor
        )
        if actor is not None:
            self.current_actor = actor
        frames: list[Frame] = []
        if name == "Routine":
            frames.append(Frame("routine", actor=actor, objects=objects_from(values[1:] + flatten(kw_values.get("object", [])), self.world), concepts=concepts_from(values), source=name, salience=0.8, meta={"participants": chars + participant_chars}))
        elif name == "Quest":
            goal = first_value(flatten(kw_values.get("goal", []) + kw_values.get("desire", []))) or first_value(values[1:])
            frames.append(Frame("want", actor=actor, goal=goal, concepts=[Memeplex(name)], source=name, salience=0.7))
            setting = first_entity(flatten(kw_values.get("setting", [])))
            if setting is not None:
                frames.append(Frame("scene", actor=actor, location=setting, source="setting", salience=0.35))
            encounter = first_character(flatten(kw_values.get("encounter", [])))
            if encounter is not None:
                frames.append(Frame("encounter", actor=actor, patient=encounter, source="encounter", salience=0.8))
        elif name == "Journey":
            destination = first_entity(flatten(kw_values.get("destination", []) + kw_values.get("setting", [])))
            frames.append(Frame("journey", actor=actor, patient=chars[1] if len(chars) > 1 else None, location=destination, concepts=[Memeplex(name)], source=name, salience=0.75, meta={"participants": chars + participant_chars}))
        elif name in {"Cautionary", "Lesson"}:
            frames.append(Frame("lesson", actor=actor, concepts=[Memeplex(name)], source=name, salience=0.6))
        elif name not in {"Response", "Resolution", "Transformation"}:
            frames.append(Frame("activity", actor=actor, concepts=[Memeplex(name)], source=name, salience=0.4))

        for frame in child_frames:
            if frame.actor is None and frame.kind not in {"declare", "scene"}:
                frame.actor = actor
        frames.extend(child_frames)
        skip = {"hero", "protagonist", "goal", "desire", "setting", "destination", "encounter"}
        for key in PHASE_KEYS:
            if key in skip:
                continue
            for value in kw_values.get(key, []):
                frames.extend(self.value_to_frames(key, value, actor))
        return EvalResult(frames=frames, values=[Memeplex(name)])

    def value_to_frames(self, key: str, value: Any, actor: Entity | None) -> list[Frame]:
        if isinstance(value, Frame):
            return [value]
        if isinstance(value, LowerExpr):
            return self.lower_expr_to_frames(value, actor)
        if isinstance(value, Entity):
            if key in {"location", "setting", "destination"}:
                return [Frame("scene", actor=actor, location=value, source=key, salience=0.4)]
            if key == "encounter" and value.kind == "character":
                return [Frame("encounter", actor=actor, patient=value, source=key, salience=0.8)]
            return [Frame("state", actor=actor, objects=[value], source=key, salience=0.35)]
        if isinstance(value, Memeplex):
            normalized = {normalize_meme(label) for label in value.labels()}
            if normalized & {"Joy", "Sadness", "Fear", "Anger", "Relief", "Guilt", "Love", "Lonely", "Kind"}:
                return [Frame("emotion", actor=actor, concepts=[value], source=key, salience=0.7)]
            return [Frame("annotation", actor=actor, concepts=[value], source=key, salience=0.2)]
        return []

    def lower_expr_to_frames(self, expr: LowerExpr, actor: Entity | None) -> list[Frame]:
        objs = objects_from(expr.args, self.world)
        name = expr.name.lower()
        locations = objects_from(flatten(expr.kwargs.get("location", [])), self.world)
        location = locations[0] if locations else None
        if name in {"lost", "lose"}:
            return [Frame("lost", actor=actor, objects=objs, location=location, source=expr.name, salience=expr.weight)]
        if name in {"broken", "break"}:
            return [Frame("broken", actor=actor, objects=objs, source=expr.name, salience=expr.weight)]
        if name in {"stuck", "trapped"}:
            return [Frame("problem", actor=actor, objects=objs, concepts=[Memeplex("stuck")], source=expr.name, salience=expr.weight)]
        return [Frame("annotation", actor=actor, objects=objs, concepts=[Memeplex(expr.name, expr.weight)], source=expr.name, salience=0.15 * expr.weight)]

    def direct_call(self, name: str, values: list[Any], kw_values: dict[str, list[Any]], child_frames: list[Frame], context: str, role: str) -> EvalResult | None:
        lname = name.lower()
        chars = [v for v in values if is_character(v)]
        fallback_actor = None if role in PHASE_KEYS else self.current_actor
        actor = chars[0] if chars else self.actor_from_kwargs(kw_values) or fallback_actor
        patient = chars[1] if len(chars) > 1 else first_character(flatten(
            kw_values.get("to", [])
            + kw_values.get("target", [])
            + kw_values.get("other", [])
            + kw_values.get("rescued", [])
            + kw_values.get("receiver", [])
            + kw_values.get("recipient", [])
        ))
        objects = objects_from([v for v in values if not is_character(v)] + flatten(v for k, v in kw_values.items() if k in OBJECT_KEYS), self.world)
        concepts = concepts_from(values + flatten(kw_values.values()))

        frame_kind = {
            "find": "find", "discover": "discover", "discovery": "discover",
            "want": "want", "desire": "want", "longing": "want",
            "lost": "lost", "loss": "lost", "lose": "lost",
            "search": "search", "ask": "ask", "request": "ask",
            "help": "help", "assist": "help", "comfort": "help",
            "give": "give", "gift": "give", "receive": "receive",
            "break": "break", "broken": "broken", "fix": "fix", "repair": "fix",
            "play": "play", "fear": "fear", "rescue": "rescue", "save": "rescue",
            "friendship": "friendship", "moral": "lesson", "lesson": "lesson",
            "refuse": "refuse", "refusal": "refuse", "apology": "apology",
            "forgiveness": "forgiveness", "return": "return", "transform": "transform",
            "problem": "problem", "reaction": "reaction", "emotion": "emotion",
            "encounter": "encounter", "meet": "encounter", "hug": "hug",
            "listen": "listen", "share": "share", "promise": "promise",
            "rest": "rest", "feed": "give", "warm": "warm", "capture": "capture",
            "catch": "capture", "take": "take", "shrink": "shrink", "grow": "grow",
            "dig": "dig", "plead": "ask", "smile": "emotion",
            "dialogue": "ask", "parting": "parting", "disturbance": "problem",
            "attemptsleep": "rest", "captureattempt": "capture",
            "kindness": "help", "magic": "annotation", "trade": "trade",
        }.get(lname)

        if frame_kind is None and name in EMOTION_MEMES:
            frame_kind = "emotion"
            concepts = [Memeplex(name)]

        if frame_kind is None:
            return None

        if frame_kind == "encounter" and len(chars) == 1 and self.current_actor is not None and self.current_actor != chars[0]:
            actor, patient = self.current_actor, chars[0]
        if frame_kind == "ask" and patient is None and len(chars) == 1 and self.current_actor is not None and self.current_actor != actor:
            patient = self.current_actor

        if frame_kind in {"emotion", "reaction"}:
            concepts = concepts or [Memeplex(name)]
            for value in flatten(kw_values.get("emotion", []) + kw_values.get("state", [])):
                if isinstance(value, Memeplex):
                    concepts.append(value)
        if frame_kind == "problem":
            lower_values = [value for value in values + flatten(kw_values.values()) if isinstance(value, LowerExpr)]
            frames = [] if lower_values else [Frame("problem", actor=actor, objects=objects, concepts=concepts, source=name)]
            for value in values + flatten(kw_values.values()):
                if isinstance(value, LowerExpr):
                    frames.extend(self.lower_expr_to_frames(value, actor))
            return EvalResult(frames=child_frames + frames, values=[Memeplex(name)])
        if frame_kind == "friendship" and len(chars) >= 2:
            actor, patient = chars[0], chars[1]
        if frame_kind == "receive" and actor is not None:
            objects = objects or objects_from(flatten(kw_values.values()), self.world)
        if frame_kind in {"shrink", "grow"} and chars:
            objects = objects_from([v for v in values if not is_character(v)], self.world)
        if frame_kind == "transform":
            result = first_value(flatten(kw_values.get("into", []) + kw_values.get("to", []) + values[1:]))
        else:
            result = first_value(flatten(kw_values.get("result", []) + kw_values.get("outcome", [])))
        positional_goal = first_value([v for v in values[2:] if not is_character(v)])
        goal = first_value(flatten(
            kw_values.get("goal", [])
            + kw_values.get("desire", [])
            + kw_values.get("ask", [])
            + kw_values.get("about", [])
        )) or positional_goal
        if frame_kind == "ask" and positional_goal is not None:
            objects = []
        frame = Frame(
            frame_kind,
            actor=actor,
            patient=patient,
            objects=objects,
            goal=goal,
            result=result,
            concepts=concepts,
            salience=0.15 if frame_kind == "annotation" else 1.0,
            source=name,
            meta={"participants": chars},
        )
        extra: list[Frame] = []
        if frame_kind == "encounter":
            for value in flatten(kw_values.get("state", [])):
                extra.extend(self.value_to_frames("state", value, patient or actor))
        if actor is not None:
            for child in child_frames:
                if child.actor is None and child.kind not in {"declare", "scene"}:
                    child.actor = actor
        if actor is not None:
            self.current_actor = actor
        return EvalResult(frames=child_frames + [frame] + extra, values=[Memeplex(name)])

    def actor_from_kwargs(self, kw_values: dict[str, list[Any]]) -> Entity | None:
        for key in ("actor", "hero", "protagonist", "rescuer", "helper", "speaker", "owner"):
            ent = first_character(flatten(kw_values.get(key, [])))
            if ent is not None:
                return ent
        return None


def is_character(value: Any) -> bool:
    return isinstance(value, Entity) and value.kind == "character"


def first_character(values: Iterable[Any]) -> Entity | None:
    for value in flatten(values):
        if is_character(value):
            return value
    return None


def first_entity(values: Iterable[Any]) -> Entity | None:
    for value in flatten(values):
        if isinstance(value, Entity):
            return value
    return None


def first_value(values: Iterable[Any]) -> Any:
    vals = flatten(values)
    return vals[0] if vals else None


def concepts_from(values: Iterable[Any]) -> list[Memeplex]:
    out: list[Memeplex] = []
    for value in flatten(values):
        if isinstance(value, Memeplex):
            out.append(value)
        elif isinstance(value, LowerExpr) and not objects_from([value], StoryWorld()):
            out.append(Memeplex(value.name, value.weight))
    return out


def concept_labels(values: Iterable[Any]) -> list[str]:
    labels: list[str] = []
    for value in flatten(values):
        if isinstance(value, Memeplex):
            labels.extend(words(x) for x in value.labels())
        elif isinstance(value, LowerExpr):
            labels.append(words(value.name))
        elif isinstance(value, str):
            labels.append(words(value))
    return [x for x in labels if x]


def objects_from(values: Iterable[Any], world: StoryWorld) -> list[Entity]:
    out: list[Entity] = []
    for value in flatten(values):
        if isinstance(value, Entity) and value.kind != "character":
            out.append(value)
        elif isinstance(value, LowerExpr):
            obj = world.physical(value.name, concept_labels(value.args + flatten(value.kwargs.values())))
            out.append(obj)
        elif isinstance(value, str) and value:
            out.append(world.physical(value))
        elif isinstance(value, Memeplex) and value.name not in EMOTION_MEMES:
            label = value.labels()[0] if value.labels() else value.name
            if words(label) not in {"joy", "sadness", "fear", "happy", "kind", "friendship"}:
                out.append(world.physical(label))
    unique: list[Entity] = []
    seen: set[str] = set()
    for obj in out:
        if obj.id not in seen:
            unique.append(obj)
            seen.add(obj.id)
    return unique


def node_labels(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return node_labels(node.left) + node_labels(node.right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        labels = [node.func.id]
        for arg in node.args:
            labels.extend(node_labels(arg))
        return labels
    if isinstance(node, (ast.List, ast.Tuple)):
        out: list[str] = []
        for elt in node.elts:
            out.extend(node_labels(elt))
        return out
    if isinstance(node, ast.Constant):
        return [str(node.value)]
    return []


def parse_story(kernel_src: str) -> list[Frame]:
    return Parser().parse(kernel_src)


def generate_world(kernel_src: str) -> StoryWorld:
    frames = parse_story(kernel_src)
    return StoryWorld().apply_all(frames)


def generate(kernel_src: str) -> str:
    return render(generate_world(kernel_src))


class Renderer:
    def __init__(self, world: StoryWorld) -> None:
        self.world = world
        self.last_subject: str | None = None

    def render(self) -> str:
        intro = [describe_character(ent, i == 0) for i, ent in enumerate(self.world.declarations[:4])]
        body: list[str] = []
        for frame in self.world.history:
            if frame.salience < 0.18:
                continue
            previous = self.last_subject
            text = self.render_frame(frame)
            if text:
                body.append(text)
            else:
                self.last_subject = previous
        sentences = self.dedupe(intro + body)
        if not sentences:
            return ""
        return " ".join(sentences)

    def dedupe(self, sentences: list[str]) -> list[str]:
        out: list[str] = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if out and out[-1].lower() == sentence.lower():
                continue
            out.append(sentence)
        return out

    def subj(self, ent: Entity | None) -> str:
        if ent is None:
            return "They"
        if self.last_subject == ent.id:
            return cap(ent.pronoun("subject"))
        self.last_subject = ent.id
        return ent.id

    def obj(self, ent: Entity | None) -> str:
        if ent is None:
            return "someone"
        if ent.kind == "character":
            return ent.id
        return self.world.object_phrase(ent)

    def participants(self, frame: Frame) -> str:
        chars = [c for c in frame.meta.get("participants", []) if is_character(c)]
        if not chars and frame.actor is not None:
            chars = [frame.actor]
            if frame.patient is not None:
                chars.append(frame.patient)
        return join([c.id for c in chars])

    def objs(self, frame: Frame) -> str:
        parts = []
        for obj in frame.objects:
            status = frame.meta.get("object_state", {}).get(obj.id)
            parts.append(self.world.object_phrase(obj, status=status))
        return join(parts)

    def concepts(self, frame: Frame) -> list[str]:
        labels: list[str] = []
        for concept in frame.concepts:
            labels.extend(words(x) for x in concept.labels())
        return [x for x in labels if x and x not in {"routine", "quest", "cautionary"}]

    def render_frame(self, frame: Frame) -> str:
        a = frame.actor
        p = frame.patient
        subject = self.subj(a)
        objects = self.objs(frame)
        concepts = self.concepts(frame)

        if frame.kind == "routine":
            if any(c in {"friendship"} for c in concepts):
                return "Every day, the friends played together."
            object_names = [display_type(o) for o in frame.objects]
            party = self.participants(frame) or subject
            if "play" in object_names or "play" in concepts:
                play_obj = next((o for o in frame.objects if display_type(o) not in {"play", "friends"}), None)
                if "friends" in object_names:
                    loc = next((o.traits[0] for o in frame.objects if display_type(o) == "play" and o.traits), "")
                    place = f" in {self.world.object_phrase(self.world.physical(loc))}" if loc else ""
                    return f"Every day, {party} played with friends{place}."
                return f"Every day, {party} played with {self.obj(play_obj)}." if play_obj else f"Every day, {party} played."
            if "jump" in object_names:
                return f"Every day, {party} loved to jump."
            if "chores" in object_names:
                return f"Every day, {party} did chores."
            if objects:
                return f"Every day, {subject} spent time with {objects}."
            return f"Every day, {subject} had a familiar routine."
        if frame.kind == "scene" and frame.location:
            return f"The story moved to {self.obj(frame.location)}."
        if frame.kind == "journey":
            party = self.participants(frame) or subject
            dest = self.obj(frame.location) if frame.location else "somewhere new"
            if dest == "underground":
                return f"{party} went underground."
            return f"{party} went to {dest}."
        if frame.kind == "want":
            goal = phrase(frame.goal, self.world) or objects or (concepts[0] if concepts else "something special")
            if isinstance(frame.goal, LowerExpr) and frame.goal.name in {"find", "search", "rescue", "fix", "return", "retrieve"}:
                return f"{subject} wanted to {goal}."
            return f"{subject} wanted {goal}."
        if frame.kind in {"find", "discover"}:
            return f"{subject} found {objects}." if objects else f"{subject} found something new."
        if frame.kind in {"lose", "lost"}:
            where = ""
            if frame.location is not None:
                loc = display_type(frame.location)
                if loc == "bottom" and frame.location.traits:
                    where = f" at the bottom of {self.world.object_phrase(self.world.physical(frame.location.traits[0]))}"
                else:
                    where = f" near {self.obj(frame.location)}"
            if objects and a:
                return f"{subject} lost {objects}{where} and felt sad."
            if p:
                return f"{subject} lost {self.obj(p)} and felt sad."
            return f"{cap(objects)} was lost{where}." if objects else ""
        if frame.kind == "search":
            return f"{subject} looked everywhere for {objects}." if objects else f"{subject} searched carefully."
        if frame.kind == "ask":
            target = self.obj(p) if p else ""
            thing = objects or phrase(frame.goal, self.world)
            if target and thing:
                if isinstance(frame.goal, LowerExpr) and frame.goal.name == "find":
                    return f"{subject} asked {target} to {thing}."
                if isinstance(frame.goal, LowerExpr) and frame.goal.name == "retrieve":
                    return f"{subject} asked {target} to {thing}."
                preposition = "about" if frame.source.lower() == "dialogue" else "for"
                return f"{subject} asked {target} {preposition} {thing}."
            if target:
                return f"{subject} asked {target} for help."
            return f"{subject} asked for help."
        if frame.kind in {"help", "rescue"}:
            target = self.obj(p) if p else (objects or "someone")
            verb = "rescued" if frame.kind == "rescue" else "helped"
            if frame.kind == "rescue" and a is not None and a.pronoun("subject") == "it":
                return f"{a.id} rescued {target}."
            if frame.source.lower() == "kindness" and p is None and not objects:
                name = a.id if a is not None else subject
                copula = "were" if a is not None and is_plural(display_type(a)) else "was"
                return f"{name} {copula} kind."
            if p is None and not objects and frame.kind == "help":
                return f"{subject} helped."
            return f"{subject} {verb} {target}."
        if frame.kind == "give":
            target = self.obj(p) if p else "someone"
            return f"{subject} gave {objects or 'something'} to {target}."
        if frame.kind == "receive":
            return f"{subject} received {objects or 'something'}."
        if frame.kind in {"break", "broken"}:
            return f"{cap(objects or 'Something')} broke."
        if frame.kind == "fix":
            return f"{subject} fixed {objects or 'it'}."
        if frame.kind == "play":
            if p:
                return f"{subject} played with {self.obj(p)}."
            return f"{subject} played with {objects}." if objects else f"{subject} played happily."
        if frame.kind == "fear":
            return f"{subject} felt scared."
        if frame.kind == "friendship":
            party = self.participants(frame)
            if party and len(frame.meta.get("participants", [])) > 2:
                return f"{party} became good friends."
            if a and p:
                return f"{a.id} and {p.id} became good friends."
            return "They became good friends."
        if frame.kind == "lesson":
            topic = join([c for c in concepts if c not in {"lesson", "moral"}])
            return f"{subject} learned an important lesson about {topic}." if topic else f"{subject} learned an important lesson."
        if frame.kind == "refuse":
            return f"{subject} said no."
        if frame.kind == "apology":
            return f"{subject} said sorry."
        if frame.kind == "forgiveness":
            return f"{subject} forgave {self.obj(p)}." if p else f"{subject} forgave them."
        if frame.kind == "return":
            return f"{subject} returned {objects or 'home'}."
        if frame.kind == "transform":
            target = phrase(frame.result, self.world)
            return f"{cap(objects or 'Something')} turned into {target}." if target else f"{cap(objects or 'Something')} changed."
        if frame.kind == "problem":
            if objects:
                return f"There was a problem with {objects}."
            if concepts:
                return f"{subject} had a problem: {join(concepts)}."
            return f"{subject} had a problem."
        if frame.kind in {"reaction", "emotion"}:
            if frame.kind == "reaction":
                if "cough" in concepts and "cover" in concepts:
                    poss = a.pronoun("possessive") if a is not None else "their"
                    return f"{subject} coughed and covered {poss} eyes."
                if "reprimand" in concepts:
                    return f"{subject} was angry and scolded them."
            feeling = join([emotion_word(c) for c in concepts])
            party = self.participants(frame)
            if frame.kind == "emotion" and party and len(frame.meta.get("participants", [])) > 1:
                return f"{party} felt {feeling}." if feeling else f"{party} felt a lot of feelings."
            return f"{subject} felt {feeling}." if feeling else f"{subject} felt a lot of feelings."
        if frame.kind == "encounter":
            return f"{subject} met {self.obj(p)}." if p else f"{subject} met someone."
        if frame.kind == "hug":
            party = self.participants(frame)
            if party and len(frame.meta.get("participants", [])) > 2:
                return f"{party} shared a warm hug."
            return f"{subject} hugged {self.obj(p)}." if p else f"{subject} got a warm hug."
        if frame.kind == "parting":
            party = self.participants(frame)
            if party and p:
                return f"{party} said goodbye with a smile." if objects else f"{party} said goodbye."
            return f"{subject} said goodbye."
        if frame.kind == "listen":
            return f"{subject} listened carefully."
        if frame.kind == "share":
            return f"{subject} shared {objects or 'what they had'}."
        if frame.kind == "promise":
            if a is not None and a.pronoun("subject") == "it":
                return f"{a.id} made a promise."
            return f"{subject} made a promise."
        if frame.kind == "rest":
            return f"{subject} rested for a while."
        if frame.kind == "warm":
            return f"{subject} warmed {objects or 'up'}."
        if frame.kind == "capture":
            if frame.source.lower() == "captureattempt":
                return f"{subject} tried to catch {objects or self.obj(p)}."
            return f"{subject} caught {objects or self.obj(p)}."
        if frame.kind == "trade":
            return f"{subject} traded {objects}." if objects else f"{subject} made a trade."
        if frame.kind == "take":
            return f"{subject} took {objects or 'it'}."
        if frame.kind == "shrink":
            return f"{cap(objects or self.obj(a))} became small."
        if frame.kind == "grow":
            return f"{cap(objects or self.obj(a))} grew big again."
        if frame.kind == "dig":
            return f"{subject} dug carefully."
        return ""


def emotion_word(label: str) -> str:
    mapping = {
        "joy": "happy", "happy": "happy", "happiness": "happy",
        "sad": "sad", "sadness": "sad", "fear": "scared",
        "scared": "scared", "angry": "angry", "anger": "angry",
        "relief": "relieved", "guilt": "sorry", "sorry": "sorry",
        "ashamed": "ashamed", "worried": "worried", "lonely": "lonely",
        "rested": "rested", "full": "full",
    }
    return mapping.get(label, label)


def phrase(value: Any, world: StoryWorld) -> str:
    if isinstance(value, Entity):
        return value.id if value.kind == "character" else world.object_phrase(value)
    if isinstance(value, Memeplex):
        return join(words(x) for x in value.labels())
    if isinstance(value, LowerExpr):
        vals = [phrase(v, world) for v in value.args]
        if value.name in {"find", "search", "rescue", "fix", "return", "retrieve"}:
            verb = "look for" if value.name == "search" else value.name
            return f"{verb} {join(vals)}".strip()
        return f"{words(value.name)} {join(vals)}".strip()
    if isinstance(value, str):
        return words(value)
    return ""


def render(world: StoryWorld) -> str:
    return Renderer(world).render()


def load_story(story_id: str) -> dict[str, Any]:
    dataset, _, line = story_id.partition(":")
    if not dataset or not line:
        raise ValueError("story id must look like data00:123")
    path = Path(__file__).parent / "TinyStories_kernels" / f"{dataset}.kernels.jsonl"
    with path.open() as f:
        for i, raw in enumerate(f):
            if i == int(line):
                return json.loads(raw)
    raise ValueError(f"{story_id} not found")


def main() -> None:
    ap = argparse.ArgumentParser(description="gen7 MUD-like story prototype")
    ap.add_argument("--story-id", help="Generate one TinyStories kernel by id, e.g. data00:18697")
    ap.add_argument("--kernel", help="Generate from an inline kernel string")
    ap.add_argument("--world", action="store_true", help="Print a compact world dump too")
    args = ap.parse_args()

    if args.story_id:
        record = load_story(args.story_id)
        kernel = record.get("kernel", "") or ""
        print(generate(kernel))
        if args.world:
            world = generate_world(kernel)
            print(json.dumps({
                "entities": {k: {"kind": v.kind, "type": v.type, "state": sorted(v.state), "memes": dict(v.memes)} for k, v in world.entities.items()},
                "frames": [f.kind for f in world.history],
            }, indent=2))
        return
    if args.kernel:
        print(generate(args.kernel))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
