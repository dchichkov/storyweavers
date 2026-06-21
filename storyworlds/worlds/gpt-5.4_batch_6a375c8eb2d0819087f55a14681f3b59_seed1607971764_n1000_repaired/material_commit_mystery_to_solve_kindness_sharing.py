#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py
==============================================================================

A standalone story world about a child mystery in a make-believe pirate den:
someone borrowed special craft material, a small problem follows, and the
children solve the mystery by choosing kindness and sharing instead of blame.

The world model tracks simple physical meters (missing, torn, found, repaired)
and emotional memes (worry, suspicion, guilt, relief, generosity). The prose is
rendered from the state changes: setup, puzzling disappearance, investigation,
gentle confession, collaborative repair, and a closing image that proves the
children changed how they treat one another.

Run it
------
    python storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py
    python storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py --theme pirates --material felt --borrower younger_sibling
    python storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py --material shells
    python storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py --all
    python storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py --trace
    python storyworlds/worlds/gpt-5.4/material_commit_mystery_to_solve_kindness_sharing.py --verify
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
REPAIR_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    shareable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    leader_title: str
    friend_title: str
    mystery_goal: str
    hideout: str
    crew_word: str
    ending_line: str
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
class MaterialCfg:
    id: str
    label: str
    phrase: str
    use_text: str
    repair_tool: str
    fragile: bool = True
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
class BorrowerCfg:
    id: str
    label: str
    type: str
    relation_text: str
    need_text: str
    confess_text: str
    gentle: bool = True
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
class ClueCfg:
    id: str
    clue_text: str
    place_text: str
    points_to: str
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
class FixCfg:
    id: str
    label: str
    helper_action: str
    closing_image: str
    repair_power: int
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
        return [e for e in self.entities.values() if e.role in {"owner", "friend"}]

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


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    owner = world.get("owner")
    friend = world.get("friend")
    if project.meters["missing"] >= THRESHOLD:
        for kid in (owner, friend):
            sig = ("worry", kid.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kid.memes["worry"] += 1
        out.append("__missing__")
    return out


def _r_damage_guilt(world: World) -> list[str]:
    out: list[str] = []
    borrower = world.get("borrower")
    project = world.get("project")
    if project.meters["torn"] >= THRESHOLD:
        sig = ("guilt", borrower.id)
        if sig not in world.fired:
            world.fired.add(sig)
            borrower.memes["guilt"] += 1
        out.append("__damage__")
    return out


def _r_kindness_relief(world: World) -> list[str]:
    out: list[str] = []
    owner = world.get("owner")
    borrower = world.get("borrower")
    friend = world.get("friend")
    if owner.memes["kindness"] >= THRESHOLD and borrower.memes["guilt"] >= THRESHOLD:
        sig = ("relief", borrower.id)
        if sig not in world.fired:
            world.fired.add(sig)
            borrower.memes["relief"] += 1
            owner.memes["relief"] += 1
            friend.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="damage_guilt", tag="emotional", apply=_r_damage_guilt),
    Rule(name="kindness_relief", tag="social", apply=_r_kindness_relief),
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


def can_borrow_material(material: MaterialCfg, borrower: BorrowerCfg) -> bool:
    return material.fragile and borrower.gentle


def can_repair(material: MaterialCfg, fix: FixCfg) -> bool:
    return material.fragile and fix.repair_power >= REPAIR_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme in THEMES:
        for material_id, material in MATERIALS.items():
            for borrower_id, borrower in BORROWERS.items():
                for fix_id, fix in FIXES.items():
                    if can_borrow_material(material, borrower) and can_repair(material, fix):
                        combos.append((theme, material_id, borrower_id, fix_id))
    return combos


def predict_repair(world: World) -> dict:
    sim = world.copy()
    project = sim.get("project")
    project.meters["found"] += 1
    if sim.facts["fix"].repair_power >= REPAIR_MIN:
        project.meters["torn"] = 0.0
        project.meters["repaired"] += 1
    return {
        "repairable": project.meters["repaired"] >= THRESHOLD,
        "damage": project.meters["torn"] >= THRESHOLD,
    }


