#!/usr/bin/env python3
"""
A child-friendly comedy storyworld about relying on a friend during a rapid,
silly rescue at a neighborhood talent show.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = ["the school hall", "the community garden", "the library courtyard"]
NAMES = ["Luna", "Milo", "Pia", "Theo", "Nia", "Sam"]
FRIENDS = ["her friend", "his cousin", "their neighbor", "her brother"]
TALENTS = ["a juggling act", "a puppet show", "a silly dance", "a song with kazoos"]
OBJECTS = ["a red hat", "a cardboard crown", "a paper mustache", "a striped umbrella"]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("speed", "balance", "distance", "ready"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "trust", "joy", "embarrassment", "confidence"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    place: str
    name: str
    companion: str
    talent: str
    prop: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


INCIDENTS = [
    {
        "problem": "the curtain cord snapped just as the act was about to begin",
        "clue": "the loose cord had landed beside a long ribbon in the costume box",
        "plan": "use the ribbon as a temporary pull, while one person held the curtain open",
        "turn": "Luna tried to fix everything at once and tied the ribbon to her own sleeve",
        "result": "the curtain opened with a cheerful swoosh instead of a frightening flop",
        "ending": "the audience laughed kindly, then clapped so loudly that the paper stars shook",
    },
    {
        "problem": "the prop table rolled away with the most important prop still on it",
        "clue": "one wheel was pointing toward the snack table, where a wedge could stop it",
        "plan": "have the friend grab the wedge while Luna guided the table back",
        "turn": "Luna chased the table so rapidly that she ended up circling the same potted plant",
        "result": "the table stopped safely, and the prop arrived before the next announcement",
        "ending": "the prop received its own tiny bow, and everyone laughed when it almost rolled back",
    },
    {
        "problem": "a gust of wind lifted the program cards and sent them skittering across the floor",
        "clue": "the cards were gathering near the bright yellow welcome mat",
        "plan": "let one helper collect cards while Luna read the order from the stack",
        "turn": "Luna grabbed three cards rapidly and discovered that all three announced the same puppet",
        "result": "the correct order was restored, with one extra puppet announcement saved for a joke",
        "ending": "the puppet bowed before appearing, and the crowd applauded the clever mistake",
    },
    {
        "problem": "the microphone made a loud pop and went silent before the first line",
        "clue": "the sound switch had been bumped by a wobbling music stand",
        "plan": "let the companion steady the stand while Luna checked the switch",
        "turn": "Luna spoke into the silent microphone anyway, and the audience watched her eyebrows perform the speech",
        "result": "the microphone returned just in time for the funniest line",
        "ending": "the audience repeated the line together, turning the accident into the best part",
    },
]


ASP_RULES = r"""
ready :- child(c), helper(h), relies_on(c,h), plan_exists, safe.
happy_ending :- ready, laughter.
valid_story :- happy_ending.
"""


def validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown child name: {params.name}")
    if params.companion not in FRIENDS:
        raise StoryError(f"Unknown companion: {params.companion}")
    if params.talent not in TALENTS:
        raise StoryError(f"Unknown talent: {params.talent}")
    if params.prop not in OBJECTS:
        raise StoryError(f"Unknown prop: {params.prop}")


def choose_incident(params: StoryParams) -> dict[str, str]:
    index = (params.seed or 0) % len(INCIDENTS)
    return INCIDENTS[index]


def tell(params: StoryParams) -> World:
    validate(params)
    incident = choose_incident(params)
    world = World(params.place)

    child = world.add(Entity("child", "character", params.name))
    helper = world.add(Entity("helper", "character", params.companion))
    prop = world.add(Entity("prop", "object", params.prop))

    child.memes["worry"] = 1
    child.memes["confidence"] = 1
    helper.memes["trust"] = 1
    child.meters["speed"] = 2
    helper.meters["speed"] = 2
    prop.meters["ready"] = 0

    world.facts.update(
        child=child,
        helper=helper,
        prop=prop,
        incident=incident,
        talent=params.talent,
        relied=False,
        safe=False,
        laughter=False,
    )

    name = child.label
    companion = helper.label

    world.events.append(
        f"At {params.place}, {name} was ready to perform {params.talent} with {params.prop}."
    )
    world.events.append(
        f"Then {incident['problem']}. The trouble was too rapid for one child to solve alone."
    )
    world.events.append(
        f"{name} grabbed the prop, spun once, and nearly marched into a chair."
    )
    world.events.append(
        f"{companion} noticed that {incident['clue']}."
    )
    world.events.append(
        f'"You should rely on me for the quick part," said {companion}. "You can handle the part that needs careful thinking."'
    )
    world.events.append(
        f'"Rely on you? Rapidly?" {name} asked. "That sounds like a recipe for a very fast disaster."'
    )
    world.events.append(
        f'"Only a small disaster," {companion} replied. "The funny kind."'
    )

    world.facts["relied"] = True
    child.memes["worry"] = 0
    child.memes["trust"] = 1
    helper.memes["confidence"] = 1
    world.events.append(f"Together they made a plan: {incident['plan']}.")
    world.events.append(f"First, {incident['turn']}.")
    world.events.append(
        f"{name} stopped, laughed, and let {companion} take the rapid job while {name} took the careful job."
    )

    prop.meters["ready"] = 1
    world.facts["safe"] = True
    world.facts["laughter"] = True
    child.memes["joy"] = 2
    helper.memes["joy"] = 2
    child.memes["confidence"] = 2
    world.events.append(f"That worked: {incident['result']}.")
    world.events.append(
        f"The two performers hurried into place, and {name} began {params.talent} with {params.prop}."
    )
    world.events.append(f"{incident['ending']}.")
    world.events.append(
        f"{name} learned that relying on a friend can make a rapid problem feel small enough to laugh at."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    talent = world.facts["talent"]
    return [
        "Write a child-facing comedy about a child who must rely on a friend during a rapid problem.",
        f"Tell a funny dialogue-rich story in which {child.label} relies on {helper.label} before performing {talent}.",
        "Give the story a happy ending where teamwork turns an embarrassing mistake into a joke.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    incident: dict[str, str] = world.facts["incident"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did {child.label} face?",
            answer=f"{incident['problem'].capitalize()}. The problem happened just before the performance and moved too rapidly for {child.label} to solve alone.",
        ),
        QAItem(
            question=f"Why did {child.label} rely on {helper.label}?",
            answer=f"{helper.label} noticed that {incident['clue']} and could handle the rapid part of the rescue.",
        ),
        QAItem(
            question="What did the friends say to each other?",
            answer=f'{helper.label} said, "You should rely on me for the quick part," and {child.label} answered, "Rely on you? Rapidly?" Their dialogue helped them divide the work.',
        ),
        QAItem(
            question="How did the plan succeed?",
            answer=f"They followed this plan: {incident['plan']}. After one funny mistake, they divided the rapid job from the careful job and {incident['result']}.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"{incident['ending']}. The child learned that relying on a friend can turn a rapid problem into a funny success.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to rely on someone?",
            answer="To rely on someone means to trust that person to help or do an important job.",
        ),
        QAItem(
            question="What does rapid mean?",
            answer="Rapid means very quick or fast.",
        ),
        QAItem(
            question="Why can dialogue help solve a problem?",
            answer="Dialogue lets characters share information, make plans, and change what they decide to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: {entity.label}; meters={meters}; memes={memes}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child", "c"),
            asp.fact("helper", "h"),
            asp.fact("relies_on", "c", "h"),
            asp.fact("plan_exists"),
            asp.fact("safe"),
            asp.fact("laughter"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def verify_asp() -> None:
    try:
        import asp
    except ImportError as exc:
        raise StoryError("ASP verification requires clingo to be installed.") from exc
    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    if "valid_story" not in names:
        raise StoryError("ASP twin did not derive valid_story.")
    for index in range(8):
        params = resolve_params(
            argparse.Namespace(
                place=None,
                name=None,
                companion=None,
                talent=None,
                prop=None,
                seed=index,
            ),
            random.Random(index),
        )
        sample = generate(params)
        if "rely" not in sample.story.lower():
            raise StoryError("Generated story does not contain the required reliance theme.")
        if not sample.world.facts["safe"] or not sample.world.facts["laughter"]:
            raise StoryError("Generated story lacks a safe happy ending.")
    print("OK: Python and ASP both derive a valid, happy reliance story.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comedy storyworld about a child relying on a friend during a rapid rescue."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=FRIENDS)
    parser.add_argument("--talent", choices=TALENTS)
    parser.add_argument("--prop", choices=OBJECTS)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(FRIENDS),
        talent=args.talent or rng.choice(TALENTS),
        prop=args.prop or rng.choice(OBJECTS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=" ".join(world.events),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        verify_asp()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(INCIDENTS)):
            local = argparse.Namespace(
                place=args.place,
                name=args.name,
                companion=args.companion,
                talent=args.talent,
                prop=args.prop,
                seed=base_seed + index,
            )
            samples.append(generate(resolve_params(local, random.Random(base_seed + index))))
    else:
        for index in range(args.n):
            local_seed = base_seed + index
            local = argparse.Namespace(
                place=args.place,
                name=args.name,
                companion=args.companion,
                talent=args.talent,
                prop=args.prop,
                seed=local_seed,
            )
            samples.append(generate(resolve_params(local, random.Random(local_seed))))

    if args.asp:
        try:
            import asp
            symbols = asp.one_model(asp_program())
            print("ASP model:", ", ".join(str(symbol) for symbol in symbols))
        except ImportError as exc:
            raise StoryError("ASP mode requires clingo to be installed.") from exc
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### comedy variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
