#!/usr/bin/env python3
"""
A small animal-story world about a curious trick, a repeated surprise,
and the laughter that helps friends learn what is really happening.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Animal:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    place: str
    trick: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Animal
    friend: Animal
    place: str
    trick: str
    attempts: int = 0
    discovered: bool = False
    repaired: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Pip", "Momo", "Tavi", "Nori", "Bram", "Cleo", "Roo"]
PLACES = [
    "the old orchard",
    "the meadow path",
    "the little pond",
    "the sunny hill",
    "the garden gate",
]
TRICKS = [
    {
        "name": "the upside-down hat",
        "object": "an old straw hat",
        "setup": "Luna tucked a leaf beneath an old straw hat and hid behind a fern",
        "first": "When Pip came near, Luna tugged the hat so it wiggled by itself.",
        "repeat": "It wiggled once, then twice, then a third time.",
        "humor": "Pip jumped so high that his tail brushed a dandelion, and the dandelion sprinkled his nose.",
        "clue": "a thin vine ran from the hat straight to Luna's hiding place",
        "repair": "Luna pulled the vine into the open and showed Pip how the hat moved",
        "ending": "the hat became a picnic bowl while the leaf rested on Luna's head",
    },
    {
        "name": "the talking stump",
        "object": "a hollow stump",
        "setup": "Luna hid behind a hollow stump and called through a tiny crack",
        "first": "Pip heard a voice say, \"Who goes there?\" and looked under every nearby bush.",
        "repeat": "Each time Pip asked a question, the stump answered with the same silly words.",
        "humor": "At last Pip asked, \"Are you a potato?\" and the stump replied, \"Are you a potato?\"",
        "clue": "Luna's pawprints circled the stump, and the voice always copied Pip exactly",
        "repair": "Luna stepped out, apologized for making Pip worry, and invited him to try the echo",
        "ending": "the stump kept its echo, but the two friends used it for a song",
    },
    {
        "name": "the rolling apple",
        "object": "a red apple",
        "setup": "Luna balanced a red apple on a sloping root and hid behind a berry bush",
        "first": "She nudged the root, and the apple rolled toward Pip as if it had chosen him.",
        "repeat": "The apple rolled toward him three times whenever he turned away.",
        "humor": "Pip tried to look brave, but he walked backward into a soft pile of leaves and wore one like a hat.",
        "clue": "the ground sloped down from the root, and a small pawprint marked the nudging spot",
        "repair": "Luna moved the apple away from the path and explained the slope before rolling it safely",
        "ending": "the apple was shared beneath the tree instead of chasing anyone",
    },
    {
        "name": "the feather sneeze",
        "object": "a bright feather",
        "setup": "Luna tied a bright feather to a grass stem beside the path",
        "first": "Whenever Pip passed, she pulled the grass so the feather brushed his nose.",
        "repeat": "Pip sneezed once, twice, and then once more.",
        "humor": "His final sneeze sent a berry rolling into his open mouth.",
        "clue": "the feather moved even when the breeze stopped, and a string glimmered below it",
        "repair": "Luna untied the string, apologized, and asked Pip whether he wanted to play a gentler guessing game",
        "ending": "the feather became a bookmark in Pip's storybook",
    },
    {
        "name": "the moonlit shadow",
        "object": "a broad cabbage leaf",
        "setup": "Luna held a broad cabbage leaf near the lantern so it made a giant shadow",
        "first": "Pip saw the shadow stretch across the shed and thought a huge animal had arrived.",
        "repeat": "The giant shape appeared whenever Pip took one step toward the door.",
        "humor": "Pip tried to roar back, but his roar came out as a tiny hiccup.",
        "clue": "the shadow's edge copied the leaf's wobbly shape",
        "repair": "Luna lowered the leaf, named the trick, and helped Pip make a funny shadow of his own",
        "ending": "two small shadows danced on the shed wall until bedtime",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal story world about a repeated trick.")
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--trick", choices=[item["name"] for item in TRICKS])
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
    hero = args.hero_name or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero]
    friend = args.friend_name or rng.choice(friend_choices)
    place = args.place or rng.choice(PLACES)
    trick = args.trick or rng.choice([item["name"] for item in TRICKS])
    return StoryParams(hero_name=hero, friend_name=friend, place=place, trick=trick)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("The two animals need different names so their conversation is clear.")
    if params.place not in PLACES:
        raise StoryError("That place is not part of this small animal world.")
    if params.trick not in {item["name"] for item in TRICKS}:
        raise StoryError("That trick is not available in the story world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    trick = next(item for item in TRICKS if item["name"] == params.trick)

    hero = Animal(
        name=params.hero_name,
        kind="fox",
        meters={"distance_to_friend": 4.0, "curiosity": 0.9},
        memes={"playful": 1.0, "curious": 1.0},
    )
    friend = Animal(
        name=params.friend_name,
        kind="rabbit",
        meters={"distance_to_trick": 3.0, "worry": 0.4},
        memes={"careful": 1.0, "humorous": 0.8},
    )
    world = World(hero=hero, friend=friend, place=params.place, trick=params.trick)

    opening = rng.choice([
        "One bright morning",
        "After breakfast",
        "At the start of a quiet afternoon",
        "While the breeze tickled the grass",
    ])
    lesson = rng.choice([
        "A joke is best when everyone can laugh after the surprise is explained.",
        "Curiosity is useful when it leads to looking closely instead of guessing wildly.",
        "A repeated trick may be funny, but a good friend notices when someone needs the truth.",
        "The funniest ending was not the surprise; it was learning how the surprise worked.",
    ])
    coda = rng.choice([
        "Afterward, they invented a rule: surprise once, explain twice.",
        "They laughed again, this time because both friends knew the secret.",
        "Before going home, they checked the path together so no one else would be startled.",
        "The next game began with a question, an answer, and permission to play.",
    ])

    lines = [
        f"{opening}, Luna the fox found {trick['object']} near {params.place}.",
        f"Luna was curious about a little trick, so {trick['setup']}.",
        f"{trick['first']} {trick['repeat']}",
        f"{params.friend_name} blinked and said, \"Is that {trick['object']} doing this?\"",
        f"Luna tried not to giggle. \"Maybe we should look more closely,\" she said.",
        f"{trick['humor']}",
        f"Then {params.friend_name} took a breath and answered, \"I want to know the trick, but I do not want to keep guessing.\"",
        f"Luna nodded. \"That is fair. Let us find the clue together.\"",
        f"They followed the evidence: {trick['clue']}.",
        f"The repeated surprise made sense at last. It was a trick, not a mysterious animal.",
        f"Luna {trick['repair']}.",
        lesson,
        coda,
        f"By sunset, {trick['ending']}.",
    ]

    world.attempts = 3
    world.discovered = True
    world.repaired = True
    world.facts.update({
        "trick_object": trick["object"],
        "repetition": trick["repeat"],
        "humor": trick["humor"],
        "clue": trick["clue"],
        "repair": trick["repair"],
        "lesson": lesson,
        "ending": trick["ending"],
        "story": " ".join(lines),
    })

    prompts = [
        f"Write an animal story about {params.hero_name}'s {params.trick} at {params.place}.",
        "Use repetition to make the trick funny, then let curiosity uncover a concrete clue.",
        "End with friends repairing the surprise and sharing a safe laugh.",
    ]

    story_qa = [
        QAItem(
            question=f"What trick did {params.hero_name} play?",
            answer=f"{params.hero_name} used {trick['object']} in this trick: {trick['setup']}.",
        ),
        QAItem(
            question="How did repetition make the trick funny?",
            answer=f"The trick happened again and again: {trick['repeat']} The repeated surprise led to a humorous moment: {trick['humor']}",
        ),
        QAItem(
            question=f"What made {params.friend_name} curious instead of simply running away?",
            answer=f"{params.friend_name} noticed the clue that {trick['clue']}.",
        ),
        QAItem(
            question="What did the friends say to each other?",
            answer=f"The friend asked, \"Is that {trick['object']} doing this?\" Luna replied, \"Maybe we should look more closely,\" and then they searched for the clue together.",
        ),
        QAItem(
            question="How was the trick repaired?",
            answer=f"{params.hero_name} {trick['repair']}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, {trick['ending']}. The friends understood the trick and could laugh together.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a trick?",
            answer="A trick is an action that makes something surprising or puzzling, often as a game or joke.",
        ),
        QAItem(
            question="Why can repetition be funny?",
            answer="Repetition can be funny because a familiar surprise returns in an unexpected rhythm, especially when the result becomes sillier each time.",
        ),
        QAItem(
            question="What does curiosity help an animal do?",
            answer="Curiosity helps an animal notice details, ask questions, and investigate carefully instead of making a quick guess.",
        ),
        QAItem(
            question="What should a friend do if a joke is no longer comfortable?",
            answer="A friend should say so clearly, and the joker should stop, explain the trick, apologize if needed, and choose a gentler game.",
        ),
        QAItem(
            question="Why is a concrete clue useful?",
            answer="A concrete clue connects the mystery to something visible, so the characters can test an idea and understand what really happened.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print()
        print("--- trace ---")
        print(f"hero={world.hero.name}, kind={world.hero.kind}, meters={world.hero.meters}, memes={world.hero.memes}")
        print(f"friend={world.friend.name}, kind={world.friend.kind}, meters={world.friend.meters}, memes={world.friend.memes}")
        print(
            f"place={world.place}, trick={world.trick}, attempts={world.attempts}, "
            f"discovered={world.discovered}, repaired={world.repaired}"
        )
        for key, value in world.facts.items():
            if key != "story":
                print(f"{key}={value}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_trick(T) :- trick(T).
valid_pair(H,F) :- hero(H), friend(F), H != F.
curious(H) :- hero(H), repeated_trick.
repaired(H,F) :- hero(H), friend(F), curious(H), clue_found, apology_given.

#show valid_place/1.
#show valid_trick/1.
#show valid_pair/2.
#show curious/1.
#show repaired/2.
"""


