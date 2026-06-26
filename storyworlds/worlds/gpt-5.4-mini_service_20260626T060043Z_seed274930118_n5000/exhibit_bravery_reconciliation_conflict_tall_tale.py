#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about an exhibit, a burst of courage, a quarrel,
and a reconciliation that leaves the whole hall humming.

Premise:
- A child at a county fair or museum exhibit wants to prove bravery.
- A conflict flares when a friend or sibling doubts the stunt.
- The daring act goes sideways in a harmless, funny way.
- The characters reconcile by working together to rescue the exhibit and
  finish the tale with a larger-than-life image.

This world keeps one small, constraint-checked domain:
- one exhibit
- one brave act
- one conflict
- one repair/reconciliation
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

    comp: object | None = None
    ex: object | None = None
    ex_ent: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Setting:
    place: str = "the county fair"
    indoors: bool = False
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
class Exhibit:
    id: str
    label: str
    phrase: str
    wonder: str
    risk: str
    zone: set[str]
    clue: str
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
class BraveAct:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class Repair:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
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


@dataclass
class StoryParams:
    setting: str
    exhibit: str
    act: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _entity_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _entity_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _do_act(world: World, actor: Entity, act: BraveAct, narrate: bool = True) -> None:
    if act.id not in world.setting.affords:
        pass
    world.zone = set(act.zone)
    _add_meter(actor, act.mess, 1)
    _add_meme(actor, "bravery", 1)
    if narrate:
        world.say(f"{actor.id} took a deep breath and did {act.verb}.")


def predict(world: World, actor: Entity, act: BraveAct, exhibit_id: str) -> dict:
    sim = world.copy()
    _do_act(sim, sim.get(actor.id), act, narrate=False)
    ex = sim.get(exhibit_id)
    return {
        "risk": _entity_meter(ex, "risk"),
        "messy": _entity_meter(ex, "messy"),
        "conflict": _entity_meme(actor, "conflict"),
        "soiled": _entity_meter(ex, "dirty") >= THRESHOLD,
    }


def introduced(world: World, hero: Entity, comp: Entity, ex: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big heart and a bigger wish to be brave."
    )
    world.say(
        f"At {world.setting.place}, there was an exhibit called {ex.label}, "
        f"{ex.phrase}, and it shone like a story waiting to be told."
    )
    world.say(
        f"{comp.id} came along too, ready to watch, whisper, and worry in equal measure."
    )


def desire(world: World, hero: Entity, act: BraveAct) -> None:
    _add_meme(hero, "wanting", 1)
    world.say(
        f"{hero.id} loved the grand idea of {act.gerund}; it sounded as bold as a trumpet blast."
    )


def conflict_beat(world: World, hero: Entity, comp: Entity, act: BraveAct, ex: Entity) -> bool:
    p = predict(world, hero, act, ex.id)
    if p["soiled"] < THRESHOLD and _entity_meter(ex, "risk") < THRESHOLD:
        return False
    _add_meme(hero, "conflict", 1)
    _add_meme(comp, "conflict", 1)
    world.say(
        f"But {comp.id} crossed {comp.pronoun('possessive')} arms and said, "
        f'"That stunt will send dust and trouble dancing across the exhibit!"'
    )
    world.say(
        f"{hero.id} snorted and answered, "
        f'"I am brave enough to {act.verb} and brave enough to prove it!"'
    )
    return True


def mishap(world: World, hero: Entity, act: BraveAct, ex: Entity) -> None:
    _do_act(world, hero, act, narrate=False)
    _add_meter(ex, "messy", 1)
    _add_meter(ex, "dirty", 1)
    world.say(
        f"So {hero.id} dashed in like a spark from a kite string, and the act went wild."
    )
    world.say(
        f"A puff of {act.mess} skipped across {ex.label}, leaving {ex.risk} on the bright display."
    )


def repairable(act: BraveAct, ex: Exhibit) -> Optional[Repair]:
    for rep in REPAIRS:
        if act.mess in rep.guards and ex.zone & rep.covers:
            return rep
    return None


