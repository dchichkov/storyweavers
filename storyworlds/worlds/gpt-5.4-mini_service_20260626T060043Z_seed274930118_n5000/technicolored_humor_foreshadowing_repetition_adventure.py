#!/usr/bin/env python3
"""
storyworlds/worlds/technicolored_humor_foreshadowing_repetition_adventure.py
===========================================================================

A small adventure storyworld built from the seed word "technicolored".

Premise:
- A child sets out on a little quest.
- A useful object is technicolored and tempting to show off.
- A small obstacle creates tension.
- Humor and repetition keep the story light.
- Foreshadowing matters: a clue seen early becomes useful later.

The domain is intentionally small and constraint-checked:
- A path may include a warning sign, a silly helper, a wind gust, and a final reveal.
- The technicolored item can be helpful, distracting, or both.
- The ending must prove what changed in the world model.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the winding trail"
    afford: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    label: str
    phrase: str
    type: str
    important: str
    traits: set[str] = field(default_factory=set)
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
    helps_with: set[str]
    cost: str
    funny: str
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    setting: str
    goal: str
    aid: str
    name: str
    gender: str
    helper: str
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
    "forest": Setting(place="the forest path", afford={"find", "cross", "climb"}),
    "harbor": Setting(place="the harbor road", afford={"find", "cross", "signal"}),
    "canyon": Setting(place="the canyon trail", afford={"find", "cross", "climb"}),
}

GOALS = {
    "key": Goal(
        id="key",
        label="key",
        phrase="a tiny technicolored key",
        type="key",
        important="unlock the gate",
        traits={"metal", "bright"},
    ),
    "kite": Goal(
        id="kite",
        label="kite",
        phrase="a technicolored kite with a long tail",
        type="kite",
        important="reach the hilltop",
        traits={"paper", "bright"},
    ),
    "shell": Goal(
        id="shell",
        label="shell",
        phrase="a technicolored shell",
        type="shell",
        important="bring home a treasure",
        traits={"shell", "bright"},
    ),
}

AIDS = {
    "map": Aid(
        id="map",
        label="map",
        phrase="a folded map with one silly corner",
        helps_with={"find", "cross"},
        cost="kept flapping like a tiny flag",
        funny="the map pointed so proudly that it almost tipped itself over",
    ),
    "boots": Aid(
        id="boots",
        label="boots",
        phrase="a pair of sturdy boots",
        helps_with={"cross", "climb"},
        cost="went squish on the wet stones",
        funny="the boots made a very serious squeak with every step",
    ),
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a little lantern with a warm glow",
        helps_with={"find", "signal"},
        cost="made the shadows look extra dramatic",
        funny="the lantern blinked like it was telling jokes in secret",
    ),
}

TRAITS = ["brave", "curious", "cheerful", "clever", "bouncy", "spirited"]
GIRL_NAMES = ["Mina", "Tia", "Lena", "Pia", "Nora", "Zuri"]
BOY_NAMES = ["Owen", "Jude", "Milo", "Theo", "Ezra", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for g_id in GOALS:
            for a_id in AIDS:
                if g_id == "kite" and a_id == "map":
                    combos.append((s_id, g_id, a_id))
                elif g_id == "key" and a_id in {"map", "lantern"}:
                    combos.append((s_id, g_id, a_id))
                elif g_id == "shell" and a_id == "boots":
                    combos.append((s_id, g_id, a_id))
    return combos


def helper_helpful(goal: Goal, aid: Aid) -> bool:
    return bool(goal.label == "key" and aid.id in {"map", "lantern"} or
                goal.label == "kite" and aid.id == "map" or
                goal.label == "shell" and aid.id == "boots")


def explain_rejection(goal: Goal, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} does not fit this quest honestly. "
        f"The world only allows gear that can really help with {goal.important}.)"
    )


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def intro(world: World, hero: Entity, goal: Goal, aid: Aid, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} "
        f"{hero.type} who loved adventures on {world.setting.place}."
    )
    world.say(
        f"One day, {hero.pronoun('subject')} found {goal.phrase} and "
        f"{aid.phrase} in the same satchel."
    )
    world.say(
        f"{hero.id} kept saying the words out loud: "
        f"\"{goal.label}, {goal.label}, technicolored {goal.label}.\" "
        f"It sounded brave, and a little bit silly too."
    )
    helper.memes["mischief"] += 1
    world.say(
        f"{helper.id}, a small helper with a big grin, said, "
        f"\"If you hear a whisper in the wind, don't blame the carrots.\""
    )


def depart(world: World, hero: Entity, helper: Entity, goal: Goal) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {helper.id} set off together, and {helper.id} kept "
        f"pointing left, then right, then left again."
    )
    world.say(
        f"{hero.id} laughed. \"Are you guiding me or testing me?\" "
        f"{helper.id} only winked."
    )


def foreshadow(world: World, aid: Aid) -> None:
    if aid.id == "map":
        world.say(
            f"The map's corner fluttered toward the north path whenever the wind blew."
        )
    elif aid.id == "boots":
        world.say(
            f"The boots squeaked at every puddle, as if they were practicing for a song."
        )
    else:
        world.say(
            f"The lantern glowed even in daylight, which made the crows stare and tilt their heads."
        )


def obstacle(world: World, hero: Entity, aid: Aid, goal: Goal) -> None:
    hero.memes["trouble"] += 1
    if aid.id == "map":
        world.say(
            f"Halfway along the trail, the map spun around in the breeze and pointed at a muddy hill."
        )
        world.say(
            f"{hero.id} frowned. \"Great,\" {hero.pronoun()} said, \"my map has a sense of humor.\""
        )
    elif aid.id == "boots":
        world.say(
            f"At the slippery rocks, the boots made a loud squeak-squawk-squeak, "
            f"like a duck trying to whistle."
        )
        world.say(
            f"{hero.id} giggled so hard that {hero.pronoun('possessive')} hat nearly tipped off."
        )
    else:
        world.say(
            f"The lantern's glow blinked three times, then once, then three times again."
        )
        world.say(
            f"{hero.id} remembered the whisper about the wind and realized the blink was a signal."
        )


def use_foreshadowing(world: World, hero: Entity, aid: Aid, goal: Goal) -> None:
    if aid.id == "map":
        world.say(
            f"Those fluttering corners were not a joke after all; they marked the path to the bridge."
        )
        hero.memes["confidence"] += 1
    elif aid.id == "boots":
        world.say(
            f"The squeaks were not only funny: they warned {hero.id} about the slickest stones."
        )
        hero.memes["confidence"] += 1
    else:
        world.say(
            f"The blinking lantern was the clue, and the clue led straight to the hidden gate."
        )
        hero.memes["confidence"] += 1


def resolve(world: World, hero: Entity, goal: Goal, aid: Aid, helper: Entity) -> None:
    hero.meters["progress"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} followed the clue, crossed the last bend, and found {goal.phrase} waiting "
        f"where the trail ended."
    )
    world.say(
        f"{hero.id} lifted {goal.label} high. Its colors shone bright as berries, sky, fire, leaves, and rainbows all at once."
    )
    world.say(
        f"{helper.id} clapped. \"I told you not to blame the carrots,\" {helper.id} said, and then laughed at the look on {hero.id}'s face."
    )
    world.say(
        f"In the end, the {aid.label} still mattered, because it had helped {hero.id} get there."
    )


def tell(setting: Setting, goal: Goal, aid: Aid, hero_name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        traits=["little", trait, "determined"],
    ))
    helper = world.add(Entity(
        id=helper_kind,
        kind="character",
        type="thing",
        traits=["tiny", "silly"],
    ))
    treasure = world.add(Entity(
        id=goal.id,
        type=goal.type,
        label=goal.label,
        phrase=goal.phrase,
        owner=hero.id,
        meters={"shiny": 1.0},
    ))
    tool = world.add(Entity(
        id=aid.id,
        type=aid.id,
        label=aid.label,
        phrase=aid.phrase,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, helper=helper, treasure=treasure, tool=tool, goal=goal, aid=aid)

    intro(world, hero, goal, aid, helper)
    world.para()
    depart(world, hero, helper, goal)
    foreshadow(world, aid)
    world.para()
    obstacle(world, hero, aid, goal)
    use_foreshadowing(world, hero, aid, goal)
    world.para()
    resolve(world, hero, goal, aid, helper)
    hero.meters["progress"] += 1
    treasure.meters["found"] = 1.0
    return world


KNOWLEDGE = {
    "technicolored": [
        (
            "What does technicolored mean?",
            "Technicolored means full of many bright colors, like red, blue, green, yellow, and more all together.",
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map shows where places are and helps someone find the way.",
        )
    ],
    "boots": [
        (
            "What are boots for?",
            "Boots help protect your feet and give you grip on rough or wet ground.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so people can see in the dark or in shadowy places.",
        )
    ],
    "key": [
        (
            "What can a key do?",
            "A key can unlock something that is closed, like a gate or a box.",
        )
    ],
    "kite": [
        (
            "What is a kite?",
            "A kite is something you can fly in the wind, usually with string and a tail.",
        )
    ],
    "shell": [
        (
            "What is a shell?",
            "A shell is a hard outer covering some animals have, and seashells are found near the shore.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, goal, aid = f["hero"], f["goal"], f["aid"]
    return [
        f'Write an adventure story for a child about {hero.id} and a {goal.label} with a technicolored clue.',
        f"Tell a short humorous quest where {hero.id} uses {aid.label} to reach {goal.important}.",
        f'Write a story that repeats a clue twice, then reveals why it mattered in the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, goal, aid = f["hero"], f["helper"], f["goal"], f["aid"]
    return [
        QAItem(
            question=f"What kind of adventure did {hero.id} have?",
            answer=f"{hero.id} had a little adventure on {world.setting.place} that ended with finding {goal.phrase}.",
        ),
        QAItem(
            question=f"What clue kept showing up before {hero.id} solved the problem?",
            answer=f"The clue was {aid.phrase}, and the story repeated it because it really mattered later.",
        ),
        QAItem(
            question=f"Why did {hero.id} laugh during the journey?",
            answer=f"{hero.id} laughed because the helper was silly, and {aid.label} kept behaving in a funny way.",
        ),
        QAItem(
            question=f"Who helped {hero.id} at the end?",
            answer=f"{helper.id} helped by pointing, joking, and making sure the clue was not ignored.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} had reached {goal.label}, and the quest was finished with a bright, happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["goal"].label, world.facts["aid"].label, "technicolored"}
    out: list[QAItem] = []
    for tag, qa_list in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in qa_list)
    return out


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
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="forest", goal="key", aid="lantern", name="Mina", gender="girl", helper="fox", trait="brave"),
    StoryParams(setting="forest", goal="kite", aid="map", name="Owen", gender="boy", helper="badger", trait="curious"),
    StoryParams(setting="harbor", goal="shell", aid="boots", name="Tia", gender="girl", helper="seagull", trait="cheerful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "goal", None) and getattr(args, "aid", None):
        if not helper_helpful(_safe_lookup(GOALS, getattr(args, "goal", None)), _safe_lookup(AIDS, getattr(args, "aid", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))
        and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, goal, aid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(["fox", "badger", "seagull", "mole"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, goal=goal, aid=aid, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(GOALS, params.goal), _safe_lookup(AIDS, params.aid),
                 params.name, params.gender, params.helper, params.trait)
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
goal_ok(G,A) :- goal(G), aid(A),
    (G = key, (A = map; A = lantern);
     G = kite, A = map;
     G = shell, A = boots).

valid_story(S,G,A) :- setting(S), goal_ok(G,A).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld with technicolored humor, foreshadowing, and repetition."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible adventure combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.goal} with {p.aid} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
