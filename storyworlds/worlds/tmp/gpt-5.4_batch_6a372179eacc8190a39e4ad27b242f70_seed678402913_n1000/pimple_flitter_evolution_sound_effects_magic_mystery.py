#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pimple_flitter_evolution_sound_effects_magic_mystery.py
==================================================================================

A standalone story world for a tall-tale mystery: a child finds a giant crop
with a strange pimple-like bump that makes impossible noises, and an elder uses
the right bit of magic to solve the mystery. Inside the bump is a tiny flitter
mid-evolution, and the ending image proves what changed: the flitter flies free
and blesses the field.

The domain is deliberately small and constraint-checked:

* A host crop (pumpkin / bean pod / apple) can only make certain magical sound
  clues.
* Each sound clue points to exactly one reasonable magical fix.
* Explicit mismatches are refused with a legible StoryError rather than
  generating a weak mystery.

Run it
------
    python storyworlds/worlds/gpt-5.4/pimple_flitter_evolution_sound_effects_magic_mystery.py
    python storyworlds/worlds/gpt-5.4/pimple_flitter_evolution_sound_effects_magic_mystery.py --host pumpkin --sound plink --magic moonwater
    python storyworlds/worlds/gpt-5.4/pimple_flitter_evolution_sound_effects_magic_mystery.py --host apple --sound hum
    python storyworlds/worlds/gpt-5.4/pimple_flitter_evolution_sound_effects_magic_mystery.py --all
    python storyworlds/worlds/gpt-5.4/pimple_flitter_evolution_sound_effects_magic_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/pimple_flitter_evolution_sound_effects_magic_mystery.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly: storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def family_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type or "helper")


