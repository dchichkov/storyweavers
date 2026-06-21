#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/non_pomp_businessman_mystery_to_solve_ghost.py
=========================================================================

A standalone story world for a child-friendly ghost-story mystery:
a child meets a very grand businessman in an old place, something spooky seems
to be haunting the building, and careful clues reveal an ordinary cause.

The domain is built to satisfy a "Mystery to Solve" shape:
- eerie sign
- a pompous guess about a ghost
- grounded clue gathering
- a concrete reveal
- an ending image that proves the place feels different after the mystery is solved

Run it
------
python storyworlds/worlds/gpt-5.4/non_pomp_businessman_mystery_to_solve_ghost.py
python storyworlds/worlds/gpt-5.4/non_pomp_businessman_mystery_to_solve_ghost.py --setting inn --mystery whisper
python storyworlds/worlds/gpt-5.4/non_pomp_businessman_mystery_to_solve_ghost.py --cause mirror_moon --setting clock_shop
python storyworlds/worlds/gpt-5.4/non_pomp_businessman_mystery_to_solve_ghost.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/non_pomp_businessman_mystery_to_solve_ghost.py --all
python storyworlds/worlds/gpt-5.4/non_pomp_businessman_mystery_to_solve_ghost.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "woman"}
        male = {"boy", "man", "businessman"}
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
class Setting:
    id: str
    label: str
    room: str
    opening: str
    spooky_corner: str
    ending_warmth: str
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
class Mystery:
    id: str
    label: str
    onset: str
    scare_line: str
    question: str
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
class Cause:
    id: str
    label: str
    kind: str
    settings: set[str]
    mysteries: set[str]
    clues: list[str]
    reveal_text: str
    explain_text: str
    fix_text: str
    ending_image: str
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
class Clue:
    id: str
    label: str
    find_text: str
    infer_text: str
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


