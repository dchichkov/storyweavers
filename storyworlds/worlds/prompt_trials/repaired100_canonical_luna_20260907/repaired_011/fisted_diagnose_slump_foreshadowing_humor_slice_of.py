#!/usr/bin/env python3
"""
A small slice-of-life storyworld about diagnosing a mysterious slump.

The story uses foreshadowing and gentle humor: a child notices a fisted
hand, helps diagnose why a friend has slumped, and discovers that a small,
ordinary kindness can change an afternoon.
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
    child: str
    friend: str
    helper: str
    place: str
    object: str
    snack: str
    symptom: int = 0
    clue: int = 0
    remedy: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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


CHILDREN = ["Luna", "Milo", "Nia", "Theo", "Poppy", "Sam"]
FRIENDS = ["Ari", "Bea", "Cal", "Drew", "Ivy", "Jo"]
HELPERS = ["Grandma June", "Mr. Patel", "Aunt Rosa", "Coach Kim"]
PLACES = ["the apartment hallway", "the library corner", "the community garden", "the laundromat bench"]
OBJECTS = ["a blue mitten", "a paper kite", "a yellow lunchbox", "a tiny red notebook"]
SNACKS = ["apple slices", "warm toast", "cheese crackers", "banana muffins"]

SYMPTOMS = [
    {
        "opening": "{friend} sat on the low step with a fist closed tight around {object}.",
        "foreshadow": "Earlier, {child} had noticed one quiet clue: {friend} kept glancing at the same crooked poster and never touched the snack bag.",
        "cause": "the strap on the object had snapped, and {friend} thought the object was ruined",
        "action": "{child} asked questions instead of guessing, then {helper} helped them inspect the broken strap",
        "result": "they tied the strap with a bright piece of string, so the object could be carried again",
        "dialogue": (
            '"Is your hand tired?" {child} asked. '
            '"No," said {friend}. "My day is the tired part."'
        ),
    },
    {
        "opening": "{friend} had slumped beside the window, making a small mountain out of one sleeve.",
        "foreshadow": "At breakfast, {child} had heard a faint rattle from {friend}'s bag, but nobody had stopped to ask about it.",
        "cause": "a loose button had fallen from the object, and {friend} was worried that everyone would laugh",
        "action": "{child} found the button under the bench while {helper} showed them how to sew it back",
        "result": "the button returned to its place, looking slightly proud and very round",
        "dialogue": (
            '"Why are you folded up like a napkin?" {child} asked. '
            '"Because my button ran away," said {friend}.'
        ),
    },
    {
        "opening": "{friend} stared at the floor with both shoulders in a deep slump.",
        "foreshadow": "{child} remembered that {friend} had packed the object carefully that morning, even though one corner already looked bent.",
        "cause": "the object had bent when it was bumped, and {friend} believed the special drawing inside was lost",
        "action": "{child} and {helper} gently flattened the cover and opened it one page at a time",
        "result": "the drawing was safe, and the bent corner became a funny-looking flap",
        "dialogue": (
            '"Can we diagnose this?" {child} asked. '
            '"Only if the doctor is allowed to use tape," said {friend}.'
        ),
    },
    {
        "opening": "{friend} sat so still that a passing breeze nearly counted as a conversation.",
        "foreshadow": "The first clue had been a tiny sigh when {friend} set the object down beside the snack.",
        "cause": "the object was stuck shut, and {friend} feared that an important note was trapped inside",
        "action": "{child} brought {helper}, who loosened the lid with a spoon handle and a very patient wiggle",
        "result": "the lid opened, and the note slid out without a single rip",
        "dialogue": (
            '"What happened?" {child} whispered. '
            '"My object is being stubborn," said {friend}. "It gets that from me."'
        ),
    },
    {
        "opening": "{friend} held one fist over the other and slumped like a sleepy question mark.",
        "foreshadow": "Before anyone spoke, {child} noticed that the object had a fresh smudge across its middle.",
        "cause": "the object had spilled ink on itself, and {friend} thought the whole afternoon was spoiled",
        "action": "{child} used a damp cloth while {helper} placed a clean sheet beneath the smudged part",
        "result": "most of the ink lifted away, leaving a silly blue moon instead of a mess",
        "dialogue": (
            '"That looks serious," {child} said. '
            '"Very serious," said {friend}. "It may be a moon emergency."'
        ),
    },
]

REMEDIES = [
    "They made a little repair station on the bench, with string, tape, and one snack for every careful attempt.",
    "{helper} declared that every good diagnosis needed a second opinion, so everyone inspected the fix and then inspected the muffins.",
    "The repair took three tries, two giggles, and one dramatic sigh from the object, which was probably just the hinge.",
    "{child} held the pieces steady while {friend} chose the color of the repair. The best fix, they decided, was one that looked cheerful.",
    "Nobody rushed. They tested the object gently, celebrated each small improvement, and kept the snack bag safely away from the glue.",
]

ENDINGS = [
    "By the time they left, {friend} was carrying the repaired object instead of hiding it. The fist had opened around a warm piece of toast.",
    "The slump disappeared slowly, like a shadow moving off the floor. {child} and {friend} walked home while the repaired object bumped a cheerful rhythm against a knee.",
    "{helper} gave the object a tiny paper badge that said, 'Still Working.' {friend} laughed so hard that the badge nearly flew away.",
    "The crooked poster was still crooked, the bench was still hard, and the afternoon was still ordinary. Somehow, it felt much better.",
    "At snack time, {friend} placed the object in the middle of the table. Its odd repair showed exactly where the worry had been and exactly where the friends had helped.",
]

ASP_RULES = r"""
#show valid/4.
#show valid_story/6.

