#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cranapple_dog_dim_conflict_rhyming_story.py
======================================================================

A standalone story world for a tiny rhyming tale about a child, a worried dog,
one little light, and a quarrel that softens into understanding.

Seed words:
- cranapple
- dog-dim

World premise
-------------
At dusk, a child carries a cranapple treat and a rhyme book to a cozy spot near
the family dog's den. The dog slips away with the only glow because the den is
too dark and scary. The child feels cross. Then the child notices how
dog-dim the den really is, understands the dog's fear, and chooses a sensible
way to share light instead of scolding.

The reasonableness constraint is simple and concrete:
- the resolution must actually fit the place
- and if the resolution needs a hangable light, the chosen glow must hang

So the world refuses combinations like hanging a smooth jar-lamp from a place
with no hook, or opening a door in a setting that has no nearby warm door.

Run it
------
python storyworlds/worlds/gpt-5.4/cranapple_dog_dim_conflict_rhyming_story.py
python storyworlds/worlds/gpt-5.4/cranapple_dog_dim_conflict_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/cranapple_dog_dim_conflict_rhyming_story.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/cranapple_dog_dim_conflict_rhyming_story.py --asp
python storyworlds/worlds/gpt-5.4/cranapple_dog_dim_conflict_rhyming_story.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "dog":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain config
# ---------------------------------------------------------------------------
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
    den_label: str
    child_spot: str
    affordances: set[str] = field(default_factory=set)
    dusk_line: str = ""
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
class Treat:
    id: str
    label: str
    phrase: str
    crumb: str
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
class Glow:
    id: str
    label: str
    phrase: str
    glow_line: str
    hangable: bool = False
    portable: bool = True
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
class Resolution:
    id: str
    need: str
    effect: str
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_dog_fears_dark(world: World) -> list[str]:
    dog = world.get("dog")
    den = world.get("den")
    if den.meters["brightness"] >= THRESHOLD:
        return []
    if "timid" not in dog.traits and "trembly" not in dog.traits:
        return []
    sig = ("fear_dark", dog.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dog.memes["fear"] += 1
    return []


def _r_light_loss_makes_conflict(world: World) -> list[str]:
    child = world.get("child")
    dog = world.get("dog")
    spot = world.get("spot")
    if spot.meters["brightness"] >= THRESHOLD:
        return []
    if dog.memes["fear"] < THRESHOLD:
        return []
    sig = ("conflict", child.id, dog.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["frustration"] += 1
    child.memes["conflict"] += 1
    dog.memes["conflict"] += 1
    return []


def _r_shared_light_brings_relief(world: World) -> list[str]:
    child = world.get("child")
    dog = world.get("dog")
    den = world.get("den")
    spot = world.get("spot")
    if den.meters["brightness"] < THRESHOLD:
        return []
    if world.facts.get("ending_mode") == "two_pools_of_light":
        good = spot.meters["brightness"] >= THRESHOLD
    else:
        good = child.attrs.get("together_place") == den.label or child.attrs.get("together_place") == spot.label
    if not good:
        return []
    sig = ("relief", child.id, dog.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    dog.memes["relief"] += 1
    child.memes["care"] += 1
    dog.memes["trust"] += 1
    child.memes["conflict"] = 0.0
    dog.memes["conflict"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="dog_fears_dark", tag="emotional", apply=_r_dog_fears_dark),
    Rule(name="light_loss_conflict", tag="social", apply=_r_light_loss_makes_conflict),
    Rule(name="shared_light_relief", tag="social", apply=_r_shared_light_brings_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def resolution_fits(setting: Setting, glow: Glow, resolution: Resolution) -> bool:
    if resolution.id not in setting.affordances:
        return False
    if resolution.need == "hangable_light" and not glow.hangable:
        return False
    if resolution.need == "portable_light" and not glow.portable:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for tid in TREATS:
            for gid, glow in GLOWS.items():
                for rid, resolution in RESOLUTIONS.items():
                    if resolution_fits(SETTINGS[sid], glow, resolution):
                        combos.append((sid, tid, gid, rid))
    return combos


def explain_rejection(setting: Setting, glow: Glow, resolution: Resolution) -> str:
    if resolution.id not in setting.affordances:
        return (
            f"(No story: {resolution.id} does not fit {setting.place}. "
            f"That place simply doesn't offer the right way to share light.)"
        )
    if resolution.need == "hangable_light" and not glow.hangable:
        return (
            f"(No story: {glow.label} cannot be hung, so it cannot support "
            f"{resolution.id}. Pick a hangable light instead.)"
        )
    if resolution.need == "portable_light" and not glow.portable:
        return (
            f"(No story: {glow.label} cannot be carried where the child and dog need it.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_why_dog_took_light(world: World) -> dict:
    sim = world.copy()
    dog = sim.get("dog")
    den = sim.get("den")
    spot = sim.get("spot")
    glow = sim.get("glow")
    den.meters["brightness"] = 0.0
    spot.meters["brightness"] = 1.0
    glow.attrs["location"] = "spot"
    propagate(sim, narrate=False)
    if dog.memes["fear"] >= THRESHOLD:
        spot.meters["brightness"] = 0.0
        den.meters["brightness"] = 1.0
        glow.attrs["location"] = "den"
        propagate(sim, narrate=False)
    return {
        "dog_afraid": dog.memes["fear"] >= THRESHOLD,
        "child_cross": sim.get("child").memes["frustration"] >= THRESHOLD,
        "den_dark": den.meters["brightness"] < THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, dog: Entity, treat: Treat, glow: Glow) -> None:
    world.say(
        f"{world.setting.dusk_line} {child.id} came skipping by with {treat.phrase}, "
        f"and {dog.id} trotted close with a hopeful nose and bright black eye."
    )
    world.say(
        f"In one hand shone {glow.phrase}; in the other rested the rhyme book small. "
        f'"A snack, a song, a cozy light — we\'ll have the sweetest dusk of all," '
        f"{child.id} said."
    )


def settle_in(world: World, child: Entity, dog: Entity, treat: Treat, glow: Glow) -> None:
    spot = world.get("spot")
    den = world.get("den")
    glow_ent = world.get("glow")
    spot.meters["brightness"] = 1.0
    den.meters["brightness"] = 0.0
    glow_ent.attrs["location"] = "spot"
    child.attrs["together_place"] = spot.label
    world.say(
        f"They curled up by {world.setting.child_spot}, where crumbs of {treat.crumb} "
        f"waited neat on a napkin white, and {glow.glow_line} made the pages light."
    )


def dog_slips_away(world: World, child: Entity, dog: Entity) -> None:
    den = world.get("den")
    spot = world.get("spot")
    glow = world.get("glow")
    propagate(world, narrate=False)
    dog.attrs["took_light"] = dog.memes["fear"] >= THRESHOLD
    if dog.attrs["took_light"]:
        spot.meters["brightness"] = 0.0
        den.meters["brightness"] = 1.0
        glow.attrs["location"] = "den"
    propagate(world, narrate=False)
    world.say(
        f"But {dog.id} heard the leaves go hiss and the fence give back a scratchy hymn. "
        f"He snatched the light and dashed to {world.setting.den_label}, and all at once the nook went dog-dim."
    )


def child_quarrel(world: World, child: Entity, dog: Entity, treat: Treat) -> None:
    world.say(
        f'"{dog.id}!" cried {child.id}. "That was our glow, our book, our bite of sweet {treat.label}!" '
        f"{child.pronoun().capitalize()} stomped one foot, and the rhyme turned sharp instead of complete."
    )
    world.say(
        f'{child.id} followed with a wrinkled brow. "{dog.id}, that was not kind at all."'
    )


def notice_fear(world: World, child: Entity, dog: Entity) -> None:
    pred = predict_why_dog_took_light(world)
    world.facts["predicted_fear"] = pred["dog_afraid"]
    world.facts["predicted_cross"] = pred["child_cross"]
    dog.memes["shiver"] += 1
    world.say(
        f"Then {child.id} looked beneath the flap and saw not mischief, bold or sly. "
        f"{dog.id} was tucked in small and tight, with worried ears and moon-round eye."
    )
    world.say(
        f"The den was dark without the glow; its corners seemed too deep, too wide. "
        f"{child.id} felt the anger shrink and guessed that fear was what {dog.id} tried to hide."
    )


def resolve_story(world: World, child: Entity, dog: Entity, resolution: Resolution) -> None:
    den = world.get("den")
    spot = world.get("spot")
    glow = world.get("glow")
    if resolution.effect == "two_pools_of_light":
        den.meters["brightness"] = 1.0
        spot.meters["brightness"] = 1.0
        child.attrs["together_place"] = spot.label
        world.facts["ending_mode"] = "two_pools_of_light"
    else:
        den.meters["brightness"] = 1.0
        spot.meters["brightness"] = 0.0
        child.attrs["together_place"] = den.label
        world.facts["ending_mode"] = "one_shared_place"
    world.facts["resolution_effect"] = resolution.effect
    glow.attrs["location"] = "shared"
    propagate(world, narrate=False)
    world.say(resolution.text)
    world.say(
        f'Soon the grumble grew more gentle. "{dog.id}, next time, nudge me first," '
        f"{child.id} said. Then {child.pronoun()} scratched {dog.pronoun('object')} under the chin, and the quarrel lost its thirst."
    )


def ending(world: World, child: Entity, dog: Entity, treat: Treat) -> None:
    mode = world.facts.get("ending_mode")
    if mode == "two_pools_of_light":
        world.say(
            f"They read a rhyme beside the napkin, and {dog.id} watched from his glowing den. "
            f"Crumbs of {treat.label} and calmer hearts made soft night feel like home again."
        )
    else:
        world.say(
            f"So child and dog sat nose to knee where one warm circle held them tight. "
            f"They shared the last of {treat.label}, and every line came out just right."
        )


def tell(
    setting: Setting,
    treat: Treat,
    glow: Glow,
    resolution: Resolution,
    child_name: str = "Mia",
    child_type: str = "girl",
    child_trait: str = "gentle",
    dog_name: str = "Pip",
    dog_trait: str = "timid",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        traits=[child_trait],
        role="child",
        attrs={"display_name": child_name},
    ))
    dog = world.add(Entity(
        id="dog",
        kind="character",
        type="dog",
        label=dog_name,
        traits=[dog_trait],
        role="dog",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    spot = world.add(Entity(
        id="spot",
        type="place",
        label=setting.child_spot,
        attrs={"place": setting.child_spot},
    ))
    den = world.add(Entity(
        id="den",
        type="place",
        label=setting.den_label,
        attrs={"place": setting.den_label},
    ))
    glow_ent = world.add(Entity(
        id="glow",
        type="light",
        label=glow.label,
        attrs={"location": "spot", "hangable": glow.hangable},
    ))
    snack = world.add(Entity(
        id="snack",
        type="treat",
        label=treat.label,
    ))

    child.memes["hope"] = 1.0
    dog.memes["fear"] = 0.0
    dog.memes["trust"] = 0.0
    child.memes["frustration"] = 0.0
    child.memes["conflict"] = 0.0
    dog.memes["conflict"] = 0.0
    spot.meters["brightness"] = 0.0
    den.meters["brightness"] = 0.0
    world.facts["ending_mode"] = ""
    world.facts["predicted_fear"] = False
    world.facts["predicted_cross"] = False

    introduce(world, child, dog, treat, glow)
    settle_in(world, child, dog, treat, glow)

    world.para()
    dog_slips_away(world, child, dog)
    child_quarrel(world, child, dog, treat)

    world.para()
    notice_fear(world, child, dog)
    resolve_story(world, child, dog, resolution)
    ending(world, child, dog, treat)

    world.facts.update(
        child=child,
        dog=dog,
        parent=parent,
        spot=spot,
        den=den,
        glow_cfg=glow,
        treat_cfg=treat,
        resolution=resolution,
        setting=setting,
        child_name=child_name,
        dog_name=dog_name,
        conflict_happened=child.memes["frustration"] >= THRESHOLD,
        dog_took_light=dog.attrs.get("took_light", False),
        peace_made=child.memes["relief"] >= THRESHOLD and dog.memes["relief"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "porch": Setting(
        id="porch",
        place="the back porch",
        den_label="the doghouse beside the porch",
        child_spot="the porch step",
        affordances={"hang_hook", "share_by_den", "open_kitchen_door"},
        dusk_line="Dusk dripped down the porch in plum and blue",
        tags={"porch"},
    ),
    "apple_tree": Setting(
        id="apple_tree",
        place="the apple tree patch",
        den_label="the little doghouse under the tree",
        child_spot="the crate under the apple tree",
        affordances={"hang_hook", "share_by_den"},
        dusk_line="Under the apple tree the shadows grew",
        tags={"tree"},
    ),
    "shed_side": Setting(
        id="shed_side",
        place="the shed side path",
        den_label="the dog nook by the shed wall",
        child_spot="the smooth flat step by the shed",
        affordances={"share_by_den", "open_kitchen_door"},
        dusk_line="Along the shed side lane the cool wind blew",
        tags={"shed"},
    ),
}

TREATS = {
    "cranapple_tart": Treat(
        id="cranapple_tart",
        label="cranapple tart",
        phrase="a little cranapple tart",
        crumb="cranapple crust",
        tags={"cranapple"},
    ),
    "cranapple_bun": Treat(
        id="cranapple_bun",
        label="cranapple bun",
        phrase="a soft cranapple bun",
        crumb="cranapple sugar",
        tags={"cranapple"},
    ),
    "cranapple_cake": Treat(
        id="cranapple_cake",
        label="cranapple cake",
        phrase="a slice of cranapple cake",
        crumb="cranapple cake",
        tags={"cranapple"},
    ),
}

GLOWS = {
    "clip_lantern": Glow(
        id="clip_lantern",
        label="clip lantern",
        phrase="a little clip lantern",
        glow_line="its amber ring made the rhyme book gleam",
        hangable=True,
        portable=True,
        tags={"lantern", "light"},
    ),
    "glow_jar": Glow(
        id="glow_jar",
        label="glow jar",
        phrase="a blue glow jar",
        glow_line="its soft blue shine made the rhyme book gleam",
        hangable=False,
        portable=True,
        tags={"light", "jar"},
    ),
    "star_lamp": Glow(
        id="star_lamp",
        label="star lamp",
        phrase="a star lamp with a gentle strap",
        glow_line="its warm gold spark made the rhyme book gleam",
        hangable=True,
        portable=True,
        tags={"light", "lamp"},
    ),
}

RESOLUTIONS = {
    "hang_hook": Resolution(
        id="hang_hook",
        need="hangable_light",
        effect="two_pools_of_light",
        text=(
            "So the child clipped the light to a hook just outside the den, where it shone for both places at once. "
            "One warm ring reached the doghouse, and one warm ring reached the reading spot, bright and clear and kind."
        ),
        qa_text="clipped the light where it could shine on both the den and the reading spot",
        tags={"share_light"},
    ),
    "share_by_den": Resolution(
        id="share_by_den",
        need="portable_light",
        effect="one_shared_place",
        text=(
            "So the child picked up the napkin and book, then scooted close beside the den with the light between them. "
            "Instead of pulling the glow away, the child moved the story nearer until fear had less room to grow."
        ),
        qa_text="moved the snack, book, and light beside the den so they could share one cozy place",
        tags={"share_space"},
    ),
    "open_kitchen_door": Resolution(
        id="open_kitchen_door",
        need="portable_light",
        effect="one_shared_place",
        text=(
            "So the child set the light by the doorway and pushed the kitchen door wide, letting a warm stripe of house-light pour outside. "
            "The bright path touched the den, and the child sat nearby where the dog could see a friend and a safe way in."
        ),
        qa_text="opened the warm door and set the light nearby so the den was no longer dark",
        tags={"door_light"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Ella", "Ruby", "Ivy", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Owen", "Max", "Theo", "Eli"]
DOG_NAMES = ["Pip", "Moss", "Toby", "Bean", "Patch", "Rufus", "Dot"]
CHILD_TRAITS = ["gentle", "bright", "patient", "lively", "thoughtful"]
DOG_TRAITS = ["timid", "trembly", "shy"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    treat: str
    glow: str
    resolution: str
    child_name: str
    child_gender: str
    dog_name: str
    child_trait: str
    dog_trait: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "cranapple": [(
        "What does cranapple mean?",
        "Cranapple is a flavor made from cranberry and apple together. It tastes fruity and tart."
    )],
    "light": [(
        "Why can a little light help a scared dog?",
        "A little light helps because it lets the dog see the space clearly. When shadows shrink, scary shapes stop feeling so mysterious."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light you can carry from place to place. It helps people see when it gets dark."
    )],
    "doghouse": [(
        "What is a doghouse for?",
        "A doghouse is a small shelter where a dog can rest and feel safe. It gives the dog a snug place out of wind or weather."
    )],
    "share_light": [(
        "How can two friends share one light?",
        "They can put the light where both can see it, or sit closer together beside it. Sharing works best when both people notice what the other one needs."
    )],
    "share_space": [(
        "Why is sitting nearby calming?",
        "Sitting nearby shows, 'You are not alone.' A calm friend close by can make a worried animal feel safe again."
    )],
    "door_light": [(
        "Why does opening a bright door help at night?",
        "A bright open door makes a dark place feel less lonely. It also gives a clear path toward warmth and safety."
    )],
}
KNOWLEDGE_ORDER = ["cranapple", "light", "lantern", "doghouse", "share_light", "share_space", "door_light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    treat = f["treat_cfg"]
    setting = f["setting"]
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old that includes the words '
            f'"cranapple" and "dog-dim". Make it about a child and a dog having a conflict over a little light.'
        ),
        (
            f"Tell a gentle conflict story in rhyming prose where {child.attrs['display_name']} brings {treat.phrase} "
            f"to {setting.place}, but {dog.label} steals the glow because the den feels too dark."
        ),
        (
            "Write a bedtime-style rhyme where anger changes into understanding after a child notices a dog's fear."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    treat = f["treat_cfg"]
    resolution = f["resolution"]
    setting = f["setting"]
    child_name = f["child_name"]
    dog_name = f["dog_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child with a rhyme book, and {dog_name}, the family dog. They start the evening together, but they quarrel when the dog runs off with the only light."
        ),
        (
            f"Why was there a conflict between {child_name} and {dog_name}?",
            f"There was a conflict because {dog_name} took the light away from the reading spot, and {child_name} felt upset and interrupted. The snack and rhyme time suddenly went dark, so the child thought the dog had spoiled the plan."
        ),
        (
            f"Why did {dog_name} take the light?",
            f"{dog_name} took the light because the den felt scary and dark. When {child_name} looked closer, the child realized the dog was not being mean — he was trying to feel safe."
        ),
        (
            f"What changed {child_name}'s feelings?",
            f"{child_name} changed after noticing how dog-dim the den really was and seeing {dog_name} tucked in tight. That turned the child's anger into understanding, because the problem was fear rather than selfishness."
        ),
        (
            "How did they solve the problem?",
            f"They solved it when the child {resolution.qa_text}. The fix matched the place and gave the dog enough light to feel calm again."
        ),
        (
            "How did the story end?",
            f"It ended with shared light and softer hearts. The child and dog could enjoy the cranapple treat and the rhyme again because the quarrel had been gently repaired."
        ),
    ]
    if resolution.effect == "two_pools_of_light":
        qa.append((
            "What shows that something changed at the end?",
            f"The ending image shows two bright places at once: the reading spot and the den. That matters because the child no longer had to choose between the treat and the dog's comfort."
        ))
    else:
        qa.append((
            "What shows that something changed at the end?",
            f"The ending image shows the child moving close instead of staying apart. That matters because closeness, not scolding, is what helped the dog feel safe."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["treat_cfg"].tags) | set(world.facts["glow_cfg"].tags) | set(world.facts["resolution"].tags) | {"doghouse"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,T,G,R) :- setting(S), treat(T), glow(G), resolution(R),
                  affords(S,R), need(R,portable_light), portable(G).
valid(S,T,G,R) :- setting(S), treat(T), glow(G), resolution(R),
                  affords(S,R), need(R,hangable_light), hangable(G).

ending_mode(R,two_pools_of_light) :- resolution(R), effect(R,two_pools_of_light).
ending_mode(R,one_shared_place)   :- resolution(R), effect(R,one_shared_place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for rid in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, rid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for gid, glow in GLOWS.items():
        lines.append(asp.fact("glow", gid))
        if glow.portable:
            lines.append(asp.fact("portable", gid))
        if glow.hangable:
            lines.append(asp.fact("hangable", gid))
    for rid, resolution in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("need", rid, resolution.need))
        lines.append(asp.fact("effect", rid, resolution.effect))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending_modes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show ending_mode/2."))
    return sorted(set(asp.atoms(model, "ending_mode")))


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

    py_modes = {(rid, res.effect) for rid, res in RESOLUTIONS.items()}
    asp_modes = set(asp_ending_modes())
    if py_modes == asp_modes:
        print("OK: ending modes match.")
    else:
        rc = 1
        print("MISMATCH in ending modes:")
        if asp_modes - py_modes:
            print("  only in clingo:", sorted(asp_modes - py_modes))
        if py_modes - asp_modes:
            print("  only in python:", sorted(py_modes - asp_modes))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming storyworld about a child, a dog, one light, and a gentle conflict."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--glow", choices=GLOWS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--dog-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.glow and args.resolution:
        setting = SETTINGS[args.setting]
        glow = GLOWS[args.glow]
        resolution = RESOLUTIONS[args.resolution]
        if not resolution_fits(setting, glow, resolution):
            raise StoryError(explain_rejection(setting, glow, resolution))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.treat is None or combo[1] == args.treat)
        and (args.glow is None or combo[2] == args.glow)
        and (args.resolution is None or combo[3] == args.resolution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, treat_id, glow_id, resolution_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    child_trait = rng.choice(CHILD_TRAITS)
    dog_trait = rng.choice(DOG_TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        treat=treat_id,
        glow=glow_id,
        resolution=resolution_id,
        child_name=child_name,
        child_gender=gender,
        dog_name=dog_name,
        child_trait=child_trait,
        dog_trait=dog_trait,
        parent=parent,
    )


def _child_ref(name: str) -> str:
    return name


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        treat = TREATS[params.treat]
        glow = GLOWS[params.glow]
        resolution = RESOLUTIONS[params.resolution]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})")

    if not resolution_fits(setting, glow, resolution):
        raise StoryError(explain_rejection(setting, glow, resolution))

    world = tell(
        setting=setting,
        treat=treat,
        glow=glow,
        resolution=resolution,
        child_name=_child_ref(params.child_name),
        child_type=params.child_gender,
        child_trait=params.child_trait,
        dog_name=params.dog_name,
        dog_trait=params.dog_trait,
        parent_type=params.parent,
    )

    story_text = world.render()
    child_name = params.child_name
    dog_name = params.dog_name
    story_text = story_text.replace("child", child_name).replace("dog", dog_name)

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


CURATED = [
    StoryParams(
        setting="porch",
        treat="cranapple_tart",
        glow="clip_lantern",
        resolution="hang_hook",
        child_name="Mia",
        child_gender="girl",
        dog_name="Pip",
        child_trait="gentle",
        dog_trait="timid",
        parent="mother",
    ),
    StoryParams(
        setting="apple_tree",
        treat="cranapple_bun",
        glow="glow_jar",
        resolution="share_by_den",
        child_name="Ben",
        child_gender="boy",
        dog_name="Moss",
        child_trait="thoughtful",
        dog_trait="shy",
        parent="father",
    ),
    StoryParams(
        setting="shed_side",
        treat="cranapple_cake",
        glow="star_lamp",
        resolution="open_kitchen_door",
        child_name="Ruby",
        child_gender="girl",
        dog_name="Bean",
        child_trait="patient",
        dog_trait="trembly",
        parent="mother",
    ),
    StoryParams(
        setting="porch",
        treat="cranapple_bun",
        glow="glow_jar",
        resolution="share_by_den",
        child_name="Theo",
        child_gender="boy",
        dog_name="Patch",
        child_trait="bright",
        dog_trait="timid",
        parent="father",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show ending_mode/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treat, glow, resolution) combos:\n")
        for setting, treat, glow, resolution in combos:
            print(f"  {setting:10} {treat:15} {glow:12} {resolution}")
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
            header = f"### {p.child_name} & {p.dog_name}: {p.treat}, {p.glow}, {p.resolution} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
