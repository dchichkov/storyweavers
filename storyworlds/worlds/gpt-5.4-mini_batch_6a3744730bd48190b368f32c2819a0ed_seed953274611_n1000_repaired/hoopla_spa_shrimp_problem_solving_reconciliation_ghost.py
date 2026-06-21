#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hoopla_spa_shrimp_problem_solving_reconciliation_ghost.py
==========================================================================================

A small ghost-story storyworld: children visit a sleepy spa, a spooky hoopla
starts around a shrimp-shaped treat, they solve the mystery, and the restless
ghost reconciles with the guests once the problem is understood.

The world is deliberately tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- inline ASP rules that mirror the Python logic
- three QA sets grounded in simulated state

Run:
    python storyworlds/worlds/gpt-5.4-mini/hoopla_spa_shrimp_problem_solving_reconciliation_ghost.py
    python storyworlds/worlds/gpt-5.4-mini/hoopla_spa_shrimp_problem_solving_reconciliation_ghost.py --verify
    python storyworlds/worlds/gpt-5.4-mini/hoopla_spa_shrimp_problem_solving_reconciliation_ghost.py --qa --json
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
    spooky: bool = False
    tasty: bool = False
    soothing: bool = False
    helps: bool = False

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
    quiet: bool = False
    spa_like: bool = False
    has_steam: bool = False
    has_water: bool = False
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
class Problem:
    id: str
    label: str
    cause: str
    effect: str
    reason: str
    noisy: bool = False
    solvable: bool = True
    scary: bool = True
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
    method: str
    calm_text: str
    fail_text: str
    power: int
    sense: int
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


