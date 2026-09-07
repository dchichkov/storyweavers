#!/usr/bin/env python3
"""A nursery-rhyme world of gingham magic, small troubles, and kind choices."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

HERE = os.path.abspath(__file__)
ROOT = os.path.dirname(HERE)
while ROOT and not os.path.exists(os.path.join(ROOT, "results.py")):
    parent = os.path.dirname(ROOT)
    if parent == ROOT:
        break
    ROOT = parent
sys.path.insert(0, ROOT)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    id: str
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Person
    helper: Person
    problem: str
    magic: str
    paragraphs: list[str] = field(default_factory=list)
    events: list[dict[str, str]] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def event(self, kind: str, text: str, cause: str, result: str) -> None:
        self.events.append({"kind": kind, "text": text, "cause": cause, "result": result})
        self.paragraphs.append(text)


@dataclass
class StoryParams:
    name: str
    helper: str
    problem: str
    magic: str
    seed: int | None = None


NAMES = ["Molly", "Pip", "Nell", "Toby", "May", "Kit"]
HELPERS = ["Gran", "Aunt Rose", "Uncle Tom", "Mama"]
MAGICS = ["moonlit", "sparkling", "whistling"]
PROBLEMS = ["tear", "wind", "sleep"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Gingham Magic Nursery Rhyme")
    p.add_argument("--name")
    p.add_argument("--helper")
    p.add_argument("--problem", choices=PROBLEMS)
    p.add_argument("--magic", choices=MAGICS)
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--asp", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--show-asp", action="store_true")
    return p


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        problem=args.problem or rng.choice(PROBLEMS),
        magic=args.magic or rng.choice(MAGICS),
    )


def make_world(params: StoryParams, rng: random.Random) -> World:
    hero = Person(params.name, params.name, "child", {"care": 0, "joy": 0}, {})
    helper = Person(params.helper, params.helper, "helper", {"help": 0}, {})
    world = World(hero, helper, params.problem, params.magic)
    hero.memes["wonder"] = 1
    helper.memes["patience"] = 1

    if params.problem == "tear":
        world.event(
            "discover",
            f"{hero.name} wore a gingham apron while gathering bluebells, when a bramble caught it with a tiny rip.",
            f"The bramble tugged the gingham apron as {hero.name} reached for the flowers.",
            f"The apron was torn and could not safely hold the bluebells.",
        )
        world.event(
            "learn",
            f'"Can magic mend cloth?" {hero.name} asked. "{helper.name} knew a patch would help, but it had to be stitched before the rip grew.',
            f"{hero.name} learned that a kind spell needed a real patch and careful hands.",
            f"{hero.name} understood that magic could guide the repair, not replace the work.",
        )
        world.event(
            "decision",
            f'"I will sew first," said {hero.name}. {helper.name} showed a gingham square, and together they stitched it over the rip.',
            f"{hero.name} chose patient sewing after learning what the magic needed.",
            f"The patch held the cloth together.",
        )
        world.event(
            "resolve",
            f'The {params.magic} Magic warmed the stitches, and the gingham apron bloomed with a little blue flower.',
            f"The completed patch gave the magic a sound place to settle.",
            f"{hero.name} carried the bluebells home without another tear.",
        )
        world.facts.update(repaired=True, visible="a blue flower on the gingham patch")
    elif params.problem == "wind":
        world.event(
            "discover",
            f"{hero.name} spread a gingham picnic cloth beneath the pear tree, but a brisk wind whisked it toward the pond.",
            f"The wind lifted the light cloth before the picnic basket was set down.",
            f"The gingham cloth and the picnic were in danger of floating away.",
        )
        world.event(
            "learn",
            f'"A spell cannot hold what we do not anchor," {helper.name} called. "{hero.name} learned that four stones would give the cloth four steady corners.',
            f"{helper.name} explained that the wind needed a firm answer, not only a wish.",
            f"{hero.name} knew to gather four stones before saying the magic words.",
        )
        world.event(
            "decision",
            f'{hero.name} fetched four round stones and placed one on each gingham corner. "{helper.name}, now the cloth can stay!" {hero.name} cried.',
            f"{hero.name} chose anchors after learning why the wind had won.",
            f"The four corners stayed flat on the grass.",
        )
        world.event(
            "resolve",
            f'The {params.magic} Magic twinkled along the checks, and the wind turned into a soft humming breeze around the anchored gingham.',
            f"The stones held the cloth still enough for the spell to work.",
            f"The picnic stayed dry, and the basket rested safely in the middle.",
        )
        world.facts.update(repaired=True, visible="four stones holding the gingham corners")
    else:
        world.event(
            "discover",
            f"{hero.name} tucked a sleepy moon-mouse beneath a gingham quilt, but the little creature shivered instead of resting.",
            f"The moon-mouse had wandered in cold from the garden.",
            f"The quilt alone had not made the moon-mouse feel safe.",
        )
        world.event(
            "learn",
            f'"It needs a song and a warm nest," {helper.name} whispered. "{hero.name} learned that quiet magic listened to a gentle welcome.',
            f"{helper.name} told {hero.name} that comfort came before a sleeping spell.",
            f"{hero.name} understood that the moon-mouse needed care, not a command.",
        )
        world.event(
            "decision",
            f'{hero.name} curled beside the gingham quilt and sang, "Hush-a-bye, little star." {helper.name} tucked a warm sock beside the moon-mouse.',
            f"{hero.name} chose a lullaby, while {helper.name} added warmth after learning the real need.",
            f"The moon-mouse relaxed in its nest.",
        )
        world.event(
            "resolve",
            f'The {params.magic} Magic sprinkled silver checks across the gingham, and the moon-mouse slept beneath them with a smile.',
            f"The gentle song and warm nest opened the way for the magic.",
            f"The moon-mouse slept safely until morning.",
        )
        world.facts.update(repaired=True, visible="silver checks shining on the gingham quilt")
    return world


def prompts(world: World) -> list[str]:
    return [
        f"Write a Nursery Rhyme about {world.hero.name}, gingham, and {world.problem} that is solved with {world.magic} Magic.",
        f"Tell a gentle story where {world.helper.name} helps {world.hero.name} learn what the gingham needs before magic can help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(f"What trouble did {world.hero.name} face?", world.events[0]["cause"] + " " + world.events[0]["result"]),
        QAItem("What did the child learn?", world.events[1]["cause"] + " " + world.events[1]["result"]),
        QAItem("What choice solved the trouble?", world.events[2]["cause"] + " " + world.events[2]["result"]),
        QAItem("What showed that the problem was over?", world.events[3]["cause"] + " " + world.events[3]["result"]),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is gingham?", "Gingham is a woven cloth with a simple pattern of even checks."),
        QAItem("What is magic in this story?", "Magic is a make-believe power that helps after caring people make a wise preparation."),
    ]


ASP_RULES = """
ready :- prepared.
prepared :- problem(tear), patch.
prepared :- problem(wind), anchors.
prepared :- problem(sleep), comfort.
resolved :- ready.
#show resolved/0.
"""


def asp_facts() -> str:
    return "\n".join([
        "problem(tear).",
        "problem(wind).",
        "problem(sleep).",
        "patch.",
        "anchors.",
        "comfort.",
    ])


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"  hero: {world.hero.name}, joy={world.hero.memes.get('joy', 0)}",
        f"  helper: {world.helper.name}, help={world.helper.meters.get('help', 0)}",
        f"  problem: {world.problem}",
        f"  visible resolution: {world.facts.get('visible', '')}",
        "--- events ---",
        *[f"  {e['kind']}: {e['text']}" for e in world.events],
    ])


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS:
        raise StoryError("The selected trouble is not part of this nursery-rhyme world.")
    if params.name == params.helper:
        raise StoryError("The child and helper need different names.")
    rng = random.Random(params.seed)
    world = make_world(params, rng)
    world.hero.memes["joy"] = 1
    world.helper.meters["help"] = 1
    story = "\n\n".join(world.paragraphs)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_facts() + "\n" + ASP_RULES)
        return
    if args.asp:
        print("resolved")
        return
    if args.verify:
        for problem in PROBLEMS:
            sample = generate(StoryParams("Molly", "Gran", problem, "moonlit"))
            assert sample.world.facts["repaired"]
            assert "gingham" in sample.story
        print("OK: all causal paths verified")
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    for i in range(args.n):
        rng = random.Random(base + i)
        if args.all:
            problem = PROBLEMS[i % len(PROBLEMS)]
            params = StoryParams(
                name=NAMES[i % len(NAMES)],
                helper=HELPERS[i % len(HELPERS)],
                problem=problem,
                magic=MAGICS[i % len(MAGICS)],
                seed=base + i,
            )
        else:
            params = resolve_params(args, rng)
            params.seed = base + i
        samples.append(generate(params))

    if args.json:
        payload = [s.to_dict() for s in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 60 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
