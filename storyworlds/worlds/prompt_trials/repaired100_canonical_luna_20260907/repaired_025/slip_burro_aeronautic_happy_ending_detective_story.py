#!/usr/bin/env python3
"""
A small detective-story world about a slipping burro, an aeronautic mystery,
and the happy ending that follows careful clues.
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
    owner: Optional[str] = None
    location: str = ""
    slipping: bool = False
    safe: bool = False


@dataclass
class Setting:
    name: str
    affordances: set[str]


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    clue: str
    obstacle: str
    deduction: str
    rescue: str
    ending: str


@dataclass
class StoryParams:
    detective: str
    companion: str
    burro_name: str
    case: str
    aeronautic_object: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


SETTING = Setting(
    name="the hilltop airfield",
    affordances={"tracks", "hangar", "wind", "landing_field", "clues"},
)

CASES = {
    "blue_ribbon": Case(
        id="blue_ribbon",
        opening="At dawn, a blue aeronautic ribbon vanished from the airfield weather balloon.",
        clue="A line of dusty hoofprints crossed the grass, but they stopped beside a patch of spilled oats.",
        obstacle="The burro had slipped on the oats and was tangled in the balloon rope near the old hangar.",
        deduction="The oats proved that the wind had not stolen the ribbon; the burro had tugged the rope while chasing its breakfast.",
        rescue="They scattered fresh oats away from the rope, steadied the burro, and loosened the knot one loop at a time.",
        ending="When the balloon rose again, the burro stood safely beneath it, wearing the recovered blue ribbon like a tiny medal.",
    ),
    "silver_propeller": Case(
        id="silver_propeller",
        opening="A silver propeller disappeared from the little aeronautic glider before its first flight.",
        clue="A bright scratch on the runway led toward a muddy hoofprint and a loose grain sack.",
        obstacle="The burro had slipped beside the sack, and the missing propeller was pinned beneath its soft pack.",
        deduction="The scratch showed that the propeller had rolled downhill before the burro tried to stop it.",
        rescue="The detectives emptied the pack, placed a board under the burro's feet, and lifted the propeller without pulling.",
        ending="The glider skimmed over the field, while the burro received a carrot and a happy pat for helping solve the case.",
    ),
    "cloud_map": Case(
        id="cloud_map",
        opening="The pilot's aeronautic cloud map vanished from a locked office on the morning of the village flight.",
        clue="A damp corner of the map was found beside the stable door, marked with one crooked hoofprint.",
        obstacle="The burro had slipped on rainwater and dragged the map beneath a hay cart while trying to stand.",
        deduction="The wet mark showed that the map had never left the airfield; it had followed the only path from the office to the stable.",
        rescue="They moved the cart slowly, offered the burro a blanket for balance, and pulled the map free.",
        ending="The pilot read the map aloud from the balloon basket, and the burro watched the safe flight from a sunny patch of grass.",
    ),
    "golden_goggles": Case(
        id="golden_goggles",
        opening="The captain's golden goggles disappeared beside the aeronautic hangar.",
        clue="Two round marks in the dust pointed toward a slippery puddle and a trail of burro hair.",
        obstacle="The burro had slipped while carrying a basket and covered the goggles with fallen leaves.",
        deduction="The round marks belonged to the goggles, so the thief was not a fox but the rolling basket.",
        rescue="The friends dried the puddle, helped the burro rise, and searched beneath every leaf along the basket's path.",
        ending="The captain wore the goggles for the afternoon flight, and the burro trotted proudly beside the cheering crew.",
    ),
}

DETECTIVES = ["Luna", "Mira", "Nico", "Tess", "Ivo"]
COMPANIONS = ["Pip", "Sana", "Oren", "June", "Taro"]
BURROS = ["Bruno", "Pepper", "Clover", "Dapple", "Marmalade"]
OBJECTS = ["weather balloon", "glider", "cloud map", "pilot goggles"]

DIALOGUES = [
    ('"A good detective follows the clue, not the noise," said {companion}.',
     '"Then we will begin with the hoofprints," said {detective}.'),
    ('"The burro is frightened, not guilty," said {detective}.',
     '"We can solve the mystery and help it at the same time," replied {companion}.'),
    ('"Look where the trail changes," whispered {companion}.',
     '"That is where the truth is waiting," answered {detective}.'),
    ('"First make the slippery place safe," said {companion}.',
     '"Then we can rescue both the clue and our friend," said {detective}.'),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective Story: slip, burro, aeronautic mystery, and happy ending."
    )
    parser.add_argument("--detective", choices=DETECTIVES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--burro-name", choices=BURROS)
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--aeronautic-object", choices=OBJECTS)
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
    detective = args.detective or rng.choice(DETECTIVES)
    companion = args.companion or rng.choice(
        [name for name in COMPANIONS if name != detective]
    )
    return StoryParams(
        detective=detective,
        companion=companion,
        burro_name=args.burro_name or rng.choice(BURROS),
        case=args.case or rng.choice(sorted(CASES)),
        aeronautic_object=args.aeronautic_object or rng.choice(OBJECTS),
    )


def validate(params: StoryParams) -> None:
    if params.case not in CASES:
        raise StoryError("That detective case is not registered in this airfield.")
    if params.aeronautic_object not in OBJECTS:
        raise StoryError("That aeronautic object is not part of the small airfield.")
    if params.detective == params.companion:
        raise StoryError("A detective and companion must be different people.")
    if not params.detective or not params.burro_name:
        raise StoryError("The case needs both a detective and a burro.")


def tell(params: StoryParams) -> World:
    validate(params)
    case = CASES[params.case]
    world = World(SETTING)
    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type="detective",
        label=params.detective,
        location="airfield",
        memes={"curiosity": 1.0, "care": 0.0, "confidence": 0.0},
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type="companion",
        label=params.companion,
        location="airfield",
        memes={"observation": 1.0, "care": 1.0},
    ))
    burro = world.add(Entity(
        id=params.burro_name,
        kind="animal",
        type="burro",
        label=params.burro_name,
        location="hangar path",
        slipping=True,
        meters={"balance": 0.0, "safety": 0.0},
        memes={"fear": 1.0, "trust": 0.0},
    ))
    object_entity = world.add(Entity(
        id="mystery_object",
        kind="thing",
        type="aeronautic",
        label=params.aeronautic_object,
        location="near the hangar",
        meters={"visibility": 0.0},
    ))
    world.facts.update(
        case=case,
        detective=detective,
        companion=companion,
        burro=burro,
        object=object_entity,
    )

    world.say(
        f"{case.opening} {params.detective}, a careful detective, arrived with "
        f"{params.companion}, a sharp-eyed companion."
    )
    world.say(
        f'"We have a mystery," said {params.detective}. '
        f'"And a burro who may need us," replied {params.companion}.'
    )
    world.say(case.clue)
    world.say(f"{case.obstacle} The slippery ground made every hurried step risky.")
    world.say(
        f'"Let us not accuse {params.burro_name} before we understand the trail," '
        f'said {params.detective}. "{case.deduction}"'
    )
    detective.memes["confidence"] += 1
    companion.memes["observation"] += 1
    burro.memes["trust"] += 1
    world.say(case.rescue)
    burro.slipping = False
    burro.safe = True
    burro.meters["balance"] = 1.0
    burro.meters["safety"] = 1.0
    object_entity.meters["visibility"] = 1.0
    world.say(
        f'"The case is solved," said {params.companion}. '
        f'"And our friend is safe," said {params.detective}.'
    )
    world.say(case.ending)
    return world


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


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    burro: Entity = world.facts["burro"]  # type: ignore[assignment]
    return [
        f"Write a Detective Story about {detective.label} solving a mystery involving a slipping burro.",
        f"Include an aeronautic clue and this turning point: {case.deduction}",
        f"End with a Happy Ending in which {burro.label} is safe and the missing object is recovered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    burro: Entity = world.facts["burro"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {detective.label} investigate?",
            answer=case.opening,
        ),
        QAItem(
            question=f"What clue did {detective.label} and {companion.label} find?",
            answer=case.clue,
        ),
        QAItem(
            question=f"Why was {burro.label} in danger?",
            answer=case.obstacle,
        ),
        QAItem(
            question="What deduction solved the mystery?",
            answer=case.deduction,
        ),
        QAItem(
            question=f"How did the detectives help {burro.label}?",
            answer=case.rescue,
        ),
        QAItem(
            question="How did the story end?",
            answer=case.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burro?",
            answer="A burro is a small donkey often known for being sure-footed, patient, and strong.",
        ),
        QAItem(
            question="What does aeronautic mean?",
            answer="Aeronautic means related to flying machines, balloons, aircraft, or the study of flight.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who studies clues and asks careful questions to discover what happened.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is a conclusion in which the main problem is solved and the characters reach safety or joy.",
        ),
        QAItem(
            question="Why should a detective protect a frightened animal?",
            answer="A detective should protect a frightened animal because solving a mystery should not create more danger for an innocent friend.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: type={entity.type}, location={entity.location}, "
            f"meters={entity.meters}, memes={entity.memes}, "
            f"slipping={entity.slipping}, safe={entity.safe}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid_case(D, C, B, O) :-
    detective(D),
    companion(C),
    burro(B),
    aeronautic_object(O),
    D != C,
    case_name(B),
    object_case(O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name in DETECTIVES:
        lines.append(asp.fact("detective", name))
    for name in COMPANIONS:
        lines.append(asp.fact("companion", name))
    for name in BURROS:
        lines.append(asp.fact("burro", name))
    for obj in OBJECTS:
        lines.append(asp.fact("aeronautic_object", obj))
    for case_id in CASES:
        lines.append(asp.fact("case_name", BURROS[0]))
        lines.append(asp.fact("object_case", OBJECTS[0]))
        break
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_case/4."))
    actual = set(asp.atoms(model, "valid_case"))
    expected = {
        (detective, companion, burro, OBJECTS[0])
        for detective in DETECTIVES
        for companion in COMPANIONS
        for burro in BURROS
        if detective != companion
    }
    if actual == expected:
        print(f"OK: clingo gate matches Python gate ({len(expected)} combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Pip", "Bruno", "blue_ribbon", "weather balloon", 0),
        StoryParams("Mira", "Sana", "Clover", "silver_propeller", "glider", 1),
        StoryParams("Nico", "June", "Dapple", "cloud_map", "cloud map", 2),
        StoryParams("Tess", "Oren", "Pepper", "golden_goggles", "pilot goggles", 3),
    ]


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    index = 0
    while len(samples) < args.n and index < max(50, args.n * 50):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        index += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


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
        print(asp_program("#show valid_case/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_case/4."))
        values = sorted(set(asp.atoms(model, "valid_case")))
        print(f"{len(values)} valid detective combinations.")
        for value in values[:20]:
            print(value)
        return

    samples = (
        [generate(params) for params in curated()]
        if args.all
        else build_story_from_args(args)
    )

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
