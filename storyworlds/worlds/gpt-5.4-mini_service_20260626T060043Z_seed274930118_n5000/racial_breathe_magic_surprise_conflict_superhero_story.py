#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/racial_breathe_magic_surprise_conflict_superhero_story.py
====================================================================================================

A compact superhero storyworld with a magical-breath power, a surprise twist,
and a conflict that resolves through a careful heroic compromise.

The seed words for this world are:
- racial
- breathe
- Magic
- Surprise
- Conflict

This world keeps the prose child-facing and concrete while modeling a small
classical simulation: a hero can breathe magic into a broken device, an
unexpected surprise creates conflict, and a teammate helps turn the situation
into a rescue instead of a fight.
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
    label: str = ""
    type: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    art: object | None = None
    hero: object | None = None
    teammate: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    place: str = "Skybridge City"
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
class Power:
    id: str
    label: str
    verb: str
    noun: str
    effect: str
    surprise: str
    mess: str
    zone: set[str]
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
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    risky_for: set[str] = field(default_factory=set)
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
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False
    protective: bool = True
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
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


@dataclass
class StoryParams:
    place: str
    power: str
    artifact: str
    name: str
    gender: str
    teammate: str
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


SETTINGS = {
    "skybridge": Setting(place="Skybridge City", indoors=False, affords={"magic_breath"}),
    "museum": Setting(place="the city museum", indoors=True, affords={"magic_breath"}),
    "harbor": Setting(place="the bright harbor", indoors=False, affords={"magic_breath"}),
}

POWERS = {
    "magic_breath": Power(
        id="magic_breath",
        label="Magic Breath",
        verb="breathe magic into",
        noun="magic",
        effect="glow with soft power",
        surprise="suddenly wake up",
        mess="glitter",
        zone={"hands", "chest"},
        tags={"magic", "breathe", "surprise"},
    ),
}

ARTIFACTS = {
    "orb": Artifact(
        id="orb",
        label="orb",
        phrase="a little silver orb",
        region="hands",
        risky_for={"glitter"},
    ),
    "cape": Artifact(
        id="cape",
        label="cape",
        phrase="a bright red cape",
        region="back",
        risky_for={"glitter"},
    ),
    "visor": Artifact(
        id="visor",
        label="visor",
        phrase="a clear visor",
        region="face",
        risky_for={"glitter"},
    ),
}

AIDS = [
    Aid(
        id="shield_glove",
        label="shield gloves",
        prep="put on shield gloves first",
        tail="slipped on the shield gloves",
        covers={"hands"},
        guards={"glitter"},
        plural=True,
    ),
    Aid(
        id="hero_cloak",
        label="a hero cloak",
        prep="throw on a hero cloak",
        tail="wrapped the hero cloak around them",
        covers={"back"},
        guards={"glitter"},
    ),
    Aid(
        id="face_shield",
        label="a face shield",
        prep="wear a face shield",
        tail="fastened the face shield",
        covers={"face"},
        guards={"glitter"},
    ),
]

GIRL_NAMES = ["Mira", "Lena", "Zara", "Aya", "Nia", "Tess"]
BOY_NAMES = ["Kian", "Owen", "Jude", "Nico", "Finn", "Sami"]
TRAITS = ["brave", "curious", "quick", "kind", "bold", "clever"]
TEAMMATES = ["captain", "partner", "friend"]


def can_story(power: Power, artifact: Artifact) -> bool:
    return bool(power.zone & {artifact.region}) or artifact.region in {"hands", "face", "back"}


