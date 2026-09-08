#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    parent = os.path.dirname(_storyworlds_dir)
    if parent == _storyworlds_dir:
        break
    _storyworlds_dir = parent
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = {
    "clocktower_square": "the clocktower square",
    "river_bridge": "the river bridge",
    "school_garden": "the school garden",
    "market_lane": "the market lane",
}

PLACE_DETAILS = {
    "clocktower_square": ("under the old clock", "a bell rope", "the town clock"),
    "river_bridge": ("above the bright river", "a coil of blue rope", "the bridge rail"),
    "school_garden": ("beside the bean rows", "a wooden gate", "the school flag"),
    "market_lane": ("between the market stalls", "a striped awning", "the baker's sign"),
}

NAMES = ["Luna", "Milo", "Pip", "Nora", "Tess", "Owen"]
HELPERS = ["Grandma", "Uncle Sol", "Mina", "Mr. Reed"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)


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
    helper: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Standard:
    id: str
    label: str
    rule: str
    rhyme: str


STANDARDS = {
    "kindness": Standard("kindness", "the kindness standard", "leave room for everyone", "kind"),
    "fairness": Standard("fairness", "the fairness standard", "take turns and share the work", "fair"),
    "care": Standard("care", "the care standard", "check each knot before you climb", "care"),
}


class ConflictModel:
    def __init__(self, world: World) -> None:
        self.world = world
        self.fired: set[str] = set()

    def resolve(self, hero: Entity, helper: Entity, standard: Standard) -> None:
        if "resolution" in self.fired:
            return
        self.fired.add("resolution")
        hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 1.0)
        hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1.0
        helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1.0
        self.world.say(
            f"{hero.label} took a breath and said, \"You are right. The {standard.label} says we must {standard.rule}.\" "
            f"{helper.label} smiled. \"Then we can solve it together, clever feather.\""
        )
        self.world.say(
            f"They changed the plan, made room, and tested each step. The trouble grew smaller because "
            f"{hero.label} chose the {standard.rhyme} way."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming conflict story about a standard.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
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
        place=args.place or rng.choice(list(SETTINGS)),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.name not in NAMES:
        raise StoryError(f"Unknown name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    world = World(SETTINGS[params.place])
    hero = world.add(Entity(params.name, "character", params.name, memes={"pride": 1.0}))
    helper = world.add(Entity("helper", "character", params.helper, memes={"patience": 1.0}))
    standard = rng.choice(list(STANDARDS.values()))
    detail, object_name, landmark = PLACE_DETAILS[params.place]
    challenge = rng.choice([
        "a little parade",
        "a lantern line",
        "a bridge-side show",
        "a garden race",
    ])
    boast = rng.choice([
        "I can lead it all by myself!",
        "No one needs to check my plan!",
        "I know the best way, and I know it fast!",
    ])
    consequence = rng.choice([
        "the flags tangled in a fluttering heap",
        "the lanterns bumped and blinked out",
        "the line stopped with a wobble and a clatter",
    ])

    world.add(Entity("standard", "rule", standard.label))
    world.add(Entity("marker", "thing", object_name, meters={"distance": 3.0}))

    world.say(
        f"In {world.place}, {hero.label} planned {challenge}, with a bright little cheer: "
        f"\"We will make the finest trail from here to {landmark}, and everyone will clap, I fear!\""
    )
    world.say(
        f"At {detail}, {hero.label} held {object_name} high and cried, \"{boast}\" "
        f"{helper.label} answered, \"A good plan needs a standard, so every friend can stand.\""
    )
    world.say(
        f"The standard was simple: {standard.label} meant to {standard.rule}. "
        f"But {hero.label} hurried past the warning, and {consequence}."
    )
    world.para()
    world.say(
        f"The crowd grew quiet. {hero.label} frowned and said, \"If I stop, the whole show will flop!\" "
        f"{helper.label} replied, \"If we listen and mend, this need not be the end.\""
    )

    model = ConflictModel(world)
    model.resolve(hero, helper, standard)

    world.say(
        f"Together they finished the {challenge}. At sunset, {landmark} shone while friends took turns, "
        f"and {hero.label} learned that a standard is not a chain but a path that keeps everyone safe and sane."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        standard=standard,
        detail=detail,
        object_name=object_name,
        landmark=landmark,
        challenge=challenge,
        boast=boast,
        consequence=consequence,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming story about {f['hero'].label} facing a conflict over {f['standard'].label}.",
        f"Tell a child-friendly tale in which a standard changes how {f['hero'].label} solves a problem.",
        "Write a gentle rhyming conflict story with dialogue, a mistake, and a repaired ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    standard = f["standard"]
    return [
        QAItem(
            question=f"What conflict did {hero} face?",
            answer=(
                f"{hero} hurried through the plan for {f['challenge']} and ignored the advice of "
                f"{helper}. As a result, {f['consequence']}. The conflict was solved when {hero} "
                f"followed {standard.label} and agreed to {standard.rule}."
            ),
        ),
        QAItem(
            question=f"What did {standard.label} teach {hero}?",
            answer=(
                f"The {standard.label} taught {hero} to {standard.rule}. Following that rule helped "
                f"{hero} and {helper} change the plan, make room, and finish the {f['challenge']} together."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"{hero} and {helper} repaired the plan by listening and taking turns. At sunset, "
                f"{f['landmark']} shone while everyone joined the finished {f['challenge']}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a standard?",
            answer="A standard is a rule or level that helps people decide how something should be done.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a problem or disagreement between people, plans, or forces.",
        ),
        QAItem(
            question="Why can listening help solve a conflict?",
            answer="Listening helps people understand one another and find a safer or fairer choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
standard(kindness).
standard(fairness).
standard(care).
conflict_present.
resolved_by_standard :- conflict_present, standard(_).
valid_story(P) :- place(P), resolved_by_standard.
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", place) for place in SETTINGS)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    actual = set(asp.atoms(model, "valid_story"))
    expected = {(place,) for place in SETTINGS}
    if actual != expected:
        print("MISMATCH between ASP and Python.")
        print("ASP:", sorted(actual))
        print("PY:", sorted(expected))
        return 1
    for seed in range(5):
        sample = generate(StoryParams("clocktower_square", "Luna", "Grandma", seed))
        if not sample.story or "standard" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP parity matches Python ({len(actual)} places); generated stories pass.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params, random.Random(params.seed))
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
    if trace and sample.world:
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: kind={entity.kind} label={entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place, NAMES[0], HELPERS[0], base_seed)
            samples.append(generate(params))
    else:
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
