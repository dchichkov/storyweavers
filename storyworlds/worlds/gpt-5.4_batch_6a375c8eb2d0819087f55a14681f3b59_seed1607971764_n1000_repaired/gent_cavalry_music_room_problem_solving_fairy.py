#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gent_cavalry_music_room_problem_solving_fairy.py

A standalone story world for a fairy-tale problem-solving story set in a music
room. A child faces one concrete music-room problem, chooses a sensible fix,
gets help, and changes the ending image by solving the problem instead of giving
up.

The domain always includes a brass gent toy and a line of toy cavalry on a
shelf, so the requested seed words belong to the world itself.

Run it
------
    python storyworlds/worlds/gpt-5.4/gent_cavalry_music_room_problem_solving_fairy.py
    python storyworlds/worlds/gpt-5.4/gent_cavalry_music_room_problem_solving_fairy.py --instrument violin --problem loose_string
    python storyworlds/worlds/gpt-5.4/gent_cavalry_music_room_problem_solving_fairy.py --problem sleepy_key --fix tuning_key
    python storyworlds/worlds/gpt-5.4/gent_cavalry_music_room_problem_solving_fairy.py --all
    python storyworlds/worlds/gpt-5.4/gent_cavalry_music_room_problem_solving_fairy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gent_cavalry_music_room_problem_solving_fairy.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "fairy"}
        male = {"boy", "father", "man", "gent"}
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
class Instrument:
    id: str
    label: str
    phrase: str
    music_word: str
    glow: str
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
class Problem:
    id: str
    label: str
    sentence: str
    discovery: str
    need: int
    compatible_instruments: set[str]
    compatible_fixes: set[str]
    caused_by: str
    ending_proof: str
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    action: str
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


@dataclass
class Helper:
    id: str
    label: str
    type: str
    power: int
    entrance: str
    advice: str
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