@dataclass
class Host:
    id: str
    label: str = ""
    phrase: str = ""
    place: str = ""
    size_line: str = ""
    bump_spot: str = ""
    release_line: str = ""
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundClue:
    id: str
    noise: str = ""
    noise_twice: str = ""
    line: str = ""
    guess: str = ""
    stage: str = ""
    required_magic: str = ""
    unlock_line: str = ""
    explain_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicFix:
    id: str
    label: str = ""
    phrase: str = ""
    action: str = ""
    result_line: str = ""
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
    host = world.get("host")
    child = world.get("child")
    elder = world.get("elder")
    if host.meters["bump"] < THRESHOLD or host.meters["sound"] < THRESHOLD:
        return []
    sig = ("mystery", host.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    elder.memes["concern"] += 1
    world.facts["mystery_alive"] = True
    return []


def _r_evolution(world: World) -> list[str]:
    host = world.get("host")
    flitter = world.get("flitter")
    child = world.get("child")
    elder = world.get("elder")
    if host.meters["opened"] < THRESHOLD or flitter.meters["awake"] < THRESHOLD:
        return []
    sig = ("evolution", flitter.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flitter.meters["flying"] += 1
    flitter.meters["hidden"] = 0.0
    child.memes["wonder"] += 1
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    elder.memes["relief"] += 1
    world.facts["mystery_solved"] = True
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="evolution", tag="magic", apply=_r_evolution),
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
            elif any(name == rule.name for name, *_ in world.fired):
                changed = changed or False
    if narrate:
        for text in produced:
            world.say(text)
    return produced


HOSTS = {
    "pumpkin": Host(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin so big it needed its own weather",
        place="the pumpkin patch",
        size_line="It was so wide that crows used it as a meeting hill.",
        bump_spot="one orange cheek",
        release_line="golden vines curled into a grin around the fence posts",
        supports={"plink", "hum"},
        tags={"pumpkin", "garden"},
    ),
    "bean": Host(
        id="bean",
        label="bean pod",
        phrase="a bean pod as long as a canoe",
        place="the bean field",
        size_line="The tallest vine leaned over the clouds and waved at passing geese.",
        bump_spot="its middle seam",
        release_line="the vines straightened up like green trumpets in a parade",
        supports={"hum", "hiccup"},
        tags={"bean", "garden"},
    ),
    "apple": Host(
        id="apple",
        label="apple",
        phrase="an apple as round as a wagon wheel",
        place="the orchard",
        size_line="Each branch bowed as if it were carrying polished red lanterns.",
        bump_spot="its shiny red side",
        release_line="the whole orchard smelled bright enough to wake the moon",
        supports={"plink", "hiccup"},
        tags={"apple", "orchard"},
    ),
}

SOUNDS = {
    "plink": SoundClue(
        id="plink",
        noise="plink",
        noise_twice="plink-plink",
        line='From inside the bump came a neat little "plink-plink!" like a silver spoon tapping a glass.',
        guess="something hard and shiny",
        stage="shell-stage",
        required_magic="moonwater",
        unlock_line="The shell softened with a tiny sparkle and split like a pebble egg.",
        explain_line="That is no ordinary bump. It is a flitter in the shell-stage of its evolution.",
        tags={"sound", "shell"},
    ),
    "hum": SoundClue(
        id="hum",
        noise="hummm",
        noise_twice="hummm-hummm",
        line='The bump answered with a deep "hummm-hummm," as if a bee had borrowed a fiddle.',
        guess="something with folded wings",
        stage="wing-stage",
        required_magic="lullaby",
        unlock_line="The humming slowed, the bump relaxed, and the seam opened like a sleepy yawn.",
        explain_line="Hear that wing-song? A flitter is halfway through the wing-stage of its evolution.",
        tags={"sound", "wings"},
    ),
    "hiccup": SoundClue(
        id="hiccup",
        noise="hik",
        noise_twice="hik-hik",
        line='Then came a comic little "hik-hik!" that made the leaves jiggle as if they were trying not to laugh.',
        guess="something sneezing sparks",
        stage="spark-stage",
        required_magic="stardust",
        unlock_line="The bump gave one last cheerful hop, then popped open in a harmless puff of silver dust.",
        explain_line="That silly sound means a flitter has reached the spark-stage of its evolution.",
        tags={"sound", "spark"},
    ),
}

MAGIC = {
    "moonwater": MagicFix(
        id="moonwater",
        label="moonwater",
        phrase="a blue bottle of moonwater",
        action="tipped three shining drops onto the bump",
        result_line="Each drop rang as clear as a bell on ice.",
        tags={"moonwater", "magic"},
    ),
    "lullaby": MagicFix(
        id="lullaby",
        label="star lullaby",
        phrase="an old star lullaby",
        action="sang the soft old star lullaby into the leaves",
        result_line="The sound floated over the field like a blanket made of music.",
        tags={"lullaby", "magic"},
    ),
    "stardust": MagicFix(
        id="stardust",
        label="stardust pinch",
        phrase="a pinch of stardust",
        action="blew a pinch of stardust across the bump",
        result_line="The dust whirled in circles and spelled one bright twinkle in the air.",
        tags={"stardust", "magic"},
    ),
}

GIRL_NAMES = ["Tilda", "Molly", "June", "Nell", "Poppy", "Mira", "Bess", "Daisy"]
BOY_NAMES = ["Eli", "Jasper", "Toby", "Finn", "Otis", "Wade", "Milo", "Bo"]
TRAITS = ["curious", "bright-eyed", "brave", "patient", "quick-listening", "wonderful"]
ELDERS = ["grandmother", "grandfather"]


def valid_combo(host_id: str, sound_id: str, magic_id: str) -> bool:
    if host_id not in HOSTS or sound_id not in SOUNDS or magic_id not in MAGIC:
        return False
    return sound_id in HOSTS[host_id].supports and SOUNDS[sound_id].required_magic == magic_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for host_id, host in HOSTS.items():
        for sound_id in sorted(host.supports):
            required = SOUNDS[sound_id].required_magic
            combos.append((host_id, sound_id, required))
    return sorted(combos)


def explain_rejection(host: Host, sound: SoundClue, magic: MagicFix) -> str:
    if sound.id not in host.supports:
        return (
            f"(No story: {host.label} stories in this world do not make the sound "
            f'"{sound.noise_twice}". Pick a sound that fits that host.)'
        )
    if sound.required_magic != magic.id:
        needed = MAGIC[sound.required_magic].label
        return (
            f"(No story: the sound clue '{sound.noise_twice}' points to {needed}, "
            f"not {magic.label}. A mystery should be solved by the clue it gives.)"
        )
    return "(No story: that combination does not form a reasonable magical mystery.)"


def predict_solution(world: World, sound_id: str, magic_id: str) -> dict:
    sim = world.copy()
    host = sim.get("host")
    flitter = sim.get("flitter")
    host.meters["sound"] += 1
    host.meters["bump"] += 1
    propagate(sim, narrate=False)
    if SOUNDS[sound_id].required_magic == magic_id:
        host.meters["opened"] += 1
        flitter.meters["awake"] += 1
        propagate(sim, narrate=False)
    return {
        "solved": bool(sim.facts.get("mystery_solved")),
        "flying": sim.get("flitter").meters["flying"],
    }


def introduce(world: World, child: Entity, elder: Entity, host_cfg: Host) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {host_cfg.place}, where rows grew taller than church steeples, "
        f"{child.id} helped {child.pronoun('possessive')} {elder.family_word} with the morning rounds."
    )
    world.say(
        f"They came upon {host_cfg.phrase}. {host_cfg.size_line}"
    )


