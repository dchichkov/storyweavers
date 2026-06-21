#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py
===============================================================================

A standalone story world for a bedtime-style "mystery to solve" tale in a
neighborhood park.

The core shape is simple and state-driven:

- A child visits the neighborhood park near evening.
- Something odd is missing from the park's marigold bed.
- A shadowy clue seems scary at first and can terrify the child.
- The child gets help, follows clues, and solves the mystery.
- The ending proves what changed: fear eases, the true cause is known, and the
  park is seen in a kinder light.

The world model uses physical meters and emotional memes.  A small causal engine
tracks fear, clues, discovery, and relief.  The Python reasonableness gate and
the inline ASP twin agree on which combinations make a good mystery.

Run it
------
    python storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py
    python storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py --missing sign --cause wind
    python storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py --cause fox --clue pawprints
    python storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py --cause raccoon --clue ribbon
    python storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/view_terrify_marigold_neighborhood_park_mystery_to.py --verify
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
FEAR_TERRIFY = 2.0


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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Parametrization knobs
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
class MissingThing:
    id: str
    label: str
    phrase: str
    home: str
    question: str
    importance: str
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
class Cause:
    id: str
    label: str
    living: bool
    scary_shape: str
    took: str
    left_by: str
    found_place: str
    resolution: str
    moral: str
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
class Clue:
    id: str
    label: str
    phrase: str
    leads_to: str
    works_for: set[str] = field(default_factory=set)
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
    type: str
    role_name: str
    calming_line: str
    find_line: str
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


def _r_shadow_fear(world: World) -> list[str]:
    child = world.get("child")
    out: list[str] = []
    if child.meters["odd_view"] >= THRESHOLD and child.memes["fear"] < THRESHOLD:
        return out
    sig = ("shadow_fear",)
    if sig in world.fired:
        return out
    if child.meters["odd_view"] >= THRESHOLD:
        world.fired.add(sig)
        child.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_terrify(world: World) -> list[str]:
    child = world.get("child")
    out: list[str] = []
    sig = ("terrify",)
    if sig in world.fired:
        return out
    if child.memes["fear"] >= FEAR_TERRIFY:
        world.fired.add(sig)
        child.memes["terrified"] += 1
        out.append("__terrify__")
    return out


