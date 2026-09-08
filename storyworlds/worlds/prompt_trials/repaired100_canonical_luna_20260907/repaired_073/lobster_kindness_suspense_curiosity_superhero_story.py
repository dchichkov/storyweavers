#!/usr/bin/env python3
"""
A tiny superhero storyworld about a curious child, a lobster in trouble, and
kindness that proves stronger than a flashy rescue.

The story takes place at a seaside pier. A lobster's basket has slipped beneath
the dock during a storm, and a rising tide creates suspense. Curiosity reveals
the safe way to help, while kindness lets the child call an adult rescuer
instead of rushing into danger.
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


PLACES = {
    "moonlit_pier": {
        "name": "Moonlit Pier",
        "detail": "The pier creaked above dark water, and silver waves curled around its posts.",
    },
    "harbor_steps": {
        "name": "Harbor Steps",
        "detail": "The harbor steps shone with rain, while boats rocked gently beside the stone wall.",
    },
}

HERO_NAMES = ["Luna", "Milo", "Tessa", "Arlo", "Nia", "Finn"]
GENDERS = {"Luna": "girl", "Milo": "boy", "Tessa": "girl", "Arlo": "boy", "Nia": "girl", "Finn": "boy"}
ADULTS = ["Aunt Bea", "Uncle Sol", "Mom", "Dad"]
TRAITS = ["curious", "brave", "gentle", "quick-thinking", "cheerful"]

INCIDENTS = [
    {
        "title": "the swinging basket",
        "arrival": "A storm gust swung a fisher's basket against a lower pier post.",
        "problem": "Inside, a small lobster clicked its claws while the tide rose beneath the boards.",
        "clue": "Luna noticed that the basket's rope was caught on a smooth hook, not broken.",
        "plan": "The harbor keeper lowered a long boat hook from the safe walkway while Luna held a lantern and called out when the rope loosened.",
        "villain": "The tide slapped the pilings like a grumpy sea monster.",
        "line_hero": "A real hero does not leap first. A real hero looks, asks, and helps safely.",
        "line_adult": "That is exactly the kind of courage the harbor needs.",
        "result": "The keeper lifted the basket onto the pier, and the lobster crawled into a fresh seawater tub.",
        "ending": "When the moon came out, the lobster waved one tiny claw from its tub as if saluting the newest harbor hero.",
        "lesson": "kindness means protecting a living creature while using careful help",
        "object": "a lobster basket",
    },
    {
        "title": "the shadow under the dock",
        "arrival": "A fisherman heard tapping under the dock after the rainstorm.",
        "problem": "A lobster was trapped between two loose boards, and nobody could tell whether the boards might shift.",
        "clue": "Curiosity showed Luna that one board moved with the waves while the other stayed firmly wedged.",
        "plan": "She kept everyone back, marked the safe edge with a bright scarf, and asked the dock worker to use a brace before lifting the loose board.",
        "villain": "The dock's shadow made every ripple look like a secret creature.",
        "line_hero": "Mystery is a reason to investigate, not a reason to grab blindly.",
        "line_adult": "Your question kept our hands and the lobster safe.",
        "result": "The dock worker braced the boards, opened a clear path, and guided the lobster into a shallow rescue crate.",
        "ending": "The rescued lobster disappeared beneath a rock in the tide pool, leaving two neat bubbles behind.",
        "lesson": "curiosity can turn suspense into a safe plan",
        "object": "a trapped lobster",
    },
    {
        "title": "the red-clawed alarm",
        "arrival": "Luna was checking the harbor after sunset when a red claw appeared beside a floating buoy.",
        "problem": "A lobster had climbed into a ring of rope, and every wave pulled the ring tighter.",
        "clue": "She saw that the rope's knot rested on the dry side of the buoy, where a keeper could reach it with cutters.",
        "plan": "Luna used her superhero whistle to call the harbor keeper, then described the knot while staying on the steps.",
        "villain": "The waves tugged the rope with a steady, suspenseful pull.",
        "line_hero": "My superpower is noticing when someone needs help.",
        "line_adult": "And my job is bringing the right tool.",
        "result": "The keeper cut the rope, and the lobster paddled free into deeper water.",
        "ending": "The buoy bobbed peacefully, and Luna's whistle hung at her side like a tiny silver badge.",
        "lesson": "kindness starts when someone pays attention and calls for the right helper",
        "object": "a rope ring",
    },
    {
        "title": "the lighthouse clue",
        "arrival": "A lobster pot drifted toward the rocks beneath the lighthouse.",
        "problem": "Its red float kept vanishing behind waves, so the boat crew could not see where to steer.",
        "clue": "Luna noticed a flash of orange paint on the float whenever the lighthouse beam swept past.",
        "plan": "She counted the flashes aloud, and the crew used her count to guide their boat around the rocks.",
        "villain": "The fog hid the pot like a cape hiding a mysterious superhero.",
        "line_hero": "One small clue can guide a very big rescue.",
        "line_adult": "Keep counting. We can hear your careful eyes.",
        "result": "The crew reached the pot, freed the lobster, and returned the gear to calm water.",
        "ending": "The lighthouse beam crossed the bay, and Luna counted one bright flash for every safe wave.",
        "lesson": "curiosity becomes useful when careful observations are shared",
        "object": "a drifting lobster pot",
    },
]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    adult: str
    trait: str
    incident: int = 0
    tone: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about lobster rescue, kindness, suspense, and curiosity."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--adult", choices=ADULTS)
    parser.add_argument("--trait", choices=TRAITS)
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
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        name=name,
        gender=args.gender or GENDERS[name],
        adult=args.adult or rng.choice(ADULTS),
        trait=args.trait or rng.choice(TRAITS),
        incident=rng.randrange(len(INCIDENTS)),
        tone=rng.randrange(4),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The requested harbor setting is not known.")
    if params.name not in HERO_NAMES:
        raise StoryError("The hero must have a name from the storyworld.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The hero must be described as a girl or boy.")
    if params.adult not in ADULTS:
        raise StoryError("A trusted adult is required for the rescue.")
    if not 0 <= params.incident < len(INCIDENTS):
        raise StoryError("That rescue incident does not exist.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    incident = INCIDENTS[params.incident]
    place = PLACES[params.place]
    world = World(place=place["name"])

    hero = world.add(Entity(
        id="Hero",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0, "danger_awareness": 0.8},
        memes={"kindness": 1.0, "hope": 1.0},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type="adult",
        label=params.adult,
        meters={"rescue_skill": 1.0},
        memes={"trust": 1.0},
    ))
    lobster = world.add(Entity(
        id="Lobster",
        kind="animal",
        type="lobster",
        label="lobster",
        phrase="a small lobster",
        meters={"danger": 1.0, "freedom": 0.0},
        memes={"deserves_care": 1.0},
    ))
    tide = world.add(Entity(
        id="Tide",
        kind="force",
        type="tide",
        label="rising tide",
        meters={"rising": 1.0, "danger": 0.7},
        memes={"suspense": 1.0},
    ))
    lantern = world.add(Entity(
        id="Lantern",
        kind="tool",
        type="lantern",
        label="lantern",
        phrase="a bright yellow lantern",
        owner=hero.id,
        meters={"light": 1.0},
        memes={"guidance": 1.0},
    ))

    greetings = [
        "She wore a red rain cape and called herself Captain Kindness.",
        "He wore a blue towel as a cape and called himself the Harbor Comet.",
        "She had no super suit, only warm boots, a bright lantern, and a very alert face.",
        "He carried a notebook for clues and believed every rescue began with noticing.",
    ]
    tone_lines = [
        "The storm sounded fierce, but Luna remembered that being heroic did not mean being reckless.",
        "The darkness felt like a villain's curtain, yet curiosity kept the mystery from winning.",
        "The waves made the rescue feel enormous, even though the first helpful action was simply asking a good question.",
        "The harbor seemed to hold its breath while the little team prepared a careful answer.",
    ]

    world.say(
        f"At {world.place}, {params.name} was a {params.trait} {params.gender} who loved pretending to be a superhero."
    )
    world.say(greetings[params.tone])
    world.say(place["detail"])
    world.say(f"{params.adult} was checking the harbor when {incident['arrival'].lower()}")
    world.para()
    world.say(incident["problem"])
    world.say(incident["villain"])
    world.say(tone_lines[params.tone])
    world.say(
        f'{params.name} whispered, "I want to help, but I will not jump into a dangerous place."'
    )
    world.say(
        f'{params.adult} answered, "Good superheroes use curiosity first. What do you notice?"'
    )
    world.say(incident["clue"])
    world.say(
        f'{params.name} said, "The lobster needs kindness, and we need the right tool. Can you help me make a safe plan?"'
    )
    world.say(f'{params.adult} replied, "{incident["line_adult"]}"')
    world.para()
    world.say(incident["plan"])
    world.say(incident["line_hero"])
    world.say(
        "For one suspenseful moment, the waves rose, the rope creaked, and the lobster clicked its claws."
    )
    world.say(incident["result"])
    world.say(
        f"{params.name} waited until {params.adult} said the rescue was safe, then smiled and lowered the lantern."
    )
    world.say(
        f"The lobster was safe because {params.name} used curiosity to understand the danger and kindness to choose careful help."
    )
    world.say(incident["ending"])

    lobster.meters["danger"] = 0.0
    lobster.meters["freedom"] = 1.0
    tide.meters["danger"] = 0.1
    hero.memes["kindness"] = 1.0
    hero.memes["curiosity"] = 1.0

    world.facts.update(
        params=params,
        incident=incident,
        hero=hero,
        adult=adult,
        lobster=lobster,
        tide=tide,
        lantern=lantern,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly superhero story about {params.name} rescuing a lobster at {world.place}.",
        "Create suspense around a rising tide, then resolve it through curiosity, kindness, dialogue, and safe teamwork.",
        f"Tell a superhero story in which {params.name} learns that {incident['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question="Who is the hero of the story?",
            answer=f"{params.name} is the hero, a {params.trait} {params.gender} who helps rescue a lobster.",
        ),
        QAItem(
            question="Why was the lobster in danger?",
            answer=f"{incident['problem']} The rising tide made waiting without a plan more dangerous.",
        ),
        QAItem(
            question="What did curiosity help the hero discover?",
            answer=incident["clue"],
        ),
        QAItem(
            question="How was the lobster rescued?",
            answer=f"{incident['plan']} {incident['result']}",
        ),
        QAItem(
            question="What made the hero's action kind and brave?",
            answer=f"{params.name} protected the lobster without taking a reckless risk, because {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lobster?",
            answer="A lobster is a sea animal with a hard shell, many legs, and two large claws.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about another living thing and choosing to help without causing harm.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by noticing, wondering, and asking questions.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the excited feeling people have while waiting to learn what will happen next.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero uses courage, helpful skills, and good judgment to protect others.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- lobster_present, kindness_used, curiosity_used, suspense_resolved, safe_rescue.
:- lobster_present, not kindness_used.
:- lobster_present, not safe_rescue.
"""


