#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/excrement_flashback_inner_monologue_pirate_tale.py
================================================================================

A standalone story world for a tiny pirate tale domain built from the seed:
a child pirate game, a rude seabird, a splat of excrement, a remembered lesson,
and a safe cleanup.

This world keeps the tone child-facing and adventurous while grounding the turn
in simulation: a treasured pirate prop is contaminated by bird excrement, the
captain feels disgust and worry, a flashback lesson is triggered, and the chosen
cleanup method either safely cleans the item or sensibly replaces it.

Run it
------
    python storyworlds/worlds/gpt-5.4/excrement_flashback_inner_monologue_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/excrement_flashback_inner_monologue_pirate_tale.py --target map --method damp_cloth
    python storyworlds/worlds/gpt-5.4/excrement_flashback_inner_monologue_pirate_tale.py --target map --method rinse_bucket
    python storyworlds/worlds/gpt-5.4/excrement_flashback_inner_monologue_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/excrement_flashback_inner_monologue_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/excrement_flashback_inner_monologue_pirate_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    washable: bool = False
    replaceable: bool = False
    material: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    sea_detail: str
    bird: str
    helper_place: str
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
    material: str
    washable: bool
    replaceable: bool
    splat_text: str
    clean_end: str
    replace_end: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
    sense: int
    mode: str
    label: str
    works_for: set[str]
    text: str
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
class MemoryLesson:
    id: str
    helper_type: str
    who: str
    flashback_text: str
    lesson_text: str
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
class StoryParams:
    setting: str
    target: str
    method: str
    memory: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_contamination(world: World) -> list[str]:
    out: list[str] = []
    target = world.get("target")
    if target.meters["contaminated"] < THRESHOLD:
        return out
    sig = ("contamination", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["disgust"] += 1
        kid.memes["worry"] += 1
    target.meters["needs_cleaning"] += 1
    out.append("__splat__")
    return out


def _r_flashback(world: World) -> list[str]:
    captain = world.get("captain")
    if captain.memes["worry"] < THRESHOLD:
        return []
    if not captain.attrs.get("remembers_lesson"):
        return []
    sig = ("flashback", captain.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["memory"] += 1
    return ["__flashback__"]


def _r_relief(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["clean"] < THRESHOLD and target.meters["replaced"] < THRESHOLD:
        return []
    sig = ("relief", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["contaminated"] = 0.0
    target.meters["needs_cleaning"] = 0.0
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="contamination", tag="physical", apply=_r_contamination),
    Rule(name="flashback", tag="memory", apply=_r_flashback),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def method_compatible(target: Target, method: Method) -> bool:
    return target.material in method.works_for


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for target_id, target in TARGETS.items():
            for method_id, method in METHODS.items():
                if method.sense < SENSE_MIN:
                    continue
                if method_compatible(target, method):
                    for memory_id in MEMORIES:
                        combos.append((setting_id, target_id, method_id, memory_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    target = TARGETS[params.target]
    method = METHODS[params.method]
    if not method_compatible(target, method):
        return "invalid"
    if method.mode == "replace":
        return "replaced"
    return "cleaned"


def predict_cleanup(target: Target, method: Method) -> dict:
    if method_compatible(target, method):
        return {"kept": True, "outcome": "replaced" if method.mode == "replace" else "cleaned"}
    return {"kept": False, "outcome": "ruined"}


def introduce(world: World, captain: Entity, mate: Entity, target: Target) -> None:
    world.say(
        f"On a bright afternoon by {world.setting.place}, {captain.id} and {mate.id} "
        f"turned driftwood and a striped blanket into a pirate ship. {world.setting.sea_detail}"
    )
    world.say(
        f'"Captain {captain.id}!" {mate.id} cried. "Guard {target.the}! It holds our best clue."'
    )


def cherish(world: World, captain: Entity, target_ent: Entity, target: Target) -> None:
    captain.memes["pride"] += 1
    world.say(
        f"{captain.id} set out {target.phrase} as carefully as if it were real treasure. "
        f"{captain.pronoun().capitalize()} did not want a single thing to spoil it."
    )


def gull_swoops(world: World) -> None:
    bird = world.setting.bird
    world.say(
        f"Then a shadow skimmed over the blanket. A hungry {bird} wheeled once above the mast-stick."
    )


def splat(world: World, target_ent: Entity, target: Target) -> None:
    target_ent.meters["contaminated"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before either child could duck, there came a rude splat. {target.splat_text}."
    )


def inner_monologue(world: World, captain: Entity, target: Target, method: Method) -> None:
    pred = predict_cleanup(target, method)
    world.facts["predicted_kept"] = pred["kept"]
    world.facts["predicted_outcome"] = pred["outcome"]
    if pred["kept"]:
        line = (
            f'"Do not grab that excrement with bare fingers," {captain.id} thought. '
            f'"If I use {method.label}, we can save {target.the} and keep the game going."'
        )
    else:
        line = (
            f'"Oh no," {captain.id} thought. "That would ruin {target.the}. '
            f'I need a gentler pirate plan."'
        )
    world.say(line)


def flashback(world: World, captain: Entity, memory: MemoryLesson) -> None:
    propagate(world, narrate=False)
    if captain.memes["memory"] >= THRESHOLD:
        world.say(
            f"At once {captain.id} remembered {memory.flashback_text}"
        )


def ask_for_help(world: World, captain: Entity, mate: Entity, helper: Entity, memory: MemoryLesson) -> None:
    mate.memes["trust"] += 1
    world.say(
        f'"{helper.label_word.capitalize()}!" {captain.id} called toward {world.setting.helper_place}. '
        f'"We need the clean way, not the quick way."'
    )
    world.say(
        f"{mate.id} nodded hard. {memory.who} had said the same thing before, and now both children believed it."
    )


def clean(world: World, helper: Entity, target_ent: Entity, target: Target, method: Method) -> None:
    if method.mode == "replace":
        target_ent.meters["replaced"] += 1
        target_ent.meters["kept"] += 1
    else:
        target_ent.meters["clean"] += 1
        target_ent.meters["kept"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} came over at once and {method.text}."
    )
    if method.mode == "replace":
        world.say(
            f"The messy one was set aside for washing later, and a fresh pirate prop took its place."
        )
    else:
        world.say(
            f"Soon the mess was gone, and nobody had to touch the excrement with bare hands."
        )


def finish_story(world: World, captain: Entity, mate: Entity, target: Target, outcome: str) -> None:
    if outcome == "replaced":
        world.say(
            f"{target.replace_end} {captain.id} lifted it high, and {mate.id} cheered as if they had won a chest of gold."
        )
    else:
        world.say(
            f"{target.clean_end} {captain.id} grinned, and {mate.id} tapped the blanket deck with happy little boots."
        )
    world.say(
        "The pirate ship sailed on, this time with clean hands, wiser hearts, and a treasure game that felt safe again."
    )


def tell(
    setting: Setting,
    target: Target,
    method: Method,
    memory: MemoryLesson,
    captain_name: str = "Nora",
    captain_gender: str = "girl",
    mate_name: str = "Finn",
    mate_gender: str = "boy",
    trait: str = "careful",
) -> World:
    world = World(setting)
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        traits=[trait, "bold"],
        attrs={"remembers_lesson": True},
    ))
    mate = world.add(Entity(
        id="mate",
        kind="character",
        type=mate_gender,
        label=mate_name,
        role="mate",
        traits=["eager"],
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=memory.helper_type,
        label=memory.who,
        role="helper",
        attrs={},
    ))
    target_ent = world.add(Entity(
        id="target",
        kind="thing",
        type=target.id,
        label=target.label,
        phrase=target.phrase,
        owner="captain",
        washable=target.washable,
        replaceable=target.replaceable,
        material=target.material,
        attrs={},
    ))

    world.facts.update(
        captain=captain,
        mate=mate,
        helper=helper,
        target_cfg=target,
        method=method,
        memory=memory,
        setting=setting,
        predicted_kept=False,
        predicted_outcome="",
    )

    introduce(world, captain, mate, target)
    cherish(world, captain, target_ent, target)
    world.para()

    gull_swoops(world)
    splat(world, target_ent, target)
    inner_monologue(world, captain, target, method)
    flashback(world, captain, memory)
    ask_for_help(world, captain, mate, helper, memory)
    world.para()

    clean(world, helper, target_ent, target, method)
    finish_story(world, captain, mate, target, outcome_of(StoryParams(
        setting=setting.id,
        target=target.id,
        method=method.id,
        memory=memory.id,
        captain=captain_name,
        captain_gender=captain_gender,
        mate=mate_name,
        mate_gender=mate_gender,
        trait=trait,
        seed=None,
    )))

    world.facts.update(
        contaminated=target_ent.meters["contaminated"] >= THRESHOLD,
        outcome="replaced" if target_ent.meters["replaced"] >= THRESHOLD else "cleaned",
        target_ent=target_ent,
        flashback_triggered=captain.memes["memory"] >= THRESHOLD,
        lesson_used=True,
    )
    return world


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="the little cove",
        sea_detail="Foamy waves whispered against the stones, and a line of shells glittered like coins",
        bird="gull",
        helper_place="the picnic basket",
        tags={"shore", "gull"},
    ),
    "pier": Setting(
        id="pier",
        place="the old pier",
        sea_detail="Ropes creaked, and the water slapped the pilings below like tiny pirate drums",
        bird="tern",
        helper_place="the bait box",
        tags={"dock", "seabird"},
    ),
    "dunes": Setting(
        id="dunes",
        place="the windy dunes",
        sea_detail="The grass bent in the salt breeze, and the sea shone blue beyond the sand hills",
        bird="gull",
        helper_place="the striped umbrella",
        tags={"sand", "gull"},
    ),
}

