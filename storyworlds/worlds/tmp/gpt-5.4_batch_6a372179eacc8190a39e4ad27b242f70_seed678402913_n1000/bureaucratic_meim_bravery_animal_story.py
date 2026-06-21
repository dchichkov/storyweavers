#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bureaucratic_meim_bravery_animal_story.py
====================================================================

A standalone story world for a gentle animal tale about bravery, a funny
bureaucratic little office, and the tiny "meim" sound of a stamp.

Premise
-------
A young animal wants to bring something comforting to a friend, but a tricky
path lies in the way. The unsafe move would be to rush across without the proper
help. The brave move is smaller and wiser: admit the worry, ask at the woodland
desk, wait for the right stamp or gear, and cross safely.

World logic
-----------
This world keeps the constraint small and concrete:

* Each obstacle has a required set of protections.
* Small animals need extra help on the swaying bridge.
* Each aid package grants a set of protections.
* A story is only valid when the chosen aid really makes the obstacle safe.

The bureaucratic flavor is not cruel or harsh here. The forest desk is fussy,
slow, and full of forms and stamps, but the grown-up lesson is that brave
children can speak up, ask for help, and use the safe system instead of taking a
risky shortcut.

Run it
------
    python storyworlds/worlds/gpt-5.4/bureaucratic_meim_bravery_animal_story.py
    python storyworlds/worlds/gpt-5.4/bureaucratic_meim_bravery_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/bureaucratic_meim_bravery_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/bureaucratic_meim_bravery_animal_story.py --verify
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
SMALL_SIZES = {"tiny", "small"}


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
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return table[case]

    def be(self) -> str:
        return "were"

    def have(self) -> str:
        return "had"


@dataclass
class Species:
    id: str
    label: str
    size: str
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    need: str
    delivered_text: str
    at_risk_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    risk: str
    requires: set[str] = field(default_factory=set)
    small_requires: set[str] = field(default_factory=set)
    shortcut_text: str = ""
    danger_text: str = ""
    cross_text: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    grants: set[str] = field(default_factory=set)
    ask_text: str = ""
    equip_text: str = ""
    cross_help_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


def _required_tokens_for(world: World) -> set[str]:
    obstacle = world.facts["obstacle_cfg"]
    species = world.facts["hero_species_cfg"]
    need = set(obstacle.requires)
    if species.size in SMALL_SIZES:
        need |= set(obstacle.small_requires)
    return need


def _r_exposed(world: World) -> list[str]:
    hero = world.get("hero")
    cargo = world.get("cargo")
    obstacle = world.get("obstacle")
    need = _required_tokens_for(world)
    have = set(hero.attrs.get("protections", set()))
    if obstacle.meters["approached"] < THRESHOLD:
        return []
    if need.issubset(have):
        return []
    sig = ("exposed", tuple(sorted(need - have)))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    cargo.meters["risk"] += 1
    return ["__risk__"]


