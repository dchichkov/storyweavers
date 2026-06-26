#!/usr/bin/env python3
"""
storyworlds/worlds/capital_sum_nation_magic_folk_tale.py
=========================================================

A small folk-tale story world about a capital in a nation, a needed sum, and a
touch of magic that helps make the numbers come out right.

The seed idea is a tiny classical tale:
A child in the capital of a nation must gather the right sum of coins for a
festival gate, but a few coins go missing. A magical helper notices a clue,
finds the hidden coins, and the exact sum is paid so the gate can open.

This world keeps the prose child-facing and causal:
setup -> trouble -> magical help -> resolved ending image.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    helper_of: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    coin_bag: object | None = None
    gatekeeper: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "grandfather"}:
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
    place: str
    nation: str
    capital: str
    gate: str
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
class Magic:
    id: str
    label: str
    phrase: str
    clue: str
    help_text: str
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
class Task:
    id: str
    goal: str
    needed_sum: int
    unit: str
    location: str
    trouble: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.magic_light: bool = False
        self.summed: int = 0

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.magic_light = self.magic_light
        w.summed = self.summed
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "rivergate": Setting(place="the river gate", nation="the green nation", capital="the capital city", gate="river gate"),
    "hillmarket": Setting(place="the hill market", nation="the sun nation", capital="the hill capital", gate="market gate"),
    "stonebridge": Setting(place="the stone bridge", nation="the oak nation", capital="the stone capital", gate="bridge gate"),
}

MAGIC = {
    "lantern_mouse": Magic(
        id="lantern_mouse",
        label="a lantern mouse",
        phrase="a little lantern mouse",
        clue="the mouse's nose twitched at the missing coin",
        help_text="It followed the glimmer under the bench and found the lost coin.",
        tags={"magic", "light", "mouse"},
    ),
    "moon_owl": Magic(
        id="moon_owl",
        label="a moon owl",
        phrase="a moon owl with silver feathers",
        clue="the owl blinked at the shadow under the basket",
        help_text="It peered into the dark and spotted two coins tucked under straw.",
        tags={"magic", "night", "owl"},
    ),
    "brook_fairy": Magic(
        id="brook_fairy",
        label="a brook fairy",
        phrase="a brook fairy with a green shawl",
        clue="the fairy heard the tiny clink behind the water jar",
        help_text="It sang to the jar, and a hidden coin rolled out laughing.",
        tags={"magic", "water", "fairy"},
    ),
}

TASKS = {
    "festival_gate": Task(
        id="festival_gate",
        goal="pay the festival gate",
        needed_sum=3,
        unit="coins",
        location="the gate square",
        trouble="the gate keeper would not open the door without the full sum",
        tags={"festival", "gate", "sum"},
    ),
    "bread_stall": Task(
        id="bread_stall",
        goal="buy bread for the dawn table",
        needed_sum=4,
        unit="coins",
        location="the market path",
        trouble="the baker would not hand over the bread without the full sum",
        tags={"bread", "market", "sum"},
    ),
    "drum_carver": Task(
        id="drum_carver",
        goal="pay the drum carver",
        needed_sum=5,
        unit="coins",
        location="the craft yard",
        trouble="the carver would not finish the drum without the full sum",
        tags={"drum", "craft", "sum"},
    ),
}

HERO_NAMES = ["Mira", "Toma", "Neli", "Boro", "Suri", "Dara", "Pavel", "Jori"]
HELPER_NAMES = ["Aunt", "Grandmother", "Uncle", "Old Man"]


@dataclass
class StoryParams:
    place: str
    task: str
    magic: str
    name: str
    helper_kind: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for task in TASKS:
            for magic in MAGIC:
                out.append((place, task, magic))
    return out


def _coin_vibes(task: Task) -> str:
    return {
        3: "three bright coins",
        4: "four bright coins",
        5: "five bright coins",
    }.get(task.needed_sum, f"{task.needed_sum} bright coins")


def _add_sum(world: World, amount: int) -> None:
    world.summed += amount
    if world.facts.get("hero"):
        hero = _safe_fact(world, world.facts, "hero")
        hero.meters["coins"] = world.summed


def tell(setting: Setting, task: Task, magic: Magic, hero_name: str, helper_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind.lower(), label=helper_kind))
    coin_bag = world.add(Entity(id="bag", type="bag", label="little bag", phrase="a little cloth bag"))
    gatekeeper = world.add(Entity(id="gatekeeper", kind="character", type="man", label="gate keeper"))
    world.facts.update(hero=hero, helper=helper, bag=coin_bag, gatekeeper=gatekeeper, task=task, magic=magic, setting=setting)

    hero.memes["hope"] += 1
    world.say(
        f"In {setting.capital}, in {setting.nation}, there lived a little {hero_name} who knew every lane and fountain."
    )
    world.say(
        f"{hero_name} loved to run through {setting.place} with {helper_kind.lower()}, and the grown-ups said {hero_name} had a kind heart."
    )
    world.say(
        f"One morning, {hero_name} had to {task.goal} with the {setting.gate} keepers, and the full sum was {_coin_vibes(task)}."
    )

    world.para()
    _add_sum(world, task.needed_sum - 1)
    missing = 1
    hero.memes["worry"] += 1
    world.say(
        f"But when {hero_name} counted the coins, {hero_name} found only {world.summed} coin{'' if world.summed == 1 else 's'} in the little bag."
    )
    world.say(
        f"That was not enough, and {task.trouble}."
    )
    world.say(
        f"{helper.phrase.capitalize()} came close and whispered, \"Do not fret. Magic can look where plain eyes do not.\""
    )
    world.magic_light = True
    helper.memes["wise"] = helper.memes.get("wise", 0) + 1
    world.say(
        f"It was then that {magic.phrase} appeared at the edge of the path. {magic.clue.capitalize()}."
    )
    world.say(magic.help_text)

    # Resolve by finding the hidden coin(s).
    if task.needed_sum == 3:
        found = 1
        world.say("Under the bench, one lost coin winked in the light.")
    elif task.needed_sum == 4:
        found = 2
        world.say("Under the straw mat, two lost coins lay side by side.")
    else:
        found = 3
        world.say("Behind the water jar, three lost coins rolled out, one after the other.")

    _add_sum(world, found)
    if world.summed < task.needed_sum:
        pass

    hero.memes["worry"] = 0
    hero.memes["joy"] += 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1

    world.para()
    world.say(
        f"{hero_name} counted again and found the full sum of {world.summed} coins."
    )
    world.say(
        f"Then the gate opened at {setting.place}, and {hero_name} and {helper_kind.lower()} walked through smiling, with the bag light and the morning bright."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    magic = _safe_fact(world, f, "magic")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short folk tale set in {setting.capital} of {setting.nation} about {hero.id} and a missing sum of coins.',
        f'Write a child-friendly magic story where a helper and {magic.label} help {hero.id} reach the full sum for {task.goal}.',
        f'Write a simple folk tale that uses the words "capital", "sum", and "nation" and ends with a gate opening.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    setting = _safe_fact(world, f, "setting")
    magic = _safe_fact(world, f, "magic")
    return [
        QAItem(
            question=f"Where did {hero.id} need to go to {task.goal}?",
            answer=f"{hero.id} needed to go to {setting.place} in {setting.capital}, the capital of {setting.nation}.",
        ),
        QAItem(
            question=f"What was the needed sum in the story?",
            answer=f"The needed sum was {task.needed_sum} coins.",
        ),
        QAItem(
            question=f"What magical helper came to help {hero.id}?",
            answer=f"{magic.phrase} came to help, and its magic helped find the missing coins.",
        ),
        QAItem(
            question=f"Why was {hero.id} worried at first?",
            answer=f"{hero.id} was worried because the little bag did not hold the full sum, and the gate would not open until the right number of coins was counted.",
        ),
        QAItem(
            question=f"What changed at the end of the tale?",
            answer=f"At the end, the missing coins were found, the full sum was paid, and the gate opened for {hero.id}.",
        ),
    ]


KNOWLEDGE = {
    "capital": [
        QAItem(
            question="What is a capital?",
            answer="A capital is the main city of a nation, where important things often happen.",
        )
    ],
    "nation": [
        QAItem(
            question="What is a nation?",
            answer="A nation is a country with its own people, places, and rules.",
        )
    ],
    "sum": [
        QAItem(
            question="What does sum mean?",
            answer="A sum is the total you get when you add numbers together.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special and impossible-feeling kind of help that makes a story wonderous.",
        )
    ],
    "coins": [
        QAItem(
            question="What are coins used for?",
            answer="Coins are small pieces of money that people can count and spend.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [KNOWLEDGE["capital"][0], KNOWLEDGE["nation"][0], KNOWLEDGE["sum"][0], KNOWLEDGE["magic"][0]]
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {e.type:10} {' '.join(bits)}")
    lines.append(f"  summed coins: {world.summed}")
    lines.append(f"  magic light: {world.magic_light}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
task(T) :- task_fact(T).
magic(M) :- magic_fact(M).
valid_story(S,T,M) :- setting(S), task(T), magic(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for tid in TASKS:
        lines.append(asp.fact("task_fact", tid))
    for mid in MAGIC:
        lines.append(asp.fact("magic_fact", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about a capital, a sum, a nation, and a little magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper-kind", choices=["Grandmother", "Aunt", "Uncle", "Old Man"])
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
    choices = valid_combos()
    if getattr(args, "place", None):
        choices = [c for c in choices if c[0] == getattr(args, "place", None)]
    if getattr(args, "task", None):
        choices = [c for c in choices if c[1] == getattr(args, "task", None)]
    if getattr(args, "magic", None):
        choices = [c for c in choices if c[2] == getattr(args, "magic", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, magic = rng.choice(choices)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_kind = getattr(args, "helper_kind", None) or rng.choice(["Grandmother", "Aunt", "Uncle", "Old Man"])
    return StoryParams(place=place, task=task, magic=magic, name=name, helper_kind=helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), MAGIC[params.magic], params.name, params.helper_kind)
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


CURATED = [
    StoryParams(place="rivergate", task="festival_gate", magic="lantern_mouse", name="Mira", helper_kind="Grandmother"),
    StoryParams(place="hillmarket", task="bread_stall", magic="brook_fairy", name="Toma", helper_kind="Aunt"),
    StoryParams(place="stonebridge", task="drum_carver", magic="moon_owl", name="Neli", helper_kind="Old Man"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, task, magic) combos:\n")
        for s, t, m in combos:
            print(f"  {s:10} {t:14} {m}")
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
            header = f"### {p.name}: {p.task} in {p.place} with {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
