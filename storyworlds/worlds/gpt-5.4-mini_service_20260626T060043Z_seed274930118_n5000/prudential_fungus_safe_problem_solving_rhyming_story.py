#!/usr/bin/env python3
"""
storyworlds/worlds/prudential_fungus_safe_problem_solving_rhyming_story.py
=========================================================================

A small storyworld about a child who finds fungus, stays safe, and solves the
problem with a prudent plan in a rhyming-story style.

The seed words are woven into the domain:
- prudential: the careful, sensible way to act
- fungus: the fuzzy problem that needs attention
- safe: the outcome we aim for

The world model tracks physical meters and emotional memes, then narrates a
short complete story with a beginning, middle turn, and ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    smell: str
    affords: set[str] = field(default_factory=set)


@dataclass
class FungusProblem:
    id: str
    label: str
    phrase: str
    mess: str
    risk: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    safe_for: set[str]
    action: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**{**v.__dict__}) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.lines = list(self.lines)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, smell="warm toast", affords={"bread", "pantry"}),
    "garden": Setting(place="the garden", indoor=False, smell="damp earth", affords={"plant", "soil"}),
}

PROBLEMS = {
    "bread_fungus": FungusProblem(
        id="bread_fungus",
        label="fungus",
        phrase="a fuzzy patch of fungus",
        mess="stale",
        risk="spoiled",
        location="on the bread",
        tags={"fungus", "bread", "safe"},
    ),
    "pot_fungus": FungusProblem(
        id="pot_fungus",
        label="fungus",
        phrase="a fuzzy ring of fungus",
        mess="damp",
        risk="wilted",
        location="around the plant pot",
        tags={"fungus", "plant", "safe"},
    ),
}

TOOLS = [
    Tool(
        id="gloves",
        label="rubber gloves",
        phrase="rubber gloves",
        safe_for={"fungus"},
        action="put on the gloves",
        tail="washed their hands and tossed the bag in the bin",
        plural=True,
    ),
    Tool(
        id="bag",
        label="a paper bag",
        phrase="a paper bag",
        safe_for={"fungus"},
        action="slid the fuzzy piece into a bag",
        tail="tied the bag shut and carried it away",
    ),
    Tool(
        id="trowel",
        label="a small trowel",
        phrase="a small trowel",
        safe_for={"fungus"},
        action="lifted the plant carefully",
        tail="moved the plant to clean soil",
    ),
]

NAMES = ["Mia", "Leo", "Nina", "Owen", "Ava", "Theo", "Luna", "Noah"]
TRAITS = ["careful", "brave", "kind", "bright", "curious", "steady"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_name(s: str) -> str:
    return re.sub(r"\W+", " ", s).strip()


def starts_with_vowel_sound(word: str) -> bool:
    return word[:1].lower() in {"a", "e", "i", "o", "u"}


def article_for(phrase: str) -> str:
    return "an" if starts_with_vowel_sound(phrase) else "a"


def rhyme_end(word: str) -> str:
    return {
        "safe": "brave",
        "glove": "love",
        "light": "bright",
        "tale": "trail",
        "clean": "glean",
        "plan": "can",
        "care": "fair",
        "away": "day",
        "bin": "win",
        "nest": "best",
    }.get(word, word)


def rhyme_sentence(a: str, b: str) -> str:
    return f"{a} {b}"


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def problem_matches_setting(problem: FungusProblem, setting: Setting) -> bool:
    if setting.indoor:
        return problem.id == "bread_fungus"
    return problem.id == "pot_fungus"


def tool_solves(problem: FungusProblem, tool: Tool) -> bool:
    return "fungus" in tool.safe_for and problem.label == "fungus"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prob_id, problem in PROBLEMS.items():
            if not problem_matches_setting(problem, setting):
                continue
            for tool in TOOLS:
                if tool_solves(problem, tool):
                    out.append((place, prob_id, tool.id))
    return out


def explain_rejection(problem: FungusProblem, tool: Tool) -> str:
    if not tool_solves(problem, tool):
        return (
            f"(No story: {tool.label} is not a safe enough way to handle {problem.label}. "
            f"Try a tool that keeps the child away from the fungus.)"
        )
    return "(No story: that combination is not reasonable in this setting.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def story_rhyme(text: str) -> str:
    return text


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    tool = next(t for t in TOOLS if t.id == params.tool)

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        owner=None,
        caretaker=None,
        meters={"worry": 0.0, "brave": 0.0, "mess": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"worry": 0.0, "help": 0.0},
        memes={"care": 0.0},
    ))
    bug = world.add(Entity(
        id="fungus",
        type="fungus",
        label=problem.label,
        phrase=problem.phrase,
        owner=None,
        caretaker=parent.id,
        location=problem.location,
        meters={"spread": 1.0, "mess": 1.0},
        memes={"alarm": 0.0},
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        plural=tool.plural,
        meters={"clean": 1.0},
    ))

    # Beginning
    world.say(
        f"{child.id} was {article_for(params.trait)} {params.trait} little {child.type}, "
        f"and {setting.smell} filled {setting.place} like a song."
    )
    world.say(
        f"{child.id} noticed {problem.phrase} {problem.location}; "
        f"it looked odd, yet not quite long, not quite wrong."
    )
    child.memes["worry"] += 1
    bug.memes["alarm"] += 1

    # Middle turn
    world.para()
    world.say(
        f"{child.id} called for {parent.label}. "
        f"'{problem.label} should not be touched bare-handed, that's fair!'"
    )
    parent.memes["care"] += 1
    parent.meters["worry"] += 1
    world.say(
        f"The {params.parent} nodded and said, 'Let's choose a {rhyme_end('safe')} way to go. "
        f"We can fix this without letting it grow.'"
    )
    child.meters["brave"] += 1
    child.memes["worry"] += 0.5

    # Resolution
    world.para()
    if tool.id == "gloves":
        world.say(
            f"They {tool.action}, then used {tool.phrase} to keep fingers away from the foe."
        )
    elif tool.id == "bag":
        world.say(
            f"They {tool.action}, and the fuzzy piece slid quietly in a row."
        )
    else:
        world.say(
            f"They {tool.action}, and with the tool they made the little problem slow."
        )

    bug.meters["spread"] = 0.0
    bug.meters["mess"] = 0.0
    bug.memes["alarm"] = 0.0
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.memes["relief"] += 1
    parent.memes["care"] += 1
    world.say(
        f"{parent.label} made the place clean and calm; {child.id} watched the safe plan show."
    )
    world.say(
        f"By the end, the fungus was gone, and {child.id} could smile in the glow."
    )

    world.facts.update(
        child=child,
        parent=parent,
        problem=problem,
        tool=tool_ent,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        f"Write a short rhyming story about {child.id} finding {problem.label} and using {tool.label} safely.",
        f"Tell a gentle problem-solving tale where a child stays safe around {problem.phrase}.",
        f"Write a child-friendly rhyme in which the grown-up and child choose a prudent plan for {problem.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    problem = f["problem"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {child.id} find the fungus?",
            answer=f"{child.id} found the fungus in {setting.place}, where the air smelled like {setting.smell}.",
        ),
        QAItem(
            question=f"Why did {child.id} call for {parent.label}?",
            answer=f"{child.id} called for {parent.label} because touching the fungus bare-handed would not be safe.",
        ),
        QAItem(
            question=f"How did they solve the fungus problem?",
            answer=f"They used {tool.phrase} and a careful plan so the fungus could be handled safely.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the fungus was cleaned away and {child.id} felt calm and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fungus?",
            answer="Fungus is a living thing that can grow in damp places. Some fungus is harmless, but some kinds need to be cleaned up safely.",
        ),
        QAItem(
            question="What does it mean to be prudent?",
            answer="To be prudent means to be careful and sensible, especially when something could be risky.",
        ),
        QAItem(
            question="Why should you wash your hands after handling something moldy?",
            answer="You wash your hands so you do not carry germs or tiny bits of mess to your mouth, eyes, or other things.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is valid in a setting when the setting matches the kind of fungus issue.
valid_problem(Place, Prob) :- setting(Place), problem(Prob), matches_setting(Place, Prob).

% A tool is a valid fix when it is marked safe for fungus and actually handles fungus.
valid_tool(Tool) :- tool(Tool), safe_for(Tool, fungus), handles(Tool, fungus).

% A full story is valid when the place/problem pair is right and there is a valid tool.
valid_story(Place, Prob, Tool) :- valid_problem(Place, Prob), valid_tool(Tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if s.indoor:
            lines.append(asp.fact("indoor", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("kind", pid, p.label))
        lines.append(asp.fact("matches_setting", "kitchen" if pid == "bread_fungus" else "garden", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        lines.append(asp.fact("handles", tool.id, "fungus"))
        for s in sorted(tool.safe_for):
            lines.append(asp.fact("safe_for", tool.id, s))
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
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small rhyming storyworld about fungus, prudence, and safe problem solving."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place or args.problem or args.tool:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.problem is None or c[1] == args.problem)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = clean_name(args.name or rng.choice(NAMES))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    if args.tool and not tool_solves(PROBLEMS[problem], next(t for t in TOOLS if t.id == tool)):
        raise StoryError(explain_rejection(PROBLEMS[problem], next(t for t in TOOLS if t.id == tool)))

    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


def valid_combos_all() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(place="kitchen", problem="bread_fungus", tool="gloves", name="Mia", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="garden", problem="pot_fungus", tool="bag", name="Leo", gender="boy", parent="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(models, "valid_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
