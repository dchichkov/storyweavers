#!/usr/bin/env python3
"""
A small space-adventure storyworld about a ship's crew, a dairy supply,
and a misplaced bra that creates suspense before friendship resolves the day.

The seed premise:
- On a starship, the staff is preparing a milk delivery for a friendly outpost.
- A crew member needs a bra/undershirt for a zero-gravity exercise suit.
- The milk is in danger because a cooling pod is running warm.
- A best friend notices the problem, helps search, and the crew learns a lesson:
  good teamwork keeps both supplies and feelings safe.

This script builds a tiny stateful simulation with meters and memes, then
renders one complete story plus QA and an ASP parity twin.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"pilot", "woman", "girl", "crewwoman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    name: str = "the bright starship"
    place: str = "the milk bay"
    station: str = "a friendly moon port"
    corridor: str = "the silver corridor"
    launch_time: str = "starlight evening"


@dataclass
class Supply:
    id: str
    label: str
    phrase: str
    type: str
    risky_when: str
    safe_when: str
    location: str


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]


@dataclass
class StoryParams:
    ship: str
    supply: str
    gear: str
    hero: str
    friend: str
    captain: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.parts: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.parts[-1].append(text)

    def para(self) -> None:
        if self.parts[-1]:
            self.parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.parts if p)

    def copy(self) -> "World":
        import copy
        w = World(self.ship)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.parts = [[]]
        return w


SUPPLIES = {
    "dairy": Supply(
        id="dairy",
        label="dairy crate",
        phrase="a sealed dairy crate with cool milk packs",
        type="dairy",
        risky_when="warm",
        safe_when="chilled",
        location="the milk bay",
    ),
    "bra": Supply(
        id="bra",
        label="sports bra",
        phrase="a soft sports bra for zero-gravity exercise",
        type="bra",
        risky_when="lost",
        safe_when="found",
        location="the locker nook",
    ),
}

GEAR = {
    "coolant": Gear(
        id="coolant",
        label="coolant gel pack",
        phrase="a coolant gel pack",
        covers={"milk"},
        helps={"warm"},
    ),
    "scanner": Gear(
        id="scanner",
        label="hand scanner",
        phrase="a hand scanner",
        covers={"search"},
        helps={"lost"},
    ),
}

SHIP = Ship()


@dataclass
class StoryState:
    warm: bool = False
    lost: bool = False
    friendship: float = 0.0
    suspense: float = 0.0
    lesson: float = 0.0
    resolved: bool = False
    found_gear: bool = False


def build_state() -> World:
    world = World(SHIP)
    world.add(Entity(id="Astra", kind="character", type="crewwoman", label="Astra"))
    world.add(Entity(id="Milo", kind="character", type="crewman", label="Milo"))
    world.add(Entity(id="CaptainRin", kind="character", type="captain", label="Captain Rin"))
    world.add(Entity(id="dairy", type="dairy", label="dairy crate", phrase="a sealed dairy crate"))
    world.add(Entity(id="bra", type="bra", label="sports bra", phrase="a soft sports bra"))
    return world


def predict_risk(world: World) -> dict:
    dairy = world.get("dairy")
    bra = world.get("bra")
    return {
        "milk_warm": dairy.meters.get("warm", 0) >= 1.0,
        "bra_lost": bra.memes.get("lost", 0) >= 1.0,
    }


def act_setup(world: World) -> None:
    world.say("On the bright starship, the staff was busy before launch.")
    world.say("Astra checked the milk bay, where a dairy crate glowed under soft blue lights.")
    world.say("Milo packed a sports bra for a zero-gravity practice run and tucked it into the locker nook.")
    world.say("Captain Rin reminded everyone that the ship had to deliver fresh supplies to a friendly moon port.")
    world.facts["setup"] = True


def act_tension(world: World) -> None:
    dairy = world.get("dairy")
    bra = world.get("bra")
    dairy.meters["warm"] = 1.0
    bra.memes["lost"] = 1.0
    world.say("But then the cooling pod blinked amber, and the milk bay felt too warm.")
    world.say("At the same time, Milo opened the locker nook and stared at the empty hook.")
    world.say("His sports bra was gone, and the exercise suit needed it before ship practice.")
    world.facts["risk"] = predict_risk(world)


def act_suspense(world: World) -> None:
    world.say("Astra's heart thumped hard. If the dairy crate stayed warm, the milk would spoil before the handoff.")
    world.say("If Milo could not find the bra, he would miss the practice and feel embarrassed in front of the crew.")
    world.say("The corridor stayed quiet, except for one tiny beep from the scanner shelf.")
    world.facts["suspense"] = True


def act_friendship(world: World) -> None:
    dairy = world.get("dairy")
    bra = world.get("bra")
    astra = world.get("Astra")
    milo = world.get("Milo")
    astra.memes["care"] = astra.memes.get("care", 0) + 1
    milo.memes["care"] = milo.memes.get("care", 0) + 1
    astra.memes["friendship"] = astra.memes.get("friendship", 0) + 1
    milo.memes["friendship"] = milo.memes.get("friendship", 0) + 1

    world.say("Astra did not blame anyone. She handed Milo the hand scanner and said, “Let’s solve both problems together.”")
    world.say("Milo smiled, because friends made hard moments feel smaller.")
    world.say("They searched the corridor first, then the storage shelf, then the warm corner beside the tea heater.")
    world.say("Under a folded spare blanket, they found the sports bra.")
    bra.memes["lost"] = 0.0
    bra.memes["found"] = 1.0
    world.say("Astra also clipped on a coolant gel pack and cooled the dairy crate before the milk could spoil.")
    dairy.meters["warm"] = 0.0
    dairy.meters["chilled"] = 1.0
    world.facts["found"] = True
    world.facts["friendship"] = True


def act_lesson(world: World) -> None:
    world.say("Captain Rin watched the two friends finish their work and nodded with a proud smile.")
    world.say("They learned that a calm crew could fix a scare faster than a panicked one.")
    world.say("When the starship reached the moon port, the dairy crate was cool, the sports bra was ready, and the staff felt closer than before.")
    world.say("The lesson settled gently over the ship like a blanket: good friends keep each other steady when the stars get tricky.")
    world.facts["lesson"] = True
    world.facts["resolved"] = True


def tell_story(world: World) -> World:
    act_setup(world)
    world.para()
    act_tension(world)
    act_suspense(world)
    world.para()
    act_friendship(world)
    act_lesson(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What was the staff trying to do on the starship?",
            answer="The staff was preparing to deliver fresh supplies and keep the ship ready for a friendly moon port.",
        ),
        QAItem(
            question="Why did Astra worry about the dairy crate?",
            answer="She worried because the cooling pod blinked amber and the dairy crate was getting warm, which could spoil the milk.",
        ),
        QAItem(
            question="What was Milo looking for?",
            answer="Milo was looking for his sports bra for a zero-gravity practice run.",
        ),
        QAItem(
            question="How did Astra and Milo solve the problem?",
            answer="They searched together, found the missing sports bra under a blanket, and used a coolant gel pack to cool the dairy crate.",
        ),
        QAItem(
            question="What lesson did the crew learn?",
            answer="They learned that calm teamwork and friendship can fix a scary problem before it grows bigger.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a coolant gel pack do?",
            answer="A coolant gel pack helps keep things cold for a little while, which is useful for food that must stay fresh.",
        ),
        QAItem(
            question="Why can a hidden object feel suspenseful in a story?",
            answer="A hidden object can feel suspenseful because the characters need it soon, so the reader wants to know whether it will be found in time.",
        ),
        QAItem(
            question="Why do friends help each other during a problem?",
            answer="Friends help each other because teamwork can make hard jobs easier and can calm worried feelings.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short space-adventure story for young children about staff on a ship, a dairy crate, and a missing bra.',
        'Tell a story where friendship solves a suspenseful problem before fresh dairy spoils.',
        'Write a gentle starship tale with a clear lesson learned and a happy ending at a moon port.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        m = {k: v for k, v in ent.meters.items() if v}
        mm = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


@dataclass
class StoryParams2:
    ship: str
    supply: str
    gear: str
    hero: str
    friend: str
    captain: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with staff, dairy, and bra.")
    ap.add_argument("--ship", choices=["bright_starship"], default="bright_starship")
    ap.add_argument("--supply", choices=sorted(SUPPLIES), default=None)
    ap.add_argument("--gear", choices=sorted(GEAR), default=None)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--captain")
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
    supply = args.supply or rng.choice(list(SUPPLIES))
    gear = args.gear or ("coolant" if supply == "dairy" else "scanner")
    hero = args.hero or rng.choice(["Astra", "Nia", "Rin"])
    friend = args.friend or rng.choice(["Milo", "Tess", "Nova"])
    captain = args.captain or "Captain Rin"
    return StoryParams(ship=args.ship, supply=supply, gear=gear, hero=hero, friend=friend, captain=captain)


def generate(params: StoryParams) -> StorySample:
    world = build_state()
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
ship(bright_starship).
supply(dairy). supply(bra).
feature(friendship). feature(suspense). feature(lesson_learned).
risky(dairy,warm).
risky(bra,lost).
fix(coolant,dairy,warm).
fix(scanner,bra,lost).
valid_story(S,Supply,Gear) :- ship(S), supply(Supply), gear_ok(Gear,Supply).
gear_ok(coolant,dairy).
gear_ok(scanner,bra).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("ship", "bright_starship")]
    lines.append(asp.fact("supply", "dairy"))
    lines.append(asp.fact("supply", "bra"))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("feature", "suspense"))
    lines.append(asp.fact("feature", "lesson_learned"))
    lines.append(asp.fact("gear", "coolant"))
    lines.append(asp.fact("gear", "scanner"))
    lines.append(asp.fact("gear_ok", "coolant", "dairy"))
    lines.append(asp.fact("gear_ok", "scanner", "bra"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show gear_ok/2."))
    got = set(asp.atoms(model, "gear_ok"))
    want = {("coolant", "dairy"), ("scanner", "bra")}
    if got == want:
        print(f"OK: ASP gate matches Python rules ({len(got)} pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("got:", sorted(got))
    print("want:", sorted(want))
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
    StoryParams(ship="bright_starship", supply="dairy", gear="coolant", hero="Astra", friend="Milo", captain="Captain Rin"),
    StoryParams(ship="bright_starship", supply="bra", gear="scanner", hero="Nia", friend="Tess", captain="Captain Rin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show gear_ok/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show gear_ok/2."))
        print(sorted(set(asp.atoms(model, "gear_ok"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
