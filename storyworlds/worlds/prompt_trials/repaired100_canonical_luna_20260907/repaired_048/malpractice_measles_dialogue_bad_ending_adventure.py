#!/usr/bin/env python3
"""
A small adventure storyworld about careful care, measles, and the danger of
malpractice. The characters use dialogue to discover that a hurried choice has
made things worse, then repair the mistake with help from a trusted clinician.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    setting: str
    child: str
    guide: str
    clinician: str
    animal: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Route:
    obstacle: str
    clue: str
    mistake: str
    danger: str
    remedy: str
    ending: str


ROUTES = [
    Route(
        "a rope bridge swayed above a foggy ravine",
        "a red ribbon tied to the safe railing",
        "the hurried guide cut the wrong rope",
        "the bridge tilted and the group nearly lost its medicine satchel",
        "the clinician secured the bridge and checked every knot before crossing",
        "the satchel reached the warm mountain clinic before sunset",
    ),
    Route(
        "a flooded jungle path blocked the way to the village",
        "fresh boot marks leading toward a raised stone trail",
        "the guide ignored the marks and sent everyone into deeper water",
        "the current tugged at the cart carrying the cooling medicine",
        "the clinician chose the raised trail and wrapped the supplies in dry leaves",
        "the villagers received safe medicine beside a bright cooking fire",
    ),
    Route(
        "a cave passage split into three dark tunnels",
        "a row of painted arrows left by earlier travelers",
        "the guide guessed instead of reading the arrows",
        "the explorers wandered until the medicine box grew warm",
        "the clinician followed the marked tunnel and cooled the box with spring water",
        "the right tunnel opened onto a valley filled with welcoming lanterns",
    ),
    Route(
        "a snowy pass hid the trail under white drifts",
        "small blue flags showing where the ground was firm",
        "the guide rushed across an unmarked slope",
        "the snow gave way and the health kit slid toward a ravine",
        "the clinician anchored a line, retrieved the kit, and followed the flags",
        "the team crossed safely while blue flags fluttered behind them",
    ),
]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(Entity("child", "character", "child", params.child, memes={"worry": 0, "courage": 0}))
    world.add(Entity("guide", "character", "guide", params.guide, memes={"confidence": 1, "care": 0}))
    world.add(Entity("clinician", "character", "clinician", params.clinician, memes={"patience": 1, "relief": 0}))
    world.add(Entity("animal", "character", "animal", params.animal, meters={"strength": 1}))
    world.add(Entity("kit", "thing", "medicine_kit", "measles care kit", meters={"safe": 1, "temperature": 0}))
    world.add(Entity("trail", "thing", "route", params.setting, meters={"known": 1}))
    return world


def tell(world: World) -> None:
    p = world.params
    rng = random.Random(p.seed if p.seed is not None else 7)
    route = rng.choice(ROUTES)
    child = world.entities["child"]
    guide = world.entities["guide"]
    clinician = world.entities["clinician"]
    animal = world.entities["animal"]
    kit = world.entities["kit"]

    child.memes["worry"] = 1
    world.facts.update(route=route, problem="measles", setting=p.setting)

    opening = [
        f"{p.child} traveled with {p.guide}, {p.clinician}, and a sturdy {p.animal} through {p.setting}.",
        f"An adventure began when {p.child} joined {p.guide}, {p.clinician}, and a sturdy {p.animal} on a journey through {p.setting}.",
        f"At the edge of {p.setting}, {p.child} checked the measles care kit before the party moved on.",
    ][rng.randrange(3)]
    print_buffer: list[str] = [opening]
    print_buffer.append(
        f"They were carrying supplies to a village where a child with measles needed careful help, not guesses."
    )
    print_buffer.append(
        f'"We must keep the kit safe and follow the care plan," said {p.clinician}.'
    )
    print_buffer.append(
        f'"I know a faster way," said {p.guide}. "Trust me."'
    )

    world.fired.add("journey_started")
    print_buffer.append(f"Then {route.obstacle} blocked their path.")
    print_buffer.append(f"{p.child} pointed to {route.clue}.")
    print_buffer.append(f'"The clue says we should slow down," {p.child} said.')
    print_buffer.append(
        f'"There is no time for that," replied {p.guide}. "I will decide."'
    )
    world.fired.add("warning_given")

    guide.memes["care"] = 0
    kit.meters["safe"] = 0
    world.fired.add("malpractice")
    print_buffer.append(
        f"The guide made a hurried choice: {route.mistake}. That unsafe act was malpractice because the guide ignored the warning and the agreed care plan."
    )
    print_buffer.append(f"{route.danger}.")
    child.memes["worry"] = 2
    print_buffer.append(
        f'"This is a bad ending if we keep rushing," whispered {p.child}.'
    )
    print_buffer.append(
        f'"Stop," said {p.clinician}. "A frightening mistake can still be faced honestly, but we must not hide it."'
    )
    world.fired.add("bad_ending_avoided")

    clinician.memes["relief"] = 1
    child.memes["courage"] = 1
    kit.meters["safe"] = 1
    kit.meters["temperature"] = 0
    print_buffer.append(f"{p.clinician} took charge carefully. {route.remedy}.")
    print_buffer.append(
        f'"I am sorry," said {p.guide}. "Next time I will listen before acting."'
    )
    print_buffer.append(
        f'"Good," said {p.clinician}. "Safe care begins with honest teamwork."'
    )
    world.fired.add("repair")
    print_buffer.append(f"At last, {route.ending}.")
    print_buffer.append(
        f"{p.child} smiled as the {p.animal} carried the empty satchel home, and the adventure ended with everyone safer and wiser."
    )
    world.facts["story"] = " ".join(print_buffer)
    world.facts["lesson"] = "Careful teamwork and honest correction are safer than hurried guesses."
    world.facts["remedy"] = route.remedy
    world.facts["mistake"] = route.mistake
    world.facts["danger"] = route.danger
    world.facts["ending"] = route.ending


PLACES = {
    "jungle": "a green jungle trail",
    "mountain": "a windy mountain pass",
    "canyon": "a red canyon path",
    "island": "a rocky island trail",
}

CHILDREN = ["Luna", "Mira", "Tavi", "Niko", "Sana"]
GUIDES = ["Pax", "Rafi", "Jo", "Kito", "Bram"]
CLINICIANS = ["Dr. Vale", "Dr. Noor", "Dr. Imani", "Dr. Rowan"]
ANIMALS = ["a sure-footed goat", "a calm donkey", "a clever dog", "a strong pony"]


ASP_RULES = r"""
safe_route :- warning_seen, clinician_listens, kit_safe.
malpractice_seen :- hurried_choice, warning_seen, ignored_warning.
repaired :- malpractice_seen, clinician_listens, kit_safe.
#show safe_route/0.
#show malpractice_seen/0.
#show repaired/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("warning_seen"),
            asp.fact("hurried_choice"),
            asp.fact("ignored_warning"),
            asp.fact("clinician_listens"),
            asp.fact("kit_safe"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about measles, malpractice, and careful dialogue.")
    parser.add_argument("--setting", choices=PLACES)
    parser.add_argument("--child")
    parser.add_argument("--guide")
    parser.add_argument("--clinician")
    parser.add_argument("--animal")
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
        setting=args.setting or rng.choice(list(PLACES)),
        child=args.child or rng.choice(CHILDREN),
        guide=args.guide or rng.choice(GUIDES),
        clinician=args.clinician or rng.choice(CLINICIANS),
        animal=args.animal or rng.choice(ANIMALS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in PLACES:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.child == params.guide:
        raise StoryError("The child and guide need different names so the dialogue stays clear.")
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=str(world.facts["story"]),
        prompts=[
            f"Write an adventure about {params.child} carrying measles care supplies through {PLACES[params.setting]}.",
            f"Include dialogue in which {params.clinician} explains why hurried malpractice is dangerous.",
            "End with a safe repair rather than hiding the mistake.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            f"Why were {p.child} and the others traveling?",
            f"They were carrying careful measles supplies to a village where a child needed help."
        ),
        QAItem(
            "What mistake caused the danger?",
            f"The guide committed malpractice by rushing: {world.facts['mistake']}."
        ),
        QAItem(
            "How did the dialogue change the group's actions?",
            f"{p.child} pointed out the clue, and the clinician listened, stopped the rush, and led the repair."
        ),
        QAItem(
            "How was the bad ending avoided?",
            f"The clinician faced the mistake honestly and then {world.facts['remedy']}."
        ),
        QAItem(
            "What did the group learn?",
            str(world.facts["lesson"]),
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            "What is measles?",
            "Measles is a contagious illness, so people should follow trusted health guidance and help protect others."
        ),
        QAItem(
            "What is malpractice?",
            "Malpractice is unsafe or improper professional action that fails to follow the required standard of care."
        ),
        QAItem(
            "Why is dialogue useful during an emergency?",
            "Clear dialogue lets people share warnings, correct mistakes, and make safer decisions together."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} meters={dict(entity.meters)} memes={dict(entity.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_route/0.\n#show malpractice_seen/0.\n#show repaired/0."))
    names = {symbol.name for symbol in model}
    needed = {"safe_route", "malpractice_seen", "repaired"}
    if not needed.issubset(names):
        print("MISMATCH: ASP did not derive the expected story states.")
        return 1
    sample = generate(
        StoryParams(
            setting="jungle",
            child="Luna",
            guide="Pax",
            clinician="Dr. Vale",
            animal="a calm donkey",
            seed=11,
        )
    )
    required = ["malpractice", "measles", "said", "safe"]
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required narrative evidence.")
        return 1
    print("OK: ASP/Python parity and generated story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_route/0.\n#show malpractice_seen/0.\n#show repaired/0."))
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("jungle", "Luna", "Pax", "Dr. Vale", "a calm donkey", base_seed),
            StoryParams("mountain", "Mira", "Rafi", "Dr. Noor", "a sure-footed goat", base_seed + 1),
            StoryParams("canyon", "Tavi", "Jo", "Dr. Imani", "a clever dog", base_seed + 2),
            StoryParams("island", "Sana", "Kito", "Dr. Rowan", "a strong pony", base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        for index in range(max(1, args.n)):
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
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        print(sample.story)
        if args.trace and sample.world:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
