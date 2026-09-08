#!/usr/bin/env python3
"""
A small comic storyworld about a terrible stench, a supposed goon, and a
delicious twist.

The simulation follows a nervous market morning. A foul smell sends a baker
and a child looking for a goon, but the frightening culprit is not a villain.
The twist is that the "goon" is a hungry goose whose muddy feathers hide a
delicious stolen pie. Once the characters talk, the chase becomes a rescue,
and the ending proves the change with a shared picnic.
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
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ImportError:
    from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("stench", "hunger", "fear", "mess", "safety", "joy", "trust"):
            self.meters.setdefault(key, 0.0)
        for key in ("goon", "helper", "delicious", "brave", "kind"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    baker: str
    helper: str
    market: str = "the morning market"
    seed: Optional[int] = None
    twist: str = "goose"
    variation: int = 0


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Twist:
    key: str
    creature: str
    creature_label: str
    false_clue: str
    true_clue: str
    rescue: str
    delicious_item: str
    final_image: str
    lesson: str


TWISTS = [
    Twist(
        "goose",
        "goose",
        "a muddy goose",
        "two huge footprints and a feather stuck in a pie crate",
        "a soft honk came from behind the flour cart",
        "wash the sticky jam from its beak and free its foot from a loop of string",
        "a warm berry pie",
        "The goose waddled beside them while three plates of pie cooled on the stall.",
        "A scary-looking visitor may need help before it needs blame.",
    ),
    Twist(
        "goose",
        "goose",
        "a rain-soaked goose",
        "a trail of feathers leading beneath the fishmonger's table",
        "a sneeze answered the baker's question from inside an empty barrel",
        "dry its feathers and untangle its wing from a market ribbon",
        "a honey cake",
        "The goose wore a paper napkin like a tiny crown beside the cake.",
        "A loud stranger can still be a hungry neighbor.",
    ),
    Twist(
        "goose",
        "goose",
        "a sleepy goose",
        "a shadow with a long beak bobbing across the bakery door",
        "a little webbed foot waved from a basket of turnips",
        "lift the basket and roll a lemon away from its trapped bill",
        "a cinnamon bun",
        "The goose shared the last cinnamon bun after giving one proud honk.",
        "A strange smell can hide a simple problem.",
    ),
]


NAMES = ["Luna", "Milo", "Pip", "Cora", "Nina", "Toby", "Daisy", "Otto"]
MARKETS = ["the morning market", "the riverside market", "the village market"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comic storyworld about a stench, a goon, and a delicious twist."
    )
    parser.add_argument("--baker")
    parser.add_argument("--helper")
    parser.add_argument("--market")
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
    baker = args.baker or "Luna"
    helper = args.helper or rng.choice([name for name in NAMES if name != baker])
    if baker == helper:
        raise StoryError("The baker and helper must have different names.")
    market = args.market or rng.choice(MARKETS)
    if not market.strip():
        raise StoryError("The market name cannot be empty.")
    return StoryParams(
        baker=baker,
        helper=helper,
        market=market,
        seed=args.seed,
        twist=rng.choice(TWISTS).key,
        variation=rng.getrandbits(63),
    )


def setup_world(params: StoryParams, twist: Twist) -> World:
    world = World(params)
    world.add(
        Entity(
            "baker",
            "character",
            params.baker,
            params.market,
            memes={"delicious": 1.0},
        )
    )
    world.add(
        Entity(
            "helper",
            "character",
            params.helper,
            params.market,
            memes={"brave": 0.4},
        )
    )
    world.add(
        Entity(
            "goon",
            "animal",
            twist.creature_label,
            params.market,
            memes={"goon": 1.0},
        )
    )
    world.add(
        Entity(
            "pie",
            "food",
            twist.delicious_item,
            params.market,
            meters={"safety": 0.8},
            memes={"delicious": 1.0},
            owner="baker",
        )
    )
    world.add(
        Entity(
            "cart",
            "object",
            "the flour cart",
            params.market,
        )
    )
    return world


def tell_story(world: World) -> None:
    params = world.params
    twist = next(item for item in TWISTS if item.key == params.twist)
    baker = world.entities["baker"]
    helper = world.entities["helper"]
    goon = world.entities["goon"]
    pie = world.entities["pie"]

    world.say(
        f"At {params.market}, {baker.label} arranged a tray of {pie.label} while "
        f"{helper.label} counted the coins."
    )
    world.say(
        f"Then a tremendous stench rolled between the stalls. It smelled like "
        f"wet socks, old cabbage, and a shoe that had lost an argument with mud."
    )
    world.say(
        f'"That is no ordinary smell," said {helper.label}. '
        f'"It smells like a goon."'
    )
    world.say(
        f'"If there is a goon near my {pie.label}, I shall question it politely," '
        f"said {baker.label}, hiding behind a rolling pin."
    )

    world.paragraph()
    world.say(f"They followed {twist.false_clue}.")
    world.say(
        f"The market grew quiet. Even a nearby cat stopped licking its paw and "
        f"looked offended by the air."
    )
    world.say(
        f'"Goon, come out!' f'" called {helper.label}. '
        f'"We know you are making that stench."'
    )
    world.say(
        f'"Please do not shout," replied {baker.label}. '
        f'"A real goon may have very sensitive feelings."'
    )
    world.say(
        f"At that moment, {twist.true_clue}. The supposed goon gave a tiny sneeze."
    )
    goon.meters["stench"] = 3.0
    goon.meters["hunger"] = 2.0
    goon.meters["fear"] = 2.0
    goon.memes["goon"] = 1.0
    world.say(
        f"Out waddled {goon.label}, covered in mud, jam, and one alarming lettuce leaf."
    )

    world.paragraph()
    world.say(
        f'"Aha!" cried {helper.label}. "The goon is a goose!"'
    )
    world.say(
        f'"And the stench?" asked {baker.label}.'
    )
    world.say(
        f'"Mostly the mud," said {helper.label}. "And perhaps the lettuce leaf."'
    )
    world.say(
        f"The goose honked and tugged at a string caught around its foot."
    )
    world.say(
        f"They discovered that the goose had not attacked the stall at all. "
        f"It had followed the smell of {pie.label} and become stuck beside the cart."
    )
    world.say(
        f"Together, they {twist.rescue}. The goose blinked, sneezed, and stood up straight."
    )
    goon.meters["stench"] = 0.5
    goon.meters["fear"] = 0.0
    goon.meters["safety"] = 2.0
    goon.memes["goon"] = 0.0
    goon.memes["helper"] = 1.0
    goon.memes["kind"] = 1.0
    baker.meters["trust"] = 2.0
    helper.meters["trust"] = 2.0

    world.say(
        f'"It was never a goon," said {baker.label}. "It was a hungry neighbor."'
    )
    world.say(
        f'"Then the neighbor deserves breakfast," said {helper.label}.'
    )
    world.say(
        f"The baker cut the {twist.delicious_item} into fair pieces. "
        f"The twist was delicious: the frightening smell had led them to a friend."
    )
    world.say(twist.final_image)
    world.say(f"Their lesson was simple: {twist.lesson}")

    world.facts.update(
        twist=twist,
        baker=baker.label,
        helper=helper.label,
        creature=goon.label,
        food=pie.label,
        market=params.market,
        stench_outcome="The stench came from mud and a lettuce leaf on the goose.",
        rescue=twist.rescue,
        final_image=twist.final_image,
    )


def story_qa(world: World) -> list[QAItem]:
    twist: Twist = world.facts["twist"]
    baker = world.facts["baker"]
    helper = world.facts["helper"]
    creature = world.facts["creature"]
    food = world.facts["food"]
    return [
        QAItem(
            "Who noticed the awful stench first?",
            f"{baker} and {helper} noticed the awful stench at {world.facts['market']}.",
        ),
        QAItem(
            "Why did the characters think there might be a goon?",
            f"They followed {twist.false_clue}, and the terrible smell made the visitor seem frightening.",
        ),
        QAItem(
            "What was the supposed goon really?",
            f"The supposed goon was {creature}, a hungry goose rather than a villain.",
        ),
        QAItem(
            "What caused the stench?",
            world.facts["stench_outcome"],
        ),
        QAItem(
            "How did the characters help the goose?",
            f"They {world.facts['rescue']}.",
        ),
        QAItem(
            "What delicious food did they share?",
            f"They shared {food}.",
        ),
        QAItem(
            "What was the comic twist?",
            f"The scary goon turned out to be a hungry goose that needed help, and the stench came from mud and lettuce.",
        ),
        QAItem(
            "What lesson did they learn?",
            twist.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a stench?",
            "A stench is a very strong and unpleasant smell.",
        ),
        QAItem(
            "What does delicious mean?",
            "Delicious means tasting very good.",
        ),
        QAItem(
            "What is a goose?",
            "A goose is a large water bird with feathers, a long neck, and a loud honk.",
        ),
        QAItem(
            "Why should people investigate carefully?",
            "Careful investigation can reveal whether something frightening is truly dangerous or simply needs help.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a funny child-facing story containing a stench, a goon, and something delicious.",
        "Create a comedy in which a frightening goon is reinterpreted by a surprising twist.",
        "Tell a short story where conversation changes a chase into a rescue and ends with shared food.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.id}: location={entity.location}; "
            f"meters={meters}; memes={memes}; owner={entity.owner or 'none'}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
child(baker).
child(helper).
animal(goose).
food(delicious_food).
smells(stench).
suspected_goon(goose).
hungry(goose).
needs_help(goose).
shared_food(baker,helper).
shared_food(helper,goose).

real_goon(X) :- suspected_goon(X), not needs_help(X).
rescued(X) :- animal(X), needs_help(X), shared_food(helper,X).
twist_funny :- suspected_goon(goose), needs_help(goose), rescued(goose).
good_ending :- twist_funny, shared_food(baker,helper), shared_food(helper,goose).

#show real_goon/1.
#show rescued/1.
#show twist_funny/0.
#show good_ending/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("child", "baker"),
            asp.fact("child", "helper"),
            asp.fact("animal", "goose"),
            asp.fact("food", "delicious_food"),
            asp.fact("smells", "stench"),
            asp.fact("suspected_goon", "goose"),
            asp.fact("hungry", "goose"),
            asp.fact("needs_help", "goose"),
            asp.fact("shared_food", "baker", "helper"),
            asp.fact("shared_food", "helper", "goose"),
        ]
    )


def asp_program(show: Optional[str] = None) -> str:
    selected = show or "#show twist_funny/0."
    return f"{asp_facts()}\n{ASP_RULES}\n{selected}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show twist_funny/0.\n#show good_ending/0."))
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    names = {symbol.name for symbol in model}
    if {"twist_funny", "good_ending"} <= names:
        sample = generate(
            StoryParams("Luna", "Milo", seed=7, twist="goose", variation=7)
        )
        required = ("stench", "goon", "delicious")
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP and Python agree on the comic twist.")
            return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


CURATED = [
    StoryParams("Luna", "Milo", twist="goose", variation=11),
    StoryParams("Cora", "Pip", twist="goose", variation=22),
    StoryParams("Nina", "Otto", twist="goose", variation=33),
]


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


def generate(params: StoryParams) -> StorySample:
    twist = next(item for item in TWISTS if item.key == params.twist)
    world = setup_world(params, twist)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show twist_funny/0.\n#show good_ending/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            samples.append(generate(params))

    if args.asp:
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program())
            print("ASP model:")
            print(" ".join(str(symbol) for symbol in model))
        except ImportError:
            print("ASP mode unavailable: clingo is not installed.")
        if not args.json and not args.qa and not args.trace:
            return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print()
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
