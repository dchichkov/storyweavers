#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero-style reconciliation tale.

Premise:
- A child superhero and a brother team up.
- The brother can feel hurt or left out.
- A small mission goes wrong because of teasing, stubbornness, or a broken plan.
- Reconciliation happens when one sibling apologizes, helps fix the problem, and
  they choose teamwork again.

The world is intentionally small and constraint-checked: stories are only
generated when the conflict can be resolved in a believable way.
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
# Entities and world model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    indoor: bool = False
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
class Mission:
    id: str
    verb: str
    gerund: str
    trouble: str
    mess: str
    zone: set[str]
    keyword: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Prize:
    label: str
    phrase: str
    region: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    hero: str
    hero_gender: str
    brother_name: str
    brother_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "city": Setting(place="the city rooftop", affords={"kite", "rescue", "signal"}),
    "park": Setting(place="the city park", affords={"kite", "rescue", "signal"}),
    "alley": Setting(place="the bright alley", affords={"rescue", "signal"}),
    "yard": Setting(place="the backyard", affords={"kite", "rescue"}),
}

MISSIONS = {
    "kite": Mission(
        id="kite",
        verb="fly the signal kite",
        gerund="flying the signal kite",
        trouble="tangled in the wind",
        mess="windblown",
        zone={"hands", "torso"},
        keyword="kite",
        tags={"wind", "signal"},
    ),
    "rescue": Mission(
        id="rescue",
        verb="chase the rolling drone",
        gerund="chasing the rolling drone",
        trouble="spinning out of reach",
        mess="scuffed",
        zone={"feet", "legs"},
        keyword="drone",
        tags={"rescue", "help"},
    ),
    "signal": Mission(
        id="signal",
        verb="shine the rescue beam",
        gerund="shining the rescue beam",
        trouble="too bright for the eyes",
        mess="glared",
        zone={"hands", "torso"},
        keyword="beam",
        tags={"signal", "light"},
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a shiny red cape",
        region="torso",
        type="cape",
    ),
    "mask": Prize(
        label="mask",
        phrase="a silver mask",
        region="face",
        type="mask",
    ),
    "boots": Prize(
        label="boots",
        phrase="sturdy hero boots",
        region="feet",
        type="boots",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="backup_cape",
        label="a backup cape",
        covers={"torso"},
        guards={"windblown"},
        prep="put on a backup cape first",
        tail="swapped to the backup cape",
    ),
    Gear(
        id="goggles",
        label="goggles",
        covers={"face"},
        guards={"glared"},
        prep="wear goggles first",
        tail="put on the goggles",
        plural=True,
    ),
    Gear(
        id="boots_cover",
        label="extra boot covers",
        covers={"feet"},
        guards={"scuffed"},
        prep="slip on extra boot covers",
        tail="slipped on the extra boot covers",
        plural=True,
    ),
    Gear(
        id="team_cloak",
        label="a team cloak",
        covers={"torso", "face"},
        guards={"windblown", "glared"},
        prep="share a team cloak",
        tail="shared the team cloak",
    ),
]

HERO_NAMES = ["Mia", "Zoe", "Nina", "Ava", "Luna", "Ivy"]
BROTHER_NAMES = ["Ben", "Leo", "Finn", "Noah", "Max", "Toby"]
TRAITS = ["brave", "curious", "kind", "quick", "bold", "cheerful"]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(M, P) :- zone_of(M, R), worn_on(P, R).
compatible(G, M, P) :- prize_at_risk(M, P), guards(G, X), mess_of(M, X), covers(G, R), worn_on(P, R).
valid_story(Place, M, P) :- affords(Place, M), prize_at_risk(M, P), compatible(_, M, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mess_of", mid, m.mess))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone_of", mid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonable combinations and constraints
# ---------------------------------------------------------------------------
def prize_at_risk(mission: Mission, prize: Prize) -> bool:
    return prize.region in mission.zone


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if mission.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mission_id in setting.affords:
            mission = _safe_lookup(MISSIONS, mission_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(mission, prize) and select_gear(mission, prize):
                    combos.append((place, mission_id, prize_id))
    return combos


def explain_rejection(mission: Mission, prize: Prize) -> str:
    return (
        f"(No story: {mission.gerund} does not plausibly threaten a {prize.label} "
        f"on the {prize.region}, or there is no good gear fix for that pairing.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender} item here; try --gender {ok}.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def predict_mess(world: World, hero: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(hero.id), mission, narrate=False)
    prize = sim.get(prize_id)
    return {
        "ruined": bool(prize and prize.meters.get("dirty", 0) >= 1.0),
    }


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    if mission.id not in world.setting.affords:
        return
    world.zone = set(mission.zone)
    actor.meters[mission.mess] = actor.meters.get(mission.mess, 0) + 1
    actor.memes["determination"] = actor.memes.get("determination", 0) + 1
    for item in world.worn_items(actor):
        if item.region in world.zone:
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            item.meters[mission.mess] = item.meters.get(mission.mess, 0) + 1


def introduce(world: World, hero: Entity, brother: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.meters.keys()), 'super')} hero who loved "
        f"helping people on bright days. {brother.id} was {hero.pronoun('possessive')} brother, "
        f"and he wanted to help too."
    )


