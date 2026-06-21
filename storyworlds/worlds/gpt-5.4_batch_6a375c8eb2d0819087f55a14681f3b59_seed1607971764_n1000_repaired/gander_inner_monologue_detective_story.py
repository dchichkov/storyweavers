#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gander_inner_monologue_detective_story.py
====================================================================

A standalone storyworld about a child detective solving a tiny barnyard mystery.

Seed:
- word: gander
- feature: inner monologue
- style: detective story

Premise
-------
A child is about to join a small fair or family moment when an important item is
missing. The child slips into detective mode, follows clues, reasons inwardly,
and discovers that a curious gander carried the item away. The ending image
proves the change: the item is returned, the gander is calmly understood, and
the child now uses a safer keeper-tool to avoid the same mix-up next time.

This world models:
- typed entities with physical meters and emotional memes
- a small causal chain from missing item -> clue -> suspicion -> search ->
  calm retrieval -> safer ending
- inner monologue generated from world state, not pasted as a fixed gimmick
- a Python reasonableness gate plus an inline ASP twin

Run
---
python storyworlds/worlds/gpt-5.4/gander_inner_monologue_detective_story.py
python storyworlds/worlds/gpt-5.4/gander_inner_monologue_detective_story.py --all
python storyworlds/worlds/gpt-5.4/gander_inner_monologue_detective_story.py --qa --json
python storyworlds/worlds/gpt-5.4/gander_inner_monologue_detective_story.py --verify
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
    kind: str = "thing"            # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    helper_source: str
    hideouts: set[str] = field(default_factory=set)
    animal_home: str = ""
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
class MissingItem:
    id: str
    label: str
    phrase: str
    use_line: str
    quality: str              # shiny | soft | food
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
class Clue:
    id: str
    label: str
    text: str
    points_to: set[str] = field(default_factory=set)
    for_qualities: set[str] = field(default_factory=set)
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
class Hideout:
    id: str
    label: str
    phrase: str
    nest_like: bool = False
    food_like: bool = False
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
class KeeperTool:
    id: str
    label: str
    phrase: str
    calm_text: str
    safe_end: str
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


