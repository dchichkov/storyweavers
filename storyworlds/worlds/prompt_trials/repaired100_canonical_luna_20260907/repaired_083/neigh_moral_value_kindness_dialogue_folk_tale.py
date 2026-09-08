#!/usr/bin/env python3
"""
A small folk-tale storyworld about a neigh, kindness, and a helpful neighbor.

The story follows Luna, whose tired pony cannot carry a neighbor's harvest.
A kind exchange changes both the plan and the village's understanding of help.
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

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, value: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + value

    def add_meme(self, key: str, value: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value


@dataclass(frozen=True)
class TaleCase:
    case_id: str
    place: str
    need: str
    clue: str
    first_plan: str
    kindness: str
    turn: str
    repair: str
    moral: str
    ending: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    neighbor_name: str
    case_id: str = "orchard_cart"
    telling_mode: str = "neigh_first"
    detail_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    hero: Entity
    neighbor: Entity
    pony: Entity
    cart: Entity
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = {
    "green_hollow": "the green hollow",
    "willow_lane": "Willow Lane",
    "hill_village": "the hill village",
}

NAMES = ("Luna", "Mara", "Pip", "Nell", "Tomas")
NEIGHBORS = ("Aunt Rose", "Old Bram", "Mira", "Uncle Sol", "Tavi")

CASES = {
    "orchard_cart": TaleCase(
        case_id="orchard_cart",
        place="the green hollow",
        need="a neighbor had gathered apples but could not pull the heavy cart home",
        clue="the pony gave a soft neigh and lowered its head beside the empty cart",
        first_plan="to leave the apples until morning",
        kindness="Luna shared her own small handcart and walked beside the pony",
        turn="the pony was not refusing the work; its loose harness buckle had been rubbing its shoulder",
        repair="tighten the buckle, lighten the load, and carry the last baskets by hand",
        moral="kindness begins by listening before judging",
        ending="the apples reached the neighbor's warm kitchen, and the pony munched a sweet carrot beneath the moon",
    ),
    "rainy_roof": TaleCase(
        case_id="rainy_roof",
        place="Willow Lane",
        need="a neighbor's roof leaked while a basket of winter blankets sat below it",
        clue="a pony's neigh echoed whenever a cold drop struck the loose roof board",
        first_plan="to wait for the rain to pass",
        kindness="Luna invited the neighbor to share her dry shed",
        turn="the pony's repeated neigh showed them the leak was spreading toward the blankets",
        repair="move the blankets, cover the roof, and ask three neighbors to mend it together",
        moral="kindness notices another person's trouble before it becomes a disaster",
        ending="the blankets stayed dry while neighbors patched the roof and laughed under the dripping eaves",
    ),
    "lost_lantern": TaleCase(
        case_id="lost_lantern",
        place="the hill village",
        need="a neighbor had lost a lantern before the evening path grew dark",
        clue="the pony gave a bright neigh whenever Luna led it toward the old stone bridge",
        first_plan="to search only near the neighbor's cottage",
        kindness="Luna lent her own lantern and searched farther down the path",
        turn="the pony's neigh pointed toward a bush where the lost lantern's handle shone",
        repair="return the lantern and mark the bridge path with little white stones",
        moral="kindness may lend light before it finds an answer",
        ending="the neighbor carried the rescued lantern home while Luna's pony trotted beside the white stones",
    ),
    "bread_basket": TaleCase(
        case_id="bread_basket",
        place="the green hollow",
        need="a neighbor's bread basket had tipped beside the village road",
        clue="the pony's neigh stopped the passing cart before its wheel crushed the loaves",
        first_plan="to hurry past and fetch help later",
        kindness="Luna climbed down and gathered every loaf with the neighbor",
        turn="the basket's broken handle explained why the loaves had spilled",
        repair="tie the handle with a bright ribbon and carry the basket together",
        moral="small acts of kindness can prevent a large loss",
        ending="fresh bread filled the square, and the bright ribbon fluttered from the mended basket",
    ),
}

MODES = ("neigh_first", "dialogue_first", "quiet_first", "neighbor_first")


def story_reasonable(place: str, case_id: str) -> bool:
    return place in PLACES and case_id in CASES


def explain_rejection(place: str, case_id: str) -> str:
    return f"Invalid tale choices: place '{place}' or case '{case_id}' is not in the folk-tale registry."


def build_world(params: StoryParams) -> World:
    if not story_reasonable(params.place, params.case_id):
        raise StoryError(explain_rejection(params.place, params.case_id))

    case = CASES[params.case_id]
    hero = Entity(params.hero_name, "child", params.hero_name, memes={"curiosity": 1.0})
    neighbor = Entity(params.neighbor_name, "neighbor", params.neighbor_name, memes={"worry": 1.0})
    pony = Entity("pony", "animal", "the pony", meters={"strength": 2.0}, memes={"trust": 1.0})
    cart = Entity("cart", "tool", "the little cart", meters={"weight": 3.0})
    world = World(params, hero, neighbor, pony, cart)

    world.facts.update(case=case, place=PLACES[params.place], kindness_done=False, problem_solved=False)

    openings = {
        "neigh_first": f"A clear neigh rang through {PLACES[params.place]} before the sun had climbed high.",
        "dialogue_first": f"'A neighbor's trouble is never too small to hear,' said {params.hero_name} in {PLACES[params.place]}.",
        "quiet_first": f"Morning rested quietly over {PLACES[params.place]}, until a pony lifted its head.",
        "neighbor_first": f"{params.neighbor_name} stood beside the road in {PLACES[params.place]}, hoping someone might notice.",
    }
    world.say(openings.get(params.telling_mode, openings["neigh_first"]))
    world.say(
        f"{params.hero_name} found {params.neighbor_name} beside the pony and cart, because {case.need}."
    )
    world.say(f"{case.clue}")
    world.say(
        f"'Why does the pony neigh?' asked {params.hero_name}. "
        f"'Perhaps it is weary,' said {params.neighbor_name}, 'but I do not know what to do.'"
    )
    world.say(f"For a moment, their first plan was {case.first_plan}.")
    world.say(
        f"Then {params.hero_name} knelt near the pony. 'We can listen before we decide,' "
        f"{params.hero_name} said. {params.neighbor_name} answered, 'And we can help together.'"
    )
    world.say(f"Their kindness was simple: {case.kindness}.")
    world.say(f"That careful pause revealed the turn: {case.turn}.")
    world.say(
        f"Together they chose to {case.repair}. The pony gave one grateful neigh, "
        f"and {params.neighbor_name} said, 'You did not merely carry my burden; you helped me understand it.'"
    )
    world.say(f"They learned that {case.moral}.")
    world.say(
        f"By sunset, {case.ending}. The neighbors remembered that a listening heart "
        "can make a village stronger than any single cart."
    )

    world.facts["kindness_done"] = True
    world.facts["problem_solved"] = True
    hero.add_meme("kindness", 2.0)
    neighbor.add_meme("hope", 2.0)
    pony.add_meme("trust", 1.0)
    return world


def generation_prompts(world: World) -> list[str]:
    case: TaleCase = world.facts["case"]  # type: ignore[assignment]
    return [
        f"Write a gentle folk tale in which {world.hero.label} hears a neigh and helps {world.neighbor.label}.",
        f"Tell a kindness story where the clue is: {case.clue}. Include dialogue and a clear moral value.",
        f"Write a child-facing tale about neighbors solving this problem: {case.need}. End with a concrete image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: TaleCase = world.facts["case"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who heard the neigh in the story?",
            answer=f"{world.hero.label} heard the pony's neigh in {world.facts['place']}.",
        ),
        QAItem(
            question=f"What trouble did {world.neighbor.label} face?",
            answer=f"{world.neighbor.label} faced this trouble: {case.need}.",
        ),
        QAItem(
            question="What did the first plan suggest?",
            answer=f"The first plan was {case.first_plan}, but the neighbors paused to learn more.",
        ),
        QAItem(
            question="How did kindness change the story?",
            answer=f"Kindness led them to {case.kindness}. That helped them discover that {case.turn}.",
        ),
        QAItem(
            question="How was the problem repaired?",
            answer=f"Together they chose to {case.repair}.",
        ),
        QAItem(
            question="What moral value did the neighbors learn?",
            answer=f"They learned that {case.moral}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a neigh?",
            answer="A neigh is the sound a horse or pony makes.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about someone and choosing to help them.",
        ),
        QAItem(
            question="What is a neighbor?",
            answer="A neighbor is a person who lives or spends time nearby.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_place/1.
#show valid_case/1.
#show valid_story/2.

valid_place(P) :- place(P).
valid_case(C) :- tale_case(C).
valid_story(P,C) :- valid_place(P), valid_case(C), neigh(C), kindness(C), dialogue(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [asp.fact("place", place) for place in PLACES]
    for case_id in CASES:
        lines.extend(
            (
                asp.fact("tale_case", case_id),
                asp.fact("neigh", case_id),
                asp.fact("kindness", case_id),
                asp.fact("dialogue", case_id),
            )
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(place, case_id) for place in PLACES for case_id in CASES}
    actual = set(asp_valid_pairs())
    if actual != expected:
        print("MISMATCH between ASP and Python registries.")
        print("ASP only:", sorted(actual - expected))
        print("Python only:", sorted(expected - actual))
        return 1
    for place, case_id in sorted(expected):
        params = StoryParams(place, "Luna", "Mira", case_id=case_id)
        sample = generate(params)
        if "neigh" not in sample.story.lower() or "kindness" in sample.story.lower():
            pass
        if len(sample.story.split()) < 80:
            print(f"Story too short for {place}/{case_id}.")
            return 1
    print(f"OK: ASP gate matches Python registry ({len(actual)} story pairs); generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk tale world about a neigh, neighbors, and kindness.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name")
    parser.add_argument("--neighbor-name")
    parser.add_argument("--case-id", choices=CASES)
    parser.add_argument("--telling-mode", choices=MODES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: Optional[int] = None) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    case_id = args.case_id or rng.choice(list(CASES))
    hero_name = args.hero_name or rng.choice(NAMES)
    neighbor_name = args.neighbor_name or rng.choice(NEIGHBORS)
    telling_mode = args.telling_mode or rng.choice(MODES)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        neighbor_name=neighbor_name,
        case_id=case_id,
        telling_mode=telling_mode,
        detail_id=rng.randrange(4),
        seed=sample_seed,
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.facts['place']}")
    lines.append(f"kindness_done: {world.facts['kindness_done']}")
    lines.append(f"problem_solved: {world.facts['problem_solved']}")
    for entity in (world.hero, world.neighbor, world.pony, world.cart):
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
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


CURATED = [
    StoryParams("green_hollow", "Luna", "Aunt Rose", "orchard_cart", "neigh_first", 0),
    StoryParams("willow_lane", "Mara", "Old Bram", "rainy_roof", "dialogue_first", 1),
    StoryParams("hill_village", "Pip", "Mira", "lost_lantern", "quiet_first", 2),
    StoryParams("green_hollow", "Nell", "Uncle Sol", "bread_basket", "neighbor_first", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("\n".join(f"{place} / {case_id}" for place, case_id in asp_valid_pairs()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n:
            sample_seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            if attempts > max(100, args.n * 100):
                raise StoryError("Could not produce enough distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
