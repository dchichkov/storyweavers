#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/arithmetic_shed_ingenious_steep_hill_path_suspense.py
======================================================================================

A tiny comedy-suspense storyworld about a steep hill path, a shed, and a child
who uses arithmetic in an ingenious way to solve a problem without any frozen
template prose.

Seed premise:
- setting: steep hill path
- words: arithmetic, shed, ingenious
- style: comedy
- feature: suspense

The simulation is small but state-driven:
- typed entities with physical meters and emotional memes
- a forward causal step that can build suspense
- a decision beat that either averts trouble or resolves it with a clever fix
- prose that is assembled from world state, not from one static paragraph

Run:
    python storyworlds/worlds/gpt-5.4-mini/arithmetic_shed_ingenious_steep_hill_path_suspense.py
    python storyworlds/worlds/gpt-5.4-mini/arithmetic_shed_ingenious_steep_hill_path_suspense.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/arithmetic_shed_ingenious_steep_hill_path_suspense.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Terrain:
    id: str
    name: str
    steepness: int
    path_kind: str
    comedic_detail: str
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
class Shed:
    id: str
    label: str
    locked: bool
    clutter: int
    contains: list[str] = field(default_factory=list)
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
class Problem:
    id: str
    label: str
    severity: int
    suspense_line: str
    comedy_line: str
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
    power: int
    method_line: str
    ending_line: str
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
    terrain: str
    shed: str
    problem: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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
    apply: callable
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


def _r_suspense(world: World) -> list[str]:
    out = []
    child = world.get("child")
    path = world.get("path")
    problem = world.get("problem")
    if child.meters["trouble"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    path.meters["tense"] += 1
    out.append(f"The {problem.label} made the hill feel extra tricky.")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense)]


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
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for terrain in TERRAIN:
        for shed in SHEDS:
            for problem in PROBLEMS:
                for fix in FIXES:
                    if is_reasonable(TERRAIN[terrain], SHEDS[shed], PROBLEMS[problem], FIXES[fix]):
                        combos.append((terrain, shed, problem, fix))
    return combos


def is_reasonable(terrain: Terrain, shed: Shed, problem: Problem, fix: Fix) -> bool:
    return terrain.steepness >= 3 and shed.clutter >= 1 and problem.severity >= 1 and fix.power >= 1


def reasonableness_message(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: the chosen problem '{problem.label}' and fix '{fix.label}' do not "
        f"make a believable suspenseful comedy on the steep hill path.)"
    )


def setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper))
    path = world.add(Entity(id="path", type="terrain", label="steep hill path"))
    shed = world.add(Entity(id="shed", type="shed", label="shed"))
    problem = world.add(Entity(id="problem", type="problem", label=params.problem))
    world.facts.update(child=child, helper=helper, path=path, shed=shed, problem=problem)


