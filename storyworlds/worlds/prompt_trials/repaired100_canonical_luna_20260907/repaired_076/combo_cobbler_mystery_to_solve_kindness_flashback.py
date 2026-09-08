#!/usr/bin/env python3
"""A rhyming cobbler mystery about kindness and remembering an old lesson."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Toby"
    setting: str = "a little cobbler shop"
    combo: str = "berry-and-apple"
    mystery: str = "missing bell"
    telling_mode: str = "rhyme"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


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
class Mystery:
    key: str
    title: str
    opening: str
    clue: str
    tempting: str
    action: str
    dialogue: str
    discovery: str
    kindness: str
    ending: str


MYSTERIES = (
    Mystery(
        "missing_bell",
        "The Bell Beneath the Bench",
        "the cobbler's silver bell vanished before the morning shoe parade",
        "a trail of floury footprints led from the counter to the old memory bench",
        "blame the sleepy shop cat and search without asking",
        "followed the footprints gently, asked who had visited the bench, and checked each safe corner",
        "A mystery needs kind eyes and ears; we ask before we guess",
        "Luna found the bell inside a basket of donated shoes, where a small child had placed it while making room",
        "Luna thanked the child and helped sort the shoes instead of scolding",
        "The silver bell rang above the door, and every donated shoe found a welcoming shelf.",
    ),
    Mystery(
        "vanished_lace",
        "The Blue Lace Riddle",
        "one bright blue lace disappeared from a pair waiting for repair",
        "a tiny blue thread curled beside the kindness jar",
        "say that a customer must have taken it",
        "looked beneath the worktable, asked the visitors calmly, and followed the thread",
        "Kind words can untangle a knot; let us seek the truth together",
        "the lace had been tied around the handle of a basket so a nervous visitor could find it again",
        "Luna praised the thoughtful idea and supplied a fresh lace for the shoe",
        "The blue lace shone like a river while its owner walked home smiling.",
    ),
    Mystery(
        "crooked_stamp",
        "The Crooked Stamp Clue",
        "the cobbler's new kindness stamp printed a crooked heart",
        "red ink dotted the path toward the rinse basin",
        "throw away the stamp and grumble that it was ruined",
        "cleaned the stamp, tested the handle, and invited the youngest helper to explain what happened",
        "A crooked heart still may show a caring start; ask gently before we part",
        "the child had pressed too hard while making thank-you cards for customers",
        "Luna showed a lighter touch and let the child make the next card",
        "The final card held a neat red heart, and the shop filled with grateful smiles.",
    ),
    Mystery(
        "quiet_hammer",
        "The Hammer That Hid",
        "the little repair hammer was missing when a loose sole needed mending",
        "a soft tapping sound came from the cupboard of old shoes",
        "snatch every box open and make the cupboard messier",
        "opened one box at a time and remembered who had last used the hammer",
        "Slow paws and patient thought make a better path than a hurried search",
        "the hammer was inside a boot being prepared for a child who needed warm shoes",
        "Luna helped finish the boot first and then returned the hammer to its hook",
        "The warm boot waited by the door, and the hammer gleamed in its proper place.",
    ),
)

MYSTERY_BY_KEY = {item.key: item for item in MYSTERIES}
NAMES = ("Luna", "Mira", "Pip", "Nell")
HELPERS = ("Toby", "Mara", "Ben", "Suki")
SETTINGS = ("a little cobbler shop", "the moonlit shoe stall", "a sunny repair nook")
COMBOS = ("berry-and-apple", "peach-and-plum", "pear-and-cherry")
MODES = ("rhyme", "chorus", "couplet", "bell")


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity("child", "character", params.name, {"curiosity": 0.8, "patience": 0.6}, {"kindness": 0.8, "confidence": 0.7}))
    helper = world.add(Entity("helper", "character", params.helper, {"care": 1.0}, {"trust": 0.9}))
    world.add(Entity("cobbler", "role", "cobbler", {"craft": 1.0}, {"welcome": 0.9}))
    world.add(Entity("combo", "food", f"{params.combo} cobbler combo", {"sweetness": 0.8}, {"comfort": 0.8}))
    world.facts.update(child=child.label, helper=helper.label, trade="cobbler", combo=params.combo)
    return world


def simulate(world: World) -> World:
    p = world.params
    mystery = MYSTERY_BY_KEY[p.mystery]
    child = world.entities["child"]
    helper = world.entities["helper"]

    world.say(f"Tap-tap, clap-clap, in a cobbler's rhyme, {child.label} visited {p.setting} at opening time.")
    world.say(f"The cobbler polished shoes while {child.label} shared a {p.combo} cobbler combo with {helper.label}.")
    world.say("Then an old memory fluttered back: once, a rushed guess had hurt a friend's feelings, while a gentle question had helped set things right.")
    world.para()
    world.say(f"That morning, {mystery.opening}. {mystery.clue}.")
    world.say(f"The quickest thought was to {mystery.tempting}, but the old memory whispered, \"Be kind before you decide.\"")
    world.say(f"{child.label} said, \"{mystery.dialogue}.\" {helper.label} answered, \"Then we will look carefully, together.\"")
    world.para()
    world.say(f"They {mystery.action}. The clue led them onward, and {mystery.discovery}.")
    world.say(f"Because {child.label} remembered the earlier lesson, {mystery.kindness}.")
    world.say(f"The mystery was solved without a harsh word, and the cobbler's shop felt brighter than before.")
    world.para()
    world.say(f"{mystery.ending}")
    world.say(f"{child.label} learned that kindness is not only a way to finish a mystery; it is a way to care for the people inside it.")

    world.fired.update({"noticed_clue", "remembered_flashback", "asked_gently", "solved_mystery", "showed_kindness"})
    child.meters["patience"] = 1.0
    child.memes.update(kindness=1.2, confidence=1.0)
    world.facts.update(
        mystery=mystery.key,
        clue=mystery.clue,
        rejected=mystery.tempting,
        action=mystery.action,
        discovery=mystery.discovery,
        kindness=mystery.kindness,
        ending=mystery.ending,
        flashback_used=True,
        mystery_solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    mystery = MYSTERY_BY_KEY[p.mystery]
    return [
        f"Write a rhyming story about {p.name} solving a mystery in {p.setting} with a cobbler and a {p.combo} combo.",
        f"Include a flashback showing how kindness helps {p.name} avoid a quick accusation. Use this clue: {mystery.clue}",
        f"End with a child-friendly image proving the mystery was solved: {mystery.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    mystery = MYSTERY_BY_KEY[p.mystery]
    return [
        QAItem(
            f"What mystery did {p.name} need to solve?",
            f"{p.name} needed to solve the mystery of {mystery.opening}.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"The clue was that {mystery.clue}. It pointed the search toward the truth.",
        ),
        QAItem(
            "What did the flashback teach Luna?",
            "The flashback taught Luna that a kind question can help more than a rushed accusation.",
        ),
        QAItem(
            f"How did {p.name} respond?",
            f"{p.name} {mystery.action}. This careful choice let the characters learn what had really happened.",
        ),
        QAItem(
            "How did kindness change the ending?",
            f"{mystery.kindness} The mystery was solved while everyone was treated with respect.",
        ),
        QAItem(
            "What final image proves the problem was resolved?",
            mystery.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does a cobbler do?",
            "A cobbler repairs, cleans, and makes shoes so people can wear them comfortably.",
        ),
        QAItem(
            "Why is it useful to ask questions during a mystery?",
            "A calm question can reveal information without blaming someone who may not have caused the problem.",
        ),
        QAItem(
            "What is kindness?",
            "Kindness means treating others with care, respect, patience, and helpful actions.",
        ),
        QAItem(
            "What is a flashback in a story?",
            "A flashback is a part of a story that shows something that happened earlier and helps explain a present choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """character(X) :- child(X).
