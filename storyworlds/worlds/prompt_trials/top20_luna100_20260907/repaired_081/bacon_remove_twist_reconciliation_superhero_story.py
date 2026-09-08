#!/usr/bin/env python3
"""
Story world: a tiny superhero story about bacon, a twist, and reconciliation.

A young hero tries to remove a troublesome smell from a neighborhood kitchen.
A surprising clue changes the plan, and a disagreement is repaired through
honest conversation and shared work.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class City:
    name: str
    place: str
    landmark: str


@dataclass
class StoryParams:
    city: str = "Brightbridge"
    hero_name: str = "Nova"
    helper_name: str = "Pip"
    problem: str = "bacon"
    feature: str = "Twist"
    style: str = "Superhero Story"
    seed: Optional[int] = None


CITIES = {
    "Brightbridge": City("Brightbridge", "the rooftop kitchen above Market Street", "the Moonbeam Tower"),
    "Sunvale": City("Sunvale", "the little firehouse kitchen", "the Golden Clock"),
    "Cloud Harbor": City("Cloud Harbor", "the café beside the sky-train", "the silver lighthouse"),
}

HERO_NAMES = ["Nova", "Dash", "Ember", "Beacon", "Skye"]
HELPER_NAMES = ["Pip", "Mira", "Jo", "Tess", "Rafi"]

PROBLEMS = ["bacon", "smoke", "sirens", "sticky syrup"]

TWISTS = {
    "bacon": {
        "premise": "A strong bacon smell floated from the community kitchen and chased people away from the morning food table.",
        "attempt": "{hero} tried to remove the smell by opening every window and waving a cape-sized towel.",
        "clue": "{helper} noticed that the smell was strongest near a cracked vent, not near the frying pan.",
        "change": "They moved the cooling bacon to a covered tray, cleaned the vent filter, and placed a small fan toward the rooftop garden.",
        "result": "The smell became gentle enough for neighbors to return, and the bacon stayed warm for everyone.",
        "lesson": "look for the real source before trying to remove a problem",
        "ending": "At sunrise, the heroes shared the last crisp strip of bacon beneath the city lights.",
    },
    "smoke": {
        "premise": "Gray smoke curled through the youth center whenever someone toasted bread.",
        "attempt": "{hero} tried to remove it by flapping a blanket, which pushed the smoke toward the reading corner.",
        "clue": "{helper} found a blocked filter behind the old toaster hood.",
        "change": "They switched off the toaster, cleared the filter with an adult, and tested the hood before cooking again.",
        "result": "The air turned clear while breakfast continued safely.",
        "lesson": "careful checking is stronger than hurried action",
        "ending": "The clean windows reflected two capes and a breakfast table full of smiles.",
    },
    "sirens": {
        "premise": "A practice alarm blared whenever the community kitchen door opened.",
        "attempt": "{hero} tried to remove the noise by holding the door shut, but then nobody could carry food inside.",
        "clue": "{helper} discovered that a loose sensor was brushing the metal frame.",
        "change": "They marked the sensor for the repair team and used a quiet side entrance until it was fixed.",
        "result": "People could enter safely without confusing the practice alarm with an emergency.",
        "lesson": "a temporary solution should protect people while the real fix is prepared",
        "ending": "The repaired door swung softly as the heroes led the first breakfast inside.",
    },
    "sticky syrup": {
        "premise": "Syrup from the pancake table spread across the kitchen floor like a shining trap.",
        "attempt": "{hero} tried to remove it with one giant cape sweep, which scattered sticky drops farther.",
        "clue": "{helper} saw that the spill began beneath a loose pitcher handle.",
        "change": "They blocked the path, asked for a mop, and replaced the cracked pitcher before cleaning the whole floor.",
        "result": "The floor became safe again, and no one slipped while carrying breakfast.",
        "lesson": "solve the cause as well as the mess",
        "ending": "The new pitcher gleamed beside a clean floor where every hero could walk safely.",
    },
}

ASP_RULES = r"""
city(C) :- city_name(C).
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
food(F) :- food_name(F).
twist(P) :- twist_name(P).
reconciled(H1,H2) :- apology(H1,H2), listening(H2,H1).
problem_solved(P) :- clue_found(P), repair_done(P).
heroic(H) :- hero(H), brave(H), kind(H), reconciled(H,Other).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name in CITIES:
        lines.append(asp.fact("city_name", name))
    lines.extend([
        asp.fact("hero_name", "hero"),
        asp.fact("helper_name", "helper"),
        asp.fact("food_name", "bacon"),
        asp.fact("twist_name", "bacon"),
        asp.fact("clue_found", "bacon"),
        asp.fact("repair_done", "bacon"),
        asp.fact("brave", "hero"),
        asp.fact("kind", "hero"),
        asp.fact("apology", "hero", "helper"),
        asp.fact("listening", "helper", "hero"),
    ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = asp.one_model(
        asp_program(
            "#show problem_solved/1.\n"
            "#show reconciled/2.\n"
            "#show heroic/2."
        )
    )
    names = set()
    for sym in shown:
        args = tuple(
            a.string if a.type == a.type.String
            else a.number if a.type == a.type.Number
            else a.name
            for a in sym.arguments
        )
        names.add((sym.name, args))
    expected = {
        ("problem_solved", ("bacon",)),
        ("reconciled", ("hero", "helper")),
        ("heroic", ("hero", "helper")),
    }
    if names == expected:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(names))
    print("PY :", sorted(expected))
    return 1


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero story about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--city", choices=list(CITIES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    city = args.city or rng.choice(list(CITIES))
    hero = args.name or rng.choice(HERO_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(helper_choices)
    if hero == helper:
        raise StoryError("The hero and helper must be different people.")
    if args.helper and args.helper not in HELPER_NAMES:
        raise StoryError(f"Unknown helper: {args.helper}")
    return StoryParams(
        city=city,
        hero_name=hero,
        helper_name=helper,
        problem=rng.choice(PROBLEMS),
        feature="Twist",
        style="Superhero Story",
    )


def generate(params: StoryParams) -> StorySample:
    if params.city not in CITIES:
        raise StoryError(f"Unknown city: {params.city}")
    if params.problem not in TWISTS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.hero_name == params.helper_name:
        raise StoryError("A hero cannot be their own helper.")

    city = CITIES[params.city]
    incident = TWISTS[params.problem]
    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.city}:{params.hero_name}:{params.helper_name}:{params.problem}"
    )

    world = World(city)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero_name,
        phrase=f"the superhero {params.hero_name}",
        meters={"courage": 1.0, "worry": 0.0},
        memes={"kindness": 1.0, "trust": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper_name,
        phrase=f"{params.helper_name}, the observant helper",
        meters={"attention": 1.0},
        memes={"patience": 1.0, "trust": 1.0},
    ))
    bacon = world.add(Entity(
        id="bacon",
        kind="food",
        label="bacon",
        phrase="a warm tray of bacon",
        owner="community",
        meters={"warmth": 1.0, "smell": 1.0},
        memes={"welcome": 1.0},
    ))

    world.say(
        f"In {city.name}, {params.hero_name} was known as a superhero who helped ordinary people with extraordinary care."
    )
    world.say(
        f"One bright morning, the hero hurried to {city.place}, where {bacon.phrase} waited for the neighborhood breakfast."
    )
    world.say(incident["premise"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"“I will remove this trouble before anyone is disappointed,” {params.hero_name} promised."
    )
    world.say(incident["attempt"].format(hero=params.hero_name, helper=params.helper_name))
    hero.meters["worry"] += 1.0
    bacon.meters["smell"] += 1.0
    world.say(
        f"“Wait,” said {params.helper_name}. “What if we find where the trouble begins instead of fighting every sign of it?”"
    )
    world.say(
        f"{params.hero_name} lowered the towel. “You are right. I was trying to be fast, not helpful.”"
    )
    world.say(incident["clue"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"The clue was the twist in the case: the bacon was not the whole problem. A nearby part of the kitchen was changing what happened."
    )
    world.say(
        f"{params.hero_name} apologized. “I brushed aside your idea. Will you help me solve this?”"
    )
    world.say(
        f"{params.helper_name} smiled. “Yes. Let us use both your courage and my careful eyes.”"
    )
    hero.memes["trust"] += 1.0
    helper.memes["trust"] += 1.0
    world.say(incident["change"].format(hero=params.hero_name, helper=params.helper_name))
    bacon.meters["smell"] = 0.0
    bacon.meters["warmth"] = 1.0
    world.say(
        f"Together they tested the kitchen once more. {incident['result'].format(hero=params.hero_name, helper=params.helper_name)}"
    )
    world.say(
        f"The reconciliation mattered as much as the repair: the two friends had disagreed, listened, and chosen to trust each other again."
    )
    world.say(
        f"{params.hero_name} recorded the lesson: “{incident['lesson'].capitalize()}.”"
    )
    world.say(incident["ending"].format(hero=params.hero_name, helper=params.helper_name))

    world.facts.update(
        hero=hero,
        helper=helper,
        bacon=bacon,
        city=city,
        problem=params.problem,
        twist=True,
        reconciled=True,
        solved=True,
        lesson=incident["lesson"],
        clue=incident["clue"].format(hero=params.hero_name, helper=params.helper_name),
        repair=incident["change"].format(hero=params.hero_name, helper=params.helper_name),
    )

    prompts = [
        f"Write a Superhero Story about {params.hero_name} helping with bacon in {city.name}.",
        f"Include a Twist where the real source of the problem is not the obvious one: {incident['clue'].format(hero=params.hero_name, helper=params.helper_name)}",
        f"Include Reconciliation between {params.hero_name} and {params.helper_name}, followed by a practical repair.",
    ]

    story_qa = [
        QAItem(
            question="What problem did the heroes face?",
            answer=incident["premise"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the obvious problem was not the whole cause: {incident['clue'].format(hero=params.hero_name, helper=params.helper_name)}",
        ),
        QAItem(
            question="How did the heroes reconcile?",
            answer=f"{params.hero_name} apologized for ignoring {params.helper_name}'s idea, and {params.helper_name} agreed to help after they listened to each other.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=incident["change"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="What lesson did the superhero learn?",
            answer=f"{params.hero_name} learned that {incident['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a fictional person with unusual abilities or courage who uses them to help others.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a disagreement by listening, apologizing when needed, and choosing to cooperate again.",
        ),
        QAItem(
            question="Why should someone find the source of a problem?",
            answer="Finding the source helps a person fix the cause instead of only hiding or removing the visible result.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show problem_solved/1.\n#show reconciled/2.\n#show heroic/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, city in enumerate(CITIES):
            params = StoryParams(
                city=city,
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                problem=PROBLEMS[index % len(PROBLEMS)],
                feature="Twist",
                style="Superhero Story",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
