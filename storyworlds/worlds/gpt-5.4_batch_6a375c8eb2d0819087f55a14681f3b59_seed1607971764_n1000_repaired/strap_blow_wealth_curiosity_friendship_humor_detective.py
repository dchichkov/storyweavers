#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py
====================================================================================

A standalone story world for a child-sized detective mystery: two friends solve
"The Case of the Wandering Satchel." The world is built around a bag with a
strap, a seeming theft, a physical cause that can really move the bag, and a
friendship-powered investigation with a little humor.

Reference seed, rebuilt as a world model:
-----------------------------------------
A detective-style story with the words "strap", "blow", and "wealth", and the
features Curiosity, Friendship, and Humor.

In this world, a grown-up's charity satchel holding fair money for books goes
missing. The children first suspect a mystery, then follow concrete clues.
Nothing supernatural or truly criminal happened: a loose strap let the satchel
get blown, tugged, or hooked into a hiding place. The detective turn comes from
the clue trail; the ending proves what changed when the satchel is found and the
grown-up fixes the bag's storage.

Run it
------
    python storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py
    python storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py --cause wind_blow
    python storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py --container trunk_satchel
    python storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py --spot under_bench
    python storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py --all
    python storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/strap_blow_wealth_curiosity_friendship_humor_detective.py --verify
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
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "librarian": "librarian"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    scene: str
    keeper_title: str
    opening_object: str
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
class Container:
    id: str
    label: str
    phrase: str
    contents: str
    strap_length: str
    heft: str
    start_place: str
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
    beat: str
    clue: str
    clue_kind: str
    spots: set[str]
    allowed_heft: set[str]
    allowed_lengths: set[str]
    humor: str
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
    found_line: str
    fix: str
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

    def detectives(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]


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
    bag = world.get("bag")
    if bag.meters["hidden"] < THRESHOLD:
        return []
    sig = ("missing_worry", bag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keeper = world.get("keeper")
    keeper.memes["worry"] += 1
    for child in world.detectives():
        child.memes["curiosity"] += 1
    world.get("room").meters["mystery"] += 1
    return []


def _r_cause_leaves_clue(world: World) -> list[str]:
    bag = world.get("bag")
    clue = world.get("clue")
    if bag.meters["hidden"] < THRESHOLD:
        return []
    if world.facts.get("clue_kind", "") == "":
        return []
    sig = ("clue_visible", world.facts["clue_kind"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["visible"] += 1
    return []


def _r_found_clears_mystery(world: World) -> list[str]:
    bag = world.get("bag")
    if bag.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", bag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["mystery"] = 0.0
    keeper = world.get("keeper")
    keeper.memes["relief"] += 1
    keeper.memes["gratitude"] += 1
    for child in world.detectives():
        child.memes["joy"] += 1
        child.memes["friendship"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_stirs_worry", tag="social", apply=_r_missing_stirs_worry),
    Rule(name="cause_leaves_clue", tag="physical", apply=_r_cause_leaves_clue),
    Rule(name="found_clears_mystery", tag="social", apply=_r_found_clears_mystery),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combo(container: Container, cause: Cause, spot: Spot) -> bool:
    return (
        spot.id in cause.spots
        and container.heft in cause.allowed_heft
        and container.strap_length in cause.allowed_lengths
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for container_id, container in CONTAINERS.items():
        for cause_id, cause in CAUSES.items():
            for spot_id, spot in SPOTS.items():
                if valid_combo(container, cause, spot):
                    out.append((container_id, cause_id, spot_id))
    return out


def explain_rejection(container: Container, cause: Cause, spot: Spot) -> str:
    if spot.id not in cause.spots:
        return (
            f"(No story: {cause.label} would not send {container.phrase} to {spot.phrase}. "
            f"Pick a hiding place that this cause could really reach.)"
        )
    if container.heft not in cause.allowed_heft:
        return (
            f"(No story: {container.phrase} is too {container.heft} for {cause.label}. "
            f"That cause would not move it in a believable detective story.)"
        )
    if container.strap_length not in cause.allowed_lengths:
        return (
            f"(No story: {cause.label} needs a {', '.join(sorted(cause.allowed_lengths))} strap, "
            f"but this bag has a {container.strap_length} strap.)"
        )
    return "(No story: this combination is not physically reasonable.)"


def predict_hiding(world: World) -> dict:
    sim = world.copy()
    bag = sim.get("bag")
    bag.meters["hidden"] += 1
    bag.meters["moved"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("room").meters["mystery"],
        "clue_visible": sim.get("clue").meters["visible"] >= THRESHOLD,
    }


def introduce(world: World, lead: Entity, partner: Entity, keeper: Entity, container: Container) -> None:
    for child in (lead, partner):
        child.memes["friendship"] += 1
        child.memes["joy"] += 1
    world.say(
        f"{lead.id} and {partner.id} were best friends and proud members of the "
        f"Maple Lane Detective Club. They had a notebook, a pencil, and more curiosity "
        f"than any two children on the street."
    )
    world.say(
        f"That afternoon they were in {world.setting.place}, where {keeper.label} had set out "
        f"{world.setting.opening_object}. Beside it sat {container.phrase}, holding {container.contents}."
    )
    world.say(
        f'"Please keep an eye on this little wealth for the new books," {keeper.label} said with a smile. '
        f'The word "wealth" made {partner.id} whisper, "Do detectives get paid in cookies instead?"'
    )


def show_bag(world: World, container: Container) -> None:
    bag = world.get("bag")
    bag.meters["secure"] = 0.0
    world.say(
        f"The satchel had a {container.strap_length} strap, and it rested at {container.start_place}. "
        f"It looked ordinary, which is exactly how good clues like to hide."
    )


def vanish(world: World, cause: Cause, spot: Spot) -> None:
    bag = world.get("bag")
    bag.meters["hidden"] += 1
    bag.meters["moved"] += 1
    bag.attrs["spot"] = spot.id
    propagate(world, narrate=False)
    keeper = world.get("keeper")
    pred = predict_hiding(world)
    world.facts["predicted_mystery"] = pred["mystery"]
    world.facts["predicted_clue_visible"] = pred["clue_visible"]
    world.say(
        f"Then came the trouble: {cause.beat}. When {keeper.label} turned back, the satchel was gone."
    )
    world.say(
        f'"My charity money!" {keeper.label} gasped. {keeper.pronoun().capitalize()} looked so startled that '
        f"the room itself seemed to hold its breath."
    )


def take_case(world: World, lead: Entity, partner: Entity) -> None:
    lead.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f'"A mystery," said {lead.id}, standing as straight as a lamppost. '
        f'"A real mystery," said {partner.id}, though {partner.pronoun()} had accidentally put the notebook upside down.'
    )


def inspect_scene(world: World, lead: Entity, partner: Entity, cause: Cause) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    lead.memes["focus"] += 1
    partner.memes["focus"] += 1
    if clue.meters["visible"] >= THRESHOLD:
        world.say(
            f"They bent low and studied the floor. {lead.id} spotted {cause.clue}. "
            f"{partner.id} almost announced a grand arrest, then stopped and giggled."
        )
    else:
        world.say(
            f"They bent low and studied the floor. At first all they found was dust and one raisin, "
            f"which {partner.id} called " + '"a suspicious grape."' + f" Then {lead.id} noticed {cause.clue}."
        )
    world.facts["clue_sentence"] = cause.clue


def follow_clue(world: World, lead: Entity, partner: Entity, cause: Cause, spot: Spot) -> None:
    world.get("clue").meters["followed"] += 1
    lead.memes["friendship"] += 1
    partner.memes["friendship"] += 1
    world.say(
        f'"You see the clue, and I will see where it points," said {lead.id}. '
        f'"That is why detectives should always have a best friend," said {partner.id}.'
    )
    world.say(
        f"The clue led them toward {spot.phrase}. {cause.humor}"
    )


def solve(world: World, lead: Entity, partner: Entity, keeper: Entity, container: Container, cause: Cause, spot: Spot) -> None:
    bag = world.get("bag")
    bag.meters["found"] += 1
    bag.meters["hidden"] = 0.0
    propagate(world, narrate=False)
    world.say(spot.found_line.format(container=container.label))
    world.say(
        f'"So nobody stole it," said {lead.id}. "{cause.label.capitalize()} caught the strap and sent it there." '
        f'{partner.id} gave a tiny detective nod, as if {partner.pronoun()} solved mysteries before breakfast.'
    )
    world.say(
        f"{keeper.label} pressed a hand to {keeper.pronoun('possessive')} heart and laughed with relief. "
        f'"My brave detectives," {keeper.pronoun()} said, "you saved the book money and my poor nerves."'
    )


def ending(world: World, lead: Entity, partner: Entity, keeper: Entity, spot: Spot) -> None:
    world.say(
        f"After that, {keeper.label} {spot.fix}. The detective club wrote the case into their notebook under the title "
        f'"The Case of the Wandering Strap."'
    )
    world.say(
        f"As they walked home, {partner.id} said the town was not rich in gold, but rich in friends. "
        f'{lead.id} agreed that this was a much better kind of wealth.'
    )


def tell(
    setting: Setting,
    container: Container,
    cause: Cause,
    spot: Spot,
    lead_name: str = "Mina",
    lead_gender: str = "girl",
    partner_name: str = "Owen",
    partner_gender: str = "boy",
    keeper_type: str = "librarian",
) -> World:
    world = World(setting)
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead", label=lead_name))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner", label=partner_name))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, role="keeper", label=setting.keeper_title))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    bag = world.add(Entity(id="bag", type="bag", label=container.label, attrs={"spot": ""}))
    clue = world.add(Entity(id="clue", type="clue", label=cause.clue_kind))
    world.facts["clue_kind"] = cause.clue_kind
    world.facts["spot_id"] = spot.id
    world.facts["cause_id"] = cause.id
    world.facts["container_id"] = container.id
    room.meters["mystery"] = 0.0
    bag.meters["hidden"] = 0.0
    bag.meters["moved"] = 0.0
    bag.meters["found"] = 0.0
    clue.meters["visible"] = 0.0
    clue.meters["noticed"] = 0.0
    clue.meters["followed"] = 0.0
    keeper.memes["worry"] = 0.0
    keeper.memes["relief"] = 0.0
    keeper.memes["gratitude"] = 0.0
    for child in (lead, partner):
        child.memes["curiosity"] = 0.0
        child.memes["friendship"] = 0.0
        child.memes["joy"] = 0.0
        child.memes["focus"] = 0.0

    introduce(world, lead, partner, keeper, container)
    show_bag(world, container)

    world.para()
    vanish(world, cause, spot)
    take_case(world, lead, partner)
    inspect_scene(world, lead, partner, cause)

    world.para()
    follow_clue(world, lead, partner, cause, spot)
    solve(world, lead, partner, keeper, container, cause, spot)
    ending(world, lead, partner, keeper, spot)

    world.facts.update(
        setting=setting,
        container=container,
        cause=cause,
        spot=spot,
        lead=lead,
        partner=partner,
        keeper=keeper,
        room=room,
        bag=bag,
        clue=clue,
        mystery_started=room.meters["mystery"] == 0.0 or keeper.memes["worry"] >= THRESHOLD,
        found=bag.meters["found"] >= THRESHOLD,
        fixed=True,
    )
    return world


