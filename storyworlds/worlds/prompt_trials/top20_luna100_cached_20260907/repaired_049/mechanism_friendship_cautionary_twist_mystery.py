#!/usr/bin/env python3
"""
A child-facing mystery storyworld about a hidden mechanism, friendship, and a
cautionary twist.

The domain is a small clockwork hill station where a missing bell signal makes
the friends investigate. Their first explanation seems right, but a careful
test reveals that the mechanism is protecting someone rather than causing
trouble.
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

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    clue: str
    false_theory: str
    hidden_cause: str
    mechanism: str
    caution: str
    action: str
    result: str
    twist: str
    ending: str


@dataclass
class World:
    place: str = "the old hill station"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CASES = [
    Case(
        "silent_bell",
        "At dawn, the little bell that warned climbers about loose stones stayed silent.",
        "A thread of blue wool caught on the bell's lower gear.",
        "The friends thought a night bird had bent the bell arm.",
        "A goat had brushed the release cord while reaching for mountain thyme.",
        "a counterweight, a grooved wheel, and a cord that released the warning bell",
        "the cord could pull hard enough to drop stones if anyone tugged it carelessly",
        "marked the cord, moved the thyme basket, and tested the wheel with a soft stick",
        "the bell rang once, and no stone fell onto the path",
        "the bell had stayed silent because its safety stop was doing its job",
        "Below the ridge, the friends heard the bell ring gently while the goat nibbled far from the cord.",
    ),
    Case(
        "lantern_lock",
        "The signal lantern above the station blinked three times and then vanished.",
        "A warm brass key lay beside the locked lantern cabinet.",
        "The friends suspected that a sneaky stranger had stolen the signal light.",
        "The cabinet's heat-release pin had slipped when the afternoon sun warmed the metal.",
        "a spring latch, a heat pin, and a shutter that closed when the lamp grew too hot",
        "forcing the shutter open could crack the glass and start a fire",
        "waited for the metal to cool, checked the pin with a feather, and opened the latch slowly",
        "the lantern shone again without a broken pane or smoky room",
        "the shutter had hidden the light to prevent a fire, not to hide a thief",
        "That night, the safe lantern swept a bright circle across the station roof.",
    ),
    Case(
        "bridge_click",
        "A wooden footbridge clicked each time someone stepped toward the river.",
        "The clicks stopped whenever a heavy sack rested near the left post.",
        "The friends decided that a troll must be warning travelers away.",
        "A loose pressure board had been built to signal when the bridge needed a second person.",
        "a pressure board, a small bell, and a locking peg",
        "removing the peg before checking the bridge could make the middle plank swing loose",
        "placed a sack on the board, examined the peg, and called an adult before crossing",
        "the bridge was tightened before anyone crossed the river",
        "the warning mechanism had been installed after an earlier plank had cracked",
        "The friends crossed together, and the river carried their relieved laughter downstream.",
    ),
    Case(
        "mirror_signal",
        "The watch mirror flashed toward the forest even though nobody stood at the tower.",
        "A tiny scratch on the mirror pointed exactly at a nest in the rafters.",
        "The friends thought a trespasser was using the tower to send secret signals.",
        "A trapped swallow was beating its wings against the mirror cord.",
        "a pivoting mirror, a cord, and a wooden stop that kept the glass from shattering",
        "pulling the cord could frighten the bird into the open stairwell",
        "covered the mirror with a cloth, opened the high window, and waited quietly",
        "the swallow flew out and the mirror settled without a crack",
        "the strange signal was a frightened bird asking for room, not a spy sending a message",
        "Afterward, the mirror flashed only when the watch keeper chose to signal.",
    ),
    Case(
        "water_gate",
        "The station fountain stopped just before the children filled their cups.",
        "Mud marked a narrow path from the fountain to a hidden side gate.",
        "The friends suspected that someone was stealing the spring water.",
        "The float valve had closed because rain had filled the catch basin too quickly.",
        "a float valve, a stone channel, and a side gate that drained extra water",
        "closing the side gate by force could flood the path below",
        "cleared leaves from the float, opened the drain gently, and kept watch by the channel",
        "the fountain flowed again while the lower path stayed dry",
        "the apparent water thief was a safety mechanism saving the path from a flood",
        "Clear water sparkled in every cup, and the friends left the drain free of leaves.",
    ),
    Case(
        "rope_lift",
        "The supply lift rose halfway and stopped with a basket of apples inside.",
        "Three fresh scratches curved around the lift's wooden brake.",
        "The friends believed someone had climbed the shaft and jammed the lift.",
        "A mouse had pulled a loose grain sack against the brake lever.",
        "a rope drum, a brake lever, and a counterweight",
        "cutting the rope or lifting the brake suddenly could send the basket racing down",
        "tied the basket secure, called the station keeper, and eased the grain sack away",
        "the lift returned safely and the apples reached the kitchen",
        "the brake had stopped the lift before the heavier sack could make it fall",
        "At supper, the first apple was cut into equal pieces for every careful helper.",
    ),
    Case(
        "snow_marker",
        "A red marker vanished from the snowy trail just before the evening fog arrived.",
        "A neat line of holes led from the marker post toward the warming shed.",
        "The friends thought a rival team had moved the marker as a prank.",
        "The marker had been pulled down by a buried guide wire when the snow shifted.",
        "a guide wire, a spring marker, and a buried release plate",
        "digging straight down could snap the spring and whip the wire upward",
        "used long sticks to find the plate, loosened snow from the side, and wore thick mittens",
        "the marker rose again and pointed travelers toward the warm shed",
        "the hidden mechanism had lowered the marker to keep the wire from striking a passerby",
        "The red marker glowed against the snow while the friends walked home side by side.",
    ),
    Case(
        "clockwork_door",
        "The old archive door opened by itself whenever the moon rose.",
        "Dust on the floor showed that it opened only three finger-widths.",
        "The friends whispered that a ghost wanted them to enter.",
        "A cooling metal rod contracted and moved the first part of the latch.",
        "a temperature rod, a brass latch, and a chain that stopped the door",
        "pushing past the chain could damage the archive's fragile shelves",
        "placed a candle far away, watched the rod cool, and asked the keeper to unlock the door",
        "the door opened fully without touching a single shelf",
        "the ghostly invitation was really an old fire-safety design revealing a hidden escape route",
        "Inside the archive, the friends found maps of the very hill they had just crossed.",
    ),
]


NAMES = {
    "girl": ["Luna", "Mira", "Nia", "Tessa", "Pia"],
    "boy": ["Leo", "Milo", "Oren", "Tavi", "Jon"],
}

FRIEND_NAMES = {
    "girl": ["Milo", "Oren", "Tavi", "Jon"],
    "boy": ["Luna", "Mira", "Nia", "Tessa"],
}

DIALOGUE = [
    ("Luna", "What did you notice before we guessed?", "The mark tells us where to look, not what to blame."),
    ("Milo", "Should we pull it and see what happens?", "No. A warning can be protecting someone."),
    ("Nia", "Could the mechanism be stopping the trouble?", "Then we should test it gently instead of fighting it."),
    ("Tavi", "Why would a broken thing leave a careful clue?", "Maybe it is not broken. Maybe it is asking us to be careful."),
]


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about friendship and a cautionary mechanism."
    )
    parser.add_argument("--place", choices=["station"])
    parser.add_argument("--case", choices=[c.id for c in CASES])
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--friend")
    parser.add_argument("--trait", choices=["curious", "patient", "brave", "careful"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice(FRIEND_NAMES[gender])
    if friend == name:
        raise StoryError("The two friends must have different names.")
    case = args.case or rng.choice([c.id for c in CASES])
    trait = args.trait or rng.choice(["curious", "patient", "brave", "careful"])
    if case not in {c.id for c in CASES}:
        raise StoryError("Unknown mystery case.")
    return StoryParams("station", case, name, gender, friend, trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "station":
        raise StoryError("This mystery belongs at the old hill station.")
    if params.name == params.friend:
        raise StoryError("Friendship needs two different people.")
    if params.case not in {c.id for c in CASES}:
        raise StoryError("That mystery case is not in the station records.")


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def tell(world: World, params: StoryParams) -> None:
    case = next(c for c in CASES if c.id == params.case)
    hero = world.add(Entity(params.name, "character", params.gender, params.name))
    friend = world.add(Entity(params.friend, "character", "person", params.friend))
    device = world.add(Entity("mechanism", "object", "mechanism", "the hidden mechanism"))

    add_meme(hero, "curiosity")
    add_meme(friend, "trust")
    add_meter(device, "risk", 1.0)

    world.say(
        f"At the old hill station, {params.name}, a {params.trait} child, and {params.friend}, "
        "their closest friend, helped inspect the strange devices that kept the mountain paths safe."
    )
    world.say(case.opening)
    world.say(
        f"They found the first clue: {case.clue} {params.name} wanted to follow it at once, "
        f"but {params.friend} stayed beside {params.name}."
    )
    world.para()

    world.say(f'"{DIALOGUE[(params.seed or 0) % len(DIALOGUE)][1]}" {params.name} asked.')
    world.say(f'"{DIALOGUE[(params.seed or 0) % len(DIALOGUE)][2]}" {params.friend} replied.')
    world.say(
        f"Together they formed a first theory: {case.false_theory} The idea sounded sensible, "
        "but neither friend touched the device."
    )
    add_meme(hero, "worry")
    add_meme(friend, "caution")
    world.say(
        f"They checked the warning marks and discovered the hidden cause: {case.hidden_cause}"
    )
    world.say(
        f"Behind the panel was {case.mechanism}. The mechanism was not merely a machine; "
        "it carried a message about what might happen next."
    )
    world.para()

    world.say(f"The caution was clear: {case.caution}")
    world.say(
        f"Because they trusted each other, {params.name} {case.action}. "
        f"{params.friend} watched the moving parts and called out each safe step."
    )
    add_meter(hero, "careful_action")
    add_meter(friend, "helped")
    add_meme(hero, "trust")
    world.say(f"Then the result answered the mystery: {case.result}")
    world.say(
        f"But the twist surprised them: {case.twist}. Their first guess had named the danger, "
        "yet friendship and patience revealed what the mechanism was really doing."
    )
    world.para()

    add_meme(hero, "wisdom")
    add_meme(friend, "wisdom")
    world.say(
        f"The station keeper thanked both friends and added a bright tag to the mechanism: "
        '"Look closely before you pull."'
    )
    world.say(
        "That evening they wrote a new rule in the station book: a strange sound deserves "
        "a question, a test should be gentle, and no friend investigates a risky machine alone."
    )
    world.say(case.ending)

    world.facts.update(
        case=case,
        hero=hero,
        friend=friend,
        device=device,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World()
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f"Write a child-friendly mystery about {hero.id} and {friend.id} investigating {case.opening}",
        f"Tell a cautionary friendship story where a mechanism seems dangerous but has a surprising purpose.",
        f"Write a mystery with a careful twist: the clue {case.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            f"What mystery did {hero.id} and {friend.id} investigate?",
            f"They investigated this mystery at the old hill station: {case.opening}",
        ),
        QAItem(
            "What clue did the friends discover?",
            f"They discovered that {case.clue}",
        ),
        QAItem(
            "What was their first theory?",
            f"Their first theory was that {case.false_theory}",
        ),
        QAItem(
            "What did the hidden mechanism do?",
            f"The mechanism involved {case.mechanism}, and it helped explain the strange event.",
        ),
        QAItem(
            "Why did the friends act carefully?",
            f"They acted carefully because {case.caution}",
        ),
        QAItem(
            "What twist did they discover?",
            f"The twist was that {case.twist}",
        ),
        QAItem(
            "How did friendship help solve the mystery?",
            f"{hero.id} and {friend.id} trusted one another, shared observations, and tested the mechanism gently instead of acting alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a mechanism?",
            "A mechanism is a group of moving parts that works in a particular way to cause an action.",
        ),
        QAItem(
            "Why is caution useful around machines?",
            "Caution is useful because a machine may move suddenly, and a gentle test can prevent damage or injury.",
        ),
        QAItem(
            "How can friendship help during a mystery?",
            "Friends can compare what they notice, remind each other to be careful, and make better choices together.",
        ),
        QAItem(
            "What is a twist in a mystery?",
            "A twist is a surprising change in understanding that makes earlier clues look different.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(
            f"{ent.id}: type={ent.type} meters={ent.meters} memes={ent.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(station, silent_bell).
valid(station, lantern_lock).
valid(station, bridge_click).
valid(station, mirror_signal).
valid(station, water_gate).
valid(station, rope_lift).
valid(station, snow_marker).
valid(station, clockwork_door).
safe_case(C) :- valid(station, C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("place", "station")]
        + [asp.fact("case", case.id) for case in CASES]
    )


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def valid_combos() -> set[tuple]:
    return {("station", case.id) for case in CASES}


def asp_verify() -> int:
    try:
        actual = asp_valid_combos()
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    expected = valid_combos()
    if actual != expected:
        print(f"MISMATCH: Python={sorted(expected)} ASP={sorted(actual)}")
        return 1
    for case in CASES:
        params = StoryParams("station", case.id, "Luna", "girl", "Milo", "careful")
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 4:
            print("MISMATCH: generated story exercise failed.")
            return 1
    print(f"OK: ASP matches Python ({len(expected)} cases), and stories exercised.")
    return 0


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
    StoryParams("station", "silent_bell", "Luna", "girl", "Milo", "curious"),
    StoryParams("station", "lantern_lock", "Leo", "boy", "Nia", "careful"),
    StoryParams("station", "clockwork_door", "Mira", "girl", "Tavi", "patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + index)
            index += 1
            try:
                params = resolve_params(args, rng)
                params.seed = base_seed + index
                sample = generate(params)
            except StoryError as error:
                print(error, file=sys.stderr)
                raise SystemExit(2)
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.case}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
