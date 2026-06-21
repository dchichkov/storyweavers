#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py
=========================================================

A standalone storyworld for a tiny magical whodunit: at a little wizard school,
a display is spoiled by a blur spell after one child makes a thoughtless comment.
Another child follows the clues, a grown-up helps, and the mystery ends with an
apology and a clearer, kinder way to speak.

The world model prefers only combinations that make common sense:
- a blur spell must actually work on the chosen target material
- the reveal method must be sensible and able to detect that spell's residue
- some cases end in a gentle confession, while others need a magical reveal

Run it
------
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py --target star_map --spell fog_chalk
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py --target stone_plaque
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/comment_blur_magic_whodunit.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
GENTLE_TRAITS = {"gentle", "patient", "kind", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    material: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "teacher_f", "witch"}
        male = {"boy", "man", "teacher_m", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher_f": "teacher", "teacher_m": "teacher"}.get(self.type, self.type)
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
    display: str
    mood: str
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
class Spell:
    id: str
    label: str
    phrase: str
    residue: str
    residue_text: str
    works_on: set[str]
    cast_line: str
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
class Target:
    id: str
    label: str
    phrase: str
    material: str
    feature: str
    place_line: str
    repaired_line: str
    blurable: bool = True
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
class Reveal:
    id: str
    label: str
    sense: int
    detects: set[str]
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


@dataclass
class Motive:
    id: str
    comment: str
    impulse: str
    confession: str
    confesses_early: bool
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
class StoryParams:
    setting: str
    target: str
    spell: str
    reveal: str
    motive: str
    sleuth: str
    sleuth_gender: str
    culprit: str
    culprit_gender: str
    owner: str
    owner_gender: str
    teacher: str
    teacher_gender: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"sleuth", "culprit", "owner"}]

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


