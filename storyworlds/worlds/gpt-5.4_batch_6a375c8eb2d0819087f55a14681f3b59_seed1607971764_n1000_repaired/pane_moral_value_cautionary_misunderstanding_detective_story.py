#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pane_moral_value_cautionary_misunderstanding_detective_story.py
=========================================================================================

A standalone story world for a tiny child-facing detective tale about a cracked
window pane, a misleading clue, a false accusation, and the lesson that good
detectives check carefully before they blame someone.

The world model tracks:
- physical meters: cracked pane, draft, danger to the place's special things, repair
- emotional memes: worry, certainty, hurt, trust, apology, relief

The story always includes a misunderstanding, but different places, clues,
causes, repairs, and delays produce different plausible stories and endings.

Run it
------
python storyworlds/worlds/gpt-5.4/pane_moral_value_cautionary_misunderstanding_detective_story.py
python storyworlds/worlds/gpt-5.4/pane_moral_value_cautionary_misunderstanding_detective_story.py --place greenhouse --cause soccer_ball --clue ribbon
python storyworlds/worlds/gpt-5.4/pane_moral_value_cautionary_misunderstanding_detective_story.py --repair sticker_patch
python storyworlds/worlds/gpt-5.4/pane_moral_value_cautionary_misunderstanding_detective_story.py --all --qa
python storyworlds/worlds/gpt-5.4/pane_moral_value_cautionary_misunderstanding_detective_story.py --verify
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
    fragile: bool = False
    portable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Place:
    id: str
    label: str
    pane_phrase: str
    treasure: str
    treasure_plural: bool
    draft_harm: str
    event: str
    fragility: int
    adult_fix_from: str
    closing_image: str
    allows: set[str] = field(default_factory=set)
    clue_spots: dict[str, str] = field(default_factory=dict)
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
class Cause:
    id: str
    label: str
    happened: str
    trace: str
    impact: int
    needs: set[str] = field(default_factory=set)
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
    item: str
    phrase: str
    owner_name: str
    owner_gender: str
    owner_kind: str
    innocent_reason: str
    note: str
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
class Repair:
    id: str
    label: str
    sense: int
    power: int
    text: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_crack_makes_draft(world: World) -> list[str]:
    pane = world.get("pane")
    room = world.get("room")
    detective = world.get("detective")
    if pane.meters["cracked"] < THRESHOLD:
        return []
    sig = ("draft", "pane")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["draft"] += 1
    room.meters["risk"] += 1
    detective.memes["worry"] += 1
    return []


