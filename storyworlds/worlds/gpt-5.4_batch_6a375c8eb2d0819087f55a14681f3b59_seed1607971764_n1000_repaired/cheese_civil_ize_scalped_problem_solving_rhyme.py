#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cheese_civil_ize_scalped_problem_solving_rhyme.py
============================================================================

A gentle ghost-story world about a child, a worried pantry ghost, and a piece
of cheese that has been nibbled or fought over by mice. The child studies the
clues, says they must "civil-ize" the pantry, and solves the problem with a
small practical plan wrapped in a rhyme.

The domain is narrow on purpose: only combinations where the chosen plan
actually matches the pantry problem are allowed. The world model tracks a few
physical meters (noise, nibbled cheese, crumbs, cover) and emotional memes
(fear, worry, calm, pride, manners), then renders a complete story from the
state change.

Run it
------
    python storyworlds/worlds/gpt-5.4/cheese_civil_ize_scalped_problem_solving_rhyme.py
    python storyworlds/worlds/gpt-5.4/cheese_civil_ize_scalped_problem_solving_rhyme.py --nuisance raid
    python storyworlds/worlds/gpt-5.4/cheese_civil_ize_scalped_problem_solving_rhyme.py --solution cloche
    python storyworlds/worlds/gpt-5.4/cheese_civil_ize_scalped_problem_solving_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/cheese_civil_ize_scalped_problem_solving_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/cheese_civil_ize_scalped_problem_solving_rhyme.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class GhostKind:
    id: str
    title: str
    hint: str
    opening: str
    wish: str
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
class CheeseKind:
    id: str
    label: str
    phrase: str
    moonline: str
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
class Nuisance:
    id: str
    clue: str
    whisper: str
    needs: set[str]
    severity: int
    damage_word: str
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
class Solution:
    id: str
    label: str
    fixes: set[str]
    sense: int
    power: int
    setup: str
    action: str
    rhyme: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_mouse_trouble(world: World) -> list[str]:
    out: list[str] = []
    mice = world.get("mice")
    cheese = world.get("cheese")
    ghost = world.get("ghost")
    room = world.get("pantry")
    needs = set(world.facts.get("needs", set()))
    severity = int(world.facts.get("severity", 0))
    if severity <= 0:
        return out
    if cheese.meters["covered"] < THRESHOLD and "protect" in needs:
        sig = ("trouble", "protect")
        if sig not in world.fired:
            world.fired.add(sig)
            cheese.meters["nibbled"] += 1
            room.meters["noise"] += 1
            ghost.memes["worry"] += 1
            mice.memes["hunger"] += 1
            out.append("__trouble__")
    if "share" in needs:
        sig = ("trouble", "share")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["noise"] += 1
            ghost.memes["worry"] += 1
            mice.memes["grabby"] += 1
            out.append("__trouble__")
    if "manners" in needs:
        sig = ("trouble", "manners")
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.memes["worry"] += 1
            mice.memes["uncivil"] += 1
            out.append("__trouble__")
    return out


