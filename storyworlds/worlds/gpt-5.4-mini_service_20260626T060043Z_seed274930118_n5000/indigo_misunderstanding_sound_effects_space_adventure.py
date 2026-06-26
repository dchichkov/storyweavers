#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure about an indigo signal,
a misunderstanding, and the sound effects that help fix it.

The source tale premise:
- A child astronaut hears strange sounds on a drifting moon.
- A quiet indigo light appears on the console.
- The sounds are misread as danger, but they are actually friendly signals.
- The crew uses the sound effects to realize the truth and make a better plan.

This world keeps the simulation small:
- A rover, a comms panel, a moon bay, a beacon, and a child explorer.
- Physical state is tracked with meters.
- Emotional state is tracked with memes.
- The story changes according to whether the signal is understood correctly,
  whether the explorer trusts the sounds, and whether a helper explains them.

The script supports the standard Storyweavers CLI:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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


# ---------------------------------------------------------------------------
# World constants and registries
# ---------------------------------------------------------------------------

NAME_POOL = [
    "Ari", "Nova", "Milo", "Luna", "Zed", "Ivy", "Kai", "Rin", "Tess", "Oren"
]
ROLE_POOL = ["pilot", "explorer", "cadet", "navigator", "engineer"]
HELPER_POOL = ["captain", "robot", "mate", "astronaut", "guide"]

SOUND_EFFECTS = {
    "beep": {
        "emoji": "beep",
        "description": "a quick console chirp",
        "meaning": "a normal status ping",
    },
    "whirr": {
        "emoji": "whirr",
        "description": "a soft machine whirr",
        "meaning": "the rover is moving safely",
    },
    "ping": {
        "emoji": "ping",
        "description": "a bright beacon ping",
        "meaning": "someone is sending a friendly signal",
    },
    "whoop": {
        "emoji": "whoop",
        "description": "an alarm whoop",
        "meaning": "something needs attention",
    },
    "clink": {
        "emoji": "clink",
        "description": "a tiny metal clink",
        "meaning": "a tool has tapped the hull",
    },
}

LOCATIONS = {
    "moon_bay": {
        "label": "the moon bay",
        "surface": "dusty silver ground",
        "echo": "soft",
        "affords": {"rover", "signal", "listen"},
    },
    "orbit_deck": {
        "label": "the orbit deck",
        "surface": "bright panels and windows",
        "echo": "clean",
        "affords": {"signal", "listen"},
    },
    "cargo_hatch": {
        "label": "the cargo hatch",
        "surface": "a narrow metal corridor",
        "echo": "tinny",
        "affords": {"rover", "signal", "listen"},
    },
}

OBJECTS = {
    "rover": {
        "label": "the little rover",
        "kind": "vehicle",
        "region": "floor",
        "color": "indigo",
    },
    "panel": {
        "label": "the comms panel",
        "kind": "device",
        "region": "wall",
        "color": "indigo",
    },
    "beacon": {
        "label": "the indigo beacon",
        "kind": "signal",
        "region": "sky",
        "color": "indigo",
    },
}


# ---------------------------------------------------------------------------
# Shared entities
# ---------------------------------------------------------------------------


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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Site:
    place: str
    echo: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    sound: str
    object: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    def __init__(self, site: Site) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------

def _narrate_sound(world: World, sound: str) -> None:
    desc = _safe_lookup(SOUND_EFFECTS, sound)["description"]
    world.say(f"The ship answered with {desc}.")


def _misunderstanding(world: World, hero: Entity, sound: str) -> None:
    if world.facts.get("understood"):
        return
    sig = ("misunderstanding", sound)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0) + 1
    world.say(
        f"{hero.id} heard the {sound} and thought it meant trouble."
    )


def _helper_explains(world: World, helper: Entity, hero: Entity, sound: str) -> None:
    if world.facts.get("understood"):
        return
    sig = ("explain", sound)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["worry"] = max(0, hero.memes.get("worry", 0) - 1)
    world.facts["understood"] = True
    world.say(
        f"{helper.label.capitalize()} smiled and said the {sound} was just a friendly signal."
    )


def _small_action(world: World, hero: Entity, obj: Entity, sound: str) -> None:
    if world.facts.get("understood"):
        sig = ("calm_action", sound)
        if sig in world.fired:
            return
        world.fired.add(sig)
        hero.meters["boldness"] = hero.meters.get("boldness", 0) + 1
        obj.meters["glow"] = obj.meters.get("glow", 0) + 1
        world.say(
            f"{hero.id} listened again, tapped the {obj.label}, and waited for the next {sound}."
        )


def tell(place: Site, sound: str, obj_id: str, name: str, role: str, helper_role: str) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=name,
        kind="character",
        type="child",
        label=f"{name}, the {role}",
        phrase=f"a small {role}",
        meters={"boldness": 0.0},
        memes={"worry": 0.0, "confusion": 0.0, "curiosity": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="adult",
        label=f"the {helper_role}",
        phrase=f"the {helper_role}",
        memes={"calm": 0.0},
    ))
    obj = world.add(Entity(
        id=obj_id,
        kind="thing",
        type="signal",
        label=_safe_lookup(OBJECTS, obj_id)["label"],
        phrase=_safe_lookup(OBJECTS, obj_id)["label"],
        meters={"glow": 1.0 if obj_id == "beacon" else 0.0},
        memes={"mystery": 1.0},
    ))

    # Act 1
    world.say(
        f"On {place.place}, {hero.id} was a {hero.phrase} who loved space sounds."
    )
    world.say(
        f"Near the {place.echo} floor, the {obj.label} flashed indigo in the dim light."
    )
    _narrate_sound(world, sound)

    # Act 2
    world.para()
    world.say(
        f"{hero.id} froze and thought the sound meant a problem."
    )
    _misunderstanding(world, hero, sound)

    if sound in {"whoop", "clink"}:
        world.say(
            f"The warning was loud enough to make {hero.id} step back."
        )
    else:
        world.say(
            f"The small echo made {hero.id} lean closer instead of running away."
        )

    world.say(
        f"Then the {helper_role} checked the panel and listened twice."
    )
    _helper_explains(world, helper, hero, sound)

    # Act 3
    world.para()
    _small_action(world, hero, obj, sound)
    if world.facts.get("understood"):
        hero.meters["boldness"] = hero.meters.get("boldness", 0) + 1
        helper.memes["pride"] = helper.memes.get("pride", 0) + 1
        world.say(
            f"{hero.id} laughed, because the indigo light was not a threat at all."
        )
        world.say(
            f"Together they followed the signal and found a safe path through the dark."
        )
    else:
        world.say(
            f"{hero.id} stayed quiet, still unsure what the sound wanted."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        obj=obj,
        sound=sound,
        understood=world.facts.get("understood", False),
        place=place.place,
    )
    return world


