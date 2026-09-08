#!/usr/bin/env python3
"""
A small mythic story world about a raffle, a dense forest, and friendship.
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
class Being:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    prize: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Being
    friend: Being
    prize: str
    forest: str = "dense"
    raffle_ticket: str = "shared"
    friendship: float = 0.0
    danger: str = "unknown"
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mira", "Tavi", "Niko", "Sora", "Pip", "Rin", "Oren"]
PRIZES = [
    "the moon-silver lantern",
    "the golden acorn",
    "the cloud-blue cloak",
    "the singing compass",
    "the starry crown",
]
OPENINGS = [
    "Long ago, beneath a moon like a white boat,",
    "In the first spring after the mountains learned to whisper,",
    "At the edge of an ancient kingdom,",
    "When the evening stars appeared above the hills,",
    "On a night when the river carried silver leaves,",
]
LESSONS = [
    "The forest remembered what the friends had learned: a prize may be won alone, but wonder grows when it is shared.",
    "From that night onward, the kingdom called their friendship a kind of magic stronger than luck.",
    "The raffle chose one ticket, yet the true treasure belonged to both hearts.",
    "The old trees taught that friendship is not a bargain for a reward; it is the light that helps us find the way.",
]
ENDINGS = [
    "They carried the prize together, and its glow made two paths where there had been only one.",
    "The prize shone above them as they walked home shoulder to shoulder.",
    "By dawn, every village child had heard how the friends had turned luck into kindness.",
    "The forest opened a bright green arch, as if the trees themselves approved.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic raffle and friendship story world.")
    ap.add_argument("--hero-name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--prize", choices=PRIZES)
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
    hero = args.hero_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != hero])
    prize = args.prize or rng.choice(PRIZES)
    return StoryParams(hero_name=hero, friend_name=friend, prize=prize)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("The two friends need different names.")
    if params.prize not in PRIZES:
        raise StoryError("That prize is not part of this raffle.")
    if not params.hero_name or not params.friend_name:
        raise StoryError("Both friends must have names.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    opening = rng.choice(OPENINGS)
    lesson = rng.choice(LESSONS)
    ending = rng.choice(ENDINGS)

    hero = Being(
        params.hero_name,
        "young traveler",
        meters={"distance_to_friend": 0.0, "distance_to_prize": 0.0},
        memes={"hope": 1.0, "friendship": 1.0},
    )
    friend = Being(
        params.friend_name,
        "young traveler",
        meters={"distance_to_hero": 0.0},
        memes={"trust": 1.0, "friendship": 1.0},
    )
    world = World(hero=hero, friend=friend, prize=params.prize, friendship=1.0)

    story = [
        f"{opening} {hero.name} and {friend.name} lived beside a dense forest where even moonlight had to ask permission to enter.",
        f"Each year the forest guardian held a raffle for {params.prize}, a wonder said to grant one honest wish.",
        f"The friends found one bright raffle ticket beneath a silver fern, but its two halves bore their names.",
        f"\"If the ticket wins, I will take the prize,\" said {hero.name}.",
        f"\"And if the forest asks us to choose, we will choose together,\" replied {friend.name}.",
        "They stepped beneath the trees to ask the guardian what the divided ticket meant.",
        "The path grew dense and twisted around roots like sleeping dragons.",
        f"At a fork, a thorny shadow whispered to {hero.name}, \"Leave {friend.name} behind, and the prize will surely be yours.\"",
        f"{hero.name} nearly followed the narrow path. Then {friend.name} called, \"A raffle may test luck, but friendship tests what we do with it!\"",
        f"{hero.name} turned back and answered, \"Then I will not trade you for a prize.\"",
        "Together they tied a red thread between their wrists and crossed the forest by its gentle pull.",
        "At the center stood the guardian, an old owl wearing a crown of leaves.",
        f"The owl opened one golden eye. \"Why did you return for one another when the {params.prize} could belong to only one?\"",
        f"{hero.name} said, \"Because a prize cannot fill the place left by a lost friend.\"",
        f"{friend.name} added, \"And whatever luck gives us, we can make kinder by sharing it.\"",
        "The owl placed the raffle ticket beneath its wing. The two halves joined, and the paper glowed like sunrise.",
        f"\"The raffle has chosen both of you,\" said the guardian. \"Not because luck has two hands, but because friendship does.\"",
        f"The friends received {params.prize} together.",
        lesson,
        f"{ending}",
    ]

    hero.meters["distance_to_prize"] = 0.0
    friend.meters["distance_to_hero"] = 0.0
    world.raffle_ticket = "joined by friendship"
    world.friendship = 2.0
    world.danger = "the shadow tried to separate the friends"
    world.facts.update(
        {
            "raffle": "a shared two-part ticket",
            "forest": "dense and twisting",
            "turn": "the hero returned instead of abandoning the friend",
            "guardian": "an old owl crowned with leaves",
            "resolution": "the raffle recognized their friendship and gave them the prize together",
            "lesson": lesson,
            "ending": ending,
        }
    )
    world.facts["story"] = " ".join(story)

    prompts = [
        f"Write a myth about a raffle for {params.prize} in a dense forest.",
        f"Tell a child-friendly myth in which {params.hero_name} and {params.friend_name} protect their friendship when luck tempts one to leave the other.",
        "Show through action and dialogue why a shared prize is less important than a loyal friend.",
    ]

    story_qa = [
        QAItem(
            question="What did the raffle ticket look like?",
            answer="It was one bright ticket whose two halves bore the names of both friends.",
        ),
        QAItem(
            question="What temptation did the forest shadow offer?",
            answer=f"The shadow urged {params.hero_name} to leave {params.friend_name} behind so the prize would be theirs alone.",
        ),
        QAItem(
            question=f"Why did {params.hero_name} turn back?",
            answer=f"{params.hero_name} turned back because losing {params.friend_name} would be worse than losing the raffle prize.",
        ),
        QAItem(
            question="Who judged the raffle?",
            answer="An old owl wearing a crown of leaves judged the raffle.",
        ),
        QAItem(
            question="How did the raffle end?",
            answer=f"The two ticket halves joined, and the guardian gave {params.prize} to both friends because they had chosen friendship.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a raffle?",
            answer="A raffle is a drawing in which a selected ticket wins a prize.",
        ),
        QAItem(
            question="What does dense mean when describing a forest?",
            answer="Dense means that many trees and plants grow close together, making the forest difficult to see or travel through.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people trust, help, and stand by one another.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an imaginative traditional tale that often explains a value, a mystery, or the actions of magical beings.",
        ),
        QAItem(
            question="Why can sharing a prize matter?",
            answer="Sharing a prize can matter because kindness and companionship may bring more lasting joy than keeping a valuable object alone.",
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
        w = sample.world
        print("\n--- trace ---")
        print(f"hero={w.hero.name}, kind={w.hero.kind}, meters={w.hero.meters}, memes={w.hero.memes}")
        print(f"friend={w.friend.name}, kind={w.friend.kind}, meters={w.friend.meters}, memes={w.friend.memes}")
        print(f"forest={w.forest}, raffle_ticket={w.raffle_ticket}, friendship={w.friendship}, danger={w.danger}")
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


ASP_RULES = r"""
valid_prize(P) :- prize(P).
shared_ticket :- ticket(shared).
friendship_wins :- shared_ticket, valid_prize(_).

#show valid_prize/1.
#show shared_ticket/0.
#show friendship_wins/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("prize", prize) for prize in PRIZES]
    facts.append(asp.fact("ticket", "shared"))
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_prizes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_prize/1."))
    return sorted(set(asp.atoms(model, "valid_prize")))


def asp_verify() -> int:
    import asp
    py = set((p,) for p in PRIZES)
    cl = set(asp_valid_prizes())
    if py != cl:
        print("MISMATCH between clingo and Python prize registry.")
        print("only in python:", sorted(py - cl))
        print("only in clingo:", sorted(cl - py))
        return 1
    for i, prize in enumerate(PRIZES):
        sample = generate(StoryParams("Luna", "Mira", prize, i))
        if prize not in sample.story or "friendship" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: clingo gate matches valid prizes ({len(py)} prizes), and stories pass.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(NAMES[i % len(NAMES)], NAMES[(i + 1) % len(NAMES)], prize, i)
            for i, prize in enumerate(PRIZES)
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_prize/1.\n#show shared_ticket/0.\n#show friendship_wins/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(p[0] for p in asp_valid_prizes()))
        return

    samples = []
    for i, params in enumerate(generation_params(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
