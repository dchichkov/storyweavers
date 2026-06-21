#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/haggard_rave_repetition_rhyming_story.py
===================================================================

A standalone storyworld about a child who wants to start a moonlit little rave,
but first notices an old scarecrow looking haggard and mends the right part the
right way. The prose leans into a gentle rhyming-story voice and uses repetition
as a deliberate refrain.

Run it
------
    python storyworlds/worlds/gpt-5.4/haggard_rave_repetition_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/haggard_rave_repetition_rhyming_story.py --place pumpkin_patch --damage floppy_hat --fix ribbon
    python storyworlds/worlds/gpt-5.4/haggard_rave_repetition_rhyming_story.py --damage sleeve_rip --fix ribbon
    python storyworlds/worlds/gpt-5.4/haggard_rave_repetition_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/haggard_rave_repetition_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/haggard_rave_repetition_rhyming_story.py --verify
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
    phrase: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    image: str
    glow_tags: set[str] = field(default_factory=set)
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
class Damage:
    id: str
    label: str
    phrase: str
    needed_fix: str
    body_part: str
    gust_line: str
    mend_line: str
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
class Fix:
    id: str
    label: str
    phrase: str
    repairs: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
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
class Glow:
    id: str
    label: str
    phrase: str
    shimmer: str
    place_tags: set[str] = field(default_factory=set)
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
class Chant:
    id: str
    call: str
    reply: str
    motion: str
    closing: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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


