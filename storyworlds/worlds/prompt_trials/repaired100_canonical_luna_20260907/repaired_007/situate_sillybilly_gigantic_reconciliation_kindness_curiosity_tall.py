#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about Sillybilly, a gigantic mix-up, and the
kindness and curiosity that lead to reconciliation.
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
from collections import defaultdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Tale:
    key: str
    object_name: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    exchange: tuple[str, str]
    action: tuple[str, str]
    ending: tuple[str, str]
    problem: str
    solution: str
    proof: str


TALES = (
    Tale(
        "bell",
        "gigantic bell",
        (
            "In the high town of Belltop, Sillybilly tried to situate a gigantic bell on the mayor's tiny porch.",
            "He had hauled it there with one sneeze, three goats, and a wagon that complained all the way uphill.",
        ),
        (
            "The bell slipped sideways and covered the porch, the doorway, and half the mayor's begonias.",
            "The mayor shouted, \"Sillybilly, you have made a gigantic muddle!\"",
        ),
        (
            "Sillybilly bowed. \"I am sorry. May I ask why the porch cracked?\"",
            "\"Because the bell needs a strong stone arch,\" said the mayor, calming down enough to point.",
        ),
        (
            "With kindness, the mayor brought neighbors, and with curiosity, Sillybilly found an old arch behind the shed.",
            "Together they rolled the bell beneath the arch, where its deep note shook dust from the moon.",
        ),
        (
            "The mayor and Sillybilly shook hands, and their reconciliation was louder than the bell.",
            "After that, the porch held flowers, the arch held music, and nobody called a question silly.",
        ),
        "the bell damaged the porch because it was placed on a weak wooden porch",
        "they found a stone arch and moved the bell together",
        "the bell rang safely beneath the stone arch",
    ),
    Tale(
        "hat",
        "gigantic hat",
        (
            "At Roundabout Fair, Sillybilly tried to situate a gigantic hat over the town's weather vane.",
            "The hat was so broad that clouds used its brim as a picnic table.",
        ),
        (
            "A gust lifted the hat and dropped it over the baker's shop, hiding every bun and broom.",
            "The baker cried, \"Sillybilly, your hat has swallowed my whole morning!\"",
        ),
        (
            "Sillybilly peeked from beneath the brim. \"What would help you find your shop again?\"",
            "\"A bright flag and a little patience,\" said the baker, softening his voice.",
        ),
        (
            "Sillybilly apologized, and the baker showed him how to tie the hat to four sturdy posts.",
            "They raised it as a fair tent, then hung the bright flag where every customer could see.",
        ),
        (
            "The baker and Sillybilly shared warm buns in their new shade.",
            "Their reconciliation made the hat useful at last, and even the clouds applauded with rain.",
        ),
        "the hat fell over the bakery and blocked its entrance",
        "they tied the hat to sturdy posts and turned it into a fair tent",
        "the bakery reopened beneath the useful hat",
    ),
    Tale(
        "marble",
        "gigantic marble",
        (
            "On Pebble Plain, Sillybilly tried to situate a gigantic marble in the village game.",
            "It was taller than the water tower and rolled whenever anyone said the word 'round.'",
        ),
        (
            "The marble rolled through the gate and bumped the gardener's fence flat.",
            "The gardener frowned. \"Sillybilly, your game has become a gigantic garden problem!\"",
        ),
        (
            "Sillybilly said, \"I am sorry. Where did the marble wish to go?\"",
            "\"Toward the old hollow hill,\" answered the gardener. \"It might fit there.\"",
        ),
        (
            "The gardener and Sillybilly followed the rolling marble with kindness instead of blame.",
            "Their curiosity led them to the hollow hill, where they guided the marble into a round stone bowl.",
        ),
        (
            "The fence was mended, the marble became the village sundial, and the gardener hugged Sillybilly.",
            "Their reconciliation made noon shine on everyone, even the fellow who had started the trouble.",
        ),
        "the marble rolled through the gate and flattened the gardener's fence",
        "they guided it into a hollow hill to become a sundial",
        "the repaired fence and village sundial showed the problem was healed",
    ),
)


PLACES = {
    "belltop": Place("belltop", "the high town of Belltop", {"town", "hill"}),
    "roundabout": Place("roundabout", "Roundabout Fair", {"fair", "town"}),
    "pebble_plain": Place("pebble_plain", "Pebble Plain", {"plain", "village"}),
}

NAMES = {
    "friend": ["Milo", "Nora", "Pip", "Tessa"],
    "neighbor": ["Mayor Ada", "Baker June", "Gardener Sol", "Captain Bea"],
}


@dataclass
class StoryParams:
    place: str = "belltop"
    friend_name: str = "Milo"
    neighbor_name: str = "Mayor Ada"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


