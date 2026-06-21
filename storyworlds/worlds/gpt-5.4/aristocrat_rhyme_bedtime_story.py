#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/aristocrat_rhyme_bedtime_story.py
============================================================

A standalone story world for a gentle bedtime tale with a tiny aristocrat,
a night-time worry, and a soothing fix that truly fits the problem.

The world rebuilds a simple premise in a state-driven way:

    A little aristocrat in a quiet old manor tries to sleep.
    A small night disturbance makes bedtime feel too big.
    The child first reaches for a grand but unhelpful idea.
    A calm grown-up notices the real cause and chooses a fitting bedtime remedy.
    The room settles, the child settles, and the ending lands in a soft rhyme.

Core reasonableness constraint
------------------------------
Not every bedtime remedy fits every disturbance. A closed window helps a cold
draft, but not thunder. A lullaby helps fear and restlessness, but does not stop
a curtain from snapping in the wind. This world therefore only generates stories
where the chosen remedy honestly addresses the disturbance.

Run it
------
    python storyworlds/worlds/gpt-5.4/aristocrat_rhyme_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/aristocrat_rhyme_bedtime_story.py --disturbance draft --remedy window_latch
    python storyworlds/worlds/gpt-5.4/aristocrat_rhyme_bedtime_story.py --disturbance thunder --remedy window_latch
    python storyworlds/worlds/gpt-5.4/aristocrat_rhyme_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/aristocrat_rhyme_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/aristocrat_rhyme_bedtime_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "lady", "mother", "woman", "duchess"}
        male = {"boy", "lord", "father", "man", "duke"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "nurse": "nurse"}.get(self.type, self.type)


@dataclass
class Chamber:
    id: str
    opening: str
    bed: str
    glow: str
    corridor: str
    rhyme_end: str


@dataclass
class Disturbance:
    id: str
    label: str
    cause: str
    sign: str
    sound: str
    fear_line: str
    fix_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GrandIdea:
    id: str
    phrase: str
    boast: str
    effect: str
    noisy: bool = False
    chilly: bool = False
    bright: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    action: str
    result: str
    sense: int
    fixes: set[str] = field(default_factory=set)
    power: int = 1
    tags: set[str] = field(default_factory=set)


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


