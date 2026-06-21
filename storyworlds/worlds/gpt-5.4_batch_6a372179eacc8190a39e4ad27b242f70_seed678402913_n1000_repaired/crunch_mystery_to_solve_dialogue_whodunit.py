#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crunch_mystery_to_solve_dialogue_whodunit.py
=======================================================================

A standalone storyworld for a tiny child-facing whodunit: someone makes a
mysterious *crunch* near a snack, a child sleuth asks questions, follows a
state-grounded clue, and gently solves the case.

The world model keeps both physical meters (crumbs, mess, distance, smell) and
emotional memes (curiosity, worry, guilt, relief). The story text is rendered
from simulated state, not from one frozen template. A Python reasonableness gate
and an inline ASP twin agree on which combinations are plausible and how the
mystery ends.

Run it
------
    python storyworlds/worlds/gpt-5.4/crunch_mystery_to_solve_dialogue_whodunit.py
    python storyworlds/worlds/gpt-5.4/crunch_mystery_to_solve_dialogue_whodunit.py --setting kitchen --snack cracker --suspect puppy
    python storyworlds/worlds/gpt-5.4/crunch_mystery_to_solve_dialogue_whodunit.py --snack carrot --container high_shelf
    python storyworlds/worlds/gpt-5.4/crunch_mystery_to_solve_dialogue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/crunch_mystery_to_solve_dialogue_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/crunch_mystery_to_solve_dialogue_whodunit.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    tiny: bool = False
    can_reach_table: bool = False
    can_reach_shelf: bool = False
    can_open_lid: bool = False
    can_smell_well: bool = False
    crunchy_eater: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"puppy", "dog", "cat", "kitten"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    cozy: str
    snack_spot: str
    footmark: str
    helper_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    crunch_word: str
    crumbs_word: str
    smell: str
    shape: str
    crunchy: bool = True
    messy: int = 1
    pet_ok: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    reach: str
    needs_open: bool = False
    pet_access: bool = True
    kid_access: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectCfg:
    id: str
    type: str
    name: str
    phrase: str
    can_reach_table: bool = False
    can_reach_shelf: bool = False
    can_open_lid: bool = False
    can_smell_well: bool = False
    tiny: bool = False
    pet_like: bool = False
    excuse: str = ""
    confession: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    needs: set[str] = field(default_factory=set)
    sense: int = 2
    question: str = ""
    notice: str = ""
    explain: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_mess_spreads(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    snack = world.entities.get("snack")
    floor = world.entities.get("floor")
    if culprit is None or snack is None or floor is None:
        return out
    if culprit.meters["ate"] < THRESHOLD:
        return out
    sig = ("mess", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    culprit.meters["crumbs_on_face"] += float(snack.attrs.get("messy", 1))
    floor.meters["crumbs"] += float(snack.attrs.get("messy", 1))
    if snack.attrs.get("smell"):
        culprit.meters["smell"] += 1
    if culprit.tiny:
        floor.meters["tiny_tracks"] += 1
    else:
        floor.meters["big_tracks"] += 1
    out.append("__mess__")
    return out


def _r_guilt_grows(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    sleuth = world.entities.get("sleuth")
    if culprit is None or sleuth is None:
        return out
    if culprit.meters["questioned"] < THRESHOLD:
        return out
    sig = ("guilt", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    culprit.memes["guilt"] += 1
    sleuth.memes["curiosity"] += 1
    out.append("__guilt__")
    return out


def _r_confession(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    if culprit is None:
        return out
    if culprit.memes["guilt"] < THRESHOLD:
        return out
    if culprit.meters["clue_strong"] < THRESHOLD:
        return out
    sig = ("confess", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    culprit.memes["confess"] += 1
    out.append("__confess__")
    return out


CAUSAL_RULES = [
    Rule(name="mess_spreads", tag="physical", apply=_r_mess_spreads),
    Rule(name="guilt_grows", tag="social", apply=_r_guilt_grows),
    Rule(name="confession", tag="social", apply=_r_confession),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        cozy="Sunlight made squares on the floor tiles.",
        snack_spot="the snack corner by the table",
        footmark="soft little tracks in the flour dust near the mat",
        helper_line="The room felt bright enough for careful looking.",
        tags={"kitchen"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        cozy="Blocks, books, and a toy train sat in neat rows.",
        snack_spot="the low art table by the window",
        footmark="tiny prints across the foam puzzle mat",
        helper_line="There was enough quiet to hear every small sound.",
        tags={"playroom"},
    ),
    "porch": Setting(
        id="porch",
        place="the back porch",
        cozy="A watering can and three sunny flowerpots stood by the step.",
        snack_spot="the little picnic bench",
        footmark="dusty marks near the doormat",
        helper_line="A small breeze moved the curtain and carried smells around.",
        tags={"porch"},
    ),
}

SNACKS = {
    "cracker": Snack(
        id="cracker",
        label="cracker",
        phrase="a round buttery cracker",
        crunch_word="crunch",
        crumbs_word="golden cracker crumbs",
        smell="buttery",
        shape="round",
        crunchy=True,
        messy=1,
        pet_ok=True,
        tags={"cracker", "crumbs"},
    ),
    "carrot": Snack(
        id="carrot",
        label="carrot stick",
        phrase="a bright orange carrot stick",
        crunch_word="crunch",
        crumbs_word="tiny orange bits",
        smell="fresh carrot",
        shape="long",
        crunchy=True,
        messy=1,
        pet_ok=True,
        tags={"carrot", "vegetable"},
    ),
    "apple": Snack(
        id="apple",
        label="apple slice",
        phrase="a crisp apple slice",
        crunch_word="crunch",
        crumbs_word="wet little apple flakes",
        smell="sweet apple",
        shape="crescent",
        crunchy=True,
        messy=1,
        pet_ok=True,
        tags={"apple", "fruit"},
    ),
    "toast": Snack(
        id="toast",
        label="toast corner",
        phrase="a crunchy toast corner",
        crunch_word="crunch",
        crumbs_word="brown toast flakes",
        smell="toasty",
        shape="triangle",
        crunchy=True,
        messy=2,
        pet_ok=False,
        tags={"toast", "crumbs"},
    ),
}

CONTAINERS = {
    "open_plate": Container(
        id="open_plate",
        label="plate",
        phrase="an open plate",
        reach="table",
        needs_open=False,
        pet_access=True,
        kid_access=True,
        tags={"plate"},
    ),
    "jar": Container(
        id="jar",
        label="glass jar",
        phrase="a glass jar with a lid",
        reach="table",
        needs_open=True,
        pet_access=False,
        kid_access=True,
        tags={"jar"},
    ),
    "high_shelf": Container(
        id="high_shelf",
        label="high shelf",
        phrase="the high shelf",
        reach="shelf",
        needs_open=False,
        pet_access=False,
        kid_access=True,
        tags={"shelf"},
    ),
}

SUSPECTS = {
    "brother": SuspectCfg(
        id="brother",
        type="boy",
        name="Ben",
        phrase="her brother Ben",
        can_reach_table=True,
        can_reach_shelf=True,
        can_open_lid=True,
        can_smell_well=False,
        tiny=False,
        pet_like=False,
        excuse="I was building a tower. I did hear a little sound, though.",
        confession="All right, I took one because I thought nobody would mind.",
        tags={"child"},
    ),
    "sister": SuspectCfg(
        id="sister",
        type="girl",
        name="Nora",
        phrase="her sister Nora",
        can_reach_table=True,
        can_reach_shelf=True,
        can_open_lid=True,
        can_smell_well=False,
        tiny=False,
        pet_like=False,
        excuse="I was coloring quietly. I smelled something good, but that was all.",
        confession="Yes, I nibbled one. I should have asked first.",
        tags={"child"},
    ),
    "puppy": SuspectCfg(
        id="puppy",
        type="puppy",
        name="Pip",
        phrase="the puppy Pip",
        can_reach_table=False,
        can_reach_shelf=False,
        can_open_lid=False,
        can_smell_well=True,
        tiny=True,
        pet_like=True,
        excuse="Pip only thumped its tail and blinked.",
        confession="Pip could not use words, but it bowed its head and licked the crumbs from its whiskers.",
        tags={"pet"},
    ),
}

CLUES = {
    "crumbs": Clue(
        id="crumbs",
        label="crumb trail",
        needs={"crumbs"},
        sense=3,
        question="Who left these crumbs?",
        notice="A neat little trail of crumbs led away from the snack spot.",
        explain="The crumbs matched the missing snack and pointed the way.",
        tags={"crumbs"},
    ),
    "smell": Clue(
        id="smell",
        label="smell clue",
        needs={"smell"},
        sense=2,
        question="Who still smells like the snack?",
        notice="The sleuth sniffed carefully and found the snack smell still hanging near one suspect.",
        explain="The smell lingered because the snack had been eaten only moments before.",
        tags={"smell"},
    ),
    "tracks": Clue(
        id="tracks",
        label="track clue",
        needs={"tracks"},
        sense=2,
        question="Whose feet went to the snack spot?",
        notice="There were tracks on the floor leading to the snack and back again.",
        explain="The size of the tracks showed whether the culprit was a child or a small pet.",
        tags={"tracks"},
    ),
}


def suspect_can_access(suspect: SuspectCfg, container: Container, snack: Snack) -> bool:
    if not snack.crunchy:
        return False
    if suspect.pet_like and not snack.pet_ok:
        return False
    if suspect.pet_like and not container.pet_access:
        return False
    if not suspect.pet_like and not container.kid_access:
        return False
    if container.reach == "table" and not suspect.can_reach_table:
        return False
    if container.reach == "shelf" and not suspect.can_reach_shelf:
        return False
    if container.needs_open and not suspect.can_open_lid:
        return False
    return True


def clue_works(clue: Clue, suspect: SuspectCfg, snack: Snack) -> bool:
    if clue.id == "crumbs":
        return snack.messy >= 1
    if clue.id == "smell":
        return bool(snack.smell)
    if clue.id == "tracks":
        return True
    return False


def sensible_clues() -> list[Clue]:
    return [cl for cl in CLUES.values() if cl.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for snack_id, snack in SNACKS.items():
            for container_id, container in CONTAINERS.items():
                for suspect_id, suspect in SUSPECTS.items():
                    if not suspect_can_access(suspect, container, snack):
                        continue
                    if any(clue_works(clue, suspect, snack) for clue in sensible_clues()):
                        combos.append((setting_id, snack_id, container_id, suspect_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    snack: str
    container: str
    suspect: str
    clue: str
    sleuth_name: str
    sleuth_gender: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="kitchen",
        snack="cracker",
        container="open_plate",
        suspect="puppy",
        clue="tracks",
        sleuth_name="Lily",
        sleuth_gender="girl",
        helper="mother",
        seed=None,
    ),
    StoryParams(
        setting="playroom",
        snack="apple",
        container="jar",
        suspect="brother",
        clue="crumbs",
        sleuth_name="Mia",
        sleuth_gender="girl",
        helper="father",
        seed=None,
    ),
    StoryParams(
        setting="porch",
        snack="carrot",
        container="open_plate",
        suspect="sister",
        clue="smell",
        sleuth_name="Max",
        sleuth_gender="boy",
        helper="mother",
        seed=None,
    ),
    StoryParams(
        setting="kitchen",
        snack="toast",
        container="high_shelf",
        suspect="brother",
        clue="crumbs",
        sleuth_name="Nora",
        sleuth_gender="girl",
        helper="father",
        seed=None,
    ),
    StoryParams(
        setting="playroom",
        snack="cracker",
        container="open_plate",
        suspect="sister",
        clue="tracks",
        sleuth_name="Ben",
        sleuth_gender="boy",
        helper="mother",
        seed=None,
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


def explain_rejection(snack: Snack, container: Container, suspect: SuspectCfg) -> str:
    if suspect.pet_like and not snack.pet_ok:
        return (
            f"(No story: {suspect.name} should not be the culprit for {snack.label}. "
            f"In this world, that snack is not a plausible pet snack.)"
        )
    if container.reach == "table" and not suspect.can_reach_table:
        return (
            f"(No story: {suspect.name} cannot reasonably reach {container.phrase}, "
            f"so there is no fair mystery to solve.)"
        )
    if container.reach == "shelf" and not suspect.can_reach_shelf:
        return (
            f"(No story: {suspect.name} cannot reach the high shelf, so the whodunit "
            f"would be unfair.)"
        )
    if container.needs_open and not suspect.can_open_lid:
        return (
            f"(No story: {suspect.name} cannot open {container.phrase}, so {suspect.pronoun('subject') if hasattr(suspect, 'pronoun') else 'the suspect'} "
            f"could not have taken the snack.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


def outcome_of(params: StoryParams) -> str:
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    if suspect.pet_like and clue.id == "tracks":
        return "discovered"
    if clue.sense >= 3:
        return "confessed"
    return "discovered"


def setup_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")

    setting = SETTINGS[params.setting]
    snack = SNACKS[params.snack]
    container = CONTAINERS[params.container]
    suspect_cfg = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]

    if not suspect_can_access(suspect_cfg, container, snack):
        raise StoryError(explain_rejection(snack, container, suspect_cfg))
    if clue.sense < SENSE_MIN or not clue_works(clue, suspect_cfg, snack):
        raise StoryError(
            f"(No story: the clue '{clue.id}' is too weak or does not fit this culprit.)"
        )

    world = World()
    sleuth = world.add(
        Entity(
            id=params.sleuth_name,
            kind="character",
            type=params.sleuth_gender,
            role="sleuth",
            label=params.sleuth_name,
            phrase=params.sleuth_name,
            can_smell_well=True,
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=params.helper,
            role="helper",
            label="the helper",
            phrase="the helper",
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character",
            type=suspect_cfg.type,
            role="culprit",
            label=suspect_cfg.name,
            phrase=suspect_cfg.phrase,
            tiny=suspect_cfg.tiny,
            can_reach_table=suspect_cfg.can_reach_table,
            can_reach_shelf=suspect_cfg.can_reach_shelf,
            can_open_lid=suspect_cfg.can_open_lid,
            can_smell_well=suspect_cfg.can_smell_well,
            attrs={
                "cfg_id": suspect_cfg.id,
                "excuse": suspect_cfg.excuse,
                "confession": suspect_cfg.confession,
            },
            tags=set(suspect_cfg.tags),
        )
    )
    snack_ent = world.add(
        Entity(
            id="snack",
            kind="thing",
            type="snack",
            label=snack.label,
            phrase=snack.phrase,
            attrs={
                "cfg_id": snack.id,
                "messy": snack.messy,
                "smell": snack.smell,
                "shape": snack.shape,
                "crunch_word": snack.crunch_word,
                "crumbs_word": snack.crumbs_word,
            },
            tags=set(snack.tags),
        )
    )
    world.add(
        Entity(
            id="container",
            kind="thing",
            type="container",
            label=container.label,
            phrase=container.phrase,
            attrs={
                "cfg_id": container.id,
                "reach": container.reach,
                "needs_open": container.needs_open,
            },
            tags=set(container.tags),
        )
    )
    world.add(Entity(id="floor", kind="thing", type="floor", label="floor", phrase="the floor"))
    sleuth.memes["curiosity"] += 1
    helper.memes["calm"] += 1

    culprit.meters["ate"] += 1
    culprit.meters["near_snack"] += 1
    propagate(world, narrate=False)

    clue_strength = float(clue.sense)
    culprit.meters["clue_strong"] = clue_strength
    world.facts.update(
        setting=setting,
        snack_cfg=snack,
        container_cfg=container,
        suspect_cfg=suspect_cfg,
        clue_cfg=clue,
        sleuth=sleuth,
        helper=helper,
        culprit=culprit,
        snack=snack_ent,
        outcome=outcome_of(params),
    )
    return world


def opening(world: World) -> None:
    setting = world.facts["setting"]
    sleuth = world.facts["sleuth"]
    helper = world.facts["helper"]
    snack = world.facts["snack_cfg"]
    container = world.facts["container_cfg"]
    world.say(
        f"After lunch, {sleuth.id} was in {setting.place}, where {setting.cozy.lower()}"
    )
    world.say(
        f"On {setting.snack_spot} sat {container.phrase} holding {snack.phrase} for later."
    )
    world.say(
        f'{helper.label_word.capitalize()} said, "Those snacks are for sharing after tidy-up."'
    )


def mysterious_crunch(world: World) -> None:
    setting = world.facts["setting"]
    snack = world.facts["snack_cfg"]
    sleuth = world.facts["sleuth"]
    culprit = world.facts["culprit"]
    culprit.memes["worry"] += 1
    sleuth.memes["surprise"] += 1
    world.say(
        f"Then a small {snack.crunch_word} came from behind the chair near {setting.snack_spot}."
    )
    world.say(
        f'{sleuth.id} froze. "Did you hear that {snack.crunch_word}?" {sleuth.pronoun()} whispered.'
    )
    if culprit.type == "puppy":
        world.say('From the corner came only a tiny tail-thump and a blink.')
    else:
        world.say('For one moment, nobody answered.')


def gather_suspects(world: World) -> None:
    suspect_cfg = world.facts["suspect_cfg"]
    sleuth = world.facts["sleuth"]
    helper = world.facts["helper"]
    world.para()
    world.say(
        f'{sleuth.id} put on a serious face. "This is a mystery to solve," {sleuth.pronoun()} said.'
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled a little. "{world.facts["setting"].helper_line}"'
    )
    world.say(
        f'{sleuth.id} looked at {suspect_cfg.phrase}. "I will ask questions first," {sleuth.pronoun()} said.'
    )


def question_suspect(world: World) -> None:
    clue = world.facts["clue_cfg"]
    culprit = world.facts["culprit"]
    culprit.meters["questioned"] += 1
    propagate(world, narrate=False)
    world.say(f'"{clue.question}" asked {world.facts["sleuth"].id}.')
    if culprit.type == "puppy":
        world.say(culprit.attrs["excuse"])
    else:
        world.say(f'"{culprit.attrs["excuse"]}" said {culprit.label}.')


def inspect_clue(world: World) -> None:
    clue = world.facts["clue_cfg"]
    setting = world.facts["setting"]
    snack = world.facts["snack_cfg"]
    culprit = world.facts["culprit"]
    floor = world.get("floor")
    world.para()
    world.say(clue.notice)
    if clue.id == "crumbs":
        floor.meters["crumbs_seen"] += 1
        world.say(
            f"The bits were {snack.crumbs_word}, and they led straight toward {culprit.label}."
        )
    elif clue.id == "smell":
        culprit.meters["smell_noticed"] += 1
        world.say(
            f"{world.facts['sleuth'].id} sniffed the air and found a faint {snack.smell} smell near {culprit.label}."
        )
    elif clue.id == "tracks":
        floor.meters["tracks_seen"] += 1
        if culprit.tiny:
            world.say(
                f"{setting.footmark.capitalize()} pointed to a very small visitor."
            )
        else:
            world.say(
                "The prints were not tiny at all. They looked just like a child's quick steps."
            )
    world.say(clue.explain)


def solve_case(world: World) -> None:
    culprit = world.facts["culprit"]
    sleuth = world.facts["sleuth"]
    helper = world.facts["helper"]
    snack = world.facts["snack_cfg"]
    outcome = world.facts["outcome"]
    world.para()
    if outcome == "confessed":
        world.say(
            f'"Aha," said {sleuth.id}. "The clue fits {culprit.label} best."'
        )
        if culprit.type == "puppy":
            world.say(culprit.attrs["confession"])
        else:
            world.say(f'"{culprit.attrs["confession"]}" said {culprit.label}.')
    else:
        if culprit.type == "puppy":
            world.say(
                f'{sleuth.id} knelt down. "It was {culprit.label}," {sleuth.pronoun()} said softly.'
            )
            world.say(culprit.attrs["confession"])
        else:
            world.say(
                f'{sleuth.id} pointed gently. "The clues say it was {culprit.label}," {sleuth.pronoun()} said.'
            )
            world.say(
                f"{culprit.label} looked at the floor, then at the snack spot, and nodded."
            )
    culprit.memes["relief"] += 1
    helper.memes["pride"] += 1
    sleuth.memes["relief"] += 1
    world.say(
        f'{helper.label_word.capitalize()} did not sound angry. "Thank you for telling the truth. Next time, ask before you take a {snack.label}."'
    )


def gentle_end(world: World) -> None:
    snack = world.facts["snack_cfg"]
    culprit = world.facts["culprit"]
    sleuth = world.facts["sleuth"]
    helper = world.facts["helper"]
    world.say(
        f"Together they brushed up the crumbs, and {culprit.label} helped carry the little brushpan."
    )
    if culprit.type == "puppy":
        world.say(
            f"Then {helper.label_word} put one proper treat into {culprit.label}'s bowl and shared the rest of the snacks fairly."
        )
    else:
        world.say(
            f"Then {helper.label_word} put the snacks back in the middle so everyone could share them fairly."
        )
    world.say(
        f'Soon the mystery was over, the room was tidy again, and {sleuth.id} smiled. "{snack.crunch_word.capitalize()} can be a clue," {sleuth.pronoun()} said, "but asking kindly solves the best mysteries."'
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    opening(world)
    world.para()
    mysterious_crunch(world)
    gather_suspects(world)
    question_suspect(world)
    inspect_clue(world)
    solve_case(world)
    gentle_end(world)
    return world


KNOWLEDGE = {
    "cracker": [
        (
            "Why do crackers make a crunch sound?",
            "Crackers are dry and crisp, so they break into little pieces when you bite them. Those tiny breaks make the crunch sound.",
        )
    ],
    "carrot": [
        (
            "Why can a carrot crunch?",
            "A carrot is firm and crisp, so your teeth snap through it with a crunch. Fresh carrots sound louder because they are stiff and juicy inside.",
        )
    ],
    "apple": [
        (
            "Why do apple slices crunch?",
            "Apple slices are crisp, so biting them breaks many tiny cells at once. That is why a fresh apple can sound loud and snappy.",
        )
    ],
    "toast": [
        (
            "Why does toast leave crumbs?",
            "Toast is dry and brittle after it is heated, so little flakes break off easily. That is why crumbs often fall when someone takes a bite.",
        )
    ],
    "crumbs": [
        (
            "What are crumbs?",
            "Crumbs are tiny bits that fall off food when it breaks or is bitten. They can show where a snack went.",
        )
    ],
    "smell": [
        (
            "How can smell help solve a mystery?",
            "A smell can stay on the air or on someone's whiskers for a little while. That can help a careful person guess what was just eaten.",
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show where someone walked and how big they were. Small tracks and big tracks can point to different suspects.",
        )
    ],
    "truth": [
        (
            "Why is it good to tell the truth after a mistake?",
            "Telling the truth helps people fix the problem together. It also helps others trust you again.",
        )
    ],
}


def pair_name(suspect_cfg: SuspectCfg) -> str:
    if suspect_cfg.pet_like:
        return f"the puppy {suspect_cfg.name}"
    if suspect_cfg.id == "brother":
        return f"the brother {suspect_cfg.name}"
    if suspect_cfg.id == "sister":
        return f"the sister {suspect_cfg.name}"
    return suspect_cfg.name


def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting"]
    snack = world.facts["snack_cfg"]
    culprit = world.facts["suspect_cfg"]
    clue = world.facts["clue_cfg"]
    sleuth = world.facts["sleuth"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "{snack.crunch_word}" and is set in {setting.place}.',
        f"Tell a gentle mystery where {sleuth.id} hears a {snack.crunch_word}, asks questions out loud, and uses a {clue.label} to discover that {pair_name(culprit)} took a snack.",
        f"Write a dialogue-heavy story about a missing {snack.label} where the clues are fair, the solving is calm, and the ending teaches kindness and truth-telling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    setting = world.facts["setting"]
    snack = world.facts["snack_cfg"]
    container = world.facts["container_cfg"]
    culprit_cfg = world.facts["suspect_cfg"]
    culprit = world.facts["culprit"]
    clue = world.facts["clue_cfg"]
    sleuth = world.facts["sleuth"]
    helper = world.facts["helper"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.id}, who hears a strange snack sound in {setting.place} and decides to solve a little mystery. {helper.label_word.capitalize()} stays calm and helps the truth come out kindly.",
        ),
        (
            "What started the mystery?",
            f"The mystery began when {sleuth.id} heard a {snack.crunch_word} near {container.phrase}. That sound mattered because the snack there was {snack.label}, which makes exactly that kind of noise.",
        ),
        (
            f"Why did {sleuth.id} think someone had taken a snack?",
            f"The sound came from the snack spot right after {helper.label_word} had said the snacks were for later. That made {sleuth.id} wonder whether somebody had sneaked one early.",
        ),
        (
            f"What clue solved the case?",
            f"The clue was a {clue.label}. {clue.explain} That clue fit {culprit.label}, so the mystery stopped being a guess and turned into an answer.",
        ),
    ]
    if outcome == "confessed":
        qa.append(
            (
                f"How was the mystery solved?",
                f"{sleuth.id} followed the clue and named {culprit.label}, and then {culprit.pronoun('subject')} admitted what had happened. The clue was strong enough that telling the truth became easier than hiding it.",
            )
        )
    else:
        qa.append(
            (
                f"How was the mystery solved?",
                f"{sleuth.id} used the clue to work out that it was {culprit.label}. Then the gentle questions and the clear evidence showed what had happened even before many words were said.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended peacefully, with the crumbs cleaned up and the snacks shared fairly. The ending shows that solving a mystery kindly can fix both the mess and the feelings around it.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    snack = world.facts["snack_cfg"]
    clue = world.facts["clue_cfg"]
    tags = {snack.id, clue.id, "truth"}
    out: list[tuple[str, str]] = []
    order = ["cracker", "carrot", "apple", "toast", "crumbs", "smell", "tracks", "truth"]
    for key in order:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.tiny:
            flags.append("tiny")
        if ent.can_reach_table:
            flags.append("reach_table")
        if ent.can_reach_shelf:
            flags.append("reach_shelf")
        if ent.can_open_lid:
            flags.append("open_lid")
        if ent.can_smell_well:
            flags.append("smell_well")
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Plausible access to the snack.
access(Sn, Cn, Su) :- crunchy(Sn), suspect(Su), container(Cn),
                      not blocked_pet_food(Sn, Su),
                      not blocked_table(Cn, Su),
                      not blocked_shelf(Cn, Su),
                      not blocked_lid(Cn, Su),
                      not blocked_pet_container(Cn, Su).

blocked_pet_food(Sn, Su) :- pet(Su), not pet_ok(Sn).
blocked_pet_container(Cn, Su) :- pet(Su), not pet_access(Cn).
blocked_table(Cn, Su) :- reach(Cn, table), not reach_table(Su).
blocked_shelf(Cn, Su) :- reach(Cn, shelf), not reach_shelf(Su).
blocked_lid(Cn, Su) :- needs_open(Cn), not open_lid(Su).

usable_clue(Su, Sn, crumbs) :- clue(crumbs), messy(Sn, M), M >= 1.
usable_clue(Su, Sn, smell)  :- clue(smell), smellful(Sn).
usable_clue(Su, Sn, tracks) :- clue(tracks).

valid(St, Sn, Cn, Su) :- setting(St), access(Sn, Cn, Su), usable_clue(Su, Sn, crumbs).
valid(St, Sn, Cn, Su) :- setting(St), access(Sn, Cn, Su), usable_clue(Su, Sn, smell).
valid(St, Sn, Cn, Su) :- setting(St), access(Sn, Cn, Su), usable_clue(Su, Sn, tracks).

chosen_valid :- chosen_setting(St), chosen_snack(Sn), chosen_container(Cn), chosen_suspect(Su),
                valid(St, Sn, Cn, Su).

outcome(confessed) :- chosen_clue(Cl), clue_sense(Cl, S), S >= 3, chosen_valid, not pet_chosen.
outcome(discovered) :- chosen_valid, pet_chosen.
outcome(discovered) :- chosen_valid, chosen_clue(Cl), clue_sense(Cl, S), S < 3.

pet_chosen :- chosen_suspect(Su), pet(Su).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        if snack.crunchy:
            lines.append(asp.fact("crunchy", snack_id))
        lines.append(asp.fact("messy", snack_id, snack.messy))
        if snack.pet_ok:
            lines.append(asp.fact("pet_ok", snack_id))
        if snack.smell:
            lines.append(asp.fact("smellful", snack_id))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("reach", container_id, container.reach))
        if container.needs_open:
            lines.append(asp.fact("needs_open", container_id))
        if container.pet_access:
            lines.append(asp.fact("pet_access", container_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        if suspect.pet_like:
            lines.append(asp.fact("pet", suspect_id))
        if suspect.can_reach_table:
            lines.append(asp.fact("reach_table", suspect_id))
        if suspect.can_reach_shelf:
            lines.append(asp.fact("reach_shelf", suspect_id))
        if suspect.can_open_lid:
            lines.append(asp.fact("open_lid", suspect_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_sense", clue_id, clue.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_container", params.container),
            asp.fact("chosen_suspect", params.suspect),
            asp.fact("chosen_clue", params.clue),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle snack whodunit with dialogue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--sleuth-name")
    ap.add_argument("--sleuth-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.container and args.suspect:
        snack = SNACKS[args.snack]
        container = CONTAINERS[args.container]
        suspect = SUSPECTS[args.suspect]
        if not suspect_can_access(suspect, container, snack):
            raise StoryError(explain_rejection(snack, container, suspect))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.snack is None or combo[1] == args.snack)
        and (args.container is None or combo[2] == args.container)
        and (args.suspect is None or combo[3] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, snack_id, container_id, suspect_id = rng.choice(sorted(combos))
    clue_choices = [
        clue_id
        for clue_id, clue in CLUES.items()
        if clue.sense >= SENSE_MIN and clue_works(clue, SUSPECTS[suspect_id], SNACKS[snack_id])
        and (args.clue is None or clue_id == args.clue)
    ]
    if not clue_choices:
        raise StoryError("(No valid clue matches the given options.)")

    clue_id = rng.choice(sorted(clue_choices))
    sleuth_gender = args.sleuth_gender or rng.choice(["girl", "boy"])
    if args.sleuth_name:
        sleuth_name = args.sleuth_name
    else:
        pool = GIRL_NAMES if sleuth_gender == "girl" else BOY_NAMES
        taken = SUSPECTS[suspect_id].name
        pool = [name for name in pool if name != taken]
        sleuth_name = rng.choice(pool)
    helper = args.helper or rng.choice(["mother", "father"])

    return StoryParams(
        setting=setting_id,
        snack=snack_id,
        container=container_id,
        suspect=suspect_id,
        clue=clue_id,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        helper=helper,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(f"{len(combos)} compatible (setting, snack, container, suspect) combos:\n")
        for setting_id, snack_id, container_id, suspect_id in combos:
            print(f"  {setting_id:8} {snack_id:8} {container_id:10} {suspect_id}")
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
                f"### {p.sleuth_name}: {p.snack} from {p.container} in {p.setting} "
                f"(suspect: {p.suspect}, clue: {p.clue}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
