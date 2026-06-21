#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grin_thingamajigger_sophisticated_sound_effects_whodunit.py
======================================================================================

A tiny whodunit-style story world about a child detective, a missing part from a
sophisticated thingamajigger, and the sound effects that solve the mystery.

The core constraint is simple: a mystery only works when the missing part could
plausibly make the heard sound from the place it was hidden. A brass bell can
jingle in a backpack or lunchbox, marbles can click in a pocket, and a little
wheel can squeak on a wagon. The world refuses mismatches.

Run it
------
    python storyworlds/worlds/gpt-5.4/grin_thingamajigger_sophisticated_sound_effects_whodunit.py
    python storyworlds/worlds/gpt-5.4/grin_thingamajigger_sophisticated_sound_effects_whodunit.py --setting school_hall --machine owl_parader
    python storyworlds/worlds/gpt-5.4/grin_thingamajigger_sophisticated_sound_effects_whodunit.py --machine marble_sorter --action wagon_squeak
    python storyworlds/worlds/gpt-5.4/grin_thingamajigger_sophisticated_sound_effects_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/grin_thingamajigger_sophisticated_sound_effects_whodunit.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class Setting:
    id: str
    place: str
    opening: str
    afford_actions: set[str] = field(default_factory=set)
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
class Piece:
    id: str
    label: str
    phrase: str
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
class Machine:
    id: str
    label: str
    phrase: str
    trick: str
    piece: str
    idle_sound: str
    final_sound: str
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
class Action:
    id: str
    container: str
    sound: str
    onomat: str
    fits: set[str] = field(default_factory=set)
    clue_line: str = ""
    carry_line: str = ""
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
class Motive:
    id: str
    reason: str
    return_line: str
    mood: str
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    piece = world.get("piece")
    detective = world.get("detective")
    if not culprit.attrs.get("has_piece"):
        return out
    if culprit.attrs.get("action_id", "") == "":
        return out
    sig = ("noise", culprit.id, culprit.attrs["action_id"])
    if sig in world.fired:
        return out
    world.fired.add(sig)
    culprit.meters["noise"] += 1
    piece.meters["hidden"] += 1
    detective.memes["curiosity"] += 1
    out.append("__noise__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    detective = world.get("detective")
    if culprit.meters["noise"] < THRESHOLD or detective.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("clue", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspicion"] += 1
    culprit.memes["worry"] += 1
    out.append("__clue__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="clue", tag="social", apply=_r_clue),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def valid_combo(machine: Machine, action: Action, setting: Setting) -> bool:
    return machine.piece in action.fits and action.id in setting.afford_actions


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid, machine in MACHINES.items():
            for aid, action in ACTIONS.items():
                if valid_combo(machine, action, setting):
                    combos.append((sid, mid, aid))
    return combos


def ending_of(motive_id: str) -> str:
    return "apology" if motive_id == "compare" else "thanks"


def predict_clue(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    culprit = sim.get("culprit")
    detective = sim.get("detective")
    return {
        "noise": culprit.meters["noise"],
        "suspicion": detective.memes["suspicion"],
    }


def introduce(world: World, detective: Entity, friend: Entity, machine: Machine, guide: Entity) -> None:
    detective.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{world.setting.opening} {detective.id} and {friend.id} stopped in front of "
        f"{machine.phrase}. It was the most sophisticated thingamajigger in the whole room."
    )
    world.say(
        f'When {guide.label_word} flipped the switch, it went {machine.idle_sound}, and both children leaned in with a grin.'
    )
    world.say(
        f"The little machine could {machine.trick}, and for one happy minute it seemed perfect."
    )


def missing_piece(world: World, detective: Entity, friend: Entity, machine: Machine, piece: Piece, owner: Entity) -> None:
    owner.memes["worry"] += 1
    world.say(
        f"Then someone noticed that {piece.phrase} was gone. Without it, the {machine.label} gave one sad hiccup and stopped."
    )
    world.say(
        f"Everyone looked at everyone else. In a room full of inventions, it suddenly felt like a real whodunit."
    )
    world.say(
        f'"Who took {piece.phrase}?" {owner.id} asked in a small voice.'
    )


def suspect_beat(world: World, culprit: Entity, action: Action) -> None:
    world.say(
        f"{culprit.id} stood near the snack table with {culprit.attrs['carrier_phrase']}. Nothing looked wrong at first."
    )
    world.say(
        f"Then {action.onomat} {action.sound}. {action.clue_line}"
    )


def listen_and_guess(world: World, detective: Entity, friend: Entity, action: Action) -> None:
    pred = predict_clue(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_suspicion"] = pred["suspicion"]
    detective.memes["care"] += 1
    world.say(
        f'{detective.id} touched {friend.id}\'s sleeve. "Listen," {detective.pronoun()} whispered. '
        f'"That sound is not coming from the table. It\'s coming from {world.get("culprit").id}\'s {action.container}."'
    )
    world.say(
        f"{friend.id} listened too and nodded. The clue was small, but it was clear."
    )


def ask_gently(world: World, detective: Entity, culprit: Entity, piece: Piece) -> None:
    culprit.memes["worry"] += 1
    world.say(
        f'{detective.id} walked over slowly. "Did {piece.phrase} end up with you by mistake?" {detective.pronoun()} asked.'
    )


def reveal(world: World, culprit: Entity, motive: Motive, piece: Piece, guide: Entity) -> None:
    culprit.attrs["has_piece"] = False
    piece.meters["hidden"] = 0.0
    piece.meters["found"] += 1
    culprit.memes["relief"] += 1
    guide.memes["relief"] += 1
    if ending_of(motive.id) == "apology":
        world.say(
            f"{culprit.id}'s cheeks turned pink. {culprit.pronoun().capitalize()} opened {culprit.pronoun('possessive')} {culprit.attrs['carrier_noun']} and held up {piece.phrase}."
        )
        world.say(
            f'"I wanted to compare it with my own little kit," {culprit.pronoun()} admitted. "{motive.reason} {motive.return_line}"'
        )
    else:
        world.say(
            f"{culprit.id} blinked, then opened {culprit.pronoun('possessive')} {culprit.attrs['carrier_noun']} and held up {piece.phrase}."
        )
        world.say(
            f'"Oh! I wasn\'t stealing it," {culprit.pronoun()} said. "{motive.reason} {motive.return_line}"'
        )


def repair(world: World, machine: Machine, piece: Piece, owner: Entity, guide: Entity, culprit: Entity) -> None:
    machine_ent = world.get("machine")
    machine_ent.meters["working"] = 1.0
    owner.memes["worry"] = 0.0
    owner.memes["joy"] += 1
    culprit.memes["worry"] = 0.0
    culprit.memes["belonging"] += 1
    world.say(
        f"{guide.label_word.capitalize()} fitted {piece.phrase} back onto the {machine.label}. This time it went {machine.final_sound}, and the whole table seemed to wake up."
    )
    if ending_of(world.facts["motive"].id) == "apology":
        world.say(
            f"{owner.id} accepted the piece, and {culprit.id} gave a shy grin when everyone saw the machine work again."
        )
    else:
        world.say(
            f"{owner.id} laughed with relief, and {culprit.id} gave a bright grin when nobody stayed angry."
        )


def ending(world: World, detective: Entity, friend: Entity, machine: Machine, culprit: Entity) -> None:
    detective.memes["pride"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'{friend.id} whispered, "You solved it." {detective.id} did not boast. {detective.pronoun().capitalize()} only smiled and watched the {machine.label} sing again.'
    )
    world.say(
        f"In that busy little corner, the mystery was over. The sound effects had told the truth, and everyone listened more carefully after that."
    )


def tell(
    setting: Setting,
    machine: Machine,
    action: Action,
    motive: Motive,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    culprit_name: str = "Milo",
    culprit_gender: str = "boy",
    owner_name: str = "June",
    owner_gender: str = "girl",
    guide_type: str = "mother",
) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["careful"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["observant"],
    ))
    culprit = world.add(Entity(
        id=culprit_name,
        kind="character",
        type=culprit_gender,
        role="culprit",
        traits=["fidgety"],
        attrs={},
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=["proud"],
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_type,
        role="guide",
        label="the grown-up",
    ))
    piece_cfg = PIECES[machine.piece]
    piece = world.add(Entity(
        id="piece",
        kind="thing",
        type="piece",
        label=piece_cfg.label,
        attrs={},
    ))
    machine_ent = world.add(Entity(
        id="machine",
        kind="thing",
        type="machine",
        label=machine.label,
        attrs={},
    ))
    machine_ent.meters["working"] = 0.0
    culprit.attrs["has_piece"] = True
    culprit.attrs["action_id"] = action.id
    culprit.attrs["carrier_phrase"] = action.carry_line
    culprit.attrs["carrier_noun"] = action.container
    detective.memes["curiosity"] = 0.0
    detective.memes["suspicion"] = 0.0
    culprit.meters["noise"] = 0.0
    piece.meters["hidden"] = 0.0
    piece.meters["found"] = 0.0
    world.facts.update(
        detective=detective,
        friend=friend,
        culprit=culprit,
        owner=owner,
        guide=guide,
        machine=machine,
        action=action,
        piece_cfg=piece_cfg,
        motive=motive,
        setting=setting,
    )

    introduce(world, detective, friend, machine, guide)
    world.para()
    missing_piece(world, detective, friend, machine, piece_cfg, owner)
    world.para()
    propagate(world, narrate=False)
    suspect_beat(world, culprit, action)
    listen_and_guess(world, detective, friend, action)
    ask_gently(world, detective, culprit, piece_cfg)
    world.para()
    reveal(world, culprit, motive, piece_cfg, guide)
    repair(world, machine, piece_cfg, owner, guide, culprit)
    ending(world, detective, friend, machine, culprit)

    world.facts.update(
        solved=piece.meters["found"] >= THRESHOLD,
        ending=ending_of(motive.id),
        sound_heard=culprit.meters["noise"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "school_hall": Setting(
        id="school_hall",
        place="the school hall",
        opening="On invention day in the school hall, paper stars swung gently over the booths.",
        afford_actions={"backpack_jingle", "pocket_clack", "lunchbox_jingle"},
        tags={"school", "mystery"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the clubhouse",
        opening="At the little neighborhood clubhouse, a row of projects stood on a long folding table.",
        afford_actions={"backpack_jingle", "pocket_clack", "lunchbox_jingle"},
        tags={"clubhouse", "mystery"},
    ),
    "yard_fair": Setting(
        id="yard_fair",
        place="the yard fair",
        opening="At the sunny yard fair behind the rec center, children wandered between homemade booths.",
        afford_actions={"pocket_clack", "wagon_squeak", "backpack_jingle"},
        tags={"yard", "mystery"},
    ),
}

PIECES = {
    "bell": Piece(
        id="bell",
        label="bell",
        phrase="the tiny brass bell",
        tags={"bell", "sound"},
    ),
    "marbles": Piece(
        id="marbles",
        label="marbles",
        phrase="the three glass marbles",
        tags={"marbles", "sound"},
    ),
    "wheel": Piece(
        id="wheel",
        label="wheel",
        phrase="the little rubber wheel",
        tags={"wheel", "sound"},
    ),
}

MACHINES = {
    "owl_parader": Machine(
        id="owl_parader",
        label="owl parader",
        phrase="June's owl parader, a brass-and-cardboard parade machine",
        trick="make a tiny owl bob along while a flag waved",
        piece="bell",
        idle_sound="whirr-whirr, ting",
        final_sound="whirr-whirr, ting-ting",
        tags={"thingamajigger", "bell"},
    ),
    "marble_sorter": Machine(
        id="marble_sorter",
        label="marble sorter",
        phrase="Otis's marble sorter, a polished little chute-and-gear machine",
        trick="send marbles down three silver paths without dropping one",
        piece="marbles",
        idle_sound="tik-tik-clack",
        final_sound="tik-tik-clack, zoom",
        tags={"thingamajigger", "marbles"},
    ),
    "rocket_cart": Machine(
        id="rocket_cart",
        label="rocket cart",
        phrase="Pia's rocket cart, a shiny rolling launch machine",
        trick="pull a paper rocket in a perfect circle around a star map",
        piece="wheel",
        idle_sound="whirr... roll",
        final_sound="whirr, roll-roll, zip",
        tags={"thingamajigger", "wheel"},
    ),
}

ACTIONS = {
    "backpack_jingle": Action(
        id="backpack_jingle",
        container="backpack",
        sound="came a tiny bell-jingle",
        onomat="Jing-jing!",
        fits={"bell"},
        clue_line="The sound was exactly the kind a loose bell would make.",
        carry_line="a lumpy red backpack on one shoulder",
        tags={"backpack", "bell"},
    ),
    "lunchbox_jingle": Action(
        id="lunchbox_jingle",
        container="lunchbox",
        sound="came a bright little jingle",
        onomat="Clink-jing!",
        fits={"bell"},
        clue_line="It sounded as if metal had tapped against metal in a lunchbox.",
        carry_line="a shiny lunchbox tucked under one arm",
        tags={"lunchbox", "bell"},
    ),
    "pocket_clack": Action(
        id="pocket_clack",
        container="pocket",
        sound="came a hard glassy click-click",
        onomat="Click-clack!",
        fits={"marbles"},
        clue_line="The noise was too round and sharp to be coins.",
        carry_line="one hand pressed against a bulging pocket",
        tags={"pocket", "marbles"},
    ),
    "wagon_squeak": Action(
        id="wagon_squeak",
        container="wagon",
        sound="rose a thin rubber squeak",
        onomat="Squeak-squeak!",
        fits={"wheel"},
        clue_line="A tiny wheel sounded lonely when it turned all by itself.",
        carry_line="a toy wagon by one knee",
        tags={"wagon", "wheel"},
    ),
}

MOTIVES = {
    "protect": Motive(
        id="protect",
        reason="I saw it wobbling near the edge, and I was afraid it would roll away.",
        return_line="I meant to hand it back after the snack break.",
        mood="careful",
        tags={"careful"},
    ),
    "tidy": Motive(
        id="tidy",
        reason="I thought it had fallen off, so I picked it up while I was helping clean crumbs.",
        return_line="I should have told someone right away.",
        mood="helpful",
        tags={"helpful"},
    ),
    "compare": Motive(
        id="compare",
        reason="I wanted to see if it matched the part on my own little kit.",
        return_line="I know I should have asked first.",
        mood="sheepish",
        tags={"apology"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lena", "June", "Ruby", "Ivy", "Tessa", "Ava"]
BOY_NAMES = ["Ben", "Milo", "Otis", "Theo", "Eli", "Max", "Finn", "Sam"]


@dataclass
class StoryParams:
    setting: str
    machine: str
    action: str
    motive: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    culprit: str
    culprit_gender: str
    owner: str
    owner_gender: str
    guide: str
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
    "bell": [(
        "Why does a loose bell make a jingly sound?",
        "A bell is hollow metal, so when it bumps and shakes, the little clapper inside strikes the sides. That makes the ringing sound."
    )],
    "marbles": [(
        "Why do marbles make a click-clack sound in a pocket?",
        "Marbles are hard and smooth, so they knock against one another and against buttons or cloth. That makes quick little clicking sounds."
    )],
    "wheel": [(
        "Why can a little wheel squeak?",
        "A small wheel can squeak when rubber rubs against the ground or its axle turns dry. The rubbing makes the high sound."
    )],
    "mystery": [(
        "What is a whodunit?",
        "A whodunit is a mystery story where people try to figure out who did something. The fun comes from following clues until the answer is clear."
    )],
    "sound": [(
        "How can listening help solve a mystery?",
        "Sounds can tell you where something is, what it is made of, or what it is touching. A careful listener notices clues other people miss."
    )],
    "thingamajigger": [(
        "What is a thingamajigger?",
        "A thingamajigger is a playful word for a gadget or little machine when you do not use its exact technical name. People often say it when something looks clever and a bit complicated."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "sound", "thingamajigger", "bell", "marbles", "wheel"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    machine = f["machine"]
    piece = f["piece_cfg"]
    setting = f["setting"]
    culprit = f["culprit"]
    detective = f["detective"]
    return [
        f'Write a child-friendly whodunit set in {setting.place} about a sophisticated thingamajigger with a missing part. Include the word "grin".',
        f"Tell a mystery where {detective.id} solves a case by listening for sound effects instead of making a wild guess.",
        f"Write a gentle whodunit about {piece.label} missing from a machine and the clue leading to {culprit.id}. Use the word \"thingamajigger\"."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    culprit = f["culprit"]
    owner = f["owner"]
    guide = f["guide"]
    machine = f["machine"]
    action = f["action"]
    piece = f["piece_cfg"]
    motive = f["motive"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery?",
            f"The mystery was that {piece.phrase} was missing from the {machine.label}. Without that piece, the machine stopped working, so everyone wanted to know who had it."
        ),
        (
            f"How did {detective.id} figure it out?",
            f"{detective.id} listened carefully and noticed the sound coming from {culprit.id}'s {action.container}. The noise matched the missing {piece.label}, so the clue pointed to the right person."
        ),
        (
            f"Did {culprit.id} mean to be mean?",
            f"No. {motive.reason} {motive.return_line} That means the problem came from a bad choice, not from cruelty."
        ),
        (
            "How did the story end?",
            f"{piece.phrase.capitalize()} was put back on the {machine.label}, and the machine worked again. The children ended with relief instead of anger because they solved the mystery gently."
        ),
    ]
    if f.get("ending") == "apology":
        qa.append((
            f"Why did {culprit.id} look sheepish at the end?",
            f"{culprit.id} had taken the part to compare it and knew {culprit.pronoun()} should have asked first. The shy grin at the end showed relief after telling the truth."
        ))
    else:
        qa.append((
            f"Why was nobody angry with {culprit.id} in the end?",
            f"{culprit.id} had picked up the part for a protective or helpful reason and gave it back right away. Once the truth was known, everyone could see the mistake was fixable."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "sound", "thingamajigger"} | set(f["piece_cfg"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="school_hall",
        machine="owl_parader",
        action="backpack_jingle",
        motive="protect",
        detective="Nora",
        detective_gender="girl",
        friend="Ben",
        friend_gender="boy",
        culprit="Milo",
        culprit_gender="boy",
        owner="June",
        owner_gender="girl",
        guide="mother",
    ),
    StoryParams(
        setting="clubhouse",
        machine="marble_sorter",
        action="pocket_clack",
        motive="compare",
        detective="Ava",
        detective_gender="girl",
        friend="Theo",
        friend_gender="boy",
        culprit="Otis",
        culprit_gender="boy",
        owner="Ruby",
        owner_gender="girl",
        guide="father",
    ),
    StoryParams(
        setting="yard_fair",
        machine="rocket_cart",
        action="wagon_squeak",
        motive="tidy",
        detective="Eli",
        detective_gender="boy",
        friend="Mia",
        friend_gender="girl",
        culprit="Finn",
        culprit_gender="boy",
        owner="Pia",
        owner_gender="girl",
        guide="mother",
    ),
    StoryParams(
        setting="school_hall",
        machine="owl_parader",
        action="lunchbox_jingle",
        motive="compare",
        detective="Ivy",
        detective_gender="girl",
        friend="Sam",
        friend_gender="boy",
        culprit="Max",
        culprit_gender="boy",
        owner="Lena",
        owner_gender="girl",
        guide="father",
    ),
]


def explain_rejection(setting: Setting, machine: Machine, action: Action) -> str:
    piece = PIECES[machine.piece]
    if action.id not in setting.afford_actions:
        return (
            f"(No story: {setting.place} does not fit the clue '{action.id}'. "
            f"A {action.container} sound is not part of this scene there.)"
        )
    return (
        f"(No story: {piece.phrase} would not plausibly make the clue '{action.id}'. "
        f"The heard sound must honestly match the missing part.)"
    )


ASP_RULES = r"""
fits_machine(M, A) :- machine_piece(M, P), action_fits(A, P).
valid(S, M, A) :- setting(S), machine(M), action(A), affords(S, A), fits_machine(M, A).

outcome(apology) :- chosen_motive(compare).
outcome(thanks)  :- chosen_motive(M), motive(M), M != compare.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for aid in sorted(SETTINGS[sid].afford_actions):
            lines.append(asp.fact("affords", sid, aid))
    for mid, machine in MACHINES.items():
        lines.append(asp.fact("machine", mid))
        lines.append(asp.fact("machine_piece", mid, machine.piece))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for pid in sorted(action.fits):
            lines.append(asp.fact("action_fits", aid, pid))
    for motive in MOTIVES:
        lines.append(asp.fact("motive", motive))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(motive_id: str) -> str:
    import asp
    model = asp.one_model(asp_program(f"chosen_motive({motive_id}).", "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    bad = []
    for motive_id in MOTIVES:
        if asp_outcome(motive_id) != ending_of(motive_id):
            bad.append(motive_id)
    if not bad:
        print("OK: ASP outcome matches ending_of().")
    else:
        rc = 1
        print("MISMATCH in outcome:", bad)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Sound-effects whodunit storyworld with a sophisticated thingamajigger."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    if not choices:
        raise StoryError("(No story: ran out of distinct names for the chosen genders.)")
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.machine and args.action:
        setting = SETTINGS[args.setting]
        machine = MACHINES[args.machine]
        action = ACTIONS[args.action]
        if not valid_combo(machine, action, setting):
            raise StoryError(explain_rejection(setting, machine, action))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.machine is None or combo[1] == args.machine)
        and (args.action is None or combo[2] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, machine_id, action_id = rng.choice(sorted(combos))
    motive_id = args.motive or rng.choice(sorted(MOTIVES))
    detective_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    culprit_gender = rng.choice(["girl", "boy"])
    owner_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    detective = _pick_name(rng, detective_gender, used)
    used.add(detective)
    friend = _pick_name(rng, friend_gender, used)
    used.add(friend)
    culprit = _pick_name(rng, culprit_gender, used)
    used.add(culprit)
    owner = _pick_name(rng, owner_gender, used)
    guide = args.guide or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        machine=machine_id,
        action=action_id,
        motive=motive_id,
        detective=detective,
        detective_gender=detective_gender,
        friend=friend,
        friend_gender=friend_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        owner=owner,
        owner_gender=owner_gender,
        guide=guide,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.machine not in MACHINES:
        raise StoryError(f"(No story: unknown machine '{params.machine}'.)")
    if params.action not in ACTIONS:
        raise StoryError(f"(No story: unknown action '{params.action}'.)")
    if params.motive not in MOTIVES:
        raise StoryError(f"(No story: unknown motive '{params.motive}'.)")
    if params.guide not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown guide '{params.guide}'.)")

    setting = SETTINGS[params.setting]
    machine = MACHINES[params.machine]
    action = ACTIONS[params.action]
    motive = MOTIVES[params.motive]
    if not valid_combo(machine, action, setting):
        raise StoryError(explain_rejection(setting, machine, action))

    world = tell(
        setting=setting,
        machine=machine,
        action=action,
        motive=motive,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        guide_type=params.guide,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, machine, action) combos:\n")
        for setting, machine, action in combos:
            print(f"  {setting:11} {machine:14} {action}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting}: {p.machine} / {p.action} / {p.motive}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
