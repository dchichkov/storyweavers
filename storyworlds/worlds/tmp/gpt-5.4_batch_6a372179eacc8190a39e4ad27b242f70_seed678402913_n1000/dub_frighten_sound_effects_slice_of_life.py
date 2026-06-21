#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dub_frighten_sound_effects_slice_of_life.py
======================================================================

A small slice-of-life story world about children making a little home show and
trying to dub sound effects over it. One child reaches for a sound that is too
loud, which can frighten a nearby listener. A calm grown-up helps them notice
the effect their choice had, then guides them toward a gentler way to finish the
show.

The world model is intentionally small and constrained:

- a pretend home show or tiny movie setup
- one dramatic sound effect the child wants to dub
- one nearby listener who may be frightened by sudden loudness
- one repair method that either truly calms the listener or is refused

Reasonableness gate
-------------------
Not every sound/listener pair makes sense. A soft sound should not generate a
"frightened listener" story, and a fix that does not actually lower the scare
enough is rejected. The world only tells situations where there is a real small
everyday problem and a believable calm repair.

Run it
------
    python storyworlds/worlds/gpt-5.4/dub_frighten_sound_effects_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/dub_frighten_sound_effects_slice_of_life.py --show toy_train --sound thunder_sheet
    python storyworlds/worlds/gpt-5.4/dub_frighten_sound_effects_slice_of_life.py --listener baby
    python storyworlds/worlds/gpt-5.4/dub_frighten_sound_effects_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/dub_frighten_sound_effects_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4/dub_frighten_sound_effects_slice_of_life.py --verify
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
SOOTHE_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class ShowSetup:
    id: str
    title: str
    props: str
    action: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundChoice:
    id: str
    label: str
    line: str
    onomat: str
    tool: str
    intensity: int
    gentle_alt: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ListenerKind:
    id: str
    label: str
    phrase: str
    sensitivity: int
    comfort: str
    type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    soothe: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def scare_value(sound: SoundChoice, listener: ListenerKind) -> int:
    return sound.intensity - listener.sensitivity


def can_frighten(sound: SoundChoice, listener: ListenerKind) -> bool:
    return scare_value(sound, listener) >= 1


def sensible_repairs(sound: SoundChoice, listener: ListenerKind) -> list[Repair]:
    need = scare_value(sound, listener)
    return [r for r in REPAIRS.values() if r.soothe >= max(SOOTHE_MIN, need)]


def _r_fright(world: World) -> list[str]:
    sound = world.facts["sound_cfg"]
    listener_cfg = world.facts["listener_cfg"]
    listener = world.get("listener")
    maker = world.get("maker")
    if listener.meters["startled"] < THRESHOLD:
        return []
    sig = ("fright", sound.id, listener_cfg.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    listener.memes["fear"] += 1
    maker.memes["guilt"] += 1
    return ["__fright__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="fright", tag="social", apply=_r_fright),
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


def predict_fright(world: World, sound: SoundChoice, listener: ListenerKind) -> dict:
    sim = world.copy()
    sim.facts["sound_cfg"] = sound
    sim.facts["listener_cfg"] = listener
    sim.get("listener").meters["startled"] += 1
    propagate(sim, narrate=False)
    return {
        "frightened": sim.get("listener").memes["fear"] >= THRESHOLD and can_frighten(sound, listener),
        "fear": sim.get("listener").memes["fear"],
        "need": scare_value(sound, listener),
    }


def introduce(world: World, maker: Entity, helper: Entity, setup: ShowSetup) -> None:
    maker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After snack time, {maker.id} and {helper.id} made {setup.title} on the living room rug. "
        f"{setup.props}"
    )
    world.say(
        f"They wanted to {setup.action}, and {maker.id} had the extra job of adding the sound effects."
    )


def settle_listener(world: World, listener: Entity, listener_cfg: ListenerKind, parent: Entity) -> None:
    if listener_cfg.id == "baby":
        world.say(
            f"Nearby, {listener.id}, {parent.label_word}'s {listener_cfg.label}, was sitting in a soft blanket basket."
        )
    elif listener_cfg.id == "cat":
        world.say(
            f"Nearby, {listener.id}, the family {listener_cfg.label}, was curled in a sunny patch on the sofa."
        )
    else:
        world.say(
            f"Nearby, {listener.id}, the little {listener_cfg.label}, was lining up blocks by the coffee table."
        )


def choose_sound(world: World, maker: Entity, sound: SoundChoice) -> None:
    maker.memes["pride"] += 1
    world.say(
        f'"I know what this part needs," said {maker.id}. "{sound.line}"'
    )
    world.say(
        f"{maker.pronoun().capitalize()} lifted {sound.tool}, ready to dub the big moment."
    )


def caution(world: World, helper: Entity, maker: Entity, listener: Entity,
            sound: SoundChoice, listener_cfg: ListenerKind, parent: Entity) -> None:
    pred = predict_fright(world, sound, listener_cfg)
    world.facts["predicted_need"] = pred["need"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} glanced at {listener.id}. "{listener.id} is right here," '
        f'{helper.pronoun()} said. "That sound might frighten {listener.pronoun("object")}."'
    )
    if pred["need"] >= 2:
        world.say(
            f'{parent.label_word.capitalize()} nodded from the couch. "Big sounds can feel extra sudden to little ears," '
            f'{parent.pronoun()} said.'
        )


