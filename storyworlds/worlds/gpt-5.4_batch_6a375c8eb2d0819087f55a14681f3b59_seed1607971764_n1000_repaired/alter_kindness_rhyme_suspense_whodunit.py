#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py
====================================================================

A standalone story world for a tiny child-facing whodunit: during a friendly
rhyme recital, someone seems to have altered the last line on a poem card.
The mystery feels tense for a moment, but the world model prefers gentle causes:
a helper may have changed the card to protect a shy friend, or a gust may have
smudged it, or a small sibling may have copied the wrong rhyme by mistake.
The detective child follows clues, asks kindly, and the ending proves that
kindness solves more than blame.

Run it
------
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py --event recital --cause helper
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py --suspect wind
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/alter_kindness_rhyme_suspense_whodunit.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KIND_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Event:
    id: str
    place: str
    gathering: str
    object_phrase: str
    hiding_spot: str
    ending_image: str
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
class PoemCard:
    id: str
    theme: str
    first_line: str
    second_line: str
    true_last: str
    wrong_last: str
    clue_mark: str
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
class Cause:
    id: str
    culprit_kind: str
    kind_score: int
    deliberate: bool
    leaves_mark: str
    clue_sentence: str
    reveal_text: str
    repair_text: str
    motive_text: str
    lesson_text: str
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
class Reward:
    id: str
    label: str
    phrase: str
    ending_glow: str
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    card = world.get("card")
    detective = world.get("detective")
    owner = world.get("owner")
    if card.meters["altered"] < THRESHOLD:
        return out
    sig = ("alarm", "card")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspense"] += 1
    owner.memes["worry"] += 1
    world.get("room").meters["tension"] += 1
    out.append("__alarm__")
    return out


