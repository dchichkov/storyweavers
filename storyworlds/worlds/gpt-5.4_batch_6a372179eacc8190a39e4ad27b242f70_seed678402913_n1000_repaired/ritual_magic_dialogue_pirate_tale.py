#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ritual_magic_dialogue_pirate_tale.py
===============================================================

A standalone storyworld about two children playing pirates who find an enchanted
sea treasure that will only open for a calm ritual. The world models a rude
first impulse, a grounded warning, a magical turn, and a respectful dialogue-led
resolution.

Run it
------
    python storyworlds/worlds/gpt-5.4/ritual_magic_dialogue_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/ritual_magic_dialogue_pirate_tale.py --lock tide_chest --offering moon_shell
    python storyworlds/worlds/gpt-5.4/ritual_magic_dialogue_pirate_tale.py --lock gull_door --offering moon_shell
    python storyworlds/worlds/gpt-5.4/ritual_magic_dialogue_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/ritual_magic_dialogue_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ritual_magic_dialogue_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "patient", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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


@dataclass
class Setting:
    id: str
    place: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicLock:
    id: str
    label: str
    phrase: str
    inscription: str
    spirit: str
    release: str
    accepts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    token: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    phrase: str
    ending_image: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    lock: str
    offering: str
    reward: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    trust: int = 6
    seed: Optional[int] = None


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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_restless_magic(world: World) -> list[str]:
    lock = world.get("lock")
    if lock.meters["jostled"] < THRESHOLD:
        return []
    sig = ("restless_magic", lock.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lock.meters["mist"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__mist__"]


def _r_opened_reward(world: World) -> list[str]:
    lock = world.get("lock")
    reward = world.get("reward")
    if lock.meters["opened"] < THRESHOLD:
        return []
    sig = ("revealed", reward.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    reward.meters["revealed"] += 1
    for kid in world.kids():
        kid.memes["wonder"] += 1
        kid.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="restless_magic", tag="magic", apply=_r_restless_magic),
    Rule(name="opened_reward", tag="magic", apply=_r_opened_reward),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="a moon-bright cove",
        image="Small waves clicked over the pebbles, and the dark water shone like blue glass.",
        tags={"sea", "cove"},
    ),
    "sea_cave": Setting(
        id="sea_cave",
        place="a hollow sea cave",
        image="The cave roof dripped softly, and each drop made a silver ring in a tide pool.",
        tags={"sea", "cave"},
    ),
    "dock": Setting(
        id="dock",
        place="the old dock at the harbor",
        image="The ropes creaked, the pilings knocked together, and gulls cried over the black water.",
        tags={"sea", "dock"},
    ),
}

LOCKS = {
    "tide_chest": MagicLock(
        id="tide_chest",
        label="tide chest",
        phrase="a barnacled tide chest",
        inscription='The lid read: "Ask the tide kindly, and bring a shell from the moonlit shore."',
        spirit="the tide-spirit",
        release="a rolled star map tucked inside blue velvet",
        accepts={"shell"},
        tags={"chest", "magic", "ritual"},
    ),
    "lantern_coffer": MagicLock(
        id="lantern_coffer",
        label="lantern coffer",
        phrase="a green-glass lantern coffer",
        inscription='Across the latch shimmered: "Offer sea glass and speak softly, and the lantern heart will wake."',
        spirit="the lantern-spirit",
        release="a pearl compass that gave off a warm little glow",
        accepts={"glass"},
        tags={"chest", "magic", "ritual", "lantern"},
    ),
    "gull_door": MagicLock(
        id="gull_door",
        label="gull door",
        phrase="a narrow door of driftwood set in the rock",
        inscription='On the frame danced the words: "Pay the watch-gulls one bright coin, and ask the wind to share the way."',
        spirit="the gull-guard",
        release="a tiny brass key tied to a red ribbon",
        accepts={"coin"},
        tags={"door", "magic", "ritual"},
    ),
}

OFFERINGS = {
    "moon_shell": Offering(
        id="moon_shell",
        label="moon shell",
        phrase="a moon-white shell",
        token="shell",
        tags={"shell", "ritual"},
    ),
    "sea_glass": Offering(
        id="sea_glass",
        label="sea glass",
        phrase="a smooth piece of sea glass",
        token="glass",
        tags={"glass", "ritual"},
    ),
    "silver_coin": Offering(
        id="silver_coin",
        label="silver coin",
        phrase="a bright silver coin",
        token="coin",
        tags={"coin", "ritual"},
    ),
    "coral_bead": Offering(
        id="coral_bead",
        label="coral bead",
        phrase="a small coral bead",
        token="coral",
        tags={"coral", "ritual"},
    ),
}

