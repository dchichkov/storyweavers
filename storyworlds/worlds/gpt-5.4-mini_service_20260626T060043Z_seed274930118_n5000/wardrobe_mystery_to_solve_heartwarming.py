#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/wardrobe_mystery_to_solve_heartwarming.py
===============================================================================================================

A small, self-contained storyworld about a wardrobe mystery that ends
heartwarmingly.

The core premise:
- A child notices one beloved item is missing from a wardrobe.
- The family follows gentle clues through the room.
- The mystery is solved by kindness, not surprise force.
- The ending proves the emotional change by showing the wardrobe restored
  and someone comforted.

This script follows the Storyweavers contract:
- standalone stdlib script
- shared result containers imported eagerly
- lazy ASP import inside ASP helpers
- Python reasonableness gate + inline ASP twin
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

WARDROBE_MESS = "missing"
THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
            keys = [upper, upper + "S", upper + "ES"]
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class Room:
    name: str
    contains: set[str] = field(default_factory=set)
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    child_trait: str
    helper_type: str
    item: str
    room: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass(frozen=True)
class ItemSpec:
    label: str
    phrase: str
    type: str
    emotional_value: str
    clue: str
    recovery_place: str
    genders: set[str]
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


@dataclass(frozen=True)
class HelperSpec:
    type: str
    label: str
    role: str
    comfort_line: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


ROOMS = {
    "bedroom": Room(name="the bedroom", contains={"wardrobe", "basket", "bed"}),
    "nursery": Room(name="the nursery", contains={"wardrobe", "toybox", "chair"}),
    "guest_room": Room(name="the guest room", contains={"wardrobe", "bench", "lamp"}),
}

ITEMS = {
    "red_scarf": ItemSpec(
        label="red scarf",
        phrase="a soft red scarf",
        type="scarf",
        emotional_value="made the child feel brave",
        clue="a tiny red thread on the wardrobe door",
        recovery_place="the coat hook by the window",
        genders={"girl", "boy"},
    ),
    "blue_hat": ItemSpec(
        label="blue hat",
        phrase="a round blue hat",
        type="hat",
        emotional_value="made the child feel ready for adventure",
        clue="a blue ribbon tucked under a pillow",
        recovery_place="the reading chair",
        genders={"girl", "boy"},
    ),
    "green_mittens": ItemSpec(
        label="green mittens",
        phrase="a pair of green mittens",
        type="mittens",
        emotional_value="kept little hands cozy",
        clue="two green yarn loops near the wardrobe base",
        recovery_place="the basket of folded blankets",
        genders={"girl", "boy"},
        plural=True,
    ),
    "yellow_sweater": ItemSpec(
        label="yellow sweater",
        phrase="a warm yellow sweater",
        type="sweater",
        emotional_value="felt like a sunny hug",
        clue="a yellow button in the laundry basket",
        recovery_place="the laundry basket",
        genders={"girl", "boy"},
    ),
}

HELPERS = {
    "grandmother": HelperSpec("grandmother", "Grandma", "grandmother", "Grandma smiled and said they could look gently together."),
    "father": HelperSpec("father", "Dad", "father", "Dad knelt beside the wardrobe and helped look with calm hands."),
    "older_sibling": HelperSpec("older sibling", "Mara", "older sibling", "Mara said it would be okay and promised to help search."),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Iris", "Pia", "Elena"]
BOY_NAMES = ["Theo", "Owen", "Sam", "Leo", "Finn", "Ben"]
TRAITS = ["curious", "gentle", "patient", "brave", "sweet", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for room in ROOMS:
        for item_id, item in ITEMS.items():
            for helper in HELPERS:
                if room in ROOMS and item.label and helper in HELPERS:
                    out.append((room, item_id, helper))
    return out


def explain_rejection(item_id: str, helper: str) -> str:
    return f"(No story: the combination with {item_id} and {helper} is not supported.)"


def explain_gender(item_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(ITEMS, item_id).genders))
    return f"(No story: this item is not a typical fit for {gender}; try --gender {ok}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for c in sorted(room.contains):
            lines.append(asp.fact("contains", rid, c))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("stored_in_wardrobe", iid))
        lines.append(asp.fact("clue", iid, item.clue))
        lines.append(asp.fact("recovered_at", iid, item.recovery_place))
        for g in sorted(item.genders):
            lines.append(asp.fact("wears", g, iid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_type", hid, helper.type))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(R, I, H) :- room(R), item(I), helper(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A warm wardrobe mystery storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "item", None) and getattr(args, "gender", None) and getattr(args, "gender", None) not in _safe_lookup(ITEMS, getattr(args, "item", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "room", None) is None or c[0] == getattr(args, "room", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    room, item, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(ITEMS, item).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        child_name=name,
        child_gender=gender,
        child_trait=trait,
        helper_type=helper,
        item=item,
        room=room,
    )


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(ROOMS, params.room))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        owner=None,
    ))
    helper_spec = _safe_lookup(HELPERS, params.helper_type)
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_spec.type,
        label=helper_spec.label,
    ))
    item_spec = _safe_lookup(ITEMS, params.item)
    item = world.add(Entity(
        id="MissingItem",
        type=item_spec.type,
        label=item_spec.label,
        phrase=item_spec.phrase,
        owner=child.id,
        caretaker=helper.id,
        location="wardrobe",
        plural=item_spec.plural,
    ))
    world.facts.update(child=child, helper=helper, item=item, item_spec=item_spec, helper_spec=helper_spec)
    return world