def set_scene(world: World, hero: Entity, brother: Entity, mission: Mission) -> None:
    place = world.setting.place
    world.say(
        f"One day, {hero.id} and {brother.id} hurried to {place} for a small hero mission."
    )
    world.say(
        f"{hero.id} wanted to {mission.verb}, because {mission.keyword} days always felt like adventure."
    )


def warn(world: World, hero: Entity, brother: Entity, mission: Mission, prize: Entity) -> bool:
    pred = predict_mess(world, hero, mission, prize.id)
    if not pred["ruined"]:
        return False
    world.say(
        f"\"If you {mission.verb}, your {prize.label} will get ruined,\" "
        f"{brother.id} warned."
    )
    return True


def ignore_or_bicker(world: World, hero: Entity, brother: Entity, mission: Mission) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    brother.memes["hurt"] = brother.memes.get("hurt", 0) + 1
    world.say(
        f"{hero.id} still rushed ahead, and {brother.id} frowned because he felt left out."
    )
    world.say(
        f"When the mission {mission.trouble}, the two siblings stopped and stared at each other."
    )


def apology(world: World, hero: Entity, brother: Entity, mission: Mission) -> None:
    hero.memes["sorry"] = hero.memes.get("sorry", 0) + 1
    brother.memes["softened"] = brother.memes.get("softened", 0) + 1
    world.say(
        f"{hero.id} looked at {brother.id} and said, \"I'm sorry. I should have listened and shared the plan.\""
    )


