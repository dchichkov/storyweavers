#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grained_mystery_to_solve_friendship_teamwork_adventure.py
====================================================================================

A standalone story world about two camp friends solving a small outdoor mystery.
A needed adventure item has gone missing, a clue points toward the culprit, and
the children recover it by working together. The prose is state-driven: the item
is hidden, worry rises, clues are noticed, teamwork grows, and the ending image
proves what changed.

The world prefers a few strong combinations over broad coverage. A reasonable
story needs:
- a setting that actually supports the culprit and hiding spot,
- an item the culprit would really carry off,
- the clue that culprit would leave behind,
- and a retrieval method that is sensible for children to try.

Run it
------
    python storyworlds/worlds/gpt-5.4/grained_mystery_to_solve_friendship_teamwork_adventure.py
    python storyworlds/worlds/gpt-5.4/grained_mystery_to_solve_friendship_teamwork_adventure.py --setting cove --item compass
    python storyworlds/worlds/gpt-5.4/grained_mystery_to_solve_friendship_teamwork_adventure.py --spot boathouse_rafters --method throw_stones
    python storyworlds/worlds/gpt-5.4/grained_mystery_to_solve_friendship_teamwork_adventure.py --all
    python storyworlds/worlds/gpt-5.4/grained_mystery_to_solve_friendship_teamwork_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/grained_mystery_to_solve_friendship_teamwork_adventure.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "counselor"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "counselor":
            return "counselor"
        return self.type
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
    opening: str
    trail_name: str
    surface: str
    affords_culprits: set[str] = field(default_factory=set)
    affords_spots: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    use: str
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
class Culprit:
    id: str
    label: str
    phrase: str
    likes: set[str] = field(default_factory=set)
    clue: str = ""
    spots: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    line: str
    infer: str
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
class Spot:
    id: str
    label: str
    phrase: str
    difficulty: int
    reach_text: str
    ending_image: str
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
class Method:
    id: str
    label: str
    sense: int
    power: int
    needs_teamwork: bool
    success: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "setting": setting,
            "noticed_names": [],
            "shared_names": [],
            "teamwork_ready": False,
            "predicted_success": False,
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "friend"]

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


