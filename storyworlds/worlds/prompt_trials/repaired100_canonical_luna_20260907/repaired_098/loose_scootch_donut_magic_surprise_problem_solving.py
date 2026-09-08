#!/usr/bin/env python3
"""A gentle ghost story about a loose donut, a tiny scootch, and problem solving."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
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


@dataclass
class Mystery:
    clue: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    ghost_name: str = "Luna"
    friend_name: str = "Milo"
    place_name: str = "the moonlit bakery"
    mystery: str = "a loose donut floating above the cooling table"
    case: str = "loose_donut"
    route: str = "whisper_first"


@dataclass(frozen=True)
class MagicCase:
    first_sign: str
    worry: str
    first_test: str
    failed_reason: str
    clue: str
    cause: str
    safe_action: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    place: Place
    ghost: Creature
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


PLACES = {
    "the moonlit bakery": Place("the moonlit bakery", "bakery"),
    "the old clock shop": Place("the old clock shop", "shop"),
    "the silver garden shed": Place("the silver garden shed", "shed"),
}

GHOSTS = [("Luna", "small ghost"), ("Boo", "friendly ghost"), ("Nell", "lantern ghost")]
FRIENDS = [("Milo", "mouse"), ("Pip", "sparrow"), ("Tess", "cat")]

CASES = {
    "loose_donut": MagicCase(
        "a loose donut rose from the cooling table",
        "the donut might drift into the dark chimney",
        "counted the sprinkles and watched which way the donut moved",
        "the donut spun in place, so the room's ordinary breeze was not enough",
        "a warm golden crumb glowed beneath the table",
        "a forgotten wish had given the donut just enough magic to float toward its missing crumb",
        "made a tiny scootch closer while staying beneath the bright window",
        "used a wooden spoon to guide the crumb back to the donut, then placed the treat inside a covered basket",
        "a surprising problem becomes smaller when friends observe it safely and try one step at a time",
        "the donut rested in its basket while Luna's soft glow made the sprinkles sparkle",
    ),
    "loose_button": MagicCase(
        "a loose silver button rolled by itself",
        "it might slip through a floorboard and wake the sleeping house",
        "blocked the nearby crack with a folded cloth",
        "the button rolled around the cloth instead of stopping",
        "a thread of blue light led from the button to a coat on the peg",
        "a wish in the coat pocket was tugging the button toward the coat's missing stitch",
        "made a careful scootch along the wall and asked for help before touching the glowing thread",
        "knotted the button back onto the coat and tucked the wish into a quiet pocket",
        "magic still needs ordinary care when something comes loose",
        "the silver button shone firmly on the coat as the blue thread faded",
    ),
    "loose_shadow": MagicCase(
        "a loose shadow slipped away from the lantern",
        "it might frighten someone who entered the room",
        "covered the lantern with a glass shade",
        "the shadow remained outside the shade and stretched toward the door",
        "two tiny footprints crossed the shadow's edge",
        "the shadow belonged to a shy night moth carrying a speck of moonlight",
        "took a small scootch backward so the moth would have room to choose its path",
        "opened the window, dimmed the lantern, and let the moth return its moonlight to the garden",
        "solving a strange problem can mean giving a small creature space",
        "the lantern cast one calm shadow while the moth glittered beyond the window",
    ),
}


ROUTES = ("whisper_first", "clue_first", "dialogue_first", "midnight_first", "surprise_first")

ASP_RULES = r"""
ghost(luna).
friend(milo).
magic_problem(loose_donut).
observed(loose_donut).
safe_step(loose_donut).
solved(loose_donut) :- magic_problem(loose_donut), observed(loose_donut), safe_step(loose_donut).
valid_story :- ghost(luna), friend(milo), solved(loose_donut).
"""


def case_id(value: str) -> str:
    return "case_" + "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("ghost", "luna"),
            asp.fact("friend", "milo"),
            asp.fact("magic_problem", "loose_donut"),
            asp.fact("observed", "loose_donut"),
            asp.fact("safe_step", "loose_donut"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    found = set(asp.atoms(model, "solved"))
    expected = {("loose_donut",)}
    if found == expected:
        print("OK: clingo gate matches python reasoning (1 magical problem).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.ghost_name,
            params.friend_name,
            params.place_name,
            params.mystery,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.place_name not in PLACES:
        raise StoryError(f"Unknown place: {params.place_name}")
    if params.case not in CASES:
        raise StoryError(f"Unknown magic case: {params.case}")
    place = PLACES[params.place_name]
    return World(
        place=Place(place.name, place.kind),
        ghost=Creature(params.ghost_name, "friendly ghost", "problem solver"),
        friend=Creature(params.friend_name, "small friend", "helper"),
        mystery=Mystery(params.mystery),
    )


def tell_story(world: World, params: StoryParams) -> None:
    ghost, friend, place, mystery = world.ghost, world.friend, world.place, world.mystery
    case = CASES[params.case]
    rng = story_rng(params)

    ghost.memes.update(curiosity=1.0, courage=0.0)
    friend.memes.update(patience=1.0, trust=1.0)

    openings = {
        "whisper_first": f"At midnight, a whisper curled through {place.name}. {ghost.name}, a friendly ghost, heard that {case.first_sign}.",
        "clue_first": f"A golden crumb glimmered on the floor of {place.name}. It pointed toward a surprise: {case.first_sign}.",
        "dialogue_first": f'"Did you see that?" {ghost.name} asked in {place.name}. {friend.name} nodded, because {case.first_sign}.',
        "midnight_first": f"The moon was high above {place.name} when {ghost.name} noticed something unusual. {case.first_sign.capitalize()}.",
        "surprise_first": f"Nobody expected magic after bedtime, but {case.first_sign} in {place.name}. {ghost.name} floated closer with {friend.name}.",
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"It was a problem because {case.worry}.",
        f"The surprise seemed harmless, but {case.worry}.",
        f"{friend.name} felt a shiver. If they ignored it, {case.worry}.",
    ]))
    world.say(rng.choice([
        f'"Let us not chase it," {friend.name} said. "Let us watch first."',
        f'"Magic can be surprising," {ghost.name} whispered. "{case.lesson.capitalize()}."',
        f'"I am scared," said {ghost.name}. {friend.name} answered, "Then we will solve it together."',
    ]))

    world.para()
    world.say(f"First, {ghost.name} {case.first_test}.")
    world.say(rng.choice([
        f"The test did not work because {case.failed_reason}.",
        f"That was a useful failure: {case.failed_reason}.",
        f'"Our first idea was wrong," {ghost.name} admitted, because {case.failed_reason}.',
    ]))
    world.say(rng.choice([
        f"Then they noticed something important: {case.clue}.",
        f"{friend.name} pointed beneath the nearest table. {case.clue.capitalize()}.",
        f"The darkness gave them a clue. {case.clue.capitalize()}.",
    ]))
    world.say(f"Now the mystery made sense. {case.cause}.")

    world.para()
    world.say(rng.choice([
        f"{ghost.name} gathered courage and {case.safe_action}.",
        f'"One tiny step," said {ghost.name}, then {case.safe_action}.',
        f"Instead of rushing, {ghost.name} {case.safe_action}.",
    ]))
    ghost.memes["courage"] = 1.0
    ghost.meters["safe_steps"] = 1.0
    world.say(rng.choice([
        f"Together, they {case.repair}.",
        f"{friend.name} steadied the light while {ghost.name} {case.repair}.",
        f'"We know what caused it now," {friend.name} said, and they {case.repair}.',
    ]))
    mystery.solved = True
    place.meters["safety"] = 1.0
    friend.memes["trust"] = 2.0

    world.para()
    world.say(rng.choice([
        f"They remembered the rule: {case.lesson}.",
        f'"Problem solving is not rushing," {ghost.name} said. "It is learning from each clue."',
        f"The magic left behind a quiet lesson: {case.lesson}.',
    ]))
    world.say(rng.choice([
        f"At last, {case.ending}.",
        f"By the time the moon moved west, {case.ending}.",
        f"The change was easy to see: {case.ending.capitalize()}.",
    ]))

    world.facts.update(
        ghost=ghost,
        friend=friend,
        place=place,
        mystery=mystery,
        case=case,
        cause=case.cause,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    ghost = world.facts["ghost"]
    place = world.facts["place"]
    return [
        f"Write a gentle ghost story about {ghost.name} solving a magical problem at {place.name}.",
        f"Include the words loose, scootch, and donut, with a surprise caused by {case.cause}.",
        f"Show problem solving through this safe action: {case.safe_action}. End with {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    ghost = facts["ghost"]
    friend = facts["friend"]
    place = facts["place"]
    return [
        QAItem(
            question=f"What surprising problem did {ghost.name} find at {place.name}?",
            answer=f"{ghost.name} found that {case.first_sign}. It mattered because {case.worry}.",
        ),
        QAItem(
            question=f"Why did {ghost.name}'s first test fail?",
            answer=f"{ghost.name} {case.first_test}, but that did not work because {case.failed_reason}.",
        ),
        QAItem(
            question=f"What clue revealed the real cause of the magic?",
            answer=f"They noticed that {case.clue}. This showed that {case.cause}.",
        ),
        QAItem(
            question=f"How did {ghost.name} solve the problem safely with {friend.name}?",
            answer=f"{ghost.name} {case.safe_action}. Then they {case.repair}.",
        ),
        QAItem(
            question="What lesson did the ghost learn?",
            answer=f"The ghost learned that {case.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in this story world?",
            answer="A ghost is a gentle, unseen or glowing character who can notice unusual things and help solve problems.",
        ),
        QAItem(
            question="What does magic mean here?",
            answer="Magic is a surprising force that makes an ordinary object behave in an unusual way, while careful actions can still help.",
        ),
        QAItem(
            question="Why is scooting safer than rushing?",
            answer="A small scootch lets someone observe each step, keep a safe distance, and change plans when new evidence appears.",
        ),
        QAItem(
            question="How does problem solving work?",
            answer="Problem solving means noticing the problem, testing an idea safely, learning from what happens, and trying a better step.",
        ),
        QAItem(
            question="Why can a surprise be useful?",
            answer="A surprise can invite careful questions and reveal a clue, even when it first feels mysterious.",
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
        description="A gentle ghost story about loose magic, a scootch, and a donut."
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
    parser.add_argument("--ghost-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--case", choices=sorted(CASES))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ghost_name, _ = rng.choice(GHOSTS)
    friend_name, _ = rng.choice(FRIENDS)
    place_name = args.place or rng.choice(sorted(PLACES))
    case_name = args.case or rng.choice(sorted(CASES))
    return StoryParams(
        seed=args.seed,
        ghost_name=args.ghost_name or ghost_name,
        friend_name=args.friend_name or friend_name,
        place_name=place_name,
        mystery=CASES[case_name].first_sign,
        case=case_name,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.ghost, world.friend):
        lines.append(f"{entity.name}: meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"{world.place.name}: meters={world.place.meters} "
        f"mystery={world.mystery.clue!r} solved={world.mystery.solved}"
    )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