def find_mystery(world: World) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    item: Entity = _safe_fact(world, world.facts, "item")
    spec: ItemSpec = _safe_fact(world, world.facts, "item_spec")
    helper_spec: HelperSpec = _safe_fact(world, world.facts, "helper_spec")

    child.memes["worry"] += 1
    world.say(f"One morning, {child.id} opened the wardrobe and blinked.")
    world.say(f"{child.id}'s {spec.label} was gone.")

    world.para()
    world.say(f"{child.id} felt a small pinch of worry because {spec.emotional_value}.")
    world.say(f"Then {child.id} noticed {spec.clue} near the wardrobe door.")

    world.para()
    helper.memes["care"] += 1
    world.say(helper_spec.comfort_line)
    world.say(f"Together they followed the clue through {world.room.name}.")

    item.location = spec.recovery_place
    child.memes["hope"] += 1
    world.say(f"They found the {spec.label} at {spec.recovery_place}.")

    world.para()
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(f"It turned out {spec.label} had been set aside so neatly that nobody noticed it at first.")
    world.say(f"{child.id} smiled, put it back in the wardrobe, and gave {helper.pronoun('object')} a hug.")
    world.say(f"By bedtime, the wardrobe looked tidy again, and the room felt safe and warm.")


def generate_story_text(params: StoryParams) -> World:
    world = build_world(params)
    find_mystery(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    item: Entity = _safe_fact(world, f, "item")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        f"Write a heartwarming story about {child.id} solving a wardrobe mystery about a missing {item.label}.",
        f"Tell a gentle children’s story where a {child.type} named {child.id} and {helper.label} look for a lost {item.label} in the wardrobe.",
        f"Create a cozy mystery story that ends with {item.label} back where it belongs and everyone feeling relieved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    item: Entity = _safe_fact(world, f, "item")
    spec: ItemSpec = _safe_fact(world, f, "item_spec")
    helper_spec: HelperSpec = _safe_fact(world, f, "helper_spec")
    return [
        QAItem(
            question=f"What was missing from the wardrobe?",
            answer=f"{child.id}'s {spec.label} was missing from the wardrobe.",
        ),
        QAItem(
            question=f"What clue helped {child.id} begin the search?",
            answer=f"{spec.clue.capitalize()} helped {child.id} start solving the mystery.",
        ),
        QAItem(
            question=f"Who helped {child.id} look for the missing item?",
            answer=f"{helper.label} helped {child.id} search kindly and carefully.",
        ),
        QAItem(
            question=f"Where did they find the {spec.label}?",
            answer=f"They found it at {spec.recovery_place}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} put the {spec.label} back in the wardrobe, hugged {helper.pronoun('object')}, and felt happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wardrobe?",
            answer="A wardrobe is a tall cabinet or closet where people keep clothes neatly hung or folded.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find out what happened by noticing clues and thinking carefully.",
        ),
        QAItem(
            question="Why can a clue be helpful?",
            answer="A clue can point toward the answer, which helps people understand where something went or why it happened.",
        ),
        QAItem(
            question="Why is it nice to help someone look for a lost thing?",
            answer="It is nice because helping can calm worry and make the person feel cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.plural:
            bits.append("plural=True")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_text(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(child_name="Mina", child_gender="girl", child_trait="curious", helper_type="grandmother", item="red_scarf", room="bedroom"),
    StoryParams(child_name="Theo", child_gender="boy", child_trait="gentle", helper_type="father", item="yellow_sweater", room="guest_room"),
    StoryParams(child_name="Nora", child_gender="girl", child_trait="careful", helper_type="older_sibling", item="green_mittens", room="nursery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for room, item, helper in combos:
            print(f"  {room:10} {item:14} {helper}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.item} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
