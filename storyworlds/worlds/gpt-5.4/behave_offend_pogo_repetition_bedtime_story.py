#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/behave_offend_pogo_repetition_bedtime_story.py
========================================================================

A small bedtime storyworld about a child who wants to pogo when the house is
trying to settle down. The world checks whether the bouncing would honestly be
too loud for a sleepy listener, and whether the offered quiet activity is truly
gentle enough for bedtime.

Seed requirements covered:
- words: behave, offend, pogo
- feature: repetition
- style: bedtime story

Run it
------
    python storyworlds/worlds/gpt-5.4/behave_offend_pogo_repetition_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/behave_offend_pogo_repetition_bedtime_story.py --listener grandma --quiet picture_book
    python storyworlds/worlds/gpt-5.4/behave_offend_pogo_repetition_bedtime_story.py --quiet pillow_fort
    python storyworlds/worlds/gpt-5.4/behave_offend_pogo_repetition_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/behave_offend_pogo_repetition_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/behave_offend_pogo_repetition_bedtime_story.py --verify
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
URGE_INIT = 5
CAUTIOUS_TRAITS = {"careful", "gentle", "sleepy", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "sister"}
        male = {"boy", "father", "grandfather", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Room:
    id: str
    label: str
    phrase: str
    echo: int
    bedtime_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Listener:
    id: str
    label: str
    phrase: str
    type: str
    sensitivity: int
    asleep_text: str
    wake_text: str
    apology_text: str
    relation_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuietChoice:
    id: str
    label: str
    phrase: str
    noise: int
    setup: str
    ending: str
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


def _r_noise_offends(world: World) -> list[str]:
    room = world.get("room")
    listener = world.get("listener")
    if room.meters["noise"] < THRESHOLD:
        return []
    if room.meters["noise"] <= listener.attrs["tolerance"]:
        return []
    sig = ("offend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    listener.memes["offended"] += 1
    listener.memes["awake"] += 1
    return ["__offended__"]


def _r_parent_worries(world: World) -> list[str]:
    listener = world.get("listener")
    parent = world.get("parent")
    if listener.memes["offended"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parent.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule("noise_offends", "social", _r_noise_offends),
    Rule("parent_worries", "social", _r_parent_worries),
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


def pogo_noise(room: Room) -> int:
    return room.echo + 2


def would_offend(room: Room, listener: Listener) -> bool:
    return pogo_noise(room) > listener.sensitivity


def quiet_works(listener: Listener, choice: QuietChoice) -> bool:
    return choice.noise <= listener.sensitivity


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for rid, room in ROOMS.items():
        for lid, listener in LISTENERS.items():
            if not would_offend(room, listener):
                continue
            for qid, choice in QUIET_CHOICES.items():
                if quiet_works(listener, choice):
                    out.append((rid, lid, qid))
    return out


def initial_restraint(trait: str) -> int:
    return 5 if trait in CAUTIOUS_TRAITS else 3


def would_heed(listener: Listener, trait: str) -> bool:
    bonus = 1 if listener.sensitivity >= 3 else 0
    return initial_restraint(trait) + 1 + bonus > URGE_INIT


def predict_pogo(world: World) -> dict:
    sim = world.copy()
    do_pogo(sim, narrate=False)
    listener = sim.get("listener")
    room = sim.get("room")
    return {
        "offends": listener.memes["offended"] >= THRESHOLD,
        "noise": room.meters["noise"],
    }


def predict_quiet(world: World, choice: QuietChoice) -> dict:
    return {
        "settles": quiet_works(LISTENERS[world.facts["listener_cfg"].id], choice),
        "noise": choice.noise,
    }


def do_pogo(world: World, narrate: bool = True) -> None:
    room = world.get("room")
    child = world.get("child")
    room.meters["noise"] += float(pogo_noise(world.facts["room_cfg"]))
    child.memes["delight"] += 1
    child.memes["defiance"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, parent: Entity, room: Room) -> None:
    world.say(
        f"In {room.label}, bedtime had almost tucked the whole house in. {room.phrase}"
    )
    world.say(
        f"{child.id} was already in pajamas, but {child.pronoun()} still had one bright idea left."
    )
    world.say(
        f"By the wall stood a little pogo stick, looking springy and awake while everyone else was growing quiet."
    )


def desire(world: World, child: Entity) -> None:
    child.memes["desire"] += 1
    child.memes["joy"] += 1
    world.say(
        f'"Just three jumps," {child.id} whispered. "I want to pogo before I sleep."'
    )
    world.say("In the child's head the thought already sounded like a song: boing-boing-boing.")


def warning(world: World, parent: Entity, child: Entity, listener: Entity,
            listener_cfg: Listener, room: Room) -> None:
    pred = predict_pogo(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_offends"] = pred["offends"]
    child.memes["conscience"] += 1
    world.say(
        f'{parent.label_word.capitalize()} touched the pogo stick first. '
        f'"Boing-boing-boing is a daytime sound," {parent.pronoun()} said softly.'
    )
    world.say(
        f'"At bedtime we behave with gentle feet. Loud thumps in {room.label} could offend {listener_cfg.phrase}, '
        f'and {listener_cfg.asleep_text}."'
    )


def heed(world: World, child: Entity, parent: Entity, quiet: QuietChoice) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} looked at the pogo stick, then at the dim hall, and slowly nodded."
    )
    world.say(
        f'"Gentle feet," {child.pronoun()} repeated. "I can behave that way."'
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled, and together they {quiet.setup}."
    )


def defy(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But wanting the jumps was stronger than waiting. Before the room could stop {child.pronoun('object')}, "
        f"{child.id} gave the pogo stick a squeeze."
    )


def boing_scene(world: World, child: Entity) -> None:
    do_pogo(world)
    world.say(
        "Boing. Boing. Boing. The sound hopped down the wall, across the floor, and into the sleepy dark."
    )
    world.say(
        f"After the third bounce, even {child.id} could hear that the house no longer sounded ready for dreams."
    )


def wake_scene(world: World, listener_cfg: Listener) -> None:
    listener = world.get("listener")
    world.say(listener_cfg.wake_text)
    if listener.memes["offended"] >= THRESHOLD:
        world.say(
            f"It was not angry noise, only bedtime noise in the wrong place, but it was enough to offend tired ears."
        )


def apology(world: World, child: Entity, listener_cfg: Listener) -> None:
    child.memes["shame"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{child.id} climbed down at once. "Oh," {child.pronoun()} whispered. "I did not mean to offend {listener_cfg.apology_text}."'
    )
    world.say(
        "The word sounded heavy and true, and the child held the pogo stick still at last."
    )


def repair(world: World, parent: Entity, child: Entity, quiet: QuietChoice) -> None:
    child.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} bent close and answered in the quietest voice. '
        f'"Then let us fix it in the quietest way."'
    )
    world.say(
        f"Together they {quiet.setup}."
    )


