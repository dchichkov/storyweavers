#!/usr/bin/env python3
"""
A myth-style story world about a sworn promise, a mistaken assumption, and a
surprising reveal.
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

TRY_BEATS = [
    "swear",
    "assumption",
    "surprise",
]

NAMES = [
    "Ari", "Bela", "Ciro", "Dara", "Eli", "Fara", "Galen", "Hera",
]

TITLES = [
    "the shepherd", "the lamp-bearer", "the tide watcher", "the seed keeper",
    "the bridge singer", "the gate guardian",
]

GIFTS = [
    "a silver key", "a bowl of figs", "a bright shell", "a woven charm",
    "a sunstone",
]

PLACES = [
    "the old hill", "the river gate", "the moon grove", "the quiet harbor",
    "the ash plain",
]


@dataclass
class StoryParams:
    hero: str
    title: str
    place: str
    gift: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "character"
    title: str = ""
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style story world of oath, mistake, and surprise.")
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
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
    return StoryParams(
        hero=args.hero or rng.choice(NAMES),
        title=args.title or rng.choice(TITLES),
        place=args.place or rng.choice(PLACES),
        gift=args.gift or rng.choice(GIFTS),
    )


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


ASP_RULES = r"""
swear_possible(P) :- place(P).
surprise_possible(G) :- gift(G).
story_ready(P,G) :- swear_possible(P), surprise_possible(G).
#show story_ready/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show story_ready/2."))
    atoms = set(asp.atoms(model, "story_ready"))
    py = {(p, g) for p in PLACES for g in GIFTS}
    if atoms == py:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(params.place)
    hero = world.add(Entity(id=params.hero, kind="character", title=params.title))
    gift = world.add(Entity(id="gift", kind="thing", label=params.gift, memes={"mystery": 1.0}))

    hero.memes["duty"] = 1.0
    hero.memes["hope"] = 1.0

    world.say(
        f"At {params.place}, {params.title} {params.hero} watched the dusk gather like a cloak."
    )
    world.say(
        f"{params.hero} lifted a hand and made a solemn swear: the path would be kept clear "
        f"and the old gate would be watched until the stars rose."
    )
    world.say(
        f"Yet {params.hero} made one assumption, as many mortals do: the wind-tossed glow in the reeds "
        f"must be a lost lantern, waiting for rescue."
    )
    world.para()
    world.say(
        f"So {params.hero} went nearer, careful and brave, and the reeds parted with a sudden surprise."
    )
    world.say(
        f"It was not a lantern at all, but {params.gift}, warm as a heartbeat and bright as morning fire."
    )
    world.say(
        f"The gift had been left there by an unseen ancestor, as if the old hill itself had answered the swear."
    )
    world.para()
    world.say(
        f"{params.hero} laughed at the false assumption, took up {params.gift}, and carried it back to the people."
    )
    world.say(
        f"That night, the gate shone with new favor, and {params.hero} was known not only for keeping vows, "
        f"but for welcoming the surprise that changed the tale."
    )

    world.facts.update(hero=hero, gift=gift, params=params)
    story = world.render()
    prompts = [
        f"Write a short myth about a {params.title} who makes a swear, learns from an assumption, and meets a surprise.",
        f"Tell a child-friendly legend set at {params.place} where {params.hero} discovers that things are not what they seemed.",
    ]
    story_qa = [
        QAItem(
            question=f"What swear did {params.hero} make at {params.place}?",
            answer=f"{params.hero} swore to keep the path clear and watch the old gate until the stars rose.",
        ),
        QAItem(
            question=f"What assumption did {params.hero} make about the glow in the reeds?",
            answer=f"{params.hero} assumed it was a lost lantern that needed rescue.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The glow was not a lantern at all. It was {params.gift}, left behind by an unseen ancestor.",
        ),
        QAItem(
            question=f"How did the story end after the surprise?",
            answer=f"{params.hero} carried {params.gift} back to the people, and the gate shone with new favor.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a swear in a story?",
            answer="A swear is a solemn promise, often made with strong feeling or honor.",
        ),
        QAItem(
            question="What is an assumption?",
            answer="An assumption is a guess someone treats as true before knowing the full facts.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that changes what someone thought would happen.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} title={e.title!r} label={e.label!r} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(hero="Ari", title="the tide watcher", place="the quiet harbor", gift="a bright shell"),
    StoryParams(hero="Hera", title="the bridge singer", place="the old hill", gift="a sunstone"),
    StoryParams(hero="Galen", title="the gate guardian", place="the river gate", gift="a silver key"),
]


def generate_many(params_list: list[StoryParams]) -> list[StorySample]:
    return [generate(p) for p in params_list]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ready/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ready/2."))
        atoms = sorted(set(asp.atoms(model, "story_ready")))
        for a in atoms:
            print(a)
        return

    if args.all:
        samples = generate_many(CURATED)
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        rng = random.Random(base_seed)
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
