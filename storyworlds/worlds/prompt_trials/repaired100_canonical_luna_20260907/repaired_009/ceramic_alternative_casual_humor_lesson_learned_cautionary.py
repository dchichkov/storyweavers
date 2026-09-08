#!/usr/bin/env python3
"""
A small animal storyworld about ceramic, alternative, and casual choices.
The premise is a young animal preparing a ceramic bowl for a picnic. A casual
shortcut cracks it, so a friend suggests an alternative plan. The lesson is
cautionary but warm: slow care can save both a dish and a friendship.
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
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    action: str
    risk: str
    alternative: str
    result: str
    lesson: str


@dataclass
class Setting:
    id: str
    place: str
    surface: str
    affords: set[str]


@dataclass
class World:
    setting: Setting
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


SETTINGS = {
    "meadow": Setting(
        "meadow",
        "the clover meadow",
        "a flat picnic cloth",
        {"picnic", "ceramic_bowl", "shade"},
    ),
    "orchard": Setting(
        "orchard",
        "the apple orchard",
        "a low wooden table",
        {"picnic", "ceramic_bowl", "shade"},
    ),
    "pond": Setting(
        "pond",
        "the pond bank",
        "a broad tree root",
        {"picnic", "ceramic_bowl", "shade"},
    ),
}

PLANS = {
    "berries": Plan(
        "berries",
        "berry lunch",
        "carry the ceramic bowl of berries to the picnic",
        "a casual swing could make the ceramic bowl bump the stone",
        "place the bowl in a soft leaf nest and carry it with two careful paws",
        "the berries reached the picnic bright and whole",
        "A careful alternative is wiser than a quick shortcut when something can break.",
    ),
    "acorns": Plan(
        "acorns",
        "acorn counting",
        "bring the ceramic bowl of acorns to the squirrel counting game",
        "a hurried hop could tip the bowl down the little hill",
        "slide the bowl inside a woven basket and move one step at a time",
        "every acorn arrived ready to be counted",
        "Protecting a fragile thing first makes the rest of the job easier.",
    ),
    "petals": Plan(
        "petals",
        "flower crowns",
        "carry the ceramic bowl of petals to the flower-circle",
        "a loose pebble could crack the bowl before the crowns were made",
        "pad the bowl with moss and ask a friend to guide the path",
        "the petals stayed soft, and the animals made bright flower crowns",
        "When a plan feels risky, asking for help is a strong choice.",
    ),
}

ANIMAL_NAMES = ["Luna", "Pip", "Mallow", "Toby", "Nell", "Bramble"]
FRIEND_NAMES = ["Otis", "Clover", "Mimi", "Rook", "Poppy"]
ANIMAL_KINDS = ["rabbit", "hedgehog", "squirrel", "mouse", "fox"]
MOODS = ["curious", "cheerful", "playful", "eager", "thoughtful"]

ARCS = {
    "berries": "berries",
    "acorns": "acorns",
    "petals": "petals",
}


@dataclass
class StoryParams:
    place: str
    plan: str
    name: str
    friend: str
    animal: str
    mood: str
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


ASP_RULES = r"""
risky(P) :- plan(P), fragile(P), casual_risk(P).
has_alternative(P) :- plan(P), alternative(P).
valid_story(S, P) :- setting(S), affords(S, ceramic_bowl), plan(P), risky(P), has_alternative(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, affordance))
    for pid in PLANS:
        lines.extend(
            [
                asp.fact("plan", pid),
                asp.fact("fragile", pid),
                asp.fact("casual_risk", pid),
                asp.fact("alternative", pid),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, pid) for sid in SETTINGS for pid in PLANS]


def asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return set(asp.atoms(model, "valid_story"))


