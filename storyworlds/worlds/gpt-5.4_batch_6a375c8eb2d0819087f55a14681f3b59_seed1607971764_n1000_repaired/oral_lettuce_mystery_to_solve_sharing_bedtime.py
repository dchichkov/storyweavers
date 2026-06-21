#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/oral_lettuce_mystery_to_solve_sharing_bedtime.py
============================================================================

A standalone story world for a gentle bedtime mystery about a missing lettuce
leaf, a child-facing clue hunt, and the calming habit of sharing.

The domain is small on purpose: two children finish their oral-care routine,
carry a bedtime lettuce snack to a little pet, notice that one leaf is missing,
and solve the mystery by following a clue to the pet's hiding place. The ending
always turns on sharing: the children share one tool while searching, and then
share the remaining lettuce with the pet once they understand what happened.

Reasonableness constraint
-------------------------
Not every pet leaves every clue or hides in every place. The world only accepts
combinations where:

* the pet is a lettuce-eating bedtime pet,
* the chosen clue is one that pet could plausibly leave, and
* the chosen hiding place is one that pet could plausibly choose.

That constraint is implemented twice:
* in Python via valid_combos() and helper predicates, and
* in an inline ASP twin via ASP_RULES + asp_facts().

Run it
------
    python storyworlds/worlds/gpt-5.4/oral_lettuce_mystery_to_solve_sharing_bedtime.py
    python storyworlds/worlds/gpt-5.4/oral_lettuce_mystery_to_solve_sharing_bedtime.py --pet rabbit --clue crumbs
    python storyworlds/worlds/gpt-5.4/oral_lettuce_mystery_to_solve_sharing_bedtime.py --pet hamster --clue slime
    python storyworlds/worlds/gpt-5.4/oral_lettuce_mystery_to_solve_sharing_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/oral_lettuce_mystery_to_solve_sharing_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/oral_lettuce_mystery_to_solve_sharing_bedtime.py --verify
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | pet | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class PetType:
    id: str
    label: str
    phrase: str
    sound: str
    appetite: str
    clues: set[str] = field(default_factory=set)
    hideouts: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    line: str
    follow: str
    answer_text: str
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
class Hideout:
    id: str
    label: str
    phrase: str
    approach: str
    ending: str
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
class Tool:
    id: str
    label: str
    phrase: str
    share_line: str
    glow: str
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
class StoryParams:
    pet: str
    clue: str
    hideout: str
    tool: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    bedtime_sound: str
    oral_item: str
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


def compatible_clue(pet: PetType, clue: Clue) -> bool:
    return clue.id in pet.clues


def compatible_hideout(pet: PetType, hideout: Hideout) -> bool:
    return hideout.id in pet.hideouts


def valid_combo(pet: PetType, clue: Clue, hideout: Hideout) -> bool:
    return compatible_clue(pet, clue) and compatible_hideout(pet, hideout)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pet_id, pet in PETS.items():
        for clue_id, clue in CLUES.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if valid_combo(pet, clue, hideout):
                    combos.append((pet_id, clue_id, hideout_id))
    return sorted(combos)


def mystery_trace(world: World) -> list[str]:
    f = world.facts
    return [
        f["clue"].label,
        f["hideout"].label,
        f["pet_cfg"].label,
    ]


def bedtime_setup(world: World, a: Entity, b: Entity, parent: Entity,
                  pet: Entity, pet_cfg: PetType, oral_item: str,
                  bedtime_sound: str) -> None:
    for kid in (a, b):
        kid.memes["calm"] += 1
        kid.memes["care"] += 1
    pet.meters["hungry"] = 1.0
    world.say(
        f"At the soft end of the day, {a.id} and {b.id} padded through the hallway "
        f"while the house made its little bedtime sound: {bedtime_sound}."
    )
    world.say(
        f"After oral care with their {oral_item}, they whispered goodnight to the sink, "
        f"took a tiny bowl of lettuce, and went to feed {pet_cfg.phrase}."
    )
    world.say(
        f"{pet_cfg.label.capitalize()} waited in the moon-silver room, making a "
        f"{pet_cfg.sound} sound that always meant {pet_cfg.appetite}."
    )
    world.facts["shared_before"] = False


