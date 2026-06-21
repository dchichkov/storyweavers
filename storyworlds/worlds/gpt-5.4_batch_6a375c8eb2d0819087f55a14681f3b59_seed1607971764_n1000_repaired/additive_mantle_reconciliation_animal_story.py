#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/additive_mantle_reconciliation_animal_story.py
=========================================================================

A standalone story world for a small animal tale about a bright craft project,
a foolish extra additive, a stained mantle, and a real reconciliation.

Reference premise
-----------------
Two young animals want to make something beautiful for an elder's festival
mantle. One of them adds too much of a color additive after being warned not to.
The mixture splashes onto the mantle. The elder feels sad, the children feel
guilty, and then they tell the truth, help repair the damage, and make peace.

Run it
------
    python storyworlds/worlds/gpt-5.4/additive_mantle_reconciliation_animal_story.py
    python storyworlds/worlds/gpt-5.4/additive_mantle_reconciliation_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/additive_mantle_reconciliation_animal_story.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/additive_mantle_reconciliation_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/additive_mantle_reconciliation_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/additive_mantle_reconciliation_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    material: str = ""
    heirloom: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Duo:
    id: str
    animal_plural: str
    children_word: str
    home: str
    festival: str
    craft_place: str
    opening: str
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
class Additive:
    id: str
    label: str
    bowl_text: str
    warning_text: str
    splash_text: str
    severity: int
    stain_kind: str
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
class Mantle:
    id: str
    label: str
    phrase: str
    material: str
    beloved_text: str
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
class Cleanup:
    id: str
    label: str
    sense: int
    power: int
    works_on: set[str]
    action_text: str
    success_text: str
    partial_text: str
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


@dataclass
class Gift:
    id: str
    label: str
    make_text: str
    end_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_stain_hurts(world: World) -> list[str]:
    mantle = world.get("mantle")
    if mantle.meters["stained"] < THRESHOLD:
        return []
    sig = ("stain_hurts", "mantle")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder = world.get(world.facts["elder_id"])
    elder.memes["sad"] += 1
    for kid in world.kids():
        kid.memes["guilt"] += 1
    world.get("room").meters["tension"] += 1
    return ["__stain__"]


