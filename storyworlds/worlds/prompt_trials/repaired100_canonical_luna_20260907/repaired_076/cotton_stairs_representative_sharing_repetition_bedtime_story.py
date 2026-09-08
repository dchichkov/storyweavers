#!/usr/bin/env python3
"""A gentle bedtime StoryWorld about sharing a cotton keepsake on the stairs."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Grandma"
    place: str = "the moonlit house"
    object_name: str = "cotton moon"
    representative: str = "a small white cloud"
    pattern: str = "share"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = ("the moonlit house", "the quiet cottage", "the little blue home")
HELPERS = ("Grandma", "Papa", "Aunt May")
NAMES = ("Luna", "Milo", "Nell", "Theo")
REPRESENTATIVES = (
    "a small white cloud",
    "a silver star",
    "a sleepy blue bird",
)
PATTERNS = ("share", "repeat", "both")
OPENINGS = (
    "When the house grew quiet, {name} carried a soft cotton treasure to the stairs.",
    "The moon climbed above {place}, and {name} found something gentle waiting by the stairs.",
    "At bedtime, {name} held the cotton keepsake close and listened to the sleepy house.",
)
CLOSINGS = (
    "At last, the cotton moon rested on the newel post, glowing like a tiny promise.",
    "Soon the stairs were still, and the shared keepsake waited softly for morning.",
    "The house fell asleep around them, while the little cotton treasure kept its place between two loving hearts.",
)


def build_world(params: StoryParams) -> World:
    if params.name not in NAMES:
        raise StoryError(f"unknown child name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"unknown helper: {params.helper}")
    if params.place not in PLACES:
        raise StoryError(f"unknown place: {params.place}")
    if params.representative not in REPRESENTATIVES:
        raise StoryError(f"unknown representative: {params.representative}")
    if params.pattern not in PATTERNS:
        raise StoryError(f"unknown sharing pattern: {params.pattern}")

    world = World(params)
    child = world.add(Entity(
        "child", "character", params.name,
        meters={"tiredness": 0.35, "stairs_distance": 0.0},
        memes={"belonging": 0.55, "worry": 0.35},
    ))
    helper = world.add(Entity(
        "helper", "character", params.helper,
        meters={"patience": 1.0},
        memes={"warmth": 1.0},
    ))
    keepsake = world.add(Entity(
        "cotton_keepsake", "object", params.object_name,
        meters={"softness": 1.0},
        memes={"comfort": 0.8},
        owner="child",
    ))
    world.add(Entity(
        "representative", "symbol", params.representative,
        meters={"brightness": 0.7},
        memes={"belonging": 0.6},
    ))
    world.facts.update(
        child=child.label,
        helper=helper.label,
        place=params.place,
        keepsake=keepsake.label,
        representative=params.representative,
        shared=False,
        repeated=False,
        bedtime_ready=False,
    )
    return world


def simulate(world: World) -> World:
    p = world.params
    child = world.entities["child"]
    helper = world.entities["helper"]
    keepsake = world.entities["cotton_keepsake"]

    opening = OPENINGS[p.variant % len(OPENINGS)].format(name=child.label, place=p.place)
    world.say(opening)
    world.say(
        f"It was {keepsake.label}, a little piece of cotton shaped like "
        f"{p.representative}. {child.label} loved it because it represented a "
        "safe place where everyone could belong."
    )
    world.say(
        f"The stairs led from the busy rooms below to the quiet bedroom above, "
        f"and bedtime was almost ready."
    )
    world.para()

    world.say(
        f"{child.label} wanted to carry the cotton treasure upstairs, but "
        f"{helper.label} was still helping another family member settle down."
    )
    world.say(
        f'"Could we share it while we wait?" {helper.label} asked. '
        f'"You may hold it first, and then I will hold it with you."'
    )
    world.say(
        f'"First you, then us," said {child.label}. '
        f'"First you, then us," {helper.label} repeated softly.'
    )
    world.facts["shared"] = True
    world.facts["sharing_rule"] = "first the child holds the cotton keepsake, then child and helper hold it together"
    child.memes["belonging"] = 0.85
    child.memes["worry"] = 0.18
    world.para()

    world.say(
        f"They climbed the stairs slowly. At each step, they repeated the same "
        f"gentle words: 'First you, then us. First you, then us.'"
    )
    world.say(
        f"The repetition made the stairs feel smaller. The cotton {p.representative} "
        f"was not being taken away; it was being shared."
    )
    world.facts["repeated"] = True
    world.facts["steps"] = 6
    world.facts["refrain"] = "First you, then us"
    child.meters["stairs_distance"] = 1.0
    child.meters["tiredness"] = 0.65
    world.para()

    world.say(
        f"At the top, {child.label} placed the cotton treasure between "
        f"{child.label} and {helper.label} on the pillow."
    )
    world.say(
        f'"Now it represents both of us," whispered {child.label}. '
        f'"Both of us," repeated {helper.label}.'
    )
    world.say(
        f"They tucked the keepsake beneath the blanket, where its soft shape "
        f"could remind them that sharing did not make love smaller."
    )
    world.facts["bedtime_ready"] = True
    world.facts["lesson"] = "Sharing can make comfort feel larger, and repetition can make a new path feel safe."
    child.meters["tiredness"] = 1.0
    child.memes["belonging"] = 1.0
    keepsake.memes["comfort"] = 1.0
    world.say(CLOSINGS[p.variant % len(CLOSINGS)])
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle bedtime story about {p.name} sharing {p.object_name} on the stairs.",
        f"Include repetition of the words 'First you, then us' and make {p.representative} represent belonging.",
        "End with a quiet image showing that sharing made comfort feel larger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            f"What did {p.name} carry to the stairs?",
            f"{p.name} carried {p.object_name}, a soft cotton keepsake shaped like {p.representative}.",
        ),
        QAItem(
            f"How did {p.name} and {p.helper} share the keepsake?",
            f"{p.name} held it first, and then {p.name} and {p.helper} held it together.",
        ),
        QAItem(
            "What words did they repeat while climbing?",
            "They repeated, 'First you, then us.' The repetition helped the stairs feel safe and manageable.",
        ),
        QAItem(
            "What did the cotton object represent?",
            f"It represented belonging and a safe place shared by {p.name} and {p.helper}.",
        ),
        QAItem(
            "What changed by the end of the story?",
            f"{p.name} learned that sharing {p.object_name} did not take comfort away; it made comfort feel larger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why can repetition help at bedtime?",
            "Repeating calm words or a familiar routine can make an uncertain moment feel predictable and safe.",
        ),
        QAItem(
            "What does sharing mean in this story?",
            "Sharing means taking turns and making room for another person, rather than treating comfort as something only one person may have.",
        ),
        QAItem(
            "Why are stairs worth climbing slowly?",
            "Going slowly on stairs helps a person pay attention to each step and reduces the chance of rushing or falling.",
        ),
        QAItem(
            "What can a representative object do?",
            "A representative object can stand for an idea or relationship, such as a cotton cloud representing belonging.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """shared(X) :- child(X), holds_first(X), holds_together(X).
