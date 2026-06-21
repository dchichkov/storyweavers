#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sow_contestant_galoshes_happy_ending_tall_tale.py
==================================================================================

A small tall-tale storyworld about a county fair, a giant sow, a contestant in
galoshes, a muddied contest, and a happy ending.

The model keeps the story grounded in state changes: a contestant enters a fair
game, a sow causes a muddy mess, the contestant's galoshes either help or fail
them, and the town responds with a cheerful resolution. The world is simple on
purpose and built around the seed words: sow, contestant, galoshes.

This is a standalone script under ``storyworlds/worlds/``.
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
BRAVERY_INIT = 4.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    wears_galoshes: bool = False
    mudproof: bool = False
    covered_in_mud: bool = False
    lucky: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
    mud_depth: int
    bright_image: str
    crowd_word: str
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


@dataclass
class Creature:
    id: str
    label: str
    size: str
    mudmaker: bool = False
    friendly: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Contest:
    id: str
    name: str
    task: str
    prize: str
    finish_line: str
    crowd_cheer: str
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


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: bool = True
    splashes_off: bool = True
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


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.meters["mud"] < THRESHOLD:
            continue
        if ("mud", ent.id) in world.fired:
            continue
        world.fired.add(("mud", ent.id))
        ent.covered_in_mud = True
        ent.memes["gasp"] += 1
        out.append("__mud__")
    return out


def _r_shine(world: World) -> list[str]:
    if "sow" not in world.entities or "contestant" not in world.entities:
        return []
    sow = world.get("sow")
    contestant = world.get("contestant")
    if sow.meters["mud"] < THRESHOLD or contestant.meters["mud"] < THRESHOLD:
        return []
    if ("shine",) in world.fired:
        return []
    world.fired.add(("shine",))
    contestant.memes["hope"] += 1
    return ["__shine__"]


CAUSAL_RULES = [Rule("mud", _r_mud), Rule("shine", _r_shine)]


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


def reasonableness_gate(contest: Contest, creature: Creature, gear: Gear) -> bool:
    return creature.mudmaker and gear.helps


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def best_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.sense)


def resolve_mud(contest: Contest, creature: Creature, delay: int) -> int:
    return contest_mudness(contest, creature) + delay


def contest_mudness(contest: Contest, creature: Creature) -> int:
    return 2 + (1 if creature.mudmaker else 0)


def can_win(remedy: Remedy, contest: Contest, creature: Creature, delay: int) -> bool:
    return remedy.power >= resolve_mud(contest, creature, delay)


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("sow").meters["mud"] += 1
    sim.get("contestant").meters["mud"] += 1
    propagate(sim, narrate=False)
    return {
        "contestant_muddy": sim.get("contestant").covered_in_mud,
        "sow_muddy": sim.get("sow").covered_in_mud,
    }


def intro(world: World, hero: Entity, contest: Contest, setting: Setting) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In {setting.place}, where the sky looked wide as a storybook, "
        f"{hero.id} entered the {contest.name}. The town called it a {contest.task}, "
        f"and every bell in the square seemed to ring hello."
    )


def tall_tale_hook(world: World, hero: Entity, sow: Creature, setting: Setting) -> None:
    world.say(
        f"Then along came a sow so grand and muddy that her snout seemed to point "
        f"at rainclouds, and her hooves could splash a puddle wider than a wagon wheel."
    )
    world.say(
        f"{hero.id} tugged at {hero.pronoun('possessive')} galoshes and laughed. "
        f'"These boots could march through a moon-sized mud pie!" {hero.pronoun()} said.'
    )
    hero.wears_galoshes = True


def mishap(world: World, hero: Entity, sow: Creature) -> None:
    hero.meters["mud"] += 1
    sow.meters["mud"] += 1
    sow.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The sow stamped once, twice, and the fairground turned to sloshy brown "
        f"spatter. A great splash leaped at {hero.id}, and the contestant's galoshes "
        f"answered the mess like two brave little ships."
    )


def warning(world: World, hero: Entity, setting: Setting, contest: Contest) -> None:
    world.say(
        f"People gasped, but {hero.id} only grinned. {hero.pronoun().capitalize()} "
        f"could still see the finish line glittering under the mud, and the crowd "
        f"held its breath as if the whole town were listening."
    )


