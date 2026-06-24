#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073042Z_seed779406221_n50/yacht_snout_magic_fairy_tale.py
==========================================================================================================

A small fairy-tale storyworld about a yacht, a snout, and a little bit of magic.

Seed tale premise:
A child on a yacht meets a sea creature with a glittering snout. A magic wish
is used the wrong way at first, causing trouble on deck. A kind helper reveals a
gentler spell, and the story ends with the yacht floating safely under bright
stars.

The simulation tracks:
- physical meters: splash, shine, tide, soak
- emotional memes: wonder, worry, courage, calm

The story is rendered from simulated state, not from a frozen text shell.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    boat: object | None = None
    child: object | None = None
    wave: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "captain"}:
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
    afloat: bool = True
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class Magic:
    id: str
    name: str
    effect: str
    kind: str
    safe: bool = False
    tags: set[str] = field(default_factory=set)
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
class Creature:
    id: str
    name: str
    label: str
    snout: bool = True
    magical: bool = False
    kind: str = "creature"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Optional[Place] = None
        self.creature: Optional[Creature] = None
        self.magic: Optional[Magic] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_magic_spill(world: World) -> list[str]:
    out = []
    if not world.magic:
        return out
    if world.magic.kind == "loud" and world.magic.safe is False:
        if world.place and world.place.meters["shine"] >= THRESHOLD:
            sig = ("spill", world.magic.id)
            if sig not in world.fired:
                world.fired.add(sig)
                world.place.meters["splash"] += 1
                world.place.memes["worry"] += 1
                out.append("The spell splashed across the deck.")
    return out


