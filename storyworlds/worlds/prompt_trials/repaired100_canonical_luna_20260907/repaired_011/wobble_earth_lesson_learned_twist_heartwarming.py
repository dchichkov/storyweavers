#!/usr/bin/env python3
"""
A small heartwarming storyworld about a wobbling model Earth and a lesson learned.

Luna discovers that a tiny wobble does not mean something is broken. With a
friend's help, she learns to pause, look closely, and make a careful repair.
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
class StoryParams:
    name: str
    helper: str
    teacher: str
    place: str
    earth_material: str
    support: str
    incident: int = 0
    lesson: int = 0
    twist: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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


NAMES = ["Luna", "Maya", "Nell", "Tavi", "Iris", "Jo"]
HELPERS = ["Milo", "Sage", "Pip", "Ari", "Bea", "Theo"]
TEACHERS = ["Ms. Rowan", "Mr. Sol", "Dr. Fern", "Ms. Avery"]
PLACES = [
    "the little planetarium",
    "the school science room",
    "the library's bright study corner",
    "the community garden classroom",
]
MATERIALS = ["painted paper", "blue clay", "a papier-mâché shell", "a soft wooden globe"]
SUPPORTS = ["a cork stand", "a ring of felt", "three smooth pebbles", "a folded cardboard base"]

INCIDENTS = [
    {
        "lead": "{name} placed the {earth_material} Earth on the {support} and gave it a gentle turn.",
        "trigger": "The Earth began to wobble. Its tiny blue oceans tilted toward the table, then tilted back.",
        "risk": "If it tipped, the careful continents might wrinkle and the class display could fall apart.",
        "action": "{helper} noticed a loose edge beneath the stand. Together, they lifted the Earth slowly and checked the bottom.",
        "resolution": "{name} tucked a small felt strip under the loose edge. The Earth became steady without losing its gentle turn.",
        "cause": "a loose edge beneath the stand made the model Earth wobble",
        "deed": "looked beneath the stand with the helper instead of grabbing the wobbling Earth",
        "result": "a small felt strip steadied the model without stopping its turn",
    },
    {
        "lead": "{name} painted one last white cloud on the {earth_material} Earth while {helper} held the {support}.",
        "trigger": "The stand rocked, and the model Earth made a slow wobble toward a tray of blue paint.",
        "risk": "One more shake could send the Earth into the paint and wash its bright continents blue.",
        "action": "{name} said, 'Let's pause.' {helper} moved the paint tray away while {name} held the stand with two calm hands.",
        "resolution": "When the tray was safe, they found one pebble missing from the base and replaced it with a smooth one.",
        "cause": "a missing pebble left the stand uneven beside the paint tray",
        "deed": "paused, moved the paint tray, and helped inspect the uneven base",
        "result": "a smooth pebble balanced the base and kept the painted Earth dry",
    },
    {
        "lead": "{name} spun the {earth_material} Earth so the classroom would see its green forests and silver rivers.",
        "trigger": "A thin thread from the display cloth caught under the stand, making the whole globe wobble.",
        "risk": "The thread pulled tighter each time the Earth turned.",
        "action": "{helper} pointed to the hidden thread. {name} stopped the spin, and they gently slid the cloth free.",
        "resolution": "The globe turned again, slowly and safely, while the loose thread was tied into a neat little bow.",
        "cause": "a display thread caught beneath the stand and pulled the globe off balance",
        "deed": "stopped the spin and worked with the helper to free the hidden thread",
        "result": "the thread came loose and the Earth turned safely again",
    },
    {
        "lead": "{name} brought the {earth_material} Earth to the window so sunlight could shine over its tiny continents.",
        "trigger": "A bright patch of sun warmed one side, and the soft Earth began to wobble on its {support}.",
        "risk": "The warm side sagged slightly, and the model might lose its round shape.",
        "action": "{name} moved the Earth into the shade while {helper} fetched a cool cloth from the teacher.",
        "resolution": "After a quiet rest, the globe regained its shape, and the class placed it where the light was gentle.",
        "cause": "strong sunlight warmed one side of the soft model Earth",
        "deed": "moved the model into shade and asked for a cool cloth",
        "result": "the Earth cooled, regained its shape, and found a gentler spot",
    },
    {
        "lead": "{name} and {helper} added tiny paper stars around the {earth_material} Earth.",
        "trigger": "One star stuck to the stand and tugged the globe into a wobble.",
        "risk": "The star pulled harder whenever someone tried to turn the Earth.",
        "action": "{name} did not yank it. Instead, {helper} warmed the paper with a careful breath while {name} loosened one corner.",
        "resolution": "The star lifted free and became a moon on a new piece of blue paper.",
        "cause": "a paper star stuck to the stand and tugged the globe sideways",
        "deed": "loosened the star carefully instead of yanking it",
        "result": "the star came free and became a new moon decoration",
    },
]

LESSONS = [
    "Ms. Rowan smiled and said, 'A wobble is a message, not a failure.' Luna wrote the sentence on a small card for the display.",
    "Luna learned that careful hands can do more than hurried hands. She showed the class how to pause, look, and then choose one small fix.",
    "The teacher explained that the Earth itself is always moving. The goal was not to freeze it, but to help its movement stay safe.",
    "Luna discovered that asking for help did not make her project less hers. It made the repair kinder and stronger.",
    "The class agreed that mistakes were clues. They began calling the little checklist beneath the globe 'the noticing list.'",
]

TWISTS = [
    "Then came the surprising part: the wobble had revealed a tiny painted heart beneath the stand, left there by last year's class.",
    "Just as everyone cheered, the globe wobbled once more. This time Luna saw that it was not a problem at all; the Earth was showing the moon she had hidden behind it.",
    "The repaired Earth cast a round shadow on the wall, and the shadow looked like a smiling face when Luna stood beside it.",
    "When the teacher turned the globe, a paper note appeared inside the stand: 'Keep looking gently.' It was Luna's own note from the first day, forgotten there.",
    "The class expected the display to be perfect, but the children chose to leave one tiny wobble mark on the label as a reminder that learning can be visible.",
]

ENDINGS = [
    "At day's end, Luna placed the Earth in the window. It turned slowly, steady on its little stand, while a heart-shaped shadow rested beside it.",
    "Before going home, Luna and {helper} took turns giving the globe one gentle spin. Each turn ended with the same warm, careful wobble.",
    "The next morning, classmates gathered around the display. Luna showed them the repair, and the Earth seemed to shine brighter because everyone knew its story.",
    "Luna carried the lesson home in her pocket on a folded card: 'Pause. Notice. Help.' Under the evening lamp, the model Earth turned without fear.",
    "The classroom grew quiet as the globe spun. Its painted oceans caught the light, and Luna felt proud—not because nothing went wrong, but because she knew what to do.",
]


ASP_RULES = r"""
#show valid/4.
#show valid_story/6.

