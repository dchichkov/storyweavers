#!/usr/bin/env python3
"""
A tiny heartwarming pirate quest in a dining room.

The model follows two children as they decide whether to rescue a darling
stuffed seal from a high dining-room chair. Suspense rises while the safer
choice becomes clear: ask a grown-up and use a sturdy step stool.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    kind: str
    role: str
    age: int
    memes: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Prop:
    id: str
    label: str
    safe: bool
    height: int = 0
    meters: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, item: object, item_id: str) -> object:
        self.entities[item_id] = item
        return item

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Quest:
    id: str
    goal: str
    place: str
    prize: str
    danger: str
    safe_method: str


QUESTS = {
    "seal": Quest(
        id="seal",
        goal="rescue the darling stuffed seal",
        place="dining room",
        prize="a warm hug and a place beside the treasure map",
        danger="a tall chair could wobble",
        safe_method="a grown-up and a sturdy step stool",
    ),
    "parrot": Quest(
        id="parrot",
        goal="bring down the darling toy parrot",
        place="dining room",
        prize="a bright perch beside the captain's cup",
        danger="a stack of chairs could tumble",
        safe_method="a grown-up and a sturdy step stool",
    ),
    "rabbit": Quest(
        id="rabbit",
        goal="fetch the darling plush rabbit",
        place="dining room",
        prize="a soft nest beside the treasure chest",
        danger="a slippery chair could slide",
        safe_method="a grown-up and a sturdy step stool",
    ),
}

NAMES = {
    "girl": ["Lily", "Mia", "Zoe", "Ava", "Nora"],
    "boy": ["Tom", "Ben", "Max", "Leo", "Sam"],
}
PIRATE_ROLES = ["captain", "navigator", "map keeper", "deck officer"]
COMFORTS = ["a striped scarf", "a little compass", "a blue ribbon"]


@dataclass
class StoryParams:
    quest: str
    captain: str
    captain_gender: str
    helper: str
    helper_gender: str
    grownup: str
    role: str
    comfort: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming dining-room pirate quest."
    )
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--captain")
    parser.add_argument("--helper")
    parser.add_argument("--grownup", choices=["mom", "dad", "grandma", "grandpa"])
    parser.add_argument("--role", choices=PIRATE_ROLES)
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


def _choose_child(rng: random.Random, gender: Optional[str] = None,
                  avoid: str = "") -> tuple[str, str]:
    gender = gender or rng.choice(["girl", "boy"])
    choices = [n for n in NAMES[gender] if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain, captain_gender = _choose_child(rng)
    helper, helper_gender = _choose_child(rng, avoid=captain)
    if args.captain:
        captain = args.captain
    if args.helper:
        if args.helper == captain:
            raise StoryError("The captain and helper need different names.")
        helper = args.helper
    return StoryParams(
        quest=args.quest or rng.choice(sorted(QUESTS)),
        captain=captain,
        captain_gender=captain_gender,
        helper=helper,
        helper_gender=helper_gender,
        grownup=args.grownup or rng.choice(["mom", "dad", "grandma", "grandpa"]),
        role=args.role or rng.choice(PIRATE_ROLES),
        comfort=rng.choice(COMFORTS),
    )


def _pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def tell(params: StoryParams) -> World:
    quest = QUESTS[params.quest]
    world = World()
    captain = Character(params.captain, "child", "captain", 6)
    helper = Character(params.helper, "child", "navigator", 5)
    grownup = Character(params.grownup, "adult", "helper", 35)
    chair = Prop("chair", "tall dining chair", safe=False, height=2)
    stool = Prop("stool", "sturdy step stool", safe=True, height=2)
    darling = Prop("darling", quest.prize.split(" and ")[0], safe=True, height=0)

    world.add(captain, "captain")
    world.add(helper, "helper")
    world.add(grownup, "grownup")
    world.add(chair, "chair")
    world.add(stool, "stool")
    world.add(darling, "darling")

    captain.memes["joy"] = 1
    helper.memes["care"] = 1
    captain.meters["quest_progress"] = 1
    world.facts.update(
        quest=quest,
        captain=captain,
        helper=helper,
        grownup=grownup,
        chair=chair,
        stool=stool,
        darling=darling,
        decided=False,
        safe=True,
    )

    world.say(
        f"After lunch, {params.captain} and {params.helper} turned the dining room "
        f"into a pirate ship. The table was the deck, the napkins were sails, and "
        f"{params.captain} wore {params.comfort} like a captain's badge."
    )
    world.say(
        f'"Crew, our quest is clear!" {params.captain} announced. '
        f'"We must {quest.goal}."'
    )
    world.say(
        f"Their darling treasure sat high on the {chair.label}, just beyond "
        f"{params.helper}'s fingertips."
    )
    world.para()
    world.say(
        f"{params.captain} looked at the chair. The room seemed suddenly quiet. "
        f"Inside, { _pronoun(params.captain_gender) } wondered, "
        f'"Could I climb up quickly and be back before anyone noticed?"'
    )
    world.say(
        f'"I could reach it," {params.captain} whispered. '
        f'"But should I?"'
    )
    world.say(
        f'{params.helper} touched the edge of the map. "{params.captain}, wait. '
        f'{quest.danger.capitalize()}. Let\'s decide carefully."'
    )
    helper.memes["wisdom"] = 1
    world.facts["suspense"] = "high"
    world.say(
        f"For one long moment, the pirate crew held its breath. The quest felt "
        f"close enough to touch, but a tumble would hurt."
    )
    world.para()
    world.say(
        f'"You are right," {params.captain} said. "A real captain does not '
        f'rush into danger. We will ask {params.grownup}."'
    )
    captain.memes["wisdom"] = 1
    captain.meters["quest_progress"] = 2
    world.facts["decided"] = True
    world.say(
        f'"{params.grownup}!" {params.helper} called. "Could you help with our quest?"'
    )
    world.say(
        f"{params.grownup.capitalize()} came in, smiled, and brought the "
        f"{stool.label}. {params.grownup.capitalize()} held it steady while "
        f"{params.captain} climbed one careful step."
    )
    captain.meters["quest_progress"] = 3
    world.say(
        f"At last, the darling treasure was safe in {params.captain}'s arms. "
        f"The crew cheered, and the dining-room ship felt bright again."
    )
    world.say(
        f'"We made it safely," {params.captain} said. '
        f'"That was the best kind of victory."'
    )
    world.say(
        f"{params.helper} placed the treasure beside the map. "
        f"The quest ended with {quest.prize}."
    )
    world.facts["suspense"] = "resolved"
    return world


def generation_prompts(world: World) -> list[str]:
    quest: Quest = world.facts["quest"]
    captain: Character = world.facts["captain"]
    helper: Character = world.facts["helper"]
    return [
        f"Write a heartwarming pirate Quest in a dining room where {captain.id} "
        f"must decide how to {quest.goal}.",
        f"Include Inner Monologue as {captain.id} wonders whether climbing is safe, "
        f"Suspense while the choice hangs in the air, and dialogue with {helper.id}.",
        f"End with a grown-up helping the children complete the quest safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    quest: Quest = world.facts["quest"]
    captain: Character = world.facts["captain"]
    helper: Character = world.facts["helper"]
    grownup: Character = world.facts["grownup"]
    return [
        QAItem(
            f"What quest did {captain.id} and {helper.id} have?",
            f"They had to {quest.goal} in the dining room.",
        ),
        QAItem(
            f"Why was {captain.id} unsure about climbing the chair?",
            f"{captain.id} realized that {quest.danger}, so climbing could hurt someone.",
        ),
        QAItem(
            f"What did {helper.id} say before {captain.id} decided?",
            f"{helper.id} told {captain.id} to wait and decide carefully because the chair might be unsafe.",
        ),
        QAItem(
            f"Who helped the children finish the quest?",
            f"{grownup.id.capitalize()} brought a sturdy step stool and held it steady.",
        ),
        QAItem(
            f"How did the pirate quest end?",
            f"{captain.id} safely rescued the darling treasure, and the crew celebrated a careful victory.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should children ask a grown-up for help reaching something high?",
            "A grown-up can choose safe equipment and steady it, helping children avoid falls.",
        ),
        QAItem(
            "What is a safe way to reach a high place?",
            "Ask a grown-up and use a sturdy step stool or ladder correctly; never climb a wobbly chair.",
        ),
        QAItem(
            "What does it mean to decide carefully?",
            "It means pausing, thinking about what could happen, listening to good advice, and choosing the safer action.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for key, item in world.entities.items():
        if isinstance(item, (Character, Prop)):
            lines.append(
                f"  {key}: {item.id} "
                f"meters={item.meters} memes={item.memes}"
            )
    lines.append(f"  decided={world.facts['decided']}")
    lines.append(f"  suspense={world.facts['suspense']}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_choice :- asked_for_help, sturdy_step_stool.
quest_complete :- safe_choice, darling_retrieved.
outcome(heartwarming) :- quest_complete.
"""


