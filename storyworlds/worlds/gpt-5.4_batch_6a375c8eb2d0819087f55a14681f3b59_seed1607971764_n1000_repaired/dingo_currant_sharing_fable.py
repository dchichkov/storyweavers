#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dingo_currant_sharing_fable.py
=========================================================

A small fable-like story world about a little dingo, a patch of currants, and
the difference between hoarding and sharing.

This world models a concrete problem instead of swapping nouns into one fixed
paragraph:

- a hungry little dingo finds ripe currants
- the currants are not easy to gather without the right helper
- the dingo chooses either to share the harvest or to hoard it
- a load that is too large for the chosen container spills
- the ending shows either fellowship and enough for all, or loss and loneliness

Run it
------
    python storyworlds/worlds/gpt-5.4/dingo_currant_sharing_fable.py
    python storyworlds/worlds/gpt-5.4/dingo_currant_sharing_fable.py --choice hoard
    python storyworlds/worlds/gpt-5.4/dingo_currant_sharing_fable.py --bush thorn_crown --helper wombat
    python storyworlds/worlds/gpt-5.4/dingo_currant_sharing_fable.py --all
    python storyworlds/worlds/gpt-5.4/dingo_currant_sharing_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dingo_currant_sharing_fable.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SHARE_PORTION = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen"}
        male = {"boy", "father"}
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
class Place:
    id: str
    label: str
    opening: str
    image: str
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
class Bush:
    id: str
    label: str
    patch_text: str
    trouble: str
    total_currants: int
    needs: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    kind: str
    label: str
    method: str
    abilities: set[str] = field(default_factory=set)
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
class Container:
    id: str
    label: str
    phrase: str
    capacity: int
    carry_text: str
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
class Choice:
    id: str
    verb: str
    vow: str
    kind_text: str
    selfish: bool
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


def helper_can_reach(bush: Bush, helper: Helper) -> bool:
    return bush.needs <= helper.abilities


def kept_load(choice: Choice, bush: Bush) -> int:
    if choice.selfish:
        return bush.total_currants
    return max(1, bush.total_currants - SHARE_PORTION)


def can_carry(choice: Choice, bush: Bush, container: Container) -> bool:
    return kept_load(choice, bush) <= container.capacity


def valid_story(bush: Bush, helper: Helper, container: Container, choice: Choice) -> bool:
    return helper_can_reach(bush, helper) and can_carry(choice, bush, container)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for bush_id, bush in BUSHES.items():
            for helper_id, helper in HELPERS.items():
                for container_id, container in CONTAINERS.items():
                    for choice_id, choice in CHOICES.items():
                        if valid_story(bush, helper, container, choice):
                            combos.append((place_id, bush_id, helper_id, container_id, choice_id))
    return combos


def explain_helper_rejection(bush: Bush, helper: Helper) -> str:
    need = ", ".join(sorted(bush.needs))
    have = ", ".join(sorted(helper.abilities))
    return (
        f"(No story: {helper.label} cannot help with {bush.label}. "
        f"That patch needs {need}, but {helper.label} only offers {have}.)"
    )


def explain_container_rejection(bush: Bush, container: Container, choice: Choice) -> str:
    return (
        f"(No story: if the dingo chooses to {choice.verb}, "
        f"{container.phrase} cannot carry enough currants from {bush.label}. "
        f"It holds {container.capacity}, but that choice leaves {kept_load(choice, bush)} to carry.)"
    )


@dataclass
class StoryParams:
    place: str
    bush: str
    helper: str
    container: str
    choice: str
    dingo_name: str
    parent_name: str
    parent_type: str
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


PLACES = {
    "creekside": Place(
        id="creekside",
        label="the creekside",
        opening="At the edge of a silver creek",
        image="dragonflies stitched blue light over the water",
        tags={"creek", "nature"},
    ),
    "red_hill": Place(
        id="red_hill",
        label="the red hill",
        opening="On a red hill under the warming sun",
        image="small stones shone like coins in the dust",
        tags={"hill", "nature"},
    ),
    "gum_grove": Place(
        id="gum_grove",
        label="the gum grove",
        opening="In the shade of the gum grove",
        image="the leaves whispered every time the breeze passed through",
        tags={"grove", "nature"},
    ),
}

