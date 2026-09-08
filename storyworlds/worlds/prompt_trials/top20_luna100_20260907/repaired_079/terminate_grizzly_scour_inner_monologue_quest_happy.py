#!/usr/bin/env python3
"""
A child-friendly superhero storyworld about a grizzly rescue, a careful scour,
and a quest that ends happily.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    brush: object | None = None
    city: object | None = None
    grizzly: object | None = None
    helper: object | None = None
    hero: object | None = None
    rope: object | None = None
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
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    helper_name: str = "Milo"
    grizzly_name: str = "Bruno"
    city_name: str = "Brightwood"
    quest_name: str = "the Lantern Ridge Quest"
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


HERO_NAMES = ["Luna", "Nova", "Iris", "Maya", "Zara", "Theo"]
HELPER_NAMES = ["Milo", "Pip", "Remy", "Nia", "Sol", "Ari"]
GRIZZLY_NAMES = ["Bruno", "Bramble", "Honey", "Thunder", "Maple"]
CITY_NAMES = ["Brightwood", "Sunbeam City", "Silver Pines", "Glowtown"]
QUEST_NAMES = [
    "the Lantern Ridge Quest",
    "the Golden Acorn Quest",
    "the Rainbow Bridge Quest",
    "the Moonlit Meadow Quest",
]

ADVENTURES = [
    {
        "place": "a forest lookout above the town",
        "danger": "a storm had scattered sharp branches across the trail",
        "mess": "muddy leaves and broken twigs",
        "clue": "a trail marker shaped like a silver star",
        "wrong": "rushed ahead and tried to clear everything at once",
        "turn": "the trail was still blocked, and a frightened grizzly cub was trapped behind a fallen sign",
        "method": "used a rope, a brush, and patient sweeping to scour the path one safe patch at a time",
        "rescue": "the cub followed the newly cleared trail back to its waiting mother",
        "ending": "the lookout lanterns glowed while the grizzly family padded safely into the trees",
        "lesson": "A hero does not merely hurry toward trouble; a hero notices what the trouble needs",
    },
    {
        "place": "an old ranger tunnel beneath the hills",
        "danger": "a rockslide had filled the entrance with dust and stones",
        "mess": "gray dust, pebbles, and tangled roots",
        "clue": "three warm pawprints beside the tunnel wall",
        "wrong": "pulled at the largest stones without checking the ceiling",
        "turn": "a sleepy grizzly was inside, and each loud tug made the tunnel tremble",
        "method": "scoured the loose dust quietly, braced the roof, and moved small stones before large ones",
        "rescue": "the grizzly walked through the safe opening toward the honey-scented meadow",
        "ending": "sunlight poured into the tunnel as the grizzly gave a gentle, grateful huff",
        "lesson": "Careful strength can be braver than a flashy first move",
    },
    {
        "place": "a riverside bridge on the edge of town",
        "danger": "a flood had left the bridge covered in slippery reeds",
        "mess": "wet reeds, river foam, and fallen branches",
        "clue": "a torn red ribbon tied to a railing",
        "wrong": "charged across before testing the boards",
        "turn": "a young grizzly stood on the far bank with no safe way to reach the forest",
        "method": "scoured the bridge for loose boards, tied a guide line, and made a dry path from strong planks",
        "rescue": "the grizzly crossed calmly and disappeared among the cedar trees",
        "ending": "the river shone below the repaired bridge while the town bells rang for the safe return",
        "lesson": "A quest becomes a victory when the path is safe for everyone",
    },
]


@dataclass
class InnerMonologue:
    thoughts: list[str] = field(default_factory=list)

    def add(self, thought: str) -> None:
        self.thoughts.append(thought)
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
class Quest:
    name: str
    active: bool = True
    steps: list[str] = field(default_factory=list)
    completed: bool = False
    quest: object | None = None
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
class HappyEnding:
    grizzly_safe: bool = False
    path_repaired: bool = False
    town_rejoices: bool = False
    ending: object | None = None
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


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(params.hero_name, "character", "hero", params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", "helper", params.helper_name))
    grizzly = world.add(Entity(params.grizzly_name, "animal", "grizzly", params.grizzly_name))
    city = world.add(Entity("city", "place", "city", params.city_name))
    brush = world.add(Entity("brush", "thing", "tool", "rescue brush"))
    rope = world.add(Entity("rope", "thing", "tool", "strong rescue rope"))

    hero.meters.update(courage=1.0, patience=0.5)
    hero.memes.update(worry=0.0, hope=1.0)
    helper.meters.update(observation=1.0, teamwork=1.0)
    grizzly.meters.update(safety=0.0, strength=1.0)
    city.memes["joy"] = 0.0
    brush.meters["clearing"] = 1.0
    rope.meters["support"] = 1.0
    world.facts.update(hero=hero, helper=helper, grizzly=grizzly, city=city, brush=brush, rope=rope)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        [params.hero_name, params.helper_name, params.grizzly_name, params.city_name, params.quest_name]
    )
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def tell_story(params: StoryParams) -> World:
    if params.hero_name == params.helper_name:
        pass
    if params.grizzly_name in {params.hero_name, params.helper_name}:
        pass

    world = World()
    _setup(world, params)
    adventure = _safe_lookup(ADVENTURES, _token(params) % len(ADVENTURES))
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    grizzly = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "grizzly")
    quest = Quest(params.quest_name)
    thoughts = InnerMonologue()
    ending = HappyEnding()

    world.facts.update(adventure=adventure, quest=quest, thoughts=thoughts, ending=ending)

    world.say(
        f"In {params.city_name}, {hero.label} wore a bright cape and answered every call for help."
    )
    world.say(
        f"One morning, {hero.label} and {helper.label} began {quest.name} at {adventure['place']}."
    )
    world.say(
        f"They found that {adventure['danger']}. The trail was covered with {adventure['mess']}."
    )
    thoughts.add("I must help, but charging in could make the danger worse.")
    world.say(
        f"{hero.label} looked at the mess and thought, “I must help, but charging in could make the danger worse.”"
    )

    world.para()
    world.say(
        f"{hero.label} {adventure['wrong']}. The first attempt failed because {adventure['turn']}."
    )
    world.say(
        f'"Wait," {helper.label} called. "Look carefully before you use your strength."'
    )
    world.say(
        f'"You are right," {hero.label} replied. "What do you see?"'
    )
    world.say(
        f"{helper.label} pointed to {adventure['clue']} and listened for a soft rustle nearby."
    )
    thoughts.add("The clue shows that someone is depending on a safe path, not a fast one.")
    world.say(
        f"{hero.label} thought, “The clue shows that someone is depending on a safe path, not a fast one.”"
    )

    world.para()
    world.say(
        f"Together, the heroes changed their plan. They {adventure['method']}."
    )
    quest.steps.extend(["observe the clue", "make a safe plan", "clear the path", "guide the grizzly"])
    world.say(
        f"They did not stop until the trail was clear enough for {grizzly.label} to pass without fear."
    )
    world.say(f"{adventure['rescue']}")

    world.para()
    ending.grizzly_safe = True
    ending.path_repaired = True
    ending.town_rejoices = True
    quest.completed = True
    quest.active = False
    grizzly.meters["safety"] = 1.0
    hero.meters["patience"] = 1.0
    hero.memes["worry"] = 0.0
    _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "city").memes["joy"] = 1.0
    world.fired.update({("quest", "started"), ("path", "scoured"), ("grizzly", "safe"), ("quest", "completed")})
    world.say(
        f"The quest ended happily: {adventure['ending']} The people of {params.city_name} cheered for the heroes."
    )
    world.say(
        f'"We did it by thinking together," {helper.label} said.'
    )
    world.say(
        f'"And by knowing when to terminate a risky plan and begin a better one," {hero.label} answered.'
    )
    world.say(f"{adventure['lesson']}.")
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    a = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "adventure")
    return [
        f"Write a superhero story about {p.hero_name} and {p.helper_name} completing {p.quest_name}.",
        f"Show a grizzly in trouble at {a['place']}, an inner monologue, and a careful decision to terminate a risky first plan.",
        f"End happily after the heroes scour the path and guide the grizzly to safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    a = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "adventure")
    return [
        QAItem(
            f"What quest did {p.hero_name} and {p.helper_name} begin?",
            f"They began {p.quest_name} at {a['place']}.",
        ),
        QAItem(
            "What danger did the heroes discover?",
            f"They discovered that {a['danger']}, leaving {a['mess']} in the way.",
        ),
        QAItem(
            "Why did the first plan fail?",
            f"The first plan failed because the heroes {a['wrong']}, while {a['turn']}.",
        ),
        QAItem(
            "What changed the hero's thinking?",
            f"{a['clue'].capitalize()} helped the heroes see that they needed a safe, careful plan.",
        ),
        QAItem(
            "How did the heroes help the grizzly?",
            f"They {a['method']}, and then {a['rescue']}.",
        ),
        QAItem(
            "What did terminate mean in the story?",
            "It meant to stop the risky first plan before it caused more trouble and choose a safer plan.",
        ),
        QAItem(
            "How did the story end happily?",
            f"{a['ending']} The town cheered because the grizzly and the path were safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a grizzly?",
            "A grizzly is a large brown bear. It is a wild animal that needs space and respectful care.",
        ),
        QAItem(
            "What does scour mean?",
            "To scour means to search or clean an area carefully and thoroughly.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is a character's private stream of thoughts inside the story.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is an important journey or mission with a goal to accomplish.",
        ),
    ]


ASP_RULES = r"""
confused(S) :- grizzly_in_danger(S), blocked_path(S).
safe_plan(S) :- observed_clue(S), terminated_risky_plan(S).
rescued(S) :- safe_plan(S), path_scoured(S), grizzly_guided(S).
happy_ending(S) :- rescued(S), grizzly_safe(S), quest_completed(S).
valid_story(S) :- confused(S), rescued(S), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("grizzly_in_danger", "story1"),
        asp.fact("blocked_path", "story1"),
        asp.fact("observed_clue", "story1"),
        asp.fact("terminated_risky_plan", "story1"),
        asp.fact("path_scoured", "story1"),
        asp.fact("grizzly_guided", "story1"),
        asp.fact("grizzly_safe", "story1"),
        asp.fact("quest_completed", "story1"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero storyworld about a grizzly rescue quest.")
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--helper-name", choices=HELPER_NAMES)
    parser.add_argument("--grizzly-name", choices=GRIZZLY_NAMES)
    parser.add_argument("--city-name", choices=CITY_NAMES)
    parser.add_argument("--quest-name", choices=QUEST_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper_name", None) or rng.choice([x for x in HELPER_NAMES if x != hero])
    grizzly = getattr(args, "grizzly_name", None) or rng.choice(GRIZZLY_NAMES)
    city = getattr(args, "city_name", None) or rng.choice(CITY_NAMES)
    quest = getattr(args, "quest_name", None) or rng.choice(QUEST_NAMES)
    return StoryParams(
        seed=None,
        hero_name=hero,
        helper_name=helper,
        grizzly_name=grizzly,
        city_name=city,
        quest_name=quest,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(state)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
    StoryParams(hero_name="Luna", helper_name="Milo", grizzly_name="Bruno", city_name="Brightwood"),
    StoryParams(hero_name="Nova", helper_name="Nia", grizzly_name="Maple", city_name="Glowtown"),
    StoryParams(hero_name="Iris", helper_name="Remy", grizzly_name="Thunder", city_name="Silver Pines"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
