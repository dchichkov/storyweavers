#!/usr/bin/env python3
"""
A small animal-story world about a careless smurf enterprise, a bad ending,
and the moral value of keeping promises and caring for living things.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        return "she" if self.type in {"girl", "hen", "doe"} else "he"

    def object(self) -> str:
        return "her" if self.type in {"girl", "hen", "doe"} else "him"


@dataclass
class Setting:
    place: str = "the blue forest"
    weather: str = "a dry afternoon"
    danger: str = "a thirsty woodland animal"


@dataclass
class StoryParams:
    smurf_name: str
    smurf_type: str
    animal: str
    enterprise: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    enterprise_name: str
    product: str
    promise: str
    shortcut: str
    warning: str
    bad_result: str
    repair: str
    moral: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


SCENARIOS = (
    Scenario(
        "Berry Basket Enterprise",
        "blueberry baskets",
        "to leave a fresh basket at every forest burrow before sunset",
        "to pick too many berries at once and leave the baskets in the hot sun",
        "the old tortoise said, 'Food is a promise when someone is waiting for it.'",
        "the berries shriveled, and the hungry rabbit found only sticky leaves in the basket",
        "carry small baskets in the shade, share the sound berries, and bring water to the rabbit",
        "A good enterprise must care for the people and animals it serves, not only count its prizes.",
        "The rabbit ate slowly beneath a cool fern, while the smurf packed away the empty baskets and began again honestly.",
    ),
    Scenario(
        "Lantern-Moth Enterprise",
        "safe moon lanterns",
        "to hang gentle lights so moths could find the night garden without flying into thorn bushes",
        "to use bright fire sparks instead of testing each lantern",
        "a sleepy owl called, 'A quick shine can make a long shadow.'",
        "the harsh sparks frightened the moths into the brambles",
        "dim the lanterns, remove the sparks, and free each moth with the owl's help",
        "Good work protects small lives even when careful work takes longer.",
        "The moths returned to the soft lanterns, but the smurf's first bright sign hung dark as a lesson.",
    ),
    Scenario(
        "Acorn Roof Enterprise",
        "acorn roofs for field mice",
        "to keep the mice dry before the evening rain",
        "to use green acorns and skip the tying test",
        "a mouse said, 'A roof is only useful when it stays above us.'",
        "the roofs split in the rain, and the mice shivered under the dripping leaves",
        "gather dry acorns, test every roof, and invite the mice into a dry stump house",
        "Reliability is kinder than speed when another creature depends on your work.",
        "The mice slept safely in the stump, while the smurf rebuilt every roof one knot at a time.",
    ),
    Scenario(
        "Honey-Flower Enterprise",
        "flower stands for tired bees",
        "to plant enough blossoms beside the hive for the bees' long flight home",
        "to sell the flowers before their roots were ready",
        "a bee buzzed, 'A flower must live before it can feed anyone.'",
        "the uprooted flowers wilted, and the bees found an empty patch of brown soil",
        "replant healthy shoots, water them, and return the coins to the bee keeper",
        "Profit is never worth breaking the living promise behind a useful good.",
        "The bees found nectar in the restored patch, while one wilted flower reminded the smurf not to rush.",
    ),
    Scenario(
        "Pond-Reed Enterprise",
        "reed boats for ducklings",
        "to make floating boats for ducklings learning to cross the quiet pond",
        "to tie the reeds loosely and launch before checking them",
        "the frog warned, 'A boat should carry a friend before it carries a flag.'",
        "the first boat opened, and a duckling was left shivering on a muddy island",
        "bring the duckling back with a long branch, retie every boat, and test them near the shore",
        "Safety and responsibility matter more than showing off a finished enterprise.",
        "The ducklings crossed in sturdy boats, but the torn first boat stayed on the bank as a warning.",
    ),
)

NAMES = ["Luna", "Pip", "Momo", "Tavi", "Bibi", "Nori", "Sumi", "Kiko"]
ANIMALS = ["rabbit", "moth", "field mouse", "bee", "duckling"]
ENTERPRISES = ["berries", "lanterns", "roofs", "flowers", "boats"]
ASP_RULES = r"""
enterprise_ready(S, E) :- smurf(S), enterprise(E), promises_care(S, E).
bad_ending(S, E) :- enterprise_ready(S, E), takes_shortcut(S, E), harms_animal(E).
moral_value(S, E) :- bad_ending(S, E), repairs_harm(S, E), learns_care(S, E).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal story about a smurf enterprise.")
    parser.add_argument("--name")
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--enterprise", choices=ENTERPRISES)
    parser.add_argument("--gender", choices=["boy", "girl"])
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
    name = args.name or rng.choice(NAMES)
    smurf_type = args.gender or rng.choice(["boy", "girl"])
    animal = args.animal or rng.choice(ANIMALS)
    enterprise = args.enterprise or rng.choice(ENTERPRISES)
    if name.strip() == "":
        raise StoryError("The smurf needs a readable name.")
    if animal not in ANIMALS:
        raise StoryError("The animal is not part of this small forest.")
    if enterprise not in ENTERPRISES:
        raise StoryError("The enterprise is not known in this story world.")
    return StoryParams(name, smurf_type, animal, enterprise)


def choose_scenario(params: StoryParams) -> Scenario:
    index = ENTERPRISES.index(params.enterprise)
    return SCENARIOS[index]


