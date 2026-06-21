#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py
==========================================================================================

A standalone story world for a tall-tale parking-lot quest about a magical
shortcut, an exclusive destination, and a bureaucratic problem that has to be
solved the sensible way.

Reference seed:
---------------
Write a story that includes the following words and narrative instruments.
Words: trapdoor, bureaucratic, exclusive
Setting: parking lot
Features: Problem Solving, Magic, Quest
Style: Tall Tale

Run it
------
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py --quest comet_pass
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py --helper stamp_giant
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py --trace
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py --json
    python storyworlds/worlds/gpt-5.4/trapdoor_bureaucratic_exclusive_parking_lot_problem_solving.py --verify
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
CALM_TRAITS = {"careful", "patient", "methodical"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Quest:
    id: str
    cargo: str
    cargo_short: str
    destination: str
    ending_image: str
    required_mark: str
    prompt_word: str
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
class Obstacle:
    id: str
    label: str
    phrase: str
    boast: str
    need: str
    solve_result: str
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
class Helper:
    id: str
    label: str
    title: str
    booth: str
    gives_mark: str
    solves: set[str]
    stamp_text: str
    solve_text: str
    flourish: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "looped": False,
            "route": "direct",
            "opened": False,
            "delivered": False,
        }

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


def _r_trapdoor_loop(world: World) -> list[str]:
    hero = world.get("hero")
    pass_ent = world.get("pass")
    if hero.meters["used_trapdoor"] < THRESHOLD or pass_ent.meters["marked"] >= THRESHOLD:
        return []
    sig = ("loop", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["back_at_start"] += 1
    hero.memes["frustration"] += 1
    hero.memes["awe"] += 1
    world.facts["looped"] = True
    world.facts["route"] = "looped"
    return ["__loop__"]


def _r_open_row(world: World) -> list[str]:
    pass_ent = world.get("pass")
    obstacle = world.get("obstacle")
    row = world.get("row")
    if pass_ent.meters["marked"] < THRESHOLD or obstacle.meters["cleared"] < THRESHOLD:
        return []
    sig = ("open_row", row.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    row.meters["open"] += 1
    row.memes["welcome"] += 1
    world.facts["opened"] = True
    return ["__open__"]


def _r_delivery_joy(world: World) -> list[str]:
    row = world.get("row")
    pass_ent = world.get("pass")
    hero = world.get("hero")
    if row.meters["open"] < THRESHOLD or pass_ent.meters["delivered"] < THRESHOLD:
        return []
    sig = ("delivered", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] += 1
    hero.memes["confidence"] += 1
    world.facts["delivered"] = True
    return ["__delivered__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="trapdoor_loop", tag="physical", apply=_r_trapdoor_loop),
    Rule(name="open_row", tag="physical", apply=_r_open_row),
    Rule(name="delivery_joy", tag="emotional", apply=_r_delivery_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


QUESTS = {
    "comet_pass": Quest(
        id="comet_pass",
        cargo="a silver comet pass folded like a tiny lightning bolt",
        cargo_short="comet pass",
        destination="the exclusive silver space for the Moon Parade",
        ending_image="The silver parking space flashed so bright that every hubcap in the lot winked back.",
        required_mark="star",
        prompt_word="comet",
        tags={"quest", "exclusive", "stamp"},
    ),
    "spiral_permit": Quest(
        id="spiral_permit",
        cargo="a blue spiral permit that hummed in a coat pocket",
        cargo_short="spiral permit",
        destination="the exclusive blue space beside the singing pay station",
        ending_image="The blue parking space began to hum a tune that made the loose shopping carts dance in a ring.",
        required_mark="spiral",
        prompt_word="permit",
        tags={"quest", "exclusive", "stamp"},
    ),
    "bell_badge": Quest(
        id="bell_badge",
        cargo="a brass bell badge warm as toast from the sun",
        cargo_short="bell badge",
        destination="the exclusive gold space under the fluttering welcome flag",
        ending_image="The gold parking space rang once, and all the painted lines stood up straight like proud soldiers.",
        required_mark="bell",
        prompt_word="badge",
        tags={"quest", "exclusive", "stamp"},
    ),
}

OBSTACLES = {
    "cone_hill": Obstacle(
        id="cone_hill",
        label="cone hill",
        phrase="a hill of orange traffic cones stacked nearly to the clouds",
        boast="The cones were piled so high that even the wind had to walk around them.",
        need="lift",
        solve_result="the lane lay clear and shining all the way to the far end of the lot",
        tags={"cones", "parking_lot"},
    ),
    "chain_gate": Obstacle(
        id="chain_gate",
        label="chain gate",
        phrase="a chain gate looped across the lane like a giant's jump rope",
        boast="The chain links were so fat and shiny they looked as if they had been polished by moonbeams.",
        need="key",
        solve_result="the gate swung wide with a polite clink and the striped lane yawned open",
        tags={"gate", "parking_lot"},
    ),
    "arrow_maze": Obstacle(
        id="arrow_maze",
        label="arrow maze",
        phrase="a maze of painted arrows that twirled every time someone blinked",
        boast="Those arrows spun so fast they could have confused a flock of geese.",
        need="guide",
        solve_result="the arrows snapped into one straight line, pointing true as a finger",
        tags={"arrows", "parking_lot"},
    ),
}

HELPERS = {
    "stamp_giant": Helper(
        id="stamp_giant",
        label="Stamp Giant",
        title="the Stamp Giant",
        booth="the tallest little booth in the county",
        gives_mark="star",
        solves={"lift"},
        stamp_text="pressed a star stamp on the pass with a thumb broad as a pancake pan",
        solve_text="lifted the cone hill aside as if it were only a basket of carrots",
        flourish="Even the parking meters stood on tiptoe to watch.",
        tags={"stamp", "giant", "magic"},
    ),
    "ribbon_clerk": Helper(
        id="ribbon_clerk",
        label="Ribbon Clerk",
        title="the Ribbon Clerk",
        booth="the neatest and most bureaucratic booth in the whole parking lot",
        gives_mark="spiral",
        solves={"key"},
        stamp_text="curled a blue spiral stamp onto the permit with one brisk tap",
        solve_text="clicked a ribbon key into the chain gate and opened it with a tidy sweep",
        flourish="The key made such a prim little sound that even the pigeons stopped cooing to listen.",
        tags={"stamp", "clerk", "magic"},
    ),
    "whistle_wizard": Helper(
        id="whistle_wizard",
        label="Whistle Wizard",
        title="the Whistle Wizard",
        booth="a booth no bigger than a mailbox and twice as magical",
        gives_mark="bell",
        solves={"guide"},
        stamp_text="tapped a bell mark onto the badge until it gave one bright ding",
        solve_text="blew a silver whistle that lined the wild arrows up nose to tail",
        flourish="For a moment, every painted stripe in the lot held still out of pure respect.",
        tags={"stamp", "wizard", "magic"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Tessa", "Nora", "June", "Ava", "Zoe", "Willa"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Ben", "Leo", "Jasper", "Eli", "Noah"]
TRAITS = ["careful", "patient", "methodical", "curious", "bold", "hurry-up"]
GUARDIANS = ["mother", "father", "aunt", "uncle"]


def helper_fits(helper: Helper, quest: Quest, obstacle: Obstacle) -> bool:
    return helper.gives_mark == quest.required_mark and obstacle.need in helper.solves


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for quest_id, quest in QUESTS.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for helper_id, helper in HELPERS.items():
                if helper_fits(helper, quest, obstacle):
                    out.append((quest_id, obstacle_id, helper_id))
    return out


@dataclass
class StoryParams:
    quest: str
    obstacle: str
    helper: str
    name: str
    gender: str
    guardian: str
    trait: str
    patience: int = 1
    seed: Optional[int] = None
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


def initial_patience(trait: str, patience: int) -> float:
    bonus = 1 if trait in CALM_TRAITS else 0
    return float(patience + bonus)


def would_try_trapdoor_first(trait: str, patience: int) -> bool:
    return initial_patience(trait, patience) < 1.5


def outcome_of(params: StoryParams) -> str:
    return "looped" if would_try_trapdoor_first(params.trait, params.patience) else "direct"


def explain_combo(quest_id: str, obstacle_id: str, helper_id: str) -> str:
    quest = QUESTS[quest_id]
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    parts = []
    if helper.gives_mark != quest.required_mark:
        parts.append(
            f"{helper.title} makes a {helper.gives_mark} mark, but the {quest.cargo_short} needs a {quest.required_mark} mark"
        )
    if obstacle.need not in helper.solves:
        parts.append(
            f"{helper.title} cannot handle {obstacle.label}; that obstacle needs {obstacle.need}"
        )
    if not parts:
        return "(No story: this combination is already valid.)"
    return "(No story: " + "; and ".join(parts) + ".)"


def introduce(world: World, hero: Entity, guardian: Entity) -> None:
    trait = next((t for t in hero.traits if t), "")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who could make a quest out of nearly anything. "
        f"One afternoon, {hero.pronoun('possessive')} {guardian.label_word} took {hero.pronoun('object')} across the biggest parking lot on earth, "
        f"or at least the biggest one either of them had ever seen."
    )


def set_quest(world: World, hero: Entity, guardian: Entity, quest: Quest) -> None:
    pass_ent = world.get("pass")
    hero.memes["duty"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"In {hero.pronoun('possessive')} pocket rode {quest.cargo}, and it had to be delivered to {quest.destination} before the sun slid behind the grocery sign."
    )
    world.say(
        f'"That pass belongs at the far end," {guardian.label_word} said. "And this lot listens to rules, even when the rules are wearing magic boots."'
    )
    world.facts["cargo_label"] = pass_ent.label


def reveal_problem(world: World, quest: Quest, obstacle: Obstacle) -> None:
    world.say(
        f"But between them and {quest.destination} stood {obstacle.phrase}. {obstacle.boast}"
    )


def tempt_trapdoor(world: World, hero: Entity) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"Then {hero.id} spotted a brass trapdoor set between two cracked parking lines. "
        f'Across it, in curly letters, was written: "Shortcut to the Exclusive Row."'
    )
    world.say(
        f"For one sparkling second, the trapdoor looked quicker than any honest lane."
    )


def predict_shortcut(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim.get("hero").meters["used_trapdoor"] += 1
    propagate(sim, narrate=False)
    return {
        "looped": sim.facts["looped"],
        "frustration": sim.get("hero").memes["frustration"],
    }


def warning(world: World, hero: Entity, guardian: Entity, helper: Helper, quest: Quest) -> None:
    pred = predict_shortcut(world, hero)
    world.facts["predicted_loop"] = pred["looped"]
    world.say(
        f'{guardian.label_word.capitalize()} pointed past the trapdoor to {helper.booth}, where {helper.title} was waiting. '
        f'"That shortcut is sly," {guardian.pronoun()} said. "This is an exclusive lane, and exclusive magic only listens to a proper stamp."'
    )
    if pred["looped"]:
        world.say(
            f'{guardian.pronoun().capitalize()} added, "If we try the trapdoor before the {quest.cargo_short} is marked, it will spit us right back where we started."'
        )


def trapdoor_try(world: World, hero: Entity) -> None:
    hero.meters["used_trapdoor"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} touched the brass ring, popped the trapdoor open, and hopped down anyway, because some lessons in a tall tale like to arrive wearing boots.'
    )
    if world.facts["looped"]:
        world.say(
            f"Down below, the stairs curled around once, twice, and a third time for bragging rights. Then the trapdoor flipped {hero.pronoun('object')} right back onto the same warm patch of asphalt, with only a sprinkle of silver dust to show for it."
        )


def meet_helper(world: World, hero: Entity, helper: Helper) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"So {hero.id} marched to {helper.booth} and met {helper.title}. {helper.flourish}"
    )


def stamp_pass(world: World, helper: Helper) -> None:
    pass_ent = world.get("pass")
    pass_ent.meters["marked"] += 1
    world.facts["mark"] = helper.gives_mark
    world.say(
        f"{helper.title} {helper.stamp_text}. At once the little pass grew warmer and brighter, as if it had remembered its job."
    )


def solve_obstacle(world: World, helper: Helper, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["cleared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.title} {helper.solve_text}, and {obstacle.solve_result}."
    )


def reach_row(world: World, hero: Entity, quest: Quest) -> None:
    row = world.get("row")
    if row.meters["open"] >= THRESHOLD:
        world.say(
            f"Past the last stripe lay {quest.destination}, glowing as if a piece of evening sky had been painted onto the pavement."
        )
    else:
        world.say(
            f"{hero.id} hurried onward, though the far row still looked tight-lipped and mysterious."
        )


def deliver(world: World, hero: Entity, quest: Quest) -> None:
    pass_ent = world.get("pass")
    pass_ent.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} set the {quest.cargo_short} exactly where it belonged. The mark flashed once, the asphalt gave a happy shiver, and the whole exclusive row stopped acting so stern."
    )


def ending(world: World, hero: Entity, guardian: Entity, quest: Quest) -> None:
    hero.memes["relief"] += 1
    world.say(
        quest.ending_image
    )
    if world.facts["route"] == "looped":
        world.say(
            f'"Fast is fine," {guardian.label_word} said, smiling, "but clever is what gets a quest across a magical parking lot."'
        )
    else:
        world.say(
            f'"See?" {guardian.label_word.capitalize()} said. "A calm mind can walk farther than a wild shortcut can jump."'
        )
    world.say(
        f"{hero.id} laughed, tucked the now-quiet trapdoor dust out of {hero.pronoun('possessive')} sleeve, and walked home feeling taller than the light poles."
    )


def tell(
    quest: Quest,
    obstacle: Obstacle,
    helper: Helper,
    *,
    name: str = "Mira",
    gender: str = "girl",
    guardian_type: str = "aunt",
    trait: str = "careful",
    patience: int = 1,
) -> World:
    world = World()

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=gender,
        label=name,
        phrase=name,
        role="hero",
        traits=[trait],
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        label="the grown-up",
        phrase="the grown-up",
        role="guardian",
    ))
    pass_ent = world.add(Entity(
        id="pass",
        kind="thing",
        type="pass",
        label=quest.cargo_short,
        phrase=quest.cargo,
        role="cargo",
        attrs={"required_mark": quest.required_mark},
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        phrase=obstacle.phrase,
        role="obstacle",
        attrs={"need": obstacle.need},
    ))
    row = world.add(Entity(
        id="row",
        kind="thing",
        type="parking_row",
        label="exclusive row",
        phrase=quest.destination,
        role="destination",
    ))
    world.add(Entity(
        id="trapdoor",
        kind="thing",
        type="trapdoor",
        label="trapdoor",
        phrase="a brass trapdoor",
        role="shortcut",
    ))
    world.add(Entity(
        id="helper",
        kind="character",
        type="helper",
        label=helper.label,
        phrase=helper.title,
        role="helper",
        attrs={"mark": helper.gives_mark, "solves": sorted(helper.solves)},
    ))

    hero.attrs["name"] = name
    hero.memes["patience"] = initial_patience(trait, patience)
    hero.memes["wonder"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["frustration"] = 0.0
    hero.memes["joy"] = 0.0

    world.facts.update(
        hero=hero,
        guardian=guardian,
        quest=quest,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        patience=patience,
        trait=trait,
    )

    introduce(world, hero, guardian)
    set_quest(world, hero, guardian, quest)

    world.para()
    reveal_problem(world, quest, obstacle)
    tempt_trapdoor(world, hero)
    warning(world, hero, guardian, helper, quest)

    if would_try_trapdoor_first(trait, patience):
        world.para()
        trapdoor_try(world, hero)

    world.para()
    meet_helper(world, hero, helper)
    stamp_pass(world, helper)
    solve_obstacle(world, helper, obstacle)
    reach_row(world, hero, quest)

    world.para()
    deliver(world, hero, quest)
    ending(world, hero, guardian, quest)

    world.facts.update(
        route=world.facts["route"],
        looped=world.facts["looped"],
        opened=world.facts["opened"],
        delivered=world.facts["delivered"],
        mark=world.facts.get("mark", ""),
    )
    return world


KNOWLEDGE = {
    "trapdoor": [
        (
            "What is a trapdoor?",
            "A trapdoor is a door set flat in the floor or ground that opens downward or upward instead of swinging from the side."
        )
    ],
    "exclusive": [
        (
            "What does exclusive mean?",
            "Exclusive means only certain people or things are allowed in. It is a way of saying not everyone may use that place."
        )
    ],
    "bureaucratic": [
        (
            "What does bureaucratic mean?",
            "Bureaucratic means there are lots of official steps, like forms, stamps, or rules to follow before something can happen."
        )
    ],
    "stamp": [
        (
            "Why do people use stamps on forms or permits?",
            "A stamp shows that an official person checked something and approved it. It helps others know the paper is real."
        )
    ],
    "parking_lot": [
        (
            "What is a parking lot?",
            "A parking lot is a place with marked spaces where cars can stop and stay for a while."
        )
    ],
    "cones": [
        (
            "What are traffic cones for?",
            "Traffic cones help guide people and cars away from places they should not go. Their bright color makes them easy to notice."
        )
    ],
    "gate": [
        (
            "Why would a lane have a gate or chain?",
            "A gate or chain keeps a place closed until the right person opens it. It is a simple way to control where people may go."
        )
    ],
    "arrows": [
        (
            "What do painted arrows on the ground do?",
            "Painted arrows show which way to go. They help people move through a place without getting confused."
        )
    ],
    "magic": [
        (
            "What makes a story magical?",
            "A magical story lets ordinary things do surprising things, like singing, glowing, or moving in impossible ways."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a clear goal. The traveler usually faces a problem and has to solve it before the journey is done."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "trapdoor",
    "exclusive",
    "bureaucratic",
    "stamp",
    "parking_lot",
    "cones",
    "gate",
    "arrows",
    "magic",
    "quest",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    quest = world.facts["quest"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper_cfg"]
    route = world.facts["route"]
    if route == "looped":
        turn = "tries a magical trapdoor shortcut first and gets sent back"
    else:
        turn = "pauses and solves the problem the sensible way"
    return [
        f'Write a tall-tale story for a 3-to-5-year-old set in a parking lot that includes the words "trapdoor," "bureaucratic," and "exclusive."',
        f"Tell a magical quest about a child named {hero.attrs['name']} who must carry a {quest.cargo_short} across a giant parking lot, where {obstacle.label} blocks the way and {helper.title} helps.",
        f"Write a child-facing problem-solving story where the hero {turn}, and the ending proves the quest reached {quest.destination}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    guardian = world.facts["guardian"]
    quest = world.facts["quest"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper_cfg"]
    pw = guardian.label_word
    qa: list[tuple[str, str]] = [
        (
            f"Who is the story about?",
            f"It is about {hero.attrs['name']}, a little {hero.type}, and {hero.pronoun('possessive')} {pw}. Together they crossed a magical parking lot to deliver the {quest.cargo_short}."
        ),
        (
            f"What was the quest?",
            f"The quest was to carry the {quest.cargo_short} to {quest.destination} before the day ended. That goal is what made every choice in the parking lot matter."
        ),
        (
            f"What problem stood in the way?",
            f"{obstacle.phrase.capitalize()} blocked the path. It was not just big-looking; it truly kept them from reaching the far row until someone solved it."
        ),
    ]
    if world.facts["looped"]:
        qa.append(
            (
                f"Why did the trapdoor not help {hero.attrs['name']} at first?",
                f"The trapdoor was a shortcut in name only, because the {quest.cargo_short} had not been stamped yet. Since the lane's magic listened to official rules, the trapdoor sent {hero.attrs['name']} right back to the start."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.attrs['name']} not use the trapdoor first?",
                f"{hero.attrs['name']} listened when {pw} warned that the shortcut would not work without the proper mark. That patience saved time, because the quest needed the right stamp before the magic lane would cooperate."
            )
        )
    qa.append(
        (
            f"How did {helper.title} solve the problem?",
            f"{helper.title} stamped the {quest.cargo_short} with the correct mark and then handled {obstacle.label}. The stamp satisfied the bureaucratic magic, and the obstacle was cleared so the row could open."
        )
    )
    qa.append(
        (
            f"How did the story end?",
            f"{hero.attrs['name']} delivered the {quest.cargo_short} to {quest.destination}, and the far parking space lit up in a magical way. The ending shows the quest was truly finished because the whole lot changed once the pass reached its place."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    quest = world.facts["quest"]
    obstacle = world.facts["obstacle_cfg"]
    tags = {"trapdoor", "exclusive", "bureaucratic", "stamp", "parking_lot", "magic", "quest"}
    tags |= set(quest.tags)
    tags |= set(obstacle.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
compatible(Q, O, H) :- quest(Q), obstacle(O), helper(H),
                       requires_mark(Q, M), gives_mark(H, M),
                       needs(O, N), solves(H, N).

% --- route / outcome model -------------------------------------------------
calm(T) :- trait_name(T), calm_trait(T).
patient_enough :- patience(P), P >= 1.
patient_enough :- chosen_trait(T), calm(T).

tries_trapdoor_first :- not patient_enough.

outcome(looped) :- tries_trapdoor_first.
outcome(direct) :- not tries_trapdoor_first.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        lines.append(asp.fact("requires_mark", quest_id, quest.required_mark))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("gives_mark", helper_id, helper.gives_mark))
        for need in sorted(helper.solves):
            lines.append(asp.fact("solves", helper_id, need))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("patience", params.patience),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        quest="comet_pass",
        obstacle="cone_hill",
        helper="stamp_giant",
        name="Mira",
        gender="girl",
        guardian="aunt",
        trait="careful",
        patience=1,
    ),
    StoryParams(
        quest="spiral_permit",
        obstacle="chain_gate",
        helper="ribbon_clerk",
        name="Finn",
        gender="boy",
        guardian="father",
        trait="hurry-up",
        patience=0,
    ),
    StoryParams(
        quest="bell_badge",
        obstacle="arrow_maze",
        helper="whistle_wizard",
        name="Tessa",
        gender="girl",
        guardian="mother",
        trait="curious",
        patience=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale parking-lot quest storyworld. Unspecified choices are picked at random from valid combinations."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--patience", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest is not None and args.obstacle is not None and args.helper is not None:
        if not helper_fits(HELPERS[args.helper], QUESTS[args.quest], OBSTACLES[args.obstacle]):
            raise StoryError(explain_combo(args.quest, args.obstacle, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        if args.quest and args.obstacle and args.helper:
            raise StoryError(explain_combo(args.quest, args.obstacle, args.helper))
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(GUARDIANS)
    trait = rng.choice(TRAITS)
    patience = args.patience if args.patience is not None else rng.choice([0, 1, 2])

    return StoryParams(
        quest=quest_id,
        obstacle=obstacle_id,
        helper=helper_id,
        name=name,
        gender=gender,
        guardian=guardian,
        trait=trait,
        patience=patience,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.guardian not in set(GUARDIANS):
        raise StoryError(f"(Unknown guardian: {params.guardian})")
    if params.patience not in {0, 1, 2}:
        raise StoryError(f"(Patience must be 0, 1, or 2; got {params.patience})")

    quest = QUESTS[params.quest]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    if not helper_fits(helper, quest, obstacle):
        raise StoryError(explain_combo(params.quest, params.obstacle, params.helper))

    world = tell(
        quest=quest,
        obstacle=obstacle,
        helper=helper,
        name=params.name,
        gender=params.gender,
        guardian_type=params.guardian,
        trait=params.trait,
        patience=params.patience,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: compatibility gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

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
        smoke_params = resolve_params(parser.parse_args([]), random.Random(777))
        smoke_params.seed = 777
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        with redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, obstacle, helper) combos:\n")
        for quest_id, obstacle_id, helper_id in combos:
            print(f"  {quest_id:14} {obstacle_id:12} {helper_id}")
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
            header = f"### {p.name}: {p.quest} / {p.obstacle} / {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
