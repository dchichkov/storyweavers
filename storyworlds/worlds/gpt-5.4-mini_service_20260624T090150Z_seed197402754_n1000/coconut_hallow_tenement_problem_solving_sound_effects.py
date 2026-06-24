#!/usr/bin/env python3
"""
A tiny fable-style storyworld about a coconut in a hallow tenement, where
problem solving and sound effects help the lesson land.

The premise:
- In an old tenement, a small helper hears a strange hollow coconut sound.
- The coconut is stuck, rolled, or splintered in a place with echoes.
- The characters solve the problem with simple tools, careful thinking, and
  a gentle lesson learned at the end.

This script is self-contained and follows the storyworld contract.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the tenement"
    echo: bool = True


@dataclass
class Problem:
    id: str
    title: str
    issue: str
    sound: str
    turn: str
    lesson: str
    keyword: str = "coconut"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    makes: str
    solves: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the hallow tenement", echo=True)

PROBLEMS = {
    "coconut_drop": Problem(
        id="coconut_drop",
        title="the coconut in the hall",
        issue="a coconut rolled under a heavy door and got stuck",
        sound="THUNK!",
        turn="they listened for the echo, found the lane of the roll, and lifted the door together",
        lesson="a calm mind can hear a path that panic misses",
        keyword="coconut",
        tags={"coconut", "hallow", "tenement"},
    ),
    "coconut_crack": Problem(
        id="coconut_crack",
        title="the cracked coconut",
        issue="a coconut split open on the stone step",
        sound="CRACK!",
        turn="they gathered the pieces, tied a cloth around the spill, and carried it to a bowl",
        lesson="when something breaks, careful hands can still make it useful",
        keyword="coconut",
        tags={"coconut", "hallow", "tenement"},
    ),
    "echo_misread": Problem(
        id="echo_misread",
        title="the strange hollow echo",
        issue="the hall gave back a hollow sound that frightened the little helper",
        sound="HOOO...",
        turn="they tapped the wall, listened again, and learned the sound came from an empty pipe",
        lesson="not every strange sound is danger; some sounds only ask to be understood",
        keyword="hallow",
        tags={"coconut", "hallow", "tenement"},
    ),
}

TOOLS = {
    "broom": Tool(
        id="broom",
        label="a broom",
        phrase="a long broom",
        use="sweep the path clear",
        makes="swish-swish",
        solves={"coconut_drop", "echo_misread"},
    ),
    "ladder": Tool(
        id="ladder",
        label="a small ladder",
        phrase="a small wooden ladder",
        use="reach the high ledge",
        makes="clack-clack",
        solves={"coconut_drop", "coconut_crack"},
    ),
    "cloth": Tool(
        id="cloth",
        label="a clean cloth",
        phrase="a clean folded cloth",
        use="wrap the cracked shell",
        makes="soft fffft",
        solves={"coconut_crack", "echo_misread"},
    ),
}

HERO_NAMES = ["Milo", "Tia", "Rin", "Sora", "Nia", "Juno"]
HERO_TYPES = ["mouse", "sparrow", "rabbit", "cat"]
HERO_TRAITS = ["kind", "careful", "brave", "patient", "curious"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    problem: str
    tool: str
    name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.solves


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not help with {problem.title}. "
        f"The problem and the tool must fit together, or the fable has no honest turn.)"
    )


def build_world(params: StoryParams) -> World:
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if not reasonableness_gate(problem, tool):
        raise StoryError(explain_rejection(problem, tool))

    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.hero_type,
        label=params.name,
        meters={"care": 1.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="rabbit",
        label="the neighbor",
        meters={"patience": 1.0},
        memes={"calm": 1.0},
    ))
    coconut = world.add(Entity(
        id="coconut",
        type="coconut",
        label="a coconut",
        phrase="a round coconut",
        owner=None,
        caretaker=None,
        region="hall",
        meters={"stuck": 1.0 if problem.id == "coconut_drop" else 0.0,
                "cracked": 1.0 if problem.id == "coconut_crack" else 0.0,
                "echo": 1.0 if problem.id == "echo_misread" else 0.0},
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        coconut=coconut,
        problem=problem,
        tool=tool,
    )
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    coconut: Entity = world.facts["coconut"]
    problem: Problem = world.facts["problem"]
    tool: Tool = world.facts["tool"]

    world.say(
        f"Once, in {world.setting.place}, there lived a little {hero.type} named {hero.id} "
        f"who was {next((t for t in HERO_TRAITS if t in hero.memes), 'curious')} by nature."
    )
    world.say(
        f"One gray morning, {hero.id} heard {problem.sound} from the hall, and then saw "
        f"{coconut.label} tied up in the trouble of the old stones."
    )
    world.para()
    world.say(
        f"{hero.id} did not rush. {hero.pronoun().capitalize()} listened again and said, "
        f"\"Let us solve this gently.\""
    )
    world.say(
        f"The neighbor brought {tool.label}, and it made a soft {tool.makes} as they began to "
        f"{tool.use}."
    )
    world.say(
        f"After that, {problem.turn}."
    )
    world.para()
    hero.memes["wisdom"] = 1.0
    helper.memes["approval"] = 1.0
    coconut.meters["safe"] = 1.0
    world.say(
        f"{coconut.label.capitalize()} was no longer stuck or feared, and the hall felt quiet again."
    )
    world.say(
        f"{hero.id} learned that {problem.lesson}, and {helper.label} smiled at the lesson well kept."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    t: Tool = f["tool"]
    h: Entity = f["hero"]
    return [
        f'Write a short fable for a child that includes the word "{p.keyword}" and the sound "{p.sound}".',
        f"Tell a gentle problem-solving story where {h.id} must face {p.title} using {t.label}.",
        f"Write a lesson-learned story in a hallow tenement with a coconut, a sound effect, and a calm fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    coconut: Entity = f["coconut"]
    return [
        QAItem(
            question=f"What problem did {hero.id} hear in the tenement?",
            answer=f"{hero.id} heard {problem.sound} and found that {problem.issue}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the trouble?",
            answer=f"{hero.id} used {tool.label}, which helped {tool.use}.",
        ),
        QAItem(
            question=f"What was the lesson learned in the end?",
            answer=f"The lesson was that {problem.lesson}.",
        ),
        QAItem(
            question=f"What happened to {coconut.label} by the end of the story?",
            answer=f"{coconut.label.capitalize()} was safe again, and the hall became calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coconut?",
            answer="A coconut is a hard fruit with a shell and soft meat inside.",
        ),
        QAItem(
            question="What is a tenement?",
            answer="A tenement is a many-room building where several families may live close together.",
        ),
        QAItem(
            question="What does a hollow sound mean?",
            answer="A hollow sound can happen when something is empty inside or when sound echoes off a space.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_ok(P) :- problem(P).
tool_ok(T) :- tool(T).

solves(T, P) :- tool(T), problem(P), helps(T, P).

valid_story(P, T) :- problem(P), tool(T), solves(T, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import per contract
    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.solves):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, t) for p in PROBLEMS for t in TOOLS if reasonableness_gate(PROBLEMS[p], TOOLS[t])}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style storyworld of coconut, hallow, and tenement.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=HERO_TRAITS)
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


CURATED = [
    StoryParams(problem="coconut_drop", tool="ladder", name="Milo", hero_type="mouse", trait="careful"),
    StoryParams(problem="coconut_crack", tool="cloth", name="Tia", hero_type="rabbit", trait="patient"),
    StoryParams(problem="echo_misread", tool="broom", name="Rin", hero_type="cat", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(p, t) for p in PROBLEMS for t in TOOLS if reasonableness_gate(PROBLEMS[p], TOOLS[t])]
    if args.problem and args.tool and not reasonableness_gate(PROBLEMS[args.problem], TOOLS[args.tool]):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool]))
    filtered = [
        (p, t) for p, t in combos
        if (args.problem is None or p == args.problem)
        and (args.tool is None or t == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    problem, tool = rng.choice(sorted(filtered))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    trait = args.trait or rng.choice(HERO_TRAITS)
    return StoryParams(problem=problem, tool=tool, name=name, hero_type=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible pairs:")
        for p, t in pairs:
            print(f"  {p:15} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.problem} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
