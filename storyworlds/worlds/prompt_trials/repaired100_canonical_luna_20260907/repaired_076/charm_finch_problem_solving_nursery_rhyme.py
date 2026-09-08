#!/usr/bin/env python3
"""A child-facing nursery-rhyme StoryWorld about a finch solving a problem with a charm."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Pip"
    setting: str = "the moonlit garden"
    charm: str = "a silver bell charm"
    problem: str = "a tangled ribbon blocked the nest path"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


PROBLEMS = (
    {
        "key": "tangled_ribbon",
        "problem": "a scarlet ribbon tangled across the narrow nest path",
        "clue": "one loose end fluttered beside a low branch",
        "bad": "pull hard until the branch snapped",
        "action": "studied the knot, held the branch steady, and teased the ribbon loose from the outside loop",
        "result": "the ribbon slid free without harming the branch",
        "ending": "The scarlet ribbon rested in a basket, and the nest path shone clear beneath the moon.",
        "lesson": "careful looking can turn a snarl into a simple plan",
    },
    {
        "key": "missing_seed",
        "problem": "the last sunflower seed rolled beneath a heavy stone",
        "clue": "a line of tiny crumbs marked the stone's downhill edge",
        "bad": "peck at the stone until your beak hurt",
        "action": "followed the crumb trail, found a twig, and used it as a lever with the helper",
        "result": "the stone tipped gently and the seed rolled into the waiting cup",
        "ending": "The seed cup brimmed beside the flowers while the little twig lay neatly on the path.",
        "lesson": "a clue and a small tool can make a big obstacle manageable",
    },
    {
        "key": "silent_charm",
        "problem": "the silver bell charm made no sound on the dark garden gate",
        "clue": "its loop had slipped behind a wooden peg",
        "bad": "shake the charm faster and louder",
        "action": "looked behind the peg, lifted the loop, and checked the clasp before trying again",
        "result": "the charm rang clearly when the gate opened",
        "ending": "Ting-a-ling went the silver charm as the gate swung wide for every bird.",
        "lesson": "checking how a thing works is wiser than simply trying harder",
    },
)
TITLES = ("The Careful Little Finch", "The Riddle of the Garden Path", "The Charm That Rang Again")
OPENINGS = (
    "Dawn wore a pink ribbon over {setting}, and {name} the finch woke with a hop.",
    "Tweet-tweet, tap-tap, the garden stirred while {name} fluttered beneath the brightening sky.",
    "In a nursery-rhyme morning, {name} carried {charm} past the flowers.",
)
REFRAINS = (
    "Look, listen, think, then try; a clever plan can reach the sky.",
    "Not by hurry, not by might, but by a clue we make things right.",
    "First we notice, then we know; step by step the answer grows.",
)


def build_world(params: StoryParams) -> World:
    world = World(params)
    bird = world.add(Entity(params.name, "finch", params.name, {"flight": 0.8, "calm": 0.5}, {"curiosity": 0.8, "confidence": 0.6}))
    helper = world.add(Entity(params.helper, "helper", params.helper, {"helpfulness": 0.9}, {"patience": 0.9}))
    charm = world.add(Entity("charm", "charm", params.charm, {"sound": 0.8}, {"hope": 0.8}, bird.id))
    world.facts.update(bird=bird.id, helper=helper.id, charm=charm.label)
    return world


def choose_problem(params: StoryParams) -> dict[str, str]:
    return PROBLEMS[params.variant % len(PROBLEMS)]


def simulate(world: World) -> World:
    p = world.params
    case = choose_problem(p)
    bird = world.entities[p.name]
    helper = world.entities[p.helper]
    world.say(random.Random(p.variant + 41).choice(OPENINGS).format(setting=p.setting, name=p.name, charm=p.charm))
    world.say(f"{p.name} was a bright little finch who loved solving puzzles, and {p.charm} bobbed cheerfully beside {bird.label}.")
    world.say(f"{helper.label} was nearby, carrying a basket and watching with patient eyes.")
    world.say(f"Then {case['problem']}.")
    world.para()
    world.say(f"{p.name} did not flap in a fuss. The important clue was that {case['clue']}.")
    world.say(random.Random(p.variant + 73).choice(REFRAINS))
    world.say(f"It would not help to {case['bad']}.")
    world.para()
    world.say(f'"What do you notice?" asked {helper.label}.')
    world.say(f'"The clue tells us where to begin," chirped {p.name}.')
    world.say(f'Together, they {case["action"]}.')
    world.say(f'"Aha!" sang {p.name}. "The careful way worked."')
    world.say(f"Because they used the clue, {case['result']}.")
    world.say(f"{case['ending']} {p.name} fluttered in a happy circle, and {p.charm} gave one bright ring.")
    world.say(f"The little finch learned that {case['lesson']}.")
    world.fired.update({"noticed_clue", "asked_helper", "tested_plan", "solved_problem"})
    bird.memes.update(confidence=1.0, joy=1.0)
    world.facts.update(
        problem=case["problem"],
        clue=case["clue"],
        rejected=case["bad"],
        action=case["action"],
        result=case["result"],
        lesson=case["lesson"],
        solved=True,
        used_clue=True,
        charm_used=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    case = choose_problem(p)
    return [
        f"Write a nursery rhyme about {p.name} the finch solving a problem with {p.charm}.",
        f"Tell a child-friendly problem-solving story where the clue is that {case['clue']}.",
        f"Write a rhyming garden tale with dialogue, a careful solution, and the ending image: {case['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    case = choose_problem(p)
    return [
        QAItem(f"What problem did {p.name} face?", f"{p.name} faced {case['problem']}."),
        QAItem("What clue did the finch notice?", f"The finch noticed that {case['clue']}."),
        QAItem("What did the finch and helper do?", f"Together, they {case['action']}."),
        QAItem("Why did they reject the hurried idea?", f"They rejected trying to {case['bad']} because hurry could cause harm and would ignore the clue."),
        QAItem("How do we know the problem was solved?", f"{case['result']}. {case['ending']}"),
        QAItem("What lesson did the finch learn?", f"The finch learned that {case['lesson']}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a charm?", "A charm is a small object kept or worn for decoration, meaning, or a pleasant sound."),
        QAItem("What is a finch?", "A finch is a small songbird with a short beak that often eats seeds."),
        QAItem("What is problem solving?", "Problem solving means noticing what is wrong, finding useful clues, making a safe plan, and checking whether the plan worked."),
        QAItem("Why should someone ask for help?", "A helper can notice another clue, suggest a safer plan, or assist with a task that is difficult alone."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """finch(X) :- bird(X).
