#!/usr/bin/env python3
"""
A child-facing whodunit about a missing coordinate, careful clues, and the
moral value of sharing knowledge so everyone can find the way.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
sys.path.insert(0, _root)
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
    facts: dict[str, object] = field(default_factory=dict)
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
class Clue:
    id: str
    sign: str
    meaning: str


@dataclass
class Case:
    id: str
    object_name: str
    place: str
    coordinate: str
    culprit: str
    motive: str
    clue: Clue
    reveal: str
    repair: str
    proof: str
    ending: str


SETTINGS = {
    "clocktower_garden": "the clocktower garden",
    "riverside_archive": "the riverside archive",
    "lantern_market": "the lantern market",
}

COORDINATES = {
    "clocktower_garden": ["north gate, third stone", "east path, red bench"],
    "riverside_archive": ["shelf four, blue box", "west room, window two"],
    "lantern_market": ["stall seven, upper hook", "south lane, lantern nine"],
}

CASES = [
    Case(
        id="star_map",
        object_name="the star map",
        place="clocktower_garden",
        coordinate="north gate, third stone",
        culprit="Milo",
        motive="he wanted to hide the map until he could solve its riddle alone",
        clue=Clue("chalk_arc", "a half-moon of blue chalk beside the watering can", "the map had been carried toward the north gate"),
        reveal="Milo had moved the map to the third stone, but a gust had tucked it beneath a loose garden sign",
        repair="made a bright coordinate card and placed a second copy on the notice board",
        proof="even visitors who had never seen the garden could follow the coordinate and find the map",
        ending="the stars came out, and the map rested beneath a clear sign that read NORTH GATE, THIRD STONE",
    ),
    Case(
        id="brass_key",
        object_name="the brass key",
        place="riverside_archive",
        coordinate="shelf four, blue box",
        culprit="Nia",
        motive="she feared someone would use the key before the museum opening",
        clue=Clue("river_silt", "a thin line of river silt below the fourth shelf", "the key had been moved near the window"),
        reveal="Nia had hidden the key in the blue box, but she had copied the coordinate incorrectly",
        repair="wrote the coordinate in words, symbols, and a simple drawn map",
        proof="every helper reached the box without needing a secret hint",
        ending="the archive door clicked open as the blue box sat beneath three easy-to-read signs",
    ),
    Case(
        id="silver_bell",
        object_name="the silver bell",
        place="lantern_market",
        coordinate="stall seven, upper hook",
        culprit="Oren",
        motive="he thought a mystery was more exciting if only clever people could solve it",
        clue=Clue("warm_wax", "a warm drop of wax on the seventh stall's counter", "the bell had been lifted toward the upper hook"),
        reveal="Oren had placed the bell on the upper hook and erased the lower arrow so others would struggle",
        repair="returned the bell to a reachable hook and posted the full coordinate for everyone",
        proof="children, elders, and new visitors all found the bell on their first try",
        ending="the silver bell rang above the market, and its lower arrow pointed plainly toward stall seven",
    ),
]

NAMES = ["Luna", "Tavi", "Mara", "Jun"]
TRAITS = ["curious", "patient", "bold", "thoughtful"]

OPENINGS = [
    "At dusk, the town's little mystery club met beneath a clock that was always five minutes slow.",
    "Rain tapped the windows when the children discovered that an important object had vanished.",
    "The market was ready for its evening game, but one missing object left a puzzling empty place.",
]

REFLECTIONS = [
    "A clue is most useful when everyone is allowed to understand it.",
    "Being clever is not a reason to hide the path from other people.",
    "A fair mystery gives every solver a real chance to follow the evidence.",
]


@dataclass
class StoryParams:
    setting: str
    case: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, case.id) for setting in SETTINGS for case in CASES if case.place == setting]


def resolve_case(case_id: str, setting: str) -> Case:
    matches = [c for c in CASES if c.id == case_id and c.place == setting]
    if not matches:
        raise StoryError(f"Case {case_id!r} is not compatible with setting {setting!r}.")
    return matches[0]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    case = resolve_case(params.case, params.setting)
    world = World()

    hero = world.add(Entity(params.hero_name, "detective", params.hero_name))
    suspect = world.add(Entity(case.culprit.lower(), "suspect", case.culprit))
    helper = world.add(Entity("pip", "helper", "Pip the magpie"))
    object_entity = world.add(Entity("missing_object", "object", case.object_name))

    rng = random.Random(params.seed)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    question = rng.choice([
        "Who moved it, and why was the coordinate missing?",
        "Which clue pointed toward the truth?",
        "Why would someone hide a perfectly good direction?",
    ])

    world.facts.update(
        hero=hero,
        suspect=suspect,
        helper=helper,
        object=object_entity,
        case=case,
        question=question,
        reflection=reflection,
    )

    world.say(opening)
    world.say(
        f"{params.hero_name}, a {params.trait} young detective, found that {case.object_name} "
        f"was missing from {SETTINGS[params.setting]}."
    )
    world.say(f"Beside the empty place lay a torn note with only one word: coordinate.")
    world.say(f"The mystery was clear: {question}")

    world.para()
    world.say(f'"We should question everyone," {params.hero_name} said.')
    world.say(f'"And check what the ground remembers," said Pip, who noticed crumbs, feathers, and footprints.')
    world.say(
        f"{params.hero_name} asked each visitor where they had been, then marked every answer on a small map. "
        "That careful beginning was the first foreshadowing: a missing direction would matter more than a missing object."
    )
    world.say(f"The first clue was {case.clue.sign}. It suggested that {case.clue.meaning}.")
    world.say(
        f"{params.hero_name} followed the clue and discovered that the last complete coordinate had pointed to "
        f"{case.coordinate}."
    )

    world.para()
    world.say(
        f"The evidence led to {case.culprit}, who admitted moving {case.object_name} because {case.motive}."
    )
    world.say(
        f'"I thought the puzzle belonged to me," {case.culprit} whispered. '
        f'"A puzzle is not fair when its path is hidden," {params.hero_name} replied.'
    )
    world.say(
        f"Then came the surprise: {case.reveal}. The object had not been truly stolen. "
        "The confusing coordinate had made an ordinary hiding place seem like a crime."
    )
    world.say(
        f"{params.hero_name} {case.repair}. The moral value was simple: {reflection}"
    )

    world.para()
    world.say(f"They tested the repair together. {case.proof}.")
    world.say(f"By morning, {case.ending}.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly whodunit in which {hero.label} investigates a missing {case.object_name}.",
        f"Include the coordinate {case.coordinate}, a foreshadowed clue, a surprising reveal, and a moral value about fairness.",
        f"Tell a mystery where someone hides {case.object_name}, but clear directions help everyone solve it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        QAItem(
            "What was missing?",
            f"{case.object_name.capitalize()} was missing from {SETTINGS[case.place]}.",
        ),
        QAItem(
            "What coordinate helped solve the mystery?",
            f"The useful coordinate was {case.coordinate}.",
        ),
        QAItem(
            "What clue foreshadowed the answer?",
            f"{case.clue.sign.capitalize()} foreshadowed that {case.clue.meaning}.",
        ),
        QAItem(
            "Who moved the object, and why?",
            f"{case.culprit} moved it because {case.motive}.",
        ),
        QAItem(
            "What was the surprising reveal?",
            f"The surprise was that {case.reveal}.",
        ),
        QAItem(
            "What moral value did the detective learn?",
            f"{hero.label} learned that {world.facts['reflection']}",
        ),
    ]


KNOWLEDGE = [
    QAItem("What is a coordinate?", "A coordinate is a direction or set of details that tells where something can be found."),
    QAItem("What is foreshadowing?", "Foreshadowing is an early hint about something that will matter later."),
    QAItem("What is a surprise in a mystery?", "A surprise is an unexpected fact that changes how the clues are understood."),
    QAItem("What is a moral value?", "A moral value is a belief about how people should treat one another."),
    QAItem("What is a whodunit?", "A whodunit is a mystery story about discovering who did something."),
]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(S, C) :- setting(S), case(C), belongs(C, S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for case in CASES:
        lines.append(asp.fact("case", case.id))
        lines.append(asp.fact("belongs", case.id, case.place))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_values = set(asp_valid_combos())
    if py == clingo_values:
        print(f"OK: ASP/Python parity ({len(py)} combinations).")
        for i, combo in enumerate(sorted(py)[:3]):
            params = StoryParams(combo[0], combo[1], "Luna", "girl", "curious", i)
            sample = generate(params)
            if not sample.story or "coordinate" not in sample.story:
                print("Generated story check failed.")
                return 1
        print("OK: generated story checks passed.")
        return 0
    print("ASP/Python mismatch.")
    print("Python only:", sorted(py - clingo_values))
    print("ASP only:", sorted(clingo_values - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(KNOWLEDGE),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Coordinate whodunit storyworld.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--case", choices=[c.id for c in CASES])
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.case:
        combos = [c for c in combos if c[1] == args.case]
    if not combos:
        raise StoryError("No compatible setting and case combination exists.")
    setting, case = rng.choice(combos)
    return StoryParams(
        setting=setting,
        case=case,
        hero_name=args.name or rng.choice(NAMES),
        hero_type=args.gender or rng.choice(["girl", "boy"]),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for setting, case in combos:
            print(f"  {setting}: {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(c.place, c.id, "Luna", "girl", "curious", base_seed + i)
            for i, c in enumerate(CASES)
        ]
    else:
        params_list = []
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(p) for p in params_list]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