# ---------------------------------------------------------------------------
# Registries and content helpers
# ---------------------------------------------------------------------------

SETTINGS = {
    "moon_bay": Site(place=LOCATIONS["moon_bay"]["label"], echo=LOCATIONS["moon_bay"]["echo"], affords=LOCATIONS["moon_bay"]["affords"]),
    "orbit_deck": Site(place=LOCATIONS["orbit_deck"]["label"], echo=LOCATIONS["orbit_deck"]["echo"], affords=LOCATIONS["orbit_deck"]["affords"]),
    "cargo_hatch": Site(place=LOCATIONS["cargo_hatch"]["label"], echo=LOCATIONS["cargo_hatch"]["echo"], affords=LOCATIONS["cargo_hatch"]["affords"]),
}

SOUNDS = {
    "beep": "beep",
    "whirr": "whirr",
    "ping": "ping",
    "whoop": "whoop",
    "clink": "clink",
}

OBJECTS_ORDER = ["beacon", "panel", "rover"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, site in SETTINGS.items():
        for sound in SOUNDS:
            for obj in OBJECTS:
                if sound in site.affords:
                    combos.append((place, sound, obj))
    return combos


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Space Adventure story for a young child about indigo lights, {f["sound"]}, and a misunderstanding.',
        f"Tell a gentle story where {f['hero'].id} hears a {f['sound']} on {f['place']} and learns it is a friendly signal.",
        f'Create a child-friendly space story that uses the word "indigo" and ends with a clearer understanding of the sound.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    obj: Entity = _safe_fact(world, f, "obj")
    sound = _safe_fact(world, f, "sound")
    understood = _safe_fact(world, f, "understood")
    qa = [
        QAItem(
            question=f"Who heard the {sound} near {obj.label}?",
            answer=f"{hero.id} heard it while standing near {obj.label} on {f['place']}.",
        ),
        QAItem(
            question=f"What color was the light on {obj.label}?",
            answer="It was indigo, which made the signal look special and a little mysterious.",
        ),
        QAItem(
            question=f"Who helped explain the sound?",
            answer=f"{helper.label.capitalize()} helped explain that the {sound} was a friendly signal.",
        ),
    ]
    if understood:
        qa.append(
            QAItem(
                question="What did the child learn by the end?",
                answer=f"{hero.id} learned that the sound was not danger; it was a friendly message that led them onward.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What was still confusing at the end?",
                answer=f"{hero.id} was still unsure about the {sound} and had not fully understood the signal yet.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound that helps tell you what is happening, like a beep, ping, or whirr.",
        ),
        QAItem(
            question="What does indigo look like?",
            answer="Indigo is a deep blue-purple color, like a dark night sky with a little blue in it.",
        ),
        QAItem(
            question="Why might astronauts listen carefully in space stories?",
            answer="Astronauts listen carefully because sounds and signals can warn them, guide them, or help them understand what to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(P). sound(S). object(O). affords(P,S).

% A misunderstanding happens when the hero hears the sound and does not yet understand it.
misunderstanding(P,S,O) :- place(P), sound(S), object(O), affords(P,S).

% If a helper explains the sound, the story resolves with understanding.
understood(P,S,O) :- misunderstanding(P,S,O), explainable(S).

% A story is reasonable if the place can host the sound and the object is visible.
valid_story(P,S,O) :- place(P), sound(S), object(O), affords(P,S).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        for sound in _safe_lookup(SETTINGS, place).affords:
            lines.append(asp.fact("affords", place, sound))
    for sound in SOUNDS:
        lines.append(asp.fact("sound", sound))
        lines.append(asp.fact("explainable", sound))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world about an indigo misunderstanding and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLE_POOL)
    ap.add_argument("--helper", choices=HELPER_POOL)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "sound", None) is None or c[1] == getattr(args, "sound", None))
        and (getattr(args, "object", None) is None or c[2] == getattr(args, "object", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, sound, obj = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAME_POOL)
    role = getattr(args, "role", None) or rng.choice(ROLE_POOL)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_POOL)
    return StoryParams(place=place, sound=sound, object=obj, name=name, role=role, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.sound, params.object, params.name, params.role, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  understood: {world.facts.get('understood', False)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection(place: str, sound: str, obj: str) -> str:
    return f"(No story: {place} cannot host the sound {sound} with {obj} in this setup.)"


def asp_show_program() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sound, object) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, sound=s, object=o, name=NAME_POOL[i % len(NAME_POOL)], role=ROLE_POOL[i % len(ROLE_POOL)], helper=HELPER_POOL[i % len(HELPER_POOL)])) for i, (p, s, o) in enumerate(valid_combos()[:10])]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
