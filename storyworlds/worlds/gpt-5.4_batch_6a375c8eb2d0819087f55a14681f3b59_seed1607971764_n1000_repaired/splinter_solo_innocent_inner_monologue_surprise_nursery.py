#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/splinter_solo_innocent_inner_monologue_surprise_nursery.py
======================================================================================

A standalone story world for a tiny nursery-rhyme-like tale:

A small child prepares to sing a solo rhyme, touches something rough and gets a
splinter, worries quietly in an innocent inner monologue, then a kind grown-up
helps. The surprise is that the ending is not a lonely solo anymore: the child
begins alone and is lovingly joined at the end.

The world model drives the prose:
- physical meters: splinter, sore, bandaged, removed
- emotional memes: pride, worry, fear, relief, belonging, courage

Reasonableness gate:
- only rough wooden props can honestly cause a splinter
- only sensible remedies are allowed by default
- outcome depends on splinter size, delay, and remedy power

Run it
------
python storyworlds/worlds/gpt-5.4/splinter_solo_innocent_inner_monologue_surprise_nursery.py
python storyworlds/worlds/gpt-5.4/splinter_solo_innocent_inner_monologue_surprise_nursery.py --prop stool --remedy tweezers
python storyworlds/worlds/gpt-5.4/splinter_solo_innocent_inner_monologue_surprise_nursery.py --prop paper_star
python storyworlds/worlds/gpt-5.4/splinter_solo_innocent_inner_monologue_surprise_nursery.py --all
python storyworlds/worlds/gpt-5.4/splinter_solo_innocent_inner_monologue_surprise_nursery.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Rhyme:
    id: str
    title: str
    opening: str
    refrain: str
    image: str
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
class Prop:
    id: str
    label: str
    phrase: str
    place: str
    touch: str
    rough: bool
    splinter_size: int
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
    sense: int
    power: int
    text: str
    fail: str
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


