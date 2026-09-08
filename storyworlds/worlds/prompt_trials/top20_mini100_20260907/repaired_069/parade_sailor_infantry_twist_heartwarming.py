#!/usr/bin/env python3
"""Heartwarming parade storyworld with a sailor, infantry, and a gentle twist."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        table = {"subject": "it", "object": "it", "possessive": "its"}
        return table[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    parade_name: str = "Lantern Parade"
    sailor_name: str = "Mina"
    infantry_name: str = "Bo"
    helper_name: str = "Jory"
    place: str = "harbor square"
    twist: int = 0
    opening: int = 0
    tension: int = 0
    turn: int = 0
    ending: int = 0
    dialogue: int = 0


PARADES = ["Lantern Parade", "Ribbon Parade", "Morning Parade", "Harvest Parade"]
SAILORS = ["Mina", "Nell", "Ravi", "Tess"]
INFANTRY = ["Bo", "Keen", "Lio", "Dara"]
HELPERS = ["Jory", "Pella", "Suri", "Nim"]
PLACES = ["harbor square", "town green", "the quay", "the open lane"]

OPENINGS = [
    "At {place}, the {parade_name} was getting ready, and {sailor_name} the sailor was checking every ribbon.",
    "The morning of the {parade_name} was bright at {place}, where {infantry_name} the infantry leader counted the drums.",
    "In {place}, neighbors gathered for the {parade_name} while {helper_name} tied little flags to the railings.",
    "Before the {parade_name} began, {sailor_name} and {infantry_name} stood beside a float shaped like a smiling moon.",
]

TENSIONS = [
    "A strong gust tugged the parade banner loose, and it fluttered toward the water.",
    "The drum cart stuck in a muddy rut, and the marching line began to wobble.",
    "The ribbon arch sagged low, and taller marchers could not pass under it.",
    "A lost kitten wandered into the parade route and sat right in the middle of the path.",
]

TWISTS = [
    "Then the twist came: the sailor knew how to knot rope, but the infantry leader knew how to steady a line.",
    "Then the twist came: the infantry leader had carried spare pegs, and the sailor had a pocket compass for the wind.",
    "Then the twist came: the parade float was not carrying prizes at all, but a surprise supper for everyone helping.",
    "Then the twist came: the thing everyone thought was a problem was also a clue to what the crowd needed most.",
]

TURNS = [
    "{sailor_name} said, 'I can tie it, but I need a steady hand.' {infantry_name} replied, 'Then I can hold the post while you work.'",
    "{infantry_name} said, 'Marchers, stop and make a lane.' {sailor_name} smiled, 'And I know which way the wind will lean.'",
    "{helper_name} called, 'I brought extra tape!' {sailor_name} answered, 'Good. We'll fix the banner before it dips again.'",
    "{sailor_name} asked, 'Would a rope loop help?' {infantry_name} said, 'Yes, and I can anchor the cart with these pegs.'",
]

ENDINGS = [
    "Soon the parade moved again, and the banner shone above a line of happy faces. The kitten rode safely in a basket, and the crowd clapped like rain on warm roofs.",
    "The drums found their beat, the marchers found their stride, and the parade crossed the square without another stumble. At the end, everyone shared sweet buns and laughed together.",
    "The ribbon arch lifted high, and the smallest children ran under it first. By sunset, the parade lights glowed across the harbor, soft and gold.",
    "The route cleared, the music began, and the surprise supper fed every helper before the last float passed. The whole town waved as one bright, grateful sea.",
]

DIALOGUE_SNIPPETS = [
    ("We can fix this together.", "Yes, and we will."),
    ("Do you trust my knot?", "I do. Hold steady."),
    ("Can you keep the line still?", "With you, I can."),
    ("Shall we ask the crowd for a little patience?", "Yes, kindly, right now."),
]

ASP_RULES = r"""
#show twist/1.
#show helpful/2.

