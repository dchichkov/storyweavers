#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vacant_widow_transformation_twist_pirate_tale.py
============================================================================

A standalone story world for a tiny pirate-flavored tale with a transformation
and a twist: two children playing pirates discover a place that looks vacant,
but the "empty" place belongs to a widow who has been too lonely to mend it.
The children help her fix the right thing, and the shabby place transforms into
a bright new lookout.

The world is intentionally small and constraint-checked:
- a repair only makes sense when it matches the broken thing's material
- the "vacant" look is caused by visible disrepair and loneliness, not magic
- the twist is always grounded in the widow's arrival and explanation
- the ending image proves what changed in the world model

Run it
------
python storyworlds/worlds/gpt-5.4/vacant_widow_transformation_twist_pirate_tale.py
python storyworlds/worlds/gpt-5.4/vacant_widow_transformation_twist_pirate_tale.py --site cottage --repair patch_kit
python storyworlds/worlds/gpt-5.4/vacant_widow_transformation_twist_pirate_tale.py --site tower --repair broom
python storyworlds/worlds/gpt-5.4/vacant_widow_transformation_twist_pirate_tale.py --repair lantern_oil
python storyworlds/worlds/gpt-5.4/vacant_widow_transformation_twist_pirate_tale.py --all --qa
python storyworlds/worlds/gpt-5.4/vacant_widow_transformation_twist_pirate_tale.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "widow", "woman"}
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class PlayTheme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    quest: str
    send_off: str
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
class Site:
    id: str
    label: str
    phrase: str
    edge: str
    broken_item: str
    item_phrase: str
    material: str
    fix_verb: str
    transform_line: str
    decay: int
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
    phrase: str
    materials: set[str] = field(default_factory=set)
    sense: int = 0
    power: int = 0
    use_text: str = ""
    qa_text: str = ""
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
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
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


