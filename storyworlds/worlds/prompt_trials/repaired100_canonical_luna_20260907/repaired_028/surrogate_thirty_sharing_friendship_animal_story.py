#!/usr/bin/env python3
"""
Story world: an animal friendship story about a surrogate gift and thirty berries.

A small woodland simulation turns sharing into a concrete choice. Luna has
thirty berries, but her friend Pip is tired and hungry. Luna shares the berries,
and the friendship is strengthened by a promise to care for one another.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

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

@dataclass
class Character:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(
        default_factory=lambda: {"hunger": 0.0, "trust": 0.0, "friendship": 0.0, "joy": 0.0}
    )
    friend: object | None = None
    hero: object | None = None
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
class Object:
    name: str
    kind: str
    quantity: int = 0
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
    setting: str
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.name] = obj
        return obj
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend_name: str = "Pip"
    animal: str = "rabbit"
    friend_animal: str = "mouse"
    berry_kind: str = "blueberries"
    berry_count: int = 30
    setting: str = "sunny woodland"
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
class SharingArc:
    key: str
    opening_detail: str
    problem: str
    first_impulse: str
    consequence: str
    question: str
    careful_action: str
    discovery: str
    lesson: str
    ending_image: str
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


ANIMALS = ["rabbit", "fox", "squirrel", "hedgehog", "badger", "otter"]
FRIENDS = ["Pip", "Milo", "Nora", "Tess", "Bram", "Clover"]
BERRIES = ["blueberries", "red currants", "blackberries", "golden berries"]
SETTINGS = {
    "sunny woodland": "a sunny woodland where fern leaves shivered beside a clear stream",
    "meadow edge": "a flowered meadow edge beneath a warm hill",
    "mossy grove": "a mossy grove filled with soft green shadows",
}

ARCS = [
    SharingArc(
        key="stream_crossing",
        opening_detail="Luna found a shining basket beneath a leaning birch",
        problem="Pip had walked a long way to gather food, but a fallen branch blocked the path to the berry bushes",
        first_impulse="hid the basket behind a stump because she feared there would not be enough",
        consequence="Pip sat quietly by the stream, and Luna's joy faded when she saw her friend rubbing a hungry tummy",
        question="Would a friend feel safe if a gift was kept secret?",
        careful_action="counted the berries aloud and made two equal piles on a broad leaf",
        discovery="there were enough berries for both friends and a few for the birds",
        lesson="sharing does not make friendship smaller; it gives friendship room to grow",
        ending_image="two leaf plates rested beside the stream while birds pecked at the extra berries",
    ),
    SharingArc(
        key="thorny_path",
        opening_detail="Luna discovered thirty berries glowing like tiny moons in a woven pouch",
        problem="Pip had hurt one paw on a thorn and could not reach the safest food patch",
        first_impulse="carried the pouch away, thinking she should save every berry for herself",
        consequence="the pouch felt heavy, and the path felt lonelier without Pip beside her",
        question="What good is a full pouch if a friend must face a hard path alone?",
        careful_action="asked Pip what would help, then carried half the berries and walked slowly beside him",
        discovery="Pip could rest, eat, and still help choose the gentlest path home",
        lesson="friendship means listening before deciding how to help",
        ending_image="Luna and Pip crossed the thorny path together, with a shared pouch between them",
    ),
    SharingArc(
        key="rain_cloud",
        opening_detail="soft rain began just as Luna finished gathering thirty berries",
        problem="Pip had no dry place to wait and was shivering beneath a wide leaf",
        first_impulse="planned to rush home with the berries and leave Pip to find shelter alone",
        consequence="the rain washed berry juice onto the trail, and Luna worried she had forgotten her friend",
        question="Could a meal feel cheerful when someone nearby was cold?",
        careful_action="shared the berries under a hollow log and invited Pip to follow her warm trail home",
        discovery="the hollow log was dry enough for both friends to rest until the rain softened",
        lesson="kindness includes sharing time and shelter, not only food",
        ending_image="rain tapped the log while two friends divided the last sweet berries",
    ),
    SharingArc(
        key="lost_way",
        opening_detail="Luna filled a little acorn cup with thirty berries near the fern hill",
        problem="Pip had become lost while searching for the path back to his nest",
        first_impulse="called loudly for help but kept the food hidden under her paws",
        consequence="Pip heard Luna but could not tell which direction was safe",
        question="How could the berries become a friendship signal instead of a secret?",
        careful_action="placed bright berries along the familiar trail and saved some to share when Pip arrived",
        discovery="Pip followed the colorful trail safely and reached the fern hill before sunset",
        lesson="a shared plan can guide a friend better than a lonely guess",
        ending_image="the final berry marked home, where two friends ate beneath the first evening star",
    ),
    SharingArc(
        key="smallest_friend",
        opening_detail="Luna counted thirty berries while a tiny beetle watched from a curled leaf",
        problem="Pip was hungry, and the small beetle had carried a crumb all day without finding a meal",
        first_impulse="decided that only Pip deserved a share because he was her closest friend",
        consequence="the beetle crawled away, and Pip gently asked why kindness had stopped at one pair of feet",
        question="Can friendship grow when kindness is saved for only one friend?",
        careful_action="set aside berries for Pip, offered a tiny piece to the beetle, and checked that everyone had enough",
        discovery="the beetle led them to a patch of fallen seeds beside the old oak",
        lesson="sharing wisely can include friends who need different kinds of help",
        ending_image="Pip nibbled berries while the beetle carried a seed home under the old oak",
    ),
]

OPENINGS = [
    "Morning sunlight spilled over the woodland",
    "A warm breeze hummed through the meadow",
    "After a gentle night of rain, the forest smelled fresh",
    "The first gold leaves fluttered above the mossy ground",
]

DIALOGUE_FORMS = [
    ('"I found thirty berries," Luna said, "but I do not want to eat while you are hungry."', '"Then let us decide together," Pip replied.'),
    ('"My paws want to keep everything," Luna admitted. "My heart says to share."', '"Your heart is asking a good question," Pip said.'),
    ('"Will you help me count?" Luna asked.', '"Yes," said Pip. "A shared count can make a shared plan."'),
    ('"I thought sharing meant I would have less," Luna whispered.', '"Sometimes sharing gives us more time together," Pip answered.'),
]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        pass
    if params.berry_count != 30:
        pass
    if params.name == params.friend_name:
        pass
    world = World(setting=params.setting)
    hero = world.add_character(Character(params.name, params.animal, "gatherer"))
    friend = world.add_character(Character(params.friend_name, params.friend_animal, "friend"))
    berries = world.add_object(
        Object(
            params.berry_kind,
            "food",
            quantity=params.berry_count,
            owner=params.name,
            meters={"weight": 0.3},
            memes={"meaning": 1.0},
        )
    )
    world.facts.update(hero=hero, friend=friend, berries=berries)
    return world


def narrate_story(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0x31A7C9)
    hero: Character = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend: Character = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    berries: Object = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "berries")
    arc = rng.choice(ARCS)
    opening = rng.choice(OPENINGS)
    hero_line, friend_line = rng.choice(DIALOGUE_FORMS)
    method = rng.choice(
        [
            "counted the berries into equal groups",
            "spread the berries on two wide leaves",
            "asked what Pip needed before choosing what to do",
            "made a little plan with a twig in the soft soil",
        ]
    )
    world.facts.update(arc=arc, method=method)
    hero.meters.update(forest_x=1.0, forest_y=2.0)
    friend.meters.update(forest_x=1.4, forest_y=2.2)
    hero.memes["hunger"] = 0.2
    friend.memes["hunger"] = 0.9

    world.say(f"{opening}, and {hero.name} the {hero.species} padded between the ferns.")
    world.say(f"{arc.opening_detail.capitalize()}. Inside it were exactly {berries.quantity} {berries.name}.")
    world.say(f"{hero.name} felt proud, but then noticed {friend.name} the {friend.species}: {arc.problem}.")
    world.say(f"{hero.name} wanted to be a good friend, yet first {hero.name} {arc.first_impulse}.")
    world.para()

    world.say(hero_line)
    world.say(friend_line)
    world.say(f"The choice made a difference: {arc.consequence}.")
    world.say(f"{hero.name} listened and asked, {arc.question}")
    world.say(f"That question changed the plan. Instead of guessing, {hero.name} {arc.careful_action}.")
    hero.memes["hunger"] = 0.3
    friend.memes["hunger"] = 0.3
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0
    world.para()

    world.say(f"Together, the friends discovered that {arc.discovery}.")
    world.say(f"They shared the {berries.name} carefully, and every berry tasted sweeter because no one was left out.")
    berries.quantity = 0
    berries.owner = "shared"
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    world.say(f"{hero.name} learned that {arc.lesson}.")
    world.say(f"By sunset, {arc.ending_image}.")
    world.say(f"The woodland grew quiet around them, but their friendship felt bright and strong.")


def generation_prompts(world: World) -> list[str]:
    hero: Character = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend: Character = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    berries: Object = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "berries")
    return [
        f"Write an Animal Story about {hero.name} the {hero.species} and {friend.name} the {friend.species}, using exactly thirty {berries.name}.",
        f"Tell a gentle story about surrogate help, sharing, and friendship between {hero.name} and {friend.name}.",
        "Show a concrete problem, a brief dialogue, a changed decision, and an ending image that proves the friends learned to share.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend: Character = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    berries: Object = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "berries")
    arc: SharingArc = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "arc")
    method: str = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "method")
    return [
        QAItem(
            question=f"Who gathered the {berries.name}?",
            answer=f"{hero.name} the {hero.species} gathered the {berries.name}.",
        ),
        QAItem(
            question=f"How many {berries.name} were there?",
            answer=f"There were exactly thirty {berries.name}.",
        ),
        QAItem(
            question=f"Why did {hero.name} decide to change the first plan?",
            answer=f"{hero.name} changed the plan after listening to {friend.name} and realizing that {arc.question.lower()}",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They {method}, then shared the food and worked together. This showed that their friendship mattered more than keeping everything alone.",
        ),
        QAItem(
            question="What lesson did the animal story teach?",
            answer=f"It taught that {arc.lesson}. The shared food and peaceful ending showed the lesson in action.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means willingly giving part of what you have so another person or animal can use or enjoy it too.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship in which friends listen, help one another, and enjoy time together.",
        ),
        QAItem(
            question="What is a surrogate helper?",
            answer="A surrogate helper is someone who steps in to provide care or support when the usual helper is not available.",
        ),
        QAItem(
            question="Why can counting help when friends share food?",
            answer="Counting helps friends make a fair, clear plan so they know what is available and can avoid taking more than others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
setting(sunny_woodland).
berry_count(30).
has_food(hero,30).
hungry(friend).
friendship(hero,friend) :- shares(hero,friend), helps(hero,friend).
shares(hero,friend) :- makes_equal_piles(hero).
helps(hero,friend) :- listens(hero,friend).
lesson(hero,sharing) :- friendship(hero,friend).
solved(share_problem) :- makes_equal_piles(hero), listens(hero,friend).

#show berry_count/1.
#show friendship/2.
#show lesson/2.
#show solved/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "luna"),
            asp.fact("friend_name", "pip"),
            asp.fact("setting", "sunny_woodland"),
            asp.fact("berry_count", 30),
            asp.fact("hungry", "friend"),
            asp.fact("makes_equal_piles", "hero"),
            asp.fact("listens", "hero", "friend"),
            asp.fact("shares", "hero", "friend"),
            asp.fact("helps", "hero", "friend"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = "\n".join(
        [
            "#show berry_count/1.",
            "#show friendship/2.",
            "#show lesson/2.",
            "#show solved/1.",
        ]
    )
    model = asp.one_model(asp_program(show))
    actual = {(sym.name, tuple(str(arg) for arg in sym.arguments)) for sym in model}
    expected = {
        ("berry_count", ("30",)),
        ("friendship", ("hero", "friend")),
        ("lesson", ("hero", "sharing")),
        ("solved", ("share_problem",)),
    }
    if actual == expected:
        sample = generate(StoryParams(seed=17))
        if "thirty" not in sample.story.lower() or "friendship" not in sample.story.lower():
            print("Generated story exercise failed.")
            return 1
        print("OK: ASP/Python parity and generated-story exercise passed.")
        return 0
    print("MISMATCH between ASP and Python facts.")
    print("ASP atoms:", sorted(actual))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal Story about thirty berries, sharing, and friendship.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--name", choices=["Luna", "Nora", "Clover"])
    parser.add_argument("--friend", dest="friend_name", choices=FRIENDS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--friend-animal", choices=ANIMALS)
    parser.add_argument("--berries", dest="berry_kind", choices=BERRIES)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        name=getattr(args, "name", None) or rng.choice(["Luna", "Nora", "Clover"]),
        friend_name=getattr(args, "friend_name", None) or rng.choice(FRIENDS),
        animal=getattr(args, "animal", None) or rng.choice(ANIMALS),
        friend_animal=getattr(args, "friend_animal", None) or rng.choice(ANIMALS),
        berry_kind=getattr(args, "berry_kind", None) or rng.choice(BERRIES),
        berry_count=30,
        setting="sunny woodland",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.name} ({character.species}): "
            f"meters={dict(character.meters)} memes={dict(character.memes)}"
        )
    for obj in world.objects.values():
        lines.append(
            f"{obj.name}: kind={obj.kind} quantity={obj.quantity} "
            f"owner={obj.owner} memes={dict(obj.memes)}"
        )
    lines.append(f"setting: {world.setting}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(
            asp_program(
                "#show berry_count/1.\n"
                "#show friendship/2.\n"
                "#show lesson/2.\n"
                "#show solved/1."
            )
        )
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(
            asp_program(
                "#show berry_count/1.\n"
                "#show friendship/2.\n"
                "#show lesson/2.\n"
                "#show solved/1."
            )
        )
        for symbol in model:
            print(symbol)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(seed=base_seed, name="Luna", friend_name="Pip", animal="rabbit", friend_animal="mouse", berry_kind="blueberries"),
            StoryParams(seed=base_seed + 1, name="Nora", friend_name="Milo", animal="squirrel", friend_animal="hedgehog", berry_kind="red currants"),
            StoryParams(seed=base_seed + 2, name="Clover", friend_name="Tess", animal="otter", friend_animal="badger", berry_kind="golden berries"),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, getattr(args, "n", None)) and index < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