def settle_listener(world: World, listener_cfg: Listener) -> None:
    listener = world.get("listener")
    listener.memes["offended"] = 0.0
    listener.memes["awake"] = 0.0
    listener.memes["comfort"] += 1
    world.say(listener_cfg.apology_text.capitalize() + " settled again as the room softened.")


def ending(world: World, child: Entity, room: Room, quiet: QuietChoice, listener_cfg: Listener,
           outcome: str) -> None:
    child.memes["love"] += 1
    child.memes["sleepy"] += 1
    if outcome == "heeded":
        world.say(
            f"Soon there was no boing-boing-boing at all, only {quiet.ending}."
        )
    else:
        world.say(
            f"Soon the boing-boing-boing was gone, and in its place came {quiet.ending}."
        )
    world.say(
        f'{child.id} tucked closer under the blanket and whispered one last time, "Bedtime means gentle feet."'
    )
    world.say(room.bedtime_image)


def tell(room: Room, listener_cfg: Listener, quiet: QuietChoice,
         name: str = "Milo", gender: str = "boy", parent_type: str = "mother",
         trait: str = "gentle") -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    listener = world.add(
        Entity(
            id="listener",
            kind="character",
            type=listener_cfg.type,
            role="listener",
            label=listener_cfg.label,
            attrs={"tolerance": listener_cfg.sensitivity},
        )
    )
    room_ent = world.add(Entity(id="room", kind="thing", type="room", label=room.label))
    child.memes["urge"] = float(URGE_INIT)
    child.memes["restraint"] = float(initial_restraint(trait))
    world.facts.update(room_cfg=room, listener_cfg=listener_cfg, quiet_cfg=quiet, trait=trait)

    opening(world, child, parent, room)
    desire(world, child)

    world.para()
    warning(world, parent, child, listener, listener_cfg, room)

    if would_heed(listener_cfg, trait):
        heed(world, child, parent, quiet)
        outcome = "heeded"
    else:
        defy(world, child)
        world.para()
        boing_scene(world, child)
        wake_scene(world, listener_cfg)
        world.para()
        apology(world, child, listener_cfg)
        repair(world, parent, child, quiet)
        settle_listener(world, listener_cfg)
        outcome = "woke_then_fixed"

    world.para()
    ending(world, child, room, quiet, listener_cfg, outcome)
    world.facts.update(
        child=child,
        parent=parent,
        listener=listener,
        room=room_ent,
        outcome=outcome,
        listener_woke=outcome == "woke_then_fixed",
        quiet_used=quiet,
    )
    return world


