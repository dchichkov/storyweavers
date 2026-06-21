#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scold_pursue_chaos_flashback_moral_value_twist.py
============================================================================

A standalone story world for a bedtime tale shaped by the seed words
"scold", "pursue", and "chaos", plus the narrative instruments Flashback,
Moral Value, and Twist.

Premise
-------
At bedtime, a child is already missing one small comfort thing. Then the family
pet begins to pursue something lively through the room. The child pursues the
pet to stop the trouble, but the chase tips a basket or pile and causes chaos.
A grown-up arrives ready to scold. In a flashback, the grown-up remembers being
small and making a messy mistake too. That memory changes the response. The
twist is that the very mess reveals the missing comfort item, and bedtime can
continue with a gentler lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/scold_pursue_chaos_flashback_moral_value_twist.py
    python storyworlds/worlds/gpt-5.4/scold_pursue_chaos_flashback_moral_value_twist.py --pet kitten --lure moth --chaos yarn_basket --hidden stuffed_rabbit
    python storyworlds/worlds/gpt-5.4/scold_pursue_chaos_flashback_moral_value_twist.py --chaos cushion_stack --hidden moon_book
    python storyworlds/worlds/gpt-5.4/scold_pursue_chaos_flashback_moral_value_twist.py --all
    python storyworlds/worlds/gpt-5.4/scold_pursue_chaos_flashback_moral_value_twist.py --qa --json
    python storyworlds/worlds/gpt-5.4/scold_pursue_chaos_flashback_moral_value_twist.py --verify
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
class PetConfig:
    id: str
    label: str
    phrase: str
    type: str
    likes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class LureConfig:
    id: str
    label: str
    phrase: str
    motion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ChaosConfig:
    id: str
    label: str
    phrase: str
    spill: str
    size: int = 1
    reveals: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HiddenConfig:
    id: str
    label: str
    phrase: str
    bedtime_use: str
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


