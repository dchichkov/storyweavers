#!/usr/bin/env python3
"""
A small animal storyworld about freight, causative kindness, and a helpful turn.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hen", "doe", "sheep"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"ram", "horse", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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


SETTING = Setting(
    place="the old forest road",
    affords={"freight", "kindness", "animal", "cart"},
)

ANIMALS = {
    "Luna": ("doe", "a young deer"),
    "Pip": ("dog", "a cheerful dog"),
    "Mara": ("hen", "a careful hen"),
    "Bram": ("ram", "a gentle ram"),
    "Niko": ("horse", "a patient horse"),
}

HELPERS = {
    "badger": ("badger", "the badger"),
    "otter": ("otter", "the otter"),
    "rabbit": ("rabbit", "the rabbit"),
    "goat": ("goat", "the goat"),
}

CARGO = [
    ("bread", "a basket of warm bread", "the village bakery"),
    ("blankets", "a bundle of soft blankets", "the hill shelter"),
    ("apples", "a crate of red apples", "the school kitchen"),
    ("books", "a box of picture books", "the forest classroom"),
]

OBSTACLES = [
    (
        "a wheel sank into a deep patch of mud",
        "the freight could tip into the ditch",
        "a firm strip of stones beside the road",
        "the helper packed flat stones under the wheel while the driver pulled slowly",
    ),
    (
        "a fallen branch blocked the narrow road",
        "dragging the cart around it could tear the freight",
        "a quiet path behind the cedar trees",
        "the helper moved the small twigs while the driver guided the cart around the branch",
    ),
    (
        "a sudden rain made the bridge slippery",
        "one frightened step could send the freight into the stream",
        "a covered footbridge farther upstream",
        "the helper tested the boards while the driver kept the cart level",
    ),
    (
        "a swarm of bees hummed around the quickest lane",
        "a loud rush could upset both the animals and the freight",
        "a longer lane through a shady orchard",
        "the helper led the way quietly while the driver followed at a patient pace",
    ),
]

MORALS = [
    "Kindness is causative: one caring choice can make another good choice possible.",
    "A strong team carries freight with gentle hearts as well as steady feet.",
    "Helping someone through a hard moment can open a safe road for everyone.",
]


@dataclass
class StoryParams:
    hero: str
    helper: str
    cargo: str
    obstacle_index: int
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, int]]:
    return [
        (hero, helper, cargo, index)
        for hero in ANIMALS
        for helper in HELPERS
        for cargo, _, _ in CARGO
        for index in range(len(OBSTACLES))
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice(list(HELPERS))
    cargo = args.cargo or rng.choice([item[0] for item in CARGO])
    index = args.obstacle_index
    if index is None:
        index = rng.randrange(len(OBSTACLES))
    if hero not in ANIMALS:
        raise StoryError(f"unknown animal hero: {hero}")
    if helper not in HELPERS:
        raise StoryError(f"unknown helper animal: {helper}")
    if cargo not in {item[0] for item in CARGO}:
        raise StoryError(f"unknown freight cargo: {cargo}")
    if not 0 <= index < len(OBSTACLES):
        raise StoryError("obstacle_index must name a known road problem")
    return StoryParams(hero=hero, helper=helper, cargo=cargo, obstacle_index=index)


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero_type, hero_label = ANIMALS[params.hero]
    helper_type, helper_label = HELPERS[params.helper]
    cargo_id, cargo_phrase, receiver = next(item for item in CARGO if item[0] == params.cargo)
    obstacle, danger, clue, method = OBSTACLES[params.obstacle_index]

    hero = world.add(Entity(params.hero.lower(), "animal", params.hero, hero_type))
    helper = world.add(Entity(params.helper, "animal", helper_label, helper_type))
    freight = world.add(Entity(cargo_id, "freight", cargo_phrase, "cargo"))
    cart = world.add(Entity("cart", "vehicle", "the little cart", "cart"))

    world.facts.update(
        hero=hero,
        helper=helper,
        freight=freight,
        cart=cart,
        receiver=receiver,
        obstacle=obstacle,
        danger=danger,
        clue=clue,
        method=method,
        cargo_phrase=cargo_phrase,
        moral=random.Random(params.seed).choice(MORALS) if params.seed is not None else MORALS[0],
    )

    hero.meters["energy"] = 5
    helper.meters["energy"] = 5
    freight.meters["safe"] = 1
    hero.memes["care"] = 1
    helper.memes["care"] = 1

    world.say(
        f"On {world.setting.place}, {hero.label} the {hero.type} pulled a little cart "
        f"loaded with {cargo_phrase}. The freight was meant for {receiver}."
    )
    world.say(
        f"{helper.label.capitalize()} walked beside the cart, carrying a small bell "
        f"so the two friends could stay together."
    )
    world.para()

    world.say(f"Then {obstacle}. {danger.capitalize()}.")
    hero.meters["energy"] -= 2
    hero.memes["worry"] = 1
    world.say(f"{hero.label} lowered {hero.pronoun('possessive')} head. \"I cannot move it alone,\" said {hero.label}.")
    world.say(
        f"{helper.label.capitalize()} came close and replied, "
        f"\"You do not have to. Let us help each other.\""
    )
    world.para()

    helper.memes["kindness"] = 1
    hero.memes["hope"] = 1
    world.say(f"First, {helper.label} noticed {clue}.")
    world.say(
        f"Because {helper.label} offered kindness, {hero.label} stopped rushing and listened. "
        f"Then {method}."
    )
    world.say(
        f"The cart moved a little, then a little more. Their careful work kept {cargo_phrase} "
        f"steady and dry."
    )
    world.para()

    hero.meters["energy"] += 1
    hero.memes["confidence"] = 1
    freight.meters["safe"] = 2
    world.say(
        f"At last they reached {receiver}. The freight arrived safely, and every good thing "
        f"inside the cart was ready to be shared."
    )
    world.say(
        f"{hero.label} smiled at {helper.label}. \"Your kindness caused my courage to grow,\" "
        f"{hero.label} said."
    )
    world.say(
        f"{helper.label.capitalize()} rang the little bell. "
        f"On the forest road, the sound meant that helping one friend had helped many."
    )
    world.say(f"They remembered this: {world.facts['moral']}")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle Animal Story about freight and causative kindness.",
        f"Tell how {f['hero'].label} and {f['helper'].label} carried {f['cargo_phrase']} safely.",
        f"Write a child-friendly story showing how kindness caused courage during this problem: {f['obstacle']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "Who carried the freight?",
            f"{f['hero'].label} and {f['helper'].label} carried {f['cargo_phrase']} together.",
        ),
        QAItem(
            "What happened on the road?",
            f"{f['obstacle'].capitalize()}. {f['danger'].capitalize()}.",
        ),
        QAItem(
            "How did the animals solve the problem?",
            f"They noticed {f['clue']}, shared the work, and used a careful plan: {f['method']}.",
        ),
        QAItem(
            "What did kindness cause?",
            f"{f['helper'].label.capitalize()}'s kindness helped {f['hero'].label} stop rushing, listen, and find courage.",
        ),
        QAItem(
            "Where did the freight go?",
            f"The freight arrived safely at {f['receiver']}.",
        ),
        QAItem("What lesson did they learn?", f["moral"]),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is freight?",
            "Freight is goods or supplies carried from one place to another.",
        ),
        QAItem(
            "What does causative mean?",
            "Causative means making something happen or helping cause a result.",
        ),
        QAItem(
            "What is kindness?",
            "Kindness means treating others with care and offering helpful support.",
        ),
        QAItem(
            "Why should animals share a heavy job?",
            "Sharing a heavy job makes it safer and gives everyone a chance to help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} kind={entity.kind:8} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "forest_road"),
        asp.fact("feature", "kindness"),
        asp.fact("domain", "freight"),
        asp.fact("causative", "kindness", "courage"),
    ]
    for hero in ANIMALS:
        lines.append(asp.fact("hero", hero.lower()))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    for cargo, _, _ in CARGO:
        lines.append(asp.fact("cargo", cargo))
    for index in range(len(OBSTACLES)):
        lines.append(asp.fact("obstacle", index))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(H, F, C, O) :-
    hero(H),
    helper(F),
    cargo(C),
    obstacle(O),
    feature(kindness),
    domain(freight),
    causative(kindness, courage).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (hero.lower(), helper, cargo, obstacle)
        for hero, helper, cargo, obstacle in valid_combos()
    }
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP gate matches Python gate ({len(python_set)} combinations).")
        return 0
    print("ASP/Python mismatch.")
    print("Only in ASP:", sorted(asp_set - python_set))
    print("Only in Python:", sorted(python_set - asp_set))
    return 1


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An Animal Story about freight and causative kindness."
    )
    parser.add_argument("--hero", choices=list(ANIMALS))
    parser.add_argument("--helper", choices=list(HELPERS))
    parser.add_argument("--cargo", choices=[item[0] for item in CARGO])
    parser.add_argument("--obstacle-index", type=int)
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
    StoryParams("Luna", "badger", "bread", 0),
    StoryParams("Pip", "otter", "blankets", 1),
    StoryParams("Mara", "rabbit", "books", 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
