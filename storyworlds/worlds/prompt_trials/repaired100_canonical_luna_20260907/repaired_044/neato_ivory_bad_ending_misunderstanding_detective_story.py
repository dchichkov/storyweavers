#!/usr/bin/env python3
"""
A small detective-story world about Neato and Ivory, a misunderstanding, and a
bad ending that is repaired by careful evidence and an honest apology.
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
        for key in ("visibility", "distance", "damage", "order"):
            self.meters.setdefault(key, 0.0)
        for key in ("trust", "worry", "curiosity", "guilt", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Case:
    id: str
    object_name: str
    clue: str
    misunderstanding: str
    bad_ending: str
    question: str
    reveal: str
    repair: str
    final_image: str
    lesson: str


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    detail: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

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
    "archive": Place("archive", "the little town archive", "where old maps slept in wooden drawers"),
    "station": Place("station", "the quiet train station", "where a brass clock watched every platform"),
    "museum": Place("museum", "the moonlit museum", "where glass cases held small treasures"),
}

CASES = {
    "ivory_compass": Case(
        id="ivory_compass",
        object_name="an ivory compass",
        clue="a thin blue thread caught on the latch",
        misunderstanding="Neato believed Ivory had taken the compass because Ivory was the last friend near the cabinet",
        bad_ending="Neato announced the accusation before checking the room, and Ivory sadly walked away",
        question="Who had touched the cabinet after Ivory?",
        reveal="the blue thread belonged to a caretaker's repair bag, and the caretaker had moved the compass to polish the shelf",
        repair="Neato found the caretaker, listened to the full explanation, and apologized to Ivory",
        final_image="the ivory compass pointed north on a clean shelf while Neato and Ivory stood together beneath the bright clock",
        lesson="A nearby friend is not automatically the cause of a missing thing; a detective checks the whole trail.",
    ),
    "neato_key": Case(
        id="neato_key",
        object_name="Neato's tiny brass key",
        clue="a row of dusty paw prints ended beside a loose floorboard",
        misunderstanding="Ivory thought Neato had hidden the key as a trick because Neato kept guarding the desk",
        bad_ending="Ivory told everyone that Neato was dishonest, and the case ended with both friends facing opposite doors",
        question="Why had Neato stayed beside the desk?",
        reveal="Neato had been protecting the loose key from falling through the floorboard",
        repair="Ivory lifted the board carefully, returned the key, and said sorry for guessing",
        final_image="the brass key rested in its blue cup as Neato and Ivory locked the case together",
        lesson="A worried silence can have a kind reason, so questions should come before blame.",
    ),
    "museum_stamp": Case(
        id="museum_stamp",
        object_name="the museum's silver stamp",
        clue="a trail of damp leaves led from the door to the empty display",
        misunderstanding="Neato thought Ivory had borrowed the stamp and forgotten to ask",
        bad_ending="Neato closed the display in anger, leaving Ivory outside in the rain",
        question="What had come through the museum door?",
        reveal="a gust had blown the stamp's soft display cloth outside, and the stamp had rolled after it",
        repair="Neato and Ivory followed the leaf trail, found the stamp beneath a bench, and dried the display",
        final_image="the silver stamp gleamed in its case while rain tapped a tidy rhythm on the museum roof",
        lesson="A clue should explain the whole path, not just point toward the easiest suspect.",
    ),
}

NAMES = ["Mara", "Tobin", "Lina", "Pax", "Wren", "Suri"]
KINDS = ["mouse", "fox", "raven", "rabbit"]

ASP_RULES = r"""
reason(P, C) :- place(P), case(C), clue(C), misunderstanding(C),
                bad_ending(C), reveal(C), repair(C).
#show reason/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for case_id, case in CASES.items():
        lines.extend([
            asp.fact("case", case_id),
            asp.fact("clue", case_id),
            asp.fact("misunderstanding", case_id),
            asp.fact("bad_ending", case_id),
            asp.fact("reveal", case_id),
            asp.fact("repair", case_id),
        ])
    return "\n".join(lines)


