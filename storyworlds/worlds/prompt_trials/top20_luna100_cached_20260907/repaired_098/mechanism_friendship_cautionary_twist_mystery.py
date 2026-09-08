#!/usr/bin/env python3
"""A child-facing friendship mystery about a small mechanism and a careful twist."""

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
class Place:
    name: str
    kind: str = "workshop"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MysteryCase:
    clue: str
    worry: str
    first_test: str
    failed_reason: str
    decisive_clue: str
    cause: str
    safe_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class Mechanism:
    name: str
    purpose: str
    working: bool = False
    checked: bool = False


@dataclass
class World:
    workshop: Place
    friend: Creature
    helper: Creature
    mechanism: Mechanism
    case: MysteryCase
    solved: bool = False
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


PLACES = {
    "clockwork shed": Place("the clockwork shed", "shed"),
    "river workshop": Place("the river workshop", "workshop"),
    "hilltop hut": Place("the hilltop hut", "hut"),
    "moonlit garage": Place("the moonlit garage", "garage"),
}

FRIENDS = [
    ("Luna", "rabbit"),
    ("Milo", "fox"),
    ("Nia", "otter"),
    ("Tavi", "sparrow"),
]

HELPERS = [
    ("Pip", "mouse"),
    ("Bea", "beaver"),
    ("Sol", "badger"),
    ("Jun", "turtle"),
]

CASES = {
    "silent_turn": MysteryCase(
        "the little wind-up turner stopped clicking",
        "the garden gate might stay open during the night",
        "counted the teeth on the wheel and turned the handle once",
        "the teeth matched and the handle moved, so a broken wheel was unlikely",
        "a thread of blue yarn caught beneath the spring cover",
        "a friendship bracelet had slipped into the mechanism and was stopping the spring",
        "kept paws and fingers away from the spring while asking a grown-up caretaker to open the cover",
        "removed the yarn with a wooden hook, cleaned the axle, and tested the turner behind a safety screen",
        "a friend may offer help, but careful boundaries protect both the friend and the machine",
        "the gate clicked shut as two friendship bracelets rested safely on a peg",
    ),
    "mysterious_beeps": MysteryCase(
        "the warning bell gave three strange beeps",
        "travelers might miss the safe path beside the pond",
        "replaced the bell's small battery and listened from the marked line",
        "the beeps continued with the fresh battery, so the battery was not the cause",
        "a damp reed touched the bell's outside contact whenever the breeze bent it",
        "a pond reed had grown through a gap and was making the warning circuit flicker",
        "stood on the dry path and asked a friend to point from a safe distance",
        "trimmed the reed with long shears, sealed the gap, and checked the bell in calm and windy air",
        "a cautious friend checks the surroundings before blaming the machine",
        "one clear bell rang while the reed moved harmlessly outside the sealed case",
    ),
    "backward_latch": MysteryCase(
        "the travel box latch kept popping backward",
        "the box could open while carrying supplies to a friend",
        "closed the latch slowly while watching its hook through a paper window",
        "the hook caught correctly, so force alone did not explain the opening",
        "a shiny seed shell lay under the latch plate",
        "a seed shell was tilting the plate just enough to release the hook",
        "stopped carrying the box and marked a safe circle around the latch",
        "swept out the shell, tightened the plate, and tested the box with a light wooden block inside",
        "a small hidden object can create a large warning, so caution belongs in ordinary tasks",
        "the clean latch held the box while friends carried it together",
    ),
    "frozen_pointer": MysteryCase(
        "the direction pointer froze before the trail walk",
        "the friends might follow the wrong path home",
        "compared the pointer with a paper compass and moved it away from the metal shelf",
        "it stayed frozen away from the shelf, so the shelf was not the only problem",
        "a clear drop of tree sap joined the pointer to its guide",
        "sap from a pine cone had glued the moving joint",
        "agreed not to force the pointer and asked the trail keeper for a proper solvent",
        "softened the sap safely, cleaned the guide, and checked the pointer against two landmarks",
        "trust grows when friends admit what they do not know and choose qualified help",
        "the pointer swung freely toward the bright trail marker",
    ),
    "rattling_pedal": MysteryCase(
        "the pedal mechanism rattled whenever a friend pressed it",
        "the little water pump might break during the dry afternoon",
        "pressed it once with a padded stick while the others watched from behind a line",
        "the pedal moved normally without a rider, so the sound needed a closer comparison",
        "the rattle began only when a loose bucket leaned against the frame",
        "the bucket was shaking the frame and making a false machine warning",
        "kept everyone behind the line and moved the bucket only after the pump stopped",
        "stored the bucket on a stable shelf, tightened the frame, and tested the pump gently",
        "a cautionary pause can reveal that a frightening sound comes from nearby, not inside",
        "the pump made a quiet stream while the bucket stood steady on its shelf",
    ),
}

CASE_KEYS = tuple(CASES)
ROUTES = (
    "clue_first",
    "friendship_first",
    "warning_first",
    "two_theories",
    "quiet_first",
    "question_first",
)

