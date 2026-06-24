#!/usr/bin/env python3
"""
storyworlds/worlds/various_madden_aspirator_subway_station_surprise_lesson.py
==============================================================================

A small ghost-story storyworld set in a subway station.

Seed tale idea:
- A child waits in a subway station after dark.
- An old aspirator starts humming near a locked service door.
- A surprising ghost appears, and the child learns a lesson about listening.
- If the child ignores the warning, the ending is bad: the station grows colder,
  the wrong door opens, and the child gets separated in the noise.

This world keeps a gentle ghost-story tone: dim lights, echoing footsteps, a
surprise reveal, a lesson learned, and a bad ending variant when caution fails.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    place: str = "the subway station"
    platform: str = "Platform 2"
    terminal: bool = True


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    region: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    helps: set[str]
    blocks: set[str]
    action: str
    result: str


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.eerie: float = 0.0
        self.noise: float = 0.0
        self.dimness: float = 0.0
        self.open_door: bool = False
        self.bad_end: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.station)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.eerie = self.eerie
        c.noise = self.noise
        c.dimness = self.dimness
        c.open_door = self.open_door
        c.bad_end = self.bad_end
        return c


def _r_eerie(world: World) -> list[str]:
    out = []
    if world.eerie < THRESHOLD:
        return out
    if ("eerie",) in world.fired:
        return out
    world.fired.add(("eerie",))
    world.dimness += 1
    out.append("The lights looked thinner, as if the station itself were holding its breath.")
    return out


def _r_door(world: World) -> list[str]:
    out = []
    if world.open_door or world.noise < THRESHOLD or world.dimness < THRESHOLD:
        return out
    if ("door",) in world.fired:
        return out
    world.fired.add(("door",))
    world.open_door = True
    out.append("A service door at the end of the platform gave a small, creaking sigh.")
    return out


def _r_bad_end(world: World) -> list[str]:
    out = []
    if world.bad_end or not world.open_door:
        return out
    if ("bad_end",) in world.fired:
        return out
    world.fired.add(("bad_end",))
    world.bad_end = True
    out.append("Cold air slid out, and the brave feeling in the station slipped away.")
    return out


CAUSAL_RULES = [
    _r_eerie,
    _r_door,
    _r_bad_end,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def character_intro(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    return f"{hero.id} was a little {trait} child who noticed odd sounds others missed."


def setting_intro(station: Station) -> str:
    return f"The {station.place} was bright in spots and dark in others, with echoes under {station.platform}."


def surprise_line(hero: Entity, guide: Entity) -> str:
    return (
        f"Then the surprise came: the whisper near the tracks belonged to {guide.label}, "
        f"a ghost with a soft voice and a coat that never quite touched the floor."
    )


def lesson_line(hero: Entity, guide: Entity) -> str:
    return (
        f"{guide.label} told {hero.id} that in a station, it was wise to stay close, "
        f"listen first, and never chase a strange sound alone."
    )


def bad_ending_line(hero: Entity) -> str:
    return (
        f"But {hero.id} did not listen fast enough, and when the door sighed open, "
        f"{hero.pronoun('subject').capitalize()} was left staring into the cold dark."
    )


def resolve_line(hero: Entity) -> str:
    return (
        f"In the end, the station remembered the lesson: a careful step can be safer "
        f"than a rushed one."
    )


def use_aspirator(world: World, hero: Entity, device: Device) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.noise += 1
    world.eerie += 1
    world.say(
        f"{hero.id} found {device.phrase} by the bench and pressed {device.pronoun('object')} on."
        if hasattr(device, "pronoun") else
        f"{hero.id} found {device.phrase} by the bench and pressed it on."
    )
    propagate(world, narrate=True)


def ask_lesson(hero: Entity, guide: Entity) -> None:
    hero.memes["listening"] = hero.memes.get("listening", 0) + 1


def tell_world(hero_name: str = "Mina", hero_type: str = "girl",
               trait: str = "curious") -> World:
    station = Station()
    world = World(station)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        label="a pale station ghost",
        traits=["gentle", "old"],
    ))
    aspirator = world.add(Entity(
        id="Aspirator",
        type="device",
        label="the aspirator",
        phrase="an old aspirator with a rattling hose",
    ))

    world.say(character_intro(hero))
    world.say(setting_intro(station))
    world.say(
        f"On the bench sat {aspirator.phrase}, and {hero.id} could not stop wondering "
        f"why anyone would leave a machine like that in a subway station."
    )

    world.para()
    world.say(
        f"{hero.id} leaned closer, and the aspirator gave a tiny hum as if it had woken up."
    )
    use_aspirator(world, hero, aspirator)
    world.say(surprise_line(hero, ghost))
    world.say(lesson_line(hero, ghost))
    ask_lesson(hero, ghost)

    world.para()
    if world.open_door:
        world.say(bad_ending_line(hero))
        world.say(
            f"The bad ending was not a monster bite or a scream; it was the feeling of "
            f"being too far from help when the echo got loud."
        )
    else:
        world.say(
            f"{hero.id} stepped back, held still, and listened until the station was quiet again."
        )
        world.say(resolve_line(hero))

    world.facts.update(
        hero=hero,
        ghost=ghost,
        aspirator=aspirator,
        station=station,
        bad_end=world.bad_end,
        open_door=world.open_door,
    )
    return world


STATION_REGISTRY = {
    "subway_station": Station(),
}

DEVICE_REGISTRY = {
    "aspirator": Device(
        id="aspirator",
        label="aspirator",
        phrase="an old aspirator with a rattling hose",
        helps={"clean", "suck", "noise"},
        blocks={"dust"},
        action="turn it on",
        result="made the air shiver",
    ),
}

GHOST_REGISTRY = {
    "ghost": "a pale station ghost",
}

TRAITS = ["curious", "brave", "careful", "quiet", "restless"]
NAMES = ["Mina", "Theo", "Lena", "Owen", "Iris", "Noah"]


@dataclass
class StoryParams:
    station: str
    device: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("station", "subway_station"))
    lines.append(asp.fact("device", "aspirator"))
    lines.append(asp.fact("helps", "aspirator", "noise"))
    lines.append(asp.fact("blocks", "aspirator", "dust"))
    lines.append(asp.fact("ghostly", "ghost"))
    lines.append(asp.fact("theme", "surprise"))
    lines.append(asp.fact("theme", "lesson_learned"))
    lines.append(asp.fact("theme", "bad_ending"))
    return "\n".join(lines)


ASP_RULES = r"""
% If a child turns on the aspirator in the subway station, the station becomes eerie.
eerie(station) :- device(aspirator), theme(surprise), theme(bad_ending).

