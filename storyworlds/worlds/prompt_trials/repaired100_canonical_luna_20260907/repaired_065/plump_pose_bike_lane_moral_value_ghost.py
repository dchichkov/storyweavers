#!/usr/bin/env python3
"""A gentle ghost story about a plump pose, a bike lane, and moral value."""

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


NAMES = ["Luna", "Milo", "Nora", "Toby", "Ivy", "Finn", "Pia", "Owen"]
HELPERS = ["grandma", "grandpa", "auntie", "uncle", "mother", "father"]
BIKE_LANES = [
    "the blue bike lane",
    "the sunny bike lane",
    "the quiet bike lane",
    "the riverside bike lane",
]
OPENINGS = [
    "The evening sky turned lavender above the bike lane.",
    "Streetlights blinked on as the last bicycles rolled home.",
    "A cool wind brushed the painted arrows in the bike lane.",
    "The moon rose over the lane beside the silent park.",
    "Dusk gathered softly around the bright white lane marks.",
]
GHOST_NAMES = ["Misty Mae", "Pip", "Willow", "Bramble", "Echo"]
OBJECTS = ["a silver bell", "a blue scarf", "a paper lantern", "a red ribbon"]
POSES = [
    "a plump little moon shape",
    "a plump owl pose",
    "a plump star pose",
    "a plump teapot pose",
]


@dataclass(frozen=True)
class Encounter:
    key: str
    trouble: str
    clue: str
    request: str
    action: str
    result: str
    lesson: str
    ending: str
    sound: str