TARGETS = {
    "map": Target(
        id="map",
        label="treasure map",
        phrase="their crinkly treasure map",
        material="paper",
        washable=True,
        replaceable=True,
        splat_text="A blob of bird excrement landed right across the red X on the treasure map",
        clean_end="The map lay flat again, its red X still bright and brave",
        replace_end="A fresh map fluttered where the spoiled one had been",
        tags={"map", "paper"},
    ),
    "flag": Target(
        id="flag",
        label="pirate flag",
        phrase="their black pirate flag",
        material="cloth",
        washable=True,
        replaceable=True,
        splat_text="A streak of bird excrement slid down the pirate flag and spotted the white skull",
        clean_end="The flag snapped in the breeze, black and clean once more",
        replace_end="A spare flag rose on the mast-stick, crisp and flappy in the wind",
        tags={"flag", "cloth"},
    ),
    "hat": Target(
        id="hat",
        label="captain hat",
        phrase="the captain hat with the crooked paper feather",
        material="straw",
        washable=True,
        replaceable=False,
        splat_text="A nasty dab of bird excrement plopped onto the brim of the captain hat",
        clean_end="The hat sat proud on the captain's head again, feather wobbling like a tiny sail",
        replace_end="The hat was back in service",
        tags={"hat", "straw"},
    ),
    "chest": Target(
        id="chest",
        label="treasure chest lid",
        phrase="the painted lid of their treasure chest",
        material="wood",
        washable=True,
        replaceable=False,
        splat_text="A splash of bird excrement hit the treasure chest lid and ran into the gold paint",
        clean_end="The chest gleamed once more, ready to guard shells and sea glass",
        replace_end="The chest was ready again",
        tags={"chest", "wood"},
    ),
}