BUSHES = {
    "low_patch": Bush(
        id="low_patch",
        label="the low currant patch",
        patch_text="a low patch of currant canes hung with dark, shiny fruit",
        trouble="The berries were easy to see, but they ripened in a wide ring and were quicker to gather with a friend.",
        total_currants=4,
        needs=set(),
        tags={"currant", "berries"},
    ),
    "arching_canes": Bush(
        id="arching_canes",
        label="the arching currant canes",
        patch_text="arching currant canes bent over a ditch, their fruit glimmering just out of easy reach",
        trouble="The canes bowed over the ditch, so someone had to hold them low.",
        total_currants=5,
        needs={"bend"},
        tags={"currant", "berries"},
    ),
    "thorn_crown": Bush(
        id="thorn_crown",
        label="the thorn-crowned currant bush",
        patch_text="a thorn-crowned currant bush tucked its bright fruit high inside a prickly ring",
        trouble="The sweetest currants hid high behind thorns, and they would only fall if someone reached above and shook them free.",
        total_currants=6,
        needs={"reach", "shake"},
        tags={"currant", "thorns", "berries"},
    ),
}

HELPERS = {
    "wombat": Helper(
        id="wombat",
        kind="animal",
        label="Woma the wombat",
        method="braced his stout back against the earth and pushed the canes down where little paws could reach",
        abilities={"bend"},
        tags={"wombat", "help"},
    ),
    "cockatoo": Helper(
        id="cockatoo",
        kind="animal",
        label="Kiri the cockatoo",
        method="fluttered above the bush and shook the high twigs until currants pattered down like small purple beads",
        abilities={"reach", "shake"},
        tags={"cockatoo", "help"},
    ),
    "kangaroo": Helper(
        id="kangaroo",
        kind="animal",
        label="Roo the kangaroo",
        method="stood tall, hooked a paw over the canes, and bent the fruiting stems toward the ground",
        abilities={"bend", "reach"},
        tags={"kangaroo", "help"},
    ),
}

CONTAINERS = {
    "leaf_cup": Container(
        id="leaf_cup",
        label="leaf cup",
        phrase="a folded leaf cup",
        capacity=2,
        carry_text="The leaf cup was neat and green, but it could hold only a few berries before its sides sagged.",
        tags={"leaf", "container"},
    ),
    "reed_basket": Container(
        id="reed_basket",
        label="reed basket",
        phrase="a tiny reed basket",
        capacity=4,
        carry_text="The reed basket was light and tidy, good for a modest gathering.",
        tags={"basket", "container"},
    ),
    "bark_basket": Container(
        id="bark_basket",
        label="bark basket",
        phrase="a bark basket with a plaited handle",
        capacity=6,
        carry_text="The bark basket was broad and steady, made to carry a fuller harvest.",
        tags={"basket", "container"},
    ),
}

CHOICES = {
    "share": Choice(
        id="share",
        verb="share",
        vow="If a friend helps me, we shall both taste the fruit.",
        kind_text="A shared berry tastes sweeter because no one eats it alone.",
        selfish=False,
        tags={"sharing", "kindness"},
    ),
    "hoard": Choice(
        id="hoard",
        verb="keep everything for himself",
        vow="If I gather the fruit, every currant shall be mine alone.",
        kind_text="A greedy paw closes so tightly that it cannot hold what matters.",
        selfish=True,
        tags={"selfishness", "sharing"},
    ),
}

DINGO_NAMES = ["Daru", "Miro", "Tali", "Jirra", "Naru", "Piri"]
PARENT_NAMES = ["Old Ember", "Soft Step", "Red Tail", "Moon Ear"]


def introduce(world: World, dingo: Entity, place: Place, bush: Bush, container: Container) -> None:
    dingo.meters["hunger"] = 2.0
    dingo.memes["hope"] = 1.0
    world.say(
        f"{place.opening}, a little dingo named {dingo.id} trotted out alone. "
        f"{place.image}."
    )
    world.say(
        f"Before long, {dingo.id} found {bush.patch_text}. {container.carry_text}"
    )
    world.say(
        f"{dingo.id}'s stomach gave a small hungry flutter, for currant was {dingo.pronoun('possessive')} favorite woodland treat."
    )


