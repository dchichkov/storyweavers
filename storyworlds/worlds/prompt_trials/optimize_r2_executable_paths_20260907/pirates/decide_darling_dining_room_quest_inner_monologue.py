#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

@dataclass
class Path:
    id: str
    problem: str
    clue: str
    actions: tuple[str, ...]
    changes: tuple[str, ...]
    ending: str
    tool: str
    risk: str
    helper: str

@dataclass
class StoryParams:
    quest: str
    problem: str
    solution: str
    hero: str
    friend: str
    helper: str
    seed: int | None = None

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    scenes: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.scenes.append(text)

    def render(self) -> str:
        return "\n\n".join(self.scenes)

PATHS = {
    "lost_key": {
        "bucket": Path(
            "lost_key", "the brass dining-room key was missing",
            "a crumb trail beneath the table",
            ("search under the table", "follow the crumbs", "lift the tablecloth"),
            ("the clue is found", "the key is recovered", "the quest succeeds"),
            "The key shone in the candlelight, and the locked recipe box opened.",
            "a wooden spoon", "a wobbling chair", "Grandma",
        ),
        "lantern": Path(
            "lost_key", "the brass dining-room key was missing",
            "a faint glint beneath the sideboard",
            ("dim the lamps", "look for the glint", "slide a serving tray underneath"),
            ("the hidden glint is noticed", "the key is safely lifted", "the quest succeeds"),
            "The tray carried the key out, and everyone cheered when the recipe box opened.",
            "a silver serving tray", "a dark corner", "Grandma",
        ),
    },
    "spilled_stars": {
        "bucket": Path(
            "spilled_stars", "a jar of paper stars had spilled across the floor",
            "the stars were caught beneath the long table",
            ("kneel beside the table", "sort the stars by color", "use a napkin as a scoop"),
            ("the stars are gathered", "the colors are sorted", "the decoration is restored"),
            "The paper stars twinkled around the birthday cake like a tiny sky.",
            "a folded napkin", "a rolling chair", "Aunt Rose",
        ),
        "lantern": Path(
            "spilled_stars", "a jar of paper stars had spilled across the floor",
            "the stars had scattered into the shadows",
            ("turn on a hand lamp", "shine it beneath the chairs", "sweep the stars into a bowl"),
            ("the shadows are searched", "every star is found", "the decoration is restored"),
            "The bowl of stars became a bright centerpiece for the birthday table.",
            "a hand lamp", "a shadowy corner", "Aunt Rose",
        ),
    },
    "missing_invitation": {
        "bucket": Path(
            "missing_invitation", "the invitation to the neighbors was missing",
            "a blue corner peeked from the table runner",
            ("check the table runner", "ask who last carried the cards", "pull the runner gently"),
            ("the hiding place is known", "the invitation is recovered", "the quest succeeds"),
            "The invitation was saved, and the neighbors arrived smiling.",
            "a gentle tug", "a table runner that could slip", "Dad",
        ),
        "lantern": Path(
            "missing_invitation", "the invitation to the neighbors was missing",
            "a blue corner showed beside the china cabinet",
            ("look beside the cabinet", "hold the plates steady", "reach with kitchen tongs"),
            ("the clue is confirmed", "the invitation is recovered", "the quest succeeds"),
            "The tongs carried the invitation free, ready for one more welcoming table.",
            "kitchen tongs", "a stack of china", "Dad",
        ),
    },
}

QUESTS = {
    "lost_key": "open the old recipe box before supper",
    "spilled_stars": "decorate the dining room before the birthday guests arrive",
    "missing_invitation": "find the last invitation before the neighbors come",
}

HEROES = ["Mia", "Lily", "Nora", "Ella"]
FRIENDS = ["Ben", "Sam", "Theo", "Owen"]
HELPERS = ["Grandma", "Aunt Rose", "Dad"]

OPENINGS = [
    "In the warm dining room, {hero} and {friend} began a little quest.",
    "The dining room smelled of cinnamon when {hero} discovered a puzzling problem.",
    "Sunlight rested on the dining-room table as {hero} and {friend} prepared for an important quest.",
]
INNER = [
    "{hero} thought, *I must decide carefully, darling. A rushed choice could make the problem worse.*",
    "{hero} wondered, *Which clue should I trust? I can decide, darling, if I stay calm.*",
    "{hero} told themself, *This feels suspenseful, darling, but a kind plan can carry us through.*",
]
DIALOGUE = [
    '"Should we hurry?" asked {friend}. "{hero}, what do you decide?"',
    '"I am worried," said {friend}. "{hero}, can we solve it together?"',
    '"The dining room feels full of suspense," whispered {friend}. "Tell me your plan."',
]

def validate(params: StoryParams) -> Path:
    if params.problem not in PATHS or params.solution not in PATHS[params.problem]:
        raise StoryError("That problem and solution do not form a supported dining-room quest path.")
    if params.hero == params.friend:
        raise StoryError("The quest needs two different children.")
    return PATHS[params.problem][params.solution]

