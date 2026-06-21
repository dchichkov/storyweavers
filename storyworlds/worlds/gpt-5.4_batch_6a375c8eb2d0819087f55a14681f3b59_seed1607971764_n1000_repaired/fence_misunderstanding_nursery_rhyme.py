#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fence_misunderstanding_nursery_rhyme.py
=================================================================

A standalone story world about a child who hears "mind the fence" as
"mend the fence" and tries to help the wrong way. The world keeps a tiny,
nursery-rhyme-like cadence while still being a simulation: a loose fence,
small animals, a misunderstanding, a warning, a turn, and a clear ending
image that shows what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/fence_misunderstanding_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/fence_misunderstanding_nursery_rhyme.py --animal chicks --flaw loose_rail --patch ribbon
    python storyworlds/worlds/gpt-5.4/fence_misunderstanding_nursery_rhyme.py --flaw wide_gap
    python storyworlds/worlds/gpt-5.4/fence_misunderstanding_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/fence_misunderstanding_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fence_misunderstanding_nursery_rhyme.py --verify
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
LISTEN_SCORE = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Animal:
    id: str
    label: str
    group: str
    sound: str
    motion: str
    pressure: int
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
class Flaw:
    id: str
    label: str
    line: str
    danger: str
    proper_fix: str
    repair_sound: str
    strain: int
    tieable: bool = True
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
    strength: int
    sense: int
    color: str
    plural: bool = False
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
class StoryParams:
    animal: str
    flaw: str
    patch: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    child_a_age: int = 5
    child_b_age: int = 6
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"mishearer", "helper"}]

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


def _r_wobble(world: World) -> list[str]:
    fence = world.get("fence")
    if fence.meters["loose"] < THRESHOLD:
        return []
    sig = ("wobble", "fence")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    yard = world.get("yard")
    yard.meters["risk"] += 1
    for child in world.children():
        child.memes["worry"] += 1
    return []


