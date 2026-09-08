#!/usr/bin/env python3
"""
A small animal story world about a sore toe, a torn fabric nest, and teamwork.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


STORIES = [
    {
        "place": "a willow tree beside the pond",
        "animal": "rabbit",
        "name": "Pip",
        "helper": "Mara the mouse",
        "object": "a soft blue nest lining",
        "problem": "a thorn had pricked Pip's toe while she carried fabric to the nest",
        "method": "Mara gathered smooth leaves while Pip held the torn fabric steady",
        "repair": "they tucked the leaves beneath the fabric and tied it with grass",
        "image": "Pip rested her healed toe on the warm lining as the nest swayed gently",
    },
    {
        "place": "a hollow log near the fern patch",
        "animal": "hedgehog",
        "name": "Hugo",
        "helper": "Tala the squirrel",
        "object": "a red sleeping blanket",
        "problem": "a sharp twig had caught Hugo's toe while he pulled the blanket home",
        "method": "Tala moved the twig aside while Hugo dragged the fabric one careful inch at a time",
        "repair": "they stitched the rip with long grass and covered the twiggy ground with moss",
        "image": "Hugo curled beneath the red blanket while his toe rested safely on moss",
    },
    {
        "place": "a sunny meadow burrow",
        "animal": "field mouse",
        "name": "Nell",
        "helper": "Bram the young badger",
        "object": "a yellow patchwork mat",
        "problem": "Nell's toe snagged on a loose thread as she pulled the fabric through the burrow door",
        "method": "Bram held the mat flat while Nell found the loose thread and wrapped it around a reed",
        "repair": "they trimmed the thread and pressed the mat beneath a row of dry flowers",
        "image": "Nell danced across the yellow mat without bumping her toe",
    },
]


@dataclass
class StoryParams:
    animal_index: int = 0
    route: int = 0
    seed: Optional[int] = None


ASP_RULES = r"""
safe_to_work :- toe_resting, helper_present.
nest_repaired :- safe_to_work, fabric_secured.
teamwork :- helper_present, fabric_secured.
"""


def build_world(params: StoryParams) -> World:
    if not 0 <= params.animal_index < len(STORIES):
        raise StoryError("animal_index must select an available animal story.")
    scene = STORIES[params.animal_index]
    world = World()
    animal = world.add(Entity(
        id="animal",
        kind="character",
        label=scene["name"],
        type=scene["animal"],
        meters={"steps": 0.0, "toe_pain": 1.0},
        memes={"worry": 1.0, "courage": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=scene["helper"],
        type="helper",
        meters={"steps": 0.0},
        memes={"kindness": 1.0, "patience": 1.0},
    ))
    fabric = world.add(Entity(
        id="fabric",
        kind="object",
        label=scene["object"],
        type="fabric",
        meters={"strength": 0.5},
        memes={"comfort": 1.0},
    ))
    world.facts.update(
        scene=scene,
        animal=animal,
        helper=helper,
        fabric=fabric,
        place=scene["place"],
        toe_resting=False,
        helper_present=True,
        fabric_secured=False,
        nest_repaired=False,
        teamwork=False,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    scene = world.facts["scene"]
    animal: Entity = world.facts["animal"]
    helper: Entity = world.facts["helper"]
    fabric: Entity = world.facts["fabric"]

    openings = [
        f"At {scene['place']}, {animal.label} carried {scene['object']} toward a cozy home.",
        f"The morning was bright at {scene['place']} until {animal.label} limped beside a bundle of {scene['object']}.",
        f"{animal.label} had one simple job at {scene['place']}: make a warm place with {scene['object']}.",
    ]
    world.say(openings[params.route % len(openings)])
    world.say(f"Then {scene['problem']}. The bundle fell, and the loose fabric trailed through the grass.")
    world.para()

    animal.memes["worry"] += 1.0
    world.say(f'"I must cease pulling for a moment," {animal.label} thought. "If I hurry, my toe may hurt more."')
    world.say(f'{helper.label} hurried over. "{animal.label}, do you need help?" {helper.label} asked.')
    world.say(f'"Yes," said {animal.label}. "I can hold the fabric, but I cannot manage the sharp place alone."')
    world.say(f'"Then we will work together," said {helper.label}.')
    world.facts["toe_resting"] = True
    animal.meters["toe_pain"] = 0.5
    animal.memes["courage"] += 1.0
    world.para()

    world.say(f"First, {scene['method']}. They stopped whenever {animal.label}'s toe began to ache.")
    fabric.meters["strength"] = 1.0
    world.say(f"The work was slow, but every small task made the {scene['object']} safer.")
    world.facts["fabric_secured"] = True
    world.facts["teamwork"] = True
    world.say(f"At last, {scene['repair']}.")
    world.facts["nest_repaired"] = True
    animal.meters["toe_pain"] = 0.0
    animal.memes["worry"] = 0.0
    animal.memes["relief"] = 1.0
    world.para()

    world.say(f'"My toe feels better because I stopped and asked for help," {animal.label} said.')
    world.say(f'"And the fabric is strong because we shared the work," {helper.label} replied.')
    world.say(f"{scene['image']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        f"Write an animal story at {scene['place']} about a sore toe, torn fabric, and teamwork.",
        f"Tell a gentle story in which {scene['animal']} must cease rushing, think quietly, and accept help.",
        "Write a child-friendly animal story using the words toe, cease, and fabric.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene = f["scene"]
    animal: Entity = f["animal"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What happened to {animal.label}'s toe?",
            answer=f"{scene['problem'].capitalize()}. {animal.label} stopped pulling so the toe could rest.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} helped by {scene['method']}. Sharing the work kept the fabric from tearing further.",
        ),
        QAItem(
            question="Why did the animals cease rushing?",
            answer=f"They ceased rushing because {animal.label}'s toe hurt, and careful teamwork was safer than pulling quickly.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They {scene['repair']}, and {scene['image'].lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or animals share tasks and help one another reach a goal.",
        ),
        QAItem(
            question="What is fabric?",
            answer="Fabric is a material made from woven or knitted fibers that can be used for blankets, clothes, or soft coverings.",
        ),
        QAItem(
            question="Why should someone stop when a toe hurts?",
            answer="Someone should stop so the toe can rest and avoid making the injury worse.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's quiet thought that shows what the character is noticing or deciding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:8} ({entity.type:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("toe_resting"),
        asp.fact("helper_present"),
        asp.fact("fabric_secured"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show safe_to_work/0.\n#show nest_repaired/0.\n#show teamwork/0.")
    model = asp.one_model(program)
    names = {symbol.name for symbol in model}
    expected = {"safe_to_work", "nest_repaired", "teamwork"}
    if expected <= names:
        print("OK: ASP twin matches the repaired teamwork state.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected repaired state.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An animal story about a sore toe, fabric, and teamwork."
    )
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
        animal_index=rng.randrange(len(STORIES)),
        route=rng.randrange(3),
        seed=args.seed,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show safe_to_work/0.\n#show nest_repaired/0.\n#show teamwork/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show safe_to_work/0.\n#show nest_repaired/0.\n#show teamwork/0.")
        )
        print("ASP atoms:", " ".join(sorted(symbol.name for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    count = len(STORIES) if args.all else max(1, args.n)
    samples: list[StorySample] = []

    for index in range(count):
        seed = base_seed + index
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        if args.all:
            params.animal_index = index % len(STORIES)
            params.route = index % 3
        samples.append(generate(params))

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
