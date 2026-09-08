#!/usr/bin/env python3
"""
A small Folk Tale storyworld set in a playroom.

Luna discovers a mysterious splash on the playroom wall before a surprise
celebration. The mystery is solved through careful clues, honest dialogue,
and a sincere apology.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "cleanliness": 1.0,
            "distance": 0.0,
            "hiddenness": 0.0,
            "completeness": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "curiosity": 0.0,
            "trust": 0.0,
            "courage": 0.0,
            "relief": 0.0,
            "joy": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "the playroom"


@dataclass
class StoryParams:
    luna_name: str
    luna_type: str
    friend_name: str
    friend_type: str
    surprise: str
    mystery: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "surprise": "a moon-shaped puppet show",
        "mystery": "a bright blue splash beneath the toy shelf",
        "clue": "Luna noticed tiny yellow footprints leading from the paint table to the splash.",
        "wrong": "She first blamed the wind-up dragon because its painted feet were blue.",
        "truth": "The dragon had blue feet, but the little yellow footprints belonged to a duck puppet Luna had moved while reaching for a ribbon.",
        "action": "Luna and her friend followed the prints, found the duck puppet beside an open cup of yellow paint, and wiped the floor together.",
        "apology": "Luna apologized to the wind-up dragon for blaming it without checking the clues.",
        "ending": "When the curtains opened, the moon puppet shone above a clean floor, and everyone clapped.",
        "lesson": "a careful look and an honest apology can mend a mistaken accusation",
    },
    {
        "surprise": "a tower of soft animal blocks",
        "mystery": "a purple splash across the playroom rug",
        "clue": "A purple bead rested beside the wet mark, and a trail of beads curved toward the dress-up chest.",
        "wrong": "Luna thought her friend had spilled the paint while hiding the surprise.",
        "truth": "The beads had fallen from Luna's own crown when she had hurried across the rug.",
        "action": "The friends lifted the rug, blotted the splash, and carried the crown back to the craft table.",
        "apology": "Luna apologized to her friend for speaking too quickly and thanked the friend for helping clean.",
        "ending": "The block tower stood tall, with the purple crown placed proudly on its highest step.",
        "lesson": "a quick guess can hurt a friend, but truth and kindness can rebuild trust",
    },
    {
        "surprise": "a tiny tea party for the stuffed animals",
        "mystery": "a red splash beside the pretend kitchen",
        "clue": "A spoon lay in the red puddle, and a line of berry-colored drops led to the cupboard.",
        "wrong": "Luna suspected the sleepy bear had tipped the pretend juice.",
        "truth": "The bear was tucked in bed, while Luna's own berry cup had rolled behind the cupboard.",
        "action": "The friends moved the cupboard carefully, found the cup, and washed the splash from the floor.",
        "apology": "Luna apologized to the bear and promised to ask questions before making a guess.",
        "ending": "The stuffed animals sat around the little table while berry cups gleamed without a single spill.",
        "lesson": "asking before accusing keeps a small mystery from becoming a big hurt",
    },
    {
        "surprise": "a parade of paper stars",
        "mystery": "a silver splash on the playroom window",
        "clue": "A loose star string touched the window, and silver dust sparkled beneath it.",
        "wrong": "Luna said the cat-shaped toy must have made the mess because it was lying nearby.",
        "truth": "The toy had been still; the loose string had brushed a cup of silver water when the curtain moved.",
        "action": "Luna tied the string higher, cleaned the window with a soft cloth, and placed the cup safely on a tray.",
        "apology": "Luna apologized to the cat-shaped toy for giving it the blame.",
        "ending": "The paper stars floated across the clean window like a small sky brought indoors.",
        "lesson": "evidence should guide a story more than a convenient guess",
    },
]


NAMES = ["Luna", "Mira", "Tessa", "Nora", "Pia"]
TYPES = ["rabbit", "fox", "mouse", "bear", "kitten"]
FRIENDS = ["Bram", "Ollie", "Suri", "Milo", "Pip"]
FRIEND_TYPES = ["badger", "squirrel", "duck", "puppy", "goat"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk Tale storyworld: Luna, a splash, and a playroom mystery.")
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--friend")
    parser.add_argument("--friend-type")
    parser.add_argument("--surprise")
    parser.add_argument("--mystery")
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
    scenario_index = rng.randrange(len(SCENARIOS))
    scenario = SCENARIOS[scenario_index]
    return StoryParams(
        luna_name=args.name or rng.choice(NAMES),
        luna_type=args.type or rng.choice(TYPES),
        friend_name=args.friend or rng.choice(FRIENDS),
        friend_type=args.friend_type or rng.choice(FRIEND_TYPES),
        surprise=args.surprise or scenario["surprise"],
        mystery=args.mystery or scenario["mystery"],
        scenario_index=scenario_index,
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    if not params.luna_name.strip() or not params.friend_name.strip():
        raise StoryError("Luna and friend names must not be empty.")
    if params.luna_name.lower() == params.friend_name.lower():
        raise StoryError("Luna and the friend must have different names.")

    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    setting = Setting()
    world = World(setting)

    luna = world.add(Entity("luna", "animal", params.luna_type, params.luna_name))
    friend = world.add(Entity("friend", "animal", params.friend_type, params.friend_name))
    splash = world.add(Entity("splash", "thing", "paint", params.mystery))
    surprise = world.add(Entity("surprise", "thing", "celebration", params.surprise))
    mystery = world.add(Entity("mystery", "thing", "puzzle", "playroom mystery"))

    world.facts.update(luna=luna, friend=friend, splash=splash, surprise=surprise, mystery=mystery, scenario=scenario)

    luna.memes["curiosity"] = 1.0
    friend.memes["trust"] = 1.0
    splash.meters["cleanliness"] = 0.0
    mystery.meters["hiddenness"] = 1.0
    surprise.meters["completeness"] = 0.0

    openings = [
        f"Long ago, in {setting.place}, {luna.label} the {luna.type} prepared {params.surprise}.",
        f"One bright morning, {luna.label} the {luna.type} tiptoed into {setting.place} to arrange {params.surprise}.",
        f"Before the other toys awoke, {luna.label} the {luna.type} was busy in {setting.place} with {params.surprise}.",
    ]
    world.say(openings[params.detail_variant % len(openings)])
    world.say(f"{friend.label} the {friend.type} was helping, for the surprise was meant to make the whole playroom smile.")
    world.say(f"Then they found {params.mystery}.")
    world.para()

    luna.memes["worry"] = 1.0
    friend.memes["worry"] = 0.5
    world.say(f"The splash made the room quiet. It reached across the floor just where the surprise would soon begin.")
    world.say(f'"Who made this mess?" asked {luna.label}. "We must solve the mystery before anyone arrives," said {friend.label}.')
    world.say(scenario["wrong"])
    world.para()

    world.say(scenario["clue"])
    world.say(f'"Let us not choose a culprit yet," said {friend.label}. "A clue should lead us to the truth."')
    world.say(f'"You are right," said {luna.label}. "I will look carefully with you."')
    world.say(scenario["truth"])
    world.para()

    luna.memes["courage"] = 1.0
    friend.memes["trust"] = 2.0
    world.say(scenario["action"])
    world.say(scenario["apology"])
    world.say(f'"Thank you for saying sorry," said {friend.label}. "Now we can finish {params.surprise} together."')
    world.para()

    splash.meters["cleanliness"] = 1.0
    splash.meters["hiddenness"] = 0.0
    surprise.meters["completeness"] = 1.0
    mystery.meters["hiddenness"] = 0.0
    luna.memes["relief"] = 1.0
    luna.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0

    world.say(scenario["ending"])
    world.say(f"{luna.label} learned that {scenario['lesson']}.")
    world.say("And from that day on, the friends searched for truth before they searched for someone to blame.")
    world.log(f"mystery_solved={params.mystery}")
    world.log("apology_given=true")
    world.log("surprise_completed=true")
    return world


def generation_prompts(world: World) -> list[str]:
    luna: Entity = world.facts["luna"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        f"Tell a child-friendly Folk Tale about {luna.label} solving a splash mystery in a playroom.",
        f"Include a surprise, an apology, and dialogue between {luna.label} and {friend.label}.",
        f"Show how the clue in this mystery leads to a kind repair: {scenario['clue']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    luna: Entity = world.facts["luna"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What surprise were {luna.label} and {friend.label} preparing?",
            answer=f"They were preparing {world.facts['surprise'].label}, a special playroom celebration.",
        ),
        QAItem(
            question="What mystery did they need to solve?",
            answer=f"They needed to discover who or what had caused {world.facts['splash'].label}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=scenario["clue"],
        ),
        QAItem(
            question=f"Why did {luna.label} give an apology?",
            answer=f"{luna.label} apologized because {luna.label} blamed someone before checking all the clues.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The friends cleaned the splash, completed the surprise, and enjoyed it together. {scenario['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an apology?",
            answer="An apology is a sincere statement that someone is sorry for causing hurt or making a mistake, often followed by an effort to repair the harm.",
        ),
        QAItem(
            question="Why should people check clues before blaming someone?",
            answer="Checking clues helps people learn what really happened and prevents an unfair accusation from hurting an innocent friend.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something prepared or revealed unexpectedly to bring wonder, delight, or another strong feeling.",
        ),
        QAItem(
            question="What makes dialogue useful in a story?",
            answer="Dialogue lets characters share information, ask questions, change their minds, and make choices that move the story forward.",
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(luna).
entity(friend).
entity(splash).
entity(surprise).
entity(mystery).

solved :- clue_checked, truth_found, splash_clean.
repaired :- solved, apology_given.
happy_end :- repaired, surprise_ready.
#show solved/0.
#show repaired/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue_checked"),
            asp.fact("truth_found"),
            asp.fact("splash_clean"),
            asp.fact("apology_given"),
            asp.fact("surprise_ready"),
        ]
    )


def asp_program(show: str = "#show solved/0. #show repaired/0. #show happy_end/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in symbols}
    expected = {"solved/0", "repaired/0", "happy_end/0"}
    if found == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(found)} != {sorted(expected)}")
    return 1


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "rabbit", "Bram", "badger", "a moon-shaped puppet show", "a bright blue splash beneath the toy shelf", scenario_index=0),
    StoryParams("Mira", "fox", "Suri", "duck", "a tower of soft animal blocks", "a purple splash across the playroom rug", scenario_index=1),
    StoryParams("Tessa", "mouse", "Ollie", "squirrel", "a tiny tea party for the stuffed animals", "a red splash beside the pretend kitchen", scenario_index=2),
    StoryParams("Nora", "bear", "Pip", "puppy", "a parade of paper stars", "a silver splash on the playroom window", scenario_index=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "splash" not in sample.story.lower() or "apolog" not in sample.story.lower():
                print("MISMATCH: generated story is missing required narrative elements.")
                sys.exit(1)
        print("OK: generated story checks passed.")
        return

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
