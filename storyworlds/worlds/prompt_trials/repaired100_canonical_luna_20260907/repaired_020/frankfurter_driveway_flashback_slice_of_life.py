#!/usr/bin/env python3
"""
A small driveway slice-of-life world about a frankfurter, a remembered afternoon,
and the quiet repair of an old family habit.
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


@dataclass
class Place:
    name: str = "the driveway"
    grill_safe: bool = True


@dataclass
class StoryParams:
    place: str = "driveway"
    hero: str = "Luna"
    helper: str = "Milo"
    elder: str = "June"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
class Arc:
    ordinary: str
    object_detail: str
    small_problem: str
    memory: str
    remembered_lesson: str
    action: str
    ending: str


ARCS = [
    Arc(
        "Luna chalked a hopscotch path beside the parked bicycles",
        "a paper plate with one frankfurter waiting near the folding table",
        "the frankfurter rolled beneath the old blue car",
        "her grandfather once turned every driveway supper into a tiny parade",
        "food tasted better when nobody had to eat alone",
        "Luna knelt with a broom while Milo held a flashlight under the car",
        "the rescued frankfurter rested in a bun while the chalk parade led everyone back to the table",
    ),
    Arc(
        "Luna sorted bottle caps into bright little circles",
        "a grilled frankfurter balanced on a bun beside the lemonade pitcher",
        "a gust of wind carried the napkin and frankfurter toward the gate",
        "her mother used to chase napkins down this same driveway on warm evenings",
        "a meal could become a memory when people laughed together",
        "June pinned the tablecloth while Luna caught the plate and Milo closed the gate",
        "the frankfurter sat safely beneath a napkin as the driveway filled with familiar laughter",
    ),
    Arc(
        "Luna washed dusty plant pots near the garage",
        "one frankfurter cooling on a small red plate",
        "the grill's side shelf sagged and tipped the plate toward the pavement",
        "June remembered fixing that shelf with a folded spoon years before",
        "small repairs were worth doing before they became big troubles",
        "Luna moved the food away, and Milo steadied the shelf while June found a wooden shim",
        "the frankfurter rested on a level table beside the newly mended grill shelf",
    ),
    Arc(
        "Luna practiced skipping a yellow rope between two chalk stars",
        "a frankfurter wrapped in foil for someone arriving late",
        "the driveway gate squeaked open and bumped the serving table",
        "Luna remembered being small enough to hide behind that gate during family picnics",
        "a place felt safe when people noticed what might hurt someone",
        "Milo held the gate while Luna moved the table and June tied the hinge with a bright ribbon",
        "the ribbon fluttered on the quiet gate while the warm frankfurter waited for its late eater",
    ),
]


def tell_story(params: StoryParams) -> World:
    if params.place != "driveway":
        raise StoryError("This storyworld only supports the driveway setting.")
    if params.hero == params.helper or params.hero == params.elder or params.helper == params.elder:
        raise StoryError("The three driveway characters must have different names.")

    world = World(Place())
    hero = world.add(Entity(params.hero, "character", "girl", params.hero))
    helper = world.add(Entity(params.helper, "character", "boy", params.helper))
    elder = world.add(Entity(params.elder, "character", "woman", params.elder))
    frankfurter = world.add(Entity("frankfurter", "food", "frankfurter", "frankfurter"))

    hero.meters["attention"] = 1.0
    helper.meters["helpfulness"] = 1.0
    elder.memes["memory"] = 1.0
    frankfurter.meters["warmth"] = 0.8

    index = (params.seed or 0) % len(ARCS)
    arc = ARCS[index]

    world.say(
        f"{hero.label} spent the afternoon in the driveway, {arc.ordinary}. "
        f"{helper.label} carried cups from the kitchen, and {elder.label} watched the grill."
    )
    world.say(
        f"Near the folding table sat {arc.object_detail}. The air smelled of toasted buns, "
        "warm pavement, and the faint green scent of cut grass."
    )
    world.facts["ordinary"] = arc.ordinary
    world.facts["object_detail"] = arc.object_detail
    world.para()

    world.say(
        f"Just as {hero.label} reached for a napkin, {arc.small_problem.capitalize()}. "
        "Everyone paused, because a small supper could still become a messy one."
    )
    hero.memes["worry"] = 1.0
    helper.memes["attention"] = 1.0
    world.facts["problem"] = arc.small_problem

    world.say(
        f"The sight pulled {hero.label} into a flashback. {arc.memory.capitalize()}. "
        f"In that old afternoon, {elder.label} had smiled and said, "
        f"\"{arc.remembered_lesson.capitalize()}\""
    )
    world.facts["flashback"] = arc.memory
    world.facts["lesson"] = arc.remembered_lesson
    world.para()

    world.say(
        f"{hero.label} told {helper.label}, \"Let's fix it before supper gets away.\" "
        f"{helper.label} answered, \"I can hold the light.\" {elder.label} added, "
        "\"Then I will help with the careful part.\""
    )
    world.say(f"Together, they {arc.action}.")
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    helper.memes["pride"] = 1.0
    elder.memes["warmth"] = 1.0
    frankfurter.meters["safety"] = 1.0
    world.facts["repaired"] = True

    world.say(
        f"{hero.label} looked at the frankfurter and remembered the old lesson: "
        f"{arc.remembered_lesson.capitalize()}. So the three of them made room at the table "
        "instead of hurrying through the meal."
    )
    world.para()
    world.say(
        f"At sunset, {arc.ending}. {hero.label} drew one last chalk star on the driveway, "
        "and the evening felt ordinary in the best possible way."
    )
    world.facts["ending"] = arc.ending
    world.facts["arc"] = index
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["elder"] = elder
    world.facts["frankfurter"] = frankfurter
    return world


NAMES = ["Luna", "Nora", "Maya", "Ivy", "Tessa"]
HELPERS = ["Milo", "Theo", "Ben", "Owen", "Sam"]
ELDERS = ["June", "Ruth", "Aunt Bea", "Nana Rose"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle slice-of-life story in a driveway involving a frankfurter and a flashback.",
        f"Tell a story about {f['hero'].label} solving this driveway problem: {f['problem']}.",
        f"Write a warm family story where a memory teaches that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    elder = f["elder"]
    return [
        QAItem(
            question=f"What was {hero.label} doing in the driveway before the problem?",
            answer=f"{hero.label} was {f['ordinary']}. {helper.label} carried cups while {elder.label} watched the grill.",
        ),
        QAItem(
            question="What food was part of the driveway supper?",
            answer=f"There was {f['object_detail']}.",
        ),
        QAItem(
            question="What small problem interrupted supper?",
            answer=f"{f['problem'].capitalize()}.",
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=f"{hero.label} remembered that {f['flashback']}. The memory taught that {f['lesson']}.",
        ),
        QAItem(
            question="How did the family solve the problem?",
            answer=f"They worked together: {f['action'].capitalize()}.",
        ),
        QAItem(
            question="What showed that the evening ended happily?",
            answer=f"{f['ending'].capitalize()} Then {hero.label} drew one last chalk star on the driveway.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frankfurter?",
            answer="A frankfurter is a sausage often served warm inside a bun.",
        ),
        QAItem(
            question="What is a driveway?",
            answer="A driveway is a paved or packed path beside a home where cars can travel or park.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when a story briefly returns to something that happened earlier.",
        ),
    ]


ASP_RULES = r"""
safe_food :- repaired.
memory_guides_action :- flashback, lesson_present.
shared_meal :- safe_food, memory_guides_action.
#show shared_meal/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("driveway"),
            asp.fact("frankfurter_present"),
            asp.fact("flashback"),
            asp.fact("lesson_present"),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str = "#show shared_meal/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "shared_meal")))


