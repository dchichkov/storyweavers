#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py
==============================================================================

A standalone story world for a tiny mythic domain: two young spirits prepare a
gift for the world, a small disaster leads one to borrow without asking, a
misunderstanding breaks their joy, and an elder helps them reconcile so they
can share and finish a bright arc together.

The world model is stateful rather than templated:
- one spirit's gift is damaged by a cause from the world
- that loss drives a secret borrowing
- unasked borrowing causes hurt and mistrust
- an elder listens, the truth becomes known
- apology plus sharing lets the pair complete the sky-gift

Run it
------
    python storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py
    python storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py --all
    python storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py --qa
    python storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py --trace --seed 9
    python storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py --asp
    python storyworlds/worlds/gpt-5.4/arc_misunderstanding_reconciliation_sharing_myth.py --verify
"""

from __future__ import annotations

import argparse
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "goddess", "daughter", "spirit_girl", "nymph"}
        male = {"boy", "god", "son", "spirit_boy"}
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


@dataclass
class Realm:
    id: str
    place: str
    opening: str
    people: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
    phrase: str
    vessel: str
    material: str
    color: str
    shareable: bool = True
    susceptible_to: set[str] = field(default_factory=set)
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
class Project:
    id: str
    label: str
    phrase: str
    image: str
    blessing: str
    keeper_gift: str
    borrower_gift: str
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
class Pair:
    id: str
    keeper_name: str
    keeper_type: str
    keeper_title: str
    borrower_name: str
    borrower_type: str
    borrower_title: str
    kinship: str
    project: str
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
    text: str
    trace_text: str
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
class Elder:
    id: str
    name: str
    type: str
    title: str
    entrance: str
    counsel: str
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
class Apology:
    id: str
    line: str
    gesture: str
    warmth: str
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
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
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


@dataclass
class Rule:
    name: str
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


def _r_need_after_loss(world: World) -> list[str]:
    out: list[str] = []
    borrower = world.get("borrower")
    if borrower.meters["gift_lost"] < THRESHOLD:
        return out
    sig = ("need_after_loss", borrower.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    borrower.memes["worry"] += 1
    borrower.memes["urgency"] += 1
    out.append("__need__")
    return out


def _r_hurt_from_unasked_borrow(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.get("keeper")
    if keeper.meters["gift_taken"] < THRESHOLD:
        return out
    sig = ("hurt_from_unasked_borrow", keeper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["hurt"] += 1
    keeper.memes["anger"] += 1
    keeper.memes["trust"] -= 1
    out.append("__hurt__")
    return out


def _r_calm_after_truth(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.get("keeper")
    borrower = world.get("borrower")
    if world.facts.get("truth_known", 0.0) < THRESHOLD:
        return out
    sig = ("calm_after_truth", keeper.id, borrower.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["anger"] = 0.0
    keeper.memes["understanding"] += 1
    borrower.memes["relief"] += 1
    out.append("__calm__")
    return out


def _r_reconcile_by_sharing(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.get("keeper")
    borrower = world.get("borrower")
    if keeper.meters["shared"] < THRESHOLD or borrower.meters["shared"] < THRESHOLD:
        return out
    sig = ("reconcile_by_sharing", keeper.id, borrower.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["love"] += 1
    borrower.memes["love"] += 1
    keeper.memes["trust"] += 1
    borrower.memes["trust"] += 1
    world.facts["reconciled"] = 1.0
    out.append("__reconciled__")
    return out


def _r_make_arc(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reconciled", 0.0) < THRESHOLD:
        return out
    sig = ("make_arc",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sky").meters["arc_glow"] += 1
    world.facts["arc_made"] = 1.0
    out.append("__arc__")
    return out


CAUSAL_RULES = [
    Rule(name="need_after_loss", apply=_r_need_after_loss),
    Rule(name="hurt_from_unasked_borrow", apply=_r_hurt_from_unasked_borrow),
    Rule(name="calm_after_truth", apply=_r_calm_after_truth),
    Rule(name="reconcile_by_sharing", apply=_r_reconcile_by_sharing),
    Rule(name="make_arc", apply=_r_make_arc),
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
        for sent in produced:
            world.say(sent)
    return produced


REALMS = {
    "valley": Realm(
        id="valley",
        place="the high valley",
        opening="Above the high valley, where lambs slept in silver grass,",
        people="the shepherd families below",
        detail="Every spring the valley waited for a sky-sign before the first seeds were pressed into the earth.",
        affords={"rainbow_arc", "moon_arc"},
        tags={"valley", "sky"},
    ),
    "isles": Realm(
        id="isles",
        place="the sea isles",
        opening="Beyond the sea isles, where little boats rocked like nutshells,",
        people="the fishing families below",
        detail="The people watched the heavens for a gentle promise before they sailed at dawn.",
        affords={"rainbow_arc", "moon_arc"},
        tags={"sea", "sky"},
    ),
    "cedar_glen": Realm(
        id="cedar_glen",
        place="the cedar glen",
        opening="Over the cedar glen, where ferns held dew like tiny mirrors,",
        people="the garden keepers below",
        detail="When the trees were ready to bloom, the glen longed for a blessing in the air.",
        affords={"blossom_arc", "rainbow_arc"},
        tags={"forest", "garden"},
    ),
}

GIFTS = {
    "sun_gold": Gift(
        id="sun_gold",
        label="sun-gold",
        phrase="a bowl of sun-gold",
        vessel="bowl",
        material="gold dust of dawn",
        color="golden",
        shareable=True,
        susceptible_to={"gust"},
        tags={"sun", "light"},
    ),
    "rain_beads": Gift(
        id="rain_beads",
        label="rain-beads",
        phrase="a shell of rain-beads",
        vessel="shell",
        material="blue drops from new rain",
        color="blue",
        shareable=True,
        susceptible_to={"gust", "thirsty_ground"},
        tags={"rain", "water"},
    ),
    "dew_silver": Gift(
        id="dew_silver",
        label="dew-silver",
        phrase="a cup of dew-silver",
        vessel="cup",
        material="silver drops gathered before sunrise",
        color="silver",
        shareable=True,
        susceptible_to={"gust"},
        tags={"dew", "moon"},
    ),
    "starlight_dust": Gift(
        id="starlight_dust",
        label="starlight dust",
        phrase="a pouch of starlight dust",
        vessel="pouch",
        material="white dust shaken from the hems of stars",
        color="white",
        shareable=True,
        susceptible_to={"moths"},
        tags={"star", "light"},
    ),
    "river_mist": Gift(
        id="river_mist",
        label="river-mist",
        phrase="a jar of river-mist",
        vessel="jar",
        material="cool mist lifted from the river at dawn",
        color="pale blue",
        shareable=True,
        susceptible_to={"thirsty_ground"},
        tags={"river", "mist"},
    ),
    "petal_glow": Gift(
        id="petal_glow",
        label="petal-glow",
        phrase="a basket of petal-glow",
        vessel="basket",
        material="soft light sleeping inside flower petals",
        color="rose and amber",
        shareable=True,
        susceptible_to={"moths"},
        tags={"flower", "garden"},
    ),
}

PROJECTS = {
    "rainbow_arc": Project(
        id="rainbow_arc",
        label="rainbow arc",
        phrase="a rainbow arc across the sky",
        image="a bright arc from one hill to the other",
        blessing="so the people below would remember that storm and sunlight can live together",
        keeper_gift="sun_gold",
        borrower_gift="rain_beads",
        tags={"arc", "rainbow"},
    ),
    "moon_arc": Project(
        id="moon_arc",
        label="moon arc",
        phrase="a moon-pale arc above the darkening world",
        image="a pearl arc that bent over the sleeping roofs",
        blessing="so the people below would feel brave when night came softly over the water",
        keeper_gift="dew_silver",
        borrower_gift="starlight_dust",
        tags={"arc", "moon"},
    ),
    "blossom_arc": Project(
        id="blossom_arc",
        label="blossom arc",
        phrase="a blossom-bright arc above the trees",
        image="a fragrant arc glowing over the cedar tops",
        blessing="so the people below would know the gardens were waking again",
        keeper_gift="river_mist",
        borrower_gift="petal_glow",
        tags={"arc", "blossom"},
    ),
}

PAIRS = {
    "dawn_rain": Pair(
        id="dawn_rain",
        keeper_name="Sola",
        keeper_type="girl",
        keeper_title="the little Dawn-Keeper",
        borrower_name="Rill",
        borrower_type="boy",
        borrower_title="the young Rain-Bearer",
        kinship="sky-siblings",
        project="rainbow_arc",
        tags={"siblings", "sky"},
    ),
    "moon_star": Pair(
        id="moon_star",
        keeper_name="Neri",
        keeper_type="girl",
        keeper_title="the Moon-Daughter",
        borrower_name="Tavi",
        borrower_type="boy",
        borrower_title="the Star-Herder",
        kinship="friends",
        project="moon_arc",
        tags={"night", "friends"},
    ),
    "river_garden": Pair(
        id="river_garden",
        keeper_name="Mira",
        keeper_type="girl",
        keeper_title="the River-Child",
        borrower_name="Peta",
        borrower_type="girl",
        borrower_title="the Garden-Daughter",
        kinship="friends",
        project="blossom_arc",
        tags={"garden", "friends"},
    ),
}

CAUSES = {
    "gust": Cause(
        id="gust",
        label="a wild gust",
        text="a wild gust came skipping over the ridge and tipped the vessel from small hands",
        trace_text="The wind spilled the borrowed spirit's gift before the work was done.",
        tags={"wind"},
    ),
    "moths": Cause(
        id="moths",
        label="silver moths",
        text="a ribbon of silver moths fluttered down and carried away the brightest bits",
        trace_text="The moths stole the shining pieces from the borrowed spirit's gift.",
        tags={"moths", "night"},
    ),
    "thirsty_ground": Cause(
        id="thirsty_ground",
        label="thirsty ground",
        text="the thirsty ground drank the scattered drops as soon as they touched the earth",
        trace_text="The earth soaked up the borrowed spirit's gift before it could be gathered again.",
        tags={"earth", "water"},
    ),
}

ELDERS = {
    "cloud_mother": Elder(
        id="cloud_mother",
        name="Cloud Mother",
        type="goddess",
        title="Cloud Mother",
        entrance="Then Cloud Mother came drifting on a broad white cloud and heard the sharp little voices.",
        counsel="No heart grows light by guessing in the dark. Speak your hurt, and speak the truth beside it.",
        tags={"elder", "cloud"},
    ),
    "river_grandmother": Elder(
        id="river_grandmother",
        name="River Grandmother",
        type="goddess",
        title="River Grandmother",
        entrance="River Grandmother rose from a curl of mist and listened with slow, kind eyes.",
        counsel="Water clears when it is still. Let each voice fall into the pool, and we will see the bottom.",
        tags={"elder", "river"},
    ),
    "owl_sage": Elder(
        id="owl_sage",
        name="the Owl Sage",
        type="god",
        title="the Owl Sage",
        entrance="The Owl Sage glided down from a cedar branch, silent as a thought, and opened his wide gold eyes.",
        counsel="When one wing beats alone, the flight turns crooked. Tell the whole thing, not half of it.",
        tags={"elder", "owl"},
    ),
}

APOLOGIES = {
    "plain": Apology(
        id="plain",
        line='I was afraid the work would fail, and I took some without asking. I should have spoken first.',
        gesture="set the vessel down with both hands",
        warmth="The simple truth made the hard knot in the air loosen at once.",
        tags={"apology"},
    ),
    "song": Apology(
        id="song",
        line='I was trying to finish our gift, not steal from you. I should have sung my need instead of hiding it.',
        gesture="sang the words softly, like a little wind through reeds",
        warmth="The small song carried more truth than a hurried excuse.",
        tags={"apology", "song"},
    ),
    "bow": Apology(
        id="bow",
        line='I meant to put it back after the arc was made, but that was still wrong. I should have asked for your help.',
        gesture="bowed low until their forehead nearly touched the light-streaked ground",
        warmth="The bow was humble enough to show that the apology was real.",
        tags={"apology", "bow"},
    ),
}


def pair_project(pair: Pair) -> Project:
    return PROJECTS[pair.project]


def gifts_for_pair(pair: Pair) -> tuple[Gift, Gift]:
    project = pair_project(pair)
    return GIFTS[project.keeper_gift], GIFTS[project.borrower_gift]


def cause_hits_pair(cause: Cause, pair: Pair) -> bool:
    _, borrower_gift = gifts_for_pair(pair)
    return cause.id in borrower_gift.susceptible_to and borrower_gift.shareable


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for pair_id, pair in PAIRS.items():
            project = pair_project(pair)
            if project.id not in realm.affords:
                continue
            for cause_id, cause in CAUSES.items():
                if cause_hits_pair(cause, pair):
                    combos.append((realm_id, pair_id, cause_id))
    return sorted(combos)


@dataclass
class StoryParams:
    realm: str
    pair: str
    cause: str
    elder: str
    apology: str
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


def introduce(world: World, keeper: Entity, borrower: Entity, pair: Pair,
              realm: Realm, project: Project, keeper_gift: Gift, borrower_gift: Gift) -> None:
    world.say(
        f"{realm.opening} lived {keeper.id}, {pair.keeper_title}, and {borrower.id}, "
        f"{pair.borrower_title}. They were {pair.kinship}, and together they had one dear task."
    )
    world.say(
        f"At the turning of the season, they would weave {project.phrase} {project.blessing}."
    )
    world.say(
        f"{keeper.id} carried {keeper_gift.phrase}, and {borrower.id} carried {borrower_gift.phrase}. "
        f"{realm.detail}"
    )


def damage_gift(world: World, borrower: Entity, cause: Cause, borrower_gift: Gift) -> None:
    borrower.meters["gift_lost"] = 1.0
    borrower.memes["worry"] = 0.0
    borrower.memes["urgency"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"But before the work was done, {cause.text}. In a blink, much of {borrower.id}'s "
        f"{borrower_gift.label} was gone."
    )
    world.facts["loss_happened"] = 1.0
    world.facts["loss_text"] = cause.trace_text


def quiet_borrow(world: World, keeper: Entity, borrower: Entity, keeper_gift: Gift) -> None:
    keeper.meters["gift_taken"] = 1.0
    borrower.meters["borrowed_unasked"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{borrower.id} looked at {keeper.id}'s {keeper_gift.vessel}, still shining with {keeper_gift.label}. "
        f"Wanting the sky-gift to be finished on time, {borrower.pronoun()} slipped a little into "
        f"{borrower.pronoun('possessive')} empty hands without asking."
    )


def discover_and_accuse(world: World, keeper: Entity, borrower: Entity, keeper_gift: Gift) -> None:
    world.say(
        f"When {keeper.id} turned and saw the missing light, {keeper.pronoun()} drew back. "
        f'"{borrower.id}, you took from my {keeper_gift.vessel}," {keeper.pronoun()} cried. '
        f'"You should have asked me!"'
    )
    world.say(
        f"{borrower.id}'s face went hot with shame. {borrower.pronoun().capitalize()} opened "
        f"{borrower.pronoun('possessive')} mouth, but the words came too slowly."
    )


def elder_listens(world: World, elder: Elder, keeper: Entity, borrower: Entity) -> None:
    world.say(elder.entrance)
    world.say(f'"{elder.counsel}"')
    world.say(
        f"So {keeper.id} spoke of hurt, and {borrower.id} spoke of fear."
    )


def reveal_truth(world: World, borrower: Entity, cause: Cause, apology: Apology) -> None:
    world.facts["truth_known"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{borrower.id} {apology.gesture} and said, "
        f'"{apology.line}"'
    )
    world.say(
        f"Then {borrower.pronoun()} told how {cause.label} had taken {borrower.pronoun('possessive')} own part of the gift. "
        f"{apology.warmth}"
    )


def forgive(world: World, keeper: Entity, borrower: Entity) -> None:
    world.say(
        f"{keeper.id} listened all the way to the end. Then {keeper.pronoun()} touched "
        f"{borrower.id}'s wrist and sighed. "
        f'"I thought you were stealing from me," {keeper.pronoun()} said. '
        f'"I was hurt, but now I see you were trying not to fail us."'
    )


def share_and_finish(world: World, keeper: Entity, borrower: Entity, project: Project,
                     keeper_gift: Gift, borrower_gift: Gift, realm: Realm) -> None:
    keeper.meters["shared"] = 1.0
    borrower.meters["shared"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f'Then {keeper.id} lifted {keeper.pronoun("possessive")} {keeper_gift.vessel}. '
        f'"If the gift is for both of us to make, then let it be shared," {keeper.pronoun()} said.'
    )
    world.say(
        f"Side by side they poured {keeper_gift.label} and the last of {borrower_gift.label} together. "
        f"The lights curled and climbed, making {project.image}."
    )
    world.say(
        f"Above {realm.people}, the {project.label} shone so clearly that even the smallest child below pointed up and smiled."
    )
    world.say(
        f"From that day on, whenever one of them was in trouble, {keeper.id} and {borrower.id} spoke first and shared first, "
        f"and the sky over {realm.place} seemed wider for it."
    )


def tell(realm: Realm, pair: Pair, cause: Cause, elder: Elder, apology: Apology) -> World:
    project = pair_project(pair)
    keeper_gift_cfg, borrower_gift_cfg = gifts_for_pair(pair)

    world = World(realm)
    world.facts.update(
        realm=realm,
        pair_cfg=pair,
        project_cfg=project,
        cause_cfg=cause,
        elder_cfg=elder,
        apology_cfg=apology,
        truth_known=0.0,
        reconciled=0.0,
        arc_made=0.0,
        loss_happened=0.0,
    )

    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=pair.keeper_type,
        label=pair.keeper_name,
        role="keeper",
        tags=set(pair.tags),
    ))
    borrower = world.add(Entity(
        id="borrower",
        kind="character",
        type=pair.borrower_type,
        label=pair.borrower_name,
        role="borrower",
        tags=set(pair.tags),
    ))
    elder_ent = world.add(Entity(
        id="elder",
        kind="character",
        type=elder.type,
        label=elder.name,
        role="elder",
        tags=set(elder.tags),
    ))
    sky = world.add(Entity(
        id="sky",
        kind="thing",
        type="sky",
        label="the sky",
        role="sky",
        tags={"sky"},
    ))
    keeper_gift = world.add(Entity(
        id="keeper_gift",
        kind="thing",
        type="gift",
        label=keeper_gift_cfg.label,
        role="keeper_gift",
        tags=set(keeper_gift_cfg.tags),
    ))
    borrower_gift = world.add(Entity(
        id="borrower_gift",
        kind="thing",
        type="gift",
        label=borrower_gift_cfg.label,
        role="borrower_gift",
        tags=set(borrower_gift_cfg.tags),
    ))

    for ent in (keeper, borrower):
        ent.memes["trust"] = 1.0
        ent.memes["love"] = 0.0
        ent.memes["hurt"] = 0.0
        ent.memes["anger"] = 0.0
        ent.memes["understanding"] = 0.0
        ent.memes["relief"] = 0.0
        ent.memes["worry"] = 0.0
        ent.memes["urgency"] = 0.0
    keeper.meters["gift_taken"] = 0.0
    keeper.meters["shared"] = 0.0
    borrower.meters["gift_lost"] = 0.0
    borrower.meters["borrowed_unasked"] = 0.0
    borrower.meters["shared"] = 0.0
    sky.meters["arc_glow"] = 0.0

    world.facts.update(
        keeper=keeper,
        borrower=borrower,
        elder=elder_ent,
        keeper_gift=keeper_gift,
        borrower_gift=borrower_gift,
        keeper_name=pair.keeper_name,
        borrower_name=pair.borrower_name,
    )

    introduce(world, keeper, borrower, pair, realm, project, keeper_gift_cfg, borrower_gift_cfg)
    world.para()
    damage_gift(world, borrower, cause, borrower_gift_cfg)
    quiet_borrow(world, keeper, borrower, keeper_gift_cfg)
    discover_and_accuse(world, keeper, borrower, keeper_gift_cfg)
    world.para()
    elder_listens(world, elder, keeper, borrower)
    reveal_truth(world, borrower, cause, apology)
    forgive(world, keeper, borrower)
    world.para()
    share_and_finish(world, keeper, borrower, project, keeper_gift_cfg, borrower_gift_cfg, realm)

    world.facts["outcome"] = "reconciled_shared_arc" if world.facts["arc_made"] >= THRESHOLD else "troubled"
    return world


KNOWLEDGE = {
    "arc": [
        (
            "What is an arc?",
            "An arc is a curved shape, like part of a circle. A rainbow makes an arc across the sky."
        )
    ],
    "rainbow": [
        (
            "Why does a rainbow look curved?",
            "A rainbow looks curved because the light and water drops spread in a round pattern. From the ground, we see part of that round shape as an arc."
        )
    ],
    "moon": [
        (
            "Why does moonlight look soft?",
            "Moonlight is soft because it is sunlight reflected from the moon. It is dimmer than daytime light, so it feels gentle."
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful?",
            "Sharing helps when two people both need something and want a good result together. It can turn a problem into teamwork."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what another person meant, but they are wrong. Talking and listening can clear it up."
        )
    ],
    "apology": [
        (
            "What makes an apology real?",
            "A real apology tells the truth about what went wrong and admits the mistake. It also shows care for the person who was hurt."
        )
    ],
    "wind": [
        (
            "How can wind make trouble?",
            "Wind can blow light things over or carry them away. That is why people hold bowls, papers, and hats carefully on gusty days."
        )
    ],
    "moths": [
        (
            "What are moths?",
            "Moths are insects with soft wings. Many come out in the evening and flutter around light."
        )
    ],
    "river": [
        (
            "What is mist?",
            "Mist is a cloud of tiny water drops floating close to the ground. It often rises near rivers in cool air."
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is water that forms in tiny drops on grass and leaves when the air cools. You can see it shining in the morning."
        )
    ],
}
KNOWLEDGE_ORDER = ["arc", "rainbow", "moon", "sharing", "misunderstanding", "apology", "wind", "moths", "river", "dew"]


def generation_prompts(world: World) -> list[str]:
    pair = world.facts["pair_cfg"]
    project = world.facts["project_cfg"]
    cause = world.facts["cause_cfg"]
    realm = world.facts["realm"]
    return [
        f'Write a short child-facing myth that includes the word "arc" and tells of a misunderstanding, reconciliation, and sharing.',
        f"Tell a gentle myth set over {realm.place} where {pair.keeper_name} and {pair.borrower_name} quarrel after {cause.label} causes trouble, then make peace and finish {project.phrase}.",
        f"Write a tiny myth in which one magical child borrows without asking, another feels hurt, an elder uncovers the truth, and the ending shows a shared sky-sign.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    pair = world.facts["pair_cfg"]
    project = world.facts["project_cfg"]
    cause = world.facts["cause_cfg"]
    realm = world.facts["realm"]
    apology = world.facts["apology_cfg"]
    keeper = world.facts["keeper"]
    borrower = world.facts["borrower"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair.keeper_name} and {pair.borrower_name}, two young magical helpers in the sky above {realm.place}. They were trying to make {project.phrase} for {realm.people}."
        ),
        (
            f"Why did {pair.borrower_name} take some of {pair.keeper_name}'s gift?",
            f"{pair.borrower_name}'s own part of the sky-gift was damaged when {cause.label} struck. {borrower.pronoun().capitalize()} wanted the work to be finished, so {borrower.pronoun()} borrowed in secret instead of asking for help."
        ),
        (
            f"Why did {pair.keeper_name} feel hurt?",
            f"{pair.keeper_name} saw that some of the shining gift was missing and thought it had been taken selfishly. That was the misunderstanding, because {pair.keeper_name} did not yet know what had happened to {pair.borrower_name}'s own share."
        ),
        (
            "How was the misunderstanding fixed?",
            f"An elder stopped them and made room for both hurt and truth. Then {pair.borrower_name} apologized and explained the loss, and {pair.keeper_name} listened all the way through before forgiving {borrower.pronoun('object')}."
        ),
        (
            "How did sharing change the ending?",
            f"Once they shared their gifts openly, they could finish the work together. Their shared kindness became {project.phrase}, so the ending proves they were no longer pulling apart."
        ),
        (
            f"What kind of apology did {pair.borrower_name} make?",
            f"{pair.borrower_name} {apology.gesture} and admitted the mistake plainly. The apology mattered because it named both the fear and the wrong choice."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"arc", "sharing", "misunderstanding", "apology"}
    project = world.facts["project_cfg"]
    cause = world.facts["cause_cfg"]
    pair = world.facts["pair_cfg"]
    if "rainbow" in project.tags:
        tags.add("rainbow")
    if "moon" in project.tags:
        tags.add("moon")
        tags.add("dew")
    if "river" in pair.tags or project.id == "blossom_arc":
        tags.add("river")
    if "wind" in cause.tags:
        tags.add("wind")
    if "moths" in cause.tags:
        tags.add("moths")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.label and ent.label != ent.id:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} truth_known={world.facts.get('truth_known')} reconciled={world.facts.get('reconciled')} arc_made={world.facts.get('arc_made')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="valley",
        pair="dawn_rain",
        cause="gust",
        elder="cloud_mother",
        apology="plain",
    ),
    StoryParams(
        realm="isles",
        pair="moon_star",
        cause="moths",
        elder="owl_sage",
        apology="song",
    ),
    StoryParams(
        realm="cedar_glen",
        pair="river_garden",
        cause="moths",
        elder="river_grandmother",
        apology="bow",
    ),
    StoryParams(
        realm="cedar_glen",
        pair="dawn_rain",
        cause="thirsty_ground",
        elder="cloud_mother",
        apology="song",
    ),
]


def explain_rejection(realm_id: str, pair_id: str, cause_id: str) -> str:
    realm = REALMS.get(realm_id)
    pair = PAIRS.get(pair_id)
    cause = CAUSES.get(cause_id)
    if realm is None or pair is None or cause is None:
        return "(No story: one or more requested ids are unknown.)"
    project = pair_project(pair)
    if project.id not in realm.affords:
        return (
            f"(No story: {realm.place} does not fit the myth of {project.label}. "
            f"Choose a realm that allows that sky-sign.)"
        )
    if not cause_hits_pair(cause, pair):
        _, borrower_gift = gifts_for_pair(pair)
        return (
            f"(No story: {cause.label} does not reasonably damage {borrower_gift.label}, "
            f"so it would not cause the secret borrowing that starts this misunderstanding.)"
        )
    return "(No story: this combination is unreasonable in this world.)"


ASP_RULES = r"""
project_for_pair(Pair, Proj) :- pair(Pair), proj_of_pair(Pair, Proj).
compatible_realm_pair(Realm, Pair) :- realm(Realm), project_for_pair(Pair, Proj), affords(Realm, Proj).
cause_hits_pair(Pair, Cause) :- borrower_gift_of_pair(Pair, Gift), susceptible(Gift, Cause), shareable(Gift).
valid(Realm, Pair, Cause) :- compatible_realm_pair(Realm, Pair), cause_hits_pair(Pair, Cause).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for proj in sorted(realm.affords):
            lines.append(asp.fact("affords", realm_id, proj))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        if gift.shareable:
            lines.append(asp.fact("shareable", gift_id))
        for cause in sorted(gift.susceptible_to):
            lines.append(asp.fact("susceptible", gift_id, cause))
    for pair_id, pair in PAIRS.items():
        lines.append(asp.fact("pair", pair_id))
        lines.append(asp.fact("proj_of_pair", pair_id, pair.project))
        project = pair_project(pair)
        lines.append(asp.fact("borrower_gift_of_pair", pair_id, project.borrower_gift))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic misunderstanding healed by truth and sharing."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (realm, pair, cause) set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.pair and args.cause:
        if (args.realm, args.pair, args.cause) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.realm, args.pair, args.cause))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.pair is None or combo[1] == args.pair)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, pair_id, cause_id = rng.choice(combos)
    elder_id = args.elder or rng.choice(sorted(ELDERS))
    apology_id = args.apology or rng.choice(sorted(APOLOGIES))
    return StoryParams(
        realm=realm_id,
        pair=pair_id,
        cause=cause_id,
        elder=elder_id,
        apology=apology_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(No story: unknown realm {params.realm!r}.)")
    if params.pair not in PAIRS:
        raise StoryError(f"(No story: unknown pair {params.pair!r}.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause {params.cause!r}.)")
    if params.elder not in ELDERS:
        raise StoryError(f"(No story: unknown elder {params.elder!r}.)")
    if params.apology not in APOLOGIES:
        raise StoryError(f"(No story: unknown apology {params.apology!r}.)")
    if (params.realm, params.pair, params.cause) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.realm, params.pair, params.cause))

    world = tell(
        realm=REALMS[params.realm],
        pair=PAIRS[params.pair],
        cause=CAUSES[params.cause],
        elder=ELDERS[params.elder],
        apology=APOLOGIES[params.apology],
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: empty story from curated sample.)")
        if "arc" not in sample.story.lower():
            raise StoryError('(Verify failed: story did not contain the word "arc".)')
        print("OK: curated smoke test generated a non-empty story with an arc ending.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED on curated sample: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Verify failed: empty story from default resolution.)")
        print("OK: default resolve_params() + generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED on default generation: {err}")

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
        print(f"{len(combos)} compatible (realm, pair, cause) combos:\n")
        for realm_id, pair_id, cause_id in combos:
            print(f"  {realm_id:11} {pair_id:13} {cause_id}")
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
            header = f"### {p.pair} in {p.realm} ({p.cause}, {p.elder}, {p.apology})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