def _r_kind_choice(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes["asked_kindly"] < THRESHOLD:
        return out
    sig = ("kind_choice", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["calm"] += 1
    world.get("owner").memes["trust"] += 1
    if "suspect" in world.entities:
        world.get("suspect").memes["relief"] += 1
    out.append("__kind__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    card = world.get("card")
    if card.meters["restored"] < THRESHOLD:
        return out
    sig = ("repair", card.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["tension"] = 0.0
    world.get("owner").memes["worry"] = 0.0
    world.get("detective").memes["pride"] += 1
    out.append("__repair__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="alarm", tag="emotional", apply=_r_alarm),
    Rule(name="kind_choice", tag="social", apply=_r_kind_choice),
    Rule(name="repair", tag="resolution", apply=_r_repair),
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
        for s in produced:
            world.say(s)
    return produced


EVENTS = {
    "recital": Event(
        id="recital",
        place="the library reading corner",
        gathering="the Little Lantern Rhyme Recital",
        object_phrase="a bright poem card clipped to a small stand",
        hiding_spot="beside the book return slot",
        ending_image="The rhyme corner felt warm again, and the little stand no longer looked lonely.",
        tags={"library", "recital", "rhyme"},
    ),
    "fair": Event(
        id="fair",
        place="the school hall",
        gathering="the Spring Rhyme Fair",
        object_phrase="a painted poem card resting on a blue easel",
        hiding_spot="behind the curtain near the stage steps",
        ending_image="The hall rang with happy claps, and the blue easel stood straight and proud.",
        tags={"school", "fair", "rhyme"},
    ),
    "picnic": Event(
        id="picnic",
        place="the park bandstand",
        gathering="the Picnic Poem Circle",
        object_phrase="a poem card tucked into a wooden frame",
        hiding_spot="under the bench by the lemonade basket",
        ending_image="The bandstand seemed bright again, and the wooden frame caught the soft afternoon sun.",
        tags={"park", "picnic", "rhyme"},
    ),
}

CARDS = {
    "moon": PoemCard(
        id="moon",
        theme="moon",
        first_line="The moon wore a silver tune,",
        second_line="and hummed above the sleepy dune.",
        true_last="Soon I would sing my rhyme by noon.",
        wrong_last="Soon I would croak beside a spoon.",
        clue_mark="a tiny silver smudge",
        tags={"moon", "rhyme"},
    ),
    "cake": PoemCard(
        id="cake",
        theme="cake",
        first_line="A baker twirled beside a cake,",
        second_line="while frosting shone upon the rake.",
        true_last="I saved one cherry for the break.",
        wrong_last="I hid one herring in the lake.",
        clue_mark="a pink sticky dot",
        tags={"cake", "rhyme"},
    ),
    "kite": PoemCard(
        id="kite",
        theme="kite",
        first_line="A kite flew high in lemon light,",
        second_line="and dipped above the hill so bright.",
        true_last="At last it bowed and slept at night.",
        wrong_last="At last it growled and bit a bite.",
        clue_mark="a line pulled slightly sideways",
        tags={"kite", "rhyme"},
    ),
}

CAUSES = {
    "helper": Cause(
        id="helper",
        culprit_kind="child",
        kind_score=3,
        deliberate=True,
        leaves_mark="a careful second sheet tucked underneath",
        clue_sentence="The card was not ripped or crumpled. Someone had laid a new line on top, neat and gentle, as if trying to help instead of harm.",
        reveal_text="It turned out that the helper had altered the last line because the owner had frozen during practice and whispered a different rhyme by accident.",
        repair_text="Together they lifted the extra sheet, smoothed the real poem, and practiced the ending in a soft, brave voice.",
        motive_text="The helper wanted to spare a friend's blush, but keeping the change secret only made the mystery bigger.",
        lesson_text="Kind help works best when it tells the truth too.",
        tags={"helper", "kindness", "paper"},
    ),
    "sibling": Cause(
        id="sibling",
        culprit_kind="child",
        kind_score=2,
        deliberate=True,
        leaves_mark="a stubby crayon tucked near the stand",
        clue_sentence="The strange line had bouncy letters and one backward word. It looked less like a trick and more like a small hand copying a rhyme too fast.",
        reveal_text="It turned out that the little sibling had altered the card while trying to make the poem sound funnier and more rhymey.",
        repair_text="The older children smiled, fetched a clean card, and let the little one help by holding the tape instead of changing the words.",
        motive_text="The small sibling was trying to join the excitement, not ruin the recital.",
        lesson_text="Even a mistake deserves a gentle answer when the heart behind it was eager, not mean.",
        tags={"sibling", "crayon", "kindness"},
    ),
    "wind": Cause(
        id="wind",
        culprit_kind="nature",
        kind_score=3,
        deliberate=False,
        leaves_mark="the clip hanging loose and a corner bent by a draft",
        clue_sentence="Nothing smelled sneaky at all. The top corner fluttered, and the card's clip hung sideways, as if a gust had nibbled the page.",
        reveal_text="It turned out that nobody had changed the poem on purpose; a gust had flipped the wrong practice strip over the real last line.",
        repair_text="They clipped the card down tightly and laughed with relief when the true rhyme peeked out again.",
        motive_text="The wind had only jostled the papers, but for a minute it made everyone wonder.",
        lesson_text="Sometimes a mystery is not about blame at all, only about looking carefully.",
        tags={"wind", "nature", "paper"},
    ),
    "teacher": Cause(
        id="teacher",
        culprit_kind="adult",
        kind_score=3,
        deliberate=True,
        leaves_mark="a neat pencil note at the bottom edge",
        clue_sentence="The new line was written in tidy grown-up letters. It looked like a correction, but the little pencil note sounded worried, not stern.",
        reveal_text="It turned out that the teacher had altered the ending during rehearsal because she thought the true line was too hard to remember.",
        repair_text="When the owner said they loved the original rhyme, the teacher smiled, erased the note, and helped them clap the beats together.",
        motive_text="The teacher meant to make the poem easier, not to take it away.",
        lesson_text="Even grown-ups can fix a mistake by listening kindly.",
        tags={"teacher", "pencil", "kindness"},
    ),
}

REWARDS = {
    "bookmark": Reward(
        id="bookmark",
        label="star bookmark",
        phrase="a starry bookmark",
        ending_glow="It flashed like a tiny gold clue solved at last.",
        tags={"bookmark", "reward"},
    ),
    "sticker": Reward(
        id="sticker",
        label="moon sticker",
        phrase="a shining moon sticker",
        ending_glow="It gleamed on the poem stand like a quiet smile.",
        tags={"sticker", "reward"},
    ),
    "bell": Reward(
        id="bell",
        label="silver bell ribbon",
        phrase="a silver bell ribbon",
        ending_glow="It chimed softly each time someone clapped.",
        tags={"bell", "reward"},
    ),
}

DETECTIVE_NAMES = ["Mina", "Tess", "Rory", "Ben", "Nora", "Eli", "Ada", "Sam", "Lila", "Finn"]
OWNER_NAMES = ["June", "Poppy", "Milo", "Iris", "Theo", "Ruby", "Luca", "Hazel"]
HELPER_NAMES = ["Kit", "Mara", "Owen", "Pia", "Ned", "Cora"]
TRAITS = ["patient", "careful", "bright", "gentle", "steady", "thoughtful"]


def cause_fits(event_id: str, cause_id: str) -> bool:
    if cause_id == "wind":
        return event_id in {"picnic", "fair"}
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for event_id in EVENTS:
        for card_id in CARDS:
            for cause_id in CAUSES:
                if cause_fits(event_id, cause_id) and CAUSES[cause_id].kind_score >= KIND_MIN:
                    combos.append((event_id, card_id, cause_id))
    return combos


def kind_causes() -> list[str]:
    return sorted(c.id for c in CAUSES.values() if c.kind_score >= KIND_MIN)


@dataclass
class StoryParams:
    event: str
    card: str
    cause: str
    reward: str
    detective: str
    detective_gender: str
    owner: str
    owner_gender: str
    helper_name: str
    helper_gender: str
    teacher_name: str = "Ms. Fern"
    trait: str = "careful"
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


def predict_culprit(world: World, cause: Cause) -> dict:
    sim = world.copy()
    card = sim.get("card")
    card.meters["altered"] += 1
    sim.facts["simulated_cause"] = cause.id
    propagate(sim, narrate=False)
    suspect = "wind" if cause.culprit_kind == "nature" else sim.get("suspect").id
    return {
        "alarm": sim.get("room").meters["tension"],
        "suspect": suspect,
        "deliberate": cause.deliberate,
    }


def introduce(world: World, event: Event, detective: Entity, owner: Entity, reward: Reward) -> None:
    detective.memes["care"] += 1
    owner.memes["hope"] += 1
    world.say(
        f"On a bright afternoon at {event.place}, everyone gathered for {event.gathering}. "
        f"{owner.id} would read a poem for the prize, {reward.phrase}, and {detective.id} stayed close to cheer."
    )


def set_scene(world: World, event: Event, card: PoemCard) -> None:
    world.say(
        f"On the little stage stood {event.object_phrase}. Its first two lines were easy to love: "
        f'"{card.first_line}" and "{card.second_line}"'
    )


def introduce_rhyme(world: World, owner: Entity, card: PoemCard) -> None:
    owner.memes["pride"] += 1
    world.say(
        f'{owner.id} had practiced the last line all morning: "{card.true_last}" '
        f'The rhyme made {owner.pronoun("object")} smile every time.'
    )


def discover_alteration(world: World, event: Event, detective: Entity, owner: Entity, card_cfg: PoemCard) -> None:
    card = world.get("card")
    card.meters["altered"] += 1
    card.attrs["visible_last"] = card_cfg.wrong_last
    world.facts["visible_last"] = card_cfg.wrong_last
    propagate(world, narrate=False)
    world.say(
        f"But when {owner.id} stepped toward the stand, the last line was wrong. "
        f'Where "{card_cfg.true_last}" should have been, the card now read "{card_cfg.wrong_last}"'
    )
    world.say(
        f"{detective.id} felt a little shiver of suspense. Someone had altered the rhyme, or something had."
    )


def gather_clue(world: World, cause: Cause, card_cfg: PoemCard, suspect: Entity) -> None:
    suspect.memes["noticed"] += 1
    world.say(
        f"{detective_name(world)} looked closely and spotted {cause.leaves_mark} and {card_cfg.clue_mark}. "
        f"{cause.clue_sentence}"
    )


def detective_name(world: World) -> str:
    return world.get("detective").id


def choose_kind_method(world: World, detective: Entity, owner: Entity, suspect: Entity) -> None:
    detective.memes["asked_kindly"] += 1
    propagate(world, narrate=False)
    if suspect.type == "wind":
        world.say(
            f'Instead of pointing at anyone, {detective.id} took a slow breath. '
            f'"Let\'s look carefully before we blame," {detective.pronoun()} said.'
        )
    else:
        world.say(
            f'{detective.id} did not accuse {suspect.id}. Instead, {detective.pronoun()} spoke softly: '
            f'"Did you see what happened to the poem card? You can tell the truth. We want to help {owner.id} read."'
        )


def reveal(world: World, cause: Cause, suspect: Entity, owner: Entity) -> None:
    suspect.memes["truth"] += 1
    owner.memes["hope"] += 1
    if suspect.type == "wind":
        world.say(
            f"Soon the loose clip tapped the stand again, and the bent corner lifted by itself. "
            f"{cause.reveal_text}"
        )
    else:
        pre = f"{suspect.id}'s shoulders dropped with relief."
        world.say(f"{pre} {cause.reveal_text}")
    world.say(cause.motive_text)


def repair(world: World, cause: Cause, owner: Entity, reward: Reward) -> None:
    card = world.get("card")
    card.meters["restored"] += 1
    card.attrs["visible_last"] = world.facts["true_last"]
    world.facts["visible_last"] = world.facts["true_last"]
    propagate(world, narrate=False)
    world.say(cause.repair_text)
    world.say(
        f'Soon {owner.id} read the true ending aloud: "{world.facts["true_last"]}" '
        f'Everyone clapped, and {reward.ending_glow}'
    )


def ending(world: World, event: Event, detective: Entity, owner: Entity, cause: Cause) -> None:
    detective.memes["kindness"] += 1
    owner.memes["bravery"] += 1
    if "suspect" in world.entities and world.get("suspect").type != "wind":
        world.get("suspect").memes["belonging"] += 1
    world.say(
        f"{cause.lesson_text} {event.ending_image}"
    )
    world.say(
        f"{detective.id} grinned at {owner.id}, and the mystery that had felt so prickly a moment before now seemed small enough to tuck away with the poem."
    )


def tell(
    event: Event,
    card_cfg: PoemCard,
    cause: Cause,
    reward: Reward,
    detective_name_value: str = "Mina",
    detective_gender: str = "girl",
    owner_name_value: str = "June",
    owner_gender: str = "girl",
    helper_name_value: str = "Kit",
    helper_gender: str = "boy",
    teacher_name_value: str = "Ms. Fern",
    trait: str = "careful",
) -> World:
    world = World()

    detective = world.add(Entity(
        id=detective_name_value,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=[trait],
        attrs={"trait": trait},
        tags={"detective"},
    ))
    owner = world.add(Entity(
        id=owner_name_value,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=["shy", "hopeful"],
        attrs={"shy": True},
        tags={"owner"},
    ))
    teacher = world.add(Entity(
        id=teacher_name_value,
        kind="character",
        type="teacher",
        role="teacher",
        traits=["kind"],
        attrs={"adult": True},
        tags={"teacher"},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=event.place,
        role="setting",
        attrs={},
        tags=set(event.tags),
    ))
    card = world.add(Entity(
        id="card",
        kind="thing",
        type="poem_card",
        label="poem card",
        role="clue",
        attrs={"visible_last": card_cfg.true_last},
        tags=set(card_cfg.tags),
    ))

    if cause.id == "teacher":
        suspect = teacher
    elif cause.id == "wind":
        suspect = world.add(Entity(
            id="wind",
            kind="thing",
            type="wind",
            label="the breeze",
            role="suspect",
            attrs={},
            tags={"wind"},
        ))
    else:
        suspect = world.add(Entity(
            id=helper_name_value,
            kind="character",
            type=helper_gender,
            role="suspect",
            traits=["eager"],
            attrs={"nearby": True},
            tags={"helper"},
        ))

    world.facts.update(
        event=event,
        card_cfg=card_cfg,
        cause=cause,
        reward=reward,
        detective=detective,
        owner=owner,
        teacher=teacher,
        suspect=suspect,
        true_last=card_cfg.true_last,
        visible_last=card_cfg.true_last,
        culprit_kind=cause.culprit_kind,
        deliberate=cause.deliberate,
        hidden_mark=cause.leaves_mark,
        kindness_used=False,
        restored=False,
    )

    introduce(world, event, detective, owner, reward)
    set_scene(world, event, card_cfg)
    introduce_rhyme(world, owner, card_cfg)

    world.para()
    discover_alteration(world, event, detective, owner, card_cfg)

    pred = predict_culprit(world, cause)
    world.facts["predicted_alarm"] = pred["alarm"]
    world.facts["predicted_suspect"] = pred["suspect"]
    gather_clue(world, cause, card_cfg, suspect)

    world.para()
    choose_kind_method(world, detective, owner, suspect)
    world.facts["kindness_used"] = True
    reveal(world, cause, suspect, owner)

    world.para()
    repair(world, cause, owner, reward)
    world.facts["restored"] = True
    ending(world, event, detective, owner, cause)

    return world


KNOWLEDGE = {
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words have matching end sounds, like moon and tune. Rhymes make poems feel bouncy and easy to remember."
    )],
    "poem_card": [(
        "What is a poem card?",
        "A poem card is a small sheet that holds the lines someone plans to read aloud. It helps a reader remember the right words."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. In a mystery, clues help you notice what really happened."
    )],
    "kindness": [(
        "Why does kindness help in a mystery?",
        "Kindness helps people feel safe enough to tell the truth. When someone is calm instead of mean, the mystery can be solved more honestly."
    )],
    "wind": [(
        "How can wind move paper?",
        "Wind pushes light things like paper and can flip a corner or loosen a page. That can make a paper look changed even when nobody meant to change it."
    )],
    "mistake": [(
        "What is the difference between a mistake and a mean trick?",
        "A mistake happens when someone gets something wrong without trying to hurt anyone. A mean trick is done on purpose to upset someone."
    )],
    "library": [(
        "What is a library reading corner?",
        "A library reading corner is a quiet place where people sit close together to hear stories or poems. It is made for listening and sharing words."
    )],
    "school": [(
        "What happens at a school fair?",
        "A school fair is a special event where children share games, art, songs, or poems. Families and teachers come to watch and clap."
    )],
    "park": [(
        "Why is paper harder to keep still outside?",
        "Outside air moves around more, so paper can flutter or bend. That is why clips and frames help hold it steady."
    )],
}

KNOWLEDGE_ORDER = ["rhyme", "poem_card", "clue", "kindness", "wind", "mistake", "library", "school", "park"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    event = f["event"]
    owner = f["owner"]
    detective = f["detective"]
    cause = f["cause"]
    prompts = [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the word "alter" and a poem read at {event.gathering}.',
        f"Tell a suspenseful but kind mystery where {detective.id} notices that {owner.id}'s rhyme card has been altered just before a performance.",
        "Write a simple mystery in which clues, rhymes, and kindness matter more than blame."
    ]
    if cause.id == "wind":
        prompts.append("Make the mystery feel tense at first, then reveal that nobody was being mean at all.")
    else:
        prompts.append("Let the detective solve the mystery by asking gentle questions instead of accusing anyone.")
    return prompts


def pair_description(world: World) -> str:
    detective = world.get("detective")
    owner = world.get("owner")
    return f"{detective.id} and {owner.id}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    event = f["event"]
    owner = f["owner"]
    detective = f["detective"]
    cause = f["cause"]
    suspect = f["suspect"]
    reward = f["reward"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_description(world)}, two children at {event.gathering}. {detective.id} tries to solve the little mystery so {owner.id} can read the poem."
        ),
        (
            "What was wrong with the poem card?",
            f"The last line had been altered, so the card showed the wrong rhyme instead of the true ending. That made the reading feel suddenly uncertain and turned the poem into a mystery."
        ),
        (
            f"Why did {detective.id} feel suspense?",
            f"{detective.id} saw that the last line had changed just before {owner.id} was meant to read aloud. The mystery mattered because {owner.id} might freeze or feel embarrassed in front of everyone."
        ),
        (
            f"How did {detective.id} solve the mystery?",
            f"{detective.id} looked for clues and spoke kindly instead of blaming anyone. That gentle choice helped the truth come out without making the room feel harsher."
        ),
    ]
    if suspect.type == "wind":
        qa.append((
            "Who altered the card?",
            "Nobody changed it on purpose. A gust had shifted the paper, and the bent clip helped the children notice what really happened."
        ))
    else:
        qa.append((
            "Who altered the card and why?",
            f"It was {suspect.id}. {cause.reveal_text} {cause.motive_text}"
        ))
    qa.append((
        "How did the children fix the problem?",
        f"{cause.repair_text} After that, {owner.id} could read the true rhyme and still try for {reward.phrase}."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the real rhyme restored and everyone calmer again. The solved mystery showed that kindness was the best clue to carry to the end."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"rhyme", "poem_card", "clue", "kindness"}
    event = f["event"]
    if event.id == "recital":
        tags.add("library")
    elif event.id == "fair":
        tags.add("school")
    elif event.id == "picnic":
        tags.add("park")
    if f["cause"].id == "wind":
        tags.add("wind")
    else:
        tags.add("mistake")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        event="recital",
        card="moon",
        cause="helper",
        reward="bookmark",
        detective="Mina",
        detective_gender="girl",
        owner="June",
        owner_gender="girl",
        helper_name="Kit",
        helper_gender="boy",
        teacher_name="Ms. Fern",
        trait="careful",
    ),
    StoryParams(
        event="fair",
        card="cake",
        cause="sibling",
        reward="sticker",
        detective="Eli",
        detective_gender="boy",
        owner="Ruby",
        owner_gender="girl",
        helper_name="Pia",
        helper_gender="girl",
        teacher_name="Ms. Fern",
        trait="patient",
    ),
    StoryParams(
        event="picnic",
        card="kite",
        cause="wind",
        reward="bell",
        detective="Ada",
        detective_gender="girl",
        owner="Theo",
        owner_gender="boy",
        helper_name="Ned",
        helper_gender="boy",
        teacher_name="Ms. Fern",
        trait="steady",
    ),
    StoryParams(
        event="fair",
        card="moon",
        cause="teacher",
        reward="bookmark",
        detective="Finn",
        detective_gender="boy",
        owner="Hazel",
        owner_gender="girl",
        helper_name="Cora",
        helper_gender="girl",
        teacher_name="Ms. Fern",
        trait="thoughtful",
    ),
]


def explain_rejection(event_id: str, cause_id: str) -> str:
    if cause_id == "wind" and event_id == "recital":
        return "(No story: the library reading corner is indoors, so a gust strong enough to alter the card is not reasonable here. Try the fair or picnic instead.)"
    return "(No story: that combination does not fit this little mystery world.)"


ASP_RULES = r"""
kind_cause(C) :- cause(C), kind_score(C, K), kind_min(M), K >= M.
fits(E, wind) :- outdoor(E).
fits(E, C)    :- cause(C), C != wind.
valid(E, P, C) :- event(E), poem(P), kind_cause(C), fits(E, C).

shown_suspect(wind) :- chosen_cause(wind).
shown_suspect(person) :- chosen_cause(C), culprit_kind(C, child).
shown_suspect(person) :- chosen_cause(C), culprit_kind(C, adult).

outcome(restored) :- valid(chosen_event_id, chosen_poem_id, chosen_cause_id).
chosen_event_id :- chosen_event(_).
chosen_poem_id  :- chosen_poem(_).
chosen_cause_id :- chosen_cause(_).

#show valid/3.
#show kind_cause/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for event_id, event in EVENTS.items():
        lines.append(asp.fact("event", event_id))
        if event_id in {"fair", "picnic"}:
            lines.append(asp.fact("outdoor", event_id))
    for card_id in CARDS:
        lines.append(asp.fact("poem", card_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("kind_score", cause_id, cause.kind_score))
        lines.append(asp.fact("culprit_kind", cause_id, cause.culprit_kind))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", ""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_causes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", ""))
    return sorted(c for (c,) in asp.atoms(model, "kind_cause"))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    if set(asp_kind_causes()) == set(kind_causes()):
        print(f"OK: kind causes match ({', '.join(kind_causes())}).")
    else:
        rc = 1
        print("MISMATCH in kind causes.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolved story is empty")
        print("OK: default resolve/generate passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle rhyming whodunit where a poem card seems altered and kindness solves the mystery."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--card", choices=CARDS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in DETECTIVE_NAMES if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.event and args.cause and not cause_fits(args.event, args.cause):
        raise StoryError(explain_rejection(args.event, args.cause))
    if args.cause and CAUSES[args.cause].kind_score < KIND_MIN:
        raise StoryError("(No story: that cause is too unkind for this world.)")

    combos = [
        c for c in valid_combos()
        if (args.event is None or c[0] == args.event)
        and (args.card is None or c[1] == args.card)
        and (args.cause is None or c[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    event_id, card_id, cause_id = rng.choice(sorted(combos))
    reward_id = args.reward or rng.choice(sorted(REWARDS))
    detective, dg = _pick_child(rng)
    owner, og = _pick_child(rng, avoid=detective)
    helper_name = _pick_name(rng, HELPER_NAMES, avoid=owner)
    helper_gender = rng.choice(["girl", "boy"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        event=event_id,
        card=card_id,
        cause=cause_id,
        reward=reward_id,
        detective=detective,
        detective_gender=dg,
        owner=owner,
        owner_gender=og,
        helper_name=helper_name,
        helper_gender=helper_gender,
        teacher_name="Ms. Fern",
        trait=trait,
    )


def _get_required(mapping: dict, key: str, field_name: str):
    if key not in mapping:
        raise StoryError(f"(Invalid {field_name}: {key})")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    event = _get_required(EVENTS, params.event, "event")
    card = _get_required(CARDS, params.card, "card")
    cause = _get_required(CAUSES, params.cause, "cause")
    reward = _get_required(REWARDS, params.reward, "reward")
    if not cause_fits(params.event, params.cause):
        raise StoryError(explain_rejection(params.event, params.cause))
    if cause.kind_score < KIND_MIN:
        raise StoryError("(No story: that cause is too unkind for this world.)")

    world = tell(
        event=event,
        card_cfg=card,
        cause=cause,
        reward=reward,
        detective_name_value=params.detective,
        detective_gender=params.detective_gender,
        owner_name_value=params.owner,
        owner_gender=params.owner_gender,
        helper_name_value=params.helper_name,
        helper_gender=params.helper_gender,
        teacher_name_value=params.teacher_name,
        trait=params.trait,
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
        print(asp_program("", ""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, card, cause) combos:\n")
        for event_id, card_id, cause_id in combos:
            print(f"  {event_id:8} {card_id:6} {cause_id}")
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
            header = f"### {p.event}: {p.card} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