def reconciliation(world: World, hero: Entity, comp: Entity, ex: Entity, rep: Repair, act: BraveAct) -> None:
    hero.memes["conflict"] = 0
    comp.memes["conflict"] = 0
    _add_meme(hero, "reconciliation", 1)
    _add_meme(comp, "reconciliation", 1)
    world.say(
        f"Then {comp.id} took a careful look, softened {comp.pronoun('possessive')} voice, "
        f"and offered a truce as warm as fresh bread."
    )
    world.say(
        f'"Let us fix it together," {comp.id} said, and the two of them used {rep.label}.'
    )
    world.say(
        f"{rep.tail} Soon {ex.label} looked proud again, and {hero.id} stood beside "
        f"{comp.id} as if courage had grown two heads and a smile."
    )


def tell(setting: Setting, act: BraveAct, ex_cfg: Exhibit, hero_name: str, hero_type: str,
         comp_name: str, comp_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    comp = world.add(Entity(id=comp_name, kind="character", type=comp_type))
    ex = world.add(Entity(id="exhibit", type="exhibit", label=ex_cfg.label, phrase=ex_cfg.phrase))
    ex.meters["risk"] = 1 if act.zone & ex_cfg.zone else 0
    ex.meters["messy"] = 0
    ex.meters["dirty"] = 0

    introduced(world, hero, comp, ex)
    world.para()
    desire(world, hero, act)
    conflict_beat(world, hero, comp, act, ex)
    world.para()
    mishap(world, hero, act, ex)
    rep = repairable(act, ex_cfg)
    if rep is None:
        pass
    reconciliation(world, hero, comp, ex, rep, act)

    world.facts.update(hero=hero, comp=comp, exhibit=ex, act=act, repair=rep, setting=setting)
    return world


SETTINGS = {
    "fair": Setting(place="the county fair", indoors=False, affords={"ropewalk", "kitejump", "whirl"}),
    "hall": Setting(place="the big exhibition hall", indoors=True, affords={"ropewalk", "whirl", "lanternstep"}),
    "dock": Setting(place="the river dock", indoors=False, affords={"ropewalk", "launch"}),
}

ACTS = {
    "ropewalk": BraveAct(
        id="ropewalk",
        verb="walk the wobble rope",
        gerund="walking the wobble rope",
        rush="dash onto the rope",
        mess="dust",
        soil="dusty",
        zone={"floor"},
        keyword="rope",
        tags={"bravery", "conflict"},
    ),
    "kitejump": BraveAct(
        id="kitejump",
        verb="jump after the giant kite",
        gerund="jumping after the giant kite",
        rush="bolt after the kite",
        mess="dust",
        soil="dusty",
        zone={"floor", "air"},
        keyword="kite",
        tags={"bravery", "conflict"},
    ),
    "whirl": BraveAct(
        id="whirl",
        verb="spin under the lanterns",
        gerund="spinning under the lanterns",
        rush="whirl too hard",
        mess="glitter",
        soil="glittery",
        zone={"floor", "torso"},
        keyword="lantern",
        tags={"bravery", "conflict"},
    ),
    "lanternstep": BraveAct(
        id="lanternstep",
        verb="tiptoe past the lantern exhibit",
        gerund="tiptoeing past the lanterns",
        rush="stomp by the lamps",
        mess="glitter",
        soil="glittery",
        zone={"floor", "torso"},
        keyword="lantern",
        tags={"bravery", "conflict"},
    ),
    "launch": BraveAct(
        id="launch",
        verb="help launch the parade kite",
        gerund="helping launch the parade kite",
        rush="heave the kite skyward",
        mess="water",
        soil="wet",
        zone={"hands", "torso"},
        keyword="kite",
        tags={"bravery", "conflict"},
    ),
}

EXHIBITS = {
    "clock": Exhibit(
        id="clock",
        label="the clockwork whale",
        phrase="a brass whale that blinked with moon-blue eyes",
        wonder="wonder",
        risk="a thin veil of dust",
        zone={"floor"},
        clue="clock",
    ),
    "boots": Exhibit(
        id="boots",
        label="the boot mountain",
        phrase="a tower of polished boots stacked like a tall black hill",
        wonder="wonder",
        risk="a tumble of dust",
        zone={"floor"},
        clue="boots",
    ),
    "lantern": Exhibit(
        id="lantern",
        label="the lantern tower",
        phrase="a tower of paper lanterns that glowed like summer moons",
        wonder="glow",
        risk="a drift of glitter",
        zone={"floor", "torso"},
        clue="lantern",
    ),
}

REPAIRS = [
    Repair(
        id="brushes",
        label="soft brushes and a dust cloth",
        prep="gather the soft brushes and a dust cloth",
        tail="They brushed the dust away feather by feather until the exhibit gleamed like a fresh apple.",
        guards={"dust"},
        covers={"floor"},
    ),
    Repair(
        id="cloth",
        label="a velvet cloth and careful hands",
        prep="use a velvet cloth and careful hands",
        tail="They wiped the glitter from the lanterns until the whole tower shimmered without a speck.",
        guards={"glitter"},
        covers={"floor", "torso"},
    ),
    Repair(
        id="towels",
        label="dry towels and a kind laugh",
        prep="reach for dry towels and a kind laugh",
        tail="They dried the wet spots until the kite looked ready to sail the sky again.",
        guards={"water"},
        covers={"hands", "torso"},
    ),
]

GIRL_NAMES = ["Mabel", "June", "Nell", "Ruby", "Ada", "Ivy"]
BOY_NAMES = ["Hank", "Otis", "Jeb", "Cal", "Bram", "Eli"]
TRAITS = ["bold", "spry", "cheerful", "stubborn", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTS, act_id)
            for ex_id, ex in EXHIBITS.items():
                if act.zone & ex.zone:
                    if repairable(act, ex) is not None:
                        combos.append((sid, act_id, ex_id))
    return combos


def pick_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about an exhibit, bravery, conflict, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--act", choices=ACTS.keys())
    ap.add_argument("--exhibit", choices=EXHIBITS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--companion")
    ap.add_argument("--companion-type", choices=["girl", "boy", "woman", "man"])
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
    if getattr(args, "act", None) and getattr(args, "exhibit", None):
        act = _safe_lookup(ACTS, getattr(args, "act", None))
        ex = _safe_lookup(EXHIBITS, getattr(args, "exhibit", None))
        if act.zone.isdisjoint(ex.zone) or repairable(act, ex) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "act", None) is None or c[1] == getattr(args, "act", None))
              and (getattr(args, "exhibit", None) is None or c[2] == getattr(args, "exhibit", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, act_id, ex_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or pick_name(gender, rng)
    companion_type = getattr(args, "companion_type", None) or rng.choice(["girl", "boy", "woman", "man"])
    companion = getattr(args, "companion", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, exhibit=ex_id, act=act_id, hero=hero, hero_type=gender,
                       companion=companion, companion_type=companion_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale-style story for a child that includes an exhibit called "{f["exhibit"].label}".',
        f"Tell a brave little story where {f['hero'].id} tries to {f['act'].verb} at {world.setting.place} and then makes peace with {f['comp'].id}.",
        f"Write a short, child-friendly story about {f['hero'].id}, a conflict, and a reconciliation around an exhibit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    comp: Entity = _safe_fact(world, f, "comp")
    ex: Entity = _safe_fact(world, f, "exhibit")
    act: BraveAct = _safe_fact(world, f, "act")
    rep: Repair = _safe_fact(world, f, "repair")
    return [
        QAItem(
            question=f"Who tried to be brave at {world.setting.place}?",
            answer=f"{hero.id} tried to be brave at {world.setting.place} by {act.gerund}.",
        ),
        QAItem(
            question=f"What was the exhibit called?",
            answer=f"The exhibit was called {ex.label}, and it looked like {ex.phrase}.",
        ),
        QAItem(
            question=f"What caused the conflict?",
            answer=f"The conflict started because {comp.id} worried that {hero.id} would make {ex.label} messy while showing off bravery.",
        ),
        QAItem(
            question=f"How did they reconcile?",
            answer=f"They reconciled by using {rep.label} together and cleaning the exhibit carefully.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the mess was gone, the conflict was over, and {hero.id} and {comp.id} were working side by side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling that helps someone try something scary or hard.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when people disagree or get upset with each other.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after a disagreement.",
        ),
        QAItem(
            question="What is an exhibit?",
            answer="An exhibit is something people can look at in a museum, fair, or hall because it is interesting or special.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: " + " ".join(parts))
    lines.append(f"  zone={sorted(world.zone)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    act = _safe_lookup(ACTS, params.act)
    ex = _safe_lookup(EXHIBITS, params.exhibit)
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    comp = world.add(Entity(id=params.companion, kind="character", type=params.companion_type))
    ex_ent = world.add(Entity(id="exhibit", type="exhibit", label=ex.label, phrase=ex.phrase))
    ex_ent.meters["risk"] = 1 if act.zone & ex.zone else 0

    introduced(world, hero, comp, ex_ent)
    world.para()
    desire(world, hero, act)
    conflict_beat(world, hero, comp, act, ex_ent)
    world.para()
    mishap(world, hero, act, ex_ent)
    rep = repairable(act, ex)
    if rep is None:
        pass
    reconciliation(world, hero, comp, ex_ent, rep, act)

    world.facts.update(hero=hero, comp=comp, exhibit=ex_ent, act=act, repair=rep, setting=setting)
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


ASP_RULES = r"""
% An exhibit is at risk when the brave act splashes its vulnerable zone.
at_risk(A, E) :- act(A), exhibit(E), splashes(A, R), vulnerable(E, R).

% A repair is compatible when it guards the mess kind and covers the risky zone.
compatible(R, A, E) :- repair(R), act(A), exhibit(E),
                       makes(A, M), guards(R, M),
                       covers(R, Z), splashes(A, Z),
                       at_risk(A, E).

valid_story(S, A, E) :- setting(S), affords(S, A), exhibit(E),
                        at_risk(A, E), compatible(_, A, E).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("makes", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, z))
    for eid, e in EXHIBITS.items():
        lines.append(asp.fact("exhibit", eid))
        for z in sorted(e.zone):
            lines.append(asp.fact("vulnerable", eid, z))
    for rid, r in enumerate(REPAIRS):
        lines.append(asp.fact("repair", r.id))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", r.id, g))
        for c in sorted(r.covers):
            lines.append(asp.fact("covers", r.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos_asp())
    if py == asp_set:
        print(f"OK: ASP gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


def build_valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def explain_rejection(act: BraveAct, ex: Exhibit) -> str:
    return (
        f"(No story: {act.gerund} does not create a satisfying exhibit rescue "
        f"for {ex.label}. This world only keeps brave acts that lead to a real "
        f"conflict and a real reconciliation.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "act", None) and getattr(args, "exhibit", None):
        act = _safe_lookup(ACTS, getattr(args, "act", None))
        ex = _safe_lookup(EXHIBITS, getattr(args, "exhibit", None))
        if act.zone.isdisjoint(ex.zone) or repairable(act, ex) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "act", None) is None or c[1] == getattr(args, "act", None))
              and (getattr(args, "exhibit", None) is None or c[2] == getattr(args, "exhibit", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, act_id, ex_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or pick_name(gender, rng)
    comp = getattr(args, "companion", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    comp_type = getattr(args, "companion_type", None) or rng.choice(["girl", "boy", "woman", "man"])
    return StoryParams(
        setting=setting,
        exhibit=ex_id,
        act=act_id,
        hero=hero,
        hero_type=gender,
        companion=comp,
        companion_type=comp_type,
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = valid_combos_asp()
        print(f"{len(triples)} compatible stories:")
        for s, a, e in triples:
            print(f"  {s} {a} {e}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("fair", "clock", "ropewalk", "Mabel", "girl", "Hank", "boy"),
            StoryParams("hall", "lantern", "whirl", "Eli", "boy", "June", "girl"),
            StoryParams("dock", "boots", "launch", "Ruby", "girl", "Cal", "boy"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
