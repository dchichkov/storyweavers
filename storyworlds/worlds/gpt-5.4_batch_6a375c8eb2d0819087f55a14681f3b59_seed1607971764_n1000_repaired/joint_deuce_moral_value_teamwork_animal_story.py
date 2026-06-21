#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/joint_deuce_moral_value_teamwork_animal_story.py
============================================================================

A standalone story world for gentle animal stories about a tied game, a broken
wagon joint, and a lesson in teamwork.

Seed instruments:
- words: "joint", "deuce"
- features: Moral Value, Teamwork
- style: Animal Story

Premise
-------
Two young animals are carrying something important to a meadow game. Their warm-up
score reaches deuce, and each friend starts wanting the next point for themself.
Then their little wagon jolts on the path and a wooden joint comes loose. The
cargo is suddenly at risk. If they stop tugging against each other and use a
sensible fix together, they arrive in time and discover that sharing effort feels
better than winning alone. If they bicker too long or choose a weak fix, the
cargo spills and the game must wait, but they still learn the same lesson.

Run it
------
python storyworlds/worlds/gpt-5.4/joint_deuce_moral_value_teamwork_animal_story.py
python storyworlds/worlds/gpt-5.4/joint_deuce_moral_value_teamwork_animal_story.py --all
python storyworlds/worlds/gpt-5.4/joint_deuce_moral_value_teamwork_animal_story.py --cargo berry_basket --breakdown handle_joint --fix vine_wrap
python storyworlds/worlds/gpt-5.4/joint_deuce_moral_value_teamwork_animal_story.py --fix leaf_band
python storyworlds/worlds/gpt-5.4/joint_deuce_moral_value_teamwork_animal_story.py --verify
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
TEAM_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Game:
    id: str
    label: str
    gear: str
    score_line: str
    play_line: str
    finish_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    fragile: int
    uses_wagon: bool = True
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Breakdown:
    id: str
    label: str
    kind: str
    severity: int
    text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    kinds: set[str]
    power: int
    teamwork: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Temper:
    id: str
    calm: int
    empathy: int
    boast: int
    line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    game: str
    cargo: str
    breakdown: str
    fix: str
    temper: str
    friend_one: str
    species_one: str
    friend_two: str
    species_two: str
    elder: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_risk(world: World) -> list[str]:
    cart = world.get("cart")
    cargo = world.get("cargo")
    if cart.meters["broken"] < THRESHOLD or cart.meters["repaired"] >= THRESHOLD:
        return []
    sig = ("risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["at_risk"] += 1
    for friend_id in ("friend1", "friend2"):
        world.get(friend_id).memes["worry"] += 1
    return ["__risk__"]


def _r_spill(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["at_risk"] < THRESHOLD:
        return []
    if world.get("friend1").meters["pulling_alone"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["spilled"] += 1
    cargo.meters["safe"] = 0.0
    for friend_id in ("friend1", "friend2"):
        world.get(friend_id).memes["sad"] += 1
        world.get(friend_id).memes["regret"] += 1
    return ["__spill__"]


def _r_stable(world: World) -> list[str]:
    cart = world.get("cart")
    cargo = world.get("cargo")
    if cart.meters["repaired"] < THRESHOLD:
        return []
    sig = ("stable",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["at_risk"] = 0.0
    cargo.meters["safe"] += 1
    for friend_id in ("friend1", "friend2"):
        world.get(friend_id).memes["relief"] += 1
        world.get(friend_id).memes["teamwork"] += 1
    return ["__stable__"]


CAUSAL_RULES = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="stable", tag="physical", apply=_r_stable),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


GAMES = {
    "acorn_roll": Game(
        id="acorn_roll",
        label="acorn roll",
        gear="smooth acorns",
        score_line="Soon the score was deuce, two points each.",
        play_line="They rolled shiny acorns between willow roots and cheered for every neat little curve.",
        finish_line="At the meadow, they took the last turn together and sent one acorn gliding straight through the ring.",
        tags={"game", "deuce", "acorn"},
    ),
    "reed_ball": Game(
        id="reed_ball",
        label="reed-ball",
        gear="a soft reed ball",
        score_line="Soon the score was deuce, with the points tied.",
        play_line="They tapped the soft reed ball back and forth and laughed each time it bounced off a mossy stone.",
        finish_line="At the meadow, they passed the reed ball to each other and scored with one shared tap.",
        tags={"game", "deuce", "ball"},
    ),
    "pebble_flip": Game(
        id="pebble_flip",
        label="pebble flip",
        gear="flat river pebbles",
        score_line="Soon the score was deuce, and nobody was ahead.",
        play_line="They flipped flat pebbles toward a painted stump and listened for the tidy click of stone on bark.",
        finish_line="At the meadow, they counted one last turn together and landed the pebble right on the bright stump top.",
        tags={"game", "deuce", "pebble"},
    ),
}

CARGOS = {
    "berry_basket": Cargo(
        id="berry_basket",
        label="berry basket",
        phrase="a basket of red berries for the meadow table",
        weight=1,
        fragile=1,
        uses_wagon=True,
        ending_image="The berries shone like little red lanterns in the grass.",
        tags={"berries", "food"},
    ),
    "seed_cakes": Cargo(
        id="seed_cakes",
        label="seed cakes",
        phrase="a tray of warm seed cakes for the teams to share",
        weight=2,
        fragile=2,
        uses_wagon=True,
        ending_image="The sweet seed cakes sat safe under a blue cloth, ready for many paws.",
        tags={"cakes", "food"},
    ),
    "goal_flags": Cargo(
        id="goal_flags",
        label="goal flags",
        phrase="a bundle of game flags for the finish line",
        weight=2,
        fragile=1,
        uses_wagon=True,
        ending_image="The bright flags fluttered over the meadow like happy leaves.",
        tags={"flags", "game"},
    ),
}

BREAKDOWNS = {
    "handle_joint": Breakdown(
        id="handle_joint",
        label="wagon handle joint",
        kind="joint",
        severity=2,
        text="a wooden joint under the wagon handle popped loose with a clack",
        tags={"joint", "wagon"},
    ),
    "wheel_peg": Breakdown(
        id="wheel_peg",
        label="wheel peg",
        kind="peg",
        severity=2,
        text="one wheel peg slipped out, and the wagon leaned to one side",
        tags={"wheel", "wagon"},
    ),
    "axle_crack": Breakdown(
        id="axle_crack",
        label="axle crack",
        kind="axle",
        severity=3,
        text="the little axle cracked and gave a worried creak",
        tags={"axle", "wagon"},
    ),
}

FIXES = {
    "vine_wrap": Fix(
        id="vine_wrap",
        label="vine wrap",
        kinds={"joint", "peg"},
        power=2,
        teamwork=1,
        text="looped a strong green vine around the loose place and pulled it snug together",
        fail="wrapped the place with vine, but the wagon still wobbled too much",
        qa_text="They looped a strong vine around the loose place and tightened it together",
        tags={"vine", "repair"},
    ),
    "stick_brace": Fix(
        id="stick_brace",
        label="stick brace",
        kinds={"joint", "axle", "peg"},
        power=3,
        teamwork=1,
        text="set a straight stick beside the break and tied it in place like a brace",
        fail="tied on a brace, but the wagon still sagged under the load",
        qa_text="They made a brace with a straight stick and tied it in place together",
        tags={"brace", "repair"},
    ),
    "leaf_band": Fix(
        id="leaf_band",
        label="leaf band",
        kinds={"joint"},
        power=1,
        teamwork=0,
        text="pressed broad leaves around the loose place and hoped that would be enough",
        fail="pressed leaves around the loose place, but they slipped at once",
        qa_text="They tried to hold the break with broad leaves",
        tags={"leaves", "repair"},
    ),
}

TEMPERS = {
    "patient": Temper(
        id="patient",
        calm=2,
        empathy=2,
        boast=0,
        line='They both took a breath. "Let us fix it together," they said at the same time.',
        tags={"teamwork", "patience"},
    ),
    "kind": Temper(
        id="kind",
        calm=1,
        empathy=2,
        boast=0,
        line='They looked at each other, and each one cared more about the other friend than about the next point.',
        tags={"teamwork", "kindness"},
    ),
    "showy": Temper(
        id="showy",
        calm=0,
        empathy=0,
        boast=2,
        line='Each one wanted to be the hero of the next point, so they both reached first and pulled at the wrong time.',
        tags={"pride"},
    ),
    "hasty": Temper(
        id="hasty",
        calm=0,
        empathy=1,
        boast=1,
        line='They hurried instead of listening, because the tied score made the next turn feel very important.',
        tags={"pride", "hurry"},
    ),
}

SPECIES = {
    "rabbit": {"label": "rabbit", "tags": {"rabbit"}},
    "otter": {"label": "otter", "tags": {"otter"}},
    "squirrel": {"label": "squirrel", "tags": {"squirrel"}},
    "beaver": {"label": "beaver", "tags": {"beaver"}},
    "hedgehog": {"label": "hedgehog", "tags": {"hedgehog"}},
    "mole": {"label": "mole", "tags": {"mole"}},
}

ELDERS = {
    "owl": "Old Owl by the meadow gate",
    "badger": "Aunt Badger by the meadow gate",
    "tortoise": "Grandpa Tortoise by the meadow gate",
}

RABBIT_NAMES = ["Pip", "Mimi", "Tansy", "Clover"]
OTTER_NAMES = ["Nip", "Moss", "Ripple", "Nell"]
SQUIRREL_NAMES = ["Hazel", "Pico", "Nutmeg", "Rill"]
BEAVER_NAMES = ["Twig", "Paddle", "Bram", "Willow"]
HEDGEHOG_NAMES = ["Bramble", "Dot", "Poppy", "Thimble"]
MOLE_NAMES = ["Milo", "Mina", "Peb", "Tumble"]


def names_for_species(species: str) -> list[str]:
    return {
        "rabbit": RABBIT_NAMES,
        "otter": OTTER_NAMES,
        "squirrel": SQUIRREL_NAMES,
        "beaver": BEAVER_NAMES,
        "hedgehog": HEDGEHOG_NAMES,
        "mole": MOLE_NAMES,
    }[species]


def fix_works(fix: Fix, breakdown: Breakdown) -> bool:
    return breakdown.kind in fix.kinds


def best_fix_for(breakdown: Breakdown) -> int:
    powers = [f.power for f in FIXES.values() if fix_works(f, breakdown)]
    return max(powers) if powers else 0


def teamwork_score(temper: Temper, fix: Fix) -> int:
    return temper.calm + temper.empathy + fix.teamwork


def needed_score(cargo: Cargo, breakdown: Breakdown) -> int:
    return cargo.weight + cargo.fragile + breakdown.severity - 1


def successful_repair(cargo: Cargo, breakdown: Breakdown, fix: Fix, temper: Temper) -> bool:
    if not fix_works(fix, breakdown):
        return False
    return fix.power + teamwork_score(temper, fix) >= needed_score(cargo, breakdown)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for game_id in GAMES:
        for cargo_id, cargo in CARGOS.items():
            for breakdown_id, breakdown in BREAKDOWNS.items():
                if not cargo.uses_wagon:
                    continue
                if best_fix_for(breakdown) <= 0:
                    continue
                combos.append((game_id, cargo_id, breakdown_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    temper = TEMPERS[params.temper]
    cargo = CARGOS[params.cargo]
    breakdown = BREAKDOWNS[params.breakdown]
    fix = FIXES[params.fix]
    return "mended" if successful_repair(cargo, breakdown, fix, temper) else "spilled"


def explain_fix_rejection(fix_id: str, breakdown_id: str) -> str:
    fix = FIXES[fix_id]
    breakdown = BREAKDOWNS[breakdown_id]
    return (
        f"(No story: {fix.label} does not make sense for a {breakdown.label}. "
        f"Choose a fix that can hold a {breakdown.kind} break together.)"
    )


def explain_combo_rejection(cargo: Cargo, breakdown: Breakdown) -> str:
    return (
        f"(No story: no fix in this world can reasonably handle a {breakdown.label} "
        f"while carrying {cargo.label}. Pick a different breakdown or cargo.)"
    )


def predict_repair(world: World, fix: Fix) -> dict:
    sim = world.copy()
    attempt_fix(sim, fix, narrate=False)
    return {
        "safe": sim.get("cargo").meters["safe"] >= THRESHOLD,
        "spilled": sim.get("cargo").meters["spilled"] >= THRESHOLD,
    }


def introduce(world: World, friend1: Entity, friend2: Entity, cargo: Cargo, game: Game) -> None:
    world.say(
        f"In the soft green woods, {friend1.id} the {friend1.type} and {friend2.id} "
        f"the {friend2.type} rolled a little wagon toward the meadow."
    )
    world.say(
        f"In the wagon was {cargo.phrase}, and tucked beside it was {game.gear} for the {game.label} game."
    )
    world.say(game.play_line)


def deuce_moment(world: World, friend1: Entity, friend2: Entity, game: Game, temper: Temper) -> None:
    friend1.memes["joy"] += 1
    friend2.memes["joy"] += 1
    friend1.memes["rivalry"] += 1
    friend2.memes["rivalry"] += 1
    world.facts["score"] = "deuce"
    world.say(game.score_line)
    if temper.boast >= 1:
        world.say(
            f"{friend1.id} grinned. \"I want the next point!\" {friend2.id} grinned too. "
            f"The tied score made each friend feel a little prickly."
        )
    else:
        world.say(
            f"{friend1.id} and {friend2.id} bounced in place, excited for the next turn."
        )


def jolt_break(world: World, breakdown: Breakdown) -> None:
    cart = world.get("cart")
    cart.meters["broken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But at the bend near the fern bank, the wagon hit a root, and {breakdown.text}."
    )
    if breakdown.kind == "joint":
        world.say("The little joint looked small, but it held the whole front of the wagon together.")
    world.say(
        "The wagon tipped, and the cargo trembled."
    )


def react(world: World, friend1: Entity, friend2: Entity, temper: Temper) -> None:
    world.say(temper.line)
    if temper.calm + temper.empathy >= TEAM_MIN:
        friend1.memes["teamwork"] += 1
        friend2.memes["teamwork"] += 1
    else:
        friend1.meters["pulling_alone"] += 1
        friend2.meters["pulling_alone"] += 1
        propagate(world, narrate=False)


def mentor_hint(world: World, elder_name: str, fix: Fix, breakdown: Breakdown) -> None:
    if world.get("cargo").meters["spilled"] >= THRESHOLD:
        return
    if breakdown.kind in fix.kinds:
        world.say(
            f"From farther down the path, {elder_name} called, "
            f"\"Two steady paws are better than four hasty ones. Look at the loose place and work as one.\""
        )


def attempt_fix(world: World, fix: Fix, narrate: bool = True) -> None:
    cart = world.get("cart")
    cargo = world.get("cargo")
    temper = world.facts["temper_cfg"]
    breakdown = world.facts["breakdown_cfg"]
    cargo_cfg = world.facts["cargo_cfg"]
    if successful_repair(cargo_cfg, breakdown, fix, temper):
        cart.meters["repaired"] += 1
        cart.meters["broken"] = 0.0
        if world.get("friend1").meters["pulling_alone"] >= THRESHOLD:
            world.get("friend1").meters["pulling_alone"] = 0.0
            world.get("friend2").meters["pulling_alone"] = 0.0
        propagate(world, narrate=False)
        if narrate:
            world.say(
                f"So they {fix.text}. The wagon steadied under their shared pull."
            )
    else:
        world.get("friend1").meters["pulling_alone"] += 1
        world.get("friend2").meters["pulling_alone"] += 1
        propagate(world, narrate=False)
        if narrate:
            world.say(
                f"They {fix.fail}. The load gave a sad lurch."
            )
            if cargo.meters["spilled"] >= THRESHOLD:
                world.say(
                    "A part of the load slid out into the grass before they could catch it."
                )


def arrival_happy(world: World, friend1: Entity, friend2: Entity, game: Game, cargo: Cargo, elder_name: str) -> None:
    friend1.memes["joy"] += 1
    friend2.memes["joy"] += 1
    friend1.memes["lesson"] += 1
    friend2.memes["lesson"] += 1
    world.say(
        f"When they reached the meadow, {elder_name} smiled to see them arrive side by side."
    )
    world.say(game.finish_line)
    world.say(
        f"Neither friend cared who had the grander turn anymore. {cargo.ending_image}"
    )
    world.say(
        f"From then on, whenever a job felt heavy, {friend1.id} and {friend2.id} remembered that teamwork could carry more than pride."
    )


def arrival_sad(world: World, friend1: Entity, friend2: Entity, game: Game, cargo: Cargo, elder_name: str) -> None:
    friend1.memes["lesson"] += 1
    friend2.memes["lesson"] += 1
    world.say(
        f"They gathered what they could, and by the time they reached the meadow, the game had to wait a little."
    )
    world.say(
        f"{elder_name} did not scold. \"You came at last,\" the elder said, \"and now you know what the path was trying to teach.\""
    )
    world.say(
        f"{friend1.id} and {friend2.id} set the wagon down gently and promised to pull together before the next point, even if the score was deuce again."
    )
    world.say(
        f"The meadow stayed kind and quiet around them, as if giving them room to begin again."
    )


def tell(
    game: Game,
    cargo_cfg: Cargo,
    breakdown: Breakdown,
    fix: Fix,
    temper: Temper,
    friend_one: str,
    species_one: str,
    friend_two: str,
    species_two: str,
    elder: str,
) -> World:
    world = World()
    friend1 = world.add(Entity(id="friend1", kind="character", type=species_one, label=friend_one, role="friend"))
    friend2 = world.add(Entity(id="friend2", kind="character", type=species_two, label=friend_two, role="friend"))
    cart = world.add(Entity(id="cart", kind="thing", type="wagon", label="little wagon"))
    cargo = world.add(Entity(id="cargo", kind="thing", type=cargo_cfg.id, label=cargo_cfg.label))
    world.facts["temper_cfg"] = temper
    world.facts["cargo_cfg"] = cargo_cfg
    world.facts["breakdown_cfg"] = breakdown
    world.facts["fix_cfg"] = fix
    world.facts["game_cfg"] = game
    world.facts["elder_name"] = ELDERS[elder]
    world.facts["friend_one_name"] = friend_one
    world.facts["friend_two_name"] = friend_two

    introduce(world, friend1=Entity(id=friend_one, type=species_one), friend2=Entity(id=friend_two, type=species_two), cargo=cargo_cfg, game=game)
    deuce_moment(world, friend1=friend1, friend2=friend2, game=game, temper=temper)
    world.para()
    jolt_break(world, breakdown=breakdown)
    react(world, friend1=friend1, friend2=friend2, temper=temper)
    mentor_hint(world, elder_name=ELDERS[elder], fix=fix, breakdown=breakdown)
    pred = predict_repair(world, fix)
    world.facts["predicted_safe"] = pred["safe"]
    world.facts["predicted_spilled"] = pred["spilled"]
    attempt_fix(world, fix=fix, narrate=True)
    world.para()
    if world.get("cargo").meters["safe"] >= THRESHOLD:
        arrival_happy(world, friend1=friend1, friend2=friend2, game=game, cargo=cargo_cfg, elder_name=ELDERS[elder])
        outcome = "mended"
    else:
        arrival_sad(world, friend1=friend1, friend2=friend2, game=game, cargo=cargo_cfg, elder_name=ELDERS[elder])
        outcome = "spilled"

    world.facts.update(
        friend1=friend1,
        friend2=friend2,
        cart=cart,
        cargo=cargo,
        outcome=outcome,
        teamwork_now=friend1.memes["teamwork"] + friend2.memes["teamwork"],
        score_word="deuce",
        repaired=cart.meters["repaired"] >= THRESHOLD,
        spilled=cargo.meters["spilled"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "deuce": [
        (
            "What does deuce mean in a game?",
            "Deuce means the score is tied and neither side is ahead. It often means the next good turn matters a lot."
        )
    ],
    "joint": [
        (
            "What is a joint on a wagon or cart?",
            "A joint is the place where two parts are fitted together so they can hold or move properly. If the joint comes loose, the whole thing can wobble."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more friends help with the same job and listen to each other. A shared job often becomes easier and safer that way."
        )
    ],
    "repair": [
        (
            "Why does a broken wagon need a brace or a tie?",
            "A broken part needs support so it does not bend the wrong way. A brace or tie helps hold the pieces together until the load is safe."
        )
    ],
    "berries": [
        (
            "Why must berries be carried gently?",
            "Berries are soft, so they can squash and spill easily. Gentle carrying keeps them whole and sweet."
        )
    ],
    "cakes": [
        (
            "Why can seed cakes slide from a wagon?",
            "Seed cakes can slip when a wagon tips or bumps hard. If the cart wobbles, a tray may slide before anyone catches it."
        )
    ],
    "flags": [
        (
            "Why are goal flags useful in a game?",
            "Goal flags help players see where to run or aim. Bright markers make a game easier to follow."
        )
    ],
}
KNOWLEDGE_ORDER = ["deuce", "joint", "teamwork", "repair", "berries", "cakes", "flags"]


def generation_prompts(world: World) -> list[str]:
    game = world.facts["game_cfg"]
    cargo = world.facts["cargo_cfg"]
    breakdown = world.facts["breakdown_cfg"]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that includes the words "joint" and "deuce".',
        f"Tell a woodland story where two animal friends are on their way to a {game.label} game with {cargo.label}, but a {breakdown.label} comes loose and they learn teamwork.",
        f"Write a moral-value story where a tied score makes friends a little proud, then a broken wagon teaches them to work together."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    friend1 = world.facts["friend_one_name"]
    friend2 = world.facts["friend_two_name"]
    game = world.facts["game_cfg"]
    cargo_cfg = world.facts["cargo_cfg"]
    breakdown = world.facts["breakdown_cfg"]
    fix = world.facts["fix_cfg"]
    elder_name = world.facts["elder_name"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {friend1} and {friend2}, two young animal friends taking a little wagon to the meadow. They are carrying {cargo_cfg.phrase} and thinking about their game."
        ),
        (
            "What happened when the score reached deuce?",
            f"When the score reached deuce, the game was tied and the next point suddenly felt very important. That made the friends excited, and in some stories it also made them a little proud and hasty."
        ),
        (
            f"What went wrong with the wagon?",
            f"The wagon hit a root, and {breakdown.text}. That mattered because the loose part made the cargo unsafe right away."
        ),
    ]
    if outcome == "mended":
        qa.append(
            (
                f"How did {friend1} and {friend2} solve the problem?",
                f"They fixed the wagon with {fix.label} and worked in the same rhythm instead of pulling against each other. {fix.qa_text}, so the cargo stopped wobbling and could reach the meadow safely."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "The story teaches that teamwork is better than trying to shine alone. When the friends shared the work and listened to each other, they protected the cargo and enjoyed the game more."
            )
        )
        qa.append(
            (
                f"Who helped them remember what to do?",
                f"{elder_name} called to them from near the meadow gate. The elder did not do the repair for them, but the calm reminder helped them notice the right way to work together."
            )
        )
    else:
        qa.append(
            (
                f"Why did the cargo spill?",
                f"The friends were too busy hurrying and pulling badly to steady the wagon first. Their fix was too weak for the break and the load, so the wobble turned into a spill."
            )
        )
        qa.append(
            (
                "What did they learn even though the middle was sad?",
                "They learned that pride can make a small problem bigger. When they finally stopped blaming and started helping, they understood that teamwork should come before winning the next point."
            )
        )
        qa.append(
            (
                f"Was {elder_name} angry?",
                f"No. The elder was gentle and let the lesson speak for itself. That kindness gave the friends space to promise a better choice next time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cargo = world.facts["cargo_cfg"]
    tags = {"deuce", "joint", "teamwork", "repair"}
    if "berries" in cargo.tags:
        tags.add("berries")
    if "cakes" in cargo.tags:
        tags.add("cakes")
    if "flags" in cargo.tags:
        tags.add("flags")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% reasonableness gate
usable_fix(B, F) :- breakdown(B), fix(F), kind_of(B, K), works_on(F, K).
possible_story(G, C, B) :- game(G), cargo(C), breakdown(B), uses_wagon(C), usable_fix(B, _).

% outcome model
teamwork_score(Tm, F, S) :- temper(Tm), fix(F), calm(Tm, C), empathy(Tm, E), teamwork(F, T), S = C + E + T.
needed(C, B, N) :- cargo(C), breakdown(B), weight(C, W), fragile(C, Fr), severity(B, Sv), N = W + Fr + Sv - 1.
success(C, B, F, Tm) :- usable_fix(B, F), power(F, P), teamwork_score(Tm, F, S), needed(C, B, N), P + S >= N.
outcome(mended) :- chosen_cargo(C), chosen_breakdown(B), chosen_fix(F), chosen_temper(Tm), success(C, B, F, Tm).
outcome(spilled) :- chosen_cargo(C), chosen_breakdown(B), chosen_fix(F), chosen_temper(Tm), not success(C, B, F, Tm).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid in GAMES:
        lines.append(asp.fact("game", gid))
    for cid, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("weight", cid, cargo.weight))
        lines.append(asp.fact("fragile", cid, cargo.fragile))
        if cargo.uses_wagon:
            lines.append(asp.fact("uses_wagon", cid))
    for bid, breakdown in BREAKDOWNS.items():
        lines.append(asp.fact("breakdown", bid))
        lines.append(asp.fact("kind_of", bid, breakdown.kind))
        lines.append(asp.fact("severity", bid, breakdown.severity))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fix.power))
        lines.append(asp.fact("teamwork", fid, fix.teamwork))
        for kind in sorted(fix.kinds):
            lines.append(asp.fact("works_on", fid, kind))
    for tid, temper in TEMPERS.items():
        lines.append(asp.fact("temper", tid))
        lines.append(asp.fact("calm", tid, temper.calm))
        lines.append(asp.fact("empathy", tid, temper.empathy))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show possible_story/3."))
    return sorted(set(asp.atoms(model, "possible_story")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_breakdown", params.breakdown),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_temper", params.temper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        game="acorn_roll",
        cargo="berry_basket",
        breakdown="handle_joint",
        fix="vine_wrap",
        temper="patient",
        friend_one="Pip",
        species_one="rabbit",
        friend_two="Moss",
        species_two="otter",
        elder="owl",
    ),
    StoryParams(
        game="reed_ball",
        cargo="goal_flags",
        breakdown="wheel_peg",
        fix="stick_brace",
        temper="kind",
        friend_one="Hazel",
        species_one="squirrel",
        friend_two="Twig",
        species_two="beaver",
        elder="badger",
    ),
    StoryParams(
        game="pebble_flip",
        cargo="seed_cakes",
        breakdown="axle_crack",
        fix="leaf_band",
        temper="showy",
        friend_one="Bramble",
        species_one="hedgehog",
        friend_two="Milo",
        species_two="mole",
        elder="tortoise",
    ),
    StoryParams(
        game="acorn_roll",
        cargo="seed_cakes",
        breakdown="axle_crack",
        fix="stick_brace",
        temper="patient",
        friend_one="Willow",
        species_one="beaver",
        friend_two="Nutmeg",
        species_two="squirrel",
        elder="owl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal teamwork story world: a tied score, a loose joint, and a lesson in working together."
    )
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--breakdown", choices=BREAKDOWNS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--temper", choices=TEMPERS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_species_and_name(rng: random.Random, avoid_name: str = "") -> tuple[str, str]:
    species = rng.choice(sorted(SPECIES))
    names = [n for n in names_for_species(species) if n != avoid_name]
    return species, rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.breakdown:
        if not fix_works(FIXES[args.fix], BREAKDOWNS[args.breakdown]):
            raise StoryError(explain_fix_rejection(args.fix, args.breakdown))

    combos = [
        combo for combo in valid_combos()
        if (args.game is None or combo[0] == args.game)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.breakdown is None or combo[2] == args.breakdown)
    ]
    if not combos:
        cargo = CARGOS[args.cargo] if args.cargo else next(iter(CARGOS.values()))
        breakdown = BREAKDOWNS[args.breakdown] if args.breakdown else next(iter(BREAKDOWNS.values()))
        raise StoryError(explain_combo_rejection(cargo, breakdown))

    game_id, cargo_id, breakdown_id = rng.choice(sorted(combos))
    possible_fixes = [
        fix_id for fix_id, fix in FIXES.items()
        if fix_works(fix, BREAKDOWNS[breakdown_id]) and (args.fix is None or fix_id == args.fix)
    ]
    if not possible_fixes:
        raise StoryError(explain_fix_rejection(args.fix, breakdown_id))
    fix_id = rng.choice(sorted(possible_fixes))
    temper_id = args.temper or rng.choice(sorted(TEMPERS))
    elder = args.elder or rng.choice(sorted(ELDERS))
    species_one, friend_one = _pick_species_and_name(rng)
    species_two, friend_two = _pick_species_and_name(rng, avoid_name=friend_one)
    return StoryParams(
        game=game_id,
        cargo=cargo_id,
        breakdown=breakdown_id,
        fix=fix_id,
        temper=temper_id,
        friend_one=friend_one,
        species_one=species_one,
        friend_two=friend_two,
        species_two=species_two,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.game not in GAMES:
        raise StoryError(f"(Unknown game: {params.game})")
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.breakdown not in BREAKDOWNS:
        raise StoryError(f"(Unknown breakdown: {params.breakdown})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.temper not in TEMPERS:
        raise StoryError(f"(Unknown temper: {params.temper})")
    if params.elder not in ELDERS:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if not fix_works(FIXES[params.fix], BREAKDOWNS[params.breakdown]):
        raise StoryError(explain_fix_rejection(params.fix, params.breakdown))

    world = tell(
        game=GAMES[params.game],
        cargo_cfg=CARGOS[params.cargo],
        breakdown=BREAKDOWNS[params.breakdown],
        fix=FIXES[params.fix],
        temper=TEMPERS[params.temper],
        friend_one=params.friend_one,
        species_one=params.species_one,
        friend_two=params.friend_two,
        species_two=params.species_two,
        elder=params.elder,
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

    parser = build_parser()
    scenarios = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        scenarios.append(params)

    mismatches = []
    for params in scenarios:
        py = outcome_of(params)
        asp_res = asp_outcome(params)
        if py != asp_res:
            mismatches.append((params, py, asp_res))
    if not mismatches:
        print(f"OK: outcome model matches on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py, asp_res in mismatches[:5]:
            print(" ", params, py, asp_res)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show possible_story/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (game, cargo, breakdown) combos:\n")
        for game_id, cargo_id, breakdown_id in combos:
            print(f"  {game_id:12} {cargo_id:12} {breakdown_id}")
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
            header = f"### {p.friend_one} and {p.friend_two}: {p.breakdown} with {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
