#!/usr/bin/env python3
"""
A small rhyming storyworld about a prospector, an incinerator, and a happy ending.

The prospector searches for a bright treasure, but a broken incinerator makes a
dangerous smoky mess. By listening to a helper and repairing the machine, the
prospector discovers that a safe, shared solution is better than a glittering
guess.
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("heat", "smoke", "weight", "shine", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("hope", "worry", "curiosity", "kindness", "joy"):
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Verse:
    id: str
    clue: str
    trouble: str
    clue_detail: str
    repair: str
    twist: str
    ending: str
    prize: str
    lesson: str


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    atmosphere: str


PLACES = {
    "hollow": Place("hollow", "Copper Hollow", "red cliffs and ringing stones"),
    "ridge": Place("ridge", "Whistling Ridge", "tall grass and singing wind"),
    "creek": Place("creek", "Silver Creek", "cool water and round pebbles"),
}

PROSPECTORS = {
    "luna": {"kind": "prospector", "label": "Luna"},
    "orin": {"kind": "prospector", "label": "Orin"},
    "mara": {"kind": "prospector", "label": "Mara"},
    "pax": {"kind": "prospector", "label": "Pax"},
}

HELPERS = {
    "badger": {"kind": "badger", "label": "Bram"},
    "wren": {"kind": "wren", "label": "Wren"},
    "otter": {"kind": "otter", "label": "Ollie"},
    "goat": {"kind": "goat", "label": "Gilda"},
}

VERSES = [
    Verse(
        "ember_bucket",
        "a blue pebble shone beside the old ash bucket",
        "the incinerator coughed a smoky cloud when Luna fed it a fallen branch",
        "three cold vents were blocked by a blanket of ash",
        "Luna and her helper cooled the machine, cleared the vents, and checked the chimney",
        "the blue pebble was not a jewel at all but a piece of painted glass from the town sign",
        "The repaired incinerator hummed safely while the glass pebble flashed like a tiny moon.",
        "a clean blue sign-stone",
        "A careful search and a safe repair can reveal the real treasure.",
    ),
    Verse(
        "tin_song",
        "a bright ringing sound came from a heap of harmless tin",
        "the incinerator's door jammed and warm smoke curled across the trail",
        "a bent latch had caught on a loose metal strap",
        "they waited for the chamber to cool, removed the strap, and fastened the latch",
        "the ringing treasure was a little bell meant for the community garden gate",
        "The bell rang over the garden as every neighbor shared the evening harvest.",
        "a garden bell",
        "A prize becomes brighter when it serves many friends.",
    ),
    Verse(
        "silver_rain",
        "silver flakes glittered near the incinerator after a night of rain",
        "water in the cracked drain made the machine hiss and shudder",
        "the silver flakes were safe mica washed down from the ridge",
        "they switched off the machine, marked the wet ground, and guided the water into a stone channel",
        "the shiny trail led to a spring that could water the dry trail garden",
        "A clear spring twinkled while the garden drank and the prospector sang.",
        "a spring-fed garden",
        "Not every glittering thing belongs in a machine or in a pocket.",
    ),
    Verse(
        "copper_clue",
        "a copper-colored clue curved beneath a pile of leaves",
        "the incinerator's warning bell stayed silent while smoke gathered inside",
        "a dusty cord had slipped away from the warning bell",
        "they opened the panel only after cooling the machine and reconnected the cord",
        "the copper clue was an old safety marker placed by earlier caretakers",
        "The warning bell chimed clearly, and the trail was safe for every explorer.",
        "a shining safety marker",
        "Good clues should help people, not merely make them rich.",
    ),
    Verse(
        "warm_stone",
        "a warm round stone waited near the incinerator fence",
        "a cracked heat shield let too much warmth reach the wooden fence",
        "the stone had rolled against the shield and left a bright gap",
        "they moved the stone, replaced the shield, and watered the fence-side flowers",
        "the warm stone was a sun-heated stone from the path, not hidden gold",
        "Flowers opened beside the cool fence as the stone rested in a sunny ring.",
        "a flower-bed stone",
        "A happy ending protects the place where everyone lives.",
    ),
]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


ASP_RULES = r"""
reasonable(P, V) :- place(P), verse(V), has_clue(V), has_trouble(V), has_repair(V), happy(V).
#show reasonable/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for verse in VERSES:
        lines.extend(
            [
                asp.fact("verse", verse.id),
                asp.fact("has_clue", verse.id),
                asp.fact("has_trouble", verse.id),
                asp.fact("has_repair", verse.id),
                asp.fact("happy", verse.id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


@dataclass
class StoryParams:
    place: str
    verse: str
    prospector: str
    helper: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That setting is not part of the prospector's trail.")
    if params.verse not in {verse.id for verse in VERSES}:
        raise StoryError("That rhyming trail clue is not available.")
    if params.prospector not in PROSPECTORS:
        raise StoryError("The prospector must be a named prospector in this world.")
    if params.helper not in HELPERS:
        raise StoryError("The helper must be a named helper in this world.")
    if params.prospector == params.helper:
        raise StoryError("The prospector and helper must be different characters.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    place = PLACES[params.place]
    verse = next(item for item in VERSES if item.id == params.verse)
    prospector_info = PROSPECTORS[params.prospector]
    helper_info = HELPERS[params.helper]

    world = World(place)
    prospector = world.add(
        Entity(
            params.prospector,
            "character",
            prospector_info["label"],
            memes={"hope": 2.0, "curiosity": 2.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "character",
            helper_info["label"],
            memes={"kindness": 2.0, "worry": 1.0},
        )
    )
    incinerator = world.add(
        Entity(
            "incinerator",
            "machine",
            "incinerator",
            meters={"heat": 1.0, "smoke": 0.0, "weight": 2.0, "shine": 0.0, "distance": 0.0},
        )
    )
    clue = world.add(
        Entity(
            "clue",
            "object",
            verse.clue,
            meters={"shine": 2.0},
        )
    )

    openings = [
        f"In {place.name}, where {place.atmosphere}, {prospector.label} the prospector followed a rhyming trail.",
        f"Along {place.name}'s {place.atmosphere}, {prospector.label} the prospector carried a map with a bouncing rhyme.",
        f"One bright morning in {place.name}, {prospector.label} the prospector went searching beneath the {place.atmosphere}.",
    ]
    world.say(rng.choice(openings))
    world.say(
        f"{helper.label} the {helper_info['kind']} came along, tapping a walking stick and chanting, "
        f'"Look low, look slow, and let the safest clues show."'
    )
    world.say(
        f"Together they reached an old incinerator beside the trail, where {verse.clue}."
    )
    world.para()

    world.say(
        f"They leaned close to inspect the clue, but {verse.trouble}. "
        f"The air grew gray, and the prospector stepped back from the incinerator."
    )
    incinerator.meters["smoke"] = 3.0
    incinerator.meters["heat"] = 3.0
    prospector.memes["worry"] = 2.0
    world.say(
        f'"Should I hurry and grab the shiny clue?" asked {prospector.label}. '
        f'"No," said {helper.label}. "We cool the machine and learn what made it unhappy."'
    )
    world.say(f"The prospector listened, because {verse.clue_detail}.")
    world.para()

    helper.memes["kindness"] += 1.0
    prospector.memes["curiosity"] += 1.0
    world.say(
        f"They marked a safe circle around the incinerator and waited until its heat fell. "
        f"Then {verse.repair}."
    )
    incinerator.meters["smoke"] = 0.0
    incinerator.meters["heat"] = 0.0
    prospector.memes["worry"] = 0.0
    world.say(
        f'"The machine is quiet now," said {helper.label}. '
        f'"And the clue can tell us more," replied {prospector.label}.'
    )
    world.say(f"The twist was that {verse.twist}.")
    world.say(
        f"{prospector.label} did not keep the discovery hidden. Instead, the prospector and "
        f"{helper.label} chose {verse.prize} for the trail community."
    )
    world.say(
        f"They shared a happy ending in a new rhyme: "
        f'"Safe hands, bright lands, kind hearts make the best plans."'
    )
    world.say(f"{verse.ending} {verse.lesson}")
    world.para()

    world.facts.update(
        place=params.place,
        verse=verse.id,
        prospector=params.prospector,
        prospector_name=prospector.label,
        helper=params.helper,
        helper_name=helper.label,
        helper_kind=helper_info["kind"],
        clue=verse.clue,
        trouble=verse.trouble,
        clue_detail=verse.clue_detail,
        repair=verse.repair,
        twist=verse.twist,
        prize=verse.prize,
        ending=verse.ending,
        lesson=verse.lesson,
        resolved=True,
        happy=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly rhyming story about prospector {f['prospector_name']} finding {f['clue']} near an incinerator.",
        f"Tell a story in which {f['helper_name']} helps {f['prospector_name']} handle this danger: {f['trouble']}.",
        f"End with a happy ending showing that {f['twist']}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"Where did {f['prospector_name']} search?",
            f"{f['prospector_name']} searched in {PLACES[f['place']].name}, where {PLACES[f['place']].atmosphere}.",
        ),
        QAItem(
            "What caused the trouble?",
            f"The trouble began because {f['trouble']}.",
        ),
        QAItem(
            f"How did {f['helper_name']} help?",
            f"{f['helper_name']} helped by making the prospector slow down and then they {f['repair']}.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {f['twist']}.",
        ),
        QAItem(
            "How did the story end happily?",
            f"They shared {f['prize']}. {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a prospector?",
            "A prospector is someone who searches for useful or valuable things in the ground.",
        ),
        QAItem(
            "What is an incinerator?",
            "An incinerator is a machine made to burn certain materials safely under controlled conditions.",
        ),
        QAItem(
            "Why should someone stay away from a smoking machine?",
            "A smoking machine may be hot or unsafe, so a person should move away and ask a trained adult for help.",
        ),
        QAItem(
            "What makes a happy ending?",
            "A happy ending resolves the main problem and shows that the characters or their world are safer or better.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = ", ".join(f"{k}={v:g}" for k, v in entity.meters.items() if v)
        memes = ", ".join(f"{k}={v:g}" for k, v in entity.memes.items() if v)
        lines.append(f"{entity.id}: meters={{{meters}}} memes={{{memes}}}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prospector and incinerator rhyming-story world with a happy ending."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--verse", choices=sorted(item.id for item in VERSES))
    parser.add_argument("--prospector", choices=sorted(PROSPECTORS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
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
    place = args.place or rng.choice(sorted(PLACES))
    verse = args.verse or rng.choice([item.id for item in VERSES])
    prospector = args.prospector or rng.choice(sorted(PROSPECTORS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    params = StoryParams(place, verse, prospector, helper)
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams("hollow", "ember_bucket", "luna", "badger"),
    StoryParams("ridge", "tin_song", "orin", "wren"),
    StoryParams("creek", "silver_rain", "mara", "otter"),
    StoryParams("hollow", "copper_clue", "pax", "goat"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "reasonable"))
    expected = {(place, verse.id) for place in PLACES for verse in VERSES}
    if actual != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip() or "happy ending" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP/Python parity holds for {len(actual)} story shapes and generated stories.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(values)} valid story shapes:")
        for place, verse in values:
            print(f"  {place} / {verse}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for offset in range(max(20, args.n * 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                return
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
        if args.all:
            params = sample.params
            header = f"### {params.prospector} / {params.helper} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
