#!/usr/bin/env python3
"""
A small space-adventure storyworld about belief, penicillin, woe, kindness, and
foreshadowing.

Seed premise:
- A young crew member hears a strange distress signal.
- Someone on the ship is aching with woe and needs penicillin.
- The crew follows the sounds, notices foreshadowing clues, and chooses kindness.
- Belief in the signal turns into action, and the ship ends in a hopeful image.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    ship: str
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

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

    def log(self, text: str) -> None:
        self.trace.append(text)


@dataclass
class StoryParams:
    ship: str
    planet: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    patient_name: str
    patient_type: str
    symptom: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SHIP_NAMES = ["Star Kite", "Blue Comet", "Silver Finch", "Orbit Lantern"]
PLANETS = ["Aster-9", "Morrow", "Luma Belt", "Cinder Moon"]
HERO_NAMES = ["Nova", "Pip", "Zia", "Rook", "Mira", "Sol", "Tavi"]
HELPER_NAMES = ["Captain Jo", "Ari", "Bea", "Lio"]
PATIENT_NAMES = ["Bean", "Tiko", "Nell", "Puck"]

SYMPTOMS = {
    "ache": "a dull ache",
    "fever": "a hot fever",
    "cough": "a rattling cough",
    "woe": "a big bundle of woe",
}

SOUND_EFFECTS = {
    "signal": "beep-beep",
    "door": "hissss",
    "scanner": "whirr",
    "footsteps": "tap tap tap",
    "craft": "zoom",
    "medicine": "plink",
    "relief": "phew",
}

# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity, patient: Entity) -> None:
    world.say(
        f"On the starship {world.ship}, {hero.id} listened for trouble while the stars slid by like silver sparks."
    )
    world.say(
        f"{helper.id} was kind and calm, and {patient.id} was trying to smile through {world.facts['symptom_text']}."
    )
    world.log("setup: crew introduced")


def foreshadow(world: World) -> None:
    world.say(
        f"Near the med cabinet, a tiny red light blinked {SOUND_EFFECTS['signal']}, {SOUND_EFFECTS['signal']}, {SOUND_EFFECTS['signal']}."
    )
    world.say(
        "The blinking light felt like a clue waiting to be noticed."
    )
    world.log("foreshadow: red light blinked")


def distress(world: World, patient: Entity) -> None:
    patient.memes["woe"] = 1.0
    world.say(
        f"Then {patient.id} made a small {SOUND_EFFECTS['door']} of a groan, because {world.facts['symptom_text']} would not go away."
    )
    world.say(
        f"{patient.pronoun().capitalize()} looked tired and tiny in the moon-white cabin."
    )
    world.log("distress: patient in woe")


def belief(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["belief"] = 1.0
    world.say(
        f"{hero.id} believed the blinking light meant they should hurry, even before anyone said why."
    )
    world.say(
        f"{helper.id} nodded, because sometimes belief was the first helpful tool on a ship."
    )
    world.log("belief: hero trusted the clue")


def search_and_find(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"They hurried down the corridor with {SOUND_EFFECTS['footsteps']} and a soft {SOUND_EFFECTS['scanner']} from the wall panel."
    )
    world.say(
        f"Behind the panel, a silver case sat exactly where the foreshadowing had pointed."
    )
    world.log("search: case found")


def give_penicillin(world: World, helper: Entity, patient: Entity) -> None:
    patient.meters["medicine"] = 1.0
    world.say(
        f"{helper.id} opened the silver case with a careful {SOUND_EFFECTS['door']} and found penicillin inside."
    )
    world.say(
        f"With a gentle hand, {helper.id} gave the medicine to {patient.id}, and the tiny cup went {SOUND_EFFECTS['medicine']} against the tray."
    )
    world.log("medicine: penicillin given")


def kindness_turn(world: World, hero: Entity, helper: Entity, patient: Entity) -> None:
    hero.memes["kindness"] = 1.0
    helper.memes["kindness"] = 1.0
    patient.memes["hope"] = 1.0
    world.say(
        f"{hero.id} sat beside {patient.id} and held {patient.pronoun('possessive')} hand until the shaking stopped."
    )
    world.say(
        f"That kindness made the cabin feel warm, even with the cold stars outside."
    )
    world.log("kindness: hand held")


def resolution(world: World, patient: Entity) -> None:
    patient.meters["medicine"] = 2.0
    patient.memes["woe"] = 0.0
    world.say(
        f"After a little while, {patient.id} blinked and sighed {SOUND_EFFECTS['relief']}."
    )
    world.say(
        f"{patient.id}'s woe grew smaller, and the starship felt like a safer place again."
    )
    world.log("resolution: relief arrived")


def tell(world: World, hero: Entity, helper: Entity, patient: Entity) -> World:
    introduce(world, hero, helper, patient)
    world.para()
    foreshadow(world)
    distress(world, patient)
    world.para()
    belief(world, hero, helper)
    search_and_find(world, hero, helper)
    give_penicillin(world, helper, patient)
    kindness_turn(world, hero, helper, patient)
    world.para()
    resolution(world, patient)
    world.say(
        f"At last, the ship drifted on through the dark, and the little red light did not seem scary anymore."
    )
    world.facts.update(hero=hero, helper=helper, patient=patient)
    return world


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------

def valid_combo(params: StoryParams) -> bool:
    if params.hero_name == params.patient_name:
        return False
    return True


ASP_RULES = r"""
% Facts are emitted from registries.
different(H, P) :- hero(H), patient(P), H != P.
valid_story(H, P) :- hero(H), patient(P), different(H, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SHIP_NAMES:
        lines.append(asp.fact("shipname", s))
    for p in PLANETS:
        lines.append(asp.fact("planet", p))
    for n in HERO_NAMES:
        lines.append(asp.fact("hero", n))
    for n in HELPER_NAMES:
        lines.append(asp.fact("helper", n))
    for n in PATIENT_NAMES:
        lines.append(asp.fact("patient", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set()
    for h in HERO_NAMES:
        for p in PATIENT_NAMES:
            if h != p:
                python_set.add((h, p))
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not valid_combo(params):
        raise StoryError("The hero and patient must be different people.")
    world = World(ship=params.ship, location=params.planet)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    patient = world.add(Entity(id=params.patient_name, kind="character", type=params.patient_type))
    world.facts["symptom_text"] = SYMPTOMS[params.symptom]
    world.facts["symptom"] = params.symptom
    tell(world, hero, helper, patient)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    patient = f["patient"].id
    symptom = f["symptom"]
    return [
        f"Write a short space adventure where {hero} believes a clue on the ship and helps {patient} find penicillin.",
        f"Tell a child-friendly story about kindness, foreshadowing, and a {symptom} on starship {world.ship}.",
        f"Write a gentle outer-space tale with a blinking signal, a medicine case, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    patient = f["patient"].id
    symptom = f["symptom_text"]
    ship = world.ship
    return [
        QAItem(
            question=f"What ship is the story set on?",
            answer=f"The story is set on the starship {ship}, where the crew listened for trouble and followed clues.",
        ),
        QAItem(
            question=f"Why did {patient} feel woe?",
            answer=f"{patient} felt woe because {symptom} would not go away, and the patient looked tired and small.",
        ),
        QAItem(
            question=f"What clue foreshadowed the medicine?",
            answer=f"A tiny red light blinked beep-beep, beep-beep, beep-beep near the med cabinet, hinting that help was nearby.",
        ),
        QAItem(
            question=f"How did {hero} show belief?",
            answer=f"{hero} believed the blinking light meant they should hurry, so they listened and went to look for the clue.",
        ),
        QAItem(
            question=f"What medicine helped {patient}?",
            answer=f"Penicillin helped {patient}, and the helper gave it carefully in the silver case.",
        ),
        QAItem(
            question=f"How did kindness change the ending?",
            answer=f"{hero} sat beside {patient} and held {patient}'s hand, and that kindness helped the cabin feel safe again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue early so readers can guess that something important may happen later.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, comfort, or care about someone else in a gentle way.",
        ),
        QAItem(
            question="Why do sound effects make a story fun?",
            answer="Sound effects like beep-beep or hissss help readers imagine what the ship, doors, and machines sound like.",
        ),
        QAItem(
            question="What is penicillin?",
            answer="Penicillin is a kind of medicine that can help some people get better when they are sick.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} ({e.type:9}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    lines.append(f"  trace: {world.trace}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with belief, penicillin, woe, kindness, and foreshadowing.")
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--planet", choices=PLANETS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--patient-name", choices=PATIENT_NAMES)
    ap.add_argument("--hero-type", choices=["boy", "girl", "pilot", "captain"], default="boy")
    ap.add_argument("--helper-type", choices=["boy", "girl", "pilot", "captain"], default="captain")
    ap.add_argument("--patient-type", choices=["boy", "girl", "pilot", "captain"], default="boy")
    ap.add_argument("--symptom", choices=sorted(SYMPTOMS))
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
    ship = args.ship or rng.choice(SHIP_NAMES)
    planet = args.planet or rng.choice(PLANETS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    patient_name = args.patient_name or rng.choice(PATIENT_NAMES)
    if hero_name == patient_name:
        raise StoryError("The hero and patient must be different people.")
    symptom = args.symptom or rng.choice(list(SYMPTOMS))
    return StoryParams(
        ship=ship,
        planet=planet,
        hero_name=hero_name,
        hero_type=args.hero_type,
        helper_name=helper_name,
        helper_type=args.helper_type,
        patient_name=patient_name,
        patient_type=args.patient_type,
        symptom=symptom,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} valid hero/patient pairs:")
        for pair in pairs:
            print(" ", pair)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    if args.all:
        params_list = [
            StoryParams(ship=s, planet=p, hero_name=h, hero_type="boy",
                        helper_name=helper, helper_type="captain",
                        patient_name=pat, patient_type="boy", symptom=sym)
            for s in SHIP_NAMES[:2]
            for p in PLANETS[:2]
            for h, pat in [("Nova", "Puck"), ("Zia", "Nell")]
            for helper in ["Captain Jo"]
            for sym in ["woe", "ache"]
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            i += 1
            sample = generate(p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
