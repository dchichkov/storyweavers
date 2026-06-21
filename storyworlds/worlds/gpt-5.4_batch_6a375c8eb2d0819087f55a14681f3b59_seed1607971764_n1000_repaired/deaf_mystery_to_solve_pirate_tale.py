#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deaf_mystery_to_solve_pirate_tale.py
===============================================================

A standalone story world for a child-facing pirate-style mystery in which a deaf
child helps solve the case of a missing treasure. The world models a small
pretend-play domain: two children are playing pirates, their treasure goes
missing, visible clues point toward a hiding spot, and the deaf scout notices
what others miss.

The world prefers *visual* or *touchable* clues that make sense for a deaf
detective. It refuses combinations where the clue would not honestly lead to the
spot, or where the chosen search tool would not help reach or inspect the place.

Run it
------
    python storyworlds/worlds/gpt-5.4/deaf_mystery_to_solve_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/deaf_mystery_to_solve_pirate_tale.py --qa
    python storyworlds/worlds/gpt-5.4/deaf_mystery_to_solve_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/deaf_mystery_to_solve_pirate_tale.py --asp
    python storyworlds/worlds/gpt-5.4/deaf_mystery_to_solve_pirate_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    crew_word: str
    mission: str
    launch: str
    ending: str
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    shine: str
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
class Mover:
    id: str
    label: str
    phrase: str
    verb: str
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
class HidingSpot:
    id: str
    label: str
    the: str
    where_line: str
    found_line: str
    affordances: set[str] = field(default_factory=set)
    allowed_movers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    sentence: str
    notice: str
    modality: str
    possible_spots: set[str] = field(default_factory=set)
    mover_tags: set[str] = field(default_factory=set)
    direct: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    supports: set[str] = field(default_factory=set)
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
        return [e for e in self.entities.values() if e.role in {"captain", "scout"}]

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


def _r_missing_treasure(world: World) -> list[str]:
    treasure = world.get("treasure")
    if treasure.meters["hidden"] < THRESHOLD:
        return []
    sig = ("missing", "treasure")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
        kid.memes["curiosity"] += 1
    return []


