#!/usr/bin/env python3
"""
A small mystery story world about a pilgrim, a recycling challenge, and a
suspicious pile of caca that becomes a funny clue about friendship.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Character] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    dialogue_turns: list[tuple[str, str]] = field(default_factory=list)

    def add(self, character: Character) -> Character:
        self.entities[character.id] = character
        return character

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    pilgrim_name: str
    friend_name: str
    guide_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    place: str
    opening: str
    missing_item: str
    clue: str
    red_herring: str
    joke: str
    solve: str
    recycle_action: str
    resolution: str
    ending: str
    lesson: str


PILGRIM_NAMES = ["Luna", "Mira", "Pip", "Nell", "Tavi"]
FRIEND_NAMES = ["Bram", "Jo", "Kito", "Suri", "Moss"]
GUIDE_NAMES = ["Rhea", "Oren", "Ada", "Toma", "Yara"]

MYSTERIES = [
    Mystery(
        place="the dusty bell path",
        opening="At dawn, Luna and her friends reached the dusty bell path on their pilgrimage.",
        missing_item="the silver token that opened the village recycling shed",
        clue="a tiny green thread caught on a hoofprint beside the caca",
        red_herring="a solemn crow staring at the path as if it knew a secret",
        joke="The caca looked innocent, but it had the worst smell of all the suspects.",
        solve="they followed the green thread to a loose strap on the pilgrims' supply cart",
        recycle_action="they sorted the torn strap's plastic buckle into the recycling bin and repaired the cart with its cloth rope",
        resolution="the token had slipped beneath the cart when the loose strap snapped",
        ending="the bell rang, and the repaired cart rolled on without leaving another mystery behind",
        lesson="careful clues and shared work can turn a smelly puzzle into a useful repair",
    ),
    Mystery(
        place="the creekside rest stop",
        opening="By noon, Luna's little pilgrimage paused beside the creekside rest stop.",
        missing_item="the blue badge used to mark the clean recycling station",
        clue="a trail of bottle caps led from the station toward a mound of caca",
        red_herring="a frog wearing a leaf like a very serious hat",
        joke="The frog looked like a guard, but it only croaked, 'Not my job!'",
        solve="they traced the bottle caps to a windblown picnic sack caught in a bush",
        recycle_action="they emptied the sack, rinsed the bottles, and placed each recyclable piece in the correct bin",
        resolution="the blue badge was tucked inside the sack with the bottles",
        ending="the frog blinked as Luna placed the blue badge above the clean, sorted bins",
        lesson="tidying clues can reveal both what is missing and what needs caring for",
    ),
    Mystery(
        place="the hilltop waystone",
        opening="Luna's pilgrimage climbed toward the hilltop waystone under a bright yellow sky.",
        missing_item="the wooden map tube holding the route to the next shelter",
        clue="a strip of paper poked from beneath a pile of caca near the waystone",
        red_herring="a round shadow that looked like a sleeping monster",
        joke="The monster turned out to be a rolled-up blanket, and it snored only when Bram poked it.",
        solve="they matched the paper strip to the torn edge of a map in the recycling basket",
        recycle_action="they removed the spoiled paper, flattened the useful cardboard, and kept the map pieces dry",
        resolution="the wind had carried the map tube into the basket with old paper",
        ending="the friends followed the restored map as the waystone cast a long arrow-shaped shadow",
        lesson="good problem solving means testing a clue instead of guessing from a scary shape",
    ),
    Mystery(
        place="the orchard gate",
        opening="Before sunset, Luna and her friends arrived at the orchard gate on their long pilgrimage.",
        missing_item="the brass key to the orchard's community recycling shed",
        clue="a shiny peel of foil glimmered beside fresh caca under the gate",
        red_herring="a line of ants marching around the gate like tiny detectives",
        joke="The ants inspected the caca, then voted unanimously to investigate somewhere else.",
        solve="they noticed the foil was part of a snack wrapper stuck to a pilgrim's muddy boot",
        recycle_action="they peeled off the wrapper, cleaned the boot, and put the foil in the metal recycling box",
        resolution="the brass key was still tied to the boot's loose lace, hidden under the wrapper",
        ending="the shed door opened, and the ants marched proudly past the shining recycling box",
        lesson="friends can solve a puzzle faster when they laugh, look closely, and help each other",
    ),
    Mystery(
        place="the lantern courtyard",
        opening="That evening, Luna's pilgrimage reached the lantern courtyard beside the old guesthouse.",
        missing_item="the small bell that warned walkers about a slippery step",
        clue="a bent cardboard tube rested beside caca near the lantern stand",
        red_herring="a flickering lantern that seemed to wink at every question",
        joke="The lantern was not winking; a moth was simply bumping into it.",
        solve="they compared the tube with the packing material in the recycling pile",
        recycle_action="they folded the cardboard for recycling and used its clean inside to make a temporary sign",
        resolution="the bell had been packed inside the tube and carried to the recycling pile by mistake",
        ending="the new sign pointed to the safe step while the recovered bell gave one cheerful ding",
        lesson="a mystery becomes smaller when friends organize the evidence and make a safe plan",
    ),
]

DIALOGUES = [
    (
        "We have a mystery, and it smells like caca.",
        "That is the funniest clue we have ever had.",
        "Then let us laugh after we look carefully.",
    ),
    (
        "Nobody touch the suspicious pile until we know what it is.",
        "Agreed. I will watch the path, and you can inspect the recycling.",
        "A good detective keeps both a nose and a notebook open.",
    ),
    (
        "Something important is missing from this pilgrimage.",
        "Could the caca be guarding it?",
        "If it is, it has chosen a very rude hiding place.",
    ),
    (
        "Friends, stay together. The clue may be small.",
        "Small clues are my favorite kind.",
        "Good. We will sort, compare, and follow the evidence.",
    ),
]


ASP_RULES = r"""
#show mystery/1.
#show solution/1.
mystery(caca) :- clue(caca).
solution(recycle) :- missing(token), recyclable(clue), friends(work_together).
solution(recycle) :- missing(badge), recyclable(clue), friends(work_together).
solution(recycle) :- missing(map), recyclable(clue), friends(work_together).
solution(recycle) :- missing(key), recyclable(clue), friends(work_together).
solution(recycle) :- missing(bell), recyclable(clue), friends(work_together).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("clue", "caca"),
            asp.fact("recyclable", "clue"),
            asp.fact("friends", "work_together"),
            asp.fact("missing", "token"),
            asp.fact("missing", "badge"),
            asp.fact("missing", "map"),
            asp.fact("missing", "key"),
            asp.fact("missing", "bell"),
        ]
    )


