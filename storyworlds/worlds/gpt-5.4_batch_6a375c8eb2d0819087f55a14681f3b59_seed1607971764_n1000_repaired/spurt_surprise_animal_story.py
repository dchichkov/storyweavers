#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py
=========================================================

A standalone story world for a small animal tale about making a surprise banner,
a sudden berry-juice spurt, and a clever fix.

The world is intentionally narrow: two little woodland animals hide in a garden
nook to make a surprise for a friend. They squeeze berries for paint through a
thin reed. If the reed clogs and the planner squeezes too hard, a bright spurt
splashes the banner. A sensible repair can still save the surprise; a weak one
cannot. The story is driven by simulated state, not by slot-filling.

Run it
------
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py --berry raspberry --banner cloth --fix petal_stamp
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py --fix lick_clean
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py --trace --seed 11
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py --json
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/spurt_surprise_animal_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return table[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Berry:
    id: str
    label: str
    color: str
    stain: int
    pressure: int
    source: str
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
class Banner:
    id: str
    label: str
    phrase: str
    material: str
    min_stain: int
    surface: str
    patchable: bool
    washable: bool
    dry_place: str
    final_image: str
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    mode: str
    works_on: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
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


def _r_spurt_marks_banner(world: World) -> list[str]:
    banner = world.get("banner")
    planner = world.get("planner")
    helper = world.get("helper")
    if banner.meters["splashed"] < THRESHOLD:
        return []
    sig = ("mark_banner", "banner")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    banner.meters["blotched"] += 1
    planner.memes["worry"] += 1
    helper.memes["worry"] += 1
    return ["__blotch__"]


def _r_fix_clears_worry(world: World) -> list[str]:
    banner = world.get("banner")
    planner = world.get("planner")
    helper = world.get("helper")
    if banner.meters["pretty"] < THRESHOLD:
        return []
    sig = ("clear_worry", "banner")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    planner.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    planner.memes["relief"] += 1
    helper.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spurt_marks_banner", tag="physical", apply=_r_spurt_marks_banner),
    Rule(name="fix_clears_worry", tag="emotional", apply=_r_fix_clears_worry),
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


def paint_shows(berry: Berry, banner: Banner) -> bool:
    return berry.stain >= banner.min_stain


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def mess_size(berry: Berry, delay: int) -> int:
    return berry.pressure + delay


def fix_works(fix: Fix, banner: Banner, berry: Berry, delay: int) -> bool:
    return banner.material in fix.works_on and fix.power >= mess_size(berry, delay)


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). A sensible animal story should use "
        f"a better repair. Try: {better}.)"
    )


def explain_combo_rejection(berry: Berry, banner: Banner) -> str:
    return (
        f"(No story: {berry.label} juice would not show clearly on the {banner.label}, "
        f"so there is no honest banner-making problem to start from. Pick a berry "
        f"with a stronger stain or a banner that can hold the color.)"
    )


def predict_spurt(world: World, berry: Berry) -> dict:
    sim = world.copy()
    banner = sim.get("banner")
    banner.meters["splashed"] += 1
    propagate(sim, narrate=False)
    return {
        "blotched": banner.meters["blotched"] >= THRESHOLD,
        "planner_worry": sim.get("planner").memes["worry"],
    }


def introduce(world: World, planner: Entity, helper: Entity, guest: Entity, banner: Banner) -> None:
    planner.memes["excitement"] += 1
    helper.memes["excitement"] += 1
    world.say(
        f"In a sunny garden corner, {planner.id} the {planner.type} and "
        f"{helper.id} the {helper.type} crouched behind a clump of mint. "
        f"They were making {banner.phrase} for {guest.id} the {guest.type}."
    )
    world.say(
        f'"It has to stay hidden," whispered {planner.id}. '
        f'"It is a surprise for when {guest.id} comes down the path."'
    )


def prepare_paint(world: World, planner: Entity, helper: Entity, berry: Berry, banner: Banner) -> None:
    world.say(
        f"Between them lay a little pile of {berry.label}s from {berry.source}, "
        f"a thin reed for painting, and {banner.phrase} spread flat on the grass."
    )
    world.say(
        f'{helper.id} touched the berries and smiled. "The {berry.color} juice will look lovely."'
    )