def discover_problem(world: World, dingo: Entity, bush: Bush, helper_cfg: Helper, container: Container, choice: Choice) -> None:
    dingo.memes["greed"] = 1.0 if choice.selfish else 0.0
    dingo.memes["generosity"] = 1.0 if not choice.selfish else 0.0
    world.say(bush.trouble)
    world.say(
        f"{dingo.id} set down {container.phrase} and whispered, "
        f'"{choice.vow}"'
    )
    if choice.selfish:
        world.say(
            f"Yet even while saying so, the little dingo kept glancing from the bush to the basket and thinking about one full mouth after another."
        )
    else:
        world.say(
            f"The thought of sharing made the lonely morning feel warmer already."
        )
    world.facts["planned_keep"] = kept_load(choice, bush)
    world.facts["container_capacity"] = container.capacity
    world.facts["gather_possible"] = helper_can_reach(bush, helper_cfg)


def meet_helper(world: World, dingo: Entity, helper_ent: Entity, helper_cfg: Helper) -> None:
    helper_ent.meters["hunger"] = 1.0
    helper_ent.memes["trust"] = 1.0
    world.say(
        f"Just then {helper_cfg.label} came along the path, saw the eager little dingo, and asked what treasure had been found."
    )
    world.say(
        f'{dingo.id} pointed with a quick paw. "{helper_ent.id}, would you help me gather the currants?"'
    )


def gather(world: World, dingo: Entity, helper_ent: Entity, bush: Bush, helper_cfg: Helper) -> None:
    helper_ent.memes["helpfulness"] = 1.0
    dingo.memes["owed_help"] = 1.0
    world.say(
        f"{helper_cfg.label} agreed and {helper_cfg.method}"
    )
    dingo.meters["currants_owned"] = float(bush.total_currants)
    world.facts["harvested"] = bush.total_currants
    world.say(
        f"Soon {bush.total_currants} ripe currants lay in a shining heap at {dingo.id}'s feet."
    )


def choose_sharing(world: World, dingo: Entity, helper_ent: Entity, choice: Choice) -> None:
    if choice.selfish:
        dingo.memes["greed"] += 1.0
        helper_ent.memes["trust"] -= 1.0
        world.say(
            f"But when {helper_ent.id} smiled and looked for a fair share, {dingo.id} pulled the basket close and said, "
            f'"Thank you, but I shall keep every currant for myself."'
        )
    else:
        dingo.memes["generosity"] += 1.0
        helper_ent.memes["gratitude"] += 1.0
        world.say(
            f"Then {dingo.id} counted out a fair share and said, "
            f'"You helped me gather them, so these currants belong to us both."'
        )


def propagate(world: World) -> None:
    dingo = world.get("dingo")
    helper = world.get("helper")
    container = world.get("container")
    if dingo.memes["generosity"] >= THRESHOLD and ("shared",) not in world.fired:
        world.fired.add(("shared",))
        dingo.meters["currants_owned"] = float(max(0, dingo.meters["currants_owned"] - SHARE_PORTION))
        helper.meters["currants_owned"] = float(SHARE_PORTION)
        dingo.memes["friendship"] += 1.0
        helper.memes["friendship"] += 1.0
        helper.memes["gratitude"] += 1.0
    if dingo.memes["greed"] >= 2.0 and ("refused",) not in world.fired:
        world.fired.add(("refused",))
        dingo.memes["lonely"] += 1.0
        helper.memes["hurt"] += 1.0
    if dingo.meters["currants_owned"] > container.attrs["capacity"] and ("spill",) not in world.fired:
        world.fired.add(("spill",))
        spilled = int(dingo.meters["currants_owned"] - container.attrs["capacity"])
        dingo.meters["spilled"] += float(spilled)
        dingo.meters["currants_owned"] = float(container.attrs["capacity"])
        dingo.memes["shock"] += 1.0
        dingo.memes["shame"] += 1.0
    if dingo.meters["currants_owned"] >= THRESHOLD and ("eat_dingo",) not in world.fired:
        world.fired.add(("eat_dingo",))
        dingo.meters["hunger"] = 0.0
        dingo.memes["content"] += 1.0
    if helper.meters["currants_owned"] >= THRESHOLD and ("eat_helper",) not in world.fired:
        world.fired.add(("eat_helper",))
        helper.meters["hunger"] = 0.0
        helper.memes["content"] += 1.0