def _r_child_alarm(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("pantry")
    ghost = world.get("ghost")
    if room.meters["noise"] >= THRESHOLD and ghost.memes["worry"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            return ["__alarm__"]
    return []


def _r_peace(world: World) -> list[str]:
    mice = world.get("mice")
    ghost = world.get("ghost")
    room = world.get("pantry")
    cheese = world.get("cheese")
    solution = world.facts.get("solution_cfg")
    if solution is None:
        return []
    fixes = set(world.facts.get("fixes", set()))
    needs = set(world.facts.get("needs", set()))
    if not needs.issubset(fixes):
        return []
    if int(solution.power) < int(world.facts.get("severity", 0)):
        return []
    sig = ("peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if "protect" in fixes:
        cheese.meters["covered"] = 1.0
    if "share" in fixes:
        mice.meters["crumbs"] += 1
        mice.memes["hunger"] = 0.0
        mice.memes["grabby"] = 0.0
    if "manners" in fixes:
        mice.memes["uncivil"] = 0.0
        mice.memes["manners"] += 1
    room.meters["noise"] = 0.0
    ghost.memes["worry"] = 0.0
    ghost.memes["calm"] += 1
    ghost.memes["gratitude"] += 1
    world.get("child").memes["fear"] = 0.0
    world.get("child").memes["pride"] += 1
    return ["__peace__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="mouse_trouble", tag="physical", apply=_r_mouse_trouble),
    Rule(name="child_alarm", tag="emotional", apply=_r_child_alarm),
    Rule(name="peace", tag="resolution", apply=_r_peace),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def valid_combo(nuisance: Nuisance, solution: Solution) -> bool:
    return (
        solution.sense >= SENSE_MIN
        and nuisance.needs.issubset(solution.fixes)
        and solution.power >= nuisance.severity
    )


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for nid, nuisance in NUISANCES.items():
        for sid, solution in SOLUTIONS.items():
            if valid_combo(nuisance, solution):
                combos.append((nid, sid))
    return combos


def explain_rejection(nuisance: Nuisance, solution: Solution) -> str:
    if solution.sense < SENSE_MIN:
        return (
            f"(No story: {solution.label} sounds too flimsy for a careful solution. "
            f"Pick a sturdier plan that would really help in a haunted pantry.)"
        )
    missing = sorted(nuisance.needs - solution.fixes)
    if missing:
        return (
            f"(No story: {solution.label} does not solve the whole pantry problem. "
            f"It still misses {', '.join(missing)}, so the ghost would stay worried.)"
        )
    if solution.power < nuisance.severity:
        return (
            f"(No story: {solution.label} is too small for this much mouse trouble. "
            f"The plan needs more power for a severity {nuisance.severity} nuisance.)"
        )
    return "(No story: this plan does not fit this pantry problem.)"


def predict_unrest(world: World, nuisance: Nuisance, solution: Solution) -> dict:
    sim = world.copy()
    sim.facts["needs"] = set(nuisance.needs)
    sim.facts["severity"] = nuisance.severity
    sim.facts["fixes"] = set()
    sim.facts["solution_cfg"] = None
    propagate(sim, narrate=False)
    troubled = sim.get("pantry").meters["noise"] >= THRESHOLD or sim.get("ghost").memes["worry"] >= THRESHOLD

    sim2 = world.copy()
    sim2.facts["needs"] = set(nuisance.needs)
    sim2.facts["severity"] = nuisance.severity
    sim2.facts["fixes"] = set(solution.fixes)
    sim2.facts["solution_cfg"] = solution
    propagate(sim2, narrate=False)
    peaceful = sim2.get("ghost").memes["calm"] >= THRESHOLD and sim2.get("pantry").meters["noise"] < THRESHOLD
    return {"troubled": troubled, "peaceful": peaceful}


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, elder: Entity) -> None:
    trait = child.traits[0] if child.traits else "thoughtful"
    world.say(
        f"Late one silver night, {child.id} padded through the old kitchen with "
        f"{child.pronoun('possessive')} {elder.label_word}. {child.pronoun().capitalize()} "
        f"was a {trait} little {child.type} who listened even when a house sounded almost asleep."
    )


def pantry_glimmer(world: World, cheese: CheeseKind) -> None:
    world.say(
        f"From the pantry door came a pale blue glow and a whispery clink. "
        f"On the middle shelf sat {cheese.phrase}, {cheese.moonline}."
    )


def reveal_trouble(world: World, ghost: Entity, nuisance: Nuisance, cheese: CheeseKind) -> None:
    world.say(
        f"But the moonlit quiet had gone crooked. {nuisance.clue} {nuisance.whisper}"
    )
    if world.get("cheese").meters["nibbled"] >= THRESHOLD:
        world.say(
            f"One side of the {cheese.label} looked sadly scalped, as if tiny teeth "
            f"had shaved away its neat round edge."
        )
    world.say(
        f"Then {ghost.attrs['title']} floated out from behind the flour tin. "
        f'"Oh dear," {ghost.pronoun()} sighed. "{ghost.attrs["opening"]}"'
    )


def ghost_request(world: World, ghost: Entity) -> None:
    world.say(
        f'"I do not wish to frighten anyone," {ghost.pronoun()} said, '
        f'"but I would like to civil-ize this pantry before dawn."'
    )
    world.say(f'"{ghost.attrs["wish"]}"')


def inspect_clues(world: World, child: Entity, nuisance: Nuisance, solution: Solution) -> None:
    pred = predict_unrest(world, nuisance, solution)
    world.facts["predicted_troubled"] = pred["troubled"]
    world.facts["predicted_peaceful"] = pred["peaceful"]
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} looked at the shelf, the crumbs, and the scurrying shadows. "
        f"{child.pronoun().capitalize()} did not run away. Instead, {child.pronoun()} "
        f"counted the clues and thought about what would calm everything down."
    )


def choose_plan(world: World, child: Entity, solution: Solution) -> None:
    world.say(
        f'"I know," whispered {child.id}. "We can try {solution.label}. '
        f'It will help the mice and guard the cheese too."'
    )
    world.say(solution.setup)


def apply_solution(world: World, child: Entity, solution: Solution) -> None:
    world.facts["fixes"] = set(solution.fixes)
    world.facts["solution_cfg"] = solution
    world.say(solution.action)
    world.say(f'Then {child.id} said in a soft rhyme, "{solution.rhyme}"')
    propagate(world, narrate=False)


def settle(world: World, child: Entity, ghost: Entity, elder: Entity, cheese: CheeseKind) -> None:
    mice = world.get("mice")
    if mice.meters["crumbs"] >= THRESHOLD:
        world.say("Tiny paws turned toward the little crumbs instead of the big wheel on the shelf.")
    if mice.memes["manners"] >= THRESHOLD:
        world.say("The quarrelsome squeaks softened into neat little waiting noises.")
    world.say(
        f"The pantry listened. The rattling stopped. The blue glow around {ghost.attrs['title']} "
        f"grew warm instead of worried."
    )
    world.say(
        f'"You solved it kindly," {ghost.pronoun()} said. "You did not only save the '
        f'{cheese.label}; you taught the room better manners."'
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled from the doorway and tucked the blanket "
        f"more snugly around {child.id}'s shoulders."
    )
    world.say(
        f"When morning came, the {cheese.label} was safe, the shelf was tidy, and even the pantry "
        f"felt less haunted and more like a place where everyone knew how to share the dark."
    )


# ---------------------------------------------------------------------------
# Main screenplay
# ---------------------------------------------------------------------------
def tell(
    ghost_cfg: GhostKind,
    cheese_cfg: CheeseKind,
    nuisance_cfg: Nuisance,
    solution_cfg: Solution,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "thoughtful",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        attrs={},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        role="ghost",
        label=ghost_cfg.title,
        attrs={"title": ghost_cfg.title, "opening": ghost_cfg.opening, "wish": ghost_cfg.wish},
    ))
    mice = world.add(Entity(
        id="mice",
        kind="character",
        type="mice",
        role="mice",
        label="the mice",
        attrs={},
    ))
    pantry = world.add(Entity(
        id="pantry",
        type="room",
        label="the pantry",
        attrs={},
    ))
    cheese = world.add(Entity(
        id="cheese",
        type="food",
        label=cheese_cfg.label,
        attrs={},
    ))

    # Initialize every meter and meme that rules read.
    pantry.meters["noise"] = 0.0
    cheese.meters["covered"] = 0.0
    cheese.meters["nibbled"] = 0.0
    mice.meters["crumbs"] = 0.0
    ghost.memes["worry"] = 0.0
    ghost.memes["calm"] = 0.0
    ghost.memes["gratitude"] = 0.0
    mice.memes["hunger"] = 0.0
    mice.memes["grabby"] = 0.0
    mice.memes["uncivil"] = 0.0
    mice.memes["manners"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["pride"] = 0.0
    child.memes["curiosity"] = 0.0

    world.facts["ghost_cfg"] = ghost_cfg
    world.facts["cheese_cfg"] = cheese_cfg
    world.facts["nuisance_cfg"] = nuisance_cfg
    world.facts["solution_cfg"] = None
    world.facts["needs"] = set(nuisance_cfg.needs)
    world.facts["severity"] = nuisance_cfg.severity
    world.facts["fixes"] = set()
    world.facts["outcome"] = "troubled"

    introduce(world, child, elder)
    pantry_glimmer(world, cheese_cfg)

    world.para()
    propagate(world, narrate=False)
    reveal_trouble(world, ghost, nuisance_cfg, cheese_cfg)
    ghost_request(world, ghost)

    world.para()
    inspect_clues(world, child, nuisance_cfg, solution_cfg)
    choose_plan(world, child, solution_cfg)
    apply_solution(world, child, solution_cfg)

    world.para()
    if ghost.memes["calm"] >= THRESHOLD:
        settle(world, child, ghost, elder, cheese_cfg)
        outcome = "peaceful"
    else:
        world.say(
            "The pantry quieted a little, but not enough. The ghost still hovered by the shelf, "
            "and the mice still looked ready to rush the cheese."
        )
        world.say(
            f"{child.id} knew the plan had not solved the whole problem yet, so {child.pronoun()} "
            f"promised to come back with a better idea before the next midnight."
        )
        outcome = "restless"

    world.facts.update(
        child=child,
        elder=elder,
        ghost=ghost,
        mice=mice,
        pantry=pantry,
        cheese=cheese,
        outcome=outcome,
        solved=outcome == "peaceful",
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
GHOSTS = {
    "cook": GhostKind(
        id="cook",
        title="the Pantry Cook Ghost",
        hint="smelled faintly of nutmeg and candle smoke",
        opening="The shelves cannot sleep when everyone is squeaking and snatching",
        wish="Please help me keep the midnight kitchen gentle.",
        tags={"ghost", "kitchen"},
    ),
    "housekeeper": GhostKind(
        id="housekeeper",
        title="the Cupboard Housekeeper Ghost",
        hint="wore a blue apron of mist",
        opening="I keep things neat, yet tonight the pantry sounds like a tin storm",
        wish="I only want the night to feel orderly again.",
        tags={"ghost", "tidy"},
    ),
    "cheesemonger": GhostKind(
        id="cheesemonger",
        title="the Old Cheese-Seller Ghost",
        hint="carried a silver scale made of moonlight",
        opening="A good cheese deserves peace, not midnight grabbing",
        wish="Help me keep my shelf fair and calm.",
        tags={"ghost", "cheese"},
    ),
}

CHEESES = {
    "cheddar": CheeseKind(
        id="cheddar",
        label="cheddar wheel",
        phrase="a round cheddar wheel",
        moonline="its orange rind shining like a little moon",
        tags={"cheese"},
    ),
    "goat": CheeseKind(
        id="goat",
        label="goat-cheese round",
        phrase="a white goat-cheese round",
        moonline="its pale edge glowing like a pearl in the dark",
        tags={"cheese"},
    ),
    "blue": CheeseKind(
        id="blue",
        label="blue cheese",
        phrase="a wedge of blue cheese",
        moonline="its silver wrapper winking under the moon",
        tags={"cheese"},
    ),
}

NUISANCES = {
    "nibble": Nuisance(
        id="nibble",
        clue="Fresh crumbs lay under the shelf, and one mouse kept springing up for secret bites.",
        whisper="A lonely little gnaw-gnaw sound came from the corner.",
        needs={"protect"},
        severity=1,
        damage_word="nibbled",
        tags={"mice", "protect"},
    ),
    "squabble": Nuisance(
        id="squabble",
        clue="Two mice were arguing over the same crumb and bumping a spoon against a jar.",
        whisper="Their squeaks rose and fell like tiny angry violins.",
        needs={"share", "manners"},
        severity=2,
        damage_word="scratched",
        tags={"mice", "share", "manners"},
    ),
    "raid": Nuisance(
        id="raid",
        clue="A whole mouse parade had found the shelf, with noses up, paws grabbing, and tails thumping tins.",
        whisper="The pantry sounded full of greedy little feet.",
        needs={"protect", "share", "manners"},
        severity=3,
        damage_word="raided",
        tags={"mice", "protect", "share", "manners"},
    ),
}

SOLUTIONS = {
    "cloche": Solution(
        id="cloche",
        label="a glass cloche and a saucer of rind bits",
        fixes={"protect"},
        sense=3,
        power=1,
        setup="Very carefully, the child set a clear glass cover over the cheese wheel.",
        action="Next to the shelf, the child placed a tiny saucer with just a few safe rind bits for sniffing.",
        rhyme="Little feet, no need to race; this big cheese keeps its sleeping place.",
        qa_text="covered the cheese with a glass cloche so the mice could not nibble it",
        tags={"cover", "cheese"},
    ),
    "crumb_song": Solution(
        id="crumb_song",
        label="a crumb bowl and a manners rhyme",
        fixes={"share", "manners"},
        sense=3,
        power=2,
        setup="The child fetched a small bowl, sprinkled crumbs into it, and set it on the floor where every mouse could reach in turn.",
        action="Then the child tapped the side of the bowl so the mice would look at the fair little supper below.",
        rhyme="Crumb by crumb and squeak by squeak, wait your turn and softly speak.",
        qa_text="set out a fair crumb bowl and used a rhyme to stop the mice from fighting",
        tags={"crumbs", "rhyme", "manners"},
    ),
    "midnight_table": Solution(
        id="midnight_table",
        label="a covered shelf, a crumb bowl, and a civil rhyme",
        fixes={"protect", "share", "manners"},
        sense=3,
        power=3,
        setup="The child covered the good cheese on the shelf, then made a tiny crumb table on the floor from a saucer and a folded napkin.",
        action="With one hand on the shelf and one hand by the saucer, the child showed the mice exactly where to gather and where not to climb.",
        rhyme="Cheese on high, crumbs below; gentle paws in a tidy row.",
        qa_text="protected the cheese and gave the mice a fair crumb table with a rhyme to teach order",
        tags={"cover", "crumbs", "rhyme", "manners"},
    ),
    "shoo": Solution(
        id="shoo",
        label="waving a towel and saying shoo",
        fixes={"protect"},
        sense=1,
        power=1,
        setup="The child grabbed a towel and flapped it in the air.",
        action="The mice jumped back for a moment, but the shelf still smelled tempting.",
        rhyme="Shoo, shoo, run from view.",
        qa_text="only waved the mice away for a moment",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Nora", "Mina", "Lucy", "Ada", "Ivy", "Rose", "Lila", "June"]
BOY_NAMES = ["Theo", "Eli", "Sam", "Noah", "Finn", "Ben", "Milo", "Leo"]
TRAITS = ["thoughtful", "steady", "brave", "gentle", "patient", "clever"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    ghost: str
    cheese: str
    nuisance: str
    solution: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spooky feeling and something mysterious, like a ghost or a whisper in the dark. In gentle ghost stories, the spooky part is there to make the problem feel strange, not to hurt anyone.",
        )
    ],
    "cheese": [
        (
            "What is cheese?",
            "Cheese is food made from milk. It can come as a wheel, a wedge, or a soft round, and people often keep it wrapped or covered so it stays nice.",
        )
    ],
    "mice": [
        (
            "Why do mice look for crumbs?",
            "Mice have strong noses and look for small bits of food they can carry or nibble. If food is left open, they may come close to sniff it out.",
        )
    ],
    "manners": [
        (
            "What does it mean to have manners?",
            "Having manners means acting in a calm and respectful way, like waiting your turn and not grabbing. Good manners help everyone share space more peacefully.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or pattern of words with matching end sounds, like row and glow. Rhymes are easy to remember, so they can help people learn a rule or a little song.",
        )
    ],
    "cover": [
        (
            "Why cover food?",
            "Covering food helps keep it clean and keeps little animals from nibbling it. A cover also shows clearly that the food is being protected.",
        )
    ],
    "crumbs": [
        (
            "Why does giving everyone a fair share stop fighting?",
            "A fair share makes it easier for everyone to wait and take turns. When there is a clear place for each little bite, there is less grabbing and less noise.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "cheese", "mice", "manners", "rhyme", "cover", "crumbs"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost_cfg = f["ghost_cfg"]
    cheese_cfg = f["cheese_cfg"]
    nuisance_cfg = f["nuisance_cfg"]
    solution_cfg = SOLUTIONS[world.facts["solution_cfg"].id] if world.facts["solution_cfg"] else f.get("solution_cfg")
    if solution_cfg is None:
        solution_cfg = SOLUTIONS["midnight_table"]
    return [
        f'Write a gentle ghost story for a young child where {child.id} finds {cheese_cfg.phrase} in a haunted pantry and must solve a mouse problem with a rhyme. Include the words "cheese", "civil-ize", and "scalped".',
        f"Tell a spooky-but-kind story about {ghost_cfg.title} who worries because the pantry is too noisy at night, and a child calmly works out a fair solution.",
        f"Write a problem-solving story where the clue is {nuisance_cfg.damage_word} cheese and the fix is {solution_cfg.label}, ending with a peaceful pantry at dawn.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    ghost = f["ghost"]
    nuisance = f["nuisance_cfg"]
    solution = SOLUTIONS[f["solution_cfg"].id] if f["solution_cfg"] else SOLUTIONS["midnight_table"]
    cheese_cfg = f["cheese_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who notices a strange problem in the pantry, and {ghost.attrs['title']} who wants the night to be calm again.",
        ),
        (
            "What was wrong in the pantry?",
            f"The pantry was noisy because of mouse trouble, and the problem reached the {cheese_cfg.label}. The ghost was worried because {nuisance.whisper.lower()} and the shelf no longer felt peaceful.",
        ),
        (
            "Why did the story say the cheese looked scalped?",
            f"It meant a little part of the cheese had been shaved away by nibbling, so its round edge looked trimmed off. The word made the cheese sound oddly spooky without meaning anyone had been hurt.",
        ),
        (
            f"How did {child.id} solve the problem?",
            f"{child.id} used problem solving instead of panic. {child.pronoun().capitalize()} {solution.qa_text} and wrapped the plan in a rhyme so the rules were easy for the mice to follow.",
        ),
    ]
    if outcome == "peaceful":
        qa.append(
            (
                "What did the ghost mean by saying the pantry should be civil-ize-d?",
                "The ghost wanted the room to become calmer, fairer, and more orderly. The child's plan turned grabbing and rattling into sharing and waiting, which is what made the pantry feel civilized again.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. {elder.label_word.capitalize()} saw that the {cheese_cfg.label} was protected, the mice had a fairer place to go, and even the ghost felt calm by morning.",
            )
        )
    else:
        qa.append(
            (
                "Did the first plan solve everything?",
                f"No. It helped a little, but the pantry was still restless, so {child.id} knew a better idea was needed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "cheese", "mice"}
    nuisance = world.facts["nuisance_cfg"]
    solution = SOLUTIONS[world.facts["solution_cfg"].id] if world.facts["solution_cfg"] else SOLUTIONS["midnight_table"]
    if "manners" in nuisance.tags or "manners" in solution.tags:
        tags.add("manners")
    if "rhyme" in solution.tags:
        tags.add("rhyme")
    if "cover" in solution.tags:
        tags.add("cover")
    if "crumbs" in solution.tags:
        tags.add("crumbs")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        ghost="cook",
        cheese="cheddar",
        nuisance="nibble",
        solution="cloche",
        child_name="Nora",
        child_gender="girl",
        elder_type="grandmother",
        trait="thoughtful",
    ),
    StoryParams(
        ghost="housekeeper",
        cheese="goat",
        nuisance="squabble",
        solution="crumb_song",
        child_name="Theo",
        child_gender="boy",
        elder_type="grandfather",
        trait="patient",
    ),
    StoryParams(
        ghost="cheesemonger",
        cheese="blue",
        nuisance="raid",
        solution="midnight_table",
        child_name="Lila",
        child_gender="girl",
        elder_type="grandmother",
        trait="clever",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(N, S) :- nuisance(N), solution(S), sense(S, Se), sense_min(M), Se >= M,
               severity(N, Sv), power(S, Pw), Pw >= Sv,
               not missing_need(N, S).

missing_need(N, S) :- needs(N, Need), not fixes(S, Need).

peaceful :- chosen_nuisance(N), chosen_solution(S), valid(N, S).
outcome(peaceful) :- peaceful.
outcome(restless) :- not peaceful.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    for cid in CHEESES:
        lines.append(asp.fact("cheese", cid))
    for nid, nuisance in NUISANCES.items():
        lines.append(asp.fact("nuisance", nid))
        lines.append(asp.fact("severity", nid, nuisance.severity))
        for need in sorted(nuisance.needs):
            lines.append(asp.fact("needs", nid, need))
    for sid, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, solution.sense))
        lines.append(asp.fact("power", sid, solution.power))
        for fix in sorted(solution.fixes):
            lines.append(asp.fact("fixes", sid, fix))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_nuisance", params.nuisance),
            asp.fact("chosen_solution", params.solution),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def outcome_of(params: StoryParams) -> str:
    nuisance = NUISANCES[params.nuisance]
    solution = SOLUTIONS[params.solution]
    return "peaceful" if valid_combo(nuisance, solution) else "restless"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos() matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for i in range(12):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(rng.randint(0, 999999)))
            p.seed = i
            cases.append(p)
        except StoryError:
            rc = 1
            print("FAILED: resolve_params() unexpectedly raised during verify.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"FAILED: smoke-test generation crashed: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost storyworld: a child solves a haunted pantry problem with rhyme."
    )
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--cheese", choices=CHEESES)
    ap.add_argument("--nuisance", choices=NUISANCES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible nuisance/solution pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.nuisance and args.solution:
        nuisance = NUISANCES[args.nuisance]
        solution = SOLUTIONS[args.solution]
        if not valid_combo(nuisance, solution):
            raise StoryError(explain_rejection(nuisance, solution))

    combos = [
        combo for combo in valid_combos()
        if (args.nuisance is None or combo[0] == args.nuisance)
        and (args.solution is None or combo[1] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid nuisance/solution combination matches the given options.)")

    nuisance_id, solution_id = rng.choice(sorted(combos))
    ghost = args.ghost or rng.choice(sorted(GHOSTS))
    cheese = args.cheese or rng.choice(sorted(CHEESES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        ghost=ghost,
        cheese=cheese,
        nuisance=nuisance_id,
        solution=solution_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [
        (params.ghost, GHOSTS),
        (params.cheese, CHEESES),
        (params.nuisance, NUISANCES),
        (params.solution, SOLUTIONS),
    ]:
        if key not in table:
            raise StoryError(f"(Unknown option: {key})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("(Unknown child gender.)")
    if params.elder_type not in {"grandmother", "grandfather"}:
        raise StoryError("(Unknown elder type.)")

    nuisance = NUISANCES[params.nuisance]
    solution = SOLUTIONS[params.solution]
    if not valid_combo(nuisance, solution):
        raise StoryError(explain_rejection(nuisance, solution))

    world = tell(
        GHOSTS[params.ghost],
        CHEESES[params.cheese],
        nuisance,
        solution,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (nuisance, solution) pairs:\n")
        for nuisance, solution in combos:
            print(f"  {nuisance:10} {solution}")
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
            header = f"### {p.child_name}: {p.nuisance} -> {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
