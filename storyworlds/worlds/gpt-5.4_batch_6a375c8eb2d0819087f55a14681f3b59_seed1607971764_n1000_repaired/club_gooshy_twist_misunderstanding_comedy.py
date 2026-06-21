#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py
=======================================================================

A standalone story world about a child who joins a club, mishears what the
leader asked everyone to bring, and proudly arrives with something gooshy.
The misunderstanding creates a comic problem, then a twist: the silly gooshy
thing turns out to be exactly what the club needs.

Run it
------
    python storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py
    python storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py --club puppet --item jelly
    python storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py --club sculpture --item slime
    python storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py --all
    python storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/club_gooshy_twist_misunderstanding_comedy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "woman", "mother", "teacher"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Club:
    id: str
    label: str
    room: str
    project: str
    project_label: str
    needs: set[str] = field(default_factory=set)
    tolerance: int = 0
    problem_line: str = ""
    use_line: str = ""
    ending_line: str = ""
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
class GooshyItem:
    id: str
    label: str
    phrase: str
    container: str
    textures: set[str] = field(default_factory=set)
    drippy: int = 0
    wobble_word: str = ""
    reveal_line: str = ""
    use_name: str = ""
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
class Misunderstanding:
    id: str
    actual: str
    heard: str
    source: str
    retell: str
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
class WalkStyle:
    id: str
    verb: str
    careful: bool
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
    def __init__(self) -> None:
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
        clone = World()
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


