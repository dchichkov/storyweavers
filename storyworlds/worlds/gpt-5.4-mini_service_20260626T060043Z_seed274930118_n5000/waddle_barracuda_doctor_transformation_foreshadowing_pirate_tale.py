#!/usr/bin/env python3
"""
A small pirate tale storyworld about a waddling sailor, a barracuda hint in the
waves, and a doctor who helps after a strange transformation.
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


# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    deck: str = "the ship"
    sea: str = "the reef"
    hero: str = "Milo"
    companion: str = "Captain Brine"
    doctor: str = "Doctor Salt"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "boy", "captain", "doctor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

WADDLE = "waddle"
BARRACUDA = "barracuda"
DOCTOR = "doctor"

SETTINGS = {
    "ship": "the ship",
    "dock": "the dock",
    "reef": "the reef",
    "cove": "the quiet cove",
}

HERO_NAMES = ["Milo", "Ned", "Pip", "Toby", "Jory", "Finn"]
DOCTOR_NAMES = ["Doctor Salt", "Doctor Cove", "Doctor Pearl"]
CAPTAIN_NAMES = ["Captain Brine", "Captain Wave", "Captain Reef"]

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def foreshadow(world: World, hero: Entity, sea_name: str) -> None:
    world.say(
        f"At {sea_name}, {hero.id} kept a little jar of shiny sea glass in {hero.pronoun('possessive')} pocket."
    )
    world.say(
        f"It rattled whenever a silver fin flashed nearby, and the crew said that was a warning from the water."
    )


def setup(world: World, hero: Entity, captain: Entity, doctor: Entity, sea_name: str) -> None:
    hero.memes["curious"] = 1
    captain.memes["watchful"] = 1
    doctor.memes["calm"] = 1
    world.say(
        f"{hero.id} was a small pirate who could only {WADDLE} well on the deck after long days at sea."
    )
    world.say(
        f"{hero.pronoun().capitalize()} served under {captain.id}, who liked brave plans and loud maps."
    )
    world.say(
        f"The crew also knew {doctor.id}, a kind {doctor.type} who carried bandages, herbs, and a steady lantern."
    )
    foreshadow(world, hero, sea_name)


def turn(world: World, hero: Entity, captain: Entity, sea_name: str) -> None:
    hero.memes["hope"] = 1
    world.para()
    world.say(
        f"One foggy evening, the ship drifted close to {sea_name}, where the water went dark and quick."
    )
    world.say(
        f"{hero.id} climbed the rail to look, and a hungry {BARRACUDA} broke the surface like a silver knife."
    )
    world.say(
        f"The crew gasped, because the fish's sharp grin matched the old warning from the sea glass jar."
    )
    world.say(
        f"{captain.id} shouted that no one should lean too far overboard, but a sudden wave still slapped the deck."
    )
    hero.meters["sea_magic"] = 1
    hero.memes["fear"] = 1


def transform(world: World, hero: Entity) -> None:
    world.para()
    hero.meters["transformed"] = 1
    hero.type = "barracuda"
    hero.label = BARRACUDA
    hero.memes["surprise"] = 1
    world.say(
        f"The wave touched {hero.id}, and with a puff of bright spray, {hero.id} changed into a {BARRACUDA}."
    )
    world.say(
        f"{hero.id} no longer {WADDLE}d on deck; now {hero.pronoun()} could dart through the water with a flick of {hero.pronoun('possessive')} tail."
    )
    world.say(
        f"The crew stared, for the worst of the storm had turned their pirate into a sea creature."
    )


def doctor_help(world: World, hero: Entity, doctor: Entity) -> None:
    world.para()
    doctor.memes["care"] = 1
    hero.memes["hope"] = 2
    world.say(
        f"{doctor.id} knelt by the rail and smiled. 'This looks like a tide trick, not a true curse,' {doctor.pronoun()} said."
    )
    world.say(
        f"{doctor.id} rubbed salt herbs on a cloth, tied it to the mast, and told {hero.id} to swim three slow circles around the ship."
    )
    world.say(
        f"With each circle, the shiny fish shape grew softer, as if the sea itself was letting go."
    )
    hero.meters["transformed"] = 0
    hero.type = "boy"
    hero.label = "boy"
    hero.memes["fear"] = 0
    hero.memes["joy"] = 2
    world.say(
        f"Then {hero.id} blinked, coughed out a mouthful of seawater, and was a pirate child again."
    )
    world.say(
        f"{doctor.id} laughed and said the sea likes to warn before it bites, and that is why careful sailors listen."
    )


def resolution(world: World, hero: Entity, captain: Entity, doctor: Entity) -> None:
    world.para()
    world.say(
        f"After that, {hero.id} kept the sea glass jar on {hero.pronoun('possessive')} belt."
    )
    world.say(
        f"When the water shimmered silver, the crew slowed down, and nobody leaned over the edge too far."
    )
    world.say(
        f"{captain.id} called it good pirate sense, and {doctor.id} called it a lesson learned before the next storm."
    )
    world.say(
        f"By morning, {hero.id} was back to {WADDLE}ing across the deck, smiling at the waves instead of fearing them."
    )


def tell(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(id=params.hero, kind="character", type="boy"))
    captain = world.add(Entity(id=params.companion, kind="character", type="captain"))
    doctor = world.add(Entity(id=params.doctor, kind="character", type="doctor"))

    setup(world, hero, captain, doctor, params.sea)
    turn(world, hero, captain, params.sea)
    transform(world, hero)
    doctor_help(world, hero, doctor)
    resolution(world, hero, captain, doctor)

    world.facts.update(
        hero=hero,
        captain=captain,
        doctor=doctor,
        sea=params.sea,
        transformed=hero.meters.get("transformed", 0) > 0,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a pirate tale for a young child that includes {WADDLE}, a {BARRACUDA}, and a {DOCTOR}.",
        f"Tell a short story where {p.hero} sees a {BARRACUDA} at {p.sea} and a {DOCTOR} helps after a strange change.",
        f"Make a gentle pirate story with foreshadowing, a transformation, and a happy ending on {p.deck}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    doctor: Entity = f["doctor"]
    sea = f["sea"]
    return [
        QAItem(
            question=f"Why did the crew pay attention to the shiny sea glass before the wave hit?",
            answer="Because it was a bit of foreshadowing. The glass rattled when a silver fin flashed nearby, warning them that something strange could happen in the water.",
        ),
        QAItem(
            question=f"What happened to {hero.id} when the wave touched them near {sea}?",
            answer=f"{hero.id} changed into a {BARRACUDA} for a while, so {hero.id} could not {WADDLE} on the deck anymore.",
        ),
        QAItem(
            question=f"How did {doctor.id} help {hero.id} become a pirate child again?",
            answer=f"{doctor.id} used salt herbs, tied them to the mast, and told {hero.id} to swim slow circles until the strange transformation faded.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end of the story?",
            answer=f"{hero.id} was back to {WADDLE}ing across the deck and smiling at the waves, because the crew had learned to watch for the warning signs.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barracuda?",
            answer="A barracuda is a long, fast sea fish with sharp teeth and a sleek body.",
        ),
        QAItem(
            question="What does a doctor do?",
            answer="A doctor helps people feel better when they are hurt, sick, or in trouble.",
        ),
        QAItem(
            question="What does it mean to waddle?",
            answer="To waddle means to walk with short, wobbly steps from side to side.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
#show warning/2.

valid(S, H) :- setting(S), hero(H), foreshadows(S, H), sea(S), doctor_present(S).

warning(S, H) :- valid(S, H), sees_barracuda(S, H), transforms(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        lines.append(asp.fact("sea", s))
        lines.append(asp.fact("foreshadows", s, "hero"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("doctor_present", "any"))
    lines.append(asp.fact("sees_barracuda", "any", "hero"))
    lines.append(asp.fact("transforms", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_valid = {(s, "hero") for s in SETTINGS}
    clingo_valid = set(asp_valid())
    if clingo_valid == python_valid:
        print(f"OK: clingo gate matches python gate ({len(clingo_valid)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo-only:", sorted(clingo_valid - python_valid))
    print("  python-only:", sorted(python_valid - clingo_valid))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with foreshadowing and transformation.")
    ap.add_argument("--deck", choices=SETTINGS.keys())
    ap.add_argument("--sea", choices=SETTINGS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--companion", choices=CAPTAIN_NAMES)
    ap.add_argument("--doctor", choices=DOCTOR_NAMES)
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
    deck = args.deck or rng.choice(list(SETTINGS.keys()))
    sea = args.sea or deck
    if deck not in SETTINGS or sea not in SETTINGS:
        raise StoryError("Unknown setting.")
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice(CAPTAIN_NAMES)
    doctor = args.doctor or rng.choice(DOCTOR_NAMES)
    return StoryParams(deck=SETTINGS[deck], sea=SETTINGS[sea], hero=hero, companion=companion, doctor=doctor)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid story patterns:")
        for s, h in vals:
            print(f"  {s} / {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for deck in SETTINGS:
            params = StoryParams(deck=SETTINGS[deck], sea=SETTINGS[deck], hero="Milo", companion="Captain Brine", doctor="Doctor Salt")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
