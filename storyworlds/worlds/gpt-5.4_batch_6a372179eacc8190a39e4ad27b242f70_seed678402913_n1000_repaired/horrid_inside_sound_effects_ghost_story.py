#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/horrid_inside_sound_effects_ghost_story.py
=====================================================================

A standalone story world for a child-facing ghost-story-shaped tale with sound
effects: a child hears a horrid sound from inside some dark place, imagines a
ghost, and then a calm helper investigates and reveals the real cause.

The simulation keeps a small physical world (doors, windows, curtains, pets,
branches, loose shutters) and emotional state (fear, relief, courage,
embarrassment, comfort). The prose is driven by that state instead of swapping
nouns into one fixed paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/horrid_inside_sound_effects_ghost_story.py
    python storyworlds/worlds/gpt-5.4/horrid_inside_sound_effects_ghost_story.py --place attic --cause branch
    python storyworlds/worlds/gpt-5.4/horrid_inside_sound_effects_ghost_story.py --place cupboard --cause branch
    python storyworlds/worlds/gpt-5.4/horrid_inside_sound_effects_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/horrid_inside_sound_effects_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/horrid_inside_sound_effects_ghost_story.py --verify
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
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    openable: bool = False
    lit: bool = False
    # Shared numeric axes.
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
    phrase: str
    house_part: str
    spooky_line: str
    hiding_spot: str
    affordances: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    sound: str
    sound_word: str
    clue: str
    reveal: str
    fix: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    hold_line: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise_fright(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    child = world.get("child")
    mystery = world.get("mystery")
    if room.meters["noise"] >= THRESHOLD and mystery.meters["hidden"] >= THRESHOLD:
        sig = ("noise_fright",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            child.memes["imagination"] += 1
            out.append("__fright__")
    return out


def _r_light_calms(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    light = world.get("light")
    if light.lit and child.memes["fear"] >= THRESHOLD:
        sig = ("light_calms",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
            child.memes["courage"] += 1
            out.append("__calm__")
    return out


def _r_reveal_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    mystery = world.get("mystery")
    if mystery.meters["revealed"] >= THRESHOLD:
        sig = ("reveal_relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 2
            child.memes["fear"] = 0.0
            child.memes["embarrassed"] += 1
            helper.memes["care"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_fright", tag="emotional", apply=_r_noise_fright),
    Rule(name="light_calms", tag="emotional", apply=_r_light_calms),
    Rule(name="reveal_relief", tag="emotional", apply=_r_reveal_relief),
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
        for s in produced:
            world.say(s)
    return produced


def valid_cause(place: Place, cause: Cause) -> bool:
    return cause.needs.issubset(place.affordances)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for cause_id, cause in CAUSES.items():
            if valid_cause(place, cause):
                combos.append((place_id, cause_id))
    return combos


def predict_spook(world: World, cause: Cause) -> dict:
    sim = world.copy()
    mystery = sim.get("mystery")
    room = sim.get("room")
    mystery.meters["hidden"] += 1
    room.meters["noise"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "imagines_ghost": child.memes["imagination"] >= THRESHOLD,
        "sound": cause.sound,
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    trait = child.traits[0] if child.traits else "small"
    world.say(
        f"On a windy evening, {child.id} was a {trait} little {child.type} staying in "
        f"{place.phrase} with {child.pronoun('possessive')} {helper.label_word}."
    )
    world.say(
        f"The house was quiet in the way old houses sometimes are, and {place.spooky_line}."
    )


def settle_in(world: World, child: Entity, comfort: Comfort, place: Place) -> None:
    child.memes["cozy"] += 1
    world.say(
        f"{child.id} sat near {place.house_part} with {comfort.phrase}. "
        f"{comfort.hold_line}"
    )


def first_sound(world: World, child: Entity, cause: Cause) -> None:
    room = world.get("room")
    mystery = world.get("mystery")
    room.meters["noise"] += 1
    mystery.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from inside {world.place.hiding_spot}, came a horrid sound: "
        f'"{cause.sound}"'
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id}'s shoulders jumped, and all at once the dark corners felt bigger."
        )


def imagine_ghost(world: World, child: Entity, cause: Cause) -> None:
    pred = predict_spook(world, cause)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'"Did you hear that?" {child.id} whispered. "It sounds like a ghost is hiding inside."'
    )
    if pred["imagines_ghost"]:
        world.say(
            f"In {child.pronoun('possessive')} head, the sound grew into chains, claws, and a floating white face."
        )


def helper_listens(world: World, helper: Entity, child: Entity, cause: Cause) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} did not laugh. {helper.pronoun().capitalize()} listened for a moment and said, '
        f'"I heard it too. Let us look before we decide it is a ghost."'
    )
    world.say(
        f"{helper.pronoun().capitalize()} tipped {helper.pronoun('possessive')} head and noticed {cause.clue}."
    )


def light_on(world: World, helper: Entity, light: Light) -> None:
    light_ent = world.get("light")
    light_ent.lit = True
    light_ent.meters["glow"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} clicked on {light.phrase}. {light.shine}"
    )


def approach(world: World, child: Entity, helper: Entity, comfort: Comfort) -> None:
    child.memes["courage"] += 1
    world.say(
        f"{child.id} stayed close and held {comfort.label} tight while they walked toward {world.place.hiding_spot}."
    )


def reveal(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    mystery = world.get("mystery")
    room = world.get("room")
    mystery.meters["revealed"] += 1
    mystery.meters["hidden"] = 0.0
    room.meters["noise"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"When {helper.label_word} opened it, there was no ghost at all. {cause.reveal}"
    )


def fix_problem(world: World, helper: Entity, cause: Cause) -> None:
    world.say(
        f"{helper.label_word.capitalize()} {cause.fix}."
    )


def resolve(world: World, child: Entity, helper: Entity, comfort: Comfort, place: Place) -> None:
    child.memes["safe"] += 1
    world.say(
        f'{child.id} let out a long breath and gave a tiny laugh. "It was only that?" {child.pronoun()} said.'
    )
    if child.memes["embarrassed"] >= THRESHOLD:
        world.say(
            f'{helper.label_word.capitalize()} squeezed {child.pronoun("possessive")} hand. "Scary sounds can feel bigger in the dark," '
            f'{helper.pronoun()} said.'
        )
    world.say(
        f"Soon {place.house_part} sounded ordinary again. {child.id} tucked {comfort.label} under one arm, and the house no longer felt full of ghosts."
    )


def tell(
    *,
    place: Place,
    cause: Cause,
    light: Light,
    comfort: Comfort,
    child_name: str,
    child_gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
        phrase=place.phrase,
    ))
    mystery = world.add(Entity(
        id="mystery",
        type="mystery",
        label="the hidden noise",
        phrase="the hidden noise",
        openable=True,
    ))
    light_ent = world.add(Entity(
        id="light",
        type="light",
        label=light.label,
        phrase=light.phrase,
        lit=False,
    ))
    comfort_ent = world.add(Entity(
        id="comfort",
        type="comfort",
        label=comfort.label,
        phrase=comfort.phrase,
        movable=True,
    ))
    world.facts["sound_effect"] = cause.sound

    introduce(world, child, helper, place)
    settle_in(world, child, comfort, place)

    world.para()
    first_sound(world, child, cause)
    imagine_ghost(world, child, cause)
    helper_listens(world, helper, child, cause)

    world.para()
    light_on(world, helper, light)
    approach(world, child, helper, comfort)
    reveal(world, child, helper, cause)
    fix_problem(world, helper, cause)

    world.para()
    resolve(world, child, helper, comfort, place)

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        cause=cause,
        light=light,
        comfort=comfort,
        room=room,
        mystery=mystery,
        ghost_real=False,
        fear_happened=child.memes["relief"] >= THRESHOLD,
        settled=child.memes["safe"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the creaky attic room",
        house_part="the attic stairs",
        spooky_line="the rafters made long shadows like bent fingers on the wall",
        hiding_spot="the little attic door",
        affordances={"window", "branch", "box", "pet"},
        tags={"attic", "house"},
    ),
    "cupboard": Place(
        id="cupboard",
        label="cupboard",
        phrase="the narrow hall outside a deep cupboard",
        house_part="the hall rug",
        spooky_line="the cupboard door stood at the end like a dark little mouth",
        hiding_spot="the tall cupboard",
        affordances={"door", "box", "pet"},
        tags={"cupboard", "house"},
    ),
    "bedroom": Place(
        id="bedroom",
        label="bedroom",
        phrase="the old bedroom under the eaves",
        house_part="the bed",
        spooky_line="the curtains puffed and sank with every sigh of wind",
        hiding_spot="the curtained window seat",
        affordances={"window", "branch", "toy", "pet"},
        tags={"bedroom", "house"},
    ),
    "parlor": Place(
        id="parlor",
        label="parlor",
        phrase="the lamp-lit parlor beside the front window",
        house_part="the sofa",
        spooky_line="the grandfather clock ticked as if it were keeping a secret",
        hiding_spot="the heavy curtain",
        affordances={"window", "branch", "clock", "pet"},
        tags={"parlor", "house"},
    ),
}

