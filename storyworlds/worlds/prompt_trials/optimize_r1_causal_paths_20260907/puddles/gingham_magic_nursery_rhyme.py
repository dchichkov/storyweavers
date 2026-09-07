#!/usr/bin/env python3
"""Gingham Magic Nursery Rhyme.

A small simulated world about a child, a gingham ribbon, and a friendly bit of
magic.  The rhyme changes when the child learns what the ribbon can really do.
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
    owner: Optional[str] = None
    location: str = ""


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    problem: str
    solution: str
    rhyme: str
    name: str = "Mina"
    helper: str = "Grandma"
    seed: Optional[int] = None


PROBLEMS = {
    "lost_star": {
        "object": "star",
        "place": "the moonlit nursery",
        "need": "find the silver star that slipped behind the toy chest",
    },
    "sleepy_moon": {
        "object": "moon",
        "place": "the quiet nursery",
        "need": "wake the little moon that forgot to shine",
    },
    "broken_song": {
        "object": "bell",
        "place": "the gingham garden",
        "need": "mend the tiny bell that lost its ring",
    },
    "wandering_bear": {
        "object": "bear",
        "place": "the blanket meadow",
        "need": "guide the small bear back to its basket",
    },
}

SOLUTIONS = {
    "lost_star": ("tie_ribbon", "ask_moon"),
    "sleepy_moon": ("hum_ribbon", "open_curtain"),
    "broken_song": ("tie_ribbon", "share_song"),
    "wandering_bear": ("ask_moon", "tie_ribbon"),
}

RHYMES = {
    "lilting": (
        "Gingham bright and gingham blue,",
        "a little spell may help us through.",
    ),
    "bouncy": (
        "Hop, hop, hush, and hop once more,",
        "magic waits beside the door.",
    ),
    "soft": (
        "Sleepy stars and silver light,",
        "kind words make the dark feel right.",
    ),
    "marching": (
        "One small step and then two feet,",
        "a brave heart makes the path complete.",
    ),
}

NAMES = ["Mina", "Pip", "Nell", "Toby", "Lulu", "Sam"]
HELPERS = ["Grandma", "Aunt May", "Papa", "Nana"]
PROBLEM_ORDER = list(PROBLEMS)
SOLUTION_ORDER = sorted({x for values in SOLUTIONS.values() for x in values})


def valid_pair(problem: str, solution: str) -> bool:
    return problem in SOLUTIONS and solution in SOLUTIONS[problem]


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

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str,
        result: str,
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def opening(world: World) -> None:
    p = world.params
    problem = PROBLEMS[p.problem]
    hero = world.entities[p.name]
    helper = world.entities[p.helper]
    hero.memes["wonder"] = 1
    hero.memes["worry"] = 1
    text = (
        f"In {problem['place']}, {p.name} wore a gingham sash and counted "
        f"the little checks: one, two, three. {p.rhyme[0]} {p.rhyme[1]} "
        f"Then a small trouble appeared: {p.name} had to {problem['need']}."
    )
    world.record(
        "arrival",
        text,
        actor=hero.id,
        target=helper.id,
        cause=f"The {problem['object']} needed help.",
        result=f"{p.name} noticed that the {problem['object']} was not where it belonged.",
    )


def problem_scene(world: World) -> None:
    p = world.params
    hero = world.entities[p.name]
    helper = world.entities[p.helper]
    obj = world.entities[p.problem]
    world.para()
    hero.memes["worry"] += 1
    obj.meters["hidden"] = 1
    questions = {
        "lost_star": (
            f'"I looked under the pillow," {p.name} said, "but the star is still away." '
            f'"Look for a glimmer, not a guess," {p.helper} replied.',
        ),
        "sleepy_moon": (
            f'"The moon has shut its eye," {p.name} whispered. '
            f'"Then let us wake it gently," said {p.helper}.',
        ),
        "broken_song": (
            f'"The bell gives no ding," {p.name} said. '
            f'"Perhaps it needs a pattern," {p.helper} answered.',
        ),
        "wandering_bear": (
            f'"The bear keeps turning round," {p.name} said. '
            f'"Ask where home feels warm," said {p.helper}.',
        ),
    }[p.problem]
    cause = {
        "lost_star": "The silver star was hidden behind the toy chest.",
        "sleepy_moon": "The paper moon had folded itself into a sleepy crescent.",
        "broken_song": "The tiny bell had lost its bright ringing pattern.",
        "wandering_bear": "The little bear had wandered away from its basket.",
    }[p.problem]
    result = "The child learned that the gingham sash was a guide, not a wishing wand."
    world.record(
        "discovery",
        f"{questions[0]} {cause} {result}",
        actor=hero.id,
        target=obj.id,
        cause=cause,
        result=result,
    )


def solve_scene(world: World) -> None:
    p = world.params
    hero = world.entities[p.name]
    helper = world.entities[p.helper]
    obj = world.entities[p.problem]
    solution = p.solution
    world.para()

    if solution == "tie_ribbon":
        hero.memes["care"] = hero.memes.get("care", 0) + 1
        obj.meters["guided"] = 1
        result = {
            "lost_star": "The sash made a gingham trail, and the silver star winked beside the chest.",
            "broken_song": "The sash held the bell's loose loop, and the bell rang ding-ding again.",
            "wandering_bear": "The sash made a soft path, and the bear padded home to its basket.",
        }.get(solution if False else p.problem, "The sash made a soft path, and the bear padded home to its basket.")
        cause = "The gingham checks gave the magic a clear path to follow."
        text = (
            f'"I will make a path," {p.name} said. {p.helper} held one end while '
            f'{p.name} tied the gingham sash in three neat bows. {result} '
            f'"It was not a wish," said {p.helper}; "it was a careful guide."'
        )
        world.record("tie_ribbon", text, actor=hero.id, target=obj.id, cause=cause, result=result)
    elif solution == "ask_moon":
        hero.memes["listening"] = 1
        obj.meters["answered"] = 1
        result = {
            "lost_star": "The moon shone a pale square of light behind the toy chest.",
            "wandering_bear": "The moon lit the basket, and the bear followed the bright patch home.",
        }[p.problem]
        cause = "The child asked kindly, so the moon showed a safe direction."
        text = (
            f'"Moon, may you show us where to look?" {p.name} asked. '
            f'"I can show, but you must choose," whispered the moon. {result} '
            f'{p.name} followed the light instead of rushing.'
        )
        world.record("ask_moon", text, actor=hero.id, target=obj.id, cause=cause, result=result)
    elif solution == "hum_ribbon":
        hero.memes["patience"] = 1
        obj.meters["awake"] = 1
        result = "The sleepy moon unfolded and spilled a round pool of silver on the rug."
        cause = "A gentle hum gave the moon a steady beat to follow."
        text = (
            f'{p.name} hummed into the gingham bow: "Hmm-hmm, rise and shine." '
            f'"That is a warm song," said {p.helper}. {result} '
            f'The room glowed softly, with no loud spell at all.'
        )
        world.record("hum_ribbon", text, actor=hero.id, target=obj.id, cause=cause, result=result)
    elif solution == "open_curtain":
        hero.memes["courage"] = 1
        obj.meters["awake"] = 1
        result = "The moon caught the dawn-colored sky and woke with a silver smile."
        cause = "Opening the curtain let real morning light join the small magic."
        text = (
            f'"Magic can have a window," {p.name} decided. {p.helper} pulled the '
            f'curtain while {p.name} held the gingham edge. {result} '
            f'"Some spells need help from the world," said {p.helper}.'
        )
        world.record("open_curtain", text, actor=hero.id, target=obj.id, cause=cause, result=result)
    elif solution == "share_song":
        hero.memes["joy"] = 1
        obj.meters["ringing"] = 1
        result = "The bell found its ding, and every toy answered with a tiny ting."
        cause = "A shared song supplied the missing rhythm."
        text = (
            f'{p.name} began a tune, and {p.helper} joined: "Ding for you, '
            f'and ding for me." {result} The gingham sash bounced like a little flag.'
        )
        world.record("share_song", text, actor=hero.id, target=obj.id, cause=cause, result=result)


def ending(world: World) -> None:
    p = world.params
    hero = world.entities[p.name]
    obj = world.entities[p.problem]
    world.para()
    obj.meters["safe"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    endings = {
        "lost_star": "The star rested on the sash's last bow, bright as a crumb of sky.",
        "sleepy_moon": "The moon hung above the bed, round and calm, while the gingham sash slept below.",
        "broken_song": "The bell swung from the sash, singing a nursery rhyme into the garden.",
        "wandering_bear": "The bear curled in its basket, and the gingham path lay quiet across the blanket meadow.",
    }
    cause = f"The {p.solution.replace('_', ' ')} solution changed the trouble into a safe ending."
    result = endings[p.problem]
    text = (
        f'{result} {p.name} bowed to the gentle magic. '
        f'"A small heart can make a large spell," {p.helper} said. '
        f'{p.rhyme[0]} {p.rhyme[1]}'
    )
    world.record("ending", text, actor=hero.id, target=obj.id, cause=cause, result=result)
    world.facts["resolved"] = True


def build_world(params: StoryParams) -> World:
    if not valid_pair(params.problem, params.solution):
        raise StoryError("That magic solution does not fit the chosen problem.")
    world = World(params)
    world.add(Entity(params.name, "character", params.name, location="nursery"))
    world.add(Entity(params.helper, "character", params.helper, location="nursery"))
    world.add(Entity("gingham", "ribbon", "gingham sash", owner=params.name, location="nursery"))
    labels = {
        "lost_star": "silver star",
        "sleepy_moon": "paper moon",
        "broken_song": "tiny bell",
        "wandering_bear": "little bear",
    }
    world.add(Entity(params.problem, "magical_object", labels[params.problem], location="nursery"))
    opening(world)
    problem_scene(world)
    solve_scene(world)
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    problem = PROBLEMS[p.problem]
    return [
        f"Write a Nursery Rhyme story with gingham and Magic, where {p.name} must {problem['need']}.",
        f"Tell a gentle rhyme in which {p.name} uses {p.solution.replace('_', ' ')} to help a magical {problem['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrival": "What trouble appeared at the beginning?",
        "discovery": "What did the child learn about the gingham sash?",
        "tie_ribbon": "How did tying the ribbon help?",
        "ask_moon": "Why did the child ask the moon?",
        "hum_ribbon": "What woke the moon?",
        "open_curtain": "How did the curtain help?",
        "share_song": "What brought the bell's song back?",
        "ending": "What showed that the trouble was over?",
    }
    out = []
    for event in world.history:
        if event.kind in questions:
            out.append(QAItem(questions[event.kind], f"{event.cause} {event.result}"))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven cloth with a simple checked pattern, often made with two colors.",
        ),
        QAItem(
            "What is magic in a story?",
            "Magic in a story is an unusual power that helps something happen beyond ordinary rules.",
        ),
        QAItem(
            "Why can a rhyme be easy to remember?",
            "A rhyme uses repeated sounds and a steady beat, which helps listeners remember its words.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes} location={entity.location}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
helpful(Solution, Problem) :- solution(Solution), fits(Solution, Problem).
fits(tie_ribbon, lost_star).
fits(ask_moon, lost_star).
fits(hum_ribbon, sleepy_moon).
fits(open_curtain, sleepy_moon).
fits(tie_ribbon, broken_song).
fits(share_song, broken_song).
fits(ask_moon, wandering_bear).
fits(tie_ribbon, wandering_bear).
valid(Problem, Solution) :- problem(Problem), helpful(Solution, Problem).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for problem in PROBLEMS:
        lines.append(asp.fact("problem", problem))
    for solution in SOLUTION_ORDER:
        lines.append(asp.fact("solution", solution))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid"))
    expected = {(p, s) for p, solutions in SOLUTIONS.items() for s in solutions}
    if found != expected:
        print("MISMATCH: ASP and Python paths differ.")
        return 1
    checked = 0
    for problem, solutions in SOLUTIONS.items():
        for solution in solutions:
            sample = generate(
                StoryParams(problem=problem, solution=solution, rhyme="lilting")
            )
            if not sample.story or not sample.story_qa:
                return 1
            checked += 1
    print(f"OK: {len(found)} ASP/Python paths and {checked} generated stories checked.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown magic problem.")
    if not valid_pair(params.problem, params.solution):
        raise StoryError("The chosen solution cannot resolve this magic problem.")
    if not params.name.strip() or not params.helper.strip():
        raise StoryError("Characters need names.")
    if params.rhyme not in RHYMES:
        raise StoryError("Unknown rhyme style.")
    params = StoryParams(
        problem=params.problem,
        solution=params.solution,
        rhyme=RHYMES[params.rhyme],
        name=params.name,
        helper=params.helper,
        seed=params.seed,
    )
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham Magic Nursery Rhyme storyworld.")
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTION_ORDER)
    parser.add_argument("--rhyme", choices=RHYMES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
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
    problems = [args.problem] if args.problem else PROBLEM_ORDER
    candidates = [
        (problem, solution)
        for problem in problems
        for solution in SOLUTIONS[problem]
        if args.solution is None or solution == args.solution
    ]
    if not candidates:
        raise StoryError("No compatible magic path matches those options.")
    problem, solution = rng.choice(candidates)
    return StoryParams(
        problem=problem,
        solution=solution,
        rhyme=args.rhyme or rng.choice(list(RHYMES)),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def curated() -> list[StoryParams]:
    return [
        StoryParams("lost_star", "tie_ribbon", "lilting", "Mina", "Grandma"),
        StoryParams("lost_star", "ask_moon", "soft", "Pip", "Nana"),
        StoryParams("sleepy_moon", "hum_ribbon", "soft", "Nell", "Aunt May"),
        StoryParams("sleepy_moon", "open_curtain", "marching", "Toby", "Papa"),
        StoryParams("broken_song", "share_song", "bouncy", "Lulu", "Grandma"),
        StoryParams("wandering_bear", "tie_ribbon", "lilting", "Sam", "Nana"),
        StoryParams("wandering_bear", "ask_moon", "soft", "Mina", "Papa"),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for problem, solution in sorted(set(asp.atoms(model, "valid"))):
            print(f"{problem:16} {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
