#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rigorous_humor_bedtime_story.py
==========================================================

A standalone story world for a funny bedtime tale about a child who notices
something odd in a dark room, worries for a moment, and then helps a grown-up
carry out a *rigorous* little bedtime check. The joke is that the "monster"
always turns out to be something ordinary and slightly silly: a coat rack in a
hat, a heap of laundry on a chair, a curtain wagging in a breeze, or a toy that
forgot to stay quiet.

The model is intentionally small and classical:

- typed entities with physical meters and emotional memes
- a tiny forward-chaining rule system
- an explicit reasonableness gate for which checking methods fit which causes
- an inline ASP twin for parity checking
- prose rendered from simulated state, not from a frozen template

Run it
------
    python storyworlds/worlds/gpt-5.4/rigorous_humor_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/rigorous_humor_bedtime_story.py --cause curtain_breeze --method lamp_scan
    python storyworlds/worlds/gpt-5.4/rigorous_humor_bedtime_story.py --cause laundry_chair --method lamp_scan
    python storyworlds/worlds/gpt-5.4/rigorous_humor_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/rigorous_humor_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rigorous_humor_bedtime_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from a nested world directory such as storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    casts_shadow: bool = False
    rustles: bool = False
    beeps: bool = False
    movable: bool = False
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


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    room: str
    moon: str
    bed: str
    ending: str