def _r_problem_stirs_worry(world: World) -> list[str]:
    inst = world.get("instrument")
    hero = world.get("hero")
    room = world.get("room")
    if inst.meters["problem"] < THRESHOLD or inst.meters["ready"] >= THRESHOLD:
        return []
    sig = ("worry", inst.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    room.meters["delay"] += 1
    return ["__worry__"]


def _r_fix_restores_music(world: World) -> list[str]:
    inst = world.get("instrument")
    room = world.get("room")
    hero = world.get("hero")
    if world.facts.get("attempt_power", 0) < world.facts.get("needed_power", 99):
        return []
    if inst.meters["problem"] < THRESHOLD:
        return []
    sig = ("restore", inst.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    inst.meters["problem"] = 0.0
    inst.meters["ready"] += 1
    room.meters["delay"] = 0.0
    hero.memes["confidence"] += 1
    hero.memes["relief"] += 1
    return ["__restored__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="problem_stirs_worry", tag="emotional", apply=_r_problem_stirs_worry),
    Rule(name="fix_restores_music", tag="physical", apply=_r_fix_restores_music),
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


def compatible_problem(instrument: Instrument, problem: Problem) -> bool:
    return instrument.id in problem.compatible_instruments


def sensible_fix(fix: Fix) -> bool:
    return fix.sense >= SENSE_MIN


def compatible_fix(problem: Problem, fix: Fix) -> bool:
    return fix.id in problem.compatible_fixes and sensible_fix(fix)


def attempt_power(problem: Problem, fix: Fix, helper: Helper) -> int:
    bonus = helper.power
    if problem.id == "lost_page" and helper.id == "cavalry_captain":
        bonus += 1
    if problem.id == "loose_string" and helper.id == "clockwork_gent":
        bonus += 1
    return fix.power + bonus


def outcome_of(params: "StoryParams") -> str:
    instrument = INSTRUMENTS[params.instrument]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    helper = HELPERS[params.helper]
    if not compatible_problem(instrument, problem):
        return "invalid"
    if not compatible_fix(problem, fix):
        return "invalid"
    score = attempt_power(problem, fix, helper)
    return "swift" if score > problem.need else "steady"


def predict_solution(problem: Problem, fix: Fix, helper: Helper) -> dict:
    score = attempt_power(problem, fix, helper)
    return {
        "needed": problem.need,
        "score": score,
        "swift": score > problem.need,
        "works": score >= problem.need,
    }


def introduce(world: World, hero: Entity, parent: Entity, instrument: Instrument) -> None:
    world.say(
        f"In the music room of a small silver house, {hero.id} liked to practice on "
        f"{instrument.phrase} when evening turned the floor into a pond of gold."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was such a polite little gent at the bench that "
        f"even {hero.pronoun('possessive')} {parent.label_word} smiled to hear the first notes."
    )
    world.say(
        "On the high shelf stood a brass gent with a tiny hat, and beside him waited "
        "a toy cavalry on painted horses, as still as storybook guards before a parade."
    )


def announce_goal(world: World, hero: Entity, instrument: Instrument) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"That night {hero.pronoun()} hoped to play a moon song so clear that the whole "
        f"room would listen, from the sleepy metronome to the cavalry on the shelf."
    )
    world.say(
        f"The first notes of the {instrument.music_word} tune rose softly, and {instrument.glow}."
    )


def discover_problem(world: World, hero: Entity, instrument_ent: Entity, problem: Problem) -> None:
    instrument_ent.meters["problem"] += 1
    world.facts["needed_power"] = problem.need
    world.say(problem.discovery)
    world.say(
        f"{hero.id} stopped, blinked, and listened again. {problem.sentence}"
    )
    propagate(world, narrate=False)


def helper_arrives(world: World, helper: Helper) -> None:
    world.say(helper.entrance)
    world.say(helper.advice)


def choose_fix(world: World, hero: Entity, fix: Fix, helper: Helper, problem: Problem) -> None:
    pred = predict_solution(problem, fix, helper)
    hero.memes["thinking"] += 1
    world.facts["predicted_score"] = pred["score"]
    world.facts["predicted_swift"] = pred["swift"]
    world.say(
        f"{hero.id} did not cry or stomp. {hero.pronoun().capitalize()} looked at the trouble, "
        f"thought for a moment, and chose {fix.label}."
    )
    world.say(
        f'"Let us solve one small thing at a time," said {helper.label}.'
    )


def apply_fix(world: World, hero: Entity, fix: Fix, helper: Helper, problem: Problem) -> None:
    world.facts["attempt_power"] = attempt_power(problem, fix, helper)
    hero.memes["bravery"] += 1
    world.say(fix.action)
    propagate(world, narrate=False)


def celebrate_swift(world: World, hero: Entity, instrument: Instrument, parent: Entity, problem: Problem) -> None:
    hero.memes["joy"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"At once the music came back, bright and whole. {hero.id} played so smoothly that "
        f"{parent.label_word} stood in the doorway and forgot to whisper."
    )
    world.say(
        f"The brass gent seemed to bow, the toy cavalry looked ready to prance, and "
        f"{problem.ending_proof}."
    )
    world.say(
        f"When the last note of the {instrument.music_word} tune faded, the music room felt "
        f"larger, kinder, and full of solved things."
    )


def celebrate_steady(world: World, hero: Entity, instrument: Instrument, parent: Entity, problem: Problem) -> None:
    hero.memes["joy"] += 1
    hero.memes["patience"] += 1
    world.say(
        f"It took another careful try, and then another soft breath, but at last the music returned. "
        f"{hero.id} kept going bravely instead of giving up."
    )
    world.say(
        f"{parent.label_word.capitalize()} came closer, warm-eyed and proud. The brass gent shone in the lamp-light, "
        f"the toy cavalry stayed for the whole song, and {problem.ending_proof}."
    )
    world.say(
        f"So the tune was not hurried, but it was true, and that made the room feel like a fairy tale all the same."
    )


def tell(
    instrument: Instrument,
    problem: Problem,
    fix: Fix,
    helper: Helper,
    hero_name: str = "Elio",
    hero_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="music room",
    ))
    instrument_ent = world.add(Entity(
        id="instrument",
        type="instrument",
        label=instrument.label,
        attrs={"instrument_id": instrument.id},
    ))
    world.add(Entity(
        id="brass_gent",
        type="gent",
        label="brass gent",
        attrs={"watching": True},
    ))
    world.add(Entity(
        id="cavalry",
        type="toys",
        label="toy cavalry",
        attrs={"watching": True},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper.type,
        label=helper.label,
        role="helper",
    ))

    world.facts.update(
        instrument_cfg=instrument,
        problem_cfg=problem,
        fix_cfg=fix,
        helper_cfg=helper,
        hero=hero,
        parent=parent,
        helper=helper_ent,
        needed_power=problem.need,
        attempt_power=0,
    )

    introduce(world, hero, parent, instrument)
    announce_goal(world, hero, instrument)

    world.para()
    discover_problem(world, hero, instrument_ent, problem)
    helper_arrives(world, helper)
    choose_fix(world, hero, fix, helper, problem)

    world.para()
    apply_fix(world, hero, fix, helper, problem)
    outcome = "swift" if instrument_ent.meters["ready"] >= THRESHOLD and world.facts["attempt_power"] > problem.need else "steady"
    if instrument_ent.meters["ready"] < THRESHOLD:
        raise StoryError("The chosen fix did not solve the music-room problem.")
    if outcome == "swift":
        celebrate_swift(world, hero, instrument, parent, problem)
    else:
        celebrate_steady(world, hero, instrument, parent, problem)

    world.facts.update(
        solved=instrument_ent.meters["ready"] >= THRESHOLD,
        outcome=outcome,
        room_delay=room.meters["delay"],
        hero_worry=hero.memes["worry"],
        hero_confidence=hero.memes["confidence"],
    )
    return world


INSTRUMENTS = {
    "piano": Instrument(
        id="piano",
        label="piano",
        phrase="the moon-colored piano",
        music_word="piano",
        glow="the ivory keys shone like little teeth of light",
        tags={"piano", "music_room"},
    ),
    "violin": Instrument(
        id="violin",
        label="violin",
        phrase="a cherry-red violin",
        music_word="violin",
        glow="its polished wood caught the lamp-light like a secret apple",
        tags={"violin", "music_room"},
    ),
    "harp": Instrument(
        id="harp",
        label="harp",
        phrase="the small golden harp",
        music_word="harp",
        glow="its strings trembled like thin moonbeams",
        tags={"harp", "music_room"},
    ),
}

PROBLEMS = {
    "lost_page": Problem(
        id="lost_page",
        label="lost page",
        sentence="The next page of the song had slipped under the cabinet, where small hands could not reach it.",
        discovery="Then a draft from the tall window fluttered the music sheets.",
        need=2,
        compatible_instruments={"piano", "violin", "harp"},
        compatible_fixes={"ribbon_hook", "broom"},
        caused_by="a draft from the window",
        ending_proof="the hidden page lay safely open on the stand, no longer hiding under the cabinet",
        tags={"sheet_music", "music_room"},
    ),
    "loose_string": Problem(
        id="loose_string",
        label="loose string",
        sentence="One string answered with a sad wobble instead of a clear note.",
        discovery="But when the tune climbed higher, one note drooped sadly.",
        need=2,
        compatible_instruments={"violin", "harp"},
        compatible_fixes={"tuning_key"},
        caused_by="a loose string",
        ending_proof="the once-wobbly string now rang true and silver",
        tags={"string", "music_room"},
    ),
    "sleepy_key": Problem(
        id="sleepy_key",
        label="sleepy key",
        sentence="A single key stayed low and would not spring up, as if it wanted one more nap.",
        discovery="Just then one note stayed stuck under the tip of a finger.",
        need=1,
        compatible_instruments={"piano"},
        compatible_fixes={"soft_cloth", "patient_press"},
        caused_by="dust around a key",
        ending_proof="the sleepy key had awakened and danced with the others again",
        tags={"piano_key", "music_room"},
    ),
}

FIXES = {
    "ribbon_hook": Fix(
        id="ribbon_hook",
        label="a ribbon hook",
        sense=3,
        power=2,
        action="With a long ribbon tied to a practice stick, the page was gently hooked and pulled back across the floor.",
        fail="The ribbon slipped away from the paper.",
        qa_text="used a ribbon hook to draw the lost page back",
        tags={"problem_solving", "sheet_music"},
    ),
    "broom": Fix(
        id="broom",
        label="the soft broom",
        sense=2,
        power=1,
        action="Using the soft broom very carefully, the page was nudged out little by little until it could be picked up.",
        fail="The broom only tickled the dust and did not quite reach.",
        qa_text="used a soft broom to push the page out",
        tags={"problem_solving", "sheet_music"},
    ),
    "tuning_key": Fix(
        id="tuning_key",
        label="the tuning key",
        sense=3,
        power=2,
        action="Very slowly the tuning key turned, and the loose string was tested again after each tiny twist.",
        fail="The string still sounded low and tired.",
        qa_text="turned the tuning key in small careful steps",
        tags={"problem_solving", "string"},
    ),
    "soft_cloth": Fix(
        id="soft_cloth",
        label="a soft cloth",
        sense=3,
        power=1,
        action="The edge of a soft cloth slid beside the sleepy key, lifting the dust away until the key popped back up.",
        fail="The key still felt sticky.",
        qa_text="cleaned beside the sticky key with a soft cloth",
        tags={"problem_solving", "cleaning"},
    ),
    "patient_press": Fix(
        id="patient_press",
        label="patient pressing",
        sense=2,
        power=1,
        action="The key was pressed and released gently, again and again, until it remembered how to rise on its own.",
        fail="The key kept sagging sleepily.",
        qa_text="pressed the key gently until it rose again",
        tags={"problem_solving", "patience"},
    ),
    "bang_harder": Fix(
        id="bang_harder",
        label="banging harder",
        sense=1,
        power=1,
        action="The keys were hit harder and harder.",
        fail="That only made the sound rougher and did not fix the real trouble.",
        qa_text="banged on the instrument",
        tags={"bad_idea"},
    ),
}

HELPERS = {
    "moon_fairy": Helper(
        id="moon_fairy",
        label="the moon fairy",
        type="fairy",
        power=1,
        entrance="From the top of the music stand a moon fairy peeped out, no bigger than a clothespin and bright as pearl dust.",
        advice='"Small troubles love small, careful hands," she whispered.',
        tags={"fairy", "help"},
    ),
    "clockwork_gent": Helper(
        id="clockwork_gent",
        label="the clockwork gent",
        type="gent",
        power=1,
        entrance="The brass gent on the shelf clicked, bowed, and stepped down with the neat manners of a toy prince.",
        advice='"A tidy mind makes a tidy answer," said the clockwork gent.',
        tags={"gent", "help"},
    ),
    "cavalry_captain": Helper(
        id="cavalry_captain",
        label="the cavalry captain",
        type="soldier",
        power=1,
        entrance="With the softest clatter, one tiny captain from the toy cavalry rode forward as if the shelf itself had opened a gate.",
        advice='"Forward by inches, not by panic," said the cavalry captain.',
        tags={"cavalry", "help"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Ivy", "Elsa"]
BOY_NAMES = ["Elio", "Rowan", "Jasper", "Theo", "Milo", "Felix"]
TRAITS = ["careful", "patient", "bright", "gentle", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for inst_id, inst in INSTRUMENTS.items():
        for prob_id, prob in PROBLEMS.items():
            if not compatible_problem(inst, prob):
                continue
            for fix_id, fix in FIXES.items():
                if compatible_fix(prob, fix):
                    combos.append((inst_id, prob_id, fix_id))
    return combos


@dataclass
class StoryParams:
    instrument: str
    problem: str
    fix: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
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


KNOWLEDGE = {
    "music_room": [
        (
            "What is a music room?",
            "A music room is a place where people keep instruments and practice songs. It is often quiet so small sounds are easier to hear."
        )
    ],
    "sheet_music": [
        (
            "What is sheet music?",
            "Sheet music is paper with notes written on it, so a player knows what sounds to make. If a page is missing, it is hard to finish the song."
        )
    ],
    "string": [
        (
            "Why does a loose string sound wrong?",
            "A loose string cannot vibrate the right way, so the note sounds low or wobbly. Tightening it carefully helps it ring clearly again."
        )
    ],
    "piano_key": [
        (
            "Why can a piano key get stuck?",
            "A piano key can stick when dust or something small gets in its way. Cleaning it gently can help it move freely again."
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means looking at what went wrong and choosing a step that truly helps. It is often slower and smarter than getting upset."
        )
    ],
    "patience": [
        (
            "Why does patience help when something is hard?",
            "Patience helps because careful steps make it easier to notice what works. Rushing can hide the real problem."
        )
    ],
    "cleaning": [
        (
            "Why can cleaning fix some small problems?",
            "Some little troubles come from dust or dirt being in the way. Cleaning removes the thing that is blocking the part from moving well."
        )
    ],
    "fairy": [
        (
            "What is a fairy in a fairy tale?",
            "A fairy is a tiny magical helper in many stories. Fairies often guide someone toward a kind or clever choice."
        )
    ],
    "gent": [
        (
            "What does gent mean?",
            "Gent is a short old-fashioned word for gentleman. In stories, it often means someone polite and neatly behaved."
        )
    ],
    "cavalry": [
        (
            "What is cavalry?",
            "Cavalry means soldiers on horses. In toy stories, a tiny cavalry can look like a brave little parade."
        )
    ],
    "help": [
        (
            "Why is asking or accepting help brave?",
            "It is brave because you are honest about the problem instead of pretending nothing is wrong. A helper can notice a good idea you missed."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "music_room",
    "sheet_music",
    "string",
    "piano_key",
    "problem_solving",
    "patience",
    "cleaning",
    "fairy",
    "gent",
    "cavalry",
    "help",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem_cfg"]
    instrument = f["instrument_cfg"]
    helper = f["helper_cfg"]
    return [
        f'Write a short fairy-tale story for a 3-to-5-year-old set in a music room, and include the words "gent" and "cavalry".',
        f"Tell a gentle problem-solving story where {hero.id} wants to play {instrument.phrase}, but {problem.label} stops the song and {helper.label} helps with a careful plan.",
        f"Write a child-friendly story in which a music-room problem is solved step by step instead of with panic, ending with the instrument singing clearly again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    instrument = f["instrument_cfg"]
    problem = f["problem_cfg"]
    fix = f["fix_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who wanted to play {instrument.phrase} in the music room. The story also includes {helper.label}, who helped when the trouble appeared."
        ),
        (
            "What problem stopped the music?",
            f"The problem was {problem.label}. {problem.sentence} That is why the tune could not continue in the normal way."
        ),
        (
            f"How did {hero.id} try to solve the problem?",
            f"{hero.id} chose {fix.label} and worked carefully instead of panicking. {fix.qa_text.capitalize()}, because that matched the real trouble."
        ),
        (
            f"Why did the plan work?",
            f"It worked because the fix fit the problem, and {helper.label} guided the work calmly. The answer was not louder noise or fussing, but a small useful step."
        ),
    ]
    if outcome == "swift":
        qa.append(
            (
                f"How did the story end?",
                f"The problem was solved quickly, and {hero.id} played the whole tune with joy. In the ending image, the brass gent seemed to bow and the toy cavalry looked ready to prance."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} feel at the end?",
                f"{hero.id} felt proud and patient because the tune came back after careful trying. The ending shows that steady work can still make a lovely fairy-tale ending."
            )
        )
    qa.append(
        (
            f"Was {hero.id}'s {parent.label_word} angry?",
            f"No. {parent.label_word.capitalize()} was proud and gentle when the music came back. The grown-up's calm presence makes the solution feel safe instead of scary."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["instrument_cfg"].tags) | set(f["problem_cfg"].tags) | set(f["fix_cfg"].tags) | set(f["helper_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        instrument="piano",
        problem="lost_page",
        fix="ribbon_hook",
        helper="moon_fairy",
        name="Lina",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        instrument="violin",
        problem="loose_string",
        fix="tuning_key",
        helper="clockwork_gent",
        name="Theo",
        gender="boy",
        parent="father",
        trait="patient",
    ),
    StoryParams(
        instrument="piano",
        problem="sleepy_key",
        fix="soft_cloth",
        helper="cavalry_captain",
        name="Mira",
        gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        instrument="harp",
        problem="lost_page",
        fix="broom",
        helper="cavalry_captain",
        name="Felix",
        gender="boy",
        parent="father",
        trait="gentle",
    ),
    StoryParams(
        instrument="piano",
        problem="sleepy_key",
        fix="patient_press",
        helper="clockwork_gent",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="bright",
    ),
]


def explain_problem(instrument: Instrument, problem: Problem) -> str:
    return (
        f"(No story: {problem.label} does not fit the {instrument.label}. "
        f"Choose a problem that could honestly happen with that instrument.)"
    )


def explain_fix(problem: Problem, fix: Fix) -> str:
    if not sensible_fix(fix):
        return (
            f"(Refusing fix '{fix.id}': it is not a sensible problem-solving move "
            f"(sense={fix.sense} < {SENSE_MIN}). Pick a calmer, more fitting fix.)"
        )
    return (
        f"(No story: {fix.label} does not match {problem.label}. "
        f"The solution must fit the real trouble.)"
    )


ASP_RULES = r"""
compatible_problem(I,P) :- instrument(I), problem(P), works_on(P,I).
sensible_fix(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
compatible_fix(P,F) :- problem(P), fix(F), solves(P,F), sensible_fix(F).
valid(I,P,F) :- compatible_problem(I,P), compatible_fix(P,F).

bonus(1) :- chosen_problem(lost_page), chosen_helper(cavalry_captain).
bonus(1) :- chosen_problem(loose_string), chosen_helper(clockwork_gent).
bonus(0) :- not bonus(1).

attempt_power(Pw + Hw + B) :- chosen_fix(F), power(F,Pw), chosen_helper(H), helper_power(H,Hw), bonus(B).
outcome(swift) :- chosen_problem(P), need(P,N), attempt_power(S), S > N.
outcome(steady) :- chosen_problem(P), need(P,N), attempt_power(S), S >= N, S <= N.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("need", pid, p.need))
        for iid in sorted(p.compatible_instruments):
            lines.append(asp.fact("works_on", pid, iid))
        for fid in sorted(p.compatible_fixes):
            lines.append(asp.fact("solves", pid, fid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_power", hid, h.power))
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
    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for s in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world in a music room: a child solves one small musical problem with a fitting fix."
    )
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible instrument/problem/fix combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.instrument and args.problem:
        instrument = INSTRUMENTS[args.instrument]
        problem = PROBLEMS[args.problem]
        if not compatible_problem(instrument, problem):
            raise StoryError(explain_problem(instrument, problem))
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not compatible_fix(problem, fix):
            raise StoryError(explain_fix(problem, fix))
    if args.fix and not sensible_fix(FIXES[args.fix]):
        raise StoryError(explain_fix(next(iter(PROBLEMS.values())), FIXES[args.fix]))

    combos = [
        c for c in valid_combos()
        if (args.instrument is None or c[0] == args.instrument)
        and (args.problem is None or c[1] == args.problem)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    instrument_id, problem_id, fix_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        instrument=instrument_id,
        problem=problem_id,
        fix=fix_id,
        helper=helper_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.instrument not in INSTRUMENTS:
        raise StoryError(f"(Unknown instrument: {params.instrument})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    instrument = INSTRUMENTS[params.instrument]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    helper = HELPERS[params.helper]

    if not compatible_problem(instrument, problem):
        raise StoryError(explain_problem(instrument, problem))
    if not compatible_fix(problem, fix):
        raise StoryError(explain_fix(problem, fix))

    world = tell(
        instrument=instrument,
        problem=problem,
        fix=fix,
        helper=helper,
        hero_name=params.name,
        hero_gender=params.gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (instrument, problem, fix) combos:\n")
        for instrument, problem, fix in combos:
            print(f"  {instrument:8} {problem:12} {fix}")
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
            header = f"### {p.name}: {p.instrument} / {p.problem} / {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
