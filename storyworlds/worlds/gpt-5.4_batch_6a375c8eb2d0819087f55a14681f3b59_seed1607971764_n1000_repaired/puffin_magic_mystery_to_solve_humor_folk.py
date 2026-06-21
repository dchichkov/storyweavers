#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/puffin_magic_mystery_to_solve_humor_folk.py
======================================================================

A standalone story world about a village mystery solved with the help of a
slightly vain puffin and one small piece of magic. Each story is a folk-tale
shaped puzzle: a festival object goes missing, a clue points toward a likely
borrower, the puffin uses a moon-feather to test the guess, and the mystery ends
with a kind trade and a laughing village.

Run it
------
    python storyworlds/worlds/gpt-5.4/puffin_magic_mystery_to_solve_humor_folk.py
    python storyworlds/worlds/gpt-5.4/puffin_magic_mystery_to_solve_humor_folk.py --festival broth_moon --suspect goat
    python storyworlds/worlds/gpt-5.4/puffin_magic_mystery_to_solve_humor_folk.py --suspect seal --gift brush
    python storyworlds/worlds/gpt-5.4/puffin_magic_mystery_to_solve_humor_folk.py --all
    python storyworlds/worlds/gpt-5.4/puffin_magic_mystery_to_solve_humor_folk.py --verify
    python storyworlds/worlds/gpt-5.4/puffin_magic_mystery_to_solve_humor_folk.py -n 5 --seed 7 --qa
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Festival:
    id: str
    place: str
    season_line: str
    object_label: str
    object_the: str
    object_phrase: str
    object_quality: str
    opening_image: str
    need_line: str
    close_line: str
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
class Suspect:
    id: str
    label: str
    kind: str
    clue: str
    gift: str
    voice: str
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
class Clue:
    id: str
    label: str
    found_text: str
    meaning: str
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
class Gift:
    id: str
    label: str
    phrase: str
    solves: str
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
class Scenario:
    festival: str
    suspect: str
    location: str
    hiding_detail: str
    motive: str
    apology: str
    trade_line: str
    ending_image: str
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


