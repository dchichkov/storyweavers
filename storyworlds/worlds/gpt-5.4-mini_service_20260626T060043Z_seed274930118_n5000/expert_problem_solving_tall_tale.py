#!/usr/bin/env python3
"""
expert_problem_solving_tall_tale.py
===================================

A small, standalone Storyweavers world about a legendary expert who solves
impossible-looking problems with outsized tools, bright ideas, and a calm head.

This world stays in the tall-tale lane: the problem is concrete, the solution is
clever, and the ending proves what changed in the world.
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    heft: int = 1


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    type: str
    trouble: str
    clue: str
    requires: set[str] = field(default_factory=set)
    resolves_with: set[str] = field(default_factory=set)
    location: str = "the town square"


@dataclass
class Setting:
    name: str
    place: str
    details: str


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    tool: bool = False
    carried: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def tools(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.tool and e.owner == actor.id]


@dataclass
class StoryParams:
    setting: str
    problem: str
    expert_name: str
    expert_type: str
    helper_name: str
    helper_type: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "ridge_town": Setting(
        name="Ridge Town",
        place="the windy ridge above town",
        details="The street there curled like a ribbon under a blue sky.",
    ),
    "harbor": Setting(
        name="Blue Harbor",
        place="the dock by the water",
        details="The waves kept slapping the pilings like eager applause.",
    ),
    "canyon": Setting(
        name="Copper Canyon",
        place="the high ledge over the canyon",
        details="The wind whistled through the rocks like a tune on a penny flute.",
    ),
}

TOOLS = {
    "rope_lasso": Tool(
        id="rope_lasso",
        label="a long rope lasso",
        phrase="a long rope lasso with a bright knot",
        helps={"pull", "reach"},
        heft=2,
    ),
    "silver_wrench": Tool(
        id="silver_wrench",
        label="a silver wrench",
        phrase="a silver wrench that could loosen anything",
        helps={"loosen", "turn"},
        heft=1,
    ),
    "lantern_cart": Tool(
        id="lantern_cart",
        label="a lantern cart",
        phrase="a lantern cart with four steady wheels",
        helps={"light", "carry"},
        heft=3,
    ),
    "songhorn": Tool(
        id="songhorn",
        label="a songhorn",
        phrase="a brass songhorn",
        helps={"calm", "signal"},
        heft=1,
    ),
}

PROBLEMS = {
    "stuck_gate": Problem(
        id="stuck_gate",
        label="the stuck gate",
        phrase="a gate that would not budge",
        type="gate",
        trouble="the town could not get through",
        clue="the hinge was jammed with old rust",
        requires={"loosen"},
        resolves_with={"silver_wrench"},
        location="the town square",
    ),
    "fallen_bell": Problem(
        id="fallen_bell",
        label="the fallen bell",
        phrase="a bell hanging too low on the tower rope",
        type="bell",
        trouble="the bell could not ring for supper",
        clue="the rope had slipped loose in the wind",
        requires={"pull", "carry"},
        resolves_with={"rope_lasso", "lantern_cart"},
        location="the clock tower",
    ),
    "spooked_crowd": Problem(
        id="spooked_crowd",
        label="the spooked crowd",
        phrase="a crowd scared stiff by a rolling thunderhead",
        type="crowd",
        trouble="nobody would cross the bridge",
        clue="the dark cloud had made every shadow seem larger",
        requires={"calm", "signal"},
        resolves_with={"songhorn"},
        location="the bridge road",
    ),
}

EXPERT_TYPES = ["man", "woman"]
HELPER_TYPES = ["boy", "girl", "man", "woman"]

GREETINGS = [
    "folks called them an expert for the simple reason that they could untie a knot in the dark",
    "everybody knew their name because they could solve a pickle quicker than a cat can blink",
    "they had a mind sharp as a paper kite in a storm",
]

NAMES = ["Milo", "June", "Annie", "Bo", "Rose", "Wren", "Eli", "Sadie", "Tess", "Hank"]
HELPER_NAMES = ["Pip", "Nell", "Tom", "Dot", "Mae", "Zig", "Lia", "Jude", "Kit", "Bea"]

KNOWLEDGE = {
    "expert": [
        (
            "What is an expert?",
            "An expert is a person who knows a lot about one kind of work and can do it well.",
        )
    ],
    "rope": [
        (
            "What is a rope used for?",
            "A rope can help you pull, tie, lift, or hold things together.",
        )
    ],
    "wrench": [
        (
            "What does a wrench do?",
            "A wrench helps loosen or tighten things like bolts and nuts.",
        )
    ],
    "lantern": [
        (
            "What does a lantern give you?",
            "A lantern gives light so people can see in the dark.",
        )
    ],
    "horn": [
        (
            "What can a horn be used for?",
            "A horn can make a loud sound to call people or signal them from far away.",
        )
    ],
    "problem": [
        (
            "What is a problem?",
            "A problem is something that is hard, stuck, broken, or confusing and needs a solution.",
        )
    ],
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    expert = world.get(world.facts["expert"].id)
    problem = world.facts["problem"]
    tool = world.get(world.facts["tool"].id)
    if expert.meters.get("effort", 0) >= THRESHOLD and tool.id in problem.resolves_with:
        sig = ("progress", problem.id)
        if sig not in world.fired:
            world.fired.add(sig)
            problem_state = world.facts["problem_state"]
            if problem_state["trouble"] > 0:
                problem_state["trouble"] = 0
                problem_state["solved"] = True
                out.append(f"The trouble gave way at last.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    crowd = world.facts["problem"].type == "crowd"
    helper = world.facts["helper"]
    if crowd and helper.memes.get("confidence", 0) >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["problem_state"]["panic"] = 0
            out.append("The nervous chatter settled down.")
    return out


CAUSAL_RULES = [Rule("progress", _r_progress), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                produced.extend(s)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return bool(problem.resolves_with & {tool.id})


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world = World(setting)

    expert = world.add(Entity(
        id=params.expert_name,
        kind="character",
        type=params.expert_type,
        label="the expert",
        phrase="the famous expert",
        meters={"effort": 0.0},
        memes={"confidence": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="the helper",
        phrase="the little helper",
        meters={"effort": 0.0},
        memes={"confidence": 0.5},
    ))
    t = world.add(Entity(
        id=tool.id,
        kind="thing",
        type=tool.id,
        label=tool.label,
        phrase=tool.phrase,
        owner=expert.id,
        tool=True,
        carried=True,
    ))
    world.facts.update(
        expert=expert,
        helper=helper,
        tool=t,
        problem=problem,
        problem_state={"trouble": 1, "panic": 1 if problem.type == "crowd" else 0, "solved": False},
    )

    world.say(
        f"{expert.id} was the kind of expert {GREETINGS[0]}."
    )
    world.say(
        f"With {helper.id} at their side, {expert.id} carried {tool.label} everywhere, "
        f"just in case a hard problem came rolling by."
    )
    world.para()
    world.say(
        f"One day at {setting.place}, there was {problem.phrase}. "
        f"{problem.trouble.capitalize()}."
    )
    world.say(
        f"{problem.clue.capitalize()}, and the whole town waited to see what the expert would do."
    )
    world.para()

    if problem.type == "crowd":
        helper.memes["confidence"] += 1
        world.say(
            f"{helper.id} took a deep breath and helped point people the right way, "
            f"while {expert.id} raised {tool.label} high like a promise."
        )
    else:
        world.say(
            f"{expert.id} studied the problem, tapped {tool.label}, and set to work without a fuss."
        )

    expert.meters["effort"] += 1
    helper.meters["effort"] += 1
    propagate(world, narrate=False)

    if problem.type == "stuck_gate":
        world.say(
            f"First {expert.id} slipped the wrench to the rusty hinge and gave it a careful turn."
        )
        world.say(
            f"Then {helper.id} braced the gate while {expert.id} pulled, and the old wood groaned awake."
        )
    elif problem.type == "fallen_bell":
        world.say(
            f"{expert.id} looped the rope lasso around the bell rope, and {helper.id} held the lantern cart steady."
        )
        world.say(
            f"Together they lifted, guided, and eased the bell back where it belonged."
        )
    else:
        world.say(
            f"{expert.id} sounded the songhorn once, then twice, and the brave note rolled clear across the bridge road."
        )
        world.say(
            f"The crowd heard the tune, found their courage, and crossed behind the helper's waving hands."
        )

    expert.meters["effort"] += 1
    helper.meters["effort"] += 1
    if problem.type == "crowd":
        helper.memes["confidence"] += 1
    propagate(world, narrate=True)

    if world.facts["problem_state"]["solved"]:
        world.say(
            f"By sunset, {problem.label} was no trouble at all. {setting.details} "
            f"And the expert went home with {helper.id}, carrying {tool.label} like it was the easiest thing in the world."
        )
    else:
        world.say(
            f"By sunset, the problem was smaller, steadier, and ready for another try tomorrow."
        )

    return world


def prompt_lines(world: World) -> list[str]:
    p = world.facts["problem"]
    tool = world.facts["tool"]
    expert = world.facts["expert"]
    helper = world.facts["helper"]
    return [
        f"Write a tall-tale story about an expert named {expert.id} who solves {p.label} with {tool.label}.",
        f"Tell a child-friendly problem-solving tale where {helper.id} helps {expert.id} and the trouble at {p.location} gets fixed.",
        f"Write a short tall tale using the word 'expert' and ending with a clear solution to {p.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["problem"]
    expert = world.facts["expert"]
    helper = world.facts["helper"]
    tool = world.facts["tool"]
    state = world.facts["problem_state"]
    qa = [
        QAItem(
            question=f"Who was the expert in the story?",
            answer=f"The expert was {expert.id}, the one everybody trusted to solve hard problems.",
        ),
        QAItem(
            question=f"What problem did {expert.id} have to solve?",
            answer=f"{expert.id} had to solve {p.phrase} at {p.location}.",
        ),
        QAItem(
            question=f"Which tool helped {expert.id} work on the problem?",
            answer=f"{tool.label} helped {expert.id}, and {helper.id} helped keep things steady while the work got done.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"The trouble was solved, so the town could move on again. "
                f"{helper.id} and {expert.id} went home with {tool.label}, and the ending showed the problem had been fixed."
            ),
        ),
    ]
    if state["panic"]:
        qa.append(
            QAItem(
                question=f"Why did the crowd calm down?",
                answer=f"The crowd calmed down because {expert.id} used {tool.label} and {helper.id} helped guide everyone safely.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    tags = {"expert", "problem"}
    p = world.facts["problem"]
    if "rope" in p.resolves_with:
        tags.add("rope")
    if "wrench" in world.facts["tool"].label:
        tags.add("wrench")
    if "lantern" in world.facts["tool"].label:
        tags.add("lantern")
    if "horn" in world.facts["tool"].label:
        tags.add("horn")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def generation_prompts(world: World) -> list[str]:
    return prompt_lines(world)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tool:
            bits.append("tool=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    lines.append(f"  problem_state: {world.facts['problem_state']}")
    return "\n".join(lines)


CURATED = [
    StoryParams("ridge_town", "stuck_gate", "Milo", "man", "Pip", "boy", "silver_wrench"),
    StoryParams("harbor", "fallen_bell", "June", "woman", "Nell", "girl", "rope_lasso"),
    StoryParams("canyon", "spooked_crowd", "Annie", "woman", "Tom", "boy", "songhorn"),
]


ASP_RULES = r"""
problem_fix(P, T) :- problem(P), tool(T), resolves_with(P, T).
valid_story(S, P, T) :- setting(S), problem(P), tool(T), problem_fix(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.resolves_with):
            lines.append(asp.fact("resolves_with", pid, t))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (s, p, t)
        for s in SETTINGS
        for p, prob in PROBLEMS.items()
        for t in TOOLS
        if reasonableness_gate(prob, TOOLS[t])
    }
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about expert problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--expert-name")
    ap.add_argument("--expert-type", choices=EXPERT_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.problem and args.tool:
        if not reasonableness_gate(PROBLEMS[args.problem], TOOLS[args.tool]):
            raise StoryError("That tool cannot honestly solve that problem in this tall tale.")
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    tool_choices = [t for t, tool in TOOLS.items() if reasonableness_gate(PROBLEMS[problem], tool)]
    if args.tool:
        if args.tool not in tool_choices:
            raise StoryError("That tool does not fit this problem.")
        tool = args.tool
    else:
        tool = rng.choice(tool_choices)
    expert_type = args.expert_type or rng.choice(EXPERT_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    expert_name = args.expert_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if helper_name == expert_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != expert_name])
    return StoryParams(setting, problem, expert_name, expert_type, helper_name, helper_type, tool)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (setting, problem, tool) stories:\n")
        for s, p, t in stories:
            print(f"  {s:12} {p:12} {t}")
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
            header = f"### {p.expert_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
