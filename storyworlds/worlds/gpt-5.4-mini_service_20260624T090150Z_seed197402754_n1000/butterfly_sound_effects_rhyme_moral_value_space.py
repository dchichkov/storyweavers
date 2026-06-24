#!/usr/bin/env python3
"""
A small space-adventure storyworld about a butterfly, playful sound effects,
gentle rhyme, and a moral choice that changes the ending.

This world is built around a tiny spaceship garden cruise:
a butterfly wants to chase glowing space petals, but a careful helper must
choose between showing off and doing the kind thing. The story model tracks
physical meters and emotional memes so the ending depends on what actually
happened in the world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, amount: float) -> None:
        self.meters[key] = self.m(key) + amount

    def add_e(self, key: str, amount: float) -> None:
        self.memes[key] = self.e(key) + amount

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"butterfly"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
class Setting:
    place: str
    wonder: str
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
class Action:
    id: str
    verb: str
    gerund: str
    sound: str
    rhyme_a: str
    rhyme_b: str
    mess: str
    zone: set[str]
    moral: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    effect: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraph_breaks: list[int] = []
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    chunks.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            chunks.append(" ".join(buf))
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "orbital_garden": Setting(
        place="the orbital garden",
        wonder="a ring of glass petals circling a silver ship",
        affords={"chase", "sing"},
    ),
    "moon_dock": Setting(
        place="the moon dock",
        wonder="small flags fluttering beside a rocket-shaped kiosk",
        affords={"chase", "help"},
    ),
    "star_hatch": Setting(
        place="the star hatch",
        wonder="a little hatch window that opened onto glittering sky",
        affords={"sing", "help"},
    ),
}

ACTIONS = {
    "chase": Action(
        id="chase",
        verb="chase the glowing butterfly lights",
        gerund="chasing glowing lights",
        sound="zip-zip!",
        rhyme_a="light",
        rhyme_b="bright",
        mess="scatter",
        zone={"near", "air"},
        moral="It is better to be gentle than to grab what shines.",
    ),
    "sing": Action(
        id="sing",
        verb="sing a space song",
        gerund="singing a space song",
        sound="la-la-la!",
        rhyme_a="moon",
        rhyme_b="tune",
        mess="hum",
        zone={"air"},
        moral="A kind voice can calm a worried friend.",
    ),
    "help": Action(
        id="help",
        verb="help fix the drifting lantern",
        gerund="helping fix the drifting lantern",
        sound="click-clack!",
        rhyme_a="glow",
        rhyme_b="show",
        mess="steady",
        zone={"hands"},
        moral="Helping is a brave way to shine.",
    ),
}

PRIZES = {
    "star_bean": Prize(
        id="star_bean",
        label="star bean",
        phrase="a tiny star bean in a clear pod",
        region="hands",
    ),
    "moon_ribbon": Prize(
        id="moon_ribbon",
        label="moon ribbon",
        phrase="a pale moon ribbon tied to the rail",
        region="air",
    ),
    "glow_map": Prize(
        id="glow_map",
        label="glow map",
        phrase="a little glow map with bright lanes",
        region="hands",
    ),
}

AIDS = {
    "soft_gloves": Aid(
        id="soft_gloves",
        label="soft gloves",
        prep="put on soft gloves first",
        effect="kept the hands safe and steady",
    ),
    "song_lamp": Aid(
        id="song_lamp",
        label="a song lamp",
        prep="turn on a song lamp",
        effect="made the room feel calm and warm",
    ),
}

BUTTERFLY_NAMES = ["Milo", "Luna", "Pip", "Nova", "Zia", "Penny"]
HELPER_NAMES = ["Captain Bea", "Mira", "Tao", "Rin", "Jules"]


@dataclass
class StoryParams:
    setting: str
    action: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
% A prize is at risk when the action's zone overlaps the prize region.
at_risk(A, P) :- action(A), prize(P), zone(A, R), region(P, R).

% An aid is useful only if it helps with the risky region.
useful(Aid, A, P) :- at_risk(A, P), aid(Aid), aid_region(Aid, R), region(P, R), aid_covers(Aid, R).

compatible(Place, A, P) :- setting(Place), affords(Place, A), at_risk(A, P), useful(_, A, P).
compat_story(Place, A, P) :- compatible(Place, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("aid_covers", aid, "hands"))
        lines.append(asp.fact("aid_region", aid, "hands"))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            action = _safe_lookup(ACTIONS, aid)
            for pid, prize in PRIZES.items():
                if prize.region in action.zone and prize.region in {"hands", "air"}:
                    combos.append((place, aid, pid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def risk_prize(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def choose_aid(action: Action, prize: Prize) -> Optional[Aid]:
    if prize.region == "hands":
        return AIDS["soft_gloves"]
    return None


def predict_mess(world: World, hero: Entity, action: Action, prize: Prize) -> bool:
    sim = world.copy()
    do_action(sim, sim.get(hero.id), action, prize, narrate=False)
    return sim.get(prize.id).m("messed") >= THRESHOLD


def do_action(world: World, hero: Entity, action: Action, prize: Prize, narrate: bool = True) -> None:
    hero.add_m(action.mess, 1)
    hero.add_e("excitement", 1)
    if risk_prize(action, prize):
        prize.add_m("messed", 1)
        if narrate:
            world.say(f"{action.sound} The motion sent tiny sparkles over the {prize.label}.")
    if narrate:
        world.say(f"The butterfly kept {action.gerund} in {world.setting.place}.")


def intro(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {world.setting.wonder} glowed softly while "
        f"{hero.id} the butterfly fluttered near the rails."
    )
    world.say(
        f"{helper.id} watched the little wings and smiled at the bright sky."
    )


def lure(world: World, hero: Entity, action: Action) -> None:
    hero.add_e("want", 1)
    world.say(
        f"{hero.id} loved the sparkle of the drifting lights, and the whole path seemed to sing, "
        f'"{action.rhyme_a}, {action.rhyme_b}!"'
    )


def warn(world: World, helper: Entity, hero: Entity, action: Action, prize: Prize) -> None:
    if predict_mess(world, hero, action, prize):
        helper.add_e("worry", 1)
        world.say(
            f'{helper.id} said, "Careful, little wings. If you go too fast, that {prize.label} may get swept away."'
        )


def refuse_or_try(world: World, hero: Entity, action: Action) -> None:
    hero.add_e("stubbornness", 1)
    world.say(
        f"{hero.id} wanted to rush ahead anyway, and the air answered with a soft {action.sound}."
    )


def help_and_turn(world: World, helper: Entity, hero: Entity, action: Action, prize: Prize) -> Optional[Aid]:
    aid = choose_aid(action, prize)
    if aid is None:
        return None
    world.say(
        f"{helper.id} reached for a kind fix and said, \"{aid.prep}. Then we can {action.verb}.\""
    )
    world.say(f"{aid.effect}.")
    return aid


def accept(world: World, hero: Entity, helper: Entity, action: Action, prize: Prize, aid: Aid) -> None:
    hero.add_e("calm", 1)
    hero.memes["stubbornness"] = 0
    world.say(
        f'{hero.id} nodded, and the two of them shared a rhyme: "{action.rhyme_a}, {action.rhyme_b}, let\'s do it with care."'
    )
    world.say(
        f"With {aid.label}, {hero.id} could {action.verb} safely, and the {prize.label} stayed bright."
    )
    world.say(
        f"The moral was simple: {action.moral}"
    )


def tell(setting: Setting, action: Action, prize: Prize, name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="butterfly", label="butterfly"))
    helper = world.add(Entity(id=helper_name, kind="character", type="captain", label="helper"))
    prize_ent = world.add(Entity(id=prize.id, type="thing", label=prize.label, phrase=prize.phrase))

    intro(world, hero, helper)
    world.para()
    lure(world, hero, action)
    warn(world, helper, hero, action, prize_ent)
    refuse_or_try(world, hero, action)
    world.para()
    aid = help_and_turn(world, helper, hero, action, prize_ent)
    if aid is not None:
        accept(world, hero, helper, action, prize_ent, aid)

    world.facts.update(hero=hero, helper=helper, prize=prize_ent, action=action, aid=aid, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    action: Action = _safe_fact(world, f, "action")
    prize: Prize = _safe_fact(world, f, "prize")
    return [
        f'Write a tiny space adventure about a butterfly named {hero.id} who wants to {action.verb} near {world.setting.place}.',
        f'Tell a story with sound effects like "{action.sound}" and a rhyme like "{action.rhyme_a}, {action.rhyme_b}".',
        f'Write a gentle story for young children where kindness helps keep a {prize.label} safe in space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    action: Action = _safe_fact(world, f, "action")
    prize: Entity = _safe_fact(world, f, "prize")
    aid: Optional[Aid] = _safe_fact(world, f, "aid")
    return [
        QAItem(
            question=f"Who was the butterfly in the story?",
            answer=f"The butterfly was {hero.id}, and {helper.id} helped {hero.pronoun('object')} stay calm.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {action.verb}. The story showed that wish with the sound effect {action.sound}.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the {prize.label}?",
            answer=f"{helper.id} worried because the action could sweep the {prize.label} into the path and make it messy.",
        ),
    ] + (
        [
            QAItem(
                question="What helped the butterfly do the job safely?",
                answer=f"The {aid.label} helped, because it made the plan careful and kind.",
            ),
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the butterfly safely {action.gerund} and the {prize.label} still bright.",
            ),
        ] if aid else []
    )


KNOWLEDGE = {
    "butterfly": [
        QAItem(
            question="What is a butterfly?",
            answer="A butterfly is an insect with wings that can flutter from place to place.",
        )
    ],
    "space": [
        QAItem(
            question="What is space?",
            answer="Space is the wide area beyond Earth where stars, planets, and moons are found.",
        )
    ],
    "sound": [
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help the reader imagine what something feels and sounds like.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bright and light.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson the story wants to teach, like being kind or careful.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["butterfly"])
    out.extend(KNOWLEDGE["space"])
    out.extend(KNOWLEDGE["sound"])
    out.extend(KNOWLEDGE["rhyme"])
    out.extend(KNOWLEDGE["moral"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="orbital_garden", action="chase", prize="star_bean", name="Luna", helper="Captain Bea"),
    StoryParams(setting="moon_dock", action="help", prize="glow_map", name="Pip", helper="Mira"),
    StoryParams(setting="star_hatch", action="sing", prize="moon_ribbon", name="Nova", helper="Tao"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure butterfly storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, action, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(BUTTERFLY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, action=action, prize=prize, name=name, helper=helper, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.helper)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.setting} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
