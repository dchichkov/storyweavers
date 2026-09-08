#!/usr/bin/env python3
"""
A small superhero storyworld about a contestant, a flashback mystery, and sharing.

The contestant must solve a mystery hidden in a flashback. The solution becomes
stronger when the contestant shares clues and credit with friends.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carries: Optional[str] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    power: str
    city: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    clue: str
    flashback: str
    mystery: str
    danger: str
    teammate: str
    teammate_power: str
    action: str
    solution: str
    shared_result: str
    final_image: str


NAMES = ["Luna", "Maya", "Zara", "Nia", "Tavi", "Remy"]
POWERS = ["starlight speed", "echo hearing", "wind lifting", "glowing maps"]
CITIES = ["Brightbridge", "Cloudline City", "Harbor Heights", "Sunbeam Square"]

CASES = [
    Case(
        "a silver button stamped with a tiny comet",
        "the night the Star Beacon went dark",
        "who stole the missing light from the city's rescue tower",
        "a storm was rolling toward the harbor",
        "Bolt",
        "a super-speed dash",
        "followed the comet marks across the roofs",
        "the button belonged to a repair coat, and the beacon had not been stolen; its safety switch was hidden under the old bridge",
        "the beacon shone again, and every helper's clue was named on the news",
        "The Star Beacon painted a silver path across the clouds while the friends stood together beneath it.",
    ),
    Case(
        "a warm blue feather beside the school clock",
        "the afternoon when every school bell rang at once",
        "who had awakened the bells and frightened the younger students",
        "the final bell began shaking the old clock tower",
        "Comet",
        "a leap that could cross three rooftops",
        "shared the feather clue before climbing the tower",
        "the feather came from a friendly sky-bird trapped in the bell rope; freeing it stopped the ringing",
        "the bird flew safely away, and the team repaired the rope together",
        "The school bells rang one gentle note as the blue bird circled above the grateful children.",
    ),
    Case(
        "a red spark trapped inside a glass marble",
        "the morning the firehouse alarm called every hero away",
        "why a fake alarm had emptied the streets",
        "a real kitchen fire had started near the market",
        "Moss",
        "a shield that could cool hot stone",
        "gave the marble to the team instead of hiding it",
        "the spark was a training signal left by a young inventor, while the real emergency needed the heroes' help",
        "the inventor apologized, and the team used the marble's signal to guide people to safety",
        "The market reopened under bright banners that read, 'Many brave hands make one safe city.'",
    ),
]


ASP_RULES = r"""
contestant(luna).
flashback(luna).
mystery(luna).
shares_clue(luna).
solves_mystery(luna).
heroic(luna) :- contestant(luna), flashback(luna), mystery(luna), shares_clue(luna), solves_mystery(luna).
#show heroic/1.
#show shares_clue/1.
#show solves_mystery/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("contestant", "luna"),
        asp.fact("flashback", "luna"),
        asp.fact("mystery", "luna"),
        asp.fact("shares_clue", "luna"),
        asp.fact("solves_mystery", "luna"),
    ])


def asp_program(show: str = "#show heroic/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about a contestant solving a flashback mystery."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--city", choices=CITIES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        power=args.power or rng.choice(POWERS),
        city=args.city or rng.choice(CITIES),
    )