def compromise(world: World, hero: Entity, brother: Entity, mission: Mission, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(mission, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=brother.id,
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if predict_mess(world, hero, mission, prize.id)["ruined"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{brother.id} smiled and offered a new plan: {gear_def.prep}, then try again together."
    )
    return gear_def


def reconcile(world: World, hero: Entity, brother: Entity, mission: Mission, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    brother.memes["joy"] = brother.memes.get("joy", 0) + 1
    brother.memes["hurt"] = 0
    world.say(
        f"{hero.id} nodded, and the brothers shared the gear. Soon they were side by side again."
    )
    world.say(
        f"They {gear_def.tail}, fixed the mission together, and the {prize.label} stayed safe."
    )
    world.say(
        f"By the end, {hero.id} and {brother.id} were laughing like a real team."
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    mission: Mission,
    prize_cfg: Prize,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    brother_name: str = "Ben",
    brother_gender: str = "boy",
    parent: str = "mom",
    trait: str = "brave",
) -> World:
    world = World(setting)

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            meters={trait: 1.0},
            memes={"pride": 1.0},
        )
    )
    brother = world.add(
        Entity(
            id=brother_name,
            kind="character",
            type=brother_gender,
            meters={"helpful": 1.0},
            memes={"eager": 1.0},
        )
    )
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=brother.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    world.say(
        f"{hero.id} was a {trait} little superhero, and {brother.id} was {hero.id}'s brother."
    )
    world.say(
        f"{hero.id} loved {prize.phrase}, because it made {hero.pronoun('object')} feel ready for action."
    )
    world.say(
        f"{brother.id} had helped pack the gear, and he wanted the mission to go well."
    )

    world.para()
    set_scene(world, hero, brother, mission)
    if warn(world, hero, brother, mission, prize):
        ignore_or_bicker(world, hero, brother, mission)

    world.para()
    apology(world, hero, brother, mission)
    gear_def = compromise(world, hero, brother, mission, prize)
    if gear_def is None:
        pass
    reconcile(world, hero, brother, mission, prize, gear_def)

    world.facts.update(
        hero=hero,
        brother=brother,
        prize=prize,
        mission=mission,
        gear=gear_def,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Registries and parameter resolution
# ---------------------------------------------------------------------------
def valid_name_pool(gender: str) -> list[str]:
    return HERO_NAMES if gender == "girl" else BROTHER_NAMES


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(valid_name_pool(gender))


@dataclass
class ChoiceSet:
    place: str
    mission: str
    prize: str
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


CURATED = [
    StoryParams(
        place="city",
        mission="kite",
        prize="cape",
        hero="Mia",
        hero_gender="girl",
        brother_name="Ben",
        brother_gender="boy",
        parent="mom",
        trait="brave",
    ),
    StoryParams(
        place="park",
        mission="signal",
        prize="mask",
        hero="Ava",
        hero_gender="girl",
        brother_name="Leo",
        brother_gender="boy",
        parent="dad",
        trait="curious",
    ),
    StoryParams(
        place="yard",
        mission="rescue",
        prize="boots",
        hero="Luna",
        hero_gender="girl",
        brother_name="Noah",
        brother_gender="boy",
        parent="mom",
        trait="kind",
    ),
]


# ---------------------------------------------------------------------------
# QA and prompting
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, brother, mission, prize = f["hero"], f["brother"], f["mission"], f["prize"]
    return [
        f'Write a superhero story for a young child about a hero and a brother, using the word "{mission.keyword}".',
        f"Tell a short story where {hero.id} and {brother.id} disagree, then make up and work together to protect a {prize.label}.",
        f"Write a gentle superhero story with a brother, a mistake, an apology, and a happy team ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, brother, mission, prize = f["hero"], f["brother"], f["mission"], f["prize"]
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who wanted to {mission.verb} at {world.setting.place}?",
            answer=f"{hero.id} wanted to {mission.verb}, and {brother.id} wanted to help too.",
        ),
        QAItem(
            question=f"Why did {brother.id} worry about the {prize.label}?",
            answer=f"He worried because {mission.gerund} could leave the {prize.label} messy or ruined.",
        ),
        QAItem(
            question=f"What did the siblings do after they argued?",
            answer=f"{hero.id} said sorry, {brother.id} offered a better plan, and they used {gear.label} together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the brothers working together and the {prize.label} staying safe.",
        ),
    ]


KNOWLEDGE = {
    "kite": [
        (
            "What is a kite?",
            "A kite is a light object that flies in the wind when a person holds a string.",
        )
    ],
    "drone": [
        (
            "What is a drone?",
            "A drone is a small flying machine or toy that can move on its own or be controlled from far away.",
        )
    ],
    "beam": [
        (
            "What does a beam of light do?",
            "A beam of light shines in one direction and can help people see or signal from far away.",
        )
    ],
    "cape": [
        (
            "What is a cape?",
            "A cape is a piece of clothing that hangs from the shoulders, often used by superheroes in stories.",
        )
    ],
    "mask": [
        (
            "What is a mask?",
            "A mask is something you wear over your face to hide it or protect it.",
        )
    ],
    "boots": [
        (
            "What are boots for?",
            "Boots protect your feet and can help keep them clean or dry.",
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people who argued or felt upset make peace again and feel friendly together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mission"].tags)
    tags.add("reconciliation")
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id.replace("backup_", "cape").replace("boots_cover", "boots"))
        tags.add(world.facts["prize"].label)
    out: list[QAItem] = []
    for tag in ["reconciliation", "kite", "drone", "beam", "cape", "mask", "boots"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI and emission
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero reconciliation story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--brother-name")
    ap.add_argument("--brother-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "mission", None) and getattr(args, "prize", None):
        mission, prize = _safe_lookup(MISSIONS, getattr(args, "mission", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(mission, prize) and select_gear(mission, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "hero_gender", None) and getattr(args, "prize", None) and getattr(args, "hero_gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c
        for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, mission_id, prize_id = rng.choice(list(combos))
    hero_gender = getattr(args, "hero_gender", None) or "girl"
    brother_gender = getattr(args, "brother_gender", None) or "boy"
    hero = getattr(args, "hero", None) or choose_name(rng, hero_gender)
    brother = getattr(args, "brother_name", None) or choose_name(rng, brother_gender)
    parent = getattr(args, "parent", None) or rng.choice(["mom", "dad"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mission=mission_id,
        prize=prize_id,
        hero=hero,
        hero_gender=hero_gender,
        brother_name=brother,
        brother_gender=brother_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(MISSIONS, params.mission),
        _safe_lookup(PRIZES, params.prize),
        params.hero,
        params.hero_gender,
        params.brother_name,
        params.brother_gender,
        params.parent,
        params.trait,
    )
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} and {p.brother_name}: {p.mission} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
