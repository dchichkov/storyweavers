#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bug_surprise_quest_pirate_tale.py
=================================================================

A standalone storyworld for a tiny pirate-tale domain with a bug, a quest,
and a surprise. The core story pattern is:

- children or pirates prepare for a quest,
- a small bug causes a puzzling problem or clue,
- an unexpected surprise changes the plan,
- the crew follows the clue, and
- the story ends with a found prize or a friendly reveal.

The world is intentionally small and classical: a few typed entities, a simple
state machine, and prose driven by simulated meters/memes rather than a frozen
template paragraph.
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
COURAGE_INIT = 5.0
SURPRISE_INIT = 0.0
CURIOSITY_INIT = 1.0


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain"}
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


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    dark_spot: str
    affords: set[str] = field(default_factory=set)
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
class Bug:
    id: str
    label: str
    kind: str
    clue: str
    surprise: str
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
class Quest:
    id: str
    label: str
    verb: str
    prize: str
    path: str
    ending: str
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
class Surprise:
    id: str
    label: str
    reveal: str
    effect: str
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
class Resolution:
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

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]


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


def _r_bug_alarm(world: World) -> list[str]:
    out: list[str] = []
    bug = world.get("bug")
    if bug.meters["noticed"] < THRESHOLD:
        return out
    sig = ("bug_alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for crew in world.crew():
        crew.memes["curiosity"] += 1
    out.append("__bug__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("surprise").meters["revealed"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for crew in world.crew():
        crew.memes["surprise"] += 1
    out.append("__surprise__")
    return out


def _r_quest_progress(world: World) -> list[str]:
    out: list[str] = []
    if world.get("quest").meters["started"] < THRESHOLD:
        return out
    if world.get("quest").meters["found"] >= THRESHOLD:
        return out
    if world.get("bug").meters["noticed"] < THRESHOLD:
        return out
    sig = ("quest_progress",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("quest").meters["found"] += 1
    out.append("__found__")
    return out


CAUSAL_RULES = [Rule("bug_alarm", _r_bug_alarm), Rule("surprise", _r_surprise), Rule("quest_progress", _r_quest_progress)]


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


def bug_is_clue(bug: Bug, quest: Quest) -> bool:
    return bug.kind in {"beetle", "firefly", "crab"} and quest.id in {"map", "treasure", "compass"}


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= 2]


def resolve_power(resolution: Resolution, quest: Quest) -> bool:
    return resolution.power >= 1 and len(quest.prize) > 0


def choose_characters(rng: random.Random) -> tuple[str, str, str, str]:
    captain_names = ["Ava", "Mia", "Lily", "Tom", "Ben", "Finn"]
    mate_names = ["Pip", "Nora", "Zoe", "Max", "Eli", "June"]
    return rng.choice(captain_names), rng.choice(["girl", "boy"]), rng.choice(mate_names), rng.choice(["girl", "boy"])


def _setup(world: World, captain: Entity, mate: Entity, quest: Quest, bug: Bug, surprise: Surprise) -> None:
    captain.memes["courage"] = COURAGE_INIT
    mate.memes["curiosity"] = CURIOSITY_INIT
    mate.memes["surprise"] = SURPRISE_INIT
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} turned {world.setting.place} into a pirate deck. "
        f"{world.setting.mood.capitalize()} hung over the water, and {world.setting.dark_spot} looked like a place for a quest."
    )
    world.say(
        f'"{quest.label}!" {captain.id} said. "If we follow {quest.path}, we might find {quest.prize}!"'
    )
    world.say(
        f"{mate.id} peered toward the shadows, listening for any sign of trouble."
    )


def _spot_bug(world: World, captain: Entity, mate: Entity, bug: Bug, quest: Quest) -> None:
    bug_ent = world.get("bug")
    bug_ent.meters["noticed"] += 1
    world.say(
        f"Then a tiny {bug.label} crawled across the deck boards. It left a little {bug.clue}."
    )
    world.say(
        f"{mate.id} blinked. \"Look! That bug is pointing the way,\" {mate.pronoun()} said."
    )


def _warn_surprise(world: World, surprise: Surprise, captain: Entity, mate: Entity) -> None:
    surprise_ent = world.get("surprise")
    surprise_ent.meters["revealed"] += 1
    world.say(
        f"Just then, the biggest surprise of all arrived: {surprise.reveal}."
    )
    world.say(
        f"{captain.id}'s eyes widened. {mate.id} laughed, because the surprise made the quest feel even grander."
    )


def _follow_clue(world: World, quest: Quest, bug: Bug, captain: Entity, mate: Entity) -> None:
    world.say(
        f"Together they followed {bug.kind} tracks along {quest.path}, past ropes and barrels, until the clue grew clearer."
    )
    world.say(
        f"The quest did not feel scary anymore. It felt like the kind of adventure that only pirate friends could finish."
    )