def _r_tip_chaos(world: World) -> list[str]:
    pet = world.entities.get("pet")
    source = world.entities.get("chaos")
    room = world.entities.get("room")
    if pet is None or source is None or room is None:
        return []
    if pet.meters["rushing"] < THRESHOLD:
        return []
    sig = ("tip", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["tipped"] += 1
    room.meters["chaos"] += float(source.attrs.get("size", 1))
    return ["__chaos__"]


def _r_reveal_hidden(world: World) -> list[str]:
    source = world.entities.get("chaos")
    hidden = world.entities.get("hidden")
    if source is None or hidden is None:
        return []
    if source.meters["tipped"] < THRESHOLD:
        return []
    sig = ("reveal", hidden.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hidden.meters["found"] += 1
    hidden.memes["relief"] += 1
    return ["__reveal__"]


def _r_chaos_feelings(world: World) -> list[str]:
    room = world.entities.get("room")
    child = world.entities.get("child")
    caregiver = world.entities.get("caregiver")
    if room is None or child is None or caregiver is None:
        return []
    if room.meters["chaos"] < THRESHOLD:
        return []
    sig = ("feelings", int(room.meters["chaos"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["guilt"] += 1
    caregiver.memes["anger"] += room.meters["chaos"]
    return ["__feelings__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="tip_chaos", tag="physical", apply=_r_tip_chaos),
    Rule(name="reveal_hidden", tag="physical", apply=_r_reveal_hidden),
    Rule(name="chaos_feelings", tag="emotional", apply=_r_chaos_feelings),
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
            if not s.startswith("__"):
                world.say(s)
    return produced


PETS = {
    "kitten": PetConfig(
        id="kitten",
        label="kitten",
        phrase="a striped kitten named Pip",
        type="kitten",
        likes={"moth", "firefly", "ribbon"},
        tags={"kitten"},
    ),
    "puppy": PetConfig(
        id="puppy",
        label="puppy",
        phrase="a tumble-footed puppy named Pebble",
        type="puppy",
        likes={"firefly", "slipper", "ribbon"},
        tags={"puppy"},
    ),
}

LURES = {
    "moth": LureConfig(
        id="moth",
        label="moth",
        phrase="a soft gray moth",
        motion="fluttered around the lamp like a tiny paper boat",
        tags={"moth"},
    ),
    "firefly": LureConfig(
        id="firefly",
        label="firefly",
        phrase="a blinking firefly",
        motion="blinked green-gold and drifted through the open window",
        tags={"firefly"},
    ),
    "ribbon": LureConfig(
        id="ribbon",
        label="ribbon",
        phrase="a loose satin ribbon",
        motion="slid from the bed and danced over the floorboards",
        tags={"ribbon"},
    ),
    "slipper": LureConfig(
        id="slipper",
        label="slipper",
        phrase="one fuzzy slipper",
        motion="skidded when a careless paw hooked it",
        tags={"slipper"},
    ),
}

CHAOS = {
    "yarn_basket": ChaosConfig(
        id="yarn_basket",
        label="yarn basket",
        phrase="a round basket full of sleepy yarn balls",
        spill="the yarn unrolled in every direction until the rug looked full of moonlit noodles",
        size=1,
        reveals={"stuffed_rabbit", "moon_book"},
        tags={"yarn"},
    ),
    "laundry_hamper": ChaosConfig(
        id="laundry_hamper",
        label="laundry hamper",
        phrase="a low hamper of warm folded pajamas",
        spill="the pajamas slid out in soft heaps across the floor",
        size=1,
        reveals={"blue_blanket", "moon_book"},
        tags={"laundry"},
    ),
    "cushion_stack": ChaosConfig(
        id="cushion_stack",
        label="cushion stack",
        phrase="a wobbly stack of floor cushions by the rocking chair",
        spill="the cushions flopped everywhere with soft thumps, and one rolled clear under the bed",
        size=2,
        reveals={"blue_blanket", "stuffed_rabbit"},
        tags={"cushion"},
    ),
}

HIDDEN = {
    "stuffed_rabbit": HiddenConfig(
        id="stuffed_rabbit",
        label="stuffed rabbit",
        phrase="the small stuffed rabbit with one bent ear",
        bedtime_use="to tuck under one arm while listening to a story",
        tags={"comfort_toy"},
    ),
    "moon_book": HiddenConfig(
        id="moon_book",
        label="moon book",
        phrase="the moon picture book with silver stars on the cover",
        bedtime_use="to read before the room went dark",
        tags={"book"},
    ),
    "blue_blanket": HiddenConfig(
        id="blue_blanket",
        label="blue blanket",
        phrase="the blue blanket with a satin edge",
        bedtime_use="to pull up to the chin at bedtime",
        tags={"blanket"},
    ),
}

MOODS = {
    "patient": {"anger": 1, "empathy": 2},
    "tired": {"anger": 2, "empathy": 1},
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ivy", "Ella", "June", "Ruby", "Tessa"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Jude", "Noah", "Evan", "Finn"]
TRAITS = ["gentle", "sleepy", "curious", "thoughtful", "small", "soft-voiced"]


def valid_combo(pet: str, lure: str, chaos: str, hidden: str) -> bool:
    return lure in PETS[pet].likes and hidden in CHAOS[chaos].reveals


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for pet_id in PETS:
        for lure_id in LURES:
            for chaos_id in CHAOS:
                for hidden_id in HIDDEN:
                    if valid_combo(pet_id, lure_id, chaos_id, hidden_id):
                        out.append((pet_id, lure_id, chaos_id, hidden_id))
    return out


def predicted_chaos_size(chaos_id: str) -> int:
    return CHAOS[chaos_id].size


def guidance_outcome(mood: str, chaos_id: str) -> str:
    anger = MOODS[mood]["anger"] + predicted_chaos_size(chaos_id)
    empathy = MOODS[mood]["empathy"] + 2
    return "gentle_guidance" if empathy >= anger else "scold_then_soften"


@dataclass
class StoryParams:
    pet: str
    lure: str
    chaos: str
    hidden: str
    name: str
    gender: str
    caregiver: str
    mood: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, child: Entity, caregiver: Entity, hidden_cfg: HiddenConfig) -> None:
    world.say(
        f"In the hush before bed, {child.id} padded about the little room while "
        f"{child.pronoun('possessive')} {caregiver.label_word} turned down the lamp."
    )
    world.say(
        f"{child.id} was a {next(iter([t for t in child.attrs.get('traits', []) if t] or ['little']))} "
        f"{child.type} who liked bedtime best when {hidden_cfg.phrase} was close by."
    )
    world.say(
        f"But tonight {hidden_cfg.phrase} was missing, and bedtime felt crooked without it."
    )


def lure_appears(world: World, pet: Entity, lure_cfg: LureConfig) -> None:
    pet.memes["interest"] += 1
    world.say(
        f"Just then, {lure_cfg.phrase} {lure_cfg.motion}. "
        f"{pet.id.capitalize()} saw it at once."
    )


def pursue_begins(world: World, child: Entity, pet: Entity, lure_cfg: LureConfig) -> None:
    pet.meters["rushing"] += 1
    child.meters["rushing"] += 1
    child.memes["worry"] += 1
    world.say(
        f"With a tiny leap, {pet.id} began to pursue the {lure_cfg.label}. "
        f"{child.id} hurried after {pet.pronoun('object')}, trying to stop the chase before anything bumped or fell."
    )


def chaos_happens(world: World, chaos_cfg: ChaosConfig) -> None:
    propagate(world, narrate=False)
    source = world.get("chaos")
    room = world.get("room")
    if source.meters["tipped"] >= THRESHOLD:
        word = "chaos" if room.meters["chaos"] >= 2 else "a little chaos"
        world.say(
            f"A paw, a foot, and one quick turn later, {source.phrase} tipped over. "
            f"{chaos_cfg.spill} For one startled moment, the room was full of {word}."
        )


def caregiver_arrives(world: World, caregiver: Entity, child: Entity) -> None:
    caregiver.memes["alarm"] += 1
    room = world.get("room")
    if room.meters["chaos"] >= 2:
        world.say(
            f'"Oh, {child.id}," {caregiver.label_word} said, hurrying in. '
            f'"What happened here?"'
        )
    else:
        world.say(
            f'{caregiver.label_word.capitalize()} looked in from the doorway and drew a surprised breath.'
        )


def flashback(world: World, caregiver: Entity, hidden_cfg: HiddenConfig) -> None:
    caregiver.memes["memory"] += 1
    caregiver.memes["empathy"] += 2
    caregiver.memes["anger"] = max(0.0, caregiver.memes["anger"] - 1.0)
    world.say(
        f"For a second, {caregiver.label_word} almost began to scold."
    )
    world.say(
        f"Then a flashback came back as warm and clear as lamplight: when "
        f"{caregiver.pronoun()} had once been small, {caregiver.pronoun('possessive')} own bedtime treasure had vanished, "
        f"and a kind grown-up had helped instead of snapping."
    )
    world.say(
        f"Remembering that, {caregiver.pronoun()} knelt down and softened {caregiver.pronoun('possessive')} voice."
    )


def reveal_twist(world: World, child: Entity, hidden_cfg: HiddenConfig) -> None:
    hidden = world.get("hidden")
    if hidden.meters["found"] >= THRESHOLD:
        child.memes["relief"] += 1
        world.say(
            f"And then came the twist: under the spill lay {hidden_cfg.phrase}."
        )
        world.say(
            f'"There it is!" {child.id} gasped. The very mess that had spoiled the room had uncovered what bedtime needed most.'
        )


def respond(world: World, caregiver: Entity, child: Entity, hidden_cfg: HiddenConfig, outcome: str) -> None:
    child.memes["honesty"] += 1
    if outcome == "scold_then_soften":
        child.memes["fear"] += 1
        world.say(
            f'"You must not race indoors like that," {caregiver.label_word} said first, and the words came out sharper than {caregiver.pronoun()} meant.'
        )
        world.say(
            f"{child.id}'s eyes filled at once, and {child.pronoun()} whispered that {child.pronoun()} had only been trying to save the room and find {hidden_cfg.label}."
        )
        world.say(
            f"Seeing that, {caregiver.label_word} touched {child.pronoun('possessive')} shoulder. "
            f'"I know you were trying to help," {caregiver.pronoun()} said. "Next time, call me instead of chasing the trouble yourself."'
        )
    else:
        world.say(
            f'"Tell me true," {caregiver.label_word} said gently. "{pet_name(world)} started the chase, and you tried to stop it, didn\'t you?"'
        )
        world.say(
            f'{child.id} nodded and told the whole thing. Because {child.pronoun()} spoke honestly, the room felt less scary right away.'
        )
        world.say(
            f'"Thank you for telling the truth," {caregiver.label_word} said. "Kind feet walk at bedtime, even when trouble zooms past."'
        )


def cleanup_and_end(world: World, caregiver: Entity, child: Entity, hidden_cfg: HiddenConfig) -> None:
    child.memes["love"] += 1
    child.memes["calm"] += 1
    caregiver.memes["love"] += 1
    caregiver.memes["calm"] += 1
    world.say(
        f"Together they set the room right again, one soft armful at a time."
    )
    world.say(
        f"When the floor was clear, {child.id} climbed into bed with {hidden_cfg.phrase} close enough {hidden_cfg.bedtime_use}."
    )
    world.say(
        f"{caregiver.label_word.capitalize()} kissed the top of {child.pronoun('possessive')} head and said that bedtime went best with honesty, gentle hands, and help asked early."
    )
    world.say(
        f"Soon the room was quiet, the pet was curled in a sleepy circle, and the little trouble of the night had turned into a wiser ending."
    )


def pet_name(world: World) -> str:
    return world.get("pet").id


def tell(
    pet_cfg: PetConfig,
    lure_cfg: LureConfig,
    chaos_cfg: ChaosConfig,
    hidden_cfg: HiddenConfig,
    name: str,
    gender: str,
    caregiver_type: str,
    mood: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        role="child",
        attrs={"traits": [trait]},
    ))
    caregiver = world.add(Entity(
        id="Parent",
        kind="character",
        type=caregiver_type,
        label="the parent",
        role="caregiver",
        attrs={"mood": mood},
    ))
    pet = world.add(Entity(
        id="Pip" if pet_cfg.id == "kitten" else "Pebble",
        kind="character",
        type=pet_cfg.type,
        label=pet_cfg.label,
        role="pet",
    ))
    chaos_ent = world.add(Entity(
        id="chaos",
        type="pile",
        label=chaos_cfg.label,
        phrase=chaos_cfg.phrase,
        attrs={"size": chaos_cfg.size},
    ))
    hidden_ent = world.add(Entity(
        id="hidden",
        type="comfort",
        label=hidden_cfg.label,
        phrase=hidden_cfg.phrase,
    ))
    room = world.add(Entity(id="room", type="room", label="bedroom"))

    world.facts["pet_cfg"] = pet_cfg
    world.facts["lure_cfg"] = lure_cfg
    world.facts["chaos_cfg"] = chaos_cfg
    world.facts["hidden_cfg"] = hidden_cfg
    world.facts["mood"] = mood

    introduce(world, child, caregiver, hidden_cfg)
    world.para()
    lure_appears(world, pet, lure_cfg)
    pursue_begins(world, child, pet, lure_cfg)
    chaos_happens(world, chaos_cfg)
    caregiver_arrives(world, caregiver, child)
    world.para()
    flashback(world, caregiver, hidden_cfg)
    reveal_twist(world, child, hidden_cfg)

    outcome = guidance_outcome(mood, chaos_cfg.id)
    respond(world, caregiver, child, hidden_cfg, outcome)
    world.para()
    cleanup_and_end(world, caregiver, child, hidden_cfg)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        pet=pet,
        chaos=chaos_ent,
        hidden=hidden_ent,
        room=room,
        outcome=outcome,
        found=hidden_ent.meters["found"] >= THRESHOLD,
        chaos_size=int(room.meters["chaos"]),
    )
    return world


KNOWLEDGE = {
    "kitten": [
        (
            "Why do kittens chase fluttery things?",
            "Kittens like quick little movements, so a fluttering thing can wake up their play instinct. They do not mean trouble, but they can make a mess while they chase."
        )
    ],
    "puppy": [
        (
            "Why do puppies chase moving things?",
            "Puppies are curious and playful, so they often run after things that slide, blink, or bounce. They need gentle teaching so their play stays safe."
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is a soft-winged insect that often flies near lamps at night. Its fluttery motion can catch an animal's eye."
        )
    ],
    "firefly": [
        (
            "What is a firefly?",
            "A firefly is a little insect that can glow in the dark. Its blinking light makes it easy to notice at night."
        )
    ],
    "ribbon": [
        (
            "Why does a ribbon look alive when it moves?",
            "A ribbon is light and loose, so it can wiggle and slide when air or paws move it. That makes it look exciting to a playful pet."
        )
    ],
    "slipper": [
        (
            "Why can a slipper start a pet game?",
            "A soft slipper can slide across the floor when a paw hooks it. Once it moves, a playful pet may think it is part of a game."
        )
    ],
    "comfort_toy": [
        (
            "Why do children like a bedtime toy?",
            "A bedtime toy can help a child feel safe and calm. Familiar things make bedtime easier when the day is ending."
        )
    ],
    "book": [
        (
            "Why is a bedtime book comforting?",
            "A bedtime book gives a child quiet words and familiar pictures before sleep. That calm routine helps the body settle down."
        )
    ],
    "blanket": [
        (
            "Why does a favorite blanket help at night?",
            "A favorite blanket feels warm and known, so it can make bedtime feel safe. Small bedtime habits help children relax."
        )
    ],
    "honesty": [
        (
            "Why is it important to tell the truth after an accident?",
            "Telling the truth helps grown-ups understand what really happened. Honest words make it easier to fix a problem together."
        )
    ],
    "gentleness": [
        (
            "Why is gentle teaching better than sharp scolding sometimes?",
            "Gentle teaching can calm a child enough to listen and learn. When someone feels safe, it is easier to remember the lesson."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "kitten",
    "puppy",
    "moth",
    "firefly",
    "ribbon",
    "slipper",
    "comfort_toy",
    "book",
    "blanket",
    "honesty",
    "gentleness",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    pet_cfg = world.facts["pet_cfg"]
    lure_cfg = world.facts["lure_cfg"]
    hidden_cfg = world.facts["hidden_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "scold", "pursue", and "chaos".',
        f"Tell a gentle night story where a {child.type} named {child.id} pursues a {pet_cfg.label} that is chasing a {lure_cfg.label}, and the resulting chaos leads to a surprise discovery.",
        f"Write a cozy story with a flashback, a moral about honesty and kindness, and a twist where a missing bedtime thing like {hidden_cfg.label} is found because of the mess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    pet = world.facts["pet"]
    lure_cfg = world.facts["lure_cfg"]
    chaos_cfg = world.facts["chaos_cfg"]
    hidden_cfg = world.facts["hidden_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {caregiver.label_word}, and {pet.id} the family {world.facts['pet_cfg'].label}. They were all part of one bedtime problem in the little room."
        ),
        (
            f"Why did {child.id} run after {pet.id}?",
            f"{child.id} ran after {pet.id} because the pet had begun to pursue the {lure_cfg.label}. {child.pronoun().capitalize()} wanted to stop the chase before bedtime turned into a mess."
        ),
        (
            "What caused the chaos?",
            f"The chaos started when the chase tipped over {chaos_cfg.phrase}. Once it fell, {chaos_cfg.spill}, and the quiet room suddenly felt wild."
        ),
        (
            f"Why did {caregiver.label_word} almost scold?",
            f"{caregiver.label_word.capitalize()} came in and saw the mess all at once, so a sharp answer rose first. The room looked out of control, and {caregiver.pronoun()} thought the children and pet had raced too fast indoors."
        ),
        (
            "What was the flashback about?",
            f"The flashback reminded {caregiver.label_word} of being small and losing a bedtime treasure too. That memory made {caregiver.pronoun('object')} choose help over harshness."
        ),
        (
            "What was the twist?",
            f"The twist was that the mess revealed {hidden_cfg.phrase}. The very chaos that seemed to ruin bedtime is what brought the missing comfort thing back."
        ),
    ]
    if outcome == "scold_then_soften":
        qa.append(
            (
                "Did the grown-up scold in the end?",
                f"{caregiver.label_word.capitalize()} spoke sharply at first, then softened and explained the lesson kindly. The flashback changed a hard moment into a gentler one."
            )
        )
    else:
        qa.append(
            (
                "How did the grown-up teach the lesson?",
                f"{caregiver.label_word.capitalize()} asked for the truth in a calm voice and thanked {child.id} for being honest. That gentle response helped the lesson land without making bedtime feel scary."
            )
        )
    qa.append(
        (
            "What is the story's moral?",
            "The story teaches that honesty, gentle feet, and asking for help early can turn a muddle into something mended. Kindness helps people learn better than panic does."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["pet_cfg"].tags)
    tags |= set(world.facts["lure_cfg"].tags)
    tags |= set(world.facts["hidden_cfg"].tags)
    tags |= {"honesty", "gentleness"}
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        pet="kitten",
        lure="moth",
        chaos="yarn_basket",
        hidden="stuffed_rabbit",
        name="Lila",
        gender="girl",
        caregiver="mother",
        mood="patient",
        trait="sleepy",
    ),
    StoryParams(
        pet="puppy",
        lure="slipper",
        chaos="laundry_hamper",
        hidden="blue_blanket",
        name="Owen",
        gender="boy",
        caregiver="father",
        mood="tired",
        trait="curious",
    ),
    StoryParams(
        pet="kitten",
        lure="ribbon",
        chaos="cushion_stack",
        hidden="blue_blanket",
        name="Mina",
        gender="girl",
        caregiver="mother",
        mood="tired",
        trait="gentle",
    ),
    StoryParams(
        pet="puppy",
        lure="firefly",
        chaos="yarn_basket",
        hidden="moon_book",
        name="Theo",
        gender="boy",
        caregiver="father",
        mood="patient",
        trait="thoughtful",
    ),
]


def explain_rejection(pet: str, lure: str, chaos: str, hidden: str) -> str:
    if lure not in PETS[pet].likes:
        likes = ", ".join(sorted(PETS[pet].likes))
        return (
            f"(No story: a {PETS[pet].label} here would not sensibly pursue {LURES[lure].label}. "
            f"Try one of: {likes}.)"
        )
    if hidden not in CHAOS[chaos].reveals:
        options = ", ".join(sorted(CHAOS[chaos].reveals))
        return (
            f"(No story: {CHAOS[chaos].label} would not plausibly hide {HIDDEN[hidden].label}. "
            f"Try one of: {options}.)"
        )
    return "(No story: that combination does not fit this little world.)"


ASP_RULES = r"""
valid(P, L, C, H) :- pet(P), lure(L), chaos(C), hidden(H),
                     likes(P, L), reveals(C, H).

anger_total(A + S) :- chosen_mood(M), mood_anger(M, A),
                      chosen_chaos(C), chaos_size(C, S).
empathy_total(E + 2) :- chosen_mood(M), mood_empathy(M, E).

outcome(gentle_guidance) :- empathy_total(E), anger_total(A), E >= A.
outcome(scold_then_soften) :- empathy_total(E), anger_total(A), E < A.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pet_id, pet in PETS.items():
        lines.append(asp.fact("pet", pet_id))
        for lure in sorted(pet.likes):
            lines.append(asp.fact("likes", pet_id, lure))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for chaos_id, chaos in CHAOS.items():
        lines.append(asp.fact("chaos", chaos_id))
        lines.append(asp.fact("chaos_size", chaos_id, chaos.size))
        for hidden in sorted(chaos.reveals):
            lines.append(asp.fact("reveals", chaos_id, hidden))
    for hidden_id in HIDDEN:
        lines.append(asp.fact("hidden", hidden_id))
    for mood_id, vals in MOODS.items():
        lines.append(asp.fact("mood", mood_id))
        lines.append(asp.fact("mood_anger", mood_id, vals["anger"]))
        lines.append(asp.fact("mood_empathy", mood_id, vals["empathy"]))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_mood", params.mood),
        asp.fact("chosen_chaos", params.chaos),
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
    for mood in MOODS:
        for chaos_id in CHAOS:
            cases.append(
                StoryParams(
                    pet="kitten",
                    lure="moth",
                    chaos=chaos_id,
                    hidden=next(iter(sorted(CHAOS[chaos_id].reveals))),
                    name="Lila",
                    gender="girl",
                    caregiver="mother",
                    mood=mood,
                    trait="gentle",
                )
            )
    bad = 0
    for params in cases:
        if asp_outcome(params) != guidance_outcome(params.mood, params.chaos):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches guidance_outcome() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "bed" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story did not render a bedtime scene.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a pet chase causes chaos, a flashback softens a scold, and a twist reveals the missing bedtime comfort."
    )
    ap.add_argument("--pet", choices=sorted(PETS))
    ap.add_argument("--lure", choices=sorted(LURES))
    ap.add_argument("--chaos", choices=sorted(CHAOS))
    ap.add_argument("--hidden", choices=sorted(HIDDEN))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pet and args.lure and args.chaos and args.hidden:
        if not valid_combo(args.pet, args.lure, args.chaos, args.hidden):
            raise StoryError(explain_rejection(args.pet, args.lure, args.chaos, args.hidden))
    if args.pet and args.lure and args.lure not in PETS[args.pet].likes:
        chaos = args.chaos or next(iter(sorted(CHAOS)))
        hidden = args.hidden or next(iter(sorted(CHAOS[chaos].reveals)))
        raise StoryError(explain_rejection(args.pet, args.lure, chaos, hidden))
    if args.chaos and args.hidden and args.hidden not in CHAOS[args.chaos].reveals:
        pet = args.pet or next(iter(sorted(PETS)))
        lure = args.lure or next(iter(sorted(PETS[pet].likes)))
        raise StoryError(explain_rejection(pet, lure, args.chaos, args.hidden))

    combos = [
        combo for combo in valid_combos()
        if (args.pet is None or combo[0] == args.pet)
        and (args.lure is None or combo[1] == args.lure)
        and (args.chaos is None or combo[2] == args.chaos)
        and (args.hidden is None or combo[3] == args.hidden)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pet, lure, chaos, hidden = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    mood = args.mood or rng.choice(sorted(MOODS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        pet=pet,
        lure=lure,
        chaos=chaos,
        hidden=hidden,
        name=name,
        gender=gender,
        caregiver=caregiver,
        mood=mood,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pet not in PETS:
        raise StoryError(f"(Invalid pet: {params.pet})")
    if params.lure not in LURES:
        raise StoryError(f"(Invalid lure: {params.lure})")
    if params.chaos not in CHAOS:
        raise StoryError(f"(Invalid chaos source: {params.chaos})")
    if params.hidden not in HIDDEN:
        raise StoryError(f"(Invalid hidden item: {params.hidden})")
    if params.mood not in MOODS:
        raise StoryError(f"(Invalid mood: {params.mood})")
    if not valid_combo(params.pet, params.lure, params.chaos, params.hidden):
        raise StoryError(explain_rejection(params.pet, params.lure, params.chaos, params.hidden))

    world = tell(
        pet_cfg=PETS[params.pet],
        lure_cfg=LURES[params.lure],
        chaos_cfg=CHAOS[params.chaos],
        hidden_cfg=HIDDEN[params.hidden],
        name=params.name,
        gender=params.gender,
        caregiver_type=params.caregiver,
        mood=params.mood,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (pet, lure, chaos, hidden) combos:\n")
        for pet, lure, chaos, hidden in combos:
            print(f"  {pet:7} {lure:8} {chaos:15} {hidden}")
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
            header = f"### {p.name}: {p.pet} pursues {p.lure} by {p.chaos} (twist: {p.hidden})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
