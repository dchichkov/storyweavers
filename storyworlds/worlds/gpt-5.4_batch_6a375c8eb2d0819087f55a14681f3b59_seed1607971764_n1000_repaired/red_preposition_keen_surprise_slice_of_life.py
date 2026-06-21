#!/usr/bin/env python3
"""
A standalone storyworld for a small slice-of-life surprise story.

A child comes home from school keen to make a small surprise for someone in the
family. Because the class has just learned about prepositions, the child writes
a clue in red pencil telling where the surprise is hidden. The world checks that
the hiding place, the preposition, the kind of paper gift, and the recipient's
ordinary routine all fit together. Some combinations also trigger a gentle turn:
with trickier prepositions, a less careful child drafts the clue wrong at first,
then a grown-up helps fix it before the surprise is found.
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

EASY_PREPOSITIONS = {"in", "on", "under"}
CAREFUL_TRAITS = {"careful", "patient", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "sister", "aunt"}
        male = {"boy", "man", "father", "grandfather", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class SurpriseItem:
    id: str
    label: str
    phrase: str
    kind_tag: str
    making_text: str
    ending_text: str
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
class Spot:
    id: str
    label: str
    room: str
    relation: str
    landmark: str
    phrase: str
    accepts: set[str] = field(default_factory=set)
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
    type: str
    routine_room: str
    routine_text: str
    delight_text: str
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
class Trait:
    id: str
    opening: str
    drafting: str
    careful: bool = False
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


def _r_find_surprise(world: World) -> list[str]:
    note = world.get("note")
    spot = world.get("spot")
    recipient = world.get("recipient")
    surprise = world.get("surprise")
    if note.meters["clear"] < THRESHOLD:
        return []
    if surprise.meters["hidden"] < THRESHOLD:
        return []
    if recipient.meters["searching"] < THRESHOLD:
        return []
    if recipient.attrs.get("room") != spot.attrs.get("room"):
        return []
    sig = ("found", recipient.id, surprise.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    surprise.meters["found"] += 1
    recipient.memes["surprised"] += 1
    recipient.memes["warmth"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="find_surprise", tag="social", apply=_r_find_surprise),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SURPRISES = {
    "drawing": SurpriseItem(
        id="drawing",
        label="drawing",
        phrase="a folded drawing of the family cat",
        kind_tag="flat",
        making_text="She drew a round cat face, then colored the scarf bright red.",
        ending_text="the drawing with the red scarf",
        tags={"drawing", "red"},
    ),
    "bookmark": SurpriseItem(
        id="bookmark",
        label="bookmark",
        phrase="a striped bookmark",
        kind_tag="slim",
        making_text="She cut a long bookmark from card and shaded one stripe red.",
        ending_text="the striped bookmark",
        tags={"bookmark", "red", "reading"},
    ),
    "paper_flower": SurpriseItem(
        id="paper_flower",
        label="paper flower",
        phrase="a paper flower",
        kind_tag="light",
        making_text="She folded a paper flower and brushed the middle with red pencil.",
        ending_text="the paper flower",
        tags={"paper_flower", "red"},
    ),
}

SPOTS = {
    "under_cushion": Spot(
        id="under_cushion",
        label="blue cushion",
        room="living_room",
        relation="under",
        landmark="blue cushion",
        phrase="under the blue cushion on the sofa",
        accepts={"flat", "slim", "light"},
        tags={"sofa", "living_room"},
    ),
    "behind_storybook": Spot(
        id="behind_storybook",
        label="storybook",
        room="living_room",
        relation="behind",
        landmark="big storybook",
        phrase="behind the big storybook on the side table",
        accepts={"flat", "slim"},
        tags={"book", "living_room"},
    ),
    "in_recipe_book": Spot(
        id="in_recipe_book",
        label="recipe book",
        room="kitchen",
        relation="in",
        landmark="recipe book",
        phrase="in the recipe book by the fruit bowl",
        accepts={"flat", "slim"},
        tags={"book", "kitchen"},
    ),
    "beside_kettle": Spot(
        id="beside_kettle",
        label="kettle",
        room="kitchen",
        relation="beside",
        landmark="silver kettle",
        phrase="beside the silver kettle",
        accepts={"flat", "slim", "light"},
        tags={"kettle", "kitchen"},
    ),
    "on_shoe_rack": Spot(
        id="on_shoe_rack",
        label="shoe rack",
        room="entryway",
        relation="on",
        landmark="shoe rack",
        phrase="on the shoe rack by the door",
        accepts={"slim", "light"},
        tags={"entryway", "shoe_rack"},
    ),
}

RECIPIENTS = {
    "mother": Recipient(
        id="mother",
        label="Mom",
        type="mother",
        routine_room="kitchen",
        routine_text="Mom always stopped in the kitchen first to set down her bag and start the kettle.",
        delight_text="Mom laughed softly and pressed the surprise to her chest.",
        tags={"mother", "kitchen"},
    ),
    "father": Recipient(
        id="father",
        label="Dad",
        type="father",
        routine_room="living_room",
        routine_text="Dad liked to sit in the living room for a minute before dinner and smooth the sofa cushion back into place.",
        delight_text="Dad's eyebrows jumped up, and then he grinned all over his face.",
        tags={"father", "living_room"},
    ),
    "grandmother": Recipient(
        id="grandmother",
        label="Grandma",
        type="grandmother",
        routine_room="living_room",
        routine_text="Grandma liked to settle in the living room with a book before supper.",
        delight_text="Grandma gave a warm little gasp and smiled the smile she used for very sweet things.",
        tags={"grandmother", "living_room", "reading"},
    ),
    "sister": Recipient(
        id="sister",
        label="Mara",
        type="sister",
        routine_room="entryway",
        routine_text="Big sister Mara always dropped her school shoes by the door and reached for the top of the shoe rack.",
        delight_text="Mara blinked, then burst out laughing and hugged the surprise carefully.",
        tags={"sister", "entryway"},
    ),
}

TRAITS = {
    "careful": Trait(
        id="careful",
        opening="careful enough to line up crayons by size",
        drafting="She read the clue twice before writing the last word.",
        careful=True,
    ),
    "patient": Trait(
        id="patient",
        opening="patient enough to fold paper edges slowly",
        drafting="She whispered the clue to herself and took her time with each letter.",
        careful=True,
    ),
    "steady": Trait(
        id="steady",
        opening="steady even when she was excited",
        drafting="She kept one finger on the hiding place while she wrote the clue.",
        careful=True,
    ),
    "dreamy": Trait(
        id="dreamy",
        opening="dreamy, with ideas arriving faster than pencils could move",
        drafting="Her thoughts skipped ahead of her hand, and the first clue came out in a rush.",
        careful=False,
    ),
    "bouncy": Trait(
        id="bouncy",
        opening="so bouncy that her slippers slapped the floor",
        drafting="She wrote fast because the surprise felt too good to keep waiting.",
        careful=False,
    ),
    "hasty": Trait(
        id="hasty",
        opening="quick with ideas and quicker still with her hand",
        drafting="She scribbled the clue in one breath, then stared at it with a wrinkled nose.",
        careful=False,
    ),
}

GIRL_NAMES = ["Lina", "Ava", "Nora", "Mia", "Ruby", "Ella", "Sana", "Poppy", "June", "Tess"]
BOY_NAMES = ["Owen", "Leo", "Max", "Ben", "Theo", "Eli", "Noah", "Sam", "Finn", "Jack"]

KNOWLEDGE = {
    "preposition": [
        (
            "What is a preposition?",
            "A preposition is a little word like in, on, under, behind, or beside. It helps tell where something is.",
        )
    ],
    "drawing": [
        (
            "Why do people make drawings for someone they love?",
            "A drawing can show care even when it is simple. Making it by hand makes the gift feel personal.",
        )
    ],
    "bookmark": [
        (
            "What is a bookmark for?",
            "A bookmark helps you keep your place in a book. It slips between pages so you can find your spot again later.",
        )
    ],
    "paper_flower": [
        (
            "Why can a paper flower be a nice surprise?",
            "A paper flower is small and handmade, so it feels thoughtful. It can brighten a table or a shelf without costing anything.",
        )
    ],
    "reading": [
        (
            "Why do some people keep a bookmark in a book?",
            "They keep a bookmark there so they can stop reading and begin again at the right page. It saves them from having to search.",
        )
    ],
    "red": [
        (
            "Why does a red mark stand out?",
            "Red is a bright color that catches your eye quickly. People often use it when they want something small to be easy to notice.",
        )
    ],
    "surprise": [
        (
            "What makes a good surprise feel kind instead of scary?",
            "A kind surprise is gentle and safe, and it is made to make someone feel loved. The fun part is the happy feeling, not a fright.",
        )
    ],
}

KNOWLEDGE_ORDER = ["preposition", "drawing", "bookmark", "paper_flower", "reading", "red", "surprise"]


def spot_works_for_item(spot: Spot, surprise: SurpriseItem) -> bool:
    return surprise.kind_tag in spot.accepts


def recipient_reaches_spot(recipient: Recipient, spot: Spot) -> bool:
    return recipient.routine_room == spot.room


def valid_combo(recipient: Recipient, surprise: SurpriseItem, spot: Spot, preposition: str) -> bool:
    return (
        spot.relation == preposition
        and spot_works_for_item(spot, surprise)
        and recipient_reaches_spot(recipient, spot)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for rid, recipient in RECIPIENTS.items():
        for sid, surprise in SURPRISES.items():
            for spot_id, spot in SPOTS.items():
                for prep in sorted({spot.relation}):
                    if valid_combo(recipient, surprise, spot, prep):
                        combos.append((rid, sid, spot_id, prep))
    return combos


def clue_needs_correction(preposition: str, trait: Trait) -> bool:
    return preposition not in EASY_PREPOSITIONS and not trait.careful


def outcome_of(params: "StoryParams") -> str:
    trait = TRAITS[params.trait]
    return "corrected" if clue_needs_correction(params.preposition, trait) else "smooth"


def explain_combo(recipient: Recipient, surprise: SurpriseItem, spot: Spot, preposition: str) -> str:
    if preposition != spot.relation:
        return (
            f"(No story: the clue says '{preposition}', but {spot.phrase} calls for "
            f"the preposition '{spot.relation}'. The hiding place and the clue must match.)"
        )
    if not spot_works_for_item(spot, surprise):
        return (
            f"(No story: {surprise.phrase} does not fit well at {spot.phrase}. "
            f"Choose a flatter or lighter surprise, or a different hiding place.)"
        )
    if not recipient_reaches_spot(recipient, spot):
        return (
            f"(No story: {recipient.label} does not normally go to the {spot.room.replace('_', ' ')} first, "
            f"so the surprise would not be found naturally there.)"
        )
    return "(No story: this surprise setup does not make sense in the world.)"


def predict_find(recipient: Recipient, surprise: SurpriseItem, spot: Spot, preposition: str, trait: Trait) -> dict:
    clear = 0.0 if clue_needs_correction(preposition, trait) else 1.0
    return {
        "needs_correction": clear < THRESHOLD,
        "found_after_fix": recipient_reaches_spot(recipient, spot) and spot_works_for_item(spot, surprise),
    }


def introduce(world: World, child: Entity, trait: Trait, recipient: Entity) -> None:
    world.say(
        f"After school, {child.id} came home {trait.opening}. {child.pronoun().capitalize()} was keen to make a small surprise for {recipient.label_word} before the evening grew busy."
    )


def lesson_memory(world: World, child: Entity) -> None:
    world.say(
        f"That afternoon, {child.id}'s class had learned that a preposition was a tiny word that told where something was. The idea stayed in {child.pronoun('possessive')} head like a little bell."
    )


def make_surprise(world: World, child: Entity, surprise_cfg: SurpriseItem) -> None:
    surprise = world.get("surprise")
    child.memes["care"] += 1
    surprise.meters["made"] += 1
    world.say(
        f"At the table, {child.pronoun()} made {surprise_cfg.phrase}. {surprise_cfg.making_text}"
    )


def plan_hiding(world: World, spot: Spot, recipient: Recipient) -> None:
    world.say(
        f"{recipient.routine_text} So {world.get('child').id} chose a place {recipient.label} was likely to notice: {spot.phrase}."
    )


def draft_clue(world: World, child: Entity, trait: Trait, spot: Spot, chosen_prep: str) -> None:
    note = world.get("note")
    child.memes["anticipation"] += 1
    world.say(trait.drafting)
    if chosen_prep == spot.relation:
        note.meters["drafted"] += 1
        world.say(
            f"With a red pencil, {child.id} wrote a clue on a little card: "
            f"\"Look {chosen_prep} the {spot.landmark}.\""
        )


def wrong_first_try(spot: Spot) -> str:
    confusing = {
        "behind": "beside",
        "beside": "behind",
        "under": "on",
        "on": "under",
        "in": "behind",
    }
    return confusing.get(spot.relation, "near")


def revise_clue(world: World, child: Entity, helper: Entity, spot: Spot) -> None:
    note = world.get("note")
    bad = wrong_first_try(spot)
    note.meters["drafted"] += 1
    note.meters["wrong"] += 1
    child.memes["worry"] += 1
    world.say(
        f"At first {child.pronoun()} wrote, \"Look {bad} the {spot.landmark}.\" Then {helper.label_word} paused beside the table and asked, \"Do you mean {bad}, or do you mean {spot.relation}?\""
    )
    world.say(
        f"{child.id} looked at the hiding place, then at the card, and felt a tiny flush in {child.pronoun('possessive')} cheeks. {child.pronoun().capitalize()} erased one word and wrote the clue again in neat red letters: \"Look {spot.relation} the {spot.landmark}.\""
    )
    note.meters["rewritten"] += 1
    note.meters["clear"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["learning"] += 1


def finalize_clue(world: World, child: Entity, spot: Spot) -> None:
    note = world.get("note")
    note.meters["clear"] = 1.0
    child.memes["confidence"] += 1
    world.say(
        f"The clue felt just right. It used the preposition that matched the place, not just the one that sounded nice."
    )


def hide_surprise(world: World, child: Entity, spot: Spot) -> None:
    surprise = world.get("surprise")
    surprise.meters["hidden"] += 1
    surprise.attrs["room"] = spot.room
    world.say(
        f"{child.id} tucked the surprise away {spot.phrase} and set the little clue card where it would be seen."
    )


def recipient_arrives(world: World, recipient: Entity) -> None:
    world.say(
        f"A little later, {recipient.label} came in. The house was ordinary in every other way: shoes by the door, a kettle waiting, late light on the floor."
    )


def read_and_search(world: World, recipient: Entity, spot: Spot) -> None:
    recipient.meters["searching"] += 1
    recipient.attrs["room"] = spot.room
    propagate(world, narrate=False)
    world.say(
        f"{recipient.label} found the card, read the red clue, and followed it to the {spot.room.replace('_', ' ')}."
    )


def found_scene(world: World, recipient: Entity, child: Entity, surprise_cfg: SurpriseItem) -> None:
    world.say(
        f"There, {recipient.pronoun()} found {surprise_cfg.ending_text}. {RECIPIENTS[world.facts['recipient_cfg'].id].delight_text}"
    )
    world.say(
        f"{child.id} could not keep the secret face any longer and smiled back. The whole surprise was small, but the room felt warmer because it had been made with care."
    )


def ending_image(world: World, recipient: Entity, child: Entity, surprise_cfg: SurpriseItem) -> None:
    child.memes["joy"] += 1
    recipient.memes["joy"] += 1
    world.say(
        f"By supper time, {surprise_cfg.ending_text} was still out where everyone could see it, and {child.id} kept glancing at it with a pleased, quiet smile."
    )


def tell(
    surprise_cfg: SurpriseItem,
    spot_cfg: Spot,
    recipient_cfg: Recipient,
    trait_cfg: Trait,
    preposition: str,
    child_name: str = "Lina",
    child_type: str = "girl",
    helper_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the grown-up"))
    recipient = world.add(
        Entity(
            id="recipient",
            kind="character",
            type=recipient_cfg.type,
            label=recipient_cfg.label,
            attrs={"room": ""},
        )
    )
    surprise = world.add(
        Entity(
            id="surprise",
            type="gift",
            label=surprise_cfg.label,
            attrs={"room": ""},
        )
    )
    note = world.add(
        Entity(
            id="note",
            type="note",
            label="clue card",
        )
    )
    spot = world.add(
        Entity(
            id="spot",
            type="spot",
            label=spot_cfg.label,
            attrs={"room": spot_cfg.room, "relation": spot_cfg.relation},
        )
    )

    world.facts["recipient_cfg"] = recipient_cfg
    world.facts["surprise_cfg"] = surprise_cfg
    world.facts["spot_cfg"] = spot_cfg
    world.facts["trait_cfg"] = trait_cfg
    world.facts["preposition"] = preposition

    child.memes["keen"] = 1.0
    child.memes["joy"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["pride"] = 0.0
    recipient.meters["searching"] = 0.0
    recipient.memes["surprised"] = 0.0
    note.meters["clear"] = 0.0
    note.meters["drafted"] = 0.0
    note.meters["rewritten"] = 0.0
    surprise.meters["made"] = 0.0
    surprise.meters["hidden"] = 0.0
    surprise.meters["found"] = 0.0

    introduce(world, child, trait_cfg, recipient)
    lesson_memory(world, child)
    make_surprise(world, child, surprise_cfg)

    world.para()
    plan_hiding(world, spot_cfg, recipient_cfg)
    pred = predict_find(recipient_cfg, surprise_cfg, spot_cfg, preposition, trait_cfg)
    world.facts["predicted_needs_correction"] = pred["needs_correction"]

    if pred["needs_correction"]:
        revise_clue(world, child, helper, spot_cfg)
    else:
        draft_clue(world, child, trait_cfg, spot_cfg, preposition)
        finalize_clue(world, child, spot_cfg)
    hide_surprise(world, child, spot_cfg)

    world.para()
    recipient_arrives(world, recipient)
    read_and_search(world, recipient, spot_cfg)
    found_scene(world, recipient, child, surprise_cfg)
    ending_image(world, recipient, child, surprise_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        recipient=recipient,
        note=note,
        surprise=surprise,
        spot=spot,
        outcome="corrected" if note.meters["rewritten"] >= THRESHOLD else "smooth",
        found=surprise.meters["found"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    recipient: str
    surprise: str
    spot: str
    preposition: str
    child_name: str
    child_gender: str
    helper: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    recipient_cfg = f["recipient_cfg"]
    surprise_cfg = f["surprise_cfg"]
    spot_cfg = f["spot_cfg"]
    prep = f["preposition"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short slice-of-life story for a 3-to-5-year-old where a child makes a surprise and writes a clue with the preposition "{prep}". Include the word "red" and the word "keen".',
        f"Tell a gentle home story where {child.id} hides {surprise_cfg.phrase} {spot_cfg.phrase} for {recipient_cfg.label} to find.",
    ]
    if outcome == "corrected":
        prompts.append(
            "Write a sweet story where a child first uses the wrong place-word in a clue, then fixes it before the surprise is found."
        )
    else:
        prompts.append(
            "Write a simple story where a child uses a school lesson about prepositions to make a family surprise work perfectly."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    recipient = f["recipient"]
    surprise_cfg = f["surprise_cfg"]
    spot_cfg = f["spot_cfg"]
    prep = f["preposition"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who came home keen to make a surprise for {recipient.label}. The story follows the small steps that turned an ordinary afternoon into a loving one.",
        ),
        (
            f"What surprise did {child.id} make?",
            f"{child.pronoun('subject').capitalize()} made {surprise_cfg.phrase}. {surprise_cfg.making_text}",
        ),
        (
            "Why did the clue card matter?",
            f"The clue card told where the surprise was hidden. It used the preposition '{prep}' so {recipient.label} would know exactly how to look.",
        ),
        (
            f"Where was the surprise hidden?",
            f"It was hidden {spot_cfg.phrase}. That place fit both the gift and {recipient.label}'s usual routine, so the surprise could be found naturally.",
        ),
    ]
    if outcome == "corrected":
        qa.append(
            (
                "Did anything almost go wrong?",
                f"Yes. {child.id} first chose the wrong place-word for the clue, and that could have sent {recipient.label} to the wrong spot. A grown-up helped {child.pronoun('object')} notice the mistake, so the clue was rewritten in red and the surprise still worked.",
            )
        )
    else:
        qa.append(
            (
                f"How did {child.id}'s school lesson help?",
                f"The lesson about prepositions helped {child.id} match the clue to the hiding place. Because the word was right from the start, {recipient.label} could follow the note without confusion.",
            )
        )
    qa.append(
        (
            f"How did {recipient.label} react?",
            f"{recipient.label} was surprised and pleased when {recipient.pronoun('subject')} found the gift. The happy reaction mattered because it showed {child.id} that a small, thoughtful surprise could brighten the whole room.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"preposition", "surprise", "red"} | set(f["surprise_cfg"].tags) | set(f["recipient_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        recipient="father",
        surprise="drawing",
        spot="under_cushion",
        preposition="under",
        child_name="Lina",
        child_gender="girl",
        helper="mother",
        trait="careful",
    ),
    StoryParams(
        recipient="mother",
        surprise="bookmark",
        spot="in_recipe_book",
        preposition="in",
        child_name="Owen",
        child_gender="boy",
        helper="father",
        trait="patient",
    ),
    StoryParams(
        recipient="grandmother",
        surprise="bookmark",
        spot="behind_storybook",
        preposition="behind",
        child_name="Ruby",
        child_gender="girl",
        helper="mother",
        trait="dreamy",
    ),
    StoryParams(
        recipient="sister",
        surprise="paper_flower",
        spot="on_shoe_rack",
        preposition="on",
        child_name="Ben",
        child_gender="boy",
        helper="mother",
        trait="bouncy",
    ),
    StoryParams(
        recipient="mother",
        surprise="paper_flower",
        spot="beside_kettle",
        preposition="beside",
        child_name="Ella",
        child_gender="girl",
        helper="father",
        trait="hasty",
    ),
]


ASP_RULES = r"""
valid(R,S,Sp,P) :- recipient(R), surprise(S), spot(Sp), preposition(P),
                   relation(Sp,P), accepts(Sp,K), surprise_kind(S,K),
                   routine_room(R,Room), spot_room(Sp,Room).

