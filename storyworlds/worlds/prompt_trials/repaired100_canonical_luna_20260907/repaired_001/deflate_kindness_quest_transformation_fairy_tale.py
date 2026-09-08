#!/usr/bin/env python3
"""
A fairy-tale storyworld about deflate, kindness, a quest, and transformation.

Luna must carry kindness across a windy kingdom to help a proud fairy whose
magic balloon has begun to deflate. The quest succeeds only when Luna shares
her last warm wish instead of keeping it. That kindness transforms the flat
balloon into a moonlit bridge.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = {
    "moonlit_meadow": "the moonlit meadow",
    "rose_valley": "the rose valley",
    "silver_wood": "the silver wood",
    "cloud_hill": "Cloud Hill",
}

PLACE_DETAILS = {
    "moonlit_meadow": ("beside a ring of white stones", "the old wishing well"),
    "rose_valley": ("between the red rose hedges", "the sleeping rose tower"),
    "silver_wood": ("under silver-leaved trees", "the lantern bridge"),
    "cloud_hill": ("above the soft clouds", "the bell-shaped moon"),
}

NAMES = ["Luna", "Mira", "Elin", "Pip", "Nella", "Tavi"]
HELPERS = ["fox", "robin", "hedgehog", "little dragon"]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: str | None = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.id == "hero":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    helper: str
    seed: int | None = None


@dataclass(frozen=True)
class Transformation:
    id: str
    change: str
    ending: str
    gift: str


TRANSFORMATIONS = [
    Transformation(
        "bridge",
        "the flattened balloon unfolded into a shining bridge",
        "a moonlit bridge arched over the dark stream",
        "a bridge for every traveler",
    ),
    Transformation(
        "lantern",
        "the flattened balloon became a golden lantern",
        "a warm lantern floated above the path",
        "a light for every lost creature",
    ),
    Transformation(
        "garden",
        "the flattened balloon opened into a garden of silver flowers",
        "a silver garden bloomed beside the road",
        "a resting place for every tired traveler",
    ),
]

INTRODUCTIONS = [
    "found a silver thread glowing in the grass",
    "heard a tiny bell ringing beneath the moon",
    "saw a blue feather drift upward instead of down",
]


class StoryModel:
    def __init__(self, world: World) -> None:
        self.world = world
        self.fired: set[str] = set()

    def deflate(self, balloon: Entity, fairy: Entity) -> None:
        balloon.meters["fullness"] = 0.0
        balloon.meters["danger"] = 1.0
        balloon.memes["worry"] = 1.0
        fairy.memes["pride"] = 0.0
        self.world.say(
            "But the fairy balloon began to deflate. Its round silver belly sank "
            "until it was no larger than a leaf."
        )

    def transform(self, balloon: Entity, transformation: Transformation) -> None:
        if "transformation" in self.fired:
            return
        self.fired.add("transformation")
        balloon.meters["fullness"] = 1.0
        balloon.meters["danger"] = 0.0
        balloon.memes["wonder"] = 1.0
        balloon.label = transformation.gift
        self.world.say(f"When Luna shared her kindness, {transformation.change}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy tale about deflate, kindness, a quest, and transformation."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name", choices=NAMES)
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
        raise StoryError(f"Unknown hero name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    world = World(SETTINGS[params.place])
    hero = world.add(Entity("hero", "character", params.name, memes={"kindness": 1.0}))
    helper = world.add(Entity("helper", "character", f"the {params.helper}"))
    fairy = world.add(Entity("fairy", "character", "the Cloud Fairy", memes={"pride": 1.0}))
    balloon = world.add(
        Entity(
            "balloon",
            "thing",
            "the fairy's silver balloon",
            meters={"fullness": 1.0, "danger": 0.0},
        )
    )
    charm = world.add(Entity("charm", "thing", "a warm wishing charm"))
    transformation = rng.choice(TRANSFORMATIONS)
    detail, landmark = PLACE_DETAILS[params.place]

    world.say(
        f"Once, in {world.place}, {hero.label} {rng.choice(INTRODUCTIONS)}. "
        f"The trail led {detail}."
    )
    world.say(
        f"At the end of the trail, {hero.label} met {fairy.label}, who guarded "
        "a silver balloon that held the moon's last sparkle."
    )
    world.say(
        f'"Please help me," said the fairy. "If my balloon deflates before moonrise, '
        "the path to the stars will disappear.\""
    )
    world.say(
        f'"I will help you," said {hero.label}. "Kindness should not be kept in a pocket."'
    )
    world.para()

    model = StoryModel(world)
    model.deflate(balloon, fairy)
    world.say(
        f"The fairy gave {hero.label} {charm.label} and sent her on a quest to find "
        "the Warm Wish hidden beyond three cold winds."
    )
    world.say(
        f"{helper.label.capitalize()} hurried beside {hero.label}. At the first wind, "
        f"the {helper.label} shivered, so {hero.label} wrapped the charm around "
        f"{helper.label}'s shoulders instead of using it for herself."
    )
    world.say(
        f'"Then how will you save the balloon?" asked {helper.label}. '
        f'"We will carry kindness together," answered {hero.label}.'
    )
    world.say(
        f"They reached the Warm Wish near {landmark}. It was small enough to hold "
        "in one hand, but it grew bright when shared."
    )
    world.say(
        f"{hero.label} offered the wish to the fairy rather than keeping its warmth."
    )
    model.transform(balloon, transformation)

    world.para()
    world.say(
        f"The fairy smiled, and {transformation.ending}. "
        f"It carried {hero.label}, {helper.label}, and every creature who had been lost."
    )
    world.say(
        f"From that night onward, {transformation.gift} stood in {world.place}. "
        f"{hero.label} remembered that a kindness grows strongest when someone gives it away."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        fairy=fairy,
        balloon=balloon,
        charm=charm,
        transformation=transformation,
        landmark=landmark,
        detail=detail,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write a fairy tale about {hero.label} on a quest to help a deflating magical balloon.",
        "Tell a child-friendly story where kindness causes a surprising transformation.",
        "Write a fairy tale with deflate, kindness, quest, and a hopeful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    transformation = f["transformation"]
    return [
        QAItem(
            question=f"Why did {hero.label} begin the quest?",
            answer=(
                f"{hero.label} began the quest because the Cloud Fairy's silver balloon "
                "was starting to deflate, and the disappearing balloon would make the "
                "path to the stars vanish."
            ),
        ),
        QAItem(
            question=f"How did {hero.label} show kindness to {helper.label}?",
            answer=(
                f"When the cold wind made {helper.label} shiver, {hero.label} gave away "
                "the warm wishing charm instead of saving it for herself. She chose to "
                "help her companion first."
            ),
        ),
        QAItem(
            question="What transformation happened at the end?",
            answer=(
                f"When Luna shared the Warm Wish, {transformation.change}. In the end, "
                f"{transformation.ending}, making {transformation.gift}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does deflate mean?",
            answer="To deflate means to lose air or become smaller and less full.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is caring about someone and choosing to help or comfort them.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey taken to find something, solve a problem, or complete an important task.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one shape, state, or kind of thing into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story QA =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world QA =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
word(deflate).
feature(kindness).
feature(quest).
feature(transformation).
style(fairy_tale).

valid_story(P) :-
    place(P),
    word(deflate),
    feature(kindness),
    feature(quest),
    feature(transformation),
    style(fairy_tale).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("place", place) for place in SETTINGS]
    lines += [
        asp.fact("word", "deflate"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "transformation"),
        asp.fact("style", "fairy_tale"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = {(place,) for place in SETTINGS}
    if found != expected:
        print("MISMATCH between ASP and Python.")
        print("ASP:", sorted(found))
        print("PY:", sorted(expected))
        return 1

    for index, place in enumerate(SETTINGS):
        params = StoryParams(place, NAMES[index % len(NAMES)], HELPERS[index % len(HELPERS)], index)
        sample = generate(params)
        required = ("deflate", "kindness", "quest")
        if not all(word in sample.story.lower() for word in required):
            print("Generated story missed a required narrative word.")
            return 1
        if len(sample.story_qa) != 3:
            print("Generated story has the wrong number of story questions.")
            return 1

    print(f"OK: ASP parity and generated stories verified ({len(expected)} places).")
    return 0


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell(params, rng)
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
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: kind={entity.kind} label={entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print()
        print(format_qa(sample))


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
        for index, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                name=NAMES[index % len(NAMES)],
                helper=HELPERS[index % len(HELPERS)],
                seed=base_seed + index,
            )
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
