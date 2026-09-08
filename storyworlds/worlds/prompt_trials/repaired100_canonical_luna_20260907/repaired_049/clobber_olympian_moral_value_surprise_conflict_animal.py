#!/usr/bin/env python3
"""
A child-facing animal storyworld about clobber, an olympian contest, and the
moral value of helping instead of winning by force.
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

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
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
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Challenge:
    id: str
    obstacle: str
    surprise: str
    first_choice: str
    clue: str
    careful_action: str
    result: str
    moral_value: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
    place: str
    animal: str
    name: str
    rival: str
    guide: str
    challenge: str
    trait: str
    seed: Optional[int] = None


SETTING = Setting(
    place="the sunny meadow arena",
    affords={"running", "jumping", "helping", "sharing"},
)

CHALLENGES = {
    "river_race": Challenge(
        id="river_race",
        obstacle="A spring flood spread shiny stones across the narrow racing path.",
        surprise="A sudden splash showed that the largest stone was loose and rocked whenever a paw touched it.",
        first_choice="The young runner wanted to clobber the loose stone aside and race on alone.",
        clue="The reeds bent toward a shallow crossing hidden behind the loose stone.",
        careful_action="asked the other animals to hold a vine, guided the smallest runners over the shallow crossing, and left the loose stone undisturbed",
        result="Everyone crossed safely, and the runners reached the finish together.",
        moral_value="Courage is stronger when it protects someone smaller than oneself.",
        ending="The animals hung a vine ribbon at the safe crossing, and the river flashed beneath it.",
    ),
    "hill_hurdles": Challenge(
        id="hill_hurdles",
        obstacle="Wind knocked the straw hurdles across the steep hill course.",
        surprise="One hurdle rolled downhill and revealed a sleepy hedgehog beneath it.",
        first_choice="The proud runner nearly tried to clobber every hurdle out of the way.",
        clue="The hedgehog's tiny tracks showed that the course could be turned into a gentle zigzag.",
        careful_action="moved the hurdles into a zigzag, carried the hedgehog to shade, and invited the slower animals to try first",
        result="The course became safe, and even the slowest runner finished smiling.",
        moral_value="A true champion makes room for others instead of trampling their path.",
        ending="The straw hurdles stood in a friendly zigzag while the hedgehog napped under a clover leaf.",
    ),
    "moonbeam_leap": Challenge(
        id="moonbeam_leap",
        obstacle="Clouds covered the white marks that showed where to leap over the moonlit ditch.",
        surprise="A silver frog sprang from the ditch and landed on a hidden stepping log.",
        first_choice="The young athlete thought about clobbering the cloudy marker post to make a new path.",
        clue="The frog's leap revealed three firm logs beneath the water grass.",
        careful_action="tested each log with a reed, called the safe steps aloud, and waited for every animal to cross",
        result="The whole group crossed without a splash, and the moon returned to the course.",
        moral_value="Patience turns a surprising problem into shared knowledge.",
        ending="Moonlight rested on the three safe logs as frogs sang below the finish flag.",
    ),
    "orchard_strength": Challenge(
        id="orchard_strength",
        obstacle="A fallen apple branch blocked the orchard strength course.",
        surprise="A nest of baby wrens trembled inside the branch.",
        first_choice="The strong contestant lifted a paw to clobber the branch apart.",
        clue="The wrens grew quiet whenever the branch was lifted gently toward the low fence.",
        careful_action="called for soft wings and careful paws, slid the branch to the fence, and left the nest in its leafy fork",
        result="The path opened while the baby wrens stayed safe and calm.",
        moral_value="Real strength is gentle enough to carry what cannot speak.",
        ending="The wrens chirped from their safe nest while apples rolled across the newly opened course.",
    ),
}

ANIMALS = [
    ("hare", "hare", "swift"),
    ("otter", "otter", "playful"),
    ("fox", "fox", "clever"),
    ("badger", "badger", "steady"),
    ("squirrel", "squirrel", "lively"),
    ("tortoise", "tortoise", "patient"),
]

NAMES = ["Luna", "Pip", "Milo", "Nia", "Clover", "Tavi", "Bram", "Mina"]
RIVALS = ["a boastful magpie", "a noisy young wolf", "a proud peacock", "a quick-footed weasel"]
GUIDES = ["an old owl", "a gentle doe", "a patient crane", "a kind field mouse"]
TRAITS = ["curious", "brave", "kind", "quick-thinking", "patient", "gentle"]

DIALOGUES = [
    "What if winning means helping everyone arrive?",
    "Did anyone notice what the path is trying to tell us?",
    "Should we look before we push?",
    "Who needs our help first?",
    "Can strength be gentle here?",
    "What changed when that stone moved?",
]

OPENINGS = [
    "Every summer, the meadow animals held an olympian day of races, leaps, and brave little trials.",
    "On a bright morning, the meadow became an olympian arena where animals came to test their feet and hearts.",
    "The animals polished the finish bell for their yearly olympian games.",
    "At sunrise, flags fluttered over the meadow, and every animal dreamed of an olympian victory.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, animal, challenge) for place in ["meadow"] for animal in CHALLENGES for challenge in CHALLENGES]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an animal story about an olympian contest, clobbering, and moral value."
    )
    parser.add_argument("--place", choices=["meadow"])
    parser.add_argument("--animal", choices=[a[0] for a in ANIMALS])
    parser.add_argument("--challenge", choices=list(CHALLENGES))
    parser.add_argument("--name")
    parser.add_argument("--rival")
    parser.add_argument("--guide")
    parser.add_argument("--trait", choices=TRAITS)
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
    animal = args.animal or rng.choice(ANIMALS)[0]
    name = args.name or rng.choice(NAMES)
    rival = args.rival or rng.choice(RIVALS)
    guide = args.guide or rng.choice(GUIDES)
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    trait = args.trait or rng.choice(TRAITS)
    if challenge not in CHALLENGES:
        raise StoryError("Unknown olympian challenge.")
    return StoryParams(
        place=args.place or "meadow",
        animal=animal,
        name=name,
        rival=rival,
        guide=guide,
        challenge=challenge,
        trait=trait,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "meadow":
        raise StoryError("The olympian animal contest belongs in the meadow.")
    if params.challenge not in CHALLENGES:
        raise StoryError("The selected challenge is not part of this storyworld.")
    if not params.name.strip():
        raise StoryError("The animal needs a name.")
    if params.name.lower() == params.rival.lower():
        raise StoryError("The runner and rival must be different characters.")


def tell(world: World, params: StoryParams) -> None:
    challenge = CHALLENGES[params.challenge]
    animal_label = dict((a, b) for a, b, _ in ANIMALS)[params.animal]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=f"{params.name} the {animal_label}",
        memes={"hope": 1.0, "pride": 1.0},
    ))
    rival = world.add(Entity(
        id="Rival",
        kind="character",
        type="animal",
        label=params.rival,
        memes={"boast": 1.0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type="animal",
        label=params.guide,
        memes={"wisdom": 1.0},
    ))
    world.add(Entity(
        id="Course",
        kind="place",
        type="arena",
        label="the meadow course",
        meters={"hazard": 1.0},
    ))

    variant = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c)
        for i, c in enumerate(
            f"{params.name}|{params.animal}|{params.challenge}|{params.trait}"
        )
    )
    opening = OPENINGS[variant % len(OPENINGS)]
    dialogue = DIALOGUES[(variant // len(OPENINGS)) % len(DIALOGUES)]

    world.say(
        f"{opening} {hero.label} was a {params.trait} {animal_label} who had practiced every morning."
    )
    world.say(
        f"{params.rival.capitalize()} strutted beside the starting line and said, "
        f"\"Only the strongest can win this olympian day.\""
    )
    world.say(
        f"{hero.label} answered, \"I want to run well, but I also want the meadow to stay safe.\""
    )
    world.para()

    world.say(f"The first trial brought trouble: {challenge.obstacle}")
    world.say(f"{params.rival.capitalize()} shouted, \"Clobber it and keep moving!\"")
    world.say(f"{hero.label} almost listened. Then came a surprise: {challenge.surprise}")
    world.say(
        f"{guide.label.capitalize()} called, \"{dialogue}\""
    )
    world.say(f"{hero.label} looked again and noticed that {challenge.clue}")
    world.para()

    world.say(f"At first, {hero.label} thought, \"{challenge.first_choice}\"")
    world.say(
        f"But the runner took a breath, chose care over clobbering, and {challenge.careful_action}."
    )
    hero.meters["helping"] = 1.0
    hero.memes["trust"] = 1.0
    rival.memes["respect"] = 1.0
    world.say(f"The result was clear: {challenge.result}")
    world.para()

    world.say(
        f"The guide smiled and said, \"The olympian prize is not only the finish bell. "
        f"It is the good choice made when nobody expects it.\""
    )
    world.say(
        f"{hero.label} learned the moral value that {challenge.moral_value}"
    )
    world.say(challenge.ending)

    world.facts.update(
        hero=hero,
        rival=rival,
        guide=guide,
        challenge=challenge,
        animal_label=animal_label,
        dialogue=dialogue,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    challenge = world.facts["challenge"]
    return [
        f"Write an animal story about {hero.label} in an olympian meadow contest.",
        f"Include a surprise conflict where clobbering seems easy, but {hero.label} chooses a moral value.",
        f"Tell how {hero.label} solves this problem: {challenge.obstacle}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    guide = f["guide"]
    challenge = f["challenge"]
    return [
        QAItem(
            question=f"Who entered the olympian animal contest?",
            answer=f"{hero.label} entered the olympian contest in the meadow.",
        ),
        QAItem(
            question="What conflict interrupted the contest?",
            answer=f"The conflict was that {challenge.obstacle}",
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was that {challenge.surprise}",
        ),
        QAItem(
            question=f"What did {rival.label} suggest?",
            answer=f"{rival.label.capitalize()} suggested clobbering the obstacle and rushing onward.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the problem?",
            answer=f"{hero.label} noticed that {challenge.clue} Then {hero.label} {challenge.careful_action}.",
        ),
        QAItem(
            question=f"What did {guide.label} help {hero.label} understand?",
            answer=f"{guide.label.capitalize()} helped {hero.label} understand that looking carefully was better than using force.",
        ),
        QAItem(
            question="What moral value did the story show?",
            answer=f"The story showed that {challenge.moral_value}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does clobber mean?",
            answer="To clobber means to hit or knock something hard, often with more force than is needed.",
        ),
        QAItem(
            question="What is an olympian contest?",
            answer="An olympian contest is a special athletic competition in which participants test skills such as running, jumping, or strength.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good principle, such as kindness, fairness, courage, or care for others, that guides a choice.",
        ),
        QAItem(
            question="Why can a surprise change a conflict?",
            answer="A surprise can reveal new information, so characters may choose a safer or kinder solution than their first plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(meadow, river_race).
valid(meadow, hill_hurdles).
valid(meadow, moonbeam_leap).
valid(meadow, orchard_strength).

moral_value(river_race, protect_small).
moral_value(hill_hurdles, make_room).
moral_value(moonbeam_leap, share_knowledge).
moral_value(orchard_strength, gentle_strength).

safe_solution(Challenge) :- valid(meadow, Challenge), moral_value(Challenge, _).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "meadow"),
            asp.fact("seed_word", "clobber"),
            asp.fact("seed_word", "olympian"),
            asp.fact("feature", "moral_value"),
            asp.fact("feature", "surprise"),
            asp.fact("feature", "conflict"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(place, challenge) for place, _, challenge in valid_combos()}
    cl = set(asp_valid_combos())
    if py != cl:
        print(f"MISMATCH: Python={sorted(py)} ASP={sorted(cl)}")
        return 1
    print(f"OK: ASP matches Python ({len(py)} combinations).")
    return 0


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
    StoryParams("meadow", "hare", "Luna", "a boastful magpie", "an old owl", "river_race", "curious"),
    StoryParams("meadow", "otter", "Pip", "a proud peacock", "a gentle doe", "hill_hurdles", "kind"),
    StoryParams("meadow", "fox", "Milo", "a quick-footed weasel", "a patient crane", "moonbeam_leap", "clever"),
    StoryParams("meadow", "badger", "Nia", "a noisy young wolf", "a kind field mouse", "orchard_strength", "brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + index
            index += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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
        if args.all:
            header = f"### {sample.params.name}: {sample.params.challenge}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
