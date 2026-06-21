#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crave_baker_surprise_curiosity_tall_tale.py
======================================================================

A standalone storyworld about a child who craves an enormous bakery treat,
grows too curious about the baker's surprise, and must learn that some wonders
need patient hands. The style leans toward a gentle Tall Tale: ovens sigh like
dragons, dough rises like a hill, and village bakery stories grow a little
larger than life.

Core premise
------------
A child visits a bakery and craves an outrageously grand treat. The baker is
making a surprise version of it and asks the child to wait. Curiosity swells.
If the child peeks too soon, opening the oven may spoil a delicate bake. A
skilled baker can sometimes save it with a steady remedy; sturdy bakes survive
the peek more easily. In the happiest endings, the child helps in a safer way
and the surprise still arrives, proving that waiting changed something real.

Reasonableness constraint
-------------------------
Not every baked thing makes sense for this premise. Only pastries that can hide
a "surprise middle" and plausibly bake into a dramatic Tall Tale reveal belong
in the story. The world refuses flat or open treats that cannot honestly hide a
surprise and later reveal it. The Python gate and the inline ASP twin enforce
the same compatibility rules.

Run it
------
    python storyworlds/worlds/gpt-5.4/crave_baker_surprise_curiosity_tall_tale.py
    python storyworlds/worlds/gpt-5.4/crave_baker_surprise_curiosity_tall_tale.py --pastry moon_bun
    python storyworlds/worlds/gpt-5.4/crave_baker_surprise_curiosity_tall_tale.py --pastry cookie   # rejected
    python storyworlds/worlds/gpt-5.4/crave_baker_surprise_curiosity_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/crave_baker_surprise_curiosity_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crave_baker_surprise_curiosity_tall_tale.py --verify
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
    can_bake: bool = False
    can_help: bool = False
    openable: bool = False
    # physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "baker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain configs
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
class Pastry:
    id: str
    label: str
    phrase: str
    giant_phrase: str
    reveal_text: str
    hideable: bool
    delicate: bool
    rise: int
    open_too_soon_text: str
    success_slice: str
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
class SurpriseFill:
    id: str
    label: str
    phrase: str
    reveal_line: str
    color: str
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
class Remedy:
    id: str
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
class HelperTask:
    id: str
    text: str
    tail: str
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


