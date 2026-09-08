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
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")) and os.path.dirname(_storyworlds_dir) != _storyworlds_dir:
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    atmosphere: str


@dataclass(frozen=True)
class Spell:
    id: str
    name: str
    effect: str
    cost: str


@dataclass(frozen=True)
class Clue:
    id: str
    object_name: str
    detail: str
    meaning: str


@dataclass(frozen=True)
class Case:
    id: str
    missing: str
    location: str
    culprit: str
    motive: str
    reveal: str
    resolution: str
    ending: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.trace.append(text)


SETTINGS = {
    "moon_library": Setting(
        "moon_library",
        "the Moon Library",
        "silver lamps hummed above shelves that leaned like sleepy giants",
    ),
    "clock_garden": Setting(
        "clock_garden",
        "the Clock Garden",
        "bronze flowers ticked whenever the wind moved through them",
    ),
    "cloud_museum": Setting(
        "cloud_museum",
        "the Cloud Museum",
        "floating glass cases drifted beneath a painted blue ceiling",
    ),
}

SPELLS = {
    "echo_glitter": Spell(
        "echo_glitter",
        "Echo Glitter",
        "makes the last sound in a room sparkle in the air",
        "it cannot repeat a lie",
    ),
    "backward_broom": Spell(
        "backward_broom",
        "Backward Broom",
        "sweeps footprints into the places they came from",
        "it leaves one bright bristle behind",
    ),
    "truth_teacup": Spell(
        "truth_teacup",
        "Truth Teacup",
        "warms when someone tells the important part of a story",
        "it cools if anyone interrupts",
    ),
}

CLUES = {
    "blue_feather": Clue(
        "blue_feather",
        "a blue feather",
        "a blue feather rested inside the locked display",
        "the night curator had visited the room",
    ),
    "sugar_clock": Clue(
        "sugar_clock",
        "a sugar clock",
        "a sugar clock had melted into a tiny puddle shaped like an arrow",
        "the missing object had been carried toward the pantry",
    ),
    "crooked_shadow": Clue(
        "crooked_shadow",
        "a crooked shadow",
        "a crooked shadow pointed at a wall with no lamp beside it",
        "someone had used a spell to hide a doorway",
    ),
    "silver_thread": Clue(
        "silver_thread",
        "a silver thread",
        "a silver thread caught on the display latch",
        "a costume pocket had brushed past the case",
    ),
}

CASES = {
    "vanished_moon": Case(
        "vanished_moon",
        "the little moonstone",
        "the locked star cabinet",
        "Pip the apprentice dragon",
        "Pip borrowed it to brighten a frightened moth's dark tunnel",
        "the moonstone was glowing inside a nest of folded maps beneath the reading table",
        "Pip returned it, then asked before borrowing magical things",
        "the cabinet shone again, while the grateful moth blinked like a tiny lantern",
    ),
    "singing_key": Case(
        "singing_key",
        "the brass singing key",
        "the music cupboard",
        "Mara the clockmaker",
        "Mara hid it because its song had begun waking the garden at midnight",
        "the key was tucked beneath a blanket beside a sleeping clockbird",
        "the friends muffled the key with velvet and repaired its noisy spring",
        "the key sang one soft note, and every clock in the garden answered politely",
    ),
    "cloud_crown": Case(
        "cloud_crown",
        "the silver cloud crown",
        "the highest glass case",
        "Nix the museum guide",
        "Nix moved it before a storm spell could wash its delicate clouds away",
        "the crown floated inside a rain barrel behind the restoration room",
        "the children dried the crown and placed a weather warning beside its case",
        "the cloud crown puffed into a gentle white halo above the museum door",
    ),
    "bonkers_bottle": Case(
        "bonkers_bottle",
        "the Bonkers Bottle",
        "the cabinet of unusual potions",
        "Tula the baker",
        "Tula carried it away because its giggles were startling the baby griffins",
        "the bottle was under a flour sack, still chuckling whenever anyone sneezed",
        "the friends corked the bottle with a calm-down charm and moved it to a quiet shelf",
        "one safe giggle escaped, bounced off the ceiling, and made everyone smile",
    ),
}


@dataclass
class StoryParams:
    setting: str
    case: str
    spell: str
    detective: str
    helper: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Pia", "Jasper", "Nora", "Theo"]
