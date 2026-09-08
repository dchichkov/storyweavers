#!/usr/bin/env python3
"""
A small mystery storyworld about bravery, a beehive, and a missing hum.
"""

from __future__ import annotations

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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("distance", "sound", "visibility", "clue"):
            self.meters.setdefault(key, 0.0)
        for key in ("bravery", "worry", "curiosity", "trust", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
    name: str
    animal: str
    helper: str
    mystery: str
    seed: Optional[int] = None
    telling: int = 0


NAMES = ["Luna", "Mira", "Nell", "Pip", "Sora", "Tavi"]
ANIMALS = ["rabbit", "fox", "mouse", "badger", "squirrel"]
HELPERS = ["Grandma Bee", "Aunt Juniper", "Old Finch", "Mama Wren"]
MYSTERIES = ["missing_hum", "silver_lid", "vanishing_pollen", "night_light"]

CASES = {
    "missing_hum": {
        "place": "the clover garden",
        "premise": "Every morning the beehive sang a warm, busy hum, but today the hive was strangely quiet",
        "question": "Why had the beehive gone silent?",
        "clue1": "a trail of tiny wax flakes leading from the hive to the old stone wall",
        "clue2": "a loose reed caught in the wall, trembling whenever the wind passed",
        "truth": "the reed had slipped against the hive entrance and made a buzzing sound that frightened the bees into a quiet corner",
        "action": "used a long twig to move the reed from a safe distance",
        "resolution": "the bees returned to the entrance and their gentle hum filled the garden again",
        "ending": "Luna listened beside the flowers as the beehive hummed like a tiny golden drum",
    },
    "silver_lid": {
        "place": "the orchard path",
        "premise": "A silver lid that covered the beehive's rain shelter disappeared before a storm",
        "question": "Who had taken the lid, and why?",
        "clue1": "round dents in the soft earth beside the hive",
        "clue2": "a bright scratch on the low branch of an apple tree",
        "truth": "a curious raccoon had carried the lid toward the tree, hoping its shine was a moon",
        "action": "asked the helper to stand nearby while gently calling the raccoon toward a basket of apples",
        "resolution": "the raccoon dropped the lid, and the rain shelter was put back before the clouds opened",
        "ending": "Rain tapped the silver lid while the bees stayed dry and Luna felt brave enough to smile",
    },
    "vanishing_pollen": {
        "place": "the school garden",
        "premise": "The yellow pollen baskets near the beehive were empty, even though the flowers were bright",
        "question": "Where had the pollen gone?",
        "clue1": "yellow dust sprinkled across a narrow boardwalk",
        "clue2": "a torn leaf tucked under the garden cart",
        "truth": "the cart wheel had brushed the flowers, shaking pollen onto the boardwalk instead of letting bees gather it",
        "action": "asked the gardener to move the cart and placed small flower markers around the hive",
        "resolution": "the bees found the flowers again and soon carried golden pollen home",
        "ending": "By sunset, the beehive glowed with new stores, and Luna's brave question had helped the whole garden",
    },
    "night_light": {
        "place": "the moonlit meadow",
        "premise": "A little light blinked inside the beehive after sunset",
        "question": "Was something trapped in the hive?",
        "clue1": "the light blinked only when moths fluttered near the roof",
        "clue2": "a thread of spider silk stretched between two tall grasses",
        "truth": "a firefly was caught in the silk above the hive, and its blinking reflection looked as if it came from inside",
        "action": "stood with the helper, freed the firefly from the grass, and watched from a respectful distance",
        "resolution": "the blinking stopped, and the bees rested safely through the night",
        "ending": "The firefly rose like a small star while the quiet beehive slept beneath the moon",
    },
}

OPENINGS = [
    "{name} the {animal} loved questions, especially questions that began with a strange sound.",
    "Luna's favorite place was near the garden, where every answer seemed to hide beneath a leaf.",
    "On the morning of the mystery, {name} was carrying a notebook when the beehive gave no greeting at all.",
    "Everyone said {name} was curious, but bravery was needed for the question waiting beside the hive.",
]


def _case(params: StoryParams) -> dict[str, str]:
    if params.mystery not in CASES:
        raise StoryError(f"Unknown beehive mystery: {params.mystery}")
    return CASES[params.mystery]


def reasonableness(params: StoryParams) -> None:
    case = _case(params)
    if not params.name.strip():
        raise StoryError("A beehive mystery needs a named investigator.")
    if not params.animal.strip():
        raise StoryError("The investigator needs a kind of animal.")
    if not case["clue1"] or not case["truth"]:
        raise StoryError("The mystery must have a concrete clue and explanation.")


def tell(params: StoryParams) -> World:
    reasonableness(params)
    case = _case(params)
    world = World(Setting(case["place"], {"observe", "ask", "solve"}))
    hero = world.add(Entity("hero", "character", params.animal, params.name, location=case["place"]))
    helper = world.add(Entity("helper", "character", "helper", params.helper, location=case["place"]))
    hive = world.add(Entity("beehive", "thing", "beehive", "the beehive", location=case["place"]))
    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 1.0
    hero.memes["bravery"] = 0.0
    hive.meters["sound"] = 0.0

    rng = random.Random((params.seed or 0) ^ 0xBEA51VE)
    opening = OPENINGS[params.telling % len(OPENINGS)].format(
        name=params.name, animal=params.animal
    )

    world.say(opening)
    world.say(f"At {case['place']}, {case['premise']}.")
    world.say(f"{params.name} looked at {hive.label} and asked, \"{case['question']}\".")
    world.say(f'"Stay on the path while we investigate," said {params.helper}.')
    world.say(f'"I can be careful and still be brave," {params.name} replied.')

    world.para()
    world.say(f"The first clue was {case['clue1']}.")
    world.say(f"{params.name} followed it only with their eyes, because the bees needed quiet.")
    world.say(f"Then {params.helper} pointed to {case['clue2']}.")
    world.say(f'"That detail changes the mystery," said {params.helper}.')
    world.say(f'"Then I know where to look next," said {params.name}.')

    hero.memes["bravery"] += 1.0
    hero.memes["worry"] = 0.0
    hero.meters["clue"] += 2.0
    world.para()
    world.say(f"The clues showed that {case['truth']}.")
    world.say(f"{params.name} {case['action']}.")
    world.say(f"No one touched the beehive, and no bee was harmed.")
    world.say(f"At once, {case['resolution']}.")

    hero.memes["trust"] = 1.0
    hero.memes["relief"] = 1.0
    hive.meters["sound"] = 1.0
    world.say(f"The mystery was solved: {case['truth'].capitalize()}.")
    world.say(case["ending"] + ".")

    world.facts.update(
        hero=hero,
        helper=helper,
        hive=hive,
        case_id=params.mystery,
        place=case["place"],
        premise=case["premise"],
        question=case["question"],
        clue1=case["clue1"],
        clue2=case["clue2"],
        truth=case["truth"],
        action=case["action"],
        resolution=case["resolution"],
        ending=case["ending"],
        brave=True,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a child-friendly mystery about {hero.label}, a brave {hero.type}, investigating a beehive at {f['place']}.",
        f"Include the clue that {f['clue1']} and explain how it helps solve the mystery.",
        f"End with this changed image: {f['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        QAItem("Who investigated the beehive mystery?", f"{hero.label}, a brave little {hero.type}, investigated the beehive mystery."),
        QAItem("What was the mystery?", f"The mystery was this: {f['question']}"),
        QAItem("What clues helped?", f"The clues were {f['clue1']} and {f['clue2']}."),
        QAItem("How was the mystery solved?", f"{hero.label} learned that {f['truth']} Then {hero.label} {f['action']}."),
        QAItem("How did bravery help?", f"{hero.label} stayed careful, asked questions, followed evidence, and acted bravely without touching the beehive."),
        QAItem("What ending proves the problem changed?", f"{f['ending']}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a beehive?", "A beehive is a home where honeybees live, raise young bees, and store honey and pollen."),
        QAItem("Why should people watch bees from a safe distance?", "Watching from a safe distance protects both people and bees from being startled."),
        QAItem("What is bravery?", "Bravery means doing a careful, helpful thing even when you feel worried."),
        QAItem("What is a mystery clue?", "A mystery clue is a detail that helps someone discover what happened."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: location={entity.location!r} meters={meters} memes={memes}")
    lines.append(f"  facts: solved={world.facts.get('solved')} brave={world.facts.get('brave')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("domain", "beehive"),
        asp.fact("hero", "investigator"),
        asp.fact("feature", "bravery"),
        asp.fact("has_clue", "investigator", "evidence"),
        asp.fact("safe_action", "investigator", "observe"),
        asp.fact("solves", "evidence", "beehive_mystery"),
    ])


ASP_RULES = r"""
investigates(investigator, beehive_mystery) :- hero(investigator), domain(beehive).
brave(investigator) :- hero(investigator), feature(bravery), safe_action(investigator, observe).
solved(beehive_mystery) :- investigates(investigator, beehive_mystery), has_clue(investigator, evidence), solves(evidence, beehive_mystery).
valid(beehive_mystery) :- brave(investigator), solved(beehive_mystery).
#show brave/1.
#show solved/1.
#show valid/1.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    brave = set(asp.atoms(model, "brave"))
    solved = set(asp.atoms(model, "solved"))
    valid = set(asp.atoms(model, "valid"))
    if brave == {("investigator",)} and solved == {("beehive_mystery",)} and valid == {("beehive_mystery",)}:
        for i, mystery in enumerate(MYSTERIES):
            sample = generate(StoryParams("Luna", "rabbit", "Grandma Bee", mystery, seed=i))
            if "beehive" not in sample.story.lower() or not sample.world.facts["solved"]:
                print("MISMATCH: generated story failed verification.")
                return 1
        print("OK: ASP gate agrees with Python reasonableness and generated stories.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Beehive bravery mystery storyworld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--telling", type=int, choices=range(len(OPENINGS)))
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
        name=args.name or rng.choice(NAMES),
        animal=args.animal or rng.choice(ANIMALS),
        helper=args.helper or rng.choice(HELPERS),
        mystery=args.mystery or rng.choice(sorted(MYSTERIES)),
        seed=args.seed,
        telling=args.telling if args.telling is not None else rng.randrange(len(OPENINGS)),
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, mystery in enumerate(sorted(MYSTERIES)):
            params = StoryParams(
                name=NAMES[i % len(NAMES)],
                animal=ANIMALS[i % len(ANIMALS)],
                helper=HELPERS[i % len(HELPERS)],
                mystery=mystery,
                seed=base_seed + i,
                telling=i % len(OPENINGS),
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