def _r_peek_spoils(world: World) -> list[str]:
    out: list[str] = []
    oven = world.get("oven")
    pastry = world.get("pastry")
    if oven.meters["opened"] < THRESHOLD:
        return out
    if pastry.attrs.get("delicate") != 1:
        return out
    sig = ("peek_spoils", pastry.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pastry.meters["slump"] += 1
    pastry.meters["height"] -= 1
    child = world.get("child")
    baker = world.get("baker")
    child.memes["worry"] += 1
    baker.memes["concern"] += 1
    out.append("__slump__")
    return out


def _r_steam_reveals(world: World) -> list[str]:
    out: list[str] = []
    oven = world.get("oven")
    if oven.meters["opened"] < THRESHOLD:
        return out
    sig = ("steam", oven.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["steam"] += 1
    out.append("__steam__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="peek_spoils", tag="physical", apply=_r_peek_spoils),
    Rule(name="steam_reveals", tag="physical", apply=_r_steam_reveals),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def can_hide_surprise(pastry: Pastry) -> bool:
    return pastry.hideable


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def slump_severity(pastry: Pastry, peek_count: int) -> int:
    return (2 if pastry.delicate else 0) + peek_count


def is_saved(remedy: Remedy, pastry: Pastry, peek_count: int) -> bool:
    if not pastry.delicate:
        return True
    return remedy.power >= slump_severity(pastry, peek_count)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pastry_id, pastry in PASTRIES.items():
        for surprise_id in SURPRISES:
            if can_hide_surprise(pastry):
                combos.append((pastry_id, surprise_id))
    return combos


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_peek(world: World) -> dict:
    sim = world.copy()
    do_peek(sim, narrate=False)
    pastry = sim.get("pastry")
    return {
        "slumps": pastry.meters["slump"] >= THRESHOLD,
        "height": pastry.meters["height"],
        "steam": sim.get("room").meters["steam"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, baker: Entity, pastry: Pastry) -> None:
    child.memes["wonder"] += 1
    child.memes["crave"] += 1
    world.say(
        f"In a town where flour dust drifted through the morning like pale snow, "
        f"{child.id} hurried to the bakery with a grand crave in {child.pronoun('possessive')} belly."
    )
    world.say(
        f"Behind the counter stood {baker.id}, the baker, who was said to knead dough so high "
        f"that sparrows sometimes circled it as if it were a hill."
    )
    world.say(
        f"That day the whole shop smelled of butter and sugar, and {child.id} could think of nothing "
        f"but {pastry.giant_phrase}."
    )


def promise_surprise(world: World, child: Entity, baker: Entity,
                     pastry: Pastry, surprise: SurpriseFill) -> None:
    pastry_ent = world.get("pastry")
    pastry_ent.meters["height"] = float(pastry.rise)
    pastry_ent.attrs["delicate"] = 1 if pastry.delicate else 0
    pastry_ent.attrs["peek_count"] = 0
    world.say(
        f'"Could you make me {pastry.giant_phrase}?" {child.id} asked. '
        f'"One so big it could shade a goat?"'
    )
    world.say(
        f'{baker.id} smiled into {baker.pronoun("possessive")} floury beard. '
        f'"I can do better than that," {baker.pronoun()} said. '
        f'"I am baking {pastry.phrase} with {surprise.phrase} tucked inside, and the best part is a surprise."'
    )


def task_offer(world: World, child: Entity, baker: Entity, task: HelperTask) -> None:
    child.memes["curiosity"] += 1
    baker.memes["care"] += 1
    world.say(
        f'"While it bakes, you may help me {task.text}," said {baker.id}. '
        f'"Busy hands make patient hearts."'
    )


def warning(world: World, child: Entity, baker: Entity, pastry: Pastry) -> None:
    pred = predict_peek(world)
    world.facts["predicted_slump"] = pred["slumps"]
    world.facts["predicted_height"] = pred["height"]
    world.facts["predicted_steam"] = pred["steam"]
    child.memes["curiosity"] += 1
    if pred["slumps"]:
        world.say(
            f'But curiosity began tickling {child.id} harder than a feather under the nose. '
            f'{baker.id} tapped the oven door and said, "Do not open it yet. '
            f'{pastry.open_too_soon_text}."'
        )
    else:
        world.say(
            f'Curiosity still made {child.id} lean toward the oven, so {baker.id} said, '
            f'"Do not open it yet. Let the heat do its quiet work."'
        )


def do_task(world: World, child: Entity, task: HelperTask) -> None:
    child.meters["helped"] += 1
    child.memes["focus"] += 1
    world.say(
        f"So {child.id} tried to {task.text}. For a little while, the job {task.tail} and kept "
        f"{child.pronoun('possessive')} hands from the oven."
    )


def curiosity_swells(world: World, child: Entity, pastry: Pastry) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Still, the bakery grew so fragrant that it seemed the very walls were humming. "
        f"{child.id} wondered whether the {pastry.label} had grown tall enough to bump the moon."
    )


def do_peek(world: World, narrate: bool = True) -> None:
    oven = world.get("oven")
    pastry = world.get("pastry")
    child = world.get("child")
    oven.meters["opened"] += 1
    pastry.attrs["peek_count"] = int(pastry.attrs.get("peek_count", 0)) + 1
    child.memes["defiance"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"At last {child.id} tiptoed close and tugged the oven door open a crack."
        )


def narrate_peek_result(world: World, pastry: Pastry) -> None:
    if world.get("pastry").meters["slump"] >= THRESHOLD:
        world.say(
            f"A puff of hot air rolled out, and the {pastry.label} gave the tiniest sigh, "
            f"as if it had been climbing a mountain and suddenly lost the path."
        )
    else:
        world.say(
            f"A cloud of sweet steam rolled out, but the {pastry.label} kept rising bravely inside."
        )


def baker_reacts(world: World, child: Entity, baker: Entity) -> None:
    child.memes["regret"] += 1
    world.say(
        f'"Oh, crumbs," said {child.id}. {baker.id} came over at once, not cross, but quick-eyed.'
    )


def remedy_success(world: World, baker: Entity, remedy: Remedy,
                   pastry: Pastry, surprise: SurpriseFill) -> None:
    pastry_ent = world.get("pastry")
    pastry_ent.meters["slump"] = 0.0
    pastry_ent.meters["saved"] += 1
    pastry_ent.meters["height"] = max(pastry_ent.meters["height"], float(pastry.rise))
    baker.memes["skill"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{baker.id} {remedy.text}."
    )
    world.say(
        f'Soon the bakery smelled grander than ever, and when the {pastry.label} was opened at last, '
        f'{surprise.reveal_line}'
    )


def remedy_fail(world: World, baker: Entity, remedy: Remedy,
                pastry: Pastry, surprise: SurpriseFill) -> None:
    pastry_ent = world.get("pastry")
    pastry_ent.meters["burned_pride"] += 1
    child = world.get("child")
    child.memes["sadness"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{baker.id} {remedy.fail}."
    )
    world.say(
        f"When the pan was opened, the {pastry.label} was smaller than promised, though "
        f"there was still {surprise.phrase} in the middle."
    )


def gentle_lesson(world: World, child: Entity, baker: Entity) -> None:
    child.memes["love"] += 1
    baker.memes["care"] += 1
    world.say(
        f'{baker.id} knelt so {baker.pronoun()} and {child.id} were eye to eye. '
        f'"A surprise is not made bigger by peeking," {baker.pronoun()} said softly. '
        f'"It grows best when you give it room."'
    )


def ending_happy(world: World, child: Entity, pastry: Pastry, surprise: SurpriseFill) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} took a bite and found {surprise.color} sweetness where plain bread had seemed to be. "
        f"{pastry.success_slice}"
    )
    world.say(
        f"After that, whenever {child.id} felt curiosity start to hop like a cricket, "
        f"{child.pronoun()} remembered the giant pastry and let wonder ripen before grabbing at it."
    )


def ending_sad_but_warm(world: World, child: Entity, pastry: Pastry) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} ate the little {pastry.label} anyway and said it was still good, just not the towering marvel "
        f"it might have been."
    )
    world.say(
        f"From then on, {child.pronoun()} tried to keep curious eyes and hands apart, because some wonders fall "
        f"when you rush them."
    )


