#!/usr/bin/env python3
"""
A standalone Space Adventure storyworld about a strange trap, a flashback,
and a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    beacon: object | None = None
    companion: object | None = None
    hero: object | None = None
    ship: object | None = None
    trap: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.meters:
            self.meters = {"power": 0.0, "stuck": 0.0, "damage": 0.0, "distance": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "trust": 0.0, "wonder": 0.0}
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
    name: str
    description: str
    gravity: str
    affords: set[str]
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
class StoryParams:
    setting: str = ""
    hero_type: str = ""
    companion_type: str = ""
    name: str = ""
    companion_name: str = ""
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
class Adventure:
    title: str
    destination: str
    mission: str
    trap: str
    clue: str
    flashback: str
    dialogue_problem: str
    repair: str
    lesson: str
    ending: str
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
    fired: set[tuple] = field(default_factory=set)

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


SETTINGS = {
    "orbit": Setting(
        name="the silver orbit",
        description="a bright ring of stars circled a blue planet below",
        gravity="light",
        affords={"scan", "repair", "remember"},
    ),
    "moon": Setting(
        name="the moon's shadow",
        description="gray craters stretched beneath a sky crowded with stars",
        gravity="low",
        affords={"scan", "repair", "remember"},
    ),
    "nebula": Setting(
        name="the violet nebula",
        description="clouds of purple light curled around the little ship",
        gravity="light",
        affords={"scan", "repair", "remember"},
    ),
    "asteroid": Setting(
        name="the glass asteroid",
        description="tiny crystals flashed like frozen rain around the landing ledge",
        gravity="weak",
        affords={"scan", "repair", "remember"},
    ),
}

HERO_TYPES = ["pilot", "astronaut", "space ranger", "scientist"]
COMPANION_TYPES = ["robot", "navigator", "mechanic", "alien"]

NAMES = {
    "pilot": ["Luna", "Mira", "Sol"],
    "astronaut": ["Luna", "Tess", "Ari"],
    "space ranger": ["Luna", "Juno", "Kai"],
    "scientist": ["Luna", "Nia", "Remy"],
    "robot": ["Bolt", "Pip", "Echo"],
    "navigator": ["Vela", "Orin", "Pip"],
    "mechanic": ["Rivet", "Mox", "Tula"],
    "alien": ["Zee", "Momo", "Ixi"],
}

ADVENTURES = [
    Adventure(
        title="the lantern moon",
        destination="a dark moonlet",
        mission="deliver a tiny beacon to a lost space garden",
        trap="a silver floor ring snapped shut around Luna's boot when the beacon was lifted",
        clue="the ring glowed only when the beacon's music played",
        flashback="Luna remembered her grandmother tapping three slow beats on a kitchen cup whenever a drawer jammed",
        dialogue_problem="Luna asked whether the strange ring was dangerous, and Bolt admitted that he had only guessed it was a handle",
        repair="played the beacon's three-note tune backward while tapping the ring in the same slow rhythm",
        lesson="A weird clue is worth studying before it is feared",
        ending="the rescued garden unfolded its glowing flowers, and the beacon lit a warm path home",
    ),
    Adventure(
        title="the upside-down comet",
        destination="a comet turning end over end",
        mission="return a drifting weather seed to its frozen cloud",
        trap="a ribbon of blue light curled around the ship and pulled it toward a silent crack",
        clue="the ribbon loosened whenever the ship's old welcome chime sounded",
        flashback="Luna remembered a school bell that stopped a frightened puppy from running by giving it one familiar sound",
        dialogue_problem="Luna said the trap felt weird, while Vela replied that weird did not mean hopeless",
        repair="broadcast the welcome chime, then steer gently along the ribbon instead of fighting it",
        lesson="Sometimes a trap is also a guide waiting for a calm answer",
        ending="the weather seed opened into snow-bright clouds, and the comet glittered like a smiling stone",
    ),
    Adventure(
        title="the whispering station",
        destination="an abandoned listening station",
        mission="find a signal for three quiet explorer families",
        trap="the station's doorway folded into a crooked loop and held the crew inside",
        clue="the loop changed shape whenever Luna laughed",
        flashback="Luna remembered laughing with her father beside a broken radio until its stuck dial finally moved",
        dialogue_problem="Luna wanted to push the door, but Mox asked what the station seemed to be listening for",
        repair="laughed together, followed the moving loop, and turned the dial only after the doorway became straight",
        lesson="Joy can be a tool when a frightening place forgets how to open",
        ending="the station sent a clear song across space, and distant lamps blinked back in reply",
    ),
    Adventure(
        title="the rainbow crater",
        destination="a crater filled with floating colors",
        mission="carry a sample of harmless stardust to the home observatory",
        trap="a rainbow bubble caught the sample case and began lifting it toward a storm",
        clue="the bubble sank when someone spoke kindly to the tiny sparks inside",
        flashback="Luna remembered soothing a glowing night-light as a child by whispering that morning would come",
        dialogue_problem="Luna feared the case was lost, while Ixi said the sparks sounded lonely rather than angry",
        repair="spoke gently to the sparks and guided the bubble down with the ship's softest air pulse",
        lesson="Listening closely can turn a strange danger into a friend",
        ending="the stardust shimmered in its case, and the crater painted a rainbow over their safe landing",
    ),
    Adventure(
        title="the sleepy satellite",
        destination="a moon-sized satellite",
        mission="wake its garden before the orbit grew cold",
        trap="a maze of blinking paths trapped Luna and Echo beneath the satellite's dome",
        clue="the correct path blinked in the same pattern as Luna's breathing",
        flashback="Luna remembered her mother teaching her to breathe slowly before opening a stuck telescope cover",
        dialogue_problem="Luna said the lights were too weird to follow, and Echo answered that a slow breath could make a pattern",
        repair="breathed together, followed the gentle blinking path, and restarted the garden's sun lamp",
        lesson="Calm attention can reveal a path hidden inside confusion",
        ending="the satellite garden woke with golden vines, and every seedling turned toward Luna's smiling helmet",
    ),
]


OPENINGS = [
    "The little ship drifted above {setting} while {name}, a young {hero_type}, checked the blinking map.",
    "Stars shone around {setting} as {name} the {hero_type} and {companion_name} the {companion_type} prepared for {title}.",
    "Far from home, {name} the {hero_type} guided the ship toward {setting}; {companion_name} watched the instruments.",
    "At {setting}, where {description}, {name} and {companion_name} began one careful space adventure.",
]

DIALOGUES = [
    '"The trap is weird," said {name}. "{weird_answer}," replied {companion_name}.',
    '"Should we pull harder?" asked {name}. "No," said {companion_name}. "Let us learn what the trap is telling us."',
    '"I am scared," {name} admitted. "{flashback_short}," said {companion_name}.',
    '"What changed?" asked {name}. "The clue changed," said {companion_name}. "So our plan can change too."',
]

REFLECTIONS = [
    "They marked the safe route on the map before moving again.",
    "The crew tested the repaired system twice, slowly and carefully.",
    "No one laughed at the first mistake; they used it as a clue.",
    "They recorded the strange event so another traveler would not feel alone.",
    "The ship's small helper light turned green, proving that the danger had passed.",
]


def stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(parts)))


def trapped(ship: Entity) -> bool:
    return ship.meters["stuck"] >= 1.0


def repair_trap(world: World, ship: Entity, beacon: Entity) -> None:
    if ("repair", ship.id) in world.fired:
        return
    if beacon.meters["power"] < 1.0:
        pass
    world.fired.add(("repair", ship.id))
    ship.meters["stuck"] = 0.0
    ship.meters["damage"] = max(0.0, ship.meters["damage"] - 1.0)
    ship.meters["distance"] += 1.0
    beacon.meters["power"] = max(0.0, beacon.meters["power"] - 0.25)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    rng = random.Random(
        params.seed
        if params.seed is not None
        else stable_seed(params.setting, params.name, params.companion_name)
    )
    adventure = rng.choice(ADVENTURES)

    hero = world.add(Entity(params.name, "character", params.hero_type))
    companion = world.add(Entity(params.companion_name, "character", params.companion_type))
    ship = world.add(Entity("ship", "vehicle", "starship", "the little starship"))
    beacon = world.add(Entity("beacon", "thing", "beacon", "a pocket-sized beacon"))
    trap = world.add(Entity("trap", "thing", "space trap", "the weird silver trap"))

    hero.memes["hope"] = 1.0
    hero.memes["wonder"] = 1.0
    companion.memes["trust"] = 1.0
    companion.memes["wonder"] = 1.0
    ship.meters["power"] = 2.0
    beacon.meters["power"] = 1.0

    ship.meters["stuck"] = 1.0
    ship.meters["damage"] = 1.0
    trap.meters["stuck"] = 1.0
    hero.memes["fear"] = 1.0
    companion.memes["fear"] = 1.0

    dialogue = rng.choice(DIALOGUES).format(
        name=params.name,
        companion_name=params.companion_name,
        weird_answer="Weird clues can still be useful",
        flashback_short="I remember a time when an old sound helped us",
    )
    opening = rng.choice(OPENINGS).format(
        setting=setting.name,
        description=setting.description,
        name=params.name,
        hero_type=params.hero_type,
        companion_name=params.companion_name,
        companion_type=params.companion_type,
        title=adventure.title,
    )

    world.say(f"{opening} They had come to {adventure.destination} to {adventure.mission}.")
    world.para()
    world.say(f"Then {adventure.trap}. The danger was weird, and the ship could not move.")
    world.say(f'{dialogue} {adventure.dialogue_problem}.')
    world.para()
    world.say(f"They scanned the trap. {adventure.clue}.")
    world.say(f"That clue opened a flashback: {adventure.flashback}. The memory gave {params.name} an idea.")
    world.para()
    world.say(f"Together they {adventure.repair}.")
    repair_trap(world, ship, beacon)
    hero.memes["fear"] = 0.0
    hero.memes["hope"] += 1.0
    companion.memes["fear"] = 0.0
    companion.memes["trust"] += 1.0
    world.say(f"The trap opened, the ship flew free, and {rng.choice(REFLECTIONS)}")
    world.say(f'"{adventure.lesson}," said {params.companion_name}.')
    world.para()
    world.say(f"It was a happy ending: {adventure.ending}.")
    world.facts = {
        "hero": hero,
        "companion": companion,
        "ship": ship,
        "beacon": beacon,
        "trap": trap,
        "adventure": adventure,
        "setting": setting,
        "flashback": adventure.flashback,
        "trap_fixed": not trapped(ship),
    }
    return world


def generation_prompts(world: World) -> list[str]:
    adventure: Adventure = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "adventure")  # type: ignore[assignment]
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")  # type: ignore[assignment]
    companion: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "companion")  # type: ignore[assignment]
    return [
        f"Write a Space Adventure about {hero.id}, {companion.id}, a weird trap, and a happy ending.",
        f"Tell a story where a flashback helps {hero.id} understand the trap during {adventure.title}.",
        f"Write child-friendly dialogue in which {hero.id} and {companion.id} solve a strange space danger together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")  # type: ignore[assignment]
    companion: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "companion")  # type: ignore[assignment]
    adventure: Adventure = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "adventure")  # type: ignore[assignment]
    setting: Setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {hero.id} and {companion.id} travel?",
            f"They traveled to {setting.name}, near {adventure.destination}, to {adventure.mission}.",
        ),
        QAItem(
            "What trapped the space travelers?",
            f"A weird trap caused trouble when {adventure.trap}.",
        ),
        QAItem(
            "What clue did they discover?",
            f"They discovered that {adventure.clue}.",
        ),
        QAItem(
            "What did the flashback help the hero remember?",
            f"The flashback reminded {hero.id} that {adventure.flashback.lower()}",
        ),
        QAItem(
            "How did the travelers escape?",
            f"They escaped when they {adventure.repair}.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily: {adventure.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a space trap?",
            "A space trap is a device or condition that holds a traveler or vehicle and requires careful thinking to escape.",
        ),
        QAItem(
            "What is a flashback?",
            "A flashback is a story moment that shows something remembered from an earlier time.",
        ),
        QAItem(
            "Why should travelers study a strange clue?",
            "A strange clue may explain how a danger works and suggest a safer solution than pulling or rushing.",
        ),
        QAItem(
            "What makes a happy ending?",
            "A happy ending shows that the main danger has passed and the characters reach safety, understanding, or another hopeful result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
trapped(S) :- ship(S), stuck(S).
powered(B) :- beacon(B), power(B).
repairable(S) :- trapped(S), powered(B), beacon(B).
valid_story(Place, Hero, Companion) :-
    setting(Place),
    hero_type(Hero),
    companion_type(Companion),
    repairable(ship).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for hero in HERO_TYPES:
        lines.append(asp.fact("hero_type", hero))
    for companion in COMPANION_TYPES:
        lines.append(asp.fact("companion_type", companion))
    lines.extend(
        [
            asp.fact("ship", "ship"),
            asp.fact("beacon", "beacon"),
            asp.fact("stuck", "ship"),
            asp.fact("power", "beacon"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {
        (setting, hero, companion)
        for setting in SETTINGS
        for hero in HERO_TYPES
        for companion in COMPANION_TYPES
    }
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: ASP gate matches Python expectations ({len(got)} combinations).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("only in ASP:", sorted(got - expected))
    print("only in Python:", sorted(expected - got))
    return 1


CURATED = [
    StoryParams("orbit", "pilot", "robot", "Luna", "Bolt"),
    StoryParams("moon", "astronaut", "navigator", "Luna", "Vela"),
    StoryParams("nebula", "space ranger", "mechanic", "Luna", "Rivet"),
    StoryParams("asteroid", "scientist", "alien", "Luna", "Zee"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Space Adventure storyworld with a weird trap and a happy ending.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero-type", choices=HERO_TYPES)
    parser.add_argument("--companion-type", choices=COMPANION_TYPES)
    parser.add_argument("--name")
    parser.add_argument("--companion-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    companion_type = getattr(args, "companion_type", None) or rng.choice(COMPANION_TYPES)
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, hero_type))
    companion_name = getattr(args, "companion_name", None) or rng.choice(_safe_lookup(NAMES, companion_type))
    if name == companion_name:
        alternatives = [n for n in _safe_lookup(NAMES, companion_type) if n != name]
        companion_name = rng.choice(alternatives)
    return StoryParams(setting, hero_type, companion_type, name, companion_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.type:12}) meters={meters} memes={memes}")
    lines.append(f"  trap_fixed={world.facts.get('trap_fixed')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        rows = asp_valid_stories()
        print(f"{len(rows)} compatible space-adventure combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < getattr(args, "n", None) and attempt < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        params = sample.params
        header = ""
        if getattr(args, "all", None):
            header = f"### {params.name}: {params.setting} ({params.hero_type} + {params.companion_type})"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
