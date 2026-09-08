#!/usr/bin/env python3
"""
A child-facing superhero story world about bacon, a difficult twist, and
reconciliation after a surprising rescue.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "Beacon City"
    hero: str = "Captain Crisp"
    friend: str = "Maya"
    rival: str = "Dr. Sizzle"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "Beacon City": {"tags": {"city", "hero", "food"}, "mood": "bright and busy"},
    "Harbor Heights": {"tags": {"harbor", "hero", "food"}, "mood": "windy and cheerful"},
    "Sunrise Town": {"tags": {"town", "hero", "food"}, "mood": "warm and welcoming"},
}


@dataclass(frozen=True)
class Arc:
    title: str
    premise: str
    problem: str
    twist: str
    choice: str
    action: str
    result: str
    ending: str
    problem_answer: str
    twist_answer: str
    reconciliation_answer: str
    result_answer: str


ARCS = [
    Arc(
        "The Vanishing Breakfast",
        "Every morning, the city gathered for a giant breakfast made with a mountain of bacon.",
        "At sunrise, the bacon vanished from every plate, and hungry families began blaming Dr. Sizzle.",
        "The missing bacon was not stolen at all: it had been pulled through hidden pipes to feed a nest of baby firebirds beneath the square.",
        "Captain Crisp lowered his shield instead of chasing the frightened scientist, while Maya asked Dr. Sizzle to explain.",
        "Together they followed the warm pipes, removed a jammed metal grate, and carried the firebirds to a safe rooftop nest.",
        "Dr. Sizzle returned the bacon he had saved and promised to build a proper firebird kitchen with the city.",
        "a breakfast table where heroes, scientists, and firebirds shared crisp strips beneath a golden sunrise",
        "The city's breakfast bacon kept vanishing, leaving families hungry and suspicious of Dr. Sizzle.",
        "The bacon was being drawn through pipes to feed baby firebirds, so Dr. Sizzle was trying to help rather than steal.",
        "Captain Crisp listened to Dr. Sizzle, and they worked together to remove the blocked grate and care for the firebirds.",
        "The scientist returned the saved bacon and joined the city in making a safe kitchen for the firebirds.",
    ),
    Arc(
        "The Great Bacon Balloon",
        "Captain Crisp used a bacon-powered balloon to carry warm meals over the rooftops.",
        "A sudden gust tore the balloon loose, sending its basket toward the clock tower.",
        "The gust came from Dr. Sizzle's machine, but he had turned it on to remove smoke from a school kitchen.",
        "Instead of scolding him, Maya told the doctor exactly where the balloon was drifting, and Captain Crisp asked for his wind controls.",
        "Dr. Sizzle reversed the machine while Captain Crisp tied a rescue line to the balloon and pulled the basket away from the tower.",
        "The children received their meals, and Dr. Sizzle apologized for rushing without warning anyone.",
        "a bacon balloon bobbing safely above the school while its former rivals waved from the roof",
        "A wind machine pushed the meal balloon toward the clock tower and endangered the school lunch.",
        "The machine had been meant to remove smoke from the school kitchen, not to wreck the balloon.",
        "The heroes and Dr. Sizzle shared information, reversed the wind, and rescued the balloon together.",
        "The children got their warm meals, and Dr. Sizzle learned to warn the city before testing a machine.",
    ),
    Arc(
        "The Crispy Cape",
        "Captain Crisp's cape could turn any crumb of bacon into a bright spark of courage.",
        "A thief grabbed the cape during the town parade, and its sparks began setting banners alight.",
        "The thief was a lonely child who wanted the cape because he believed heroes never noticed children like him.",
        "Captain Crisp asked him to stop running and promised to listen before taking the cape back.",
        "Maya used a hose to remove the little flames while the child held the cape still and named every place he felt unseen.",
        "The child returned the cape, joined the parade crew, and received a safe badge made from a bacon-shaped button.",
        "the once-lonely child marching beside Captain Crisp beneath a cape that glowed softly, never wildly",
        "A stolen cape made sparks that threatened the parade banners.",
        "The thief was a lonely child seeking attention and belonging, not someone planning a grand crime.",
        "Captain Crisp listened without anger, and the child helped remove the flames before returning the cape.",
        "The child became part of the parade crew and learned that asking for help was braver than stealing.",
    ),
    Arc(
        "The Friendly Fridge",
        "A giant talking fridge protected the city's emergency bacon for hungry neighbors.",
        "The fridge locked its doors and would not release even one slice when a storm cut the power.",
        "Its lock had tightened because Dr. Sizzle had secretly removed the fridge's old battery to power his own lab.",
        "Maya told Dr. Sizzle that the neighbors needed food first, and he admitted what he had done.",
        "He helped Captain Crisp remove the battery from the lab's loudest machine and return it to the fridge.",
        "The fridge opened, shared its bacon, and invited Dr. Sizzle to label every emergency switch.",
        "the smiling fridge serving bacon sandwiches while Dr. Sizzle carefully held a bright red instruction card",
        "A storm trapped emergency bacon behind a locked, powerless fridge.",
        "Dr. Sizzle had removed the fridge's battery for his lab, causing the lock to fail.",
        "He admitted the mistake and helped return the battery so the fridge could serve the neighbors.",
        "The fridge fed the city, and Dr. Sizzle became its careful emergency helper.",
    ),
    Arc(
        "The Shadow on the Skillet",
        "A dark shape crept across the city's giant skillet whenever someone shouted during breakfast.",
        "The shadow grew so large that it covered the streets and made everyone afraid to speak.",
        "It was made from frightened feelings trapped in the skillet, not from a monster.",
        "Captain Crisp and Dr. Sizzle stopped arguing and each apologized for words that had made the shadow grow.",
        "They spoke calmly while Maya helped remove the cold bacon stuck beneath the skillet's handle.",
        "The shadow shrank into a harmless wisp, and the skillet cooked breakfast with a gentle sunny glow.",
        "a small smiling wisp curling above the skillet as former enemies passed one warm plate between them",
        "A giant shadow covered the city whenever people shouted near the breakfast skillet.",
        "The shadow was formed from trapped frightened feelings rather than a monster.",
        "Captain Crisp and Dr. Sizzle reconciled, then removed the stuck bacon that kept the skillet cold and tense.",
        "The shadow became harmless, and breakfast returned with a warm glow.",
    ),
]


OPENINGS = [
    "In {setting}, every child knew that a superhero could save a city with courage, kindness, and one sizzling strip of bacon.",
    "The morning sun flashed on the towers of {setting} as {hero} hurried toward the smell of bacon.",
    "People in {setting} had many heroes, but none wore a cape as bright as {hero}'s.",
    "Before the first alarm rang, {hero} and {friend} were sharing bacon on a rooftop above {setting}.",
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.rival))
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def build_story(world: World) -> str:
    facts = world.facts
    arc: Arc = facts["arc"]
    opening = fill(OPENINGS[facts["opening_variant"]], facts)
    parts = [
        f"{opening} This adventure was called \"{arc.title}.\"",
        f"{fill(arc.premise, facts)} {fill(arc.problem, facts)}",
        f"\"We should hear the whole story before we choose a target,\" said {facts['friend']}. {fill(arc.twist, facts)}",
        f"{facts['hero']} lowered a gloved hand. \"Then we solve the real problem together.\" {fill(arc.choice, facts)}",
        fill(arc.action, facts),
        f"{fill(arc.result, facts)} \"A true hero makes room for a second chance,\" said {facts['friend']}.",
        f"By sunset, {fill(arc.ending, facts)}. That was the day {facts['hero']} learned that a twist can open the door to reconciliation.",
    ]
    return "\n\n".join(parts)


ASP_RULES = r"""
setting(beacon_city).
setting(harbor_heights).
setting(sunrise_town).