def asp_facts() -> str:
    import asp

    facts = []
    facts.extend(asp.fact("place", place) for place in PLACES)
    facts.extend(asp.fact("trick", trick["name"]) for trick in TRICKS)
    facts.append(asp.fact("hero", "luna"))
    facts.append(asp.fact("friend", "pip"))
    facts.extend([
        asp.fact("repeated_trick"),
        asp.fact("clue_found"),
        asp.fact("apology_given"),
    ])
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    place_model = asp.one_model(asp_program("#show valid_place/1."))
    trick_model = asp.one_model(asp_program("#show valid_trick/1."))
    pair_model = asp.one_model(asp_program("#show valid_pair/2."))
    curious_model = asp.one_model(asp_program("#show curious/1."))
    repaired_model = asp.one_model(asp_program("#show repaired/2."))

    py_places = {(place,) for place in PLACES}
    py_tricks = {(trick["name"],) for trick in TRICKS}
    py_pairs = {("luna", "pip")}
    py_curious = {("luna",)}
    py_repaired = {("luna", "pip")}

    checks = [
        ("places", py_places, set(asp.atoms(place_model, "valid_place"))),
        ("tricks", py_tricks, set(asp.atoms(trick_model, "valid_trick"))),
        ("pairs", py_pairs, set(asp.atoms(pair_model, "valid_pair"))),
        ("curiosity", py_curious, set(asp.atoms(curious_model, "curious"))),
        ("repair", py_repaired, set(asp.atoms(repaired_model, "repaired"))),
    ]
    failed = False
    for label, expected, actual in checks:
        if expected != actual:
            failed = True
            print(f"MISMATCH in {label}:")
            print("  python:", sorted(expected))
            print("  clingo:", sorted(actual))
    if failed:
        return 1

    for index, trick in enumerate(TRICKS):
        params = StoryParams(
            hero_name=NAMES[index % len(NAMES)],
            friend_name=NAMES[(index + 1) % len(NAMES)],
            place=PLACES[index % len(PLACES)],
            trick=trick["name"],
            seed=index,
        )
        sample = generate(params)
        if not sample.story or params.hero_name not in sample.story or params.friend_name not in sample.story:
            print("Generated-story exercise failed.")
            return 1

    print("OK: ASP/Python parity and generated-story exercises passed.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        result = []
        for index, trick in enumerate(TRICKS):
            hero = NAMES[index % len(NAMES)]
            friend = NAMES[(index + 1) % len(NAMES)]
            result.append(
                StoryParams(
                    hero_name=hero,
                    friend_name=friend,
                    place=PLACES[index % len(PLACES)],
                    trick=trick["name"],
                    seed=index,
                )
            )
        return result

    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(max(0, args.n))
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show valid_place/1.\n"
            "#show valid_trick/1.\n"
            "#show valid_pair/2.\n"
            "#show curious/1.\n"
            "#show repaired/2."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program(
            "#show valid_place/1.\n"
            "#show valid_trick/1.\n"
            "#show valid_pair/2.\n"
            "#show curious/1.\n"
            "#show repaired/2."
        ))
        for predicate in ("valid_place", "valid_trick", "valid_pair", "curious", "repaired"):
            for atom in asp.atoms(model, predicate):
                print(f"{predicate}{atom}")
        return

    samples = []
    for index, params in enumerate(generation_params(args)):
        if params.seed is None:
            params.seed = (args.seed if args.seed is not None else 0) + index
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