ASP_RULES = r"""
safe_friendship(F) :- friend(F), names_risk(F), chooses_safe_action(F).
solved(M) :- mechanism(M), cause(M, _), repaired(M).
valid_story(F,M) :- safe_friendship(F), solved(M).
"""


def mechanism_id(name: str) -> str:
    return "mechanism_" + "".join(
        ch if ch.isalnum() else "_" for ch in name.lower()
    ).strip("_")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("friend", "friend"),
        asp.fact("names_risk", "friend"),
        asp.fact("chooses_safe_action", "friend"),
    ]
    for key, case in CASES.items():
        mid = mechanism_id(key)
        lines.extend(
            (
                asp.fact("mechanism", mid),
                asp.fact("cause", mid, case.cause),
                asp.fact("repaired", mid),
            )
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show solved/1."))
    asp_solved = set(asp.atoms(model, "solved"))
    py_solved = {(mechanism_id(key),) for key in CASES}
    if asp_solved == py_solved:
        print(f"OK: clingo gate matches python reasoning ({len(py_solved)} mechanisms).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(asp_solved))
    print("python:", sorted(py_solved))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place_name,
            params.friend_name,
            params.friend_species,
            params.helper_name,
            params.helper_species,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place_name: str = "clockwork shed"
    friend_name: str = "Luna"
    friend_species: str = "rabbit"
    helper_name: str = "Pip"
    helper_species: str = "mouse"
    mechanism_name: str = "the little wind-up turner"
    case: str = "silent_turn"
    route: str = "clue_first"


def build_world(params: StoryParams) -> World:
    if params.place_name not in PLACES:
        raise StoryError(f"Unknown place: {params.place_name}")
    if params.case not in CASES:
        raise StoryError(f"Unknown mechanism mystery: {params.case}")
    if not params.friend_name.strip():
        raise StoryError("Friend name cannot be empty.")
    if not params.helper_name.strip():
        raise StoryError("Helper name cannot be empty.")

    template = PLACES[params.place_name]
    return World(
        workshop=Place(template.name, template.kind),
        friend=Creature(
            params.friend_name,
            params.friend_species,
            "careful friend",
        ),
        helper=Creature(
            params.helper_name,
            params.helper_species,
            "trusted mechanism keeper",
        ),
        mechanism=Mechanism(
            params.mechanism_name,
            "helping the nearby path or gate stay safe",
        ),
        case=CASES[params.case],
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    friend = world.friend
    helper = world.helper
    place = world.workshop
    machine = world.mechanism
    case = world.case

    friend.memes.update(friendship=1, caution=0, curiosity=1)
    helper.memes.update(trust=1, patience=1)

    openings = {
        "clue_first": (
            f"{case.clue.capitalize()} waited inside {place.name}. "
            f"{friend.name} the {friend.species} noticed it while checking "
            f"{machine.name}, the mechanism that helped keep the path safe."
        ),
        "friendship_first": (
            f"{friend.name} and {helper.name} were close friends who fixed small "
            f"things together in {place.name}. That morning, {machine.name} made "
            f"a sound neither friend expected."
        ),
        "warning_first": (
            f'"Do not touch it yet," {friend.name} said when {machine.name} "
            f"behaved strangely in {place.name}. {case.clue.capitalize()}'
        ),
        "two_theories": (
            f"Two ideas moved through {place.name}: the mechanism was broken, "
            f"or something beside it was pretending to be a problem. "
            f"{friend.name} began with {case.clue}."
        ),
        "quiet_first": (
            f"The workshop became unusually quiet. {machine.name} had stopped, "
            f"and {friend.name} found {case.clue} beside the marked safety line."
        ),
        "question_first": (
            f'"What made {case.clue}?" asked {friend.name}. '
            f"The question mattered because {machine.name} was supposed to help '
            f"keep {place.name} safe."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"The worry was real: {case.worry}.",
                f"Nobody laughed, because {case.worry}.",
                f"{helper.name} kept everyone back from the moving parts; {case.worry}.",
                f"A friendship could not make the danger disappear. {case.worry.capitalize()}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f'"I want to help," {helper.name} said. "{friend.name}, tell me what you know first."',
                f'"Friends do not have to solve everything alone," {helper.name} said. '
                f'{friend.name} nodded. "Then we will check it safely."',
                f'{friend.name} whispered, "I am worried." '
                f'{helper.name} replied, "Thank you for saying so. Worry is useful when it helps us pause."',
            ]
        )
    )

    world.para()
    world.say(f"First, {friend.name} {case.first_test}.")
    world.say(
        rng.choice(
            [
                f"The first idea failed because {case.failed_reason}.",
                f"That test changed their minds: {case.failed_reason}.",
                f'"Our first guess is not enough," {friend.name} said. {case.failed_reason.capitalize()}.',
                f"They recorded the failed test instead of hiding it. {case.failed_reason.capitalize()}.',
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"Then they noticed the decisive clue: {case.decisive_clue}.",
                f"{helper.name} pointed from outside the safe line. {case.decisive_clue.capitalize()}.",
                f"A second look revealed something small but important: {case.decisive_clue}.",
            ]
        )
    )
    world.say(f"The twist was surprising: {case.cause}. The mechanism was not telling the whole story by itself.")

    world.para()
    world.say(
        rng.choice(
            [
                f"{friend.name} wanted to hurry, but instead {friend.name} {case.safe_action}.",
                f'"Friendship means keeping each other safe," {friend.name} said, then {friend.name} {case.safe_action}.',
                f"Care changed the next step. {friend.name} {case.safe_action}.",
            ]
        )
    )
    friend.memes["caution"] = 1
    friend.meters["safe_tests"] = 2
    world.say(
        rng.choice(
            [
                f"With the right help, they {case.repair}.",
                f'{helper.name} handled the tricky part while {friend.name} watched the measurements; together they {case.repair}.',
                f'"Now we can fix the cause, not just the sound," {helper.name} said, and they {case.repair}.',
            ]
        )
    )
    machine.checked = True
    machine.working = True
    world.solved = True
    helper.memes["trust"] = 2
    world.workshop.meters["safety_checked"] = 1

    world.para()
    world.say(
        rng.choice(
            [
                f"{friend.name} learned that {case.lesson}.",
                f'"What will we remember?" {helper.name} asked. '
                f'{friend.name} answered, "{case.lesson.capitalize()}."',
                f"The mystery left a rule for both friends: {case.lesson}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"At sunset, {case.ending}.",
                f"When the final check was complete, {case.ending}.",
                f"The repaired mechanism showed what had changed: {case.ending.capitalize()}.",
            ]
        )
    )
    world.facts.update(
        friend=friend,
        helper=helper,
        place=place,
        mechanism=machine,
        case=case,
        cause=case.cause,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    machine = world.facts["mechanism"]
    case = world.facts["case"]
    return [
        f"Write a child-facing mystery about {friend.name} and {helper.name} investigating {machine.name} in {place.name}.",
        f"Show friendship and caution as the friends discover that {case.cause}.",
        f"End with this changed image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    machine = world.facts["mechanism"]
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What mystery did {friend.name} investigate in {place.name}?",
            answer=f"{friend.name} investigated why {case.clue}. It mattered because {case.worry}.",
        ),
        QAItem(
            question=f"Why did the first test not solve the problem with {machine.name}?",
            answer=f"{friend.name} {case.first_test}. The test did not solve the mystery because {case.failed_reason}.",
        ),
        QAItem(
            question=f"What twist revealed the real cause?",
            answer=f"They discovered that {case.decisive_clue}. The real cause was that {case.cause}.",
        ),
        QAItem(
            question=f"How did {friend.name} show caution?",
            answer=f"{friend.name} {case.safe_action}. This kept the friends away from an unsafe action while they learned more.",
        ),
        QAItem(
            question=f"How did {friend.name} and {helper.name} repair the mechanism?",
            answer=f"Together they {case.repair}. They learned that {case.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, signal, or do a useful job.",
        ),
        QAItem(
            question="Why is caution important around moving parts?",
            answer="Caution helps people pause, keep a safe distance, and ask a qualified helper before touching a machine.",
        ),
        QAItem(
            question="How can friendship help during a mystery?",
            answer="Friends can share observations, listen to worries, and help one another choose safe actions.",
        ),
        QAItem(
            question="Why can a small object cause a large machine problem?",
            answer="A small object can block, tilt, or join two parts that need to move separately, changing how the whole mechanism works.",
        ),
        QAItem(
            question="Why should investigators test more than one explanation?",
            answer="The first guess may be wrong. Comparing safe tests helps reveal the real cause instead of blaming the nearest or loudest part.",
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
    ap = argparse.ArgumentParser(
        description="Friendship mystery about a mechanism, caution, and a twist."
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--friend-name")
    ap.add_argument("--helper-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_name = args.place or rng.choice(sorted(PLACES))
    friend_name, friend_species = rng.choice(FRIENDS)
    helper_name, helper_species = rng.choice(HELPERS)
    case = rng.choice(CASE_KEYS)
    mechanism_names = {
        "silent_turn": "the little wind-up turner",
        "mysterious_beeps": "the warning bell mechanism",
        "backward_latch": "the travel-box latch",
        "frozen_pointer": "the direction pointer",
        "rattling_pedal": "the water-pump pedal",
    }
    return StoryParams(
        seed=args.seed,
        place_name=place_name,
        friend_name=args.friend_name or friend_name,
        friend_species=friend_species,
        helper_name=args.helper_name or helper_name,
        helper_species=helper_species,
        mechanism_name=mechanism_names[case],
        case=case,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.workshop, world.friend, world.helper):
        lines.append(
            f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}"
        )
    lines.append(
        f"mechanism: name={world.mechanism.name!r} purpose={world.mechanism.purpose!r} "
        f"checked={world.mechanism.checked} working={world.mechanism.working}"
    )
    lines.append(
        f"mystery: clue={world.case.clue!r} cause={world.case.cause!r} "
        f"solved={world.solved}"
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
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = 3 if args.all else args.n
    if count < 1:
        raise StoryError("The number of stories must be at least one.")
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