def asp_verify() -> int:
    expected = [()]
    actual = asp_outcome()
    if actual == expected:
        print("OK: ASP and Python agree that the repaired meal is shared.")
        return 0
    print(f"MISMATCH: python=shared_meal asp={actual}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A driveway slice-of-life story about a frankfurter and a flashback."
    )
    parser.add_argument("--place", choices=["driveway"])
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--elder", choices=ELDERS)
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
    hero = args.hero or rng.choice(NAMES)
    helper_choices = [x for x in HELPERS if x != hero]
    helper = args.helper or rng.choice(helper_choices)
    elder_choices = [x for x in ELDERS if x not in {hero, helper}]
    elder = args.elder or rng.choice(elder_choices)
    return StoryParams(
        place=args.place or "driveway",
        hero=hero,
        helper=helper,
        elder=elder,
        seed=args.seed,
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
        lines.append(
            f"  {entity.id:12} ({entity.kind:9}) meters={meters} memes={memes}"
        )
    facts = {
        key: value.id if isinstance(value, Entity) else value
        for key, value in world.facts.items()
    }
    lines.append(f"  facts: {facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(ARCS)):
            params = StoryParams(
                place="driveway",
                hero="Luna",
                helper="Milo",
                elder="June",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(args.n * 20, 20)
        while len(samples) < args.n and index < limit:
            seed = base_seed + index
            index += 1
            local_args = argparse.Namespace(
                place=args.place,
                hero=args.hero,
                helper=args.helper,
                elder=args.elder,
            )
            params = resolve_params(local_args, random.Random(seed))
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
