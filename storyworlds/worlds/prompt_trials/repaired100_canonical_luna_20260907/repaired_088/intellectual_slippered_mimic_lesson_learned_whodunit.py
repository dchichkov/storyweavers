#!/usr/bin/env python3
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

from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    detective_name: str
    helper_name: str
    suspect_name: str
    case_id: str
    seed: Optional[int] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    slippered_clue: str
    first_guess: str
    false_test: str
    decisive_clue: str
    cause: str
    repair: str
    ending: str
    lesson: str


CASES = [
    Case(
        "vanished_voice",
        "The library bell rang by itself, and a clever voice from behind the curtain answered every question.",
        "A trail of soft slipper prints crossed the dusty sill and ended beside a small brass speaking tube.",
        "Luna first suspected the old parrot because it could mimic almost any sound.",
        "But the parrot was asleep in its cage, and its feathers had not moved.",
        "An intellectual puzzle card beside the tube carried the same blue ink as the caretaker's lesson board.",
        "The caretaker had hidden a talking toy to rehearse a lesson, but a loose spring made it mimic voices at the wrong time.",
        "They tightened the spring, returned the toy to its box, and labeled it before the next lesson.",
        "When the bell rang again, the library answered only with quiet pages and Luna's pleased smile.",
        "A surprising sound should be tested with evidence before anyone is blamed.",
    ),
    Case(
        "moving_portrait",
        "A portrait in the school hall seemed to whisper a new riddle each time someone walked past.",
        "Tiny slippered marks appeared beneath the frame, though the floor around it was clean.",
        "The children guessed that a ghost was moving behind the portrait.",
        "Luna knocked gently, but the wall gave one hollow sound and no ghostly reply.",
        "A mimic speaker was tucked behind the frame, connected to a timer used for an intellectual riddle game.",
        "A timer had been set for the wrong hour after a helper moved the speaker during cleaning.",
        "They reset the timer, secured the speaker, and wrote the correct hour on a bright card.",
        "The portrait stayed silent until the proper game began, then offered one fair riddle.",
        "When a mystery repeats a pattern, check the tool and its timing.",
    ),
    Case(
        "moonlit_message",
        "A note appeared on Luna's desk in her own handwriting, warning that the class prize had vanished.",
        "The note was smudged by a slippered heel and smelled faintly of lavender soap.",
        "Luna wondered whether her mimic friend had copied her writing as a prank.",
        "The friend showed both hands and explained that the copy machine had been unplugged all afternoon.",
        "The note's strange letter spacing matched the intellectual practice sheets stored beside the laundry room.",
        "A breeze had pushed a practice sheet through the open door, where a damp stamp copied its message onto Luna's blank paper.",
        "They dried the stamp, closed the door, and placed the practice sheets in a folder.",
        "The prize was found exactly where it belonged, while the false warning rested in the folder as a useful clue.",
        "A familiar appearance does not prove who made something.",
    ),
    Case(
        "silent_clock",
        "The classroom clock stopped at noon, then began mimicking the teacher's cough.",
        "A line of slipper prints led from the clock to a shelf of old music boxes.",
        "The class suspected the clock had become haunted.",
        "Luna checked the clock's hands and found them still, even when the cough sounded.",
        "One music box contained an intellectual recording card and a loose reed that made the copied cough.",
        "The music box had been placed too close to the clock, and its reed was triggered by vibration.",
        "They moved the music box, repaired the reed, and gave the clock a fresh battery.",
        "At the next noon, the clock chimed clearly while the music box waited for its turn.",
        "Two events can happen together without one causing the other.",
    ),
]

CASE_BY_ID = {case.id: case for case in CASES}
NAMES = ["Luna", "Milo", "Nia", "Theo", "Ada", "Sam"]
HELPERS = ["Mara", "Jon", "Pip", "Aunt Sol", "Ravi"]
SUSPECTS = ["the parrot", "the shadow", "the caretaker", "the wind", "the toy maker"]
MODES = ["clue_first", "dialogue_first", "quiet_open", "question_open"]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0x51F00D)
    text = "|".join((params.detective_name, params.helper_name, params.suspect_name, params.case_id))
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:]


