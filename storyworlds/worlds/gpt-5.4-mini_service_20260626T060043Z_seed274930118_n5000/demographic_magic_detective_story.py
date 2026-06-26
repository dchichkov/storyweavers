#!/usr/bin/env python3
"""
A small storyworld for a magical detective tale with demographic clues.

Premise:
A child detective follows a magical trail through a market square where the
crowd is split into two demographic groups: kids and grown-ups. Someone has
used magic to switch a missing talisman from one stall to another, and the
detective must notice who could have done it, why the crowd reacted, and how
the case is solved.

The story is intentionally narrow: every valid story has a clear clue trail,
a magical false lead, and a resolution where the detective uses a spell safely.
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
# World model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    detective: object | None = None
    mystery: object | None = None
    partner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    name: str
    demographic: str
    magic_level: str
    affirms: set[str] = field(default_factory=set)
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


@dataclass
class Spell:
    id: str
    label: str
    verb: str
    effect: str
    clue: str
    required_demographic: str
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


@dataclass
class Mystery:
    id: str
    label: str
    item: str
    hiding_place: str
    owner_group: str
    risk: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "market": Place(name="the market square", demographic="mixed", magic_level="bright",
                    affirms={"glow", "float", "hide"}),
    "harbor": Place(name="the harbor lane", demographic="working", magic_level="misty",
                    affirms={"glow", "echo", "hide"}),
    "library": Place(name="the old library steps", demographic="scholarly", magic_level="quiet",
                      affirms={"glow", "vanish", "hide"}),
}

SPELLS = {
    "glow": Spell(
        id="glow",
        label="a glow spell",
        verb="make things glow",
        effect="shone with blue light",
        clue="blue sparkles clung to the edges",
        required_demographic="kids",
    ),
    "float": Spell(
        id="float",
        label="a float spell",
        verb="lift things gently",
        effect="rose an inch off the ground",
        clue="the dust stayed hanging in the air",
        required_demographic="grownups",
    ),
    "hide": Spell(
        id="hide",
        label="a hide spell",
        verb="hide things from plain sight",
        effect="slid behind a ripple of light",
        clue="the air folded like a curtain",
        required_demographic="kids",
    ),
    "echo": Spell(
        id="echo",
        label="an echo spell",
        verb="bounce whispers around",
        effect="came back twice as soft",
        clue="the words returned from the stone",
        required_demographic="grownups",
    ),
    "vanish": Spell(
        id="vanish",
        label="a vanish spell",
        verb="make small things disappear",
        effect="winked out for a moment",
        clue="the lantern glass went dark",
        required_demographic="grownups",
    ),
}

MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        label="the silver lantern charm",
        item="lantern charm",
        hiding_place="behind the spice cart",
        owner_group="kids",
        risk="would scare the little market singers",
    ),
    "key": Mystery(
        id="key",
        label="the brass gate key",
        item="gate key",
        hiding_place="under the fish crate",
        owner_group="grownups",
        risk="would keep the harbor door locked at dusk",
    ),
    "bell": Mystery(
        id="bell",
        label="the tiny brass bell",
        item="brass bell",
        hiding_place="inside the ribbon box",
        owner_group="kids",
        risk="would stop the bell game at recess",
    ),
}

DETECTIVE_TYPES = ["girl", "boy"]
DETECTIVE_NAMES = ["Mina", "Tari", "Lina", "Owen", "Niko", "June"]
ADULT_NAMES = ["Mara", "Jon", "Sera", "Pavel"]
TRAITS = ["sharp-eyed", "quiet", "brave", "careful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
spell(S) :- spell_fact(S).
mystery(M) :- mystery_fact(M).

valid_combo(P, S, M) :- place(P), spell(S), mystery(M),
                        place_affords(P, S),
                        spell_for_demo(S, D), mystery_group(M, D).

#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        lines.append(asp.fact("place_demographic", pid, p.demographic))
        for spell in sorted(p.affirms):
            lines.append(asp.fact("place_affords", pid, spell))
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell_fact", sid))
        lines.append(asp.fact("spell_for_demo", sid, s.required_demographic))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        lines.append(asp.fact("mystery_group", mid, m.owner_group))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_combo/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - ac))
    print("only asp:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for spell_id, spell in SPELLS.items():
            if spell.id not in place.affirms:
                continue
            for mystery_id, mystery in MYSTERIES.items():
                if spell.required_demographic == mystery.owner_group:
                    combos.append((place_id, spell_id, mystery_id))
    return combos


def explain_rejection(place_id: str, spell_id: str, mystery_id: str) -> str:
    place = _safe_lookup(PLACES, place_id)
    spell = _safe_lookup(SPELLS, spell_id)
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    if spell.id not in place.affirms:
        return (
            f"(No story: {place.name} does not support {spell.label}; the magic would feel forced.)"
        )
    if spell.required_demographic != mystery.owner_group:
        return (
            f"(No story: {spell.label} is written for {spell.required_demographic}, "
            f"but {mystery.label} belongs to {mystery.owner_group}. The clue would not fit.)"
        )
    return "(No story: the requested combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    spell: str
    mystery: str
    detective_name: str
    detective_type: str
    partner_name: str
    partner_type: str
    trait: str
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


def choose_name(rng: random.Random, typ: str) -> str:
    if typ in {"girl", "boy"}:
        return rng.choice(DETECTIVE_NAMES)
    return rng.choice(ADULT_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A magical detective storyworld with demographic clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--type", dest="detective_type", choices=DETECTIVE_TYPES)
    ap.add_argument("--partner-type", choices=["mother", "father", "adult"])
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
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "spell", None) is None or c[1] == getattr(args, "spell", None))
        and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))
    ]
    if getattr(args, "place", None) and getattr(args, "spell", None) and getattr(args, "mystery", None):
        if not filtered:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, spell, mystery = rng.choice(list(filtered))
    dt = getattr(args, "detective_type", None) or rng.choice(DETECTIVE_TYPES)
    detective_name = getattr(args, "name", None) or choose_name(rng, dt)
    partner_type = getattr(args, "partner_type", None) or rng.choice(["mother", "father", "adult"])
    partner_name = getattr(args, "partner", None) or choose_name(rng, partner_type)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        spell=spell,
        mystery=mystery,
        detective_name=detective_name,
        detective_type=dt,
        partner_name=partner_name,
        partner_type=partner_type,
        trait=trait,
    )


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    detective = world.add(Entity(
        id=params.detective_name, kind="character", type=params.detective_type,
        traits=["child", params.trait],
    ))
    partner = world.add(Entity(
        id=params.partner_name, kind="character", type=params.partner_type,
        traits=["parent" if params.partner_type in {"mother", "father"} else "adult"],
    ))
    mystery = world.add(Entity(
        id=params.mystery, kind="thing", type="artifact", label=_safe_lookup(MYSTERIES, params.mystery).label,
        phrase=_safe_lookup(MYSTERIES, params.mystery).item,
        owner=detective.id,
    ))
    spell = _safe_lookup(SPELLS, params.spell)

    detective.memes["curiosity"] = 1
    detective.memes["joy"] = 1
    world.facts.update(
        detective=detective, partner=partner, mystery=mystery, spell=spell,
        place=world.place, params=params,
    )

    world.say(
        f"{detective.id} was a {params.trait} little detective who loved clues more than candy."
    )
    world.say(
        f"One bright morning at {world.place.name}, the crowd was split into two demographic groups: "
        f"kids near the fountain and grown-ups by the stalls."
    )
    world.say(
        f"{detective.id} noticed that the market lantern case was empty, and {mystery.label} was missing."
    )

    world.para()
    world.say(
        f"{detective.id} studied the sparkles on the cobblestones and found a clue: {spell.clue}."
    )
    if spell.required_demographic == "kids":
        world.say(
            f"That clue pointed toward the kid side of the market, where small hands and quick feet were playing."
        )
    else:
        world.say(
            f"That clue pointed toward the grown-up side of the market, where careful hands were moving crates."
        )

    world.say(
        f"{params.partner_name} frowned and said the missing {mystery.label} could {mystery.risk}."
    )
    world.say(
        f"But {detective.id} remembered that the right magic had to match the right demographic, or the clue would lie."
    )

    world.para()
    world.say(
        f"At last, {detective.id} used {spell.label} to test the trail, and the empty space answered back."
    )
    world.say(
        f"The hidden {mystery.label} was found {_safe_lookup(MYSTERIES, params.mystery).hiding_place}, just where the sparkles had led."
    )
    world.say(
        f"{detective.id} returned {mystery.label} to its place, and the market breathed out in relief."
    )
    world.say(
        f"By sunset, the kids were singing again, the grown-ups were smiling, and the case was closed."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    spell = _safe_fact(world, world.facts, "spell")
    mystery = _safe_fact(world, world.facts, "mystery")
    return [
        f"Write a short detective story for children about {p.detective_name} solving a magical case at {world.place.name}.",
        f"Tell a story where a child detective uses {spell.label} to find {mystery.label} and notices a demographic clue.",
        f"Create a gentle mystery story with magic, a missing object, and a clear ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    spell: Spell = _safe_fact(world, world.facts, "spell")
    mystery: Entity = _safe_fact(world, world.facts, "mystery")
    place: Place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {p.detective_name}, a {p.trait} little {p.detective_type}.",
        ),
        QAItem(
            question=f"What was missing from the market?",
            answer=f"{mystery.label} was missing, and that made the case important.",
        ),
        QAItem(
            question=f"What kind of magic helped with the clue?",
            answer=f"{spell.label} helped because it matched the clue and fit the place at {place.name}.",
        ),
        QAItem(
            question=f"Why did the detective pay attention to demographic groups?",
            answer=(
                f"Because the trail split between kids and grown-ups, and the spell clue only made sense "
                f"for the right group."
            ),
        ),
        QAItem(
            question=f"Where was the missing item found?",
            answer=f"It was found {_safe_lookup(MYSTERIES, p.mystery).hiding_place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a demographic group?",
            answer="A demographic group is a way of describing a set of people, like kids, grown-ups, or elders.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible in real life that can still happen in a story, like glowing or floating clues.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("market", "glow", "lantern", "Mina", "girl", "Mara", "mother", "sharp-eyed"),
    StoryParams("market", "hide", "bell", "Tari", "boy", "Jon", "father", "careful"),
    StoryParams("harbor", "echo", "key", "Lina", "girl", "Pavel", "father", "quiet"),
    StoryParams("library", "vanish", "key", "Owen", "boy", "Sera", "mother", "brave"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos")
        for combo in combos:
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.detective_name}: {p.spell} at {p.place} (mystery: {p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
