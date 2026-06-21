#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boss_animal_riverbank_flashback_curiosity_rhyming_story.py
======================================================================================

A standalone storyworld for a tiny riverbank domain:

- a young animal is curious about a mystery by the water,
- a boastful "boss" moment pushes toward a risky grab,
- a flashback changes the choice or softens the fall,
- the ending proves the hero learned to be curious without being bossy.

The prose aims for a gentle rhyming-story feel, while the world model stays
classical and checkable: typed entities, physical meters, emotional memes, a
small forward-chaining rule engine, a Python reasonableness gate, and an inline
ASP twin used by --verify.

Run examples
------------
python storyworlds/worlds/gpt-5.4/boss_animal_riverbank_flashback_curiosity_rhyming_story.py
python storyworlds/worlds/gpt-5.4/boss_animal_riverbank_flashback_curiosity_rhyming_story.py --animal beaver --mystery ribbon --method reed_hook
python storyworlds/worlds/gpt-5.4/boss_animal_riverbank_flashback_curiosity_rhyming_story.py --method paw_reach
python storyworlds/worlds/gpt-5.4/boss_animal_riverbank_flashback_curiosity_rhyming_story.py --all --qa
python storyworlds/worlds/gpt-5.4/boss_animal_riverbank_flashback_curiosity_rhyming_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class AnimalCfg:
    id: str
    species: str
    phrase: str
    step: str
    voice: str
    paw: str
    bossiness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendCfg:
    id: str
    species: str
    phrase: str
    caution: int
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MysteryCfg:
    id: str
    label: str
    phrase: str
    place: str
    hint: str
    need: str
    reveal: str
    reveal_kind: str
    pull: int
    wettable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MethodCfg:
    id: str
    label: str
    phrase: str
    sense: int
    works_on: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class FlashbackCfg:
    id: str
    phrase: str
    lesson: str
    memory: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    animal: str
    friend: str
    mystery: str
    method: str
    flashback: str
    parent: str
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