def _r_polite_trust(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("asked_first", False):
        return out
    widow = world.get("widow")
    sig = ("trust_from_asking",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    widow.memes["trust"] += 1
    widow.memes["fear"] = 0.0
    out.append("__trust__")
    return out


def _r_repair_transforms(world: World) -> list[str]:
    out: list[str] = []
    site_ent = world.get("site")
    widow = world.get("widow")
    if site_ent.meters["mended"] < THRESHOLD:
        return out
    sig = ("repair_transforms",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    site_ent.meters["vacant"] = 0.0
    site_ent.meters["welcoming"] += 1
    widow.memes["hope"] += 1
    widow.memes["lonely"] = max(0.0, widow.memes["lonely"] - 1.0)
    for kid in world.kids():
        kid.memes["joy"] += 1
    out.append("__transform__")
    return out


def _r_kindness_binds(world: World) -> list[str]:
    out: list[str] = []
    widow = world.get("widow")
    site_ent = world.get("site")
    if widow.memes["trust"] < THRESHOLD or site_ent.meters["welcoming"] < THRESHOLD:
        return out
    sig = ("kindness_binds",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    widow.memes["belonging"] += 1
    for kid in world.kids():
        kid.memes["belonging"] += 1
    out.append("__belonging__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="polite_trust", tag="social", apply=_r_polite_trust),
    Rule(name="repair_transforms", tag="physical", apply=_r_repair_transforms),
    Rule(name="kindness_binds", tag="social", apply=_r_kindness_binds),
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


THEMES = {
    "pirates": PlayTheme(
        id="pirates",
        scene="a windy little harbor kingdom",
        rig="A driftwood bench was their ship, a stick was their mast, and a chalk line on the stones was the edge of the sea.",
        captain="Captain",
        mate="First Mate",
        quest="the best lookout in the bay",
        send_off="sailed off in their game again",
    ),
    "corsairs": PlayTheme(
        id="corsairs",
        scene="a salt-sprayed cove of make-believe",
        rig="A rowboat turned upside down was their ship, a red scarf was their flag, and three shells in a line marked hidden reefs.",
        captain="Captain",
        mate="Lookout",
        quest="a brave new pirate den",
        send_off="ran back to their play with sea songs in their heads",
    ),
}

SITES = {
    "cottage": Site(
        id="cottage",
        label="cottage",
        phrase="a small shore cottage",
        edge="at the far end of the lane above the harbor",
        broken_item="sail-cloth awning",
        item_phrase="the torn sail-cloth awning over the porch",
        material="cloth",
        fix_verb="patched the torn cloth and tied it firm",
        transform_line="The porch stopped looking vacant and began to look like a little captain's deck.",
        decay=2,
        tags={"cottage", "cloth"},
    ),
    "boathouse": Site(
        id="boathouse",
        label="boathouse",
        phrase="an old blue boathouse",
        edge="beside the sleepy pier",
        broken_item="crooked net curtain",
        item_phrase="the salt-stiff net curtain in the window",
        material="rope",
        fix_verb="retied the net and hung it straight",
        transform_line="The window no longer looked vacant. It winked at the water like it was awake again.",
        decay=1,
        tags={"boathouse", "rope"},
    ),
    "tower": Site(
        id="tower",
        label="tower room",
        phrase="a narrow lamp tower by the rocks",
        edge="on the black stones beyond the little beach",
        broken_item="dusty lamp",
        item_phrase="the dusty harbor lamp inside the tower room",
        material="lamp",
        fix_verb="cleaned the lamp glass and filled it carefully",
        transform_line="The tower room lost its vacant stare and shone like a watchful star above the tide.",
        decay=3,
        tags={"tower", "lamp"},
    ),
}

REPAIRS = {
    "patch_kit": Repair(
        id="patch_kit",
        label="patch kit",
        phrase="a sailor's patch kit",
        materials={"cloth"},
        sense=3,
        power=2,
        use_text="used a little sailor's patch kit from Widow Maren's basket to mend the torn cloth",
        qa_text="used a patch kit to mend the torn cloth",
        tags={"patch"},
    ),
    "twine": Repair(
        id="twine",
        label="twine",
        phrase="a spool of strong twine",
        materials={"rope"},
        sense=3,
        power=2,
        use_text="used strong twine to knot the loose net back into place",
        qa_text="used twine to tie the loose net straight again",
        tags={"rope"},
    ),
    "lantern_oil": Repair(
        id="lantern_oil",
        label="lantern oil",
        phrase="a small oil flask and rag",
        materials={"lamp"},
        sense=3,
        power=3,
        use_text="wiped the lamp glass, filled the lamp with a little oil, and set the wick right",
        qa_text="cleaned the lamp and filled it with oil",
        tags={"lamp"},
    ),
    "broom": Repair(
        id="broom",
        label="broom",
        phrase="a straw broom",
        materials={"dust"},
        sense=2,
        power=1,
        use_text="swept in neat circles until the boards looked less gray",
        qa_text="swept the place with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Ava", "Zoe", "Nora", "Lucy", "Maya", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "curious", "gentle", "brave", "thoughtful", "steady"]
APPROACHES = ["ask", "sneak"]
WIDOW_NAMES = ["Widow Maren", "Widow June", "Widow Elin"]

KNOWLEDGE = {
    "widow": [(
        "What is a widow?",
        "A widow is a woman whose husband has died. She may feel lonely or sad, so kindness can matter a lot."
    )],
    "vacant": [(
        "What does vacant mean?",
        "Vacant means empty or unused. A place can look vacant when nobody is there at that moment or when it has been left shabby and quiet."
    )],
    "patch": [(
        "What does a patch kit do?",
        "A patch kit helps mend torn cloth by covering the rip and holding it together. It can make an old sail or awning useful again."
    )],
    "rope": [(
        "Why does twine help with loose rope or netting?",
        "Twine can tie rope or netting back into place. Good knots stop things from sagging and flapping in the wind."
    )],
    "lamp": [(
        "Why does a lamp tower need a clean lamp?",
        "A clean, filled lamp can shine brightly. That helps people see the shore or the path in the dark."
    )],
    "kindness": [(
        "Why is it good to ask before using someone else's place?",
        "Asking first shows respect. It helps people feel safe and makes trust easier."
    )],
}
KNOWLEDGE_ORDER = ["widow", "vacant", "kindness", "patch", "rope", "lamp"]


def can_repair(site: Site, repair: Repair) -> bool:
    return site.material in repair.materials


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def repair_works(site: Site, repair: Repair) -> bool:
    return can_repair(site, repair) and repair.power >= site.decay


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for site_id, site in SITES.items():
        for repair_id, repair in REPAIRS.items():
            if can_repair(site, repair) and repair.sense >= SENSE_MIN:
                combos.append((site_id, repair_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    site: str
    repair: str
    approach: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    widow_name: str
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


def predict_welcome(world: World, approach: str) -> dict:
    sim = world.copy()
    sim.facts["asked_first"] = approach == "ask"
    widow = sim.get("widow")
    if approach == "sneak":
        widow.memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "trust": widow.memes["trust"],
        "fear": widow.memes["fear"],
    }


def introduce_play(world: World, a: Entity, b: Entity, theme: PlayTheme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright, windy afternoon, {a.id} and {b.id} turned the harbor path into {theme.scene}. {theme.rig}"
    )
    world.say(
        f"\"{theme.captain} {a.id} and {theme.mate} {b.id}!\" {a.id} cried. \"Today we will find {theme.quest}.\""
    )


def spot_place(world: World, a: Entity, b: Entity, site: Site) -> None:
    site_ent = world.get("site")
    site_ent.meters["vacant"] = 1.0
    world.say(
        f"Beyond the gulls and the ropes, they saw {site.phrase} {site.edge}. Its windows looked dim, and {site.item_phrase} hung in such a tired way that the place seemed vacant."
    )
    world.say(
        f"\"There,\" said {a.id}. \"A pirate lookout if ever I saw one.\""
    )
    b.memes["wonder"] += 1


def temptation(world: World, a: Entity, site: Site) -> None:
    a.memes["desire"] += 1
    world.say(
        f"{a.id} took one eager step toward the {site.label}. \"Maybe there is treasure inside,\" {a.pronoun()} whispered."
    )


def caution(world: World, b: Entity, a: Entity, site: Site) -> None:
    pred = predict_welcome(world, world.facts["planned_approach"])
    world.facts["predicted_trust"] = pred["trust"]
    world.facts["predicted_fear"] = pred["fear"]
    b.memes["caution"] += 1
    if world.facts["planned_approach"] == "ask":
        world.say(
            f"{b.id} touched {a.id}'s sleeve. \"Let's call out first,\" {b.pronoun()} said. \"A place can look vacant and still belong to someone.\""
        )
    else:
        world.say(
            f"{b.id} touched {a.id}'s sleeve. \"We should ask first,\" {b.pronoun()} said, glancing at the tired porch. \"A place can look vacant and still belong to someone.\""
        )


def ask_first(world: World, a: Entity, b: Entity) -> None:
    world.facts["asked_first"] = True
    world.history.append("asked_first")
    propagate(world, narrate=False)
    world.say(
        f"Together they cupped their hands and called, \"Ahoy the house! Is anyone there?\""
    )


def sneak_first(world: World, a: Entity, b: Entity, site: Site) -> None:
    widow = world.get("widow")
    widow.memes["fear"] += 1
    world.facts["asked_first"] = False
    world.history.append("sneak_first")
    world.say(
        f"But the game pulled hard at {a.id}. {a.pronoun().capitalize()} crept up the path and peeped past {site.item_phrase}, with {b.id} hurrying after {a.pronoun('object')}."
    )


def widow_arrives(world: World, widow: Entity, site: Site) -> None:
    if world.facts.get("asked_first"):
        world.say(
            f"A soft voice answered from the side garden. Out came {widow.id}, a widow with a basket on her arm and sea wind in her gray scarf."
        )
    else:
        world.say(
            f"The gate clicked behind them. Out came {widow.id}, a widow with a basket on her arm and surprise in her eyes."
        )
    world.say(
        f"\"This is my {site.label},\" {widow.pronoun()} said. \"It only looks vacant because I have not had the heart to mend {site.item_phrase} since my husband died.\""
    )
    widow.memes["sadness"] += 1


def apology_or_greeting(world: World, a: Entity, b: Entity, widow: Entity) -> None:
    if world.facts.get("asked_first"):
        world.say(
            f"{a.id} and {b.id} stood very still. Then {a.id} said, \"We are sorry. We thought the place was empty.\""
        )
        world.say(
            f"{widow.id}'s face softened a little because they had called out instead of barging in."
        )
    else:
        widow.memes["fear"] += 1
        a.memes["shame"] += 1
        b.memes["shame"] += 1
        world.say(
            f"{a.id}'s pirate shoulders dropped at once. \"We are sorry,\" {a.pronoun()} said. \"We should have asked.\""
        )
        world.say(
            f"{b.id} nodded hard. \"We thought it was empty, but we were wrong.\""
        )


def offer_help(world: World, widow: Entity, repair: Repair, site: Site) -> None:
    widow.memes["trust"] += 1
    world.say(
        f"{widow.id} looked at the children, then at {site.item_phrase}. \"If you truly want to help,\" {widow.pronoun()} said, \"there is a right way to mend a place.\""
    )
    world.say(
        f"In {widow.pronoun('possessive')} basket was {repair.phrase}."
    )


def do_repair(world: World, a: Entity, b: Entity, widow: Entity, site: Site, repair: Repair) -> None:
    site_ent = world.get("site")
    site_ent.meters["mended"] += 1
    world.history.append("repaired")
    world.say(
        f"Under {widow.id}'s gentle directions, {a.id} and {b.id} {repair.use_text}. Soon they had {site.fix_verb}."
    )
    propagate(world, narrate=False)
    world.say(site.transform_line)


def share_new_name(world: World, a: Entity, b: Entity, widow: Entity, theme: PlayTheme, site: Site) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
    widow.memes["love"] += 1
    world.say(
        f"{widow.id} smiled for the first time that day. \"My husband used to call this place the Gull's Watch,\" {widow.pronoun()} said. \"Perhaps it can be lively again.\""
    )
    world.say(
        f"\"Then it can be our pirate lookout too,\" said {b.id}, and this time everyone laughed."
    )
    world.say(
        f"When the evening light turned gold, the once-vacant {site.label} looked bright and friendly. {theme.send_off}, and now they waved every time they passed the widow's gate."
    )


def tell(
    theme: PlayTheme,
    site: Site,
    repair: Repair,
    approach: str,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    widow_name: str = "Widow Maren",
    trait: str = "careful",
) -> World:
    world = World()
    world.facts["planned_approach"] = approach
    world.facts["asked_first"] = False
    world.facts["predicted_trust"] = 0.0
    world.facts["predicted_fear"] = 0.0

    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
    ))
    world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    widow = world.add(Entity(
        id=widow_name,
        kind="character",
        type="widow",
        role="widow",
        label="the widow",
    ))
    widow.memes["lonely"] = 1.0
    site_ent = world.add(Entity(
        id="site",
        kind="thing",
        type="place",
        label=site.label,
        phrase=site.phrase,
    ))
    site_ent.meters["vacant"] = 1.0
    site_ent.meters["mended"] = 0.0
    site_ent.meters["welcoming"] = 0.0

    introduce_play(world, a, b, theme)
    spot_place(world, a, b, site)

    world.para()
    temptation(world, a, site)
    caution(world, b, a, site)

    if approach == "ask":
        ask_first(world, a, b)
    else:
        sneak_first(world, a, b, site)

    world.para()
    widow_arrives(world, widow, site)
    apology_or_greeting(world, a, b, widow)

    world.para()
    offer_help(world, widow, repair, site)
    do_repair(world, a, b, widow, site, repair)

    world.para()
    share_new_name(world, a, b, widow, theme, site)

    outcome = "welcomed" if approach == "ask" else "apology"
    world.facts.update(
        theme=theme,
        site_cfg=site,
        repair_cfg=repair,
        instigator=a,
        cautioner=b,
        widow=widow,
        outcome=outcome,
        transformed=site_ent.meters["welcoming"] >= THRESHOLD,
        repaired=site_ent.meters["mended"] >= THRESHOLD,
    )
    return world


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two young pirates"
    if a.type == "girl" and b.type == "girl":
        return "two young pirate girls"
    return "two young pirates"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    site = f["site_cfg"]
    repair = f["repair_cfg"]
    widow = f["widow"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short pirate-flavored story for a 3-to-5-year-old that includes the words "vacant" and "widow".',
        f"Tell a story where {a.id} and {b.id} think {site.phrase} is vacant, but the twist is that {widow.id} the widow still lives there.",
        f"Write a transformation story in which children mend {site.item_phrase} with {repair.label} and turn a lonely place bright again.",
    ]
    if outcome == "apology":
        prompts.append(
            f"Make the children start with the wrong choice by sneaking close first, then apologize and earn trust by helping."
        )
    else:
        prompts.append(
            f"Make the children call out politely before entering, so the widow feels safe enough to accept their help."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    widow = f["widow"]
    site = f["site_cfg"]
    repair = f["repair_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, and {widow.id}, the widow who owned the place they found."
        ),
        (
            f"Why did the {site.label} seem vacant at first?",
            f"It seemed vacant because the windows were dim and {site.item_phrase} looked tired and broken. The shabby outside made the children think nobody cared for it anymore."
        ),
        (
            f"What was the twist in the story?",
            f"The twist was that the place was not empty at all. It belonged to {widow.id}, a widow who had been too sad and lonely to mend it since her husband died."
        ),
    ]
    if f["outcome"] == "welcomed":
        qa.append((
            "How did the children first speak to the widow?",
            f"They called out before going in, and that helped {widow.id} feel safer. Asking first showed respect, so trust could grow right away."
        ))
    else:
        qa.append((
            "What mistake did the children make, and how did they fix it?",
            f"They crept up without asking because the pirate game pulled them along. Then they apologized and helped mend the place, which is how they earned {widow.id}'s trust."
        ))
    qa.append((
        f"How did they help {widow.id}?",
        f"They {repair.qa_text}. That repair changed the place from shabby and lonely to bright and cared for."
    ))
    qa.append((
        "What changed by the end of the story?",
        f"The once-vacant-looking {site.label} looked welcoming again, and {widow.id} was smiling instead of keeping to herself. The children also learned that a quiet place can still be someone's home."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"widow", "vacant", "kindness"} | set(world.facts["repair_cfg"].tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:16} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        site="cottage",
        repair="patch_kit",
        approach="ask",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        widow_name="Widow Maren",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        theme="corsairs",
        site="boathouse",
        repair="twine",
        approach="sneak",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        widow_name="Widow June",
        trait="thoughtful",
        seed=2,
    ),
    StoryParams(
        theme="pirates",
        site="tower",
        repair="lantern_oil",
        approach="ask",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        widow_name="Widow Elin",
        trait="steady",
        seed=3,
    ),
]


def explain_rejection(site: Site, repair: Repair) -> str:
    if repair.sense < SENSE_MIN:
        return (
            f"(No story: {repair.label} is too weak a fix in this world. The children need a sensible way to mend {site.item_phrase}.)"
        )
    return (
        f"(No story: {repair.label} does not fit {site.item_phrase}. The repair must match the material that is actually broken.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "welcomed" if params.approach == "ask" else "apology"


ASP_RULES = r"""
usable_repair(S, R) :- site(S), repair(R), site_material(S, M), fixes(R, M), sense(R, N), sense_min(K), N >= K.
valid(S, R) :- usable_repair(S, R).

outcome(welcomed) :- approach(ask).
outcome(apology)  :- approach(sneak).

#show valid/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, site in SITES.items():
        lines.append(asp.fact("site", sid))
        lines.append(asp.fact("site_material", sid, site.material))
        lines.append(asp.fact("decay", sid, site.decay))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
        for material in sorted(repair.materials):
            lines.append(asp.fact("fixes", rid, material))
    for app in APPROACHES:
        lines.append(asp.fact("approach_choice", app))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("approach", params.approach),
    ])
    model = asp.one_model(asp_program(extra))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    py_gate = set(valid_combos())
    asp_gate = set(asp_valid_combos())
    if py_gate == asp_gate:
        print(f"OK: gate matches valid_combos() ({len(py_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_gate - asp_gate:
            print("  only in python:", sorted(py_gate - asp_gate))
        if asp_gate - py_gate:
            print("  only in clingo:", sorted(asp_gate - py_gate))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(25):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() smoke case seed={s}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")
        for p in mismatches[:5]:
            print(f"  {p} -> python={outcome_of(p)} asp={asp_outcome(p)}")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: normal generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-flavored story world: a place that looks vacant, a widow, and a repairing transformation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (site, repair) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.repair:
        site = SITES[args.site]
        repair = REPAIRS[args.repair]
        if not (can_repair(site, repair) and repair.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(site, repair))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        site = SITES[args.site] if args.site else next(iter(SITES.values()))
        raise StoryError(explain_rejection(site, REPAIRS[args.repair]))

    combos = [
        c for c in valid_combos()
        if (args.site is None or c[0] == args.site)
        and (args.repair is None or c[1] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, repair_id = rng.choice(sorted(combos))
    instigator, ig = _pick_child(rng)
    cautioner, cg = _pick_child(rng, avoid=instigator)
    return StoryParams(
        theme=args.theme or rng.choice(sorted(THEMES)),
        site=site_id,
        repair=repair_id,
        approach=args.approach or rng.choice(APPROACHES),
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=args.parent or rng.choice(["mother", "father"]),
        widow_name=rng.choice(WIDOW_NAMES),
        trait=rng.choice(TRAITS),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(No story: unknown theme '{params.theme}'.)")
    if params.site not in SITES:
        raise StoryError(f"(No story: unknown site '{params.site}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(No story: unknown repair '{params.repair}'.)")
    if params.approach not in APPROACHES:
        raise StoryError(f"(No story: unknown approach '{params.approach}'.)")
    site = SITES[params.site]
    repair = REPAIRS[params.repair]
    if not (can_repair(site, repair) and repair.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(site, repair))

    world = tell(
        theme=THEMES[params.theme],
        site=site,
        repair=repair,
        approach=params.approach,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        widow_name=params.widow_name,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (site, repair) combinations:\n")
        for site_id, repair_id in combos:
            print(f"  {site_id:10} {repair_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.site} with {p.repair} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