def asp_facts() -> str:
    return "\n".join([
        "asked_for_help.",
        "sturdy_step_stool.",
        "darling_retrieved.",
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show outcome/1.\n"


def asp_check() -> bool:
    try:
        import asp
        model = asp.one_model(asp_program())
        return bool(asp.atoms(model, "outcome"))
    except ImportError as exc:
        raise StoryError("ASP mode requires clingo and storyworlds/asp.py.") from exc


def verify() -> int:
    try:
        if not asp_check():
            print("ASP verification failed.")
            return 1
    except StoryError as exc:
        print(exc)
        return 1
    sample = generate(
        StoryParams(
            quest="seal",
            captain="Lily",
            captain_gender="girl",
            helper="Tom",
            helper_gender="boy",
            grownup="mom",
            role="captain",
            comfort="a blue ribbon",
        )
    )
    checks = [
        "dining room" in sample.story,
        "decide" in sample.story,
        "darling" in sample.story,
        "stool" in sample.story,
        len(sample.story_qa) >= 5,
    ]
    if all(checks):
        print("OK: Python story and ASP safety model agree.")
        return 0
    print("Verification failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("seal", "Lily", "girl", "Tom", "boy", "mom", "captain", "a blue ribbon"),
    StoryParams("parrot", "Max", "boy", "Mia", "girl", "dad", "navigator", "a little compass"),
    StoryParams("rabbit", "Ava", "girl", "Leo", "boy", "grandma", "map keeper", "a striped scarf"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print("ASP safety outcome available:", asp_check())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### Quest {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