def warn(world: World, planner: Entity, helper: Entity, berry: Berry) -> None:
    pred = predict_spurt(world, berry)
    world.facts["predicted_blotch"] = pred["blotched"]
    helper.memes["care"] += 1
    extra = " It might jump out in a spurt." if pred["blotched"] else ""
    world.say(
        f'{helper.id} watched the narrow reed and said, '
        f'"Squeeze gently, {planner.id}. If the berry skins clog the tip, the juice may pop out all at once."{extra}'
    )


def defy(world: World, planner: Entity) -> None:
    planner.memes["hurry"] += 1
    world.say(
        f"But {planner.id} was in a hurry to finish before the guest arrived. "
        f"{planner.pronoun().capitalize()} pressed the berries a little harder."
    )


def spurt(world: World, planner: Entity, helper: Entity, berry: Berry, banner_ent: Entity, banner: Banner) -> None:
    banner_ent.meters["splashed"] += 1
    banner_ent.meters["wet"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once, the blocked reed gave a tiny cough. Then a bright {berry.color} spurt "
        f"shot across the air and splashed onto the {banner.label}."
    )
    if banner_ent.meters["blotched"] >= THRESHOLD:
        world.say(
            f"A round blot spread over the neat middle, and both little makers froze."
        )
    planner.memes["guilt"] += 1
    helper.memes["alarm"] += 1


def react(world: World, planner: Entity, helper: Entity) -> None:
    world.say(
        f'"Oh no," breathed {planner.id}. {helper.id} put one paw over {helper.pronoun("possessive")} mouth, '
        f"and for a moment the surprise felt ruined."
    )


def repair_success(world: World, planner: Entity, helper: Entity, guest: Entity,
                   fix: Fix, banner_ent: Entity, banner: Banner, berry: Berry) -> None:
    banner_ent.meters["blotched"] = 0.0
    banner_ent.meters["pretty"] += 1
    banner_ent.meters["saved"] += 1
    propagate(world, narrate=False)
    body = fix.text.format(banner=banner.label, color=berry.color)
    world.say(body)
    world.say(
        f"Soon the accident no longer looked like a mistake. It looked like the best part of the banner."
    )
    world.para()
    guest.memes["surprise"] += 1
    planner.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Just then, {guest.id} came around the bend, slow and cheerful, and stopped with a blink."
    )
    world.say(
        f'"Surprise!" cried {planner.id} and {helper.id}. {guest.id} stared at the banner and smiled so wide that '
        f"{guest.pronoun('possessive')} whiskers seemed to shine."
    )
    world.say(
        f"{banner.final_image} The happy accident had turned into a gift all its own."
    )


def repair_fail(world: World, planner: Entity, helper: Entity, guest: Entity,
                fix: Fix, banner_ent: Entity, banner: Banner, berry: Berry) -> None:
    banner_ent.meters["messy"] += 1
    planner.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    body = fix.fail.format(banner=banner.label, color=berry.color)
    world.say(body)
    world.say(
        f"The stain stayed dark and sticky on the {banner.label}, and there was no more time to begin again."
    )
    world.para()
    guest.memes["surprise"] += 1
    planner.memes["honesty"] += 1
    helper.memes["honesty"] += 1
    world.say(
        f"When {guest.id} came around the bend, {planner.id}'s ears drooped. "
        f'"It was meant to be a pretty surprise," {planner.pronoun()} admitted.'
    )
    world.say(
        f"But {guest.id} looked at the smeared banner, then at the berry-stained paws, and gave them both a gentle hug."
    )
    world.say(
        f'"It is still a surprise," said {guest.id}. "I can see how hard you tried." '
        f"After that, the three friends hung the crooked banner anyway, and the garden felt warm with kindness."
    )


