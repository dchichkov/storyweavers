#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py
============================================================================

A standalone story world about a tiny imp, a transformed keepsake, and a
mystery that must be solved before dawn seals the spell.

This world models a small mystery domain:
- a child treasures a keepsake,
- an imp transforms it in the night,
- a clue points toward the imp's hiding place,
- the child and a grown-up choose a sensible remedy,
- and if they are too late, the curse hardens into a bad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py --curse moth --place attic
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py --remedy moonwater
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py --json
    python storyworlds/worlds/gpt-5.4/imp_transformation_mystery_to_solve_bad_ending.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    from_who: str
    use_text: str
    material: str
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
class Curse:
    id: str
    form_label: str
    phrase: str
    onset: str
    clue: str
    hide_tag: str
    remedy_kind: str
    hardness: int
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
class Place:
    id: str
    label: str
    phrase: str
    clue_text: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    kind: str
    power: int
    sense: int
    action: str
    fail_action: str
    qa_text: str
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


def _r_curse_worry(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    child = world.get("child")
    if keepsake.meters["cursed"] >= THRESHOLD:
        sig = ("curse_worry", keepsake.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            child.memes["wonder"] += 1
            world.facts["mystery_started"] = True
            out.append("__mystery__")
    return out


def _r_clue_suspicion(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("mystery_started"):
        return out
    child = world.get("child")
    helper = world.get("helper")
    sig = ("suspicion",)
    if sig not in world.fired:
        world.fired.add(sig)
        child.memes["curiosity"] += 1
        helper.memes["concern"] += 1
        out.append("__clue__")
    return out


def _r_dawn_loss(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    if keepsake.meters["sealed"] >= THRESHOLD:
        sig = ("loss", keepsake.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["sadness"] += 1
            world.get("helper").memes["sadness"] += 1
            world.get("imp").memes["glee"] += 1
            out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule(name="curse_worry", tag="emotional", apply=_r_curse_worry),
    Rule(name="clue_suspicion", tag="social", apply=_r_clue_suspicion),
    Rule(name="dawn_loss", tag="ending", apply=_r_dawn_loss),
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


def clue_matches_place(curse: Curse, place: Place) -> bool:
    return curse.hide_tag in place.tags


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def can_reverse(curse: Curse, remedy: Remedy) -> bool:
    return curse.remedy_kind == remedy.kind


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for curse_id, curse in CURSES.items():
        for place_id, place in PLACES.items():
            for remedy_id, remedy in REMEDIES.items():
                if clue_matches_place(curse, place) and can_reverse(curse, remedy) and remedy.sense >= SENSE_MIN:
                    combos.append((curse_id, place_id, remedy_id))
    return combos


def curse_severity(curse: Curse, delay: int) -> int:
    return curse.hardness + delay


def is_reversed(curse: Curse, remedy: Remedy, delay: int) -> bool:
    return remedy.power >= curse_severity(curse, delay)


def predict_hideout(world: World, curse: Curse) -> dict:
    place = next((p for p in PLACES.values() if clue_matches_place(curse, p)), None)
    return {
        "clue": curse.clue,
        "place": place.id if place else "",
        "place_label": place.label if place else "",
    }


def introduce(world: World, child: Entity, helper: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"{child.id} loved mysteries almost as much as {child.pronoun('possessive')} {keepsake.label}. "
        f"It had come from {keepsake.from_who}, and {child.pronoun()} liked to {keepsake.use_text} before bed."
    )
    world.say(
        f"{helper.label_word.capitalize()} used to smile and say that treasured things kept the warmest memories."
    )


def night_turn(world: World, child: Entity, keepsake_ent: Entity, curse: Curse) -> None:
    keepsake_ent.meters["cursed"] += 1
    keepsake_ent.attrs["form"] = curse.form_label
    keepsake_ent.attrs["clue"] = curse.clue
    keepsake_ent.attrs["original_label"] = keepsake_ent.label
    propagate(world, narrate=False)
    world.say(
        f"That night, while the house was still and the moonlight made pale squares on the floor, "
        f"an imp slipped in through the crack under the window."
    )
    world.say(
        f"By morning, {child.id}'s {keepsake_ent.label} was gone. In its place sat {curse.phrase}, and {curse.onset}"
    )


def discover(world: World, child: Entity, helper: Entity, curse: Curse) -> None:
    pred = predict_hideout(world, curse)
    world.facts["predicted_place"] = pred["place"]
    world.facts["predicted_clue"] = pred["clue"]
    world.say(
        f'{child.id} stared hard. "{curse.clue.capitalize()}," {child.pronoun()} whispered. '
        f'"That is not ordinary at all."'
    )
    world.say(
        f"{helper.label_word.capitalize()} knelt beside {child.pronoun('object')} and looked carefully too. "
        f'"An imp leaves a different sign in every hiding place," {helper.pronoun()} said. '
        f'"If we read the clue properly, we may find where it went."'
    )


def inspect_place(world: World, child: Entity, helper: Entity, place: Place, curse: Curse) -> None:
    child.memes["bravery"] += 1
    helper.memes["resolve"] += 1
    world.say(
        f"They followed the clue to {place.phrase}. There they found {place.clue_text}"
    )
    world.say(
        f"The mystery tightened instead of loosening, and even the quiet corners seemed to be listening."
    )
    world.facts["found_hideout"] = clue_matches_place(curse, place)


def find_imp(world: World, imp: Entity, place: Place) -> None:
    imp.meters["seen"] += 1
    world.say(
        f"Then two bright eyes blinked from the shadows, and the little imp showed its sharp grin from {place.phrase}."
    )


def challenge(world: World, child: Entity, helper: Entity, remedy: Remedy, curse: Curse) -> None:
    world.say(
        f'{child.id} held tight to {helper.label_word if helper.type in {"aunt", "uncle"} else helper.label_word}\'s sleeve, '
        f"but did not run. {helper.label_word.capitalize()} reached for {remedy.phrase}."
    )
    world.say(
        f'"A borrowed shape must go home," {helper.pronoun()} said, and {remedy.action}.'
    )
    world.facts["attempted_remedy"] = remedy.id
    world.facts["remedy_kind"] = remedy.kind
    world.facts["needed_kind"] = curse.remedy_kind


def restore(world: World, child: Entity, helper: Entity, keepsake_ent: Entity, keepsake: Keepsake) -> None:
    keepsake_ent.meters["cursed"] = 0.0
    keepsake_ent.attrs["form"] = keepsake.label
    child.memes["worry"] = 0.0
    child.memes["joy"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"The strange shape shivered, folded in on itself, and opened again as {keepsake.phrase}. "
        f"The imp yelped once and darted out the window, empty-handed."
    )
    world.say(
        f"{child.id} gathered the {keepsake.label} close. The room did not feel spooky anymore, only very still and very safe."
    )


def fail_reversal(world: World, child: Entity, helper: Entity, keepsake_ent: Entity, curse: Curse, remedy: Remedy) -> None:
    keepsake_ent.meters["sealed"] += 1
    keepsake_ent.meters["cursed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But dawn was already thinning the shadows. {remedy.fail_action}, and the spell clamped shut like a tiny lock."
    )
    world.say(
        f"The imp gave a pleased little bow. {curse.phrase.capitalize()} stayed exactly as it was."
    )
    world.say(
        f"{child.id} understood then that they had solved the mystery too late."
    )


def bad_ending(world: World, child: Entity, helper: Entity, keepsake: Keepsake, curse: Curse) -> None:
    world.say(
        f"{helper.label_word.capitalize()} put an arm around {child.id}, but neither of them could change the morning. "
        f"{child.id}'s {keepsake.label} was lost inside {curse.form_label} now."
    )
    world.say(
        f"After that, {child.id} still looked at every odd shadow and every crooked sparkle, wondering whether the imp might return. "
        f"It was a mystery remembered, not a mystery neatly solved."
    )


def tell(
    keepsake: Keepsake,
    curse: Curse,
    place: Place,
    remedy: Remedy,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_type: str = "aunt",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper"))
    imp = world.add(Entity(id="Imp", kind="character", type="imp", role="imp", label="the imp"))
    keepsake_ent = world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake.label,
            phrase=keepsake.phrase,
            owner=child.id,
            attrs={"form": keepsake.label, "clue": "", "original_label": keepsake.label},
            tags=set(keepsake.tags),
        )
    )

    world.facts["mystery_started"] = False
    world.facts["predicted_place"] = ""
    world.facts["predicted_clue"] = ""
    world.facts["found_hideout"] = False
    world.facts["attempted_remedy"] = ""
    world.facts["remedy_kind"] = remedy.kind
    world.facts["needed_kind"] = curse.remedy_kind
    world.facts["delay"] = delay

    introduce(world, child, helper, keepsake)
    world.para()
    night_turn(world, child, keepsake_ent, curse)
    discover(world, child, helper, curse)

    world.para()
    inspect_place(world, child, helper, place, curse)
    find_imp(world, imp, place)
    challenge(world, child, helper, remedy, curse)

    world.para()
    if is_reversed(curse, remedy, delay):
        restore(world, child, helper, keepsake_ent, keepsake)
        outcome = "restored"
    else:
        fail_reversal(world, child, helper, keepsake_ent, curse, remedy)
        bad_ending(world, child, helper, keepsake, curse)
        outcome = "sealed"

    world.facts.update(
        child=child,
        helper=helper,
        imp=imp,
        keepsake_cfg=keepsake,
        curse=curse,
        place=place,
        remedy=remedy,
        keepsake=keepsake_ent,
        outcome=outcome,
        severity=curse_severity(curse, delay),
    )
    return world


KNOWLEDGE = {
    "imp": [
        (
            "What is an imp in a story?",
            "An imp is a tiny troublesome creature from make-believe stories. It likes tricks, mischief, and sneaky little pranks."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with hidden clues that you have to figure out. You look carefully, notice signs, and try to explain what happened."
        )
    ],
    "moonwater": [
        (
            "What is moonwater in a fantasy story?",
            "Moonwater is pretend water said to shine with moonlight. In stories, it is often used to wash away enchantments."
        )
    ],
    "rhyme": [
        (
            "Why do magic stories use rhymes?",
            "Rhymes are easy to remember and sound a little musical. In stories, that makes them feel like words with special power."
        )
    ],
    "bell": [
        (
            "Why might a bell break a spell in a story?",
            "A clear bell sound cuts through quiet and makes hidden things jump. In fantasy stories, that sharp sound can shake a spell apart."
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or space under the roof of a house. People often keep trunks, boxes, and old things there."
        )
    ],
    "pantry": [
        (
            "What is a pantry?",
            "A pantry is a small room or cupboard where food is kept. You might find flour, jars, and other kitchen things there."
        )
    ],
    "hearth": [
        (
            "What is a hearth?",
            "A hearth is the floor of a fireplace and the warm area around it. Ash and soot often gather there."
        )
    ],
    "garden": [
        (
            "Why does moss grow in shady garden places?",
            "Moss likes damp, shady spots where water stays. That is why you often see it on stones or wooden corners."
        )
    ],
}
KNOWLEDGE_ORDER = ["imp", "mystery", "moonwater", "rhyme", "bell", "attic", "pantry", "hearth", "garden"]


KEEPSAKES = {
    "music_box": Keepsake(
        id="music_box",
        label="music box",
        phrase="a small silver music box",
        from_who="Grandma",
        use_text="wind it and listen for the soft tune",
        material="silver",
        tags={"mystery"},
    ),
    "teacup": Keepsake(
        id="teacup",
        label="teacup",
        phrase="a painted blue teacup",
        from_who="Grandpa",
        use_text="set it carefully on the shelf and admire the blue flowers",
        material="china",
        tags={"mystery"},
    ),
    "brass_key": Keepsake(
        id="brass_key",
        label="brass key",
        phrase="an old brass key on a ribbon",
        from_who="her grandfather" if False else "Grandpa",
        use_text="hold it up to the light and imagine which lock it once opened",
        material="brass",
        tags={"mystery"},
    ),
}

CURSES = {
    "moth": Curse(
        id="moth",
        form_label="a paper-pale moth",
        phrase="a paper-pale moth where it should have been",
        onset="a dusting of silver powder lay on the sill.",
        clue="silver dust",
        hide_tag="dust",
        remedy_kind="rhyme",
        hardness=1,
        tags={"imp", "mystery", "attic", "rhyme"},
    ),
    "toadstool": Curse(
        id="toadstool",
        form_label="a red-capped toadstool",
        phrase="a red-capped toadstool in its place",
        onset="a wet green thread of moss curled across the shelf.",
        clue="green moss",
        hide_tag="moss",
        remedy_kind="moonwater",
        hardness=2,
        tags={"imp", "mystery", "garden", "moonwater"},
    ),
    "coal": Curse(
        id="coal",
        form_label="a lump of whispering coal",
        phrase="a lump of whispering coal where it belonged",
        onset="a little black crescent of soot marked the floorboards.",
        clue="black soot",
        hide_tag="soot",
        remedy_kind="bell",
        hardness=2,
        tags={"imp", "mystery", "hearth", "bell"},
    ),
    "salt": Curse(
        id="salt",
        form_label="a neat white heap of salt",
        phrase="a neat white heap of salt on the table",
        onset="sugary crumbs glittered all around it.",
        clue="sugary crumbs",
        hide_tag="sugar",
        remedy_kind="moonwater",
        hardness=3,
        tags={"imp", "mystery", "pantry", "moonwater"},
    ),
}

PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the attic",
        clue_text="fine dust on the floor and one tiny footprint on an old trunk.",
        tags={"dust", "attic"},
    ),
    "garden_gate": Place(
        id="garden_gate",
        label="garden gate",
        phrase="the shaded garden gate",
        clue_text="a damp patch of moss and a bent leaf, as if something small had scrambled through.",
        tags={"moss", "garden"},
    ),
    "hearth": Place(
        id="hearth",
        label="hearth",
        phrase="the hearth",
        clue_text="fresh soot by the fender and a crooked scratch no broom had made.",
        tags={"soot", "hearth"},
    ),
    "pantry": Place(
        id="pantry",
        label="pantry",
        phrase="the pantry",
        clue_text="a line of sugar grains leading behind the flour tin.",
        tags={"sugar", "pantry"},
    ),
}

REMEDIES = {
    "rhyme_book": Remedy(
        id="rhyme_book",
        label="rhyme book",
        phrase="the little rhyme book from the hall drawer",
        kind="rhyme",
        power=1,
        sense=3,
        action="read the old turning-back rhyme in a steady voice",
        fail_action="the rhyme fluttered through the air and faded",
        qa_text="read the turning-back rhyme aloud",
        tags={"rhyme"},
    ),
    "moonwater": Remedy(
        id="moonwater",
        label="moonwater",
        phrase="a blue bottle of moonwater",
        kind="moonwater",
        power=2,
        sense=3,
        action="sprinkled three shining drops over the false shape",
        fail_action="the moonwater flashed once and slid away",
        qa_text="sprinkled moonwater over the transformed shape",
        tags={"moonwater"},
    ),
    "copper_bell": Remedy(
        id="copper_bell",
        label="copper bell",
        phrase="the small copper bell from the mantel",
        kind="bell",
        power=2,
        sense=2,
        action="rang it once, clear and bright, so the sound skipped through the room",
        fail_action="the bell rang, but the note came back dull and tired",
        qa_text="rang the copper bell over the spell",
        tags={"bell"},
    ),
    "broom": Remedy(
        id="broom",
        label="broom",
        phrase="the kitchen broom",
        kind="sweep",
        power=1,
        sense=1,
        action="swept at the shape crossly",
        fail_action="the broom only stirred the air",
        qa_text="tried to sweep the spell away",
        tags=set(),
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ada", "Ruby", "Elsie", "Poppy", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Eli", "Owen", "Sam", "Noah"]


@dataclass
class StoryParams:
    keepsake: str
    curse: str
    place: str
    remedy: str
    child_name: str
    child_gender: str
    helper_type: str
    delay: int = 0
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
    keepsake = f["keepsake_cfg"]
    curse = f["curse"]
    outcome = f["outcome"]
    if outcome == "sealed":
        return [
            f'Write a child-friendly mystery story that includes the word "imp" and begins when a treasured {keepsake.label} is transformed.',
            f"Tell a spooky-but-gentle mystery where {child.id} follows {curse.clue} to solve an imp's trick, but reaches the answer too late.",
            f'Write a transformation mystery with a bad ending: an imp changes a keepsake, clues point to the hiding place, and dawn seals the spell before it can be undone.',
        ]
    return [
        f'Write a child-friendly mystery story that includes the word "imp" and begins when a treasured {keepsake.label} is transformed.',
        f"Tell a gentle mystery where {child.id} follows {curse.clue} to find an imp and reverse the spell before dawn.",
        f'Write a transformation mystery for a young child in which careful clue-reading leads to the right hiding place and the spell is broken in time.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    keepsake = f["keepsake_cfg"]
    curse = f["curse"]
    place = f["place"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was what happened to {child.id}'s {keepsake.label}. It had been changed into {curse.form_label}, so {child.id} had to figure out what the imp had done and where it had gone."
        ),
        (
            f"What clue helped {child.id} solve the mystery?",
            f"The clue was {curse.clue}. That clue matched {place.label}, so it told them where the imp was likely hiding."
        ),
        (
            f"Why did {child.id} and {helper.label_word} go to {place.phrase}?",
            f"They went there because the strange sign near the transformed keepsake pointed that way. In this story, {curse.clue} is the kind of clue an imp leaves around {place.label}."
        ),
    ]
    if outcome == "restored":
        qa.append(
            (
                f"How did they change the keepsake back?",
                f"{helper.label_word.capitalize()} {remedy.qa_text}. That was the right kind of remedy for this curse, and they used it before the spell grew too hard."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the keepsake safely restored and the imp fleeing away. The room felt ordinary again, which showed the mystery had truly been solved."
            )
        )
    else:
        qa.append(
            (
                f"Why did the ending turn out badly?",
                f"They found the truth, but dawn came too soon and the spell sealed shut. The remedy was not strong enough for a curse that had already hardened, so the keepsake stayed transformed."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly because {child.id}'s {keepsake.label} was still trapped as {curse.form_label}. The imp escaped, so the mystery was understood but not happily fixed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"imp", "mystery"} | set(f["curse"].tags) | set(f["place"].tags) | set(f["remedy"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: {{k: v for k, v in world.facts.items() if k not in {'child', 'helper', 'imp', 'keepsake', 'keepsake_cfg', 'curse', 'place', 'remedy'}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        keepsake="music_box",
        curse="moth",
        place="attic",
        remedy="rhyme_book",
        child_name="Nora",
        child_gender="girl",
        helper_type="aunt",
        delay=0,
    ),
    StoryParams(
        keepsake="teacup",
        curse="coal",
        place="hearth",
        remedy="copper_bell",
        child_name="Theo",
        child_gender="boy",
        helper_type="uncle",
        delay=0,
    ),
    StoryParams(
        keepsake="brass_key",
        curse="toadstool",
        place="garden_gate",
        remedy="moonwater",
        child_name="Mina",
        child_gender="girl",
        helper_type="mother",
        delay=1,
    ),
    StoryParams(
        keepsake="music_box",
        curse="salt",
        place="pantry",
        remedy="moonwater",
        child_name="Eli",
        child_gender="boy",
        helper_type="father",
        delay=1,
    ),
    StoryParams(
        keepsake="teacup",
        curse="salt",
        place="pantry",
        remedy="moonwater",
        child_name="Ruby",
        child_gender="girl",
        helper_type="aunt",
        delay=2,
    ),
]


def explain_rejection(curse: Curse, place: Place, remedy: Remedy) -> str:
    if not clue_matches_place(curse, place):
        return (
            f"(No story: the clue for {curse.form_label} is {curse.clue}, which does not point to {place.label}. "
            f"A mystery should let the clue honestly lead to the hiding place.)"
        )
    if not can_reverse(curse, remedy):
        return (
            f"(No story: {remedy.label} cannot undo the spell on {curse.form_label}. "
            f"This curse needs a {curse.remedy_kind} remedy.)"
        )
    if remedy.sense < SENSE_MIN:
        return (
            f"(No story: {remedy.label} is too weak or silly for this world. "
            f"Pick a more sensible remedy.)"
        )
    return "(No story: this combination does not make sense.)"


def outcome_of(params: StoryParams) -> str:
    curse = CURSES[params.curse]
    remedy = REMEDIES[params.remedy]
    return "restored" if is_reversed(curse, remedy, params.delay) else "sealed"


ASP_RULES = r"""
clue_match(C, P) :- curse(C), place(P), hide_tag(C, T), place_tag(P, T).
right_remedy(C, R) :- curse(C), remedy(R), remedy_kind(C, K), kind(R, K).
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.

valid(C, P, R) :- clue_match(C, P), right_remedy(C, R), sensible(R).

severity(H + D) :- chosen_curse(C), hardness(C, H), delay(D).
reversed :- chosen_curse(C), chosen_remedy(R), right_remedy(C, R), power(R, P), severity(V), P >= V.

outcome(restored) :- reversed.
outcome(sealed) :- not reversed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for kid in KEEPSAKES:
        lines.append(asp.fact("keepsake", kid))
    for cid, curse in CURSES.items():
        lines.append(asp.fact("curse", cid))
        lines.append(asp.fact("hide_tag", cid, curse.hide_tag))
        lines.append(asp.fact("remedy_kind", cid, curse.remedy_kind))
        lines.append(asp.fact("hardness", cid, curse.hardness))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", pid, tag))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("kind", rid, remedy.kind))
        lines.append(asp.fact("power", rid, remedy.power))
        lines.append(asp.fact("sense", rid, remedy.sense))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_curse", params.curse),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, an imp, a transformed keepsake, and a mystery before dawn."
    )
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--curse", choices=CURSES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how close to dawn they are when they try the remedy")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid (curse, place, remedy) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run generation smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.curse and args.place and args.remedy:
        curse = CURSES[args.curse]
        place = PLACES[args.place]
        remedy = REMEDIES[args.remedy]
        if not (clue_matches_place(curse, place) and can_reverse(curse, remedy) and remedy.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(curse, place, remedy))
    elif args.curse and args.place:
        curse = CURSES[args.curse]
        place = PLACES[args.place]
        remedy = sensible_remedies()[0]
        if not clue_matches_place(curse, place):
            raise StoryError(explain_rejection(curse, place, remedy))
    elif args.curse and args.remedy:
        curse = CURSES[args.curse]
        remedy = REMEDIES[args.remedy]
        place = next(iter(PLACES.values()))
        if not (can_reverse(curse, remedy) and remedy.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(curse, place, remedy))

    combos = [
        c for c in valid_combos()
        if (args.curse is None or c[0] == args.curse)
        and (args.place is None or c[1] == args.place)
        and (args.remedy is None or c[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    curse_id, place_id, remedy_id = rng.choice(sorted(combos))
    keepsake_id = args.keepsake or rng.choice(sorted(KEEPSAKES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        keepsake=keepsake_id,
        curse=curse_id,
        place=place_id,
        remedy=remedy_id,
        child_name=name,
        child_gender=gender,
        helper_type=helper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.curse not in CURSES:
        raise StoryError(f"(Unknown curse: {params.curse})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.helper_type not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")

    curse = CURSES[params.curse]
    place = PLACES[params.place]
    remedy = REMEDIES[params.remedy]
    if not (clue_matches_place(curse, place) and can_reverse(curse, remedy) and remedy.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(curse, place, remedy))

    world = tell(
        KEEPSAKES[params.keepsake],
        curse,
        place,
        remedy,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        delay=params.delay,
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_remedies()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible remedies match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (curse, place, remedy) combos:\n")
        for curse, place, remedy in combos:
            print(f"  {curse:10} {place:12} {remedy}")
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
                f"### {p.child_name}: {p.curse} via {p.place} with {p.remedy} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