REWARDS = {
    "star_map": Reward(
        id="star_map",
        phrase="a rolled star map tucked inside blue velvet",
        ending_image="They followed the star map home under a sky full of kind, clear lights.",
        use="show the safe way home across the rocks",
        tags={"map"},
    ),
    "pearl_compass": Reward(
        id="pearl_compass",
        phrase="a pearl compass that gave off a warm little glow",
        ending_image="The pearl compass glowed in their hands like a sleepy star on the deck.",
        use="point them back to the harbor path",
        tags={"compass", "lantern"},
    ),
    "brass_key": Reward(
        id="brass_key",
        phrase="a tiny brass key tied to a red ribbon",
        ending_image="The brass key swung between them while the harbor lights blinked across the water.",
        use="unlock the little chart cupboard on the dock",
        tags={"key"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah"]
TRAITS = ["careful", "cautious", "patient", "sensible", "curious", "thoughtful"]


def compatible(lock: MagicLock, offering: Offering) -> bool:
    return offering.token in lock.accepts


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for lid, lock in LOCKS.items():
            for oid, offering in OFFERINGS.items():
                if compatible(lock, offering):
                    out.append((sid, lid, oid))
    return out


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def explain_rejection(lock: MagicLock, offering: Offering) -> str:
    want = ", ".join(sorted(lock.accepts))
    return (
        f"(No story: {lock.label} will not answer {offering.phrase}. "
        f"It needs a ritual offering of type: {want}.)"
    )


def predict_mist(world: World) -> dict:
    sim = world.copy()
    lock = sim.get("lock")
    lock.meters["jostled"] += 1
    propagate(sim, narrate=False)
    return {
        "mist": lock.meters["mist"] >= THRESHOLD,
        "fear": sum(k.memes["fear"] for k in sim.kids()),
    }


def play_setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One evening, {a.id} and {b.id} played pirates in {setting.place}. {setting.image}"
    )
    world.say(
        f'"Captain {a.id}!" {b.id} whispered. "Do you see treasure?"'
    )
    world.say(
        f'"A real pirate always does," {a.id} said, sweeping an arm at the shadows.'
    )


def discover(world: World, lock_cfg: MagicLock) -> None:
    lock = world.get("lock")
    lock.meters["sealed"] = 1
    world.say(
        f"Behind a heap of driftwood they found {lock_cfg.phrase}. Salt shimmered on it, "
        f"and pale letters moved across the latch as if moonlight were reading them aloud."
    )
    world.say(lock_cfg.inscription)


def tempt(world: World, a: Entity, lock_cfg: MagicLock) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"No waiting," {a.id} said. "I can pry that {lock_cfg.label} open with my hook."'
    )


def warn(world: World, b: Entity, a: Entity, lock_cfg: MagicLock, parent: Entity) -> None:
    pred = predict_mist(world)
    b.memes["caution"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    extra = ""
    if pred["mist"]:
        extra = f" {b.id} could almost imagine cold blue mist pouring out."
    world.say(
        f'{b.id} touched the glowing words with one finger. "{a.id}, listen. '
        f'This is a ritual chest. {lock_cfg.spirit.capitalize()} wants asking, not grabbing."{extra}'
    )
    world.say(
        f'"If we are rude, we should call {parent.label_word} before the magic turns cross," {b.id} added.'
    )


def back_down(world: World, a: Entity, b: Entity, offering: Offering) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the shining latch, then at {b.id}, and let out a breath. '
        f'"All right," {a.pronoun()} said. "No prying. We will do the ritual properly."'
    )
    world.say(
        f"They set down {offering.phrase} between them and knelt as still as two little sailors before a map."
    )


def rude_try(world: World, a: Entity, lock_cfg: MagicLock) -> None:
    lock = world.get("lock")
    lock.meters["jostled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} caught the latch and tugged. At once the {lock_cfg.label} shivered."
    )
    if lock.meters["mist"] >= THRESHOLD:
        world.say(
            "Blue mist whirled out in a cold puff, and the cave filled with a sound like tiny glass bells."
        )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}!" {b.id} cried. "The magic is waking up!"')


def help_arrives(world: World, parent: Entity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came over quickly, boots tapping the stones, but {parent.pronoun()} did not shout."
    )
    world.say(
        f'"Treasure that asks for a ritual must be answered politely," {parent.pronoun()} said. '
        f'"Magic listens to the tone of your heart as much as the words."'
    )


