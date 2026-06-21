#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py
==============================================================

A standalone storyworld for a humorous folk-tale quest set in an auditorium.

In this little world, a child must recover the missing drum beater before a
festival can begin in the village auditorium. The beater may be stuck in the
rafters, lost under the stage, or trapped inside a locked music cupboard. A
helper and a retrieval trick must genuinely fit the problem. Once the beater is
found, the old festival drum booms out a ridiculous sound, and the whole hall
changes from worried silence to laughter.

Run it
------
    python storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py
    python storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py --obstacle rafters
    python storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py --helper caretaker
    python storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py --json
    python storyworlds/worlds/gpt-5.4/auditorium_humor_quest_folk_tale.py --verify
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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Hall:
    id: str
    phrase: str
    town: str
    festival: str
    drum_name: str
    ending_image: str
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
class Obstacle:
    id: str
    location: str
    need: str
    detail: str
    search_line: str
    success_line: str
    mishap_line: str
    difficulty: int
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
class Trick:
    id: str
    label: str
    action: str
    result: str
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
class Helper:
    id: str
    label: str
    type: str
    skills: set[str]
    entrance: str
    funny_line: str
    humor: int
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
    def __init__(self, hall: Hall) -> None:
        self.hall = hall
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
        clone = World(self.hall)
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


def _r_missing_worry(world: World) -> list[str]:
    beater = world.get("beater")
    elder = world.get("elder")
    hall = world.get("hall")
    hero = world.get("hero")
    if beater.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["worry"] += 1
    hero.memes["duty"] += 1
    hall.meters["silence"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    beater = world.get("beater")
    elder = world.get("elder")
    helper = world.get("helper")
    if beater.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["worry"] = 0.0
    elder.memes["relief"] += 1
    helper.memes["pride"] += 1
    return []


def _r_drum_laughs(world: World) -> list[str]:
    drum = world.get("drum")
    hall = world.get("hall")
    hero = world.get("hero")
    helper = world.get("helper")
    elder = world.get("elder")
    if drum.meters["struck"] < THRESHOLD or world.get("beater").meters["found"] < THRESHOLD:
        return []
    sig = ("drum_laughs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["silence"] = 0.0
    hall.meters["festival_ready"] += 1
    hall.memes["mirth"] += 1 + world.facts.get("humor_bonus", 0)
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    elder.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="found_relief", tag="social", apply=_r_found_relief),
    Rule(name="drum_laughs", tag="social", apply=_r_drum_laughs),
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
                produced.extend(sents)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(obstacle: Obstacle, helper: Helper, trick: Trick) -> bool:
    return obstacle.need == trick.id and trick.id in helper.skills


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hall_id in HALLS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for helper_id, helper in HELPERS.items():
                for trick_id, trick in TRICKS.items():
                    if valid_combo(obstacle, helper, trick):
                        combos.append((hall_id, obstacle_id, helper_id, trick_id))
    return combos


def laughter_kind(obstacle: Obstacle, helper: Helper) -> str:
    score = helper.humor + (1 if obstacle.id in {"under_stage", "cupboard"} else 0)
    return "roaring" if score >= 3 else "warm"


def predict_success(world: World, obstacle: Obstacle, helper: Helper, trick: Trick) -> dict:
    sim = world.copy()
    can = valid_combo(obstacle, helper, trick)
    if can:
        sim.get("beater").meters["found"] += 1
        sim.facts["humor_bonus"] = 1 if laughter_kind(obstacle, helper) == "roaring" else 0
        sim.get("drum").meters["struck"] += 1
        propagate(sim, narrate=False)
    return {
        "can_retrieve": can,
        "festival_ready": sim.get("hall").meters["festival_ready"],
        "mirth": sim.get("hall").memes["mirth"],
    }


def introduce(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"In {world.hall.town}, people said the old auditorium had beams as high as a pine grove "
        f"and echoes as round as bread loaves. On the morning of {world.hall.festival}, "
        f"{hero.id} came there early and found {elder.id} walking in worried little circles."
    )


def explain_problem(world: World, hero: Entity, elder: Entity) -> None:
    hall = world.hall
    world.say(
        f'"Child," said {elder.id}, "our {hall.drum_name} will not sing tonight. '
        f'Its beater is missing, and without its first boom the benches will stay still '
        f'and the lamps will look lonely."'
    )
    world.say(
        f"{hero.id} looked across the empty seats, the dim stage, and the long red curtains. "
        f"A silent auditorium felt wrong, as if a feast had forgotten its soup."
    )


def accept_quest(world: World, hero: Entity) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'"Then I will look for it," said {hero.id}. {hero.pronoun().capitalize()} was small, '
        f"but the brave are often the first to step into a quiet room."
    )