def build_world(params: StoryParams) -> World:
    if params.name not in NAMES:
        raise StoryError("name must be a registered contestant")
    if params.power not in POWERS:
        raise StoryError("power must be a registered superhero power")
    if params.city not in CITIES:
        raise StoryError("city must be a registered setting")

    cursor = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.city)
    case = CASES[cursor % len(CASES)]
    world = World()

    contestant = world.add(Entity(
        "contestant", "hero", params.name,
        meters={"courage": 1.0, "clues_shared": 0.0},
        memes={"wonder": 1.0, "trust": 0.0},
    ))
    partner = world.add(Entity(
        "partner", "hero", case.teammate,
        meters={"helpfulness": 1.0},
        memes={"trust": 0.5},
    ))
    mystery = world.add(Entity(
        "mystery", "clue", case.clue,
        meters={"hidden": 1.0},
        memes={"importance": 1.0},
    ))

    world.facts.update(
        contestant=contestant,
        partner=partner,
        mystery=mystery,
        case=case,
        city=params.city,
        power=params.power,
    )

    world.say(
        f"In {params.city}, {params.name} entered the Young Heroes Contest with "
        f"{params.power}."
    )
    world.say(
        f"The prize was a chance to protect the city for one day, but {params.name} "
        f"knew that a true hero needed more than a dazzling power."
    )

    world.para()
    world.say(
        f"During the contest, {params.name} touched {case.clue}, and a flashback burst "
        f"across the room: {case.flashback}."
    )
    world.say(
        f"The memory revealed a mystery to solve: {case.mystery}."
    )
    world.say(
        f'"I found the first clue," said {params.name}. "Will you help me understand it?"'
    )
    world.say(
        f'"Of course," replied {case.teammate}. "A shared clue can travel farther than one hero."'
    )

    world.para()
    world.say(
        f"{params.name} shared the clue with {case.teammate} instead of keeping it for the contest."
    )
    contestant.meters["clues_shared"] = 1.0
    contestant.memes["trust"] = 1.0
    partner.memes["trust"] = 1.0
    world.say(
        f"{case.teammate} used {case.teammate_power}, while {params.name} {case.action}."
    )
    world.say(f"Then {case.danger}.")
    world.say(
        f'"The flashback shows another path!" called {case.teammate}. '
        f'"Let us use both clues."'
    )
    world.say(
        f"{params.name} listened, and together they discovered that {case.solution}."
    )
    mystery.meters["hidden"] = 0.0
    mystery.meters["solved"] = 1.0
    world.fired.add("mystery_solved")

    world.para()
    world.say(
        f"The judges had expected one contestant to claim the victory, but {params.name} "
        f"shared the answer and the credit."
    )
    world.say(case.shared_result)
    world.say(case.final_image)
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    hero: Entity = world.facts["contestant"]
    return [
        f"Write a superhero story about contestant {hero.label} solving this mystery: {case.mystery}.",
        f"Include a flashback showing {case.flashback}, followed by sharing clues with {world.facts['partner'].label}.",
        "Show how teamwork changes the result of a superhero contest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    hero: Entity = world.facts["contestant"]
    partner: Entity = world.facts["partner"]
    return [
        QAItem(
            "Who was the contestant in the story?",
            f"The contestant was {hero.label}, a young hero with {world.facts['power']}.",
        ),
        QAItem(
            "What did the flashback reveal?",
            f"The flashback showed {case.flashback}, which gave {hero.label} the first clue about the mystery.",
        ),
        QAItem(
            f"How did {hero.label} solve the mystery?",
            f"{hero.label} shared {case.clue} with {partner.label}; together they learned that {case.solution}.",
        ),
        QAItem(
            "Why was sharing important?",
            f"Sharing let both heroes combine their different clues and powers, so the danger was handled and the credit was shared too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a flashback?",
            "A flashback is a scene that shows something that happened earlier in a story.",
        ),
        QAItem(
            "What is a mystery to solve?",
            "A mystery to solve is a question or puzzling event whose answer must be discovered from clues.",
        ),
        QAItem(
            "Why can sharing help a team?",
            "Sharing clues, tools, and credit helps teammates combine their strengths and make better decisions.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    heroic = any(atom.name == "heroic" for atom in model)
    if not heroic:
        print("MISMATCH: ASP did not derive heroic.")
        return 1
    sample = generate(StoryParams("Luna", "starlight speed", "Brightbridge", seed=1))
    required = ["flashback", "mystery", "shared"]
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks a required narrative instrument.")
        return 1
    if "together" not in sample.story.lower():
        print("MISMATCH: generated story lacks a collaborative resolution.")
        return 1
    print("OK: ASP and Python agree; generated story exercises flashback, mystery, and sharing.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("heroic:", any(atom.name == "heroic" for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "starlight speed", "Brightbridge", base_seed),
            StoryParams("Maya", "echo hearing", "Cloudline City", base_seed + 1),
            StoryParams("Zara", "glowing maps", "Harbor Heights", base_seed + 2),
        ]
    else:
        params_list = []
        for index in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

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
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