def _r_good_clue(world: World) -> list[str]:
    treasure = world.get("treasure")
    clue = world.get("clue")
    tool = world.get("tool")
    if treasure.meters["hidden"] < THRESHOLD:
        return []
    if clue.meters["noticed"] < THRESHOLD or tool.meters["ready"] < THRESHOLD:
        return []
    sig = ("lead", world.facts["spot"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["lead"] += 1
    for kid in world.kids():
        kid.memes["hope"] += 1
    return []


def _r_find_treasure(world: World) -> list[str]:
    treasure = world.get("treasure")
    spot = world.get("spot")
    if world.get("room").meters["lead"] < THRESHOLD:
        return []
    if spot.meters["searched"] < THRESHOLD:
        return []
    sig = ("found", "treasure")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["hidden"] = 0.0
    treasure.meters["found"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_treasure", tag="physical", apply=_r_missing_treasure),
    Rule(name="good_clue", tag="mystery", apply=_r_good_clue),
    Rule(name="find_treasure", tag="physical", apply=_r_find_treasure),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def clue_matches(mover: Mover, spot: HidingSpot, clue: Clue) -> bool:
    if clue.modality not in {"visual", "touch"}:
        return False
    if spot.id not in clue.possible_spots:
        return False
    if mover.id not in spot.allowed_movers:
        return False
    return bool(mover.tags & clue.mover_tags)


def tool_helps(spot: HidingSpot, tool: Tool) -> bool:
    return bool(spot.affordances & tool.supports)


def valid_combo(mover: Mover, spot: HidingSpot, clue: Clue, tool: Tool) -> bool:
    return clue_matches(mover, spot, clue) and tool_helps(spot, tool)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for theme_id in THEMES:
        for treasure_id in TREASURES:
            for mover_id, mover in MOVERS.items():
                for spot_id, spot in SPOTS.items():
                    for clue_id, clue in CLUES.items():
                        for tool_id, tool in TOOLS.items():
                            if valid_combo(mover, spot, clue, tool):
                                combos.append((theme_id, treasure_id, mover_id, spot_id, clue_id, tool_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    clue = CLUES[params.clue]
    return "quick" if clue.direct else "detour"


def predict_success(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["noticed"] += 1
    sim.get("tool").meters["ready"] += 1
    if not CLUES[sim.facts["clue"].id].direct:
        sim.get("room").meters["false_guess"] += 1
    sim.get("spot").meters["searched"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("treasure").meters["found"] >= THRESHOLD,
        "lead": sim.get("room").meters["lead"] >= THRESHOLD,
    }


def play_setup(world: World, captain: Entity, scout: Entity, theme: Theme, treasure: Treasure) -> None:
    for kid in world.kids():
        kid.memes["joy"] += 1
    world.say(
        f"One bright afternoon, {captain.id} and {scout.id} turned the living room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'{captain.id} thumped the sofa-arm like a drum. "{theme.launch}!"'
    )
    world.say(
        f"They had one special prize for the game: {treasure.phrase}, {treasure.shine}."
    )


def introduce_deaf_scout(world: World, scout: Entity) -> None:
    world.say(
        f"{scout.id} was deaf, and {scout.pronoun()} was very good at watching faces, hands, and tiny changes in a room."
    )
    world.say(
        f"When {captain.id if 'captain' in world.entities else 'the captain'} talked too fast, {scout.id} tapped a finger in the air for \"slow down,\" and everyone smiled and tried again."
    )


def vanish(world: World, captain: Entity, scout: Entity, treasure: Treasure, theme: Theme) -> None:
    world.get("treasure").meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, just as they were ready for {theme.mission}, {captain.id} looked at the rug and froze. "
        f'"Wait. Where is {treasure.label}?"'
    )
    world.say(
        f"{scout.id} turned in a quick circle. The prize was gone."
    )


def wrong_guess(world: World, captain: Entity, mover: Mover) -> None:
    captain.memes["hurry"] += 1
    world.say(
        f'"Maybe {mover.phrase} took it!" {captain.id} blurted. For one breath, the mystery felt bigger than the game.'
    )


def notice_clue(world: World, scout: Entity, clue: Clue) -> None:
    pred = predict_success(world)
    scout.memes["focus"] += 1
    world.get("clue").meters["noticed"] += 1
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_lead"] = pred["lead"]
    world.say(
        f"But {scout.id} did not rush. {scout.pronoun().capitalize()} pointed instead. {clue.notice}"
    )
    world.say(
        f'''{clue.sentence} {scout.id} signed, \"Look first. Then guess.\"'''
    )


def follow_detour(world: World, captain: Entity, scout: Entity, clue: Clue) -> None:
    world.get("room").meters["false_guess"] += 1
    captain.memes["embarrassment"] += 1
    world.say(
        f"The clue was not clear at first. {captain.id} checked the wrong corner and found only dust and one lonely block."
    )
    world.say(
        f"{scout.id} crouched lower, looked again, and traced the real path with one careful finger."
    )


def search_spot(world: World, captain: Entity, scout: Entity, spot: HidingSpot, tool: Tool) -> None:
    world.get("tool").meters["ready"] += 1
    world.say(
        f"Together they used {tool.phrase}. {captain.id} {tool.action}, and {scout.id} watched the place {spot.where_line}."
    )
    world.get("spot").meters["searched"] += 1
    propagate(world, narrate=False)


def recover(world: World, captain: Entity, scout: Entity, treasure: Treasure, spot: HidingSpot) -> None:
    world.say(
        f"{spot.The} held the answer. There was {treasure.label}, {spot.found_line}."
    )
    world.say(
        f'{captain.id} gave a happy gasp. "{treasure.label.capitalize()}!"'
    )


def explain(world: World, helper: Entity, captain: Entity, scout: Entity, mover: Mover, clue: Clue) -> None:
    for kid in world.kids():
        kid.memes["pride"] += 1
    if mover.id == "kitten":
        cause = f"{mover.label} must have {mover.verb} it while chasing the shiny edge"
    elif mover.id == "breeze":
        cause = f"a little gust must have {mover.verb} it when the window was open"
    else:
        cause = f"{mover.label} must have {mover.verb} it while trying to help the game"
    world.say(
        f"{helper.label_word.capitalize()} came over and looked where they were pointing. "
        f'"I see it now," {helper.pronoun()} said. "{clue.label.capitalize()} was the clue. {cause}."'
    )
    world.say(
        f'''{captain.id} looked at {scout.id} and grinned. \"You solved it.\"'''
    )


def mend_and_end(world: World, captain: Entity, scout: Entity, theme: Theme, treasure: Treasure) -> None:
    captain.memes["trust"] += 1
    scout.memes["trust"] += 1
    captain.memes["joy"] += 1
    scout.memes["joy"] += 1
    world.say(
        f'{captain.id} touched {scout.id}\'s shoulder so {scout.pronoun()} would see, then said clearly, "Next time I will not guess before I look."'
    )
    world.say(
        f'''{scout.id} smiled and signed, \"Crew first. Mystery second. Treasure always.\"'''
    )
    world.say(
        f"Soon the {theme.crew_word} were off again, {theme.ending}, with {treasure.ending_image} proving the case was solved."
    )

def tell(
    treasure_cfg: Treasure,
    mover: Mover,
    spot_cfg: Spot,
    clue_cfg: Clue,
    tool_cfg: Tool,
    captain_name: str,
    captain_gender: str,
    scout_name: str,
    scout_gender: str,
    helper_type: HelperType,
    theme=None,
) -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        traits=["bold"],
    ))
    scout = world.add(Entity(
        id=scout_name,
        kind="character",
        type=scout_gender,
        label=scout_name,
        role="scout",
        traits=["careful", "deaf"],
        attrs={"deaf": True},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    treasure = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        tags=set(treasure_cfg.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=clue_cfg.label,
        tags=set(clue_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        tags=set(tool_cfg.tags),
    ))
    spot = world.add(Entity(
        id="spot",
        type="spot",
        label=spot_cfg.label,
        tags=set(spot_cfg.tags),
    ))

    world.facts.update(
        theme=theme,
        treasure_cfg=treasure_cfg,
        mover=mover,
        spot=spot_cfg,
        clue=clue_cfg,
        tool=tool_cfg,
        captain=captain,
        scout=scout,
        helper=helper,
    )

    play_setup(world, captain, scout, theme, treasure_cfg)
    introduce_deaf_scout(world, scout)

    world.para()
    vanish(world, captain, scout, treasure_cfg, theme)
    wrong_guess(world, captain, mover)
    notice_clue(world, scout, clue_cfg)

    world.para()
    if not clue_cfg.direct:
        follow_detour(world, captain, scout, clue_cfg)
    search_spot(world, captain, scout, spot_cfg, tool_cfg)
    recover(world, captain, scout, treasure_cfg, spot_cfg)

    world.para()
    explain(world, helper, captain, scout, mover, clue_cfg)
    mend_and_end(world, captain, scout, theme, treasure_cfg)

    world.facts.update(
        outcome=outcome_of(StoryParams(
            theme=theme.id,
            treasure=treasure_cfg.id,
            mover=mover.id,
            spot=spot_cfg.id,
            clue=clue_cfg.id,
            tool=tool_cfg.id,
            captain_name=captain_name,
            captain_gender=captain_gender,
            scout_name=scout_name,
            scout_gender=scout_gender,
            helper=helper_type,
            seed=None,
        )),
        found=world.get("treasure").meters["found"] >= THRESHOLD,
        false_guess=world.get("room").meters["false_guess"] >= THRESHOLD,
    )
    return world
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


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a rocking pirate ship",
        rig="The sofa was the deck, a striped blanket was the sail, a cardboard tube was the spyglass, and a chalk map curled across the floor.",
        crew_word="pirates",
        mission="the final hunt for buried gold",
        launch="Captain and Scout to the deck",
        ending="following the map with slower eyes and brighter smiles",
    ),
    "islanders": Theme(
        id="islanders",
        scene="a stormy island harbor",
        rig="A chair became the mast, a blue towel turned into the sea, and a basket by the wall was the supply dock.",
        crew_word="crew",
        mission="the search for the hidden harbor treasure",
        launch="Crew, take your places",
        ending="marching over the rug like brave sailors",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a moonlit pirate cove",
        rig="The coffee table was the cliff, two cushions were the boats, and a crayon X shone on the paper map.",
        crew_word="corsairs",
        mission="the chase for the lost cove prize",
        launch="To the cove, mates",
        ending="setting off again with a solved-secret grin",
    ),
}

TREASURES = {
    "shell_key": Treasure(
        id="shell_key",
        label="the shell key",
        phrase="a little shell key tied with red string",
        shine="white and pearly in the window light",
        ending_image="the shell key swinging safely from the map-corner",
        tags={"shell", "treasure"},
    ),
    "golden_coin": Treasure(
        id="golden_coin",
        label="the golden coin",
        phrase="a big golden coin cut from bright card",
        shine="glittery enough to look real",
        ending_image="the golden coin gleaming in the captain's palm",
        tags={"coin", "treasure"},
    ),
    "ruby_box": Treasure(
        id="ruby_box",
        label="the ruby box",
        phrase="a tiny red treasure box with a clicky lid",
        shine="small but grand, like a captain's prize",
        ending_image="the ruby box resting on the blanket-sail",
        tags={"box", "treasure"},
    ),
}

MOVERS = {
    "kitten": Mover(
        id="kitten",
        label="the kitten",
        phrase="the kitten",
        verb="batted",
        tags={"playful", "low", "paw"},
    ),
    "breeze": Mover(
        id="breeze",
        label="the breeze",
        phrase="the breeze",
        verb="slid",
        tags={"light", "wind", "soft"},
    ),
    "cousin": Mover(
        id="cousin",
        label="little Jo",
        phrase="little Jo",
        verb="tucked",
        tags={"small", "helpful", "high"},
    ),
}

SPOTS = {
    "under_table": HidingSpot(
        id="under_table",
        label="under the table",
        the="the dark space under the table",
        where_line="under the table legs",
        found_line="half tucked beside a wooden leg",
        affordances={"dark", "under"},
        allowed_movers={"kitten", "breeze"},
        tags={"dark_place"},
    ),
    "curtain_fold": HidingSpot(
        id="curtain_fold",
        label="inside the curtain fold",
        the="the long curtain fold",
        where_line="where the curtain pooled by the wall",
        found_line="caught in the soft curtain fold",
        affordances={"soft", "high"},
        allowed_movers={"breeze", "cousin"},
        tags={"curtain"},
    ),
    "boot": HidingSpot(
        id="boot",
        label="inside a rain boot",
        the="the rain boot by the door",
        where_line="inside the boot-top by the door",
        found_line="nestled at the bottom of the boot",
        affordances={"narrow", "low"},
        allowed_movers={"kitten", "cousin"},
        tags={"boot"},
    ),
}

CLUES = {
    "paw_marks": Clue(
        id="paw_marks",
        label="tiny paw marks",
        sentence="Tiny dusty paw marks dotted the rug in a crooked line.",
        notice="There were tiny paw marks, too small for a child and too neat to be an accident.",
        modality="visual",
        possible_spots={"under_table", "boot"},
        mover_tags={"paw", "playful", "low"},
        direct=False,
        tags={"paw", "visual_clue"},
    ),
    "glitter_peek": Clue(
        id="glitter_peek",
        label="a glittery peek",
        sentence="A bright glint winked where no treasure should have been.",
        notice="A little glittery corner was peeking out.",
        modality="visual",
        possible_spots={"under_table", "curtain_fold"},
        mover_tags={"wind", "soft", "light"},
        direct=True,
        tags={"glitter", "visual_clue"},
    ),
    "boot_sand": Clue(
        id="boot_sand",
        label="a sprinkle of sand",
        sentence="A pale sprinkle of sand lay beside one boot even though the floor had just been swept.",
        notice="There was fresh sand beside one boot and a faint shine deep inside.",
        modality="visual",
        possible_spots={"boot"},
        mover_tags={"small", "helpful", "high"},
        direct=True,
        tags={"sand", "visual_clue"},
    ),
    "curtain_bulge": Clue(
        id="curtain_bulge",
        label="a curtain bulge",
        sentence="One curtain hung strangely, with a small round bump in the cloth.",
        notice="One curtain looked puffier than the other one.",
        modality="visual",
        possible_spots={"curtain_fold"},
        mover_tags={"wind", "soft", "high", "small", "helpful"},
        direct=True,
        tags={"curtain", "visual_clue"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="the little pirate lantern",
        action="held it low so warm light slid into the shadows",
        supports={"dark"},
        tags={"lantern"},
    ),
    "hook": Tool(
        id="hook",
        label="hook",
        phrase="the toy pirate hook",
        action="used it gently to lift and pull without pushing an arm too far in",
        supports={"under", "narrow", "soft"},
        tags={"hook"},
    ),
    "spyglass": Tool(
        id="spyglass",
        label="spyglass",
        phrase="the cardboard spyglass",
        action="peered through it and pointed where the glimmer looked brightest",
        supports={"high", "soft"},
        tags={"spyglass"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nora", "Zoe", "Ava", "Mina", "Tess", "Ruby"]
BOY_NAMES = ["Tom", "Finn", "Max", "Leo", "Eli", "Theo", "Sam", "Ben"]


KNOWLEDGE = {
    "deaf": [
        (
            "What does it mean if someone is deaf?",
            "A deaf person does not hear in the usual way, or may not hear at all. They can still notice many things with their eyes, hands, and attention."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. Good detectives slow down and notice clues before they guess."
        )
    ],
    "pirate": [
        (
            "What is a pirate in pretend play?",
            "In pretend play, a pirate is someone in a make-believe sea adventure who hunts for treasure and sails on imaginary ships."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp that gives light. In a game, a lantern can help you see into dark corners."
        )
    ],
    "hook": [
        (
            "What is a hook used for?",
            "A hook can pull or lift something from a tight place. You still have to use it gently and carefully."
        )
    ],
    "spyglass": [
        (
            "What is a spyglass?",
            "A spyglass is a small telescope sailors used to look far away. In pretend play, it helps children search and focus on what they see."
        )
    ],
    "paw": [
        (
            "What are paw marks?",
            "Paw marks are little prints left by an animal's feet. They can show where a pet has been."
        )
    ],
    "curtain": [
        (
            "Why can a curtain bulge matter in a mystery?",
            "If a curtain hangs in a strange shape, something may be tucked inside it. A changed shape can be a clue."
        )
    ],
    "sand": [
        (
            "Why can sand be a clue indoors?",
            "Sand does not belong on a clean floor, so it can show that something was carried or dragged from one place to another."
        )
    ],
}
KNOWLEDGE_ORDER = ["deaf", "clue", "pirate", "lantern", "hook", "spyglass", "paw", "curtain", "sand"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    scout = f["scout"]
    treasure = f["treasure_cfg"]
    theme = f["theme"]
    clue = f["clue"]
    if f.get("outcome") == "detour":
        return [
            f'Write a gentle pirate-style mystery for a 3-to-5-year-old that includes the word "deaf" and a missing treasure called {treasure.label}.',
            f"Tell a pretend-play pirate story where {scout.id}, a deaf scout, notices a clue that everyone else almost misunderstands before the children solve the mystery.",
            f"Write a story where {captain.id} guesses too fast, {scout.id} slows the search down, and the {theme.crew_word} find the treasure by following {clue.label}.",
        ]
    return [
        f'Write a gentle pirate-style mystery for a 3-to-5-year-old that includes the word "deaf" and a missing treasure called {treasure.label}.',
        f"Tell a story where a deaf child playing pirates notices a tiny visual clue and helps solve the mystery of a missing prize.",
        f"Write a short pirate adventure in which {captain.id} and {scout.id} lose their treasure during play and solve the case by looking carefully instead of guessing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    scout = f["scout"]
    helper = f["helper"]
    treasure = f["treasure_cfg"]
    mover = f["mover"]
    spot = f["spot"]
    clue = f["clue"]
    tool = f["tool"]
    theme = f["theme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id} and {scout.id}, two children playing {theme.crew_word}. {scout.id} is deaf, and that careful way of noticing things helps solve the mystery."
        ),
        (
            f"What mystery did the children have to solve?",
            f"They had to find {treasure.label} after it suddenly disappeared during their pirate game. The missing prize turned their pretend adventure into a real little mystery."
        ),
        (
            f"How did {scout.id} help?",
            f"{scout.id} slowed down and noticed {clue.label} instead of making a fast guess. Because {scout.pronoun()} watched the room so carefully, the children got a real lead instead of more confusion."
        ),
        (
            f"Why did the children search {spot.label}?",
            f"They searched {spot.label} because the clue pointed there and their tool could help them check it properly. The search worked because the clue matched the hiding place instead of being a wild guess."
        ),
        (
            f"How did they find {treasure.label}?",
            f"They used {tool.phrase} and searched {spot.label}. Then they discovered {treasure.label} there and knew the mystery was solved."
        ),
    ]
    if world.facts.get("false_guess"):
        qa.append(
            (
                f"Did {captain.id} guess right at first?",
                f"No. {captain.id} hurried and checked the wrong place first. After that, {scout.id} looked again and followed the clue more carefully, which led them to the right spot."
            )
        )
    qa.append(
        (
            f"What had really happened to {treasure.label}?",
            f"{mover.label.capitalize()} had moved it, and {clue.label} showed the trail. The clue let the children explain the mystery without staying upset or blaming each other."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children playing pirates again and trusting careful looking more than quick guesses. The ending image of {treasure.ending_image} shows that the treasure was safe and the mystery was over."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"deaf", "clue", "pirate"}
    tags |= set(f["tool"].tags)
    tags |= set(f["clue"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    theme: str
    treasure: str
    mover: str
    spot: str
    clue: str
    tool: str
    captain_name: str = "Tom"
    captain_gender: str = "boy"
    scout_name: str = "Lina"
    scout_gender: str = "girl"
    helper: str = "mother"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        theme="pirates",
        treasure="shell_key",
        mover="kitten",
        spot="under_table",
        clue="paw_marks",
        tool="lantern",
        captain_name="Tom",
        captain_gender="boy",
        scout_name="Lina",
        scout_gender="girl",
        helper="mother",
    ),
    StoryParams(
        theme="islanders",
        treasure="golden_coin",
        mover="breeze",
        spot="curtain_fold",
        clue="glitter_peek",
        tool="spyglass",
        captain_name="Finn",
        captain_gender="boy",
        scout_name="Mara",
        scout_gender="girl",
        helper="father",
    ),
    StoryParams(
        theme="corsairs",
        treasure="ruby_box",
        mover="cousin",
        spot="boot",
        clue="boot_sand",
        tool="hook",
        captain_name="Ava",
        captain_gender="girl",
        scout_name="Ben",
        scout_gender="boy",
        helper="aunt",
    ),
    StoryParams(
        theme="pirates",
        treasure="golden_coin",
        mover="breeze",
        spot="curtain_fold",
        clue="curtain_bulge",
        tool="spyglass",
        captain_name="Nora",
        captain_gender="girl",
        scout_name="Theo",
        scout_gender="boy",
        helper="mother",
    ),
]


def explain_rejection(mover: Mover, spot: HidingSpot, clue: Clue, tool: Tool) -> str:
    if clue.modality not in {"visual", "touch"}:
        return (
            f"(No story: {clue.label} is not a clue this deaf detective could reasonably follow. "
            f"Choose a clue that can be seen or felt.)"
        )
    if mover.id not in spot.allowed_movers:
        return (
            f"(No story: {mover.label} would not naturally move the treasure to {spot.label}. "
            f"Pick a different mover or hiding spot.)"
        )
    if spot.id not in clue.possible_spots or not (mover.tags & clue.mover_tags):
        return (
            f"(No story: {clue.label} does not honestly point to {spot.label} for {mover.label}. "
            f"The mystery needs a clue that really fits the hiding place.)"
        )
    if not tool_helps(spot, tool):
        return (
            f"(No story: {tool.phrase} does not help search {spot.label}. "
            f"Pick a tool that can actually reach or inspect that place.)"
        )
    return "(No story: this combination does not form a reasonable mystery.)"


ASP_RULES = r"""
visual_clue(C) :- clue(C), modality(C, visual).
touch_clue(C)  :- clue(C), modality(C, touch).
deaf_friendly(C) :- visual_clue(C).
deaf_friendly(C) :- touch_clue(C).

clue_matches(M, S, C) :- mover(M), spot(S), clue(C),
                         deaf_friendly(C),
                         possible_spot(C, S),
                         mover_tag_match(M, C),
                         allowed(M, S).

tool_helps(S, T) :- spot_affordance(S, A), tool_support(T, A).

valid(Th, Tr, M, S, C, T) :- theme(Th), treasure(Tr),
                             clue_matches(M, S, C),
                             tool_helps(S, T).

quick(C)  :- clue(C), direct(C).
detour(C) :- clue(C), not direct(C).

outcome(quick)  :- chosen_clue(C), quick(C).
outcome(detour) :- chosen_clue(C), detour(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for treasure_id in TREASURES:
        lines.append(asp.fact("treasure", treasure_id))
    for mover_id, mover in MOVERS.items():
        lines.append(asp.fact("mover", mover_id))
        for tag in sorted(mover.tags):
            lines.append(asp.fact("mover_tag", mover_id, tag))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for affordance in sorted(spot.affordances):
            lines.append(asp.fact("spot_affordance", spot_id, affordance))
        for mover_id in sorted(spot.allowed_movers):
            lines.append(asp.fact("allowed", mover_id, spot_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("modality", clue_id, clue.modality))
        if clue.direct:
            lines.append(asp.fact("direct", clue_id))
        for spot_id in sorted(clue.possible_spots):
            lines.append(asp.fact("possible_spot", clue_id, spot_id))
        for tag in sorted(clue.mover_tags):
            lines.append(asp.fact("clue_mover_tag", clue_id, tag))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for support in sorted(tool.supports):
            lines.append(asp.fact("tool_support", tool_id, support))
    for mover_id, mover in MOVERS.items():
        for clue_id, clue in CLUES.items():
            if mover.tags & clue.mover_tags:
                lines.append(asp.fact("mover_tag_match", mover_id, clue_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            asp.fact("chosen_clue", params.clue),
            "#show outcome/1.",
        )
    )
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a deaf scout solves a pirate-style mystery."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mover and args.spot and args.clue and args.tool:
        mover = MOVERS[args.mover]
        spot = SPOTS[args.spot]
        clue = CLUES[args.clue]
        tool = TOOLS[args.tool]
        if not valid_combo(mover, spot, clue, tool):
            raise StoryError(explain_rejection(mover, spot, clue, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.mover is None or combo[2] == args.mover)
        and (args.spot is None or combo[3] == args.spot)
        and (args.clue is None or combo[4] == args.clue)
        and (args.tool is None or combo[5] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, treasure, mover, spot, clue, tool = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    scout_gender = rng.choice(["girl", "boy"])
    captain_name = _pick_name(rng, captain_gender)
    scout_name = _pick_name(rng, scout_gender, avoid=captain_name)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        theme=theme,
        treasure=treasure,
        mover=mover,
        spot=spot,
        clue=clue,
        tool=tool,
        captain_name=captain_name,
        captain_gender=captain_gender,
        scout_name=scout_name,
        scout_gender=scout_gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        treasure = TREASURES[params.treasure]
        mover = MOVERS[params.mover]
        spot = SPOTS[params.spot]
        clue = CLUES[params.clue]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not valid_combo(mover, spot, clue, tool):
        raise StoryError(explain_rejection(mover, spot, clue, tool))

    world = tell(
        theme=theme,
        treasure_cfg=treasure,
        mover=mover,
        spot_cfg=spot,
        clue_cfg=clue,
        tool_cfg=tool,
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        scout_name=params.scout_name,
        scout_gender=params.scout_gender,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, treasure, mover, spot, clue, tool) combos:\n")
        for theme, treasure, mover, spot, clue, tool in combos:
            print(f"  {theme:10} {treasure:12} {mover:8} {spot:13} {clue:14} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.captain_name} & {p.scout_name}: {p.treasure} "
                f"({p.mover}, {p.spot}, {p.clue}, {p.tool}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
