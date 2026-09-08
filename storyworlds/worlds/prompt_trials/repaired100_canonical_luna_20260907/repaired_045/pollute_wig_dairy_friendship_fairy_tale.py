#!/usr/bin/env python3
"""
A child-friendly fairy-tale storyworld about friendship, a polluted dairy spring,
and a wig that helps reveal the truth.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    friend: str
    trickster: str
    village: str
    wig: str
    dairy: str
    seed: Optional[int] = None
    variant: int = 0
    telling_mode: int = 0


HERO_NAMES = ["Luna", "Mira", "Nell", "Poppy", "Tessa", "Wren"]
FRIEND_NAMES = ["Bram", "Finn", "Ollie", "Pip", "Rowan", "Theo"]
TRICKSTER_NAMES = ["Muddlewitch", "Lady Lark", "Grumble Goblin", "Crumble Crow"]
VILLAGES = ["Moonbell", "Daisy Hollow", "Silvermead", "Clover Glen"]
WIGS = ["a silver moon wig", "a curly gold wig", "a blue feather wig", "a red velvet wig"]
DAIRIES = ["the Moonmilk Dairy", "the Clover Dairy", "the Sunrise Dairy", "the Bellflower Dairy"]

OPENINGS = [
    "Once upon a time, in {village}, {hero} wore a {wig_plain} and helped at {dairy}.",
    "In the fairy-tale village of {village}, {hero} and {friend} were known for sharing every chore at {dairy}.",
    "Beyond seven green hills stood {village}, where {hero} kept watch over the bright white bells of {dairy}.",
    "At dawn in {village}, {hero} brushed a {wig_plain} while {friend} carried milk from {dairy}.",
    "The people of {village} trusted {hero} and {friend}, for their friendship was warmer than fresh milk from {dairy}.",
]

DIALOGUES = [
    '"The stream smells strange," said {friend}. "Then we must find what caused it," said {hero}.',
    '"Should we run to the castle?" asked {hero}. "Together," answered {friend}. "First we look, then we act."',
    '"I cannot lift the old gate alone," said {hero}. "You do not have to," said {friend}. "Friends make one strong team."',
    '"The wig is only a disguise," whispered {friend}. "But friendship helps us see clearly," replied {hero}.',
    '"I am frightened," said {friend}. "So am I," said {hero}, "but we can still help each other."',
]

ENDING_LINES = [
    "From that day on, the dairy kept a clean-water bell, and the friends rang it whenever someone needed help.",
    "The village planted blue flowers beside the stream, and every child remembered that friendship can mend what carelessness harms.",
    "The queen gave them a silver bucket, but the friends treasured their joined hands even more.",
    "At sunset, clean milk flowed again, and the two friends shared a warm cup beneath the old willow.",
    "The wig became a silly festival hat, while the dairy became famous for kindness as well as cheese.",
]


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fairy-tale storyworld about dairy, pollution, wigs, and friendship.")
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--trickster")
    parser.add_argument("--village")
    parser.add_argument("--wig")
    parser.add_argument("--dairy")
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


def generate_world(params: StoryParams) -> World:
    world = World(params.village)
    world.add(Entity("hero", "character", params.hero, memes={"Friendship": 0.5}))
    world.add(Entity("friend", "character", params.friend, memes={"Friendship": 0.5}))
    world.add(Entity("trickster", "character", params.trickster))
    world.add(Entity("wig", "thing", params.wig, owner="hero"))
    world.add(Entity("dairy", "place", params.dairy, meters={"cleanliness": 0.8}))
    world.add(Entity("stream", "place", "the milk-white stream", meters={"cleanliness": 0.7}))
    world.add(Entity("bucket", "thing", "the silver cleaning bucket"))
    return world


def tell(world: World, params: StoryParams) -> World:
    rng = random.Random((params.seed or 0) ^ params.variant ^ 0xD41RY)
    hero = world.get("hero")
    friend = world.get("friend")
    trickster = world.get("trickster")
    wig = world.get("wig")
    dairy = world.get("dairy")
    stream = world.get("stream")

    wig_plain = params.wig
    if wig_plain.startswith(("a ", "an ", "the ")):
        wig_plain = wig_plain[2:] if wig_plain.startswith(("a ", "an ")) else wig_plain[4:]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)].format(
        village=params.village,
        hero=params.hero,
        friend=params.friend,
        wig_plain=wig_plain,
        dairy=params.dairy,
    )

    world.say(opening)
    world.say(
        f"One morning, the cows would not drink, because dark foam had begun to pollute the stream beside {params.dairy}."
    )
    world.say(
        f"{params.hero} saw a muddy trail leading from the stream to an old stone shed, while {params.friend} noticed that the dairy's clean-water wheel had stopped."
    )

    world.para()
    world.say(rng.choice(DIALOGUES).format(hero=params.hero, friend=params.friend))
    world.say(
        f"Inside the shed, the friends found {params.trickster} wearing {params.wig} and hiding a sack of bitter black powder."
    )
    world.say(
        f'"I only wanted a grand disguise," admitted {params.trickster}. "I poured the powder into the stream so no one would see me take the dairy bell."'
    )
    world.say(
        f"{params.hero} did not shout. Instead, {params.friend} held the wig steady while {params.hero} followed the powder trail back to the broken wheel."
    )
    world.say(
        f"They discovered the real danger: the wheel was jammed by a thorny vine, so fresh water could not wash the polluting powder away."
    )

    world.para()
    world.say(
        f'"We can free the wheel, but I need you to hold this gate," said {params.hero}. "{params.friend} smiled. "And I need you to trust me."'
    )
    world.say(
        f"{params.friend} used the silly wig as a soft cushion beneath the gate while {params.hero} pulled the vine loose with both hands."
    )
    world.say(
        f"Clean water rushed through the channel, carrying the dark foam into a waiting clay basin instead of farther down the valley."
    )
    world.say(
        f"{params.trickster} helped scoop the polluted water safely into the basin and returned the dairy bell."
    )
    world.say(
        f"By working side by side, {params.hero} and {params.friend} protected the cows, the stream, and every family that depended on the dairy."
    )

    world.para()
    world.say(
        f'"I thought a disguise would make me important," said {params.trickster}. "Now I know that helping others is a better kind of magic."'
    )
    world.say(
        f"{params.hero} and {params.friend} forgave the trickster, but they also taught {params.trickster} how to check the water before anyone drank it."
    )
    world.say(rng.choice(ENDING_LINES))

    dairy.meters["cleanliness"] = 1.0
    stream.meters["cleanliness"] = 1.0
    wig.owner = "village"
    hero.memes["Friendship"] = 1.0
    friend.memes["Friendship"] = 1.0
    trickster.memes["Accountability"] = 1.0
    world.fired.update({"pollution_discovered", "dairy_restored", "friendship_proved"})

    world.facts = {
        "hero": params.hero,
        "friend": params.friend,
        "trickster": params.trickster,
        "village": params.village,
        "wig": params.wig,
        "dairy": params.dairy,
        "pollution": "bitter black powder polluted the stream",
        "cause": f"{params.trickster} poured bitter black powder into the stream while hiding the dairy bell",
        "solution": f"{params.friend} held the gate with the wig while {params.hero} freed the water wheel",
        "lesson": "Friendship means trusting one another and helping repair harm.",
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy tale about {f['hero']} and {f['friend']} proving Friendship while saving {f['dairy']}.",
        f"Tell a child-friendly story in {f['village']} where {f['wig']} becomes useful during a polluted-stream rescue.",
        f"Write a fairy tale involving dairy, a wig, pollution, dialogue, and this lesson: {f['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who worked together in the fairy tale?",
            answer=f"{f['hero']} and {f['friend']} worked together because their friendship helped them solve the danger.",
        ),
        QAItem(
            question="What polluted the stream?",
            answer=f"The stream was polluted by bitter black powder that {f['trickster']} poured into it.",
        ),
        QAItem(
            question=f"How did the wig help {f['hero']} and {f['friend']}?",
            answer=f"{f['friend']} used {f['wig']} as a soft cushion beneath the gate while {f['hero']} freed the water wheel.",
        ),
        QAItem(
            question="What happened to the dairy?",
            answer=f"The friends restored the clean water at {f['dairy']}, so the cows and village families were safe again.",
        ),
        QAItem(
            question="How did the trickster make amends?",
            answer=f"{f['trickster']} helped collect the polluted water, returned the dairy bell, and learned to check the water before anyone drank it.",
        ),
        QAItem(
            question="What lesson did the friends prove?",
            answer=f"They proved that {f['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to pollute something?",
            answer="To pollute something means to make it dirty or unsafe by adding harmful waste or substances.",
        ),
        QAItem(
            question="What is dairy?",
            answer="Dairy refers to milk and foods made from milk, such as cheese, butter, and yogurt.",
        ),
        QAItem(
            question="What is a wig?",
            answer="A wig is hair made from cloth, thread, or other material that someone wears on the head as a covering or disguise.",
        ),
        QAItem(
            question="What is Friendship?",
            answer="Friendship is a caring bond in which people trust, help, and look after one another.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("virtue", "friendship"),
            asp.fact("danger", "pollution"),
            asp.fact("place", "dairy"),
            asp.fact("object", "wig"),
            asp.fact("repair", "clean_water"),
        ]
    )


ASP_RULES = r"""
safe_story :- virtue(friendship), danger(pollution), place(dairy), object(wig), repair(clean_water).
#show safe_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show safe_story/0."))
    atoms = set(asp.atoms(model, "safe_story"))
    expected = {()}
    if atoms == expected:
        print("OK: clingo friendship-and-repair gate matches Python.")
        return 0
    print("MISMATCH between clingo and Python.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(expected))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes} owner={entity.owner}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("== Generation prompts ==", sample.prompts),
            ("== Story questions ==", sample.story_qa),
            ("== World questions ==", sample.world_qa),
        ]:
            print(title)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def generate(params: StoryParams) -> StorySample:
    if not params.hero.strip() or not params.friend.strip():
        raise StoryError("hero and friend names must not be empty")
    if params.hero.casefold() == params.friend.casefold():
        raise StoryError("hero and friend must have different names")
    world = tell(generate_world(params), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Luna", "Bram", "Muddlewitch", "Moonbell", "a silver moon wig", "the Moonmilk Dairy", seed=11, variant=11),
    StoryParams("Mira", "Pip", "Lady Lark", "Daisy Hollow", "a curly gold wig", "the Clover Dairy", seed=29, variant=29, telling_mode=2),
    StoryParams("Poppy", "Theo", "Grumble Goblin", "Clover Glen", "a blue feather wig", "the Sunrise Dairy", seed=47, variant=47, telling_mode=4),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name.casefold() != hero.casefold()]
    return StoryParams(
        hero=hero,
        friend=args.friend or rng.choice(friend_choices),
        trickster=args.trickster or rng.choice(TRICKSTER_NAMES),
        village=args.village or rng.choice(VILLAGES),
        wig=args.wig or rng.choice(WIGS),
        dairy=args.dairy or rng.choice(DAIRIES),
        variant=rng.randrange(1_000_000_000),
        telling_mode=rng.randrange(len(OPENINGS)),
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
        print(format_json(samples))
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
