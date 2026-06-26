#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Space Adventure tale:
a ninetieth mission, a genetic sample, a humorous dialogue, and a flashback
that explains why the ending matters.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Location:
    id: str
    label: str
    kind: str
    detail: str


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    owner: str = ""
    state: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Character:
    id: str
    label: str
    role: str
    pronoun: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    location: Location
    pilot: Character
    companion: Character
    artifact: ObjectThing
    ship: ObjectThing
    hazard: str
    humor: str
    flashback_reason: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    location: str
    hazard: str
    sample: str
    pilot_name: str
    companion_name: str
    seed: Optional[int] = None


LOCATIONS = {
    "orbital_lab": Location(
        id="orbital_lab",
        label="the orbital lab",
        kind="station",
        detail="The lab windows glowed with blue Earth-light, and instruments hummed softly.",
    ),
    "moon_base": Location(
        id="moon_base",
        label="the moon base",
        kind="base",
        detail="The base sat under a silver dome, with dust drifting like glitter outside.",
    ),
    "asteroid_deck": Location(
        id="asteroid_deck",
        label="the asteroid deck",
        kind="station",
        detail="The deck was narrow and bright, with cables floating beside the railings.",
    ),
}

HAZARDS = {
    "micro_meteor": "a micro-meteor shower",
    "power_blink": "a power blink in the main ring",
    "drift_alarm": "a drifting cargo crate",
}

SAMPLES = {
    "fern_dna": ObjectThing(
        id="fern_dna",
        label="the genetic sample",
        phrase="a sealed box of fern DNA",
        kind="sample",
        state="sealed",
    ),
    "starflower_genes": ObjectThing(
        id="starflower_genes",
        label="the genetic sample",
        phrase="a tiny vial of starflower genes",
        kind="sample",
        state="sealed",
    ),
    "lunar_spores": ObjectThing(
        id="lunar_spores",
        label="the genetic sample",
        phrase="a glass capsule of lunar spores",
        kind="sample",
        state="sealed",
    ),
}

HUMORS = [
    "The ship's snack printer kept offering soup labeled 'not soup,' which made everyone laugh.",
    "A sleepy repair drone rolled by wearing a sticker that said 'Do not wake me before orbit.'",
    "The navigation screen briefly called the moon 'a nearby very round problem,' and that seemed fair.",
]

FLASBACKS = [
    "He remembered the first mission, when a tiny mistake had turned a clean sample into a floating mess.",
    "She flashed back to the day the captain said careful hands mattered more than fast hands in space.",
    "They both remembered a training drill where a cracked seal had taught them to slow down and check twice.",
]

PILOT_NAMES = ["Mara", "Tess", "Jun", "Ivo", "Rin", "Lio", "Nova", "Zed"]
COMPANION_NAMES = ["Pip", "Echo", "Milo", "Suri", "Bo", "Kai", "Luna", "Orin"]


