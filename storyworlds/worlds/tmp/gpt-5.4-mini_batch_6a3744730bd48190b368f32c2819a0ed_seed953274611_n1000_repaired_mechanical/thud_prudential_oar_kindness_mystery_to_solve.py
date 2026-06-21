#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thud_prudential_oar_kindness_mystery_to_solve.py
================================================================================

A small mythic storyworld about a river-bridge, a puzzling thud, a prudent choice,
and kindness that resolves a conflict.

Seed inspiration:
- Words: thud, prudential, oar
- Features: Kindness, Mystery to Solve, Conflict
- Style: Myth

This world simulates a tiny mythical domain:
a village hears a strange thud from the riverbank, a prudent keeper worries
about safe choices, a broken oar becomes part of the mystery, and a kind act
reveals the answer. The stories are driven by world state, not a frozen text
template.
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
from typing import Optional

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
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class CharacterSpec:
    id: str
    type: str
    role: str
    label: str
    traits: list[str] = field(default_factory=list)
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
class ProblemSpec:
    id: str
    title: str
    omen: str
    thud_source: str
    mystery: str
    conflict: str
    kindness_route: str
    solution: str
    ending_image: str
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
class ObjectSpec:
    id: str
    label: str
    kind: str
    can_break: bool = False
    can_heal: bool = False
    can_row: bool = False
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
    problem: str
    keeper: str
    seeker: str
    helper: str
    broken_object: str
    kindness_route: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_ripple(world: World) -> list[str]:
    out: list[str] = []
    if world.get("river").meters["disturbance"] >= THRESHOLD and ("ripple",) not in world.fired:
        world.fired.add(("ripple",))
        world.get("river").meters["danger"] += 1
        world.get("seeker").memes["fear"] += 1
        out.append("")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.get("broken").meters["revealed"] >= THRESHOLD and ("reveal",) not in world.fired:
        world.fired.add(("reveal",))
        world.get("seeker").memes["wonder"] += 1
        out.append("")
    return out


CAUSAL_RULES = [_r_ripple, _r_reveal]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule(world):
                changed = True


def one_model_through(world: World) -> None:
    propagate(world)


def myth_name(kind: str) -> str:
    return {"river": "River", "keeper": "Keeper", "seeker": "Seeker", "helper": "Helper"}.get(kind, kind)


PROBLEMS = {
    "river-gate": ProblemSpec(
        id="river-gate",
        title="The River Gate and the Hidden Thud",
        omen="a thud from the rivergate",
        thud_source="the old river gate",
        mystery="who struck the gate in the dark",
        conflict="the keeper feared the river would swallow the village if the gate stayed shut",
        kindness_route="offer a lantern and speak gently to the frightened one",
        solution="the helper opened the latch and found a stranded child with a snapped oar",
        ending_image="the river gate stood open and the lantern's glow lay golden on the water",
        tags={"thud", "oar", "kindness", "mystery", "conflict"},
    ),
    "reed-bridge": ProblemSpec(
        id="reed-bridge",
        title="The Reed Bridge and the Prudential Warning",
        omen="a thud beneath the reed bridge",
        thud_source="the bridge's loose plank",
        mystery="what made the bridge groan so hard",
        conflict="the prudent keeper feared a crossing in the dark",
        kindness_route="wait together and share the oar as a pole",
        solution="the seeker found the loose plank and the helper steadied the crossing",
        ending_image="the reed bridge was calm, and the oar rested safely in kind hands",
        tags={"prudential", "oar", "kindness", "mystery", "conflict"},
    ),
}

CHARACTERS = {
    "keeper": CharacterSpec("keeper", "keeper", "keeper", "the prudent keeper", ["prudential", "careful"]),
    "seeker": CharacterSpec("seeker", "seer", "seeker", "the mystery seeker", ["curious", "brave"]),
    "helper": CharacterSpec("helper", "girl", "helper", "the kind helper", ["kind", "gentle"]),
}