def spot_bump(world: World, child: Entity, host_cfg: Host) -> None:
    host = world.get("host")
    host.meters["bump"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"But right on {host_cfg.bump_spot} sat a round little pimple of a bump, "
        f"glowing faintly as if it had swallowed a firefly."
    )


def hear_clue(world: World, child: Entity, sound_cfg: SoundClue) -> None:
    host = world.get("host")
    host.meters["sound"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} bent close. {sound_cfg.line}"
    )
    world.say(
        f'"That is odd," {child.pronoun()} whispered. "It sounds like {sound_cfg.guess} is trapped in there."'
    )


def inspect(world: World, elder: Entity, child: Entity, sound_cfg: SoundClue, magic_cfg: MagicFix) -> None:
    pred = predict_solution(world, sound_cfg.id, magic_cfg.id)
    world.facts["predicted_solved"] = pred["solved"]
    elder.memes["wisdom"] += 1
    world.say(
        f"{elder.family_word.capitalize()} laid an ear against the giant fruit and listened all the way to the roots."
    )
    world.say(
        f'"Well now," {elder.pronoun()} said, "{sound_cfg.explain_line}"'
    )


def choose_magic(world: World, elder: Entity, magic_cfg: MagicFix) -> None:
    elder.memes["confidence"] += 1
    world.say(
        f"Then {elder.family_word} reached into {elder.pronoun('possessive')} apron pocket and pulled out {magic_cfg.phrase}."
    )
    world.say(
        f"{elder.pronoun().capitalize()} {magic_cfg.action}. {magic_cfg.result_line}"
    )


def solve_mystery(world: World, child: Entity, elder: Entity, host_cfg: Host, sound_cfg: SoundClue) -> None:
    host = world.get("host")
    flitter = world.get("flitter")
    host.meters["opened"] += 1
    flitter.meters["awake"] += 1
    propagate(world, narrate=False)
    world.say(sound_cfg.unlock_line)
    world.say(
        f"Out floated a flitter no bigger than a thumb, with wings thin as onion skin and bright as dawn on a spoon."
    )
    world.say(
        f"It circled {child.id}'s nose once, twice, then shook itself all over. "
        f"That last shake finished its evolution, and the tiny creature flashed from sleepy silver into honey-gold."
    )
    world.say(
        f'{child.id} laughed. "So that was the mystery!"'
    )
    world.say(
        f"The freed flitter zipped up with a merry {sound_cfg.noise_twice}, and {host_cfg.release_line}."
    )


def close_story(world: World, child: Entity, elder: Entity, host_cfg: Host) -> None:
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    world.say(
        f'From then on, whenever a crop wore a strange little pimple, {child.id} did not call it trouble at once.'
    )
    world.say(
        f"{child.pronoun().capitalize()} listened for the hidden song, and {elder.family_word} only smiled, because some mysteries in {host_cfg.place} were really miracles waiting for room to stretch their wings."
    )


def tell(
    host_cfg: Host,
    sound_cfg: SoundClue,
    magic_cfg: MagicFix,
    child_name: str = "Tilda",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
            tags={"child"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
            traits=["calm", "wise"],
            tags={"elder"},
        )
    )
    host = world.add(
        Entity(
            id="host",
            kind="thing",
            type="host",
            label=host_cfg.label,
            phrase=host_cfg.phrase,
            tags=set(host_cfg.tags),
        )
    )
    flitter = world.add(
        Entity(
            id="flitter",
            kind="thing",
            type="creature",
            label="flitter",
            phrase="a tiny flitter",
            tags={"flitter", "magic"},
        )
    )
    flitter.meters["hidden"] = 1.0

    introduce(world, child, elder, host_cfg)
    spot_bump(world, child, host_cfg)

    world.para()
    hear_clue(world, child, sound_cfg)
    inspect(world, elder, child, sound_cfg, magic_cfg)

    world.para()
    choose_magic(world, elder, magic_cfg)
    solve_mystery(world, child, elder, host_cfg, sound_cfg)

    world.para()
    close_story(world, child, elder, host_cfg)

    world.facts.update(
        child=child,
        elder=elder,
        host_cfg=host_cfg,
        sound_cfg=sound_cfg,
        magic_cfg=magic_cfg,
        solved=bool(world.facts.get("mystery_solved")),
        sound_text=sound_cfg.noise_twice,
        stage=sound_cfg.stage,
    )
    return world


