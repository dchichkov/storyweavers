#!/usr/bin/env python3
"""
A child-facing mystery storyworld about a stingy brass bell, a reunion, and the
curiosity that reveals why the bell will not ring.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    aunt: Item
    bell: Item
    reunion: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    aunt_name: str
    reunion: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mina", "Toby", "Iris", "Pip", "Nora", "Leo", "Milo"]
AUNTS = ["Aunt Bea", "Aunt Jo", "Uncle Ren", "Grandma Sol", "Cousin Ada"]
REUNIONS = [
    "the old orchard",
    "the village hall",
    "the lakeside picnic",
    "the train-yard garden",
    "the moonlit barn",
]


ASP_RULES = r"""
#show curious/1.
#show stingy/1.
#show reunited/1.
#show bad_ending/1.

curious(H) :- follows_clue(H).
stingy(B) :- keeps_sound(B).
reunited(G) :- family_gathers(G), bell_found(G).
bad_ending(G) :- family_gathers(G), bell_found(G), bell_unfixed(G).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("follows_clue", "hero"),
            asp.fact("keeps_sound", "bell"),
            asp.fact("family_gathers", "reunion"),
            asp.fact("bell_found", "reunion"),
            asp.fact("bell_unfixed", "reunion"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show curious/1.\n"
        "#show stingy/1.\n"
        "#show reunited/1.\n"
        "#show bad_ending/1."
    )
    model = asp.one_model(program)
    actual = set()
    for atom in model:
        if atom.name == "curious":
            actual.add(("curious", (atom.arguments[0].name,)))
        elif atom.name == "stingy":
            actual.add(("stingy", (atom.arguments[0].name,)))
        elif atom.name == "reunited":
            actual.add(("reunited", (atom.arguments[0].name,)))
        elif atom.name == "bad_ending":
            actual.add(("bad_ending", (atom.arguments[0].name,)))
    expected = {
        ("curious", ("hero",)),
        ("stingy", ("bell",)),
        ("reunited", ("reunion",)),
        ("bad_ending", ("reunion",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    params = StoryParams("Luna", "Aunt Bea", "the old orchard", seed=7)
    sample = generate(params)
    required = ["Luna", "Aunt Bea", "bell", "reunion"]
    if not all(word.lower() in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required grounded details.")
        return 1
    print("OK: ASP parity and generated-story checks verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld about a stingy brass bell and a family reunion."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--aunt-name", choices=AUNTS)
    ap.add_argument("--reunion", choices=REUNIONS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        aunt_name=args.aunt_name or rng.choice(AUNTS),
        reunion=args.reunion or rng.choice(REUNIONS),
    )


def build_world(params: StoryParams) -> World:
    if not params.name or not params.aunt_name or not params.reunion:
        raise StoryError("A reunion mystery needs a child, a helper, and a meeting place.")
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.aunt_name}|{params.reunion}")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"curious {params.name}",
        kind="character",
        memes={"curiosity": 1.0, "worry": 0.35},
    )
    aunt = Item(
        id="aunt",
        label=params.aunt_name,
        phrase=params.aunt_name,
        kind="character",
        memes={"kindness": 0.9, "patience": 0.8},
    )
    bell = Item(
        id="bell",
        label="brass bell",
        phrase="a small brass bell with a stubborn silver clapper",
        kind="instrument",
        owner="reunion",
        meters={"diameter": 0.12, "sound": 0.0, "weight": 0.4},
        memes={"stinginess": 1.0, "secrecy": 0.8},
    )
    return World(hero=hero, aunt=aunt, bell=bell, reunion=params.reunion, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _mystery_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    a = world.aunt.label
    place = world.reunion
    hiding_place = _choice(
        rng,
        ["inside an empty flour sack", "beneath a blue picnic bench", "behind the stage curtain"],
    )
    clue = _choice(
        rng,
        ["three dusty crescent marks", "a thread of red ribbon", "one bright brass scratch"],
    )
    failed_plan = _choice(
        rng,
        ["a wooden spoon", "a pine cone", "a rolled-up napkin"],
    )
    world.facts.update(
        arc="mystery",
        discovery=(
            f"the bell was hiding {hiding_place}, and its clapper was tied still with "
            f"a narrow knot"
        ),
        cause=(
            "a worried caretaker had tied the clapper so the old bell would not ring "
            "during a storm, then forgotten the knot"
        ),
        clue=clue,
        resolution=(
            f"{h} loosened the knot with {a}'s help and tested the bell over a folded coat"
        ),
        consequence=(
            "the family heard the reunion bell too late and began supper without waiting "
            "for the missing cousins"
        ),
        ending=(
            "the bell finally gave one clear note, but the reunion table had already gone "
            "quiet and several guests had left"
        ),
        bad_ending=True,
        stingy=True,
    )
    lines = [
        f"At {place}, {h} arrived early for a family reunion and noticed that the welcome bell made no sound.",
        f"Everyone pulled its cord. The bell gave only a tiny cough, as if it were being stingy with every note.",
        f'"A bell should ring when it is asked," said {h}. "{a}, do you hear that strange little silence?"',
        f'"I hear the silence," said {a}. "Then let us look for a clue instead of pulling harder."',
        f"Near the bell stand, {h} found {clue} in the dust and followed them behind a stack of chairs.",
        f"The marks led to {hiding_place}. Inside was the brass bell, wrapped in a cloth with its clapper tied tight.",
        f'"Who tied you up?" asked {h}. The bell did not answer, but its quiet shine made the question feel important.',
        f"{a} remembered that a storm had once frightened the caretaker. The knot had been meant to keep the bell from banging all night, but nobody had untied it afterward.",
        f"{h} tried to pry the knot loose with {failed_plan}. The plan slipped, the napkin flew, and the bell stayed stubbornly silent.",
        f'"Curiosity needs care," said {a}. "Let us loosen one loop at a time."',
        f"Together they eased the knot apart and tested the bell over a folded coat. DONG! The sound bounced across the yard.",
        f"But the reunion had already begun without them. {world.facts['consequence'].capitalize()}.",
        f"By the time {h} and {a} reached the table, {world.facts['ending']}. {h} carried the untied bell home, determined to ask questions before the next silence grew.",
    ]
    return " ".join(lines)


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x5A17C)
    return _mystery_arc(world, rng)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = world.hero.label
    return [
        QAItem(
            question=f"What mystery did {h} notice at the reunion?",
            answer=f"{h} noticed that the brass bell would not ring even when people pulled its cord.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was {f['clue']} in the dust, which led to the bell hidden behind the chairs.",
        ),
        QAItem(
            question="Why was the bell silent?",
            answer=f"The bell was silent because {f['cause']}.",
        ),
        QAItem(
            question=f"What did {h} and the helper do?",
            answer=f"{f['resolution'].capitalize()}.",
        ),
        QAItem(
            question="Why did the story have a bad ending?",
            answer=f"The ending was bad because {f['consequence']}, so the bell was fixed too late.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brass bell?",
            answer="A brass bell is a hollow metal object that makes a ringing sound when its clapper strikes the inside.",
        ),
        QAItem(
            question="What does curiosity do in a mystery?",
            answer="Curiosity encourages a character to notice clues, ask questions, and investigate instead of giving up.",
        ),
        QAItem(
            question="What is a reunion?",
            answer="A reunion is a meeting where people who have been apart come together again.",
        ),
        QAItem(
            question="Why can a bell be tied still?",
            answer="A bell can be tied still to stop it from making noise, such as during a storm or while it is being carried.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-facing mystery about a stingy brass bell that will not ring at a reunion.",
        f"Tell a curiosity-driven mystery set at {world.reunion}, with clues, a helpful relative, and a bad ending caused by delay.",
        "Write a gentle mystery in which asking careful questions reveals why an important sound is missing.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.aunt, world.bell]:
        lines.append(
            f"  {ent.id:6} {ent.kind:10} label={ent.label!r} owner={ent.owner!r} "
            f"meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  reunion={world.reunion!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.extend(["", "== World QA =="])
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show curious/1.\n"
                "#show stingy/1.\n"
                "#show reunited/1.\n"
                "#show bad_ending/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show curious/1.\n"
                "#show stingy/1.\n"
                "#show reunited/1.\n"
                "#show bad_ending/1."
            )
        )
        print("ASP model:")
        for atom in sorted(str(item) for item in model):
            print(f"  {atom}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Aunt Bea", "the old orchard", seed=base_seed),
            StoryParams("Mina", "Uncle Ren", "the village hall", seed=base_seed + 1),
            StoryParams("Iris", "Grandma Sol", "the lakeside picnic", seed=base_seed + 2),
            StoryParams("Pip", "Cousin Ada", "the moonlit barn", seed=base_seed + 3),
        ]
        samples = [generate(item) for item in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No story could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.reunion}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