CAUSES = {
    "branch": Cause(
        id="branch",
        label="branch",
        phrase="a branch tapping glass",
        sound="Tap-tap... skrrratch!",
        sound_word="tap",
        clue="a trembling shadow waving across the wall",
        reveal="A thin tree branch was scraping the window and tapping the glass whenever the wind pushed it.",
        fix="drew the curtain back and nudged the branch away from the pane",
        needs={"window", "branch"},
        tags={"wind", "window", "branch"},
    ),
    "loose_shutter": Cause(
        id="loose_shutter",
        label="loose shutter",
        phrase="a loose shutter",
        sound="Bang... creak... bang!",
        sound_word="bang",
        clue="the wall giving a little shiver with each gust",
        reveal="A loose shutter outside was flapping and knocking against the house.",
        fix="latched the shutter tight so it could not flap anymore",
        needs={"window"},
        tags={"wind", "window", "shutter"},
    ),
    "kitten": Cause(
        id="kitten",
        label="kitten",
        phrase="a stray kitten",
        sound="Mrrrow? Scritch-scritch!",
        sound_word="mrrrow",
        clue="a soft little shadow moving low near the floor",
        reveal="A small kitten had wandered in and was batting at a paper bag with both paws.",
        fix="lifted the kitten gently out and set down a saucer of milk in the kitchen",
        needs={"pet"},
        tags={"cat", "pet"},
    ),
    "hat_box": Cause(
        id="hat_box",
        label="hat box",
        phrase="a wobbling hat box",
        sound="Bump! Rustle-rustle!",
        sound_word="bump",
        clue="dust shaking down from a high shelf",
        reveal="An old hat box had tipped sideways, and tissue paper inside kept sliding and rustling.",
        fix="set the hat box straight and tucked the tissue paper back inside",
        needs={"box"},
        tags={"box", "paper"},
    ),
    "toy_mouse": Cause(
        id="toy_mouse",
        label="wind-up toy",
        phrase="a wind-up toy mouse",
        sound="Whirr... click-click!",
        sound_word="whirr",
        clue="a tiny silver key glinting near the baseboard",
        reveal="A forgotten toy mouse was still half-wound and jittering every time it bumped the wall.",
        fix="picked up the toy mouse and turned its key until the spring went still",
        needs={"toy"},
        tags={"toy", "spring"},
    ),
    "clock_chime": Cause(
        id="clock_chime",
        label="clock",
        phrase="an old clock",
        sound="Dong... creeeak...",
        sound_word="dong",
        clue="the long shadow of the pendulum swaying on the carpet",
        reveal="The old clock had given an unexpected chime, and its wooden case answered with a sleepy creak.",
        fix="opened the clock door, steadied the pendulum, and smiled at the harmless noise",
        needs={"clock"},
        tags={"clock", "wood"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        shine="A clean yellow circle jumped onto the floorboards and chased the worst shadows away.",
        tags={"flashlight", "light"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a little camping lantern",
        shine="Its warm glow made the dark corners look smaller and kinder.",
        tags={"lantern", "light"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="night-light",
        phrase="a blue night-light",
        shine="Soft blue light spread over the room like a careful whisper.",
        tags={"nightlight", "light"},
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="the fuzzy blanket",
        phrase="a fuzzy blanket around the knees",
        hold_line="The blanket felt warm enough to make even the storm outside seem far away.",
        tags={"blanket", "comfort"},
    ),
    "bear": Comfort(
        id="bear",
        label="the stuffed bear",
        phrase="a stuffed bear with one shiny button eye",
        hold_line="Its soft fur was a good thing to squeeze whenever the house gave a creak.",
        tags={"bear", "comfort"},
    ),
    "pillow": Comfort(
        id="pillow",
        label="the little pillow",
        phrase="a little pillow hugged close",
        hold_line="It smelled faintly of soap and made the room feel more like bedtime than mystery.",
        tags={"pillow", "comfort"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ella", "Ruby", "Anna", "Clara", "Zoe"]
BOY_NAMES = ["Owen", "Max", "Theo", "Ben", "Sam", "Eli", "Leo", "Finn"]
TRAITS = ["sleepy", "curious", "shivery", "brave", "small"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    cause: str
    light: str
    comfort: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost_story": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky story meant to give you a shiver. It often begins with a strange sound or shadow before the mystery is explained."
        )
    ],
    "window": [
        (
            "Why can a branch make noises on a window?",
            "When the wind blows, a branch can tap and scrape the glass. In the dark, that can sound much bigger and stranger than it really is."
        )
    ],
    "shutter": [
        (
            "What does a loose shutter sound like?",
            "A loose shutter can bang and creak when the wind hits it. The wood moves and knocks against the house."
        )
    ],
    "pet": [
        (
            "Why do small animals sound louder at night?",
            "At night the house is quieter, so little scratches and mews stand out more. Your ears notice them because there are fewer other sounds around."
        )
    ],
    "box": [
        (
            "Why does paper rustle?",
            "Paper rustles when it rubs and folds against itself. In a still room, that soft sound can seem mysterious."
        )
    ],
    "toy": [
        (
            "How can a wind-up toy make noise by itself?",
            "A wind-up toy stores energy in a spring. Until the spring unwinds, it can whirr, click, and bump around on its own."
        )
    ],
    "clock": [
        (
            "Why do old clocks creak?",
            "Old wooden clocks can creak when their parts move. A chime or swinging pendulum can make the case answer with little sounds."
        )
    ],
    "light": [
        (
            "Why does light make scary things feel less scary?",
            "Light helps you see what is really there. Once your eyes can see clearly, your mind does not have to guess as much."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost_story", "window", "shutter", "pet", "box", "toy", "clock", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    cause = f["cause"]
    helper = f["helper"]
    return [
        f'Write a short ghost story for a 3-to-5-year-old that includes the words "horrid" and "inside" and uses sound effects like "{cause.sound}".',
        f"Tell a spooky-but-safe story where a child named {child.id} hears a strange noise inside {place.hiding_spot} and thinks it might be a ghost until {helper.label_word} helps investigate.",
        f"Write a gentle mystery in an old house where a dark sound seems scary at first, but the ending reveals an ordinary cause and leaves the child feeling safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    cause = f["cause"]
    light = f["light"]
    comfort = f["comfort"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {child.pronoun('possessive')} {helper.label_word}. They are together in {place.phrase} when the mystery begins."
        ),
        (
            "What made the story feel spooky at first?",
            f"The spooky feeling began when a horrid sound came from inside {place.hiding_spot}: {cause.sound} The dark room and the hidden noise made {child.id} imagine a ghost before anyone knew the real cause."
        ),
        (
            f"Why did {child.id} think there might be a ghost?",
            f"{child.id} could hear the sound but could not see what was making it. When scary noises stay hidden in the dark, a child's imagination can turn them into ghosts and monsters."
        ),
        (
            f"How did {helper.label_word} help?",
            f"{helper.label_word.capitalize()} stayed calm, listened for clues, and turned on {light.phrase}. Then {helper.pronoun()} walked over with {child.id} to look at the place where the sound was coming from."
        ),
        (
            "What was really making the noise?",
            f"It was not a ghost at all. {cause.reveal}"
        ),
        (
            "How did the story end?",
            f"{helper.label_word.capitalize()} fixed the problem, and the room sounded ordinary again. {child.id} still held {comfort.label}, but now it was for coziness instead of fear."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost_story", "light"}
    cause_id = world.facts["cause"].id
    if cause_id == "branch":
        tags.add("window")
    elif cause_id == "loose_shutter":
        tags.add("shutter")
    elif cause_id == "kitten":
        tags.add("pet")
    elif cause_id == "hat_box":
        tags.add("box")
    elif cause_id == "toy_mouse":
        tags.add("toy")
    elif cause_id == "clock_chime":
        tags.add("clock")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.openable:
            bits.append("openable=True")
        if ent.lit:
            bits.append("lit=True")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        cause="branch",
        light="lantern",
        comfort="bear",
        child_name="Lila",
        child_gender="girl",
        helper_type="grandmother",
        trait="shivery",
    ),
    StoryParams(
        place="cupboard",
        cause="hat_box",
        light="flashlight",
        comfort="blanket",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        trait="curious",
    ),
    StoryParams(
        place="bedroom",
        cause="toy_mouse",
        light="nightlight",
        comfort="pillow",
        child_name="Nora",
        child_gender="girl",
        helper_type="mother",
        trait="sleepy",
    ),
    StoryParams(
        place="parlor",
        cause="clock_chime",
        light="lantern",
        comfort="bear",
        child_name="Owen",
        child_gender="boy",
        helper_type="grandfather",
        trait="brave",
    ),
    StoryParams(
        place="bedroom",
        cause="kitten",
        light="flashlight",
        comfort="blanket",
        child_name="Ruby",
        child_gender="girl",
        helper_type="mother",
        trait="small",
    ),
]


def explain_rejection(place: Place, cause: Cause) -> str:
    need_words = ", ".join(sorted(cause.needs))
    has_words = ", ".join(sorted(place.affordances))
    return (
        f"(No story: {cause.label} needs a place with {need_words}, but {place.label} only has {has_words}. "
        f"The noise would not make sense there, so this ghost-story setup is refused.)"
    )


ASP_RULES = r"""
valid(P, C) :- place(P), cause(C), cause_need_count(C, N), met_need_count(P, C, N).
met_need_count(P, C, N) :- N = #count { Need : needs(C, Need), affords(P, Need) }.

% Every generated story in this world resolves as "explained" because the child
% investigates with a helper and the hidden cause is revealed.
outcome(explained) :- chosen_place(_), chosen_cause(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for need in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, need))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for need in sorted(cause.needs):
            lines.append(asp.fact("needs", cause_id, need))
        lines.append(asp.fact("cause_need_count", cause_id, len(cause.needs)))
    for light_id in LIGHTS:
        lines.append(asp.fact("light", light_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_cause", params.cause),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    smoke_cases = list(CURATED)
    try:
        parsed = build_parser().parse_args([])
        sample_params = resolve_params(parsed, random.Random(123))
        smoke_cases.append(sample_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAILURE: resolve_params() raised {err}")

    for params in smoke_cases:
        try:
            params.seed = params.seed if params.seed is not None else 999
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "horrid" not in sample.story or "inside" not in sample.story:
                raise StoryError("required seed words missing from story")
            if asp_outcome(params) != "explained":
                raise StoryError("ASP outcome mismatch")
        except Exception as err:  # pragma: no cover - defensive verify path
            rc = 1
            print(f"SMOKE FAILURE for {params}: {err}")
            break

    if rc == 0:
        print(f"OK: generated {len(smoke_cases)} smoke-test stories without crashing.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a horrid sound inside and thinks it is a ghost until a calm helper reveals the real cause."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible place/cause set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if not valid_cause(place, cause):
            raise StoryError(explain_rejection(place, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cause_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    light_id = args.light or rng.choice(sorted(LIGHTS))
    comfort_id = args.comfort or rng.choice(sorted(COMFORTS))
    helper_type = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        cause=cause_id,
        light=light_id,
        comfort=comfort_id,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort item: {params.comfort})")
    if not valid_cause(PLACES[params.place], CAUSES[params.cause]):
        raise StoryError(explain_rejection(PLACES[params.place], CAUSES[params.cause]))

    world = tell(
        place=PLACES[params.place],
        cause=CAUSES[params.cause],
        light=LIGHTS[params.light],
        comfort=COMFORTS[params.comfort],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause) combos:\n")
        for place, cause in combos:
            print(f"  {place:10} {cause}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.cause} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