class StoryWorld:
    def __init__(self, world: World) -> None:
        self.world = world
        self.fired: set[str] = set()

    def update(self) -> None:
        w = self.world
        if w.hazard == "micro_meteor":
            w.ship.meters["shield_stress"] = w.ship.meters.get("shield_stress", 0.0) + 1.0
            w.pilot.memes["focus"] = w.pilot.memes.get("focus", 0.0) + 1.0
        elif w.hazard == "power_blink":
            w.ship.meters["power"] = w.ship.meters.get("power", 2.0) - 1.0
            w.companion.memes["worry"] = w.companion.memes.get("worry", 0.0) + 1.0
        elif w.hazard == "drift_alarm":
            w.ship.meters["motion"] = w.ship.meters.get("motion", 0.0) + 1.0
            w.artifact.meters["risk"] = w.artifact.meters.get("risk", 0.0) + 1.0

    def resolve(self) -> None:
        w = self.world
        if w.hazard == "micro_meteor":
            w.ship.state = "shielded"
            w.artifact.state = "safe"
        elif w.hazard == "power_blink":
            w.ship.state = "rerouted"
            w.artifact.state = "safe"
        else:
            w.ship.state = "anchored"
            w.artifact.state = "safe"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with humor, dialogue, and flashback.")
    ap.add_argument("--location", choices=sorted(LOCATIONS))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--sample", choices=sorted(SAMPLES))
    ap.add_argument("--pilot-name")
    ap.add_argument("--companion-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    location = args.location or rng.choice(list(LOCATIONS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    sample = args.sample or rng.choice(list(SAMPLES))
    pilot_name = args.pilot_name or rng.choice(PILOT_NAMES)
    companion_name = args.companion_name or rng.choice(COMPANION_NAMES)
    return StoryParams(location=location, hazard=hazard, sample=sample, pilot_name=pilot_name, companion_name=companion_name)


def _build_world(params: StoryParams) -> World:
    loc = LOCATIONS[params.location]
    hazard = HAZARDS[params.hazard]
    sample = dataclasses.replace(SAMPLES[params.sample])
    pilot = Character(id="pilot", label=params.pilot_name, role="pilot", pronoun="she")
    companion = Character(id="companion", label=params.companion_name, role="engineer", pronoun="they")
    ship = ObjectThing(id="ship", label="the ship", phrase="the old silver ship", kind="ship", state="unsteady")
    sample.owner = pilot.label
    w = World(
        location=loc,
        pilot=pilot,
        companion=companion,
        artifact=sample,
        ship=ship,
        hazard=hazard,
        humor=random.choice(HUMORS),
        flashback_reason=random.choice(FLASBACKS),
    )
    return w


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    sim = StoryWorld(world)

    w = world
    w.say(
        f"{w.pilot.label} was ready for the ninetieth mission, and {w.companion.label} grinned beside the console."
    )
    w.say(
        f"They had to carry {w.artifact.phrase} through {w.location.label}, where {w.location.detail.lower()}"
    )
    w.say(f"{w.companion.label} said, “If this one counts as easy, I hope the universe is listening.”")
    w.say(f"{w.pilot.label} laughed. “The universe never listens. It only tests our helmets.”")
    w.say(w.humor)

    w.para()
    w.say(f"Then {w.hazard} arrived, and the ship gave a worried little shudder.")
    w.say(f"{w.companion.label} pointed at the controls. “Bad news. Good news. The bad news is obvious.”")
    w.say(f"{w.pilot.label} answered, “The good news is we are experts at obvious bad news.”")
    w.say(f"That joke worked because everyone was tense, and nobody wanted to admit it first.")

    w.para()
    w.say(f"{w.pilot.label} looked at the sample and had a flashback.")
    w.say(w.flashback_reason)
    w.say(f"That memory made her slow down, seal the case, and route power through the backup spine.")
    sim.update()
    sim.resolve()

    w.say(
        f"With careful hands, {w.pilot.label} and {w.companion.label} steadied the cargo, and the ship stopped trembling."
    )
    w.say(
        f'“See?” {w.companion.label} said. “Ninetieth try, and we finally get the dramatic part in the right order.”'
    )
    w.say(
        f"{w.pilot.label} smiled as {w.artifact.phrase} stayed safe, and the ship glided on under the bright station lights."
    )

    w.facts.update(
        params=params,
        location=w.location,
        hazard=w.hazard,
        sample=w.artifact,
        pilot=w.pilot,
        companion=w.companion,
        resolved=True,
    )

    prompts = [
        "Write a short Space Adventure story about a ninetieth mission, a genetic sample, and a funny rescue.",
        f"Tell a child-friendly spaceship story where {params.pilot_name} and {params.companion_name} protect a genetic sample from danger.",
        "Write a playful space tale with dialogue and a flashback that helps solve the problem.",
    ]

    story_qa = [
        QAItem(
            question=f"Why were {w.pilot.label} and {w.companion.label} careful with the sample?",
            answer=f"They were carrying {w.artifact.phrase} through {w.location.label}, and the hazard could have damaged it, so careful hands were the safest choice.",
        ),
        QAItem(
            question=f"What made {w.pilot.label} remember the flashback?",
            answer=f"The danger on the ninetieth mission reminded her of an earlier mistake, so she thought about the lesson before acting.",
        ),
        QAItem(
            question=f"How did the story end for {w.artifact.label}?",
            answer=f"It stayed safe, because {w.pilot.label} and {w.companion.label} used the backup system and steadied the cargo in time.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a genetic sample?",
            answer="A genetic sample is a tiny bit of living material, like DNA or spores, that scientists study to learn about how something grows or survives.",
        ),
        QAItem(
            question="Why do spaceships need backup systems?",
            answer="Spaceships need backup systems because space is risky, and a backup can keep lights, air, or power working if the main system has trouble.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly shows something that happened earlier, so the reader understands why a character acts a certain way now.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for obj in [world.ship, world.artifact]:
        lines.append(f"{obj.id}: state={obj.state} meters={obj.meters} memes={obj.memes}")
    lines.append(f"pilot={world.pilot.label} memes={world.pilot.memes} meters={world.pilot.meters}")
    lines.append(f"companion={world.companion.label} memes={world.companion.memes} meters={world.companion.meters}")
    lines.append(f"location={world.location.label}")
    lines.append(f"hazard={world.hazard}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    return "\n".join(
        [
            "location(orbital_lab).",
            "location(moon_base).",
            "location(asteroid_deck).",
            "hazard(micro_meteor).",
            "hazard(power_blink).",
            "hazard(drift_alarm).",
            "sample(fern_dna).",
            "sample(starflower_genes).",
            "sample(lunar_spores).",
        ]
    )


ASP_RULES = r"""
safe(Loc, Sample) :- location(Loc), sample(Sample).
story(Loc, Haz, Sample) :- location(Loc), hazard(Haz), sample(Sample), safe(Loc, Sample).
#show story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    return 0


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
        print(asp_program("#show story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("orbital_lab", "micro_meteor", "fern_dna", "Mara", "Pip"),
            StoryParams("moon_base", "power_blink", "starflower_genes", "Tess", "Echo"),
            StoryParams("asteroid_deck", "drift_alarm", "lunar_spores", "Jun", "Milo"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