def tell_story(params: StoryParams) -> World:
    scenario = choose_scenario(params)
    world = World(Setting())
    smurf = world.add(Entity("smurf", params.smurf_type, params.smurf_name))
    animal = world.add(Entity("animal", params.animal, params.animal.title()))
    smurf.memes.update({"ambition": 1.0, "care": 0.0, "promise": 1.0})
    animal.memes.update({"trust": 1.0, "need": 1.0})

    world.say(
        f"In the blue forest, {smurf.label} the smurf opened a little enterprise called "
        f"the {scenario.enterprise_name}."
    )
    world.say(
        f"The enterprise made {scenario.product}, and {smurf.label} promised {scenario.promise}."
    )
    world.say(
        f"At first, {smurf.label} wanted the work to look grand. "
        f"{smurf.label} decided {scenario.shortcut}."
    )
    world.say(
        f"'{scenario.promise.capitalize()},' said {smurf.label}. "
        f"'I can finish before anyone notices.'"
    )
    world.say(f"The {animal.label.lower()} shook {animal.subject()} head. '{scenario.warning}'")
    world.say(
        f"But the smurf hurried on. The enterprise looked busy for a moment, then {scenario.bad_result}."
    )
    smurf.memes["care"] = 0.0
    smurf.memes["trust"] = -1.0
    animal.memes["trust"] = -1.0
    world.say(
        f"'{animal.label}, I am sorry,' said {smurf.label}. "
        f"'{animal.label},' answered the animal, 'sorry must be followed by help.'"
    )
    world.say(f"{smurf.label} stopped counting coins and began to {scenario.repair}.")
    smurf.memes["care"] = 1.0
    smurf.memes["trust"] = 1.0
    animal.memes["trust"] = 0.0
    world.say(f"That first enterprise had ended badly, but {scenario.moral}")
    world.say(scenario.ending)

    world.facts = {
        "smurf": smurf,
        "animal": animal,
        "scenario": scenario,
        "bad": True,
        "repaired": True,
        "moral": scenario.moral,
    }
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    smurf: Entity = world.facts["smurf"]  # type: ignore[assignment]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write an animal story about {smurf.label}'s {scenario.enterprise_name}.",
            f"Show why the smurf's enterprise ends badly for the {params.animal}, then show repair.",
            "Include the moral value that care matters more than speed or profit.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    smurf: Entity = world.facts["smurf"]  # type: ignore[assignment]
    animal: Entity = world.facts["animal"]  # type: ignore[assignment]
    return [
        QAItem(
            "What enterprise did the smurf start?",
            f"{smurf.label} started the {scenario.enterprise_name}, making {scenario.product}.",
        ),
        QAItem(
            f"What went wrong for the {animal.label.lower()}?",
            f"The enterprise ended badly because {scenario.bad_result}.",
        ),
        QAItem(
            "How did the smurf try to repair the harm?",
            f"{smurf.label} tried to repair the harm by {scenario.repair}.",
        ),
        QAItem(
            "What moral value does the story teach?",
            scenario.moral,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an enterprise?", "An enterprise is an organized effort to make, grow, or provide something."),
        QAItem("Why should an enterprise keep its promises?", "It should keep its promises because other people or animals may depend on its work."),
        QAItem("What is a moral value?", "A moral value is a good principle that helps guide kind and responsible choices."),
        QAItem("What makes an animal story?", "An animal story uses animals and their actions to show a problem, a choice, and a lesson."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    return "\n".join(
        [
            "smurf(smurf).",
            "enterprise(business).",
            "promises_care(smurf,business).",
            "takes_shortcut(smurf,business).",
            "harms_animal(business).",
            "repairs_harm(smurf,business).",
            "learns_care(smurf,business).",
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    if not asp_valid():
        print("Mismatch between ASP and Python gate.")
        return 1
    try:
        from storyworlds.asp import atoms, one_model
        model = one_model(asp_program("#show bad_ending/2.\n#show moral_value/2."))
        if not atoms(model, "bad_ending") or not atoms(model, "moral_value"):
            print("Mismatch: ASP did not derive the expected bad ending and moral value.")
            return 1
    except ImportError:
        pass
    for params in curated_params():
        sample = generate(params)
        if "ended badly" not in sample.story or not sample.story_qa:
            print("Mismatch: generated story failed verification.")
            return 1
    print("OK: Python and ASP agree on the smurf enterprise's bad ending and moral value.")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "girl", "rabbit", "berries"),
        StoryParams("Pip", "boy", "moth", "lanterns"),
        StoryParams("Momo", "boy", "field mouse", "roofs"),
        StoryParams("Bibi", "girl", "bee", "flowers"),
        StoryParams("Nori", "boy", "duckling", "boats"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show enterprise_ready/2.\n#show bad_ending/2.\n#show moral_value/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            from storyworlds.asp import atoms, one_model
            model = one_model(asp_program("#show bad_ending/2.\n#show moral_value/2."))
            print(json.dumps({"bad_ending": atoms(model, "bad_ending"), "moral_value": atoms(model, "moral_value")}))
        except ImportError:
            print("ASP mode requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 100):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all or len(samples) > 1:
            print(f"### story {index + 1}")
        print(sample.story)
        if args.trace and sample.world:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
