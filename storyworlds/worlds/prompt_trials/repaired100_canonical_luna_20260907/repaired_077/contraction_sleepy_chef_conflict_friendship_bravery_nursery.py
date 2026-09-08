#!/usr/bin/env python3
"""
A gentle nursery-rhyme storyworld about a sleepy chef, a contraction,
friendship, and brave teamwork in a little nursery kitchen.
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
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    chef_name: str
    friend_name: str
    kitchen: str
    dish: str
    seed: Optional[int] = None


@dataclass
class World:
    chef: Character
    friend: Character
    kitchen: str
    dish: str
    contraction: str = ""
    sleepy: bool = False
    conflict: bool = False
    friendship: bool = False
    bravery: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Pip", "Mina", "Toby", "Nell", "Bram", "Daisy", "Rory"]
KITCHENS = [
    "the moonlit nursery kitchen",
    "the tiny kitchen by the rocking horse",
    "the warm kitchen beneath the nursery window",
    "the little kitchen beside the storybook shelf",
]
DISHES = ["porridge", "berry buns", "apple soup", "cinnamon toast"]
CONTRACTIONS = ["can't", "don't", "isn't", "we're", "it's"]

INCIDENTS = [
    {
        "title": "the too-early breakfast bell",
        "contraction": "can't",
        "setup": "the breakfast bell rang before the porridge was ready",
        "mistake": "the sleepy chef said, \"I can't stir one more time,\" and the friend thought the chef meant to quit",
        "risk": "the porridge could scorch if no one watched the pot",
        "clue": "the chef's hand still held the wooden spoon, even while the chef's eyes drooped",
        "first_action": "pulled the spoon away and frowned",
        "reply": "\"I can't do this alone,\" whispered the chef.",
        "friend_reply": "\"You don't have to,\" said the friend. \"We can make one small plan.\"",
        "repair": "opened the window, lowered the flame, and stirred while the chef rested on a stool",
        "ending": "the porridge puffed in soft bubbles as two spoons tapped a cheerful beat",
    },
    {
        "title": "the missing berry bowl",
        "contraction": "don't",
        "setup": "the bowl of berries rolled beneath a cupboard",
        "mistake": "the sleepy chef said, \"Don't ask me where it went,\" and the friend thought the chef was angry",
        "risk": "the berries might be crushed if someone dragged the heavy cupboard",
        "clue": "a red berry shine glimmered beside the cupboard's little wheel",
        "first_action": "reached for the cupboard handle with a worried sigh",
        "reply": "\"Don't make it worse,\" said the chef sleepily.",
        "friend_reply": "\"Then let's look before we lift,\" answered the friend.",
        "repair": "used a wooden spoon to roll the bowl gently into the open",
        "ending": "the berries bobbed in their bowl while the cupboard stayed safely still",
    },
    {
        "title": "the upside-down recipe",
        "contraction": "it's",
        "setup": "the recipe card slipped upside down beside a warm tray",
        "mistake": "the sleepy chef said, \"It's not clear,\" and the friend thought the chef disliked the friend's help",
        "risk": "a wrong measure could make the buns too salty",
        "clue": "the tiny salt drawing sat beside the number one, not the number four",
        "first_action": "snatched the card back with a hurt face",
        "reply": "\"It's not your fault,\" murmured the chef. \"My eyes are full of sleep.\"",
        "friend_reply": "\"Then we'll turn the card together,\" said the friend.",
        "repair": "turned the card right-side up and counted the spoonfuls aloud",
        "ending": "the buns rose like golden hills with just one small pinch of salt",
    },
    {
        "title": "the rattling mixing bowl",
        "contraction": "we're",
        "setup": "the mixing bowl rattled near the edge of the low table",
        "mistake": "the sleepy chef said, \"We're late,\" and the friend thought the chef wanted to rush",
        "risk": "the bowl could fall and spill batter across the nursery floor",
        "clue": "the clock had stopped, while the batter still needed a quiet minute",
        "first_action": "hurried to pour the batter before checking the table",
        "reply": "\"We're not racing,\" said the chef, catching a yawn.",
        "friend_reply": "\"Good,\" said the friend. \"We can steady the bowl first.\"",
        "repair": "moved the bowl away from the edge and waited until the batter was smooth",
        "ending": "the bowl sat safe and snug while the nursery clock began to tick again",
    },
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme sleepy chef storyworld.")
    ap.add_argument("--chef-name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--kitchen", choices=KITCHENS)
    ap.add_argument("--dish", choices=DISHES)
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
    chef = args.chef_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([name for name in NAMES if name != chef])
    kitchen = args.kitchen or rng.choice(KITCHENS)
    dish = args.dish or rng.choice(DISHES)
    return StoryParams(chef_name=chef, friend_name=friend, kitchen=kitchen, dish=dish)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.chef_name == params.friend_name:
        raise StoryError("The chef and friend need different names.")
    if params.kitchen not in KITCHENS:
        raise StoryError("That kitchen is not part of this nursery world.")
    if params.dish not in DISHES:
        raise StoryError("That dish is not on the nursery menu.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = rng.choice(INCIDENTS)

    chef = Character(
        name=params.chef_name,
        kind="chef",
        meters={"energy": 0.28, "distance_to_stove": 1.0},
        memes={"sleepy": 1.0, "careful": 0.7},
    )
    friend = Character(
        name=params.friend_name,
        kind="friend",
        meters={"energy": 0.82, "distance_to_chef": 0.7},
        memes={"loyal": 1.0, "brave": 0.8},
    )
    world = World(
        chef=chef,
        friend=friend,
        kitchen=params.kitchen,
        dish=params.dish,
        contraction=incident["contraction"],
        sleepy=True,
        conflict=True,
    )

    opening = rng.choice([
        "In the nursery kitchen, bright as a moonbeam and twice as small,",
        "When the rocking horse creaked and the night birds called,",
        "By the window where the silver star curtains swayed,",
        "At the little stove beneath the nursery clock,",
    ])
    coda = rng.choice([
        "And friendship, warm as toast, made the sleepy hour bright.",
        "So brave little helpers may rest, then begin again right.",
        "For kind words can mend a quarrel before morning light.",
        "And teamwork can turn a muddle to a meal just right.",
    ])

    lines = [
        f"{opening} {chef.name} the chef prepared {params.dish} for the nursery hall.",
        f"{chef.name} was sleepy, sleepy, sleepy, and {friend.name} stood nearby to help.",
        f"Then {incident['setup']}, and a small conflict began.",
        f"{incident['reply']} The contraction sounded sharp in the quiet kitchen.",
        f"{friend.name} misunderstood and {incident['first_action']}.",
        f"\"{incident['friend_reply'][1:-1]}\"",
        f"{chef.name} blinked. \"{incident['reply'][1:-1]}\"",
        f"{friend.name} took a brave breath. \"Then I will listen, not guess.\"",
        f"Together they looked closely. The clue was this: {incident['clue']}.",
        f"The danger was plain: {incident['risk']}.",
        f"So {friend.name} and {chef.name} {incident['repair']}.",
        f"{incident['ending']}.",
        coda,
        f"Goodnight, goodnight, to the chef and friend; their quarrel was mended, and kindness was the end.",
    ]

    world.friendship = True
    world.bravery = True
    world.facts.update({
        "incident": incident["title"],
        "contraction": incident["contraction"],
        "risk": incident["risk"],
        "clue": incident["clue"],
        "repair": incident["repair"],
        "ending": incident["ending"],
    })
    world.chef.meters["energy"] = 0.12
    world.friend.memes["brave"] = 1.0
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a nursery rhyme about {params.chef_name}, a sleepy chef, and a {incident['contraction']} misunderstanding.",
        f"Tell a child-friendly story in {params.kitchen} where friendship resolves {incident['title']}.",
        f"Show bravery through listening, checking a clue, and safely helping with {params.dish}.",
    ]

    story_qa = [
        QAItem(
            question=f"What did the sleepy chef's contraction seem to mean in {incident['title']}?",
            answer=f"It seemed to mean that the chef wanted to give up, but the chef really meant that help was needed because sleepiness made the task hard.",
        ),
        QAItem(
            question="What caused the conflict?",
            answer=f"The conflict began when {incident['mistake']}.",
        ),
        QAItem(
            question="What clue corrected the misunderstanding?",
            answer=f"The clue was that {incident['clue']}.",
        ),
        QAItem(
            question="How did the friends show bravery?",
            answer=f"They showed bravery by pausing, listening instead of guessing, and then they {incident['repair']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended when {incident['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a contraction?",
            answer="A contraction is a shortened form of two words, such as can't for cannot or we're for we are.",
        ),
        QAItem(
            question="What should a sleepy chef do?",
            answer="A sleepy chef should pause, move away from hot or sharp tools, and ask a trusted helper or adult to keep the kitchen safe.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is caring about someone, listening to them, and helping kindly when a problem appears.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing a safe and kind thing even when you feel worried, embarrassed, or unsure.",
        ),
        QAItem(
            question="Why should people check clues before blaming someone?",
            answer="Checking clues helps people understand what really happened and prevents a small misunderstanding from becoming a bigger conflict.",
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
        print("\n--- trace ---")
        print(f"chef={world.chef.name}, kind={world.chef.kind}, meters={world.chef.meters}, memes={world.chef.memes}")
        print(f"friend={world.friend.name}, kind={world.friend.kind}, meters={world.friend.meters}, memes={world.friend.memes}")
        print(
            f"kitchen={world.kitchen}, dish={world.dish}, contraction={world.contraction}, "
            f"sleepy={world.sleepy}, conflict={world.conflict}, friendship={world.friendship}, bravery={world.bravery}"
        )
        print(f"facts={world.facts}")
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


ASP_RULES = r"""
valid_kitchen(K) :- kitchen(K).
valid_dish(D) :- dish(D).
valid_contraction(C) :- contraction(C).
safe_conflict(C) :- conflict(C), friendship(C), bravery(C).
"""


def asp_facts() -> str:
    import asp
    facts = []
    facts.extend(asp.fact("kitchen", kitchen) for kitchen in KITCHENS)
    facts.extend(asp.fact("dish", dish) for dish in DISHES)
    facts.extend(asp.fact("contraction", contraction) for contraction in CONTRACTIONS)
    facts.append(asp.fact("conflict", "misunderstanding"))
    facts.append(asp.fact("friendship", "repair"))
    facts.append(asp.fact("bravery", "repair"))
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    expected_kitchens = {(item,) for item in KITCHENS}
    expected_dishes = {(item,) for item in DISHES}
    expected_contractions = {(item,) for item in CONTRACTIONS}
    model = asp.one_model(asp_program("#show valid_kitchen/1. #show valid_dish/1. #show valid_contraction/1."))
    actual_kitchens = set(asp.atoms(model, "valid_kitchen"))
    actual_dishes = set(asp.atoms(model, "valid_dish"))
    actual_contractions = set(asp.atoms(model, "valid_contraction"))
    if (
        actual_kitchens != expected_kitchens
        or actual_dishes != expected_dishes
        or actual_contractions != expected_contractions
    ):
        print("MISMATCH between ASP registries and Python registries.")
        return 1
    for index in range(5):
        params = StoryParams(
            chef_name=NAMES[index],
            friend_name=NAMES[index + 1],
            kitchen=KITCHENS[index % len(KITCHENS)],
            dish=DISHES[index % len(DISHES)],
            seed=index,
        )
        sample = generate(params)
        if not sample.story or "chef" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP registries match Python registries and generated stories pass.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                chef_name=NAMES[index % len(NAMES)],
                friend_name=NAMES[(index + 1) % len(NAMES)],
                kitchen=KITCHENS[index % len(KITCHENS)],
                dish=DISHES[index % len(DISHES)],
                seed=index,
            )
            for index in range(len(INCIDENTS))
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [
        resolve_params(args, random.Random(base + index))
        for index in range(max(0, args.n))
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_kitchen/1. #show valid_dish/1. #show valid_contraction/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show valid_kitchen/1. #show valid_dish/1. #show valid_contraction/1.")
        )
        for predicate in ("valid_kitchen", "valid_dish", "valid_contraction"):
            for atom in sorted(asp.atoms(model, predicate)):
                print(atom[0])
        return

    samples = []
    base = args.seed if args.seed is not None else 0
    for index, params in enumerate(generation_params(args)):
        params.seed = base + index
        samples.append(generate(params))

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