OBJECTS = {
    "oar": ObjectSpec("oar", "oar", "tool", can_row=True, tags={"oar"}),
    "lantern": ObjectSpec("lantern", "lantern", "tool", can_heal=True, tags={"kindness"}),
    "gate": ObjectSpec("gate", "gate", "thing", can_break=True, tags={"thud"}),
    "bridge": ObjectSpec("bridge", "bridge", "thing", can_break=True, tags={"prudential"}),
}

KNOWLEDGE = {
    "oar": [("What is an oar?", "An oar is a long paddle used to row a boat on water.")],
    "kindness": [("What is kindness?", "Kindness is when someone helps gently and cares about another's trouble.")],
    "mystery": [("What is a mystery?", "A mystery is a puzzle where the answer is not known at first.")],
    "prudential": [("What does prudential mean?", "Prudential means careful and wise about what could go wrong.")],
    "thud": [("What is a thud?", "A thud is a heavy sound, like something hitting wood or earth.")],
    "conflict": [("What is conflict?", "Conflict is when two ideas or wishes are in tension and must be resolved.")],
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in PROBLEMS:
        for kid in CHARACTERS:
            for obj in OBJECTS:
                if obj == "oar":
                    out.append((pid, kid, obj))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic tiny storyworld of thuds, prudence, oars, and kindness.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--keeper", choices=CHARACTERS)
    ap.add_argument("--seeker", choices=CHARACTERS)
    ap.add_argument("--helper", choices=CHARACTERS)
    ap.add_argument("--broken-object", choices=OBJECTS, dest="broken_object")
    ap.add_argument("--kindness-route", choices=["lantern", "wait"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    pid = args.problem or rng.choice(list(PROBLEMS))
    keeper = args.keeper or "keeper"
    seeker = args.seeker or "seeker"
    helper = args.helper or "helper"
    broken = args.broken_object or "oar"
    route = args.kindness_route or rng.choice(["lantern", "wait"])
    return StoryParams(problem=pid, keeper=keeper, seeker=seeker, helper=helper, broken_object=broken, kindness_route=route)


def tell(params: StoryParams) -> World:
    if params.broken_object not in OBJECTS:
        raise StoryError("Unknown object.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")

    world = World()
    problem = PROBLEMS[params.problem]
    keeper = world.add(Entity(id="keeper", kind="character", type="man", role="keeper", label=CHARACTERS[params.keeper].label, traits=CHARACTERS[params.keeper].traits))
    seeker = world.add(Entity(id="seeker", kind="character", type="boy", role="seeker", label=CHARACTERS[params.seeker].label, traits=CHARACTERS[params.seeker].traits))
    helper = world.add(Entity(id="helper", kind="character", type="girl", role="helper", label=CHARACTERS[params.helper].label, traits=CHARACTERS[params.helper].traits))
    broken = world.add(Entity(id="broken", kind="thing", type="tool", label=OBJECTS[params.broken_object].label))
    river = world.add(Entity(id="river", kind="thing", type="river", label="the river"))
    gate = world.add(Entity(id="gate", kind="thing", type="thing", label="the gate"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="tool", label="the lantern"))

    world.facts["problem"] = problem
    world.facts["keeper"] = keeper
    world.facts["seeker"] = seeker
    world.facts["helper"] = helper
    world.facts["broken"] = broken
    world.facts["route"] = params.kindness_route
    world.facts["oar"] = broken
    world.facts["river"] = river

    keeper.memes["prudence"] = 1.0
    seeker.memes["curiosity"] = 1.0
    helper.memes["kindness"] = 1.0

    world.say(f"In a mythic season, {keeper.label} watched over {problem.title.lower()}.")
    world.say(f"Then came {problem.omen}, and everyone listened to the strange sound.")

    world.para()
    keeper.memes["conflict"] += 1
    seeker.memes["mystery"] += 1
    world.say(f"{keeper.label_word.capitalize()} felt the conflict at once: {problem.conflict}.")
    world.say(f"{seeker.label_word.capitalize()} wanted to solve the mystery: {problem.mystery}.")

    world.para()
    if params.kindness_route == "lantern":
        helper.meters["light"] += 1
        lantern.meters["glow"] += 1
        world.say(f"{helper.label_word.capitalize()} lifted {lantern.label} and spoke kindly: \"Let us be wise together.\"")
        world.say(f"That kindness steadied the others, and the prudent keeper agreed to look more closely.")
    else:
        broken.meters["revealed"] += 1
        world.say(f"{helper.label_word.capitalize()} asked for patience, and they waited by the water.")
        world.say("The waiting was kind, and it let the mystery rise to the surface like moonlight.")

    world.para()
    broken.meters["thud"] += 1
    river.meters["disturbance"] += 1
    gate.meters["seen"] += 1
    one_model_through(world)
    world.say(f"At last they found the answer: {problem.solution}.")
    world.say(f"The old {broken.label} lay near the bank, and the thud had been its cry in the dark.")

    world.para()
    keeper.memes["relief"] += 1
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"So the conflict ended without anger.")
    world.say(f"By dawn, {problem.ending_image}.")

    world.facts["ending"] = "resolved"
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    return [
        f"Write a myth about {p.title.lower()} that includes the words thud, prudential, and oar.",
        f"Tell a small myth where a prudent keeper faces a conflict, a mystery is solved, and kindness matters.",
        f"Write a child-friendly mythic story with a hidden answer, a gentle helper, and an oar near the river.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["problem"]
    helper = world.facts["helper"]
    keeper = world.facts["keeper"]
    seeker = world.facts["seeker"]
    broken = world.facts["broken"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was {p.mystery}. They listened for the thud, looked to the riverbank, and found a real clue instead of guessing."
        ),
        QAItem(
            question="How did kindness help?",
            answer=f"{helper.label_word.capitalize()} spoke gently and helped the others stay calm. That kindness made it easier for {keeper.label_word} and {seeker.label_word} to solve the problem together."
        ),
        QAItem(
            question="What object mattered most?",
            answer=f"The {broken.label} mattered most because it was part of the clue. The broken oar explained the thud and pointed them toward the answer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags) | {"thud", "oar", "kindness", "mystery", "conflict"}
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
thud_source(river_gate).
problem(river_gate).
problem(reed_bridge).
kindness_route(lantern).
kindness_route(wait).
valid(P, K, H, O, R) :- problem(P), keeper(K), helper(H), oar(O), route(R).
ending(resolved) :- valid(_,_,_,_,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for cid in CHARACTERS:
        lines.append(asp.fact("keeper", cid))
        lines.append(asp.fact("helper", cid))
    for oid in OBJECTS:
        lines.append(asp.fact("oar", oid) if oid == "oar" else asp.fact("object", oid))
    for r in ["lantern", "wait"]:
        lines.append(asp.fact("route", r))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    try:
        import asp
        clingo_set = set(asp_valid_combos())
        python_set = set(valid_combos())
        if clingo_set == python_set:
            print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
        else:
            rc = 1
            print("MISMATCH in ASP gate:")
            if clingo_set - python_set:
                print("  only in clingo:", sorted(clingo_set - python_set))
            if python_set - clingo_set:
                print("  only in python:", sorted(python_set - clingo_set))
    except Exception as err:
        print(f"ASP ERROR: {err}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PROBLEMS:
        for k in CHARACTERS:
            for o in OBJECTS:
                combos.append((p, k, o))
    return combos


CURATED = [
    StoryParams(problem="river-gate", keeper="keeper", seeker="seeker", helper="helper", broken_object="oar", kindness_route="lantern"),
    StoryParams(problem="reed-bridge", keeper="keeper", seeker="seeker", helper="helper", broken_object="oar", kindness_route="wait"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
