#!/usr/bin/env python3
"""
A small cautionary whodunit about Rut, whose bravery becomes useful only when
paired with careful observation.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "visibility", "security", "noise"):
            self.meters.setdefault(key, 0.0)
        for key in ("bravery", "caution", "worry", "trust", "relief", "curiosity"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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
    seed: Optional[int] = None
    detective: str = "Luna"
    partner: str = "Mara"
    place: str = "Moonlit Library"
    missing_item: str = "silver bookmark"
    culprit: str = "the draft"
    bravery: bool = True
    cautionary: bool = True


NAMES = ["Luna", "Nia", "Tavi", "Mina", "Oren", "Suri"]
PARTNERS = ["Mara", "Theo", "Pip", "Iris", "Jules"]
PLACES = [
    "Moonlit Library",
    "Rainy Museum",
    "Clockwork Garden",
    "Old Harbor Station",
]
ITEMS = [
    ("silver bookmark", "a silver bookmark"),
    ("blue music box key", "a blue music box key"),
    ("brass theater bell", "a brass theater bell"),
    ("painted compass", "a painted compass"),
]

CASES = [
    {
        "opening": "The reading room was ready for its evening mystery game when the display case clicked open.",
        "clue": "a thin line of dust stopped at the window latch",
        "false": "the muddy paw print beside the case",
        "truth": "the window had been opened just enough for a gust to lift the item from its velvet stand",
        "danger": "a loose stack of atlases leaned toward the dark stairwell",
        "action": "braced the atlases, closed the window gently, and followed the silver gleam beneath a reading table",
        "ending": "the silver bookmark rested safely between two pages about winter stars",
        "lesson": "Bravery is strongest when it pauses to notice who might be harmed.",
    },
    {
        "opening": "At the Rainy Museum, a tiny alarm chimed before the doors opened.",
        "clue": "three dry drops formed a neat trail from the umbrella rack to the model train",
        "false": "a visitor's red scarf caught on the display rope",
        "truth": "water from a folded umbrella had slipped under the platform and nudged the key away",
        "danger": "the wet floor reached the model train's bright electrical wires",
        "action": "stood guard, warned the visitors, and used a cloth to guide the key away from the wires",
        "ending": "the blue key was found beside a dry ticket stub",
        "lesson": "A brave detective protects people before chasing a dramatic answer.",
    },
    {
        "opening": "The Clockwork Garden's noon bell refused to ring, and the gardener found the brass bell missing.",
        "clue": "a row of bent daisies pointed toward the hedge, while every footprint stopped before the pond",
        "false": "the fox-shaped garden statue seemed to have moved",
        "truth": "a gust had rolled the bell along the hedge, where the daisies had brushed its path",
        "danger": "the bell lay beside a deep pond hidden by tall reeds",
        "action": "tied a bright ribbon to a rake, reached from firm ground, and pulled the bell back without stepping into the reeds",
        "ending": "the brass bell rang over the garden, and the bent daisies stood quiet again",
        "lesson": "Caution does not shrink bravery; it gives bravery a safe direction.",
    },
    {
        "opening": "At Old Harbor Station, the last clock gave a soft cough and lost its painted compass.",
        "clue": "a thread of blue wool hung from the luggage cart, but the cart's wheel marks led away from the clock",
        "false": "the station cat stared at the clock with suspicious yellow eyes",
        "truth": "the compass had slipped into the cart's canvas fold when the clock keeper moved the luggage",
        "danger": "the cart stood at the edge of a platform where a night train was due",
        "action": "called for the keeper, blocked the cart with a lantern, and checked the canvas fold before the train arrived",
        "ending": "the painted compass returned to the clock, pointing north beneath the station lamp",
        "lesson": "A calm question can solve what a hurried accusation would only tangle.",
    },
]


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    detective = world.add(
        Entity(
            "detective",
            "character",
            params.detective,
            "child_detective",
            memes={"bravery": 1.0, "curiosity": 1.0},
        )
    )
    partner = world.add(
        Entity(
            "partner",
            "character",
            params.partner,
            "helper",
            memes={"caution": 1.0, "trust": 1.0},
        )
    )
    item = world.add(
        Entity(
            "missing",
            "object",
            params.missing_item,
            "clue_object",
            meters={"security": 1.0},
        )
    )
    detective.memes["caution"] = 1.0
    partner.memes["caution"] = 1.0
    world.facts.update(
        detective=detective,
        partner=partner,
        item=item,
        params=params,
    )
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    detective: Entity = world.facts["detective"]
    partner: Entity = world.facts["partner"]
    item: Entity = world.facts["item"]

    variant = params.seed if params.seed is not None else sum(
        ord(c) for c in f"{params.detective}|{params.partner}|{params.place}|{params.missing_item}"
    )
    case = CASES[variant % len(CASES)]

    world.say(
        f"In the {params.place}, {detective.label} worked as a young detective with "
        f"{partner.label}, the most careful helper in town."
    )
    world.say(case["opening"])
    world.say(f"The missing object was {item.label}, and the room held its breath.")
    world.para()

    world.say(
        f"{detective.label} pointed toward {case['false']}. "
        f"\"That looks suspicious,\" {detective.label} said."
    )
    world.say(
        f"\"It may be a clue,\" {partner.label} replied, \"but let us look for what it changed.\""
    )
    world.say(f"They noticed {case['clue']}.")
    detective.memes["curiosity"] += 1.0
    detective.memes["worry"] += 1.0

    world.say(
        f"{detective.label} wanted to rush after the first suspect, but {partner.label} "
        f"asked for one quiet breath. The real clue was that {case['truth']}."
    )
    world.say(f"Then they saw the next danger: {case['danger']}.")
    detective.meters["visibility"] = 1.0
    detective.memes["bravery"] += 1.0
    partner.memes["caution"] += 1.0
    world.para()

    world.say(
        f"\"I can go first,\" said {detective.label}. \"But I will go carefully.\" "
        f"\"And I will watch the safe path,\" said {partner.label}."
    )
    world.say(f"Together, they {case['action']}.")
    world.say(
        f"The mystery was solved without blaming anyone: {case['truth'].capitalize()}."
    )
    item.meters["security"] = 1.0
    detective.memes["relief"] += 1.0
    partner.memes["relief"] += 1.0
    detective.memes["trust"] += 1.0

    world.para()
    world.say(f"At last, {case['ending']}.")
    world.say(
        f"{partner.label} smiled at {detective.label}. \"Your bravery helped us move,\" "
        f"{partner.label} said. \"Your caution helped us move safely,\" answered {detective.label}."
    )
    world.say(f"{detective.label} learned that {case['lesson']}")
    world.say(
        f"The false clue was left where it belonged, while {item.label} returned to its case."
    )

    world.facts.update(
        case=case,
        resolved=True,
        clue=case["clue"],
        false_clue=case["false"],
        truth=case["truth"],
        danger=case["danger"],
        action=case["action"],
        ending=case["ending"],
        lesson=case["lesson"],
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    detective: Entity = world.facts["detective"]
    partner: Entity = world.facts["partner"]
    item: Entity = world.facts["item"]
    case = world.facts["case"]
    return [
        QAItem(
            f"Who investigated the missing {item.label} in the {params.place}?",
            f"{detective.label} investigated it with help from {partner.label}. They solved the mystery by observing clues instead of rushing to accuse someone.",
        ),
        QAItem(
            f"What first seemed suspicious during the search for the {item.label}?",
            f"{case['false'].capitalize()} seemed suspicious at first, but it was a false clue rather than proof that anyone had taken the item.",
        ),
        QAItem(
            f"What real clue helped explain where the {item.label} went?",
            f"They noticed that {case['clue']}. This clue showed how the item had moved, rather than merely making someone look guilty.",
        ),
        QAItem(
            f"What danger did the detectives face while solving the case?",
            f"They discovered that {case['danger']}. They had to protect the area before reaching for the missing item.",
        ),
        QAItem(
            f"How did {detective.label} and {partner.label} recover the {item.label}?",
            f"They {case['action']}. Their shared plan used {detective.label}'s bravery with {partner.label}'s caution.",
        ),
        QAItem(
            f"What lesson did {detective.label} learn from the cautionary mystery?",
            f"{case['lesson']} The case showed that brave action works best when it follows careful observation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a whodunit?",
            "A whodunit is a mystery story in which characters gather clues to discover who caused an event.",
        ),
        QAItem(
            "Why should a detective check a clue before accusing someone?",
            "A detective should check a clue because something that looks suspicious may have an innocent explanation.",
        ),
        QAItem(
            "What does bravery mean?",
            "Bravery means facing a difficult or frightening situation and doing what is helpful despite fear.",
        ),
        QAItem(
            "What does caution mean?",
            "Caution means thinking about danger and choosing a careful way to act.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a cautionary whodunit about {params.detective} investigating a missing {params.missing_item} in the {params.place}.",
        f"Tell a child-friendly mystery where the false clue is {case['false']} but the real clue is that {case['clue']}.",
        f"Show how bravery and caution help {params.detective} and {params.partner} solve a mystery without blaming the wrong person.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:14}) "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A careful mystery begins with a clue and a false suspicion.
investigates(luna) :- has_clue(luna), checks_false_clue(luna).

% Bravery is useful when it is joined to caution.
brave_action(luna) :- brave(luna), cautious(luna), danger_present.

% The missing object is recovered when the detective follows the real clue.
solved(luna) :- investigates(luna), brave_action(luna), follows_real_clue(luna).

#show investigates/1.
#show brave_action/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("has_clue", "luna"),
            asp.fact("checks_false_clue", "luna"),
            asp.fact("brave", "luna"),
            asp.fact("cautious", "luna"),
            asp.fact("danger_present"),
            asp.fact("follows_real_clue", "luna"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"investigates/1", "brave_action/1", "solved/1"}
    if found == expected:
        print("OK: ASP twin matches the bravery-and-caution mystery logic.")
        return 0
    print("MISMATCH:", sorted(found), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary whodunit about bravery, caution, and a missing object."
    )
    parser.add_argument("--detective", choices=NAMES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--missing-item", choices=[item[0] for item in ITEMS])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        detective=args.detective or rng.choice(NAMES),
        partner=args.partner or rng.choice(PARTNERS),
        place=args.place or rng.choice(PLACES),
        missing_item=args.missing_item or rng.choice([item[0] for item in ITEMS]),
        bravery=True,
        cautionary=True,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(
        name if False else None
    )
]

CURATED = [
    StoryParams(
        detective="Luna",
        partner="Mara",
        place="Moonlit Library",
        missing_item="silver bookmark",
    ),
    StoryParams(
        detective="Nia",
        partner="Theo",
        place="Rainy Museum",
        missing_item="blue music box key",
    ),
    StoryParams(
        detective="Tavi",
        partner="Iris",
        place="Clockwork Garden",
        missing_item="brass theater bell",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(" ".join(str(symbol) for symbol in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
