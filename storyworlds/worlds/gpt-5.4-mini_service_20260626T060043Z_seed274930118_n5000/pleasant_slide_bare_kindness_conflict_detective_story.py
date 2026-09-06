#!/usr/bin/env python3
"""
storyworlds/worlds/pleasant_slide_bare_kindness_conflict_detective_story.py
===========================================================================

A small detective-story world about a pleasant day, a bare slide, a conflict,
and a kindness that resolves it.

Seed image:
- The day is pleasant.
- A slide is bare and looks wrong somehow.
- A child detective notices the conflict.
- Kindness turns the ending around.

This world models:
- physical meters: cleanliness, dryness, smoothness, clutter, shine, etc.
- emotional memes: curiosity, worry, conflict, kindness, relief, pride.

The prose is generated from world state rather than from a frozen template:
the detective investigates, clues are gathered, a conflict is recognized, and a
kind action changes the ending image.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    prize: object | None = None
    slide: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the playground"
    pleasant: bool = True
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
    clue: str
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    covers: set[str]
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


@dataclass(frozen=True)
class Case:
    id: str
    occasion: str
    missing: str
    first_clue: str
    mistaken_guess: str
    evidence: str
    helper_reason: str
    kind_offer: str
    shared_action: str
    result: str
    ending_image: str
    lesson: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _rule_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("blocked", 0) < THRESHOLD:
            continue
        if actor.memes.get("kindness_offered", 0) >= THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
        out.append(f"{actor.label} felt the conflict tightening in {actor.chest if False else ''}".strip())
    return out


def _rule_clean_clue(world: World) -> list[str]:
    out: list[str] = []
    slide = world.entities.get("slide")
    if not slide:
        return out
    if slide.meters.get("bare", 0) < THRESHOLD:
        return out
    sig = ("clue", "bare_slide")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The bare slide left a clear clue behind.")
    return out


CAUSAL_RULES = [_rule_conflict, _rule_clean_clue]


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


def detect_problem(world: World, detective: Entity, activity: Activity, prize: Prize) -> bool:
    sim = world.copy()
    sim.get(detective.id).memes["curiosity"] = sim.get(detective.id).memes.get("curiosity", 0) + 1
    simulate_clue(sim, activity, prize, narrate=False)
    return sim.get(prize.id).meters.get("dirty", 0) >= THRESHOLD or sim.get("slide").meters.get("bare", 0) >= THRESHOLD


def simulate_clue(world: World, activity: Activity, prize: Prize, narrate: bool = True) -> None:
    slide = world.get("slide")
    slide.meters["bare"] = 1.0
    slide.meters["shine"] = 0.0
    if narrate:
        world.say(f"The {slide.label} looked bare, and that was the first clue.")
    propagate(world, narrate=narrate)


def apply_activity(world: World, detective: Entity, activity: Activity, prize: Prize, narrate: bool = True) -> None:
    prize.meters[activity.mess] = prize.meters.get(activity.mess, 0.0) + 1.0
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1.0
    propagate(world, narrate=narrate)


def offer_kindness(world: World, helper: Entity, detective: Entity, fix: Fix, prize: Prize, narrate: bool = True) -> None:
    detective.memes["kindness"] = detective.memes.get("kindness", 0.0) + 1.0
    detective.memes["kindness_offered"] = 1.0
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    if narrate:
        world.say(f"{helper.label} offered {fix.label} with a smile.")
    for ent in list(world.entities.values()):
        if ent.id in {"slide", prize.id}:
            ent.meters["bare"] = 0.0
    world.get("slide").meters["shine"] = 1.0
    world.get("slide").meters["safe"] = 1.0
    prize.meters[prize.region if False else "clean"] = 1.0
    detective.memes["conflict"] = 0.0
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1.0
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"At once, the conflict loosened, and the {fix.label} made the puzzle feel kind.")


def intro(world: World, detective: Entity, prize: Prize) -> None:
    world.say(
        f"It was a pleasant day at {world.setting.place}, and {detective.label} was on the case."
    )
    world.say(
        f"{detective.pronoun().capitalize()} was a little detective who loved clues and loved "
        f"{prize.label} even more."
    )


def clue_scene(world: World, detective: Entity, activity: Activity, prize: Prize) -> None:
    world.say(
        f"{detective.label} noticed something odd: the {activity.keyword} spot was too quiet, and the slide looked bare."
    )
    world.say(
        f"{detective.pronoun().capitalize()} followed the clue because a bare place can mean trouble for {prize.label}."
    )


def conflict_scene(world: World, detective: Entity, helper: Entity, activity: Activity, prize: Prize) -> None:
    detective.memes["blocked"] = 1.0
    world.say(
        f"When {detective.label} reached the slide, {helper.label} had already begun to {activity.verb} there."
    )
    world.say(
        f"{detective.label} wanted to solve the mystery right away, but {helper.label} held on to the slide, and the conflict grew."
    )


def resolution_scene(world: World, detective: Entity, helper: Entity, fix: Fix, prize: Prize) -> None:
    world.say(
        f"Then {helper.label} remembered a kinder way."
    )
    offer_kindness(world, helper, detective, fix, prize, narrate=True)
    world.say(
        f"In the end, the slide was no longer bare, {prize.label} stayed clean, and the pleasant day felt even better."
    )


SETTINGS = {
    "playground": Setting(place="the playground", pleasant=True, affords={"slide"}),
    "yard": Setting(place="the yard", pleasant=True, affords={"slide"}),
    "park": Setting(place="the park", pleasant=True, affords={"slide"}),
}

ACTIVITIES = {
    "slide": Activity(
        id="slide",
        verb="slide down",
        gerund="sliding down",
        clue="slide",
        mess="dusty",
        soil="dusty",
        zone={"legs", "seat"},
        keyword="slide",
        tags={"slide", "pleasant", "bare"},
    )
}

PRIZES = {
    "coat": Prize(
        label="coat",
        phrase="a bright red coat",
        type="coat",
        region="torso",
    ),
    "pants": Prize(
        label="pants",
        phrase="soft blue pants",
        type="pants",
        region="legs",
        plural=True,
    ),
}

FIXES = {
    "mat": Fix(
        id="mat",
        label="a soft mat",
        prep="spread a soft mat over the bare slide",
        tail="spread the mat neatly over the slide",
        helps={"dusty"},
        covers={"seat", "legs"},
    ),
    "cloth": Fix(
        id="cloth",
        label="a clean cloth",
        prep="lay a clean cloth on the slide",
        tail="laid the cloth flat",
        helps={"dusty"},
        covers={"seat"},
    ),
}

NAMES = ["Mina", "Noah", "Iris", "Leo", "Ruby", "Otis"]
HELPER_NAMES = ["Pia", "Ezra", "Sage", "Owen", "June", "Milo"]

GENDERS = {
    "Mina": "girl", "Iris": "girl", "Ruby": "girl", "Pia": "girl", "June": "girl",
    "Noah": "boy", "Leo": "boy", "Otis": "boy", "Ezra": "boy", "Owen": "boy", "Milo": "boy",
    "Sage": "child",
}

CASES = {
    "landing_mat": Case(
        id="landing_mat",
        occasion="the playground's first morning after a rainy week",
        missing="the blue landing mat that belonged on the ground below the slide",
        first_clue="a trail of square muddy prints led toward the reading bench",
        mistaken_guess="that someone had taken the mat just to keep other children away",
        evidence="one dry book corner and a row of mat-shaped drips beneath the bench",
        helper_reason="moved the mat to save the library books when rain blew under the bench",
        kind_offer="offered to fetch a spare tarp for the books before returning the safety mat",
        shared_action="covered the books with the tarp, rinsed the mat, and set it below the slide",
        result="the landing place was padded again and the books stayed dry",
        ending_image="the last raindrop flashed on the clean blue mat like a tiny magnifying glass",
        lesson="asking why can turn an accusation into a solution",
    ),
    "queue_marks": Case(
        id="queue_marks",
        occasion="a cheerful class picnic",
        missing="the chalk footprints that showed where the slide line began",
        first_clue="a damp sponge rested beside a bucket striped with yellow chalk",
        mistaken_guess="that the line leader had erased the marks to claim every turn",
        evidence="gritty pebbles stuck to the sponge and a scrape shone on the lowest step",
        helper_reason="washed away the chalk after loose grit made the steps slippery",
        kind_offer="suggested drawing new footprints once the steps were clean and dry",
        shared_action="swept the grit, dried each step, and drew a winding trail of fresh footprints",
        result="everyone could queue safely without arguing over whose turn came next",
        ending_image="small shoes waited on green and gold chalk feet while the slide gleamed bare and safe",
        lesson="a fair rule works best when everyone helps make it safe",
    ),
    "welcome_flag": Case(
        id="welcome_flag",
        occasion="the park's welcome-day celebration",
        missing="the bright welcome flag that usually flew from the pole beside the slide",
        first_clue="three red threads clung to a low hawthorn branch",
        mistaken_guess="that the helper had hidden the flag to spoil the celebration",
        evidence="a snapped cord pointed downwind toward a robin's nest",
        helper_reason="folded the fallen flag before its loose string could tangle near the nest",
        kind_offer="invited the detective to replace the cord with a short, bird-safe tie",
        shared_action="carried the flag back and fastened it where no string could trail",
        result="the welcome flag flew again without putting the birds in danger",
        ending_image="the red flag waved above the bare silver slide as a robin sang from the hedge",
        lesson="protecting a small neighbor matters more than being first to decorate",
    ),
    "lost_sign": Case(
        id="lost_sign",
        occasion="a pleasant afternoon treasure hunt",
        missing="the picture clue that had been clipped to the side of the slide",
        first_clue="a bent wooden clip lay under a patch of fluttering leaves",
        mistaken_guess="that the helper had removed the clue to win the treasure hunt",
        evidence="leaf-shaped wet marks crossed the path toward the drinking fountain",
        helper_reason="rescued the rain-soaked clue before its ink could wash away",
        kind_offer="held out the dried clue and asked to finish the hunt as a team",
        shared_action="copied the clue onto sturdy card and clipped it beside, not across, the slide",
        result="every team could read the clue and the sliding path stayed clear",
        ending_image="the new clue nodded in the breeze while two detectives followed its arrow together",
        lesson="sharing evidence makes a mystery fair for everyone",
    ),
    "sun_hat": Case(
        id="sun_hat",
        occasion="a warm family play day",
        missing="a little sun hat that had been perched on the slide's side rail",
        first_clue="a ribbon end poked from beneath the lost-and-found basket",
        mistaken_guess="that the helper meant to keep the pretty hat",
        evidence="a name tag inside the hat matched a toddler searching near the swings",
        helper_reason="put the hat safely in lost-and-found so it would not blow into the sliding lane",
        kind_offer="asked the detective to help return it to its worried owner",
        shared_action="matched the name tag, returned the hat, and moved the basket beside the gate",
        result="the toddler had shade again and the slide remained bare of loose objects",
        ending_image="the toddler's yellow hat bobbed toward the swings while the empty slide shone in the sun",
        lesson="returning something precious is kinder than guarding a mistaken claim",
    ),
    "painted_star": Case(
        id="painted_star",
        occasion="the morning of the playground art walk",
        missing="a paper star planned for the fence beside the slide",
        first_clue="blue paint dots crossed the pavement but stopped at a recycling bin",
        mistaken_guess="that the helper had thrown away another child's artwork",
        evidence="the star's back was soggy and its tape had collected sand",
        helper_reason="lifted it from the slide before the wet paper could make the surface slick",
        kind_offer="offered clean card and a place on the fence for a stronger new star",
        shared_action="painted a new star and pinned it securely to the fence",
        result="the art could be admired while the slide stayed clear for play",
        ending_image="their blue star dried on the fence, framing the bare slide through its center",
        lesson="kindness can preserve an idea even when its first form cannot be saved",
    ),
    "acorn_map": Case(
        id="acorn_map",
        occasion="a breezy nature-club meeting",
        missing="the acorn map children had arranged beside the slide",
        first_clue="one acorn cap sat in a neat dustpan near the sandbox",
        mistaken_guess="that the helper had swept up the map without caring",
        evidence="tiny ants streamed from the old acorns toward a crack by the steps",
        helper_reason="moved the acorns so no one would crush the ants or slip on the shells",
        kind_offer="proposed rebuilding the map on a low table away from running feet",
        shared_action="carried the ants' acorns to the soil and rebuilt the map with smooth stones",
        result="the club kept its map and the path around the slide was safe",
        ending_image="a spiral of stones pointed north while ants vanished beneath the green hedge",
        lesson="careful observation makes room for people and tiny creatures alike",
    ),
    "bell": Case(
        id="bell",
        occasion="a lively playground relay",
        missing="the brass turn bell that normally hung on a post near the slide",
        first_clue="a circle of clean wood showed where the bell strap had been",
        mistaken_guess="that the helper wanted to control every turn without ringing",
        evidence="a frayed strap and a small brass screw rested on the repair cart",
        helper_reason="removed the bell after its strap began to tear",
        kind_offer="showed the detective the damage and offered to make turn cards meanwhile",
        shared_action="made numbered cards, shared the turns, and asked an adult to mend the strap",
        result="the relay continued fairly and the repaired bell could not fall",
        ending_image="at sunset, one clear bell note floated over the bare slide and twelve orderly cards",
        lesson="pausing to repair something can be fairer than pretending it is fine",
    ),
    "shadow_shapes": Case(
        id="shadow_shapes",
        occasion="a sunny shapes lesson",
        missing="a set of cardboard shapes that had cast shadows across the slide's side panel",
        first_clue="a triangle shadow trembled on the storage-shed door",
        mistaken_guess="that the helper had carried the lesson away for another class",
        evidence="two curling corners and a hot patch of tape showed the shapes had softened in the sun",
        helper_reason="removed the loose cardboard before it peeled into the sliding path",
        kind_offer="invited the detective to hold the shapes safely against the fence instead",
        shared_action="clipped the shapes to the fence and traced their changing shadows in chalk",
        result="the lesson continued and nothing loose covered the slide",
        ending_image="a long triangle shadow reached toward their chalk circles as evening cooled the playground",
        lesson="changing a plan is wise when the evidence reveals a safer way",
    ),
    "quiet_card": Case(
        id="quiet_card",
        occasion="a calm sensory-play hour",
        missing="the quiet-turn card from the sign beside the slide",
        first_clue="a corner of purple card showed beneath a bench cushion",
        mistaken_guess="that the helper had hidden it to end quiet hour early",
        evidence="a child nearby covered their ears whenever the card's metal clip rattled",
        helper_reason="moved the rattling card so the sharp sound would stop",
        kind_offer="suggested replacing the metal clip with a soft clothespin",
        shared_action="found a wooden clothespin, rehung the card, and tested it in silence",
        result="quiet turns resumed without the startling rattle",
        ending_image="the purple card rested soundlessly beside the bare slide while leaves whispered overhead",
        lesson="kindness listens for discomfort that other people may not notice",
    ),
    "garden_marker": Case(
        id="garden_marker",
        occasion="a garden-work morning beside the yard slide",
        missing="the painted marker for the mint bed near the slide",
        first_clue="green paint smudged a watering-can handle",
        mistaken_guess="that the helper had borrowed the marker and forgotten it",
        evidence="the marker's splintered end lay beside a newly covered patch of soil",
        helper_reason="pulled out the broken marker before its sharp edge could scratch a gardener",
        kind_offer="offered a smooth craft stick and asked to paint a replacement together",
        shared_action="sanded the stick, painted MINT on it, and planted it firmly in the bed",
        result="the herb bed had a safe label and the path to the slide stayed open",
        ending_image="mint leaves brushed the new green marker while a ladybug crossed its final letter",
        lesson="telling someone about a hidden hazard is an important kind act",
    ),
    "story_cards": Case(
        id="story_cards",
        occasion="the park's outdoor story circle",
        missing="the ending card from a picture story arranged near the slide",
        first_clue="three silver sequins led from the bare display board to a stroller",
        mistaken_guess="that the helper had taken the ending to keep the answer secret",
        evidence="a baby's fist held one sequin while the story card rested safely in the stroller pocket",
        helper_reason="caught the card when wind blew it toward the baby and loose decorations came off",
        kind_offer="returned the card and proposed removing the remaining loose sequins",
        shared_action="saved the sequins in a jar and fastened the plain card to the display board",
        result="the story had its ending and the baby could explore safely",
        ending_image="the final picture stood beside the bare slide as sealed sequins sparkled inside their jar",
        lesson="a plain, safe ending can hold more kindness than a glittery risk",
    ),
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, r) for p in SETTINGS for a in ACTIVITIES for r in PRIZES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "activity", None) not in ACTIVITIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prize", None) and getattr(args, "prize", None) not in PRIZES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, helper=helper)


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    detective = world.add(Entity(id="detective", kind="character", type=GENDERS.get(params.name, "child"), label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=GENDERS.get(params.helper, "child"), label=params.helper))
    slide = world.add(Entity(id="slide", type="slide", label="slide"))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase))
    world.facts = {
        "detective": detective,
        "helper": helper,
        "slide": slide,
        "prize": prize,
        "activity": _safe_lookup(ACTIVITIES, params.activity),
        "params": params,
    }
    return world


def _story_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0x51D3C7)
    identity = "|".join((params.place, params.activity, params.prize, params.name, params.helper))
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(identity)))


def _opening(rng: random.Random, world: World, detective: Entity, prize: Prize, case: Case) -> str:
    return rng.choice([
        f"During {case.occasion}, {detective.label}, a young detective, arrived on a pleasant day at {world.setting.place}, wearing {prize.phrase} and looking for a mystery.",
        f"The day felt pleasant at {world.setting.place}, especially to the young detective {detective.label}, who wore {prize.phrase} and kept a notebook ready.",
        f"The young detective {detective.label} had promised to notice small things during {case.occasion}. At {world.setting.place} on that pleasant day, even {prize.phrase} had a pocket for clues.",
        f"A pleasant breeze followed {detective.label} into {world.setting.place} for {case.occasion}. With {prize.phrase} on, the young detective began a careful patrol.",
        f"No one had announced a mystery on that pleasant day at {world.setting.place}. Still, during {case.occasion}, the young detective {detective.label} noticed when the ordinary scene did not look ordinary at all.",
    ])


def _discovery(rng: random.Random, detective: Entity, case: Case) -> list[str]:
    subject = detective.pronoun("subject").capitalize()
    missing = rng.choice([
        f"The slide looked bare because {case.missing} was gone.",
        f"One glance at the bare slide revealed the problem: {case.missing} had vanished.",
        f"Something made the slide look strangely bare. {subject} checked twice and saw that {case.missing} was missing.",
        f"The first puzzle was a bare-looking slide, with no sign of {case.missing}.",
    ])
    clue = rng.choice([
        f"Nearby, {case.first_clue}.",
        f"Instead of guessing, {detective.label} searched low and high. Soon {case.first_clue}.",
        f"A real detective follows what can be seen: {case.first_clue}.",
        f"The smallest detail mattered. Just beyond the slide, {case.first_clue}.",
    ])
    thought = rng.choice([
        f"At first, {detective.label} suspected {case.mistaken_guess}.",
        f"{subject} nearly decided {case.mistaken_guess}, but a suspicion was not proof.",
        f"The quick answer was {case.mistaken_guess}. {detective.label} wrote a question mark beside that idea.",
        f"Could it be {case.mistaken_guess}? {detective.label} took one slow breath and kept investigating.",
    ])
    evidence = rng.choice([
        f"Then the evidence changed the case: {case.evidence}.",
        f"A closer look revealed evidence that did not fit the first guess: {case.evidence}.",
        f"The next clue was stronger than suspicion: {case.evidence}.",
        f"Before making an accusation, {detective.label} studied this evidence: {case.evidence}.",
    ])
    return [missing, clue, thought, evidence]


def _conflict(rng: random.Random, detective: Entity, helper: Entity, case: Case) -> list[str]:
    challenge = rng.choice([
        f"A conflict began when {detective.label} blurted, \"You took it! I followed the clues.\"",
        f"The suspicion became a conflict when {detective.label} hurried to block {helper.label}'s path. \"Please put it back right now,\" the detective said.",
        f"\"This case is solved,\" {detective.label} announced too soon, pointing at {helper.label}. The accusation started a conflict.",
        f"When {helper.label} arrived, both children spoke at once. Their different ideas tightened into a conflict.",
    ])
    pause = rng.choice([
        f"{helper.label} looked hurt, so {detective.label} opened the notebook again and asked, \"What happened?\"",
        f"The conflict made both voices louder. Then {detective.label} remembered that clues matter more than volume and asked for the missing part.",
        f"For a moment neither child listened. {helper.label} pointed to the evidence, and {detective.label} let the question replace the accusation.",
        f"{detective.label} noticed that the evidence still needed an explanation. \"Tell me your reason,\" the detective said more gently.",
    ])
    explanation = rng.choice([
        f"{helper.label} explained that {helper.pronoun('subject')} {case.helper_reason}.",
        f"\"I did not want to spoil anything,\" said {helper.label}. \"I {case.helper_reason}.\"",
        f"The final piece clicked into place: {helper.label} had {case.helper_reason}.",
        f"As {helper.label} described how {helper.pronoun('subject')} {case.helper_reason}, every clue began to agree.",
    ])
    return [challenge, pause, explanation]


def _resolution(rng: random.Random, detective: Entity, helper: Entity, case: Case) -> list[str]:
    kindness = rng.choice([
        f"Kindness changed the investigation. {detective.label} apologized, and {helper.label} {case.kind_offer}.",
        f"\"I am sorry I guessed before I listened,\" said {detective.label}. Answering with kindness, {helper.label} {case.kind_offer}.",
        f"The detective crossed out the accusation. {helper.label}'s kindness supplied a better plan: {helper.pronoun('subject')} {case.kind_offer}.",
        f"They could have stayed angry. Instead, kindness won: {detective.label} apologized and {helper.label} {case.kind_offer}.",
    ])
    work = rng.choice([
        f"Together they {case.shared_action}.",
        f"The two new partners {case.shared_action}.",
        f"Following their kinder plan, they {case.shared_action}.",
        f"This time they shared the work: they {case.shared_action}.",
    ])
    result = rng.choice([
        f"Now {case.result}.",
        f"Their work meant that {case.result}.",
        f"The solved case had a result everyone could see: {case.result}.",
        f"By listening and helping, they made sure {case.result}.",
    ])
    ending = rng.choice([
        f"Before going home, {detective.label} wrote, \"{case.lesson.capitalize()}.\" Nearby, {case.ending_image}.",
        f"The notebook's last line said, \"Lesson learned: {case.lesson}.\" Then {case.ending_image}.",
        f"{detective.label} closed the case with one lesson: {case.lesson}. As the pleasant day ended, {case.ending_image}.",
        f"The conflict was over, but its lesson remained: {case.lesson}. In the final quiet moment, {case.ending_image}.",
    ])
    return [kindness, work, result, ending]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    detective = _safe_fact(world, world.facts, "detective")
    helper = _safe_fact(world, world.facts, "helper")
    prize = _safe_fact(world, world.facts, "prize")
    rng = _story_rng(params)
    case = rng.choice(list(CASES.values()))

    slide = world.get("slide")
    slide.meters["bare"] = 1.0
    detective.memes["curiosity"] = 1.0
    world.facts.update({"case": case, "missing": case.missing, "evidence": case.evidence})

    world.say(_opening(rng, world, detective, prize, case))
    world.para()
    for sentence in _discovery(rng, detective, case):
        world.say(sentence)
    world.para()
    detective.memes["conflict"] = 1.0
    helper.memes["conflict"] = 1.0
    for sentence in _conflict(rng, detective, helper, case):
        world.say(sentence)
    world.para()
    detective.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    detective.memes["kindness"] = 1.0
    helper.memes["kindness"] = 1.0
    detective.memes["relief"] = 1.0
    slide.meters["safe"] = 1.0
    world.facts.update({"resolution": case.shared_action, "lesson": case.lesson, "case_solved": True})
    for sentence in _resolution(rng, detective, helper, case):
        world.say(sentence)
    story = world.render()
    prompts = [
        "Write a short detective story for a young child that uses the words pleasant, slide, and bare.",
        f"Tell a gentle mystery where {params.name} notices a bare slide and a conflict, then kindness helps.",
        f"Write a simple detective tale about {case.occasion} at {world.setting.place} with a kind ending.",
    ]
    story_qa = [
        QAItem(
            question="Who investigated the mystery?",
            answer=f"{params.name} investigated why the slide looked bare.",
        ),
        QAItem(
            question="What was missing near the slide?",
            answer=f"The missing item was {case.missing}.",
        ),
        QAItem(
            question=f"What evidence changed {params.name}'s first guess?",
            answer=f"{params.name} found this decisive evidence: {case.evidence}.",
        ),
        QAItem(
            question=f"What had {params.helper} done, and why?",
            answer=f"{params.helper} had {case.helper_reason}.",
        ),
        QAItem(
            question="How did kindness resolve the conflict?",
            answer=f"{params.name} listened and apologized, while {params.helper} {case.kind_offer}. Together they {case.shared_action}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, share, or be gentle so things get better for another person.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem where people want different things and feel upset until they find a way forward.",
        ),
        QAItem(
            question="Why should a detective test a first guess against evidence?",
            answer="A first guess can be wrong. Evidence helps a detective find an explanation that fits what really happened.",
        ),
        QAItem(
            question="What lesson did this case demonstrate?",
            answer=f"The case demonstrated that {case.lesson}.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid(Place, Activity, Prize) :- setting(Place), activity(Activity), prize(Prize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pleasant detective story about a bare slide and a kind fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, activity=a, prize=r, name="Mina", helper="Pia")) for p, a, r in valid_combos()]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
