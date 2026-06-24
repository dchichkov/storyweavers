#!/usr/bin/env python3
"""
A standalone story world for a tiny nursery-rhyme-like toll bridge tale.

Premise:
- A small traveler wants to cross a bridge.
- The bridge has a toll gate.
- A gunner-like bellkeeper named Gunner warns them with foreshadowing clues.
- If the traveler tries to slip through, the gate stays shut and the story
  resolves only when the toll is paid.

The prose is built from a simulated world state so the ending image changes the
world, not just the nouns.
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


@dataclass
class Place:
    id: str
    label: str
    toll_needed: bool = True
    exposed: bool = False
    sound: str = "bell"
    mood: str = "quiet"


@dataclass
class Toll:
    id: str
    label: str
    phrase: str
    amount: int = 1


@dataclass
class StoryParams:
    place: str
    traveler: str
    companion: str
    toll: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "bridge": Place(id="bridge", label="the little toll bridge", toll_needed=True, exposed=True, sound="bell", mood="windy"),
    "lane": Place(id="lane", label="the lane by the river", toll_needed=True, exposed=False, sound="bell", mood="misty"),
    "arch": Place(id="arch", label="the stone arch gate", toll_needed=True, exposed=True, sound="chime", mood="golden"),
}

TRAVELERS = {
    "mira": ("Mira", "girl", ["curious", "small", "brave"]),
    "ben": ("Ben", "boy", ["cheery", "small", "careful"]),
    "pip": ("Pip", "child", ["tiny", "lively", "careful"]),
}

COMPANIONS = {
    "mother": ("mother", "mother"),
    "father": ("father", "father"),
    "grandma": ("grandma", "woman"),
}

TOLLS = {
    "coin": Toll(id="coin", label="a bright coin", phrase="a bright coin for the toll", amount=1),
    "shell": Toll(id="shell", label="a smooth shell", phrase="a smooth shell for the toll", amount=1),
    "button": Toll(id="button", label="a brass button", phrase="a brass button for the toll", amount=1),
}


ASP_RULES = r"""
place(P) :- setting(P).
toll(T) :- toll_item(T).
traveler(X) :- child(X).
companion(C) :- helper(C).

needs_toll(P) :- setting(P), requires_toll(P).
can_open(P) :- needs_toll(P), toll_item(T), paid(T).

warning(P) :- needs_toll(P), foreshadow(P).
resolved(P) :- can_open(P), warning(P).

#show needs_toll/1.
#show can_open/1.
#show warning/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.toll_needed:
            lines.append(asp.fact("requires_toll", pid))
        if place.exposed:
            lines.append(asp.fact("foreshadow", pid))
    for tid in TOLLS:
        lines.append(asp.fact("toll_item", tid))
    for cid in COMPANIONS:
        lines.append(asp.fact("helper", cid))
    for tid in TRAVELERS:
        lines.append(asp.fact("child", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    got = set(asp.atoms(model, "resolved"))
    want = {("bridge",), ("lane",), ("arch",)}
    if got == want:
        print(f"OK: ASP reasoner sees {len(want)} resolved places.")
        return 0
    print("Mismatch in ASP parity.")
    print("got:", sorted(got))
    print("want:", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small toll-bridge nursery rhyme world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--traveler", choices=TRAVELERS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--toll", choices=TOLLS)
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


def reasonableness_gate(place: Place, toll: Toll) -> bool:
    return place.toll_needed and toll.amount >= 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    traveler = args.traveler or rng.choice(list(TRAVELERS))
    companion = args.companion or rng.choice(list(COMPANIONS))
    toll = args.toll or rng.choice(list(TOLLS))
    if not reasonableness_gate(PLACES[place], TOLLS[toll]):
        raise StoryError("The chosen place needs no toll, so there is no story to tell.")
    return StoryParams(place=place, traveler=traveler, companion=companion, toll=toll)


def predict_gate(world: World) -> bool:
    return world.place.toll_needed


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    trav_name, trav_type, trav_traits = TRAVELERS[params.traveler]
    comp_label, comp_type = COMPANIONS[params.companion]
    toll = TOLLS[params.toll]

    world = World(place)
    traveler = world.add(Entity(id=trav_name, kind="character", type=trav_type, traits=trav_traits))
    companion = world.add(Entity(id=comp_label, kind="character", type=comp_type, label=comp_label))
    toll_ent = world.add(Entity(id=toll.id, type="thing", label=toll.label, phrase=toll.phrase))

    traveler.memes["hope"] = 1
    traveler.memes["curiosity"] = 1
    world.say(f"{trav_name} was a {trav_traits[0]} little traveler who came to {place.label}.")
    world.say(f"{trav_name} loved the road ahead, and the road was small and bright.")

    world.para()
    world.say(f"Along the rail sat {comp_label}, and {comp_label} kept the toll with a steady eye.")
    world.say(f"The wind went hush, and the {place.sound} gave a soft sound to foreshadow what might be.")

    world.para()
    traveler.memes["desire"] = 1
    world.say(f"{trav_name} wanted to cross at once, but the little toll gate stood in the way.")
    world.say(f'"Pay the toll," said {comp_label}, "or the gate will stay shut all day."')

    if predict_gate(world):
        traveler.memes["caution"] = 1
        traveler.memes["fear"] = 1
        world.say(f"{trav_name} tried to slip ahead, but the gate did not budge.")
        world.say(f"{trav_name} frowned, then found {toll.label} in {trav_name}\'s hand and placed it down with care.")
        toll_ent.meters["paid"] = 1
        traveler.memes["relief"] = 1
        world.say(f"At once, the gate swung open, and {trav_name} went across with {comp_label}.")
        world.say(f"The river stayed calm, and {trav_name} reached the far side with a brave little smile.")
    world.facts.update(traveler=traveler, companion=companion, toll=toll_ent, place=place, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme story about {f['traveler'].id} at {f['place'].label} with a toll and a gentle warning.",
        f"Tell a cautionary tale where {f['traveler'].id} must pay {f['toll'].label} before crossing the bridge.",
        f"Write a short foreshadowing story with {f['companion'].id} keeping watch by the toll gate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trav = f["traveler"]
    comp = f["companion"]
    place = f["place"]
    toll = f["toll"]
    return [
        QAItem(
            question=f"Who wanted to cross {place.label}?",
            answer=f"{trav.id} wanted to cross {place.label}, because the far side looked bright and inviting.",
        ),
        QAItem(
            question=f"Who kept the toll safe at {place.label}?",
            answer=f"{comp.id} kept the toll safe and watched the gate with a calm, steady eye.",
        ),
        QAItem(
            question=f"What had to be paid before the gate would open?",
            answer=f"{toll.label} had to be paid before the toll gate would open.",
        ),
        QAItem(
            question=f"Why was there a warning before the crossing?",
            answer=f"There was a warning because the bridge needed a toll, and the soft bell sound foreshadowed that the gate would not open without it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toll?",
            answer="A toll is a small payment asked for before someone may use a road, bridge, or gate.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives little clues early on that help you guess what may happen next.",
        ),
        QAItem(
            question="Why is caution useful near a toll gate?",
            answer="Caution helps a traveler stop, listen, and do the right thing before trying to go through.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="bridge", traveler="mira", companion="mother", toll="coin"),
    StoryParams(place="lane", traveler="ben", companion="father", toll="shell"),
    StoryParams(place="arch", traveler="pip", companion="grandma", toll="button"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_open/1."))
        print(sorted(set(asp.atoms(model, "can_open"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
