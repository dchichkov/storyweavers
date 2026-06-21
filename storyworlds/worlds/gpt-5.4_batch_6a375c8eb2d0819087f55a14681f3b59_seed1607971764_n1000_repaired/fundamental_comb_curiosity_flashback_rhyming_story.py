#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fundamental_comb_curiosity_flashback_rhyming_story.py
=================================================================================

A standalone story world about a curious child, a special comb, a tugging tangle,
and a gentle flashback that teaches a fundamental rule: start at the ends and go
slow.

The world builds small, constraint-checked rhyming stories in which:
- a child notices a treasured comb and grows curious,
- a tangle or snag makes the child rush,
- the comb gets stuck and feelings rise,
- a caregiver remembers, in a flashback, being taught the same gentle method,
- the child learns the careful way and ends in a calmer, brighter state.

Run it
------
    python storyworlds/worlds/gpt-5.4/fundamental_comb_curiosity_flashback_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/fundamental_comb_curiosity_flashback_rhyming_story.py --place bedroom --hair curls --comb wide_tooth
    python storyworlds/worlds/gpt-5.4/fundamental_comb_curiosity_flashback_rhyming_story.py --comb fine_tooth --hair curls
    python storyworlds/worlds/gpt-5.4/fundamental_comb_curiosity_flashback_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/fundamental_comb_curiosity_flashback_rhyming_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    light: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
class Hair:
    id: str
    label: str
    phrase: str
    tangle: str
    suits: set[str] = field(default_factory=set)
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
class Comb:
    id: str
    label: str
    phrase: str
    material: str
    suits: set[str] = field(default_factory=set)
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
class Snag:
    id: str
    label: str
    cause: str
    fix: str
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
class Memory:
    id: str
    scene: str
    opener: str
    helper: str
    line: str
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


