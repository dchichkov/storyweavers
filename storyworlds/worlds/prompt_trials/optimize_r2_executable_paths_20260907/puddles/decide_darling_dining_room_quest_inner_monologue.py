#!/usr/bin/env python3
"""A small dining-room quest about deciding what to do with a darling gift.

The child must choose how to protect a treasured paper lantern before a lively
indoor game. The inner monologue carries suspense, while spoken exchanges let
the child and a helper share clues and change the plan.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meter(key) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Path:
    problem: str
    clue: str
    actions: tuple[str, ...]
    changes: tuple[str, ...]
    ending: str


PATHS = {
    "wobbling_candle": Path(
        problem="A candle on the dining table made the lantern's paper tail wobble close to the flame.",
        clue="The child noticed the warm air lifting the tail.",
        actions=("notice", "move_candle", "hang_lantern"),
        changes=("risk_removed", "lantern_safe"),
        ending="The lantern glowed above the table while the candle flickered safely below.",
    ),
    "spilled_punch": Path(
        problem="A cup of berry punch stood beside the darling lantern, and one careless elbow could spill it.",
        clue="The child saw a purple drop trembling on the cup's rim.",
        actions=("notice", "move_punch", "hang_lantern"),
        changes=("spill_risk_removed", "lantern_safe"),
        ending="The lantern shone over a clear table, and the punch waited safely at the far end.",
    ),
    "missing_hook": Path(
        problem="The lantern was ready for the quest, but its little hanging hook was missing.",
        clue="A bright thread under the napkin showed where the hook had fallen.",
        actions=("search", "find_hook", "hang_lantern"),
        changes=("hook_found", "lantern_safe"),
        ending="The lantern hung proudly above the chairs, its paper stars turning in the gentle air.",
    ),
    "crowded_table": Path(
        problem="The dining table was crowded with plates, so the darling lantern had no safe place to rest.",
        clue="The child remembered the empty sideboard beside the window.",
        actions=("notice", "clear_sideboard", "hang_lantern"),
        changes=("safe_space_made", "lantern_safe"),
        ending="The lantern watched over the dinner table from the quiet sideboard.",
    ),
}

SOLUTIONS = {
    "wobbling_candle": ("move_candle", "hang_lantern"),
    "spilled_punch": ("move_punch", "hang_lantern"),
    "missing_hook": ("find_hook", "hang_lantern"),
    "crowded_table": ("clear_sideboard", "hang_lantern"),
}

SETTINGS = {"dining_room": "the dining room"}
CHILDREN = ["Mira", "Nina", "Owen", "Theo", "Luca", "Ivy"]
HELPERS = ["Mom", "Dad", "Aunt Rose"]
MOODS = ["hopeful", "careful", "curious", "brave"]
OPENINGS = [
    "The dining room was warm with evening light.",
    "The long table gleamed beneath the dining room window.",
    "After supper, the dining room became a little adventure room.",
    "Golden light rested on every plate and spoon in the dining room.",
]


@dataclass
class StoryParams:
    problem: str
    solution: str
    name: str
    helper: str
    mood: str
    seed: Optional[int] = None


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str
    actor: str
    target: str


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, text: str, cause: str, result: str,
               actor: str, target: str) -> None:
        self.history.append(Event(kind, text, cause, result, actor, target))
        self.say(text)
        self.turn += 1

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def validate_params(params: StoryParams) -> None:
    if params.problem not in PATHS:
        raise StoryError("That dining-room problem is not supported.")
    if params.solution not in SOLUTIONS[params.problem]:
        raise StoryError("That solution does not fit the chosen problem.")
    if not params.name.strip() or not params.helper.strip():
        raise StoryError("The child and helper need names.")
    if params.name in {"lantern", "candle", "punch", "hook", "sideboard"}:
        raise StoryError("The child's name collides with a story object.")


def build_world(params: StoryParams, rng: random.Random) -> World:
    validate_params(params)
    path = PATHS[params.problem]
    world = World(params)
    child = world.add(Entity(params.name, "character", params.name))
    helper = world.add(Entity(params.helper, "character", params.helper))
    lantern = world.add(Entity(
        "lantern", "object", "lantern",
        "a darling paper lantern covered in tiny gold stars",
        owner=child.id,
    ))
    world.add(Entity("candle", "object", "candle", "a little candle"))
    world.add(Entity("punch", "object", "punch", "a cup of berry punch"))
    world.add(Entity("hook", "object", "hook", "a small brass hook"))
    world.add(Entity("sideboard", "object", "sideboard", "the empty sideboard"))
    world.facts.update(
        child=child,
        helper=helper,
        lantern=lantern,
        path=path,
        solved=False,
        inner_thought="",
        opening=rng.choice(OPENINGS),
        quest_word=rng.choice(["quest", "mission", "search"]),
    )
    child.add_meme(params.mood)
    child.add_meme("love", 1)
    return world


def begin(world: World) -> None:
    p = world.params
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    lantern: Entity = f["lantern"]  # type: ignore[assignment]
    path: Path = f["path"]  # type: ignore[assignment]
    text = (
        f'{f["opening"]} {child.id} carried {lantern.phrase} to the table. '
        f'"It is time for our little {f["quest_word"]}," {child.id} said. '
        f'"Then let us make it safe," {helper.id} replied. '
        f'{path.problem} '
        f'Inside, {child.id} thought, "Please let me decide before anything goes wrong." '
        f'The room suddenly felt full of waiting sounds: a clock tick, a spoon tap, '
        f'and the soft suspense of the next choice.'
    )
    child.add_meme("suspense")
    child.add_meter("risk_seen")
    f["inner_thought"] = "The child wondered whether the next move would protect the gift."
    world.record(
        "problem",
        text,
        cause=path.problem,
        result=path.clue,
        actor=child.id,
        target=lantern.id,
    )


def act_notice(world: World) -> None:
    p = world.params
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    path: Path = f["path"]  # type: ignore[assignment]
    child.add_meter("clue_found")
    child.add_meme("confidence")
    text = (
        f'{path.clue} "{path.clue} I know what to do," {child.id} whispered. '
        f'"Tell me your idea," {helper.id} said. '
        f'"I will decide carefully, then you can help me check it."'
    )
    world.record(
        "notice",
        text,
        cause=path.clue,
        result="The child shared the clue and chose a careful plan.",
        actor=child.id,
        target=helper.id,
    )


def act_search(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    child.add_meter("search_steps", 1)
    text = (
        f'{child.id} looked beneath a folded napkin while {helper.id} held the '
        f'lantern steady. "Look slowly," {helper.id} advised. '
        f'"I see a bright thread!" {child.id} answered.'
    )
    world.record(
        "search",
        text,
        cause="The missing hook could be near the lantern's place.",
        result="The child found a bright thread leading to the hook.",
        actor=child.id,
        target="hook",
    )


def act_solution(world: World) -> None:
    p = world.params
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    lantern: Entity = f["lantern"]  # type: ignore[assignment]
    solution = p.solution
    if solution == "move_candle":
        result = "The candle moved to the far end of the table."
        detail = f'{child.id} slid the candle away from the lantern\'s paper tail.'
        target = "candle"
    elif solution == "move_punch":
        result = "The punch moved to the far end of the table."
        detail = f'{helper.id} carried the cup away while {child.id} watched the purple rim.'
        target = "punch"
    elif solution == "find_hook":
        result = "The brass hook was back in the lantern's ribbon."
        detail = f'{child.id} fastened the hook while {helper.id} held the ribbon open.'
        target = "hook"
    else:
        result = "The empty sideboard became a safe place."
        detail = f'{child.id} and {helper.id} made a clear space on the sideboard.'
        target = "sideboard"
    child.add_meter("solution_steps", 1)
    child.add_meme("relief")
    text = (
        f'"I decide!" {child.id} said. {detail} '
        f'"That choice gives the lantern room to shine," {helper.id} said. {result}'
    )
    world.record(
        "decide",
        text,
        cause="The child used the clue to choose a safe action.",
        result=result,
        actor=child.id,
        target=target,
    )


def finish(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    lantern: Entity = f["lantern"]  # type: ignore[assignment]
    path: Path = f["path"]  # type: ignore[assignment]
    child.add_meter("safe", 1)
    child.add_meme("joy")
    lantern.add_meter("hung", 1)
    f["solved"] = True
    text = (
        f'{child.id} and {helper.id} lifted {lantern.label} together toward its hook. '
        f'The lantern settled above the table without a bump. {path.ending} '
        f'"We did it," {child.id} said. "You noticed, you decided, and you helped," '
        f'{helper.id} answered. The suspense melted into a warm smile that belonged '
        f'to both of them.'
    )
    world.record(
        "resolve",
        text,
        cause="The safe action removed the danger before the lantern was hung.",
        result=path.ending,
        actor=child.id,
        target=lantern.id,
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    world = build_world(params, rng)
    begin(world)
    if params.solution == "find_hook":
        act_search(world)
    else:
        act_notice(world)
    act_solution(world)
    finish(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    path = PATHS[p.problem]
    return [
        f"Write a heartwarming dining-room quest where {p.name} must decide how to protect a darling lantern: {path.problem}",
        f"Include suspense, an inner monologue, and a spoken exchange between {p.name} and {p.helper} before the lantern is safely hung.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What problem threatened the darling lantern?", world.history[0].cause),
        QAItem("What clue helped the child decide?", world.history[0].result),
        QAItem("What did the child decide to do?", world.history[2].result),
        QAItem("How did the quest end?", world.history[-1].result),
    ]


KNOWLEDGE = {
    "wobbling_candle": QAItem(
        "Why should paper stay away from a candle?",
        "Paper can catch fire, so it should be kept away from a candle and watched by a grown-up.",
    ),
    "spilled_punch": QAItem(
        "Why is a spilled drink a problem for paper?",
        "A drink can soak paper, wrinkle it, and make its colors run.",
    ),
    "missing_hook": QAItem(
        "Why does a hanging lantern need a strong hook?",
        "A strong hook holds the lantern up so it will not fall onto people or the table.",
    ),
    "crowded_table": QAItem(
        "Why is a clear space useful in a dining room?",
        "A clear space gives objects room to stay steady and keeps elbows from knocking them over.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE[world.params.problem]]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def valid_paths() -> list[tuple[str, str]]:
    return [(problem, solution) for problem, choices in SOLUTIONS.items() for solution in choices]


ASP_RULES = r"""
at_risk(wobbling_candle) :- problem(wobbling_candle).
at_risk(spilled_punch) :- problem(spilled_punch).
at_risk(missing_hook) :- problem(missing_hook).
at_risk(crowded_table) :- problem(crowded_table).
valid(Problem, Solution) :- at_risk(Problem), solution(Problem, Solution).
"""


def asp_facts() -> str:
    import importlib
    asp = importlib.import_module("asp")
    lines = []
    for problem, choices in SOLUTIONS.items():
        lines.append(asp.fact("problem", problem))
        for choice in choices:
            lines.append(asp.fact("solution", problem, choice))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import importlib
    asp = importlib.import_module("asp")
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid"))
    expected = set(valid_paths())
    if found != expected:
        print("MISMATCH: ASP and Python paths differ.")
        return 1
    rng = random.Random(19)
    for problem, solution in expected:
        params = StoryParams(problem, solution, "Robin", "Dad", "careful")
        sample = generate(params)
        check_sample(sample)
    print(f"OK: {len(expected)} executable paths and story checks.")
    return 0


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert world.facts["solved"] is True
    assert world.facts["lantern"].meter("hung") == 1
    assert len(world.history) == 4
    assert any("I decide" in event.text for event in world.history)
    assert any("thought" in event.text for event in world.history)
    assert all("{" not in event.text and "}" not in event.text for event in world.history)
    assert all(event.actor in world.entities and event.target in world.entities
               for event in world.history)
    assert sample.story_qa and all(len(item.answer.split()) >= 3 for item in sample.story_qa)
    assert sample.story.count('"') >= 6
    assert "dining room" in sample.story
    assert "lantern" in sample.story


CURATED = [
    StoryParams("wobbling_candle", "move_candle", "Mira", "Mom", "hopeful"),
    StoryParams("spilled_punch", "move_punch", "Owen", "Dad", "careful"),
    StoryParams("missing_hook", "find_hook", "Nina", "Aunt Rose", "curious"),
    StoryParams("crowded_table", "clear_sideboard", "Theo", "Mom", "brave"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming dining-room decision quest.")
    parser.add_argument("--problem", choices=sorted(PATHS))
    parser.add_argument("--solution", choices=sorted({s for choices in SOLUTIONS.values() for s in choices}))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problems = [args.problem] if args.problem else sorted(PATHS)
    problem = rng.choice(problems)
    choices = list(SOLUTIONS[problem])
    if args.solution is not None:
        if args.solution not in choices:
            raise StoryError("That solution does not fit the selected dining-room problem.")
        solution = args.solution
    else:
        solution = rng.choice(choices)
    return StoryParams(
        problem=problem,
        solution=solution,
        name=args.name or rng.choice(CHILDREN),
        helper=args.helper or rng.choice(HELPERS),
        mood=args.mood or rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params, random.Random(params.seed))
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    check_sample(sample)
    return sample


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import importlib
        asp = importlib.import_module("asp")
        model = asp.one_model(asp_program())
        for problem, solution in sorted(asp.atoms(model, "valid")):
            print(f"{problem}: {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload,
                         indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.problem}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
