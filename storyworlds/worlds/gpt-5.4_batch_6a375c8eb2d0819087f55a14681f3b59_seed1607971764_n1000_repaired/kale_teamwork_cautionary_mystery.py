#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py
==============================================================

A standalone storyworld for a child-facing mystery about missing kale leaves.

Premise
-------
Two children notice that kale keeps disappearing from a small garden bed. One of
them wants to use a quick but unsafe "mystery fix" to stop the thief at once.
The other child slows down, follows clues, and works together with a grown-up to
find the real culprit and choose a safe solution.

This world keeps the style close to a gentle mystery:
- there is a real question at the center ("Who is eating the kale?");
- the middle turn comes from following physical clues in the garden;
- the cautionary beat rejects a harmful shortcut;
- the ending image proves what changed: the kale is protected and the children
  know who the night visitor was.

Run it
------
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py --culprit slug
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py --fix fence
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py --shortcut snap_trap
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py --all
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/kale_teamwork_cautionary_mystery.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    edible: bool = False
    helpful: bool = False
    # physical + emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
    garden_phrase: str
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


@dataclass
class Culprit:
    id: str
    label: str
    article: str
    movement: str
    bite_mark: str
    clue: str
    clue_phrase: str
    trail: str
    visits_when: str
    likes_kale: bool = True
    can_jump: bool = False
    can_squeeze: bool = False
    damp_loving: bool = False
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
class SafeFix:
    id: str
    label: str
    works_for: set[str]
    setup_text: str
    ending_text: str
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
class Shortcut:
    id: str
    label: str
    sense: int
    hurts_helpers: bool
    messy: bool
    text: str
    why_bad: str
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


