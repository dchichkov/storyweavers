#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld set in a market.

A star-shaped lantern goes missing during a busy market evening. Suspense grows
as Luna follows a trail of silver dust, but a careful helper helps her test
each clue. The lesson learned is that a bright guess is not the same as proof,
and that returning what was borrowed makes the whole market shine.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the market"


@dataclass
class World:
    setting: Setting
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
    child_name: str
    helper_name: str
    market_mood: str
    seed: Optional[int] = None
    incident_id: Optional[str] = None


@dataclass(frozen=True)
class Incident:
    id: str
    opening: str
    clue: str
    false_guess: str
    decisive_clue: str
    cause: str
    repair: str
    ending: str


CHILD_NAMES = ["Luna", "Milo", "Nia", "Pip", "Tessa", "Ollie"]
HELPER_NAMES = ["Mara", "Jun", "Ari", "Grandma Rose", "Theo"]
MARKET_MOODS = ["bustling", "rainy", "twinkling", "sleepy", "cheerful"]

INCIDENTS = [
    Incident(
        id="silver_ribbon",
        opening="At market close, the great star lantern above the fruit stall gave one sad blink and vanished.",
        clue="A thin silver ribbon curled from the empty hook toward the basket lane.",
        false_guess="Luna guessed that the wind had snatched the star into the dark.",
        decisive_clue="Mara found matching silver dust beneath a folded awning, where the lantern had brushed while being carried.",
        cause="the baker had borrowed the star lantern to light a dark path and set it under the awning when rain began",
        repair="They carried the lantern back, dried its paper points, and hung it on the strong hook.",
        ending="The market sang, 'Star bright, star right,' while the lantern shone above the fruit like a tiny moon.",
    ),
    Incident(
        id="goat_cart",
        opening="At market close, a star-shaped sign was missing from the berry cart, and the cart squeaked in suspense.",
        clue="Three blue berry leaves lay in a line beside the empty signpost.",
        false_guess="Luna guessed that a playful goat had eaten the sign.",
        decisive_clue="The leaves led to a handcart, where the star sign rested safely under a cloth.",
        cause="the berry seller had moved the sign onto the handcart while making room for a new basket",
        repair="They lifted the sign from the cart and tied it firmly beside the berries.",
        ending="The goat nibbled hay, the berries gleamed, and the star sign twinkled above the cart.",
    ),
    Incident(
        id="rainy_roof",
        opening="At market close, the little star flag atop the flower stall drooped beneath a sudden patter of rain.",
        clue="A trail of bright drops ran from the flagpole to the covered herb table.",
        false_guess="Luna guessed that a puddle had swallowed the flag's silver shine.",
        decisive_clue="Under the herb table they found the flag folded beside a leaky roof tile.",
        cause="the florist had taken down the flag to keep it dry and forgotten where it was placed",
        repair="They dried the flag, fixed the loose tile with an adult's help, and raised the flag again.",
        ending="The rain tapped a gentle rhyme while the star flag danced above the dry flowers.",
    ),
    Incident(
        id="music_box",
        opening="At market close, the star on the musician's music box stopped glowing halfway through a tune.",
        clue="A soft chime sounded from behind the honey stall.",
        false_guess="Luna guessed that the music box had lost its magic.",
        decisive_clue="Behind the honey stall, they found the star resting beside a loose battery cover.",
        cause="the musician had removed the star while checking the music box and carried it to the honey stall",
        repair="They returned the star, secured the cover, and tested the tune with careful hands.",
        ending="The music played, the star glowed, and the market bounced to a bright little beat.",
    ),
]

INCIDENT_BY_ID = {item.id: item for item in INCIDENTS}


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0x5A17)
    text = "|".join([params.child_name, params.helper_name, params.market_mood, params.incident_id or ""])
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:]