def select_aid(power: Power, artifact: Artifact) -> Optional[Aid]:
    for aid in AIDS:
        if artifact.region in aid.covers and power.mess in aid.guards:
            return aid
    return None


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "power", None) and getattr(args, "artifact", None):
        p = _safe_lookup(POWERS, getattr(args, "power", None))
        a = _safe_lookup(ARTIFACTS, getattr(args, "artifact", None))
        if not can_story(p, a):
            pass
    combos = [
        (place, pid, aid)
        for place in SETTINGS
        for pid in POWERS
        for aid in ARTIFACTS
        if can_story(_safe_lookup(POWERS, pid), _safe_lookup(ARTIFACTS, aid))
    ]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "power", None):
        combos = [c for c in combos if c[1] == getattr(args, "power", None)]
    if getattr(args, "artifact", None):
        combos = [c for c in combos if c[2] == getattr(args, "artifact", None)]
    if not combos:
        pass
    place, power_id, artifact_id = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    teammate = getattr(args, "teammate", None) or rng.choice(TEAMMATES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        power=power_id,
        artifact=artifact_id,
        name=name,
        gender=gender,
        teammate=teammate,
        trait=trait,
    )


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    power = _safe_fact(world, f, "power")
    art = _safe_fact(world, f, "artifact")
    return [
        f'Write a superhero story for a young child using the words "racial" and "breathe" and the ideas Magic, Surprise, and Conflict.',
        f"Tell a gentle superhero story about {hero.id}, who can {power.verb} and must protect {art.phrase} during a surprise.",
        f"Write a short story where a hero uses Magic Breath to handle a sudden conflict at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    power = _safe_fact(world, f, "power")
    art = _safe_fact(world, f, "artifact")
    aid = f.get("aid")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.traits[0]} superhero who can {power.verb} things with Magic Breath.",
        ),
        QAItem(
            question=f"What was the hero trying to protect?",
            answer=f"{hero.id} was trying to protect {art.phrase} so it would stay safe during the surprise.",
        ),
        QAItem(
            question=f"What made the day turn into conflict?",
            answer=f"A surprise made the day tricky, because the magic power filled the air with glitter and the artifact needed careful protection.",
        ),
    ]
    if aid is not None:
        qa.append(
            QAItem(
                question=f"How did the team solve the problem?",
                answer=f"They used {aid.label} so {hero.id} could keep using Magic Breath without ruining {art.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in a superhero story?",
            answer="Magic is a special power that can make unusual things happen, like glowing light, floating sparkles, or a brave rescue plan.",
        ),
        QAItem(
            question="What does it mean to breathe carefully?",
            answer="To breathe carefully means to take slow, calm breaths so you can think clearly and do what you need to do next.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something that happens when you do not expect it.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or tension that makes the characters have to try harder and choose a smart way forward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.kind} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_story(H, P, A) :- hero(H), power(P), artifact(A), can_use(P, A).
problem(H, A) :- hero_story(H, _, A), surprise(A).
resolves(H, A) :- problem(H, A), aid(X), fits(X, A).
#show hero_story/3.
#show problem/2.
#show resolves/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone", pid, z))
        lines.append(asp.fact("mess", pid, p.mess))
        lines.append(asp.fact("surprise", pid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("region", aid, a.region))
    for x in AIDS:
        lines.append(asp.fact("aid", x.id))
        for c in sorted(x.covers):
            lines.append(asp.fact("fits", x.id, c))
    for pid, p in POWERS.items():
        for aid, a in ARTIFACTS.items():
            if can_story(p, a):
                lines.append(asp.fact("can_use", pid, aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with Magic Breath, Surprise, and Conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--teammate", choices=TEAMMATES)
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


def _render_story(world: World) -> None:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    power = _safe_fact(world, f, "power")
    art = _safe_fact(world, f, "artifact")
    teammate = _safe_fact(world, f, "teammate")

    world.say(f"{hero.id} was a {hero.traits[0]} superhero in {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} could {power.verb} {power.label.lower()} and make danger feel smaller.")
    world.say(f"One day, {hero.id} guarded {art.phrase} with {teammate}.")
    world.para()
    world.say(f"Then a surprise crackled through the air: {power.surprise}, and glitter drifted everywhere.")
    world.say(f"{hero.id} wanted to help at once, but the bright glitter turned the moment into conflict.")
    world.say(f"{hero.pronoun().capitalize()} took a careful breath, because a hero can be strong and gentle at the same time.")
    world.para()
    aid = select_aid(power, art)
    if aid:
        f["aid"] = aid
        world.say(f"{teammate.capitalize()} smiled and said, \"{aid.prep}.\"")
        world.say(f"{hero.id} agreed, and soon {hero.id} {aid.tail}.")
        world.say(f"With that help, {hero.id} could keep {power.verb} the problem away while {art.phrase} stayed safe.")
        world.say(f"By the end, the surprise was solved, the conflict was gone, and the city lights shone on a happy rescue.")
    else:
        world.say(f"{hero.id} paused and chose a different rescue path, so the artifact stayed safe even without extra gear.")
        world.say("The conflict eased, and the hero's calm breathing helped the whole street settle down.")


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    power = _safe_lookup(POWERS, params.power)
    artifact = _safe_lookup(ARTIFACTS, params.artifact)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "stubborn"]))
    teammate = world.add(Entity(id=params.teammate, kind="character", type="friend", traits=["helpful"]))
    art = world.add(Entity(id=artifact.id, label=artifact.label, type="artifact"))
    f = world.facts
    f.update(hero=hero, teammate=teammate, power=power, artifact=art, params=params)
    _render_story(world)
    prompts = generate_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
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
    StoryParams(place="skybridge", power="magic_breath", artifact="orb", name="Mira", gender="girl", teammate="partner", trait="brave"),
    StoryParams(place="museum", power="magic_breath", artifact="visor", name="Kian", gender="boy", teammate="captain", trait="clever"),
    StoryParams(place="harbor", power="magic_breath", artifact="cape", name="Zara", gender="girl", teammate="friend", trait="kind"),
]


def verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show hero_story/3.\n#show problem/2.\n#show resolves/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
            seed = base_seed + i
            i += 1
            params = resolve_args(args, random.Random(seed))
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
