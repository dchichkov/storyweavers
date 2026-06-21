#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defeat_sound_effects_mystery.py
==========================================================

A standalone story world for a child-sized mystery built from the seed words
"defeat" and "Sound Effects". Two children hear a spooky noise, follow a real
clue, and solve the mystery in a sensible way.

The world prefers a small set of plausible mysteries over broad coverage:
a place must actually support the noisy source, and the chosen fix must really
fit that source. Some stories end with the children solving the problem
themselves; harder ones end with a grown-up finishing the practical fix after
the children bravely report what they found.

Run it
------
    python storyworlds/worlds/gpt-5.4/defeat_sound_effects_mystery.py
    python storyworlds/worlds/gpt-5.4/defeat_sound_effects_mystery.py --place library --source shutter --method latch
    python storyworlds/worlds/gpt-5.4/defeat_sound_effects_mystery.py --place greenhouse --source marble
    python storyworlds/worlds/gpt-5.4/defeat_sound_effects_mystery.py --all
    python storyworlds/worlds/gpt-5.4/defeat_sound_effects_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/defeat_sound_effects_mystery.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man", "janitor", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "librarian": "librarian",
            "janitor": "janitor",
            "caretaker": "caretaker",
            "teacher": "teacher",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    hush: str
    corner: str
    caretaker_line: str
    spook: int = 1
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound: str
    sound_line: str
    located: str
    clue: str
    reveal: str
    solved_line: str
    difficulty: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    report: str
    power: int = 1
    handles: set[str] = field(default_factory=set)
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "pal"}]

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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    room = world.entities.get("room")
    if source is None or room is None:
        return out
    if source.meters["active"] < THRESHOLD:
        return out
    sig = ("noise", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["noise"] += 1
    room.meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["curiosity"] += 1
    out.append("__noise__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if clue is None or clue.meters["found"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("confidence", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["confidence"] += 1
        if kid.memes["fear"] >= THRESHOLD:
            kid.memes["fear"] -= 0.5
    out.append("__clue__")
    return out


def _r_silence(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    room = world.entities.get("room")
    if source is None or source.meters["active"] >= THRESHOLD:
        return out
    sig = ("silence", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if room is not None:
        room.meters["quiet"] += 1
        room.meters["noise"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    out.append("__silence__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="clue", tag="social", apply=_r_clue),
    Rule(name="silence", tag="physical", apply=_r_silence),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for _ in range(len(CAUSAL_RULES) + 4):
        before = set(world.fired)
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
        if world.fired == before:
            break
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


PLACES = {
    "library": Place(
        id="library",
        label="the old library",
        opening="After school, the library was almost empty, with tall shelves and a long strip of gold light across the floor.",
        hush="Every whisper seemed to float higher than usual between the books.",
        corner="the long window by the map shelf",
        caretaker_line="the librarian came with quiet shoes and a ring of tiny keys",
        spook=2,
        affords={"shutter", "marble"},
        tags={"library", "mystery"},
    ),
    "clubhouse": Place(
        id="clubhouse",
        label="the backyard clubhouse",
        opening="Late in the afternoon, the little clubhouse smelled of wood, crayons, and old summer plans.",
        hush="The yard outside had gone still, which made every small sound feel bigger.",
        corner="the toy chest under the bench",
        caretaker_line="their dad ducked through the small door with a warm flashlight",
        spook=1,
        affords={"toy", "marble"},
        tags={"clubhouse", "mystery"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the school greenhouse",
        opening="Near sunset, the greenhouse glowed green and glassy, with rows of leaves shining like polished paper.",
        hush="Water drops and leaf shadows made the room feel full of secrets.",
        corner="the sink and potting shelf",
        caretaker_line="the caretaker hurried in with a toolbox that rattled softly",
        spook=2,
        affords={"pipe", "shutter"},
        tags={"greenhouse", "mystery"},
    ),
}

SOURCES = {
    "shutter": Source(
        id="shutter",
        label="a loose shutter",
        sound="clack-clack... clack!",
        sound_line="From the far side of the room came a sharp sound: clack-clack... clack!",
        located="the loose shutter tapping the frame",
        clue="the curtain kept puffing inward on a ribbon of cold air",
        reveal="It was only the shutter, not a ghost at all, knocking whenever the wind pushed it.",
        solved_line="Once the shutter was fastened, the room stopped answering itself.",
        difficulty=1,
        tags={"wind", "window", "sound_effects"},
    ),
    "marble": Source(
        id="marble",
        label="a runaway marble",
        sound="tik... tik-tik... tik!",
        sound_line="Something answered from the boards below: tik... tik-tik... tik!",
        located="a marble rolling in and out beneath a low shelf",
        clue="a bright blue marble flashed whenever the floor tipped just a little",
        reveal="The mystery sound was a marble, rolling every time the floor slanted and tapping the wood.",
        solved_line="The tiny ticking stopped the moment the marble was held still.",
        difficulty=1,
        tags={"rolling", "marble", "sound_effects"},
    ),
    "toy": Source(
        id="toy",
        label="a forgotten toy robot",
        sound="bzzzt... whirr... bzzzt!",
        sound_line="Then came the strangest noise of all: bzzzt... whirr... bzzzt!",
        located="the old toy robot twitching under the lid of the chest",
        clue="a faint blue blink leaked through the crack in the toy chest",
        reveal="The noisy culprit was a toy robot with a sleepy battery, buzzing whenever it woke for one more second.",
        solved_line="With the toy switched off, the clubhouse became cozy instead of creepy.",
        difficulty=1,
        tags={"toy", "battery", "sound_effects"},
    ),
    "pipe": Source(
        id="pipe",
        label="a drippy pipe",
        sound="plink... plink-plink... plonk.",
        sound_line="Behind the leaves came a watery answer: plink... plink-plink... plonk.",
        located="the little pipe above the sink dripping into a metal scoop",
        clue="a silver scoop under the sink held fresh dots of water",
        reveal="The eerie music was only water from a loose pipe, dropping into metal and echoing around the glass room.",
        solved_line="After the valve was turned snug, only the soft leaf-rustle remained.",
        difficulty=2,
        tags={"water", "pipe", "sound_effects"},
    ),
}

METHODS = {
    "latch": Method(
        id="latch",
        label="fasten the latch",
        action="reached up and fastened the latch tight",
        report="fastened the loose shutter so the wind could not bang it anymore",
        power=1,
        handles={"shutter"},
        tags={"window_fix"},
    ),
    "pocket": Method(
        id="pocket",
        label="pick it up",
        action="stooped down, picked up the marble, and tucked it safely away",
        report="picked up the rolling marble and stopped its ticking",
        power=1,
        handles={"marble"},
        tags={"pickup"},
    ),
    "switch_off": Method(
        id="switch_off",
        label="switch it off",
        action="lifted the chest lid and clicked the toy robot off",
        report="switched off the toy robot that had been buzzing in the chest",
        power=1,
        handles={"toy"},
        tags={"toy_fix"},
    ),
    "valve": Method(
        id="valve",
        label="tighten the valve",
        action="turned the little valve until the drip gave one last plink and quit",
        report="tightened the valve so the pipe stopped dripping into the metal scoop",
        power=2,
        handles={"pipe"},
        tags={"water_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "clever", "patient", "steady", "brave"]
STRONG_TRAITS = {"clever", "steady", "brave"}
CAREGIVERS = {
    "librarian": "librarian",
    "father": "father",
    "caretaker": "caretaker",
}


def source_fits(place: Place, source: Source) -> bool:
    return source.id in place.affords


def method_fits(source: Source, method: Method) -> bool:
    return source.id in method.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if not source_fits(place, source):
                continue
            for method_id, method in METHODS.items():
                if method_fits(source, method):
                    combos.append((place_id, source_id, method_id))
    return combos


def skill_value(trait: str) -> int:
    return 2 if trait in STRONG_TRAITS else 1


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    source = SOURCES[params.source]
    method = METHODS[params.method]
    score = skill_value(params.trait) + method.power
    needed = source.difficulty + place.spook
    return "kids_solve" if score >= needed else "grownup_solves"


def predict_outcome(place: Place, source: Source, method: Method, trait: str) -> dict:
    return {
        "score": skill_value(trait) + method.power,
        "needed": source.difficulty + place.spook,
        "kids_solve": skill_value(trait) + method.power >= source.difficulty + place.spook,
    }


def introduce(world: World, lead: Entity, pal: Entity, place: Place) -> None:
    world.say(place.opening)
    world.say(
        f"{lead.id} and {pal.id} had promised to put things away before going home, "
        f"but {place.hush}"
    )
    world.say(
        f"That made the whole place feel like the beginning of a mystery."
    )


def hear_noise(world: World, lead: Entity, pal: Entity, source: Source) -> None:
    src = world.get("source")
    src.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(source.sound_line)
    world.say(
        f'{pal.id} froze. "Did you hear that?" {pal.pronoun()} whispered.'
    )
    world.say(
        f'{lead.id} listened hard. Another sound came: {source.sound}'
    )


def fear_guess(world: World, lead: Entity, pal: Entity, place: Place) -> None:
    room = world.get("room")
    if room.meters["mystery"] >= THRESHOLD:
        world.say(
            f'"It sounds like it came from {place.corner}," {pal.id} said, scooting closer.'
        )
        world.say(
            f'For one breath, both children wondered if the room was trying to tell them a secret.'
        )


def search(world: World, lead: Entity, pal: Entity, source: Source) -> None:
    lead.memes["resolve"] += 1
    pal.memes["trust"] += 1
    world.say(
        f'{lead.id} took one careful step, then another. {pal.id} followed, holding onto courage the way some children hold onto a mitten.'
    )
    world.say(
        f"The sound led them toward {source.located}."
    )


def find_clue(world: World, lead: Entity, source: Source) -> None:
    clue = world.get("clue")
    clue.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {lead.id} noticed the real clue: {source.clue}."
    )
    world.say(
        f"That was the first crack in the mystery."
    )


def explain_clue(world: World, lead: Entity, source: Source, method: Method) -> None:
    world.say(
        f'"I do not think this is magic," {lead.id} said. "I think something real is making that sound, and we can stop it the right way."'
    )
    if source.id in method.handles:
        world.say(
            f"The plan was simple now: {method.label}."
        )


def kids_fix(world: World, lead: Entity, source: Source, method: Method) -> None:
    world.get("source").meters["active"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Very gently, {lead.id} {method.action}."
    )
    world.say(source.reveal)
    world.say(source.solved_line)


def call_grownup(world: World, lead: Entity, pal: Entity, helper: Entity, source: Source, method: Method, place: Place) -> None:
    pal.memes["fear"] += 0.5
    world.say(
        f'The clue helped, but the job still looked too tricky for small hands. "{helper.label_word.capitalize()}!" {pal.id} called.'
    )
    world.say(
        f"In a moment, {place.caretaker_line}."
    )
    world.say(
        f"{lead.id} pointed at the clue and explained what they had found."
    )
    world.get("source").meters["active"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {method.action}."
    )
    world.say(source.reveal)
    world.say(
        f"{source.solved_line} The children had solved the mystery first in their minds, and the grown-up finished the practical part."
    )


def ending(world: World, lead: Entity, pal: Entity, helper: Entity, outcome: str, place: Place) -> None:
    if outcome == "kids_solve":
        world.say(
            f'{pal.id} let out a laugh that sounded brighter than the whole room had a minute before. "We did it," {pal.pronoun()} said.'
        )
        world.say(
            f"They had not defeated a monster. They had used brave eyes and calm thinking to defeat a noisy little mystery in {place.label}."
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} smiled at them both. "You were right to look for a clue and right to call for help," {helper.pronoun()} said.'
        )
        world.say(
            f"{lead.id} and {pal.id} stood in the new quiet and felt their fear shrink. Together they had defeated the mystery, even if grown-up hands had finished the fix."
        )


def tell(
    place: Place,
    source: Source,
    method: Method,
    lead_name: str = "Lily",
    lead_gender: str = "girl",
    pal_name: str = "Tom",
    pal_gender: str = "boy",
    trait: str = "careful",
    caregiver: str = "librarian",
) -> World:
    world = World(place)
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        traits=[trait],
        label=lead_name,
    ))
    pal = world.add(Entity(
        id=pal_name,
        kind="character",
        type=pal_gender,
        role="pal",
        traits=["loyal"],
        label=pal_name,
    ))
    helper_type = CAREGIVERS[caregiver]
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_type,
    ))
    room = world.add(Entity(id="room", type="room", label=place.label))
    src = world.add(Entity(id="source", type="source", label=source.label, phrase=source.located))
    clue = world.add(Entity(id="clue", type="clue", label="clue", phrase=source.clue))

    introduce(world, lead, pal, place)
    world.para()
    hear_noise(world, lead, pal, source)
    fear_guess(world, lead, pal, place)
    world.para()
    search(world, lead, pal, source)
    find_clue(world, lead, source)
    explain_clue(world, lead, source, method)
    world.para()

    outcome = "kids_solve" if predict_outcome(place, source, method, trait)["kids_solve"] else "grownup_solves"
    if outcome == "kids_solve":
        kids_fix(world, lead, source, method)
    else:
        call_grownup(world, lead, pal, helper, source, method, place)

    world.para()
    ending(world, lead, pal, helper, outcome, place)

    world.facts.update(
        place=place,
        source_cfg=source,
        method=method,
        lead=lead,
        pal=pal,
        helper=helper,
        room=room,
        clue=clue,
        outcome=outcome,
        clue_found=clue.meters["found"] >= THRESHOLD,
        noise_heard=room.meters["mystery"] >= THRESHOLD,
        source_silenced=room.meters["quiet"] >= THRESHOLD,
        score=predict_outcome(place, source, method, trait)["score"],
        needed=predict_outcome(place, source, method, trait)["needed"],
    )
    return world


@dataclass
class StoryParams:
    place: str
    source: str
    method: str
    lead_name: str
    lead_gender: str
    pal_name: str
    pal_gender: str
    trait: str
    caregiver: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand at first, so you look for clues to explain it.",
        )
    ],
    "sound_effects": [
        (
            "What are sound effects in a story?",
            "Sound effects are words like clack, plink, or whirr that help you hear a sound in your imagination.",
        )
    ],
    "window": [
        (
            "Why can a loose shutter make a loud sound?",
            "A loose shutter can bang against a window frame when the wind pushes it, so it makes a clacking noise.",
        )
    ],
    "marble": [
        (
            "Why does a marble make noise when it rolls?",
            "A hard marble taps the floor or wood as it moves, so even a tiny marble can make a clear ticking sound.",
        )
    ],
    "toy": [
        (
            "Why can a toy buzz by itself?",
            "Some toys have batteries and switches, so if one is left on it can buzz or move until the battery fades.",
        )
    ],
    "water": [
        (
            "Why does dripping water sound loud in a quiet room?",
            "Each drop hits and echoes, so in a quiet room even a small plink can seem big and spooky.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure out what really happened.",
        )
    ],
    "help": [
        (
            "When should children call a grown-up for help?",
            "Children should call a grown-up when a problem is tricky, high up, sharp, leaky, or unsafe for small hands.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "sound_effects", "clue", "window", "marble", "toy", "water", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    pal = f["pal"]
    place = f["place"]
    source = f["source_cfg"]
    outcome = f["outcome"]
    if outcome == "kids_solve":
        return [
            f'Write a short mystery story for a 3-to-5-year-old that includes sound effects and the word "defeat".',
            f"Tell a gentle mystery where {lead.id} and {pal.id} hear {source.sound} in {place.label} and solve the puzzle by following a real clue.",
            f"Write a child-facing mystery in which a spooky sound turns out to have an ordinary cause, and the children defeat the mystery with calm thinking.",
        ]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes sound effects and the word "defeat".',
        f"Tell a gentle mystery where {lead.id} and {pal.id} hear {source.sound} in {place.label}, find the clue, and then call a grown-up to finish the safe fix.",
        f"Write a story where children bravely investigate a spooky noise, discover the ordinary cause, and defeat their fear by using clues and asking for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    pal = f["pal"]
    helper = f["helper"]
    place = f["place"]
    source = f["source_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {pal.id}, two children in {place.label}. They hear a strange sound and try to learn what is really making it.",
        ),
        (
            "What made the place feel mysterious at the start?",
            f"The place was quiet, and then the children heard {source.sound}. The sudden noise in such a hush made the room feel spooky.",
        ),
        (
            "What clue helped them solve the mystery?",
            f"The key clue was that {source.clue}. That clue showed them the sound had a real cause instead of something magical.",
        ),
    ]
    if f["outcome"] == "kids_solve":
        qa.append(
            (
                f"How did {lead.id} solve the mystery?",
                f"{lead.id} noticed the clue and then {method.action}. That stopped the sound and showed that {source.reveal.lower()}",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and happily. The children defeated the mystery by understanding it, and the room felt safe again.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {lead.id} and {pal.id} call {helper.label_word}?",
                f"They had figured out what the clue meant, but the fix was still too tricky for small hands. Calling a grown-up was part of solving the mystery safely.",
            )
        )
        qa.append(
            (
                f"What did {helper.label_word} do?",
                f"{helper.label_word.capitalize()} {method.action}. That practical fix stopped the sound after the children had already pointed to the real cause.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the noise gone and the children feeling brave. They defeated the mystery by finding the clue and getting the right help.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "sound_effects", "clue"}
    tags |= set(f["source_cfg"].tags)
    if f["outcome"] == "grownup_solves":
        tags.add("help")
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.traits:
            bits.append(f"traits={entity.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:8} ({entity.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library",
        source="shutter",
        method="latch",
        lead_name="Lily",
        lead_gender="girl",
        pal_name="Tom",
        pal_gender="boy",
        trait="brave",
        caregiver="librarian",
    ),
    StoryParams(
        place="clubhouse",
        source="toy",
        method="switch_off",
        lead_name="Max",
        lead_gender="boy",
        pal_name="Mia",
        pal_gender="girl",
        trait="clever",
        caregiver="father",
    ),
    StoryParams(
        place="greenhouse",
        source="pipe",
        method="valve",
        lead_name="Nora",
        lead_gender="girl",
        pal_name="Eli",
        pal_gender="boy",
        trait="careful",
        caregiver="caretaker",
    ),
    StoryParams(
        place="library",
        source="marble",
        method="pocket",
        lead_name="Sam",
        lead_gender="boy",
        pal_name="Rose",
        pal_gender="girl",
        trait="steady",
        caregiver="librarian",
    ),
]


def explain_rejection(place: Place, source: Source, method: Method) -> str:
    if not source_fits(place, source):
        return (
            f"(No story: {source.label} does not belong in {place.label}, so the mystery would not feel grounded there.)"
        )
    if not method_fits(source, method):
        return (
            f"(No story: the method '{method.id}' does not actually solve {source.label}. Pick the fix that matches the real cause.)"
        )
    return "(No story: this combination is not a reasonable mystery.)"


ASP_RULES = r"""
source_fits(P, S) :- place(P), source(S), affords(P, S).
method_fits(S, M) :- source(S), method(M), handles(M, S).
valid(P, S, M) :- source_fits(P, S), method_fits(S, M).

skill(2) :- trait(T), strong_trait(T).
skill(1) :- trait(T), not strong_trait(T).
score(V) :- skill(S), chosen_method(M), power(M, P), V = S + P.
needed(V) :- chosen_place(P), spook(P, SP), chosen_source(S), difficulty(S, D), V = SP + D.

outcome(kids_solve) :- score(SC), needed(N), SC >= N.
outcome(grownup_solves) :- score(SC), needed(N), SC < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("spook", place_id, place.spook))
        for source_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("difficulty", source_id, source.difficulty))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("power", method_id, method.power))
        for source_id in sorted(method.handles):
            lines.append(asp.fact("handles", method_id, source_id))
    for trait in sorted(STRONG_TRAITS):
        lines.append(asp.fact("strong_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_method", params.method),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spooky sound, a clue, and a small mystery defeated by reason."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.method:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        method = METHODS[args.method]
        if not (source_fits(place, source) and method_fits(source, method)):
            raise StoryError(explain_rejection(place, source, method))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        if args.place and args.source and args.method:
            raise StoryError(explain_rejection(PLACES[args.place], SOURCES[args.source], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, method_id = rng.choice(sorted(combos))
    lead_name, lead_gender = _pick_child(rng)
    pal_name, pal_gender = _pick_child(rng, avoid=lead_name)
    trait = args.trait or rng.choice(TRAITS)
    caregiver = args.caregiver or rng.choice(sorted(CAREGIVERS))
    return StoryParams(
        place=place_id,
        source=source_id,
        method=method_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        pal_name=pal_name,
        pal_gender=pal_gender,
        trait=trait,
        caregiver=caregiver,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        source = SOURCES[params.source]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not source_fits(place, source) or not method_fits(source, method):
        raise StoryError(explain_rejection(place, source, method))

    world = tell(
        place=place,
        source=source,
        method=method,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        pal_name=params.pal_name,
        pal_gender=params.pal_gender,
        trait=params.trait,
        caregiver=params.caregiver,
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
        print(f"{len(combos)} compatible (place, source, method) combos:\n")
        for place, source, method in combos:
            print(f"  {place:10} {source:8} {method}")
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
            header = f"### {p.lead_name} & {p.pal_name}: {p.source} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
