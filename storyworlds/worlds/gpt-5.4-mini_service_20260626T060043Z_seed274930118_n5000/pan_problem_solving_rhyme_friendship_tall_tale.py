#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale problem-solving friendship story about
a pan, with rhymes and a satisfying fix.

Premise:
A pair of friends need to cook a giant breakfast in a comically oversized pan.
The pan is too hot, too slippery, or too stuck depending on the sampled setup.

Tension:
The friends try the wrong quick fix first, which makes the problem worse.

Turn:
They stop, rhyme their way through the trouble, and choose a sensible tool or
method that actually solves the problem.

Resolution:
The pan works, the meal gets made, and the friends end together on a bright,
friendly note.

This world models:
- physical meters: heat, balance, shine, stickiness, progress
- emotional memes: worry, courage, friendship, pride, relief
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
# Core domain data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    in_hand: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    heat_source: str
    wind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    consequence: str
    meter: str
    start_value: float = 1.0


@dataclass
class Fix:
    id: str
    label: str
    verb: str
    rhyme: str
    solves: str
    requires: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.history = list(self.history)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barnyard": Setting(place="the barnyard", heat_source="a wood stove", wind="a warm prairie wind", affords={"stuck", "slip"}),
    "kitchen": Setting(place="the kitchen", heat_source="a stove", wind="a window breeze", affords={"stuck", "slip"}),
    "camp": Setting(place="the campfire clearing", heat_source="a campfire", wind="a moonlit breeze", affords={"stuck", "slip"}),
}

PROBLEMS = {
    "stuck": Problem(
        id="stuck",
        label="stuck pan",
        trouble="the pan was glued to the stove with old syrup",
        consequence="no breakfast could lift off the bottom",
        meter="stickiness",
    ),
    "slip": Problem(
        id="slip",
        label="slippery pan",
        trouble="the pan kept scooting away like a fish on ice",
        consequence="the pancake batter would slide right out",
        meter="balance",
    ),
}

FIXES = {
    "salt": Fix(
        id="salt",
        label="a shake of salt",
        verb="sprinkled",
        rhyme="Salt in a circle, plain and bright, helps a pan behave just right.",
        solves="stickiness",
        requires={"stuck"},
    ),
    "towel": Fix(
        id="towel",
        label="a folded towel",
        verb="set under it",
        rhyme="Towel on the table, square and neat, gives a pan a steady seat.",
        solves="balance",
        requires={"slip"},
    ),
    "spoon": Fix(
        id="spoon",
        label="a long wooden spoon",
        verb="used as a handle helper",
        rhyme="Spoon in the middle, strong and true, gives a big old pan its due.",
        solves="control",
        requires={"stuck", "slip"},
    ),
}

HERO_NAMES = ["Mabel", "Otis", "Nell", "Bo", "June", "Pip", "Willa", "Buck"]
FRIEND_NAMES = ["Eli", "Rose", "Jasper", "Dot", "Milo", "Greta", "Tess", "Hank"]

TRAITS = ["brave", "cheery", "lively", "nimble", "stubborn", "kind"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, problem: str, fix: str) -> bool:
    if place not in SETTINGS or problem not in PROBLEMS or fix not in FIXES:
        return False
    if problem not in SETTINGS[place].affords:
        return False
    return problem in FIXES[fix].requires


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for problem in PROBLEMS:
            for fix in FIXES:
                if valid_combo(place, problem, fix):
                    out.append((place, problem, fix))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is valid at a place if that place affords it.
valid_problem(P, Prob) :- setting(P), problem(Prob), affords(P, Prob).

% A fix is valid for a problem when it solves that problem.
valid_fix(Prob, Fix) :- problem(Prob), fix(Fix), requires(Fix, Prob).

% A complete story is valid if the place supports the problem and the fix
% is compatible with that problem.
valid_story(P, Prob, Fix) :- valid_problem(P, Prob), valid_fix(Prob, Fix).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for p in sorted(fx.requires):
            lines.append(asp.fact("requires", fid, p))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character"))
    friend = world.add(Entity(id=params.friend, kind="character"))
    pan = world.add(Entity(id="pan", label="pan", phrase="a giant iron pan"))
    pan.meters = {"heat": 1.0, "stickiness": 0.0, "balance": 0.0, "shine": 0.2, "progress": 0.0}
    pan.memes = {"worry": 0.0, "friendship": 1.0, "pride": 0.0, "relief": 0.0}
    world.add(pan)
    world.facts.update(hero=hero, friend=friend, pan=pan)
    return world


def apply_problem(world: World, problem: Problem) -> None:
    pan = world.get("pan")
    pan.meters[problem.meter] = problem.start_value
    pan.memes["worry"] += 1.0
    world.say(
        f"In {world.setting.place}, {world.facts['hero'].id} and {world.facts['friend'].id} found a giant pan as wide as a wagon wheel."
    )
    world.say(
        f"It looked ready to cook a breakfast for a whole parade, but {problem.trouble}."
    )
    world.say(
        f"That meant {problem.consequence}, and the two friends scratched their heads beneath {world.setting.heat_source}."
    )