def build_world(params: StoryParams) -> World:
    if params.detective_name == params.helper_name:
        raise StoryError("detective and helper must be different characters")
    if params.case_id not in CASE_BY_ID:
        raise StoryError(f"unknown case_id: {params.case_id}")

    rng = _rng(params)
    case = CASE_BY_ID[params.case_id]
    mode = params.telling_mode if params.telling_mode in MODES else rng.choice(MODES)
    world = World()

    luna = world.add(Entity("luna", "character", "child", params.detective_name))
    helper = world.add(Entity("helper", "character", "helper", params.helper_name))
    suspect = world.add(Entity("suspect", "character", "suspect", params.suspect_name))
    mimic = world.add(Entity("mimic", "thing", "mimic", "mimic device"))
    slipper = world.add(Entity("slipper", "thing", "footwear", "slipper"))
    clue = world.add(Entity("clue", "thing", "clue", "intellectual clue"))

    luna.memes.update(curiosity=1.0, caution=0.0, confidence=0.0)
    helper.memes.update(trust=1.0, patience=1.0)
    mimic.meters.update(volume=1.0, fault=1.0)
    slipper.meters["prints"] = 1.0
    clue.meters["reliability"] = 0.0

    openings = {
        "clue_first": f"The first clue in the quiet study was clear: {case.opening}",
        "dialogue_first": f'"Did you hear that?" {params.detective_name} asked when {case.opening[0].lower() + case.opening[1:]}',
        "quiet_open": f"The room was quiet before the mystery began. Then {case.opening}",
        "question_open": f"Who had changed the calm room? Luna wondered when {case.opening}",
    }
    world.say(openings[mode])
    world.say(f"{_capitalize(case.slippered_clue)} Luna noticed that the trail belonged to a slippered visitor, not an invisible one.")
    world.para()

    luna.memes["caution"] = 1.0
    helper.memes["trust"] = 2.0
    world.say(f'"Let us investigate together," said {params.helper_name}. "A good whodunit needs a careful question and a careful answer."')
    world.say(f'"Then we will not blame {params.suspect_name} yet," said {params.detective_name}.')
    world.say(case.first_guess)
    world.say(case.false_test)
    world.para()

    clue.meters["reliability"] = 1.0
    luna.memes["confidence"] = 2.0
    world.say(f"They followed the slippered prints and examined the intellectual clue instead of trusting the loudest theory. {case.decisive_clue}")
    world.say(f"That evidence changed what Luna knew: {_capitalize(case.cause)}.")
    world.say(f"The mimic was a tool with a fault, not a mysterious creature, and the suspected character was cleared.")
    world.para()

    mimic.meters["fault"] = 0.0
    mimic.meters["volume"] = 0.0
    luna.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    world.say(f"{case.repair}.")
    world.say(f'"The lesson is worth keeping," said {params.helper_name}.')
    world.say(f'"Yes," Luna replied. "{case.lesson}"')
    world.say(f"{case.ending}")
    world.say(f"Everyone left with a lesson learned: {case.lesson}")

    world.facts.update(
        case=case,
        mode=mode,
        detective=luna,
        helper=helper,
        suspect=suspect,
        mimic=mimic,
        slipper=slipper,
        clue=clue,
        cause=case.cause,
        lesson=case.lesson,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    return [
        f"Write a child-friendly whodunit about {f['detective'].label} investigating this mystery: {case.opening}",
        f"Include a slippered clue, a mimic, an intellectual clue, and a brief exchange between {f['detective'].label} and {f['helper'].label}.",
        f"End with the true cause being repaired and a concrete lesson learned: {case.lesson}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    d = f["detective"].label
    h = f["helper"].label
    s = f["suspect"].label
    return [
        QAItem(
            f"What mystery did {d} investigate?",
            f"{d} investigated this mystery: {case.opening} The strange event began the whodunit.",
        ),
        QAItem(
            "What did the slippered clue show?",
            f"The slippered prints showed that someone had crossed the room, so the trail could be followed rather than treated as a ghostly sign.",
        ),
        QAItem(
            f"Why did {d} and {h} work together?",
            f"They worked together so they could test the evidence carefully instead of blaming {s} too quickly.",
        ),
        QAItem(
            "What was the real cause of the trouble?",
            f"The real cause was that {case.cause} The mimic was faulty or misplaced, not magical.",
        ),
        QAItem(
            "What lesson was learned?",
            f"The lesson learned was: {case.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mimic?", "A mimic is something that copies a sound, movement, or appearance."),
        QAItem("What does intellectual mean?", "Intellectual means connected with careful thinking, learning, or solving problems."),
        QAItem("What does slippered mean?", "Slippered means wearing soft shoes called slippers."),
        QAItem("What is a whodunit?", "A whodunit is a mystery story about discovering who caused an event."),
        QAItem("Why should clues be tested?", "Clues should be tested because a first guess can be wrong, while evidence can reveal what really happened."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"  solved={world.facts.get('solved')}")
    lines.append(f"  case={world.facts['case'].id}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "mystery_room"),
            asp.fact("object", "mimic"),
            asp.fact("clue", "slippered_prints"),
            asp.fact("clue", "intellectual_evidence"),
            asp.fact("action", "question"),
            asp.fact("action", "test"),
            asp.fact("action", "repair"),
            asp.fact("value", "lesson_learned"),
        ]
    )


ASP_RULES = r"""
has_clues :- clue(slippered_prints), clue(intellectual_evidence).
investigated :- action(question), action(test), has_clues.
repaired :- action(repair), object(mimic).
lesson_learned :- value(lesson_learned), investigated, repaired.
valid_story :- lesson_learned.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if any(symbol.name == "valid_story" for symbol in model):
        sample = generate(StoryParams("Luna", "Mara", "the parrot", CASES[0].id, seed=7))
        if not sample.story or "lesson learned" not in sample.story.lower():
            print("MISMATCH: generated story did not exercise the lesson resolution.")
            return 1
        print("OK: ASP twin and generated story agree.")
        return 0
    print("MISMATCH: ASP twin did not confirm validity.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A small intellectual slippered mimic whodunit storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--suspect")
    parser.add_argument("--case", dest="case_id")
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
    return StoryParams(
        detective_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        suspect_name=args.suspect or rng.choice(SUSPECTS),
        case_id=args.case_id or rng.choice(CASES).id,
        seed=None,
        telling_mode=rng.choice(MODES),
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Mara", "the parrot", "vanished_voice", seed=11, telling_mode="clue_first"),
    StoryParams("Theo", "Pip", "the shadow", "moving_portrait", seed=12, telling_mode="dialogue_first"),
    StoryParams("Nia", "Aunt Sol", "the toy maker", "moonlit_message", seed=13, telling_mode="quiet_open"),
    StoryParams("Ada", "Ravi", "the wind", "silent_clock", seed=14, telling_mode="question_open"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
