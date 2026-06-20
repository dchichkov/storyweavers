#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scribble_drastic_twist_happy_ending_whodunit.py
================================================================================

A standalone storyworld for a tiny whodunit-style mystery with a scribble,
a drastic twist, and a happy ending.

Domain premise:
- A child notices a mysterious scribble.
- Different clues and suspects are modeled as world state.
- A careful search reveals a drastic twist: the "mystery" is an accidental
  mix-up, not a mean act.
- The story ends happily with the mistaken blame cleared away.

The script follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python validity checks and an inline ASP twin
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""  # detective, helper, suspect, parent, witness
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    name: str
    dust: str
    hiding_spot: str
    mood: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Scribble:
    id: str
    line: str
    medium: str
    color: str
    shape: str
    can_smear: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    kind: str
    text: str
    points_to: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    cause: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    rules = [R_SUSPECT_SCRIBBLE, R_NOTICE_SMUDGE, R_PIECES_FIT, R_TWIST_REVEAL, R_HAPPY_END]
    while changed:
        changed = False
        for rule in rules:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _detective(world: World) -> Entity:
    for e in list(world.entities.values()):
        if e.role == "detective":
            return e
    raise StoryError("No detective in world.")


def _helper(world: World) -> Entity:
    for e in list(world.entities.values()):
        if e.role == "helper":
            return e
    raise StoryError("No helper in world.")


def _suspect(world: World) -> Entity:
    for e in list(world.entities.values()):
        if e.role == "suspect":
            return e
    raise StoryError("No suspect in world.")


def _scribble(world: World) -> Entity:
    return world.get("scribble")


def _clue_box(world: World) -> Entity:
    return world.get("cluebox")


def _reveal_stage(world: World) -> Entity:
    return world.get("reveal")