def _r_safe_path(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    need = _required_tokens_for(world)
    have = set(hero.attrs.get("protections", set()))
    if obstacle.meters["approached"] < THRESHOLD:
        return []
    if not need.issubset(have):
        return []
    sig = ("safe", tuple(sorted(need)))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["safe"] += 1
    hero.memes["confidence"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="exposed", tag="risk", apply=_r_exposed),
    Rule(name="safe_path", tag="safety", apply=_r_safe_path),
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
        for line in produced:
            world.say(line)
    return produced


SPECIES = {
    "mouse": Species(
        id="mouse",
        label="mouse",
        size="tiny",
        style="small enough to slip through almost anything, though a swaying bridge feels huge",
        tags={"mouse", "small_animals"},
    ),
    "squirrel": Species(
        id="squirrel",
        label="squirrel",
        size="small",
        style="quick and bright-eyed, with a tail that twitched when feelings were big",
        tags={"squirrel", "small_animals"},
    ),
    "rabbit": Species(
        id="rabbit",
        label="rabbit",
        size="small",
        style="soft-footed and careful, with long ears that lifted at every new sound",
        tags={"rabbit", "small_animals"},
    ),
    "badger": Species(
        id="badger",
        label="badger",
        size="medium",
        style="sturdy and slow to boast, but very steady once a choice was made",
        tags={"badger"},
    ),
    "fox": Species(
        id="fox",
        label="fox",
        size="medium",
        style="light on the paws and sharp-eyed, though even sharp eyes can feel nervous",
        tags={"fox"},
    ),
}

CARGO = {
    "soup": Cargo(
        id="soup",
        label="soup",
        phrase="a warm acorn soup in a corked jar",
        need="a warm supper",
        delivered_text="The jar was still warm when it arrived.",
        at_risk_text="If the path went badly, the soup would spill and the warm supper would be lost.",
        tags={"soup", "helping"},
    ),
    "bandage": Cargo(
        id="bandage",
        label="bandage leaf",
        phrase="a clean bandage leaf tied with grass",
        need="a soft wrapping for a sore paw",
        delivered_text="The leaf stayed clean and smooth, ready to wrap a sore paw.",
        at_risk_text="If the path went badly, the clean leaf would get muddy and no longer help.",
        tags={"bandage", "helping"},
    ),
    "cake": Cargo(
        id="cake",
        label="seed cake",
        phrase="a round seed cake with two shiny berries on top",
        need="a cheering treat",
        delivered_text="Not a single berry slid off the top.",
        at_risk_text="If the path went badly, the cake would tumble apart before it reached its friend.",
        tags={"cake", "helping"},
    ),
}

OBSTACLES = {
    "bridge": Obstacle(
        id="bridge",
        label="the bridge",
        scene="a rope bridge that swayed above the brook",
        risk="swaying planks and a windy middle",
        requires={"pass"},
        small_requires={"rope"},
        shortcut_text="The planks clacked and the brook rushed below. It looked faster to hurry across without stopping at the desk.",
        danger_text="A small traveler could wobble there, and careful paws might still lose what they were carrying.",
        cross_text="step by step over the bridge while the brook muttered below",
        ending_image="On the far bank, the bridge still swayed behind them, but the parcel in their paws did not shake at all.",
        tags={"bridge", "bureaucratic_path"},
    ),
    "tunnel": Obstacle(
        id="tunnel",
        label="the tunnel",
        scene="a reed tunnel under the hill where the daylight turned green and dim",
        risk="dark turns and a drippy floor",
        requires={"lantern"},
        small_requires=set(),
        shortcut_text="The tunnel mouth was only a dark oval. It would be easy to duck inside and hope for the best.",
        danger_text="In the dark, a traveler could bump the wall, miss a turn, and drop what they meant to carry safely.",
        cross_text="pad through the dim tunnel while the lantern made a warm circle of light",
        ending_image="Behind them, the tunnel stayed green and shadowy, but ahead the doorway glowed like morning.",
        tags={"tunnel", "dark"},
    ),
    "puddles": Obstacle(
        id="puddles",
        label="the puddle lane",
        scene="a lane of silver puddles splashed across the path",
        risk="slick mud and splashy stepping-stones",
        requires={"boots"},
        small_requires=set(),
        shortcut_text="The stones looked close together. It would be easy to skip the desk and start hopping from one shiny patch to the next.",
        danger_text="One slip would splash muddy water high, and small paws might save themselves but not the thing they were carrying.",
        cross_text="pick a dry rhythm through the puddle lane",
        ending_image="The puddles still flashed in the sun behind them, but the bundle they carried stayed neat and dry.",
        tags={"puddles", "mud"},
    ),
}

AIDS = {
    "bridge_pass": Aid(
        id="bridge_pass",
        label="bridge pass",
        phrase="a stamped bridge pass on stiff bark paper",
        grants={"pass"},
        ask_text="ask for a bridge pass",
        equip_text="Meim slid over a neat bark pass with a red string through the corner.",
        cross_help_text="The pass let the bridge keeper nod them through.",
        tags={"pass", "stamp", "bridge"},
    ),
    "guide_kit": Aid(
        id="guide_kit",
        label="guide kit",
        phrase="a stamped bridge pass and a soft guide rope",
        grants={"pass", "rope"},
        ask_text="ask for the little-traveler guide kit",
        equip_text="Meim handed over a bark pass and looped a soft guide rope into a tidy circle.",
        cross_help_text="The pass opened the gate, and the guide rope kept each brave little step steady.",
        tags={"pass", "rope", "stamp", "bridge"},
    ),
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a tiny jar lantern with a glow-seed inside",
        grants={"lantern"},
        ask_text="ask to borrow the tunnel lantern",
        equip_text="Meim lifted down a tiny jar lantern, and the glow-seed inside shone like a sleepy star.",
        cross_help_text="The lantern turned each dark turn into something easy to see.",
        tags={"lantern", "light"},
    ),
    "boots": Aid(
        id="boots",
        label="boots",
        phrase="a pair of waxed leaf boots",
        grants={"boots"},
        ask_text="ask for the puddle boots",
        equip_text="Meim found a pair of waxed leaf boots and tied them snugly at the ankles.",
        cross_help_text="The boots kept the splashes low and the careful steps sure.",
        tags={"boots", "mud"},
    ),
}