def _r_missing_stirs_worry(world: World) -> list[str]:
    item = world.get("festival_item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_stirs_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["worry"] += 1
    world.get("puffin").memes["worry"] += 1
    world.get("child").memes["curiosity"] += 1
    world.get("puffin").memes["curiosity"] += 1
    world.get("village").memes["worry"] += 1
    return []


def _r_clue_points_to_suspect(world: World) -> list[str]:
    clue_ent = world.get("clue")
    if clue_ent.meters["seen"] < THRESHOLD:
        return []
    suspect = world.get("suspect")
    sig = ("clue_points", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["suspected"] += 1
    world.get("child").memes["certainty"] += 1
    return []


def _r_magic_reveals_place(world: World) -> list[str]:
    feather = world.get("feather")
    clue_ent = world.get("clue")
    if feather.meters["used"] < THRESHOLD or clue_ent.meters["seen"] < THRESHOLD:
        return []
    sig = ("magic_reveals",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("path").meters["revealed"] += 1
    world.get("child").memes["hope"] += 1
    world.get("puffin").memes["pride"] += 1
    return []


def _r_kind_trade_returns_item(world: World) -> list[str]:
    suspect = world.get("suspect")
    item = world.get("festival_item")
    gift = world.get("gift")
    if gift.meters["offered"] < THRESHOLD or suspect.meters["need_met"] < THRESHOLD:
        return []
    sig = ("kind_trade",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    suspect.memes["relief"] += 1
    suspect.memes["gratitude"] += 1
    world.get("child").memes["relief"] += 1
    world.get("puffin").memes["relief"] += 1
    world.get("village").memes["relief"] += 1
    world.get("village").memes["laughter"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_stirs_worry", tag="social", apply=_r_missing_stirs_worry),
    Rule(name="clue_points_to_suspect", tag="social", apply=_r_clue_points_to_suspect),
    Rule(name="magic_reveals_place", tag="magic", apply=_r_magic_reveals_place),
    Rule(name="kind_trade_returns_item", tag="social", apply=_r_kind_trade_returns_item),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


FESTIVALS = {
    "broth_moon": Festival(
        id="broth_moon",
        place="the cliff village",
        season_line="Each year, when the first silver fog climbed from the sea, the people of the cliff village made moon-broth in a black iron pot.",
        object_label="moon ladle",
        object_the="the moon ladle",
        object_phrase="a moon ladle carved from pale driftwood",
        object_quality="It made the soup shine as if a star had melted into it.",
        opening_image="The pot already steamed in the square, and every nose in the village pointed toward supper.",
        need_line="Without the moon ladle, the broth would not be stirred in the old lucky way.",
        close_line="That night the broth tasted warm, brave, and just a little bit silly.",
        tags={"soup", "festival", "magic"},
    ),
    "harbor_echo": Festival(
        id="harbor_echo",
        place="the harbor village",
        season_line="Each spring, when the boats were painted fresh and bright, the harbor village rang a bell to ask the sea for gentle weather.",
        object_label="harbor bell",
        object_the="the harbor bell",
        object_phrase="a harbor bell with a moon-bright handle",
        object_quality="Its clear note skipped over the water like a pebble.",
        opening_image="The boats bobbed at their ropes, and even the gulls seemed to wait for the first ring.",
        need_line="Without the harbor bell, the blessing song could not properly begin.",
        close_line="That evening the bell rang so merrily that even the ropes seemed to dance.",
        tags={"bell", "festival", "magic"},
    ),
    "lantern_reel": Festival(
        id="lantern_reel",
        place="the windy lane",
        season_line="On the longest evening of summer, the folk of the windy lane braided lanterns with ribbon and danced until the stars grew jealous.",
        object_label="star ribbon",
        object_the="the star ribbon",
        object_phrase="a star ribbon woven with tiny silver shells",
        object_quality="It made every lantern sway as if it knew the steps already.",
        opening_image="Lantern frames hung from doorways, and the lane smelled of lamp oil, bread, and salt.",
        need_line="Without the star ribbon, the first lantern could not be tied, and no one wished to start the reel crooked.",
        close_line="By moonrise the lanterns twirled so neatly that the old aunties clapped in time.",
        tags={"lantern", "festival", "magic"},
    ),
}

SUSPECTS = {
    "goat": Suspect(
        id="goat",
        label="Old Nib the goat",
        kind="goat",
        clue="hoofprints",
        gift="brush",
        voice="bleated through a mouthful of leaves",
        tags={"goat", "funny"},
    ),
    "baker": Suspect(
        id="baker",
        label="Marta the baker",
        kind="person",
        clue="flour",
        gift="wooden_spoon",
        voice="said, pink with embarrassment",
        tags={"baker", "bread"},
    ),
    "seal": Suspect(
        id="seal",
        label="Round Finn the seal",
        kind="seal",
        clue="fish_scales",
        gift="shell_ball",
        voice="barked with the innocent face of someone trying very hard not to look guilty",
        tags={"seal", "sea", "funny"},
    ),
}

CLUES = {
    "hoofprints": Clue(
        id="hoofprints",
        label="a line of moony hoofprints",
        found_text="In the damp dust lay a line of moony hoofprints, neat as stamped cookies.",
        meaning="The marks were too tidy for a dog and too proud for a sheep.",
        tags={"tracks"},
    ),
    "flour": Clue(
        id="flour",
        label="a puff of flour",
        found_text="By the empty peg lay a puff of flour, white and soft as a sneeze.",
        meaning="Someone had carried the mystery away with baking hands.",
        tags={"flour"},
    ),
    "fish_scales": Clue(
        id="fish_scales",
        label="three shining fish scales",
        found_text="On the step glittered three fish scales, shining like tiny coins.",
        meaning="No land creature in the village left such slippery little calling cards.",
        tags={"fish", "sea"},
    ),
}

GIFTS = {
    "brush": Gift(
        id="brush",
        label="a back-scratching brush",
        phrase="a long willow brush",
        solves="something to scratch an unreachable itch",
        tags={"brush"},
    ),
    "wooden_spoon": Gift(
        id="wooden_spoon",
        label="a stout wooden spoon",
        phrase="a stout wooden spoon from the cookfire shed",
        solves="a proper tool for stirring sticky jam",
        tags={"spoon"},
    ),
    "shell_ball": Gift(
        id="shell_ball",
        label="a clacking shell ball",
        phrase="a clacking ball woven from smooth shells",
        solves="a shiny toy to bat and chase",
        tags={"toy", "shell"},
    ),
}

SCENARIOS = {
    ("broth_moon", "goat"): Scenario(
        festival="broth_moon",
        suspect="goat",
        location="the cabbage patch behind the well",
        hiding_detail="The moon ladle was leaning against a fence post like a royal scratching stick.",
        motive="Old Nib had borrowed it to scratch the place between his shoulders that no honest horn could ever reach.",
        apology="I meant to bring it back before the broth sang.",
        trade_line="A brush would do the job without seasoning the village supper with goat hair.",
        ending_image="Old Nib scratched happily against the new brush and looked so pleased that even the mayor laughed.",
    ),
    ("harbor_echo", "goat"): Scenario(
        festival="harbor_echo",
        suspect="goat",
        location="the cabbage patch behind the well",
        hiding_detail="The harbor bell hung from the fence, and Old Nib was admiring his own reflection in it.",
        motive="Old Nib had borrowed it because the polished bell made him feel grand, as if he were mayor of all goats.",
        apology="I only wished to look important for one little nibble of the afternoon.",
        trade_line="A brush would make a finer throne gift than a bell ever could.",
        ending_image="The goat strutted with the brush tucked under one foreleg like a prince with a scepter.",
    ),
    ("lantern_reel", "goat"): Scenario(
        festival="lantern_reel",
        suspect="goat",
        location="the cabbage patch behind the well",
        hiding_detail="The star ribbon was looped around Old Nib's horns in two crooked bows.",
        motive="Old Nib had borrowed it because the shells tickled when the wind shook them, and he fancied himself handsome.",
        apology="No ribbon has ever applauded me so sweetly.",
        trade_line="A brush would suit his vanity better and leave the dancing ribbon for the dancers.",
        ending_image="Old Nib stood very still while the child brushed him, as solemn as a king being crowned.",
    ),
    ("broth_moon", "baker"): Scenario(
        festival="broth_moon",
        suspect="baker",
        location="the warm bakery shelf",
        hiding_detail="The moon ladle rested beside a pan of plum jam, sticky up to its chin.",
        motive="Marta had borrowed it because her jam bubbled too fiercely, and the nearest spoon had snapped that morning.",
        apology="I told myself I would rinse it in one blink and one blink turned into three trays of buns.",
        trade_line="A stout wooden spoon would save both the jam and the lucky ladle from another sticky quarrel.",
        ending_image="Marta laughed so hard at herself that flour jumped from her apron in a little white cloud.",
    ),
    ("harbor_echo", "baker"): Scenario(
        festival="harbor_echo",
        suspect="baker",
        location="the warm bakery shelf",
        hiding_detail="The harbor bell stood beside the oven, and Marta was using its handle to tap the bread pans in a steady rhythm.",
        motive="Marta had borrowed it because the pans all stuck, and the bell-handle was smooth and cool in her floury hand.",
        apology="I only meant to borrow the handle, not the whole blessing.",
        trade_line="A stout wooden spoon could rap pans all morning without stealing the village weather song.",
        ending_image="Afterward the baker tapped her pans with the spoon and declared it a better drummer than any bell.",
    ),
    ("broth_moon", "seal"): Scenario(
        festival="broth_moon",
        suspect="seal",
        location="the tide pool below the stairs",
        hiding_detail="The moon ladle floated in a tide pool while Round Finn nudged it in circles like a silver boat.",
        motive="Round Finn had borrowed it because the curved bowl made the prettiest little whirlpools.",
        apology="I did not know people could miss a thing so quickly when it still made such good circles.",
        trade_line="A shell ball would chase and clack without delaying supper.",
        ending_image="Round Finn spent the evening batting the shell ball between his flippers and splashing like a drum.",
    ),
    ("harbor_echo", "seal"): Scenario(
        festival="harbor_echo",
        suspect="seal",
        location="the tide pool below the stairs",
        hiding_detail="The harbor bell lay in the water while Round Finn bumped it with his nose to hear the muffled bonk beneath the waves.",
        motive="Round Finn had borrowed it because he liked the underwater bonk, which sounded to him like a whale laughing in a bucket.",
        apology="A sea creature cannot be blamed for loving a sea-sounding bell.",
        trade_line="A shell ball would clack for play and let the harbor bell sing where people could hear it.",
        ending_image="The seal rolled the shell ball against the rocks until even the crabs seemed curious.",
    ),
    ("lantern_reel", "seal"): Scenario(
        festival="lantern_reel",
        suspect="seal",
        location="the tide pool below the stairs",
        hiding_detail="The star ribbon trailed over the water like a bit of fallen moonlight, and Round Finn kept trying to catch its shells with his whiskers.",
        motive="Round Finn had borrowed it because the shells winked in the tide and made a game too bright to ignore.",
        apology="It looked exactly like the sort of thing the sea had misplaced for me.",
        trade_line="A shell ball would be a fairer plaything than the first ribbon of the reel.",
        ending_image="Round Finn tossed the shell ball, missed it grandly, and fell over with such dignity that the puffin snorted.",
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for (festival_id, suspect_id), _scenario in SCENARIOS.items():
        suspect = SUSPECTS[suspect_id]
        combos.append((festival_id, suspect_id, suspect.clue, suspect.gift))
    return sorted(combos)


@dataclass
class StoryParams:
    festival: str
    suspect: str
    clue: str
    gift: str
    child_name: str
    child_gender: str
    puffin_name: str
    elder_type: str
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


def explain_bad_combo(festival_id: str, suspect_id: str) -> str:
    if festival_id not in FESTIVALS:
        return f"(No story: unknown festival '{festival_id}'.)"
    if suspect_id not in SUSPECTS:
        return f"(No story: unknown suspect '{suspect_id}'.)"
    fest = FESTIVALS[festival_id]
    suspect = SUSPECTS[suspect_id]
    return (
        f"(No story: {suspect.label} is not a sensible borrower for {fest.object_the} "
        f"in this little world. Pick one of the compatible mystery shapes instead.)"
    )


def explain_bad_clue(suspect_id: str, clue_id: str) -> str:
    suspect = SUSPECTS[suspect_id]
    expected = suspect.clue
    return (
        f"(No story: {suspect.label} should leave the clue '{expected}', not '{clue_id}'. "
        f"The mystery must be solvable from a plausible trace.)"
    )


def explain_bad_gift(suspect_id: str, gift_id: str) -> str:
    suspect = SUSPECTS[suspect_id]
    expected = suspect.gift
    return (
        f"(No story: the kind ending for {suspect.label} needs gift '{expected}', not "
        f"'{gift_id}'. The trade should solve the borrower's real need.)"
    )


def setup_story(world: World, festival: Festival, child: Entity, puffin: Entity, elder: Entity) -> None:
    world.say(
        f"{festival.season_line} {festival.opening_image}"
    )
    world.say(
        f"In that village lived {child.id}, a sharp-eyed {child.type}, and {puffin.id}, "
        f"a puffin with a striped beak and the confident walk of someone who believed "
        f"he had invented walking."
    )
    world.say(
        f"{elder.label_word.capitalize()} always trusted the two of them with small errands, "
        f"because one had patience and the other had feathers."
    )


def announce_need(world: World, festival: Festival, child: Entity, elder: Entity) -> None:
    item = world.get("festival_item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {elder.label_word} reached for {festival.object_phrase}, the peg was bare. "
        f"{festival.need_line}"
    )
    world.say(
        f'"Oh dear," said {elder.label_word}. "Someone has walked off with {festival.object_the}."'
    )


def inspect_clue(world: World, clue: Clue, suspect: Suspect, child: Entity, puffin: Entity) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(clue.found_text)
    world.say(
        f'{child.id} crouched down. "{clue.meaning}"'
    )
    boast = {
        "hoofprints": "I would have noticed them first if I had been looking lower.",
        "flour": "A fine clue. It nearly went up my nose.",
        "fish_scales": "Shiny evidence is my favorite kind of evidence.",
    }[clue.id]
    world.say(
        f'"Then it points to {suspect.label}," said {puffin.id}. "{boast}"'
    )


def use_magic_feather(world: World, festival: Festival, child: Entity, puffin: Entity, scenario: Scenario) -> None:
    feather = world.get("feather")
    feather.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{puffin.id} pulled a silver feather from under one wing. It was no ordinary feather. "
        f"In the old stories, a puffin feather borrowed one truth from moonlight and gave it back before dawn."
    )
    world.say(
        f'{child.id} laid the feather on {festival.object_the}\'s empty peg. '
        f'At once it spun, shivered, and slid through the air like a tiny boat with somewhere urgent to be.'
    )
    world.say(
        f"It pointed toward {scenario.location}. {puffin.id} puffed out his chest so far that he nearly toppled over the step."
    )


def discover_borrower(
    world: World,
    suspect: Suspect,
    scenario: Scenario,
    child: Entity,
    puffin: Entity,
) -> None:
    suspect_ent = world.get("suspect")
    suspect_ent.meters["found_at_place"] += 1
    world.say(
        f"They followed the feather and found {suspect.label} at {scenario.location}. "
        f"{scenario.hiding_detail}"
    )
    world.say(
        f'"{suspect.voice.capitalize()}," said {child.id}, "did you take it?"'
    )
    world.say(
        f'{suspect.label} {suspect.voice}. "{scenario.motive} {scenario.apology}"'
    )
    suspect_ent.meters["need_shown"] += 1
    suspect_ent.memes["embarrassment"] += 1
    puffin.memes["amusement"] += 1
    child.memes["kindness"] += 1


def make_trade(world: World, gift: Gift, scenario: Scenario, child: Entity, puffin: Entity, suspect: Suspect) -> None:
    gift_ent = world.get("gift")
    suspect_ent = world.get("suspect")
    gift_ent.meters["offered"] += 1
    suspect_ent.meters["need_met"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} thought for a moment. "{scenario.trade_line}"'
    )
    world.say(
        f"{puffin.id} nodded so hard that his beak clicked. Together they offered {gift.phrase}, "
        f"which was exactly right for {gift.solves}."
    )
    world.say(
        f"{suspect.label} handed back the missing treasure at once, looking relieved instead of sneaky."
    )


def celebration(
    world: World,
    festival: Festival,
    child: Entity,
    puffin: Entity,
    elder: Entity,
    scenario: Scenario,
) -> None:
    world.say(
        f"They carried {festival.object_the} home. {festival.close_line}"
    )
    world.say(
        f"{scenario.ending_image}"
    )
    world.say(
        f"{elder.label_word.capitalize()} rang, stirred, or tied as the custom required, and the whole village cheered. "
        f"{child.id} bowed. {puffin.id} bowed lower, for he felt bows should always notice the puffin."
    )


def tell(
    festival: Festival,
    suspect_cfg: Suspect,
    clue_cfg: Clue,
    gift_cfg: Gift,
    scenario: Scenario,
    child_name: str = "Mira",
    child_gender: str = "girl",
    puffin_name: str = "Tumble",
    elder_type: str = "aunt",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=["patient", "curious"],
        )
    )
    puffin = world.add(
        Entity(
            id=puffin_name,
            kind="character",
            type="puffin",
            role="helper",
            label=puffin_name,
            traits=["proud", "funny"],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            traits=["calm"],
        )
    )
    village = world.add(
        Entity(
            id="village",
            kind="thing",
            type="village",
            label="the village",
        )
    )
    festival_item = world.add(
        Entity(
            id="festival_item",
            kind="thing",
            type="festival_item",
            label=festival.object_label,
            attrs={"festival": festival.id},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="thing",
            type="clue",
            label=clue_cfg.label,
            attrs={"clue_id": clue_cfg.id},
        )
    )
    suspect = world.add(
        Entity(
            id="suspect",
            kind="character" if suspect_cfg.kind == "person" else "thing",
            type=suspect_cfg.kind,
            role="suspect",
            label=suspect_cfg.label,
            attrs={"suspect_id": suspect_cfg.id},
        )
    )
    feather = world.add(
        Entity(
            id="feather",
            kind="thing",
            type="magic",
            label="moon feather",
        )
    )
    gift = world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift_cfg.label,
            attrs={"gift_id": gift_cfg.id},
        )
    )
    path = world.add(
        Entity(
            id="path",
            kind="thing",
            type="path",
            label="the path of the mystery",
        )
    )

    world.facts.update(
        festival=festival,
        suspect_cfg=suspect_cfg,
        clue_cfg=clue_cfg,
        gift_cfg=gift_cfg,
        scenario=scenario,
        child=child,
        puffin=puffin,
        elder=elder,
        solved=False,
        returned=False,
        location=scenario.location,
    )

    setup_story(world, festival, child, puffin, elder)
    world.para()
    announce_need(world, festival, child, elder)
    inspect_clue(world, clue_cfg, suspect_cfg, child, puffin)
    world.para()
    use_magic_feather(world, festival, child, puffin, scenario)
    discover_borrower(world, suspect_cfg, scenario, child, puffin)
    world.para()
    make_trade(world, gift_cfg, scenario, child, puffin, suspect_cfg)
    celebration(world, festival, child, puffin, elder, scenario)

    world.facts["solved"] = world.get("path").meters["revealed"] >= THRESHOLD
    world.facts["returned"] = world.get("festival_item").meters["found"] >= THRESHOLD
    return world


CHILD_NAMES = ["Mira", "Oren", "Tali", "Bram", "Nella", "Ivo", "Sula", "Perrin"]
PUFFIN_NAMES = ["Tumble", "Pebble", "Skipper", "Pip", "Dabble"]
ELDERS = ["aunt", "uncle", "mother", "father"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    festival = f["festival"]
    suspect = f["suspect_cfg"]
    clue = f["clue_cfg"]
    child = f["child"]
    puffin = f["puffin"]
    return [
        f'Write a short folk-tale for a 3-to-5-year-old about a missing festival object, a puffin, and a mystery solved with a little magic. Include the word "puffin".',
        f"Tell a village mystery where {child.id} and a puffin named {puffin.id} find {clue.label} and use a magic feather to discover that {suspect.label} borrowed {festival.object_the}.",
        f"Write a gentle humorous tale in which a magical clue leads to a kind solution, and the ending shows the village celebrating once {festival.object_the} is returned.",
    ]


KNOWLEDGE = {
    "puffin": [
        (
            "What is a puffin?",
            "A puffin is a seabird with a bright beak and short wings. It lives near the sea and can swim very well."
        )
    ],
    "festival": [
        (
            "What is a festival?",
            "A festival is a special day when people gather to celebrate together. They may sing, eat, dance, or use treasured objects that belong to the whole village."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Footprints, flour, or fish scales can all be clues if they point to what happened."
        )
    ],
    "magic": [
        (
            "What does magic do in a folk tale?",
            "In a folk tale, magic often helps the truth come into view. It does not replace thinking, but it can nudge a kind and clever person in the right direction."
        )
    ],
    "kindness": [
        (
            "Why is kindness a good way to solve a problem?",
            "Kindness can fix the real reason behind the trouble instead of only scolding. When someone is helped fairly, they are more ready to return what they took and make things right."
        )
    ],
    "goat": [
        (
            "Why do goats rub and scratch on things?",
            "Goats like to rub on posts, fences, and brushes when they itch. A brush is safer and kinder than using something important that belongs to everyone."
        )
    ],
    "baker": [
        (
            "What does a baker use to stir hot jam or dough?",
            "A baker uses sturdy kitchen tools like spoons and paddles. Good tools keep food moving without borrowing the wrong thing."
        )
    ],
    "seal": [
        (
            "Why might a seal chase shiny things?",
            "Seals notice movement and sparkle in the water. A clacky toy can keep a playful seal busy without taking something from people."
        )
    ],
}
KNOWLEDGE_ORDER = ["puffin", "festival", "clue", "magic", "kindness", "goat", "baker", "seal"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    festival = f["festival"]
    suspect = f["suspect_cfg"]
    clue = f["clue_cfg"]
    gift = f["gift_cfg"]
    scenario = f["scenario"]
    child = f["child"]
    puffin = f["puffin"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a careful {child.type}, and {puffin.id}, a puffin who helps solve a village mystery. They work together when {festival.object_the} goes missing."
        ),
        (
            f"What was missing?",
            f"{festival.object_the.capitalize()} was missing just when the village needed it for the festival. That mattered because {festival.need_line[0].lower() + festival.need_line[1:]}"
        ),
        (
            "What clue did they find?",
            f"They found {clue.label}. That clue mattered because {clue.meaning.lower()}"
        ),
        (
            f"How did the magic help solve the mystery?",
            f"{puffin.id} used a moon-feather that spun toward the truth. It did not choose a random path; it only worked after they noticed the right clue and thought about what it meant."
        ),
        (
            f"Why had {suspect.label} taken the missing thing?",
            f"{scenario.motive} {scenario.apology} The trouble was silly rather than mean, which is why a kind answer could fix it."
        ),
        (
            "How did they solve the problem?",
            f"They offered {gift.phrase} instead. That solved the real need, so {suspect.label} gladly returned {festival.object_the} and the festival could begin."
        ),
        (
            "How did the story end?",
            f"The village celebrated once {festival.object_the} was back in place. The ending image shows what changed: the missing object returned, the borrower relieved, and everyone laughing instead of worrying."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    suspect = world.facts["suspect_cfg"]
    tags = {"puffin", "festival", "clue", "magic", "kindness", suspect.id}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:13} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="broth_moon",
        suspect="goat",
        clue="hoofprints",
        gift="brush",
        child_name="Mira",
        child_gender="girl",
        puffin_name="Tumble",
        elder_type="aunt",
    ),
    StoryParams(
        festival="broth_moon",
        suspect="baker",
        clue="flour",
        gift="wooden_spoon",
        child_name="Oren",
        child_gender="boy",
        puffin_name="Pebble",
        elder_type="father",
    ),
    StoryParams(
        festival="harbor_echo",
        suspect="seal",
        clue="fish_scales",
        gift="shell_ball",
        child_name="Tali",
        child_gender="girl",
        puffin_name="Skipper",
        elder_type="uncle",
    ),
    StoryParams(
        festival="lantern_reel",
        suspect="goat",
        clue="hoofprints",
        gift="brush",
        child_name="Bram",
        child_gender="boy",
        puffin_name="Pip",
        elder_type="mother",
    ),
    StoryParams(
        festival="harbor_echo",
        suspect="baker",
        clue="flour",
        gift="wooden_spoon",
        child_name="Nella",
        child_gender="girl",
        puffin_name="Dabble",
        elder_type="aunt",
    ),
]


ASP_RULES = r"""
valid(F,S,C,G) :- scenario(F,S), clue_of(S,C), gift_of(S,G).

solved(F,S) :- scenario(F,S), clue_of(S,_), gift_of(S,_).
returned(F,S) :- solved(F,S).

#show valid/4.
#show solved/2.
#show returned/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for festival_id in FESTIVALS:
        lines.append(asp.fact("festival", festival_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        lines.append(asp.fact("clue_of", suspect_id, suspect.clue))
        lines.append(asp.fact("gift_of", suspect_id, suspect.gift))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for gift_id in GIFTS:
        lines.append(asp.fact("gift", gift_id))
    for festival_id, suspect_id in sorted(SCENARIOS):
        lines.append(asp.fact("scenario", festival_id, suspect_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP valid combos match Python valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation and emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolve/generate produced an empty story")
        print("OK: default resolve_params() and generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a puffin, a small magical mystery, and a kind folk-tale ending."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--puffin-name")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.suspect and args.clue:
        expected = SUSPECTS[args.suspect].clue
        if args.clue != expected:
            raise StoryError(explain_bad_clue(args.suspect, args.clue))
    if args.suspect and args.gift:
        expected = SUSPECTS[args.suspect].gift
        if args.gift != expected:
            raise StoryError(explain_bad_gift(args.suspect, args.gift))
    if args.festival and args.suspect and (args.festival, args.suspect) not in SCENARIOS:
        raise StoryError(explain_bad_combo(args.festival, args.suspect))

    combos = [
        combo
        for combo in valid_combos()
        if (args.festival is None or combo[0] == args.festival)
        and (args.suspect is None or combo[1] == args.suspect)
        and (args.clue is None or combo[2] == args.clue)
        and (args.gift is None or combo[3] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, suspect_id, clue_id, gift_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    puffin_name = args.puffin_name or rng.choice(PUFFIN_NAMES)
    elder_type = args.elder or rng.choice(ELDERS)
    return StoryParams(
        festival=festival_id,
        suspect=suspect_id,
        clue=clue_id,
        gift=gift_id,
        child_name=child_name,
        child_gender=child_gender,
        puffin_name=puffin_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.festival not in FESTIVALS:
        raise StoryError(f"(No story: unknown festival '{params.festival}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(No story: unknown suspect '{params.suspect}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.gift not in GIFTS:
        raise StoryError(f"(No story: unknown gift '{params.gift}'.)")
    if (params.festival, params.suspect) not in SCENARIOS:
        raise StoryError(explain_bad_combo(params.festival, params.suspect))
    if params.clue != SUSPECTS[params.suspect].clue:
        raise StoryError(explain_bad_clue(params.suspect, params.clue))
    if params.gift != SUSPECTS[params.suspect].gift:
        raise StoryError(explain_bad_gift(params.suspect, params.gift))

    world = tell(
        festival=FESTIVALS[params.festival],
        suspect_cfg=SUSPECTS[params.suspect],
        clue_cfg=CLUES[params.clue],
        gift_cfg=GIFTS[params.gift],
        scenario=SCENARIOS[(params.festival, params.suspect)],
        child_name=params.child_name,
        child_gender=params.child_gender,
        puffin_name=params.puffin_name,
        elder_type=params.elder_type,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, suspect, clue, gift) combos:\n")
        for festival_id, suspect_id, clue_id, gift_id in combos:
            print(f"  {festival_id:13} {suspect_id:8} {clue_id:12} {gift_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.puffin_name}: {p.festival} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
