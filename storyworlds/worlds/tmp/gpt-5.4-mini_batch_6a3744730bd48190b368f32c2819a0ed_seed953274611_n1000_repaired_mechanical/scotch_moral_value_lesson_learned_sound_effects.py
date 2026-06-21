#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scotch_moral_value_lesson_learned_sound_effects.py
====================================================================================

A small whodunit-style storyworld about a missing treat, a careful clue trail,
and a moral ending. The story uses typed entities with physical meters and
emotional memes, a state-driven turn, sound effects, and a clear lesson learned.

Seed words / features:
- scotch
- Moral Value
- Lesson Learned
- Sound Effects
- Style: Whodunit
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Place:
    id: str
    label: str
    dark: bool = False
    secret: bool = False
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
    phrase: str
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
class Action:
    id: str
    verb: str
    noise: str
    reveals: str
    risk: str
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
    lesson: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_shock(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    if culprit and culprit.meters["guilty"] >= THRESHOLD:
        sig = ("shock", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.characters():
                if kid.role in {"detective", "friend"}:
                    kid.memes["alert"] += 1
            out.append("__shock__")
    return out


def _r_clear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved"):
        sig = ("clear",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.characters():
                kid.memes["relief"] += 1
            out.append("__clear__")
    return out


CAUSAL_RULES = [Rule("shock", _r_shock), Rule("clear", _r_clear)]


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


def reasonable_action(action: Action) -> bool:
    return action.sense >= 2


def valid_pair(place: Place, clue: Clue) -> bool:
    return place.secret and place.dark and ("scotch" in clue.tags or "tape" in clue.tags)


def best_action() -> Action:
    return max(ACTIONS.values(), key=lambda a: a.sense)


def solve_truth(world: World, action: Action, culprit: Entity, detective: Entity) -> None:
    culprit.meters["guilty"] += 1
    culprit.memes["nervous"] += 1
    world.say(f"{detective.id} tiptoed into {world.facts['place'].label}, eyeing the quiet corners.")
    world.say(
        f'"{detective.id}," whispered {culprit.id}, "I know who moved the {world.facts["missing"].label}." '
        f"Scotch tape crinkled softly near the floor. {action.noise}"
    )
    culprit.memes["shame"] += 1


def inspect(world: World, detective: Entity, clue: Clue, place: Place) -> None:
    detective.memes["curious"] += 1
    world.say(
        f"{detective.id} found {clue.phrase} by the doorway. In the dim light, "
        f"the clue looked like a tiny promise."
    )
    world.say(
        f'Then came a little sound: {ACTIONS["tap"].noise} {ACTIONS["tap"].noise.lower()}! '
        f"{detective.id} followed the sound toward {place.label}."
    )


def accuse(world: World, detective: Entity, culprit: Entity, missing: Entity) -> None:
    detective.memes["certainty"] += 1
    world.say(
        f'"Aha," said {detective.id}. "The missing {missing.label} did not walk away. '
        f'It was moved, and someone left {world.facts["clue"].label} behind."'
    )
    world.say(
        f"{culprit.id} blushed and looked down at {culprit.pronoun('possessive')} shoes."
    )


def explain_moral(world: World, adult: Entity, culprit: Entity, detective: Entity) -> None:
    culprit.memes["lesson"] += 1
    detective.memes["lesson"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {adult.label_word.capitalize()} knelt beside them. "
        f'"It is better to tell the truth than to hide it," {adult.pronoun()} said. '
        f'"A small lie can make a small problem grow into a bigger one."'
    )
    world.say(
        f"{culprit.id} nodded. {detective.id} nodded too. They had learned that a good clue "
        f"could catch a trick, but honesty was the best way to make things right."
    )


def reveal_end(world: World, adult: Entity, missing: Entity, clue: Clue) -> None:
    world.facts["resolved"] = True
    world.say(
        f"At last, {adult.label_word} opened the little box and there was the {missing.label}, "
        f"safe and shiny, with {clue.label} stuck to the side."
    )
    world.say(
        f'"{ACTIONS["tap"].noise}," went the room as the last piece clicked into place.'
    )
    propagate(world, narrate=False)


def tell(place: Place, clue: Clue, action: Action, resolution: Resolution,
         detective_name: str = "Mia", detective_gender: str = "girl",
         culprit_name: str = "Noah", culprit_gender: str = "boy",
         adult_type: str = "mother") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_gender, role="culprit"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, label="the grown-up", role="adult"))
    missing = world.add(Entity(id="missing", type="thing", label="tin of scotch mints"))
    box = world.add(Entity(id="box", type="thing", label="little box"))
    world.facts.update(place=place, clue=clue, action=action, resolution=resolution, missing=missing, box=box)
    world.say(
        f"On a hush-hush evening, {detective.id} noticed something odd in {place.label}. "
        f"The shelf was tidy, but one sweet tin was gone."
    )
    world.say(
        f"{detective.id} loved mysteries. {culprit.id} looked extra fidgety, and the floor had "
        f"a pale strip of {clue.label} near the rug."
    )
    world.para()
    inspect(world, detective, clue, place)
    accuse(world, detective, culprit, missing)
    culprit.memes["fear"] += 1
    culprit.meters["guilty"] += 0.0
    if resolution.sense >= 2:
        world.say(
            f'"I know how to fix this," said the grown-up, and {resolution.text}.'
        )
        reveal_end(world, adult, missing, clue)
        explain_moral(world, adult, culprit, detective)
    else:
        world.say(
            f"The grown-up hesitated, and {resolution.fail}. The case stayed messy, with no neat ending."
        )
    world.para()
    world.say(
        f"In the end, {detective.id} kept the clue in mind, {culprit.id} told the truth, "
        f"and the room felt calm again."
    )
    world.facts["resolved"] = resolution.sense >= 2
    world.facts["culprit"] = culprit
    world.facts["detective"] = detective
    world.facts["adult"] = adult
    return world


@dataclass
class StoryParams:
    place: str
    clue: str
    action: str
    resolution: str
    detective_name: str
    detective_gender: str
    culprit_name: str
    culprit_gender: str
    adult_type: str
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


PLACES = {
    "hall": Place(id="hall", label="the hallway", dark=True, secret=True, tags={"mystery"}),
    "study": Place(id="study", label="the study", dark=True, secret=True, tags={"mystery"}),
    "pantry": Place(id="pantry", label="the pantry", dark=True, secret=True, tags={"mystery"}),
}

CLUES = {
    "scotch": Clue(id="scotch", label="scotch tape", phrase="a strip of scotch tape", tags={"scotch", "tape"}),
    "lint": Clue(id="lint", label="lint", phrase="a fuzzy bit of lint", tags={"lint"}),
    "crumb": Clue(id="crumb", label="crumb", phrase="one tiny crumb", tags={"crumb"}),
}

ACTIONS = {
    "tap": Action(id="tap", verb="tap", noise="tap", reveals="sound", risk="small", tags={"sound"}),
    "creak": Action(id="creak", verb="creak", noise="creak", reveals="sound", risk="small", tags={"sound"}),
    "rustle": Action(id="rustle", verb="rustle", noise="rustle", reveals="sound", risk="small", tags={"sound"}),
}

RESOLUTIONS = {
    "apology": Resolution(
        id="apology",
        sense=3,
        power=3,
        text="he checked the cupboard, found the missing tin, and admitted he had moved it for a surprise snack",
        fail="he looked around, but the answer never came",
        lesson="tell the truth and fix your mistakes",
        tags={"truth"},
    ),
    "return": Resolution(
        id="return",
        sense=3,
        power=2,
        text="she opened the box and put the tin back where it belonged",
        fail="she closed the box and hoped nobody would notice",
        lesson="put things back after borrowing them",
        tags={"truth"},
    ),
    "shrug": Resolution(
        id="shrug",
        sense=1,
        power=1,
        text="he shrugged and guessed, which did not help",
        fail="he shrugged and guessed, which did not help",
        lesson="",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Mia", "Nia", "Tess", "Lena", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Owen", "Max", "Leo", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for c in CLUES.values():
            for a in ACTIONS.values():
                if valid_pair(p, c):
                    combos.append((p.id, c.id, a.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with scotch tape, clues, and a moral lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--culprit")
    ap.add_argument("--culprit-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.resolution and not reasonable_action(RESOLUTIONS[args.resolution]):
        raise StoryError("That ending is too weak to count as a proper lesson learned.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, action = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice([k for k, v in RESOLUTIONS.items() if reasonable_action(v)])
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    culprit_gender = args.culprit_gender or rng.choice(["girl", "boy"])
    culprit_pool = GIRL_NAMES if culprit_gender == "girl" else BOY_NAMES
    culprit = args.culprit or rng.choice(culprit_pool)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        clue=clue,
        action=action,
        resolution=resolution,
        detective_name=name,
        detective_gender=gender,
        culprit_name=culprit,
        culprit_gender=culprit_gender,
        adult_type=adult,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit story for a 3-to-5-year-old that includes "{f["clue"].label}" and the word "scotch".',
        f"Tell a small mystery where {f['detective'].id} follows a clue, hears a sound effect, and learns a moral lesson about telling the truth.",
        f"Write a child-friendly detective story with a tidy ending, a hidden snack, and a clear lesson learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    adult = f["adult"]
    missing = f["missing"]
    clue = f["clue"]
    resolution = f["resolution"]
    qa = [
        ("What kind of story is this?",
         f"It is a little whodunit. {detective.id} follows clues in a quiet place and finds out who moved the missing {missing.label}."),
        ("What clue did the detective notice?",
         f"{detective.id} noticed {clue.phrase}. That mattered because scotch tape is easy to spot when something has been moved in a hurry."),
        ("What sound effect helped the detective?",
         f"The detective heard little tapping sounds. Those sounds made the clue trail feel alive and helped point the way."),
        ("Who moved the missing thing?",
         f"{culprit.id} moved it. {culprit.id} was fidgety at first, but the story ends with the truth coming out."),
    ]
    if f.get("resolved"):
        qa.append(
            ("How was the mystery solved?",
             f"The grown-up found the missing {missing.label} and {resolution.text}. The clue and the truth matched up, so the case made sense at last.")
        )
        qa.append(
            ("What lesson did the children learn?",
             f"{resolution.lesson.capitalize()}. The grown-up said it kindly, and both children learned that honesty helps fix a problem better than hiding it.")
        )
    else:
        qa.append(
            ("Why did the story stay messy?",
             f"The ending was too weak to clear things up. The clues were there, but the problem never got a proper solution.")
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["action"].tags)
    if f.get("resolved"):
        tags |= {"truth"}
    out: list[tuple[str, str]] = []
    if "scotch" in tags:
        out.append(("What is scotch tape?",
                    "Scotch tape is a sticky tape people use to hold small things together. It can also leave a clue behind if someone is moving things around.")) 
    if "sound" in tags:
        out.append(("What is a sound effect?",
                    "A sound effect is a little sound that helps a story feel real, like tap-tap or creak-creak. It can make a mystery feel suspenseful.")) 
    if "truth" in tags:
        out.append(("Why is telling the truth important?",
                    "Telling the truth helps people solve problems and trust one another. A lie can make a small mistake harder to fix.")) 
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    action = ACTIONS[params.action]
    resolution = RESOLUTIONS[params.resolution]
    return tell(
        place=place,
        clue=clue,
        action=action,
        resolution=resolution,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        culprit_name=params.culprit_name,
        culprit_gender=params.culprit_gender,
        adult_type=params.adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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


ASP_RULES = r"""
valid(P,C,A) :- place(P), clue(C), action(A), secret(P), dark(P), clue_scotch(C).
resolved(R) :- resolution(R), sense(R,S), S >= 2.
lesson(R) :- resolution(R), resolved(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.secret:
            lines.append(asp.fact("secret", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if "scotch" in c.tags:
            lines.append(asp.fact("clue_scotch", cid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in ASP:", sorted(a - b))
        print("  only in Python:", sorted(b - a))
    # Smoke test: ordinary generation should work.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(
        place="hall",
        clue="scotch",
        action="tap",
        resolution="apology",
        detective_name="Mia",
        detective_gender="girl",
        culprit_name="Noah",
        culprit_gender="boy",
        adult_type="mother",
    ),
    StoryParams(
        place="study",
        clue="scotch",
        action="creak",
        resolution="return",
        detective_name="Eli",
        detective_gender="boy",
        culprit_name="Ava",
        culprit_gender="girl",
        adult_type="father",
    ),
    StoryParams(
        place="pantry",
        clue="scotch",
        action="rustle",
        resolution="apology",
        detective_name="Zoe",
        detective_gender="girl",
        culprit_name="Leo",
        culprit_gender="boy",
        adult_type="mother",
    ),
]


def valid_story_choices() -> list[str]:
    return [k for k, v in RESOLUTIONS.items() if reasonable_action(v)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with scotch, clues, sound effects, and a moral lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--culprit")
    ap.add_argument("--culprit-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.resolution and not reasonable_action(RESOLUTIONS[args.resolution]):
        raise StoryError("That resolution is too weak for a proper moral lesson.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, action = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(valid_story_choices())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    culprit_gender = args.culprit_gender or rng.choice(["girl", "boy"])
    culprit = args.culprit or rng.choice(GIRL_NAMES if culprit_gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        clue=clue,
        action=action,
        resolution=resolution,
        detective_name=name,
        detective_gender=gender,
        culprit_name=culprit,
        culprit_gender=culprit_gender,
        adult_type=adult,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show resolved/1.\n#show lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, c, a in combos:
            print(f"  {p:8} {c:8} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.detective_name}: {p.clue} in {p.place} ({p.resolution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
