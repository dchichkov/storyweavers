#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/eruption_conditioner_dialogue_sharing_rhyming_story.py
=================================================================================

A standalone story world about two children making pretend volcanoes and learning
to share one bottle of conditioner. The world stays small and concrete: the
children build volcanoes, notice a shortage, argue in dialogue, and choose a
sharing plan that the simulated state can actually support.

The style aims for a child-facing rhyming story, but the prose is still driven by
world state rather than a frozen template. A bottle amount, a volcano size, and a
sharing plan determine whether the ending becomes:

* two small eruptions, when there is enough conditioner for both volcanoes, or
* one shared eruption, when there is only enough for one volcano and the children
  decide to work together.

Run it
------
    python storyworlds/worlds/gpt-5.4/eruption_conditioner_dialogue_sharing_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/eruption_conditioner_dialogue_sharing_rhyming_story.py --shell tall_cone --bottle small
    python storyworlds/worlds/gpt-5.4/eruption_conditioner_dialogue_sharing_rhyming_story.py --plan divide
    python storyworlds/worlds/gpt-5.4/eruption_conditioner_dialogue_sharing_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/eruption_conditioner_dialogue_sharing_rhyming_story.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    surface: str
    detail: str
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
class Shell:
    id: str
    label: str
    phrase: str
    need: int
    crater: str
    material: str
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
class Bottle:
    id: str
    label: str
    phrase: str
    amount: int
    smell: str
    color: str
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
class Plan:
    id: str
    label: str
    kind: str
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


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen table",
        surface="a tray on the kitchen table",
        detail="Sunlight lay in yellow squares across the table.",
        tags={"kitchen", "indoors"},
    ),
    "porch": Setting(
        id="porch",
        place="the back porch",
        surface="a plastic mat on the back porch",
        detail="A breeze moved the leaves, but the mat kept the project neat.",
        tags={"porch", "outdoors"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom floor",
        surface="a wipe-clean mat on the playroom floor",
        detail="The room smelled like crayons and old games waiting for a turn.",
        tags={"playroom", "indoors"},
    ),
}

SHELLS = {
    "cup_cone": Shell(
        id="cup_cone",
        label="cup cone",
        phrase="a little cup cone",
        need=1,
        crater="a tiny round crater",
        material="packed sand around a paper cup",
        tags={"volcano", "small"},
    ),
    "sand_mound": Shell(
        id="sand_mound",
        label="sand mound",
        phrase="a sandy mound with a thumb-made crater",
        need=1,
        crater="a shallow sandy crater",
        material="damp sand",
        tags={"volcano", "small"},
    ),
    "tall_cone": Shell(
        id="tall_cone",
        label="tall cone",
        phrase="a tall clay cone",
        need=2,
        crater="a deep clay crater",
        material="modeling clay",
        tags={"volcano", "big"},
    ),
}

BOTTLES = {
    "small": Bottle(
        id="small",
        label="small bottle",
        phrase="a small bottle of strawberry conditioner",
        amount=2,
        smell="strawberry sweet",
        color="pink",
        tags={"conditioner", "small_bottle"},
    ),
    "medium": Bottle(
        id="medium",
        label="medium bottle",
        phrase="a medium bottle of coconut conditioner",
        amount=3,
        smell="coconut soft",
        color="white",
        tags={"conditioner", "medium_bottle"},
    ),
    "big": Bottle(
        id="big",
        label="big bottle",
        phrase="a big bottle of vanilla conditioner",
        amount=4,
        smell="vanilla warm",
        color="cream",
        tags={"conditioner", "big_bottle"},
    ),
}

