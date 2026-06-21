#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tupperware_misunderstanding_suspense_happy_ending_ghost_story.py
=============================================================================================

A standalone story world for a gentle ghost-story misunderstanding built around
tupperware. A child hears an eerie nighttime sound, mistakes an ordinary cause
for a ghost, and then learns the truth with help from a calm grown-up.

The world model is small on purpose:
- typed entities share one Entity dataclass
- physical meters track sounds, light, motion, and discovered causes
- emotional memes track fear, suspense, relief, courage, and joy
- a few causal rules turn strange noises into fear, light into calm, and a
  revealed cause into relief

The reasonableness gate is also deliberately small:
- each place only affords certain causes
- some causes create a snack ending, while others end in tidying-up
- the inline ASP twin mirrors the same compatibility and ending rules

Run it
------
    python storyworlds/worlds/gpt-5.4/tupperware_misunderstanding_suspense_happy_ending_ghost_story.py
    python storyworlds/worlds/gpt-5.4/tupperware_misunderstanding_suspense_happy_ending_ghost_story.py --place kitchen --cause fridge_stack
    python storyworlds/worlds/gpt-5.4/tupperware_misunderstanding_suspense_happy_ending_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/tupperware_misunderstanding_suspense_happy_ending_ghost_story.py --qa
    python storyworlds/worlds/gpt-5.4/tupperware_misunderstanding_suspense_happy_ending_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives under storyworlds/worlds/gpt-5.4/, so the