ROOMS = {
    "hallway": Room(
        "hallway",
        "the hallway",
        "A moon-shaped night-light made a pale stripe across the boards.",
        3,
        "Outside the window, the moon looked pleased to see the house calm again.",
        tags={"hallway", "bedtime"},
    ),
    "bedroom": Room(
        "bedroom",
        "the bedroom",
        "A star blanket was folded back, and the lamp glowed low beside the bed.",
        2,
        "The blanket rose and fell with sleepy breaths while the stars on the quilt stayed still.",
        tags={"bedroom", "bedtime"},
    ),
    "attic": Room(
        "attic",
        "the attic room",
        "The little room tucked under the roof held its breath with the rafters.",
        4,
        "Above the roof, the night sky rested quietly while the attic room finally did the same.",
        tags={"attic", "bedtime"},
    ),
}

LISTENERS = {
    "baby_brother": Listener(
        "baby_brother",
        "baby brother",
        "the baby brother in the next room",
        "brother",
        3,
        "the baby brother was trying to stay asleep in the next room",
        'Then from the next room came a small, surprised cry. The baby brother had woken and begun to fuss.',
        "the baby brother",
        "brother",
        tags={"baby", "sleep"},
    ),
    "grandma": Listener(
        "grandma",
        "grandma",
        "Grandma in the guest bed",
        "grandmother",
        2,
        "Grandma was dozing in the guest bed after her long visit",
        'A soft voice floated from the guest bed: "Oh dear, that is a lively sound for such a sleepy hour." Grandma was awake now.',
        "Grandma",
        "grandma",
        tags={"grandma", "sleep"},
    ),
    "little_sister": Listener(
        "little_sister",
        "little sister",
        "the little sister curled up under her duck blanket",
        "sister",
        3,
        "the little sister was already nearly asleep under her duck blanket",
        'From the little bed came a rustle and a blink. The little sister pushed up on one elbow, wide awake.',
        "the little sister",
        "sister",
        tags={"sister", "sleep"},
    ),
}

QUIET_CHOICES = {
    "picture_book": QuietChoice(
        "picture_book",
        "picture book",
        "a picture book about sleepy foxes",
        0,
        "opened a picture book about sleepy foxes and turned the pages with careful fingers",
        "the hush of turning pages",
        tags={"book", "quiet"},
    ),
    "whisper_song": QuietChoice(
        "whisper_song",
        "whisper song",
        "a whisper song",
        0,
        "sat on the bed and hummed a whisper song so softly it felt like breathing",
        "a tiny tune that barely stirred the air",
        tags={"song", "quiet"},
    ),
    "moon_puzzle": QuietChoice(
        "moon_puzzle",
        "moon puzzle",
        "a moon puzzle",
        0,
        "worked a moon puzzle on the blanket, piece by piece, without a thump",
        "the small click of puzzle pieces finding their places",
        tags={"puzzle", "quiet"},
    ),
    "pillow_fort": QuietChoice(
        "pillow_fort",
        "pillow fort",
        "a pillow fort",
        2,
        "dragged pillows into a fort by the bed",
        "the soft flop of pillows",
        tags={"pillow", "quiet"},
    ),
}