def _r_hold_or_fail(world: World) -> list[str]:
    fence = world.get("fence")
    patch = world.get("patch")
    animal = world.get("animal")
    if patch.meters["applied"] < THRESHOLD or fence.meters["loose"] < THRESHOLD:
        return []
    sig = ("hold_or_fail", patch.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    strain = fence.attrs["strain"]
    pressure = animal.attrs["pressure"]
    strength = patch.attrs["strength"]
    if strength >= strain + pressure:
        fence.meters["held"] += 1
        return []
    animal.meters["escaped"] += 1
    yard = world.get("yard")
    yard.meters["chaos"] += 1
    for child in world.children():
        child.memes["fear"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="hold_or_fail", tag="physical", apply=_r_hold_or_fail),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


ANIMALS = {
    "chicks": Animal(
        id="chicks",
        label="chicks",
        group="little yellow chicks",
        sound="peep-peep",
        motion="bobbing like drops of sun",
        pressure=1,
        tags={"chicks", "farm_animals"},
    ),
    "ducklings": Animal(
        id="ducklings",
        label="ducklings",
        group="round ducklings",
        sound="peep-quack",
        motion="waddling in a neat soft line",
        pressure=2,
        tags={"ducklings", "farm_animals"},
    ),
    "lamb": Animal(
        id="lamb",
        label="lamb",
        group="a woolly lamb",
        sound="baa",
        motion="bouncing on springy knees",
        pressure=2,
        tags={"lamb", "farm_animals"},
    ),
    "goat": Animal(
        id="goat",
        label="goat",
        group="a nimble little goat",
        sound="maa",
        motion="dancing on quick bright hooves",
        pressure=3,
        tags={"goat", "farm_animals"},
    ),
}

FLAWS = {
    "loose_rail": Flaw(
        id="loose_rail",
        label="loose rail",
        line="one rail in the garden fence rocked when the wind gave it a nudge",
        danger="a loose rail could leave a wriggle-room opening",
        proper_fix="set the rail straight and tapped it firm with a small hammer",
        repair_sound="tap-tap-tap",
        strain=1,
        tieable=True,
        tags={"fence", "repair"},
    ),
    "sleepy_latch": Flaw(
        id="sleepy_latch",
        label="sleepy latch",
        line="the little gate latch on the fence would not stay kissed shut",
        danger="a sleepy latch could let the gate swing wide",
        proper_fix="lifted the latch, set it right, and fastened it with a screw-driver",
        repair_sound="turn-turn-turn",
        strain=2,
        tieable=True,
        tags={"fence", "gate"},
    ),
    "wide_gap": Flaw(
        id="wide_gap",
        label="wide gap",
        line="two boards in the fence stood too far apart, making a wide gap",
        danger="a wide gap needed a real board, not a little tie",
        proper_fix="held a fresh board in place and fixed it snug against the posts",
        repair_sound="tap-clink-tap",
        strain=4,
        tieable=False,
        tags={"fence", "repair"},
    ),
}

PATCHES = {
    "ribbon": Patch(
        id="ribbon",
        label="ribbon",
        phrase="a red ribbon from the play basket",
        strength=1,
        sense=2,
        color="red",
        plural=False,
        tags={"ribbon", "soft_things"},
    ),
    "scarf": Patch(
        id="scarf",
        label="scarf",
        phrase="a soft blue scarf from the peg",
        strength=2,
        sense=3,
        color="blue",
        plural=False,
        tags={"scarf", "soft_things"},
    ),
    "skipping_rope": Patch(
        id="skipping_rope",
        label="skipping rope",
        phrase="a skipping rope striped in green and white",
        strength=3,
        sense=3,
        color="green-and-white",
        plural=False,
        tags={"rope", "playthings"},
    ),
    "paper_chain": Patch(
        id="paper_chain",
        label="paper chain",
        phrase="a paper chain snipped for a game",
        strength=0,
        sense=1,
        color="many-colored",
        plural=False,
        tags={"paper", "playthings"},
    ),
}

GIRL_NAMES = ["May", "Lily", "Molly", "Rose", "Nell", "Poppy", "Daisy", "Tess"]
BOY_NAMES = ["Tom", "Ben", "Ned", "Finn", "Jack", "Eli", "Sam", "Theo"]
TRAITS = ["careful", "steady", "thoughtful", "gentle", "curious", "bold"]


def valid_patch_for_flaw(flaw: Flaw, patch: Patch) -> bool:
    return flaw.tieable and patch.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id in ANIMALS:
        for flaw_id, flaw in FLAWS.items():
            for patch_id, patch in PATCHES.items():
                if valid_patch_for_flaw(flaw, patch):
                    combos.append((animal_id, flaw_id, patch_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_clarify(relation: str, child_a_age: int, child_b_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and child_b_age > child_a_age
    score = initial_caution(trait) + (2.0 if helper_older else 0.0)
    return helper_older and score >= LISTEN_SCORE


def outcome_of(params: StoryParams) -> str:
    if would_clarify(params.relation, params.child_a_age, params.child_b_age, params.trait):
        return "clarified"
    flaw = FLAWS[params.flaw]
    patch = PATCHES[params.patch]
    animal = ANIMALS[params.animal]
    return "held" if patch.strength >= flaw.strain + animal.pressure else "escaped"


def explain_rejection(flaw: Flaw, patch: Patch) -> str:
    if not flaw.tieable:
        return (
            f"(No story: {flaw.label} cannot honestly be 'mended' with {patch.label}. "
            f"It needs a real board or tool, so the misunderstanding would not make a sensible little plot.)"
        )
    if patch.sense < SENSE_MIN:
        return (
            f"(No story: {patch.label} is too flimsy to count as even a childlike attempt to mend a fence. "
            f"Choose ribbon, scarf, or skipping_rope instead.)"
        )
    return "(No story: this patch does not fit this fence trouble.)"


def predict_patch(world: World, patch_id: str) -> dict:
    sim = world.copy()
    sim.get("patch").attrs["strength"] = PATCHES[patch_id].strength
    sim.get("patch").label = PATCHES[patch_id].label
    sim.get("patch").meters["applied"] += 1
    propagate(sim, narrate=False)
    return {
        "escaped": sim.get("animal").meters["escaped"] >= THRESHOLD,
        "held": sim.get("fence").meters["held"] >= THRESHOLD,
    }


def opening(world: World, a: Entity, b: Entity, animal: Animal, flaw: Flaw) -> None:
    for child in (a, b):
        child.memes["joy"] += 1
    world.say(
        f"In a little garden bright with dew, {a.id} and {b.id} skipped two by two. "
        f"Along the fence went {animal.group}, {animal.motion}, with a {animal.sound} tune."
    )
    world.say(
        f"But not all was neat in the morning sun: {flaw.line}. "
        f"The fence looked fine from far away, though close it was not quite done."
    )


def warning(world: World, parent: Entity, a: Entity, flaw: Flaw) -> None:
    world.say(
        f'{a.id} started toward the corner where the animals nosed and played. '
        f'"Mind the fence, my little dear," said {a.pronoun("possessive")} '
        f'{parent.label_word}, "for {flaw.danger}."'
    )


def mishear(world: World, a: Entity) -> None:
    a.memes["pride"] += 1
    a.memes["misunderstood"] += 1
    world.say(
        f'''But in {a.id}'s busy little head, "Mind the fence" came out "Mend the fence" instead. '''
        f'{a.pronoun().capitalize()} puffed up proudly. "I can help!" {a.pronoun()} said.'
    )


def helper_warning(world: World, b: Entity, a: Entity, patch: Patch) -> None:
    pred = predict_patch(world, patch.id)
    world.facts["predicted_patch_holds"] = pred["held"]
    world.facts["predicted_escape"] = pred["escaped"]
    b.memes["caution"] += 1
    tail = (
        " It might keep things still for a blink."
        if pred["held"]
        else " It might not hold at all."
    )
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, maybe ' 
        f'"mind" means be careful, not mend with {patch.label}," {b.pronoun()} said.{tail}'
    )


def clarify_early(world: World, parent: Entity, a: Entity, b: Entity, flaw: Flaw) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} stopped, blinked once, and listened. "{b.id} is right," said '
        f'{parent.label_word}. "I meant take care near the fence, not fix it yourself."'
    )
    world.say(
        f"So the children stood back on the path while the grown-up bent to the wood. "
        f'Soon came {flaw.repair_sound}, and the shaky place was snug again.'
    )


def try_patch(world: World, a: Entity, patch: Patch) -> None:
    a.memes["defiance"] += 1
    patch_ent = world.get("patch")
    patch_ent.label = patch.label
    patch_ent.attrs["strength"] = patch.strength
    patch_ent.meters["applied"] += 1
    world.say(
        f'{a.id} hurried off and brought {patch.phrase}. With nimble fingers '
        f'{a.pronoun()} looped it round the fence and made a proud small bow.'
    )
    propagate(world, narrate=False)


def patch_result(world: World, animal: Animal) -> None:
    if world.get("animal").meters["escaped"] >= THRESHOLD:
        world.say(
            f"But the little tying was only a tiny trying. The fence gave a wobble, "
            f"and out skipped the {animal.label} with a {animal.sound} chorus."
        )
    else:
        world.say(
            f"For one small moment the patch held tight enough. The {animal.label} stayed in, "
            f"though the fence still looked sleepy and wrong."
        )


def chase_if_needed(world: World, a: Entity, b: Entity, animal: Animal) -> None:
    if world.get("animal").meters["escaped"] < THRESHOLD:
        return
    world.say(
        f'{a.id} gasped, {b.id} darted, and the yard went all a-flutter. '
        f'The {animal.label} scampered through the herbs and round the watering can.'
    )


def adult_fix(world: World, parent: Entity, flaw: Flaw, animal: Animal) -> None:
    fence = world.get("fence")
    fence.meters["loose"] = 0.0
    fence.meters["held"] = 1.0
    world.get("yard").meters["risk"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} came quick but calm. "{animal.sound.capitalize()} is not a repair song," '
        f'{parent.pronoun()} said, almost smiling. Then {parent.pronoun()} {flaw.proper_fix}.'
    )
    if world.get("animal").meters["escaped"] >= THRESHOLD:
        world.say(
            f'When the fence stood firm again, {parent.pronoun()} gathered the {animal.label} back inside, '
            f'one after another, soft and safe.'
        )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for child in (a, b):
        child.memes["lesson"] += 1
        child.memes["fear"] = 0.0
        child.memes["joy"] += 1
    world.say(
        f'Then {parent.label_word} knelt in the clover. "Helping is kind," {parent.pronoun()} said, '
        f'"but first we must hear words the right way round. "Mind" can mean take care."'
    )
    world.say(
        f'{a.id} nodded, and {b.id} nodded too. The misunderstanding felt small now that it had a name.'
    )