def wrong_try(world: World, problem: Problem) -> None:
    pan = world.get("pan")
    if problem.id == "stuck":
        pan.meters["stickiness"] += 0.5
        pan.memes["worry"] += 0.5
        world.say("They tried a quick tug, but the pan only clung tighter and gave a stubborn squeak.")
    else:
        pan.meters["balance"] -= 0.4
        pan.memes["worry"] += 0.5
        world.say("They tried to chase it by hand, but the pan skittered away and nearly waltzed off the table.")


def rhyme_fix(world: World, fix: Fix) -> None:
    pan = world.get("pan")
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(f"{hero.id} and {friend.id} paused, took a breath, and sang:")
    world.say(f'"{fix.rhyme}"')
    if fix.id == "salt":
        pan.meters["stickiness"] = max(0.0, pan.meters["stickiness"] - 1.0)
        pan.meters["progress"] += 0.6
        pan.memes["pride"] += 0.4
    elif fix.id == "towel":
        pan.meters["balance"] += 1.0
        pan.meters["progress"] += 0.6
        pan.memes["pride"] += 0.4
    else:
        pan.meters["stickiness"] = max(0.0, pan.meters["stickiness"] - 0.5)
        pan.meters["balance"] += 0.5
        pan.meters["progress"] += 1.0
        pan.memes["pride"] += 0.7


def solve_problem(world: World, problem: Problem, fix: Fix) -> None:
    pan = world.get("pan")
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(f"{friend.id} fetched {fix.label}, and {hero.id} {fix.verb} it with a grin.")
    rhyme_fix(world, fix)
    pan.memes["worry"] = max(0.0, pan.memes["worry"] - 1.0)
    pan.memes["relief"] += 1.0
    world.say(
        f"Just like that, the old trouble loosened its grip, and the giant pan settled down steady as a barn door in a calm wind."
    )
    world.say(
        f"The friends poured in the batter, and the pancake rose tall and round, puffing up like a sunrise."
    )
    world.say(
        f"By the end, {hero.id} and {friend.id} had {problem.label} turned into a fine feast, and the pan shone like a silver moon in a blue sky."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    hero = world.facts["hero"]
    friend = world.facts["friend"]

    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0

    world.say(
        f"{hero.id} was a {params.trait} cook with a laugh as loud as a kettle, and {friend.id} was a friendly helper with quick hands."
    )
    world.say(
        f"Together they wanted to make a breakfast so big it could feed the rooster, the cow, and half the county fair."
    )
    world.para()
    apply_problem(world, problem)
    world.para()
    wrong_try(world, problem)
    world.say(
        f"{hero.id} said, 'When the pan won't play nice, we must think twice.'"
    )
    world.say(
        f"{friend.id} replied, 'A small mind may fret, but a wise heart can set the table yet.'"
    )
    solve_problem(world, problem, fix)
    world.para()
    world.say(
        f"So the two friends ate their towering breakfast side by side, smiling big enough to light the porch and the pasture."
    )

    world.facts.update(problem=problem, fix=fix, params=params)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale about {f['hero'].id} and {f['friend'].id}, who need to solve a problem with a pan.",
        f"Tell a rhyming friendship story where {f['hero'].id} and {f['friend'].id} fix a {f['problem'].label} in {world.setting.place}.",
        f"Write a child-friendly tall tale that includes a pan, a mistake, a rhyme, and a clever repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    problem = world.facts["problem"]
    fix = world.facts["fix"]
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}. They worked together the whole time.",
        ),
        QAItem(
            question=f"What problem did the giant pan have?",
            answer=f"The pan had a {problem.label} problem, so {problem.trouble}.",
        ),
        QAItem(
            question=f"What did the friends do after their first try did not work?",
            answer=f"They stopped, sang a rhyme, and used {fix.label} to solve the problem the sensible way.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the pan working well, a tall breakfast ready, and the friends happy together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pan used for?",
            answer="A pan is used for cooking food on a stove, over a fire, or on another hot surface.",
        ),
        QAItem(
            question="Why can a pan be hot?",
            answer="A pan can be hot because heat from a stove or fire spreads into the metal and warms it up.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bright and right.",
        ),
        QAItem(
            question="Why do friends help each other solve problems?",
            answer="Friends help each other because two caring heads can often find a better idea than one.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make the trouble go away or work out better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about friends solving a pan problem with rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.fix:
        combos = [c for c in combos if c[2] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if friend == hero:
        friend = rng.choice([n for n in FRIEND_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, fix=fix, hero=hero, friend=friend, trait=trait)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, problem, fix in valid_combos():
            p = StoryParams(
                place=place,
                problem=problem,
                fix=fix,
                hero=random.choice(HERO_NAMES),
                friend=random.choice(FRIEND_NAMES),
                trait=random.choice(TRAITS),
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
