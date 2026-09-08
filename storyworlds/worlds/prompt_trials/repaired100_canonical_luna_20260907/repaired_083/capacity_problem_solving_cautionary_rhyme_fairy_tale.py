#!/usr/bin/env python3
"""
A small fairy-tale storyworld about capacity, careful choices, and a rhyme
that helps a child solve a problem before a magical vessel overflows.
"""

from __future__ import annotations

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
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class Vessel:
    id: str
    label: str
    capacity: int
    color: str
    safe_for: str


@dataclass(frozen=True)
class Trial:
    trial_id: str
    object_name: str
    amount: int
    vessel_id: str
    clue: str
    danger: str
    first_guess: str
    test: str
    twist: str
    repair: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    trial_id: str = "moonwater"
    telling_mode: str = "clue_first"
    detail_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    vessels: dict[str, Vessel] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


PLACES = {
    "moonlit_hill": "the moonlit hill",
    "rose_tower": "the rose tower",
    "whispering_wood": "the whispering wood",
}

VESSELS = {
    "acorn_cup": Vessel("acorn_cup", "the acorn cup", 2, "brown", "dew"),
    "silver_basin": Vessel("silver_basin", "the silver basin", 5, "silver", "moonwater"),
    "dragon_pot": Vessel("dragon_pot", "the dragon pot", 8, "red", "ember_soup"),
}

TRIALS = {
    "moonwater": Trial(
        "moonwater",
        "moonwater",
        7,
        "silver_basin",
        "the basin was marked with five tiny stars",
        "moonwater began to spill across the spell stones",
        "that the basin could hold any amount because it was enchanted",
        "count the stars, read the old brass number, and pour the water into a larger pot",
        "the basin's magic made it shine, but its capacity was still only five cups",
        "stop pouring, move the extra water into the dragon pot, and mark the basin with a bright five",
        "magic may sparkle, but a container still has a limit",
        "the basin held five shining cups while the two extra cups rested safely in the dragon pot",
    ),
    "dew": Trial(
        "dew",
        "morning dew",
        3,
        "acorn_cup",
        "two drops already trembled at the acorn cup's brim",
        "the thirsty garden sprites asked for one more cup",
        "that the little cup would stretch because it had grown beside an oak",
        "measure the cup with pebbles and share the dew between two bowls",
        "the oak had made the cup sturdy, not endless",
        "give the acorn cup two pebbles of dew and place the last pebble in a leaf bowl",
        "a strong little thing can still have a small capacity",
        "the acorn cup gleamed with two drops while a leaf bowl held the final gift",
    ),
    "ember_soup": Trial(
        "ember_soup",
        "ember soup",
        9,
        "dragon_pot",
        "the dragon pot's painted flame ended below the soup's rising bubbles",
        "that the pot's dragon picture meant it could swallow every flame",
        "stir the soup into marked ladles and compare the total with the pot's red line",
        "the dragon on the pot was a picture, not a promise of unlimited room",
        "remove one ladle before the soup reaches the red line and serve it in a bowl",
        "pictures can invite courage, but marks and measures keep us safe",
        "the dragon pot sat below its red line while one warm bowl waited beside it",
    ),
}


MODES = (
    "clue_first",
    "rhyme_first",
    "question_first",
    "helper_first",
    "quiet_first",
)

OPENINGS = {
    "clue_first": "{hero} saw a warning before the trouble began.",
    "rhyme_first": "Measure the cup, mind the brim; a careful rhyme was {hero}'s gem.",
    "question_first": "Could a magical vessel hold more than its own capacity?",
    "helper_first": "{helper} carried the shining vessel while {hero} followed with a measuring spoon.",
    "quiet_first": "The fairy kingdom was quiet except for a silver drip.",
}

BRIDGES = (
    "The small clue waited like a pebble in a shoe.",
    "{hero} tucked the detail into memory instead of rushing past it.",
    "A wise helper notices what a hurried hand forgets.",
    "The warning was tiny, but tiny warnings can guard large treasures.",
)