@dataclass
class StoryParams:
    host: str
    sound: str
    magic: str
    child_name: str
    child_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "flitter": [
        (
            "What is a flitter?",
            "In this story world, a flitter is a tiny magical creature that hides inside plants while its wings are growing. When it is ready, it flutters out and brings a bit of blessing with it.",
        )
    ],
    "evolution": [
        (
            "What does evolution mean in this story?",
            "Here, evolution means the flitter is changing from one growing stage into another. It starts hidden and sleepy, and ends winged and ready to fly.",
        )
    ],
    "moonwater": [
        (
            "What is moonwater?",
            "Moonwater is pretend magic water that has sat under moonlight. In stories, it is gentle and sparkly and can help hidden magic open up.",
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft song meant to calm someone down. In a magical story, a lullaby can soothe even a creature hiding inside a bump.",
        )
    ],
    "stardust": [
        (
            "What is stardust in a tall tale?",
            "Stardust is pretend glittering dust from the stars. In tall tales, it can wake magic or help a mystery pop open in a bright little flash.",
        )
    ],
    "pumpkin": [
        (
            "What is a pumpkin patch?",
            "A pumpkin patch is a place where pumpkins grow in rows on vines. In a tall tale, the pumpkins can be as big as anything the storyteller dares to claim.",
        )
    ],
    "bean": [
        (
            "Why are giant beans common in tall tales?",
            "Tall tales like to take ordinary things and stretch them bigger than life. A bean vine that reaches the clouds is the kind of boasty, playful exaggeration tall tales enjoy.",
        )
    ],
    "apple": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees grow in rows. People walk there to care for the trees and gather the fruit when it is ready.",
        )
    ],
    "sound": [
        (
            "Why can a sound be a clue in a mystery?",
            "A sound tells you that something is happening even when you cannot see it yet. Careful listening can help you figure out what is hidden.",
        )
    ],
    "magic": [
        (
            "What makes a story feel magical?",
            "A story feels magical when ordinary things, like a bump on fruit or a soft song, do impossible and wonderful things. Magic often turns a problem into a surprise.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "flitter",
    "evolution",
    "sound",
    "magic",
    "moonwater",
    "lullaby",
    "stardust",
    "pumpkin",
    "bean",
    "apple",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    host = f["host_cfg"]
    sound_cfg = f["sound_cfg"]
    magic_cfg = f["magic_cfg"]
    return [
        'Write a tall-tale mystery for a 3-to-5-year-old that includes the words "pimple", "flitter", and "evolution".',
        f"Tell a playful story where {child.id} finds a pimple-like bump on a giant {host.label}, hears {sound_cfg.noise_twice}, and solves the mystery with {magic_cfg.label}.",
        "Write a child-facing story with sound effects, gentle magic, a hidden creature to discover, and an ending image that shows the mystery has truly been solved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    host = f["host_cfg"]
    sound_cfg = f["sound_cfg"]
    magic_cfg = f["magic_cfg"]
    elder_word = elder.family_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {elder_word}, who find a strange bump on a giant {host.label}. Together they listen carefully and solve the mystery.",
        ),
        (
            f"What first made {child.id} notice something was wrong?",
            f"{child.id} saw a glowing little pimple of a bump on the giant {host.label}. Then the bump made the sound {sound_cfg.noise_twice}, which turned simple curiosity into a real mystery.",
        ),
        (
            f"What was the mystery to solve?",
            f"They needed to find out what was hiding inside the bump and making that odd sound. The sound was the best clue, because it told them the bump was not ordinary at all.",
        ),
        (
            f"How did {elder_word} figure it out?",
            f"{elder_word.capitalize()} listened to the sound and recognized the stage of the hidden flitter. That clue showed which magic would help the creature safely finish its evolution.",
        ),
        (
            f"How did they solve the mystery?",
            f"They used {magic_cfg.label}, because it matched the clue hidden in the sound {sound_cfg.noise_twice}. When the right magic touched the bump, it opened and the flitter came out.",
        ),
        (
            "What was really inside the bump?",
            f"A tiny flitter was inside, growing through a stage of its evolution. The bump looked troublesome at first, but it was really a little magical cradle.",
        ),
        (
            "How did the story end?",
            f"The flitter flew free, and the whole place changed to show the mystery was solved. {host.release_line[0].upper()}{host.release_line[1:]}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"flitter", "evolution", "sound", "magic"}
    tags |= set(f["host_cfg"].tags)
    tags |= set(f["magic_cfg"].tags)
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        host="pumpkin",
        sound="plink",
        magic="moonwater",
        child_name="Tilda",
        child_gender="girl",
        elder="grandmother",
        trait="curious",
    ),
    StoryParams(
        host="pumpkin",
        sound="hum",
        magic="lullaby",
        child_name="Jasper",
        child_gender="boy",
        elder="grandfather",
        trait="patient",
    ),
    StoryParams(
        host="bean",
        sound="hiccup",
        magic="stardust",
        child_name="Mira",
        child_gender="girl",
        elder="grandmother",
        trait="bright-eyed",
    ),
    StoryParams(
        host="apple",
        sound="plink",
        magic="moonwater",
        child_name="Otis",
        child_gender="boy",
        elder="grandfather",
        trait="quick-listening",
    ),
    StoryParams(
        host="apple",
        sound="hiccup",
        magic="stardust",
        child_name="Poppy",
        child_gender="girl",
        elder="grandmother",
        trait="brave",
    ),
]


ASP_RULES = r"""
supports_sound(H, S) :- host(H), host_supports(H, S).
correct_magic(S, M) :- sound(S), required_magic(S, M).

valid(H, S, M) :- supports_sound(H, S), correct_magic(S, M).

solved(H, S, M) :- valid(H, S, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for host_id, host in HOSTS.items():
        lines.append(asp.fact("host", host_id))
        for sound_id in sorted(host.supports):
            lines.append(asp.fact("host_supports", host_id, sound_id))
    for sound_id, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sound_id))
        lines.append(asp.fact("required_magic", sound_id, sound.required_magic))
    for magic_id in MAGIC:
        lines.append(asp.fact("magic", magic_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_host", params.host),
            asp.fact("chosen_sound", params.sound),
            asp.fact("chosen_magic", params.magic),
            "picked_valid :- chosen_host(H), chosen_sound(S), chosen_magic(M), valid(H,S,M).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_valid/0."))
    return bool(asp.atoms(model, "picked_valid"))


def outcome_of(params: StoryParams) -> str:
    return "solved" if valid_combo(params.host, params.sound, params.magic) else "invalid"


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
    for seed in range(20):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_solved(params) != (outcome_of(params) == "solved"):
            bad += 1
    if bad == 0:
        print(f"OK: ASP solved/parity matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} solved checks differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("Smoke test generated incomplete output.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale magical mystery about a strange bump, a flitter, and the right clue."
    )
    ap.add_argument("--host", choices=HOSTS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.host and args.sound and args.magic:
        host = HOSTS[args.host]
        sound = SOUNDS[args.sound]
        magic = MAGIC[args.magic]
        if not valid_combo(args.host, args.sound, args.magic):
            raise StoryError(explain_rejection(host, sound, magic))
    elif args.host and args.sound and args.sound not in HOSTS[args.host].supports:
        raise StoryError(explain_rejection(HOSTS[args.host], SOUNDS[args.sound], MAGIC[SOUNDS[args.sound].required_magic]))
    elif args.sound and args.magic and SOUNDS[args.sound].required_magic != args.magic:
        host_id = args.host or next(iter(HOSTS))
        raise StoryError(explain_rejection(HOSTS[host_id], SOUNDS[args.sound], MAGIC[args.magic]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.host is None or combo[0] == args.host)
        and (args.sound is None or combo[1] == args.sound)
        and (args.magic is None or combo[2] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    host_id, sound_id, magic_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        host=host_id,
        sound=sound_id,
        magic=magic_id,
        child_name=child_name,
        child_gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.host not in HOSTS:
        raise StoryError(f"(No story: unknown host '{params.host}'.)")
    if params.sound not in SOUNDS:
        raise StoryError(f"(No story: unknown sound '{params.sound}'.)")
    if params.magic not in MAGIC:
        raise StoryError(f"(No story: unknown magic '{params.magic}'.)")
    if not valid_combo(params.host, params.sound, params.magic):
        raise StoryError(explain_rejection(HOSTS[params.host], SOUNDS[params.sound], MAGIC[params.magic]))

    world = tell(
        host_cfg=HOSTS[params.host],
        sound_cfg=SOUNDS[params.sound],
        magic_cfg=MAGIC[params.magic],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (host, sound, magic) combos:\n")
        for host_id, sound_id, magic_id in combos:
            print(f"  {host_id:8} {sound_id:8} {magic_id}")
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
            header = f"### {p.child_name}: {p.host} / {p.sound} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