def _r_accusation_hurts(world: World) -> list[str]:
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.memes["accused"] < THRESHOLD:
        return []
    sig = ("hurt", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    suspect.memes["sad"] += 1
    detective.memes["certainty"] += 1
    detective.memes["trust"] -= 1
    return []


def _r_apology_repairs_trust(world: World) -> list[str]:
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.memes["apology"] < THRESHOLD:
        return []
    sig = ("trust_back", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["relief"] += 1
    suspect.memes["trust"] += 1
    detective.memes["humility"] += 1
    detective.memes["trust"] += 2
    return []


CAUSAL_RULES = [
    Rule(name="crack_makes_draft", tag="physical", apply=_r_crack_makes_draft),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
    Rule(name="apology_repairs_trust", tag="social", apply=_r_apology_repairs_trust),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(made)
    if narrate:
        for line in out:
            world.say(line)
    return out


def crack_severity(place: Place, cause: Cause, delay: int) -> int:
    return place.fragility + cause.impact + delay


def is_saved(place: Place, cause: Cause, repair: Repair, delay: int) -> bool:
    return repair.power >= crack_severity(place, cause, delay)


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for cause_id, cause in CAUSES.items():
            if cause_id not in place.allows:
                continue
            if not cause.needs.issubset(place.tags):
                continue
            for clue_id in place.clue_spots:
                combos.append((place_id, cause_id, clue_id))
    return combos


def explain_rejection(place: Place, cause: Cause) -> str:
    if cause.id not in place.allows:
        return (
            f"(No story: {cause.label} is not a plausible way to crack a pane at "
            f"{place.label}. Pick a cause that fits the place.)"
        )
    if not cause.needs.issubset(place.tags):
        return (
            f"(No story: {cause.label} needs details this place does not have, so "
            f"the accident would feel ungrounded here.)"
        )
    return "(No story: this combination is not plausible in the world.)"


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def predict_if_wait(world: World, place: Place, cause: Cause, delay: int) -> dict:
    sim = world.copy()
    sim.get("room").meters["risk"] += delay
    return {
        "severity": crack_severity(place, cause, delay),
        "harm": place.draft_harm,
    }


def introduce(world: World, detective: Entity, partner: Entity, place: Place) -> None:
    detective.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"{detective.id} liked to call {detective.pronoun('possessive')}self a little "
        f"detective. That afternoon, {detective.id} and {partner.id} were helping in "
        f"{place.label} before {place.event}."
    )
    world.say(
        f"They checked the rows and shelves like true sleuths, making sure "
        f"{place.treasure} looked just right."
    )


def discover(world: World, detective: Entity, partner: Entity, place: Place, clue: Clue) -> None:
    pane = world.get("pane")
    pane.meters["cracked"] += 1
    propagate(world, narrate=False)
    spot = place.clue_spots[clue.id]
    world.say(
        f"Then {partner.id} stopped short. A long crack ran across one window pane, "
        f"and cool air slipped in through the gap."
    )
    world.say(
        f"Right by the frame, on {spot}, lay {clue.phrase}. To {detective.id}, it "
        f"looked exactly like the sort of clue a detective dreams of."
    )


def accuse(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    detective.memes["accused"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Aha!" whispered {detective.id}. "This must mean {suspect.id} did it."'
    )
    world.say(
        f"When {suspect.id} came near, {detective.id} pointed at {clue.item} and "
        f"said, \"I solved the case. You cracked the pane.\""
    )


def suspect_reply(world: World, suspect: Entity, clue: Clue) -> None:
    world.say(
        f"{suspect.id}'s face fell. \"I didn't break it,\" {suspect.pronoun()} said. "
        f"\"I only left {clue.item} there because {clue.innocent_reason}.\""
    )
    if clue.note:
        world.say(clue.note)


def recheck_scene(world: World, detective: Entity, partner: Entity, cause: Cause) -> None:
    detective.memes["certainty"] = 0.0
    detective.memes["doubt"] += 1
    world.say(
        f"{partner.id} knelt by the sill and looked again. \"A real detective checks "
        f"more than one clue,\" {partner.pronoun()} said."
    )
    world.say(
        f"This time they noticed the rest of the scene: {cause.trace}. Suddenly the "
        f"first guess no longer fit."
    )


def tell_adult(world: World, detective: Entity, adult: Entity, place: Place, cause: Cause, delay: int) -> None:
    pred = predict_if_wait(world, place, cause, delay)
    world.facts["predicted_severity"] = pred["severity"]
    detective.memes["honesty"] += 1
    world.say(
        f"{detective.id} swallowed hard and ran to {adult.id}. "
        f"\"We found the cracked pane,\" {detective.pronoun()} said. "
        f"\"We need help before {pred['harm']}.\""
    )


def repair_success(world: World, adult: Entity, repair: Repair, place: Place) -> None:
    pane = world.get("pane")
    room = world.get("room")
    pane.meters["covered"] += 1
    room.meters["risk"] = 0.0
    pane.meters["fixed"] += 1
    world.say(
        f"{adult.id} came quickly and {repair.text.format(place=place.label)}."
    )
    world.say(
        f"Soon the crack was safely covered, and the cold draft could not nip at "
        f"{place.treasure} anymore."
    )


def repair_fail(world: World, adult: Entity, repair: Repair, place: Place) -> None:
    pane = world.get("pane")
    room = world.get("room")
    room.meters["risk"] += 1
    pane.meters["fixed"] += 0.5
    world.say(
        f"{adult.id} hurried over and {repair.fail.format(place=place.label)}."
    )
    world.say(
        f"But too much time had already passed. The draft kept creeping in, and "
        f"{place.draft_harm}."
    )


def apology(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    detective.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} turned red. \"I am sorry,\" {detective.pronoun()} said. "
        f"\"I saw {clue.item} and blamed you before I knew the truth.\""
    )
    world.say(
        f"{suspect.id} gave a small nod. The hurt did not vanish all at once, but "
        f"the apology opened the door for trust to come back."
    )


def ending_saved(world: World, detective: Entity, partner: Entity, suspect: Entity, place: Place) -> None:
    detective.memes["relief"] += 1
    partner.memes["relief"] += 1
    suspect.memes["relief"] += 1
    world.say(
        f"After that, the three children checked the room together, and the case "
        f"felt solved in the right way."
    )
    world.say(
        f"By evening, {place.closing_image}. {detective.id} wrote one last note in "
        f"{detective.pronoun('possessive')} pretend detective book: good hearts "
        f"look twice before they blame."
    )


def ending_spoiled(world: World, detective: Entity, partner: Entity, suspect: Entity, place: Place) -> None:
    detective.memes["sorrow"] += 1
    partner.memes["sorrow"] += 1
    suspect.memes["sorrow"] += 1
    world.say(
        f"The grown-ups saved what they could, but some of {place.treasure} were "
        f"already spoiled. The room felt much quieter after that."
    )
    world.say(
        f"{detective.id} never forgot the lesson. A rushed guess had hurt a friend "
        f"and wasted precious time, and even a clever detective must choose truth "
        f"and kindness before pride."
    )


def tell(
    place: Place,
    cause: Cause,
    clue: Clue,
    repair: Repair,
    detective_name: str = "Milo",
    detective_gender: str = "boy",
    partner_name: str = "June",
    partner_gender: str = "girl",
    adult_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["curious"],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["careful"],
    ))
    suspect = world.add(Entity(
        id=clue.owner_name,
        kind="character",
        type=clue.owner_gender,
        role="suspect",
        traits=[clue.owner_kind],
    ))
    adult = world.add(Entity(
        id="Aunt Bea" if adult_type == "mother" else "Mr. Reed",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    world.add(Entity(id="pane", type="pane", label="pane", fragile=True))
    world.add(Entity(id="room", type="place", label=place.label))

    world.facts.update(
        place=place,
        cause=cause,
        clue=clue,
        repair=repair,
        detective=detective,
        partner=partner,
        suspect=suspect,
        adult=adult,
        delay=delay,
    )

    introduce(world, detective, partner, place)
    world.para()
    discover(world, detective, partner, place, clue)
    accuse(world, detective, suspect, clue)
    suspect_reply(world, suspect, clue)
    recheck_scene(world, detective, partner, cause)
    world.para()
    tell_adult(world, detective, adult, place, cause, delay)
    saved = is_saved(place, cause, repair, delay)
    if saved:
        repair_success(world, adult, repair, place)
    else:
        repair_fail(world, adult, repair, place)
    apology(world, detective, suspect, clue)
    world.para()
    if saved:
        ending_saved(world, detective, partner, suspect, place)
        outcome = "saved"
    else:
        ending_spoiled(world, detective, partner, suspect, place)
        outcome = "spoiled"

    world.facts.update(
        outcome=outcome,
        cracked=True,
        false_accusation=True,
        saved=saved,
        severity=crack_severity(place, cause, delay),
    )
    return world


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="the school greenhouse",
        pane_phrase="the greenhouse pane",
        treasure="small tomato plants and basil trays",
        treasure_plural=True,
        draft_harm="the little plants began to droop from the cold air",
        event="the spring seed sale",
        fragility=2,
        adult_fix_from="the tool bench",
        closing_image="the small plants stood straight again beneath the warm glass",
        allows={"soccer_ball", "rolling_cart", "falling_broom"},
        clue_spots={
            "ribbon": "the watering shelf",
            "marble": "the damp floor by the seed trays",
            "glove": "a potting table",
        },
        tags={"yard", "tools", "plants", "glass"},
    ),
    "art_room": Place(
        id="art_room",
        label="the art room",
        pane_phrase="the tall classroom pane",
        treasure="bright paper paintings drying on a line",
        treasure_plural=True,
        draft_harm="the wet paintings fluttered and smeared at the edges",
        event="the hallway art show",
        fragility=2,
        adult_fix_from="the supply closet",
        closing_image="the paintings glowed in a neat row, safe from the wind",
        allows={"soccer_ball", "rolling_cart", "falling_broom"},
        clue_spots={
            "ribbon": "the paint shelf",
            "marble": "the windowsill",
            "glove": "the sink counter",
        },
        tags={"yard", "tools", "paint", "glass"},
    ),
    "bakery": Place(
        id="bakery",
        label="the little bakery",
        pane_phrase="the front window pane",
        treasure="cooling berry pies on the counter",
        treasure_plural=True,
        draft_harm="the pies cooled too fast and their tops sagged",
        event="the afternoon customers",
        fragility=3,
        adult_fix_from="the storage closet",
        closing_image="the pies sat round and proud in the warm sweet shop",
        allows={"rolling_cart", "falling_broom"},
        clue_spots={
            "ribbon": "the wrapping table",
            "marble": "the bench by the door",
            "glove": "the flour shelf",
        },
        tags={"tools", "food", "glass"},
    ),
}

CAUSES = {
    "soccer_ball": Cause(
        id="soccer_ball",
        label="a stray soccer ball",
        happened="A stray soccer ball had hit the glass.",
        trace="a muddy ball mark on the outside wall and a bounce line through the dust",
        impact=2,
        needs={"yard"},
        tags={"ball", "glass"},
    ),
    "rolling_cart": Cause(
        id="rolling_cart",
        label="a rolling cart",
        happened="A cart had rolled and bumped the window.",
        trace="tiny wheel tracks leading downhill and a seed cart resting crooked by the frame",
        impact=2,
        needs={"tools"},
        tags={"cart", "glass"},
    ),
    "falling_broom": Cause(
        id="falling_broom",
        label="a falling broom",
        happened="A broom had tipped and struck the window.",
        trace="a broom on the floor and a fresh nick in the wooden handle",
        impact=1,
        needs={"tools"},
        tags={"broom", "glass"},
    ),
}

CLUES = {
    "ribbon": Clue(
        id="ribbon",
        item="a blue ribbon",
        phrase="a blue ribbon looped under a flowerpot",
        owner_name="Tessa",
        owner_gender="girl",
        owner_kind="helper",
        innocent_reason="she had tied herb bundles with it that morning",
        note="She pointed to the neat herb bundles on the table, each one tied with the same bright blue ribbon.",
        tags={"ribbon", "misunderstanding"},
    ),
    "marble": Clue(
        id="marble",
        item="a green marble",
        phrase="a green marble shining beside the frame",
        owner_name="Ben",
        owner_gender="boy",
        owner_kind="collector",
        innocent_reason="he had been showing it to everyone during a break",
        note="He opened his hand and showed another marble just like it. \"One must have rolled away earlier,\" he said.",
        tags={"marble", "misunderstanding"},
    ),
    "glove": Clue(
        id="glove",
        item="a small gardening glove",
        phrase="a small gardening glove with dirt on the thumb",
        owner_name="Nora",
        owner_gender="girl",
        owner_kind="helper",
        innocent_reason="she had used it while carrying pots and forgot to pick it up",
        note="Near the potting bench, there were fresh handprints in soil where she had been working long before the crack.",
        tags={"glove", "misunderstanding"},
    ),
}

REPAIRS = {
    "board_and_tape": Repair(
        id="board_and_tape",
        label="board and tape",
        sense=3,
        power=5,
        text="covered the broken pane with a stiff board and strong tape, then called the glazier",
        fail="tried to cover the broken pane with a stiff board and strong tape, but the room had already suffered the draft",
        qa_text="covered the broken pane with a stiff board and strong tape and called for proper repair",
        tags={"repair", "board"},
    ),
    "cardboard_cover": Repair(
        id="cardboard_cover",
        label="cardboard cover",
        sense=2,
        power=4,
        text="slid thick cardboard over the crack and taped every edge tight",
        fail="slid thick cardboard over the crack, but not before the draft had already done its harm",
        qa_text="covered the broken pane with thick cardboard and tape",
        tags={"repair", "cardboard"},
    ),
    "sticker_patch": Repair(
        id="sticker_patch",
        label="sticker patch",
        sense=1,
        power=1,
        text="pressed a cheerful star sticker over the crack as if that could stop the wind",
        fail="pressed a cheerful star sticker over the crack, and of course the wind slipped right around it",
        qa_text="tried to use a little sticker on the crack",
        tags={"repair", "bad_fix"},
    ),
}

GIRL_NAMES = ["June", "Mia", "Lena", "Ruby", "Clara", "Nina", "Elsie", "Mabel"]
BOY_NAMES = ["Milo", "Owen", "Theo", "Finn", "Cal", "Jasper", "Eli", "Hugo"]


@dataclass
class StoryParams:
    place: str
    cause: str
    clue: str
    repair: str
    detective: str
    detective_gender: str
    partner: str
    partner_gender: str
    adult: str
    delay: int = 0
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
    "pane": [
        (
            "What is a pane?",
            "A pane is one flat piece of glass in a window. If a pane cracks, air and weather can come through."
        )
    ],
    "glass": [
        (
            "Why can broken glass be dangerous?",
            "Broken glass can be sharp, and it can cut skin. It also leaves an opening where wind, rain, or cold air can get in."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to find the truth. A good detective checks carefully instead of guessing too fast."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something is true, but it is not. Asking and checking can help clear it up."
        )
    ],
    "apology": [
        (
            "Why is it important to apologize after blaming someone unfairly?",
            "An apology shows that you know you were wrong and want to make things better. It helps repair hurt feelings and rebuild trust."
        )
    ],
    "ball": [
        (
            "Why can a ball crack a window?",
            "A hard ball moving fast can hit glass with enough force to crack it. That is why balls should stay away from windows."
        )
    ],
    "cart": [
        (
            "Why should rolling carts be watched carefully?",
            "A cart can roll if the ground slopes or if nobody holds it still. Then it can bump into something fragile."
        )
    ],
    "broom": [
        (
            "How can a broom break something by accident?",
            "If a broom tips over near glass, its hard handle can strike the surface. Even an ordinary tool can cause trouble if it falls."
        )
    ],
    "repair": [
        (
            "What should you do if you find a broken window pane?",
            "Tell a grown-up right away and keep people away from the broken glass. A proper cover or repair can stop the danger from getting worse."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    clue = f["clue"]
    suspect = f["suspect"]
    detective = f["detective"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old about a cracked pane in {place.label} and a clue that leads to a misunderstanding.',
        f"Tell a child-sized mystery where {detective.id} wrongly blames {suspect.id} after finding {clue.item}, then learns that a careful detective checks every clue before speaking.",
        'Write a cautionary story with the word "pane" that teaches not to accuse someone before knowing the truth.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    partner = f["partner"]
    suspect = f["suspect"]
    adult = f["adult"]
    place = f["place"]
    cause = f["cause"]
    clue = f["clue"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who wanted to solve a mystery, {partner.id}, who helped look carefully, and {suspect.id}, who was blamed by mistake."
        ),
        (
            f"What mystery did they find in {place.label}?",
            f"They found a cracked window pane with cool air slipping through it. That mattered because {place.draft_harm} if nobody helped in time."
        ),
        (
            f"Why did {detective.id} think {suspect.id} broke the pane?",
            f"{detective.id} saw {clue.item} near the window and treated it like a perfect clue. But one clue by itself was not enough to prove who cracked the glass."
        ),
        (
            f"Why was that a misunderstanding?",
            f"It was a misunderstanding because {suspect.id} had left {clue.item} there for an innocent reason: {clue.innocent_reason}. The clue was real, but the guess about what it meant was wrong."
        ),
        (
            "How did they learn what really happened?",
            f"When they checked the whole scene again, they saw {cause.trace}. Those extra signs showed that {cause.label} had cracked the pane instead."
        ),
        (
            f"What did {detective.id} do after learning the truth?",
            f"{detective.id} told {adult.id} about the broken pane and apologized to {suspect.id}. That mattered because honesty and kindness fixed more than one problem at once."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did the grown-up help save things in {place.label}?",
                f"{adult.id} {repair.qa_text}. That blocked the draft before it could keep harming {place.treasure}."
            )
        )
        qa.append(
            (
                "What was the lesson at the end?",
                f"The lesson was to look carefully and tell the truth instead of blaming too fast. A good detective uses patience, and a good friend uses kindness."
            )
        )
    else:
        qa.append(
            (
                "Did the rushed mistake matter?",
                f"Yes. By the time help came, some of {place.treasure} were already spoiled. The story warns that a false accusation can hurt feelings and waste the time needed to fix the real problem."
            )
        )
        qa.append(
            (
                "What was the lesson at the end?",
                f"The lesson was that guessing too quickly can cause two kinds of harm: it hurts a friend and it delays real help. Careful truth-telling matters, especially in an emergency."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pane", "glass", "detective", "misunderstanding", "apology", "repair"}
    tags |= set(f["cause"].tags)
    out: list[tuple[str, str]] = []
    order = ["pane", "glass", "detective", "misunderstanding", "apology", "ball", "cart", "broom", "repair"]
    for tag in order:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="greenhouse",
        cause="rolling_cart",
        clue="ribbon",
        repair="board_and_tape",
        detective="Milo",
        detective_gender="boy",
        partner="June",
        partner_gender="girl",
        adult="mother",
        delay=0,
    ),
    StoryParams(
        place="art_room",
        cause="soccer_ball",
        clue="marble",
        repair="cardboard_cover",
        detective="Lena",
        detective_gender="girl",
        partner="Theo",
        partner_gender="boy",
        adult="father",
        delay=1,
    ),
    StoryParams(
        place="bakery",
        cause="falling_broom",
        clue="glove",
        repair="board_and_tape",
        detective="Ruby",
        detective_gender="girl",
        partner="Owen",
        partner_gender="boy",
        adult="mother",
        delay=0,
    ),
    StoryParams(
        place="greenhouse",
        cause="soccer_ball",
        clue="glove",
        repair="cardboard_cover",
        detective="Cal",
        detective_gender="boy",
        partner="Mia",
        partner_gender="girl",
        adult="father",
        delay=2,
    ),
]


ASP_RULES = r"""
valid(P,C,L) :- place(P), cause(C), clue(L),
                allows(P,C),
                clue_spot(P,L),
                cause_need_ok(P,C).

cause_need_ok(P,C) :- not need(C,_).
cause_need_ok(P,C) :- need(C,T), tag(P,T), not missing_need(P,C).
missing_need(P,C)  :- need(C,T), not tag(P,T).

sensible_repair(R) :- repair(R), sense(R,S), sense_min(M), S >= M.

severity(V) :- chosen_place(P), chosen_cause(C), delay(D),
               fragility(P,F), impact(C,I), V = F + I + D.
saved :- chosen_repair(R), power(R,Pw), severity(V), Pw >= V.

outcome(saved) :- saved.
outcome(spoiled) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("fragility", place_id, place.fragility))
        for cause_id in sorted(place.allows):
            lines.append(asp.fact("allows", place_id, cause_id))
        for clue_id in sorted(place.clue_spots):
            lines.append(asp.fact("clue_spot", place_id, clue_id))
        for tag in sorted(place.tags):
            lines.append(asp.fact("tag", place_id, tag))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("impact", cause_id, cause.impact))
        for need in sorted(cause.needs):
            lines.append(asp.fact("need", cause_id, need))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_repair"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_repair", params.repair),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.cause not in CAUSES or params.repair not in REPAIRS:
        raise StoryError("(Cannot compute outcome: unknown place, cause, or repair.)")
    return "saved" if is_saved(PLACES[params.place], CAUSES[params.cause], REPAIRS[params.repair], params.delay) else "spoiled"


def _smoke_emit() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: story was empty.)")
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=False, header="### smoke")
    finally:
        sys.stdout = old
    if "pane" not in sample.story:
        raise StoryError('(Smoke test failed: expected the story to contain "pane".)')


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_repairs = set(asp_sensible_repairs())
    python_repairs = {r.id for r in sensible_repairs()}
    if clingo_repairs == python_repairs:
        print(f"OK: sensible repairs match ({sorted(clingo_repairs)}).")
    else:
        rc = 1
        print("MISMATCH in sensible repairs:")
        print("  clingo:", sorted(clingo_repairs))
        print("  python:", sorted(python_repairs))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome checks differ.")

    try:
        _smoke_emit()
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a little detective, a cracked pane, and the lesson not to accuse too quickly."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the children wait before getting help")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render a curated set")
    ap.add_argument("--trace", action="store_true", help="dump the world model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if (args.place, args.cause, next(iter(place.clue_spots))) not in valid_combos() and args.cause not in place.allows:
            raise StoryError(explain_rejection(place, cause))
        if args.cause not in place.allows or not cause.needs.issubset(place.tags):
            raise StoryError(explain_rejection(place, cause))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cause_id, clue_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    detective, detective_gender = _pick_name(rng)
    partner, partner_gender = _pick_name(rng, avoid=detective)
    adult = args.adult or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        cause=cause_id,
        clue=clue_id,
        repair=repair_id,
        detective=detective,
        detective_gender=detective_gender,
        partner=partner,
        partner_gender=partner_gender,
        adult=adult,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if (params.place, params.cause, params.clue) not in valid_combos():
        raise StoryError(explain_rejection(PLACES[params.place], CAUSES[params.cause]))
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        place=PLACES[params.place],
        cause=CAUSES[params.cause],
        clue=CLUES[params.clue],
        repair=REPAIRS[params.repair],
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        adult_type=params.adult,
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
        print(asp_program("", "#show valid/3.\n#show sensible_repair/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        repairs = asp_sensible_repairs()
        print(f"sensible repairs: {', '.join(repairs)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause, clue) combos:\n")
        for place, cause, clue in combos:
            print(f"  {place:10} {cause:12} {clue}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.detective} investigates {p.place} "
                f"({p.cause}, clue: {p.clue}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
