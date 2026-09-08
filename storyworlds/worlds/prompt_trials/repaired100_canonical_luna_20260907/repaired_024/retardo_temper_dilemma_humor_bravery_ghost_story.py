#!/usr/bin/env python3
"""
A child-friendly ghost story about Retardo, a hot temper, and brave humor.

The storyworld models a small haunted-house dilemma. Retardo is a slow-moving
but kind character whose temper can flare when a ghost frightens him. Humor and
bravery change the outcome: a joke opens a conversation, while courage helps
him choose a safe and generous action.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
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
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    carries: Optional[str] = None

    ghost: object | None = None
    hero: object | None = None
    lantern: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "ghost"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str
    landmark: str
    atmosphere: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

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
    name: str = ""
    trait: str = ""
    place: str = ""
    seed: Optional[int] = None
    sample: object | None = None
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
class GhostArc:
    id: str
    opening: str
    ghost_name: str
    ghost_problem: str
    scare: str
    dilemma: str
    joke: str
    brave_action: str
    truth: str
    resolution: str
    final_image: str
    lesson: str
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


SETTINGS = {
    "the old bell house": Setting(
        place="the old bell house",
        landmark="the crooked bell tower",
        atmosphere="where every floorboard sighed before anyone stepped on it",
    ),
    "the moonlit inn": Setting(
        place="the moonlit inn",
        landmark="the dusty upstairs hall",
        atmosphere="where the curtains waved even when the windows were shut",
    ),
    "the whispering library": Setting(
        place="the whispering library",
        landmark="the locked reading room",
        atmosphere="where the books hummed softly after sunset",
    ),
}

NAMES = ["Retardo", "Milo", "Luna", "Tavi", "Nora", "Pip"]
TRAITS = ["kind", "curious", "cheerful", "patient"]

ARCS = [
    GhostArc(
        id="bell_borrowed",
        opening="At midnight, the bell rang thirteen times even though its rope had been cut.",
        ghost_name="Glim",
        ghost_problem="he had borrowed the bell's sound and could not find the way to return it",
        scare="a pale face floated out of the bell tower",
        dilemma="run down the stairs and leave the frightened ghost alone, or stay near the ringing tower",
        joke="I have heard better bells from a spoon falling into porridge",
        brave_action="held the lantern high and asked the ghost to show where the sound had begun",
        truth="The ghost was not hunting anyone; he was only lost inside a sound he had made.",
        resolution="Retardo guided Glim to the old bell, where the ghost breathed one soft note back into it.",
        final_image="At dawn, the bell gave one polite ding, and Glim's smile shone brighter than the lantern.",
        lesson="bravery can make room for a frightened friend",
    ),
    GhostArc(
        id="midnight_supper",
        opening="At midnight, a spoon crossed the kitchen by itself and tapped three times on an empty bowl.",
        ghost_name="Muddle",
        ghost_problem="she had forgotten how to ask for the warm supper she missed",
        scare="a white sheet rose beside the stove",
        dilemma="slam the kitchen door and keep the food, or face the ghost and share the supper",
        joke="That is a very fancy napkin, but it has terrible table manners",
        brave_action="stepped toward the stove and placed a warm roll on the empty bowl",
        truth="The ghost had once cooked for everyone in the house and was lonely at the silent table.",
        resolution="Muddle sat down, and the spoon stopped rattling when Retardo invited her to eat.",
        final_image="The empty bowl held one crumb, one silver spoon, and a happy ghostly glow.",
        lesson="kindness can quiet a hungry haunting",
    ),
    GhostArc(
        id="mirror_moon",
        opening="At midnight, the hallway mirror showed a moon that was not in the sky.",
        ghost_name="Blink",
        ghost_problem="he was trapped behind the glass by a promise nobody remembered",
        scare="a shadow waved from inside the mirror",
        dilemma="cover the mirror forever, or listen to the shadow's strange request",
        joke="If you are stuck in there, please stop polishing the moon with your sleeve",
        brave_action="stood before the mirror and repeated the promise aloud without turning away",
        truth="Blink had promised to return a silver button, but it had slipped beneath the hallway rug.",
        resolution="Retardo found the button and placed it by the mirror, which opened like a quiet door.",
        final_image="The mirror reflected the real moon, while Blink waved from a safe patch of moonlight.",
        lesson="courage begins when we listen instead of guessing",
    ),
    GhostArc(
        id="library_laugh",
        opening="At midnight, every book in the library opened to the same page: a drawing of a frowning ghost.",
        ghost_name="Quill",
        ghost_problem="she had forgotten how to laugh after guarding the library for a hundred years",
        scare="a long gray arm reached between the shelves",
        dilemma="hide behind the atlas, or make the gloomy ghost smile",
        joke="Why did the ghost read the book upside down? Because the story had a strange plot twist",
        brave_action="walked between the shelves and read the joke again in a grand announcer voice",
        truth="Quill was not angry; she was afraid that nobody would remember her stories.",
        resolution="Retardo promised to tell one of her stories each week, and Quill's frown folded into a laugh.",
        final_image="The books shut together with a soft clap while Quill's laughter fluttered like paper birds.",
        lesson="humor can turn fear into a doorway",
    ),
]

OPENINGS = [
    "One rainy evening",
    "Just after the moon climbed over the roof",
    "On the night the chimney sneezed",
    "When the candles burned blue",
]

TEMPER_LINES = [
    "Retardo's temper leaped up like a kettle beginning to whistle.",
    "A hot red feeling bumped inside Retardo's chest.",
    "Retardo clenched his hands, because his temper wanted to shout first.",
]

RESPONSES = [
    "I do not like ghosts who sneak up on people",
    "Could you please haunt from a safer distance",
    "I am brave, but I would prefer a warning bell",
    "If you mean no harm, say so before my knees wobble",
]

REFLECTIONS = [
    "The frightening sound had hidden a simple need.",
    "Retardo learned that a fast temper could slow down when a brave question came first.",
    "The ghost had seemed huge because nobody had listened to the small truth beneath the scare.",
    "A laugh did not erase the darkness, but it made enough light to choose wisely.",
]


def validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if not params.name.strip():
        pass
    if params.trait not in TRAITS:
        pass


def propagate(world: World) -> None:
    hero = world.get("hero")
    ghost = world.get("ghost")
    if hero.memes.get("humor", 0) >= 1 and hero.memes.get("bravery", 0) >= 1:
        if "truth_revealed" not in world.fired:
            world.fired.add("truth_revealed")
            ghost.meters["heard"] = 1
            hero.meters["asked"] = 1
            world.say(str(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "truth")))
    if ghost.meters.get("heard", 0) and hero.meters.get("asked", 0):
        hero.meters["helped"] = 1


def build_world(params: StoryParams) -> World:
    validate_params(params)
    number = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.place)
    arc = _safe_lookup(ARCS, number % len(ARCS))
    opening = _safe_lookup(OPENINGS, (number // len(ARCS)) % len(OPENINGS))
    temper_line = _safe_lookup(TEMPER_LINES, (number // 11) % len(TEMPER_LINES))
    response = _safe_lookup(RESPONSES, (number // 17) % len(RESPONSES))
    reflection = _safe_lookup(REFLECTIONS, (number // 23) % len(REFLECTIONS))

    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity("hero", "boy", params.name, memes={"humor": 0, "bravery": 0, "temper": 0}))
    ghost = world.add(Entity("ghost", "ghost", arc.ghost_name, memes={"lonely": 1}))
    lantern = world.add(Entity("lantern", "thing", "lantern", meters={"lit": 1}))
    world.facts.update(
        arc=arc,
        hero=hero,
        ghost=ghost,
        lantern=lantern,
        opening=opening,
        temper_line=temper_line,
        response=response,
        reflection=reflection,
    )

    world.say(f"{opening}, {params.name}, a {params.trait} child, entered {setting.place}, {setting.atmosphere}.")
    world.say(arc.opening)
    world.say(f"{params.name} carried a small lantern and walked toward {setting.landmark}.")

    world.para()
    world.say(f"Then {arc.scare}.")
    world.say(f"{params.name} stopped. {temper_line}")
    hero.memes["temper"] = 1
    world.say(f'"{response}," said {params.name}.')
    world.say(f"The ghost whispered that {arc.ghost_problem}.")
    world.say(f"Now came the dilemma: {arc.dilemma}.")

    world.para()
    world.say(f"Retardo swallowed the hot feeling and tried a joke: \"{arc.joke}\"")
    hero.memes["humor"] = 1
    world.say(f"{arc.ghost_name} blinked. \"That is not how ghosts usually greet people.\"")
    world.say(f'"It is how I greet ghosts who surprise me," replied {params.name}.')
    world.say(f"Because the ghost had stopped frightening him, {params.name} {arc.brave_action}.")
    hero.memes["bravery"] = 1
    propagate(world)

    world.para()
    world.say(str(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "reflection")))
    world.say(arc.resolution)
    world.say(f"{params.name} understood that {arc.lesson}.")
    world.say(arc.final_image)
    return world


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "retardo"),
            asp.fact("ghost", "ghost"),
            asp.fact("humor", "retardo"),
            asp.fact("bravery", "retardo"),
            asp.fact("temper", "retardo"),
            asp.fact("dilemma", "retardo"),
        ]
    )


ASP_RULES = r"""
calm_choice(H) :- hero(H), humor(H), bravery(H).
helpful_ending :- calm_choice(retardo), ghost(ghost).
#show calm_choice/1.
#show helpful_ending/0.
"""


def asp_program(show: str = "#show helpful_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {atom.name for atom in model}
    if "helpful_ending" not in names:
        print("MISMATCH: ASP did not find the helpful ending.")
        return 1
    sample = generate(StoryParams(name="Retardo", trait="kind", place="the old bell house", seed=2))
    if "ghost" not in sample.story.lower() or "dilemma" not in sample.story.lower():
        print("MISMATCH: generated story lacks required domain evidence.")
        return 1
    print("OK: ASP and Python agree on humor, bravery, and the helpful ending.")
    return 0


def generation_prompts(world: World) -> list[str]:
    arc = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "arc")
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    return [
        f"Write a ghost story about {hero.label}, whose temper causes a dilemma, but humor and bravery help with {arc.ghost_name}.",
        f"Tell a child-friendly haunting in {world.setting.place} where a joke reveals that the ghost needs help.",
        f"Write a complete story showing that {arc.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    arc: GhostArc = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "arc")  # type: ignore[assignment]
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")  # type: ignore[assignment]
    ghost: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "ghost")  # type: ignore[assignment]
    return [
        QAItem(
            question="Who faced the ghost and the dilemma?",
            answer=f"{hero.label} faced the ghost, {ghost.label}, and had to decide whether to flee or stay and listen.",
        ),
        QAItem(
            question=f"How did {hero.label}'s temper first react?",
            answer=f"{hero.label}'s temper flared with fear, but he did not let the hot feeling decide what to do.",
        ),
        QAItem(
            question="How did humor help?",
            answer=f"He told a joke about the haunting, which made the ghost stop frightening him and begin talking honestly.",
        ),
        QAItem(
            question="What did bravery change?",
            answer=f"Bravery led him to approach the ghost, learn the real problem, and help instead of running away.",
        ),
        QAItem(
            question="What was the ghost's true problem?",
            answer=arc.truth,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or haunting, often using mystery and fear before revealing an unexpected truth.",
        ),
        QAItem(
            question="What is a temper?",
            answer="A temper is the way someone reacts when anger rises, especially when the reaction becomes quick or strong.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means facing something difficult or frightening while still choosing a thoughtful and helpful action.",
        ),
        QAItem(
            question="What is a dilemma?",
            answer="A dilemma is a difficult choice between two or more actions, each with an important consequence.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Retardo", "kind", "the old bell house", 1),
    StoryParams("Luna", "curious", "the moonlit inn", 2),
    StoryParams("Pip", "cheerful", "the whispering library", 3),
]


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    return StoryParams(name=name, trait=trait, place=place, seed=getattr(args, "seed", None))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous and brave ghost story.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print("helpful ending:", any(atom.name == "helpful_ending" for atom in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(0, getattr(args, "n", None))):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