def asp_program(show: str = "#show mystery/1.\n#show solution/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous recycling pilgrimage mystery.")
    parser.add_argument("--pilgrim-name", choices=PILGRIM_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--guide-name", choices=GUIDE_NAMES)
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
    pilgrim = args.pilgrim_name or rng.choice(PILGRIM_NAMES)
    friend = args.friend_name or rng.choice([name for name in FRIEND_NAMES if name != pilgrim])
    guide = args.guide_name or rng.choice(GUIDE_NAMES)
    if pilgrim == friend:
        raise StoryError("The pilgrim and friend must have different names.")
    return StoryParams(pilgrim_name=pilgrim, friend_name=friend, guide_name=guide)


def _variation(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in f"{params.pilgrim_name}:{params.friend_name}:{params.guide_name}")


def _setup_world(params: StoryParams) -> World:
    world = World()
    pilgrim = world.add(Character("pilgrim", params.pilgrim_name, "pilgrim"))
    friend = world.add(Character("friend", params.friend_name, "friend"))
    guide = world.add(Character("guide", params.guide_name, "guide"))
    pilgrim.memes["curiosity"] = 1.0
    friend.memes["friendship"] = 1.0
    guide.memes["patience"] = 1.0
    world.meters.update(distance=1.0, danger=0.0, evidence=0.0, sorted_recyclables=0.0)
    world.facts.update(pilgrim=pilgrim, friend=friend, guide=guide)
    return world


def _say(world: World, speaker: Character, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'{speaker.name} said, "{line}"')


def generate_story(world: World, params: StoryParams) -> None:
    pilgrim: Character = world.facts["pilgrim"]
    friend: Character = world.facts["friend"]
    guide: Character = world.facts["guide"]

    key = _variation(params)
    mystery = MYSTERIES[key % len(MYSTERIES)]
    first, second, third = DIALOGUES[(key // len(MYSTERIES)) % len(DIALOGUES)]

    world.facts.update(mystery=mystery, dialogue=(first, second, third))
    world.say(mystery.opening)
    world.say(
        f"Pilgrim {pilgrim.name} carried a walking stick, {friend.name} carried a sack for things "
        f"to recycle, and Guide {guide.name} carried the route book."
    )
    world.say(f"Then they discovered that {mystery.missing_item} had vanished. Near it, {mystery.clue}.")
    world.meters["evidence"] = 1.0

    world.para()
    _say(world, pilgrim, first)
    _say(world, friend, second)
    _say(world, guide, third)
    world.say(f"{mystery.red_herring}. {mystery.joke}")
    world.say(f"{friend.name} pointed out that the pile was only a clue, not a culprit.")

    world.para()
    world.say(
        f"The friends made a careful plan: {pilgrim.name} watched the path, {friend.name} sorted "
        f"nearby objects, and Guide {guide.name} compared each clue with the route book."
    )
    world.say(f"Together, they discovered that {mystery.solve}.")
    world.say(f"{mystery.recycle_action}.")
    world.meters["sorted_recyclables"] = 1.0
    world.meters["danger"] = 0.0
    world.memes["friendship"] = 2.0
    _say(world, guide, "You solved it because you listened to one another.")
    _say(world, pilgrim, "And because nobody blamed the caca before checking the facts.")
    world.say(f"At last, {mystery.resolution}.")
    world.say(
        f"{mystery.ending}. They agreed that {mystery.lesson}."
    )
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]
    pilgrim: Character = world.facts["pilgrim"]
    friend: Character = world.facts["friend"]
    guide: Character = world.facts["guide"]
    return [
        QAItem(
            question=f"Who was the pilgrim, and what disappeared during the journey?",
            answer=f"The pilgrim was {pilgrim.name}, and {mystery.missing_item} disappeared.",
        ),
        QAItem(
            question=f"What suspicious clue did {friend.name} notice?",
            answer=f"{friend.name} noticed that {mystery.clue}.",
        ),
        QAItem(
            question=f"How did {pilgrim.name}, {friend.name}, and Guide {guide.name} solve the mystery?",
            answer=(
                f"{pilgrim.name} watched the path, {friend.name} sorted nearby objects, and "
                f"Guide {guide.name} compared the clues with the route book. They learned that "
                f"{mystery.solve}, then they recycled materials safely."
            ),
        ),
        QAItem(
            question="What showed that the mystery had a happy ending?",
            answer=f"{mystery.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does recycle mean?",
            answer="To recycle means to collect and process used materials so they can become useful things again.",
        ),
        QAItem(
            question="Why should people avoid blaming someone before checking clues?",
            answer="People should check clues first because a guess can be unfair and can hide the real solution.",
        ),
        QAItem(
            question="How does friendship help solve a problem?",
            answer="Friendship helps because friends share ideas, notice different details, and encourage one another to keep trying.",
        ),
        QAItem(
            question="Why should a person leave animal caca alone?",
            answer="Animal caca can carry germs, so people should avoid touching it and wash their hands after being outdoors.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]
    pilgrim: Character = world.facts["pilgrim"]
    friend: Character = world.facts["friend"]
    return [
        f"Write a child-friendly mystery about pilgrim {pilgrim.name} and {friend.name} finding "
        f"a missing object near caca at {mystery.place}.",
        f"Include humorous dialogue, careful problem solving, and a recycling action. Use the clue: {mystery.clue}.",
        f"End a friendship mystery with this concrete image: {mystery.ending}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.entities.values():
        lines.append(
            f"  {character.id}: name={character.name} role={character.role} "
            f"meters={character.meters} memes={character.memes}"
        )
    lines.append(f"  world meters={world.meters}")
    lines.append(f"  world memes={world.memes}")
    lines.append(f"  dialogue turns={len(world.dialogue_turns)}")
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("Luna", "Bram", "Rhea"),
    StoryParams("Mira", "Jo", "Oren"),
    StoryParams("Pip", "Kito", "Ada"),
    StoryParams("Nell", "Suri", "Toma"),
    StoryParams("Tavi", "Moss", "Yara"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    mysteries = asp.atoms(model, "mystery")
    solutions = asp.atoms(model, "solution")
    if ("caca",) not in mysteries or ("recycle",) not in solutions:
        print("MISMATCH: ASP did not find the caca clue and recycling solution.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if len(sample.world.dialogue_turns) < 5:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
        if "caca" not in sample.story.lower() or "recycl" not in sample.story.lower():
            print("MISMATCH: generated story lost required domain words.")
            return 1
    print("OK: ASP and Python story checks agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("mystery:", asp.atoms(model, "mystery"))
        print("solution:", asp.atoms(model, "solution"))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            index += 1
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            if index > max(args.n * 100, 100):
                raise StoryError("Could not produce enough distinct story variants.")

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