safe_climb(X) :- child(X), repeated(X), stairs(X).
bedtime_ready(X) :- shared(X), safe_climb(X), comfort_object(X).
#show bedtime_ready/1.
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp

    p = params or StoryParams()
    child = p.name.lower()
    return "\n".join([
        asp.fact("child", child),
        asp.fact("holds_first", child),
        asp.fact("holds_together", child),
        asp.fact("repeated", child),
        asp.fact("stairs", child),
        asp.fact("comfort_object", child),
    ])


def asp_program(params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    params = StoryParams()
    model = asp.one_model(asp_program(params))
    found = set(asp.atoms(model, "bedtime_ready"))
    expected = {(params.name.lower(),)}
    if found != expected:
        print(f"ASP verification failed: expected {expected}, got {found}")
        return 1
    sample = generate(params)
    checks = (
        "cotton" in sample.story.lower(),
        "stairs" in sample.story.lower(),
        "represent" in sample.story.lower(),
        "First you, then us" in sample.story,
        sample.world is not None and sample.world.facts["shared"],
        sample.world is not None and sample.world.facts["repeated"],
    )
    if not all(checks):
        print("Story verification failed.")
        return 1
    print("OK: ASP and Python agree that sharing, repetition, and a safe climb lead to bedtime.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle cotton-and-stairs bedtime StoryWorld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--representative", choices=REPRESENTATIVES)
    parser.add_argument("--pattern", choices=PATTERNS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        representative=args.representative or rng.choice(REPRESENTATIVES),
        pattern=args.pattern or rng.choice(PATTERNS),
        variant=rng.randrange(1, 2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}")
        print(f"entities: {list(sample.world.entities)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(StoryParams(
                seed=base_seed,
                name="Luna",
                helper="Grandma",
                place=place,
                representative=representative,
                pattern=pattern,
                variant=index + 1,
            ))
            for index, (place, representative, pattern) in enumerate([
                ("the moonlit house", "a small white cloud", "share"),
                ("the quiet cottage", "a silver star", "repeat"),
                ("the little blue home", "a sleepy blue bird", "both"),
            ])
        ]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + index)))
            for index in range(max(1, args.n))
        ]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
