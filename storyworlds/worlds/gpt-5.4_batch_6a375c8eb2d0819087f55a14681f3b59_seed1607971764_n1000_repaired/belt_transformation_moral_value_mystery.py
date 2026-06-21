#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/belt_transformation_moral_value_mystery.py
=====================================================================

A standalone storyworld for a tiny mystery domain: a child finds a strange belt
with a hidden pocket, wonders who it belongs to, and solves the mystery by
choosing honesty over keeping what was found.

The world models:
- physical state in meters (belt tightness, glow, clue revealed, object found)
- emotional state in memes (curiosity, worry, honesty, relief, trust)

The central transformation is state-driven:
- when the child acts selfishly, the belt stays stiff and uneasy
- when the child tells the truth and returns the hidden object, the belt warms,
  loosens, and reveals its clue
- the ending image proves that honesty changed both the belt and the people

Run it
------
python storyworlds/worlds/gpt-5.4/belt_transformation_moral_value_mystery.py
python storyworlds/worlds/gpt-5.4/belt_transformation_moral_value_mystery.py --place attic --item key --owner gardener
python storyworlds/worlds/gpt-5.4/belt_transformation_moral_value_mystery.py --item lantern  # rejected: won't fit in the belt pocket
python storyworlds/worlds/gpt-5.4/belt_transformation_moral_value_mystery.py --all
python storyworlds/worlds/gpt-5.4/belt_transformation_moral_value_mystery.py --qa --json
python storyworlds/worlds/gpt-5.4/belt_transformation_moral_value_mystery.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    wearable: bool = False
    pocket_size: int = 0
    item_size: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man", "gardener", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    label: str
    scene: str
    hush: str
    afford_owners: set[str] = field(default_factory=set)
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
class HiddenItem:
    id: str
    label: str
    phrase: str
    clue: str
    use: str
    size: int
    owner_tags: set[str] = field(default_factory=set)
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
class Owner:
    id: str
    type: str
    label: str
    place_tags: set[str] = field(default_factory=set)
    seeks: str = ""
    thanks: str = ""
    clue_line: str = ""
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
class Reward:
    id: str
    label: str
    phrase: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_selfish_tightens(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    belt = world.get("belt")
    if child.memes["kept_secret"] >= THRESHOLD:
        sig = ("tighten",)
        if sig not in world.fired:
            world.fired.add(sig)
            belt.meters["tight"] += 1
            child.memes["worry"] += 1
            out.append("__tight__")
    return out


def _r_honesty_transforms(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    belt = world.get("belt")
    item = world.get("item")
    if child.memes["honest"] >= THRESHOLD and item.meters["returned"] >= THRESHOLD:
        sig = ("transform",)
        if sig not in world.fired:
            world.fired.add(sig)
            belt.meters["glow"] += 1
            belt.meters["soft"] += 1
            belt.meters["revealed"] += 1
            child.memes["relief"] += 1
            child.memes["trust"] += 1
            out.append("__transform__")
    return out


def _r_owner_relieved(world: World) -> list[str]:
    out: list[str] = []
    owner = world.get("owner")
    item = world.get("item")
    if item.meters["returned"] >= THRESHOLD:
        sig = ("relieved",)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["relief"] += 1
            owner.memes["gratitude"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="selfish_tightens", tag="moral", apply=_r_selfish_tightens),
    Rule(name="honesty_transforms", tag="moral", apply=_r_honesty_transforms),
    Rule(name="owner_relieved", tag="social", apply=_r_owner_relieved),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def fits_pocket(item: HiddenItem) -> bool:
    return item.size <= 1


def owner_matches(place: Place, owner: Owner, item: HiddenItem) -> bool:
    return owner.id in place.afford_owners and owner.id in item.owner_tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in HIDDEN_ITEMS.items():
            if not fits_pocket(item):
                continue
            for owner_id, owner in OWNERS.items():
                if owner_matches(place, owner, item):
                    combos.append((place_id, item_id, owner_id))
    return combos


def explain_rejection(item: HiddenItem, owner: Optional[Owner] = None, place: Optional[Place] = None) -> str:
    if not fits_pocket(item):
        return (
            f"(No story: {item.phrase} is too big to hide in a belt pocket. "
            f"This mystery needs a small object that could honestly be tucked inside the belt.)"
        )
    if owner is not None and place is not None and not owner_matches(place, owner, item):
        return (
            f"(No story: {owner.label} does not fit this clue in {place.label}. "
            f"Pick an owner who would plausibly use {item.label} there.)"
        )
    return "(No valid combination matches the given options.)"


def predict_transformation(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    item = sim.get("item")
    child.memes["honest"] += 1
    item.meters["returned"] += 1
    propagate(sim, narrate=False)
    belt = sim.get("belt")
    return {
        "glows": belt.meters["glow"] >= THRESHOLD,
        "revealed": belt.meters["revealed"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Late one afternoon, {child.id} wandered into {place.label}. "
        f"{place.scene} {place.hush}"
    )


def find_belt(world: World, child: Entity) -> None:
    belt = world.get("belt")
    belt.meters["found"] += 1
    world.say(
        f"Behind a stack of dusty boxes, {child.id} found an old belt with a brass buckle. "
        f"The leather was cool and dark, and a tiny stitched pocket hid on the inside."
    )


def find_object(world: World, child: Entity, item_cfg: HiddenItem) -> None:
    item = world.get("item")
    item.meters["found"] += 1
    world.say(
        f"When {child.pronoun()} slipped a finger into the little pocket, "
        f"{child.pronoun()} pulled out {item_cfg.phrase}. "
        f"It was such a small thing that it felt like a whisper from a secret."
    )


def first_clue(world: World, child: Entity, item_cfg: HiddenItem) -> None:
    world.say(
        f'There was one clue: {item_cfg.clue}. "{item_cfg.use}," {child.id} murmured. '
        f"That made the belt feel less like trash and more like a puzzle."
    )


def temptation(world: World, child: Entity, item_cfg: HiddenItem) -> None:
    child.memes["tempted"] += 1
    world.say(
        f"For a moment, {child.id} wondered whether to keep {item_cfg.label}. "
        f"No one had seen {child.pronoun('object')} find it, and mysteries can make the wrong idea seem shiny."
    )


def secret_choice(world: World, child: Entity) -> None:
    child.memes["kept_secret"] += 1
    propagate(world, narrate=False)
    belt = world.get("belt")
    if belt.meters["tight"] >= THRESHOLD:
        world.say(
            f"{child.id} slipped the belt around {child.pronoun('possessive')} waist to think. "
            f"At once it pulled oddly tight, not enough to hurt, but enough to make {child.pronoun('object')} frown."
        )


def search_owner(world: World, child: Entity, owner: Entity, owner_cfg: Owner, item_cfg: HiddenItem) -> None:
    world.say(
        f"Then {child.id} heard slow footsteps and saw {owner.label} looking from shelf to shelf. "
        f'"I cannot find my {item_cfg.label}," {owner.pronoun()} said. "{owner_cfg.seeks}"'
    )


def wonder_and_predict(world: World, child: Entity) -> None:
    pred = predict_transformation(world)
    world.facts["predicted_glow"] = pred["glows"]
    world.facts["predicted_reveal"] = pred["revealed"]
    if pred["glows"]:
        world.say(
            f"{child.id} looked down at the stubborn belt and had a strange thought: maybe this was the kind of mystery that opened only for the truth."
        )


def confess(world: World, child: Entity, owner: Entity, item_cfg: HiddenItem) -> None:
    child.memes["honest"] += 1
    world.say(
        f'{child.id} took a breath. "I found {item_cfg.phrase} hidden in this belt," {child.pronoun()} said. '
        f'"I almost kept it, but it belongs to someone."'
    )


def return_item(world: World, child: Entity, owner: Entity, item_cfg: HiddenItem) -> None:
    item = world.get("item")
    item.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} placed {item_cfg.label} in {owner.label}'s hand. "
        f"{owner.pronoun().capitalize()} stared at it as if a missing piece of the room had suddenly clicked back into place."
    )


def transform_belt(world: World, child: Entity, owner_cfg: Owner) -> None:
    belt = world.get("belt")
    if belt.meters["revealed"] >= THRESHOLD:
        world.say(
            f"Right then the belt changed. The stiff leather softened, the brass buckle gave a warm gold gleam, and a hidden line of stitching loosened to show {owner_cfg.clue_line}."
        )


def resolve_mystery(world: World, owner: Entity, owner_cfg: Owner) -> None:
    world.say(
        f'"So that is why it came back," {owner.label} whispered. "{owner_cfg.thanks}"'
    )


def reward_scene(world: World, child: Entity, reward_cfg: Reward) -> None:
    child.memes["joy"] += 1
    child.memes["trust"] += 1
    world.say(
        f"As a thank-you, {world.get('owner').label} gave {child.id} {reward_cfg.phrase}. "
        f"{reward_cfg.final_image}"
    )


def moral_close(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} understood then that the truest way to solve a mystery was not by grabbing the secret, but by being worthy of it."
    )


def tell(
    place: Place,
    item_cfg: HiddenItem,
    owner_cfg: Owner,
    reward_cfg: Reward,
    child_name: str = "Lina",
    child_type: str = "girl",
    trait: str = "careful",
) -> World:
    world = World(place=place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        traits=[trait],
        role="finder",
        attrs={"display_name": child_name},
    ))
    belt = world.add(Entity(
        id="belt",
        kind="thing",
        type="belt",
        label="the belt",
        wearable=True,
        pocket_size=1,
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.label,
        portable=True,
        item_size=item_cfg.size,
    ))
    owner = world.add(Entity(
        id="owner",
        kind="character",
        type=owner_cfg.type,
        label=owner_cfg.label,
        role="owner",
    ))

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        owner_cfg=owner_cfg,
        reward_cfg=reward_cfg,
        child=child,
        owner=owner,
        belt=belt,
        item=item,
    )

    introduce(world, child, place)
    find_belt(world, child)
    find_object(world, child, item_cfg)
    first_clue(world, child, item_cfg)

    world.para()
    temptation(world, child, item_cfg)
    secret_choice(world, child)
    search_owner(world, child, owner, owner_cfg, item_cfg)
    wonder_and_predict(world, child)

    world.para()
    confess(world, child, owner, item_cfg)
    return_item(world, child, owner, item_cfg)
    transform_belt(world, child, owner_cfg)
    resolve_mystery(world, owner, owner_cfg)

    world.para()
    reward_scene(world, child, reward_cfg)
    moral_close(world, child)

    world.facts.update(
        transformed=world.get("belt").meters["revealed"] >= THRESHOLD,
        returned=world.get("item").meters["returned"] >= THRESHOLD,
        tightened=world.get("belt").meters["tight"] >= THRESHOLD,
        honest=world.get("child").memes["honest"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the old attic",
        scene="Slanted windows let in strips of pale light, and every trunk seemed to keep its own quiet secret.",
        hush="The boards gave small creaks, as if the room were thinking.",
        afford_owners={"caretaker", "teacher"},
        tags={"attic", "mystery"},
    ),
    "library": Place(
        id="library",
        label="the back room of the library",
        scene="Tall shelves made long shadows, and the smell of paper hung in the still air.",
        hush="Even the dust seemed to settle softly, as if it did not want to disturb a clue.",
        afford_owners={"librarian", "teacher"},
        tags={"library", "mystery"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        scene="Rakes leaned like sleepy guards, and a small square window painted the floor with gray light.",
        hush="Somewhere outside, leaves scratched the wall with a whispering sound.",
        afford_owners={"gardener", "caretaker"},
        tags={"garden", "mystery"},
    ),
}

HIDDEN_ITEMS = {
    "key": HiddenItem(
        id="key",
        label="the little key",
        phrase="a little key with a green thread tied to it",
        clue="one side was worn shiny from careful fingers",
        use="A key opens something that matters",
        size=1,
        owner_tags={"caretaker", "librarian", "teacher", "gardener"},
        tags={"key", "honesty"},
    ),
    "seed_packet": HiddenItem(
        id="seed_packet",
        label="the tiny seed packet",
        phrase="a tiny seed packet folded into a square",
        clue="three sunflower seeds rattled inside",
        use="Someone was saving this for planting",
        size=1,
        owner_tags={"gardener"},
        tags={"seeds", "honesty"},
    ),
    "note": HiddenItem(
        id="note",
        label="the folded note",
        phrase="a folded note no bigger than a stamp",
        clue="one corner showed neat blue writing",
        use="A note can carry a secret without making a sound",
        size=1,
        owner_tags={"teacher", "librarian", "caretaker"},
        tags={"note", "honesty"},
    ),
    "lantern": HiddenItem(
        id="lantern",
        label="the toy lantern",
        phrase="a toy lantern with a tin handle",
        clue="the handle clicked against the buckle",
        use="A lantern gives light",
        size=3,
        owner_tags={"caretaker"},
        tags={"lantern"},
    ),
}

OWNERS = {
    "caretaker": Owner(
        id="caretaker",
        type="caretaker",
        label="the caretaker",
        place_tags={"attic", "shed"},
        seeks="Without it, I cannot open the old supply chest.",
        thanks="It only reveals its clue when the finder chooses honesty first.",
        clue_line="the caretaker's initials stitched in tiny thread",
        tags={"caretaker", "gratitude"},
    ),
    "librarian": Owner(
        id="librarian",
        type="librarian",
        label="the librarian",
        place_tags={"library"},
        seeks="Without it, I cannot open the cabinet of special books.",
        thanks="This belt was my grandfather's, and it has always loved a truthful hand.",
        clue_line="a small owl stitched beside the librarian's initials",
        tags={"librarian", "gratitude"},
    ),
    "teacher": Owner(
        id="teacher",
        type="teacher",
        label="the teacher",
        place_tags={"attic", "library"},
        seeks="Without it, I cannot unlock the box for tomorrow's lesson.",
        thanks="Long ago, someone said this belt keeps secrets only until kindness catches up with them.",
        clue_line="a stitched star beside the teacher's initials",
        tags={"teacher", "gratitude"},
    ),
    "gardener": Owner(
        id="gardener",
        type="gardener",
        label="the gardener",
        place_tags={"shed"},
        seeks="Without it, I cannot reach the seed drawer I was looking for.",
        thanks="It has a strange old habit of loosening only when the right thing is done.",
        clue_line="a tiny stitched sunflower and the gardener's initials",
        tags={"gardener", "gratitude"},
    ),
}

REWARDS = {
    "bookmark": Reward(
        id="bookmark",
        label="bookmark",
        phrase="a pressed-flower bookmark",
        final_image="The bookmark shone from one page of a storybook, and the belt rested calmly nearby as if the whole room trusted the evening again.",
        tags={"bookmark"},
    ),
    "button": Reward(
        id="button",
        label="button",
        phrase="a bright brass button for a keepsake box",
        final_image="It clicked warmly in {child}'s pocket, while the old belt lay open and easy on the table, no longer hiding from anyone.",
        tags={"button"},
    ),
    "sunflower": Reward(
        id="sunflower",
        label="sunflower",
        phrase="a small paper cup with a sunflower sprout",
        final_image="The green shoot stood straight on the windowsill, and the belt hung loose on its hook like a mystery finally at rest.",
        tags={"sunflower"},
    ),
}


@dataclass
class StoryParams:
    place: str
    item: str
    owner: str
    reward: str
    child_name: str
    child_type: str
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
    "belt": [(
        "What is a belt?",
        "A belt is a strap you wear around your waist to hold clothes in place. Some belts also have buckles, loops, or little hidden pockets."
    )],
    "honesty": [(
        "Why is honesty important when you find something?",
        "Honesty helps lost things get back to the people who need them. It also helps other people trust you because you chose what was right instead of what was easy."
    )],
    "key": [(
        "What does a key do?",
        "A key opens a lock that matches it. Even a tiny key can matter a lot if it opens an important box or door."
    )],
    "note": [(
        "Why can a note be important?",
        "A note can carry instructions, a reminder, or a message someone needs. Even a very small note can help solve a problem."
    )],
    "seeds": [(
        "What grows from seeds?",
        "Seeds can grow into plants when they are planted in soil and given water and light. A few tiny seeds can become something tall and bright."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something hidden or not understood yet. You solve it by noticing clues and thinking carefully."
    )],
}
KNOWLEDGE_ORDER = ["belt", "mystery", "honesty", "key", "note", "seeds"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    place = world.facts["place"]
    item = world.facts["item_cfg"]
    owner = world.facts["owner_cfg"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "belt" and ends by praising honesty.',
        f"Tell a mystery where {display_name(child)} finds an old belt in {place.label}, discovers {item.phrase}, and solves the puzzle by returning it to {owner.label}.",
        f'Write a child-facing story with transformation and moral value: a strange belt changes after a child tells the truth instead of keeping a found clue.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    owner = world.facts["owner"]
    place = world.facts["place"]
    item = world.facts["item_cfg"]
    owner_cfg = world.facts["owner_cfg"]
    reward = world.facts["reward_cfg"]
    name = display_name(child)

    qa = [
        (
            "Who is the story about?",
            f"It is about {name}, who found an old belt and a hidden clue, and {owner.label}, who had lost something important."
        ),
        (
            f"Where did {name} find the belt?",
            f"{name} found it in {place.label}, where the shadows and quiet corners made the room feel full of secrets. That setting made the belt seem like the start of a mystery."
        ),
        (
            f"What was hidden in the belt?",
            f"{name} found {item.phrase} tucked in the belt's secret pocket. The tiny clue made {name} wonder who needed it and what it was for."
        ),
        (
            f"Why did the belt feel strange when {name} thought about keeping the clue?",
            f"The belt pulled tight as soon as {name} kept the find a secret. In this story's world, the belt reacts to selfish hiding by growing uneasy."
        ),
        (
            f"How was the mystery solved?",
            f"{name} told the truth and returned {item.label} to {owner.label}. That honest choice solved the mystery because {owner.label} explained why the item mattered."
        ),
    ]
    if world.facts.get("transformed"):
        qa.append((
            "What changed after the truth was told?",
            f"The belt softened and glowed, and a hidden stitched clue appeared on it. The change showed that honesty had opened the mystery in a way sneaking could not."
        ))
    qa.append((
        f"What happened at the end?",
        f"{owner.label.capitalize()} thanked {name} and gave {child.pronoun('object')} {reward.phrase}. The last image shows the room feeling calm again because the secret was handled honestly."
    ))
    qa.append((
        "What is the moral of the story?",
        f"The story teaches that honesty is the right way to handle a mystery. Telling the truth helped both the lost object and the strange belt find peace."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"belt", "mystery", "honesty"} | set(world.facts["item_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library",
        item="key",
        owner="librarian",
        reward="bookmark",
        child_name="Lina",
        child_type="girl",
        trait="careful",
    ),
    StoryParams(
        place="shed",
        item="seed_packet",
        owner="gardener",
        reward="sunflower",
        child_name="Milo",
        child_type="boy",
        trait="gentle",
    ),
    StoryParams(
        place="attic",
        item="note",
        owner="teacher",
        reward="button",
        child_name="Nora",
        child_type="girl",
        trait="thoughtful",
    ),
]


ASP_RULES = r"""
fits_pocket(I) :- item(I), size(I,S), S <= 1.
matches_owner(P,I,O) :- place(P), item(I), owner(O), place_allows(P,O), item_owner(I,O).
valid(P,I,O) :- fits_pocket(I), matches_owner(P,I,O).

transforms :- kept_secret, honest, returned.
outcome(transformed) :- transforms.
#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for owner_id in sorted(place.afford_owners):
            lines.append(asp.fact("place_allows", place_id, owner_id))
    for item_id, item in HIDDEN_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("size", item_id, item.size))
        for owner_id in sorted(item.owner_tags):
            lines.append(asp.fact("item_owner", item_id, owner_id))
    for owner_id in OWNERS:
        lines.append(asp.fact("owner", owner_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome() -> str:
    import asp

    model = asp.one_model(asp_program("kept_secret.\nhonest.\nreturned.\n"))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: a child finds a belt, faces a temptation, and solves the mystery through honesty."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=HIDDEN_ITEMS)
    ap.add_argument("--owner", choices=OWNERS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Lina", "Nora", "Maya", "Ella", "Ivy", "Lucy"]
BOY_NAMES = ["Milo", "Theo", "Eli", "Ben", "Finn", "Noah"]
TRAITS = ["careful", "gentle", "thoughtful", "brave", "patient", "curious"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item:
        item = HIDDEN_ITEMS[args.item]
        if not fits_pocket(item):
            raise StoryError(explain_rejection(item))
    if args.place and args.owner and args.item:
        place = PLACES[args.place]
        owner = OWNERS[args.owner]
        item = HIDDEN_ITEMS[args.item]
        if not owner_matches(place, owner, item):
            raise StoryError(explain_rejection(item, owner=owner, place=place))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.owner is None or combo[2] == args.owner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, owner_id = rng.choice(sorted(combos))
    reward_id = args.reward or rng.choice(sorted(REWARDS.keys()))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        item=item_id,
        owner=owner_id,
        reward=reward_id,
        child_name=child_name,
        child_type=child_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in HIDDEN_ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.owner not in OWNERS:
        raise StoryError(f"(Unknown owner: {params.owner})")
    if params.reward not in REWARDS:
        raise StoryError(f"(Unknown reward: {params.reward})")

    place = PLACES[params.place]
    item = HIDDEN_ITEMS[params.item]
    owner = OWNERS[params.owner]
    reward = REWARDS[params.reward]

    if not fits_pocket(item):
        raise StoryError(explain_rejection(item))
    if not owner_matches(place, owner, item):
        raise StoryError(explain_rejection(item, owner=owner, place=place))

    world = tell(
        place=place,
        item_cfg=item,
        owner_cfg=owner,
        reward_cfg=reward,
        child_name=params.child_name,
        child_type=params.child_type,
        trait=params.trait,
    )

    story = world.render()
    if reward.id == "button":
        story = story.replace("{child}", display_name(world.facts["child"]))

    return StorySample(
        params=params,
        story=story,
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
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    out = asp_outcome()
    if out == "transformed":
        print("OK: ASP outcome model reaches transformed.")
    else:
        rc = 1
        print(f"MISMATCH in outcome model: got {out!r}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(123)))
        if not sample.story.strip():
            raise StoryError("empty random story")
        print("OK: seeded random generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {exc}")

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
        print(f"{len(combos)} compatible (place, item, owner) combos:\n")
        for place, item, owner in combos:
            print(f"  {place:8} {item:12} {owner}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.item} in {p.place} ({p.owner})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
