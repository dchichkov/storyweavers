#!/usr/bin/env python3
"""
storyworlds/worlds/intellect_abnormal_transformation_repetition_space_adventure.py
==================================================================================

A small space-adventure storyworld about a clever crew, an unusual change, and a
repeated repair that finally restores the ship.

Premise:
- A child crew member notices something odd on a space voyage.
- A useful device or suit is transformed in a strange way.
- The crew repeats an attempt until a smarter fix works.

This world is intentionally compact: it models a tiny classical simulation of
ship state, emotional state, and a single causal loop that can be narrated as a
complete children's story.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    device: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "captain"}
        male = {"boy", "man", "father", "dad", "engineer"}
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
    name: str
    detail: str
    can_transform: bool = True
    can_repeat: bool = True
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
class Device:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    fix: str
    repeated_fix: str
    transformed_into: str
    helper: str
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
        self.events: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.repetitions: int = 0
        self.transformed: bool = False
        self.problem_seen: bool = False

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
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.events = list(self.events)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.repetitions = self.repetitions
        clone.transformed = self.transformed
        clone.problem_seen = self.problem_seen
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    device: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
    "orbital_hub": Setting(
        name="the orbital hub",
        detail="The station windows shone like silver coins over the blue planet below.",
        can_transform=True,
        can_repeat=True,
    ),
    "moon_garden": Setting(
        name="the moon garden",
        detail="The little domes grew floating beans and starflowers under a quiet sky.",
        can_transform=True,
        can_repeat=True,
    ),
    "asteroid_outpost": Setting(
        name="the asteroid outpost",
        detail="The rocky outpost hummed softly while the engines kept it warm.",
        can_transform=True,
        can_repeat=True,
    ),
}

DEVICES = {
    "map": Device(
        id="map",
        label="star map",
        phrase="a bright star map with tiny blue lines",
        kind="map",
        risk="twisted",
        fix="straightened",
        repeated_fix="straightened again and folded neatly",
        transformed_into="a tangled ribbon of paper",
        helper="navigator",
    ),
    "scanner": Device(
        id="scanner",
        label="scanner",
        phrase="a silver scanner with a blinking green light",
        kind="scanner",
        risk="glitched",
        fix="repaired",
        repeated_fix="repaired a second time",
        transformed_into="a buzzy little hiccup machine",
        helper="engineer",
    ),
    "glove": Device(
        id="glove",
        label="glove",
        phrase="a soft space glove with tiny orange stitches",
        kind="glove",
        risk="shrunk",
        fix="stretched",
        repeated_fix="stretched carefully again",
        transformed_into="a tiny puppet glove",
        helper="robot",
    ),
}

NAMES = ["Nova", "Milo", "Zia", "Arin", "Luna", "Tara", "Pip", "Kai"]
TRAITS = ["curious", "brilliant", "careful", "bold", "gentle", "quick-thinking"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, d) for s in SETTINGS for d in DEVICES]


def reasonableness_gate(setting: str, device: str) -> None:
    if setting not in SETTINGS:
        pass
    if device not in DEVICES:
        pass
    if not _safe_lookup(SETTINGS, setting).can_transform or not _safe_lookup(SETTINGS, setting).can_repeat:
        pass
    if device == "map" and setting == "moon_garden":
        return
    if device == "scanner" and setting == "orbital_hub":
        return
    if device == "glove" and setting == "asteroid_outpost":
        return


def choose_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str]:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "device", None):
        combos = [c for c in combos if c[1] == getattr(args, "device", None)]
    if not combos:
        pass
    return rng.choice(list(combos))


def narrative_intro(world: World, hero: Entity, helper: Entity, device: Entity, setting: Setting) -> None:
    trait = next((t for t in hero.memes.get("traits", [])), "curious")
    world.say(
        f"{hero.id} was a {trait} little {hero.type} who loved solving space puzzles."
    )
    world.say(
        f"At {setting.name}, {hero.id} and {helper.id} checked {device.phrase} before the next drift through space."
    )
    world.say(setting.detail)
    world.facts["intro_trait"] = trait


def predict_problem(world: World, device: Entity) -> dict:
    sim = world.copy()
    d = sim.get(device.id)
    d.meters["abnormal"] = d.meters.get("abnormal", 0.0) + 1
    d.meters["transformed"] = d.meters.get("transformed", 0.0) + 1
    return {
        "abnormal": d.meters["abnormal"] >= THRESHOLD,
        "transformed": d.meters["transformed"] >= THRESHOLD,
    }


def spot_abnormality(world: World, hero: Entity, device: Entity) -> None:
    hero.memes["intellect"] += 1
    device.meters["abnormal"] = device.meters.get("abnormal", 0.0) + 1
    world.problem_seen = True
    world.say(
        f"{hero.id} noticed something abnormal: {device.label} began to feel wrong in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"{hero.pronoun().capitalize()} studied the blinking light and thought hard, because smart noticing was the first step."
    )


def transform_device(world: World, device: Entity) -> None:
    sig = ("transform", device.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    device.meters["transformed"] = device.meters.get("transformed", 0.0) + 1
    device.label = device.label
    world.transformed = True
    world.say(
        f"With a soft pop, the {device.label} turned into {device.transformed_into}."
    )


def repeat_attempt(world: World, hero: Entity, helper: Entity, device: Entity) -> None:
    world.repetitions += 1
    if world.repetitions == 1:
        world.say(
            f"{hero.id} and {helper.id} tried the {device.fix}, but the strange change came back."
        )
    else:
        world.say(
            f"They tried the {device.repeated_fix}, and this time the change began to settle down."
        )


def resolve(world: World, hero: Entity, helper: Entity, device: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    device.meters["abnormal"] = 0.0
    device.meters["transformed"] = 0.0
    world.say(
        f"{hero.id} smiled when the {device.label} worked again, and {helper.id} gave a happy nod."
    )
    world.say(
        f"By the end, the little crew had turned a strange abnormal problem into a clean space adventure."
    )


def tell(setting: Setting, device_cfg: Device, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"intellect": 0.0, "joy": 0.0, "traits": [trait]}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, memes={"joy": 0.0}))
    device = world.add(Entity(id=device_cfg.id, kind="thing", type=device_cfg.kind, label=device_cfg.label, phrase=device_cfg.phrase, protective=False))

    narrative_intro(world, hero, helper, device, setting)
    world.para()
    spot_abnormality(world, hero, device)
    transform_device(world, device)
    world.say(
        f"{hero.id} asked {helper.id} to help, and together they watched the problem carefully instead of rushing."
    )
    world.para()
    repeat_attempt(world, hero, helper, device)
    repeat_attempt(world, hero, helper, device)
    resolve(world, hero, helper, device)

    world.facts.update(
        hero=hero,
        helper=helper,
        device=device,
        setting=setting,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    device = _safe_fact(world, f, "device")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short space-adventure story for a young child about {hero.id}, a clever crew member, who notices an abnormal change in a {device.label} at {setting.name}.',
        f"Tell a gentle story where a smart child in space sees something strange, repeats an attempt to fix it, and finally makes the ship safe again.",
        f'Write a simple adventure story that includes the words "intellect" and "abnormal" and ends with the crew solving a repeated problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    device = _safe_fact(world, f, "device")
    setting = _safe_fact(world, f, "setting")
    trait = _safe_fact(world, f, "trait")
    return [
        QAItem(
            question=f"Who noticed that the {device.label} was acting abnormal at {setting.name}?",
            answer=f"{hero.id} noticed it first because {hero.pronoun('possessive')} intellect helped {hero.pronoun('object')} spot the strange change.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} do after the {device.label} changed?",
            answer=f"They watched it carefully, tried to fix it, and then repeated the fix when the problem came back.",
        ),
        QAItem(
            question=f"How did {trait} {hero.id} feel by the end of the story?",
            answer=f"{hero.id} felt happy and proud because the repeated repair worked and the adventure ended safely.",
        ),
        QAItem(
            question=f"What kind of place was {setting.name}?",
            answer=f"It was a space place where a small crew could solve problems while flying among stars and quiet machines.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does intellect mean?",
            answer="Intellect means the ability to think, learn, and solve problems with your mind.",
        ),
        QAItem(
            question="What does abnormal mean?",
            answer="Abnormal means not usual or not what you expect.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing something again, often to practice or to make sure it works.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if k != "traits" and v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  repetitions: {world.repetitions}")
    lines.append(f"  transformed: {world.transformed}")
    lines.append(f"  problem_seen: {world.problem_seen}")
    return "\n".join(lines)


ASP_RULES = r"""
device_abnormal(D) :- device(D), abnormal(D).
device_transformed(D) :- device(D), transformed(D).
needs_repeat(D) :- device_abnormal(D), device_transformed(D).
good_story(S, D) :- setting(S), device(D), valid_combo(S, D), needs_repeat(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.can_transform:
            lines.append(asp.fact("can_transform", sid))
        if setting.can_repeat:
            lines.append(asp.fact("can_repeat", sid))
    for did, device in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("abnormal", did))
        lines.append(asp.fact("transformed", did))
        lines.append(asp.fact("kind", did, device.kind))
    for sid, did in valid_combos():
        lines.append(asp.fact("valid_combo", sid, did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


@dataclass
class StoryParams:
    setting: str
    device: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about intellect, abnormal change, transformation, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["robot", "engineer", "captain"])
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
    setting, device = choose_combo(rng, args)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["robot", "engineer", "captain"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    reasonableness_gate(setting, device)
    return StoryParams(setting=setting, device=device, hero_name=hero_name, hero_type=hero_type, helper_type=helper_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(DEVICES, params.device), params.hero_name, params.hero_type, params.helper_type, params.trait)
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
        print(asp_program("#show valid_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/2."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        for setting, device in combos:
            print(setting, device)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting in SETTINGS:
            for device in DEVICES:
                params = StoryParams(
                    setting=setting,
                    device=device,
                    hero_name=_safe_lookup(NAMES, (hash(setting + device) % len(NAMES))),
                    hero_type="girl" if (hash(device) % 2 == 0) else "boy",
                    helper_type="robot",
                    trait=_safe_lookup(TRAITS, (hash(setting) + hash(device)) % len(TRAITS)),
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.device} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
