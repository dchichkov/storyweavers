#!/usr/bin/env python3
"""
A small cautionary whodunit about a dart, a train consist, and a sentence
that helps a careful child solve a mystery without blaming the wrong person.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    place: str
    hero_name: str
    helper_name: str
    case: int = 0
    opening: int = 0
    caution: int = 0
    reveal: int = 0
    ending: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "station": Setting("the little station", {"dart", "consist", "sentence"}),
    "museum": Setting("the railway museum", {"dart", "consist", "sentence"}),
    "platform": Setting("the quiet platform", {"dart", "consist", "sentence"}),
}

HERO_NAMES = ["Luna", "Mara", "Tess", "Nora", "Iris", "June"]
HELPER_NAMES = ["Pip", "Owen", "Bea", "Sam", "Milo", "Rae"]

CASES = [
    {
        "dart": "a blue toy dart",
        "missing": "the dart had vanished from the display board",
        "suspect": "the ticket seller",
        "clues": "a round blue mark on the timetable, a draft beneath the door, and a fresh line in the dust",
        "question": "Who moved the dart, and why did the blue mark point toward the old train?",
        "answer": "The dart had not been stolen at all. A gust had knocked it loose, and it had rolled beneath the consist.",
        "action": "crawl beneath the train",
        "warning": "Do not crawl under a train, even when it is old and still. We can ask an adult and inspect from the safe side.",
        "repair": "The curator used a long wooden hook to retrieve the dart while everyone stayed behind the yellow line.",
        "lesson": "a mystery is never a reason to enter a dangerous place",
        "ending": "The blue dart returned to its board, and the silent consist looked peaceful behind the bright safety line.",
    },
    {
        "dart": "a red foam dart",
        "missing": "the dart was stuck inside the conductor's empty office",
        "suspect": "the young guide",
        "clues": "a red feather, a half-open window, and tiny wheel tracks in the dust",
        "question": "Who put the dart in the office, and what had carried it there?",
        "answer": "A breeze had pushed the dart through the open window, and a display cart had made the wheel tracks.",
        "action": "reach through the broken window",
        "warning": "Stop at the window. Broken edges can hurt, and guessing is not worth a cut.",
        "repair": "The curator closed the window, wore gloves, and used tongs to lift the dart safely.",
        "lesson": "a careful investigator protects people before solving the puzzle",
        "ending": "The red dart rested in its case while the old consist gleamed under the museum lights.",
    },
    {
        "dart": "a yellow practice dart",
        "missing": "the dart had appeared beside a locked luggage trunk",
        "suspect": "the caretaker",
        "clues": "yellow paint on the floor, a loose display ribbon, and no scratch on the trunk",
        "question": "Who opened the trunk, and why was there no mark on its lock?",
        "answer": "Nobody opened it. The dart had bounced off the ribbon and landed beside the trunk.",
        "action": "force the trunk open",
        "warning": "Do not force a lock. We can leave the trunk closed and ask the caretaker about it.",
        "repair": "The caretaker tightened the ribbon and returned the dart to its marked place.",
        "lesson": "an unexplained object does not prove that someone did something wrong",
        "ending": "The yellow dart stood beside its label, and the locked trunk remained safely closed.",
    },
    {
        "dart": "a green wooden dart",
        "missing": "the dart was found near the wheels of the visiting consist",
        "suspect": "a passenger",
        "clues": "a damp footprint, a green thread, and a puddle beneath the baggage door",
        "question": "Who left the dart by the wheels, and what moved it?",
        "answer": "Rainwater had carried the dart along the platform after it slipped from a display basket.",
        "action": "step between the rails to pick it up",
        "warning": "Never step between rails to retrieve a toy. We will stay on the platform and call the conductor.",
        "repair": "The conductor stopped the inspection, fetched a brush, and swept the dart away from the wheels.",
        "lesson": "safe distance matters more than a quick answer",
        "ending": "The green dart dried in a basket while the consist waited beyond the line.",
    },
]

OPENINGS = [
    "Luna visited {place} with {helper} after the last bell had rung.",
    "At {place}, {hero} and {helper} studied an old railway display beneath a cloudy sky.",
    "The lamps blinked on at {place} just as {hero} noticed something strange.",
    "Before going home, {hero} promised {helper} one careful look around {place}.",
]

CAUTIONS = [
    '"Let us gather facts before we name a culprit," said {hero}.',
    '"A clue is not a sentence," {hero} reminded {helper}. "It needs evidence."',
    '"Stay behind the line and tell me exactly what you saw," said {hero}.',
    '"We can be curious without being careless," {hero} said.',
]

REVEALS = [
    "They compared each clue instead of choosing the most exciting story.",
    "The two investigators drew the clues in the dust, keeping every detail in its proper place.",
    "They asked the curator for help and waited where the floor was marked safe.",
    "They listened to the wind, watched the wheels, and left every locked thing untouched.",
]

ENDINGS = [
    "{helper} smiled. \"The true answer is kinder than a quick accusation.\"",
    "\"Now I know what to do,\" said {helper}. \"Look carefully, then choose safely.\"",
    "{hero} nodded. \"Good questions protect people while they uncover the truth.\"",
    "\"The safest clue was the one that told us where not to step,\" said {helper}.",
]


ASP_RULES = r"""
#show valid/2.
setting(station). setting(museum). setting(platform).
affords(station,dart). affords(station,consist). affords(station,sentence).
affords(museum,dart). affords(museum,consist). affords(museum,sentence).
affords(platform,dart). affords(platform,consist). affords(platform,sentence).
valid(P, W) :- setting(P), affords(P, W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for word in sorted(setting.affords):
            lines.append(asp.fact("affords", name, word))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, word) for place, setting in SETTINGS.items() for word in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    setting = SETTINGS[params.place]
    case = CASES[params.case % len(CASES)]
    world = StoryState(setting)

    hero = world.add(Entity(
        params.hero_name, "character", "child", traits=["careful", "curious"],
        meters={"distance_from_track": 4.0}, memes={"caution": 1.0},
    ))
    helper = world.add(Entity(
        params.helper_name, "character", "child", traits=["observant"],
        meters={"distance_from_track": 4.0}, memes={"curiosity": 1.0},
    ))
    curator = world.add(Entity(
        "Curator", "character", "adult", traits=["patient"],
        meters={"distance_from_track": 5.0}, memes={"trust": 1.0},
    ))
    dart = world.add(Entity(
        "dart", "thing", "dart", label=case["dart"], owner="display",
        meters={"distance_from_track": 1.0}, memes={"mystery": 1.0},
    ))
    consist = world.add(Entity(
        "consist", "thing", "train consist", label="the old train consist",
        meters={"distance_from_track": 0.0}, memes={"danger": 1.0},
    ))

    place = setting.name
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        place=place, hero=hero.id, helper=helper.id
    ))
    world.say(f"On a display board, they read a sentence about {dart.label}. Then they discovered that {case['missing']}.")
    world.say(f'"Perhaps {case["suspect"]} took it," whispered {helper.id}. "{case["question"]}"')
    world.para()
    world.say(f"They found {case['clues']}.")
    world.say(CAUTIONS[params.caution % len(CAUTIONS)].format(hero=hero.id, helper=helper.id))
    world.say(f'{helper.id} wanted to {case["action"]}, but {hero.id} gently held up a hand.')
    world.say(REVEALS[params.reveal % len(REVEALS)])
    world.say(f'"I see a safer plan," said {helper.id}. "Let us ask the curator."')
    world.say(f'{curator.id} arrived and examined the clues without disturbing them.')
    world.say(f'"The sentence gives us a question, not a guilty person," said {curator.id}. "{case["answer"]}"')
    world.para()
    world.say(case["repair"])
    world.say(f'{ENDINGS[params.ending % len(ENDINGS)].format(hero=hero.id, helper=helper.id)}')
    world.say(f'Together they learned that {case["lesson"]}.')
    world.say(case["ending"])

    world.facts.update(
        hero=hero, helper=helper, curator=curator, dart=dart,
        consist=consist, case=case, place=place,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a cautionary whodunit at {f['place']} involving {f['dart'].label}.",
        f"Tell a child-friendly mystery in which {f['helper'].id} and {f['hero'].id} solve a missing-dart case without blaming anyone too soon.",
        "Write a story using a dart, a railway consist, a sentence, careful dialogue, and a safe resolution.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    hero = f["hero"].id
    helper = f["helper"].id
    return [
        QAItem(
            f"What disappeared in the mystery?",
            f"The missing object was {case['dart']}. {hero} and {helper} investigated it without disturbing the railway display.",
        ),
        QAItem(
            f"Who did {helper} first suspect?",
            f"{helper} first suspected {case['suspect']}, but the clues did not prove that person was responsible.",
        ),
        QAItem(
            "What clues helped solve the case?",
            f"They noticed {case['clues']}. Those details supported the explanation that {case['answer']}",
        ),
        QAItem(
            f"What dangerous action did {helper} consider?",
            f"{helper} considered trying to {case['action']}, but {hero} stopped the plan and kept everyone away from the train.",
        ),
        QAItem(
            "What lesson did the children learn?",
            f"They learned that {case['lesson']}. The curator retrieved the dart safely instead of letting anyone take a risky shortcut.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a dart?",
            "A dart is a small pointed or toy object made to travel through the air, though a toy dart should still be used carefully.",
        ),
        QAItem(
            "What is a train consist?",
            "A train consist is a group of railway cars joined together and treated as one train.",
        ),
        QAItem(
            "Why should people stay away from railway tracks?",
            "People should stay away from railway tracks because trains and their wheels are heavy, fast, and difficult to stop.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:14}) "
            f"meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([x for x in HELPER_NAMES if x != hero])
    return StoryParams(
        place=place,
        hero_name=hero,
        helper_name=helper,
        case=rng.randrange(len(CASES)),
        opening=rng.randrange(len(OPENINGS)),
        caution=rng.randrange(len(CAUTIONS)),
        reveal=rng.randrange(len(REVEALS)),
        ending=rng.randrange(len(ENDINGS)),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cautionary whodunit world involving a dart and a train consist."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        rng = random.Random(17)
        for _ in range(5):
            sample = generate(resolve_params(args, rng))
            if not sample.story or len(sample.story_qa) < 3:
                raise StoryError("Generated story verification failed.")
        print("OK: generated stories pass basic checks.")
        return
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:\n")
        for place, word in asp_valid():
            print(f"  {place:10} {word}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            samples.append(generate(StoryParams(
                place=place,
                hero_name=f"{place.title()}Luna",
                helper_name=f"{place.title()}Pip",
            )))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
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
