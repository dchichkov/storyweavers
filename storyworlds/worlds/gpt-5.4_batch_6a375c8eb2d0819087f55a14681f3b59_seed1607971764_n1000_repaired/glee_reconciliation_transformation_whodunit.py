#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/glee_reconciliation_transformation_whodunit.py
============================================================================

A small, child-facing whodunit storyworld about a costume mystery at a tiny
school show. A costume seems to vanish; the hero blurts out the wrong suspect;
clues lead to a kind helper who transformed the damaged costume to save the
performance; then the children reconcile and step onstage in glee.

The domain is intentionally narrow and constraint-checked. Not every helper can
reasonably fix every costume problem. The Python reasonableness gate and the
inline ASP twin both enforce the same compatibility rule:

    helper can fix (theme, accident) iff
        the helper knows that transformation theme
        and has the right kind of fix for that accident

Run it
------
    python storyworlds/worlds/gpt-5.4/glee_reconciliation_transformation_whodunit.py
    python storyworlds/worlds/gpt-5.4/glee_reconciliation_transformation_whodunit.py --theme butterfly --accident rip --helper nana_rosa
    python storyworlds/worlds/gpt-5.4/glee_reconciliation_transformation_whodunit.py --theme flower --accident stain --helper coach_lee
    python storyworlds/worlds/gpt-5.4/glee_reconciliation_transformation_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/glee_reconciliation_transformation_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/glee_reconciliation_transformation_whodunit.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "grandmother", "coach"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Theme:
    id: str
    start_form: str
    end_form: str
    costume_name: str
    parade_name: str
    display_spot: str
    transformed_text: str
    opening_image: str
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
class Accident:
    id: str
    problem_text: str
    clue_text: str
    discovery_text: str
    fix_need: str
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
class HelperCfg:
    id: str
    name: str
    type: str
    title: str
    station: str
    clue: str
    repair_text: str
    reveal_text: str
    themes: set[str] = field(default_factory=set)
    accidents: set[str] = field(default_factory=set)
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