def boom(world: World, maker: Entity, listener: Entity, sound: SoundChoice) -> None:
    listener.meters["startled"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{sound.onomat} went the {sound.tool} as {maker.id} dubbed the scene.'
    )
    if listener.memes["fear"] >= THRESHOLD and can_frighten(world.facts["sound_cfg"], world.facts["listener_cfg"]):
        world.say(
            f"{listener.id} jumped, eyes wide, and the happy room suddenly felt too sharp."
        )


def comfort_fail(world: World, parent: Entity, maker: Entity, helper: Entity,
                 listener: Entity, listener_cfg: ListenerKind) -> None:
    listener.memes["fear"] += 1
    maker.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"{parent.label_word.capitalize()} opened {parent.pronoun('possessive')} arms, but {listener.id} was still trembling."
    )
    world.say(
        f"The show stopped. {maker.id} put {maker.pronoun('possessive')} hands in {maker.pronoun('possessive')} lap and wished "
        f"{maker.pronoun()} could take the sound back."
    )
    world.say(
        f"They spent the rest of the afternoon keeping the room quiet while {listener.id} held {listener_cfg.comfort} close."
    )


def repair_scene(world: World, parent: Entity, maker: Entity, helper: Entity,
                 listener: Entity, sound: SoundChoice, repair: Repair) -> None:
    listener.memes["fear"] = 0.0
    listener.memes["calm"] += 1
    maker.memes["relief"] += 1
    maker.memes["lesson"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came closer and {repair.text.format(listener=listener.id, alt=sound.gentle_alt)}"
    )
    world.say(
        f"{listener.id} blinked, then leaned in again when the next sound was small and soft."
    )
    world.say(
        f"{maker.id} listened carefully this time and smiled when {listener.id} stayed calm."
    )


def finish_show(world: World, maker: Entity, helper: Entity, setup: ShowSetup, sound: SoundChoice) -> None:
    maker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Soon the little show was moving again. They dubbed the last parts with {sound.gentle_alt}, and {setup.ending}"
    )