def _r_tug_snag(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hair = world.get("hair")
    comb = world.get("comb")
    if child.meters["rushing"] < THRESHOLD:
        return out
    if hair.meters["tangled"] < THRESHOLD:
        return out
    sig = ("tug_snag", comb.id, hair.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hair.meters["snagged"] += 1
    comb.meters["stuck"] += 1
    child.memes["frustration"] += 1
    child.memes["worry"] += 1
    world.get("caregiver").memes["concern"] += 1
    out.append("__snag__")
    return out


def _r_gentle_smooth(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hair = world.get("hair")
    comb = world.get("comb")
    if child.meters["gentle_try"] < THRESHOLD:
        return out
    if world.facts.get("comb_ok") is not True:
        return out
    sig = ("gentle_smooth", comb.id, hair.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hair.meters["tangled"] = 0.0
    hair.meters["snagged"] = 0.0
    hair.meters["smooth"] += 1
    comb.meters["stuck"] = 0.0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = 0.0
    world.get("caregiver").memes["relief"] += 1
    out.append("__smooth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tug_snag", tag="physical", apply=_r_tug_snag),
    Rule(name="gentle_smooth", tag="physical", apply=_r_gentle_smooth),
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
            if sent == "__snag__":
                world.say("The comb gave a tiny tug, not a swish but a shrug, and worry rose quicker than a bug.")
            elif sent == "__smooth__":
                world.say("Soon the knots slipped free with a soft little swoom, and the whole head seemed to brighten the room.")
    return produced


def comb_fits(comb: Comb, hair: Hair) -> bool:
    return hair.id in comb.suits


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for snag_id in sorted(setting.affords):
            for hair_id, hair in HAIRS.items():
                for comb_id, comb in COMBS.items():
                    if snag_id in hair.suits and comb_fits(comb, hair):
                        combos.append((place, hair_id, comb_id, snag_id))
    return combos


def explain_rejection(setting: Optional[Setting], hair: Hair, comb: Comb, snag: Optional[Snag]) -> str:
    if not comb_fits(comb, hair):
        good = ", ".join(sorted(cid for cid, c in COMBS.items() if comb_fits(c, hair)))
        return (
            f"(No story: {comb.label} is not a sensible match for {hair.label}. "
            f"That comb would only make the tangles worse. Try one of: {good}.)"
        )
    if snag is not None and setting is not None and snag.id not in setting.affords:
        good = ", ".join(sorted(setting.affords))
        return (
            f"(No story: a {snag.label} does not fit {setting.place}. "
            f"That place supports these snag types: {good}.)"
        )
    if snag is not None and snag.id not in hair.suits:
        good = ", ".join(sorted(hair.suits))
        return (
            f"(No story: {hair.label} does not reasonably get a {snag.label} in this world. "
            f"Try one of these snag types for that hair: {good}.)"
        )
    return "(No story: the requested combination is not reasonable.)"


def predict_snag(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["rushing"] += 1
    propagate(sim, narrate=False)
    return {
        "snagged": sim.get("hair").meters["snagged"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, caregiver: Entity, comb: Comb) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"In {world.setting.light} light at {world.setting.place}, {child.id} found {comb.phrase} and held it just right."
    )
    world.say(
        f"It shone with a hush, not loud like a drum, and {child.id} whispered, \"Whose pretty old comb has become this home's hum?\""
    )
    world.say(
        f"{world.setting.detail} Curiosity twinkled in {child.pronoun('possessive')} eyes like a starry little kite."
    )
    caregiver.memes["tenderness"] += 1


def show_tangle(world: World, child: Entity, hair: Hair, snag: Snag) -> None:
    world.say(
        f"But on {child.pronoun('possessive')} head sat {hair.phrase}, and there in the middle was {snag.cause}."
    )
    world.say(
        f"The trouble was small, yet it pinched all the same, like a knot with a tug and a mischievous game."
    )


def ask_about_comb(world: World, child: Entity, caregiver: Entity) -> None:
    world.say(
        f"\"Why do you keep it up high? Why not in a bin?\" asked {child.id}. \"There must be a story tucked somewhere within.\""
    )
    pred = predict_snag(world)
    world.facts["predicted_snag"] = pred["snagged"]
    caregiver.memes["remembering"] += 1
    if pred["snagged"]:
        world.say(
            f"{child.id}'s {caregiver.label_word} saw the quick little hurry in {child.pronoun('possessive')} hand and thought, not yet, not that spin."
        )


def rush_pull(world: World, child: Entity, comb: Comb, hair: Hair) -> None:
    child.meters["rushing"] += 1
    child.memes["impatience"] += 1
    world.say(
        f"Still {child.id} was curious and eager to try, so {child.pronoun()} drew the {comb.label} through fast with a huff and a sigh."
    )
    propagate(world, narrate=True)
    if hair.meters["snagged"] >= THRESHOLD:
        world.say(
            f'"Ow," said {child.id}, going still as a mouse. "It stuck, and it pulled, and I do not like this in the house."'
        )


def comfort(world: World, child: Entity, caregiver: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f"{caregiver.label_word.capitalize()} knelt close and loosened {child.pronoun('possessive')} fingers. "
        f"\"A special old comb is for care, not for speed. First we breathe, then we help what your tangles need.\""
    )


def flashback(world: World, caregiver: Entity, memory: Memory, comb: Comb) -> None:
    world.para()
    world.say(
        f"Then {caregiver.label_word} smiled a small memory smile, and a flashback came floating from long-ago miles."
    )
    world.say(
        f"{memory.opener} {memory.scene}, and {memory.helper} used this very {comb.label} to put every stray little lock in its place."
    )
    world.say(
        f"Back then, a gentle voice shared a fundamental rule, warm and clear: \"{memory.line}\""
    )
    world.say(
        "The old lesson had stayed, soft as a song, and now it was ready to help once more along."
    )


def gentle_fix(world: World, child: Entity, caregiver: Entity, snag: Snag) -> None:
    world.para()
    world.say(
        f"{caregiver.label_word.capitalize()} dabbed a little water where {snag.fix}, and parted the hair with patient hands there."
    )
    world.say(
        f"\"Start at the ends,\" said {caregiver.label_word}, \"then small steps up high. Slow makes it easier. Slow lets the sore spots sigh.\""
    )
    child.meters["gentle_try"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{child.id} tried the careful way next, not with a yank but a glide, and listened to the lesson like a friend at {child.pronoun('possessive')} side."
    )


def closing(world: World, child: Entity, comb: Comb, hair: Hair) -> None:
    world.say(
        f"When the last knot was gone, {hair.phrase} lay smooth in a gleam, and {comb.phrase} no longer felt scary, but kind as a dream."
    )
    world.say(
        f"\"Now I know why you keep it,\" said {child.id} with a grin. \"The fundamental way is gentle first, and that is where care should begin.\""
    )
    world.say(
        f"And in the calm evening light at {world.setting.place}, {child.id} set the {comb.label} back softly, with wonder and grace."
    )


def tell(
    setting: Setting,
    hair_cfg: Hair,
    comb_cfg: Comb,
    snag_cfg: Snag,
    memory_cfg: Memory,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    caregiver_type: str = "mother",
    child_trait: str = "curious",
) -> World:
    world = World(setting)

    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    child.attrs["name"] = child_name
    child.attrs["trait"] = child_trait
    child.tags |= {"child"}
    child.meters["rushing"] = 0.0
    child.meters["gentle_try"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["impatience"] = 0.0
    child.memes["frustration"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["pride"] = 0.0
    child.memes["trust"] = 0.0

    caregiver = world.add(Entity(id="caregiver", kind="character", type=caregiver_type, label="the caregiver"))
    caregiver.memes["concern"] = 0.0
    caregiver.memes["remembering"] = 0.0
    caregiver.memes["relief"] = 0.0
    caregiver.memes["tenderness"] = 0.0

    hair = world.add(Entity(id="hair", kind="thing", type="hair", label=hair_cfg.label, tags=set(hair_cfg.tags)))
    hair.meters["tangled"] = 1.0
    hair.meters["snagged"] = 0.0
    hair.meters["smooth"] = 0.0

    comb = world.add(Entity(id="comb", kind="thing", type="comb", label=comb_cfg.label, tags=set(comb_cfg.tags)))
    comb.attrs["material"] = comb_cfg.material
    comb.meters["stuck"] = 0.0

    world.facts["comb_ok"] = comb_fits(comb_cfg, hair_cfg)
    world.facts["setting"] = setting
    world.facts["hair_cfg"] = hair_cfg
    world.facts["comb_cfg"] = comb_cfg
    world.facts["snag_cfg"] = snag_cfg
    world.facts["memory_cfg"] = memory_cfg
    world.facts["child_name"] = child_name
    world.facts["caregiver_type"] = caregiver_type

    opening(world, child, caregiver, comb_cfg)
    show_tangle(world, child, hair_cfg, snag_cfg)

    world.para()
    ask_about_comb(world, child, caregiver)
    rush_pull(world, child, comb_cfg, hair)
    comfort(world, child, caregiver)
    flashback(world, caregiver, memory_cfg, comb_cfg)
    gentle_fix(world, child, caregiver, snag_cfg)

    world.para()
    closing(world, child, comb_cfg, hair_cfg)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        hair=hair,
        comb=comb,
        snagged=hair.meters["snagged"] < THRESHOLD and comb.meters["stuck"] < THRESHOLD,
        learned=child.memes["pride"] >= THRESHOLD,
        smooth=hair.meters["smooth"] >= THRESHOLD,
        curiosity=child.memes["curiosity"] >= THRESHOLD,
        flashback_used=caregiver.memes["remembering"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        light="the early morning",
        detail="A quilt sat in a puff on the bed, and the window made pale stripes on the floor.",
        affords={"ribbon_knot", "sleep_tangle"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden gate",
        light="the leafy afternoon",
        detail="Sweet peas leaned by the fence, and the breeze kept brushing by with a green little swish.",
        affords={"leaf_snag", "wind_tangle"},
    ),
    "bathroom": Setting(
        id="bathroom",
        place="the bathroom stool",
        light="the steamy evening",
        detail="The mirror wore tiny cloud dots, and a towel hung nearby like a waiting sail.",
        affords={"soap_tangle", "sleep_tangle"},
    ),
}

HAIRS = {
    "curls": Hair(
        id="curls",
        label="curls",
        phrase="springy curls",
        tangle="nestled curls",
        suits={"ribbon_knot", "sleep_tangle", "leaf_snag", "soap_tangle"},
        tags={"hair", "curls"},
    ),
    "waves": Hair(
        id="waves",
        label="waves",
        phrase="long wavy hair",
        tangle="rolling waves of hair",
        suits={"sleep_tangle", "wind_tangle", "ribbon_knot"},
        tags={"hair", "waves"},
    ),
    "straight": Hair(
        id="straight",
        label="straight hair",
        phrase="straight shining hair",
        tangle="straight hair with a stubborn kink",
        suits={"sleep_tangle", "wind_tangle", "leaf_snag"},
        tags={"hair", "straight_hair"},
    ),
}

COMBS = {
    "wide_tooth": Comb(
        id="wide_tooth",
        label="wide-tooth comb",
        phrase="a honey-colored wide-tooth comb",
        material="wood",
        suits={"curls", "waves"},
        tags={"comb", "wide_tooth"},
    ),
    "pocket": Comb(
        id="pocket",
        label="pocket comb",
        phrase="a smooth pocket comb",
        material="shell",
        suits={"waves", "straight"},
        tags={"comb", "pocket_comb"},
    ),
    "fine_tooth": Comb(
        id="fine_tooth",
        label="fine-tooth comb",
        phrase="a slim fine-tooth comb",
        material="wood",
        suits={"straight"},
        tags={"comb", "fine_tooth"},
    ),
}

SNAGS = {
    "ribbon_knot": Snag(
        id="ribbon_knot",
        label="ribbon knot",
        cause="a ribbon knot left from yesterday's play",
        fix="the ribbon looped too tightly",
        tags={"ribbon"},
    ),
    "sleep_tangle": Snag(
        id="sleep_tangle",
        label="sleep tangle",
        cause="a sleepy pillow tangle from turning in dreams",
        fix="the bedhead curled into itself",
        tags={"sleep"},
    ),
    "leaf_snag": Snag(
        id="leaf_snag",
        label="leaf snag",
        cause="a tiny leaf caught where the breeze had played",
        fix="the leaf had twined itself in",
        tags={"leaf"},
    ),
    "wind_tangle": Snag(
        id="wind_tangle",
        label="wind tangle",
        cause="a wind tangle tied by the running air",
        fix="the breezy knot sat tight",
        tags={"wind"},
    ),
    "soap_tangle": Snag(
        id="soap_tangle",
        label="soap tangle",
        cause="a soap tangle left after hasty washing",
        fix="the damp knot clung together",
        tags={"soap"},
    ),
}

MEMORIES = {
    "first_school": Memory(
        id="first_school",
        scene="on the first day of school, when the morning felt bigger than a face",
        opener="Long ago",
        helper="Grandma",
        line="Start at the ends, and be patient, my dear; slow little strokes make the pathway clear.",
        tags={"flashback", "school"},
    ),
    "windy_fair": Memory(
        id="windy_fair",
        scene="after a windy fair, when ribbons had flown and laughter had raced",
        opener="Years before",
        helper="Grandpa",
        line="Do not fight every knot in one swooping sweep; begin where it loosens, and peace you will keep.",
        tags={"flashback", "fair"},
    ),
    "rainy_walk": Memory(
        id="rainy_walk",
        scene="after a rainy walk, when damp strands had curled every which way",
        opener="Once before",
        helper="Grandma",
        line="A gentle hand first, then the comb can come through; calm is the clever and kind thing to do.",
        tags={"flashback", "rain"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Rose", "Ava", "Ella", "Zoe", "Lucy"]
BOY_NAMES = ["Finn", "Theo", "Max", "Leo", "Eli", "Noah", "Sam", "Ben"]
TRAITS = ["curious", "bright", "eager", "gentle", "bouncy"]


@dataclass
class StoryParams:
    place: str
    hair: str
    comb: str
    snag: str
    memory: str
    child_name: str
    child_gender: str
    caregiver: str
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


KNOWLEDGE = {
    "comb": [
        (
            "What is a comb for?",
            "A comb helps separate hair into smaller parts so knots can come out. Used gently, it keeps hair tidy without pulling too hard.",
        )
    ],
    "wide_tooth": [
        (
            "Why can a wide-tooth comb help with curls?",
            "A wide-tooth comb has bigger spaces between its teeth, so it does not grab curls so tightly. That makes it gentler on curly or wavy hair.",
        )
    ],
    "pocket_comb": [
        (
            "What is a pocket comb?",
            "A pocket comb is a small comb you can carry easily. It works best for lighter tangles, not big tight knots.",
        )
    ],
    "fine_tooth": [
        (
            "Why should a fine-tooth comb be used carefully?",
            "Its teeth are close together, so it can catch on tangles fast. That is why it is better for smoother straight hair than for thick curls.",
        )
    ],
    "hair": [
        (
            "What is a tangle?",
            "A tangle is when strands of hair twist around one another and get caught. Pulling hard usually hurts more, but going slowly can help.",
        )
    ],
    "fundamental": [
        (
            "What does fundamental mean?",
            "Fundamental means very important and basic, like a first rule you should remember. In this story, the fundamental rule is to start at the ends and go slowly.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when the story pauses the present and remembers something from the past. It can explain why a character knows what to do now.",
        )
    ],
    "ribbon": [
        (
            "Why can a ribbon make a knot in hair?",
            "If a ribbon twists and tightens, hair can loop around it and get caught. That can turn a small bow into a stubborn knot.",
        )
    ],
    "leaf": [
        (
            "How can a leaf get stuck in hair?",
            "A leaf can blow in on the wind and catch between strands. If the hair is moving around, the leaf may twist into a little snag.",
        )
    ],
    "sleep": [
        (
            "Why does hair get messy after sleeping?",
            "When you roll on a pillow, strands can rub, twist, and bunch together. That can leave sleepy knots or bedhead in the morning.",
        )
    ],
    "wind": [
        (
            "Why does wind tangle hair?",
            "Wind blows different strands in different directions at once. When they cross over each other enough times, they can knot together.",
        )
    ],
    "soap": [
        (
            "Why can wet hair tangle after washing?",
            "Wet hair can cling together in little groups, especially if it is rubbed quickly. Gentle fingers and patient combing help it come apart.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "comb",
    "wide_tooth",
    "pocket_comb",
    "fine_tooth",
    "hair",
    "fundamental",
    "flashback",
    "ribbon",
    "leaf",
    "sleep",
    "wind",
    "soap",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    hair_cfg = f["hair_cfg"]
    comb_cfg = f["comb_cfg"]
    setting = f["setting"]
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old that includes the words '
            f'"fundamental" and "{comb_cfg.label.split()[0]}". Make it about curiosity, a special comb, and a gentle lesson.'
        ),
        (
            f"Tell a rhyming story where a {child.type} named {child.attrs['name']} grows curious about a treasured {comb_cfg.label} at {setting.place}, "
            f"gets it stuck in {hair_cfg.phrase}, and learns the careful way through a flashback."
        ),
        (
            "Write a simple child-facing story in rhyme where an old object holds a memory, a small mistake leads to a gentle correction, "
            "and the ending shows what changed."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    hair_cfg = f["hair_cfg"]
    comb_cfg = f["comb_cfg"]
    snag_cfg = f["snag_cfg"]
    memory_cfg = f["memory_cfg"]
    name = child.attrs["name"]
    pw = caregiver.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a curious child, and {name}'s {pw}. The special object in the story is {comb_cfg.phrase}.",
        ),
        (
            f"Why was {name} curious about the comb?",
            f"{name} saw that the comb was kept carefully and looked different from an ordinary comb. That made {child.pronoun('object')} wonder why it mattered so much.",
        ),
        (
            f"What went wrong when {name} used the comb too quickly?",
            f"The comb snagged in {hair_cfg.phrase} because {child.pronoun()} pulled too fast through {snag_cfg.cause}. The quick tug made {name} feel worried and uncomfortable.",
        ),
        (
            f"Why did {name}'s {pw} tell a flashback?",
            f"{pw.capitalize()} remembered learning the same lesson long ago, so the flashback showed where the gentle method came from. It helped explain why the comb was special and why slowness mattered.",
        ),
        (
            "What was the fundamental rule in the story?",
            "The fundamental rule was to start at the ends and go slowly. That worked because gentle little steps loosened the knot instead of yanking it tighter.",
        ),
        (
            f"How did the story end?",
            f"The knot came out, the hair turned smooth, and {name} put the comb back softly. The ending shows that {child.pronoun()} changed from rushing with curiosity to handling the comb with care.",
        ),
    ]
    if world.facts.get("smooth"):
        qa.append(
            (
                f"How did {name} solve the problem after the flashback?",
                f"{pw.capitalize()} helped with patience and a small bit of care where {snag_cfg.fix}, and then {name} tried again gently. Because the comb matched the hair and the strokes began at the ends, the snag came free.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"comb", "hair", "fundamental", "flashback"}
    comb_cfg = world.facts["comb_cfg"]
    snag_cfg = world.facts["snag_cfg"]
    tags |= set(comb_cfg.tags)
    tags |= set(snag_cfg.tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bedroom",
        hair="curls",
        comb="wide_tooth",
        snag="ribbon_knot",
        memory="first_school",
        child_name="Nora",
        child_gender="girl",
        caregiver="mother",
        trait="curious",
    ),
    StoryParams(
        place="garden",
        hair="waves",
        comb="pocket",
        snag="wind_tangle",
        memory="windy_fair",
        child_name="Finn",
        child_gender="boy",
        caregiver="father",
        trait="bright",
    ),
    StoryParams(
        place="bathroom",
        hair="straight",
        comb="fine_tooth",
        snag="sleep_tangle",
        memory="rainy_walk",
        child_name="Mia",
        child_gender="girl",
        caregiver="mother",
        trait="eager",
    ),
    StoryParams(
        place="garden",
        hair="straight",
        comb="pocket",
        snag="leaf_snag",
        memory="first_school",
        child_name="Theo",
        child_gender="boy",
        caregiver="father",
        trait="gentle",
    ),
    StoryParams(
        place="bedroom",
        hair="waves",
        comb="wide_tooth",
        snag="sleep_tangle",
        memory="windy_fair",
        child_name="Rose",
        child_gender="girl",
        caregiver="mother",
        trait="bouncy",
    ),
]


ASP_RULES = r"""
% comb fits hair when declared suitable
fits(C, H) :- suits(C, H).

% a snag belongs in a place when that place affords it
allowed(P, S) :- affords(P, S).

% a hair type can reasonably get a snag when declared compatible
reasonable_snag(H, S) :- hair_snag(H, S).

valid(P, H, C, S) :- place(P), hair(H), comb(C), snag(S),
                     allowed(P, S), reasonable_snag(H, S), fits(C, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for snag_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, snag_id))
    for hair_id, hair in HAIRS.items():
        lines.append(asp.fact("hair", hair_id))
        for snag_id in sorted(hair.suits):
            lines.append(asp.fact("hair_snag", hair_id, snag_id))
    for comb_id, comb in COMBS.items():
        lines.append(asp.fact("comb", comb_id))
        for hair_id in sorted(comb.suits):
            lines.append(asp.fact("suits", comb_id, hair_id))
    for snag_id in SNAGS:
        lines.append(asp.fact("snag", snag_id))
    for memory_id in MEMORIES:
        lines.append(asp.fact("memory", memory_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: smoke-test story came out empty.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(777)
        args = build_parser().parse_args([])
        params = resolve_params(args, rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Verify failed: default resolved story came out empty.)")
        print("OK: default resolve/generate succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a curious child, a treasured comb, a flashback, and a gentle lesson."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hair", choices=HAIRS)
    ap.add_argument("--comb", choices=COMBS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_obj = SETTINGS.get(args.place) if args.place else None
    hair_obj = HAIRS.get(args.hair) if args.hair else None
    comb_obj = COMBS.get(args.comb) if args.comb else None
    snag_obj = SNAGS.get(args.snag) if args.snag else None

    if hair_obj is not None and comb_obj is not None and not comb_fits(comb_obj, hair_obj):
        raise StoryError(explain_rejection(place_obj, hair_obj, comb_obj, snag_obj))
    if place_obj is not None and snag_obj is not None and snag_obj.id not in place_obj.affords:
        safe_hair = hair_obj if hair_obj is not None else next(iter(HAIRS.values()))
        safe_comb = comb_obj if comb_obj is not None else next(iter(COMBS.values()))
        raise StoryError(explain_rejection(place_obj, safe_hair, safe_comb, snag_obj))
    if hair_obj is not None and snag_obj is not None and snag_obj.id not in hair_obj.suits:
        safe_comb = comb_obj if comb_obj is not None else next(iter(COMBS.values()))
        raise StoryError(explain_rejection(place_obj, hair_obj, safe_comb, snag_obj))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hair is None or combo[1] == args.hair)
        and (args.comb is None or combo[2] == args.comb)
        and (args.snag is None or combo[3] == args.snag)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, hair, comb, snag = rng.choice(sorted(combos))
    memory = args.memory or rng.choice(sorted(MEMORIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        hair=hair,
        comb=comb,
        snag=snag,
        memory=memory,
        child_name=name,
        child_gender=gender,
        caregiver=caregiver,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.hair not in HAIRS:
        raise StoryError(f"(Invalid hair: {params.hair})")
    if params.comb not in COMBS:
        raise StoryError(f"(Invalid comb: {params.comb})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Invalid snag: {params.snag})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Invalid memory: {params.memory})")

    setting = SETTINGS[params.place]
    hair_cfg = HAIRS[params.hair]
    comb_cfg = COMBS[params.comb]
    snag_cfg = SNAGS[params.snag]

    if not comb_fits(comb_cfg, hair_cfg) or params.snag not in setting.affords or params.snag not in hair_cfg.suits:
        raise StoryError(explain_rejection(setting, hair_cfg, comb_cfg, snag_cfg))

    world = tell(
        setting=setting,
        hair_cfg=hair_cfg,
        comb_cfg=comb_cfg,
        snag_cfg=snag_cfg,
        memory_cfg=MEMORIES[params.memory],
        child_name=params.child_name,
        child_gender=params.child_gender,
        caregiver_type=params.caregiver,
        child_trait=params.trait,
    )

    story_text = world.render().replace("child", params.child_name)
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hair, comb, snag) combos:\n")
        for place, hair, comb, snag in combos:
            print(f"  {place:9} {hair:8} {comb:11} {snag}")
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
            header = f"### {p.child_name}: {p.place}, {p.hair}, {p.comb}, {p.snag}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
