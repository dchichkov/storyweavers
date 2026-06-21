#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/leisure_prepare_mystery_to_solve_flashback_friendship.py
===================================================================================

A standalone story world about two friends spending their leisure time turning an
ordinary place into a tiny space station. While they prepare for a pretend
mission, an important object goes missing. The loss becomes a small mystery to
solve, a flashback reveals what really happened, and friendship helps the
children repair a wobbly moment and finish together.

Run it
------
    python storyworlds/worlds/gpt-5.4/leisure_prepare_mystery_to_solve_flashback_friendship.py
    python storyworlds/worlds/gpt-5.4/leisure_prepare_mystery_to_solve_flashback_friendship.py --mission comet_watch --item star_map
    python storyworlds/worlds/gpt-5.4/leisure_prepare_mystery_to_solve_flashback_friendship.py --location between_books
    python storyworlds/worlds/gpt-5.4/leisure_prepare_mystery_to_solve_flashback_friendship.py --all
    python storyworlds/worlds/gpt-5.4/leisure_prepare_mystery_to_solve_flashback_friendship.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/leisure_prepare_mystery_to_solve_flashback_friendship.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = True
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
# Registry types
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mission:
    id: str
    scene: str
    place_noun: str
    goal: str
    prep_line: str
    launch_line: str
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
    short: str
    shape: str
    use_text: str
    flashback_action: str
    ending_hold: str
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
class Location:
    id: str
    label: str
    phrase: str
    fit_shapes: set[str]
    found_line: str
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
class Decor:
    id: str
    setup: str
    remembered_move: str
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
# Rules
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


def _r_missing_stirs_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.attrs.get("where") != "lost":
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("lead", "friend"):
        world.get(eid).memes["worry"] += 1
    return ["__missing__"]


