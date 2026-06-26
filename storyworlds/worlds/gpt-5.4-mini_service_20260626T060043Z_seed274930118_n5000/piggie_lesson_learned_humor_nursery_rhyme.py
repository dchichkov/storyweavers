#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/piggie_lesson_learned_humor_nursery_rhyme.py
========================================================================================================================

A small standalone storyworld for a piggie-shaped nursery-rhyme tale with a
gentle lesson learned and a bit of humor.

Premise:
- Piggie loves a silly game in the nursery and wants to keep playing after being
  told to be careful.

Tension:
- A tiny mess risk appears: a favorite bow, bib, or blanket could get spoiled.

Turn:
- A grown-up or helper notices the risk and offers a simple safer choice.

Resolution:
- Piggie learns the lesson, chooses the safer way, and the ending shows what
  changed: the mess is avoided and the mood becomes bright again.
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def v(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    indoor: bool
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
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
    type: str
    region: str
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
        self.weather: str = ""
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.weather = self.weather
        clone.fired = set(self.fired)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("sticky", "splashy"):
            if actor.m(mess) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spill", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.m(mess) + 1
                item.meters["dirty"] = item.m("dirty") + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.m("dirty") < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["work"] = carer.m("work") + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("guided", 0.0) < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["lesson"] = actor.memes.get("lesson", 0.0) + 1
        out.append("__lesson__")
    return out


CAUSAL_RULES = [_r_spill, _r_worry, _r_lesson]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if x != "__lesson__")
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.m("dirty") >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.m(activity.mess) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The nursery was snug and bright, with a little rug for feet to land just right."
    return f"{setting.place.capitalize()} looked neat, with space enough for a tiny treat."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little piggie with a round pink nose and a ready-to-go grin.")


def loves_game(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb}; {activity.gerund} made the day feel like a song.")


def gift(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id}'s {parent.label} gave {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} proudly.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "went to" if not world.setting.indoor else "came to"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, with a snort and a wiggle of glee.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"You\'ll get your {prize.label} {activity.soil}," {parent.label} said. "Let\'s be wise and kind."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"{hero.id} gave a tiny huff, then tried to {activity.rush}.")


def guide(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["guided"] = hero.memes.get("guided", 0.0) + 1
    world.say(f"Then {parent.label} held out a warm hand and showed {hero.id} a safer way.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        return None
    world.say(f'"How about we {gear_def.prep}?" {parent.label} asked, with a twinkle and a grin.')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1
    world.say(f"{hero.id} blinked, then nodded. {hero.id} learned the lesson: a safer choice can still be fun.")
    world.say(
        f"So they {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"and {prize.label} stayed clean and neat."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Piggie", hero_type: str = "piggie",
         parent_label: str = "mama pig") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label=parent_label))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_game(world, hero, activity)
    gift(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    guide(world, parent, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"bounce", "spill"}),
    "yard": Setting(place="the yard", indoor=False, affords={"mud", "bounce"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"spill"}),
}

ACTIVITIES = {
    "bounce": Activity(
        id="bounce",
        verb="bounce on the little rug",
        gerund="bouncing on the little rug",
        rush="bounce toward the toy chest",
        mess="sticky",
        soil="sticky and smudgy",
        zone={"feet"},
        weather="",
        keyword="bounce",
        tags={"bounce", "fun"},
    ),
    "spill": Activity(
        id="spill",
        verb="splash in the pudding",
        gerund="splashing in the pudding",
        rush="dash toward the pudding bowl",
        mess="sticky",
        soil="sticky and messy",
        zone={"hands", "mouth"},
        weather="",
        keyword="pudding",
        tags={"pudding", "mess"},
    ),
    "mud": Activity(
        id="mud",
        verb="dance in the mud",
        gerund="dancing in the mud",
        rush="trot toward the muddy patch",
        mess="splashy",
        soil="splashy and muddy",
        zone={"feet", "legs"},
        weather="sunny",
        keyword="mud",
        tags={"mud", "mess"},
    ),
}

PRIZES = {
    "bow": Prize(label="bow", phrase="a shiny red bow", type="bow", region="head"),
    "bib": Prize(label="bib", phrase="a clean little bib", type="bib", region="chest"),
    "blanket": Prize(label="blanket", phrase="a soft blue blanket", type="blanket", region="body", plural=False),
}

GEAR = [
    Gear(
        id="apron",
        label="a big apron",
        covers={"chest"},
        guards={"sticky"},
        prep="put on a big apron first",
        tail="walked back to the table with a big apron on",
    ),
    Gear(
        id="rainboots",
        label="rain boots",
        covers={"feet", "legs"},
        guards={"splashy"},
        prep="wear rain boots before the muddy fun",
        tail="went back out in rain boots",
        plural=True,
    ),
    Gear(
        id="hairclip",
        label="a little hair clip",
        covers={"head"},
        guards={"sticky"},
        prep="pin up the bow with a little hair clip",
        tail="tripped along happily with the hair clip in place",
    ),
]

PIG_NAMES = ["Piggie", "Pip", "Pippa", "Percy", "Penny"]
PARENT_LABELS = ["mama pig", "papa pig", "grandpig"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = _safe_lookup(ACTIVITIES, aid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, aid, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short nursery-rhyme story about {hero.id}, a silly little piggie, who wants to {act.verb}.',
        f'Tell a gentle story where {hero.id} and {parent.label} find a safer choice so {prize.phrase} stays clean.',
        f'Write a playful story for a young child with the words "{act.keyword}" and "lesson learned".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {prize.phrase} could get {act.soil}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that a safer choice can still be fun.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the problem?",
                answer=f"{gear.label} helped because it let {hero.id} play while {prize.label} stayed clean.",
            )
        )
    return qa


KNOWLEDGE = {
    "piggie": [
        (
            "What is a piggie?",
            "A piggie is a little pig, often round and pink, with a snout that likes to sniff and snuffle.",
        )
    ],
    "bounce": [
        (
            "Why do kids like bouncing?",
            "Bouncing feels bouncy and funny, and it can make little feet want to tap and hop.",
        )
    ],
    "mud": [
        (
            "What is mud?",
            "Mud is wet dirt. It can squish under your shoes and make a mess on your clothes.",
        )
    ],
    "pudding": [
        (
            "Why can pudding be messy?",
            "Pudding is soft and slippery, so it can splash, smear, and stick to hands and faces.",
        )
    ],
    "lesson": [
        (
            "What does it mean to learn a lesson?",
            "Learning a lesson means you understand something important and do better next time.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("piggie")
    if world.facts.get("gear"):
        tags.add("lesson")
    out: list[QAItem] = []
    for tag in ("piggie", "bounce", "mud", "pudding", "lesson"):
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
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not endanger {prize.label}.)"
    return f"(No story: no gear in this world actually protects {prize.label} from {activity.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Piggie nursery-rhyme storyworld with a lesson learned and a touch of humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(PIG_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=rng.choice(PARENT_LABELS))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, "piggie", params.parent)
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
    StoryParams(place="nursery", activity="bounce", prize="bib", name="Piggie", parent="mama pig"),
    StoryParams(place="yard", activity="mud", prize="bow", name="Pip", parent="papa pig"),
    StoryParams(place="kitchen", activity="spill", prize="blanket", name="Pippa", parent="grandpig"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(set(asp.atoms(model, 'valid')))} compatible combos:")
        for t in sorted(set(asp.atoms(model, "valid"))):
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