@dataclass
class Cause:
    id: str
    category: str
    sign: str
    source_label: str
    source_phrase: str
    clue: str
    silly_guess: str
    reveal: str
    fix: str
    qa_fix: str
    shadow: int = 0
    rustle: int = 0
    beep: int = 0
    movable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    sense: int
    covers: set[str]
    title: str
    phrase: str
    action: str
    follow: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_notice_shadow(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    source = world.get("source")
    if source.meters["shadow"] < THRESHOLD or room.meters["dark"] < THRESHOLD:
        return []
    sig = ("worry_shadow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    room.meters["mystery"] += 1
    return []


def _r_notice_sound(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    source = world.get("source")
    if source.meters["rustle"] < THRESHOLD and source.meters["beep"] < THRESHOLD:
        return []
    sig = ("worry_sound",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    room.meters["mystery"] += 1
    return []


def _r_relief_after_fix(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    source = world.get("source")
    if source.meters["fixed"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["giggles"] += 1
    child.memes["sleepy"] += 1
    child.memes["worry"] = 0.0
    room.meters["mystery"] = 0.0
    room.meters["calm"] += 1
    return []


CAUSAL_RULES = [
    Rule("notice_shadow", "physical", _r_notice_shadow),
    Rule("notice_sound", "physical", _r_notice_sound),
    Rule("relief_after_fix", "social", _r_relief_after_fix),
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
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def cause_signals(cause: Cause) -> set[str]:
    out: set[str] = set()
    if cause.category:
        out.add(cause.category)
    if cause.shadow:
        out.add("shadow")
    if cause.rustle:
        out.add("breeze")
    if cause.beep:
        out.add("sound")
    return out


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_fits(method: Method, cause: Cause) -> bool:
    return method.sense >= SENSE_MIN and bool(method.covers & cause_signals(cause))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for cause_id, cause in CAUSES.items():
            for method_id, method in METHODS.items():
                if method_fits(method, cause):
                    combos.append((setting_id, cause_id, method_id))
    return combos


def explain_rejection(cause: Cause, method: Method) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it is too silly to count as a sensible "
            f"bedtime check here. Try one of: {better}.)"
        )
    needed = ", ".join(sorted(cause_signals(cause)))
    covered = ", ".join(sorted(method.covers))
    return (
        f"(No story: {method.title} checks [{covered}], but {cause.source_label} is a "
        f"[{needed}] kind of bedtime mystery. Pick a method that can honestly reveal it.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_worry(world: World, cause: Cause) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["shadow"] += cause.shadow
    source.meters["rustle"] += cause.rustle
    source.meters["beep"] += cause.beep
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "worried": child.memes["worry"] >= THRESHOLD,
        "mystery": sim.get("room").meters["mystery"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def bedtime_setup(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    room = world.get("room")
    room.meters["dark"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f"In {world.setting.room}, {child.id} was tucked into {world.setting.bed}, "
        f"with {comfort.phrase} nearby. {world.setting.moon}"
    )
    world.say(
        f"{child.id}'s {parent.label_word} had already kissed {child.pronoun('object')} good night "
        f"and was halfway to the door."
    )


def clue_appears(world: World, child: Entity, cause: Cause) -> None:
    source = world.get("source")
    source.meters["shadow"] += cause.shadow
    source.meters["rustle"] += cause.rustle
    source.meters["beep"] += cause.beep
    propagate(world, narrate=False)
    world.say(cause.clue)
    world.say(
        f'"Oh," whispered {child.id}, "what if it is {cause.silly_guess}?"'
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"The room felt one pinch more mysterious, which is what shadows and odd little sounds do at bedtime."
        )


def parent_returns(world: World, child: Entity, parent: Entity, cause: Cause) -> None:
    pred = predict_worry(world, cause)
    world.facts["predicted_mystery"] = pred["mystery"]
    child.memes["trust"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came back at once and sat on the edge of the bed."
    )
    world.say(
        f'"Then we will do a rigorous little bedtime check," {parent.pronoun()} said. '
        f'"Not a noisy one. Not a bonky one. A proper one."'
    )


def child_reacts(world: World, child: Entity) -> None:
    child.memes["courage"] += 1
    world.say(
        f'{child.id} peeked over the blanket. "Can a proper one be quick?" {child.pronoun()} asked.'
    )
    world.say(
        '"Quick, quiet, and very serious," came the answer, which sounded so serious that it was almost funny.'
    )


def inspect(world: World, child: Entity, parent: Entity, method: Method, cause: Cause) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Together they began {method.phrase}. {parent.label_word.capitalize()} {method.action}."
    )
    world.say(method.follow)
    world.say(cause.reveal)


def fix_source(world: World, parent: Entity, cause: Cause) -> None:
    source = world.get("source")
    source.meters["fixed"] += 1
    source.meters["shadow"] = 0.0
    source.meters["rustle"] = 0.0
    source.meters["beep"] = 0.0
    propagate(world, narrate=False)
    world.say(cause.fix)
    world.say(
        f'"There," said {parent.label_word}. "The mystery was only being busy, not being scary."'
    )


def bedtime_end(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    if child.memes["giggles"] >= THRESHOLD:
        world.say(
            f"{child.id} let out a small laugh that sounded much braver than the earlier whisper."
        )
    world.say(
        f"Soon the room looked ordinary again, which at bedtime is one of the nicest sights in the world."
    )
    world.say(
        f"{child.id} snuggled close to {comfort.phrase} and {comfort.ending}."
    )
    world.say(
        f"{world.setting.ending} Even the shadows seemed ready to sleep."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, cause: Cause, method: Method, comfort: Comfort,
         child_name: str = "Nora", child_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label=setting.room))
    source = world.add(Entity(
        id="source",
        type="source",
        label=cause.source_label,
        casts_shadow=bool(cause.shadow),
        rustles=bool(cause.rustle),
        beeps=bool(cause.beep),
        movable=cause.movable,
    ))

    bedtime_setup(world, child, parent, comfort)
    world.para()
    clue_appears(world, child, cause)
    parent_returns(world, child, parent, cause)
    child_reacts(world, child)
    world.para()
    inspect(world, child, parent, method, cause)
    fix_source(world, parent, cause)
    world.para()
    bedtime_end(world, child, parent, comfort)

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        source=source,
        setting=setting,
        cause=cause,
        method=method,
        comfort=comfort,
        resolved=source.meters["fixed"] >= THRESHOLD,
        worried=child.memes["relief"] >= THRESHOLD or world.facts.get("predicted_mystery", 0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "moon_room": Setting(
        "moon_room",
        "a small moonlit bedroom",
        "Moonlight lay across the rug in a pale silver stripe.",
        "a soft bed with a quilt tucked under the chin",
        "Before long, slow bedtime breaths filled the room.",
    ),
    "bunk_nook": Setting(
        "bunk_nook",
        "a cozy bunk nook",
        "A sleepy moon shone through the window and climbed the ladder in stripes.",
        "the lower bunk with pillows like little clouds",
        "Soon the bunk nook was quiet except for the soft sound of breathing.",
    ),
    "star_room": Setting(
        "star_room",
        "a room with star stickers on the ceiling",
        "The ceiling stars were dim now, and the real stars blinked outside.",
        "a warm bed that smelled faintly of soap and blankets",
        "At last the room settled into its peaceful nighttime hush.",
    ),
}

CAUSES = {
    "rack_shadow": Cause(
        "rack_shadow",
        "shadow",
        "a tall shadow",
        "the coat rack",
        "a coat rack wearing a floppy hat",
        "A tall shape stretched across the wall, long as a giraffe and much less polite.",
        "a very thin night giant wearing three jackets and one hat",
        "When the lamp came on, the terrible shape turned into the coat rack, with a scarf drooping from one arm and a hat tilted on top as if it were trying to look important.",
        "Dad lifted the hat from the coat rack and hung the scarf properly. At once the shadow shrank from giant size to ordinary coat-rack size.",
        "moved the hat and scarf so the coat rack stopped making a giant shadow",
        shadow=1,
        movable=True,
        tags={"shadow", "coat_rack"},
    ),
    "laundry_chair": Cause(
        "laundry_chair",
        "pile",
        "a lumpy shape",
        "the laundry chair",
        "a chair with pajamas and socks slumped over it",
        "Near the chair sat a roundish lump with two sleeves sticking out, as if a sleepy potato had borrowed clothes.",
        "a potato professor who had come to give a strict lecture on bedtime",
        "Under the light, the alarming lump became a chair full of pajamas, socks, and one shirt hanging sideways in a very suspicious way.",
        "Mom folded the laundry into a neat pile and set the chair free again. Without the heap, there was nothing left to look potato-shaped at all.",
        "folded the laundry so the chair no longer looked like a creature",
        shadow=1,
        movable=True,
        tags={"laundry", "shadow"},
    ),
    "curtain_breeze": Cause(
        "curtain_breeze",
        "breeze",
        "a wiggly curtain",
        "the curtain",
        "the curtain by the cracked window",
        "The curtain gave a soft flap-flap and waved at the room as if it had an opinion.",
        "a polite ghost practicing napkin dances",
        "The mystery turned out to be the curtain puffing in and out because the window was open just a crack.",
        "Parent clicked the window shut and tucked the curtain back into place. The waving stopped, and so did the ghostly performance.",
        "shut the window and settled the curtain so it stopped waving",
        rustle=1,
        shadow=1,
        movable=False,
        tags={"curtain", "wind", "shadow"},
    ),
    "toy_beep": Cause(
        "toy_beep",
        "sound",
        "a tiny beep",
        "the toy submarine",
        "a toy submarine under the dresser",
        "From somewhere near the floor came a tiny beep ... then another one, very proud of itself.",
        "a baby robot teaching the furniture to sing",
        "They found the toy submarine under the dresser, blinking because its button had been pressed earlier and it was not at all finished with itself.",
        "Parent switched the toy submarine off and parked it on the shelf for tomorrow. The room grew quiet enough to hear only blankets rustle.",
        "switched off the toy submarine so it stopped beeping",
        beep=1,
        movable=True,
        tags={"sound", "toy"},
    ),
}

METHODS = {
    "lamp_scan": Method(
        "lamp_scan",
        3,
        {"shadow", "breeze"},
        "lamp scan",
        "a rigorous little lamp scan",
        "clicked on the bedside lamp and looked slowly from wall to chair to window",
        "They did not pounce on anything. They simply looked carefully, which is less dramatic and much more useful.",
        "used the lamp to look carefully around the room",
        tags={"lamp", "checklist"},
    ),
    "tidy_check": Method(
        "tidy_check",
        3,
        {"pile", "shadow", "sound"},
        "tidy check",
        "a rigorous tidy-and-peek check",
        "picked up the stray socks, peered behind the chair, and checked the floor one calm corner at a time",
        "The check was so neat that even the dust motes seemed to line up politely and wait their turn.",
        "tidied the room a little while checking each corner calmly",
        tags={"tidy", "checklist"},
    ),
    "listen_peek": Method(
        "listen_peek",
        2,
        {"sound", "breeze"},
        "listen and peek",
        "a rigorous listen-and-peek",
        "stood still for one breath, listened, then followed the sound with careful little peeks",
        "When nobody is shouting, small noises tell on themselves very quickly.",
        "stood still, listened carefully, and followed the little sound",
        tags={"listen", "checklist"},
    ),
    "pot_hat_plan": Method(
        "pot_hat_plan",
        1,
        {"nothing"},
        "pot-on-head plan",
        "the pot-on-head plan",
        "balanced a soup pot on somebody's head",
        "It would have made a grand clang and exactly zero sense.",
        "put a pot on somebody's head",
        tags={"silly"},
    ),
}

COMFORTS = {
    "rabbit": Comfort("rabbit", "a floppy rabbit", "pulled the floppy rabbit under one arm", tags={"toy_comfort"}),
    "blanket": Comfort("blanket", "the corner of a favorite blanket", "rubbed the blanket corner and let the mattress feel soft underneath", tags={"blanket"}),
    "owl": Comfort("owl", "a stuffed owl", "nestled the stuffed owl under the chin like a watchful friend", tags={"toy_comfort"}),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe", "Rose", "Lucy"]
BOY_NAMES = ["Ben", "Theo", "Max", "Leo", "Sam", "Finn", "Eli", "Noah"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    cause: str
    method: str
    comfort: str
    child: str
    gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "shadow": [(
        "Why can shadows look different at night?",
        "At night, a small lamp or moonlight can stretch a shadow across the wall. That can make ordinary things look much bigger or stranger than they really are."
    )],
    "coat_rack": [(
        "Why can a coat rack look spooky in the dark?",
        "A coat rack can hold hats, scarves, and coats in odd shapes. In dim light, all those shapes can join into one silly-looking shadow."
    )],
    "laundry": [(
        "Why can a pile of laundry look like something else?",
        "Clothes can slump into bumps and sleeves and funny corners. In the dark, your eyes may guess wrong before the light shows what it really is."
    )],
    "curtain": [(
        "Why does a curtain move when a window is open?",
        "Air from the open window pushes the curtain and makes it flap or wave. The curtain is only moving because the breeze is moving it."
    )],
    "wind": [(
        "What is a breeze?",
        "A breeze is a gentle little wind. It can move curtains, leaves, and light things without being strong or scary."
    )],
    "sound": [(
        "Why do small sounds seem louder at bedtime?",
        "When a room gets quiet, tiny beeps and rustles stand out more. Your ears notice them because there is less other noise around."
    )],
    "lamp": [(
        "How can a lamp help with a bedtime worry?",
        "A lamp adds steady light so you can see what is really in the room. Good light often turns a scary guess into an ordinary answer."
    )],
    "tidy": [(
        "Why can tidying a room help at bedtime?",
        "Tidying removes lumpy piles and hidden toys that can make strange shapes or noises. A calmer room is easier to understand when the lights are low."
    )],
    "listen": [(
        "Why is listening quietly useful when you hear a tiny noise?",
        "If you stay still and listen, you can tell where the sound is coming from. Quiet listening is a careful way to solve a little mystery."
    )],
    "checklist": [(
        "What does rigorous mean?",
        "Rigorous means careful, thorough, and done step by step. In the story, the bedtime check was rigorous because the parent looked or listened properly instead of guessing wildly."
    )],
    "toy": [(
        "Why should noisy toys be put away before bed?",
        "A toy that beeps or flashes can wake you up or make you wonder what the sound is. Putting it away helps the room stay quiet for sleep."
    )],
    "blanket": [(
        "Why do blankets feel comforting at bedtime?",
        "A blanket feels soft and warm, and that can help your body relax. Cozy things often make it easier to settle down and sleep."
    )],
    "toy_comfort": [(
        "Why do some children sleep with a stuffed toy?",
        "A stuffed toy can feel familiar and safe at bedtime. Holding something soft can make the room feel friendlier."
    )],
}
KNOWLEDGE_ORDER = [
    "checklist", "shadow", "coat_rack", "laundry", "curtain", "wind",
    "sound", "lamp", "tidy", "listen", "toy", "blanket", "toy_comfort"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cause = f["cause"]
    return [
        'Write a funny bedtime story for a 3-to-5-year-old that includes the word "rigorous".',
        f"Tell a gentle bedtime story where {child.id} notices {cause.sign} in the dark, imagines something silly, and a calm grown-up solves the mystery step by step.",
        "Write a child-facing story with a bedtime worry, a humorous turn, and a cozy ending where the room feels safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cause = f["cause"]
    method = f["method"]
    comfort = f["comfort"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} at bedtime and {child.pronoun('possessive')} {pw}, who comes back to help. The story follows a small nighttime worry that turns into a funny, ordinary answer."
        ),
        (
            f"What worried {child.id} at first?",
            f"{child.id} noticed {cause.sign} and imagined it might be {cause.silly_guess}. In the dark, the clue felt mysterious before anyone checked it properly."
        ),
        (
            f"What did {child.id}'s {pw} do?",
            f"{pw.capitalize()} did {method.qa_text}. The check was rigorous because it happened calmly and step by step instead of turning into a wild guessing game."
        ),
        (
            "What was the mystery really?",
            f"It was {cause.source_phrase}. Once the room was checked carefully, the spooky idea disappeared and the real cause looked ordinary."
        ),
        (
            "How was the problem fixed?",
            f"{pw.capitalize()} {cause.qa_fix}. That changed the room itself, so the shadow or sound stopped instead of merely being ignored."
        ),
        (
            "How did the story end?",
            f"It ended cozily: {child.id} settled back down with {comfort.phrase}, laughed a little, and felt ready to sleep. The ending image shows that the room became calm again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["cause"].tags) | set(f["method"].tags) | set(f["comfort"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        flags = [n for n, on in (
            ("casts_shadow", e.casts_shadow),
            ("rustles", e.rustles),
            ("beeps", e.beeps),
            ("movable", e.movable),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_room", "rack_shadow", "lamp_scan", "rabbit", "Nora", "girl", "mother"),
    StoryParams("bunk_nook", "laundry_chair", "tidy_check", "owl", "Ben", "boy", "father"),
    StoryParams("star_room", "curtain_breeze", "listen_peek", "blanket", "Mia", "girl", "mother"),
    StoryParams("moon_room", "toy_beep", "tidy_check", "rabbit", "Theo", "boy", "father"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
signal(C, shadow) :- cause(C), casts_shadow(C).
signal(C, breeze) :- cause(C), rustles(C).
signal(C, sound)  :- cause(C), beeps(C).
signal(C, Cat)    :- cause_category(C, Cat).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
fits(M, C)  :- sensible(M), covers(M, Sig), signal(C, Sig).
valid(S, C, M) :- setting(S), cause(C), method(M), fits(M, C).

resolved(C, M) :- fits(M, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_category", cid, cause.category))
        if cause.shadow:
            lines.append(asp.fact("casts_shadow", cid))
        if cause.rustle:
            lines.append(asp.fact("rustles", cid))
        if cause.beep:
            lines.append(asp.fact("beeps", cid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for sig in sorted(method.covers):
            lines.append(asp.fact("covers", mid, sig))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0

    a_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if a_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(a_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_valid - p_valid:
            print("  only in clingo:", sorted(a_valid - p_valid))
        if p_valid - a_valid:
            print("  only in python:", sorted(p_valid - a_valid))

    a_sensible = set(asp_sensible())
    p_sensible = {m.id for m in sensible_methods()}
    if a_sensible == p_sensible:
        print(f"OK: sensible methods match ({sorted(a_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(a_sensible)} python={sorted(p_sensible)}")

    smoke_cases = list(CURATED)
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases.append(p)
    except StoryError as err:
        rc = 1
        print(f"SMOKE SETUP FAILED: resolve_params default raised StoryError: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise RuntimeError("empty story")
            if "rigorous" not in sample.story.lower():
                raise RuntimeError("story missing required seed word 'rigorous'")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=(i == 1), header="")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE FAILED on case {i}: {err}")
            break
    else:
        print(f"OK: smoke-tested generate()/emit() on {len(smoke_cases)} scenarios.")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Funny bedtime story world: a child notices something odd, a calm grown-up performs a rigorous check, and the room becomes cozy again."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.method:
        cause = CAUSES[args.cause]
        method = METHODS[args.method]
        if not method_fits(method, cause):
            raise StoryError(explain_rejection(cause, method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.cause is None or c[1] == args.cause)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, cause, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    return StoryParams(setting, cause, method, comfort, child, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CAUSES[params.cause],
        METHODS[params.method],
        COMFORTS[params.comfort],
        params.child,
        params.gender,
        params.parent,
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
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cause, method) combos:\n")
        for setting, cause, method in combos:
            print(f"  {setting:10} {cause:15} {method}")
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
            header = f"### {p.child}: {p.cause} with {p.method} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