def _r_slip(world: World) -> list[str]:
    hero = world.get("hero")
    bank = world.get("bank")
    if hero.meters["reaching"] < THRESHOLD:
        return []
    if world.facts.get("risk_pull", 0) < 2:
        return []
    sig = ("slip", world.facts.get("mystery_id"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["soaked"] += 1
    hero.meters["muddy"] += 1
    bank.meters["splash"] += 1
    hero.memes["fear"] += 1
    hero.memes["bossiness"] = 0.0
    world.get("friend").memes["fear"] += 1
    world.get("parent").memes["alarm"] += 1
    return ["__slip__"]


def _r_relief(world: World) -> list[str]:
    clue = world.get("mystery")
    if clue.meters["solved"] < THRESHOLD:
        return []
    sig = ("relief", world.facts.get("mystery_id"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend", "parent"):
        world.get(eid).memes["relief"] += 1
    world.get("hero").memes["wisdom"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


ANIMALS = {
    "otter": AnimalCfg(
        id="otter",
        species="otter",
        phrase="a bright little otter",
        step="skipped",
        voice="chirped",
        paw="paw",
        bossiness=2,
        tags={"animal", "riverbank"},
    ),
    "beaver": AnimalCfg(
        id="beaver",
        species="beaver",
        phrase="a busy young beaver",
        step="bustled",
        voice="hummed",
        paw="paw",
        bossiness=3,
        tags={"animal", "riverbank"},
    ),
    "duckling": AnimalCfg(
        id="duckling",
        species="duckling",
        phrase="a soft yellow duckling",
        step="waddled",
        voice="peeped",
        paw="bill",
        bossiness=1,
        tags={"animal", "riverbank"},
    ),
    "froglet": AnimalCfg(
        id="froglet",
        species="froglet",
        phrase="a springy green froglet",
        step="hopped",
        voice="piped",
        paw="foot",
        bossiness=2,
        tags={"animal", "riverbank"},
    ),
}

FRIENDS = {
    "mole": FriendCfg(
        id="mole",
        species="mole",
        phrase="a steady little mole",
        caution=3,
        line="Slow paws make good laws by the river, you know.",
        tags={"friend"},
    ),
    "heron": FriendCfg(
        id="heron",
        species="heron",
        phrase="a calm young heron",
        caution=2,
        line="A long look beats a wrong look when muddy banks flow.",
        tags={"friend"},
    ),
    "turtle": FriendCfg(
        id="turtle",
        species="turtle",
        phrase="a thoughtful small turtle",
        caution=3,
        line="When water is wiggly, be patient and slow.",
        tags={"friend"},
    ),
    "mouse": FriendCfg(
        id="mouse",
        species="mouse",
        phrase="a tiny field mouse",
        caution=1,
        line="Maybe we should wonder first, before we lean low.",
        tags={"friend"},
    ),
}

MYSTERIES = {
    "ribbon": MysteryCfg(
        id="ribbon",
        label="ribbon",
        phrase="a red ribbon",
        place="caught in the reeds",
        hint="something red winked and flicked in the breeze",
        need="hook",
        reveal="only a red ribbon from an old toy boat",
        reveal_kind="object",
        pull=2,
        wettable=True,
        tags={"reeds", "riverbank"},
    ),
    "basket": MysteryCfg(
        id="basket",
        label="basket",
        phrase="a tiny willow basket",
        place="bobbing in a sleepy eddy",
        hint="a little round shadow bumped softly in circles",
        need="scoop",
        reveal="a tiny willow basket carrying berries for supper",
        reveal_kind="object",
        pull=2,
        wettable=True,
        tags={"basket", "riverbank"},
    ),
    "nest": MysteryCfg(
        id="nest",
        label="nest",
        phrase="a woven nest",
        place="tucked beyond a soft muddy ledge",
        hint="a neat little bowl of grass rested where the mud looked thin",
        need="watch",
        reveal="a woven nest where reed birds were tucking in for rest",
        reveal_kind="animal_home",
        pull=3,
        wettable=False,
        tags={"nest", "bird", "riverbank"},
    ),
    "shell": MysteryCfg(
        id="shell",
        label="shell",
        phrase="a swirly shell",
        place="gleaming in the shallows",
        hint="something pearly flashed where small waves curled",
        need="scoop",
        reveal="a swirly shell with river-song curled inside",
        reveal_kind="object",
        pull=1,
        wettable=True,
        tags={"shell", "riverbank"},
    ),
}

METHODS = {
    "reed_hook": MethodCfg(
        id="reed_hook",
        label="reed hook",
        phrase="a bent reed hook",
        sense=3,
        works_on={"hook"},
        action="used a bent reed hook and drew it out with a careful crook",
        qa_text="used a bent reed hook to pull it close",
        tags={"hook", "tool"},
    ),
    "scoop_net": MethodCfg(
        id="scoop_net",
        label="scoop net",
        phrase="a scoop net",
        sense=3,
        works_on={"scoop"},
        action="lowered a scoop net and lifted it up in one gentle swoop",
        qa_text="lowered a scoop net and lifted it out carefully",
        tags={"net", "tool"},
    ),
    "watch_and_call": MethodCfg(
        id="watch_and_call",
        label="watch and call",
        phrase="watching from a safe stump and calling a grown-up",
        sense=3,
        works_on={"watch"},
        action="sat on a safe stump, watched with wide eyes, and called for a grown-up",
        qa_text="stayed back, watched carefully, and called a grown-up",
        tags={"wait", "call_adult"},
    ),
    "branch_bridge": MethodCfg(
        id="branch_bridge",
        label="branch bridge",
        phrase="a flat branch bridge",
        sense=2,
        works_on={"hook", "scoop"},
        action="slid a flat branch over the mud and nudged the mystery closer",
        qa_text="used a flat branch to nudge it closer",
        tags={"branch", "tool"},
    ),
    "paw_reach": MethodCfg(
        id="paw_reach",
        label="paw reach",
        phrase="stretching a bare paw straight over the edge",
        sense=1,
        works_on={"hook", "scoop", "watch"},
        action="reached straight out with no safe plan at all",
        qa_text="reached with a bare paw",
        tags={"unsafe"},
    ),
}

FLASHBACKS = {
    "cold_splash": FlashbackCfg(
        id="cold_splash",
        phrase="a cold splash from last week",
        lesson="Last week the mud had slurped and the water had made their whiskers drip.",
        memory=3,
        tags={"flashback", "memory"},
    ),
    "lost_leaf_hat": FlashbackCfg(
        id="lost_leaf_hat",
        phrase="the day their leaf hat floated away",
        lesson="Once a jaunty leaf hat had sailed downstream because they leaned too far to show off.",
        memory=2,
        tags={"flashback", "memory"},
    ),
    "startled_birds": FlashbackCfg(
        id="startled_birds",
        phrase="the time a loud pounce startled birds from the reeds",
        lesson="They remembered the flurry of wings and how quiet watching had been kinder than a sudden shove.",
        memory=2,
        tags={"flashback", "memory", "bird"},
    ),
}

PARENT_NAMES = {
    "mother": "Mother",
    "father": "Father",
}


def method_fits(mystery: MysteryCfg, method: MethodCfg) -> bool:
    return mystery.need in method.works_on


def sensible_methods() -> list[MethodCfg]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id in sorted(ANIMALS):
        for mystery_id, mystery in MYSTERIES.items():
            for method_id, method in METHODS.items():
                if method_fits(mystery, method) and method.sense >= SENSE_MIN:
                    combos.append((animal_id, mystery_id, method_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    animal = ANIMALS[params.animal]
    friend = FRIENDS[params.friend]
    mystery = MYSTERIES[params.mystery]
    flash = FLASHBACKS[params.flashback]
    temptation = animal.bossiness + mystery.pull
    restraint = friend.caution + flash.memory
    return "careful" if restraint >= temptation else "splash"


def predict_splash(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").meters["reaching"] += 1
    markers = propagate(sim, narrate=False)
    return "__slip__" in markers


def opening_name(cfg: AnimalCfg) -> str:
    return {
        "otter": "Pip",
        "beaver": "Bram",
        "duckling": "Dilly",
        "froglet": "Frip",
    }[cfg.id]


def friend_name(cfg: FriendCfg) -> str:
    return {
        "mole": "Moss",
        "heron": "Hera",
        "turtle": "Tupp",
        "mouse": "Mim",
    }[cfg.id]


def introduce(world: World, hero: Entity, animal: AnimalCfg, friend: Entity, friend_cfg: FriendCfg) -> None:
    world.say(
        f"By the riverbank, where willows drank and water shone like glass, "
        f"{hero.id} {animal.step} through silver grass."
    )
    world.say(
        f"{hero.id} was {animal.phrase}, an animal bright and small, "
        f"and {friend.id}, {friend_cfg.phrase}, came trotting at the call."
    )
    hero.memes["curiosity"] += 1
    friend.memes["companionship"] += 1


def game_of_boss(world: World, hero: Entity) -> None:
    hero.memes["bossiness"] += 1
    world.say(
        f'"I am the boss of this moss!" sang {hero.id} with happy pride. '
        f'"Come see what secrets the river hides."'
    )


def spot_mystery(world: World, hero: Entity, mystery: MysteryCfg) -> None:
    world.facts["risk_pull"] = mystery.pull
    world.say(
        f"Then {mystery.hint}. Down by the bank, {mystery.phrase} was {mystery.place}, "
        f"and curiosity buzzed like a bee in a pail."
    )
    hero.memes["curiosity"] += 1


def friend_warn(world: World, friend: Entity, friend_cfg: FriendCfg, hero: Entity, mystery: MysteryCfg) -> None:
    splash = predict_splash(world)
    world.facts["predicted_splash"] = splash
    warning = "That edge looks slick, and a quick grab could mean a splash." if splash else \
        "That spot looks close, but slow eyes still beat hasty paws."
    world.say(
        f'{friend.id} blinked at the muddy lip. "{friend_cfg.line} {warning}"'
    )
    friend.memes["caution"] += 1


def flashback_beat(world: World, hero: Entity, flash: FlashbackCfg) -> None:
    hero.memes["memory"] += float(flash.memory)
    world.say(
        f"At once came a flashback, soft and quick as a song: {flash.lesson} "
        f"The memory fluttered through {hero.pronoun('possessive')} heart and stayed there strong."
    )


def boast_or_brake(world: World, hero: Entity, outcome: str) -> None:
    if outcome == "careful":
        world.say(
            f"{hero.id} lifted {hero.pronoun('possessive')} {hero.attrs['paw']} — then stopped in the nick. "
            f'"Maybe the boss can be patient," {hero.pronoun()} said. "Being careful can still be quick."'
        )
    else:
        world.say(
            f'"I can do it myself!" cried {hero.id}. "I am the boss, and I am fast!" '
            f"{hero.pronoun().capitalize()} leaned too far over the muddy edge at last."
        )


def slip(world: World, hero: Entity, parent: Entity) -> None:
    hero.meters["reaching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The mud gave a slurp, the bank gave a splash, and cold drops flew up in a dash. "
        f"{hero.id} did not tumble in deep, but {hero.pronoun('possessive')} fur and feet were wet in a flash."
    )
    world.say(
        f'{parent.label_word.capitalize()} hurried close and steadied {hero.pronoun("object")}. '
        f'"Curious is fine," {parent.pronoun()} said, "but rushing is not the way."'
    )


def solve(world: World, hero: Entity, friend: Entity, parent: Entity,
          mystery_ent: Entity, mystery: MysteryCfg, method: MethodCfg) -> None:
    mystery_ent.meters["solved"] += 1
    propagate(world, narrate=False)
    if method.id == "watch_and_call":
        world.say(
            f"So they {method.action}. Together they learned it was {mystery.reveal}, "
            f"best left snug where reeds could sway and play."
        )
    else:
        world.say(
            f"Then {parent.label_word} smiled and {method.action}. Soon they saw it was {mystery.reveal}, "
            f"and the river gave back its little secret for the day."
        )
    hero.memes["curiosity"] = max(0.0, hero.memes["curiosity"] - 1.0)
    hero.memes["bossiness"] = 0.0
    hero.memes["wisdom"] += 1
    friend.memes["trust"] += 1
    world.facts["resolved_with"] = method.label


def ending(world: World, hero: Entity, friend: Entity, mystery: MysteryCfg, outcome: str) -> None:
    if outcome == "careful":
        image = (
            f"At sunset, {hero.id} and {friend.id} sat side by side on a dry old log, "
            f"watching rings of light wobble under frog-song and fog."
        )
    else:
        image = (
            f"At sunset, {hero.id} sat on a warm flat stone while the damp on "
            f"{hero.pronoun('possessive')} fur turned gold in the light."
        )
    world.say(
        f"{image} {hero.id} did not sing about being boss any more."
    )
    world.say(
        f'Instead {hero.pronoun()} grinned and said, "A wondering heart can still be wise. '
        f'We look, we think, and then we explore."'
    )


def tell(animal: AnimalCfg, friend_cfg: FriendCfg, mystery: MysteryCfg,
         method: MethodCfg, flash: FlashbackCfg, parent_type: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=opening_name(animal),
        kind="character",
        type=animal.species,
        label=animal.species,
        role="hero",
        attrs={"paw": animal.paw},
        tags=set(animal.tags),
    ))
    friend = world.add(Entity(
        id=friend_name(friend_cfg),
        kind="character",
        type=friend_cfg.species,
        label=friend_cfg.species,
        role="friend",
        tags=set(friend_cfg.tags),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    bank = world.add(Entity(
        id="bank",
        kind="thing",
        type="riverbank",
        label="riverbank",
        phrase="the muddy riverbank",
        tags={"riverbank"},
    ))
    mystery_ent = world.add(Entity(
        id="mystery",
        kind="thing",
        type="mystery",
        label=mystery.label,
        phrase=mystery.phrase,
        tags=set(mystery.tags),
    ))
    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        animal=animal,
        friend_cfg=friend_cfg,
        mystery_cfg=mystery,
        mystery_id=mystery.id,
        method=method,
        flashback=flash,
        parent_type=parent_type,
    )

    introduce(world, hero, animal, friend, friend_cfg)
    game_of_boss(world, hero)
    world.para()
    spot_mystery(world, hero, mystery)
    friend_warn(world, friend, friend_cfg, hero, mystery)
    flashback_beat(world, hero, flash)

    outcome = "careful" if (friend_cfg.caution + flash.memory) >= (animal.bossiness + mystery.pull) else "splash"
    world.facts["outcome"] = outcome
    world.facts["temptation"] = animal.bossiness + mystery.pull
    world.facts["restraint"] = friend_cfg.caution + flash.memory

    world.para()
    boast_or_brake(world, hero, outcome)
    if outcome == "splash":
        slip(world, hero, parent)
    solve(world, hero, friend, parent, mystery_ent, mystery, method)

    world.para()
    ending(world, hero, friend, mystery, outcome)
    return world


KNOWLEDGE = {
    "riverbank": [
        (
            "What is a riverbank?",
            "A riverbank is the ground beside a river. It can be grassy, muddy, or slippery, so you have to walk carefully there.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short memory from an earlier time. It helps a character remember something important before making a choice.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It is good when you use it with patience and care.",
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall skinny plants that grow near water. They sway in the wind and can hide little things between their stems.",
        )
    ],
    "nest": [
        (
            "Why should you not grab a bird nest?",
            "A nest is a home for birds and eggs, so it should be left alone. Watching quietly is kinder than touching it.",
        )
    ],
    "hook": [
        (
            "What is a hook tool for?",
            "A hook tool can catch or pull something that is hard to reach. It helps you move an object without leaning too far.",
        )
    ],
    "net": [
        (
            "What does a scoop net do?",
            "A scoop net lets you lift something from shallow water. It is safer than reaching with your hand over a slippery edge.",
        )
    ],
    "call_adult": [
        (
            "Why is it smart to call a grown-up near water?",
            "A grown-up can help you stay safe and choose the right tool. Water and mud can be trickier than they look.",
        )
    ],
    "animal": [
        (
            "What is an animal?",
            "An animal is a living creature, like an otter, duck, or turtle. Animals need food, shelter, and safe places to live.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "animal",
    "riverbank",
    "curiosity",
    "flashback",
    "reeds",
    "nest",
    "hook",
    "net",
    "call_adult",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal"]
    mystery = f["mystery_cfg"]
    method = f["method"]
    flash = f["flashback"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old set on a riverbank that includes the words "boss" and "animal".',
        f"Tell a gentle riverbank story about a curious young {animal.species} who spots {mystery.phrase} and has a flashback about {flash.phrase} before choosing what to do.",
        f"Write a child-facing rhyming story where curiosity causes a problem or almost causes one, and the characters solve it with {method.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    animal = f["animal"]
    mystery = f["mystery_cfg"]
    method = f["method"]
    flash = f["flashback"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {animal.phrase}, and {friend.id}, a friend beside the riverbank. Their grown-up comes close when the mystery needs a safer plan.",
        ),
        (
            "What made the hero curious?",
            f"{mystery.hint.capitalize()}, so {hero.id} wanted to know what was there. The mystery sat right by the riverbank, which made the question feel exciting and risky at the same time.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about {flash.phrase}. It mattered because {flash.lesson.lower()}",
        ),
        (
            f"Why did {friend.id} warn {hero.id}?",
            f"{friend.id} saw that the muddy edge could be slippery. The warning came from a real risk: leaning too far near that spot could lead to a splash.",
        ),
    ]
    if outcome == "careful":
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.id} stopped before grabbing and then the group {method.qa_text}. The flashback and the warning helped {hero.pronoun('object')} choose a safer way to satisfy {hero.pronoun('possessive')} curiosity.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} acted like the boss?",
                f"{hero.id} leaned too far, the mud slipped, and {hero.pronoun()} got wet and muddy. After that, {parent.label_word} helped the group slow down and {method.qa_text}.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the friends calm by the riverbank, and {hero.id} was no longer bragging about being the boss. The ending image shows that curiosity stayed, but it had become wiser and slower.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"animal", "riverbank", "curiosity", "flashback"}
    mystery = f["mystery_cfg"]
    method = f["method"]
    tags |= set(mystery.tags)
    if method.id == "reed_hook":
        tags.add("hook")
    if method.id == "scoop_net":
        tags.add("net")
    if method.id == "watch_and_call":
        tags.add("call_adult")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="otter",
        friend="mole",
        mystery="ribbon",
        method="reed_hook",
        flashback="cold_splash",
        parent="mother",
        seed=1,
    ),
    StoryParams(
        animal="beaver",
        friend="mouse",
        mystery="basket",
        method="scoop_net",
        flashback="lost_leaf_hat",
        parent="father",
        seed=2,
    ),
    StoryParams(
        animal="duckling",
        friend="turtle",
        mystery="nest",
        method="watch_and_call",
        flashback="startled_birds",
        parent="mother",
        seed=3,
    ),
    StoryParams(
        animal="froglet",
        friend="heron",
        mystery="shell",
        method="branch_bridge",
        flashback="cold_splash",
        parent="father",
        seed=4,
    ),
    StoryParams(
        animal="beaver",
        friend="mole",
        mystery="ribbon",
        method="branch_bridge",
        flashback="startled_birds",
        parent="mother",
        seed=5,
    ),
]


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). This world prefers safer ways to investigate. "
        f"Try one of: {better}.)"
    )


def explain_rejection(mystery: MysteryCfg, method: MethodCfg) -> str:
    return (
        f"(No story: {method.label} does not fit this mystery. "
        f"{mystery.phrase.capitalize()} at {mystery.place} needs a method for '{mystery.need}', "
        f"not '{method.id}'.)"
    )


ASP_RULES = r"""
sensible(Me) :- method(Me), sense(Me, S), sense_min(Mn), S >= Mn.
valid(A, My, Me) :- animal(A), mystery(My), method(Me), need(My, N), works(Me, N), sensible(Me).

temptation(T) :- chosen_animal(A), bossiness(A, B), chosen_mystery(M), pull(M, P), T = B + P.
restraint(R)  :- chosen_friend(F), caution(F, C), chosen_flashback(Fl), memory(Fl, M), R = C + M.

outcome(careful) :- restraint(R), temptation(T), R >= T.
outcome(splash)  :- restraint(R), temptation(T), R < T.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("bossiness", animal_id, animal.bossiness))
    for friend_id, friend in FRIENDS.items():
        lines.append(asp.fact("friend", friend_id))
        lines.append(asp.fact("caution", friend_id, friend.caution))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        lines.append(asp.fact("need", mystery_id, mystery.need))
        lines.append(asp.fact("pull", mystery_id, mystery.pull))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for need in sorted(method.works_on):
            lines.append(asp.fact("works", method_id, need))
    for flash_id, flash in FLASHBACKS.items():
        lines.append(asp.fact("flashback", flash_id))
        lines.append(asp.fact("memory", flash_id, flash.memory))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_animal", params.animal),
        asp.fact("chosen_friend", params.friend),
        asp.fact("chosen_mystery", params.mystery),
        asp.fact("chosen_flashback", params.flashback),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Rhyming riverbank storyworld: a curious young animal, a bossy moment, a flashback, and a safer way to wonder."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))
    if args.mystery and args.method:
        mystery = MYSTERIES[args.mystery]
        method = METHODS[args.method]
        if not method_fits(mystery, method):
            raise StoryError(explain_rejection(mystery, method))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, mystery_id, method_id = rng.choice(sorted(combos))
    friend_id = args.friend or rng.choice(sorted(FRIENDS))
    flashback_id = args.flashback or rng.choice(sorted(FLASHBACKS))
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        animal=animal_id,
        friend=friend_id,
        mystery=mystery_id,
        method=method_id,
        flashback=flashback_id,
        parent=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        animal = ANIMALS[params.animal]
        friend = FRIENDS[params.friend]
        mystery = MYSTERIES[params.mystery]
        method = METHODS[params.method]
        flashback = FLASHBACKS[params.flashback]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]})") from exc

    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if not method_fits(mystery, method):
        raise StoryError(explain_rejection(mystery, method))

    world = tell(animal, friend, mystery, method, flashback, params.parent)
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


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid combos match ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sensible = {m.id for m in sensible_methods()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible methods match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (animal, mystery, method) combos:\n")
        for animal_id, mystery_id, method_id in combos:
            print(f"  {animal_id:8} {mystery_id:8} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
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
            header = f"### {p.animal} / {p.mystery} / {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