feature(twist).
feature(reconciliation).
ingredient(bacon).
action(remove).

valid_story(S) :- setting(S), feature(twist), feature(reconciliation),
                  ingredient(bacon), action(remove).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        lines.append(asp.fact("setting", setting.lower().replace(" ", "_")))
    lines.extend(
        [
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("ingredient", "bacon"),
            asp.fact("action", "remove"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero story world about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--rival")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Captain Crisp", "Bacon Bolt", "Sizzle Star"])
    friend = args.friend or rng.choice(["Maya", "Leo", "Zara"])
    rival = args.rival or rng.choice(["Dr. Sizzle", "Professor Smoke", "The Grease Goblin"])
    if len({hero, friend, rival}) != 3:
        raise StoryError("The hero, friend, and rival must all be different characters.")
    return StoryParams(setting=setting, hero=hero, friend=friend, rival=rival)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}.")
    if len({params.hero, params.friend, params.rival}) != 3:
        raise StoryError("The hero, friend, and rival must all be different characters.")

    seed = stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="superhero",
            meters={"speed": 0.8, "strength": 0.8},
            memes={"courage": 1.0, "mercy": 0.8},
        )
    )
    friend = world.add(
        Entity(
            name=params.friend,
            kind="helper",
            meters={"care": 0.9},
            memes={"listening": 1.0, "reconciliation": 1.0},
        )
    )
    rival = world.add(
        Entity(
            name=params.rival,
            kind="inventor",
            meters={"machine_power": 0.7},
            memes={"confusion": 0.6, "hope": 0.5},
        )
    )
    world.add(Entity(name="the bacon", kind="food", meters={"warmth": 0.8, "supply": 1.0}))
    world.add(Entity(name="the city problem", kind="threat", meters={"danger": 0.7}))
    world.add(Entity(name="the rescue tool", kind="gear", meters={"usefulness": 0.9}))

    rival.memes["confusion"] = 0.2
    rival.memes["hope"] = 1.0
    hero.memes["mercy"] = 1.0

    facts = {
        "hero": params.hero,
        "friend": params.friend,
        "rival": params.rival,
        "setting": params.setting,
        "arc": arc,
        "opening_variant": (seed // len(ARCS)) % len(OPENINGS),
        "title": arc.title,
    }
    world.facts.update(facts)

    story = build_story(world)
    prompts = [
        f"Write a superhero story about {params.hero}, bacon, and a surprising twist in {params.setting}.",
        f"Tell a child-friendly adventure where {params.hero} removes a danger and reconciles with {params.rival}.",
        "Write a superhero story showing that listening can turn a conflict into teamwork.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} face?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question=f"How did {params.hero} and {params.rival} reach reconciliation?",
            answer=arc.reconciliation_answer,
        ),
        QAItem(
            question="What changed at the end of the adventure?",
            answer=arc.result_answer,
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities and good choices to help others.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make peace after a disagreement and work toward understanding.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals the situation is different from what people expected.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="To remove something means to take it away from a place or problem.",
        ),
        QAItem(
            question="What is bacon?",
            answer="Bacon is a savory food often cooked until its edges are crisp and warm.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
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


def python_valid_settings() -> list[str]:
    return sorted(setting.lower().replace(" ", "_") for setting in SETTING_REGISTRY)


def asp_valid_settings() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(setting,) for setting in python_valid_settings()}
    actual = set(asp_valid_settings())
    if expected != actual:
        print("MISMATCH between clingo and Python:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1

    rng = random.Random(17)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story.strip():
            print("Generated an empty story.")
            return 1

    print(f"OK: clingo gate matches Python ({len(expected)} settings), and stories generate.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for item in asp_valid_settings():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Captain Crisp",
                        friend="Maya",
                        rival="Dr. Sizzle",
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            current_seed = base_seed + index
            index += 1
            rng = random.Random(current_seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = current_seed
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
