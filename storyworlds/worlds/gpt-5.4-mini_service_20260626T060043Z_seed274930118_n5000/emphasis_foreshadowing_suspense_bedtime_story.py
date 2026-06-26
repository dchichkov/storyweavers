#!/usr/bin/env python3
"""
A small storyworld for a bedtime tale with foreshadowing and suspense.

Premise:
- A child gets ready for bed in a quiet room.
- Something small seems wrong: a soft rustle, a missing favorite blanket, a shadow.
- A parent notices the worry and helps the child solve the mystery.
- The ending resolves into a safe, cozy bedtime image.

The world is intentionally tiny and classical: a few typed entities, a few state
changes, and one clear turn from worry to comfort.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
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
class BedtimeSetting:
    place: str = "the bedroom"
    quiet: bool = True
    affords: set[str] = field(default_factory=lambda: {"bedtime", "story", "nightlight"})


@dataclass
class BedtimeProblem:
    id: str
    worry: str
    foreshadow: str
    trigger: str
    turn: str
    ending: str
    clue: str
    keyword: str = "emphasis"
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortTool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: BedtimeSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_type: str
    problem: str
    tool: str
    seed: Optional[int] = None


SETTING = BedtimeSetting()

PROBLEMS = {
    "rustle": BedtimeProblem(
        id="rustle",
        worry="heard a tiny rustle near the bed",
        foreshadow="there was a soft shiver from under the blanket",
        trigger="a little rustle under the bed",
        turn="peek under the bed with the nightlight",
        ending="the room was calm again, with only the blanket breathing in the dark",
        clue="a mouse in the wall",
        tags={"suspense", "foreshadowing"},
    ),
    "missing_blanket": BedtimeProblem(
        id="missing_blanket",
        worry="could not find the favorite blanket",
        foreshadow="the blanket had slipped from the chair earlier",
        trigger="an empty chair where the blanket should have been",
        turn="look behind the chair and under the pillow",
        ending="the blanket was back under the chin, warm and safe",
        clue="the blanket had fallen beside the bed",
        tags={"foreshadowing"},
    ),
    "shadow": BedtimeProblem(
        id="shadow",
        worry="saw a big shadow on the wall",
        foreshadow="the moonlight had been stretching the curtains into long shapes",
        trigger="a shadow that seemed to move when the curtain moved",
        turn="open the curtain just a little and check the window",
        ending="the shadow was only a tree branch waving outside",
        clue="a tree branch outside the window",
        tags={"suspense"},
    ),
}

TOOLS = {
    "nightlight": ComfortTool(
        id="nightlight",
        label="nightlight",
        phrase="a small nightlight with a warm glow",
        solves={"rustle", "shadow"},
        prep="turn on the nightlight",
        tail="left the nightlight glowing softly by the bed",
    ),
    "blanket": ComfortTool(
        id="blanket",
        label="blanket",
        phrase="a soft blanket with sleepy stars",
        solves={"missing_blanket"},
        prep="shake out the blanket and smooth it down",
        tail="tucked the blanket in neatly",
    ),
    "teddy": ComfortTool(
        id="teddy",
        label="teddy bear",
        phrase="a teddy bear with round stitched ears",
        solves={"rustle", "missing_blanket", "shadow"},
        prep="hold the teddy bear close",
        tail="set teddy bear beside the pillow",
        plural=False,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ella", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Max", "Ben"]
TRAITS = ["sleepy", "gentle", "curious", "brave", "quiet"]


ASP_RULES = r"""
problem_needs_tool(P, T) :- problem(P), solves(T, P).
valid_story(P, T) :- problem(P), tool(T), solves(T, P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "bedroom"), asp.fact("quiet", "bedroom")]
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.solves):
            lines.append(asp.fact("solves", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def bed_time_reasonable(problem: BedtimeProblem, tool: ComfortTool) -> bool:
    return problem.id in tool.solves


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime Story world with foreshadowing and suspense.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        if not bed_time_reasonable(PROBLEMS[args.problem], TOOLS[args.tool]):
            raise StoryError("That comfort tool does not reasonably solve the bedtime problem.")
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool = args.tool or rng.choice([t for t in TOOLS if problem in TOOLS[t].solves])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(child_name=name, child_gender=gender, parent_type=parent, problem=problem, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        meters={"sleepy": 0.3, "comfort": 0.2},
        memes={"worry": 0.0, "hope": 0.2},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        meters={"quiet": 1.0},
        memes={"care": 1.0},
    ))
    blanket = world.add(Entity(
        id="blanket",
        type="blanket",
        label="blanket",
        phrase="a soft blanket",
        owner=child.id,
        caretaker=parent.id,
        meters={"coziness": 1.0},
    ))
    tool = world.add(Entity(
        id=params.tool,
        type=params.tool,
        label=TOOLS[params.tool].label,
        phrase=TOOLS[params.tool].phrase,
        owner=child.id,
        caretaker=parent.id,
        protective=True,
    ))
    problem = PROBLEMS[params.problem]

    # Setup
    world.say(f"{child.id} was a little {params.child_gender} who was getting ready for bed in {world.setting.place}.")
    world.say(f"{child.id} liked the quiet of night, and {problem.foreshadow}.")
    world.say(f"{problem.worry.capitalize()}, and that made {child.pronoun('object')} pause.")
    world.para()

    # Suspense
    world.say(f"The {params.parent_type} came in with a soft smile and listened.")
    world.say(f"Together they noticed {problem.trigger}.")
    child.memes["worry"] += 1.0
    parent.memes["care"] += 0.5
    world.say(f"{child.id} held still, because the room felt very big for one small moment.")
    world.para()

    # Resolution
    world.say(f"Then {params.parent_type} said it was time to {TOOLS[params.tool].prep}.")
    if params.tool == "blanket":
        world.say(f"They found the answer by the bed: {problem.clue}.")
    elif params.tool == "nightlight":
        world.say(f"The warm glow showed that {problem.clue} was not scary at all.")
    else:
        world.say(f"{tool.label.capitalize()} helped chase the worry away, and {problem.clue} seemed ordinary again.")
    child.memes["worry"] = 0.0
    child.memes["peace"] = 1.0
    child.meters["coziness"] = 1.0
    blanket.worn_by = child.id
    tool.worn_by = child.id
    world.say(f"{child.id} sighed, snuggled in, and {params.parent_type} {problem.ending}.")
    world.say(f"At last, {child.id} fell asleep with {tool.label} nearby and the blanket tucked close.")

    world.facts.update(child=child, parent=parent, blanket=blanket, tool=tool, problem=problem, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    t = world.facts["tool"]
    c = world.facts["child"]
    return [
        f'Write a bedtime story for a small child that uses the word "{p.keyword}" and includes foreshadowing.',
        f"Tell a gentle suspense story where {c.id} notices {p.worry} and a parent helps with {t.label}.",
        f"Write a cozy bedtime tale where a quiet room has a small mystery and ends with safe sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    p = f["parent"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What was {c.id} worried about at bedtime?",
            answer=f"{c.id} was worried because {problem.worry}. The little mystery made the room feel suspenseful for a moment.",
        ),
        QAItem(
            question=f"How did {p.label} help {c.id} feel safer?",
            answer=f"{p.label.capitalize()} helped by using {tool.label} and checking the clue carefully. That turned the worry into something ordinary and safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {c.id} was cozy, calm, and ready to sleep. The bedtime mystery was solved, and the room felt peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue early in a story that hints that something important may happen later.",
        ),
        QAItem(
            question="What does suspense do in a bedtime story?",
            answer="Suspense makes you wonder what is going to happen next, but in a gentle bedtime story it ends safely and calmly.",
        ),
        QAItem(
            question="Why do children like a nightlight?",
            answer="A nightlight gives a soft glow, which can make a dark room feel friendlier and easier to settle in.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(child_name="Mia", child_gender="girl", parent_type="mother", problem="rustle", tool="nightlight"),
    StoryParams(child_name="Leo", child_gender="boy", parent_type="father", problem="missing_blanket", tool="blanket"),
    StoryParams(child_name="Ava", child_gender="girl", parent_type="mother", problem="shadow", tool="teddy"),
]


def explain_rejection(problem: BedtimeProblem, tool: ComfortTool) -> str:
    return f"(No story: {tool.label} does not reasonably solve {problem.id} in this bedtime world.)"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, t) for p in PROBLEMS for t in TOOLS if bed_time_reasonable(PROBLEMS[p], TOOLS[t]))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print("\n".join(f"{p} {t}" for p, t in pairs))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
