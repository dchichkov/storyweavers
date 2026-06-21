#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/except_shorten_bravery_moral_value_whodunit.py
===========================================================================

A standalone storyworld for a gentle child-sized whodunit: a special classroom
object goes missing, one child notices a clue, and bravery plus kindness help
the truth come out.

This world is built around two features:
- Bravery: the seeker must decide whether to ask a hard question.
- Moral Value: the ending turns on honesty, asking first, and making things right.

It also includes the words "except" and "shorten" in the stories it tells.

Run it
------
    python storyworlds/worlds/gpt-5.4/except_shorten_bravery_moral_value_whodunit.py
    python storyworlds/worlds/gpt-5.4/except_shorten_bravery_moral_value_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/except_shorten_bravery_moral_value_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/except_shorten_bravery_moral_value_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/except_shorten_bravery_moral_value_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/except_shorten_bravery_moral_value_whodunit.py --verify
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
COURAGE_MIN = 6
KINDNESS_MIN = 5


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    hush: str
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
class MissingItem:
    id: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Motive:
    id: str
    reason: str
    confession: str
    moral: str
    item_tags: set[str] = field(default_factory=set)
    spot_tags: set[str] = field(default_factory=set)
    clue_tags: set[str] = field(default_factory=set)
    place_tags: set[str] = field(default_factory=set)
    honesty_bonus: int = 0
    brave_text: str = ""
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


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    reveal: str
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
    sentence: str
    point: str
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


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        opening="Sunlight lay in warm squares across the classroom rug.",
        hush="The room felt as if it were holding its breath for a mystery.",
        tags={"craft", "cozy", "storage"},
    ),
    "library": Setting(
        id="library",
        place="the school library corner",
        opening="The library corner smelled like paper and clean crayons.",
        hush="Even the beanbags seemed to listen while the mystery grew.",
        tags={"cozy", "storage"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        opening="Blocks, puppets, and paper crowns waited around the bright playroom.",
        hush="The playroom suddenly felt like the sort of place where clues might whisper.",
        tags={"craft", "storage"},
    ),
}

ITEMS = {
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        phrase="the silver ribbon for the reading prize",
        tags={"trimmable", "giftable", "portable", "decor"},
    ),
    "bookmark": MissingItem(
        id="bookmark",
        label="bookmark",
        phrase="the star-shaped bookmark for story time",
        tags={"trimmable", "giftable", "portable", "paper"},
    ),
    "paper_chain": MissingItem(
        id="paper_chain",
        label="paper chain",
        phrase="the paper chain for the class party",
        plural=False,
        tags={"trimmable", "portable", "decor", "paper"},
    ),
}

MOTIVES = {
    "repair": Motive(
        id="repair",
        reason="the end looked messy and needed a careful fix",
        confession="I saw the end was frayed, and I wanted to shorten it so it would not drag or tear.",
        moral="It is kind to help, but you still have to ask first and tell the truth.",
        item_tags={"trimmable"},
        spot_tags={"craft"},
        clue_tags={"snip"},
        place_tags={"craft"},
        honesty_bonus=1,
        brave_text="asking about the little snip-mark felt scary because it might hurt a friend's feelings",
    ),
    "surprise": Motive(
        id="surprise",
        reason="a secret treat seemed like a good way to shorten the long wait before the celebration",
        confession="I wanted to make a tiny surprise with it and shorten the long wait before the celebration, but then I hid it and made everyone worry.",
        moral="Even a happy surprise should not begin with taking something in secret.",
        item_tags={"giftable"},
        spot_tags={"cozy", "craft"},
        clue_tags={"star"},
        place_tags={"cozy", "craft"},
        honesty_bonus=0,
        brave_text="asking about the secret paper star felt brave because the clue pointed toward someone the seeker liked",
    ),
    "tidy": Motive(
        id="tidy",
        reason="the item might get stepped on if it stayed on the floor",
        confession="I moved it to keep it safe, and then I forgot to say where I put it.",
        moral="Helping quietly can still cause trouble when you leave people confused.",
        item_tags={"portable"},
        spot_tags={"storage"},
        clue_tags={"label"},
        place_tags={"storage"},
        honesty_bonus=2,
        brave_text="speaking up felt brave because everyone was guessing except the one child who already looked worried",
    ),
}