def _r_repair_softens(world: World) -> list[str]:
    mantle = world.get("mantle")
    repaired = mantle.meters["clean"] >= THRESHOLD or mantle.meters["patched"] >= THRESHOLD
    if not repaired:
        return []
    elder = world.get(world.facts["elder_id"])
    if not (world.facts.get("confessed") and world.facts.get("apologized")):
        return []
    sig = ("repair_softens", "mantle")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["warmth"] += 1
    elder.memes["sad"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["guilt"] = 0.0
        kid.memes["trust"] += 1
    world.get("room").meters["tension"] = 0.0
    return ["__peace__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stain_hurts", tag="social", apply=_r_stain_hurts),
    Rule(name="repair_softens", tag="social", apply=_r_repair_softens),
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


def cleanup_works(cleanup: Cleanup, mantle: Mantle) -> bool:
    return mantle.material in cleanup.works_on


def sensible_cleanups() -> list[Cleanup]:
    return [c for c in CLEANUPS.values() if c.sense >= SENSE_MIN]


def spill_severity(additive: Additive, delay: int) -> int:
    return additive.severity + delay


def is_restored(cleanup: Cleanup, additive: Additive, delay: int) -> bool:
    return cleanup.power >= spill_severity(additive, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for duo_id in DUOS:
        for add_id, additive in ADDITIVES.items():
            for mantle_id, mantle in MANTLES.items():
                for cleanup_id, cleanup in CLEANUPS.items():
                    if cleanup_works(cleanup, mantle) and cleanup.sense >= SENSE_MIN:
                        combos.append((duo_id, add_id, mantle_id, cleanup_id))
    return combos


def explain_cleanup_rejection(cleanup: Cleanup, mantle: Mantle) -> str:
    if cleanup.sense < SENSE_MIN:
        better = ", ".join(sorted(c.id for c in sensible_cleanups()))
        return (
            f"(Refusing cleanup '{cleanup.id}': it is a poor, rough choice for a child-facing "
            f"story (sense={cleanup.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {cleanup.label} is not a good way to clean {mantle.phrase}. "
        f"That mantle is made of {mantle.material}, so the repair should match the material.)"
    )


def outcome_of(params: "StoryParams") -> str:
    cleanup = CLEANUPS[params.cleanup]
    additive = ADDITIVES[params.additive]
    return "restored" if is_restored(cleanup, additive, params.delay) else "mended"


def predict_spill(world: World, additive_id: str) -> dict:
    sim = world.copy()
    additive = ADDITIVES[additive_id]
    _do_spill(sim, additive, narrate=False)
    elder = sim.get(sim.facts["elder_id"])
    mantle = sim.get("mantle")
    return {
        "stained": mantle.meters["stained"] >= THRESHOLD,
        "sad": elder.memes["sad"] >= THRESHOLD,
    }


def _do_spill(world: World, additive: Additive, narrate: bool = True) -> None:
    mantle = world.get("mantle")
    mantle.meters["stained"] += 1
    mantle.meters["mess"] += float(additive.severity)
    propagate(world, narrate=narrate)


def introduce(world: World, duo: Duo, a: Entity, b: Entity, elder: Entity, mantle: Mantle) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"In {duo.home}, two young {duo.animal_plural}, {a.id} and {b.id}, were helping "
        f"{elder.id} get ready for {duo.festival}. {duo.opening}"
    )
    world.say(
        f"Across a low stump table lay {mantle.phrase}. {elder.id} loved that mantle because "
        f"{mantle.beloved_text}"
    )
    world.say(
        f"{a.id} and {b.id} wanted to paint a tiny border of berries and stars along the hem "
        f"to make the old mantle shine during the parade."
    )


def need_additive(world: World, additive: Additive, b: Entity) -> None:
    world.say(
        f"On the table stood a bowl of berry color and a little jar of {additive.label}, "
        f"an additive the young helpers were only supposed to use one pinch at a time."
    )
    world.say(
        f'{b.id} read the note tied around the jar. "{additive.warning_text}," {b.pronoun()} said.'
    )


def tempt(world: World, additive: Additive, a: Entity) -> None:
    a.memes["eagerness"] += 1
    world.say(
        f"But {a.id} stared at the bowl and thought a brighter swirl would look even better. "
        f'"Just a little more {additive.label}," {a.pronoun()} whispered.'
    )


def warn(world: World, additive: Additive, a: Entity, b: Entity) -> None:
    pred = predict_spill(world, additive.id)
    world.facts["predicted_spill"] = pred["stained"]
    b.memes["caution"] += 1
    extra = " It could jump right out of the bowl." if pred["stained"] else ""
    world.say(
        f'{b.id} put a paw over the jar. "Please do not pour more. This additive is meant for one '
        f'small pinch, and {elder_name(world)}\'s mantle is right here.{extra}"'
    )


def defy(world: World, additive: Additive, a: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f"{a.id} meant to be quick and clever, not unkind. Still, {a.pronoun()} tipped in one "
        f"extra spoonful."
    )
    world.say(additive.bowl_text)


def spill(world: World, additive: Additive, mantle: Mantle) -> None:
    _do_spill(world, additive, narrate=False)
    world.say(
        f"Then the bowl burped, foamed, and {additive.splash_text} onto {mantle.phrase}. "
        f"A crooked stain spread across the soft cloth."
    )
    propagate(world, narrate=False)


def distress(world: World, elder: Entity, a: Entity, b: Entity, mantle: Mantle) -> None:
    world.say(
        f"{elder.id} turned from the shelf and saw the mark. {elder.pronoun().capitalize()} did not shout. "
        f"{elder.pronoun().capitalize()} only touched the damp place on the mantle and went very still."
    )
    if elder.heirloom:
        world.say(
            f'"Oh," {elder.id} said softly. "This mantle has been with my family for many seasons."'
        )
    world.say(
        f"{a.id}'s ears drooped. {b.id} stared at the floorboards. The room felt much smaller than before."
    )


def confess(world: World, a: Entity, b: Entity) -> None:
    world.facts["confessed"] = True
    a.memes["honesty"] += 1
    b.memes["honesty"] += 1
    world.say(
        f'"I did it," {a.id} said at last. "I used too much additive after {b.id} warned me."'
    )
    world.say(
        f'"And I should have fetched help sooner," {b.id} added. "We are sorry."'
    )


def choose_cleanup(world: World, cleanup: Cleanup, mantle: Mantle, elder: Entity) -> None:
    world.say(
        f"{elder.id} took a slow breath and knelt by the stump table. "
        f'"We cannot undo the splash," {elder.pronoun()} said, "but we can make a careful start."'
    )
    world.say(cleanup.action_text.replace("{mantle}", mantle.label))


def repair(world: World, cleanup: Cleanup, additive: Additive, mantle: Mantle, gift: Gift) -> None:
    mantle_ent = world.get("mantle")
    if is_restored(cleanup, additive, world.facts["delay"]):
        mantle_ent.meters["clean"] += 1
        mantle_ent.meters["stained"] = 0.0
        world.say(cleanup.success_text.replace("{mantle}", mantle.label))
        world.facts["repair_outcome"] = "restored"
    else:
        mantle_ent.meters["patched"] += 1
        mantle_ent.meters["stained"] = 0.0
        world.say(cleanup.partial_text.replace("{mantle}", mantle.label))
        world.say(gift.make_text.replace("{mantle}", mantle.label))
        world.facts["repair_outcome"] = "mended"
    propagate(world, narrate=False)


def reconcile(world: World, elder: Entity, a: Entity, b: Entity, mantle: Mantle, gift: Gift) -> None:
    world.facts["apologized"] = True
    propagate(world, narrate=False)
    outcome = world.facts["repair_outcome"]
    if outcome == "restored":
        world.say(
            f'{elder.id} opened {elder.pronoun("possessive")} arms, and the two little helpers hurried in. '
            f'"Thank you for telling the truth and helping to fix it," {elder.pronoun()} said.'
        )
        world.say(
            f'"We will ask before we touch the additive again," {a.id} and {b.id} promised.'
        )
        world.say(
            f"That evening {elder.id} wore the mantle to {world.facts['duo'].festival}, and the small "
            f"painted stars near the hem looked gentle and bright instead of wild."
        )
    else:
        world.say(
            f'{elder.id} smoothed the mended place and smiled a little. "It is not exactly the same," '
            f'{elder.pronoun()} said, "but it is honest, and it was repaired with loving paws."'
        )
        world.say(
            f"{a.id} leaned against {elder.id}, and {b.id} touched the new trim. The mistake had become a "
            f"careful promise they could all see."
        )
        world.say(
            f"That evening {elder.id} wore the mantle to {world.facts['duo'].festival}, and {gift.end_text}"
        )


def elder_name(world: World) -> str:
    return str(world.facts.get("elder_name", "the elder"))


def tell(
    duo: Duo,
    additive: Additive,
    mantle_cfg: Mantle,
    cleanup: Cleanup,
    gift: Gift,
    *,
    instigator: str = "Pip",
    cautioner: str = "Moss",
    elder_name_value: str = "Old Fern",
    delay: int = 0,
    relation: str = "friends",
) -> World:
    world = World()
    world.facts["delay"] = delay
    world.facts["confessed"] = False
    world.facts["apologized"] = False
    world.facts["elder_name"] = elder_name_value
    world.facts["duo"] = duo

    a = world.add(Entity(
        id=instigator,
        kind="character",
        type="animal_child",
        label=instigator,
        role="instigator",
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type="animal_child",
        label=cautioner,
        role="cautioner",
        attrs={"relation": relation},
    ))
    elder = world.add(Entity(
        id=elder_name_value,
        kind="character",
        type="animal_elder",
        label=elder_name_value,
        role="elder",
        heirloom=True,
    ))
    room = world.add(Entity(
        id="room",
        type="place",
        label=duo.craft_place,
    ))
    mantle = world.add(Entity(
        id="mantle",
        type="mantle",
        label=mantle_cfg.label,
        material=mantle_cfg.material,
        heirloom=True,
    ))
    world.facts["elder_id"] = elder.id

    introduce(world, duo, a, b, elder, mantle_cfg)
    need_additive(world, additive, b)

    world.para()
    tempt(world, additive, a)
    warn(world, additive, a, b)
    defy(world, additive, a)

    world.para()
    spill(world, additive, mantle_cfg)
    distress(world, elder, a, b, mantle_cfg)

    world.para()
    confess(world, a, b)
    choose_cleanup(world, cleanup, mantle_cfg, elder)
    repair(world, cleanup, additive, mantle_cfg, gift)

    world.para()
    reconcile(world, elder, a, b, mantle_cfg, gift)

    world.facts.update(
        instigator=a,
        cautioner=b,
        elder=elder,
        mantle_cfg=mantle_cfg,
        additive=additive,
        cleanup=cleanup,
        gift=gift,
        relation=relation,
        outcome=world.facts["repair_outcome"],
        mantle_restored=world.facts["repair_outcome"] == "restored",
        mantle_mended=world.facts["repair_outcome"] == "mended",
        stain_happened=True,
    )
    return world


DUOS = {
    "squirrels": Duo(
        id="squirrels",
        animal_plural="squirrels",
        children_word="kits",
        home="the hollow oak",
        festival="the Lantern Leaf Walk",
        craft_place="the acorn-workroom",
        opening="Morning light slipped through the round window and made the paint jars glow like little suns.",
        tags={"forest", "festival"},
    ),
    "rabbits": Duo(
        id="rabbits",
        animal_plural="rabbits",
        children_word="bunnies",
        home="the bramble burrow",
        festival="the Moonpetal March",
        craft_place="the root-cellar table",
        opening="A kettle hummed in the corner, and every shelf smelled of clover and clean cloth.",
        tags={"burrow", "festival"},
    ),
    "mice": Duo(
        id="mice",
        animal_plural="mice",
        children_word="mice",
        home="the reed cottage",
        festival="the Firefly Evening",
        craft_place="the pebble-topped bench",
        opening="Tiny lamps made gold dots on the walls, and brushes stood in a cup like a little meadow.",
        tags={"cottage", "festival"},
    ),
}

ADDITIVES = {
    "sparkle_dust": Additive(
        id="sparkle_dust",
        label="sparkle dust",
        bowl_text="At once the color puffed up in a fizzy silver cloud.",
        warning_text="one pinch only",
        splash_text="spattered silver-flecked berry paint",
        severity=2,
        stain_kind="bright flecks",
        tags={"additive", "sparkle"},
    ),
    "pine_resin": Additive(
        id="pine_resin",
        label="pine-resin additive",
        bowl_text="The color turned thick and sticky and began to pop in slow green blips.",
        warning_text="stir gently and never add extra",
        splash_text="flung a sticky ribbon of green-brown color",
        severity=3,
        stain_kind="sticky smear",
        tags={"additive", "resin"},
    ),
    "flower_milk": Additive(
        id="flower_milk",
        label="flower-milk additive",
        bowl_text="The color rose in a pink froth, light as bubbles and twice as busy.",
        warning_text="just one soft spoon-tip",
        splash_text="splashed rosy foam",
        severity=1,
        stain_kind="rosy foam",
        tags={"additive", "dye"},
    ),
}

MANTLES = {
    "moss": Mantle(
        id="moss",
        label="moss mantle",
        phrase="a soft moss mantle",
        material="mosscloth",
        beloved_text="its green nap had been brushed smooth by many gentle hands",
        tags={"mantle", "cloth"},
    ),
    "wool": Mantle(
        id="wool",
        label="wool mantle",
        phrase="a warm wool mantle",
        material="wool",
        beloved_text="its edges still held the neat stitches of an old winter gift",
        tags={"mantle", "wool"},
    ),
    "feather": Mantle(
        id="feather",
        label="feather mantle",
        phrase="a pale feather mantle",
        material="feather",
        beloved_text="it was light enough to sway like a whisper when its owner walked",
        tags={"mantle", "feather"},
    ),
}

CLEANUPS = {
    "dew_rinse": Cleanup(
        id="dew_rinse",
        label="a bowl of warm dew-water",
        sense=3,
        power=2,
        works_on={"mosscloth", "wool"},
        action_text="Together they dabbed at the {mantle} with a bowl of warm dew-water and soft thistledown cloths.",
        success_text="Little by little, the stain loosened until the {mantle} looked soft and clear again.",
        partial_text="The worst of the stain lifted, but a cloudy mark stayed behind on the {mantle}.",
        qa_text="They dabbed it clean with warm dew-water and soft cloths",
        tags={"cleaning", "water"},
    ),
    "comb_brush": Cleanup(
        id="comb_brush",
        label="a feather comb and dry brush",
        sense=3,
        power=2,
        works_on={"feather", "mosscloth"},
        action_text="Together they used a feather comb and a dry brush, teasing the color out of the {mantle} a little at a time.",
        success_text="The color dusted away from the {mantle}, and the soft fibers fluffed back into place.",
        partial_text="Most of the color came free, but one pale streak still lingered on the {mantle}.",
        qa_text="They brushed and combed the color out very carefully",
        tags={"cleaning", "brush"},
    ),
    "soap_foam": Cleanup(
        id="soap_foam",
        label="meadow-soap foam",
        sense=3,
        power=3,
        works_on={"wool", "mosscloth"},
        action_text="Together they worked meadow-soap foam into the {mantle} with tiny circles, then blotted the suds away.",
        success_text="Soon the stain faded almost entirely, and the {mantle} looked ready for the festival once more.",
        partial_text="Even after the careful foam, a faint memory of the splash remained on the {mantle}.",
        qa_text="They cleaned it with gentle soap foam and patient blotting",
        tags={"cleaning", "soap"},
    ),
    "sand_scrub": Cleanup(
        id="sand_scrub",
        label="rough sand scrubbing",
        sense=1,
        power=2,
        works_on={"wool"},
        action_text="They rubbed and rubbed at the {mantle} with rough sand.",
        success_text="The mark came away, though the cloth looked tired.",
        partial_text="The cloth frayed before the color was gone.",
        qa_text="They scrubbed it with rough sand",
        tags={"rough"},
    ),
}

GIFTS = {
    "acorn_clasp": Gift(
        id="acorn_clasp",
        label="an acorn clasp",
        make_text="So {a} and {b} polished a tiny acorn clasp and fastened it over the softened mark, turning the place into a new bit of shine on the {mantle}.",
        end_text="a little acorn clasp winked from the mended place, and no one looking at it could miss the care tucked into the repair",
        tags={"gift", "repair"},
    ),
    "fern_patch": Gift(
        id="fern_patch",
        label="a fern patch",
        make_text="So {a} and {b} stitched a small fern patch over the last shadow, and the new green leaf looked as if it had always belonged on the {mantle}.",
        end_text="a fern patch rested over the old splash, making the whole mantle look as if spring itself had leaned down to bless it",
        tags={"gift", "repair"},
    ),
    "berry_button": Gift(
        id="berry_button",
        label="a berry-red button",
        make_text="So {a} and {b} sewed on a berry-red button above the faint mark, and the new little circle made the {mantle} look cheerful instead of sorry.",
        end_text="a berry-red button glowed near the hem, small and brave and full of the children's apology",
        tags={"gift", "repair"},
    ),
}


@dataclass
class StoryParams:
    duo: str = ""
    additive: str = ""
    mantle: str = ""
    cleanup: str = ""
    gift: str = ""
    instigator: str = ""
    cautioner: str = ""
    elder_name: str = ""
    delay: int = 0
    relation: str = "friends"
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
        duo="squirrels",
        additive="sparkle_dust",
        mantle="moss",
        cleanup="dew_rinse",
        gift="acorn_clasp",
        instigator="Pip",
        cautioner="Moss",
        elder_name="Old Fern",
        delay=0,
        relation="friends",
    ),
    StoryParams(
        duo="rabbits",
        additive="pine_resin",
        mantle="wool",
        cleanup="dew_rinse",
        gift="fern_patch",
        instigator="Nib",
        cautioner="Clover",
        elder_name="Aunt Briar",
        delay=1,
        relation="siblings",
    ),
    StoryParams(
        duo="mice",
        additive="flower_milk",
        mantle="feather",
        cleanup="comb_brush",
        gift="berry_button",
        instigator="Pico",
        cautioner="Tansy",
        elder_name="Grand Reed",
        delay=0,
        relation="friends",
    ),
    StoryParams(
        duo="squirrels",
        additive="pine_resin",
        mantle="wool",
        cleanup="soap_foam",
        gift="acorn_clasp",
        instigator="Hazel",
        cautioner="Pine",
        elder_name="Mossy Oak",
        delay=0,
        relation="siblings",
    ),
    StoryParams(
        duo="rabbits",
        additive="sparkle_dust",
        mantle="feather",
        cleanup="comb_brush",
        gift="fern_patch",
        instigator="Thimble",
        cautioner="Bramble",
        elder_name="Grand Clover",
        delay=1,
        relation="friends",
    ),
]