def _r_gander_takes(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("item_taken"):
        return out
    item = world.get("item")
    gander = world.get("gander")
    hideout = world.facts["hideout_cfg"]
    if item.attrs.get("quality") in {"shiny", "soft", "food"} and gander.memes["curious"] >= THRESHOLD:
        sig = ("take", item.id, hideout.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        item.attrs["location"] = hideout.id
        item.meters["missing"] += 1
        gander.meters["has_item"] += 1
        world.facts["item_taken"] = True
        out.append("__taken__")
    return out


def _r_clue_from_hideout(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("item_taken"):
        return out
    clue = world.facts["clue_cfg"]
    hideout = world.facts["hideout_cfg"]
    item = world.get("item")
    sig = ("clue", clue.id, hideout.id)
    if sig in world.fired:
        return out
    if hideout.id in clue.points_to and item.attrs.get("quality") in clue.for_qualities:
        world.fired.add(sig)
        world.facts["clue_visible"] = True
        world.facts["lead_to"] = hideout.id
        out.append("__clue__")
    return out


def _r_detective_infers(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("clue_visible"):
        return out
    detective = world.get("detective")
    sig = ("infer", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspicion"] += 1
    detective.memes["bravery"] += 1
    world.facts["suspected_gander"] = True
    out.append("__inferred__")
    return out


CAUSAL_RULES = [
    Rule(name="gander_takes", tag="physical", apply=_r_gander_takes),
    Rule(name="clue_from_hideout", tag="physical", apply=_r_clue_from_hideout),
    Rule(name="detective_infers", tag="mental", apply=_r_detective_infers),
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


def item_fits_hideout(item: MissingItem, hideout: Hideout) -> bool:
    if item.quality == "soft":
        return hideout.nest_like
    if item.quality == "shiny":
        return hideout.nest_like
    if item.quality == "food":
        return hideout.food_like
    return False


def clue_matches(item: MissingItem, clue: Clue, hideout: Hideout) -> bool:
    return item.quality in clue.for_qualities and hideout.id in clue.points_to


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for clue_id, clue in CLUES.items():
                for hideout_id, hideout in HIDEOUTS.items():
                    if hideout_id not in setting.hideouts:
                        continue
                    if item_fits_hideout(item, hideout) and clue_matches(item, clue, hideout):
                        combos.append((setting_id, item_id, clue_id, hideout_id))
    return sorted(combos)


def predict_case(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "taken": bool(sim.facts.get("item_taken")),
        "clue_visible": bool(sim.facts.get("clue_visible")),
        "suspected_gander": bool(sim.facts.get("suspected_gander")),
        "lead_to": sim.facts.get("lead_to", ""),
    }


def inner(world: World, detective: Entity, text: str) -> None:
    detective.memes["thinking"] += 1
    world.say(f'{detective.id} thought, "{text}"')


def introduce(world: World, detective: Entity, grownup: Entity, item: MissingItem) -> None:
    world.say(
        f"{detective.id} liked mysteries so much that even an ordinary afternoon in "
        f"{world.setting.place} could feel like the first page of a detective story."
    )
    world.say(
        f"That day, {grownup.label_word} had set out {item.phrase}, and {item.use_line}"
    )
    detective.memes["eager"] += 1


def missing(world: World, detective: Entity, item_ent: Entity) -> None:
    item_ent.meters["noticed_missing"] += 1
    detective.memes["concern"] += 1
    world.say(
        f"But when {detective.id} reached for the {item_ent.label}, it was gone."
    )
    inner(world, detective, "A clue is never just a clue. It is a tiny arrow pointing somewhere.")


def observe(world: World, detective: Entity, clue: Clue) -> None:
    world.say(
        f"On the ground nearby lay {clue.text}."
    )
    inner(world, detective, f"If I read this sign the right way, it may tell me where to look next.")
    detective.memes["focus"] += 1


def warn_about_gander(world: World, grownup: Entity, detective: Entity) -> None:
    gander = world.get("gander")
    world.say(
        f'"Careful around the gander," {grownup.label_word} said softly. '
        f'"He is proud and noisy, but he calms down when people move slowly."'
    )
    detective.memes["care"] += 1
    gander.memes["guarding"] += 1


def infer(world: World, detective: Entity, clue: Clue, hideout: Hideout) -> None:
    detective.memes["detective_pride"] += 1
    inner(world, detective, f"{clue.label.capitalize()}... that means the trail is leading toward {hideout.phrase}.")
    world.say(
        f"{detective.id} crouched low, studying the clue as if it were a secret note from the yard itself."
    )


def search(world: World, detective: Entity, hideout: Hideout) -> None:
    world.say(
        f"{detective.id} tiptoed to {hideout.phrase} and peered in."
    )


def reveal(world: World, detective: Entity, item_ent: Entity, hideout: Hideout) -> None:
    gander = world.get("gander")
    item_ent.meters["found"] += 1
    world.say(
        f"There it was: the {item_ent.label}, tucked inside {hideout.phrase} while the gander stood nearby, neck high and eyes bright."
    )
    inner(world, detective, "So that was it. He was not being mean. He was collecting treasures his own way.")
    detective.memes["understanding"] += 1
    gander.memes["proud"] += 1


def calm_retrieve(world: World, grownup: Entity, detective: Entity, tool: KeeperTool, item_ent: Entity) -> None:
    gander = world.get("gander")
    world.say(
        f"{grownup.label_word.capitalize()} did not snatch or shout. {grownup.pronoun().capitalize()} {tool.calm_text}"
    )
    gander.memes["calm"] += 1
    gander.memes["guarding"] = 0.0
    gander.meters["has_item"] = 0.0
    item_ent.meters["missing"] = 0.0
    item_ent.attrs["location"] = "detective"
    detective.memes["relief"] += 1
    detective.memes["gratitude"] += 1


def explain_case(world: World, detective: Entity, item: MissingItem, clue: Clue, hideout: Hideout) -> None:
    world.say(
        f'"I solved it," {detective.id} said. "The {clue.label} led me to {hideout.label}, and the gander had carried the {item.label} there."'
    )
    inner(world, detective, "A real detective does not only find what is lost. A real detective understands why it was lost.")


def ending(world: World, detective: Entity, tool: KeeperTool, item: MissingItem) -> None:
    detective.memes["joy"] += 1
    detective.memes["confidence"] += 1
    world.say(
        f"Soon the small trouble was mended, and {item.use_line.lower()}"
    )
    world.say(
        f"After that, {detective.id} always remembered {tool.safe_end}"
    )
    world.say(
        f"And whenever the gander waddled past, {detective.id} gave him a respectful little nod, as one detective to another."
    )


def tell(
    setting: Setting,
    item: MissingItem,
    clue: Clue,
    hideout: Hideout,
    tool: KeeperTool,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    grownup_type: str = "mother",
) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        label=detective_name,
        traits=["careful", "curious"],
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grown-up",
    ))
    gander = world.add(Entity(
        id="gander",
        kind="animal",
        type="gander",
        role="suspect",
        label="the gander",
        traits=["proud", "curious"],
        attrs={"home": setting.animal_home},
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        role="missing_item",
        label=item.label,
        attrs={"quality": item.quality, "location": "table"},
        tags=set(item.tags),
    ))

    detective.memes["curiosity"] = 1.0
    detective.memes["thinking"] = 0.0
    detective.memes["focus"] = 0.0
    detective.memes["relief"] = 0.0
    detective.memes["understanding"] = 0.0
    gander.memes["curious"] = 1.0
    gander.memes["guarding"] = 0.0
    gander.memes["calm"] = 0.0
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] = 0.0

    world.facts.update(
        setting=setting,
        item_cfg=item,
        clue_cfg=clue,
        hideout_cfg=hideout,
        tool_cfg=tool,
        item_taken=False,
        clue_visible=False,
        suspected_gander=False,
        lead_to="",
    )

    propagate(world, narrate=False)

    introduce(world, detective, grownup, item)
    missing(world, detective, item_ent)

    world.para()
    observe(world, detective, clue)
    warn_about_gander(world, grownup, detective)
    infer(world, detective, clue, hideout)

    world.para()
    search(world, detective, hideout)
    reveal(world, detective, item_ent, hideout)

    world.para()
    calm_retrieve(world, grownup, detective, tool, item_ent)
    explain_case(world, detective, item, clue, hideout)
    ending(world, detective, tool, item)

    world.facts.update(
        detective=detective,
        grownup=grownup,
        gander=gander,
        item_ent=item_ent,
        solved=item_ent.attrs.get("location") == "detective",
        inner_lines=int(detective.memes["thinking"]),
    )
    return world


SETTINGS = {
    "farmyard": Setting(
        id="farmyard",
        place="the farmyard",
        scene="barn doors, straw, and a little table near the gate",
        helper_source="a scoop of grain from the shed",
        hideouts={"nest_box", "reed_bank", "feed_crate"},
        animal_home="the goose pen",
        tags={"farm", "yard"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard behind the barn",
        scene="apple trees, tall grass, and a wooden bench by the fence",
        helper_source="a handful of corn from the basket",
        hideouts={"nest_box", "reed_bank", "feed_crate"},
        animal_home="the pond path",
        tags={"orchard", "yard"},
    ),
}

ITEMS = {
    "ribbon": MissingItem(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon on the table",
        use_line="everyone was meant to pin it on the pie basket for the little fair photo.",
        quality="soft",
        tags={"ribbon", "fair"},
    ),
    "spoon": MissingItem(
        id="spoon",
        label="silver spoon",
        phrase="a silver spoon beside the jam jar",
        use_line="it was needed to stir the berry jam before supper.",
        quality="shiny",
        tags={"spoon", "kitchen"},
    ),
    "roll": MissingItem(
        id="roll",
        label="warm bread roll",
        phrase="a warm bread roll on a napkin",
        use_line="it was supposed to go with the picnic lunch.",
        quality="food",
        tags={"bread", "picnic"},
    ),
}

CLUES = {
    "feathers": Clue(
        id="feathers",
        label="white feathers",
        text="two white feathers and a bent stem of straw",
        points_to={"nest_box"},
        for_qualities={"soft", "shiny"},
        tags={"feather", "bird"},
    ),
    "webbed_tracks": Clue(
        id="webbed_tracks",
        label="webbed tracks",
        text="a neat line of webbed tracks pressed into the dust",
        points_to={"reed_bank", "feed_crate"},
        for_qualities={"food"},
        tags={"tracks", "bird"},
    ),
    "grain_scatter": Clue(
        id="grain_scatter",
        label="scattered grain",
        text="a little scatter of grain beside wide bird prints",
        points_to={"feed_crate"},
        for_qualities={"food"},
        tags={"grain", "bird"},
    ),
    "straw_trail": Clue(
        id="straw_trail",
        label="a straw trail",
        text="a crooked straw trail leading toward the nesting corner",
        points_to={"nest_box"},
        for_qualities={"soft"},
        tags={"straw", "nest"},
    ),
}

HIDEOUTS = {
    "nest_box": Hideout(
        id="nest_box",
        label="the nest box",
        phrase="the nest box under the shelf",
        nest_like=True,
        food_like=False,
        tags={"nest", "barn"},
    ),
    "reed_bank": Hideout(
        id="reed_bank",
        label="the pond reeds",
        phrase="the pond reeds by the fence",
        nest_like=False,
        food_like=True,
        tags={"pond", "reeds"},
    ),
    "feed_crate": Hideout(
        id="feed_crate",
        label="the feed crate",
        phrase="the feed crate by the wall",
        nest_like=False,
        food_like=True,
        tags={"feed", "barn"},
    ),
}

TOOLS = {
    "grain": KeeperTool(
        id="grain",
        label="grain",
        phrase="a scoop of grain",
        calm_text="shook a scoop of grain onto the ground a few steps away, and while the gander turned to peck at it, gently lifted the item free.",
        safe_end="that a calm helper and a little space worked better than rushing a proud bird.",
        tags={"grain", "animal_care"},
    ),
    "basket_lid": KeeperTool(
        id="basket_lid",
        label="basket lid",
        phrase="a basket lid",
        calm_text="held a basket lid in front like a quiet shield, guiding the gander sideways until there was room to pick the item up.",
        safe_end="to fetch the basket lid before going near the gander's favorite corner.",
        tags={"basket", "animal_care"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ella", "Ruby", "Anna", "Clara"]
BOY_NAMES = ["Ben", "Max", "Sam", "Theo", "Leo", "Finn", "Eli", "Noah"]


@dataclass
class StoryParams:
    setting: str
    item: str
    clue: str
    hideout: str
    tool: str
    detective_name: str
    detective_gender: str
    grownup: str
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
    "gander": [
        (
            "What is a gander?",
            "A gander is a male goose. Ganders can be loud and proud, and they sometimes guard a place they like."
        )
    ],
    "feather": [
        (
            "Why can feathers be a clue near birds?",
            "Feathers come from birds, so finding them can show that a bird has been nearby. A detective uses that kind of sign to narrow down what happened."
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show which way an animal walked and what kind of feet it has. They help you follow a trail without seeing the animal move."
        )
    ],
    "nest": [
        (
            "Why might a bird carry soft things to a nest?",
            "Birds often like soft things in a nest because they make it feel snug. A ribbon or straw can look useful to a bird, even if it belongs to people."
        )
    ],
    "grain": [
        (
            "Why does grain help calm a bird?",
            "Food can draw a bird's attention away for a moment. That gives a grown-up time to move slowly and keep everyone safe."
        )
    ],
    "animal_care": [
        (
            "Why should you move slowly around a guarding bird?",
            "Sudden rushing can make the bird feel alarmed. Slow, calm movement helps the bird settle and keeps people safer."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks what they mean, and uses them to solve a mystery. Good detectives also try to understand why something happened."
        )
    ],
}
KNOWLEDGE_ORDER = ["gander", "feather", "tracks", "nest", "grain", "animal_care", "detective"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    item = f["item_cfg"]
    hideout = f["hideout_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes a gander, a missing {item.label}, and inner monologue.',
        f"Tell a small mystery where {detective.id} notices clues, thinks carefully to {detective.pronoun('object')}, and finds a missing {item.label} near {hideout.label}.",
        'Write a child-facing detective story with short inner thoughts and a calm ending where understanding solves the mystery better than scolding.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    grownup = f["grownup"]
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    hideout = f["hideout_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who loves mysteries, a helpful {grownup.label_word}, and a proud gander. The story follows {detective.id} as a tiny detective solving a missing-item case."
        ),
        (
            f"What was missing?",
            f"The missing thing was the {item.label}. It mattered because {item.use_line}"
        ),
        (
            "What clue started the case?",
            f"The first clue was {clue.text}. That clue mattered because it pointed the detective toward {hideout.label}."
        ),
        (
            "How did the inner monologue help solve the mystery?",
            f"{detective.id} talked quietly inside {detective.pronoun('possessive')} own mind, reminding {detective.pronoun('object')}self that clues point somewhere. Those thoughts helped {detective.pronoun('object')} slow down, read the sign carefully, and follow the trail instead of guessing."
        ),
        (
            "Why did the detective think the gander had the item?",
            f"{detective.id} saw a clue that matched the place where the item was hidden. The clue and the hideout fit together, so the gander became the best suspect."
        ),
        (
            "How did they get the item back safely?",
            f"{grownup.label_word.capitalize()} stayed calm and used {tool.phrase} instead of grabbing or shouting. That gave the gander space to settle, and then the item could be taken back safely."
        ),
        (
            "How did the story end?",
            f"The mystery was solved, the {item.label} was returned, and {detective.id} understood that the gander was collecting things in his own way. The ending feels peaceful because the problem is fixed with patience and care."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"gander", "detective"}
    clue = world.facts["clue_cfg"]
    hideout = world.facts["hideout_cfg"]
    tool = world.facts["tool_cfg"]
    if clue.id == "feathers":
        tags.add("feather")
    if clue.id == "webbed_tracks":
        tags.add("tracks")
    if hideout.nest_like:
        tags.add("nest")
    tags |= set(tool.tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if k not in {'detective', 'grownup', 'gander', 'item_ent'}} }")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="farmyard",
        item="ribbon",
        clue="straw_trail",
        hideout="nest_box",
        tool="basket_lid",
        detective_name="Nora",
        detective_gender="girl",
        grownup="mother",
    ),
    StoryParams(
        setting="farmyard",
        item="spoon",
        clue="feathers",
        hideout="nest_box",
        tool="grain",
        detective_name="Ben",
        detective_gender="boy",
        grownup="father",
    ),
    StoryParams(
        setting="orchard",
        item="roll",
        clue="webbed_tracks",
        hideout="reed_bank",
        tool="grain",
        detective_name="Lily",
        detective_gender="girl",
        grownup="mother",
    ),
    StoryParams(
        setting="orchard",
        item="roll",
        clue="grain_scatter",
        hideout="feed_crate",
        tool="basket_lid",
        detective_name="Max",
        detective_gender="boy",
        grownup="father",
    ),
]


def explain_rejection(item: MissingItem, clue: Clue, hideout: Hideout) -> str:
    if not item_fits_hideout(item, hideout):
        if item.quality in {"soft", "shiny"}:
            return (
                f"(No story: a {item.label} fits a nest-like hiding place, but {hideout.label} is not the kind of spot a curious gander would choose for that treasure.)"
            )
        return (
            f"(No story: a {item.label} is food, but {hideout.label} is not the kind of place a gander would take food.)"
        )
    return (
        f"(No story: {clue.label} does not honestly point to {hideout.label} for a missing {item.label}. The detective needs a fair clue, not a random guess.)"
    )


ASP_RULES = r"""
fits_hideout(I,H) :- item(I), quality(I,soft), nest_like(H).
fits_hideout(I,H) :- item(I), quality(I,shiny), nest_like(H).
fits_hideout(I,H) :- item(I), quality(I,food), food_like(H).

clue_matches(I,C,H) :- item(I), clue(C), hideout(H),
                       clue_points(C,H),
                       quality(I,Q),
                       clue_quality(C,Q).

valid(S,I,C,H) :- setting(S), item(I), clue(C), hideout(H),
                  setting_hideout(S,H),
                  fits_hideout(I,H),
                  clue_matches(I,C,H).

taken(I,H) :- chosen_item(I), chosen_hideout(H), fits_hideout(I,H).
visible_clue(C,H) :- chosen_item(I), chosen_clue(C), chosen_hideout(H),
                     taken(I,H), clue_matches(I,C,H).
suspected_gander :- visible_clue(_, _).
solved :- chosen_item(I), chosen_hideout(H), chosen_clue(C), chosen_tool(T),
          taken(I,H), visible_clue(C,H), tool(T).
outcome(solved) :- solved.

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hideout in sorted(setting.hideouts):
            lines.append(asp.fact("setting_hideout", sid, hideout))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("quality", iid, item.quality))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for hideout in sorted(clue.points_to):
            lines.append(asp.fact("clue_points", cid, hideout))
        for q in sorted(clue.for_qualities):
            lines.append(asp.fact("clue_quality", cid, q))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        if hideout.nest_like:
            lines.append(asp.fact("nest_like", hid))
        if hideout.food_like:
            lines.append(asp.fact("food_like", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
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
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_hideout", params.hideout),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra))
    got = asp.atoms(model, "outcome")
    return got[0][0] if got else "?"


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    clue = CLUES[params.clue]
    hideout = HIDEOUTS[params.hideout]
    if item_fits_hideout(item, hideout) and clue_matches(item, clue, hideout):
        return "solved"
    return "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child detective solves a gentle gander mystery with inner monologue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.clue and args.hideout:
        item = ITEMS[args.item]
        clue = CLUES[args.clue]
        hideout = HIDEOUTS[args.hideout]
        if not (item_fits_hideout(item, hideout) and clue_matches(item, clue, hideout)):
            raise StoryError(explain_rejection(item, clue, hideout))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
        and (args.hideout is None or combo[3] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, clue_id, hideout_id = rng.choice(combos)
    tool = args.tool or rng.choice(sorted(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        clue=clue_id,
        hideout=hideout_id,
        tool=tool,
        detective_name=name,
        detective_gender=gender,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    clue = CLUES[params.clue]
    hideout = HIDEOUTS[params.hideout]
    tool = TOOLS[params.tool]

    if params.hideout not in setting.hideouts:
        raise StoryError(f"(No story: {hideout.label} is not available in {setting.place}.)")
    if not item_fits_hideout(item, hideout) or not clue_matches(item, clue, hideout):
        raise StoryError(explain_rejection(item, clue, hideout))

    world = tell(
        setting=setting,
        item=item,
        clue=clue,
        hideout=hideout,
        tool=tool,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        grownup_type=params.grownup,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

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
        print(f"{len(combos)} compatible (setting, item, clue, hideout) combos:\n")
        for setting, item, clue, hideout in combos:
            print(f"  {setting:8} {item:7} {clue:13} {hideout}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.detective_name}: {p.item} in {p.setting} ({p.clue} -> {p.hideout})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