def tell(pastry: Pastry, surprise: SurpriseFill, remedy: Remedy, task: HelperTask,
         child_name: str = "Mira", child_type: str = "girl",
         baker_name: str = "Old Rowan", baker_type: str = "man",
         peek_count: int = 1) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, role="child", label=child_name))
    baker = world.add(Entity(id="baker", kind="character", type=baker_type, role="baker",
                             label=baker_name, can_bake=True))
    room = world.add(Entity(id="room", type="bakery", label="the bakery"))
    oven = world.add(Entity(id="oven", type="oven", label="the oven", openable=True))
    pastry_ent = world.add(Entity(id="pastry", type="pastry", label=pastry.label))
    child.attrs["name"] = child_name
    baker.attrs["name"] = baker_name
    pastry_ent.attrs["delicate"] = 1 if pastry.delicate else 0
    pastry_ent.attrs["peek_count"] = 0
    room.meters["steam"] = 0.0
    oven.meters["opened"] = 0.0
    pastry_ent.meters["height"] = 0.0
    pastry_ent.meters["slump"] = 0.0
    pastry_ent.meters["saved"] = 0.0
    pastry_ent.meters["burned_pride"] = 0.0
    child.memes["curiosity"] = 1.0
    child.memes["crave"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["regret"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["lesson"] = 0.0
    baker.memes["care"] = 1.0
    baker.memes["skill"] = 0.0
    baker.memes["concern"] = 0.0

    introduce(world, child, baker, pastry)
    promise_surprise(world, child, baker, pastry, surprise)

    world.para()
    task_offer(world, child, baker, task)
    warning(world, child, baker, pastry)
    do_task(world, child, task)
    curiosity_swells(world, child, pastry)

    world.para()
    for _ in range(peek_count):
        do_peek(world, narrate=True)
    narrate_peek_result(world, pastry)
    baker_reacts(world, child, baker)

    saved = is_saved(remedy, pastry, peek_count)
    world.para()
    if saved:
        remedy_success(world, baker, remedy, pastry, surprise)
        gentle_lesson(world, child, baker)
        world.para()
        ending_happy(world, child, pastry, surprise)
        outcome = "saved"
    else:
        remedy_fail(world, baker, remedy, pastry, surprise)
        gentle_lesson(world, child, baker)
        world.para()
        ending_sad_but_warm(world, child, pastry)
        outcome = "slumped"

    world.facts.update(
        child=child,
        baker=baker,
        pastry_cfg=pastry,
        surprise_cfg=surprise,
        remedy=remedy,
        task=task,
        peek_count=peek_count,
        outcome=outcome,
        slumped=world.get("pastry").meters["slump"] >= THRESHOLD or outcome == "slumped",
        saved=saved,
        steam=world.get("room").meters["steam"] >= THRESHOLD,
        opened=world.get("oven").meters["opened"],
        hidden=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PASTRIES = {
    "moon_bun": Pastry(
        id="moon_bun",
        label="moon bun",
        phrase="a moon bun",
        giant_phrase="a moon bun as round as a wagon wheel",
        reveal_text="a glowing middle",
        hideable=True,
        delicate=True,
        rise=3,
        open_too_soon_text="Moon buns are shy. If the oven yawns too soon, they sink in the middle",
        success_slice="Each slice looked so full and high that it could have served as a pillow for a giant mouse.",
        tags={"bun", "baking", "patience"},
    ),
    "thunder_loaf": Pastry(
        id="thunder_loaf",
        label="thunder loaf",
        phrase="a thunder loaf",
        giant_phrase="a thunder loaf long as a canoe",
        reveal_text="a rumbling sweet center",
        hideable=True,
        delicate=False,
        rise=2,
        open_too_soon_text="Thunder loaves are sturdy, but even sturdy things deserve patience",
        success_slice="The loaf stood on the counter like a golden log from a fairy-tale forest.",
        tags={"bread", "baking", "patience"},
    ),
    "star_pocket": Pastry(
        id="star_pocket",
        label="star pocket",
        phrase="a star pocket",
        giant_phrase="a star pocket puffed as high as a scarecrow's hat",
        reveal_text="a bright filling hidden in folds",
        hideable=True,
        delicate=True,
        rise=3,
        open_too_soon_text="Star pockets need a steady oven. Open the door too soon and the puff may fall flat",
        success_slice="When it was cut, the crust opened like a tiny dawn.",
        tags={"pastry", "baking", "patience"},
    ),
    "cookie": Pastry(
        id="cookie",
        label="cookie",
        phrase="a cookie",
        giant_phrase="a cookie big as a cartwheel",
        reveal_text="not much of a hidden middle at all",
        hideable=False,
        delicate=False,
        rise=0,
        open_too_soon_text="Cookies bake fast",
        success_slice="It was still tasty.",
        tags={"cookie"},
    ),
}

SURPRISES = {
    "berry_comet": SurpriseFill(
        id="berry_comet",
        label="berry comet",
        phrase="a berry-comet filling",
        reveal_line="out slid a streak of purple berry jam bright enough to make the child gasp.",
        color="purple",
        tags={"berries", "surprise"},
    ),
    "honey_sun": SurpriseFill(
        id="honey_sun",
        label="honey sun",
        phrase="a honey-sun center",
        reveal_line="golden honey curled through the middle like a little sunrise caught in bread.",
        color="golden",
        tags={"honey", "surprise"},
    ),
    "cinnamon_map": SurpriseFill(
        id="cinnamon_map",
        label="cinnamon map",
        phrase="a cinnamon-map swirl",
        reveal_line="the inside showed a brown spiral so grand it looked like a map of a tiny windy kingdom.",
        color="brown",
        tags={"cinnamon", "surprise"},
    ),
}

REMEDIES = {
    "steam_pan": Remedy(
        id="steam_pan",
        sense=3,
        power=3,
        text="slid in a little pan of hot water, shut the oven, and told the heat to mind its manners",
        fail="tried a pan of hot water and a patient oven, but the puff had already dropped too far to climb again",
        qa_text="saved the pastry by adding steam and steady heat",
        tags={"steam", "oven", "baking"},
    ),
    "warm_cloth": Remedy(
        id="warm_cloth",
        sense=2,
        power=2,
        text="set a warm cloth over the pan for a moment and gave the dough one more calm chance to rise",
        fail="covered the pan with a warm cloth, but the pastry still stayed low and shy",
        qa_text="tried to rescue it with warmth and another gentle rise",
        tags={"warmth", "baking"},
    ),
    "loud_shout": Remedy(
        id="loud_shout",
        sense=1,
        power=0,
        text="shouted at the pastry to rise higher",
        fail="shouted at the pastry, but shouting never taught dough to stand tall",
        qa_text="shouted at it",
        tags={"silly"},
    ),
}

TASKS = {
    "count_raisin": HelperTask(
        id="count_raisin",
        text="count the raisins in a jar taller than a boot",
        tail="gave numbers to chase",
        tags={"counting"},
    ),
    "brush_glaze": HelperTask(
        id="brush_glaze",
        text="brush shine onto little rolls waiting on a tray",
        tail="filled the air with careful work",
        tags={"helping"},
    ),
    "line_tins": HelperTask(
        id="line_tins",
        text="set paper rounds into cake tins one by one",
        tail="made a neat rustling music",
        tags={"helping"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Tess", "Nora", "Ruby", "Wren", "Ada"]
BOY_NAMES = ["Finn", "Jory", "Milo", "Tobin", "Eli", "Bram", "Theo"]
BAKER_NAMES = ["Old Rowan", "Marta", "Juniper", "Mr. Bell", "Aunt Saffron"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    pastry: str
    surprise: str
    remedy: str
    task: str
    child_name: str
    child_type: str
    baker_name: str
    baker_type: str
    peek_count: int = 1
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
    "baking": [
        ("Why can opening an oven too soon be a problem?",
         "Some baked dough needs steady heat to keep rising. If you open the oven too early, cool air can make a delicate pastry sink."),
    ],
    "patience": [
        ("Why does patience matter when something is baking?",
         "Baking takes time because heat changes the dough slowly. Waiting lets the inside cook and rise the way it should."),
    ],
    "steam": [
        ("What does steam do in baking?",
         "Steam adds moisture and warmth. In some breads or pastries, that can help the crust stay soft at first so the bake can keep puffing."),
    ],
    "surprise": [
        ("What is a surprise filling in a pastry?",
         "It is something tasty hidden inside, like jam, honey, or cinnamon. You do not see it at first, so finding it feels special."),
    ],
    "berries": [
        ("What is jam made from?",
         "Jam is usually made from fruit cooked with sugar until it turns thick and sweet. Berry jam tastes bright and fruity."),
    ],
    "honey": [
        ("Where does honey come from?",
         "Honey is made by bees from flower nectar. It is sweet and golden."),
    ],
    "cinnamon": [
        ("What is cinnamon?",
         "Cinnamon is a brown spice with a warm smell and taste. Bakers use it to make sweet food smell cozy."),
    ],
    "counting": [
        ("Why is counting a helpful bakery job for a child?",
         "Counting keeps hands busy and helps a baker know how many things are ready. It is a safe way to help without touching hot ovens."),
    ],
    "helping": [
        ("How can a child help in a bakery safely?",
         "A child can do cool, simple jobs like lining tins or brushing glaze on things that are not hot. Safe helping means staying away from the oven unless a grown-up says it is time."),
    ],
}
KNOWLEDGE_ORDER = [
    "baking", "patience", "steam", "surprise", "berries", "honey",
    "cinnamon", "counting", "helping"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pastry = f["pastry_cfg"]
    surprise = f["surprise_cfg"]
    child = f["child"]
    baker = f["baker"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            f'Write a Tall Tale for a 3-to-5-year-old that includes the words "crave" and "baker", where a child grows curious about a surprise inside {pastry.phrase}.',
            f"Tell a bakery story where {child.label} craves {pastry.giant_phrase}, peeks too soon, and {baker.label} kindly saves the bake.",
            f"Write a gentle Tall Tale about curiosity, patience, and a hidden {surprise.label} inside a giant pastry.",
        ]
    return [
        f'Write a Tall Tale for a 3-to-5-year-old that includes the words "crave" and "baker", where a child peeks too soon at a baking surprise.',
        f"Tell a warm cautionary bakery story where {child.label}'s curiosity makes a giant {pastry.label} fall before it is ready.",
        f"Write a simple story about how surprise and curiosity can pull against patience in a bakery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    baker = f["baker"]
    pastry = f["pastry_cfg"]
    surprise = f["surprise_cfg"]
    remedy = f["remedy"]
    task = f["task"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child with a mighty crave for bakery wonders, and {baker.label}, the baker who was making the treat. The story follows their day in the bakery from wanting to waiting."
        ),
        (
            f"What did {child.label} want?",
            f"{child.label} wanted {pastry.giant_phrase}. The wish felt huge because the bakery smelled so rich and the promise of a hidden surprise made the treat seem even grander."
        ),
        (
            "What was the surprise?",
            f"The baker had hidden {surprise.phrase} inside the pastry. That secret filling is what made curiosity tug so hard."
        ),
        (
            f"Why did {baker.label} give {child.label} another job?",
            f"{baker.label} asked {child.label} to {task.text} so those small safe jobs could keep little hands busy. The job was meant to help {child.pronoun('object')} wait instead of touching the oven."
        ),
        (
            f"What went wrong when {child.label} peeked?",
            (
                f"{child.label} opened the oven too soon. "
                + (
                    f"The {pastry.label} slumped because that kind of pastry needs steady heat and does not like a sudden gulp of cool air."
                    if f.get("predicted_slump")
                    else f"The peek let out heat and steam, even though this pastry was sturdy enough to keep going."
                )
            ),
        ),
    ]
    if outcome == "saved":
        qa.append((
            f"How did {baker.label} fix the problem?",
            f"{baker.label} {remedy.qa_text}. That careful remedy gave the pastry another chance, and the surprise inside still reached the table."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily with the giant pastry opened at last and the hidden {surprise.label} shining from the middle. The ending shows that patience mattered, because the child learned to let wonder finish growing before grabbing at it."
        ))
    else:
        qa.append((
            f"Could {baker.label} save the pastry completely?",
            f"No. {baker.label} tried, but the pastry stayed lower and smaller than it should have been. The child still got something sweet, yet the lost height showed what the early peek had changed."
        ))
        qa.append((
            "What did the child learn?",
            f"{child.label} learned that surprise does not get better when you rush it. Curiosity is natural, but patient hands give delicate things room to become what they were meant to be."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["pastry_cfg"].tags) | set(world.facts["surprise_cfg"].tags) | set(world.facts["task"].tags)
    if world.facts["outcome"] == "saved":
        tags |= set(world.facts["remedy"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        flags = [n for n, on in (("can_bake", ent.can_bake), ("can_help", ent.can_help), ("openable", ent.openable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        pastry="moon_bun",
        surprise="berry_comet",
        remedy="steam_pan",
        task="count_raisin",
        child_name="Mira",
        child_type="girl",
        baker_name="Old Rowan",
        baker_type="man",
        peek_count=1,
    ),
    StoryParams(
        pastry="star_pocket",
        surprise="honey_sun",
        remedy="warm_cloth",
        task="line_tins",
        child_name="Finn",
        child_type="boy",
        baker_name="Marta",
        baker_type="woman",
        peek_count=1,
    ),
    StoryParams(
        pastry="thunder_loaf",
        surprise="cinnamon_map",
        remedy="warm_cloth",
        task="brush_glaze",
        child_name="Ruby",
        child_type="girl",
        baker_name="Mr. Bell",
        baker_type="man",
        peek_count=1,
    ),
    StoryParams(
        pastry="star_pocket",
        surprise="berry_comet",
        remedy="warm_cloth",
        task="count_raisin",
        child_name="Theo",
        child_type="boy",
        baker_name="Juniper",
        baker_type="woman",
        peek_count=2,
    ),
]


def explain_rejection(pastry: Pastry) -> str:
    return (
        f"(No story: {pastry.phrase.capitalize()} does not honestly hide a surprise middle, "
        f"so there is no fair reveal for curiosity to tug against. Pick a pastry like "
        f"moon_bun, thunder_loaf, or star_pocket.)"
    )


def explain_remedy(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    pastry = PASTRIES[params.pastry]
    remedy = REMEDIES[params.remedy]
    return "saved" if is_saved(remedy, pastry, params.peek_count) else "slumped"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% compatibility: only pastries that can honestly hide a surprise make sense here
valid(P, S) :- pastry(P), surprise(S), hideable(P).

% sensible remedy gate
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.

% outcome model
severity(Peeks + 2) :- chosen_pastry(P), delicate(P), peek_count(Peeks).
severity(Peeks)     :- chosen_pastry(P), not delicate(P), peek_count(Peeks).
saved               :- chosen_pastry(P), not delicate(P).
saved               :- chosen_pastry(P), delicate(P), chosen_remedy(R), power(R, Pow), peek_count(Peeks), Pow >= Peeks + 2.

outcome(saved)   :- saved.
outcome(slumped) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pastry_id, pastry in PASTRIES.items():
        lines.append(asp.fact("pastry", pastry_id))
        if pastry.hideable:
            lines.append(asp.fact("hideable", pastry_id))
        if pastry.delicate:
            lines.append(asp.fact("delicate", pastry_id))
    for surprise_id in SURPRISES:
        lines.append(asp.fact("surprise", surprise_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_pastry", params.pastry),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("peek_count", params.peek_count),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        cset = set(asp_valid_combos())
        pset = set(valid_combos())
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    sensible_py = {r.id for r in sensible_remedies()}
    sensible_asp = set(asp_sensible())
    if sensible_py == sensible_asp:
        print(f"OK: sensible remedies match ({sorted(sensible_py)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(sensible_asp)} python={sorted(sensible_py)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    # smoke test ordinary generation/emit path
    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"VERIFY smoke test failed: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale bakery storyworld: a child craves a giant pastry, curiosity leads to a peek, and a baker answers with skill and patience."
    )
    ap.add_argument("--pastry", choices=PASTRIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--baker-name")
    ap.add_argument("--baker-type", choices=["woman", "man"])
    ap.add_argument("--peek-count", type=int, choices=[1, 2], help="how many times the child peeks")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible pastry/surprise pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pastry and not PASTRIES[args.pastry].hideable:
        raise StoryError(explain_rejection(PASTRIES[args.pastry]))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.pastry is None or combo[0] == args.pastry)
        and (args.surprise is None or combo[1] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pastry_id, surprise_id = rng.choice(sorted(combos))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    task_id = args.task or rng.choice(sorted(TASKS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    baker_type = args.baker_type or rng.choice(["woman", "man"])
    baker_name = args.baker_name or rng.choice(BAKER_NAMES)
    peek_count = args.peek_count if args.peek_count is not None else rng.choice([1, 1, 2])

    return StoryParams(
        pastry=pastry_id,
        surprise=surprise_id,
        remedy=remedy_id,
        task=task_id,
        child_name=child_name,
        child_type=child_type,
        baker_name=baker_name,
        baker_type=baker_type,
        peek_count=peek_count,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        pastry = PASTRIES[params.pastry]
        surprise = SURPRISES[params.surprise]
        remedy = REMEDIES[params.remedy]
        task = TASKS[params.task]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not pastry.hideable:
        raise StoryError(explain_rejection(pastry))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))

    world = tell(
        pastry=pastry,
        surprise=surprise,
        remedy=remedy,
        task=task,
        child_name=params.child_name,
        child_type=params.child_type,
        baker_name=params.baker_name,
        baker_type=params.baker_type,
        peek_count=params.peek_count,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", world.facts["child"].label).replace("baker", world.facts["baker"].label),
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (pastry, surprise) combos:\n")
        for pastry_id, surprise_id in combos:
            print(f"  {pastry_id:12} {surprise_id}")
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
            header = f"### {p.child_name}: {p.pastry} with {p.surprise} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
