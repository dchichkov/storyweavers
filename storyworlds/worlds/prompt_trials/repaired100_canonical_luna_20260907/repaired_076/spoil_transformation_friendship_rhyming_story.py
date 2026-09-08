#!/usr/bin/env python3
"""A gentle rhyming StoryWorld about spoiled treasure, transformation, and friendship."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ("Luna", "Milo", "Nia", "Pip")
FRIENDS = ("Tavi", "Bea", "Ollie", "Suri")
PLACES = ("the moonlit garden", "the little orchard", "the ribbon meadow", "the sunny lane")
OBJECTS = ("a berry cake", "a basket of peaches", "a honey bun", "a basket of plums")
MODES = ("bells", "claps", "whispers", "drums")


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend: str = "Tavi"
    setting: str = "the moonlit garden"
    treat: str = "a berry cake"
    telling_mode: str = "bells"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


@dataclass(frozen=True)
class Scenario:
    key: str
    discovery: str
    clue: str
    tempting_choice: str
    action: str
    dialogue: str
    transformation: str
    lesson: str
    ending: str


SCENARIOS = (
    Scenario(
        "moldy_cake",
        "the berry cake had been left too long beneath a warm cloth",
        "a green spot and a sour smell warned that the cake had spoiled",
        "hide the spoiled cake and serve it anyway",
        "told the truth, carried the cake to the compost, and asked the friend to help make a fresh snack",
        "A spoiled treat is not a treat to share; we can change our plan with care",
        "the spoiled cake became compost for flowers, while a fresh berry snack brought smiles",
        "honesty can turn a disappointing mistake into a useful new beginning",
        "By moonrise, bright flowers grew beside the compost, and two friends shared a fresh berry tart.",
    ),
    Scenario(
        "rainy_peaches",
        "the basket of peaches waited through a rainy afternoon",
        "soft brown patches showed that some peaches had spoiled",
        "blame the friend who packed the basket",
        "sorted the good fruit, set the spoiled pieces aside, and invited the friend to make peach prints",
        "the sad basket became a bright art table with fruit-print pictures",
        "friends can solve a problem without turning it into blame",
        "Peach suns covered the table, and the friends laughed beneath the silver rain.",
    ),
    Scenario(
        "honey_bun",
        "the honey bun rested in a warm pocket during a long walk",
        "its sticky wrapper and odd smell showed it had spoiled",
        "pretend the bun still tasted fine",
        "checked it together, discarded it safely, and shared crunchy apples from the picnic bag",
        "a spoiled snack became a lesson in noticing clues and caring for one another",
        "a truthful pause protects friends better than a hurried bite",
        "The empty apple bowl shone in the grass while the honey bun rested safely in the bin.",
    ),
    Scenario(
        "plum_basket",
        "the basket of plums had tipped beneath the old tree",
        "bruises and a fuzzy coat showed which plums had spoiled",
        "throw away the whole basket in a rush",
        "examined each plum, saved the sound ones, and used the spoiled fruit to feed the garden compost",
        "a mixed-up basket became a careful sorting game",
        "patience helps us save what is still good",
        "The sound plums filled a blue bowl, and the compost warmed the roots below.",
    ),
)
SCENARIO_BY_KEY = {item.key: item for item in SCENARIOS}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming storyworld about spoil, transformation, and friendship.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--setting", choices=PLACES)
    parser.add_argument("--treat", choices=OBJECTS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        setting=args.setting or rng.choice(PLACES),
        treat=args.treat or rng.choice(OBJECTS),
        telling_mode=rng.choice(MODES),
        variant=rng.randrange(1, 2**31),
    )


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(params.name, "character", params.name, meters={"care": 0.7}, memes={"joy": 0.7}))
    friend = world.add(Entity(params.friend, "character", params.friend, meters={"care": 0.8}, memes={"trust": 0.7}))
    world.add(Entity("treat", "food", params.treat, owner=params.name, meters={"freshness": 0.5}))
    world.add(Entity("garden", "place", params.setting, meters={"growth": 0.5}))
    world.facts.update(child=child.label, friend=friend.label, treat=params.treat, setting=params.setting)
    return world


def simulate(world: World, scenario: Scenario) -> World:
    p = world.params
    child = world.entities[p.name]
    friend = world.entities[p.friend]

    openings = (
        f"Moon-moon, bright balloon, {p.name} skipped beneath the moon.",
        f"Tap-tap toes and a silver tune led {p.name} through {p.setting}.",
        f"With a hum and a hop, {p.name} reached the garden stop.",
    )
    world.say(openings[p.variant % len(openings)])
    world.say(
        f"{p.name} carried {p.treat} for {p.friend}, because a friendship grows when kindness is shared."
    )
    world.say(f"{p.friend} waved from {p.setting}, and the two friends began a cheerful rhyme.")
    world.para()
    world.say(f"But {scenario.discovery}.")
    world.say(f"{scenario.clue.capitalize()}.")
    world.say(
        f"The quickest idea was to {scenario.tempting_choice}, but a quick choice can hide an important clue."
    )
    world.para()
    world.say(
        f"“What shall we do?” asked {p.name}. “We can tell the truth and try another way,” said {p.friend}."
    )
    world.say(f"Together they {scenario.action}.")
    world.say(f"“{scenario.dialogue},” {p.friend} sang.")
    refrain = {
        "bells": "Ding-ding, tell and think; friendship helps us stop and blink.",
        "claps": "Clap-clap, truth is bright; caring friends can make things right.",
        "whispers": "Whisper low, then choose with care; honest friends are always there.",
        "drums": "Drum-drum, plans can change; kindness makes a wider range.",
    }[p.telling_mode]
    world.say(refrain)
    world.para()
    world.say(f"Then {scenario.transformation}.")
    world.say(f"{p.name} smiled, and {p.friend} smiled too. {scenario.lesson.capitalize()}.")
    world.say(scenario.ending)

    child.meters["care"] = 1.0
    child.memes["joy"] = 1.0
    friend.memes["trust"] = 1.0
    world.fired.update({"noticed_spoil", "spoke_truth", "friend_helped", "transformed", "resolved"})
    world.facts.update(
        discovery=scenario.discovery,
        clue=scenario.clue,
        rejected=scenario.tempting_choice,
        action=scenario.action,
        transformation=scenario.transformation,
        lesson=scenario.lesson,
        ending=scenario.ending,
        friendship_strengthened=True,
        spoiled_item_not_shared=True,
    )
    return world


def generation_prompts(world: World, scenario: Scenario) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly rhyming story about {p.name} and {p.friend} discovering that {p.treat} has spoiled.",
        f"Tell a friendship story in which the clue '{scenario.clue}' leads to an honest choice and a transformation.",
        f"End with this image: {scenario.ending}",
    ]


def story_qa(world: World, scenario: Scenario) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"What spoiled in {p.name}'s story?",
            answer=f"{p.treat} spoiled because {scenario.discovery}. The clue was that {scenario.clue}."
        ),
        QAItem(
            question=f"What did {p.name} and {p.friend} say to each other?",
            answer=f"{p.name} asked, “What shall we do?” {p.friend} answered, “We can tell the truth and try another way.”"
        ),
        QAItem(
            question="What choice did the friends make?",
            answer=f"They {scenario.action}. They did not {scenario.tempting_choice}."
        ),
        QAItem(
            question="How did the spoiled thing become part of a better ending?",
            answer=f"{scenario.transformation.capitalize()}. This changed the disappointment into a useful or joyful result."
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that {scenario.lesson}."
        ),
        QAItem(
            question="What final image proves the story changed?",
            answer=scenario.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when food has spoiled?",
            answer="Spoiled food has changed in a way that can make it unsafe or unpleasant to eat, such as developing mold, a sour smell, or a strange texture."
        ),
        QAItem(
            question="What should someone do with food that may have spoiled?",
            answer="They should not taste it or serve it. They should tell a trusted adult and follow local food-safety guidance for discarding or composting it."
        ),
        QAItem(
            question="How can friendship help when a plan goes wrong?",
            answer="Friends can speak honestly, listen without blaming, and work together to find a safe and kind new plan."
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation is a meaningful change, such as turning a mistake or disappointment into learning, art, compost, or a stronger friendship."
        ),
    ]


ASP_RULES = """spoiled(X) :- spoil_clue(X).
truthful(X) :- spoiled(X), spoke_truth(X).
helped(X,Y) :- truthful(X), friend(Y), friend_helped(X,Y).
transformed(X) :- truthful(X), composted(X).
safe_resolution(X) :- transformed(X), spoiled_item_not_shared(X).
"""


def asp_facts(params: Optional[StoryParams] = None, scenario: Optional[Scenario] = None) -> str:
    import asp
    p = params or StoryParams()
    atom = p.name.lower()
    friend = p.friend.lower()
    lines = [
        asp.fact("friend", friend),
        asp.fact("spoil_clue", atom),
        asp.fact("spoke_truth", atom),
        asp.fact("friend_helped", atom, friend),
        asp.fact("composted", atom),
        asp.fact("spoiled_item_not_shared", atom),
    ]
    return "\n".join(lines)


def asp_program(show: str, params: Optional[StoryParams] = None, scenario: Optional[Scenario] = None) -> str:
    return f"{asp_facts(params, scenario)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    params = StoryParams()
    model = asp.one_model(asp_program("#show safe_resolution/1.", params, SCENARIOS[0]))
    found = set(asp.atoms(model, "safe_resolution"))
    if not found:
        print("ASP verification failed.")
        return 1
    for scenario in SCENARIOS:
        sample = generate(StoryParams(scenario=scenario.key, variant=17))
        if "spoiled" not in sample.story.lower() or scenario.lesson not in sample.story:
            print(f"Story verification failed for {scenario.key}.")
            return 1
    print("OK: ASP twin and generated stories confirm honest transformation after spoil.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.friend == params.name:
        raise StoryError("friend must be different from the main character")
    if params.treat not in OBJECTS:
        raise StoryError(f"unknown treat: {params.treat}")
    scenario = SCENARIOS[params.variant % len(SCENARIOS)]
    world = simulate(build_world(params), scenario)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world, scenario),
        story_qa=story_qa(world, scenario),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}")
        print(f"events: {sorted(sample.world.fired)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_resolution/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_resolution/1."))
        print("\n".join(str(atom) for atom in model))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(
                StoryParams(
                    seed=base_seed,
                    name="Luna",
                    friend="Tavi",
                    setting="the moonlit garden",
                    treat=OBJECTS[index],
                    variant=index,
                    telling_mode=MODES[index % len(MODES)],
                )
            )
            for index in range(len(SCENARIOS))
        ]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + index)))
            for index in range(max(1, args.n))
        ]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
