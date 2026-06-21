#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/eighteenth_spud_raw_surprise_reconciliation_bedtime_story.py
=======================================================================================

A small bedtime-story world about two children counting potatoes for tomorrow's
soup, a secret idea sparked by the eighteenth spud, a hurt misunderstanding, and
a soft reconciliation before sleep.

Core premise
------------
A child notices that the eighteenth potato is just right for a simple stamp.
The child hides the raw spud to make a bedtime surprise card. Another child
sees the basket count come up short, thinks the potato was taken unfairly,
speaks sharply, and hurts the planner's feelings. A calm grown-up slows the
moment down. The surprise is revealed, the misunderstanding is repaired, and the
ending image shows what changed: the children settle into bed reconciled.

The world model tracks physical meters (counted potatoes, hidden spud, paint on
paper, cut stamp) and emotional memes (suspicion, hurt, guilt, trust, relief,
delight). Prose is rendered from state and trace facts rather than from a frozen
paragraph template.

Run it
------
python storyworlds/worlds/gpt-5.4/eighteenth_spud_raw_surprise_reconciliation_bedtime_story.py
python storyworlds/worlds/gpt-5.4/eighteenth_spud_raw_surprise_reconciliation_bedtime_story.py --qa
python storyworlds/worlds/gpt-5.4/eighteenth_spud_raw_surprise_reconciliation_bedtime_story.py --all
python storyworlds/worlds/gpt-5.4/eighteenth_spud_raw_surprise_reconciliation_bedtime_story.py --motif moon --potato round --recipient sibling
python storyworlds/worlds/gpt-5.4/eighteenth_spud_raw_surprise_reconciliation_bedtime_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Motif:
    id: str
    label: str
    article: str
    shape_word: str
    needs_flatness: int
    paint: str
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
class PotatoKind:
    id: str
    label: str
    phrase: str
    flatness: int
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
class Recipient:
    id: str
    label: str
    relation_word: str
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
class Repair:
    id: str
    label: str
    allows_for: set[str]
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


def _r_missing_spud(world: World) -> list[str]:
    basket = world.get("basket")
    other = world.get("other")
    if basket.meters["expected_count"] < THRESHOLD:
        return []
    if basket.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_spud",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    other.memes["suspicion"] += 1
    other.memes["worry"] += 1
    return ["__missing__"]


