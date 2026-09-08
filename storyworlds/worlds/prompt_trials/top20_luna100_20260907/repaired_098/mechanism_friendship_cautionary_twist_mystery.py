#!/usr/bin/env python3
"""A child-facing mystery about friendship, a clever mechanism, and a safe twist."""

from __future__ import annotations

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
class Workshop:
    name: str
    kind: str = "workshop"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MysteryCase:
    clue: str
    danger: str
    first_test: str
    failed_reason: str
    mechanism_clue: str
    cause: str
    friendship_choice: str
    repair: str
    lesson: str
    ending: str


@dataclass
class Mystery:
    clue: str
    answer: str
    solved: bool = False


@dataclass
class World:
    workshop: Workshop
    maker: Creature
    friend: Creature
    mystery: Mystery
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


WORKSHOPS = {
    "moonlit shed": Workshop("the moonlit shed"),
    "blue gear room": Workshop("the blue gear room"),
    "willow workshop": Workshop("the willow workshop"),
}

MAKERS = [
    ("Luna", "fox"),
    ("Luna", "mouse"),
    ("Luna", "otter"),
    ("Luna", "rabbit"),
]

FRIENDS = [
    ("Pip", "sparrow"),
    ("Mara", "badger"),
    ("Theo", "turtle"),
    ("Nell", "squirrel"),
]

CASES = {
    "bell_gate": MysteryCase(
        clue="the warning bell rang by itself",
        danger="a startled friend might run into the busy path",
        first_test="held the bell rope still and watched the gate",
        failed_reason="the bell rang again even though the rope did not move",
        mechanism_clue="a bright thread ran from the bell hook to a loose wheel",
        cause="a wind-driven wheel was tugging the thread through a simple pulley mechanism",
        friendship_choice="told their friend the frightening truth instead of pretending everything was fine",
        repair="removed the loose wheel, tied the thread safely, and tested the bell with an empty path",
        lesson="a good friend shares a worry early and checks the cause before making a risky guess",
        ending="the bell gave one gentle note while the friends crossed the quiet path together",
    ),
    "turning_lantern": MysteryCase(
        clue="the workshop lantern kept turning toward the door",
        danger="someone might follow its moving light into a blocked corner",
        first_test="placed the lantern on a level table and marked its handle with chalk",
        failed_reason="the chalk mark turned even when the table stayed still",
        mechanism_clue="a small magnet glimmered beneath the table's wooden top",
        cause="a hidden magnet was pulling a metal plate inside the lantern's swivel mechanism",
        friendship_choice="asked their friend to stand back while they investigated together",
        repair="removed the magnet, steadied the swivel, and marked the safe place for the lantern",
        lesson="friendship means making room for another person's safety, not daring someone to come closer",
        ending="the lantern shone steadily over both friends as they packed away the tools",
    ),
    "clicking_box": MysteryCase(
        clue="a locked supply box clicked after sunset",
        danger="someone might force it open and break the tools inside",
        first_test="listened from the floor while their friend counted the clicks",
        failed_reason="the sound continued after the box was moved away from the wall",
        mechanism_clue="a springy metal tab pressed against the box lid",
        cause="the box's cooling latch was contracting and releasing through its locking mechanism",
        friendship_choice="stopped their friend from using a stick and explained why the noise needed patience",
        repair="waited for the metal to cool, opened the latch with its proper key, and softened the tab",
        lesson="a friend can prevent harm by slowing down a tempting but unsafe action",
        ending="the box rested silently on its shelf, with its key hanging on a bright blue hook",
    ),
    "rolling_sign": MysteryCase(
        clue="the safety sign rolled across the floor each morning",
        danger="the sign could block the workshop door during an emergency",
        first_test="set the sign upright and drew a line around its wheels",
        failed_reason="the wheels stayed inside the line, so someone had not pushed it",
        mechanism_clue="one wheel was linked to a slanted axle beneath the sign",
        cause="a loose axle mechanism turned whenever the floor warmed in the morning sun",
        friendship_choice="trusted their friend's observation even though the first idea had been theirs",
        repair="replaced the bent axle, added a wheel stop, and checked that the door opened fully",
        lesson="friendship grows when people listen to one another and change a plan when evidence changes",
        ending="the sign stood firm beside the open door, pointing everyone toward safety",
    ),
    "whistling_pipe": MysteryCase(
        clue="a pipe whistled whenever the friends entered",
        danger="the sharp sound could frighten someone into dropping a heavy tool",
        first_test="closed the nearest valve while their friend watched from the clear floor",
        failed_reason="the whistle remained, so that valve was not controlling the sound",
        mechanism_clue="a tiny flap trembled inside the pipe's side opening",
        cause="a loose flap mechanism was vibrating in the draft from the roof vent",
        friendship_choice="warned their friend before touching the pipe and accepted help from the caretaker",
        repair="closed the vent, secured the flap, and tested the pipe with both friends at a safe distance",
        lesson="caution is a way to care for friends before a small surprise becomes a large accident",
        ending="the pipe made only a soft breath while the friends laughed beside the quiet workbench",
    ),
    "vanishing_crank": MysteryCase(
        clue="the hand-crank on the little lift kept disappearing",
        danger="someone might reach beneath the lift to search for it",
        first_test="searched the floor with a ruler instead of putting hands under the platform",
        failed_reason="there were no scratches or dust marks where the crank should have fallen",
        mechanism_clue="a shiny catch appeared beside the lift's folding handle",
        cause="the crank was being pulled into a storage slot by a spring mechanism",
        friendship_choice="kept their friend behind the painted safety line while they inspected the catch",
        repair="released the spring safely, labeled the storage slot, and locked the lift before leaving",
        lesson="protecting a friend can mean choosing a slower method that keeps curious hands away from moving parts",
        ending="the crank rested in its labeled slot while the lift waited safely at floor level",
    ),
    "shaking_bridge": MysteryCase(
        clue="the model bridge shook without anyone touching it",
        danger="a friend might place a hand on it and be pinched by its moving pieces",
        first_test="watched the bridge from two marked spots while their friend tapped no part of it",
        failed_reason="the shaking began only when the nearby water wheel turned",
        mechanism_clue="a thin belt jumped against a small wooden gear",
        cause="the water wheel's vibrating belt was transferring motion through the gear mechanism",
        friendship_choice="asked their friend to step back and helped explain the evidence instead of blaming them",
        repair="stopped the wheel, tightened the belt, and added a soft guard around the gear",
        lesson="a careful friend looks for a connected cause before blaming the nearest person",
        ending="the model bridge stood still as a paper boat crossed its little stream",
    ),
    "shadow_switch": MysteryCase(
        clue="the workshop lights switched off when a shadow crossed the wall",
        danger="someone might hurry through the dark and trip over the tools",
        first_test="covered the wall sensor with a cloth while their friend stayed near the door",
        failed_reason="the lights still went out, so the shadow sensor was not the cause",
        mechanism_clue="a cord brushed the switch whenever the hanging coat swung",
        cause="the coat's swinging button was pressing the switch through a simple lever mechanism",
        friendship_choice="guided their friend to wait in the bright doorway rather than chase the swinging coat",
        repair="moved the coat, guarded the switch, and tested the lights with the floor clear",
        lesson="a trustworthy friend makes a safe waiting place before trying to solve a puzzling problem",
        ending="the lights stayed bright as the coat rested quietly on its peg",
    ),
}

