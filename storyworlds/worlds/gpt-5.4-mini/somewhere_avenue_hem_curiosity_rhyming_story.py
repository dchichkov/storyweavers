#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/somewhere_avenue_hem_curiosity_rhyming_story.py
===============================================================================

A standalone storyworld for a tiny rhyming story domain built from the seed
words "somewhere", "avenue", and "hem", with Curiosity as the central feature.

Premise:
- A curious child follows a small clue somewhere along the avenue.
- Their outfit's hem gets involved in a little snaggy problem.
- A careful helper and a simple fix turn the moment into a bright ending.

The world is intentionally small and classical: a few typed entities, physical
meters and emotional memes, forward-chained causal rules, a reasonableness gate,
a declarative ASP twin, and three grounded Q&A sets.
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    wearable: bool = False
    helper: bool = False
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
    avenue: str
    somewhere: str
    width: str
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
class Hint:
    id: str
    label: str
    place_word: str
    shine: str
    sound: str
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
class Problem:
    id: str
    label: str
    snag_kind: str
    risk_word: str
    power: int
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
    label: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_snag(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hem = world.get("hem")
    if child.meters["wandering"] < THRESHOLD or child.meters["curious"] < THRESHOLD:
        return out
    sig = ("snag",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hem.meters["snagged"] += 1
    child.memes["startle"] += 1
    out.append("__snag__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    hem = world.get("hem")
    if hem.meters["snagged"] < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("street").meters["tension"] += 1
    return out


CAUSAL_RULES = [Rule("snag", "physical", _r_snag), Rule("settle", "physical", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def risk_at_hand(problem: Problem) -> bool:
    return problem.id == "bramble"


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_works(fix: Fix, problem: Problem) -> bool:
    return fix.power >= problem.power


def predict_snag(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["wandering"] += 1
    sim.get("child").meters["curious"] += 1
    _do_problem(sim, sim.get("problem"))
    return {
        "snagged": sim.get("hem").meters["snagged"] >= THRESHOLD,
        "tension": sim.get("street").meters["tension"],
    }


def _do_problem(world: World, problem: Entity, narrate: bool = True) -> None:
    if problem.label == "bramble":
        world.get("hem").meters["snagged"] += 1
        propagate(world, narrate=narrate)


def opening(world: World, child: Entity, guide: Entity, place: Place, hint: Hint) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Somewhere along the avenue, {child.id} went by a little {place.name}, "
        f"with {guide.id} close behind in the bright clean light."
    )
    world.say(
        f"{child.id} felt a spark of Curiosity. {child.pronoun().capitalize()} "
        f"followed {hint.sound} and {hint.shine}, and wondered what the clue might mean."
    )
    world.say(
        f"The {place.width} little path looked like a rhyme, and every step felt "
        f"like a line."
    )


def notice_hem(world: World, child: Entity, hem: Entity) -> None:
    world.say(
        f"But the {hem.label} on {child.pronoun('possessive')} coat danced and swayed, "
        f"and skimmed the stones with a silky parade."
    )


def wander(world: World, child: Entity, place: Place) -> None:
    child.meters["wandering"] += 1
    child.memes["curious"] += 1
    world.say(
        f"{child.id} wandered the avenue gently and slow, looking for somewhere "
        f"the small clue could go."
    )


def tempt(world: World, child: Entity, hint: Hint) -> None:
    world.say(
        f'"Could the bright little sparkle be hidden right here?" {child.id} asked, '
        f"with wonder and cheer."
    )
    world.say(
        f"The sound of {hint.sound} seemed nearer, the shine looked so clear, and "
        f"Curiosity tugged {child.pronoun('object')} onward with no fear."
    )


def warn(world: World, guide: Entity, child: Entity, problem: Problem, hem: Entity) -> None:
    pred = predict_snag(world)
    guide.memes["care"] += 1
    if pred["snagged"]:
        world.say(
            f'{guide.id} smiled and said, "Careful now, dear. That {problem.label} '
            f'can catch at your hem if you draw too near."'
        )
        world.say(
            f'"A snagged-up hem can trip up your step, and then your whole afternoon '
            f'might lose its pep."'
        )
    else:
        world.say(
            f"{guide.id} glanced at the path and stayed close beside, ready to help "
            f"if the little quest tried to slide."
        )


def defy(world: World, child: Entity) -> None:
    child.memes["boldness"] += 1
    world.say(
        f"But {child.id} had Curiosity humming like a tune, so {child.id} leaned in "
        f"and reached there soon."
    )


def snag(world: World, problem: Problem) -> None:
    _do_problem(world, world.get("problem"))
    world.say(
        f"The bramble brushed softly, then snagged at the hem, and the coat gave a "
        f"tiny surprised gem."
    )
    world.say(
        f"It did not tear wide or scatter the thread, but it stopped the child short "
        f"and asked them to tread."
    )


def rescue(world: World, guide: Entity, fix: Fix, hem: Entity) -> None:
    world.say(
        f"{guide.id} knelt right down and used {fix.text}, quick and light, to free "
        f"the hem from its prickly bite."
    )
    hem.meters["snagged"] = 0.0
    world.say(
        f"The coat came unstuck, and the little day shone, as smooth as a pebble "
        f"that rolls to its home."
    )


def lesson(world: World, guide: Entity, child: Entity, fix: Fix) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'"I like your Curiosity," {guide.id} said warm. "Just keep it safe and '
        f"calm through the storm."
    )
    world.say(
        f'"When something is prickly or tricky or tight, a gentle good fix is the '
        f"brightest of light."
    )
    world.say(
        f"{child.id} nodded and grinned, now wiser than before, with a clean little "
        f"hem and a heart wanting more."
    )
    world.say(
        f"So they walked on together, through somewhere and through, with Curiosity "
        f"safe and the avenue blue."
    )


def explain_curiosity(world: World, child: Entity, guide: Entity, problem: Problem) -> None:
    world.say(
        f"{child.id} wanted to know what was hidden nearby, because Curiosity made "
        f"{child.pronoun('possessive')} eyes dart high."
    )


def tell(place: Place, hint: Hint, problem: Problem, fix: Fix,
         child_name: str = "Mina", child_gender: str = "girl",
         guide_name: str = "Aunt June", guide_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="curious_child", traits=["curious"]))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender,
                             role="guide", traits=["calm"]))
    world.add(Entity(id="street", type="place", label="avenue"))
    hem = world.add(Entity(id="hem", type="thing", label="hem"))
    world.add(Entity(id="problem", type="thing", label=problem.label))
    world.facts["place"] = place
    world.facts["hint"] = hint
    world.facts["problem"] = problem
    world.facts["fix"] = fix
    world.facts["child"] = child
    world.facts["guide"] = guide
    world.facts["hem"] = hem

    opening(world, child, guide, place, hint)
    notice_hem(world, child, hem)
    world.para()
    wander(world, child, place)
    tempt(world, child, hint)
    explain_curiosity(world, child, guide, problem)
    warn(world, guide, child, problem, hem)
    world.para()
    defy(world, child)
    snag(world, problem)
    world.para()
    if fix_works(fix, problem):
        rescue(world, guide, fix, hem)
        lesson(world, guide, child, fix)
    else:
        world.say(
            f"The tiny fix was not enough, and the prickly spot held tight. "
            f"Still, {guide.id} kept {child.id} calm until the hem was free in sight."
        )
        hem.meters["snagged"] = 0.0
        child.memes["relief"] += 1
        world.say(
            f"Together they stepped away, safe and sound, with the lesson tucked "
            f"away like a ribbon found."
        )

    outcome = "fixed" if fix_works(fix, problem) else "recovered"
    world.facts["outcome"] = outcome
    return world


PLACES = {
    "street_corner": Place("street_corner", "little corner garden", "avenue", "somewhere", "narrow", tags={"avenue"}),
    "bookshop": Place("bookshop", "bookshop window", "avenue", "somewhere", "small", tags={"avenue"}),
    "bakery": Place("bakery", "bakery door", "avenue", "somewhere", "cozy", tags={"avenue"}),
}

HINTS = {
    "crumb": Hint("crumb", "crumb", "bench seat", "sparkle", "tiny tap", tags={"curiosity"}),
    "note": Hint("note", "note", "lamp post", "glint", "rustle", tags={"curiosity"}),
    "ribbon": Hint("ribbon", "ribbon", "brick wall", "shimmer", "flutter", tags={"curiosity"}),
}

PROBLEMS = {
    "bramble": Problem("bramble", "bramble", "prickly snag", "hem", 2, tags={"hem"}),
    "fence": Problem("fence", "low fence", "catch", "hem", 1, tags={"hem"}),
}

FIXES = {
    "gentle_pull": Fix("gentle_pull", "a gentle pull", 2, 2,
                       "a gentle pull", "a gentle tug", "freed the hem with a gentle pull", tags={"hem"}),
    "careful_turn": Fix("careful_turn", "a careful turn", 3, 3,
                        "a careful turn", "a careful turn", "carefully turned the coat free", tags={"hem"}),
    "clip": Fix("clip", "a tiny clip", 1, 1,
                "a tiny clip", "a tiny clip", "snipped the snag free", tags={"hem"}),
}

TRAITS = ["curious", "bright-eyed", "gentle", "cheerful", "thoughtful"]
NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tess", "Ruby", "Owen", "Milo", "Finn", "Jules"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid in PLACES:
        for hid in HINTS:
            for prid in PROBLEMS:
                for fid, fix in FIXES.items():
                    if risk_at_hand(PROBLEMS[prid]) and fix.sense >= SENSE_MIN:
                        combos.append((pid, hid, prid, fid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    hint: str
    problem: str
    fix: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
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


KNOWLEDGE = {
    "curiosity": [("What is curiosity?",
                   "Curiosity is the wish to find out more. It makes children ask questions and look closely at things.")],
    "hem": [("What is a hem?",
             "A hem is the folded edge at the bottom of a coat, dress, or skirt.")],
    "avenue": [("What is an avenue?",
                "An avenue is a wide street with places and houses along it.")],
    "bramble": [("What is a bramble?",
                 "A bramble is a prickly plant with sharp stems that can snag cloth.")],
    "snag": [("What does snag mean?",
              "A snag is when cloth catches on something rough or sharp and gets stuck.")],
    "clip": [("What does a tiny clip do?",
              "A tiny clip can help hold or free a small bit of cloth without being rough.")],
}
KNOWLEDGE_ORDER = ["curiosity", "hem", "avenue", "bramble", "snag", "clip"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, hint, problem = f["place"], f["hint"], f["problem"]
    return [
        f'Write a rhyming story for a young child that uses the words "somewhere", "avenue", and "hem".',
        f"Tell a gentle Curiosity story where {f['child'].id} follows a little clue along the avenue and a hem gets snagged on {problem.label}.",
        f"Write a small rhyming tale about a curious child, a helper, and a hem that needs a safe fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, guide, problem, fix = f["child"], f["guide"], f["problem"], f["fix"]
    qa = [
        QAItem("Who is the story about?",
               f"It is about {child.id}, a curious child, and {guide.id}, who stayed nearby to help. The story follows their little walk along the avenue."),
        QAItem("What made the child keep looking around?",
               f"Curiosity kept {child.id} looking around and wondering what was happening somewhere on the avenue. That feeling made the child follow the clue before noticing the hem."),
        QAItem("What got stuck in the story?",
               f"The hem got snagged on {problem.label}. It was only a small snag, but it stopped the child long enough for the helper to step in."),
    ]
    if f["outcome"] == "fixed":
        qa.append(QAItem(
            "How was the hem freed?",
            f"{guide.id} used {fix.qa_text} to free the hem. The safe fix worked because it was gentle enough for the snag and strong enough to solve it."
        ))
        qa.append(QAItem(
            "How did the child feel at the end?",
            f"{child.id} felt relieved and happy. Curiosity was still there, but now it was paired with a calm, safe choice."
        ))
    else:
        qa.append(QAItem(
            "What happened when the first fix was not enough?",
            f"The first fix was not enough, so {guide.id} stayed calm and helped {child.id} step back. The hem still came free, but only after they slowed down and tried again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hint"].tags) | set(world.facts["problem"].tags) | set(world.facts["fix"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("street_corner", "crumb", "bramble", "gentle_pull", "Mina", "girl", "Aunt June", "woman"),
    StoryParams("bookshop", "note", "bramble", "careful_turn", "Owen", "boy", "Dad", "man"),
    StoryParams("bakery", "ribbon", "fence", "clip", "Ivy", "girl", "Mom", "woman"),
]


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return f"(No story: the problem '{problem.label}' and fix '{fix.label}' do not form a strong enough rhyming rescue.)"


def explain_fix(rid: str) -> str:
    r = FIXES[rid]
    if r.sense < SENSE_MIN:
        better = " / ".join(sorted(f.id for f in sensible_fixes()))
        return f"(Refusing fix '{rid}': it scores too low on common sense. Try: {better}.)"
    return ""


ASP_RULES = r"""
valid(P,H,R,F) :- place(P), hint(H), problem(R), fix(F), risk(R), sense(F,S), sense_min(M), S >= M.
outcome(fixed) :- chosen_fix(F), power(F,P), chosen_problem(R), power_req(R,Q), P >= Q.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HINTS:
        lines.append(asp.fact("hint", hid))
    for rid, r in PROBLEMS.items():
        lines.append(asp.fact("problem", rid))
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("power_req", rid, r.power))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test produced story text.")
    except Exception as e:
        rc = 1
        print("SMOKE TEST FAILED:", e)
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming curiosity storyworld with hem and avenue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hint", choices=HINTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["woman", "man"])
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hint is None or c[1] == args.hint)
              and (args.problem is None or c[2] == args.problem)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hint, problem, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    guide = args.guide or ("Aunt June" if guide_gender == "woman" else "Uncle Ray")
    return StoryParams(place, hint, problem, fix, name, gender, guide, guide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], HINTS[params.hint], PROBLEMS[params.problem], FIXES[params.fix],
                 params.child_name, params.child_gender, params.guide_name, params.guide_gender)
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