def _r_sharp_words_hurt(world: World) -> list[str]:
    planner = world.get("planner")
    other = world.get("other")
    if other.memes["accused"] < THRESHOLD or planner.memes["secret"] < THRESHOLD:
        return []
    sig = ("sharp_words_hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    planner.memes["hurt"] += 1
    other.memes["guilt_seed"] += 1
    return ["__hurt__"]


def _r_repair_softens(world: World) -> list[str]:
    planner = world.get("planner")
    other = world.get("other")
    if planner.memes["forgiven"] < THRESHOLD or other.memes["apologized"] < THRESHOLD:
        return []
    sig = ("repair_softens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    planner.memes["relief"] += 1
    other.memes["relief"] += 1
    planner.memes["trust"] += 1
    other.memes["trust"] += 1
    return ["__repaired__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_spud", tag="social", apply=_r_missing_spud),
    Rule(name="sharp_words_hurt", tag="social", apply=_r_sharp_words_hurt),
    Rule(name="repair_softens", tag="social", apply=_r_repair_softens),
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


MOTIFS = {
    "moon": Motif(
        id="moon",
        label="moon",
        article="a moon",
        shape_word="crescent",
        needs_flatness=2,
        paint="pale silver paint",
        ending_image="The card leaned beside the lamp, and the silver moon on it seemed to float with the real moonlight.",
        tags={"moon", "potato_stamp", "bedtime"},
    ),
    "star": Motif(
        id="star",
        label="star",
        article="a star",
        shape_word="star",
        needs_flatness=3,
        paint="gold paint",
        ending_image="The gold stars on the cards twinkled softly while the blankets settled around them.",
        tags={"star", "potato_stamp", "bedtime"},
    ),
    "cloud": Motif(
        id="cloud",
        label="cloud",
        article="a cloud",
        shape_word="puffy cloud",
        needs_flatness=1,
        paint="soft blue paint",
        ending_image="By the bed, the little cloud print looked quiet and gentle, like a dream waiting to begin.",
        tags={"cloud", "potato_stamp", "bedtime"},
    ),
}

POTATOES = {
    "round": PotatoKind(
        id="round",
        label="round spud",
        phrase="a round little spud",
        flatness=3,
        tags={"potato", "round"},
    ),
    "oval": PotatoKind(
        id="oval",
        label="oval spud",
        phrase="an oval kitchen spud",
        flatness=2,
        tags={"potato", "oval"},
    ),
    "knobbly": PotatoKind(
        id="knobbly",
        label="knobbly spud",
        phrase="a knobbly garden spud",
        flatness=1,
        tags={"potato", "knobbly"},
    ),
}

RECIPIENTS = {
    "sibling": Recipient(
        id="sibling",
        label="the other child",
        relation_word="sibling",
        tags={"sibling", "surprise"},
    ),
    "parent": Recipient(
        id="parent",
        label="the parent",
        relation_word="parent",
        tags={"parent", "surprise"},
    ),
    "grandparent": Recipient(
        id="grandparent",
        label="Grandma",
        relation_word="grandparent",
        tags={"grandparent", "surprise"},
    ),
}

REPAIRS = {
    "share_surprise": Repair(
        id="share_surprise",
        label="share the surprise",
        allows_for={"sibling"},
        qa_text="gave the surprise card to the hurt child and let the surprise belong to both of them",
        tags={"sharing", "apology"},
    ),
    "second_print": Repair(
        id="second_print",
        label="make a second print together",
        allows_for={"sibling", "parent", "grandparent"},
        qa_text="made a second little print together so no one was left outside the surprise",
        tags={"sharing", "apology", "making_together"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Ivy", "Wren", "June", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Ben", "Arlo", "Finn", "Jude", "Noah"]
TRAITS = ["gentle", "eager", "careful", "sleepy", "warm-hearted", "curious"]


def compatible_potato(motif: Motif, potato: PotatoKind) -> bool:
    return potato.flatness >= motif.needs_flatness


def compatible_repair(recipient: Recipient, repair: Repair) -> bool:
    return recipient.id in repair.allows_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for motif_id, motif in MOTIFS.items():
        for potato_id, potato in POTATOES.items():
            if not compatible_potato(motif, potato):
                continue
            for recipient_id, recipient in RECIPIENTS.items():
                for repair_id, repair in REPAIRS.items():
                    if compatible_repair(recipient, repair):
                        combos.append((motif_id, potato_id, recipient_id, repair_id))
    return sorted(combos)


@dataclass
class StoryParams:
    motif: str
    potato: str
    recipient: str
    repair: str
    planner_name: str
    planner_gender: str
    other_name: str
    other_gender: str
    parent: str
    planner_trait: str
    other_trait: str
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


def explain_potato_rejection(motif: Motif, potato: PotatoKind) -> str:
    return (
        f"(No story: {potato.phrase} is too uneven for {motif.article} stamp. "
        f"{motif.article.capitalize()} needs a flatter cut face, so choose a rounder spud.)"
    )


def explain_repair_rejection(recipient: Recipient, repair: Repair) -> str:
    targets = ", ".join(sorted(repair.allows_for))
    return (
        f"(No story: repair '{repair.id}' only works when the surprise is for {targets}. "
        f"If the surprise is for {recipient.relation_word}, the hurt child needs a different way back in.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.repair == "share_surprise" and params.recipient == "sibling":
        return "gifted"
    return "together"


def count_and_whisper(world: World, planner: Entity, other: Entity, potato: PotatoKind) -> None:
    basket = world.get("basket")
    planner.memes["calm"] += 1
    other.memes["calm"] += 1
    basket.meters["expected_count"] = 18
    basket.meters["in_basket"] = 18
    world.say(
        f"After supper, when the kitchen had grown golden and quiet, {planner.id} and "
        f"{other.id} helped count the potatoes for tomorrow's soup."
    )
    world.say(
        f"They counted in whispers because bedtime was close: first, second, third, and on and on "
        f"until the eighteenth potato rested in {planner.pronoun('possessive')} palm."
    )
    world.say(
        f"It was {potato.phrase}, and somehow it looked too special to tumble into the bowl with the others."
    )


def spark_surprise(world: World, planner: Entity, motif: Motif, recipient: Recipient) -> None:
    planner.memes["secret"] += 1
    planner.memes["delight"] += 1
    spud = world.get("spud")
    basket = world.get("basket")
    basket.meters["in_basket"] = 17
    basket.meters["missing"] = 1
    spud.meters["hidden"] = 1
    target_name = {
        "sibling": world.get("other").id,
        "parent": world.get("parent").label_word,
        "grandparent": "Grandma",
    }[recipient.id]
    world.facts["target_name"] = target_name
    world.say(
        f"A tiny idea bloomed in {planner.id}'s mind. The raw spud had a smooth side just right for "
        f"{motif.article} stamp, and {planner.pronoun()} wanted to make a sleepy surprise for {target_name}."
    )
    world.say(
        f"So {planner.pronoun()} slipped the eighteenth spud behind the flour tin and smiled to {planner.pronoun('object')}self."
    )


def notice_gap(world: World, other: Entity) -> None:
    propagate(world, narrate=False)
    basket = world.get("basket")
    if basket.meters["missing"] >= THRESHOLD:
        world.say(
            f"When {other.id} looked into the bowl again, {other.pronoun()} blinked. "
            f"There should have been eighteen potatoes, but now there were only seventeen."
        )


def accuse(world: World, planner: Entity, other: Entity) -> None:
    other.memes["accused"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Did you keep the nicest one for yourself?" {other.id} asked. The words came out sharper than '
        f"{other.pronoun()} meant them to."
    )
    if planner.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{planner.id}'s face changed at once. {planner.pronoun().capitalize()} pressed {planner.pronoun('possessive')} lips together "
            f"and looked down at the floorboards."
        )


def slow_down(world: World, parent: Entity, planner: Entity, other: Entity) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} was folding towels nearby and heard the hurt in the room."
    )
    world.say(
        f'"Slow voices," {parent.pronoun()} said softly. "A misunderstanding can sound bigger than it is. '
        f'Let us see what happened before bedtime grows any heavier."'
    )
    other.memes["listening"] += 1
    planner.memes["listening"] += 1


def reveal_surprise(world: World, planner: Entity, other: Entity, motif: Motif, recipient: Recipient) -> None:
    spud = world.get("spud")
    card = world.get("card")
    spud.meters["cut"] = 1
    card.meters["painted"] = 1
    card.attrs["motif"] = motif.id
    planner.memes["bravery"] += 1
    world.say(
        f"Very carefully, {planner.id} reached behind the flour tin and brought out the hidden potato, "
        f"now cut in half so its pale inside showed."
    )
    world.say(
        f'"I was making a stamp," {planner.pronoun()} whispered. "A raw spud stamp. See?"'
    )
    target_name = world.facts["target_name"]
    world.say(
        f"Beside it lay a little card with {motif.paint} on it, and on the paper bloomed {motif.article} for {target_name}."
    )
    world.facts["revealed"] = True
    if recipient.id != "sibling":
        other.memes["left_out"] += 1


def apology(world: World, other: Entity, planner: Entity) -> None:
    other.memes["apologized"] += 1
    other.memes["guilt"] += 1
    world.say(
        f'{other.id} swallowed hard. "I am sorry," {other.pronoun()} said. '
        f'"I thought you were being mean, and I did not ask kindly."'
    )


def repair_share_surprise(world: World, planner: Entity, other: Entity, motif: Motif) -> None:
    planner.memes["forgiven"] += 1
    other.memes["included"] += 1
    planner.memes["delight"] += 1
    world.say(
        f"{planner.id} looked up again and gave a small smile. "
        f'"It was for you," {planner.pronoun()} said. "I wanted to tuck {motif.article} by your pillow."'
    )
    world.say(
        f"{other.id}'s eyes went wide with surprise. The hurt melted fast, because the missing spud had been hidden for love, not for greed."
    )
    propagate(world, narrate=False)


def repair_second_print(world: World, planner: Entity, other: Entity, motif: Motif, recipient: Recipient) -> None:
    planner.memes["forgiven"] += 1
    other.memes["included"] += 1
    other.memes["delight"] += 1
    card = world.get("card")
    card.meters["painted"] += 1
    if recipient.id == "parent":
        destination = f"{world.get('parent').label_word}'s bedside table"
    elif recipient.id == "grandparent":
        destination = "the envelope for Grandma"
    else:
        destination = f"{other.id}'s pillow"
    world.say(
        f'"We can make two," {planner.id} said after a moment. "One for {world.facts["target_name"]}, and one for us to keep."'
    )
    world.say(
        f"So the children pressed the cut potato into the paint together and stamped a second {motif.label}. "
        f"This time, nobody stood outside the surprise."
    )
    world.say(
        f"One card was set aside for {destination}, and the other was left where both children could look at it."
    )
    propagate(world, narrate=False)


def bedtime_close(world: World, planner: Entity, other: Entity, parent: Entity, motif: Motif) -> None:
    planner.memes["sleepy"] += 1
    other.memes["sleepy"] += 1
    world.say(
        f"Soon the towels were put away, the paint was wiped from small fingers, and {parent.label_word} led them down the dim hall."
    )
    world.say(
        f"In bed, {planner.id} and {other.id} whispered one last good night to each other, and the room felt light again."
    )
    world.say(motif.ending_image)


def tell(
    motif: Motif,
    potato: PotatoKind,
    recipient: Recipient,
    repair: Repair,
    planner_name: str = "Lila",
    planner_gender: str = "girl",
    other_name: str = "Theo",
    other_gender: str = "boy",
    parent_type: str = "mother",
    planner_trait: str = "gentle",
    other_trait: str = "curious",
) -> World:
    world = World()
    planner = world.add(
        Entity(
            id=planner_name,
            kind="character",
            type=planner_gender,
            role="planner",
            traits=[planner_trait],
        )
    )
    other = world.add(
        Entity(
            id=other_name,
            kind="character",
            type=other_gender,
            role="other",
            traits=[other_trait],
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    basket = world.add(Entity(id="basket", type="basket", label="mixing bowl"))
    spud = world.add(Entity(id="spud", type="potato", label=potato.label))
    card = world.add(Entity(id="card", type="card", label="little card"))

    basket.meters["expected_count"] = 0
    basket.meters["in_basket"] = 0
    basket.meters["missing"] = 0
    spud.meters["hidden"] = 0
    spud.meters["cut"] = 0
    card.meters["painted"] = 0

    world.facts.update(
        planner=planner,
        other=other,
        parent=parent,
        basket=basket,
        spud=spud,
        card=card,
        motif=motif,
        potato_cfg=potato,
        recipient=recipient,
        repair=repair,
        target_name="",
        revealed=False,
    )

    count_and_whisper(world, planner, other, potato)
    world.para()
    spark_surprise(world, planner, motif, recipient)
    notice_gap(world, other)
    accuse(world, planner, other)

    world.para()
    slow_down(world, parent, planner, other)
    reveal_surprise(world, planner, other, motif, recipient)
    apology(world, other, planner)

    if repair.id == "share_surprise":
        repair_share_surprise(world, planner, other, motif)
    else:
        repair_second_print(world, planner, other, motif, recipient)

    world.para()
    bedtime_close(world, planner, other, parent, motif)

    world.facts.update(
        missing_spud=world.get("basket").meters["missing"] >= THRESHOLD,
        planner_hurt=planner.memes["hurt"] >= THRESHOLD,
        reconciled=planner.memes["relief"] >= THRESHOLD and other.memes["relief"] >= THRESHOLD,
        outcome=outcome_of(
            StoryParams(
                motif=motif.id,
                potato=potato.id,
                recipient=recipient.id,
                repair=repair.id,
                planner_name=planner_name,
                planner_gender=planner_gender,
                other_name=other_name,
                other_gender=other_gender,
                parent=parent_type,
                planner_trait=planner_trait,
                other_trait=other_trait,
                seed=None,
            )
        ),
    )
    return world


KNOWLEDGE = {
    "potato": [
        (
            "What is a potato?",
            "A potato is a plant food that grows under the ground. People cook potatoes to eat them, but a raw one can also be used for simple stamping art with a grown-up's help.",
        )
    ],
    "potato_stamp": [
        (
            "What is a potato stamp?",
            "A potato stamp is a cut potato used like a little print block. You dip the cut side in paint and press it onto paper to make a shape.",
        )
    ],
    "raw": [
        (
            "What does raw mean?",
            "Raw means not cooked yet. A raw potato is still firm and plain, just as it came from the kitchen or garden.",
        )
    ],
    "sharing": [
        (
            "How can sharing fix hurt feelings?",
            "Sharing can help because it shows that there is room for both people. When someone is invited back in, the sad feeling often softens.",
        )
    ],
    "apology": [
        (
            "What makes an apology feel real?",
            "A real apology says what was done wrong and tries to make things better. Gentle words matter most when they are joined to kind actions.",
        )
    ],
    "moon": [
        (
            "Why do bedtime stories use the moon so often?",
            "The moon is quiet, silver, and easy to notice at night. It helps a story feel calm and ready for sleep.",
        )
    ],
    "star": [
        (
            "Why do stars fit bedtime stories?",
            "Stars are small lights in the dark sky. They make night feel wide and wonder-filled instead of lonely.",
        )
    ],
    "cloud": [
        (
            "Why can a cloud feel sleepy in a story?",
            "Clouds drift slowly and softly. That makes them feel gentle, like a thought getting ready to dream.",
        )
    ],
    "bedtime": [
        (
            "Why do people whisper near bedtime?",
            "Whispers are quiet and slow, so they help a room settle down. Soft sounds make it easier for bodies and minds to get ready for sleep.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "potato",
    "potato_stamp",
    "raw",
    "sharing",
    "apology",
    "moon",
    "star",
    "cloud",
    "bedtime",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    planner = f["planner"]
    other = f["other"]
    motif = f["motif"]
    recipient = f["recipient"]
    repair = f["repair"]
    target_name = f["target_name"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "eighteenth", "spud", and "raw", and centers on a surprise and a reconciliation.',
        f"Tell a gentle nighttime story where {planner.id} hides the eighteenth spud to make {motif.article} surprise for {target_name}, and {other.id} misunderstands before the truth comes out.",
        f"Write a soft story about hurt feelings, apology, and repair, ending with {repair.label} and a calm bedtime image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    planner = f["planner"]
    other = f["other"]
    parent = f["parent"]
    motif = f["motif"]
    recipient = f["recipient"]
    repair = f["repair"]
    target_name = f["target_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {planner.id} and {other.id}, two children helping in the kitchen before bed, and their {parent.label_word}. The story follows a misunderstanding between the children and how they mend it.",
        ),
        (
            "What was special about the potato they found?",
            f"It was the eighteenth potato they counted, and {planner.id} thought it was just right for a stamp. Because the spud was still raw and smooth on one side, it could be cut and pressed into paint.",
        ),
        (
            f"Why did {planner.id} hide the spud?",
            f"{planner.id} hid it to make {motif.article} surprise card for {target_name}. The hiding was meant to protect the surprise, but it also made the basket count come up short.",
        ),
        (
            f"Why did {other.id} get upset?",
            f"{other.id} saw that one potato was missing and thought {planner.id} had taken the nicest one unfairly. That wrong guess led to sharp words, and the sharp words hurt {planner.id}'s feelings.",
        ),
        (
            "How was the misunderstanding solved?",
            f"{parent.label_word.capitalize()} slowed everyone down, and then {planner.id} showed the cut raw potato and the painted card. After that, {other.id} apologized, because the missing spud had been hidden for a kind reason instead of a selfish one.",
        ),
    ]
    if repair.id == "share_surprise":
        qa.append(
            (
                "What made the reconciliation feel complete?",
                f"The surprise turned out to be for {other.id}, so the hurt child discovered that love had been underneath the secret all along. That surprise changed the whole meaning of the missing potato, and the two children felt close again.",
            )
        )
    else:
        qa.append(
            (
                "What did the children do after the apology?",
                f"They made a second print together so no one would be left outside the surprise. Making something side by side gave the apology a shape the children could see and hold.",
            )
        )
    if recipient.id == "parent":
        qa.append(
            (
                "Who was the surprise card for?",
                f"It was for their {parent.label_word}. The children turned one secret card into a shared bedtime gift.",
            )
        )
    elif recipient.id == "grandparent":
        qa.append(
            (
                "Who was the surprise card for?",
                "It was for Grandma. The card became a gentle family surprise instead of a private secret.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"potato", "raw", "bedtime"}
    motif = world.facts["motif"]
    repair = world.facts["repair"]
    tags |= set(motif.tags)
    tags |= set(repair.tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        motif="moon",
        potato="oval",
        recipient="sibling",
        repair="share_surprise",
        planner_name="Lila",
        planner_gender="girl",
        other_name="Theo",
        other_gender="boy",
        parent="mother",
        planner_trait="gentle",
        other_trait="curious",
        seed=None,
    ),
    StoryParams(
        motif="star",
        potato="round",
        recipient="parent",
        repair="second_print",
        planner_name="Mina",
        planner_gender="girl",
        other_name="Arlo",
        other_gender="boy",
        parent="father",
        planner_trait="careful",
        other_trait="eager",
        seed=None,
    ),
    StoryParams(
        motif="cloud",
        potato="knobbly",
        recipient="grandparent",
        repair="second_print",
        planner_name="Owen",
        planner_gender="boy",
        other_name="June",
        other_gender="girl",
        parent="mother",
        planner_trait="sleepy",
        other_trait="warm-hearted",
        seed=None,
    ),
    StoryParams(
        motif="moon",
        potato="round",
        recipient="parent",
        repair="second_print",
        planner_name="Nora",
        planner_gender="girl",
        other_name="Finn",
        other_gender="boy",
        parent="father",
        planner_trait="gentle",
        other_trait="careful",
        seed=None,
    ),
    StoryParams(
        motif="star",
        potato="round",
        recipient="sibling",
        repair="share_surprise",
        planner_name="Ben",
        planner_gender="boy",
        other_name="Ivy",
        other_gender="girl",
        parent="mother",
        planner_trait="curious",
        other_trait="sleepy",
        seed=None,
    ),
]


ASP_RULES = r"""
valid(M, P, R, Fix) :- motif(M), potato(P), recipient(R), repair(Fix),
                       needs(M, Need), flatness(P, Flat), Flat >= Need,
                       allowed(Fix, R).

outcome(gifted) :- chosen_recipient(sibling), chosen_repair(share_surprise).
outcome(together) :- not outcome(gifted).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for motif_id, motif in MOTIFS.items():
        lines.append(asp.fact("motif", motif_id))
        lines.append(asp.fact("needs", motif_id, motif.needs_flatness))
    for potato_id, potato in POTATOES.items():
        lines.append(asp.fact("potato", potato_id))
        lines.append(asp.fact("flatness", potato_id, potato.flatness))
    for recipient_id in RECIPIENTS:
        lines.append(asp.fact("recipient", recipient_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for rid in sorted(repair.allows_for):
            lines.append(asp.fact("allowed", repair_id, rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_recipient", params.recipient),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=True, header="### smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: the eighteenth spud, a surprise, and a bedtime reconciliation."
    )
    ap.add_argument("--motif", choices=sorted(MOTIFS))
    ap.add_argument("--potato", choices=sorted(POTATOES))
    ap.add_argument("--recipient", choices=sorted(RECIPIENTS))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.motif is not None and args.motif not in MOTIFS:
        raise StoryError(f"(Unknown motif: {args.motif})")
    if args.potato is not None and args.potato not in POTATOES:
        raise StoryError(f"(Unknown potato: {args.potato})")
    if args.recipient is not None and args.recipient not in RECIPIENTS:
        raise StoryError(f"(Unknown recipient: {args.recipient})")
    if args.repair is not None and args.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {args.repair})")

    if args.motif and args.potato:
        motif = MOTIFS[args.motif]
        potato = POTATOES[args.potato]
        if not compatible_potato(motif, potato):
            raise StoryError(explain_potato_rejection(motif, potato))
    if args.recipient and args.repair:
        recipient = RECIPIENTS[args.recipient]
        repair = REPAIRS[args.repair]
        if not compatible_repair(recipient, repair):
            raise StoryError(explain_repair_rejection(recipient, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.motif is None or combo[0] == args.motif)
        and (args.potato is None or combo[1] == args.potato)
        and (args.recipient is None or combo[2] == args.recipient)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    motif_id, potato_id, recipient_id, repair_id = rng.choice(sorted(combos))
    planner_gender = rng.choice(["girl", "boy"])
    other_gender = rng.choice(["girl", "boy"])
    planner_name = _pick_name(rng, planner_gender)
    other_name = _pick_name(rng, other_gender, avoid=planner_name)
    parent = args.parent or rng.choice(["mother", "father"])
    planner_trait = rng.choice(TRAITS)
    other_trait = rng.choice(TRAITS)
    return StoryParams(
        motif=motif_id,
        potato=potato_id,
        recipient=recipient_id,
        repair=repair_id,
        planner_name=planner_name,
        planner_gender=planner_gender,
        other_name=other_name,
        other_gender=other_gender,
        parent=parent,
        planner_trait=planner_trait,
        other_trait=other_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.motif not in MOTIFS:
        raise StoryError(f"(Unknown motif: {params.motif})")
    if params.potato not in POTATOES:
        raise StoryError(f"(Unknown potato: {params.potato})")
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(Unknown recipient: {params.recipient})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    motif = MOTIFS[params.motif]
    potato = POTATOES[params.potato]
    recipient = RECIPIENTS[params.recipient]
    repair = REPAIRS[params.repair]

    if not compatible_potato(motif, potato):
        raise StoryError(explain_potato_rejection(motif, potato))
    if not compatible_repair(recipient, repair):
        raise StoryError(explain_repair_rejection(recipient, repair))

    world = tell(
        motif=motif,
        potato=potato,
        recipient=recipient,
        repair=repair,
        planner_name=params.planner_name,
        planner_gender=params.planner_gender,
        other_name=params.other_name,
        other_gender=params.other_gender,
        parent_type=params.parent,
        planner_trait=params.planner_trait,
        other_trait=params.other_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (motif, potato, recipient, repair) combos:\n")
        for motif, potato, recipient, repair in combos:
            print(f"  {motif:6} {potato:8} {recipient:11} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.planner_name} and {p.other_name}: {p.motif} / {p.potato} / {p.recipient} / {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