SETTINGS = {
    "library_hall": Setting(
        id="library_hall",
        place="the town library hall",
        scene="rows of bright book tables and paper stars",
        keeper_title="Mrs. Reed the librarian",
        opening_object="a bright table of donated storybooks",
        tags={"library", "books"},
    ),
    "museum_corner": Setting(
        id="museum_corner",
        place="the little history museum",
        scene="glass cases and creaky floorboards",
        keeper_title="Mr. Bell the guide",
        opening_object="a display of old maps and shiny buttons",
        tags={"museum", "history"},
    ),
    "school_fair": Setting(
        id="school_fair",
        place="the school fair hall",
        scene="paper chains, cakes, and a guessing jar",
        keeper_title="Ms. Park the teacher",
        opening_object="a long cake table with raffle signs",
        tags={"school", "fair"},
    ),
}

CONTAINERS = {
    "coin_satchel": Container(
        id="coin_satchel",
        label="coin satchel",
        phrase="a blue coin satchel",
        contents="the day's coin money for fresh library books",
        strap_length="long",
        heft="light",
        start_place="the edge of the table",
        tags={"bag", "coins"},
    ),
    "receipt_pouch": Container(
        id="receipt_pouch",
        label="receipt pouch",
        phrase="a red receipt pouch",
        contents="folded bills and receipts for the fair stall",
        strap_length="medium",
        heft="light",
        start_place="a chair beside the table",
        tags={"bag", "paper"},
    ),
    "trunk_satchel": Container(
        id="trunk_satchel",
        label="trunk satchel",
        phrase="a brown trunk satchel",
        contents="donation notes and the heavier lockbox key",
        strap_length="long",
        heft="heavy",
        start_place="a low wooden hook",
        tags={"bag", "key"},
    ),
}