def build_world(params: StoryParams, rng: random.Random) -> World:
    path = validate(params)
    world = World()
    hero = world.add(Entity(params.hero, "character", params.hero))
    friend = world.add(Entity(params.friend, "character", params.friend))
    helper = world.add(Entity("helper", "character", params.helper))
    table = world.add(Entity("dining_table", "object", "the dining table"))
    hero.memes["courage"] += 1
    friend.memes["care"] += 1
    table.meters["importance"] += 1
    world.facts.update(path=path, hero=hero, friend=friend, helper=helper)
    world.say(rng.choice(OPENINGS).format(hero=params.hero, friend=params.friend))
    world.say(f'"Our quest is to {QUESTS[params.problem]}," said {params.hero}.')
    world.say(path.problem.capitalize() + ".")
    world.say(rng.choice(INNER).format(hero=params.hero))
    world.say(rng.choice(DIALOGUE).format(hero=params.hero, friend=params.friend))
    world.say(
        f'"I decide we should use {path.clue}. We will move gently and ask {params.helper} '
        f'for help if we need it," said {params.hero}.'
    )
    world.say(
        f'{params.hero} and {params.friend} first {path.actions[0]}, then they {path.actions[1]}. '
        f'The suspense grew when they found {path.risk}.'
    )
    world.say(
        f'"I see it!" cried {params.friend}. "{params.hero}, do the careful next step." '
        f'"Together," said {params.hero}.'
    )
    world.say(
        f'They {path.actions[2]}. Because they had learned {path.clue}, '
        f'{path.changes[0]} and {path.changes[1]}.'
    )
    world.say(
        f'{params.helper} joined them. "You made a thoughtful decision," {params.helper} said. '
        f'"A quest is easier when brave friends share the work."'
    )
    world.say(f'{path.ending} {params.hero} felt the warm glow of a kind decision.')
    world.facts["solved"] = True
    world.facts["clue"] = path.clue
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Path = f["path"]
    hero = f["hero"].id
    friend = f["friend"].id
    return [
        f"Write a heartwarming dining-room Quest where {hero} must decide how to solve {p.problem}.",
        f"Include an Inner Monologue in which {hero} thinks carefully before choosing {p.tool}.",
        f"Build Suspense as {hero} and {friend} face {p.risk}, then end with {p.ending}",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: Path = f["path"]
    hero, friend, helper = f["hero"].id, f["friend"].id, f["helper"].id
    return [
        QAItem(
            "What quest did the children undertake?",
            f"{hero} and {friend} worked in the dining room to {QUESTS[next(k for k,v in QUESTS.items() if v == QUESTS.get(world.facts['path'].id, ''))]}."
            if False else f"{hero} and {friend} tried to {QUESTS[world.facts['path'].id]}."
        ),
        QAItem(
            "What clue helped them decide what to do?",
            f"They used {p.clue}, which pointed them toward a careful solution."
        ),
        QAItem(
            "How did the children solve the problem?",
            f"{hero} and {friend} followed the path of {p.actions[0]}, {p.actions[1]}, and {p.actions[2]}; this led to the successful change that {p.changes[1]}."
        ),
        QAItem(
            "Why was the ending heartwarming?",
            f"{helper} praised their thoughtful decision, and the children completed the quest by helping one another."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("Why should people move carefully around a dining table?", "Careful movements protect dishes, people, and clues from being knocked over."),
        QAItem("What is an inner monologue?", "An inner monologue is a character's private thought, showing what the character is considering."),
        QAItem("How can suspense help a story?", "Suspense makes readers wonder what will happen next before the problem is solved."),
    ]

def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = build_world(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Heartwarming dining-room quest storyworld.")
    p.add_argument("--quest", choices=QUESTS)
    p.add_argument("--problem", choices=PATHS)
    p.add_argument("--solution", choices=["bucket", "lantern"])
    p.add_argument("--hero")
    p.add_argument("--friend")
    p.add_argument("--helper", choices=HELPERS)
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--seed", type=int)
    p.add_argument("--all", action="store_true")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--asp", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--show-asp", action="store_true")
    return p

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problem = args.problem or args.quest or rng.choice(list(PATHS))
    solution = args.solution or rng.choice(["bucket", "lantern"])
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice([x for x in FRIENDS if x != hero])
    helper = args.helper or rng.choice(HELPERS)
    params = StoryParams(problem, problem, solution, hero, friend, helper)
    validate(params)
    return params

ASP_RULES = """
hazard(lost_key,bucket). hazard(lost_key,lantern).
hazard(spilled_stars,bucket). hazard(spilled_stars,lantern).
hazard(missing_invitation,bucket). hazard(missing_invitation,lantern).
solves(P,S) :- hazard(P,S).
"""

def asp_facts() -> str:
    return "\n".join(f"problem({p}). solution({s})." for p in PATHS for s in PATHS[p])

def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES

def verify() -> int:
    for problem, options in PATHS.items():
        for solution, path in options.items():
            params = StoryParams(problem, problem, solution, "Mia", "Ben", "Grandma", 1)
            sample = generate(params)
            if path.ending not in sample.story or "decide" not in sample.story or "darling" not in sample.story:
                return 1
            if '"' not in sample.story:
                return 1
    return 0

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = dict(e.meters)
        memes = dict(e.memes)
        lines.append(f"{e.id}: meters={meters}, memes={memes}")
    lines.append(f"facts={list(world.facts)}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("\n== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("\n== World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)

def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        print(asp_program())
        return
    rng = random.Random(args.seed)
    samples = []
    if args.all:
        for problem in PATHS:
            for solution in PATHS[problem]:
                samples.append(generate(StoryParams(problem, problem, solution, "Mia", "Ben", "Grandma", args.seed)))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = rng.randrange(2**31)
            samples.append(generate(params))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) != 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 60 + "\n")
        emit(sample, args.trace, args.qa)

if __name__ == "__main__":
    main()