def introduce_play(world: World, owner: Entity, friend: Entity, theme: Theme) -> None:
    owner.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {owner.id} and {friend.id} turned the living room into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.leader_title} {owner.id} and {theme.friend_title} {friend.id}!" '
        f"{owner.id} cheered. \"Today we will solve {theme.mystery_goal}.\""
    )


def build_project(world: World, owner: Entity, material: MaterialCfg, theme: Theme) -> None:
    project = world.get("project")
    project.meters["whole"] = 1.0
    world.say(
        f"They spread out {material.phrase} on the rug and used the {material.label} to "
        f"{material.use_text}. Soon they had the beginning of a secret map for {theme.hideout}."
    )
    world.say(
        f"{owner.id} smiled at the neat stack of material and said they should save the last best piece for the middle."
    )


def step_away(world: World, owner: Entity, friend: Entity) -> None:
    world.say(
        f"Then {owner.id} went to fetch crayons, and {friend.id} went to get the tape from the shelf."
    )


def disappearance(world: World, owner: Entity, friend: Entity, material: MaterialCfg) -> None:
    project = world.get("project")
    project.meters["missing"] += 1
    propagate(world, narrate=False)
    owner.memes["suspicion"] += 1
    friend.memes["suspicion"] += 1
    world.say(
        f"When they hurried back, the best piece of {material.label} was gone. The careful pile had a hole in it, and the half-made map looked wrong without it."
    )
    world.say(
        f'"Oh no," whispered {friend.id}. "{theme_word(world)}! The material is missing."'
    )
    world.facts["mystery_started"] = True


def investigate(world: World, owner: Entity, friend: Entity, clue: ClueCfg) -> None:
    world.say(
        f"They did not shout or stomp. Instead, they looked for clues. {clue.clue_text} {clue.place_text}"
    )
    world.say(
        f"{owner.id} knelt down and traced the sign with one finger. {friend.id} followed close behind, both of them trying to think like careful detectives instead of angry ones."
    )


def find_borrower(world: World, borrower: Entity, material: MaterialCfg, clue: ClueCfg) -> None:
    project = world.get("project")
    project.meters["found"] += 1
    world.facts["found_place"] = clue.points_to
    world.say(
        f"The clue led them to {clue.points_to}, where they found {borrower.id} holding the missing {material.label}. A corner of it was bent, and one small part had torn."
    )
    project.meters["torn"] += 1
    propagate(world, narrate=False)


def confession(world: World, borrower: Entity, borrower_cfg: BorrowerCfg, material: MaterialCfg) -> None:
    world.say(
        f'{borrower.id} looked up with wide eyes. "{borrower_cfg.confess_text} I wanted it because {borrower_cfg.need_text}."'
    )
    world.say(
        f"{borrower.id} hugged the piece of material close and looked ready to cry. The mystery was solved, but now the room felt full of hurt feelings."
    )


def kind_response(world: World, owner: Entity, friend: Entity, borrower: Entity, material: MaterialCfg) -> None:
    owner.memes["kindness"] += 1
    friend.memes["sharing"] += 1
    project = world.get("project")
    pred = predict_repair(world)
    world.facts["predicted_repairable"] = pred["repairable"]
    world.say(
        f"{owner.id} took a slow breath. Instead of blaming {borrower.id}, {owner.pronoun()} said, "
        f'"You should have asked first, but we can still be kind. We can share the material and fix the torn part together."'
    )
    world.say(
        f'{friend.id} nodded. "{borrower.id} can help too," {friend.pronoun()} said. "Let\'s commit to mending it before the game starts again."'
    )
    propagate(world, narrate=False)
    if pred["repairable"]:
        world.say(
            f"The gentle words changed the air at once. {borrower.id}'s shoulders loosened because kindness made room for the truth."
        )