def valid_combos() -> list[tuple[str, str]]:
    return [(place, tale.key) for place in PLACES for tale in TALES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    friend = args.friend or rng.choice(NAMES["friend"])
    neighbor = args.neighbor or rng.choice(NAMES["neighbor"])
    return StoryParams(place=place, friend_name=friend, neighbor_name=neighbor)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}. Choose a listed place.")
    if not params.friend_name.strip() or not params.neighbor_name.strip():
        raise StoryError("Both character names must be non-empty.")
    if params.friend_name.strip().lower() == params.neighbor_name.strip().lower():
        raise StoryError("The two characters need different names.")

    rng = random.Random(params.seed)
    tale = TALES[rng.randrange(len(TALES))]
    world = World(PLACES[params.place])
    friend = world.add(Entity("sillybilly", "character", params.friend_name))
    neighbor = world.add(Entity("neighbor", "character", params.neighbor_name))
    object_entity = world.add(Entity("gigantic_object", "object", tale.object_name))

    friend.memes["curiosity"] = 1.0
    friend.memes["kindness"] = 1.0
    neighbor.memes["patience"] = 0.0
    object_entity.meters["gigantic"] = 1.0
    world.place.meters["open_space"] = 1.0

    for line in tale.opening:
        world.say(line.replace("Sillybilly", friend.label))
    world.para()

    object_entity.meters["misplaced"] = 1.0
    world.place.meters["trouble"] = 1.0
    friend.memes["worry"] = 1.0
    neighbor.memes["anger"] = 1.0
    for line in tale.trouble:
        world.say(line.replace("Sillybilly", friend.label).replace("the mayor", neighbor.label.lower()))
    world.para()

    friend.memes["curiosity"] += 1.0
    neighbor.memes["patience"] += 1.0
    for line in tale.exchange:
        world.say(line.replace("Sillybilly", friend.label).replace("the mayor", neighbor.label.lower()))
    world.para()

    object_entity.meters["misplaced"] = 0.0
    object_entity.meters["situated"] = 1.0
    world.place.meters["trouble"] = 0.0
    friend.memes["kindness"] += 1.0
    neighbor.memes["anger"] = 0.0
    neighbor.memes["reconciliation"] = 1.0
    for line in tale.action:
        world.say(line.replace("Sillybilly", friend.label).replace("the mayor", neighbor.label.lower()))
    world.para()

    friend.memes["joy"] = 1.0
    neighbor.memes["joy"] = 1.0
    world.facts.update(
        friend=friend.label,
        neighbor=neighbor.label,
        tale=tale,
        object=tale.object_name,
        problem=tale.problem,
        solution=tale.solution,
        proof=tale.proof,
        reconciled=True,
        curious=True,
        kind=True,
    )
    for line in tale.ending:
        world.say(line.replace("Sillybilly", friend.label).replace("the mayor", neighbor.label.lower()))
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    f = world.facts
    tale: Tale = f["tale"]
    prompts = [
        "Write a child-friendly Tall Tale using the words situate, sillybilly, and gigantic.",
        f"Tell a Tall Tale in which {f['friend']} uses curiosity and kindness after {f['problem']}.",
        "Show reconciliation through a brief conversation and a concrete happy ending.",
    ]
    story_questions = [
        QAItem(
            "What gigantic problem happened?",
            f"The {f['object']} caused trouble because {f['problem']}.",
        ),
        QAItem(
            "How did curiosity and kindness help?",
            f"{f['friend']} asked a careful question, and then {f['solution']}.",
        ),
        QAItem(
            "What showed that reconciliation happened?",
            f"The story ended with {f['proof']}, and the two characters made peace.",
        ),
    ]
    world_questions = [
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a disagreement by listening, apologizing, and finding a way forward together.",
        ),
        QAItem(
            "Why is curiosity useful?",
            "Curiosity encourages someone to ask questions and learn what is really happening before choosing a solution.",
        ),
        QAItem(
            "What does kindness mean?",
            "Kindness means treating others with care and helping instead of adding blame to a difficult moment.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_questions,
        world_qa=world_questions,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  place: {world.place.id}, meters={dict(world.place.meters)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = r"""
gigantic(gigantic_object).
misplaced(gigantic_object) :- trouble.
curious(sillybilly).
kind(sillybilly).
reconciliation :- curious(sillybilly), kind(sillybilly), neighbor_patient.
situated(gigantic_object) :- reconciliation.
#show reconciliation/0.
#show situated/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("trouble"),
            asp.fact("neighbor_patient"),
            asp.fact("sillybilly"),
            asp.fact("gigantic_object"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show reconciliation/0."))
        if not asp.atoms(model, "reconciliation"):
            print("ASP parity failed: reconciliation was not derived.")
            return 1
        sample = generate(StoryParams(seed=7))
        if "reconciliation" not in sample.story.lower():
            print("Story smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A Sillybilly gigantic reconciliation Tall Tale world.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--friend")
    parser.add_argument("--neighbor")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reconciliation/0.\n#show situated/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reconciliation/0.\n#show situated/1."))
        print({"reconciliation": asp.atoms(model, "reconciliation"), "situated": asp.atoms(model, "situated")})
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for i, place in enumerate(PLACES):
            samples.append(generate(StoryParams(place=place, seed=base_seed + i)))
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