CASES_LIST = list(CASES)
ROUTES = (
    "clue_first",
    "dialogue_first",
    "friend_first",
    "theory_first",
    "quiet_first",
    "countdown",
    "ending_first",
    "question_first",
)


ASP_RULES = r"""
brave(A) :- maker(A), sees_mystery(A), chooses_safe_action(A).
friendship(A,B) :- maker(A), friend(B), listens(A,B), protects(A,B).
solved(C) :- mystery(C), answer(C,_).
valid_story(C) :- brave(maker), friendship(maker,friend), mystery(C), solved(C).
"""


def case_id(clue: str) -> str:
    return "case_" + "".join(ch if ch.isalnum() else "_" for ch in clue.lower()).strip("_")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("maker", "maker"),
        asp.fact("friend", "friend"),
        asp.fact("sees_mystery", "maker"),
        asp.fact("chooses_safe_action", "maker"),
        asp.fact("listens", "maker", "friend"),
        asp.fact("protects", "maker", "friend"),
    ]
    for item in CASES.values():
        cid = case_id(item.clue)
        lines.append(asp.fact("mystery", cid))
        lines.append(asp.fact("answer", cid, item.cause))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show solved/1.\n#show friendship/2.\n#show brave/1.")
    )
    solved = set(asp.atoms(model, "solved"))
    friendship = set(asp.atoms(model, "friendship"))
    brave = set(asp.atoms(model, "brave"))
    expected_solved = {(case_id(item.clue),) for item in CASES.values()}
    if solved == expected_solved and friendship == {("maker", "friend")} and brave == {("maker",)}:
        print(f"OK: clingo gate matches python reasoning ({len(expected_solved)} mysteries).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo solved:", sorted(solved))
    print("python solved:", sorted(expected_solved))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.workshop_name,
            params.maker_name,
            params.maker_species,
            params.friend_name,
            params.friend_species,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


