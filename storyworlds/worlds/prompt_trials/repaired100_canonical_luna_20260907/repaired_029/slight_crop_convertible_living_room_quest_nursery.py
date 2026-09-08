#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about Luna, a slight crop in a convertible
living room, and a gentle quest to repair a little moon-cart.
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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_worlds = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_worlds, "results.py")):
    _worlds = os.path.dirname(_worlds)
sys.path.insert(0, _worlds)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    location: str = "living_room"


@dataclass
class Setting:
    id: str
    label: str
    affords: set[str]
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass(frozen=True)
class Quest:
    id: str
    title: str
    object_label: str
    problem: str
    clue: str
    tool: str
    action: str
    helper_action: str
    result: str
    ending: str


@dataclass(frozen=True)
class StoryParams:
    setting: str
    feature: str
    quest: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


SETTINGS = {
    "living_room": Setting(
        id="living_room",
        label="the living room",
        affords={"quest", "play", "repair"},
    )
}

FEATURES = {
    "quest": "Quest",
}

QUESTS = {
    "moon_cart": Quest(
        id="moon_cart",
        title="The Moon-Cart Quest",
        object_label="the little moon-cart",
        problem="one slight wheel had slipped beneath a fold of cloth",
        clue="a pale crop-shaped mark showed where the wheel belonged",
        tool="a ribbon and a wooden button",
        action="looped the ribbon through the wheel and pressed the button against its axle",
        helper_action="held the lamp low so the hidden groove could be seen",
        result="the wheel clicked straight, and the moon-cart rolled around the rug",
        ending="the moon-cart carried a silver sock beneath the sofa while Luna hummed a bright nursery rhyme",
    ),
    "star_cradle": Quest(
        id="star_cradle",
        title="The Star-Cradle Quest",
        object_label="the small star cradle",
        problem="a slight blue blanket had caught on its rocking runner",
        clue="a crop of golden thread pointed toward the loose corner",
        tool="a soft comb and a spool of yellow yarn",
        action="combed the blanket free and tied the loose thread into a neat bow",
        helper_action="counted each slow rock and stopped the cradle before it bumped",
        result="the cradle rocked gently, and its paper stars blinked in time",
        ending="the star cradle rested by the bookcase as sleepy shadows danced across the living-room wall",
    ),
    "button_boat": Quest(
        id="button_boat",
        title="The Button-Boat Quest",
        object_label="the convertible button-boat",
        problem="a slight tear had opened in its paper sail",
        clue="a crop of red paper lay beside the tear like a ready-made patch",
        tool="paste and a strip of red paper",
        action="brushed paste around the tear and placed the paper patch over it",
        helper_action="blew one careful breeze while watching the sail stay flat",
        result="the convertible boat sailed across the blue rug without sinking",
        ending="the button-boat docked beside a cushion, carrying a thimble full of pretend rain",
    ),
}

NAMES = ["Luna", "Mira", "Nell", "Pip", "Toby"]
TRAITS = ["gentle", "curious", "patient", "bright", "kind"]

OPENINGS = [
    "{name} lived in a living room where cushions made hills and a rug made a sea.",
    "In the living room, where soft chairs stood in a row, {name} found a quest waiting below.",
    "One bright morning, {name} heard a tiny rattle beneath the living-room table.",
    "The living room was still as a rhyme when {name} noticed a small thing out of time.",
]

DIALOGUES = [
    '"What is wrong?" asked {name}. "Let us look before we tug."',
    '"Can we mend it?" asked {name}. "Yes," said the helper. "A careful hand can try."',
    '"The clue is small," said {name}. "Small clues can lead us far."',
    '"Do not hurry," said the helper. "{name}, show me what you see."',
]

REFLECTIONS = [
    "Luna learned that a slight trouble may hide a useful clue.",
    "The quest taught {name} that patient eyes can turn a tangle into a rhyme.",
    "A careful repair was better than a mighty pull.",
    "The living room seemed brighter because kindness had made room for play.",
]


def _add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] += amount


def _add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] += amount


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, feature, quest)
        for setting in SETTINGS
        for feature in FEATURES
        for quest in QUESTS
        if feature in SETTINGS[setting].affords
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "living_room"
    feature = args.feature or "quest"
    quest = args.quest or rng.choice(list(QUESTS))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if feature not in FEATURES:
        raise StoryError(f"Unknown feature: {feature}")
    if quest not in QUESTS:
        raise StoryError(f"Unknown quest: {quest}")
    if feature not in SETTINGS[setting].affords:
        raise StoryError(f"The setting does not afford the feature: {feature}")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, feature, quest, name, trait, args.seed)


