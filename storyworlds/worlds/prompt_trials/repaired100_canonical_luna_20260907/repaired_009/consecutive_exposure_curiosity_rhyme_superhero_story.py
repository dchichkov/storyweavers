#!/usr/bin/env python3
"""
A small superhero storyworld about consecutive exposure and curiosity.
Luna discovers that seeing the same puzzling moon-mark on consecutive rooftops
is not a danger but a clue. A rhyme, shared aloud with her helper, reveals how
to guide a lost cloud-dragon home.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Clue:
    id: str
    mark: str
    location: str
    meaning: str


@dataclass(frozen=True)
class Rhyme:
    id: str
    line: str
    answer: str


@dataclass
class Setting:
    id: str
    place: str
    landmarks: tuple[str, ...]
    affords: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    "skyline": Setting(
        "skyline",
        "the Moonbeam City rooftops",
        ("the clock tower", "the library roof", "the bridge beacon"),
        {"observe", "fly", "echo"},
    ),
    "harbor": Setting(
        "harbor",
        "the Starfish Harbor rooftops",
        ("the lighthouse", "the ferry shed", "the signal mast"),
        {"observe", "fly", "echo"},
    ),
    "garden": Setting(
        "garden",
        "the Sunflower Garden towers",
        ("the glasshouse", "the bell tower", "the water tower"),
        {"observe", "fly", "echo"},
    ),
}

CLUES = {
    "silver_moon": Clue(
        "silver_moon",
        "a silver crescent with one blue dot",
        "the same mark appears on consecutive rooftops",
        "the marks form a safe path for a traveler in the clouds",
    ),
    "red_star": Clue(
        "red_star",
        "a red star beside two tiny lines",
        "the same mark appears on consecutive towers",
        "the marks point toward the warmest rooftop vent",
    ),
    "green_wave": Clue(
        "green_wave",
        "a green wave beneath a yellow spark",
        "the same mark appears on consecutive beacons",
        "the marks show where a frightened creature can land",
    ),
}

RHYMES = {
    "moon_path": Rhyme(
        "moon_path",
        "“When moon marks meet in a row, follow the glow where soft winds blow.”",
        "follow the consecutive marks toward the gentle wind",
    ),
    "star_vent": Rhyme(
        "star_vent",
        "“A star in sight, then lines of two, find the warm place waiting for you.”",
        "find the warm rooftop vent",
    ),
    "wave_landing": Rhyme(
        "wave_landing",
        "“Green waves gleam and yellow sparks, guide small wings through evening dark.”",
        "guide the creature to the beacon path",
    ),
}

HERO_NAMES = ["Luna", "Mira", "Nova", "Tara", "Zee"]
HELPER_NAMES = ["Pip", "Robin", "Sunny", "Kai", "Moss"]
POWERS = ["moonlight vision", "wind listening", "star jumps", "gentle thunder"]
TRAITS = ["curious", "brave", "patient", "cheerful"]

ARCS = {
    "silver_moon": ("silver_moon", "moon_path", "a cloud-dragon had lost its way above the city"),
    "red_star": ("red_star", "star_vent", "a tiny sky-mouse was shivering between tall towers"),
    "green_wave": ("green_wave", "wave_landing", "a young storm-bird could not find a safe place to land"),
}


ASP_RULES = r"""
consecutive_exposure(C) :- clue(C), exposure(C, N), N >= 2.
useful_clue(C) :- consecutive_exposure(C), meaning(C, M).
valid_story(S, C, R) :- setting(S), clue(C), rhyme(R), affords(S, observe),
    useful_clue(C), teaches(R, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feature in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, feature))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("meaning", cid, clue.meaning))
        lines.append(asp.fact("exposure", cid, 2))
    for rid, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
        clue_id = {"moon_path": "silver_moon", "star_vent": "red_star", "wave_landing": "green_wave"}[rid]
        lines.append(asp.fact("teaches", rid, clue_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting_id, clue_id, rhyme_id)
        for setting_id in SETTINGS
        for clue_id in CLUES
        for rhyme_id, rhyme in RHYMES.items()
        if rhyme_id == ARCS[clue_id][1]
    ]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


