#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/psychedelic_positive_miss_twist_humor_heartwarming.py
=================================================================================

A standalone story world about a shy child who folds a paper airplane carrying a
kind note for Miss Maple. The note is bright, positive, and sometimes hilariously
misses its first target -- but the miss can become the heartwarming twist that
helps the message arrive anyway.

The little domain is constraint-checked:
- a fold must be able to reach the target directly, OR
- if it is likely to miss, the setting must provide a plausible helper who can
  notice the plane and bring the note along.

The prose is driven by simulated state: hope, worry, embarrassment, laughter,
relief, and gratitude all come from the world model, not from template swaps.

Run it
------
    python storyworlds/worlds/gpt-5.4/psychedelic_positive_miss_twist_humor_heartwarming.py
    python storyworlds/worlds/gpt-5.4/psychedelic_positive_miss_twist_humor_heartwarming.py --asp
    python storyworlds/worlds/gpt-5.4/psychedelic_positive_miss_twist_humor_heartwarming.py --verify
    python storyworlds/worlds/gpt-5.4/psychedelic_positive_miss_twist_humor_heartwarming.py -n 5 --seed 7 --qa
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "teacher"}
        male = {"boy", "father", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "teacher": "teacher",
            "grandpa": "grandpa",
        }.get(self.type, self.type)
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
    distance: int
    breeze: int
    helper_id: str
    helper_label: str
    helper_type: str
    helper_action: str
    landing: str
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
class PaperStyle:
    id: str
    phrase: str
    colors: str
    doodle: str
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
class Fold:
    id: str
    label: str
    power: int
    wobble: int
    comic: str
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
class Target:
    id: str
    label: str
    phrase: str
    distance_bonus: int
    easy_catch: bool
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


def plane_range(setting: Setting, fold: Fold, target: Target) -> int:
    return fold.power - setting.breeze + target.distance_bonus


def direct_hit_possible(setting: Setting, fold: Fold, target: Target) -> bool:
    return plane_range(setting, fold, target) >= setting.distance


def helper_rescue_possible(setting: Setting, fold: Fold, target: Target) -> bool:
    if setting.helper_id == "none":
        return False
    return plane_range(setting, fold, target) >= max(1, setting.distance - 1)


def valid_combo(setting: Setting, fold: Fold, target: Target) -> bool:
    return direct_hit_possible(setting, fold, target) or helper_rescue_possible(setting, fold, target)


def outcome_for(setting: Setting, fold: Fold, target: Target) -> str:
    return "direct" if direct_hit_possible(setting, fold, target) else "helper"


