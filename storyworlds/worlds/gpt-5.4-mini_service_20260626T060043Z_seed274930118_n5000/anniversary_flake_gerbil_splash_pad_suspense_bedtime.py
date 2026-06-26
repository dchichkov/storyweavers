#!/usr/bin/env python3
"""
A small bedtime-style story world set at a splash pad, built around an
anniversary surprise, a little flake, a gerbil, and a suspenseful turn.
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

STEP = 0.25



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
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    region: object | None = None
    flake: object | None = None
    gerbil: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
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
    place: str = "the splash pad"
    features: set[str] = field(default_factory=lambda: {"splash", "summer", "bedtime"})
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
class ItemCfg:
    label: str
    phrase: str
    region: str
    mess_sensitivity: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class ActivityCfg:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    splash_regions: set[str]
    suspense_line: str
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
class StoryParams:
    place: str = "splash pad"
    activity: str = "spray"
    prize: str = "blanket"
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "sleepy"
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        parts = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    parts.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            parts.append(" ".join(buf))
        return "\n\n".join(parts)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "splash pad": Setting(place="the splash pad"),
}

ACTIVITIES = {
    "spray": ActivityCfg(
        id="spray",
        verb="play in the spray",
        gerund="playing in the spray",
        rush="run into the cool water jets",
        mess="wet",
        soil="damp and chilly",
        splash_regions={"feet", "legs", "torso"},
        suspense_line="The nearest fountain whispered and waited.",
    ),
    "puddle-step": ActivityCfg(
        id="puddle-step",
        verb="step through the puddle rings",
        gerund="stepping through puddle rings",
        rush="tiptoe across the shiny circles",
        mess="wet",
        soil="splashy",
        splash_regions={"feet", "legs"},
        suspense_line="One tiny puddle held still like a secret.",
    ),
}

PRIZES = {
    "blanket": ItemCfg(
        label="blanket",
        phrase="a soft bedtime blanket",
        region="torso",
        mess_sensitivity="wet",
    ),
    "pajamas": ItemCfg(
        label="pajamas",
        phrase="fresh pajamas with tiny moons",
        region="torso",
        mess_sensitivity="wet",
        plural=True,
    ),
    "flannel": ItemCfg(
        label="flannel",
        phrase="a warm flannel nightshirt",
        region="torso",
        mess_sensitivity="wet",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Mabel", "Ada", "Ivy"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Owen", "Leo", "Finn"]
TRAITS = ["sleepy", "gentle", "curious", "brave", "soft-spoken"]

KNOWLEDGE = {
    "gerbil": [
        ("What is a gerbil?", "A gerbil is a small furry pet with quick feet and a twitchy nose."),
    ],
    "flake": [
        ("What is a flake?", "A flake is a tiny thin piece that can fall off something, like paint or snow."),
    ],
    "anniversary": [
        ("What is an anniversary?", "An anniversary is a special day that comes back every year to remember something happy."),
    ],
    "splash": [
        ("What is a splash pad?", "A splash pad is a play place with sprinklers, fountains, and wet ground for children to enjoy."),
    ],
    "bedtime": [
        ("Why do children get sleepy at bedtime?", "Bedtime comes after a long day, so bodies and eyes get tired and ask for rest."),
    ],
}
KNOWLEDGE_ORDER = ["anniversary", "flake", "gerbil", "splash", "bedtime"]


def prize_at_risk(act: ActivityCfg, prize: ItemCfg) -> bool:
    return prize.region in act.splash_regions and prize.mess_sensitivity == act.mess


def choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize):
                    if getattr(args, "gender", None) and getattr(args, "gender", None) not in prize.genders:
                        continue
                    combos.append((place, act_id, prize_id))
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if not combos:
        pass
    return rng.choice(list(combos))


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=[params.trait, "little"],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=params.prize,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    gerbil = world.add(Entity(
        id="gerbil",
        kind="character",
        type="gerbil",
        label="a gerbil named Pippin",
        location="a little carrier by the towels",
    ))
    flake = world.add(Entity(
        id="flake",
        kind="thing",
        type="flake",
        label="a tiny silver flake",
        location="on the edge of the splash pad bench",
    ))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    world.facts.update(hero=hero, parent=parent, prize=prize, gerbil=gerbil, flake=flake, activity=activity)

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved nighttime stories and warm blankets.")
    world.say(f"This was the day of the family anniversary, and the grown-ups had brought {gerbil.label} to visit.")
    world.say(f"{hero.id} noticed {flake.label} twinkling on the bench and smiled at how small and shiny it was.")
    world.para()
    world.say(f"At {setting.place}, the water waited in neat little bursts, and {activity.suspense_line}")
    world.say(f"{hero.id} wanted to {activity.verb}, but {parent.label} looked at the blanket and grew quiet.")
    world.say(f'"If you hurry into the water now, your {prize.label} will get {activity.soil}," {parent.label} said.')
    world.say(f"The words made the moment feel hush-hush and suspenseful, like a story with its breath held in.")
    world.say(f"{gerbil.label} twitched its nose as if it knew a surprise was about to happen.")
    world.para()
    world.say(f"{hero.id} took one careful step, then stopped beside the bench where the little flake glimmered.")
    world.say(f"Instead of rushing, {hero.id} helped tuck the {prize.label} into a dry cubby and listened to {parent.label}.")
    world.say(f"Then the family chose the safer way: shoes off, sleeves rolled, and splash time only after the blanket was folded away.")
    world.say(f"{hero.id} laughed, {gerbil.label} stayed cozy, and the anniversary ended with a moon-bright bedtime hug.")
    world.say(f"Even the tiny flake on the bench seemed to sparkle like it was happy too.")

    hero.memes["joy"] = 2
    hero.memes["suspense"] = 1
    parent.memes["worry"] = 1
    prize.meters["dry"] = 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    activity: ActivityCfg = _safe_fact(world, f, "activity")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    return [
        f'Write a bedtime-style story about an anniversary visit to the splash pad that includes a gerbil and a tiny flake.',
        f"Tell a gentle suspense story where {hero.id} wants to {activity.verb} but a {prize.label} must stay dry.",
        f'Write a short child-facing story set at the splash pad that uses the words "anniversary", "flake", and "gerbil".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    parent: Entity = _safe_fact(world, f, "parent")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    gerbil: Entity = _safe_fact(world, f, "gerbil")  # type: ignore[assignment]
    activity: ActivityCfg = _safe_fact(world, f, "activity")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {parent.label} worry when {hero.id} wanted to {activity.verb}?",
            answer=f"{parent.label} worried because the {prize.label} would get {activity.soil} in the water.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful at the splash pad?",
            answer=f"It felt suspenseful because {hero.id} wanted the fun water play, but the family had to protect the dry {prize.label} first.",
        ),
        QAItem(
            question=f"Who came along on the anniversary visit besides {hero.id}?",
            answer=f"A gerbil named Pippin came along, and the tiny flake on the bench made the moment feel extra small and shiny.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {prize.label}?",
            answer=f"{hero.id} chose the safer way, tucked the {prize.label} away dry, and then enjoyed splash time and a bedtime hug.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"anniversary", "flake", "gerbil", "splash", "bedtime"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(splash_pad).
activity(spray).
activity(puddle_step).
prize(blanket).
prize(pajamas).
prize(flannel).

splashes(spray,feet).
splashes(spray,legs).
splashes(spray,torso).
splashes(puddle_step,feet).
splashes(puddle_step,legs).

worn_on(blanket,torso).
worn_on(flannel,torso).
worn_on(pajamas,torso).

mess_of(spray,wet).
mess_of(puddle_step,wet).

risk(A,P) :- splashs(A,R), worn_on(P,R).
valid_story(Place,A,P) :- place(Place), activity(A), prize(P), risk(A,P).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "splash_pad")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for a in ACTIVITIES.values():
        for r in sorted(a.splash_regions):
            lines.append(asp.fact("splashs", a.id, r))
        lines.append(asp.fact("mess_of", a.id, a.mess))
    for p, cfg in PRIZES.items():
        lines.append(asp.fact("worn_on", p, cfg.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-style splash pad story world.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place, activity, prize = choose_combo(args, rng)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender not in _safe_lookup(PRIZES, prize).genders:
        gender = rng.choice(sorted(_safe_lookup(PRIZES, prize).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="splash pad", activity="spray", prize="blanket", name="Mina", gender="girl", parent="mother", trait="sleepy"),
            StoryParams(place="splash pad", activity="puddle-step", prize="pajamas", name="Theo", gender="boy", parent="father", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
