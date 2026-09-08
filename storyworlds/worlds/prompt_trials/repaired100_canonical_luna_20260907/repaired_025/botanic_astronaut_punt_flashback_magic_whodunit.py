#!/usr/bin/env python3
"""
A tiny botanic whodunit in which an astronaut must punt a moon-seed through a
magical greenhouse, using a flashback to discover who moved the missing bloom.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""


@dataclass
class Setting:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
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


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    missing: str
    clue: str
    flashback: str
    reveal: str
    ending: str


@dataclass
class StoryParams:
    name: str
    astronaut: str
    botanic_place: str
    punt_object: str
    case: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mara", "Orin", "Tavi", "Sol"]
ASTRONAUTS = ["astronaut", "space botanist", "moon gardener"]
PLACES = ["the glass moon conservatory", "the orbital botanic dome", "the quiet greenhouse"]
PUNT_OBJECTS = ["a silver watering can", "a round seed pod", "a blue garden float"]

CASES = {
    "starlily": Case(
        "starlily",
        "At midnight, the glass moon conservatory shimmered with tiny green stars.",
        "the rare starlily had vanished from its warm shelf",
        "a crescent of damp soil led from the shelf to the little canal",
        "Luna remembered seeing a shadow punt a silver watering can across that canal before the lights blinked",
        "the shadow belonged to Pip, a helpful maintenance rover, which had moved the flower away from a leaking pipe",
        "When the starlily was returned, its petals opened and painted a moon on the dome.",
    ),
    "moonfern": Case(
        "moonfern",
        "The orbital botanic dome floated above Earth like a bright seed.",
        "the first moonfern had disappeared from its numbered tray",
        "three floating spores rested beside the old practice canal",
        "Luna remembered hearing a gentle splash just before the fern went missing",
        "the caretaker's drone had punted the fern to safety when a magic root cracked the tray",
        "The fern unfurled toward Earth, and every leaf held a tiny blue reflection.",
    ),
    "comet_orchid": Case(
        "comet_orchid",
        "In the quiet greenhouse, comet orchids glowed whenever someone told the truth.",
        "the smallest orchid was gone from its velvet stand",
        "a trail of golden pollen crossed the canal toward the tool locker",
        "Luna remembered that her own punt had sent a garden float spinning beside the orchid",
        "the flower had followed the float's magic reflection into the locker, where a cold draft protected it",
        "The orchid returned to the stand and glowed warmly over the solved case.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Botanic astronaut punt flashback magic whodunit.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--astronaut", choices=ASTRONAUTS)
    parser.add_argument("--botanic-place", choices=PLACES)
    parser.add_argument("--punt-object", choices=PUNT_OBJECTS)
    parser.add_argument("--case", choices=sorted(CASES))
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
        name=args.name or rng.choice(NAMES),
        astronaut=args.astronaut or rng.choice(ASTRONAUTS),
        botanic_place=args.botanic_place or rng.choice(PLACES),
        punt_object=args.punt_object or rng.choice(PUNT_OBJECTS),
        case=args.case or rng.choice(sorted(CASES)),
    )


def tell(params: StoryParams) -> World:
    case = CASES[params.case]
    setting = Setting("greenhouse", params.botanic_place, {"botanic", "magic", "canal", "punt"})
    world = World(setting)
    hero = world.add(Entity(
        params.name,
        "character",
        "astronaut",
        params.name,
        meters={"observation": 0.0, "punt_skill": 0.0},
        memes={"curiosity": 1.0, "doubt": 0.0, "confidence": 0.0},
        location="greenhouse",
    ))
    plant = world.add(Entity(
        "missing_plant",
        "thing",
        "botanic_plant",
        "the missing plant",
        meters={"magic": 1.0, "safe": 0.0},
        memes={"hope": 1.0},
        location="unknown",
    ))
    canal = world.add(Entity(
        "canal",
        "thing",
        "canal",
        "the practice canal",
        meters={"water": 1.0},
        location="greenhouse",
    ))
    world.add(Entity(
        "punt_object",
        "thing",
        "garden_tool",
        params.punt_object,
        meters={"floating": 1.0},
        location="canal",
    ))
    world.facts.update(hero=hero, plant=plant, canal=canal, case=case, params=params)

    world.say(f"{case.opening} {params.name}, an {params.astronaut}, was tending the botanic beds.")
    world.say(f"Then {case.missing}. No lock was broken, and the magical leaves still hummed softly.")
    world.para()
    world.say(f'"Who moved it?" asked {params.name}.')
    world.say('"A good whodunit begins with the smallest true clue," whispered the greenhouse bell.')
    world.say(f"{case.clue.capitalize()}.")
    hero.meters["observation"] = 1.0
    hero.memes["doubt"] = 1.0
    world.say(f'"I should not guess yet," said {params.name}. "I will follow the trail."')
    world.para()
    world.say(f"FLASHBACK: {case.flashback}.")
    world.say(f"{params.name} remembered carrying {params.punt_object} to the canal and giving it one careful punt.")
    hero.meters["punt_skill"] = 1.0
    world.say(f'"The punt was mine, but the disappearance was not," said {params.name}.')
    world.say('"Then ask what the magic was protecting," replied the bell.')
    world.para()
    world.say(f"{case.reveal}.")
    hero.memes["confidence"] = 1.0
    plant.location = "safe_shelf"
    plant.meters["safe"] = 1.0
    world.fired.add("case_solved")
    world.say(f"{params.name} returned the plant gently and marked the pipe with a bright ribbon.")
    world.say(case.ending)
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        f"Write a botanic whodunit about {params.name}, an {params.astronaut}, solving a missing-plant mystery.",
        f"Use a flashback to explain how {params.name} used a punt in {params.botanic_place}.",
        f"Include magic, a clue, a fair reveal, and this ending image: {case.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        QAItem(f"What went missing in {params.botanic_place}?", case.missing.capitalize() + "."),
        QAItem("What clue did the astronaut discover?", case.clue.capitalize() + "."),
        QAItem("What did the flashback reveal?", case.flashback + "."),
        QAItem("How was the punt connected to the mystery?", f"{params.name} used {params.punt_object} to make one careful punt across the canal."),
        QAItem("Who or what explained the disappearance?", case.reveal.capitalize() + "."),
        QAItem("How did the story end?", case.ending),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a botanic garden?", "A botanic garden is a place where many kinds of plants are grown and studied."),
        QAItem("What is an astronaut?", "An astronaut is a person trained to travel and work in space."),
        QAItem("What does punt mean here?", "Here, punt means to push or send a floating object across water with a pole or careful shove."),
        QAItem("What is a flashback?", "A flashback is a part of a story that returns to an earlier event."),
        QAItem("What is a whodunit?", "A whodunit is a mystery story about discovering who caused a puzzling event."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:14} type={entity.type:14} location={entity.location:12} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return (
        params.name in NAMES
        and params.astronaut in ASTRONAUTS
        and params.botanic_place in PLACES
        and params.punt_object in PUNT_OBJECTS
        and params.case in CASES
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The chosen astronaut, botanic place, punt object, or case is not in this world.")
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid_story(N,A,P,O,C) :-
    name(N), astronaut(A), place(P), punt_object(O), case_name(C),
    botanic(P), magic_case(C), whodunit(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in NAMES:
        lines.append(asp.fact("name", value))
    for value in ASTRONAUTS:
        lines.append(asp.fact("astronaut", value))
    for value in PLACES:
        lines.append(asp.fact("place", value))
    for value in PUNT_OBJECTS:
        lines.append(asp.fact("punt_object", value))
    for value in CASES:
        lines.append(asp.fact("case_name", value))
    for value in PLACES:
        lines.append(asp.fact("botanic", value))
    for value in CASES:
        lines.append(asp.fact("magic_case", value))
        lines.append(asp.fact("whodunit", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {
        (name, astronaut, place, punt_object, case)
        for name in NAMES
        for astronaut in ASTRONAUTS
        for place in PLACES
        for punt_object in PUNT_OBJECTS
        for case in CASES
    }
    if actual != expected:
        print("MISMATCH between clingo and Python.")
        print("only in clingo:", sorted(actual - expected)[:10])
        print("only in python:", sorted(expected - actual)[:10])
        return 1
    for params in [
        StoryParams("Luna", "astronaut", PLACES[0], PUNT_OBJECTS[0], "starlily", 1),
        StoryParams("Mara", "moon gardener", PLACES[1], PUNT_OBJECTS[1], "moonfern", 2),
    ]:
        sample = generate(params)
        if "FLASHBACK" not in sample.story or "punt" not in sample.story.lower():
            print("Generated-story exercise failed.")
            return 1
    print(f"OK: clingo gate matches Python gate ({len(expected)} combinations).")
    return 0


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        params_list = [
            StoryParams("Luna", "astronaut", PLACES[0], PUNT_OBJECTS[0], case_id, i)
            for i, case_id in enumerate(CASES)
        ]
        return [generate(params) for params in params_list]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    seen = set()
    for i in range(max(args.n * 20, 20)):
        params = resolve_params(args, random.Random(base + i))
        params.seed = base + i
        sample = generate(params)
        if sample.story not in seen:
            samples.append(sample)
            seen.add(sample.story)
        if len(samples) >= args.n:
            break
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combinations.")
        for combo in combos[:20]:
            print(combo)
        return
    samples = build_samples(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