def _r_blame_hurts(world: World) -> list[str]:
    if world.facts.get("blame_spoken", 0) < THRESHOLD:
        return []
    sig = ("blame_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("friend").memes["hurt"] += 1
    world.get("lead").memes["guilt_seed"] += 1
    return ["__hurt__"]


def _r_flashback_gives_clue(world: World) -> list[str]:
    if world.facts.get("flashback_seen", 0) < THRESHOLD:
        return []
    item = world.get("item")
    if item.attrs.get("where") != "lost":
        return []
    sig = ("flashback_clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["clue_ready"] = 1.0
    for eid in ("lead", "friend"):
        world.get(eid).memes["hope"] += 1
    return ["__clue__"]


def _r_found_repairs(world: World) -> list[str]:
    item = world.get("item")
    if item.attrs.get("where") == "lost":
        return []
    sig = ("found_repairs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("lead", "friend"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["joy"] += 1
    if world.facts.get("blame_spoken", 0) >= THRESHOLD:
        world.get("lead").memes["guilt"] += 1
        world.get("friend").memes["forgiven"] += 1
    world.get("lead").memes["trust"] += 1
    world.get("friend").memes["trust"] += 1
    return ["__repaired__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_stirs_worry),
    Rule(name="blame_hurts", tag="social", apply=_r_blame_hurts),
    Rule(name="flashback_clue", tag="memory", apply=_r_flashback_gives_clue),
    Rule(name="found_repairs", tag="social", apply=_r_found_repairs),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints and outcome model
# ---------------------------------------------------------------------------
def location_fits(item: MissingItem, location: Location) -> bool:
    return item.shape in location.fit_shapes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for item_id, item in ITEMS.items():
            for location_id, location in LOCATIONS.items():
                if not location_fits(item, location):
                    continue
                for decor_id in DECORS:
                    combos.append((mission_id, item_id, location_id, decor_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "repair" if params.trust_level <= 4 else "smooth"


def explain_rejection(item: MissingItem, location: Location) -> str:
    return (
        f"(No story: {item.phrase} is the wrong shape for {location.phrase}. "
        f"This world only hides objects in places where they could reasonably fit.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_search(world: World, location_id: str) -> dict:
    sim = world.copy()
    sim.facts["flashback_seen"] = 1.0
    propagate(sim, narrate=False)
    if sim.facts.get("clue_ready", 0) >= THRESHOLD:
        sim.get("item").attrs["where"] = location_id
        propagate(sim, narrate=False)
    return {
        "finds_item": sim.get("item").attrs.get("where") != "lost",
        "trust_after": sim.get("lead").memes["trust"] + sim.get("friend").memes["trust"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, lead: Entity, friend: Entity, mission: Mission, decor: Decor, parent: Entity) -> None:
    for kid in (lead, friend):
        kid.memes["joy"] += 1
        kid.memes["trust"] = float(world.facts["trust_level"])
    world.say(
        f"On a bright afternoon of leisure, {lead.id} and {friend.id} hurried to "
        f"{world.facts['setting_phrase']} and turned it into {mission.scene}."
    )
    world.say(decor.setup)
    world.say(
        f"They wanted to prepare for {mission.goal}, and even {lead.id}'s "
        f"{parent.label_word} smiled at the paper stars and blanket control panels."
    )


def show_item_need(world: World, lead: Entity, friend: Entity, item: MissingItem, mission: Mission) -> None:
    world.say(
        f'"Ready for launch?" {lead.id} asked. "{item.short.capitalize()} first," '
        f"{friend.id} said. {item.use_text}."
    )
    world.say(mission.prep_line)


def discover_missing(world: World, lead: Entity, friend: Entity, item: MissingItem) -> None:
    world.get("item").attrs["where"] = "lost"
    propagate(world, narrate=False)
    world.say(
        f"But when {lead.id} reached for {item.phrase}, it was not on the crate-table "
        f"where the friends had left it."
    )
    world.say(
        f"They looked under the silver scarf, behind the cardboard console, and inside the snack tin. "
        f"The little space station suddenly felt still."
    )


def blame_or_hold(world: World, lead: Entity, friend: Entity, outcome: str, item: MissingItem) -> None:
    if outcome == "repair":
        world.facts["blame_spoken"] = 1.0
        propagate(world, narrate=False)
        world.say(
            f'"Did you move {item.short}?" {lead.id} blurted. The words came out sharper '
            f"than {lead.pronoun()} meant them to."
        )
        world.say(
            f"{friend.id}'s shoulders dropped. "
            f'"I was helping, not hiding it," {friend.pronoun()} said quietly.'
        )
    else:
        world.say(
            f'{lead.id} frowned but took a slow breath. "This is a mystery to solve," '
            f'{lead.pronoun()} said. "Let\'s think before we guess."'
        )
        world.say(
            f"{friend.id} nodded and stayed close beside {lead.pronoun('object')}."
        )


def flashback(world: World, lead: Entity, friend: Entity, item: MissingItem, decor: Decor) -> None:
    world.facts["flashback_seen"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id} blinked and pressed a hand to {friend.pronoun('possessive')} forehead. "
        f'"Wait," {friend.pronoun()} whispered. "I remember something."'
    )
    world.say(
        f"In a quick flashback, {friend.id} remembered {decor.remembered_move} "
        f"so it would not get bent while they worked. {item.flashback_action}."
    )


def search_and_find(world: World, lead: Entity, friend: Entity, item: MissingItem, location: Location) -> None:
    prediction = predict_search(world, location.id)
    if not prediction["finds_item"]:
        raise StoryError("(Internal story error: the flashback failed to lead to the item.)")
    world.say(
        f'"If that memory is right," {lead.id} said, "we should check {location.phrase}."'
    )
    world.get("item").attrs["where"] = location.id
    propagate(world, narrate=False)
    world.say(location.found_line.replace("{item}", item.short))
    world.say(
        f"{lead.id} lifted it high as if it were a tiny moon coming out from behind a cloud."
    )


def repair_friendship(world: World, lead: Entity, friend: Entity, outcome: str) -> None:
    if outcome == "repair":
        world.say(
            f'{lead.id} looked at {friend.id} and swallowed. "I am sorry I blamed you," '
            f'{lead.pronoun()} said. "I was worried and I forgot we are a team."'
        )
        world.say(
            f'{friend.id} gave a small smile. "We solved it together," {friend.pronoun()} said, '
            f'and the sore feeling melted away.'
        )
    else:
        world.say(
            f"The two friends bumped shoulders and grinned. Solving the mystery together "
            f"made the station feel even more real."
        )


def launch(world: World, lead: Entity, friend: Entity, mission: Mission, item: MissingItem, parent: Entity) -> None:
    for kid in (lead, friend):
        kid.memes["friendship"] += 1
        kid.memes["wonder"] += 1
    world.say(
        mission.launch_line.replace("{lead}", lead.id).replace("{friend}", friend.id).replace("{item}", item.ending_hold)
    )
    world.say(
        f"{parent.label_word.capitalize()} dimmed the lamp for one minute, and stars from the window "
        f"glimmered on the blanket roof."
    )
    world.say(
        f"With {item.ending_hold} safe again, the friends counted down together and flew into their game "
        f"side by side, brave, busy, and glad they had trusted their friendship."
    )


def tell(
    mission: Mission,
    item_cfg: MissingItem,
    location_cfg: Location,
    decor_cfg: Decor,
    *,
    lead_name: str = "Nova",
    lead_gender: str = "girl",
    friend_name: str = "Jet",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    trust_level: int = 5,
) -> World:
    world = World()
    world.facts["setting_phrase"] = "the attic corner by the round window"
    world.facts["trust_level"] = trust_level
    world.facts["blame_spoken"] = 0.0
    world.facts["flashback_seen"] = 0.0
    world.facts["clue_ready"] = 0.0

    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        label=lead_name,
        traits=["eager"],
        attrs={"friend": friend_name},
        tags={"friendship"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        label=friend_name,
        traits=["helpful"],
        attrs={"friend": lead_name},
        tags={"friendship"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        portable=False,
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="mission_item",
        label=item_cfg.label,
        attrs={"where": "crate"},
        tags=set(item_cfg.tags),
    ))

    outcome = "repair" if trust_level <= 4 else "smooth"

    introduce(world, lead, friend, mission, decor_cfg, parent)
    show_item_need(world, lead, friend, item_cfg, mission)

    world.para()
    discover_missing(world, lead, friend, item_cfg)
    blame_or_hold(world, lead, friend, outcome, item_cfg)

    world.para()
    flashback(world, lead, friend, item_cfg, decor_cfg)
    search_and_find(world, lead, friend, item_cfg, location_cfg)
    repair_friendship(world, lead, friend, outcome)

    world.para()
    launch(world, lead, friend, mission, item_cfg, parent)

    world.facts.update(
        mission=mission,
        item_cfg=item_cfg,
        location_cfg=location_cfg,
        decor_cfg=decor_cfg,
        lead=lead,
        friend=friend,
        parent=parent,
        outcome=outcome,
        item_found=world.get("item").attrs.get("where") != "lost",
        final_location=world.get("item").attrs.get("where"),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
MISSIONS = {
    "comet_watch": Mission(
        id="comet_watch",
        scene="a silver comet station",
        place_noun="station",
        goal="their comet-watch mission",
        prep_line="They checked the pillow meteor shields and the tape-tube telescope one more time.",
        launch_line="{lead} spread the star blanket, {friend} aimed the cardboard telescope, and together they tucked {item} beside the launch button.",
        tags={"space", "stars"},
    ),
    "moon_mail": Mission(
        id="moon_mail",
        scene="a moon-mail rocket post",
        place_noun="rocket",
        goal="delivering moon-mail to the dark side of the moon",
        prep_line="They stacked tiny envelopes in a shoebox airlock and straightened the foil flag by the window.",
        launch_line="{lead} fed the mail chute, {friend} tapped the dashboard, and together they set {item} by the captain's seat.",
        tags={"space", "moon"},
    ),
    "ring_rescue": Mission(
        id="ring_rescue",
        scene="a ring-rescue shuttle",
        place_noun="shuttle",
        goal="saving a lost toy satellite near the shining rings",
        prep_line="They lined up cushion thrusters and tested the whooshing sound of the fan-made engine.",
        launch_line="{lead} held the rescue rope, {friend} watched the ring chart, and together they clipped {item} beside the pilot light.",
        tags={"space", "planets"},
    ),
}

ITEMS = {
    "star_map": MissingItem(
        id="star_map",
        label="star map",
        phrase="the folded star map",
        short="the star map",
        shape="flat",
        use_text="Without it, they could not tell which bright dot was their pretend comet.",
        flashback_action="The memory sparkled because the map had made a soft paper swish.",
        ending_hold="the folded star map",
        tags={"map", "stars"},
    ),
    "moon_key": MissingItem(
        id="moon_key",
        label="moon key",
        phrase="the moon key",
        short="the moon key",
        shape="small",
        use_text="Without it, the airlock box was only a box, not a moon-door.",
        flashback_action="The memory clinked in {friend_pos} mind like a tiny bell.",
        ending_hold="the moon key",
        tags={"key", "moon"},
    ),
    "signal_badge": MissingItem(
        id="signal_badge",
        label="signal badge",
        phrase="the shiny signal badge",
        short="the signal badge",
        shape="small",
        use_text="Without it, nobody looked quite ready to lead the pretend crew.",
        flashback_action="The memory flashed like foil catching sunlight.",
        ending_hold="the shiny signal badge",
        tags={"badge", "space"},
    ),
    "ring_chart": MissingItem(
        id="ring_chart",
        label="ring chart",
        phrase="the ring chart",
        short="the ring chart",
        shape="flat",
        use_text="Without it, they could not guide the shuttle safely through the paper rings.",
        flashback_action="The memory came back with the scrape of paper over cardboard.",
        ending_hold="the ring chart",
        tags={"chart", "planets"},
    ),
}

LOCATIONS = {
    "between_books": Location(
        id="between_books",
        label="between the atlas books",
        phrase="between the atlas books on the low shelf",
        fit_shapes={"flat"},
        found_line="There, peeking out between two tall books, was {item}.",
        tags={"bookshelf"},
    ),
    "inside_toolbox": Location(
        id="inside_toolbox",
        label="inside the red toolbox",
        phrase="inside the red toolbox by the wall",
        fit_shapes={"small"},
        found_line="Inside the red toolbox, under the safe scissors and string, lay {item}.",
        tags={"toolbox"},
    ),
    "under_cushion": Location(
        id="under_cushion",
        label="under the seat cushion",
        phrase="under the silver seat cushion",
        fit_shapes={"flat", "small"},
        found_line="{item} was tucked under the silver seat cushion, exactly where the memory had pointed.",
        tags={"cushion"},
    ),
    "tin_drawer": Location(
        id="tin_drawer",
        label="inside the little tin drawer",
        phrase="inside the little tin drawer under the crate-table",
        fit_shapes={"small"},
        found_line="The little tin drawer slid open with a ping, and there was {item}.",
        tags={"drawer"},
    ),
}

DECORS = {
    "foil_stars": Decor(
        id="foil_stars",
        setup="A blanket became the cabin roof, foil stars twinkled on the wall, and a cardboard box hummed as the control desk.",
        remembered_move="sliding a stack of foil stars aside and setting the mission gear somewhere safe",
        tags={"stars"},
    ),
    "meteor_pillows": Decor(
        id="meteor_pillows",
        setup="Round pillows became sleepy meteors, a laundry basket became the cargo pod, and a blue scarf drifted like a nebula.",
        remembered_move="clearing the meteor pillows from the floor and lifting the mission gear out of the way",
        tags={"meteors"},
    ),
    "rocket_tubes": Decor(
        id="rocket_tubes",
        setup="Tape tubes stood up like rocket pipes, a milk crate became the captain's table, and paper planets swung from string.",
        remembered_move="straightening the rocket tubes and moving the mission gear before one tube rolled onto it",
        tags={"rocket"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Skye", "Ayla", "Tessa", "Ivy", "Nora"]
BOY_NAMES = ["Jet", "Leo", "Orion", "Max", "Finn", "Theo", "Kai", "Milo"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mission: str
    item: str
    location: str
    decor: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trust_level: int = 6
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
    "stars": [
        (
            "What is a star map?",
            "A star map is a picture that helps you know where stars are in the sky. It is like a guide for looking up."
        )
    ],
    "moon": [
        (
            "What does a key do in pretend play?",
            "A pretend key can make a game feel real because it stands for opening something important. In stories, a key often means there is a problem to solve."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back at something that happened earlier. It helps readers understand the present problem."
        )
    ],
    "friendship": [
        (
            "What can good friends do when there is a misunderstanding?",
            "Good friends can stop, listen, and tell the truth kindly. Then they can fix the problem together."
        )
    ],
    "mystery": [
        (
            "What makes something a mystery to solve?",
            "A mystery is when you do not know an important answer yet. You look for clues, remember facts, and figure it out."
        )
    ],
    "bookshelf": [
        (
            "Why might a flat paper fit between books?",
            "A flat paper can slide into a narrow space more easily than a chunky object can. Its shape matches the gap."
        )
    ],
    "toolbox": [
        (
            "What is a toolbox for?",
            "A toolbox holds small tools and bits and pieces in one place. It helps people keep things tidy and easy to find."
        )
    ],
    "cushion": [
        (
            "Why do children sometimes check under a cushion for a lost thing?",
            "Small things can slip or get tucked under cushions while people are playing. A soft seat can hide an object from sight."
        )
    ],
    "drawer": [
        (
            "What is a drawer?",
            "A drawer is a small box-like space that slides in and out of furniture. People use drawers to keep things inside."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "mystery",
    "flashback",
    "friendship",
    "stars",
    "moon",
    "bookshelf",
    "toolbox",
    "cushion",
    "drawer",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    item = f["item_cfg"]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "leisure" and "prepare". The story should center on two friends and a missing object.',
        f"Tell a gentle story where two friends prepare for {mission.goal}, but {item.short} goes missing and becomes a mystery to solve through a flashback.",
        f"Write a child-friendly story with friendship, a small misunderstanding, and a happy ending where the children solve a space-themed mystery together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    parent = f["parent"]
    mission = f["mission"]
    item = f["item_cfg"]
    location = f["location_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {lead.id} and {friend.id}, who turned their play space into {mission.scene}. They were getting ready for a pretend mission while {lead.id}'s {parent.label_word} watched nearby."
        ),
        (
            f"Why did the missing {item.label} matter?",
            f"The missing {item.label} mattered because {item.use_text.lower()} That made the loss feel like a real problem inside their space adventure."
        ),
        (
            "What made the problem a mystery to solve?",
            f"The object had been there before, and then it was suddenly gone, so the children had to search for clues instead of guessing wildly. The story turns into a mystery because the answer is hidden until the flashback points them in the right direction."
        ),
        (
            "How did the flashback help?",
            f"The flashback helped {friend.id} remember moving the item earlier while they were setting up their pretend station. That memory gave them a real clue about checking {location.phrase}."
        ),
    ]
    if outcome == "repair":
        qa.append(
            (
                f"How did friendship help after {lead.id} said something hurtful?",
                f"At first, {lead.id} blurted out blame because the missing object made {lead.pronoun('object')} worried. After the item was found, {lead.pronoun()} apologized, and the friends chose to stay a team instead of staying upset."
            )
        )
    else:
        qa.append(
            (
                "How did the friends work together?",
                f"They stayed calm, treated the problem like a puzzle, and listened when {friend.id} remembered an earlier moment. Because they trusted each other, the clue could lead them straight to the answer."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the missing object safely found and the pretend mission ready at last. The final image shows the friends counting down together, which proves the mystery is solved and their friendship is strong."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mystery", "flashback", "friendship"}
    tags |= set(f["mission"].tags)
    tags |= set(f["location_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if attrs:
            parts.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v}' for k, v in sorted(world.facts.items()) if k in {'trust_level', 'blame_spoken', 'flashback_seen', 'clue_ready', 'outcome', 'final_location', 'item_found'})}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(I, L) :- item(I), location(L), shape(I, S), accepts(L, S).
valid(M, I, L, D) :- mission(M), item(I), location(L), decor(D), fits(I, L).

repair :- trust_level(T), T <= 4.
smooth :- trust_level(T), T > 4.

outcome(repair) :- repair.
outcome(smooth) :- smooth.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("shape", item_id, item.shape))
    for location_id, location in LOCATIONS.items():
        lines.append(asp.fact("location", location_id))
        for shape in sorted(location.fit_shapes):
            lines.append(asp.fact("accepts", location_id, shape))
    for decor_id in DECORS:
        lines.append(asp.fact("decor", decor_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trust_level", params.trust_level)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome disagreements.")

    smoke = CURATED[0]
    try:
        sample = generate(smoke)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        mission="comet_watch",
        item="star_map",
        location="between_books",
        decor="foil_stars",
        lead_name="Nova",
        lead_gender="girl",
        friend_name="Jet",
        friend_gender="boy",
        parent="mother",
        trust_level=7,
    ),
    StoryParams(
        mission="moon_mail",
        item="moon_key",
        location="inside_toolbox",
        decor="rocket_tubes",
        lead_name="Luna",
        lead_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        parent="father",
        trust_level=3,
    ),
    StoryParams(
        mission="ring_rescue",
        item="ring_chart",
        location="under_cushion",
        decor="meteor_pillows",
        lead_name="Orion",
        lead_gender="boy",
        friend_name="Skye",
        friend_gender="girl",
        parent="mother",
        trust_level=6,
    ),
    StoryParams(
        mission="comet_watch",
        item="signal_badge",
        location="tin_drawer",
        decor="rocket_tubes",
        lead_name="Ayla",
        lead_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="father",
        trust_level=2,
    ),
]


# ---------------------------------------------------------------------------
# CLI / interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: two friends prepare a space adventure, lose an important object, solve the mystery with a flashback, and strengthen their friendship."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--decor", choices=DECORS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trust-level", type=int, choices=list(range(1, 8)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.location:
        item = ITEMS[args.item]
        location = LOCATIONS[args.location]
        if not location_fits(item, location):
            raise StoryError(explain_rejection(item, location))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.item is None or combo[1] == args.item)
        and (args.location is None or combo[2] == args.location)
        and (args.decor is None or combo[3] == args.decor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, item, location, decor = rng.choice(sorted(combos))
    lead_name, lead_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=lead_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trust_level = args.trust_level if args.trust_level is not None else rng.randint(2, 7)

    return StoryParams(
        mission=mission,
        item=item,
        location=location,
        decor=decor,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trust_level=trust_level,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.location not in LOCATIONS:
        raise StoryError(f"(Unknown location: {params.location})")
    if params.decor not in DECORS:
        raise StoryError(f"(Unknown decor: {params.decor})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if not location_fits(ITEMS[params.item], LOCATIONS[params.location]):
        raise StoryError(explain_rejection(ITEMS[params.item], LOCATIONS[params.location]))

    world = tell(
        MISSIONS[params.mission],
        ITEMS[params.item],
        LOCATIONS[params.location],
        DECORS[params.decor],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trust_level=params.trust_level,
    )

    story = world.render().replace("{friend_pos}", world.get("friend").pronoun("possessive"))
    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (mission, item, location, decor) combos:\n")
        for mission, item, location, decor in combos:
            print(f"  {mission:12} {item:12} {location:14} {decor}")
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
            header = f"### {p.lead_name} & {p.friend_name}: {p.mission}, {p.item} at {p.location} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