def asp_program(show: str = "#show reason/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


@dataclass
class StoryParams:
    place: str
    case: str
    detective: str
    detective_kind: str
    friend: str
    friend_kind: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That detective setting is not available.")
    if params.case not in CASES:
        raise StoryError("That mystery is not available.")
    if params.detective_kind not in KINDS or params.friend_kind not in KINDS:
        raise StoryError("Both characters need known animal kinds.")
    if params.detective == params.friend:
        raise StoryError("The detective and friend must have different names.")
    if not params.detective.strip() or not params.friend.strip():
        raise StoryError("Both characters need names.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    place = PLACES[params.place]
    case = CASES[params.case]
    world = World(place)

    detective = world.add(Entity(params.detective, "character", params.detective))
    friend = world.add(Entity(params.friend, "character", params.friend))
    evidence = world.add(Entity("evidence", "clue", case.clue))
    object_entity = world.add(Entity("missing_object", "object", case.object_name))

    openings = [
        f"At {place.name}, {params.detective} the {params.detective_kind} opened a detective notebook.",
        f"The little case began when {params.detective} the {params.detective_kind} noticed an empty place in {place.name}.",
        f"On a quiet morning, {params.detective} the {params.detective_kind} became a detective inside {place.name}.",
    ]
    world.say(rng.choice(openings))
    world.say(f"{params.friend} the {params.friend_kind} stood nearby while {case.object_name} was reported missing. {place.detail.capitalize()}.")
    world.say(f'"We will solve this neatly," said {params.detective}. "Neato clues first, guesses later."')
    world.say(f'"I will help," said {params.friend}. "Ask me anything you need to know."')
    world.para()

    detective.memes["curiosity"] += 1
    friend.memes["worry"] += 1
    object_entity.meters["visibility"] = 0
    world.say(f"The first clue was {case.clue}.")
    world.say(f"{case.misunderstanding}.")
    world.say(f'"You were the last one here," said {params.detective}. "Did you take it?"')
    world.say(f'"No," said {params.friend}. "I saw the empty place, but I did not touch the missing object."')
    world.para()

    detective.memes["trust"] -= 1
    friend.memes["worry"] += 1
    world.say(f"The misunderstanding grew because {case.question}")
    world.say(f"{case.bad_ending}.")
    world.say(f"The bad ending felt heavy: the case was not solved, and the two friends stopped walking together.")
    world.para()

    evidence.meters["visibility"] = 1
    evidence.meters["order"] = 2
    detective.memes["curiosity"] += 2
    friend.memes["relief"] += 1
    world.say(f"Then {params.detective} noticed that {case.clue}.")
    world.say(f'"Wait," said {params.detective}. "I asked who was nearby, but I did not ask what happened afterward."')
    world.say(f'"Let us follow the evidence," said {params.friend}. "The clue may tell a longer story."')
    world.say(f"They asked the next careful question: {case.question}")
    world.say(f"The reveal was clear: {case.reveal}.")
    world.say(f"{case.repair}.")
    detective.memes["trust"] += 2
    friend.memes["trust"] += 2
    detective.memes["guilt"] += 1
    object_entity.meters["visibility"] = 1
    world.say(f'"I am sorry I decided before I investigated," said {params.detective}.')
    world.say(f'"Thank you for coming back to the case," said {params.friend}. "Now we know the truth."')
    world.say(f"They finished the detective work together. {case.final_image}.")
    world.say(f"The lesson of the case was simple: {case.lesson}")

    world.facts.update(
        place=params.place,
        case=params.case,
        detective=params.detective,
        detective_kind=params.detective_kind,
        friend=params.friend,
        friend_kind=params.friend_kind,
        object_name=case.object_name,
        clue=case.clue,
        misunderstanding=case.misunderstanding,
        bad_ending=case.bad_ending,
        question=case.question,
        reveal=case.reveal,
        repair=case.repair,
        final_image=case.final_image,
        lesson=case.lesson,
        resolved="yes",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Detective Story about {f['detective']} and {f['friend']} investigating {f['object_name']}.",
        f"Include a misunderstanding caused by this clue: {f['clue']}.",
        f"Give the story a bad ending first, then repair it when the characters discover that {f['reveal']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['detective']} investigate the mystery?",
            answer=f"{f['detective']} investigated it at {PLACES[f['place']].name}.",
        ),
        QAItem(
            question=f"What object was missing?",
            answer=f"The missing object was {f['object_name']}.",
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"The misunderstanding began because {f['misunderstanding']}.",
        ),
        QAItem(
            question="What was the bad ending?",
            answer=f"The bad ending was that {f['bad_ending']}.",
        ),
        QAItem(
            question="What clue changed the investigation?",
            answer=f"The important clue was {f['clue']}.",
        ),
        QAItem(
            question="What was finally revealed?",
            answer=f"It was revealed that {f['reveal']}.",
        ),
        QAItem(
            question="How did the friends repair the bad ending?",
            answer=f"They repaired it when {f['repair']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective studies clues, asks careful questions, and checks evidence to solve a mystery.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is a wrong idea caused when someone does not yet know the whole truth.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a detail that can help explain what happened.",
        ),
        QAItem(
            question="Why should a detective avoid quick blame?",
            answer="A detective should avoid quick blame because the first guess may be wrong and may hurt an innocent friend.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.id}")
    for entity in world.entities.values():
        meters = ", ".join(f"{k}={v}" for k, v in entity.meters.items() if v)
        memes = ", ".join(f"{k}={v}" for k, v in entity.memes.items() if v)
        lines.append(f"{entity.id}: meters={{{meters}}} memes={{{memes}}}")
    lines.append("facts=" + json.dumps(world.facts, ensure_ascii=False, sort_keys=True))
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detective Story world of Neato, Ivory, clues, and repaired misunderstandings.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--detective")
    parser.add_argument("--detective-kind", choices=KINDS)
    parser.add_argument("--friend")
    parser.add_argument("--friend-kind", choices=KINDS)
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
    detective = args.detective or rng.choice(NAMES)
    friend = args.friend or rng.choice([name for name in NAMES if name != detective])
    detective_kind = args.detective_kind or rng.choice(KINDS)
    friend_kind = args.friend_kind or rng.choice(KINDS)
    params = StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        case=args.case or rng.choice(sorted(CASES)),
        detective=detective,
        detective_kind=detective_kind,
        friend=friend,
        friend_kind=friend_kind,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("archive", "ivory_compass", "Neato", "mouse", "Ivory", "raven"),
    StoryParams("station", "neato_key", "Ivory", "rabbit", "Neato", "fox"),
    StoryParams("museum", "museum_stamp", "Neato", "fox", "Ivory", "mouse"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "reason"))
    expected = {(place, case) for place in PLACES for case in CASES}
    if actual != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "Neato" not in sample.story and "Ivory" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP gate matches Python registry gate ({len(actual)} combinations), and stories generated.")
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
        values = sorted(set(asp.atoms(model, "reason")))
        print(f"{len(values)} valid detective-story shapes:")
        for place, case in values:
            print(f"  {place} / {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(20, args.n * 20)):
            if len(samples) >= args.n:
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
            if sample.story in seen:
                continue
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
            params = sample.params
            header = f"### {params.detective} / {params.friend} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
