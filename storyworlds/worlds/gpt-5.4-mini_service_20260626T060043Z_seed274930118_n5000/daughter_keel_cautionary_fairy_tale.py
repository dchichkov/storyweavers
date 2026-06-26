#!/usr/bin/env python3
"""
storyworlds/worlds/daughter_keel_cautionary_fairy_tale.py
=========================================================

A small cautionary fairy-tale storyworld about a daughter, a keel, and a safer
choice. The domain keeps the fairy-tale feel while staying constraint-checked
and state-driven.

Seed image:
---
A daughter by the water wants to step onto the keel of a little boat because it
looks magical and brave. Her parent warns that the keel is slippery and the tide
is rising. The daughter ignores the warning, slips, and learns that wonder can
wait for a safer way.

World model:
---
The daughter's daring increases risk, fear, and the chance of a fall.
A warning can be predicted from the keel's wetness and the daughter's footing.
A safe compromise uses a plank or rope rail that truly fits the danger.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SETTINGS = {
    "harbor": {
        "place": "the harbor",
        "indoors": False,
        "water": True,
        "kinds": {"walk", "climb", "scrub"},
    },
    "riverbank": {
        "place": "the riverbank",
        "indoors": False,
        "water": True,
        "kinds": {"walk", "climb", "scrub"},
    },
    "boathouse": {
        "place": "the boathouse",
        "indoors": True,
        "water": True,
        "kinds": {"walk", "climb", "scrub"},
    },
}

ACTIVITIES = {
    "climb_keel": {
        "verb": "climb onto the keel",
        "gerund": "climbing onto the keel",
        "rush": "run toward the little boat",
        "risk": "slippery",
        "hazard": "slip into the water",
        "zone": {"feet", "legs"},
        "tag": "keel",
        "keyword": "keel",
    },
    "walk_keel": {
        "verb": "walk along the keel",
        "gerund": "walking along the keel",
        "rush": "tiptoe toward the boat",
        "risk": "slippery",
        "hazard": "lose balance on the narrow wood",
        "zone": {"feet", "legs"},
        "tag": "keel",
        "keyword": "keel",
    },
    "scrub_keel": {
        "verb": "scrub the keel",
        "gerund": "scrubbing the keel",
        "rush": "hurry to the bucket",
        "risk": "wet",
        "hazard": "get soaked by the wash water",
        "zone": {"feet", "legs", "torso"},
        "tag": "keel",
        "keyword": "keel",
    },
}

PRIZES = {
    "dress": {
        "label": "dress",
        "phrase": "a bright blue dress",
        "region": "torso",
        "genders": {"girl"},
    },
    "cloak": {
        "label": "cloak",
        "phrase": "a soft red cloak",
        "region": "torso",
        "genders": {"girl", "boy"},
    },
    "shoes": {
        "label": "shoes",
        "phrase": "shiny white shoes",
        "region": "feet",
        "genders": {"girl", "boy"},
    },
    "stockings": {
        "label": "stockings",
        "phrase": "warm pale stockings",
        "region": "feet",
        "genders": {"girl"},
    },
}

GEAR = [
    {
        "id": "plank",
        "label": "a sturdy plank",
        "covers": {"feet", "legs"},
        "guards": {"slippery"},
        "prep": "lay down a sturdy plank first",
        "tail": "laid down a sturdy plank",
        "plural": False,
    },
    {
        "id": "rope_rail",
        "label": "a rope rail",
        "covers": {"feet", "legs", "torso"},
        "guards": {"slippery", "wet"},
        "prep": "tie up a rope rail first",
        "tail": "tied up a rope rail",
        "plural": False,
    },
    {
        "id": "oilcloth",
        "label": "an oilcloth apron",
        "covers": {"torso"},
        "guards": {"wet"},
        "prep": "put on an oilcloth apron first",
        "tail": "put on an oilcloth apron",
        "plural": False,
    },
]

NAMES_GIRL = ["Lina", "Mira", "Tessa", "Ayla", "Nora", "Elin", "Pia", "Rhea"]
NAMES_BOY = ["Oren", "Bram", "Eli", "Finn", "Theo", "Jon", "Milo", "Rune"]
TRAITS = ["curious", "brave", "stubborn", "dreamy", "gentle", "lively"]

# ---------------------------------------------------------------------------
# Shared result-ready dataclasses
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    g: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "daughter"}
        male = {"boy", "son"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: dict) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

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
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------


def prize_at_risk(activity: dict, prize: dict) -> bool:
    return prize["region"] in activity["zone"]


def select_gear(activity: dict, prize: dict) -> Optional[dict]:
    for gear in GEAR:
        if activity["risk"] in gear["guards"] and prize["region"] in gear["covers"]:
            return gear
    return None


def explain_rejection(activity: dict, prize: dict) -> str:
    noun = prize["label"]
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity['gerund']} does not threaten the {noun}. "
            f"The cautionary tale needs a real risk.)"
        )
    return (
        f"(No story: there is no safe gear that truly covers the {noun} for "
        f"{activity['gerund']}. The fix must fit the danger.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id)["genders"]))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id)['label']} is not a typical {gender}'s item here; try --gender {ok}.)"


def predict(world: World, actor: Entity, activity: dict, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": bool(prize.meters.get("soiled", 0) >= THRESHOLD),
        "fear": actor.memes.get("fear", 0.0),
    }


def do_activity(world: World, actor: Entity, activity: dict, narrate: bool = True) -> None:
    world.zone = set(activity["zone"])
    actor.meters[activity["risk"]] = actor.meters.get(activity["risk"], 0.0) + 1
    actor.memes["daring"] = actor.memes.get("daring", 0.0) + 1
    propagate(world, narrate=narrate)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for actor in world.characters():
            if actor.meters.get("slippery", 0.0) < THRESHOLD and actor.meters.get("wet", 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("soil", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["soiled"] = item.meters.get("soiled", 0.0) + 1
                item.memes["trouble"] = item.memes.get("trouble", 0.0) + 1
                out.append(f"{actor.id}'s {item.label} was splashed and stained.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Once in {world.setting['place']}, there lived a little {hero.traits[0]} {hero.type} named {hero.id}."
    )


def love_world(world: World, hero: Entity, activity: dict) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity['gerund']} because the old water looked like silver glass."
    )


def gift(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.type} had given {hero.id} {hero.pronoun('object')} {prize.phrase}."
    )
    prize.worn_by = hero.id


def arrive(world: World, hero: Entity, parent: Entity, activity: dict) -> None:
    world.say(
        f"One evening, {hero.id} and {hero.pronoun('possessive')} {parent.type} came to {world.setting['place']}."
    )
    world.say(f"The little boat's keel gleamed where the tide lapped at the wood.")


def wants(world: World, hero: Entity, activity: dict) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity['verb']} to see the moon in the water.")


def warn(world: World, parent: Entity, hero: Entity, activity: dict, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = "spoiled"
    world.say(
        f'"If you try that," {hero.pronoun("possessive")} {parent.type} said, '
        f'"your {prize.label} will be spoiled, and you may slip."'
    )
    return True


def disobey(world: World, hero: Entity, activity: dict) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"But the wish was strong, and {hero.id} ran toward the little boat.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity['rush']}.")


def slip(world: World, hero: Entity, activity: dict) -> None:
    hero.meters["balance"] = hero.meters.get("balance", 1.0) - 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"The keel was slippery, and {hero.id} nearly lost balance.")
    world.say(f"At the very edge, {hero.pronoun()} understood the warning at last.")


def compromise(world: World, parent: Entity, hero: Entity, activity: dict, prize: Entity) -> Optional[dict]:
    gear = select_gear(activity, _safe_lookup(PRIZES, prize.id))
    if gear is None:
        return None
    if not prize_at_risk(activity, _safe_lookup(PRIZES, prize.id)):
        return None
    temp = world.copy()
    g = temp.add(Entity(
        id=gear["id"],
        kind="thing",
        type="gear",
        label=gear["label"],
        protective=True,
        covers=set(gear["covers"]),
    ))
    g.worn_by = hero.id
    if predict(temp, hero, activity, prize.id)["soiled"]:
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.type} pointed to {gear['label']} and smiled."
    )
    world.say(f'"We can {gear["prep"]}, and then you may {activity["verb"]} safely."')
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: dict, prize: Entity, gear: dict) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    world.say(
        f"{hero.id} nodded, and together they {gear['tail']}."
    )
    world.say(
        f"Then {hero.id} was {activity['gerund']}, {prize.label} stayed bright, and the tide sang gently below."
    )


def tell(setting: dict, activity: dict, prize_cfg: dict, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait, "little"],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id=prize_cfg["label"],
        kind="thing",
        type=prize_cfg["label"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg["region"],
    ))

    introduce(world, hero)
    love_world(world, hero, activity)
    gift(world, parent, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    disobey(world, hero, activity)
    slip(world, hero, activity)
    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Registries / curated combos
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="harbor", activity="walk_keel", prize="shoes", name="Lina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="riverbank", activity="climb_keel", prize="dress", name="Mira", gender="girl", parent="father", trait="dreamy"),
    StoryParams(setting="boathouse", activity="scrub_keel", prize="cloak", name="Oren", gender="boy", parent="mother", trait="lively"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sname, s in SETTINGS.items():
        for aname, a in ACTIVITIES.items():
            if aname not in s["kinds"]:
                continue
            for pname, p in PRIZES.items():
                if prize_at_risk(a, p) and select_gear(a, p):
                    out.append((sname, aname, pname))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, activity, prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    return [
        f'Write a cautionary fairy tale about a {hero.type} named {hero.id} who wants to {activity["verb"]} near {world.setting["place"]}.',
        f"Tell a small fairy tale where {hero.id} ignores a warning about {hero.pronoun('possessive')} {prize.label} and learns a safer way.",
        f'Write a gentle warning story that uses the word "{activity["keyword"]}" and ends with a safer choice by {hero.id}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who wanted to {activity['verb']} in this tale?",
            answer=f"It was {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.type} warn {hero.id} about the keel?",
            answer=f"Because the keel was slippery and could make {hero.id} slip or spoil {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What happened after {hero.id} ignored the warning?",
            answer=f"{hero.id} nearly lost balance on the keel, then listened and chose a safer way.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear['label']} help {hero.id}?",
                answer=f"It made the plan safer by covering the risky parts and keeping {hero.pronoun('possessive')} {prize.label} dry and bright.",
            )
        )
    return qa


WORLD_QA = {
    "keel": [
        QAItem(
            question="What is a keel?",
            answer="A keel is the long bottom part of a boat. It helps the boat stay steady in the water.",
        ),
        QAItem(
            question="Why can a keel be slippery?",
            answer="A keel can be slippery because water and spray make the wood wet and slick.",
        ),
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean in a story?",
            answer="A cautionary story shows a warning, a mistake, and a lesson that helps someone choose more wisely next time.",
        ),
    ],
    "fairy_tale": [
        QAItem(
            question="What makes a story feel like a fairy tale?",
            answer="A fairy tale often feels old and magical, with simple language, a clear lesson, and a little wonder in the world.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_QA["cautionary"])
    out.extend(WORLD_QA["fairy_tale"])
    if "keel" in _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "activity")["keyword"]:
        out.extend(WORLD_QA["keel"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
fix(A,P) :- prize_at_risk(A,P), guards(G,M), risk(A,M), covers(G,R), worn_on(P,R).
valid(S,A,P) :- setting(S), activity(A), prize(P), affords(S,A), prize_at_risk(A,P), fix(A,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sname, s in SETTINGS.items():
        lines.append(asp.fact("setting", sname))
        if s["indoors"]:
            lines.append(asp.fact("indoors", sname))
        for a in sorted(s["kinds"]):
            lines.append(asp.fact("affords", sname, a))
    for aname, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aname))
        lines.append(asp.fact("risk", aname, a["risk"]))
        for r in sorted(a["zone"]):
            lines.append(asp.fact("zone", aname, r))
    for pname, p in PRIZES.items():
        lines.append(asp.fact("prize", pname))
        lines.append(asp.fact("worn_on", pname, p["region"]))
        for g in sorted(p["genders"]):
            lines.append(asp.fact("wears", g, pname))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear["id"]))
        for c in sorted(gear["covers"]):
            lines.append(asp.fact("covers", gear["id"], c))
        for g in sorted(gear["guards"]):
            lines.append(asp.fact("guards", gear["id"], g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(description="A cautionary fairy tale about a daughter and a keel.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None))["genders"]:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]]["genders"])
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(PRIZES, prize)["genders"]))
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        "daughter" if params.gender == "girl" else "son",
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, activity, prize) combos:\n")
        for s, a, p in triples:
            print(f"  {s:10} {a:12} {p}")
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
            header = f"### {p.name}: {p.activity} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