REPLIES = (
    "'Let us measure before we pour,' said {hero}.",
    "'A bright vessel can still be a small vessel,' said {helper}.",
    "'Guessing is not measuring,' {hero} replied.",
    "'Count the room, then choose the room,' said {helper}.",
)


def story_reasonable(place: str, trial_id: str) -> bool:
    return place in PLACES and trial_id in TRIALS


def explain_rejection(place: str, trial_id: str) -> str:
    if place not in PLACES:
        return f"(No story: '{place}' is not one of the fairy-tale places.)"
    return f"(No story: '{trial_id}' is not a safe capacity trial.)"


def tell(params: StoryParams) -> World:
    if not story_reasonable(params.place, params.trial_id):
        raise StoryError(explain_rejection(params.place, params.trial_id))

    trial = TRIALS[params.trial_id]
    vessel = VESSELS[trial.vessel_id]
    world = World(PLACES[params.place])

    hero = world.add(Entity(params.hero_name, "character", params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_name))
    vessel_entity = world.add(Entity(vessel.id, "vessel", vessel.label))
    vessel_entity.add_meter("capacity", vessel.capacity)
    vessel_entity.add_meter("filled_before", min(vessel.capacity - 1, trial.amount))
    vessel_entity.add_meme("trust", 1)
    hero.add_meme("care", 1)
    helper.add_meme("wisdom", 1)

    world.vessels[vessel.id] = vessel
    world.facts.update(
        hero=hero,
        helper=helper,
        trial=trial,
        vessel=vessel,
        place=world.place,
        amount=trial.amount,
        capacity=vessel.capacity,
        overflow=trial.amount - vessel.capacity,
    )

    mode = params.telling_mode if params.telling_mode in OPENINGS else "clue_first"
    world.say(OPENINGS[mode].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"In {world.place}, {params.hero_name} helped {params.helper_name} prepare "
        f"{trial.object_name} for the Fairy Queen."
    )
    world.say(
        f"They carried {trial.amount} cups toward {vessel.label}, whose capacity was only "
        f"{vessel.capacity} cups."
    )
    world.say(f"Before the pouring, {trial.clue}.")
    world.say(BRIDGES[params.detail_id % len(BRIDGES)].format(hero=params.hero_name))
    world.say(f"Then the trouble grew: {trial.danger}.")
    world.say(f"At first, they guessed {trial.first_guess}.")
    world.say(REPLIES[(params.detail_id + 1) % len(REPLIES)].format(
        hero=params.hero_name, helper=params.helper_name
    ))
    world.say(
        f"To solve the problem, they decided to {trial.test}. "
        "They counted the vessel's capacity instead of trusting its sparkle."
    )
    world.say(f"The twist was that {trial.twist}.")
    world.say(
        f"{params.hero_name} and {params.helper_name} worked together to {trial.repair}. "
        f"'Measure the brim, keep danger dim,' said {params.hero_name}; "
        f"{params.helper_name} answered, 'A careful rhyme can guide each limb.'"
    )
    world.say(f"They learned that {trial.lesson}.")
    world.say(
        f"At last, {trial.ending}. The Fairy Queen smiled because the magic was safe."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly fairy tale about capacity and {trial.object_name}.",
        f"Tell a cautionary rhyme in which a vessel can hold only {world.facts['capacity']} cups.",
        f"Create a problem-solving story using this clue: {trial.clue}. Include dialogue, a twist, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    vessel: Vessel = world.facts["vessel"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            "What problem did the fairy tale present?",
            f"{hero.label} and {helper.label} had {trial.amount} cups of {trial.object_name}, "
            f"but {vessel.label} had a capacity of only {vessel.capacity} cups.",
        ),
        QAItem(
            "What clue warned them?",
            f"The clue was that {trial.clue}. It showed that the vessel had a limit.",
        ),
        QAItem(
            "What did they first guess?",
            f"They first guessed {trial.first_guess}. They later checked that guess instead of trusting it.",
        ),
        QAItem(
            "How did they solve the problem?",
            f"They solved it by choosing to {trial.test}, and then they chose to {trial.repair}.",
        ),
        QAItem(
            "What was the cautionary lesson?",
            f"They learned that {trial.lesson}.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended when {trial.ending}. The magic stayed safe because they respected capacity.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does capacity mean?",
            "Capacity is the greatest amount that a container or space can safely hold.",
        ),
        QAItem(
            "Why should someone check capacity before pouring?",
            "Checking capacity helps prevent spilling, breaking, or making a dangerous mess.",
        ),
        QAItem(
            "What is a cautionary tale?",
            "A cautionary tale is a story that shows a danger and teaches people how to avoid it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_place/1.
#show valid_trial/1.
#show safe_story/2.

valid_place(P) :- place(P).
valid_trial(T) :- trial(T), capacity(T,C), amount(T,A), A > C.
safe_story(P,T) :- valid_place(P), valid_trial(T), vessel(T,V), vessel_capacity(V,C), amount(T,A), A > C.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for trial in TRIALS.values():
        vessel = VESSELS[trial.vessel_id]
        lines.append(asp.fact("trial", trial.trial_id))
        lines.append(asp.fact("capacity", trial.trial_id, vessel.capacity))
        lines.append(asp.fact("amount", trial.trial_id, trial.amount))
        lines.append(asp.fact("vessel", trial.trial_id, vessel.id))
        lines.append(asp.fact("vessel_capacity", vessel.id, vessel.capacity))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_trial/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_trials() -> set[str]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_trial/1."))
    return {args[0] for args in asp.atoms(model, "valid_trial")}


def asp_verify() -> int:
    py_trials = {
        trial_id
        for trial_id, trial in TRIALS.items()
        if trial.amount > VESSELS[trial.vessel_id].capacity
    }
    asp_trials = asp_valid_trials()
    if py_trials == asp_trials:
        print(f"OK: ASP gate matches Python registry ({len(py_trials)} trials).")
        for trial_id in sorted(py_trials):
            sample = generate(
                StoryParams(
                    place="moonlit_hill",
                    hero_name="Luna",
                    helper_name="Pip",
                    trial_id=trial_id,
                )
            )
            if "capacity" not in sample.story.lower():
                print("Generated story omitted capacity language.")
                return 1
        print("OK: generated stories exercised.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP only:", sorted(asp_trials - py_trials))
    print("Python only:", sorted(py_trials - asp_trials))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale capacity problem-solving storyworld."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--trial-id", choices=sorted(TRIALS))
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero_name or rng.choice(["Luna", "Mira", "Tessa", "Nell"])
    helper = args.helper_name or rng.choice(["Pip", "Rowan", "the Old Wizard", "Aunt Fern"])
    index = sample_seed if sample_seed is not None else rng.randrange(2**31)
    trial_id = args.trial_id or list(TRIALS)[index % len(TRIALS)]
    mode = MODES[(index // len(TRIALS)) % len(MODES)]
    detail = (index // (len(TRIALS) * len(MODES))) % len(BRIDGES)
    return StoryParams(
        place=place,
        hero_name=hero,
        helper_name=helper,
        trial_id=trial_id,
        telling_mode=mode,
        detail_id=detail,
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
    lines = ["--- world trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for vessel in world.vessels.values():
        lines.append(
            f"{vessel.id}: capacity={vessel.capacity} color={vessel.color} safe_for={vessel.safe_for}"
        )
    return "\n".join(lines)


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


CURATED = [
    StoryParams(
        place="moonlit_hill",
        hero_name="Luna",
        helper_name="Pip",
        trial_id="moonwater",
        telling_mode="clue_first",
        detail_id=0,
    ),
    StoryParams(
        place="rose_tower",
        hero_name="Mira",
        helper_name="Rowan",
        trial_id="dew",
        telling_mode="rhyme_first",
        detail_id=1,
    ),
    StoryParams(
        place="whispering_wood",
        hero_name="Tessa",
        helper_name="Aunt Fern",
        trial_id="ember_soup",
        telling_mode="helper_first",
        detail_id=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(sorted(asp_valid_trials())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed), seed)
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
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
