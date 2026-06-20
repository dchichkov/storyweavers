#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rag_dialogue_sharing_problem_solving_fable.py
=============================================================================

A standalone storyworld for a small fable-like tale about two animal friends,
one rag, a shared problem, and a kind solution.

Seed premise
------------
A little fable where a small rag becomes useful only after the characters talk,
share, and solve a problem together.

This world models:
- typed entities with physical meters and emotional memes
- a forward causal turn driven by a problem
- dialogue as part of the story beat, not as decoration
- sharing as the moral hinge
- a concrete ending image proving the problem was solved

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/rag_dialogue_sharing_problem_solving_fable.py
    python storyworlds/worlds/gpt-5.4-mini/rag_dialogue_sharing_problem_solving_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/rag_dialogue_sharing_problem_solving_fable.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/rag_dialogue_sharing_problem_solving_fable.py --trace
    python storyworlds/worlds/gpt-5.4-mini/rag_dialogue_sharing_problem_solving_fable.py --json
    python storyworlds/worlds/gpt-5.4-mini/rag_dialogue_sharing_problem_solving_fable.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sheep", "goat", "cow", "hen"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"rabbit"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Asset:
    id: str
    label: str
    phrase: str
    purpose: str
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
    need: str
    caused_by: str
    fix_hint: str
    severity: int = 1
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
    action: str
    requires_share: bool
    power: int
    outcome: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_need(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["problem"] < THRESHOLD:
            continue
        sig = ("need", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["worry"] += 1
        out.append("__problem__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.memes["share"] < THRESHOLD:
            continue
        sig = ("share", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["hope"] += 1
        out.append("__share__")
    return out


CAUSAL_RULES = [Rule("need", _r_need), Rule("share", _r_share)]


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


def predict_fix(world: World, fixer_id: str, asset_id: str, problem_id: str, fix_id: str) -> dict:
    sim = world.copy()
    do_fix(sim, sim.get(fixer_id), ASSETS[asset_id], PROBLEMS[problem_id], FIXES[fix_id], narrate=False)
    return {
        "solved": sim.facts.get("solved", False),
        "shared": sim.facts.get("shared", False),
    }


def do_problem(world: World, problem: Problem) -> None:
    world.get("problem").meters["problem"] += problem.severity
    world.say(
        f"One morning, the little fable garden grew troubled because {problem.need}."
    )
    world.say(
        f'"{problem.label}," said the first friend, "this will not do."'
    )


def ask_share(world: World, a: Entity, b: Entity, asset: Asset, problem: Problem) -> None:
    a.memes["wanting"] += 1
    world.say(
        f'"We have {asset.phrase}," said {a.id}. "Can we use it to help?" '
        f'"We can," said {b.id}, "if we share it fairly."'
    )


def share_asset(world: World, a: Entity, b: Entity, asset: Asset) -> None:
    a.memes["share"] += 1
    b.memes["share"] += 1
    world.facts["shared"] = True
    world.say(f"They laid the {asset.label} between them and each took one end.")


def do_fix(world: World, fixer: Entity, asset: Asset, problem: Problem, fix: Fix,
           narrate: bool = True) -> None:
    if fix.requires_share and not world.facts.get("shared"):
        return
    if narrate:
        world.say(
            f'"Then let us {fix.action}," said {fixer.id}, and both friends nodded.'
        )
    fixer.memes["calm"] += 1
    world.get("problem").meters["problem"] = max(0.0, world.get("problem").meters["problem"] - fix.power)
    world.facts["solved"] = world.get("problem").meters["problem"] < THRESHOLD
    if narrate and world.facts["solved"]:
        world.say(
            f"The {problem.label} was solved at last, and the {asset.label} was no longer just old cloth."
        )


def ending(world: World, a: Entity, b: Entity, asset: Asset, problem: Problem) -> None:
    if world.facts.get("solved"):
        world.say(
            f"By sunset, the {asset.label} had become a useful helper, and the two friends smiled at their neat little fix."
        )
        world.say(
            "The fable ended the way good sharing does: with less fuss, more peace, and two friends working as one."
        )
    else:
        world.say(
            f"By sunset, the {problem.label} still stood in the way, and the {asset.label} remained only a hopeful idea."
        )


def tell(a_name: str, b_name: str, asset: Asset, problem: Problem, fix: Fix) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type="rabbit", role="helper", traits=["kind"]))
    b = world.add(Entity(id=b_name, kind="character", type="sheep", role="helper", traits=["wise"]))
    world.add(Entity(id="problem", kind="thing", type="problem", label=problem.label))
    world.facts["asset"] = asset
    world.facts["problem_cfg"] = problem
    world.facts["fix"] = fix

    world.say(
        f"{a.id} and {b.id} lived by a small green fence where every day brought a small lesson."
    )
    world.say(
        f"They had {asset.phrase}, a little {asset.label} that could help when things got stuck."
    )
    world.para()
    do_problem(world, problem)
    ask_share(world, a, b, asset, problem)
    share_asset(world, a, b, asset)
    do_fix(world, a, asset, problem, fix)
    world.para()
    ending(world, a, b, asset, problem)

    world.facts.update(
        a=a,
        b=b,
        outcome="solved" if world.facts.get("solved") else "unsolved",
    )
    return world


ASSETS = {
    "rag": Asset("rag", "rag", "a soft rag", "wipe away mud", {"rag", "cloth", "sharing"}),
    "cloth": Asset("cloth", "cloth", "a clean cloth", "wipe a spill", {"cloth"}),
    "towel": Asset("towel", "towel", "a little towel", "dry paws", {"towel"}),
}

PROBLEMS = {
    "muddy_gate": Problem("muddy_gate", "muddy gate", "the gate was stuck with mud", "rain", "wipe the mud away", 1, {"mud", "gate"}),
    "sticky_paw": Problem("sticky_paw", "sticky paw", "a paw was muddy and would not open the latch", "mud", "wipe the paw clean", 1, {"mud"}),
}

FIXES = {
    "share_and_wipe": Fix("share_and_wipe", "share and wipe", "share the rag and wipe the mud away", True, 2, "cleaned the latch", {"share", "rag"}),
    "wipe_alone": Fix("wipe_alone", "wipe alone", "wipe it alone", False, 1, "tried to fix it by one friend", {"rag"}),
}

NAMES_A = ["Pip", "Milo", "Tia", "Nia", "Luna", "Bram"]
NAMES_B = ["Rue", "Bea", "Ollie", "Poppy", "Sage", "Ned"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for a in ASSETS:
        for p in PROBLEMS:
            for f in FIXES:
                if a == "rag" and f == "share_and_wipe" and p in PROBLEMS:
                    out.append((a, p, f))
    return out


@dataclass
@dataclass
class StoryParams:
    asset: str
    problem: str
    fix: str
    a_name: str
    b_name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    asset, problem, fix = f["asset"], f["problem_cfg"], f["fix"]
    return [
        f'Write a short fable about two friends who share a {asset.label} to solve {problem.label}.',
        f"Tell a dialogue-driven story where {f['a'].id} and {f['b'].id} talk kindly, share a {asset.label}, and fix a problem together.",
        f'Write a child-friendly fable about sharing and problem solving that includes the word "rag".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, asset, problem, fix = f["a"], f["b"], f["asset"], f["problem_cfg"], f["fix"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two small friends who live by a fence and try to help each other.",
        ),
        QAItem(
            question="What problem did they face?",
            answer=f"They faced {problem.label}. The {problem.label} made it hard to keep going until they found a way to solve it.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They shared the {asset.label} and used it together. That gave them enough help to finish the fix and make the problem go away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rag?",
            answer="A rag is a soft piece of cloth used for wiping or cleaning small messes.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps because two friends can use the same thing together and solve a problem more easily.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="It means finding a good way to make the trouble stop or to make the task possible again.",
        ),
    ]


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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rag", "muddy_gate", "share_and_wipe", "Pip", "Rue"),
    StoryParams("rag", "sticky_paw", "share_and_wipe", "Milo", "Bea"),
]


def explain_rejection(asset: Asset, problem: Problem, fix: Fix) -> str:
    if fix.requires_share and asset.id != "rag":
        return "(No story: this fable needs the rag to matter, and a shared rag-based fix is the heart of the tale.)"
    return "(No story: the chosen pieces do not make a clear sharing-and-problem-solving fable.)"


def valid_story(params: StoryParams) -> bool:
    return params.asset == "rag" and params.fix == "share_and_wipe" and params.problem in PROBLEMS


ASP_RULES = r"""
valid(A, P, F) :- asset(A), problem(P), fix(F), share_fix(F), rag_asset(A).
solved :- valid(A, P, F), asset(A), problem(P), fix(F), power(F, Pow), Pow >= 2.
shared :- valid(A, P, F), share_fix(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, a in ASSETS.items():
        lines.append(asp.fact("asset", aid))
        if aid == "rag":
            lines.append(asp.fact("rag_asset", aid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
        if f.requires_share:
            lines.append(asp.fact("share_fix", fid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    rc = 0
    if py == clingo:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("  only python:", sorted(py - clingo))
        print("  only asp:", sorted(clingo - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-like storyworld about a rag, dialogue, sharing, and problem solving.")
    ap.add_argument("--asset", choices=ASSETS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    if args.asset and args.asset != "rag":
        raise StoryError("(No story: this seed asks for a rag fable, so the asset must be rag.)")
    if args.fix and args.fix != "share_and_wipe":
        raise StoryError("(No story: the fable needs a shared, rag-based solution.)")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("(No story: unknown problem.)")
    combos = [c for c in valid_combos()
              if (args.asset is None or c[0] == args.asset)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    asset, problem, fix = rng.choice(sorted(combos))
    return StoryParams(
        asset=asset,
        problem=problem,
        fix=fix,
        a_name=args.name_a or rng.choice(NAMES_A),
        b_name=args.name_b or rng.choice([n for n in NAMES_B if n != (args.name_a or "")]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.a_name, params.b_name, ASSETS[params.asset], PROBLEMS[params.problem], FIXES[params.fix])
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
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
            params = resolve_params(args, random.Random(seed))
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