def resolve(world: World, dingo: Entity, helper_ent: Entity, bush: Bush, container: Container, choice: Choice, parent: Entity) -> None:
    propagate(world)
    spilled = int(dingo.meters["spilled"])
    world.para()
    if choice.selfish:
        if spilled > 0:
            world.say(
                f"{dingo.id} tried to heap all {bush.total_currants} currants into {container.phrase}, "
                f"but {spilled} rolled over the rim and vanished into the grass."
            )
            world.say(
                f"{helper_ent.id} watched quietly, for a berry that is denied to a friend often escapes the greedy paw as well."
            )
            world.say(
                f"When {parent.id} later heard the tale, {parent.pronoun()} said, "
                f'"Who will not share even a currant may lose a feast and keep only shame."'
            )
            world.say(
                f"So the little dingo ate a smaller meal than {dingo.pronoun()} had dreamed of, and it tasted flat in a lonely mouth."
            )
            world.facts["outcome"] = "spilled"
        else:
            world.say(
                f"{dingo.id} carried the full basket away alone. The currants filled {dingo.pronoun('possessive')} belly, but the path felt longer without a friend beside {dingo.pronoun('object')}."
            )
            world.say(
                f"When {parent.id} later heard the tale, {parent.pronoun()} said, "
                f'"Food kept from a helper fills the stomach, but it leaves the heart hungry."'
            )
            world.say(
                f"The little dingo looked back toward the path and wished one warm laugh had been traded for two berries."
            )
            world.facts["outcome"] = "lonely"
    else:
        world.say(
            f"{dingo.id} and {helper_ent.id} sat in the shade and ate their currants together, one by one, until both hunger and hurry were gone."
        )
        world.say(
            f"Because the load was lighter, {container.phrase} rode easily on {dingo.id}'s shoulder, and a few currant seeds were tucked into soft earth near the path."
        )
        world.say(
            f"When {parent.id} later heard the tale, {parent.pronoun()} said, "
            f'"A shared meal plants tomorrow as well as feeding today."'
        )
        world.say(
            f"By the next rain, two green shoots stood where the seeds had been pressed down, and the little dingo smiled whenever {dingo.pronoun()} passed them."
        )
        world.facts["outcome"] = "shared"

    world.facts["spilled"] = spilled
    world.facts["dingo_kept"] = int(dingo.meters["currants_owned"])
    world.facts["helper_got"] = int(helper_ent.meters["currants_owned"])
    world.facts["dingo_hunger_after"] = int(dingo.meters["hunger"])
    world.facts["helper_hunger_after"] = int(helper_ent.meters["hunger"])


def tell(
    place: Place,
    bush: Bush,
    helper_cfg: Helper,
    container: Container,
    choice: Choice,
    dingo_name: str,
    parent_name: str,
    parent_type: str,
) -> World:
    world = World()
    dingo = world.add(Entity(id=dingo_name, kind="character", type="animal", label="the little dingo", role="hero"))
    helper_ent = world.add(Entity(id=helper_cfg.label.split()[0], kind="character", type="animal", label=helper_cfg.label, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, label="the elder dingo", role="elder"))
    container_ent = world.add(
        Entity(
            id="container",
            kind="thing",
            type="container",
            label=container.label,
            attrs={"capacity": container.capacity},
        )
    )
    bush_ent = world.add(
        Entity(
            id="bush",
            kind="thing",
            type="bush",
            label=bush.label,
            attrs={"total_currants": bush.total_currants},
        )
    )

    world.facts["place"] = place
    world.facts["bush"] = bush
    world.facts["helper_cfg"] = helper_cfg
    world.facts["container_cfg"] = container
    world.facts["choice_cfg"] = choice
    world.facts["dingo"] = dingo
    world.facts["helper"] = helper_ent
    world.facts["parent"] = parent
    world.facts["container"] = container_ent
    world.facts["bush_entity"] = bush_ent
    world.facts["spilled"] = 0
    world.facts["outcome"] = ""

    introduce(world, dingo, place, bush, container)
    discover_problem(world, dingo, bush, helper_cfg, container, choice)

    world.para()
    meet_helper(world, dingo, helper_ent, helper_cfg)
    gather(world, dingo, helper_ent, bush, helper_cfg)
    choose_sharing(world, dingo, helper_ent, choice)
    resolve(world, dingo, helper_ent, bush, container, choice, parent)
    return world