@dataclass
class StoryParams:
    place: str
    clue: str
    rhyme: str
    hero: str
    helper: str
    power: str
    trait: str
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about consecutive exposure, curiosity, and rhyme."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--rhyme", choices=RHYMES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--trait", choices=TRAITS)
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
    choices = valid_combos()
    if args.place:
        choices = [item for item in choices if item[0] == args.place]
    if args.clue:
        choices = [item for item in choices if item[1] == args.clue]
    if args.rhyme:
        choices = [item for item in choices if item[2] == args.rhyme]
    if not choices:
        raise StoryError("The requested place, clue, and rhyme do not form a valid story.")
    place, clue, rhyme = rng.choice(choices)
    return StoryParams(
        place=place,
        clue=clue,
        rhyme=rhyme,
        hero=args.hero or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        power=args.power or rng.choice(POWERS),
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(4),
        turn=rng.randrange(4),
        ending=rng.randrange(4),
    )


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.rhyme not in RHYMES:
        raise StoryError(f"Unknown rhyme: {params.rhyme}")
    expected_rhyme = ARCS[params.clue][1]
    if params.rhyme != expected_rhyme:
        raise StoryError(
            f"The rhyme '{params.rhyme}' does not explain the clue '{params.clue}'."
        )

    setting = SETTINGS[params.place]
    clue = CLUES[params.clue]
    rhyme = RHYMES[params.rhyme]
    problem = ARCS[params.clue][2]
    world = World(setting)

    hero = world.add(
        Entity(
            params.hero,
            "hero",
            params.hero,
            meters={"distance": 0.0, "danger": 0.0},
            memes={"curiosity": 1.0, "courage": 0.0, "wonder": 0.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper,
            "helper",
            params.helper,
            meters={"distance": 0.0},
            memes={"trust": 1.0, "understanding": 0.0},
        )
    )
    traveler = world.add(
        Entity(
            "traveler",
            "creature",
            "the lost cloud traveler",
            meters={"safe": 0.0, "distance": 3.0},
            memes={"fear": 1.0, "relief": 0.0},
        )
    )

    fmt = {
        "hero": hero.label,
        "helper": helper.label,
        "place": setting.place,
        "power": params.power,
        "trait": params.trait,
        "mark": clue.mark,
        "problem": problem,
        "meaning": clue.meaning,
        "rhyme": rhyme.line,
    }

    openings = [
        "{hero} was a {trait} superhero whose {power} made even quiet rooftops sparkle. One evening, {hero} spotted {mark} on {landmark1}.",
        "High above {place}, {hero} practiced {power} while {helper} checked the city lights. Then a strange mark appeared: {mark}.",
        "The people of {place} knew {hero} as a helpful hero, but that night {hero} had a new mystery to solve. {mark} glimmered near {landmark1}.",
        "{hero} and {helper} were crossing {place} when a worried cloud traveler swooped past them. Behind it, {mark} shone on {landmark1}.",
    ]
    turns = [
        "{hero} did not blast the mystery away. Curiosity made {hero} look closely, and the same mark appeared on the next rooftop, then on the next one.",
        '"Wait," said {hero}. “The marks came in consecutive places. Maybe their repeated exposure is a message, not a threat.”',
        "{helper} pointed to the shining trail. “You have seen that symbol more than once,” {helper} said. “What does the pattern tell you?”",
        "{hero} listened to the wind, counted the repeated marks, and realized that each new exposure made the path clearer.",
    ]
    endings = [
        "The cloud traveler curled beside the warm light, safe at last. Below, the city cheered as {hero} learned that careful curiosity can be a superpower.",
        "By moonrise, the repeated marks faded. {helper} grinned, and {hero} tucked the rhyme into a notebook for the next mystery.",
        "The rooftops glowed in a bright row, and the rescued traveler gave a happy cloud puff. {hero} had turned a puzzling pattern into a safe journey.",
        "Everyone watched the traveler soar home. {hero} smiled because the smallest clue, seen again and again, had led to the biggest save.",
    ]

    landmark1, landmark2, landmark3 = setting.landmarks
    world.say(
        openings[params.opening % len(openings)].format(
            **fmt, landmark1=landmark1, landmark2=landmark2, landmark3=landmark3
        )
    )
    world.say(f"Far below, {problem.capitalize()}.")
    world.para()

    world.say(turns[params.turn % len(turns)].format(**fmt))
    world.say(f'"I hear a rhythm in it," said {helper}. “Try a rhyme.”')
    world.say(f'{hero} answered, “{rhyme.line.strip("“”")}”')
    world.para()

    hero.memes["curiosity"] += 1.0
    hero.memes["courage"] += 1.0
    helper.memes["understanding"] += 1.0
    traveler.meters["distance"] = 0.0
    traveler.meters["safe"] = 1.0
    traveler.memes["fear"] = 0.0
    traveler.memes["relief"] = 1.0
    hero.meters["distance"] = 3.0

    world.say(
        f"Together, {hero.label} and {helper.label} followed the consecutive signs. "
        f"The rhyme showed them how to {rhyme.answer}, and the {params.power} carried their message through the clouds."
    )
    world.say(
        f"The traveler understood the gentle signal and flew toward {landmark3}, where a safe landing waited."
    )
    world.para()
    world.say(endings[params.ending % len(endings)].format(**fmt))

    world.facts.update(
        hero=hero,
        helper=helper,
        traveler=traveler,
        clue=clue,
        rhyme=rhyme,
        problem=problem,
        exposure_count=3,
        path=(landmark1, landmark2, landmark3),
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    clue: Clue = world.facts["clue"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a superhero story about consecutive exposure to {clue.mark}.",
            "Tell a child-friendly adventure where Curiosity and Rhyme help a hero solve a repeating clue.",
            "Write a Superhero Story in which a repeated pattern becomes a safe path.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Clue = world.facts["clue"]
    rhyme: Rhyme = world.facts["rhyme"]
    traveler: Entity = world.facts["traveler"]
    return [
        QAItem(
            "What did the hero see on consecutive rooftops?",
            f"{hero.label} saw {clue.mark} on consecutive rooftops.",
        ),
        QAItem(
            "Why did the repeated exposure matter?",
            f"The repeated exposure mattered because {clue.meaning}.",
        ),
        QAItem(
            f"How did {helper.label} help?",
            f"{helper.label} helped by asking {hero.label} to listen for a rhyme in the pattern.",
        ),
        QAItem(
            "What proved that the plan worked?",
            f"The plan worked because the lost cloud traveler reached a safe landing and felt relief.",
        ),
        QAItem(
            "What rhyme guided the rescue?",
            rhyme.line,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does consecutive mean?",
            "Consecutive means following one after another without a gap in the sequence.",
        ),
        QAItem(
            "What does exposure mean here?",
            "Exposure means seeing or encountering something; repeated exposure means encountering it again and again.",
        ),
        QAItem(
            "What is curiosity?",
            "Curiosity is a wish to learn more about something mysterious or interesting.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a phrase or pair of words with matching or similar ending sounds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting.place}")
    lines.append(f"exposure_count: {world.facts.get('exposure_count', 0)}")
    lines.append(f"path: {' -> '.join(world.facts.get('path', ())) }")
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.label}: meters={meters} memes={memes}")
    return "\n".join(lines)


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
    python_values = set(valid_combos())
    asp_values = set(asp_valid())
    if python_values == asp_values:
        print(f"OK: ASP and Python agree on {len(python_values)} valid combos.")
        return 0
    print("Mismatch between ASP and Python:")
    print("Only Python:", sorted(python_values - asp_values))
    print("Only ASP:", sorted(asp_values - python_values))
    return 1


CURATED = [
    StoryParams(
        place="skyline",
        clue="silver_moon",
        rhyme="moon_path",
        hero="Luna",
        helper="Pip",
        power="moonlight vision",
        trait="curious",
    ),
    StoryParams(
        place="harbor",
        clue="red_star",
        rhyme="star_vent",
        hero="Mira",
        helper="Robin",
        power="wind listening",
        trait="patient",
        opening=1,
        turn=1,
        ending=1,
    ),
    StoryParams(
        place="garden",
        clue="green_wave",
        rhyme="wave_landing",
        hero="Nova",
        helper="Sunny",
        power="star jumps",
        trait="brave",
        opening=2,
        turn=2,
        ending=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + attempts))
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