CAUSES = {
    "wind_blow": Cause(
        id="wind_blow",
        label="a blow of wind",
        beat="a door banged open and one strong blow of wind lifted the loose strap",
        clue="a paper receipt fluttering like a tiny flag",
        clue_kind="flutter_mark",
        spots={"behind_curtain", "under_stage"},
        allowed_heft={"light"},
        allowed_lengths={"long", "medium"},
        humor="Halfway there, the curtain puffed out again and nearly made both detectives accuse the air.",
        tags={"wind", "air"},
    ),
    "puppy_tug": Cause(
        id="puppy_tug",
        label="a playful puppy",
        beat="the baker's puppy mistook the dangling strap for a toy and gave it a cheerful tug",
        clue="small pawprints and one drooly ribbon of dust",
        clue_kind="pawprints",
        spots={"under_bench", "behind_curtain"},
        allowed_heft={"light"},
        allowed_lengths={"long"},
        humor='The puppy sneezed in the middle of the chase and looked offended, as if dust had broken the law.',
        tags={"puppy", "paw"},
    ),
    "cart_hook": Cause(
        id="cart_hook",
        label="the rolling supply cart",
        beat="the rolling supply cart trundled past, and a side hook caught the strap with a sneaky little snag",
        clue="a chalky scrape line pointing away from the table",
        clue_kind="scrape_line",
        spots={"behind_crate", "under_stage"},
        allowed_heft={"light", "heavy"},
        allowed_lengths={"long"},
        humor="The cart squeaked so loudly that even the mystery seemed to confess.",
        tags={"cart", "hook"},
    ),
}

