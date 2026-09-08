#!/usr/bin/env python3
"""
A small tall-tale ecosystem storyworld.

A curious child crawls through a brown meadow tunnel and discovers that the
whole little ecosystem is preparing for a storm. The exaggerated adventure is
grounded in state: curiosity reveals clues, foreshadowing prepares the child,
and a brave crawl helps protect the creatures.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
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


@dataclass
class Setting:
    place: str
    weather: str = "quiet morning"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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
    explorer_name: str
    helper_name: str
    ecosystem_name: str
    seed: Optional[int] = None
    crawl_route: Optional[str] = None
    telling_mode: Optional[str] = None


EXPLORERS = ["Luna", "Milo", "Tessa", "Bram", "Nia", "Otto"]
HELPERS = ["Pip", "Aunt Bea", "Ravi", "Grandpa Sol", "Wren"]
ECOSYSTEMS = ["the Brownroot Hollow", "the Chestnut Crawl", "the Russet Meadow"]
ROUTES = ["under the roots", "through the fern tunnel", "beside the sleepy stream"]
MODES = ["question", "warning", "discovery", "counting"]


@dataclass(frozen=True)
class Tale:
    id: str
    opening: str
    foreshadow: str
    clue: str
    danger: str
    giant_claim: str
    repair: str
    ending: str
    creature: str


TALES = [
    Tale(
        "root_rain",
        "A brown root rose from the meadow like a bridge built by a sleeping giant.",
        "Three leaves shivered even though the morning air was still.",
        "A line of ants was carrying seeds uphill, away from the stream.",
        "The stream was about to leap its muddy bank.",
        "Luna crawled beneath the root so quickly that the earth seemed to scoot backward.",
        "She and Pip opened a safe channel with twigs, stones, and one enormous spoon.",
        "The flood curled harmlessly around the hollow, while the ants marched home on a dry brown ridge.",
        "ants",
    ),
    Tale(
        "mushroom_thunder",
        "Brown mushrooms stood in a ring, each one wide enough to shade a wagon.",
        "The mushrooms had folded their caps before a single cloud appeared.",
        "A beetle tapped twice on every stem and then hurried toward a high log.",
        "Thunder was gathering beyond the hill.",
        "Luna crawled beneath the mushroom ring and warned every beetle, worm, and cricket.",
        "Pip tied bright grass flags along the high path so the small creatures could find shelter.",
        "When the thunder rolled, the ecosystem tucked itself safely beneath the log, and the mushrooms opened like umbrellas afterward.",
        "beetles",
    ),
    Tale(
        "wind_grass",
        "The brown grass bent in one long wave, although there was no wind Luna could feel.",
        "A feather spun in circles and landed pointing toward the old stone wall.",
        "Tiny spiders had strengthened their webs on the wall's sheltered side.",
        "A great gust was racing across the plain.",
        "Luna crawled low enough to make a tunnel in the grass, and the gust sailed over her like a silver whale.",
        "She and her helper placed fallen sticks beside the wall to make safe bridges for the snails.",
        "The wind roared past, but the little ecosystem held together behind its new wall of sticks.",
        "snails",
    ),
    Tale(
        "dry_sun",
        "The brown hill was so warm that a lizard claimed it was the sun's doorstep.",
        "Every flower turned its face toward one shaded stone.",
        "A bee circled the stone, then disappeared through a crack where cool soil breathed.",
        "The afternoon heat would soon become too strong.",
        "Luna crawled through the crack and discovered a hidden underground garden.",
        "She and Pip made a leaf roof over the entrance and carried drops of water in acorn cups.",
        "At sunset, the ecosystem glimmered under its leaf roof, and the lizard admitted the hill was only almost the sun's doorstep.",
        "bees",
    ),
    Tale(
        "moon_mud",
        "The brown mud held footprints so large that Luna suspected a moon had walked there.",
        "The newest prints filled with clear water before the sky had begun to darken.",
        "Frogs were moving their eggs from the low puddle to a high patch of moss.",
        "Night rain would drown the low nursery.",
        "Luna crawled along the prints and found a hollow leading to the mossy bank.",
        "With Pip, she built a tiny mud dam and guided the water around the eggs.",
        "By moonrise, the frogs sang from safe moss, and the giant footprints belonged only to a very ordinary heron.",
        "frogs",
    ),
]

TALE_BY_ID = {t.id: t for t in TALES}


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xC0B4A)
    material = "|".join(
        [params.explorer_name, params.helper_name, params.ecosystem_name,
         params.crawl_route or "", params.telling_mode or ""]
    )
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(material)))


def _sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:]


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    tale = TALE_BY_ID.get(params.crawl_route or "") or rng.choice(TALES)
    route = params.crawl_route if params.crawl_route in ROUTES else rng.choice(ROUTES)
    mode = params.telling_mode if params.telling_mode in MODES else rng.choice(MODES)

    world = World(Setting("the Brownroot ecosystem"))
    explorer = world.add(Entity(params.explorer_name, "character", "child", params.explorer_name))
    helper = world.add(Entity(params.helper_name, "character", "helper", params.helper_name))
    habitat = world.add(Entity("habitat", "place", "ecosystem", params.ecosystem_name))
    creature = world.add(Entity("creatures", "animal", "community", tale.creature))
    root = world.add(Entity("root", "thing", "root", "brown root"))

    explorer.memes.update(curiosity=1.0, courage=0.0, attention=0.0)
    helper.memes["trust"] = 1.0
    habitat.meters.update(safety=0.0, water=1.0)
    creature.meters["safety"] = 0.0
    root.meters["height"] = 3.0

    openings = {
        "question": f'"Why is the brown ground whispering?" {params.explorer_name} asked at the edge of {params.ecosystem_name}.',
        "warning": f"{params.explorer_name} entered {params.ecosystem_name} just before the brown grass gave a warning shiver.",
        "discovery": f"{params.explorer_name} discovered {params.ecosystem_name} beneath a brown hill that looked small from far away.",
        "counting": f"{params.explorer_name} counted one brown root, two beetles, and three odd shadows before the ecosystem surprised everyone.",
    }
    world.say(openings[mode])
    world.say(f"The curious child wanted to {route}, although the root was tall enough to make a grown-up duck.")
    world.para()

    explorer.memes["curiosity"] += 1
    world.say(f'"Curiosity can be useful if it keeps its eyes open," {params.helper_name} said.')
    world.say(f'"Then I will keep my eyes open and my knees low," said {params.explorer_name}.')
    world.say(f"That was wise, because {tale.foreshadow}")
    world.say(f"The first clue was plain: {tale.clue}.")
    world.para()

    explorer.memes["attention"] = 1.0
    explorer.memes["courage"] = 1.0
    world.say(f"{params.explorer_name} and {params.helper_name} followed the clue into {tale.danger.lower()}.")
    world.say(f"The child began to crawl. The crawl was so steady that even a sleepy worm lifted its head to watch.")
    world.say(f"At the end of the trail, they found the {tale.creature} of the ecosystem gathered together.")
    world.say(f'"We should help before the trouble arrives," said {params.explorer_name}.')
    world.say(f'"That is the tallest idea you have had all morning," {params.helper_name} replied.')
    world.say(tale.giant_claim)
    world.para()

    habitat.meters["safety"] = 1.0
    creature.meters["safety"] = 1.0
    explorer.memes["courage"] = 2.0
    world.say(f"They did not simply stare at the danger. {tale.repair}.")
    world.say(f"The small ecosystem changed because the clues had changed their plan: they used the high path, the sheltered place, and the careful crawl.")
    world.say(tale.ending)
    world.say(f"{params.explorer_name} went home muddy, proud, and still curious, but now the brown hollow had one more protector.")
    world.facts.update(
        explorer=explorer,
        helper=helper,
        habitat=habitat,
        creature=creature,
        root=root,
        tale=tale,
        route=route,
        mode=mode,
        place=world.setting.place,
        solved=True,
        foreshadowing=tale.foreshadow,
        danger=tale.danger,
        repair=tale.repair,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale = f["tale"]
    return [
        f"Write a child-facing Tall Tale about {f['explorer'].id} exploring {f['place']} and crawling {f['route']}.",
        f"Include Curiosity and Foreshadowing: begin with {tale.foreshadow} and let the clue reveal {tale.danger}.",
        f"Show how {f['explorer'].id} and {f['helper'].id} protect the {tale.creature} ecosystem, then end with a concrete image of safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tale = f["tale"]
    return [
        QAItem(
            f"Why did {f['explorer'].id} crawl through the ecosystem?",
            f"{f['explorer'].id} crawled to follow the clue and reach the {tale.creature} before {tale.danger.lower()}.",
        ),
        QAItem(
            "What foreshadowed the trouble?",
            f"The warning was that {tale.foreshadow} This showed that the ecosystem was changing before the main danger arrived.",
        ),
        QAItem(
            "How did curiosity help?",
            f"Curiosity made the child notice that {tale.clue} instead of walking past it. That clue changed the plan from guessing to helping.",
        ),
        QAItem(
            "What happened to the ecosystem?",
            f"{tale.repair}. As a result, the {tale.creature} found safety and the ecosystem remained together.",
        ),
        QAItem(
            "What did the child learn?",
            "The child learned that curiosity is strongest when it pays attention, listens to warnings, and leads to helpful action.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an ecosystem?", "An ecosystem is a community of living things and the place where they depend on one another."),
        QAItem("What does crawl mean?", "To crawl means to move close to the ground using hands, knees, or many small legs."),
        QAItem("What is foreshadowing?", "Foreshadowing is an early hint that prepares us for something that happens later."),
        QAItem("What is curiosity?", "Curiosity is the wish to learn or find out more about something."),
        QAItem("What color was central to this story?", "Brown was central because the brown roots, soil, grass, and hollow helped describe the ecosystem."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    lines = ["--- world model ---", f"setting: {world.setting.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: route={world.facts['route']}, solved={world.facts['solved']}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "brown_ecosystem"),
            asp.fact("feature", "curiosity"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("action", "crawl"),
            asp.fact("community", "ecosystem"),
            asp.fact("color", "brown"),
            asp.fact("action", "protect"),
        ]
    )


ASP_RULES = r"""
observant :- feature(curiosity), feature(foreshadowing).
explorer_ready :- action(crawl), observant.
ecosystem_present :- community(ecosystem), color(brown).
protected :- action(protect), explorer_ready, ecosystem_present.
valid_story :- protected.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm validity.")
        return 1
    try:
        sample = generate(StoryParams("Luna", "Pip", "the Brownroot Hollow", seed=88))
        if not sample.story or "ecosystem" not in sample.story.lower() or "crawl" not in sample.story.lower():
            print("MISMATCH: generated story failed required narrative checks.")
            return 1
    except Exception as exc:
        print(f"MISMATCH: generated story failed: {exc}")
        return 1
    print("OK: ASP twin and generated story agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tall Tale ecosystem crawl storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--ecosystem")
    parser.add_argument("--route")
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    route = args.route or rng.choice(ROUTES)
    if route not in ROUTES:
        raise StoryError(f"unknown crawl route: {route}")
    return StoryParams(
        explorer_name=args.name or rng.choice(EXPLORERS),
        helper_name=args.helper or rng.choice(HELPERS),
        ecosystem_name=args.ecosystem or rng.choice(ECOSYSTEMS),
        crawl_route=route,
        telling_mode=args.mode or rng.choice(MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.explorer_name.strip():
        raise StoryError("explorer_name must not be empty")
    if not params.helper_name.strip():
        raise StoryError("helper_name must not be empty")
    if not params.ecosystem_name.strip():
        raise StoryError("ecosystem_name must not be empty")
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Pip", "the Brownroot Hollow", crawl_route="root_rain", seed=101),
    StoryParams("Milo", "Aunt Bea", "the Chestnut Crawl", crawl_route="mushroom_thunder", seed=202),
    StoryParams("Nia", "Wren", "the Russet Meadow", crawl_route="wind_grass", seed=303),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
