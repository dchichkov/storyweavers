#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a curious child, a little stage, and a star.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Stage:
    name: str
    phrase: str
    room: str


@dataclass
class StoryParams:
    stage: str = "Willow Hall"
    hero_name: str = "Mira"
    helper_name: str = "Pip"
    incident: str = "shadow"
    seed: Optional[int] = None


class World:
    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


STAGE_REGISTRY = {
    "Willow Hall": Stage("Willow Hall", "the little stage in Willow Hall", "the village hall"),
    "Acorn Room": Stage("Acorn Room", "the puppet stage in the Acorn Room", "the school"),
    "Moonbeam Room": Stage("Moonbeam Room", "the story stage in the Moonbeam Room", "the library"),
}

HERO_NAMES = ["Mira", "Nell", "Tavi", "Lulu", "Robin"]
HELPER_NAMES = ["Pip", "Bram", "Nori", "Kit", "Wren"]

INCIDENTS = {
    "shadow": {
        "premise": "A wide curtain fold cast a shadow over the paper star, making its bright points hard to see.",
        "mistake": "Mira pulled the star toward the curtain's edge, but the cloth folded over it again.",
        "clue": "Pip watched the shadow slide when the curtain swayed, and saw that the star itself was still bright.",
        "change": "They tied the curtain back with a soft cloth loop and hung the star in the clear space beside it.",
        "result": "The star's points showed clearly, while the curtain stayed safely away from the little stage light.",
        "ending": "The star shone above the stage, and the curtain made a quiet, moon-blue frame.",
        "lesson": "look closely at a problem before deciding what to move",
        "meter": "visibility",
    },
    "tangle": {
        "premise": "The star's ribbon had curled around its points until the paper shape looked like a lopsided moon.",
        "mistake": "Mira tugged at the ribbon, but the tight curl only hugged the star more firmly.",
        "clue": "Pip noticed that the ribbon was looped around one wooden peg, not knotted through the star.",
        "change": "They lifted the loop off the peg, smoothed the ribbon flat, and fastened it with a broad paper tab.",
        "result": "The star hung straight, and its ribbon no longer caught on the stage's wooden edge.",
        "ending": "Five neat points danced above the boards as the ribbon made a small, golden bow.",
        "lesson": "find where a tangle begins instead of pulling harder",
        "meter": "alignment",
    },
    "draft": {
        "premise": "A little draft from the open window made the paper star spin until its face disappeared.",
        "mistake": "Mira tried to hold the star still with one finger, but each turn made it wobble again.",
        "clue": "Pip held a loose paper strip nearby; it fluttered toward the window whenever the star spun.",
        "change": "They closed the window gently and hung the star from a short, balanced thread.",
        "result": "The star faced the audience, while fresh air still came through the room's open doorway.",
        "ending": "The star held still above the boards, and the audience's smiles twinkled back.",
        "lesson": "notice what is moving around a problem before trying to stop it",
        "meter": "steadiness",
    },
}