def tell(world: World, terrain: Terrain, shed_cfg: Shed, problem: Problem, fix: Fix) -> None:
    child = world.get("child")
    helper = world.get("helper")
    path = world.get("path")
    shed = world.get("shed")
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1

    world.say(
        f"On a {terrain.name}, {child.id} and {helper.id} walked along the steep hill path, "
        f"where even the pebbles seemed to hold their breath. {terrain.comedic_detail}"
    )
    world.say(
        f"Near the {shed.label}, they found a tiny puzzle that felt a bit dramatic: {problem.suspense_line}"
    )
    world.para()
    child.meters["trouble"] += 1
    world.say(
        f"{child.id} peeked at the {shed.label}. \"I can fix this,\" {child.id} said, "
        f"and {child.pronoun().capitalize()} reached for {problem.label} with an ingenious grin."
    )
    world.say(f"Then came the suspense: {problem.comedy_line}")
    propagate(world, narrate=True)

    if problem.id == "stuck_door":
        child.memes["worry"] += 1
        world.say(
            f"{helper.id} glanced at the door, then at the hill, then at the shed, and whispered, "
            f'\"Let\'s use arithmetic before we use elbow grease.\"'
        )
    world.para()
    world.say(
        f"{helper.id} had a clever idea. {fix.method_line} "
        f"It was the kind of plan that sounded like nonsense until it worked."
    )

    if fix.id == "count_steps":
        child.meters["trouble"] = 0
        path.meters["ease"] += 1
        child.memes["joy"] += 1
        world.say(
            f"{child.id} counted the steps out loud: one, two, three, four. "
            f"Each number made the climb feel smaller, and the path stopped acting so suspicious."
        )
    elif fix.id == "divide_candies":
        shed.meters["calm"] += 1
        child.memes["joy"] += 1
        world.say(
            f"{child.id} divided the candy into equal piles, and suddenly everyone agreed the math was brilliant. "
            f"The shed no longer felt mysterious; it just felt helpful."
        )
    else:
        child.meters["trouble"] = 0
        child.memes["joy"] += 1
        world.say(
            f"{helper.id} solved it with a scribble, a grin, and a very serious face that made it even funnier."
        )

    world.para()
    world.say(
        f"At last, the {shed.label} stopped being a worry and became part of the joke. "
        f"{fix.ending_line}"
    )

    world.facts.update(
        terrain=terrain,
        shed_cfg=shed_cfg,
        problem_cfg=problem,
        fix_cfg=fix,
        outcome="resolved",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story that includes the words "arithmetic", "shed", and "ingenious" on a steep hill path.',
        f"Tell a suspenseful but funny story where {f['child'].id} faces {f['problem_cfg'].label} near a shed and solves it with arithmetic.",
        f"Write a child-friendly scene in which an ingenious idea turns a scary hill-path moment into a laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    problem = world.facts["problem_cfg"]
    fix = world.facts["fix_cfg"]
    return [
        QAItem(
            question="What made the story suspenseful?",
            answer=f"The suspense came from {problem.label} near the shed on the steep hill path. The problem felt tricky before the clever fix made everything safe again.",
        ),
        QAItem(
            question="How did arithmetic help?",
            answer=f"{helper.id} used arithmetic to guide the plan, and that kept the solution neat instead of chaotic. The numbers gave {child.id} something clear to do while the scene felt tense.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the shed turning from a worry into part of the joke, and the hill path feeling safe again. The ingenious idea worked, so the children could laugh on their way home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is arithmetic?",
            answer="Arithmetic is the part of math that uses counting, adding, subtracting, and similar number ideas. People use it to solve small everyday problems.",
        ),
        QAItem(
            question="What is a shed?",
            answer="A shed is a small building used for storing things like tools, buckets, or garden supplies. It is usually not the main house.",
        ),
        QAItem(
            question="What does ingenious mean?",
            answer="Ingenious means very clever and full of good ideas. An ingenious plan is smart in a way that surprises people.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:8} ({e.type:9}) meters={dict(meters)} memes={dict(memes)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TERRAIN:
        lines.append(asp.fact("terrain", tid))
        lines.append(asp.fact("steepness", tid, TERRAIN[tid].steepness))
    for sid in SHEDS:
        lines.append(asp.fact("shed", sid))
        lines.append(asp.fact("clutter", sid, SHEDS[sid].clutter))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, PROBLEMS[pid].severity))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, FIXES[fid].power))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(T,S,P,F) :- terrain(T), shed(S), problem(P), fix(F), steepness(T,St), clutter(S,C), severity(P,V), power(F,Pw), St >= 3, C >= 1, V >= 1, Pw >= 1.
#show reasonable/4.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        p = StoryParams(terrain="steep_hill", shed="old_shed", problem="stuck_door", fix="count_steps", child="Nia", child_gender="girl", helper="Milo", helper_gender="boy")
        s = generate(p)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(s, trace=True, qa=True)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


