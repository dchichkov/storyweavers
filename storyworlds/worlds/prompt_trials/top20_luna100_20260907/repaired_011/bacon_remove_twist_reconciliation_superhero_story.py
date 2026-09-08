#!/usr/bin/env python3
"""
A small standalone superhero storyworld about bacon, a twist, and reconciliation.

A young hero must remove a runaway bacon banner from a city clock before it
causes trouble. The hero's rival helps, and an honest conversation turns a
mess into a friendship.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str
    rival: str
    helper: str
    city: str
    bacon_style: str
    problem: int = 0
    premise: int = 0
    twist: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


HEROES = ["Luna", "Nova", "Sol", "Comet", "Mira", "Bolt"]
RIVALS = ["Shadow Fox", "Captain Crumb", "Gale Girl", "Dr. Sizzle", "Mister Mist"]
HELPERS = ["Pip", "Tess", "Rafi", "Jo", "Nell", "Wren"]
CITIES = ["Brighton", "Moonbeam City", "Star Harbor", "Sunrise Town", "Cloudtop"]
BACON_STYLES = ["crispy bacon", "smoky bacon", "maple bacon", "peppery bacon"]


PROBLEMS = [
    {
        "lead": "At breakfast, {hero} powered up a huge bacon banner for the city's hero parade.",
        "trigger": "A warm gust tore the banner loose, and it wrapped around the hands of the giant clock.",
        "risk": "The clock began to slow, so everyone below might miss the school-bus bell.",
        "action": "{hero} flew close, but the banner's sticky maple corner snagged on a gear.",
        "cause": "the wind wrapped a bacon parade banner around the city clock",
        "deed": "flew near the clock and tried to free the sticky corner",
        "result": "the banner was removed without stopping the clock",
    },
    {
        "lead": "{hero} carried a basket of bacon to the rooftop rescue club's picnic.",
        "trigger": "A gust lifted the picnic cloth, and the basket slid toward a roof drain.",
        "risk": "If the basket blocked the drain, rainwater could flood the club below.",
        "action": "{hero} reached for the basket, but a bacon strip hooked around the drain's metal grate.",
        "cause": "a picnic cloth sent a bacon basket sliding toward a roof drain",
        "deed": "grabbed the basket and noticed the bacon caught on the grate",
        "result": "the bacon was removed and the drain stayed clear",
    },
    {
        "lead": "{hero} helped decorate the community center with a shiny bacon-shaped signal.",
        "trigger": "The signal's shiny strip reflected sunlight into every window across the square.",
        "risk": "Drivers shielded their eyes, and the neighborhood grew confused.",
        "action": "{hero} climbed the signal, but the strip had twisted around a loose cable.",
        "cause": "a shiny bacon decoration reflected sunlight across the square",
        "deed": "climbed up and found the strip twisted around a cable",
        "result": "the bright strip was removed and the windows were safe again",
    },
    {
        "lead": "{hero} promised to deliver breakfast to the tired night-watch team.",
        "trigger": "A small robot vacuum rolled through the station and carried the bacon tray away.",
        "risk": "The tray headed straight toward the open elevator shaft.",
        "action": "{hero} blocked the robot, but the tray slid under a bench beside the shaft.",
        "cause": "a robot vacuum carried a bacon tray toward an open elevator shaft",
        "deed": "blocked the robot and searched beneath the nearby bench",
        "result": "the tray was removed from danger and delivered to the watch team",
    },
]

TWISTS = [
    "Then came the twist: the rival had not caused the trouble. The rival had secretly tied a safety cord to the banner, and that cord was the only reason it had not fallen.",
    "The twist surprised everyone. The bacon basket belonged to the rival, who had brought it for the rescue club's shared breakfast.",
    "A second twist appeared in the sunlight: the shiny strip was not a villain's weapon at all. It was a thank-you gift that the rival had made by hand.",
    "The twist was hidden under the bench. The rival's lost lunch note explained that the rival had planned to apologize before the accident began.",
]

RECONCILIATIONS = [
    "'I thought you wanted to make trouble,' said {hero}. 'I thought you wanted to take all the credit,' said {rival}. They listened to each other, then agreed to share the next rescue.",
    "'You saved my breakfast,' said {rival}. 'You saved the clock,' said {hero}. The two heroes shook hands and chose a team name: the Bacon Brigade.",
    "'I should have asked before blaming you,' {hero} admitted. {rival} nodded. 'And I should have explained my plan.' Together, they packed the safe leftovers for the helpers.",
    "'We both rushed,' said {hero}. 'We both can slow down,' said {rival}. Their honest words changed the quarrel into a promise to work side by side.",
]

ENDINGS = [
    "That evening, the city clock chimed on time. A tiny bacon badge on its base reminded everyone that brave heroes remove danger and make room for second chances.",
    "At sunset, the rescue club shared the bacon picnic on a clean rooftop. {hero} and {rival} laughed when their new team flag curled into a breakfast mustache.",
    "The next parade carried a smaller, safer banner. This time {hero} and {rival} held it together, while the crowd cheered for their fresh friendship.",
    "Before bed, {helper} drew two capes on the team's notice board. Under them were the words, 'Courage helps, but listening saves the day.'",
]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

hero(H) :- hero_name(H).
rival(R) :- rival_name(R).
helper(P) :- helper_name(P).
city(C) :- city_name(C).
bacon_style(B) :- bacon_name(B).

valid(H, R, B) :- hero_name(H), rival_name(R), bacon_name(B), H != R.
valid_story(H, R, C, B) :- valid(H, R, B), city_name(C).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for item in HEROES:
        lines.append(asp.fact("hero_name", item))
    for item in RIVALS:
        lines.append(asp.fact("rival_name", item))
    for item in HELPERS:
        lines.append(asp.fact("helper_name", item))
    for item in CITIES:
        lines.append(asp.fact("city_name", item))
    for item in BACON_STYLES:
        lines.append(asp.fact("bacon_name", item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    expected = {
        (hero, rival, bacon)
        for hero in HEROES
        for rival in RIVALS
        for bacon in BACON_STYLES
        if hero != rival
    }
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: clingo gate matches Python validity ({len(actual)} combinations).")
        return 0
    print("MISMATCH between Python and clingo validity.")
    print("Only in Python:", sorted(expected - actual))
    print("Only in clingo:", sorted(actual - expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about bacon, removal, and reconciliation."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--rival", choices=RIVALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("--bacon-style", choices=BACON_STYLES, dest="bacon_style")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    rival = args.rival or rng.choice(RIVALS)
    if hero == rival:
        raise StoryError("The hero and rival must be different characters.")
    return StoryParams(
        hero=hero,
        rival=rival,
        helper=args.helper or rng.choice(HELPERS),
        city=args.city or rng.choice(CITIES),
        bacon_style=args.bacon_style or rng.choice(BACON_STYLES),
        problem=rng.randrange(len(PROBLEMS)),
        premise=rng.randrange(len(PROBLEMS)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.problem = seed % len(PROBLEMS)
    params.premise = (seed // len(PROBLEMS)) % len(PROBLEMS)
    params.twist = (seed // 3) % len(TWISTS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    problem = PROBLEMS[params.problem % len(PROBLEMS)]
    values = {
        "hero": params.hero,
        "rival": params.rival,
        "helper": params.helper,
        "city": params.city,
        "bacon_style": params.bacon_style,
    }

    world = World()
    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            label=params.hero,
            memes={"courage": 1.0, "trust": 0.0},
        )
    )
    rival = world.add(
        Entity(
            id=params.rival,
            kind="character",
            label=params.rival,
            memes={"pride": 1.0, "trust": 0.0},
        )
    )
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper))
    bacon = world.add(
        Entity(
            id="bacon",
            kind="food",
            label=params.bacon_style,
            meters={"danger": 0.0},
            memes={"importance": 1.0},
        )
    )
    clock = world.add(
        Entity(
            id="city_clock",
            kind="place",
            label=f"{params.city} clock",
            meters={"working": 1.0},
            memes={"attention": 0.0},
        )
    )

    world.say(
        f"In {params.city}, {params.hero} was known as a superhero who could lift a bus, "
        f"but never wasted a crumb of {params.bacon_style}."
    )
    world.say(
        f"One bright morning, {params.helper} asked {params.hero} and {params.rival} "
        f"to help prepare the city's hero parade."
    )
    world.say(problem["lead"].format(**values))

    world.para()
    bacon.meters["danger"] = 1.0
    clock.memes["attention"] = 1.0
    world.say(problem["trigger"].format(**values))
    world.say(problem["risk"].format(**values))
    world.say(problem["action"].format(**values))
    world.say(f"'Careful!' cried {params.helper}. 'The {params.bacon_style} is close to the danger!'")
    world.say(f"'I can remove it,' said {params.hero}.")
    world.say(f"'Not alone,' said {params.rival}. 'Let me hold the loose end.'")

    world.para()
    world.say(TWISTS[params.twist % len(TWISTS)].format(**values))
    world.say(problem["deed"].capitalize() + ".")
    bacon.meters["danger"] = 0.0
    clock.meters["working"] = 1.0
    hero.memes["trust"] = 1.0
    rival.memes["trust"] = 1.0
    world.say(f"Working together, {params.hero} and {params.rival} carefully removed the bacon from the trouble spot.")
    world.say(RECONCILIATIONS[params.twist % len(RECONCILIATIONS)].format(**values))

    world.para()
    hero.memes["relief"] = 1.0
    rival.memes["relief"] = 1.0
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        hero=params.hero,
        rival=params.rival,
        helper=params.helper,
        city=params.city,
        bacon=params.bacon_style,
        danger_cause=problem["cause"],
        helpful_action=problem["deed"],
        result=problem["result"],
        twist=TWISTS[params.twist % len(TWISTS)],
        reconciled=True,
        resolved=True,
    )

    prompts = [
        "Write a child-friendly superhero story about bacon, a dangerous twist, and reconciliation.",
        f"Tell a superhero story in which {params.hero} and {params.rival} must remove bacon from danger in {params.city}.",
        f"Write a story where a superhero problem creates a twist, but honest dialogue helps {params.hero} and {params.rival} become a team.",
    ]

    story_qa = [
        QAItem(
            question="Who were the two superheroes in the story?",
            answer=f"{params.hero} and {params.rival} were the two superheroes who worked together.",
        ),
        QAItem(
            question="What caused the danger?",
            answer=f"The danger began because {problem['cause']}.",
        ),
        QAItem(
            question="What did the heroes remove?",
            answer=f"They carefully removed the {params.bacon_style} from the dangerous spot.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {TWISTS[params.twist % len(TWISTS)].split('.')[0].lower()}.",
        ),
        QAItem(
            question="How did the heroes reconcile?",
            answer=f"They reconciled by listening, speaking honestly, and agreeing to work together instead of blaming each other.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero uses courage, helpful skills, and good judgment to protect people and solve problems.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away from a place, especially when it is causing trouble.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes readers understand the problem or characters in a new way.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and finding a way to cooperate.",
        ),
        QAItem(
            question="Why should people be careful around moving machines?",
            answer="People should be careful around moving machines because loose objects can get caught and cause injuries or damage.",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:12} ({entity.kind:9}) {' '.join(details)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Shadow Fox", "Pip", "Brighton", "crispy bacon", 0, 0, 0, 0),
        StoryParams("Nova", "Captain Crumb", "Tess", "Moonbeam City", "maple bacon", 1, 1, 1, 1),
        StoryParams("Sol", "Gale Girl", "Rafi", "Star Harbor", "smoky bacon", 2, 2, 2, 2),
        StoryParams("Comet", "Dr. Sizzle", "Jo", "Sunrise Town", "peppery bacon", 3, 3, 3, 3),
    ]


CURATED = build_curated()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} valid hero, rival, and bacon combinations:\n")
        for hero, rival, bacon in combinations[:40]:
            print(f"  {hero} + {rival} + {bacon}")
        if len(combinations) > 40:
            print(f"  ... and {len(combinations) - 40} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero}: the {sample.params.bacon_style} rescue"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