HELPERS = ["Bram", "Tess", "Ollie", "Suri", "Wren", "Mina"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, m) for s in SETTINGS for c in CASES for m in SPELLS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    for field_name, registry in (
        ("setting", SETTINGS),
        ("case", CASES),
        ("spell", SPELLS),
    ):
        value = getattr(args, field_name, None)
        if value is not None and value not in registry:
            raise StoryError(f"Unknown {field_name}: {value}")
    choices = [
        combo for combo in valid_combos()
        if getattr(args, "setting", None) in (None, combo[0])
        and getattr(args, "case", None) in (None, combo[1])
        and getattr(args, "spell", None) in (None, combo[2])
    ]
    if not choices:
        raise StoryError("No compatible setting, case, and spell combination exists.")
    setting, case, spell = rng.choice(choices)
    detective = getattr(args, "detective", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if detective == helper:
        raise StoryError("The detective and helper must have different names.")
    return StoryParams(setting, case, spell, detective, helper, getattr(args, "seed", None))


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    world.add(Entity("detective", "character", params.detective, memes={"curiosity": 1.0}))
    world.add(Entity("helper", "character", params.helper, memes={"helpfulness": 1.0}))
    world.add(Entity("missing", "artifact", CASES[params.case].missing, meters={"present": 0.0}))
    world.add(Entity("case_room", "place", world.setting.place, meters={"magical": 1.0}))
    world.facts["case"] = CASES[params.case]
    world.facts["spell"] = SPELLS[params.spell]
    return world


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xB0NKE if False else params.seed ^ 0xB0A7)
    text = "|".join((params.setting, params.case, params.spell, params.detective, params.helper))
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(text)))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    rng = _rng(params)
    case = CASES[params.case]
    spell = SPELLS[params.spell]
    detective = world.entities["detective"]
    helper = world.entities["helper"]
    missing = world.entities["missing"]

    clue = rng.choice(list(CLUES.values()))
    opening = rng.choice([
        f"At {world.setting.place}, {params.detective} was learning to solve magical mysteries.",
        f"The lamps in {world.setting.place} hummed while {params.detective} began a very strange detective case.",
        f"Nothing seemed bonkers at {world.setting.place} until {params.detective} found the empty place where {case.missing} should have been.",
    ])
    world.say(opening)
    world.say(
        f"The missing treasure had vanished from {case.location}, and the lock was still closed. "
        f"That meant the thief had used magic, a secret passage, or both."
    )
    world.say(
        f"Near the case, {clue.detail}. {params.detective} wrote the clue down instead of blaming anyone."
    )
    detective.memes["curiosity"] = 2.0
    world.say(
        f"\"I think {clue.meaning},\" said {params.detective}. "
        f"\"Or the whole room has gone bonkers,\" replied {params.helper}."
    )
    world.say(
        f"{params.helper} pointed to the foreshadowing detail: {spell.cost}. "
        f"\"Then we should use {spell.name} carefully,\" said {params.detective}."
    )
    world.say(
        f"They cast {spell.name}. The magic {spell.effect}, revealing a trail toward {case.location}."
    )
    world.say(
        f"At the end of the trail, {case.reveal}. "
        f"{params.detective} asked, \"Why did you take it?\""
    )
    world.say(
        f"{case.culprit} answered, \"I did it because {case.motive}.\" "
        f"The reason did not erase the theft, but it explained the mystery."
    )
    helper.memes["honesty"] = 1.0
    world.say(
        f"{params.helper} said, \"A good mystery needs the truth, and a good friend needs a kinder plan.\" "
        f"Together, the children {case.resolution}."
    )
    missing.meters["present"] = 1.0
    world.facts["solved"] = True
    world.say(
        f"The case was solved. {case.ending} "
        f"{params.detective} underlined the lesson: ask questions before making accusations."
    )

    story = " ".join(world.trace)
    prompts = [
        "Write a child-friendly bonkers magic whodunit with a missing object and a fair solution.",
        f"Tell a mystery in {world.setting.place} where foreshadowing helps {params.detective} find {case.missing}.",
        f"Use {spell.name} in a gentle magical detective story.",
    ]
    story_qa = [
        QAItem("What disappeared?", f"{case.missing} disappeared from {case.location}."),
        QAItem("What clue helped solve the case?", f"The clue was that {clue.detail}, which suggested that {clue.meaning}."),
        QAItem("What magical tool did the detectives use?", f"They used {spell.name}, which {spell.effect}."),
        QAItem("Why was the object moved?", f"{case.culprit} moved it because {case.motive}."),
        QAItem("How was the mystery resolved?", f"They {case.resolution}."),
    ]
    world_qa = [
        QAItem("What is foreshadowing?", "Foreshadowing is a small detail that gives a helpful hint about something that happens later."),
        QAItem("What makes a whodunit fair?", "A fair whodunit gives readers clues that can point toward the answer before the mystery is solved."),
        QAItem("What is magic in this storyworld?", "Magic is a playful force that can reveal clues, but it must be used carefully and honestly."),
        QAItem("What does bonkers mean here?", "Bonkers means wildly silly or surprising, while the mystery still has a clear cause and solution."),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


ASP_RULES = r"""
valid(S,C,M) :- setting(S), case(C), spell(M).
solved(C) :- case(C).
"""


def asp_facts() -> str:
    import asp
    facts = []
    for key in SETTINGS:
        facts.append(asp.fact("setting", key))
    for key in CASES:
        facts.append(asp.fact("case", key))
    for key in SPELLS:
        facts.append(asp.fact("spell", key))
    return "\n".join(facts)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("ASP/Python mismatch.")
        print("Only Python:", sorted(expected - actual))
        print("Only ASP:", sorted(actual - expected))
        return 1
    for seed in range(3):
        params = StoryParams("moon_library", "vanished_moon", "echo_glitter", "Luna", "Bram", seed)
        sample = generate(params)
        if "bonkers" not in sample.story.lower() and "bonkers" not in sample.to_json().lower():
            print("Generated story missed the required seed word.")
            return 1
    print(f"OK: ASP matches Python for {len(expected)} combinations and generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bonkers magical whodunit with foreshadowing.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--spell", choices=SPELLS)
    parser.add_argument("--detective")
    parser.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting, case, spell in valid_combos():
            samples.append(generate(StoryParams(setting, case, spell, "Luna", "Bram")))
    else:
        for index in range(max(args.n, 0)):
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = base_seed + index
            params = resolve_params(local_args, random.Random(local_args.seed))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
