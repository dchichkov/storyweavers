#!/usr/bin/env python3
"""
A heartwarming storyworld about helium balloons, a worried friend, and the
bravery it takes to ask for help.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_here = Path(__file__).resolve()
_storyworlds_dir = next(
    (parent for parent in _here.parents if (parent / "results.py").is_file()),
    None,
)
if _storyworlds_dir is None:
    raise RuntimeError("Could not find storyworlds/results.py")
sys.path.insert(0, str(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Entity
    friend: Entity
    helper: Entity
    balloon: Entity
    place: str
    snag: str
    color: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    friend_name: str
    helper_name: str
    place: str
    snag: str
    color: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Theo", "Ruby", "Omar", "Bea", "Pip"]
HELPERS = ["Aunt Jo", "Grandpa", "Ms. Rowan", "Mr. Lee", "Grandma"]
PLACES = [
    "the school garden",
    "the library courtyard",
    "the neighborhood picnic",
    "the little park",
]
SNAGS = [
    "a low apple branch",
    "the edge of a garden awning",
    "a wooden trellis",
    "the corner of a shady pergola",
]
COLORS = ["blue", "yellow", "red", "green", "pink"]


ASP_RULES = r"""
brave(H) :- feels_fear(H), asks_help(H).
rescued(B) :- adult_assists(_), balloon_safe(B).
comforted(F) :- rescued(B), smiles(F).
#show brave/1.
#show rescued/1.
#show comforted/1.
"""


def _default_world() -> World:
    params = StoryParams(
        name="Luna",
        friend_name="Milo",
        helper_name="Aunt Jo",
        place=PLACES[0],
        snag=SNAGS[0],
        color=COLORS[0],
        seed=1,
    )
    world = build_world(params)
    simulate(world)
    return world


def asp_facts(world: Optional[World] = None) -> str:
    import asp

    if world is None:
        world = _default_world()
    facts = [
        asp.fact("feels_fear", "hero")
        if world.hero.memes.get("fear", 0) > 0
        else "",
        asp.fact("asks_help", "hero") if world.facts.get("asked_for_help") else "",
        asp.fact("adult_assists", "helper") if world.facts.get("adult_assisted") else "",
        asp.fact("balloon_safe", "balloon") if world.facts.get("balloon_safe") else "",
        asp.fact("smiles", "friend") if world.facts.get("friend_relieved") else "",
    ]
    return "\n".join(line for line in facts if line)


def asp_program(show: Optional[str] = None, world: Optional[World] = None) -> str:
    if show is None:
        show = "#show brave/1.\n#show rescued/1.\n#show comforted/1."
    return f"{asp_facts(world)}\n{ASP_RULES}\n{show}\n"


def _python_atoms(world: World) -> set[tuple[str, tuple[str, ...]]]:
    result: set[tuple[str, tuple[str, ...]]] = set()
    if world.hero.memes.get("fear", 0) > 0 and world.facts.get("asked_for_help"):
        result.add(("brave", ("hero",)))
    if world.facts.get("adult_assisted") and world.facts.get("balloon_safe"):
        result.add(("rescued", ("balloon",)))
    if world.facts.get("balloon_safe") and world.facts.get("friend_relieved"):
        result.add(("comforted", ("friend",)))
    return result


def asp_verify() -> int:
    import asp

    cases = [
        StoryParams("Luna", "Milo", "Aunt Jo", PLACES[0], SNAGS[0], COLORS[0], 11),
        StoryParams("Nia", "Theo", "Grandpa", PLACES[1], SNAGS[2], COLORS[3], 22),
        StoryParams("Ruby", "Omar", "Ms. Rowan", PLACES[2], SNAGS[3], COLORS[4], 33),
    ]
    for params in cases:
        world = build_world(params)
        simulate(world)
        model = asp.one_model(asp_program(world=world))
        actual = {
            (atom.name, tuple(arg.name for arg in atom.arguments))
            for atom in model
        }
        expected = _python_atoms(world)
        if actual != expected:
            print("MISMATCH between ASP and Python expectations.")
            print("ASP:", sorted(actual))
            print("PY :", sorted(expected))
            return 1
        sample = generate(params)
        if not all(mark in sample.story for mark in ('"', "At ", "By the time")):
            print("MISMATCH: generated story is missing a beginning, dialogue, or ending.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated story is missing its question-and-answer sets.")
            return 1
    print("OK: ASP parity and generated-story checks verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming helium-balloon stories about everyday bravery."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--helper-name", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--color", choices=COLORS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    possible_friends = [candidate for candidate in NAMES if candidate != name]
    friend_name = args.friend_name or rng.choice(possible_friends)
    if friend_name == name:
        raise StoryError("The hero and friend must have different names.")
    return StoryParams(
        name=name,
        friend_name=friend_name,
        helper_name=args.helper_name or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        snag=args.snag or rng.choice(SNAGS),
        color=args.color or rng.choice(COLORS),
    )


def _validate_params(params: StoryParams) -> None:
    checks = [
        ("name", params.name, NAMES),
        ("friend name", params.friend_name, NAMES),
        ("helper name", params.helper_name, HELPERS),
        ("place", params.place, PLACES),
        ("snag", params.snag, SNAGS),
        ("color", params.color, COLORS),
    ]
    for label, value, choices in checks:
        if value not in choices:
            raise StoryError(f"Unknown {label}: {value!r}. Choose a listed option.")
    if params.name == params.friend_name:
        raise StoryError("The hero and friend must have different names.")


def build_world(params: StoryParams) -> World:
    _validate_params(params)
    seed = params.seed
    if seed is None:
        seed = sum(
            ord(char)
            for char in (
                f"{params.name}|{params.friend_name}|{params.helper_name}|"
                f"{params.place}|{params.snag}|{params.color}"
            )
        )
    hero = Entity(
        id="hero",
        label=params.name,
        kind="child",
        memes={"fear": 0.55, "courage": 0.18, "trust": 0.35},
    )
    friend = Entity(
        id="friend",
        label=params.friend_name,
        kind="child",
        owner="friend",
        memes={"worry": 0.78, "relief": 0.0, "trust": 0.48},
    )
    helper = Entity(
        id="helper",
        label=params.helper_name,
        kind="adult",
        memes={"kindness": 0.85, "attention": 0.7},
    )
    balloon = Entity(
        id="balloon",
        label=f"{params.color} helium balloon",
        kind="balloon",
        owner="friend",
        meters={"height_m": 2.1, "tethered": 1.0, "snagged": 1.0},
        memes={"cheer": 0.7},
    )
    return World(
        hero=hero,
        friend=friend,
        helper=helper,
        balloon=balloon,
        place=params.place,
        snag=params.snag,
        color=params.color,
        seed=seed,
    )


def simulate(world: World) -> None:
    """Move the world through worry, a brave request, and a safe resolution."""
    if world.balloon.meters.get("tethered") != 1.0:
        raise StoryError("The balloon needs a tied ribbon so the children can ask for help safely.")
    if world.balloon.meters.get("snagged") != 1.0:
        raise StoryError("This story needs the balloon ribbon to be caught on a reachable place.")

    world.facts.update(
        noticed_snag=True,
        asked_for_help=False,
        adult_assisted=False,
        balloon_safe=False,
        friend_relieved=False,
    )

    # The hero acts while still afraid; bravery changes from a feeling into a choice.
    world.hero.memes["courage"] = 0.82
    world.hero.memes["fear"] = 0.25
    world.hero.memes["trust"] = 0.74
    world.facts["asked_for_help"] = True

    # The adult keeps the children on the ground and frees the ribbon with a hook.
    world.facts["adult_assisted"] = True
    world.balloon.meters.update(height_m=1.2, snagged=0.0, tethered=1.0)
    world.facts["balloon_safe"] = True
    world.friend.memes.update(worry=0.12, relief=0.88, trust=0.82)
    world.facts["friend_relieved"] = True

    if not is_reasonable(world):
        raise StoryError("The requested story state is not safe or emotionally coherent.")


def is_reasonable(world: World) -> bool:
    return bool(
        world.facts.get("asked_for_help")
        and world.facts.get("adult_assisted")
        and world.facts.get("balloon_safe")
        and world.hero.memes.get("fear", 0) > 0
        and world.hero.memes.get("courage", 0) > 0.5
        and world.friend.memes.get("relief", 0) > 0.5
        and world.balloon.meters.get("tethered") == 1.0
        and world.balloon.meters.get("snagged") == 0.0
    )


def _compose_story(world: World) -> str:
    h = world.hero.label
    f = world.friend.label
    adult = world.helper.label
    place = world.place
    color = world.color
    snag = world.snag

    if world.hero.memes["courage"] > 0.5 and world.facts["asked_for_help"]:
        brave_action = f'{h} took one wobbly breath and called, "{adult}, could you help us, please?"'
    else:
        brave_action = f"{h} looked around, hoping someone would notice."

    lines = [
        f"At {place}, {h} and {f} were tying paper hearts to a little basket when a {color} helium balloon bobbed above them.",
        f"A breeze lifted its ribbon onto {snag}. {f} still held the loose end, but the balloon tugged gently overhead.",
        f'"I want it back, but I feel silly asking," {f} whispered. {h} admitted, "I feel nervous too, but we can ask together."',
        brave_action,
        f'"Thank you for telling me," {adult} answered. "Stay right here on the ground, and I will free it carefully."',
        f"{adult} used a long-handled garden hook to ease the ribbon down without climbing or pulling hard.",
        f'{f} smiled as {adult} helped tie the ribbon securely to the basket handle. "I thought I had to solve it alone," {f} said.',
        f'"Me too," said {h}. "Asking together made it easier." The paper hearts fluttered beside the balloon instead of chasing it into the sky.',
        f"By the time the afternoon light warmed {place}, {h} and {f} were carrying the basket side by side, with the {color} balloon floating safely above them.",
    ]
    world.facts.update(
        discovery="speaking up let the children get safe help instead of trying to reach the balloon themselves",
        cause=f"a breeze caught the balloon's ribbon on {world.snag}",
        resolution=f"{world.helper.label} used a long-handled garden hook to free the ribbon, then helped tie it securely to the basket",
        ending=f"the {world.color} balloon floated safely above the basket as the friends carried it together",
        story=" ".join(lines),
    )
    return world.facts["story"]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.friend.label
    return [
        QAItem(
            question=f"What made {f} feel worried?",
            answer=f"{f} felt worried because a breeze caught the helium balloon's ribbon on {world.snag}.",
        ),
        QAItem(
            question=f"How did {h} show bravery?",
            answer=f"{h} felt nervous but asked {world.helper.label} to help, so the children did not try to reach the balloon by themselves.",
        ),
        QAItem(
            question="How was the balloon made safe?",
            answer=f"{world.helper.label} used a long-handled garden hook to free the ribbon and helped tie it securely to the basket.",
        ),
        QAItem(
            question="What changed for the friends by the end?",
            answer=f"{h} and {f} learned that asking for help together felt easier, and they carried the basket with the balloon safely tied to it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is helium?",
            answer="Helium is a very light gas. It can make a properly tied balloon float upward in the air.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing a helpful or right thing even when you feel afraid or unsure.",
        ),
        QAItem(
            question="Why should a child ask an adult for help with a stuck balloon?",
            answer="An adult can reach or free a stuck balloon safely, so a child does not need to climb or pull on it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story for young children about bravery and asking for help.",
        f"Tell a gentle story at {world.place} about friends and a helium balloon caught on {world.snag}.",
        "Show how a nervous child can be brave, work with a friend, and solve a small problem safely.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.friend, world.helper, world.balloon):
        lines.append(
            f"  {entity.id:7} {entity.kind:8} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.extend(
        [
            f"  place={world.place!r}",
            f"  snag={world.snag!r}",
            f"  facts={world.facts}",
        ]
    )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    out.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.extend(["", "== World QA =="])
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    story = _compose_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        world = _default_world()
        model = asp.one_model(asp_program(world=world))
        print(", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", "Aunt Jo", PLACES[0], SNAGS[0], COLORS[0], 101),
            StoryParams("Nia", "Theo", "Grandpa", PLACES[1], SNAGS[2], COLORS[3], 202),
            StoryParams("Ruby", "Omar", "Ms. Rowan", PLACES[2], SNAGS[3], COLORS[4], 303),
            StoryParams("Pip", "Bea", "Grandma", PLACES[3], SNAGS[1], COLORS[1], 404),
        ]
        samples = [generate(params) for params in curated]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.friend_name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
