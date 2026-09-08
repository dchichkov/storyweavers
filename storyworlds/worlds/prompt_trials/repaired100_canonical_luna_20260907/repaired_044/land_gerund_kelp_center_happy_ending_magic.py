#!/usr/bin/env python3
"""
A small ghost-story world about a magical kelp center where a landing spell
goes wrong until two friends listen to a shy ghost and repair the welcome.
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ImportError:
    from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("glow", "drift", "salt", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "hope", "trust", "joy", "loneliness"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Place:
    id: str
    name: str
    detail: str


@dataclass(frozen=True)
class Incident:
    id: str
    premise: str
    omen: str
    problem: str
    clue: str
    magic: str
    resolution: str
    ending: str
    lesson: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


PLACES = {
    "cove": Place("cove", "the moonlit cove", "black rocks curved around a quiet pool"),
    "harbor": Place("harbor", "the old harbor", "silver ropes rested beside the dark water"),
    "island": Place("island", "the little island", "pale sand shone beneath the tide"),
}

INCIDENTS = [
    Incident(
        "bell_kelp",
        "prepared a welcome bell from a long ribbon of kelp",
        "a pale handprint appeared on the wet sand",
        "the landing circle slid away from the shore whenever the bell rang",
        "the kelp ribbon was tied backward around a shell marked with a tiny star",
        "the ghost's blue light could untie knots made by frightened hands",
        "retied the kelp in the old welcoming shape and invited the ghost to ring the bell",
        "The ghost's bell chimed, and warm lights floated over the water like friendly fireflies.",
        "A strange warning may be a lonely friend's way of asking to be heard.",
    ),
    Incident(
        "singing_seaweed",
        "built a small center where travelers could rest among singing kelp",
        "the kelp whispered one name after every wave",
        "the center's doors vanished whenever someone tried to enter",
        "a strand of kelp pointed toward a forgotten lantern under the floor",
        "a ghostly breath could brighten a lantern without burning the kelp",
        "lifted the lantern, thanked its unseen keeper, and opened the center together",
        "The doors stayed open while the quiet ghost sat beside the brightest kelp.",
        "A welcome grows stronger when everyone who guards it is remembered.",
    ),
    Incident(
        "drifting_crown",
        "made a crown of kelp for the first visitor to land",
        "a green crown drifted in circles against the tide",
        "the visitor's boat could not touch the shore",
        "three glowing bubbles rose from the crown's empty center",
        "the ghost could guide bubbles into a path across the water",
        "followed the glowing path and placed the crown on the welcome stone",
        "The boat landed safely, and the ghost wore the crown for one happy dance.",
        "Magic works best when it makes room for someone who has been left out.",
    ),
]


CHARACTERS = {
    "luna": ("Luna", "child"),
    "milo": ("Milo", "child"),
    "piper": ("Piper", "child"),
    "sage": ("Sage", "child"),
}

HELPERS = {
    "otter": ("an otter", "otter"),
    "crab": ("a crab", "crab"),
    "tern": ("a tern", "tern"),
}

NAMES = ["Luna", "Milo", "Piper", "Sage", "Nell", "Cora"]


ASP_RULES = r"""
safe_place(P) :- place(P).
good_incident(I) :- incident(I), has_magic(I), has_resolution(I), happy_ending(I).
valid_story(P,I) :- safe_place(P), good_incident(I).
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for incident in INCIDENTS:
        lines.extend(
            [
                asp.fact("incident", incident.id),
                asp.fact("has_magic", incident.id),
                asp.fact("has_resolution", incident.id),
                asp.fact("happy_ending", incident.id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


@dataclass
class StoryParams:
    place: str
    incident: str
    hero: str
    helper: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The chosen place is not part of the moonlit shore.")
    if params.incident not in {item.id for item in INCIDENTS}:
        raise StoryError("The chosen ghostly incident is not in this world.")
    if not params.hero.strip():
        raise StoryError("The hero needs a name.")
    if not params.helper.strip():
        raise StoryError("The helper needs a name.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different characters.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    incident = next(item for item in INCIDENTS if item.id == params.incident)
    place = PLACES[params.place]
    world = World(place)

    hero = Entity("hero", "character", params.hero)
    helper = Entity("helper", "character", params.helper)
    ghost = Entity("ghost", "ghost", "the kelp ghost")
    kelp = Entity("kelp", "plant", "the silver kelp")
    center = Entity("center", "place", "the kelp center")
    world.add(hero)
    world.add(helper)
    world.add(ghost)
    world.add(kelp)
    world.add(center)

    hero.memes["hope"] = 1
    helper.memes["trust"] = 1
    ghost.memes["loneliness"] = 3
    kelp.meters["glow"] = 1
    center.meters["warmth"] = 1

    openings = [
        f"At {place.name}, {params.hero} built a tiny kelp center where lost travelers could land.",
        f"On a quiet evening, {params.hero} and {params.helper} opened a kelp center at {place.name}.",
        f"The moon rose over {place.name} as {params.hero} prepared a magical kelp center.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{params.helper} helped {params.hero} braid kelp into a landing path, while "
        f"{incident.premise}."
    )
    world.say(f"{place.detail}, and the center glimmered with a gentle blue welcome.")
    world.para()

    world.say(f"Then {incident.omen}.")
    world.say(f"{incident.problem.capitalize()}.")
    hero.memes["fear"] += 1
    center.meters["drift"] += 2
    kelp.meters["drift"] += 2
    world.para()

    world.say(
        f'"We should leave before the magic grows wild," said {params.hero}. '
        f'"Or we should ask what it wants," answered {params.helper}.'
    )
    world.say(f"{params.helper} listened closely and discovered that {incident.clue}.")
    helper.memes["trust"] += 2
    ghost.memes["hope"] += 1
    world.para()

    world.say(f"They held the kelp together while {params.helper} used {incident.magic}.")
    world.say(f"The blue light showed that the ghost had not meant to frighten anyone.")
    world.say(f"{params.hero} apologized, and {params.helper} {incident.resolution}.")
    world.say(f"{incident.ending} {incident.lesson}")
    hero.memes["fear"] = 0
    ghost.memes["loneliness"] = 0
    ghost.memes["joy"] = 2
    center.meters["warmth"] = 3
    kelp.meters["glow"] = 3

    world.facts.update(
        place=params.place,
        place_name=place.name,
        incident=incident.id,
        hero=params.hero,
        helper=params.helper,
        premise=incident.premise,
        omen=incident.omen,
        problem=incident.problem,
        clue=incident.clue,
        magic=incident.magic,
        resolution=incident.resolution,
        ending=incident.ending,
        lesson=incident.lesson,
        ghost="the kelp ghost",
        object="kelp",
        center="the kelp center",
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story about {f['hero']} and {f['helper']} at {f['place_name']}.",
        f"Tell how a magical kelp center is saved after {f['problem']}.",
        f"Include the clue that {f['clue']} and end with a happy welcome.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"Where did {f['hero']} build the magical center?",
            f"{f['hero']} built it at {f['place_name']}.",
        ),
        QAItem(
            "What went wrong?",
            f"The problem was that {f['problem']}.",
        ),
        QAItem(
            f"What clue did {f['helper']} discover?",
            f"{f['helper']} discovered that {f['clue']}.",
        ),
        QAItem(
            "How did the magic help?",
            f"The magic helped because {f['magic']}.",
        ),
        QAItem(
            "How did the story end?",
            f"{f['ending']} The friends also learned that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is kelp?", "Kelp is a large sea plant that grows in ocean water."),
        QAItem("What is a ghost story?", "A ghost story is a tale about a spirit or mysterious presence."),
        QAItem("What is magic in a story?", "Magic is an imaginative power that makes unusual things possible."),
        QAItem("What is a happy ending?", "A happy ending is a conclusion in which the main problem is safely resolved."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = ", ".join(f"{k}={v:g}" for k, v in entity.meters.items() if v)
        memes = ", ".join(f"{k}={v:g}" for k, v in entity.memes.items() if v)
        lines.append(f"{entity.label}: meters={{{meters}}} memes={{{memes}}}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ghost Story world: magical kelp center and a happy landing."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--incident", choices=[item.id for item in INCIDENTS])
    parser.add_argument("--hero")
    parser.add_argument("--helper")
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
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        incident=args.incident or rng.choice([item.id for item in INCIDENTS]),
        hero=hero,
        helper=helper,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("cove", "bell_kelp", "Luna", "Milo"),
    StoryParams("harbor", "singing_seaweed", "Piper", "Sage"),
    StoryParams("island", "drifting_crown", "Cora", "Nell"),
]


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {(place, incident.id) for place in PLACES for incident in INCIDENTS}
    if actual != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1
    print(f"OK: ASP and Python agree on {len(actual)} valid story shapes.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} valid story shapes:")
        for place, incident in values:
            print(f"  {place} / {incident}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for offset in range(max(20, args.n * 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} / {sample.params.helper} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