def required_tokens(species: Species, obstacle: Obstacle) -> set[str]:
    need = set(obstacle.requires)
    if species.size in SMALL_SIZES:
        need |= set(obstacle.small_requires)
    return need


def aid_covers(species: Species, obstacle: Obstacle, aid: Aid) -> bool:
    return required_tokens(species, obstacle).issubset(set(aid.grants))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for species_id, species in SPECIES.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for aid_id, aid in AIDS.items():
                if aid_covers(species, obstacle, aid):
                    combos.append((species_id, obstacle_id, aid_id))
    return sorted(combos)


@dataclass
class StoryParams:
    species: str
    obstacle: str
    aid: str
    cargo: str
    hero_name: str
    friend_name: str
    friend_species: str
    clerk_name: str = "Meim"
    seed: Optional[int] = None


GIRLISH_NAMES = ["Pip", "Mimi", "Tansy", "Nell", "Moss", "Poppy", "Wren", "Daisy"]
BOYISH_NAMES = ["Pip", "Bram", "Ollie", "Nook", "Moss", "Tad", "Ash", "Rowan"]
NEUTRAL_NAMES = ["Pip", "Moss", "Pebble", "Clover", "Juniper", "Nook", "Tansy", "Bram"]

CURATED = [
    StoryParams(
        species="mouse",
        obstacle="bridge",
        aid="guide_kit",
        cargo="soup",
        hero_name="Pip",
        friend_name="Moss",
        friend_species="rabbit",
        clerk_name="Meim",
    ),
    StoryParams(
        species="badger",
        obstacle="bridge",
        aid="bridge_pass",
        cargo="cake",
        hero_name="Bram",
        friend_name="Tansy",
        friend_species="squirrel",
        clerk_name="Meim",
    ),
    StoryParams(
        species="rabbit",
        obstacle="tunnel",
        aid="lantern",
        cargo="bandage",
        hero_name="Nell",
        friend_name="Pebble",
        friend_species="fox",
        clerk_name="Meim",
    ),
    StoryParams(
        species="squirrel",
        obstacle="puddles",
        aid="boots",
        cargo="cake",
        hero_name="Juniper",
        friend_name="Clover",
        friend_species="mouse",
        clerk_name="Meim",
    ),
]


def pick_name(rng: random.Random, avoid: str = "") -> str:
    pool = [n for n in NEUTRAL_NAMES if n != avoid]
    return rng.choice(pool)


def explain_rejection(species: Species, obstacle: Obstacle, aid: Aid) -> str:
    need = sorted(required_tokens(species, obstacle))
    have = sorted(aid.grants)
    return (
        f"(No story: {species.label} crossing {obstacle.label} needs {need}, "
        f"but {aid.label} only provides {have}. The safe help must really match "
        f"the obstacle.)"
    )


def introduce(world: World, hero: Entity, friend: Entity, cargo: Entity, cargo_cfg: Cargo, species: Species) -> None:
    hero.memes["care"] += 1
    world.say(
        f"{hero.id} the {species.label} was {species.style}."
    )
    world.say(
        f"That morning, {friend.id} the {friend.type} was waiting at the far burrow and needed {cargo_cfg.need}."
    )
    world.say(
        f"So {hero.id} set out carrying {cargo_cfg.phrase} for {friend.id}."
    )


def reach_obstacle(world: World, hero: Entity, obstacle: Entity, obstacle_cfg: Obstacle) -> None:
    obstacle.meters["approached"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before long, {hero.id} reached {obstacle_cfg.scene}."
    )
    world.say(
        f"It was a place of {obstacle_cfg.risk}."
    )
    world.say(obstacle_cfg.shortcut_text)


def imagine_rush(world: World, cargo_cfg: Cargo, obstacle_cfg: Obstacle) -> None:
    pred = predict_risk(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f"{obstacle_cfg.danger_text} {cargo_cfg.at_risk_text}"
    )


def office_scene(world: World, hero: Entity, clerk: Entity, aid_cfg: Aid) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Beside the path stood the Bureau of Small Paths, a tiny stump office with clipboards, numbered leaves, and shelves of borrowed gear."
    )
    world.say(
        f"It looked almost bureaucratic, which made {hero.id}'s whiskers tingle."
    )
    world.say(
        f"At the desk sat {clerk.id}, the patient turtle clerk, who could stamp passes and lend exactly the right things."
    )
    world.say(
        f"{hero.id} wanted to turn away rather than {aid_cfg.ask_text}."
    )