# package dir is three levels up.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    dark_detail: str
    investigate_path: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    places: set[str]
    sound_text: str
    sight_text: str
    whisper_guess: str
    reveal_text: str
    ending_image: str
    treat: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    beam_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    cause: str
    helper: str
    light: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child", "friend"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise_to_fear(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    if source is None or source.meters["noisy"] < THRESHOLD:
        return out
    for child in world.children():
        sig = ("fear_from_noise", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["fear"] += 1
        child.memes["suspense"] += 1
        out.append("__eerie__")
    return out


def _r_light_calms(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    if helper is None or helper.meters["light_on"] < THRESHOLD:
        return out
    for child in world.children():
        sig = ("calm_from_light", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
        child.memes["courage"] += 1
        out.append("__light__")
    return out


def _r_reveal_to_relief(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    if source is None or source.meters["revealed"] < THRESHOLD:
        return out
    for child in world.children():
        sig = ("relief_after_reveal", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["fear"] = 0.0
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_to_fear", tag="emotion", apply=_r_noise_to_fear),
    Rule(name="light_calms", tag="emotion", apply=_r_light_calms),
    Rule(name="reveal_to_relief", tag="emotion", apply=_r_reveal_to_relief),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        opening="The house was quiet, and the kitchen looked silver-blue under the moon.",
        dark_detail="From the doorway, the counters made long dark shapes, and every little click sounded larger than it should.",
        investigate_path="down the hall to the kitchen",
        affords={"fridge_stack", "cat_snack"},
        tags={"kitchen"},
    ),
    "pantry": Place(
        id="pantry",
        label="the pantry",
        opening="The house was quiet, and the pantry door stood a little open in the hall.",
        dark_detail="Inside, the shelves were dim and close together, and the shadows looked as if they were whispering to one another.",
        investigate_path="to the pantry at the end of the hall",
        affords={"cookie_tower", "wind_lid"},
        tags={"pantry"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        opening="The house was quiet, and the back porch windows glimmered with thin moonlight.",
        dark_detail="Coats hung by the door, and the moving shadows made the porch feel taller and stranger than it did in daytime.",
        investigate_path="to the back porch",
        affords={"wind_lid", "cat_snack"},
        tags={"porch"},
    ),
}

CAUSES = {
    "fridge_stack": Cause(
        id="fridge_stack",
        label="shivering tupperware stack",
        places={"kitchen"},
        sound_text="a thin clack-clack came from the kitchen, as if bony fingers were tapping plastic",
        sight_text="a tall stack of tupperware boxes gave a tiny shiver whenever the refrigerator hummed",
        whisper_guess="Maybe it is a kitchen ghost, waking up and knocking from the dark.",
        reveal_text="The refrigerator gave another sleepy hum, and a stack of tupperware boxes trembled against one another on top of it. Nothing spooky was there at all—just plastic boxes chattering because the fridge was vibrating.",
        ending_image="Together they moved the tupperware stack to a steadier shelf, and the kitchen grew still again.",
        treat=False,
        tags={"fridge", "tupperware"},
    ),
    "cat_snack": Cause(
        id="cat_snack",
        label="cat nudging a snack box",
        places={"kitchen", "porch"},
        sound_text="something made a soft bump... bump... bump, then a scritch across the floor",
        sight_text="a pale round shape slid through the dark and seemed to stop whenever anyone held a breath",
        whisper_guess="Maybe a little ghost is rolling its head across the floor.",
        reveal_text="The beam dropped to the floor, and there was the family cat, batting a tupperware box with crackers inside. Each nudge made the box bump and roll, and the pale thing they had feared was only the white lid flashing in the dark.",
        ending_image="The helper shook a few crackers into a small bowl, and the cat purred while the children laughed at their brave little 'ghost.'",
        treat=True,
        tags={"cat", "tupperware", "snack"},
    ),
    "cookie_tower": Cause(
        id="cookie_tower",
        label="wobbly cookie boxes",
        places={"pantry"},
        sound_text="from the pantry came a little tap... tap... tap, followed by a soft plastic sigh",
        sight_text="something pale leaned out between the shelves and then ducked back again",
        whisper_guess="Maybe a pantry ghost is peeking out, waiting for us to come closer.",
        reveal_text="On the top shelf, one round tupperware box full of cookies was leaning against another. Each time the house settled, the boxes tipped and tapped together, making the pale lid peep out and vanish again.",
        ending_image="Soon they were each holding half a cookie, and the pantry no longer felt haunted at all.",
        treat=True,
        tags={"cookies", "tupperware", "pantry"},
    ),
    "wind_lid": Cause(
        id="wind_lid",
        label="windy lid",
        places={"pantry", "porch"},
        sound_text="a faint fluttering click came and went, like a whisper that kept changing its mind",
        sight_text="a loose tupperware lid lifted and settled in the draft, making a white blink in the dark",
        whisper_guess="Maybe a ghost is waving at us from the shadows.",
        reveal_text="A window had been left a crack open, and the night breeze was lifting a loose tupperware lid and letting it fall again. The white blink in the dark was only the lid tipping up and down in the draft.",
        ending_image="After the window was shut and the lid was snapped back onto its box, the room felt ordinary and safe again.",
        treat=False,
        tags={"wind", "tupperware"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight from the drawer",
        beam_text="A bright circle of light slid ahead of them and pushed the shadows back.",
        tags={"flashlight"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="night-light",
        phrase="the little blue night-light from the hall",
        beam_text="The small blue glow was gentle, but it was enough to make the dark corners soften.",
        tags={"nightlight"},
    ),
    "lantern": Light(
        id="lantern",
        label="camping lantern",
        phrase="the camping lantern from the closet",
        beam_text="Warm yellow light bloomed around them and made the floorboards look friendly again.",
        tags={"lantern"},
    ),
}

HELPERS = {"mother", "father", "grandmother", "grandfather"}
GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "curious", "quiet", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for cause_id in sorted(CAUSES):
            if cause_id in place.affords and place_id in CAUSES[cause_id].places:
                combos.append((place_id, cause_id))
    return combos


def ending_of(cause_id: str) -> str:
    if cause_id not in CAUSES:
        raise StoryError(f"(Unknown cause '{cause_id}'.)")
    return "snack" if CAUSES[cause_id].treat else "tidy"


def explain_rejection(place_id: str, cause_id: str) -> str:
    if place_id not in PLACES:
        return f"(Unknown place '{place_id}'.)"
    if cause_id not in CAUSES:
        return f"(Unknown cause '{cause_id}'.)"
    return (
        f"(No story: {CAUSES[cause_id].label} does not fit {PLACES[place_id].label}. "
        f"Pick a cause that could reasonably happen there.)"
    )


def introduce(world: World, child: Entity, friend: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"It was late, and {child.id} and {friend.id} were supposed to be settling down for sleep at {helper.label_word}'s house."
    )
    world.say(place.opening)
    world.say(
        f"{child.id} pulled the blanket up to {child.pronoun('possessive')} chin, while {friend.id} listened to the tiny house sounds that usually seemed sleepy and small."
    )


def stir_mystery(world: World, child: Entity, friend: Entity, place: Place, cause: Cause) -> None:
    source = world.get("source")
    source.meters["noisy"] += 1
    source.meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(place.dark_detail)
    world.say(
        f"Then {cause.sound_text}. In the dark, {cause.sight_text}."
    )
    fear = max(child.memes["fear"], friend.memes["fear"])
    tag = "Both children went very still." if fear >= THRESHOLD else "They fell quiet at once."
    world.say(tag)


def whisper_guess(world: World, child: Entity, friend: Entity, cause: Cause) -> None:
    world.say(f'"Did you hear that?" {friend.id} whispered.')
    world.say(
        f'{child.id} nodded. "{cause.whisper_guess}"'
    )
    world.say(
        f"For a few long breaths, neither child wanted to put even one foot on the floor."
    )


def call_for_help(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'At last, {child.id} called softly, "{helper.label_word.capitalize()}? Something in the dark sounds spooky."'
    )


def helper_arrives(world: World, helper: Entity, light: Light, place: Place) -> None:
    helper.meters["light_on"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} came to the doorway, carrying {light.phrase}."
    )
    world.say(light.beam_text)
    world.say(
        f'"Let us look before we decide it is a ghost," {helper.pronoun()} said, and together they crept {place.investigate_path}.'
    )


def reveal(world: World, child: Entity, friend: Entity, helper: Entity, cause: Cause) -> None:
    source = world.get("source")
    source.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(cause.reveal_text)
    world.say(
        f"{child.id} let out a long breath, and {friend.id} pressed a hand over {friend.pronoun('possessive')} smile."
    )
    world.say(
        f'"So the ghost was only tupperware," {child.id} said.'
    )
    world.say(
        f'"And a jumpy imagination," {helper.label_word} said with a warm little laugh.'
    )


def ending(world: World, child: Entity, friend: Entity, helper: Entity, cause: Cause) -> None:
    if cause.treat:
        child.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(cause.ending_image)
        world.say(
            f"After that, even the moonlit house felt cozy, and bedtime no longer seemed scary at all."
        )
    else:
        child.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(cause.ending_image)
        world.say(
            f"When they went back to bed, the dark sounded ordinary again, and the children felt proud that they had asked for help instead of feeding the fright."
        )


def tell(
    place: Place,
    cause: Cause,
    light: Light,
    child_name: str,
    child_gender: str,
    friend_name: str,
    friend_gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        attrs={"trait": trait},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    world.add(Entity(
        id="place",
        kind="place",
        type="place",
        label=place.label,
        tags=set(place.tags),
    ))
    world.add(Entity(
        id="source",
        kind="thing",
        type="mystery",
        label=cause.label,
        tags=set(cause.tags),
    ))

    introduce(world, child, friend, helper, place)
    world.para()
    stir_mystery(world, child, friend, place, cause)
    whisper_guess(world, child, friend, cause)
    call_for_help(world, child, helper)
    world.para()
    helper_arrives(world, helper, light, place)
    reveal(world, child, friend, helper, cause)
    world.para()
    ending(world, child, friend, helper, cause)

    world.facts.update(
        child=child,
        friend=friend,
        helper=helper,
        place=place,
        cause=cause,
        light=light,
        ending=ending_of(cause.id),
        feared=child.memes["relief"] >= THRESHOLD or friend.memes["relief"] >= THRESHOLD,
        asked_for_help=child.memes["trust"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    place = world.facts["place"]
    cause = world.facts["cause"]
    return [
        'Write a gentle ghost-story for a 3-to-5-year-old that includes the word "tupperware" and ends happily.',
        f"Tell a suspenseful but safe bedtime story where {child.id} and {friend.id} hear a spooky sound near {place.label} and mistake it for a ghost.",
        f"Write a misunderstanding story where a scary nighttime clue turns out to be {cause.label}, and the ending feels warm instead of frightening.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    cause = world.facts["cause"]
    light = world.facts["light"]
    ending_kind = world.facts["ending"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id}, two children trying to be brave at bedtime, and {helper.label_word} who helps them investigate. The story happens near {place.label} at night.",
        ),
        (
            f"Why did {child.id} and {friend.id} think there might be a ghost?",
            f"They heard a strange sound in the dark and saw something pale moving, so their imaginations turned the mystery into a ghost. The dark hid the real cause, which made the misunderstanding feel much bigger.",
        ),
        (
            f"What was the scary thing really?",
            f"It was really {cause.label}. When {helper.label_word} brought {light.label}, the light made the true cause easy to see.",
        ),
        (
            f"How was the problem solved?",
            f"{child.id} called for help instead of staying alone with the fear, and {helper.label_word} came with {light.phrase}. Looking closely changed the mystery into an ordinary explanation.",
        ),
    ]
    if ending_kind == "snack":
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the children laughing after the truth was found. The last image is cozy because the tupperware mystery led to a small treat instead of a scare.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the room quiet and ordinary again after the tupperware was fixed. The children went back to bed feeling safe because the scary misunderstanding had been explained.",
            )
        )
    return qa


KNOWLEDGE = {
    "tupperware": [
        (
            "What is tupperware?",
            "Tupperware is a plastic container with a lid that people use to store food or small things. When lids wobble or boxes bump together, they can make clicky sounds.",
        )
    ],
    "ghost": [
        (
            "Why can shadows feel scary at night?",
            "Shadows can look strange at night because there is less light to show what things really are. When you cannot see clearly, your imagination may guess the wrong thing.",
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help when something seems scary?",
            "A flashlight helps you see what is really there. Clear light can turn a spooky guess into an ordinary answer.",
        )
    ],
    "cat": [
        (
            "Why do cats make noises at night?",
            "Cats often walk, scratch, and bat toys or boxes when the house is quiet. Their small sounds can seem much louder at night.",
        )
    ],
    "wind": [
        (
            "How can wind make a room sound spooky?",
            "Wind can rattle loose things, tap lids, and make small objects flutter. Those sounds are ordinary, but in the dark they can feel mysterious.",
        )
    ],
    "fridge": [
        (
            "Can a refrigerator make other things shake?",
            "Yes. A refrigerator can hum or vibrate a little, and nearby boxes may tremble or tap together because of that movement.",
        )
    ],
    "cookies": [
        (
            "Why do containers of cookies sometimes make noises?",
            "If one container leans against another, they can tap when a shelf shifts or the house settles. Hard cookies and plastic lids can make light knocking sounds.",
        )
    ],
    "help": [
        (
            "What should a child do if a dark room feels scary?",
            "It is a good idea to call a trusted grown-up. Asking for help is a brave way to learn what is really going on.",
        )
    ],
}
KNOWLEDGE_ORDER = ["tupperware", "ghost", "help", "flashlight", "cat", "wind", "fridge", "cookies"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cause = world.facts["cause"]
    light = world.facts["light"]
    tags = {"tupperware", "ghost", "help"} | set(cause.tags) | set(light.tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        cause="fridge_stack",
        helper="mother",
        light="flashlight",
        child_name="Lily",
        child_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        trait="careful",
    ),
    StoryParams(
        place="pantry",
        cause="cookie_tower",
        helper="grandfather",
        light="lantern",
        child_name="Mia",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        trait="curious",
    ),
    StoryParams(
        place="porch",
        cause="wind_lid",
        helper="father",
        light="nightlight",
        child_name="Sam",
        child_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        trait="quiet",
    ),
    StoryParams(
        place="kitchen",
        cause="cat_snack",
        helper="grandmother",
        light="flashlight",
        child_name="Ava",
        child_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        trait="brave",
    ),
]


ASP_RULES = r"""
valid(P, C) :- place(P), cause(C), affords(P, C), happens_in(C, P).

ending(snack, C) :- cause(C), treat(C).
ending(tidy, C)  :- cause(C), not treat(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cause_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, cause_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("happens_in", cause_id, place_id))
        if cause.treat:
            lines.append(asp.fact("treat", cause_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending(cause_id: str) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            extra=f"chosen({cause_id}).\nending_of(E) :- chosen(C), ending(E, C).",
            show="#show ending_of/1.",
        )
    )
    out = asp.atoms(model, "ending_of")
    return out[0][0] if out else "?"


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

    bad: list[tuple[str, str, str]] = []
    for cause_id in sorted(CAUSES):
        py = ending_of(cause_id)
        asp_val = asp_ending(cause_id)
        if py != asp_val:
            bad.append((cause_id, py, asp_val))
    if not bad:
        print("OK: ending model matches ending_of().")
    else:
        rc = 1
        print("MISMATCH in ending model:")
        for cause_id, py, asp_val in bad:
            print(f"  {cause_id}: python={py} clingo={asp_val}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(7))
        params.seed = 7
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty random story.)")
        print("OK: random generation smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spooky tupperware misunderstanding with a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in PLACES:
        raise StoryError(f"(Unknown place '{args.place}'.)")
    if args.cause is not None and args.cause not in CAUSES:
        raise StoryError(f"(Unknown cause '{args.cause}'.)")
    if args.light is not None and args.light not in LIGHTS:
        raise StoryError(f"(Unknown light '{args.light}'.)")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{args.helper}'.)")

    if args.place and args.cause:
        if (args.place, args.cause) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.place, args.cause))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cause_id = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    light = args.light or rng.choice(sorted(LIGHTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        cause=cause_id,
        helper=helper,
        light=light,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause '{params.cause}'.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light '{params.light}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if (params.place, params.cause) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.cause))

    world = tell(
        place=PLACES[params.place],
        cause=CAUSES[params.cause],
        light=LIGHTS[params.light],
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper,
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
        print(asp_program(show="#show valid/2.\n#show ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause) combos:\n")
        for place_id, cause_id in combos:
            print(f"  {place_id:8} {cause_id:12} -> {asp_ending(cause_id)}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} & {p.friend_name}: {p.cause} at {p.place} ({ending_of(p.cause)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
