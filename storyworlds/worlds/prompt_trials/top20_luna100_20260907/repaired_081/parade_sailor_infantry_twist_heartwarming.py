#!/usr/bin/env python3
"""
Story world: a heartwarming parade story about a sailor, infantry, and a
surprising turn.

A young sailor wants to march proudly with an infantry band, but a small parade
problem reveals that the quietest helper may be carrying the biggest hope.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
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


@dataclass
class Parade:
    name: str
    route: str
    weather: str


@dataclass
class StoryParams:
    parade: str = "Harbor Homecoming Parade"
    sailor_name: str = "Luna"
    infantry_name: str = "Mara"
    instrument: str = "small brass bell"
    twist: str = "hidden_guest"
    style: str = "heartwarming"
    seed: Optional[int] = None


@dataclass
class World:
    parade: Parade
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


PARADES = {
    "Harbor Homecoming Parade": Parade(
        "Harbor Homecoming Parade", "the bright harbor road", "a soft golden morning"
    ),
    "Lantern Day Parade": Parade(
        "Lantern Day Parade", "the old market street", "a warm evening breeze"
    ),
    "River Welcome Parade": Parade(
        "River Welcome Parade", "the riverside avenue", "a clear blue afternoon"
    ),
}

SAILOR_NAMES = ["Luna", "Niko", "Pia", "Sol", "Tessa"]
INFANTRY_NAMES = ["Mara", "Ivo", "June", "Rafi", "Anya"]
INSTRUMENTS = ["small brass bell", "silver drum", "wooden flute", "bright bugle"]

TWISTS = {
    "hidden_guest": {
        "problem": "The sailor's place in the parade was empty because the sailor kept slipping away before the march began.",
        "clue": "The infantry helper noticed tiny wet footprints leading from the parade route to the old harbor steps.",
        "change": "They followed the footprints and found a shy child sailor hiding there with a frightened rescue dog.",
        "ending": "The rescue dog trotted beside the parade, wearing a ribbon, while everyone clapped for the smallest sailor.",
        "lesson": "kindness can make room for someone who is afraid",
    },
    "missing_music": {
        "problem": "The parade's opening tune could not begin because the sailor's instrument made no sound.",
        "clue": "The infantry helper saw that the instrument's loose cord was tangled around a remembrance ribbon.",
        "change": "They untangled the ribbon, repaired the cord, and invited the sailor to choose a gentler opening note.",
        "ending": "The first soft note floated over the crowd, and the whole parade found its happy rhythm.",
        "lesson": "careful listening can turn a mistake into a welcome",
    },
    "rain_flag": {
        "problem": "Rain began just before the parade, and the sailor's flag drooped against the muddy road.",
        "clue": "The infantry helper noticed that the flag was dry beneath the parade cart's canvas roof.",
        "change": "They made a light frame from spare sticks and covered the flag with a clear, safe sleeve.",
        "ending": "The flag rose bright above the rain, and children followed it with shining faces.",
        "lesson": "a thoughtful plan can protect what matters",
    },
    "quiet_march": {
        "problem": "The sailor worried that a healing foot would keep them from joining the parade.",
        "clue": "The infantry helper saw that the route had a shorter garden path with benches along it.",
        "change": "They changed the march into a welcoming walk, adding pauses where every tired marcher could rest.",
        "ending": "The sailor rang the bell from a garden bench, and the infantry waved back at every pause.",
        "lesson": "belonging matters more than keeping exactly the same pace",
    },
}

ASP_RULES = r"""
parade(P) :- parade_name(P).
sailor(S) :- sailor_name(S).
infantry(I) :- infantry_name(I).
twist_done(T) :- twist(T), resolved(T).
heartwarming(T) :- twist_done(T), kindness(T).
ready(P) :- parade_name(P), safe(P), inclusive(P).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name in PARADES:
        lines.append(asp.fact("parade_name", name))
    lines.extend(
        [
            asp.fact("sailor_name", "sailor"),
            asp.fact("infantry_name", "infantry"),
            asp.fact("twist", "story_twist"),
            asp.fact("resolved", "story_twist"),
            asp.fact("kindness", "story_twist"),
            asp.fact("safe", "Harbor Homecoming Parade"),
            asp.fact("inclusive", "Harbor Homecoming Parade"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show ready/1.\n#show heartwarming/1.\n#show twist_done/1."
        )
    )
    found = set()
    for symbol in model:
        args = tuple(
            a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name
            for a in symbol.arguments
        )
        found.add((symbol.name, args))
    wanted = {
        ("ready", ("Harbor Homecoming Parade",)),
        ("heartwarming", ("story_twist",)),
        ("twist_done", ("story_twist",)),
    }
    if found == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(found))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade story about a sailor, infantry, and a twist."
    )
    parser.add_argument("--parade", choices=list(PARADES))
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
    parser.add_argument("--instrument", choices=INSTRUMENTS)
    parser.add_argument("--twist", choices=list(TWISTS))
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
    sailor = args.sailor or rng.choice(SAILOR_NAMES)
    infantry = args.infantry or rng.choice([name for name in INFANTRY_NAMES if name != sailor])
    if sailor == infantry:
        raise StoryError("The sailor and infantry helper must be different people.")
    return StoryParams(
        parade=args.parade or rng.choice(list(PARADES)),
        sailor_name=sailor,
        infantry_name=infantry,
        instrument=args.instrument or rng.choice(INSTRUMENTS),
        twist=args.twist or rng.choice(list(TWISTS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.parade not in PARADES:
        raise StoryError(f"Unknown parade: {params.parade}")
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")
    if params.sailor_name == params.infantry_name:
        raise StoryError("The sailor and infantry helper must be different people.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.parade}:{params.sailor_name}:{params.infantry_name}:{params.twist}"
    )
    parade = PARADES[params.parade]
    twist = TWISTS[params.twist]
    world = World(parade)

    sailor = world.add(
        Entity(
            "sailor",
            "character",
            params.sailor_name,
            "a young sailor in a neat blue uniform",
            meters={"confidence": 0.4, "energy": 0.8},
            memes={"hope": 0.8, "worry": 0.5},
        )
    )
    infantry = world.add(
        Entity(
            "infantry",
            "character",
            params.infantry_name,
            "an observant infantry helper",
            meters={"patience": 0.9, "readiness": 0.8},
            memes={"kindness": 1.0, "curiosity": 0.7},
        )
    )
    instrument = world.add(
        Entity(
            "instrument",
            "thing",
            params.instrument,
            owner="sailor",
            meters={"condition": 0.7, "sound": 0.4},
            memes={"memory": 0.8, "joy": 0.6},
        )
    )

    world.say(
        f"On {parade.weather}, {params.sailor_name} polished {instrument.phrase} for the {params.parade}."
    )
    world.say(
        f"The sailor hoped to march with the infantry along {parade.route}, where families were already gathering."
    )
    world.say(
        f"“I want everyone to hear us,” {params.sailor_name} said. “Then let us make sure everyone has a place,” {params.infantry_name} replied."
    )
    world.say(twist["problem"])
    sailor.meters["confidence"] -= 0.2
    sailor.memes["worry"] += 0.4
    world.say(
        f"{params.sailor_name} tried to solve the trouble quickly, but the parade still did not feel ready."
    )
    world.say(
        f"“What are you noticing?” {params.infantry_name} asked. “I notice that I am looking only at the march,” {params.sailor_name} admitted."
    )
    world.say(
        f"Instead of hurrying, {params.infantry_name} checked the route, the waiting families, and the quiet spaces beside the road."
    )
    world.say(twist["clue"])
    world.say(
        f"That clue changed the plan. {params.sailor_name} carried {instrument.phrase} carefully while {params.infantry_name} led the way."
    )
    world.say(twist["change"])

    instrument.meters["condition"] = 1.0
    instrument.meters["sound"] = 1.0
    sailor.meters["confidence"] = 1.0
    sailor.memes["worry"] = 0.1
    sailor.memes["belonging"] = 1.0
    infantry.memes["kindness"] = 1.0
    world.say(
        f"The sailor was no longer trying to make the parade perfect; the sailor was helping make it welcoming."
    )
    world.say(
        f"“Ready?” {params.sailor_name} asked. “Ready together,” {params.infantry_name} answered."
    )
    world.say(twist["ending"])
    world.say(
        f"The parade moved on, but its warmest sound was not the loudest one: it was the cheer that told everyone, “You may walk with us.”"
    )

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        instrument=instrument,
        resolved=True,
        kindness=True,
        twist=params.twist,
        lesson=twist["lesson"],
        clue=twist["clue"],
        change=twist["change"],
    )

    prompts = [
        f"Write a heartwarming story about sailor {params.sailor_name} joining the {params.parade}.",
        f"Include infantry helper {params.infantry_name}, {params.instrument}, and a surprising but gentle twist.",
        f"Show how a parade problem changes into an act of kindness and belonging.",
    ]

    story_qa = [
        QAItem(
            question="What problem interrupted the parade?",
            answer=twist["problem"],
        ),
        QAItem(
            question=f"What clue did {params.infantry_name} notice?",
            answer=twist["clue"],
        ),
        QAItem(
            question="How did the characters change their plan?",
            answer=twist["change"],
        ),
        QAItem(
            question="What was the heartwarming twist?",
            answer=twist["ending"],
        ),
        QAItem(
            question=f"What lesson did {params.sailor_name} learn?",
            answer=f"{params.sailor_name} learned that {twist['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people move together while music, flags, or decorations help celebrate an event.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry are soldiers trained to serve and move on foot.",
        ),
        QAItem(
            question="Why can a twist make a story meaningful?",
            answer="A twist can reveal something unexpected that changes how the characters understand the problem and makes the ending more powerful.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
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
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
        print(f"facts: {sample.world.facts}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show ready/1.\n#show heartwarming/1.\n#show twist_done/1."
            )
        )
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for parade_name in PARADES:
            params = StoryParams(
                parade=parade_name,
                sailor_name=SAILOR_NAMES[0],
                infantry_name=INFANTRY_NAMES[0],
                instrument=INSTRUMENTS[0],
                twist=list(TWISTS)[len(samples) % len(TWISTS)],
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show ready/1.\n#show heartwarming/1.\n#show twist_done/1."
            )
        )
        print("ASP model:")
        for symbol in model:
            print(symbol)
        return

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