def _r_splat(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    hero = world.get("hero")
    friend = world.get("friend")
    table = world.get("table")
    if item.meters["opened"] < THRESHOLD:
        return out
    if item.attrs.get("drippy", 0) <= 0:
        return out
    if hero.memes["bouncy"] < THRESHOLD:
        return out
    sig = ("splat", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    table.meters["mess"] += 1
    item.meters["spilled"] += 1
    hero.memes["embarrassment"] += 1
    friend.memes["surprise"] += 1
    out.append("__splat__")
    return out


def _r_fix_project(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    project = world.get("project")
    hero = world.get("hero")
    leader = world.get("leader")
    needs = set(project.attrs.get("needs", set()))
    textures = set(item.attrs.get("textures", set()))
    if item.meters["opened"] < THRESHOLD:
        return out
    if not (needs & textures):
        return out
    sig = ("fix", project.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["fixed"] += 1
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    leader.memes["relief"] += 1
    leader.memes["amusement"] += 1
    out.append("__fixed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="splat", tag="physical", apply=_r_splat),
    Rule(name="fix_project", tag="physical", apply=_r_fix_project),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def fits_need(club: Club, item: GooshyItem) -> bool:
    return bool(set(club.needs) & set(item.textures))


def reasonable_combo(club: Club, item: GooshyItem) -> bool:
    return fits_need(club, item) and item.drippy <= club.tolerance


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for club_id, club in CLUBS.items():
        for item_id, item in ITEMS.items():
            if not reasonable_combo(club, item):
                continue
            for mis_id in MISUNDERSTANDINGS:
                combos.append((club_id, item_id, mis_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    item = ITEMS[params.item]
    return "splat_success" if item.drippy > 0 and params.walk == "skip" else "tidy_success"


def explain_rejection(club: Club, item: GooshyItem) -> str:
    if not fits_need(club, item):
        want = " or ".join(sorted(club.needs))
        have = ", ".join(sorted(item.textures))
        return (
            f"(No story: {item.phrase} is gooshy, but it does not give the {club.label} "
            f"the kind of texture this project needs. The club needs something {want}; "
            f"this item only gives {have}.)"
        )
    return (
        f"(No story: {item.phrase} would be too messy for the {club.label}. "
        f"It drips more than this club can handle before the twist can feel funny.)"
    )


def predict_splat(world: World) -> bool:
    sim = world.copy()
    sim.get("item").meters["opened"] += 1
    propagate(sim, narrate=False)
    return sim.get("table").meters["mess"] >= THRESHOLD


def predict_fix(world: World) -> bool:
    sim = world.copy()
    sim.get("item").meters["opened"] += 1
    propagate(sim, narrate=False)
    return sim.get("project").meters["fixed"] >= THRESHOLD


def opening_setup(world: World, hero: Entity, friend: Entity, leader: Entity,
                  club: Club, mis: Misunderstanding, item: GooshyItem) -> None:
    hero.memes["excitement"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"After school, {hero.id} hurried to the {club.label} in {club.room}. "
        f"The club was building {club.project}."
    )
    world.say(
        f"At the end of the last meeting, {leader.id} had called out, "
        f'"{mis.actual}!" But a {mis.source} swallowed the middle of the sentence, '
        f"and {hero.id} heard, \"{mis.heard}.\""
    )
    world.say(
        f"So {hero.id} arrived proudly carrying {item.phrase} in {item.container}. "
        f"To {hero.pronoun('object')}, it seemed obvious that every good club needed something gooshy."
    )


def friend_checks(world: World, hero: Entity, friend: Entity, club: Club, item: GooshyItem) -> None:
    will_splat = predict_splat(world)
    world.say(
        f'{friend.id} blinked at the bowl in {hero.id}\'s hands. "Why did you bring {item.label} to {club.label}?" '
        f"{friend.pronoun()} whispered."
    )
    if will_splat:
        friend.memes["worry"] += 1
        world.say(
            f'"Because gooshy was the homework," {hero.id} said. '
            f'{friend.id} looked at the wobbling {item.label} and took one careful step backward.'
        )
    else:
        world.say(
            f'"Because gooshy was the homework," {hero.id} said. '
            f'{friend.id} tried not to laugh, but one giggle escaped anyway.'
        )


def club_problem(world: World, leader: Entity, club: Club) -> None:
    world.say(
        f"Inside the room, the project was not going well. {club.problem_line}"
    )


def reveal_item(world: World, hero: Entity, friend: Entity, item: GooshyItem, walk: WalkStyle) -> None:
    if walk.careful:
        world.say(
            f"{hero.id} {walk.verb} to the table and lifted the lid. "
            f"{item.reveal_line}"
        )
    else:
        hero.memes["bouncy"] += 1
        world.say(
            f"{hero.id} could not help {walk.verb} the last two steps. "
            f"When {hero.pronoun()} lifted the lid, {item.reveal_line}"
        )
    world.get("item").meters["opened"] += 1
    propagate(world, narrate=False)


def splat_or_not(world: World, hero: Entity, friend: Entity, item: GooshyItem) -> None:
    table = world.get("table")
    if table.meters["mess"] >= THRESHOLD:
        world.say(
            f"Plop. A soft gooshy blob slid onto the table and wiggled toward the project. "
            f"{hero.id}'s ears turned warm, and {friend.id} made a tiny squeak."
        )
    else:
        world.say(
            f"The room went very still for one beat while everyone stared at the shiny gooshy surprise."
        )


def twist_solution(world: World, leader: Entity, hero: Entity, club: Club, item: GooshyItem) -> None:
    project = world.get("project")
    if project.meters["fixed"] < THRESHOLD:
        raise StoryError("(World error: the chosen gooshy item did not solve the club problem.)")
    if world.get("table").meters["mess"] >= THRESHOLD:
        world.say(
            f"Then {leader.id}'s face changed. {leader.pronoun().capitalize()} scooped up the runaway {item.use_name} with a craft stick and laughed. "
            f'"Wait," {leader.pronoun()} said. "{club.use_line}"'
        )
    else:
        world.say(
            f"Then {leader.id}'s face changed. {leader.pronoun().capitalize()} leaned in and laughed softly. "
            f'"Wait," {leader.pronoun()} said. "{club.use_line}"'
        )
    world.say(
        f"In one funny little twist, the mistaken snack became exactly the thing the club had been missing."
    )
    hero.memes["embarrassment"] = 0.0
    hero.memes["joy"] += 1


def clear_misunderstanding(world: World, leader: Entity, hero: Entity, friend: Entity, mis: Misunderstanding) -> None:
    friend.memes["joy"] += 1
    world.say(
        f'{hero.id} blinked. "{mis.heard}?" {hero.pronoun()} asked.'
    )
    world.say(
        f'{leader.id} laughed so hard {leader.pronoun()} had to put a hand on the table. '
        f'"No, I said, \'{mis.actual}.\' But I am very glad you heard the silly version."'
    )
    world.say(
        f"Now everybody understood the misunderstanding, and instead of feeling foolish, {hero.id} felt wonderfully useful."
    )


def ending(world: World, hero: Entity, friend: Entity, club: Club, item: GooshyItem) -> None:
    if world.get("table").meters["mess"] >= THRESHOLD:
        world.say(
            f"{friend.id} wiped the table while still giggling, and {hero.id} helped shape the last shiny bits into place."
        )
    else:
        world.say(
            f"{friend.id} leaned close and grinned at {hero.id} as the project finally looked right."
        )
    world.say(
        f"Soon {club.ending_line}"
    )
    world.say(
        f"When the meeting ended, someone had taped a fresh little sign by the door: "
        f'"{club.label} -- and maybe the Gooshy Club too." '
        f"{hero.id} walked home smiling."
    )


def tell(club: Club, item_cfg: GooshyItem, mis: Misunderstanding, walk: WalkStyle,
         hero_name: str = "Mia", hero_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         leader_name: str = "Ms. Nia", leader_gender: str = "teacher") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["eager"],
        attrs={"walk": walk.id},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["helpful"],
        attrs={},
    ))
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=["kind"],
        attrs={},
    ))
    world.add(Entity(
        id="table",
        type="table",
        label="the club table",
        attrs={},
    ))
    world.add(Entity(
        id="project",
        type="project",
        label=club.project_label,
        attrs={"needs": set(club.needs)},
    ))
    world.add(Entity(
        id="item",
        type="item",
        label=item_cfg.label,
        attrs={"textures": set(item_cfg.textures), "drippy": item_cfg.drippy},
    ))

    world.facts.update(
        club=club,
        item_cfg=item_cfg,
        misunderstanding=mis,
        walk=walk,
        hero=hero,
        friend=friend,
        leader=leader,
        predicted_splat=False,
        predicted_fix=False,
    )
    world.facts["predicted_splat"] = predict_splat(world)
    world.facts["predicted_fix"] = predict_fix(world)

    opening_setup(world, hero, friend, leader, club, mis, item_cfg)
    world.para()
    friend_checks(world, hero, friend, club, item_cfg)
    club_problem(world, leader, club)
    world.para()
    reveal_item(world, hero, friend, item_cfg, walk)
    splat_or_not(world, hero, friend, item_cfg)
    twist_solution(world, leader, hero, club, item_cfg)
    world.para()
    clear_misunderstanding(world, leader, hero, friend, mis)
    ending(world, hero, friend, club, item_cfg)

    world.facts.update(
        outcome="splat_success" if world.get("table").meters["mess"] >= THRESHOLD else "tidy_success",
        mess=world.get("table").meters["mess"] >= THRESHOLD,
        fixed=world.get("project").meters["fixed"] >= THRESHOLD,
    )
    return world


CLUBS = {
    "puppet": Club(
        id="puppet",
        label="Puppet Club",
        room="the music room",
        project="a cardboard swamp for a sneezy monster puppet",
        project_label="swamp backdrop",
        needs={"wobble", "smooth"},
        tolerance=2,
        problem_line="The swamp on the backdrop looked flat and dry, and the monster puppet was supposed to rise out of something squishy and funny.",
        use_line="This wobble makes our swamp look alive.",
        ending_line="the monster puppet bobbed up from a perfect silly swamp, and the whole club clapped.",
        tags={"club", "puppet", "wobble"},
    ),
    "science": Club(
        id="science",
        label="Science Club",
        room="the bright little lab",
        project="a table of things that might be solids and might be liquids",
        project_label="wobble test",
        needs={"wobble"},
        tolerance=2,
        problem_line="The class wanted a material that would jiggle when tapped but would not pour away too quickly, and all they had was plain water and hard blocks.",
        use_line="This is perfect for our wobble test.",
        ending_line="everyone took turns tapping the tray and laughing as the sample shivered in place.",
        tags={"club", "science", "wobble"},
    ),
    "sculpture": Club(
        id="sculpture",
        label="Sculpture Club",
        room="the art room",
        project="a moon model with tiny craters",
        project_label="moon model",
        needs={"moldable"},
        tolerance=0,
        problem_line="The moon model was too stiff, so every crater looked like a poke from one bored finger instead of a real bumpy moon.",
        use_line="This soft texture lets us stamp real craters.",
        ending_line="the moon model ended up round, dimpled, and so good that even the glue bottles seemed impressed.",
        tags={"club", "art", "moon"},
    ),
}

ITEMS = {
    "jelly": GooshyItem(
        id="jelly",
        label="jelly",
        phrase="a bowl of raspberry jelly",
        container="a wobbling glass bowl",
        textures={"wobble", "smooth"},
        drippy=1,
        wobble_word="wobbled like a happy little bell",
        reveal_line="the jelly gave one brave shiver and wobbled like a tiny red hill.",
        use_name="jelly",
        tags={"jelly", "wobble", "gooshy"},
    ),
    "pudding": GooshyItem(
        id="pudding",
        label="pudding",
        phrase="a cup of chocolate pudding",
        container="a paper cup with a lid",
        textures={"wobble", "smooth"},
        drippy=2,
        wobble_word="shivered in a silky brown wobble",
        reveal_line="the pudding shivered in a silky brown wobble.",
        use_name="pudding",
        tags={"pudding", "gooshy", "wobble"},
    ),
    "dough": GooshyItem(
        id="dough",
        label="dough",
        phrase="a tin of soft salt dough",
        container="a round tin",
        textures={"moldable"},
        drippy=0,
        wobble_word="sat in one squishy lump",
        reveal_line="the dough sat there in one patient squishy lump, ready to be pressed.",
        use_name="dough",
        tags={"dough", "gooshy", "moldable"},
    ),
    "slime": GooshyItem(
        id="slime",
        label="slime",
        phrase="a tub of green slime",
        container="a plastic tub",
        textures={"sticky"},
        drippy=1,
        wobble_word="stretched in shiny strings",
        reveal_line="the slime stretched in shiny green strings that looked far too proud of themselves.",
        use_name="slime",
        tags={"slime", "sticky", "gooshy"},
    ),
}

MISUNDERSTANDINGS = {
    "echo": Misunderstanding(
        id="echo",
        actual="Bring your notebook to club",
        heard="Bring something gooshy to club",
        source="clangy hallway echo",
        retell="A hallway echo swallowed the middle of the sentence.",
        tags={"misunderstanding", "hearing"},
    ),
    "kazoo": Misunderstanding(
        id="kazoo",
        actual="Bring your folder to club",
        heard="Bring something gooshy to club",
        source="kazoo toot from the next room",
        retell="A kazoo toot chopped the sentence in half.",
        tags={"misunderstanding", "hearing"},
    ),
    "sneeze": Misunderstanding(
        id="sneeze",
        actual="Bring your ruler to club",
        heard="Bring something gooshy to club",
        source="giant sneeze from the coat hooks",
        retell="A huge sneeze blasted through the hallway right then.",
        tags={"misunderstanding", "hearing"},
    ),
}

WALKS = {
    "tiptoe": WalkStyle(
        id="tiptoe",
        verb="tiptoed",
        careful=True,
        tags={"careful"},
    ),
    "skip": WalkStyle(
        id="skip",
        verb="skipping",
        careful=False,
        tags={"bouncy"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Lucy", "Anna", "Ella"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Eli", "Finn", "Noah", "Theo"]
LEADER_NAMES = ["Ms. Nia", "Mr. Omar", "Ms. June", "Mr. Eli"]


@dataclass
class StoryParams:
    club: str
    item: str
    misunderstanding: str
    walk: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    leader: str
    leader_gender: str
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


KNOWLEDGE = {
    "club": [
        (
            "What is a club at school?",
            "A school club is a small group that meets to do something together after class. People in a club usually share the same activity or interest."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears, sees, or thinks something the wrong way. Then people mean one thing but another person believes something different."
        )
    ],
    "wobble": [
        (
            "What does wobble mean?",
            "To wobble means to shake or jiggle from side to side. Jelly wobbles because it is soft and can move without falling apart right away."
        )
    ],
    "jelly": [
        (
            "Why does jelly jiggle?",
            "Jelly jiggles because it is soft and springy. It keeps its shape a little, but it still moves when you tap it."
        )
    ],
    "pudding": [
        (
            "Why is pudding called gooshy?",
            "Pudding can feel gooshy because it is thick, soft, and smooth all at once. It is not hard like a cracker and not runny like plain water."
        )
    ],
    "dough": [
        (
            "What is dough good for?",
            "Soft dough is good for shaping and pressing because it changes form when you push it. That makes it useful for making patterns and little models."
        )
    ],
    "slime": [
        (
            "Why is slime sticky?",
            "Slime is sticky because it stretches and clings to itself and other things. That is why people play with it carefully and keep it off carpets and hair."
        )
    ],
    "careful": [
        (
            "Why does carrying something carefully help?",
            "Carrying something carefully helps keep it from tipping, splashing, or sliding out. Slow hands and slow steps make fewer messes."
        )
    ],
}
KNOWLEDGE_ORDER = ["club", "misunderstanding", "wobble", "jelly", "pudding", "dough", "slime", "careful"]


def generation_prompts(world: World) -> list[str]:
    club = world.facts["club"]
    item = world.facts["item_cfg"]
    mis = world.facts["misunderstanding"]
    hero = world.facts["hero"]
    outcome = world.facts["outcome"]
    if outcome == "splat_success":
        return [
            f'Write a funny story for a 3-to-5-year-old about a child who goes to {club.label} after hearing "{mis.heard}" by mistake and brings something gooshy.',
            f"Tell a comedy where {hero.id} proudly carries {item.phrase} to {club.label}, makes a small mess, and then discovers the mistake somehow solves the club's problem.",
            f'Write a misunderstanding story with a twist ending where the words "club" and "gooshy" both appear and the funny mistake turns useful.'
        ]
    return [
        f'Write a funny story for a 3-to-5-year-old about a child who goes to {club.label} after hearing "{mis.heard}" by mistake and brings something gooshy.',
        f"Tell a comedy where {hero.id} proudly carries {item.phrase} to {club.label}, everyone stares, and then the odd choice turns out to be exactly right.",
        f'Write a misunderstanding story with a twist ending where the words "club" and "gooshy" both appear and the silly mistake helps the whole group.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    leader = world.facts["leader"]
    club = world.facts["club"]
    item = world.facts["item_cfg"]
    mis = world.facts["misunderstanding"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who hurried to {club.label}, and about {friend.id} and {leader.id} there too. The whole story grows from what {hero.id} thought was the club homework."
        ),
        (
            f"Why did {hero.id} bring {item.label} to the club?",
            f"{hero.id} brought {item.label} because {hero.pronoun()} misheard {leader.id}. {hero.pronoun().capitalize()} heard \"{mis.heard}\" instead of \"{mis.actual},\" so the silly choice felt perfectly sensible."
        ),
        (
            f"What problem did the {club.label} have?",
            f"The club's project was not working yet. {club.problem_line} That is why the gooshy surprise mattered when it appeared."
        ),
    ]
    if world.facts["mess"]:
        qa.append(
            (
                f"What happened when {hero.id} opened the {item.label}?",
                f"A soft gooshy blob plopped onto the table and made a little mess first. That happened because {hero.id} was skipping and the {item.label} was drippy enough to slide."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} opened the {item.label}?",
                f"Everyone stared for a quiet second, but nothing spilled. {hero.id} had carried it carefully, so the funny reveal stayed tidy."
            )
        )
    qa.append(
        (
            "What was the twist in the story?",
            f"The twist was that the mistaken gooshy thing turned out to be exactly what the club needed. Even though {hero.id} had misunderstood the instructions, the odd item fixed the project instead of ruining the meeting."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the club laughing, the project finally working, and {hero.id} feeling proud instead of embarrassed. The fresh sign calling it maybe the Gooshy Club showed that the misunderstanding had become a happy joke."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"club", "misunderstanding"}
    club = world.facts["club"]
    item = world.facts["item_cfg"]
    walk = world.facts["walk"]
    tags |= set(club.tags)
    tags |= set(item.tags)
    tags |= set(walk.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {}
            for k, v in e.attrs.items():
                if isinstance(v, set):
                    shown[k] = sorted(v)
                else:
                    shown[k] = v
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        club="puppet",
        item="jelly",
        misunderstanding="echo",
        walk="skip",
        hero="Mia",
        hero_gender="girl",
        friend="Ben",
        friend_gender="boy",
        leader="Ms. Nia",
        leader_gender="teacher",
        seed=None,
    ),
    StoryParams(
        club="science",
        item="pudding",
        misunderstanding="kazoo",
        walk="tiptoe",
        hero="Leo",
        hero_gender="boy",
        friend="Ava",
        friend_gender="girl",
        leader="Mr. Omar",
        leader_gender="man",
        seed=None,
    ),
    StoryParams(
        club="sculpture",
        item="dough",
        misunderstanding="sneeze",
        walk="tiptoe",
        hero="Nora",
        hero_gender="girl",
        friend="Max",
        friend_gender="boy",
        leader="Ms. June",
        leader_gender="teacher",
        seed=None,
    ),
]


ASP_RULES = r"""
fits(C, I) :- club(C), item(I), club_need(C, T), item_texture(I, T).
valid(C, I, M) :- club(C), item(I), misunderstanding(M), fits(C, I),
                  tolerance(C, Tol), drip(I, D), D <= Tol.

splat :- chosen_item(I), chosen_walk(skip), drip(I, D), D > 0.
outcome(splat_success) :- splat.
outcome(tidy_success) :- not splat.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for club_id, club in CLUBS.items():
        lines.append(asp.fact("club", club_id))
        lines.append(asp.fact("tolerance", club_id, club.tolerance))
        for need in sorted(club.needs):
            lines.append(asp.fact("club_need", club_id, need))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("drip", item_id, item.drippy))
        for tex in sorted(item.textures):
            lines.append(asp.fact("item_texture", item_id, tex))
    for mis_id in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mis_id))
    for walk_id in WALKS:
        lines.append(asp.fact("walk", walk_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_walk", params.walk),
    ])
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: empty story.)")
    _ = format_qa(sample)
    if sample.world is None:
        raise StoryError("(Smoke test failed: missing world model.)")
    _ = dump_trace(sample.world)
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=True, qa=True, header="### smoke")
    finally:
        sys.stdout = old


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        c = set(asp_valid_combos())
        p = set(valid_combos())
        print("MISMATCH in valid combos:")
        if c - p:
            print("  only in clingo:", sorted(c - p))
        if p - c:
            print("  only in python:", sorted(p - c))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args(["--seed", str(seed)]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test passed for ordinary generation, trace, and QA.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a club misunderstanding, a gooshy mistake, and a funny twist."
    )
    ap.add_argument("--club", choices=CLUBS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--walk", choices=WALKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--leader")
    ap.add_argument("--leader-gender", choices=["teacher", "man", "woman"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.club is not None and args.club not in CLUBS:
        raise StoryError("(Unknown club.)")
    if args.item is not None and args.item not in ITEMS:
        raise StoryError("(Unknown item.)")
    if args.misunderstanding is not None and args.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("(Unknown misunderstanding.)")
    if args.walk is not None and args.walk not in WALKS:
        raise StoryError("(Unknown walk style.)")

    if args.club and args.item:
        club = CLUBS[args.club]
        item = ITEMS[args.item]
        if not reasonable_combo(club, item):
            raise StoryError(explain_rejection(club, item))

    combos = [
        c for c in valid_combos()
        if (args.club is None or c[0] == args.club)
        and (args.item is None or c[1] == args.item)
        and (args.misunderstanding is None or c[2] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    club_id, item_id, mis_id = rng.choice(sorted(combos))
    walk = args.walk or rng.choice(sorted(WALKS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    leader = args.leader or rng.choice(LEADER_NAMES)
    leader_gender = args.leader_gender or ("man" if leader.startswith("Mr.") else "teacher")

    return StoryParams(
        club=club_id,
        item=item_id,
        misunderstanding=mis_id,
        walk=walk,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        leader=leader,
        leader_gender=leader_gender,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.club not in CLUBS:
        raise StoryError("(Unknown club in params.)")
    if params.item not in ITEMS:
        raise StoryError("(Unknown item in params.)")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("(Unknown misunderstanding in params.)")
    if params.walk not in WALKS:
        raise StoryError("(Unknown walk style in params.)")
    if not reasonable_combo(CLUBS[params.club], ITEMS[params.item]):
        raise StoryError(explain_rejection(CLUBS[params.club], ITEMS[params.item]))

    world = tell(
        club=CLUBS[params.club],
        item_cfg=ITEMS[params.item],
        mis=MISUNDERSTANDINGS[params.misunderstanding],
        walk=WALKS[params.walk],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (club, item, misunderstanding) combos:\n")
        for club, item, mis in combos:
            print(f"  {club:10} {item:8} {mis}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.item} at {p.club} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