def meet_helper(world: World, helper: Helper) -> None:
    world.say(helper.entrance)
    world.say(helper.funny_line)


def search(world: World, obstacle: Obstacle) -> None:
    world.say(obstacle.search_line)
    world.say(obstacle.detail)


def warn_plan(world: World, hero: Entity, helper: Helper, obstacle: Obstacle, trick: Trick) -> None:
    pred = predict_success(world, obstacle, helper, trick)
    world.facts["predicted_ready"] = pred["festival_ready"]
    world.facts["predicted_mirth"] = pred["mirth"]
    world.say(
        f'{hero.id} studied the trouble and whispered, "If we use {trick.label}, we can reach the beater." '
        f"{helper.label.capitalize()} nodded, for that was work {helper.pronoun('object') if hasattr(helper, 'pronoun') else 'they'} knew well."
    )


def retrieve(world: World, obstacle: Obstacle, helper_cfg: Helper, trick: Trick) -> None:
    beater = world.get("beater")
    helper = world.get("helper")
    beater.meters["missing"] = 0.0
    beater.meters["found"] += 1
    beater.attrs["place"] = "hero's hands"
    world.facts["retrieval_place"] = obstacle.location
    world.facts["humor_bonus"] = 1 if laughter_kind(obstacle, helper_cfg) == "roaring" else 0
    helper.memes["mischief"] += float(helper_cfg.humor)
    world.say(
        f"Together they {trick.action}, and {obstacle.success_line} "
        f"Soon the beater was safe at last."
    )
    world.say(obstacle.mishap_line)
    propagate(world, narrate=False)


def strike_drum(world: World, hero: Entity, elder: Entity, helper_cfg: Helper, obstacle: Obstacle) -> None:
    drum = world.get("drum")
    drum.meters["struck"] += 1
    propagate(world, narrate=False)
    sound = "BWOOMP-hee!" if laughter_kind(obstacle, helper_cfg) == "roaring" else "Bwoom!"
    world.say(
        f"{hero.id} carried the beater to the stage. {elder.id} lifted one hand, "
        f"the lamps were lit, and {hero.id} struck the {world.hall.drum_name}. "
        f"It answered with a splendid sound: {sound}"
    )
    if laughter_kind(obstacle, helper_cfg) == "roaring":
        world.say(
            "The note came out so grand and so crooked at the same time that the first row giggled, "
            "the second row snorted, and soon the whole hall bent with roaring laughter."
        )
    else:
        world.say(
            "The note rolled along the benches like a cheerful barrel, and smiles opened all across the hall."
        )


def close_story(world: World, hero: Entity, elder: Entity, helper_cfg: Helper) -> None:
    world.say(
        f'{elder.id} pressed a warm honey cake into {hero.id}\'s hand and said, '
        f'"A quest that saves a feast is good. A quest that saves a feast and makes people laugh is better."'
    )
    world.say(
        f"From that evening on, when people in {world.hall.town} spoke of courage, they also spoke of laughter, "
        f"for {hero.id} and {helper_cfg.label} had taught them that a glad heart can wake even an old auditorium."
    )
    world.say(world.hall.ending_image)


