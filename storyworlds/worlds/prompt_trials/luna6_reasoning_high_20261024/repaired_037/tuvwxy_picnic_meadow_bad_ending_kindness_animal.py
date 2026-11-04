#!/usr/bin/env python3
"""
A small animal-story world about a picnic in a meadow, a selfish choice,
a spoiled lunch, and kindness offered when it is needed most.

Seed tale:
---
The raccoon tuvwxy wanted the picnic treats all to himself. When Pip the field
mouse warned that the basket needed help, tuvwxy turned Pip away. A gust, a
shower, or a trail of ants spoiled the food. Pip still helped tuvwxy gather
what they could, and shared an apple. Their picnic ended early, but tuvwxy
learned to make room for a friend before trouble came.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    spot: str
    description: str
    affords: set[str]
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


# ---------------------------------------------------------------------------
# Registries and story parameters
# ---------------------------------------------------------------------------
PLACE_ID = "picnic_meadow"


@dataclass
class StoryParams:
    place: str
    spot: str
    trouble: str
    hero_name: str = "tuvwxy"
    friend_name: str = "Pip"
    seed: Optional[int] = None
    opening: int = 0


SPOTS = {
    "under_oak": {
        "description": "beneath a broad oak in the picnic meadow",
        "affords": {"gust", "shower"},
    },
    "willow_brook": {
        "description": "beside a little brook in the picnic meadow, near a willow",
        "affords": {"gust", "ants"},
    },
    "clover_rise": {
        "description": "on a low clover rise in the picnic meadow",
        "affords": {"shower", "ants"},
    },
}

TROUBLES = {
    "gust": {
        "food": "berry buns",
        "condition": "mud-smeared",
        "request": (
            '"The basket lid is flapping. May I tie it to that nearby tree root '
            'with my scarf?" {friend} asked.'
        ),
        "hazard": (
            "A sudden gust swept across the meadow. Because {hero} had left the "
            "basket unfastened, it skidded into a muddy hollow and toppled over. "
            "The berry buns tumbled out and were smeared with mud."
        ),
        "rescue": (
            "Together, they lifted the basket from the muddy hollow and gathered "
            "the buns, but mud had soaked through the paper."
        ),
        "cleanup": (
            "They tucked the mud-smeared buns back into their paper and packed "
            "them away."
        ),
        "cause": (
            "tuvwxy refused to fasten the basket before the gust came, so it "
            "tipped into the mud"
        ),
    },
    "shower": {
        "food": "apple tarts",
        "condition": "soggy",
        "request": (
            '"Those clouds are dripping. May I cover the open basket with this '
            'wide burdock leaf?" {friend} asked.'
        ),
        "hazard": (
            "Rain pattered over the picnic meadow. Since {hero} had left the "
            "basket uncovered, water ran through the paper wrapping and made "
            "the apple tarts soggy."
        ),
        "rescue": (
            "Together, they carried the basket beneath the oak, but rain had "
            "already soaked the apple tarts."
        ),
        "cleanup": (
            "They wrapped the soggy tarts in the wet paper and packed them away."
        ),
        "cause": (
            "tuvwxy refused to cover the basket before the shower began, so "
            "rain soaked the tarts"
        ),
    },
    "ants": {
        "food": "honey biscuits",
        "condition": "covered with ants",
        "request": (
            '"Ants are following the honey smell. May I help close the tin and '
            'move it off the grass?" {friend} asked.'
        ),
        "hazard": (
            "A line of ants found the open tin. Before {hero} could close it, "
            "the tiny visitors had reached the honey biscuits."
        ),
        "rescue": (
            "Together, they closed the tin gently and carried it away from the "
            "ant trail. The honey biscuits were already covered with ants."
        ),
        "cleanup": (
            "They left the ant-covered biscuits undisturbed and packed the "
            "closed tin away without harming a single ant."
        ),
        "cause": (
            "tuvwxy refused to close the tin when Pip noticed the ants, so the "
            "ants reached the biscuits"
        ),
    },
}

OPENINGS = [
    "The raccoon {hero} spread a yellow blanket at {place} and set down a basket of {food}.",
    "At {place}, raccoon {hero} arranged a yellow blanket and a basket of {food} for lunch.",
    "A quiet morning found raccoon {hero} carrying a yellow blanket and {food} to {place}.",
    "Raccoon {hero} had planned a fine lunch of {food}, so {hero} carried the basket to {place}.",
]

FRIEND_NAMES = ["Pip", "Moss", "Fern", "Lark", "Wren", "Mallow"]


def python_valid() -> list[tuple[str, str]]:
    """The Python reasonableness gate: each trouble must fit its picnic spot."""
    return sorted(
        (spot_id, trouble)
        for spot_id, spot in SPOTS.items()
        for trouble in spot["affords"]
        if trouble in TROUBLES
    )


def validate_name(name: str, role: str) -> None:
    if not name or not re.fullmatch(r"[A-Za-z][A-Za-z'-]*", name):
        raise StoryError(f"The {role} name must use letters, apostrophes, or hyphens.")


def validate_params(params: StoryParams) -> None:
    if params.place != PLACE_ID:
        raise StoryError("This story takes place in the picnic meadow.")
    if params.spot not in SPOTS:
        raise StoryError(f"Unknown picnic spot: {params.spot}.")
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown picnic trouble: {params.trouble}.")
    if (params.spot, params.trouble) not in set(python_valid()):
        raise StoryError(
            f"The {params.trouble} trouble is not a reasonable fit for "
            f"the {params.spot} picnic spot."
        )
    validate_name(params.hero_name, "raccoon")
    validate_name(params.friend_name, "field mouse")
    if params.hero_name.casefold() == params.friend_name.casefold():
        raise StoryError("The raccoon and the field mouse need different names.")
    if not isinstance(params.opening, int) or not 0 <= params.opening < len(OPENINGS):
        raise StoryError("The selected picnic opening is not available.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Spot, Trouble) :- affords(Spot, Trouble).
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines = [asp.fact("setting", PLACE_ID)]
    for spot_id, spot in sorted(SPOTS.items()):
        lines.append(asp.fact("spot", spot_id))
        for trouble in sorted(spot["affords"]):
            lines.append(asp.fact("affords", spot_id, trouble))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    answer_sets = set(asp_valid())
    python_sets = set(python_valid())
    if answer_sets == python_sets:
        print(f"OK: clingo gate matches Python gate ({len(answer_sets)} spot/trouble pairs).")
        return 0

    print("MISMATCH between clingo and Python:")
    if answer_sets - python_sets:
        print("  only in clingo:", sorted(answer_sets - python_sets))
    if python_sets - answer_sets:
        print("  only in Python:", sorted(python_sets - answer_sets))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> StoryState:
    validate_params(params)
    spot_data = SPOTS[params.spot]
    trouble = TROUBLES[params.trouble]
    setting = Setting(
        place=params.place,
        spot=params.spot,
        description=spot_data["description"],
        affords=set(spot_data["affords"]),
        meters={"grass_wetness": 0.0, "wind_strength": 0.0},
    )
    world = StoryState(setting=setting)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="raccoon",
            label=params.hero_name,
            phrase=f"the raccoon {params.hero_name}",
            meters={"food_security": 1.0, "helpfulness": 0.0},
            memes={"selfishness": 0.7, "regret": 0.0, "kindness": 0.2},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type="field mouse",
            label=params.friend_name,
            phrase=f"the field mouse {params.friend_name}",
            meters={"food_security": 0.7, "friendship": 0.8},
            memes={"kindness": 0.9, "trust": 0.7},
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            kind="thing",
            type="picnic basket",
            label="the picnic basket",
            meters={"secured": 0.0, "condition": 1.0},
            memes={},
        )
    )
    food = world.add(
        Entity(
            id="food",
            kind="thing",
            type="picnic food",
            label=trouble["food"],
            phrase=trouble["food"],
            owner=hero.id,
            meters={"freshness": 1.0},
            memes={},
        )
    )
    apple = world.add(
        Entity(
            id="apple",
            kind="thing",
            type="apple",
            label="a crisp red apple",
            phrase="a crisp red apple",
            owner=friend.id,
            meters={"freshness": 1.0, "shared": 0.0},
            memes={"generosity": 0.8},
        )
    )
    blanket = world.add(
        Entity(
            id="blanket",
            kind="thing",
            type="picnic blanket",
            label="the yellow blanket",
            meters={"tidiness": 1.0},
            memes={},
        )
    )

    opening = OPENINGS[params.opening].format(
        hero=hero.label,
        place=setting.description,
        food=trouble["food"],
    )
    world.say(opening)
    world.say(
        f"The field mouse {friend.label} set down a crisp red apple. "
        f'"I brought this for us to share," {friend.label} said.'
    )
    world.say(trouble["request"].format(friend=friend.label))
    world.say(
        f'"No. These treats are mine, and I do not need you meddling," '
        f'{hero.label} said, pulling the basket close.'
    )
    world.say(
        f'"I only wanted to help," {friend.label} replied, stepping back. '
        f'"I will stay nearby."'
    )

    hero.memes["selfishness"] = 1.0
    world.facts.update(
        request_refused=True,
        kindness_offered=True,
        trouble=params.trouble,
        spot=params.spot,
    )

    world.para()
    if params.trouble == "gust":
        setting.meters["wind_strength"] = 0.9
    elif params.trouble == "shower":
        setting.meters["grass_wetness"] = 0.9
    else:
        setting.meters["grass_wetness"] = 0.1

    world.say(trouble["hazard"].format(hero=hero.label))
    world.say(
        f'"Oh no! I cannot manage it alone. Will you help me, {friend.label}?" '
        f'{hero.label} called.'
    )
    world.say(
        f'"Yes," {friend.label} answered. "Let us lift it gently and save what we can."'
    )
    world.say(trouble["rescue"])

    basket.meters["secured"] = 0.6
    basket.meters["condition"] = 0.4
    food.meters["freshness"] = 0.0
    food.memes["spoiled"] = 1.0
    hero.meters["food_security"] = 0.0
    hero.meters["helpfulness"] = 0.7
    hero.memes["regret"] = 0.9
    friend.memes["trust"] = 0.65
    world.facts.update(
        food_condition=trouble["condition"],
        bad_ending=True,
        rescue_completed=True,
        consequence=trouble["cause"],
    )

    world.para()
    world.say(trouble["cleanup"])
    world.say(
        f'"I was wrong to shut you out," {hero.label} said. '
        f'"May we share your apple now?"'
    )
    world.say(
        f'"Of course," said {friend.label}, breaking the apple in two. '
        f'"There is enough for both of us."'
    )
    apple.meters["shared"] = 1.0
    hero.memes["kindness"] = 0.8
    hero.memes["regret"] = 0.6
    world.say(
        f"{hero.label} made room on the yellow blanket and offered "
        f"{friend.label} the larger apple half."
    )
    world.say(
        f"On the rumpled blanket, the two friends shared the little red apple. "
        f"The ruined {trouble['food']} stayed in the basket, and their picnic "
        f"ended before lunch."
    )

    world.facts.update(
        hero_name=hero.label,
        friend_name=friend.label,
        food_name=food.label,
        apple_shared=True,
        lesson=trouble["cause"],
    )
    return world


# ---------------------------------------------------------------------------
# Prompts and questions
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryState) -> list[str]:
    facts = world.facts
    return [
        (
            f"Write an animal story about {facts['hero_name']} the raccoon "
            f"and a picnic at {world.setting.description}."
        ),
        (
            f"Tell a child-friendly story in which {facts['hero_name']} first "
            f"rejects {facts['friend_name']}'s help, loses the picnic food, "
            "and learns to return kindness."
        ),
        (
            "Include spoken dialogue, a clear cause for the spoiled picnic, "
            "and a gentle bad ending that still shows friendship."
        ),
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    facts = world.facts
    trouble = TROUBLES[str(facts["trouble"])]
    return [
        QAItem(
            question=f"Where did {facts['hero_name']} and {facts['friend_name']} have their picnic?",
            answer=(
                f"They spread their blanket at {world.setting.description}. "
                "That was where the basket was left within reach of the trouble."
            ),
        ),
        QAItem(
            question=f"What did {facts['friend_name']} offer to do?",
            answer=(
                f"{facts['friend_name']} offered a practical way to protect "
                f"the {trouble['food']}, but {facts['hero_name']} refused the help."
            ),
        ),
        QAItem(
            question=f"Why was the picnic food spoiled?",
            answer=(
                f"{facts['hero_name']} refused to prepare for the trouble. "
                f"Then {trouble['cause']}."
            ),
        ),
        QAItem(
            question=f"How did {facts['friend_name']} show kindness after being turned away?",
            answer=(
                f"{facts['friend_name']} came back to help lift and gather the "
                f"basket, then shared a crisp red apple with {facts['hero_name']}."
            ),
        ),
        QAItem(
            question="Why was the ending a sad one for the picnic?",
            answer=(
                f"The {trouble['food']} could not be eaten, so the picnic ended "
                "before lunch. The friends still shared an apple, but kindness "
                "could not undo the spoiled meal."
            ),
        ),
        QAItem(
            question=f"What did {facts['hero_name']} learn?",
            answer=(
                f"{facts['hero_name']} learned that refusing a friend's help "
                "can make a small problem worse, and that it is better to make "
                "room for kindness before trouble arrives."
            ),
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a raccoon?",
            answer="A raccoon is a small mammal with a bushy tail and dark markings on its face.",
        ),
        QAItem(
            question="Why should picnic food be kept covered?",
            answer="Covered food is less likely to be reached by rain, dirt, or insects.",
        ),
        QAItem(
            question="What does it mean to show kindness?",
            answer="Showing kindness means treating others with care and offering help when they need it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    lines.append(
        f"  setting: place={world.setting.place}, spot={world.setting.spot}, "
        f"description={world.setting.description!r}"
    )
    lines.append(f"  setting meters: {world.setting.meters}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.type:14}) label={entity.label!r} "
            f"owner={entity.owner!r}"
        )
        lines.append(f"      meters={entity.meters}")
        lines.append(f"      memes={entity.memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and emission
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or PLACE_ID
    if place != PLACE_ID:
        raise StoryError("This story takes place in the picnic meadow.")

    requested_spot = getattr(args, "spot", None)
    requested_trouble = getattr(args, "trouble", None)
    if requested_spot is not None and requested_spot not in SPOTS:
        raise StoryError(f"Unknown picnic spot: {requested_spot}.")
    if requested_trouble is not None and requested_trouble not in TROUBLES:
        raise StoryError(f"Unknown picnic trouble: {requested_trouble}.")

    if requested_spot is not None:
        spot = requested_spot
    elif requested_trouble is not None:
        possible_spots = [
            spot_id for spot_id, data in SPOTS.items()
            if requested_trouble in data["affords"]
        ]
        if not possible_spots:
            raise StoryError(f"No picnic spot can support {requested_trouble}.")
        spot = rng.choice(possible_spots)
    else:
        spot = rng.choice(list(SPOTS))

    if requested_trouble is not None:
        trouble = requested_trouble
    else:
        trouble = rng.choice(sorted(SPOTS[spot]["affords"]))

    params = StoryParams(
        place=place,
        spot=spot,
        trouble=trouble,
        hero_name=getattr(args, "name", None) or "tuvwxy",
        friend_name=getattr(args, "friend", None) or rng.choice(FRIEND_NAMES),
        seed=getattr(args, "seed", None),
        opening=rng.randrange(len(OPENINGS)),
    )
    validate_params(params)
    return params


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


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def verify_generated_stories() -> int:
    combinations = python_valid()
    for index, (spot, trouble) in enumerate(combinations):
        params = StoryParams(
            place=PLACE_ID,
            spot=spot,
            trouble=trouble,
            hero_name="tuvwxy",
            friend_name=FRIEND_NAMES[index % len(FRIEND_NAMES)],
            seed=1000 + index,
            opening=index % len(OPENINGS),
        )
        sample = generate(params)
        if "tuvwxy" not in sample.story:
            print(f"FAIL: the seed character is missing in {spot}/{trouble}.")
            return 1
        if "picnic meadow" not in sample.story:
            print(f"FAIL: the setting is missing in {spot}/{trouble}.")
            return 1
        if '"' not in sample.story or "asked" not in sample.story or "said" not in sample.story:
            print(f"FAIL: spoken dialogue is missing in {spot}/{trouble}.")
            return 1
        if sample.world is None or not sample.world.facts.get("bad_ending"):
            print(f"FAIL: the bad picnic outcome is missing in {spot}/{trouble}.")
            return 1
        if sample.world.entities["food"].meters["freshness"] != 0.0:
            print(f"FAIL: the simulated food outcome is inconsistent in {spot}/{trouble}.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print(f"FAIL: questions and answers are missing in {spot}/{trouble}.")
            return 1
    print(f"OK: exercised {len(combinations)} generated picnic stories.")
    return 0


def run_verify() -> int:
    asp_status = asp_verify()
    story_status = verify_generated_stories()
    return 1 if asp_status or story_status else 0


# ---------------------------------------------------------------------------
# Command line interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal story world: tuvwxy's picnic in a meadow."
    )
    parser.add_argument("--place", help="The setting; this world uses picnic_meadow.")
    parser.add_argument("--spot", help="Picnic spot: under_oak, willow_brook, or clover_rise.")
    parser.add_argument("--trouble", help="Picnic trouble: gust, shower, or ants.")
    parser.add_argument("--name", help="Name for the raccoon (default: tuvwxy).")
    parser.add_argument("--friend", help="Name for the field mouse.")
    parser.add_argument("-n", type=int, default=1, help="Number of stories to generate.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="Generate every valid spot/trouble combination.")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="Print the ASP-valid picnic combinations.")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def all_params(args: argparse.Namespace) -> list[StoryParams]:
    place = args.place or PLACE_ID
    if place != PLACE_ID:
        raise StoryError("This story takes place in the picnic meadow.")
    if args.spot is not None and args.spot not in SPOTS:
        raise StoryError(f"Unknown picnic spot: {args.spot}.")
    if args.trouble is not None and args.trouble not in TROUBLES:
        raise StoryError(f"Unknown picnic trouble: {args.trouble}.")

    combinations = [
        pair for pair in python_valid()
        if (args.spot is None or pair[0] == args.spot)
        and (args.trouble is None or pair[1] == args.trouble)
    ]
    if not combinations:
        raise StoryError("Those picnic choices do not make a reasonable combination.")

    params_list = []
    for index, (spot, trouble) in enumerate(combinations):
        params = StoryParams(
            place=place,
            spot=spot,
            trouble=trouble,
            hero_name=args.name or "tuvwxy",
            friend_name=args.friend or FRIEND_NAMES[index % len(FRIEND_NAMES)],
            seed=args.seed,
            opening=index % len(OPENINGS),
        )
        validate_params(params)
        params_list.append(params)
    return params_list


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.show_asp:
            print(asp_program())
            return
        if args.verify:
            raise SystemExit(run_verify())
        if args.asp:
            valid = asp_valid()
            print(f"{len(valid)} valid picnic combinations:\n")
            for spot, trouble in valid:
                print(f"  {spot:12} {trouble}")
            return

        if args.all:
            params_list = all_params(args)
        else:
            if args.n < 1:
                raise StoryError("The number of stories must be at least one.")
            base_seed = args.seed if args.seed is not None else random.randrange(2**31)
            params_list = []
            for index in range(args.n):
                rng = random.Random(base_seed + index)
                params = resolve_params(args, rng)
                params.seed = base_seed + index
                params_list.append(params)

        samples = [generate(params) for params in params_list]
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return

        for index, sample in enumerate(samples):
            header = f"### variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
