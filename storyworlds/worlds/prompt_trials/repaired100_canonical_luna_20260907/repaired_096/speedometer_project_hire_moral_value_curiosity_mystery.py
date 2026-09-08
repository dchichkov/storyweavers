#!/usr/bin/env python3
"""
A child-facing mystery about a speedometer, a project, and a fair hire.

Luna must discover why a careful project keeps showing impossible speed. The
answer matters because a quick hire could reward a flashy guess instead of the
curiosity and honest work that make a project trustworthy.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    epithet: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "workshop_yard": Setting(
        place="the workshop yard",
        epithet="where wheels, tools, and bright ideas shared the morning sun",
        affords={"speedometer_project"},
    )
}

PROJECTS = {
    "speedometer_project": {
        "label": "the wheel-speed project",
        "purpose": "measure how fast a small cart could travel safely",
        "mystery": "the speedometer flashed a thrilling speed even when the cart barely rolled",
        "risk": "hiring the wrong helper could make the team trust a false measurement",
        "clue": "a thin stripe of blue paint on the speedometer cable",
        "cause": "the cable had been routed too close to a spinning paint wheel, so the wheel made extra pulses",
        "solution": "moved the cable away from the paint wheel, secured it with a cloth loop, and tested it beside a marked path",
        "proof": "the speedometer matched the cart's measured distance on three calm runs",
        "lesson": "curiosity is a moral value when it helps people check what is true before their choices affect others",
    }
}

ROLES = {
    "careful_builder": {
        "label": "careful builder",
        "skill": "checking measurements",
        "strength": "patient curiosity",
    },
    "bold_tinkerer": {
        "label": "bold tinkerer",
        "skill": "inventing quick tools",
        "strength": "creative energy",
    },
    "kind_observer": {
        "label": "kind observer",
        "skill": "noticing who may be overlooked",
        "strength": "thoughtful listening",
    },
}

NAMES = ["Luna", "Milo", "Nia", "Oren", "Tessa", "Jai"]
TRAITS = ["curious", "patient", "brave", "careful", "inventive"]

OPENINGS = [
    "At sunrise, the workshop yard filled with the soft clink of wheels and tools.",
    "The workshop yard was preparing for a project fair when one instrument began telling a strange story.",
    "In the workshop yard, every good project started with a question and ended with a test.",
    "Luna loved the workshop yard because even a loose bolt could become a mystery.",
]

INVESTIGATIONS = [
    "listed what the speedometer showed and what the cart actually did",
    "asked when the strange reading first appeared",
    "marked the cable's path with chalk before moving anything",
    "invited each teammate to describe the result without blaming anyone",
]

RESPONSES = [
    "The supervisor gave every applicant the same small trial and read each person's explanation aloud.",
    "The team paused the hiring decision so the evidence, not the loudest voice, could guide them.",
    "The children made a table of observations and let the quietest helper speak first.",
]

@dataclass
class StoryParams:
    place: str
    project: str
    hire: str
    hero_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, project, hire)
        for place, setting in SETTINGS.items()
        for project in setting.affords
        for hire in ROLES
    ]


def explain_rejection() -> str:
    return "The selected setting, project, and hire role do not form a compatible story."


def build_world(params: StoryParams) -> World:
    if (params.place, params.project, params.hire) not in valid_combos():
        raise StoryError(explain_rejection())

    rng = random.Random(params.seed)
    setting = SETTINGS[params.place]
    project = PROJECTS[params.project]
    role = ROLES[params.hire]

    world = World(setting)
    luna = world.add(Entity(
        "hero",
        "character",
        params.hero_name,
        meters={"care": 0.8, "curiosity": 0.9},
        memes={"moral_value": 0.9},
    ))
    mentor = world.add(Entity(
        "mentor",
        "character",
        "the project mentor",
        meters={"experience": 0.8},
        memes={"fairness": 0.9},
    ))
    instrument = world.add(Entity(
        "speedometer",
        "tool",
        "the speedometer",
        meters={"accuracy": 0.4},
        memes={"trust": 0.3},
    ))
    candidate = world.add(Entity(
        "candidate",
        "character",
        f"the {role['label']}",
        meters={"skill": 0.7},
        memes={"honesty": 0.8},
    ))

    investigation = rng.choice(INVESTIGATIONS)
    response = rng.choice(RESPONSES)
    test_object = rng.choice(["a chalk line", "a row of wooden pegs", "a blue measuring ribbon"])
    dialogue = rng.choice([
        f'"The speedometer says fast, but the wheels say slow," {params.hero_name} said. "Can we test both?"',
        f'"Before we hire anyone, we should find the cause," {params.hero_name} told the mentor.',
        f'"A surprising number is a clue, not a command," {params.hero_name} said.',
        f'"Curiosity should open the door to evidence," {params.hero_name} said. "It should not close it with a guess."',
    ])
    candidate_reply = rng.choice([
        f'"I do not know yet," said the {role["label"]}, "but I can show how I would find out."',
        f'"Let us repeat the run," said the {role["label"]}. "A fair hire needs a fair test."',
        f'"The reading may be wrong," said the {role["label"]}. "I would rather check than pretend."',
    ])

    world.facts.update(
        hero=luna,
        mentor=mentor,
        instrument=instrument,
        candidate=candidate,
        project=project,
        role=role,
        investigation=investigation,
        response=response,
        test_object=test_object,
        dialogue=dialogue,
        candidate_reply=candidate_reply,
        resolved=True,
    )

    world.say(rng.choice(OPENINGS))
    world.say(
        f"{params.hero_name}, a {params.trait} young builder, was leading {project['label']} "
        f"to {project['purpose']}."
    )
    world.say(
        f"Then a mystery appeared: {project['mystery']}. The problem was serious because {project['risk']}."
    )

    world.para()
    world.say(
        f"The workshop needed to hire a helper for the next stage. The {role['label']} looked promising, "
        f"but a quick choice might reward a confident guess instead of careful work."
    )
    world.say(dialogue)
    world.say(f"{params.hero_name} {investigation}.")
    world.say(f"The first useful clue was {project['clue']}.")
    world.say(candidate_reply)

    world.para()
    world.say(
        f"{response} Then {params.hero_name} placed {test_object} beside the cart and watched the "
        "speedometer during a slow, measured run."
    )
    world.say(
        f"The turning point came when the team saw that {project['cause']}."
    )
    world.say(
        f"They {project['solution']}. The test was fair because every helper could see the same marks "
        "and explain the same result."
    )

    world.para()
    world.say(
        f"After the repair, {project['proof']}. The mentor hired the helper who had shown useful skill, "
        "honesty about uncertainty, and willingness to investigate."
    )
    world.say(
        f"{params.hero_name} learned that {project['lesson']}."
    )
    world.say(
        "By afternoon, the speedometer needle moved calmly along the dial while the cart rolled "
        "beside a neat row of chalk marks."
    )
    return world


KNOWLEDGE = {
    "speedometer": (
        "What is a speedometer?",
        "A speedometer is an instrument that shows how fast something is moving.",
    ),
    "project": (
        "What is a project?",
        "A project is a planned piece of work that people complete to make, learn, or solve something.",
    ),
    "hire": (
        "What does hire mean?",
        "To hire someone means to choose and pay that person to do a job.",
    ),
    "curiosity": (
        "What is curiosity?",
        "Curiosity is the wish to learn more by asking questions and looking for answers.",
    ),
    "moral_value": (
        "What is a moral value?",
        "A moral value is a belief about how people should act, such as being honest, fair, or kind.",
    ),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    project = f["project"]
    return [
        f"Write a child-facing mystery about a speedometer in {project['label']}.",
        f"Tell a story about Luna investigating why {project['mystery']}.",
        "Write a mystery in which curiosity and a moral value guide a fair hire for a project.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    project = f["project"]
    return [
        QAItem(
            "What mystery did Luna need to solve?",
            f"Luna needed to discover why {project['mystery']}.",
        ),
        QAItem(
            "Why did Luna delay the hire?",
            f"Luna delayed the hire because {project['risk']}. She wanted evidence instead of a quick guess.",
        ),
        QAItem(
            "What clue turned the investigation toward the truth?",
            f"The clue was {project['clue']}. Luna had first {f['investigation']}.",
        ),
        QAItem(
            "What caused the strange speedometer reading?",
            f"The cause was that {project['cause']}.",
        ),
        QAItem(
            "How did the team test the repaired project?",
            f"They {project['solution']}, and {project['proof']}.",
        ),
        QAItem(
            "What moral value did Luna practice?",
            f"Luna practiced honesty and fairness by using curiosity to check the evidence before making the hire. "
            f"The lesson was that {project['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE.values()]


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


ASP_RULES = r"""
#show valid/3.
valid(P, R, H) :- place(P), project(R), hire(H), affords(P, R), role(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for project in sorted(setting.affords):
            lines.append(asp.fact("affords", place, project))
    for project in PROJECTS:
        lines.append(asp.fact("project", project))
    for hire in ROLES:
        lines.append(asp.fact("role", hire))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print("ASP/Python mismatch.")
        print("Only in Python:", sorted(py - clingo))
        print("Only in ASP:", sorted(clingo - py))
        return 1
    for params in CURATED:
        generate(params)
    print(f"OK: ASP/Python parity holds for {len(py)} combinations; generated stories pass.")
    return 0


def tell(params: StoryParams) -> World:
    return build_world(params)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about a speedometer, project, hire, moral value, and curiosity."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--project", choices=sorted(PROJECTS))
    parser.add_argument("--hire", choices=sorted(ROLES))
    parser.add_argument("--name")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.project:
        combos = [c for c in combos if c[1] == args.project]
    if args.hire:
        combos = [c for c in combos if c[2] == args.hire]
    if not combos:
        raise StoryError("No compatible setting, project, and hire choices remain.")
    place, project, hire = rng.choice(combos)
    return StoryParams(
        place=place,
        project=project,
        hire=hire,
        hero_name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
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
    StoryParams(
        place="workshop_yard",
        project="speedometer_project",
        hire="careful_builder",
        hero_name="Luna",
        trait="curious",
        seed=96096,
    )
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for place, project, hire in asp_valid_combos():
            print(f"{place:16} {project:22} {hire}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n, 1)):
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