def generation_prompts(world: World) -> list[str]:
    bush = world.facts["bush"]
    choice = world.facts["choice_cfg"]
    helper = world.facts["helper_cfg"]
    dingo = world.facts["dingo"]
    if choice.selfish:
        return [
            'Write a short fable for a 3-to-5-year-old that includes the words "dingo" and "currant" and teaches that hoarding brings loss.',
            f"Tell a fable where a little dingo gets help from {helper.label} gathering currants, but tries to keep them all and learns a lonely lesson.",
            f"Write a child-facing moral tale about {dingo.id}, {bush.label}, and why refusing to share even a small currant can cost more than it saves.",
        ]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "dingo" and "currant" and centers on sharing.',
        f"Tell a gentle fable where a little dingo gathers currants with help from {helper.label}, shares fairly, and leaves behind hope for tomorrow.",
        f"Write a storybook fable about {dingo.id} learning that sharing a currant harvest makes both the meal and the world feel bigger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    dingo = world.facts["dingo"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    bush = world.facts["bush"]
    container = world.facts["container_cfg"]
    choice = world.facts["choice_cfg"]
    outcome = world.facts["outcome"]
    harvested = world.facts["harvested"]
    spilled = world.facts["spilled"]
    dingo_kept = world.facts["dingo_kept"]
    helper_got = world.facts["helper_got"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little dingo named {dingo.id}, {helper.id} who helped gather fruit, and {parent.id} who later named the lesson. The story stays small and simple so the choice about sharing can shine clearly.",
        ),
        (
            "What did the little dingo find?",
            f"{dingo.id} found {bush.label} full of ripe currants. Seeing that fruit is what started both the hunger and the temptation to keep too much.",
        ),
        (
            f"Why did {dingo.id} need help?",
            f"{bush.trouble} That is why {helper.id}'s help changed what the little dingo could gather.",
        ),
        (
            f"What choice did {dingo.id} make after the currants were gathered?",
            f"{dingo.id} chose to {choice.verb}. The choice mattered because {helper.id} had earned a fair share by helping with the harvest.",
        ),
    ]

    if outcome == "shared":
        qa.append(
            (
                f"What happened because {dingo.id} shared the currants?",
                f"{helper.id} received {helper_got} currants, and both animals were able to eat with happy hearts. The lighter load fit easily in {container.phrase}, so the ending showed plenty instead of strain.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the meal shared, hunger eased, and currant seeds tucked into the earth. The new green shoots proved that kindness can feed tomorrow as well as today.",
            )
        )
    elif outcome == "spilled":
        qa.append(
            (
                f"What happened when {dingo.id} tried to keep all {harvested} currants?",
                f"{spilled} currants spilled because {container.phrase} was too small for such a greedy load. The loss came from trying to carry more alone than was wise to keep.",
            )
        )
        qa.append(
            (
                "What lesson did the elder give?",
                f"{parent.id} said that one who will not share may lose the feast as well. The spilled berries turned greed into a visible lesson the little dingo could not ignore.",
            )
        )
    else:
        qa.append(
            (
                f"Was {dingo.id} full and happy after keeping everything?",
                f"{dingo.pronoun().capitalize()} was full, but not truly happy. The currants fed {dingo.pronoun('possessive')} stomach, yet the empty path beside {dingo.pronoun('object')} showed the cost of not sharing.",
            )
        )
        qa.append(
            (
                "What was the moral feeling at the end?",
                f"The ending felt lonely rather than joyful. Even without a spill, keeping every currant left the little dingo wishing friendship had mattered more.",
            )
        )
    return qa


