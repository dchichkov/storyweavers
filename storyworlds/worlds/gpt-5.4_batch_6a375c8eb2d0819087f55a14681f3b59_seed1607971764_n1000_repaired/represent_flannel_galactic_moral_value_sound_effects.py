#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/represent_flannel_galactic_moral_value_sound_effects.py
===================================================================================

A standalone story world for a small folk-tale domain:

A child is chosen to represent a village in a night lantern walk under a
galactic sky. On the way to the hill, the ceremonial banner is torn. The child
must choose a sensible patch and a sturdy way to mend it before the wind at the
hilltop can snatch it again. The world models cloth, damage, wind, courage, and
honesty; the prose follows the simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/represent_flannel_galactic_moral_value_sound_effects.py
    python storyworlds/worlds/gpt-5.4/represent_flannel_galactic_moral_value_sound_effects.py --hill moonhill --tear split
    python storyworlds/worlds/gpt-5.4/represent_flannel_galactic_moral_value_sound_effects.py --patch paper
    python storyworlds/worlds/gpt-5.4/represent_flannel_galactic_moral_value_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/represent_flannel_galactic_moral_value_sound_effects.py --qa --json
    python storyworlds/worlds/gpt-5.4/represent_flannel_galactic_moral_value_sound_effects.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    cloth: bool = False
    carried: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)
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
class Hill:
    id: str
    place: str
    path: str
    sky: str
    wind: int
    emblem: str
    closing: str
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
class Tear:
    id: str
    label: str
    size: int
    sound: str
    place: str
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
class Patch:
    id: str
    label: str
    phrase: str
    toughness: int
    warmth: int
    cloth: bool = True
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
class Method:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )
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


def _r_worry(world: World) -> list[str]:
    banner = world.get("banner")
    child = world.get("child")
    if banner.meters["torn"] >= THRESHOLD and ("worry", banner.id) not in world.fired:
        world.fired.add(("worry", banner.id))
        child.memes["worry"] += 1
        return ["__worry__"]
    return []


def _r_wind_tug(world: World) -> list[str]:
    banner = world.get("banner")
    hill = world.get("hill")
    child = world.get("child")
    if banner.meters["mended"] < THRESHOLD:
        return []
    if ("wind_tug", banner.id) in world.fired:
        return []
    if hill.meters["wind"] < THRESHOLD:
        return []
    world.fired.add(("wind_tug", banner.id))
    strain = max(0.0, hill.meters["wind"] - banner.meters["secure"])
    banner.meters["strain"] += strain
    if strain >= THRESHOLD:
        child.memes["fear"] += 1
        return ["__strain__"]
    child.memes["relief"] += 1
    return []


def _r_fail(world: World) -> list[str]:
    banner = world.get("banner")
    child = world.get("child")
    if banner.meters["strain"] < THRESHOLD:
        return []
    if ("fail", banner.id) in world.fired:
        return []
    world.fired.add(("fail", banner.id))
    banner.meters["ripped_again"] += 1
    banner.meters["whole"] = 0.0
    child.memes["shame"] += 1
    return ["__ripped_again__"]


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="wind_tug", tag="physical", apply=_r_wind_tug),
    Rule(name="fail", tag="physical", apply=_r_fail),
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


def patch_fits(tear: Tear, patch: Patch) -> bool:
    return patch.cloth and patch.toughness >= tear.size


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def wind_need(hill: Hill, tear: Tear) -> int:
    return hill.wind + max(0, tear.size - 1)


def holds(method: Method, hill: Hill, tear: Tear, patch: Patch) -> bool:
    secure = method.power + patch.toughness
    return secure >= wind_need(hill, tear)


def explain_rejection(tear: Tear, patch: Patch) -> str:
    if not patch.cloth:
        return (
            f"(No story: {patch.label} is not proper cloth, so it will not mend "
            f"{tear.label}. A ceremonial banner needs a real fabric patch.)"
        )
    if patch.toughness < tear.size:
        return (
            f"(No story: {patch.label} is too slight for {tear.label}. "
            f"Pick a stronger cloth, such as flannel or felt.)"
        )
    return "(No story: this patch does not suit the tear.)"


