#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py
=============================================================================

A small storyworld for a child-facing ghost-story-flavored tale about a scary
shape in the dark that turns out to be jelly. The world models a frightened
mistake, a grounded reveal, and a playful transformation into something funny.

Core domain
-----------
A child wakes at night, sees a pale wobbling shape in a dim place, and whispers
that it might be a ghost. A calm helper comes to look. The helper uses a
sensible reveal method -- turning on a light, tapping the bowl so it jiggles, or
both -- and the "ghost" is revealed to be jelly. Then the helper transforms the
jelly into a silly snack with a face or funny shape, and fear turns into
laughter.

Run it
------
python storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py
python storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py --qa
python storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py --trace
python storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py --json
python storyworlds/worlds/gpt-5.4/jelly_dialogue_humor_transformation_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
# File lives under storyworlds/worlds/gpt-5.4/, so we need the package dir
# storyworlds/ on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
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
            "sister": "sister",
            "brother": "brother",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    dim: bool = True
    moonlit: bool = False
    spooky_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Flavor:
    id: str
    label: str
    color_word: str
    pale: bool = False
    clear: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def ghostly(self) -> bool:
        return self.pale or self.clear


@dataclass
class Mold:
    id: str
    label: str
    phrase: str
    spooky: bool = False
    wobble_word: str = "wobbled"
    shadow_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    gives_light: bool = False
    makes_wobble: bool = False
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Finish:
    id: str
    label: str
    text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    flavor: str
    mold: str
    response: str
    finish: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


PLACES = {
    "pantry": Place(
        id="pantry",
        label="pantry shelf",
        phrase="the pantry shelf beside the kitchen door",
        dim=True,
        moonlit=False,
        spooky_line="The crack under the door let in only a thin stripe of light.",
        tags={"dark", "kitchen"},
    ),
    "windowsill": Place(
        id="windowsill",
        label="kitchen windowsill",
        phrase="the kitchen windowsill",
        dim=True,
        moonlit=True,
        spooky_line="Moonlight slipped through the window and made bright edges on everything.",
        tags={"moon", "kitchen"},
    ),
    "icebox": Place(
        id="icebox",
        label="old icebox tray",
        phrase="the old icebox tray in the back of the fridge",
        dim=True,
        moonlit=False,
        spooky_line="When the door was only a little open, the cold blue light made shapes look strange.",
        tags={"cold", "kitchen"},
    ),
    "table": Place(
        id="table",
        label="kitchen table",
        phrase="the middle of the kitchen table",
        dim=False,
        moonlit=False,
        spooky_line="The room was plain and bright enough to see clearly.",
        tags={"kitchen"},
    ),
}

FLAVORS = {
    "lemon": Flavor(
        id="lemon",
        label="lemon jelly",
        color_word="pale yellow",
        pale=True,
        clear=False,
        tags={"jelly", "yellow"},
    ),
    "lychee": Flavor(
        id="lychee",
        label="lychee jelly",
        color_word="almost clear",
        pale=False,
        clear=True,
        tags={"jelly", "clear"},
    ),
    "strawberry": Flavor(
        id="strawberry",
        label="strawberry jelly",
        color_word="pink",
        pale=False,
        clear=False,
        tags={"jelly", "pink"},
    ),
    "lime": Flavor(
        id="lime",
        label="lime jelly",
        color_word="bright green",
        pale=False,
        clear=False,
        tags={"jelly", "green"},
    ),
}

MOLDS = {
    "ring": Mold(
        id="ring",
        label="ring",
        phrase="a tall ring of jelly",
        spooky=True,
        wobble_word="shivered in a neat round wobble",
        shadow_line="Its hollow middle looked like a dark mouth from far away.",
        tags={"ring"},
    ),
    "tower": Mold(
        id="tower",
        label="tower",
        phrase="a tall tower of jelly",
        spooky=True,
        wobble_word="quivered from top to bottom",
        shadow_line="Its long shape made a thin, standing shadow on the wall.",
        tags={"tower"},
    ),
    "sheet": Mold(
        id="sheet",
        label="sheet",
        phrase="a loose, folded sheet of jelly",
        spooky=True,
        wobble_word="flapped and jiggled all at once",
        shadow_line="Its droopy folds looked exactly wrong in the dark, like a tiny floating sheet.",
        tags={"sheet"},
    ),
    "star": Mold(
        id="star",
        label="star",
        phrase="a little star-shaped jelly",
        spooky=False,
        wobble_word="twinkled and wobbled",
        shadow_line="Its points were too cheerful to be spooky.",
        tags={"star"},
    ),
}