ASP_RULES = r"""
stage(S) :- stage_name(S).
problem(I) :- incident(I).
solved(I) :- problem(I), clue_seen(I), repair_chosen(I), safe_result(I).
curious_hero(H) :- hero(H), asked_question(H).
ready_for_show(I) :- solved(I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for stage_name in STAGE_REGISTRY:
        lines.append(asp.fact("stage_name", stage_name))
    for incident in INCIDENTS:
        lines.append(asp.fact("incident", incident))
        lines.append(asp.fact("clue_seen", incident))
        lines.append(asp.fact("repair_chosen", incident))
        lines.append(asp.fact("safe_result", incident))
    lines.extend(
        [
            asp.fact("hero", "stage_child"),
            asp.fact("asked_question", "stage_child"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Make a gentle nursery-rhyme tale about a stage, a star, and a curious child."
    )
    parser.add_argument("--stage", choices=STAGE_REGISTRY)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--incident", choices=INCIDENTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    stage = args.stage or rng.choice(list(STAGE_REGISTRY))
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    if helper == hero:
        raise StoryError("The helper should be a different person from the curious child.")
    incident = args.incident or rng.choice(list(INCIDENTS))
    return StoryParams(stage=stage, hero_name=hero, helper_name=helper, incident=incident)


def reasonableness_gate(params: StoryParams) -> None:
    if params.stage not in STAGE_REGISTRY:
        raise StoryError(f"Unknown stage: {params.stage}")
    if params.incident not in INCIDENTS:
        raise StoryError(f"Unknown stage-star problem: {params.incident}")
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("The child and helper must both have names.")
    if params.hero_name.strip().casefold() == params.helper_name.strip().casefold():
        raise StoryError("The helper should be a different person from the curious child.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    stage = STAGE_REGISTRY[params.stage]
    incident = INCIDENTS[params.incident]
    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.stage}:{params.hero_name}:{params.helper_name}:{params.incident}"
    )
    world = World(stage)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero_name,
            type="curious_child",
            location="stage",
            meters={"attention": 0.2, "confidence": 0.4},
            memes={"curiosity": 0.8, "worry": 0.2, "pride": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper_name,
            type="friend",
            location="stage",
            meters={"helpfulness": 0.8},
            memes={"patience": 0.8, "kindness": 0.8},
        )
    )
    star = world.add(
        Entity(
            id="star",
            kind="prop",
            label="paper star",
            type="stage_decoration",
            owner=hero.id,
            location="stage",
            meters={incident["meter"]: 0.2, "damage": 0.0},
            memes={"hope": 0.8, "worry": 0.1},
        )
    )

    openings = [
        f"At {stage.name}, where the floorboards creaked a tune, {params.hero_name} set a paper star on the stage.",
        f"The {stage.phrase} was ready for a little play, but {params.hero_name} had one starry puzzle to sway.",
        f"Before the audience came to {stage.room}, {params.hero_name} carried a bright paper star to the stage.",
    ]
    world.say(rng.choice(openings))
    world.say(incident["premise"])
    world.say(incident["mistake"].replace("Mira", params.hero_name))
    world.say(
        f"{params.hero_name} thought, “What is making the star seem wrong? "
        "I will look before I try again.”"
    )
    hero.meters["attention"] = 0.9
    hero.memes["worry"] = 0.4
    star.memes["worry"] = 0.5

    world.say(
        f"“I wonder what the star is telling us,” said {params.hero_name}. "
        f"“Let us watch it carefully,” said {params.helper_name}."
    )
    world.say(incident["clue"].replace("Pip", params.helper_name))
    world.say(
        f"{params.hero_name} nodded. “Now I see! Let us fix what is causing it, "
        "not tug at the star.”"
    )

    # The clue changes the child's choice, and the repair changes the stage state.
    world.say(incident["change"].replace("They", f"{params.hero_name} and {params.helper_name}"))
    star.meters[incident["meter"]] = 1.0
    star.memes["worry"] = 0.0
    star.memes["hope"] = 1.0
    hero.meters["confidence"] = 0.9
    hero.memes["curiosity"] = 1.0
    hero.memes["pride"] = 0.8
    world.say(incident["result"])
    world.say(
        f"{params.helper_name} smiled. “Your careful question found the answer.” "
        f"{params.hero_name} beamed. “And now our star is ready to shine!”"
    )
    world.say(incident["ending"])

    world.facts.update(
        hero=hero,
        helper=helper,
        star=star,
        stage=stage,
        incident=params.incident,
        clue=incident["clue"].replace("Pip", params.helper_name),
        repair=incident["change"].replace("They", f"{params.hero_name} and {params.helper_name}"),
        result=incident["result"],
        lesson=incident["lesson"],
        solved=True,
    )

    prompts = [
        f"Write a nursery-rhyme-style story about {params.hero_name}, a curious child on {stage.phrase}, and a paper star.",
        f"Show how {params.hero_name} and {params.helper_name} use this clue: {incident['clue'].replace('Pip', params.helper_name)}",
        f"Include a gentle inner thought, a spoken exchange, and the lesson: {incident['lesson']}.",
    ]
    story_qa = [
        QAItem(
            question="What went wrong with the paper star?",
            answer=incident["premise"],
        ),
        QAItem(
            question=f"What did {params.hero_name} and {params.helper_name} notice?",
            answer=incident["clue"].replace("Pip", params.helper_name),
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=incident["change"].replace("They", f"{params.hero_name} and {params.helper_name}"),
        ),
        QAItem(
            question=f"What did {params.hero_name} learn?",
            answer=f"{params.hero_name} learned to {incident['lesson']}.",
        ),
        QAItem(
            question="What showed that their solution worked?",
            answer=incident["result"],
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a stage?",
            answer="A stage is a raised or marked place where people perform plays, music, or other shows for an audience.",
        ),
        QAItem(
            question="Why might a paper star move on a stage?",
            answer="A paper star can move when a draft, loose thread, curtain, or nearby object pushes or catches it.",
        ),
        QAItem(
            question="What does curiosity help someone do?",
            answer="Curiosity helps someone ask questions, look for clues, and understand a problem before choosing what to do.",
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


def asp_verify() -> int:
    import asp

    show = "#show ready_for_show/1.\n#show curious_hero/1.\n#show solved/1."
    model = asp.one_model(asp_program(show))
    actual = {
        (symbol.name, tuple(
            arg.string if arg.type == arg.type.String
            else arg.number if arg.type == arg.type.Number
            else arg.name
            for arg in symbol.arguments
        ))
        for symbol in model
    }
    expected = {
        ("ready_for_show", (incident,))
        for incident in INCIDENTS
    } | {
        ("solved", (incident,))
        for incident in INCIDENTS
    } | {("curious_hero", ("stage_child",))}
    if actual != expected:
        print("MISMATCH between ASP and Python reasoning.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for index, incident_name in enumerate(INCIDENTS):
        params = StoryParams(
            stage=list(STAGE_REGISTRY)[index % len(STAGE_REGISTRY)],
            hero_name=HERO_NAMES[index],
            helper_name=HELPER_NAMES[index],
            incident=incident_name,
            seed=index,
        )
        sample = generate(params)
        if (
            not sample.world.facts.get("solved")
            or sample.world.entities["star"].meters[INCIDENTS[incident_name]["meter"]] != 1.0
            or "thought," not in sample.story
            or "said " not in sample.story
            or not sample.story.endswith(INCIDENTS[incident_name]["ending"])
        ):
            print(f"Generated-story check failed for {incident_name}.")
            return 1

    print("OK: ASP and Python parity looks good; generated stories pass their checks.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ready_for_show/1.\n#show curious_hero/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, incident in enumerate(INCIDENTS):
            params = StoryParams(
                stage=list(STAGE_REGISTRY)[index % len(STAGE_REGISTRY)],
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                incident=incident,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

    if args.asp:
        import asp

        show = "#show ready_for_show/1.\n#show curious_hero/1.\n#show solved/1."
        for symbol in asp.one_model(asp_program(show)):
            print(symbol)
        if not args.json:
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