def _r_mystery_rises(world: World) -> list[str]:
    place = world.get("place")
    cause = world.get("cause")
    child = world.get("child")
    businessman = world.get("businessman")
    mystery_id = world.facts["mystery_id"]
    if cause.meters["active"] < THRESHOLD:
        return []
    sig = ("mystery", mystery_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters[mystery_id] += 1
    place.meters["uncanny"] += 1
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    businessman.memes["fear"] += 1
    businessman.memes["pomp"] += 1
    return ["__mystery__"]


def _r_clues_make_certainty(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["clues_found"] < 2:
        return []
    sig = ("certainty",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["certainty"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    return ["__certainty__"]


def _r_solution_calms(world: World) -> list[str]:
    place = world.get("place")
    child = world.get("child")
    businessman = world.get("businessman")
    cause = world.get("cause")
    if cause.meters["solved"] < THRESHOLD:
        return []
    sig = ("calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["uncanny"] = 0.0
    for mid in MYSTERIES:
        place.meters[mid] = 0.0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    businessman.memes["relief"] += 1
    businessman.memes["gratitude"] += 1
    businessman.memes["pomp"] = max(0.0, businessman.memes["pomp"] - 2)
    return ["__calm__"]


CAUSAL_RULES = [
    Rule(name="mystery_rises", tag="physical", apply=_r_mystery_rises),
    Rule(name="clues_make_certainty", tag="epistemic", apply=_r_clues_make_certainty),
    Rule(name="solution_calms", tag="social", apply=_r_solution_calms),
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


SETTINGS = {
    "inn": Setting(
        id="inn",
        label="the Moonlit Inn",
        room="the long front hall",
        opening="The sea air pressed softly at the windows, and every old board seemed ready to tell a secret.",
        spooky_corner="the salt-dark vent by the stairs",
        ending_warmth="lamplight gleamed on the polished banister",
        tags={"inn", "old_building", "night"},
    ),
    "clock_shop": Setting(
        id="clock_shop",
        label="Brass Bell Clock Shop",
        room="the room of ticking clocks",
        opening="Tall clocks stood shoulder to shoulder, and their tiny ticks made the quiet feel deeper.",
        spooky_corner="the swinging sign outside the front window",
        ending_warmth="the clocks ticked like calm little hearts",
        tags={"shop", "clocks", "night"},
    ),
    "conservatory": Setting(
        id="conservatory",
        label="the glass conservatory",
        room="the fern room",
        opening="Moonlight rested on the glass roof, and the leaves made long green shadows on the floor.",
        spooky_corner="the tall mirror beside the lemon tree",
        ending_warmth="dew shone on the leaves like silver beads",
        tags={"glass", "plants", "night"},
    ),
    "guild_hall": Setting(
        id="guild_hall",
        label="the old guild hall",
        room="the echoing gallery",
        opening="Painted beams crossed high overhead, and each whisper came back sounding older than before.",
        spooky_corner="the narrow side passage and rafters",
        ending_warmth="the gallery looked grand in a kinder way",
        tags={"hall", "rafters", "night"},
    ),
}

MYSTERIES = {
    "whisper": Mystery(
        id="whisper",
        label="whispering in the walls",
        onset="a hushy whisper came slipping through the room",
        scare_line='"A ghost is talking in there,"',
        question="What was making the whispering sound?",
        tags={"ghost", "sound", "mystery"},
    ),
    "footsteps": Mystery(
        id="footsteps",
        label="soft footsteps overhead",
        onset="soft steps padded overhead where no one should have been",
        scare_line='"Something is walking above us,"',
        question="Who or what was making the footsteps?",
        tags={"ghost", "steps", "mystery"},
    ),
    "glow": Mystery(
        id="glow",
        label="a pale glow with no lamp",
        onset="a pale glow slid across the dark room even though no lamp was lit",
        scare_line='"There is a lantern with nobody holding it,"',
        question="What made the strange glow?",
        tags={"ghost", "light", "mystery"},
    ),
    "chime": Mystery(
        id="chime",
        label="a bell chiming by itself",
        onset="a lonely bell gave one bright ring all by itself",
        scare_line='"A spirit is ringing the bell,"',
        question="What was making the bell chime?",
        tags={"ghost", "bell", "mystery"},
    ),
}

CLUES = {
    "cold_draft": Clue(
        id="cold_draft",
        label="a cold draft",
        find_text="A thin ribbon of cold air touched the child's cheek.",
        infer_text="Air could travel where a ghost could be blamed.",
        tags={"air", "draft"},
    ),
    "open_grille": Clue(
        id="open_grille",
        label="an open grille",
        find_text="Behind a coat stand, the child found an old brass grille standing slightly open.",
        infer_text="An opening in the wall could turn wind into a whisper.",
        tags={"wall", "vent"},
    ),
    "paw_print": Clue(
        id="paw_print",
        label="a dusty paw print",
        find_text="On the stair rail sat a neat dusty paw print, as round as a coin.",
        infer_text="A small animal had been walking where people thought no one could walk.",
        tags={"animal", "paw"},
    ),
    "orange_fur": Clue(
        id="orange_fur",
        label="a tuft of orange fur",
        find_text="A soft tuft of orange fur clung to a splinter near the rafters.",
        infer_text="Fur meant feet, and feet meant the mystery was alive, not magical.",
        tags={"animal", "fur"},
    ),
    "silver_beam": Clue(
        id="silver_beam",
        label="a silver beam",
        find_text="A narrow silver beam slid over the floor and landed on the child's shoe.",
        infer_text="Light had come from somewhere real and straight.",
        tags={"light", "moon"},
    ),
    "crooked_mirror": Clue(
        id="crooked_mirror",
        label="a crooked mirror",
        find_text="The tall mirror leaned at a funny angle, as if someone had bumped it.",
        infer_text="A tilted mirror could toss moonlight across the room.",
        tags={"light", "mirror"},
    ),
    "rust_flakes": Clue(
        id="rust_flakes",
        label="tiny rust flakes",
        find_text="Tiny rust flakes glittered on the window ledge like brown crumbs.",
        infer_text="Metal had been rubbing and shaking somewhere nearby.",
        tags={"metal", "rust"},
    ),
    "swaying_shadow": Clue(
        id="swaying_shadow",
        label="a swaying shadow",
        find_text="On the wall, the child noticed a long shadow swaying back and forth with the wind.",
        infer_text="Something outside was moving enough to ring or knock.",
        tags={"shadow", "wind"},
    ),
}

CAUSES = {
    "sea_draft": Cause(
        id="sea_draft",
        label="a sea draft rushing through an old speaking tube",
        kind="repair",
        settings={"inn", "guild_hall"},
        mysteries={"whisper"},
        clues=["cold_draft", "open_grille"],
        reveal_text="Inside the wall waited an old speaking tube. Wind from outside ran through it and whispered into the hall.",
        explain_text="It had sounded ghostly only because the building was old and hollow in just the right way.",
        fix_text="The businessman fetched felt and a screwdriver, and together they closed the loose grille so the wind could not hiss through anymore.",
        ending_image="After that, the hall held only a sleepy hush and the faraway sound of the sea.",
        tags={"air", "repair", "ghost_story"},
    ),
    "attic_cat": Cause(
        id="attic_cat",
        label="a marmalade cat in the rafters",
        kind="rescue",
        settings={"inn", "clock_shop", "guild_hall"},
        mysteries={"footsteps"},
        clues=["paw_print", "orange_fur"],
        reveal_text="Up in the rafters crouched a marmalade cat with bright eyes and careful paws.",
        explain_text="The soft footsteps had belonged to a hungry little climber, not a ghost at all.",
        fix_text="The businessman set down a saucer of milk and opened the loft door, and the cat came padding out with a rusty bell caught on its collar.",
        ending_image="Soon the cat curled by the stove, and every sound in the room felt friendly.",
        tags={"animal", "rescue", "ghost_story"},
    ),
    "mirror_moon": Cause(
        id="mirror_moon",
        label="moonlight bouncing from a tilted mirror",
        kind="repair",
        settings={"conservatory", "guild_hall"},
        mysteries={"glow"},
        clues=["silver_beam", "crooked_mirror"],
        reveal_text="Moonlight had been striking the crooked mirror and bouncing in one pale bar across the room.",
        explain_text="From far away it looked like a floating lantern, but it was only light taking a strange path.",
        fix_text="The businessman straightened the mirror and wedged one leg with folded felt until it stood still and true.",
        ending_image="Then the moon rested quietly on the glass instead of creeping through the room.",
        tags={"light", "repair", "ghost_story"},
    ),
    "loose_chain": Cause(
        id="loose_chain",
        label="a loose brass chain on the outside sign",
        kind="repair",
        settings={"inn", "clock_shop"},
        mysteries={"chime"},
        clues=["rust_flakes", "swaying_shadow"],
        reveal_text="Outside, the sign chain bumped the brass bell each time the wind gave it a nudge.",
        explain_text="The ring had sounded lonely because it came in single bright notes through the dark.",
        fix_text="The businessman climbed the step stool, tightened the chain, and wrapped the bell hook so it could not tap by mistake.",
        ending_image="After that, the shop kept its proper quiet, broken only by warm ticking and low voices.",
        tags={"metal", "repair", "ghost_story"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Elsie", "Tessa", "June", "Ruby", "Mabel"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Jasper", "Finn", "Hugo", "Eli", "Rowan"]
CHILD_TRAITS = ["careful", "curious", "patient", "bright", "steady", "thoughtful"]
BUSINESSMAN_NAMES = ["Mr. Vale", "Mr. Crimp", "Mr. Flint", "Mr. Thorne", "Mr. Bell"]
BUSINESSMAN_TRAITS = ["grand", "fussy", "showy", "stiff", "booming"]


def valid_combo(setting_id: str, mystery_id: str, cause_id: str) -> bool:
    if setting_id not in SETTINGS or mystery_id not in MYSTERIES or cause_id not in CAUSES:
        return False
    cause = CAUSES[cause_id]
    return setting_id in cause.settings and mystery_id in cause.mysteries


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for mystery_id in MYSTERIES:
            for cause_id in CAUSES:
                if valid_combo(setting_id, mystery_id, cause_id):
                    combos.append((setting_id, mystery_id, cause_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    cause: str
    clue1: str
    clue2: str
    child_name: str
    child_gender: str
    child_trait: str
    businessman_name: str
    businessman_trait: str
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


def explain_rejection(setting_id: str, mystery_id: str, cause_id: str) -> str:
    if cause_id not in CAUSES:
        return f"(No story: unknown cause '{cause_id}'.)"
    if mystery_id not in MYSTERIES:
        return f"(No story: unknown mystery '{mystery_id}'.)"
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    cause = CAUSES[cause_id]
    parts: list[str] = []
    if setting_id not in cause.settings:
        parts.append(
            f"{cause.label} does not fit {SETTINGS[setting_id].label}"
        )
    if mystery_id not in cause.mysteries:
        parts.append(
            f"{cause.label} would not make {MYSTERIES[mystery_id].label}"
        )
    joined = " and ".join(parts) if parts else "the combination is unreasonable"
    return f"(No story: {joined}. Pick a setting, mystery, and cause that truly belong together.)"


def outcome_of(params: StoryParams) -> str:
    if params.cause not in CAUSES:
        return "?"
    return CAUSES[params.cause].kind


def predict_mystery(world: World, mystery_id: str) -> dict:
    sim = world.copy()
    sim.get("cause").meters["active"] += 1
    propagate(sim, narrate=False)
    return {
        "present": sim.get("place").meters[mystery_id] >= THRESHOLD,
        "fear_child": sim.get("child").memes["fear"],
        "fear_businessman": sim.get("businessman").memes["fear"],
    }


def introduce(world: World, child: Entity, businessman: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    businessman.memes["pomp"] += 2
    world.say(
        f"One windy evening, {child.id} stepped into {setting.label} with a pocket notebook and a brave little lamp."
    )
    world.say(setting.opening)
    world.say(
        f"There {child.pronoun()} met {businessman.id}, a businessman in a velvet coat. "
        f"He carried so much pomp that even the tassel on his cane seemed to stand up straighter."
    )


def first_sign(world: World, child: Entity, businessman: Entity, setting: Setting, mystery: Mystery) -> None:
    pred = predict_mystery(world, mystery.id)
    world.facts["predicted_present"] = pred["present"]
    world.facts["predicted_fear_child"] = pred["fear_child"]
    world.facts["predicted_fear_businessman"] = pred["fear_businessman"]
    world.get("cause").meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"While they stood in {setting.room}, {mystery.onset}"
    )
    world.say(
        f'{businessman.id} froze. {mystery.scare_line} he said in a grand whisper.'
    )


def boast_and_worry(world: World, child: Entity, businessman: Entity, setting: Setting, mystery: Mystery) -> None:
    extra = ""
    if businessman.memes["pomp"] >= 2:
        extra = " He lifted one hand as if he were about to make a speech to the moon."
    world.say(
        f'"I run this place with perfect order," {businessman.id} declared. '
        f'"No ghost may prance through my rooms with such rude manners."{extra}'
    )
    world.say(
        f"{child.id} felt a flutter in {child.pronoun('possessive')} tummy, but curiosity tugged harder than fear."
    )
    world.say(
        f'{child.pronoun("possessive").capitalize()} notebook had two little boxes on the first page: "ghost" and "non-ghost." '
        f'{child.pronoun().capitalize()} tapped the second box with the pencil.'
    )


def discover_clue(world: World, child: Entity, clue: Clue, index: int) -> None:
    child.meters["clues_found"] += 1
    child.attrs.setdefault("clues_seen", []).append(clue.id)
    propagate(world, narrate=False)
    lead = "First" if index == 1 else "Then"
    world.say(f"{lead}, {clue.find_text}")
    world.say(f"{child.id} crouched down and thought. {clue.infer_text}")


def connect_clues(world: World, child: Entity, businessman: Entity, setting: Setting) -> None:
    if child.memes["certainty"] < THRESHOLD:
        raise StoryError("The child does not have enough evidence to solve the mystery.")
    world.say(
        f"{child.id} looked from one clue to the next and then toward {setting.spooky_corner}."
    )
    world.say(
        f'"It is not time to run," {child.pronoun()} said. "It is time to look one step farther."'
    )
    businessman.memes["trust"] += 1
    world.say(
        f"For the first time, {businessman.id} lowered his voice and followed quietly behind."
    )


def reveal(world: World, child: Entity, businessman: Entity, cause: Cause) -> None:
    cause_ent = world.get("cause")
    cause_ent.meters["solved"] += 1
    propagate(world, narrate=False)
    world.say(cause.reveal_text)
    world.say(cause.explain_text)
    if cause.kind == "rescue":
        world.say(
            f'{businessman.id} blinked. "So that was our ghost?" he said, sounding more sorry than scared.'
        )
    else:
        world.say(
            f'{businessman.id} blinked. "So that was our ghost?" he said, and his big pomp folded smaller all at once.'
        )


def fix_and_change(world: World, child: Entity, businessman: Entity, setting: Setting, cause: Cause) -> None:
    world.say(cause.fix_text)
    if cause.kind == "rescue":
        world.say(
            f'"Thank you for looking kindly instead of loudly," {businessman.id} told {child.id}.'
        )
    else:
        world.say(
            f'"Thank you for looking closely instead of guessing grandly," {businessman.id} told {child.id}.'
        )
    child.memes["trust"] += 1
    businessman.memes["humility"] += 1
    world.say(
        f"After that, {setting.ending_warmth}, and {cause.ending_image}"
    )


def closing(world: World, child: Entity, businessman: Entity, mystery: Mystery) -> None:
    if businessman.memes["pomp"] < 1:
        world.say(
            f'{businessman.id} gave a sheepish smile. "I think the ghost can retire," he said.'
        )
    world.say(
        f'{child.id} drew a neat circle around the "non-ghost" box and answered {mystery.question.lower()} with a satisfied nod.'
    )


def tell(
    setting: Setting,
    mystery: Mystery,
    cause: Cause,
    clue1: Clue,
    clue2: Clue,
    child_name: str = "Lina",
    child_gender: str = "girl",
    child_trait: str = "curious",
    businessman_name: str = "Mr. Vale",
    businessman_trait: str = "grand",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label="the child",
            traits=[child_trait],
            attrs={"clues_seen": []},
        )
    )
    businessman = world.add(
        Entity(
            id=businessman_name,
            kind="character",
            type="businessman",
            role="businessman",
            label="the businessman",
            traits=[businessman_trait],
            attrs={"title": "owner"},
        )
    )
    place = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=setting.label,
            attrs={"setting_id": setting.id},
        )
    )
    cause_ent = world.add(
        Entity(
            id="cause",
            kind="thing",
            type="cause",
            label=cause.label,
            attrs={"cause_id": cause.id},
        )
    )

    world.facts["setting"] = setting
    world.facts["mystery_cfg"] = mystery
    world.facts["mystery_id"] = mystery.id
    world.facts["cause_cfg"] = cause
    world.facts["clues"] = [clue1, clue2]
    world.facts["child"] = child
    world.facts["businessman"] = businessman
    world.facts["outcome"] = cause.kind

    introduce(world, child, businessman, setting)
    world.para()
    first_sign(world, child, businessman, setting, mystery)
    boast_and_worry(world, child, businessman, setting, mystery)
    world.para()
    discover_clue(world, child, clue1, 1)
    discover_clue(world, child, clue2, 2)
    connect_clues(world, child, businessman, setting)
    world.para()
    reveal(world, child, businessman, cause)
    fix_and_change(world, child, businessman, setting, cause)
    closing(world, child, businessman, mystery)

    world.facts["solved"] = world.get("cause").meters["solved"] >= THRESHOLD
    world.facts["clue_count"] = int(world.get("child").meters["clues_found"])
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky kind of story that makes a place feel strange and mysterious. In stories for children, the scary thing is often explained in the end.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something puzzling that people do not understand yet. You solve it by noticing clues and thinking carefully about what they mean.",
        )
    ],
    "draft": [
        (
            "What is a draft in an old building?",
            "A draft is a moving stream of air that slips through cracks or openings. It can whistle or hiss and make a room sound spooky.",
        )
    ],
    "mirror": [
        (
            "How can a mirror make a strange light?",
            "A mirror can bounce light from one place to another. If the mirror is tilted, the light can slide across a room and look surprising.",
        )
    ],
    "cat": [
        (
            "Why can a cat sound spooky in a dark place?",
            "A cat can make soft footsteps, bright eye-shines, and small bumps in the dark. If you cannot see the cat yet, those sounds can feel mysterious.",
        )
    ],
    "bell": [
        (
            "Why might a bell ring by itself?",
            "A bell can ring if wind shakes the thing attached to it. It may sound magical at first, but a moving chain or hook can be the real cause.",
        )
    ],
    "businessman": [
        (
            "What is a businessman?",
            "A businessman is a man whose work is running a shop, company, or other business. In stories, a businessman may care a lot about keeping things in order.",
        )
    ],
    "pomp": [
        (
            "What does pomp mean?",
            "Pomp means showy grandness, like acting extra important with fancy words or gestures. It can look impressive, but it does not help you solve a mystery.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small piece of information that helps you understand something bigger. When clues fit together, they can point to the truth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "mystery", "clue", "businessman", "pomp", "draft", "mirror", "cat", "bell"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    businessman = world.facts["businessman"]
    setting = world.facts["setting"]
    mystery = world.facts["mystery_cfg"]
    cause = world.facts["cause_cfg"]
    return [
        f'Write a child-friendly ghost story with a mystery to solve in {setting.label}, and include the words "non", "pomp", and "businessman".',
        f"Tell a spooky-but-gentle story where {child.id} notices clues, while {businessman.id}, a businessman full of pomp, first thinks a ghost is making {mystery.label}.",
        f"Write a story set in {setting.label} where a frightening sign turns out to be {cause.label}, and end with the place feeling safe and changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    businessman = world.facts["businessman"]
    setting = world.facts["setting"]
    mystery = world.facts["mystery_cfg"]
    cause = world.facts["cause_cfg"]
    clue1, clue2 = world.facts["clues"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a careful child with a notebook, and {businessman.id}, a businessman who runs {setting.label}. They begin the story feeling uneasy because something spooky seems to be happening in the building.",
        ),
        (
            f"What mystery did they have to solve in {setting.label}?",
            f"They had to solve the mystery of {mystery.label}. It seemed ghostly at first because the strange sign came suddenly through the dark room.",
        ),
        (
            f"Why did {businessman.id} think there was a ghost?",
            f"{businessman.id} heard or saw the strange sign before he knew its cause, so he jumped to a ghost idea. His pomp also made him speak grandly before anyone had checked the clues.",
        ),
        (
            f"What clues helped {child.id} solve the mystery?",
            f"{child.id} noticed {clue1.label} and {clue2.label}. Those clues mattered because together they pointed toward something real in the building instead of anything magical.",
        ),
        (
            f"How was the mystery solved?",
            f"{cause.reveal_text} {cause.explain_text}",
        ),
    ]
    if outcome == "rescue":
        qa.append(
            (
                f"How did the ending show that the place was safe again?",
                f"The ending became warm and friendly after the hidden animal was helped. {cause.ending_image} That new calm feeling proved the mystery had been solved.",
            )
        )
    else:
        qa.append(
            (
                f"How did {businessman.id} change by the end?",
                f"He stopped guessing grandly and listened to careful evidence instead. After the fix, his pomp shrank and he thanked {child.id} for looking closely.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "mystery", "clue", "businessman", "pomp"}
    cause = world.facts["cause_cfg"]
    for tag in cause.tags:
        if tag == "air":
            tags.add("draft")
        elif tag == "light":
            tags.add("mirror")
        elif tag == "animal":
            tags.add("cat")
        elif tag == "metal":
            tags.add("bell")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="inn",
        mystery="whisper",
        cause="sea_draft",
        clue1="cold_draft",
        clue2="open_grille",
        child_name="Nora",
        child_gender="girl",
        child_trait="curious",
        businessman_name="Mr. Vale",
        businessman_trait="grand",
    ),
    StoryParams(
        setting="clock_shop",
        mystery="footsteps",
        cause="attic_cat",
        clue1="paw_print",
        clue2="orange_fur",
        child_name="Theo",
        child_gender="boy",
        child_trait="patient",
        businessman_name="Mr. Crimp",
        businessman_trait="showy",
    ),
    StoryParams(
        setting="conservatory",
        mystery="glow",
        cause="mirror_moon",
        clue1="silver_beam",
        clue2="crooked_mirror",
        child_name="Mira",
        child_gender="girl",
        child_trait="bright",
        businessman_name="Mr. Flint",
        businessman_trait="stiff",
    ),
    StoryParams(
        setting="clock_shop",
        mystery="chime",
        cause="loose_chain",
        clue1="rust_flakes",
        clue2="swaying_shadow",
        child_name="Owen",
        child_gender="boy",
        child_trait="steady",
        businessman_name="Mr. Bell",
        businessman_trait="booming",
    ),
    StoryParams(
        setting="guild_hall",
        mystery="footsteps",
        cause="attic_cat",
        clue1="paw_print",
        clue2="orange_fur",
        child_name="Ruby",
        child_gender="girl",
        child_trait="thoughtful",
        businessman_name="Mr. Thorne",
        businessman_trait="fussy",
    ),
]


ASP_RULES = r"""
valid(S, M, C) :- setting(S), mystery(M), cause(C), fits_setting(C, S), makes(C, M).

outcome(C, rescue) :- cause_kind(C, rescue).
outcome(C, repair) :- cause_kind(C, repair).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_kind", cid, cause.kind))
        for sid in sorted(cause.settings):
            lines.append(asp.fact("fits_setting", cid, sid))
        for mid in sorted(cause.mysteries):
            lines.append(asp.fact("makes", cid, mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(cause_id: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("chosen_cause", cause_id), "#show outcome/2."))
    outcomes = asp.atoms(model, "outcome")
    for cid, kind in outcomes:
        if cid == cause_id:
            return kind
    return "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    outcome_bad = []
    for cid in CAUSES:
        if outcome_of(
            StoryParams(
                setting=next(iter(CAUSES[cid].settings)),
                mystery=next(iter(CAUSES[cid].mysteries)),
                cause=cid,
                clue1=CAUSES[cid].clues[0],
                clue2=CAUSES[cid].clues[1],
                child_name="Test",
                child_gender="girl",
                child_trait="curious",
                businessman_name="Mr. Vale",
                businessman_trait="grand",
            )
        ) != asp_outcome(cid):
            outcome_bad.append(cid)
    if not outcome_bad:
        print("OK: outcome model matches Python for every cause.")
    else:
        rc = 1
        print("MISMATCH in outcomes:", sorted(outcome_bad))

    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story mystery world: a child follows clues, and a pompous businessman learns to look closely."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--businessman-name", choices=BUSINESSMAN_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery and args.cause and not valid_combo(args.setting, args.mystery, args.cause):
        raise StoryError(explain_rejection(args.setting, args.mystery, args.cause))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        if (args.mystery is None or combo[1] == args.mystery)
        if (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, cause_id = rng.choice(sorted(combos))
    cause = CAUSES[cause_id]
    clue1, clue2 = rng.sample(cause.clues, 2)
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    child_trait = rng.choice(CHILD_TRAITS)
    businessman_name = args.businessman_name or rng.choice(BUSINESSMAN_NAMES)
    businessman_trait = rng.choice(BUSINESSMAN_TRAITS)
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        cause=cause_id,
        clue1=clue1,
        clue2=clue2,
        child_name=child_name,
        child_gender=gender,
        child_trait=child_trait,
        businessman_name=businessman_name,
        businessman_trait=businessman_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.mystery, params.cause):
        raise StoryError(explain_rejection(params.setting, params.mystery, params.cause))
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(No story: unknown mystery '{params.mystery}'.)")
    cause = CAUSES[params.cause]
    if params.clue1 not in cause.clues or params.clue2 not in cause.clues or params.clue1 == params.clue2:
        raise StoryError("(No story: the chosen clues do not honestly support this cause.)")
    if params.clue1 not in CLUES or params.clue2 not in CLUES:
        raise StoryError("(No story: unknown clue id.)")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("(No story: child gender must be 'girl' or 'boy'.)")

    world = tell(
        setting=SETTINGS[params.setting],
        mystery=MYSTERIES[params.mystery],
        cause=cause,
        clue1=CLUES[params.clue1],
        clue2=CLUES[params.clue2],
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
        businessman_name=params.businessman_name,
        businessman_trait=params.businessman_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, cause) combos:\n")
        for setting_id, mystery_id, cause_id in combos:
            print(f"  {setting_id:13} {mystery_id:10} {cause_id}")
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
            header = f"### {p.child_name}: {p.mystery} at {p.setting} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
