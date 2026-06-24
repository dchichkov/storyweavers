#!/usr/bin/env python3
"""
storyworlds/worlds/yacht_snout_magic_fairy_tale.py
===================================================

A small fairy-tale storyworld about a child on a yacht, a magical snout, and a
gentle repair after a spell goes wrong.

Premise:
- A child and a helper are sailing on a yacht.
- A magical snout (a sea-creature's nose, or a plush snout on a ship mascot)
  reacts to a spell and causes trouble.
- A grown-up or helper discovers a practical way to calm the magic and restore
  the voyage.

The world keeps two accumulating measures on entities:
- meters: physical state like sparkle, dampness, stuckness, glow
- memes: emotional state like worry, wonder, relief, pride

The story is driven by world state, not a fixed paragraph template. The same
small set of entities can produce a few plausible fairy-tale variations.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    entities: set[str] = field(default_factory=set)
    helper: object | None = None
    snout: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    weather: str = ""
    magic: bool = False
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
class Spell:
    id: str
    label: str
    incantation: str
    effect: str
    mess: str
    clue: str
    tags: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    label: str
    body_part: str
    risk: str
    tags: set[str] = field(default_factory=set)
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
class Fix:
    id: str
    label: str
    method: str
    comfort: str
    clears: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "attrs": dict(v.attrs), "tags": set(v.tags),
            "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    snout = world.get("snout")
    if child.meters["spell"] < THRESHOLD:
        return out
    sig = ("magic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snout.meters["glow"] += 1
    snout.meters["sparkle"] += 1
    child.memes["wonder"] += 1
    out.append("__magic__")
    return out


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    snout = world.get("snout")
    if snout.meters["glow"] < THRESHOLD:
        return out
    sig = ("trouble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    snout.meters["stuck"] += 1
    out.append("__trouble__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    snout = world.get("snout")
    if snout.meters["stuck"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["calm"] += 1
    child.memes["relief"] += 1
    snout.meters["stuck"] = 0
    snout.meters["glow"] = 0
    out.append("__fix__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_magic, _r_trouble, _r_fix):
            out = rule(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combo(place: str, spell: str, trouble: str, fix: str) -> bool:
    p = _safe_lookup(PLACES, place)
    s = _safe_lookup(SPELLS, spell)
    t = _safe_lookup(TROUBLES, trouble)
    f = _safe_lookup(FIXES, fix)
    return p.magic and spell in p.affords and t.body_part == "snout" and t.risk in s.effect and t.risk in f.clears


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for spell in SPELLS:
            for trouble in TROUBLES:
                for fix in FIXES:
                    if valid_combo(place, spell, trouble, fix):
                        out.append((place, spell, trouble, fix))
    return out


@dataclass
class StoryParams:
    place: str
    spell: str
    trouble: str
    fix: str
    child_name: str
    child_kind: str
    helper_name: str
    helper_kind: str
    seed: Optional[int] = None
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
        return None


PLACES = {
    "harbor": Place(id="harbor", label="the harbor", weather="windy", magic=True, affords={"spell"}),
    "moon_deck": Place(id="moon_deck", label="the moonlit deck", weather="soft", magic=True, affords={"spell"}),
    "blue_bay": Place(id="blue_bay", label="the blue bay", weather="bright", magic=True, affords={"spell"}),
}

SPELLS = {
    "singing": Spell(id="singing", label="a singing spell", incantation="twinkle, twinkle", effect="glow", mess="sparkle", clue="The words were sweet, but they woke the magic.", tags={"magic", "spell"}),
    "starlight": Spell(id="starlight", label="a starlight spell", incantation="shine and sway", effect="sparkle", mess="glow", clue="The spell made the night feel bright and strange.", tags={"magic", "spell"}),
}

TROUBLES = {
    "snout_glow": Trouble(id="snout_glow", label="a glowing snout", body_part="snout", risk="glow", tags={"snout", "magic"}),
    "snout_sparkle": Trouble(id="snout_sparkle", label="a sparkling snout", body_part="snout", risk="sparkle", tags={"snout", "magic"}),
}

FIXES = {
    "moonwater": Fix(id="moonwater", label="moonwater", method="sprinkled moonwater on the snout", comfort="the magic softened", clears={"glow", "sparkle"}, tags={"water", "magic"}),
    "lullaby": Fix(id="lullaby", label="a lullaby", method="sang a gentle lullaby", comfort="the snout settled", clears={"glow", "sparkle"}, tags={"music", "magic"}),
}

CHILD_NAMES = ["Luna", "Milo", "Iris", "Finn", "Nora", "Ari"]
HELPER_NAMES = ["Captain Reed", "Grandma Pearl", "Sailor Bee", "Old Finch"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a yacht, a snout, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--kind", choices=["girl", "boy"])
    ap.add_argument("--helper-kind", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "spell", None) is None or c[1] == getattr(args, "spell", None))
              and (getattr(args, "trouble", None) is None or c[2] == getattr(args, "trouble", None))
              and (getattr(args, "fix", None) is None or c[3] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, spell, trouble, fix = rng.choice(list(combos))
    child_kind = getattr(args, "kind", None) or rng.choice(["girl", "boy"])
    helper_kind = getattr(args, "helper_kind", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        spell=spell,
        trouble=trouble,
        fix=fix,
        child_name=child_name,
        child_kind=child_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    child = world.add(Entity(id="child", kind="character", type=params.child_kind, label=params.child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_kind, label=params.helper_name, role="helper"))
    snout = world.add(Entity(id="snout", kind="thing", type="snout", label="the snout", tags={"snout"}))
    child.meters["spell"] = 0
    child.memes["wonder"] = 0
    child.memes["worry"] = 0
    child.memes["relief"] = 0
    helper.memes["calm"] = 0
    snout.meters["glow"] = 0
    snout.meters["stuck"] = 0
    snout.meters["sparkle"] = 0

    spell = _safe_lookup(SPELLS, params.spell)
    trouble = _safe_lookup(TROUBLES, params.trouble)
    fix = _safe_lookup(FIXES, params.fix)

    world.say(f"On the {world.place.label}, {child.label_word} {params.child_name} rode a little yacht with {helper.label_word} {params.helper_name}.")
    world.say(f"The yacht had a cheerful mascot, {trouble.label}, tucked near the rail.")
    world.para()
    child.meters["spell"] += 1
    world.say(f"{child.label_word.capitalize()} whispered {spell.incantation}, and the words made {trouble.label} twitch.")
    world.say(spell.clue)
    propagate(world, narrate=True)
    world.para()
    world.say(f"{params.child_name} saw the trouble and looked at {params.helper_name}.")
    world.say(f"{helper.label_word.capitalize()} smiled and {fix.method}, because {fix.label} could calm the magic without harming it.")
    propagate(world, narrate=True)
    world.para()
    if snout.meters["stuck"] == 0:
        world.say(f"At last, {trouble.label} rested quietly again, and the yacht slid on under a silver sky.")
    else:
        world.say(f"The magic still clung to {trouble.label}, so the voyage stayed uneasy.")
    world.facts.update(
        child=child,
        helper=helper,
        snout=snout,
        spell=spell,
        trouble=trouble,
        fix=fix,
        place=world.place,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child about {f["child"].label_word} on a yacht, a magic snout, and a gentle fix.',
        f"Tell a child-friendly tale where {f['child'].label_word} casts a spell on the yacht and {f['helper'].label_word} calms the snout with moonwater or a lullaby.",
        f'Write a short magical story that uses the words "yacht" and "snout" and ends with the trouble settled and the voyage safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    spell = f["spell"]
    trouble = f["trouble"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who sailed on the yacht in this story?",
            answer=f"{child.label_word.capitalize()} {child.label} sailed with {helper.label_word} {helper.label} on the yacht.",
        ),
        QAItem(
            question=f"What did {child.label} whisper to make the magic start?",
            answer=f"{child.label} whispered {spell.incantation}. That spell woke the magic and made {trouble.label} glow.",
        ),
        QAItem(
            question=f"What went wrong with {trouble.label} after the spell?",
            answer=f"{trouble.label.capitalize()} began to glow and sparkle, and then it got stuck with too much magic.",
        ),
        QAItem(
            question=f"How did {helper.label} help settle the trouble?",
            answer=f"{helper.label} {fix.method}, which helped calm the magic and settle {trouble.label}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The snout grew quiet again, and the yacht kept sailing under a soft, safe sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a yacht?", answer="A yacht is a boat that sails on water, often used for a trip or a fancy ride."),
        QAItem(question="What does magic mean in a fairy tale?", answer="Magic is a special kind of pretend power that can make strange and wonderful things happen."),
        QAItem(question="What is a snout?", answer="A snout is the nose and mouth part of an animal's face, like on a pig, seal, or fox."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    parts.append(f"fired={sorted(world.fired)}")
    return "\n".join(parts)


CURATED = [
    StoryParams(place="harbor", spell="singing", trouble="snout_glow", fix="moonwater", child_name="Luna", child_kind="girl", helper_name="Captain Reed", helper_kind="boy"),
    StoryParams(place="moon_deck", spell="starlight", trouble="snout_sparkle", fix="lullaby", child_name="Finn", child_kind="boy", helper_name="Grandma Pearl", helper_kind="girl"),
    StoryParams(place="blue_bay", spell="singing", trouble="snout_sparkle", fix="lullaby", child_name="Iris", child_kind="girl", helper_name="Sailor Bee", helper_kind="girl"),
]


ASP_RULES = r"""
place_magic(P) :- place(P), magic_place(P).
trouble_started(T) :- spell(S), effect(S, E), trouble(T), risk(T, E).
fix_works(F, T) :- fix(F), clears(F, R), trouble(T), risk(T, R).
valid(P,S,T,F) :- place_magic(P), spell(S), trouble_started(T), fix_works(F, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.magic:
            lines.append(asp.fact("magic_place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("effect", sid, s.effect))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("risk", tid, t.risk))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for c in sorted(f.clears):
            lines.append(asp.fact("clears", fid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
        return 1
    if not generate(CURATED[0]).story:
        print("SMOKE TEST FAILED")
        return 1
    print(f"OK: ASP matches python on {len(py)} combos, and generation works.")
    return 0


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params_for_seed(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for combo in combos:
            print(combo)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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
            header = f"### {p.child_name} on {p.place} with {p.spell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