def _r_follow_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_matches") and world.get("child").meters["clue_seen"] >= THRESHOLD:
        sig = ("follow_clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").meters["trail_progress"] += 1
            out.append("__trail__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["trail_progress"] >= THRESHOLD and child.meters["object_found"] >= THRESHOLD:
        sig = ("solve",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 2
            child.memes["wonder"] += 1
            child.memes["fear"] = 0.0
            child.meters["mystery_solved"] += 1
            out.append("__solved__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="shadow_fear", tag="emotional", apply=_r_shadow_fear),
    Rule(name="terrify", tag="emotional", apply=_r_terrify),
    Rule(name="follow_clue", tag="physical", apply=_r_follow_clue),
    Rule(name="solve", tag="resolution", apply=_r_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def clue_fits(cause: Cause, clue: Clue) -> bool:
    return cause.id in clue.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for missing_id in MISSING:
        for cause_id in CAUSES:
            for clue_id, clue in CLUES.items():
                if clue_fits(CAUSES[cause_id], clue):
                    combos.append((missing_id, cause_id, clue_id))
    return combos


def explain_rejection(cause: Cause, clue: Clue) -> str:
    return (
        f"(No story: the clue '{clue.label}' does not honestly point to {cause.label}. "
        f"A mystery should be solvable from real evidence, so choose a clue that fits the cause.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_scare(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["odd_view"] += 1
    sim.get("child").memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "terrified": sim.get("child").memes["terrified"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"In the evening, when the neighborhood park was turning soft and gold, "
        f"{child.id} walked there with {child.pronoun('possessive')} {helper.label_word}. "
        f"The swings were still, and the little marigold bed by the path shone like a row of tiny suns."
    )


def park_view(world: World, child: Entity, missing: MissingThing) -> None:
    child.memes["calm"] += 1
    world.say(
        f"{child.id} liked the view from the low hill near the sandbox. From there, "
        f"{child.pronoun()} could see the pond, the benches, and {missing.home}."
    )


def discover_missing(world: World, child: Entity, missing: MissingThing) -> None:
    child.meters["noticed_missing"] += 1
    world.say(
        f"But when {child.pronoun()} looked carefully, {child.pronoun()} stopped. "
        f"{missing.phrase} was gone."
    )
    world.say(
        f'"Oh," {child.id} whispered, "{missing.question}" {missing.importance}'
    )


def shadow_scare(world: World, child: Entity, cause: Cause) -> None:
    child.meters["odd_view"] += 1
    child.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Down by the marigolds, the fading light made {cause.scary_shape}. "
        f"For one quick moment, the strange view seemed big enough to terrify {child.id}."
    )


def comfort(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    scared = child.memes["terrified"] >= THRESHOLD
    if scared:
        world.say(
            f"{helper.label_word.capitalize()} knelt beside {child.id} and held {child.pronoun('possessive')} hand. "
            f'"{helper.calming_line}"'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} touched {child.id}\'s shoulder and said, "{helper.calming_line}"'
        )


def inspect_clue(world: World, child: Entity, helper: Entity, clue: Clue, cause: Cause) -> None:
    child.meters["clue_seen"] += 1
    world.facts["clue_matches"] = clue_fits(cause, clue)
    propagate(world, narrate=False)
    world.say(
        f"Together they looked closer. Near the marigolds they found {clue.phrase}."
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled a small solving smile. "{helper.find_line} {clue.leads_to}"'
    )


def follow_trail(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"So they followed the clue past the drinking fountain and around the little maple tree. "
        f"Step by step, the mystery felt smaller and the park felt friendlier."
    )


def find_object(world: World, child: Entity, missing: MissingThing, cause: Cause) -> None:
    child.meters["object_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"And there, {cause.found_place}, they found {missing.phrase}. {cause.left_by}"
    )


def explain(world: World, child: Entity, helper: Entity, missing: MissingThing, cause: Cause) -> None:
    world.say(
        f'"So that was the mystery," said {helper.label_word}. "{cause.resolution}"'
    )
    world.say(
        f"{child.id} let out a long breath. {cause.moral}"
    )


def ending(world: World, child: Entity, missing: MissingThing) -> None:
    world.say(
        f"Before they went home, {child.id} set {missing.phrase} back in its place and looked over the quiet park once more. "
        f"The same evening view no longer seemed spooky at all. The marigold bed glowed softly, and the mystery was asleep for the night."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    *,
    missing: MissingThing,
    cause: Cause,
    clue: Clue,
    helper_cfg: Helper,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_name: str = "Parent",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_name, role="helper"))
    park = world.add(Entity(id="park", kind="thing", type="park", label="neighborhood park"))
    bed = world.add(Entity(id="flowers", kind="thing", type="flowerbed", label="marigold bed"))

    child.attrs["name"] = child_name
    helper.attrs["name"] = helper_cfg.label
    world.facts["clue_matches"] = clue_fits(cause, clue)

    child.memes["fear"] = 0.0
    child.memes["terrified"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["wonder"] = 0.0
    child.meters["odd_view"] = 0.0
    child.meters["clue_seen"] = 0.0
    child.meters["trail_progress"] = 0.0
    child.meters["object_found"] = 0.0
    child.meters["mystery_solved"] = 0.0

    introduce(world, child, helper)
    park_view(world, child, missing)

    world.para()
    discover_missing(world, child, missing)
    shadow_scare(world, child, cause)
    comfort(world, child, helper)

    world.para()
    inspect_clue(world, child, helper, clue, cause)
    follow_trail(world, child, helper, clue)
    find_object(world, child, missing, cause)
    explain(world, child, helper, missing, cause)

    world.para()
    ending(world, child, missing)

    world.facts.update(
        child=child,
        helper=helper,
        park=park,
        flowers=bed,
        missing=missing,
        cause=cause,
        clue=clue,
        outcome="solved" if child.meters["mystery_solved"] >= THRESHOLD else "unsolved",
        terrified=child.memes["terrified"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
MISSING = {
    "sign": MissingThing(
        id="sign",
        label="the little garden sign",
        phrase="the little garden sign",
        home="the tiny sign that said PLEASE DO NOT PICK THE MARIGOLDS",
        question="Where did the marigold sign go",
        importance="Without it, the flower bed looked bare and wrong.",
        tags={"sign", "marigold", "park"},
    ),
    "watering_can": MissingThing(
        id="watering_can",
        label="the green watering can",
        phrase="the green watering can",
        home="the green watering can that usually rested by the marigold bed",
        question="Who moved the watering can",
        importance="The flowers looked thirsty without it nearby.",
        tags={"watering_can", "marigold", "park"},
    ),
    "ribbon": MissingThing(
        id="ribbon",
        label="the yellow ribbon",
        phrase="the yellow ribbon",
        home="the yellow ribbon tied around the little fence beside the marigolds",
        question="Where did the yellow ribbon go",
        importance="It was the cheerful finishing touch of the flower bed.",
        tags={"ribbon", "marigold", "park"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="the wind",
        living=False,
        scary_shape="a long wobbling shadow that kept bobbing and bowing",
        took="blew it away",
        left_by="The evening breeze had tucked it there without meaning any harm.",
        found_place="under the slide where dry leaves had gathered",
        resolution="The wind had blown it from the marigold bed and carried it to a quiet corner.",
        moral="It had looked mysterious in the dim light, but it was only the wind being busy.",
        tags={"wind", "weather"},
    ),
    "fox": Cause(
        id="fox",
        label="a small fox",
        living=True,
        scary_shape="two bright eyes and a bushy-tail shadow behind the bench",
        took="nudged it away",
        left_by="A small fox had borrowed it while sniffing for crumbs, then dropped it when something rustled.",
        found_place="beside the hedge near the far bench",
        resolution="A curious fox had nosed it away, then left it behind when it lost interest.",
        moral="The park still held small wild visitors, but knowing the truth made them feel more wonderful than scary.",
        tags={"fox", "animal"},
    ),
    "raccoon": Cause(
        id="raccoon",
        label="a raccoon",
        living=True,
        scary_shape="a round shadow with careful little hands near the trash bin",
        took="carried it off",
        left_by="A raccoon had dragged it a little way, then set it down when it found nothing tasty about it.",
        found_place="behind the recycling bin, safe and only a little dusty",
        resolution="A nosy raccoon had carried it away for a minute, then abandoned it.",
        moral="Sometimes a thing that seems spooky is only an animal being curious in the dusk.",
        tags={"raccoon", "animal"},
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="pawprints",
        phrase="tiny pawprints pressed into the damp soil",
        leads_to="Little tracks are better than scary guesses.",
        works_for={"fox", "raccoon"},
        tags={"tracks", "animal"},
    ),
    "petals": Clue(
        id="petals",
        label="marigold petals",
        phrase="three bright marigold petals caught in a line along the path",
        leads_to="If pieces make a trail, we can walk where the trail goes.",
        works_for={"wind", "fox", "raccoon"},
        tags={"marigold", "trail"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="a snagged ribbon thread",
        phrase="a tiny yellow thread snagged on the hedge",
        leads_to="A caught thread can show the way a thing traveled.",
        works_for={"wind", "raccoon"},
        tags={"ribbon", "trail"},
    ),
}

HELPERS = {
    "mother": Helper(
        id="mother",
        label="mom",
        type="mother",
        role_name="mom",
        calming_line="Let us look closely before we let shadows choose the story.",
        find_line="Every clue tells a quiet truth.",
        tags={"family"},
    ),
    "father": Helper(
        id="father",
        label="dad",
        type="father",
        role_name="dad",
        calming_line="A dark shape can look bigger than it really is. We can solve this together.",
        find_line="Clues help our eyes and hearts slow down.",
        tags={"family"},
    ),
    "gardener": Helper(
        id="gardener",
        label="the gardener",
        type="woman",
        role_name="gardener",
        calming_line="The park looks different at dusk, but it still leaves honest clues.",
        find_line="The ground usually whispers what happened.",
        tags={"community"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Eli", "Max", "Noah", "Finn", "Theo"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    missing: str
    cause: str
    clue: str
    helper: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "marigold": [
        (
            "What is a marigold?",
            "A marigold is a bright garden flower, often yellow or orange. It grows in sunny blossoms that can make a flower bed look warm and cheerful."
        )
    ],
    "wind": [
        (
            "How can wind move things in a park?",
            "Wind can push light things along the ground or blow them into corners and under benches. That is why a small sign, ribbon, or paper can end up somewhere surprising."
        )
    ],
    "tracks": [
        (
            "What can pawprints tell you?",
            "Pawprints can show that an animal walked through a place. They can also help you guess where it went next."
        )
    ],
    "fox": [
        (
            "Do foxes live near parks?",
            "Sometimes they do. A fox may visit a quiet park at dusk if it is looking for food or sniffing around."
        )
    ],
    "raccoon": [
        (
            "Why do raccoons pick things up?",
            "Raccoons are curious animals and often touch or carry things while they explore. They are looking and smelling to learn what something is."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet. You solve it by noticing clues and thinking carefully."
        )
    ],
    "park": [
        (
            "Why can a park look different in the evening?",
            "When the light gets dim, shadows grow longer and shapes can look strange. The place is the same, but your eyes may need more time to understand what they see."
        )
    ],
}

KNOWLEDGE_ORDER = ["mystery", "park", "marigold", "wind", "tracks", "fox", "raccoon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    missing = f["missing"]
    cause = f["cause"]
    return [
        'Write a bedtime story for a 3-to-5-year-old set in a neighborhood park, with a gentle mystery to solve, and include the words "view", "terrify", and "marigold".',
        f"Tell a soft, suspenseful story where {child.attrs['name']} notices that {missing.phrase} is missing from the marigold bed, feels frightened by an evening view, and solves the mystery with {helper.label_word}.",
        f"Write a calm mystery story in which a scary shadow first seems to terrify a child, but the real answer turns out to be {cause.label} and the ending makes the park feel safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    missing = f["missing"]
    clue = f["clue"]
    cause = f["cause"]
    helper_word = helper.label_word
    name = child.attrs["name"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name} and {helper_word} in the neighborhood park. They notice that {missing.phrase} is missing from the marigold bed."
        ),
        (
            "What made the park feel scary at first?",
            f"The evening light made a strange shadowy view near the marigolds. For a moment, that unclear shape seemed big enough to terrify {name} because {child.pronoun()} did not yet know what it really was."
        ),
        (
            f"How did {name} start solving the mystery?",
            f"{name} did not run away. {helper_word.capitalize()} helped {child.pronoun('object')} look closely, and together they found {clue.phrase}, which gave them a real clue to follow."
        ),
        (
            f"What was the true answer to the mystery?",
            f"The real cause was {cause.label}. They found {missing.phrase} {cause.found_place}, and that discovery showed the scary guess had been wrong."
        ),
        (
            "How did the story end?",
            f"It ended quietly and safely. {name} put {missing.phrase} back, and the same park view that had seemed spooky now felt gentle because the mystery was solved."
        ),
    ]
    if f["terrified"]:
        items.append(
            (
                f"Why did {name} feel better after the clue was found?",
                f"{name} felt better because the clue turned a scary feeling into something understandable. Once they could follow real evidence, fear gave way to relief and wonder."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "park", "marigold"}
    cause = world.facts["cause"]
    clue = world.facts["clue"]
    tags |= set(cause.tags)
    tags |= set(clue.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
clue_fits(Cause, Clue) :- clue_for(Clue, Cause).
valid(Missing, Cause, Clue) :- missing(Missing), cause(Cause), clue(Clue), clue_fits(Cause, Clue).

% fear / terrify / solved model
fear_after_shadow(2).
terrified :- fear_after_shadow(F), terrify_level(T), F >= T.
solved :- chosen_cause(C), chosen_clue(K), clue_fits(C, K).

outcome(solved) :- solved.
#show valid/3.
#show outcome/1.
#show terrified/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MISSING:
        lines.append(asp.fact("missing", mid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for kid, clue in CLUES.items():
        lines.append(asp.fact("clue", kid))
        for cause_id in sorted(clue.works_for):
            lines.append(asp.fact("clue_for", kid, cause_id))
    lines.append(asp.fact("terrify_level", int(FEAR_TERRIFY)))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> tuple[str, bool]:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_clue", params.clue),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1.\n#show terrified/0."))
    outcome_atoms = asp.atoms(model, "outcome")
    terrified = bool(asp.atoms(model, "terrified"))
    outcome = outcome_atoms[0][0] if outcome_atoms else "?"
    return outcome, terrified


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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        py_outcome = "solved" if clue_fits(CAUSES[params.cause], CLUES[params.clue]) else "?"
        asp_out, _ = asp_outcome(params)
        if py_outcome != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        missing="sign",
        cause="wind",
        clue="petals",
        helper="mother",
        child_name="Mina",
        child_gender="girl",
        seed=101,
    ),
    StoryParams(
        missing="watering_can",
        cause="fox",
        clue="pawprints",
        helper="father",
        child_name="Leo",
        child_gender="boy",
        seed=102,
    ),
    StoryParams(
        missing="ribbon",
        cause="raccoon",
        clue="ribbon",
        helper="gardener",
        child_name="Ruby",
        child_gender="girl",
        seed=103,
    ),
    StoryParams(
        missing="sign",
        cause="raccoon",
        clue="pawprints",
        helper="mother",
        child_name="Ben",
        child_gender="boy",
        seed=104,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime mystery in a neighborhood park."
    )
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.clue:
        cause = CAUSES[args.cause]
        clue = CLUES[args.clue]
        if not clue_fits(cause, clue):
            raise StoryError(explain_rejection(cause, clue))

    combos = [
        c
        for c in valid_combos()
        if (args.missing is None or c[0] == args.missing)
        and (args.cause is None or c[1] == args.cause)
        and (args.clue is None or c[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    missing, cause, clue = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)

    return StoryParams(
        missing=missing,
        cause=cause,
        clue=clue,
        helper=helper,
        child_name=child_name,
        child_gender=child_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.missing not in MISSING:
        raise StoryError(f"(Unknown missing thing: {params.missing})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not clue_fits(CAUSES[params.cause], CLUES[params.clue]):
        raise StoryError(explain_rejection(CAUSES[params.cause], CLUES[params.clue]))

    helper_cfg = HELPERS[params.helper]
    helper_name = helper_cfg.label.capitalize() if helper_cfg.id in {"mother", "father"} else helper_cfg.label

    world = tell(
        missing=MISSING[params.missing],
        cause=CAUSES[params.cause],
        clue=CLUES[params.clue],
        helper_cfg=helper_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=helper_name,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        print(asp_program(show="#show valid/3.\n#show outcome/1.\n#show terrified/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (missing, cause, clue) combos:\n")
        for missing, cause, clue in combos:
            print(f"  {missing:12} {cause:8} {clue}")
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
            header = f"### {p.child_name}: missing {p.missing}, cause {p.cause}, clue {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
