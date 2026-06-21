#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fiftieth_rhyme_pirate_tale.py
========================================================

A standalone story world for a tiny pirate celebration tale: two children need
the missing fiftieth treasure-piece for a pirate party, but the last clue on the
rhyme card is smeared. One child rushes toward the wrong hiding place, time is
lost, and a helper nudges them back with the remembered rhyme. The right rhyme
leads them to the true hiding spot, they recover the missing piece, and the
party song finally feels complete.

The world is intentionally small and constrained:

* The hidden place must exist in the chosen setting.
* The remembered cue word must rhyme with that hiding place.
* Some hiding places sit near splashing water, so a rushed wrong turn can leave
  the treasure-piece damp before the children rescue it.

Run it
------
    python storyworlds/worlds/gpt-5.4/fiftieth_rhyme_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/fiftieth_rhyme_pirate_tale.py --setting deck --hideout chest --cue best
    python storyworlds/worlds/gpt-5.4/fiftieth_rhyme_pirate_tale.py --hideout mast --cue shell
    python storyworlds/worlds/gpt-5.4/fiftieth_rhyme_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/fiftieth_rhyme_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fiftieth_rhyme_pirate_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    scene: str
    afford_hideouts: set[str] = field(default_factory=set)
    splashy: bool = False
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
class Hideout:
    id: str
    label: str
    the: str
    spot: str
    family: str
    near_water: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Cue:
    id: str
    word: str
    family: str
    remembered_line: str
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
    finish: str
    song_line: str
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
class Helper:
    id: str
    label: str
    type: str
    entrance: str
    hint_style: str
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
        self.facts: dict = {
            "near_water": False,
            "delay": 0,
            "found": False,
            "outcome": "dry",
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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_wrong_turn_raises_worry(world: World) -> list[str]:
    clue = world.get("clue")
    tide = world.get("tide")
    treasure = world.get("treasure")
    if clue.meters["wrong_turn"] < THRESHOLD:
        return []
    if treasure.meters["found"] >= THRESHOLD:
        return []
    sig = ("wrong_turn_raises_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tide.meters["near"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__worry__"]


def _r_splash_treasure(world: World) -> list[str]:
    tide = world.get("tide")
    treasure = world.get("treasure")
    if not world.facts.get("near_water", False):
        return []
    if tide.meters["near"] < THRESHOLD:
        return []
    if treasure.meters["found"] >= THRESHOLD:
        return []
    sig = ("splash_treasure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["wet"] += 1
    return ["__splash__"]


def _r_found_brings_relief(world: World) -> list[str]:
    treasure = world.get("treasure")
    if treasure.meters["found"] < THRESHOLD:
        return []
    sig = ("found_brings_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="wrong_turn_raises_worry", tag="emotional", apply=_r_wrong_turn_raises_worry),
    Rule(name="splash_treasure", tag="physical", apply=_r_splash_treasure),
    Rule(name="found_brings_relief", tag="emotional", apply=_r_found_brings_relief),
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


def supports(setting: Setting, hideout: Hideout) -> bool:
    return hideout.id in setting.afford_hideouts


def rhymes(cue: Cue, hideout: Hideout) -> bool:
    return cue.family == hideout.family


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hideout_id, hideout in HIDEOUTS.items():
            for cue_id, cue in CUES.items():
                if supports(setting, hideout) and rhymes(cue, hideout):
                    combos.append((setting_id, hideout_id, cue_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    hideout = HIDEOUTS[params.hideout]
    return "splashy" if hideout.near_water and params.delay > 0 else "dry"


def predict_risk(setting: Setting, hideout: Hideout, delay: int) -> dict:
    sim = World(setting)
    sim.add(Entity(id="clue", label="clue card"))
    sim.add(Entity(id="tide", label="the tide"))
    sim.add(Entity(id="treasure", label="treasure"))
    sim.facts["near_water"] = hideout.near_water
    sim.facts["delay"] = delay
    if delay > 0:
        sim.get("clue").meters["wrong_turn"] += 1
        propagate(sim, narrate=False)
    return {
        "wet": sim.get("treasure").meters["wet"] >= THRESHOLD,
        "tide_near": sim.get("tide").meters["near"] >= THRESHOLD,
    }


def introduce(world: World, captain: Entity, mate: Entity, helper_ent: Entity,
              treasure: Treasure) -> None:
    world.say(
        f"On the morning of Captain Gran's fiftieth voyage party, {captain.id} and "
        f"{mate.id} turned {world.setting.place} into {world.setting.scene}."
    )
    world.say(
        f"A mop handle became a mast, a blanket became a sail, and even "
        f"{helper_ent.label} was given pirate work to do."
    )
    world.say(
        f"They had strung up forty-nine bright pieces already, but {treasure.phrase} "
        f"was still missing. Without it, {treasure.finish} would not be complete."
    )


def need_clue(world: World, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    for kid in (captain, mate):
        kid.memes["hope"] += 1
    world.say(
        f'"We only need one more," {captain.id} said. "The fiftieth piece goes last, '
        f'and then we can sing the rhyme for Gran."'
    )
    world.say(
        f"{mate.id} unfolded the clue card, the one meant to lead them to "
        f"{treasure.label}."
    )


def smudge(world: World, mate: Entity, hideout: Hideout) -> None:
    clue = world.get("clue")
    clue.meters["smudged"] += 1
    wind = "sea spray" if hideout.near_water or world.setting.splashy else "a jumpy gust of wind"
    world.say(
        f"But {wind} had blurred the last word. The card now read only, "
        f'"Find the fiftieth treasure by the ..."'
    )
    world.say(
        f'{mate.id} squinted. "The place-name is gone," {mate.pronoun()} said.'
    )


def rush_wrong_way(world: World, captain: Entity, hideout: Hideout) -> None:
    clue = world.get("clue")
    captain.memes["impatience"] += 1
    clue.meters["wrong_turn"] += 1
    world.say(
        f'"Maybe it means the barrel," {captain.id} guessed, already dashing the wrong way. '
        f'Pirates in a hurry can sound bold, but this time the guess did not rhyme and did not fit.'
    )
    propagate(world, narrate=False)
    if hideout.near_water:
        world.say(
            f"While they wasted that moment, little waves kept patting near {hideout.the}."
        )
    else:
        world.say(
            "While they wasted that moment, the party bunting flapped and the children felt the time slip by."
        )


def helper_hint(world: World, helper_cfg: Helper, helper_ent: Entity, cue: Cue) -> None:
    helper_ent.memes["calm"] += 1
    world.say(
        f"{helper_cfg.entrance} {helper_ent.label.capitalize()} called after them, "
        f'"Wait, mates! I still remember the other line."'
    )
    world.say(
        f'{helper_ent.pronoun().capitalize()} said it slowly, {helper_cfg.hint_style}: '
        f'"{cue.remembered_line}"'
    )


def solve_rhyme(world: World, mate: Entity, cue: Cue, hideout: Hideout) -> None:
    mate.memes["clever"] += 1
    world.get("clue").meters["solved"] += 1
    world.say(
        f'{mate.id} stopped running and listened to the end-sound. '
        f'"{cue.word}" ... "{hideout.label}"! "{hideout.The} rhymes with {cue.word}," '
        f'{mate.pronoun()} cried.'
    )
    world.say(
        f"Now the smeared clue suddenly made sense, and the right hiding place stood bright in both their minds."
    )


def find_treasure(world: World, captain: Entity, mate: Entity,
                  treasure_cfg: Treasure, hideout: Hideout) -> None:
    treasure = world.get("treasure")
    treasure.meters["found"] += 1
    propagate(world, narrate=False)
    damp = treasure.meters["wet"] >= THRESHOLD
    if damp:
        world.say(
            f"They hurried to {hideout.spot}, and there it was: {treasure_cfg.phrase}, "
            f"a little damp but still shining."
        )
    else:
        world.say(
            f"They hurried to {hideout.spot}, and there it was: {treasure_cfg.phrase}, "
            f"tucked safe and dry exactly where the rhyme had promised."
        )
    world.say(
        f"{captain.id} lifted it high, and {mate.id} laughed so hard that the gulls answered back."
    )


def finish_party(world: World, captain: Entity, mate: Entity, helper_ent: Entity,
                 treasure_cfg: Treasure) -> None:
    treasure = world.get("treasure")
    if treasure.meters["wet"] >= THRESHOLD:
        treasure.meters["dried"] += 1
        world.say(
            f"{helper_ent.label.capitalize()} dabbed the treasure dry with a clean corner of sailcloth."
        )
    world.say(
        f"Soon {treasure_cfg.finish} was complete, with the fiftieth piece glinting at the end."
    )
    world.say(
        f'Together they sang, "{treasure_cfg.song_line}"'
    )
    world.say(
        "Captain Gran clapped, the little pirate party cheered, and the rhyme sounded truer because they had slowed down enough to hear it."
    )


def tell(setting: Setting, hideout: Hideout, cue: Cue, treasure_cfg: Treasure,
         helper_cfg: Helper, captain_name: str = "Mara", captain_gender: str = "girl",
         mate_name: str = "Finn", mate_gender: str = "boy",
         helper_type: str = "mother", delay: int = 1) -> World:
    world = World(setting)
    world.facts["near_water"] = hideout.near_water
    world.facts["delay"] = delay

    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=["eager"],
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        traits=["thoughtful"],
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_cfg.label,
        attrs={"helper_id": helper_cfg.id},
    ))
    world.add(Entity(id="clue", type="paper", label="clue card"))
    world.add(Entity(id="tide", type="water", label="the tide"))
    treasure = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        attrs={"treasure_id": treasure_cfg.id},
    ))
    treasure.meters["found"] = 0.0
    treasure.meters["wet"] = 0.0

    introduce(world, captain, mate, helper_ent, treasure_cfg)
    need_clue(world, captain, mate, treasure_cfg)

    world.para()
    smudge(world, mate, hideout)
    if delay > 0:
        rush_wrong_way(world, captain, hideout)
    else:
        world.say(
            f"{captain.id} almost bolted off, but checked {captain.pronoun('possessive')} boots and made {captain.pronoun('object')}self wait."
        )
    helper_hint(world, helper_cfg, helper_ent, cue)
    solve_rhyme(world, mate, cue, hideout)

    world.para()
    find_treasure(world, captain, mate, treasure_cfg, hideout)
    finish_party(world, captain, mate, helper_ent, treasure_cfg)

    world.facts.update(
        captain=captain,
        mate=mate,
        helper=helper_ent,
        setting=setting,
        hideout=hideout,
        cue=cue,
        treasure_cfg=treasure_cfg,
        helper_cfg=helper_cfg,
        found=world.get("treasure").meters["found"] >= THRESHOLD,
        outcome="splashy" if world.get("treasure").meters["wet"] >= THRESHOLD else "dry",
        rhyme_solved=world.get("clue").meters["solved"] >= THRESHOLD,
        wrong_turn=world.get("clue").meters["wrong_turn"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "deck": Setting(
        id="deck",
        place="the back deck",
        scene="a bright pirate ship above the flower beds",
        afford_hideouts={"mast", "chest", "bell"},
        splashy=False,
    ),
    "dock": Setting(
        id="dock",
        place="the old harbor dock",
        scene="a bobbing pirate harbor with rope loops and gull cries",
        afford_hideouts={"mast", "hook", "pier", "chest"},
        splashy=True,
    ),
    "cove": Setting(
        id="cove",
        place="the little cove",
        scene="a secret pirate bay where smooth stones shone like coins",
        afford_hideouts={"pier", "bell", "chest"},
        splashy=True,
    ),
}

HIDEOUTS = {
    "chest": Hideout(
        id="chest",
        label="chest",
        the="the chest",
        spot="the old toy chest under the striped flag",
        family="est",
        near_water=False,
        tags={"chest"},
    ),
    "mast": Hideout(
        id="mast",
        label="mast",
        the="the mast",
        spot="the broom-handle mast tied to the railing",
        family="ast",
        near_water=False,
        tags={"mast"},
    ),
    "hook": Hideout(
        id="hook",
        label="hook",
        the="the hook",
        spot="the iron hook beside the coiled rope",
        family="ook",
        near_water=False,
        tags={"hook"},
    ),
    "bell": Hideout(
        id="bell",
        label="bell",
        the="the bell",
        spot="the brass bell hanging by the hatch",
        family="ell",
        near_water=False,
        tags={"bell"},
    ),
    "pier": Hideout(
        id="pier",
        label="pier",
        the="the pier",
        spot="the last post of the little pier",
        family="eer",
        near_water=True,
        tags={"pier", "water"},
    ),
}

CUES = {
    "best": Cue(
        id="best",
        word="best",
        family="est",
        remembered_line="To make Gran smile the very best,",
        tags={"rhyme"},
    ),
    "fast": Cue(
        id="fast",
        word="fast",
        family="ast",
        remembered_line="The brave old captain sailed so fast,",
        tags={"rhyme"},
    ),
    "book": Cue(
        id="book",
        word="book",
        family="ook",
        remembered_line="Check the map and not the book,",
        tags={"rhyme"},
    ),
    "shell": Cue(
        id="shell",
        word="shell",
        family="ell",
        remembered_line="Hear the clang and find the shell,",
        tags={"rhyme", "shell"},
    ),
    "cheer": Cue(
        id="cheer",
        word="cheer",
        family="eer",
        remembered_line="One more find for fiftieth cheer,",
        tags={"rhyme", "water"},
    ),
}

TREASURES = {
    "shell": Treasure(
        id="shell",
        label="silver shell",
        phrase="the missing silver shell charm",
        finish="Gran's shell crown",
        song_line="Fifty bright pieces, hip-hip-hooray, Captain Gran sails smiling today!",
        tags={"shell", "party"},
    ),
    "coin": Treasure(
        id="coin",
        label="gold coin",
        phrase="the last gold coin token",
        finish="the treasure banner",
        song_line="Fifty gold glimmers, jingle and shine, Captain Gran, this day is thine!",
        tags={"coin", "party"},
    ),
    "star": Treasure(
        id="star",
        label="sea-star badge",
        phrase="the missing sea-star badge",
        finish="the birthday sash",
        song_line="Fifty brave voyages over the foam, Captain Gran, our hearts say home!",
        tags={"star", "party"},
    ),
}

HELPERS = {
    "parrot": Helper(
        id="parrot",
        label="the parrot",
        type="thing",
        entrance="From the rail,",
        hint_style="with a squawk and a bob of the head",
        tags={"parrot"},
    ),
    "mother": Helper(
        id="mother",
        label="mom",
        type="mother",
        entrance="From the picnic table,",
        hint_style="like a captain tapping out a beat on the wood",
        tags={"adult"},
    ),
    "father": Helper(
        id="father",
        label="dad",
        type="father",
        entrance="From beside the cake box,",
        hint_style="in a deep sea-captain voice",
        tags={"adult"},
    ),
}

GIRL_NAMES = ["Mara", "Nell", "Ruby", "Tess", "Ivy", "Lila", "Poppy", "Cora"]
BOY_NAMES = ["Finn", "Owen", "Jude", "Eli", "Nico", "Toby", "Max", "Theo"]


@dataclass
class StoryParams:
    setting: str
    hideout: str
    cue: str
    treasure: str
    helper: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    helper_type: str
    delay: int = 1
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
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme happens when words end with the same sound, like bell and shell. Rhymes help people remember songs and clues."
        )
    ],
    "pier": [
        (
            "What is a pier?",
            "A pier is a long platform that reaches out over the water. Boats can stop beside it, and people can walk on it."
        )
    ],
    "mast": [
        (
            "What is a mast?",
            "A mast is the tall pole on a boat that holds up the sails. In pirate pretend-play, a broom or pole can become a mast."
        )
    ],
    "hook": [
        (
            "What is a hook?",
            "A hook is a curved piece of metal used to hang or hold things. On a dock, hooks often help keep ropes tidy."
        )
    ],
    "bell": [
        (
            "Why would a boat have a bell?",
            "A bell can help people signal on a boat. Its clear ringing sound is easy to hear over wind and water."
        )
    ],
    "shell": [
        (
            "What is a shell charm?",
            "A shell charm is a small shell used as a decoration. It can make a crown or necklace look bright and beachy."
        )
    ],
    "water": [
        (
            "Why can things get damp near the sea?",
            "Sea water splashes and spray can land on nearby things. Even if something does not fall in, it can still get a little wet."
        )
    ],
    "parrot": [
        (
            "Why do pirate stories often have parrots?",
            "Parrots are bright, noisy birds, so they fit the lively feeling of pirate tales. In stories, they often repeat words or clues in a funny way."
        )
    ],
    "adult": [
        (
            "Why is it helpful when a grown-up stays calm?",
            "A calm grown-up can help children slow down and think clearly. That makes problems easier to solve."
        )
    ],
}
KNOWLEDGE_ORDER = ["rhyme", "pier", "mast", "hook", "bell", "shell", "water", "parrot", "adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treasure = f["treasure_cfg"]
    hideout = f["hideout"]
    cue = f["cue"]
    captain = f["captain"]
    mate = f["mate"]
    helper_cfg = f["helper_cfg"]
    outcome = f["outcome"]
    prompt1 = (
        f'Write a short pirate tale for a 3-to-5-year-old that includes the word "fiftieth" '
        f"and uses a rhyme clue to help two children find a missing treasure-piece."
    )
    prompt2 = (
        f"Tell a story where {captain.id} and {mate.id} need {treasure.phrase} for a pirate party, "
        f"but the clue card is smeared and only the remembered rhyme word {cue.word!r} helps them think of {hideout.the}."
    )
    if helper_cfg.id == "parrot":
        prompt3 = (
            "Write a playful pirate story where a parrot repeats part of a rhyme and the children solve the clue before the celebration begins."
        )
    elif outcome == "splashy":
        prompt3 = (
            "Write a gentle pirate birthday story where a rushed wrong guess costs time, the missing treasure-piece gets a little damp near the water, and a calm helper guides the children back to the right rhyme."
        )
    else:
        prompt3 = (
            "Write a warm pirate birthday story where the children pause, listen for the rhyme, and find the missing piece just in time to finish the party song."
        )
    return [prompt1, prompt2, prompt3]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    hideout = f["hideout"]
    cue = f["cue"]
    treasure = f["treasure_cfg"]
    helper_ent = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What were the children trying to find?",
            f"They were trying to find {treasure.phrase}, the missing fiftieth piece for {treasure.finish}. Without it, the pirate celebration would not feel finished."
        ),
        (
            "Why did they need the rhyme?",
            f"The last word on the clue card had been smeared, so they could not read the hiding place. The remembered rhyme helped them match {cue.word} to {hideout.label} and think of the right spot."
        ),
    ]
    if f.get("wrong_turn"):
        qa.append(
            (
                f"Why did {captain.id} and {mate.id} start to worry?",
                f"They lost time when {captain.id} rushed toward the wrong place before checking the rhyme. That mistake made the treasure feel farther away, and it mattered even more because the party was almost ready to begin."
            )
        )
    qa.append(
        (
            f"How did {helper_ent.label} help them?",
            f"{helper_ent.label.capitalize()} did not solve everything for them. {helper_ent.pronoun().capitalize()} calmly repeated the remembered line, which gave the children the sound they needed to solve the clue themselves."
        )
    )
    if outcome == "splashy":
        qa.append(
            (
                "What was different when they found the treasure-piece?",
                f"They found it a little damp near {hideout.the}, because the wrong turn gave the splashing water extra time to reach it. Even so, it was still safe to use once it had been dried."
            )
        )
    else:
        qa.append(
            (
                "What was different at the end of the story?",
                f"At the end, the missing piece was safe and dry, the rhyme had been solved, and the pirate party could finally begin. The children sounded more thoughtful because they had learned to listen before rushing."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["cue"].tags) | set(f["hideout"].tags) | set(f["helper_cfg"].tags)
    tags |= set(f["treasure_cfg"].tags)
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
        bits: list[str] = []
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts | {'captain': world.facts['captain'].id if 'captain' in world.facts else '', 'mate': world.facts['mate'].id if 'mate' in world.facts else ''}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="dock",
        hideout="pier",
        cue="cheer",
        treasure="shell",
        helper="mother",
        captain_name="Mara",
        captain_gender="girl",
        mate_name="Finn",
        mate_gender="boy",
        helper_type="mother",
        delay=1,
    ),
    StoryParams(
        setting="deck",
        hideout="chest",
        cue="best",
        treasure="coin",
        helper="parrot",
        captain_name="Ruby",
        captain_gender="girl",
        mate_name="Eli",
        mate_gender="boy",
        helper_type="mother",
        delay=0,
    ),
    StoryParams(
        setting="dock",
        hideout="hook",
        cue="book",
        treasure="star",
        helper="father",
        captain_name="Nell",
        captain_gender="girl",
        mate_name="Theo",
        mate_gender="boy",
        helper_type="father",
        delay=1,
    ),
    StoryParams(
        setting="deck",
        hideout="bell",
        cue="shell",
        treasure="shell",
        helper="parrot",
        captain_name="Poppy",
        captain_gender="girl",
        mate_name="Owen",
        mate_gender="boy",
        helper_type="mother",
        delay=0,
    ),
]


