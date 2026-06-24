#!/usr/bin/env python3
"""
A small comedy storyworld about a textile employee who insists on sharing, with
repetition as the engine of the joke.

Premise:
- A textile employee is trying to finish a simple job in a cloth shop.
- The employee keeps insisting that everyone share one special textile sample.
- Repetition turns the insistence into a comic pattern.
- The situation resolves when the employee learns that sharing can mean taking
  turns, not giving away everything at once.

The world model tracks physical materials and emotional pressure:
- meters: cloth, cut, folded, tangled, clean, scattered
- memes: insistence, annoyance, cooperation, relief, laughter

The story is generated from simulated state rather than fixed prose.
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

ASP_RULES = r"""
% A textile item becomes shared when more than one person has access to it.
shared(T) :- textile(T), available(T), count_users(T, N), N >= 2.

% An employee insisting too much creates annoyance.
annoying(E) :- employee(E), insists(E, T), repeated(E, T, N), N >= 3.

% A reasonable fix is turn-taking sharing.
resolved(E, T) :- employee(E), textile(T), shares_turns(E, T).
"""

LOCATIONS = {
    "workroom": {
        "label": "the workroom",
        "detail": "The workroom smelled like warm thread and fresh cloth.",
    },
    "counter": {
        "label": "the shop counter",
        "detail": "The shop counter was crowded with buttons, ribbons, and folded fabric.",
    },
    "storage": {
        "label": "the storage room",
        "detail": "The storage room was packed with shelves of textiles in neat stacks.",
    },
}

TEXTILES = {
    "bolts": {
        "label": "a long bolt of striped textile",
        "short": "the striped bolt",
        "kind": "bolt",
        "share_mode": "take turns",
    },
    "scarves": {
        "label": "a soft stack of scarves",
        "short": "the scarf stack",
        "kind": "scarves",
        "share_mode": "split evenly",
    },
    "ribbons": {
        "label": "a bright bundle of ribbons",
        "short": "the ribbon bundle",
        "kind": "ribbons",
        "share_mode": "pass around",
    },
    "sample": {
        "label": "a fancy textile sample with tiny stars",
        "short": "the starry sample",
        "kind": "sample",
        "share_mode": "look together",
    },
}

NAMES = ["Mina", "Owen", "Lila", "Noah", "Pia", "June", "Eli", "Tess"]
COWORKERS = ["the clerk", "the cutter", "the tailor", "the helper"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    textile: str
    name: str
    coworker: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.repeats: int = 0

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a textile employee who insists on sharing.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--textile", choices=TEXTILES)
    ap.add_argument("--name")
    ap.add_argument("--coworker", choices=COWORKERS)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in LOCATIONS:
        lines.append(asp.fact("place", place))
    for tid, t in TEXTILES.items():
        lines.append(asp.fact("textile", tid))
        lines.append(asp.fact("available", tid))
        lines.append(asp.fact("share_mode", tid, t["share_mode"]))
    for name in NAMES:
        lines.append(asp.fact("employee_name", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in LOCATIONS:
        for textile in TEXTILES:
            combos.append((place, textile))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.textile:
        combos = [c for c in combos if c[1] == args.textile]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, textile = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    coworker = args.coworker or rng.choice(COWORKERS)
    return StoryParams(place=place, textile=textile, name=name, coworker=coworker)


def _shared_turns(world: World, hero: Entity, textile: Entity, turns: int = 3) -> None:
    for i in range(turns):
        world.repeats += 1
        if i == 0:
            world.say(f'{hero.id} looked at {textile.label} and said, "We should share it."')
        else:
            world.say(f'{hero.id} said it again: "We should share it."')
        hero.memes["insistence"] += 1
        textile.meters["handled"] = textile.meters.get("handled", 0) + 1
        if i >= 1:
            world.say(f'The room repeated the idea back like a bouncing ball: share it, share it, share it.')


def generate_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.name, kind="employee", type="employee"))
    coworker = world.add(Entity(id=params.coworker, kind="character", type="coworker"))
    textile_cfg = TEXTILES[params.textile]
    textile = world.add(Entity(id="textile", kind="thing", type="textile", label=textile_cfg["label"]))

    hero.meters["cloth"] = 1
    textile.meters["clean"] = 1
    hero.memes["insistence"] = 0
    coworker.memes["annoyance"] = 0
    coworker.memes["cooperation"] = 0

    world.say(f'{params.name} was a textile employee in {LOCATIONS[params.place]["label"]}.')
    world.say(LOCATIONS[params.place]["detail"])
    world.say(f'The employee was proud of {textile.label} and kept a careful hand on it.')

    world.para()
    world.say(f'{params.name} wanted everyone to share {textile.short}, and {params.name} insisted.')
    _shared_turns(world, hero, textile, turns=3)

    coworker.memes["annoyance"] += 1
    world.say(f'{params.coworker} blinked and asked, "Share it with whom?"')
    world.say(f'{params.name} answered by insisting again, which made the joke feel even rounder.')
    world.say(f'"We can all share," {params.name} said, "because sharing is nicer than choosing."')

    world.para()
    world.say(f'{params.coworker} pointed to a small table and suggested a better way.')
    world.say(f'"How about we {textile_cfg["share_mode"]}?" {params.coworker} asked.')
    world.say(f'That meant everyone could enjoy {textile.short} without grabbing it all at once.')

    hero.memes["insistence"] = 0
    hero.memes["cooperation"] = 1
    coworker.memes["cooperation"] = 1
    world.say(f'{params.name} stopped insisting, laughed at the repetition, and nodded.')
    world.say(f'Together they took turns with {textile.short}, and the whole room felt lighter.')

    world.facts.update(
        hero=hero,
        coworker=coworker,
        textile=textile,
        textile_cfg=textile_cfg,
        place=params.place,
        repeats=world.repeats,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short funny story for a young child about a textile employee who keeps insisting on sharing.',
        f'Write a comedy story set in {LOCATIONS[f["place"]]["label"]} where {f["hero"].id} repeats "We should share it."',
        f'Tell a playful story about {f["textile_cfg"]["label"]} and how sharing can become funny when someone insists too much.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    coworker = f["coworker"]
    textile = f["textile"]
    cfg = f["textile_cfg"]
    place = LOCATIONS[f["place"]]["label"]
    return [
        QAItem(
            question=f"What kind of worker was {hero.id}?",
            answer=f'{hero.id} was a textile employee working in {place}.',
        ),
        QAItem(
            question=f'What did {hero.id} keep insisting about {textile.short}?',
            answer=f'{hero.id} kept insisting that everyone should share {textile.short}.',
        ),
        QAItem(
            question=f'How did {coworker.id} help solve the problem?',
            answer=f'{coworker.id} suggested a better sharing plan: they could {cfg["share_mode"]} and take turns.',
        ),
        QAItem(
            question=f'What made the story funny?',
            answer='The employee repeated the same idea over and over, so the sharing joke kept coming back.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is textile?",
            answer="Textile is cloth or fabric made by weaving or knitting threads together.",
        ),
        QAItem(
            question="What does an employee do?",
            answer="An employee is a person who works for a place or a business and helps get the job done.",
        ),
        QAItem(
            question="What does insist mean?",
            answer="To insist means to keep saying something is important and not want to give up the idea.",
        ),
        QAItem(
            question="Why can repetition be funny in a story?",
            answer="Repetition can be funny because the same words or action happen again and again in a playful way.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind:8}) meters={e.meters} memes={e.memes}")
    lines.append(f"  repeats: {world.repeats}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_program("#show shared/1.\n#show annoying/1.\n#show resolved/2.")
    model = asp.one_model(program)
    if model is None:
        raise StoryError("ASP solver produced no model.")
    print("OK: ASP program solved successfully.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(place="workroom", textile="sample", name="Mina", coworker="the clerk"),
    StoryParams(place="counter", textile="bolts", name="Owen", coworker="the tailor"),
    StoryParams(place="storage", textile="ribbons", name="Tess", coworker="the helper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shared/1.\n#show annoying/1.\n#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show shared/1.\n#show annoying/1.\n#show resolved/2."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.textile} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