def build_world(params: StoryParams) -> World:
    if not params.child_name.strip():
        raise StoryError("child_name must not be empty")
    if not params.helper_name.strip():
        raise StoryError("helper_name must not be empty")
    if params.market_mood not in MARKET_MOODS:
        raise StoryError(f"unknown market mood: {params.market_mood}")

    rng = _rng(params)
    incident = INCIDENT_BY_ID.get(params.incident_id or "")
    if incident is None:
        incident = rng.choice(INCIDENTS)

    world = World(Setting())
    child = world.add(Entity("child", "character", params.child_name))
    helper = world.add(Entity("helper", "character", params.helper_name))
    star = world.add(Entity("star", "object", "star lantern"))
    market = world.add(Entity("market", "place", "market"))

    child.memes.update(curiosity=1.0, courage=1.0)
    helper.memes.update(care=1.0)
    star.meters.update(brightness=1.0, safety=0.0)
    world.facts.update(
        child=child,
        helper=helper,
        star=star,
        market=market,
        incident=incident,
        mood=params.market_mood,
        suspense=True,
        solved=False,
    )

    openings = [
        incident.opening,
        f"In the {params.market_mood} market, {incident.opening[0].lower() + incident.opening[1:]}",
        f"Come hear the market rhyme: {incident.opening}",
    ]
    world.say(openings[rng.randrange(len(openings))])
    world.say(f"{child.label} stared at the empty place. The star had been the market's brightest little welcome.")
    world.para()

    world.say(f'"We must not hurry to blame," said {helper.label}. "{child.label}, let us follow what the clues can prove."')
    world.say(f'"Then I will look closely," said {child.label}. "I will follow the silver trail, but I will not leap to a guess."')
    world.say(incident.clue)
    world.say(incident.false_guess)
    world.facts["first_guess"] = incident.false_guess
    world.para()

    child.memes["focus"] = 1.0
    helper.memes["patience"] = 1.0
    world.say(f"The market held its breath. Then {incident.decisive_clue}")
    world.say(f"Now they understood: {_capitalize(incident.cause)}.")
    world.facts["cause"] = incident.cause
    world.facts["decisive_clue"] = incident.decisive_clue
    world.facts["suspense"] = False
    world.para()

    star.meters["brightness"] = 2.0
    star.meters["safety"] = 1.0
    child.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    world.say(f'"A lesson learned is a lantern for tomorrow," said {helper.label}. {incident.repair}.')
    world.say("They agreed to ask before borrowing bright things and to return every useful object to its proper place.")
    world.say(incident.ending)
    world.facts["repair"] = incident.repair
    world.facts["solved"] = True
    world.facts["ending"] = incident.ending
    return world


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    child = world.facts["child"].label
    helper = world.facts["helper"].label
    return [
        f"Write a nursery-rhyme-style suspense story in a market where a star goes missing and {child} follows a clue.",
        f"Show {child} and {helper} speaking back and forth while they test a false guess and discover that {incident.cause}.",
        "End with a concrete market image and a lesson learned about asking before borrowing and returning what was used.",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.facts["incident"]
    child = world.facts["child"].label
    helper = world.facts["helper"].label
    return [
        QAItem(
            question=f"What happened to the star in the market?",
            answer=f"The star disappeared from its usual place, creating suspense until {child} and {helper} followed the clues.",
        ),
        QAItem(
            question=f"What was {child}'s first guess?",
            answer=f"{child} first guessed that {incident.false_guess.split(' guessed that ', 1)[-1].rstrip('.')}. The guess was not enough because they still needed proof.",
        ),
        QAItem(
            question="What clue solved the mystery?",
            answer=f"The decisive clue was this: {incident.decisive_clue} It connected the missing star to what had really happened.",
        ),
        QAItem(
            question="What caused the star to go missing?",
            answer=f"The star went missing because {incident.cause}.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was to ask before borrowing something and to return it carefully so other people can depend on it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the exciting feeling of waiting to learn what will happen or how a mystery will end.",
        ),
        QAItem(
            question="What is a market?",
            answer="A market is a place where people meet to buy, sell, and share goods.",
        ),
        QAItem(
            question="What is a star?",
            answer="A star is a bright shape or object; in this story, the star is a lantern that helps make the market welcoming.",
        ),
        QAItem(
            question="Why is a lesson learned useful?",
            answer="A lesson learned helps someone make a wiser choice the next time a similar problem appears.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: suspense={world.facts['suspense']} solved={world.facts['solved']}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "market"),
            asp.fact("object", "star"),
            asp.fact("feature", "suspense"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("action", "follow_clue"),
            asp.fact("action", "repair"),
            asp.fact("outcome", "star_returned"),
        ]
    )


ASP_RULES = r"""
mystery_begins :- setting(market), object(star), feature(suspense).
careful_search :- mystery_begins, action(follow_clue).
lesson_learned :- careful_search, action(repair).
valid_story :- lesson_learned, outcome(star_returned).
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm validity.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("solved"):
            print("MISMATCH: generated story did not reach a solved state.")
            return 1
        if "star" not in sample.story.lower() or "market" not in sample.story.lower():
            print("MISMATCH: generated story omitted required domain terms.")
            return 1
    print("OK: ASP twin confirms the storyworld and generated stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme suspense storyworld in a market.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--mood", choices=MARKET_MOODS)
    parser.add_argument("--incident")
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
    return StoryParams(
        child_name=args.name or rng.choice(CHILD_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        market_mood=args.mood or rng.choice(MARKET_MOODS),
        incident_id=args.incident or rng.choice(INCIDENTS).id,
    )


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
    StoryParams("Luna", "Mara", "twinkling", "silver_ribbon"),
    StoryParams("Milo", "Jun", "rainy", "rainy_roof"),
    StoryParams("Nia", "Grandma Rose", "cheerful", "music_box"),
    StoryParams("Pip", "Theo", "bustling", "goat_cart"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

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