RESPONSES = {
    "lamp": Response(
        id="lamp",
        label="switch on the lamp",
        sense=3,
        gives_light=True,
        makes_wobble=False,
        text="reached for the little lamp and clicked it on",
        qa_text="turned on the lamp so they could see clearly",
        tags={"lamp", "light"},
    ),
    "spoon": Response(
        id="spoon",
        label="tap the bowl with a spoon",
        sense=2,
        gives_light=False,
        makes_wobble=True,
        text="picked up a spoon and gave the bowl the gentlest tap",
        qa_text="tapped the bowl so the jelly jiggle showed what it really was",
        tags={"spoon", "jiggle"},
    ),
    "lamp_and_spoon": Response(
        id="lamp_and_spoon",
        label="switch on the lamp and tap the bowl",
        sense=3,
        gives_light=True,
        makes_wobble=True,
        text="clicked on the little lamp and then tapped the bowl with a spoon",
        qa_text="turned on the lamp and tapped the bowl, making the jelly easy to recognize",
        tags={"lamp", "spoon", "light", "jiggle"},
    ),
    "hide": Response(
        id="hide",
        label="hide under a blanket",
        sense=1,
        gives_light=False,
        makes_wobble=False,
        text="ducked away from the shape",
        qa_text="hid from it",
        tags={"fear"},
    ),
}