careful_trait(T) :- trait(T), is_careful(T).
easy_prep(P) :- preposition(P), prep_easy(P).

needs_correction :- chosen_prep(P), not easy_prep(P), chosen_trait(T), not careful_trait(T).

outcome(corrected) :- needs_correction.
outcome(smooth) :- not needs_correction.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, recipient in RECIPIENTS.items():
        lines.append(asp.fact("recipient", rid))
        lines.append(asp.fact("routine_room", rid, recipient.routine_room))
    for sid, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("surprise_kind", sid, surprise.kind_tag))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("relation", spot_id, spot.relation))
        lines.append(asp.fact("spot_room", spot_id, spot.room))
        for kind_tag in sorted(spot.accepts):
            lines.append(asp.fact("accepts", spot_id, kind_tag))
    all_preps = sorted({spot.relation for spot in SPOTS.values()})
    for prep in all_preps:
        lines.append(asp.fact("preposition", prep))
        if prep in EASY_PREPOSITIONS:
            lines.append(asp.fact("prep_easy", prep))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        if trait.careful:
            lines.append(asp.fact("is_careful", trait_id))
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
            asp.fact("chosen_prep", params.preposition),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(200):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child makes a small household surprise with a preposition clue."
    )
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--preposition", choices=sorted({spot.relation for spot in SPOTS.values()}))
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(GIRL_NAMES)
    return rng.choice(BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.recipient and args.surprise and args.spot and args.preposition:
        recipient = RECIPIENTS[args.recipient]
        surprise = SURPRISES[args.surprise]
        spot = SPOTS[args.spot]
        if not valid_combo(recipient, surprise, spot, args.preposition):
            raise StoryError(explain_combo(recipient, surprise, spot, args.preposition))

    combos = [
        combo
        for combo in valid_combos()
        if (args.recipient is None or combo[0] == args.recipient)
        and (args.surprise is None or combo[1] == args.surprise)
        and (args.spot is None or combo[2] == args.spot)
        and (args.preposition is None or combo[3] == args.preposition)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    recipient_id, surprise_id, spot_id, preposition = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or pick_name(rng, child_gender)
    helper = args.helper or ("father" if recipient_id == "mother" else "mother")
    trait = args.trait or rng.choice(sorted(TRAITS))

    return StoryParams(
        recipient=recipient_id,
        surprise=surprise_id,
        spot=spot_id,
        preposition=preposition,
        child_name=child_name,
        child_gender=child_gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(Unknown recipient: {params.recipient})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.preposition not in {spot.relation for spot in SPOTS.values()}:
        raise StoryError(f"(Unknown preposition: {params.preposition})")

    recipient = RECIPIENTS[params.recipient]
    surprise = SURPRISES[params.surprise]
    spot = SPOTS[params.spot]
    if not valid_combo(recipient, surprise, spot, params.preposition):
        raise StoryError(explain_combo(recipient, surprise, spot, params.preposition))

    world = tell(
        surprise_cfg=surprise,
        spot_cfg=spot,
        recipient_cfg=recipient,
        trait_cfg=TRAITS[params.trait],
        preposition=params.preposition,
        child_name=params.child_name,
        child_type="girl" if params.child_gender == "girl" else "boy",
        helper_type=params.helper,
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
        print(f"{len(combos)} compatible (recipient, surprise, spot, preposition) combos:\n")
        for recipient, surprise, spot, prep in combos:
            print(f"  {recipient:12} {surprise:12} {spot:18} {prep}")
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
            header = (
                f"### {p.child_name}: {p.surprise} for {p.recipient} "
                f"({p.preposition} / {p.spot}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