def tell(
    hall: Hall,
    obstacle: Obstacle,
    helper_cfg: Helper,
    trick: Trick,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_name: str = "Old Bren",
    elder_gender: str = "man",
) -> World:
    world = World(hall)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder", label=elder_name))
    helper = world.add(
        Entity(
            id=helper_cfg.label.title(),
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            attrs={"helper_id": helper_cfg.id},
        )
    )
    beater = world.add(
        Entity(
            id="beater",
            kind="thing",
            type="beater",
            label="drum beater",
            attrs={"place": obstacle.location},
        )
    )
    drum = world.add(Entity(id="drum", kind="thing", type="drum", label=hall.drum_name))
    hall_ent = world.add(Entity(id="hall", kind="thing", type="auditorium", label="auditorium"))

    beater.meters["missing"] = 1.0
    beater.meters["found"] = 0.0
    drum.meters["struck"] = 0.0
    hall_ent.meters["silence"] = 0.0
    hall_ent.meters["festival_ready"] = 0.0
    hall_ent.memes["mirth"] = 0.0
    hero.memes["bravery"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["duty"] = 0.0
    helper.memes["mischief"] = 0.0
    elder.memes["worry"] = 0.0
    elder.memes["joy"] = 0.0

    world.facts.update(
        hall=hall,
        obstacle=obstacle,
        helper_cfg=helper_cfg,
        trick=trick,
        hero=hero,
        elder=elder,
        helper=helper,
        beater=beater,
        humor_bonus=0,
        outcome=laughter_kind(obstacle, helper_cfg),
    )

    propagate(world, narrate=False)

    introduce(world, hero, elder)
    explain_problem(world, hero, elder)
    accept_quest(world, hero)

    world.para()
    meet_helper(world, helper_cfg)
    search(world, obstacle)
    warn_plan(world, hero, helper_cfg, obstacle, trick)

    world.para()
    retrieve(world, obstacle, helper_cfg, trick)
    strike_drum(world, hero, elder, helper_cfg, obstacle)

    world.para()
    close_story(world, hero, elder, helper_cfg)
    return world


HALLS = {
    "village": Hall(
        id="village",
        phrase="the village auditorium",
        town="Willow Reed",
        festival="the Lantern Feast",
        drum_name="Drum of Merriment",
        ending_image="And under the painted ceiling of the auditorium, the laughter bobbed up and down like bright paper lanterns on a river.",
        tags={"auditorium", "festival"},
    ),
    "school": Hall(
        id="school",
        phrase="the school auditorium",
        town="Thimble Glen",
        festival="the Apple Moon Fair",
        drum_name="Drum of Glad News",
        ending_image="By the time the candles burned low, the auditorium rafters seemed to be smiling down with the people below.",
        tags={"auditorium", "festival"},
    ),
    "town": Hall(
        id="town",
        phrase="the town auditorium",
        town="Mossy Bridge",
        festival="the Harvest Supper",
        drum_name="Drum of First Cheer",
        ending_image="So the old auditorium, which had begun the day as solemn as a boot, ended it ringing with cheerful voices and clapping hands.",
        tags={"auditorium", "festival"},
    ),
}

OBSTACLES = {
    "rafters": Obstacle(
        id="rafters",
        location="the rafters above the stage",
        need="climb",
        detail="There, high above the stage, the beater had caught between two dark beams like a stubborn little bird.",
        search_line="They searched along the stage and then looked up, and up again.",
        success_line="the helper reached the beam and shook the beater loose into a waiting curtain",
        mishap_line="On the way down, the ladder squeaked so loudly that it sounded like three ducks trying to sing in harmony, and even Old Bren had to cover a smile.",
        difficulty=2,
        tags={"rafters", "high"},
    ),
    "under_stage": Obstacle(
        id="under_stage",
        location="under the stage",
        need="sweep",
        detail="Beneath the stage lay shadows, old programs, and dust as soft as flour. Somewhere in that gray nest, the beater had rolled away.",
        search_line="They knelt at the lip of the stage and peered into the dark under it.",
        success_line="they whisked the dust aside until the beater rolled out like a shy sausage from a pantry",
        mishap_line="A cloud of dust flew into the helper's nose, and the sneeze that followed was so huge that two sparrows burst from the curtains in alarm.",
        difficulty=1,
        tags={"stage", "dust"},
    ),
    "cupboard": Obstacle(
        id="cupboard",
        location="the locked music cupboard",
        need="unlock",
        detail="At the back of the auditorium stood the old music cupboard, swollen by damp and cross as a miser. Inside, something knocked faintly whenever the door was nudged.",
        search_line="They followed a tiny thumping sound to the music cupboard at the back wall.",
        success_line="the rusty door sprang wide and the beater tumbled out wrapped in a trumpet banner",
        mishap_line="The door also flung out a long forgotten comic wig, which landed on Old Bren's head so neatly that the rows of empty seats seemed ready to laugh before the people even arrived.",
        difficulty=2,
        tags={"cupboard", "lock"},
    ),
}

TRICKS = {
    "climb": Trick(
        id="climb",
        label="a ladder",
        action="set up a ladder and climbed carefully into the high dimness",
        result="reach high places",
        tags={"ladder", "height"},
    ),
    "sweep": Trick(
        id="sweep",
        label="a long broom",
        action="lay flat and pushed a long broom into the dusty shadows",
        result="draw hidden things out",
        tags={"broom", "dust"},
    ),
    "unlock": Trick(
        id="unlock",
        label="a brass key",
        action="fitted a brass key into the stubborn lock and leaned with all their patience",
        result="open locked things",
        tags={"key", "lock"},
    ),
}

HELPERS = {
    "usher": Helper(
        id="usher",
        label="the nimble usher",
        type="woman",
        skills={"climb"},
        entrance="Just then the nimble usher came skipping down the aisle with a feather duster tucked behind one ear.",
        funny_line='"If the beater has climbed higher than I have, then it deserves the view," she said.',
        humor=1,
        tags={"usher", "ladder"},
    ),
    "fiddler": Helper(
        id="fiddler",
        label="the skinny fiddler",
        type="man",
        skills={"sweep"},
        entrance="From behind a velvet curtain popped the skinny fiddler, carrying a broom as if it were another instrument.",
        funny_line='"I cannot play dust," he said, "but I can certainly chase it."',
        humor=2,
        tags={"fiddler", "broom"},
    ),
    "caretaker": Helper(
        id="caretaker",
        label="the jingling caretaker",
        type="man",
        skills={"unlock"},
        entrance="From the side door came the jingling caretaker, with so many keys at his belt that he sounded like a walking wind chime.",
        funny_line='"Every lock has a secret, and every secret gets tired of being kept," he said.',
        humor=2,
        tags={"caretaker", "key"},
    ),
    "stagehand": Helper(
        id="stagehand",
        label="the long-armed stagehand",
        type="man",
        skills={"climb"},
        entrance="The long-armed stagehand stepped from the wings, rolling his sleeves as calmly as if he had all day to borrow the sky.",
        funny_line='"If it is hiding up high, I will ask it to come down politely," he said.',
        humor=1,
        tags={"stagehand", "ladder"},
    ),
}


GIRL_NAMES = ["Mira", "Tessa", "Lina", "Nora", "Pia", "Anya"]
BOY_NAMES = ["Ivo", "Milo", "Tobin", "Eli", "Ned", "Oren"]
ELDER_NAMES = ["Old Bren", "Aunt Sella", "Master Rowan", "Granny Vale"]


@dataclass
class StoryParams:
    hall: str
    obstacle: str
    helper: str
    trick: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
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
        hall="village",
        obstacle="rafters",
        helper="usher",
        trick="climb",
        hero="Mira",
        hero_gender="girl",
        elder="Old Bren",
        elder_gender="man",
    ),
    StoryParams(
        hall="school",
        obstacle="under_stage",
        helper="fiddler",
        trick="sweep",
        hero="Tobin",
        hero_gender="boy",
        elder="Granny Vale",
        elder_gender="woman",
    ),
    StoryParams(
        hall="town",
        obstacle="cupboard",
        helper="caretaker",
        trick="unlock",
        hero="Lina",
        hero_gender="girl",
        elder="Master Rowan",
        elder_gender="man",
    ),
    StoryParams(
        hall="village",
        obstacle="rafters",
        helper="stagehand",
        trick="climb",
        hero="Ivo",
        hero_gender="boy",
        elder="Aunt Sella",
        elder_gender="woman",
    ),
]


