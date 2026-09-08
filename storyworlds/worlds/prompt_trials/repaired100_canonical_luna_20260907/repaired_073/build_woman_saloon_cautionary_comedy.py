#!/usr/bin/env python3
"""
A child-facing cautionary comedy about a woman building a saloon sign safely.
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


SETTINGS = {
    "dusty_town": {
        "place": "the dusty town square",
        "detail": "The square had a wooden platform, a shady porch, and a wide patch of packed earth for careful work.",
        "affords": {"build", "gather", "repair"},
    },
    "river_town": {
        "place": "the riverside town square",
        "detail": "A slow river shone beside the square, where ropes, planks, and painted boards waited under a canvas awning.",
        "affords": {"build", "gather", "repair"},
    },
    "hill_town": {
        "place": "the little hill-town square",
        "detail": "The square sat on a gentle hill, so every loose object seemed eager to roll downhill.",
        "affords": {"build", "gather", "repair"},
    },
}

NAMES = ["Luna", "Mara", "Nell", "Pia", "Rosa", "Tess", "Wren", "Ada"]
TRAITS = ["clever", "cheerful", "brave", "curious", "patient", "bouncy"]
HELPERS = ["Grandma June", "Aunt Bea", "Mister Sol", "Uncle Vic"]

INCIDENTS = [
    {
        "arrival": "Luna had promised to build a bright sign for the new saloon porch.",
        "problem": "The tallest plank wobbled whenever the wind puffed against it.",
        "mistake": "At first, Luna tried to hold the plank with one hand while balancing on a barrel with the other.",
        "clue": "A small scrape in the dirt showed that the barrel was sliding toward the porch steps.",
        "plan": "The woman stepped down, set the barrel aside, and asked the helper to brace the plank while she measured from the ground.",
        "helper_line": "A barrel is a fine place for apples, but a poor place for pretending to be stairs.",
        "child_line": "Then I will build from the ground up, where my boots know what they are doing.",
        "result": "The helper held the frame, Luna fitted two crosspieces, and everyone checked the feet before lifting the sign.",
        "ending": "When evening came, the saloon sign swung gently above the porch, while the barrel safely held a basket of apples.",
        "lesson": "a clever builder stops when a plan becomes unsafe and chooses a steadier method",
        "object": "wooden saloon sign",
    },
    {
        "arrival": "Mara brought painted letters to build a cheerful sign for the town saloon.",
        "problem": "A gust scattered the letters across the square before the glue was ready.",
        "mistake": "Mara chased the biggest letter first, but the letter O rolled away like a wheel.",
        "clue": "The letters had tiny pencil marks on their backs showing where each one belonged.",
        "plan": "The woman crouched on the ground, gathered the letters with a helper, and sorted them by their marks before building anything.",
        "helper_line": "That O has gone on a round adventure, but it still needs a proper address.",
        "child_line": "I will stop chasing and start reading the clues.",
        "result": "The letters were sorted, glued by an adult, and pressed under boards until the sign was secure.",
        "ending": "The word SALOON shone above the porch, and the runaway O rested politely between two wooden blocks.",
        "lesson": "slowing down to organize scattered pieces can prevent a small mess from becoming a bigger one",
        "object": "painted letters",
    },
    {
        "arrival": "Nell wanted to build a little porch bench outside the saloon for tired travelers.",
        "problem": "Two boards looked alike, but one had a cracked end hidden under old paint.",
        "mistake": "Nell chose the shinier board because she thought it looked more important.",
        "clue": "Tapping both boards made the cracked one give a hollow, rattly sound.",
        "plan": "The woman put the boards on the ground, asked a helper to inspect them, and used the sound and visible crack to choose safe wood.",
        "helper_line": "Shiny paint can hide a grumpy board, but it cannot hide every rattle.",
        "child_line": "Then the rattle gets a vote before the bench does.",
        "result": "The cracked board became a short shelf, and the sound boards formed a sturdy bench.",
        "ending": "Travelers sat on the new bench while the old cracked board held a row of flowerpots.",
        "lesson": "checking materials before building helps people use the right piece for the right job",
        "object": "bench boards",
    },
    {
        "arrival": "Pia was helping build a small counter for the saloon kitchen.",
        "problem": "A box of nails had tipped over, and shiny nails covered the walking path.",
        "mistake": "Pia reached quickly for the nearest nail without noticing how close it was to a boot.",
        "clue": "The nails glittered beside the path where people carried heavy boards.",
        "plan": "The woman stopped the work, asked everyone to step back, and had the helper sweep the nails into a tin before building again.",
        "helper_line": "A tiny nail can make a very large story if someone steps on it.",
        "child_line": "This is one story I would rather keep in the tin.",
        "result": "The path was cleared, the nails were counted, and the counter was built on a clean work area.",
        "ending": "The finished counter held cups and plates, while every nail slept safely inside its tin.",
        "lesson": "cleaning a work area before continuing can keep a building job safe",
        "object": "counter",
    },
    {
        "arrival": "Rosa planned to build a shade awning for the saloon porch.",
        "problem": "The cloth was longer than the porch, and one corner dragged near a wagon wheel.",
        "mistake": "Rosa tugged the cloth alone, hoping it would become shorter through determination.",
        "clue": "The dragging corner left a dusty line straight toward the wheel.",
        "plan": "The woman folded the cloth on the ground, marked the safe length, and asked a helper to hold the opposite corner while an adult trimmed it.",
        "helper_line": "Determination is strong, but it has never learned to measure.",
        "child_line": "Good. The measuring tape can be the boss today.",
        "result": "The cloth was trimmed and tied high enough that wagons could pass beneath it.",
        "ending": "The awning made a cool blue shadow, and the wagon wheel rolled past without eating a single corner.",
        "lesson": "measuring and asking for help make building plans more reliable",
        "object": "shade awning",
    },
    {
        "arrival": "Tess came to build a flower box beneath the saloon window.",
        "problem": "The box leaned because one foot was shorter than the others.",
        "mistake": "Tess tried to fix the lean by putting a pebble under it and calling the pebble a foundation.",
        "clue": "Water poured into the box ran toward the same low corner.",
        "plan": "The woman emptied the box, checked it on level ground, and replaced the pebble with a proper wooden shim chosen by the helper.",
        "helper_line": "That pebble is brave, but it is not trained in carpentry.",
        "child_line": "It may return to its old career as a pebble.",
        "result": "The box sat level, and the adults secured it before adding soil.",
        "ending": "Bright flowers grew evenly beneath the window, and the pebble rested beside a path as itself again.",
        "lesson": "testing a structure and using the right material works better than a funny shortcut",
        "object": "flower box",
    },
    {
        "arrival": "Wren wanted to build a small stage for music outside the saloon.",
        "problem": "The boards were stacked beside a slope, and one board began to slide downhill.",
        "mistake": "Wren chased it while carrying a hammer, which made both the board and the hammer wobble.",
        "clue": "A trail of dust showed that several boards could slide if the stack stayed there.",
        "plan": "The woman put down the hammer, moved away from the slope, and asked adults to shift the boards to flat ground before building.",
        "helper_line": "A hammer is useful for boards, but it cannot argue with a hill.",
        "child_line": "Then the hill gets no more boards until we choose a flatter floor.",
        "result": "The boards were stacked safely on level ground, and the stage frame was built there.",
        "ending": "Musicians played on the sturdy stage, while the hill watched empty-handed.",
        "lesson": "moving materials to a safe place before building prevents chasing trouble",
        "object": "small stage",
    },
    {
        "arrival": "Ada was asked to build a little signpost pointing visitors toward the saloon porch.",
        "problem": "The arrow pointed toward a muddy ditch instead of the porch.",
        "mistake": "Ada said the ditch must be the saloon's secret entrance.",
        "clue": "Footprints and the porch steps showed that visitors actually approached from the other direction.",
        "plan": "The woman compared the map, the footprints, and the building before turning the arrow with a helper.",
        "helper_line": "A secret entrance should at least have a dry welcome mat.",
        "child_line": "Then this ditch is only secretly muddy.",
        "result": "The signpost was turned toward the porch and set firmly in the ground.",
        "ending": "Visitors followed the arrow to the saloon, while the ditch kept its very private puddles.",
        "lesson": "checking a plan against real evidence is better than trusting a funny guess",
        "object": "signpost",
    },
]

OPENINGS = [
    "One sunny morning",
    "After breakfast",
    "On a breezy afternoon",
    "Just before supper",
    "While the town woke up",
    "Near the end of a warm day",
]

TURN_WORDS = [
    "Then a small detail changed the plan.",
    "But the work gave them a warning.",
    "That was when Luna noticed something important.",
    "The first idea sounded funny, but it was not safe.",
    "A careful look showed the better answer.",
    "Just then, the ground offered a useful clue.",
]

ENDINGS = [
    "By sunset",
    "When the sky turned pink",
    "Before the evening lamps were lit",
    "As the last customers arrived",
    "At the end of the workday",
    "When the first stars appeared",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
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


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    turn: int = 0
    ending: int = 0
    humor: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary comedy about building something for a saloon."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "woman"])
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender or "woman"
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        name=name,
        gender=gender,
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        turn=rng.randrange(len(TURN_WORDS)),
        ending=rng.randrange(len(ENDINGS)),
        humor=rng.randrange(8),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("The chosen place is not available for this building story.")
    if params.gender not in {"girl", "woman"}:
        raise StoryError("The builder must be a girl or woman in this storyworld.")
    if params.helper not in HELPERS:
        raise StoryError("The chosen helper is not part of this town.")
    if not 0 <= params.incident < len(INCIDENTS):
        raise StoryError("The building problem is outside the storyworld.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident]
    world = World(place=setting["place"])

    builder = world.add(Entity(
        id="Builder",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"care": 1.0, "confidence": 0.8, "risk_awareness": 0.3},
        memes={"pride": 0.8, "humor": 0.7},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="adult",
        label=params.helper,
        meters={"care": 1.0, "experience": 1.0},
        memes={"patience": 1.0},
    ))
    saloon = world.add(Entity(
        id="Saloon",
        kind="place",
        type="saloon",
        label="saloon",
        phrase="the little wooden saloon",
        meters={"open": 0.0, "welcoming": 0.8},
        memes={"community": 1.0},
    ))
    material = world.add(Entity(
        id="BuildObject",
        kind="thing",
        type="building_material",
        label=incident["object"],
        phrase=f"the {incident['object']}",
        owner="Builder",
        meters={"assembled": 0.0, "safe": 0.0},
        memes={"usefulness": 0.8},
    ))
    tool = world.add(Entity(
        id="Tool",
        kind="thing",
        type="tool",
        label="measuring tape",
        phrase="a yellow measuring tape",
        owner="Helper",
        meters={"available": 1.0},
        memes={"carefulness": 1.0},
    ))
    ground = world.add(Entity(
        id="Ground",
        kind="place",
        type="work_area",
        label="work area",
        phrase="a clear, level work area",
        meters={"clear": 0.0, "level": 1.0},
    ))

    name = params.name
    world.say(
        f"{OPENINGS[params.opening]}, {name}, a {params.trait} {params.gender}, came to {world.place} to build something useful for the town saloon."
    )
    world.say(setting["detail"])
    world.say(incident["arrival"])
    world.say(
        f"{params.helper} watched nearby and kept the measuring tape ready, because a good build begins with a good look."
    )
    world.para()

    world.say(incident["problem"])
    world.say(incident["mistake"])
    world.say(
        f'{params.helper} called, "{incident["helper_line"]}"'
    )
    world.say(
        f'{name} answered, "{incident["child_line"]}"'
    )
    world.say(
        f"{name} took one step back and looked at the work area instead of trying the same trick again."
    )
    world.say(f"{TURN_WORDS[params.turn]} {incident['clue']}")
    world.para()

    world.say(
        f"{incident['plan'].replace('The woman', name).replace('the woman', name)}"
    )
    world.say(
        f"{params.helper} asked, 'What do we check before we lift it?'"
    )
    world.say(
        f'{name} replied, "The ground, the pieces, and where our feet will go."'
    )
    world.say(
        f"{incident['result']}"
    )
    world.say(
        f"{name} learned that {incident['lesson']}."
    )
    world.say(
        "The work was still cheerful, but nobody treated a wobble, a sharp nail, a sliding board, or a muddy ditch as a joke."
    )
    world.para()

    world.say(
        f"{ENDINGS[params.ending]}, the finished {incident['object']} belonged beside the saloon, and the work area was clear again."
    )
    world.say(incident["ending"])
    world.say(
        f"The woman builder smiled at {params.helper}. 'A safe build is a happy build,' she said."
    )
    world.say(
        f"{params.helper} nodded. 'And a happy build gives the town one less thing to trip over.'"
    )

    material.meters["assembled"] = 1.0
    material.meters["safe"] = 1.0
    ground.meters["clear"] = 1.0
    builder.meters["risk_awareness"] = 1.0
    builder.memes["pride"] = 1.0
    saloon.meters["open"] = 1.0

    world.facts.update(
        builder=builder,
        helper=helper,
        saloon=saloon,
        material=material,
        tool=tool,
        ground=ground,
        params=params,
        incident=incident,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a cautionary comedy for a young child about {params.name}, a woman who builds a {incident['object']} for a saloon.",
        f"Tell a funny story in which a building mistake becomes a safety lesson through dialogue and careful checking.",
        f"Write a child-friendly saloon story showing that {incident['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question="Who built something for the saloon?",
            answer=f"{params.name}, a {params.trait} {params.gender}, built the {incident['object']} for the town saloon.",
        ),
        QAItem(
            question="What went wrong during the building work?",
            answer=incident["problem"],
        ),
        QAItem(
            question="What clue helped the builder understand the danger?",
            answer=incident["clue"],
        ),
        QAItem(
            question="How did the builder and helper make the work safe?",
            answer=f"{incident['plan']} {incident['result']}",
        ),
        QAItem(
            question="What lesson did the builder learn?",
            answer=f"{params.name} learned that {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does build mean?",
            answer="Build means to put materials together to make something useful or strong.",
        ),
        QAItem(
            question="What is a saloon?",
            answer="A saloon is an old-fashioned public place where people might meet, eat, drink, and talk.",
        ),
        QAItem(
            question="Why should people check a building area?",
            answer="People should check a building area to find sharp objects, loose materials, slippery spots, or other dangers before they work.",
        ),
        QAItem(
            question="Why can asking for help be wise?",
            answer="Asking for help can be wise because another person may notice a danger, hold a piece steady, or know a safer method.",
        ),
        QAItem(
            question="What is a measuring tape used for?",
            answer="A measuring tape is used to find the length or distance of something so pieces can fit properly.",
        ),
    ]


ASP_RULES = r"""
#show safe_build/1.
safe_build(story) :-
    woman_builder,
    saloon_project,
    caution_checked,
    dialogue_plan,
    material_secure.