def tell(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    world = World(setting)

    hero = world.add(Entity(params.name, "character", params.name))
    helper = world.add(Entity("mother", "helper", "Mum"))
    object_entity = world.add(Entity("quest_object", "object", quest.object_label))
    object_entity.meters["slight"] = 1.0
    object_entity.meters["convertible"] = 1.0
    problem = world.add(Entity("problem", "problem", quest.problem))
    tool = world.add(Entity("tool", "tool", quest.tool))

    world.facts.update(
        hero=hero,
        helper=helper,
        object=object_entity,
        problem=problem,
        tool=tool,
        quest=quest,
        clue=quest.clue,
        action=quest.action,
        helper_action=quest.helper_action,
        result=quest.result,
        ending=quest.ending,
    )

    world.say(rng.choice(OPENINGS).format(name=params.name))
    world.say(
        f"{params.name} was a {params.trait} child, slight and bright, "
        f"who loved a small {FEATURES[params.feature].lower()}."
    )
    world.say(
        f"Near the sofa waited {quest.object_label}, a convertible wonder "
        "that could be a cart, a boat, or a toy for the day."
    )
    _add_meme(hero, "curiosity")
    world.para()

    world.say(f"But {quest.problem}, so the toy could not begin its journey.")
    world.say(f"{params.name} felt worried, yet curiosity gave a little tap at the door.")
    world.say(rng.choice(DIALOGUES).format(name=params.name))
    world.say(f"Mum smiled and said, \"{quest.clue}.\"")
    _add_meme(hero, "worry")
    _add_meter(hero, "observed")

    world.para()
    world.say(
        f"{params.name} looked closely and found {quest.clue}. "
        "Then the plan became clear: test one small fix before trying another."
    )
    _add_meme(hero, "problem_solving")
    world.say(
        f"With {quest.tool}, {params.name} {quest.action}, "
        f"while Mum {quest.helper_action}."
    )
    world.say(f'"Will it work?" asked Mum. "{quest.result.capitalize()}" said {params.name}.')
    _add_meter(problem, "repaired")
    _add_meme(hero, "joy")

    world.para()
    world.say(f"{quest.result.capitalize()}.")
    world.say(rng.choice(REFLECTIONS).format(name=params.name))
    world.say(f"At bedtime, {quest.ending}.")
    world.fired.add("observe")
    world.fired.add("repair")
    return world


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else f"{params.name}:{params.quest}")
    world = tell(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    quest: Quest = world.facts["quest"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a Nursery Rhyme style Quest for {hero.label} in a living room.",
        f"Show how {hero.label} repairs {quest.object_label} after noticing {quest.clue}.",
        "Include the words slight, crop, and convertible in a gentle child-facing story.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    return [
        QAItem(
            f"What quest did {hero.label} find in the living room?",
            f"{hero.label} found {quest.title.lower()}, involving {quest.object_label}.",
        ),
        QAItem(
            "What was wrong with the quest object?",
            f"The problem was that {quest.problem}.",
        ),
        QAItem(
            f"What clue did {hero.label} notice?",
            f"{hero.label} noticed that {quest.clue}.",
        ),
        QAItem(
            "How was the problem repaired?",
            f"Using {quest.tool}, the child {quest.action}, while Mum {quest.helper_action}.",
        ),
        QAItem(
            "What showed that the repair worked?",
            f"The repair worked because {quest.result}; afterward, {quest.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a convertible object?",
            "A convertible object can change into another useful shape or form.",
        ),
        QAItem(
            "What does slight mean?",
            "Slight means small in amount, size, or degree.",
        ),
        QAItem(
            "What is a crop?",
            "A crop is a plant grown for food, or a small cut or portion of something.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a journey or task undertaken to reach a goal.",
        ),
        QAItem(
            "Why is it useful to look closely at a problem?",
            "Looking closely can reveal a clue that helps someone choose a safe and effective solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:14} ({entity.kind:9}) "
            f"meters={meters} memes={memes} location={entity.location}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
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
valid_setting(S) :- setting(S), affords(S,quest).
valid_quest(Q) :- quest(Q), clue(Q), tool(Q).
compatible(S,Q) :- valid_setting(S), valid_quest(Q).
#show compatible/2.
"""


def asp_facts() -> str:
    from asp import fact

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(fact("setting", sid))
        for affordance in sorted(setting.affords):
            lines.append(fact("affords", sid, affordance))
    for qid, quest in QUESTS.items():
        lines.extend(
            [
                fact("quest", qid),
                fact("clue", qid),
                fact("tool", qid),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    from asp import atoms, one_model

    model = one_model(asp_program())
    return sorted(set(atoms(model, "compatible")))


def asp_verify() -> int:
    expected = {(setting, quest) for setting, _, quest in valid_combos()}
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: ASP matches Python ({len(actual)} combinations).")
        for params in [
            StoryParams("living_room", "quest", "moon_cart", "Luna", "gentle", 1),
            StoryParams("living_room", "quest", "button_boat", "Mira", "curious", 2),
        ]:
            sample = generate(params)
            if not sample.story or "Luna" not in sample.story and params.name not in sample.story:
                return 1
        return 0
    print("ASP/Python mismatch.")
    print("Only in ASP:", sorted(actual - expected))
    print("Only in Python:", sorted(expected - actual))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Nursery Rhyme style living-room Quest storyworld."
    )
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--feature", choices=FEATURES, default=None)
    parser.add_argument("--quest", choices=QUESTS, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--trait", choices=TRAITS, default=None)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible combinations:")
        for pair in pairs:
            print(" ", pair)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, quest in enumerate(QUESTS):
            params = StoryParams(
                "living_room",
                "quest",
                quest,
                NAMES[index % len(NAMES)],
                TRAITS[index % len(TRAITS)],
                base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 0) * 50 + 50):
            if len(samples) >= max(args.n, 0):
                break
            seed = base_seed + index
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