% A surprise is possible when the station is eerie and a ghost is present.
surprise(station) :- eerie(station), ghostly(ghost).

% A lesson is learned when the ghost warns the child.
lesson_learned(station) :- surprise(station).

% A bad ending is possible when the child ignores the warning.
bad_ending(station) :- lesson_learned(station).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story subway station world with a surprise, a lesson, and a bad ending."
    )
    ap.add_argument("--station", choices=STATION_REGISTRY.keys())
    ap.add_argument("--device", choices=DEVICE_REGISTRY.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    station = args.station or "subway_station"
    device = args.device or "aspirator"
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(station=station, device=device, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params.name, params.gender, params.trait)
    prompts = [
        'Write a short ghost story set in a subway station with an old aspirator.',
        f"Tell a spooky-but-gentle story about {params.name} discovering a surprising ghost and learning a lesson.",
        "Write a child-facing story with a surprise, a lesson learned, and a bad ending if the warning is ignored.",
    ]
    story_qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {params.name}, a little {params.trait} child in a subway station.",
        ),
        QAItem(
            question="What was the surprise in the story?",
            answer="The surprise was that the whisper by the tracks belonged to a ghost in the station.",
        ),
        QAItem(
            question="What lesson did the ghost give?",
            answer="The ghost said to stay close, listen first, and never chase strange sounds alone.",
        ),
        QAItem(
            question="What made the ending bad?",
            answer="The ending was bad because the child did not listen fast enough, and the door opened into cold dark space.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a subway station?",
            answer="A subway station is a place underground or partly underground where people wait for trains.",
        ),
        QAItem(
            question="What does an aspirator do?",
            answer="An aspirator sucks air or dust through a hose, like an old cleaning machine.",
        ),
        QAItem(
            question="Why can dark stations feel spooky?",
            answer="Dark stations can feel spooky because echoes, shadows, and quiet places make small sounds seem bigger.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"station={world.station.place} platform={world.station.platform}")
    lines.append(f"eerie={world.eerie} noise={world.noise} dimness={world.dimness}")
    lines.append(f"open_door={world.open_door} bad_end={world.bad_end}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise/1.\n#show lesson_learned/1.\n#show bad_ending/1."))
    atoms = {str(sym) for sym in model}
    expected = {"surprise(station)", "lesson_learned(station)", "bad_ending(station)"}
    if atoms >= expected:
        print("OK: ASP rules derive the expected ghost-story phases.")
        return 0
    print("MISMATCH in ASP derivation.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(station="subway_station", device="aspirator", name="Mina", gender="girl", trait="curious"),
    StoryParams(station="subway_station", device="aspirator", name="Theo", gender="boy", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show surprise/1.\n#show lesson_learned/1.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show surprise/1.\n#show lesson_learned/1.\n#show bad_ending/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
