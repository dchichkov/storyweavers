#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cutter_friendship_suspense_mystery.py
================================================================

A standalone story world about two friends, a missing craft cutter, and a small
mystery that turns out to be an act of friendship.

The world models:
- a craft project that needs one shaped cutter
- a missing cutter borrowed for a second task
- a suspenseful hiding place with a clue-sound
- two friends whose trust and worry shape how they ask what happened

The story always resolves with friendship, but the middle turn depends on the
state of the world: some searches stay gentle, while scarier clues and lower
trust can lead to a huffy accusation followed by an apology.

Run it
------
python storyworlds/worlds/gpt-5.4/cutter_friendship_suspense_mystery.py
python storyworlds/worlds/gpt-5.4/cutter_friendship_suspense_mystery.py --project star_banner
python storyworlds/worlds/gpt-5.4/cutter_friendship_suspense_mystery.py --hideout puppet_stage --qa
python storyworlds/worlds/gpt-5.4/cutter_friendship_suspense_mystery.py --all
python storyworlds/worlds/gpt-5.4/cutter_friendship_suspense_mystery.py --asp
python storyworlds/worlds/gpt-5.4/cutter_friendship_suspense_mystery.py --verify
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
TRUST_KIND_MIN = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    needed_cutter: str
    opening: str
    display: str
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
class CutterCfg:
    id: str
    label: str
    phrase: str
    shape_word: str
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
class Hideout:
    id: str
    label: str
    place_line: str
    sound: str
    shadow: str
    open_line: str
    scary: int
    clue_kind: str
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
class BorrowUse:
    id: str
    label: str
    phrase: str
    needs_cutter: str
    clue_kind: str
    reason: str
    reveal: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_missing_worry(world: World) -> list[str]:
    lead = world.get("lead")
    friend = world.get("friend")
    cutter = world.get("cutter")
    project = world.get("project")
    if cutter.meters["borrowed"] < THRESHOLD or project.meters["waiting"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.get("room").meters["mystery"] += 1
    return ["__missing__"]


def _r_clue(world: World) -> list[str]:
    helper = world.get("helper")
    hideout = world.get("hideout")
    if helper.meters["working"] < THRESHOLD:
        return []
    sig = ("clue", world.facts["hideout_cfg"].id, world.facts["borrow_use_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hideout.meters["sound"] += 1
    hideout.meters["shadow"] += 1
    world.get("room").meters["mystery"] += 1
    return ["__clue__"]


def _r_together_courage(world: World) -> list[str]:
    lead = world.get("lead")
    friend = world.get("friend")
    if lead.memes["worry"] < THRESHOLD or friend.memes["worry"] < THRESHOLD:
        return []
    sig = ("together_courage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["courage"] += 1
    friend.memes["courage"] += 1
    lead.memes["trust"] += 1
    friend.memes["trust"] += 1
    return ["__together__"]


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue", tag="physical", apply=_r_clue),
    Rule(name="together_courage", tag="emotional", apply=_r_together_courage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def compatible(project: Project, cutter: CutterCfg, borrow_use: BorrowUse, hideout: Hideout) -> bool:
    return (
        project.needed_cutter == cutter.id
        and borrow_use.needs_cutter == cutter.id
        and borrow_use.clue_kind == hideout.clue_kind
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for project_id, project in PROJECTS.items():
        for cutter_id, cutter in CUTTERS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                for use_id, use in BORROW_USES.items():
                    if compatible(project, cutter, use, hideout):
                        combos.append((project_id, cutter_id, hideout_id, use_id))
    return combos


def reaction_mode(hideout: Hideout, trust: int) -> str:
    if hideout.scary >= 2 and trust < TRUST_KIND_MIN:
        return "blurt"
    return "kind"


def predict_reaction(project: Project, cutter: CutterCfg, hideout: Hideout, borrow_use: BorrowUse,
                     trust: int) -> dict:
    world = World()
    lead = world.add(Entity(id="lead", kind="character", type="girl"))
    friend = world.add(Entity(id="friend", kind="character", type="boy"))
    world.add(Entity(id="room", label="room"))
    world.add(Entity(id="project", label=project.label))
    world.add(Entity(id="cutter", label=cutter.label))
    world.add(Entity(id="helper", kind="character", type="girl"))
    world.add(Entity(id="hideout", label=hideout.label))
    world.facts["hideout_cfg"] = hideout
    world.facts["borrow_use_cfg"] = borrow_use
    lead.memes["trust"] = float(trust)
    friend.memes["trust"] = float(trust)
    world.get("project").meters["waiting"] = 1
    world.get("cutter").meters["borrowed"] = 1
    world.get("helper").meters["working"] = 1
    propagate(world, narrate=False)
    return {
        "mystery": world.get("room").meters["mystery"],
        "worry": lead.memes["worry"] + friend.memes["worry"],
        "mode": reaction_mode(hideout, trust),
    }


def introduce(world: World, project: Project, cutter: CutterCfg, lead: Entity, friend: Entity) -> None:
    for kid in (lead, friend):
        kid.memes["joy"] += 1
    world.say(
        f"After afternoon reading time, {lead.id} and {friend.id} sat at the art table as if it were a detective desk. "
        f"They were making {project.phrase}, and the most important tool was {cutter.phrase}."
    )
    world.say(project.opening)


def notice_missing(world: World, project: Project, cutter: CutterCfg, lead: Entity, friend: Entity) -> None:
    world.get("project").meters["waiting"] = 1
    world.get("cutter").meters["borrowed"] = 1
    propagate(world, narrate=False)
    world.say(
        f"But when {lead.id} reached for the tray of tools, the place for the {cutter.label} was empty."
    )
    world.say(
        f'"It was right here," {friend.id} whispered. The half-finished {project.label} seemed to wait and stare back at them.'
    )


def search(world: World, hideout: Hideout, borrow_use: BorrowUse, lead: Entity, friend: Entity) -> None:
    world.get("helper").meters["working"] = 1
    propagate(world, narrate=False)
    world.say(
        f"They looked under the paper scraps, inside the ribbon box, and behind the jars of glue, but the cutter was nowhere."
    )
    world.say(
        f"Then, from {hideout.place_line}, they heard {hideout.sound}. A {hideout.shadow} trembled there too."
    )
    world.say(
        f'{lead.id} and {friend.id} stopped at once. For one quiet second, the missing cutter felt less like a lost tool and more like the middle of a mystery.'
    )


def stick_together(world: World, lead: Entity, friend: Entity) -> None:
    world.say(
        f'{friend.id} slid a little closer. "{lead.id}, let\'s go together," {friend.pronoun()} said.'
    )
    world.say(
        f"Standing shoulder to shoulder made the room feel a little less spooky."
    )


def blurt_line(world: World, lead: Entity, friend: Entity, cutter: CutterCfg) -> None:
    lead.memes["huff"] += 1
    world.say(
        f'{lead.id} took a breath that came out too fast. "Who took the {cutter.label}?" {lead.pronoun()} called. '
        f'"That was not kind!"'
    )
    world.say(
        f"{friend.id} squeezed {lead.pronoun('possessive')} hand at once, already wishing the question had sounded softer."
    )


def kind_line(world: World, lead: Entity, friend: Entity, cutter: CutterCfg) -> None:
    lead.memes["patience"] += 1
    friend.memes["patience"] += 1
    world.say(
        f'{lead.id} cupped {lead.pronoun("possessive")} hands and called, "Hello? Did someone borrow the {cutter.label}? '
        f'We need it, but we can share."'
    )
    world.say(
        f"{friend.id} nodded beside {lead.pronoun('object')}, and the brave, gentle words made the mystery feel smaller."
    )


def reveal(world: World, hideout: Hideout, borrow_use: BorrowUse, cutter: CutterCfg,
           helper: Entity, lead: Entity, friend: Entity) -> None:
    world.get("cutter").meters["borrowed"] = 0
    world.get("helper").meters["working"] = 0
    world.get("cutter").meters["returned"] = 1
    helper.memes["relief"] += 1
    world.say(
        hideout.open_line
    )
    world.say(
        f"It was {helper.id}, holding the {cutter.label} and a piece of paper. {borrow_use.reveal}"
    )
    world.say(
        f'"I wanted it to be a surprise," {helper.id} said. "{borrow_use.reason}"'
    )


def repair_friendship(world: World, mode: str, lead: Entity, friend: Entity, helper: Entity) -> None:
    for kid in (lead, friend, helper):
        kid.memes["friendship"] += 1
        kid.memes["relief"] += 1
    if mode == "blurt":
        lead.memes["sorry"] += 1
        world.say(
            f'{lead.id} felt {lead.pronoun("possessive")} cheeks grow warm. "I\'m sorry I shouted," {lead.pronoun()} said. '
            f'"The dark corner and the missing tool made me think the wrong thing."'
        )
        world.say(
            f'{helper.id} smiled and handed the cutter back. "{friend.id} was right to come close instead of running away," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'{helper.id} smiled with relief. "Thank you for asking so gently," {helper.pronoun()} said. '
            f'"I only wanted to finish before you noticed."'
        )


def share_and_finish(world: World, project: Project, cutter: CutterCfg, borrow_use: BorrowUse,
                     lead: Entity, friend: Entity, helper: Entity) -> None:
    world.get("project").meters["waiting"] = 0
    world.get("project").meters["finished"] = 1
    world.say(
        f"Together they finished the tiny surprise first, and then the {cutter.label} went back to the art table."
    )
    world.say(
        f"Soon the friends were cutting, folding, and smoothing paper again until {project.display}."
    )
    world.say(
        borrow_use.ending_image
    )


def tell(project: Project, cutter: CutterCfg, hideout: Hideout, borrow_use: BorrowUse,
         lead_name: str = "Mia", lead_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         helper_name: str = "Tara", helper_gender: str = "girl",
         trust: int = 6) -> World:
    world = World()
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="room", type="room", label="art room"))
    world.add(Entity(id="project", type="project", label=project.label))
    world.add(Entity(id="cutter", type="tool", label=cutter.label))
    world.add(Entity(id="hideout", type="place", label=hideout.label))

    lead.memes["trust"] = float(trust)
    friend.memes["trust"] = float(trust)
    helper.memes["generosity"] = 1.0

    world.facts["project_cfg"] = project
    world.facts["cutter_cfg"] = cutter
    world.facts["hideout_cfg"] = hideout
    world.facts["borrow_use_cfg"] = borrow_use
    world.facts["trust"] = trust

    introduce(world, project, cutter, lead, friend)

    world.para()
    notice_missing(world, project, cutter, lead, friend)
    search(world, hideout, borrow_use, lead, friend)
    stick_together(world, lead, friend)

    mode = reaction_mode(hideout, trust)
    world.facts["mode"] = mode
    world.facts["predicted"] = predict_reaction(project, cutter, hideout, borrow_use, trust)
    world.para()
    if mode == "blurt":
        blurt_line(world, lead, friend, cutter)
    else:
        kind_line(world, lead, friend, cutter)

    world.para()
    reveal(world, hideout, borrow_use, cutter, helper, lead, friend)
    repair_friendship(world, mode, lead, friend, helper)

    world.para()
    share_and_finish(world, project, cutter, borrow_use, lead, friend, helper)

    world.facts.update(
        lead=lead,
        friend=friend,
        helper=helper,
        outcome="apology" if mode == "blurt" else "shared",
        cutter_found=world.get("cutter").meters["returned"] >= THRESHOLD,
        project_finished=world.get("project").meters["finished"] >= THRESHOLD,
        mystery_level=world.get("room").meters["mystery"],
    )
    return world


PROJECTS = {
    "star_banner": Project(
        id="star_banner",
        label="star banner",
        phrase="a silver star banner for the reading corner",
        needed_cutter="star_cutter",
        opening="Every bright scrap of paper felt like a clue waiting to become part of the banner.",
        display="a silver star banner danced above the books",
        tags={"paper", "stars"},
    ),
    "moon_cards": Project(
        id="moon_cards",
        label="moon cards",
        phrase="a set of moon cards for the class poem wall",
        needed_cutter="moon_cutter",
        opening="They wanted each card to look like a little piece of nighttime.",
        display="a row of moon cards glowed softly on the wall",
        tags={"paper", "moon"},
    ),
    "wave_picture": Project(
        id="wave_picture",
        label="wave picture",
        phrase="a blue wave picture for the hallway board",
        needed_cutter="wave_cutter",
        opening="The paper ocean looked calm, but it still needed one perfect edge to make it swish.",
        display="a blue wave picture curled across the hallway board",
        tags={"paper", "waves"},
    ),
}

CUTTERS = {
    "star_cutter": CutterCfg(
        id="star_cutter",
        label="star cutter",
        phrase="the little star cutter with yellow handles",
        shape_word="star",
        tags={"cutter", "stars"},
    ),
    "moon_cutter": CutterCfg(
        id="moon_cutter",
        label="moon cutter",
        phrase="the crescent moon cutter with smooth silver sides",
        shape_word="moon",
        tags={"cutter", "moon"},
    ),
    "wave_cutter": CutterCfg(
        id="wave_cutter",
        label="wave cutter",
        phrase="the wavy cutter with blue grips",
        shape_word="wave",
        tags={"cutter", "waves"},
    ),
}

HIDEOUTS = {
    "curtain_nook": Hideout(
        id="curtain_nook",
        label="curtain nook",
        place_line="the curtain nook by the tall window",
        sound="a thin rustle-rustle, as if paper were brushing paper",
        shadow="long window-shadow",
        open_line="Very slowly, they pulled the curtain aside.",
        scary=1,
        clue_kind="rustle",
        tags={"window", "rustle"},
    ),
    "supply_closet": Hideout(
        id="supply_closet",
        label="supply closet",
        place_line="the half-open supply closet",
        sound="a tiny tap-tap from inside, then a hush",
        shadow="narrow stripe of dark",
        open_line="They nudged the closet door wider until the hinges gave a soft squeak.",
        scary=2,
        clue_kind="tap",
        tags={"closet", "tap"},
    ),
    "puppet_stage": Hideout(
        id="puppet_stage",
        label="puppet stage",
        place_line="behind the puppet stage",
        sound="a whispery swish under the hanging cloth",
        shadow="lumpy cloth-shadow",
        open_line="They lifted the curtain of the puppet stage just a little.",
        scary=3,
        clue_kind="swish",
        tags={"puppet", "shadow"},
    ),
}

BORROW_USES = {
    "thank_you_stars": BorrowUse(
        id="thank_you_stars",
        label="thank-you stars",
        phrase="cutting thank-you stars",
        needs_cutter="star_cutter",
        clue_kind="rustle",
        reason="I was making tiny stars to tape onto your banner so it would sparkle even more",
        reveal="A neat row of silver stars lay beside her like secret treasure.",
        ending_image="At the end, the banner glittered with stars from all three friends, and the mystery corner felt cheerful instead of strange.",
        tags={"sharing", "stars"},
    ),
    "sleepy_moon_note": BorrowUse(
        id="sleepy_moon_note",
        label="sleepy moon note",
        phrase="cutting a moon note",
        needs_cutter="moon_cutter",
        clue_kind="tap",
        reason="I was making a moon note to tuck beside your cards, but the tape roll kept bumping the shelf",
        reveal="On the floor beside him sat a card with one pale moon and a pencil message curling under it.",
        ending_image="When they pinned up the cards, the little moon note sat beside them, and all three children smiled every time they passed it.",
        tags={"sharing", "moon"},
    ),
    "wave_name_surprise": BorrowUse(
        id="wave_name_surprise",
        label="wave name surprise",
        phrase="cutting a wave border",
        needs_cutter="wave_cutter",
        clue_kind="swish",
        reason="I was making a wave border with your names on it so the picture would look finished before you came back",
        reveal="A strip of blue paper waves was draped across his knees like a small secret sea.",
        ending_image="Later the hallway board showed one wide blue sea with all their names tucked into the waves together.",
        tags={"sharing", "waves"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ella", "Ava", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Tom", "Max", "Leo", "Finn", "Eli", "Noah", "Sam"]


@dataclass
class StoryParams:
    project: str
    cutter: str
    hideout: str
    borrow_use: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    helper_name: str
    helper_gender: str
    trust: int = 6
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
    "cutter": [
        (
            "What is a craft cutter?",
            "A craft cutter is a tool used to make a shape in paper or soft material. Children should use one carefully and share it kindly."
        )
    ],
    "stars": [
        (
            "Why do stars make good decorations?",
            "Star shapes are bright and simple, so they stand out quickly on a wall or banner. They can make a project look shiny and special."
        )
    ],
    "moon": [
        (
            "Why do moons feel mysterious in stories?",
            "The moon shines in the dark and changes shape across the month, so it often makes a scene feel quiet and full of wonder."
        )
    ],
    "waves": [
        (
            "Why do wave shapes look lively?",
            "Wave lines bend and curve, so they make paper art feel as if it is moving. That is why they are often used for sea pictures."
        )
    ],
    "sharing": [
        (
            "What should you do if you need a tool your friend is using?",
            "You should ask calmly and be ready to share. Kind words help everyone solve the problem faster."
        )
    ],
    "shadow": [
        (
            "Why can shadows look scary at first?",
            "A shadow only shows a dark shape, not all the details. That can make ordinary things seem mysterious until you look closely."
        )
    ],
    "closet": [
        (
            "Why do little sounds seem louder in a closet?",
            "Closets are small spaces, so taps and rustles bounce around inside them. That can make a tiny noise feel important."
        )
    ],
    "window": [
        (
            "Why does paper rustle near a window?",
            "A little breeze can move thin paper and make it whisper or rustle. The sound can be soft but easy to notice in a quiet room."
        )
    ],
    "puppet": [
        (
            "Why does a puppet stage make a good hiding spot in a pretend mystery?",
            "A puppet stage has cloth and corners that hide small movements. That makes it perfect for a gentle, spooky surprise."
        )
    ],
}
KNOWLEDGE_ORDER = ["cutter", "stars", "moon", "waves", "sharing", "shadow", "closet", "window", "puppet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    project = f["project_cfg"]
    cutter = f["cutter_cfg"]
    hideout = f["hideout_cfg"]
    helper = f["helper"]
    lead = f["lead"]
    friend = f["friend"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short mystery story for a 3-to-5-year-old about friendship and a missing {cutter.label}. Include the word "cutter".',
        f"Tell a gentle suspense story where {lead.id} and {friend.id} search for a missing {cutter.label} near the {hideout.label} while trying to finish {project.phrase}.",
    ]
    if outcome == "apology":
        prompts.append(
            f"Write a child-friendly mystery where a scary clue makes {lead.id} speak too sharply, but the friends discover that {helper.id} was only helping and the story ends with an apology and sharing."
        )
    else:
        prompts.append(
            f"Write a child-friendly mystery where the missing tool turns out to be part of a friendly surprise, and the children solve it by asking kindly and staying together."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    helper = f["helper"]
    project = f["project_cfg"]
    cutter = f["cutter_cfg"]
    hideout = f["hideout_cfg"]
    use = f["borrow_use_cfg"]
    mode = f["mode"]
    predicted = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {lead.id} and {friend.id}, and their friend {helper.id}. They are all connected by the same missing {cutter.label}."
        ),
        (
            f"Why did {lead.id} and {friend.id} care about the missing cutter?",
            f"They needed the {cutter.label} to finish {project.phrase}. When its place on the tool tray was empty, their project had to wait."
        ),
        (
            "What made the room feel mysterious?",
            f"They heard {hideout.sound} from {hideout.place_line} and saw {hideout.shadow}. Those clues turned an ordinary search into a suspenseful mystery."
        ),
        (
            f"Why did the friends stay together?",
            f"They were worried, but standing close made them braver. In the world state, both children's courage rose once they faced the mystery side by side."
        ),
    ]
    if mode == "blurt":
        qa.append(
            (
                f"Why did {lead.id} call out so sharply?",
                f"{lead.id} was already worried about the missing cutter, and the {hideout.label} was the scariest kind of hiding place in this story. Because the clues felt spooky and trust started lower, the fear came out as a sharp question before {lead.id} had time to slow down."
            )
        )
        qa.append(
            (
                f"What happened after they found {helper.id}?",
                f"They learned that {helper.id} had borrowed the cutter to help, not to be mean. Then {lead.id} apologized for shouting, so the mystery ended by repairing friendship instead of hurting it."
            )
        )
    else:
        qa.append(
            (
                f"How did {lead.id} and {friend.id} solve the mystery?",
                f"They solved it by asking gently instead of blaming anyone. That gave {helper.id} room to explain the surprise right away."
            )
        )
        qa.append(
            (
                f"Why was {helper.id} using the cutter?",
                f"{helper.id} was {use.phrase} to help with the project. The hidden work was meant as a friendly surprise, not as a trick."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the cutter returned, the project finished, and all three friends working together. The final picture proves what changed: the mystery corner stopped feeling spooky and became part of a shared art project."
        )
    )
    qa.append(
        (
            "Was the mystery dangerous?",
            f"No, it was only suspenseful, not dangerous. The biggest problem was worry and misunderstanding, and that changed once the friends looked closely and talked."
        )
    )
    if predicted["mystery"] >= 2:
        qa.append(
            (
                "Why did the search feel tense before the answer came?",
                f"The world model built up mystery from two things at once: the missing cutter and the clue coming from the hiding place. That is why the room felt so quiet and full of questions before the reveal."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    project = world.facts["project_cfg"]
    cutter = world.facts["cutter_cfg"]
    hideout = world.facts["hideout_cfg"]
    use = world.facts["borrow_use_cfg"]
    tags = set(project.tags) | set(cutter.tags) | set(hideout.tags) | set(use.tags)
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="star_banner",
        cutter="star_cutter",
        hideout="curtain_nook",
        borrow_use="thank_you_stars",
        lead_name="Mia",
        lead_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper_name="Lucy",
        helper_gender="girl",
        trust=7,
    ),
    StoryParams(
        project="moon_cards",
        cutter="moon_cutter",
        hideout="supply_closet",
        borrow_use="sleepy_moon_note",
        lead_name="Nora",
        lead_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        helper_name="Sam",
        helper_gender="boy",
        trust=4,
    ),
    StoryParams(
        project="wave_picture",
        cutter="wave_cutter",
        hideout="puppet_stage",
        borrow_use="wave_name_surprise",
        lead_name="Ava",
        lead_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        helper_name="Maya",
        helper_gender="girl",
        trust=3,
    ),
    StoryParams(
        project="moon_cards",
        cutter="moon_cutter",
        hideout="supply_closet",
        borrow_use="sleepy_moon_note",
        lead_name="Ella",
        lead_gender="girl",
        friend_name="Noah",
        friend_gender="boy",
        helper_name="Zoe",
        helper_gender="girl",
        trust=8,
    ),
]


def explain_rejection(project_id: str, cutter_id: str, hideout_id: str, use_id: str) -> str:
    project = PROJECTS.get(project_id)
    cutter = CUTTERS.get(cutter_id)
    hideout = HIDEOUTS.get(hideout_id)
    use = BORROW_USES.get(use_id)
    if not all([project, cutter, hideout, use]):
        return "(No story: one of the requested ids is unknown.)"
    if project.needed_cutter != cutter.id:
        return (
            f"(No story: {project.label} needs a {project.needed_cutter.replace('_', ' ')}, "
            f"not {cutter.label}. The project and the tool must honestly fit.)"
        )
    if use.needs_cutter != cutter.id:
        return (
            f"(No story: {use.label} would not use the {cutter.label}. The borrowed tool must make sense for the hidden task.)"
        )
    if use.clue_kind != hideout.clue_kind:
        return (
            f"(No story: {use.label} makes a {use.clue_kind} clue, but {hideout.label} is built for a {hideout.clue_kind} clue. "
            f"The suspense beat must match the hiding place.)"
        )
    return "(No story: this combination does not make a coherent mystery.)"


ASP_RULES = r"""
fits_project(P,C) :- project(P), cutter(C), needs_cutter(P,C).
fits_use(U,C) :- borrow_use(U), cutter(C), use_needs(U,C).
fits_clue(H,U) :- hideout(H), borrow_use(U), clue_kind(H,K), use_clue(U,K).

valid(P,C,H,U) :- fits_project(P,C), fits_use(U,C), fits_clue(H,U).

kind :- chosen_hideout(H), chosen_trust(T), scary(H,S), trust_kind_min(M), T >= M.
kind :- chosen_hideout(H), chosen_trust(_), scary(H,S), S < 2.
blurt :- chosen_hideout(H), chosen_trust(T), scary(H,S), S >= 2, trust_kind_min(M), T < M.

outcome(shared) :- kind.
outcome(apology) :- blurt.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("needs_cutter", pid, project.needed_cutter))
    for cid in CUTTERS:
        lines.append(asp.fact("cutter", cid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("clue_kind", hid, hideout.clue_kind))
        lines.append(asp.fact("scary", hid, hideout.scary))
    for uid, use in BORROW_USES.items():
        lines.append(asp.fact("borrow_use", uid))
        lines.append(asp.fact("use_needs", uid, use.needs_cutter))
        lines.append(asp.fact("use_clue", uid, use.clue_kind))
    lines.append(asp.fact("trust_kind_min", TRUST_KIND_MIN))
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
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    hideout = HIDEOUTS[params.hideout]
    return "apology" if reaction_mode(hideout, params.trust) == "blurt" else "shared"


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story is empty.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="")
        print("OK: smoke test passed for normal generate/emit.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: friendship mystery with a missing cutter."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--cutter", choices=CUTTERS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--borrow-use", dest="borrow_use", choices=BORROW_USES)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.cutter and args.hideout and args.borrow_use:
        if not compatible(PROJECTS[args.project], CUTTERS[args.cutter], BORROW_USES[args.borrow_use], HIDEOUTS[args.hideout]):
            raise StoryError(explain_rejection(args.project, args.cutter, args.hideout, args.borrow_use))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.cutter is None or combo[1] == args.cutter)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.borrow_use is None or combo[3] == args.borrow_use)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, cutter_id, hideout_id, use_id = rng.choice(sorted(combos))
    lead_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    lead_name = _pick_name(rng, lead_gender, used)
    used.add(lead_name)
    friend_name = _pick_name(rng, friend_gender, used)
    used.add(friend_name)
    helper_name = _pick_name(rng, helper_gender, used)
    trust = args.trust if args.trust is not None else rng.randint(2, 9)
    return StoryParams(
        project=project_id,
        cutter=cutter_id,
        hideout=hideout_id,
        borrow_use=use_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"Unknown project: {params.project}")
    if params.cutter not in CUTTERS:
        raise StoryError(f"Unknown cutter: {params.cutter}")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"Unknown hideout: {params.hideout}")
    if params.borrow_use not in BORROW_USES:
        raise StoryError(f"Unknown borrow_use: {params.borrow_use}")

    project = PROJECTS[params.project]
    cutter = CUTTERS[params.cutter]
    hideout = HIDEOUTS[params.hideout]
    use = BORROW_USES[params.borrow_use]
    if not compatible(project, cutter, use, hideout):
        raise StoryError(explain_rejection(params.project, params.cutter, params.hideout, params.borrow_use))

    world = tell(
        project=project,
        cutter=cutter,
        hideout=hideout,
        borrow_use=use,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (project, cutter, hideout, borrow_use) combos:\n")
        for project, cutter, hideout, use in combos:
            print(f"  {project:12} {cutter:12} {hideout:13} {use}")
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
            header = f"### {p.lead_name}, {p.friend_name}, and {p.helper_name}: {p.project} / {p.hideout} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