TERRAIN = {
    "steep_hill": Terrain(id="steep_hill", name="a steep hill path", steepness=5, path_kind="path", comedic_detail="A squirrel zipped uphill like it was late for a meeting."),
    "extra_steep_hill": Terrain(id="extra_steep_hill", name="an extra-steep hill path", steepness=6, path_kind="path", comedic_detail="A breeze tried to help and only succeeded in making everyone lean sideways."),
}

SHEDS = {
    "old_shed": Shed(id="old_shed", label="shed", locked=True, clutter=3, contains=["rakes", "buckets"], tags={"shed"}),
    "tiny_shed": Shed(id="tiny_shed", label="shed", locked=False, clutter=2, contains=["paint cans"], tags={"shed"}),
}

PROBLEMS = {
    "stuck_door": Problem(id="stuck_door", label="stuck door", severity=2, suspense_line="the little door gave a grumpy creak and refused to open", comedy_line="It wobbled like it was thinking very hard about staying shut.", tags={"suspense", "shed"}),
    "missing_key": Problem(id="missing_key", label="missing key", severity=2, suspense_line="the key was nowhere to be seen, which felt very dramatic", comedy_line="It was so missing that even the dust looked apologetic.", tags={"suspense", "shed"}),
}

FIXES = {
    "count_steps": Fix(id="count_steps", label="count steps", power=2, method_line="They counted the hill steps and matched each step to a number so nobody slipped into panic.", ending_line="The numbers worked like a little staircase for their brains.", tags={"arithmetic"}),
    "divide_candies": Fix(id="divide_candies", label="divide candies", power=2, method_line="They divided the snacks into equal piles and used the totals as a clue.", ending_line="Everyone agreed that math had rescued the mood.", tags={"arithmetic"}),
    "tally_stones": Fix(id="tally_stones", label="tally stones", power=2, method_line="They made tidy stone tallies on the path and compared the piles like detectives.", ending_line="The shed seemed less spooky once the tally stones got the last laugh.", tags={"arithmetic"}),
}


CURATED = [
    StoryParams(terrain="steep_hill", shed="old_shed", problem="stuck_door", fix="count_steps", child="Nia", child_gender="girl", helper="Milo", helper_gender="boy"),
    StoryParams(terrain="extra_steep_hill", shed="tiny_shed", problem="missing_key", fix="divide_candies", child="Pip", child_gender="boy", helper="June", helper_gender="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    terrain = args.terrain or rng.choice(list(TERRAIN))
    shed = args.shed or rng.choice(list(SHEDS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    fix = args.fix or rng.choice(list(FIXES))
    if terrain not in TERRAIN or shed not in SHEDS or problem not in PROBLEMS or fix not in FIXES:
        raise StoryError("invalid choice")
    if not is_reasonable(TERRAIN[terrain], SHEDS[shed], PROBLEMS[problem], FIXES[fix]):
        raise StoryError(reasonableness_message(PROBLEMS[problem], FIXES[fix]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or (rng.choice(["Nia", "Pip", "Ada", "Jo", "Max", "Tess"]) )
    helper = args.helper or (rng.choice(["Milo", "June", "Ollie", "Bea", "Finn", "Ivy"]) )
    return StoryParams(
        terrain=terrain, shed=shed, problem=problem, fix=fix,
        child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender
    )


def generate(params: StoryParams) -> StorySample:
    if params.terrain not in TERRAIN or params.shed not in SHEDS or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("invalid params")
    if not is_reasonable(TERRAIN[params.terrain], SHEDS[params.shed], PROBLEMS[params.problem], FIXES[params.fix]):
        raise StoryError(reasonableness_message(PROBLEMS[params.problem], FIXES[params.fix]))
    world = World()
    setup(world, params)
    tell(world, TERRAIN[params.terrain], SHEDS[params.shed], PROBLEMS[params.problem], FIXES[params.fix])
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy-suspense storyworld on a steep hill path.")
    ap.add_argument("--terrain", choices=TERRAIN)
    ap.add_argument("--shed", choices=SHEDS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
