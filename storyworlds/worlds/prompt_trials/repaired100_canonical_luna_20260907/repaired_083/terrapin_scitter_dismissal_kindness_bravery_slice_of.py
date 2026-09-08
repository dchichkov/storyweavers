#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a terrapin, a scitter, and a gentle
dismissal that is repaired through kindness and bravery.
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
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class Scenario:
    id: str
    setting: str
    dismissal: str
    clue: str
    repair: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    scenario_id: str = "garden_circle"
    telling_mode: str = "ordinary_morning"
    detail_id: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


SCENARIOS = {
    "garden_circle": Scenario(
        id="garden_circle",
        setting="the little garden circle behind the library",
        dismissal="Mara dismissed Pip's idea before he could finish explaining it",
        clue="Pip had noticed a thin trail of silver seed husks beside the empty flower pot",
        repair="Mara listened, followed the trail with Pip, and invited him to show the group what he had found",
        ending="the group planted the rescued seeds in a bright row, while Pip and Mara shared the watering can",
        lesson="kindness makes room for a quiet idea, and bravery helps someone offer it again",
    ),
    "bus_stop": Scenario(
        id="bus_stop",
        setting="the covered bus stop on a cool school morning",
        dismissal="Nell dismissed Pip's warning that the loose sign might fall",
        clue="Pip saw one bright screw resting on the bench below the sign",
        repair="Nell stopped, thanked Pip, and asked the driver to check the sign before anyone stood beneath it",
        ending="the sign was fastened safely, and Pip and Nell waited together under its steady blue roof",
        lesson="bravery can be a small clear warning, and kindness means taking it seriously",
    ),
    "laundry_room": Scenario(
        id="laundry_room",
        setting="the warm laundry room of the apartment house",
        dismissal="Nell dismissed Pip when he said one basket belonged to a neighbor who needed it",
        clue="Pip recognized a red mitten tucked beneath the folded towels",
        repair="Nell apologized, checked the name tag, and carried the basket to the right door with Pip",
        ending="the neighbor received the basket, and the red mitten warmed two grateful hands",
        lesson="kindness notices who might be missing, while bravery speaks before a mistake grows",
    ),
    "pond_shelf": Scenario(
        id="pond_shelf",
        setting="the wooden shelf beside the community pond",
        dismissal="Mara dismissed Pip's plan to move a fallen twig away from the ducklings",
        clue="Pip could see the twig caught across the narrow path to the water",
        repair="Mara crouched beside him, and together they moved it gently with a long stick",
        ending="the ducklings reached the pond, and the terrapin and scitter watched from the sunny shelf",
        lesson="a careful helping hand can be brave without being loud",
    ),
}

MODES = (
    "ordinary_morning",
    "quiet_start",
    "friend_first",
    "question_first",
)

OPENINGS = {
    "ordinary_morning": "It was an ordinary morning, the kind that begins with a cup, a path, and a small thing needing care.",
    "quiet_start": "The day began quietly, with soft feet, warm light, and a little work waiting nearby.",
    "friend_first": "'Good morning,' said {friend}, as {hero} carried a basket toward the day.",
    "question_first": "What can happen when someone is dismissed too quickly? {hero} was about to find out.",
}


def story_reasonable(scenario_id: str) -> bool:
    return scenario_id in SCENARIOS


def explain_rejection(scenario_id: str) -> str:
    return f"(No story: the scenario '{scenario_id}' is not part of this small slice-of-life world.)"