def ending(world: World, hero: Entity, sow: Creature, contest: Contest, remedy: Remedy) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.meters["mud"] = 0
    world.get("sow").meters["mud"] = 0
    world.say(
        f"At last, a cheerful helper rolled in a barrel of clean straw and a warm "
        f"bucket of rinse water. {remedy.text.replace('{target}', 'the galoshes')}"
    )
    world.say(
        f"The sow shook herself into a spotless shine, the contestant crossed the "
        f"finish line, and the crowd gave a cheer big enough to shingle the roof."
    )
    world.say(
        f"By sundown, {hero.id} was waving {hero.pronoun('possessive')} galoshes "
        f"over {hero.pronoun('possessive')} head like trophies, and the sow was "
        f"sleeping contentedly beside a ribbon that read {contest.prize}."
    )


def happy_finish(world: World, hero: Entity, sow: Creature, contest: Contest, gear: Gear) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"The contestant's galoshes never gave up, and neither did {hero.id}. "
        f"{hero.pronoun().capitalize()} splashed through the last stretch, waved to "
        f"the sow, and won the day with a grin."
    )
    world.say(
        f"The crowd cheered, the sow snorted a merry goodbye, and the fair closed "
        f"under a bright, gold-laced sunset."
    )


def tell(setting: Setting, creature: Creature, contest: Contest, gear: Gear,
         remedy: Remedy, hero_name: str = "Mabel", hero_type: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, role="contestant",
        label="contestant", wears_galoshes=True, mudproof=True,
        traits=["brave", "cheerful"], attrs={"setting": setting.id}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="helper",
        label="the grown-up"
    ))
    sow = world.add(Entity(
        id="sow", kind="character", type="sow", role="mischief",
        label=creature.label, traits=["grand"], mudproof=False, lucky=True
    ))
    world.facts.update(setting=setting, contest=contest, gear=gear, remedy=remedy)
    intro(world, hero, contest, setting)
    world.para()
    tall_tale_hook(world, hero, sow, setting)
    world.say(f"The {contest.name} was about {contest.task}, and the finish line sat near {setting.bright_image}.")
    world.para()
    mishap(world, hero, sow)
    warning(world, hero, setting, contest)
    world.para()
    if can_win(remedy, contest, creature, delay):
        if gear.helps:
            happy_finish(world, hero, sow, contest, gear)
        ending(world, hero, sow, contest, remedy)
    else:
        world.say("But that wouldn't be a happy ending, so this world refuses the tale.")
    world.facts.update(hero=hero, parent=parent, sow=sow, outcome="happy", delay=delay)
    return world


SETTINGS = {
    "fairgrounds": Setting(
        id="fairgrounds",
        place="the county fairgrounds",
        mud_depth=3,
        bright_image="a row of lanterns and a red prize ribbon",
        crowd_word="crowd",
    ),
    "meadow": Setting(
        id="meadow",
        place="the meadow beside the fair",
        mud_depth=2,
        bright_image="a blue ribbon gate and a straw fence",
        crowd_word="neighbors",
    ),
}

CREATURES = {
    "sow": Creature(id="sow", label="sow", size="big", mudmaker=True, friendly=True),
}

CONTESTS = {
    "muddash": Contest(
        id="muddash",
        name="muddash",
        task="racing through the mud without losing your boots",
        prize="first prize",
        finish_line="the striped ribbon",
        crowd_cheer="Hooray!",
    ),
    "hogsong": Contest(
        id="hogsong",
        name="hog-song contest",
        task="singing a tune while a sow splashed nearby",
        prize="blue ribbon",
        finish_line="the bandstand",
        crowd_cheer="Bravo!",
    ),
}

GEARS = {
    "galoshes": Gear(
        id="galoshes",
        label="galoshes",
        phrase="a pair of tall red galoshes",
        helps=True,
        splashes_off=True,
        tags={"galoshes", "mud"},
    ),
    "boots": Gear(
        id="boots",
        label="boots",
        phrase="sturdy boots",
        helps=True,
        splashes_off=True,
        tags={"boots"},
    ),
}

REMEDIES = {
    "stomp": Remedy(
        id="stomp",
        sense=2,
        power=2,
        text="scrubbed the galoshes clean and set them by the stove until they gleamed again",
        fail="tried to scrub the galoshes clean, but the mud kept laughing",
        qa_text="scrubbed the galoshes clean",
        tags={"cleaning"},
    ),
    "hose": Remedy(
        id="hose",
        sense=3,
        power=4,
        text="hosed off the mud in one shining swoop and lined the galoshes up to dry",
        fail="hosed at the mud, but it clung like a stubborn hymn",
        qa_text="hosed off the mud",
        tags={"cleaning"},
    ),
    "straw": Remedy(
        id="straw",
        sense=4,
        power=5,
        text="rolled out fresh straw and wiped the galoshes until they sparkled like polished apples",
        fail="rolled out straw, but the mud was already too deep",
        qa_text="rolled out fresh straw and wiped the galoshes clean",
        tags={"cleaning"},
    ),
}

