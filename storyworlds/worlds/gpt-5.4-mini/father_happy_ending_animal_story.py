#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/father_happy_ending_animal_story.py
====================================================================

A standalone storyworld about an animal child, a small problem, a helpful
father, and a happy ending.

The tiny domain:
- A young animal wants to reach something nice.
- The path is blocked by a small danger or worry.
- The child makes a poor choice, then calls for help.
- The father uses a sensible fix.
- The ending proves the change with a warm, safe image.

Style goal:
- Simple, child-facing, concrete prose.
- Animal-story feel: den, nest, pond, meadow, cubs, pups, kits, chicks.
- Happy ending only.
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
SENSE_MIN = 2
BRAVE_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"father", "dad", "male"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mother", "mom", "female"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"cub", "kit", "chick", "pup", "foal"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    cozy: str
    risky_spot: str
    ending_image: str

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
class Want:
    id: str
    verb: str
    goal: str
    lure: str
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
class Hazard:
    id: str
    label: str
    kind: str
    danger_line: str
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["fear"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("father").memes["alert"] += 1
    out.append("__worry__")
    return out


def _r_resolve(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hazard = world.get("hazard")
    if child.meters["stuck"] < THRESHOLD:
        return out
    if hazard.meters["blocked"] < THRESHOLD:
        return out
    sig = ("resolve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("father").memes["pride"] += 1
    out.append("__resolve__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("resolve", _r_resolve)]


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def risk_ok(want: Want, hazard: Hazard) -> bool:
    return want.id in hazard.tags


def fire_severity(hazard: Hazard, delay: int) -> int:
    return 1 + delay if hazard.kind in {"branch", "mud"} else 2 + delay


def contained(fix: Fix, hazard: Hazard, delay: int) -> bool:
    return fix.power >= fire_severity(hazard, delay)


def explain_rejection(want: Want, hazard: Hazard) -> str:
    return f"(No story: {want.label} does not really fit with {hazard.label}, so there is no honest problem to solve.)"


def explain_fix_rejection(fid: str) -> str:
    fix = FIXES[fid]
    return f"(Refusing fix '{fid}': it is too weak or too odd for a child-safe happy ending. Try one of: {', '.join(f.id for f in sensible_fixes())}.)"


def _do_attempt(world: World, hazard: Hazard) -> None:
    world.get("child").meters["stuck"] += 1
    world.get("hazard").meters["blocked"] += 1
    propagate(world, narrate=False)


def predict(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    _do_attempt(sim, hazard)
    return {
        "stuck": sim.get("child").meters["stuck"] >= THRESHOLD,
        "alert": sim.get("father").memes["alert"],
    }


def intro(world: World, child: Entity, father: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At {place.label}, a little {child.type} named {child.id} lived with {father.label}."
    )
    world.say(
        f"{child.id} loved the soft {place.cozy} and the bright day near the {place.risky_spot}."
    )


def want_scene(world: World, child: Entity, want: Want) -> None:
    child.memes["desire"] += 1
    world.say(
        f"One morning, {child.id} wanted to {want.verb}. {want.lure}."
    )


def warn_scene(world: World, father: Entity, child: Entity, hazard: Hazard) -> None:
    pred = predict(world, hazard)
    father.memes["care"] += 1
    world.facts["pred"] = pred
    world.say(
        f"{child.id} paused, because {hazard.danger_line}."
    )
    world.say(
        f"Then {father.label} nodded toward the danger and said, "
        f"\"Let's do this the safe way.\""
    )


def rush_scene(world: World, child: Entity, want: Want) -> None:
    child.memes["brave"] += 1
    world.say(f"{child.id} ran ahead anyway and tried to {want.verb}.")


def accident_scene(world: World, hazard: Hazard) -> None:
    child = world.get("child")
    child.meters["stuck"] += 1
    world.get("hazard").meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the {hazard.label} got in the way, and {child.id} could not quite make it."
    )


def call_father(world: World, child: Entity, father: Entity) -> None:
    child.memes["fear"] += 1
    world.say(f"\"{father.id}!\" {child.id} called, and {father.label} came right away.")


def fix_scene(world: World, father: Entity, fix: Fix, hazard: Hazard) -> None:
    world.get("hazard").meters["blocked"] = 0.0
    world.get("child").meters["stuck"] = 0.0
    father.memes["pride"] += 1
    world.say(
        f"{father.label.capitalize()} {fix.text.replace('{hazard}', hazard.label)}."
    )
    world.say(
        f"The danger was gone, and the path opened again at once."
    )


def lesson_scene(world: World, father: Entity, child: Entity, want: Want) -> None:
    child.memes["joy"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"{father.label.capitalize()} gave {child.id} a hug and said that brave paws "
        f"are paws that ask for help."
    )
    world.say(
        f"{child.id} smiled and promised to listen next time."
    )


def ending_scene(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"In the end, {child.id} was safe and happy, with {place.ending_image}."
    )
    world.say(
        f"{child.id} and {world.get('father').label} stayed together, warm and glad."
    )


def tell(place: Place, want: Want, hazard: Hazard, fix: Fix,
         child_name: str = "Milo", child_type: str = "cub",
         father_label: str = "father", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    father = world.add(Entity(id="father", kind="character", type="father", label=father_label, role="father"))
    world.add(Entity(id="hazard", type="thing", label=hazard.label))
    world.facts.update(place=place, want=want, hazard=hazard, fix=fix, delay=delay)

    intro(world, child, father, place)
    world.para()
    want_scene(world, child, want)
    warn_scene(world, father, child, hazard)
    rush_scene(world, child, want)
    accident_scene(world, hazard)
    call_father(world, child, father)
    if contained(fix, hazard, delay):
        world.para()
        fix_scene(world, father, fix, hazard)
        lesson_scene(world, father, child, want)
        world.para()
        ending_scene(world, child, place)
        outcome = "happy"
    else:
        raise StoryError("This world only tells happy endings; choose a stronger fix.")
    world.facts["outcome"] = outcome
    return world


PLACES = {
    "pond": Place("pond", "the pond", "reeds and lily pads", "muddy bank", "the ripples shining under the sun"),
    "meadow": Place("meadow", "the meadow", "soft grass and flowers", "thorny briars", "the flowers nodding beside the path"),
    "nest": Place("nest", "the nest", "warm twigs and feathers", "a loose branch", "the eggs tucked safely under a wing"),
}

WANTS = {
    "lily": Want("lily", "pick a lily", "a pale lily by the water", "Its petals looked like tiny bowls", {"pond"}),
    "berries": Want("berries", "reach the berries", "a bunch of ripe berries", "The berries were red and sweet", {"meadow"}),
    "eggs": Want("eggs", "check the eggs", "a little nest full of eggs", "The nest looked cozy and important", {"nest"}),
}

HAZARDS = {
    "mud": Hazard("mud", "the muddy bank", "mud", "The bank was slippery and could trap small paws", {"pond"}),
    "briers": Hazard("briers", "the briars", "thorn", "The briars could scratch a cub's fur", {"meadow"}),
    "branch": Hazard("branch", "the loose branch", "branch", "The branch wobbled and could drop a chick", {"nest"}),
}

FIXES = {
    "bridge": Fix("bridge", 3, 3, "picked up a sturdy stick and made a little bridge over the {hazard}", "tried to make a bridge, but it slipped", "made a safe little bridge over the {hazard}", {"pond"}),
    "around": Fix("around", 3, 3, "walked around the {hazard} and held out a steady paw", "tried to go around, but the way was still blocked", "walked around the {hazard}", {"meadow", "nest"}),
    "wait": Fix("wait", 2, 2, "waited for the ground to settle before taking another step", "waited, but nothing changed", "waited for the ground to settle", {"pond", "meadow", "nest"}),
}

GENTLE_NAMES = ["Milo", "Pip", "Luna", "Toby", "Nina", "Rae", "Bram", "Kiki"]
CHILD_TYPES = ["cub", "kit", "pup", "chick"]


@dataclass
@dataclass
class StoryParams:
    place: str
    want: str
    hazard: str
    fix: str
    child_name: str
    child_type: str
    father_label: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for wid, want in WANTS.items():
            for hid, hazard in HAZARDS.items():
                if want.id in hazard.tags:
                    for fid, fix in FIXES.items():
                        if place.id in fix.tags and fix.sense >= SENSE_MIN:
                            out.append((pid, wid, hid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child with a father and a happy ending that includes "{f["father"].label}".',
        f"Tell a gentle story about {f['child'].id}, {f['father'].label}, and {f['want'].label}, ending with a safe, warm scene.",
        f'Write a simple story where a little animal wants to {f["want"].verb} but needs help from {f["father"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get("child")
    father = world.get("father")
    want = f["want"]
    hazard = f["hazard"]
    fix = f["fix"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, a little {child.type}, and {father.label}. They are the ones who live through the little trouble and the happy ending."
        ),
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {want.verb}. {want.lure}, so it felt exciting and hard to wait."
        ),
        QAItem(
            question="Why did the child need help?",
            answer=f"The {hazard.label} made the idea tricky because {hazard.danger_line.lower()}. That is why {father.label} had to step in and help safely."
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{father.label.capitalize()} {fix.qa_text.replace('{hazard}', hazard.label)}. That worked because it was strong enough to beat the problem and keep the child safe."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {child.id} safe and smiling at {f['place'].ending_image}. The problem was gone, so the last picture is calm and warm."
        ),
    ]


WORLD_KNOWLEDGE = {
    "father": [QAItem("What is a father?", "A father is a grown-up parent who can help, protect, and comfort a child.")],
    "cub": [QAItem("What is a cub?", "A cub is a baby animal, like a baby bear or a baby fox.")],
    "kit": [QAItem("What is a kit?", "A kit is a baby animal, often a baby fox, rabbit, or beaver.")],
    "pup": [QAItem("What is a pup?", "A pup is a young animal, like a puppy or a baby wolf.")],
    "chick": [QAItem("What is a chick?", "A chick is a baby bird.")],
    "pond": [QAItem("What is a pond?", "A pond is a small body of water, smaller than a lake.")],
    "meadow": [QAItem("What is a meadow?", "A meadow is an open field with grass and flowers.")],
    "nest": [QAItem("What is a nest?", "A nest is a cozy place birds make for eggs and chicks.")],
    "mud": [QAItem("Why can mud be slippery?", "Mud can be slippery because it is wet and soft, so paws or shoes can slide.")],
    "thorn": [QAItem("Why are briars or thorns a problem?", "Thorns can scratch skin or fur, so animals try not to brush into them.")],
    "branch": [QAItem("Why can a loose branch be dangerous?", "A loose branch can wobble or break, so it is not a steady place to stand.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["father"].type, world.facts["place"].id, world.facts["hazard"].kind}
    out: list[QAItem] = []
    for tag in ["father", "cub", "kit", "pup", "chick", "pond", "meadow", "nest", "mud", "thorn", "branch"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "lily", "mud", "bridge", "Milo", "cub", "father"),
    StoryParams("meadow", "berries", "briers", "around", "Luna", "kit", "father"),
    StoryParams("nest", "eggs", "branch", "wait", "Toby", "chick", "father"),
]


def outcome_of(params: StoryParams) -> str:
    return "happy"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for wid in WANTS:
        lines.append(asp.fact("want", wid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,W,H) :- want(W), hazard(H), fix(F), sense(F,S), sense_min(M), S >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        a = set(asp_valid_combos())
        p = set(valid_combos())
        if a == p:
            print(f"OK: gate matches valid_combos() ({len(a)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid_combos")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"VERIFY FAILED: {e}")
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a father and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combos available.")
    pid, wid, hid = rng.choice(combos)
    if args.place:
        pid = args.place
    if args.want:
        wid = args.want
    if args.hazard:
        hid = args.hazard
    want, hazard = WANTS[wid], HAZARDS[hid]
    if not risk_ok(want, hazard):
        raise StoryError(explain_rejection(want, hazard))
    fid = args.fix or rng.choice([f.id for f in sensible_fixes() if place_ok(f, pid)])
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(args.fix))
    name = args.name or rng.choice(GENTLE_NAMES)
    ctype = args.child_type or rng.choice(CHILD_TYPES)
    return StoryParams(pid, wid, hid, fid, name, ctype, "father")


def place_ok(fix: Fix, pid: str) -> bool:
    return pid in fix.tags


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], WANTS[params.want], HAZARDS[params.hazard], FIXES[params.fix],
                 child_name=params.child_name, child_type=params.child_type, father_label=params.father_label, delay=params.delay)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
