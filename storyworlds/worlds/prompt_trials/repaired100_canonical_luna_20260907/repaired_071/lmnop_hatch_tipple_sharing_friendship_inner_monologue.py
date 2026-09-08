#!/usr/bin/env python3
"""
Standalone storyworld: a slice-of-life friendship story about sharing a hatch
and a tipple while learning what the letters lmnop mean to someone else.
"""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "sunny kitchen": {"warm": True},
    "school art room": {"warm": False},
    "apartment balcony": {"warm": True},
    "grandmother's porch": {"warm": True},
}

HEROES = ["Luna", "Mara", "Nico", "Pia", "Sam"]
FRIENDS = ["Ivo", "Tess", "Rin", "Jo", "Bea"]
OBJECTS = ["wooden hatch", "garden hatch", "little hatch"]
TIPPLES = ["apple tipple", "berry tipple", "lemon tipple"]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    hatch: str
    tipple: str
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join(
        [params.place, params.hero, params.friend, params.hatch, params.tipple]
    )
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def build_world(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hatch not in OBJECTS:
        raise StoryError(f"Unknown hatch: {params.hatch}.")
    if params.tipple not in TIPPLES:
        raise StoryError(f"Unknown tipple: {params.tipple}.")

    rng = random.Random(_stable_seed(params) ^ 0x51A7)
    w = World(params)

    hero = w.add(Entity("hero", "child", params.hero, memes={"worry": 0.0, "trust": 0.0}))
    friend = w.add(
        Entity("friend", "child", params.friend, memes={"worry": 0.0, "trust": 0.0})
    )
    hatch = w.add(
        Entity(
            "hatch",
            "object",
            params.hatch,
            meters={"closed": 1.0, "weight": 1.0},
        )
    )
    tipple = w.add(
        Entity(
            "tipple",
            "drink",
            params.tipple,
            meters={"full": 1.0, "cups": 2.0},
        )
    )

    w.facts.update(
        hero=hero,
        friend=friend,
        hatch=hatch,
        tipple=tipple,
        place=params.place,
        lmnop="lmnop",
        shared=False,
        opened=False,
        repaired=False,
    )

    openings = [
        f"In the {params.place}, {params.hero} was practicing the letters lmnop on a scrap of paper.",
        f"{params.hero} spent a quiet afternoon in the {params.place}, where the letters lmnop marched across a paper napkin.",
        f"The {params.place} felt ordinary until {params.hero} noticed the little letters lmnop beside the {params.hatch}.",
    ]
    w.say(rng.choice(openings))
    w.say(
        f"{params.friend} arrived carrying two clean cups and a small pitcher of {params.tipple}."
    )
    w.say(
        f'"I brought enough for both of us," {params.friend} said. '
        f'"Then we can finish the lmnop game together."'
    )
    w.say(
        f"{params.hero} smiled, though a small thought fluttered inside: "
        f'"What if {params.friend} wants the best cup, and I choose badly?"'
    )

    w.para()
    w.say(
        f"At the edge of the room, the {params.hatch} had stuck halfway open. "
        f"It covered the box of letter tiles they needed."
    )
    w.say(
        f"{params.hero} pulled once, but the {params.hatch} did not move. "
        f"The handle felt cold and the box remained just out of reach."
    )
    w.say(
        f'"We can try together," {params.hero} said. "You lift while I slide the box."'
    )
    w.say(
        f'"I was hoping to do it myself," {params.friend} admitted. '
        f'"But I do want to share the tiles."'
    )
    hero.memes["worry"] += 1.0
    friend.memes["worry"] += 1.0
    w.say(
        f"{params.hero} thought, \"Sharing does not mean doing everything for someone. "
        f"It can mean making room for both of us.\""
    )

    w.para()
    w.say(
        f"They counted to three and lifted the {params.hatch} together. "
        f"The box slid free, and the letters clattered softly onto the table."
    )
    hatch.meters["closed"] = 0.0
    w.facts["opened"] = True
    w.say(
        f"{params.friend} poured the {params.tipple} into two cups, stopping when each cup held the same amount."
    )
    w.say(
        f'"You take the cup with the blue mark," {params.friend} offered. '
        f'"I will take the one with the tiny crack."'
    )
    w.say(
        f'"Thank you," {params.hero} replied. "Let us trade halfway through the lmnop game."'
    )
    w.say(
        f"They arranged l, m, n, o, and p in a crooked row. "
        f"The game became easier because neither friend had to guard the tiles or the drink."
    )
    tipple.meters["cups"] = 0.0
    w.facts["shared"] = True
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0

    w.para()
    w.say(
        f"After the last tile was placed, the {params.hatch} slipped shut again with a gentle click."
    )
    w.say(
        f"{params.hero} and {params.friend} put the empty cups beside the box and fixed the loose hatch handle with an adult's help."
    )
    hatch.meters["closed"] = 1.0
    w.facts["repaired"] = True
    w.say(
        f"{params.friend} looked at the shared row of letters. "
        f'"Next time, we should start with two cups and two pairs of hands."'
    )
    w.say(
        f'"And no one has to wonder alone," {params.hero} said.'
    )
    w.say(
        f"{params.hero} felt the worried thought grow smaller. "
        f"The {params.hatch} was secure, the {params.tipple} had been shared, and friendship made the ordinary afternoon feel bright."
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a slice-of-life friendship story using the words lmnop, {p.hatch}, and {p.tipple}.",
        f"Show {p.hero} and {p.friend} sharing a {p.tipple} while opening a {p.hatch}.",
        "Include an inner monologue that changes into a spoken conversation and a cooperative choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Where were {p.hero} and {p.friend} spending time?",
            answer=f"{p.hero} and {p.friend} were spending time in the {p.place}.",
        ),
        QAItem(
            question=f"What was stuck?",
            answer=f"The {p.hatch} was stuck halfway open and covered the box of letter tiles.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.friend} open the hatch?",
            answer=f"They lifted the {p.hatch} together while {p.hero} slid the letter-tile box free.",
        ),
        QAItem(
            question=f"How did the friends share the {p.tipple}?",
            answer=f"{p.friend} poured the {p.tipple} into two equal cups, and they agreed to trade cups halfway through the lmnop game.",
        ),
        QAItem(
            question=f"What did {p.hero} learn about sharing?",
            answer=f"{p.hero} learned that sharing can mean making room for both people instead of doing everything alone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use, enjoy, or help with something together.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship in which people listen, help, and enjoy time together.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a person has inside their mind.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life storyworld about lmnop, a hatch, tipple, and friendship."
    )
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--hatch", choices=OBJECTS)
    parser.add_argument("--tipple", choices=TIPPLES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    available = [name for name in FRIENDS if name != hero]
    friend = args.friend or rng.choice(available)
    hatch = args.hatch or rng.choice(OBJECTS)
    tipple = args.tipple or rng.choice(TIPPLES)
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(
        place=place,
        hero=hero,
        friend=friend,
        hatch=hatch,
        tipple=tipple,
        seed=args.seed,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind} meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_story(P) :- valid_place(P), has_hatch(P), has_tipple(P).
"""


def asp_facts() -> str:
    import asp

    facts = []
    for place in PLACES:
        facts.append(asp.fact("place", place))
        facts.append(asp.fact("has_hatch", place))
        facts.append(asp.fact("has_tipple", place))
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str]]:
    return {(place,) for place in PLACES}


def asp_verify() -> int:
    try:
        import asp
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = valid_combos()
    if actual != expected:
        print("ASP/Python mismatch.")
        print("Only in ASP:", sorted(actual - expected))
        print("Only in Python:", sorted(expected - actual))
        return 1
    for index, place in enumerate(PLACES):
        sample = generate(
            StoryParams(
                place=place,
                hero=HEROES[index % len(HEROES)],
                friend=FRIENDS[index % len(FRIENDS)],
                hatch=OBJECTS[index % len(OBJECTS)],
                tipple=TIPPLES[index % len(TIPPLES)],
                seed=index,
            )
        )
        if not sample.story or "lmnop" not in sample.story:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(expected)} places).")
    return 0


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible places:")
        for place in PLACES:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(PLACES):
            hero = HEROES[index % len(HEROES)]
            friend = FRIENDS[index % len(FRIENDS)]
            if friend == hero:
                friend = FRIENDS[(index + 1) % len(FRIENDS)]
            samples.append(
                generate(
                    StoryParams(
                        place=place,
                        hero=hero,
                        friend=friend,
                        hatch=OBJECTS[index % len(OBJECTS)],
                        tipple=TIPPLES[index % len(TIPPLES)],
                        seed=base_seed + index,
                    )
                )
            )
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