SPOTS = {
    "art_drawer": Spot(
        id="art_drawer",
        label="art drawer",
        phrase="the shallow art drawer beside the scissors cup",
        reveal="Inside the art drawer, under a sheet of yellow paper, lay the missing item.",
        tags={"craft", "storage"},
    ),
    "cushion_nook": Spot(
        id="cushion_nook",
        label="cushion nook",
        phrase="the cushion nook behind the reading tent",
        reveal="Tucked behind the biggest cushion was the missing item.",
        tags={"cozy"},
    ),
    "cubby": Spot(
        id="cubby",
        label="cubby",
        phrase="the top cubby near the door",
        reveal="On the top cubby shelf, just where small eyes could miss it, sat the missing item.",
        tags={"storage"},
    ),
}

CLUES = {
    "snipped_thread": Clue(
        id="snipped_thread",
        label="snipped thread",
        sentence="Near the empty hook lay one tiny snipped thread, neat as a whisper.",
        point="The clue suggested scissors and careful fingers.",
        tags={"snip"},
    ),
    "paper_star": Clue(
        id="paper_star",
        label="paper star",
        sentence="By the window gleamed a folded paper star with a dot of paste on one side.",
        point="The clue suggested secret crafting and a surprise plan.",
        tags={"star"},
    ),
    "name_label": Clue(
        id="name_label",
        label="name label",
        sentence="Beside the rug was a little paper label from a cubby basket.",
        point="The clue suggested somebody had tried to put things away neatly.",
        tags={"label"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    owner = world.get("owner")
    seeker = world.get("seeker")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    seeker.memes["curiosity"] += 1
    return []


def _r_clue_suspicion(world: World) -> list[str]:
    seeker = world.get("seeker")
    if world.facts.get("clue_seen", 0.0) < THRESHOLD:
        return []
    sig = ("clue_suspicion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["suspicion"] += 1
    return []


def _r_gentle_confession(world: World) -> list[str]:
    culprit = world.get("culprit")
    seeker = world.get("seeker")
    if world.facts.get("gentle_question", 0.0) < THRESHOLD:
        return []
    if culprit.memes["guilt"] < THRESHOLD:
        return []
    sig = ("gentle_confession",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    courage = int(seeker.memes["bravery"])
    kindness = int(seeker.memes["kindness"])
    bonus = int(world.facts.get("honesty_bonus", 0))
    if courage + kindness + bonus >= 11:
        culprit.memes["honesty"] += 1
        world.facts["confessed"] = 1.0
    return []


def _r_recovery_relief(world: World) -> list[str]:
    item = world.get("item")
    owner = world.get("owner")
    culprit = world.get("culprit")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("recovery_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["relief"] += 1
    culprit.memes["remorse"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="clue_suspicion", tag="mental", apply=_r_clue_suspicion),
    Rule(name="gentle_confession", tag="social", apply=_r_gentle_confession),
    Rule(name="recovery_relief", tag="social", apply=_r_recovery_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def combo_valid(setting: Setting, item: MissingItem, motive: Motive, spot: Spot, clue: Clue) -> bool:
    return (
        bool(setting.tags & motive.place_tags)
        and bool(item.tags & motive.item_tags)
        and bool(spot.tags & motive.spot_tags)
        and bool(clue.tags & motive.clue_tags)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for mid, motive in MOTIVES.items():
                for spid, spot in SPOTS.items():
                    for cid, clue in CLUES.items():
                        if combo_valid(setting, item, motive, spot, clue):
                            combos.append((sid, iid, mid, spid, cid))
    return combos


def explain_rejection(setting: Setting, item: MissingItem, motive: Motive, spot: Spot, clue: Clue) -> str:
    reasons = []
    if not (setting.tags & motive.place_tags):
        reasons.append(f"{setting.place} does not fit the motive '{motive.id}'")
    if not (item.tags & motive.item_tags):
        reasons.append(f"{item.label} does not suit the motive '{motive.id}'")
    if not (spot.tags & motive.spot_tags):
        reasons.append(f"{spot.label} is not a sensible hiding place for '{motive.id}'")
    if not (clue.tags & motive.clue_tags):
        reasons.append(f"{clue.label} does not match the motive '{motive.id}'")
    joined = "; ".join(reasons) if reasons else "the pieces do not fit together"
    return f"(No story: {joined}.)"


def outcome_of(params: "StoryParams") -> str:
    motive = MOTIVES[params.motive]
    score = params.bravery + params.kindness + motive.honesty_bonus
    return "confessed" if score >= 11 else "found"


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    item: str
    motive: str
    spot: str
    clue: str
    seeker: str
    seeker_gender: str
    owner: str
    owner_gender: str
    culprit: str
    culprit_gender: str
    adult: str
    bravery: int = 6
    kindness: int = 5
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
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


def introduce(world: World, seeker: Entity, owner: Entity, culprit: Entity, item_cfg: MissingItem) -> None:
    world.say(world.setting.opening)
    world.say(
        f"{owner.id} had brought out {item_cfg.phrase}, and everybody wanted a turn to admire it."
    )
    world.say(
        f"{seeker.id} loved small puzzles, and {culprit.id} was close by, trying to look busy and ordinary."
    )


def discover_missing(world: World, owner: Entity, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when story time was about to begin, {owner.id} looked at the empty hook and gasped. "
        f'"The {item.label} is gone!"'
    )
    world.say(
        f"Children looked under the table and behind the easel. Everyone guessed except the child who had hidden the truth."
    )
    world.say(world.setting.hush)


def inspect_clue(world: World, seeker: Entity, clue: Clue) -> None:
    world.facts["clue_seen"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{seeker.id} knelt by the rug and found a clue. {clue.sentence}"
    )
    world.say(clue.point)


def ponder(world: World, seeker: Entity, motive: Motive, culprit: Entity, adult: Entity) -> None:
    world.say(
        f"{seeker.id} felt a flutter in {seeker.pronoun('possessive')} chest. {motive.brave_text}."
    )
    world.say(
        f"{adult.label_word.capitalize()} did not rush to blame anyone. "
        f'"A good detective looks carefully and speaks kindly," {adult.pronoun()} said.'
    )
    world.say(
        f"{seeker.id} looked at {culprit.id}, then at the clue, and chose bravery over whispering."
    )


def gentle_question(world: World, seeker: Entity, culprit: Entity, motive: Motive) -> None:
    world.facts["gentle_question"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f'{seeker.id} took a breath. "{culprit.id}," {seeker.pronoun()} asked softly, '
        f'"did you move the {world.get("item").label}? I am not trying to be mean. I just want to help."'
    )
    if world.facts.get("confessed", 0.0) >= THRESHOLD:
        world.say(
            f"{culprit.id}'s shoulders drooped. {culprit.pronoun().capitalize()} nodded and whispered, "
            f'"Yes. {motive.confession}"'
        )


def follow_clue(world: World, seeker: Entity, adult: Entity, spot: Spot, culprit: Entity) -> None:
    world.say(
        f"When no answer came at first, {seeker.id} and {adult.label_word} followed the clue to {spot.phrase}."
    )
    world.say(spot.reveal)
    item = world.get("item")
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{culprit.id} saw the item in {adult.pronoun('possessive')} hands and could not keep quiet anymore."
    )


def return_item(world: World, owner: Entity, culprit: Entity, motive: Motive) -> None:
    item = world.get("item")
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{culprit.id} carried the {item.label} back to {owner.id} with both hands."
    )
    world.say(
        f'"I should have asked first," {culprit.pronoun()} said. "{motive.moral}"'
    )


def close_story(world: World, seeker: Entity, owner: Entity, culprit: Entity, adult: Entity, motive: Motive) -> None:
    item = world.get("item")
    if world.facts.get("confessed", 0.0) >= THRESHOLD:
        world.say(
            f"{owner.id} hugged the {item.label} to {owner.pronoun('possessive')} chest, then gave {culprit.id} a small forgiving smile."
        )
        world.say(
            f'{adult.label_word.capitalize()} nodded. "That was brave detective work," {adult.pronoun()} said, '
            f'"and it was brave to tell the truth too."'
        )
    else:
        world.say(
            f"{owner.id} let out a long relieved breath when the {item.label} was found."
        )
        world.say(
            f'{adult.label_word.capitalize()} crouched beside the children. "Mysteries grow smaller when honesty gets bigger," '
            f'{adult.pronoun()} said.'
        )
    world.say(
        f"Soon the room was warm again, and the mystery had turned into a lesson about courage, kindness, and telling the truth."
    )
    world.say(
        f"After that, whenever something was missing in {world.setting.place}, {seeker.id} remembered that the best clue was not the paper scrap or thread at all, but the brave way to ask."
    )
    world.facts["moral"] = motive.moral


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    motive: Motive,
    spot: Spot,
    clue: Clue,
    seeker_name: str,
    seeker_gender: str,
    owner_name: str,
    owner_gender: str,
    culprit_name: str,
    culprit_gender: str,
    adult_type: str,
    bravery: int,
    kindness: int,
) -> World:
    world = World(setting)

    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_gender, role="culprit"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the teacher"))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, role="item"))
    hiding_spot = world.add(Entity(id="spot", kind="thing", type="spot", label=spot.label, role="spot"))

    seeker.memes["bravery"] = float(bravery)
    seeker.memes["kindness"] = float(kindness)
    culprit.memes["guilt"] = 1.0
    owner.memes["worry"] = 0.0
    owner.memes["relief"] = 0.0
    item.meters["missing"] = 0.0
    item.meters["found"] = 0.0
    world.facts["clue_seen"] = 0.0
    world.facts["gentle_question"] = 0.0
    world.facts["confessed"] = 0.0
    world.facts["honesty_bonus"] = motive.honesty_bonus
    world.facts["setting"] = setting
    world.facts["item_cfg"] = item_cfg
    world.facts["motive"] = motive
    world.facts["spot_cfg"] = spot
    world.facts["clue_cfg"] = clue
    world.facts["seeker"] = seeker
    world.facts["owner"] = owner
    world.facts["culprit"] = culprit
    world.facts["adult"] = adult

    introduce(world, seeker, owner, culprit, item_cfg)
    discover_missing(world, owner, item)
    world.para()

    inspect_clue(world, seeker, clue)
    ponder(world, seeker, motive, culprit, adult)
    gentle_question(world, seeker, culprit, motive)
    world.para()

    if world.facts.get("confessed", 0.0) >= THRESHOLD:
        return_item(world, owner, culprit, motive)
    else:
        follow_clue(world, seeker, adult, spot, culprit)
        world.say(
            f'"I was the one who moved it," {culprit.id} admitted at last. "{motive.confession}"'
        )
        world.say(
            f'{adult.label_word.capitalize()} listened, then said, "Next time, help with open hands and honest words."'
        )
    close_story(world, seeker, owner, culprit, adult, motive)
    world.facts["outcome"] = "confessed" if world.facts.get("confessed", 0.0) >= THRESHOLD else "found"
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when your stomach feels jumpy. It is not the same as being loud or never feeling scared."
        )
    ],
    "honesty": [
        (
            "Why is honesty important in a mystery?",
            "Honesty helps people stop guessing and start understanding what really happened. It also helps trust grow again after a mistake."
        )
    ],
    "ask_first": [
        (
            "Why should you ask before borrowing something?",
            "You should ask first because the thing belongs to someone else or is being used for a plan. Asking shows respect and keeps people from worrying."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what happened. In a mystery, clues guide careful thinking instead of wild guessing."
        )
    ],
    "surprise": [
        (
            "Can a surprise still cause trouble?",
            "Yes. A surprise can be meant kindly, but if it starts with hiding or taking something, it can make other people scared or confused."
        )
    ],
    "repair": [
        (
            "Is fixing something helpful?",
            "Fixing something can be helpful when you do it carefully and with permission. Good helping also includes telling the truth about what you did."
        )
    ],
    "tidy": [
        (
            "Can tidying ever confuse people?",
            "Yes. If you move an important thing and forget to tell anyone, people may think it is lost. Tidying works best when others know where things went."
        )
    ],
}
KNOWLEDGE_ORDER = ["clue", "bravery", "honesty", "ask_first", "surprise", "repair", "tidy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    item_cfg = f["item_cfg"]
    motive = f["motive"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "except" and "shorten" and centers on a missing {item_cfg.label}.',
        f"Tell a classroom mystery where {seeker.id} notices a clue, acts with bravery, and solves the problem through kindness instead of meanness.",
        f'Write a short child-facing mystery with a moral about honesty and asking first, where a child hides {item_cfg.phrase} because {motive.reason}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    owner = f["owner"]
    culprit = f["culprit"]
    adult = f["adult"]
    item_cfg = f["item_cfg"]
    motive = f["motive"]
    clue = f["clue_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {item_cfg.phrase} had gone missing just before story time. That made {owner.id} worried and turned the room quiet like a little whodunit."
        ),
        (
            f"What clue did {seeker.id} find?",
            f"{seeker.id} found {clue.label}. The clue mattered because it pointed toward how the item had been moved and what kind of plan was behind it."
        ),
        (
            f"Why was {seeker.id} brave?",
            f"{seeker.id} was brave because asking a careful question can feel scary when a friend might be upset. Still, {seeker.pronoun().capitalize()} chose to speak kindly and help the truth come out."
        ),
    ]

    if outcome == "confessed":
        qa.append(
            (
                f"Why did {culprit.id} confess?",
                f"{culprit.id} confessed after {seeker.id} asked gently instead of accusing. The kind question made room for honesty, and that is why the hidden reason finally came out."
            )
        )
        qa.append(
            (
                f"Why had {culprit.id} taken the {item_cfg.label}?",
                f"{culprit.id} had taken it because {motive.reason}. {motive.confession}"
            )
        )
    else:
        qa.append(
            (
                f"How was the missing {item_cfg.label} found?",
                f"{seeker.id} and the {adult.label_word} followed the clue to {spot.label}. They found the item there, and then {culprit.id} admitted the truth because hiding it no longer worked."
            )
        )
        qa.append(
            (
                f"What did {culprit.id} learn?",
                f"{culprit.id} learned that even a helpful idea can become a problem when it is secret. {motive.moral}"
            )
        )

    qa.append(
        (
            "How did the story end?",
            f"It ended with the room feeling calm again and the children understanding a better way to act next time. The mystery was solved, and the lesson about honesty stayed behind after the clues were gone."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    motive = world.facts["motive"]
    tags = {"clue", "bravery", "honesty", "ask_first", motive.id}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,I,M,Sp,C) :-
    setting(S), item(I), motive(M), spot(Sp), clue(C),
    setting_tag(S, PT), motive_place(M, PT),
    item_tag(I, IT), motive_item(M, IT),
    spot_tag(Sp, ST), motive_spot(M, ST),
    clue_tag(C, CT), motive_clue(M, CT).

score(B + K + Bonus) :- bravery(B), kindness(K), chosen_motive(M), honesty_bonus(M, Bonus).
outcome(confessed) :- score(V), V >= 11.
outcome(found) :- score(V), V < 11.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(setting.tags):
            lines.append(asp.fact("setting_tag", sid, tag))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for mid, motive in MOTIVES.items():
        lines.append(asp.fact("motive", mid))
        lines.append(asp.fact("honesty_bonus", mid, motive.honesty_bonus))
        for tag in sorted(motive.item_tags):
            lines.append(asp.fact("motive_item", mid, tag))
        for tag in sorted(motive.spot_tags):
            lines.append(asp.fact("motive_spot", mid, tag))
        for tag in sorted(motive.clue_tags):
            lines.append(asp.fact("motive_clue", mid, tag))
        for tag in sorted(motive.place_tags):
            lines.append(asp.fact("motive_place", mid, tag))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        for tag in sorted(spot.tags):
            lines.append(asp.fact("spot_tag", sid, tag))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("clue_tag", cid, tag))
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
            asp.fact("chosen_motive", params.motive),
            asp.fact("bravery", params.bravery),
            asp.fact("kindness", params.kindness),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for _ in range(50):
        try:
            p = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI / interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="classroom",
        item="ribbon",
        motive="repair",
        spot="art_drawer",
        clue="snipped_thread",
        seeker="Lily",
        seeker_gender="girl",
        owner="Ben",
        owner_gender="boy",
        culprit="Mia",
        culprit_gender="girl",
        adult="teacher",
        bravery=7,
        kindness=5,
    ),
    StoryParams(
        setting="library",
        item="bookmark",
        motive="surprise",
        spot="cushion_nook",
        clue="paper_star",
        seeker="Tom",
        seeker_gender="boy",
        owner="Ava",
        owner_gender="girl",
        culprit="Nora",
        culprit_gender="girl",
        adult="teacher",
        bravery=5,
        kindness=4,
    ),
    StoryParams(
        setting="playroom",
        item="paper_chain",
        motive="tidy",
        spot="cubby",
        clue="name_label",
        seeker="Max",
        seeker_gender="boy",
        owner="Zoe",
        owner_gender="girl",
        culprit="Ella",
        culprit_gender="girl",
        adult="teacher",
        bravery=6,
        kindness=6,
    ),
    StoryParams(
        setting="classroom",
        item="bookmark",
        motive="tidy",
        spot="cubby",
        clue="name_label",
        seeker="Lucy",
        seeker_gender="girl",
        owner="Sam",
        owner_gender="boy",
        culprit="Finn",
        culprit_gender="boy",
        adult="teacher",
        bravery=4,
        kindness=5,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle child-sized whodunit: a missing object, a clue, bravery, and honesty."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--adult", choices=["teacher"], default=None)
    ap.add_argument("--bravery", type=int, choices=range(3, 9))
    ap.add_argument("--kindness", type=int, choices=range(3, 9))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.motive and args.spot and args.clue:
        if not combo_valid(
            SETTINGS[args.setting],
            ITEMS[args.item],
            MOTIVES[args.motive],
            SPOTS[args.spot],
            CLUES[args.clue],
        ):
            raise StoryError(
                explain_rejection(
                    SETTINGS[args.setting],
                    ITEMS[args.item],
                    MOTIVES[args.motive],
                    SPOTS[args.spot],
                    CLUES[args.clue],
                )
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.motive is None or combo[2] == args.motive)
        and (args.spot is None or combo[3] == args.spot)
        and (args.clue is None or combo[4] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, motive_id, spot_id, clue_id = rng.choice(sorted(combos))
    used: set[str] = set()
    seeker, seeker_gender = _pick_name(rng, used)
    used.add(seeker)
    owner, owner_gender = _pick_name(rng, used)
    used.add(owner)
    culprit, culprit_gender = _pick_name(rng, used)
    adult = args.adult or "teacher"
    bravery = args.bravery if args.bravery is not None else rng.randint(4, 7)
    kindness = args.kindness if args.kindness is not None else rng.randint(4, 7)

    return StoryParams(
        setting=setting_id,
        item=item_id,
        motive=motive_id,
        spot=spot_id,
        clue=clue_id,
        seeker=seeker,
        seeker_gender=seeker_gender,
        owner=owner,
        owner_gender=owner_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        adult=adult,
        bravery=bravery,
        kindness=kindness,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        motive = MOTIVES[params.motive]
        spot = SPOTS[params.spot]
        clue = CLUES[params.clue]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not combo_valid(setting, item, motive, spot, clue):
        raise StoryError(explain_rejection(setting, item, motive, spot, clue))

    world = tell(
        setting=setting,
        item_cfg=item,
        motive=motive,
        spot=spot,
        clue=clue,
        seeker_name=params.seeker,
        seeker_gender=params.seeker_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        adult_type=params.adult,
        bravery=params.bravery,
        kindness=params.kindness,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, motive, spot, clue) combos:\n")
        for setting, item, motive, spot, clue in combos:
            print(f"  {setting:10} {item:12} {motive:8} {spot:13} {clue}")
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
            header = f"### {p.setting}: {p.item}, {p.motive}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
