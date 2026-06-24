#!/usr/bin/env python3
"""
storyworlds/worlds/ferris_lesson_learned_problem_solving_repetition_fable.py
============================================================================

A small fable-style story world about Ferris learning to solve a problem by
trying, noticing, and trying again.

Seed idea:
- Ferris wants something small and important.
- A simple obstacle appears.
- Ferris makes a few repeated attempts.
- Ferris learns a calmer, smarter way to solve the problem.
- The ending proves the lesson learned.

The prose is built from simulated state, not a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    want: str
    reach: str
    reward: str
    challenge: str
    solution_kind: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    use_line: str
    outcome_line: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_too_hard(world: World) -> list[str]:
    out: list[str] = []
    ferris = world.entities.get("Ferris")
    if not ferris:
        return out
    if ferris.memes.get("frustration", 0) < THRESHOLD:
        return out
    if ferris.memes.get("problem_seen", 0) < THRESHOLD:
        return out
    sig = ("too_hard",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ferris.memes["resolve"] = ferris.memes.get("resolve", 0) + 1
    out.append("Ferris paused and thought instead of rushing.")
    return out


CAUSAL_RULES = [
    _r_too_hard,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_facts(world: World) -> None:
    ferris = world.get("Ferris")
    goal = world.facts["goal"]
    tool = world.facts.get("tool")
    world.facts["ferris"] = ferris
    world.facts["tool"] = tool
    world.facts["goal"] = goal


def attempt(world: World, ferris: Entity, goal: Goal, tool: Optional[Tool], attempt_no: int) -> None:
    ferris.memes["tries"] = ferris.memes.get("tries", 0) + 1
    if attempt_no == 1:
        world.say(f"Ferris wanted to {goal.want}, but the {goal.challenge} blocked the way.")
    elif attempt_no == 2:
        world.say(f"Ferris tried again, this time with a little more care.")
    else:
        world.say(f"Ferris tried once more, remembering what the first attempts had taught him.")

    if attempt_no == 1:
        ferris.memes["frustration"] = ferris.memes.get("frustration", 0) + 1
        ferris.memes["problem_seen"] = 1
        world.say(f"{ferris.id} {goal.reach}, but the plan did not work.")
    elif attempt_no == 2:
        ferris.memes["frustration"] = ferris.memes.get("frustration", 0) + 1
        ferris.meters["distance"] = ferris.meters.get("distance", 0) + 1
        world.say(f"{ferris.id} {goal.reach}, and still the result was not enough.")
    else:
        if tool is not None:
            ferris.meters["distance"] = ferris.meters.get("distance", 0) + 1
            ferris.memes["calm"] = ferris.memes.get("calm", 0) + 1
            ferris.memes["solve"] = ferris.memes.get("solve", 0) + 1
            world.say(tool.use_line)
            world.say(tool.outcome_line)
            world.say(f"At last, {ferris.id} could {goal.reward}.")
        else:
            world.say(f"Ferris stopped and looked for a better way.")
    propagate(world, narrate=True)


def tell(setting: Setting, goal: Goal, tool: Optional[Tool], name: str = "Ferris") -> World:
    world = World(setting)
    ferris = world.add(Entity(id=name, kind="character", type="fox"))
    ferris.memes["hope"] = 1
    world.facts["goal"] = goal

    world.say(
        f"{ferris.id} was a small fox who lived near {setting.place} and liked to solve little problems."
    )
    world.say(
        f"One morning, {ferris.id} wanted to {goal.want}, because {goal.reward} was waiting on the other side."
    )
    world.para()

    attempt(world, ferris, goal, tool, 1)
    world.para()
    attempt(world, ferris, goal, tool, 2)
    world.para()
    attempt(world, ferris, goal, tool, 3)

    world.para()
    ferris.memes["lesson"] = 1
    world.say(
        f"Ferris learned that a smart heart can keep trying without getting angry."
    )
    world.say(
        f"From then on, {ferris.id} remembered the lesson: {goal.lesson}."
    )

    world.facts["ferris"] = ferris
    return world


SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"apple"}),
    "stream": Setting(place="the stream", affords={"water"}),
    "hill": Setting(place="the hill", affords={"kite"}),
}


GOALS = {
    "apple": Goal(
        id="apple",
        want="reach the apples on the high branch",
        reach="stretched on tiptoe again and again",
        reward="pick a sweet apple",
        challenge="high branch",
        solution_kind="ladder",
        lesson="look for the right tool instead of only pushing harder",
        tags={"apple", "fruit"},
    ),
    "water": Goal(
        id="water",
        want="carry water to the thirsty flowers",
        reach="walked carefully to the stream and back",
        reward="water the flowers",
        challenge="long path",
        solution_kind="cup",
        lesson="a small, steady helper can do what rushing cannot",
        tags={"water", "flowers"},
    ),
    "kite": Goal(
        id="kite",
        want="fly a kite over the hill",
        reach="ran into the wind and held the string tight",
        reward="watch the kite lift into the sky",
        challenge="wind",
        solution_kind="tail",
        lesson="when one way fails, a better plan can still be found",
        tags={"kite", "wind"},
    ),
}


TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="a little ladder",
        helps={"apple"},
        use_line="Ferris dragged over a little ladder and climbed up carefully.",
        outcome_line="The ladder reached the branch, and the apples came within easy reach.",
    ),
    "cup": Tool(
        id="cup",
        label="a small cup",
        helps={"water"},
        use_line="Ferris filled a small cup and carried it with slow, careful steps.",
        outcome_line="The cup held the water steady, drop by drop, until the flowers drank it up.",
    ),
    "tail": Tool(
        id="tail",
        label="a long tail ribbon",
        helps={"kite"},
        use_line="Ferris tied the string to a long tail ribbon so it would not slip.",
        outcome_line="The ribbon steadied the string, and the kite began to dance above the hill.",
    ),
}


@dataclass
class StoryParams:
    place: str
    goal: str
    tool: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for goal_id in setting.affords:
            goal = GOALS[goal_id]
            for tool_id, tool in TOOLS.items():
                if goal_id in tool.helps:
                    combos.append((place, goal_id, tool_id))
    return combos


KNOWLEDGE = {
    "apple": [("What is an apple?", "An apple is a round fruit that grows on trees and can be sweet or tart.")],
    "water": [("Why do flowers need water?", "Flowers need water so they can stay healthy and grow." )],
    "kite": [("What makes a kite fly?", "A kite flies when the wind pushes on it while someone holds the string.")],
    "ladder": [("What is a ladder for?", "A ladder helps someone reach something that is high up.")],
    "cup": [("What is a cup used for?", "A cup is used for carrying or drinking a small amount of liquid.")],
    "tail": [("What is a tail ribbon?", "A ribbon can help hold something steady or make it easier to see.")],
}


def generation_prompts(world: World) -> list[str]:
    goal = world.facts["goal"]
    return [
        f'Write a fable for young children about Ferris who wants to {goal.want}.',
        f"Tell a short moral story where Ferris faces the {goal.challenge} and keeps trying.",
        f"Write a gentle repetition story with Ferris that ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    ferris = world.facts["ferris"]
    goal = world.facts["goal"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question=f"What did {ferris.id} want to do in the story?",
            answer=f"{ferris.id} wanted to {goal.want}, and that became the problem he had to solve.",
        ),
        QAItem(
            question=f"What made the task hard for {ferris.id}?",
            answer=f"The {goal.challenge} made it hard, so {ferris.id} had to try more than once.",
        ),
        QAItem(
            question=f"How did {ferris.id} finally solve the problem?",
            answer=f"He used {tool.label} and a calmer plan, which helped him {goal.reward}.",
        ),
        QAItem(
            question=f"What lesson did {ferris.id} learn?",
            answer=f"{ferris.id} learned that {goal.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    goal = world.facts["goal"]
    out: list[QAItem] = []
    for tag in goal.tags | world.facts["tool"].helps:
        if tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(goal: Goal, tool: Tool) -> str:
    return f"(No story: {tool.label} does not help with {goal.id}; the compromise would not solve the problem.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for g in sorted(setting.affords):
            lines.append(asp.fact("affords", place, g))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("challenge", gid, goal.challenge))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Goal, Tool) :- affords(Place, Goal), helps(Tool, Goal).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about Ferris, problem solving, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", default="Ferris")
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
    if args.goal and args.tool:
        goal = GOALS[args.goal]
        tool = TOOLS[args.tool]
        if args.goal not in tool.helps:
            raise StoryError(explain_rejection(goal, tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.goal is None or c[1] == args.goal)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal, tool = rng.choice(sorted(combos))
    return StoryParams(place=place, goal=goal, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], GOALS[params.goal], TOOLS[params.tool], params.name)
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


CURATED = [
    StoryParams(place="orchard", goal="apple", tool="ladder"),
    StoryParams(place="stream", goal="water", tool="cup"),
    StoryParams(place="hill", goal="kite", tool="tail"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, goal, tool) combos:\n")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