def ending(world: World, a: Entity, b: Entity, animal: Animal) -> None:
    world.say(
        f'By afternoon the fence stood straight and square. {a.id} and {b.id} fed crumbs through the safe side slats, '
        f'and the {animal.label} answered with a gentle {animal.sound}.'
    )
    world.say(
        "So there in the garden, under the blue, they learned to listen before they do."
    )


def tell(
    animal_cfg: Animal,
    flaw_cfg: Flaw,
    patch_cfg: Patch,
    child_a: str = "May",
    child_a_gender: str = "girl",
    child_b: str = "Tom",
    child_b_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    child_a_age: int = 5,
    child_b_age: int = 6,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=child_a,
            kind="character",
            type=child_a_gender,
            role="mishearer",
            age=child_a_age,
            traits=["eager"],
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=child_b,
            kind="character",
            type=child_b_gender,
            role="helper",
            age=child_b_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    fence = world.add(
        Entity(
            id="fence",
            type="fence",
            label="fence",
            attrs={"strain": flaw_cfg.strain, "flaw": flaw_cfg.id},
        )
    )
    yard = world.add(Entity(id="yard", type="yard", label="garden yard"))
    animal = world.add(
        Entity(
            id="animal",
            type="animal",
            label=animal_cfg.label,
            attrs={"pressure": animal_cfg.pressure},
        )
    )
    patch = world.add(
        Entity(
            id="patch",
            type="patch",
            label=patch_cfg.label,
            attrs={"strength": patch_cfg.strength},
        )
    )

    fence.meters["loose"] = 1.0
    fence.meters["held"] = 0.0
    yard.meters["risk"] = 0.0
    yard.meters["chaos"] = 0.0
    animal.meters["escaped"] = 0.0
    patch.meters["applied"] = 0.0
    a.memes["misunderstood"] = 0.0
    a.memes["fear"] = 0.0
    b.memes["caution"] = initial_caution(trait)
    b.memes["fear"] = 0.0

    propagate(world, narrate=False)

    opening(world, a, b, animal_cfg, flaw_cfg)
    world.para()
    warning(world, parent, a, flaw_cfg)
    mishear(world, a)
    helper_warning(world, b, a, patch_cfg)

    clarified = would_clarify(relation, child_a_age, child_b_age, trait)

    world.para()
    if clarified:
        clarify_early(world, parent, a, b, flaw_cfg)
    else:
        try_patch(world, a, patch_cfg)
        patch_result(world, animal_cfg)
        chase_if_needed(world, a, b, animal_cfg)
        world.para()
        adult_fix(world, parent, flaw_cfg, animal_cfg)
        lesson(world, parent, a, b)

    if clarified:
        world.para()
        lesson(world, parent, a, b)
    world.para()
    ending(world, a, b, animal_cfg)

    world.facts.update(
        child_a=a,
        child_b=b,
        parent=parent,
        animal_cfg=animal_cfg,
        flaw_cfg=flaw_cfg,
        patch_cfg=patch_cfg,
        clarified=clarified,
        escaped=animal.meters["escaped"] >= THRESHOLD,
        held=fence.meters["held"] >= THRESHOLD,
        outcome="clarified" if clarified else ("escaped" if animal.meters["escaped"] >= THRESHOLD else "held"),
        relation=relation,
    )
    return world


KNOWLEDGE = {
    "fence": [
        (
            "What is a fence for?",
            "A fence marks an edge and helps keep things safely in or out. A good fence is strong and steady, not wobbly.",
        )
    ],
    "repair": [
        (
            "Why do grown-ups fix loose wood with tools?",
            "Tools help press, hold, and fasten wood the right way. A soft ribbon cannot do the same hard job for very long.",
        )
    ],
    "gate": [
        (
            "What does a gate latch do?",
            "A latch helps a gate stay shut until someone opens it on purpose. If the latch is loose, the gate can swing open.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon good for?",
            "A ribbon is good for tying, wrapping, or decorating light things. It is soft and pretty, but it is not a real fence repair.",
        )
    ],
    "scarf": [
        (
            "Can a scarf fix a fence?",
            "A scarf can wrap around something for a little while, but it is cloth, not a proper repair tool. A grown-up still needs to mend the fence the right way.",
        )
    ],
    "rope": [
        (
            "What is a rope stronger than a ribbon for?",
            "A rope can pull or hold more than a ribbon because it is made for harder work. Even so, some jobs still need wood and tools.",
        )
    ],
    "farm_animals": [
        (
            "Why do little farm animals slip through small openings?",
            "Small animals can wriggle through places that look tiny to us. That is why fences and gates must close all the way.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. Talking again and listening carefully can clear it up.",
        )
    ],
}
KNOWLEDGE_ORDER = ["misunderstanding", "fence", "repair", "gate", "ribbon", "scarf", "rope", "farm_animals"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    flaw = f["flaw_cfg"]
    patch = f["patch_cfg"]
    animal = f["animal_cfg"]
    outcome = f["outcome"]
    if outcome == "clarified":
        return [
            'Write a short nursery-rhyme-style story for a 3-to-5-year-old about a misunderstanding around a fence.',
            f"Tell a gentle story where {a.id} hears 'mind the fence' as 'mend the fence,' but {b.id} helps explain the words before anything goes wrong.",
            f"Write a rhyming garden story with {animal.label}, a shaky {flaw.label}, and a child who almost tries to fix it with {patch.label}.",
        ]
    if outcome == "held":
        return [
            'Write a short nursery-rhyme-style story for a 3-to-5-year-old about a misunderstanding around a fence.',
            f"Tell a gentle story where {a.id} misunderstands a warning about the fence and ties on {patch.label}, which holds only for a moment until a grown-up repairs it properly.",
            f"Write a garden rhyme with {animal.label}, a wobbly fence, and a kind lesson about listening carefully.",
        ]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old about a misunderstanding around a fence.',
        f"Tell a nursery-rhyme-like story where {a.id} hears 'mind the fence' as 'mend the fence,' tries to help with {patch.label}, and the {animal.label} slip out before a grown-up fixes things.",
        f"Write a child-facing rhyme about a mistaken idea, a loose fence, and a calm ending after a little chase.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    parent = f["parent"]
    animal = f["animal_cfg"]
    flaw = f["flaw_cfg"]
    patch = f["patch_cfg"]
    outcome = f["outcome"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.id} and {b.id}, in a little garden with {animal.label}. Their {parent.label_word} helps when the fence trouble needs a real fix.",
        ),
        (
            "What was wrong with the fence?",
            f"The fence had a {flaw.label}. That mattered because {flaw.danger}.",
        ),
        (
            f"What did {a.id} misunderstand?",
            f'{a.id} heard "mind the fence" as "mend the fence." Because of that mix-up, {a.pronoun()} thought the grown-up was asking for a repair instead of warning {a.pronoun("object")} to be careful.',
        ),
    ]
    if outcome == "clarified":
        qa.append(
            (
                f"How was the misunderstanding fixed?",
                f"{b.id} stopped {a.id} and explained that 'mind' meant be careful. Then their {parent.label_word} repaired the fence properly, so the children could stand back and watch safely.",
            )
        )
    elif outcome == "held":
        qa.append(
            (
                f"What happened when {a.id} tied on the {patch.label}?",
                f"The {patch.label} held for one small moment, so the {animal.label} did not get out. But it was only a temporary hold, which showed that a child's patch was not the same as a real repair.",
            )
        )
        qa.append(
            (
                "Why did the grown-up still fix the fence afterward?",
                f"The fence was still wrong underneath the patch. The grown-up used the proper method because soft things like {patch.label} cannot make a shaky fence truly safe.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.id} tried to mend the fence with {patch.label}?",
                f"The patch did not hold, and the {animal.label} slipped out. The trouble happened because the misunderstanding led to a weak fix for a stronger problem.",
            )
        )
        qa.append(
            (
                "How did the story end safely?",
                f"Their {parent.label_word} calmly repaired the fence and gathered the {animal.label} back inside. After that, the children understood the words better and stayed on the safe side of the slats.",
            )
        )
    qa.append(
        (
            "What lesson did the children learn?",
            "They learned that helping starts with listening carefully. They also learned that fence repairs belong to grown-ups with the right tools.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"misunderstanding"} | set(f["animal_cfg"].tags) | set(f["flaw_cfg"].tags) | set(f["patch_cfg"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="chicks",
        flaw="loose_rail",
        patch="ribbon",
        child_a="May",
        child_a_gender="girl",
        child_b="Tom",
        child_b_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        child_a_age=4,
        child_b_age=7,
    ),
    StoryParams(
        animal="ducklings",
        flaw="loose_rail",
        patch="skipping_rope",
        child_a="Ben",
        child_a_gender="boy",
        child_b="Rose",
        child_b_gender="girl",
        parent="father",
        trait="curious",
        relation="friends",
        child_a_age=5,
        child_b_age=5,
    ),
    StoryParams(
        animal="lamb",
        flaw="sleepy_latch",
        patch="scarf",
        child_a="Nell",
        child_a_gender="girl",
        child_b="Finn",
        child_b_gender="boy",
        parent="mother",
        trait="steady",
        relation="siblings",
        child_a_age=6,
        child_b_age=6,
    ),
    StoryParams(
        animal="goat",
        flaw="sleepy_latch",
        patch="ribbon",
        child_a="Jack",
        child_a_gender="boy",
        child_b="Molly",
        child_b_gender="girl",
        parent="father",
        trait="bold",
        relation="friends",
        child_a_age=6,
        child_b_age=5,
    ),
]