ENCOUNTERS = [
    Encounter(
        "bell",
        "A silver bell kept ringing from the middle of the lane, although no bicycle was there.",
        "the bell's shadow pointed toward a bent sign at the curb",
        "Please help me move the fallen sign before a rider comes through.",
        "Luna asked the ghost to wait, then carried the sign to the safe edge while the helper watched the lane.",
        "The bell grew quiet, and the arrows were visible again.",
        "Moral value means choosing what protects other people, even when nobody is watching.",
        "The ghost floated beside the restored sign and finally smiled.",
        "ting-ting",
    ),
    Encounter(
        "scarf",
        "A blue scarf drifted across the lane and wrapped around a bicycle's parked wheel.",
        "the scarf had caught on a low branch, not on a ghostly hand",
        "Please keep the lane clear before someone rides past.",
        "Luna stopped behind the curb, asked the helper to watch for bikes, and used a long branch to loosen the scarf.",
        "The wheel was free, and the scarf fluttered safely from a fence.",
        "Moral value means taking careful action when someone else could be put at risk.",
        "The ghost made a plump pose beside the fence, like a friendly blue balloon.",
        "swish-whoo",
    ),
    Encounter(
        "lantern",
        "A paper lantern hovered low over the lane and made a bright patch that hid the painted arrow.",
        "its string was looped around a signpost",
        "Please uncover the arrow so riders can see where to go.",
        "Luna kept her feet out of the lane, called the helper, and untangled the string from the sidewalk side.",
        "The arrow shone clearly, and the lantern hung above the path.",
        "Moral value means making a fair path for everyone who needs it.",
        "The ghost settled into a plump moon pose beneath the glowing lantern.",
        "flicker-flap",
    ),
    Encounter(
        "ribbon",
        "A red ribbon stretched across the lane like a mysterious line in the dark.",
        "one end was tied to a loose festival basket near the curb",
        "Please stop the ribbon from becoming a trap for a rider.",
        "Luna placed a small warning cone nearby, then asked the helper to untie the basket while she held the ribbon clear.",
        "The lane opened, and the basket rested safely beside the fence.",
        "Moral value means using courage with care instead of rushing into danger.",
        "The ghost bowed in a plump pose, and the ribbon became a bright bow on the basket.",
        "flit-flit",
    ),
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def title(self) -> str:
        return self.label


@dataclass
class Setting:
    place: str = "the bike lane"
    time: str = "evening"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper: str
    ghost_name: str
    encounter_key: str
    pose: str
    object_name: str
    opening_index: int = 0
    dialogue_index: int = 0
    ending_index: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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


DIALOGUE = [
    ("Is someone there?", "Yes," , "said the ghost. \"I am here, but I do not want to frighten anyone.\""),
    ("What do you need?", "I need help," , "the ghost whispered. \"The lane must be safe for riders.\""),
    ("Can you show me the trouble?", "I can," , "said the ghost. \"Please look before you leap.\""),
    ("Will you wait for me?", "I will," , "said the ghost. \"Kindness can be patient.\""),
]


def encounter_for(key: str) -> Encounter:
    for encounter in ENCOUNTERS:
        if encounter.key == key:
            return encounter
    raise StoryError(f"Unknown encounter: {key}")


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", "child", params.hero_name))
    helper = world.add(Entity("helper", "adult", params.helper.capitalize()))
    ghost = world.add(Entity("ghost", "ghost", params.ghost_name))
    prop = world.add(Entity("prop", "object", params.object_name))
    encounter = encounter_for(params.encounter_key)

    hero.memes.update(courage=1.0, kindness=1.0, moral_value=1.0)
    helper.memes.update(guidance=1.0, care=1.0)
    ghost.memes.update(worry=1.0, trust=1.0)
    prop.meters.update(clearance=0.0, visibility=0.5)

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    question, answer_start, answer_end = DIALOGUE[params.dialogue_index % len(DIALOGUE)]
    ending_lead = [
        "When the night grew still,",
        "Before the moon climbed high,",
        "At last, the lane became quiet,",
        "By the time the streetlights glowed warmly,",
    ][params.ending_index % 4]

    world.say(opening)
    world.say(
        f"{hero.title()} walked beside {setting.place}, where bicycles had a clear painted path. "
        f"A {params.object_name} rested near the curb, and the air smelled of rain."
    )
    world.say(
        f"Then a pale ghost named {ghost.title()} appeared in {params.pose}. "
        f"It looked plump and friendly rather than frightening, but {encounter.trouble}"
    )
    world.para()

    world.say(f'"{question}" {hero.title()} asked.')
    world.say(f'{answer_start} {answer_end}')
    world.say(
        f"{hero.title()} did not run or step into the riding path. "
        f"Instead, {hero.title()} listened for the clue: {encounter.clue}."
    )
    world.say(
        f"{helper.title()} called from the sidewalk, \"I can watch the lane while you explain what you found.\""
    )
    world.say(
        f"{hero.title()} answered, \"We will make it safe before we make it spooky.\""
    )
    world.para()

    world.say(encounter.request)
    world.say(encounter.action)
    world.say(encounter.result)
    world.say(f"The ghost explained, \"{encounter.lesson}\"")
    world.say(
        f"{ending_lead} {encounter.ending} "
        f"The little {params.object_name} remained safely by the curb, where it could not surprise a rider."
    )

    prop.meters.update(clearance=1.0, visibility=1.0)
    ghost.memes.update(worry=0.0, trust=1.0, gratitude=1.0)
    hero.memes.update(courage=1.0, kindness=1.0, moral_value=1.0)
    world.fired.update(
        {
            ("trouble", encounter.key),
            ("clue", encounter.key),
            ("safe_action", encounter.key),
            ("moral_value", encounter.key),
        }
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        ghost=ghost,
        prop=prop,
        encounter=encounter,
        params=params,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    encounter: Encounter = world.facts["encounter"]  # type: ignore[assignment]
    return [
        f"Write a gentle ghost story about {params.hero_name} in {params.place}.",
        f"Include a plump pose and let a ghost ask for help because {encounter.trouble.lower()}",
        "Show Moral Value through a safe, kind choice that protects bicycle riders.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    encounter: Encounter = world.facts["encounter"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {params.hero_name} meet {ghost.title()}?",
            answer=f"{params.hero_name} met {ghost.title()} beside {params.place}, where bicycles use a marked path.",
        ),
        QAItem(
            question="Why did the ghost need help?",
            answer=f"The ghost needed help because {encounter.trouble.lower()}",
        ),
        QAItem(
            question="What clue explained the strange event?",
            answer=f"The clue was that {encounter.clue}.",
        ),
        QAItem(
            question=f"How did {params.hero_name} and {helper.title()} keep the lane safe?",
            answer=encounter.action,
        ),
        QAItem(
            question="What Moral Value did the ghost explain?",
            answer=encounter.lesson,
        ),
        QAItem(
            question="What final image showed that the problem was solved?",
            answer=encounter.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a bike lane be kept clear?",
            answer="A bike lane should be kept clear so riders can travel without striking objects or people.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or mysterious presence, often with a feeling of wonder or gentle suspense.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a principle about choosing what is kind, honest, fair, or safe.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.type} {entity.title()} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_lane(H,G,L) :- hero(H), ghost(G), lane(L), clue_seen(L), helper(H).
moral_value(H) :- safe_lane(H,G,L), protects_riders(L).
peace(G) :- moral_value(H), ghost(G).
#show safe_lane/3.
#show moral_value/1.
#show peace/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("ghost", "ghost"),
            asp.fact("helper", "hero"),
            asp.fact("lane", "bike_lane"),
            asp.fact("clue_seen", "bike_lane"),
            asp.fact("protects_riders", "bike_lane"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about Moral Value in a bike lane."
    )
    parser.add_argument("--place", choices=BIKE_LANES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--ghost", choices=GHOST_NAMES)
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
        place=args.place or rng.choice(BIKE_LANES),
        hero_name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        ghost_name=args.ghost or rng.choice(GHOST_NAMES),
        encounter_key=rng.choice([e.key for e in ENCOUNTERS]),
        pose=rng.choice(POSES),
        object_name=rng.choice(OBJECTS),
        opening_index=rng.randrange(len(OPENINGS)),
        dialogue_index=rng.randrange(len(DIALOGUE)),
        ending_index=rng.randrange(4),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(place=params.place), params)
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


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        names = {sym.name for sym in model}
        if not {"safe_lane", "moral_value", "peace"} <= names:
            return 1
    except Exception as exc:
        print(f"ASP verification failed: {exc}", file=sys.stderr)
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "Moral Value" not in sample.story:
            return 1
        if "bike lane" not in sample.story:
            return 1
        if len(sample.story_qa) < 3:
            return 1
    return 0


CURATED = [
    StoryParams(
        place="the blue bike lane",
        hero_name="Luna",
        helper="grandma",
        ghost_name="Misty Mae",
        encounter_key="bell",
        pose="a plump little moon shape",
        object_name="a silver bell",
        opening_index=0,
        dialogue_index=1,
        ending_index=0,
    ),
    StoryParams(
        place="the riverside bike lane",
        hero_name="Nora",
        helper="grandpa",
        ghost_name="Pip",
        encounter_key="scarf",
        pose="a plump owl pose",
        object_name="a blue scarf",
        opening_index=2,
        dialogue_index=0,
        ending_index=2,
    ),
    StoryParams(
        place="the quiet bike lane",
        hero_name="Milo",
        helper="auntie",
        ghost_name="Willow",
        encounter_key="lantern",
        pose="a plump star pose",
        object_name="a paper lantern",
        opening_index=3,
        dialogue_index=2,
        ending_index=1,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
