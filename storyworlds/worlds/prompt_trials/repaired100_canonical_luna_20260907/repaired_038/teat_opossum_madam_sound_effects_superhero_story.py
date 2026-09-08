#!/usr/bin/env python3
"""
A tiny superhero storyworld about Madam, an opossum, and a lost teat-shaped
silver bell. Sound effects, physical meters, and emotional memes drive each
story from trouble to a brave, caring rescue.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


@dataclass(frozen=True)
class Scenario:
    id: str
    arrival: str
    danger: str
    sound: str
    turn: str
    clue: str
    action: str
    result: str
    ending: str


@dataclass
class StoryParams:
    name: str
    hero_title: str
    helper: str
    scenario: str
    opening: int
    dialogue: int
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Luna", "Milo", "Zara", "Nia", "Theo", "Pip"]
HELPERS = ["Captain Comet", "Dr. Bright", "Madam Star", "Coach Nova"]
OPENINGS = [
    "At sunset",
    "Before the town parade",
    "On a bright Saturday morning",
    "Just as the moon rose",
    "During the little city's lantern festival",
    "After the school bell rang",
]
DIALOGUES = [
    (
        '"I can help," said {name}. "What did you notice?"',
        '"The bell follows warm, gentle sounds," said {helper}. "Listen before you leap."',
    ),
    (
        '"I am scared, but I will not run away," said {name}.',
        '"Courage means caring carefully," said {helper}. "Look for the clue."',
    ),
    (
        '"Tell me your plan," said {name}.',
        '"First we protect the opossum, then we solve the mystery," said {helper}.',
    ),
    (
        '"I heard a tiny cry," said {name}. "Someone needs a hero."',
        '"A thoughtful hero uses a soft voice and steady hands," said {helper}.',
    ),
]

SCENARIOS = {
    "rooftop_bell": Scenario(
        "rooftop_bell",
        "Madam, a friendly opossum who wore a red cape, found a small silver teat-shaped bell on a rooftop.",
        "When Madam tugged it, the bell's ringing lifted her toward the edge of the roof.",
        "KLANG-kling-WHOOOSH!",
        "The opossum's cape snagged on a chimney, and she dangled above the street.",
        "Her whiskers pointed toward a warm bakery vent, where the bell's ringing became softer.",
        "used a scarf as a safety line, called to Madam in a calm rhythm, and guided her toward the vent",
        "Madam landed safely, and the silver bell stopped pulling her upward.",
        "The bell rested in a velvet box while Madam's red cape fluttered like a superhero flag.",
    ),
    "garden_echo": Scenario(
        "garden_echo",
        "Madam, a curious opossum, discovered a silver teat-shaped bell beneath the community garden.",
        "Its ringing made the garden statues march toward a sleeping baby bird's nest.",
        "DING-dong-DUM!",
        "The statues stopped whenever Madam tapped her paws twice.",
        "The baby bird chirped twice from the nest, matching Madam's careful rhythm.",
        "stood between the statues and the nest, copied the two soft taps, and led the statues back to their stones",
        "The statues became still, and the baby bird remained safe in its nest.",
        "Madam placed one paw beside the bell, and the garden grew quiet enough to hear the leaves.",
    ),
    "market_whirl": Scenario(
        "market_whirl",
        "At the market, Madam found a shiny teat-shaped bell inside a basket of apples.",
        "One ring made the apples spin into a red whirlwind around the shoppers.",
        "WHIRR-pop-pop-BONG!",
        "The whirlwind slowed whenever the bell was covered by a blue cloth.",
        "A blue cloth lay beside the baker's cart, and the apples rolled away from it.",
        "covered the bell, moved the shoppers behind the cart, and guided each apple into a crate",
        "The market became still, and no one was hurt.",
        "Madam received one clean apple as a medal and wore the blue cloth like a tiny cape.",
    ),
    "moon_bridge": Scenario(
        "moon_bridge",
        "Madam carried a silver teat-shaped bell across a moonlit bridge.",
        "The bridge began to bounce whenever the bell rang, leaving a family of ducklings stranded.",
        "BOING-ting-ting-BOING!",
        "The bridge steadied when everyone hummed one low note together.",
        "Madam's soft humming blended with the ducklings' quiet peeps.",
        "asked the helper to hum, then crossed slowly and carried the bell into a padded basket",
        "The bridge held firm, and the ducklings waddled safely to the other side.",
        "Under the moon, Madam's basket gave one gentle chime and then slept.",
    ),
}

REGISTRY = {
    "heroes": {"luna", "milo", "zara", "nia", "theo", "pip"},
    "helpers": {"captain_comet", "dr_bright", "madam_star", "coach_nova"},
    "scenarios": set(SCENARIOS),
}


def _meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario]
    world = World()
    hero = world.add(Entity(params.name.lower(), "character", params.name))
    helper = world.add(Entity(params.helper.lower().replace(" ", "_"), "character", params.helper))
    opossum = world.add(Entity("madam", "animal", "Madam"))
    bell = world.add(Entity("teat_bell", "object", "silver teat-shaped bell"))
    world.facts.update(hero=hero, helper=helper, opossum=opossum, bell=bell, scenario=scenario)

    opening = OPENINGS[params.opening % len(OPENINGS)]
    first, second = DIALOGUES[params.dialogue % len(DIALOGUES)]
    first = first.format(name=params.name, helper=params.helper)
    second = second.format(name=params.name, helper=params.helper)

    world.say(
        f"{opening}, {params.name}, a young superhero in a bright cape, patrolled the town "
        f"with {params.helper}."
    )
    world.say(scenario.arrival)
    world.say(
        f"The strange {bell.label} shone beside Madam's paws. "
        "It looked small, but its secret power was not small at all."
    )
    world.para()

    world.say(first)
    world.say(second)
    world.say(scenario.danger)
    world.say(f'Then the silver bell cried, "{scenario.sound}"')
    _meter(bell, "danger", 1.0)
    _meter(opossum, "distance", 1.0)
    _meme(hero, "worry", 1.0)
    _meme(opossum, "fear", 1.0)

    world.say(scenario.turn)
    world.say(
        f"{params.name} took one slow breath. {scenario.clue} "
        "That clue changed the rescue plan."
    )
    world.para()

    world.say(
        f'"Stay with me, Madam," said {params.name}. '
        '"We will use the clue, not our panic."'
    )
    world.say(
        f'"I see it," said {params.helper}. '
        '"A real superhero protects others before showing off."'
    )
    world.say(scenario.action + ".")
    _meter(bell, "danger", 0.0)
    _meter(opossum, "distance", 0.0)
    _meter(opossum, "safe", 1.0)
    _meme(hero, "worry", 0.0)
    _meme(hero, "courage", 1.0)
    _meme(opossum, "relief", 1.0)
    world.fired.add(("rescue", params.scenario))

    world.say(scenario.result)
    world.say(
        f"{params.helper} smiled. "
        f'"{params.name}, your best superpower was careful listening." '
        f"{params.name} smiled too, because the clue had made the rescue possible."
    )
    world.para()
    world.say(scenario.ending)
    world.facts["resolved"] = True
    return world


def valid_scenarios() -> list[str]:
    return sorted(SCENARIOS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenario = args.scenario or rng.choice(valid_scenarios())
    if scenario not in SCENARIOS:
        raise StoryError(f"Unknown rescue scenario: {scenario}.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        hero_title=args.hero_title or "young superhero",
        helper=args.helper or rng.choice(HELPERS),
        scenario=scenario,
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Scenario = f["scenario"]
    return [
        f"Write a superhero story about {f['opossum'].label}, a teat-shaped bell, and {s.id.replace('_', ' ')}.",
        "Tell a child-friendly rescue story in which sound effects reveal the safe solution.",
        f"Write a story where {f['hero'].label} protects an opossum by noticing this clue: {s.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Scenario = f["scenario"]
    hero = f["hero"].label
    helper = f["helper"].label
    return [
        QAItem(
            f"Who rescued Madam?",
            f"{hero} rescued Madam with help from {helper}. They used observation and a careful plan instead of rushing.",
        ),
        QAItem(
            f"What happened when the silver teat-shaped bell rang?",
            f"The bell made the sound effect {s.sound} and caused the danger described in the story: {s.danger}",
        ),
        QAItem(
            "What clue helped the heroes?",
            f"The important clue was that {s.clue} This showed them how to change their rescue plan.",
        ),
        QAItem(
            "How did the heroes keep Madam safe?",
            f"They {s.action}. This worked because they followed the clue and moved carefully.",
        ),
        QAItem(
            "What proved that the rescue succeeded?",
            f"{s.result} At the end, {s.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an opossum?",
            "An opossum is a small mammal with a pointed face, a long tail, and strong climbing skills.",
        ),
        QAItem(
            "What is a teat?",
            "A teat is a nipple on a mammal's body through which milk can pass to a nursing young animal.",
        ),
        QAItem(
            "Why should a superhero listen before acting?",
            "Listening can reveal a useful clue, so a superhero can protect people and animals with a safer plan.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


ASP_RULES = r"""
hero(X) :- registered_hero(X).
helper(X) :- registered_helper(X).
scenario(X) :- registered_scenario(X).
valid_story(H, S) :- hero(H), scenario(S), superhero_theme.
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("superhero_theme")]
    for hero in sorted(REGISTRY["heroes"]):
        lines.append(asp.fact("registered_hero", hero))
    for helper in sorted(REGISTRY["helpers"]):
        lines.append(asp.fact("registered_helper", helper))
    for scenario in sorted(REGISTRY["scenarios"]):
        lines.append(asp.fact("registered_scenario", scenario))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = {
        (hero, scenario)
        for hero in sorted(REGISTRY["heroes"])
        for scenario in sorted(REGISTRY["scenarios"])
    }
    actual = asp_valid_pairs()
    if expected != actual:
        print("ASP/Python parity failed.")
        print("Only in Python:", sorted(expected - actual))
        print("Only in ASP:", sorted(actual - expected))
        return 1
    for scenario in valid_scenarios():
        params = StoryParams("Luna", "young superhero", "Madam Star", scenario, 0, 0)
        sample = generate(params)
        if not sample.story or "Madam" not in sample.story:
            print(f"Generated story check failed for {scenario}.")
            return 1
    print(f"OK: ASP parity and generated stories verified ({len(expected)} pairs).")
    return 0


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld with Madam, an opossum, and sound effects."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--hero-title")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS))
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


CURATED = [
    StoryParams("Luna", "young superhero", "Captain Comet", "rooftop_bell", 0, 0),
    StoryParams("Zara", "young superhero", "Madam Star", "garden_echo", 1, 1),
    StoryParams("Milo", "young superhero", "Dr. Bright", "market_whirl", 2, 2),
    StoryParams("Nia", "young superhero", "Coach Nova", "moon_bridge", 3, 3),
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                if attempt > max(100, args.n * 100):
                    break
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
