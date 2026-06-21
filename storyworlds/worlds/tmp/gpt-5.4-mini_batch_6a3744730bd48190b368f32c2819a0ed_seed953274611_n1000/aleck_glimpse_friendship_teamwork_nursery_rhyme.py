#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aleck_glimpse_friendship_teamwork_nursery_rhyme.py
===================================================================================

A tiny nursery-rhyme storyworld about Aleck and Glimpse: two friends who try to
carry out a small chore together, get tangled up by a simple mistake, and then
solve it with teamwork. The world keeps the story child-facing, concrete, and
state-driven.

Seed words:
- aleck
- glimpse

Features:
- Friendship
- Teamwork

Style:
- Nursery rhyme
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: {"weight": 0.0, "tied": 0.0, "placed": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "pride": 0.0, "teamwork": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    prop: str
    task: str
    ending: str


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    use: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    risk: str
    fixed_by: str
    size: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    helper1: str
    helper2: str
    problem: str
    child1: str
    child1_type: str
    child2: str
    child2_type: str
    parent: str
    seed: Optional[int] = None


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


def _r_risk(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.role != "problem" or e.meters["placed"] < THRESHOLD:
            continue
        sig = ("risk", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["worry"] += 1
        world.get("room").meters["tension"] += 1
        out.append("__risk__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    a = world.get("Aleck")
    b = world.get("Glimpse")
    if a.meters["placed"] >= THRESHOLD and b.meters["placed"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["teamwork"] += 1
            b.memes["teamwork"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("risk", _r_risk), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid in HELPERS:
            for pid in PROBLEMS:
                if HELPERS[hid].safe and PROBLEMS[pid].size <= 2:
                    combos.append((sid, hid, pid))
    return combos


def explain_rejection(problem: Problem, helper: Helper) -> str:
    if not helper.safe:
        return f"(No story: {helper.label} is too unsafe for a nursery-rhyme story.)"
    if problem.size > 2:
        return f"(No story: {problem.label} is too large for a tiny teamwork tale.)"
    return "(No story: this combination does not fit the storyworld's simple premise.)"


def rhyme_opening(a: Entity, b: Entity, setting: Setting) -> str:
    return (
        f"Old Aleck and Glimpse went out one day, to {setting.place} where small chores play. "
        f"{setting.prop.capitalize()} waited there, neat as can be, and they both smiled bright as bright could be."
    )


def setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(rhyme_opening(a, b, setting))
    world.say(f"They sang a little song while they went along, as friendly as friends could be.")


def trouble(world: World, problem: Problem, setting: Setting) -> None:
    world.para()
    p = world.get(problem.id)
    p.meters["placed"] += 1
    world.say(
        f"But there by {setting.place}, {problem.label} gave a sigh; "
        f"it wobbled and wanted to tip right by."
    )
    propagate(world, narrate=False)
    world.say(
        f"A tiny glimpse of a mess peeked out, and Aleck said, "
        f'"Oh no, oh no, this will surely flout our show!"'
    )


def teamwork_fix(world: World, a: Entity, b: Entity, problem: Problem, setting: Setting) -> None:
    world.para()
    a.meters["placed"] += 1
    b.meters["placed"] += 1
    propagate(world, narrate=False)
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    world.say(
        f"Then Aleck held one side, Glimpse held the other, and together they "
        f"mended it like sister and brother."
    )
    world.say(
        f"They tucked {problem.label} in place with a careful little grace, and "
        f"{setting.task} was done in a cozy, happy space."
    )


def ending(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.para()
    world.say(
        f"At last they laughed, side by side; {setting.ending}, and friendship "
        f"stayed as bright as a guide."
    )
    world.say("For Aleck and Glimpse knew, plain and true, that teamwork makes small jobs shine through.")


HELPERS = {
    "rope": Helper("rope", "a soft rope", "tool", "tie things gently", safe=True, tags={"rope", "teamwork"}),
    "basket": Helper("basket", "a little basket", "tool", "carry things together", safe=True, tags={"basket", "teamwork"}),
    "gloves": Helper("gloves", "two cloth gloves", "gear", "hold things snugly", safe=True, tags={"gloves", "teamwork"}),
}

PROBLEMS = {
    "ball": Problem("ball", "a rolling ball", "small obstacle", "be held and lifted together", size=1, tags={"ball"}),
    "kite": Problem("kite", "a tangled kite string", "small obstacle", "be untangled together", size=2, tags={"kite"}),
    "box": Problem("box", "a tilted box of toys", "small obstacle", "be set upright together", size=2, tags={"box"}),
}

SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "a toy shelf", "sort the toys", "the room felt warm and tidy"),
    "yard": Setting("yard", "the yard", "a little wheelbarrow", "stack the blocks", "the garden looked neat and sweet"),
    "porch": Setting("porch", "the porch", "a teacup tray", "carry the cups", "the porch was calm as a lullaby"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme friendship teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--helper1", choices=HELPERS)
    ap.add_argument("--helper2", choices=HELPERS)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, helper1, problem = rng.choice(sorted(combos))
    helper2 = args.helper2 or rng.choice([k for k in HELPERS if k != helper1])
    if args.helper1:
        helper1 = args.helper1
    if args.helper2:
        helper2 = args.helper2
    if args.problem and PROBLEMS[args.problem].size > 2:
        raise StoryError(explain_rejection(PROBLEMS[args.problem], HELPERS[helper1]))
    if helper1 == helper2:
        helper2 = rng.choice([k for k in HELPERS if k != helper1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        helper1=helper1,
        helper2=helper2,
        problem=problem,
        child1="Aleck",
        child1_type="boy",
        child2="Glimpse",
        child2_type="girl",
        parent=parent,
    )


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id="Aleck", kind="character", type=params.child1_type, role="child"))
    g = world.add(Entity(id="Glimpse", kind="character", type=params.child2_type, role="child"))
    world.add(Entity(id="room", kind="thing", type="room", role="room", meters={"tension": 0.0}))
    world.add(Entity(id="problem", kind="thing", type="problem", role="problem", label=PROBLEMS[params.problem].label))

    setup(world, a, g, SETTINGS[params.setting])
    trouble(world, PROBLEMS[params.problem], SETTINGS[params.setting])
    teamwork_fix(world, a, g, PROBLEMS[params.problem], SETTINGS[params.setting])
    ending(world, a, g, SETTINGS[params.setting])

    world.facts.update(
        a=a, g=g, setting=SETTINGS[params.setting], problem=PROBLEMS[params.problem],
        helper1=HELPERS[params.helper1], helper2=HELPERS[params.helper2],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a nursery-rhyme story about Aleck and Glimpse that shows friendship and teamwork.',
        f"Tell a short rhyme where Aleck and Glimpse work together to solve {f['problem'].label}.",
        f'Write a child-friendly story that includes the words "aleck" and "glimpse" and ends happily.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["a"]
    g = f["g"]
    problem = f["problem"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         "It is about Aleck and Glimpse, two friends who work side by side."),
        ("What problem did they face?",
         f"They had to handle {problem.label} at {setting.place}. It started to wobble, so they needed teamwork."),
        ("How did they solve it?",
         f"Aleck held one side and Glimpse held the other, so they fixed {problem.label} together."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork means people help each other and do a job together."),
        QAItem("What is friendship?", "Friendship means being kind, sharing, and looking out for one another."),
        QAItem("Why is it nice to work together?", "Working together can make a job easier, safer, and more fun."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    for key in (params.setting, params.helper1, params.helper2, params.problem):
        if key not in SETTINGS and key not in HELPERS and key not in PROBLEMS:
            raise StoryError(f"invalid story parameter: {key}")
    if params.setting not in SETTINGS or params.problem not in PROBLEMS:
        raise StoryError("(Invalid parameters.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S,H1,H2,P) :- setting(S), helper(H1), helper(H2), problem(P), H1 != H2.
story(S,H1,H2,P) :- valid(S,H1,H2,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if h.safe:
            lines.append(asp.fact("safe_helper", hid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("size", pid, p.size))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except Exception as exc:  # pragma: no cover
        print(f"SKIP: clingo unavailable: {exc}")
        return 0
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="nursery", helper1="rope", helper2="basket", problem="ball",
                child1="Aleck", child1_type="boy", child2="Glimpse", child2_type="girl",
                parent="mother"),
    StoryParams(setting="yard", helper1="gloves", helper2="rope", problem="kite",
                child1="Aleck", child1_type="boy", child2="Glimpse", child2_type="girl",
                parent="father"),
    StoryParams(setting="porch", helper1="basket", helper2="gloves", problem="box",
                child1="Aleck", child1_type="boy", child2="Glimpse", child2_type="girl",
                parent="mother"),
]


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
