#!/usr/bin/env python3
"""
A small Whodunit-style world about meyme, port, and eyer, where a repeated
clue helps friends discover who moved a bright harbor bell.
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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "weight", "visibility", "sound"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Place:
    id: str
    name: str
    water: bool


@dataclass(frozen=True)
class Case:
    id: str
    object_name: str
    repeated_clue: str
    first_sighting: str
    second_sighting: str
    mistaken_guess: str
    hidden_cause: str
    reveal_action: str
    resolution: str
    ending: str
    lesson: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, str] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
    "port": Place("port", "the little port", True),
    "jetty": Place("jetty", "the wooden jetty", True),
    "cove": Place("cove", "the quiet cove", True),
}

CASES = {
    "repeated_bell": Case(
        id="repeated_bell",
        object_name="the moon bell",
        repeated_clue="a bright blue thread appeared beside the bell",
        first_sighting="a bright blue thread lay beside the empty hook",
        second_sighting="the same blue thread glimmered near the fish crates",
        mistaken_guess="everyone suspected the sleepy seal who had been near the ropes",
        hidden_cause="a small gull had dragged the bell away while collecting blue thread for its nest",
        reveal_action="followed the blue thread around the stacked crates",
        resolution="returned the bell to its hook and carried the loose thread to the gull's nest",
        ending="The moon bell rang above the port, and the gull's blue nest shone safely in the sunset.",
        lesson="When a clue repeats, it may be pointing to a path instead of pointing at a person.",
    ),
    "repeated_shell": Case(
        id="repeated_shell",
        object_name="the captain's shell",
        repeated_clue="three white shells formed a tiny arrow",
        first_sighting="three white shells pointed away from the empty basket",
        second_sighting="three more white shells pointed toward the tide pool",
        mistaken_guess="the friends blamed the crab who had borrowed the basket",
        hidden_cause="the crab had been making arrows to guide a lost hatchling home",
        reveal_action="matched the shell arrows and followed them along the sand",
        resolution="found the basket beside the tide pool and helped the hatchling reach its mother",
        ending="The captain's shell rested in its basket while little shell arrows marked a safe way home.",
        lesson="A repeated sign can tell two stories at once if we stop and look closely.",
    ),
    "repeated_rope": Case(
        id="repeated_rope",
        object_name="the red harbor rope",
        repeated_clue="a wet red knot appeared in every place the rope had touched",
        first_sighting="a wet red knot marked the empty post",
        second_sighting="another wet red knot marked the old boat shed",
        mistaken_guess="the children suspected the fisherman who had left in a hurry",
        hidden_cause="the rope had slipped loose and floated through the tide before catching on the shed",
        reveal_action="compared the knots and traced the wet marks toward the water",
        resolution="pulled the rope from the tide and tied it firmly around the harbor post",
        ending="The red rope held fast as boats bobbed gently beneath the first evening star.",
        lesson="Repeating marks can show where an object traveled, not who took it.",
    ),
}

NAMES = ["Luna", "Meyme", "Pip", "Nori", "Eyer", "Tavi"]
ANIMALS = {
    "otter": "otter",
    "tern": "tern",
    "seal": "seal",
    "crab": "crab",
    "mouse": "mouse",
}

ASP_RULES = r"""
reasonable(P, C) :- place(P), case(C), repeated_clue(C), resolution(C).
#show reasonable/2.
"""


@dataclass
class StoryParams:
    place: str
    case: str
    hero: str
    hero_kind: str
    helper: str
    helper_kind: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in PLACES:
        lines.append(asp.fact("place", key))
    for key, case in CASES.items():
        lines.extend(
            [
                asp.fact("case", key),
                asp.fact("repeated_clue", key),
                asp.fact("resolution", key),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That place is not in the small harbor world.")
    if params.case not in CASES:
        raise StoryError("That mystery is not in the casebook.")
    if params.hero_kind not in ANIMALS or params.helper_kind not in ANIMALS:
        raise StoryError("The hero and helper must be known harbor animals.")
    if params.hero == params.helper:
        raise StoryError("The detective and helper must be different characters.")
    if params.hero_kind == params.helper_kind and params.hero == params.helper:
        raise StoryError("The detective pair cannot be the same character.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    place = PLACES[params.place]
    case = CASES[params.case]
    world = World(place)

    hero = world.add(Entity(params.hero, "character", params.hero))
    helper = world.add(Entity(params.helper, "character", params.helper))
    clue = world.add(Entity("repeated_clue", "thing", case.repeated_clue))
    missing = world.add(Entity("missing_object", "thing", case.object_name))

    hero.memes["curiosity"] = 1
    helper.memes["trust"] = 1
    clue.meters["visibility"] = 2
    missing.meters["distance"] = 1

    openings = [
        f"At {place.name}, Luna the {params.hero_kind} kept a careful notebook about every harbor mystery.",
        f"The little port was waking when Luna the {params.hero_kind} became its newest detective.",
        f"Near {place.name}, Luna the {params.hero_kind} watched gulls, boats, and footprints with bright attention.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{params.helper} the {params.helper_kind} helped Luna, and together they prepared to inspect "
        f"{case.object_name} before the harbor festival."
    )
    world.say(
        f"They called their method Repetition: notice what happens once, then notice what happens again."
    )
    world.para()

    world.say(
        f"Just before the festival, {case.object_name} vanished from its place. "
        f"At the first spot, {case.first_sighting}."
    )
    world.say(f'"That may be the first clue," said {params.helper}. "Let us remember it exactly."')
    hero.memes["worry"] = 1
    world.para()

    world.say(f"They searched the ropes, crates, and damp boards. Then {case.second_sighting}.")
    world.say(
        f'"It happened twice," Luna said. "{case.repeated_clue.capitalize()}."'
    )
    world.say(
        f"For a moment, {case.mistaken_guess}. The harbor grew quiet while everyone waited for an answer."
    )
    helper.memes["worry"] = 1
    world.para()

    world.say(
        f'"A repeated clue is not a quick accusation," said {params.helper}. '
        f'"It is a trail."'
    )
    world.say(f"Luna nodded, and they {case.reveal_action}.")
    world.say(f"The hidden truth was simple: {case.hidden_cause}.")
    world.say(f'{params.helper} whispered, "Now the pieces fit."')
    world.say(f"Luna answered, "Then let us fix the trouble instead of blaming anyone."")
    world.para()

    world.say(f"Together, Luna and {params.helper} {case.resolution}.")
    hero.memes["relief"] = 1
    helper.memes["relief"] = 1
    missing.meters["distance"] = 0
    world.say(
        f"They thanked the worried neighbors and wrote the clue in their notebook: "
        f"{case.lesson}"
    )
    world.say(case.ending)

    world.facts.update(
        place=params.place,
        case=params.case,
        hero=params.hero,
        helper=params.helper,
        hero_kind=params.hero_kind,
        helper_kind=params.helper_kind,
        object_name=case.object_name,
        repeated_clue=case.repeated_clue,
        first_sighting=case.first_sighting,
        second_sighting=case.second_sighting,
        mistaken_guess=case.mistaken_guess,
        hidden_cause=case.hidden_cause,
        reveal_action=case.reveal_action,
        resolution=case.resolution,
        ending=case.ending,
        lesson=case.lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle Whodunit about {f['hero']} and {f['helper']} investigating {f['object_name']} at {PLACES[f['place']].name}.",
        f"Use Repetition: the clue appears first as '{f['first_sighting']}' and again as '{f['second_sighting']}'.",
        f"Reveal that {f['hidden_cause']} and end with a safe harbor image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"Where did Luna investigate the missing object?",
            f"Luna investigated it at {PLACES[f['place']].name}.",
        ),
        QAItem(
            "What object disappeared?",
            f"{f['object_name'].capitalize()} disappeared before the harbor festival.",
        ),
        QAItem(
            "What clue repeated?",
            f"The repeated clue was that {f['repeated_clue']}.",
        ),
        QAItem(
            "What did the detectives first suspect?",
            f"They first suspected that {f['mistaken_guess'].rstrip('.')}.",
        ),
        QAItem(
            "What was the real cause?",
            f"The real cause was that {f['hidden_cause']}.",
        ),
        QAItem(
            "How was the mystery resolved?",
            f"They {f['resolution']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a whodunit?", "A whodunit is a mystery story about discovering who caused an event."),
        QAItem("What does repetition mean?", "Repetition means that something happens or appears again."),
        QAItem("Why are clues useful?", "Clues help characters connect details and understand what happened."),
        QAItem("What is a port?", "A port is a place beside water where boats can arrive and leave."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place={world.place.id}"]
    for entity in world.entities.values():
        meters = ", ".join(f"{k}={v:g}" for k, v in entity.meters.items() if v)
        memes = ", ".join(f"{k}={v:g}" for k, v in entity.memes.items() if v)
        lines.append(f"{entity.id}: meters={{{meters}}} memes={{{memes}}}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
    parser = argparse.ArgumentParser(description="Meyme port eyer Repetition Whodunit world.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--hero")
    parser.add_argument("--hero-kind", choices=sorted(ANIMALS))
    parser.add_argument("--helper")
    parser.add_argument("--helper-kind", choices=sorted(ANIMALS))
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
    hero_kind = args.hero_kind or rng.choice(sorted(ANIMALS))
    helper_kind = args.helper_kind or rng.choice(sorted(ANIMALS))
    params = StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        case=args.case or rng.choice(sorted(CASES)),
        hero=hero,
        hero_kind=hero_kind,
        helper=helper,
        helper_kind=helper_kind,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("port", "repeated_bell", "Luna", "otter", "Meyme", "tern"),
    StoryParams("jetty", "repeated_shell", "Eyer", "mouse", "Pip", "crab"),
    StoryParams("cove", "repeated_rope", "Meyme", "seal", "Luna", "tern"),
]


def asp_verify() -> int:
    import asp
    actual = set(asp.atoms(asp.one_model(asp_program()), "reasonable"))
    expected = {(place, case) for place in PLACES for case in CASES}
    if actual != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 4:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP gate and generated stories verified ({len(actual)} combinations).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        values = sorted(set(asp.atoms(asp.one_model(asp_program()), "reasonable")))
        print(f"{len(values)} valid story shapes:")
        for place, case in values:
            print(f"  {place} / {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for offset in range(max(20, args.n * 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
