#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alum_pish_revolutionary_problem_solving_teamwork_happy.py
====================================================================================

A small detective-style storyworld about two children solving the case of a
missing notebook for a school invention day. The world uses a few physical
meters and emotional memes, a reasonableness gate, and a simple ASP twin.

Every story includes the words "alum", "pish", and "revolutionary", but the
details vary across a small set of coherent scenarios:

- a wet mishap puts the notebook at risk
- a grown-up moves it to a sensible drying place
- the children must combine clues instead of guessing
- the ending proves that teamwork solved the mystery

Run it
------
    python storyworlds/worlds/gpt-5.4/alum_pish_revolutionary_problem_solving_teamwork_happy.py
    python storyworlds/worlds/gpt-5.4/alum_pish_revolutionary_problem_solving_teamwork_happy.py --place classroom --hazard rinse_cup
    python storyworlds/worlds/gpt-5.4/alum_pish_revolutionary_problem_solving_teamwork_happy.py --hideout lamp_table
    python storyworlds/worlds/gpt-5.4/alum_pish_revolutionary_problem_solving_teamwork_happy.py --all
    python storyworlds/worlds/gpt-5.4/alum_pish_revolutionary_problem_solving_teamwork_happy.py --qa --json
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man", "caretaker"}
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
            "librarian": "librarian",
            "caretaker": "caretaker",
            "teacher": "teacher",
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
class Setting:
    id: str
    place: str
    keeper_type: str
    scene: str
    has_sun: bool = False
    has_heat: bool = False
    hideouts: set[str] = field(default_factory=set)
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
class Project:
    id: str
    title: str
    device: str
    display: str
    kit_line: str
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
class Hazard:
    id: str
    source: str
    clue: str
    wetness: str
    move_reason: str
    dry_need: str
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
    phrase: str
    needs: set[str] = field(default_factory=set)
    spot_line: str = ""
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
        self.facts: dict = {
            "noticed_alum": False,
            "noticed_drops": False,
            "noticed_warmth": False,
            "brushed_alum": False,
            "solution_ready": False,
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
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]

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


