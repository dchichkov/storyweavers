#!/usr/bin/env python3
"""Gingham Magic: a tiny nursery-rhyme world of a cloth, a bell, and a choice."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_here = Path(__file__).resolve()
for parent in [_here.parent, *_here.parents]:
    candidate = parent / "results.py"
    if candidate.exists():
        sys.path.insert(0, str(parent))
        break
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str
    result: str


@dataclass
class StoryParams:
    problem: str
    solution: str
    name: str
    friend: str
    color: str = "blue"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, actor: str, target: str, text: str,
               cause: str, result: str) -> None:
        self.events.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PROBLEMS = {
    "lost_bell": {
        "clue": "a silver tinkle beneath the gingham cloth",
        "solutions": ("lift", "sing"),
    },
    "sleepy_star": {
        "clue": "the star's tiny yawn",
        "solutions": ("fold", "hum"),
    },
    "rainy_riddle": {
        "clue": "three drops tapping the nursery window",
        "solutions": ("cover", "dance"),
    },
    "tangled_ribbon": {
        "clue": "a loose red thread beside the knot",
        "solutions": ("untie", "whistle"),
    },
}

SOLUTION_NAMES = {
    "lift": "lift the cloth",
    "sing": "sing a searching song",
    "fold": "fold the cloth into a nest",
    "hum": "hum a sleepy tune",
    "cover": "cover the riddle",
    "dance": "dance the drops away",
    "untie": "untie the ribbon",
    "whistle": "whistle for help",
}

NAMES = ["Pip", "Nell", "Mina", "Toby", "Wren", "Kit"]
FRIENDS = ["Moth", "Mouse", "Robin", "Bunny", "Fox", "Cricket"]

KNOWLEDGE = {
    "gingham": QAItem(
        "What is gingham?",
        "Gingham is woven cloth with a neat checked pattern of two colors.",
    ),
    "magic": QAItem(
        "What makes magic useful in this story?",
        "The magic responds to a careful action, helping the child notice a clue and solve the trouble.",
    ),
    "nursery": QAItem(
        "Why do nursery rhymes use repeated sounds?",
        "Repeated sounds make a rhyme easy to remember and pleasant to say aloud.",
    ),
}


def valid_plan(problem: str, solution: str) -> bool:
    return problem in PROBLEMS and solution in PROBLEMS[problem]["solutions"]


def validate(params: StoryParams) -> None:
    if not params.name.strip() or not params.friend.strip():
        raise StoryError("The child and helper need names.")
    if params.name == params.friend:
        raise StoryError("The child and helper need different names.")
    if not valid_plan(params.problem, params.solution):
        choices = ", ".join(PROBLEMS.get(params.problem, {}).get("solutions", ()))
        raise StoryError(
            f"Solution '{params.solution}' does not fit problem '{params.problem}'. "
            f"Choose: {choices or 'a supported problem'}."
        )


def make_world(params: StoryParams) -> World:
    validate(params)
    w = World()
    child = w.add(Entity(
        params.name, "character", params.name,
        memes={"curiosity": 1.0, "courage": 0.0}, location="nursery",
    ))
    friend = w.add(Entity(
        params.friend, "helper", params.friend,
        memes={"kindness": 1.0}, location="nursery",
    ))
    cloth = w.add(Entity(
        "gingham", "thing", f"{params.color} gingham cloth",
        meters={"spread": 0.0, "magic": 1.0}, location="nursery",
    ))
    trouble = w.add(Entity(
        "trouble", "thing", {
            "lost_bell": "lost silver bell",
            "sleepy_star": "sleepy paper star",
            "rainy_riddle": "rainy riddle",
            "tangled_ribbon": "tangled red ribbon",
        }[params.problem],
        meters={"hidden": 1.0}, location="nursery",
    ))
    w.facts.update(child=child, friend=friend, cloth=cloth, trouble=trouble)
    return w


def opening(w: World, p: StoryParams) -> None:
    child = w.facts["child"]
    friend = w.facts["friend"]
    cloth = w.facts["cloth"]
    lines = {
        "lost_bell": (
            f"{p.name} found the {cloth.label} beneath the moonbeam bright; "
            f"something was missing from the nursery night."
        ),
        "sleepy_star": (
            f"{p.name} spread the {cloth.label} beside the little bed; "
            "a paper star drooped its silver head."
        ),
        "rainy_riddle": (
            f"Rain tapped softly, and {p.name} held the {cloth.label} tight; "
            "a riddle hid from morning light."
        ),
        "tangled_ribbon": (
            f"{p.name} saw the {cloth.label} in a basket of cheer; "
            "a tangled red ribbon seemed stuck fast there."
        ),
    }
    w.record(
        "arrival", child.id, cloth.id,
        lines[p.problem] + f' "{p.name}, shall we mend it?" {p.name} asked. '
        f'"We shall," said {p.friend}, leaning near. '
        f'The {cloth.label} gave one small shimmer, as if it could hear.',
        "The nursery object was not ready for its bedtime use.",
        "The child and helper agreed to look closely instead of giving up.",
    )


def reveal(w: World, p: StoryParams) -> None:
    child = w.facts["child"]
    friend = w.facts["friend"]
    trouble = w.facts["trouble"]
    clue = PROBLEMS[p.problem]["clue"]
    child.memes["courage"] += 1
    trouble.meters["hidden"] = 0
    w.para()
    w.record(
        "clue", child.id, trouble.id,
        f"Then {clue} came clear. " 
        f'"I hear a clue," said {p.name}. "{p.friend}, do you hear it too?" '
        f'"I do," answered {p.friend}. "Let the clue choose our next step." '
        f'Together they watched the {trouble.label}, and the gingham checks glowed softly.',
        f"The trouble was hidden until the nursery clue was noticed.",
        f"The spoken exchange gave both children the same useful knowledge: the magic was awake.",
    )


def solve(w: World, p: StoryParams) -> None:
    child = w.facts["child"]
    friend = w.facts["friend"]
    cloth = w.facts["cloth"]
    trouble = w.facts["trouble"]
    solution = p.solution
    child.memes["courage"] += 1
    cloth.meters["spread"] += 1
    trouble.meters["solved"] = 1
    action = {
        "lift": f"{p.name} lifted the cloth by its blue checked corner",
        "sing": f"{p.name} sang, 'Bell below, bell below, ring where the gingham goes!'",
        "fold": f"{p.name} folded the cloth into a soft little nest",
        "hum": f"{p.name} hummed a low tune, 'Rest, bright star, rest'",
        "cover": f"{p.name} covered the riddle with the gingham cloth",
        "dance": f"{p.name} danced three raindrop steps around the cloth",
        "untie": f"{p.name} loosened the ribbon one loop at a time",
        "whistle": f"{p.name} gave a clear, merry whistle",
    }[solution]
    result = {
        "lift": "The lost bell rolled out with a bright ding.",
        "sing": "The bell answered from under the cradle with a clear ding.",
        "fold": "The sleepy star tucked itself into the checks and opened its silver eyes.",
        "hum": "The star heard the gentle hum and shone above the bed.",
        "cover": "The riddle's wet letters dried into a readable rhyme.",
        "dance": "The drops spun away, leaving the riddle bright and clear.",
        "untie": "The ribbon slipped free and curled into a cheerful bow.",
        "whistle": "A friendly robin flew in and tugged the loose end free.",
    }[solution]
    w.para()
    w.record(
        solution, child.id, trouble.id,
        f"{action}. {result} "
        f'"It worked!" cried {p.name}. "{p.friend}, the magic listened." '
        f'"It listened because you noticed and tried," said {p.friend}.',
        f"The {SOLUTION_NAMES[solution]} matched the clue and changed the hidden trouble.",
        result,
    )


def ending(w: World, p: StoryParams) -> None:
    child = w.facts["child"]
    friend = w.facts["friend"]
    cloth = w.facts["cloth"]
    trouble = w.facts["trouble"]
    w.para()
    images = {
        "lost_bell": "The bell rang ding-dong while the gingham checks danced in the moonlight.",
        "sleepy_star": "The star twinkled once, then nestled above the bed like a tiny moon.",
        "rainy_riddle": "The nursery window shone, and the dry rhyme curled like a smile.",
        "tangled_ribbon": "The red bow bobbed on the basket, bright as a cherry in spring.",
    }
    child.memes["joy"] = 1.0
    w.record(
        "ending", child.id, cloth.id,
        f"{p.name} and {p.friend} put the {trouble.label} in its proper place. "
        f"{images[p.problem]} "
        f"Together they whispered, 'Gingham magic, safe and sound,' "
        "and the nursery answered with a warm, sleepy glow.",
        "The chosen action solved the trouble and restored the nursery.",
        "The child and helper ended together with the magical gingham cloth ready for tomorrow.",
    )


def generate(params: StoryParams) -> StorySample:
    w = make_world(params)
    opening(w, params)
    reveal(w, params)
    solve(w, params)
    ending(w, params)
    story = w.render()
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(w, params),
        story_qa=story_qa(w),
        world_qa=list(KNOWLEDGE.values()),
        world=w,
    )


def prompts(w: World, p: StoryParams) -> list[str]:
    return [
        f"Write a nursery rhyme about {p.name}, a gingham cloth, and a {p.problem.replace('_', ' ')}.",
        f"Tell a magical nursery story in which {p.name} uses {SOLUTION_NAMES[p.solution]} with {p.friend}.",
    ]


def story_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            "What clue helped the children?",
            w.events[1].result,
        ),
        QAItem(
            "How did the children solve the trouble?",
            w.events[2].cause + " " + w.events[2].result,
        ),
        QAItem(
            "What changed at the end?",
            w.events[3].result,
        ),
    ]


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for entity in w.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: location={entity.location}, "
            f"meters={meters}, memes={memes}"
        )
    lines.append("--- events ---")
    for event in w.events:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
visible_clue(P) :- problem(P).
compatible(P, S) :- problem_solution(P, S).
solved(P, S) :- compatible(P, S), visible_clue(P).
"""