def _r_spook(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    if not ghost or ghost.meters["trouble"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("child", "parent"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
    out.append("The hallway felt colder, and everyone held still for a breath.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if ghost.meters["trouble"] < THRESHOLD:
        return out
    if child.memes["understanding"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["comfort"] += 1
    child.memes["kindness"] += 1
    out.append("The coldness softened, as if the ghost had finally been heard.")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_at_risk(problem: Problem, place: Place) -> bool:
    return problem.noisy and place.spa_like


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def can_solve(fix: Fix, problem: Problem) -> bool:
    return fix.power >= (2 if problem.scary else 1)


def predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    sim.get("ghost").meters["trouble"] += 1
    propagate(sim, narrate=False)
    return {"spooky": sim.get("child").memes["fear"] >= THRESHOLD}


def tell_intro(world: World, child: Entity, parent: Entity, place: Place) -> None:
    world.say(
        f"{child.id} and {parent.label_word.capitalize()} went to the {place.label} "
        f"for a quiet afternoon. The towels were warm, the lights were low, and the air "
        f"smelled like soap and steam."
    )


def tell_hoopla(world: World, child: Entity, problem: Problem, shrimp: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then a strange hoopla began near the snack tray. A shrimp-shaped treat "
        f"knocked against a bowl, and a pale ghost puffed up from the mist as if "
        f"someone had called its name."
    )
    world.say(
        f'"Why is it making such a fuss?" {child.id} whispered. '
        f"The little shrimp gleamed pink in the steam."
    )


def warn_and_think(world: World, parent: Entity, child: Entity, problem: Problem, fix: Fix) -> None:
    pred = predict(world, problem)
    parent.memes["care"] += 1
    world.facts["predicted_spooky"] = pred["spooky"]
    world.say(
        f'"That hoopla means something is wrong," {parent.label_word.capitalize()} said. '
        f'"Let\'s think it through before we get scared."'
    )
    if pred["spooky"]:
        world.say(
            f"{child.id} looked again and noticed the ghost was not angry at the shrimp. "
            f"It seemed upset about the noise and the lonely cold room."
        )


def solve_problem(world: World, child: Entity, parent: Entity, ghost: Entity, fix: Fix, problem: Problem) -> None:
    child.memes["understanding"] += 1
    world.say(
        f"{child.id} pointed to the tray and said, "
        f'"Maybe the ghost just wants the room calm again." '
        f"Then {child.id} used {fix.method}."
    )
    if can_solve(fix, problem):
        ghost.meters["trouble"] = 0.0
        world.say(
            f"{fix.calm_text}. The hoopla faded, and the ghost drifted closer, no longer rattling the cups."
        )
    else:
        ghost.meters["trouble"] += 1
        world.say(f"{fix.fail_text}. The cold stayed sharp, and the spooky fuss only grew.")


def reconcile(world: World, child: Entity, parent: Entity, ghost: Entity, place: Place) -> None:
    child.memes["kindness"] += 1
    ghost.memes["comfort"] += 1
    world.say(
        f"Then {child.id} offered the shrimp treat on a little plate and bowed politely. "
        f'"We were noisy," {child.id} said. "We can be quiet now."'
    )
    world.say(
        f"The ghost stopped hovering so hard. It gave a slow, swirly nod, and the {place.label} "
        f"felt warm again, like a blanket fresh from the dryer."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled, and together they left the steam room in peace."
    )


def tell_story(place: Place, problem: Problem, fix: Fix, child_name: str = "Mina",
               child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost", label="the ghost", spooky=True))
    shrimp = world.add(Entity(id="shrimp", kind="thing", type="food", label="a shrimp-shaped treat", tasty=True))
    child.memes["curiosity"] = 1
    tell_intro(world, child, parent, place)
    world.para()
    tell_hoopla(world, child, problem, shrimp)
    warn_and_think(world, parent, child, problem, fix)
    world.para()
    solve_problem(world, child, parent, ghost, fix, problem)
    world.para()
    reconcile(world, child, parent, ghost, place)
    world.facts.update(child=child, parent=parent, ghost=ghost, shrimp=shrimp, place=place, problem=problem, fix=fix)
    return world


PLACES = {
    "spa": Place(id="spa", label="spa", quiet=True, spa_like=True, has_steam=True, has_water=True),
    "bathhouse": Place(id="bathhouse", label="bathhouse", quiet=True, spa_like=True, has_steam=True, has_water=True),
    "pool": Place(id="pool", label="pool room", quiet=False, spa_like=False, has_steam=False, has_water=True),
}

PROBLEMS = {
    "echo": Problem(id="echo", label="loud echo", cause="a shouting game", effect="the ghost got jumpy", reason="the room was too quiet and every sound bounced", noisy=True, solvable=True, scary=True, tags={"ghost", "hoopla"}),
    "steam": Problem(id="steam", label="foggy steam", cause="a vent", effect="the ghost could not see the calm face", reason="steam made the room look spooky", noisy=False, solvable=True, scary=True, tags={"ghost", "spa"}),
    "shrimp": Problem(id="shrimp", label="shrimp confusion", cause="a snack tray", effect="the ghost mistook the snack for a message", reason="the shrimp looked like a tiny curled signal", noisy=True, solvable=True, scary=False, tags={"shrimp", "hoopla"}),
}

FIXES = {
    "speak_softly": Fix(id="speak_softly", label="soft voices", method="speaking softly", calm_text="The child and parent lowered their voices and moved slowly", fail_text="They tried whispering, but the hoopla kept bouncing around", power=2, sense=3, tags={"quiet"}),
    "turn_light_on": Fix(id="turn_light_on", label="bright light", method="turning on the lamp", calm_text="A lamp clicked on, and the ghost's pale shape became easy to see", fail_text="The lamp blinked, but the room still felt unsettled", power=2, sense=2, tags={"light"}),
    "leave_plate": Fix(id="leave_plate", label="a little plate", method="placing the shrimp on a little plate", calm_text="The shrimp treat rested still and neat, and that seemed to settle the ghost at once", fail_text="The plate helped a little, but the ghost was still fussy", power=3, sense=3, tags={"food", "shrimp"}),
    "call_name": Fix(id="call_name", label="a gentle greeting", method="calling the ghost by its old name", calm_text="The ghost blinked, remembered, and drifted closer with less fuss", fail_text="The name did not help, and the hoopla stayed loud", power=1, sense=1, tags={"ghost"}),
}

@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    parent_type: str = "mother"
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
    StoryParams(place="spa", problem="echo", fix="speak_softly", child_name="Mina", child_gender="girl", parent_type="mother"),
    StoryParams(place="bathhouse", problem="steam", fix="leave_plate", child_name="Owen", child_gender="boy", parent_type="father"),
    StoryParams(place="spa", problem="shrimp", fix="leave_plate", child_name="June", child_gender="girl", parent_type="mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for problem_id, problem in PROBLEMS.items():
            if not problem_at_risk(problem, place):
                continue
            for fix_id, fix in FIXES.items():
                if fix.sense >= SENSE_MIN and can_solve(fix, problem):
                    combos.append((pid, problem_id, fix_id))
    return combos


KNOWLEDGE = {
    "ghost": [("What is a ghost in a story?", "A ghost is a spooky character that can float, whisper, or rattle around in a pretend scary story.")],
    "spa": [("What is a spa?", "A spa is a quiet place where people go to relax in warm water, steam, and calm rooms.")],
    "shrimp": [("What is a shrimp?", "A shrimp is a small sea animal with a curled body. Some stories also use shrimp as food.")],
    "quiet": [("Why do quiet voices help in a spooky room?", "Quiet voices make less bouncing sound, so a room feels calmer and less startling.")],
    "light": [("Why can a lamp help in a spooky room?", "Light helps people see what is really there, which makes strange shadows less scary.")],
    "food": [("Why might leaving food alone help?", "Food on a plate stays neat and still, which can stop a messy mix-up or a noisy fuss.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child that includes the words "hoopla", "spa", and "shrimp".',
        f"Tell a gentle spooky story where {f['child'].id} solves a strange problem at the {f['place'].label} and then makes peace with the ghost.",
        f"Write a child-facing story with a mystery, a solution, and a reconciliation in a quiet spa setting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, ghost, place, problem, fix = f["child"], f["parent"], f["ghost"], f["place"], f["problem"], f["fix"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, {parent.label_word}, and a lonely ghost at the {place.label}. The story begins with a calm visit and turns spooky when the hoopla starts."),
        ("What started the hoopla?", f"The hoopla started around {problem.label}. The noise and the odd shrimp-shaped treat made the room feel strange enough for a ghostly fuss."),
        ("How did they solve the problem?", f"They used {fix.method} and paid attention to what the ghost seemed to need. That changed the room from noisy and spooky to calm and friendly."),
        ("How did the story end?", f"It ended with reconciliation. {ghost.label.capitalize()} was no longer upset, and everyone left the {place.label} in peace."),
    ]
    if world.facts["ghost"].memes["comfort"] >= THRESHOLD:
        qa.append(("Why did the ghost calm down?", f"The ghost calmed down because the children solved the problem instead of arguing with it. Once the room was quieter and the shrimp treat was handled kindly, the ghost felt heard."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["fix"].tags) | {"ghost", "spa", "shrimp"}
    out = []
    for key in ["ghost", "spa", "shrimp", "quiet", "light", "food"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
            bits.append(f"attrs={e.attrs}")
        if e.spooky:
            bits.append("spooky=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
spooky(g) :- ghost(g), trouble(g).
fearful(c) :- child(c), spooky(g), trouble(g).
understood(c) :- child(c), fix(F), sense(F,S), sense_min(M), S >= M.
reconciled(g,c) :- ghost(g), child(c), trouble(g), understood(c).
valid(P,Prob,Fix) :- place(P), problem(Prob), fix(Fix), noisy(Prob), spa_like(P), fix_sense(Fix,S), sense_min(M), S >= M.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.spa_like:
            lines.append(asp.fact("spa_like", pid))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if pr.noisy:
            lines.append(asp.fact("noisy", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_sense", fid, f.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke story generated.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world about a spa, hoopla, and shrimp.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def explain_rejection(place: Place, problem: Problem) -> str:
    if not problem_at_risk(problem, place):
        return f"(No story: the {place.label} is too ordinary for this problem to become spooky.)"
    return "(No story: no valid fix fits this problem.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Owen", "June", "Pia", "Noah", "Ivy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, problem=problem, fix=fix, child_name=name, child_gender=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell_story(PLACES[params.place], PROBLEMS[params.problem], FIXES[params.fix],
                       child_name=params.child_name, child_gender=params.child_gender,
                       parent_type=params.parent_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 and not args.all else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
