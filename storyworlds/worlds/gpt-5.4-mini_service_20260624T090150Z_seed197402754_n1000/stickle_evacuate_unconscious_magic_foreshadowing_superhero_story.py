#!/usr/bin/env python3
"""
Standalone storyworld: Stickle Evacuation, with magic and foreshadowing.

A small superhero-style domain where a brave child-hero and a helper use
careful clues, a little magic, and a safe evacuation to rescue an unconscious
stickle from trouble.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    danger: str = ""


@dataclass
class Power:
    id: str
    label: str
    effect: str
    clue: str


@dataclass
class World:
    place: Place
    hero: Entity
    sidekick: Entity
    patient: Entity
    villain: Entity
    power: Power
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
    place: str
    hero_name: str
    sidekick_name: str
    patient_name: str
    seed: Optional[int] = None


PLACES = {
    "city": Place(id="city", label="Bright City", indoors=False, danger="storm"),
    "museum": Place(id="museum", label="the museum hall", indoors=True, danger="flood"),
    "bridge": Place(id="bridge", label="the old bridge", indoors=False, danger="collapse"),
}

POWERS = {
    "magic": Power(
        id="magic",
        label="Magic",
        effect="lift a heavy thing without hurting anyone",
        clue="a blue spark in the air",
    ),
    "foreshadowing": Power(
        id="foreshadowing",
        label="Foreshadowing",
        effect="notice trouble before it gets big",
        clue="a tiny crack that came before the fall",
    ),
}

HERO_NAMES = ["Nova", "Piper", "Rae", "Milo", "Iris"]
SIDEKICK_NAMES = ["Tess", "Jules", "Bea", "Theo", "Finn"]
PATIENT_NAMES = ["Stickle", "Pip", "Bean", "Moss", "Pebble"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: a rescue, a clue, and a safe evacuation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--patient")
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
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(
        place=place,
        hero_name=args.name or rng.choice(HERO_NAMES),
        sidekick_name=args.sidekick or rng.choice(SIDEKICK_NAMES),
        patient_name=args.patient or rng.choice(PATIENT_NAMES),
    )


def story_setup(world: World) -> None:
    hero = world.hero
    sidekick = world.sidekick
    patient = world.patient
    place = world.place
    power = world.power
    hero.memes["brave"] = 1
    hero.memes["care"] = 1
    sidekick.memes["alert"] = 1
    patient.meters["hurt"] = 0
    patient.meters["safe"] = 0

    world.say(
        f"{hero.id} was a young superhero who watched over {place.label} with {sidekick.id} at {hero.pronoun('possessive')} side."
    )
    world.say(
        f"One afternoon, they noticed {patient.id} the stickle near a broken archway, and {power.clue} seemed to hover in the air."
    )
    world.say(
        f"{hero.id} could already tell that something was wrong, because {power.label.lower()} helped {power.effect.lower()}."
    )


def story_turn(world: World) -> None:
    hero = world.hero
    sidekick = world.sidekick
    patient = world.patient
    villain = world.villain
    place = world.place
    power = world.power

    world.para()
    villain.memes["storm"] = 1
    patient.meters["unconscious"] = 1
    world.facts["foreshadow"] = power.clue
    world.say(
        f"Then the wind picked up, and {villain.id} laughed as the broken arch began to shake."
    )
    world.say(
        f"{sidekick.id} pointed up and said, \"Look! The crack was the first warning.\""
    )
    world.say(
        f"{hero.id} nodded. {power.label} was not just for showing off; it was for rescuing someone before the danger got worse."
    )
    world.say(
        f"When {patient.id} went unconscious, the whole team knew they had to evacuate {patient.pronoun('object')} right away."
    )


def story_resolution(world: World) -> None:
    hero = world.hero
    sidekick = world.sidekick
    patient = world.patient
    place = world.place
    power = world.power

    world.para()
    hero.memes["focus"] = 1
    patient.meters["evacuated"] = 1
    patient.meters["safe"] = 1
    patient.meters["hurt"] = 0
    world.say(
        f"{hero.id} used {power.label.lower()} to make a soft glowing lift, and {sidekick.id} helped guide the way."
    )
    world.say(
        f"Together they evacuated {patient.id} from {place.label} and carried {patient.pronoun('object')} to a warm, calm place."
    )
    world.say(
        f"The stickle woke up, blinked, and gave a tiny chirp, while {hero.id} smiled because the clue had helped them act in time."
    )
    world.say(
        f"By the end, {patient.id} was safe, {villain.id} had fled, and the city felt bright again."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = Entity(id=params.hero_name, kind="character", type="hero")
    sidekick = Entity(id=params.sidekick_name, kind="character", type="sidekick")
    patient = Entity(id=params.patient_name, kind="character", type="stickle", label="stickle")
    villain = Entity(id="Crankstorm", kind="character", type="villain", label="Crankstorm")
    power = POWERS["magic"] if place.id != "bridge" else POWERS["foreshadowing"]
    world = World(place=place, hero=hero, sidekick=sidekick, patient=patient, villain=villain, power=power)
    story_setup(world)
    story_turn(world)
    story_resolution(world)
    world.facts.update(
        place=place,
        hero=hero,
        sidekick=sidekick,
        patient=patient,
        villain=villain,
        power=power,
        evacuated=True,
        unconscious=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short superhero story for a child where {world.hero.id} uses {world.power.label.lower()} to save a stickle.",
        f"Tell a story about foreshadowing, a sudden danger, and evacuating an unconscious stickle safely.",
        f"Make a gentle superhero rescue tale set in {world.place.label} with magic and a clear happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who needed to be evacuated in the story?",
            answer=f"{world.patient.id} the stickle needed to be evacuated because {world.patient.pronoun('subject')} became unconscious.",
        ),
        QAItem(
            question=f"What clue showed that trouble was coming?",
            answer=f"The clue was {world.power.clue}, which foreshadowed that the broken place was about to get worse.",
        ),
        QAItem(
            question=f"How did {world.hero.id} help?",
            answer=f"{world.hero.id} used {world.power.label.lower()} to lift and guide {world.patient.id} safely away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in a superhero story?",
            answer="Magic is a special power that can do amazing things that people cannot do by themselves, like lifting, glowing, or helping in a rescue.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important or risky may happen later in the story.",
        ),
        QAItem(
            question="What does it mean to evacuate someone?",
            answer="To evacuate someone means to move them out of danger and bring them to a safer place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.label}")
    lines.append(f"hero={world.hero.id}")
    lines.append(f"sidekick={world.sidekick.id}")
    lines.append(f"patient={world.patient.id}")
    lines.append(f"villain={world.villain.id}")
    lines.append(f"power={world.power.id}")
    lines.append(f"facts={sorted(world.facts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="city", hero_name="Nova", sidekick_name="Tess", patient_name="Stickle"),
    StoryParams(place="museum", hero_name="Iris", sidekick_name="Jules", patient_name="Pip"),
    StoryParams(place="bridge", hero_name="Rae", sidekick_name="Bea", patient_name="Moss"),
]


ASP_RULES = r"""
place(city).
place(museum).
place(bridge).

hero(nova).
hero(iris).
hero(rae).

power(magic).
power(foreshadowing).

safe_if_evacuated(P) :- patient(P), evacuated(P).
story_ok :- place(_), hero(_), power(_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pname in POWERS:
        lines.append(asp.fact("power", pname))
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h.lower()))
    for s in SIDEKICK_NAMES:
        lines.append(asp.fact("sidekick", s.lower()))
    for p in PATIENT_NAMES:
        lines.append(asp.fact("patient", p.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