def discover_missing(world: World, a: Entity, b: Entity, pet_cfg: PetType) -> None:
    bowl = world.get("bowl")
    bowl.meters["lettuce_leaves"] = 2.0
    bowl.meters["missing_leaves"] = 1.0
    for kid in (a, b):
        kid.memes["puzzled"] += 1
    world.say(
        f"But when {a.id} lifted the bowl, both children stopped. One lettuce leaf "
        f"was gone."
    )
    world.say(
        f'"That is a bedtime mystery," {b.id} whispered. "{pet_cfg.label.capitalize()} '
        f'was waiting, and now the bowl is lighter."'
    )


def choose_kindness(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    for kid in (a, b):
        kid.memes["kindness"] += 1
    world.say(
        f'{a.id} almost said, "Did you take it?" but {parent.label_word} knelt beside '
        f"them and shook {parent.pronoun('possessive')} head."
    )
    world.say(
        f'"Let\'s solve the mystery with gentle eyes," {parent.pronoun()} said. '
        f'"A kind guess is better than a grumpy guess at bedtime."'
    )
    world.facts["blame_avoided"] = True


def share_tool(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    lamp = world.get("tool")
    lamp.meters["shared"] += 1
    for kid in (a, b):
        kid.memes["teamwork"] += 1
    world.say(tool.share_line.format(a=a.id, b=b.id))
    world.say(
        f"The {tool.label} {tool.glow}, and the mystery stopped feeling sharp and scary."
    )
    world.facts["shared_before"] = True


def reveal_clue(world: World, clue: Clue, a: Entity, b: Entity) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["found"] = 1.0
    for kid in (a, b):
        kid.memes["curious"] += 1
    world.say(clue.line)
    world.say(clue.follow.format(a=a.id, b=b.id))
    world.facts["clue_found"] = clue.id


def find_hideout(world: World, hideout: Hideout, pet_cfg: PetType,
                 a: Entity, b: Entity, pet: Entity) -> None:
    hideout_ent = world.get("hideout")
    hideout_ent.meters["reached"] = 1.0
    pet.meters["found"] = 1.0
    pet.meters["safe"] = 1.0
    pet.meters["has_leaf"] = 1.0
    world.say(hideout.approach.format(a=a.id, b=b.id))
    world.say(
        f"There was {pet_cfg.phrase}, tucked in {hideout.phrase} with the missing "
        f"lettuce leaf held close."
    )
    world.say(hideout.ending.format(pet=pet_cfg.label))


def understand_pet(world: World, pet_cfg: PetType, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["understanding"] += 1
        kid.memes["puzzled"] = 0.0
    world.say(
        f'"Oh," said {a.id}, very softly. "{pet_cfg.label.capitalize()} was not being '
        f'naughty. {pet.pronoun if False else ""}'
    )
    world.say(
        f'{b.id} smiled. "{pet_cfg.label.capitalize()} just wanted a quiet nibble '
        f'before sleep, the same way we wanted a quiet story."'
    )
    world.facts["solved"] = True


def share_lettuce(world: World, a: Entity, b: Entity, pet_cfg: PetType) -> None:
    bowl = world.get("bowl")
    bowl.meters["shared_out"] = 1.0
    bowl.meters["missing_leaves"] = 0.0
    bowl.meters["lettuce_leaves"] = 0.0
    pet = world.get("pet")
    pet.meters["hungry"] = 0.0
    pet.meters["full"] = 1.0
    for kid in (a, b):
        kid.memes["warmth"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"So {a.id} tore the last clean leaf into small, soft pieces, and {b.id} held out "
        f"both hands so they could share the lettuce fairly."
    )
    world.say(
        f"They gave some to {pet_cfg.label} and kept a little for a morning treat, because "
        f"sharing at bedtime meant thinking about now and later."
    )
    world.facts["shared_lettuce"] = True


def ending(world: World, a: Entity, b: Entity, parent: Entity, pet_cfg: PetType) -> None:
    for kid in (a, b):
        kid.memes["sleepy"] += 1
    world.say(
        f"{parent.label_word.capitalize()} tucked the blanket around their shoulders while "
        f"{pet_cfg.phrase} munched in the dim room."
    )
    world.say(
        f"Soon the mystery was no longer a worry at all, only a small solved secret, and "
        f"{a.id} and {b.id} went to bed knowing that shared clues and shared lettuce had "
        f"made the night gentler."
    )


def tell(pet_cfg: PetType, clue: Clue, hideout: Hideout, tool: Tool,
         child1: str = "Nora", child1_gender: str = "girl",
         child2: str = "Ben", child2_gender: str = "boy",
         parent_type: str = "mother", bedtime_sound: str = "the clock going tick-tick",
         oral_item: str = "toothbrushes") -> World:
    world = World()
    a = world.add(Entity(
        id=child1,
        kind="character",
        type=child1_gender,
        role="child1",
        label=child1,
        attrs={"shares": True},
    ))
    b = world.add(Entity(
        id=child2,
        kind="character",
        type=child2_gender,
        role="child2",
        label=child2,
        attrs={"shares": True},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={"calm": True},
    ))
    pet = world.add(Entity(
        id="pet",
        kind="pet",
        type=pet_cfg.id,
        role="pet",
        label=pet_cfg.label,
        attrs={"likes": "lettuce"},
    ))
    world.add(Entity(
        id="bowl",
        kind="thing",
        type="bowl",
        label="lettuce bowl",
        attrs={"owner": "children"},
    ))
    world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        attrs={"shared": True},
    ))
    world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        attrs={"kind": clue.id},
    ))
    world.add(Entity(
        id="hideout",
        kind="thing",
        type="hideout",
        label=hideout.label,
        attrs={"kind": hideout.id},
    ))

    world.facts.update(
        pet_cfg=pet_cfg,
        clue=clue,
        hideout=hideout,
        tool=tool,
        oral_item=oral_item,
        bedtime_sound=bedtime_sound,
        child1=a,
        child2=b,
        parent=parent,
        pet=pet,
        blame_avoided=False,
        shared_before=False,
        clue_found="",
        solved=False,
        shared_lettuce=False,
    )

    bedtime_setup(world, a, b, parent, pet, pet_cfg, oral_item, bedtime_sound)
    world.para()
    discover_missing(world, a, b, pet_cfg)
    choose_kindness(world, a, b, parent)
    share_tool(world, a, b, tool)
    world.para()
    reveal_clue(world, clue, a, b)
    find_hideout(world, hideout, pet_cfg, a, b, pet)
    world.say(
        f'{a.id} let out the tiny breath {a.pronoun()} had been holding. "So that is the mystery."'
    )
    world.para()
    world.say(
        f'"Oh," said {a.id}, very softly. "{pet_cfg.label.capitalize()} was not being naughty."'
    )
    world.say(
        f'{b.id} smiled. "{pet_cfg.label.capitalize()} just wanted a quiet nibble before sleep, '
        f"the same way we wanted a quiet story."
    )
    world.facts["solved"] = True
    share_lettuce(world, a, b, pet_cfg)
    ending(world, a, b, parent, pet_cfg)
    return world