def _r_embarrassment(world: World) -> list[str]:
    plane = world.get("plane")
    child = world.get("child")
    if plane.meters["missed"] < THRESHOLD:
        return []
    sig = ("embarrassed",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    return []


def _r_delivery_relief(world: World) -> list[str]:
    plane = world.get("plane")
    child = world.get("child")
    miss_maple = world.get("miss_maple")
    if plane.meters["delivered"] < THRESHOLD:
        return []
    sig = ("delivered",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    miss_maple.memes["gratitude"] += 1
    miss_maple.memes["warmth"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="embarrassment", tag="emotion", apply=_r_embarrassment),
    Rule(name="delivery_relief", tag="emotion", apply=_r_delivery_relief),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "porch": Setting(
        id="porch",
        place="the front porch",
        distance=2,
        breeze=0,
        helper_id="none",
        helper_label="nobody",
        helper_type="thing",
        helper_action="",
        landing="the welcome mat",
        tags={"home"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden gate",
        distance=3,
        breeze=1,
        helper_id="puppy",
        helper_label="the puppy",
        helper_type="animal",
        helper_action="trotted over with the paper airplane hanging from its collar",
        landing="the tulip bed",
        tags={"garden", "pet"},
    ),
    "music_room": Setting(
        id="music_room",
        place="the music room doorway",
        distance=3,
        breeze=0,
        helper_id="robot",
        helper_label="the little robot vacuum",
        helper_type="machine",
        helper_action="whirred in a proud circle and pushed the paper airplane right to Miss Maple's shoe",
        landing="the shiny floor",
        tags={"indoors", "robot"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the end of the hallway",
        distance=4,
        breeze=1,
        helper_id="grandpa",
        helper_label="Grandpa",
        helper_type="grandpa",
        helper_action="picked it up with a grin and carried it the rest of the way like a butler",
        landing="the umbrella stand",
        tags={"home", "grandpa"},
    ),
}

PAPER_STYLES = {
    "rainbow": PaperStyle(
        id="rainbow",
        phrase="a sheet covered in rainbow swirls",
        colors="rainbow swirls",
        doodle="little smiling suns",
        tags={"psychedelic", "color"},
    ),
    "psychedelic": PaperStyle(
        id="psychedelic",
        phrase="a psychedelic page full of loopy stars and twisty flowers",
        colors="psychedelic loops of pink, blue, and orange",
        doodle="goofy dancing mushrooms",
        tags={"psychedelic", "color"},
    ),
    "confetti": PaperStyle(
        id="confetti",
        phrase="a bright sheet speckled like confetti",
        colors="sparkly dots of red, yellow, and green",
        doodle="tiny laughing hearts",
        tags={"color"},
    ),
}

FOLDS = {
    "dart": Fold(
        id="dart",
        label="dart plane",
        power=4,
        wobble=0,
        comic="shot forward so quickly that the child's mouth popped open in surprise",
        tags={"fast"},
    ),
    "glider": Fold(
        id="glider",
        label="glider",
        power=3,
        wobble=0,
        comic="sailed with a slow, proud nose like a duck pretending to be a pilot",
        tags={"gentle"},
    ),
    "floppy": Fold(
        id="floppy",
        label="floppy fold",
        power=2,
        wobble=1,
        comic="flapped its wings twice, as if it had suddenly remembered it was only paper",
        tags={"funny"},
    ),
}

TARGETS = {
    "apron_pocket": Target(
        id="apron_pocket",
        label="apron pocket",
        phrase="Miss Maple's apron pocket",
        distance_bonus=1,
        easy_catch=True,
        tags={"near"},
    ),
    "teacup_table": Target(
        id="teacup_table",
        label="little table",
        phrase="the little table beside Miss Maple",
        distance_bonus=0,
        easy_catch=True,
        tags={"table"},
    ),
    "song_book": Target(
        id="song_book",
        label="song book",
        phrase="the open song book in front of Miss Maple",
        distance_bonus=-1,
        easy_catch=False,
        tags={"far"},
    ),
}

CHILD_NAMES = ["Lila", "Milo", "Nora", "Ben", "Ava", "Finn", "Rosa", "Theo"]
CHILD_TYPES = {
    "Lila": "girl",
    "Milo": "boy",
    "Nora": "girl",
    "Ben": "boy",
    "Ava": "girl",
    "Finn": "boy",
    "Rosa": "girl",
    "Theo": "boy",
}
HELPER_NAMES = ["Pip", "June", "Tess", "Omar", "Ivy", "Kit"]
HELPER_TYPES = {
    "Pip": "boy",
    "June": "girl",
    "Tess": "girl",
    "Omar": "boy",
    "Ivy": "girl",
    "Kit": "boy",
}
TRAITS = ["shy", "gentle", "hopeful", "careful", "bouncy", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for fid, fold in FOLDS.items():
            for tid, target in TARGETS.items():
                if valid_combo(setting, fold, target):
                    combos.append((sid, fid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    paper: str
    fold: str
    target: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
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


CURATED = [
    StoryParams(
        setting="porch",
        paper="psychedelic",
        fold="glider",
        target="apron_pocket",
        child_name="Lila",
        child_type="girl",
        helper_name="Pip",
        helper_type="boy",
        trait="shy",
        seed=1,
    ),
    StoryParams(
        setting="garden",
        paper="rainbow",
        fold="floppy",
        target="teacup_table",
        child_name="Milo",
        child_type="boy",
        helper_name="June",
        helper_type="girl",
        trait="hopeful",
        seed=2,
    ),
    StoryParams(
        setting="music_room",
        paper="confetti",
        fold="floppy",
        target="song_book",
        child_name="Nora",
        child_type="girl",
        helper_name="Omar",
        helper_type="boy",
        trait="careful",
        seed=3,
    ),
    StoryParams(
        setting="hallway",
        paper="psychedelic",
        fold="glider",
        target="song_book",
        child_name="Finn",
        child_type="boy",
        helper_name="Ivy",
        helper_type="girl",
        trait="thoughtful",
        seed=4,
    ),
]


def explain_rejection(setting: Setting, fold: Fold, target: Target) -> str:
    return (
        f"(No story: from {setting.place}, a {fold.label} cannot honestly reach "
        f"{target.phrase}, and there is no plausible rescue path that would still "
        f"deliver the note. Pick a stronger fold, an easier target, or a setting "
        f"with a helper.)"
    )


def predict_flight(setting: Setting, fold: Fold, target: Target) -> dict:
    return {
        "range": plane_range(setting, fold, target),
        "direct": direct_hit_possible(setting, fold, target),
        "helper": helper_rescue_possible(setting, fold, target),
        "outcome": outcome_for(setting, fold, target),
    }


def setup_scene(world: World, child: Entity, pal: Entity, miss_maple: Entity,
                setting: Setting, paper: PaperStyle) -> None:
    child.memes["hope"] += 1
    child.memes["love"] += 1
    pal.memes["care"] += 1
    world.say(
        f"On a soft afternoon, {child.id} sat near {setting.place} with {pal.id} and a note for "
        f"{miss_maple.id}. The note was folded from {paper.phrase}, covered in {paper.colors}, "
        f"and so cheerful it looked almost psychedelic."
    )
    world.say(
        f'"I want it to feel really positive," {child.id} said. "Miss Maple always cheers everyone up. '
        f'I do not want her to miss how thankful I am."'
    )


def write_note(world: World, child: Entity, paper: PaperStyle) -> None:
    plane = world.get("plane")
    plane.attrs["message"] = "You make ordinary afternoons feel brave and bright."
    world.say(
        f"Across one corner, {child.id} added {paper.doodle}. Across the middle, "
        f"{child.pronoun().capitalize()} wrote, \"Thank you for making the day kinder.\""
    )


def plan_throw(world: World, child: Entity, pal: Entity, setting: Setting,
               fold: Fold, target: Target) -> None:
    pred = predict_flight(setting, fold, target)
    world.facts["predicted_range"] = pred["range"]
    world.facts["predicted_outcome"] = pred["outcome"]
    pal.memes["worry"] += 1
    world.say(
        f"{pal.id} helped crease the {fold.label}. \"Aim for {target.phrase},\" "
        f"{pal.pronoun()} whispered."
    )
    if pred["direct"]:
        world.say(
            f"{pal.id} smiled. \"That one should reach just fine,\" {pal.pronoun()} said."
        )
    else:
        world.say(
            f"{pal.id} tilted {pal.pronoun('possessive')} head. \"It might miss on the first try,\" "
            f"{pal.pronoun()} warned, \"but maybe that will not be the end of the story.\""
        )


def launch_direct(world: World, child: Entity, setting: Setting, fold: Fold, target: Target) -> None:
    plane = world.get("plane")
    plane.meters["flown"] += 1
    plane.meters["delivered"] += 1
    child.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} took one brave breath and tossed the plane. It {fold.comic}, "
        f"then slid neatly into {target.phrase}."
    )


def launch_miss(world: World, child: Entity, setting: Setting, fold: Fold, target: Target) -> None:
    plane = world.get("plane")
    plane.meters["flown"] += 1
    plane.meters["missed"] += 1
    child.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} tossed the plane. It {fold.comic}, drifted sideways, and missed "
        f"{target.phrase} by a whisker."
    )
    world.say(
        f"Instead, it landed in {setting.landing}. For one tiny moment, {child.id}'s ears felt hot."
    )


def helper_turn(world: World, child: Entity, pal: Entity, miss_maple: Entity,
                setting: Setting) -> None:
    plane = world.get("plane")
    helper = world.get("setting_helper")
    plane.meters["rescued"] += 1
    plane.meters["delivered"] += 1
    child.memes["laughter"] += 1
    miss_maple.memes["surprise"] += 1
    propagate(world, narrate=False)
    if setting.helper_id == "puppy":
        world.say(
            f"Then {helper.label} {setting.helper_action}. {pal.id} laughed so hard {pal.pronoun()} had to hold "
            f"{pal.pronoun('possessive')} belly."
        )
    elif setting.helper_id == "robot":
        world.say(
            f"Then {helper.label} {setting.helper_action}. The silly little machine bumped once against the wall, "
            f"as if it were bowing for applause."
        )
    else:
        world.say(
            f"Then {helper.label} {setting.helper_action}. Even {child.id} had to laugh at that."
        )
    world.say(
        f"Miss Maple blinked, then smiled as she unfolded the note instead of asking who had planned such a crooked delivery."
    )


def read_and_reply(world: World, child: Entity, miss_maple: Entity, pal: Entity,
                   setting: Setting, outcome: str) -> None:
    child.memes["relief"] += 1
    miss_maple.memes["love"] += 1
    world.say(
        f"She read the kind words slowly, with one hand over her heart. \"Oh,\" she said, "
        f"\"this is the loveliest surprise.\""
    )
    if outcome == "direct":
        world.say(
            f"Miss Maple looked straight at {child.id}. \"A careful note can fly a long way,\" "
            f"she said, and {child.id} stood a little taller."
        )
    else:
        world.say(
            f"\"A funny trip can still carry a true message,\" Miss Maple said. \"Sometimes a miss becomes its own little miracle.\""
        )
    world.say(
        f"She hugged {child.id} first and then squeezed {pal.id}'s shoulder too. After that, the bright plane stayed tucked nearby like a small flag of kindness."
    )


def ending_image(world: World, child: Entity, miss_maple: Entity, setting: Setting,
                 paper: PaperStyle) -> None:
    world.say(
        f"By the end, even the room felt lighter. {miss_maple.id} set the note where everyone could see its "
        f"{paper.colors}, and {child.id} grinned every time the page caught the light."
    )


def tell(setting: Setting, paper: PaperStyle, fold: Fold, target: Target,
         child_name: str, child_type: str, helper_name: str, helper_type: str,
         trait: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=[trait],
        attrs={},
    ))
    pal = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="friend",
        traits=["supportive"],
        attrs={},
    ))
    miss_maple = world.add(Entity(
        id="Miss Maple",
        kind="character",
        type="teacher",
        role="recipient",
        label="Miss Maple",
        attrs={},
    ))
    plane = world.add(Entity(
        id="plane",
        kind="thing",
        type="paper_plane",
        label="paper airplane",
        attrs={"message": ""},
    ))
    helper_ent = world.add(Entity(
        id="setting_helper",
        kind="thing" if setting.helper_type not in {"grandpa"} else "character",
        type=setting.helper_type,
        role="helper",
        label=setting.helper_label,
        attrs={},
    ))

    world.facts["predicted_range"] = 0
    world.facts["predicted_outcome"] = ""
    world.facts["outcome"] = outcome_for(setting, fold, target)
    world.facts["setting"] = setting
    world.facts["paper"] = paper
    world.facts["fold"] = fold
    world.facts["target"] = target
    world.facts["child"] = child
    world.facts["pal"] = pal
    world.facts["miss_maple"] = miss_maple
    world.facts["plane"] = plane
    world.facts["setting_helper"] = helper_ent

    setup_scene(world, child, pal, miss_maple, setting, paper)
    write_note(world, child, paper)

    world.para()
    plan_throw(world, child, pal, setting, fold, target)

    world.para()
    if world.facts["outcome"] == "direct":
        launch_direct(world, child, setting, fold, target)
    else:
        launch_miss(world, child, setting, fold, target)
        helper_turn(world, child, pal, miss_maple, setting)

    world.para()
    read_and_reply(world, child, miss_maple, pal, setting, world.facts["outcome"])
    ending_image(world, child, miss_maple, setting, paper)
    return world


