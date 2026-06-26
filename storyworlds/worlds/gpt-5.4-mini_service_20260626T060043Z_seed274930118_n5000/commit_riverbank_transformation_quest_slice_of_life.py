#!/usr/bin/env python3
"""
A small story world set at a riverbank, where a child makes a tiny commitment,
takes a gentle quest, and ends transformed by what they learn and do.

The seed idea is slice-of-life: a quiet day near the river becomes meaningful
because someone decides to commit to a helpful task, follows it through, and
changes a little in the process.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str = "riverbank"
    child: str = "Mina"
    companion: str = "Grandpa"
    quest: str = "collect the fallen litter"
    transformation: str = "brave"
    commitment: str = "commit to helping the riverbank stay clean"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 1.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"care": 0.0, "confidence": 0.0, "calm": 0.0})

    def pronoun(self) -> str:
        return "they"


@dataclass
class World:
    place: str
    child: Person
    companion: Person
    river_cleanliness: float = 0.4
    river_mood: float = 0.3
    found_items: list[str] = field(default_factory=list)
    committed: bool = False
    quest_started: bool = False
    quest_finished: bool = False
    transformed: bool = False
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Riverbank slice-of-life story world.")
    ap.add_argument("--place", choices=["riverbank"], default="riverbank")
    ap.add_argument("--child")
    ap.add_argument("--companion")
    ap.add_argument("--quest")
    ap.add_argument("--transformation")
    ap.add_argument("--commitment")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


NAME_POOL = ["Mina", "Theo", "Iris", "Jun", "Sana", "Ari", "Niko", "Lina"]
COMPANION_POOL = ["Grandpa", "Mom", "Auntie", "Dad", "Neighbor Sam"]
QUEST_POOL = [
    "collect the fallen litter",
    "stack smooth stones into a little wall",
    "bring seeds to plant by the reeds",
    "return a lost kite to the path",
]
TRANS_POOL = ["confident", "kind", "patient", "careful", "thoughtful"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAME_POOL)
    companion = args.companion or rng.choice(COMPANION_POOL)
    quest = args.quest or rng.choice(QUEST_POOL)
    transformation = args.transformation or rng.choice(TRANS_POOL)
    commitment = args.commitment or "commit to helping the riverbank stay tidy"
    if "commit" not in commitment.lower():
        commitment = f"commit to {commitment}"
    if args.place and args.place != "riverbank":
        raise StoryError("This world only supports the riverbank setting.")
    return StoryParams(
        place="riverbank",
        child=child,
        companion=companion,
        quest=quest,
        transformation=transformation,
        commitment=commitment,
    )


def make_world(params: StoryParams) -> World:
    child = Person(name=params.child, role="child")
    companion = Person(name=params.companion, role="companion")
    return World(place=params.place, child=child, companion=companion)


def _maybe_transform(world: World, params: StoryParams) -> None:
    if world.committed and world.quest_finished:
        world.transformed = True
        world.child.memes["confidence"] += 1.0
        world.child.memes["care"] += 1.0
        world.child.memes["calm"] += 0.5
        world.say(
            f"By the end, {world.child.name} felt {params.transformation} in a new way, "
            f"like the riverbank had given back a quiet, shiny piece of courage."
        )


def generate_story(world: World, params: StoryParams) -> None:
    world.say(
        f"On a soft afternoon at the riverbank, {world.child.name} walked beside {world.companion.name} "
        f"and watched the water slide past the reeds."
    )
    world.say(
        f"{world.child.name} noticed a tiny ring of litter near a smooth stone and made a small promise: "
        f"{params.commitment}."
    )
    world.committed = True
    world.child.memes["care"] += 1.0
    world.child.meters["energy"] -= 0.1
    world.say(
        f"{world.companion.name} smiled and gave {world.child.name} a bag and a glove, "
        f"because this little quest was best done carefully, one handful at a time."
    )
    world.quest_started = True
    world.say(
        f"So {world.child.name} began the quest to {params.quest}, stepping slowly along the bank, "
        f"picking up paper, a bottle cap, and a bent straw."
    )
    world.found_items.extend(["paper", "bottle cap", "bent straw"])
    world.river_cleanliness += 0.4
    world.river_mood += 0.3
    world.child.meters["energy"] -= 0.2
    world.child.memes["confidence"] += 0.5
    world.say(
        f"At first, {world.child.name}'s hands were a little unsure, but the shore grew cleaner and the water "
        f"looked brighter where the mess had been."
    )
    world.quest_finished = True
    world.say(
        f"When the bag was full, {world.child.name} stood up straighter and looked at the riverbank with a warm smile."
    )
    _maybe_transform(world, params)


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {p.child} spend the afternoon?",
            answer=f"{p.child} spent the afternoon at the riverbank with {p.companion}.",
        ),
        QAItem(
            question=f"What did {p.child} commit to do?",
            answer=f"{p.child} made a commitment to {p.quest} and help the riverbank stay clean.",
        ),
        QAItem(
            question=f"How did the quest change {p.child}?",
            answer=f"By the end, {p.child} felt more {p.transformation}, because finishing the quest gave {p.child} more confidence.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land next to a river.",
        ),
        QAItem(
            question="Why might people pick up litter near water?",
            answer="People pick up litter near water to keep the shore clean and protect the place where animals and plants live.",
        ),
        QAItem(
            question="What does it mean to commit to something?",
            answer="To commit to something means to decide to do it and keep trying until it is done.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a gentle slice-of-life story set at a {params.place} about a child who makes a commitment.",
        f"Tell a child-friendly quest story where {params.child} goes to the riverbank to {params.quest}.",
        f"Write a short story about how helping at the riverbank can transform someone into a more {params.transformation} person.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(riverbank).
commitment(X) :- phrase(X).
quest(Q) :- task(Q).
transformation(T) :- feeling(T).
valid_story :- place(riverbank), commitment(_), quest(_), transformation(_).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "riverbank"),
            asp.fact("phrase", "commit to helping the riverbank stay clean"),
            asp.fact("task", "collect the fallen litter"),
            asp.fact("feeling", "brave"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP story gate is satisfiable.")
        return 0
    print("MISMATCH: ASP story gate did not produce a model.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        print(asdict(sample.params))
        print({
            "child": sample.world.child.meters | sample.world.child.memes,
            "river_cleanliness": sample.world.river_cleanliness,
            "river_mood": sample.world.river_mood,
            "committed": sample.world.committed,
            "quest_started": sample.world.quest_started,
            "quest_finished": sample.world.quest_finished,
            "transformed": sample.world.transformed,
            "found_items": sample.world.found_items,
        })
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Mina",
        companion="Grandpa",
        quest="collect the fallen litter",
        transformation="confident",
        commitment="commit to helping the riverbank stay clean",
    ),
    StoryParams(
        child="Theo",
        companion="Mom",
        quest="bring seeds to plant by the reeds",
        transformation="thoughtful",
        commitment="commit to taking care of the quiet shore",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
