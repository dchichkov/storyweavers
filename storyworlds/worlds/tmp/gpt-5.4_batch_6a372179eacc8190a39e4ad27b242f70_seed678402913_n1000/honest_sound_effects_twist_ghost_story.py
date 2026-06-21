#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/honest_sound_effects_twist_ghost_story.py
====================================================================

A standalone storyworld for a gentle ghost-story-shaped tale with a twist:
a child hears spooky night sounds, imagines a ghost, then chooses to be honest
about being scared. A calm grown-up investigates with the child and reveals an
ordinary cause. The ending image proves what changed: the same sound is no
longer frightening once it is understood.

This world keeps its schema deliberately small and conservative:
one shared Entity dataclass, a few config dataclasses, a forward-chaining rule
or two, and a reasonableness gate mirrored by an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/honest_sound_effects_twist_ghost_story.py
    python storyworlds/worlds/gpt-5.4/honest_sound_effects_twist_ghost_story.py --place attic --source rocking_chair
    python storyworlds/worlds/gpt-5.4/honest_sound_effects_twist_ghost_story.py --place cellar --source curtain
    python storyworlds/worlds/gpt-5.4/honest_sound_effects_twist_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/honest_sound_effects_twist_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/honest_sound_effects_twist_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 4.0


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
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    spooky_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound1: str
    sound2: str
    action: str
    reveal: str
    ending_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    entry: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_sound_spreads(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    house = world.entities.get("house")
    child = world.entities.get("child")
    if source is None or house is None or child is None:
        return out
    if source.meters["rattling"] < THRESHOLD:
        return out
    sig = ("sound_spreads",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    house.meters["noise"] += 1
    child.memes["fear"] += 1
    out.append("__spooky__")
    return out


def _r_honesty_brings_help(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if child is None or helper is None:
        return out
    if child.memes["honesty"] < THRESHOLD:
        return out
    sig = ("honesty_brings_help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["care"] += 1
    child.memes["trust"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [
    Rule(name="sound_spreads", tag="physical", apply=_r_sound_spreads),
    Rule(name="honesty_brings_help", tag="social", apply=_r_honesty_brings_help),
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


PLACES = {
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the long hallway outside the bedrooms",
        spooky_detail="The floorboards there always seemed to remember every step.",
        tags={"house", "hallway"},
    ),
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the little attic above the stairs",
        spooky_detail="The slanted ceiling and old shadows made it feel like a place that kept secrets.",
        tags={"house", "attic"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the back porch with the screen door",
        spooky_detail="At night the dark window made the porch look deeper than it really was.",
        tags={"house", "porch"},
    ),
}

SOURCES = {
    "curtain": Source(
        id="curtain",
        label="loose curtain",
        sound1="whooo",
        sound2="swish-swish",
        action="the window was cracked open, and the curtain kept puffing in and brushing the wall",
        reveal="A stripe of moonlight showed the curtain lifting and falling in the breeze.",
        ending_image="the curtain breathed in and out like a slow white sail",
        supports={"hallway"},
        tags={"wind", "curtain"},
    ),
    "rocking_chair": Source(
        id="rocking_chair",
        label="old rocking chair",
        sound1="creak",
        sound2="creeeak-creak",
        action="the attic window was open just enough for a draft to nudge the old rocking chair",
        reveal="The chair moved by itself only because the night breeze kept giving it a tiny push.",
        ending_image="the old chair rocked once more, gentle and silly instead of scary",
        supports={"attic"},
        tags={"wind", "chair"},
    ),
    "tin_cup": Source(
        id="tin_cup",
        label="tin cup on a hook",
        sound1="clink",
        sound2="plink-clink",
        action="the screen door trembled whenever the wind touched it, and the hanging tin cup tapped the post",
        reveal="The cup bumped the wooden post each time the screen door shivered.",
        ending_image="the little cup tapped the post like a spoon on a mug",
        supports={"porch"},
        tags={"wind", "cup"},
    ),
    "apples": Source(
        id="apples",
        label="basket of apples",
        sound1="bump",
        sound2="thump-thump",
        action="one apple had rolled loose in the attic basket and kept nudging the others",
        reveal="When the helper lifted the lantern, one round apple slowly rolled and bumped the basket side.",
        ending_image="the runaway apple wobbled to a stop in a pool of warm light",
        supports={"attic"},
        tags={"apple", "basket"},
    ),
    "boots": Source(
        id="boots",
        label="wet boots",
        sound1="drip",
        sound2="plip...plip",
        action="rainwater was dripping from a pair of boots onto the metal tray by the back door",
        reveal="Each cold drop landed on the tray with a tiny silver sound.",
        ending_image="the last drop fell softly onto the tray, and then the porch was still",
        supports={"porch", "hallway"},
        tags={"rain", "boots"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        type="mother",
        entry="Mom came in with sleepy eyes and a kind voice.",
        comfort_line='"Thank you for telling me the honest truth," she said. "Being honest about being scared is brave."',
        tags={"parent"},
    ),
    "father": HelperCfg(
        id="father",
        type="father",
        entry="Dad came in tying his robe and listening carefully.",
        comfort_line='"Thank you for telling me the honest truth," he said. "Being honest about fear helps us solve it."',
        tags={"parent"},
    ),
    "grandmother": HelperCfg(
        id="grandmother",
        type="grandmother",
        entry="Grandma padded in softly, with her slippers whispering on the floor.",
        comfort_line='"Thank you for being honest with me," she said. "A true feeling is easier to help than a hidden one."',
        tags={"parent"},
    ),
    "grandfather": HelperCfg(
        id="grandfather",
        type="grandfather",
        entry="Grandpa opened the door with a small lamp in his hand.",
        comfort_line='"Thank you for being honest," he said. "A spooky sound gets smaller when we face the real thing together."',
        tags={"parent"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="cut a bright yellow path through the dark",
        tags={"flashlight"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a little camping lantern",
        glow="glowed warm and round like a pocket moon",
        tags={"lantern"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="night-light",
        phrase="a night-light",
        glow="made a small puddle of gold on the floor",
        tags={"nightlight"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Sophie", "Ella", "Lucy", "Zoe", "Ava"]
BOY_NAMES = ["Ben", "Owen", "Theo", "Max", "Leo", "Sam", "Noah", "Eli"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "imaginative", "sensitive"]


def source_fits(place_id: str, source_id: str) -> bool:
    return place_id in SOURCES[source_id].supports


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id in sorted(PLACES):
        for source_id in sorted(SOURCES):
            if source_fits(place_id, source_id):
                combos.append((place_id, source_id))
    return combos


@dataclass
class StoryParams:
    place: str
    source: str
    helper: str
    light: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


def _sound_once(world: World) -> None:
    source = world.get("source")
    source.meters["rattling"] += 1
    propagate(world, narrate=False)


def predict_spookiness(world: World) -> dict:
    sim = world.copy()
    _sound_once(sim)
    child = sim.get("child")
    house = sim.get("house")
    return {
        "fear": child.memes["fear"],
        "noise": house.meters["noise"],
    }


def introduce(world: World, child: Entity, place: Place, helper: Entity) -> None:
    trait = child.attrs.get("trait", "little")
    world.say(
        f"Late one night, {child.id} lay awake in bed, listening to the house."
    )
    world.say(
        f"{place.phrase.capitalize()} looked extra dark, and {place.spooky_detail}"
    )
    world.say(
        f"{child.id} was a {trait} little {child.type} who usually tried hard to act brave, "
        f"especially when {child.pronoun('possessive')} {helper.label_word} was nearby."
    )


def first_sound(world: World, child: Entity, source_cfg: Source) -> None:
    _sound_once(world)
    world.say(
        f"Then the sound came: {source_cfg.sound1}! {source_cfg.sound2}!"
    )
    world.say(
        f"It slid through the dark so strangely that {child.id} pulled the blanket up to "
        f"{child.pronoun('possessive')} chin and wondered if a ghost was tiptoeing about."
    )


def pretend_brave(world: World, child: Entity) -> None:
    child.memes["bravery"] = BRAVERY_INIT
    child.memes["pretense"] += 1
    world.say(
        f'"I am not scared," {child.id} whispered into the dark.'
    )
    world.say(
        f"But the room did not believe the whisper, and neither did {child.id}'s thumping heart."
    )


def choose_honesty(world: World, child: Entity, helper: Entity, place: Place, source_cfg: Source) -> None:
    pred = predict_spookiness(world)
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["honesty"] += 1
    child.memes["pretense"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"The sound came again from {place.phrase}: {source_cfg.sound1}! {source_cfg.sound2}!"
    )
    world.say(
        f"This time {child.id} took a shaky breath, padded to {helper.label_word}'s room, and said, "
        f'"I want to be honest. I really am scared."'
    )
    world.say(helper.attrs["comfort_line"])


def investigate(world: World, child: Entity, helper: Entity, place: Place, light: Light, source_cfg: Source) -> None:
    light_ent = world.get("light")
    light_ent.meters["on"] += 1
    child.memes["curiosity"] += 1
    world.say(helper.attrs["entry"])
    world.say(
        f"Together they took {light.phrase} that {light.glow} and walked toward {place.phrase}."
    )
    world.say(
        f"The dark seemed full of secrets for one more moment. Then they stopped and listened: "
        f"{source_cfg.sound1}! {source_cfg.sound2}!"
    )


def reveal(world: World, child: Entity, helper: Entity, source_cfg: Source) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    source = world.get("source")
    source.meters["understood"] += 1
    world.say(
        f"{source_cfg.reveal} {source_cfg.action}."
    )
    world.say(
        f'"So that is our ghost," {helper.label_word} said with a smile.'
    )
    world.say(
        f"{child.id} blinked, then laughed a little. It had sounded spooky in the dark, "
        f"but in the light it was only an ordinary thing making an ordinary noise."
    )


def ending(world: World, child: Entity, helper: Entity, source_cfg: Source) -> None:
    child.memes["safety"] += 1
    child.memes["trust"] += 1
    world.say(
        f"On the way back to bed, {child.id} held {helper.label_word}'s hand and felt much taller inside."
    )
    world.say(
        f"Now when the house made a sound, {child.pronoun()} knew it was better to tell the honest truth than to hide under the blankets alone."
    )
    world.say(
        f"Behind them, {source_cfg.ending_image}, and not a single bit of it was a ghost."
    )


def tell(
    place: Place,
    source_cfg: Source,
    helper_cfg: HelperCfg,
    light_cfg: Light,
    child_name: str = "Lila",
    child_gender: str = "girl",
    trait: str = "imaginative",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label="the helper",
            attrs={"comfort_line": helper_cfg.comfort_line, "entry": helper_cfg.entry},
            tags=set(helper_cfg.tags),
        )
    )
    house = world.add(
        Entity(
            id="house",
            kind="thing",
            type="house",
            label="house",
        )
    )
    world.add(
        Entity(
            id="source",
            kind="thing",
            type="source",
            label=source_cfg.label,
            tags=set(source_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="light",
            kind="thing",
            type="light",
            label=light_cfg.label,
            tags=set(light_cfg.tags),
        )
    )

    introduce(world, child, place, helper)
    world.para()
    first_sound(world, child, source_cfg)
    pretend_brave(world, child)
    world.para()
    choose_honesty(world, child, helper, place, source_cfg)
    world.para()
    investigate(world, child, helper, place, light_cfg, source_cfg)
    reveal(world, child, helper, source_cfg)
    world.para()
    ending(world, child, helper, source_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        source_cfg=source_cfg,
        light_cfg=light_cfg,
        outcome="revealed",
        honest=child.memes["honesty"] >= THRESHOLD,
        fear_before=world.facts.get("predicted_fear", 0.0),
        fear_after=child.memes["fear"],
    )
    return world


KNOWLEDGE = {
    "ghost_story": [
        (
            "What is a ghost story?",
            "A ghost story is a story that feels spooky and mysterious. It often starts with something strange and then explains what is really happening."
        )
    ],
    "honest": [
        (
            "What does it mean to be honest?",
            "Being honest means telling the truth about what happened or how you feel. Honest words help other people understand how to help you."
        )
    ],
    "wind": [
        (
            "Can wind make spooky sounds?",
            "Yes. Wind can rattle, creak, tap, or swish when it moves curtains, doors, cups, or chairs."
        )
    ],
    "curtain": [
        (
            "Why can a curtain sound spooky at night?",
            "A curtain can puff and brush against a wall or window when air moves it. In the dark, that soft swish can sound much stranger than it really is."
        )
    ],
    "chair": [
        (
            "Why does a rocking chair creak?",
            "A rocking chair creaks when its wooden parts rub and move. A tiny push can make it rock and speak in squeaky sounds."
        )
    ],
    "cup": [
        (
            "Why does a metal cup make a clink sound?",
            "Metal is hard, so when a cup taps wood or another hard thing it makes a bright clink. Little taps can sound loud at night."
        )
    ],
    "boots": [
        (
            "Why do wet boots drip?",
            "Wet boots drip because water slides off them a little at a time. Each drop can make a tiny sound when it lands."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight shines light exactly where you point it. That helps you see what a mysterious shape or sound really is."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern spreads a warm light around you so you can see nearby things clearly. Seeing clearly often makes a spooky feeling smaller."
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small steady glow in the dark. It can help a room feel calmer and easier to understand."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost_story",
    "honest",
    "wind",
    "curtain",
    "chair",
    "cup",
    "boots",
    "flashlight",
    "lantern",
    "nightlight",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    source_cfg = f["source_cfg"]
    helper = f["helper"]
    light_cfg = f["light_cfg"]
    return [
        f'Write a gentle ghost-story-style tale for a 3-to-5-year-old that includes the word "honest" and sound effects like "{source_cfg.sound1}" and "{source_cfg.sound2}".',
        f"Tell a twist story where a child named {child.id} hears a spooky sound in {place.phrase}, admits the honest truth about being scared, and discovers the noise is really {source_cfg.label}.",
        f"Write a cozy nighttime story where {helper.label_word} and {child.id} carry {light_cfg.phrase} into the dark, and the ghost turns out to be an ordinary household sound.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    source_cfg = f["source_cfg"]
    light_cfg = f["light_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type} who heard a spooky sound at night, and {child.pronoun('possessive')} {helper.label_word}, who helped investigate it."
        ),
        (
            "What made the story feel like a ghost story at first?",
            f"The dark place and the strange sound effects made it feel spooky. When {child.id} heard '{source_cfg.sound1}' and '{source_cfg.sound2}', {child.pronoun()} imagined a ghost before knowing the real cause."
        ),
        (
            f"Why did {child.id} go to {helper.label_word}?",
            f"{child.id} first tried to pretend to be brave, but the sound kept coming back and the fear grew. Then {child.pronoun()} chose to be honest and said the true thing: that {child.pronoun()} was scared."
        ),
        (
            f"How did {helper.label_word} help?",
            f"{helper.label_word.capitalize()} listened calmly and went with {child.id} to look instead of laughing or getting angry. They used {light_cfg.phrase} so they could see what was really making the noise."
        ),
        (
            "What was the twist at the end?",
            f"The twist was that there was no ghost at all. The scary sound came from {source_cfg.label}, and once they saw it clearly, it stopped feeling magical and mean."
        ),
        (
            "What did the child learn?",
            f"{child.id} learned that being honest about fear is brave. Telling the truth brought help quickly, and understanding the sound made the house feel safe again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost_story", "honest"}
    tags |= set(world.facts["source_cfg"].tags)
    tags |= set(world.facts["light_cfg"].tags)
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
    for ent in world.entities.values():
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
        place="hallway",
        source="curtain",
        helper="mother",
        light="flashlight",
        child_name="Lila",
        child_gender="girl",
        trait="imaginative",
    ),
    StoryParams(
        place="attic",
        source="rocking_chair",
        helper="grandfather",
        light="lantern",
        child_name="Ben",
        child_gender="boy",
        trait="quiet",
    ),
    StoryParams(
        place="porch",
        source="tin_cup",
        helper="grandmother",
        light="lantern",
        child_name="Nora",
        child_gender="girl",
        trait="careful",
    ),
    StoryParams(
        place="attic",
        source="apples",
        helper="father",
        light="flashlight",
        child_name="Theo",
        child_gender="boy",
        trait="curious",
    ),
    StoryParams(
        place="hallway",
        source="boots",
        helper="mother",
        light="nightlight",
        child_name="Lucy",
        child_gender="girl",
        trait="thoughtful",
    ),
]


def explain_rejection(place_id: str, source_id: str) -> str:
    place = PLACES[place_id]
    source_cfg = SOURCES[source_id]
    supported = ", ".join(sorted(source_cfg.supports))
    return (
        f"(No story: {source_cfg.label} does not make sense in {place.label}. "
        f"That source belongs in: {supported}.)"
    )


ASP_RULES = r"""
fits(P, S) :- source_supports(S, P).
valid(P, S) :- place(P), source(S), fits(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in sorted(PLACES):
        lines.append(asp.fact("place", place_id))
    for source_id, source_cfg in sorted(SOURCES.items()):
        lines.append(asp.fact("source", source_id))
        for place_id in sorted(source_cfg.supports):
            lines.append(asp.fact("source_supports", source_id, place_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: empty story.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an honest child, spooky sounds, and a cozy ghost-story twist."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, source) set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and not source_fits(args.place, args.source):
        raise StoryError(explain_rejection(args.place, args.source))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        source=source_id,
        helper=helper_id,
        light=light_id,
        child_name=child_name,
        child_gender=child_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if not source_fits(params.place, params.source):
        raise StoryError(explain_rejection(params.place, params.source))

    world = tell(
        place=PLACES[params.place],
        source_cfg=SOURCES[params.source],
        helper_cfg=HELPERS[params.helper],
        light_cfg=LIGHTS[params.light],
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source) combos:\n")
        for place_id, source_id in combos:
            print(f"  {place_id:8} {source_id}")
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
            header = f"### {p.child_name}: {p.source} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
