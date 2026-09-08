#!/usr/bin/env python3
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

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Instrument:
    id: str
    label: str
    sound: str
    size: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RoomPlan:
    id: str
    label: str
    clutter: int
    capacity: int
    echo: str


INSTRUMENTS = {
    "drum": Instrument("drum", "a huge brass drum", "BOOM", "wide", {"width": 3.0}, {"energy": 2.0}),
    "horn": Instrument("horn", "a silver horn", "TOOT", "long", {"length": 2.0}, {"brightness": 1.0}),
    "piano": Instrument("piano", "an upright piano", "CLANG", "heavy", {"weight": 5.0}, {"gravity": 2.0}),
}

ROOMS = {
    "music_room": RoomPlan(
        "music_room",
        "the music room",
        clutter=10,
        capacity=10,
        echo="The walls threw every note back twice.",
    ),
    "assembly_room": RoomPlan(
        "assembly_room",
        "the assembly room",
        clutter=10,
        capacity=20,
        echo="The high rafters made even a whisper sound grand.",
    ),
}

HERO_NAMES = ["Luna", "Mara", "Tess", "Pip"]
HELPER_NAMES = ["Mr. Bell", "Aunt June", "Professor Reed"]
ENTERPRISE_NAMES = ["The Ten-Note Enterprise", "The Grand Busy Band", "The Room-Saving Company"]


@dataclass
class StoryParams:
    place: str = "music_room"
    instrument: str = "drum"
    name: str = "Luna"
    helper: str = "Mr. Bell"
    enterprise: str = "The Ten-Note Enterprise"
    seed: int | None = None


@dataclass
class World:
    room: RoomPlan
    instrument: Instrument
    hero: str
    helper: str
    enterprise: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def reasonability_gate(room: RoomPlan, instrument: Instrument) -> bool:
    return room.id == "music_room" and room.capacity >= 10 and room.clutter >= 10


def build_world(params: StoryParams) -> World:
    if params.place not in ROOMS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.instrument not in INSTRUMENTS:
        raise StoryError(f"Unknown instrument: {params.instrument}")
    room = ROOMS[params.place]
    instrument = INSTRUMENTS[params.instrument]
    if not reasonability_gate(room, instrument):
        raise StoryError("This enterprise needs a music room with ten clear places.")
    world = World(room, instrument, params.name, params.helper, params.enterprise)
    clutter = 10
    world.meters.update({"clutter": clutter, "clear_space": 0, "sound": 0})
    world.memes.update({"worry": 3, "courage": 1, "wonder": 0})
    world.facts["transformation"] = "ten busy music stands became one orderly orchestra"
    return world