def _find_prize(world: World, quest: Quest, captain: Entity, mate: Entity) -> None:
    q = world.get("quest")
    q.meters["started"] += 1
    q.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {quest.ending} and found {quest.prize} tucked safely inside."
    )
    world.say(
        f"{captain.id} held it up high, and {mate.id} cheered so loudly the gulls fluttered away."
    )


def _resolution(world: World, captain: Entity, mate: Entity, quest: Quest, resolution: Resolution) -> None:
    world.say(
        f"That was the surprise behind the quest: {resolution.text.format(prize=quest.prize)}."
    )
    world.say(
        f"{captain.id} grinned and said, \"A pirate quest is better with a clue, a surprise, and a friend.\""
    )
    for crew in (captain, mate):
        crew.memes["joy"] += 1
        crew.memes["relief"] += 1


def tell(setting: Setting, bug: Bug, quest: Quest, surprise: Surprise, resolution: Resolution,
         captain_name: str, captain_gender: str, mate_name: str, mate_gender: str) -> World:
    world = World(setting)
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    bug_ent = world.add(Entity(id="bug", kind="thing", type=bug.kind, label=bug.label, tags=set(bug.tags)))
    quest_ent = world.add(Entity(id="quest", kind="thing", type="quest", label=quest.label))
    surprise_ent = world.add(Entity(id="surprise", kind="thing", type="surprise", label=surprise.label))
    world.facts["bug"] = bug
    world.facts["quest"] = quest
    world.facts["surprise"] = surprise
    world.facts["resolution"] = resolution

    _setup(world, captain, mate, quest, bug, surprise)
    world.para()
    _spot_bug(world, captain, mate, bug, quest)
    _warn_surprise(world, surprise, captain, mate)
    _follow_clue(world, quest, bug, captain, mate)
    world.para()
    _find_prize(world, quest, captain, mate)
    _resolution(world, captain, mate, quest, resolution)

    outcome = "found"
    world.facts.update(captain=captain, mate=mate, bug_ent=bug_ent, quest_ent=quest_ent,
                       surprise_ent=surprise_ent, outcome=outcome)
    return world


SETTINGS = {
    "dock": Setting(id="dock", place="the dock", mood="the sea sparkled nearby", dark_spot="the crates in the shade", affords={"quest"}, tags={"pirate", "sea"}),
    "cove": Setting(id="cove", place="the cove", mood="waves whispered at the rocks", dark_spot="the cave mouth", affords={"quest"}, tags={"pirate", "cove"}),
    "ship": Setting(id="ship", place="the little ship", mood="the sails snapped in the breeze", dark_spot="the hold below deck", affords={"quest"}, tags={"pirate", "ship"}),
}

BUGS = {
    "beetle": Bug(id="beetle", label="beetle", kind="beetle", clue="shiny trail", surprise="a clue in its shell", tags={"bug", "clue"}),
    "firefly": Bug(id="firefly", label="firefly", kind="firefly", clue="glowing path", surprise="a lantern-like wink", tags={"bug", "light"}),
    "crab": Bug(id="crab", label="crab", kind="crab", clue="crooked track", surprise="a sideways message", tags={"bug", "clue"}),
}

QUESTS = {
    "map": Quest(id="map", label="map quest", verb="follow the map", prize="the hidden map", path="the rope line", ending="a barrel with a red ribbon", tags={"quest", "map"}),
    "treasure": Quest(id="treasure", label="treasure quest", verb="hunt for treasure", prize="the gold coin", path="the broken plank path", ending="the captain's chest", tags={"quest", "treasure"}),
    "compass": Quest(id="compass", label="compass quest", verb="find the compass", prize="the tiny brass compass", path="the stair to the stern", ending="the lantern nook", tags={"quest", "compass"}),
}

SURPRISES = {
    "note": Surprise(id="note", label="folded note", reveal="a folded note tied to a hook", effect="it changed the plan", tags={"surprise"}),
    "parrot": Surprise(id="parrot", label="parrot", reveal="a parrot wearing a ribbon", effect="it sang the clue aloud", tags={"surprise"}),
    "bottle": Surprise(id="bottle", label="message bottle", reveal="a message bottle bobbing in a tide pool", effect="it glittered like a tiny star", tags={"surprise"}),
}

RESOLUTIONS = {
    "lantern": Resolution(id="lantern", sense=3, power=1, text="a lantern lit the path to {prize}", fail="could not keep up with the dark", qa_text="lit the path with a lantern", tags={"light"}),
    "chalk": Resolution(id="chalk", sense=2, power=1, text="a chalk mark showed where {prize} waited", fail="smudged before the clue could help", qa_text="used chalk marks to follow the clue", tags={"clue"}),
    "birdsong": Resolution(id="birdsong", sense=3, power=1, text="the parrot's birdsong pointed to {prize}", fail="was too quiet to matter", qa_text="followed birdsong to the prize", tags={"sound"}),
    "water_skin": Resolution(id="water_skin", sense=1, power=0, text="a water skin helped with thirst", fail="did not help with the quest", qa_text="used water skin", tags={"weak"}),
}