def R_SUSPECT_SCRIBBLE(world: World) -> list[str]:
    out: list[str] = []
    scribble = _scribble(world)
    suspect = _suspect(world)
    clue_box = _clue_box(world)
    if scribble.meters["noticed"] < THRESHOLD:
        return out
    sig = ("suspect_scribble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    suspect.memes["nervous"] += 1
    clue_box.meters["mystery"] += 1
    out.append(f"The strange scribble made everyone wonder if {suspect.id} had done something wrong.")
    return out


def R_NOTICE_SMUDGE(world: World) -> list[str]:
    out: list[str] = []
    scribble = _scribble(world)
    if scribble.meters["examined"] < THRESHOLD:
        return out
    sig = ("notice_smudge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective = _detective(world)
    helper = _helper(world)
    world.get("trail").meters["smear"] += 1
    detective.memes["curious"] += 1
    helper.memes["hope"] += 1
    out.append(f"{detective.id} bent close and saw a dusty smudge near the scribble, which made the question feel bigger.")
    return out


def R_PIECES_FIT(world: World) -> list[str]:
    out: list[str] = []
    clue_box = _clue_box(world)
    suspect = _suspect(world)
    twist = world.get("twist")
    if clue_box.meters["puzzle"] < THRESHOLD:
        return out
    sig = ("pieces_fit",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue_box.meters["clear"] += 1
    twist.meters["possible"] += 1
    out.append(f"Then the pieces fit: the neat shapes near the desk did not match a guilty mess at all.")
    return out


def R_TWIST_REVEAL(world: World) -> list[str]:
    out: list[str] = []
    twist = world.get("twist")
    if twist.meters["possible"] < THRESHOLD:
        return out
    sig = ("twist_reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    reveal = _reveal_stage(world)
    reveal.meters["truth"] += 1
    out.append("The drastic twist was that the scribble was only a practice line from a new marker, and the real trouble was a bumped stack of paper.")
    return out


def R_HAPPY_END(world: World) -> list[str]:
    out: list[str] = []
    reveal = _reveal_stage(world)
    if reveal.meters["truth"] < THRESHOLD:
        return out
    sig = ("happy_end",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective = _detective(world)
    helper = _helper(world)
    suspect = _suspect(world)
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    suspect.memes["relief"] += 1
    out.append(f"Everyone laughed softly when the mistake was cleared up, and {suspect.id} stopped looking worried.")
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    detective: str
    helper: str
    suspect: str
    parent: str
    scribble: str
    twist: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "classroom": Place("classroom", "the classroom", "chalk dust", "the art table", "bright", {"desk", "paper", "marker"}),
    "library": Place("library", "the library corner", "paper dust", "the reading rug", "quiet", {"book", "paper", "marker"}),
    "kitchen": Place("kitchen", "the kitchen nook", "flour dust", "the recipe board", "busy", {"paper", "marker", "note"}),
}

SCRIBBLES = {
    "marker": Scribble("marker", "a scribble on the paper", "marker", "blue", "loop", tags={"marker", "paper"}),
    "crayon": Scribble("crayon", "a scribble on the note", "crayon", "red", "swirl", tags={"crayon", "note"}),
    "pencil": Scribble("pencil", "a scribble in the notebook", "pencil", "gray", "zigzag", tags={"pencil", "paper"}),
}

TWISTS = {
    "practice": Twist("practice", "practice line", "the scribble was a practice line", "a new marker slipped", tags={"marker", "twist"}),
    "label": Twist("label", "label mix-up", "the scribble was a label that fell off", "the sticky label peeled loose", tags={"note", "twist"}),
    "art": Twist("art", "art surprise", "the scribble was part of a hidden picture", "an art project was folded over", tags={"paper", "twist"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ava", "Zoe", "Ella", "Maya", "Ivy"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Owen", "Theo", "Eli", "Max", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, place in SETTINGS.items():
        for scribble_id, scribble in SCRIBBLES.items():
            for twist_id, twist in TWISTS.items():
                if scribble.tags & place.tags:
                    combos.append((sid, scribble_id, twist_id))
    return combos


def explain_rejection(setting: str, scribble: str) -> str:
    return f"(No story: {scribble} does not fit naturally in {setting}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a scribble, a drastic twist, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scribble", choices=SCRIBBLES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.scribble and args.setting:
        if args.setting == "library" and args.scribble == "crayon":
            raise StoryError("(No story: crayons do not naturally make sense in that quiet library clue.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.scribble is None or c[1] == args.scribble)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, scribble_id, twist_id = rng.choice(sorted(combos))
    detect = args.detective or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != detect])
    suspect = args.suspect or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n not in {detect, helper}])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, detect, helper, suspect, parent, scribble_id, twist_id)


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.setting]
    world = World(place)
    detective = world.add(Entity(params.detective, kind="character", type="girl" if params.detective in GIRL_NAMES else "boy", role="detective"))
    helper = world.add(Entity(params.helper, kind="character", type="girl" if params.helper in GIRL_NAMES else "boy", role="helper"))
    suspect = world.add(Entity(params.suspect, kind="character", type="girl" if params.suspect in GIRL_NAMES else "boy", role="suspect"))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    scribble = world.add(Entity("scribble", type="thing", label=SCRIBBLES[params.scribble].line))
    cluebox = world.add(Entity("cluebox", type="thing", label="the clue box"))
    trail = world.add(Entity("trail", type="thing", label="the dusty trail"))
    twist = world.add(Entity("twist", type="thing", label=TWISTS[params.twist].label))
    reveal = world.add(Entity("reveal", type="thing", label="the reveal"))

    detective.memes["curious"] = 1.0
    helper.memes["hope"] = 1.0
    suspect.memes["worry"] = 1.0

    world.say(f"On a bright day at {place.name}, {detective.id} found a strange scribble near {place.hiding_spot}.")
    world.say(f"{helper.id} leaned in, and {suspect.id} looked nervous while {parent.label_word} watched nearby.")
    world.para()
    scribble.meters["noticed"] += 1
    detective.meters["noticed"] += 1
    world.say(f'"{scribble.line}!" {detective.id} said. "Who could have made that?"')
    world.say(f"It was the sort of mystery that made the room feel very still.")

    world.para()
    scribble.meters["examined"] += 1
    cluebox.meters["puzzle"] += 1
    world.say(f"{helper.id} found a tiny clue by the desk and set it beside the scribble.")
    world.say(f"{parent.label_word.capitalize()} said to look carefully before guessing.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"{detective.id} compared the clue, the dusty trail, and the scribble's shape.")
    world.say(f"Then the drastic twist arrived: the scribble matched a practice line, not a secret message.")
    twist.meters["possible"] += 1
    reveal.meters["truth"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"It turned out the real problem was a bumped stack of paper and a marker left uncapped.")
    world.say(f"{suspect.id} had not done anything wrong, and the whole room felt lighter at once.")
    propagate(world, narrate=True)

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect,
        parent=parent,
        scribble=scribble,
        cluebox=cluebox,
        trail=trail,
        twist=twist,
        reveal=reveal,
        setting=place,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the word "scribble" and ends with a happy twist.',
        f"Tell a mystery story where {f['detective'].id} notices a scribble at {f['setting'].name}, but the answer turns out kinder than expected.",
        f'Write a short story in whodunit style with a drastic twist and a happy ending, using the word "drastic".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective, helper, suspect, parent = f["detective"], f["helper"], f["suspect"], f["parent"]
    scribble, twist, reveal = f["scribble"], f["twist"], f["reveal"]
    qa = [
        QAItem(
            question="Who noticed the mysterious scribble?",
            answer=f"{detective.id} noticed it first. {detective.id} was the one who kept asking careful questions instead of jumping to a guess."
        ),
        QAItem(
            question="What made the mystery feel serious?",
            answer=f"The scribble looked odd, and {suspect.id} seemed nervous. That made everyone think something drastic might have happened."
        ),
        QAItem(
            question="What was the drastic twist?",
            answer=f"The twist was that the scribble was not a secret clue from a bad deed at all. It was only a practice line from a marker, and the real trouble was a small messy accident."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. {suspect.id} was cleared, the room's little mess was understood, and everyone could laugh because the mystery was solved kindly."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scribble?",
            answer="A scribble is a quick, messy line or drawing made by a pencil, pen, crayon, or marker."
        ),
        QAItem(
            question="What does drastic mean?",
            answer="Drastic means very sudden or very extreme. A drastic change is a big change, not a tiny one."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what you thought was happening. It makes the story feel different in a new way."
        ),
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where the characters try to figure out who did something or what really happened."
        ),
    ]


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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
noticed_scribble :- scribble_notice.
smudge_seen :- scribble_examined.
pieces_fit :- clue_puzzle.
twist_reveal :- twist_possible.
happy_end :- twist_reveal.

valid_story(S, Sc, T) :- setting(S), scribble(Sc), twist(T), compatible(S, Sc), compatible_twist(Sc, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for scid, sc in SCRIBBLES.items():
        lines.append(asp.fact("scribble", scid))
        for tag in sc.tags:
            lines.append(asp.fact("compatible", tag, scid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if asp_set - py:
            print("  only in clingo:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, scribble=None, twist=None, detective=None, helper=None, suspect=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_scribble_choice(scribble: str) -> str:
    return f"(No story: the word {scribble!r} does not fit the tiny mystery well here.)"


def valid_story_with_params(args: argparse.Namespace) -> bool:
    return True


def pair_name(a: str, b: str) -> str:
    return f"{a} and {b}"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("classroom", "Mia", "Noah", "Luna", "mother", "marker", "practice"),
    StoryParams("library", "Leo", "Ivy", "Ben", "father", "pencil", "art"),
    StoryParams("kitchen", "Ava", "Theo", "Maya", "mother", "crayon", "label"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
