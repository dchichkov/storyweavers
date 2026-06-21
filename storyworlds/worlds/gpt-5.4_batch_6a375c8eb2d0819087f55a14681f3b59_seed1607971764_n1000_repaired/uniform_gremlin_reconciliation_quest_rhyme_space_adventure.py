#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/uniform_gremlin_reconciliation_quest_rhyme_space_adventure.py
================================================================================================

A standalone story world for a tiny space-adventure domain:

A young cadet in a neat space uniform is sent on a small quest across a bright
station sector. A pocket-sized gremlin snatches an important mission item,
thinking it might help repair or warm its little nest. The cadet follows a trail
of playful rhyme clues through the station, discovers the misunderstanding, and
makes peace by offering the right helpful gift. The gremlin returns the item,
joins the quest, and the ending image proves that both the mission and the
friendship were repaired.

The world enforces one key common-sense constraint:

    The chosen peace-offering must genuinely solve the gremlin's need, and the
    stolen item must be something the gremlin could plausibly mistake for help
    with that same need.

So the engine refuses mismatched stories where the reconciliation would be weak
or unearned.

Run it
------
    python storyworlds/worlds/gpt-5.4/uniform_gremlin_reconciliation_quest_rhyme_space_adventure.py
    python storyworlds/worlds/gpt-5.4/uniform_gremlin_reconciliation_quest_rhyme_space_adventure.py --sector moon_docks --stolen map_strip --need patch --gift foil_patch
    python storyworlds/worlds/gpt-5.4/uniform_gremlin_reconciliation_quest_rhyme_space_adventure.py --gift warm_scarf
    python storyworlds/worlds/gpt-5.4/uniform_gremlin_reconciliation_quest_rhyme_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/uniform_gremlin_reconciliation_quest_rhyme_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/uniform_gremlin_reconciliation_quest_rhyme_space_adventure.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pilot_girl"}
        male = {"boy", "father", "man", "pilot_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Sector:
    id: str
    place: str
    intro: str
    path: str
    beacon: str
    clue_trail: str
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
class StolenItem:
    id: str
    label: str
    phrase: str
    pocket_place: str
    purpose: str
    mistaken_for: set[str] = field(default_factory=set)
    rhyme_line: str = ""
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
class Need:
    id: str
    problem: str
    line: str
    repair_verb: str
    clue_reason: str
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
class Gift:
    id: str
    label: str
    phrase: str
    satisfies: set[str] = field(default_factory=set)
    help_line: str = ""
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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
class StoryParams:
    sector: str
    stolen: str
    need: str
    gift: str
    cadet_name: str
    cadet_gender: str
    grownup: str
    trait: str
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
    def __init__(self, sector: Sector) -> None:
        self.sector = sector
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
        clone = World(self.sector)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_missing_item(world: World) -> list[str]:
    cadet = world.get("cadet")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_item", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cadet.memes["worry"] += 1
    cadet.memes["focus"] += 1
    return []


def _r_repair_trust(world: World) -> list[str]:
    gremlin = world.get("gremlin")
    if gremlin.meters["nest_helped"] < THRESHOLD:
        return []
    sig = ("repair_trust", gremlin.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gremlin.memes["trust"] += 1
    gremlin.memes["relief"] += 1
    return []


def _r_return_item(world: World) -> list[str]:
    cadet = world.get("cadet")
    gremlin = world.get("gremlin")
    item = world.get("item")
    if gremlin.memes["trust"] < THRESHOLD or cadet.memes["offered_help"] < THRESHOLD:
        return []
    sig = ("return_item", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["returned"] += 1
    cadet.memes["relief"] += 1
    cadet.memes["trust"] += 1
    gremlin.memes["guilt"] = 0.0
    return []


def _r_mission_complete(world: World) -> list[str]:
    item = world.get("item")
    beacon = world.get("beacon")
    if item.meters["returned"] < THRESHOLD or beacon.meters["reached"] < THRESHOLD:
        return []
    sig = ("mission_complete", beacon.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    beacon.meters["lit"] += 1
    world.get("cadet").memes["joy"] += 1
    world.get("gremlin").memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_item", tag="emotion", apply=_r_missing_item),
    Rule(name="repair_trust", tag="emotion", apply=_r_repair_trust),
    Rule(name="return_item", tag="social", apply=_r_return_item),
    Rule(name="mission_complete", tag="physical", apply=_r_mission_complete),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SECTORS = {
    "moon_docks": Sector(
        id="moon_docks",
        place="the Moon Docks",
        intro="Blue windows looked out on the stars, and little ships bobbed in their silver clamps.",
        path="past crate towers and under round glass tubes",
        beacon="the moon-lantern beacon",
        clue_trail="a trail of chalky moon dust and tiny rhyme notes",
        ending="the dock lamps blinked on like a row of sleepy moons",
        tags={"space", "station"},
    ),
    "ring_garden": Sector(
        id="ring_garden",
        place="the Ring Garden",
        intro="Leafy vines floated inside clear tubes, and tiny water pearls drifted around the roots.",
        path="between glowing planters and over soft magnet bridges",
        beacon="the garden guide light",
        clue_trail="a trail of silver leaves and tiny rhyme notes",
        ending="the plants shone green and the bridge lights winked in a bright circle",
        tags={"space", "garden"},
    ),
    "comet_bridge": Sector(
        id="comet_bridge",
        place="the Comet Bridge",
        intro="Far below, a band of ice rocks glittered while the bridge floor hummed with gentle light.",
        path="along the humming rail and through wide star doors",
        beacon="the comet bell beacon",
        clue_trail="a trail of sparkly frost and tiny rhyme notes",
        ending="the bridge glowed white and the far comet stones flashed back like mirrors",
        tags={"space", "bridge"},
    ),
}

STOLEN_ITEMS = {
    "map_strip": StolenItem(
        id="map_strip",
        label="star map strip",
        phrase="a folded star map strip",
        pocket_place="the top pocket of the uniform",
        purpose="show the safest little route to the beacon",
        mistaken_for={"patch"},
        rhyme_line="Map in a flap, don't stomp and don't snap.",
        tags={"map", "quest"},
    ),
    "heat_thread": StolenItem(
        id="heat_thread",
        label="heat thread spool",
        phrase="a tiny spool of heat thread",
        pocket_place="the side pocket of the uniform",
        purpose="wrap the beacon switch so small hands could turn it without a cold sting",
        mistaken_for={"warmth"},
        rhyme_line="Thread of red, for a chilly bed.",
        tags={"thread", "warm"},
    ),
    "hum_cell": StolenItem(
        id="hum_cell",
        label="humming cell",
        phrase="a little humming cell",
        pocket_place="a snug inside pocket of the uniform",
        purpose="make the beacon sing its wake-up tune",
        mistaken_for={"power"},
        rhyme_line="Tiny hum, where soft lights come.",
        tags={"battery", "light"},
    ),
}

NEEDS = {
    "patch": Need(
        id="patch",
        problem="a tear in the roof of its tiny nest",
        line="My home had a rip, so I grabbed with a zip.",
        repair_verb="patch the tear",
        clue_reason="The gremlin wanted something flat and shiny to cover the rip.",
        tags={"repair"},
    ),
    "warmth": Need(
        id="warmth",
        problem="a cold nest tucked beside a drafty vent",
        line="My bed felt like ice in the venting night.",
        repair_verb="warm the nest",
        clue_reason="The gremlin wanted something soft or glowing to keep the nest warm.",
        tags={"warm"},
    ),
    "power": Need(
        id="power",
        problem="a dark nest lamp with no gentle buzz left in it",
        line="No glow, no gleam, no lamp for a dream.",
        repair_verb="light the nest lamp",
        clue_reason="The gremlin wanted a small power source for the lamp.",
        tags={"light"},
    ),
}

GIFTS = {
    "foil_patch": Gift(
        id="foil_patch",
        label="foil patch",
        phrase="a neat foil patch kit",
        satisfies={"patch"},
        help_line="A foil patch could cover the rip without taking anyone else's map.",
        tags={"repair"},
    ),
    "warm_scarf": Gift(
        id="warm_scarf",
        label="comet scarf",
        phrase="a tiny comet scarf",
        satisfies={"warmth"},
        help_line="A comet scarf could curl around the nest and keep the draft away.",
        tags={"warm"},
    ),
    "spark_cell": Gift(
        id="spark_cell",
        label="spark cell",
        phrase="a spare spark cell",
        satisfies={"power"},
        help_line="A spare spark cell could wake the nest lamp with a safe little buzz.",
        tags={"light"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Ava", "Nora", "Zoe", "Iris", "Skye"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Theo", "Kai", "Orion", "Eli"]
TRAITS = ["brave", "careful", "curious", "kind", "steady", "bright"]


def valid_combo(stolen: StolenItem, need: Need, gift: Gift) -> bool:
    return need.id in stolen.mistaken_for and need.id in gift.satisfies


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sector_id in SECTORS:
        for stolen_id, stolen in STOLEN_ITEMS.items():
            for need_id, need in NEEDS.items():
                for gift_id, gift in GIFTS.items():
                    if valid_combo(stolen, need, gift):
                        combos.append((sector_id, stolen_id, need_id, gift_id))
    return combos


def explain_rejection(stolen: StolenItem, need: Need, gift: Gift) -> str:
    if need.id not in stolen.mistaken_for:
        return (
            f"(No story: a gremlin needing {need.problem} would not sensibly steal "
            f"{stolen.phrase}. The misunderstanding has to fit the need.)"
        )
    if need.id not in gift.satisfies:
        return (
            f"(No story: {gift.phrase} would not really help with {need.problem}. "
            f"The peace-offering must solve the gremlin's need for the reconciliation to feel earned.)"
        )
    return "(No story: this combination does not make a reasonable quest.)"


def predict_return(world: World, gift: Gift) -> dict:
    sim = world.copy()
    gremlin = sim.get("gremlin")
    cadet = sim.get("cadet")
    if world.facts["need"].id in gift.satisfies:
        gremlin.meters["nest_helped"] += 1
        cadet.memes["offered_help"] += 1
        propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "returned": item.meters["returned"] >= THRESHOLD,
        "trust": gremlin.memes["trust"],
    }


def introduction(world: World, cadet: Entity, grownup: Entity, item: Entity, sector: Sector) -> None:
    world.say(
        f"{cadet.id} zipped up a bright space uniform with a silver badge on the chest. "
        f"{sector.intro}"
    )
    world.say(
        f'"Cadet {cadet.id}," said {cadet.pronoun("possessive")} {grownup.label_word}, '
        f'"please carry {item.label} to {sector.beacon} in {sector.place}."'
    )
    cadet.memes["duty"] += 1
    cadet.memes["joy"] += 1


def mission_setup(world: World, cadet: Entity, item_cfg: StolenItem, sector: Sector) -> None:
    world.say(
        f"{item_cfg.phrase.capitalize()} rested in {item_cfg.pocket_place}, ready to "
        f"{item_cfg.purpose}."
    )
    world.say(
        f"{cadet.id} set off {sector.path}, feeling very grand and helpful in the tidy uniform."
    )


def snatch(world: World, cadet: Entity, gremlin: Entity, item: Entity, item_cfg: StolenItem) -> None:
    item.meters["missing"] += 1
    gremlin.memes["guilt"] += 1
    world.facts["snatcher"] = gremlin
    propagate(world, narrate=False)
    world.say(
        f"Then a tiny gremlin popped from behind a pipe, twinkly-eyed and quick as a blink. "
        f"With one whiskery zip, it tugged {item_cfg.phrase} from {item_cfg.pocket_place} and vanished."
    )
    if cadet.memes["worry"] >= THRESHOLD:
        world.say(
            f"{cadet.id} gasped. Without it, the quest to reach {world.sector.beacon} might fail."
        )


def first_rhyme(world: World, cadet: Entity, item_cfg: StolenItem, sector: Sector) -> None:
    world.say(
        f"On the floor lay the first clue: {sector.clue_trail}. One note read, "
        f'"{item_cfg.rhyme_line}"'
    )
    cadet.memes["curiosity"] += 1
    cadet.memes["hope"] += 1


def chase(world: World, cadet: Entity, sector: Sector) -> None:
    world.say(
        f"So the cadet hurried on, not stomping, not shouting, but following the clues "
        f"{sector.path}. The little rhyme trail made the chase feel more like a puzzle than a fight."
    )
    cadet.meters["distance"] += 1


def second_rhyme(world: World, need: Need) -> None:
    world.say(
        f"Behind a round vent, another note fluttered. It said, "
        f'"{need.line}"'
    )


def discovery(world: World, cadet: Entity, gremlin: Entity, need: Need, gift: Gift) -> None:
    pred = predict_return(world, gift)
    world.facts["predicted_return"] = pred["returned"]
    world.say(
        f"At last {cadet.id} found the gremlin in a little nest nook. The poor thing looked up and pointed "
        f"to {need.problem}."
    )
    world.say(
        f'"I did a bad snatch," the gremlin whispered. "I thought your thing could help." '
        f"{need.clue_reason}"
    )
    cadet.memes["anger"] = 0.0
    cadet.memes["understanding"] += 1


def offer_help(world: World, cadet: Entity, gremlin: Entity, gift: Gift, need: Need) -> None:
    cadet.memes["offered_help"] += 1
    gremlin.meters["nest_helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{cadet.id} took a slow breath and said, "You should not grab from someone\'s uniform pocket. '
        f'But I can still help."'
    )
    world.say(
        f"{cadet.pronoun().capitalize()} offered {gift.phrase}. {gift.help_line} "
        f"Together they used it to {need.repair_verb}."
    )


def reconciliation(world: World, cadet: Entity, gremlin: Entity, item: Entity) -> None:
    propagate(world, narrate=False)
    if item.meters["returned"] < THRESHOLD:
        raise StoryError("(Internal story failure: the item should have been returned after help.)")
    world.say(
        f'The gremlin\'s ears drooped. "I am sorry," it said. "I was scared for my nest."'
    )
    world.say(
        f'{cadet.id} nodded. "I was upset too, but now we understand each other." '
        f"The gremlin placed the missing item back into {cadet.pronoun('possessive')} hands."
    )


def finish_quest(world: World, cadet: Entity, gremlin: Entity, beacon: Entity, item_cfg: StolenItem, sector: Sector) -> None:
    beacon.meters["reached"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Side by side, cadet and gremlin hurried to {sector.beacon}. "
        f"With {item_cfg.phrase} safely back, they finished the little mission at last."
    )
    if beacon.meters["lit"] >= THRESHOLD:
        world.say(
            f"Warm light spilled over {sector.place}, and {sector.ending}."
        )
    world.say(
        f'The gremlin chimed a last rhyme: "Friend to friend, we mend and send." '
        f'{cadet.id} laughed, and the quest ended brighter than it began.'
    )


def tell(
    sector: Sector,
    stolen: StolenItem,
    need: Need,
    gift: Gift,
    cadet_name: str = "Luna",
    cadet_gender: str = "girl",
    grownup_type: str = "mother",
    trait: str = "kind",
) -> World:
    world = World(sector=sector)
    cadet = world.add(
        Entity(
            id="cadet",
            kind="character",
            type="pilot_girl" if cadet_gender == "girl" else "pilot_boy",
            label=cadet_name,
            role="cadet",
            attrs={"name": cadet_name, "trait": trait},
            tags={"cadet"},
        )
    )
    gremlin = world.add(
        Entity(
            id="gremlin",
            kind="character",
            type="gremlin",
            label="the gremlin",
            role="gremlin",
            tags={"gremlin"},
        )
    )
    grownup = world.add(
        Entity(
            id="grownup",
            kind="character",
            type=grownup_type,
            label="the grown-up",
            role="grownup",
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="tool",
            label=stolen.label,
            role="mission_item",
            tags=set(stolen.tags),
        )
    )
    beacon = world.add(
        Entity(
            id="beacon",
            kind="thing",
            type="beacon",
            label=sector.beacon,
            role="beacon",
            tags={"beacon"},
        )
    )
    peace_gift = world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift.label,
            role="gift",
            tags=set(gift.tags),
        )
    )

    world.facts.update(
        sector=sector,
        stolen=stolen,
        need=need,
        gift=gift,
        cadet=cadet,
        gremlin=gremlin,
        grownup=grownup,
        item=item,
        beacon=beacon,
        gift_entity=peace_gift,
    )

    introduction(world, cadet, grownup, item, sector)
    mission_setup(world, cadet, stolen, sector)

    world.para()
    snatch(world, cadet, gremlin, item, stolen)
    first_rhyme(world, cadet, stolen, sector)
    chase(world, cadet, sector)
    second_rhyme(world, need)

    world.para()
    discovery(world, cadet, gremlin, need, gift)
    offer_help(world, cadet, gremlin, gift, need)
    reconciliation(world, cadet, gremlin, item)

    world.para()
    finish_quest(world, cadet, gremlin, beacon, stolen, sector)

    world.facts.update(
        outcome="reconciled" if item.meters["returned"] >= THRESHOLD and beacon.meters["lit"] >= THRESHOLD else "failed",
        reconciled=item.meters["returned"] >= THRESHOLD,
        mission_done=beacon.meters["lit"] >= THRESHOLD,
        rhyme_count=3,
    )
    return world


KNOWLEDGE = {
    "gremlin": [
        (
            "What is a gremlin in this story world?",
            "A gremlin is a tiny make-believe creature that can be mischievous but is not always mean. In this world, the gremlin makes a bad choice because it is worried about its nest.",
        )
    ],
    "uniform": [
        (
            "What is a uniform?",
            "A uniform is a special set of clothes people wear for a certain job or team. It helps show what role they have and can help them keep important tools with them.",
        )
    ],
    "map": [
        (
            "What does a map help you do?",
            "A map helps you find the right way to go. It shows routes and keeps travelers from getting lost.",
        )
    ],
    "battery": [
        (
            "What does a small power cell do?",
            "A power cell stores energy for a tool or light. When it is connected safely, it can make something glow or hum.",
        )
    ],
    "warm": [
        (
            "Why would a tiny nest need warmth?",
            "A nest needs warmth so the creature inside can rest safely and comfortably. Cold drafts can make a small home hard to sleep in.",
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something means to fix what is broken or torn. After a repair, the thing works better or feels safe again.",
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a signal light that helps guide people or shows them where to go. In a space adventure, it can shine so travelers know the path is safe.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching sounds, like light and bright. Rhymes can make clues easier to remember.",
        )
    ],
    "apology": [
        (
            "Why does saying sorry matter?",
            "Saying sorry matters because it shows you know you hurt or upset someone. A true apology helps people begin to trust each other again.",
        )
    ],
}

KNOWLEDGE_ORDER = ["gremlin", "uniform", "map", "battery", "warm", "repair", "beacon", "rhyme", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cadet = f["cadet"]
    sector = f["sector"]
    stolen = f["stolen"]
    need = f["need"]
    return [
        (
            f'Write a short space adventure for a 3-to-5-year-old that includes the words '
            f'"uniform" and "gremlin", with a quest, a misunderstanding, and a happy reconciliation.'
        ),
        (
            f"Tell a gentle story where a cadet named {cadet.label} in {sector.place} follows rhyme clues "
            f"after a gremlin steals {stolen.phrase}, then learns the creature only wanted help with {need.problem}."
        ),
        (
            f"Write a child-facing quest story with little rhymes along the way, where kindness repairs a problem "
            f"faster than anger."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cadet = f["cadet"]
    gremlin = f["gremlin"]
    sector = f["sector"]
    stolen = f["stolen"]
    need = f["need"]
    gift = f["gift"]
    grownup = f["grownup"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {cadet.label}, a young cadet in a space uniform, and a tiny gremlin in {sector.place}. "
            f"The story also includes {cadet.pronoun('possessive')} {grownup.label_word}, who gives the quest at the start.",
        ),
        (
            f"What was {cadet.label}'s quest?",
            f"{cadet.label}'s quest was to carry {stolen.phrase} to {sector.beacon}. "
            f"The item mattered because it would help {stolen.purpose}.",
        ),
        (
            "What went wrong at first?",
            f"A gremlin snatched the important item from the cadet's uniform pocket and ran away. "
            f"That made the quest feel shaky because the beacon work could not be finished without it.",
        ),
        (
            "Why did the gremlin take the item?",
            f"The gremlin took it because it was worried about {need.problem}. "
            f"It made a wrong guess and thought the cadet's item might solve that problem.",
        ),
        (
            "How did the cadet find the gremlin?",
            f"{cadet.label} followed a trail of rhyme clues through {sector.place}. "
            f"The rhymes turned the chase into a puzzle, so the cadet kept looking instead of giving up.",
        ),
        (
            "How did they make peace?",
            f"{cadet.label} listened, understood the gremlin's problem, and offered {gift.phrase} instead. "
            f"That gift really helped, so the gremlin said sorry and returned the missing item.",
        ),
        (
            "How did the story end?",
            f"They reached {sector.beacon} together and finished the mission. "
            f"The bright ending shows that the quest was completed and the new friendship was real.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"gremlin", "uniform", "beacon", "rhyme", "apology"}
    stolen = f["stolen"]
    need = f["need"]
    if "map" in stolen.tags:
        tags.add("map")
    if "battery" in stolen.tags:
        tags.add("battery")
    if "warm" in stolen.tags or "warm" in need.tags:
        tags.add("warm")
    if "repair" in need.tags or "repair" in f["gift"].tags:
        tags.add("repair")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        sector="moon_docks",
        stolen="map_strip",
        need="patch",
        gift="foil_patch",
        cadet_name="Luna",
        cadet_gender="girl",
        grownup="mother",
        trait="kind",
    ),
    StoryParams(
        sector="ring_garden",
        stolen="heat_thread",
        need="warmth",
        gift="warm_scarf",
        cadet_name="Milo",
        cadet_gender="boy",
        grownup="father",
        trait="careful",
    ),
    StoryParams(
        sector="comet_bridge",
        stolen="hum_cell",
        need="power",
        gift="spark_cell",
        cadet_name="Mira",
        cadet_gender="girl",
        grownup="mother",
        trait="bright",
    ),
    StoryParams(
        sector="moon_docks",
        stolen="hum_cell",
        need="power",
        gift="spark_cell",
        cadet_name="Theo",
        cadet_gender="boy",
        grownup="father",
        trait="steady",
    ),
    StoryParams(
        sector="ring_garden",
        stolen="map_strip",
        need="patch",
        gift="foil_patch",
        cadet_name="Skye",
        cadet_gender="girl",
        grownup="mother",
        trait="curious",
    ),
]


ASP_RULES = r"""
reasonable(Stolen, Need, Gift) :- mistaken_for(Stolen, Need), satisfies(Gift, Need).
valid(Sector, Stolen, Need, Gift) :- sector(Sector), stolen(Stolen), need(Need), gift(Gift),
                                     reasonable(Stolen, Need, Gift).

outcome(reconciled) :- chosen(Sector, Stolen, Need, Gift), valid(Sector, Stolen, Need, Gift).
:- chosen(Sector, Stolen, Need, Gift), not valid(Sector, Stolen, Need, Gift).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sector_id in SECTORS:
        lines.append(asp.fact("sector", sector_id))
    for stolen_id, stolen in STOLEN_ITEMS.items():
        lines.append(asp.fact("stolen", stolen_id))
        for need_id in sorted(stolen.mistaken_for):
            lines.append(asp.fact("mistaken_for", stolen_id, need_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for need_id in sorted(gift.satisfies):
            lines.append(asp.fact("satisfies", gift_id, need_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen", params.sector, params.stolen, params.need, params.gift),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "invalid"


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

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            continue

    for params in cases:
        out = asp_outcome(params)
        if out != "reconciled":
            rc = 1
            print("ASP outcome mismatch or invalid scenario:", params)

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke test")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cadet, a gremlin, a rhyme trail, and a reconciled space quest."
    )
    ap.add_argument("--sector", choices=SECTORS)
    ap.add_argument("--stolen", choices=STOLEN_ITEMS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--cadet-name")
    ap.add_argument("--cadet-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stolen and args.need and args.gift:
        stolen = STOLEN_ITEMS[args.stolen]
        need = NEEDS[args.need]
        gift = GIFTS[args.gift]
        if not valid_combo(stolen, need, gift):
            raise StoryError(explain_rejection(stolen, need, gift))

    combos = [
        combo
        for combo in valid_combos()
        if (args.sector is None or combo[0] == args.sector)
        and (args.stolen is None or combo[1] == args.stolen)
        and (args.need is None or combo[2] == args.need)
        and (args.gift is None or combo[3] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sector_id, stolen_id, need_id, gift_id = rng.choice(sorted(combos))
    cadet_gender = args.cadet_gender or rng.choice(["girl", "boy"])
    cadet_name = args.cadet_name or rng.choice(GIRL_NAMES if cadet_gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        sector=sector_id,
        stolen=stolen_id,
        need=need_id,
        gift=gift_id,
        cadet_name=cadet_name,
        cadet_gender=cadet_gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        sector = SECTORS[params.sector]
        stolen = STOLEN_ITEMS[params.stolen]
        need = NEEDS[params.need]
        gift = GIFTS[params.gift]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not valid_combo(stolen, need, gift):
        raise StoryError(explain_rejection(stolen, need, gift))

    world = tell(
        sector=sector,
        stolen=stolen,
        need=need,
        gift=gift,
        cadet_name=params.cadet_name,
        cadet_gender=params.cadet_gender,
        grownup_type=params.grownup,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sector, stolen, need, gift) combos:\n")
        for sector_id, stolen_id, need_id, gift_id in combos:
            print(f"  {sector_id:12} {stolen_id:10} {need_id:8} {gift_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.cadet_name}: {p.sector} ({p.stolen} / {p.need} / {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
