#!/usr/bin/env python3
"""
Story world: a heartwarming parade story with a sailor, infantry, and a twist.

A small town plans a parade, but rain, a lost drum ribbon, and a shy sailor
change the day. The infantry helps, the sailor finds a new place in the march,
and the twist turns into a warm ending where everyone belongs.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str = "harbor square"
    sailor_name: str = "Nell"
    infantry_name: str = "Pip"
    parade: str = "spring parade"
    twist: str = "the sailor is afraid of marching in front of a crowd"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = [
    "harbor square",
    "market lane",
    "school yard",
    "lamp-lit plaza",
    "river steps",
]

SAILOR_NAMES = ["Nell", "Mara", "June", "Ada", "Toby"]
INFANTRY_NAMES = ["Pip", "Owen", "Sana", "Reed", "Iris"]
PARADES = [
    "spring parade",
    "harvest parade",
    "lantern parade",
    "welcome parade",
    "harbor parade",
]

TWISTS = [
    "the sailor is afraid of marching in front of a crowd",
    "the infantry band has only one drum with a torn ribbon",
    "the parade banner is too heavy for the youngest marchers",
    "the sailor knows the best route through the square, but forgets the words to the song",
    "the infantry captain expected a loud show, but the crowd needs something gentler",
]


ASP_RULES = r"""
parade_ready(P) :- parade_name(P), route_clear(P), music_ready(P), hearts_brave(P).
heartwarming(E) :- helped(E), shared_job(E), smiled(E).
twist_resolved(T) :- twist_name(T), understood(T), kind_choice(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("parade_name", "parade"))
    lines.append(asp.fact("twist_name", "twist"))
    lines.append(asp.fact("route_clear", "parade"))
    lines.append(asp.fact("music_ready", "parade"))
    lines.append(asp.fact("hearts_brave", "parade"))
    lines.append(asp.fact("helped", "sailor"))
    lines.append(asp.fact("shared_job", "sailor"))
    lines.append(asp.fact("smiled", "sailor"))
    lines.append(asp.fact("understood", "twist"))
    lines.append(asp.fact("kind_choice", "twist"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show parade_ready/1.\n#show heartwarming/1.\n#show twist_resolved/1.")
    )
    atoms = set()
    for sym in model:
        args = []
        for a in sym.arguments:
            if a.type.name == "String":
                args.append(a.string)
            elif a.type.name == "Number":
                args.append(a.number)
            else:
                args.append(a.name)
        atoms.add((sym.name, tuple(args)))

    want = {
        ("parade_ready", ("parade",)),
        ("heartwarming", ("sailor",)),
        ("twist_resolved", ("twist",)),
    }
    if atoms == want:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming parade story world with a sailor, infantry, and a twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sailor")
    ap.add_argument("--infantry")
    ap.add_argument("--parade", choices=PARADES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    sailor_name = args.sailor or rng.choice(SAILOR_NAMES)
    infantry_name = args.infantry or rng.choice([n for n in INFANTRY_NAMES if n != sailor_name])
    if sailor_name == infantry_name:
        raise StoryError("The sailor and infantry should be different characters.")
    return StoryParams(
        place=place,
        sailor_name=sailor_name,
        infantry_name=infantry_name,
        parade=args.parade or rng.choice(PARADES),
        twist=args.twist or rng.choice(TWISTS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.parade not in PARADES:
        raise StoryError(f"Unknown parade: {params.parade}")
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")

    rng = random.Random(
        params.seed if params.seed is not None else f"{params.place}:{params.sailor_name}:{params.infantry_name}:{params.parade}:{params.twist}"
    )
    world = World()

    sailor = world.add(
        Entity(
            id="sailor",
            kind="character",
            label=params.sailor_name,
            phrase=f"{params.sailor_name}, a sailor with a careful smile",
            meters={"step": 0.0, "fear": 0.0, "hope": 1.0},
            memes={"brave": 0.2, "lonely": 0.6, "warmth": 0.1},
        )
    )
    infantry = world.add(
        Entity(
            id="infantry",
            kind="character",
            label=params.infantry_name,
            phrase=f"{params.infantry_name}, an infantry helper with steady boots",
            meters={"drum": 1.0, "ribbon": 1.0, "march": 0.0},
            memes={"proud": 0.6, "kind": 0.5, "busy": 0.3},
        )
    )
    banner = world.add(
        Entity(
            id="banner",
            kind="thing",
            label="parade banner",
            phrase="a parade banner with bright blue streamers",
            owner="infantry",
            meters={"flutter": 1.0, "wet": 0.0, "lift": 0.0},
            memes={"joy": 1.0, "worry": 0.0},
        )
    )

    world.say(f"At {params.place}, people gathered early for the {params.parade}.")
    world.say(f"{params.sailor_name} came from the harbor to watch, and {params.infantry_name} arrived with the infantry line and the parade banner.")
    world.say(
        f"Then the twist appeared: {params.twist}."
    )
    world.say(
        f'“I do not want to spoil the parade,” {params.sailor_name} said softly.'
    )
    world.say(
        f'“You will not spoil it,” {params.infantry_name} said. “We will make room for you.”'
    )

    if "afraid" in params.twist:
        sailor.meters["fear"] = 1.0
        sailor.memes["lonely"] = 0.9
        world.say(
            f"{params.sailor_name} stood by the steps, holding a cap tight in both hands while the music warmed up."
        )
        world.say(
            f'{params.infantry_name} asked, “Could you help us by leading the first wave from the side?”'
        )
        world.say(
            f'“From the side?” {params.sailor_name} asked.'
        )
        world.say(
            f'“Yes,” said {params.infantry_name}. “Your sea-spotter eyes are the best in town. You can call the turns when the crowd cannot see them.”'
        )
        sailor.meters["fear"] = 0.2
        sailor.memes["hope"] = 0.9
        banner.meters["lift"] = 1.0
        world.say(
            f"{params.sailor_name} nodded and took a small whistle instead of a front-row place."
        )
        world.say(
            f"The infantry marched, and {params.sailor_name} guided the line around puddles, ribbons, and a laughing puppy."
        )
    elif "drum" in params.twist:
        infantry.meters["ribbon"] = 0.2
        world.say(
            f"The infantry's drum ribbon had torn, and the bright banner drooped a little in the rain."
        )
        world.say(
            f'“We can still keep time,” said {params.infantry_name}, “but it needs a new ribbon.”'
        )
        world.say(
            f'“I have one,” said {params.sailor_name}, lifting a spare blue sail tie from a pocket.'
        )
        world.say(
            f'“That will hold?” asked {params.infantry_name}.'
        )
        world.say(
            f'“It holds boats,” said {params.sailor_name}, smiling. “It can hold a drum ribbon too.”'
        )
        infantry.meters["ribbon"] = 1.0
        banner.meters["lift"] = 1.0
        world.say(
            f"The infantry beat the drum again, and the parade stepped forward in a safer, steadier line."
        )
    elif "heavy" in params.twist:
        banner.meters["lift"] = 0.2
        world.say(
            f"The parade banner was too heavy for the youngest marchers, and their arms trembled."
        )
        world.say(
            f'“I can carry one end,” said {params.sailor_name}.'
        )
        world.say(
            f'“And we can share the other end in pairs,” said {params.infantry_name}.'
        )
        world.say(
            f'“Would that still look like a parade?” asked a little marcher.'
        )
        world.say(
            f'“Yes,” said {params.infantry_name}. “A good parade is strongest when everyone can help.”'
        )
        banner.meters["lift"] = 1.0
        world.say(
            f"So the banner rose evenly, and the youngest marchers walked with bright, proud steps."
        )
    elif "forgets the words" in params.twist:
        sailor.memes["worry"] = 1.0
        world.say(
            f"{params.sailor_name} knew the route through the square but forgot the parade song at the very first note."
        )
        world.say(
            f'“I remember,” said {params.infantry_name}, “you hum the start, and we will answer.”'
        )
        world.say(
            f'“That sounds kind,” said {params.sailor_name}. “I can hum.”'
        )
        world.say(
            f"So the sailor hummed the tune, and the infantry sang it back, filling the square with a warm, wobbly chorus."
        )
        sailor.memes["warmth"] = 1.0
    else:
        world.say(
            f"{params.infantry_name} had planned a loud parade, but the crowd looked tired after the rain."
        )
        world.say(
            f'“Maybe we need a gentler start,” said {params.sailor_name}.'
        )
        world.say(
            f'“A gentler start can still be joyful,” said {params.infantry_name}.'
        )
        world.say(
            f"So the parade began with soft steps, a wave from the sailors, and a slow drum that made the children clap instead of cover their ears."
        )
        banner.meters["lift"] = 1.0

    world.say(
        f'The crowd began to smile, because {params.sailor_name} and {params.infantry_name} were not trying to look perfect; they were trying to help.'
    )
    world.say(
        f'“Ready?” asked {params.infantry_name}.'
    )
    world.say(
        f'“Ready,” said {params.sailor_name}, and the answer sounded much braver than before.'
    )
    world.say(
        f"The parade moved through {params.place}, with the infantry stepping in time and the sailor helping where the day needed it most."
    )
    world.say(
        f"In the end, the twist did not ruin the parade. It made it warmer."
    )
    world.say(
        f"The sailor found a place in the story, the infantry found a gentler way to march, and the whole square cheered when the banner passed by."
    )

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        banner=banner,
        place=params.place,
        parade=params.parade,
        twist=params.twist,
    )

    prompts = [
        f"Write a heartwarming story about a parade at {params.place} with {params.sailor_name} and {params.infantry_name}.",
        f"Include a twist where {params.twist}, and show how the characters help each other.",
        f"Make the story child-facing, with a short dialogue exchange and a happy ending image.",
    ]

    story_qa = [
        QAItem(
            question="Where did the parade happen?",
            answer=f"The parade happened at {params.place}.",
        ),
        QAItem(
            question="Who were the two main helpers?",
            answer=f"The two main helpers were {params.sailor_name}, the sailor, and {params.infantry_name}, from the infantry.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {params.twist}.",
        ),
        QAItem(
            question="How did the twist change the parade?",
            answer="It made the characters work together in a kinder, smarter way.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the parade moving happily and everyone feeling included.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a happy public march or celebration where people walk together, often with music or decorations.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry is a group of soldiers who usually move and work on foot.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works on or travels by water, often on a boat or ship.",
        ),
    ]

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent.label} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show parade_ready/1.\n#show heartwarming/1.\n#show twist_resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                sailor_name=SAILOR_NAMES[i % len(SAILOR_NAMES)],
                infantry_name=INFANTRY_NAMES[i % len(INFANTRY_NAMES)],
                parade=PARADES[i % len(PARADES)],
                twist=TWISTS[i % len(TWISTS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
