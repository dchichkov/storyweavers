#!/usr/bin/env python3
"""
A tiny heartwarming storyworld about a glamorous surprise.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Mara"
    celebration: str = "the Moonlight Parade"
    gift: str = "a silver cape"
    scenario_id: int = 0
    telling_mode: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


CHILDREN = ["Luna", "Nia", "Pip", "Milo", "Sora", "Tavi"]
HELPERS = ["Mara", "Jo", "Ari", "Bea", "Sol"]
CELEBRATIONS = [
    "the Moonlight Parade",
    "the Lantern Garden Party",
    "the Little Star Fair",
    "the Rainbow Theater Night",
]
GIFTS = [
    "a silver cape",
    "a crown of paper stars",
    "a velvet dancing jacket",
    "a pair of glittering shoes",
]

SCENARIOS = [
    {
        "opening": "Luna believed the old community hall looked too plain for the evening celebration",
        "secret": "Mara and the neighbors had been sewing bright scraps into a glamorous curtain behind the closed stage",
        "clue": "a single gold thread peeked from beneath the door",
        "worry": "Luna might feel forgotten when everyone else hurried away from her",
        "dialogue": (
            '"Why is everyone whispering?" Luna asked. '
            '"Because some good things need a little quiet first," Mara replied.'
        ),
        "reveal": "the curtain opened to reveal a sparkling welcome sign made from hundreds of kind notes",
        "change": "Luna stopped measuring beauty by shiny things and saw how every careful note carried love",
        "ending": "the glamorous curtain shimmered while neighbors hugged beneath it",
    },
    {
        "opening": "Luna practiced a simple dance beside the bakery, certain she was not special enough for the celebration",
        "secret": "Mara had asked each shopkeeper to add one tiny ribbon to a costume made just for Luna",
        "clue": "ribbons appeared everywhere, even on the baker's flour sack",
        "worry": "Luna would hide at the back instead of joining the parade",
        "dialogue": (
            '"I think the parade has no place for me," Luna said. '
            '"Then we will make a place together," Mara answered.'
        ),
        "reveal": "a glamorous costume appeared, stitched from ribbons that represented all the people who cared for her",
        "change": "Luna understood that belonging was something a community could build with many small acts",
        "ending": "Luna led the parade, and every ribbon danced in the warm evening breeze",
    },
    {
        "opening": "Luna polished the hall windows while the town prepared for a glamorous music night",
        "secret": "the musicians were practicing a song whose melody Luna had hummed while helping others",
        "clue": "the same little tune floated from behind every locked door",
        "worry": "Luna thought her quiet work would go unnoticed",
        "dialogue": (
            '"Nobody hears my small song," Luna said. '
            '"We have heard it all along," Mara replied.'
        ),
        "reveal": "the band played Luna's melody as the lights rose around her",
        "change": "Luna learned that a gentle contribution can travel farther than its maker expects",
        "ending": "the whole hall sang softly together beneath a ceiling of golden lights",
    },
    {
        "opening": "Luna carried chairs into the garden and wondered why the celebration decorations were still hidden",
        "secret": "the children had turned an empty corner into a glamorous story nook filled with cushions and painted stars",
        "clue": "blue paint dotted the path like a trail of tiny planets",
        "worry": "Luna might think her favorite stories were too ordinary to share",
        "dialogue": (
            '"My stories are only little stories," Luna said. '
            '"Little stories can hold very big hearts," Mara told her.'
        ),
        "reveal": "the story nook was dedicated to Luna, with a sign inviting everyone to hear her favorite tale",
        "change": "Luna discovered that sharing what she loved could make strangers feel like friends",
        "ending": "children listened close as Luna read beneath a glamorous arch of painted stars",
    },
]

REFLECTIONS = [
    "The brightest surprise was not the sparkle; it was knowing she had been noticed.",
    "Warm hearts can make ordinary materials feel more beautiful than jewels.",
    "A surprise becomes truly special when it helps someone see their own worth.",
    "Love often arrives through many small hands, each carrying one shining piece.",
]

WORLD_KNOWLEDGE = [
    QAItem(
        question="What does glamorous mean?",
        answer="Glamorous means especially beautiful, exciting, or sparkling in a way that attracts attention.",
    ),
    QAItem(
        question="What is a surprise?",
        answer="A surprise is something unexpected that happens or is revealed to someone.",
    ),
    QAItem(
        question="Why can a small gift feel important?",
        answer="A small gift can feel important when it shows that someone paid attention and cared.",
    ),
    QAItem(
        question="What makes a story heartwarming?",
        answer="A heartwarming story shows kindness, belonging, or love bringing comfort and happiness.",
    ),
]

ASP_RULES = r"""
glamorous(gift).
kind(helper).
needs_surprise(child).
prepared(helper, gift).
prepared(helper, celebration).
can_delight(child) :- needs_surprise(child), prepared(helper, gift), prepared(helper, celebration).
valid_story :- glamorous(gift), kind(helper), can_delight(child).
#show valid_story/0.
"""


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    child = Entity(
        "child",
        "character",
        "girl",
        params.child_name,
        traits=["kind", "thoughtful"],
        meters={"confidence": 0.35, "joy": 0.25},
        memes={"belonging": 0.35, "hope": 0.45},
    )
    helper = Entity(
        "helper",
        "character",
        "woman",
        params.helper_name,
        traits=["patient", "creative"],
        meters={"care": 1.0},
        memes={"love": 1.0},
    )
    gift = Entity(
        "gift",
        "object",
        "present",
        params.gift,
        traits=["glamorous", "handmade"],
        meters={"sparkle": 1.0},
        memes={"meaning": 1.0},
    )
    world = World()
    world.add(child)
    world.add(helper)
    world.add(gift)

    openings = [
        f"In a friendly little town, {child.label} helped prepare for {params.celebration}.",
        f"The town was getting ready for {params.celebration}, and {child.label} was busy making everything shine.",
        f"On the morning of {params.celebration}, {child.label} found plenty of work and very little attention.",
    ]
    world.say(openings[params.telling_mode % len(openings)])
    world.say(f"{scenario['opening'].capitalize()}.")
    world.say(f"{helper.label} smiled kindly, but kept one hand behind her back. {scenario['secret'].capitalize()}.")
    world.say(f"{scenario['clue'].capitalize()}.")
    world.say(f"{scenario['worry'].capitalize()}.")

    world.para()
    world.say(scenario["dialogue"])
    world.say(
        f"{child.label} followed the clue while {helper.label} and the neighbors "
        "tried very hard not to grin."
    )
    world.say(f"Then came the surprise: {scenario['reveal'].capitalize()}.")
    world.say(
        f"The handmade {params.gift} was glamorous, but the loving details mattered even more."
    )

    child.meters["confidence"] += 0.65
    child.meters["joy"] += 0.75
    child.memes["belonging"] += 0.65
    child.memes["hope"] += 0.45

    world.para()
    world.say(f"{child.label} touched the gift and laughed with happy surprise.")
    world.say(f"{scenario['change'].capitalize()}.")
    world.say(f"{helper.label} said, \"You helped make this town brighter just by being you.\"")
    world.say(f"{child.label} answered, \"Then I will share the brightness too.\"")
    world.say(REFLECTIONS[(params.scenario_id + params.telling_mode) % len(REFLECTIONS)])
    world.say(f"At the end of {params.celebration}, {scenario['ending']}.")

    world.facts.update(
        child=child,
        helper=helper,
        gift=gift,
        scenario=scenario,
        celebration=params.celebration,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a heartwarming story about {facts['child'].label} receiving a glamorous surprise.",
        f"Tell a child-friendly story set during {facts['celebration']} where kindness changes a character's confidence.",
        f"Create a gentle surprise story involving a handmade {facts['gift'].label} and a caring helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"]
    helper = facts["helper"]
    scenario = facts["scenario"]
    gift = facts["gift"]
    return [
        QAItem(
            question=f"What surprise did {child.label} receive?",
            answer=f"{child.label} received {gift.label}, prepared with loving details by {helper.label} and the neighbors.",
        ),
        QAItem(
            question="What clue helped reveal the surprise?",
            answer=f"The clue was that {scenario['clue']}. It led toward the hidden preparation.",
        ),
        QAItem(
            question=f"How did {child.label} change?",
            answer=f"{child.label} learned that {scenario['change']}. The surprise helped the child feel valued and included.",
        ),
        QAItem(
            question="Why was the gift more than merely glamorous?",
            answer=f"The gift was glamorous because it looked beautiful, but it mattered because many people made it carefully to show love.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"At the end, {scenario['ending']}. The image showed that the surprise brought the community together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("glamorous", "gift"),
            asp.fact("kind", "helper"),
            asp.fact("needs_surprise", "child"),
            asp.fact("prepared", "helper", "gift"),
            asp.fact("prepared", "helper", "celebration"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> None:
    if not params.child_name.strip():
        raise StoryError("The child needs a name.")
    if not params.helper_name.strip():
        raise StoryError("The helper needs a name.")
    if params.child_name == params.helper_name:
        raise StoryError("The child and helper must have different names.")
    if not params.gift.strip():
        raise StoryError("The surprise needs a gift.")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid_story"):
        for params in [
            StoryParams(),
            StoryParams(scenario_id=2, telling_mode=1),
        ]:
            python_reasonable(params)
            sample = generate(params)
            if not sample.story or "surprise" not in sample.story.lower():
                print("MISMATCH: generated story failed its surprise check.")
                return 1
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print("MISMATCH: ASP did not find a valid story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming storyworld about a glamorous surprise."
    )
    parser.add_argument("--child-name", choices=CHILDREN)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--celebration", choices=CELEBRATIONS)
    parser.add_argument("--gift", choices=GIFTS)
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
    params = StoryParams(
        child_name=args.child_name or rng.choice(CHILDREN),
        helper_name=args.helper_name or rng.choice(HELPERS),
        celebration=args.celebration or rng.choice(CELEBRATIONS),
        gift=args.gift or rng.choice(GIFTS),
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(6),
    )
    python_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    python_reasonable(params)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:7} ({entity.type:7}) "
            f"meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


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
    StoryParams(child_name="Luna", helper_name="Mara", celebration=CELEBRATIONS[0], gift=GIFTS[0]),
    StoryParams(child_name="Nia", helper_name="Jo", celebration=CELEBRATIONS[1], gift=GIFTS[1], scenario_id=1),
    StoryParams(child_name="Milo", helper_name="Bea", celebration=CELEBRATIONS[2], gift=GIFTS[2], scenario_id=2),
    StoryParams(child_name="Sora", helper_name="Ari", celebration=CELEBRATIONS[3], gift=GIFTS[3], scenario_id=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("valid story:", bool(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