def tell(world: World) -> None:
    r = world.room
    h = world.hero
    helper = world.helper
    instrument = world.instrument
    enterprise = world.enterprise

    world.say(
        f"In {r.label}, Luna began the Ten Enterprise, a busy plan to make ten instruments play one mighty song before lunchtime."
    )
    world.say(
        f"She had chosen {instrument.label}, and its {instrument.sound} was so large that the music room seemed to grow a second ceiling."
    )
    world.say(
        f"Ten stands crowded the floor, ten music folders leaned like tired towers, and {r.echo}"
    )

    world.para()
    world.say(
        f'"This enterprise is too busy to move," {helper} said, pointing at the tangled chairs and rattling stands.'
    )
    world.say(
        f'"Then we will transform the busy room into a band," Luna answered. "But we will change one thing at a time."'
    )
    world.say(
        f"Luna counted ten stations, moved the tallest stands to the wall, and gave each instrument one clear patch of floor."
    )
    world.say(
        f"At the tenth move, the last loose cord slid away from the doorway. The room had not become larger, but its paths had become clear."
    )

    world.para()
    world.say(
        f"{helper} lifted one hand. Luna tapped {instrument.label}: {instrument.sound}."
    )
    world.say(
        f"Nine other players answered in turn. The ten separate noises transformed into a single marching tune that rolled through the room and out beneath the door."
    )
    world.say(
        f"The busy enterprise became a concert, and every player could see every other player."
    )

    world.para()
    world.say(
        f"Luna's final note made a music stand tremble, but it stayed safely in its place."
    )
    world.say(
        f"The {enterprise} ended with ten players, ten clear stations, and one enormous smile from {helper}."
    )
    world.say(
        f"That evening, the music room looked almost ordinary, except that the ten empty spaces seemed to hum with the shape of the song."
    )
    world.say(
        "The tall-tale lesson was this: a busy enterprise can transform into something wonderful when people count carefully, clear a path, and listen to one another."
    )

    world.meters.update({"clutter": 0, "clear_space": 10, "sound": 10})
    world.memes.update({"worry": 0, "courage": 4, "wonder": 10})
    world.facts.update(
        before_clutter=10,
        after_clear_space=10,
        players=10,
        resolved=True,
        final_image="ten empty spaces hummed with the shape of the song",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a tall tale about {world.hero}'s busy ten-player enterprise in {world.room.label}.",
        f"Show a transformation from a cluttered music room to an orderly concert.",
        f"Include {world.instrument.sound}, a brief exchange with {world.helper}, and ten clear stations.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What enterprise did Luna begin?",
            "Luna began a ten-player enterprise to make ten instruments play one mighty song in the music room.",
        ),
        QAItem(
            "Why was the music room too busy at first?",
            "Ten stands, ten folders, tangled chairs, and loose cords crowded the floor and blocked clear paths.",
        ),
        QAItem(
            "How did Luna transform the room?",
            "She counted ten stations, moved the tallest stands to the wall, and gave each instrument one clear patch of floor.",
        ),
        QAItem(
            "What happened when the players listened to one another?",
            "Their ten separate noises transformed into one marching tune that rolled through the room.",
        ),
        QAItem(
            "What lesson did the tall tale teach?",
            "A busy enterprise can transform into something wonderful when people count carefully, clear a path, and listen to one another.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a transformation?",
            "A transformation is a meaningful change from one condition or form into another.",
        ),
        QAItem(
            "Why should a music room have clear paths?",
            "Clear paths help musicians move safely, reach their instruments, and avoid tripping over stands or cords.",
        ),
        QAItem(
            "What makes an ensemble sound together?",
            "An ensemble sounds together when its players listen, keep a shared rhythm, and respond to one another.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"place: {world.room.label}",
            f"instrument: {world.instrument.label}",
            f"clutter meter: {world.meters['clutter']}",
            f"clear-space meter: {world.meters['clear_space']}",
            f"sound meter: {world.meters['sound']}",
            f"memes: {world.memes}",
            f"transformation: {world.facts['transformation']}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
ten_required :- capacity(music_room, C), C >= 10.
enterprise_ready :- ten_required, busy(music_room, 10).
transformed(music_room) :- enterprise_ready, clear_spaces(music_room, 10).
valid(P) :- transformed(P).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("room", "music_room"),
            asp.fact("capacity", "music_room", 10),
            asp.fact("busy", "music_room", 10),
            asp.fact("clear_spaces", "music_room", 10),
        ]
    )


def asp_program(show: str = "#show transformed/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "transformed"))
    expected = {("music_room",)}
    if actual != expected:
        print(f"MISMATCH: expected {sorted(expected)}, got {sorted(actual)}")
        return 1
    sample = generate(StoryParams(seed=1))
    if "transformed" not in sample.story and "transform" not in sample.story:
        print("MISMATCH: generated story lacks transformation language")
        return 1
    print("OK: Python and ASP agree on the ten-place transformation.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A tall tale about Luna's ten-person enterprise in a busy music room."
    )
    parser.add_argument("--place", choices=sorted(ROOMS), default=None)
    parser.add_argument("--instrument", choices=sorted(INSTRUMENTS), default=None)
    parser.add_argument("--name", choices=HERO_NAMES, default=None)
    parser.add_argument("--helper", choices=HELPER_NAMES, default=None)
    parser.add_argument("--enterprise", choices=ENTERPRISE_NAMES, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or "music_room",
        instrument=args.instrument or rng.choice(sorted(INSTRUMENTS)),
        name=args.name or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        enterprise=args.enterprise or rng.choice(ENTERPRISE_NAMES),
        seed=args.seed,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
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
        for atom in sorted(asp.atoms(model, "transformed")):
            print(atom)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(
                place="music_room",
                instrument=instrument,
                name=name,
                helper=helper,
                enterprise=enterprise,
                seed=seed + i,
            )
            for i, (instrument, name, helper, enterprise) in enumerate(
                [
                    ("drum", "Luna", "Mr. Bell", "The Ten-Note Enterprise"),
                    ("horn", "Mara", "Aunt June", "The Grand Busy Band"),
                    ("piano", "Tess", "Professor Reed", "The Room-Saving Company"),
                ]
            )
        ]
    else:
        rng = random.Random(seed)
        params_list = []
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