def _r_notebook_risk(world: World) -> list[str]:
    notebook = world.get("notebook")
    if notebook.meters["missing"] < THRESHOLD:
        return []
    if notebook.attrs.get("moved_to"):
        return []
    sig = ("risk", "notebook")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    notebook.meters["at_risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_drying(world: World) -> list[str]:
    notebook = world.get("notebook")
    if notebook.meters["moved"] < THRESHOLD:
        return []
    hideout = world.get("hideout")
    need = notebook.attrs.get("dry_need", "")
    if need and need not in hideout.attrs.get("qualities", set()):
        return []
    sig = ("drying", notebook.id, hideout.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    notebook.meters["drying"] += 1
    notebook.meters["safe"] += 1
    return []


def _r_solution(world: World) -> list[str]:
    if not (
        world.facts.get("noticed_alum")
        and world.facts.get("noticed_drops")
        and world.facts.get("noticed_warmth")
    ):
        return []
    sig = ("solution",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["solution_ready"] = True
    for kid in world.kids():
        kid.memes["confidence"] += 1
    return []


def _r_reunion(world: World) -> list[str]:
    notebook = world.get("notebook")
    if notebook.meters["found"] < THRESHOLD:
        return []
    sig = ("reunion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    world.get("keeper").memes["gratitude"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="notebook_risk", tag="physical", apply=_r_notebook_risk),
    Rule(name="drying", tag="physical", apply=_r_drying),
    Rule(name="solution", tag="social", apply=_r_solution),
    Rule(name="reunion", tag="social", apply=_r_reunion),
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


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the bright classroom",
        keeper_type="teacher",
        scene="Sun squares lay on the floor beside the science shelf.",
        has_sun=True,
        has_heat=True,
        hideouts={"windowsill", "radiator_shelf"},
        tags={"school"},
    ),
    "library": Setting(
        id="library",
        place="the little library workroom",
        keeper_type="librarian",
        scene="A brass lamp glowed beside the return cart, and the room smelled like paper and polish.",
        has_sun=True,
        has_heat=False,
        hideouts={"lamp_table", "sunny_cart"},
        tags={"library"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the glassy greenhouse classroom",
        keeper_type="teacher",
        scene="Warm panes ticked softly, and rows of leaves shone with tiny drops.",
        has_sun=True,
        has_heat=True,
        hideouts={"potting_bench", "brick_ledge"},
        tags={"greenhouse"},
    ),
}

PROJECTS = {
    "seed_sorter": Project(
        id="seed_sorter",
        title="the revolutionary seed sorter",
        device="a little seed sorter",
        display="a tray of neat beans and sunflower seeds",
        kit_line="On the science table sat a packet marked alum for the crystal labels they had grown to decorate the display.",
        tags={"science", "invention"},
    ),
    "message_lamp": Project(
        id="message_lamp",
        title="the revolutionary message lamp",
        device="a blinking message lamp",
        display="a row of paper code cards",
        kit_line="Near the wires stood a packet marked alum from yesterday's crystal experiment, still sparkling under the light.",
        tags={"science", "light"},
    ),
    "wind_cart": Project(
        id="wind_cart",
        title="the revolutionary wind cart",
        device="a tiny wind cart",
        display="a smooth cardboard track",
        kit_line="Beside the wheels rested a packet marked alum, left from the crystal-growing kit the club had borrowed for signs.",
        tags={"science", "motion"},
    ),
}

HAZARDS = {
    "rinse_cup": Hazard(
        id="rinse_cup",
        source="a tipped rinse cup",
        clue="a silver ribbon of water",
        wetness="a damp corner",
        move_reason="to keep it from soaking up the spill",
        dry_need="warm",
        tags={"water"},
    ),
    "mister": Hazard(
        id="mister",
        source="a careless puff from the plant mister",
        clue="tiny round drops",
        wetness="speckled dampness",
        move_reason="to keep the pages from catching more spray",
        dry_need="sunny",
        tags={"water", "plants"},
    ),
    "drippy_pot": Hazard(
        id="drippy_pot",
        source="a flowerpot that had dripped after watering",
        clue="dark wet dots",
        wetness="a wet edge",
        move_reason="to save the notebook from the drips",
        dry_need="sunny",
        tags={"water", "plants"},
    ),
}

HIDEOUTS = {
    "windowsill": Hideout(
        id="windowsill",
        label="windowsill",
        phrase="the sunny windowsill",
        needs={"sunny"},
        spot_line="A warm beam touched the windowsill there.",
        tags={"sunny"},
    ),
    "radiator_shelf": Hideout(
        id="radiator_shelf",
        label="radiator shelf",
        phrase="the shelf above the radiator",
        needs={"warm"},
        spot_line="A soft ribbon of heat rose from the radiator beneath it.",
        tags={"warm"},
    ),
    "lamp_table": Hideout(
        id="lamp_table",
        label="lamp table",
        phrase="the lamp table beside the return basket",
        needs={"warm"},
        spot_line="The brass lamp made a cozy pool of warmth over the table.",
        tags={"warm"},
    ),
    "sunny_cart": Hideout(
        id="sunny_cart",
        label="return cart",
        phrase="the sunny top shelf of the return cart",
        needs={"sunny"},
        spot_line="The cart stood in a patch of clean morning sun.",
        tags={"sunny"},
    ),
    "potting_bench": Hideout(
        id="potting_bench",
        label="potting bench",
        phrase="the dry end of the potting bench",
        needs={"warm"},
        spot_line="The bench stayed warm near the vent and dry away from the watering cans.",
        tags={"warm"},
    ),
    "brick_ledge": Hideout(
        id="brick_ledge",
        label="brick ledge",
        phrase="the sunny brick ledge under the glass",
        needs={"sunny"},
        spot_line="The brick ledge held the day's brightest sunlight.",
        tags={"sunny"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nell", "Ivy", "June", "Tess", "Ruby", "Ada"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Jasper", "Theo", "Arlo", "Ben", "Nico"]
TRAITS = ["careful", "curious", "steady", "quick-eyed", "thoughtful", "patient"]


def hideout_qualities(setting: Setting, hideout: Hideout) -> set[str]:
    quals = set(hideout.needs)
    if setting.has_sun:
        quals.add("sunny")
    if setting.has_heat:
        quals.add("warm")
    return quals


def valid_combo(place_id: str, hazard_id: str, hideout_id: str) -> bool:
    if place_id not in SETTINGS or hazard_id not in HAZARDS or hideout_id not in HIDEOUTS:
        return False
    setting = SETTINGS[place_id]
    hazard = HAZARDS[hazard_id]
    hideout = HIDEOUTS[hideout_id]
    if hideout_id not in setting.hideouts:
        return False
    quals = hideout_qualities(setting, hideout)
    return hazard.dry_need in quals


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in SETTINGS:
        for hazard_id in HAZARDS:
            for hideout_id in HIDEOUTS:
                if valid_combo(place_id, hazard_id, hideout_id):
                    combos.append((place_id, hazard_id, hideout_id))
    return sorted(combos)


def explain_rejection(place_id: str, hazard_id: str, hideout_id: str) -> str:
    if place_id not in SETTINGS:
        return f"(No story: unknown place '{place_id}'.)"
    if hazard_id not in HAZARDS:
        return f"(No story: unknown hazard '{hazard_id}'.)"
    if hideout_id not in HIDEOUTS:
        return f"(No story: unknown hideout '{hideout_id}'.)"
    setting = SETTINGS[place_id]
    hazard = HAZARDS[hazard_id]
    hideout = HIDEOUTS[hideout_id]
    if hideout_id not in setting.hideouts:
        return (
            f"(No story: {hideout.phrase} does not belong in {setting.place}, so it "
            f"cannot be the sensible place where the notebook was moved.)"
        )
    return (
        f"(No story: {hazard.source} would call for a {hazard.dry_need} spot, but "
        f"{hideout.phrase} in {setting.place} does not honestly provide that.)"
    )


@dataclass
class StoryParams:
    place: str
    project: str
    hazard: str
    hideout: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    keeper_name: str
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


def intro(world: World, lead: Entity, partner: Entity, keeper: Entity, project: Project) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
        kid.memes["team"] += 1
    world.say(
        f"After school, {lead.id} and {partner.id} padded into {world.setting.place} like a pair of tiny detectives."
    )
    world.say(world.setting.scene)
    world.say(
        f"They were helping {keeper.id} finish plans for {project.title}, {project.device} for Invention Day."
    )
    world.say(
        f"On the worktable lay {project.display}, a sharpened pencil, and a striped notebook full of sketches."
    )
    world.say(project.kit_line)


def problem(world: World, lead: Entity, partner: Entity, keeper: Entity, hazard: Hazard) -> None:
    notebook = world.get("notebook")
    notebook.meters["missing"] += 1
    notebook.attrs["hazard_source"] = hazard.source
    notebook.attrs["dry_need"] = hazard.dry_need
    propagate(world, narrate=False)
    world.say(
        f"Then {keeper.id} turned back to the table and stopped. The striped notebook was gone."
    )
    world.say(
        f"Only {hazard.clue} and {hazard.wetness} showed where it had been."
    )
    world.say(
        f'"Pish," said the caretaker from the hall. "It is only a school notebook."'
    )
    world.say(
        f"But {lead.id} and {partner.id} knew better. Without the notebook, the whole display would be unfinished."
    )


def inspect_alum(world: World, lead: Entity) -> None:
    world.facts["noticed_alum"] = True
    lead.memes["focus"] += 1
    world.say(
        f'{lead.id} knelt by the science table. "Look," {lead.pronoun()} whispered. '
        f'"There is alum dust here, and a few bright grains on the floor."'
    )
    world.say(
        "The sparkly trail was too neat to be plain dust. Something had brushed past the packet."
    )


def inspect_drops(world: World, partner: Entity, hazard: Hazard) -> None:
    world.facts["noticed_drops"] = True
    partner.memes["focus"] += 1
    world.say(
        f'{partner.id} followed the wet marks with one finger in the air. '
        f'"These drops came from {hazard.source}," {partner.pronoun()} said.'
    )
    world.say(
        f'"Whoever moved the notebook must have done it {hazard.move_reason}."'
    )


def inspect_warm_place(world: World, lead: Entity, partner: Entity, hideout: Hideout) -> None:
    world.facts["noticed_warmth"] = True
    world.say(
        f"Together they looked around the room again, slower this time. {hideout.spot_line}"
    )
    world.say(
        f'{lead.id} glanced at {partner.id}. "{hideout.phrase.capitalize()} would dry a damp notebook," {lead.pronoun()} said.'
    )


def infer_solution(world: World, lead: Entity, partner: Entity, hideout: Hideout) -> None:
    propagate(world, narrate=False)
    if not world.facts.get("solution_ready"):
        raise StoryError("(No story: the children do not have enough grounded clues to infer the hiding place.)")
    for kid in (lead, partner):
        kid.memes["trust"] += 1
    world.say(
        f"{partner.id}'s eyes grew wide. The alum trail, the wet marks, and the warm spot all pointed the same way."
    )
    world.say(
        f'"Case solved," said {lead.id}. "Nobody stole it. Someone moved it to {hideout.phrase}."'
    )


def find_notebook(world: World, lead: Entity, partner: Entity, keeper: Entity, hideout: Hideout) -> None:
    notebook = world.get("notebook")
    hide_ent = world.get("hideout")
    notebook.attrs["moved_to"] = hideout.id
    notebook.meters["moved"] += 1
    world.facts["brushed_alum"] = True
    propagate(world, narrate=False)
    notebook.meters["found"] += 1
    notebook.meters["missing"] = 0.0
    notebook.meters["damp"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They hurried to {hideout.phrase}, and there it was: the striped notebook, safe and drying."
    )
    world.say(
        f"A few tiny alum grains still glittered on the cover, just enough to prove the path it had taken."
    )
    mover = notebook.attrs.get("moved_by_name", keeper.id)
    world.say(
        f'{keeper.id} gave a soft laugh. "{mover} put it there to protect it," {keeper.pronoun()} said. '
        f'"I was so busy tidying the table that I forgot to tell you."'
    )


def happy_end(world: World, lead: Entity, partner: Entity, keeper: Entity, project: Project) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
    world.say(
        f"{keeper.id} opened the notebook, and the plans for {project.title} were all there, dry and crisp."
    )
    world.say(
        f'"You two worked like real detectives," {keeper.pronoun()} said. "One of you found the alum clue, and one of you followed the water. Together, you solved it."'
    )
    world.say(
        f"By the time the doors opened, {project.device} stood ready, the signs were straight, and the whole room seemed to smile with them."
    )


def tell(
    setting: Setting,
    project: Project,
    hazard: Hazard,
    hideout: Hideout,
    lead_name: str,
    lead_gender: str,
    partner_name: str,
    partner_gender: str,
    keeper_name: str,
    trait: str,
) -> World:
    world = World(setting)

    lead = world.add(
        Entity(
            id=lead_name,
            kind="character",
            type=lead_gender,
            role="lead",
            attrs={"trait": trait},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            attrs={"trait": "helper"},
        )
    )
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=setting.keeper_type,
            role="keeper",
            label="the keeper",
        )
    )
    notebook = world.add(
        Entity(
            id="notebook",
            kind="thing",
            type="notebook",
            label="striped notebook",
            role="missing_item",
            attrs={
                "dry_need": hazard.dry_need,
                "moved_to": "",
                "moved_by_name": keeper_name,
            },
        )
    )
    hide_ent = world.add(
        Entity(
            id="hideout",
            kind="thing",
            type="hideout",
            label=hideout.label,
            attrs={"qualities": hideout_qualities(setting, hideout)},
        )
    )
    world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=setting.place,
        )
    )

    intro(world, lead, partner, keeper, project)
    world.para()
    problem(world, lead, partner, keeper, hazard)
    world.para()
    inspect_alum(world, lead)
    inspect_drops(world, partner, hazard)
    inspect_warm_place(world, lead, partner, hideout)
    infer_solution(world, lead, partner, hideout)
    world.para()
    find_notebook(world, lead, partner, keeper, hideout)
    happy_end(world, lead, partner, keeper, project)

    world.facts.update(
        setting=setting,
        project=project,
        hazard=hazard,
        hideout_cfg=hideout,
        lead=lead,
        partner=partner,
        keeper=keeper,
        notebook=notebook,
        found=notebook.meters["found"] >= THRESHOLD,
        teamwork=(lead.memes["trust"] >= THRESHOLD and partner.memes["trust"] >= THRESHOLD),
        dry_need=hazard.dry_need,
    )
    return world


KNOWLEDGE = {
    "alum": [
        (
            "What is alum?",
            "Alum is a kind of powder or crystal people use in some science and craft projects. It can leave sparkly grains that are easy to notice.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks what they mean. Good detectives do not just guess; they put small facts together to solve a problem.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful in solving problems?",
            "Teamwork helps because one person may notice a clue that another person misses. When people share what they know, the answer can become clearer.",
        )
    ],
    "water": [
        (
            "Why should you move a damp notebook to a warm or sunny place?",
            "Paper can wrinkle or tear if it stays wet. A warm or sunny place helps it dry more safely.",
        )
    ],
    "library": [
        (
            "What is a return cart in a library?",
            "A return cart is a rolling shelf where library books are placed before they go back to their proper spots.",
        )
    ],
    "greenhouse": [
        (
            "What is a greenhouse?",
            "A greenhouse is a bright building with lots of glass where plants can stay warm and sunny.",
        )
    ],
    "radiator": [
        (
            "What does a radiator do?",
            "A radiator gives off heat to warm a room. That warmth can also help damp things dry.",
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "teamwork", "alum", "water", "library", "greenhouse", "radiator"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    project = f["project"]
    setting = f["setting"]
    hazard = f["hazard"]
    return [
        (
            f'Write a short detective story for a 3-to-5-year-old where two children solve the case of a missing notebook by combining clues. '
            f'Include the words "alum", "pish", and "revolutionary".'
        ),
        (
            f"Tell a gentle mystery set in {setting.place} where {lead.id} and {partner.id} help recover plans for {project.title} after {hazard.source} leaves clues behind."
        ),
        (
            "Write a child-facing problem-solving story with teamwork, a false worry about theft, and a happy ending where the missing pages are found safe and dry."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    keeper = f["keeper"]
    project = f["project"]
    hazard = f["hazard"]
    hideout = f["hideout_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {partner.id}, two small detectives, and {keeper.id}, who was taking care of the invention plans in {setting.place}.",
        ),
        (
            "What was missing?",
            f"The striped notebook of plans for {project.title} was missing. Without it, the children could not finish the display for Invention Day.",
        ),
        (
            "Why did the children think the notebook mattered?",
            f"It held the sketches and notes for {project.device}. That meant the whole project could be delayed if they did not find it quickly.",
        ),
        (
            "What clues did the children use?",
            f"They used three clues: alum grains on the floor, wet marks from {hazard.source}, and the sight of a {hazard.dry_need} place that could dry paper safely. Each clue mattered, but the answer became clear only when they put them together.",
        ),
        (
            "Why did the notebook end up in that hiding place?",
            f"It had been moved there {hazard.move_reason}. The safe spot matched what a careful grown-up would choose for a damp notebook.",
        ),
        (
            "How did teamwork help solve the mystery?",
            f"{lead.id} noticed the alum clue, while {partner.id} made sense of the wet trail. When they shared what each had found, they could infer the right place instead of guessing.",
        ),
        (
            "How did the story end?",
            f"They found the notebook safe and drying at {hideout.phrase}, and the plans were fine. After that, the room felt cheerful again because the children had solved the case together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "teamwork", "alum", "water"}
    if f["setting"].id == "library":
        tags.add("library")
    if f["setting"].id == "greenhouse":
        tags.add("greenhouse")
    if f["hideout_cfg"].id == "radiator_shelf":
        tags.add("radiator")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        project="seed_sorter",
        hazard="rinse_cup",
        hideout="radiator_shelf",
        lead_name="Ada",
        lead_gender="girl",
        partner_name="Milo",
        partner_gender="boy",
        keeper_name="Ms. Fern",
        trait="careful",
    ),
    StoryParams(
        place="library",
        project="message_lamp",
        hazard="mister",
        hideout="sunny_cart",
        lead_name="Finn",
        lead_gender="boy",
        partner_name="Ruby",
        partner_gender="girl",
        keeper_name="Mrs. Bell",
        trait="quick-eyed",
    ),
    StoryParams(
        place="greenhouse",
        project="wind_cart",
        hazard="drippy_pot",
        hideout="brick_ledge",
        lead_name="June",
        lead_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        keeper_name="Mr. Reed",
        trait="patient",
    ),
    StoryParams(
        place="classroom",
        project="message_lamp",
        hazard="mister",
        hideout="windowsill",
        lead_name="Nell",
        lead_gender="girl",
        partner_name="Arlo",
        partner_gender="boy",
        keeper_name="Ms. Vale",
        trait="thoughtful",
    ),
    StoryParams(
        place="greenhouse",
        project="seed_sorter",
        hazard="rinse_cup",
        hideout="potting_bench",
        lead_name="Jasper",
        lead_gender="boy",
        partner_name="Ivy",
        partner_gender="girl",
        keeper_name="Ms. Moss",
        trait="steady",
    ),
]


ASP_RULES = r"""
qualifies(Place, Hideout, sunny) :- setting(Place), hideout(Hideout), place_has_sun(Place).
qualifies(Place, Hideout, warm)  :- setting(Place), hideout(Hideout), place_has_heat(Place).
qualifies(Place, Hideout, Need)  :- hideout_needs(Hideout, Need).

valid(Place, Hazard, Hideout) :-
    setting(Place), hazard(Hazard), hideout(Hideout),
    available(Place, Hideout),
    hazard_needs(Hazard, Need),
    qualifies(Place, Hideout, Need).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.has_sun:
            lines.append(asp.fact("place_has_sun", sid))
        if setting.has_heat:
            lines.append(asp.fact("place_has_heat", sid))
        for hideout_id in sorted(setting.hideouts):
            lines.append(asp.fact("available", sid, hideout_id))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_needs", hid, hazard.dry_need))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        for need in sorted(hideout.needs):
            lines.append(asp.fact("hideout_needs", hid, need))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style storyworld: two children solve the case of a missing notebook with clues, teamwork, and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--lead-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, hazard, hideout) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hazard and args.hideout and not valid_combo(args.place, args.hazard, args.hideout):
        raise StoryError(explain_rejection(args.place, args.hazard, args.hideout))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.hideout is None or combo[2] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, hazard, hideout = rng.choice(combos)
    project = args.project or rng.choice(sorted(PROJECTS))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or pick_name(rng, lead_gender)
    partner_name = args.partner_name or pick_name(rng, partner_gender, avoid=lead_name)
    keeper_name = rng.choice(["Ms. Fern", "Mr. Reed", "Mrs. Bell", "Ms. Vale", "Mr. Stone"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        project=project,
        hazard=hazard,
        hideout=hideout,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        keeper_name=keeper_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.project not in PROJECTS:
        raise StoryError(f"(No story: unknown project '{params.project}'.)")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(No story: unknown hazard '{params.hazard}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")
    if not valid_combo(params.place, params.hazard, params.hideout):
        raise StoryError(explain_rejection(params.place, params.hazard, params.hideout))

    world = tell(
        setting=SETTINGS[params.place],
        project=PROJECTS[params.project],
        hazard=HAZARDS[params.hazard],
        hideout=HIDEOUTS[params.hideout],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        keeper_name=params.keeper_name,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "alum" not in sample.story or "pish" not in sample.story or "revolutionary" not in sample.story:
            raise StoryError("smoke test story missing required words or story text")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story:
            raise StoryError("empty generated story")
        print("OK: default-style seeded generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SEEDED GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hazard, hideout) combos:\n")
        for place, hazard, hideout in combos:
            print(f"  {place:10} {hazard:10} {hideout}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.lead_name} & {p.partner_name}: {p.project} at {p.place} ({p.hazard} -> {p.hideout})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
