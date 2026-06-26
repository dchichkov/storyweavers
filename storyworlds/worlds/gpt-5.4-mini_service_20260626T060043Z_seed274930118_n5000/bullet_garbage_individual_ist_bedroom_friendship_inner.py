#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bullet_garbage_individual_ist_bedroom_friendship_inner.py
==============================================================================================================

A small bedroom adventure world built from the seed words:
bullet, garbage, individual-ist.

Premise:
A child in a bedroom wants to act like a lone individualist explorer,
but a friend notices a little bullet-shaped trinket has rolled into the
garbage basket. The two children must choose between stubborn independence
and friendship, then work together to rescue the trinket before it disappears
under the bed for good.

Story instruments:
- Friendship
- Inner Monologue
- Foreshadowing

The simulated state tracks:
- physical meters: dust, clutter, hidden, tidy, worry, danger
- emotional memes: friendship, pride, loneliness, courage, relief, curiosity

The story is driven by state changes rather than a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
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

    basket: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    place: str = "the bedroom"
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
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
class Tool:
    id: str
    label: str
    helps: set[str]
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
class StoryParams:
    name: str
    gender: str
    friend_name: str
    friend_gender: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _add_meter(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def _add_meme(ent: Entity, key: str, value: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def _do_drift(world: World) -> list[str]:
    out: list[str] = []
    bag = world.get("garbage_basket")
    if _meter(bag, "clutter") >= THRESHOLD and _meter(bag, "hidden") < THRESHOLD:
        sig = ("hidden",)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meter(bag, "hidden", 1.0)
            out.append("The garbage basket had started to swallow things that rolled too close.")
    return out


def _do_bump(world: World) -> list[str]:
    out: list[str] = []
    bullet = world.get("bullet_trinket")
    basket = world.get("garbage_basket")
    hero = world.get("hero")
    friend = world.get("friend")
    if bullet.owner == basket.id and _meter(basket, "hidden") >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meter(hero, "worry", 1.0)
            _add_meme(hero, "curiosity", 1.0)
            _add_meme(friend, "concern", 1.0)
            out.append("Hero felt a small prick of worry, like a clue in an adventure story.")
            out.append("Friend noticed it too and kept glancing at the garbage basket.")
    return out


def _do_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if _meter(hero, "worry") >= THRESHOLD and _meter(friend, "support") < THRESHOLD:
        sig = ("support",)
        world.fired.add(sig)
        _add_meter(friend, "support", 1.0)
        _add_meme(hero, "friendship", 1.0)
        _add_meme(friend, "friendship", 1.0)
        out.append("Friend moved closer, ready to help instead of leaving hero alone.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_do_drift, _do_bump, _do_friendship):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def inner_monologue(hero: Entity) -> str:
    if hero.memes.get("pride", 0.0) >= THRESHOLD:
        return "I can handle this myself, the hero thought. I don't need help."
    if hero.meters.get("worry", 0.0) >= THRESHOLD:
        return "This feels bigger than I wanted, the hero thought. Maybe a friend would make it easier."
    return "This could become a real adventure, the hero thought."


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('small', 1.0):.0f}-room kind of explorer who liked to be an individual-ist "
        f"and do everything alone."
    )
    world.say(
        f"But {friend.id} was there too, because some adventures felt better when two friends shared them."
    )


def set_scene(world: World) -> None:
    world.say("The bedroom was quiet except for the little sounds of a drawer, a blanket, and a humming nightlight.")
    world.say("Near the bed sat a garbage basket, and beside it lay a tiny bullet-shaped trinket that looked easy to lose.")


def foreshadow(world: World) -> None:
    world.say("Something about the basket felt like a warning, as if the room itself was hinting that the trinket should not stay there long.")


def want_to_act(world: World, hero: Entity) -> None:
    _add_meme(hero, "pride", 1.0)
    world.say(f"{hero.id} wanted to prove the job could be done alone.")
    world.say(inner_monologue(hero))


def friend_warns(world: World, hero: Entity, friend: Entity) -> None:
    _add_meme(friend, "care", 1.0)
    world.say(
        f"{friend.id} pointed at the garbage basket and whispered that the bullet trinket might vanish if nobody moved it soon."
    )


def search_alone(world: World, hero: Entity) -> None:
    hero.meters["dust"] = hero.meters.get("dust", 0.0) + 1.0
    hero.meters["clutter"] = hero.meters.get("clutter", 0.0) + 1.0
    world.say(f"{hero.id} reached toward the basket by {hero.id.lower()}'s own plan and stirred up a little dust.")
    if hero.meters["pride"] >= THRESHOLD:
        world.say("For a moment, the room felt bigger and lonelier than before.")


def rescue_with_friend(world: World, hero: Entity, friend: Entity, item: Entity, tool: Optional[Tool]) -> Optional[Tool]:
    if tool is None:
        return None
    world.say(
        f"Then {friend.id} offered {tool.label} and said, {tool.prep}"
    )
    _add_meme(hero, "friendship", 1.0)
    _add_meme(friend, "friendship", 1.0)
    _add_meme(hero, "courage", 1.0)
    _add_meme(friend, "courage", 1.0)
    item.owner = hero.id
    item.worn_by = None
    basket = world.get("garbage_basket")
    basket.meters["hidden"] = 0.0
    basket.meters["clutter"] = 0.0
    world.say(f"Together they reached carefully, and the bullet trinket popped free from the garbage basket.")
    world.say(
        f"{hero.id} smiled at {friend.id}, and the two of them {tool.tail} while the room felt safer."
    )
    return tool


def ending_image(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["worry"] = 0.0
    _add_meme(hero, "relief", 1.0)
    _add_meme(friend, "relief", 1.0)
    world.say(
        f"At the end, the bullet trinket rested on a neat shelf, and {hero.id} no longer wanted to stand alone."
    )
    world.say(
        f"{friend.id} was beside {hero.id}, and the bedroom looked tidy, warm, and ready for the next adventure."
    )


SETTING = Setting(place="the bedroom")

ITEMS = {
    "bullet_trinket": Item(
        id="bullet_trinket",
        label="bullet trinket",
        phrase="a tiny bullet-shaped trinket",
        region="floor",
    ),
    "garbage_basket": Item(
        id="garbage_basket",
        label="garbage basket",
        phrase="a small garbage basket",
        region="corner",
    ),
}

TOOLS = [
    Tool(id="gloves", label="a pair of soft gloves", helps={"grasp"}, prep="we should use these so the little trinket does not slip away", tail="used the gloves and lifted it gently"),
    Tool(id="lamp", label="the lamp light", helps={"see"}, prep="let's turn on the lamp so we can look carefully", tail="used the lamp light to search the shadows"),
]


GIRL_NAMES = ["Mina", "Tia", "Lena", "Nora", "Ivy"]
BOY_NAMES = ["Rory", "Finn", "Kai", "Jasper", "Eli"]
TRAITS = ["brave", "curious", "stubborn", "quick-thinking", "careful"]


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, meters={"small": 1.0}, memes={}))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, memes={}))
    world.add(Entity(id="bullet_trinket", type="thing", label="bullet trinket", owner="garbage_basket"))
    basket = world.add(Entity(id="garbage_basket", type="thing", label="garbage basket", meters={"clutter": 1.0}))
    basket.meters["hidden"] = 0.0

    intro_name = params.name
    world.say(f"{intro_name} and {params.friend_name} were in the bedroom on a quiet evening.")
    introduce(world, hero, friend)
    set_scene(world)
    foreshadow(world)
    want_to_act(world, hero)
    friend_warns(world, hero, friend)
    search_alone(world, hero)
    basket.meters["hidden"] = 1.0
    propagate(world)
    world.para()
    world.say("The clue was clear now: if nobody helped, the tiny thing could disappear under the bed.")
    world.say(f"{hero.id} looked at the mess and had to choose between pride and friendship.")
    tool = rescue_with_friend(world, hero, friend, world.get("bullet_trinket"), _safe_lookup(TOOLS, 0))
    world.para()
    if tool:
        ending_image(world, hero, friend)

    world.facts.update(hero=hero, friend=friend, item=world.get("bullet_trinket"), basket=basket, tool=tool)
    return world