def explain_method(mid: str) -> str:
    m = METHODS[mid]
    better = ", ".join(sorted(x.id for x in sensible_methods()))
    return (
        f"(Refusing method '{mid}': it scores too low on common sense "
        f"(sense={m.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hill_id in HILLS:
        for tear_id, tear in TEARS.items():
            for patch_id, patch in PATCHES.items():
                if patch_fits(tear, patch):
                    combos.append((hill_id, tear_id, patch_id))
    return combos


def predict_walk(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "strain": sim.get("banner").meters["strain"],
        "fails": sim.get("banner").meters["ripped_again"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, elder: Entity, hill: Hill) -> None:
    world.say(
        f"In a valley village where lamps were lit one by one at dusk, "
        f"{child.id} lived with {elder.label_word}. Every year the people climbed "
        f"{hill.place} to hang a banner that would represent them beneath {hill.sky}."
    )
    world.say(
        f"That year the elders chose {child.id} to carry the village banner, for "
        f"{child.pronoun()} walked carefully and listened well."
    )


def banner_setup(world: World, child: Entity, hill: Hill) -> None:
    banner = world.get("banner")
    child.memes["pride"] += 1
    world.say(
        f"The banner was stitched with a {hill.emblem}, and when evening wind "
        f"brushed it, it whispered, 'swish, swish.' {child.id} held the pole with "
        f"both hands and smiled at the honor."
    )
    banner.meters["whole"] = 1.0


def accident(world: World, child: Entity, tear: Tear) -> None:
    banner = world.get("banner")
    banner.meters["whole"] = 0.0
    banner.meters["torn"] += 1
    banner.meters["tear_size"] = float(tear.size)
    child.memes["shock"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But along {world.facts['hill'].path}, a thorn caught the cloth. "
        f'"{tear.sound}!" cried the banner, and a {tear.label} opened {tear.place}.'
    )
    world.say(
        f"{child.id}'s heart knocked like a small drum. If the banner failed, "
        f"{child.pronoun()} could not represent the village as promised."
    )


def confess(world: World, child: Entity, elder: Entity) -> None:
    child.memes["honesty"] += 1
    world.say(
        f'{child.id} did not hide the trouble. "{elder.label_word.capitalize()}, '
        f'the banner is torn," {child.pronoun()} said. "Please help me mend it '
        f'the right way."'
    )


def choose_patch(world: World, elder: Entity, patch: Patch) -> None:
    banner = world.get("banner")
    banner.attrs["patch"] = patch.id
    world.say(
        f"{elder.label_word.capitalize()} opened a work pouch and brought out "
        f"{patch.phrase}. The old hands touched the cloth and nodded."
    )
    if patch.id == "flannel":
        world.say(
            "It was soft flannel, thick and warm, the sort of cloth that keeps "
            "its promise when cold wind begins to sing."
        )
    elif patch.id == "felt":
        world.say(
            "It was humble felt, plain to the eye but steady under a needle."
        )
    else:
        world.say(
            f"It looked bright, and for a breath it seemed enough."
        )


def mend(world: World, child: Entity, elder: Entity, method: Method, patch: Patch, tear: Tear) -> None:
    banner = world.get("banner")
    hill = world.get("hill")
    banner.meters["mended"] = 1.0
    banner.meters["secure"] = float(method.power + patch.toughness)
    world.say(
        f"{elder.label_word.capitalize()} showed {child.id} how to hold the cloth "
        f"still while {elder.pronoun()} {method.text.format(patch=patch.label, tear=tear.label)}."
    )
    pred = predict_walk(world)
    world.facts["predicted_fail"] = pred["fails"]
    if pred["fails"]:
        world.say(
            f"The night wind already hissed over {hill.place}, and both of them "
            f"could hear that the mend might not hold."
        )
    else:
        world.say(
            f"When the last stitch was tucked in, the banner gave only a small "
            f'"swish" instead of a frightened flap.'
        )


def hilltop_success(world: World, child: Entity, elder: Entity, hill: Hill, patch: Patch, method: Method) -> None:
    banner = world.get("banner")
    banner.meters["whole"] = 1.0
    child.memes["relief"] += 1
    child.memes["wisdom"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Up on {hill.place}, the wind came running -- whooosh, whooosh -- but the "
        f"{patch.label} patch and the careful {method.label} held fast."
    )
    world.say(
        f"{child.id} lifted the banner high. The {hill.emblem} shone by lantern "
        f"light, and all the village could see who they were."
    )
    world.say(
        f"From that night on, people said that {child.id} had learned a deep old "
        f"truth: honest hands and patient work are stronger than hurry. {hill.closing}"
    )


def hilltop_failure(world: World, child: Entity, elder: Entity, hill: Hill, method: Method) -> None:
    banner = world.get("banner")
    propagate(world, narrate=False)
    child.memes["honesty"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f"Up on {hill.place}, the wind came running -- whooosh, whooosh -- and "
        f"{method.fail}."
    )
    world.say(
        f'"Rrrrip!" went the cloth. {child.id} caught the pole before it fell, '
        f"and tears sprang to {child.pronoun('possessive')} eyes."
    )
    world.say(
        f"But {child.pronoun()} told the truth at once, and the villagers gathered "
        f"close. They tied their own lantern ribbons along the bare pole until it "
        f"gleamed like a little river of light."
    )
    world.say(
        f"So {child.id} still walked at the front, not because the banner was whole, "
        f"but because a truthful heart could still represent the village. {hill.closing}"
    )


def tell(
    hill: Hill,
    tear: Tear,
    patch: Patch,
    method: Method,
    *,
    child_name: str = "Toma",
    child_gender: str = "boy",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder"))
    world.add(Entity(id="banner", type="banner", label="the village banner", cloth=True, carried=True))
    hill_ent = world.add(Entity(id="hill", type="hill", label=hill.place))
    hill_ent.meters["wind"] = float(hill.wind)

    world.facts["hill"] = hill
    world.facts["tear_cfg"] = tear
    world.facts["patch_cfg"] = patch
    world.facts["method_cfg"] = method

    introduce(world, child, elder, hill)
    banner_setup(world, child, hill)

    world.para()
    accident(world, child, tear)
    confess(world, child, elder)
    choose_patch(world, elder, patch)
    mend(world, child, elder, method, patch, tear)

    world.para()
    success = holds(method, hill, tear, patch)
    if success:
        hilltop_success(world, child, elder, hill, patch, method)
        outcome = "held"
    else:
        hilltop_failure(world, child, elder, hill, method)
        outcome = "ripped"

    world.facts.update(
        child=child,
        elder=elder,
        banner=world.get("banner"),
        hill=hill,
        tear=tear,
        patch=patch,
        method=method,
        outcome=outcome,
        truth_told=child.memes["honesty"] >= THRESHOLD,
        secure=world.get("banner").meters["secure"],
        wind_need=wind_need(hill, tear),
    )
    return world


HILLS = {
    "moonhill": Hill(
        id="moonhill",
        place="Moon Hill",
        path="the nettle path",
        sky="the galactic dark, bright with many stars",
        wind=2,
        emblem="silver owl",
        closing="The lamps bobbed home like fireflies, and the tale was told beside every hearth.",
        tags={"sky", "wind"},
    ),
    "riverbank": Hill(
        id="riverbank",
        place="the Riverbank Rise",
        path="the willow path",
        sky="the galactic night reflected in black water",
        wind=1,
        emblem="gold fish",
        closing="The river kept the lanterns in its mirror, and the children remembered the lesson.",
        tags={"river", "wind"},
    ),
    "stonegate": Hill(
        id="stonegate",
        place="Stone Gate Hill",
        path="the steep sheep track",
        sky="the galactic blue between the first evening stars",
        wind=3,
        emblem="red fox",
        closing="The gate stones glowed until dawn, and even the oldest shepherd smiled.",
        tags={"hill", "wind"},
    ),
}

TEARS = {
    "nick": Tear(
        id="nick",
        label="small nick",
        size=1,
        sound="snick",
        place="near the lower edge",
        tags={"tear"},
    ),
    "split": Tear(
        id="split",
        label="long split",
        size=2,
        sound="rrrip",
        place="through the middle seam",
        tags={"tear"},
    ),
    "gash": Tear(
        id="gash",
        label="wide gash",
        size=3,
        sound="ra-a-ip",
        place="beside the painted emblem",
        tags={"tear"},
    ),
}

PATCHES = {
    "flannel": Patch(
        id="flannel",
        label="flannel",
        phrase="a square of red flannel",
        toughness=2,
        warmth=2,
        cloth=True,
        tags={"flannel", "cloth"},
    ),
    "felt": Patch(
        id="felt",
        label="felt",
        phrase="a round of gray felt",
        toughness=3,
        warmth=1,
        cloth=True,
        tags={"felt", "cloth"},
    ),
    "silk": Patch(
        id="silk",
        label="silk",
        phrase="a shining piece of silk",
        toughness=1,
        warmth=0,
        cloth=True,
        tags={"silk", "cloth"},
    ),
    "paper": Patch(
        id="paper",
        label="paper",
        phrase="a pretty scrap of star paper",
        toughness=0,
        warmth=0,
        cloth=False,
        tags={"paper"},
    ),
}

METHODS = {
    "backstitch": Method(
        id="backstitch",
        label="backstitch",
        sense=3,
        power=3,
        text="sewed the {patch} over the {tear} with neat backstitches, tugging each one snug",
        fail="the stitches pulled and the patch began to flap",
        qa_text="sewed the patch on with neat backstitches",
        tags={"sew"},
    ),
    "blanket_stitch": Method(
        id="blanket_stitch",
        label="blanket stitch",
        sense=3,
        power=2,
        text="worked a blanket stitch all around the {patch}, making a strong little fence of thread",
        fail="the edge held for a breath, then the wind worried it loose",
        qa_text="worked a blanket stitch all around the patch",
        tags={"sew"},
    ),
    "knot_tie": Method(
        id="knot_tie",
        label="knot tie",
        sense=2,
        power=1,
        text="tied the {patch} across the {tear} with crossed threads and quick knots",
        fail="the knots skipped and jumped under the hard wind",
        qa_text="tied the patch on with quick knots",
        tags={"tie"},
    ),
    "paste": Method(
        id="paste",
        label="paste",
        sense=1,
        power=0,
        text="spread berry paste under the {patch} and pressed it flat",
        fail="the paste turned slick in the night air at once",
        qa_text="pressed the patch on with paste",
        tags={"glue"},
    ),
}

CHILD_NAMES = ["Toma", "Mira", "Oren", "Lina", "Bram", "Sela", "Neri", "Pia"]
TRAITS = ["careful", "steady", "bright-eyed", "gentle"]


@dataclass
class StoryParams:
    hill: str
    tear: str
    patch: str
    method: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str = "careful"
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
    "flannel": [
        (
            "What is flannel?",
            "Flannel is a soft cloth, often a little fuzzy and warm. Because it is real fabric, it can be useful for mending other cloth things.",
        )
    ],
    "felt": [
        (
            "What is felt?",
            "Felt is cloth made of pressed fibers. It is thick and can be sturdy even when it looks plain.",
        )
    ],
    "silk": [
        (
            "What is silk like?",
            "Silk is smooth and shiny cloth. It is beautiful, but some silk is too delicate for rough jobs in strong wind.",
        )
    ],
    "paper": [
        (
            "Why is paper a poor patch for cloth outdoors?",
            "Paper tears easily and can grow soft in damp night air. A banner in the wind needs real cloth instead.",
        )
    ],
    "sew": [
        (
            "Why can sewing be stronger than pasting for a cloth patch?",
            "Sewing uses thread to hold cloth to cloth all around the tear. That makes the mend much less likely to peel away when the wind pulls on it.",
        )
    ],
    "tie": [
        (
            "Why can a quick knot be weaker than careful stitching?",
            "A few quick knots hold only in small spots. Careful stitching spreads the pull across the cloth and keeps it from opening again.",
        )
    ],
    "wind": [
        (
            "Why is wind hard on a banner?",
            "A banner catches air like a sail. If it is torn or weakly mended, the wind keeps tugging at the same place until the cloth pulls apart.",
        )
    ],
    "truth": [
        (
            "Why is telling the truth important when something goes wrong?",
            "Telling the truth helps people fix the real problem sooner. It also shows courage, because honesty matters more than pretending everything is fine.",
        )
    ],
    "represent": [
        (
            "What does it mean to represent a village?",
            "To represent a village means to stand for the people and show others who they are. In a story, carrying the village banner can be a way to do that.",
        )
    ],
    "galactic": [
        (
            "What does galactic mean?",
            "Galactic means having to do with the stars and the great spread of space. In a story, a galactic sky sounds very wide and full of wonder.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "represent",
    "flannel",
    "felt",
    "silk",
    "paper",
    "sew",
    "tie",
    "wind",
    "truth",
    "galactic",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    hill = f["hill"]
    tear = f["tear"]
    patch = f["patch"]
    method = f["method"]
    outcome = f["outcome"]
    prompts = [
        (
            f'Write a folk tale for a 3-to-5-year-old about a child chosen to represent '
            f'a village during a lantern walk under a galactic sky.'
        ),
        (
            f'Include a torn banner, the word "{patch.label}", gentle sound effects like '
            f'"swish" or "whooosh," and a moral about honesty and patience.'
        ),
    ]
    if outcome == "held":
        prompts.append(
            f"Tell how {child.id} used a {patch.label} patch and {method.label} to save a banner with a {tear.label} on the way to {hill.place}."
        )
    else:
        prompts.append(
            f"Tell how {child.id} tried to mend a banner with {patch.label} and {method.label}, but still learned that truth can represent a village better than pride."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    hill = f["hill"]
    tear = f["tear"]
    patch = f["patch"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was chosen to represent the village, and {elder.label_word}, who helped with the torn banner.",
        ),
        (
            f"Why was carrying the banner important?",
            f"The banner showed the village emblem during the lantern walk. Carrying it meant {child.id} was standing for the whole village under the night sky.",
        ),
        (
            f"What happened to the banner on the way to {hill.place}?",
            f"A thorn caught it and made a {tear.label}. The tearing sound warned {child.id} that the village banner might not survive the climb.",
        ),
        (
            f"Why did {child.id} ask for help instead of hiding the tear?",
            f"{child.pronoun('subject').capitalize()} knew the banner had to be mended properly if it was going to represent the village. Asking for help showed honesty before the hard wind could make the damage worse.",
        ),
    ]
    if outcome == "held":
        qa.extend(
            [
                (
                    f"How did they mend the banner?",
                    f"They used {patch.phrase} and {method.qa_text}. That made the banner strong enough for the wind on {hill.place}.",
                ),
                (
                    f"How did the repair change what happened at the hilltop?",
                    f"The mend held when the wind rushed over the hill, so the banner could still fly. Because the patch was sturdy enough and the stitches were careful, {child.id} finished the walk proudly.",
                ),
                (
                    "What is the moral of the story?",
                    "The story teaches that honest hands and patient work are stronger than hurry. The happy ending came because the child told the truth and took time to mend the banner well.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Did the first repair hold at the hilltop?",
                    f"No. The wind pulled at the weak mend until the cloth ripped again. The repair failed because the night gusts were stronger than that patch-and-method pair could bear.",
                ),
                (
                    "How did the villagers solve the problem after the banner ripped again?",
                    f"They tied their lantern ribbons along the bare pole and walked together anyway. That let {child.id} still lead honestly, even without a whole banner.",
                ),
                (
                    "What is the moral of the story?",
                    "The story teaches that truth matters more than looking perfect. Even after the cloth failed, the child could still do right by speaking plainly and accepting help.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"represent", "truth", "wind", "galactic"}
    tags |= set(f["patch"].tags)
    tags |= set(f["method"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hill="moonhill",
        tear="split",
        patch="flannel",
        method="backstitch",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        trait="steady",
    ),
    StoryParams(
        hill="riverbank",
        tear="nick",
        patch="silk",
        method="blanket_stitch",
        child_name="Oren",
        child_gender="boy",
        elder_type="grandfather",
        trait="careful",
    ),
    StoryParams(
        hill="stonegate",
        tear="split",
        patch="felt",
        method="knot_tie",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
        trait="gentle",
    ),
    StoryParams(
        hill="stonegate",
        tear="gash",
        patch="felt",
        method="backstitch",
        child_name="Bram",
        child_gender="boy",
        elder_type="grandfather",
        trait="steady",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "held" if holds(METHODS[params.method], HILLS[params.hill], TEARS[params.tear], PATCHES[params.patch]) else "ripped"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(H, T, P) :- hill(H), tear(T), patch(P), cloth(P), toughness(P, PT), size(T, TS), PT >= TS.
sensible(M)    :- method(M), sense(M, S), sense_min(Min), S >= Min.

% --- outcome model ---------------------------------------------------------
need(H, T, W + TS - 1) :- chosen_hill(H), chosen_tear(T), wind(H, W), size(T, TS).
secure(M, P, MP + PT)  :- chosen_method(M), chosen_patch(P), power(M, MP), toughness(P, PT).
outcome(held)          :- secure(M, P, S), need(H, T, N), S >= N.
outcome(ripped)        :- secure(M, P, S), need(H, T, N), S < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, hill in HILLS.items():
        lines.append(asp.fact("hill", hid))
        lines.append(asp.fact("wind", hid, hill.wind))
    for tid, tear in TEARS.items():
        lines.append(asp.fact("tear", tid))
        lines.append(asp.fact("size", tid, tear.size))
    for pid, patch in PATCHES.items():
        lines.append(asp.fact("patch", pid))
        lines.append(asp.fact("toughness", pid, patch.toughness))
        if patch.cloth:
            lines.append(asp.fact("cloth", pid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hill", params.hill),
            asp.fact("chosen_tear", params.tear),
            asp.fact("chosen_patch", params.patch),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sense = set(asp_sensible())
    p_sense = {m.id for m in sensible_methods()}
    if c_sense == p_sense:
        print(f"OK: sensible methods match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for seed in range(100):
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
        print(f"MISMATCH: {bad}/{len(cases)} outcome cases differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: a child mends a torn banner before a windy lantern walk."
    )
    ap.add_argument("--hill", choices=HILLS)
    ap.add_argument("--tear", choices=TEARS)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.patch and args.tear:
        tear = TEARS[args.tear]
        patch = PATCHES[args.patch]
        if not patch_fits(tear, patch):
            raise StoryError(explain_rejection(tear, patch))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hill is None or combo[0] == args.hill)
        and (args.tear is None or combo[1] == args.tear)
        and (args.patch is None or combo[2] == args.patch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hill, tear, patch = rng.choice(sorted(combos))
    method = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        hill=hill,
        tear=tear,
        patch=patch,
        method=method,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hill not in HILLS:
        raise StoryError(f"(Unknown hill: {params.hill})")
    if params.tear not in TEARS:
        raise StoryError(f"(Unknown tear: {params.tear})")
    if params.patch not in PATCHES:
        raise StoryError(f"(Unknown patch: {params.patch})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    hill = HILLS[params.hill]
    tear = TEARS[params.tear]
    patch = PATCHES[params.patch]
    method = METHODS[params.method]

    if not patch_fits(tear, patch):
        raise StoryError(explain_rejection(tear, patch))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        hill=hill,
        tear=tear,
        patch=patch,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hill, tear, patch) combos:\n")
        for hill, tear, patch in combos:
            print(f"  {hill:10} {tear:6} {patch}")
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
            header = f"### {p.child_name}: {p.patch} + {p.method} on {p.tear} at {p.hill} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