def tell(berry: Berry, banner: Banner, fix: Fix,
         planner_name: str = "Pip", planner_species: str = "mouse",
         helper_name: str = "Mimi", helper_species: str = "rabbit",
         guest_name: str = "Moss", guest_species: str = "hedgehog",
         delay: int = 0) -> World:
    world = World()
    planner = world.add(Entity(id=planner_name, kind="character", type=planner_species, role="planner"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_species, role="helper"))
    guest = world.add(Entity(id=guest_name, kind="character", type=guest_species, role="guest"))
    banner_ent = world.add(Entity(id="banner", type="banner", label=banner.label))
    bowl = world.add(Entity(id="berries", type="berries", label=berry.label))
    reed = world.add(Entity(id="reed", type="tool", label="reed"))

    world.facts.update(
        berry=berry,
        banner_cfg=banner,
        fix=fix,
        planner=planner,
        helper=helper,
        guest=guest,
        bowl=bowl,
        reed=reed,
        delay=delay,
    )

    introduce(world, planner, helper, guest, banner)
    prepare_paint(world, planner, helper, berry, banner)

    world.para()
    warn(world, planner, helper, berry)
    defy(world, planner)

    world.para()
    spurt(world, planner, helper, berry, banner_ent, banner)
    react(world, planner, helper)

    saved = fix_works(fix, banner, berry, delay)
    world.para()
    if saved:
        repair_success(world, planner, helper, guest, fix, banner_ent, banner, berry)
        outcome = "saved"
    else:
        repair_fail(world, planner, helper, guest, fix, banner_ent, banner, berry)
        outcome = "messy"

    world.facts.update(
        banner=banner_ent,
        outcome=outcome,
        saved=saved,
        spurted=banner_ent.meters["splashed"] >= THRESHOLD,
        visible=paint_shows(berry, banner),
        mess_size=mess_size(berry, delay),
    )
    return world


THEMES = {
    "mouse_rabbit_hedgehog": ("Pip", "mouse", "Mimi", "rabbit", "Moss", "hedgehog"),
    "squirrel_duck_badger": ("Nip", "squirrel", "Dabble", "duck", "Bram", "badger"),
    "vole_fawn_tortoise": ("Tavi", "vole", "Fern", "fawn", "Pebble", "tortoise"),
}

BERRIES = {
    "blueberry": Berry(
        id="blueberry",
        label="blueberry",
        color="blue",
        stain=2,
        pressure=1,
        source="the shady patch under the plum tree",
        tags={"berries", "blue"},
    ),
    "raspberry": Berry(
        id="raspberry",
        label="raspberry",
        color="red",
        stain=3,
        pressure=2,
        source="the brambly hedge",
        tags={"berries", "red"},
    ),
    "blackberry": Berry(
        id="blackberry",
        label="blackberry",
        color="purple",
        stain=3,
        pressure=2,
        source="the old fence",
        tags={"berries", "purple"},
    ),
    "gooseberry": Berry(
        id="gooseberry",
        label="gooseberry",
        color="pale green",
        stain=1,
        pressure=1,
        source="the low bush by the stones",
        tags={"berries", "green"},
    ),
}

BANNERS = {
    "cloth": Banner(
        id="cloth",
        label="cloth banner",
        phrase="a small white cloth banner",
        material="cloth",
        min_stain=2,
        surface="soft",
        patchable=True,
        washable=True,
        dry_place="the warm stone by the thyme",
        final_image="The cloth banner fluttered between two twigs, with petal stars dancing around the words",
        tags={"cloth", "banner"},
    ),
    "leaf": Banner(
        id="leaf",
        label="leaf banner",
        phrase="a chain of broad dock leaves tied with grass",
        material="leaf",
        min_stain=2,
        surface="waxy",
        patchable=True,
        washable=False,
        dry_place="the mossy log",
        final_image="The leaf banner hung over the path, each patched leaf shining like a tiny green flag",
        tags={"leaf", "banner"},
    ),
    "bark": Banner(
        id="bark",
        label="bark card",
        phrase="a smooth piece of birch bark trimmed into a little card",
        material="bark",
        min_stain=1,
        surface="smooth",
        patchable=False,
        washable=True,
        dry_place="the flat root in the sun",
        final_image="The bark card rested against a mushroom, with the berry mark turned into a bright round berry sun",
        tags={"bark", "banner"},
    ),
}