METHODS = {
    "damp_cloth": Method(
        id="damp_cloth",
        sense=3,
        mode="clean",
        label="a damp cloth and careful hands",
        works_for={"paper", "cloth", "straw", "wood"},
        text="took a damp cloth, wiped the mess away in small careful strokes, and then helped the children wash their hands",
        qa_text="used a damp cloth and careful wiping to clean it safely",
        tags={"cloth", "wash_hands"},
    ),
    "rinse_bucket": Method(
        id="rinse_bucket",
        sense=3,
        mode="clean",
        label="a little rinse bucket",
        works_for={"cloth", "wood"},
        text="poured a little clean water over it and rinsed the mess away before it could dry",
        qa_text="rinsed it with clean water",
        tags={"water", "wash_hands"},
    ),
    "spare_prop": Method(
        id="spare_prop",
        sense=2,
        mode="replace",
        label="the spare pirate box",
        works_for={"paper", "cloth"},
        text="opened the spare pirate box and brought out a clean replacement while the dirty one was wrapped away",
        qa_text="replaced it with a clean spare one",
        tags={"replacement", "wash_hands"},
    ),
    "bare_hand": Method(
        id="bare_hand",
        sense=1,
        mode="bad",
        label="bare hands",
        works_for=set(),
        text="tried to brush it away with bare fingers",
        qa_text="touched it with bare hands",
        tags={"unsafe"},
    ),
}