PETS = {
    "rabbit": PetType(
        id="rabbit",
        label="rabbit",
        phrase="the little rabbit",
        sound="soft snuffly",
        appetite="it was ready for a leafy snack",
        clues={"crumbs", "pawprint"},
        hideouts={"blanket_nest", "bookcase_cubby"},
        tags={"rabbit", "lettuce", "sharing"},
    ),
    "tortoise": PetType(
        id="tortoise",
        label="tortoise",
        phrase="the drowsy tortoise",
        sound="small scrape-scrape",
        appetite="it was thinking about one more crunch",
        clues={"crumbs", "drag_mark"},
        hideouts={"curtain_corner", "plant_pot"},
        tags={"tortoise", "lettuce", "sharing"},
    ),
    "hamster": PetType(
        id="hamster",
        label="hamster",
        phrase="the round little hamster",
        sound="faint whisk-whisk",
        appetite="it hoped for one last bedtime nibble",
        clues={"crumbs", "pawprint"},
        hideouts={"slipper_hollow", "bookcase_cubby"},
        tags={"hamster", "lettuce", "sharing"},
    ),
}

CLUES = {
    "crumbs": Clue(
        id="crumbs",
        label="nibbled crumbs",
        line="Near the bowl lay a tiny crescent of nibbled lettuce crumbs, as neat as green confetti.",
        follow="{a} pointed to the floor, and {b} bent close so they could follow the little green trail together.",
        answer_text="They found tiny lettuce crumbs leading away from the bowl.",
        tags={"clue", "lettuce"},
    ),
    "pawprint": Clue(
        id="pawprint",
        label="dusty pawprint",
        line="On the moonlit floor there was one dusty pawprint beside a thin green thread.",
        follow="{b} held the light low while {a} traced the small print toward the shadows.",
        answer_text="They found a small pawprint beside the missing lettuce trail.",
        tags={"clue", "pawprint"},
    ),
    "drag_mark": Clue(
        id="drag_mark",
        label="leaf drag mark",
        line="Across the rug ran a faint leaf drag mark, as if something patient had pulled supper behind it.",
        follow="{a} and {b} knelt shoulder to shoulder and followed the little line without making a sound.",
        answer_text="They found a drag mark showing that the lettuce had been pulled away slowly.",
        tags={"clue", "trail"},
    ),
}