@dataclass
class StoryParams:
    seed: Optional[int] = None
    workshop_name: str = "the moonlit shed"
    maker_name: str = "Luna"
    maker_species: str = "fox"
    friend_name: str = "Pip"
    friend_species: str = "sparrow"
    clue: str = "the warning bell rang by itself"
    answer: str = "a wind-driven wheel was tugging the thread through a simple pulley mechanism"
    case: str = "bell_gate"
    route: str = "clue_first"


def build_world(params: StoryParams) -> World:
    if params.workshop_name not in WORKSHOPS:
        raise StoryError(f"Unknown workshop: {params.workshop_name}")
    if params.case not in CASES:
        raise StoryError(f"Unknown mystery case: {params.case}")
    if not params.maker_name.strip() or not params.friend_name.strip():
        raise StoryError("Character names must not be empty.")
    template = WORKSHOPS[params.workshop_name]
    return World(
        workshop=Workshop(template.name, template.kind),
        maker=Creature(params.maker_name, params.maker_species, "young mechanism maker"),
        friend=Creature(params.friend_name, params.friend_species, "trusted friend"),
        mystery=Mystery(params.clue, params.answer),
    )


def tell_story(world: World, params: StoryParams) -> None:
    maker = world.maker
    friend = world.friend
    workshop = world.workshop
    mystery = world.mystery
    case = CASES[params.case]
    rng = story_rng(params)

    maker.memes.update(curiosity=1, caution=0, friendship=0)
    friend.memes.update(trust=1, courage=1)

    openings = {
        "clue_first": (
            f"{mystery.clue.capitalize()} startled {maker.name} and {friend.name} in "
            f"{workshop.name}. The young {maker.species} builder knew that {case.danger}."
        ),
        "dialogue_first": (
            f'"Do not touch it yet," {maker.name} said in {workshop.name}. '
            f'{friend.name} looked at the mystery: {mystery.clue}.'
        ),
        "friend_first": (
            f"{friend.name} was helping {maker.name} sort gears in {workshop.name} when "
            f"{mystery.clue}. Their friendship mattered because {case.danger}."
        ),
        "theory_first": (
            f"One guess blamed a broken tool, and another blamed the wind. In "
            f"{workshop.name}, {maker.name} began checking after {mystery.clue}."
        ),
        "quiet_first": (
            f"The tools went quiet in {workshop.name}. Then {maker.name} noticed that "
            f"{mystery.clue}, while {friend.name} watched from the clear floor."
        ),
        "countdown": (
            f"Before the workshop closed, {maker.name} needed to explain why "
            f"{mystery.clue}. {friend.name} stayed close, but {case.danger}."
        ),
        "ending_first": (
            f"By evening, {case.ending}. Earlier that day, the peaceful ending seemed "
            f"unlikely because {mystery.clue}."
        ),
        "question_first": (
            f'"What is making that happen?" asked {friend.name}. {maker.name} pointed to '
            f"the mystery in {workshop.name}: {mystery.clue}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"The danger was not a reason to panic. It was a reason to make a safe plan, because {case.danger}.",
                f"{maker.name} placed a bright line on the floor. If the mystery changed, {case.danger}.",
                f"Friends can be curious together, but they must also watch for danger: {case.danger}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f'"We can solve it without rushing," {maker.name} said. "{friend.name}, please tell me what you notice."',
                f'"I will stay behind the line," {friend.name} promised. {maker.name} answered, "And I will listen to your clues."',
                f'{friend.name} asked, "What if your first guess is wrong?" "Then our friendship will help us try a safer second guess," said {maker.name}.',
            ]
        )
    )

    world.para()
    world.say(f"First, {maker.name} {case.first_test}.")
    world.say(
        rng.choice(
            [
                f"The test did not fit: {case.failed_reason}.",
                f"{maker.name} frowned, because {case.failed_reason}.",
                f'"That answer cannot be right," {maker.name} admitted. {case.failed_reason.capitalize()}.',
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"Then {friend.name} spotted the important clue: {case.mechanism_clue}.",
                f"{friend.name} pointed without stepping closer. {case.mechanism_clue.capitalize()}.",
                f"Because they looked together, they noticed the mechanism clue: {case.mechanism_clue}.",
            ]
        )
    )
    world.say(f"The twist was surprising but ordinary: {case.cause}.")

    world.para()
    world.say(
        rng.choice(
            [
                f"{maker.name} {case.friendship_choice}.",
                f'"I trust you enough to tell you the whole worry," {maker.name} said, and then {case.friendship_choice}.',
                f"The mystery tested their friendship. {maker.name} {case.friendship_choice}.",
            ]
        )
    )
    maker.memes["caution"] = 1
    maker.memes["friendship"] = 1
    maker.meters["safe_tests"] = 2
    world.say(
        rng.choice(
            [
                f"Together, they {case.repair}.",
                f"{friend.name} watched the boundary while {maker.name} worked. At last, they {case.repair}.",
                f'"Now we know the cause," {friend.name} said. They {case.repair}.',
            ]
        )
    )
    mystery.solved = True
    friend.memes["trust"] = 2
    workshop.meters["safe"] = 1

    world.para()
    world.say(
        rng.choice(
            [
                f"The mystery taught them that {case.lesson}.",
                f'{friend.name} smiled. "That was a strange twist." {maker.name} replied, "{case.lesson.capitalize()}."',
                f"They wrote one rule beside the tools: {case.lesson}.',
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"At last, {case.ending}.",
                f"When the floor was clear and the mechanism was still, {case.ending}.",
                f"The repaired workshop showed what had changed: {case.ending.capitalize()}.",
            ]
        )
    )

    world.facts.update(
        maker=maker,
        friend=friend,
        workshop=workshop,
        mystery=mystery,
        case=case,
        cause=case.cause,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
        friendship=maker.memes["friendship"],
        caution=maker.memes["caution"],
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-facing mystery about {world.maker.name} and {world.friend.name} investigating {world.mystery.clue}.",
        f"Show friendship and caution as the characters discover that {case.cause}.",
        f"Include this safe repair: they {case.repair}. End with this image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    maker = world.facts["maker"]
    friend = world.facts["friend"]
    workshop = world.facts["workshop"]
    mystery = world.facts["mystery"]
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What mystery did {maker.name} and {friend.name} investigate in {workshop.name}?",
            answer=f"They investigated why {mystery.clue}. It mattered because {case.danger}.",
        ),
        QAItem(
            question=f"Why did {maker.name}'s first test fail?",
            answer=f"{maker.name} {case.first_test}. The test failed because {case.failed_reason}.",
        ),
        QAItem(
            question="What twist revealed the real cause?",
            answer=f"The important clue was that {case.mechanism_clue}. It showed that {case.cause}.",
        ),
        QAItem(
            question=f"How did {maker.name} show friendship and caution?",
            answer=f"{maker.name} {case.friendship_choice}. This protected both friends while they investigated.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They {case.repair}. They learned that {case.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of connected parts that work together to make something move, open, close, or change.",
        ),
        QAItem(
            question="Why should friends speak up about danger?",
            answer="Speaking up gives friends a chance to stop, make a safe plan, and prevent a small problem from causing harm.",
        ),
        QAItem(
            question="Can a first guess about a mystery be wrong?",
            answer="Yes. A safe test may show that the first guess does not fit, so careful solvers change their idea.",
        ),
        QAItem(
            question="What does friendship look like in this story world?",
            answer="Friendship means listening, telling the truth about worries, respecting safety boundaries, and helping another person learn from evidence.",
        ),
        QAItem(
            question="Why are moving mechanisms handled carefully?",
            answer="Connected moving parts can pinch, pull, or start unexpectedly, so people should keep clear and use a safe method.",
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
        description="A friendship mystery about mechanisms and caution."
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
    parser.add_argument("--workshop", choices=sorted(WORKSHOPS))
    parser.add_argument("--maker-name")
    parser.add_argument("--friend-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    workshop_name = args.workshop or rng.choice(sorted(WORKSHOPS))
    maker_name, maker_species = rng.choice(MAKERS)
    friend_name, friend_species = rng.choice(FRIENDS)
    case_name = rng.choice(CASES_LIST)
    case = CASES[case_name]
    return StoryParams(
        seed=args.seed,
        workshop_name=workshop_name,
        maker_name=args.maker_name or maker_name,
        maker_species=maker_species,
        friend_name=args.friend_name or friend_name,
        friend_species=friend_species,
        clue=case.clue,
        answer=case.cause,
        case=case_name,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.maker, world.friend):
        lines.append(
            f"{entity.name}: species={entity.species} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"{world.workshop.name}: meters={world.workshop.meters}; "
        f"mystery={world.mystery.clue!r}; solved={world.mystery.solved}; "
        f"cause={world.facts['cause']!r}"
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
        print(asp_program("#show solved/1.\n#show friendship/2.\n#show brave/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show solved/1.\n#show friendship/2.\n#show brave/1.")
        )
        print(
            {
                "solved": sorted(asp.atoms(model, "solved")),
                "friendship": sorted(asp.atoms(model, "friendship")),
                "brave": sorted(asp.atoms(model, "brave")),
            }
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    if count < 1:
        raise StoryError("The number of stories must be at least 1.")

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
