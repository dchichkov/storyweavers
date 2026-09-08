#!/usr/bin/env python3
"""
A small fable world about a banquet, a proud young baker, and a lesson learned
through transformation.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    child: str
    helper: str
    animal: str
    feast: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    title: str
    banquet_problem: str
    boast: str
    failed_plan: str
    evidence: str
    honest_action: str
    transformation: str
    lesson: str
    ending: str


NAMES = ["Luna", "Mira", "Tessa", "Nora", "Pia", "Cleo"]
HELPERS = ["Grandmother Inez", "Uncle Ren", "Aunt Sol", "Mara the gardener"]
ANIMALS = ["a fox", "a sparrow", "a tortoise", "a little goat"]
FEASTS = ["the harvest banquet", "the moonlit banquet", "the village spring banquet"]

TRIALS = [
    Trial(
        "the crooked cake",
        "the tallest cake leaned toward the mayor's chair",
        "that a grand banquet must have a grand cake, even if it needed no help",
        "piled on another layer and watched the cake lean farther",
        "a loose table leg trembled whenever someone carried a tray past it",
        "asked the guests to step back while the helpers steadied the table and rebuilt the cake",
        "the proud baker became a careful host who noticed the needs beneath the glitter",
        "a feast is held up by care, not by height",
        "the cake stood straight, and every slice was shared from a table that no longer wobbled",
    ),
    Trial(
        "the silent bell",
        "the brass bell meant to call everyone to supper made no sound",
        "that loud wishes alone could wake the bell",
        "struck it harder until its clapper fell into the grass",
        "a small crack showed that the bell's rope had frayed",
        "stopped striking, found the clapper, and asked the village smith to mend the rope",
        "the proud child changed from a commander into a listener",
        "good leaders repair what they use instead of blaming what is broken",
        "when the bell rang at last, it sounded gentle enough for every guest to hear",
    ),
    Trial(
        "the empty table",
        "one long table had no food while the decorated tables overflowed",
        "that the empty table belonged to unimportant guests",
        "carried the best dishes to the nearest tables and ignored the quiet corner",
        "a row of small footprints led from the kitchen to families who had arrived late",
        "carried warm plates to the empty table and invited those families to sit first",
        "the proud host became a generous one who saw every guest",
        "a banquet is truly rich only when nobody is left outside its welcome",
        "the quiet table filled with laughter until it was the liveliest place in the garden",
    ),
    Trial(
        "the painted pears",
        "the shining pears on the dessert plate were hard and flavorless",
        "that beautiful food did not need to be tested",
        "covered the pears with honey and served them without asking",
        "the gardener showed that the pears had been painted for decoration",
        "removed the paint, washed the fruit, and brought fresh pears from the orchard",
        "the proud cook became a truthful one who valued safety over appearance",
        "what looks ready is not always ready to eat",
        "fresh pears glowed on the dessert plate, and their sweet juice needed no paint",
    ),
    Trial(
        "the missing seats",
        "the banquet had more guests than chairs",
        "that latecomers could stand while the important guests sat",
        "kept the finest chairs behind a velvet rope",
        "the helper counted children, elders, and tired workers waiting at the edge",
        "opened the rope, fetched benches, and squeezed the tables into a friendly circle",
        "the proud ruler became a thoughtful neighbor",
        "a welcome is measured by the room made for others",
        "the banquet circle grew wider until even the moon seemed to have a seat",
    ),
]


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    trial = TRIALS[rng.randrange(len(TRIALS))]
    world = World(place="the village orchard beneath lantern trees")

    child = world.add(Entity(params.child, "character", "child", params.child))
    helper = world.add(Entity(params.helper, "character", "helper", params.helper))
    animal = world.add(Entity("animal", "character", "animal", params.animal))
    table = world.add(Entity("banquet_table", "thing", "table", "banquet table"))
    table.meters["stability"] = 0.4
    child.memes["pride"] = 1.0
    helper.memes["patience"] = 1.0
    animal.memes["warning"] = 1.0

    world.say(
        f"In {world.place}, {child.id} prepared {params.feast}. "
        f"{child.id} had polished the plates, folded the napkins, and arranged the banquet "
        f"so grandly that even {animal.label} stopped to stare."
    )
    world.say(
        f"{helper.id} smiled and said, \"A banquet shines brightest when every guest is remembered.\" "
        f"{child.id} replied, \"Do not worry. My splendid plan needs no changing.\""
    )
    world.say(f"Then {trial.banquet_problem}.")
    world.para()

    world.say(f"{child.id} boasted {trial.boast}.")
    world.say(
        f"{child.id} tried to fix matters by {trial.failed_plan}. "
        f"The plan made the trouble worse, and {animal.label} gave a worried little cry."
    )
    world.say(
        f"{helper.id} asked, \"What do you notice if you stop defending the plan?\" "
        f"{child.id} answered, \"I notice that {trial.evidence}.\""
    )
    world.say(
        f"The truth was plain: {trial.evidence}. "
        f"{child.id} took a slow breath and decided that being right mattered less than making things right."
    )
    world.para()

    world.say(f"At last, {child.id} {trial.honest_action}.")
    world.say(
        f"The banquet changed because {child.id} changed first. {trial.transformation.capitalize()}. "
        f"{helper.id} nodded, and {animal.label} settled peacefully beneath the table."
    )
    world.say(
        f"\"I thought a grand host never needed help,\" {child.id} said. "
        f"{helper.id} replied, \"A wise host knows when help can make kindness larger.\""
    )

    child.memes["pride"] = 0.0
    child.memes["humility"] = 1.0
    child.memes["care"] = 1.0
    table.meters["stability"] = 1.0
    world.para()

    world.say(
        f"The guests enjoyed the banquet, and {child.id} learned that {trial.lesson}."
    )
    world.say(f"When the lanterns glowed like small moons, {trial.ending}.")
    world.facts.update(child=child, helper=helper, animal=animal, table=table, trial=trial)
    return world


def generation_prompts(world: World) -> list[str]:
    trial: Trial = world.facts["trial"]
    child: Entity = world.facts["child"]
    return [
        f"Write a fable about {child.id} learning humility during a banquet.",
        f"Tell a transformation story in which {child.id} changes after {trial.banquet_problem}.",
        f"Write a gentle fable showing that {trial.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    trial: Trial = world.facts["trial"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            f"What problem happened at {child.id}'s banquet?",
            f"The problem was that {trial.banquet_problem}.",
        ),
        QAItem(
            f"What did {child.id} believe at first?",
            f"{child.id} believed {trial.boast}.",
        ),
        QAItem(
            "What evidence helped reveal the truth?",
            f"The evidence was that {trial.evidence}.",
        ),
        QAItem(
            f"How did {helper.id} help {child.id}?",
            f"{helper.id} asked {child.id} to stop defending the plan and notice what was really happening.",
        ),
        QAItem(
            "How did the main character transform?",
            f"{trial.transformation.capitalize()} {child.id} learned that {trial.lesson}.",
        ),
        QAItem(
            "What lesson does the fable teach?",
            f"It teaches that {trial.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a banquet?",
            "A banquet is a large, special meal prepared for many people, often to celebrate something.",
        ),
        QAItem(
            "What is a fable?",
            "A fable is a short story that often uses animals or imagined characters to teach a lesson.",
        ),
        QAItem(
            "What does transformation mean in a story?",
            "Transformation means that a character changes in an important way, such as becoming kinder, wiser, or more responsible.",
        ),
        QAItem(
            "Why is listening useful?",
            "Listening helps people notice evidence, understand others, and make better choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
problem_at_banquet :- banquet, unstable_table.
needs_help :- problem_at_banquet, proud_host.
learned_lesson :- needs_help, honest_action.
transformed :- learned_lesson, humble_host.
happy_banquet :- transformed, shared_welcome.

#show problem_at_banquet/0.
#show needs_help/0.
#show learned_lesson/0.
#show transformed/0.
#show happy_banquet/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("banquet"),
            asp.fact("unstable_table"),
            asp.fact("proud_host"),
            asp.fact("honest_action"),
            asp.fact("humble_host"),
            asp.fact("shared_welcome"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transformed/0. #show happy_banquet/0."))
    transformed = bool(asp.atoms(model, "transformed"))
    happy = bool(asp.atoms(model, "happy_banquet"))
    if transformed and happy:
        print("OK: ASP and Python agree that the host transformed and the banquet became happy.")
        return 0
    print("MISMATCH: ASP did not confirm the fable's transformation.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A banquet fable about lesson learned and transformation.")
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--feast", choices=FEASTS)
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
    return StoryParams(
        child=args.child or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        animal=args.animal or rng.choice(ANIMALS),
        feast=args.feast or rng.choice(FEASTS),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.child or not params.helper or not params.animal or not params.feast:
        raise StoryError("A child, helper, animal, and feast are required.")
    world = build_world(params)
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:16} ({entity.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Grandmother Inez", "a fox", "the harvest banquet", 7201),
    StoryParams("Mira", "Uncle Ren", "a tortoise", "the moonlit banquet", 7202),
    StoryParams("Nora", "Aunt Sol", "a sparrow", "the village spring banquet", 7203),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show transformed/0. #show happy_banquet/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program(
                "#show problem_at_banquet/0. "
                "#show needs_help/0. "
                "#show learned_lesson/0. "
                "#show transformed/0. "
                "#show happy_banquet/0."
            )
        )
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
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
