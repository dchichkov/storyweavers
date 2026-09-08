#!/usr/bin/env python3
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


@dataclass(frozen=True)
class Territory:
    id: str
    label: str
    smallest: bool
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    territory: Territory
    hero: str
    mayor: str
    goose: str
    law: str
    misunderstanding: str
    foreshadowing: str
    suspense: str
    paragraphs: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


TERRITORIES = {
    "buttonwood": Territory(
        "buttonwood",
        "the smallest territory in the valley",
        True,
        {"area": 1.0, "border": 4.0},
        {"pride": 2.0, "confusion": 1.0},
    ),
    "teacup": Territory(
        "teacup",
        "the tiny territory beneath the teacup",
        True,
        {"area": 0.5, "border": 2.0},
        {"pride": 1.0, "confusion": 2.0},
    ),
    "puddle": Territory(
        "puddle",
        "the least-sized territory beside the puddle",
        True,
        {"area": 0.7, "border": 3.0},
        {"pride": 1.0, "confusion": 1.0},
    ),
}

LAWS = {
    "least": "The Least Law says that the least patch of land still deserves the same careful respect as a giant kingdom.",
}

NAMES = ["Luna", "Milo", "Pip", "Nora", "Tavi"]
MAYORS = ["Mayor Puddlewick", "Mayor Crumpet", "Mayor Bellweather"]
GOOSE_NAMES = ["Goose Honk", "Professor Wobble", "Duchess Beak"]


@dataclass(frozen=True)
class StoryParams:
    territory: str
    name: str
    mayor: str
    goose: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("buttonwood", "Luna", "Mayor Puddlewick", "Goose Honk", 1),
    StoryParams("teacup", "Milo", "Mayor Crumpet", "Professor Wobble", 2),
    StoryParams("puddle", "Nora", "Mayor Bellweather", "Duchess Beak", 3),
]


def _valid(params: StoryParams) -> None:
    if params.territory not in TERRITORIES:
        raise StoryError(f"Unknown territory: {params.territory}")
    if not params.name.strip():
        raise StoryError("The hero needs a name.")
    if not params.mayor.strip() or not params.goose.strip():
        raise StoryError("The mayor and goose need names.")


