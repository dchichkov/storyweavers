#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/papaya_mole_surprise_magic_suspense_comedy.py
========================================================================

A tiny story world about a child planning a papaya surprise, a sneaky mole under
the ground, and a burst of silly magic. The stories are child-facing, suspenseful
without being harsh, and end in comedy.

Run it
------
    python storyworlds/worlds/gpt-5.4/papaya_mole_surprise_magic_suspense_comedy.py
    python storyworlds/worlds/gpt-5.4/papaya_mole_surprise_magic_suspense_comedy.py --place garden --spot basket --catalyst wishing_pebble
    python storyworlds/worlds/gpt-5.4/papaya_mole_surprise_magic_suspense_comedy.py --spot shelf
    python storyworlds/worlds/gpt-5.4/papaya_mole_surprise_magic_suspense_comedy.py --response stomp
    python storyworlds/worlds/gpt-5.4/papaya_mole_surprise_magic_suspense_comedy.py --all --qa
    python storyworlds/worlds/gpt-5.4/papaya_mole_surprise_magic_suspense_comedy.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    afford_spots: set[str] = field(default_factory=set)
    afford_catalysts: set[str] = field(default_factory=set)
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
class Spot:
    id: str
    label: str
    phrase: str
    accessible: bool = True
    wobble_text: str = ""
    reveal_text: str = ""
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
class Catalyst:
    id: str
    label: str
    accidental_text: str
    glow_text: str
    surge: int
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
class Response:
    id: str
    sense: int
    power: int
    offer_text: str
    calm_text: str
    fail_text: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_tunnel(world: World) -> list[str]:
    papaya = world.get("papaya")
    spot = world.get("spot")
    mole = world.get("mole")
    child = world.get("child")
    helper = world.get("helper")
    if papaya.meters["hidden"] < THRESHOLD or not spot.attrs.get("accessible", False):
        return []
    sig = ("tunnel", spot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mole.meters["near"] += 1
    mole.meters["sniffing"] += 1
    spot.meters["wobbling"] += 1
    child.memes["worry"] += 1
    helper.memes["curiosity"] += 1
    return ["__tunnel__"]


def _r_magic(world: World) -> list[str]:
    papaya = world.get("papaya")
    if papaya.meters["enchanted"] < THRESHOLD or papaya.meters["hidden"] < THRESHOLD:
        return []
    sig = ("magic", "papaya")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    papaya.meters["glowing"] += 1
    return ["__magic__"]


def _r_bump(world: World) -> list[str]:
    papaya = world.get("papaya")
    spot = world.get("spot")
    child = world.get("child")
    mole = world.get("mole")
    if papaya.meters["glowing"] < THRESHOLD or spot.meters["wobbling"] < THRESHOLD:
        return []
    sig = ("bump", spot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    papaya.meters["rolling"] += 1
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    mole.memes["pride"] += 1
    return ["__bump__"]


CAUSAL_RULES = [
    Rule(name="tunnel", tag="physical", apply=_r_tunnel),
    Rule(name="magic", tag="magic", apply=_r_magic),
    Rule(name="bump", tag="physical", apply=_r_bump),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        opening="The garden smelled like warm dirt and mint, and the stepping stones made a neat little path.",
        afford_spots={"basket", "wheelbarrow", "stump"},
        afford_catalysts={"wishing_pebble", "moonbeam", "sneeze_spell"},
        tags={"garden"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the greenhouse",
        opening="The greenhouse was bright and foggy, with little drops sliding down the glass.",
        afford_spots={"basket", "wheelbarrow"},
        afford_catalysts={"wishing_pebble", "sneeze_spell"},
        tags={"greenhouse"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard",
        opening="The orchard was full of crooked shadows, soft grass, and trees that looked like they were whispering.",
        afford_spots={"basket", "stump"},
        afford_catalysts={"wishing_pebble", "moonbeam", "sneeze_spell"},
        tags={"orchard"},
    ),
}

SPOTS = {
    "basket": Spot(
        id="basket",
        label="basket",
        phrase="a picnic basket with a cloth lid",
        accessible=True,
        wobble_text="The basket gave one tiny hop, then another, as if it had remembered feet.",
        reveal_text="the cloth lid popped up like a yawn",
        tags={"basket"},
    ),
    "wheelbarrow": Spot(
        id="wheelbarrow",
        label="wheelbarrow",
        phrase="a red wheelbarrow tipped against a post",
        accessible=True,
        wobble_text="The wheelbarrow rocked on one wheel and squeaked like a surprised duck.",
        reveal_text="the tray tipped forward with a rusty squeak",
        tags={"wheelbarrow"},
    ),
    "stump": Spot(
        id="stump",
        label="stump",
        phrase="a hollow old stump beside the path",
        accessible=True,
        wobble_text="The stump shivered, and a ring of loose dirt trembled around it.",
        reveal_text="a shower of crumbs of bark flew out of the hollow",
        tags={"stump"},
    ),
    "shelf": Spot(
        id="shelf",
        label="shelf",
        phrase="a high wooden shelf",
        accessible=False,
        wobble_text="",
        reveal_text="",
        tags={"shelf"},
    ),
}

CATALYSTS = {
    "wishing_pebble": Catalyst(
        id="wishing_pebble",
        label="wishing pebble",
        accidental_text="A smooth wishing pebble slipped from a pocket and knocked softly against the papaya.",
        glow_text="gold freckles of light ran over the papaya skin",
        surge=1,
        tags={"magic", "wish"},
    ),
    "moonbeam": Catalyst(
        id="moonbeam",
        label="moonbeam",
        accidental_text="A skinny moonbeam slid through the leaves and landed right on the hidden papaya.",
        glow_text="the papaya shone as if a tiny lamp had been tucked inside it",
        surge=2,
        tags={"magic", "moon"},
    ),
    "sneeze_spell": Catalyst(
        id="sneeze_spell",
        label="sneeze spell",
        accidental_text="A leftover sneeze spell from a joke magic set escaped with a silly 'piff!' and dusted the papaya.",
        glow_text="sparkly hiccup-light blinked over the papaya in little bursts",
        surge=2,
        tags={"magic", "spell"},
    ),
}

RESPONSES = {
    "share_slice": Response(
        id="share_slice",
        sense=3,
        power=3,
        offer_text="cut a sweet slice of papaya and held it low to the ground",
        calm_text="The smell made the mystery stop at once. The mole poked out, sniffed hard, and forgot to look mysterious anymore.",
        fail_text="held out a slice, but the magic papaya had already bounced away too fast to bribe",
        qa_text="offered the mole a slice of papaya",
        tags={"sharing", "papaya"},
    ),
    "sing_jingle": Response(
        id="sing_jingle",
        sense=2,
        power=2,
        offer_text="sang a tiny jingle about snacks, soft paws, and no more surprises",
        calm_text="The tune wobbled through the dirt. The mole popped up with its nose twitching and listened so hard that the magic settled down.",
        fail_text="sang a calming jingle, but the glowing papaya kept wobbling louder than the song",
        qa_text="sang a calming jingle to the mole",
        tags={"music"},
    ),
    "napkin_trail": Response(
        id="napkin_trail",
        sense=2,
        power=2,
        offer_text="laid a neat trail of papaya cubes on a napkin from the hiding spot to the grass",
        calm_text="That was too tempting to resist. The mole followed the little trail one cube at a time until the trouble rolled out into the open.",
        fail_text="laid a trail of papaya cubes, but the enchanted fruit lurched first and burst before the mole could follow",
        qa_text="laid a trail of papaya cubes for the mole",
        tags={"sharing", "trail"},
    ),
    "stomp": Response(
        id="stomp",
        sense=1,
        power=1,
        offer_text="stomped at the ground and barked, 'Stop being mysterious!'",
        calm_text="The ground happened to stop wobbling, but it was not a kind idea.",
        fail_text="stomped at the ground, which only made the magic papaya jiggle harder",
        qa_text="stomped at the ground",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Tessa", "Mila", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Eli", "Theo", "Finn", "Sam"]
HELPER_NAMES = ["Pip", "June", "Milo", "Ivy", "Toby", "Wren"]
TRAITS = ["giggly", "curious", "dramatic", "careful", "bouncy", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for spot_id in setting.afford_spots:
            spot = SPOTS[spot_id]
            if not spot.accessible:
                continue
            for catalyst_id in setting.afford_catalysts:
                combos.append((place, spot_id, catalyst_id))
    return sorted(combos)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def suspense_level(catalyst: Catalyst, delay: int) -> int:
    return catalyst.surge + delay


def outcome_of(params: "StoryParams") -> str:
    response = RESPONSES[params.response]
    catalyst = CATALYSTS[params.catalyst]
    return "shared" if response.power >= suspense_level(catalyst, params.delay) else "splat"


def explain_spot(spot: Spot) -> str:
    if not spot.accessible:
        return (
            f"(No story: a mole cannot reasonably reach {spot.phrase}. "
            f"The hidden papaya needs a ground-level spot the mole could tunnel to.)"
        )
    return "(No story: this hiding spot does not fit the chosen setting.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a gentler fix like {better}.)"
    )


@dataclass
class StoryParams:
    place: str
    spot: str
    catalyst: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    delay: int = 0
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


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "wobbling": sim.get("spot").meters["wobbling"] >= THRESHOLD,
        "glowing": sim.get("papaya").meters["glowing"] >= THRESHOLD,
        "rolling": sim.get("papaya").meters["rolling"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type} who loved making cheerful secrets."
    )
    world.say(
        f"That afternoon, {child.id} wanted to surprise {helper.id} and {child.pronoun('possessive')} {parent.label_word} with a special snack: a ripe papaya with orange slices tucked inside like sunshine."
    )
    world.say(world.setting.opening)


def hide_papaya(world: World, child: Entity, spot: Spot) -> None:
    papaya = world.get("papaya")
    papaya.meters["hidden"] = 1.0
    world.say(
        f"To keep the surprise safe, {child.id} hid the papaya in {spot.phrase} and whispered, \"Stay there until the big ta-da.\""
    )


def accident(world: World, child: Entity, helper: Entity, catalyst: Catalyst) -> None:
    papaya = world.get("papaya")
    papaya.meters["enchanted"] = 1.0
    child.memes["surprise"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"But then {catalyst.accidental_text} At once, {catalyst.glow_text}."
    )


def rising_suspense(world: World, child: Entity, helper: Entity, spot: Spot) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_wobble"] = pred["wobbling"]
    world.facts["predicted_glow"] = pred["glowing"]
    world.facts["predicted_roll"] = pred["rolling"]
    world.say(
        f"{child.id} froze. From {spot.phrase} came a muffled rustle."
    )
    world.say(spot.wobble_text)
    world.say(
        f"\"Did your surprise just gulp?\" {helper.id} whispered. {child.id} was not sure whether to laugh or hide behind {child.pronoun('possessive')} own elbows."
    )


def inspect(world: World, child: Entity, helper: Entity, response: Response) -> None:
    child.memes["bravery"] += 1
    helper.memes["bravery"] += 1
    world.say(
        f"Instead of running, the two children crept closer. {helper.id} squeezed {child.id}'s hand, and {child.id} {response.offer_text}."
    )


def calm_and_reveal(
    world: World,
    child: Entity,
    helper: Entity,
    parent: Entity,
    spot: Spot,
    response: Response,
) -> None:
    mole = world.get("mole")
    papaya = world.get("papaya")
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    mole.memes["trust"] += 1
    papaya.meters["safe"] += 1
    world.say(response.calm_text)
    world.say(
        f"Then {spot.reveal_text}, and out popped a mole with glowing whiskers, a papaya seed on its nose, and the roundest surprised eyes in {world.setting.place}."
    )
    world.say(
        f"{child.id}'s {parent.label_word} came over just in time to see the mole bow by accident. \"Well,\" {parent.pronoun()} said, trying not to laugh, \"that is the fanciest snack thief I have ever met.\""
    )
    world.say(
        f"They all shared the papaya after that, even the mole, who sat up on the grass and chewed so neatly that everyone laughed instead of gasped."
    )
    world.say(
        f"In the end, the surprise was not only the papaya. It was that a mysterious wobble turned into the silliest picnic guest of all."
    )


def comic_splat(
    world: World,
    child: Entity,
    helper: Entity,
    parent: Entity,
    spot: Spot,
    response: Response,
) -> None:
    mole = world.get("mole")
    papaya = world.get("papaya")
    papaya.meters["splat"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(response.fail_text + ".")
    world.say(
        f"With one last magical wobble, {spot.reveal_text}, the papaya burst open in a bright orange plop, and a mole shot out wearing half the peel like a shiny helmet."
    )
    world.say(
        f"For one tiny second nobody spoke. Then {helper.id} snorted, {child.id} giggled, and even {child.id}'s {parent.label_word} had to sit down on the grass to laugh."
    )
    world.say(
        f"The mole blinked, licked a bit of papaya from its whiskers, and took a proud little march through the mush as if this had been the plan all along."
    )
    world.say(
        f"So the surprise picnic became a surprise cleanup instead, with sticky hands, loud laughter, and the funniest mole anyone had ever seen."
    )


def tell(
    setting: Setting,
    spot_cfg: Spot,
    catalyst: Catalyst,
    response: Response,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=["helpful"],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
        )
    )
    papaya = world.add(
        Entity(
            id="papaya",
            kind="thing",
            type="fruit",
            label="papaya",
            role="snack",
            attrs={},
        )
    )
    spot = world.add(
        Entity(
            id="spot",
            kind="thing",
            type="spot",
            label=spot_cfg.label,
            role="spot",
            attrs={"accessible": spot_cfg.accessible},
        )
    )
    world.add(
        Entity(
            id="mole",
            kind="character",
            type="animal",
            label="mole",
            role="mole",
            attrs={},
        )
    )

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        papaya=papaya,
        spot_cfg=spot_cfg,
        catalyst=catalyst,
        response=response,
        delay=delay,
        place=setting,
    )

    introduce(world, child, helper, parent)
    hide_papaya(world, child, spot_cfg)

    world.para()
    accident(world, child, helper, catalyst)
    for _ in range(delay + 1):
        propagate(world, narrate=False)
    rising_suspense(world, child, helper, spot_cfg)

    world.para()
    inspect(world, child, helper, response)
    outcome = "shared" if response.power >= suspense_level(catalyst, delay) else "splat"
    if outcome == "shared":
        calm_and_reveal(world, child, helper, parent, spot_cfg, response)
    else:
        comic_splat(world, child, helper, parent, spot_cfg, response)

    world.facts["outcome"] = outcome
    world.facts["mystery_wobble"] = world.get("spot").meters["wobbling"] >= THRESHOLD
    world.facts["magic_glow"] = world.get("papaya").meters["glowing"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "papaya": [
        (
            "What is a papaya?",
            "A papaya is a sweet tropical fruit with orange flesh and shiny black seeds inside. People can slice it and eat it as a snack.",
        )
    ],
    "mole": [
        (
            "What is a mole?",
            "A mole is a small animal that digs tunnels in the ground. It has strong front paws and a very good nose.",
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic in a story means something impossible happens, like a fruit glowing or a pebble making wishes feel real. It adds wonder and surprise.",
        )
    ],
    "garden": [
        (
            "Why might a mole be in a garden?",
            "A garden has soft dirt that is easy to dig through. Moles also look for little things to eat under the ground there.",
        )
    ],
    "greenhouse": [
        (
            "What is a greenhouse?",
            "A greenhouse is a glass house where plants grow warm and protected. Sunlight gets in, and the air inside can feel damp and bright.",
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where many fruit trees grow together. People go there to care for the trees and pick fruit.",
        )
    ],
    "wish": [
        (
            "What is a wishing pebble in a pretend story?",
            "A wishing pebble is a made-up lucky stone that characters treat like a tiny magic helper. In real life it is only a pebble, but in stories it can start surprising events.",
        )
    ],
    "moon": [
        (
            "Why does moonlight feel mysterious at night?",
            "Moonlight is soft and pale, so it makes shapes and shadows look different from daytime. That can make ordinary things seem magical or spooky in a fun way.",
        )
    ],
    "spell": [
        (
            "What is a spell?",
            "A spell is a piece of pretend magic that makes something unusual happen. Story spells can sparkle, glow, or turn a mistake into a surprise.",
        )
    ],
    "sharing": [
        (
            "Why can sharing food calm a problem in a story?",
            "Sharing can turn a fight or mystery into friendliness. When someone feels welcomed, they are more likely to stop grabbing and start behaving gently.",
        )
    ],
    "music": [
        (
            "Why can a gentle song help when someone is scared?",
            "A soft song can make a moment feel calmer and less jumpy. It gives everyone something steady to listen to.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "papaya",
    "mole",
    "garden",
    "greenhouse",
    "orchard",
    "magic",
    "wish",
    "moon",
    "spell",
    "sharing",
    "music",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    spot = f["spot_cfg"]
    catalyst = f["catalyst"]
    outcome = f["outcome"]
    if outcome == "shared":
        end = "ends with everyone sharing the snack and laughing"
    else:
        end = "ends with a silly papaya splat and a laughing cleanup"
    return [
        f'Write a funny bedtime story for a 3-to-5-year-old that includes the words "papaya" and "mole", uses surprise, magic, and suspense, and {end}.',
        f"Tell a light comedy where {child.id} hides a papaya in {spot.phrase}, something magical happens because of a {catalyst.label}, and a mole turns the mystery into a joke.",
        f"Write a child-friendly suspense story where {helper.id} and {child.id} hear a wobble in {world.setting.place}, creep closer, and discover that the scary mystery is actually silly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    spot = f["spot_cfg"]
    catalyst = f["catalyst"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.id}, and a sneaky mole in {world.setting.place}. The whole problem starts because {child.id} is trying to keep a papaya surprise secret.",
        ),
        (
            f"Why did {child.id} hide the papaya?",
            f"{child.id} hid the papaya to save it for a surprise snack. That secret is what lets the wobbling mystery begin.",
        ),
        (
            f"What made the papaya seem magical?",
            f"The {catalyst.label} touched the hidden papaya, and it began to glow. That magic made the quiet hiding place feel strange and suspenseful.",
        ),
        (
            "Why did the children feel nervous?",
            f"They heard rustling and saw {spot.label} start to wobble. Because the papaya was hidden, they could not see the mole yet, so the bumping felt mysterious.",
        ),
    ]
    if outcome == "shared":
        qa.append(
            (
                "How did they solve the mystery?",
                f"They did not shout or run. Instead, they {response.qa_text}, which made the mole come out calmly and turned the strange wobble into a friendly surprise.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with laughter and shared papaya. The scary-seeming mystery became funny once everyone saw the mole and understood what had happened.",
            )
        )
    else:
        qa.append(
            (
                "What happened when their plan was too slow?",
                f"The enchanted papaya burst in a silly orange splat before the children could calm everything down. That surprise broke the suspense and made the whole scene funny instead of scary.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with sticky cleanup, laughing children, and a mole wearing papaya peel like a helmet. Even though the snack got messy, the family was safe and cheerful at the end.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"papaya", "mole", "magic"}
    tags |= set(world.setting.tags)
    tags |= set(f["catalyst"].tags)
    tags |= set(f["response"].tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        spot="basket",
        catalyst="wishing_pebble",
        response="share_slice",
        child_name="Lina",
        child_gender="girl",
        helper_name="Pip",
        helper_gender="boy",
        parent="mother",
        trait="giggly",
        delay=0,
    ),
    StoryParams(
        place="orchard",
        spot="stump",
        catalyst="moonbeam",
        response="share_slice",
        child_name="Max",
        child_gender="boy",
        helper_name="Ivy",
        helper_gender="girl",
        parent="father",
        trait="dramatic",
        delay=1,
    ),
    StoryParams(
        place="greenhouse",
        spot="wheelbarrow",
        catalyst="sneeze_spell",
        response="sing_jingle",
        child_name="Ruby",
        child_gender="girl",
        helper_name="Toby",
        helper_gender="boy",
        parent="mother",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        place="garden",
        spot="wheelbarrow",
        catalyst="moonbeam",
        response="napkin_trail",
        child_name="Eli",
        child_gender="boy",
        helper_name="June",
        helper_gender="girl",
        parent="father",
        trait="clever",
        delay=1,
    ),
    StoryParams(
        place="orchard",
        spot="basket",
        catalyst="sneeze_spell",
        response="share_slice",
        child_name="Nora",
        child_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        parent="mother",
        trait="bouncy",
        delay=0,
    ),
]


ASP_RULES = r"""
valid(Place, Spot, Cat) :-
    setting(Place), spot(Spot), catalyst(Cat),
    affords_spot(Place, Spot), affords_catalyst(Place, Cat),
    accessible(Spot).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

severity(V) :- chosen_catalyst(C), surge(C, S), delay(D), V = S + D.
success :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(shared) :- success.
outcome(splat)  :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in sorted(setting.afford_spots):
            lines.append(asp.fact("affords_spot", sid, spot))
        for cat in sorted(setting.afford_catalysts):
            lines.append(asp.fact("affords_catalyst", sid, cat))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.accessible:
            lines.append(asp.fact("accessible", spot_id))
    for cat_id, catalyst in CATALYSTS.items():
        lines.append(asp.fact("catalyst", cat_id))
        lines.append(asp.fact("surge", cat_id, catalyst.surge))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_catalyst", params.catalyst),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a papaya surprise, a mole, and silly magic."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--catalyst", choices=CATALYSTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time for the wobble to build")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def _pick_helper(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    choices = [name for name in HELPER_NAMES if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot is not None and not SPOTS[args.spot].accessible:
        raise StoryError(explain_spot(SPOTS[args.spot]))
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.spot is None or combo[1] == args.spot)
        and (args.catalyst is None or combo[2] == args.catalyst)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, spot, catalyst = rng.choice(combos)
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    helper_name, helper_gender = _pick_helper(rng, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        place=place,
        spot=spot,
        catalyst=catalyst,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.catalyst not in CATALYSTS:
        raise StoryError(f"(Unknown catalyst: {params.catalyst})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if (params.place, params.spot, params.catalyst) not in set(valid_combos()):
        if params.spot in SPOTS and not SPOTS[params.spot].accessible:
            raise StoryError(explain_spot(SPOTS[params.spot]))
        raise StoryError("(The chosen place, spot, and catalyst do not form a reasonable story.)")

    world = tell(
        setting=SETTINGS[params.place],
        spot_cfg=SPOTS[params.spot],
        catalyst=CATALYSTS[params.catalyst],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))

    py_sens = {r.id for r in sensible_responses()}
    clingo_sens = set(asp_sensible())
    if py_sens == clingo_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

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
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: normal generate/emit smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, spot, catalyst) combos:\n")
        for place, spot, catalyst in combos:
            print(f"  {place:10} {spot:12} {catalyst}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.catalyst} at {p.place} ({p.spot}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
