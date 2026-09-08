#!/usr/bin/env python3
"""
A small heartwarming storyworld about Mar, a curious noise-dim, and a surprising
sound that leads to a happy ending.
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
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "hidden": 0.0, "safe": 1.0}
        if not self.memes:
            self.memes = {"suspense": 0.0, "curiosity": 0.0, "happiness": 0.0}


@dataclass
class Setting:
    id: str
    place: str
    affordances: set[str]


@dataclass
class StoryParams:
    setting: str
    hero_type: str
    helper_type: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    sound: str
    clue: str
    discovery: str
    repair: str
    ending: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


SETTINGS = {
    "garden": Setting("garden", "the moonlit garden", {"listen", "search", "repair"}),
    "porch": Setting("porch", "the warm front porch", {"listen", "search", "repair"}),
    "woodland": Setting("woodland", "the quiet woodland path", {"listen", "search", "repair"}),
}

ANIMAL_TYPES = ["rabbit", "fox", "bear", "squirrel", "hedgehog"]

NAMES = {
    "rabbit": ["Mar", "Pip", "Nora"],
    "fox": ["Luna", "Finn", "Tess"],
    "bear": ["Milo", "Bram", "Mara"],
    "squirrel": ["Suki", "Jax", "Nim"],
    "hedgehog": ["Holly", "Pico", "Wren"],
}

INCIDENTS = [
    Incident(
        title="the whispering lantern",
        sound="a tiny hum rose from behind the flower pots",
        clue="a silver thread trembled whenever the breeze touched the old lantern",
        discovery="the hum came from a loose bell hidden inside the lantern",
        repair="tied the bell securely and placed a soft leaf beneath it so it could chime gently",
        ending="the lantern gave one clear, friendly ring, and fireflies gathered around Mar like little stars",
        lesson="Curiosity is safest when we investigate gently and help one another",
    ),
    Incident(
        title="the rattling basket",
        sound="three soft knocks came from a basket near the steps",
        clue="a round acorn rolled whenever the basket tilted",
        discovery="a lost baby bird had tucked the acorn beside a loose wooden bead",
        repair="lifted the basket carefully, returned the acorn, and fastened the bead",
        ending="the basket became quiet, and the baby bird chirped happily from a nearby branch",
        lesson="A careful listener can turn a frightening sound into a kind discovery",
    ),
    Incident(
        title="the singing gate",
        sound="the garden gate made a low, mysterious note",
        clue="a blue ribbon was caught around one of its hinges",
        discovery="the ribbon was rubbing the hinge and making the strange noise",
        repair="freed the ribbon, cleaned the hinge, and tied the ribbon to the gatepost",
        ending="the gate opened with a bright little squeak while everyone walked through together",
        lesson="Small clues can guide a brave heart toward a gentle solution",
    ),
    Incident(
        title="the hidden drum",
        sound="a distant thump echoed under the old bench",
        clue="dust puffed out in a neat circle each time the thump returned",
        discovery="a toy drum had rolled beneath the bench, where a breeze was tapping it",
        repair="pulled the drum out with a long stick and placed it where children could play it safely",
        ending="Mar tapped a cheerful beat, and the mysterious thump became music for the whole evening",
        lesson="Questions become less scary when friends search together",
    ),
]


def _stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(parts)))


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_type not in ANIMAL_TYPES or params.helper_type not in ANIMAL_TYPES:
        raise StoryError("Both characters must be friendly woodland animals.")
    if params.hero_name == params.helper_name:
        raise StoryError("The two characters need different names.")

    setting = SETTINGS[params.setting]
    seed = params.seed if params.seed is not None else _stable_seed(
        params.setting, params.hero_type, params.helper_type,
        params.hero_name, params.helper_name,
    )
    rng = random.Random(seed)
    incident = rng.choice(INCIDENTS)

    world = World(setting)
    mar = world.add(Entity(params.hero_name, "character", params.hero_type))
    helper = world.add(Entity(params.helper_name, "character", params.helper_type))
    noise_dim = world.add(Entity("noise-dim", "thing", "noise-dim", "a small round noise-dim"))
    clue = world.add(Entity("clue", "thing", "clue", incident.clue))

    mar.memes["curiosity"] = 1.0
    helper.memes["happiness"] = 0.5
    noise_dim.meters["hidden"] = 1.0
    noise_dim.meters["safe"] = 1.0

    mar.memes["suspense"] = 1.0
    helper.memes["suspense"] = 1.0

    first = (
        f"Mar, a young {params.hero_type}, was spending a quiet evening in {setting.place} "
        f"with {params.helper_name}, a kind {params.helper_type}. They were listening for "
        f"the gentle sounds of night when {incident.sound}."
    )
    second = (
        f"Mar leaned closer, but did not touch anything. The sound made "
        f"{params.hero_name}'s heart beat quickly. {params.helper_name} noticed {incident.clue}."
    )
    third = (
        f'"Should we run away?" Mar asked. "{params.helper_name} shook their head. '
        f'"We can be curious and careful at the same time. Let us look together."'
    )
    fourth = (
        f"They searched slowly, keeping their paws where everyone could see them. At last, "
        f"they learned that {incident.discovery}. The noise-dim had seemed mysterious, "
        f"but it was only waiting for help."
    )
    fifth = (
        f"Together they {incident.repair}. The suspense softened into relief, and Mar's "
        f"curiosity became a bright smile."
    )
    sixth = (
        f'"You helped me understand the sound," Mar said. "{incident.lesson}," '
        f"{params.helper_name} replied. {incident.ending}."
    )

    for paragraph in (first, second, third, fourth, fifth, sixth):
        world.say(paragraph)

    mar.memes["suspense"] = 0.0
    helper.memes["suspense"] = 0.0
    mar.memes["happiness"] = 1.0
    helper.memes["happiness"] = 1.0
    noise_dim.meters["hidden"] = 0.0
    noise_dim.meters["safe"] = 1.0

    world.facts = {
        "hero": mar,
        "helper": helper,
        "noise_dim": noise_dim,
        "clue": clue,
        "incident": incident,
        "setting": setting,
        "resolved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {hero.id}, a curious animal, and a mysterious noise-dim.",
        f"Tell a suspenseful but gentle story in which {hero.id} and {helper.id} investigate {incident.title}.",
        f"Write a story with curiosity, careful teamwork, dialogue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where were {hero.id} and {helper.id}?",
            f"They were together in {setting.place}, listening carefully to the sounds of evening.",
        ),
        QAItem(
            "What made the moment suspenseful?",
            f"They heard {incident.sound}, and at first they did not know what was causing it.",
        ),
        QAItem(
            "What clue helped them?",
            f"They noticed that {incident.clue}, which gave them a safe place to begin looking.",
        ),
        QAItem(
            "How did the friends solve the mystery?",
            f"They searched slowly and discovered that {incident.discovery}. Then they {incident.repair}.",
        ),
        QAItem(
            "What did Mar learn?",
            f"Mar learned that {incident.lesson.lower()}.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily: {incident.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is suspense?",
            "Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            "What is curiosity?",
            "Curiosity is the wish to learn or find out more about something.",
        ),
        QAItem(
            "Why is it useful to investigate gently?",
            "Gentle investigation helps people learn the truth without hurting themselves, others, or the things around them.",
        ),
        QAItem(
            "What makes an ending happy?",
            "A happy ending shows that a problem has been solved and the characters feel safe, relieved, or joyful.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters}, memes={memes}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
animal(rabbit).
animal(fox).
animal(bear).
animal(squirrel).
animal(hedgehog).

setting(garden).
setting(porch).
setting(woodland).

has_noise_dim.
has_clue.
safe_search :- has_noise_dim, has_clue.
valid_story(S) :- setting(S), safe_search.
happy_ending :- safe_search.
"""


