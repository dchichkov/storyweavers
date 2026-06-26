#!/usr/bin/env python3
"""
storyworlds/worlds/spanish_friendship_twist_rhyming_story.py
=============================================================

A small story world about friendship, a Spanish word or two, and a twist that
turns worry into warm togetherness.

Premise:
- Two friends are making a cheerful card, poster, or note with Spanish words.
- A tiny twist makes one friend misread the message.
- The friends talk, fix the mix-up, and end with a brighter bond.

The prose aims for a soft rhyming-story feel: short, child-facing lines with
light rhyme and a clear turn from misunderstanding to friendship.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: str = ""
    card: object | None = None
    friend: object | None = None
    hero: object | None = None
    ribbon: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    mood: str
    supports: set[str] = field(default_factory=set)
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
    twist: str
    rhyme_a: str
    rhyme_b: str
    mess: str
    zone: set[str]
    keyword: str = "spanish"
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
    label: str
    phrase: str
    type: str
    region: str
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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        return c


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.carried_by != actor.id:
                continue
            if item.region not in world.zone:
                continue
            sig = ("smudge", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] = item.meters.get("mess", 0.0) + 1
            item.meters["tired"] = item.meters.get("tired", 0.0) + 1
            out.append(f"{item.label.capitalize()} got a little smudged.")
    return out


CAUSAL_RULES = [
    _r_smudge,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_line(setting: Setting) -> str:
    return f"The {setting.place} felt {setting.mood}, all bright and neat."


def intro_line(hero: Entity, friend: Entity) -> str:
    return f"{hero.id} and {friend.id} were friends who liked to make things sweet."


def predict_mixup(world: World, hero: Entity, act: Activity, prize: Prize) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["mess"] = 1
    sim.zone = set(act.zone)
    for item in sim.entities.values():
        if item.carried_by == hero.id and item.region in sim.zone:
            item.meters["mess"] = item.meters.get("mess", 0) + 1
    return {
        "smudged": any(
            item.carried_by == hero.id and item.region in sim.zone
            for item in sim.entities.values()
        )
    }


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.supports:
        pass
    world.zone = set(activity.zone)
    actor.meters["mess"] = actor.meters.get("mess", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(world: World, activity: Activity, prize: Prize, hero: Entity, friend: Entity, gear: Gear) -> World:
    card = world.add(Entity(
        id="card", type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=friend.id, region=prize.region, plural=prize.plural,
    ))
    ribbon = world.add(Entity(
        id="ribbon", type="ribbon", label="a ribbon", owner=hero.id, region="torso"
    ))
    card.carried_by = hero.id
    ribbon.carried_by = hero.id

    hero.memes["love"] = 1
    friend.memes["love"] = 1
    hero.memes["trust"] = 1
    friend.memes["trust"] = 1

    world.say(intro_line(hero, friend))
    world.say(
        f"They wanted to make a {prize.label} for a neighbor new and bright, "
        f"with a little bit of {activity.keyword} and a lot of friendship light."
    )
    world.say(
        f"{hero.id} wrote 'hola' in careful loops; {friend.id} smiled, warm and neat. "
        f"The letters danced like tiny bells, all happy, soft, and sweet."
    )

    world.para()
    world.say(setting_line(world.setting))
    world.say(
        f"Then came the twist: the ribbon slid, and one sticker flipped away. "
        f"Now the card looked almost right, but not quite right that day."
    )
    world.say(
        f"{friend.id} frowned and said, 'Did we just write the wrong word by mistake?'"
    )
    world.say(
        f"{hero.id} felt a pinch of worry too, like little crumbs in cake."
    )
    friend.memes["worry"] = 1
    hero.memes["worry"] = 1

    world.para()
    world.say(
        f"{hero.id} held up the card and spoke so kind, with steady, sunny cheer. "
        f"'No need to rush; let's check it out and make the meaning clear.'"
    )
    world.say(
        f"They looked again, then laughed a bit: the card had lost one piece. "
        f"So 'hola, amiga' needed fixing, to bring the joy and peace."
    )
    world.say(
        f"They used the spare sticker and the gear, and set the sign back straight. "
        f"The tiny twist became a grin, and then a lovely fate."
    )
    gear.worn_by = hero.id
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0

    world.say(
        f"At last they taped the final piece, and proudly held it high. "
        f"The card said 'hola, amiga' now, as clear as morning sky."
    )
    world.say(
        f"So the twist turned into friendship, warm as toast and bright as gold; "
        f"two pals made something special, and their happy hearts felt bold."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=card,
        gear=gear,
        activity=activity,
        setting=world.setting,
        twist="missing sticker",
        resolved=True,
    )
    return world


SETTINGS = {
    "library": Setting(place="the library corner", mood="quiet and cozy", supports={"card"}),
    "garden": Setting(place="the garden table", mood="sunny and easy", supports={"card"}),
    "classroom": Setting(place="the classroom desk", mood="bright and busy", supports={"card"}),
}

ACTIVITIES = {
    "card": Activity(
        id="card",
        verb="make a friendship card",
        gerund="making a friendship card",
        twist="a sticker slides away",
        rhyme_a="bright",
        rhyme_b="light",
        mess="glue",
        zone={"torso"},
        keyword="spanish",
    ),
}

PRIZES = {
    "card": Prize(
        label="card",
        phrase="a little friendship card with Spanish words",
        type="card",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="spare_sticker",
        label="a spare sticker",
        covers={"torso"},
        guards={"glue"},
        prep="use a spare sticker",
        tail="used the spare sticker and pressed the card just right",
    ),
]

NAMES = ["Mia", "Nora", "Luz", "Sofia", "Ana", "Ivy", "Lola", "June"]
TRAITS = ["kind", "cheery", "brave", "gentle", "lively"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    friend: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.supports:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: this little world only supports {activity.id} with {prize.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about friendship, Spanish words, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_supported(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != hero])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, friend=friend, trait=trait)


def prize_supported(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone and activity.mess in {"glue"}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about friendship and the Spanish word "hola".',
        f"Tell a gentle story where {f['hero'].id} and {f['friend'].id} make a card together and a tiny twist changes the mood.",
        f"Write a child-friendly rhyme about two friends fixing a mix-up on a Spanish friendship card.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    card = _safe_fact(world, f, "prize")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} making?",
            answer=f"They were making {card.phrase}, a little card with Spanish words for friendship.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer="A sticker slid away, so the card looked a little wrong at first.",
        ),
        QAItem(
            question=f"How did they fix the card?",
            answer=f"They used {gear.label} and pressed the card back into place so the words looked right again.",
        ),
        QAItem(
            question=f"How did the friends feel at the end?",
            answer=f"They felt happy and proud, and their friendship felt warm and strong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hola mean?",
            answer="Hola is a Spanish word that means hello.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and help each other feel safe and happy.",
        ),
        QAItem(
            question="Why do people use stickers on cards?",
            answer="People use stickers to decorate cards and make them look bright and cheerful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl"))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl"))
    act = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)
    gear = GEAR[0]

    hero.memes["trust"] = 1
    friend.memes["trust"] = 1
    hero.memes["love"] = 1
    friend.memes["love"] = 1

    tell(world, act, prize, hero, friend, gear)

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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(setting.supports):
            lines.append(asp.fact("supports", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
fixable(A,P) :- prize_at_risk(A,P), mess(A,M), guards(G,M), covers(G,R), worn_on(P,R), zone(A,R).
valid_story(Place,A,P) :- supports(Place,A), fixable(A,P).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [
            StoryParams(place=p, activity=a, prize=r, hero="Mia", friend="Luz", trait="kind")
            for p, a, r in valid_combos()
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