KNOWLEDGE = {
    "currant": [
        (
            "What is a currant?",
            "A currant is a very small berry that grows on a bush. It can taste sweet or tart, and many currants together make a good little harvest.",
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because it lets good things help more than one person. When someone helped you, sharing also shows that you noticed their effort and cared about it.",
        )
    ],
    "basket": [
        (
            "Why do containers matter when you carry fruit?",
            "A container must be big and strong enough for what it holds. If it is too small, fruit can spill or get squashed.",
        )
    ],
    "help": [
        (
            "Why should you thank a helper?",
            "You should thank a helper because their work made the job easier or even possible. Gratitude reminds us that we do not do everything alone.",
        )
    ],
    "thorns": [
        (
            "Why are thorns tricky?",
            "Thorns are sharp parts of a plant that protect it. They can scratch you, so sometimes you need a safer way to reach the fruit inside.",
        )
    ],
    "seeds": [
        (
            "What can happen when seeds are planted?",
            "If seeds land in good soil and get water and sun, they can grow into new plants. That is how one meal can help make another someday.",
        )
    ],
}
KNOWLEDGE_ORDER = ["currant", "sharing", "basket", "help", "thorns", "seeds"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"currant", "sharing", "help"}
    bush = world.facts["bush"]
    container = world.facts["container_cfg"]
    outcome = world.facts["outcome"]
    if bush.id == "thorn_crown":
        tags.add("thorns")
    if container.id in {"leaf_cup", "reed_basket", "bark_basket"}:
        tags.add("basket")
    if outcome == "shared":
        tags.add("seeds")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="creekside",
        bush="arching_canes",
        helper="wombat",
        container="reed_basket",
        choice="share",
        dingo_name="Daru",
        parent_name="Old Ember",
        parent_type="animal",
    ),
    StoryParams(
        place="red_hill",
        bush="thorn_crown",
        helper="cockatoo",
        container="bark_basket",
        choice="share",
        dingo_name="Miro",
        parent_name="Soft Step",
        parent_type="animal",
    ),
    StoryParams(
        place="gum_grove",
        bush="low_patch",
        helper="kangaroo",
        container="leaf_cup",
        choice="hoard",
        dingo_name="Tali",
        parent_name="Red Tail",
        parent_type="animal",
    ),
    StoryParams(
        place="creekside",
        bush="low_patch",
        helper="wombat",
        container="reed_basket",
        choice="hoard",
        dingo_name="Jirra",
        parent_name="Moon Ear",
        parent_type="animal",
    ),
    StoryParams(
        place="red_hill",
        bush="arching_canes",
        helper="kangaroo",
        container="reed_basket",
        choice="share",
        dingo_name="Naru",
        parent_name="Old Ember",
        parent_type="animal",
    ),
]


