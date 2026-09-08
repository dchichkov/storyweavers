#!/usr/bin/env python3
"""
A small Ghost Story world about a saltine, a frightened child, and the bravery
that helps a lonely ghost find its way home.
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "light", "noise", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("bravery", "fear", "loneliness", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Place:
    id: str
    name: str
    detail: str


@dataclass(frozen=True)
class Haunting:
    id: str
    clue: str
    ghost_problem: str
    first_scare: str
    ghost_words: str
    brave_action: str
    hidden_truth: str
    repair: str
    ending: str
    lesson: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if not line:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


PLACES = {
    "schoolhouse": Place("schoolhouse", "the old schoolhouse", "where moonlight striped the dusty floor"),
    "lighthouse": Place("lighthouse", "the empty lighthouse", "where the stairs curled around a cold lantern room"),
    "train_station": Place("train_station", "the little train station", "where the waiting room smelled of rain and wood"),
}

HAUNTINGS = {
    "lost_lantern": Haunting(
        "lost_lantern",
        "a pale glow blinked beneath the locked classroom door",
        "she could not remember where she had left her little lantern",
        "the door creaked open by itself, and a chilly shape floated into the hall",
        "Please do not leave me in the dark.",
        "held up a saltine like a tiny moon and walked toward the ghost instead of running away",
        "the ghost had been a child who once waited for a family wagon that never returned",
        "found the lantern in a cupboard, lit it, and carried it to the front steps",
        "The ghost smiled, and its light rose through the roof like a warm star.",
        "Bravery does not mean feeling no fear; it means choosing a kind step while fear is nearby.",
    ),
    "whispering_bell": Haunting(
        "whispering_bell",
        "the brass bell whispered one name whenever the wind stopped",
        "he was trapped beside the bell because no one had answered his last call",
        "the bell rang three times, though its rope hung perfectly still",
        "I called for help, but everyone hurried past.",
        "answered the bell aloud and offered the ghost half of the saltine",
        "the ghost had guarded the station during a storm and feared being forgotten",
        "rang the bell once for goodbye and opened the waiting-room door",
        "Morning trains passed while one soft bell note followed the ghost into the dawn.",
        "A brave hello can loosen a loneliness that has lasted a very long time.",
    ),
    "moonlit_ticket": Haunting(
        "moonlit_ticket",
        "a ticket slid across the floor with a silver handprint on it",
        "she had missed the last train and could not find the right platform",
        "a transparent face appeared in the dark window and tapped twice",
        "I only want to go where the lights are kind.",
        "kept the saltine beside the ticket and followed the ghost to the platform",
        "the ghost had been waiting for a train that had changed its route years ago",
        "made a row of lanterns point toward the open country road",
        "The ghost stepped into the lantern glow, and the silver handprint faded from the ticket.",
        "Courage can help someone discover that the path has changed without hope ending.",
    ),
}


ASP_RULES = r"""
place(P) :- place_registry(P).
haunting(H) :- haunting_registry(H).
has_clue(H) :- clue(H).
has_problem(H) :- problem(H).
has_brave_action(H) :- brave_action(H).
has_repair(H) :- repair(H).
valid_story(P,H) :- place(P), haunting(H), has_clue(H), has_problem(H),
    has_brave_action(H), has_repair(H).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place_registry", place_id))
    for haunting_id, haunting in HAUNTINGS.items():
        lines.extend(
            [
                asp.fact("haunting_registry", haunting_id),
                asp.fact("clue", haunting_id),
                asp.fact("problem", haunting_id),
                asp.fact("brave_action", haunting_id),
                asp.fact("repair", haunting_id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: "StoryParams") -> None:
    if params.place not in PLACES:
        raise StoryError("That place is not part of the ghost story world.")
    if params.haunting not in HAUNTINGS:
        raise StoryError("That haunting is not part of the ghost story world.")
    if not params.hero.strip() or not params.helper.strip():
        raise StoryError("The child and helper need names.")
    if params.hero == params.helper:
        raise StoryError("The child and helper must be different characters.")


@dataclass
class StoryParams:
    place: str
    haunting: str
    hero: str
    helper: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    place = PLACES[params.place]
    haunting = HAUNTINGS[params.haunting]
    world = World(place)

    child = world.add(Entity("hero", "character", params.hero))
    helper = world.add(Entity("helper", "character", params.helper))
    ghost = world.add(Entity("ghost", "ghost", "the ghost"))
    saltine = world.add(Entity("saltine", "object", "saltine"))

    openings = [
        f"One windy evening, {params.hero} and {params.helper} entered {place.name}, {place.detail}.",
        f"At moonrise, {params.hero} visited {place.name} with {params.helper}, who carried a small flashlight.",
        f"{place.name.capitalize()} looked ordinary in daylight, but that night {params.hero} and {params.helper} heard something inside.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{params.hero} had brought one crisp saltine for the walk home, while {params.helper} promised to stay close."
    )
    world.say(f"Then {haunting.clue}.")
    world.para()

    child.memes["fear"] += 2
    ghost.memes["loneliness"] += 2
    world.say(f"{haunting.first_scare} {params.hero} froze beside the wall.")
    world.say(
        f'"Do not come closer," whispered {params.hero}. "I am scared." '
        f'"That is all right," said {params.helper}. "We can still listen."'
    )
    world.say(f"The ghost said, \"{haunting.ghost_words}\"")
    world.para()

    child.memes["bravery"] += 1
    helper.memes["trust"] += 1
    saltine.meters["warmth"] += 1
    world.say(
        f"{params.helper} reminded {params.hero} that bravery could be small, so {params.hero} {haunting.brave_action}."
    )
    world.say(
        f'"Is that what you need?" asked {params.hero}. "Yes," answered the ghost. "A kind light and someone who will not forget me."'
    )
    world.para()

    child.memes["bravery"] += 2
    child.memes["fear"] = 0
    ghost.memes["loneliness"] = 0
    ghost.memes["relief"] += 2
    saltine.meters["light"] += 1
    world.say(f"Together, they discovered that {haunting.hidden_truth}.")
    world.say(f"{params.hero} and {params.helper} {haunting.repair}.")
    world.say(f"The ghost thanked them and promised, \"I will remember your brave little saltine.\"")
    world.say(f"{haunting.ending} {haunting.lesson}")
    world.para()

    world.facts.update(
        place=params.place,
        place_name=place.name,
        haunting=params.haunting,
        hero=params.hero,
        helper=params.helper,
        clue=haunting.clue,
        problem=haunting.ghost_problem,
        first_scare=haunting.first_scare,
        ghost_words=haunting.ghost_words,
        brave_action=haunting.brave_action,
        hidden_truth=haunting.hidden_truth,
        repair=haunting.repair,
        ending=haunting.ending,
        lesson=haunting.lesson,
        object="saltine",
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly Ghost Story about {f['hero']} and {f['helper']} carrying a saltine into {f['place_name']}.",
        f"Tell a gentle ghost story in which bravery helps {f['hero']} learn that {f['hidden_truth']}.",
        f"Write a story where a frightened child speaks kindly to a lonely ghost and helps it by using a small saltine and a light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['hero']} and {f['helper']} meet the ghost?",
            answer=f"They met the ghost in {f['place_name']}.",
        ),
        QAItem(
            question="What did the ghost need?",
            answer=f"The ghost needed help because {f['problem']}.",
        ),
        QAItem(
            question=f"What did {f['hero']} do when the ghost appeared?",
            answer=f"{f['hero']} showed bravery and {f['brave_action']}.",
        ),
        QAItem(
            question="What did the characters discover about the ghost?",
            answer=f"They discovered that {f['hidden_truth']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['ending']}",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"{f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saltine?",
            answer="A saltine is a thin, crisp cracker that is often lightly salted.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing to do a helpful or right thing even when you feel afraid.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or mysterious presence, often with a surprising or gentle ending.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place.name}"]
    for entity in world.entities.values():
        meters = ", ".join(f"{k}={v:g}" for k, v in entity.meters.items() if v)
        memes = ", ".join(f"{k}={v:g}" for k, v in entity.memes.items() if v)
        lines.append(f"{entity.id}: meters={{ {meters} }} memes={{ {memes} }}")
    return "\n".join(lines)


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


NAMES = ["Luna", "Mara", "Theo", "Nell", "Owen", "Iris"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Saltine Bravery Ghost Story world.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--haunting", choices=sorted(HAUNTINGS))
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
        haunting=args.haunting or rng.choice(sorted(HAUNTINGS)),
        hero=hero,
        helper=helper,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("schoolhouse", "lost_lantern", "Luna", "Mara"),
    StoryParams("lighthouse", "whispering_bell", "Theo", "Iris"),
    StoryParams("train_station", "moonlit_ticket", "Nell", "Owen"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {(place, haunting) for place in PLACES for haunting in HAUNTINGS}
    if actual != expected:
        print("MISMATCH between ASP and Python story gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for index, params in enumerate(CURATED):
        params.seed = index + 100
        sample = generate(params)
        if not sample.story or "saltine" not in sample.story.lower():
            print("MISMATCH: generated story lacks the required saltine.")
            return 1
        if not any("bravery" in item.answer.lower() for item in sample.story_qa):
            print("MISMATCH: generated QA lacks the bravery feature.")
            return 1
    print(f"OK: ASP parity and generated stories verified ({len(actual)} combinations).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} valid story shapes:")
        for place, haunting in values:
            print(f"  {place} / {haunting}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, curated in enumerate(CURATED):
            params = StoryParams(
                curated.place,
                curated.haunting,
                curated.hero,
                curated.helper,
                base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= max(args.n, 1):
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
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
            header = f"### {sample.params.hero} / {sample.params.haunting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