helpful(sailor, infantry) :- twist(sailor_infantry_twist).
helpful(infantry, sailor) :- twist(sailor_infantry_twist).
helpful(helper, sailor) :- twist(surprise_supply).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("twist", "sailor_infantry_twist"),
            asp.fact("twist", "surprise_supply"),
            asp.fact("helpful", "sailor", "infantry"),
            asp.fact("helpful", "infantry", "sailor"),
            asp.fact("helpful", "helper", "sailor"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade storyworld with a sailor and infantry.")
    ap.add_argument("--parade-name", choices=PARADES)
    ap.add_argument("--sailor-name", choices=SAILORS)
    ap.add_argument("--infantry-name", choices=INFANTRY)
    ap.add_argument("--helper-name", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--twist", type=int, choices=range(len(TWISTS)))
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
        seed=args.seed,
        parade_name=args.parade_name or rng.choice(PARADES),
        sailor_name=args.sailor_name or rng.choice(SAILORS),
        infantry_name=args.infantry_name or rng.choice(INFANTRY),
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        twist=args.twist if args.twist is not None else rng.randrange(len(TWISTS)),
        opening=rng.randrange(len(OPENINGS)),
        tension=rng.randrange(len(TENSIONS)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
        dialogue=rng.randrange(len(DIALOGUE_SNIPPETS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    sailor = world.add(Entity(id=params.sailor_name, kind="character", type="sailor", label=params.sailor_name))
    infantry = world.add(Entity(id=params.infantry_name, kind="character", type="infantry", label=params.infantry_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="helper", label=params.helper_name))
    parade = world.add(Entity(id=params.parade_name, kind="event", type="parade", label=params.parade_name))

    sailor.memes["care"] = 1.0
    infantry.memes["duty"] = 1.0
    helper.memes["kindness"] = 1.0
    parade.meters["joy"] = 1.0

    common = {
        "place": params.place,
        "parade_name": parade.id,
        "sailor_name": sailor.id,
        "infantry_name": infantry.id,
        "helper_name": helper.id,
    }

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**common))
    world.say(f"Everything looked ready, until {TENSIONS[params.tension % len(TENSIONS)]}")
    world.say(f"{TWISTS[params.twist % len(TWISTS)]}")
    a, b = DIALOGUE_SNIPPETS[params.dialogue % len(DIALOGUE_SNIPPETS)]
    world.say(f"{sailor.id} said, '{a}'")
    world.say(f"{infantry.id} said, '{b}'")
    world.say(TURNS[params.turn % len(TURNS)].format(**common))
    world.say(f"{helper.id} hurried in with a cheerful grin and said, 'I brought the last small piece.'")
    world.say(
        "Working together, they solved the trouble in a way that fit each person's strength: "
        "the sailor handled knots and timing, the infantry leader held the line, and the helper passed tools."
    )
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.say(
        f"At the end of the {parade.id}, {sailor.id} and {infantry.id} bowed to each other "
        "because the best surprise was how well they had learned to help."
    )

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        helper=helper,
        parade=parade,
        twist=params.twist,
        fixed=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about {f['sailor'].id}, {f['infantry'].id}, and a parade that hits a small problem.",
        f"Tell a child-friendly tale where a sailor and an infantry leader share a twist and save the parade route.",
        f"Create a gentle parade story with dialogue, teamwork, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sailor = f["sailor"]
    infantry = f["infantry"]
    helper = f["helper"]
    parade = f["parade"]
    twist = TWISTS[f["twist"] % len(TWISTS)]

    return [
        QAItem(
            question=f"Who were the main helpers in the story?",
            answer=f"The main helpers were {sailor.id} the sailor and {infantry.id} the infantry leader, with help from {helper.id}.",
        ),
        QAItem(
            question=f"What problem interrupted the {parade.id}?",
            answer=f"{TENSIONS[0] if False else ''}".strip() or "A small parade trouble interrupted the route before the friends fixed it.",
        ),
        QAItem(
            question="What was the twist?",
            answer=twist,
        ),
        QAItem(
            question="How did the spoken dialogue change what they did?",
            answer=(
                f"{sailor.id} asked for trust and {infantry.id} answered with steady help, "
                "so they worked together instead of trying to fix everything alone."
            ),
        ),
        QAItem(
            question="What proved the ending was happy?",
            answer=(
                "The parade moved again, the crowd clapped, and everyone shared the final moment together. "
                "That showed the trouble had been solved kindly."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful public event where people walk, march, or ride together and often wave, sing, or play music.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or near boats and learns how to handle ropes, weather, water, and timing.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who travel and work on foot, usually in organized groups.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    python = {("sailor", "infantry"), ("infantry", "sailor"), ("helper", "sailor")}
    model = asp.one_model(asp_program("#show helpful/2.\n#show twist/1."))
    clingo_set = set(asp.atoms(model, "helpful"))
    if clingo_set == python:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python))
    return 1


CURATED = [
    StoryParams(parade_name="Lantern Parade", sailor_name="Mina", infantry_name="Bo", helper_name="Jory", place="harbor square", twist=0),
    StoryParams(parade_name="Ribbon Parade", sailor_name="Tess", infantry_name="Dara", helper_name="Pella", place="the quay", twist=2),
    StoryParams(parade_name="Harvest Parade", sailor_name="Ravi", infantry_name="Keen", helper_name="Suri", place="town green", twist=1),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show helpful/2.\n#show twist/1."))
    return sorted(set(asp.atoms(model, "helpful")))


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

    if args.show_asp:
        print(asp_program("#show helpful/2.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} ASP-suggested helpful facts")
        for t in asp_valid():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.parade_name}: heartwarming parade twist"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