ASP_RULES = r"""
% compatibility: a helper is suitable when it supplies every needed ability
missing_need(B,H) :- needs(B,A), not has_ability(H,A).
helper_ok(B,H)    :- bush(B), helper(H), not missing_need(B,H).

% carrying: a selfish choice keeps the whole harvest; a sharing choice keeps less
kept_load(B,C,Total) :- harvest(B,Total), choice(C), selfish(C).
kept_load(B,C,Total-Share) :- harvest(B,Total), choice(C), not selfish(C), share_portion(Share).

carry_ok(B,Cont,C) :- kept_load(B,C,K), capacity(Cont,Cap), K <= Cap.

valid(P,B,H,Cont,C) :- place(P), bush(B), helper(H), container(Cont), choice(C),
                       helper_ok(B,H), carry_ok(B,Cont,C).

outcome(shared) :- chosen_choice(share).
outcome(spilled) :- chosen_choice(hoard), chosen_bush(B), chosen_container(Cont),
                    kept_load(B,hoard,K), capacity(Cont,Cap), K > Cap.
outcome(lonely) :- chosen_choice(hoard), chosen_bush(B), chosen_container(Cont),
                   kept_load(B,hoard,K), capacity(Cont,Cap), K <= Cap.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for bush_id, bush in BUSHES.items():
        lines.append(asp.fact("bush", bush_id))
        lines.append(asp.fact("harvest", bush_id, bush.total_currants))
        for need in sorted(bush.needs):
            lines.append(asp.fact("needs", bush_id, need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for ability in sorted(helper.abilities):
            lines.append(asp.fact("has_ability", helper_id, ability))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("capacity", container_id, container.capacity))
    for choice_id, choice in CHOICES.items():
        lines.append(asp.fact("choice", choice_id))
        if choice.selfish:
            lines.append(asp.fact("selfish", choice_id))
    lines.append(asp.fact("share_portion", SHARE_PORTION))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_choice", params.choice),
            asp.fact("chosen_bush", params.bush),
            asp.fact("chosen_container", params.container),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    choice = CHOICES[params.choice]
    bush = BUSHES[params.bush]
    container = CONTAINERS[params.container]
    if not choice.selfish:
        return "shared"
    if kept_load(choice, bush) > container.capacity:
        return "spilled"
    return "lonely"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a little dingo, a currant harvest, and a lesson about sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bush", choices=BUSHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--dingo-name")
    ap.add_argument("--parent-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bush and args.helper:
        bush = BUSHES[args.bush]
        helper = HELPERS[args.helper]
        if not helper_can_reach(bush, helper):
            raise StoryError(explain_helper_rejection(bush, helper))
    if args.bush and args.container and args.choice:
        bush = BUSHES[args.bush]
        container = CONTAINERS[args.container]
        choice = CHOICES[args.choice]
        if not can_carry(choice, bush, container):
            raise StoryError(explain_container_rejection(bush, container, choice))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.bush is None or combo[1] == args.bush)
        and (args.helper is None or combo[2] == args.helper)
        and (args.container is None or combo[3] == args.container)
        and (args.choice is None or combo[4] == args.choice)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, bush, helper, container, choice = rng.choice(sorted(combos))
    dingo_name = args.dingo_name or rng.choice(DINGO_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    return StoryParams(
        place=place,
        bush=bush,
        helper=helper,
        container=container,
        choice=choice,
        dingo_name=dingo_name,
        parent_name=parent_name,
        parent_type="animal",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.bush not in BUSHES:
        raise StoryError(f"(Unknown bush: {params.bush})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Unknown choice: {params.choice})")

    place = PLACES[params.place]
    bush = BUSHES[params.bush]
    helper = HELPERS[params.helper]
    container = CONTAINERS[params.container]
    choice = CHOICES[params.choice]

    if not helper_can_reach(bush, helper):
        raise StoryError(explain_helper_rejection(bush, helper))
    if not can_carry(choice, bush, container):
        raise StoryError(explain_container_rejection(bush, container, choice))

    world = tell(
        place=place,
        bush=bush,
        helper_cfg=helper,
        container=container,
        choice=choice,
        dingo_name=params.dingo_name,
        parent_name=params.parent_name,
        parent_type=params.parent_type,
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


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP valid_combos parity matches ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = []
    for params in cases:
        if params.choice in CHOICES and params.bush in BUSHES and params.container in CONTAINERS:
            py_out = outcome_of(params)
            asp_out = asp_outcome(params)
            if py_out != asp_out:
                mismatches.append((params, py_out, asp_out))
    if not mismatches:
        print(f"OK: outcome model parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py_out, asp_out in mismatches[:5]:
            print(" ", params, py_out, asp_out)

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke_sample, trace=False, qa=True)
        printed = buf.getvalue()
        if smoke_sample.story.strip() not in printed:
            raise StoryError("emit() smoke test did not print the story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, bush, helper, container, choice) combos:\n")
        for place, bush, helper, container, choice in combos:
            print(f"  {place:10} {bush:14} {helper:10} {container:11} {choice}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = (
                f"### {p.dingo_name}: {p.choice} at {p.place} "
                f"({p.bush}, {p.helper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