MEMORIES = {
    "aunt_marina": MemoryLesson(
        id="aunt_marina",
        helper_type="aunt",
        who="Aunt Marina",
        flashback_text="the day before, when Aunt Marina had knelt by the tide pool and said, \"If a bird leaves excrement on something, do not rub it with your hands. Call me, and we will clean it the calm way.\"",
        lesson_text="Do not touch bird excrement with bare hands. Ask a grown-up and clean it the calm way.",
        tags={"germs", "ask_adult"},
    ),
    "dad_joel": MemoryLesson(
        id="dad_joel",
        helper_type="father",
        who="Dad Joel",
        flashback_text="yesterday on the dock, when Dad Joel had pointed at a bench and said, \"Bird excrement can be full of germs. We use water or a cloth, and then we wash our hands.\"",
        lesson_text="Bird excrement can have germs, so use a safe cleanup and wash hands after.",
        tags={"germs", "wash_hands"},
    ),
    "uncle_rae": MemoryLesson(
        id="uncle_rae",
        helper_type="uncle",
        who="Uncle Rae",
        flashback_text="a windy morning when Uncle Rae had laughed softly and said, \"A good pirate never snatches at a dirty mess. A good pirate gets help and keeps the crew safe.\"",
        lesson_text="A careful pirate gets help and keeps the crew safe.",
        tags={"ask_adult", "safety"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Zoe", "Ava", "Lucy", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Finn", "Leo", "Jack", "Theo", "Max", "Eli", "Noah", "Sam"]
TRAITS = ["careful", "steady", "thoughtful", "brave", "watchful"]


KNOWLEDGE = {
    "germs": [
        (
            "Why should you not touch bird excrement with bare hands?",
            "Bird excrement can have germs in it. A grown-up should help clean it, and then everyone should wash their hands."
        )
    ],
    "wash_hands": [
        (
            "Why do people wash their hands after something dirty gets on them?",
            "Washing hands helps remove dirt and germs. That keeps the mess from spreading to faces, food, or toys."
        )
    ],
    "map": [
        (
            "What is a treasure map?",
            "A treasure map is a pretend or real drawing that shows where treasure might be hidden. In pirate games, it helps children imagine where to search next."
        )
    ],
    "flag": [
        (
            "What is a pirate flag?",
            "A pirate flag is a cloth sign pirates flew on their ships in stories. In play, it helps a pretend ship feel real and exciting."
        )
    ],
    "water": [
        (
            "When is water useful for cleaning?",
            "Water helps wash away many messes from strong materials like cloth or wood. But delicate things, like paper, may need a gentler way."
        )
    ],
    "replacement": [
        (
            "Why is replacing a dirty prop sometimes a good idea?",
            "If something is too delicate or too messy to keep using right away, a clean spare one lets the game continue safely. Then the dirty thing can be cleaned later by a grown-up."
        )
    ],
}
KNOWLEDGE_ORDER = ["germs", "wash_hands", "map", "flag", "water", "replacement"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    target = f["target_cfg"]
    method = f["method"]
    setting = f["setting"]
    return [
        f'Write a short pirate tale for a 3-to-5-year-old that includes the word "excrement", uses a flashback, and includes inner monologue.',
        f"Tell a gentle beach pirate story where {captain.label} and {mate.label} are playing at {setting.place}, a bird messes up {target.the}, and the children remember a safety lesson.",
        f"Write a child-facing story in a pirate-tale style where a treasured prop is saved with {method.label} after a seabird leaves excrement on it."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    helper = f["helper"]
    target = f["target_cfg"]
    method = f["method"]
    memory = f["memory"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {captain.label} and {mate.label}, pretending to be pirates by {f['setting'].place}. Their helper, {helper.label}, is part of the story too because that grown-up helps them solve the mess safely."
        ),
        (
            f"What spoiled {target.the}?",
            f"A seabird dropped excrement on {target.the}. That nasty splat changed the game at once because the children could not safely keep using it the same way."
        ),
        (
            f"What did {captain.label} think when the mess landed?",
            f"{captain.label} had an inner monologue and told {captain.pronoun('object')}self not to grab the excrement with bare fingers. {captain.pronoun().capitalize()} was trying to protect {target.the} and keep everyone safe."
        ),
        (
            "What was the flashback about?",
            f"The flashback was about a lesson from {memory.who}. In that remembered moment, the grown-up explained that bird excrement should be handled calmly and safely instead of being touched with bare hands."
        ),
        (
            "How did they solve the problem?",
            f"They asked {helper.label} for help, and {helper.pronoun()} {method.qa_text}. That worked because it was a sensible way to deal with the dirty mess without spreading it."
        ),
    ]
    if outcome == "replaced":
        qa.append(
            (
                f"Was {target.the} cleaned or replaced?",
                f"It was replaced with a clean spare one. The dirty one was set aside for later, which let the pirate game go on without the children using the messy prop."
            )
        )
    else:
        qa.append(
            (
                f"How did the story end?",
                f"{target.clean_end} The ending shows that the children learned from the flashback and used a safe plan, so the pirate game could continue happily."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["memory"].tags) | set(f["method"].tags) | set(f["target_cfg"].tags)
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
        if e.material:
            bits.append(f"material={e.material}")
        if e.washable:
            bits.append("washable=True")
        if e.replaceable:
            bits.append("replaceable=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_method_rejection(target: Target, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: '{method.id}' is known to the world but refused because touching excrement with bare hands is not a sensible fix. "
            f"Pick a safer method like damp_cloth, rinse_bucket, or spare_prop.)"
        )
    return (
        f"(No story: {method.label} does not fit {target.the}. "
        f"{target.the.capitalize()} is made of {target.material}, so this cleanup would not preserve it safely.)"
    )


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
compatible(T, M) :- target(T), material(T, Mat), works_for(M, Mat).
valid(S, T, M, Mem) :- setting(S), target(T), method(M), memory(Mem), sensible(M), compatible(T, M).

outcome(cleaned)  :- chosen_target(T), chosen_method(M), compatible(T, M), mode(M, clean).
outcome(replaced) :- chosen_target(T), chosen_method(M), compatible(T, M), mode(M, replace).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("material", tid, target.material))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("mode", mid, method.mode))
        for mat in sorted(method.works_for):
            lines.append(asp.fact("works_for", mid, mat))
    for mem in MEMORIES:
        lines.append(asp.fact("memory", mem))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


CURATED = [
    StoryParams(
        setting="cove",
        target="map",
        method="damp_cloth",
        memory="aunt_marina",
        captain="Nora",
        captain_gender="girl",
        mate="Finn",
        mate_gender="boy",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        setting="pier",
        target="flag",
        method="rinse_bucket",
        memory="dad_joel",
        captain="Theo",
        captain_gender="boy",
        mate="Mia",
        mate_gender="girl",
        trait="steady",
        seed=None,
    ),
    StoryParams(
        setting="dunes",
        target="map",
        method="spare_prop",
        memory="uncle_rae",
        captain="Lucy",
        captain_gender="girl",
        mate="Max",
        mate_gender="boy",
        trait="thoughtful",
        seed=None,
    ),
    StoryParams(
        setting="cove",
        target="hat",
        method="damp_cloth",
        memory="dad_joel",
        captain="Jack",
        captain_gender="boy",
        mate="Rose",
        mate_gender="girl",
        trait="watchful",
        seed=None,
    ),
    StoryParams(
        setting="pier",
        target="chest",
        method="rinse_bucket",
        memory="aunt_marina",
        captain="Ava",
        captain_gender="girl",
        mate="Leo",
        mate_gender="boy",
        trait="brave",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pirate game, a rude bird, excrement, a flashback lesson, and a safe cleanup."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.method:
        target = TARGETS[args.target]
        method = METHODS[args.method]
        if not method_compatible(target, method) or method.sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(target, method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.target is None or combo[1] == args.target)
        and (args.method is None or combo[2] == args.method)
        and (args.memory is None or combo[3] == args.memory)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, target_id, method_id, memory_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    mate_gender = rng.choice(["girl", "boy"])
    captain = _pick_name(rng, captain_gender)
    mate = _pick_name(rng, mate_gender, avoid=captain)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        target=target_id,
        method=method_id,
        memory=memory_id,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")

    target = TARGETS[params.target]
    method = METHODS[params.method]
    if method.sense < SENSE_MIN or not method_compatible(target, method):
        raise StoryError(explain_method_rejection(target, method))

    world = tell(
        setting=SETTINGS[params.setting],
        target=target,
        method=method,
        memory=MEMORIES[params.memory],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
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
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed on seed {seed}")
            break

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches.append((params, py, asp))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py, asp in mismatches[:5]:
            print(" ", params, py, asp)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, target, method, memory) combos:\n")
        for setting_id, target_id, method_id, memory_id in combos:
            print(f"  {setting_id:7} {target_id:6} {method_id:12} {memory_id}")
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
            header = f"### {p.captain} & {p.mate}: {p.target} with {p.method} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