def _choice(mapping, key):
    if key not in mapping:
        raise StoryError(f"Unknown choice: {key}")
    return mapping[key]


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.plan not in PLANS:
        raise StoryError(f"Unknown plan: {params.plan}")
    if not params.name.strip():
        raise StoryError("The animal needs a name.")
    if not params.friend.strip():
        raise StoryError("The helper needs a name.")

    setting = SETTINGS[params.place]
    plan = PLANS[params.plan]
    world = World(setting)

    hero = world.add(
        Entity(
            params.name,
            params.name,
            "animal",
            meters={"balance": 1.0, "cracks": 0.0},
            memes={"eagerness": 1.0, "worry": 0.0, "pride": 0.0},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            params.friend,
            "animal",
            meters={"balance": 1.0, "cracks": 0.0},
            memes={"patience": 1.0, "kindness": 1.0},
        )
    )
    bowl = world.add(
        Entity(
            "ceramic_bowl",
            "the ceramic bowl",
            "ceramic",
            meters={"cracks": 0.0, "distance": 0.0},
            memes={"care": 0.0},
        )
    )
    basket = world.add(
        Entity(
            "leaf_nest",
            "a soft leaf nest",
            "alternative_tool",
            meters={"support": 1.0},
            memes={"safety": 1.0},
        )
    )

    opening_lines = [
        f"{hero.label} the {params.animal} woke up {params.mood} in {setting.place}. A picnic waited nearby, and the shiny ceramic bowl sat on {setting.surface}.",
        f"On a bright morning in {setting.place}, {hero.label} the {params.animal} found the ceramic bowl beside the picnic basket. It looked grand enough to hold a king's lunch, or at least three berries.",
        f"{hero.label} had one important job at the picnic: {plan.action}. The {params.mood} {params.animal} gave the bowl a proud little wiggle.",
        f"The animals were preparing a feast in {setting.place}. {hero.label} watched the ceramic bowl sparkle and decided that carrying it would be easy-peasy.",
    ]
    world.say(opening_lines[params.opening % len(opening_lines)])
    world.say(f'"I can take it quickly," said {hero.label}. "The picnic is only a short hop away."')
    world.say(f'"Short hops can still have long tumbles," {friend.label} replied, watching the pebbles near {setting.surface}.')
    world.para()

    world.say(f"{hero.label} tried a casual shortcut because {plan.risk}.")
    world.say(f"The bowl bumped once. Then it made a tiny sound like a mouse clearing its throat: crack.")
    bowl.meters["cracks"] = 1.0
    hero.memes["worry"] = 1.0
    hero.meters["balance"] = 0.0
    world.say(f'"Oh dear," said {hero.label}. "I thought being quick was clever."')
    world.say(f'"Quick is useful for chasing butterflies," said {friend.label}, "but this bowl needs an alternative."')
    world.para()

    world.say(f"{friend.label} showed {hero.label} {basket.label}.")
    world.say(f'"Let us {plan.alternative}," {friend.label} suggested.')
    world.say(f'"That is slower," {hero.label} said.')
    world.say(f'"Yes," said {friend.label}. "It is also much less bumpy."')
    hero.memes["eagerness"] = 0.0
    hero.memes["pride"] = 1.0
    bowl.meters["cracks"] = 0.0
    bowl.meters["distance"] = 1.0
    bowl.memes["care"] = 1.0
    world.say(f"{hero.label} listened, placed the ceramic bowl in the soft leaf nest, and carried it with {friend.label}.")
    world.say(f"They took the smooth path together, and {plan.result}.")
    world.para()

    endings = [
        f"At the picnic, {hero.label} touched the bowl gently and said, 'I will remember this.' The animals laughed kindly, and the bowl held the lunch without one more crack.",
        f"The animals cheered when the bowl arrived. {hero.label} smiled at {friend.label}; the alternative had taken longer, but it had saved the feast.",
        f"After lunch, {hero.label} put the leaf nest beside the bowl for next time. Even the bowl seemed to shine with its new lesson.",
        f"A butterfly landed on the picnic cloth, and nobody chased it while carrying dishes. {hero.label} had learned that caution could be cheerful too.",
    ]
    world.say(endings[params.ending % len(endings)])
    world.say(f"The lesson was simple: {plan.lesson}")

    world.facts.update(hero=hero, friend=friend, bowl=bowl, basket=basket, plan=plan)
    return world


def prompts(world: World) -> list[str]:
    plan: Plan = world.facts["plan"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write an animal story about {hero.label} carrying a ceramic bowl for {plan.name}.",
        f"Tell a casual animal adventure in which a risky shortcut leads to an alternative plan: {plan.alternative}.",
        "Write a humorous but cautionary lesson story about caring for a fragile ceramic object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    plan: Plan = world.facts["plan"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        QAItem(
            "What was the animal trying to carry?",
            f"{hero.label} was trying to carry a ceramic bowl for {plan.name}.",
        ),
        QAItem(
            "Why did the first plan go wrong?",
            f"The casual shortcut was risky because {plan.risk}.",
        ),
        QAItem(
            f"What alternative did {friend.label} suggest?",
            f"{friend.label} suggested that they {plan.alternative}.",
        ),
        QAItem(
            "What lesson did the animals learn?",
            plan.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is ceramic?",
            "Ceramic is a hard material made from clay and heated until it becomes strong, though it can still crack when dropped or bumped.",
        ),
        QAItem(
            "Why can a soft nest help carry a bowl?",
            "A soft nest cushions the bowl and helps keep it steady while someone carries it.",
        ),
        QAItem(
            "What does caution mean?",
            "Caution means slowing down and thinking about danger before acting.",
        ),
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    plan = args.plan or rng.choice(list(PLANS))
    return StoryParams(
        place=place,
        plan=plan,
        name=args.name or rng.choice(ANIMAL_NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        animal=args.animal or rng.choice(ANIMAL_KINDS),
        mood=args.mood or rng.choice(MOODS),
        opening=rng.randrange(4),
        turn=rng.randrange(4),
        ending=rng.randrange(4),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.label}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        description="Animal storyworld about a ceramic bowl, an alternative plan, and a cautionary lesson."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--plan", choices=sorted(PLANS))
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--animal", choices=ANIMAL_KINDS)
    parser.add_argument("--mood", choices=MOODS)
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


def asp_verify() -> int:
    python_valid = set(valid_combos())
    clingo_valid = asp_valid()
    if python_valid == clingo_valid:
        for params in CURATED:
            generate(params)
        print(f"OK: ASP and Python agree on {len(python_valid)} valid combinations.")
        return 0
    print("Mismatch between ASP and Python:")
    print("Only Python:", sorted(python_valid - clingo_valid))
    print("Only ASP:", sorted(clingo_valid - python_valid))
    return 1


CURATED = [
    StoryParams("meadow", "berries", "Luna", "Otis", "rabbit", "curious", 0, 0, 0),
    StoryParams("orchard", "acorns", "Pip", "Clover", "squirrel", "playful", 1, 1, 1),
    StoryParams("pond", "petals", "Mallow", "Mimi", "hedgehog", "thoughtful", 2, 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 50):
            if len(samples) >= args.n:
                break
            rng = random.Random(seed + index)
            params = resolve_params(args, rng)
            params.seed = seed + index
            sample = generate(params)
            if sample.story not in seen:
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
