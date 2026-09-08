#!/usr/bin/env python3
"""A child-facing pirate tale about a historic shutter, friendship, and problem solving."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ShutterCase:
    problem: str
    risk: str
    first_test: str
    failed_reason: str
    clue: str
    cause: str
    brave_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class HistoricShutter:
    name: str
    material: str
    age: str
    open: bool = False
    secure: bool = False
    preserved: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    harbor: Place
    captain: Creature
    friend: Creature
    shutter: HistoricShutter
    case: ShutterCase
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HARBORS = {
    "Lantern Cove": Place("Lantern Cove", "historic harbor"),
    "Bell Reef": Place("Bell Reef", "rocky harbor"),
    "Maple Quay": Place("Maple Quay", "old harbor"),
}

CAPTAINS = [
    ("Luna", "parrot"),
    ("Mara", "cat"),
    ("Tavi", "otter"),
]

FRIENDS = [
    ("Pip", "monkey"),
    ("Nell", "seal"),
    ("Bo", "penguin"),
]

SHUTTERS = [
    ("the tide-watch shutter", "cedar", "one hundred years old"),
    ("the bell-house shutter", "oak", "eighty years old"),
    ("the map-room shutter", "pine", "ninety years old"),
]

CASES = {
    "swollen_hinge": ShutterCase(
        "the historic shutter would not close",
        "a storm could blow salt water into the harbor's old map room",
        "lifted the shutter gently with a rope sling",
        "the shutter moved, but its lower edge still scraped the stone sill",
        "a line of damp sand glittered beneath one hinge",
        "a high tide had pushed sand into the hinge pocket and raised the shutter crookedly",
        "asked her friend to hold the rope while she stayed on the dry side of the sill",
        "brushed out the sand, oiled the hinge, and fitted a small cedar guide beneath the edge",
        "friends solve hard problems by sharing safe jobs and listening to evidence",
        "the historic shutter rested straight while the map room stayed dry beneath a clear moon",
    ),
    "loose_latch": ShutterCase(
        "the old shutter kept swinging open",
        "a gust could slam it against the bell-house wall",
        "tested the latch with a soft tug instead of forcing it",
        "the latch held once, but sprang free when the shutter shook",
        "a bright brass shaving lay inside the latch hole",
        "a worn latch pin had bent against a hidden nail",
        "kept everyone behind the painted safety line while her friend fetched the tool box",
        "removed the nail, replaced the pin, and tied a gentle storm cord through the new ring",
        "problem solving means finding the part that fails instead of blaming the whole object",
        "the old shutter clicked shut and held steady as the harbor bell rang",
    ),
    "salt_crack": ShutterCase(
        "a narrow crack had appeared in the historic shutter",
        "rain might enter and weaken the treasured wood",
        "held a paper sail near the crack to see whether air passed through",
        "the paper did not move, so the mark was not an open split",
        "white salt traced the mark after the morning fog dried",
        "salt had dried on the surface and made a harmless line look like a crack",
        "told her friend the scary guess before choosing a calm inspection",
        "washed the salt away, sealed the sound wood with harbor wax, and recorded the check",
        "friendship grows when people share worries honestly and test them kindly",
        "the cedar grain shone cleanly while two friends logged its history together",
    ),
    "stuck_bar": ShutterCase(
        "the wooden bar would not slide into place",
        "the shutter could not be secured before the evening squall",
        "checked whether the bar was straight with a marked deck plank",
        "the bar was straight, so bending was not the cause",
        "a tiny shell was wedged deep in the bar channel",
        "a wave had tossed the shell through an open vent during high tide",
        "worked from the sheltered deck and let her friend watch the channel",
        "lifted out the shell with a hook, cleaned the channel, and tested the bar three times",
        "careful teamwork can turn a stuck answer into a chain of small questions",
        "the bar slid home with a friendly wooden knock before the squall arrived",
    ),
    "missing_pin": ShutterCase(
        "the shutter's wooden safety pin was missing",
        "the panel might swing loose while visitors stood nearby",
        "searched the marked tool tray and the floor around the hinge",
        "the pin was nowhere in the tray or under the shutter",
        "a round scrape circled the captain's brass compass case",
        "the pin had rolled beneath the compass case when the deck tilted",
        "asked her friend to steady the display while she used a cloth-covered hook",
        "retrieved the pin, added a cord loop, and checked that the display was stable",
        "a friend can protect both a precious object and a worried person during a search",
        "the pinned shutter guarded the compass while gulls wheeled above the quiet quay",
    ),
}

ROUTES = (
    "clue_first",
    "dialogue_first",
    "storm_first",
    "history_first",
    "friend_first",
    "question_first",
)


ASP_RULES = r"""
safe_action(captain) :- captain(captain), has_friend(captain), uses_evidence(captain).
solved(shutter) :- shutter(shutter), cause_known(shutter), repair_planned(shutter).
valid_story :- safe_action(captain), solved(shutter).
"""


def safe_id(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("captain", "captain"),
        asp.fact("has_friend", "captain"),
        asp.fact("uses_evidence", "captain"),
        asp.fact("shutter", "shutter"),
        asp.fact("cause_known", "shutter"),
        asp.fact("repair_planned", "shutter"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = set(asp.atoms(model, "valid_story"))
    if valid == {()}:
        print("OK: clingo gate matches python reasoning.")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(valid))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.harbor,
            params.captain_name,
            params.friend_name,
            params.shutter_name,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


@dataclass
class StoryParams:
    seed: Optional[int] = None
    harbor: str = "Lantern Cove"
    captain_name: str = "Luna"
    captain_species: str = "parrot"
    friend_name: str = "Pip"
    friend_species: str = "monkey"
    shutter_name: str = "the tide-watch shutter"
    shutter_material: str = "cedar"
    shutter_age: str = "one hundred years old"
    case: str = "swollen_hinge"
    route: str = "clue_first"


def build_world(params: StoryParams) -> World:
    if params.harbor not in HARBORS:
        raise StoryError(f"Unknown harbor: {params.harbor}")
    if params.case not in CASES:
        raise StoryError(f"Unknown shutter problem: {params.case}")
    harbor = HARBORS[params.harbor]
    shutter_case = CASES[params.case]
    return World(
        harbor=Place(harbor.name, harbor.kind),
        captain=Creature(params.captain_name, params.captain_species, "young captain"),
        friend=Creature(params.friend_name, params.friend_species, "trusted friend"),
        shutter=HistoricShutter(
            params.shutter_name,
            params.shutter_material,
            params.shutter_age,
        ),
        case=shutter_case,
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    captain = world.captain
    friend = world.friend
    harbor = world.harbor
    shutter = world.shutter
    case = world.case

    captain.memes.update(curiosity=1.0, courage=0.0)
    friend.memes.update(loyalty=1.0, patience=1.0)

    openings = {
        "clue_first": (
            f"At {harbor.name}, the historic {shutter.name} stood above the harbor steps. "
            f"One morning, {captain.name} the {captain.species} saw that {case.problem}."
        ),
        "dialogue_first": (
            f'"A pirate captain checks the harbor before sailing," {captain.name} said at {harbor.name}. '
            f'Then {captain.name} noticed that {case.problem}.'
        ),
        "storm_first": (
            f"Dark clouds gathered over {harbor.name}, where the {shutter.age} {shutter.name} guarded an old room. "
            f"Before the storm arrived, {captain.name} discovered that {case.problem}."
        ),
        "history_first": (
            f"The {shutter.name} had watched ships enter {harbor.name} for {shutter.age}. "
            f"{captain.name} wanted to protect its story, but first had to solve this problem: {case.problem}."
        ),
        "friend_first": (
            f"{captain.name} and {friend.name} were polishing the historic {shutter.name} at {harbor.name}. "
            f"They stopped when {captain.name} noticed that {case.problem}."
        ),
        "question_first": (
            f'"How can we keep the old shutter safe?" asked {captain.name} at {harbor.name}. '
            f'The question mattered because {case.problem}.'
        ),
    }

    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"It was not only an old piece of wood. {case.risk.capitalize()}.",
                f"The shutter carried the harbor's history, and {case.risk}.",
                f"Every sailor valued the shutter because {case.risk}.",
            ]
        )
    )
    world.say(
        f'"We can solve this together," {friend.name} said. '
        f'"You watch the shutter, and I will watch the safe path."'
    )
    world.say(
        f'"And we will trust what the clues tell us," {captain.name} replied.'
    )

    world.para()
    world.say(f"First, {captain.name} {case.first_test}.")
    world.say(
        rng.choice(
            [
                f"The test did not settle the problem because {case.failed_reason}.",
                f"That first idea failed: {case.failed_reason}.",
                f'"That is useful, even though it is not the answer," {captain.name} said, because {case.failed_reason}.',
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"Then {friend.name} spotted the important clue: {case.clue}.",
                f"Together they looked again. {case.clue.capitalize()}.",
                f"{captain.name} followed the evidence until {case.clue}.",
            ]
        )
    )
    world.say(f"At last, they understood the cause: {case.cause}.")
    world.facts["cause"] = case.cause

    world.para()
    world.say(
        rng.choice(
            [
                f"{captain.name} felt a flutter of fear, but {captain.name} {case.brave_action}.",
                f'"I am nervous," {captain.name} admitted. "I can still choose the safe step." Then {captain.name} {case.brave_action}.',
                f"Friendship made the next action possible: {captain.name} {case.brave_action}.",
            ]
        )
    )
    captain.memes["courage"] = 1.0
    world.say(
        rng.choice(
            [
                f"{friend.name} helped while {captain.name} checked the historic wood, and together they {case.repair}.",
                f'"Slow and steady," {friend.name} said as they {case.repair}.',
                f"The repair matched the evidence. They {case.repair}.",
            ]
        )
    )
    shutter.secure = True
    shutter.meters["hinge_checks"] = 3.0
    shutter.memes["trust"] = 1.0
    world.facts["repair"] = case.repair

    world.para()
    world.say(
        rng.choice(
            [
                f"{captain.name} wrote the lesson in the ship's log: {case.lesson}.",
                f'"What did we learn?" asked {friend.name}. {captain.name} answered, "{case.lesson.capitalize()}."',
                f"The solved problem left a bright rule for every young sailor: {case.lesson}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"By sunset, {case.ending}.",
                f"When the storm clouds sailed away, {case.ending}.",
                f"The harbor showed what had changed: {case.ending.capitalize()}.",
            ]
        )
    )
    world.facts.update(
        captain=captain,
        friend=friend,
        harbor=harbor,
        shutter=shutter,
        case=case,
        solved=True,
        friendship=True,
        bravery=captain.memes["courage"],
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a pirate tale about {world.captain.name} and {world.friend.name} protecting {world.shutter.name} at {world.harbor.name}.",
        f"Tell a friendship and problem-solving story in which the real cause is that {world.case.cause}.",
        f"End with this image: {world.case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain = world.captain
    friend = world.friend
    shutter = world.shutter
    case = world.case
    harbor = world.harbor
    return [
        QAItem(
            question=f"What problem did {captain.name} find at {harbor.name}?",
            answer=f"{captain.name} found that {case.problem}. It mattered because {case.risk}.",
        ),
        QAItem(
            question=f"Why did the first test not solve the problem with {shutter.name}?",
            answer=f"{captain.name} {case.first_test}. That test did not settle the problem because {case.failed_reason}.",
        ),
        QAItem(
            question=f"What clue helped {captain.name} and {friend.name} discover the cause?",
            answer=f"They noticed that {case.clue}. This showed that {case.cause}.",
        ),
        QAItem(
            question=f"How did friendship help solve the shutter problem?",
            answer=f"{friend.name} helped {captain.name} share the safe jobs and listen to the evidence. Together they {case.repair}.",
        ),
        QAItem(
            question=f"What lesson did {captain.name} learn?",
            answer=f"{captain.name} learned that {case.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a hinged panel that can cover a window or opening and help protect the place behind it.",
        ),
        QAItem(
            question="Why is the shutter historic?",
            answer=f"This shutter is historic because it has guarded {world.harbor.name} for {world.shutter.age} and carries part of the harbor's story.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing a difficulty, testing ideas safely, using evidence, and choosing a fitting repair.",
        ),
        QAItem(
            question="How can friends work safely together?",
            answer="Friends can divide clear jobs, communicate their worries, stay within safe boundaries, and listen to one another's observations.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Historic shutter pirate tale about friendship and problem solving."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--harbor", choices=sorted(HARBORS))
    parser.add_argument("--captain-name")
    parser.add_argument("--friend-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    harbor = args.harbor or rng.choice(sorted(HARBORS))
    captain_name, captain_species = rng.choice(CAPTAINS)
    friend_name, friend_species = rng.choice(FRIENDS)
    shutter_name, material, age = rng.choice(SHUTTERS)
    case_name = rng.choice(sorted(CASES))
    return StoryParams(
        seed=args.seed,
        harbor=harbor,
        captain_name=args.captain_name or captain_name,
        captain_species=captain_species,
        friend_name=args.friend_name or friend_name,
        friend_species=friend_species,
        shutter_name=shutter_name,
        shutter_material=material,
        shutter_age=age,
        case=case_name,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.harbor, world.captain, world.friend, world.shutter):
        lines.append(
            f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}"
        )
    lines.append(
        f"case: cause={world.facts['cause']!r} repair={world.facts['repair']!r} "
        f"solved={world.facts['solved']}"
    )
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []

    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