def tell(setup: ShowSetup, sound: SoundChoice, listener_cfg: ListenerKind,
         repair: Repair, maker_name: str = "Nora", maker_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    listener = world.add(
        Entity(
            id={"baby": "Milo", "cat": "Pebble", "toddler": "June"}[listener_cfg.id],
            kind="character" if listener_cfg.id != "cat" else "thing",
            type=listener_cfg.type,
            role="listener",
            label=listener_cfg.label,
            phrase=listener_cfg.phrase,
        )
    )

    world.facts.update(
        setup=setup,
        sound_cfg=sound,
        listener_cfg=listener_cfg,
        repair=repair,
        maker=maker,
        helper=helper,
        parent=parent,
        listener=listener,
    )

    introduce(world, maker, helper, setup)
    settle_listener(world, listener, listener_cfg, parent)

    world.para()
    choose_sound(world, maker, sound)
    caution(world, helper, maker, listener, sound, listener_cfg, parent)

    world.para()
    boom(world, maker, listener, sound)

    soothed = repair.soothe >= scare_value(sound, listener_cfg)
    world.para()
    if soothed:
        repair_scene(world, parent, maker, helper, listener, sound, repair)
        world.para()
        finish_show(world, maker, helper, setup, sound)
        outcome = "soothed"
    else:
        comfort_fail(world, parent, maker, helper, listener, listener_cfg)
        outcome = "tearful"

    world.facts.update(
        outcome=outcome,
        frightened=listener.memes["calm"] < THRESHOLD and listener.memes["fear"] >= THRESHOLD or outcome == "tearful",
        repaired=soothed,
        scare=scare_value(sound, listener_cfg),
    )
    return world


SHOWS = {
    "toy_train": ShowSetup(
        id="toy_train",
        title="a tiny train movie",
        props="A shoebox tunnel leaned against a stack of books, and a red wooden train waited on painter's tape tracks.",
        action="roll the train through the tunnel and past the paper station",
        ending="the train reached the station, and both children gave it a proud little clap",
        tags={"home", "toys"},
    ),
    "kitchen_band": ShowSetup(
        id="kitchen_band",
        title="a spoon-and-pan concert",
        props="A pot, a wooden spoon, and two upside-down bowls sat on a towel like a small stage.",
        action="play a make-believe concert for the family",
        ending="their concert ended with a bow so deep they nearly tipped over",
        tags={"music", "home"},
    ),
    "sock_dragon": ShowSetup(
        id="sock_dragon",
        title="a sock-dragon show",
        props="A striped sock puppet peeked over the arm of the couch, and a green blanket became a mountain.",
        action="make the dragon cross the blanket mountain and find a paper treasure",
        ending="the dragon found the treasure, and even its silly felt tongue seemed pleased",
        tags={"puppet", "home"},
    ),
}

SOUNDS = {
    "thunder_sheet": SoundChoice(
        id="thunder_sheet",
        label="thunder boom",
        line='I can dub a thunder boom right here!',
        onomat="BWOOM",
        tool="cookie sheet",
        intensity=3,
        gentle_alt="a finger-tapped rumble on the sofa cushion",
        tags={"sound_effects", "loud", "thunder"},
    ),
    "pan_crash": SoundChoice(
        id="pan_crash",
        label="crash bang",
        line='Let me dub a crash bang for the exciting part!',
        onomat="CLANG-CLASH",
        tool="metal pan",
        intensity=3,
        gentle_alt="a soft tap-tap with a wooden spoon",
        tags={"sound_effects", "loud", "crash"},
    ),
    "dragon_roar": SoundChoice(
        id="dragon_roar",
        label="dragon roar",
        line='I can dub the dragon with my biggest roar!',
        onomat="ROAAR",
        tool="own voice",
        intensity=2,
        gentle_alt="a low little rrrr like a sleepy dragon",
        tags={"sound_effects", "voice", "dragon"},
    ),
}

LISTENERS = {
    "baby": ListenerKind(
        id="baby",
        label="baby brother",
        phrase="a baby brother with round surprised eyes",
        sensitivity=1,
        comfort="his soft blanket",
        type="brother",
        tags={"baby", "family"},
    ),
    "toddler": ListenerKind(
        id="toddler",
        label="little cousin",
        phrase="a little cousin building block towers",
        sensitivity=1,
        comfort="her stuffed bunny",
        type="girl",
        tags={"toddler", "family"},
    ),
    "cat": ListenerKind(
        id="cat",
        label="cat",
        phrase="the family cat with twitchy ears",
        sensitivity=2,
        comfort="the warm sofa cushion",
        type="thing",
        tags={"cat", "pet"},
    ),
}

REPAIRS = {
    "soft_redub": Repair(
        id="soft_redub",
        label="soft re-dub",
        soothe=3,
        text='knelt beside {listener}, rubbed a small back, and said, "Let us try that part again with {alt} instead."',
        qa_text="They tried the scene again with a much softer sound effect.",
        tags={"gentle_sound", "redo"},
    ),
    "count_then_tap": Repair(
        id="count_then_tap",
        label="count and tap",
        soothe=2,
        text='held up a hand and said, "First we count to three, and then we make only a tiny sound."',
        qa_text="They warned the listener first and replaced the big noise with a tiny tap.",
        tags={"warning", "gentle_sound"},
    ),
    "hug_only": Repair(
        id="hug_only",
        label="just a hug",
        soothe=1,
        text='picked {listener} up for a cuddle, but the room was still waiting for the loud sound to happen again',
        qa_text="The grown-up only gave comfort, without changing the sound itself.",
        tags={"comfort"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for show_id in SHOWS:
        for sound_id, sound in SOUNDS.items():
            for listener_id, listener in LISTENERS.items():
                if can_frighten(sound, listener) and sensible_repairs(sound, listener):
                    combos.append((show_id, sound_id, listener_id))
    return combos


@dataclass
class StoryParams:
    show: str
    sound: str
    listener: str
    repair: str
    maker_name: str
    maker_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "sound_effects": [
        (
            "What are sound effects?",
            "Sound effects are sounds added to a story, show, or movie to help listeners imagine what is happening. They can be made with voices, hands, or everyday objects."
        )
    ],
    "dub": [
        (
            "What does it mean to dub a sound?",
            "To dub a sound means to add the sound to the story part on purpose. Someone makes or records the noise so the scene feels more alive."
        )
    ],
    "loud": [
        (
            "Why can a loud sound frighten someone?",
            "A loud sound can feel sudden and strong, especially to little ears. When a body is surprised too quickly, it may jump before it understands the sound is safe."
        )
    ],
    "baby": [
        (
            "Why do babies startle easily?",
            "Babies are still getting used to the world, so sudden lights and sounds can surprise them fast. Gentle voices and calm sounds help them feel safe."
        )
    ],
    "toddler": [
        (
            "Why might a little child get scared by a big noise?",
            "Little children do not always know a noise is pretend before they hear it. If the sound comes all at once, it can feel real for a moment."
        )
    ],
    "cat": [
        (
            "Why do cats jump at sudden noises?",
            "Cats have quick ears and notice sharp sounds right away. A sudden clang can make a cat spring away before it decides everything is fine."
        )
    ],
    "gentle_sound": [
        (
            "How can you make a pretend storm or crash more gently?",
            "You can tap softly, rub paper, or use a quiet voice instead of a bang. A gentle version still tells the story without hurting anyone's ears."
        )
    ],
    "warning": [
        (
            "Why does it help to warn someone before a sound?",
            "A warning gives the body a moment to get ready. Then the sound feels less surprising and less scary."
        )
    ],
}
KNOWLEDGE_ORDER = ["sound_effects", "dub", "loud", "baby", "toddler", "cat", "gentle_sound", "warning"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setup = f["setup"]
    sound = f["sound_cfg"]
    listener = f["listener_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short slice-of-life story for a 3-to-5-year-old about children making {setup.title} at home, '
        f'and include the words "dub" and "frighten".'
    )
    if outcome == "soothed":
        return [
            base,
            f"Tell a gentle story where a child tries to dub a {sound.label}, it almost frightens {listener.phrase}, and a grown-up helps them make the sound softer.",
            f"Write a cozy home story with sound effects, a brief scare, and a calm ending where the children finish their little show in a kinder way.",
        ]
    return [
        base,
        f"Tell a small cautionary story where the children choose a sound that is too big for {listener.phrase}, and the rest of the afternoon becomes quiet and careful.",
        f"Write a home story about pretend play, sound effects, and learning that exciting sounds should not frighten someone nearby.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    parent = f["parent"]
    listener = f["listener"]
    setup = f["setup"]
    sound = f["sound_cfg"]
    repair = f["repair"]
    parent_word = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.id} and {helper.id} making {setup.title} at home. A nearby listener, {listener.id}, also matters because the sound choices affect {listener.pronoun('object')}."
        ),
        (
            "What were the children doing?",
            f"They were putting on {setup.title} and trying to dub the sound effects themselves. The project started as an ordinary, happy home activity on the living room rug."
        ),
        (
            f"What sound did {maker.id} want to dub?",
            f"{maker.id} wanted to dub a {sound.label}. {maker.pronoun().capitalize()} thought the big sound would make the exciting part feel more real."
        ),
        (
            f"Why did {helper.id} and {parent_word} worry about the sound?",
            f"They saw that {listener.id} was very close by, and they knew a sudden loud sound could frighten {listener.pronoun('object')}. The worry came from who was in the room, not from the show itself."
        ),
    ]
    if f["outcome"] == "soothed":
        qa.extend(
            [
                (
                    f"What happened when the loud sound was made?",
                    f"{listener.id} jumped because the sound came suddenly and felt too sharp. That quick reaction showed the children that their pretend effect was real enough to scare someone nearby."
                ),
                (
                    f"How did {parent_word} help fix the problem?",
                    f"{parent_word.capitalize()} stepped in calmly and changed the way the sound was made. {repair.qa_text} That solved the real problem because the new sound no longer overwhelmed {listener.id}."
                ),
                (
                    "How did the story end?",
                    f"The children finished the show with gentler sound effects, and the room felt calm again. The ending proves they learned that a fun show should not frighten the people listening."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    "What happened after the loud sound?",
                    f"{listener.id} stayed upset, so the show had to stop. The problem lasted because comfort alone did not change the too-big sound choice."
                ),
                (
                    "How did the story end?",
                    f"The afternoon turned quiet while everyone helped {listener.id} feel safe again. The ending shows that exciting play has to pause when a sound is strong enough to frighten someone."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sound_effects", "dub", "loud"} | set(world.facts["listener_cfg"].tags) | set(world.facts["repair"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        show="toy_train",
        sound="thunder_sheet",
        listener="baby",
        repair="soft_redub",
        maker_name="Nora",
        maker_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        show="sock_dragon",
        sound="dragon_roar",
        listener="cat",
        repair="count_then_tap",
        maker_name="Mia",
        maker_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        parent="father",
    ),
    StoryParams(
        show="kitchen_band",
        sound="pan_crash",
        listener="toddler",
        repair="soft_redub",
        maker_name="Sam",
        maker_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        parent="mother",
    ),
    StoryParams(
        show="sock_dragon",
        sound="thunder_sheet",
        listener="baby",
        repair="hug_only",
        maker_name="Ella",
        maker_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="father",
    ),
]


def explain_rejection(sound: SoundChoice, listener: ListenerKind) -> str:
    if not can_frighten(sound, listener):
        return (
            f"(No story: {sound.label} is not strong enough to plausibly frighten a nearby {listener.label}. "
            f"This world only tells cases where the sound choice creates a real small problem.)"
        )
    if not sensible_repairs(sound, listener):
        return (
            f"(No story: none of the repair methods in this world would truly calm a {listener.label} after a {sound.label}. "
            f"Pick a listener or sound with a believable gentle fix.)"
        )
    return "(No story: this combination does not form a reasonable everyday problem.)"


def explain_repair(sound_id: str, listener_id: str, repair_id: str) -> str:
    sound = SOUNDS[sound_id]
    listener = LISTENERS[listener_id]
    repair = REPAIRS[repair_id]
    need = scare_value(sound, listener)
    return (
        f"(Refusing repair '{repair_id}': it is too weak for a {sound.label} near a {listener.label} "
        f"(soothe={repair.soothe}, need={need}). Pick a repair that actually changes the sound enough.)"
    )


ASP_RULES = r"""
% A listener is plausibly frightened when the sound's intensity is greater than
% the listener's tolerance.
frightens(S, L) :- sound(S), listener(L), intensity(S, I), sensitivity(L, T), I > T.
need(S, L, N)   :- frightens(S, L), intensity(S, I), sensitivity(L, T), N = I - T.

% A repair is sensible when it is strong enough both for the world's minimum
% standard and for the actual scare level.
strong_enough(R, S, L) :- repair(R), need(S, L, N), soothe(R, V), V >= N.
sensible_repair(R, S, L) :- strong_enough(R, S, L), soothe_min(M), soothe(R, V), V >= M.

valid(Show, S, L) :- show(Show), frightens(S, L), sensible_repair(_, S, L).

outcome(soothed) :- chosen_sound(S), chosen_listener(L), chosen_repair(R),
                    frightens(S, L), need(S, L, N), soothe(R, V), V >= N.
outcome(tearful) :- chosen_sound(S), chosen_listener(L), chosen_repair(R),
                    frightens(S, L), need(S, L, N), soothe(R, V), V < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for show_id in SHOWS:
        lines.append(asp.fact("show", show_id))
    for sound_id, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sound_id))
        lines.append(asp.fact("intensity", sound_id, sound.intensity))
    for listener_id, listener in LISTENERS.items():
        lines.append(asp.fact("listener", listener_id))
        lines.append(asp.fact("sensitivity", listener_id, listener.sensitivity))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("soothe", repair_id, repair.soothe))
    lines.append(asp.fact("soothe_min", SOOTHE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_sound", params.sound),
            asp.fact("chosen_listener", params.listener),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    sound = SOUNDS[params.sound]
    listener = LISTENERS[params.listener]
    repair = REPAIRS[params.repair]
    return "soothed" if repair.soothe >= scare_value(sound, listener) else "tearful"


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

    cases: list[StoryParams] = list(CURATED)
    rng = random.Random(17)
    parser = build_parser()
    for _ in range(20):
        try:
            params = resolve_params(parser.parse_args([]), rng)
            cases.append(params)
        except StoryError:
            rc = 1
            print("Unexpected StoryError during resolve_params smoke generation.")
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
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: children dub sound effects, a loud choice can frighten someone nearby, and they learn a gentler way."
    )
    ap.add_argument("--show", choices=SHOWS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--listener", choices=LISTENERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


GIRL_NAMES = ["Nora", "Mia", "Ella", "Ava", "Lucy", "Rose", "Zoe", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Eli", "Theo", "Jack"]


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.listener:
        sound = SOUNDS[args.sound]
        listener = LISTENERS[args.listener]
        if not can_frighten(sound, listener):
            raise StoryError(explain_rejection(sound, listener))
    combos = [
        c for c in valid_combos()
        if (args.show is None or c[0] == args.show)
        and (args.sound is None or c[1] == args.sound)
        and (args.listener is None or c[2] == args.listener)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    show_id, sound_id, listener_id = rng.choice(sorted(combos))
    sound = SOUNDS[sound_id]
    listener = LISTENERS[listener_id]

    if args.repair is not None:
        if REPAIRS[args.repair].soothe < scare_value(sound, listener):
            raise StoryError(explain_repair(sound_id, listener_id, args.repair))
        repair_id = args.repair
    else:
        repair_id = rng.choice(sorted(r.id for r in sensible_repairs(sound, listener)))

    maker_name, maker_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=maker_name)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        show=show_id,
        sound=sound_id,
        listener=listener_id,
        repair=repair_id,
        maker_name=maker_name,
        maker_gender=maker_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.show not in SHOWS:
        raise StoryError(f"(Invalid show: {params.show})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Invalid sound: {params.sound})")
    if params.listener not in LISTENERS:
        raise StoryError(f"(Invalid listener: {params.listener})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Invalid repair: {params.repair})")

    sound = SOUNDS[params.sound]
    listener = LISTENERS[params.listener]
    repair = REPAIRS[params.repair]

    if not can_frighten(sound, listener):
        raise StoryError(explain_rejection(sound, listener))
    if repair.soothe < scare_value(sound, listener):
        raise StoryError(explain_repair(params.sound, params.listener, params.repair))

    world = tell(
        setup=SHOWS[params.show],
        sound=sound,
        listener_cfg=listener,
        repair=repair,
        maker_name=params.maker_name,
        maker_gender=params.maker_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (show, sound, listener) combos:\n")
        for show_id, sound_id, listener_id in combos:
            print(f"  {show_id:12} {sound_id:14} {listener_id}")
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
            header = f"### {p.maker_name} and {p.helper_name}: {p.show}, {p.sound}, {p.listener}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