def asp_facts() -> str:
    import asp

    facts = []
    for animal in ANIMAL_TYPES:
        facts.append(asp.fact("animal", animal))
    for setting in SETTINGS:
        facts.append(asp.fact("setting", setting))
    facts.extend([
        asp.fact("has_noise_dim"),
        asp.fact("has_clue"),
    ])
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = {(name,) for name in SETTINGS}
    actual = asp_valid_settings()
    if actual != expected:
        print("MISMATCH between ASP and Python expectations:")
        print("only in ASP:", sorted(actual - expected))
        print("only in Python:", sorted(expected - actual))
        return 1
    for setting in SETTINGS:
        params = StoryParams(setting, "rabbit", "fox", "Mar", "Luna", 9)
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("Generated story failed resolution.")
            return 1
    print(f"OK: ASP gate matches Python expectations ({len(actual)} settings).")
    return 0


CURATED = [
    StoryParams("garden", "rabbit", "fox", "Mar", "Luna"),
    StoryParams("porch", "hedgehog", "bear", "Holly", "Milo"),
    StoryParams("woodland", "squirrel", "rabbit", "Suki", "Pip"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming noise-dim storyworld.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero-type", choices=ANIMAL_TYPES)
    parser.add_argument("--helper-type", choices=ANIMAL_TYPES)
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or rng.choice(ANIMAL_TYPES)
    helper_type = args.helper_type or rng.choice(ANIMAL_TYPES)
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    helper_name = args.helper_name or rng.choice(NAMES[helper_type])
    if hero_name == helper_name:
        choices = [name for name in NAMES[helper_type] if name != hero_name]
        helper_name = rng.choice(choices)
    return StoryParams(setting, hero_type, helper_type, hero_name, helper_name)


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


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1.\n#show happy_ending/0."))
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name}: {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