def perform_ritual(world: World, a: Entity, b: Entity, offering: Offering, lock_cfg: MagicLock) -> None:
    lock = world.get("lock")
    lock.meters["calmed"] += 1
    world.say(
        f"They placed {offering.phrase} on the stone before the latch. Then all three of them bowed their heads."
    )
    world.say(
        f'"{lock_cfg.spirit.capitalize()}, please share the way," {b.id} said softly.'
    )
    world.say(
        f'"We came with kind hands," {a.id} added. "Please open for us."'
    )
    lock.meters["opened"] += 1
    lock.meters["sealed"] = 0.0
    lock.meters["mist"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"The glowing letters loosened, the salt crust cracked with a tiny sigh, and the {lock_cfg.label} opened by itself."
    )


def reveal(world: World, reward_cfg: Reward, parent: Entity) -> None:
    reward = world.get("reward")
    world.say(
        f"Inside lay {reward_cfg.phrase}. {parent.label_word.capitalize()} smiled as the children stared."
    )
    world.say(
        f'"See?" {parent.pronoun()} said. "A pirate can be brave and gentle at the same time."'
    )


def ending(world: World, a: Entity, b: Entity, reward_cfg: Reward, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["joy"] += 1
    world.say(
        f'{a.id} held the treasure carefully, and {b.id} grinned. "The ritual worked because we asked kindly," {b.id} said.'
    )
    world.say(
        f'"And because we listened first," {a.id} answered.'
    )
    world.say(
        f"Together they used it to {reward_cfg.use}, and {reward_cfg.ending_image}"
    )


def tell(
    setting: Setting,
    lock_cfg: MagicLock,
    offering: Offering,
    reward_cfg: Reward,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the captain parent",
    ))
    lock = world.add(Entity(
        id="lock",
        type="magic_lock",
        label=lock_cfg.label,
        phrase=lock_cfg.phrase,
        tags=set(lock_cfg.tags),
    ))
    reward = world.add(Entity(
        id="reward",
        type="reward",
        label=reward_cfg.id,
        phrase=reward_cfg.phrase,
        tags=set(reward_cfg.tags),
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    play_setup(world, a, b, setting)
    discover(world, lock_cfg)

    world.para()
    tempt(world, a, lock_cfg)
    warn(world, b, a, lock_cfg, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, offering)
        world.para()
        perform_ritual(world, a, b, offering, lock_cfg)
    else:
        rude_try(world, a, lock_cfg)
        alarm(world, b, parent)
        world.para()
        help_arrives(world, parent)
        perform_ritual(world, a, b, offering, lock_cfg)

    reveal(world, reward_cfg, parent)
    world.para()
    ending(world, a, b, reward_cfg, setting)

    outcome = "averted" if averted else "guided"
    world.facts.update(
        setting=setting,
        lock_cfg=lock_cfg,
        offering=offering,
        reward_cfg=reward_cfg,
        instigator=a,
        cautioner=b,
        parent=parent,
        lock=lock,
        reward=reward,
        relation=relation,
        outcome=outcome,
        averted=averted,
        mist_seen=lock.meters["jostled"] >= THRESHOLD,
        promised=all(k.memes["lesson"] >= THRESHOLD for k in (a, b)),
    )
    return world


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    lock_cfg = f["lock_cfg"]
    offering = f["offering"]
    if f["outcome"] == "averted":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old that includes the word "ritual" and uses magic and dialogue.',
            f"Tell a gentle pirate tale where {a.id} wants to force open a magical {lock_cfg.label}, but {b.id} stops {a.pronoun('object')} and the children perform a calm ritual instead.",
            f"Write a story with moonlit sea magic, respectful dialogue, and {offering.phrase} used in a ritual that opens treasure kindly.",
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the word "ritual" and uses magic and dialogue.',
        f"Tell a pirate tale where {a.id} tries to tug open a magical {lock_cfg.label}, blue mist spills out, and a calm grown-up teaches the proper ritual.",
        f"Write a story with sea magic, spoken lines, and a respectful ritual using {offering.phrase} to turn a scary moment into a safe one.",
    ]


KNOWLEDGE = {
    "ritual": [
        (
            "What is a ritual?",
            "A ritual is a special set of actions and words done in a careful order. In stories, a ritual often shows respect and helps magic know what you mean.",
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic means something wonderful or strange happens in a way that ordinary tools cannot explain. Story magic often follows rules, like kind words or special objects.",
        )
    ],
    "shell": [
        (
            "What is a shell?",
            "A shell is the hard outside home of a sea animal. You can find empty shells on the beach after the animal is gone.",
        )
    ],
    "glass": [
        (
            "What is sea glass?",
            "Sea glass is broken glass that waves have rolled smooth. The water rubs the sharp edges away until it feels soft in your hand.",
        )
    ],
    "coin": [
        (
            "What is a coin?",
            "A coin is a small round piece of metal used as money. In stories, it can also be a token or offering.",
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass helps people find direction. It points a steady way so travelers do not get lost.",
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map shows where places are and how to travel between them. Sailors use maps to find safe paths.",
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key fits a lock and lets you open something that was shut. A special key in a story can also mean a secret is ready to be found.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ritual", "magic", "shell", "glass", "coin", "map", "compass", "key"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    lock_cfg = f["lock_cfg"]
    offering = f["offering"]
    reward_cfg = f["reward_cfg"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were playing pirates near the sea. It is also about their {pw}, who helped them understand the magic.",
        ),
        (
            "What treasure did they find?",
            f"They found {lock_cfg.phrase} with glowing writing on it. The writing showed that the treasure wanted a ritual instead of rough hands.",
        ),
        (
            f"Why did {b.id} tell {a.id} not to pry it open?",
            f"{b.id} read the shining message and understood that the magic wanted polite asking. {b.pronoun().capitalize()} also guessed that grabbing the latch would wake the magic in a scary way.",
        ),
    ]
    if f["outcome"] == "guided":
        qa.append(
            (
                "What happened when the chest or door was tugged the wrong way?",
                "Blue mist spilled out and the magic felt cross. That scary turn showed the children why the ritual rules mattered.",
            )
        )
        qa.append(
            (
                f"How did their {pw} help?",
                f"Their {pw} came quickly and stayed calm. {parent.pronoun().capitalize()} taught them to place {offering.phrase} down first and speak kindly to the spirit.",
            )
        )
    else:
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} listened and backed away from the latch. Because {a.pronoun()} stopped in time, the magic never burst out in a scary puff.",
            )
        )
    qa.append(
        (
            "How did they open the treasure safely?",
            f"They used {offering.phrase} as the offering and spoke softly during the ritual. The lock opened after they asked with kind words instead of trying to force it.",
        )
    )
    qa.append(
        (
            "What was inside, and why did that matter at the end?",
            f"Inside was {reward_cfg.phrase}. It mattered because they could use it to {reward_cfg.use}, proving the ritual gave them something helpful, not just something shiny.",
        )
    )
    qa.append(
        (
            "What did the children learn?",
            "They learned that being brave does not mean being rough. In this story, listening and speaking kindly were what made the magic safe.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ritual", "magic"}
    tags |= set(f["offering"].tags)
    tags |= set(f["reward_cfg"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cove",
        lock="tide_chest",
        offering="moon_shell",
        reward="star_map",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        trust=5,
    ),
    StoryParams(
        setting="sea_cave",
        lock="lantern_coffer",
        offering="sea_glass",
        reward="pearl_compass",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=4,
    ),
    StoryParams(
        setting="dock",
        lock="gull_door",
        offering="silver_coin",
        reward="brass_key",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="patient",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        trust=6,
    ),
]


ASP_RULES = r"""
compatible(L, O) :- accepts(L, T), token(O, T).
valid(S, L, O) :- setting(S), lock(L), offering(O), compatible(L, O).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(guided) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid, lock in LOCKS.items():
        lines.append(asp.fact("lock", lid))
        for token in sorted(lock.accepts):
            lines.append(asp.fact("accepts", lid, token))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("token", oid, offering.token))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait) else "guided"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True, header="### smoke")
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate children, sea magic, and a ritual treasure."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lock", choices=LOCKS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--reward", choices=REWARDS)
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lock and args.offering:
        lock_cfg = LOCKS[args.lock]
        offering = OFFERINGS[args.offering]
        if not compatible(lock_cfg, offering):
            raise StoryError(explain_rejection(lock_cfg, offering))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.lock is None or c[1] == args.lock)
        and (args.offering is None or c[2] == args.offering)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, lock_id, offering_id = rng.choice(sorted(combos))
    reward = args.reward or rng.choice(sorted(REWARDS))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        setting=setting,
        lock=lock_id,
        offering=offering_id,
        reward=reward,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=ages[0],
        cautioner_age=ages[1],
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        lock_cfg = LOCKS[params.lock]
        offering = OFFERINGS[params.offering]
        reward = REWARDS[params.reward]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not compatible(lock_cfg, offering):
        raise StoryError(explain_rejection(lock_cfg, offering))

    world = tell(
        setting=setting,
        lock_cfg=lock_cfg,
        offering=offering,
        reward_cfg=reward,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (setting, lock, offering) combos:\n")
        for setting, lock_id, offering in combos:
            print(f"  {setting:9} {lock_id:15} {offering}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.lock} with {p.offering} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