def repair_and_share(world: World, owner: Entity, friend: Entity, borrower: Entity,
                     material: MaterialCfg, fix: FixCfg, theme: Theme) -> None:
    project = world.get("project")
    project.meters["missing"] = 0.0
    project.meters["torn"] = 0.0
    project.meters["repaired"] += 1
    owner.memes["sharing"] += 1
    borrower.memes["sharing"] += 1
    borrower.memes["gratitude"] += 1
    world.say(
        f"Together they {fix.helper_action} using {material.repair_tool}. Then {owner.id} slid one extra piece of {material.label} over to {borrower.id} so {borrower.pronoun()} could make a tiny flag of {borrower.pronoun('possessive')} own."
    )
    world.say(
        f"Soon the map was whole again, and now it was better than before because three pairs of hands had worked on it."
    )
    world.para()
    world.say(
        f"When the game began again, the crew hurried toward {theme.hideout}. {fix.closing_image}"
    )


def theme_word(world: World) -> str:
    return world.facts["theme"].crew_word.capitalize()


def tell(theme: Theme, material: MaterialCfg, borrower_cfg: BorrowerCfg, clue: ClueCfg,
         fix: FixCfg, owner_name: str = "Lila", owner_gender: str = "girl",
         friend_name: str = "Tom", friend_gender: str = "boy",
         parent_type: str = "mother", borrower_name: str = "Nia") -> World:
    world = World()
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=["careful", "kind"],
        attrs={},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["brave", "thoughtful"],
        attrs={},
    ))
    borrower = world.add(Entity(
        id=borrower_name,
        kind="character",
        type=borrower_cfg.type,
        role="borrower",
        traits=["small", "gentle"],
        attrs={"relation": borrower_cfg.relation_text},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    world.add(Entity(
        id="project",
        kind="thing",
        type="map",
        label="map",
        role="project",
        portable=True,
        shareable=True,
        attrs={},
    ))
    world.facts.update(
        theme=theme,
        material=material,
        borrower_cfg=borrower_cfg,
        clue=clue,
        fix=fix,
        owner=owner,
        friend=friend,
        borrower=borrower,
        parent=parent,
        mystery_started=False,
        predicted_repairable=False,
        found_place="",
    )

    introduce_play(world, owner, friend, theme)
    build_project(world, owner, material, theme)
    world.para()
    step_away(world, owner, friend)
    disappearance(world, owner, friend, material)
    investigate(world, owner, friend, clue)
    find_borrower(world, borrower, material, clue)
    world.para()
    confession(world, borrower, borrower_cfg, material)
    kind_response(world, owner, friend, borrower, material)
    repair_and_share(world, owner, friend, borrower, material, fix, theme)

    world.facts.update(
        outcome="shared_repaired",
        repaired=world.get("project").meters["repaired"] >= THRESHOLD,
        solved=world.get("project").meters["found"] >= THRESHOLD,
        kindness=owner.memes["kindness"] >= THRESHOLD,
        shared=owner.memes["sharing"] >= THRESHOLD and borrower.memes["sharing"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a windy pirate cove",
        rig="The sofa was their ship, two pillows were sea rocks, a blue blanket was the water, and a cardboard box became a treasure chest.",
        leader_title="Captain",
        friend_title="Scout",
        mystery_goal="the missing-map mystery",
        hideout="the treasure cave under the table",
        crew_word="pirates",
        ending_line="The ship sailed again.",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a jungle island full of secret paths",
        rig="The sofa was their jeep, two chairs were jungle gates, a green blanket was the tall grass, and a shoebox became a field trunk.",
        leader_title="Guide",
        friend_title="Tracker",
        mystery_goal="the lost-clue mystery",
        hideout="the hidden camp under the table",
        crew_word="explorers",
        ending_line="The expedition set off again.",
    ),
    "sailors": Theme(
        id="sailors",
        scene="a bright harbor with a whispering lighthouse",
        rig="The sofa was their boat, a laundry basket was the dock, a striped towel was the sea, and a box lid became a captain's chart board.",
        leader_title="Captain",
        friend_title="Mate",
        mystery_goal="the harbor-chart mystery",
        hideout="the lamp-lit cabin under the table",
        crew_word="sailors",
        ending_line="The little boat glided again.",
    ),
}

MATERIALS = {
    "felt": MaterialCfg(
        id="felt",
        label="felt",
        phrase="bright squares of felt",
        use_text="cut a wavy sea and a little red X",
        repair_tool="a strip of tape and a careful press",
        fragile=True,
        tags={"felt", "material", "sharing"},
    ),
    "paper": MaterialCfg(
        id="paper",
        label="paper",
        phrase="thick gold paper",
        use_text="draw a treasure path and fold a tiny compass rose",
        repair_tool="glue stick and smooth fingers",
        fragile=True,
        tags={"paper", "material", "sharing"},
    ),
    "cloth": MaterialCfg(
        id="cloth",
        label="cloth",
        phrase="soft blue cloth",
        use_text="make a sea chart with stitched-looking lines",
        repair_tool="tape on the back and a flat book on top",
        fragile=True,
        tags={"cloth", "material", "sharing"},
    ),
}

BORROWERS = {
    "younger_sibling": BorrowerCfg(
        id="younger_sibling",
        label="younger sibling",
        type="girl",
        relation_text="little sister",
        need_text="I wanted to make a flag for the cave too",
        confess_text="I'm sorry. I took it without asking",
        gentle=True,
        tags={"sibling", "kindness"},
    ),
    "neighbor_friend": BorrowerCfg(
        id="neighbor_friend",
        label="neighbor friend",
        type="boy",
        relation_text="neighbor friend",
        need_text="I wanted to bring a clue gift to the game",
        confess_text="I'm sorry. I borrowed it and hid because I felt embarrassed",
        gentle=True,
        tags={"friend", "kindness"},
    ),
    "little_cousin": BorrowerCfg(
        id="little_cousin",
        label="little cousin",
        type="girl",
        relation_text="little cousin",
        need_text="I wanted my own tiny sail for the cardboard boat",
        confess_text="I'm sorry. I thought there was enough for everyone",
        gentle=True,
        tags={"cousin", "kindness"},
    ),
}

CLUES = {
    "glitter": ClueCfg(
        id="glitter",
        clue_text="A trail of silver glitter twinkled on the floor.",
        place_text="It curved past the hall and stopped by the low reading nook.",
        points_to="the reading nook",
        tags={"clue", "mystery"},
    ),
    "scrap": ClueCfg(
        id="scrap",
        clue_text="A tiny scrap of matching material peeked from under a chair leg.",
        place_text="Beside it sat one small pair of socks turned in a hurry toward the window bench.",
        points_to="the window bench",
        tags={"clue", "mystery"},
    ),
    "tape": ClueCfg(
        id="tape",
        clue_text="The tape roll was missing too, and a sticky little print shone on the floor.",
        place_text="The mark led toward the blanket fort by the wall.",
        points_to="the blanket fort",
        tags={"clue", "mystery"},
    ),
}

FIXES = {
    "tape_patch": FixCfg(
        id="tape_patch",
        label="tape patch",
        helper_action="lined up the torn edges and pressed them flat with a neat tape patch",
        closing_image="The repaired map fluttered between them like a treasure secret that was safe again.",
        repair_power=2,
        tags={"repair", "sharing"},
    ),
    "glue_press": FixCfg(
        id="glue_press",
        label="glue press",
        helper_action="dabbed on glue, matched the edges, and waited with very patient hands",
        closing_image="The smooth map shone in the lamplight while three smiling heads bent over it.",
        repair_power=2,
        tags={"repair", "sharing"},
    ),
    "back_patch": FixCfg(
        id="back_patch",
        label="back patch",
        helper_action="placed a careful patch behind the tear and rubbed out every wrinkle",
        closing_image="The patched chart lay proud on the rug, ready to guide the crew once more.",
        repair_power=2,
        tags={"repair", "sharing"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
BORROWER_NAMES = ["Nia", "Oli", "Pia", "Tess", "Milo", "June"]


@dataclass
class StoryParams:
    theme: str = "pirates"
    material: str = "felt"
    borrower: str = "younger_sibling"
    clue: str = "glitter"
    fix: str = "tape_patch"
    owner_name: str = "Lila"
    owner_gender: str = "girl"
    friend_name: str = "Tom"
    friend_gender: str = "boy"
    parent: str = "mother"
    borrower_name: str = "Nia"
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
    "material": [(
        "What does the word material mean in a craft story?",
        "Material means the stuff you use to make something, like paper, felt, or cloth. Different material can bend, tear, or patch in different ways."
    )],
    "sharing": [(
        "Why is sharing helpful when children make something together?",
        "Sharing helps everyone join in and use what is there fairly. It can turn a quarrel into teamwork because each child has a part to do."
    )],
    "kindness": [(
        "What is kindness when someone makes a mistake?",
        "Kindness means speaking gently and helping fix the problem instead of only blaming. It does not hide the mistake, but it makes it easier to tell the truth."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something you do not understand yet and want to figure out. You solve it by noticing clues and thinking carefully."
    )],
    "repair": [(
        "What does it mean to repair something torn?",
        "To repair something is to mend it so it can be used again. You line parts up, patch them carefully, and make them strong enough to hold."
    )],
    "commit": [(
        "What does commit mean when friends say they will commit to a plan?",
        "It means they promise to keep trying and really do the plan. They are not just wishing; they are deciding to follow through."
    )],
    "felt": [(
        "What is felt?",
        "Felt is a soft cloth-like material often used for crafts. It is easy to cut and shape, but it can still bend or tear if someone pulls it."
    )],
    "paper": [(
        "Why can paper tear?",
        "Paper is useful for drawing and folding, but it can rip if it is tugged too hard. That is why careful hands matter."
    )],
    "cloth": [(
        "What is cloth used for in pretend play?",
        "Cloth can become many things in a game, like a sail, a sea, or a flag. It helps children imagine new places with one simple piece."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "kindness", "sharing", "repair", "commit", "material", "felt", "paper", "cloth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    borrower = f["borrower"]
    material = f["material"]
    theme = f["theme"]
    return [
        f'Write a short pirate-style story for a 3-to-5-year-old about a missing craft material, a small mystery to solve, and a kind ending. Include the words "material" and "commit".',
        f"Tell a gentle adventure where {owner.id} and {friend.id} discover that some {material.label} is missing, follow clues, and find {borrower.id} before choosing sharing over blame.",
        f"Write a story where children playing {theme.crew_word} solve a mystery with careful thinking, then commit to fixing the problem together and sharing what they made.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    borrower = f["borrower"]
    material = f["material"]
    clue = f["clue"]
    theme = f["theme"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id} and {friend.id}, who were playing {theme.crew_word}, and {borrower.id}, who took the missing piece of {material.label}. Their game turned into a little mystery to solve."
        ),
        (
            "What was the mystery?",
            f"The best piece of {material.label} disappeared from the map they were making. That mattered because the missing material left the pretend treasure map unfinished."
        ),
        (
            "How did they solve the mystery?",
            f"They looked for clues instead of shouting, and {clue.clue_text.lower()} {clue.place_text.lower()} That trail led them to {f['found_place']}, where they found {borrower.id} with the missing piece."
        ),
        (
            f"Why had {borrower.id} taken the material?",
            f"{borrower.id} wanted to join the game by making something small too. {borrower.pronoun().capitalize()} took it without asking, and that is why the piece went missing."
        ),
        (
            "How did kindness change what happened next?",
            f"{owner.id} did not only blame {borrower.id}; {owner.pronoun()} offered to share and help fix the tear. Because the answer was kind, {borrower.id} felt safe enough to stop hiding and help mend the map."
        ),
        (
            "What did the children commit to do?",
            f"They said they would commit to repairing the torn piece together before starting the game again. That promise turned the solved mystery into a shared job instead of a fight."
        ),
        (
            "How did the story end?",
            f"They repaired the map with a {fix.label} and shared extra material so everyone could make part of the game. The ending image shows three children hurrying back to play together, which proves they had changed from suspicion to sharing."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mystery", "kindness", "sharing", "repair", "commit", "material"}
    material_id = world.facts["material"].id
    if material_id in KNOWLEDGE:
        tags.add(material_id)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        material="felt",
        borrower="younger_sibling",
        clue="glitter",
        fix="tape_patch",
        owner_name="Lila",
        owner_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
        borrower_name="Nia",
    ),
    StoryParams(
        theme="explorers",
        material="paper",
        borrower="neighbor_friend",
        clue="scrap",
        fix="glue_press",
        owner_name="Mia",
        owner_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="father",
        borrower_name="Milo",
    ),
    StoryParams(
        theme="sailors",
        material="cloth",
        borrower="little_cousin",
        clue="tape",
        fix="back_patch",
        owner_name="Ava",
        owner_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        parent="mother",
        borrower_name="June",
    ),
]


def explain_rejection(material: MaterialCfg, borrower: BorrowerCfg, fix: FixCfg) -> str:
    if not can_borrow_material(material, borrower):
        return (
            f"(No story: {borrower.label} is not a plausible gentle borrower for fragile {material.label}, "
            f"so the mystery would not resolve with a kind confession.)"
        )
    if not can_repair(material, fix):
        return (
            f"(No story: {fix.label} is too weak to repair torn {material.label}, "
            f"so the ending would not honestly resolve into sharing and repair.)"
        )
    return "(No story: this combination does not fit the world rules.)"


ASP_RULES = r"""
borrow_ok(M,B) :- material(M), borrower(B), fragile(M), gentle(B).
repair_ok(M,F) :- material(M), fix(F), fragile(M), repair_power(F,P), repair_min(Min), P >= Min.
valid(T,M,B,F) :- theme(T), borrow_ok(M,B), repair_ok(M,F).

solved        :- chosen_clue(C), clue(C).
repaired      :- chosen_fix(F), repair_power(F,P), repair_min(Min), P >= Min.
kind_ending   :- chosen_borrower(B), gentle(B), repaired, solved.
outcome(shared_repaired) :- kind_ending.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for mid, material in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        if material.fragile:
            lines.append(asp.fact("fragile", mid))
    for bid, borrower in BORROWERS.items():
        lines.append(asp.fact("borrower", bid))
        if borrower.gentle:
            lines.append(asp.fact("gentle", bid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("repair_power", fid, fix.repair_power))
    lines.append(asp.fact("repair_min", REPAIR_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_borrower", params.borrower),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_clue", params.clue),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared_repaired"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate-style mystery about missing craft material, kindness, and sharing."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--borrower", choices=BORROWERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.borrower and args.fix:
        material = MATERIALS[args.material]
        borrower = BORROWERS[args.borrower]
        fix = FIXES[args.fix]
        if not (can_borrow_material(material, borrower) and can_repair(material, fix)):
            raise StoryError(explain_rejection(material, borrower, fix))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.material is None or c[1] == args.material)
        and (args.borrower is None or c[2] == args.borrower)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, material, borrower, fix = rng.choice(sorted(combos))
    clue = args.clue or rng.choice(sorted(CLUES))
    owner_name, owner_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=owner_name)
    borrower_name = rng.choice([n for n in BORROWER_NAMES if n not in {owner_name, friend_name}])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        material=material,
        borrower=borrower,
        clue=clue,
        fix=fix,
        owner_name=owner_name,
        owner_gender=owner_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        borrower_name=borrower_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.borrower not in BORROWERS:
        raise StoryError(f"(Unknown borrower: {params.borrower})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")

    material = MATERIALS[params.material]
    borrower = BORROWERS[params.borrower]
    fix = FIXES[params.fix]
    if not (can_borrow_material(material, borrower) and can_repair(material, fix)):
        raise StoryError(explain_rejection(material, borrower, fix))

    world = tell(
        theme=THEMES[params.theme],
        material=material,
        borrower_cfg=borrower,
        clue=CLUES[params.clue],
        fix=fix,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        borrower_name=params.borrower_name,
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
        print(f"{len(combos)} compatible (theme, material, borrower, fix) combos:\n")
        for theme, material, borrower, fix in combos:
            print(f"  {theme:10} {material:8} {borrower:16} {fix}")
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
            header = f"### {p.owner_name}, {p.friend_name}, and {p.borrower_name}: {p.material} mystery ({p.theme}, {p.borrower}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
