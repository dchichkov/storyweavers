#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gassy_heinie_poker_twist_whodunit.py
===============================================================

A small cozy-whodunit storyworld for a child-facing mystery with a twist:
a rude little noise or smell seems to come from one of the people in the room,
but the true culprit is an ordinary object. The clue-solving turn uses a
fireplace poker to reach the hidden spot safely.

Seed requirements carried through the prose:
- includes the words "gassy", "heinie", and "poker"
- includes a clear Twist
- style stays close to a gentle Whodunit

Run it
------
    python storyworlds/worlds/gpt-5.4/gassy_heinie_poker_twist_whodunit.py
    python storyworlds/worlds/gpt-5.4/gassy_heinie_poker_twist_whodunit.py --setting parlor --pastime puzzle_table --cause beanbag
    python storyworlds/worlds/gpt-5.4/gassy_heinie_poker_twist_whodunit.py --cause bellows
    python storyworlds/worlds/gpt-5.4/gassy_heinie_poker_twist_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/gassy_heinie_poker_twist_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/gassy_heinie_poker_twist_whodunit.py --verify
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
# from the repo root or from this nested subdirectory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Core entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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


# ---------------------------------------------------------------------------
# Domain knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    room: str
    opening: str
    features: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Pastime:
    id: str
    name: str
    opening: str
    trigger: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    trigger: str
    needs: set[str] = field(default_factory=set)
    sound_text: str = ""
    smell_text: str = ""
    hide_text: str = ""
    reveal_text: str = ""
    clue_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World state and rule engine.
# ---------------------------------------------------------------------------
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"detective", "friend"}]

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


