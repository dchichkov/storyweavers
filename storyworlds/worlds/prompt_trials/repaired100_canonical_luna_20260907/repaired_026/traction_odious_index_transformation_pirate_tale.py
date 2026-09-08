#!/usr/bin/env python3
"""
A tiny pirate tale about traction, an odious index, and a transformation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here)))))
if os.path.exists(os.path.join(_root, "storyworlds", "results.py")):
    sys.path.insert(0, os.path.join(_root, "storyworlds"))
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    place: str
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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Captain Luna"
    deckhand: str = "Pip"
    place: str = "the slippery deck of the Sea Finch"
    cargo: str = "the old treasure index"


CAPTAIN_NAMES = ["Captain Luna", "Captain Maris", "Captain Sol", "Captain Nera"]
DECKHAND_NAMES = ["Pip", "Tavi", "Moss", "Rin"]
PLACES = [
    "the slippery deck of the Sea Finch",
    "the rain-dark deck of the Moon Minnow",
    "the wind-bent deck of the Starling",
]
CARGO_NAMES = [
    "the old treasure index",
    "the captain's island index",
    "the salt-stained treasure index",
]


ARCS = [
    {
        "island": "Cinder Key",
        "problem": "a burst of rain had made the deck slick",
        "odious": "an odious blob of tar",
        "plan": "rub the tar beneath the index so it would stick to the table",
        "harm": "the tar could stain the pages and make the index impossible to open",
        "tool": "a coil of rough rope",
        "action": "looped the rope around the table legs and laid a dry sailcloth beneath the index",
        "change": "the loose table became steady, and the tar was scraped into a sealed tin",
        "ending": "the index opened safely while the ship sailed toward Cinder Key",
    },
    {
        "island": "Whisper Reef",
        "problem": "the ship was pitching hard beside a sudden reef",
        "odious": "an odious smear of fish oil",
        "plan": "spread the oil on the cover and pretend the index had always belonged to the cabin floor",
        "harm": "the oil could make the book slide overboard and ruin its marked pages",
        "tool": "a pair of brass clamps",
        "action": "clamped the reading board to the rail and tucked the index inside a dry chart case",
        "change": "the chart case held firm, and the fish oil was washed from the deck",
        "ending": "the index guided the crew through the reef as gulls cried above the wake",
    },
    {
        "island": "Lantern Isle",
        "problem": "a gust had sent maps and mugs skittering across the deck",
        "odious": "an odious puddle of sticky molasses",
        "plan": "press the index into the molasses and claim it was a new treasure map",
        "harm": "the sweet mess would glue pages together and hide the real route",
        "tool": "a wooden book cradle",
        "action": "placed the index in the cradle and weighed the cradle with two clean cannonballs",
        "change": "the pages stayed open, while the molasses was carried below for the cook",
        "ending": "the index shone under the lantern as the crew found Lantern Isle",
    },
    {
        "island": "Blue Heron Bay",
        "problem": "the deck boards had lost their traction after a night of spray",
        "odious": "an odious smear of black paint",
        "plan": "paint a false mark across the index and hide it beneath a loose board",
        "harm": "the paint would cover the owner's notes and the loose board could swallow the book",
        "tool": "sand, wax, and a bright red flag",
        "action": "scattered sand for traction, waxed the board edges, and raised the red flag to warn the crew",
        "change": "the deck grew safe underfoot, and the clean index was returned to the captain's chest",
        "ending": "the red flag snapped proudly while the index rested dry beside the ship's compass",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a pirate tale about traction, an odious plan, and transformation."
    )
    parser.add_argument("--captain")
    parser.add_argument("--deckhand")
    parser.add_argument("--place")
    parser.add_argument("--cargo")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    deckhand = args.deckhand or rng.choice([n for n in DECKHAND_NAMES if n != captain])
    place = args.place or rng.choice(PLACES)
    cargo = args.cargo or rng.choice(CARGO_NAMES)
    if captain.strip().lower() == deckhand.strip().lower():
        raise StoryError("The captain and deckhand must have different names.")
    if not place.strip():
        raise StoryError("The ship's place cannot be empty.")
    if not cargo.strip():
        raise StoryError("The cargo must have a name.")
    return StoryParams(
        seed=args.seed,
        captain=captain,
        deckhand=deckhand,
        place=place,
        cargo=cargo,
    )


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    world.add(
        Entity(
            "captain",
            "character",
            params.captain,
            meters={"balance": 0.7, "safety": 0.8},
            memes={"trust": 0.5, "worry": 0.2},
        )
    )
    world.add(
        Entity(
            "deckhand",
            "character",
            params.deckhand,
            meters={"balance": 0.5, "traction": 0.2},
            memes={"curiosity": 0.8, "shame": 0.0},
        )
    )
    world.add(
        Entity(
            "index",
            "book",
            params.cargo,
            meters={"dryness": 0.8, "traction": 0.1, "legibility": 1.0},
            memes={"importance": 1.0},
            owner="captain",
        )
    )
    world.facts.update(
        captain=params.captain,
        deckhand=params.deckhand,
        index=params.cargo,
        place=params.place,
    )
    return world


def tell(params: StoryParams) -> World:
    rng = random.Random((params.seed if params.seed is not None else 17) ^ 0xA71CE)
    arc = rng.choice(ARCS)
    world = make_world(params)
    captain = params.captain
    deckhand = params.deckhand

    index = world.entities["index"]
    index.meters["traction"] = 0.05
    index.meters["safety"] = 0.3
    index.meters["legibility"] = 0.75
    world.facts.update(
        island=arc["island"],
        problem=arc["problem"],
        odious=arc["odious"],
        plan=arc["plan"],
        harm=arc["harm"],
        tool=arc["tool"],
        action=arc["action"],
        change=arc["change"],
        ending=arc["ending"],
        transformed=True,
    )

    openings = [
        f"At dawn, {captain} guided the ship across {arc['island']} while {arc['problem']} on {params.place}.",
        f"The Sea Finch rolled toward {arc['island']}; on {params.place}, {arc['problem']}.",
        f"Pirates fear storms, reefs, and poor footing. That morning, near {arc['island']}, {arc['problem']}.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"The captain had brought {params.cargo}, an index filled with routes, shoals, and safe places to anchor."
    )
    world.say(
        f"{deckhand} spotted {arc['odious']} beside the chart table and whispered, "
        f'"Captain, we could {arc["plan"]}."'
    )
    world.say(f"The idea sounded clever for one second, but {arc['harm']}.")
    world.para()
    world.say(
        f'{captain} shook their head. "No odious trick with a book that guides our crew. '
        f"Tell me what the deck needs instead.\""
    )
    world.say(
        f'"It needs traction," {deckhand} answered. "And the index needs a safe place to rest."'
    )
    world.say(
        f"{captain} nodded. Together they used {arc['tool']} and chose a safer course."
    )
    world.say(f"Then {deckhand} {arc['action']}.")
    world.say(f"{arc['change']}.")
    world.para()
    world.say(
        f"The transformation was plain: the slippery danger became a steady working deck, "
        f"and the tempting trick became an honest repair."
    )
    world.say(
        f'"You changed the whole problem," {captain} said. "You found traction instead of trouble."'
    )
    world.say(
        f'"And I learned that an index is for finding the way, not for hiding a lie," '
        f"{deckhand} replied."
    )
    world.say(f"By sunset, {arc['ending']}.")
    world.say(
        f"{captain} placed one hand on the dry cover. \"A true pirate protects the route and the crew.\""
    )

    index.meters.update(
        traction=0.95,
        safety=1.0,
        dryness=1.0,
        legibility=1.0,
    )
    index.memes["importance"] = 1.0
    world.entities["deckhand"].meters["traction"] = 1.0
    world.entities["deckhand"].memes.update(shame=0.1, pride=0.8)
    world.entities["captain"].memes["trust"] = 1.0
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly Pirate Tale set on {f['place']} where traction saves {f['index']}.",
        f"Tell a pirate story in which {f['deckhand']} rejects an odious plan involving {f['index']} and transforms danger into a repair.",
        f"Write a short Transformation tale using the words traction, odious, and index.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What problem did the pirates face near {f['island']}?",
            f"They faced {f['problem']}, which made the deck and the treasure index unsafe.",
        ),
        QAItem(
            f"What odious plan did {f['deckhand']} suggest?",
            f"{f['deckhand']} suggested that they {f['plan']}.",
        ),
        QAItem(
            "Why was the plan dangerous?",
            f"It was dangerous because {f['harm']}.",
        ),
        QAItem(
            f"How did {f['deckhand']} transform the problem?",
            f"{f['deckhand']} {f['action']}. Then {f['change']}.",
        ),
        QAItem(
            "What showed that the transformation worked?",
            f"At the end, {f['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is traction?",
            "Traction is the grip that helps feet, wheels, or objects avoid sliding.",
        ),
        QAItem(
            "What does odious mean?",
            "Odious means very unpleasant, hateful, or deserving strong dislike.",
        ),
        QAItem(
            "What is an index?",
            "An index is a list or guide that helps someone find information or places.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a change that turns something into a different or improved form.",
        ),
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
        meters = {k: round(v, 3) for k, v in entity.meters.items()}
        memes = {k: round(v, 3) for k, v in entity.memes.items()}
        owner = f" owner={entity.owner}" if entity.owner else ""
        lines.append(
            f"  {entity.id}: {entity.kind} {entity.label!r}{owner} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
safe_index(I) :- index(I), traction(I,T), T >= 0.9, legible(I).
transformed(I) :- index(I), safe_index(I), dry(I).
honest_choice(D) :- deckhand(D), transformed(I), index(I).
#show safe_index/1.
#show transformed/1.
#show honest_choice/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("deckhand", "deckhand"),
            asp.fact("index", "index"),
            asp.fact("traction", "index", 1),
            asp.fact("dry", "index"),
            asp.fact("legible", "index"),
        ]
    )


def asp_program() -> str:
    return f"""
{asp_facts()}
{ASP_RULES}
"""


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        names = {symbol.name for symbol in model}
        expected = {"safe_index", "transformed", "honest_choice"}
        if expected.issubset(names):
            sample = generate(StoryParams(seed=11))
            if not all(word in sample.story.lower() for word in ("traction", "odious", "index")):
                raise StoryError("Generated story omitted a required seed word.")
            print("OK: ASP parity and generated-story checks passed.")
            return 0
        print("MISMATCH: ASP did not derive the expected transformed state.")
        return 1
    except ImportError:
        sample = generate(StoryParams(seed=11))
        if all(word in sample.story.lower() for word in ("traction", "odious", "index")):
            print("OK: Python gate passed; clingo is unavailable for the ASP half.")
            return 0
        print("MISMATCH: generated story omitted a required seed word.")
        return 1


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        seed=101,
        captain="Captain Luna",
        deckhand="Pip",
        place="the slippery deck of the Sea Finch",
        cargo="the old treasure index",
    ),
    StoryParams(
        seed=202,
        captain="Captain Maris",
        deckhand="Tavi",
        place="the rain-dark deck of the Moon Minnow",
        cargo="the salt-stained treasure index",
    ),
    StoryParams(
        seed=303,
        captain="Captain Sol",
        deckhand="Moss",
        place="the wind-bent deck of the Starling",
        cargo="the captain's island index",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            import storyworlds.asp as asp

            print("ASP atoms:")
            for symbol in asp.one_model(asp_program()):
                print(symbol)
        except ImportError:
            print("ASP mode requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            request = argparse.Namespace(
                captain=args.captain,
                deckhand=args.deckhand,
                place=args.place,
                cargo=args.cargo,
                seed=seed,
            )
            params = resolve_params(request, rng)
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

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
