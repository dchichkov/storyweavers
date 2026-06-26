#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/meme_grizzly_pier_dining_room_lesson_learned.py
============================================================================================

A small Adventure-style storyworld set in a dining room, where a child,
a grizzly, and a pier-shaped project learn teamwork and a lesson learned
about asking for help.

The seed words are woven into the domain:
- meme
- grizzly
- pier

The story is intentionally compact and child-facing, with a clear turn:
a tricky problem in the dining room is solved through teamwork, and the
ending proves what changed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the dining room"
    afford: str = "lesson"


@dataclass
class Objective:
    id: str
    label: str
    phrase: str
    problem: str
    solution: str
    keyword: str


@dataclass
class StoryParams:
    place: str
    objective: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


OBJECTIVES = {
    "lesson": Objective(
        id="lesson",
        label="lesson card",
        phrase="a bright lesson card",
        problem="the lesson card had slid behind the pier model",
        solution="they would need teamwork to lift the pier model safely",
        keyword="lesson learned",
    ),
    "teamwork": Objective(
        id="teamwork",
        label="teamwork sign",
        phrase="a teamwork sign",
        problem="the teamwork sign had fallen under the table edge",
        solution="they would need teamwork to reach it without tipping the dishes",
        keyword="teamwork",
    ),
}

GENDERS = {"girl", "boy"}
NAMES = {"girl": ["Mia", "Lily", "Ava"], "boy": ["Noah", "Leo", "Finn"]}
HELPERS = ["grizzly", "grandpa", "big sister"]


def protagonist_phrase(name: str, gender: str) -> str:
    return f"little {name}" if gender in GENDERS else name


def is_reasonable(setting: Setting, objective: Objective) -> bool:
    return setting.place == "the dining room" and objective.id in {"lesson", "teamwork"}


def explain_rejection(setting: Setting, objective: Objective) -> str:
    return (
        f"(No story: this world only works in {setting.place} with a dining-room "
        f"lesson about {objective.keyword}.)"
    )


def build_world(params: StoryParams) -> World:
    setting = Setting(place=params.place)
    objective = OBJECTIVES[params.objective]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0, "worry": 0.0, "joy": 0.0},
        memes={"lesson": 0.0, "teamwork": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="grizzly" if params.helper == "grizzly" else "adult",
        label=params.helper,
        meters={"strength": 2.0, "worry": 0.0, "joy": 0.0},
        memes={"lesson": 0.0, "teamwork": 0.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type="thing",
        label=objective.label,
        phrase=objective.phrase,
        owner=child.id,
        caretaker=helper.id,
        meters={"stuck": 1.0, "tilt": 0.0},
        memes={"important": 1.0},
    ))
    pier = world.add(Entity(
        id="pier",
        type="thing",
        label="pier model",
        phrase="a little wooden pier model",
        owner=child.id,
        meters={"weight": 1.0, "stability": 1.0},
        memes={"adventure": 1.0},
    ))

    world.facts.update(
        child=child, helper=helper, prize=prize, pier=pier, objective=objective, setting=setting
    )

    world.say(
        f"One afternoon in the dining room, {params.name} found {objective.phrase} missing."
    )
    world.say(
        f"It had slipped behind the pier model, and that made the room feel like a tiny adventure map."
    )
    world.para()
    world.say(
        f"{params.name} wanted to grab it alone, but the table chairs were in the way and the pier model was too wobbly."
    )
    world.say(
        f"{params.name} frowned and said the problem out loud: {objective.problem}."
    )
    world.para()
    helper.memes["teamwork"] += 1
    child.memes["teamwork"] += 1
    child.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    child.meters["worry"] += 1
    helper.meters["joy"] += 1
    world.say(
        f"The grizzly padded closer, nudged a chair aside, and showed how teamwork could make the search safe."
    )
    world.say(
        f"Together they lifted the pier model just enough to slide the {objective.label} free."
    )
    world.para()
    child.meters["joy"] += 1
    child.meters["worry"] = 0.0
    prize.meters["stuck"] = 0.0
    prize.meters["tilt"] = 0.0
    world.say(
        f"{params.name} laughed, hugged the grizzly, and learned a lesson learned: big problems feel smaller when friends work together."
    )
    world.say(
        f"By the end, the dining room was tidy again, the pier model stood straight, and the {objective.label} was safe in {params.name}'s hands."
    )
    return world


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "dining_room"),
        asp.fact("objective", "lesson"),
        asp.fact("objective", "teamwork"),
        asp.fact("place_is", "lesson", "dining_room"),
        asp.fact("place_is", "teamwork", "dining_room"),
        asp.fact("has_helper", "grizzly"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(dining_room, lesson, grizzly).
valid_story(dining_room, teamwork, grizzly).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        ("dining_room", "lesson", "grizzly"),
        ("dining_room", "teamwork", "grizzly"),
    }
    cl = set(asp_valid())
    if cl == py:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    objective: Objective = f["objective"]
    child: Entity = f["child"]
    return [
        f'Write a short adventure story in the dining room with "{objective.keyword}" and a grizzly helper.',
        f"Tell a child-facing story where {child.label} learns teamwork while looking behind a pier model.",
        f"Write a story that includes the words meme, grizzly, and pier, and ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    objective: Objective = f["objective"]
    return [
        QAItem(
            question=f"What did {child.label} need help finding in the dining room?",
            answer=f"{child.label} needed help finding {objective.phrase} after it slipped behind the pier model.",
        ),
        QAItem(
            question=f"Who helped {child.label} in the story?",
            answer=f"The grizzly helped by moving a chair and lifting the pier model a little.",
        ),
        QAItem(
            question=f"What lesson learned did {child.label} understand at the end?",
            answer="The lesson learned was that teamwork can make a tricky job easier and safer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or friends help each other to finish something together.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large bear, and in stories it can also be a strong helper.",
        ),
        QAItem(
            question="What is a pier?",
            answer="A pier is a long wooden walkway that reaches out over water, and in this story it is also a model shape on the table.",
        ),
        QAItem(
            question="What is a meme?",
            answer="A meme is a small idea, joke, or image that people share and remember easily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style dining-room storyworld.")
    ap.add_argument("--place", choices=["the dining room"], default="the dining room")
    ap.add_argument("--objective", choices=sorted(OBJECTIVES), default=None)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["grizzly"], default="grizzly")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for obj_id, obj in OBJECTIVES.items():
        if is_reasonable(Setting(), obj):
            out.append(("the dining room", obj_id, "grizzly"))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    objective = args.objective or rng.choice(sorted(OBJECTIVES))
    obj = OBJECTIVES[objective]
    if not is_reasonable(Setting(place=args.place), obj):
        raise StoryError(explain_rejection(Setting(place=args.place), obj))
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or "grizzly"
    return StoryParams(place=args.place, objective=objective, name=name, gender=gender, helper=helper)


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


CURATED = [
    StoryParams(place="the dining room", objective="lesson", name="Mia", gender="girl", helper="grizzly"),
    StoryParams(place="the dining room", objective="teamwork", name="Leo", gender="boy", helper="grizzly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
