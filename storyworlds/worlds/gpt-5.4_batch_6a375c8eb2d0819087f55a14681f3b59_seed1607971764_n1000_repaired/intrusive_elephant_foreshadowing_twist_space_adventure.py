#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/intrusive_elephant_foreshadowing_twist_space_adventure.py
=====================================================================================

A standalone story world for a tiny space adventure with an intrusive mystery,
foreshadowing clues, and a twist: the feared "space intruder" is really a lost
young elephant from the station zoo.

The engine models concrete world state: a ship corridor, a hidden stowaway,
physical clues, rising worry, a calm investigation, a reveal, and a gentle
return. The prose is rendered from that simulated state, not from a single
frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/intrusive_elephant_foreshadowing_twist_space_adventure.py
    python storyworlds/worlds/gpt-5.4/intrusive_elephant_foreshadowing_twist_space_adventure.py --mission comet --hideout greenhouse
    python storyworlds/worlds/gpt-5.4/intrusive_elephant_foreshadowing_twist_space_adventure.py --hideout vent
    python storyworlds/worlds/gpt-5.4/intrusive_elephant_foreshadowing_twist_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/intrusive_elephant_foreshadowing_twist_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/intrusive_elephant_foreshadowing_twist_space_adventure.py --verify
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
        female = {"girl", "mother", "woman", "captain_f"}
        male = {"boy", "father", "man", "captain_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "elephant":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "captain_f": "captain",
            "captain_m": "captain",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
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
class Mission:
    id: str
    title: str
    ship: str
    route: str
    task: str
    window: str
    ending: str
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
class Hideout:
    id: str
    label: str
    the: str
    space_desc: str
    noise: str
    roomy: bool
    leafy: bool = False
    near_window: bool = False
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
    text: str
    points_to: set[str] = field(default_factory=set)
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
    method: str
    works_in: set[str] = field(default_factory=set)
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


def _r_intrusion(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("noise_happened"):
        return out
    intruder = world.get("elephant")
    ship = world.get("ship")
    for kid_id in ("hero", "pal"):
        kid = world.get(kid_id)
        sig = ("alarm", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["worry"] += 1
        ship.meters["racket"] += 1
        out.append("__worry__")
    if intruder.meters["hidden"] >= THRESHOLD and ("hungry", intruder.id) not in world.fired:
        world.fired.add(("hungry", intruder.id))
        intruder.memes["hunger"] += 1
    return out


def _r_clue_stack(world: World) -> list[str]:
    out: list[str] = []
    clue_count = int(world.facts.get("clue_count", 0))
    if clue_count >= 2 and ("suspect_elephant",) not in world.fired:
        world.fired.add(("suspect_elephant",))
        for kid_id in ("hero", "pal"):
            world.get(kid_id).memes["curiosity"] += 1
        out.append("__suspect__")
    return out


def _r_reveal_relief(world: World) -> list[str]:
    out: list[str] = []
    intruder = world.get("elephant")
    if intruder.meters["revealed"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        for kid_id in ("hero", "pal"):
            kid = world.get(kid_id)
            kid.memes["worry"] = 0.0
            kid.memes["relief"] += 1
            kid.memes["wonder"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="intrusion", tag="social", apply=_r_intrusion),
    Rule(name="clues", tag="inference", apply=_r_clue_stack),
    Rule(name="reveal_relief", tag="emotional", apply=_r_reveal_relief),
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


def hideout_accepts(hideout: Hideout) -> bool:
    return hideout.roomy


def clue_fits_hideout(clue: Clue, hideout: Hideout) -> bool:
    return hideout.id in clue.points_to


def tool_works(tool: Tool, hideout: Hideout) -> bool:
    return hideout.id in tool.works_in


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for hideout_id, hideout in HIDEOUTS.items():
            if not hideout_accepts(hideout):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_works(tool, hideout):
                    combos.append((mission_id, hideout_id, tool_id))
    return combos


def clue_pool_for_hideout(hideout_id: str) -> list[str]:
    return sorted(cid for cid, clue in CLUES.items() if clue_fits_hideout(clue, HIDEOUTS[hideout_id]))


def predict_twist(world: World, hideout_id: str) -> dict:
    sim = world.copy()
    clues = clue_pool_for_hideout(hideout_id)[:2]
    sim.facts["clue_count"] = 0
    for clue_id in clues:
        sim.facts["clue_count"] += 1
        sim.facts.setdefault("seen_clues", []).append(clue_id)
        propagate(sim, narrate=False)
    return {
        "suspects_elephant": world.get("hero").memes["curiosity"] < THRESHOLD and any(
            sig == ("suspect_elephant",) for sig in sim.fired
        ),
        "clues": clues,
    }


def intro(world: World, hero: Entity, pal: Entity, captain: Entity, mission: Mission) -> None:
    for kid in (hero, pal):
        kid.memes["joy"] += 1
    world.say(
        f"{hero.id} and {pal.id} were junior star scouts aboard the {mission.ship}. "
        f"They were helping {captain.label_word} on {mission.task} along {mission.route}."
    )
    world.say(
        f"Outside the window, {mission.window}. Inside, the little ship hummed as smoothly as a song."
    )


def intrusive_noise(world: World, hero: Entity, pal: Entity, hideout: Hideout) -> None:
    world.facts["noise_happened"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then an intrusive sound broke into the quiet -- {hideout.noise} from {hideout.the}. "
        f"The whole corridor gave a tiny shiver."
    )
    world.say(
        f'"Did you hear that?" {pal.id} whispered. {hero.id} nodded and stared toward {hideout.the}.'
    )


def foreshadow(world: World, clue_ids: list[str]) -> None:
    for clue_id in clue_ids:
        clue = CLUES[clue_id]
        world.facts["clue_count"] += 1
        world.facts["seen_clues"].append(clue_id)
        propagate(world, narrate=False)
        world.say(clue.text)
    if ("suspect_elephant",) in world.fired:
        hero = world.get("hero")
        pal = world.get("pal")
        world.say(
            f'{hero.id} blinked. "That is a very strange trail," {hero.pronoun()} said. '
            f'"Strange in a big, round, trunkish sort of way," {pal.id} murmured.'
        )


def investigate(world: World, hero: Entity, pal: Entity, captain: Entity, hideout: Hideout) -> None:
    hero.memes["bravery"] += 1
    pal.memes["bravery"] += 1
    world.say(
        f"{captain.label_word.capitalize()} lowered a gentle flashlight and led them to {hideout.the}. "
        f"{hideout.space_desc}"
    )
    world.say(
        f'Together they counted to three. Then {captain.label_word} slid the panel aside.'
    )


def reveal(world: World, elephant: Entity, hideout: Hideout) -> None:
    elephant.meters["hidden"] = 0.0
    elephant.meters["revealed"] += 1
    elephant.memes["fright"] += 1
    propagate(world, narrate=False)
    world.say(
        f"It was not a moon bandit or a space goblin at all. Curled inside {hideout.the} was a small silver-blanketed elephant, "
        f"with soft ears, worried eyes, and a trunk that gave one hopeful wiggle."
    )
    world.say(
        f'The twist made everybody gasp. The intrusive mystery was only a lost elephant looking for a place to hide.'
    )


def soothe(world: World, captain: Entity, elephant: Entity, tool: Tool) -> None:
    elephant.memes["trust"] += 1
    world.say(
        f"{captain.label_word.capitalize()} did not shout. {captain.pronoun().capitalize()} held out {tool.phrase} and {tool.method}."
    )
    world.say(
        "The little elephant stopped backing away. Its trunk reached forward, slow and careful, and the frightened look began to melt."
    )


def return_elephant(world: World, hero: Entity, pal: Entity, mission: Mission, hideout: Hideout) -> None:
    elephant = world.get("elephant")
    elephant.meters["returned"] += 1
    hero.memes["care"] += 1
    pal.memes["care"] += 1
    world.say(
        f"Soon the scouts walked beside the elephant all the way to the station zoo gate. "
        f"The zookeeper laughed with relief when {hero.id} explained where the tiny runaway had been hiding."
    )
    world.say(
        f"Back on the {mission.ship}, the corridor felt peaceful again, and {mission.ending}."
    )


def closing_image(world: World, hero: Entity, pal: Entity, mission: Mission) -> None:
    world.say(
        f"From then on, whenever the ship made a funny thump, {hero.id} and {pal.id} listened before guessing. "
        f"Some space surprises were not dangerous at all. Some just needed kindness, a good clue, and room for an elephant."
    )


def tell(
    mission: Mission,
    hideout: Hideout,
    clues: list[Clue],
    tool: Tool,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    pal_name: str = "Jet",
    pal_type: str = "boy",
    captain_type: str = "captain_f",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    pal = world.add(Entity(id="pal", kind="character", type=pal_type, label=pal_name, role="pal"))
    captain = world.add(Entity(id="captain", kind="character", type=captain_type, label="the captain", role="captain"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=mission.ship))
    elephant = world.add(Entity(id="elephant", kind="character", type="elephant", label="the elephant", role="intruder"))
    elephant.meters["hidden"] = 1.0
    elephant.memes["fright"] = 1.0

    world.facts["noise_happened"] = False
    world.facts["clue_count"] = 0
    world.facts["seen_clues"] = []

    intro(world, hero, pal, captain, mission)
    world.para()
    intrusive_noise(world, hero, pal, hideout)
    foreshadow(world, [clue.id for clue in clues])
    world.para()
    investigate(world, hero, pal, captain, hideout)
    reveal(world, elephant, hideout)
    world.para()
    soothe(world, captain, elephant, tool)
    return_elephant(world, hero, pal, mission, hideout)
    closing_image(world, hero, pal, mission)

    world.facts.update(
        hero=hero,
        pal=pal,
        captain=captain,
        ship=ship,
        elephant=elephant,
        mission=mission,
        hideout=hideout,
        clues=clues,
        tool=tool,
        outcome="returned" if elephant.meters["returned"] >= THRESHOLD else "lost",
    )
    return world


MISSIONS = {
    "moon": Mission(
        id="moon",
        title="Moon Mail Run",
        ship="Starhopper",
        route="the blue curve of the moon road",
        task="a moon-mail delivery run between bright little stations",
        window="craters drifted past like silver bowls",
        ending="the mail sacks sat neatly in place, and one small silver trunk print still gleamed on the floor",
        tags={"moon", "space"},
    ),
    "comet": Mission(
        id="comet",
        title="Comet Map Patrol",
        ship="Comet Kite",
        route="the glittering tail paths near a sleepy comet",
        task="a map-check patrol for sparkling beacon lights",
        window="ice dust flashed outside like shaken sugar",
        ending="the map board blinked green again, and one tiny trumpet sound seemed to wink through the air",
        tags={"comet", "space"},
    ),
    "rings": Mission(
        id="rings",
        title="Ring Garden Supply Trip",
        ship="Ringbird",
        route="the slow gold curve of the planet rings",
        task="a supply trip to the ring gardens",
        window="the planet's rings shone like a giant golden ribbon",
        ending="the seed boxes were stacked in tidy rows, and the ship felt as calm as a sleeping star",
        tags={"rings", "space"},
    ),
}

HIDEOUTS = {
    "cargo": Hideout(
        id="cargo",
        label="cargo locker",
        the="the cargo locker",
        space_desc="Metal lunch tins and padded crates were stacked there in neat moon-gray towers",
        noise="a bump-bump and a tiny trumpet peep",
        roomy=True,
        tags={"cargo"},
    ),
    "greenhouse": Hideout(
        id="greenhouse",
        label="greenhouse bay",
        the="the greenhouse bay",
        space_desc="Round leaves floated in trays, and drops of water trembled on the stems",
        noise="leafy rustling and a soft bonk against a watering can",
        roomy=True,
        leafy=True,
        tags={"plants"},
    ),
    "observation": Hideout(
        id="observation",
        label="observation dome",
        the="the observation dome curtain nook",
        space_desc="The stars pressed close to the glass, and a silver curtain hung in a sleepy fold",
        noise="a curtain swish and one round, sneezy huff",
        roomy=True,
        near_window=True,
        tags={"window"},
    ),
    "vent": Hideout(
        id="vent",
        label="maintenance vent",
        the="the maintenance vent",
        space_desc="The vent was narrow and full of humming pipes",
        noise="a tap-tap from the vent grille",
        roomy=False,
        tags={"tight"},
    ),
}

CLUES = {
    "prints": Clue(
        id="prints",
        label="round prints",
        text="On the shiny floor were four dusty round prints, much wider than a cat's and much softer-looking than a boot's.",
        points_to={"cargo", "greenhouse", "observation"},
        tags={"tracks", "elephant"},
    ),
    "peanut": Clue(
        id="peanut",
        label="sweet snack smell",
        text='A sweet snack smell drifted through the corridor. "That smells like the zoo snack cart," said the captain.',
        points_to={"cargo", "observation"},
        tags={"smell", "elephant"},
    ),
    "leaf": Clue(
        id="leaf",
        label="chewed leaves",
        text="By the door lay a half-chewed leaf, nibbled in a neat half-moon bite.",
        points_to={"greenhouse"},
        tags={"leaf", "elephant"},
    ),
    "blanket": Clue(
        id="blanket",
        label="silver thread",
        text="A silver thread was caught on the latch, the kind used in warm animal blankets at the station zoo.",
        points_to={"cargo", "observation", "greenhouse"},
        tags={"blanket", "zoo"},
    ),
}

TOOLS = {
    "apples": Tool(
        id="apples",
        label="star apples",
        phrase="a bowl of star apples",
        method="and made a soft trail of sweet slices across the floor",
        works_in={"cargo", "observation", "greenhouse"},
        tags={"food"},
    ),
    "song": Tool(
        id="song",
        label="humming song",
        phrase="a quiet humming song",
        method="while tapping a slow, friendly marching beat with a boot",
        works_in={"cargo", "observation"},
        tags={"music"},
    ),
    "watering": Tool(
        id="watering",
        label="watering wand",
        phrase="the watering wand",
        method="and misted the leaves until the little trunk reached out to play in the cool sparkle",
        works_in={"greenhouse"},
        tags={"water"},
    ),
}


GIRL_NAMES = ["Mira", "Nova", "Luna", "Zuri", "Pia", "Tess", "Rhea", "Ivy"]
BOY_NAMES = ["Jet", "Orion", "Max", "Leo", "Finn", "Sol", "Nico", "Arlo"]
TRAITS = ["brave", "careful", "curious", "steady", "gentle"]


@dataclass
class StoryParams:
    mission: str
    hideout: str
    tool: str
    hero_name: str
    hero_gender: str
    pal_name: str
    pal_gender: str
    captain_gender: str
    clue1: str
    clue2: str
    hero_trait: str = "curious"
    pal_trait: str = "brave"
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


CURATED = [
    StoryParams(
        mission="moon",
        hideout="cargo",
        tool="apples",
        hero_name="Mira",
        hero_gender="girl",
        pal_name="Jet",
        pal_gender="boy",
        captain_gender="captain_f",
        clue1="prints",
        clue2="blanket",
        hero_trait="curious",
        pal_trait="steady",
    ),
    StoryParams(
        mission="comet",
        hideout="greenhouse",
        tool="watering",
        hero_name="Nova",
        hero_gender="girl",
        pal_name="Orion",
        pal_gender="boy",
        captain_gender="captain_m",
        clue1="leaf",
        clue2="prints",
        hero_trait="gentle",
        pal_trait="careful",
    ),
    StoryParams(
        mission="rings",
        hideout="observation",
        tool="song",
        hero_name="Luna",
        hero_gender="girl",
        pal_name="Finn",
        pal_gender="boy",
        captain_gender="captain_f",
        clue1="peanut",
        clue2="blanket",
        hero_trait="brave",
        pal_trait="curious",
    ),
]


KNOWLEDGE = {
    "elephant": [
        (
            "What does an elephant use its trunk for?",
            "An elephant uses its trunk to smell, pick things up, drink water, and touch gently. It is like a nose, a hand, and a hose all together."
        )
    ],
    "tracks": [
        (
            "What can footprints tell you?",
            "Footprints can show that something passed by and how big it might be. A round print can be a good clue when you are trying to solve a mystery."
        )
    ],
    "zoo": [
        (
            "What is a zoo?",
            "A zoo is a place where animals are cared for by keepers. The keepers make sure the animals are fed, safe, and not lost."
        )
    ],
    "space": [
        (
            "Why do spaceships make strange sounds?",
            "Spaceships can hum, click, and thump because machines, doors, and air systems are always working. A funny sound does not always mean danger."
        )
    ],
    "plants": [
        (
            "Why do plants need water?",
            "Plants need water to stay alive and keep their leaves firm. Water helps them carry food through their stems."
        )
    ],
    "music": [
        (
            "Why can a soft song help a scared animal?",
            "A soft song can make the world feel calmer and less sudden. Slow, gentle sounds help a frightened animal feel safe enough to come closer."
        )
    ],
    "food": [
        (
            "Why might food help someone find a lost animal?",
            "A familiar food smell can help guide a lost animal back to people. It works best when the people move slowly and do not scare the animal."
        )
    ],
    "water": [
        (
            "Why would cool mist interest an elephant?",
            "Elephants like water because it cools them and feels good on their skin. A playful spray can help a nervous elephant relax."
        )
    ],
}
KNOWLEDGE_ORDER = ["space", "tracks", "zoo", "elephant", "plants", "music", "food", "water"]


def pair_noun(hero: Entity, pal: Entity) -> str:
    if hero.type == "girl" and pal.type == "girl":
        return "two young star scouts"
    if hero.type == "boy" and pal.type == "boy":
        return "two young star scouts"
    return "two young star scouts"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    hideout = f["hideout"]
    hero = f["hero"]
    pal = f["pal"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "intrusive" and "elephant". Use foreshadowing clues before the twist.',
        f"Tell a gentle starship mystery where {hero.label} and {pal.label} hear an intrusive noise from {hideout.the}, fear a space intruder, and then discover a surprising lost elephant.",
        f"Write a story set on a small ship during {mission.task} where clues quietly point to the truth before the reveal."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    captain = f["captain"]
    mission = f["mission"]
    hideout = f["hideout"]
    tool = f["tool"]
    clues = f["clues"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, pal)}, {hero.label} and {pal.label}, and their captain on the {mission.ship}. They were on {mission.task} when the mystery began."
        ),
        (
            "What was the intrusive problem at the start?",
            f"They heard an intrusive noise coming from {hideout.the}. The strange bumping interrupted their peaceful work and made them worry that something had sneaked aboard."
        ),
        (
            "What clues came before the twist?",
            f"They found {clues[0].label} and {clues[1].label}. Those details quietly pointed toward an animal from the zoo before anyone saw the truth."
        ),
        (
            "What was the twist?",
            f"The children expected a dangerous space intruder, but the hidden visitor was really a small lost elephant. The twist works because the scary sound turned out to come from someone frightened, not someone mean."
        ),
        (
            f"How did the captain help the elephant come out of {hideout.the}?",
            f"The captain used {tool.phrase} and moved in a calm, gentle way. That helped the elephant trust the people instead of hiding even deeper."
        ),
        (
            "How did the story end?",
            f"They walked the elephant back to the station zoo and finished the trip more wisely than before. At the end, the ship felt peaceful again, which showed the mystery had truly been solved."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"space", "elephant"}
    for clue in f["clues"]:
        tags |= set(clue.tags)
    tags |= set(f["hideout"].tags)
    tags |= set(f["tool"].tags)
    tags |= {"zoo"}
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: clue_count={world.facts.get('clue_count')} seen_clues={world.facts.get('seen_clues')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(hideout: Hideout, tool: Optional[Tool] = None) -> str:
    if not hideout.roomy:
        return (
            f"(No story: {hideout.the} is too cramped for a young elephant, so the twist would not be believable. "
            f"Pick a roomier hiding place like the cargo locker, greenhouse bay, or observation dome.)"
        )
    if tool is not None and not tool_works(tool, hideout):
        return (
            f"(No story: {tool.label} is not a good way to coax an elephant out of {hideout.the}. "
            f"Choose a tool that fits that place.)"
        )
    return "(No story: that combination does not fit this world.)"


ASP_RULES = r"""
acceptable_hideout(H) :- hideout(H), roomy(H).
compatible_tool(H, T) :- tool(T), works_in(T, H).
valid(M, H, T) :- mission(M), acceptable_hideout(H), compatible_tool(H, T).

shown_clue(H, C) :- clue(C), clue_points_to(C, H).
has_two_clues(H) :- acceptable_hideout(H), 2 <= #count { C : shown_clue(H, C) }.
twist_ready(H) :- has_two_clues(H).

#show valid/3.
#show twist_ready/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        if hideout.roomy:
            lines.append(asp.fact("roomy", hid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for hid in sorted(clue.points_to):
            lines.append(asp.fact("clue_points_to", cid, hid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for hid in sorted(tool.works_in):
            lines.append(asp.fact("works_in", tid, hid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_twist_ready() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(h for (h,) in asp.atoms(model, "twist_ready"))


def smoke_emit(sample: StorySample) -> None:
    if not sample.story.strip():
        raise StoryError("generated story was empty")
    _ = format_qa(sample)


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    ready = set(asp_twist_ready())
    py_ready = {hid for hid in HIDEOUTS if hideout_accepts(HIDEOUTS[hid]) and len(clue_pool_for_hideout(hid)) >= 2}
    if ready == py_ready:
        print(f"OK: twist-ready hideouts match ({sorted(ready)}).")
    else:
        rc = 1
        print(f"MISMATCH in twist-ready hideouts: clingo={sorted(ready)} python={sorted(py_ready)}")

    try:
        sample = generate(CURATED[0])
        smoke_emit(sample)
        print("OK: smoke test generate/emit path ran.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            smoke_emit(sample)
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SEEDED GENERATION FAILED at seed {seed}: {err}")
            break

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an intrusive ship mystery with foreshadowing and a twist."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--pal-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--pal-gender", choices=["girl", "boy"])
    ap.add_argument("--captain-gender", choices=["captain_f", "captain_m"])
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
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hideout is not None:
        hideout = HIDEOUTS[args.hideout]
        if not hideout_accepts(hideout):
            raise StoryError(explain_rejection(hideout))
    if args.hideout is not None and args.tool is not None:
        hideout = HIDEOUTS[args.hideout]
        tool = TOOLS[args.tool]
        if not tool_works(tool, hideout):
            raise StoryError(explain_rejection(hideout, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.hideout is None or combo[1] == args.hideout)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, hideout_id, tool_id = rng.choice(sorted(combos))
    clues = clue_pool_for_hideout(hideout_id)
    if len(clues) < 2:
        raise StoryError("(No story: this hiding place does not have enough clues for foreshadowing.)")
    clue1, clue2 = rng.sample(clues, 2)

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    pal_gender = args.pal_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    pal_name = args.pal_name or _pick_name(rng, pal_gender, avoid=hero_name)
    captain_gender = args.captain_gender or rng.choice(["captain_f", "captain_m"])
    hero_trait = rng.choice(TRAITS)
    pal_trait = rng.choice(TRAITS)

    return StoryParams(
        mission=mission_id,
        hideout=hideout_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        pal_name=pal_name,
        pal_gender=pal_gender,
        captain_gender=captain_gender,
        clue1=clue1,
        clue2=clue2,
        hero_trait=hero_trait,
        pal_trait=pal_trait,
    )


def _checked_lookup(table: dict, key: str, kind: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {kind} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    mission = _checked_lookup(MISSIONS, params.mission, "mission")
    hideout = _checked_lookup(HIDEOUTS, params.hideout, "hideout")
    tool = _checked_lookup(TOOLS, params.tool, "tool")
    if not hideout_accepts(hideout):
        raise StoryError(explain_rejection(hideout))
    if not tool_works(tool, hideout):
        raise StoryError(explain_rejection(hideout, tool))

    clue1 = _checked_lookup(CLUES, params.clue1, "clue")
    clue2 = _checked_lookup(CLUES, params.clue2, "clue")
    if clue1.id == clue2.id:
        raise StoryError("(No story: foreshadowing needs two distinct clues.)")
    for clue in (clue1, clue2):
        if not clue_fits_hideout(clue, hideout):
            raise StoryError(f"(No story: clue '{clue.id}' does not fit {hideout.the}.)")

    world = tell(
        mission=mission,
        hideout=hideout,
        clues=[clue1, clue2],
        tool=tool,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        pal_name=params.pal_name,
        pal_type=params.pal_gender,
        captain_type=params.captain_gender,
    )
    world.get("hero").label = params.hero_name
    world.get("pal").label = params.pal_name
    world.get("hero").traits = [params.hero_trait]
    world.get("pal").traits = [params.pal_trait]

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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, hideout, tool) combos:\n")
        for mission, hideout, tool in combos:
            print(f"  {mission:8} {hideout:12} {tool}")
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
            header = f"### {p.hero_name} & {p.pal_name}: {p.mission} / {p.hideout} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