HIDEOUTS = {
    "blanket_nest": Hideout(
        id="blanket_nest",
        label="blanket nest",
        phrase="a fold of the spare blanket by the rocking chair",
        approach="Step by step, {a} and {b} reached the rocking chair and lifted the blanket edge together.",
        ending="The leaf had not been stolen for mischief. {pet} had tucked it away in a cozy place.",
        tags={"hideout", "blanket"},
    ),
    "bookcase_cubby": Hideout(
        id="bookcase_cubby",
        label="bookcase cubby",
        phrase="the lowest cubby under the bookcase",
        approach="They tiptoed to the bookcase, shared the light between them, and peeped into the lowest cubby.",
        ending="It was a secret supper corner, chosen because it felt snug and safe for {pet}.",
        tags={"hideout", "bookcase"},
    ),
    "curtain_corner": Hideout(
        id="curtain_corner",
        label="curtain corner",
        phrase="the quiet corner behind the long curtain",
        approach="Together they followed the trail to the curtain and parted the cloth with two careful hands.",
        ending="Behind the curtain, the missing leaf looked less like trouble and more like a sleepy plan.",
        tags={"hideout", "curtain"},
    ),
    "plant_pot": Hideout(
        id="plant_pot",
        label="plant pot nook",
        phrase="the warm nook behind the big plant pot",
        approach="The trail curved toward the window, and {a} and {b} discovered a little nook behind the plant pot.",
        ending="It was the sort of hidden place a quiet {pet} might choose for a last munch before bed.",
        tags={"hideout", "plant"},
    ),
    "slipper_hollow": Hideout(
        id="slipper_hollow",
        label="slipper hollow",
        phrase="the hollow of a soft house slipper by the dresser",
        approach="By the dresser, they found one slipper tipped on its side and looked inside together.",
        ending="The slipper had become a tiny supper cave, perfect for a shy {pet}.",
        tags={"hideout", "slipper"},
    ),
}