def _r_splinter_hurts(world: World) -> list[str]:
    child = world.get("child")
    finger = world.get("finger")
    if finger.meters["splinter"] < THRESHOLD:
        return []
    sig = ("splinter_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    finger.meters["sore"] += 1
    child.memes["worry"] += 1
    child.memes["fear"] += 1
    child.memes["courage"] -= 1
    return ["__ouch__"]


def _r_sore_shakes_song(world: World) -> list[str]:
    child = world.get("child")
    finger = world.get("finger")
    if finger.meters["sore"] < THRESHOLD or child.memes["pride"] < THRESHOLD:
        return []
    sig = ("sore_shakes_song",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hesitation"] += 1
    return ["__hesitate__"]


def _r_fix_brings_relief(world: World) -> list[str]:
    child = world.get("child")
    finger = world.get("finger")
    if finger.meters["removed"] < THRESHOLD or finger.meters["bandaged"] < THRESHOLD:
        return []
    sig = ("fix_brings_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["courage"] += 2
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="splinter_hurts", tag="physical", apply=_r_splinter_hurts),
    Rule(name="sore_shakes_song", tag="emotional", apply=_r_sore_shakes_song),
    Rule(name="fix_brings_relief", tag="emotional", apply=_r_fix_brings_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(prop: Prop) -> bool:
    return prop.rough and prop.splinter_size > 0


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def severity_of(prop: Prop, delay: int) -> int:
    return prop.splinter_size + delay


def is_fixed(remedy: Remedy, prop: Prop, delay: int) -> bool:
    return remedy.power >= severity_of(prop, delay)


def predict_after_splinter(world: World, prop: Prop) -> dict:
    sim = world.copy()
    finger = sim.get("finger")
    finger.meters["splinter"] += prop.splinter_size
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "sore": finger.meters["sore"],
        "worry": child.memes["worry"],
        "hesitation": child.memes["hesitation"],
    }


def setup_story(world: World, child: Entity, grownup: Entity, rhyme: Rhyme, prop: Prop) -> None:
    child.memes["pride"] += 1
    child.memes["courage"] += 1
    world.say(
        f"In the bright nursery room, {child.id} stood small and tall all at once. "
        f'Today was {child.pronoun("possessive")} turn to sing a solo called "{rhyme.title}."'
    )
    world.say(
        f'{rhyme.opening} {child.id} held the last line in {child.pronoun("possessive")} head: '
        f'"{rhyme.refrain}"'
    )
    world.say(
        f"Near {prop.place} waited {prop.phrase}, ready for the little show. "
        f"{grownup.label_word.capitalize()} smiled and said the room was listening."
    )


def touch_prop(world: World, child: Entity, prop: Prop) -> None:
    world.say(
        f"{child.id} reached for {prop.phrase} to {prop.touch}. The wood gave a shy little catch."
    )


def get_splinter(world: World, child: Entity, prop: Prop) -> None:
    finger = world.get("finger")
    finger.meters["splinter"] += prop.splinter_size
    world.facts["splinter_size"] = prop.splinter_size
    propagate(world, narrate=False)
    world.say(
        f"A tiny splinter slipped into {child.pronoun('possessive')} finger. "
        f"It was small, but it stung like a sharp crumb of straw."
    )


def inner_monologue(world: World, child: Entity, rhyme: Rhyme) -> None:
    worry = world.get("child").memes["worry"]
    extra = " The thought felt innocent and brave, but also wobbly." if worry >= THRESHOLD else ""
    world.say(
        f'{child.id} did not cry out. Inside, {child.pronoun()} thought, '
        f'"I wanted to sing so sweet and solo. If I hide my hand, maybe the song can still go."'
        f"{extra}"
    )
    if world.get("child").memes["hesitation"] >= THRESHOLD:
        world.say(
            f'But when {child.pronoun()} whispered "{rhyme.refrain}" to {child.pronoun("object")}self, '
            f"the note trembled a little."
        )


def notice_and_ask(world: World, grownup: Entity, child: Entity, prop: Prop) -> None:
    pred = predict_after_splinter(world, prop)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{grownup.label_word.capitalize()} saw the curl of {child.id}\'s hand and bent down close. '
        f'"Little one, what pricked you?" {grownup.pronoun()} asked.'
    )
    world.say(
        f'Then {child.id} opened {child.pronoun("possessive")} palm and whispered, '
        f'"A splinter. I meant no fuss. I only wanted the song."'
    )


def kind_reply(world: World, grownup: Entity, child: Entity) -> None:
    world.say(
        f'"That is an innocent wish," {grownup.label_word} said softly. '
        f'"Songs are for sharing, and hurts are for telling."'
    )


def fix_success(world: World, grownup: Entity, child: Entity, remedy: Remedy) -> None:
    finger = world.get("finger")
    finger.meters["splinter"] = 0.0
    finger.meters["removed"] += 1
    finger.meters["bandaged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{grownup.label_word.capitalize()} {remedy.text}. Soon the sore place felt tucked and safe."
    )


def fix_fail(world: World, grownup: Entity, child: Entity, remedy: Remedy) -> None:
    finger = world.get("finger")
    finger.meters["bandaged"] += 1
    finger.meters["sore"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{grownup.label_word.capitalize()} {remedy.fail}. The finger felt safer, but not ready for a brave high note."
    )


def surprise_finish(world: World, grownup: Entity, child: Entity, rhyme: Rhyme) -> None:
    child.memes["belonging"] += 2
    world.say(
        f"Then came the surprise. {grownup.label_word.capitalize()} tapped the floor once and said, "
        f'"You may start it solo, and we will answer on the last line."'
    )
    world.say(
        f"{child.id} sang the first part alone, soft as a wren at dawn. "
        f'On "{rhyme.refrain}," the whole room joined in, and the song bloomed wide.'
    )
    world.say(
        f"{rhyme.image} {child.id}'s face shone; the solo had begun lonely, but it ended held by many."
    )


def gentle_rest_finish(world: World, grownup: Entity, child: Entity, rhyme: Rhyme) -> None:
    child.memes["belonging"] += 1
    child.memes["relief"] += 1
    world.say(
        f"Then came a different surprise. {grownup.label_word.capitalize()} set the solo aside and said, "
        f'"Today you may hum beside me, and that is still music."'
    )
    world.say(
        f"So {child.id} nestled near and hummed {rhyme.refrain} while the room rocked slowly together. "
        f"The hurt finger rested, and the child was not alone."
    )
    world.say(
        f"{rhyme.image} The stage no longer mattered half so much as the warm ring of voices."
    )


def tell(
    rhyme: Rhyme,
    prop: Prop,
    remedy: Remedy,
    *,
    child_name: str = "Milly",
    child_type: str = "girl",
    grownup_type: str = "teacher",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    grownup = world.add(Entity(id="Grownup", kind="character", type=grownup_type, role="grownup", label="the grown-up"))
    finger = world.add(Entity(id="finger", type="finger", label="finger"))
    prop_ent = world.add(Entity(id="prop", type="prop", label=prop.label, tags=set(prop.tags)))

    child.memes["pride"] = 0.0
    child.memes["courage"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["hesitation"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["belonging"] = 0.0
    finger.meters["splinter"] = 0.0
    finger.meters["sore"] = 0.0
    finger.meters["removed"] = 0.0
    finger.meters["bandaged"] = 0.0
    prop_ent.meters["roughness"] = float(prop.splinter_size if prop.rough else 0)

    setup_story(world, child, grownup, rhyme, prop)
    world.para()
    touch_prop(world, child, prop)
    get_splinter(world, child, prop)
    inner_monologue(world, child, rhyme)
    world.para()
    notice_and_ask(world, grownup, child, prop)
    kind_reply(world, grownup, child)

    fixed = is_fixed(remedy, prop, delay)
    world.facts["delay"] = delay
    world.facts["fixed"] = fixed
    world.facts["outcome"] = "sang" if fixed else "rested"

    if fixed:
        world.para()
        fix_success(world, grownup, child, remedy)
        surprise_finish(world, grownup, child, rhyme)
    else:
        world.para()
        fix_fail(world, grownup, child, remedy)
        gentle_rest_finish(world, grownup, child, rhyme)

    world.facts.update(
        child=child,
        grownup=grownup,
        finger=finger,
        rhyme=rhyme,
        prop_cfg=prop,
        remedy=remedy,
        prop=prop_ent,
    )
    return world


RHYMES = {
    "moon": Rhyme(
        id="moon",
        title="Moon Cup, Silver Spoon",
        opening="Round the rug and past the chair, the morning hummed a milky tune.",
        refrain="Moon cup, silver spoon, sing me safely to the noon.",
        image="Like a lamp in a shell, the room seemed pearly and mild.",
        tags={"rhyme", "moon"},
    ),
    "lamb": Rhyme(
        id="lamb",
        title="Little Lamb by the Window",
        opening="By the blocks and by the books, the nursery waited for a gentle croon.",
        refrain="Little lamb, do not roam; every kind voice leads you home.",
        image="Like lamb's wool in sunlight, the air turned soft around the child.",
        tags={"rhyme", "lamb"},
    ),
    "sparrow": Rhyme(
        id="sparrow",
        title="Sparrow on the Sill",
        opening="On the painted sill of morning, the room kept time with a tiny tune.",
        refrain="Sparrow small, sparrow bright, borrow one star from the light.",
        image="Like feathers in a warm breeze, the voices fluttered and settled.",
        tags={"rhyme", "sparrow"},
    ),
}

PROPS = {
    "stool": Prop(
        id="stool",
        label="stool",
        phrase="a little wooden stool",
        place="the song corner",
        touch="climb up high enough to be seen",
        rough=True,
        splinter_size=2,
        tags={"wood", "stool", "splinter"},
    ),
    "rattle_box": Prop(
        id="rattle_box",
        label="rattle box",
        phrase="a wooden rattle box",
        place="the shelf by the rug",
        touch="lift the keepers' box of rhythm eggs",
        rough=True,
        splinter_size=1,
        tags={"wood", "music", "splinter"},
    ),
    "window_frame": Prop(
        id="window_frame",
        label="window frame",
        phrase="the old wooden window frame",
        place="the sunny window",
        touch="steady a small hand before the first note",
        rough=True,
        splinter_size=3,
        tags={"wood", "window", "splinter"},
    ),
    "paper_star": Prop(
        id="paper_star",
        label="paper star",
        phrase="a paper star on a string",
        place="the reading nook",
        touch="pat the hanging decoration for luck",
        rough=False,
        splinter_size=0,
        tags={"paper", "decoration"},
    ),
}

REMEDIES = {
    "tweezers": Remedy(
        id="tweezers",
        sense=3,
        power=3,
        text="brought out clean tweezers, lifted the splinter free, and wrapped the finger in a tiny bandage",
        fail="tried gently with the tweezers, but the little thorn sat too deep for one quick turn",
        qa_text="used clean tweezers to take the splinter out and wrapped the finger in a small bandage",
        tags={"tweezers", "bandage", "splinter"},
    ),
    "warm_cloth": Remedy(
        id="warm_cloth",
        sense=2,
        power=2,
        text="soothed the finger with a warm cloth, eased the splinter free, and added a neat little bandage",
        fail="soothed the finger with a warm cloth and covered it with a bandage, though the splinter still pinched underneath",
        qa_text="used a warm cloth, removed the splinter, and covered the finger with a bandage",
        tags={"bandage", "warm_cloth", "splinter"},
    ),
    "bandage_only": Remedy(
        id="bandage_only",
        sense=1,
        power=1,
        text="put on a bandage right away",
        fail="put on a bandage right away, but the splinter still poked beneath it",
        qa_text="put a bandage over the finger",
        tags={"bandage"},
    ),
}

GIRL_NAMES = ["Milly", "Daisy", "Lulu", "Nell", "Poppy", "Tess", "Maisie", "Ivy"]
BOY_NAMES = ["Toby", "Ned", "Ollie", "Finn", "Milo", "Jem", "Rory", "Kit"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for rhyme_id in RHYMES:
        for prop_id, prop in PROPS.items():
            if not hazard_at_risk(prop):
                continue
            for remedy_id, remedy in REMEDIES.items():
                if remedy.sense >= SENSE_MIN:
                    combos.append((rhyme_id, prop_id, remedy_id))
    return combos


@dataclass
class StoryParams:
    rhyme: str
    prop: str
    remedy: str
    name: str
    gender: str
    grownup: str
    delay: int = 0
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "splinter": [
        (
            "What is a splinter?",
            "A splinter is a tiny sharp piece of wood that gets stuck in your skin. Even a small one can sting a lot.",
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a sore spot and helps protect it from bumps and dirt. It does not always remove what is inside the skin.",
        )
    ],
    "tweezers": [
        (
            "What are tweezers for?",
            "Tweezers are a small tool for gripping tiny things. A careful grown-up can use them to take out a splinter.",
        )
    ],
    "warm_cloth": [
        (
            "Why might a warm cloth help a sore finger?",
            "A warm cloth can help a sore finger feel calmer and softer. That can make gentle cleaning and care easier.",
        )
    ],
    "solo": [
        (
            "What is a solo?",
            "A solo is a part of a song or performance done by one person alone. Sometimes a solo begins alone and ends with others joining in.",
        )
    ],
    "nursery": [
        (
            "What is a nursery rhyme?",
            "A nursery rhyme is a short song or poem with simple, musical words. It is meant to be easy to remember and pleasing to say aloud.",
        )
    ],
    "tell_hurt": [
        (
            "Why should a child tell a grown-up about a splinter?",
            "A grown-up can help remove the splinter safely before the sore spot gets worse. Telling early is brave and helps the hurt heal sooner.",
        )
    ],
}
KNOWLEDGE_ORDER = ["splinter", "tell_hurt", "tweezers", "warm_cloth", "bandage", "solo", "nursery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    rhyme = f["rhyme"]
    prop = f["prop_cfg"]
    if f["outcome"] == "sang":
        return [
            f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "splinter", "solo", and "innocent".',
            f"Tell a gentle story where {child.id} is meant to sing a solo from {rhyme.title}, gets a splinter from {prop.phrase}, thinks worried thoughts inside, and ends in a sweet surprise.",
            f"Write a musical story in which a child tries to be brave and quiet about a small hurt, but a kind grown-up helps and the ending turns from lonely to shared.",
        ]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "splinter", "solo", and "innocent".',
        f"Tell a soft story where {child.id} plans to sing a solo from {rhyme.title}, gets a splinter from {prop.phrase}, and a grown-up gently changes the plan.",
        f"Write a story with inner monologue and a surprise ending where a child learns that resting with others can still be part of the song.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    rhyme = f["rhyme"]
    prop = f["prop_cfg"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little child getting ready to sing a solo, and {grownup.label_word} who notices the trouble and helps. The story stays close to one small hurt and one kind fix.",
        ),
        (
            f"Why did {child.id} touch {prop.phrase}?",
            f"{child.id} was getting ready for the song and reached for {prop.phrase} as part of the little performance. The splinter came from that ordinary, innocent moment.",
        ),
        (
            f"What happened to {child.id}'s finger?",
            f"A tiny splinter slipped into {child.pronoun('possessive')} finger and made it sore. Even though it was small, it made singing feel shaky.",
        ),
        (
            f"What did {child.id} think inside?",
            f"{child.id} thought about hiding the hurt so the solo could still go on. That inner monologue shows {child.pronoun('possessive')} wish was innocent, but also worried.",
        ),
        (
            f"How did {grownup.label_word} help?",
            f"{grownup.label_word.capitalize()} listened kindly and {remedy.qa_text}. The help mattered because the sore finger was making the song feel hard.",
        ),
    ]
    if outcome == "sang":
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that {child.id} began the song solo, but the whole room joined on the last line. That changed the moment from lonely bravery into shared joy.",
            )
        )
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt relieved and brave again. The finger was safe, and the child no longer had to carry the song alone.",
            )
        )
    else:
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that the solo was set aside, and {child.id} was invited to hum close beside {grownup.label_word} instead. The song changed shape so the child could rest and still belong.",
            )
        )
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt comforted, even though the finger was still too sore for a full solo. Being included gently mattered more than standing alone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"splinter", "solo", "nursery", "tell_hurt"}
    remedy = world.facts["remedy"]
    for tag in remedy.tags:
        if tag in {"tweezers", "warm_cloth", "bandage"}:
            tags.add(tag)
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        rhyme="moon",
        prop="stool",
        remedy="tweezers",
        name="Milly",
        gender="girl",
        grownup="teacher",
        delay=0,
    ),
    StoryParams(
        rhyme="lamb",
        prop="rattle_box",
        remedy="warm_cloth",
        name="Toby",
        gender="boy",
        grownup="mother",
        delay=0,
    ),
    StoryParams(
        rhyme="sparrow",
        prop="window_frame",
        remedy="warm_cloth",
        name="Nell",
        gender="girl",
        grownup="teacher",
        delay=1,
    ),
    StoryParams(
        rhyme="moon",
        prop="window_frame",
        remedy="tweezers",
        name="Finn",
        gender="boy",
        grownup="father",
        delay=1,
    ),
]


