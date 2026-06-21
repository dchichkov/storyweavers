#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jug_reconciliation_happy_ending_suspense_ghost_story.py
===================================================================================

A small storyworld for gentle ghost-story suspense around a missing jug.

Premise
-------
Two children fall out after an old jug goes missing. That night, a spooky sound
comes from a dark place in the house. The children creep closer with a grown-up,
expecting a ghost. Instead they discover an ordinary cause: wind, drips, or a
tiny mouse making the jug sound eerie. The truth untangles the misunderstanding,
one child apologizes, and the story ends in reconciliation.

Run it
------
python storyworlds/worlds/gpt-5.4/jug_reconciliation_happy_ending_suspense_ghost_story.py
python storyworlds/worlds/gpt-5.4/jug_reconciliation_happy_ending_suspense_ghost_story.py --setting attic --cause wind_whistle
python storyworlds/worlds/gpt-5.4/jug_reconciliation_happy_ending_suspense_ghost_story.py --light candle
python storyworlds/worlds/gpt-5.4/jug_reconciliation_happy_ending_suspense_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/jug_reconciliation_happy_ending_suspense_ghost_story.py --qa --json
python storyworlds/worlds/gpt-5.4/jug_reconciliation_happy_ending_suspense_ghost_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
SOFTHEARTED_TRAITS = {"gentle", "softhearted", "honest", "careful"}


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    place_phrase: str
    opening: str
    dark_detail: str
    ending_image: str
    breezy: bool = False
    drippy: bool = False
    mousey: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class JugConfig:
    id: str
    label: str
    phrase: str
    color: str
    chipped: bool = False
    open_mouth: bool = True
    handle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    sound: str
    reveal: str
    qa_cause: str
    needs_breezy: bool = False
    needs_drippy: bool = False
    needs_mousey: bool = False
    needs_chipped: bool = False
    needs_open: bool = False
    needs_handle: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    sense: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"accuser", "friend"}]

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