def _r_mystery(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["blurred"] < THRESHOLD:
        return []
    sig = ("mystery", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["mystery"] += 1
    world.get("teacher").memes["concern"] += 1
    world.get("sleuth").memes["curiosity"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__mystery__"]


def _r_residue(world: World) -> list[str]:
    target = world.get("target")
    culprit = world.get("culprit")
    residue = world.facts.get("residue", "")
    if target.meters["blurred"] < THRESHOLD or not residue:
        return []
    sig = ("residue", residue)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.attrs["residue"] = residue
    culprit.attrs["residue"] = residue
    target.meters["clue"] += 1
    culprit.meters["clue"] += 1
    return [faint_residue_line(world)]


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="residue", tag="physical", apply=_r_residue),
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


def blur_risk(spell: Spell, target: Target) -> bool:
    return target.blurable and target.material in spell.works_on


def sensible_reveals() -> list[Reveal]:
    return [r for r in REVEALS.values() if r.sense >= SENSE_MIN]


def reveal_works(spell: Spell, reveal: Reveal) -> bool:
    return spell.residue in reveal.detects and reveal.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for target_id, target in TARGETS.items():
        for spell_id, spell in SPELLS.items():
            if not blur_risk(spell, target):
                continue
            for reveal_id, reveal in REVEALS.items():
                if reveal_works(spell, reveal):
                    combos.append((target_id, spell_id, reveal_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    motive = MOTIVES[params.motive]
    if motive.confesses_early and params.trait in GENTLE_TRAITS:
        return "confession"
    return "revealed"


def faint_residue_line(world: World) -> str:
    spell = world.facts["spell_cfg"]
    return (
        f"When the blur settled, a faint trace of {spell.residue_text} clung to one corner. "
        f"It was small, but it looked like the sort of clue a careful wizard could follow."
    )


def predict_confession(world: World) -> bool:
    sim = world.copy()
    motive = sim.facts["motive_cfg"]
    trait = sim.facts["sleuth"].traits[0] if sim.facts["sleuth"].traits else ""
    return motive.confesses_early and trait in GENTLE_TRAITS


def introduce(world: World, sleuth: Entity, owner: Entity, target: Target) -> None:
    world.say(
        f"In {world.setting.place}, the children were getting ready for a small display of magic work. "
        f"{target.place_line}"
    )
    world.say(
        f"{owner.id} had made {target.phrase}, and {sleuth.id} liked standing nearby because {world.setting.mood}."
    )


def comment_scene(world: World, culprit: Entity, owner: Entity, motive: Motive, target: Target) -> None:
    culprit.memes["sharpness"] += 1
    owner.memes["pride"] += 1
    owner.memes["hurt"] += 1
    world.say(
        f"{culprit.id} glanced at {target.the if hasattr(target, 'the') else target.label} and made a quick comment: "
        f'"{motive.comment}"'
    )
    world.say(
        f"The words were meant to be small, but they landed heavily. {owner.id} looked down at "
        f"{target.label} and smoothed one edge with careful fingers."
    )


def owner_answer(world: World, owner: Entity, target: Target) -> None:
    owner.memes["bravery"] += 1
    world.say(
        f'"I worked hard on the {target.label}," {owner.id} said softly. "It does not have to be perfect to be good."'
    )


def temptation(world: World, culprit: Entity, motive: Motive, spell: Spell) -> None:
    culprit.memes["impulse"] += 1
    world.say(
        f"But {motive.impulse}. On the supply table sat {spell.phrase}, and the magic of it promised a quick little fix."
    )


def cast_blur(world: World, culprit: Entity, target_ent: Entity, spell: Spell, target: Target) -> None:
    culprit.memes["guilt"] += 1
    culprit.meters["magic_used"] += 1
    target_ent.meters["blurred"] += 1
    world.facts["residue"] = spell.residue
    world.facts["blurred_by"] = culprit.id
    propagate(world, narrate=True)
    world.say(
        f"{culprit.id} whispered {spell.cast_line}. At once, the neat lines on the {target.label} ran together in a pale blur."
    )


def discover(world: World, teacher: Entity, sleuth: Entity, target: Target) -> None:
    world.say(
        f"When {teacher.id} came by, {teacher.pronoun()} stopped short. "
        f'"Who blurred the {target.label}?" {teacher.pronoun()} asked. "This looks like a little whodunit."'
    )
    world.say(
        f"{sleuth.id} leaned closer, eyes bright with curiosity. The mystery had begun."
    )


def inspect(world: World, sleuth: Entity, spell: Spell) -> None:
    sleuth.meters["clue"] += 1
    world.say(
        f"{sleuth.id} noticed the strange trace near the corner and remembered that {spell.label} often left {spell.residue_text} behind."
    )


def kind_question(world: World, sleuth: Entity, culprit: Entity, motive: Motive) -> None:
    sleuth.memes["kindness"] += 1
    culprit.memes["pressure"] += 1
    world.say(
        f'{sleuth.id} did not point or accuse. "{culprit.id}," {sleuth.pronoun()} said gently, '
        f'"did something happen after that comment? You can tell the truth."'
    )


def confession(world: World, culprit: Entity, owner: Entity, motive: Motive, target: Target) -> None:
    culprit.memes["relief"] += 1
    culprit.memes["guilt"] = max(0.0, culprit.memes["guilt"] - 1.0)
    owner.memes["hurt"] = max(0.0, owner.memes["hurt"] - 0.5)
    world.say(
        f"{culprit.id}'s shoulders dropped. {motive.confession}"
    )
    world.say(
        f'"I was trying to hide the problem after my mean comment," {culprit.pronoun()} admitted. '
        f'"But I only made the {target.label} worse."'
    )


def reveal_culprit(world: World, teacher: Entity, culprit: Entity, reveal: Reveal, spell: Spell) -> None:
    culprit.memes["guilt"] += 1
    world.say(
        f"{teacher.id} chose {reveal.label}. {teacher.pronoun().capitalize()} {reveal.action}, and the leftover magic glimmered at once."
    )
    world.say(
        f"The glow matched the {spell.label} dust on {culprit.id}'s sleeve. No one had to guess any longer."
    )


def apology(world: World, culprit: Entity, owner: Entity) -> None:
    culprit.memes["lesson"] += 1
    culprit.memes["relief"] += 1
    owner.memes["relief"] += 1
    owner.memes["hurt"] = 0.0
    world.say(
        f'{culprit.id} looked at {owner.id} and said, "I am sorry for the comment, and I am sorry I used magic to hide things instead of telling the truth."'
    )
    world.say(
        f'{owner.id} nodded. "Next time, just tell me what happened," {owner.pronoun()} said. "Kind words work better than sneaky spells."'
    )


def repair(world: World, teacher: Entity, culprit: Entity, owner: Entity, target_ent: Entity, target: Target) -> None:
    target_ent.meters["blurred"] = 0.0
    target_ent.meters["repaired"] += 1
    world.get("room").meters["mystery"] = 0.0
    for kid in world.kids():
        kid.memes["worry"] = 0.0
    world.say(
        f"Together they fetched a clearing charm and patient hands. Soon {target.repaired_line}"
    )
    world.say(
        f"{culprit.id} held the corner steady while {owner.id} fixed the last neat line, and {teacher.id} smiled to see them working side by side."
    )


def ending(world: World, sleuth: Entity, owner: Entity, target: Target) -> None:
    sleuth.memes["pride"] += 1
    world.say(
        f"By the end of the morning, the little mystery was solved, the {target.label} was clear again, and the room no longer felt full of questions."
    )
    world.say(
        f"A new note sat beside it in tidy writing: Be careful with magic, and even more careful with your words. "
        f"{sleuth.id} liked that better than any clever twist."
    )


def tell(
    setting: Setting,
    target: Target,
    spell: Spell,
    reveal: Reveal,
    motive: Motive,
    sleuth_name: str = "Nora",
    sleuth_gender: str = "girl",
    culprit_name: str = "Finn",
    culprit_gender: str = "boy",
    owner_name: str = "Mira",
    owner_gender: str = "girl",
    teacher_name: str = "Master Elm",
    teacher_gender: str = "teacher_m",
    trait: str = "gentle",
) -> World:
    world = World(setting)

    sleuth = world.add(
        Entity(
            id=sleuth_name,
            kind="character",
            type=sleuth_gender,
            role="sleuth",
            traits=[trait],
            attrs={},
            tags={"detective"},
        )
    )
    culprit = world.add(
        Entity(
            id=culprit_name,
            kind="character",
            type=culprit_gender,
            role="culprit",
            traits=["hasty"],
            attrs={},
            tags={"truth"},
        )
    )
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            role="owner",
            traits=["careful"],
            attrs={},
            tags={"art"},
        )
    )
    teacher = world.add(
        Entity(
            id=teacher_name,
            kind="character",
            type=teacher_gender,
            role="teacher",
            label="the teacher",
            attrs={},
            tags={"adult"},
        )
    )
    target_ent = world.add(
        Entity(
            id="target",
            kind="thing",
            type="display",
            label=target.label,
            material=target.material,
            attrs={},
            tags=set(target.tags),
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=setting.place,
            attrs={},
        )
    )

    for ent in (sleuth, culprit, owner, teacher, target_ent, room):
        ent.attrs.setdefault("residue", "")
        ent.meters["clue"] += 0.0
        ent.meters["blurred"] += 0.0
        ent.meters["repaired"] += 0.0
        ent.memes["worry"] += 0.0
        ent.memes["relief"] += 0.0

    world.facts.update(
        setting=setting,
        target_cfg=target,
        target=target_ent,
        spell_cfg=spell,
        reveal_cfg=reveal,
        motive_cfg=motive,
        sleuth=sleuth,
        culprit=culprit,
        owner=owner,
        teacher=teacher,
        residue=spell.residue,
    )

    introduce(world, sleuth, owner, target)
    world.para()
    comment_scene(world, culprit, owner, motive, target)
    owner_answer(world, owner, target)
    temptation(world, culprit, motive, spell)

    world.para()
    cast_blur(world, culprit, target_ent, spell, target)
    discover(world, teacher, sleuth, target)
    inspect(world, sleuth, spell)

    world.para()
    kind_question(world, sleuth, culprit, motive)
    early = predict_confession(world)
    if early:
        confession(world, culprit, owner, motive, target)
    else:
        reveal_culprit(world, teacher, culprit, reveal, spell)

    world.para()
    apology(world, culprit, owner)
    repair(world, teacher, culprit, owner, target_ent, target)
    ending(world, sleuth, owner, target)

    world.facts.update(
        outcome="confession" if early else "revealed",
        mystery=room.meters["mystery"] >= THRESHOLD,
        blurred=target_ent.meters["repaired"] < THRESHOLD,
        repaired=target_ent.meters["repaired"] >= THRESHOLD,
        clue_residue=spell.residue,
        confessed=early,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the bright spell classroom",
        display="class display",
        mood="sunbeams kept sliding over jars of chalk and tiny wands",
        tags={"school", "magic"},
    ),
    "library": Setting(
        id="library",
        place="the round school library",
        display="reading table display",
        mood="the lamps glowed softly between tall shelves of spellbooks",
        tags={"library", "magic"},
    ),
    "hall": Setting(
        id="hall",
        place="the front hall of the little wizard school",
        display="hall display",
        mood="every footstep sounded important on the polished floor",
        tags={"school", "magic"},
    ),
}

SPELLS = {
    "fog_chalk": Spell(
        id="fog_chalk",
        label="fog chalk",
        phrase="a stick of fog chalk",
        residue="silver_dust",
        residue_text="silver dust",
        works_on={"paper", "glass"},
        cast_line='"Hush and smudge."',
        tags={"magic", "chalk"},
    ),
    "smudge_wand": Spell(
        id="smudge_wand",
        label="smudge wand",
        phrase="a smudge wand",
        residue="blue_spark",
        residue_text="tiny blue sparks",
        works_on={"paper", "glass", "steam"},
        cast_line='"Blur a bit, not a lot."',
        tags={"magic", "wand"},
    ),
    "mist_ring": Spell(
        id="mist_ring",
        label="mist ring",
        phrase="a mist ring",
        residue="violet_mist",
        residue_text="violet mist",
        works_on={"glass", "steam"},
        cast_line='"Mist around and soften."',
        tags={"magic", "ring"},
    ),
}

TARGETS = {
    "star_map": Target(
        id="star_map",
        label="star map",
        phrase="a star map painted with tiny silver moons",
        material="paper",
        feature="its careful silver moons",
        place_line="A star map painted with tiny silver moons stood on an easel by the window.",
        repaired_line="the silver moons on the star map shone sharply again.",
        blurable=True,
        tags={"stars", "paper"},
    ),
    "potion_label": Target(
        id="potion_label",
        label="potion label",
        phrase="a potion label written for a honey-sleep syrup bottle",
        material="glass",
        feature="its curly gold letters",
        place_line="A bottle with a fresh potion label sat in the middle of the table for everyone to admire.",
        repaired_line="the potion label's curly letters could be read clearly again.",
        blurable=True,
        tags={"potion", "glass"},
    ),
    "window_sign": Target(
        id="window_sign",
        label="window sign",
        phrase="a welcome sign floating against the library glass",
        material="glass",
        feature="its floating welcome letters",
        place_line="A welcome sign floated against the glass, shining where the morning light touched it.",
        repaired_line="the welcome sign floated neatly again, every letter crisp.",
        blurable=True,
        tags={"glass", "sign"},
    ),
    "stone_plaque": Target(
        id="stone_plaque",
        label="stone plaque",
        phrase="a heavy stone plaque by the archway",
        material="stone",
        feature="its carved edge",
        place_line="A heavy stone plaque leaned by the archway, waiting to be set in place.",
        repaired_line="the carved stone looked the same as before.",
        blurable=False,
        tags={"stone"},
    ),
}

REVEALS = {
    "moon_lens": Reveal(
        id="moon_lens",
        label="the moon lens",
        sense=3,
        detects={"silver_dust", "blue_spark"},
        action="held the moon lens over the blur",
        qa_text="used the moon lens to make the leftover magic show itself",
        tags={"detective", "lens"},
    ),
    "echo_tea": Reveal(
        id="echo_tea",
        label="a cup of echo tea",
        sense=3,
        detects={"blue_spark", "violet_mist"},
        action="poured one drop of echo tea beside the blur and watched the magic answer back",
        qa_text="used echo tea to wake the leftover magic and show who had touched it",
        tags={"detective", "tea"},
    ),
    "sniffing_cat": Reveal(
        id="sniffing_cat",
        label="the sniffing cat",
        sense=2,
        detects={"silver_dust", "violet_mist"},
        action="let the sniffing cat pad around the table until its whiskers twitched at the right trail",
        qa_text="let the sniffing cat follow the magical scent",
        tags={"cat", "detective"},
    ),
    "wild_guess": Reveal(
        id="wild_guess",
        label="a wild guess",
        sense=1,
        detects=set(),
        action="asked everyone to point at whoever looked nervous",
        qa_text="made a wild guess",
        tags={"guess"},
    ),
}

MOTIVES = {
    "hide_mistake": Motive(
        id="hide_mistake",
        comment="That line looks crooked.",
        impulse="the mean little comment made the room feel awkward, and now guilt pushed harder than patience",
        confession='At last, {name} blurted out the truth before anyone else had to speak.',
        confesses_early=True,
        tags={"comment", "truth"},
    ),
    "jealousy": Motive(
        id="jealousy",
        comment="Everyone will stare at that instead of my project.",
        impulse="a jealous thought slipped in, and for a moment being noticed felt more important than being honest",
        confession='The truth did not come out right away, because jealousy likes hiding in the corners.',
        confesses_early=False,
        tags={"comment", "jealousy"},
    ),
    "show_off": Motive(
        id="show_off",
        comment="I could make it look more magical than that in one second.",
        impulse="showing off seemed exciting, and the wish to be impressive rushed ahead of good sense",
        confession='The braggy feeling stuck around, so the truth needed help to come into the open.',
        confesses_early=False,
        tags={"comment", "boast"},
    ),
}

GIRL_NAMES = ["Nora", "Mira", "Lina", "Ava", "Ivy", "Zoe", "Ruby", "Tessa"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Owen", "Jude", "Ben", "Arlo", "Theo"]
TRAITS = ["gentle", "patient", "kind", "thoughtful", "curious", "brisk"]


def explain_rejection(spell: Spell, target: Target) -> str:
    if not target.blurable:
        return (
            f"(No story: {target.label} is made of {target.material}, and these little blur spells do not sensibly smear it. "
            f"Pick a paper or glass display so the mystery can really happen.)"
        )
    return (
        f"(No story: {spell.label} does not work on {target.material}, so it would not create a real blur on the {target.label}.)"
    )


def explain_reveal(reveal: Reveal) -> str:
    options = ", ".join(sorted(r.id for r in sensible_reveals()))
    return (
        f"(Refusing reveal '{reveal.id}': it scores too low on common sense "
        f"(sense={reveal.sense} < {SENSE_MIN}). Try one of: {options}.)"
    )


def explain_combo_reveal(spell: Spell, reveal: Reveal) -> str:
    return (
        f"(No story: {reveal.label} would not find the residue left by {spell.label}. "
        f"The clue and the reveal method must actually match.)"
    )


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in this story?",
            "Magic is a special power that can change how things look or act. In this story, children use small school spells, but they still need to use them carefully."
        )
    ],
    "comment": [
        (
            "Why can a careless comment hurt?",
            "A careless comment can make someone feel small, even if it was said quickly. Words can leave a mark before anyone notices."
        )
    ],
    "blur": [
        (
            "What does blur mean?",
            "Blur means something stops looking clear and sharp. The edges run together, so it becomes hard to read or see properly."
        )
    ],
    "chalk": [
        (
            "What is fog chalk?",
            "Fog chalk is pretend magic chalk that can smear neat lines into a misty blur. It leaves a little magical trace behind."
        )
    ],
    "wand": [
        (
            "What is a smudge wand?",
            "A smudge wand is a tiny wand used for softening or blurring marks. In careful hands it can help with art, but used badly it causes trouble."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to solve a mystery. A good detective does not have to be mean to find the truth."
        )
    ],
    "lens": [
        (
            "What does a lens do?",
            "A lens helps you see something more clearly. A magic lens can make hidden marks or clues show up."
        )
    ],
    "tea": [
        (
            "What is echo tea in this world?",
            "Echo tea is pretend magic tea that makes leftover spell traces answer back. It helps grown-ups notice magic that has already happened."
        )
    ],
    "cat": [
        (
            "Why would a magical cat help with clues?",
            "In pretend magic stories, an animal helper can notice smells or traces people miss. The cat is calm and follows the trail step by step."
        )
    ],
    "truth": [
        (
            "Why is telling the truth better than hiding a mistake?",
            "Telling the truth lets people fix the real problem together. Hiding a mistake usually makes the problem bigger."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "comment", "blur", "chalk", "wand", "detective", "lens", "tea", "cat", "truth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sleuth = f["sleuth"]
    culprit = f["culprit"]
    owner = f["owner"]
    target = f["target_cfg"]
    spell = f["spell_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short magical whodunit for a 3-to-5-year-old that includes the words "comment" and "blur". '
        f"The mystery should center on a {target.label} spoiled by {spell.label}."
    )
    if outcome == "confession":
        return [
            base,
            f"Tell a gentle school mystery where {culprit.id} makes an unkind comment, uses magic badly, and confesses when {sleuth.id} asks kindly.",
            f"Write a magical whodunit in which a blurred {target.label} is the mystery, but the answer comes from honesty and apology instead of punishment.",
        ]
    return [
        base,
        f"Tell a magical whodunit where {sleuth.id} follows the clue left on the blurred {target.label} and a grown-up reveal spell shows who did it.",
        f"Write a child-friendly mystery where a blur spell hides the truth for a little while, then the clues and a caring teacher uncover it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    culprit = f["culprit"]
    owner = f["owner"]
    teacher = f["teacher"]
    target = f["target_cfg"]
    spell = f["spell_cfg"]
    reveal = f["reveal_cfg"]
    motive = f["motive_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.id}, who follows the clues, {culprit.id}, who caused the trouble, and {owner.id}, whose {target.label} was blurred. {teacher.id} helps the children solve the mystery and set things right."
        ),
        (
            f"What was the mystery?",
            f"The mystery was who had turned {owner.id}'s {target.label} into a blur. The change happened suddenly, so everyone had to look for a clue instead of guessing."
        ),
        (
            f"What happened before the magic trouble?",
            f"{culprit.id} made a hurtful comment about the {target.label}, and the words made the room feel awkward. That unkind moment came first, and then the blur spell made the problem bigger."
        ),
        (
            f"How did {sleuth.id} help solve the case?",
            f"{sleuth.id} noticed the small trace left by the spell and stayed calm instead of pointing fingers. That careful noticing is what turned the blur into a real clue."
        ),
    ]
    if outcome == "confession":
        qa.append(
            (
                f"How was the mystery solved?",
                f"The mystery was solved when {sleuth.id} asked a gentle question and {culprit.id} confessed. The kind question mattered because {culprit.id} already felt guilty after the mean comment and the bad spell."
            )
        )
    else:
        qa.append(
            (
                f"How did {teacher.id} find out who did it?",
                f"{teacher.id} {reveal.qa_text}. The reveal worked because it matched the residue left by {spell.label}, so the clue pointed to the right person instead of being a wild guess."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with an apology, the {target.label} fixed, and the children working together again. The clear ending image shows that truth and kindness repaired what the blur spell had spoiled."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"magic", "comment", "blur", "truth", "detective"}
    tags |= set(world.facts["spell_cfg"].tags)
    tags |= set(world.facts["reveal_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.material:
            bits.append(f"material={e.material}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(Tg, Sp) :- target(Tg), spell(Sp), blurable(Tg), material(Tg, M), works_on(Sp, M).
sensible(R)    :- reveal(R), sense(R, S), sense_min(Min), S >= Min.
matches(Sp, R) :- spell_residue(Sp, Res), detects(R, Res).
valid(Tg, Sp, R) :- hazard(Tg, Sp), sensible(R), matches(Sp, R).

% --- outcome model ---------------------------------------------------------
gentle_trait(T) :- trait(T), gentle(T).
outcome(confession) :- motive_confesses_early, gentle_trait(T).
outcome(revealed)   :- not outcome(confession).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("material", tid, target.material))
        if target.blurable:
            lines.append(asp.fact("blurable", tid))
    for spid, spell in SPELLS.items():
        lines.append(asp.fact("spell", spid))
        lines.append(asp.fact("spell_residue", spid, spell.residue))
        for mat in sorted(spell.works_on):
            lines.append(asp.fact("works_on", spid, mat))
    for rid, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", rid))
        lines.append(asp.fact("sense", rid, reveal.sense))
        for res in sorted(reveal.detects):
            lines.append(asp.fact("detects", rid, res))
    for tr in sorted(GENTLE_TRAITS):
        lines.append(asp.fact("gentle", tr))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra_lines = [asp.fact("trait", params.trait)]
    if MOTIVES[params.motive].confesses_early:
        extra_lines.append(asp.fact("motive_confesses_early"))
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="classroom",
        target="star_map",
        spell="fog_chalk",
        reveal="moon_lens",
        motive="hide_mistake",
        sleuth="Nora",
        sleuth_gender="girl",
        culprit="Finn",
        culprit_gender="boy",
        owner="Mira",
        owner_gender="girl",
        teacher="Master Elm",
        teacher_gender="teacher_m",
        trait="gentle",
    ),
    StoryParams(
        setting="library",
        target="window_sign",
        spell="mist_ring",
        reveal="sniffing_cat",
        motive="show_off",
        sleuth="Theo",
        sleuth_gender="boy",
        culprit="Ruby",
        culprit_gender="girl",
        owner="Lina",
        owner_gender="girl",
        teacher="Miss Wren",
        teacher_gender="teacher_f",
        trait="patient",
    ),
    StoryParams(
        setting="hall",
        target="potion_label",
        spell="smudge_wand",
        reveal="echo_tea",
        motive="jealousy",
        sleuth="Ava",
        sleuth_gender="girl",
        culprit="Milo",
        culprit_gender="boy",
        owner="Ivy",
        owner_gender="girl",
        teacher="Master Reed",
        teacher_gender="teacher_m",
        trait="curious",
    ),
    StoryParams(
        setting="classroom",
        target="window_sign",
        spell="smudge_wand",
        reveal="moon_lens",
        motive="hide_mistake",
        sleuth="Leo",
        sleuth_gender="boy",
        culprit="Tessa",
        culprit_gender="girl",
        owner="Zoe",
        owner_gender="girl",
        teacher="Miss Wren",
        teacher_gender="teacher_f",
        trait="thoughtful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical whodunit with a comment, a blur, and a small school mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--teacher", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (target, spell, reveal) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reveal and REVEALS[args.reveal].sense < SENSE_MIN:
        raise StoryError(explain_reveal(REVEALS[args.reveal]))

    if args.target and args.spell:
        target = TARGETS[args.target]
        spell = SPELLS[args.spell]
        if not blur_risk(spell, target):
            raise StoryError(explain_rejection(spell, target))

    if args.spell and args.reveal:
        spell = SPELLS[args.spell]
        reveal = REVEALS[args.reveal]
        if not reveal_works(spell, reveal):
            raise StoryError(explain_combo_reveal(spell, reveal))

    combos = [
        combo for combo in valid_combos()
        if (args.target is None or combo[0] == args.target)
        and (args.spell is None or combo[1] == args.spell)
        and (args.reveal is None or combo[2] == args.reveal)
    ]
    if not combos:
        if args.target and not TARGETS[args.target].blurable:
            spell = SPELLS[args.spell] if args.spell else next(iter(SPELLS.values()))
            raise StoryError(explain_rejection(spell, TARGETS[args.target]))
        raise StoryError("(No valid combination matches the given options.)")

    target_id, spell_id, reveal_id = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    motive = args.motive or rng.choice(sorted(MOTIVES))
    teacher_gender = args.teacher or rng.choice(["teacher_f", "teacher_m"])
    teacher_name = rng.choice(["Miss Wren", "Mistress Pine"] if teacher_gender == "teacher_f" else ["Master Elm", "Master Reed"])

    sleuth_gender = rng.choice(["girl", "boy"])
    culprit_gender = rng.choice(["girl", "boy"])
    owner_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()
    sleuth = pick_name(rng, sleuth_gender, used)
    used.add(sleuth)
    culprit = pick_name(rng, culprit_gender, used)
    used.add(culprit)
    owner = pick_name(rng, owner_gender, used)
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        target=target_id,
        spell=spell_id,
        reveal=reveal_id,
        motive=motive,
        sleuth=sleuth,
        sleuth_gender=sleuth_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        owner=owner,
        owner_gender=owner_gender,
        teacher=teacher_name,
        teacher_gender=teacher_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.spell not in SPELLS:
        raise StoryError(f"(Unknown spell: {params.spell})")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Unknown reveal: {params.reveal})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Unknown motive: {params.motive})")

    target = TARGETS[params.target]
    spell = SPELLS[params.spell]
    reveal = REVEALS[params.reveal]

    if not blur_risk(spell, target):
        raise StoryError(explain_rejection(spell, target))
    if reveal.sense < SENSE_MIN:
        raise StoryError(explain_reveal(reveal))
    if not reveal_works(spell, reveal):
        raise StoryError(explain_combo_reveal(spell, reveal))

    world = tell(
        setting=SETTINGS[params.setting],
        target=target,
        spell=spell,
        reveal=reveal,
        motive=MOTIVES[params.motive],
        sleuth_name=params.sleuth,
        sleuth_gender=params.sleuth_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        teacher_name=params.teacher,
        teacher_gender=params.teacher_gender,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_reveals()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible reveals match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible reveals: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
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

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible reveals: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (target, spell, reveal) combos:\n")
        for target, spell, reveal in combos:
            print(f"  {target:12} {spell:12} {reveal}")
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
            header = f"### {p.sleuth}: {p.target} blurred by {p.spell} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
