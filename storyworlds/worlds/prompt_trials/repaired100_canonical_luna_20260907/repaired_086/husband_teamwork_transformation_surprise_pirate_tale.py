#!/usr/bin/env python3
"""A child-safe pirate tale about a husband, teamwork, transformation, and surprise."""

from __future__ import annotations

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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


HUSBANDS = ["Hugo", "Marek", "Owen", "Pablo", "Rafi", "Silas", "Tobin", "Wes"]
WIVES = ["Lina", "Mara", "Nell", "Pearl", "Rosa", "Suri", "Tala", "Vera"]
ISLANDS = ["Whispering Key", "Coconut Moon Cay", "Blue Lantern Isle", "Turtleback Island"]
TREASURES = ["a silver compass", "a singing shell", "a golden mango seed", "a star-shaped spyglass"]
WEATHER = ["a warm copper sunset", "a blue morning after rain", "a moonlit evening", "a windy afternoon"]
METHODS = [
    "the husband held the torn sail while his partner stitched it with bright red thread",
    "the husband steadied the boat while his partner read the tide marks",
    "the husband gathered floating boards while his partner tied them into a small raft",
    "the husband watched the reef while his partner followed the glow of the plankton",
]
SURPRISES = [
    "the treasure was not gold but a tiny garden that could grow on the ship",
    "the old chest opened into a bright parrot-shaped lantern",
    "the treasure map transformed into a message from the island's children",
    "the supposed treasure was a lost baby turtle wrapped in a captain's scarf",
]
LESSONS = [
    "teamwork can transform a frightening problem into a joyful surprise",
    "a good crew shares jobs instead of guarding every idea alone",
    "the best treasure may be something that helps many friends",
    "a surprise becomes sweeter when everyone has helped make it safe",
]
OPENINGS = [
    "Under a warm copper sunset",
    "At dawn, when the sea shone like a blue button",
    "While moonlight silvered the waves",
    "On a breezy afternoon",
    "After a rain shower washed the deck clean",
]
DIALOGUES = [
    ('"I cannot mend this sail alone," said {wife}.', '"Then I will hold it steady," said {husband}. "We can mend it together."'),
    ('"The tide is hiding the path," said {wife}.', '"I will watch the waves while you read the signs," said {husband}.'),
    ('"These boards are too heavy for me," said {wife}.', '"Not for us together," said {husband}. "You tie, and I will carry."'),
    ('"The island sounds close, but I cannot see it," said {wife}.', '"Follow the sound," said {husband}. "I will keep the boat clear."'),
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    husband: str
    wife: str
    island: str
    treasure: str
    weather: str
    method_id: int
    surprise_id: int
    lesson_id: int
    opening_id: int
    dialogue_id: int
    seed: Optional[int] = None


@dataclass
class World:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate Tale StoryWorld about a husband, teamwork, transformation, and surprise."
    )
    parser.add_argument("--husband", choices=HUSBANDS)
    parser.add_argument("--wife", choices=WIVES)
    parser.add_argument("--island", choices=ISLANDS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        husband=args.husband or rng.choice(HUSBANDS),
        wife=args.wife or rng.choice(WIVES),
        island=args.island or rng.choice(ISLANDS),
        treasure=rng.choice(TREASURES),
        weather=rng.choice(WEATHER),
        method_id=rng.randrange(len(METHODS)),
        surprise_id=rng.randrange(len(SURPRISES)),
        lesson_id=rng.randrange(len(LESSONS)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
    )


def tell(params: StoryParams) -> World:
    if params.husband == params.wife:
        raise StoryError("The husband and wife must have different names.")
    if params.method_id not in range(len(METHODS)):
        raise StoryError("Unknown teamwork method.")
    if params.surprise_id not in range(len(SURPRISES)):
        raise StoryError("Unknown surprise.")
    if params.lesson_id not in range(len(LESSONS)):
        raise StoryError("Unknown lesson.")

    world = World()
    husband = world.add(Entity(
        "husband", "person", params.husband, "captain's husband",
        meters={"strength": 0.8, "safety": 0.3},
        memes={"worry": 0.7, "trust": 0.5},
    ))
    wife = world.add(Entity(
        "wife", "person", params.wife, "captain",
        meters={"navigation": 0.8, "safety": 0.3},
        memes={"worry": 0.7, "trust": 0.5},
    ))
    ship = world.add(Entity(
        "ship", "boat", "the Mango Gull", "shared pirate boat",
        meters={"sail_strength": 0.4, "seaworthiness": 0.5},
        memes={"hope": 0.6},
    ))
    island = world.add(Entity(
        "island", "place", params.island, "mysterious island",
        meters={"distance": 1.0},
        memes={"mystery": 0.9},
    ))
    world.facts.update(
        husband=husband,
        wife=wife,
        ship=ship,
        island=island,
        teamwork=False,
        transformed=False,
        surprise=params.surprise_id,
        resolved=False,
    )

    world.say(f"{OPENINGS[params.opening_id]}, {params.husband} sailed with {params.wife} toward {params.island}.")
    world.say(f"They were husband and wife, and their little ship, the Mango Gull, carried {params.treasure} on its painted flag.")
    world.say(f"They hoped to find a treasure rumored to appear only during {params.weather}.")
    world.para()

    world.say("A sudden gust ripped the ship's sail, and the Mango Gull spun toward a ring of dark rocks.")
    world.say(f'"We must turn now!" cried {params.wife}. "The sail will not answer me."')
    world.say(f'"I will not let the sea frighten us," said {params.husband}. "Tell me what you need."')
    first, second = DIALOGUES[params.dialogue_id]
    world.say(first.format(wife=params.wife, husband=params.husband))
    world.say(second.format(wife=params.wife, husband=params.husband))
    world.say(f"Together, {METHODS[params.method_id]}.")
    world.say("The ship steadied, the rocks slipped behind them, and the two sailors discovered that their separate skills worked like two hands on one rope.")
    husband.memes.update(worry=0.2, trust=0.9)
    wife.memes.update(worry=0.2, trust=0.9)
    ship.meters.update(sail_strength=0.9, seaworthiness=0.9)
    world.facts["teamwork"] = True
    world.para()

    world.say(f"At last, they reached {params.island}. A little chest rested beneath a palm tree, but it was covered with seaweed and would not open.")
    world.say(f"{params.husband} used his strength to lift the heavy lid while {params.wife} noticed a shell-shaped key hidden in the sand.")
    world.say("They turned the key together.")
    world.say(f"Surprise! {SURPRISES[params.surprise_id].capitalize()}.")
    world.say(f"The treasure was transformed by their teamwork: what looked like {params.treasure} became a gift meant to care for the whole crew.")
    world.say(f'"Our greatest treasure was not waiting inside the chest," said {params.wife}.')
    world.say(f'"It was the way we solved the storm together," said {params.husband}.')
    world.say(f"They carried the transformed treasure home, where every sailor could share its wonder.")
    world.say(f"They learned that {LESSONS[params.lesson_id]}.")
    world.say(f"That night, {params.husband} and {params.wife} watched the new treasure glow beside the Mango Gull, while friendly stars blinked above {params.island}.")
    husband.memes.update(pride=0.9, care=1.0)
    wife.memes.update(pride=0.9, care=1.0)
    island.memes.update(mystery=0.0, welcome=1.0)
    world.facts.update(teamwork=True, transformed=True, resolved=True)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-safe Pirate Tale about husband {params.husband} and {params.wife} using teamwork.",
            f"Tell how teamwork transforms a danger near {params.island} into a surprise.",
            f"End with {params.husband} and {params.wife} sharing a transformed treasure.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = world.facts["params"] if "params" in world.facts else None
    husband = f["husband"].label
    wife = f["wife"].label
    island = f["island"].label
    surprise = SURPRISES[world.facts["surprise"]]
    return [
        QAItem(
            "What danger did the husband and his wife face?",
            f"A gust ripped the Mango Gull's sail and pushed the ship toward dark rocks, so the husband and his wife had to work quickly to steer safely.",
        ),
        QAItem(
            "How did the husband and his wife use teamwork?",
            f"{METHODS[world.facts.get('method_id', 0)] if 'method_id' in world.facts else 'They combined the husband’s strength with the wife’s careful navigation'}." 
            if False else
            f"They combined the husband's practical help with his wife's navigation. They held, tied, watched, and steered together until the ship was safe.",
        ),
        QAItem(
            "What surprise did they discover?",
            f"Surprise! {surprise.capitalize()}. The treasure became a useful or caring gift instead of an ordinary chest of gold.",
        ),
        QAItem(
            "What changed because of their teamwork?",
            f"The torn sail was repaired, the ship reached {island} safely, and the mysterious treasure transformed into something the whole crew could enjoy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does teamwork mean?",
            "Teamwork means people share jobs, listen to one another, and combine their skills to solve a problem.",
        ),
        QAItem(
            "What is transformation?",
            "Transformation is a meaningful change in form, condition, or purpose. In this tale, a mysterious treasure changes into a helpful gift.",
        ),
        QAItem(
            "Why can a surprise be valuable?",
            "A surprise can reveal an unexpected possibility, especially when it rewards patience, cooperation, or care for others.",
        ),
        QAItem(
            "What makes a pirate adventure safe for children?",
            "A child-safe pirate adventure uses imaginary danger, careful choices, kind relationships, and problem solving rather than frightening harm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key in ("teamwork", "transformed", "resolved"):
        lines.append(f"  fact.{key}={world.facts.get(key)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("domain", "pirate_tale"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "transformation"),
        asp.fact("feature", "surprise"),
        asp.fact("role", "husband"),
        asp.fact("safety", "child_safe"),
    ])


ASP_RULES = """
valid_story :-
    domain(pirate_tale),
    feature(teamwork),
    feature(transformation),
    feature(surprise),
    role(husband),
    safety(child_safe).
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    accepted = any(symbol.name == "valid_story" for symbol in symbols)
    if not accepted:
        print("Mismatch: ASP rejected the pirate teamwork story.")
        return 1
    rng = random.Random(086)
    sample = generate(resolve_params(build_parser().parse_args([]), rng))
    if not sample.story or "husband" not in sample.story.lower():
        print("Mismatch: generated story failed the husband gate.")
        return 1
    print("OK: ASP and Python accepted the pirate teamwork story.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams("Hugo", "Lina", "Whispering Key", "a silver compass", "a warm copper sunset", 0, 0, 0, 0, 0),
    StoryParams("Marek", "Pearl", "Blue Lantern Isle", "a singing shell", "a moonlit evening", 1, 1, 1, 2, 1),
    StoryParams("Silas", "Vera", "Turtleback Island", "a star-shaped spyglass", "a blue morning after rain", 2, 2, 2, 1, 2),
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
        print("compatible story:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            seed = base + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