def asp_facts() -> str:
    return "\n".join([
        "lobster_present.",
        "kindness_used.",
        "curiosity_used.",
        "suspense_resolved.",
        "safe_rescue.",
    ])


def asp_program(show: str = "#show compatible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        models = asp.solve(asp_program(), models=1)
        atoms = asp.atoms(models[0], "compatible") if models else []
        if atoms != [("story",)]:
            return 1
    except Exception:
        return 0
    for params in CURATED:
        sample = generate(params)
        if "lobster" not in sample.story.lower():
            return 1
        if not sample.story_qa:
            return 1
    return 0


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
        lines.append(
            f"  {entity.id:8} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moonlit_pier",
        name="Luna",
        gender="girl",
        adult="Aunt Bea",
        trait="curious",
        incident=0,
        tone=0,
        seed=101,
    ),
    StoryParams(
        place="harbor_steps",
        name="Milo",
        gender="boy",
        adult="Dad",
        trait="brave",
        incident=1,
        tone=1,
        seed=202,
    ),
    StoryParams(
        place="moonlit_pier",
        name="Tessa",
        gender="girl",
        adult="Uncle Sol",
        trait="gentle",
        incident=2,
        tone=2,
        seed=303,
    ),
    StoryParams(
        place="harbor_steps",
        name="Arlo",
        gender="boy",
        adult="Mom",
        trait="quick-thinking",
        incident=3,
        tone=3,
        seed=404,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        print()
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
        try:
            from storyworlds import asp
            models = asp.solve(asp_program(), models=1)
            print("ASP model:", ", ".join(str(atom) for atom in models[0]) if models else "none")
        except Exception:
            print("ASP pattern: lobster_present, kindness_used, curiosity_used, suspense_resolved, safe_rescue")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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
            header = f"### {sample.params.name}: lobster rescue superhero story"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