solved(X) :- finch(X), noticed_clue(X), asked_helper(X), tested_plan(X).
safe_solution(X) :- solved(X), used_clue(X), charm_used(X).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp
    name = (params or StoryParams()).name.lower()
    return "\n".join(
        asp.fact(predicate, name)
        for predicate in ("bird", "finch", "noticed_clue", "asked_helper", "tested_plan", "used_clue", "charm_used")
    )


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_solution/1."))
    found = bool(asp.atoms(model, "safe_solution"))
    sample = generate(StoryParams(variant=2))
    ok = found and sample.world is not None and sample.world.facts.get("solved") is True
    print("OK: ASP and Python both confirm the clue-based charm solution." if ok else "ASP verification failed.")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme finch problem-solving StoryWorld.")
    parser.add_argument("--name", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--setting", default=None)
    parser.add_argument("--charm", default=None)
    parser.add_argument("--problem", choices=tuple(case["key"] for case in PROBLEMS), default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problems = {case["key"]: case for case in PROBLEMS}
    key = args.problem or rng.choice(tuple(problems))
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(("Luna", "Pip", "Mira", "Tansy")),
        helper=args.helper or rng.choice(("Pip", "Robin", "Nell")),
        setting=args.setting or rng.choice(("the moonlit garden", "the clover yard", "the singing orchard")),
        charm=args.charm or rng.choice(("a silver bell charm", "a blue bead charm", "a tiny gold charm")),
        problem=problems[key]["problem"],
        variant=rng.randrange(1, 2**31),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.name or not params.helper:
        raise StoryError("A finch and a helper need names before the story can begin.")
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_solution/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = []
        for index in range(len(PROBLEMS)):
            case = PROBLEMS[index]
            samples.append(generate(StoryParams(problem=case["problem"], variant=index + 10)))
    else:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(args.n)]
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_solution/1.", samples[0].params))
        print("ASP:", ", ".join(str(atom) for atom in model))
        return
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
