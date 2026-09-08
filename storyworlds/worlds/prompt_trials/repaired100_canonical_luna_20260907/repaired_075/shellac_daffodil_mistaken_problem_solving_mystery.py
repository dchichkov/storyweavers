#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("dry", "coated", "safe", "confusion", "curiosity", "relief"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
    name: str
    animal: str
    helper: str
    case: str
    telling: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Nell", "Pip", "Tavi"]
ANIMALS = ["rabbit", "fox", "mouse", "badger", "cat"]
HELPERS = ["Grandma", "Aunt Suri", "Mr. Rowan", "Uncle Jo"]
CASES = ["greenhouse", "workshop", "schoolroom", "porch", "museum"]

CASE_DATA = {
    "greenhouse": {
        "place": "the old greenhouse",
        "object": "a little wooden flower box",
        "mystery": "a bright daffodil had vanished from the flower box, leaving only a pale crescent of pollen",
        "false": "the damp footprint beside the bench",
        "clue": "a thin amber shine on the latch",
        "method": "following the pollen trail and testing the latch before guessing",
        "answer": "the flower had not been stolen at all; a gust had pushed the box behind the watering cart",
        "ending": "The daffodil stood in a sunny jar, glowing beside the restored flower box.",
    },
    "workshop": {
        "place": "the village repair workshop",
        "object": "a small display plaque",
        "mystery": "a daffodil painted on the plaque had turned cloudy beneath its protective shellac",
        "false": "a dark brush mark that looked like a spill",
        "clue": "the shellac was smooth everywhere except where a loose thread had rested",
        "method": "examining the surface under a lamp and asking when the plaque had last been moved",
        "answer": "the cloudy shape came from a thread trapped under fresh shellac, not from a careless painter",
        "ending": "After the careful repair, the golden daffodil shone beneath a clear, even coat of shellac.",
    },
    "schoolroom": {
        "place": "the little schoolroom",
        "object": "a locked science cupboard",
        "mystery": "a shellac jar and a pressed daffodil seemed to have switched places on the teacher's shelf",
        "false": "the muddy mark below the cupboard",
        "clue": "the shelf dust was unbroken except for a narrow line made by a sliding box",
        "method": "comparing the shelf marks, the labels, and the cupboard key",
        "answer": "the boxes had been slid aside during cleaning, and the mistaken labels had made the arrangement look mysterious",
        "ending": "The corrected labels rested above the daffodil, while the shellac jar gleamed safely behind the cupboard door.",
    },
    "porch": {
        "place": "the rain-darkened porch",
        "object": "a framed botanical drawing",
        "mystery": "the drawing's daffodil looked wet, although its frame was dry",
        "false": "a round water mark near the rocking chair",
        "clue": "the drops all pointed toward the glass rather than away from it",
        "method": "checking the direction of the drops and opening the frame from the back",
        "answer": "condensation had formed inside the glass after the warm frame met the cold rain",
        "ending": "The dry drawing showed its daffodil clearly as the rain whispered beyond the porch.",
    },
    "museum": {
        "place": "the town history museum",
        "object": "a case of garden treasures",
        "mystery": "the label for a shellac sample pointed toward a pressed daffodil instead",
        "false": "a visitor's glove lying near the case",
        "clue": "the label cord was twisted around the neighboring hook",
        "method": "tracing the cord, reading the catalog number, and checking the case photograph",
        "answer": "the label had swung on its cord during cleaning and had never been moved by a visitor",
        "ending": "The label hung straight again, and the pressed daffodil rested proudly beside its true shellac sample.",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A shellac, daffodil, and mistaken mystery world.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--telling", type=int, choices=range(4))
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
        name=args.name or rng.choice(NAMES),
        animal=args.animal or rng.choice(ANIMALS),
        helper=args.helper or rng.choice(HELPERS),
        case=args.case or rng.choice(CASES),
        telling=args.telling if args.telling is not None else rng.randrange(4),
    )


def tell(params: StoryParams) -> World:
    if params.case not in CASE_DATA:
        raise StoryError(f"Unknown mystery case: {params.case}")
    data = CASE_DATA[params.case]
    world = World(data["place"])
    hero = world.add(Entity("hero", "character", params.name, params.animal, location=data["place"]))
    helper = world.add(Entity("helper", "character", params.helper, "helper", location=data["place"]))
    shellac = world.add(Entity("shellac", "thing", "shellac", "protective finish", location=data["place"]))
    daffodil = world.add(Entity("daffodil", "thing", "daffodil", "flower", location=data["place"]))
    hero.memes["curiosity"] = 1
    shellac.meters["safe"] = 1
    daffodil.meters["safe"] = 1
    rng = random.Random((params.seed or 0) ^ 0xDAFF10)

    openings = [
        f"{params.name}, a young {params.animal}, loved mysteries because every answer began with a careful look.",
        f"On a quiet morning, {params.name} the {params.animal} noticed that something at {data['place']} did not make sense.",
        f"{params.name} was carrying a notebook when a small puzzle appeared at {data['place']}.",
        f"The day began with sunshine, a bright daffodil, and one very mistaken guess.",
    ]
    world.say(openings[params.telling % len(openings)])
    world.say(f"In {data['place']}, {data['mystery']}.")
    world.say(f"The {data['object']} belonged to the community, so {params.name} wanted to solve the problem without damaging anything.")
    world.para()
    world.say(f"{params.name} pointed at {data['false']} and said, \"That must be what happened.\"")
    world.say(f"{params.helper} shook {params.helper.lower()}s head. \"It may be a clue, but it is not proof. What else can we observe?\"")
    hero.memes["confusion"] = 1
    world.say(f"That question stopped the mistaken guess. {params.name} looked closer and found that {data['clue']}.")
    world.say(f"\"Then the mystery has a trail,\" {params.name} said. \"I will check the evidence before I choose an answer.\"")
    world.para()
    hero.memes["curiosity"] = 2
    world.say(f"{params.name} solved the problem by {data['method']}.")
    world.say(f"The evidence showed that {data['answer']}.")
    hero.memes["confusion"] = 0
    hero.memes["relief"] = 1
    shellac.meters["coated"] = 1
    daffodil.meters["safe"] = 1
    world.say(f"{params.helper} smiled. \"A good mystery is solved by patient questions, not by the first story that sounds right.\"")
    world.say(f"{params.name} nodded. \"Next time, I will test my guess before I call it true.\"")
    world.say(data["ending"])
    world.facts.update(
        hero=hero,
        helper=helper,
        shellac=shellac,
        daffodil=daffodil,
        data=data,
        solved=True,
        method=data["method"],
        false_clue=data["false"],
        clue=data["clue"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    data = world.facts["data"]
    hero = world.facts["hero"]
    return [
        f"Write a mystery for {hero.label} in which shellac and a daffodil seem connected to a mistaken guess.",
        f"Tell a Problem Solving story where {hero.label} uses this clue: {data['clue']}.",
        f"Write a gentle mystery ending with this image: {data['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    data = f["data"]
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem("Who solved the mystery?", f"{hero.label}, a young {hero.type}, solved the mystery by observing carefully and checking the evidence."),
        QAItem("What was the mistaken first guess?", f"{hero.label} first guessed that {data['false']} explained the problem, but that guess was not proof."),
        QAItem("What clue changed the plan?", f"The important clue was that {data['clue']}."),
        QAItem("How was the problem solved?", f"{hero.label} solved it by {data['method']}. The evidence showed that {data['answer']}."),
        QAItem("What did the helper teach?", f"{helper.label} taught that a mystery should be solved with patient questions and evidence rather than the first tempting guess."),
        QAItem("How do we know the ending was safe?", f"The ending shows that {data['ending']}"),
    ]


KNOWLEDGE = [
    QAItem("What is shellac?", "Shellac is a coating made from natural resin that can protect and give a surface a smooth shine."),
    QAItem("What is a daffodil?", "A daffodil is a spring flower, usually yellow or white, with a trumpet-shaped center."),
    QAItem("What does mistaken mean?", "Mistaken means wrong because someone misunderstood or did not yet have enough evidence."),
    QAItem("What is problem solving?", "Problem solving means noticing a difficulty, gathering clues, testing ideas, and choosing a safe answer."),
    QAItem("What is a mystery?", "A mystery is a question or puzzling event whose answer must be discovered from clues."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: location={entity.location}, meters={meters}, memes={memes}")
    lines.append(f"  solved={world.facts.get('solved')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("material", "shellac"),
        asp.fact("object", "daffodil"),
        asp.fact("method", "observe"),
        asp.fact("method", "test"),
        asp.fact("requires", "mystery", "observe"),
        asp.fact("requires", "mystery", "test"),
        asp.fact("safe", "shellac"),
        asp.fact("safe", "daffodil"),
    ])


ASP_RULES = r"""
can_solve(mystery) :- requires(mystery, observe), method(observe),
                       requires(mystery, test), method(test).
valid(mystery) :- can_solve(mystery), safe(shellac), safe(daffodil).
#show can_solve/1.
#show valid/1.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if set(asp.atoms(model, "valid")) == {("mystery",)}:
        print("OK: ASP gate agrees with Python reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("\n".join(str(atom) for atom in asp.one_model(asp_program())))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for i, case in enumerate(CASES):
            params = StoryParams(
                name=NAMES[i % len(NAMES)],
                animal=ANIMALS[i % len(ANIMALS)],
                helper=HELPERS[i % len(HELPERS)],
                case=case,
                telling=i % 4,
                seed=seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(seed + i)
            params = resolve_params(args, rng)
            params.seed = seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
