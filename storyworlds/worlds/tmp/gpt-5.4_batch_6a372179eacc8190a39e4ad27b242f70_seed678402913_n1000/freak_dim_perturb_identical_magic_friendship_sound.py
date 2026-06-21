#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/freak_dim_perturb_identical_magic_friendship_sound.py
=================================================================================

A standalone story world about a child and a magical friend in a tall-tale
landscape where a noisy disturbance upsets the path home. The core shape is:

    huge place + magical friendship + sound disturbance + matching fix

The seed words "freak-dim", "perturb", and "identical" are built directly into
the prose and the world model. The child and magical friend must make an
identical sound together to steady a flickering path. Only some magical tools
can truly calm a given disturbance, and the world refuses mismatched choices.

Run it
------
    python storyworlds/worlds/gpt-5.4/freak_dim_perturb_identical_magic_friendship_sound.py
    python storyworlds/worlds/gpt-5.4/freak_dim_perturb_identical_magic_friendship_sound.py --all
    python storyworlds/worlds/gpt-5.4/freak_dim_perturb_identical_magic_friendship_sound.py --qa
    python storyworlds/worlds/gpt-5.4/freak_dim_perturb_identical_magic_friendship_sound.py --verify
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
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str = ""
    scale_line: str = ""
    dim_spot: str = ""
    path_name: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendKind:
    id: str
    label: str = ""
    phrase: str = ""
    glow: str = ""
    sound_style: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Disturbance:
    id: str
    label: str = ""
    sound: str = ""
    boom: str = ""
    perturb_line: str = ""
    antidotes: set[str] = field(default_factory=set)
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str = ""
    phrase: str = ""
    sound_word: str = ""
    make_line: str = ""
    style: str = ""
    power: int = 1
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_path_wobbles(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    storm = world.get("disturbance")
    if storm.meters["ringing"] >= THRESHOLD and path.meters["steady"] > 0:
        sig = ("wobble",)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["steady"] = 0.0
            path.meters["lost"] += 1
            world.get("hero").memes["worry"] += 1
            world.get("friend").memes["worry"] += 1
            out.append("__wobble__")
    return out


def _r_identical_steadies(world: World) -> list[str]:
    out: list[str] = []
    pair = world.get("pair")
    storm = world.get("disturbance")
    path = world.get("path")
    if pair.meters["identical_sound"] >= THRESHOLD and storm.meters["calmed"] >= THRESHOLD:
        sig = ("steady",)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["steady"] += 1
            path.meters["lost"] = 0.0
            world.get("hero").memes["hope"] += 1
            world.get("friend").memes["hope"] += 1
            out.append("__steady__")
    return out


CAUSAL_RULES = [
    Rule(name="path_wobbles", tag="physical", apply=_r_path_wobbles),
    Rule(name="identical_steadies", tag="magical", apply=_r_identical_steadies),
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


def valid_fix(disturbance: Disturbance, charm: Charm) -> bool:
    return charm.id in disturbance.antidotes and charm.power >= disturbance.severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for friend_id in FRIENDS:
            for disturbance_id, disturbance in DISTURBANCES.items():
                for charm_id, charm in CHARMS.items():
                    if valid_fix(disturbance, charm):
                        combos.append((setting_id, friend_id, disturbance_id, charm_id))
    return combos


def explain_rejection(disturbance: Disturbance, charm: Charm) -> str:
    if charm.id not in disturbance.antidotes:
        good = ", ".join(sorted(disturbance.antidotes))
        return (
            f"(No story: {charm.label} does not make the right kind of sound to calm "
            f"{disturbance.label}. In this world, that disturbance settles only for: {good}.)"
        )
    return (
        f"(No story: {charm.label} is too weak for {disturbance.label}. "
        f"It needs power {disturbance.severity} or more.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("disturbance").meters["ringing"] += 1
    propagate(sim, narrate=False)
    return {
        "path_lost": sim.get("path").meters["lost"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"] + sim.get("friend").memes["worry"],
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"In {setting.place}, where hills were so tall they had to bend to fit under the moon, "
        f"{hero.id} walked one evening with {friend.phrase}. "
        f"{setting.scale_line}"
    )
    world.say(
        f"They were the sort of friends who could laugh at the same pebble and hear music in the same breeze. "
        f"{friend.id} glowed {friend.attrs['glow']}."
    )


def path_setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    path = world.get("path")
    path.meters["steady"] += 1
    world.say(
        f"Between them ran {setting.path_name}, a magic path stitched from moon-thread and cricket song. "
        f"It always held still when friends stayed close."
    )
    world.say(
        f"But ahead lay {setting.dim_spot}, a freak-dim patch where even brave shadows tiptoed."
    )


def warning(world: World, hero: Entity, friend: Entity, disturbance: Disturbance) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_path_lost"] = pred["path_lost"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'Just then came {disturbance.sound}: {disturbance.boom}! '
        f'The racket began to perturb the night itself.'
    )
    if pred["path_lost"]:
        world.say(
            f'{friend.id} twitched {friend.pronoun("possessive")} bright ears. '
            f'"That noise will shake our path loose," {friend.pronoun()} warned.'
        )


def trouble(world: World, hero: Entity, friend: Entity, disturbance: Disturbance) -> None:
    storm = world.get("disturbance")
    storm.meters["ringing"] += 1
    hero.memes["alarm"] += 1
    friend.memes["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The sound rolled again, bigger this time, and the moon-thread path shivered like a silver shoelace in a storm."
    )
    if world.get("path").meters["lost"] >= THRESHOLD:
        world.say(
            f"One curl of it vanished into the dark, and for a breath both friends stood still and listened hard."
        )


def plan(world: World, hero: Entity, friend: Entity, charm: Charm) -> None:
    hero.memes["resolve"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'"We can fix it," said {hero.id}. "{charm.make_line}"'
    )
    world.say(
        f'{friend.id} nodded. "Then we must make one identical sound together, not almost the same and not nearly the same. '
        f'Identical."'
    )


def perform_fix(world: World, hero: Entity, friend: Entity, disturbance: Disturbance, charm: Charm) -> None:
    pair = world.get("pair")
    storm = world.get("disturbance")
    pair.meters["identical_sound"] += 1
    if valid_fix(disturbance, charm):
        storm.meters["calmed"] += 1
        storm.meters["ringing"] = 0.0
    propagate(world, narrate=False)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"So {hero.id} lifted {charm.phrase}, and {friend.id} joined in with {friend.pronoun("possessive")} own magic voice. "
        f'"{charm.sound_word}!" sang the charm. "{friend.attrs["echo_word"]}!" sang the friend.'
    )
    world.say(
        f"The two notes met in the air, polished each other bright, and turned into one identical ribbon of sound."
    )


def resolution(world: World, hero: Entity, friend: Entity, setting: Setting, disturbance: Disturbance, charm: Charm) -> None:
    if world.get("path").meters["steady"] >= THRESHOLD:
        hero.memes["relief"] += 1
        friend.memes["relief"] += 1
        world.say(
            f"At once {disturbance.label} settled down. The magic path straightened, shining from toe to tail through the freak-dim place."
        )
        world.say(
            f"They crossed {setting.dim_spot} side by side, laughing softly so they would not wake the stars."
        )
        world.say(
            f"By the time they reached home, the night seemed bigger, kinder, and full of room for two friends who knew how to listen together."
        )
    else:
        raise StoryError("The magical fix failed to steady the path; this combination should have been rejected.")


def tell(setting: Setting, friend_cfg: FriendKind, disturbance: Disturbance, charm: Charm,
         hero_name: str = "Mira", hero_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(
        Entity(
            id=friend_cfg.label.title(),
            kind="character",
            type="creature",
            role="friend",
            phrase=friend_cfg.phrase,
            attrs={"glow": friend_cfg.glow, "echo_word": friend_cfg.sound_style},
            tags=set(friend_cfg.tags),
        )
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    path = world.add(Entity(id="path", type="path", label="moon-thread path"))
    storm = world.add(Entity(id="disturbance", type="disturbance", label=disturbance.label, tags=set(disturbance.tags)))
    pair = world.add(Entity(id="pair", type="friendship", label="friendship chord"))
    charm_ent = world.add(Entity(id="charm", type="charm", label=charm.label, phrase=charm.phrase, tags=set(charm.tags)))

    introduce(world, hero, friend, setting)
    path_setup(world, hero, friend, setting)

    world.para()
    warning(world, hero, friend, disturbance)
    trouble(world, hero, friend, disturbance)

    world.para()
    plan(world, hero, friend, charm)
    perform_fix(world, hero, friend, disturbance, charm)
    resolution(world, hero, friend, setting, disturbance, charm)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        path=path,
        disturbance_cfg=disturbance,
        disturbance=storm,
        charm_cfg=charm,
        charm=charm_ent,
        setting=setting,
        fixed=path.meters["steady"] >= THRESHOLD,
        identical=pair.meters["identical_sound"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    friend: str
    disturbance: str
    charm: str
    hero_name: str
    hero_gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "canyon": Setting(
        id="canyon",
        place="the Whistleback Canyon",
        scale_line="Its cliffs were so high that sunrise had to climb them like a ladder.",
        dim_spot="the freak-dim bend under the leaning cliff",
        path_name="the Long Silver Footpath",
        tags={"canyon", "night"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the Moonmilk Meadow",
        scale_line="The grass there grew taller than fence posts and bowed whenever a song passed by.",
        dim_spot="the freak-dim hollow behind the haystack hill",
        path_name="the Dew-Lantern Trail",
        tags={"meadow", "night"},
    ),
    "marsh": Setting(
        id="marsh",
        place="the Starbucket Marsh",
        scale_line="Its pools were so shiny that frogs checked their faces in them before croaking.",
        dim_spot="the freak-dim reed tunnel by the black-water bend",
        path_name="the Glowstep Ribbon",
        tags={"marsh", "night"},
    ),
}

FRIENDS = {
    "sprite": FriendKind(
        id="sprite",
        label="Pip",
        phrase="a pocket-sized echo sprite",
        glow="like a spoonful of moonlight",
        sound_style="ting-ting",
        tags={"sprite", "friendship"},
    ),
    "foal": FriendKind(
        id="foal",
        label="Comet",
        phrase="a cloud-foal with a mane full of sparks",
        glow="with pearl-white puffs around every hoof",
        sound_style="whinny-hum",
        tags={"foal", "friendship"},
    ),
    "cricket": FriendKind(
        id="cricket",
        label="Brassie",
        phrase="a lantern cricket as long as a loaf of bread",
        glow="through a shell as warm as a window lamp",
        sound_style="zirr-zirr",
        tags={"cricket", "friendship"},
    ),
}

DISTURBANCES = {
    "wind_sneeze": Disturbance(
        id="wind_sneeze",
        label="the giant wind sneeze",
        sound="a wind sneeze from the far ridge",
        boom="FWOOOF-CHOO",
        perturb_line="It made the reeds bow and the path wobble.",
        antidotes={"whistle", "humming_ribbon"},
        severity=1,
        tags={"wind", "sound"},
    ),
    "drum_bees": Disturbance(
        id="drum_bees",
        label="the drum-bee swarm",
        sound="a swarm of drum-bees",
        boom="BUM-BUZZA-BUM",
        perturb_line="Every wingbeat thudded like a tiny marching band.",
        antidotes={"drum_shell"},
        severity=2,
        tags={"bees", "sound"},
    ),
    "frog_thunder": Disturbance(
        id="frog_thunder",
        label="the thunder-frog chorus",
        sound="a chorus of thunder-frogs",
        boom="BROOOOM-BLOP",
        perturb_line="The marsh water jumped in its puddles every time they burped a note.",
        antidotes={"drum_shell", "humming_ribbon"},
        severity=2,
        tags={"frogs", "sound"},
    ),
}

CHARMS = {
    "whistle": Charm(
        id="whistle",
        label="silver whistle",
        phrase="the silver whistle",
        sound_word="PHEE-ree",
        make_line="I still have the silver whistle in my pocket.",
        style="thin",
        power=1,
        tags={"whistle", "sound"},
    ),
    "drum_shell": Charm(
        id="drum_shell",
        label="drum shell",
        phrase="the drum shell",
        sound_word="BOOM-loom",
        make_line="Tap the drum shell with me and hold the beat steady.",
        style="round",
        power=2,
        tags={"drum", "sound"},
    ),
    "humming_ribbon": Charm(
        id="humming_ribbon",
        label="humming ribbon",
        phrase="the humming ribbon",
        sound_word="Hummmm-lin",
        make_line="Stretch the humming ribbon between us and let it sing.",
        style="soft",
        power=2,
        tags={"hum", "sound"},
    ),
}

GIRL_NAMES = ["Mira", "Tessa", "Nell", "Ruby", "June", "Dora", "Lark", "Mae"]
BOY_NAMES = ["Eli", "Jasper", "Finn", "Otis", "Milo", "Beau", "Rory", "Cole"]


KNOWLEDGE = {
    "sound": [
        (
            "What is a sound?",
            "A sound is something you hear when air wiggles and carries that wiggle to your ears. Some sounds are soft and calming, and some are loud and startling."
        )
    ],
    "whistle": [
        (
            "What does a whistle do?",
            "A whistle makes a high clear sound when you blow through it. People can use that sound to signal or call."
        )
    ],
    "drum": [
        (
            "How does a drum make noise?",
            "A drum makes noise when something taps or hits it and the surface vibrates. The air carries that thump to your ears."
        )
    ],
    "hum": [
        (
            "What is a hum?",
            "A hum is a long soft sound, like saying mmm with your mouth closed. It can feel smooth and steady."
        )
    ],
    "friendship": [
        (
            "Why can friends solve problems together?",
            "Friends can notice different parts of a problem and help each other stay brave. Working together often makes a hard thing easier."
        )
    ],
    "wind": [
        (
            "What is wind?",
            "Wind is moving air. When it rushes fast, it can whistle, shake grass, and make big whooshing sounds."
        )
    ],
    "bees": [
        (
            "Why do bees buzz?",
            "Bees buzz because their wings beat very fast. That quick motion makes the air vibrate."
        )
    ],
    "frogs": [
        (
            "Why do frogs make croaking sounds?",
            "Frogs push air through their throats to call to other frogs. Some croaks are soft, and some can sound very loud."
        )
    ],
}
KNOWLEDGE_ORDER = ["friendship", "sound", "wind", "bees", "frogs", "whistle", "drum", "hum"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    disturbance = f["disturbance_cfg"]
    charm = f["charm_cfg"]
    setting = f["setting"]
    return [
        f'Write a tall-tale style story for a 3-to-5-year-old that includes the words "freak-dim", "perturb", and "identical".',
        f"Tell a magical friendship story where {hero.id} and {friend.id} cross {setting.place} and use sound to calm {disturbance.label}.",
        f"Write a child-facing story where two friends must make an identical sound with a {charm.label} to set a magic path right again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    disturbance = f["disturbance_cfg"]
    charm = f["charm_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, {friend.phrase}, walking together through {setting.place}. Their friendship matters because the magic path listens to them both."
        ),
        (
            "What upset the magic path?",
            f"{disturbance.label.capitalize()} upset it with {disturbance.boom}. The noisy racket began to perturb the night, so the moon-thread path wobbled and partly vanished."
        ),
        (
            "Why did they need to make one identical sound?",
            f"They needed the same note at the same time to calm the disturbance and steady the path. In this world, the path listens for friends working together, not for one lonely sound."
        ),
        (
            f"How did {hero.id} and {friend.id} fix the problem?",
            f"They used {charm.phrase} and matched the sound together until it became one identical ribbon of music. That calmed {disturbance.label} and made the path shine straight again."
        ),
        (
            "How did the story end?",
            f"It ended with the two friends crossing the freak-dim place safely side by side. The ending shows that their shared listening and bravery changed the night."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"friendship", "sound"}
    tags |= set(world.facts["disturbance_cfg"].tags)
    tags |= set(world.facts["charm_cfg"].tags)
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="canyon",
        friend="sprite",
        disturbance="wind_sneeze",
        charm="whistle",
        hero_name="Mira",
        hero_gender="girl",
        parent="mother",
    ),
    StoryParams(
        setting="meadow",
        friend="foal",
        disturbance="drum_bees",
        charm="drum_shell",
        hero_name="Eli",
        hero_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="marsh",
        friend="cricket",
        disturbance="frog_thunder",
        charm="humming_ribbon",
        hero_name="June",
        hero_gender="girl",
        parent="mother",
    ),
]


ASP_RULES = r"""
valid_fix(D, C) :- antidote(D, C), charm_power(C, P), severity(D, S), P >= S.
valid(S, F, D, C) :- setting(S), friend(F), disturbance(D), charm(C), valid_fix(D, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for friend_id in FRIENDS:
        lines.append(asp.fact("friend", friend_id))
    for disturbance_id, disturbance in DISTURBANCES.items():
        lines.append(asp.fact("disturbance", disturbance_id))
        lines.append(asp.fact("severity", disturbance_id, disturbance.severity))
        for antidote in sorted(disturbance.antidotes):
            lines.append(asp.fact("antidote", disturbance_id, antidote))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        lines.append(asp.fact("charm_power", charm_id, charm.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "identical" not in sample.story or "freak-dim" not in sample.story:
            raise StoryError("Smoke test story missing required core words or story text.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: magical friendship, noisy trouble, and an identical sound that fixes the path."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--disturbance", choices=DISTURBANCES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.disturbance and args.charm:
        disturbance = DISTURBANCES[args.disturbance]
        charm = CHARMS[args.charm]
        if not valid_fix(disturbance, charm):
            raise StoryError(explain_rejection(disturbance, charm))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.friend is None or combo[1] == args.friend)
        and (args.disturbance is None or combo[2] == args.disturbance)
        and (args.charm is None or combo[3] == args.charm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, friend_id, disturbance_id, charm_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        friend=friend_id,
        disturbance=disturbance_id,
        charm=charm_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Unknown friend: {params.friend})")
    if params.disturbance not in DISTURBANCES:
        raise StoryError(f"(Unknown disturbance: {params.disturbance})")
    if params.charm not in CHARMS:
        raise StoryError(f"(Unknown charm: {params.charm})")

    disturbance = DISTURBANCES[params.disturbance]
    charm = CHARMS[params.charm]
    if not valid_fix(disturbance, charm):
        raise StoryError(explain_rejection(disturbance, charm))

    world = tell(
        SETTINGS[params.setting],
        FRIENDS[params.friend],
        disturbance,
        charm,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, friend, disturbance, charm) combos:\n")
        for setting_id, friend_id, disturbance_id, charm_id in combos:
            print(f"  {setting_id:8} {friend_id:8} {disturbance_id:12} {charm_id}")
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
            header = (
                f"### {p.hero_name}: {p.setting} / {p.friend} / "
                f"{p.disturbance} / {p.charm}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
