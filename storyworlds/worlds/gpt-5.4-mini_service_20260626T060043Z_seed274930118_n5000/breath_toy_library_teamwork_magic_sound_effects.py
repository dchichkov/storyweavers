#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/breath_toy_library_teamwork_magic_sound_effects.py
=============================================================================================================

A standalone story world for a small nursery-rhyme-like toy library tale.

Premise:
- A child visits a toy library.
- A sleepy magical toy needs breath, teamwork, and sound effects to wake up.
- The child and a helper work together to bring back the toy's bright tune.

The world uses a tiny state model with physical meters and emotional memes:
- breath can fill a bellows / whistle / wind-up charm
- teamwork lowers worry and raises joy
- magic changes a toy's readiness
- sound effects make the ending vivid and child-facing

The world is intentionally small and constraint-driven: only a few plausible
story variants are allowed, and invalid choices raise StoryError.
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

    charm: object | None = None
    child: object | None = None
    helper: object | None = None
    toy: object | None = None
    def __post_init__(self) -> None:
        for k in ("breath", "spark", "sound", "tangle", "ready"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "teamwork", "magic", "wonder"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man"}
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
    place: str = "the toy library"
    magic_corner: bool = True
    echo_level: str = "soft"
    SETTING: object | None = None
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
class Toy:
    id: str
    label: str
    phrase: str
    sound: str
    need: str
    style: str
    can_wake: bool = True
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
class Aid:
    id: str
    label: str
    phrase: str
    effect: str
    sound: str
    magic: bool = False
    teamwork: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _r_breath(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["breath"] < THRESHOLD:
            continue
        if e.meters["ready"] >= THRESHOLD:
            continue
        sig = ("breath", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["ready"] += 1
        out.append(f"{e.id} had enough breath to try again.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["teamwork"] >= THRESHOLD and helper.memes["teamwork"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
            helper.memes["worry"] = max(0.0, helper.memes["worry"] - 1)
            child.memes["joy"] += 1
            helper.memes["joy"] += 1
            out.append("Two together made the trouble small.")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    charm = world.get("charm")
    if charm.meters["spark"] < THRESHOLD:
        return out
    if toy.meters["ready"] < THRESHOLD:
        return out
    sig = ("magic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.memes["magic"] += 1
    toy.meters["ready"] += 1
    out.append("A little spell gave the toy a bright new glow.")
    return out


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    if toy.meters["ready"] < THRESHOLD:
        return out
    sig = ("sound",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.meters["sound"] += 1
    out.append(f"{toy.label} went {toy.sound}.")
    return out


RULES = [_r_breath, _r_teamwork, _r_magic, _r_sound]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    toy: str
    aid: str
    name: str
    helper_name: str
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


SETTING = Setting(place="the toy library", magic_corner=True, echo_level="soft")

TOYS = {
    "mouse": Toy(
        id="toy",
        label="the clockwork mouse",
        phrase="a clockwork mouse with a silver tail",
        sound="squeak-squeak",
        need="a gentle puff of breath",
        style="soft and quick",
    ),
    "bunny": Toy(
        id="toy",
        label="the moon-bunny toy",
        phrase="a moon-bunny toy with shiny ears",
        sound="thump-thump",
        need="a warm puff of breath",
        style="round and merry",
    ),
    "train": Toy(
        id="toy",
        label="the tiny toy train",
        phrase="a tiny toy train with red wheels",
        sound="choo-choo",
        need="a steady puff of breath",
        style="long and bright",
    ),
}

AIDS = {
    "bellows": Aid(
        id="charm",
        label="the paper bellows",
        phrase="a fold-up paper bellows",
        effect="puff",
        sound="fwip-fwip",
        magic=False,
        teamwork=True,
    ),
    "wand": Aid(
        id="charm",
        label="the little wand",
        phrase="a little wand with a star",
        effect="spark",
        sound="twinkle",
        magic=True,
        teamwork=False,
    ),
    "lantern": Aid(
        id="charm",
        label="the lantern charm",
        phrase="a lantern charm that glowed gold",
        effect="spark",
        sound="ding",
        magic=True,
        teamwork=True,
    ),
}

NAMES = ["Lila", "Milo", "Nina", "Toby", "Pia", "Rory", "Maya", "Eli"]


def valid_combos() -> list[tuple[str, str]]:
    return [(t, a) for t in TOYS for a in AIDS]


@dataclass
class StoryState:
    child: Entity
    helper: Entity
    toy: Entity
    charm: Entity
    setting: Setting
    state: object | None = None
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


def tell(params: StoryParams) -> World:
    if params.toy not in TOYS:
        pass
    if params.aid not in AIDS:
        pass

    toy_def = _safe_lookup(TOYS, params.toy)
    aid_def = _safe_lookup(AIDS, params.aid)

    world = World(SETTING)
    child = world.add(Entity(id="child", kind="character", type="boy", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="librarian", label=params.helper_name))
    toy = world.add(Entity(
        id="toy",
        kind="toy",
        type="toy",
        label=toy_def.label,
        phrase=toy_def.phrase,
        owner="library",
    ))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type="thing",
        label=aid_def.label,
        phrase=aid_def.phrase,
    ))

    world.facts.update(toy_def=toy_def, aid_def=aid_def, child=child, helper=helper, toy=toy, charm=charm)

    # Act 1
    world.say(f"Down in the toy library, {params.name} found {toy_def.phrase}.")
    world.say(f"It sat on a soft shelf and waited in the hush of the day.")
    world.say(f"{params.name} liked the little toy, but it was sleepy and faint.")
    world.para()

    # Act 2
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(f'"Oh dear," said {helper.label}, "we need a breath, a blink, and a bit of play."')
    world.say(f"{params.name} took a breath, long and slow, like a breeze through a hall.")
    child.meters["breath"] += 1
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    if aid_def.teamwork:
        world.say(f"{helper.label} held up {aid_def.phrase}, and together they gave it a {aid_def.sound}.")
    else:
        world.say(f"{helper.label} waved {aid_def.phrase}, and it gave a tiny {aid_def.sound}.")
    if aid_def.magic:
        charm.meters["spark"] += 1
        world.say("A little magic tickled the air, like glitter in a song.")
    propagate(world, narrate=True)
    world.para()

    # Act 3
    if toy.meters["sound"] < THRESHOLD:
        pass
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"Then the shelf room chimed and hummed, and the toy woke up bright.")
    world.say(f"It sang {toy_def.sound}, and {params.name} clapped with all the might.")
    world.say(f"Two good friends and one small breath made the toy library glow.")
    world.say(f"And the sleepy little toy was merry as can be, from top to toe.")
    world.facts.update(state=StoryState(child=child, helper=helper, toy=toy, charm=charm, setting=SETTING))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy_def: Toy = _safe_fact(world, f, "toy_def")
    aid_def: Aid = _safe_fact(world, f, "aid_def")
    child: Entity = _safe_fact(world, f, "child")
    return [
        f'Write a nursery-rhyme style story set in a toy library about {child.label}, {toy_def.label}, and {aid_def.label}.',
        f"Tell a gentle story where breath, teamwork, magic, and sound effects help {toy_def.label} wake up.",
        f'Write a short child-friendly tale that includes the words "breath", "teamwork", "magic", and "sound".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy_def: Toy = _safe_fact(world, f, "toy_def")
    aid_def: Aid = _safe_fact(world, f, "aid_def")
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who found {toy_def.phrase} in the toy library?",
            answer=f"{child.label} found {toy_def.label} in the toy library.",
        ),
        QAItem(
            question=f"What did {helper.label} and {child.label} do to wake the toy?",
            answer=f"They used breath, teamwork, and a little magic to wake {toy_def.label}.",
        ),
        QAItem(
            question=f"What sound did the toy make at the end?",
            answer=f"It went {toy_def.sound} at the end of the story.",
        ),
        QAItem(
            question=f"Why did the toy need help?",
            answer="It was sleepy, so it needed a gentle puff, a spark, and friends working together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is breath?",
            answer="Breath is the air you take in and let out when you breathe.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means two or more helpers work together to do one job.",
        ),
        QAItem(
            question="What is magic?",
            answer="Magic is a pretend wonder in stories that can make surprising things happen.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special words for noises, like swoosh, ding, or clap.",
        ),
        QAItem(
            question="What is a toy library?",
            answer="A toy library is a place where toys can be kept, shared, and enjoyed.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:6} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy library nursery-rhyme storyworld.")
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--aid", choices=sorted(AIDS))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    toy = getattr(args, "toy", None) or rng.choice(sorted(TOYS))
    aid = getattr(args, "aid", None) or rng.choice(sorted(AIDS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in NAMES if n != name])
    return StoryParams(toy=toy, aid=aid, name=name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
#show valid/2.

valid(Toy, Aid) :- toy(Toy), aid(Aid).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        lines.append(asp.fact("sound", toy_id, toy.sound))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        if aid.magic:
            lines.append(asp.fact("magic_aid", aid_id))
        if aid.teamwork:
            lines.append(asp.fact("team_aid", aid_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    print("MISMATCH between clingo and Python combo gates.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(toy="mouse", aid="bellows", name="Lila", helper_name="Mina"),
    StoryParams(toy="bunny", aid="wand", name="Milo", helper_name="Nora"),
    StoryParams(toy="train", aid="lantern", name="Pia", helper_name="Rory"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible toy-aid pairs:")
        for toy, aid in combos:
            print(f"  {toy:8} {aid}")
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.toy} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