child(N) :- child_name(N).
friend(F) :- friend_name(F).
helper(H) :- helper_name(H).
place(P) :- place_name(P).
object(O) :- object_name(O).
snack(S) :- snack_name(S).

compatible(O, S) :- object_name(O), snack_name(S).

valid(N, F, O, S) :-
    child_name(N),
    friend_name(F),
    object_name(O),
    snack_name(S),
    N != F.

valid_story(N, F, H, P, O, S) :-
    valid(N, F, O, S),
    helper_name(H),
    place_name(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in CHILDREN:
        lines.append(asp.fact("child_name", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend_name", value))
    for value in HELPERS:
        lines.append(asp.fact("helper_name", value))
    for value in PLACES:
        lines.append(asp.fact("place_name", value))
    for value in OBJECTS:
        lines.append(asp.fact("object_name", value))
    for value in SNACKS:
        lines.append(asp.fact("snack_name", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (child, friend, obj, snack)
        for child in CHILDREN
        for friend in FRIENDS
        for obj in OBJECTS
        for snack in SNACKS
        if child != friend
    ]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life storyworld about diagnosing a mysterious slump."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--snack", choices=SNACKS)
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
    child = args.child or rng.choice(CHILDREN)
    friend_choices = [name for name in FRIENDS if name != child]
    friend = args.friend or rng.choice(friend_choices)

    if args.friend and args.friend == child:
        raise StoryError("The child and friend must have different names so their conversation is clear.")

    return StoryParams(
        child=child,
        friend=friend,
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        object=args.object_name or rng.choice(OBJECTS),
        snack=args.snack or rng.choice(SNACKS),
        symptom=rng.randrange(len(SYMPTOMS)),
        clue=rng.randrange(len(SYMPTOMS)),
        remedy=rng.randrange(len(REMEDIES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.symptom = seed % len(SYMPTOMS)
    params.clue = (seed // 2) % len(SYMPTOMS)
    params.remedy = (seed // 3) % len(REMEDIES)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    if params.child == params.friend:
        raise StoryError("A story needs two distinct characters for a useful back-and-forth exchange.")

    symptom = SYMPTOMS[params.symptom % len(SYMPTOMS)]
    values = {
        "child": params.child,
        "friend": params.friend,
        "helper": params.helper,
        "place": params.place,
        "object": params.object,
        "snack": params.snack,
    }

    world = World()
    child = world.add(Entity(
        id=params.child,
        kind="character",
        label=params.child,
        memes={"curiosity": 0.0, "care": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        label=params.friend,
        memes={"energy": 0.0, "worry": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        label=params.helper,
        memes={"patience": 1.0},
    ))
    obj = world.add(Entity(
        id="object",
        label=params.object,
        meters={"condition": 0.45},
        memes={"importance": 1.0},
    ))
    snack = world.add(Entity(
        id="snack",
        label=params.snack,
        meters={"warmth": 1.0},
        memes={"comfort": 1.0},
    ))

    world.say(
        f"On an ordinary afternoon at {params.place}, {params.child} found {params.friend} "
        f"sitting beside {params.object}."
    )
    world.say(symptom["opening"].format(**values))
    world.say(symptom["foreshadow"].format(**values))
    world.say(
        f"The {params.place.split('the ')[-1]} smelled faintly of {params.snack}, "
        f"and nobody seemed in a hurry."
    )

    world.para()
    friend.memes["worry"] = 1.0
    friend.memes["energy"] = 0.2
    child.memes["curiosity"] = 1.0
    obj.meters["condition"] = 0.2
    world.say(symptom["dialogue"].format(**values))
    world.say(
        f"{params.child} did not diagnose the problem from across the room. "
        f"Instead, {params.child} listened while {params.friend} explained that {symptom['cause']}."
    )
    world.say(
        f"{params.child} nodded. 'Let us check one small thing at a time,' {params.child} said."
    )
    world.say(symptom["action"].format(**values))

    world.para()
    child.memes["care"] = 1.0
    friend.memes["worry"] = 0.3
    friend.memes["energy"] = 0.8
    obj.meters["condition"] = 1.0
    world.say(REMEDIES[params.remedy % len(REMEDIES)].format(**values))
    world.say(symptom["result"].format(**values))
    world.say(
        f"{params.friend} looked at {params.child}. 'So the diagnosis was not that I was bad at fixing things?' "
        f"{params.child} shook {params.child}'s head. 'It was that you needed a teammate.'"
    )
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.child,
        friend=params.friend,
        helper=params.helper,
        place=params.place,
        object=params.object,
        snack=params.snack,
        symptom=params.symptom % len(SYMPTOMS),
        cause=symptom["cause"],
        action=symptom["action"],
        result=symptom["result"],
        diagnosed=True,
        resolved=True,
    )

    prompts = [
        "Write a gentle slice-of-life story in which a child diagnoses why a friend has slumped.",
        f"Tell a funny, child-friendly story about {params.child} noticing {params.friend}'s fisted hand and helping with {params.object}.",
        f"Write a foreshadowing story where a small clue explains {params.friend}'s slump and teamwork repairs the problem.",
    ]

    story_qa = [
        QAItem(
            question=f"Where did {params.child} find {params.friend}?",
            answer=f"{params.child} found {params.friend} at {params.place}, sitting beside {params.object}.",
        ),
        QAItem(
            question="What clue foreshadowed the problem?",
            answer=f"The early clue was that {symptom['foreshadow'].format(**values)}",
        ),
        QAItem(
            question=f"What did {params.child} do instead of simply guessing?",
            answer=f"{params.child} listened to {params.friend}, asked questions, and helped inspect {params.object} with {params.helper}.",
        ),
        QAItem(
            question="What was the diagnosis?",
            answer=f"The problem was that {symptom['cause']}; it was not a personal failure by the friend.",
        ),
        QAItem(
            question="How was the slump changed?",
            answer=f"They solved the practical problem together, and {params.friend} felt less worried because {params.child} stayed patient and helpful.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does diagnose mean?",
            answer="To diagnose means to carefully figure out what is causing a problem.",
        ),
        QAItem(
            question="What is a slump?",
            answer="A slump is a low, tired, or discouraged feeling or period when someone is not doing their usual best.",
        ),
        QAItem(
            question="Why is foreshadowing useful in a story?",
            answer="Foreshadowing gives an early clue that helps readers understand an important event later.",
        ),
        QAItem(
            question="What does fisted mean?",
            answer="Fisted means held in a tightly closed fist.",
        ),
        QAItem(
            question="How can humor help a difficult moment?",
            answer="Gentle humor can make a difficult moment feel less frightening while people still take the problem seriously.",
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
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  facts      {world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            child="Luna",
            friend="Ari",
            helper="Grandma June",
            place="the library corner",
            object="a tiny red notebook",
            snack="banana muffins",
            symptom=2,
            clue=2,
            remedy=3,
            ending=2,
        ),
        StoryParams(
            child="Milo",
            friend="Bea",
            helper="Mr. Patel",
            place="the community garden",
            object="a blue mitten",
            snack="apple slices",
            symptom=0,
            clue=0,
            remedy=0,
            ending=0,
        ),
        StoryParams(
            child="Nia",
            friend="Cal",
            helper="Aunt Rosa",
            place="the apartment hallway",
            object="a paper kite",
            snack="cheese crackers",
            symptom=4,
            clue=4,
            remedy=4,
            ending=4,
        ),
        StoryParams(
            child="Theo",
            friend="Drew",
            helper="Coach Kim",
            place="the laundromat bench",
            object="a yellow lunchbox",
            snack="warm toast",
            symptom=3,
            clue=3,
            remedy=2,
            ending=3,
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
        print(asp_program("#show valid_story/6."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "{" in sample.story or "}" in sample.story:
                print("FAILED: generated story contains unresolved template text.")
                sys.exit(1)
        print(f"OK: generated and checked {len(CURATED)} curated stories.")
        return

    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} valid (child, friend, object, snack) combinations:\n")
        for child, friend, obj, snack in combinations[:40]:
            print(f"  {child} / {friend} / {obj} / {snack}")
        if len(combinations) > 40:
            print(f"  ... and {len(combinations) - 40} more")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and attempt < limit:
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            apply_seeded_structure(params, seed)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise StoryError("Could not produce enough distinct stories from the requested options.")

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
            header = f"### {params.child}: diagnosing {params.friend}'s slump"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"

        emit(sample, trace=args.trace, qa=args.qa, header=header)

        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