def _r_disturb(world: World) -> list[str]:
    room = world.get("room")
    child = world.get("child")
    out: list[str] = []
    if room.meters["noise"] >= THRESHOLD:
        sig = ("noise_fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["unease"] += 1
            out.append("__noise__")
    if room.meters["draft"] >= THRESHOLD:
        sig = ("draft_fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["cold"] += 1
            child.memes["unease"] += 1
            out.append("__draft__")
    if room.meters["flash"] >= THRESHOLD:
        sig = ("flash_fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["unease"] += 1
            out.append("__flash__")
    return out


def _r_grand_idea(world: World) -> list[str]:
    room = world.get("room")
    child = world.get("child")
    out: list[str] = []
    if room.meters["brightness"] >= THRESHOLD:
        sig = ("bright_restless",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["restless"] += 1
            out.append("__bright__")
    if room.meters["clatter"] >= THRESHOLD:
        sig = ("clatter_restless",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["restless"] += 1
            out.append("__clatter__")
    if room.meters["chill"] >= THRESHOLD:
        sig = ("chill_cold",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["cold"] += 1
            out.append("__chill__")
    return out


def _r_sleep(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    sig = ("sleep",)
    if sig in world.fired:
        return []
    if room.meters["noise"] < THRESHOLD and room.meters["draft"] < THRESHOLD and room.meters["flash"] < THRESHOLD and child.memes["restless"] < THRESHOLD and child.memes["unease"] < THRESHOLD:
        world.fired.add(sig)
        child.meters["sleep"] += 1
        child.memes["calm"] += 1
        return ["__sleep__"]
    return []


CAUSAL_RULES = [
    Rule("disturb", "physical", _r_disturb),
    Rule("grand_idea", "physical", _r_grand_idea),
    Rule("sleep", "resolution", _r_sleep),
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


def valid_combo(disturbance: Disturbance, remedy: Remedy) -> bool:
    return disturbance.id in remedy.fixes and remedy.sense >= 2


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for did, d in DISTURBANCES.items():
        for rid, r in REMEDIES.items():
            if valid_combo(d, r):
                out.append((did, rid))
    return out


def predict_sleep(world: World, remedy: Remedy) -> dict:
    sim = world.copy()
    apply_remedy(sim, remedy, narrate=False)
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "asleep": child.meters["sleep"] >= THRESHOLD,
        "calm": child.memes["calm"],
        "unease": child.memes["unease"],
    }


def introduce(world: World, chamber: Chamber, child: Entity, caregiver: Entity) -> None:
    world.say(
        f"{chamber.opening} In the oldest tower of the manor lived {child.id}, "
        f"a very small aristocrat with a very grand blanket and a very sleepy yawn."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked soft things, silver stars on the ceiling, "
        f"and hearing {caregiver.label_word}'s footsteps grow slower as the house grew still."
    )


def bedtime_setup(world: World, chamber: Chamber, child: Entity) -> None:
    child.memes["drowsy"] += 1
    world.say(
        f"{chamber.bed} {chamber.glow} The pillows were plump, the sheets were neat, "
        f"and the whole room looked ready for little feet to stop wriggling."
    )


def disturbance_arrives(world: World, disturbance: Disturbance, chamber: Chamber) -> None:
    room = world.get("room")
    room.meters["disturbance"] += 1
    if disturbance.id == "draft":
        room.meters["draft"] += 1
        room.meters["noise"] += 1
    elif disturbance.id == "thunder":
        room.meters["noise"] += 1
        room.meters["flash"] += 1
    elif disturbance.id == "creak":
        room.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {disturbance.sign}. {disturbance.sound} {disturbance.fear_line}"
    )


def grand_try(world: World, child: Entity, idea: GrandIdea) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I am an aristocrat," whispered {child.id}, trying to sound brave. '
        f'"Perhaps {idea.boast}."'
    )
    world.say(f"{child.id} reached for {idea.phrase}.")
    room = world.get("room")
    if idea.noisy:
        room.meters["clatter"] += 1
    if idea.chilly:
        room.meters["chill"] += 1
    if idea.bright:
        room.meters["brightness"] += 1
    propagate(world, narrate=False)
    child.memes["restless"] += 1
    world.say(idea.effect)


def caregiver_notices(world: World, caregiver: Entity, child: Entity, disturbance: Disturbance, remedy: Remedy) -> None:
    pred = predict_sleep(world, remedy)
    world.facts["predicted_asleep"] = pred["asleep"]
    world.say(
        f"{caregiver.label_word.capitalize()} came back to the doorway and saw that "
        f"{child.id} was more wakeful than before."
    )
    world.say(
        f'"Little aristocrat," {caregiver.pronoun()} said softly, '
        f'"the room does not need a grander trick. It needs the right small fix."'
    )


def entity_by_role(world: World, role: str) -> Entity:
    for ent in world.entities.values():
        if ent.role == role:
            return ent
    return world.get(role)


def remedy_past_tense(remedy: Remedy, child: Entity) -> str:
    return {
        "window_latch": "latched the window and tucked the blanket",
        "lullaby": "hummed a lullaby",
        "hall_check": "checked the hall with a small lamp",
        "count_rain": f"counted raindrops with {child.id}",
        "kiss_forehead": f"gave {child.id} a kiss",
    }[remedy.id]


def apply_remedy(world: World, remedy: Remedy, narrate: bool = True) -> None:
    room = world.get("room")
    child = entity_by_role(world, "child")
    caregiver = entity_by_role(world, "caregiver")
    if "draft" in remedy.fixes:
        room.meters["draft"] = 0.0
        room.meters["noise"] = 0.0
    if "thunder" in remedy.fixes:
        room.meters["noise"] = 0.0
        room.meters["flash"] = 0.0
    if "creak" in remedy.fixes:
        room.meters["noise"] = 0.0
    room.meters["brightness"] = 0.0
    room.meters["clatter"] = 0.0
    room.meters["chill"] = 0.0
    child.memes["unease"] = 0.0
    child.memes["restless"] = 0.0
    child.meters["cold"] = 0.0
    child.memes["trust"] += 1
    propagate(world, narrate=False)
    if narrate:
        action = remedy.action.format(name=child.id).replace("Caregiver", caregiver.label_word.capitalize())
        world.say(action)
        world.say(remedy.result)


def settle_end(world: World, child: Entity, disturbance: Disturbance, chamber: Chamber) -> None:
    child.memes["calm"] += 1
    child.meters["sleep"] += 1
    rhyme = RHYMES[disturbance.id]
    world.say(
        f"Soon {child.id}'s eyes grew heavy. {rhyme[0]} {rhyme[1]}"
    )
    world.say(
        f"And in that quiet manor room, the little aristocrat drifted into sleep, "
        f"{chamber.rhyme_end}."
    )


def tell(
    chamber: Chamber,
    disturbance: Disturbance,
    idea: GrandIdea,
    remedy: Remedy,
    child_name: str = "Pearl",
    child_type: str = "girl",
    title_word: str = "Lady",
    caregiver_type: str = "mother",
    trait: str = "proud",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=title_word,
            role="child",
            traits=[trait, "little"],
        )
    )
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=caregiver_type,
            label="the caregiver",
            role="caregiver",
        )
    )
    room = world.add(Entity(id="room", type="room", label="the room"))

    introduce(world, chamber, child, caregiver)
    bedtime_setup(world, chamber, child)

    world.para()
    disturbance_arrives(world, disturbance, chamber)
    grand_try(world, child, idea)

    world.para()
    caregiver_notices(world, caregiver, child, disturbance, remedy)
    apply_remedy(world, remedy, narrate=True)
    settle_end(world, child, disturbance, chamber)

    world.facts.update(
        chamber=chamber,
        disturbance=disturbance,
        idea=idea,
        remedy=remedy,
        child=child,
        caregiver=caregiver,
        room=room,
        slept=child.meters["sleep"] >= THRESHOLD,
        title_word=title_word,
    )
    return world


CHAMBERS = {
    "tower": Chamber(
        "tower",
        "Moonlight lay in a pale square on the rug.",
        "A high canopied bed stood by the wall.",
        "A single lamp made a honey-colored glow.",
        "Beyond the door, the corridor was long and hushy.",
        "where the dark felt light and the night sat right",
    ),
    "nursery": Chamber(
        "nursery",
        "The nursery windows held a silver moon.",
        "A little carved bed rested beneath a painted ceiling.",
        "The night-light glowed like a sleepy peach.",
        "Beyond the door, the old hall listened quietly.",
        "where the hush was deep and the dreams could keep",
    ),
}

DISTURBANCES = {
    "draft": Disturbance(
        "draft",
        "a cold draft",
        "the window latch had slipped loose",
        "the curtain fluttered and the window whispered at its frame",
        "The blanket edge lifted, and a little cold nose peeped in.",
        "The night felt too wide and too chilly for easy sleep.",
        fix_tags={"window", "tuck"},
        tags={"wind", "window", "sleep"},
    ),
    "thunder": Disturbance(
        "thunder",
        "a thunder grumble",
        "a storm had rolled over the manor",
        "far clouds rumbled, and one soft flash blinked at the glass",
        "The room seemed to hold its breath between one rumble and the next.",
        "Even a grand room can feel small when the sky talks loudly.",
        fix_tags={"lullaby", "count"},
        tags={"thunder", "storm", "sleep"},
    ),
    "creak": Disturbance(
        "creak",
        "a stair creak",
        "the old house was settling",
        "a board in the corridor gave a long, thin creak",
        "The sound came once, then again, like the house clearing its throat.",
        "It was only a little sound, but little sounds can grow in the dark.",
        fix_tags={"lamp", "check"},
        tags={"house", "night", "sleep"},
    ),
}

GRAND_IDEAS = {
    "crown": GrandIdea(
        "crown",
        "the tiny gold crown from the toy chest",
        "my crown will make me bold",
        "But the little crown felt hard and poky on the pillow, and sleep would not come near.",
        tags={"crown"},
    ),
    "bell": GrandIdea(
        "bell",
        "a silver handbell from the bedside table",
        "a brave bell will chase every worry away",
        "Yet the bell gave a bright cling-cling, and the room felt even more awake.",
        noisy=True,
        tags={"bell"},
    ),
    "lantern": GrandIdea(
        "lantern",
        "the bright reading lantern",
        "more light will make the shadows mind their manners",
        "But the stronger light made the corners sharp instead of soft, and the bed felt less sleepy than before.",
        bright=True,
        tags={"light"},
    ),
    "cloak": GrandIdea(
        "cloak",
        "a velvet parade cloak",
        "my velvet cloak will keep every worry away",
        "But the heavy cloak slipped and bunched and left cold spaces where the blanket should have been.",
        chilly=True,
        tags={"cloak"},
    ),
}

REMEDIES = {
    "window_latch": Remedy(
        "window_latch",
        "latch the window and tuck the blanket",
        "Caregiver crossed the rug, set the window snug in its frame, and tucked the blanket under {name}'s feet.",
        "At once the curtain grew still, and the cold little edge of the night stayed outside where it belonged.",
        3,
        fixes={"draft"},
        tags={"window", "blanket", "sleep"},
    ),
    "lullaby": Remedy(
        "lullaby",
        "hum a lullaby",
        "Caregiver sat beside the bed and hummed a slow lullaby, soft as slippers on a runner.",
        "The thunder kept its distance outside, while the song made a smaller, kinder sound inside the room.",
        3,
        fixes={"thunder"},
        tags={"song", "lullaby", "sleep"},
    ),
    "hall_check": Remedy(
        "hall_check",
        "check the hall with a small lamp",
        "Caregiver lifted a tiny shaded lamp, opened the door a crack, and showed {name} the empty hall.",
        "The old board gave one harmless creak and then seemed almost shy, as if it had only wanted to say good night.",
        3,
        fixes={"creak"},
        tags={"lamp", "hall", "sleep"},
    ),
    "count_rain": Remedy(
        "count_rain",
        "count raindrops together",
        "Caregiver held {name}'s hand and counted the rain between the thunder grumbles: one, two, three, breathe.",
        "The counting turned the storm into a pattern, and patterns are easier to rest beside than surprises.",
        2,
        fixes={"thunder"},
        tags={"counting", "storm", "sleep"},
    ),
    "kiss_forehead": Remedy(
        "kiss_forehead",
        "give a kiss",
        "Caregiver kissed {name}'s forehead and smiled.",
        "The kiss was lovely, but the room itself stayed just as noisy as before.",
        1,
        fixes=set(),
        tags={"kiss"},
    ),
}

RHYMES = {
    "draft": (
        "The curtain stayed still, and the blanket held tight.",
        "The room was not deep; it was ready for sleep.",
    ),
    "thunder": (
        "The clouds could roll on, but the fear was all gone.",
        "The sky kept its drum, yet soft dreams still came.",
    ),
    "creak": (
        "The floor gave one squeak, then no more for the week.",
        "The hall kept its keep, and the child fell asleep.",
    ),
}

GIRL_NAMES = ["Pearl", "Ivy", "Clara", "Nell", "Rose", "Lila", "Mabel", "June"]
BOY_NAMES = ["Jasper", "Hugh", "Owen", "Felix", "Theo", "Milo", "Arlo", "Ned"]
TRAITS = ["proud", "gentle", "curious", "solemn", "brave", "sleepy"]


@dataclass
class StoryParams:
    chamber: str
    disturbance: str
    grand_idea: str
    remedy: str
    name: str
    gender: str
    title_word: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "aristocrat": [(
        "What is an aristocrat?",
        "An aristocrat is a person from a family with a title, like a lord or a lady. In this story, the child is little and fancy, but still needs comfort like any other child."
    )],
    "window": [(
        "Why can a loose window make bedtime harder?",
        "A loose window can let in cold air and rustly sounds. That can make a room feel chilly and wakeful instead of cozy."
    )],
    "thunder": [(
        "What is thunder?",
        "Thunder is the big rumbling sound storms make in the sky. It can sound huge, but the sound itself is not inside your room."
    )],
    "lullaby": [(
        "What is a lullaby?",
        "A lullaby is a quiet song sung to help someone feel calm and sleepy. Slow sounds can make the body feel steady and safe."
    )],
    "lamp": [(
        "Why does a small lamp feel calmer than a bright light at bedtime?",
        "A small lamp lets you see enough without waking the whole room up. Gentle light helps bedtime stay soft."
    )],
    "sleep": [(
        "What helps a child fall asleep?",
        "A calm room, a warm bed, and a steady grown-up voice can all help. Sleep comes more easily when the body feels safe and the room feels quiet."
    )],
    "storm": [(
        "Why can counting help during a storm?",
        "Counting gives the mind a simple pattern to follow. That can make a scary sound feel more manageable."
    )],
}
KNOWLEDGE_ORDER = ["aristocrat", "window", "thunder", "lullaby", "lamp", "storm", "sleep"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    disturbance = f["disturbance"]
    remedy = f["remedy"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the word "aristocrat" and ends with a gentle rhyme.',
        f"Tell a soft night story about a little aristocrat named {child.id} who is kept awake by {disturbance.label} until a grown-up uses {remedy.label}.",
        f'Write a cozy manor bedtime tale with simple rhyming lines, where a grand child learns that the right small comfort works better than a fancy idea.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    disturbance = f["disturbance"]
    idea = f["idea"]
    remedy = f["remedy"]
    title_word = f["title_word"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little aristocrat called {title_word} {child.id}, and {caregiver.label_word} who helps at bedtime."
        ),
        (
            "What disturbed bedtime?",
            f"Bedtime was disturbed by {disturbance.label}. {disturbance.sign.capitalize()}, which made the room feel less cozy and made {child.id} uneasy."
        ),
        (
            f"What grand idea did {child.id} try first?",
            f"{child.id} first reached for {idea.phrase}. That idea sounded grand, but it did not solve the real problem and only left {child.pronoun('object')} more wakeful."
        ),
        (
            f"How did {caregiver.label_word} help?",
            f"{caregiver.label_word.capitalize()} {remedy_past_tense(remedy, child)}. The remedy matched the real cause of the trouble, so the room became calmer and {child.id} could finally rest."
        ),
        (
            "Why did the remedy work better than the grand idea?",
            f"The grand idea was mostly for feeling important, while the remedy changed the room itself. Once the true source of the worry was handled, {child.id}'s body could settle and sleep."
        ),
        (
            "How did the story end?",
            f"It ended softly, with the manor room quiet again and the little aristocrat falling asleep. The rhyming lines at the end show that the room and the child both became calm."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"aristocrat", "sleep"} | set(world.facts["disturbance"].tags) | set(world.facts["remedy"].tags)
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


CURATED = [
    StoryParams("tower", "draft", "cloak", "window_latch", "Pearl", "girl", "Lady", "mother", "proud"),
    StoryParams("nursery", "thunder", "bell", "lullaby", "Jasper", "boy", "Lord", "father", "solemn"),
    StoryParams("tower", "creak", "lantern", "hall_check", "Clara", "girl", "Lady", "nurse", "curious"),
    StoryParams("nursery", "thunder", "crown", "count_rain", "Hugh", "boy", "Lord", "mother", "brave"),
]


def explain_rejection(disturbance: Disturbance, remedy: Remedy) -> str:
    if remedy.sense < 2:
        return (
            f"(No story: {remedy.label} is soothing, but it does not actually solve {disturbance.label}. "
            f"This world prefers remedies that honestly fit the bedtime trouble.)"
        )
    return (
        f"(No story: {remedy.label} does not fit {disturbance.label}. "
        f"The remedy must address the real cause, not just sound comforting.)"
    )


ASP_RULES = r"""
fits(D, R) :- disturbance(D), remedy(R), fixes(R, D).
sensible(R) :- remedy(R), sense(R, S), S >= 2.
valid(D, R) :- fits(D, R), sensible(R).

asleep(D, R) :- valid(D, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CHAMBERS:
        lines.append(asp.fact("chamber", cid))
    for did in DISTURBANCES:
        lines.append(asp.fact("disturbance", did))
    for gid in GRAND_IDEAS:
        lines.append(asp.fact("idea", gid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        for d in sorted(remedy.fixes):
            lines.append(asp.fact("fixes", rid, d))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "aristocrat" not in sample.story.lower():
            raise StoryError("smoke test story missing required bedtime content")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a little aristocrat, a night worry, and a fitting bedtime remedy."
    )
    ap.add_argument("--chamber", choices=CHAMBERS)
    ap.add_argument("--disturbance", choices=DISTURBANCES)
    ap.add_argument("--grand-idea", dest="grand_idea", choices=GRAND_IDEAS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--title-word", choices=["Lady", "Lord"])
    ap.add_argument("--caregiver", choices=["mother", "father", "nurse"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid disturbance/remedy pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.disturbance and args.remedy:
        d, r = DISTURBANCES[args.disturbance], REMEDIES[args.remedy]
        if not valid_combo(d, r):
            raise StoryError(explain_rejection(d, r))

    combos = [
        c for c in valid_combos()
        if (args.disturbance is None or c[0] == args.disturbance)
        and (args.remedy is None or c[1] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    disturbance, remedy = rng.choice(sorted(combos))
    chamber = args.chamber or rng.choice(sorted(CHAMBERS))
    grand_idea = args.grand_idea or rng.choice(sorted(GRAND_IDEAS))
    gender = args.gender or rng.choice(["girl", "boy"])
    default_title = "Lady" if gender == "girl" else "Lord"
    title_word = args.title_word or default_title
    if gender == "girl" and title_word == "Lord":
        raise StoryError("(No story: use --title-word Lady for a girl in this world.)")
    if gender == "boy" and title_word == "Lady":
        raise StoryError("(No story: use --title-word Lord for a boy in this world.)")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father", "nurse"])
    trait = rng.choice(TRAITS)
    return StoryParams(chamber, disturbance, grand_idea, remedy, name, gender, title_word, caregiver, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CHAMBERS[params.chamber],
        DISTURBANCES[params.disturbance],
        GRAND_IDEAS[params.grand_idea],
        REMEDIES[params.remedy],
        params.name,
        params.gender,
        params.title_word,
        params.caregiver,
        params.trait,
    )
    story = world.render()
    remedy = world.facts["remedy"]
    story = story.replace("{name}", params.name)
    remedy_action = remedy.action.replace("{name}", params.name)
    remedy_result = remedy.result.replace("{name}", params.name)
    if remedy_action in story and remedy_result in story:
        pass
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (disturbance, remedy) pairs:\n")
        for d, r in combos:
            print(f"  {d:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.disturbance} -> {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
