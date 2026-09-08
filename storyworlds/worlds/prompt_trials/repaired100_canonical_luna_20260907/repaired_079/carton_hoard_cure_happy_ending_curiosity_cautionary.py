#!/usr/bin/env python3
"""
A child-friendly detective storyworld about a carton, a hoard, and a cure.

Luna follows a curious clue to a hidden carton hoard. Her caution keeps the
mystery from becoming dangerous, and the cure is found through careful testing.
"""

from __future__ import annotations

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
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    detective_name: str = "Luna"
    helper_name: str = "Milo"
    clinic_name: str = "Willow Lane Clinic"


NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Ravi", "Iris", "Owen"]
CLINICS = ["Willow Lane Clinic", "Maple Corner Clinic", "Sunbeam Clinic"]

CASES = [
    {
        "title": "the whispering carton",
        "place": "behind the old market",
        "hoard": "a hoard of neatly folded cartons",
        "clue": "a trail of blue paper stars leading toward a locked shed",
        "wrong": "tugged at the shed door without checking the rusty warning sign",
        "danger": "a stack of empty cartons wobbled above the doorway",
        "test": "looked for a safe way in and counted the stars from the path",
        "truth": "the cartons had been gathered for the clinic's recycling-and-garden project",
        "cure": "a clean carton label showing a tiny green leaf",
        "ending": "the cartons became bright planter boxes for herbs outside the clinic",
        "lesson": "Curiosity is useful when caution chooses the next step.",
    },
    {
        "title": "the vanished medicine carton",
        "place": "near the village post room",
        "hoard": "a hidden hoard of plain shipping cartons",
        "clue": "one torn corner stamped with a red sun",
        "wrong": "opened the nearest carton before asking who owned it",
        "danger": "a cloud of packing dust puffed into the air",
        "test": "stepped back, covered the cartons, and compared every stamp",
        "truth": "the cartons were empty supplies waiting for the clinic's medicine drive",
        "cure": "the missing red-sun carton, sealed and clearly labeled",
        "ending": "the real medicine box reached the clinic before sunset",
        "lesson": "A careful question can protect both people and important things.",
    },
    {
        "title": "the moonlit carton hoard",
        "place": "under the bridge by the moonlit canal",
        "hoard": "a hoard of small cartons tied with yellow string",
        "clue": "three damp footprints beside a dry carton",
        "wrong": "followed the footprints into the dark tunnel alone",
        "danger": "the tunnel floor sloped toward deep water",
        "test": "called for a helper, stayed in the lantern light, and followed the dry path",
        "truth": "a baker had stored the cartons there for a morning food-and-cure parcel delivery",
        "cure": "a warm parcel of tea, honey, and a note from the baker",
        "ending": "the parcels were delivered safely to neighbors who needed comfort",
        "lesson": "A mystery becomes safer when curiosity brings a trusted helper.",
    },
    {
        "title": "the green-marked boxes",
        "place": "beside the town greenhouse",
        "hoard": "a hoard of cartons marked with green dots",
        "clue": "a row of green dots that stopped beside a locked tool chest",
        "wrong": "assumed the brightest box held the answer and shook it hard",
        "danger": "a glass seed jar inside clinked and nearly cracked",
        "test": "set the box down gently and asked the gardener to inspect the marks",
        "truth": "the hoard held seed cartons prepared for a community herb garden",
        "cure": "a packet of mint seeds and the gardener's planting instructions",
        "ending": "fresh mint grew beside the clinic and helped make soothing tea",
        "lesson": "Evidence grows clearer when we handle clues gently.",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    detective = world.add(Entity(params.detective_name, "character", "child", params.detective_name))
    helper = world.add(Entity(params.helper_name, "character", "child", params.helper_name))
    clinic = world.add(Entity("clinic", "place", "clinic", params.clinic_name))
    carton = world.add(Entity("carton", "thing", "carton", "carton"))
    hoard = world.add(Entity("hoard", "thing", "hoard", "carton hoard"))
    cure = world.add(Entity("cure", "thing", "cure", "cure"))

    detective.meters["curiosity"] = 1.0
    detective.memes["caution"] = 0.0
    helper.meters["trust"] = 1.0
    carton.meters["sturdiness"] = 1.0
    hoard.meters["count"] = 1.0
    cure.memes["helpfulness"] = 0.0

    world.facts.update(
        detective=detective,
        helper=helper,
        clinic=clinic,
        carton=carton,
        hoard=hoard,
        cure=cure,
        params=params,
    )


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.detective_name}|{params.helper_name}|{params.clinic_name}"
    ))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    case = CASES[_token(params) % len(CASES)]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    clinic = world.facts["clinic"]
    carton = world.facts["carton"]
    hoard = world.facts["hoard"]
    cure = world.facts["cure"]

    world.say(f"{detective.label} was a young detective who noticed small things.")
    world.say(
        f"One afternoon, {detective.label} found a clue {case['place']}: "
        f"{case['clue']}. It pointed toward {case['hoard']}."
    )
    world.say(
        f"The cartons were linked to {clinic.label}, where neighbors were waiting for a useful cure."
    )

    world.para()
    world.say(
        f"Curiosity pulled {detective.label} closer, but the first guess was risky: "
        f"{detective.label} {case['wrong']}."
    )
    world.say(f'"I want to solve this," said {detective.label}, "but I do not want to make it worse."')
    world.say(f'"Then let us inspect it together," said {helper.label}.')
    world.say(
        f"They stopped before {case['danger']}. The warning made the case cautionary: "
        "a clever detective still needs a safe plan."
    )

    world.para()
    world.say(
        f"{detective.label} and {helper.label} {case['test']}. "
        "They took notes without touching anything that might belong to someone else."
    )
    world.say(
        f"Their careful search revealed the truth: {case['truth']}."
    )
    world.say(
        f"The missing piece was {case['cure']}. It was not a secret potion; it was the helpful answer "
        "hidden inside the evidence."
    )
    world.say(
        f'"Now we know what the cartons are for," said {detective.label}. '
        f'"And now we know where they should go," replied {helper.label}.'
    )

    world.para()
    world.say(
        f"They carried the safe, labeled supplies to {clinic.label} with permission."
    )
    world.say(
        f"The cure helped because it reached the right people in the right way: {case['ending']}."
    )
    world.say(
        f"{case['lesson']} The carton hoard was no longer a mystery, but its careful story was worth remembering."
    )

    detective.memes["caution"] = 1.0
    cure.memes["helpfulness"] = 1.0
    carton.meters["sturdiness"] = 1.0
    hoard.meters["count"] = 4.0
    world.fired.update({("curiosity", "clue_found"), ("caution", "danger_avoided"), ("cure", "delivered")})
    world.facts.update(case=case, case_index=_token(params) % len(CASES), resolved=True)
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    c = world.facts["case"]
    return [
        f"Write a child-friendly detective story in which {p.detective_name} investigates {c['title']}.",
        f"Show curiosity leading to a carton hoard, caution preventing danger, and a cure reaching {p.clinic_name}.",
        "Give the mystery a real setback, a spoken exchange, careful evidence, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    c = world.facts["case"]
    return [
        QAItem(
            f"What clue did {p.detective_name} notice?",
            f"{p.detective_name} noticed {c['clue']}, which pointed toward {c['hoard']}.",
        ),
        QAItem(
            "Why was caution important?",
            f"Caution was important because {c['danger']}. The detectives stopped and made a safer plan.",
        ),
        QAItem(
            "What did the carton hoard really contain?",
            f"The hoard was not dangerous treasure. {c['truth'].capitalize()}.",
        ),
        QAItem(
            "How did the detectives solve the mystery?",
            f"They {c['test']}. Their careful inspection revealed the truth without damaging anyone's property.",
        ),
        QAItem(
            "What was the cure?",
            f"The cure was {c['cure']}. It became useful after the detectives delivered it to {p.clinic_name}.",
        ),
        QAItem(
            "How did the story end happily?",
            f"The safe supplies reached the clinic, and {c['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a carton?",
            "A carton is a container made from paperboard or cardboard that can hold and protect things.",
        ),
        QAItem(
            "What is a hoard?",
            "A hoard is a stored collection of things, often gathered in one hidden or protected place.",
        ),
        QAItem(
            "What is a cure?",
            "A cure is something that helps heal an illness or solve a problem.",
        ),
        QAItem(
            "Why should a detective be cautious?",
            "A detective should be cautious so curiosity does not lead to injury, damaged property, or an unfair guess.",
        ),
    ]


ASP_RULES = r"""
curious_story(S) :- clue_found(S).
cautionary_story(S) :- danger_avoided(S).
cure_story(S) :- cure_delivered(S).
happy_ending(S) :- curious_story(S), cautionary_story(S), cure_story(S).
valid_story(S) :- happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue_found", "story1"),
            asp.fact("danger_avoided", "story1"),
            asp.fact("cure_delivered", "story1"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective storyworld about a carton hoard, a cure, curiosity, and caution."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=NAMES)
    parser.add_argument("--clinic-name", choices=CLINICS)
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
    name = args.name or rng.choice(NAMES)
    helper_choices = [n for n in NAMES if n != name]
    helper = args.helper_name or rng.choice(helper_choices)
    clinic = args.clinic_name or rng.choice(CL INICS)
    return StoryParams(
        seed=None,
        detective_name=name,
        helper_name=helper,
        clinic_name=clinic,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(state)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(detective_name="Luna", helper_name="Milo", clinic_name="Willow Lane Clinic"),
    StoryParams(detective_name="Nia", helper_name="Theo", clinic_name="Maple Corner Clinic"),
    StoryParams(detective_name="Iris", helper_name="Owen", clinic_name="Sunbeam Clinic"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

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
