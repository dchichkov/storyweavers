#!/usr/bin/env python3
"""
A small adventure storyworld: a brave child makes a dramatic entry into the
police station to help find a lost puppy, and the day ends happily.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- typed physical meters and emotional memes
- causal world-state simulation
- lazy ASP import inside helpers
- generate / emit / main / parser / params
- optional QA, JSON, trace, ASP, verify, show-asp
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the police station"
    affords: set[str] = field(default_factory=lambda: {"entry"})
    setting: object | None = None
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
class Scene:
    id: str
    verb: str
    gerund: str
    dramatic_entry: str
    risk: str
    tag: str
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
    tags: set[str] = field(default_factory=set)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


SCENES = {
    "entry": Scene(
        id="entry",
        verb="rush inside to tell the officers about the lost puppy",
        gerund="rushing inside to tell the officers about the lost puppy",
        dramatic_entry="made a dramatic entry through the front door",
        risk="scared the adults",
        tag="entry",
    ),
    "police": Scene(
        id="police",
        verb="ask the police for help",
        gerund="asking the police for help",
        dramatic_entry="walked up bravely to the police desk",
        risk="lost the courage to speak",
        tag="police",
    ),
    "bravery": Scene(
        id="bravery",
        verb="speak bravely about the missing puppy",
        gerund="speaking bravely about the missing puppy",
        dramatic_entry="stepped forward with brave feet",
        risk="stayed silent too long",
        tag="bravery",
    ),
}

PRIZES = {
    "puppy": Prize(
        label="puppy",
        phrase="a tiny brown puppy with a red collar",
        type="puppy",
        tags={"lost", "pet"},
    ),
    "badge": Prize(
        label="badge",
        phrase="a shiny badge-shaped sticker",
        type="badge",
        tags={"police"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Ben", "Zoe", "Theo"]
PARENTS = ["mother", "father"]
TRAITS = ["brave", "curious", "kind", "bold"]


@dataclass
class StoryParams:
    scene: str
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


class StoryState:
    def __init__(self, world: World, hero: Entity, parent: Entity, prize: Entity, scene: Scene) -> None:
        self.world = world
        self.hero = hero
        self.parent = parent
        self.prize = prize
        self.scene = scene


def ensure_reasonable(scene: Scene, prize: Prize) -> None:
    if scene.id == "police" and "police" not in prize.tags and prize.type != "puppy":
        pass
    if scene.id in {"entry", "bravery"} and prize.type != "puppy":
        pass


def intro(state: StoryState) -> None:
    w = state.world
    hero = state.hero
    parent = state.parent
    prize = state.prize
    scene = state.scene
    w.say(
        f"{hero.id} was a little {next(t for t in [state.world.facts['trait']] if t)} {hero.type} "
        f"who liked adventure and noticed when something was wrong."
    )
    w.say(
        f"One afternoon, {hero.id}'s {parent.pronoun('possessive') if False else parent.type} told a story "
        f"about {prize.phrase}, and {hero.id} wanted to help."
    )


def predict_success(world: World, scene: Scene, prize: Prize) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["bravery"] += 1
    hero.memes["hope"] += 1
    return scene.id in {"entry", "police", "bravery"} and prize.type == "puppy"


def act_setup(state: StoryState) -> None:
    w = state.world
    hero = state.hero
    parent = state.parent
    prize = state.prize
    scene = state.scene
    w.say(
        f"The trip led them to {w.setting.place}, where a worried officer said the puppy had not been found yet."
    )
    w.say(
        f"{hero.id} took a deep breath and made a dramatic entry, because {hero.pronoun('subject')} did not want to wait outside."
    )
    hero.memes["bravery"] += 1
    hero.memes["hope"] += 1
    w.facts["entry_made"] = True
    if scene.id == "police":
        w.say(f"At the desk, {hero.id} asked the police for help in a small but clear voice.")
    else:
        w.say(f"{hero.id} wanted to speak bravely to the police before the chance could slip away.")


def tension(state: StoryState) -> None:
    w = state.world
    hero = state.hero
    prize = state.prize
    w.say(
        f"For a moment, {hero.id}'s voice shook, and the room felt serious."
    )
    hero.memes["fear"] += 1
    w.facts["tension"] = True
    if prize.type == "puppy":
        w.say("The missing puppy mattered, so everyone listened closely.")


def turn(state: StoryState) -> None:
    w = state.world
    hero = state.hero
    prize = state.prize
    hero.memes["bravery"] += 1
    w.say(
        f"Then {hero.id} remembered why {hero.pronoun('subject')} came: {hero.pronoun('possessive')} brave entry could help."
    )
    w.say(
        f"{hero.id} described the puppy's red collar, the little muddy paws, and the place where it had last been seen."
    )
    w.facts["clue_shared"] = True
    w.facts["police_helping"] = True


def resolution(state: StoryState) -> None:
    w = state.world
    hero = state.hero
    prize = state.prize
    w.say(
        f"The officers nodded, one officer whistled, and soon the search began."
    )
    w.say(
        f"Before long, the puppy came trotting back, tail wagging like a happy flag."
    )
    w.say(
        f"{hero.id} smiled so wide that the whole police station felt brighter."
    )
    w.say(
        f"It was a happy ending: the puppy was safe, and {hero.id} had been brave enough to begin."
    )
    hero.memes["joy"] += 2
    hero.memes["hope"] += 1
    w.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    hero_type = params.gender
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_type,
        label=params.name,
        meters={},
        memes={},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={},
        memes={},
    ))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
    ))
    scene = _safe_lookup(SCENES, params.scene)
    world.facts.update(trait=params.trait, scene=scene, prize=prize_cfg, hero=hero, parent=parent)

    world.say(
        f"{hero.id} was a {params.trait} little {params.gender} who loved adventure."
    )
    world.say(
        f"That day, {hero.id} heard about {prize_cfg.phrase} and knew it was time for a rescue."
    )
    world.para()
    intro(StoryState(world, hero, parent, prize, scene))
    world.para()
    act_setup(StoryState(world, hero, parent, prize, scene))
    tension(StoryState(world, hero, parent, prize, scene))
    world.para()
    turn(StoryState(world, hero, parent, prize, scene))
    resolution(StoryState(world, hero, parent, prize, scene))
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    scene = _safe_fact(world, f, "scene")
    return [
        f'Write an adventure story for a small child about {hero.id} and a dramatic entry at the police station.',
        f"Tell a brave rescue tale where a child must speak to the police and find a happy ending.",
        f"Write a short story in which someone chooses bravery, enters a police station, and helps a lost puppy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    scene: Scene = _safe_fact(world, f, "scene")
    prize: Prize = _safe_fact(world, f, "prize")
    return [
        QAItem(
            question=f"Who made the dramatic entry into the police station?",
            answer=f"{hero.id} made the dramatic entry, because {hero.pronoun('subject')} wanted to help find the lost puppy.",
        ),
        QAItem(
            question=f"Why did {hero.id} go to the police station?",
            answer=f"{hero.id} went there to ask the police for help with {prize.phrase}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, because the puppy was found safe and everyone felt relieved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What do police do?",
            answer="Police help keep people safe, answer calls for help, and look for missing things or people.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard while still choosing to do the right thing.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters feel glad by the end.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(scene="entry", prize="puppy", name="Mia", gender="girl", parent="mother", trait="brave"),
    StoryParams(scene="police", prize="puppy", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(scene="bravery", prize="puppy", name="Nora", gender="girl", parent="mother", trait="bold"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about bravery, police, and a happy ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    scene = getattr(args, "scene", None) or rng.choice(list(SCENES))
    prize = getattr(args, "prize", None) or "puppy"
    ensure_reasonable(_safe_lookup(SCENES, scene), _safe_lookup(PRIZES, prize))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(scene=scene, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
scene(entry).
scene(police).
scene(bravery).

prize(puppy).
prize(badge).

police_related(puppy).
police_related(badge).

valid(S, P) :- scene(S), prize(P), P = puppy.
valid_story(S, P) :- valid(S, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        if "police" in _safe_lookup(PRIZES, pid).tags:
            lines.append(asp.fact("police_related", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(s, p) for s in SCENES for p in PRIZES if p == "puppy"}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate")
    if asp_set - py_set:
        print(" only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
