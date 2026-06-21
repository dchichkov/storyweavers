#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crime_caribou_tongue_reconciliation_conflict_pirate_tale.py
======================================================================================

A standalone story world for a tiny pirate-flavored domain: two children playing
pirates lose a "treasure" item, one child accuses the other of a pirate crime,
a conflict flares, and then tracks reveal that a real caribou took the missing
thing. The accuser must repair the hurt with a genuine apology or shared act of
care, and the ending image shows whether the friendship feels bright again or
only quietly mended.

The world is deliberately small and constraint-checked:

* Only some treasure items are believable for a curious caribou to take.
* Only places near the north shore plausibly host a wandering caribou.
* Explicitly weak repair methods are known to the world but refused.
* The prose is driven by simulated state: missing item -> accusation -> hurt ->
  clue -> innocence -> repair -> reconciliation.

Run it
------
    python storyworlds/worlds/gpt-5.4/crime_caribou_tongue_reconciliation_conflict_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/crime_caribou_tongue_reconciliation_conflict_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/crime_caribou_tongue_reconciliation_conflict_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crime_caribou_tongue_reconciliation_conflict_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/crime_caribou_tongue_reconciliation_conflict_pirate_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    edible: bool = False
    salty: bool = False
    woolly: bool = False
    living: bool = False
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    mission: str
    send_off: str
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
class Place:
    id: str
    label: str
    detail: str
    surface: str
    supports_caribou: bool = True
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
class Treasure:
    id: str
    label: str
    phrase: str
    stash: str
    clue_text: str
    recovery_text: str
    edible: bool = False
    salty: bool = False
    woolly: bool = False
    attractive: bool = False
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
class Accusation:
    id: str
    line: str
    hurt: int
    cooling: str
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
class Repair:
    id: str
    sense: int
    warmth: int
    line: str
    action: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("accused_id"):
        return out
    accused = world.get(world.facts["accused_id"])
    accuser = world.get(world.facts["accuser_id"])
    if accused.memes["hurt"] < THRESHOLD:
        return out
    sig = ("conflict", accused.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    accuser.memes["worry"] += 1
    world.facts["conflict_live"] = True
    out.append("__conflict__")
    return out


def _r_innocence(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["found"] < THRESHOLD or not world.facts.get("caribou_taken"):
        return out
    sig = ("innocence", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["innocent"] = True
    accused = world.get(world.facts["accused_id"])
    accuser = world.get(world.facts["accuser_id"])
    accused.memes["relief"] += 1
    accuser.memes["guilt"] += 1
    out.append("__innocence__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("repair_made"):
        return out
    if not world.facts.get("innocent"):
        return out
    accuser = world.get(world.facts["accuser_id"])
    accused = world.get(world.facts["accused_id"])
    sig = ("reconcile", accuser.id, accused.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    accuser.memes["care"] += 1
    accused.memes["trust"] += 1
    world.facts["reconciled"] = True
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="innocence", tag="social", apply=_r_innocence),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


def attractive_to_caribou(place: Place, treasure: Treasure) -> bool:
    return place.supports_caribou and treasure.attractive


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def hurt_level(accusation: Accusation, delay: int) -> int:
    return accusation.hurt + delay


def outcome_of(params: "StoryParams") -> str:
    repair = REPAIRS[params.repair]
    tone = ACCUSATIONS[params.accusation]
    return "bright" if repair.warmth >= hurt_level(tone, params.delay) else "quiet"


def predict_caribou(world: World) -> dict:
    sim = world.copy()
    item = sim.get("item")
    if sim.facts.get("caribou_taken"):
        item.meters["missing"] += 1
        item.meters["licked"] += 1
        item.meters["found"] += 1
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "licked": item.meters["licked"] >= THRESHOLD,
        "caribou": sim.facts.get("caribou_taken", False),
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    title_a, title_b = theme.titles
    world.say(
        f"On a bright cold afternoon, {a.id} and {b.id} turned {place.label} into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f"{place.detail} "
        f'"{title_a} {a.id} and {title_b} {b.id}!" {a.id} cried. '
        f'"Today we hunt {theme.mission}!"'
    )


def stash_treasure(world: World, keeper: Entity, item: Entity, treasure: Treasure) -> None:
    item.attrs["keeper"] = keeper.id
    keeper.attrs["keeps"] = item.id
    world.say(
        f"{keeper.id} tucked {treasure.phrase} {treasure.stash}, and both pirates "
        f"agreed that whoever found it later could share first bite or first turn."
    )


def vanish(world: World, treasure: Treasure) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    if world.facts["caribou_taken"]:
        item.meters["licked"] += 1
    world.say(
        f"But when they dashed back to the hiding place, {treasure.phrase} was gone. "
        f"The little chest looked empty enough to make the whole game stop."
    )


def accuse(world: World, accuser: Entity, accused: Entity, tone: Accusation, treasure: Treasure) -> None:
    accused.memes["hurt"] += tone.hurt
    accuser.memes["anger"] += 1
    world.say(
        f'{accuser.id} stared at the empty spot and blurted, "{tone.line}"'
    )
    world.say(
        f"For one hot moment it felt like a real pirate conflict instead of play. "
        f"{accused.id}'s face changed at once."
    )
    propagate(world, narrate=False)
    world.say(tone.cooling)


def protest(world: World, accused: Entity, treasure: Treasure) -> None:
    accused.memes["fairness"] += 1
    world.say(
        f'"I did not take {treasure.phrase}," {accused.id} said. '
        f'{accused.pronoun().capitalize()} pressed {accused.pronoun("possessive")} '
        f'lips together, too hurt to say much more.'
    )


def notice_clue(world: World, accused: Entity, place: Place, treasure: Treasure) -> None:
    pred = predict_caribou(world)
    world.facts["predicted_caribou"] = pred["caribou"]
    if pred["caribou"]:
        world.say(
            f"Then {accused.id} pointed down. Across the {place.surface} ran a line "
            f"of fresh hoofprints, and beside them lay {treasure.clue_text}."
        )


def discover(world: World, place: Place, treasure: Treasure) -> None:
    item = world.get("item")
    item.meters["found"] += 1
    item.attrs["location"] = "gate"
    caribou = world.get("caribou")
    caribou.meters["nearby"] += 1
    world.say(
        f"They followed the prints to the driftwood gate, and there stood a young "
        f"caribou. Its dark nose hovered over {treasure.phrase}, and its rough "
        f"tongue was busy with it."
    )
    world.say(
        f"The mystery opened all at once: no pirate crime had happened between the "
        f"children at all. The wandering caribou had found the treasure first."
    )
    world.say(treasure.recovery_text)
    propagate(world, narrate=False)


def repair_scene(world: World, accuser: Entity, accused: Entity, repair: Repair) -> None:
    world.facts["repair_made"] = True
    accuser.memes["guilt"] += 1
    world.say(
        f'{accuser.id} swallowed hard. "{repair.line}"'
    )
    world.say(repair.action)
    propagate(world, narrate=False)


def bright_ending(world: World, a: Entity, b: Entity, theme: Theme, treasure: Treasure) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["peace"] += 1
    world.say(
        f"Soon the hurt was gone as quickly as a wave sliding back from shore. "
        f"{a.id} and {b.id} tucked {treasure.phrase} into the chest again and "
        f"shared it fairly this time."
    )
    world.say(
        f"When they ran off once more, they did not feel like quarrelling pirates "
        f"anymore. They felt like shipmates again, and {theme.send_off}."
    )


def quiet_ending(world: World, a: Entity, b: Entity, theme: Theme, treasure: Treasure) -> None:
    for kid in (a, b):
        kid.memes["peace"] += 1
    world.say(
        f"{b.id} nodded, and that helped, though the sore spot did not vanish all "
        f"at once. Together they put {treasure.phrase} back in the chest and made "
        f"a new rule: no one would call blame before looking for tracks."
    )
    world.say(
        f"A little later they were sailing their pretend ship again, quieter than "
        f"before but side by side, and {theme.send_off}."
    )
def tell(
    place: Place,
    treasure: Treasure,
    accusation: Accusation,
    repair: Repair,
    accuser_name: str,
    accuser_gender: str,
    accused_name: str,
    accused_gender: str,
    parent_type: ParentType,
    delay: Delay,
    theme=None,
) -> World:
    world = World()
    a = world.add(Entity(id=accuser_name, kind="character", type=accuser_gender, role="accuser"))
    b = world.add(Entity(id=accused_name, kind="character", type=accused_gender, role="accused"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="treasure",
            label=treasure.label,
            edible=treasure.edible,
            salty=treasure.salty,
            woolly=treasure.woolly,
        )
    )
    world.add(Entity(id="caribou", kind="character", type="animal", role="caribou", label="the caribou", living=True))
    world.facts.update(
        theme=theme,
        place=place,
        treasure=treasure,
        accusation=accusation,
        repair=repair,
        accuser_id=a.id,
        accused_id=b.id,
        parent=parent,
        delay=delay,
        caribou_taken=attractive_to_caribou(place, treasure),
        innocent=False,
        reconciled=False,
        repair_made=False,
        conflict_live=False,
    )

    play_setup(world, a, b, theme, place)
    stash_treasure(world, b, item, treasure)

    world.para()
    vanish(world, treasure)
    accuse(world, a, b, accusation, treasure)
    protest(world, b, treasure)

    for _ in range(delay):
        b.memes["hurt"] += 1
        a.memes["worry"] += 1

    world.para()
    notice_clue(world, b, place, treasure)
    discover(world, place, treasure)

    world.para()
    repair_scene(world, a, b, repair)
    if outcome_of(
        StoryParams(
            theme=theme.id,
            place=place.id,
            treasure=treasure.id,
            accusation=accusation.id,
            repair=repair.id,
            accuser=accuser_name,
            accuser_gender=accuser_gender,
            accused=accused_name,
            accused_gender=accused_gender,
            parent=parent_type,
            delay=delay,
            seed=None,
        )
    ) == "bright":
        bright_ending(world, a, b, theme, treasure)
    else:
        quiet_ending(world, a, b, theme, treasure)

    world.facts["outcome"] = outcome_of(
        StoryParams(
            theme=theme.id,
            place=place.id,
            treasure=treasure.id,
            accusation=accusation.id,
            repair=repair.id,
            accuser=accuser_name,
            accuser_gender=accuser_gender,
            accused=accused_name,
            accused_gender=accused_gender,
            parent=parent_type,
            delay=delay,
            seed=None,
        )
    )
    world.facts["accuser"] = a
    world.facts["accused"] = b
    world.facts["item"] = item
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
        scene="a wind-bent pirate cove",
        rig="An old sled was their ship, a broom was their mast, and a striped scarf served as the flag.",
        titles=("Captain", "Scout"),
        mission="the hidden winter treasure",
        send_off="the snowy cove looked wide enough for every adventure in the world",
    ),
    "raiders": Theme(
        id="raiders",
        scene="a frost-blue raider bay",
        rig="A laundry basket was their boat, a mop became their oar, and a mitten tied to a stick fluttered like a brave sea flag.",
        titles=("Captain", "Mate"),
        mission="the lost salt-gold",
        send_off="their ship seemed ready to cut through snow like foam",
    ),
    "islanders": Theme(
        id="islanders",
        scene="a little island harbor of snow",
        rig="A bench was their dock, a shovel was their anchor, and a cardboard box held the pirate spoils.",
        titles=("Captain", "Lookout"),
        mission="the secret chest by the shore",
        send_off="their game sailed on brighter than before",
    ),
}

PLACES = {
    "shore": Place(
        id="shore",
        label="the snowy shore behind the house",
        detail="Beyond the fence, the white hills rolled toward the cold sea.",
        surface="crisp snow",
        supports_caribou=True,
        tags={"snow", "caribou"},
    ),
    "harbor_yard": Place(
        id="harbor_yard",
        label="the little harbor yard",
        detail="Fish racks clicked softly in the wind, and the far hill lay pale and quiet.",
        surface="powdery snow",
        supports_caribou=True,
        tags={"snow", "caribou"},
    ),
    "lantern_walk": Place(
        id="lantern_walk",
        label="the lantern walk by the boathouse",
        detail="A strip of driftwood fence curled beside the path like the edge of a tiny harbor.",
        surface="thin snow",
        supports_caribou=True,
        tags={"snow", "caribou"},
    ),
    "market_alley": Place(
        id="market_alley",
        label="the market alley",
        detail="Barrels, doors, and warm windows stood close together all around them.",
        surface="packed boards",
        supports_caribou=False,
        tags={"town"},
    ),
}

TREASURES = {
    "biscuit": Treasure(
        id="biscuit",
        label="salt biscuit",
        phrase="the captain's salt biscuit",
        stash="inside a little tin under the sled",
        clue_text="a crumb and a wet lick-mark on the tin lid",
        recovery_text="The biscuit was mostly safe, only shiny with one silly lick.",
        edible=True,
        salty=True,
        woolly=False,
        attractive=True,
        tags={"biscuit", "salt", "tongue", "caribou"},
    ),
    "kelp_rope": Treasure(
        id="kelp_rope",
        label="kelp rope",
        phrase="the plaited kelp rope",
        stash="inside the chest behind the bench",
        clue_text="a torn green strand caught in the fence",
        recovery_text="The rope dangled from the caribou's mouth like a sea-green ribbon.",
        edible=False,
        salty=False,
        woolly=False,
        attractive=True,
        tags={"seaweed", "caribou"},
    ),
    "mitten": Treasure(
        id="mitten",
        label="wool mitten",
        phrase="the warm wool mitten full of pretend coins",
        stash="under the striped scarf on the box",
        clue_text="a tuft of wool and a dark print beside it",
        recovery_text="The mitten was damp at the cuff where the caribou had licked the salty wool with its tongue.",
        edible=False,
        salty=False,
        woolly=True,
        attractive=True,
        tags={"mitten", "wool", "tongue", "caribou"},
    ),
    "compass": Treasure(
        id="compass",
        label="brass compass",
        phrase="the shiny brass compass",
        stash="in the toy chest by the wall",
        clue_text="nothing at all",
        recovery_text="It was not the sort of thing a caribou would bother with.",
        edible=False,
        salty=False,
        woolly=False,
        attractive=False,
        tags={"compass"},
    ),
}

ACCUSATIONS = {
    "worried": Accusation(
        id="worried",
        line="Did you take it without telling me? That feels like a pirate crime.",
        hurt=1,
        cooling="The words came out shaky more than mean, but they still landed hard.",
        tags={"conflict"},
    ),
    "snappy": Accusation(
        id="snappy",
        line="You took it! That was a pirate crime, and you know it!",
        hurt=2,
        cooling="The sentence had a sharp tongue on it, and the game turned sour right away.",
        tags={"conflict", "tongue"},
    ),
    "booming": Accusation(
        id="booming",
        line="Thief! You stole the treasure! That was the worst pirate crime of all!",
        hurt=3,
        cooling="The shout rang across the yard. Even the wind seemed to stop and listen.",
        tags={"conflict"},
    ),
}

REPAIRS = {
    "honest_sorry": Repair(
        id="honest_sorry",
        sense=3,
        warmth=2,
        line="I was wrong, and I hurt you. I am sorry for blaming you before I knew the truth.",
        action="Then the accuser put the treasure back into the other child's hands first, to show the apology was real.",
        qa_text="gave a direct apology and admitted the blame had been unfair",
        tags={"apology", "reconciliation"},
    ),
    "share_first": Repair(
        id="share_first",
        sense=2,
        warmth=2,
        line="I should not have blamed you. You can have first share, and I am sorry.",
        action="To prove it, the accuser let the other child choose the first piece and the first turn of the game.",
        qa_text="apologized and gave the other child first share of the treasure",
        tags={"apology", "sharing", "reconciliation"},
    ),
    "search_and_wrap": Repair(
        id="search_and_wrap",
        sense=3,
        warmth=4,
        line="I blamed you too fast. Let me fix it with you, because you did nothing wrong.",
        action="The accuser brushed off the treasure, wrapped it up carefully, and stood shoulder to shoulder with the other child.",
        qa_text="apologized warmly and helped clean up the treasure beside the other child",
        tags={"apology", "care", "reconciliation"},
    ),
    "bossy_mumble": Repair(
        id="bossy_mumble",
        sense=1,
        warmth=1,
        line="Fine. Maybe it was not you. Come on.",
        action="The words were small and grudging, more like an order than an apology.",
        qa_text="mumbled something grudging instead of giving a real apology",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lily", "Nora", "Mia", "Ava", "Ella", "Lucy", "Rose", "Zoe"]
BOY_NAMES = ["Tom", "Finn", "Leo", "Max", "Eli", "Noah", "Sam", "Theo"]


KNOWLEDGE = {
    "caribou": [
        (
            "What is a caribou?",
            "A caribou is a large deer that lives in cold places. It has big hooves for snow and likes to wander while it looks for food."
        )
    ],
    "tongue": [
        (
            "Why would a caribou lick something?",
            "Animals use their tongue to taste and explore. A salty or interesting thing can make a caribou stop and lick it."
        )
    ],
    "apology": [
        (
            "What makes an apology feel real?",
            "A real apology says what was wrong and tries to repair the hurt. It helps the other person feel seen and safe again."
        )
    ],
    "sharing": [
        (
            "Why does sharing help after a fight?",
            "Sharing shows that you care about being fair again. It can help turn a conflict back into friendship."
        )
    ],
    "tracks": [
        (
            "What can hoofprints tell you?",
            "Hoofprints are tracks left by animals' feet. They can show where an animal walked and help you solve a mystery."
        )
    ],
    "crime": [
        (
            "What does the word crime mean in a pretend pirate game?",
            "In a pretend game, children may use the word crime to mean a serious wrong or a theft in the story they are acting out. It is part of the game talk, not a real court case."
        )
    ],
}
KNOWLEDGE_ORDER = ["crime", "caribou", "tongue", "tracks", "apology", "sharing"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for treasure_id, treasure in TREASURES.items():
            if attractive_to_caribou(place, treasure):
                combos.append((place_id, treasure_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    accuser = f["accuser"]
    accused = f["accused"]
    treasure = f["treasure"]
    theme = f["theme"]
    place = f["place"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "crime", "caribou", and "tongue".',
        f"Tell a gentle conflict-and-reconciliation tale where {accuser.id} and {accused.id} play pirates at {place.label}, accuse each other over {treasure.phrase}, and then discover a real caribou caused the trouble.",
        f"Write a complete little adventure where a pretend pirate crime turns into a misunderstanding, and the ending shows the children becoming shipmates again."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    accuser = f["accuser"]
    accused = f["accused"]
    treasure = f["treasure"]
    place = f["place"]
    accusation = f["accusation"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {accuser.id} and {accused.id}, who were pretending to be pirates together. Their game turns serious for a moment when the treasure goes missing."
        ),
        (
            "What started the conflict?",
            f"The conflict started when {treasure.phrase} disappeared from its hiding place and {accuser.id} blamed {accused.id}. {accuser.id} even called it a pirate crime before knowing what had really happened."
        ),
        (
            f"Why was {accused.id} hurt?",
            f"{accused.id} was hurt because the blame came before any proof. The accusation sounded like distrust, so the game stopped feeling safe and playful."
        ),
        (
            "How did they learn the truth?",
            f"They saw hoofprints and another clue in the snow, then followed them to a young caribou. The caribou's rough tongue and the missing treasure showed that the animal, not the other child, had taken it."
        ),
        (
            f"How did {accuser.id} try to fix the problem?",
            f"{accuser.id} {repair.qa_text}. That mattered because the truth alone did not erase the hurt; the friendship still needed care."
        ),
    ]
    if outcome == "bright":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a bright reconciliation. The children shared the treasure fairly and went back to their pirate game as happy shipmates."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a quieter reconciliation. The apology helped, and the children made peace, but they also learned to look for tracks before blaming each other."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"crime", "caribou", "tracks"}
    if "tongue" in f["treasure"].tags or "tongue" in f["accusation"].tags:
        tags.add("tongue")
    tags.add("apology")
    if "sharing" in f["repair"].tags:
        tags.add("sharing")
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
        flags = []
        if e.edible:
            flags.append("edible")
        if e.salty:
            flags.append("salty")
        if e.woolly:
            flags.append("woolly")
        if e.living:
            flags.append("living")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} innocent={world.facts.get('innocent')} reconciled={world.facts.get('reconciled')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    theme: str
    place: str
    treasure: str
    accusation: str
    repair: str
    accuser: str
    accuser_gender: str
    accused: str
    accused_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        theme="pirates",
        place="shore",
        treasure="biscuit",
        accusation="snappy",
        repair="search_and_wrap",
        accuser="Nora",
        accuser_gender="girl",
        accused="Tom",
        accused_gender="boy",
        parent="mother",
        delay=0,
        seed=None,
    ),
    StoryParams(
        theme="raiders",
        place="harbor_yard",
        treasure="mitten",
        accusation="worried",
        repair="honest_sorry",
        accuser="Finn",
        accuser_gender="boy",
        accused="Lily",
        accused_gender="girl",
        parent="father",
        delay=1,
        seed=None,
    ),
    StoryParams(
        theme="islanders",
        place="lantern_walk",
        treasure="kelp_rope",
        accusation="booming",
        repair="share_first",
        accuser="Ava",
        accuser_gender="girl",
        accused="Leo",
        accused_gender="boy",
        parent="mother",
        delay=1,
        seed=None,
    ),
]


def explain_rejection(place: Place, treasure: Treasure) -> str:
    if not place.supports_caribou:
        return (
            f"(No story: {place.label} is too enclosed for a wandering caribou, so "
            f"the missing-treasure mystery would have no believable animal cause.)"
        )
    return (
        f"(No story: {treasure.phrase} is not the sort of thing a caribou would "
        f"take, so the clue-and-discovery turn would not make sense here.)"
    )


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it is too weak to count as a real act of "
        f"reconciliation in this world (sense={repair.sense} < {SENSE_MIN}). "
        f"Try one of: {better}.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(Place, Treasure) :- place(Place), treasure(Treasure), supports_caribou(Place), attractive(Treasure).
sensible_repair(R) :- repair(R), sense(R, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
hurt(H + D) :- chosen_accusation(A), hurt_base(A, H), delay(D).
bright :- chosen_repair(R), warmth(R, W), hurt(V), W >= V.
outcome(bright) :- bright.
outcome(quiet) :- not bright.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.supports_caribou:
            lines.append(asp.fact("supports_caribou", pid))
    for tid, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if treasure.attractive:
            lines.append(asp.fact("attractive", tid))
    for aid, acc in ACCUSATIONS.items():
        lines.append(asp.fact("accusation", aid))
        lines.append(asp.fact("hurt_base", aid, acc.hurt))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("warmth", rid, repair.warmth))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_repair"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_accusation", params.accusation),
            asp.fact("chosen_repair", params.repair),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_repairs = set(asp_sensible_repairs())
    p_repairs = {r.id for r in sensible_repairs()}
    if c_repairs == p_repairs:
        print(f"OK: sensible repairs match ({sorted(c_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_repairs)} python={sorted(p_repairs)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate play, a missing treasure, a caribou clue, and reconciliation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--accusation", choices=ACCUSATIONS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the hurt sits before the apology")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos and sensible repairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.treasure:
        place = PLACES[args.place]
        treasure = TREASURES[args.treasure]
        if not attractive_to_caribou(place, treasure):
            raise StoryError(explain_rejection(place, treasure))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.treasure is None or c[1] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, treasure_id = rng.choice(sorted(combos))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    accusation_id = args.accusation or rng.choice(sorted(ACCUSATIONS))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    accuser, accuser_gender = _pick_kid(rng)
    accused, accused_gender = _pick_kid(rng, avoid=accuser)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        theme=theme_id,
        place=place_id,
        treasure=treasure_id,
        accusation=accusation_id,
        repair=repair_id,
        accuser=accuser,
        accuser_gender=accuser_gender,
        accused=accused,
        accused_gender=accused_gender,
        parent=parent,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        place = PLACES[params.place]
        treasure = TREASURES[params.treasure]
        accusation = ACCUSATIONS[params.accusation]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not attractive_to_caribou(place, treasure):
        raise StoryError(explain_rejection(place, treasure))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        theme=theme,
        place=place,
        treasure=treasure,
        accusation=accusation,
        repair=repair,
        accuser_name=params.accuser,
        accuser_gender=params.accuser_gender,
        accused_name=params.accused,
        accused_gender=params.accused_gender,
        parent_type=params.parent,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible_repair/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, treasure) combos:\n")
        for place_id, treasure_id in combos:
            print(f"  {place_id:14} {treasure_id}")
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
            header = f"### {p.accuser} & {p.accused}: {p.treasure} at {p.place} ({p.accusation}, {p.repair}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