remembered(X) :- character(X), flashback(X).
careful(X) :- remembered(X), asked_gently(X), noticed_clue(X).
solved(X) :- careful(X), mystery_present(X).
kind_result(X) :- solved(X), kindness_shown(X).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp
    name = (params or StoryParams()).name.lower()
    facts = (
        ("child", name),
        ("flashback", name),
        ("noticed_clue", name),
        ("asked_gently", name),
        ("mystery_present", name),
        ("kindness_shown", name),
    )
    return "\n".join(asp.fact(predicate, value) for predicate, value in facts)


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program("#show kind_result/1."))
    found = set(asp.atoms(symbols, "kind_result"))
    if found:
        print("OK: ASP twin confirms a kind, clue-based mystery solution.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rhyming cobbler mystery StoryWorld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--combo", choices=COMBOS)
    parser.add_argument("--mystery", choices=tuple(MYSTERY_BY_KEY))
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
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        setting=args.setting or rng.choice(SETTINGS),
        combo=args.combo or rng.choice(COMBOS),
        mystery=args.mystery or rng.choice(tuple(MYSTERY_BY_KEY)),
        telling_mode=rng.choice(MODES),
        variant=rng.randrange(1, 2**31),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERY_BY_KEY:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}\nfired: {sorted(sample.world.fired)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show kind_result/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for index, mystery in enumerate(MYSTERIES):
            params = StoryParams(
                seed=base_seed,
                name=NAMES[index % len(NAMES)],
                helper=HELPERS[index % len(HELPERS)],
                setting=SETTINGS[index % len(SETTINGS)],
                combo=COMBOS[index % len(COMBOS)],
                mystery=mystery.key,
                telling_mode=MODES[index % len(MODES)],
                variant=index + 101,
            )
            samples.append(generate(params))
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + index)))
            for index in range(args.n)
        ]

    if args.asp:
        import asp
        symbols = asp.one_model(asp_program("#show kind_result/1.", samples[0].params))
        if not asp.atoms(symbols, "kind_result"):
            raise StoryError("ASP reasoning rejected the generated story.")

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