ASP_RULES = r"""
valid_patch(F, P) :- flaw(F), patch(P), tieable(F), patch_sense(P, S), sense_min(M), S >= M.
valid(A, F, P) :- animal(A), valid_patch(F, P).

helper_older :- relation(siblings), child_b_age(B), child_a_age(A), B > A.
cautious_trait(T) :- trait(T), cautious(T).
init_caution(5) :- cautious_trait(T).
init_caution(3) :- trait(T), not cautious_trait(T).
clarified :- helper_older, init_caution(C), listen_score(L), C + 2 >= L.

strain_total(V) :- chosen_flaw(F), flaw_strain(F, FS), chosen_animal(A), animal_pressure(A, AP), V = FS + AP.
holds_patch :- chosen_patch(P), patch_strength(P, PS), strain_total(V), PS >= V.

outcome(clarified) :- clarified.
outcome(held) :- not clarified, holds_patch.
outcome(escaped) :- not clarified, not holds_patch.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("animal_pressure", aid, animal.pressure))
    for fid, flaw in FLAWS.items():
        lines.append(asp.fact("flaw", fid))
        lines.append(asp.fact("flaw_strain", fid, flaw.strain))
        if flaw.tieable:
            lines.append(asp.fact("tieable", fid))
    for pid, patch in PATCHES.items():
        lines.append(asp.fact("patch", pid))
        lines.append(asp.fact("patch_strength", pid, patch.strength))
        lines.append(asp.fact("patch_sense", pid, patch.sense))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("listen_score", int(LISTEN_SCORE)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_flaw", params.flaw),
            asp.fact("chosen_patch", params.patch),
            asp.fact("relation", params.relation),
            asp.fact("child_a_age", params.child_a_age),
            asp.fact("child_b_age", params.child_b_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a nursery-rhyme misunderstanding about a fence."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--flaw", choices=FLAWS)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.flaw and args.patch:
        flaw = FLAWS[args.flaw]
        patch = PATCHES[args.patch]
        if not valid_patch_for_flaw(flaw, patch):
            raise StoryError(explain_rejection(flaw, patch))

    combos = [
        c
        for c in valid_combos()
        if (args.animal is None or c[0] == args.animal)
        and (args.flaw is None or c[1] == args.flaw)
        and (args.patch is None or c[2] == args.patch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, flaw, patch = rng.choice(sorted(combos))
    child_a, child_a_gender = _pick_child(rng)
    child_b, child_b_gender = _pick_child(rng, avoid=child_a)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    child_a_age, child_b_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        animal=animal,
        flaw=flaw,
        patch=patch,
        child_a=child_a,
        child_a_gender=child_a_gender,
        child_b=child_b,
        child_b_gender=child_b_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        child_a_age=child_a_age,
        child_b_age=child_b_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.flaw not in FLAWS:
        raise StoryError(f"(Unknown flaw: {params.flaw})")
    if params.patch not in PATCHES:
        raise StoryError(f"(Unknown patch: {params.patch})")

    animal = ANIMALS[params.animal]
    flaw = FLAWS[params.flaw]
    patch = PATCHES[params.patch]
    if not valid_patch_for_flaw(flaw, patch):
        raise StoryError(explain_rejection(flaw, patch))

    world = tell(
        animal_cfg=animal,
        flaw_cfg=flaw,
        patch_cfg=patch,
        child_a=params.child_a,
        child_a_gender=params.child_a_gender,
        child_b=params.child_b,
        child_b_gender=params.child_b_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        child_a_age=params.child_a_age,
        child_b_age=params.child_b_age,
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
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, flaw, patch) combos:\n")
        for animal, flaw, patch in combos:
            print(f"  {animal:10} {flaw:12} {patch}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a} & {p.child_b}: {p.animal}, {p.flaw}, {p.patch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