def asp_facts() -> str:
    try:
        import asp
    except ImportError as exc:
        raise StoryError("ASP mode requires clingo and storyworlds/asp.py.") from exc
    lines = []
    for problem, data in PROBLEMS.items():
        lines.append(asp.fact("problem", problem))
        for solution in data["solutions"]:
            lines.append(asp.fact("problem_solution", problem, solution))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/2.") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        found = set(asp.atoms(model, "compatible"))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    expected = {(p, s) for p, data in PROBLEMS.items() for s in data["solutions"]}
    if found != expected:
        print("MISMATCH: ASP and Python paths differ.")
        return 1
    for problem, solution in sorted(expected):
        sample = generate(StoryParams(problem, solution, "Pip", "Moth"))
        assert sample.world.facts["trouble"].meters["solved"] == 1
        assert "{" not in sample.story and "}" not in sample.story
        assert any('said Pip' in e.text and 'answered Moth' in e.text for e in sample.world.events)
    print(f"OK: {len(expected)} executable paths verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham Magic nursery-rhyme storyworld.")
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=sorted(SOLUTION_NAMES))
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--color", default="blue")
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
    problems = [args.problem] if args.problem else sorted(PROBLEMS)
    problem = rng.choice(problems)
    choices = PROBLEMS[problem]["solutions"]
    if args.solution is not None:
        if args.solution not in choices:
            raise StoryError(
                f"Solution '{args.solution}' does not fit problem '{problem}'."
            )
        solution = args.solution
    else:
        solution = rng.choice(choices)
    return StoryParams(
        problem=problem,
        solution=solution,
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        color=args.color,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print("\n== Generation prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            for problem, solution in sorted(asp.atoms(model, "compatible")):
                print(f"{problem}: {solution}")
        except Exception as exc:
            raise SystemExit(str(exc)) from exc
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(problem, solution, NAMES[i % len(NAMES)],
                        FRIENDS[i % len(FRIENDS)], seed=base + i)
            for i, (problem, data) in enumerate(sorted(PROBLEMS.items()))
            for solution in data["solutions"]
        ]
    else:
        params_list = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            params_list.append(params)

    samples = [generate(p) for p in params_list]
    if args.json:
        payload = samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        )
        print(payload)
        return
    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header="" if len(samples) == 1 else f"### rhyme {i + 1}",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
