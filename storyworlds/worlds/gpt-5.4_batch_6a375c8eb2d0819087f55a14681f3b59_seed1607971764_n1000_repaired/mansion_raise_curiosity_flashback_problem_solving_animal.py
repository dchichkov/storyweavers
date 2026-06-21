#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mansion_raise_curiosity_flashback_problem_solving_animal.py
======================================================================================

A standalone story world for a gentle animal tale about curiosity in an old
mansion, a remembered lesson, and a problem solved by raising a rescue platform
the sensible way.

Premise
-------
A small animal sees or hears something odd at an old mansion and follows that
curiosity inside. There, a younger animal is stuck high above the floor. The
hero first feels the pull to act quickly, then remembers an older family
member's advice in a flashback: when something is too high, stop, look around,
and use the room to raise help safely. The children-sized animal characters then
solve the problem with fitting objects from the room and bring the frightened
little one down.

Run it
------
    python storyworlds/worlds/gpt-5.4/mansion_raise_curiosity_flashback_problem_solving_animal.py
    python storyworlds/worlds/gpt-5.4/mansion_raise_curiosity_flashback_problem_solving_animal.py --room kitchen --stranded kitten
    python storyworlds/worlds/gpt-5.4/mansion_raise_curiosity_flashback_problem_solving_animal.py --room library --solution stool_lift
    python storyworlds/worlds/gpt-5.4/mansion_raise_curiosity_flashback_problem_solving_animal.py --all
    python storyworlds/worlds/gpt-5.4/mansion_raise_curiosity_flashback_problem_solving_animal.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mansion_raise_curiosity_flashback_problem_solving_animal.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse_girl", "rabbit_girl", "squirrel_girl", "otter_girl", "girl"}
        male = {"mouse_boy", "rabbit_boy", "squirrel_boy", "otter_boy", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Room:
    id: str
    label: str
    clue: str
    perch: str
    affordances: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Stranded:
    id: str
    label: str
    phrase: str
    voice: str
    perch_detail: str
    reason: str
    height: int
    light: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Solution:
    id: str
    label: str
    needs: set[str]
    power: int
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_stuck_worry(world: World) -> list[str]:
    kid = world.entities.get("little_one")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if kid is None or hero is None or friend is None:
        return []
    if kid.meters["stuck"] < THRESHOLD:
        return []
    sig = ("stuck_worry", kid.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.memes["fear"] += 1
    hero.memes["concern"] += 1
    friend.memes["worry"] += 1
    return ["__stuck__"]


def _r_rescued_relief(world: World) -> list[str]:
    kid = world.entities.get("little_one")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if kid is None or hero is None or friend is None:
        return []
    if kid.meters["safe"] < THRESHOLD:
        return []
    sig = ("rescued_relief", kid.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.memes["fear"] = 0.0
    kid.memes["relief"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    friend.memes["relief"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck_worry", tag="emotional", apply=_r_stuck_worry),
    Rule(name="rescued_relief", tag="emotional", apply=_r_rescued_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_solution(room: Room, stranded: Stranded, solution: Solution) -> bool:
    return solution.needs.issubset(room.affordances) and solution.power >= stranded.height


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for stranded_id, stranded in STRANDED.items():
            for solution_id, solution in SOLUTIONS.items():
                if valid_solution(room, stranded, solution):
                    combos.append((room_id, stranded_id, solution_id))
    return combos


def predict_reach(world: World, stranded: Stranded, solution: Solution) -> dict:
    sim = world.copy()
    sim.facts["predicted_solution"] = solution.id
    enough = valid_solution(sim.room, stranded, solution)
    return {
        "reachable": enough,
        "height": stranded.height,
        "power": solution.power,
    }


def introduce_outside(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"One breezy afternoon, {hero.id} and {friend.id} played in the ivy near an old mansion."
    )
    world.say(
        f"{hero.id} was the sort of little {hero.label} who noticed every odd flutter, glimmer, and whisper."
    )
    hero.memes["curiosity"] += 1


def notice_clue(world: World, hero: Entity, room: Room) -> None:
    world.say(
        f"From a cracked window came {room.clue}. At once, {hero.id}'s curiosity rose higher than the ivy."
    )
    world.facts["curiosity_trigger"] = room.clue


def step_inside(world: World, hero: Entity, friend: Entity, room: Room) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'"Let us only peek," said {friend.id}. Together they padded into the mansion and reached the {room.label}.'
    )
    world.say(
        f"The room was big and still, with dust dancing where the late light slanted in."
    )


def discover_problem(world: World, hero: Entity, friend: Entity, stranded: Stranded, room: Room) -> None:
    little = world.get("little_one")
    little.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then they heard {stranded.voice}. {little.id}, {stranded.phrase}, was stranded on {room.perch} {stranded.perch_detail}."
    )
    world.say(
        f"{little.id} had gone there because {stranded.reason}, and now {little.pronoun()} did not dare climb back down."
    )


def first_try(world: World, hero: Entity, stranded: Stranded) -> None:
    hero.meters["jump_attempt"] += 1
    world.say(
        f"{hero.id} stretched up on tiptoe and gave one hopeful hop, but {hero.pronoun('possessive')} paws still could not reach."
    )
    if stranded.height >= 3:
        world.say(
            "The perch was simply too high for one brave leap."
        )


def flashback(world: World, hero: Entity) -> None:
    hero.memes["remembering"] += 1
    elder = world.facts["elder_name"]
    elder_kind = world.facts["elder_kind"]
    world.say(
        f"Then a warm memory came back to {hero.id} like a little lantern in the mind."
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered how {elder}, the wise old {elder_kind}, once said, "
        f'"When something is too high, do not flurry. Stop, look around, and use what is steady to raise help safely."'
    )


def plan(world: World, hero: Entity, friend: Entity, stranded: Stranded, solution: Solution) -> None:
    pred = predict_reach(world, stranded, solution)
    world.facts["predicted_reachable"] = pred["reachable"]
    world.facts["predicted_height"] = pred["height"]
    world.facts["predicted_power"] = pred["power"]
    hero.memes["focus"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"I know," said {hero.id}. "We do not need a bigger jump. We need a better plan."'
    )
    world.say(
        f"{hero.id} looked around the room and chose {solution.label}."
    )


def solve(world: World, hero: Entity, friend: Entity, stranded: Stranded, solution: Solution) -> None:
    little = world.get("little_one")
    if not valid_solution(world.room, stranded, solution):
        raise StoryError(explain_rejection(ROOMS[world.room.id], stranded, solution))
    world.facts["used_solution"] = solution.id
    hero.meters["problem_solved"] += 1
    little.meters["stuck"] = 0.0
    little.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(solution.action.format(hero=hero.id, friend=friend.id, little=little.id, perch=world.room.perch))
    world.say(
        f"Soon {little.id} was tucked safely against the floor instead of trembling up high."
    )


def ending(world: World, hero: Entity, friend: Entity, stranded: Stranded) -> None:
    little = world.get("little_one")
    world.say(
        f'{little.id} gave a tiny happy sound. "Thank you," {little.pronoun()} whispered.'
    )
    world.say(
        f"{hero.id} smiled, and {friend.id} touched shoulders with {hero.pronoun('object')}."
    )
    world.say(
        f"When they stepped back out of the mansion, the evening air felt soft and brave. "
        f"{hero.id} was still curious about the big old house, but now {hero.pronoun()} knew curiosity shone brightest when it walked beside careful thinking."
    )


ROOMS = {
    "library": Room(
        id="library",
        label="library",
        clue="a thin peeping sound above the books",
        perch="the top of a picture ledge",
        affordances={"ladder", "blanket"},
        tags={"library", "mansion"},
    ),
    "kitchen": Room(
        id="kitchen",
        label="kitchen",
        clue="a nervous mew by the copper pots",
        perch="the high pantry shelf",
        affordances={"basket", "cord", "stool"},
        tags={"kitchen", "mansion"},
    ),
    "music_room": Room(
        id="music_room",
        label="music room",
        clue="a frightened squeak near the tall piano",
        perch="the carved mantel",
        affordances={"bench", "cushions"},
        tags={"music", "mansion"},
    ),
}

STRANDED = {
    "sparrow": Stranded(
        id="sparrow",
        label="sparrow chick",
        phrase="a fluffed-up sparrow chick",
        voice="a peep-peep-peep from overhead",
        perch_detail="with one wing pressed close",
        reason="it had chased a dancing speck of light",
        height=2,
        light=True,
        tags={"bird", "high_place"},
    ),
    "mouse": Stranded(
        id="mouse",
        label="mouse pup",
        phrase="a tiny mouse pup",
        voice="a small squeaky call from the shadows",
        perch_detail="with its tail curled tight",
        reason="it had scampered after the smell of crumbs",
        height=2,
        tags={"mouse", "high_place"},
    ),
    "kitten": Stranded(
        id="kitten",
        label="kitten",
        phrase="a soot-smudged kitten",
        voice="a wavering little mew from above",
        perch_detail="with its paws tucked under",
        reason="it had followed a fluttering moth",
        height=3,
        tags={"cat", "high_place"},
    ),
}

SOLUTIONS = {
    "blanket_hammock": Solution(
        id="blanket_hammock",
        label="the rolling ladder and a folded blanket",
        needs={"ladder", "blanket"},
        power=3,
        action="{hero} and {friend} dragged the rolling ladder beneath {perch}, tied the folded blanket across two rungs like a soft hammock, and raised it little by little until {little} could step into it.",
        qa_text="They used the rolling ladder and a folded blanket to raise a soft hammock until the little one could step into it.",
        tags={"ladder", "blanket", "problem_solving"},
    ),
    "basket_lift": Solution(
        id="basket_lift",
        label="a bread basket, a cord, and the sturdy stool",
        needs={"basket", "cord", "stool"},
        power=3,
        action="{hero} climbed onto the sturdy stool while {friend} held it still, and together they looped the cord through the basket handle and raised the basket up to {little}.",
        qa_text="They stood on the stool and used a cord to raise a basket up to the little one.",
        tags={"basket", "stool", "problem_solving"},
    ),
    "cushion_steps": Solution(
        id="cushion_steps",
        label="the piano bench and a pile of sofa cushions",
        needs={"bench", "cushions"},
        power=2,
        action="{hero} and {friend} pushed the piano bench near {perch}, stacked the cushions into wide soft steps, and raised a safe little staircase almost to the top.",
        qa_text="They pushed the piano bench over and made cushion steps that raised a safe path to the perch.",
        tags={"cushions", "bench", "problem_solving"},
    ),
}

GIRL_NAMES = ["Pip", "Mimi", "Tansy", "Nell", "Daisy", "Hazel"]
BOY_NAMES = ["Pico", "Moss", "Bram", "Toby", "Nibbles", "Jasper"]
HERO_SPECIES = [
    ("squirrel", "squirrel_girl", "squirrel_boy"),
    ("rabbit", "rabbit_girl", "rabbit_boy"),
    ("mouse", "mouse_girl", "mouse_boy"),
]
FRIEND_SPECIES = [
    ("hedgehog", "hedgehog", "hedgehog"),
    ("otter", "otter_girl", "otter_boy"),
    ("mole", "mole", "mole"),
]
ELDERS = [
    ("Grandmother Fern", "tortoise"),
    ("Aunt Willow", "owl"),
    ("Old Bramble", "badger"),
]

KNOWLEDGE = {
    "mansion": [
        (
            "What is a mansion?",
            "A mansion is a very big house with many rooms. Old mansions can feel echoey because sounds bounce around inside them."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to look closer, ask questions, and find out more. It can help you learn when you stay thoughtful and careful."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a memory from earlier that comes back during the story. It can help a character understand what to do next."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong, thinking about what tools you have, and trying a sensible plan. Good problem solving is calm, careful, and step by step."
        )
    ],
    "ladder": [
        (
            "What does a ladder help you do?",
            "A ladder helps you reach a high place safely by giving you steady steps. It works best when someone uses it carefully."
        )
    ],
    "basket": [
        (
            "How can a basket help in a rescue?",
            "A basket can hold something gently while it is lifted or carried. In a rescue, a soft basket can make a little animal feel safer."
        )
    ],
    "cushions": [
        (
            "Why are cushions useful for a gentle rescue?",
            "Cushions are soft, so they can make a safer place to climb or land. They are helpful when someone small is scared and needs a gentle path."
        )
    ],
    "kitten": [
        (
            "Why do kittens climb into tricky places?",
            "Kittens are curious and like to chase movement, smells, and fluttering things. Sometimes that curiosity takes them somewhere hard to get down from."
        )
    ],
    "bird": [
        (
            "Why might a little bird be scared high up indoors?",
            "A little bird can feel trapped if it is high up in a strange room with no easy branch to hop to. Big echoes and smooth walls can make climbing down hard."
        )
    ],
    "mouse": [
        (
            "Why might a tiny mouse get stuck above the floor?",
            "A tiny mouse may scamper up after food or a smell and then feel frightened about climbing back down. Small bodies can be brave and scared at the same time."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "mansion",
    "curiosity",
    "flashback",
    "problem_solving",
    "ladder",
    "basket",
    "cushions",
    "kitten",
    "bird",
    "mouse",
]


@dataclass
class StoryParams:
    room: str
    stranded: str
    solution: str
    hero_name: str
    hero_gender: str
    hero_species: str
    friend_name: str
    friend_gender: str
    friend_species: str
    elder_name: str
    elder_kind: str
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def _hero_type(species: str, gender: str) -> str:
    for label, female_type, male_type in HERO_SPECIES:
        if label == species:
            return female_type if gender == "girl" else male_type
    return species


def _friend_type(species: str, gender: str) -> str:
    for label, female_type, male_type in FRIEND_SPECIES:
        if label == species:
            return female_type if gender == "girl" else male_type
    return species


def explain_rejection(room: Room, stranded: Stranded, solution: Solution) -> str:
    if not solution.needs.issubset(room.affordances):
        missing = sorted(solution.needs - room.affordances)
        return (
            f"(No story: {room.label} does not provide what {solution.label} needs. "
            f"Missing: {', '.join(missing)}.)"
        )
    return (
        f"(No story: {solution.label} cannot reach {stranded.phrase}. "
        f"The little one is too high for that plan.)"
    )


def tell(
    room: Room,
    stranded: Stranded,
    solution: Solution,
    *,
    hero_name: str,
    hero_gender: str,
    hero_species: str,
    friend_name: str,
    friend_gender: str,
    friend_species: str,
    elder_name: str,
    elder_kind: str,
) -> World:
    world = World(room)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=_hero_type(hero_species, hero_gender),
            label=hero_species,
            role="hero",
            attrs={"gender": hero_gender, "species": hero_species},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=_friend_type(friend_species, friend_gender),
            label=friend_species,
            role="friend",
            attrs={"gender": friend_gender, "species": friend_species},
        )
    )
    little = world.add(
        Entity(
            id=stranded.label.title(),
            kind="character",
            type="little_animal",
            label=stranded.label,
            role="little_one",
            attrs={"stranded_id": stranded.id},
        )
    )
    world.facts["elder_name"] = elder_name
    world.facts["elder_kind"] = elder_kind
    world.facts["room"] = room
    world.facts["stranded_cfg"] = stranded
    world.facts["solution_cfg"] = solution
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["little_one"] = little

    introduce_outside(world, hero, friend)
    notice_clue(world, hero, room)
    step_inside(world, hero, friend, room)

    world.para()
    discover_problem(world, hero, friend, stranded, room)
    first_try(world, hero, stranded)

    world.para()
    flashback(world, hero)
    plan(world, hero, friend, stranded, solution)
    solve(world, hero, friend, stranded, solution)

    world.para()
    ending(world, hero, friend, stranded)

    world.facts.update(
        rescued=little.meters["safe"] >= THRESHOLD,
        scared_at_first=little.memes["relief"] >= THRESHOLD or friend.memes["worry"] >= THRESHOLD,
        used_flashback=hero.memes["remembering"] >= THRESHOLD,
        curious=hero.memes["curiosity"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    room = world.facts["room"]
    stranded = world.facts["stranded_cfg"]
    return [
        f'Write an Animal Story for a 3-to-5-year-old about a curious {hero.label} who explores a mansion and helps a frightened little animal.',
        f"Tell a gentle story where {hero.id} follows a clue into the {room.label}, has a flashback to an elder's advice, and solves the problem of rescuing {stranded.phrase}.",
        f'Write a story that uses the words "mansion" and "raise" and shows curiosity leading to careful problem solving instead of a wild jump.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    little = world.facts["little_one"]
    room = world.facts["room"]
    stranded = world.facts["stranded_cfg"]
    solution = world.facts["solution_cfg"]
    elder_name = world.facts["elder_name"]
    elder_kind = world.facts["elder_kind"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a curious little {hero.label}, and {friend.id}, {hero.pronoun('possessive')} friend. Together they explore the old mansion and help {little.id}."
        ),
        (
            "Why did they go into the mansion?",
            f"They heard {room.clue}, and {hero.id} wanted to find out what it was. Curiosity pulled them inside, but it also led them to the little one who needed help."
        ),
        (
            f"Who was stuck in the {room.label}?",
            f"{little.id}, {stranded.phrase}, was stuck on {room.perch} {stranded.perch_detail}. {little.pronoun().capitalize()} had gone up there because {stranded.reason} and then felt too scared to come down."
        ),
        (
            f"What memory helped {hero.id} solve the problem?",
            f"{hero.id} had a flashback to advice from {elder_name}, the old {elder_kind}. The memory reminded {hero.pronoun('object')} not to leap wildly, but to stop, look around, and raise help safely."
        ),
        (
            f"How did {hero.id} and {friend.id} rescue {little.id}?",
            f"{solution.qa_text} That plan worked because the room had the right sturdy things and the rescue could reach high enough."
        ),
        (
            "How did the story end?",
            f"{little.id} was safely back on the floor and no longer afraid. When they walked out of the mansion, {hero.id} had learned that curiosity is brightest when careful thinking walks beside it."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    stranded = world.facts["stranded_cfg"]
    solution = world.facts["solution_cfg"]
    tags = {"mansion", "curiosity", "flashback", "problem_solving"}
    tags |= solution.tags
    if stranded.id == "kitten":
        tags.add("kitten")
    elif stranded.id == "sparrow":
        tags.add("bird")
    elif stranded.id == "mouse":
        tags.add("mouse")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:16} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="library",
        stranded="sparrow",
        solution="blanket_hammock",
        hero_name="Pip",
        hero_gender="girl",
        hero_species="squirrel",
        friend_name="Moss",
        friend_gender="boy",
        friend_species="mole",
        elder_name="Grandmother Fern",
        elder_kind="tortoise",
        seed=None,
    ),
    StoryParams(
        room="kitchen",
        stranded="kitten",
        solution="basket_lift",
        hero_name="Bram",
        hero_gender="boy",
        hero_species="rabbit",
        friend_name="Hazel",
        friend_gender="girl",
        friend_species="hedgehog",
        elder_name="Aunt Willow",
        elder_kind="owl",
        seed=None,
    ),
    StoryParams(
        room="music_room",
        stranded="mouse",
        solution="cushion_steps",
        hero_name="Mimi",
        hero_gender="girl",
        hero_species="mouse",
        friend_name="Toby",
        friend_gender="boy",
        friend_species="otter",
        elder_name="Old Bramble",
        elder_kind="badger",
        seed=None,
    ),
]


ASP_RULES = r"""
valid(Room, Stranded, Solution) :-
    room(Room), stranded(Stranded), solution(Solution),
    enough_power(Solution, Stranded),
    needs_met(Room, Solution).

needs_met(Room, Solution) :- solution(Solution), room(Room), not missing_need(Room, Solution).
missing_need(Room, Solution) :- requires(Solution, Need), not has(Room, Need).

enough_power(Solution, Stranded) :- power(Solution, P), height(Stranded, H), P >= H.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for affordance in sorted(room.affordances):
            lines.append(asp.fact("has", room_id, affordance))
    for stranded_id, stranded in STRANDED.items():
        lines.append(asp.fact("stranded", stranded_id))
        lines.append(asp.fact("height", stranded_id, stranded.height))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        lines.append(asp.fact("power", solution_id, solution.power))
        for need in sorted(solution.needs):
            lines.append(asp.fact("requires", solution_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke-tested on 20 seeds.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: curiosity leads into a mansion, a flashback guides the plan, and careful problem solving rescues a little animal."
    )
    ap.add_argument("--room", choices=sorted(ROOMS))
    ap.add_argument("--stranded", choices=sorted(STRANDED))
    ap.add_argument("--solution", choices=sorted(SOLUTIONS))
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-species", choices=sorted(label for label, *_ in HERO_SPECIES))
    ap.add_argument("--friend-species", choices=sorted(label for label, *_ in FRIEND_SPECIES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (room, stranded, solution) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.stranded and args.solution:
        room = ROOMS[args.room]
        stranded = STRANDED[args.stranded]
        solution = SOLUTIONS[args.solution]
        if not valid_solution(room, stranded, solution):
            raise StoryError(explain_rejection(room, stranded, solution))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.stranded is None or combo[1] == args.stranded)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, stranded_id, solution_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_species = args.hero_species or rng.choice(sorted(label for label, *_ in HERO_SPECIES))
    friend_species = args.friend_species or rng.choice(sorted(label for label, *_ in FRIEND_SPECIES))
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    elder_name, elder_kind = rng.choice(ELDERS)
    return StoryParams(
        room=room_id,
        stranded=stranded_id,
        solution=solution_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_species=hero_species,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_species=friend_species,
        elder_name=elder_name,
        elder_kind=elder_kind,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.stranded not in STRANDED:
        raise StoryError(f"(Unknown stranded animal: {params.stranded})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    room = ROOMS[params.room]
    stranded = STRANDED[params.stranded]
    solution = SOLUTIONS[params.solution]
    if not valid_solution(room, stranded, solution):
        raise StoryError(explain_rejection(room, stranded, solution))

    world = tell(
        room=room,
        stranded=stranded,
        solution=solution,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_species=params.hero_species,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        friend_species=params.friend_species,
        elder_name=params.elder_name,
        elder_kind=params.elder_kind,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (room, stranded, solution) combos:\n")
        for room_id, stranded_id, solution_id in combos:
            print(f"  {room_id:10} {stranded_id:8} {solution_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} rescues a {p.stranded} in the {p.room} with {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