KNOWLEDGE = {
    "auditorium": [
        (
            "What is an auditorium?",
            "An auditorium is a big room where many people can sit together to listen, watch, sing, or celebrate. It usually has rows of seats and a stage at the front."
        )
    ],
    "festival": [
        (
            "Why do people gather for a festival?",
            "People gather for a festival to share food, songs, games, and stories. Festivals help a town feel together and joyful."
        )
    ],
    "rafters": [
        (
            "What are rafters?",
            "Rafters are long beams high under a roof. They help hold the roof up, and they are far above people's heads."
        )
    ],
    "stage": [
        (
            "What is a stage?",
            "A stage is the raised place at the front where people perform, speak, or play music. Everyone else watches from the seats."
        )
    ],
    "lock": [
        (
            "What does a key do?",
            "A key opens a lock when it is the right shape. It lets you open doors or cupboards that are meant to stay shut."
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps you reach places that are high above the ground. People should use one carefully so they do not fall."
        )
    ],
    "broom": [
        (
            "What can a broom do besides sweep a floor?",
            "A broom can also reach under places that are hard to get to with your hands. It can push or pull light things out."
        )
    ],
    "drum": [
        (
            "How does a drum make a sound?",
            "A drum makes a sound when something strikes its tight top. The top vibrates and sends the sound out into the air."
        )
    ],
    "laughter": [
        (
            "Why do people laugh together?",
            "People laugh together when something sounds or looks funny and safe. Shared laughter can make everyone feel lighter and closer."
        )
    ],
}
KNOWLEDGE_ORDER = ["auditorium", "festival", "rafters", "stage", "lock", "ladder", "broom", "drum", "laughter"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    hall = world.facts["hall"]
    obstacle = world.facts["obstacle"]
    helper = world.facts["helper_cfg"]
    trick = world.facts["trick"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old about a child in an auditorium who goes on a quest to recover a missing drum beater before {hall.festival}.',
        f"Tell a humorous quest story where {hero.id} searches for a lost beater in {obstacle.location} and gets help from {helper.label} using {trick.label}.",
        f'Write a warm folk-style story that includes the word "auditorium" and ends with a whole town laughing together after a brave child solves a festival problem.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    hall = world.facts["hall"]
    obstacle = world.facts["obstacle"]
    helper_cfg = world.facts["helper_cfg"]
    trick = world.facts["trick"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who goes on a quest in the auditorium, and {elder.id}, who is worried about the coming festival. {helper_cfg.label.capitalize()} also helps when the search becomes hard."
        ),
        (
            "What problem did the child need to solve?",
            f"The festival drum could not be played because its beater was missing. Without that first sound, the auditorium would have stayed quiet and the feast could not begin properly."
        ),
        (
            "Where was the missing beater?",
            f"It was in {obstacle.location}. That hiding place mattered because it could not be reached by ordinary grabbing."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} worked with {helper_cfg.label} and used {trick.label}. That plan fit the problem, so they could reach the beater safely and bring it back to the stage."
        ),
        (
            "Why did people laugh at the end?",
            f"When the drum was finally struck, the sound came out in a funny way, and there had already been a silly mishap during the search. The trouble changed into joy, so the whole hall laughed together."
        ),
    ]
    if outcome == "roaring":
        qa.append(
            (
                "Was the ending quiet or noisy?",
                "It was very noisy in a happy way. The search ended with a big comic moment, and the drum's crooked boom made the laughter spread across the whole auditorium."
            )
        )
    else:
        qa.append(
            (
                "How did the mood change by the end?",
                "At first the hall felt worried and still because the festival could not begin. By the end it felt warm and bright, because the quest succeeded and the drum brought smiles back."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["hall"].tags)
    obstacle = world.facts["obstacle"]
    trick = world.facts["trick"]
    tags |= set(obstacle.tags)
    tags |= set(trick.tags)
    tags |= {"drum", "laughter"}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obstacle_id: str, helper_id: str, trick_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    helper = HELPERS[helper_id]
    trick = TRICKS[trick_id]
    if obstacle.need != trick.id:
        return (
            f"(No story: {trick.label} does not solve a beater lost in {obstacle.location}. "
            f"This obstacle needs {TRICKS[obstacle.need].label} instead.)"
        )
    return (
        f"(No story: {helper.label} does not know how to use {trick.label} for this quest. "
        f"Choose a helper whose skills fit the problem.)"
    )


def outcome_of(params: StoryParams) -> str:
    return laughter_kind(OBSTACLES[params.obstacle], HELPERS[params.helper])


ASP_RULES = r"""
valid(H,O,He,T) :- hall(H), obstacle(O), helper(He), trick(T), needs(O,T), knows(He,T).

laughter_score(O,He,S) :- helper_humor(He,H), dusty_bonus(O,B), S = H + B.
dusty_bonus(under_stage,1).
dusty_bonus(cupboard,1).
dusty_bonus(rafters,0).

outcome(He,O,roaring) :- laughter_score(O,He,S), S >= 3.
outcome(He,O,warm) :- laughter_score(O,He,S), S < 3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hall_id in HALLS:
        lines.append(asp.fact("hall", hall_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_humor", helper_id, helper.humor))
        for skill in sorted(helper.skills):
            lines.append(asp.fact("knows", helper_id, skill))
    for trick_id in TRICKS:
        lines.append(asp.fact("trick", trick_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_obstacle", params.obstacle),
            "picked_outcome(X) :- chosen_helper(H), chosen_obstacle(O), outcome(H,O,X).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A humorous folk-tale quest in an auditorium. Unspecified choices are picked at random from valid combinations."
    )
    ap.add_argument("--hall", choices=HALLS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.helper and args.trick:
        if not valid_combo(OBSTACLES[args.obstacle], HELPERS[args.helper], TRICKS[args.trick]):
            raise StoryError(explain_rejection(args.obstacle, args.helper, args.trick))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hall is None or combo[0] == args.hall)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
        and (args.trick is None or combo[3] == args.trick)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hall_id, obstacle_id, helper_id, trick_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(
        hall=hall_id,
        obstacle=obstacle_id,
        helper=helper_id,
        trick=trick_id,
        hero=hero,
        hero_gender=gender,
        elder=elder,
        elder_gender=elder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hall not in HALLS:
        raise StoryError(f"(Unknown hall: {params.hall})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.trick not in TRICKS:
        raise StoryError(f"(Unknown trick: {params.trick})")

    hall = HALLS[params.hall]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    trick = TRICKS[params.trick]
    if not valid_combo(obstacle, helper, trick):
        raise StoryError(explain_rejection(params.obstacle, params.helper, params.trick))

    world = tell(
        hall=hall,
        obstacle=obstacle,
        helper_cfg=helper,
        trick=trick,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        elder_name=params.elder,
        elder_gender=params.elder_gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hall, obstacle, helper, trick) combos:\n")
        for hall_id, obstacle_id, helper_id, trick_id in combos:
            print(f"  {hall_id:8} {obstacle_id:12} {helper_id:10} {trick_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero}: {p.obstacle} in {p.hall} hall with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