def build_story(params: StoryParams) -> World:
    _valid(params)
    territory = TERRITORIES[params.territory]
    world = World(
        territory=territory,
        hero=params.name,
        mayor=params.mayor,
        goose=params.goose,
        law=LAWS["least"],
        misunderstanding="Luna thought the law banned anyone from stepping across the border.",
        foreshadowing="A red ribbon on the border kept twitching whenever the goose sneezed.",
        suspense="At midnight, a huge shadow crept toward the forbidden line.",
    )
    world.meters.update({"border": territory.meters["border"], "alarm": 0.0, "distance": 0.0})
    world.memes.update({"curiosity": 1.0, "worry": 0.0, "relief": 0.0})
    world.facts.update(
        law=world.law,
        territory=territory.label,
        misunderstanding=world.misunderstanding,
        foreshadowing=world.foreshadowing,
        suspense=world.suspense,
    )

    world.say(
        f"In {territory.label}, {params.name} served as the assistant keeper of the border. "
        f"The border was a line of red ribbon stretched around three flowerpots, and {params.mayor} "
        f"called it important because even the least territory needed a law."
    )
    world.say(
        f"The law was simple: “{world.law}” "
        f"Unfortunately, {params.name} misunderstood it. {params.name} thought the law meant nobody "
        f"could cross the ribbon, not even to rescue a runaway sandwich."
    )
    world.say(
        f"“Does the law really forbid one little step?” asked {params.name}. "
        f"“It forbids careless trespassing,” said {params.mayor}. "
        f"“That sounds exactly like one little step wearing a hat,” replied {params.name}."
    )
    world.say(
        f"That evening, {world.foreshadowing} {params.name} tightened the knot, while {params.goose} "
        f"watched the border with the serious expression of a goose who had misplaced a crown."
    )
    world.meters["alarm"] = 1.0
    world.memes["worry"] = 1.0
    world.say(
        f"Then the moon rose. {world.suspense} It slid closer, closer, and closer. "
        f"{params.name} held the law book in one hand and a broom in the other. "
        f"The shadow reached the ribbon."
    )
    world.say(
        f"“Stop!” cried {params.name}. “The law says no crossing!” "
        f"“Read the whole sentence,” called {params.mayor} from the window. "
        f"“It says to respect the territory, not to abandon common sense!”"
    )
    world.say(
        f"{params.name} looked again. The shadow was not a giant burglar. It was {params.goose}, "
        f"dragging a picnic blanket that had caught on the ribbon. The goose sneezed, the ribbon flew loose, "
        f"and the blanket landed over {params.name}'s head."
    )
    world.meters["distance"] = 1.0
    world.memes["worry"] = 0.0
    world.memes["relief"] = 1.0
    world.say(
        f"{params.name} stepped across the border carefully, freed {params.goose}, and tied the ribbon again. "
        f"{params.mayor} marked the safe crossing in the law book. The least territory still had its law, "
        f"but now its keeper understood what the law was for."
    )
    world.say(
        f"At breakfast, {params.goose} sat proudly inside the flowerpot while {params.name} posted a new sign: "
        f"“Respect the border. Rescue sandwiches when necessary.” "
        f"The territory was tiny, the goose was enormous, and the law finally made sense."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a funny suspense story set in {world.territory.label}, where a character misunderstands a law.",
        f"Use this foreshadowing: {world.foreshadowing}",
        f"Resolve the suspense when the character learns that the law protects the territory rather than banning common sense.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What did the hero misunderstand about the law?",
            f"{world.hero} thought the law banned every crossing of the border, even an emergency rescue. "
            f"The law actually required people to respect the least territory carefully.",
        ),
        QAItem(
            "What foreshadowed the nighttime trouble?",
            f"The red border ribbon kept twitching whenever {world.goose} sneezed. "
            f"That small clue hinted that the goose and the ribbon would cause trouble later.",
        ),
        QAItem(
            "What made the suspenseful shadow?",
            f"The shadow was {world.goose} dragging a picnic blanket that had caught on the border ribbon. "
            f"It looked frightening until {world.hero} examined it.",
        ),
        QAItem(
            "How was the misunderstanding resolved?",
            f"{world.mayor} explained that the law protected the territory but did not forbid sensible rescue work. "
            f"{world.hero} then freed the goose and repaired the ribbon.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a territory?",
            "A territory is a particular area of land that belongs to or is cared for by a group or place.",
        ),
        QAItem(
            "Why can a law be useful?",
            "A law can be useful because it gives people a shared rule for protecting one another and handling problems fairly.",
        ),
        QAItem(
            "What does least mean?",
            "Least means the smallest amount or the smallest degree among the choices being compared.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"  territory: {world.territory.id} ({world.territory.label})",
            f"  meters: {world.meters}",
            f"  memes: {world.memes}",
            f"  law: {world.law}",
            f"  misunderstanding: {world.misunderstanding}",
            f"  foreshadowing: {world.foreshadowing}",
            f"  suspense: {world.suspense}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(key, "least") for key in TERRITORIES]


ASP_RULES = r"""
valid(T,L) :- territory(T), law(L), smallest(T), least_law(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key, territory in TERRITORIES.items():
        lines.append(asp.fact("territory", key))
        if territory.smallest:
            lines.append(asp.fact("smallest", key))
    lines.append(asp.fact("law", "least"))
    lines.append(asp.fact("least_law", "least"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_rows = set(asp_valid_combos())
    if py == clingo_rows:
        print(f"OK: ASP/Python parity holds for {len(py)} combinations.")
        return 0
    print("MISMATCH")
    print("Python only:", sorted(py - clingo_rows))
    print("ASP only:", sorted(clingo_rows - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comic suspense story about the least territory and a misunderstood law."
    )
    parser.add_argument("--territory", choices=sorted(TERRITORIES))
    parser.add_argument("--name")
    parser.add_argument("--mayor")
    parser.add_argument("--goose")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    territory = args.territory or rng.choice(sorted(TERRITORIES))
    name = args.name or rng.choice(NAMES)
    mayor = args.mayor or rng.choice(MAYORS)
    goose = args.goose or rng.choice(GOOSE_NAMES)
    return StoryParams(territory, name, mayor, goose, args.seed)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        rows = asp_valid_combos()
        print(f"{len(rows)} compatible combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            sample = generate(params)
            if sample.story not in seen:
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