def _r_mystery(world: World) -> list[str]:
    culprit = world.get("culprit")
    if culprit.meters["active"] < THRESHOLD:
        return []
    sig = ("mystery", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room = world.get("room")
    room.meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["suspicion"] += 1
    return []


def _r_blame(world: World) -> list[str]:
    suspect = world.get("suspect")
    if suspect.memes["blamed"] < THRESHOLD:
        return []
    sig = ("blame", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["embarrassed"] += 1
    for kid in world.kids():
        if kid.id != suspect.id:
            kid.memes["worry"] += 1
    return []


def _r_reveal(world: World) -> list[str]:
    culprit = world.get("culprit")
    if culprit.meters["found"] < THRESHOLD:
        return []
    sig = ("reveal", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room = world.get("room")
    room.meters["mystery"] = 0.0
    suspect = world.get("suspect")
    suspect.memes["embarrassed"] = 0.0
    suspect.memes["relief"] += 1
    for kid in world.kids():
        kid.memes["suspicion"] = 0.0
        kid.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="blame", tag="social", apply=_r_blame),
    Rule(name="reveal", tag="social", apply=_r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for text in produced:
            world.say(text)
    return produced


# ---------------------------------------------------------------------------
# Constraints and silent prediction.
# ---------------------------------------------------------------------------
def cause_supported(setting: Setting, cause: Cause) -> bool:
    return cause.needs.issubset(setting.features)


def trigger_matches(pastime: Pastime, cause: Cause) -> bool:
    return pastime.trigger == cause.trigger


def valid_combo(setting: Setting, pastime: Pastime, cause: Cause) -> bool:
    return cause_supported(setting, cause) and trigger_matches(pastime, cause)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, pastime in PASTIMES.items():
            for cid, cause in CAUSES.items():
                if valid_combo(setting, pastime, cause):
                    combos.append((sid, pid, cid))
    return sorted(combos)


def predict_disturbance(setting: Setting, pastime: Pastime, cause: Cause) -> dict:
    return {
        "supported": cause_supported(setting, cause),
        "triggered": trigger_matches(pastime, cause),
        "disturbance": valid_combo(setting, pastime, cause),
    }


# ---------------------------------------------------------------------------
# Screenplay verbs.
# ---------------------------------------------------------------------------
def introduce(world: World, setting: Setting, pastime: Pastime, detective: Entity,
              friend: Entity, grownup: Entity, pet: Entity) -> None:
    for kid in (detective, friend):
        kid.memes["cozy"] += 1
    world.say(
        f"{setting.opening} In {setting.room}, {detective.id}, {friend.id}, "
        f"and {grownup.label_word} settled in with {pastime.opening}."
    )
    world.say(
        f"{pet.label.capitalize()} curled nearby while the fire clicked and the rain tapped softly outside."
    )
    world.say(pastime.detail)


def disturb(world: World, cause: Cause, detective: Entity, friend: Entity, suspect: Entity) -> None:
    culprit = world.get("culprit")
    culprit.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then it happened: {cause.sound_text} {cause.smell_text}".strip()
    )
    world.say(
        f"{friend.id} blinked. \"That sounded like a tiny gassy ghost,\" {friend.pronoun()} whispered."
    )
    suspect.memes["blamed"] += 1
    propagate(world, narrate=False)
    if suspect.kind == "character":
        world.say(
            f"{detective.id} felt heat climb into {detective.pronoun('possessive')} cheeks. "
            f"No one wanted to point at anybody's heinie without proof, but every face in the room had turned toward {suspect.id}."
        )
    else:
        world.say(
            f"For one worried second, everyone stared at {suspect.label}, as if the poor pet might be the culprit."
        )


def accuse(world: World, detective: Entity, friend: Entity, suspect: Entity, grownup: Entity) -> None:
    if suspect.kind == "character":
        world.say(
            f"\"I didn't do it,\" {suspect.id} said at once, folding {suspect.pronoun('possessive')} hands in {suspect.pronoun('possessive')} lap."
        )
        world.say(
            f"{grownup.label_word.capitalize()} lifted a calm finger. \"A good whodunit needs clues, not guesses,\" {grownup.pronoun()} said."
        )
    else:
        world.say(
            f"\"It wasn't {suspect.label},\" said {grownup.label_word}. \"We will not blame a dog just because he has a nose and a tail.\""
        )
    world.say(
        f"{detective.id} looked around the room again, trying to think like a very small detective."
    )


def inspect(world: World, setting: Setting, cause: Cause, detective: Entity, friend: Entity, grownup: Entity) -> None:
    pred = predict_disturbance(setting, PASTIMES[world.facts["pastime"].id], cause)
    world.facts["predicted_disturbance"] = pred["disturbance"]
    world.say(
        f"That was when {detective.id} noticed {cause.clue_text}"
    )
    world.say(
        f"\"Maybe the sound came from over there,\" {detective.pronoun()} said."
    )
    world.say(
        f"{grownup.label_word.capitalize()} took the fireplace poker and used its long iron tip to reach the dark spot safely. {cause.hide_text}"
    )


def reveal(world: World, cause: Cause, detective: Entity, friend: Entity, suspect: Entity, grownup: Entity) -> None:
    culprit = world.get("culprit")
    culprit.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(cause.reveal_text)
    if suspect.kind == "character":
        world.say(
            f"{friend.id} gasped. \"So it was never {suspect.id} at all!\""
        )
    else:
        world.say(
            f"{friend.id} laughed with relief. \"So {suspect.label} was innocent!\""
        )
    world.say(
        f"It was the Twist of the whole little whodunit: the room had blamed a person or pet, but the real trouble had been an ordinary thing all along."
    )
    if suspect.kind == "character":
        suspect.memes["hurt"] += 1
        world.say(
            f"{detective.id} turned to {suspect.id}. \"I'm sorry we looked at you first,\" {detective.pronoun()} said."
        )
    else:
        world.say(
            f"{grownup.label_word.capitalize()} rubbed {suspect.label}'s ears and said, \"A detective should clear the innocent too.\""
        )


def ending(world: World, pastime: Pastime, detective: Entity, friend: Entity, grownup: Entity, pet: Entity) -> None:
    for kid in (detective, friend):
        kid.memes["joy"] += 1
    world.say(
        f"Soon the mystery had melted into giggles. {grownup.label_word.capitalize()} moved the troublesome thing away, and {detective.id} and {friend.id} went back to {pastime.name} with kinder eyes."
    )
    world.say(
        f"Even {pet.label} thumped the floor as if applauding the case being closed."
    )
    world.say(
        f"After that, whenever a silly puff or funny smell drifted through the room, they remembered the night of the poker, the false blame, and the clue that solved everything."
    )


# ---------------------------------------------------------------------------
# Story assembly.
# ---------------------------------------------------------------------------
def tell(setting: Setting, pastime: Pastime, cause: Cause, detective_name: str,
         detective_gender: str, friend_name: str, friend_gender: str,
         suspect_role: str, grownup_type: str, pet_type: str) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
        traits=["observant"],
        tags={"detective"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["dramatic"],
        tags={"friend"},
    ))
    grownup = world.add(Entity(
        id="Parent",
        kind="character",
        type=grownup_type,
        label="the parent",
        role="grownup",
        tags={"grownup"},
    ))
    pet_label = {"dog": "the dog", "cat": "the cat"}[pet_type]
    pet = world.add(Entity(
        id="Pet",
        kind="thing",
        type=pet_type,
        label=pet_label,
        phrase=pet_label,
        role="pet",
        tags={pet_type},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=setting.room,
        phrase=setting.room,
        tags=set(setting.tags),
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="thing",
        type="cause",
        label=cause.label,
        phrase=cause.phrase,
        role="culprit",
        tags=set(cause.tags),
    ))

    if suspect_role == "detective":
        suspect = detective
    elif suspect_role == "friend":
        suspect = friend
    else:
        suspect = pet
    world.entities["suspect"] = suspect

    world.facts.update(
        setting=setting,
        pastime=pastime,
        cause=cause,
        detective=detective,
        friend=friend,
        grownup=grownup,
        pet=pet,
        suspect=suspect,
    )

    introduce(world, setting, pastime, detective, friend, grownup, pet)
    world.para()
    disturb(world, cause, detective, friend, suspect)
    accuse(world, detective, friend, suspect, grownup)
    world.para()
    inspect(world, setting, cause, detective, friend, grownup)
    reveal(world, cause, detective, friend, suspect, grownup)
    world.para()
    ending(world, pastime, detective, friend, grownup, pet)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "parlor": Setting(
        id="parlor",
        room="the front parlor",
        opening="Rain slid down the windows like silver strings.",
        features={"hearth", "rocking_chair", "basket"},
        tags={"fireplace"},
    ),
    "cottage": Setting(
        id="cottage",
        room="the little cottage sitting room",
        opening="Wind hummed outside the cottage, but indoors the lamps glowed warm and steady.",
        features={"hearth", "boot_tray"},
        tags={"fireplace", "boots"},
    ),
    "library_nook": Setting(
        id="library_nook",
        room="the library nook by the fireplace",
        opening="The house had gone quiet enough for the clock to sound important.",
        features={"hearth", "basket", "rocking_chair"},
        tags={"fireplace", "books"},
    ),
}