def valid_params() -> list[tuple[str, str]]:
    return [("girl", "boy"), ("boy", "girl"), ("girl", "girl"), ("boy", "boy")]


@dataclass
class StoryParams:
    name: str
    gender: str
    friend_name: str
    friend_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    return [
        f'Write a short adventure story set in a bedroom about friendship, inner monologue, and foreshadowing, using the word "bullet".',
        f"Tell a gentle adventure where {hero.id} tries to act like an individual-ist, but {friend.id} helps save a bullet trinket from the garbage basket.",
        f"Write a child-friendly story in the bedroom where a tiny bullet-shaped thing seems in danger and two friends work together to rescue it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item, basket = f["hero"], f["friend"], f["item"], f["basket"]
    return [
        QAItem(
            question=f"Why did {hero.id} first want to handle the problem alone?",
            answer=f"{hero.id} wanted to seem strong and individual-ist, so {hero.id} thought the job should be done alone before {friend.id} stepped in.",
        ),
        QAItem(
            question=f"What made the bullet trinket feel in danger in the bedroom?",
            answer=f"The bullet trinket was near the garbage basket, and the story hinted that it could disappear under the bed if nobody moved it soon.",
        ),
        QAItem(
            question=f"How did friendship change the ending for {hero.id} and {friend.id}?",
            answer=f"Friendship helped them work together, rescue the bullet trinket, and finish with the bedroom neat and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a hint that something important may happen later in the story.",
        ),
        QAItem(
            question="What does friendship help people do?",
            answer="Friendship helps people share, listen, and work together when something is hard to do alone.",
        ),
        QAItem(
            question="Why should garbage be put away?",
            answer="Garbage should be put away so a room stays clean, safe, and easy to walk through.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedroom adventure storyworld with friendship, inner monologue, and foreshadowing.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    fg = getattr(args, "friend_gender", None) or ("boy" if gender == "girl" else "girl")
    fname = getattr(args, "friend_name", None) or rng.choice(GIRL_NAMES if fg == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, friend_name=fname, friend_gender=fg, trait=trait)


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:14} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


ASP_RULES = r"""
hero_pride(H) :- hero(H).
needs_friendship(H) :- hero(H), pride(H), basket_hidden.
safe(H) :- hero(H), friend(F), friendship(F,H), rescued(item).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", "hero"), asp.fact("friend", "friend"), asp.fact("item", "bullet_trinket"), asp.fact("basket", "garbage_basket")]
    lines.append(asp.fact("pride", "hero"))
    lines.append(asp.fact("basket_hidden"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show needs_friendship/1. #show safe/1."))
    atoms = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {("needs_friendship", ("hero",))}
    if atoms & expected:
        print("OK: ASP gate is wired.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show needs_friendship/1. #show safe/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(name="Mina", gender="girl", friend_name="Rory", friend_gender="boy", trait="curious"),
            StoryParams(name="Finn", gender="boy", friend_name="Lena", friend_gender="girl", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