SPOTS = {
    "under_bench": Spot(
        id="under_bench",
        label="under the bench",
        phrase="the bench by the wall",
        found_line="There, under the bench, lay the {container}, dusty but safe.",
        fix="hung the satchel high on a peg instead of leaving it where a puppy could reach",
        tags={"bench"},
    ),
    "behind_curtain": Spot(
        id="behind_curtain",
        label="behind the curtain",
        phrase="the tall blue curtain",
        found_line="Behind the curtain, tucked in the fold of cloth, sat the {container}.",
        fix="tied the strap into a shorter loop before setting the satchel down again",
        tags={"curtain"},
    ),
    "under_stage": Spot(
        id="under_stage",
        label="under the stage",
        phrase="the little wooden stage",
        found_line="Under the stage, beside a lost spoon, rested the {container}.",
        fix="kept the satchel in a drawer whenever the door or cart might rush past",
        tags={"stage"},
    ),
    "behind_crate": Spot(
        id="behind_crate",
        label="behind the crate",
        phrase="the stack of apple crates",
        found_line="Behind the crate, snug in the corner, was the {container}.",
        fix="moved the satchel away from the cart path and looped the strap twice around the hook",
        tags={"crate"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Lila", "Nora", "June", "Poppy", "Ava", "Ruby"]
BOY_NAMES = ["Owen", "Max", "Theo", "Finn", "Eli", "Ben", "Leo", "Jude"]


@dataclass
class StoryParams:
    setting: str
    container: str
    cause: str
    spot: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    keeper_type: str = "librarian"
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
    "strap": [(
        "What is a strap?",
        "A strap is a long piece of material on a bag that helps you hold it or hang it up. If it dangles loose, it can get caught on things."
    )],
    "wind": [(
        "What can a strong blow of wind do?",
        "A strong blow of wind can push light things, flap paper, and swing loose cloth or straps around. That is why people tuck things in safely."
    )],
    "puppy": [(
        "Why might a puppy tug on a bag strap?",
        "Puppies like things that dangle and bounce, because they look like toys. A grown-up has to keep bags and important things out of reach."
    )],
    "cart": [(
        "Why can wheels and hooks move things by accident?",
        "If a hook catches a strap, it can pull the bag along without meaning to. Accidents happen when things stick together and keep moving."
    )],
    "clue": [(
        "What is a clue in a detective story?",
        "A clue is a small sign that points toward what happened. Good detectives look carefully and put clues together."
    )],
    "friendship": [(
        "Why do friends make good detectives?",
        "Friends can notice different clues and help each other think. When they trust each other, they solve problems better together."
    )],
    "wealth": [(
        "What does wealth mean in this story?",
        "Here, wealth means something valuable that people are taking care of. At the end, the children also use the word to mean the richer treasure of friendship."
    )],
}
KNOWLEDGE_ORDER = ["strap", "wind", "puppy", "cart", "clue", "friendship", "wealth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    cause = f["cause"]
    container = f["container"]
    spot = f["spot"]
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "strap", "blow", and "wealth".',
        f"Tell a gentle mystery where best friends {lead.id} and {partner.id} investigate a missing {container.label} and discover that {cause.label}, not a thief, moved it.",
        f"Write a humorous friendship story in a detective style where children follow a clue trail to {spot.label} and solve the case together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    keeper = f["keeper"]
    container = f["container"]
    cause = f["cause"]
    spot = f["spot"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the detectives in the story?",
            f"The detectives are {lead.id} and {partner.id}, two best friends in the Maple Lane Detective Club. They work together, and that friendship helps them stay calm and curious."
        ),
        (
            f"What seemed to go missing?",
            f"{container.phrase.capitalize()} seemed to disappear. It held {container.contents}, so {keeper.label} was worried right away."
        ),
        (
            "Why did everyone think there was a mystery?",
            f"The satchel was there one moment and gone the next, so it looked as if someone had taken it. That sudden change made the room feel full of mystery and made the children start investigating."
        ),
        (
            "What clue did the children find?",
            f"They found {cause.clue}. That clue mattered because it pointed toward how the satchel had moved instead of pointing to a thief."
        ),
        (
            "How did the friends solve the case?",
            f"They searched together and followed the clue toward {spot.phrase}. Working side by side let one child notice the clue while the other kept the idea of the case straight."
        ),
        (
            "What really happened to the satchel?",
            f"{cause.label.capitalize()} caught the strap and sent the satchel to {spot.label}. Nobody stole it, and the missing money was safe the whole time."
        ),
        (
            "How did the story end?",
            f"The satchel was found, {keeper.label} felt relieved, and the grown-up changed how the bag was kept so it would not wander again. The ending also shows a deeper kind of wealth, because the friends go home proud of solving the case together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"strap", "clue", "friendship", "wealth"}
    cause = world.facts["cause"]
    if cause.id == "wind_blow":
        tags.add("wind")
    if cause.id == "puppy_tug":
        tags.add("puppy")
    if cause.id == "cart_hook":
        tags.add("cart")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="library_hall",
        container="coin_satchel",
        cause="wind_blow",
        spot="behind_curtain",
        lead_name="Mina",
        lead_gender="girl",
        partner_name="Owen",
        partner_gender="boy",
        keeper_type="librarian",
    ),
    StoryParams(
        setting="school_fair",
        container="receipt_pouch",
        cause="puppy_tug",
        spot="under_bench",
        lead_name="Ruby",
        lead_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        keeper_type="librarian",
    ),
    StoryParams(
        setting="museum_corner",
        container="trunk_satchel",
        cause="cart_hook",
        spot="behind_crate",
        lead_name="Nora",
        lead_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        keeper_type="librarian",
    ),
    StoryParams(
        setting="school_fair",
        container="coin_satchel",
        cause="cart_hook",
        spot="under_stage",
        lead_name="June",
        lead_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        keeper_type="librarian",
    ),
    StoryParams(
        setting="library_hall",
        container="receipt_pouch",
        cause="wind_blow",
        spot="under_stage",
        lead_name="Poppy",
        lead_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        keeper_type="librarian",
    ),
]


ASP_RULES = r"""
valid(C, Ca, S) :-
    container(C), cause(Ca), spot(S),
    reaches(Ca, S),
    allowed_heft(Ca, H), heft(C, H),
    allowed_length(Ca, L), strap_length(C, L).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("heft", cid, container.heft))
        lines.append(asp.fact("strap_length", cid, container.strap_length))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for spot_id in sorted(cause.spots):
            lines.append(asp.fact("reaches", cause_id, spot_id))
        for heft in sorted(cause.allowed_heft):
            lines.append(asp.fact("allowed_heft", cause_id, heft))
        for length in sorted(cause.allowed_lengths):
            lines.append(asp.fact("allowed_length", cause_id, length))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default generation produced empty story")
        print("OK: default seeded generation passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective mystery about a wandering satchel. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--lead-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (container, cause, spot) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container and args.cause and args.spot:
        container = CONTAINERS[args.container]
        cause = CAUSES[args.cause]
        spot = SPOTS[args.spot]
        if not valid_combo(container, cause, spot):
            raise StoryError(explain_rejection(container, cause, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.container is None or combo[0] == args.container)
        and (args.cause is None or combo[1] == args.cause)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    container_id, cause_id, spot_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or _pick_name(rng, lead_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=lead_name)
    return StoryParams(
        setting=setting_id,
        container=container_id,
        cause=cause_id,
        spot=spot_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        keeper_type="librarian",
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        container = CONTAINERS[params.container]
        cause = CAUSES[params.cause]
        spot = SPOTS[params.spot]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not valid_combo(container, cause, spot):
        raise StoryError(explain_rejection(container, cause, spot))

    world = tell(
        setting=setting,
        container=container,
        cause=cause,
        spot=spot,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        keeper_type=params.keeper_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (container, cause, spot) combos:\n")
        for container, cause, spot in combos:
            print(f"  {container:14} {cause:10} {spot}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lead_name} & {p.partner_name}: {p.cause} / {p.container} / {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
