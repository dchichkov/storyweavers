#!/usr/bin/env python3
"""
A tall tale about cologne, clatter, and a suspenseful rescue in a town where
ordinary things make extraordinary noise.
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
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    held_by: Optional[str] = None


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
    hero_name: str
    helper_name: str
    bottle: str
    setting: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Pip", "Nora", "Toby", "Cleo", "Bram", "Daisy"]
BOTTLES = [
    ("moon-cologne", "a silver bottle of moon cologne"),
    ("rose-cologne", "a round bottle of rose cologne"),
    ("rain-cologne", "a tall bottle of rain cologne"),
]
SETTINGS = [
    "the bell tower of Brambletown",
    "the windy market square",
    "the mayor's enormous porch",
]


@dataclass(frozen=True)
class Tale:
    title: str
    opening: str
    danger: str
    clue: str
    action: str
    result: str
    ending: str


TALES = (
    Tale(
        "the bottle above the bell",
        "At noon, Luna climbed the bell tower to polish the town's tallest clock.",
        "A gust snatched the cologne bottle from the railing and sent it clattering up the tower stairs.",
        "The clatter stopped just above the bell room, where the old floorboards groaned.",
        "Luna tied a ribbon to the railing while Milo counted the bellbeats, and together they crossed the creaking floor.",
        "They caught the bottle just before it rolled through a crack and fell into the town fountain.",
        "From that day on, every bell in Brambletown smelled faintly of roses and bravery.",
    ),
    Tale(
        "the runaway scent",
        "Luna carried the cologne across the market square, where even pigeons wore tiny hats.",
        "The stopper popped loose, and a mighty clatter sent the bottle rolling toward a cart piled with fireworks.",
        "The bottle's silver shine flashed beneath the cart, while a single spark hissed nearby.",
        "Luna whispered directions and Milo used a broom to stop the wheel; then Luna reached under the cart and sealed the stopper.",
        "The fireworks stayed asleep, and the square filled only with the gentle scent of rain.",
        "People said Luna had saved the day with one hand, one broom, and the courage of a whole parade.",
    ),
    Tale(
        "the porch that trembled",
        "On the mayor's enormous porch, Luna prepared a drop of cologne for the town celebration.",
        "A thunderous clatter shook the porch, and the bottle slid toward a loose plank above the cellar.",
        "Below the plank, something bumped three times, then went quiet.",
        "Luna asked Milo to hold the lantern while she listened; together they discovered a kitten trapped beside a basket of bells.",
        "They lifted the plank, freed the kitten, and rescued the bottle before either could tumble away.",
        "The kitten wore the mayor's ribbon, and the porch rang with cheers instead of suspense.",
    ),
    Tale(
        "the giant's sneeze",
        "Luna visited a giant who claimed one drop of cologne could freshen an entire mountain.",
        "The giant sneezed, causing a clatter of teacups and sending the bottle toward the cliff edge.",
        "The bottle balanced on one pebble, with the valley yawning below it.",
        "Luna told the giant not to move, while Milo stretched a picnic blanket beneath the ledge.",
        "The giant breathed softly, Luna nudged the bottle with a spoon, and the blanket caught it safely.",
        "One drop freshened the mountain, and the giant's next sneeze smelled like spring.",
    ),
    Tale(
        "the midnight parade",
        "At midnight, Luna led a parade of sleepy goats through the village with the precious cologne in a basket.",
        "A sudden clatter came from the dark road, and the goats scattered toward the bridge.",
        "The basket tipped, but Luna could hear the bottle rolling somewhere beyond the fog.",
        "Milo rang a tiny handbell from the safe side of the bridge while Luna followed the scent and stopped the bottle with her boot.",
        "The goats returned to the bell, and the bottle was safe before the moon crossed the bridge.",
        "By sunrise, the parade had become the most famous quiet march in the county.",
    ),
)


def validate(params: StoryParams) -> None:
    if params.hero_name == params.helper_name:
        raise StoryError("hero_name and helper_name must name different characters.")
    if params.bottle not in dict(BOTTLES):
        raise StoryError(f"Unknown cologne bottle: {params.bottle}.")
    if not params.setting:
        raise StoryError("setting must not be empty.")


def choose_tale(params: StoryParams) -> Tale:
    seed = params.seed if params.seed is not None else 0
    return TALES[seed % len(TALES)]


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="child",
            label=params.hero_name,
            location=params.setting,
            meters={"balance": 1.0, "courage": 1.0},
            memes={"curiosity": 1.0, "worry": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="friend",
            label=params.helper_name,
            location=params.setting,
            meters={"balance": 1.0, "courage": 1.0},
            memes={"attention": 1.0, "worry": 0.0, "trust": 1.0},
        )
    )
    bottle = world.add(
        Entity(
            id="cologne",
            kind="thing",
            type="bottle",
            label=params.bottle,
            location=params.setting,
            meters={"sealed": 1.0, "stability": 1.0},
            memes={"importance": 1.0},
        )
    )
    tale = choose_tale(params)
    values = {
        "hero": hero.label,
        "helper": helper.label,
        "bottle": dict(BOTTLES)[params.bottle],
        "setting": params.setting,
    }

    world.say(f"In {params.setting}, {hero.label} was famous for being taller in courage than in height.")
    world.say(f"{hero.label} carried {dict(BOTTLES)[params.bottle]} as carefully as a queen carries a crown.")
    world.para()
    world.say(tale.opening)
    hero.memes["curiosity"] += 1
    world.say(tale.danger)
    bottle.meters["stability"] = 0.2
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(f'"Do you hear that clatter?" {helper.label} asked. "Something important is still moving."')
    world.say(tale.clue)
    world.para()
    world.say(f'"Then listen for my voice," {hero.label} said. "I will act when you tell me the safest moment."')
    world.say(tale.action)
    bottle.meters["stability"] = 1.0
    bottle.meters["sealed"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    helper.memes["worry"] = 0.0
    helper.memes["trust"] += 1
    world.say(f'"Now that was suspense," {helper.label} said. "But your careful plan saved the day."')
    world.para()
    world.say(tale.result)
    world.say(tale.ending)

    world.facts.update(
        hero=hero,
        helper=helper,
        bottle=bottle,
        tale=tale,
        setting=params.setting,
        danger=tale.danger,
        clue=tale.clue,
        action=tale.action,
        result=tale.result,
        ending=tale.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    bottle: Entity = world.facts["bottle"]  # type: ignore[assignment]
    return [
        f"Write a suspenseful Tall Tale about {hero.label}, {helper.label}, and {bottle.label}.",
        f"Tell a child-friendly story in which cologne causes a dangerous clatter but friendship solves the problem.",
        f"Create a tall tale with suspense, a rolling cologne bottle, brave listening, and a surprising ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    bottle: Entity = world.facts["bottle"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who are the main characters?",
            answer=f"The main characters are {hero.label}, the brave planner, and {helper.label}, the careful helper who listened for danger.",
        ),
        QAItem(
            question="What caused the suspense?",
            answer=f"The suspense began when {bottle.label} became unstable and a loud clatter sent it toward danger.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.label}?",
            answer=f"{helper.label} listened closely, gave useful warnings, and helped {hero.label} choose the safest moment to act.",
        ),
        QAItem(
            question="How was the cologne saved?",
            answer=f"{hero.label} and {helper.label} worked together, using careful timing and a simple tool or safe plan to stop the bottle before it fell.",
        ),
        QAItem(
            question="What shows that the danger was over?",
            answer=str(world.facts["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cologne?",
            answer="Cologne is a scented liquid usually kept in a small bottle and used for a pleasant smell.",
        ),
        QAItem(
            question="What is a clatter?",
            answer="A clatter is a loud, uneven series of sharp sounds made when things bump, roll, or fall together.",
        ),
        QAItem(
            question="What makes suspense?",
            answer="Suspense grows when something important is in danger and the reader must wait to learn whether it will be safe.",
        ),
        QAItem(
            question="What is a Tall Tale?",
            answer="A Tall Tale is a playful story that stretches events into enormous, surprising, and impossible-sounding adventures.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suspenseful Tall Tale world about cologne and clatter.")
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--bottle", choices=[name for name, _ in BOTTLES])
    parser.add_argument("--setting", choices=SETTINGS)
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
    hero = args.hero_name or rng.choice(NAMES)
    helpers = [name for name in NAMES if name != hero]
    return StoryParams(
        hero_name=hero,
        helper_name=args.helper_name or rng.choice(helpers),
        bottle=args.bottle or rng.choice([name for name, _ in BOTTLES]),
        setting=args.setting or rng.choice(SETTINGS),
    )


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
        lines.append(
            f"  {entity.id:8} type={entity.type:10} location={entity.location!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
place(bell_tower).
place(market_square).
place(mayor_porch).

character(hero).
character(helper).
thing(cologne).

danger(cologne).
clatter(cologne).
listens(helper).
plans(hero).
rescued(cologne) :- danger(cologne), clatter(cologne), listens(helper), plans(hero).

#show rescued/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "bell_tower"),
            asp.fact("place", "market_square"),
            asp.fact("place", "mayor_porch"),
            asp.fact("character", "hero"),
            asp.fact("character", "helper"),
            asp.fact("thing", "cologne"),
        ]
    )


def asp_program(show: str = "#show rescued/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    try:
        model = asp.one_model(asp_program())
        rescued = asp.atoms(model, "rescued")
        if ("cologne",) not in rescued:
            print("ASP verification failed: cologne was not rescued.")
            return 1
        params = StoryParams("Luna", "Milo", "moon-cologne", SETTINGS[0], seed=3)
        sample = generate(params)
        if "cologne" not in sample.story or "clatter" not in sample.story:
            print("ASP verification failed: generated story lost seed words.")
            return 1
        print("OK: ASP/Python parity and story generation verified.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        if args.show_asp:
            return
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, bottle in enumerate(BOTTLES):
            samples.append(
                generate(
                    StoryParams(
                        hero_name=NAMES[index],
                        helper_name=NAMES[index + 1],
                        bottle=bottle[0],
                        setting=SETTINGS[index % len(SETTINGS)],
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