"""


def asp_facts() -> str:
    return "\n".join(
        [
            "woman_builder.",
            "saloon_project.",
            "caution_checked.",
            "dialogue_plan.",
            "material_secure.",
        ]
    )


def asp_program(show: str = "#show safe_build/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        symbols = asp.one_model(asp_program())
        if not asp.atoms(symbols, "safe_build"):
            print("ASP verification failed: no safe_build atom.", file=sys.stderr)
            return 1
    except ImportError:
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}", file=sys.stderr)
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "saloon" not in sample.story.lower():
            print("Python verification failed: incomplete story.", file=sys.stderr)
            return 1
        if len(sample.story_qa) < 5:
            print("Python verification failed: missing story QA.", file=sys.stderr)
            return 1
        if "said" not in sample.story and '"' not in sample.story:
            print("Python verification failed: missing dialogue.", file=sys.stderr)
            return 1
        if sample.world is None or sample.world.facts["material"].meters["safe"] != 1.0:
            print("Python verification failed: unsafe final state.", file=sys.stderr)
            return 1
    return 0


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
        lines.append(
            f"  {entity.id:12} ({entity.type:18}) {' '.join(details)}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="dusty_town",
        name="Luna",
        gender="woman",
        helper="Grandma June",
        trait="clever",
        incident=0,
        opening=0,
        turn=0,
        ending=0,
        humor=1,
    ),
    StoryParams(
        place="river_town",
        name="Mara",
        gender="woman",
        helper="Aunt Bea",
        trait="cheerful",
        incident=1,
        opening=2,
        turn=2,
        ending=1,
        humor=3,
    ),
    StoryParams(
        place="hill_town",
        name="Tess",
        gender="woman",
        helper="Uncle Vic",
        trait="bouncy",
        incident=6,
        opening=4,
        turn=5,
        ending=4,
        humor=6,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            from storyworlds import asp
            symbols = asp.one_model(asp_program())
            atoms = asp.atoms(symbols, "safe_build")
            if atoms:
                print("1 safe build: woman builder, saloon project, caution checked, dialogue plan, material secure")
            else:
                print("0 safe builds")
        except ImportError:
            print("1 safe build: woman builder, saloon project, caution checked, dialogue plan, material secure")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: a cautionary saloon-building comedy"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