def brave_choice(world: World, hero: Entity, clerk: Entity, aid_cfg: Aid) -> None:
    hero.memes["bravery"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    world.say(
        f"But bravery did not mean running at the problem. It meant taking one deep breath, stepping up to the desk, and saying, "
        f'"Please, may I {aid_cfg.ask_text}?"'
    )
    world.say(
        f'{clerk.id} smiled. "That is a very brave thing to ask when you feel fluttery," {clerk.pronoun()} said.'
    )


def stamp_and_equip(world: World, hero: Entity, aid_ent: Entity, aid_cfg: Aid) -> None:
    hero.attrs["protections"] = set(aid_cfg.grants)
    aid_ent.attrs["grants"] = set(aid_cfg.grants)
    hero.memes["confidence"] += 1
    world.say(
        f"{aid_cfg.equip_text}"
    )
    world.say(
        'Then the red stamp came down on the bark card and made a funny little sound: "meim."'
    )
    world.say(
        f"The sound made {hero.id} smile, because now the scary path had a plan."
    )


def cross(world: World, hero: Entity, cargo: Entity, obstacle: Entity, obstacle_cfg: Obstacle, aid_cfg: Aid) -> None:
    obstacle.meters["approached"] += 1
    propagate(world, narrate=False)
    if obstacle.meters["safe"] < THRESHOLD:
        raise StoryError("Internal story error: attempted crossing without safe aid.")
    cargo.meters["delivered"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"With {aid_cfg.phrase}, {hero.id} could {obstacle_cfg.cross_text}."
    )
    world.say(
        f"{aid_cfg.cross_help_text}"
    )


def deliver(world: World, hero: Entity, friend: Entity, cargo_cfg: Cargo, obstacle_cfg: Obstacle) -> None:
    friend.memes["comfort"] += 1
    world.say(
        f"When {hero.id} reached the far side, {friend.id} was waiting by the door with hopeful eyes."
    )
    world.say(
        f"{cargo_cfg.delivered_text} {friend.id} took it in both paws and smiled so wide that the whole doorway seemed warmer."
    )
    world.say(
        f"{obstacle_cfg.ending_image} {hero.id} felt taller inside, because asking for help had carried them farther than a reckless dash ever could."
    )


def tell(
    species_cfg: Species,
    obstacle_cfg: Obstacle,
    aid_cfg: Aid,
    cargo_cfg: Cargo,
    hero_name: str,
    friend_name: str,
    friend_species_cfg: Species,
    clerk_name: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=species_cfg.label,
        label=species_cfg.label,
        role="hero",
        tags=set(species_cfg.tags),
        attrs={"size": species_cfg.size, "protections": set()},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_species_cfg.label,
        label=friend_species_cfg.label,
        role="friend",
        tags=set(friend_species_cfg.tags),
    ))
    clerk = world.add(Entity(
        id=clerk_name,
        kind="character",
        type="turtle",
        label="turtle clerk",
        role="clerk",
        tags={"turtle", "bureaucratic"},
    ))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type=cargo_cfg.label,
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        tags=set(cargo_cfg.tags),
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        kind="thing",
        type=obstacle_cfg.id,
        label=obstacle_cfg.label,
        tags=set(obstacle_cfg.tags),
    ))
    aid_ent = world.add(Entity(
        id="aid",
        kind="thing",
        type=aid_cfg.id,
        label=aid_cfg.label,
        phrase=aid_cfg.phrase,
        tags=set(aid_cfg.tags),
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        clerk=clerk,
        cargo=cargo,
        obstacle=obstacle,
        aid=aid_ent,
        hero_species_cfg=species_cfg,
        friend_species_cfg=friend_species_cfg,
        cargo_cfg=cargo_cfg,
        obstacle_cfg=obstacle_cfg,
        aid_cfg=aid_cfg,
        required=sorted(required_tokens(species_cfg, obstacle_cfg)),
        brave=True,
    )

    introduce(world, hero, friend, cargo, cargo_cfg, species_cfg)
    world.para()
    reach_obstacle(world, hero, obstacle, obstacle_cfg)
    imagine_rush(world, cargo_cfg, obstacle_cfg)
    world.para()
    office_scene(world, hero, clerk, aid_cfg)
    brave_choice(world, hero, clerk, aid_cfg)
    stamp_and_equip(world, hero, aid_ent, aid_cfg)
    world.para()
    cross(world, hero, cargo, obstacle, obstacle_cfg, aid_cfg)
    deliver(world, hero, friend, cargo_cfg, obstacle_cfg)
    return world


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("obstacle").meters["approached"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("cargo").meters["risk"] >= THRESHOLD,
        "fear": sim.get("hero").memes["fear"],
    }


KNOWLEDGE = {
    "bridge": [
        (
            "Why can a bridge feel scary to a small animal?",
            "A bridge can sway and bounce, and a small body feels that movement more strongly. Holding the right support can make each step steadier."
        )
    ],
    "tunnel": [
        (
            "Why is a lantern useful in a dark tunnel?",
            "A lantern makes a circle of light so you can see where to step and where to turn. Seeing clearly helps your body stay calm and careful."
        )
    ],
    "puddles": [
        (
            "Why do boots help in puddles?",
            "Boots keep splashes and mud off your feet and ankles. That makes it easier to walk without slipping."
        )
    ],
    "stamp": [
        (
            "What does a stamp do in a little office?",
            "A stamp marks a paper to show that something has been checked or allowed. It helps people know the safe rules have been followed."
        )
    ],
    "bureaucratic": [
        (
            "What does bureaucratic mean?",
            "Bureaucratic means full of rules, papers, and careful steps before something is allowed. It can feel slow, but sometimes those steps help keep everyone safe."
        )
    ],
    "bravery": [
        (
            "Is bravery the same as rushing into danger?",
            "No. Bravery can mean telling the truth about being scared and still choosing the wise thing to do."
        )
    ],
    "helping": [
        (
            "Why is bringing something to a sick or sad friend kind?",
            "It shows you noticed what your friend needed and took time to help. Kind help can warm both the giver and the receiver."
        )
    ],
}
KNOWLEDGE_ORDER = ["bureaucratic", "stamp", "bridge", "tunnel", "puddles", "bravery", "helping"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    species = world.facts["hero_species_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    cargo = world.facts["cargo_cfg"]
    return [
        f'Write an Animal Story for a 3-to-5-year-old that includes the words "bureaucratic" and "meim" and shows bravery in a gentle way.',
        f"Tell a story about {hero.id} the {species.label}, who wants to carry {cargo.phrase} across {obstacle.label} and learns that brave asking can be better than brave rushing.",
        f'Write a short forest tale where a child faces a fussy little office, hears a stamp go "meim," and ends the story feeling bigger inside.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    clerk = world.facts["clerk"]
    cargo_cfg = world.facts["cargo_cfg"]
    obstacle_cfg = world.facts["obstacle_cfg"]
    aid_cfg = world.facts["aid_cfg"]
    req = world.facts["required"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {hero.type}, who wanted to help {friend.id}. {hero.id} had to carry {cargo_cfg.phrase} across {obstacle_cfg.label}."
        ),
        (
            f"Why did {hero.id} stop instead of rushing ahead?",
            f"{hero.id} stopped because {obstacle_cfg.label} looked risky without the right help. If {hero.pronoun()} had rushed, {cargo_cfg.at_risk_text.lower()}"
        ),
        (
            "What was bureaucratic in the story?",
            f"The little Bureau of Small Paths was bureaucratic because it had clipboards, numbered leaves, and careful rules before anyone crossed. It felt fussy, but the rules helped {hero.id} get the right safe help."
        ),
        (
            'What made the "meim" sound?',
            f'The red stamp at {clerk.id}\'s desk made the "meim" sound when it came down on the bark card. That sound showed {hero.id} now had a real plan instead of only a worried feeling.'
        ),
        (
            f"How was {hero.id} brave?",
            f"{hero.id} was brave by walking up to the desk and asking for help even while feeling fluttery. The brave part was choosing the wise safe step, not pretending there was no fear."
        ),
        (
            f"How did {aid_cfg.label} help {hero.id}?",
            f"It gave {hero.id} what {obstacle_cfg.label} required: {', '.join(req)}. Because the help matched the danger, {hero.pronoun()} could cross safely and keep the gift safe too."
        ),
        (
            "How did the story end?",
            f"{hero.id} reached {friend.id} with the gift still safe, and both of them felt warmer and calmer. The ending shows that asking for help changed fear into a steady kind of bravery."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bureaucratic", "stamp", "bravery", "helping"}
    tags |= set(world.facts["obstacle_cfg"].tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {}
            for key, value in ent.attrs.items():
                if isinstance(value, set):
                    if value:
                        shown[key] = sorted(value)
                elif value not in ("", None, [], {}):
                    shown[key] = value
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
small_size(tiny).
small_size(small).

needs(Species, Obstacle, Need) :-
    species(Species), obstacle(Obstacle), required(Obstacle, Need).

needs(Species, Obstacle, Need) :-
    species(Species), size(Species, Sz), small_size(Sz),
    obstacle(Obstacle), small_required(Obstacle, Need).

covers(Species, Obstacle, Aid) :-
    species(Species), obstacle(Obstacle), aid(Aid),
    not missing_need(Species, Obstacle, Aid).

missing_need(Species, Obstacle, Aid) :-
    needs(Species, Obstacle, Need),
    not grants(Aid, Need).

valid(Species, Obstacle, Aid) :-
    species(Species), obstacle(Obstacle), aid(Aid),
    covers(Species, Obstacle, Aid).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for species_id, species in SPECIES.items():
        lines.append(asp.fact("species", species_id))
        lines.append(asp.fact("size", species_id, species.size))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        for token in sorted(obstacle.requires):
            lines.append(asp.fact("required", obstacle_id, token))
        for token in sorted(obstacle.small_requires):
            lines.append(asp.fact("small_required", obstacle_id, token))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for token in sorted(aid.grants):
            lines.append(asp.fact("grants", aid_id, token))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: bravery, a bureaucratic little office, and the safe help that really fits the path."
    )
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-species", choices=SPECIES)
    ap.add_argument("--clerk-name", default="Meim")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.species and args.obstacle and args.aid:
        species_cfg = SPECIES[args.species]
        obstacle_cfg = OBSTACLES[args.obstacle]
        aid_cfg = AIDS[args.aid]
        if not aid_covers(species_cfg, obstacle_cfg, aid_cfg):
            raise StoryError(explain_rejection(species_cfg, obstacle_cfg, aid_cfg))

    combos = [
        combo for combo in valid_combos()
        if (args.species is None or combo[0] == args.species)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    species_id, obstacle_id, aid_id = rng.choice(combos)
    cargo_id = args.cargo or rng.choice(sorted(CARGO))
    hero_name = args.hero_name or pick_name(rng)
    friend_name = args.friend_name or pick_name(rng, avoid=hero_name)
    friend_species = args.friend_species or rng.choice(sorted(SPECIES))
    return StoryParams(
        species=species_id,
        obstacle=obstacle_id,
        aid=aid_id,
        cargo=cargo_id,
        hero_name=hero_name,
        friend_name=friend_name,
        friend_species=friend_species,
        clerk_name=args.clerk_name or "Meim",
    )


def generate(params: StoryParams) -> StorySample:
    if params.species not in SPECIES:
        raise StoryError(f"Unknown species: {params.species}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.aid not in AIDS:
        raise StoryError(f"Unknown aid: {params.aid}")
    if params.cargo not in CARGO:
        raise StoryError(f"Unknown cargo: {params.cargo}")
    if params.friend_species not in SPECIES:
        raise StoryError(f"Unknown friend species: {params.friend_species}")

    species_cfg = SPECIES[params.species]
    obstacle_cfg = OBSTACLES[params.obstacle]
    aid_cfg = AIDS[params.aid]
    cargo_cfg = CARGO[params.cargo]
    if not aid_covers(species_cfg, obstacle_cfg, aid_cfg):
        raise StoryError(explain_rejection(species_cfg, obstacle_cfg, aid_cfg))

    world = tell(
        species_cfg=species_cfg,
        obstacle_cfg=obstacle_cfg,
        aid_cfg=aid_cfg,
        cargo_cfg=cargo_cfg,
        hero_name=params.hero_name,
        friend_name=params.friend_name,
        friend_species_cfg=SPECIES[params.friend_species],
        clerk_name=params.clerk_name,
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


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verify failed to run clingo: {exc}")
        return 1

    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "meim" not in sample.story.lower() or "bureaucratic" not in sample.story.lower():
            raise StoryError("Smoke test story did not contain required seed words.")
        print("OK: curated smoke test generated a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story:
            raise StoryError("Random smoke test produced empty story.")
        print("OK: random generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (species, obstacle, aid) combos:\n")
        for species, obstacle, aid in combos:
            print(f"  {species:9} {obstacle:8} {aid}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} the {p.species}: {p.obstacle} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
