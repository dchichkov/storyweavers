#!/usr/bin/env python3
"""
A small ghost storyworld about a fraction, teamwork, repetition, and a mystery.

Luna hears the same three knocks in the old schoolhouse. With her friends, she
uses a fraction of the lantern's light and repeats the clues until the ghost's
mystery is solved kindly.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    caretaker: str
    object_name: str
    fraction: str
    mystery: int = 0
    repetition: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


NAMES = ["Luna", "Milo", "Nia", "Theo", "Zara", "Ivy", "Owen", "Mara"]
FRIENDS = ["Pip", "Bea", "Sol", "Ravi", "Tess", "Finn", "June", "Kai"]
CARETAKERS = ["Mrs. Bell", "Mr. Reed", "Aunt May", "Grandpa Moss"]
OBJECTS = ["blue lantern", "brass key", "music box", "silver bell"]
FRACTIONS = ["one half", "one third", "two thirds", "three fourths"]

MYSTERIES = [
    {
        "opening": "At the old schoolhouse, the blue lantern blinked even though nobody had lit it.",
        "cause": "three soft knocks came from behind the locked reading-room door",
        "clue": "a dusty trail of tiny footprints curved toward the cupboard",
        "action": "Luna held the lantern while the friends counted the footprints together",
        "reveal": "a shy little ghost named Wisp was hiding beside a box of lost music cards",
        "reason": "Wisp had been trying to find the card for a lullaby that once comforted lonely children",
    },
    {
        "opening": "The moon shone through the schoolhouse windows, but one pale shadow moved against the wall.",
        "cause": "the same short tune played from the silent music box",
        "clue": "a chalk star appeared each time the tune stopped",
        "action": "the friends repeated the tune and marked each chalk star on the floor",
        "reveal": "a friendly ghost was pointing toward a loose floorboard",
        "reason": "the ghost wanted help finding a keepsake hidden beneath the boards",
    },
    {
        "opening": "Luna heard a whisper in the empty classroom just as the clock struck nine.",
        "cause": "the whisper repeated the words, 'Not yet, not yet,' from the coat closet",
        "clue": "inside the closet, one mitten trembled whenever the words were spoken",
        "action": "the team repeated the whisper softly and watched the mitten's movement",
        "reveal": "a small ghost was waving from behind the coats",
        "reason": "the ghost had lost a family photograph and could not leave without it",
    },
    {
        "opening": "Rain tapped the schoolhouse roof while a pale glow bobbed down the hallway.",
        "cause": "the glow stopped at the same cracked tile again and again",
        "clue": "each stop made a little ring of dust rise from the tile",
        "action": "the friends took turns shining the lantern and repeating the stopping place",
        "reveal": "a gentle ghost was waiting beside a buried tin whistle",
        "reason": "the whistle had belonged to the ghost's brother, and its song was unfinished",
    },
    {
        "opening": "The old schoolhouse was quiet until a tiny bell rang from the attic.",
        "cause": "the bell rang four times, paused, and rang four times again",
        "clue": "four silver specks glittered below the attic stairs",
        "action": "the team repeated the bell pattern and followed the specks carefully",
        "reveal": "a smiling ghost sat beside a dusty trunk",
        "reason": "the trunk held drawings the ghost wanted children to see",
    },
]

REPETITIONS = [
    "They said together, 'Knock, listen, look,' then said it again, slower and clearer.",
    "First Luna counted the sound. Then the friends repeated the count: one, two, three; one, two, three.",
    "They whispered the clue once, twice, and a third time, until every teammate noticed the same detail.",
    "The team took turns saying, 'We check, we share, we solve.' The words grew steadier each time.",
    "They copied the sound in a careful rhythm, pausing after every repeat so nobody missed the answer.",
    "Again and again, they followed the same path, because repetition made the confusing clue plain.",
]

ENDINGS = [
    "The ghost smiled and the lantern became warm and steady. At dawn, the children placed the found treasure in the schoolhouse display.",
    "When the mystery was solved, the pale shadow turned bright as moonlight. The friends left a note promising to return for another careful search.",
    "The ghost played one gentle note, and the old schoolhouse no longer felt lonely. Luna divided the lantern light among the team, and everyone walked home together.",
    "By morning, the repeated knocks had become a cheerful little rhythm. The friends wrote the solution on the board so the next visitor would know what had happened.",
    "The ghost floated through the wall with a grateful wave. Behind it, the hidden object gleamed, proving that patient teamwork can brighten a dark place.",
    "The last mystery clue became a tiny star in the air. Luna and her friends laughed softly, then closed the door with the ghost's happy song behind them.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

name(N) :- name_option(N).
friend(F) :- friend_option(F).
caretaker(C) :- caretaker_option(C).
object(O) :- object_option(O).
fraction(F) :- fraction_option(F).
mystery(M) :- mystery_option(M).
repeat_style(R) :- repeat_option(R).

valid(N, F, O) :- name_option(N), friend_option(F), object_option(O).
valid_story(N, F, O, Q) :- valid(N, F, O), fraction_option(Q).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in NAMES:
        lines.append(asp.fact("name_option", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend_option", value))
    for value in CARETAKERS:
        lines.append(asp.fact("caretaker_option", value))
    for value in OBJECTS:
        lines.append(asp.fact("object_option", value))
    for value in FRACTIONS:
        lines.append(asp.fact("fraction_option", value))
    for index in range(len(MYSTERIES)):
        lines.append(asp.fact("mystery_option", index))
    for index in range(len(REPETITIONS)):
        lines.append(asp.fact("repeat_option", index))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(name, friend, obj) for name in NAMES for friend in FRIENDS for obj in OBJECTS]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_values = set(valid_combos())
    clingo_values = set(asp_valid_combos())
    if python_values == clingo_values:
        print(f"OK: clingo gate matches valid_combos() ({len(python_values)} combinations).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    print("Only in Python:", sorted(python_values - clingo_values))
    print("Only in clingo:", sorted(clingo_values - python_values))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about fractions, repetition, and teamwork."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--caretaker", choices=CARETAKERS)
    parser.add_argument("--object-name", dest="object_name", choices=OBJECTS)
    parser.add_argument("--fraction", choices=FRACTIONS)
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
    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")

    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        caretaker=args.caretaker or rng.choice(CARETAKERS),
        object_name=args.object_name or rng.choice(OBJECTS),
        fraction=args.fraction or rng.choice(FRACTIONS),
        mystery=rng.randrange(len(MYSTERIES)),
        repetition=rng.randrange(len(REPETITIONS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.mystery = seed % len(MYSTERIES)
    params.repetition = (seed // len(MYSTERIES)) % len(REPETITIONS)
    params.ending = (seed // 3) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    if params.fraction not in FRACTIONS:
        raise StoryError("The fraction must be one of the registered simple fractions.")
    if params.mystery < 0 or params.mystery >= len(MYSTERIES):
        raise StoryError("That mystery is not part of the schoolhouse story.")
    if params.repetition < 0 or params.repetition >= len(REPETITIONS):
        raise StoryError("That repetition pattern is not available.")
    if params.ending < 0 or params.ending >= len(ENDINGS):
        raise StoryError("That ending is not available.")

    mystery = MYSTERIES[params.mystery]
    w = World()

    child = w.add(
        Entity(
            id="child",
            kind="character",
            label=params.name,
            memes={"curiosity": 1.0, "courage": 0.0, "relief": 0.0},
        )
    )
    friend = w.add(
        Entity(
            id="friend",
            kind="character",
            label=params.friend,
            memes={"curiosity": 1.0, "teamwork": 0.0},
        )
    )
    caretaker = w.add(
        Entity(
            id="caretaker",
            kind="character",
            label=params.caretaker,
            memes={"trust": 1.0},
        )
    )
    lantern = w.add(
        Entity(
            id="lantern",
            label="lantern",
            meters={"light": 1.0, "shared_fraction": 0.0},
            memes={"warmth": 0.0},
        )
    )
    ghost = w.add(
        Entity(
            id="ghost",
            kind="spirit",
            label="ghost",
            meters={"visibility": 0.0},
            memes={"loneliness": 1.0, "hope": 0.0},
        )
    )
    object_entity = w.add(
        Entity(
            id="mystery_object",
            label=params.object_name,
            meters={"hidden": 1.0},
            memes={"meaning": 0.0},
        )
    )

    w.say(
        f"{params.name} and {params.friend} visited the old schoolhouse with {params.caretaker} "
        f"on a moonlit evening."
    )
    w.say(mystery["opening"])
    w.say(
        f"{params.caretaker} gave them one lantern and said, "
        f"'Stay together, listen carefully, and leave nothing unsafe behind.'"
    )

    w.para()
    lantern.meters["shared_fraction"] = 0.5
    lantern.memes["warmth"] = 0.5
    ghost.meters["visibility"] = 0.5
    child.memes["courage"] = 0.5
    friend.memes["teamwork"] = 0.5
    w.say(
        f"Then {mystery['cause']}. The sound made the hallway feel larger and darker."
    )
    w.say(
        f"{params.name} lifted the lantern, but used only {params.fraction} of its light "
        f"at a time so the team could save the rest for the next clue."
    )
    w.say(f"{mystery['clue']}.")
    w.say(REPETITIONS[params.repetition])
    w.say(f"'{mystery['action'].capitalize()}. What do you notice?' asked {params.name}.")
    w.say(
        f"'{mystery['clue'].capitalize()},' answered {params.friend}. "
        f"'The same clue keeps returning.'"
    )
    w.say(
        f"'Then we follow it together,' said {params.name}. "
        f"'Together,' repeated {params.friend}."
    )

    w.para()
    child.memes["courage"] = 1.0
    friend.memes["teamwork"] = 1.0
    lantern.meters["shared_fraction"] = 1.0
    lantern.memes["warmth"] = 1.0
    ghost.meters["visibility"] = 1.0
    ghost.memes["loneliness"] = 0.0
    ghost.memes["hope"] = 1.0
    object_entity.meters["hidden"] = 0.0
    object_entity.memes["meaning"] = 1.0
    w.say(f"Behind the final clue, {mystery['reveal']}.")
    w.say(
        f"The ghost explained that {mystery['reason']}. "
        f"{params.name} held out the lantern, and {params.friend} carefully found the "
        f"{params.object_name}."
    )
    w.say(
        f"'We found it because we repeated the clue and shared the work,' said {params.name}."
    )
    w.say(
        f"'And because even a fraction of light can help when friends carry it together,' "
        f"added {params.friend}."
    )
    w.say(ENDINGS[params.ending])

    w.facts.update(
        child=params.name,
        friend=params.friend,
        caretaker=params.caretaker,
        object_name=params.object_name,
        fraction=params.fraction,
        mystery_cause=mystery["cause"],
        clue=mystery["clue"],
        helpful_action=mystery["action"],
        reveal=mystery["reveal"],
        resolved=True,
        teamwork=True,
        repetition=True,
    )

    prompts = [
        "Write a child-friendly ghost story in which a fraction of lantern light, repetition, and teamwork solve a mystery.",
        f"Tell a gentle ghost story about {params.name} and {params.friend} solving a repeated clue in an old schoolhouse.",
        f"Write a mystery story where {params.fraction} of a lantern's light helps a team find a lost {params.object_name}.",
    ]

    story_qa = [
        QAItem(
            question="Who entered the old schoolhouse?",
            answer=f"{params.name} and {params.friend} entered the old schoolhouse with {params.caretaker}.",
        ),
        QAItem(
            question="What repeated event made the mystery suspenseful?",
            answer=f"The mystery began when {mystery['cause']}. The repeated event made the quiet schoolhouse feel mysterious.",
        ),
        QAItem(
            question="How did the fraction help the team?",
            answer=f"{params.name} used {params.fraction} of the lantern's light at a time, saving enough light to examine the next clue.",
        ),
        QAItem(
            question="How did the friends solve the mystery?",
            answer=f"They repeated the clue, noticed {mystery['clue']}, and worked together until {mystery['reveal']}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The ghost was no longer lonely, the {params.object_name} was found, and the schoolhouse felt warm instead of frightening.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a fraction?",
            answer="A fraction names a part of a whole, such as one half of a lantern's light.",
        ),
        QAItem(
            question="Why can repetition help solve a mystery?",
            answer="Repetition helps people notice a pattern because the same sound or clue appears more than once.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share jobs, listen to one another, and work toward the same goal.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or strange event, often with a mystery for the characters to solve.",
        ),
        QAItem(
            question="Why should explorers stay together in a dark place?",
            answer="Explorers should stay together so they can share light, help one another, and make safer decisions.",
        ),
    ]

    return StorySample(
        params=params,
        story=w.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=w,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:16} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            name="Luna",
            friend="Pip",
            caretaker="Mrs. Bell",
            object_name="blue lantern",
            fraction="one half",
            mystery=0,
            repetition=0,
            ending=0,
        ),
        StoryParams(
            name="Milo",
            friend="Bea",
            caretaker="Mr. Reed",
            object_name="music box",
            fraction="one third",
            mystery=1,
            repetition=2,
            ending=2,
        ),
        StoryParams(
            name="Nia",
            friend="Sol",
            caretaker="Aunt May",
            object_name="silver bell",
            fraction="two thirds",
            mystery=3,
            repetition=4,
            ending=4,
        ),
        StoryParams(
            name="Theo",
            friend="Ravi",
            caretaker="Grandpa Moss",
            object_name="brass key",
            fraction="three fourths",
            mystery=4,
            repetition=5,
            ending=5,
        ),
    ]


CURATED = build_curated()


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
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or len(sample.story.split()) < 100:
                print("FAIL: generated story is too short.")
                sys.exit(1)
        print(f"OK: generated {len(CURATED)} curated stories.")
        return

    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid (name, friend, object) combinations:\n")
        for name, friend, object_name in triples[:40]:
            print(f"  {name:8} + {friend:8} -> {object_name}")
        if len(triples) > 40:
            print(f"  ... and {len(triples) - 40} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"### {params.name}: the {params.fraction} lantern mystery "
                f"with {params.friend}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
