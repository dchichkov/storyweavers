#!/usr/bin/env python3
"""
storyworlds/worlds/doctor_surprise_pirate_tale.py
=================================================

A tiny story world in the spirit of a Pirate Tale: a pirate crew sets out on
the sea, faces a problem, and is surprised by a doctor who brings a clever fix.

The world is small and classical:
- A captain, a doctor, a crew, a ship, and one troubling surprise.
- Physical state uses meters; emotional state uses memes.
- The tale is driven by the state of the crew, the ship, and the surprise.

The seed image behind this world:
- A pirate crew sails with a proud captain.
- Something sudden goes wrong on the ship.
- A doctor appears with a helpful, surprising remedy.
- The crew ends the tale relieved, thankful, and ready to sail on.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"hurt": 0.0, "broken": 0.0, "fresh": 0.0}
        if not self.memes:
            self.memes = {"surprise": 0.0, "worry": 0.0, "joy": 0.0, "gratitude": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Event:
    name: str
    apply: Callable[[World], list[str]]


@dataclass
class StoryParams:
    ship: str
    captain: str
    doctor: str
    surprise: str
    hero: str
    seed: Optional[int] = None


SHIP_NAMES = ["the Salt Fox", "the Blue Comet", "the Lucky Gull", "the Red Sail"]
CAPTAIN_NAMES = ["Captain Mara", "Captain Finn", "Captain Bea", "Captain Jory"]
DOCTOR_NAMES = ["Doctor Nell", "Doctor Bram", "Doctor Tess", "Doctor Pip"]
HERO_NAMES = ["Rowan", "Nia", "Tom", "Lena", "Milo", "Zara"]
SURPRISES = {
    "storm": {
        "label": "sudden storm",
        "problem": "the sails tore in the wind",
        "mess": "torn",
        "fix": "stitched sailcloth",
        "fix_verb": "patch",
        "emotion": "surprise",
    },
    "cough": {
        "label": "sneezing cough",
        "problem": "the little cabin boy could not stop coughing",
        "mess": "weak",
        "fix": "warm tea",
        "fix_verb": "brew",
        "emotion": "worry",
    },
    "sprain": {
        "label": "ankle sprain",
        "problem": "the deckhand could not hop up the steps",
        "mess": "slow",
        "fix": "a neat wrap",
        "fix_verb": "wrap",
        "emotion": "worry",
    },
    "parrot": {
        "label": "shy parrot",
        "problem": "the ship's parrot would not come out of its crate",
        "mess": "hidden",
        "fix": "bright berries",
        "fix_verb": "treat",
        "emotion": "surprise",
    },
}


def setup_world(params: StoryParams) -> World:
    w = World(place="the sea")
    captain = w.add(Entity(id="captain", kind="character", type="pirate", label=params.captain, traits=["proud", "bold"]))
    doctor = w.add(Entity(id="doctor", kind="character", type="doctor", label=params.doctor, traits=["calm", "kind"]))
    hero = w.add(Entity(id="hero", kind="character", type="pirate", label=params.hero, traits=["small", "eager"]))
    ship = w.add(Entity(id="ship", kind="thing", type="ship", label=params.ship, phrase=params.ship))
    surprise = w.add(Entity(id="surprise", kind="thing", type=params.surprise, label=SURPRISES[params.surprise]["label"]))
    w.facts.update(params=params, captain=captain, doctor=doctor, hero=hero, ship=ship, surprise=surprise)
    return w


def _storm_rule(world: World) -> list[str]:
    out: list[str] = []
    s = world.get("surprise")
    ship = world.get("ship")
    if s.id != "surprise":
        return out
    if s.meters["broken"] >= THRESHOLD and ("storm",) not in world.fired:
        world.fired.add(("storm",))
        ship.meters["broken"] += 1
        out.append("The ship groaned as the surprise made trouble on deck.")
    return out


RULES: list[Event] = [Event("storm", _storm_rule)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def surprise_spec(kind: str) -> dict:
    if kind not in SURPRISES:
        raise StoryError(f"Unknown surprise: {kind}")
    return SURPRISES[kind]


def introduce(world: World) -> None:
    captain = world.get("captain")
    hero = world.get("hero")
    ship = world.get("ship")
    world.say(
        f"{captain.label} sailed {ship.label} with {hero.label}, who loved every splash of the sea."
    )
    world.say(
        f"{hero.label} liked shiny ropes, salty air, and the proud song of the rigging."
    )


def set_sail(world: World) -> None:
    world.say(
        f"One bright day, {world.get('captain').label} promised a fast trip across the blue water."
    )
    world.say("The crew laughed, because the wind felt friendly and the deck was warm under their boots.")


def surprise_arrives(world: World, kind: str) -> None:
    spec = surprise_spec(kind)
    surpr = world.get("surprise")
    surpr.meters["broken"] += 1
    world.get("captain").memes["surprise"] += 1
    world.get("hero").memes["surprise"] += 1
    world.get("captain").memes["worry"] += 1
    world.say(
        f"Then came a {spec['label']}, and {spec['problem']}."
    )
    world.say(
        f"The crew blinked at the sudden trouble, because it had arrived like a splash from nowhere."
    )
    propagate(world, narrate=True)


def ask_doctor(world: World, kind: str) -> None:
    spec = surprise_spec(kind)
    doctor = world.get("doctor")
    captain = world.get("captain")
    hero = world.get("hero")
    world.say(
        f"Just then, {doctor.label} stepped onto the deck with a small grin, which was a surprise all by itself."
    )
    world.say(
        f'"I know that trouble," {doctor.label} said. "I brought {spec["fix"]} to {spec["fix_verb"]} it."'
    )
    doctor.memes["joy"] += 1
    captain.memes["worry"] += 1
    hero.memes["surprise"] += 1


def heal(world: World, kind: str) -> None:
    spec = surprise_spec(kind)
    surpr = world.get("surprise")
    captain = world.get("captain")
    hero = world.get("hero")
    doctor = world.get("doctor")
    surpr.meters["broken"] = max(0.0, surpr.meters["broken"] - 1.0)
    surpr.meters["fresh"] += 1
    captain.memes["worry"] = 0.0
    captain.memes["joy"] += 1
    hero.memes["joy"] += 1
    hero.memes["gratitude"] += 1
    doctor.memes["gratitude"] += 1
    world.say(
        f"{doctor.label} used {spec['fix']} to {spec['fix_verb']} the trouble, and the deck grew calm again."
    )
    world.say(
        f"The crew stared, then cheered, because the cure was clever and the doctor had brought it like hidden treasure."
    )
    world.say(
        f"At last, {hero.label} smiled at {doctor.label}, and even {world.get('captain').label} tipped a hat in thanks."
    )


def end_image(world: World) -> None:
    hero = world.get("hero")
    captain = world.get("captain")
    doctor = world.get("doctor")
    world.say(
        f"By sunset, {world.place} glowed gold, the ship was steady, and {hero.label} was laughing beside {doctor.label}."
    )
    world.say(
        f"{captain.label} watched the calm sea and felt lucky that the surprise had brought help instead of harm."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    set_sail(world)
    surprise_arrives(world, params.surprise)
    world.para()
    ask_doctor(world, params.surprise)
    heal(world, params.surprise)
    world.para()
    end_image(world)
    return world


def valid_surprises() -> list[str]:
    return list(SURPRISES.keys())


@dataclass
class StoryParamsRegistry:
    pass


SETTINGS = {"sea": "the sea"}
CAPTAINS = CAPTAIN_NAMES
DOCTORS = DOCTOR_NAMES
HEROES = HERO_NAMES


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for ship in SHIP_NAMES:
        for captain in CAPTAIN_NAMES:
            for doctor in DOCTOR_NAMES:
                for surprise in SURPRISES:
                    out.append((ship, captain, surprise))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Pirate Tale for young children that includes a doctor and the word "{f["surprise"].label}".',
        f"Tell a gentle sea story where {f['captain'].label} is startled, {f['doctor'].label} helps, and the crew feels better.",
        f'Write a small pirate adventure with a surprise on the ship and a doctor who fixes it with kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap = f["captain"]
    doc = f["doctor"]
    hero = f["hero"]
    surpr = f["surprise"]
    spec = SURPRISES[surpr.type]
    return [
        QAItem(
            question=f"Who was sailing the ship with {hero.label}?",
            answer=f"{cap.label} was sailing {f['ship'].label} with {hero.label}.",
        ),
        QAItem(
            question=f"What surprising trouble happened on the ship?",
            answer=f"A {spec['label']} happened, and {spec['problem']}.",
        ),
        QAItem(
            question=f"Who helped fix the trouble?",
            answer=f"{doc.label}, the doctor, helped fix it with {spec['fix']}.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt happy and thankful after the doctor made things calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a doctor do?",
            answer="A doctor helps people feel better when they are hurt or sick.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something sudden that you did not expect.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used by pirates for sailing, exploring, and carrying their crew.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
surprising(X) :- surprise(X).
doctor_present(D) :- doctor(D).
helpful(D, X) :- doctor(D), surprise(X).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SHIP_NAMES:
        lines.append(asp.fact("ship", s))
    for c in CAPTAIN_NAMES:
        lines.append(asp.fact("captain", c))
    for d in DOCTOR_NAMES:
        lines.append(asp.fact("doctor", d))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show surprising/1.\n#show helpful/2."))
    atoms = set((s.name, tuple(a.name if a.type != 0 else a.number for a in s.arguments)) for s in model)
    expected = {("surprising", (k,)) for k in SURPRISES} | {("helpful", (d, s)) for d in DOCTOR_NAMES for s in SURPRISES}
    if atoms == expected:
        print(f"OK: ASP parity matches {len(expected)} facts.")
        return 0
    print("Mismatch between ASP and Python expectations.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a doctor surprise.")
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
    ap.add_argument("--doctor", choices=DOCTOR_NAMES)
    ap.add_argument("--surprise", choices=valid_surprises())
    ap.add_argument("--hero", choices=HERO_NAMES)
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
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    doctor = args.doctor or rng.choice(DOCTOR_NAMES)
    surprise = args.surprise or rng.choice(valid_surprises())
    hero = args.hero or rng.choice(HERO_NAMES)
    return StoryParams(ship=ship, captain=captain, doctor=doctor, surprise=surprise, hero=hero)


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
    StoryParams(ship="the Salt Fox", captain="Captain Mara", doctor="Doctor Nell", surprise="storm", hero="Rowan"),
    StoryParams(ship="the Blue Comet", captain="Captain Finn", doctor="Doctor Bram", surprise="cough", hero="Nia"),
    StoryParams(ship="the Lucky Gull", captain="Captain Bea", doctor="Doctor Tess", surprise="sprain", hero="Tom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show surprising/1.\n#show helpful/2."))
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.hero} on {p.ship} with {p.doctor} ({p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
