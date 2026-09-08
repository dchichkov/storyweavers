#!/usr/bin/env python3
"""
A small child-friendly whodunit about a pimple, a shared quest, and solving a
mystery by sharing clues instead of blaming friends.
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
class Person:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective_name: str
    friend_name: str
    caretaker_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    place: str
    quest: str
    pimple_clue: str
    false_suspect: str
    hidden_cause: str
    shared_action: str
    solution: str
    ending: str
    lesson: str


NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Owen", "Zara", "Finn"]
CARETAKERS = ["Aunt Bea", "Coach Mira", "Ms. Robin", "Grandpa Sol"]

CASES = [
    Case(
        place="the Moonbeam Clubhouse",
        quest="find the missing silver star before the evening show",
        pimple_clue="a tiny dab of blue face paint beside the empty star box",
        false_suspect="Milo",
        hidden_cause="the star had slipped into a paper-moon pocket when the backdrop was folded",
        shared_action="shared their clues and unfolded the backdrop one careful panel at a time",
        solution="Luna spotted the star shining inside the moon pocket",
        ending="the rescued star twinkled above the stage while everyone took a bow",
        lesson="sharing clues makes a mystery smaller and kinder",
    ),
    Case(
        place="the Sunflower Reading Room",
        quest="return a golden bookmark before the library bell",
        pimple_clue="a bright yellow thread caught on the reading basket",
        false_suspect="Nia",
        hidden_cause="the bookmark was tucked inside a book about bees that had been moved to the nature shelf",
        shared_action="compared their memories and searched only the shelves connected to the clues",
        solution="the bookmark appeared between two pages in the bee book",
        ending="the library bell rang as the bookmark rested safely in its favorite book",
        lesson="a good detective listens before making a guess",
    ),
    Case(
        place="the Little Lantern Garden",
        quest="find the missing watering badge for the garden helpers",
        pimple_clue="a damp circle beneath a bench and three tiny green leaves",
        false_suspect="Theo",
        hidden_cause="the badge had slid beneath a watering can when a snail crawled across the path",
        shared_action="shared jobs, with one friend checking the path and another lifting the cans gently",
        solution="the badge was found under the can beside the snail's trail",
        ending="the helpers hung the badge on the garden gate beside a row of shining leaves",
        lesson="careful teamwork can follow even the smallest trail",
    ),
    Case(
        place="the Cloud Kite Field",
        quest="solve who moved the red kite before the wind grew strong",
        pimple_clue="a red thread, a muddy footprint, and a kite-shaped shadow near the shed",
        false_suspect="Pia",
        hidden_cause="the kite had been moved indoors by the caretaker to keep its paper tail dry",
        shared_action="shared what each person had seen instead of accusing the person nearest the shed",
        solution="the group found the kite safely hanging in the dry shed",
        ending="the red kite climbed into the blue sky, its tail dancing above the friends",
        lesson="asking a question can reveal a kinder answer than blaming",
    ),
]

OPENINGS = [
    "The afternoon began with a bright plan and one puzzling problem.",
    "At first, everything seemed ready for a cheerful club meeting.",
    "The friends were halfway through their quest when a strange clue appeared.",
    "A small mystery waited where the children had planned to share a big adventure.",
]

DIALOGUE = [
    ("A pimple? That is not a reason to hide or blame anyone.", "I noticed a clue, but I do not know what it means yet.", "Then let us share every clue before we choose a suspect."),
    ("Nobody touches the evidence until we look closely.", "I saw something too, and I was afraid to say it.", "Thank you for sharing. Your clue may change the whole case."),
    ("A mystery needs patient eyes, not quick accusations.", "I wondered if I caused the trouble.", "We will solve the problem together and check the facts."),
    ("Let us protect the quest and protect each other's feelings.", "I can tell what I saw, even if it seems small.", "Small clues can point to a big answer."),
]


class World:
    def __init__(self) -> None:
        self.people: dict[str, Person] = {}
        self.place = Place("unassigned")
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, person: Person) -> Person:
        self.people[person.id] = person
        return person

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ASP_RULES = r"""
#show pimple/1.
#show quest/1.
#show shared_solution/1.
pimple(face) :- clue(small_mark).
quest(active) :- missing(item), goal(recover).
shared_solution(found) :- clue(shared), method(compare), cause(hidden).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("clue", "small_mark"),
            asp.fact("missing", "item"),
            asp.fact("goal", "recover"),
            asp.fact("clue", "shared"),
            asp.fact("method", "compare"),
            asp.fact("cause", "hidden"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pimple quest whodunit about sharing clues.")
    ap.add_argument("--detective-name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--caretaker-name", choices=CARETAKERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective_name or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != detective]
    friend = args.friend_name or rng.choice(friend_choices)
    caretaker = args.caretaker_name or rng.choice(CARETAKERS)
    if detective == friend:
        raise StoryError("detective and friend must have different names")
    return StoryParams(detective, friend, caretaker)


def _setup(params: StoryParams) -> World:
    world = World()
    detective = world.add(Person("detective", params.detective_name, "detective"))
    friend = world.add(Person("friend", params.friend_name, "friend"))
    caretaker = world.add(Person("caretaker", params.caretaker_name, "caretaker"))
    world.facts.update(detective=detective, friend=friend, caretaker=caretaker)
    return world


def _say(world: World, person: Person, line: str) -> None:
    world.dialogue_turns.append((person.name, line))
    world.say(f'{person.name} said, "{line}"')


def _case_index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed % len(CASES)
    return sum(ord(ch) for ch in f"{params.detective_name}:{params.friend_name}:{params.caretaker_name}") % len(CASES)


def generate_story(world: World, params: StoryParams) -> None:
    detective: Person = world.facts["detective"]
    friend: Person = world.facts["friend"]
    caretaker: Person = world.facts["caretaker"]
    index = _case_index(params)
    case = CASES[index]
    opening = OPENINGS[(index + len(params.detective_name)) % len(OPENINGS)]
    first, second, third = DIALOGUE[(index + len(params.friend_name)) % len(DIALOGUE)]

    world.place = Place(case.place)
    world.facts.update(case=case, opening=opening, case_index=index, pimple="a small pimple", solved=False)
    detective.memes["curiosity"] = 1.0
    friend.memes["honesty"] = 1.0
    caretaker.memes["care"] = 1.0
    world.place.meters["mystery"] = 1.0

    world.say(opening)
    world.say(
        f"{detective.name} and {friend.name} had begun a quest at {case.place}: they wanted to {case.quest}. "
        f"Then {detective.name} noticed a small pimple on the end of {detective.name}'s nose. "
        "It felt embarrassing, but it was only a skin bump, not a secret or a sign that anyone had done something wrong."
    )
    world.say(
        f"Just then, the quest's important item was missing. {case.pimple_clue.capitalize()} "
        f"The clue made {friend.name} look worried because it seemed to point toward {friend.name}."
    )

    world.para()
    _say(world, caretaker, first)
    _say(world, detective, second)
    _say(world, friend, third)
    world.say(
        f"{friend.name} took a slow breath and shared one more fact: {case.hidden_cause.split(' when ')[0]} "
        "They had not mentioned it because they feared being blamed."
    )
    world.say(
        f"{detective.name} listened instead of pointing at {friend.name}. "
        f"The pimple, the thread, and the missing item were clues, but none of them proved who had caused the trouble."
    )

    world.para()
    world.say(f"The friends {case.shared_action}.")
    world.say(
        f"{caretaker.name} asked them to test each idea gently. First they checked the place named by the muddy mark. "
        f"Then {detective.name} followed the smallest detail while {friend.name} remembered the last safe moment."
    )
    world.say(f"{case.solution.capitalize()}.")
    _say(world, friend, "I am glad I shared what I knew.")
    _say(world, detective, "I am glad I listened before I guessed.")
    world.say(
        f"The mystery was solved, and {friend.name} was not the culprit. "
        f"They finished the quest together because {case.lesson}."
    )
    world.say(f"At the end, {case.ending}.")
    world.place.meters["mystery"] = 0.0
    world.facts["solved"] = True


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    detective: Person = world.facts["detective"]
    friend: Person = world.facts["friend"]
    caretaker: Person = world.facts["caretaker"]
    return [
        QAItem(
            question=f"What quest were {detective.name} and {friend.name} trying to complete?",
            answer=f"They were trying to {case.quest}.",
        ),
        QAItem(
            question=f"Why did the clue seem to point toward {friend.name}?",
            answer=f"It seemed to point toward {friend.name} because {case.pimple_clue}.",
        ),
        QAItem(
            question="How did sharing help solve the problem?",
            answer=f"The friends shared their observations and {case.shared_action}, which revealed that {case.hidden_cause}.",
        ),
        QAItem(
            question=f"What did {caretaker.name} teach the friends about the pimple and the mystery?",
            answer="The pimple was a small skin bump, and it was not proof that anyone had caused the missing-item problem. Careful clues and kind questions mattered more than blame.",
        ),
        QAItem(
            question="What final image showed that the quest ended well?",
            answer=f"At the end, {case.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pimple?",
            answer="A pimple is a small raised spot on the skin that can happen when a pore becomes blocked or irritated.",
        ),
        QAItem(
            question="Why should people avoid squeezing a pimple?",
            answer="People should avoid squeezing a pimple because touching it can irritate the skin and spread germs.",
        ),
        QAItem(
            question="What does a whodunit ask?",
            answer="A whodunit asks who caused or carried out a puzzling event and uses clues to discover the answer.",
        ),
        QAItem(
            question="Why is sharing information useful when solving a problem?",
            answer="Sharing information lets people compare what they noticed, correct mistaken guesses, and find a safer solution together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    detective: Person = world.facts["detective"]
    friend: Person = world.facts["friend"]
    return [
        f"Write a child-friendly whodunit about {detective.name} and {friend.name} completing a quest to {case.quest}.",
        f"Include a small pimple, the clue that {case.pimple_clue}, and dialogue where the friends share information instead of blaming one another.",
        f"End with a concrete image showing that the mystery was solved: {case.ending}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for person in world.people.values():
        lines.append(
            f"  {person.id}: name={person.name} role={person.role} "
            f"meters={person.meters} memes={person.memes}"
        )
    lines.append(f"  place: {world.place.name} meters={world.place.meters} memes={world.place.memes}")
    lines.append(f"  mystery solved: {world.facts.get('solved')}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _setup(params)
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
    StoryParams("Luna", "Milo", "Aunt Bea"),
    StoryParams("Nia", "Theo", "Coach Mira"),
    StoryParams("Zara", "Finn", "Ms. Robin"),
    StoryParams("Pia", "Owen", "Grandpa Sol"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show pimple/1.\n#show quest/1.\n#show shared_solution/1."))
    found = {
        "pimple": ("face",) in asp.atoms(model, "pimple"),
        "quest": ("active",) in asp.atoms(model, "quest"),
        "shared_solution": ("found",) in asp.atoms(model, "shared_solution"),
    }
    if not all(found.values()):
        print(f"MISMATCH: ASP parity failed: {found}")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("solved"):
            print("MISMATCH: generated story did not solve its mystery.")
            return 1
        if len(sample.world.dialogue_turns) < 6:
            print("MISMATCH: generated story lacks dialogue turns.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pimple/1.\n#show quest/1.\n#show shared_solution/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show pimple/1.\n#show quest/1.\n#show shared_solution/1."))
        print("pimple:", asp.atoms(model, "pimple"))
        print("quest:", asp.atoms(model, "quest"))
        print("shared_solution:", asp.atoms(model, "shared_solution"))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(args.n):
            trial_args = argparse.Namespace(
                detective_name=args.detective_name,
                friend_name=args.friend_name,
                caretaker_name=args.caretaker_name,
            )
            params = resolve_params(trial_args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                params.seed += len(CASES)
                sample = generate(params)
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