def _r_missing_leaves(world: World) -> list[str]:
    out: list[str] = []
    kale = world.get("kale")
    culprit = world.get("culprit")
    if culprit.meters["visited"] >= THRESHOLD and kale.meters["nibbled"] < THRESHOLD:
        kale.meters["nibbled"] += 1
        kale.meters["lost_leaves"] += 1
        world.get("garden").meters["mystery"] += 1
        sig = ("nibbled", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__nibbled__")
    return out


def _r_leave_clue(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    if culprit.meters["visited"] < THRESHOLD:
        return out
    clue_kind = world.facts["clue_kind"]
    patch = world.get("garden")
    sig = ("clue", culprit.id, clue_kind)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patch.attrs["clue_found"] = clue_kind
    patch.meters["clue_seen"] += 1
    out.append("__clue__")
    return out


def _r_shortcut_risk(world: World) -> list[str]:
    out: list[str] = []
    if world.get("shortcut").meters["chosen"] < THRESHOLD:
        return out
    shortcut_cfg = world.facts["shortcut_cfg"]
    if shortcut_cfg.hurts_helpers:
        helper = world.get("helper")
        helper.meters["risk"] += 1
        sig = ("helper_risk", shortcut_cfg.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__risk__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_leaves", tag="physical", apply=_r_missing_leaves),
    Rule(name="leave_clue", tag="physical", apply=_r_leave_clue),
    Rule(name="shortcut_risk", tag="cautionary", apply=_r_shortcut_risk),
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


def clue_matches(culprit: Culprit, clue_kind: str) -> bool:
    return culprit.clue == clue_kind


def fix_works(culprit_id: str, fix: SafeFix) -> bool:
    return culprit_id in fix.works_for


def sensible_shortcuts() -> list[Shortcut]:
    return [s for s in SHORTCUTS.values() if s.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for culprit_id, culprit in CULPRITS.items():
            for clue_kind in CLUES:
                if not clue_matches(culprit, clue_kind):
                    continue
                for fix_id, fix in FIXES.items():
                    if fix_works(culprit_id, fix):
                        combos.append((setting_id, culprit_id, clue_kind, fix_id))
    return combos


def predict_shortcut_risk(world: World, shortcut: Shortcut) -> dict:
    sim = world.copy()
    sim.get("shortcut").meters["chosen"] = 1.0
    sim.facts["shortcut_cfg"] = shortcut
    propagate(sim, narrate=False)
    return {
        "helper_risk": sim.get("helper").meters["risk"],
        "garden_mess": float(shortcut.messy),
    }


def visit_night(world: World) -> None:
    world.get("culprit").meters["visited"] += 1
    propagate(world, narrate=False)


def introduce(world: World, kid1: Entity, kid2: Entity, grown: Entity) -> None:
    for kid in (kid1, kid2):
        kid.memes["curious"] += 1
        kid.memes["care"] += 1
    world.say(
        f"At {world.setting.place}, {kid1.id} and {kid2.id} helped {grown.label_word} "
        f"take care of {world.setting.garden_phrase}. The bed was full of curly kale, "
        f"and in the soft light it looked almost like a row of little green secrets."
    )
    world.say(world.setting.mood)


def discover_loss(world: World, kid1: Entity, kid2: Entity) -> None:
    kale = world.get("kale")
    world.say(
        f"One morning, {kid1.id} bent over the kale and stopped. "
        f"Several leaves had been chewed away in the night."
    )
    world.say(
        f'"That is strange," {kid2.id} whispered. "Someone keeps taking bites of the kale, '
        f'and nobody ever sees who."'
    )
    if kale.meters["nibbled"] >= THRESHOLD:
        world.say(
            "The mystery made the little garden feel bigger and quieter than before."
        )


def propose_shortcut(world: World, bold: Entity, careful: Entity, shortcut: Shortcut) -> None:
    bold.memes["urgency"] += 1
    world.say(
        f'{bold.id} looked around the bed and lowered {bold.pronoun("possessive")} voice. '
        f'"Maybe we should {shortcut.text}," {bold.pronoun()} said.'
    )
    world.say(
        f"For a moment, that quick plan sounded like the fastest way to catch the thief."
    )


def warn_shortcut(world: World, careful: Entity, grown: Entity, shortcut: Shortcut) -> None:
    pred = predict_shortcut_risk(world, shortcut)
    careful.memes["caution"] += 1
    world.facts["predicted_helper_risk"] = pred["helper_risk"]
    world.say(
        f'{careful.id} shook {careful.pronoun("possessive")} head. '
        f'"No. {shortcut.why_bad}," {careful.pronoun()} said.'
    )
    if pred["helper_risk"] >= THRESHOLD:
        helper = world.get("helper")
        world.say(
            f'{grown.label_word.capitalize()} nodded. "And it could hurt {helper.label}, '
            f'who helps the garden. We need clues first, not a dangerous guess."'
        )


def investigate(world: World, kid1: Entity, kid2: Entity, culprit: Culprit) -> None:
    kid1.memes["teamwork"] += 1
    kid2.memes["teamwork"] += 1
    world.say(
        f"So the two children worked together instead. {kid1.id} checked the soil, "
        f"and {kid2.id} looked under the leaves."
    )
    world.say(
        f"There they found {culprit.clue_phrase}. Suddenly the mystery did not feel empty "
        f"anymore. It felt like a trail."
    )


def reason_out(world: World, grown: Entity, culprit: Culprit) -> None:
    world.say(
        f'{grown.label_word.capitalize()} knelt beside them and studied the clue. '
        f'"{culprit.clue_phrase[0].upper()}{culprit.clue_phrase[1:]} belong to {culprit.article} '
        f'{culprit.label}," {grown.pronoun()} said.'
    )
    world.say(
        f'"It comes by {culprit.visits_when}, {culprit.movement}, and nibbles the kale."'
    )
    world.get("culprit").attrs["revealed"] = True


def choose_fix(world: World, kid1: Entity, kid2: Entity, grown: Entity,
               culprit: Culprit, fix: SafeFix) -> None:
    for kid in (kid1, kid2):
        kid.memes["relief"] += 1
        kid.memes["purpose"] += 1
    world.say(
        f'{kid1.id} looked at {kid2.id}. "{kid2.id} was right," {kid1.pronoun()} said. '
        f'"We should protect the kale without hurting anything."'
    )
    world.say(
        f"Together, they {fix.setup_text}. Their hands moved quickly, but carefully, "
        f"because solving a garden mystery was easier when nobody rushed the wrong way."
    )
    world.get("kale").meters["protected"] += 1
    world.get("garden").meters["safe"] += 1
    world.get("helper").meters["risk"] = 0.0


def ending(world: World, kid1: Entity, kid2: Entity, culprit: Culprit, fix: SafeFix) -> None:
    for kid in (kid1, kid2):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"That evening they waited by the window. When the moon rose, they finally saw "
        f"{culprit.article} {culprit.label} {culprit.movement} near the bed, exactly as the clue had promised."
    )
    world.say(
        f"{fix.ending_text} The kale stayed safe, and the children had their answer at last."
    )
    world.say(
        f"After that, whenever a mystery appeared in the garden, {kid1.id} and {kid2.id} "
        f"remembered to look for clues and make a plan together before trying anything bold."
    )


def tell(setting: Setting, culprit: Culprit, clue_kind: str, fix: SafeFix, shortcut: Shortcut,
         kid1_name: str = "Mia", kid1_gender: str = "girl",
         kid2_name: str = "Ben", kid2_gender: str = "boy",
         grown_type: str = "grandmother", bold_role: str = "kid1") -> World:
    world = World(setting)

    kid1 = world.add(Entity(
        id=kid1_name,
        kind="character",
        type=kid1_gender,
        label=kid1_name,
        role="investigator",
        attrs={"careful": bold_role != "kid1"},
    ))
    kid2 = world.add(Entity(
        id=kid2_name,
        kind="character",
        type=kid2_gender,
        label=kid2_name,
        role="investigator",
        attrs={"careful": bold_role != "kid2"},
    ))
    grown = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grown_type,
        label="the grown-up",
        role="helper",
    ))
    world.add(Entity(
        id="garden",
        type="garden",
        label="garden bed",
    ))
    world.add(Entity(
        id="kale",
        type="vegetable",
        label="kale",
        edible=True,
    ))
    world.add(Entity(
        id="culprit",
        type="animal",
        label=culprit.label,
        attrs={"visits_when": culprit.visits_when},
    ))
    world.add(Entity(
        id="helper",
        type="helper",
        label="the helpful garden beetles",
        helpful=True,
    ))
    world.add(Entity(
        id="shortcut",
        type="tool",
        label=shortcut.label,
    ))

    world.facts["clue_kind"] = clue_kind
    world.facts["shortcut_cfg"] = shortcut

    visit_night(world)

    bold = kid1 if bold_role == "kid1" else kid2
    careful = kid2 if bold_role == "kid1" else kid1

    introduce(world, kid1, kid2, grown)
    discover_loss(world, kid1, kid2)

    world.para()
    propose_shortcut(world, bold, careful, shortcut)
    warn_shortcut(world, careful, grown, shortcut)

    world.para()
    investigate(world, kid1, kid2, culprit)
    reason_out(world, grown, culprit)
    choose_fix(world, kid1, kid2, grown, culprit, fix)

    world.para()
    ending(world, kid1, kid2, culprit, fix)

    world.facts.update(
        setting=setting,
        culprit_cfg=culprit,
        fix_cfg=fix,
        shortcut_cfg=shortcut,
        kid1=kid1,
        kid2=kid2,
        grown=grown,
        bold=bold,
        careful=careful,
        clue_kind=clue_kind,
        clue_phrase=culprit.clue_phrase,
        solved=world.get("culprit").attrs.get("revealed", False),
        protected=world.get("kale").meters["protected"] >= THRESHOLD,
        risky_idea=shortcut.id,
    )
    return world


SETTINGS = {
    "schoolyard": Setting(
        id="schoolyard",
        place="the corner of the schoolyard garden",
        garden_phrase="the small raised beds behind the classroom",
        mood="A robin sang from the fence, but under the leaves the shadows looked deep enough to hide a tiny thief.",
        tags={"garden", "school"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard garden",
        garden_phrase="the neat wooden bed by the shed",
        mood="The hose was coiled in a silver loop, and the rows of vegetables looked as if they were keeping a secret.",
        tags={"garden", "home"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard garden",
        garden_phrase="the bright boxes of vegetables beside the brick wall",
        mood="The stones still held the night's coolness, and every leaf seemed to be listening for footsteps.",
        tags={"garden", "city"},
    ),
}

CLUES = {
    "slime_trail": "a silvery trail",
    "round_droppings": "little round droppings",
    "white_feather": "a loose white feather",
}

CULPRITS = {
    "slug": Culprit(
        id="slug",
        label="slug",
        article="a",
        movement="glided slowly",
        bite_mark="ragged holes",
        clue="slime_trail",
        clue_phrase="a thin silvery trail on the dark soil",
        trail="silver",
        visits_when="night",
        likes_kale=True,
        can_squeeze=True,
        damp_loving=True,
        tags={"slug", "garden_animal"},
    ),
    "rabbit": Culprit(
        id="rabbit",
        label="rabbit",
        article="a",
        movement="hopped softly",
        bite_mark="neat nibbles",
        clue="round_droppings",
        clue_phrase="little round droppings near the stems",
        trail="round prints",
        visits_when="dawn",
        likes_kale=True,
        can_jump=True,
        tags={"rabbit", "garden_animal"},
    ),
    "pigeon": Culprit(
        id="pigeon",
        label="pigeon",
        article="a",
        movement="flapped down",
        bite_mark="torn edges",
        clue="white_feather",
        clue_phrase="a loose white feather caught beside the kale",
        trail="feathers",
        visits_when="early morning",
        likes_kale=True,
        tags={"pigeon", "garden_bird"},
    ),
}

FIXES = {
    "copper_ring": SafeFix(
        id="copper_ring",
        label="copper ring",
        works_for={"slug"},
        setup_text="wrapped a bright copper ring around the kale bed",
        ending_text="The slug reached the edge, touched the copper, and turned away into the grass",
        qa_text="They put a copper ring around the bed so the slug would turn away",
        tags={"copper", "garden_safety"},
    ),
    "fence": SafeFix(
        id="fence",
        label="small fence",
        works_for={"rabbit"},
        setup_text="tied up a small fence around the kale with string and careful knots",
        ending_text="The rabbit sniffed at the little fence, twitched its nose, and hopped off to the clover instead",
        qa_text="They built a small fence so the rabbit could not reach the kale",
        tags={"fence", "garden_safety"},
    ),
    "net_cover": SafeFix(
        id="net_cover",
        label="soft net cover",
        works_for={"pigeon"},
        setup_text="spread a soft net cover over the kale and tucked the edges down neatly",
        ending_text="The pigeon landed on the path, tilted its head at the covered bed, and then pecked for seeds somewhere else",
        qa_text="They covered the kale with a soft net so the pigeon could not peck the leaves",
        tags={"net", "garden_safety"},
    ),
}

SHORTCUTS = {
    "soap_spray": Shortcut(
        id="soap_spray",
        label="strong soap spray",
        sense=1,
        hurts_helpers=True,
        messy=True,
        text="mix a strong soap spray and splash every leaf",
        why_bad="that could coat the kale and bother the helpful bugs too",
        tags={"spray", "harmful"},
    ),
    "snap_trap": Shortcut(
        id="snap_trap",
        label="snap trap",
        sense=1,
        hurts_helpers=True,
        messy=False,
        text="set a snapping trap right beside the bed",
        why_bad="that could hurt the wrong creature, or even a helping hand",
        tags={"trap", "harmful"},
    ),
    "safe_watch": Shortcut(
        id="safe_watch",
        label="quiet watch",
        sense=2,
        hurts_helpers=False,
        messy=False,
        text="sit quietly and watch for clues first",
        why_bad="that part is safe, but guessing without clues would still not solve much",
        tags={"observe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Anna", "Lucy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    setting: str
    culprit: str
    clue: str
    fix: str
    shortcut: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    grown: str
    bold_role: str
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
    "slug": [(
        "What is a slug?",
        "A slug is a soft little animal with no shell. It often comes out when it is damp and can nibble leaves in a garden."
    )],
    "rabbit": [(
        "Why might a rabbit eat garden leaves?",
        "Rabbits eat plants, and tender leaves can look like a snack to them. If a garden is easy to reach, a rabbit may hop in and nibble."
    )],
    "pigeon": [(
        "What is a pigeon?",
        "A pigeon is a bird with strong wings and quick feet. It can land in a garden, peck around, and fly away again."
    )],
    "copper": [(
        "Why do gardeners use a copper ring for slugs?",
        "A copper ring is a gentle barrier around a plant bed. It helps turn slugs away without spraying poison on the leaves."
    )],
    "fence": [(
        "What does a garden fence do?",
        "A little garden fence makes a boundary around plants. It helps keep larger nibblers, like rabbits, from reaching the leaves."
    )],
    "net": [(
        "Why use a soft net cover in a garden?",
        "A soft net cover lets light and air in while keeping birds away from the leaves. It protects the plants without hurting the birds."
    )],
    "trap": [(
        "Why can traps be a bad idea in a garden?",
        "A trap can hurt the wrong animal, or even a person who reaches into the garden. When children are unsure, they should ask a grown-up and choose a safer plan."
    )],
    "spray": [(
        "Why should children not spray mystery mixtures on food plants?",
        "Food plants should stay clean and safe to eat. Spraying a strong mystery mixture can bother helpful insects and leave a mess on the leaves."
    )],
    "observe": [(
        "Why is looking for clues a good first step in a mystery?",
        "Clues help you know what really happened. When you understand the problem first, you can choose a fix that truly fits."
    )],
    "garden_safety": [(
        "How can teamwork help in a garden problem?",
        "One person might notice a clue while another thinks of a careful plan. Working together helps people solve the problem without making a new one."
    )],
}
KNOWLEDGE_ORDER = [
    "slug", "rabbit", "pigeon", "copper", "fence", "net",
    "trap", "spray", "observe", "garden_safety",
]


CURATED = [
    StoryParams(
        setting="schoolyard",
        culprit="slug",
        clue="slime_trail",
        fix="copper_ring",
        shortcut="soap_spray",
        kid1="Mia",
        kid1_gender="girl",
        kid2="Ben",
        kid2_gender="boy",
        grown="grandmother",
        bold_role="kid1",
    ),
    StoryParams(
        setting="backyard",
        culprit="rabbit",
        clue="round_droppings",
        fix="fence",
        shortcut="snap_trap",
        kid1="Nora",
        kid1_gender="girl",
        kid2="Leo",
        kid2_gender="boy",
        grown="grandfather",
        bold_role="kid2",
    ),
    StoryParams(
        setting="courtyard",
        culprit="pigeon",
        clue="white_feather",
        fix="net_cover",
        shortcut="soap_spray",
        kid1="Zoe",
        kid1_gender="girl",
        kid2="Max",
        kid2_gender="boy",
        grown="grandmother",
        bold_role="kid1",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    k1 = f["kid1"]
    k2 = f["kid2"]
    culprit = f["culprit_cfg"]
    shortcut = f["shortcut_cfg"]
    fix = f["fix_cfg"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old about two children who discover that something is eating kale in a garden.',
        f"Tell a teamwork story where {k1.id} and {k2.id} follow clues, reject {shortcut.label}, and solve the mystery safely.",
        f'Write a cautionary mystery that includes the word "kale" and ends with children choosing {fix.label} instead of a harmful shortcut.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    k1 = f["kid1"]
    k2 = f["kid2"]
    grown = f["grown"]
    culprit = f["culprit_cfg"]
    fix = f["fix_cfg"]
    shortcut = f["shortcut_cfg"]
    clue_phrase = f["clue_phrase"]
    careful = f["careful"]
    bold = f["bold"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The children found that their kale had been chewed in the night, but they did not know who had done it. The missing leaves turned the garden into a little mystery they wanted to solve together."
        ),
        (
            "How did the children work together?",
            f"They searched in different ways instead of arguing. One child checked the soil while the other looked under the leaves, so together they found {clue_phrase}."
        ),
        (
            f"Why did {careful.id} say no to {shortcut.label}?",
            f"{careful.id} said no because {shortcut.why_bad}. That mattered because a quick guess could have hurt helpful creatures instead of solving the real problem."
        ),
        (
            "What clue solved the mystery?",
            f"They found {clue_phrase}. That clue pointed to {culprit.article} {culprit.label}, so the grown-up could explain who had been nibbling the kale."
        ),
        (
            "How did they protect the kale at the end?",
            f"{fix.qa_text}. They chose a fix that matched the real visitor, which is why the kale stayed safe without anyone being harmed."
        ),
        (
            f"What did {bold.id} learn?",
            f"{bold.id} learned that a fast idea is not always the best idea. Looking for clues first helped the children protect the kale in a careful way."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    culprit = f["culprit_cfg"]
    fix = f["fix_cfg"]
    shortcut = f["shortcut_cfg"]
    tags = set(culprit.tags) | set(fix.tags) | set(shortcut.tags) | {"observe", "garden_safety"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.helpful:
            bits.append("helpful=True")
        if ent.edible:
            bits.append("edible=True")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo_rejection(culprit: Culprit, clue: str, fix: SafeFix) -> str:
    if not clue_matches(culprit, clue):
        shown = CLUES[culprit.clue]
        asked = CLUES[clue]
        return (
            f"(No story: {culprit.article} {culprit.label} would leave {shown}, not {asked}. "
            f"The clue has to match the real garden visitor for the mystery to make sense.)"
        )
    if not fix_works(culprit.id, fix):
        return (
            f"(No story: {fix.label} does not fit {culprit.article} {culprit.label}. "
            f"The ending fix must actually protect the kale from the real culprit.)"
        )
    return "(No story: the requested combination is not reasonable.)"


def explain_shortcut(shortcut_id: str) -> str:
    shortcut = SHORTCUTS[shortcut_id]
    better = ", ".join(sorted(s.id for s in sensible_shortcuts()))
    return (
        f"(Refusing shortcut '{shortcut_id}': it scores too low on common sense "
        f"(sense={shortcut.sense} < {SENSE_MIN}). This world knows about harmful shortcuts "
        f"but will not choose them as valid solutions. Try a safer option such as: {better}.)"
    )


ASP_RULES = r"""
clue_matches(C, Cl) :- culprit(C), clue_of(C, Cl).
fix_works(C, F) :- fix(F), works_for(F, C).
valid(S, C, Cl, F) :- setting(S), culprit(C), clue(Cl), fix(F),
                      clue_matches(C, Cl), fix_works(C, F).

sensible_shortcut(Sc) :- shortcut(Sc), sense(Sc, N), sense_min(M), N >= M.

helper_risk :- chosen_shortcut(Sc), hurts_helpers(Sc).
solved :- chosen_culprit(C), chosen_clue(Cl), clue_of(C, Cl).
protected :- chosen_culprit(C), chosen_fix(F), works_for(F, C).

outcome(happy) :- solved, protected.
outcome(bad_guess) :- not solved.
outcome(bad_fix) :- solved, not protected.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("clue_of", culprit_id, culprit.clue))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for culprit_id in sorted(fix.works_for):
            lines.append(asp.fact("works_for", fix_id, culprit_id))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("sense", shortcut_id, shortcut.sense))
        if shortcut.hurts_helpers:
            lines.append(asp.fact("hurts_helpers", shortcut_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_shortcuts() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_shortcut/1."))
    return sorted(sc for (sc,) in asp.atoms(model, "sensible_shortcut"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_shortcut", params.shortcut),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def outcome_of(params: StoryParams) -> str:
    solved = clue_matches(CULPRITS[params.culprit], params.clue)
    protected = fix_works(params.culprit, FIXES[params.fix])
    if solved and protected:
        return "happy"
    if not solved:
        return "bad_guess"
    return "bad_fix"


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

    clingo_sensible = set(asp_sensible_shortcuts())
    python_sensible = {s.id for s in sensible_shortcuts()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible shortcuts match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible shortcuts: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story during verify smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a gentle garden mystery about kale, teamwork, and a careful choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--grown", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--bold-role", choices=["kid1", "kid2"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.clue and args.fix:
        culprit = CULPRITS[args.culprit]
        fix = FIXES[args.fix]
        if not (clue_matches(culprit, args.clue) and fix_works(args.culprit, fix)):
            raise StoryError(explain_combo_rejection(culprit, args.clue, fix))
    if args.shortcut and SHORTCUTS[args.shortcut].sense < SENSE_MIN:
        raise StoryError(explain_shortcut(args.shortcut))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, culprit_id, clue_kind, fix_id = rng.choice(sorted(combos))
    shortcut_id = args.shortcut or rng.choice(sorted(s.id for s in sensible_shortcuts()))
    kid1_name, kid1_gender = _pick_kid(rng)
    kid2_name, kid2_gender = _pick_kid(rng, avoid=kid1_name)
    grown = args.grown or rng.choice(["grandmother", "grandfather", "mother", "father"])
    bold_role = args.bold_role or rng.choice(["kid1", "kid2"])

    return StoryParams(
        setting=setting_id,
        culprit=culprit_id,
        clue=clue_kind,
        fix=fix_id,
        shortcut=shortcut_id,
        kid1=kid1_name,
        kid1_gender=kid1_gender,
        kid2=kid2_name,
        kid2_gender=kid2_gender,
        grown=grown,
        bold_role=bold_role,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")

    culprit = CULPRITS[params.culprit]
    fix = FIXES[params.fix]
    shortcut = SHORTCUTS[params.shortcut]

    if not clue_matches(culprit, params.clue) or not fix_works(params.culprit, fix):
        raise StoryError(explain_combo_rejection(culprit, params.clue, fix))
    if shortcut.sense < SENSE_MIN:
        raise StoryError(explain_shortcut(params.shortcut))

    world = tell(
        setting=SETTINGS[params.setting],
        culprit=culprit,
        clue_kind=params.clue,
        fix=fix,
        shortcut=shortcut,
        kid1_name=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2_name=params.kid2,
        kid2_gender=params.kid2_gender,
        grown_type=params.grown,
        bold_role=params.bold_role,
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
        print(asp_program("", "#show valid/4.\n#show sensible_shortcut/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible shortcuts: {', '.join(asp_sensible_shortcuts())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, culprit, clue, fix) combos:\n")
        for setting_id, culprit_id, clue_kind, fix_id in combos:
            print(f"  {setting_id:10} {culprit_id:8} {clue_kind:15} {fix_id}")
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
            header = f"### {p.kid1} & {p.kid2}: {p.culprit} in {p.setting} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
