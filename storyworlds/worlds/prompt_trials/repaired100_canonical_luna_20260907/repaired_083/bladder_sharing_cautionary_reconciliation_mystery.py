#!/usr/bin/env python3
"""
A small mystery storyworld about bladder-sharing, caution, and reconciliation.

The story follows Luna and a friend who discover that a shared bladder-shaped
water balloon has been assigned to the wrong team. Careful checking prevents a
mess, and an honest conversation repairs trust.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class Case:
    case_id: str
    setup: str
    clue: str
    trouble: str
    first_guess: str
    test: str
    twist: str
    repair: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    case_id: str = "blue_thread"
    telling_mode: str = "clue_first"
    detail_id: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


CASES = {
    "blue_thread": Case(
        case_id="blue_thread",
        setup="At the sharing table, a round water bladder rested under a blue cloth",
        clue="one blue thread was caught beneath its strap",
        trouble="the label on the bladder said it belonged to Luna's team, but the thread matched Mara's scarf",
        first_guess="that Mara had taken Luna's team's bladder by mistake",
        test="compare the strap, the label, and the sign-out card while keeping the bladder closed",
        twist="the label had been copied before the teams changed places",
        repair="admit the mix-up, give the bladder to Mara's team for this round, and write fresh labels together",
        lesson="sharing works best when people check both objects and promises before blaming anyone",
        ending="the bladder passed safely between the teams beneath two bright, matching labels",
    ),
    "hidden_mark": Case(
        case_id="hidden_mark",
        setup="A shared bladder sat beside three empty cups",
        clue="a tiny silver star showed only when the bladder was turned toward the window",
        trouble="both teams thought the bladder was theirs, and one child reached for its knot",
        first_guess="that the star was only a scratch",
        test="ask an adult to hold the bladder still and compare its star with the inventory picture",
        twist="the star was the mark for the community team's spare bladder",
        repair="move the spare to the center shelf and invite both teams to use it in turns",
        lesson="a small mark can carry an important promise about shared property",
        ending="the silver star flashed from the center shelf as each team took a fair turn",
    ),
    "missing_card": Case(
        case_id="missing_card",
        setup="The activity box held a bladder, two cups, and one empty card pocket",
        clue="a torn corner of paper clung to the box's wet side",
        trouble="without its card, nobody knew whether the bladder was full or reserved",
        first_guess="that someone had hidden the instructions",
        test="dry the box, ask each team what they remembered, and compare their stories with the supply list",
        twist="the card had stuck to the underside of the box after a spill",
        repair="replace the card, mark the safe fill line, and agree that either team may request a turn",
        lesson="missing information should invite questions, not accusations",
        ending="the repaired card stood in its pocket while the bladder waited at the safe fill line",
    ),
    "double_knot": Case(
        case_id="double_knot",
        setup="Two knots appeared at the neck of one large bladder",
        clue="only one knot had a green paint dot",
        trouble="the children argued over which knot opened the shared container",
        first_guess="that the bladder had two owners",
        test="stop pulling, call the caretaker, and inspect the paint dot on the instruction sheet",
        twist="one knot was a safety tie and the other was the carrying loop",
        repair="leave the safety tie closed, use the loop to carry the bladder, and share it by a written turn list",
        lesson="careful rules protect shared things and shared friendships",
        ending="the green-dotted safety knot stayed closed while the turn list traveled from hand to hand",
    ),
}

MODES = ("clue_first", "dialogue_first", "question_first", "quiet_first", "helper_first")

OPENINGS = {
    "clue_first": "{hero} noticed the first clue before anyone noticed the mystery.",
    "dialogue_first": "\"Let's share fairly,\" said {friend}, as {hero} carried the activity box.",
    "question_first": "Why was one bladder listed for two teams? Luna was about to find out.",
    "quiet_first": "The room was quiet except for cups tapping beside the shared supplies.",
    "helper_first": "{friend} checked the table while {hero} readied the shared bladder.",
}

BRIDGES = (
    "The clue was small, but Luna kept it in mind.",
    "Luna pointed to it. \"That may matter,\" she said.",
    "They did not touch the object until they understood the clue.",
    "The mystery waited while both teams stood back.",
    "Mara drew the clue on the sign-out card so nobody would forget it.",
)

REPLIES = (
    "\"We have a guess, not proof,\" said Luna.",
    "\"Let's ask before we accuse,\" Mara replied.",
    "Mara nodded. \"Sharing means checking together.\"",
    "\"Stop and look carefully,\" Luna said.",
    "The two friends agreed that a calm question was safer than a quick tug.",
)


def story_reasonable(hero_name: str, friend_name: str, case_id: str) -> bool:
    return bool(hero_name.strip()) and bool(friend_name.strip()) and case_id in CASES


def tell(params: StoryParams) -> World:
    if not story_reasonable(params.hero_name, params.friend_name, params.case_id):
        raise StoryError("The story needs two named friends and a registered mystery case.")
    world = World()
    case = CASES[params.case_id]
    hero = world.add(Entity("hero", "character", params.hero_name))
    friend = world.add(Entity("friend", "character", params.friend_name))
    bladder = world.add(Entity("shared_bladder", "object", "a shared water bladder"))
    bladder.add_meter("water", 0.6)
    bladder.add_meter("distance", 1.0)
    bladder.add_meme("trust", 0.8)
    bladder.add_meme("care", 1.0)

    world.facts.update(hero=hero, friend=friend, bladder=bladder, case=case)

    mode = params.telling_mode if params.telling_mode in OPENINGS else "clue_first"
    world.say(OPENINGS[mode].format(hero=hero.label, friend=friend.label))
    world.say(
        f"In the bright activity room, {hero.label} and {friend.label} were preparing to share "
        "water with two teams."
    )
    world.say(f"{case.setup}. It looked ordinary until they saw that {case.clue}.")
    world.say(BRIDGES[params.detail_id % len(BRIDGES)])
    world.say(f"The clue mattered because {case.trouble}.")
    world.say(f"At first, they guessed {case.first_guess}.")
    world.say(REPLIES[(params.detail_id + 1) % len(REPLIES)])
    world.say(
        f"Instead of grabbing the bladder, they decided to {case.test}. "
        "They kept the container closed and safe while they compared the facts."
    )
    world.say(f"Then the mystery turned: {case.twist}.")
    world.say(
        f"{hero.label} took a breath. \"I want this to be fair,\" {hero.label} said. "
        f"{friend.label} answered, \"Me too. Let's fix it together.\" "
        f"Together they chose to {case.repair}."
    )
    hero.add_meme("trust", 0.5)
    friend.add_meme("trust", 0.5)
    world.say(f"They learned that {case.lesson}.")
    world.say(
        f"At the end, {case.ending}. "
        "No one had to hide a mistake, because careful sharing had made room for honesty."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly mystery about {hero.label} investigating a shared bladder.",
        f"Include the clue that {case.clue}, a cautious test, reconciliation, and a fair ending.",
        f"Show why {case.lesson} through dialogue and a concrete change in the shared object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What mystery did {hero.label} and {friend.label} investigate?",
            f"They investigated a shared bladder whose ownership and turn were unclear because {case.trouble}.",
        ),
        QAItem(
            "What clue helped them?",
            f"The clue was that {case.clue}. It gave them a fact to check instead of a reason to blame someone.",
        ),
        QAItem(
            "What did they first think?",
            f"They first thought {case.first_guess}, but they treated that idea as a guess rather than proof.",
        ),
        QAItem(
            "How did they stay cautious?",
            f"They stayed cautious by choosing to {case.test}. They kept the bladder closed and safe while checking.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {case.twist}.",
        ),
        QAItem(
            "How did the friends reconcile?",
            f"They reconciled by choosing to {case.repair}. They admitted the mix-up and made a fair plan together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a bladder?",
            "A bladder is a flexible container or body part that can hold liquid; in this story, it is a shared water container.",
        ),
        QAItem(
            "Why should children be cautious with a water bladder?",
            "They should keep it closed, avoid pulling its knots, and ask a responsible adult before moving or filling it.",
        ),
        QAItem(
            "What does sharing mean?",
            "Sharing means allowing others a fair use of something while caring for it together.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is repairing a disagreement through honesty, listening, and a fair new plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_case/1.
#show safe_story/1.

valid_case(C) :- case(C).
safe_story(C) :- valid_case(C), has_bladder(C), has_sharing(C), has_caution(C), has_reconciliation(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for case_id in CASES:
        lines.extend(
            [
                asp.fact("case", case_id),
                asp.fact("has_bladder", case_id),
                asp.fact("has_sharing", case_id),
                asp.fact("has_caution", case_id),
                asp.fact("has_reconciliation", case_id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_case/1."))
    return sorted(asp.atoms(model, "valid_case"))


def asp_verify() -> int:
    asp_cases = {item[0] for item in asp_valid_cases()}
    py_cases = set(CASES)
    if asp_cases != py_cases:
        print("MISMATCH between ASP and Python:")
        print("ASP only:", sorted(asp_cases - py_cases))
        print("Python only:", sorted(py_cases - asp_cases))
        return 1
    for case_id in py_cases:
        params = StoryParams("Luna", "Mara", case_id=case_id)
        sample = generate(params)
        if not sample.story or "bladder" not in sample.story.lower():
            print(f"Generated story failed for {case_id}.")
            return 1
    print(f"OK: ASP gate matches Python registry ({len(py_cases)} cases), and stories generate.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bladder-sharing cautionary reconciliation mystery storyworld.")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--case-id", choices=sorted(CASES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: Optional[int] = None) -> StoryParams:
    hero = getattr(args, "hero_name", None) or rng.choice(["Luna", "Mia", "Nia", "Pip"])
    friend = getattr(args, "friend_name", None) or rng.choice(["Mara", "Theo", "Sam", "Jules"])
    case_id = getattr(args, "case_id", None) or rng.choice(list(CASES))
    index = sample_seed if sample_seed is not None else rng.randrange(2**31)
    return StoryParams(
        hero_name=hero,
        friend_name=friend,
        case_id=case_id,
        telling_mode=MODES[(index // len(CASES)) % len(MODES)],
        detail_id=index % len(BRIDGES),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Mara", "blue_thread", "clue_first", 0),
    StoryParams("Luna", "Theo", "hidden_mark", "dialogue_first", 1),
    StoryParams("Luna", "Sam", "missing_card", "question_first", 2),
    StoryParams("Luna", "Jules", "double_knot", "quiet_first", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("\n".join(str(item) for item in asp_valid_cases()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            params = resolve_params(args, random.Random(base_seed + index), base_seed + index)
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