GIRL_NAMES = ["Ava", "Mia", "Lily", "Nora", "Zoe", "June", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Finn", "Max", "Eli", "Jack"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for bid, bug in BUGS.items():
            for qid in QUESTS:
                if bug_is_clue(bug, QUESTS[qid]):
                    combos.append((sid, bid, qid))
    return combos


@dataclass
class StoryParams:
    setting: str
    bug: str
    quest: str
    surprise: str
    resolution: str
    captain_name: str = ""
    captain_gender: str = ""
    mate_name: str = ""
    mate_gender: str = ""
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a bug, a quest, and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bug", choices=BUGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--mate")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bug is None or c[1] == args.bug)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bug, quest = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    resolution = args.resolution or rng.choice(sorted(r.id for r in sensible_resolutions()))
    captain_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    captain_gender = "girl" if captain_name in GIRL_NAMES else "boy"
    mate_name = args.mate or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != captain_name])
    mate_gender = "girl" if mate_name in GIRL_NAMES else "boy"
    return StoryParams(setting=setting, bug=bug, quest=quest, surprise=surprise, resolution=resolution,
                       captain_name=captain_name, captain_gender=captain_gender,
                       mate_name=mate_name, mate_gender=mate_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the word "bug" and a surprising clue.',
        f"Tell a pirate story where {f['captain'].id} and {f['mate'].id} follow a quest, notice a bug, and find a surprise.",
        f"Write a gentle adventure story with a bug, a quest, and an unexpected reveal near {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain, mate = f["captain"], f["mate"]
    bug, quest, surprise, resolution = f["bug"], f["quest"], f["surprise"], f["resolution"]
    qa = [
        QAItem(
            question="Who went on the pirate quest?",
            answer=f"{captain.id} and {mate.id} went together. They acted like a small pirate crew and stayed side by side the whole time.",
        ),
        QAItem(
            question="What did the bug do in the story?",
            answer=f"The {bug.label} left a clue for them to follow. That tiny sign helped turn the bug into part of the quest instead of just a distraction.",
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {surprise.reveal}. It changed the mood of the story and made the quest feel magical.",
        ),
        QAItem(
            question="How did they finish the quest?",
            answer=f"They followed the clue and reached the prize in the end. {resolution.qa_text.capitalize()}, so the ending felt like a real pirate victory.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["bug"].tags) | set(world.facts["quest"].tags) | set(world.facts["surprise"].tags)
    tags |= set(world.facts["resolution"].tags)
    out = []
    if "bug" in tags:
        out.append(QAItem("What is a bug?", "A bug is a tiny animal with a hard little body or wings. Bugs can be helpful, and some bugs leave clues or glow in the dark."))
    if "quest" in tags:
        out.append(QAItem("What is a quest?", "A quest is a mission or search for something important. In stories, a quest often means following clues and trying hard to reach a goal."))
    if "surprise" in tags:
        out.append(QAItem("What is a surprise?", "A surprise is something you did not expect. It can make a story feel exciting and new."))
    if "light" in tags:
        out.append(QAItem("Why is a lantern useful on a ship?", "A lantern gives steady light without needing the sun. Pirates can use it to see in dark places like a hold or cave."))
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
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,Q) :- setting(S), bug(B), quest(Q), bug_clue(B,Q).
bug_clue(B,Q) :- bug_kind(B,K), quest_topic(Q,K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BUGS.items():
        lines.append(asp.fact("bug", bid))
        lines.append(asp.fact("bug_kind", bid, b.kind))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_topic", qid, q.id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, bug=None, quest=None, surprise=None, resolution=None, name=None, mate=None), random.Random(7)))
        assert sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= 2]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.bug not in BUGS or params.quest not in QUESTS:
        raise StoryError("Invalid story parameters.")
    if params.surprise not in SURPRISES:
        raise StoryError("Invalid surprise parameter.")
    if params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid resolution parameter.")
    if RESOLUTIONS[params.resolution].sense < 2:
        raise StoryError("That resolution is too weak for this story.")
    world = tell(SETTINGS[params.setting], BUGS[params.bug], QUESTS[params.quest],
                 SURPRISES[params.surprise], RESOLUTIONS[params.resolution],
                 params.captain_name, params.captain_gender, params.mate_name, params.mate_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(setting="dock", bug="beetle", quest="map", surprise="note", resolution="lantern", captain_name="Ava", captain_gender="girl", mate_name="Pip", mate_gender="boy"),
    StoryParams(setting="cove", bug="firefly", quest="compass", surprise="parrot", resolution="birdsong", captain_name="Tom", captain_gender="boy", mate_name="Nora", mate_gender="girl"),
    StoryParams(setting="ship", bug="crab", quest="treasure", surprise="bottle", resolution="chalk", captain_name="Lily", captain_gender="girl", mate_name="Ben", mate_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, bug, quest) combos:")
        for s, b, q in asp_valid_combos():
            print(f"  {s:6} {b:8} {q}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