KNOWLEDGE = {
    "paper_plane": [
        (
            "What is a paper airplane?",
            "A paper airplane is a toy plane folded from paper. It can glide through the air when you toss it gently."
        )
    ],
    "psychedelic": [
        (
            "What does psychedelic mean?",
            "Psychedelic means full of wild, bright, swirling colors and shapes. It often looks dreamy, surprising, and a little bit magical."
        )
    ],
    "positive": [
        (
            "What is a positive note?",
            "A positive note is a message with kind, hopeful words. It helps someone feel seen, thanked, or cheered up."
        )
    ],
    "robot": [
        (
            "What is a robot vacuum?",
            "A robot vacuum is a little machine that moves around cleaning the floor by itself. It can look funny because it hums and bumps as it goes."
        )
    ],
    "puppy": [
        (
            "Why do puppies make people laugh?",
            "Puppies move in bouncy, surprising ways, and they often do silly things without meaning to. That makes many moments feel playful."
        )
    ],
    "kindness": [
        (
            "Why do kind words matter?",
            "Kind words can make someone feel noticed and loved. Even a small message can change the mood of a whole day."
        )
    ],
}
KNOWLEDGE_ORDER = ["paper_plane", "psychedelic", "positive", "robot", "puppy", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    fold = f["fold"]
    setting = f["setting"]
    target = f["target"]
    outcome = f["outcome"]
    if outcome == "direct":
        return [
            'Write a heartwarming story for a young child that includes the words "psychedelic", "positive", and "miss".',
            f"Tell a warm, funny story where {child.id} folds a {fold.label} to send a kind note to Miss Maple near {setting.place}, and the throw works beautifully.",
            f"Write a gentle story about a shy child sending a positive paper airplane toward {target.phrase}, ending with a grateful hug."
        ]
    return [
        'Write a heartwarming story for a young child that includes the words "psychedelic", "positive", and "miss", and use a funny twist.',
        f"Tell a warm story where {child.id} tries to send a kind paper airplane to Miss Maple near {setting.place}, but the plane misses and an unexpected helper saves the day.",
        "Write a gentle humorous tale where a child's crooked plan goes wrong in a lovable way, yet the kind message still arrives."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    pal = f["pal"]
    fold = f["fold"]
    setting = f["setting"]
    target = f["target"]
    miss_maple = f["miss_maple"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to send a thankful note to {miss_maple.id}, and {pal.id}, who helped with the plan."
        ),
        (
            "What made the note look special?",
            f"The note was folded from bright paper and covered in wild, cheerful colors. It looked almost psychedelic because the page was full of swirls and funny doodles."
        ),
        (
            f"Why did {child.id} make the note?",
            f"{child.id} wanted to thank {miss_maple.id} for making ordinary days feel kinder. The note was meant to be a small, positive surprise."
        ),
    ]
    if outcome == "direct":
        qa.append(
            (
                f"Did the paper airplane miss {target.phrase}?",
                f"No. The plane flew right into {target.phrase}. That made {child.id} feel relieved right away because the brave little plan worked."
            )
        )
        qa.append(
            (
                f"How did Miss Maple react?",
                f"She read the note slowly and put her hand over her heart. Then she thanked {child.id} warmly and made the child feel proud of being brave."
            )
        )
    else:
        helper = f["setting_helper"]
        qa.append(
            (
                f"What happened when the airplane missed {target.phrase}?",
                f"It drifted away and landed in {setting.landing} instead. That made {child.id} feel embarrassed for a moment because the surprise had gone crooked."
            )
        )
        qa.append(
            (
                "What was the funny twist?",
                f"The note still reached Miss Maple because {helper.label} helped without meaning to. The silly rescue turned the miss into the part everyone laughed about."
            )
        )
        qa.append(
            (
                "Why was the ending still happy?",
                f"Miss Maple cared more about the loving message than the crooked delivery. She even said the funny trip made the kindness feel more real and memorable."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"paper_plane", "positive", "kindness"}
    if "psychedelic" in world.facts["paper"].tags:
        tags.add("psychedelic")
    if world.facts["setting"].helper_id == "robot":
        tags.add("robot")
    if world.facts["setting"].helper_id == "puppy":
        tags.add("puppy")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
reachable(S,F,T) :- setting(S), fold(F), target(T),
                    power(F,P), breeze(S,B), bonus(T,TB), distance(S,D),
                    P - B + TB >= D.
helper_path(S,F,T) :- setting(S), fold(F), target(T),
                      helper(S,H), H != none,
                      power(F,P), breeze(S,B), bonus(T,TB), distance(S,D),
                      P - B + TB >= D - 1.
valid(S,F,T) :- reachable(S,F,T).
valid(S,F,T) :- not reachable(S,F,T), helper_path(S,F,T).

outcome(direct) :- chosen_setting(S), chosen_fold(F), chosen_target(T), reachable(S,F,T).
outcome(helper) :- chosen_setting(S), chosen_fold(F), chosen_target(T),
                   not reachable(S,F,T), helper_path(S,F,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("distance", sid, setting.distance))
        lines.append(asp.fact("breeze", sid, setting.breeze))
        lines.append(asp.fact("helper", sid, setting.helper_id))
    for fid, fold in FOLDS.items():
        lines.append(asp.fact("fold", fid))
        lines.append(asp.fact("power", fid, fold.power))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("bonus", tid, target.distance_bonus))
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
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_fold", params.fold),
        asp.fact("chosen_target", params.target),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A story world about a kind paper airplane for Miss Maple. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--paper", choices=PAPER_STYLES)
    ap.add_argument("--fold", choices=FOLDS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.fold and args.target:
        setting = SETTINGS[args.setting]
        fold = FOLDS[args.fold]
        target = TARGETS[args.target]
        if not valid_combo(setting, fold, target):
            raise StoryError(explain_rejection(setting, fold, target))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.fold is None or combo[1] == args.fold)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, fold_id, target_id = rng.choice(sorted(combos))
    paper_id = args.paper or rng.choice(sorted(PAPER_STYLES))
    child_name = args.name or rng.choice(CHILD_NAMES)
    child_type = CHILD_TYPES[child_name]
    helper_name = rng.choice([n for n in HELPER_NAMES if n != child_name])
    helper_type = HELPER_TYPES[helper_name]
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        paper=paper_id,
        fold=fold_id,
        target=target_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.paper not in PAPER_STYLES:
        raise StoryError(f"(Unknown paper style: {params.paper})")
    if params.fold not in FOLDS:
        raise StoryError(f"(Unknown fold: {params.fold})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if not params.child_name:
        raise StoryError("(Child name must not be empty.)")
    if not valid_combo(SETTINGS[params.setting], FOLDS[params.fold], TARGETS[params.target]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], FOLDS[params.fold], TARGETS[params.target]))

    world = tell(
        setting=SETTINGS[params.setting],
        paper=PAPER_STYLES[params.paper],
        fold=FOLDS[params.fold],
        target=TARGETS[params.target],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed unexpectedly for seed {seed}.")
            break

    bad = 0
    for params in cases:
        py_out = outcome_for(SETTINGS[params.setting], FOLDS[params.fold], TARGETS[params.target])
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # noqa: BLE001
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
        print(f"{len(combos)} valid (setting, fold, target) combos:\n")
        for setting, fold, target in combos:
            print(f"  {setting:10} {fold:8} {target}")
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
            header = f"### {p.child_name}: {p.fold} from {p.setting} toward {p.target}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