FIXES = {
    "petal_stamp": Fix(
        id="petal_stamp",
        label="petal stamp",
        sense=3,
        power=3,
        mode="decorate",
        works_on={"cloth", "bark"},
        text="Mimi did not scrub at all. Instead, they pressed tiny daisy petals around the {color} blot and turned it into a flower burst on the {banner}.",
        fail="They tried to cover the stain with petals, but the wet {color} juice soaked through and left the {banner} smudgy underneath.",
        qa_text="They turned the blot into a flower burst with daisy petals",
        tags={"petals", "decorate"},
    ),
    "leaf_patch": Fix(
        id="leaf_patch",
        label="leaf patch",
        sense=3,
        power=3,
        mode="patch",
        works_on={"leaf", "cloth"},
        text="Pip fetched a shiny spare leaf, and together they laid it over the splash, tying it neatly so the {banner} looked as if it had always meant to wear a green heart.",
        fail="They tied on a little patch, but the sticky {color} juice spread beyond it and the {banner} still looked messy.",
        qa_text="They covered the splash with a neat leaf patch",
        tags={"leaf_patch", "patch"},
    ),
    "brook_rinse": Fix(
        id="brook_rinse",
        label="brook rinse",
        sense=2,
        power=2,
        mode="wash",
        works_on={"cloth", "bark"},
        text="They hurried to the brook, rinsed the worst of the stain away, and laid the {banner} out to dry before adding the words again in smaller careful strokes.",
        fail="They rushed to the brook, but the {color} stain had already sunk in too deeply, and the {banner} came back damp and blotchy.",
        qa_text="They rinsed the banner in the brook and wrote on it again",
        tags={"brook", "wash"},
    ),
    "lick_clean": Fix(
        id="lick_clean",
        label="lick it clean",
        sense=1,
        power=1,
        mode="badidea",
        works_on={"cloth", "leaf", "bark"},
        text="",
        fail="They tried licking the stain clean, but that only smeared the {color} juice farther across the {banner}.",
        qa_text="They tried licking the stain clean",
        tags={"bad_idea"},
    ),
}

ANIMAL_NAMES = {
    "mouse": ["Pip", "Nib", "Tuppy", "Mote"],
    "rabbit": ["Mimi", "Hopper", "Clover", "Dot"],
    "hedgehog": ["Moss", "Bramble", "Pine", "Prickle"],
    "squirrel": ["Nip", "Hazel", "Skip", "Tansy"],
    "duck": ["Dabble", "Puddle", "Ripple", "Wiggle"],
    "badger": ["Bram", "Stripe", "Sett", "Mallow"],
    "vole": ["Tavi", "Nibble", "Mallow", "Poppy"],
    "fawn": ["Fern", "Bracken", "Willow", "Lilt"],
    "tortoise": ["Pebble", "Mosscap", "Shellow", "Slowly"],
}

KNOWLEDGE = {
    "berries": [
        (
            "Why can berries be used like paint?",
            "Many berries have strong juice inside them, and that juice can leave color on cloth, bark, or paper. Dark berries stain best because their color shows clearly.",
        )
    ],
    "reed": [
        (
            "Why might juice come out in a spurt from a reed?",
            "If the tip of a hollow reed gets clogged, pressure builds up behind the juice. When the clog shifts, the juice can jump out all at once in a spurt.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something kind or exciting that someone does without telling another person first. It works best when it is hidden until the right moment.",
        )
    ],
    "cloth": [
        (
            "Why can a cloth banner be washed?",
            "Cloth can hold water without breaking apart, so a small stain can sometimes be rinsed and dried. You still need to act quickly before the color sinks in.",
        )
    ],
    "leaf": [
        (
            "Why is a leaf banner hard to wash?",
            "A leaf can tear or curl when it gets too wet. That is why patching a leaf is often gentler than scrubbing it.",
        )
    ],
    "bark": [
        (
            "Why does birch bark make a good little sign?",
            "Birch bark is light, smooth, and stiff enough to hold its shape. You can draw on it carefully without it flopping over.",
        )
    ],
    "petals": [
        (
            "How can petals help fix a picture?",
            "Petals can turn a mistake into part of the design. If a blot looks like a flower center, petals around it can make it look planned.",
        )
    ],
    "patch": [
        (
            "What does a patch do?",
            "A patch covers a torn or messy spot with another piece of material. It is useful when washing would make the original surface worse.",
        )
    ],
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream of moving water. Animals can use its cool water to rinse things gently.",
        )
    ],
}
KNOWLEDGE_ORDER = ["surprise", "berries", "reed", "cloth", "leaf", "bark", "petals", "patch", "brook"]