PASTIMES = {
    "puzzle_table": Pastime(
        id="puzzle_table",
        name="the puzzle",
        opening="a moon puzzle spread across the low table",
        trigger="sit",
        detail="They leaned over shiny blue puzzle pieces and took turns guessing where the moon's white edge should go.",
        tags={"puzzle"},
    ),
    "cocoa_circle": Pastime(
        id="cocoa_circle",
        name="their cocoa-and-story circle",
        opening="steaming mugs of cocoa and a book with a red ribbon bookmark",
        trigger="warm",
        detail="The room smelled of cinnamon, and every now and then someone blew on a mug and watched the steam curl upward.",
        tags={"cocoa"},
    ),
    "shadow_show": Pastime(
        id="shadow_show",
        name="their shadow-animal show",
        opening="a sheet pinned up for shadow animals",
        trigger="step",
        detail="They made rabbits, birds, and wobbling dragons with the lamp behind the sheet, stepping back and forth to make the shadows grow.",
        tags={"shadow"},
    ),
}

CAUSES = {
    "beanbag": Cause(
        id="beanbag",
        label="beanbag chair",
        phrase="the old striped beanbag chair",
        trigger="sit",
        needs={"rocking_chair"},
        sound_text="a polite little pfffft rose from under the rocking chair.",
        smell_text="A dusty puff followed it.",
        hide_text="With a gentle tug, the poker pulled out the old striped beanbag chair that had been wedged under the rocker.",
        reveal_text="When grownup nudged the rocker again, the trapped air sighed out of the beanbag once more. The sound matched the mystery exactly.",
        clue_text="a strip of blue cloth peeking from beneath the rocking chair, quivering each time someone shifted.",
        tags={"beanbag"},
    ),
    "boot": Cause(
        id="boot",
        label="rain boot",
        phrase="a muddy yellow rain boot",
        trigger="warm",
        needs={"hearth", "boot_tray"},
        sound_text="something near the fire gave a soft blurp.",
        smell_text="Then a warm swampy smell drifted out.",
        hide_text="The poker slid a muddy yellow rain boot away from the hearth, where it had been heating on the edge of the boot tray.",
        reveal_text="A bubble of trapped water popped inside the warm boot and sent out the same silly blurp and smell. The mystery had come from the boot, not from anybody's body.",
        clue_text="a curl of steam lifting from one lonely boot by the hearth while the others stood dry and quiet.",
        tags={"boot"},
    ),
    "bellows": Cause(
        id="bellows",
        label="fireplace bellows",
        phrase="the old leather fireplace bellows",
        trigger="step",
        needs={"hearth", "basket"},
        sound_text="from the log basket came a sudden braaap that made everyone jump.",
        smell_text="A puff of sooty air drifted after it.",
        hide_text="The poker lifted the old leather bellows from behind the log basket, where one side had been trapped under the basket's foot.",
        reveal_text="As soon as the basket shifted, the squeezed bellows let out another grand braaap of air. It had sounded shockingly rude, but it was only trapped wind in the bellows.",
        clue_text="the log basket standing crooked, with a leather corner pinched underneath it.",
        tags={"bellows"},
    ),
}

