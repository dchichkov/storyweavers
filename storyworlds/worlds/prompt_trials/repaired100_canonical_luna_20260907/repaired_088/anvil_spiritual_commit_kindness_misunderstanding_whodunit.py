#!/usr/bin/env python3
"""
A gentle whodunit in a small forge.

An anvil goes missing before a spiritual bell-making ceremony. Luna and her
helper investigate a misunderstanding, discover that the anvil was moved for
an act of kindness, and commit to a clearer way of helping one another.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
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
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    luna_name: str
    helper_name: str
    neighbor_name: str
    seed: Optional[int] = None
    case_id: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    spiritual_reason: str
    first_clue: str
    misunderstanding: str
    decisive_clue: str
    kindness: str
    repair: str
    ending: str
    culprit: str


LUNA_NAMES = ["Luna", "Mira", "Tess", "Nia", "Pia", "Sage"]
HELPER_NAMES = ["Ari", "Noah", "June", "Milo", "Ravi", "Ivy"]
NEIGHBOR_NAMES = ["the baker", "the gardener", "the bell keeper", "the woodworker", "the courier"]

CASES = [
    Case(
        "bell_ribbon",
        "A red ribbon had been tied to every forge handle, but the anvil was gone",
        "the anvil was needed to shape a small bell for the evening gratitude circle",
        "one red thread snagged on the empty anvil stand",
        "Luna thought the bell keeper had borrowed the anvil without asking",
        "the thread led beneath the covered cart, where a note said, 'For the quiet workshop'",
        "the neighbor had moved the heavy anvil so an older craftsperson could work safely indoors",
        "They returned the anvil together and placed a bright sign on the borrowing shelf",
        "At sunset, the new bell rang beside the shining anvil, and everyone knew where help had begun",
        "a well-meant move that was not explained",
    ),
    Case(
        "clay_feathers",
        "small clay feathers covered the forge floor, and the anvil was missing",
        "the group planned a spiritual welcome charm for a child who felt lonely",
        "three feathers pointed toward the storage room",
        "Luna suspected that someone had hidden the anvil to spoil the welcome",
        "fresh wheel marks crossed the dust toward a side room marked QUIET",
        "the gardener had moved it to make a safe path for a wheelchair",
        "They cleared the path, rolled the anvil back with help, and added a shared moving rule",
        "The welcome charm chimed softly while the clear path let every guest enter",
        "a safety kindness hidden by a misunderstanding",
    ),
    Case(
        "candle_count",
        "twelve unlit candles stood in a circle around an empty anvil stand",
        "the candles were for a spiritual promise to speak gently during hard work",
        "candle twelve had a smear of blue polishing paste",
        "Luna thought the newest apprentice had taken the anvil in a hurry",
        "the paste matched a trail ending at a low table where a repaired handle waited",
        "the apprentice had moved the anvil to repair its loose wooden handle before the ceremony",
        "They thanked the apprentice, finished the handle, and wrote down the repair plan",
        "The twelve candles glowed around a steady anvil, and the promise felt ready to keep",
        "a secret repair meant kindly",
    ),
    Case(
        "chalk_moon",
        "a chalk moon was drawn on the forge door, while the anvil had vanished",
        "the moon marked a spiritual night of quiet making and shared wishes",
        "a line of silver chalk dust ran from the stand to the courtyard",
        "Luna wondered whether the courier had carried the anvil away by mistake",
        "the dust stopped beside a blanket where the anvil sheltered a shivering stray cat",
        "the courier had placed the anvil near the blanket to hold it down in the wind",
        "They moved the blanket to a safe corner, returned the anvil, and thanked the courier",
        "Under the real moon, the bell rang for the cat, the helpers, and a kinder courtyard",
        "a temporary shelter made without telling anyone",
    ),
]


TELLING_MODES = ["clue_first", "dialogue_first", "quiet_open", "question_open"]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA88F)
    text = "|".join((params.luna_name, params.helper_name, params.neighbor_name, params.case_id or ""))
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def _choose_case(params: StoryParams, rng: random.Random) -> Case:
    if params.case_id:
        for case in CASES:
            if case.id == params.case_id:
                return case
        raise StoryError(f"Unknown case_id {params.case_id!r}; choose one of {[c.id for c in CASES]}.")
    return rng.choice(CASES)


def build_world(params: StoryParams) -> World:
    if not params.luna_name.strip() or not params.helper_name.strip():
        raise StoryError("Luna and helper names must not be empty.")
    rng = _rng(params)
    case = _choose_case(params, rng)
    mode = params.telling_mode if params.telling_mode in TELLING_MODES else rng.choice(TELLING_MODES)

    world = World()
    luna = world.add(Entity("luna", "character", params.luna_name, memes={"curiosity": 1.0}))
    helper = world.add(Entity("helper", "character", params.helper_name, memes={"care": 1.0}))
    neighbor = world.add(Entity("neighbor", "character", params.neighbor_name))
    anvil = world.add(Entity("anvil", "tool", "the anvil", meters={"stability": 0.0}))
    bell = world.add(Entity("bell", "object", "the unfinished bell", meters={"shape": 0.0}))
    note = world.add(Entity("note", "clue", "the borrowing note"))

    openings = {
        "clue_first": f"The first clue was strange: {case.opening}.",
        "dialogue_first": f'"Something is wrong," said {params.luna_name} when {case.opening.lower()}.',
        "quiet_open": f"The forge was quiet before the ceremony. Then {case.opening.lower()}.',
        "question_open": f"Who had moved the anvil? In the forge, {case.opening.lower()}.",
    }
    world.say(openings[mode])
    world.say(f"The anvil mattered because {case.spiritual_reason}.")
    world.facts.update(
        luna=luna,
        helper=helper,
        neighbor=neighbor,
        anvil=anvil,
        bell=bell,
        note=note,
        case=case,
        mode=mode,
        solved=False,
        kindness_seen=False,
    )

    world.para()
    world.say(f'"Let us ask before we accuse," {params.helper_name} said.')
    world.say(f'"And let us follow the clues together," {params.luna_name} replied.')
    world.say(f"They formed a careful whodunit team. Their first clue was {case.first_clue}.")
    world.say(f"At first, {params.luna_name} believed {case.misunderstanding}.")
    luna.memes["trust"] = 1.0
    helper.memes["trust"] = 1.0

    world.para()
    world.say(f"They checked the dust, the door, and the empty stand instead of guessing. {case.decisive_clue}.")
    world.say(f'"That does not look like stealing," said {params.luna_name}. "It looks like someone was trying to help."')
    world.say(f'"Kindness still needs a clear message," {params.helper_name} answered.')
    world.facts["kindness_seen"] = True

    world.para()
    world.say(f"They learned the truth: {case.kindness}.")
    world.say(f"The misunderstanding softened when {params.neighbor_name} explained what had happened.")
    world.say(f"{case.repair}.")
    world.say(f"They committed to a new rule: anyone who moves the anvil would leave a note and ask for help with its weight.")
    world.say(f"{case.ending}.")
    anvil.meters["stability"] = 1.0
    bell.meters["shape"] = 1.0
    luna.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    world.facts["solved"] = True
    world.facts["culprit"] = case.culprit
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    return [
        f"Write a child-friendly spiritual whodunit in a forge where {case.opening.lower()}.",
        f"Show {world.facts['luna'].label} and {world.facts['helper'].label} investigating a misunderstanding about the anvil without blaming anyone.",
        f"Include kindness, a brief spoken exchange, a clear decisive clue, and a commitment that prevents the problem from happening again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    luna: Entity = world.facts["luna"]
    helper: Entity = world.facts["helper"]
    neighbor: Entity = world.facts["neighbor"]
    return [
        QAItem(
            question="What had happened to the anvil?",
            answer=f"The anvil had been moved because {case.kindness}. It was not stolen; it was part of a kindness that had not been explained.",
        ),
        QAItem(
            question=f"Why did {luna.label} and {helper.label} investigate together?",
            answer=f"They investigated together so they could follow evidence instead of letting a misunderstanding turn into blame. They checked the forge carefully and listened to the explanation.",
        ),
        QAItem(
            question="What clue solved the whodunit?",
            answer=f"The decisive clue was that {case.decisive_clue}. It showed where the anvil had gone and why the move made sense.",
        ),
        QAItem(
            question=f"How did {neighbor.label} show kindness?",
            answer=f"{neighbor.label} showed kindness by helping with a real need: {case.kindness}. The good intention became clearer when the team asked questions.",
        ),
        QAItem(
            question="What did the characters commit to doing next time?",
            answer="They committed to leaving a note and asking for help whenever someone moved the heavy anvil, so kindness would not create another misunderstanding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an anvil?", "An anvil is a heavy metal block used as a sturdy surface for shaping metal."),
        QAItem("What does spiritual mean?", "Spiritual can describe something connected with inner meaning, reflection, gratitude, or a sense of care."),
        QAItem("What does commit mean?", "To commit means to make a firm promise or decision to do something."),
        QAItem("What is a misunderstanding?", "A misunderstanding happens when people understand a situation differently from what was really meant."),
        QAItem("What is kindness?", "Kindness means choosing to help, care for, or treat someone gently."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: {entity.kind} meters={entity.meters} memes={entity.memes}")
    lines.append(f"  solved={world.facts['solved']} kindness_seen={world.facts['kindness_seen']}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "forge"),
            asp.fact("object", "anvil"),
            asp.fact("feature", "kindness"),
            asp.fact("feature", "misunderstanding"),
            asp.fact("action", "investigate"),
            asp.fact("action", "commit"),
            asp.fact("purpose", "spiritual"),
        ]
    )


ASP_RULES = r"""
has_clue :- object(anvil), action(investigate).
kindness_possible :- feature(kindness), feature(misunderstanding).
case_solved :- has_clue, kindness_possible, purpose(spiritual), action(commit).
valid_story :- case_solved.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm validity.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts["solved"]:
            print("MISMATCH: generated story was not solved.")
            return 1
        if "anvil" not in sample.story.lower() or "kindness" not in sample.story.lower():
            print("MISMATCH: generated story lost required world details.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Spiritual anvil whodunit storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--neighbor")
    parser.add_argument("--case")
    parser.add_argument("--mode", choices=TELLING_MODES)
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
    return StoryParams(
        luna_name=args.name or rng.choice(LUNA_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        neighbor_name=args.neighbor or rng.choice(NEIGHBOR_NAMES),
        case_id=args.case or rng.choice(CASES).id,
        telling_mode=args.mode or rng.choice(TELLING_MODES),
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Ari", "the bell keeper", seed=101, case_id="bell_ribbon", telling_mode="dialogue_first"),
    StoryParams("Mira", "June", "the gardener", seed=202, case_id="clay_feathers", telling_mode="clue_first"),
    StoryParams("Tess", "Noah", "the apprentice", seed=303, case_id="candle_count", telling_mode="quiet_open"),
    StoryParams("Nia", "Ivy", "the courier", seed=404, case_id="chalk_moon", telling_mode="question_open"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