def _r_haggard(world: World) -> list[str]:
    scarecrow = world.get("scarecrow")
    if scarecrow.meters["damage"] < THRESHOLD:
        return []
    sig = ("haggard", world.facts.get("damage_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    scarecrow.meters["slump"] += 1
    scarecrow.memes["lonely"] += 1
    scarecrow.memes["embarrassed"] += 1
    return ["__haggard__"]


def _r_restored(world: World) -> list[str]:
    scarecrow = world.get("scarecrow")
    glow = world.get("glow")
    if scarecrow.meters["mended"] < THRESHOLD or glow.meters["lit"] < THRESHOLD:
        return []
    sig = ("restored", world.facts.get("damage_id", ""), world.facts.get("glow_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    scarecrow.meters["slump"] = 0.0
    scarecrow.meters["upright"] += 1
    scarecrow.memes["lonely"] = 0.0
    scarecrow.memes["joy"] += 1
    scarecrow.memes["pride"] += 1
    return ["__restored__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="haggard", tag="emotional", apply=_r_haggard),
    Rule(name="restored", tag="emotional", apply=_r_restored),
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
        for line in produced:
            world.say(line)
    return produced


def fix_matches(damage: Damage, fix: Fix) -> bool:
    return damage.needed_fix in fix.repairs


def glow_fits(place: Place, glow: Glow) -> bool:
    return bool(place.glow_tags & glow.place_tags)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for damage_id, damage in DAMAGES.items():
            for fix_id, fix in FIXES.items():
                if not fix_matches(damage, fix):
                    continue
                for glow_id, glow in GLOWS.items():
                    if not glow_fits(place, glow):
                        continue
                    for chant_id in CHANTS:
                        combos.append((place_id, damage_id, fix_id, glow_id, chant_id))
    return combos


def explain_rejection(damage: Damage, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not honestly mend {damage.phrase}. "
        f"This world only tells versions where the chosen fix fits the damage.)"
    )


def explain_glow(place: Place, glow: Glow) -> str:
    return (
        f"(No story: {glow.label} does not suit {place.label}. "
        f"Pick a glow that belongs in that place.)"
    )


def predict_mood(world: World, fix: Fix, glow: Glow) -> dict:
    sim = world.copy()
    sim.facts["fix_id"] = fix.id
    sim.facts["glow_id"] = glow.id
    _do_mend(sim, fix, narrate=False)
    _do_light(sim, glow, narrate=False)
    return {
        "upright": sim.get("scarecrow").meters["upright"] >= THRESHOLD,
        "joy": sim.get("scarecrow").memes["joy"] >= THRESHOLD,
        "lonely": sim.get("scarecrow").memes["lonely"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"In {place.phrase}, {child.id} skipped where the moon made silver loops. "
        f"{place.image}"
    )
    world.say(
        f"{child.id} loved little night dances, tiny and bright, and whispered, "
        f'"Tonight is the night for a twinkle-light rave."'
    )


def spot_scary_sad(world: World, child: Entity, scarecrow: Entity, damage: Damage) -> None:
    propagate(world, narrate=False)
    world.say(
        f"But by the path stood {scarecrow.phrase}. {damage.phrase.capitalize()} made "
        f"{scarecrow.pronoun('object')} look haggard, not grand, and not brave."
    )
    world.say(
        f'{child.id} slowed down. "Oh dear," {child.pronoun()} said softly. '
        f'"A rave should not start while a friend looks this gray."'
    )


def wind_nudges(world: World, damage: Damage) -> None:
    scarecrow = world.get("scarecrow")
    scarecrow.meters["wobble"] += 1
    world.say(damage.gust_line)


def promise_help(world: World, child: Entity, scarecrow: Entity) -> None:
    scarecrow.memes["hope"] += 1
    child.memes["care"] += 1
    world.say(
        f'"Not yet, not yet, not yet," sang {child.id}. "First we mend, then we sway."'
    )
    world.say(
        f'That little refrain floated out three times, and {scarecrow.label} listened all the way.'
    )


def _do_mend(world: World, fix: Fix, narrate: bool = True) -> None:
    scarecrow = world.get("scarecrow")
    scarecrow.meters["mended"] += 1
    scarecrow.meters["damage"] = 0.0
    if narrate:
        world.say(
            f"{fix.action.capitalize()}, {fix.phrase} did exactly what it should do."
        )


def mend(world: World, child: Entity, damage: Damage, fix: Fix) -> None:
    _do_mend(world, fix, narrate=False)
    world.say(
        f"{child.id} fetched {fix.phrase} and {fix.action}. {damage.mend_line}"
    )
    world.say(
        f'"Mend it neat, mend it sweet; mend it neat, mend it sweet," '
        f'{child.id} chimed.'
    )


def _do_light(world: World, glow: Glow, narrate: bool = True) -> None:
    lamp = world.get("glow")
    lamp.meters["lit"] += 1
    if narrate:
        world.say(glow.shimmer)


def light_the_patch(world: World, child: Entity, glow: Glow) -> None:
    _do_light(world, glow, narrate=False)
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} set out {glow.phrase}, and {glow.shimmer}"
    )


def dance(world: World, child: Entity, scarecrow: Entity, chant: Chant) -> None:
    child.memes["joy"] += 1
    scarecrow = world.get("scarecrow")
    scarecrow.memes["joy"] += 1
    world.say(
        f'Soon {child.id} called, "{chant.call}" and answered, "{chant.reply}"'
    )
    world.say(
        f"Round they went with {chant.motion}, and again they went, and again they went, "
        f"because the best little songs love to repeat what they mean."
    )
    world.say(
        f"{chant.closing} The old scarecrow no longer looked haggard at all."
    )


def closing_image(world: World, place: Place, scarecrow: Entity) -> None:
    world.say(
        f"By the end, {place.label} glowed softly, and {scarecrow.label} stood tall in the light. "
        f"What began as a lonely corner had become a merry moon-bright sight."
    )


def tell(
    place: Place,
    damage: Damage,
    fix: Fix,
    glow: Glow,
    chant: Chant,
    child_name: str = "Pip",
    child_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=["kind", "lively"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    scarecrow = world.add(Entity(
        id="scarecrow",
        kind="thing",
        type="scarecrow",
        label="the scarecrow",
        phrase="an old scarecrow with button eyes",
        role="friend",
    ))
    lamp = world.add(Entity(
        id="glow",
        kind="thing",
        type="light",
        label=glow.label,
        phrase=glow.phrase,
        role="glow",
    ))

    world.facts.update(
        child=child,
        parent=parent,
        scarecrow=scarecrow,
        place=place,
        damage=damage,
        damage_id=damage.id,
        fix=fix,
        fix_id=fix.id,
        glow=glow,
        glow_id=glow.id,
        chant=chant,
    )

    scarecrow.meters["damage"] = 1.0
    scarecrow.meters["mended"] = 0.0
    scarecrow.meters["slump"] = 0.0
    scarecrow.meters["upright"] = 0.0
    scarecrow.meters["wobble"] = 0.0
    scarecrow.memes["lonely"] = 0.0
    scarecrow.memes["embarrassed"] = 0.0
    scarecrow.memes["hope"] = 0.0
    scarecrow.memes["joy"] = 0.0
    scarecrow.memes["pride"] = 0.0
    child.memes["care"] = 0.0
    child.memes["joy"] = 0.0
    lamp.meters["lit"] = 0.0

    introduce(world, child, place)
    spot_scary_sad(world, child, scarecrow, damage)

    world.para()
    wind_nudges(world, damage)
    promise_help(world, child, scarecrow)

    world.para()
    mend(world, child, damage, fix)
    light_the_patch(world, child, glow)

    world.para()
    dance(world, child, scarecrow, chant)
    closing_image(world, place, scarecrow)

    world.facts.update(
        restored=scarecrow.meters["upright"] >= THRESHOLD,
        lit=lamp.meters["lit"] >= THRESHOLD,
        lonely_before=("haggard", damage.id) in world.fired,
    )
    return world


PLACES = {
    "pumpkin_patch": Place(
        id="pumpkin_patch",
        label="the pumpkin patch",
        phrase="the pumpkin patch",
        image="Round pumpkins sat like sleepy drums beside the rows.",
        glow_tags={"lantern", "firefly"},
        tags={"pumpkin_patch", "garden"},
    ),
    "apple_orchard": Place(
        id="apple_orchard",
        label="the apple orchard",
        phrase="the apple orchard",
        image="The apples bobbed overhead like red moons in the leaves.",
        glow_tags={"lantern", "firefly", "paper_star"},
        tags={"orchard", "apple"},
    ),
    "sunflower_garden": Place(
        id="sunflower_garden",
        label="the sunflower garden",
        phrase="the sunflower garden",
        image="Tall flowers nodded as if they already knew a chorus.",
        glow_tags={"firefly", "paper_star"},
        tags={"sunflower", "garden"},
    ),
}

DAMAGES = {
    "floppy_hat": Damage(
        id="floppy_hat",
        label="floppy hat",
        phrase="his big patchwork hat had slipped over one eye",
        needed_fix="ribbon",
        body_part="hat",
        gust_line="A soft puff of wind tipped the hat lower still, and the poor scarecrow sagged with a sigh.",
        mend_line="Up popped the brim, straight and trim, and the button eyes shone again.",
        tags={"hat", "scarecrow"},
    ),
    "sleeve_rip": Damage(
        id="sleeve_rip",
        label="ripped sleeve",
        phrase="one sleeve was torn and straw was peeking out",
        needed_fix="patch",
        body_part="sleeve",
        gust_line="A soft puff of wind teased more straw through the tear, and the poor scarecrow looked smaller somehow.",
        mend_line="The tear sat flat at once, and no more straw poked into the night air.",
        tags={"patch", "straw"},
    ),
    "loose_straw": Damage(
        id="loose_straw",
        label="loose straw waist",
        phrase="the twine at his middle had come loose, so his straw puffed out in a tired heap",
        needed_fix="twine",
        body_part="middle",
        gust_line="A soft puff of wind made the loose straw rustle and tumble, and the poor scarecrow leaned sideways.",
        mend_line="The straw tucked in snugly, and the middle held firm again.",
        tags={"twine", "straw"},
    ),
}

FIXES = {
    "ribbon": Fix(
        id="ribbon",
        label="ribbon",
        phrase="a moon-blue ribbon",
        repairs={"ribbon"},
        action="looped it neatly round the hat and tied a bow that would not slide",
        qa_text="tied a blue ribbon around the hat so it stayed up",
        tags={"ribbon"},
    ),
    "patch": Fix(
        id="patch",
        label="cloth patch",
        phrase="a small red cloth patch",
        repairs={"patch"},
        action="pressed the patch over the tear and fastened it snug and square",
        qa_text="covered the torn sleeve with a cloth patch",
        tags={"patch"},
    ),
    "twine": Fix(
        id="twine",
        label="twine",
        phrase="a warm brown piece of twine",
        repairs={"twine"},
        action="wrapped the twine around the middle and pulled the bundle tight",
        qa_text="wrapped twine around the middle to hold the straw in",
        tags={"twine"},
    ),
}

GLOWS = {
    "lantern": Glow(
        id="lantern",
        label="lantern",
        phrase="a small pumpkin lantern",
        shimmer="the lantern cast a cozy ring of gold over the ground.",
        place_tags={"lantern"},
        tags={"lantern", "light"},
    ),
    "firefly": Glow(
        id="firefly",
        label="fireflies",
        phrase="a jam jar of blinking fireflies",
        shimmer="tiny green sparks bobbed and blinked like polite little stars.",
        place_tags={"firefly"},
        tags={"firefly", "light"},
    ),
    "paper_star": Glow(
        id="paper_star",
        label="paper star lamp",
        phrase="a paper star lamp on a string",
        shimmer="the star lamp glowed pale and pearly, as if a piece of moon had come down to help.",
        place_tags={"paper_star"},
        tags={"lamp", "light"},
    ),
}

CHANTS = {
    "twirl": Chant(
        id="twirl",
        call="Twirl once, twirl twice",
        reply="twirl once, twirl twice!",
        motion="small moonlit turns",
        closing="Soon even the pumpkins seemed to grin in a ring",
        tags={"dance", "repetition"},
    ),
    "clap": Chant(
        id="clap",
        call="Clap and tap, clap and tap",
        reply="clap and tap in line!",
        motion="claps, taps, and light little hops",
        closing="Soon even the apples seemed to keep the time",
        tags={"dance", "repetition"},
    ),
    "sway": Chant(
        id="sway",
        call="Sway this way, sway that way",
        reply="sway this way, sway that way!",
        motion="side-to-side sways soft as hay",
        closing="Soon even the flowers seemed to nod to the rhyme",
        tags={"dance", "repetition"},
    ),
}


@dataclass
class StoryParams:
    place: str
    damage: str
    fix: str
    glow: str
    chant: str
    child_name: str
    child_type: str
    parent: str
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


GIRL_NAMES = ["Pip", "June", "Mia", "Tess", "Nora", "Lila", "Ava", "Molly"]
BOY_NAMES = ["Pip", "Finn", "Leo", "Max", "Eli", "Noah", "Theo", "Ben"]

KNOWLEDGE = {
    "haggard": [
        (
            "What does haggard mean?",
            "Haggard means someone or something looks very tired, worn out, or droopy. It is a word for looking as if the day has been a little too long.",
        )
    ],
    "rave": [
        (
            "What is a rave in this story?",
            "Here, a rave is a lively little dance party with music, movement, and lights. In a child-sized story, it just means a bright, happy time for dancing together.",
        )
    ],
    "scarecrow": [
        (
            "What does a scarecrow do?",
            "A scarecrow stands in a garden or field to help keep birds away from the plants. It is usually made from old clothes, straw, and sticks.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon good for?",
            "A ribbon can tie something gently in place, like a hat or a bow. It is soft, but it can still help when the job is a small one.",
        )
    ],
    "patch": [
        (
            "What does a cloth patch do?",
            "A cloth patch covers a tear in fabric so the hole is not open anymore. It helps keep the cloth neat and together.",
        )
    ],
    "twine": [
        (
            "What is twine?",
            "Twine is a thin, strong string that can wrap around things and hold them together. Gardeners often use it when something needs tying.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light with a cover around it, so it can glow softly. It helps people see when the sky is dark.",
        )
    ],
    "firefly": [
        (
            "What is a firefly?",
            "A firefly is a small bug that can glow in the dark. Its tiny light helps make summer nights look sparkly.",
        )
    ],
    "lamp": [
        (
            "What is a paper star lamp?",
            "A paper star lamp is a light inside a star-shaped cover. It shines gently and can make a place feel festive.",
        )
    ],
    "repetition": [
        (
            "What is repetition in a story?",
            "Repetition is when a story says the same words or a very similar line again on purpose. It makes the rhythm stronger and helps the important idea stick in your mind.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "haggard",
    "rave",
    "scarecrow",
    "ribbon",
    "patch",
    "twine",
    "lantern",
    "firefly",
    "lamp",
    "repetition",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    damage = f["damage"]
    place = f["place"]
    glow = f["glow"]
    chant = f["chant"]
    return [
        (
            'Write a short rhyming story for a 3-to-5-year-old that includes the words '
            '"haggard" and "rave", and uses repetition as a refrain.'
        ),
        (
            f"Tell a gentle moonlit story where {child.id} finds a scarecrow in "
            f"{place.label} looking haggard because of {damage.label}, mends the problem, "
            f"and then starts a tiny rave under {glow.label}."
        ),
        (
            f'Write a child-facing story with repeated lines like "{chant.call}" so the rhythm '
            f"returns again and again before the happy ending."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    scarecrow = f["scarecrow"]
    damage = f["damage"]
    fix = f["fix"]
    glow = f["glow"]
    chant = f["chant"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and a lonely scarecrow in {place.label}. The story follows how {child.id} notices the problem before the dance begins.",
        ),
        (
            "Why did the scarecrow look haggard?",
            f"The scarecrow looked haggard because {damage.phrase}. That damage made him seem droopy and left out instead of ready for the little rave.",
        ),
        (
            f"What did {child.id} do before starting the rave?",
            f"{child.id} stopped to mend the scarecrow with {fix.phrase}. The child chose helping first, because a party felt wrong while a friend was still sagging sadly.",
        ),
        (
            "How did the story use repetition?",
            f"The story repeated little singing lines like '{chant.call}' and 'Not yet, not yet, not yet.' Saying the words again made the rhythm feel bouncy and helped show what mattered.",
        ),
    ]
    if f.get("restored"):
        qa.append(
            (
                f"How did {child.id} fix the problem?",
                f"{child.id} {fix.qa_text}. After that, the scarecrow could stand tall again instead of wobbling in the wind.",
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"At the end, the lights were glowing and the scarecrow joined the little rave instead of standing alone. The ending image proves the place changed from a sad corner into a bright dancing one.",
            )
        )
    if f.get("lit"):
        qa.append(
            (
                f"Why did the {glow.label} matter?",
                f"The {glow.label} made the patch feel warm and welcoming. Once the light came on, the repaired scarecrow looked ready to celebrate, not hide.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"haggard", "rave", "scarecrow", "repetition"}
    tags |= set(f["fix"].tags)
    tags |= set(f["glow"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_fix(D, F) :- damage(D), fix(F), needed_fix(D, K), repairs(F, K).
fits_glow(P, G) :- place(P), glow(G), place_tag(P, T), glow_tag(G, T).
valid(P, D, F, G, C) :- place(P), damage(D), fix(F), glow(G), chant(C),
                        fits_fix(D, F), fits_glow(P, G).
#show valid/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for tag in sorted(place.glow_tags):
            lines.append(asp.fact("place_tag", place_id, tag))
    for damage_id, damage in DAMAGES.items():
        lines.append(asp.fact("damage", damage_id))
        lines.append(asp.fact("needed_fix", damage_id, damage.needed_fix))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for rep in sorted(fix.repairs):
            lines.append(asp.fact("repairs", fix_id, rep))
    for glow_id, glow in GLOWS.items():
        lines.append(asp.fact("glow", glow_id))
        for tag in sorted(glow.place_tags):
            lines.append(asp.fact("glow_tag", glow_id, tag))
    for chant_id in CHANTS:
        lines.append(asp.fact("chant", chant_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: mend the haggard scarecrow, then begin the moonlit rave."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--glow", choices=GLOWS)
    ap.add_argument("--chant", choices=CHANTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.damage and args.fix:
        if not fix_matches(DAMAGES[args.damage], FIXES[args.fix]):
            raise StoryError(explain_rejection(DAMAGES[args.damage], FIXES[args.fix]))
    if args.place and args.glow:
        if not glow_fits(PLACES[args.place], GLOWS[args.glow]):
            raise StoryError(explain_glow(PLACES[args.place], GLOWS[args.glow]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.damage is None or combo[1] == args.damage)
        and (args.fix is None or combo[2] == args.fix)
        and (args.glow is None or combo[3] == args.glow)
        and (args.chant is None or combo[4] == args.chant)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, damage_id, fix_id, glow_id, chant_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        damage=damage_id,
        fix=fix_id,
        glow=glow_id,
        chant=chant_id,
        child_name=child_name,
        child_type=child_type,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.damage not in DAMAGES:
        raise StoryError(f"(Unknown damage: {params.damage})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.glow not in GLOWS:
        raise StoryError(f"(Unknown glow: {params.glow})")
    if params.chant not in CHANTS:
        raise StoryError(f"(Unknown chant: {params.chant})")

    place = PLACES[params.place]
    damage = DAMAGES[params.damage]
    fix = FIXES[params.fix]
    glow = GLOWS[params.glow]
    chant = CHANTS[params.chant]

    if not fix_matches(damage, fix):
        raise StoryError(explain_rejection(damage, fix))
    if not glow_fits(place, glow):
        raise StoryError(explain_glow(place, glow))

    world = tell(
        place=place,
        damage=damage,
        fix=fix,
        glow=glow,
        chant=chant,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent,
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


CURATED = [
    StoryParams(
        place="pumpkin_patch",
        damage="floppy_hat",
        fix="ribbon",
        glow="lantern",
        chant="twirl",
        child_name="Pip",
        child_type="girl",
        parent="mother",
    ),
    StoryParams(
        place="apple_orchard",
        damage="sleeve_rip",
        fix="patch",
        glow="paper_star",
        chant="clap",
        child_name="Finn",
        child_type="boy",
        parent="father",
    ),
    StoryParams(
        place="sunflower_garden",
        damage="loose_straw",
        fix="twine",
        glow="firefly",
        chant="sway",
        child_name="June",
        child_type="girl",
        parent="mother",
    ),
    StoryParams(
        place="apple_orchard",
        damage="floppy_hat",
        fix="ribbon",
        glow="firefly",
        chant="clap",
        child_name="Theo",
        child_type="boy",
        parent="father",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, damage, fix, glow, chant) combos:\n")
        for place, damage, fix, glow, chant in combos:
            print(f"  {place:17} {damage:12} {fix:7} {glow:10} {chant}")
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
            header = f"### {p.child_name}: {p.damage} at {p.place} with {p.fix} and {p.glow}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