child(N) :- name(N).
helper(H) :- helper_name(H).
teacher(T) :- teacher_name(T).
place(P) :- place_name(P).
material(M) :- material_name(M).
support(S) :- support_name(S).

compatible(M, S) :- material_support(M, S).
valid(N, M, S, P) :- name(N), material_name(M), support_name(S), place_name(P), compatible(M, S).
valid_story(N, H, T, M, S, P) :- valid(N, M, S, P), helper_name(H), teacher_name(T).
"""


MATERIAL_SUPPORTS = [
    ("painted paper", "a cork stand"),
    ("painted paper", "a ring of felt"),
    ("blue clay", "a ring of felt"),
    ("blue clay", "three smooth pebbles"),
    ("a papier-mâché shell", "a cork stand"),
    ("a papier-mâché shell", "a folded cardboard base"),
    ("a soft wooden globe", "three smooth pebbles"),
    ("a soft wooden globe", "a folded cardboard base"),
]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in NAMES:
        lines.append(asp.fact("name", value))
    for value in HELPERS:
        lines.append(asp.fact("helper_name", value))
    for value in TEACHERS:
        lines.append(asp.fact("teacher_name", value))
    for value in PLACES:
        lines.append(asp.fact("place_name", value))
    for value in MATERIALS:
        lines.append(asp.fact("material_name", value))
    for value in SUPPORTS:
        lines.append(asp.fact("support_name", value))
    for material, support in MATERIAL_SUPPORTS:
        lines.append(asp.fact("material_support", material, support))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return list(dict.fromkeys(MATERIAL_SUPPORTS))


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted({(material, support) for _, material, support, _ in asp.atoms(model, "valid")})


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    clingo_pairs = set(asp_valid_combos())
    if python_pairs == clingo_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_pairs - clingo_pairs:
        print("  only in python:", sorted(python_pairs - clingo_pairs))
    if clingo_pairs - python_pairs:
        print("  only in clingo:", sorted(clingo_pairs - python_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming storyworld about Luna, a wobbling Earth, and a lesson learned."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--teacher", choices=TEACHERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--earth-material", dest="earth_material", choices=MATERIALS)
    parser.add_argument("--support", choices=SUPPORTS)
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
    combos = valid_combos()
    if args.earth_material and args.support:
        if (args.earth_material, args.support) not in combos:
            raise StoryError(
                "No believable story: that Earth material and support do not make a steady display."
            )
    if args.earth_material:
        combos = [pair for pair in combos if pair[0] == args.earth_material]
    if args.support:
        combos = [pair for pair in combos if pair[1] == args.support]
    if not combos:
        raise StoryError("No valid Earth material and support pair matches the requested options.")
    material, support = rng.choice(sorted(combos))
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        teacher=args.teacher or rng.choice(TEACHERS),
        place=args.place or rng.choice(PLACES),
        earth_material=material,
        support=support,
        incident=rng.randrange(len(INCIDENTS)),
        lesson=rng.randrange(len(LESSONS)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.lesson = (seed // len(INCIDENTS)) % len(LESSONS)
    params.twist = (seed // 3) % len(TWISTS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "name": params.name,
        "helper": params.helper,
        "teacher": params.teacher,
        "place": params.place,
        "earth_material": params.earth_material,
        "support": params.support,
    }
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    world = World()
    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            label=params.name,
            memes={"curiosity": 0.4, "confidence": 0.2},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            label=params.helper,
            memes={"kindness": 0.5},
        )
    )
    teacher = world.add(
        Entity(
            id=params.teacher,
            kind="character",
            label=params.teacher,
            memes={"patience": 0.7},
        )
    )
    earth = world.add(
        Entity(
            id="earth_model",
            kind="model",
            label="the model Earth",
            meters={"balance": 0.8, "motion": 0.4},
            memes={"meaning": 0.2},
        )
    )
    stand = world.add(
        Entity(
            id="display_support",
            kind="support",
            label=params.support,
            meters={"stability": 0.8},
            memes={"trust": 0.2},
        )
    )

    world.say(
        f"In {values['place']}, {params.name} was preparing a model Earth for the class display."
    )
    world.say(
        f"The {params.earth_material} globe rested on {params.support}, and {params.teacher} "
        f"reminded everyone that the real Earth is always moving."
    )
    world.say(incident["lead"].format(**values))

    world.para()
    earth.meters["balance"] = 0.3
    earth.meters["motion"] = 0.8
    earth.memes["meaning"] = 0.8
    stand.meters["stability"] = 0.3
    child.memes["worry"] = 0.8
    world.say(incident["trigger"].format(**values))
    world.say(incident["risk"].format(**values))
    world.say(f'"Should we catch it?" asked {params.name}.')
    world.say(f'"First, let us notice why it is wobbling," said {params.helper}.')
    world.say(incident["action"].format(**values))

    world.para()
    stand.meters["stability"] = 1.0
    earth.meters["balance"] = 1.0
    earth.memes["meaning"] = 1.0
    child.memes["worry"] = 0.1
    child.memes["confidence"] = 1.0
    helper.memes["pride"] = 0.8
    world.say(incident["resolution"].format(**values))
    world.say(LESSONS[params.lesson % len(LESSONS)].format(**values))
    world.say(TWISTS[params.twist % len(TWISTS)].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.name,
        helper=params.helper,
        teacher=params.teacher,
        place=params.place,
        earth_material=params.earth_material,
        support=params.support,
        incident=params.incident % len(INCIDENTS),
        wobble_cause=incident["cause"],
        helpful_action=incident["deed"],
        result=incident["result"],
        lesson=LESSONS[params.lesson % len(LESSONS)],
        twist=TWISTS[params.twist % len(TWISTS)],
        wobble_resolved=True,
    )

    prompts = [
        "Write a heartwarming child-friendly story about Luna discovering that a wobbling model Earth can teach a lesson.",
        f"Tell a story in which {params.name} and {params.helper} carefully repair a wobbling Earth model in {params.place}.",
        f"Write a gentle story with a lesson learned and a surprising twist about {params.earth_material} resting on {params.support}.",
    ]

    story_qa = [
        QAItem(
            question="Who was preparing the model Earth?",
            answer=f"{params.name} was preparing the model Earth with help from {params.helper} in {params.place}.",
        ),
        QAItem(
            question="Why did the Earth wobble?",
            answer=f"The Earth wobbled because {incident['cause']}.",
        ),
        QAItem(
            question=f"What did {params.name} do to help?",
            answer=f"{params.name} {incident['deed']}.",
        ),
        QAItem(
            question="What lesson did Luna learn?",
            answer=LESSONS[params.lesson % len(LESSONS)],
        ),
        QAItem(
            question="What was the twist?",
            answer=TWISTS[params.twist % len(TWISTS)],
        ),
        QAItem(
            question="How was the problem resolved?",
            answer=f"In the end, {incident['result']}. The Earth could move safely again.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is Earth?",
            answer="Earth is the planet where people, animals, and plants live.",
        ),
        QAItem(
            question="What does it mean for something to wobble?",
            answer="To wobble means to move from side to side in an unsteady way.",
        ),
        QAItem(
            question="Why is it useful to pause when something goes wrong?",
            answer="Pausing gives us time to notice the cause and choose a safe, helpful action.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is an idea or skill someone gains from an experience.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story different from what readers expected.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:16} ({entity.kind:10}) {' '.join(details)}")
    if world.facts:
        lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            name="Luna",
            helper="Milo",
            teacher="Ms. Rowan",
            place="the little planetarium",
            earth_material="painted paper",
            support="a cork stand",
            incident=0,
            lesson=0,
            twist=0,
            ending=0,
        ),
        StoryParams(
            name="Maya",
            helper="Sage",
            teacher="Mr. Sol",
            place="the school science room",
            earth_material="blue clay",
            support="three smooth pebbles",
            incident=1,
            lesson=1,
            twist=1,
            ending=1,
        ),
        StoryParams(
            name="Nell",
            helper="Pip",
            teacher="Dr. Fern",
            place="the library's bright study corner",
            earth_material="a papier-mâché shell",
            support="a folded cardboard base",
            incident=2,
            lesson=2,
            twist=2,
            ending=2,
        ),
        StoryParams(
            name="Tavi",
            helper="Ari",
            teacher="Ms. Avery",
            place="the community garden classroom",
            earth_material="a soft wooden globe",
            support="a ring of felt",
            incident=4,
            lesson=3,
            twist=4,
            ending=4,
        ),
    ]


CURATED = build_curated()


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for curated in CURATED:
            generate(curated)
        print(f"OK: generated {len(CURATED)} curated stories.")
        return
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible Earth material/support pairs:\n")
        for material, support in pairs:
            print(f"  {material:24} -> {support}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name}: a wobbling Earth lesson"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
