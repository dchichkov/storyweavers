#!/usr/bin/env python3
"""
A small fable-style storyworld about a mammy who solves a problem by thinking
carefully, asking for help, and choosing a practical fix.

The seed idea is a classic TinyStories-like fable:
- a child or animal gets into a small trouble,
- mammy notices the real cause,
- they try a sensible fix,
- the ending proves the problem changed.

The world is intentionally small and constraint-checked so every generated story
feels like a complete little fable.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------

@dataclass
class Character:
    id: str
    role: str
    kind: str = "character"
    species: str = "animal"
    name: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"mammy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"son", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def title(self) -> str:
        return self.role


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    visible: str
    risk: str
    fix: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.characters: dict[str, Character] = {}
        self.objects: dict[str, dict] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.id] = ch
        return ch

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "orchard": Setting("the orchard", {"trees", "fruit", "paths"}),
    "cottage": Setting("the cottage", {"rooms", "table", "stove"}),
    "pond": Setting("the pond", {"water", "reeds", "stones"}),
    "meadow": Setting("the meadow", {"grass", "flowers", "stones"}),
}

PROBLEMS = {
    "jar": Problem(
        id="jar",
        label="stuck jar",
        cause="the lid was too tight",
        visible="would not open",
        risk="the jam would stay out of reach",
        fix="use a warm cloth and a steady twist",
        solved_by="warm_cloth",
        tags={"kitchen", "careful"},
    ),
    "kite": Problem(
        id="kite",
        label="tangled kite string",
        cause="the string had looped around a branch",
        visible="was caught in the tree",
        risk="the kite could not fly",
        fix="walk to the branch, loosen the loop, and wind the string neatly",
        solved_by="branch_help",
        tags={"wind", "tree"},
    ),
    "bridge": Problem(
        id="bridge",
        label="wobbly little bridge",
        cause="a plank had slipped loose",
        visible="made a shaky path",
        risk="someone might stumble",
        fix="set the plank straight and test each step slowly",
        solved_by="plank_fix",
        tags={"path", "careful"},
    ),
    "basket": Problem(
        id="basket",
        label="full basket that tipped",
        cause="the handle was caught on a thorn",
        visible="leaned sideways",
        risk="the apples would fall",
        fix="lift the handle free, then carry the basket with two hands",
        solved_by="two_hands",
        tags={"fruit", "careful"},
    ),
}

HEROES = [
    ("Bram", "boy"),
    ("Poppy", "girl"),
    ("Milo", "boy"),
    ("Luna", "girl"),
]

MAMMY_NAMES = ["Mammy Rose", "Mammy June", "Mammy Nell", "Mammy Belle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
problem(C) :- cause(C,_).
solvable(C) :- fix(C,_).
good_story(S,P) :- setting(S), problem(P), allowed(S,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(s.features):
            lines.append(asp.fact("feature", sid, feat))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("cause", pid, p.cause))
        lines.append(asp.fact("fix", pid, p.solved_by))
        lines.append(asp.fact("label", pid, p.label))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for sid in SETTINGS:
        for pid in PROBLEMS:
            lines.append(asp.fact("allowed", sid, pid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    models = asp.one_model(asp_program("#show good_story/2."))
    atom_set = set(asp.atoms(models, "good_story"))
    py_set = {(sid, pid) for sid in SETTINGS for pid in PROBLEMS}
    if atom_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} pairs).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in clingo:", sorted(atom_set - py_set))
    print("only in python:", sorted(py_set - atom_set))
    return 1


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]

    world = World(setting)
    hero_name, hero_kind = next((n, k) for n, k in HEROES if n == params.hero)
    hero = world.add_character(Character(id="hero", role="child", species=hero_kind, name=hero_name))
    mammy = world.add_character(Character(id="mammy", role="mammy", species="animal", name=params.helper))

    world.facts.update(hero=hero, mammy=mammy, problem=problem, setting=setting)

    # Act 1: situation.
    world.say(
        f"Once upon a time, in {setting.place}, there was a little {hero.kind} named {hero.name} "
        f"and {mammy.name}, who was known by everyone as a wise mammy."
    )
    world.say(
        f"One morning, {hero.name} found a {problem.label} that {problem.visible}, "
        f"because {problem.cause}."
    )

    # Act 2: tension.
    world.para()
    hero.memes["worry"] = 1
    world.say(
        f"{hero.name} frowned, because {problem.risk}. "
        f"{mammy.name} looked at the problem and did not rush."
    )
    world.say(
        f"She said, \"Let us think first, and then we will solve it properly.\""
    )

    # Act 3: solution.
    world.para()
    if problem.solved_by == "warm_cloth":
        world.say(
            f"{mammy.name} warmed a cloth by the stove, wrapped it around the lid, and turned it slowly."
        )
        world.say(
            f"With one careful twist, the jar opened at last."
        )
    elif problem.solved_by == "branch_help":
        world.say(
            f"{mammy.name} pointed to the branch, and {hero.name} climbed close enough to loosen the loop."
        )
        world.say(
            f"Then they wound the string neatly, and the kite hung free in the breeze."
        )
    elif problem.solved_by == "plank_fix":
        world.say(
            f"{mammy.name} knelt by the bridge, set the plank straight, and pressed it down firmly."
        )
        world.say(
            f"She tested it with one slow step, and the little bridge stood steady again."
        )
    else:
        world.say(
            f"{mammy.name} lifted the handle free from the thorn and handed the basket back with both hands."
        )
        world.say(
            f"The apples stayed inside, and the basket carried on without tipping."
        )

    hero.memes["relief"] = 1
    world.say(
        f"{hero.name} smiled, because the problem was solved, and {mammy.name} smiled too."
    )
    world.say(
        f"That day, the little one learned that a calm mind and a good helper can make a hard thing easy."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].name
    mammy = f["mammy"].name
    problem = f["problem"].label
    place = f["setting"].place
    return [
        f'Write a short fable about {mammy} helping {hero} solve a {problem} at {place}.',
        f'Write a child-friendly story where a wise mammy uses careful thinking to fix a small problem.',
        f'Tell a simple fable about a child, a problem, and a sensible solution in {place}.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].name
    mammy = f["mammy"].name
    problem = f["problem"]
    setting = f["setting"].place
    return [
        QAItem(
            question=f"What problem did {hero} find in {setting}?",
            answer=f"{hero} found a {problem.label}. It was a small trouble, but it needed a careful fix.",
        ),
        QAItem(
            question=f"How did {mammy} solve the problem?",
            answer=f"{mammy} solved it by choosing a calm, practical step: {problem.fix}.",
        ),
        QAItem(
            question=f"What did {hero} learn at the end?",
            answer="The child learned that if you stop, think, and try a sensible fix, a hard problem can become easy.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often teaches a lesson, sometimes with animals or gentle, wise characters.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make the trouble better or make it go away.",
        ),
        QAItem(
            question="Why is it helpful to think before acting?",
            answer="Thinking first helps you choose a safe and sensible plan instead of making the trouble worse.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PROBLEMS]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about mammy problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero", choices=[n for n, _ in HEROES])
    ap.add_argument("--helper", choices=MAMMY_NAMES)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, problem = rng.choice(sorted(combos))
    hero = args.hero or rng.choice([n for n, _ in HEROES])
    helper = args.helper or rng.choice(MAMMY_NAMES)
    return StoryParams(setting=setting, problem=problem, hero=hero, helper=helper)

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ch in world.characters.values():
        bits = []
        if ch.memes:
            bits.append(f"memes={dict(ch.memes)}")
        if ch.meters:
            bits.append(f"meters={dict(ch.meters)}")
        lines.append(f"  {ch.id:8} ({ch.role:7}) name={ch.name} {' '.join(bits)}")
    if world.facts:
        lines.append(f"  facts: problem={world.facts['problem'].id}, setting={world.facts['setting'].place}")
    return "\n".join(lines)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))

def asp_verify_gate() -> int:
    py = set(valid_combos())
    asp_pairs = set(asp_valid_pairs())
    if py == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - asp_pairs:
        print("  only in python:", sorted(py - asp_pairs))
    if asp_pairs - py:
        print("  only in clingo:", sorted(asp_pairs - py))
    return 1

ASP_RULES = r"""
good_story(S,P) :- setting(S), problem(P), allowed(S,P).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

CURATED = [
    StoryParams("orchard", "basket", "Poppy", "Mammy Rose"),
    StoryParams("cottage", "jar", "Bram", "Mammy June"),
    StoryParams("meadow", "kite", "Luna", "Mammy Nell"),
    StoryParams("pond", "bridge", "Milo", "Mammy Belle"),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        import asp
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible setting/problem pairs:")
        for s, p in pairs:
            print(f"  {s:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero} / {p.problem} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