SUSPECT_ROLES = {
    "detective": "the detective child",
    "friend": "the other child",
    "pet": "the pet",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Maya", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Noah", "Theo"]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    pastime: str
    cause: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    suspect_role: str
    grownup: str
    pet: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="parlor",
        pastime="puzzle_table",
        cause="beanbag",
        detective_name="Lily",
        detective_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        suspect_role="friend",
        grownup="mother",
        pet="dog",
    ),
    StoryParams(
        setting="cottage",
        pastime="cocoa_circle",
        cause="boot",
        detective_name="Max",
        detective_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        suspect_role="pet",
        grownup="father",
        pet="dog",
    ),
    StoryParams(
        setting="library_nook",
        pastime="shadow_show",
        cause="bellows",
        detective_name="Zoe",
        detective_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        suspect_role="detective",
        grownup="mother",
        pet="cat",
    ),
]


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "fireplace": [
        (
            "What is a fireplace poker?",
            "A fireplace poker is a long metal tool used by grown-ups to move logs or reach safely into a fireplace area. Its length helps hands stay away from hot places.",
        )
    ],
    "beanbag": [
        (
            "Why can a beanbag make a puffing sound?",
            "A beanbag can trap air inside its cloth and stuffing. When someone squishes it, the air can squeeze out with a funny pfft noise.",
        )
    ],
    "boot": [
        (
            "Why might a warm rain boot smell funny?",
            "A wet boot can hold muddy water inside. When it gets warm, the smell can drift out more strongly.",
        )
    ],
    "bellows": [
        (
            "What do fireplace bellows do?",
            "Bellows push air toward a fire. If they are squeezed by accident, they can make a loud burst of air and dust.",
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what really happened. Good detectives look for clues before they blame anyone.",
        )
    ],
    "apology": [
        (
            "Why should you apologize after blaming someone unfairly?",
            "An apology helps repair hurt feelings. It shows that finding the truth matters more than winning a guess.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fireplace", "beanbag", "boot", "bellows", "clue", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    cause = f["cause"]
    pastime = f["pastime"]
    return [
        'Write a gentle whodunit for a 3-to-5-year-old that includes the words "gassy", "heinie", and "poker".',
        f"Tell a cozy mystery where {detective.id} and {friend.id} are busy with {pastime.name} when a silly rude sound starts a false accusation.",
        f"Write a Twist ending where the blamed person is innocent and the real culprit turns out to be {cause.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    grownup = f["grownup"]
    suspect = f["suspect"]
    cause = f["cause"]
    pastime = f["pastime"]
    setting = f["setting"]

    who = f"{detective.id}, {friend.id}, and their {grownup.label_word}"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {who} in {setting.room}. They are having a cozy time together when a tiny mystery interrupts them.",
        ),
        (
            "What were they doing when the mystery began?",
            f"They were enjoying {pastime.name}. That quiet, close moment made the strange puff and smell very easy to notice.",
        ),
        (
            "Why did everyone start guessing about a person or pet?",
            f"The sound was sudden and silly, so it seemed as if it must have come from someone in the room. That quick guess made feelings wobbly before any real clue had been checked.",
        ),
    ]
    if suspect.kind == "character":
        qa.append(
            (
                f"Why did {suspect.id} feel embarrassed?",
                f"{suspect.id} felt embarrassed because everyone looked at {suspect.pronoun('object')} before they had proof. Being blamed first made the mystery feel personal instead of playful.",
            )
        )
    else:
        qa.append(
            (
                "Why was the pet innocent?",
                f"The pet was only nearby when the noise happened. The real clue pointed to {cause.phrase}, so the pet had been blamed for the wrong reason.",
            )
        )
    qa.append(
        (
            "How did they solve the mystery?",
            f"{detective.id} noticed a clue, and {grownup.label_word} used the fireplace poker to reach the hidden spot safely. That let them uncover {cause.phrase} and test it, which proved the true cause.",
        )
    )
    qa.append(
        (
            "What was the Twist?",
            f"The Twist was that the room had suspected a person or pet, but the real culprit was {cause.phrase}. The clue changed the story from blame to understanding.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with relief, apology, and laughter. Once the truth was known, they could go back to {pastime.name} with kinder feelings.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"clue", "apology"} | set(world.facts["setting"].tags) | set(world.facts["cause"].tags)
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


# ---------------------------------------------------------------------------
# Trace and rejection helpers.
# ---------------------------------------------------------------------------
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
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, pastime: Pastime, cause: Cause) -> str:
    if not cause_supported(setting, cause):
        need = ", ".join(sorted(cause.needs))
        have = ", ".join(sorted(setting.features))
        return (
            f"(No story: {cause.phrase} needs setting features [{need}], but {setting.id} only has [{have}]. "
            f"The culprit has to be physically present in the room for a fair whodunit.)"
        )
    return (
        f"(No story: {cause.phrase} is triggered by '{cause.trigger}', but {pastime.id} triggers '{pastime.trigger}'. "
        f"The disturbance has to happen for a sensible mystery to begin.)"
    )


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supported(S, C) :- cause(C), setting(S), needs_all_met(S, C).
needs_all_met(S, C) :- not missing_need(S, C).
missing_need(S, C) :- needs(C, F), not has_feature(S, F).

trigger_match(P, C) :- pastime(P), cause(C), pastime_trigger(P, T), cause_trigger(C, T).

valid(S, P, C) :- supported(S, C), trigger_match(P, C).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(setting.features):
            lines.append(asp.fact("has_feature", sid, feat))
    for pid, pastime in PASTIMES.items():
        lines.append(asp.fact("pastime", pid))
        lines.append(asp.fact("pastime_trigger", pid, pastime.trigger))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_trigger", cid, cause.trigger))
        for feat in sorted(cause.needs):
            lines.append(asp.fact("needs", cid, feat))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases = list(CURATED)
    for idx in range(3):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(900 + idx))
        except StoryError as err:
            rc = 1
            print(f"SMOKE PARAM ERROR: {err}")
            continue
        smoke_cases.append(params)

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if "gassy" not in sample.story or "heinie" not in sample.story or "poker" not in sample.story:
                raise StoryError("seed words missing from story")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE GENERATION FAILED for {params}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle whodunit storyworld with a silly false blame and a twisty reveal."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pastime", choices=PASTIMES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--suspect-role", choices=SUSPECT_ROLES)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--pet", choices=["dog", "cat"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.pastime and args.cause:
        setting = SETTINGS[args.setting]
        pastime = PASTIMES[args.pastime]
        cause = CAUSES[args.cause]
        if not valid_combo(setting, pastime, cause):
            raise StoryError(explain_rejection(setting, pastime, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.pastime is None or combo[1] == args.pastime)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, pastime_id, cause_id = rng.choice(combos)
    detective_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=detective_name)
    suspect_role = args.suspect_role or rng.choice(sorted(SUSPECT_ROLES))
    if suspect_role == "detective" and detective_name == friend_name:
        raise StoryError("(No story: the detective and friend cannot share the same name.)")
    return StoryParams(
        setting=setting_id,
        pastime=pastime_id,
        cause=cause_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        suspect_role=suspect_role,
        grownup=args.grownup or rng.choice(["mother", "father"]),
        pet=args.pet or rng.choice(["dog", "cat"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.pastime not in PASTIMES:
        raise StoryError(f"(Unknown pastime: {params.pastime})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.suspect_role not in SUSPECT_ROLES:
        raise StoryError(f"(Unknown suspect role: {params.suspect_role})")
    if params.grownup not in {"mother", "father"}:
        raise StoryError(f"(Unknown grownup: {params.grownup})")
    if params.pet not in {"dog", "cat"}:
        raise StoryError(f"(Unknown pet: {params.pet})")

    setting = SETTINGS[params.setting]
    pastime = PASTIMES[params.pastime]
    cause = CAUSES[params.cause]
    if not valid_combo(setting, pastime, cause):
        raise StoryError(explain_rejection(setting, pastime, cause))

    world = tell(
        setting=setting,
        pastime=pastime,
        cause=cause,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        suspect_role=params.suspect_role,
        grownup_type=params.grownup,
        pet_type=params.pet,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, pastime, cause) combos:\n")
        for setting, pastime, cause in combos:
            print(f"  {setting:12} {pastime:12} {cause}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.pastime} / {p.cause}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