PLANS = {
    "divide": Plan(
        id="divide",
        label="divide the conditioner into two cups",
        kind="divide",
        tags={"sharing", "fairness"},
    ),
    "teamwork": Plan(
        id="teamwork",
        label="pour everything into one volcano and do it together",
        kind="teamwork",
        tags={"sharing", "teamwork"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ruby", "Ella", "Anna"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Sam", "Eli", "Noah", "Finn"]
TRAITS = ["eager", "careful", "bouncy", "curious", "patient", "sparkly"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"first", "second"}]


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


def _r_shortage_conflict(world: World) -> list[str]:
    bottle = world.get("bottle")
    need_each = world.facts["shell_cfg"].need
    for kid in world.kids():
        if kid.memes["want_own"] < THRESHOLD:
            continue
    if bottle.meters["amount"] < need_each * 2:
        sig = ("shortage_conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["worry"] += 1
                kid.memes["conflict"] += 1
            return ["__shortage__"]
    return []


def _r_ready(world: World) -> list[str]:
    out: list[str] = []
    need = world.facts["shell_cfg"].need
    for vid in ("volcano_a", "volcano_b", "shared_volcano"):
        if vid not in world.entities:
            continue
        volcano = world.get(vid)
        if volcano.meters["conditioner"] >= need and volcano.meters["baking_soda"] >= THRESHOLD:
            sig = ("ready", vid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            volcano.meters["ready"] += 1
            out.append("__ready__")
    return out


def _r_eruption(world: World) -> list[str]:
    out: list[str] = []
    for vid in ("volcano_a", "volcano_b", "shared_volcano"):
        if vid not in world.entities:
            continue
        volcano = world.get(vid)
        if volcano.meters["ready"] < THRESHOLD or volcano.meters["vinegar"] < THRESHOLD:
            continue
        sig = ("eruption", vid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        volcano.meters["eruption"] += 1
        volcano.meters["foam"] += volcano.meters["conditioner"]
        out.append("__eruption__")
    return out


CAUSAL_RULES = [
    Rule(name="shortage_conflict", tag="social", apply=_r_shortage_conflict),
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="eruption", tag="physical", apply=_r_eruption),
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
                produced.extend(out)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def enough_for_divide(shell: Shell, bottle: Bottle) -> bool:
    return bottle.amount >= shell.need * 2


def enough_for_teamwork(shell: Shell, bottle: Bottle) -> bool:
    return bottle.amount >= shell.need


def valid_plan(shell: Shell, bottle: Bottle, plan: Plan) -> bool:
    if plan.kind == "divide":
        return enough_for_divide(shell, bottle)
    if plan.kind == "teamwork":
        return enough_for_teamwork(shell, bottle)
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for shell_id, shell in SHELLS.items():
            for bottle_id, bottle in BOTTLES.items():
                for plan_id, plan in PLANS.items():
                    if valid_plan(shell, bottle, plan):
                        combos.append((setting_id, shell_id, bottle_id, plan_id))
    return combos


def explain_rejection(shell: Shell, bottle: Bottle, plan: Plan) -> str:
    if plan.kind == "divide":
        need = shell.need * 2
        return (
            f"(No story: {bottle.phrase} holds {bottle.amount} squeeze"
            f"{'' if bottle.amount == 1 else 's'}, but two {shell.label} volcanoes "
            f"need {need}. There is not enough conditioner for a fair split.)"
        )
    return (
        f"(No story: even one {shell.label} volcano needs {shell.need} squeeze"
        f"{'' if shell.need == 1 else 's'} of conditioner, but {bottle.phrase} "
        f"holds only {bottle.amount}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    shell = SHELLS[params.shell]
    bottle = BOTTLES[params.bottle]
    plan = PLANS[params.plan]
    if not valid_plan(shell, bottle, plan):
        return "invalid"
    return "two_small" if plan.kind == "divide" else "one_shared"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict_options(world: World, shell: Shell, bottle: Bottle) -> dict:
    return {
        "enough_for_two": enough_for_divide(shell, bottle),
        "enough_for_one": enough_for_teamwork(shell, bottle),
    }


def introduce(world: World, a: Entity, b: Entity, helper: Entity, shell: Shell, bottle: Bottle) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["want_own"] = 1.0
    world.say(
        f"{a.id} and {b.id} sat by {world.setting.surface}, bright-eyed with glee. "
        f'"Let\'s build volcanoes!" they sang. "One for you, and one for me!"'
    )
    world.say(
        f"They patted {shell.material} into shape until each volcano wore {shell.crater}. "
        f"{world.setting.detail}"
    )
    world.say(
        f"Beside the tray stood {bottle.phrase}. It smelled {bottle.smell}, soft and sweet, "
        f"and everyone said the lava would be foamy if that bottle joined the treat."
    )
    world.facts["need_each"] = shell.need
    world.facts["starting_amount"] = bottle.amount


def reach_and_argue(world: World, a: Entity, b: Entity, bottle: Entity) -> None:
    a.memes["grabby"] += 1
    b.memes["grabby"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} reached first. "I want the first pink squeeze!" {a.pronoun()} cried with pride. '
        f'"If my mountain makes the biggest eruption, I will dance from side to side."'
    )
    world.say(
        f'{b.id} reached too. "That is not fair," {b.pronoun()} said. '
        f'"I helped build this bubbling hill. We should share the conditioner bottle, '
        f"not grab and grab our fill."
    )
    if bottle.meters["amount"] < world.facts["need_each"] * 2:
        world.say(
            "They counted the squeezes on the bottle and their smiles grew small with doubt. "
            "There might not be enough for two proud lava rivers rushing out."
        )


def helper_reads_world(world: World, helper: Entity, shell: Shell, bottle: Bottle) -> None:
    pred = predict_options(world, shell, bottle)
    world.facts["predicted_two"] = pred["enough_for_two"]
    world.facts["predicted_one"] = pred["enough_for_one"]
    if pred["enough_for_two"]:
        world.say(
            f'{helper.label_word.capitalize()} knelt beside them. "Count with me, one squeeze, then two. '
            f'There is enough for both volcanoes if both of you are fair and true."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} knelt beside them. "Listen close before you pout. '
            f'This bottle can help one good eruption, but not two big ones pouring out."'
        )


def choose_plan(world: World, a: Entity, b: Entity, helper: Entity, plan: Plan) -> None:
    if plan.kind == "divide":
        world.say(
            f'"Then let\'s use little cups," said {helper.label_word}. "Share it with a careful hand." '
            f'"A smaller burst for each of you is still a lovely, fizzy plan."'
        )
        world.say(
            f'{a.id} looked at {b.id}. "{b.id}, will you share?" {a.pronoun()} asked at last. '
            f'"Yes," said {b.id}. "If we take turns, the fun will stay and the fuss will pass."'
        )
        for kid in (a, b):
            kid.memes["fairness"] += 1
            kid.memes["conflict"] = 0.0
            kid.memes["relief"] += 1
    else:
        world.say(
            f'"Then let us make one grand volcano," said {helper.label_word}, calm and wise. '
            f'"Two hands can pour one mighty stream, and both can cheer the foamy surprise."'
        )
        world.say(
            f'{b.id} held out a measuring cup. "{a.id}, come pour with me." '
            f'{a.id} nodded. "One shared hill is better than one sad child and one happy me."'
        )
        for kid in (a, b):
            kid.memes["fairness"] += 1
            kid.memes["conflict"] = 0.0
            kid.memes["relief"] += 1
            kid.memes["teamwork"] += 1


def prepare_divide(world: World, a: Entity, b: Entity, shell: Shell, bottle: Entity) -> None:
    bottle.meters["amount"] -= shell.need
    world.get("volcano_a").meters["conditioner"] += shell.need
    world.get("volcano_a").meters["baking_soda"] += 1
    bottle.meters["amount"] -= shell.need
    world.get("volcano_b").meters["conditioner"] += shell.need
    world.get("volcano_b").meters["baking_soda"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They squeezed the conditioner into two little cups, one for {a.id} and one for {b.id}. "
        f"Each child stirred a silky swirl, and each small crater waited wide."
    )
    world.say(
        "The pinky foam looked glossy-smooth; the baking soda sat below. "
        "Two tiny mountains stood quite still, all set to fizz and glow."
    )


def prepare_teamwork(world: World, a: Entity, b: Entity, shell: Shell, bottle: Entity) -> None:
    world.add(Entity(id="shared_volcano", type="volcano", label="shared volcano"))
    bottle.meters["amount"] -= shell.need
    world.get("shared_volcano").meters["conditioner"] += shell.need
    world.get("shared_volcano").meters["baking_soda"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they chose the steadiest hill and patted its sides just so. "
        f"{a.id} poured, {b.id} held the cup, and the creamy lava waited low."
    )
    world.say(
        "Nothing was wasted, nothing was hidden, nothing was claimed alone. "
        "Their plan made room for both small hands around one careful cone."
    )


def erupt_divide(world: World, a: Entity, b: Entity, shell: Shell) -> None:
    world.get("volcano_a").meters["vinegar"] += 1
    world.get("volcano_b").meters["vinegar"] += 1
    propagate(world, narrate=False)
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f'"Ready?" asked {a.id}. "Ready!" sang {b.id}. They poured with a twinkly grip. '
        f"Up came a fizz, then a frothy hiss, then foam with a slippery skip."
    )
    world.say(
        "One little eruption puffed and plopped. Then the other joined the song. "
        "Two tiny lava crowns rolled down, and both children clapped along."
    )
    world.facts["eruption_count"] = 2
    world.facts["used_amount"] = shell.need * 2


def erupt_teamwork(world: World, a: Entity, b: Entity, shell: Shell) -> None:
    world.get("shared_volcano").meters["vinegar"] += 1
    propagate(world, narrate=False)
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f'"Now!" cried {a.id}. "{b.id}, pour!" The vinegar slipped in white. '
        f"Then up rushed foam in a scented bloom, all bubbly, soft, and bright."
    )
    world.say(
        "The eruption rolled in a creamy ring and slid from the crater lip. "
        "Both children laughed as they leaned in close to watch each wiggly drip."
    )
    world.facts["eruption_count"] = 1
    world.facts["used_amount"] = shell.need


def ending_divide(world: World, a: Entity, b: Entity, helper: Entity, bottle: Entity) -> None:
    world.say(
        f'{helper.label_word.capitalize()} smiled. "See what sharing can do? Two turns, two cheers, no lonely face." '
        f'{a.id} bumped {b.id} with a floury elbow. "{b.id}, thanks for making space."'
    )
    left = int(bottle.meters["amount"])
    if left > 0:
        world.say(
            f"There was even {left} squeeze left in the bottle, resting there like a tiny treat. "
            "They saved it for another day, which made the ending neat and sweet."
        )
    else:
        world.say(
            "The bottle was light, the tray was bright, and the quarrel was all through. "
            "Two small volcanoes stood side by side, and both hearts felt brand new."
        )


def ending_teamwork(world: World, a: Entity, b: Entity, helper: Entity, bottle: Entity) -> None:
    world.say(
        f'{helper.label_word.capitalize()} smiled. "One shared plan can still be grand. '
        f'You did not grab. You chose to share, and that made room for every hand."'
    )
    left = int(bottle.meters["amount"])
    tail = "a little" if left == 1 else str(left)
    if left > 0:
        world.say(
            f"There was {tail} squeeze left in the conditioner bottle, soft and slow. "
            f"But the best part was not what stayed. It was watching kindness grow."
        )
    else:
        world.say(
            "The bottle was empty, the mat was speckled, the foamy river curled and shone. "
            "The children had made one splendid hill, and no one watched alone."
        )
@dataclass
class StoryParams:
    setting: str
    shell: str
    bottle: str
    plan: str
    first_name: str
    first_gender: str
    second_name: str
    second_gender: str
    helper: str
    first_trait: str
    second_trait: str
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
    "volcano": [
        (
            "What is an eruption?",
            "An eruption is when a volcano pushes material out from its top. In a toy science project, the eruption is pretend foam and fizz instead of hot rock."
        )
    ],
    "conditioner": [
        (
            "What is conditioner?",
            "Conditioner is a creamy hair product that helps make hair feel smooth. In this story, the children used it as part of a foamy volcano mixture, not for hair."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting more than one person use or enjoy something fairly. It helps everyone feel included instead of left out."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people do one job together and help each other. It can turn a problem into something everyone can enjoy."
        )
    ],
    "baking_soda": [
        (
            "Why do baking soda and vinegar fizz?",
            "They fizz because they react together and make a gas called carbon dioxide. The bubbles push the foamy mixture up and out."
        )
    ],
}

KNOWLEDGE_ORDER = ["volcano", "conditioner", "sharing", "teamwork", "baking_soda"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["first"]
    b = f["second"]
    shell = f["shell_cfg"]
    bottle = f["bottle_cfg"]
    ending = f["ending"]
    if ending == "two_small":
        return [
            'Write a rhyming story for a 3-to-5-year-old that includes the words "eruption" and "conditioner" and uses dialogue about sharing.',
            f"Tell a gentle rhyming story where {a.id} and {b.id} each build a {shell.label} volcano and learn to share {bottle.phrase} fairly.",
            "Write a child-facing poem-story with spoken lines, a small argument, and a happy ending where both children get a turn."
        ]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the words "eruption" and "conditioner" and uses dialogue about sharing.',
        f"Tell a gentle rhyming story where {a.id} and {b.id} want separate volcanoes, but there is only enough {bottle.label} conditioner for one shared eruption.",
        "Write a child-facing poem-story with spoken lines, a shortage, and a warm ending where teamwork matters more than having your own turn."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["first"]
    b = f["second"]
    helper = f["helper"]
    shell = f["shell_cfg"]
    bottle = f["bottle_cfg"]
    ending = f["ending"]
    used = f["used_amount"]
    remaining = f["remaining_amount"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children making pretend volcanoes, and their {helper.label_word} who helps them solve a problem. The problem begins when both children want the same bottle of conditioner for their lava."
        ),
        (
            "Why did the children start to argue?",
            f"They argued because both of them wanted the conditioner first, and the bottle might not hold enough for two full volcanoes. The shortage made each child worry about missing out on the eruption."
        ),
        (
            "How did the grown-up help?",
            f"The {helper.label_word} stopped the grabbing and counted what the bottle could really do. Then {helper.pronoun()} suggested a sharing plan that matched the amount of conditioner they had."
        ),
    ]
    if ending == "two_small":
        qa.append(
            (
                "What was their sharing plan?",
                f"They divided the conditioner into two cups so each {shell.label} volcano got enough to work. That plan was fair because the bottle held enough for both small eruptions."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"Both volcanoes fizzed and foamed, so each child got a turn to enjoy the eruption. Sharing changed the ending from a tug-of-war into two happy cheers."
            )
        )
    else:
        qa.append(
            (
                "Why did they choose one shared volcano instead of two?",
                f"They chose one shared volcano because the bottle had enough conditioner for one good eruption, but not for two separate ones. Working together let both children enjoy the result instead of one child winning and the other feeling left out."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The children poured together and watched one big foamy eruption spill over the crater. The ending feels happy because they shared the job and the joy, even though they did not each get a separate volcano."
            )
        )
    qa.append(
        (
            "How much conditioner did they use?",
            f"They used {used} squeeze{'' if used == 1 else 's'} of conditioner during the project. There were {remaining} squeeze{'' if remaining == 1 else 's'} left at the end."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"volcano", "conditioner", "sharing", "baking_soda"}
    if world.facts["ending"] == "one_shared":
        tags.add("teamwork")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
enough_for_divide(S,B) :- shell_need(S,N), bottle_amount(B,A), A >= N*2.
enough_for_teamwork(S,B) :- shell_need(S,N), bottle_amount(B,A), A >= N.

valid(St,S,B,divide) :- setting(St), shell(S), bottle(B), enough_for_divide(S,B).
valid(St,S,B,teamwork) :- setting(St), shell(S), bottle(B), enough_for_teamwork(S,B).

outcome(two_small) :- chosen_shell(S), chosen_bottle(B), chosen_plan(divide), enough_for_divide(S,B).
outcome(one_shared) :- chosen_shell(S), chosen_bottle(B), chosen_plan(teamwork), enough_for_teamwork(S,B).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for shell_id, shell in SHELLS.items():
        lines.append(asp.fact("shell", shell_id))
        lines.append(asp.fact("shell_need", shell_id, shell.need))
    for bottle_id, bottle in BOTTLES.items():
        lines.append(asp.fact("bottle", bottle_id))
        lines.append(asp.fact("bottle_amount", bottle_id, bottle.amount))
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_shell", params.shell),
            asp.fact("chosen_bottle", params.bottle),
            asp.fact("chosen_plan", params.plan),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
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
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test story was empty")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="kitchen",
        shell="cup_cone",
        bottle="small",
        plan="divide",
        first_name="Lily",
        first_gender="girl",
        second_name="Ben",
        second_gender="boy",
        helper="mother",
        first_trait="eager",
        second_trait="patient",
        seed=None,
    ),
    StoryParams(
        setting="porch",
        shell="tall_cone",
        bottle="small",
        plan="teamwork",
        first_name="Mia",
        first_gender="girl",
        second_name="Theo",
        second_gender="boy",
        helper="father",
        first_trait="bouncy",
        second_trait="careful",
        seed=None,
    ),
    StoryParams(
        setting="playroom",
        shell="sand_mound",
        bottle="medium",
        plan="divide",
        first_name="Ruby",
        first_gender="girl",
        second_name="Nora",
        second_gender="girl",
        helper="mother",
        first_trait="curious",
        second_trait="patient",
        seed=None,
    ),
    StoryParams(
        setting="porch",
        shell="tall_cone",
        bottle="medium",
        plan="teamwork",
        first_name="Eli",
        first_gender="boy",
        second_name="Max",
        second_gender="boy",
        helper="father",
        first_trait="eager",
        second_trait="curious",
        seed=None,
    ),
    StoryParams(
        setting="kitchen",
        shell="tall_cone",
        bottle="big",
        plan="divide",
        first_name="Ava",
        first_gender="girl",
        second_name="Leo",
        second_gender="boy",
        helper="mother",
        first_trait="sparkly",
        second_trait="careful",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: two children, one conditioner bottle, and a sharing choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shell", choices=SHELLS)
    ap.add_argument("--bottle", choices=BOTTLES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shell and args.bottle and args.plan:
        shell = SHELLS[args.shell]
        bottle = BOTTLES[args.bottle]
        plan = PLANS[args.plan]
        if not valid_plan(shell, bottle, plan):
            raise StoryError(explain_rejection(shell, bottle, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.shell is None or combo[1] == args.shell)
        and (args.bottle is None or combo[2] == args.bottle)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, shell_id, bottle_id, plan_id = rng.choice(sorted(combos))
    first_gender = rng.choice(["girl", "boy"])
    second_gender = rng.choice(["girl", "boy"])
    first_name = _pick_name(rng, first_gender)
    second_name = _pick_name(rng, second_gender, avoid=first_name)
    helper = args.helper or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        shell=shell_id,
        bottle=bottle_id,
        plan=plan_id,
        first_name=first_name,
        first_gender=first_gender,
        second_name=second_name,
        second_gender=second_gender,
        helper=helper,
        first_trait=rng.choice(TRAITS),
        second_trait=rng.choice(TRAITS),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.shell not in SHELLS:
        raise StoryError(f"(Unknown shell: {params.shell})")
    if params.bottle not in BOTTLES:
        raise StoryError(f"(Unknown bottle: {params.bottle})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    shell = SHELLS[params.shell]
    bottle = BOTTLES[params.bottle]
    plan = PLANS[params.plan]
    if not valid_plan(shell, bottle, plan):
        raise StoryError(explain_rejection(shell, bottle, plan))

    world = tell(
        setting=SETTINGS[params.setting],
        shell=shell,
        bottle_cfg=bottle,
        plan=plan,
        first_name=params.first_name,
        first_gender=params.first_gender,
        second_name=params.second_name,
        second_gender=params.second_gender,
        helper_type=params.helper,
        first_trait=params.first_trait,
        second_trait=params.second_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, shell, bottle, plan) combos:\n")
        for setting_id, shell_id, bottle_id, plan_id in combos:
            print(f"  {setting_id:9} {shell_id:11} {bottle_id:7} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.first_name} & {p.second_name}: {p.shell} with {p.bottle} ({p.plan}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    shell: Shell,
    bottle_cfg: Bottle,
    plan: Plan,
    first_name: str = "Lily",
    first_gender: str = "girl",
    second_name: str = "Leo",
    second_gender: str = "boy",
    helper_type: str = "mother",
    first_trait: str = "eager",
    second_trait: str = "curious",
) -> World:
    world = World(setting)
    a = world.add(Entity(id=first_name, kind="character", type=first_gender, role="first", attrs={"trait": first_trait}))
    b = world.add(Entity(id=second_name, kind="character", type=second_gender, role="second", attrs={"trait": second_trait}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    bottle = world.add(Entity(id="bottle", type="bottle", label=bottle_cfg.label, tags=set(bottle_cfg.tags)))
    bottle.meters["amount"] = float(bottle_cfg.amount)
    world.add(Entity(id="volcano_a", type="volcano", label=f"{a.id}'s volcano"))
    world.add(Entity(id="volcano_b", type="volcano", label=f"{b.id}'s volcano"))

    world.facts["setting"] = setting
    world.facts["shell_cfg"] = shell
    world.facts["bottle_cfg"] = bottle_cfg
    world.facts["plan_cfg"] = plan
    world.facts["first"] = a
    world.facts["second"] = b
    world.facts["helper"] = helper
    world.facts["used_amount"] = 0
    world.facts["eruption_count"] = 0

    introduce(world, a, b, helper, shell, bottle_cfg)
    world.para()
    reach_and_argue(world, a, b, bottle)
    helper_reads_world(world, helper, shell, bottle_cfg)
    choose_plan(world, a, b, helper, plan)
    world.para()

    if plan.kind == "divide":
        prepare_divide(world, a, b, shell, bottle)
        erupt_divide(world, a, b, shell)
        world.para()
        ending_divide(world, a, b, helper, bottle)
    else:
        prepare_teamwork(world, a, b, shell, bottle)
        erupt_teamwork(world, a, b, shell)
        world.para()
        ending_teamwork(world, a, b, helper, bottle)

    world.facts["ending"] = "two_small" if plan.kind == "divide" else "one_shared"
    world.facts["remaining_amount"] = int(world.get("bottle").meters["amount"])
    return world


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
