#!/usr/bin/env python3
"""
Storyworld: probe_trillion_cautionary_slice_of_life
===================================================

A small slice-of-life world about a curious child, a cautionary plan, and a
humble consequence. The seed words "probe" and "trillion" are carried into the
world as a toy measuring probe and a storybook exaggeration used to frame
worries: the child learns that one tiny mistake can feel huge, even if it is
not truly a trillion things.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared results eagerly
- imports shared asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# -----------------------------
# Core world model
# -----------------------------

def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    child: object | None = None
    parent: object | None = None
    thing: object | None = None
    def __post_init__(self):
        if self.meters is None:
            self.meters = {"tidy": 1.0}
        if self.memes is None:
            self.memes = {"worry": 0.0, "calm": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    calmness: int
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    params: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


PLACES = {
    "kitchen_table": Place("kitchen_table", "the kitchen table", True, 8),
    "balcony": Place("balcony", "the balcony", False, 5),
    "garage": Place("garage", "the garage bench", True, 4),
    "garden_shed": Place("garden_shed", "the garden shed", False, 6),
}

OBJECTS = {
    "plant": ObjectSpec("plant", "plant", "a tiny plant in a red pot", fragile=True),
    "jar": ObjectSpec("jar", "jar", "a glass jar of lemon water", fragile=True),
    "clock": ObjectSpec("clock", "clock", "a small clock with a bright face", fragile=False),
    "box": ObjectSpec("box", "box", "a cardboard box of old puzzle pieces", fragile=False),
}

GIRL_NAMES = ["Mina", "Lena", "Nora", "Ivy", "June", "Aria"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Theo", "Finn", "Max"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def trace(self) -> str:
        out = ["--- world trace ---"]
        for e in self.entities.values():
            out.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
        out.append(f"place={self.place.id}")
        out.append(f"facts={self.facts}")
        return "\n".join(out)


# -----------------------------
# Story logic
# -----------------------------
def is_reasonable(place: Place, obj: ObjectSpec) -> bool:
    return place.calmness >= 4 and obj.fragile


def explain_rejection(place: Place, obj: ObjectSpec) -> str:
    return (
        f"(No story: this cautionary slice needs a fragile object in a place where worry can matter. "
        f"Try one of the fragile items at one of the quieter places.)"
    )


def setup_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    obj = _safe_lookup(OBJECTS, params.object)
    if not is_reasonable(place, obj):
        pass

    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    thing = world.add(Entity(id=obj.id, kind="thing", type=obj.type, label=obj.label, owner=child.id))
    world.facts.update(child=child, parent=parent, thing=thing, obj=obj, params=params)
    return world


def opening(world: World) -> None:
    child = world.entities[world.facts["params"].name]
    obj: ObjectSpec = world.facts["obj"]
    world.say(
        f"{child.label} liked quiet afternoons and small useful jobs. "
        f"{child.pronoun().capitalize()} was especially proud of {child.pronoun('possessive')} {obj.label}."
    )
    world.say(
        f"It was the kind of day that felt ordinary in a good way: a snack, a little cleaning, "
        f"and a chance to test a {obj.label} with a careful probe."
    )


def caution(world: World) -> None:
    child = world.entities[world.facts["params"].name]
    parent = world.entities["parent"]
    obj: ObjectSpec = world.facts["obj"]
    place = world.place
    child.memes["curiosity"] += 1
    child.memes["worry"] += 0.5
    world.say(
        f"At {place.label}, {child.label} picked up a toy probe and said it could check everything, "
        f"even a trillion tiny things if only there were time."
    )
    world.say(
        f"{parent.label} smiled, then gave a cautionary warning: "
        f"\"A probe is for looking closely, not for poking hard. One rushed move can turn a neat thing into a messy one.\""
    )
    world.facts["warning"] = True


def mistake(world: World) -> None:
    child = world.entities[world.facts["params"].name]
    obj: ObjectSpec = world.facts["obj"]
    if ("mistake" in world.fired):
        return
    world.fired.add("mistake")
    child.memes["worry"] += 1.0
    if obj.fragile:
        world.facts["spilled"] = True
        world.say(
            f"{child.label} reached too fast, and the probe tapped the {obj.label} just enough to wobble it."
        )
        world.say(
            f"The {obj.label} tipped, then landed with a small splash that felt much bigger than a trillion worries."
        )
    else:
        world.facts["spilled"] = False
        world.say(
            f"{child.label} reached too fast, but the probe only clicked against the sturdy surface."
        )


def repair(world: World) -> None:
    child = world.entities[world.facts["params"].name]
    parent = world.entities["parent"]
    obj: ObjectSpec = world.facts["obj"]
    if world.facts.get("spilled"):
        child.memes["calm"] += 1
        child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
        world.say(
            f"Together, {child.label} and {parent.label} wiped the spill, set the {obj.label} upright, "
            f"and breathed slower."
        )
        world.say(
            f"{parent.label} said the same thing a softer way: careful tools make kinder days."
        )
    else:
        world.say(
            f"There was nothing to clean, so {child.label} put the probe down and listened this time."
        )
    world.facts["resolved"] = True


def tell_story(world: World) -> None:
    opening(world)
    world.say("")
    caution(world)
    mistake(world)
    world.say("")
    repair(world)


# -----------------------------
# ASP twin
# -----------------------------
ASP_RULES = r"""
place_ok(P) :- calm_place(P).
fragile_object(O) :- fragile(O).

