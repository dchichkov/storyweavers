#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scooter_german_stop_sound_effects_conflict_cautionary.py
=================================================================================================

A small fable-style story world about a child, a scooter, a cautionary choice,
and the sounds that mark the turn. The domain is intentionally narrow: a rider
wants to scoot too fast, a careful caretaker warns them, the child nearly
ignores the warning, and the story resolves with a safer stop.

Seed tale inspiration:
---
A little child loved a scooter and loved the fast sound it made on the path.
One day the child raced toward a corner where a sign and a German-speaking
neighbor both said "Stop!" The child wanted to keep going, but the wheel slid
and the ride turned risky. A wiser companion showed how to slow down, brake,
and listen. The child learned that speed can feel fun, but caution keeps trips
kind and safe.

World model:
---
- The rider has physical state measured in meters and emotional state measured
  in memes.
- The scooter can be fast, wobbly, or safely stopped.
- Sound effects are part of the narration and world state: "vrrm", "skrrt",
  and "stop" matter because they cue the change in motion.
- Conflict arises when the rider ignores a caution.
- The ending proves the lesson by changing motion, sound, and emotion.

Style:
---
Fable-like, short, concrete, and child-facing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

SCENE_METER = 1.0
SPEED_LIMIT = 2.0
WOBBLE_LIMIT = 1.0



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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    ridden_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    traits: list[str] = field(default_factory=list)

    caregiver: object | None = None
    child: object | None = None
    scooter: object | None = None
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
class Setting:
    place: str = "the lane"
    afford_stop: bool = True
    afford_roll: bool = True
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
class Scooter:
    id: str
    label: str
    phrase: str
    color: str
    sound_on_start: str = "vrrm"
    sound_on_brake: str = "skrrt"
    sound_on_stop: str = "stop"
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
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    caregiver: str
    trait: str
    scooter: str
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
        c = World(copy.deepcopy(self.setting))
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_speed(world: World) -> list[str]:
    out: list[str] = []
    rider = next((e for e in world.characters() if e.ridden_by), None)
    scooter = next((e for e in world.entities.values() if e.type == "scooter"), None)
    if not rider or not scooter:
        return out
    if rider.meters["push"] < SCENE_METER:
        return out
    sig = ("speed", rider.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.meters["speed"] += 1
    scooter.meters["speed"] += 1
    rider.memes["excitement"] += 1
    out.append(f"{scooter.label} went {scooter.sound_on_start} as {rider.id} pushed faster.")
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    rider = next((e for e in world.characters() if e.ridden_by), None)
    scooter = next((e for e in world.entities.values() if e.type == "scooter"), None)
    if not rider or not scooter:
        return out
    if rider.meters["speed"] < SPEED_LIMIT:
        return out
    sig = ("wobble", rider.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.meters["wobble"] += 1
    scooter.meters["wobble"] += 1
    rider.memes["risk"] += 1
    out.append("The wheels made a shaky skrrt on the path.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    rider = next((e for e in world.characters() if e.ridden_by), None)
    if not rider:
        return out
    if rider.memes["warned"] < SCENE_METER or rider.memes["stubborn"] < SCENE_METER:
        return out
    sig = ("conflict", rider.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.memes["conflict"] += 1
    out.append("__conflict__")
    return out


def _r_stop(world: World) -> list[str]:
    out: list[str] = []
    rider = next((e for e in world.characters() if e.ridden_by), None)
    scooter = next((e for e in world.entities.values() if e.type == "scooter"), None)
    if not rider or not scooter:
        return out
    if rider.memes["caution"] < SCENE_METER:
        return out
    sig = ("stop", rider.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.meters["speed"] = 0
    scooter.meters["speed"] = 0
    rider.meters["wobble"] = 0
    scooter.meters["wobble"] = 0
    rider.memes["conflict"] = 0
    rider.memes["calm"] += 1
    out.append(f"At last the scooter said {scooter.sound_on_stop}, and everything grew still.")
    return out


CAUSAL_RULES = [
    _r_speed,
    _r_wobble,
    _r_conflict,
    _r_stop,
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
                for s in sents:
                    if s != "__conflict__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, child: Entity) -> dict:
    sim = world.copy()
    sim.get(child.id).meters["push"] += 1
    propagate(sim, narrate=False)
    rider = sim.get(child.id)
    return {
        "wobble": rider.meters["wobble"] >= WOBBLE_LIMIT,
        "conflict": rider.memes["conflict"] >= SCENE_METER,
    }


def make_story(world: World, child: Entity, caregiver: Entity, scooter: Entity) -> None:
    world.say(
        f"Once there was a little {child.pronoun('subject').capitalize() if False else child.type} named {child.id} "
        f"who loved {scooter.label} more than any toy."
    )
    world.say(
        f"{child.id} liked the bright {scooter.color} scooter because every ride began with a happy {scooter.sound_on_start}."
    )
    world.say(
        f"{caregiver.pronoun('subject').capitalize()} often watched the lane and taught {child.id} to listen before rushing."
    )

    world.para()
    world.say(
        f"One day {child.id} rolled toward the corner of {world.setting.place}."
    )
    world.say(
        f"Just ahead, a sign with the word stop stood near a neighbor who spoke German and called out, \"Stopp!\""
    )
    world.say(
        f"{child.id} wanted one more fast turn, and the little scooter buzzed louder with each push."
    )
    child.meters["push"] += 1
    child.memes["stubborn"] += 1
    child.memes["warned"] += 1
    child.memes["caution"] += 1
    prediction = predict_risk(world, child)
    world.facts["prediction"] = prediction
    world.say(
        f"{caregiver.id} said, \"Stop now, little one. Fast wheels can slip when the path bends.\""
    )
    if prediction["wobble"]:
        world.say(
            f"The warning was wise, because the scooter was already starting to wobble."
        )
    world.say(
        f"{child.id} heard the caution but leaned forward anyway."
    )
    propagate(world, narrate=True)

    world.para()
    if child.memes["conflict"] >= SCENE_METER:
        world.say(
            f"{child.id} frowned at the sudden silence, but then {caregiver.id} showed how to press the brake and plant both feet."
        )
        child.memes["caution"] += 1
        propagate(world, narrate=True)
        world.say(
            f"{child.id} nodded and said, \"I will stop when I am told.\""
        )
        world.say(
            f"After that, the scooter rested quietly, and the lane stayed safe for the next rider."
        )
    else:
        world.say(
            f"{child.id} slowed before the bend and learned that a safe stop can be its own kind of victory."
        )
        child.memes["caution"] += 1
        propagate(world, narrate=True)
        world.say(
            f"The scooter ended still and tidy beside the curb."
        )

    world.facts.update(child=child, caregiver=caregiver, scooter=scooter)


SETTINGS = {
    "lane": Setting(place="the lane"),
    "courtyard": Setting(place="the courtyard"),
    "path": Setting(place="the path"),
}

SCOOTERS = {
    "red": Scooter(id="red", label="a red scooter", phrase="a red scooter with little bell", color="red"),
    "blue": Scooter(id="blue", label="a blue scooter", phrase="a blue scooter with shiny wheels", color="blue"),
    "green": Scooter(id="green", label="a green scooter", phrase="a green scooter with a bright handle", color="green"),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Anna", "Nora"]
BOY_NAMES = ["Finn", "Leo", "Otto", "Ben", "Theo"]
TRAITS = ["curious", "lively", "brave", "cheerful", "stubborn"]


KNOWLEDGE = {
    "scooter": [
        ("What is a scooter?", "A scooter is a small ride-on vehicle with wheels and a handlebar that you push with one foot."),
    ],
    "stop": [
        ("What does a stop sign mean?", "A stop sign tells people to stop moving, look around, and go only when it is safe."),
    ],
    "german": [
        ("What is German?", "German is a language people speak in Germany and in some other places."),
    ],
    "sound": [
        ("What is a sound effect?", "A sound effect is a special noise, like vrrm or skrrt, that helps tell what is happening."),
    ],
    "caution": [
        ("What does caution mean?", "Caution means being careful and thinking about danger before you act."),
    ],
    "conflict": [
        ("What is conflict in a story?", "Conflict is the problem or disagreement that makes a story tense before it gets better."),
    ],
}

ASP_RULES = r"""
rider(X) :- child(X).
warning(X) :- hears_stop(X).
risk(X) :- rider(X), fast(X), bend_ahead(X).
conflict(X) :- rider(X), warning(X), stubborn(X).
safe_stop(X) :- rider(X), caution(X).
story_ok(X) :- rider(X), safe_stop(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for sid in SCOOTERS:
        lines.append(asp.fact("scooter_kind", sid))
        lines.append(asp.fact("sound_on_start", sid, _safe_lookup(SCOOTERS, sid).sound_on_start))
        lines.append(asp.fact("sound_on_brake", sid, _safe_lookup(SCOOTERS, sid).sound_on_brake))
        lines.append(asp.fact("sound_on_stop", sid, _safe_lookup(SCOOTERS, sid).sound_on_stop))
    lines.append(asp.fact("theme", "scooter"))
    lines.append(asp.fact("theme", "german"))
    lines.append(asp.fact("theme", "stop"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like scooter story world with sound effects and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scooter", choices=SCOOTERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    scooter = getattr(args, "scooter", None) or rng.choice(list(SCOOTERS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, child_name=name, child_gender=gender, caregiver=caregiver, trait=trait, scooter=scooter)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, traits=[params.trait, "little"]))
    caregiver = world.add(Entity(id=params.caregiver.title(), kind="character", type=params.caregiver, label=params.caregiver))
    scooter_cfg = _safe_lookup(SCOOTERS, params.scooter)
    scooter = world.add(Entity(id=scooter_cfg.id, type="scooter", label=scooter_cfg.label, phrase=scooter_cfg.phrase))
    scooter.ridden_by = child.id

    make_story(world, child, caregiver, scooter)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a short fable about a child and a scooter, where a German 'stop' warning changes the ride.",
            f"Tell a gentle story that uses the sound effects {scooter_cfg.sound_on_start} and {scooter_cfg.sound_on_stop}.",
            f"Write a cautionary tale about listening before a scooter turn.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    caregiver: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "caregiver")
    scooter: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scooter")
    pred = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prediction")
    return [
        QAItem(
            question=f"Who wanted to ride the scooter?",
            answer=f"{child.id} wanted to ride the scooter because {child.pronoun('subject')} loved {scooter.label}.",
        ),
        QAItem(
            question=f"What did the German warning word and the stop sign tell {child.id} to do?",
            answer=f"They told {child.id} to stop and be careful before the corner.",
        ),
        QAItem(
            question=f"Why did the ride become tense?",
            answer=f"It became tense because {child.id} kept pushing fast even after the warning, and the scooter began to wobble.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the scooter stopped safely, the warning listened to, and {child.id} calmer and wiser.",
        ),
        QAItem(
            question=f"What sound effect marked the start of the ride?",
            answer=f"The scooter started with {scooter.sound_on_start}.",
        ),
        QAItem(
            question=f"Was there any danger predicted?",
            answer=f"Yes. The prediction said wobble={pred['wobble']} and conflict={pred['conflict']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["scooter"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["stop"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["german"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["sound"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["caution"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["conflict"])
    return out


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
    lines.append("== (3) World questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.ridden_by:
            bits.append(f"ridden_by={e.ridden_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(place, scooter) for place in SETTINGS for scooter in SCOOTERS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def build_story_params_from_combo(place: str, scooter: str, seed: int) -> StoryParams:
    rng = random.Random(seed)
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, child_name=name, child_gender=gender, caregiver=caregiver, trait=trait, scooter=scooter, seed=seed)


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, scooter in combos:
            print(f"  {place:10} {scooter}")
        return

    if getattr(args, "all", None):
        seeds = [1, 2, 3, 4, 5]
        samples = [generate(build_story_params_from_combo(place, scooter, seed))
                   for seed, (place, scooter) in zip(seeds, valid_combos())][: getattr(args, "n", None) if getattr(args, "n", None) else 5]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
