#!/usr/bin/env python3
"""A child-friendly superhero story about reggae, caramel, and a cradle."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Place:
    key: str
    name: str
    detail: str


@dataclass(frozen=True)
class Mission:
    key: str
    danger: str
    clue: str
    first_guess: str
    test: str
    reveal: str
    power: str
    safe_plan: str
    setback: str
    ending: str
    lesson: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Milo"
    place: str = "moonlight_square"
    mission: str = "caramel_cradle"
    narrative_mode: int = 0
    dialogue_mode: int = 0
    turn_mode: int = 0


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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


PLACES = {
    "moonlight_square": Place(
        "moonlight_square",
        "Moonlight Square",
        "where lanterns swayed above a little reggae concert",
    ),
    "harbor_stage": Place(
        "harbor_stage",
        "Harbor Stage",
        "where warm drums echoed beside the sleeping boats",
    ),
    "garden_bandstand": Place(
        "garden_bandstand",
        "Garden Bandstand",
        "where bright flowers nodded to a gentle reggae beat",
    ),
}

MISSIONS = {
    "caramel_cradle": Mission(
        "caramel_cradle",
        "a gust is rocking the baby cradle toward a fountain",
        "a sticky caramel ribbon shines across the stones",
        "the caramel came from a candy cart and the cart pushed the cradle",
        "follow the ribbon from a dry distance and compare it with the cart's wheel marks",
        "the ribbon was stretched by a runaway caramel kite, while the cradle had rolled on its own loose wheel",
        "Luna can hear tiny changes in rhythm and use sound to find the loose wheel",
        "ask the grown-up stage keeper to block the fountain while Luna and Milo guide the cradle with a soft safety rope",
        "the wind snaps the caramel kite higher before they can pull it down",
        "the cradle stops safely beneath a striped awning, but the caramel kite sails away",
        "A bright clue can be connected to the wrong cause. Testing an idea helps a hero choose wisely.",
    ),
    "reggae_lantern": Mission(
        "reggae_lantern",
        "a lantern is swinging over the cradle and may fall",
        "a reggae drumbeat makes the lantern tremble at every third beat",
        "the drummer is shaking the lantern on purpose",
        "ask the drummer to pause while Luna watches whether the lantern still moves",
        "the lantern keeps swinging because its cord is caught on a banner hook",
        "Luna's careful listening reveals the repeating pull of the trapped cord",
        "have an adult lower the banner pole while the children stay behind the painted line",
        "a loose ribbon wraps around the pole and delays the rescue",
        "the lantern is lowered safely, and the cradle rests under calm golden light",
        "A pattern can reveal a hidden cause, but safety must come before speed.",
    ),
    "caramel_path": Mission(
        "caramel_path",
        "the baby blanket is sliding toward a hot caramel pot",
        "small caramel dots lead from the cradle to the kitchen tent",
        "someone carried the blanket to the cooks",
        "compare the dots with the blanket's edge and the wind direction",
        "the blanket caught on a breeze, and caramel drops fell from a spoon nearby",
        "Luna's cape can block the breeze without touching the hot equipment",
        "tell the cook to turn off the heat while an adult retrieves the blanket with tongs",
        "the blanket lands beside the tent before the heat is fully off",
        "the cook cools it on a clean table, and the baby sleeps peacefully again",
        "A careful helper protects people and objects instead of grabbing in a hurry.",
    ),
}

OPENINGS = (
    "Luna's silver cape shimmered as the evening reggae music began.",
    "When the first drumbeat rolled across the square, Luna noticed that something was wrong.",
    "The town's young superhero had come to enjoy the music, but trouble arrived with the breeze.",
    "Under strings of lanterns, Luna heard a small cry beneath the cheerful reggae rhythm.",
)

DIALOGUES = (
    '"I hear a pattern, but I do not know its cause yet," Luna said.',
    '"Let us test the clue before we blame anyone," Milo replied.',
    '"A real hero keeps everyone safe while solving the puzzle," said Milo.',
    '"We can be brave and careful at the same time," Luna answered.',
)

TURNS = (
    "Luna's first idea sounded exciting, but the next test changed the whole mission.",
    "The clue did not point to a villain. It pointed to an ordinary problem that needed care.",
    "Once they checked the evidence, the mystery became a rescue plan.",
    "The reggae beat helped Luna notice what hurried eyes had missed.",
)

ASP_RULES = r"""
item(carame l_kite).
item(cradle).
mission(M) :- mission_fact(M).
safe_plan(M) :- mission_fact(M), adult_supervised(M).
lesson(M) :- mission_fact(M), teaches_care(M).
"""

# The predicate above intentionally uses a malformed-looking source token only
# in the rule text? No: keep the ASP twin valid and explicit.
ASP_RULES = r"""
item(caramel_kite).
item(cradle).
mission(M) :- mission_fact(M).
safe_plan(M) :- mission_fact(M), adult_supervised(M).
lesson(M) :- mission_fact(M), teaches_care(M).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("item", "caramel_kite"),
        asp.fact("item", "cradle"),
    ]
    for key in MISSIONS:
        lines.extend(
            [
                asp.fact("mission_fact", key),
                asp.fact("adult_supervised", key),
                asp.fact("teaches_care", key),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero story about reggae, caramel, and a cradle."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--mission", choices=sorted(MISSIONS))
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
        seed=args.seed,
        hero=args.hero or rng.choice(["Luna", "Nova", "Skye"]),
        helper=args.helper or rng.choice(["Milo", "Tariq", "Pia"]),
        place=args.place or rng.choice(list(PLACES)),
        mission=args.mission or rng.choice(list(MISSIONS)),
        narrative_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        turn_mode=rng.randrange(len(TURNS)),
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if not params.hero.strip() or not params.helper.strip():
        raise StoryError("Hero and helper names must not be empty.")

    place = PLACES[params.place]
    mission = MISSIONS[params.mission]
    world = World(place)

    hero = world.add(
        Entity(
            params.hero,
            "hero",
            params.hero,
            meters={"distance_to_cradle": 8.0, "danger": 0.0},
            memes={"courage": 2.0, "care": 1.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "helper",
            params.helper,
            meters={"distance_to_cradle": 7.0},
            memes={"patience": 2.0, "care": 2.0},
        )
    )
    cradle = world.add(
        Entity(
            "cradle",
            "object",
            "the cradle",
            meters={"distance_to_fountain": 3.0},
            memes={"safety": 0.0},
        )
    )
    caramel = world.add(
        Entity(
            "caramel",
            "material",
            "the caramel ribbon",
            meters={"distance_to_cradle": 1.0},
            memes={"clue": 1.0},
        )
    )

    world.say(OPENINGS[params.narrative_mode])
    world.say(
        f"{params.hero} and {params.helper} stood in {place.name}, {place.detail}, "
        "when a baby began to fuss."
    )
    world.say(
        f"Nearby, {mission.danger}. Beside the path, {mission.clue}."
    )
    world.para()

    world.say(f"{params.hero} lifted a hand toward the trouble, but paused.")
    world.say(DIALOGUES[params.dialogue_mode])
    world.say(
        f"At first, {params.hero} guessed that {mission.first_guess}."
    )
    world.say(
        f"Instead of rushing, the friends chose to {mission.test}."
    )
    world.say(f"The check showed that {mission.reveal}.")
    world.say(TURNS[params.turn_mode])
    world.say(
        f"Then {params.hero} used superhero hearing: {mission.power}."
    )

    world.para()
    world.say(f'"Stay behind me and the safety line," {params.hero} told {params.helper}.')
    world.say(f'"I will call the stage keeper," {params.helper} answered.')
    world.say(f"They decided to {mission.safe_plan}.")
    world.say(
        f"The plan worked safely, although {mission.setback}."
    )
    world.say(
        f"In the end, {mission.ending}."
    )
    world.say(
        f"{params.hero} smiled, because the lesson was clear: {mission.lesson}"
    )

    hero.memes["wisdom"] = 2.0
    cradle.memes["safety"] = 2.0
    world.facts.update(
        hero=hero,
        helper=helper,
        cradle=cradle,
        caramel=caramel,
        place=place,
        mission=mission,
        solved=True,
        safe_rescue=True,
        lesson_learned=True,
    )
    world.trace.extend(
        [
            f"music:reggae",
            f"material:caramel",
            f"object:cradle",
            f"clue:{mission.clue}",
            f"test:{mission.test}",
            f"reveal:{mission.reveal}",
            f"safe_plan:{mission.safe_plan}",
            f"lesson:{mission.lesson}",
        ]
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a child-friendly superhero story starring {hero.label} with reggae music, caramel, and a cradle.",
        f"Show {hero.label} solving a small rescue problem by testing the clue: {mission.clue}.",
        f"End with the lesson: {mission.lesson}",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            "What danger did the hero notice?",
            f"{hero.label} noticed that {mission.danger}.",
        ),
        QAItem(
            "What clue did the hero find?",
            f"The clue was that {mission.clue}.",
        ),
        QAItem(
            f"How did {hero.label} avoid a mistaken guess?",
            f"{hero.label} and {helper.label} chose to {mission.test}.",
        ),
        QAItem(
            "What did the test reveal?",
            f"It revealed that {mission.reveal}.",
        ),
        QAItem(
            "How did the heroes keep the rescue safe?",
            f"They decided to {mission.safe_plan}.",
        ),
        QAItem(
            "What lesson did the superhero learn?",
            mission.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should children stay away from a hot caramel pot?",
            "Hot caramel can burn skin badly, so children should stay back and let a grown-up handle the pot.",
        ),
        QAItem(
            "Why is testing a clue useful?",
            "Testing a clue separates what someone observed from what they merely guessed, which helps prevent unfair blame.",
        ),
        QAItem(
            "What makes a superhero rescue responsible?",
            "A responsible rescue protects people first, uses safe tools and barriers, and asks a trained grown-up for help.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {entry}" for entry in world.trace)
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}) meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(mission="caramel_cradle"),
    StoryParams(
        hero="Nova",
        helper="Pia",
        place="harbor_stage",
        mission="reggae_lantern",
        narrative_mode=2,
        dialogue_mode=1,
        turn_mode=3,
    ),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    show = (
        "#show item/1.\n"
        "#show mission/1.\n"
        "#show safe_plan/1.\n"
        "#show lesson/1.\n"
    )
    models = asp.solve(asp_program(show), models=1)
    if not models:
        print("ASP produced no model.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.world.facts["solved"]:
            print("Python reasonableness check failed.")
            return 1

    print("OK: ASP and Python checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    show = (
        "#show item/1.\n"
        "#show mission/1.\n"
        "#show safe_plan/1.\n"
        "#show lesson/1.\n"
    )

    if args.show_asp:
        print(asp_program(show))
        return

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP unavailable: {exc}") from exc
        models = asp.solve(asp_program(show), models=1)
        print(json.dumps([[str(atom) for atom in model] for model in models], indent=2))
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