def explain_rejection(prop: Prop) -> str:
    return (
        f"(No story: {prop.phrase} is not a believable source of a splinter here. "
        f"A splinter story needs rough wood that can honestly prick a finger.)"
    )


def explain_remedy(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.prop not in PROPS or params.remedy not in REMEDIES:
        raise StoryError("(Cannot compute outcome for unknown prop or remedy.)")
    return "sang" if is_fixed(REMEDIES[params.remedy], PROPS[params.prop], params.delay) else "rested"


ASP_RULES = r"""
hazard(P) :- prop(P), rough(P), splinter_size(P, S), S > 0.
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
valid(Rh, P, Rm) :- rhyme(Rh), prop(P), remedy(Rm), hazard(P), sensible(Rm).

severity(Sz + D) :- chosen_prop(P), splinter_size(P, Sz), delay(D).
fixed :- chosen_remedy(R), power(R, P), severity(V), P >= V.
outcome(sang) :- fixed.
outcome(rested) :- not fixed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rhyme_id in RHYMES:
        lines.append(asp.fact("rhyme", rhyme_id))
    for prop_id, prop in PROPS.items():
        lines.append(asp.fact("prop", prop_id))
        if prop.rough:
            lines.append(asp.fact("rough", prop_id))
        lines.append(asp.fact("splinter_size", prop_id, prop.splinter_size))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("power", remedy_id, remedy.power))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_prop", params.prop),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    py_sensible = {r.id for r in sensible_remedies()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible remedies match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a nursery-rhyme solo, a splinter, inner worry, and a kind surprise."
    )
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["teacher", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the sore finger goes before care")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump the world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (rhyme, prop, remedy) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop:
        if args.prop not in PROPS:
            raise StoryError("(Unknown prop.)")
        if not hazard_at_risk(PROPS[args.prop]):
            raise StoryError(explain_rejection(PROPS[args.prop]))
    if args.remedy:
        if args.remedy not in REMEDIES:
            raise StoryError("(Unknown remedy.)")
        if REMEDIES[args.remedy].sense < SENSE_MIN:
            raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.rhyme is None or combo[0] == args.rhyme)
        and (args.prop is None or combo[1] == args.prop)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    rhyme_id, prop_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["teacher", "mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])

    return StoryParams(
        rhyme=rhyme_id,
        prop=prop_id,
        remedy=remedy_id,
        name=name,
        gender=gender,
        grownup=grownup,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme '{params.rhyme}'.)")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop '{params.prop}'.)")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy '{params.remedy}'.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender '{params.gender}'.)")
    if params.grownup not in {"teacher", "mother", "father"}:
        raise StoryError(f"(Unknown grownup '{params.grownup}'.)")
    if params.delay not in {0, 1, 2}:
        raise StoryError("(Delay must be 0, 1, or 2.)")

    prop = PROPS[params.prop]
    remedy = REMEDIES[params.remedy]
    if not hazard_at_risk(prop):
        raise StoryError(explain_rejection(prop))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))

    world = tell(
        RHYMES[params.rhyme],
        prop,
        remedy,
        child_name=params.name,
        child_type=params.gender,
        grownup_type=params.grownup,
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
        print(f"{len(combos)} compatible (rhyme, prop, remedy) combos:\n")
        for rhyme_id, prop_id, remedy_id in combos:
            print(f"  {rhyme_id:8} {prop_id:12} {remedy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.rhyme} / {p.prop} / {p.remedy} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