def _r_show_risk(world: World) -> list[str]:
    costume = world.entities.get("costume")
    hero = world.entities.get("hero")
    if costume is None or hero is None:
        return []
    if costume.meters["damaged"] < THRESHOLD:
        return []
    sig = ("show_risk", costume.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("stage").meters["show_risk"] += 1
    hero.memes["worry"] += 1
    return []


def _r_wrong_blame(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if hero.memes["accused_friend"] < THRESHOLD:
        return []
    if friend.attrs.get("innocent") is not True:
        return []
    sig = ("wrong_blame", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    hero.memes["guilt_seed"] += 1
    world.get("bond").meters["strained"] += 1
    return []


def _r_costume_ready(world: World) -> list[str]:
    costume = world.entities.get("costume")
    if costume is None:
        return []
    if costume.meters["mended"] < THRESHOLD or costume.meters["transformed"] < THRESHOLD:
        return []
    sig = ("costume_ready", costume.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("stage").meters["ready"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if hero.memes["apologized"] < THRESHOLD or friend.memes["forgave"] < THRESHOLD:
        return []
    sig = ("reconcile", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("bond").meters["strained"] = 0.0
    world.get("bond").meters["repaired"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="show_risk", tag="physical", apply=_r_show_risk),
    Rule(name="wrong_blame", tag="social", apply=_r_wrong_blame),
    Rule(name="costume_ready", tag="physical", apply=_r_costume_ready),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


THEMES = {
    "butterfly": Theme(
        id="butterfly",
        start_form="a shy little cocoon",
        end_form="a bright butterfly",
        costume_name="costume",
        parade_name="the Transformation Parade",
        display_spot="the costume hook by the blue curtain",
        transformed_text="a pair of painted wings stitched over the back and two soft silver feelers above the hood",
        opening_image="The hall smelled like paste and crayons, and the costume hook by the blue curtain looked important as a treasure shelf.",
        tags={"butterfly", "transformation", "wings"},
    ),
    "frog": Theme(
        id="frog",
        start_form="a wiggly tadpole",
        end_form="a springy frog",
        costume_name="costume",
        parade_name="the Transformation Parade",
        display_spot="the peg beside the music stand",
        transformed_text="two springy green legs and a neat round frog collar where the old tail panel had been",
        opening_image="The hall buzzed with whispers, and the peg beside the music stand held the morning's most important costume.",
        tags={"frog", "transformation", "legs"},
    ),
    "flower": Theme(
        id="flower",
        start_form="a tiny seed",
        end_form="a tall flower",
        costume_name="costume",
        parade_name="the Transformation Parade",
        display_spot="the little rack beside the window",
        transformed_text="a ring of bright petals and a sunny yellow center that turned the plain cape into a blossom",
        opening_image="Sunshine slid through the classroom window, and the little rack beside it held a costume everyone wanted to see finished.",
        tags={"flower", "transformation", "petals"},
    ),
}

ACCIDENTS = {
    "rip": Accident(
        id="rip",
        problem_text="One side seam had ripped open from hem to waist.",
        clue_text="a tiny loop of repair thread",
        discovery_text="the cloth hung open where it should have lain smooth",
        fix_need="something careful had to be sewn or tied before the show could begin",
        tags={"rip", "repair"},
    ),
    "stain": Accident(
        id="stain",
        problem_text="A round purple juice stain had bloomed across the front.",
        clue_text="a dusty sparkle stuck in the sticky patch",
        discovery_text="the dark blotch sat right in the middle where everyone would look first",
        fix_need="the front needed to be covered or remade so the stain would not spoil the show",
        tags={"stain", "repair"},
    ),
    "loose_strap": Accident(
        id="loose_strap",
        problem_text="The neck strap had come loose and dangled like a tired string.",
        clue_text="a shiny snap on the floor",
        discovery_text="the top kept sliding sideways instead of sitting straight",
        fix_need="the top had to be fastened firmly or the costume would not stay on",
        tags={"strap", "repair"},
    ),
}

HELPERS = {
    "nana_rosa": HelperCfg(
        id="nana_rosa",
        name="Nana Rosa",
        type="grandmother",
        title="the costume volunteer",
        station="the sewing table near the folded curtains",
        clue="a curl of silver thread",
        repair_text="had carried the costume to the sewing table, mended the damage, and added just enough new cloth to help the change look magical",
        reveal_text='\"I did take it,\" Nana Rosa said, lifting the costume gently. \"I found the damage and hurried to save your turn onstage.\"',
        themes={"butterfly", "frog", "flower"},
        accidents={"rip", "loose_strap"},
        tags={"sewing", "thread", "apology"},
    ),
    "mr_piper": HelperCfg(
        id="mr_piper",
        name="Mr. Piper",
        type="teacher",
        title="the art teacher",
        station="the art cart by the sink",
        clue="a dusting of gold sparkle paste",
        repair_text="had whisked the costume to the art cart, covered the trouble spot, and turned the plain front into the show's bright final shape",
        reveal_text='\"Mysteries are easier with clues than guesses,\" Mr. Piper said kindly. \"The stain looked sad, so I changed it into part of the costume.\"',
        themes={"butterfly", "flower"},
        accidents={"stain"},
        tags={"art", "paste", "apology"},
    ),
    "coach_lee": HelperCfg(
        id="coach_lee",
        name="Coach Lee",
        type="coach",
        title="the movement coach",
        station="the prop bench by the gym door",
        clue="a neat green felt crumb beside a snap",
        repair_text="had taken the costume to the prop bench, fastened it tight, and rebuilt the loose part into something the hero could hop and twirl in",
        reveal_text='\"I borrowed it for a minute,\" Coach Lee said. \"A wobbly costume makes a wobbly parade, so I fixed it before anyone tripped.\"',
        themes={"frog"},
        accidents={"loose_strap"},
        tags={"felt", "snap", "apology"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Ava", "Ivy", "Maya", "Zoe"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Finn", "Max", "Theo", "Eli", "Sam"]
TRAITS = ["careful", "curious", "eager", "thoughtful", "quick", "bright"]


def can_fix(theme_id: str, accident_id: str, helper_id: str) -> bool:
    if theme_id not in THEMES or accident_id not in ACCIDENTS or helper_id not in HELPERS:
        return False
    helper = HELPERS[helper_id]
    return theme_id in helper.themes and accident_id in helper.accidents


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in sorted(THEMES):
        for accident_id in sorted(ACCIDENTS):
            for helper_id in sorted(HELPERS):
                if can_fix(theme_id, accident_id, helper_id):
                    combos.append((theme_id, accident_id, helper_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    accident: str
    helper: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
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


def accident_happens(world: World, hero: Entity, costume: Entity, accident: Accident) -> None:
    costume.meters["damaged"] += 1
    costume.attrs["accident_id"] = accident.id
    costume.attrs["problem_text"] = accident.problem_text
    propagate(world, narrate=False)
    hero.memes["alarm"] += 1
    world.say(
        f"{hero.id} had made a costume to begin as {world.facts['theme'].start_form} and end as "
        f"{world.facts['theme'].end_form}. But when {hero.pronoun()} checked it before the parade, "
        f"{accident.discovery_text}. {accident.problem_text}"
    )
    world.say(
        f"If nothing changed, {hero.pronoun('possessive')} big moment in {world.facts['theme'].parade_name} would be spoiled."
    )


def vanish(world: World, hero: Entity, friend: Entity, theme: Theme, accident: Accident, helper: HelperCfg) -> None:
    costume = world.get("costume")
    costume.location = helper.station
    costume.meters["missing"] += 1
    hero.memes["suspicion"] += 1
    world.say(
        f"{hero.id} set the costume on {theme.display_spot} for one quick minute and ran to wash sticky fingers. "
        f"When {hero.pronoun()} came back, the hook was empty."
    )
    world.say(
        f'"The Case of the Vanishing Costume," {hero.id} whispered. On the floor lay {accident.clue_text}.'
    )
    world.say(
        f"{friend.id} was the only one nearby, holding a box of parade ribbons and blinking in surprise."
    )


def accuse(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["accused_friend"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Did you take it?" {hero.id} asked {friend.id} too fast.'
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f'{friend.id} drew back. "No," {friend.pronoun()} said quietly. "I wanted to help, not hide it."'
        )
    else:
        world.say(
            f'{friend.id} shook {friend.pronoun("possessive")} head. "No. I did not touch it."'
        )


def investigate(world: World, hero: Entity, friend: Entity, helper: HelperCfg, accident: Accident) -> None:
    friend.memes["kindness"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"For one little breath, {hero.id} wanted to stay cross. Then {friend.id} pointed at the floor."
    )
    world.say(
        f'"If I had hidden it," {friend.pronoun()} said, "why would I leave {helper.clue} behind?" '
        f"The clue did not lead to the ribbon box at all. It pointed toward {helper.station}."
    )
    world.say(
        f"Together they followed the trail and thought about what the costume needed: {accident.fix_need}."
    )


def reveal(world: World, hero: Entity, friend: Entity, helper_ent: Entity, helper_cfg: HelperCfg, theme: Theme) -> None:
    costume = world.get("costume")
    costume.location = helper_cfg.station
    costume.meters["missing"] = 0.0
    costume.meters["mended"] += 1
    costume.meters["transformed"] += 1
    propagate(world, narrate=False)
    helper_ent.memes["care"] += 1
    world.say(
        f"At {helper_cfg.station}, they found {helper_cfg.name} smiling over the costume."
    )
    world.say(helper_cfg.reveal_text)
    world.say(
        f"{helper_cfg.name} {helper_cfg.repair_text}. Now it had {theme.transformed_text}."
    )
    world.say(
        f"What had looked like a theft was really a rescue, and the mystery softened at once."
    )


def apologize(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apologized"] += 1
    friend.memes["forgave"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} looked at {friend.id} and felt the hot little sting of having guessed wrong. '
        f'"I am sorry," {hero.pronoun()} said. "I should have followed the clue before blaming you."'
    )
    world.say(
        f'{friend.id} smiled again. "Next time," {friend.pronoun()} said, "we solve the mystery together first."'
    )


def parade_end(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    costume = world.get("costume")
    hero.memes["glee"] += 1
    friend.memes["glee"] += 1
    world.say(
        f"When the music started, {hero.id} stepped into the transformed costume and turned from {theme.start_form} into {theme.end_form} right under the lights."
    )
    world.say(
        f"{friend.id} stood at the curtain, grinning with pure glee as the class gasped and clapped."
    )
    world.say(
        f"The mystery was solved, the friendship was mended, and the costume shimmered like proof that good changes can happen twice in one morning."
    )
    world.facts["ending_image"] = (
        f"{hero.id} onstage as {theme.end_form}, with {friend.id} smiling beside the curtain"
    )
    world.facts["costume_ready"] = costume.meters["mended"] >= THRESHOLD and costume.meters["transformed"] >= THRESHOLD
    world.facts["reconciled"] = world.get("bond").meters["repaired"] >= THRESHOLD


def tell(
    theme: Theme,
    accident: Accident,
    helper_cfg: HelperCfg,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"mystery_name": "The Case of the Vanishing Costume"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["loyal"],
        attrs={"innocent": True},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.name,
        role="helper",
        attrs={"title": helper_cfg.title, "station": helper_cfg.station},
    ))
    costume = world.add(Entity(
        id="costume",
        kind="thing",
        type="costume",
        label=f"{theme.start_form} costume",
        owner=hero.id,
        location=theme.display_spot,
        attrs={"theme": theme.id},
    ))
    world.add(Entity(id="stage", kind="thing", type="stage", label="the stage"))
    world.add(Entity(id="bond", kind="thing", type="friendship", label="their friendship"))

    world.facts.update(
        theme=theme,
        accident=accident,
        helper_cfg=helper_cfg,
        hero=hero,
        friend=friend,
        helper=helper_ent,
        costume=costume,
    )

    world.say(
        f"{theme.opening_image} {hero.id} and {friend.id} had been waiting all week for {theme.parade_name}."
    )
    world.say(
        f"{hero.id}, a {trait} {hero.type}, kept peeking at the costume and imagining the exact moment it would change from {theme.start_form} into {theme.end_form}."
    )

    world.para()
    accident_happens(world, hero, costume, accident)
    vanish(world, hero, friend, theme, accident, helper_cfg)

    world.para()
    accuse(world, hero, friend)
    investigate(world, hero, friend, helper_cfg, accident)

    world.para()
    reveal(world, hero, friend, helper_ent, helper_cfg, theme)
    apologize(world, hero, friend)

    world.para()
    parade_end(world, hero, friend, theme)
    return world


KNOWLEDGE = {
    "butterfly": [
        ("What does a caterpillar turn into?",
         "A caterpillar can change into a butterfly. That kind of big change is called metamorphosis.")
    ],
    "frog": [
        ("How does a tadpole change as it grows?",
         "A tadpole starts with a tail and later grows legs as it becomes a frog. It changes shape as it grows up.")
    ],
    "flower": [
        ("How can a seed become a flower?",
         "A seed can sprout, grow leaves and a stem, and then open into a flower. It takes water, light, and time.")
    ],
    "repair": [
        ("Why do people repair costumes before a show?",
         "They repair costumes so they will stay on properly and look the way the play needs. Fixing a problem early keeps the show safe and smooth.")
    ],
    "apology": [
        ("Why is it good to apologize after blaming someone unfairly?",
         "An apology shows that you know you hurt someone and want to make things right. It helps trust grow back.")
    ],
    "clue": [
        ("What is a clue in a mystery?",
         "A clue is a small sign that helps you figure out what happened. Good detectives look at clues before they guess.")
    ],
    "glee": [
        ("What does glee mean?",
         "Glee means bright, happy delight. It is the kind of joy that almost bubbles over.")
    ],
}
KNOWLEDGE_ORDER = ["clue", "repair", "apology", "glee", "butterfly", "frog", "flower"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    theme = world.facts["theme"]
    accident = world.facts["accident"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "glee" and ends in reconciliation.',
        f"Tell a gentle mystery where {hero.id}'s parade costume vanishes after {accident.problem_text.lower()} and the wrong friend is blamed before the truth is found.",
        f"Write a child-facing story about transformation where {theme.start_form} becomes {theme.end_form}, a clue solves the problem, and {hero.id} and {friend.id} make up in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    helper_cfg = world.facts["helper_cfg"]
    theme = world.facts["theme"]
    accident = world.facts["accident"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {hero.id}'s costume seemed to disappear just before the parade. It looked like someone had taken it, so {hero.id} started trying to solve a little whodunit."
        ),
        (
            f"Why did {hero.id} think something was wrong before the costume vanished?",
            f"{accident.problem_text} That meant the costume was already in trouble before it went missing, so the parade felt at risk."
        ),
        (
            f"Why did {hero.id} blame {friend.id} at first?",
            f"{friend.id} was the only one standing nearby when {hero.id} came back, so the guess came too quickly. {hero.id} looked at who was close instead of following the clue first."
        ),
        (
            f"How did {friend.id} help solve the mystery?",
            f"{friend.id} pointed out that the clue did not match the ribbon box at all. That calm idea turned the story from blaming into investigating."
        ),
        (
            f"Who really took the costume, and why?",
            f"It was {helper_cfg.name}. {helper.pronoun().capitalize()} took it to {helper_cfg.station} because the costume was damaged and needed help before the show."
        ),
        (
            "How was the costume transformed?",
            f"It started as {theme.start_form} and came back ready to become {theme.end_form}. The helper changed the damaged parts into new costume pieces, so the repair became part of the transformation."
        ),
        (
            f"How did {hero.id} and {friend.id} reconcile?",
            f"{hero.id} apologized for blaming {friend.id} without knowing the truth. {friend.id} forgave {hero.pronoun('object')}, so the friendship was repaired along with the costume."
        ),
        (
            "How did the story end?",
            f"It ended with the mystery solved and the parade saved. {friend.id} watched in glee as {hero.id} stepped onstage in the transformed costume."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"clue", "repair", "apology", "glee"}
    theme = world.facts["theme"]
    tags |= theme.tags & {"butterfly", "frog", "flower"}
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
        parts = [f"({ent.type})"]
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.location:
            parts.append(f"location={ent.location}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if attrs:
            parts.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="butterfly",
        accident="rip",
        helper="nana_rosa",
        hero_name="Lina",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        trait="careful",
        seed=101,
    ),
    StoryParams(
        theme="butterfly",
        accident="stain",
        helper="mr_piper",
        hero_name="Owen",
        hero_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        trait="curious",
        seed=102,
    ),
    StoryParams(
        theme="frog",
        accident="loose_strap",
        helper="coach_lee",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        trait="eager",
        seed=103,
    ),
    StoryParams(
        theme="frog",
        accident="rip",
        helper="nana_rosa",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        trait="bright",
        seed=104,
    ),
    StoryParams(
        theme="flower",
        accident="stain",
        helper="mr_piper",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        trait="thoughtful",
        seed=105,
    ),
]


def explain_rejection(theme_id: str, accident_id: str, helper_id: str) -> str:
    theme = THEMES.get(theme_id)
    accident = ACCIDENTS.get(accident_id)
    helper = HELPERS.get(helper_id)
    if theme is None or accident is None or helper is None:
        return "(No story: one or more requested ids are unknown.)"
    if theme_id not in helper.themes:
        known = ", ".join(sorted(helper.themes))
        return (
            f"(No story: {helper.name} does not work on the {theme.id} transformation here. "
            f"{helper.pronoun('subject').capitalize()} reasonably helps with: {known}.)"
        )
    known_acc = ", ".join(sorted(helper.accidents))
    return (
        f"(No story: {helper.name} cannot reasonably fix a {accident.id} in this world. "
        f"{helper.pronoun('subject').capitalize()} handles: {known_acc}.)"
    )


ASP_RULES = r"""
valid(T, A, H) :- theme(T), accident(A), helper(H), can_theme(H, T), can_accident(H, A).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in sorted(THEMES):
        lines.append(asp.fact("theme", theme_id))
    for accident_id in sorted(ACCIDENTS):
        lines.append(asp.fact("accident", accident_id))
    for helper_id, helper in sorted(HELPERS.items()):
        lines.append(asp.fact("helper", helper_id))
        for theme_id in sorted(helper.themes):
            lines.append(asp.fact("can_theme", helper_id, theme_id))
        for accident_id in sorted(helper.accidents):
            lines.append(asp.fact("can_accident", helper_id, accident_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_emit(sample: StorySample) -> None:
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: empty story.)")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-facing whodunit about a vanished costume, a kind transformation, and reconciliation."
    )
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--accident", choices=sorted(ACCIDENTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (theme, accident, helper) triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.theme and args.accident and args.helper:
        if not can_fix(args.theme, args.accident, args.helper):
            raise StoryError(explain_rejection(args.theme, args.accident, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.accident is None or combo[1] == args.accident)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, accident_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        accident=accident_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(No story: unknown theme '{params.theme}'.)")
    if params.accident not in ACCIDENTS:
        raise StoryError(f"(No story: unknown accident '{params.accident}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not can_fix(params.theme, params.accident, params.helper):
        raise StoryError(explain_rejection(params.theme, params.accident, params.helper))

    world = tell(
        theme=THEMES[params.theme],
        accident=ACCIDENTS[params.accident],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, accident, helper) combos:\n")
        for theme_id, accident_id, helper_id in combos:
            print(f"  {theme_id:10} {accident_id:12} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.theme} / {p.accident} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