TOOLS = {
    "night_light": Tool(
        id="night_light",
        label="night-light lantern",
        phrase="a little night-light lantern",
        share_line="{a} carried a little night-light lantern for three steps, then passed it to {b} for three more.",
        glow="made a buttery circle on the floor",
        tags={"light", "sharing"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="round magnifier",
        phrase="a round magnifier with a blue handle",
        share_line="{b} held the round magnifier first, and then {a} took a turn, because clues are easier to find when turns are fair.",
        glow="caught the lamplight and made the crumbs look important",
        tags={"tool", "sharing"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="pocket flashlight",
        phrase="a small pocket flashlight",
        share_line="{a} and {b} shared one small flashlight, taking turns with it so nobody had to search alone.",
        glow="drew a silver path across the rug",
        tags={"light", "sharing"},
    ),
}

BEDTIME_SOUNDS = [
    "the clock going tick-tick",
    "the heater humming softly",
    "the rain tapping the window",
    "the floorboards giving one sleepy creak",
]

ORAL_ITEMS = [
    "toothbrushes",
    "little cups from their oral-care shelf",
    "soft toothbrushes and minty rinse cups",
]

GIRL_NAMES = ["Nora", "Lila", "Mina", "Tess", "Ivy", "Lucy", "Ada", "Rose"]
BOY_NAMES = ["Ben", "Owen", "Milo", "Theo", "Evan", "Finn", "Noah", "Leo"]


def explain_rejection(pet: PetType, clue: Clue, hideout: Hideout) -> str:
    if not compatible_clue(pet, clue):
        allowed = ", ".join(sorted(pet.clues))
        return (
            f"(No story: a {pet.label} would not normally leave the clue '{clue.id}' here. "
            f"Try one of its clue types instead: {allowed}.)"
        )
    allowed = ", ".join(sorted(pet.hideouts))
    return (
        f"(No story: a {pet.label} would not usually hide in '{hideout.id}' in this bedtime world. "
        f"Try one of its likely hideouts instead: {allowed}.)"
    )


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two sisters"
    if a.type == "boy" and b.type == "boy":
        return "two brothers"
    return "a brother and a sister"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["child1"], f["child2"]
    pet_cfg, clue, hideout = f["pet_cfg"], f["clue"], f["hideout"]
    tool = f["tool"]
    return [
        (
            f'Write a gentle bedtime story for a 3-to-5-year-old that includes the words '
            f'"oral" and "lettuce", where two children solve a small mystery together.'
        ),
        (
            f"Tell a cozy mystery-to-solve story where {a.id} and {b.id} notice a missing "
            f"lettuce leaf at bedtime, share {tool.phrase}, and discover {pet_cfg.phrase} in "
            f"the {hideout.label}."
        ),
        (
            f"Write a soft story about sharing turns, following {clue.label}, and learning that "
            f"the missing leaf was a sleepy pet's snack, not a naughty trick."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["child1"], f["child2"], f["parent"]
    pet_cfg, clue, hideout, tool = f["pet_cfg"], f["clue"], f["hideout"], f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, who were getting ready for bed, "
            f"and their {pet_cfg.label}. Their {parent.label_word} helps them stay kind while "
            f"they solve the mystery."
        ),
        (
            "What made the mystery begin?",
            f"The children brought a bowl of lettuce at bedtime and noticed that one leaf was gone. "
            f"That missing leaf turned an ordinary feeding time into a mystery to solve."
        ),
        (
            "How did the children solve the mystery?",
            f"They shared {tool.phrase} and followed {clue.answer_text.lower()} "
            f"The clue led them all the way to the {hideout.label}, where the missing leaf was waiting with the pet."
        ),
        (
            "Why did the parent tell them to use kind guesses?",
            f"The parent wanted them to solve the problem without blaming each other. "
            f"That kept the bedtime mood calm and helped them notice the real clue instead of starting an argument."
        ),
        (
            "What was really happening to the missing lettuce?",
            f"The pet had carried the leaf away for a quiet bedtime nibble in the {hideout.label}. "
            f"It was not a trick at all; the pet was looking for a snug place to eat before sleep."
        ),
        (
            "How did sharing help at the end?",
            f"They shared one tool while searching, and later they shared the remaining lettuce fairly. "
            f"Because they worked together, the mystery felt smaller and the ending felt warm instead of upset."
        ),
    ]
    return qa


KNOWLEDGE = {
    "oral": [
        (
            "What does oral care mean?",
            "Oral care means taking care of your mouth, teeth, and gums. At bedtime it often means brushing gently so your mouth stays clean and healthy."
        )
    ],
    "lettuce": [
        (
            "What is lettuce?",
            "Lettuce is a leafy green vegetable. Some little pets enjoy nibbling it as a crunchy snack."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else have a turn or a part too. It helps people feel included and cared for."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues point your eyes and mind in the right direction."
        )
    ],
    "rabbit": [
        (
            "Why might a rabbit like a quiet place to eat?",
            "Rabbits are often calmer when they feel tucked away and safe. A cozy corner can make chewing feel peaceful."
        )
    ],
    "hamster": [
        (
            "Why do hamsters like little hiding places?",
            "Hamsters are small animals that often feel safe in tiny snug spaces. A little nook can feel like a shelter to them."
        )
    ],
    "tortoise": [
        (
            "Why does a tortoise move slowly?",
            "A tortoise has a heavy shell and short legs, so it moves in a patient, steady way. Slow steps can still get it exactly where it wants to go."
        )
    ],
    "light": [
        (
            "Why is one small light useful at bedtime?",
            "A small light helps you see softly without waking the whole room. It can make a dark corner feel gentle instead of scary."
        )
    ],
}
KNOWLEDGE_ORDER = ["oral", "lettuce", "sharing", "clue", "rabbit", "hamster", "tortoise", "light"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"oral", "lettuce", "sharing", "clue"}
    tags |= set(f["pet_cfg"].tags)
    tags |= set(f["tool"].tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  solved path: {mystery_trace(world)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        pet="rabbit",
        clue="crumbs",
        hideout="blanket_nest",
        tool="night_light",
        child1="Nora",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        parent="mother",
        bedtime_sound="the clock going tick-tick",
        oral_item="toothbrushes",
    ),
    StoryParams(
        pet="tortoise",
        clue="drag_mark",
        hideout="curtain_corner",
        tool="flashlight",
        child1="Mina",
        child1_gender="girl",
        child2="Theo",
        child2_gender="boy",
        parent="father",
        bedtime_sound="the rain tapping the window",
        oral_item="little cups from their oral-care shelf",
    ),
    StoryParams(
        pet="hamster",
        clue="pawprint",
        hideout="slipper_hollow",
        tool="magnifier",
        child1="Lucy",
        child1_gender="girl",
        child2="Ivy",
        child2_gender="girl",
        parent="mother",
        bedtime_sound="the heater humming softly",
        oral_item="soft toothbrushes and minty rinse cups",
    ),
    StoryParams(
        pet="rabbit",
        clue="pawprint",
        hideout="bookcase_cubby",
        tool="flashlight",
        child1="Owen",
        child1_gender="boy",
        child2="Leo",
        child2_gender="boy",
        parent="father",
        bedtime_sound="the floorboards giving one sleepy creak",
        oral_item="toothbrushes",
    ),
]


ASP_RULES = r"""
compatible_clue(P, C) :- pet(P), clue(C), leaves(P, C).
compatible_hideout(P, H) :- pet(P), hideout(H), hides_in(P, H).
valid(P, C, H) :- compatible_clue(P, C), compatible_hideout(P, H).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pet_id, pet in PETS.items():
        lines.append(asp.fact("pet", pet_id))
        for clue_id in sorted(pet.clues):
            lines.append(asp.fact("leaves", pet_id, clue_id))
        for hideout_id in sorted(pet.hideouts):
            lines.append(asp.fact("hides_in", pet_id, hideout_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify should catch any crash
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a missing lettuce leaf, a gentle mystery, and sharing."
    )
    ap.add_argument("--pet", choices=sorted(PETS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (pet, clue, hideout) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pet and args.clue and args.hideout:
        pet = PETS[args.pet]
        clue = CLUES[args.clue]
        hideout = HIDEOUTS[args.hideout]
        if not valid_combo(pet, clue, hideout):
            raise StoryError(explain_rejection(pet, clue, hideout))

    combos = [
        combo for combo in valid_combos()
        if (args.pet is None or combo[0] == args.pet)
        and (args.clue is None or combo[1] == args.clue)
        and (args.hideout is None or combo[2] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pet_id, clue_id, hideout_id = rng.choice(combos)
    tool_id = args.tool or rng.choice(sorted(TOOLS))
    parent = args.parent or rng.choice(["mother", "father"])
    child1_gender = rng.choice(["girl", "boy"])
    child2_gender = rng.choice(["girl", "boy"])
    child1 = _pick_name(rng, child1_gender)
    child2 = _pick_name(rng, child2_gender, avoid=child1)
    bedtime_sound = rng.choice(BEDTIME_SOUNDS)
    oral_item = rng.choice(ORAL_ITEMS)

    return StoryParams(
        pet=pet_id,
        clue=clue_id,
        hideout=hideout_id,
        tool=tool_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        parent=parent,
        bedtime_sound=bedtime_sound,
        oral_item=oral_item,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    pet_cfg = PETS[params.pet]
    clue = CLUES[params.clue]
    hideout = HIDEOUTS[params.hideout]
    tool = TOOLS[params.tool]

    if not valid_combo(pet_cfg, clue, hideout):
        raise StoryError(explain_rejection(pet_cfg, clue, hideout))

    world = tell(
        pet_cfg=pet_cfg,
        clue=clue,
        hideout=hideout,
        tool=tool,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
        bedtime_sound=params.bedtime_sound,
        oral_item=params.oral_item,
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
        print(f"{len(combos)} compatible (pet, clue, hideout) combos:\n")
        for pet_id, clue_id, hideout_id in combos:
            print(f"  {pet_id:9} {clue_id:10} {hideout_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.child1} & {p.child2}: {p.pet}, {p.clue}, {p.hideout}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