FINISHES = {
    "berry_face": Finish(
        id="berry_face",
        label="berry face",
        text="Then {helper} pressed in two blueberry eyes and a raspberry smile, turning the wobble into the silliest face in the kitchen.",
        ending_image="{child} laughed so hard that the berry-eyed jelly shook on the plate like it was laughing too.",
        tags={"berries", "humor"},
    ),
    "cream_hat": Finish(
        id="cream_hat",
        label="cream hat",
        text="Then {helper} set a puff of whipped cream on top like a floppy nightcap, and suddenly the scary shape looked sleepy instead of spooky.",
        ending_image="The jelly sat there in its cream hat, wobbling like a polite little ghost who had forgotten how to be frightening.",
        tags={"cream", "humor"},
    ),
    "star_cuts": Finish(
        id="star_cuts",
        label="star cuts",
        text="Then {helper} slid the jelly onto a board and cut it into bouncing star pieces, each one wobbling away from the next like a parade of tiny dancers.",
        ending_image="{child} popped one star into {child_possessive} mouth and grinned at the plate of jiggling stars.",
        tags={"stars", "humor"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
HELPER_OPTIONS = [
    ("mother", "Mom", "woman"),
    ("father", "Dad", "man"),
    ("sister", None, "girl"),
    ("brother", None, "boy"),
]


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


def _r_ghostly_shape(world: World) -> list[str]:
    child = world.get("child")
    jelly = world.get("jelly")
    place = world.facts["place_cfg"]
    flavor = world.facts["flavor_cfg"]
    mold = world.facts["mold_cfg"]
    if not (place.dim and flavor.ghostly and mold.spooky):
        return []
    sig = ("ghostly_shape",)
    if sig in world.fired:
        return []
    if jelly.meters["revealed"] >= THRESHOLD:
        return []
    world.fired.add(sig)
    jelly.meters["ghost_seeming"] += 1
    child.memes["fear"] += 1
    return ["__ghost__"]


def _r_reveal_by_light(world: World) -> list[str]:
    jelly = world.get("jelly")
    child = world.get("child")
    if jelly.meters["lit"] < THRESHOLD:
        return []
    sig = ("reveal_by_light",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    jelly.meters["revealed"] += 1
    jelly.meters["ghost_seeming"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["curiosity"] += 1
    return ["__revealed__"]


def _r_reveal_by_wobble(world: World) -> list[str]:
    jelly = world.get("jelly")
    child = world.get("child")
    if jelly.meters["jiggled"] < THRESHOLD:
        return []
    sig = ("reveal_by_wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    jelly.meters["revealed"] += 1
    jelly.meters["ghost_seeming"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["curiosity"] += 1
    return ["__revealed__"]


def _r_laughter_after_finish(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    jelly = world.get("jelly")
    if jelly.meters["transformed"] < THRESHOLD:
        return []
    sig = ("laughter_after_finish",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["giggles"] += 1
    child.memes["relief"] += 1
    helper.memes["warmth"] += 1
    return ["__laugh__"]


CAUSAL_RULES = [
    Rule(name="ghostly_shape", tag="fear", apply=_r_ghostly_shape),
    Rule(name="reveal_by_light", tag="reveal", apply=_r_reveal_by_light),
    Rule(name="reveal_by_wobble", tag="reveal", apply=_r_reveal_by_wobble),
    Rule(name="laughter_after_finish", tag="humor", apply=_r_laughter_after_finish),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


def spooky_combo(place: Place, flavor: Flavor, mold: Mold) -> bool:
    return place.dim and flavor.ghostly and mold.spooky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN and (r.gives_light or r.makes_wobble)]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for flavor_id, flavor in FLAVORS.items():
            for mold_id, mold in MOLDS.items():
                if spooky_combo(place, flavor, mold):
                    combos.append((place_id, flavor_id, mold_id))
    return combos


def explain_rejection(place: Place, flavor: Flavor, mold: Mold) -> str:
    if not place.dim:
        return (
            f"(No story: {place.phrase} is not dim enough for a ghost mistake. "
            f"In this world, the scary misunderstanding needs darkness or strange light.)"
        )
    if not flavor.ghostly:
        return (
            f"(No story: {flavor.label} is {flavor.color_word}, which does not read as ghostly here. "
            f"Use a pale or clear jelly for the mistaken ghost shape.)"
        )
    if not mold.spooky:
        return (
            f"(No story: {mold.phrase} looks too cheerful to be mistaken for a ghost. "
            f"Pick a taller or droopier shape.)"
        )
    return "(No story: this combination does not support the ghostly misunderstanding.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a reveal method like {better}.)"
    )


def reveal_outcome(response: Response) -> str:
    return "revealed" if (response.gives_light or response.makes_wobble) and response.sense >= SENSE_MIN else "unresolved"


def helper_label(role: str, helper: Entity) -> str:
    if role in {"mother", "father"}:
        return role
    return helper.label_word


def predict_reveal(place: Place, flavor: Flavor, mold: Mold, response: Response) -> dict:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="girl", label="child"))
    world.add(Entity(id="helper", kind="character", type="woman", label="helper"))
    jelly = world.add(Entity(id="jelly", kind="thing", type="dessert", label=flavor.label))
    world.facts.update(place_cfg=place, flavor_cfg=flavor, mold_cfg=mold)
    propagate(world, narrate=False)
    if response.gives_light:
        jelly.meters["lit"] += 1
    if response.makes_wobble:
        jelly.meters["jiggled"] += 1
    propagate(world, narrate=False)
    return {
        "initial_fear": child.memes["fear"],
        "revealed": jelly.meters["revealed"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, helper: Entity, place: Place, flavor: Flavor, mold: Mold) -> None:
    world.say(
        f"Late one night, {child.id} padded to the kitchen for a sip of water."
    )
    world.say(
        f"{place.spooky_line} On {place.phrase} stood {mold.phrase} of {flavor.color_word} {flavor.label}."
    )
    world.say(
        f"{mold.shadow_line} In that hush and half-light, it did not look like a dessert at all."
    )
    propagate(world, narrate=False)
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f'"Oh!" {child.id} whispered. "There is a ghost in the kitchen."'
        )


def call_helper(world: World, child: Entity, helper: Entity, helper_role_name: str) -> None:
    child.memes["hope"] += 1
    world.say(
        f'{child.id} backed up one careful step and called, "{helper.id}, please come see."'
    )
    world.say(
        f"{helper.id} came in with sleepy hair and a calm face. "
        f'"A ghost?" {helper.pronoun()} said. "Let us look before we decide."'
    )
    world.facts["helper_role_name"] = helper_role_name


def reveal(world: World, child: Entity, helper: Entity, place: Place, flavor: Flavor,
           mold: Mold, response: Response) -> None:
    jelly = world.get("jelly")
    pred = predict_reveal(place, flavor, mold, response)
    world.facts["predicted_fear"] = pred["initial_fear"]
    world.facts["predicted_revealed"] = pred["revealed"]
    world.say(f"{helper.id} {response.text}.")
    if response.gives_light:
        jelly.meters["lit"] += 1
        world.say("Warm light spread over the counter and chased the sharp shadows away.")
    if response.makes_wobble:
        jelly.meters["jiggled"] += 1
        world.say(
            f"The shape {mold.wobble_word}, and a tiny wet plop came from the bowl."
        )
    propagate(world, narrate=False)
    if jelly.meters["revealed"] >= THRESHOLD:
        child.memes["wonder"] += 1
        world.say(
            f'"That is not a ghost at all," {helper.id} said, smiling. "It is jelly."'
        )
        world.say(
            f'{child.id} blinked at it. "A ghost would not jiggle like that," {child.pronoun()} said.'
        )
        world.say(
            f'"A very serious ghost might try," {helper.id} said, and now even {child.id} had to snort a little.'
        )


def transform(world: World, child: Entity, helper: Entity, finish: Finish) -> None:
    jelly = world.get("jelly")
    jelly.meters["transformed"] += 1
    world.say(
        finish.text.format(
            helper=helper.id,
            child=child.id,
            child_possessive=child.pronoun("possessive"),
        )
    )
    propagate(world, narrate=False)


def ending(world: World, child: Entity, helper: Entity, finish: Finish) -> None:
    world.say(
        finish.ending_image.format(
            helper=helper.id,
            child=child.id,
            child_possessive=child.pronoun("possessive"),
        )
    )
    world.say(
        f"When {child.id} went back to bed, the kitchen no longer felt haunted. "
        f"It felt like a place where even a scare could wobble into a joke."
    )


def tell(place: Place, flavor: Flavor, mold: Mold, response: Response, finish: Finish,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         helper_role: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        attrs={"helper_role": helper_role},
    ))
    jelly = world.add(Entity(
        id="jelly",
        kind="thing",
        type="dessert",
        label=flavor.label,
        phrase=f"{mold.phrase} of {flavor.label}",
        tags=set(flavor.tags) | set(mold.tags),
    ))
    world.facts.update(
        place_cfg=place,
        flavor_cfg=flavor,
        mold_cfg=mold,
        response_cfg=response,
        finish_cfg=finish,
        child=child,
        helper=helper,
        jelly=jelly,
    )

    opening(world, child, helper, place, flavor, mold)
    world.para()
    call_helper(world, child, helper, helper_label(helper_role, helper))
    world.para()
    reveal(world, child, helper, place, flavor, mold, response)
    world.para()
    transform(world, child, helper, finish)
    ending(world, child, helper, finish)

    world.facts.update(
        scared_initially=child.memes["hope"] >= THRESHOLD or jelly.meters["revealed"] >= THRESHOLD,
        revealed=jelly.meters["revealed"] >= THRESHOLD,
        transformed=jelly.meters["transformed"] >= THRESHOLD,
        laughing=child.memes["giggles"] >= THRESHOLD,
        helper_role_name=helper_label(helper_role, helper),
    )
    return world


KNOWLEDGE = {
    "jelly": [
        (
            "What is jelly?",
            "Jelly is a soft dessert made to hold together but still wobble when you shake it. That wobble is why it can look funny in a bowl."
        )
    ],
    "light": [
        (
            "Why do things look scarier in the dark?",
            "In the dark, you cannot see edges and colors clearly, so your brain may guess the wrong thing. A shape can seem spooky until you add more light."
        )
    ],
    "shadows": [
        (
            "What does a shadow do to a shape?",
            "A shadow can stretch a shape or hide part of it. That can make an ordinary thing look bigger or stranger than it really is."
        )
    ],
    "spoon": [
        (
            "Why would tapping jelly help you know what it is?",
            "Tapping jelly makes it jiggle in a special way. That silly wobble tells you it is a dessert, not a ghost."
        )
    ],
    "berries": [
        (
            "Why do faces on food look funny?",
            "A face on food is surprising because food does not really have feelings. The surprise makes many people laugh."
        )
    ],
    "cream": [
        (
            "What is whipped cream like?",
            "Whipped cream is light, soft, and fluffy. It can make a dessert look playful."
        )
    ],
    "stars": [
        (
            "Why do star shapes feel cheerful?",
            "Stars are bright and playful shapes in many stories and pictures. They often feel less scary than long shadows or droopy shapes."
        )
    ],
}
KNOWLEDGE_ORDER = ["jelly", "light", "shadows", "spoon", "berries", "cream", "stars"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    flavor = f["flavor_cfg"]
    return [
        f'Write a short ghost-story-style story for a 3-to-5-year-old that includes the word "jelly" and ends in laughter.',
        f"Tell a bedtime kitchen story where {child.id} mistakes {flavor.label} on {place.phrase} for a ghost, then a calm {helper_label(helper.attrs.get('helper_role', ''), helper)} reveals the truth.",
        "Write a gentle spooky story with dialogue, a funny reveal, and a transformation that turns a scare into a silly snack.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    flavor = f["flavor_cfg"]
    mold = f["mold_cfg"]
    response = f["response_cfg"]
    finish = f["finish_cfg"]
    helper_role_name = f["helper_role_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who woke in the night and thought there was a ghost in the kitchen, and {helper.id}, the {helper_role_name} who came to help."
        ),
        (
            "Why did the jelly look like a ghost at first?",
            f"It was sitting on {place.phrase} in dim light, and its {flavor.color_word} color and {mold.label} shape looked strange from far away. The dark hid the ordinary details, so {child.id} made a frightened guess."
        ),
        (
            f"What did {child.id} say when {child.pronoun()} saw it?",
            f'{child.id} whispered that there was a ghost in the kitchen. The whisper shows that {child.pronoun()} felt scared and did not yet know what the shape really was.'
        ),
        (
            f"How did {helper.id} figure out it was jelly?",
            f"{helper.id} {response.qa_text}. That changed the scene from a shadowy guess into something clear enough to understand."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                "How did the scary moment turn funny?",
                f"After the reveal, {helper.id} changed the jelly with {finish.label}. That transformation gave the jelly a silly new look, so fear turned into giggles."
            )
        )
    if f.get("laughing"):
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt relieved and amused. By the end, the kitchen seemed safe again because the 'ghost' had turned into a wobbling joke."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"jelly", "light", "shadows"}
    response = f["response_cfg"]
    finish = f["finish_cfg"]
    if "spoon" in response.tags or "jiggle" in response.tags:
        tags.add("spoon")
    if finish.id == "berry_face":
        tags.add("berries")
    if finish.id == "cream_hat":
        tags.add("cream")
    if finish.id == "star_cuts":
        tags.add("stars")
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="windowsill",
        flavor="lychee",
        mold="sheet",
        response="lamp_and_spoon",
        finish="berry_face",
        child_name="Lily",
        child_gender="girl",
        helper_name="Mom",
        helper_gender="mother",
        helper_role="mother",
        seed=101,
    ),
    StoryParams(
        place="pantry",
        flavor="lemon",
        mold="tower",
        response="lamp",
        finish="cream_hat",
        child_name="Ben",
        child_gender="boy",
        helper_name="Dad",
        helper_gender="father",
        helper_role="father",
        seed=102,
    ),
    StoryParams(
        place="icebox",
        flavor="lychee",
        mold="ring",
        response="spoon",
        finish="star_cuts",
        child_name="Mia",
        child_gender="girl",
        helper_name="Zoe",
        helper_gender="girl",
        helper_role="sister",
        seed=103,
    ),
]


ASP_RULES = r"""
ghostly_flavor(F) :- flavor(F), pale(F).
ghostly_flavor(F) :- flavor(F), clear(F).

spooky_combo(P, F, M) :- place(P), dim(P), ghostly_flavor(F), mold(M), spooky(M).

sensible_response(R) :- response(R), sense(R, S), sense_min(Min), S >= Min, gives_light(R).
sensible_response(R) :- response(R), sense(R, S), sense_min(Min), S >= Min, makes_wobble(R).

revealed(R) :- sensible_response(R), gives_light(R).
revealed(R) :- sensible_response(R), makes_wobble(R).
outcome(R, revealed) :- revealed(R).
outcome(R, unresolved) :- response(R), not revealed(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.dim:
            lines.append(asp.fact("dim", place_id))
        if place.moonlit:
            lines.append(asp.fact("moonlit", place_id))
    for flavor_id, flavor in FLAVORS.items():
        lines.append(asp.fact("flavor", flavor_id))
        if flavor.pale:
            lines.append(asp.fact("pale", flavor_id))
        if flavor.clear:
            lines.append(asp.fact("clear", flavor_id))
    for mold_id, mold in MOLDS.items():
        lines.append(asp.fact("mold", mold_id))
        if mold.spooky:
            lines.append(asp.fact("spooky", mold_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        if response.gives_light:
            lines.append(asp.fact("gives_light", response_id))
        if response.makes_wobble:
            lines.append(asp.fact("makes_wobble", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show spooky_combo/3."))
    return sorted(set(asp.atoms(model, "spooky_combo")))


def asp_sensible_responses() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(response_id: str) -> str:
    import asp
    model = asp.one_model(asp_program("", f"#show outcome/2."))
    outcomes = {rid: out for rid, out in asp.atoms(model, "outcome")}
    return outcomes.get(response_id, "?")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a ghostly jelly misunderstanding that turns funny."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flavor", choices=FLAVORS)
    ap.add_argument("--mold", choices=MOLDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--finish", choices=FINISHES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=["mother", "father", "sister", "brother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid spooky combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_helper(role: str, rng: random.Random, avoid: str = "") -> tuple[str, str]:
    if role == "mother":
        return "Mom", "mother"
    if role == "father":
        return "Dad", "father"
    if role == "sister":
        return pick_name(rng, "girl", avoid=avoid), "girl"
    if role == "brother":
        return pick_name(rng, "boy", avoid=avoid), "boy"
    raise StoryError(f"(No story: unknown helper role '{role}'.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.flavor and args.mold:
        place = PLACES[args.place]
        flavor = FLAVORS[args.flavor]
        mold = MOLDS[args.mold]
        if not spooky_combo(place, flavor, mold):
            raise StoryError(explain_rejection(place, flavor, mold))

    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.flavor is None or combo[1] == args.flavor)
        and (args.mold is None or combo[2] == args.mold)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, flavor_id, mold_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    finish_id = args.finish or rng.choice(sorted(FINISHES.keys()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or pick_name(rng, child_gender)
    helper_role = args.helper_role or rng.choice(["mother", "father", "sister", "brother"])
    helper_name, helper_gender = resolve_helper(helper_role, rng, avoid=child_name)

    return StoryParams(
        place=place_id,
        flavor=flavor_id,
        mold=mold_id,
        response=response_id,
        finish=finish_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_role,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.flavor not in FLAVORS:
        raise StoryError(f"(No story: unknown flavor '{params.flavor}'.)")
    if params.mold not in MOLDS:
        raise StoryError(f"(No story: unknown mold '{params.mold}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if params.finish not in FINISHES:
        raise StoryError(f"(No story: unknown finish '{params.finish}'.)")

    place = PLACES[params.place]
    flavor = FLAVORS[params.flavor]
    mold = MOLDS[params.mold]
    response = RESPONSES[params.response]
    finish = FINISHES[params.finish]

    if not spooky_combo(place, flavor, mold):
        raise StoryError(explain_rejection(place, flavor, mold))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        flavor=flavor,
        mold=mold,
        response=response,
        finish=finish,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_role=params.helper_role,
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
    try:
        clingo_set = set(asp_valid_combos())
        python_set = set(valid_combos())
        if clingo_set == python_set:
            print(f"OK: ASP spooky_combo matches valid_combos() ({len(clingo_set)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid combos:")
            if clingo_set - python_set:
                print("  only in clingo:", sorted(clingo_set - python_set))
            if python_set - clingo_set:
                print("  only in python:", sorted(python_set - clingo_set))

        clingo_responses = set(asp_sensible_responses())
        python_responses = {r.id for r in sensible_responses()}
        if clingo_responses == python_responses:
            print(f"OK: sensible responses match ({sorted(clingo_responses)}).")
        else:
            rc = 1
            print("MISMATCH in sensible responses:")
            print("  clingo:", sorted(clingo_responses))
            print("  python:", sorted(python_responses))

        for response_id in RESPONSES:
            asp_result = asp_outcome(response_id)
            py_result = reveal_outcome(RESPONSES[response_id])
            if asp_result != py_result:
                rc = 1
                print(f"MISMATCH in outcome for {response_id}: clingo={asp_result} python={py_result}")
    except Exception as err:
        rc = 1
        print(f"VERIFY ERROR in ASP phase: {err}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "jelly" not in sample.story.lower():
            raise StoryError("(Verify failed: smoke-test story did not render a jelly story.)")
        print("OK: smoke-test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"VERIFY ERROR in smoke test: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show spooky_combo/3.\n#show sensible_response/1.\n#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible_responses())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} spooky (place, flavor, mold) combos:\n")
        for place_id, flavor_id, mold_id in combos:
            print(f"  {place_id:10} {flavor_id:10} {mold_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.flavor} {p.mold} at {p.place} ({p.response}, {p.finish})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
