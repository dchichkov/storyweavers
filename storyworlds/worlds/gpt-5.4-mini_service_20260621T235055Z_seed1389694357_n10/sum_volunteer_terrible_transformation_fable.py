#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T235055Z_seed1389694357_n10/sum_volunteer_terrible_transformation_fable.py
===============================================================================================================

A standalone storyworld for a tiny fable-like domain: a sum is mishandled,
a volunteer steps in, and a terrible mess leads to a transformation. The world
keeps physical meters and emotional memes, uses a forward causal model, and
renders a child-facing story with a clear beginning, turn, and ending image.

The seed prompt asked for these words and instruments:
- sum
- volunteer
- terrible
- Transformation
- Style: Fable
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
from pathlib import Path
from typing import Callable, Optional


def _bootstrap_results() -> None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "results.py").exists():
            sys.path.insert(0, str(parent))
            return
        if (parent / "storyworlds" / "results.py").exists():
            sys.path.insert(0, str(parent / "storyworlds"))
            return


_bootstrap_results()
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
ASP_RULES = r"""
need_help(P) :- puzzle(P), pieces(P, N), sum_goal(P, G), N < G.
terrible_mess(M) :- mess(M), dirt(M, D), D >= 2.
transforms(P, T) :- need_help(P), volunteer(V), helps(V, P), change_to(P, T), not blocked(P).
outcome("fixed") :- transforms(P, T), not terrible_mess(M).
outcome("changed") :- terrible_mess(M), transforms(P, T).
outcome("stuck") :- need_help(P), not transforms(P, _).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "she"}
        male = {"boy", "father", "man", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    light: str


@dataclass
class Puzzle:
    id: str
    label: str
    pieces: int
    sum_goal: int
    action: str
    result_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Work:
    id: str
    label: str
    label_after: str
    transform_word: str
    transforms_to: str
    required_help: int
    mess_name: str
    mess_severity: int
    blocked_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    help_line: str
    tool: str
    kindness: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    puzzle: str
    work: str
    helper: str
    seed: Optional[int] = None


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_doubt(world: World) -> list[str]:
    out = []
    p = world.get("puzzle")
    if p.meters["shortage"] >= THRESHOLD and ("doubt", p.id) not in world.fired:
        world.fired.add(("doubt", p.id))
        p.memes["worry"] += 1
        out.append("")
    return out


def _r_mess(world: World) -> list[str]:
    out = []
    w = world.get("work")
    if w.meters["scramble"] < THRESHOLD:
        return out
    if ("mess", w.id) in world.fired:
        return out
    world.fired.add(("mess", w.id))
    w.meters["terrible"] += 1
    world.get("room").meters["mess"] += w.mess_severity
    out.append("__terrible__")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    p = world.get("puzzle")
    w = world.get("work")
    h = world.get("helper")
    if p.meters["fixed"] >= THRESHOLD:
        return out
    if p.meters["shortage"] < THRESHOLD:
        return out
    if h.meters["help"] < THRESHOLD:
        return out
    if w.meters["blocked"] >= THRESHOLD:
        return out
    if ("transform", p.id) in world.fired:
        return out
    if h.attrs.get("power", 0) < w.attrs.get("required_help", 1):
        return out
    world.fired.add(("transform", p.id))
    p.meters["fixed"] += 1
    p.meters["changed"] += 1
    p.meters["glow"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("doubt", _r_doubt), Rule("mess", _r_mess), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "classroom": Setting("classroom", "a sunny classroom", "quiet chalk dust", "bright window light"),
    "kitchen": Setting("kitchen", "a warm kitchen", "soft crumbs", "golden lamplight"),
    "barn": Setting("barn", "an old barn", "hay and straw", "slanted afternoon light"),
}

PUZZLES = {
    "sum": Puzzle("sum", "a sum of numbers", 2, 4, "count the blocks together", "counted sum", {"sum", "numbers"}),
    "beads": Puzzle("beads", "a bead pattern", 3, 5, "line up the beads", "bead line", {"sum", "pattern"}),
    "coins": Puzzle("coins", "a pile of coins", 1, 3, "add the coins up", "coin stack", {"sum", "coins"}),
}

WORKS = {
    "mud": Work("mud", "mud on the floor", "clean floor", "smooth it into a clean patch", "made clean", 2, "mud", 2, tags={"terrible", "mud"}),
    "spilled_ink": Work("spilled_ink", "spilled ink", "neat page", "blot it dry", "blotted clean", 2, "ink", 3, tags={"terrible", "ink"}),
    "tangled_wool": Work("tangled_wool", "tangled wool", "neat skein", "comb it smooth", "smoothed wool", 1, "tangle", 2, tags={"terrible", "wool"}),
}

HELPERS = {
    "volunteer": Helper("volunteer", "a volunteer", "I can help.", "hands", "kind", 3, {"volunteer"}),
    "mouse": Helper("mouse", "a mouse helper", "I will help too.", "tiny paws", "gentle", 2, {"volunteer"}),
    "grandparent": Helper("grandparent", "a grandparent", "Let me lend a hand.", "basket", "patient", 4, {"volunteer"}),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PUZZLES.values():
            for w in WORKS.values():
                if p.sum_goal >= 3 and w.mess_severity >= 2:
                    for h in HELPERS:
                        out.append((s, p.id, w.id, h))
    return out


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen parts do not make a good fable-like change.)"


def _choose_name(rng: random.Random) -> str:
    return rng.choice(["Mina", "Toby", "Lena", "Owen", "Pia", "Arlo"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.puzzle is None or c[1] == args.puzzle)
              and (args.work is None or c[2] == args.work)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, puzzle, work, helper = rng.choice(sorted(combos))
    return StoryParams(setting=setting, puzzle=puzzle, work=work, helper=helper)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    puzzle = PUZZLES[params.puzzle]
    work = WORKS[params.work]
    helper = HELPERS[params.helper]
    child = world.add(Entity(id=_choose_name(random.Random(params.seed or 0)), kind="character", type="girl", label="child", role="learner"))
    assistant = world.add(Entity(id=helper.label, kind="character", type="thing", label=helper.label, role="helper", tags=set(helper.tags), attrs={"power": helper.power}))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    p = world.add(Entity(id="puzzle", kind="thing", type="puzzle", label=puzzle.label, attrs={"goal": puzzle.sum_goal}, meters=defaultdict(float)))
    p.meters["shortage"] = max(0.0, puzzle.sum_goal - puzzle.pieces)
    w = world.add(Entity(id="work", kind="thing", type="work", label=work.label, attrs={"required_help": work.required_help}, meters=defaultdict(float)))
    w.meters["scramble"] = 1.0
    h = world.add(Entity(id="helper", kind="character", type="thing", label=helper.label, attrs={"power": helper.power}, meters=defaultdict(float)))
    h.meters["help"] = 1.0

    world.say(f"In {setting.place}, a child faced a {puzzle.label_word if hasattr(puzzle, 'label_word') else puzzle.label}.")
    world.say(f"The sum looked simple, but it became hard when {work.label} made the day feel terrible.")
    world.para()
    world.say(f"Then {helper.label} stepped forward and said, \"{helper.help_line}\"")
    propagate(world, narrate=False)
    if p.meters["fixed"] >= THRESHOLD:
        world.say(f"Together they changed the problem into {puzzle.result_name}, and the terrible mess became calm.")
        world.say(f"By the end, the room was {work.label_after}, and the sum was solved with a smile.")
    else:
        world.say(f"The help was not enough, so the fable ended with the trouble still waiting.")
    world.facts.update(setting=setting, puzzle=puzzle, work=work, helper=helper, outcome="fixed" if p.meters["fixed"] >= THRESHOLD else "stuck")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable with the words "sum", "volunteer", and "terrible" in which a helper changes a problem at the {f["setting"].place}.',
        f"Tell a short moral story where a volunteer helps with a sum and turns a terrible mess into something better.",
        f"Write a child-friendly fable about a sum that needs help, a volunteer who steps in, and a transformation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p, w, h = f["puzzle"], f["work"], f["helper"]
    return [
        QAItem(
            question="What was the main problem in the story?",
            answer=f"It was a sum that needed help, and the work made things feel terrible. The trouble was shown in the {w.label} and in how hard the sum felt to finish.",
        ),
        QAItem(
            question="Who volunteered to help?",
            answer=f"{h.label} volunteered and offered help. That choice mattered because the helper had enough power to guide the change.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The terrible mess changed into a calmer place, and the sum was solved. The story ends with a transformation, not with the trouble still hanging around.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "sum": [QAItem(question="What is a sum?", answer="A sum is what you get when you add numbers together.")],
    "volunteer": [QAItem(question="What does it mean to volunteer?", answer="To volunteer means to offer help by choice.")],
    "terrible": [QAItem(question="What does terrible mean?", answer="Terrible means very bad or upsetting.")],
    "transformation": [QAItem(question="What is a transformation?", answer="A transformation is a big change from one form or state to another.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ("sum", "volunteer", "terrible", "transformation") for q in WORLD_KNOWLEDGE[key]]


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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("puzzle", pid) for pid in PUZZLES]
    lines += [asp.fact("sum_goal", pid, p.sum_goal) for pid, p in PUZZLES.items()]
    lines += [asp.fact("pieces", pid, p.pieces) for pid, p in PUZZLES.items()]
    lines += [asp.fact("mess", wid) for wid in WORKS]
    lines += [asp.fact("dirt", wid, w.mess_severity) for wid, w in WORKS.items()]
    lines += [asp.fact("volunteer", hid) for hid in HELPERS]
    lines += [asp.fact("helps", hid, pid) for hid in HELPERS for pid in PUZZLES]
    lines += [asp.fact("change_to", pid, WORKS[next(iter(WORKS))].label_after) for pid in PUZZLES]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    asp_outcome = asp.atoms(model, "outcome")
    sample = generate(StoryParams(setting="classroom", puzzle="sum", work="mud", helper="volunteer"))
    py_ok = sample.world.facts["outcome"]
    if (asp_outcome and asp_outcome[0][0] == "fixed") and py_ok == "fixed":
        print("OK: ASP and Python both report a transformed ending.")
    else:
        print("MISMATCH between ASP and Python outcome.")
        return 1
    try:
        _ = generate(resolve_params(argparse.Namespace(setting=None, puzzle=None, work=None, helper=None), random.Random(7)))
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about sum, volunteer, terrible, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--work", choices=WORKS)
    ap.add_argument("--helper", choices=HELPERS)
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
        print("=== trace ===")
        for e in sample.world.entities.values():
            print(e.id, dict(e.meters), dict(e.memes), e.attrs)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show outcome/1."))
        print("outcomes:", asp.atoms(model, "outcome"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="classroom", puzzle="sum", work="mud", helper="volunteer"),
            StoryParams(setting="kitchen", puzzle="coins", work="spilled_ink", helper="grandparent"),
            StoryParams(setting="barn", puzzle="beads", work="tangled_wool", helper="mouse"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
