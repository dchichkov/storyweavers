#!/usr/bin/env python3
"""
A small folk-tale storyworld about Blu, a repeated warning, and a transformation
at the riverbank that ends badly when the warning is ignored.
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: str | None = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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
    seed: int | None = None
    hero: str = "Blu"
    helper: str = "Mara"
    place: str = "the riverbank"
    object_name: str = "the silver reed"
    warning_count: int = 3


HERO_NAMES = ["Blu", "Neri", "Luma", "Pico"]
HELPER_NAMES = ["Mara", "Tavi", "Oren", "Sela"]
OBJECTS = ["the silver reed", "the blue stone", "the willow flute", "the moon bowl"]
PLACES = ["the riverbank", "the reed bank", "the old riverbank"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Folk-tale storyworld about Blu at the riverbank."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", dest="object_name")
    parser.add_argument("--warning-count", type=int, choices=[2, 3, 4])
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
    hero = args.hero or "Blu"
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    place = args.place or rng.choice(PLACES)
    object_name = args.object_name or rng.choice(OBJECTS)
    warning_count = args.warning_count or rng.choice([2, 3, 4])
    if hero.strip().lower() == helper.strip().lower():
        raise StoryError("The hero and helper must have different names.")
    if not hero.strip():
        raise StoryError("The hero name cannot be empty.")
    if not place:
        raise StoryError("The story needs a riverbank setting.")
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        place=place,
        object_name=object_name,
        warning_count=warning_count,
    )


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero,
            meters={"distance_to_water": 2.0, "balance": 1.0},
            memes={"curiosity": 0.8, "pride": 0.3, "fear": 0.0, "regret": 0.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper,
            meters={"distance_to_water": 3.0},
            memes={"care": 0.9, "worry": 0.2},
        )
    )
    relic = world.add(
        Entity(
            "relic",
            "relic",
            params.object_name,
            owner="river",
            meters={"magic": 1.0, "dryness": 1.0, "danger": 0.2},
            memes={"patience": 1.0},
        )
    )
    river = world.add(
        Entity(
            "river",
            "place",
            "the dark river",
            meters={"current": 0.9, "depth": 1.0},
            memes={"anger": 0.0},
        )
    )
    world.facts.update(hero=hero, helper=helper, relic=relic, river=river)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    relic = world.get("relic")
    river = world.get("river")

    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in params.hero + params.helper + params.object_name)
    rng = random.Random(seed ^ 0xB10)

    warnings = [
        f'"Do not lift {relic.label} three times," {helper.label} warned. "The river changes what greedy hands hold."',
        f'"Leave {relic.label} where the reeds keep it," {helper.label} said. "Some gifts are warnings in disguise."',
        f'"Blu, listen to the river," {helper.label} pleaded. "Its quiet voice is still a voice."',
    ]
    transformations = [
        "Blu's fingers turned green like wet willow leaves, and their feet stiffened into roots.",
        "Blu's coat became slick river scales, and a cold fin rose along their back.",
        "Blu's hands changed into thin reeds, waving helplessly whenever the current breathed.",
    ]
    endings = [
        "The river carried Blu past the bend, while the silver reed lay bright and untouched on the bank.",
        "By sunset, only Blu's blue scarf remained snagged in the reeds, and no one heard Blu answer again.",
        "The current swallowed Blu's footsteps, leaving the riverbank quiet beneath a hard gray sky.",
    ]

    relic.meters["danger"] = 0.8
    hero.memes["curiosity"] += 0.5
    world.facts.update(
        warning_count=params.warning_count,
        warning=warnings[rng.randrange(len(warnings))],
        transformation=transformations[rng.randrange(len(transformations))],
        bad_ending=endings[rng.randrange(len(endings))],
        repeated_warning="Do not touch it again.",
        outcome="Blu ignored the repeated warning and was transformed by the river.",
        lesson="A warning repeated is not a warning made smaller.",
        place=params.place,
        hero_name=hero.label,
        helper_name=helper.label,
        relic_name=relic.label,
    )

    world.say(
        f"Long ago, at {params.place}, {hero.label} found {relic.label} shining between the reeds."
    )
    world.say(
        f"The river was swift that morning, and the old people of the bank said the relic belonged to the river itself."
    )
    world.para()

    world.say(world.facts["warning"])
    world.say(
        f"{hero.label} nodded, but curiosity pulled harder than wisdom. "
        f'"It is only a little treasure," {hero.label} said.'
    )
    world.say(f"{hero.label} touched {relic.label}. The current gave one deep boom.")
    world.para()

    for number in range(params.warning_count):
        if number == 0:
            world.say(f'"Do not touch it again," {helper.label} said.')
        elif number == 1:
            world.say(
                f'"Do not touch it again," {helper.label} repeated, stepping away from the water.'
            )
        else:
            world.say(
                f'"Do not touch it again," {helper.label} cried for the {number + 1}th time.'
            )
        world.say(
            f"{hero.label} reached for {relic.label} once more, believing repetition had made the words harmless."
        )

    hero.memes["pride"] += 0.8
    river.memes["anger"] = 1.0
    relic.meters["danger"] = 1.0
    relic.meters["dryness"] = 0.0
    world.say(
        f"{hero.label} lifted {relic.label} above their head and laughed at the dark water."
    )
    world.say("The river rose without rain.")
    world.para()

    world.say(world.facts["transformation"])
    world.say(
        f'"Blu!" {helper.label} shouted. "Let go and come back!" '
        f'"I cannot," {hero.label} answered, as the river pulled at the bank.'
    )
    world.say(
        f"{helper.label} threw a rope, but {hero.label}'s changed hands could not hold it."
    )
    world.say(world.facts["bad_ending"])
    world.say(
        f"The river took {relic.label} back, but it did not give {hero.label} back."
    )

    hero.meters["distance_to_water"] = 0.0
    hero.meters["balance"] = 0.0
    hero.memes["regret"] = 1.0
    relic.meters["danger"] = 0.0
    relic.owner = "river"
    world.facts["bad_end"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a Folk Tale about {facts['hero_name']} at {facts['place']} who ignores a repeated warning about {facts['relic_name']}.",
        f"Tell a folk tale in which blu appears as {facts['hero_name']}, a transformation follows repeated disobedience, and the ending is bad.",
        f"Write a child-facing riverbank tale using Bad Ending, Repetition, and Transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question=f"What did {facts['hero_name']} find at the riverbank?",
            answer=f"{facts['hero_name']} found {facts['relic_name']} shining between the reeds at {facts['place']}.",
        ),
        QAItem(
            question=f"What warning did {facts['helper_name']} repeat?",
            answer=f"{facts['helper_name']} repeatedly warned, \"{facts['repeated_warning']}\"",
        ),
        QAItem(
            question=f"What transformation happened to {facts['hero_name']}?",
            answer=f"{facts['transformation']}",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because {facts['hero_name']} ignored the repeated warning, was transformed, and was carried away by the river.",
        ),
        QAItem(
            question="What lesson does the tale give?",
            answer=facts["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land along the edge of a river.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or condition into another.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a traditional-style story often shared to entertain and teach a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: round(value, 3) for key, value in entity.meters.items()}
        memes = {key: round(value, 3) for key, value in entity.memes.items()}
        lines.append(
            f"  {entity.id}: {entity.label}; meters={meters}; memes={memes}; owner={entity.owner}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
dangerous_relic(R) :- relic(R), touched(R), river_angry.
transformed(H) :- hero(H), touched(R), river_angry.
bad_end(H) :- transformed(H), swept_away(H).
warning_ignored(H) :- hero(H), warning_repeated, touched(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("hero", "blu"),
            asp.fact("relic", "relic"),
            asp.fact("touched", "relic"),
            asp.fact("river_angry"),
            asp.fact("warning_repeated"),
            asp.fact("swept_away", "blu"),
        ]
    )


def asp_program(show: str = "#show dangerous_relic/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program(
            "#show dangerous_relic/1. #show transformed/1. #show bad_end/1. #show warning_ignored/1."
        )
    )
    names = {(symbol.name, tuple(str(arg) for arg in symbol.arguments)) for symbol in model}
    expected = {
        ("dangerous_relic", ("relic",)),
        ("transformed", ("blu",)),
        ("bad_end", ("blu",)),
        ("warning_ignored", ("blu",)),
    }
    if names != expected:
        print("MISMATCH between ASP and Python assumptions.")
        print("got:", sorted(names))
        print("expected:", sorted(expected))
        return 1

    sample = generate(StoryParams(seed=17))
    required = ["Blu", "riverbank", "again", "river", "warning"]
    if not all(word.lower() in sample.story.lower() for word in required):
        print("MISMATCH: generated story omitted required narrative facts.")
        return 1
    if not sample.world.facts.get("bad_end"):
        print("MISMATCH: generated story did not reach its bad ending.")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


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
    StoryParams(seed=11, hero="Blu", helper="Mara", place="the riverbank", object_name="the silver reed", warning_count=3),
    StoryParams(seed=22, hero="Blu", helper="Tavi", place="the reed bank", object_name="the blue stone", warning_count=2),
    StoryParams(seed=33, hero="Blu", helper="Sela", place="the old riverbank", object_name="the willow flute", warning_count=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show dangerous_relic/1. #show transformed/1. #show bad_end/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show dangerous_relic/1. #show transformed/1. #show bad_end/1. #show warning_ignored/1."
            )
        )
        print("ASP atoms:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