NAMES = [
    "Pip", "Moss", "Nib", "Clover", "Pico", "Tansy", "Hazel", "Pine",
    "Thimble", "Bramble", "Sorrel", "Pebble", "Ash", "Willow",
]
ELDER_NAMES = [
    "Old Fern", "Aunt Briar", "Grand Reed", "Mossy Oak", "Grand Clover", "Elder Sedge",
]

KNOWLEDGE = {
    "additive": [
        (
            "What is an additive?",
            "An additive is something small you put into another mixture to change it a little. If you add too much, the mixture can behave in a messy or surprising way."
        )
    ],
    "mantle": [
        (
            "What is a mantle?",
            "A mantle is a wrap or cloak worn over the shoulders. It keeps someone warm and can also be special for ceremonies or celebrations."
        )
    ],
    "apology": [
        (
            "What does it mean to reconcile with someone?",
            "To reconcile means to make peace again after hurt feelings or a mistake. People often do it by telling the truth, saying sorry, and helping repair what went wrong."
        )
    ],
    "water": [
        (
            "Why do some cloth things need gentle water to be cleaned?",
            "Gentle water can loosen dirt or color without hurting soft cloth. If you scrub too hard, you might damage the fabric instead of helping it."
        )
    ],
    "brush": [
        (
            "Why would a feather mantle need brushing instead of soaking?",
            "Feathers are light and delicate, so careful brushing can protect their shape. Too much wet cleaning can flatten them and make them clump together."
        )
    ],
    "soap": [
        (
            "What does soap do when something is stained?",
            "Soap helps lift oily or sticky bits away from cloth so they can be wiped off. Gentle soap works best when you are patient and careful."
        )
    ],
    "repair": [
        (
            "Can something be mended even if it is not exactly the same as before?",
            "Yes. A good repair can make something useful and beautiful again, even if a small mark or patch remains."
        )
    ],
}
KNOWLEDGE_ORDER = ["additive", "mantle", "apology", "water", "brush", "soap", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    additive = f["additive"]
    mantle = f["mantle_cfg"]
    elder = f["elder"]
    duo = f["duo"]
    if f["outcome"] == "restored":
        return [
            f'Write a gentle animal story for a 3-to-5-year-old that uses the words "additive" and "mantle".',
            f"Tell a forest story where two young {duo.animal_plural} spill a color additive on {elder.id}'s {mantle.label}, then tell the truth and make peace by helping clean it.",
            f'Write a reconciliation story in which a child-like animal ignores a warning, makes a mess, says sorry, and helps fix the problem before a festival begins.',
        ]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that uses the words "additive" and "mantle".',
        f"Tell a story where two young {duo.animal_plural} stain an elder's mantle with too much additive, and reconciliation comes through apology and mending.",
        f'Write a child-facing animal tale where a mistake cannot be erased completely, but kindness and repair turn the ending warm again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    elder = f["elder"]
    additive = f["additive"]
    mantle = f["mantle_cfg"]
    cleanup = f["cleanup"]
    duo = f["duo"]
    gift = f["gift"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young {duo.animal_plural}, {a.id} and {b.id}, and {elder.id}. They were trying to make {elder.id}'s {mantle.label} look special for {duo.festival}."
        ),
        (
            f"Why did {b.id} warn {a.id} about the additive?",
            f"{b.id} warned {a.id} because the additive was only meant to be used in a tiny amount. Too much could make the paint jump out of the bowl and splash onto the mantle."
        ),
        (
            f"What happened when {a.id} added too much?",
            f"The bowl foamed and splashed color onto the mantle. That stain made {elder.id} sad and made both young helpers feel guilty."
        ),
        (
            f"How did {a.id} and {b.id} begin to fix the mistake?",
            f"They told the truth and said they were sorry before they started cleaning. That mattered because reconciliation began when they stopped hiding and chose to help."
        ),
    ]
    if outcome == "restored":
        qa.append(
            (
                f"How was the mantle saved?",
                f"They used {cleanup.label} and worked very carefully until the stain faded away. The repair succeeded because that cleaning method matched the mantle's material and was gentle enough for it."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly, with peace restored between the children and {elder.id}. {elder.id} wore the mantle to the festival, showing that trust had come back along with the cloth."
            )
        )
    else:
        qa.append(
            (
                f"Why did they add {gift.label} to the mantle?",
                f"They had cleaned away the worst of the stain, but a small mark remained. The new piece turned the damaged place into a careful repair, so their apology could be seen as well as heard."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with reconciliation, not perfection. The mantle was mended and worn proudly, which showed that love and honesty mattered more than getting everything back exactly as it was."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"additive", "mantle", "apology", "repair"}
    tags |= set(f["cleanup"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.material:
            bits.append(f"material={e.material}")
        if e.heirloom:
            bits.append("heirloom=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
compatible(M, C) :- mantle(M), cleanup(C), works_on(C, Mat), material(M, Mat).
sensible(C)      :- cleanup(C), sense(C, S), sense_min(Min), S >= Min.
valid(D, A, M, C) :- duo(D), additive(A), compatible(M, C), sensible(C).

% --- outcome model ---------------------------------------------------------
severity(V) :- chosen_additive(A), additive_severity(A, S), delay(D), V = S + D.
restored    :- chosen_cleanup(C), cleanup_power(C, P), severity(V), P >= V.
outcome(restored) :- restored.
outcome(mended)   :- not restored.

#show valid/4.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for duo_id in DUOS:
        lines.append(asp.fact("duo", duo_id))
    for add_id, additive in ADDITIVES.items():
        lines.append(asp.fact("additive", add_id))
        lines.append(asp.fact("additive_severity", add_id, additive.severity))
    for mantle_id, mantle in MANTLES.items():
        lines.append(asp.fact("mantle", mantle_id))
        lines.append(asp.fact("material", mantle_id, mantle.material))
    for cleanup_id, cleanup in CLEANUPS.items():
        lines.append(asp.fact("cleanup", cleanup_id))
        lines.append(asp.fact("sense", cleanup_id, cleanup.sense))
        lines.append(asp.fact("cleanup_power", cleanup_id, cleanup.power))
        for mat in sorted(cleanup.works_on):
            lines.append(asp.fact("works_on", cleanup_id, mat))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_additive", params.additive),
            asp.fact("chosen_cleanup", params.cleanup),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sensible = {c.id for c in sensible_cleanups()}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible cleanups match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible cleanups:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(cl_sensible))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(smoke, trace=True, qa=True, header="### smoke")
        _ = smoke.to_dict()
        print("OK: smoke test generated, emitted, and serialized a normal story.")
    except Exception as exc:  # pragma: no cover - explicit verification guard
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: too much additive stains a mantle, and careful repair leads to reconciliation."
    )
    ap.add_argument("--duo", choices=DUOS)
    ap.add_argument("--additive", choices=ADDITIVES)
    ap.add_argument("--mantle", choices=MANTLES)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the splash sits before cleanup begins")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_two_names(rng: random.Random) -> tuple[str, str]:
    a, b = rng.sample(NAMES, 2)
    return a, b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mantle is not None and args.cleanup is not None:
        mantle = MANTLES[args.mantle]
        cleanup = CLEANUPS[args.cleanup]
        if not cleanup_works(cleanup, mantle) or cleanup.sense < SENSE_MIN:
            raise StoryError(explain_cleanup_rejection(cleanup, mantle))
    if args.cleanup is not None and CLEANUPS[args.cleanup].sense < SENSE_MIN:
        mantle = MANTLES[args.mantle] if args.mantle else next(iter(MANTLES.values()))
        raise StoryError(explain_cleanup_rejection(CLEANUPS[args.cleanup], mantle))

    combos = [
        c for c in valid_combos()
        if (args.duo is None or c[0] == args.duo)
        and (args.additive is None or c[1] == args.additive)
        and (args.mantle is None or c[2] == args.mantle)
        and (args.cleanup is None or c[3] == args.cleanup)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    duo_id, additive_id, mantle_id, cleanup_id = rng.choice(sorted(combos))
    gift_id = args.gift or rng.choice(sorted(GIFTS))
    instigator, cautioner = _pick_two_names(rng)
    elder_name_value = rng.choice(ELDER_NAMES)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    relation = rng.choice(["friends", "siblings"])
    return StoryParams(
        duo=duo_id,
        additive=additive_id,
        mantle=mantle_id,
        cleanup=cleanup_id,
        gift=gift_id,
        instigator=instigator,
        cautioner=cautioner,
        elder_name=elder_name_value,
        delay=delay,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.duo not in DUOS:
        raise StoryError(f"(Unknown duo '{params.duo}')")
    if params.additive not in ADDITIVES:
        raise StoryError(f"(Unknown additive '{params.additive}')")
    if params.mantle not in MANTLES:
        raise StoryError(f"(Unknown mantle '{params.mantle}')")
    if params.cleanup not in CLEANUPS:
        raise StoryError(f"(Unknown cleanup '{params.cleanup}')")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift '{params.gift}')")

    mantle = MANTLES[params.mantle]
    cleanup = CLEANUPS[params.cleanup]
    if cleanup.sense < SENSE_MIN or not cleanup_works(cleanup, mantle):
        raise StoryError(explain_cleanup_rejection(cleanup, mantle))

    if not params.instigator or not params.cautioner or params.instigator == params.cautioner:
        raise StoryError("(Story needs two different young animals.)")
    if not params.elder_name:
        raise StoryError("(Story needs an elder name.)")

    gift_template = GIFTS[params.gift]
    gift = Gift(
        id=gift_template.id,
        label=gift_template.label,
        make_text=gift_template.make_text.replace("{a}", params.instigator).replace("{b}", params.cautioner),
        end_text=gift_template.end_text,
        tags=set(gift_template.tags),
    )

    world = tell(
        DUOS[params.duo],
        ADDITIVES[params.additive],
        mantle,
        cleanup,
        gift,
        instigator=params.instigator,
        cautioner=params.cautioner,
        elder_name_value=params.elder_name,
        delay=params.delay,
        relation=params.relation,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible cleanups: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (duo, additive, mantle, cleanup) combos:\n")
        for duo_id, additive_id, mantle_id, cleanup_id in combos:
            print(f"  {duo_id:10} {additive_id:13} {mantle_id:8} {cleanup_id}")
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.additive} on {p.mantle} "
                f"({p.cleanup}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
