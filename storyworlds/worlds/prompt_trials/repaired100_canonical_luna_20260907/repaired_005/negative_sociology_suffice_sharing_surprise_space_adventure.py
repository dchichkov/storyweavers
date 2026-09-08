#!/usr/bin/env python3
"""
A small space-adventure story world about Luna, negative signals, sociology,
sharing, and a surprising repair.

Seed tale:
---
Luna flew the little ship Starling between bright moons, carrying a box of
garden seeds to a lonely space station. A negative warning blinked whenever
the Starling passed the station's dark ring. Luna tried a faster route and a
slower route, but the warning returned. She asked the station children what
they saw. They explained that the ring was not dangerous; it was a shared
welcome beacon whose signal had been reversed after a repair. Luna shared her
spare green crystal, the children turned it together, and the beacon shone a
happy welcome. The surprise was that the warning had been asking for help all
along.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    name: str = "Luna"
    title: str = "space adventure"
    seed: Optional[int] = None
    mission: str = "seeds"
    setting: str = "station"
    route: int = 0
    signal: int = 0
    helper: int = 0
    surprise: int = 0


@dataclass(frozen=True)
class Mission:
    id: str
    cargo: str
    recipient: str
    problem: str
    danger: str
    clue: str
    cause: str
    fix: str
    resolution: str
    endings: tuple[str, ...]


MISSIONS = {
    "seeds": Mission(
        id="seeds",
        cargo="a box of moon-garden seeds",
        recipient="the children of Echo Station",
        problem="a negative warning flashed whenever the Starling neared the station's dark ring",
        danger="the warning might make Luna turn away before the children received their garden",
        clue="the station children all pointed to the same backward arrow on the ring",
        cause="the welcome beacon had been wired backward after a hurried repair",
        fix="share her spare green crystal and turn the beacon's signal around together",
        resolution="the warning changed into a warm green welcome, and the seeds reached the station",
        endings=(
            "The children planted the seeds beneath a glass dome, where tiny green leaves soon surprised everyone.",
            "A new garden glowed beside the landing pad while the Starling's green crystal shone in the beacon.",
            "The station children shared the first moon-melon, saving a slice for Luna's next visit.",
            "From orbit, Luna saw the garden form a bright green circle around the once-dark ring.",
        ),
    ),
    "music": Mission(
        id="music",
        cargo="a case of small singing stones",
        recipient="the musicians of Comet Harbor",
        problem="a negative signal told the Starling to stop whenever it entered the harbor's purple mist",
        danger="the musicians might miss the night concert",
        clue="the harbor families hummed whenever the signal made its low, puzzled beep",
        cause="the signal was a musical invitation played upside down",
        fix="share her tuning fork and let the families turn the transmitter together",
        resolution="the beep became a cheerful melody, and the singing stones reached the concert",
        endings=(
            "The harbor sang in three languages while purple mist curled around the dancing lights.",
            "Each family added one note, and the shared song guided the Starling home.",
            "The singing stones chimed from the stage as Luna smiled at the surprising invitation.",
            "The harbor's signal became a gentle song that no traveler mistook for danger again.",
        ),
    ),
    "water": Mission(
        id="water",
        cargo="a tank of fresh blue water",
        recipient="the night gardeners of Little Orbits",
        problem="a negative red mark appeared whenever the Starling crossed the settlement's silver bridge",
        danger="the gardeners could lose their water before the dry night began",
        clue="the gardeners had placed their own blue cups beneath the red mark",
        cause="the bridge's red lamp meant 'please share water,' not 'stay away'",
        fix="share the Starling's water gauge and teach the gardeners to reset the lamp",
        resolution="the red mark became a blue sharing sign, and every garden received water",
        endings=(
            "Blue drops glittered on every leaf as the gardeners thanked Luna beneath the stars.",
            "The settlement saved one cup for the Starling, proving that sharing could travel both ways.",
            "The bridge shone blue from end to end, and thirsty flowers opened together.",
            "Luna left with an empty tank and a full heart as the gardens drank quietly.",
        ),
    ),
}

SETTINGS = {
    "station": Setting("Echo Station", "a dark ring, glass domes, and windows full of tiny stars"),
    "harbor": Setting("Comet Harbor", "purple mist, silver docks, and colorful signal towers"),
    "settlement": Setting("Little Orbits", "round homes, silver bridges, and gardens under clear roofs"),
}

ROUTES = (
    "take the shortest route",
    "circle the station once before approaching",
    "fly beneath the ring and rise slowly",
    "follow the old delivery lane",
)
SIGNALS = (
    "a red warning",
    "a black arrow",
    "a blinking negative sign",
    "a frowning signal",
)
HELPERS = (
    "ask the children to describe the signal",
    "listen to the families beside the transmitter",
    "watch what the gardeners do with their cups",
    "invite everyone nearby to inspect the beacon",
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A sharing space adventure about Luna and a surprising signal.")
    parser.add_argument("--name", choices=["Luna", "Captain Luna"], default="Luna")
    parser.add_argument("--mission", choices=MISSIONS, default=None)
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
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
        name=args.name,
        seed=args.seed,
        mission=args.mission or rng.choice(list(MISSIONS)),
        setting=args.setting or rng.choice(list(SETTINGS)),
        route=rng.randrange(len(ROUTES)),
        signal=rng.randrange(len(SIGNALS)),
        helper=rng.randrange(len(HELPERS)),
        surprise=rng.randrange(4),
    )


def reasonableness_gate(params: StoryParams, mission: Mission) -> None:
    if not params.name.strip():
        raise StoryError("A space captain needs a name.")
    if params.name not in {"Luna", "Captain Luna"}:
        raise StoryError("This adventure belongs to Luna; use Luna or Captain Luna.")
    if params.mission not in MISSIONS:
        raise StoryError("Unknown mission.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown space setting.")
    if not 0 <= params.route < len(ROUTES):
        raise StoryError("Unknown route.")
    if not 0 <= params.signal < len(SIGNALS):
        raise StoryError("Unknown signal.")
    if not 0 <= params.helper < len(HELPERS):
        raise StoryError("Unknown helper choice.")
    if not 0 <= params.surprise < 4:
        raise StoryError("Unknown surprise ending.")


ASP_RULES = r"""
captain(luna).
mission(seeds; music; water).
feature(sharing).
feature(surprise).
theme(negative).
theme(sociology).
theme(suffice).