GIRL_NAMES = ["Lila", "Nora", "Mia", "Eva", "Ruby", "Tess"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Owen", "Finn", "Leo"]
TRAITS = ["gentle", "careful", "sleepy", "thoughtful", "bouncy", "curious"]

KNOWLEDGE = {
    "pogo": [(
        "What is a pogo stick?",
        "A pogo stick is a jumping toy with a spring. It can be fun to bounce on, but indoors it can be very loud."
    )],
    "bedtime": [(
        "Why do people use quiet voices at bedtime?",
        "Quiet voices help everyone in the house settle down and rest. When the house is calm, it is easier for sleepy people to stay asleep."
    )],
    "offend": [(
        "What does offend mean?",
        "To offend someone means to upset them or bother them. In this story, the loud bouncing bothered tired ears at bedtime."
    )],
    "book": [(
        "Why is reading a good bedtime activity?",
        "Reading is gentle and quiet, so it helps bodies slow down. A calm story can make sleepy feelings grow."
    )],
    "song": [(
        "Why can a soft song feel calming?",
        "A soft song has a gentle rhythm that does not bump or crash. That can help people feel safe and sleepy."
    )],
    "puzzle": [(
        "Why is a puzzle quieter than jumping?",
        "A puzzle uses hands and eyes more than big body bounces. That means it makes much less noise."
    )],
    "baby": [(
        "Why do babies wake easily?",
        "Babies are often light sleepers, so sudden sounds can wake them quickly. Loud noises can change a calm room very fast."
    )],
    "grandma": [(
        "Why might Grandma need a quiet room at night?",
        "A grown-up guest may be tired from the day and ready for rest. A quiet room helps her body stay peaceful."
    )],
}
KNOWLEDGE_ORDER = ["pogo", "bedtime", "offend", "baby", "grandma", "book", "song", "puzzle"]


@dataclass
class StoryParams:
    room: str
    listener: str
    quiet: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    listener_cfg = f["listener_cfg"]
    quiet = f["quiet_cfg"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "behave", "offend", and "pogo", and use gentle repetition.',
        f"Tell a soft bedtime story where {child.id} wants to pogo indoors, but a parent explains that the noise could offend {listener_cfg.phrase}.",
        f"Write a short sleepy story with the repeated sound 'boing-boing-boing' that ends with {child.id} choosing {quiet.phrase} instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    listener_cfg = f["listener_cfg"]
    room_cfg = f["room_cfg"]
    quiet = f["quiet_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted one more exciting jump at bedtime, and {child.pronoun('possessive')} {pw}, who helped turn the night gentle again."
        ),
        (
            f"What did {child.id} want to do?",
            f"{child.id} wanted to pogo indoors before sleeping. The springy idea felt exciting, even though the house was already trying to be quiet."
        ),
        (
            f"Why did {child.id}'s {pw} warn {child.pronoun('object')}?",
            f"{pw.capitalize()} warned {child.pronoun('object')} because loud pogo thumps in {room_cfg.label} would travel through the sleepy house. They could offend {listener_cfg.phrase} and wake {listener_cfg.relation_word} up."
        ),
    ]
    if f["outcome"] == "heeded":
        qa.append((
            f"Did anyone get woken up?",
            f"No. {child.id} stopped before jumping and chose a quieter bedtime activity instead. That choice protected the sleepy room before the problem could happen."
        ))
    else:
        qa.append((
            f"What happened after the pogo jumps?",
            f"The boing-boing-boing was loud enough to wake {listener_cfg.apology_text}. {child.id} heard the consequence right away and understood why bedtime needed gentler sounds."
        ))
        qa.append((
            f"What did {child.id} do after that?",
            f"{child.id} apologized and stopped bouncing. Then {child.pronoun()} joined {child.pronoun('possessive')} {pw} in {quiet.phrase}, which helped the room grow calm again."
        ))
    qa.append((
        "How did the story end?",
        f"It ended quietly, with {quiet.phrase} taking the place of noisy bouncing. The last image shows the house settled again, which proves that {child.id} learned to behave with gentle feet."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pogo", "bedtime", "offend"} | set(f["listener_cfg"].tags)
    q = f["quiet_cfg"]
    if q.id == "picture_book":
        tags.add("book")
    elif q.id == "whisper_song":
        tags.add("song")
    elif q.id == "moon_puzzle":
        tags.add("puzzle")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "baby_brother", "picture_book", "Milo", "boy", "mother", "gentle"),
    StoryParams("hallway", "grandma", "moon_puzzle", "Lila", "girl", "father", "bouncy"),
    StoryParams("attic", "little_sister", "whisper_song", "Theo", "boy", "mother", "curious"),
    StoryParams("bedroom", "grandma", "picture_book", "Ruby", "girl", "father", "careful"),
]


def explain_rejection(room: Room, listener: Listener, quiet: Optional[QuietChoice] = None) -> str:
    if not would_offend(room, listener):
        return (
            f"(No story: pogoing in {room.label} would not honestly be loud enough to bother {listener.phrase}. "
            f"The warning needs a real bedtime risk.)"
        )
    if quiet is not None and not quiet_works(listener, quiet):
        return (
            f"(No story: {quiet.phrase} is still too noisy for {listener.phrase}. "
            f"A bedtime fix must truly be quieter than the pogo thumps.)"
        )
    return "(No story: this combination is not a reasonable bedtime problem and fix.)"


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
would_offend(R, L) :- room(R), listener(L), echo(R, E), pogo_base(P), tolerance(L, T), E + P > T.
quiet_works(L, Q)  :- listener(L), quiet(Q), quiet_noise(Q, N), tolerance(L, T), N <= T.
valid(R, L, Q)     :- would_offend(R, L), quiet_works(L, Q).

% --- outcome model ----------------------------------------------------------
restraint(5) :- trait(T), cautious(T).
restraint(3) :- trait(T), not cautious(T).
bonus(1)     :- chosen_listener(L), sensitive(L).
bonus(0)     :- chosen_listener(L), not sensitive(L).

heed         :- restraint(R), bonus(B), urge_init(U), R + 1 + B > U.
outcome(heeded)        :- heed.
outcome(woke_then_fixed) :- not heed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("echo", rid, room.echo))
    for lid, listener in LISTENERS.items():
        lines.append(asp.fact("listener", lid))
        lines.append(asp.fact("tolerance", lid, listener.sensitivity))
        if listener.sensitivity >= 3:
            lines.append(asp.fact("sensitive", lid))
    for qid, quiet in QUIET_CHOICES.items():
        lines.append(asp.fact("quiet", qid))
        lines.append(asp.fact("quiet_noise", qid, quiet.noise))
    lines.append(asp.fact("pogo_base", 2))
    lines.append(asp.fact("urge_init", URGE_INIT))
    for t in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious", t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_listener", params.listener),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "heeded" if would_heed(LISTENERS[params.listener], params.trait) else "woke_then_fixed"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a child wants to pogo, the house needs quiet."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--listener", choices=LISTENERS)
    ap.add_argument("--quiet", choices=QUIET_CHOICES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.listener and not would_offend(ROOMS[args.room], LISTENERS[args.listener]):
        raise StoryError(explain_rejection(ROOMS[args.room], LISTENERS[args.listener]))
    if args.listener and args.quiet and not quiet_works(LISTENERS[args.listener], QUIET_CHOICES[args.quiet]):
        room = ROOMS[args.room] if args.room else next(iter(ROOMS.values()))
        raise StoryError(explain_rejection(room, LISTENERS[args.listener], QUIET_CHOICES[args.quiet]))

    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.listener is None or c[1] == args.listener)
        and (args.quiet is None or c[2] == args.quiet)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room, listener, quiet = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(room, listener, quiet, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ROOMS[params.room],
        LISTENERS[params.listener],
        QUIET_CHOICES[params.quiet],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, listener, quiet) combos:\n")
        for room, listener, quiet in combos:
            print(f"  {room:8} {listener:14} {quiet}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: pogo in {p.room} with {p.listener} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