GIRL_NAMES = ["Mabel", "Nell", "Ruby", "Dot", "Ivy", "Bea"]
BOY_NAMES = ["Jeb", "Walt", "Roy", "Abe", "Otis", "Bo"]
TRAITS = ["bold", "cheery", "spirited", "merry", "spry", "lively"]


@dataclass
class StoryParams:
    setting: str = "fairgrounds"
    contest: str = "muddash"
    gear: str = "galoshes"
    remedy: str = "hose"
    name: str = "Mabel"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "merry"
    delay: int = 0
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid in CONTESTS:
            for gid, gear in GEARS.items():
                if gear.helps:
                    combos.append((sid, cid, gid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    contest = f["contest"]
    return [
        f'Write a tall-tale style story for a child that includes the words "sow", "contestant", and "galoshes".',
        f"Tell a happy-ending fairground story where {hero.id} the contestant meets a sow in the mud and the galoshes save the day.",
        f"Write a cheerful tall tale about {hero.id} winning {contest.name} at {setting.place} with a muddy sow nearby.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sow = f["sow"]
    contest = f["contest"]
    setting = f["setting"]
    remedy = f["remedy"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a contestant at {setting.place}, and a grand sow that made the day extra muddy."),
        ("What did the contestant wear?",
         f"{hero.id} wore galoshes. They helped {hero.id} splash through the mud without losing heart."),
        ("What was the contest like?",
         f"It was a {contest.name}, with mud, cheering, and a finish line shining like a ribbon in the sun."),
        ("How did the story end?",
         f"It ended happily. The mud got cleaned up, the sow was calm and shiny again, and {hero.id} felt proud."),
        ("What happened to the galoshes?",
         f"They were cleaned by the grown-up after the contest. That way the contestant could keep them ready for the next muddy adventure."),
    ]
    qa.append((
        "Why did the grown-up help?",
        f"The grown-up helped because the mud was deep and the contest got messy. The remedy cleaned the galoshes, so the happy ending could still shine."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set()
    tags |= REMEDIES[world.facts["remedy"].id].tags if world.facts.get("remedy") else set()
    tags |= world.facts["gear"].tags if world.facts.get("gear") else set()
    tags |= {"mud", "galoshes"}
    for tag, items in [
        ("galoshes", [("What are galoshes?", "Galoshes are tall waterproof boots that help keep feet dry in mud and puddles.")]),
        ("mud", [("What is mud?", "Mud is wet dirt. It sticks to shoes, boots, and clothes.")]),
        ("sow", [("What is a sow?", "A sow is a female pig.")]),
    ]:
        if tag in tags:
            out.extend(items)
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
        if e.wears_galoshes:
            bits.append("wears_galoshes=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="fairgrounds", contest="muddash", gear="galoshes", remedy="hose", name="Mabel", gender="girl", parent="mother", trait="merry", delay=0),
    StoryParams(setting="meadow", contest="hogsong", gear="boots", remedy="straw", name="Jeb", gender="boy", parent="father", trait="bold", delay=0),
]


def explain_rejection(gear: Gear) -> str:
    return f"(No story: the chosen gear '{gear.label}' cannot support the happy ending in this world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CONTESTS:
        lines.append(asp.fact("contest", cid))
    for gid, gear in GEARS.items():
        lines.append(asp.fact("gear", gid))
        if gear.helps:
            lines.append(asp.fact("helps", gid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        lines.append(asp.fact("power", rid, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
valid(S,C,G) :- setting(S), contest(C), gear(G), helps(G).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    # smoke test: ordinary generation should not crash
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with a sow, a contestant, and galoshes.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--contest", choices=CONTESTS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gear and args.gear not in GEARS:
        raise StoryError("Unknown gear.")
    gear = GEARS[args.gear] if args.gear else GEARS["galoshes"]
    if not gear.helps:
        raise StoryError(explain_rejection(gear))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.contest is None or c[1] == args.contest)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, contest, gear_id = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, contest=contest, gear=gear_id, remedy=remedy, name=name, gender=gender, parent=parent, trait=trait, delay=args.delay)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.contest not in CONTESTS or params.gear not in GEARS or params.remedy not in REMEDIES:
        raise StoryError("Invalid params.")
    world = tell(
        SETTINGS[params.setting],
        CREATURES["sow"],
        CONTESTS[params.contest],
        GEARS[params.gear],
        REMEDIES[params.remedy],
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        for s, c, g in asp_valid_combos():
            print(f"  {s:10} {c:10} {g}")
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
            header = f"### {p.name}: {p.contest} at {p.setting} ({p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