def explain_rejection(setting: Optional[Setting], hideout: Optional[Hideout], cue: Optional[Cue]) -> str:
    if setting is not None and hideout is not None and not supports(setting, hideout):
        return (
            f"(No story: {hideout.the} is not part of {setting.place}, so the clue could not honestly point there. "
            f"Pick a hiding place that belongs in that setting.)"
        )
    if hideout is not None and cue is not None and not rhymes(cue, hideout):
        return (
            f"(No story: {cue.word!r} does not rhyme with {hideout.label!r}, so the remembered line would not help solve the clue. "
            f"Pick a cue word from the same rhyme family.)"
        )
    return "(No story: this combination does not make a clear rhyme clue.)"


ASP_RULES = r"""
valid(S, H, C) :- setting(S), hideout(H), cue(C), affords(S, H), family_hideout(H, F), family_cue(C, F).

splashy :- chosen_hideout(H), near_water(H), delay(D), D > 0.
outcome(splashy) :- splashy.
outcome(dry) :- not splashy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.afford_hideouts):
            lines.append(asp.fact("affords", sid, hid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("family_hideout", hid, hideout.family))
        if hideout.near_water:
            lines.append(asp.fact("near_water", hid))
    for cid, cue in CUES.items():
        lines.append(asp.fact("cue", cid))
        lines.append(asp.fact("family_cue", cid, cue.family))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate party, a missing fiftieth piece, and a rhyme clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = no wrong turn, 1 = a rushed wrong turn first")
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-name")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible rhyme-clue set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    hideout = HIDEOUTS.get(args.hideout) if args.hideout else None
    cue = CUES.get(args.cue) if args.cue else None

    if setting is not None and hideout is not None and not supports(setting, hideout):
        raise StoryError(explain_rejection(setting, hideout, cue))
    if hideout is not None and cue is not None and not rhymes(cue, hideout):
        raise StoryError(explain_rejection(setting, hideout, cue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hideout is None or combo[1] == args.hideout)
        and (args.cue is None or combo[2] == args.cue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hideout_id, cue_id = rng.choice(sorted(combos))
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    captain_name = args.captain_name or _pick_name(rng, captain_gender)
    mate_name = args.mate_name or _pick_name(rng, mate_gender, avoid=captain_name)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        setting=setting_id,
        hideout=hideout_id,
        cue=cue_id,
        treasure=treasure_id,
        helper=helper_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.cue not in CUES:
        raise StoryError(f"(Unknown cue: {params.cue})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.helper_type not in {"mother", "father"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")
    if params.delay not in {0, 1}:
        raise StoryError("(Delay must be 0 or 1.)")

    setting = SETTINGS[params.setting]
    hideout = HIDEOUTS[params.hideout]
    cue = CUES[params.cue]
    if not supports(setting, hideout) or not rhymes(cue, hideout):
        raise StoryError(explain_rejection(setting, hideout, cue))

    helper_cfg = HELPERS[params.helper]
    world = tell(
        setting=setting,
        hideout=hideout,
        cue=cue,
        treasure_cfg=TREASURES[params.treasure],
        helper_cfg=helper_cfg,
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hideout, cue) combos:\n")
        for setting_id, hideout_id, cue_id in combos:
            print(f"  {setting_id:8} {hideout_id:8} {cue_id}")
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
                f"### {p.captain_name} & {p.mate_name}: {p.treasure} via {p.cue} -> "
                f"{p.hideout} at {p.setting} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