valid_adventure(C, M) :-
    captain(C),
    mission(M),
    feature(sharing),
    feature(surprise),
    theme(negative),
    theme(sociology),
    theme(suffice).

#show valid_adventure/2.
#show feature/1.
#show theme/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("captain", "luna"),
        asp.fact("feature", "sharing"),
        asp.fact("feature", "surprise"),
        asp.fact("theme", "negative"),
        asp.fact("theme", "sociology"),
        asp.fact("theme", "suffice"),
    ]
    for mission in MISSIONS:
        lines.append(asp.fact("mission", mission))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_adventure/2."))
    found = set(asp.atoms(model, "valid_adventure"))
    expected = {("luna", mission) for mission in MISSIONS}
    if found != expected:
        print("MISMATCH")
        print("clingo:", sorted(found))
        print("python:", sorted(expected))
        return 1
    print(f"OK: clingo matches Python gate ({len(expected)} adventures).")
    return 0


def build_world(params: StoryParams, mission: Mission, setting: Setting) -> World:
    world = World(setting)
    luna = world.add(Entity("captain", "character", params.name, "captain"))
    cargo = world.add(Entity("cargo", "thing", mission.cargo, "cargo"))
    station = world.add(Entity("station", "place", setting.place, "station"))
    beacon = world.add(Entity("beacon", "thing", "the shared beacon", "beacon"))
    neighbors = world.add(Entity("neighbors", "group", mission.recipient, "community"))

    luna.memes.update({"curiosity": 0.0, "concern": 0.0, "trust": 0.0, "relief": 0.0, "joy": 0.0})
    cargo.meters.update({"safety": 0.8, "needed": 1.0})
    beacon.meters.update({"clarity": 0.2, "danger": 0.0, "repaired": 0.0})
    neighbors.memes.update({"welcome": 0.2, "cooperation": 0.0, "hope": 0.6})

    world.say(f"{params.name} piloted the small ship Starling through the gentle dark of space.")
    world.say(f"She carried {mission.cargo} to {mission.recipient} at {setting.place}.")
    world.say(f"All around her were {setting.detail}.")
    world.para()

    world.say(f"As she prepared to {ROUTES[params.route]}, {SIGNALS[params.signal]} appeared on her screen.")
    world.say(f"{mission.problem.capitalize()}. If she trusted the negative sign, {mission.danger}.")
    world.say(f'"Should I turn back?" Luna asked.')
    world.say(f'"Please wait and talk with us," called a voice from {setting.place}.')
    world.say(f'"We can look together," Luna replied.')
    world.para()

    luna.memes["concern"] = 1.0
    beacon.meters["danger"] = 1.0
    world.say(f"Luna decided to {HELPERS[params.helper]}.")
    world.say(f"The neighbors did not hide from the strange signal. Instead, they showed her how everyone shared the beacon's little control room.")
    world.say(f"Then {mission.clue}.")
    world.say(f"That was the surprising clue: {mission.cause}.")
    world.para()

    luna.memes["curiosity"] = 1.0
    luna.memes["trust"] = 1.0
    neighbors.memes["cooperation"] = 1.0
    world.say(f'"The negative sign is not saying no," Luna explained. "It is asking us to help."')
    world.say(f'"Then let us share what we have," said the neighbors.')
    world.say(f"Luna opened her tool drawer and {mission.fix}.")
    beacon.meters["clarity"] = 1.0
    beacon.meters["danger"] = 0.0
    beacon.meters["repaired"] = 1.0
    cargo.meters["safety"] = 1.0
    neighbors.memes["hope"] = 1.0
    luna.memes["relief"] = 1.0
    luna.memes["joy"] = 1.0
    world.para()

    world.say(f"At once, {mission.resolution}.")
    world.say(mission.endings[params.surprise])
    world.say(f"Luna waved from the Starling, glad that listening together had made enough room for everyone.")
    world.facts.update(
        luna=luna,
        cargo=cargo,
        station=station,
        beacon=beacon,
        neighbors=neighbors,
        mission=mission,
        setting=setting,
        signal=SIGNALS[params.signal],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]  # type: ignore[assignment]
    return [
        "Write a gentle Space Adventure for a young child about Luna, sharing, and a surprise.",
        f"Tell a story in which a negative signal seems dangerous but {mission.cause}.",
        "Show how sociology means people understand a problem by listening and working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            "Who piloted the Starling?",
            "Luna piloted the Starling while carrying an important delivery through space.",
        ),
        QAItem(
            "What negative thing happened?",
            f"{mission.problem.capitalize()} The warning made Luna worry that {mission.danger}.",
        ),
        QAItem(
            "How did Luna learn what the signal meant?",
            f"She listened to the people at {setting.place}. They noticed {mission.clue}, which revealed that {mission.cause}.",
        ),
        QAItem(
            "How did sharing solve the problem?",
            f"Luna shared her tools and worked with the neighbors to {mission.fix}.",
        ),
        QAItem(
            "What was the surprise at the end?",
            f"The surprising truth was that {mission.cause}. After everyone helped, {mission.resolution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does sharing mean?",
            "Sharing means willingly giving or using something together so that more than one person can benefit.",
        ),
        QAItem(
            "What is a surprise in a story?",
            "A surprise is an unexpected change or discovery that makes the ending more interesting.",
        ),
        QAItem(
            "Why can people solve problems together?",
            "People can solve problems together because each person may notice a different clue, skill, or useful idea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(details)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    mission = MISSIONS.get(params.mission)
    if mission is None:
        raise StoryError("Unknown mission.")
    reasonableness_gate(params, mission)
    world = build_world(params, mission, SETTINGS[params.setting])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_adventure/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_adventure/2."))
        print(asp.atoms(model, "valid_adventure"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        index = 0
        for mission_id in MISSIONS:
            for setting_id in SETTINGS:
                rng = random.Random(base_seed + index)
                params = StoryParams(
                    name="Luna",
                    seed=base_seed + index,
                    mission=mission_id,
                    setting=setting_id,
                    route=rng.randrange(len(ROUTES)),
                    signal=rng.randrange(len(SIGNALS)),
                    helper=rng.randrange(len(HELPERS)),
                    surprise=rng.randrange(4),
                )
                samples.append(generate(params))
                index += 1
    else:
        for index in range(max(1, args.n)):
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