def tell(params: StoryParams) -> World:
    if not story_reasonable(params.scenario_id):
        raise StoryError(explain_rejection(params.scenario_id))
    scenario = SCENARIOS[params.scenario_id]
    mode = params.telling_mode if params.telling_mode in OPENINGS else MODES[0]
    world = World(scenario)

    terrapin = world.add(Entity("terrapin", "animal", params.hero_name))
    scitter = world.add(Entity("scitter", "animal", params.friend_name))
    terrapin.add_meter("steady_steps", 2)
    terrapin.add_meme("kindness", 1)
    scitter.add_meter("quick_steps", 2)
    scitter.add_meme("trust", 1)

    world.facts.update(
        terrapin=terrapin,
        scitter=scitter,
        setting=scenario.setting,
        dismissal=scenario.dismissal,
        clue=scenario.clue,
        repair=scenario.repair,
        ending=scenario.ending,
        lesson=scenario.lesson,
    )

    world.say(OPENINGS[mode].format(hero=terrapin.label, friend=scitter.label))
    world.say(
        f"In {scenario.setting}, {terrapin.label} the terrapin and {scitter.label} the scitter "
        "were doing an ordinary job together."
    )
    world.say(
        f"{terrapin.label} noticed something important: {scenario.clue}. "
        f"He took one brave breath and tried to explain."
    )
    world.say(f"But {scenario.dismissal}.")
    world.say(
        f"'I may be wrong,' said {terrapin.label}, 'but could we look once more?' "
        f"{scitter.label} answered, 'I will look with you.'"
    )
    world.say(
        f"The dismissal made {terrapin.label} feel small, but his Bravery did not vanish. "
        "He pointed carefully to the clue instead of giving up."
    )
    world.say(
        f"Then {scitter.label} used Kindness: {scenario.repair}. "
        "They checked the small fact together before deciding what to do."
    )
    world.say(
        f"'Thank you for telling me,' said {scitter.label}. "
        f"{terrapin.label} smiled. 'Thank you for listening.'"
    )
    world.say(
        f"By the end, {scenario.ending}. "
        f"They learned that {scenario.lesson}."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.scenario
    hero: Entity = world.facts["terrapin"]  # type: ignore[assignment]
    friend: Entity = world.facts["scitter"]  # type: ignore[assignment]
    return [
        f"Write a slice-of-life story about {hero.label} the terrapin and {friend.label} the scitter.",
        f"Include a dismissal caused by this moment: {scenario.dismissal}.",
        f"Show Kindness and Bravery repairing the problem after this clue: {scenario.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.scenario
    hero: Entity = world.facts["terrapin"]  # type: ignore[assignment]
    friend: Entity = world.facts["scitter"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.label} notice?",
            answer=f"{hero.label} noticed that {scenario.clue}.",
        ),
        QAItem(
            question=f"What dismissal happened to {hero.label}?",
            answer=f"{friend.label} dismissed {hero.label} when {scenario.dismissal.split(' dismissed ', 1)[1]}.",
        ),
        QAItem(
            question="How did Bravery appear in the story?",
            answer=f"Bravery appeared when {hero.label} took another breath and pointed carefully to the clue instead of giving up.",
        ),
        QAItem(
            question="How did Kindness help?",
            answer=f"Kindness helped when {scenario.repair}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {scenario.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a terrapin?",
            answer="A terrapin is a turtle-like animal that can live near water.",
        ),
        QAItem(
            question="What can dismissal mean?",
            answer="Dismissal can mean turning away an idea or concern before listening carefully.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is treating someone with care, respect, and attention.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing what seems right even when speaking or acting feels difficult.",
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
#show valid_scenario/1.
#show valid_story/1.

valid_scenario(S) :- scenario(S).
valid_story(S) :- valid_scenario(S), has_terrapin(S), has_scitter(S), has_kindness(S), has_bravery(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for scenario_id in SCENARIOS:
        lines.append(asp.fact("scenario", scenario_id))
        lines.append(asp.fact("has_terrapin", scenario_id))
        lines.append(asp.fact("has_scitter", scenario_id))
        lines.append(asp.fact("has_kindness", scenario_id))
        lines.append(asp.fact("has_bravery", scenario_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_scenarios() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_scenario/1."))
    return sorted(set(asp.atoms(model, "valid_scenario")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    asp_set = {row[0] for row in asp_valid_scenarios()}
    py_set = set(SCENARIOS)
    if asp_set != py_set:
        print("MISMATCH between ASP and Python:")
        print("ASP only:", sorted(asp_set - py_set))
        print("Python only:", sorted(py_set - asp_set))
        return 1
    for scenario_id in py_set:
        sample = generate(
            StoryParams(
                hero_name="Luna",
                friend_name="Scitter",
                scenario_id=scenario_id,
                seed=1,
            )
        )
        if not sample.story or "Luna" not in sample.story or "Scitter" not in sample.story:
            print(f"Generated story failed for {scenario_id}.")
            return 1
        if "Kindness" not in sample.story or "Bravery" not in sample.story:
            print(f"Feature coverage failed for {scenario_id}.")
            return 1
    print(f"OK: ASP gate matches Python registry ({len(py_set)} scenarios), and generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life terrapin and scitter storyworld about dismissal, Kindness, and Bravery."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--scenario", dest="scenario_id", choices=sorted(SCENARIOS))
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    scenario_id = getattr(args, "scenario_id", None) or rng.choice(list(SCENARIOS))
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Luna", "Milo", "Nia", "Pip", "Tessa"])
    friend_name = getattr(args, "friend_name", None) or rng.choice(["Scitter", "Mara", "Nell", "Toby", "Rae"])
    index = sample_seed if sample_seed is not None else rng.randrange(2**31)
    return StoryParams(
        hero_name=hero_name,
        friend_name=friend_name,
        scenario_id=scenario_id,
        telling_mode=MODES[(index // len(SCENARIOS)) % len(MODES)],
        detail_id=index % 7,
        seed=sample_seed,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"setting: {world.scenario.setting}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append("state: dismissal repaired through kindness and bravery")
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
    StoryParams("Luna", "Scitter", "garden_circle", "ordinary_morning", 0),
    StoryParams("Milo", "Mara", "bus_stop", "quiet_start", 1),
    StoryParams("Nia", "Nell", "laundry_room", "friend_first", 2),
    StoryParams("Pip", "Rae", "pond_shelf", "question_first", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("\n".join(str(item) for item in asp_valid_scenarios()))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
            if sample.story in seen:
                if attempt > args.n * 100:
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
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