def _r_missing(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("missing", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guide = world.get("guide")
    guide.memes["worry"] += 1
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    return []


def _r_teamwork(world: World) -> list[str]:
    if len(world.facts.get("shared_names", [])) < 2:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["teamwork"] += 1
        kid.memes["trust"] += 1
    world.facts["teamwork_ready"] = True
    return []


def _r_recovered(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["recovered"] < THRESHOLD:
        return []
    sig = ("recovered", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guide = world.get("guide")
    guide.memes["relief"] += 1
    guide.memes["worry"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing", tag="social", apply=_r_missing),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="recovered", tag="social", apply=_r_recovered),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def item_matches_culprit(item: MissingItem, culprit: Culprit) -> bool:
    return bool(item.tags & culprit.likes)


def clue_matches_culprit(clue: Clue, culprit: Culprit) -> bool:
    return clue.id == culprit.clue


def spot_matches_culprit(spot: Spot, culprit: Culprit) -> bool:
    return spot.id in culprit.spots


def setting_supports(setting: Setting, culprit: Culprit, spot: Spot) -> bool:
    return culprit.id in setting.affords_culprits and spot.id in setting.affords_spots


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                for clue_id, clue in CLUES.items():
                    for spot_id, spot in SPOTS.items():
                        if (
                            setting_supports(setting, culprit, spot)
                            and item_matches_culprit(item, culprit)
                            and clue_matches_culprit(clue, culprit)
                            and spot_matches_culprit(spot, culprit)
                        ):
                            combos.append((setting_id, item_id, culprit_id, clue_id, spot_id))
    return combos


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    spot = SPOTS[params.spot]
    return "team_solved" if method.power >= spot.difficulty else "guide_helped"


def explain_combo_rejection(setting: Optional[Setting], item: Optional[MissingItem],
                            culprit: Optional[Culprit], clue: Optional[Clue],
                            spot: Optional[Spot]) -> str:
    if setting and culprit and culprit.id not in setting.affords_culprits:
        return (f"(No story: {culprit.label} would not fit {setting.place}, so the mystery "
                f"has the wrong animal for that place.)")
    if setting and spot and spot.id not in setting.affords_spots:
        return (f"(No story: {spot.label} is not a believable hiding place in {setting.place}.)")
    if item and culprit and not item_matches_culprit(item, culprit):
        return (f"(No story: {culprit.label} would not be tempted by {item.phrase}, "
                f"so there is no honest mystery there.)")
    if clue and culprit and not clue_matches_culprit(clue, culprit):
        return (f"(No story: {clue.label} is not the kind of clue a {culprit.label} would leave.)")
    if spot and culprit and not spot_matches_culprit(spot, culprit):
        return (f"(No story: a {culprit.label} would not stash things in {spot.label}.)")
    return "(No story: the requested mystery pieces do not fit together.)"


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (f"(Refusing method '{method_id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try a safer teamwork method such as {better}.)")


def predict_retrieval(method: Method, spot: Spot) -> bool:
    return method.power >= spot.difficulty


def introduce(world: World, a: Entity, b: Entity, guide: Entity, item: MissingItem) -> None:
    setting = world.setting
    world.say(
        f"{a.id} and {b.id} were camp friends who liked making every walk feel like an expedition. "
        f"That morning they hurried to {setting.place} for the {setting.trail_name}."
    )
    world.say(
        f"{setting.opening} On the grained wooden table by the trail sign, "
        f"{guide.label_word} Mae had meant to leave {item.phrase}."
    )


def discover_loss(world: World, guide: Entity, item_ent: Entity, item: MissingItem) -> None:
    item_ent.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the place where it should have been was empty. "
        f'"Oh dear," Counselor Mae said. "We need {item.phrase} because {item.use}."'
    )
    world.say("At once, the walk turned into a mystery to solve.")


def first_search(world: World, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["searching"] += 1
    world.say(
        f"{a.id} looked high. {b.id} looked low. Instead of blaming each other, they knelt together "
        f"and searched the ground near the trail sign."
    )


def notice_clue(world: World, kid: Entity, clue: Clue, setting: Setting) -> None:
    kid.memes["noticed"] += 1
    world.facts["noticed_names"].append(kid.id)
    world.say(
        f"{kid.id} pointed first. {clue.line} in {setting.surface}."
    )


def share_idea(world: World, kid: Entity, speech: str) -> None:
    kid.memes["shared"] += 1
    world.facts["shared_names"].append(kid.id)
    propagate(world, narrate=False)
    world.say(f'{kid.id} said, "{speech}"')


def infer_culprit(world: World, culprit: Culprit, clue: Clue) -> None:
    world.facts["culprit_inferred"] = culprit.id
    world.say(
        f"They thought about the clue together. {clue.infer} "
        f'"Then it must have been {culprit.phrase}," they said.'
    )


def follow_trail(world: World, a: Entity, b: Entity, spot: Spot) -> None:
    for kid in (a, b):
        kid.memes["hope"] += 1
    world.say(
        f"Side by side, they followed the little signs until they reached {spot.phrase}. "
        f"{spot.reach_text}"
    )


def attempt_retrieval(world: World, a: Entity, b: Entity, method: Method,
                      spot: Spot, item_ent: Entity, item: MissingItem) -> None:
    world.facts["predicted_success"] = predict_retrieval(method, spot)
    if method.needs_teamwork:
        a.memes["team_plan"] += 1
        b.memes["team_plan"] += 1
    if method.power >= spot.difficulty:
        item_ent.meters["recovered"] += 1
        item_ent.meters["hidden"] = 0.0
        propagate(world, narrate=False)
        world.say(
            f"{a.id} and {b.id} used {method.label}. {method.success} "
            f"Soon {item.phrase} was safely back in {a.pronoun('possessive')} hands."
        )
    else:
        world.say(
            f"{a.id} and {b.id} tried {method.label}. {method.fail}"
        )


def guide_finishes(world: World, guide: Entity, item_ent: Entity, item: MissingItem,
                   method: Method) -> None:
    guide.memes["helpfulness"] += 1
    item_ent.meters["recovered"] += 1
    item_ent.meters["hidden"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Counselor Mae had been right behind them. {guide.pronoun().capitalize()} smiled and helped with the last careful reach, "
        f"because the children had already solved the mystery even if {method.label} was not quite enough."
    )
    world.say(
        f'When {guide.pronoun()} handed {item.phrase} back, {a_or_b(world)} both laughed with relief.'
    )


def a_or_b(world: World) -> str:
    kids = world.kids()
    if len(kids) != 2:
        return "the children"
    return f"{kids[0].id} and {kids[1].id}"


def launch_adventure(world: World, a: Entity, b: Entity, guide: Entity,
                     item: MissingItem, spot: Spot) -> None:
    for kid in (a, b):
        kid.memes["adventure"] += 1
    world.say(
        f'Counselor Mae tucked {item.phrase} into the pack again. "Ready for the trail now?" '
        f'{guide.pronoun()} asked.'
    )
    world.say(
        f'"Ready!" shouted {a.id} and {b.id}. They set off at once, and {spot.ending_image}'
    )


def tell(setting: Setting, item: MissingItem, culprit: Culprit, clue: Clue, spot: Spot,
         method: Method, friend1: str = "Nora", gender1: str = "girl",
         friend2: str = "Eli", gender2: str = "boy") -> World:
    world = World(setting)
    a = world.add(Entity(id=friend1, kind="character", type=gender1, role="friend",
                         traits=["brave", "kind"], attrs={"friend": friend2}))
    b = world.add(Entity(id=friend2, kind="character", type=gender2, role="friend",
                         traits=["careful", "loyal"], attrs={"friend": friend1}))
    guide = world.add(Entity(id="Mae", kind="character", type="counselor", role="guide",
                             label="the counselor"))
    item_ent = world.add(Entity(id="item", type="item", label=item.label, tags=set(item.tags)))
    world.add(Entity(id="spot", type="spot", label=spot.label, tags=set(spot.tags)))
    world.add(Entity(id="clue", type="clue", label=clue.label, tags=set(clue.tags)))

    introduce(world, a, b, guide, item)
    discover_loss(world, guide, item_ent, item)

    world.para()
    first_search(world, a, b)
    notice_clue(world, a, clue, setting)
    share_idea(world, a, "Something carried it away, not a person.")
    share_idea(world, b, clue.infer)
    infer_culprit(world, culprit, clue)

    world.para()
    follow_trail(world, a, b, spot)
    attempt_retrieval(world, a, b, method, spot, item_ent, item)
    if item_ent.meters["recovered"] < THRESHOLD:
        guide_finishes(world, guide, item_ent, item, method)

    world.para()
    launch_adventure(world, a, b, guide, item, spot)

    world.facts.update(
        friend1=a,
        friend2=b,
        guide=guide,
        item_cfg=item,
        culprit=culprit,
        clue_cfg=clue,
        spot_cfg=spot,
        method=method,
        recovered=item_ent.meters["recovered"] >= THRESHOLD,
        outcome="team_solved" if method.power >= spot.difficulty else "guide_helped",
    )
    return world


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="the cove trailhead",
        opening="A pale breeze came in from the water, and the dock ropes clicked softly against the posts.",
        trail_name="Shell Cove Quest",
        surface="the fine sand by the planks",
        affords_culprits={"gull"},
        affords_spots={"driftwood_hollow", "boathouse_rafters"},
        tags={"beach", "adventure"},
    ),
    "pine_trail": Setting(
        id="pine_trail",
        place="the pine trail gate",
        opening="Tall pines made green shadows, and the morning smelled like bark and warm needles.",
        trail_name="Whispering Pine Loop",
        surface="the soft dirt under the needles",
        affords_culprits={"squirrel"},
        affords_spots={"tree_fork", "root_hollow"},
        tags={"forest", "adventure"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the meadow path",
        opening="The grass bent in shiny waves, and little white clouds sailed over the hill.",
        trail_name="Sky Meadow Hunt",
        surface="the dusty path between the grasses",
        affords_culprits={"goat"},
        affords_spots={"berry_bush_gap"},
        tags={"field", "adventure"},
    ),
}

ITEMS = {
    "compass": MissingItem(
        id="compass",
        label="compass",
        phrase="the brass compass",
        use="it points the way at each fork",
        tags={"shiny", "metal"},
    ),
    "map": MissingItem(
        id="map",
        label="trail map",
        phrase="the rolled trail map",
        use="it shows where the secret marker stones are hidden",
        tags={"paper", "rolled"},
    ),
    "pennant": MissingItem(
        id="pennant",
        label="camp pennant",
        phrase="the red camp pennant",
        use="the first team is supposed to carry it like a flag",
        tags={"cloth", "fluttery"},
    ),
}

CULPRITS = {
    "gull": Culprit(
        id="gull",
        label="gull",
        phrase="a nosy gull",
        likes={"shiny", "paper"},
        clue="feather",
        spots={"driftwood_hollow", "boathouse_rafters"},
        tags={"bird", "beach"},
    ),
    "squirrel": Culprit(
        id="squirrel",
        label="squirrel",
        phrase="a busy squirrel",
        likes={"paper", "cloth"},
        clue="pinecone_bits",
        spots={"tree_fork", "root_hollow"},
        tags={"forest", "animal"},
    ),
    "goat": Culprit(
        id="goat",
        label="goat",
        phrase="the little camp goat",
        likes={"cloth"},
        clue="chew_marks",
        spots={"berry_bush_gap"},
        tags={"farm", "animal"},
    ),
}

CLUES = {
    "feather": Clue(
        id="feather",
        label="a white feather",
        line="A white feather lay there, and tiny bird tracks stitched a crooked trail",
        infer="Bird feet and a feather meant the thief had wings.",
        tags={"feather", "tracks"},
    ),
    "pinecone_bits": Clue(
        id="pinecone_bits",
        label="pinecone bits",
        line="Little pinecone crumbs were scattered there, with quick scratchy prints between them",
        infer="Only a squirrel would leave crumbs like that and dart away so fast.",
        tags={"pinecone", "prints"},
    ),
    "chew_marks": Clue(
        id="chew_marks",
        label="chew marks",
        line="Fresh nibbled edges showed on a strap, and boxy hoofprints pressed the dust nearby",
        infer="Hoofprints and nibble marks pointed to the camp goat.",
        tags={"hooves", "teeth"},
    ),
}

SPOTS = {
    "driftwood_hollow": Spot(
        id="driftwood_hollow",
        label="a driftwood hollow",
        phrase="a driftwood hollow beside the shore",
        difficulty=1,
        reach_text="Inside, something red-gold glimmered between two weathered boards.",
        ending_image="the sea flashed beside them while the recovered item bounced happily in the pack.",
        tags={"driftwood", "shore"},
    ),
    "boathouse_rafters": Spot(
        id="boathouse_rafters",
        label="the boathouse rafters",
        phrase="the boathouse rafters above the door",
        difficulty=3,
        reach_text="Up near the beams, a stolen treasure peeked out from a nest of rope ends.",
        ending_image="their footsteps drummed over the dock while gulls wheeled above the water.",
        tags={"boathouse", "high"},
    ),
    "tree_fork": Spot(
        id="tree_fork",
        label="a tree fork",
        phrase="a crook high in an old pine",
        difficulty=2,
        reach_text="Tucked in the fork was the missing thing, caught between bark and twigs.",
        ending_image="sunlight blinked through the pines as the map led them deeper along the trail.",
        tags={"tree", "high"},
    ),
    "root_hollow": Spot(
        id="root_hollow",
        label="a root hollow",
        phrase="a root hollow under a bent pine",
        difficulty=1,
        reach_text="Just inside the hollow, the missing thing waited under a fan of dry needles.",
        ending_image="their boots crunched over needles while the forest opened ahead like a secret gate.",
        tags={"roots", "ground"},
    ),
    "berry_bush_gap": Spot(
        id="berry_bush_gap",
        label="a berry-bush gap",
        phrase="a narrow gap under a berry bush",
        difficulty=2,
        reach_text="There, beyond the thorny branches, the red cloth had snagged and fluttered.",
        ending_image="the hill path curled ahead, and the rescued pennant snapped brightly in the breeze.",
        tags={"bush", "thorny"},
    ),
}

METHODS = {
    "shoulder_boost": Method(
        id="shoulder_boost",
        label="a shoulder boost",
        sense=3,
        power=2,
        needs_teamwork=True,
        success="One friend steadied the other, and together they reached just far enough.",
        fail="They stretched hard, but the hiding place was still a little too high.",
        qa_text="They used a shoulder boost so one child could reach while the other kept things steady.",
        tags={"teamwork", "balance"},
    ),
    "branch_hook": Method(
        id="branch_hook",
        label="a long branch hook",
        sense=3,
        power=3,
        needs_teamwork=True,
        success="One child held the branch low while the other guided the tip, and they hooked the item free.",
        fail="They nudged at it, but it stayed wedged where it was.",
        qa_text="They worked together with a long branch to hook the item loose.",
        tags={"teamwork", "tool"},
    ),
    "crawl_together": Method(
        id="crawl_together",
        label="careful crawling together",
        sense=2,
        power=1,
        needs_teamwork=True,
        success="One held branches back while the other crawled in and pulled the item out.",
        fail="They got close, but the hiding place still kept the item out of reach.",
        qa_text="They crawled carefully together, with one child making space for the other.",
        tags={"teamwork", "careful"},
    ),
    "throw_stones": Method(
        id="throw_stones",
        label="throwing stones up at it",
        sense=1,
        power=1,
        needs_teamwork=False,
        success="By sheer luck the item dropped free, though it was not a wise plan.",
        fail="The stones only clacked nearby, and the item stayed put.",
        qa_text="They threw stones at the hiding place.",
        tags={"unsafe"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    item: str
    culprit: str
    clue: str
    spot: str
    method: str
    friend1: str
    gender1: str
    friend2: str
    gender2: str
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


KNOWLEDGE = {
    "compass": [
        ("What does a compass do?",
         "A compass helps people know direction. Its needle points north, which helps travelers choose the right way.")
    ],
    "map": [
        ("What does a trail map show?",
         "A trail map shows paths and landmarks. It helps walkers know where they are going.")
    ],
    "pennant": [
        ("What is a pennant?",
         "A pennant is a small flag. Teams carry one to show their group or mark the front of a walk.")
    ],
    "gull": [
        ("Why might a gull grab something at the shore?",
         "Gulls are curious birds and often swoop at things that look shiny or easy to snatch. At the shore, they are always watching for interesting bits.")
    ],
    "squirrel": [
        ("Why do squirrels hide things?",
         "Squirrels like to gather and tuck things into safe places. They are quick climbers, so they often hide things in trees or near roots.")
    ],
    "goat": [
        ("Why does a goat nibble cloth or straps?",
         "Goats explore with their mouths and may nibble strange things they find. That is why loose cloth and straps should be kept out of their reach.")
    ],
    "feather": [
        ("What can a feather tell you in a mystery?",
         "A feather can be a clue that a bird was nearby. Clues help people infer what happened without seeing it happen.")
    ],
    "pinecone_bits": [
        ("Why are pinecone bits a clue in the woods?",
         "Pinecone bits show that a forest animal may have been eating or carrying something there. Small clues can point toward the right animal.")
    ],
    "chew_marks": [
        ("What are chew marks?",
         "Chew marks are little bite signs left by teeth. They can help you guess what animal touched an object.")
    ],
    "branch_hook": [
        ("Why can a long branch help reach something safely?",
         "A long branch gives extra reach. If used carefully, it can move an item without making someone climb too high.")
    ],
    "shoulder_boost": [
        ("What makes a shoulder boost work?",
         "A shoulder boost works when one person stays steady and the other moves carefully. It takes trust and teamwork.")
    ],
    "crawl_together": [
        ("Why is teamwork useful in a tight hiding place?",
         "Teamwork lets one child hold things back while the other reaches in. Sharing jobs makes a tricky problem easier to solve.")
    ],
}
KNOWLEDGE_ORDER = [
    "compass", "map", "pennant",
    "gull", "squirrel", "goat",
    "feather", "pinecone_bits", "chew_marks",
    "branch_hook", "shoulder_boost", "crawl_together",
]

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Eli", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


CURATED = [
    StoryParams(
        setting="cove",
        item="compass",
        culprit="gull",
        clue="feather",
        spot="driftwood_hollow",
        method="crawl_together",
        friend1="Nora",
        gender1="girl",
        friend2="Eli",
        gender2="boy",
    ),
    StoryParams(
        setting="pine_trail",
        item="map",
        culprit="squirrel",
        clue="pinecone_bits",
        spot="tree_fork",
        method="shoulder_boost",
        friend1="Mia",
        gender1="girl",
        friend2="Ben",
        gender2="boy",
    ),
    StoryParams(
        setting="meadow",
        item="pennant",
        culprit="goat",
        clue="chew_marks",
        spot="berry_bush_gap",
        method="shoulder_boost",
        friend1="Ava",
        gender1="girl",
        friend2="Finn",
        gender2="boy",
    ),
    StoryParams(
        setting="cove",
        item="map",
        culprit="gull",
        clue="feather",
        spot="boathouse_rafters",
        method="branch_hook",
        friend1="Lucy",
        gender1="girl",
        friend2="Max",
        gender2="boy",
    ),
    StoryParams(
        setting="cove",
        item="map",
        culprit="gull",
        clue="feather",
        spot="boathouse_rafters",
        method="shoulder_boost",
        friend1="Anna",
        gender1="girl",
        friend2="Leo",
        gender2="boy",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    item = f["item_cfg"]
    culprit = f["culprit"]
    clue = f["clue_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    if outcome == "team_solved":
        return [
            f'Write an adventure story for a 3-to-5-year-old in which two camp friends solve a mystery and recover {item.phrase}. Include the word "grained".',
            f"Tell a friendship-and-teamwork mystery where {a.id} and {b.id} follow {clue.label} to {spot.label} and get {item.phrase} back from {culprit.phrase}.",
            f"Write a gentle adventure where a missing object delays a trail walk, but two friends work together to solve the puzzle and save the day.",
        ]
    return [
        f'Write an adventure story for a 3-to-5-year-old in which two camp friends solve a mystery, but a grown-up helps with the very last reach. Include the word "grained".',
        f"Tell a teamwork mystery where {a.id} and {b.id} correctly follow {clue.label} to {spot.label}, yet still need Counselor Mae's careful help to recover {item.phrase}.",
        f"Write a story about friendship and problem-solving where the children crack the case themselves even though the hiding place is too hard to reach alone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    item = f["item_cfg"]
    culprit = f["culprit"]
    clue = f["clue_cfg"]
    spot = f["spot_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two camp friends, {a.id} and {b.id}, and Counselor Mae. The friends wanted to go on an adventure trail, but first they had to solve a mystery."
        ),
        (
            f"What was missing?",
            f"{item.phrase.capitalize()} was missing from the table at the trail sign. That mattered because {item.use}."
        ),
        (
            "What clue did the children find?",
            f"They found {clue.label}. The clue mattered because {clue.infer.lower()}"
        ),
        (
            f"How did {a.id} and {b.id} show teamwork?",
            f"They searched together, shared their ideas, and followed the clue side by side. The mystery became easier because each child added part of the answer."
        ),
    ]
    if outcome == "team_solved":
        qa.append((
            f"How did they get the missing item back?",
            f"They found it at {spot.label} and used {method.qa_text} That worked because the method was strong enough for that hiding place."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the trail walk beginning at last. The children set off proudly because they had solved the mystery themselves."
        ))
    else:
        qa.append((
            f"Did the children solve the mystery even though they needed help at the end?",
            f"Yes. They correctly followed the clue to {spot.label} and figured out what had happened. Counselor Mae only helped with the last hard reach after the children had already solved the case."
        ))
        qa.append((
            "How did the story end?",
            f"It still ended happily, with the missing item returned and the adventure beginning. The friends learned that solving a mystery and asking for help can both be part of good teamwork."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {f["item_cfg"].id, f["culprit"].id, f["clue_cfg"].id, f["method"].id}
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} teamwork_ready={world.facts.get('teamwork_ready')}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, C, Cl, Sp) :-
    setting(S), item(I), culprit(C), clue(Cl), spot(Sp),
    affords_culprit(S, C), affords_spot(S, Sp),
    item_tag(I, T), likes(C, T),
    leaves(C, Cl), hides(C, Sp).

sensible(M) :-
    method(M), sense(M, Sc), sense_min(Min), Sc >= Min.

team_solved :-
    chosen_method(M), power(M, P),
    chosen_spot(Sp), difficulty(Sp, D),
    P >= D.

guide_helped :-
    chosen_method(M), power(M, P),
    chosen_spot(Sp), difficulty(Sp, D),
    P < D.

outcome(team_solved) :- team_solved.
outcome(guide_helped) :- guide_helped.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cid in sorted(setting.affords_culprits):
            lines.append(asp.fact("affords_culprit", sid, cid))
        for sp in sorted(setting.affords_spots):
            lines.append(asp.fact("affords_spot", sid, sp))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("likes", cid, tag))
        lines.append(asp.fact("leaves", cid, culprit.clue))
        for sp in sorted(culprit.spots):
            lines.append(asp.fact("hides", cid, sp))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("difficulty", sid, spot.difficulty))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_spot", params.spot),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: story text was empty.")
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
    rendered = buf.getvalue()
    if "smoke" not in rendered or not sample.world_qa:
        raise StoryError("Smoke test failed: emit/QA did not produce expected output.")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible_methods())
    if py_sens == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_sens)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure during verify at seed {seed}.")
            break
    diffs = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not diffs:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(diffs)}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: camp friends solve a little mystery through friendship and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--friend1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--friend2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    item = ITEMS.get(args.item) if args.item else None
    culprit = CULPRITS.get(args.culprit) if args.culprit else None
    clue = CLUES.get(args.clue) if args.clue else None
    spot = SPOTS.get(args.spot) if args.spot else None

    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))

    explicit_all = all(x is not None for x in (setting, item, culprit, clue, spot))
    if explicit_all:
        combo = (args.setting, args.item, args.culprit, args.clue, args.spot)
        if combo not in valid_combos():
            raise StoryError(explain_combo_rejection(setting, item, culprit, clue, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.clue is None or combo[3] == args.clue)
        and (args.spot is None or combo[4] == args.spot)
    ]
    if not combos:
        raise StoryError(explain_combo_rejection(setting, item, culprit, clue, spot))

    chosen = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    name_pool1 = GIRL_NAMES if gender1 == "girl" else BOY_NAMES
    friend1 = args.friend1 or rng.choice(name_pool1)

    gender2 = args.gender2 or rng.choice(["girl", "boy"])
    name_pool2 = [n for n in (GIRL_NAMES if gender2 == "girl" else BOY_NAMES) if n != friend1]
    if not name_pool2:
        name_pool2 = GIRL_NAMES if gender2 == "girl" else BOY_NAMES
    friend2 = args.friend2 or rng.choice(name_pool2)
    if friend2 == friend1:
        alts = [n for n in name_pool2 if n != friend1]
        friend2 = rng.choice(alts) if alts else (friend1 + " Jr")

    return StoryParams(
        setting=chosen[0],
        item=chosen[1],
        culprit=chosen[2],
        clue=chosen[3],
        spot=chosen[4],
        method=method_id,
        friend1=friend1,
        gender1=gender1,
        friend2=friend2,
        gender2=gender2,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.item not in ITEMS:
        raise StoryError(f"Unknown item: {params.item}")
    if params.culprit not in CULPRITS:
        raise StoryError(f"Unknown culprit: {params.culprit}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.spot not in SPOTS:
        raise StoryError(f"Unknown spot: {params.spot}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")
    combo = (params.setting, params.item, params.culprit, params.clue, params.spot)
    if combo not in valid_combos():
        raise StoryError(explain_combo_rejection(
            SETTINGS[params.setting], ITEMS[params.item], CULPRITS[params.culprit],
            CLUES[params.clue], SPOTS[params.spot]
        ))
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))

    world = tell(
        setting=SETTINGS[params.setting],
        item=ITEMS[params.item],
        culprit=CULPRITS[params.culprit],
        clue=CLUES[params.clue],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
        friend1=params.friend1,
        gender1=params.gender1,
        friend2=params.friend2,
        gender2=params.gender2,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible_methods()
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (setting, item, culprit, clue, spot) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = (
                f"### {p.friend1} & {p.friend2}: {p.item} at {p.setting} "
                f"({p.culprit}, {p.spot}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