def _r_spooky_sound(world: World) -> list[str]:
    jug = world.get("jug")
    if jug.meters["sounding"] < THRESHOLD:
        return []
    sig = ("spooky_sound",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("room").meters["tension"] += 1
    return ["__spooky__"]


def _r_peace(world: World) -> list[str]:
    a = world.get("accuser")
    b = world.get("friend")
    if a.memes["sorry"] < THRESHOLD or b.memes["forgive"] < THRESHOLD:
        return []
    sig = ("peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["peace"] += 1
    b.memes["peace"] += 1
    a.memes["guilt"] = 0.0
    b.memes["hurt"] = 0.0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="spooky_sound", tag="emotional", apply=_r_spooky_sound),
    Rule(name="peace", tag="social", apply=_r_peace),
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


SETTINGS = {
    "attic": Setting(
        id="attic",
        label="attic",
        place_phrase="the attic",
        opening="Upstairs, the attic sat above the house with slanty beams and old trunks.",
        dark_detail="The moon made thin stripes across the floorboards, and every board seemed ready to creak.",
        ending_image="The attic no longer felt haunted; it felt like a high, dusty room full of sleepy moonlight.",
        breezy=True,
        drippy=True,
        mousey=False,
        tags={"attic", "dark_house"},
    ),
    "porch": Setting(
        id="porch",
        label="back porch",
        place_phrase="the back porch",
        opening="Out back, the porch held a row of boots, flowerpots, and the night wind.",
        dark_detail="The dark garden pressed up against the steps, and the porch boards gave small sighs in the breeze.",
        ending_image="The porch looked friendly again, with night air moving softly through the railings.",
        breezy=True,
        drippy=False,
        mousey=False,
        tags={"porch", "night"},
    ),
    "pantry": Setting(
        id="pantry",
        label="pantry",
        place_phrase="the pantry",
        opening="Near the kitchen, the pantry was lined with shelves and sleepy jars.",
        dark_detail="The little room was dark except for a sliver of light under the door, and every shelf made thick shadows.",
        ending_image="The pantry smelled of oats and apples, and not one corner seemed spooky anymore.",
        breezy=False,
        drippy=True,
        mousey=True,
        tags={"pantry", "night"},
    ),
}

JUGS = {
    "blue_water_jug": JugConfig(
        id="blue_water_jug",
        label="blue jug",
        phrase="an old blue water jug",
        color="blue",
        chipped=True,
        open_mouth=True,
        handle=True,
        tags={"jug", "blue"},
    ),
    "cream_milk_jug": JugConfig(
        id="cream_milk_jug",
        label="cream jug",
        phrase="a creamy white milk jug",
        color="cream",
        chipped=False,
        open_mouth=True,
        handle=True,
        tags={"jug", "cream"},
    ),
    "painted_flower_jug": JugConfig(
        id="painted_flower_jug",
        label="painted jug",
        phrase="a painted flower jug",
        color="green",
        chipped=True,
        open_mouth=True,
        handle=True,
        tags={"jug", "flowers"},
    ),
}

CAUSES = {
    "wind_whistle": Cause(
        id="wind_whistle",
        sound="an oo-oo sound, thin as a ghost breathing through its teeth",
        reveal="the night wind was slipping across the chipped rim of the jug and making it sing",
        qa_cause="Wind skimmed over the chipped rim of the jug and made a long whistling note.",
        needs_breezy=True,
        needs_chipped=True,
        tags={"wind", "ghost_sound"},
    ),
    "drip_plink": Cause(
        id="drip_plink",
        sound="a slow plink... plink... plink, as if invisible fingers were tapping from inside",
        reveal="a tiny leak overhead was dropping water into the empty jug one silver drop at a time",
        qa_cause="A little leak was dripping into the empty jug, so each drop made a spooky plink.",
        needs_drippy=True,
        needs_open=True,
        tags={"water", "ghost_sound"},
    ),
    "mouse_tap": Cause(
        id="mouse_tap",
        sound="a nervous clink-clink, followed by a rustle that stopped whenever anyone held still",
        reveal="a tiny mouse was nosing a spoon against the jug's handle while it searched for oats",
        qa_cause="A little mouse kept nudging a spoon against the jug's handle, which made the clinking sound.",
        needs_mousey=True,
        needs_handle=True,
        tags={"mouse", "ghost_sound"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on with a steady white circle",
        sense=3,
        tags={"flashlight", "safe_light"},
    ),
    "lantern": Light(
        id="lantern",
        label="camp lantern",
        phrase="a camping lantern",
        glow="glowed warm and round in the dark",
        sense=3,
        tags={"lantern", "safe_light"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="clip-on night-light",
        phrase="a clip-on night-light",
        glow="made a small pearly pool of light",
        sense=2,
        tags={"nightlight", "safe_light"},
    ),
    "candle": Light(
        id="candle",
        label="candle",
        phrase="a candle",
        glow="flickered with a real flame",
        sense=1,
        tags={"candle"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["gentle", "stormy", "honest", "careful", "softhearted", "quick-worried"]


def cause_fits(setting: Setting, jug: JugConfig, cause: Cause) -> bool:
    if cause.needs_breezy and not setting.breezy:
        return False
    if cause.needs_drippy and not setting.drippy:
        return False
    if cause.needs_mousey and not setting.mousey:
        return False
    if cause.needs_chipped and not jug.chipped:
        return False
    if cause.needs_open and not jug.open_mouth:
        return False
    if cause.needs_handle and not jug.handle:
        return False
    return True


def sensible_lights() -> list[Light]:
    return [light for light in LIGHTS.values() if light.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for jug_id, jug in JUGS.items():
            for cause_id, cause in CAUSES.items():
                if cause_fits(setting, jug, cause):
                    combos.append((setting_id, jug_id, cause_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    jug: str
    cause: str
    light: str
    helper: str
    accuser: str
    accuser_gender: str
    friend: str
    friend_gender: str
    relation: str
    trait: str
    seed: Optional[int] = None


def setup_day(world: World, a: Entity, b: Entity, helper: Entity, setting: Setting, jug_cfg: JugConfig) -> None:
    jug = world.get("jug")
    a.memes["trust"] = 4.0
    b.memes["trust"] = 4.0
    world.say(
        f"{a.id} and {b.id} loved helping {helper.label_word} with old, interesting things, "
        f"especially {jug_cfg.phrase} with its {jug_cfg.color} shine."
    )
    world.say(setting.opening)
    world.say(
        f"That afternoon they wanted the jug for moonflowers and pretend potions, but when they looked up, "
        f"the shelf was empty."
    )
    world.say(
        f'{a.id} frowned at once. "Did you hide the jug?" {a.pronoun()} asked.'
    )
    b.memes["hurt"] += 1
    a.memes["suspicion"] += 1
    world.say(
        f'{b.id} stared back. "No," {b.pronoun()} said, and the warm part of the day went cold between them.'
    )


def night_falls(world: World, setting: Setting) -> None:
    world.para()
    world.say(
        "That night, the house grew still enough for tiny noises to matter."
    )
    world.say(setting.dark_detail)


def awaken_sound(world: World, setting: Setting, cause: Cause) -> None:
    jug = world.get("jug")
    jug.meters["sounding"] += 1
    jug.meters["found"] += 1
    world.facts["sound_text"] = cause.sound
    world.say(
        f"Then, from {setting.place_phrase}, they heard {cause.sound}."
    )
    propagate(world, narrate=False)


def fear_reaction(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"{a.id} grabbed {b.id}'s sleeve. The two of them listened so hard that even their breathing seemed noisy."
    )
    world.say(
        f'For one frightened moment, neither child said the word ghost, but both of them were thinking it.'
    )


def fetch_light(world: World, helper: Entity, light: Light) -> None:
    world.para()
    world.say(
        f"{helper.label_word.capitalize()} came out in slippers with {light.phrase} that {light.glow}."
    )
    world.say(
        f'"Let us look before we decide what it is," {helper.pronoun()} said softly.'
    )


def walk_to_sound(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    pair = "side by side" if world.facts.get("relation") == "friends" else "shoulder to shoulder"
    world.say(
        f"They walked toward {setting.place_phrase} {pair}, though each child wished the other would go first."
    )


def discover(world: World, helper: Entity, cause: Cause, jug_cfg: JugConfig, setting: Setting) -> None:
    jug = world.get("jug")
    jug.meters["discovered"] += 1
    world.say(
        f"The light reached the shelf, and there sat the {jug_cfg.label}."
    )
    world.say(
        f"It was not a ghost at all. {cause.reveal}."
    )
    world.say(
        f'"I put the jug here after washing it," {helper.label_word} explained. '
        f'"I wanted it safe and dry, and I forgot to tell you."'
    )
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.get("room").meters["tension"] = 0.0
    world.facts["discovery"] = cause.qa_cause
    world.facts["setting_phrase"] = setting.place_phrase


def apologize(world: World, a: Entity, b: Entity, trait: str) -> None:
    a.memes["guilt"] += 1
    a.memes["sorry"] += 1
    if trait in SOFTHEARTED_TRAITS:
        line = (
            f'{a.id} looked at {b.id} right away. "I am sorry," {a.pronoun()} whispered. '
            f'"I should not have blamed you for the missing jug."'
        )
    else:
        line = (
            f'{a.id} swallowed hard, then said, "I was wrong. I blamed you for the jug, '
            f'and I am sorry."'
        )
    world.para()
    world.say(line)


def forgive(world: World, b: Entity, a: Entity) -> None:
    b.memes["forgive"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{b.id} nodded and moved closer. "I did feel hurt," {b.pronoun()} said, '
        f'"but I know you were scared and upset."'
    )
    world.say(
        f"Then {b.id} slipped a hand into {a.id}'s, and the quarrel finally let go."
    )


def ending(world: World, a: Entity, b: Entity, helper: Entity, jug_cfg: JugConfig, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.para()
    world.say(
        f"Together they carried the {jug_cfg.label} downstairs and set moonflowers inside it."
    )
    world.say(
        f"The pale petals opened in the kitchen light while {helper.label_word} smiled over their heads."
    )
    world.say(
        f"{setting.ending_image} The children were not whispering about ghosts anymore. They were talking to each other again."
    )


def tell(
    setting: Setting,
    jug_cfg: JugConfig,
    cause: Cause,
    light: Light,
    helper_type: str,
    accuser_name: str,
    accuser_gender: str,
    friend_name: str,
    friend_gender: str,
    relation: str,
    trait: str,
) -> World:
    world = World()
    a = world.add(Entity(
        id="accuser",
        kind="character",
        type=accuser_gender,
        label=accuser_name,
        role="accuser",
        traits=[trait],
    ))
    b = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["patient"],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        role="helper",
    ))
    world.add(Entity(id="room", type="room", label=setting.label))
    world.add(Entity(
        id="jug",
        type="jug",
        label=jug_cfg.label,
        phrase=jug_cfg.phrase,
        tags=set(jug_cfg.tags),
        attrs={"color": jug_cfg.color},
    ))

    world.facts["relation"] = relation
    world.facts["accuser_name"] = accuser_name
    world.facts["friend_name"] = friend_name
    world.facts["helper_word"] = helper.label_word
    world.facts["light"] = light
    world.facts["setting"] = setting
    world.facts["jug_cfg"] = jug_cfg
    world.facts["cause"] = cause
    world.facts["trait"] = trait

    setup_day(world, a, b, helper, setting, jug_cfg)
    night_falls(world, setting)
    awaken_sound(world, setting, cause)
    fear_reaction(world, a, b)
    fetch_light(world, helper, light)
    walk_to_sound(world, a, b, setting)
    discover(world, helper, cause, jug_cfg, setting)
    apologize(world, a, b, trait)
    forgive(world, b, a)
    ending(world, a, b, helper, jug_cfg, setting)

    world.facts["accuser"] = a
    world.facts["friend"] = b
    world.facts["helper"] = helper
    world.facts["peace"] = a.memes["peace"] >= THRESHOLD and b.memes["peace"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "jug": [
        ("What is a jug?", "A jug is a container with a handle and a mouth for pouring water, milk, or flowers into and out of it."),
    ],
    "wind": [
        ("Why can wind make a spooky sound?", "Wind can whistle when it slides past a narrow edge or opening. The noise can sound strange in the dark even when nothing scary is there."),
    ],
    "water": [
        ("Why do drips sound loud at night?", "At night everything is quieter, so a single drip can seem much louder than it does in the daytime."),
    ],
    "mouse": [
        ("Can a tiny mouse make a big-sounding noise?", "Yes. A little mouse can bump spoons, jars, or paper, and those hard things can make clinks that sound bigger than the mouse really is."),
    ],
    "flashlight": [
        ("Why is a flashlight good for the dark?", "A flashlight gives bright light without a flame. It helps you look carefully and stay safe."),
    ],
    "lantern": [
        ("What does a camping lantern do?", "A camping lantern glows all around, so people can see in the dark without using fire."),
    ],
    "nightlight": [
        ("What is a night-light for?", "A night-light makes a small, gentle light. It helps dark places feel easier to see."),
    ],
    "ghost_sound": [
        ("Why can ordinary things sound spooky?", "In the dark, your ears may notice a sound before your eyes can explain it. When you look carefully, the sound often comes from something ordinary."),
    ],
    "apology": [
        ("What does an apology do?", "An apology tells someone you know you hurt them and wish you had acted better. It helps begin fixing a friendship."),
    ],
    "forgiveness": [
        ("What is forgiveness?", "Forgiveness is choosing to let kindness grow again after someone says sorry. It does not erase the hurt, but it can help two people heal."),
    ],
}
KNOWLEDGE_ORDER = [
    "jug",
    "ghost_sound",
    "wind",
    "water",
    "mouse",
    "flashlight",
    "lantern",
    "nightlight",
    "apology",
    "forgiveness",
]


def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting"]
    cause = world.facts["cause"]
    jug_cfg = world.facts["jug_cfg"]
    a = world.facts["accuser"]
    b = world.facts["friend"]
    helper = world.facts["helper"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "jug", takes place near {setting.place_phrase}, and ends in reconciliation.',
        f"Tell a suspenseful but happy story where {a.label} wrongly blames {b.label} after a {jug_cfg.label} goes missing, and {helper.label_word} helps them discover that the spooky sound came from {cause.id.replace('_', ' ')}.",
        f"Write a child-facing ghost-style story with shadows, a missing jug, a frightening sound, an apology, and a warm ending where the children make peace.",
    ]


def relation_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    a = world.facts["accuser"]
    b = world.facts["friend"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    jug_cfg = world.facts["jug_cfg"]
    cause = world.facts["cause"]
    rel = world.facts["relation"]
    pair = relation_noun(a, b, rel)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, and their {helper.label_word} who helps them in the night. The children start the story upset with each other, then end it close again.",
        ),
        (
            "Why were the children upset before the spooky sound began?",
            f"The old {jug_cfg.label} was missing from its shelf, and {a.label} blamed {b.label} for hiding it. That accusation hurt {b.label}'s feelings and made the room between them feel cold.",
        ),
        (
            f"What did they hear from {setting.place_phrase}?",
            f"They heard {cause.sound}. In the quiet dark, that ordinary noise sounded ghostly before anyone knew what was making it.",
        ),
        (
            "What was really making the spooky sound?",
            f"{world.facts['discovery']} It seemed frightening only because they heard it first and understood it later.",
        ),
        (
            f"How did {helper.label_word} help?",
            f"{helper.label_word.capitalize()} brought {world.facts['light'].phrase} and led the children to look carefully instead of guessing. The light turned fear into understanding because it showed the jug and the real cause.",
        ),
        (
            f"How did {a.label} and {b.label} reconcile?",
            f"{a.label} apologized for blaming {b.label}, and {b.label} forgave {a.pronoun('object')}. They moved close again and carried the jug together, which proves the quarrel was over.",
        ),
        (
            "How did the story end?",
            f"It ended happily with moonflowers inside the jug and the children talking to each other again. The same place that had felt haunted now felt safe and gentle.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cause = world.facts["cause"]
    light = world.facts["light"]
    tags = {"jug", "ghost_sound", "apology", "forgiveness"} | set(cause.tags) | set(light.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic",
        jug="blue_water_jug",
        cause="wind_whistle",
        light="flashlight",
        helper="grandmother",
        accuser="Lily",
        accuser_gender="girl",
        friend="Tom",
        friend_gender="boy",
        relation="siblings",
        trait="gentle",
    ),
    StoryParams(
        setting="pantry",
        jug="cream_milk_jug",
        cause="drip_plink",
        light="lantern",
        helper="mother",
        accuser="Max",
        accuser_gender="boy",
        friend="Mia",
        friend_gender="girl",
        relation="friends",
        trait="careful",
    ),
    StoryParams(
        setting="pantry",
        jug="painted_flower_jug",
        cause="mouse_tap",
        light="nightlight",
        helper="father",
        accuser="Zoe",
        accuser_gender="girl",
        friend="Ava",
        friend_gender="girl",
        relation="siblings",
        trait="stormy",
    ),
    StoryParams(
        setting="porch",
        jug="painted_flower_jug",
        cause="wind_whistle",
        light="lantern",
        helper="grandmother",
        accuser="Ben",
        accuser_gender="boy",
        friend="Sam",
        friend_gender="boy",
        relation="friends",
        trait="honest",
    ),
]


def explain_rejection(setting: Setting, jug: JugConfig, cause: Cause) -> str:
    reasons: list[str] = []
    if cause.needs_breezy and not setting.breezy:
        reasons.append(f"{setting.place_phrase} is not breezy enough for the jug to whistle")
    if cause.needs_drippy and not setting.drippy:
        reasons.append(f"{setting.place_phrase} has no little leak for drips")
    if cause.needs_mousey and not setting.mousey:
        reasons.append(f"{setting.place_phrase} is not a sensible place for a mouse-and-spoon clink")
    if cause.needs_chipped and not jug.chipped:
        reasons.append(f"the {jug.label} has no chipped rim for the wind to sing across")
    if cause.needs_open and not jug.open_mouth:
        reasons.append(f"the {jug.label} is not open for drips to plink into")
    if cause.needs_handle and not jug.handle:
        reasons.append(f"the {jug.label} has no handle for a spoon to tap")
    if not reasons:
        reasons.append("this combination does not make a believable spooky sound")
    return "(No story: " + "; ".join(reasons) + ".)"


def explain_light(light_id: str) -> str:
    light = LIGHTS[light_id]
    better = ", ".join(sorted(l.id for l in sensible_lights()))
    return (
        f"(Refusing light '{light_id}': it scores too low on common sense "
        f"(sense={light.sense} < {SENSE_MIN}). A gentle ghost story should use a safe light. "
        f"Try: {better}.)"
    )


ASP_RULES = r"""
valid(S, J, C) :- setting(S), jug(J), cause(C),
                  fits_setting(S, C), fits_jug(J, C).

fits_setting(S, C) :- not need_breezy(C), not need_drippy(C), not need_mousey(C), setting(S).
fits_setting(S, C) :- need_breezy(C), breezy(S), not need_drippy(C), not need_mousey(C).
fits_setting(S, C) :- need_drippy(C), drippy(S), not need_breezy(C), not need_mousey(C).
fits_setting(S, C) :- need_mousey(C), mousey(S), not need_breezy(C), not need_drippy(C).
fits_setting(S, C) :- need_breezy(C), need_drippy(C), breezy(S), drippy(S), not need_mousey(C).

fits_jug(J, C) :- jug(J), cause(C),
                  not need_chipped(C), not need_open(C), not need_handle(C).
fits_jug(J, C) :- need_chipped(C), chipped(J), not need_open(C), not need_handle(C).
fits_jug(J, C) :- need_open(C), open_mouth(J), not need_chipped(C), not need_handle(C).
fits_jug(J, C) :- need_handle(C), handle(J), not need_chipped(C), not need_open(C).
fits_jug(J, C) :- need_chipped(C), need_open(C), chipped(J), open_mouth(J), not need_handle(C).
fits_jug(J, C) :- need_chipped(C), need_handle(C), chipped(J), handle(J), not need_open(C).
fits_jug(J, C) :- need_open(C), need_handle(C), open_mouth(J), handle(J), not need_chipped(C).
fits_jug(J, C) :- need_chipped(C), need_open(C), need_handle(C), chipped(J), open_mouth(J), handle(J).

sensible_light(L) :- light(L), sense(L, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.breezy:
            lines.append(asp.fact("breezy", setting_id))
        if setting.drippy:
            lines.append(asp.fact("drippy", setting_id))
        if setting.mousey:
            lines.append(asp.fact("mousey", setting_id))
    for jug_id, jug in JUGS.items():
        lines.append(asp.fact("jug", jug_id))
        if jug.chipped:
            lines.append(asp.fact("chipped", jug_id))
        if jug.open_mouth:
            lines.append(asp.fact("open_mouth", jug_id))
        if jug.handle:
            lines.append(asp.fact("handle", jug_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        if cause.needs_breezy:
            lines.append(asp.fact("need_breezy", cause_id))
        if cause.needs_drippy:
            lines.append(asp.fact("need_drippy", cause_id))
        if cause.needs_mousey:
            lines.append(asp.fact("need_mousey", cause_id))
        if cause.needs_chipped:
            lines.append(asp.fact("need_chipped", cause_id))
        if cause.needs_open:
            lines.append(asp.fact("need_open", cause_id))
        if cause.needs_handle:
            lines.append(asp.fact("need_handle", cause_id))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("sense", light_id, light.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_lights() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible_light/1."))
    return sorted(light for (light,) in asp.atoms(model, "sensible_light"))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    python_lights = {light.id for light in sensible_lights()}
    clingo_lights = set(asp_sensible_lights())
    if python_lights == clingo_lights:
        print(f"OK: sensible lights match ({sorted(python_lights)}).")
    else:
        rc = 1
        print("MISMATCH in sensible lights:")
        print("  python:", sorted(python_lights))
        print("  clingo:", sorted(clingo_lights))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params() raised {err!r}")

    for params in smoke_cases[:3]:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            with redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header="### smoke")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL: generate/emit crashed for {params}: {err!r}")
            break

    if rc == 0:
        print("OK: smoke generation and emit passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a missing jug, a spooky sound, and a reconciled friendship."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--jug", choices=JUGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.light and LIGHTS[args.light].sense < SENSE_MIN:
        raise StoryError(explain_light(args.light))
    if args.setting and args.jug and args.cause:
        setting = SETTINGS[args.setting]
        jug = JUGS[args.jug]
        cause = CAUSES[args.cause]
        if not cause_fits(setting, jug, cause):
            raise StoryError(explain_rejection(setting, jug, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.jug is None or combo[1] == args.jug)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, jug_id, cause_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(light.id for light in sensible_lights()))
    helper = args.helper or rng.choice(["mother", "father", "grandmother"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    accuser_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    accuser = _pick_name(rng, accuser_gender)
    friend = _pick_name(rng, friend_gender, avoid=accuser)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        jug=jug_id,
        cause=cause_id,
        light=light_id,
        helper=helper,
        accuser=accuser,
        accuser_gender=accuser_gender,
        friend=friend,
        friend_gender=friend_gender,
        relation=relation,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        jug = JUGS[params.jug]
        cause = CAUSES[params.cause]
        light = LIGHTS[params.light]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]}.)") from None

    if light.sense < SENSE_MIN:
        raise StoryError(explain_light(params.light))
    if not cause_fits(setting, jug, cause):
        raise StoryError(explain_rejection(setting, jug, cause))

    world = tell(
        setting=setting,
        jug_cfg=jug,
        cause=cause,
        light=light,
        helper_type=params.helper,
        accuser_name=params.accuser,
        accuser_gender=params.accuser_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        relation=params.relation,
        trait=params.trait,
    )

    story_text = world.render().replace("accuser", params.accuser).replace("friend", params.friend)
    story_text = story_text.replace("helper", world.facts["helper_word"])
    story_text = story_text.replace("  ", " ")

    story_text = story_text.replace("accuser", params.accuser)
    story_text = story_text.replace("friend", params.friend)
    story_text = story_text.replace(' "I am sorry," she whispered.', ' "I am sorry," she whispered.')
    story_text = story_text.replace(' "I am sorry," he whispered.', ' "I am sorry," he whispered.')

    story_text = story_text.replace(world.get("accuser").id, params.accuser)
    story_text = story_text.replace(world.get("friend").id, params.friend)

    # The world stores internal ids; the child-facing story uses the labels.
    for internal_id, label in [("accuser", params.accuser), ("friend", params.friend), ("helper", world.facts["helper_word"].capitalize())]:
        story_text = story_text.replace(internal_id, label)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("#show valid/3.\n#show sensible_light/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        lights = asp_sensible_lights()
        print(f"sensible lights: {', '.join(lights)}\n")
        print(f"{len(combos)} compatible (setting, jug, cause) combos:\n")
        for setting_id, jug_id, cause_id in combos:
            print(f"  {setting_id:8} {jug_id:18} {cause_id}")
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
            header = f"### {p.accuser} & {p.friend}: {p.jug} in {p.setting} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
