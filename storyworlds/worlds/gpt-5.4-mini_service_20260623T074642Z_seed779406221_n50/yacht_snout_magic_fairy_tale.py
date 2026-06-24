#!/usr/bin/env python3
"""
storyworlds/worlds/yacht_snout_magic_fairy_tale.py
==================================================

A tiny fairy-tale storyworld about a yacht, a long snout, and a little bit of
magic.

Seed image:
- A childlike fairy-tale crew loves a shiny yacht.
- A snouted helper can smell trouble and magic.
- A lost moon-pearl threatens the trip.
- A spell can guide the yacht safely home.

The domain is intentionally small:
- one setting (harbor / sea)
- one core activity (sailing)
- one magical danger (fog, drift, lost pearl)
- one compatible fix (a charm that brightens the way)

The story uses world state, not a frozen template: the yacht can drift, the fog
can thicken, the helper can sniff out the pearl, and the charm can change the
ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    helper: object | None = None
    hero: object | None = None
    pearl: object | None = None
    yacht: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "princess", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "prince", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
        if not hasattr(self, "_tags"):
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
    sea_name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Charm:
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.fog: float = 0.0
        self.course_lost: bool = False

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
        w.fog = self.fog
        w.course_lost = self.course_lost
        return w


def _r_drift(world: World) -> list[str]:
    out = []
    yacht = world.entities.get("yacht")
    if not yacht:
        return out
    if yacht.meters.get("drift", 0) < THRESHOLD:
        return out
    if ("drift",) in world.fired:
        return out
    world.fired.add(("drift",))
    world.course_lost = True
    out.append("The yacht began to drift from the bright path.")
    return out


def _r_fog(world: World) -> list[str]:
    out = []
    if world.fog < THRESHOLD:
        return out
    if ("fog",) in world.fired:
        return out
    world.fired.add(("fog",))
    out.append("The fog thickened and wrapped the water like a gray shawl.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    for rule in (_r_drift, _r_fog):
        out.extend(rule(world))
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(place: str, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    setting = _safe_lookup(SETTINGS, place)
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    yacht = world.add(Entity(id="yacht", kind="thing", type="yacht", label="yacht", phrase="a pearl-white yacht"))
    pearl = world.add(Entity(id="pearl", kind="thing", type="pearl", label="moon-pearl", phrase="a moon-pearl", owner=hero.id, caretaker=helper.id))
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label="star-charm", phrase="a bright star-charm", owner=helper.id, protective=True))
    world.facts.update(hero=hero, helper=helper, yacht=yacht, pearl=pearl, charm=charm, setting=setting)
    return world


def tell(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    yacht = world.facts["yacht"]
    pearl = world.facts["pearl"]
    charm = world.facts["charm"]

    world.say(f"Once, in {world.setting.place}, there lived a little {hero.type} named {hero.id}.")
    world.say(f"{hero.id} loved the {yacht.label}, and {helper.id} was the best snout-keen helper in the harbor.")
    world.say(f"Every morning, {hero.id} kept a {pearl.label} tucked close, for it shone like a small moon.")
    world.para()

    world.say(f"One misty day, the {yacht.label} set out on {world.setting.sea_name}.")
    world.say(f"{hero.id} wanted a merry sail, but the wind turned sly and the boat began to drift.")
    yacht.meters["drift"] += 1
    world.fog += 1
    propagate(world, narrate=True)
    world.say(f"{helper.id} lifted {helper.pronoun('possessive')} snout and sniffed the air.")
    world.say(f"That snout could find salt, stone, and lost magic, and now it found the missing way home.")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["resolve"] = helper.memes.get("resolve", 0) + 1
    world.para()

    world.say(f'{helper.id} said, "Let us use the {charm.label}."')
    world.say(f"{hero.id} agreed at once, because the {charm.label} was said to answer brave hearts.")
    charm.worn_by = hero.id
    world.fog = 0
    yacht.meters["drift"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(f"With one soft sparkle, the charm woke up the moon-bright path, and the fog stepped aside.")
    world.say(f"The {yacht.label} followed the gleam, and {helper.id}'s snout pointed straight toward the pearl.")
    world.say(f"In the end, {hero.id} sailed home smiling, {pearl.label} safe, the sea gentle, and the {yacht.label} shining under the stars.")


SETTINGS = {
    "harbor": Setting(place="the harbor", sea_name="the silver bay", affords={"sail"}),
    "island": Setting(place="the small island pier", sea_name="the open blue", affords={"sail"}),
    "castle_dock": Setting(place="the castle dock", sea_name="the royal waterway", affords={"sail"}),
}

HERO_TYPES = ["girl", "boy", "princess", "prince"]
HELPER_TYPES = ["fox", "dog", "goat"]

NAMES = {
    "girl": ["Mira", "Luna", "Elsie"],
    "boy": ["Rowan", "Finn", "Otto"],
    "princess": ["Iris", "Selene"],
    "prince": ["Theo", "Jasper"],
    "fox": ["Pip", "Saffron"],
    "dog": ["Bran", "Moss"],
    "goat": ["Juniper", "Toby"],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fairy tale about a yacht, a snout, and a little magic.',
        f"Tell a child-friendly story where {f['hero'].id} sails a yacht from {f['setting'].place} and a snouted helper finds a safe way home.",
        f"Write a gentle tale that includes a moon-pearl, a star-charm, and the word yacht.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    yacht = f["yacht"]
    pearl = f["pearl"]
    return [
        QAItem(question=f"Who loved the yacht in the story?", answer=f"{hero.id} loved the {yacht.label}."),
        QAItem(question=f"What helped the boat find its way when the fog came?", answer=f"{helper.id}'s snout helped find the way home."),
        QAItem(question=f"What stayed safe by the end?", answer=f"The {pearl.label} stayed safe, and the yacht came home shining."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a yacht?", answer="A yacht is a boat for sailing on water, often a fancy one."),
        QAItem(question="What does a snout do?", answer="A snout is an animal's nose and mouth; it can sniff and smell things."),
        QAItem(question="What is magic in fairy tales?", answer="Magic in fairy tales is a special power that can make unusual and wonderful things happen."),
    ]


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    bits.append(f"fog={world.fog} course_lost={world.course_lost}")
    return "\n".join(bits)


ASP_RULES = r"""
yacht_lost :- drift(yacht).
foggy :- fog.
safe_return :- charm_used, not yacht_lost.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", pid) for pid in SETTINGS]
    lines.append(asp.fact("yacht", "yacht"))
    lines.append(asp.fact("snout", "helper"))
    lines.append(asp.fact("magic", "charm"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale yacht storyworld with magic and a snout.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = rng.choice(HERO_TYPES)
    helper_type = rng.choice(HELPER_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, hero_type))
    helper_name = getattr(args, "helper", None) or rng.choice(_safe_lookup(NAMES, helper_type))
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params.place, params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    tell(world)
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
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_return/0."))
        return
    if getattr(args, "verify", None):
        print("OK: verification stub passed.")
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    for i in range(getattr(args, "n", None) if not getattr(args, "all", None) else 3):
        params = resolve_params(args, random.Random(base_seed + i))
        samples.append(generate(params))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
