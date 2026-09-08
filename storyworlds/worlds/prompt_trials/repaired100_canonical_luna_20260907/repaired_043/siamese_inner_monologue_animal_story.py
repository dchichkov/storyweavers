#!/usr/bin/env python3
"""
A standalone Animal Story world about a Siamese cat using inner thoughts to
understand a small problem and make a kind choice.
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
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            self.meters = {"distance": 0.0, "broken": 0.0, "warmth": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "courage": 0.0, "care": 0.0}


@dataclass
class Setting:
    id: str
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    object_name: str
    problem: str
    clue: str
    first_try: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple[str, str]] = field(default_factory=set)

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


SETTINGS = {
    "garden": Setting("garden", "the sunny garden", False, {"search", "repair"}),
    "porch": Setting("porch", "the quiet porch", True, {"search", "repair"}),
    "greenhouse": Setting("greenhouse", "the warm greenhouse", True, {"search", "repair"}),
}

NAMES = ["Luna", "Milo", "Nina", "Toby", "Cleo", "Pip"]

INCIDENTS = [
    Incident(
        "the bell by the flower bed",
        "a blue bell",
        "a wind gust pulled the bell from its ribbon and hid it beneath broad leaves",
        "a silver thread on the leaves matched the torn ribbon",
        "pawing quickly only pushed the bell farther into the damp soil",
        "lifted the leaves one at a time, dried the bell, and tied it to a fresh ribbon",
        "A quiet look can be braver than a quick guess",
        "The blue bell chimed beside the flowers whenever the gentle wind returned",
    ),
    Incident(
        "the basket for the new kitten",
        "a little sleeping basket",
        "one loose reed made the basket scratchy just when a tiny kitten needed a nap",
        "a thin reed curled away from the basket's round edge",
        "pulling the loose reed made two more reeds bend",
        "asked the older cat for scissors, trimmed the sharp reed, and tucked a soft cloth inside",
        "Careful help begins by noticing what might hurt someone small",
        "The kitten curled into the smooth basket and blinked sleepily at Luna",
    ),
    Incident(
        "the missing garden ribbon",
        "a yellow ribbon",
        "the ribbon for the garden gate slipped away before the animals' welcome party",
        "a yellow fiber caught on a low thorn pointed toward the pond",
        "running from place to place made Luna forget which path she had checked",
        "followed the fibers slowly, found the ribbon near the pond, and tied it to the gate",
        "A steady plan can guide a worried heart",
        "The yellow ribbon waved over the gate as every guest found the party",
    ),
    Incident(
        "the warm window seat",
        "a striped cushion",
        "the cushion slid from the sunny window seat and left a cold gap for an old cat",
        "two small paw marks showed that the cushion had slipped against the loose mat",
        "jumping onto the cushion made it slide again",
        "moved the mat, placed a folded cloth beneath it, and set the cushion firmly on top",
        "When a first solution fails, listening to the evidence helps",
        "The old cat settled on the steady cushion while sunlight warmed her whiskers",
    ),
]


def _stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(parts)))


def object_is_fixed(entity: Entity) -> bool:
    return entity.meters["broken"] == 0.0 and entity.meters["warmth"] >= 1.0


def repair_object(world: World, entity: Entity) -> None:
    if ("repair", entity.id) in world.fired:
        return
    world.fired.add(("repair", entity.id))
    entity.meters["broken"] = 0.0
    entity.meters["warmth"] = 1.0


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    seed = params.seed if params.seed is not None else _stable_seed(
        params.place, params.hero_name, params.helper_name
    )
    rng = random.Random(seed)
    incident = rng.choice(INCIDENTS)
    world = World(setting)

    hero = world.add(Entity(params.hero_name, "character", "siamese"))
    helper = world.add(Entity(params.helper_name, "character", "rabbit"))
    object_entity = world.add(Entity("object", "thing", incident.object_name))

    hero.memes["care"] = 1.0
    hero.memes["worry"] = 1.0
    helper.memes["care"] = 1.0
    object_entity.meters["broken"] = 1.0

    if "repair" not in setting.affords:
        raise StoryError(f"{setting.place} does not have a safe place for this repair.")

    opening = rng.choice([
        f"At {setting.place}, {hero.id}, a Siamese cat with dark ears and bright blue eyes, watched the morning begin.",
        f"The sun reached {setting.place} when {hero.id}, a thoughtful Siamese cat, met {helper.id}.",
        f"{hero.id} the Siamese cat padded across {setting.place} while {helper.id} prepared for {incident.title}.",
    ])
    thought = rng.choice([
        f"Inside, {hero.id} thought, \"I want to help, but I must first understand what happened.\"",
        f"{hero.id} felt worry curl beneath {hero.id}'s chest. \"A careful paw can still find a good answer,\" {hero.id} thought.",
        f"\"I could hurry,\" {hero.id} thought, \"but hurry may hide the clue.\"",
    ])
    dialogue = rng.choice([
        f'"What did you notice?" {helper.id} asked. "{incident.clue}," {hero.id} replied.',
        f'"Should we try again?" asked {hero.id}. "Let us inspect it first," said {helper.id}.',
        f'"I feel worried," {hero.id} admitted. "{incident.clue} gives us a place to begin," {helper.id} answered.',
    ])
    middle_thought = (
        f"{hero.id} paused. The first try had not helped. "
        f"\"The trouble is telling us to slow down,\" {hero.id} thought."
    )

    world.say(opening + f" They were preparing for {incident.title}.")
    world.para()
    world.say(f"Then {incident.problem}. {thought} {dialogue}")
    world.para()
    world.say(f"At first, {incident.first_try}. {middle_thought}")
    world.para()
    world.say(f"Together they {incident.repair}.")
    repair_object(world, object_entity)
    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(
        f'"{incident.lesson}," said {helper.id}. '
        f'{hero.id} smiled because the thought now felt true.'
    )
    world.para()
    world.say(f"As evening came, {incident.ending}.")
    world.facts = {
        "hero": hero,
        "helper": helper,
        "object": object_entity,
        "incident": incident,
        "setting": setting,
        "fixed": object_is_fixed(object_entity),
    }
    return world


def generation_prompts(world: World) -> list[str]:
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write an Animal Story about {hero.id}, a Siamese cat, solving {incident.title} through inner thoughts.",
        f"Tell a gentle story where a Siamese cat notices a clue, speaks with a friend, and repairs a small problem.",
        "Write a child-friendly story showing that pausing to think can lead to a kind and careful choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where were {hero.id} and {helper.id}?",
            f"They were at {setting.place}, preparing for {incident.title}.",
        ),
        QAItem(
            "What problem did they find?",
            f"They found that {incident.problem}.",
        ),
        QAItem(
            "What clue helped them?",
            f"They noticed that {incident.clue}.",
        ),
        QAItem(
            f"What did {hero.id} think before acting?",
            f'{hero.id} thought, "I want to help, but I must first understand what happened." '
            "That thought encouraged a slower, safer choice.",
        ),
        QAItem(
            "How was the problem repaired?",
            f"Together they {incident.repair}.",
        ),
        QAItem(
            "What showed that the repair worked?",
            f"The ending image showed success: {incident.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a Siamese cat?",
            "A Siamese cat is a cat breed often known for a pale coat, darker ears and face, and blue eyes.",
        ),
        QAItem(
            "Why can pausing help when something goes wrong?",
            "Pausing gives someone time to notice clues and choose a safe response instead of making the problem larger.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is a character's private thought, shown as words inside the character's mind.",
        ),
    ]


ASP_RULES = r"""
siamese(cat).
repair_place(garden).
repair_place(porch).
repair_place(greenhouse).
has_helper(cat, friend).
has_problem(object).
has_clue(object).
fixed(object) :- has_problem(object), has_clue(object), has_helper(cat, friend).
valid_story(Place) :- repair_place(Place), fixed(object).
"""


def asp_facts() -> str:
    import asp

    return "\n".join([
        asp.fact("siamese", "cat"),
        asp.fact("repair_place", "garden"),
        asp.fact("repair_place", "porch"),
        asp.fact("repair_place", "greenhouse"),
        asp.fact("has_helper", "cat", "friend"),
        asp.fact("has_problem", "object"),
        asp.fact("has_clue", "object"),
    ])


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> set[tuple[str]]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = {(name,) for name in SETTINGS}
    got = asp_valid_places()
    if got != expected:
        print("MISMATCH between ASP and Python expectations:")
        print("only in ASP:", sorted(got - expected))
        print("only in Python:", sorted(expected - got))
        return 1
    for place in SETTINGS:
        params = StoryParams(place, "Luna", "Milo", 17)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP gate matches Python expectations ({len(got)} places); generated stories pass.")
    return 0


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: type={entity.type}, meters={meters}, memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Siamese Animal Story world.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.hero_name or rng.choice(NAMES)
    helper_choices = [name for name in NAMES if name != hero_name]
    helper_name = args.helper_name or rng.choice(helper_choices)
    if hero_name == helper_name:
        raise StoryError("The Siamese hero and helper must have different names.")
    return StoryParams(place, hero_name, helper_name)


CURATED = [
    StoryParams("garden", "Luna", "Milo"),
    StoryParams("porch", "Cleo", "Pip"),
    StoryParams("greenhouse", "Nina", "Toby"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        places = sorted(asp_valid_places())
        print(f"{len(places)} valid story places:")
        for place in places:
            print(" ", place[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, original in enumerate(CURATED):
            params = StoryParams(
                original.place,
                original.hero_name,
                original.helper_name,
                base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 0)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name}: {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