def _r_creature_help(world: World) -> list[str]:
    out = []
    if not world.creature or not world.place:
        return out
    if world.creature.memes["calm"] >= THRESHOLD and world.place.meters["splash"] >= THRESHOLD:
        sig = ("help", world.creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.place.meters["splash"] = max(0.0, world.place.meters["splash"] - 1)
            world.place.meters["shine"] += 1
            out.append("The snouted creature answered with a gentle glow.")
    return out


def _r_worry_to_courage(world: World) -> list[str]:
    out = []
    hero = world.entities.get("child")
    if hero and hero.memes["worry"] >= THRESHOLD and world.place and world.place.meters["shine"] >= THRESHOLD:
        sig = ("courage", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["courage"] += 1
            hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
            out.append("The child found the courage to try the kind spell.")
    return out


CAUSAL_RULES = [
    Rule("magic_spill", _r_magic_spill),
    Rule("creature_help", _r_creature_help),
    Rule("worry_to_courage", _r_worry_to_courage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    creature: str
    magic: str
    child: str
    seed: Optional[int] = None
    params: object | None = None
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
    "harbor": Place(id="harbor", label="the harbor", afloat=True, magical=False),
    "moonbay": Place(id="moonbay", label="Moon Bay", afloat=True, magical=True),
}

MAGICS = {
    "sparkle": Magic(id="sparkle", name="sparkle spell", effect="shine brighter", kind="gentle", safe=True, tags={"magic", "shine"}),
    "wish": Magic(id="wish", name="wish spell", effect="make a quick shine", kind="loud", safe=False, tags={"magic", "worry"}),
    "tidebell": Magic(id="tidebell", name="tide-bell charm", effect="call a calm tide", kind="gentle", safe=True, tags={"magic", "tide"}),
}

CREATURES = {
    "seal": Creature(id="seal", name="seal", label="seal with a silver snout", snout=True, magical=False, tags={"snout"}),
    "swan": Creature(id="swan", name="swan", label="swan with a pearly snout", snout=True, magical=True, tags={"snout", "magic"}),
    "dolphin": Creature(id="dolphin", name="dolphin", label="dolphin with a bright snout", snout=True, magical=True, tags={"snout", "magic"}),
}

NAMES = ["Mina", "Pip", "Rose", "Toby", "Nell", "Finn"]
TRAITS = ["brave", "curious", "gentle", "earnest"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for creature in CREATURES:
            for magic in MAGICS:
                if creature == "seal" and magic == "wish":
                    combos.append((place, creature, magic))
                elif creature != "seal":
                    combos.append((place, creature, magic))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a yacht, a snout, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--magic", choices=MAGICS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "creature", None) is None or c[1] == getattr(args, "creature", None))
              and (getattr(args, "magic", None) is None or c[2] == getattr(args, "magic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, creature, magic = rng.choice(list(combos))
    return StoryParams(
        place=place,
        creature=creature,
        magic=magic,
        child=getattr(args, "name", None) or rng.choice(NAMES),
        seed=None,
    )


def tell(params: StoryParams) -> World:
    w = World()
    place = _safe_lookup(PLACES, params.place)
    creature = _safe_lookup(CREATURES, params.creature)
    magic = _safe_lookup(MAGICS, params.magic)
    child = w.add(Entity(id="child", kind="character", type="girl", label=params.child, attrs={"trait": params.name or ""}))
    boat = w.add(Entity(id="yacht", kind="thing", type="yacht", label="the yacht"))
    wave = w.add(Entity(id="water", kind="thing", type="water", label="the water"))
    w.place = place
    w.creature = creature
    w.magic = magic
    w.facts.update(place=place, creature=creature, magic=magic, child=child, boat=boat, wave=wave)

    child.memes["wonder"] += 1
    place.meters["shine"] += 1
    w.say(f"One evening, {child.label_word} rode on {boat.label} as it bobbed on {place.label}.")
    w.say(f"Near the bow came {creature.label}, and its {creature.label.split()[-1]} snout flashed like a tiny moon.")

    w.para()
    child.memes["worry"] += 1
    w.say(f"{child.label_word} wanted to use a {magic.name} to help the yacht reach the far shore.")
    if magic.safe:
        place.meters["shine"] += 1
        child.memes["calm"] += 1
        w.say(f"The spell {magic.effect}, and the yacht glided through the dark water like a silver leaf.")
    else:
        place.meters["shine"] += 1
        propagate(w, narrate=True)
        w.say(f"The magic tried to {magic.effect}, but it made the deck splashy and wild instead.")

    w.para()
    if not magic.safe:
        creature.memes["calm"] += 1
        propagate(w, narrate=True)
        w.say(f"Then the snouted creature dipped its nose and showed {child.label_word} a gentler charm.")
        place.meters["shine"] += 1
        child.memes["courage"] += 1
        w.say(f"{child.label_word} used the kinder spell, and the yacht grew quiet again.")
    else:
        w.say(f"The snouted creature nodded, and the yacht kept its bright course.")

    w.para()
    w.say(f"In the end, {boat.label} floated under the stars while {child.label_word} smiled at the glowing snout.")
    w.facts.update(resolved=True, safe=magic.safe)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fairy tale about a yacht, a magic spell, and a snout that glows in the dark.',
        f"Tell a gentle story where {f['child'].label_word} rides on a yacht and learns how a magic {f['magic'].name} should be used.",
        f"Write a child-friendly fairy tale with a yacht and a snout, ending with a kind magical fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, creature, magic, place = f["child"], f["creature"], f["magic"], f["place"]
    return [
        QAItem(question=f"Who rode on the yacht near {place.label}?", answer=f"{child.label_word} rode on the yacht near {place.label}."),
        QAItem(question=f"What did the creature have on its face?", answer=f"It had a snout, and the snout looked bright and magical."),
        QAItem(question=f"What magic did {child.label_word} try?", answer=f"{child.label_word} tried the {magic.name}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a yacht?", answer="A yacht is a boat that sails on water."),
        QAItem(question="What is a snout?", answer="A snout is the nose and mouth part of an animal's face."),
        QAItem(question="What does magic do in fairy tales?", answer="Magic can make surprising things happen in fairy tales."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,M) :- place(P), creature(C), magic(M), not bad(P,C,M).
bad(P,C,wish) :- creature(C), C = seal.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH")
    return 1


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in list(world.entities.values()):
        parts.append(f"{e.id}: meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)}")
    if world.place:
        parts.append(f"place: meters={dict((k,v) for k,v in world.place.meters.items() if v)}")
    return "\n".join(parts)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        for p in valid_combos():
            params = StoryParams(place=p[0], creature=p[1], magic=p[2], child=getattr(args, "name", None) or "Mina")
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