@dataclass
class StoryParams:
    theme: str
    berry: str
    banner: str
    fix: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for berry_id, berry in BERRIES.items():
        for banner_id, banner in BANNERS.items():
            if not paint_shows(berry, banner):
                continue
            for fix_id, fix in FIXES.items():
                if fix.sense < SENSE_MIN:
                    continue
                if banner.material in fix.works_on:
                    combos.append((berry_id, banner_id, fix_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    planner = f["planner"]
    helper = f["helper"]
    guest = f["guest"]
    berry = f["berry"]
    banner = f["banner_cfg"]
    if f["outcome"] == "saved":
        return [
            f'Write a short animal story for a 3-to-5-year-old that includes the word "spurt" and ends with a happy surprise.',
            f"Tell a gentle woodland story where {planner.id} the {planner.type} and {helper.id} the {helper.type} make a secret banner for {guest.id} the {guest.type}, but a berry spurt splashes it and they cleverly save it.",
            f"Write a child-friendly animal story about a surprise present going wrong for one moment and then becoming even prettier because of the fix.",
        ]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the word "spurt" and a surprise that nearly goes wrong.',
        f"Tell a woodland story where {planner.id} the {planner.type} tries to make a berry-painted banner for {guest.id} the {guest.type}, but a sudden spurt leaves a messy blot just before the surprise.",
        f"Write a simple animal story where friends make a kind surprise, have a little accident, and learn that the love behind the gift still matters.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    planner = f["planner"]
    helper = f["helper"]
    guest = f["guest"]
    berry = f["berry"]
    banner = f["banner_cfg"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {planner.id} the {planner.type}, {helper.id} the {helper.type}, and their friend {guest.id} the {guest.type}. The two little makers were trying to prepare a surprise for their friend.",
        ),
        (
            f"What were {planner.id} and {helper.id} making?",
            f"They were making {banner.phrase} for {guest.id}. They wanted to hide it until the right moment so the gift would feel like a real surprise.",
        ),
        (
            f"Why did the juice come out in a spurt?",
            f"The berry juice was being pushed through a narrow reed, and the tip got blocked. When {planner.id} squeezed harder, the pressure made the juice jump out all at once.",
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                "How did they save the surprise?",
                f"{fix.qa_text}. That worked because it matched the {banner.material} banner and covered the accident before {guest.id} arrived.",
            )
        )
        qa.append(
            (
                f"How did {guest.id} feel at the end?",
                f"{guest.id} felt delighted and surprised when the banner was shown at last. The ending proves the problem was solved because the banner looked beautiful instead of ruined.",
            )
        )
    else:
        qa.append(
            (
                "Did the surprise still matter after the mistake?",
                f"Yes. The banner stayed messy, but {guest.id} could still see the care behind it and hugged the others. The surprise changed from a perfect-looking gift into a loving one.",
            )
        )
        qa.append(
            (
                f"Why could they not fully fix the {banner.label} in time?",
                f"The chosen repair was too weak for such a big juicy splash on that kind of material. By the time they tried, the stain had already spread and there was not enough time to begin again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"surprise", "berries"}
    tags.add(f["banner_cfg"].material)
    tags.add("reed")
    if f["fix"].id == "petal_stamp":
        tags.add("petals")
    if f["fix"].id == "leaf_patch":
        tags.add("patch")
    if f["fix"].id == "brook_rinse":
        tags.add("brook")
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="mouse_rabbit_hedgehog",
        berry="raspberry",
        banner="cloth",
        fix="petal_stamp",
        delay=0,
    ),
    StoryParams(
        theme="squirrel_duck_badger",
        berry="blackberry",
        banner="leaf",
        fix="leaf_patch",
        delay=0,
    ),
    StoryParams(
        theme="vole_fawn_tortoise",
        berry="blueberry",
        banner="bark",
        fix="brook_rinse",
        delay=0,
    ),
    StoryParams(
        theme="mouse_rabbit_hedgehog",
        berry="raspberry",
        banner="bark",
        fix="brook_rinse",
        delay=1,
    ),
    StoryParams(
        theme="squirrel_duck_badger",
        berry="blackberry",
        banner="cloth",
        fix="brook_rinse",
        delay=1,
    ),
]


ASP_RULES = r"""
visible(B, Ba) :- berry(B), banner(Ba), stain(B, S), min_stain(Ba, M), S >= M.
sensible(F)    :- fix(F), sense(F, S), sense_min(M), S >= M.
works(F, Ba)   :- fix(F), banner(Ba), material(Ba, Mat), fix_works_on(F, Mat).
valid(B, Ba, F) :- visible(B, Ba), sensible(F), works(F, Ba).

mess_size(V) :- chosen_berry(B), pressure(B, P), delay(D), V = P + D.
saved :- chosen_banner(Ba), chosen_fix(F), works(F, Ba),
         fix_power(F, Pow), mess_size(V), Pow >= V.

outcome(saved) :- saved.
outcome(messy) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for berry_id, berry in BERRIES.items():
        lines.append(asp.fact("berry", berry_id))
        lines.append(asp.fact("stain", berry_id, berry.stain))
        lines.append(asp.fact("pressure", berry_id, berry.pressure))
    for banner_id, banner in BANNERS.items():
        lines.append(asp.fact("banner", banner_id))
        lines.append(asp.fact("min_stain", banner_id, banner.min_stain))
        lines.append(asp.fact("material", banner_id, banner.material))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("fix_power", fix_id, fix.power))
        for mat in sorted(fix.works_on):
            lines.append(asp.fact("fix_works_on", fix_id, mat))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_berry", params.berry),
        asp.fact("chosen_banner", params.banner),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "saved" if fix_works(FIXES[params.fix], BANNERS[params.banner], BERRIES[params.berry], params.delay) else "messy"


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

    cases = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: little animals, a surprise banner, and a berry spurt."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--berry", choices=BERRIES)
    ap.add_argument("--banner", choices=BANNERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how close the guest is when the accident happens")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(args.fix))

    if args.berry and args.banner:
        berry = BERRIES[args.berry]
        banner = BANNERS[args.banner]
        if not paint_shows(berry, banner):
            raise StoryError(explain_combo_rejection(berry, banner))

    combos = [
        combo for combo in valid_combos()
        if (args.berry is None or combo[0] == args.berry)
        and (args.banner is None or combo[1] == args.banner)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    berry_id, banner_id, fix_id = rng.choice(sorted(combos))
    theme = args.theme or rng.choice(sorted(THEMES))
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        theme=theme,
        berry=berry_id,
        banner=banner_id,
        fix=fix_id,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.berry not in BERRIES:
        raise StoryError(f"(Unknown berry: {params.berry})")
    if params.banner not in BANNERS:
        raise StoryError(f"(Unknown banner: {params.banner})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if (params.berry, params.banner, params.fix) not in set(valid_combos()):
        berry = BERRIES[params.berry]
        banner = BANNERS[params.banner]
        fix = FIXES[params.fix]
        if fix.sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(params.fix))
        raise StoryError(explain_combo_rejection(berry, banner))

    planner_name, planner_species, helper_name, helper_species, guest_name, guest_species = THEMES[params.theme]
    world = tell(
        berry=BERRIES[params.berry],
        banner=BANNERS[params.banner],
        fix=FIXES[params.fix],
        planner_name=planner_name,
        planner_species=planner_species,
        helper_name=helper_name,
        helper_species=helper_species,
        guest_name=guest_name,
        guest_species=guest_species,
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
        print(f"{len(combos)} valid (berry, banner, fix) combos:\n")
        for berry, banner, fix in combos:
            print(f"  {berry:10} {banner:8} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.theme}: {p.berry} on {p.banner} with {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
