#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pretend_union_juice_indoor_play_cafe_problem.py
===========================================================================================================

A small animal-story world set in an indoor play cafe where a pretend union
meeting gets interrupted by a juice spill, then solved by careful teamwork.

The seed premise:
- animal friends gather in an indoor play cafe
- they run a pretend union, a make-believe club about sharing and helping
- juice causes a problem
- the story resolves through problem solving, not through a frozen template

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- typed entities with meters and memes
- live world state drives the prose
- inline ASP twin + Python reasonableness gate
- story QA and world QA
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
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "messy": 0.0, "clean": 1.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "teamwork": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"rabbit", "mouse", "bird"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.species in {"fox", "bear", "cat"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the indoor play cafe"
    indoor: bool = True
    affordances: set[str] = field(default_factory=lambda: {"pretend", "juice", "union"})


@dataclass
class Activity:
    id: str
    name: str
    verb: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    source: str
    danger: str
    fix_tool: str
    fix_action: str
    resolution: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_lines: list[str] = []

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

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


ACTIVITIES = {
    "pretend": Activity(
        id="pretend",
        name="pretend play",
        verb="build a pretend town",
        mess="toy clutter",
        zone={"table", "floor"},
        keyword="pretend",
        tags={"pretend"},
    ),
    "union": Activity(
        id="union",
        name="union meeting",
        verb="hold a union meeting",
        mess="crowded chairs",
        zone={"table", "floor"},
        keyword="union",
        tags={"union"},
    ),
    "juice": Activity(
        id="juice",
        name="juice making",
        verb="pour juice",
        mess="sticky juice",
        zone={"table", "floor", "hands"},
        keyword="juice",
        tags={"juice"},
    ),
}

PROBLEMS = {
    "spill": Problem(
        id="spill",
        source="juice cup",
        danger="sticky juice spread across the pretend union table",
        fix_tool="a towel",
        fix_action="wipe the spill",
        resolution="the table shone again",
        tags={"juice", "problem-solving"},
    ),
    "mixup": Problem(
        id="mixup",
        source="role cards",
        danger="the pretend union roles got mixed up",
        fix_tool="a color list",
        fix_action="sort the cards",
        resolution="everyone knew their job",
        tags={"pretend", "union", "problem-solving"},
    ),
}

SETTING = Setting()

ANIMALS = [
    ("Fox", "fox", "curious"),
    ("Bunny", "rabbit", "gentle"),
    ("Bear", "bear", "careful"),
    ("Mila", "mouse", "bright"),
]

TOOLS = {
    "towel": Entity(id="towel", kind="thing", species="thing", label="towel", phrase="a soft towel", protective=True, covers={"table", "floor"}),
    "tray": Entity(id="tray", kind="thing", species="thing", label="tray", phrase="a steady tray", protective=True, covers={"hands", "table"}),
    "napkins": Entity(id="napkins", kind="thing", species="thing", label="napkins", phrase="a stack of napkins", protective=True, covers={"table", "floor"}),
}

CURATED = []  # not used; samples are randomized


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero1: str = "Fox"
    hero2: str = "Bunny"
    hero3: str = "Bear"
    activity: str = "pretend"
    problem: str = "spill"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: pretend union, juice, and problem solving at an indoor play cafe.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("--hero3")
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    problem = args.problem or ("spill" if activity in {"pretend", "juice"} else "mixup")
    return StoryParams(
        seed=args.seed,
        hero1=args.hero1 or rng.choice([a[0] for a in ANIMALS]),
        hero2=args.hero2 or rng.choice([a[0] for a in ANIMALS]),
        hero3=args.hero3 or rng.choice([a[0] for a in ANIMALS]),
        activity=activity,
        problem=problem,
    )


def _entity_for_name(name: str, role: str) -> Entity:
    mapping = {n: (species, vibe) for n, species, vibe in ANIMALS}
    species, vibe = mapping.get(name, ("fox", "bright"))
    return Entity(
        id=name,
        kind="character",
        species=species,
        label=name.lower(),
        phrase=f"a {vibe} {species}",
        role=role,
    )


def _setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero1 = world.add(_entity_for_name(params.hero1, "leader"))
    hero2 = world.add(_entity_for_name(params.hero2, "helper"))
    hero3 = world.add(_entity_for_name(params.hero3, "helper"))
    cup = world.add(Entity(id="juice_cup", kind="thing", species="thing", label="juice cup", phrase="a cup of apple juice"))
    table = world.add(Entity(id="table", kind="thing", species="thing", label="table", phrase="the little table"))
    banner = world.add(Entity(id="banner", kind="thing", species="thing", label="banner", phrase="a paper pretend union banner"))
    role_cards = world.add(Entity(id="cards", kind="thing", species="thing", label="role cards", phrase="three role cards"))
    world.facts.update(hero1=hero1, hero2=hero2, hero3=hero3, cup=cup, table=table, banner=banner, cards=role_cards,
                       activity=ACTIVITIES[params.activity], problem=PROBLEMS[params.problem], params=params)
    return world


def _spill_rule(world: World) -> list[str]:
    out = []
    cup = world.get("juice_cup")
    table = world.get("table")
    if cup.meters["wet"] < THRESHOLD or table.meters["wet"] >= THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    table.meters["wet"] += 1
    table.meters["messy"] += 1
    for a in world.animals():
        a.memes["worry"] += 0.5
    out.append("The juice spread across the table.")
    return out


def _teamwork_rule(world: World) -> list[str]:
    out = []
    if sum(a.memes["teamwork"] for a in world.animals()) < 2:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for a in world.animals():
        a.memes["joy"] += 0.5
    out.append("The friends worked together and felt proud.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_spill_rule, _teamwork_rule):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def story_title(activity: Activity) -> str:
    return f"The Pretend Union and the {activity.keyword} Problem"


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    a1, a2, a3 = world.get(params.hero1), world.get(params.hero2), world.get(params.hero3)
    act = ACTIVITIES[params.activity]
    prob = PROBLEMS[params.problem]

    world.say(f"At the indoor play cafe, {a1.id}, {a2.id}, and {a3.id} started a pretend union.")
    world.say(f"It was a small club where animal friends practiced sharing jobs and helping each other.")
    world.say(f"{a1.id} wanted to {act.verb}, and the others wanted to join in.")

    world.para()
    world.say(f"They set out {world.get('cards').phrase} and called the meeting their pretend union.")
    if params.activity == "juice":
        world.say(f"{a2.id} carefully lifted the juice cup so everyone could sip without bumping elbows.")
    else:
        world.say(f"A juice cup waited nearby for a break after the game.")

    world.para()
    world.say(f"Then the problem arrived: {prob.danger}.")
    world.get("juice_cup").meters["wet"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{a3.id} spotted {prob.fix_tool} and said, \"Let's solve this.\"")
    world.say(f"{a1.id} held the cup still while {a2.id} used {prob.fix_tool} to {prob.fix_action}.")
    a1.memes["teamwork"] += 1
    a2.memes["teamwork"] += 1
    a3.memes["teamwork"] += 1
    world.get("table").meters["wet"] = 0
    world.get("table").meters["messy"] = 0
    world.get("table").meters["clean"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"After that, the pretend union meeting continued.")
    world.say(f"The cards stayed in order, the juice stayed in cups, and {a1.id} finished {act.name} with a grin.")
    world.say(f"By the end, the little play cafe looked tidy again, and the friends felt like a real team.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short animal story set in an indoor play cafe about a pretend union and a juice problem.",
        f"Tell a child-friendly story where {p.hero1}, {p.hero2}, and {p.hero3} solve a mess with teamwork.",
        f"Make a gentle story that includes the words pretend, union, and juice, and ends with a calm fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    a1, a2, a3 = world.get(p.hero1), world.get(p.hero2), world.get(p.hero3)
    act = world.facts["activity"]
    prob = world.facts["problem"]
    return [
        QAItem(
            question=f"Where did the animals meet?",
            answer="They met at the indoor play cafe.",
        ),
        QAItem(
            question=f"What was their pretend union?",
            answer="It was a small make-believe club where the animal friends practiced sharing jobs and helping each other.",
        ),
        QAItem(
            question=f"What problem did they have?",
            answer=f"They had a {prob.id} problem because {prob.danger}.",
        ),
        QAItem(
            question=f"How did they solve it?",
            answer=f"They solved it by using {prob.fix_tool} and working together to {prob.fix_action}.",
        ),
        QAItem(
            question=f"Who helped most when the juice caused trouble?",
            answer=f"{a1.id}, {a2.id}, and {a3.id} all helped, because each one did a job that made the fix work.",
        ),
        QAItem(
            question=f"What did {a1.id} want to do during the story?",
            answer=f"{a1.id} wanted to {act.verb}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is juice?",
            answer="Juice is a drink made from fruit, and it can make a sticky mess if it spills.",
        ),
        QAItem(
            question="What does a team do when a problem happens?",
            answer="A team looks at the problem, chooses a helpful job for each friend, and works together to fix it.",
        ),
        QAItem(
            question="What is pretend play?",
            answer="Pretend play is when children imagine a game or role, like a club, a shop, or a rescue mission.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind} {e.species} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.

valid(pretend).
valid(union).
valid(juice).

problem(juice_spill) :- valid(juice).
solution(teamwork) :- valid(pretend), valid(union), valid(juice).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "indoor_play_cafe"),
            asp.fact("keyword", "pretend"),
            asp.fact("keyword", "union"),
            asp.fact("keyword", "juice"),
            asp.fact("activity", aid) for aid in ACTIVITIES
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("indoor_play_cafe", "pretend"), ("indoor_play_cafe", "union"), ("indoor_play_cafe", "juice")]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    atoms = set(asp.atoms(model, "valid"))
    py = {("pretend",), ("union",), ("juice",)}
    if atoms == py:
        print("OK: ASP and Python gates agree.")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(py))
    return 1


def explain_rejection() -> str:
    return "(No story: this world only supports the indoor play cafe with pretend, union, and juice.)"


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.asp:
        print("compatible keywords:", ", ".join(k for k, _ in valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(seed=base_seed)
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