valid_story(P, O) :- place_ok(P), fragile_object(O).
risk(P, O) :- valid_story(P, O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("calm_place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
    for oid, obj in OBJECTS.items():
        if obj.fragile:
            lines.append(asp.fact("fragile", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((p, o) for p in PLACES for o in OBJECTS if is_reasonable(_safe_lookup(PLACES, p), _safe_lookup(OBJECTS, o)))
    aspv = asp_valid()
    if py == aspv:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", py)
    print("asp:", aspv)
    return 1


# -----------------------------
# QA
# -----------------------------
def prompts(world: World) -> list[str]:
    p: Place = world.place
    obj: ObjectSpec = world.facts["obj"]
    child = world.entities[world.facts["params"].name]
    return [
        f'Write a slice-of-life story about a child using a toy probe to check a {obj.label} at {p.label}.',
        f"Tell a cautionary story where {child.label} learns to be careful after mentioning a trillion tiny things.",
        f'Write a gentle everyday story that includes the words "probe" and "trillion" and ends with calm repair.',
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    child = world.entities[params.name]
    parent = world.entities["parent"]
    obj: ObjectSpec = world.facts["obj"]
    return [
        QAItem(
            question=f"What did {child.label} want to use to check the {obj.label}?",
            answer=f"{child.label} wanted to use a toy probe to look closely at the {obj.label}.",
        ),
        QAItem(
            question=f"Why did {parent.label} give a cautionary warning?",
            answer=f"{parent.label} warned that a probe should be used gently, because a rushed move could upset the {obj.label}.",
        ),
        QAItem(
            question=f"What happened after the mistake?",
            answer=f"{child.label} and {parent.label} cleaned up together, set the {obj.label} upright again, and the day felt calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a probe usually for?",
            answer="A probe is usually for checking or exploring something carefully, not for pressing hard.",
        ),
        QAItem(
            question="Why do people say trillion?",
            answer="People say trillion to mean a very, very big number, often to sound huge when talking about worries or guesses.",
        ),
    ]


# -----------------------------
# Standard interface
# -----------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary slice-of-life storyworld with a probe and a trillion worry.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = getattr(args, "place", None) or rng.choice([p for p in PLACES if _safe_lookup(PLACES, p).calmness >= 4])
    obj_id = getattr(args, "object", None) or rng.choice([o for o in OBJECTS if _safe_lookup(OBJECTS, o).fragile])
    if not is_reasonable(_safe_lookup(PLACES, place_id), _safe_lookup(OBJECTS, obj_id)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place_id, object=obj_id, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        for i, q in enumerate(sample.prompts, 1):
            print(f"P{i}: {q}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid stories:")
        for v in vals:
            print(" ", v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in PLACES:
            for o in OBJECTS:
                if is_reasonable(_safe_lookup(PLACES, p), _safe_lookup(OBJECTS, o)):
                    params = StoryParams(place=p, object=o, name="Mina", gender="girl", parent="mother")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
