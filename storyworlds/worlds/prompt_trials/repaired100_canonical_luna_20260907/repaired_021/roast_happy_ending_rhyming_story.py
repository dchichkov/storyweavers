#!/usr/bin/env python3
"""
A small rhyming story world about a roast, a mistake, and a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    cook: str
    helper: str
    roast: str
    place: str = "the little kitchen"
    seed: Optional[int] = None


COOKS = ["Luna", "Milo", "Pip", "Nora", "Cora", "Bram"]
HELPERS = ["Poppy", "Toby", "Daisy", "Finn", "Mina", "Ollie"]
ROASTS = [
    ("carrot roast", "a golden carrot roast"),
    ("potato roast", "a warm potato roast"),
    ("apple roast", "a sweet apple roast"),
]
PLACES = ["the little kitchen", "the cozy cottage", "the bright village hall"]


@dataclass(frozen=True)
class Arc:
    title: str
    opening: str
    mistake: str
    trouble: str
    friend_line: str
    repair: str
    lesson: str
    ending: str


ARCS = (
    Arc(
        "the smoky surprise",
        "Luna stirred the roast with a hop and a rhyme, while Poppy set the table in excellent time.",
        "But Luna looked out at a bird in a tree, and forgot the small timer beside the tea.",
        "A smoky gray curl rose up through the air; the roast had grown dark, and the cooks stopped to stare.",
        '"Do not hide it," said Poppy. "We still have a chance. We can trim it and make a new plan for our dance."',
        "They scraped off the dark bits, added bright herbs, and warmed the good pieces with care.",
        "A mistake can feel big, but honest hands and helpful hearts can make a meal—and a friendship—better.",
        "They laughed as they served every bite with delight, and the moon watched their happy feast that night.",
    ),
    Arc(
        "the runaway tray",
        "Luna carried the roast on a tray through the room, while Poppy hummed a cheerful tune with a broom.",
        "Then one little slipper went slip-slip-slide, and the tray tipped gently to one side.",
        "The roast did not fall, but the sauce made a stream that ran to the door like a shiny gold dream.",
        '"We need not fuss," said Poppy. "Let us follow the flow. We can catch every drop before out it can go."',
        "They blocked the sauce with bread, wiped the floor clean, and placed the roast on a steadier stand.",
        "When friends share a problem, a spill can become a plan instead of a reason to blame.",
        "The roast reached the plates, and their bright laughter rang as warmly as bells in the band.",
    ),
    Arc(
        "the missing spice",
        "For the village supper, Luna made a roast with a fragrant, delicious design, while Poppy arranged napkins in a neat little line.",
        "But the pepper was missing, and Luna cried, 'Oh dear! Without it, the supper may not bring good cheer!'",
        "They searched every shelf, every basket, and chair, but found only a button and one purple pear.",
        '"Taste what we have," said Poppy. "A new flavor may grow. We can make this roast special in ways we know."',
        "They used herbs, apples, and a squeeze of lemon, then shared a small taste before serving.",
        "A missing ingredient does not end a good meal when people listen, experiment, and help.",
        "The guests cheered for the roast, and Luna learned that brave changes can make happy endings the most delicious kind.",
    ),
)


def choose_arc(seed: int) -> Arc:
    return ARCS[seed % len(ARCS)]


def build_world(params: StoryParams) -> World:
    if params.cook == params.helper:
        raise StoryError("The cook and helper must have different names.")
    if params.roast not in dict(ROASTS):
        raise StoryError(f"Unknown roast: {params.roast}.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")

    world = World()
    cook = world.add(
        Entity(
            id=params.cook,
            kind="character",
            type="cook",
            label="cook",
            traits=["cheerful", "careful"],
            meters={"energy": 1.0, "safety": 1.0},
            memes={"hope": 1.0, "pride": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="helper",
            label="helper",
            traits=["kind", "clever"],
            meters={"energy": 1.0, "safety": 1.0},
            memes={"care": 1.0, "trust": 1.0},
        )
    )
    roast = world.add(
        Entity(
            id="roast",
            kind="thing",
            type="food",
            label=params.roast,
            phrase=dict(ROASTS)[params.roast],
            owner=cook.id,
            meters={"warmth": 1.0, "goodness": 1.0},
            memes={"celebration": 1.0},
        )
    )
    arc = choose_arc(params.seed or 0)
    values = {
        "cook": cook.id,
        "helper": helper.id,
        "roast": roast.phrase,
        "place": params.place,
    }

    world.say(f"In {params.place}, {arc.opening.format(**values)}")
    world.say(
        f"{cook.id} wanted the {roast.label} to be perfect, but {helper.id} knew that a shared effort could make supper bright."
    )
    world.para()
    world.say(arc.mistake.format(**values))
    cook.memes["worry"] = 1.0
    roast.meters["goodness"] = 0.55
    world.say(arc.trouble.format(**values))
    helper.memes["worry"] = 0.5
    world.say(arc.friend_line.format(**values))
    world.para()
    world.say(f'"I was trying to make everything perfect," {cook.id} said. "Thank you for helping me try again."')
    world.say(arc.repair.format(**values))
    roast.meters["goodness"] = 1.0
    roast.meters["warmth"] = 1.0
    cook.memes["hope"] = 2.0
    cook.memes["gratitude"] = 1.0
    helper.memes["trust"] = 2.0
    world.say(arc.lesson.format(**values))
    world.para()
    world.say(arc.ending.format(**values))

    world.facts.update(
        cook=cook,
        helper=helper,
        roast=roast,
        place=params.place,
        arc=arc,
        trouble=arc.trouble.format(**values),
        friend_line=arc.friend_line.format(**values),
        repair=arc.repair.format(**values),
        ending=arc.ending.format(**values),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    cook: Entity = world.facts["cook"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    roast: Entity = world.facts["roast"]  # type: ignore[assignment]
    place = world.facts["place"]
    return [
        f"Write a child-friendly rhyming story about {cook.id} making {roast.phrase} in {place}.",
        f"Tell a rhyming story where {helper.id} helps {cook.id} rescue a roast after a cooking mistake.",
        "Create a short roast story with a problem, spoken dialogue, teamwork, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    cook: Entity = world.facts["cook"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    roast: Entity = world.facts["roast"]  # type: ignore[assignment]
    place = world.facts["place"]
    return [
        QAItem(
            question="Who made the roast?",
            answer=f"{cook.id} made {roast.phrase} in {place}, with help from {helper.id}.",
        ),
        QAItem(
            question=f"What went wrong for {cook.id}?",
            answer=str(world.facts["trouble"]),
        ),
        QAItem(
            question=f"What did {helper.id} say?",
            answer=f"{helper.id} encouraged {cook.id} not to hide the problem and suggested working together. {world.facts['friend_line']}",
        ),
        QAItem(
            question="How was the roast rescued?",
            answer=f"{world.facts['repair']} The friends worked carefully instead of blaming one another.",
        ),
        QAItem(
            question="How did the story end?",
            answer=str(world.facts["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a roast?",
            answer="A roast is food cooked with heat, often in an oven or over a fire, until it is warm and ready to eat.",
        ),
        QAItem(
            question="Why can teamwork help with a mistake?",
            answer="Teamwork helps because people can share ideas, divide tasks, and encourage one another while fixing the problem.",
        ),
        QAItem(
            question="What makes an ending happy?",
            answer="A happy ending shows that the characters are safe, connected, and better able to face life after the problem.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rhyming roast story world.")
    parser.add_argument("--cook")
    parser.add_argument("--helper")
    parser.add_argument("--roast", choices=[name for name, _ in ROASTS])
    parser.add_argument("--place", choices=PLACES)
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
    cook = args.cook or rng.choice(COOKS)
    helper_choices = [name for name in HELPERS if name != cook]
    helper = args.helper or rng.choice(helper_choices)
    roast = args.roast or rng.choice([name for name, _ in ROASTS])
    place = args.place or rng.choice(PLACES)
    return StoryParams(cook=cook, helper=helper, roast=roast, place=place)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        if entity.owner:
            details.append(f"owner={entity.owner}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) {' '.join(details)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
food(roast).
problem(roast).
helper(h).
honest(h).
repairs(h, roast).
happy_ending(roast) :- problem(roast), helper(h), honest(h), repairs(h, roast).
#show happy_ending/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("food", "roast"),
            asp.fact("problem", "roast"),
            asp.fact("helper", "h"),
            asp.fact("honest", "h"),
            asp.fact("repairs", "h", "roast"),
        ]
    )


def asp_program(show: str = "#show happy_ending/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    try:
        model = asp.one_model(asp_program())
        endings = asp.atoms(model, "happy_ending")
        if ("roast",) not in endings:
            print("ASP verification failed: no happy ending.")
            return 1
        sample = generate(
            StoryParams(
                cook="Luna",
                helper="Poppy",
                roast="carrot roast",
                place="the little kitchen",
                seed=0,
            )
        )
        if "happy" not in sample.story.lower() or not sample.story_qa:
            print("ASP verification failed: generated story check failed.")
            return 1
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1
    print("OK: ASP/Python parity and generated story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp
        print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, roast in enumerate(ROASTS):
            params = StoryParams(
                cook=COOKS[index % len(COOKS)],
                helper=HELPERS[index % len(HELPERS)],
                roast=roast[0],
                place=PLACES[index % len(PLACES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
