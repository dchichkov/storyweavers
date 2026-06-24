#!/usr/bin/env python3
"""
A tiny mythic story world about a dumb vessel and teamwork.

This world tells a small, classical tale in a myth style:
a vessel is too clumsy to cross the water alone, so the crew learns
that shared effort can carry what one pair of hands cannot.

The simulation tracks:
- physical meters: weight, drift, strain, waterline, progress
- emotional memes: hope, pride, worry, trust, relief
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owned_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class CrewRole:
    id: str
    name: str
    talent: str
    mythic_title: str


@dataclass
class VesselSpec:
    id: str
    label: str
    phrase: str
    flaw: str
    challenge: str
    helper_needed: str


@dataclass
class Place:
    id: str
    label: str
    water: bool = True
    currents: str = "strong"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    vessel: str
    crew_size: int
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


PLACES = {
    "harbor": Place(id="harbor", label="the harbor", currents="tide-tossed", tags={"water", "launch"}),
    "river": Place(id="river", label="the river", currents="swift", tags={"water", "journey"}),
    "bay": Place(id="bay", label="the bay", currents="restless", tags={"water", "crossing"}),
}

VESSELS = {
    "barge": VesselSpec(
        id="barge",
        label="a dumb barge",
        phrase="a dumb barge with a heavy hull and a blunt nose",
        flaw="stuck in the shallows",
        challenge="the current kept turning it sideways",
        helper_needed="many hands and steady ropes",
    ),
    "boat": VesselSpec(
        id="boat",
        label="a dumb boat",
        phrase="a dumb boat with a low mast and a stubborn keel",
        flaw="too clumsy for the narrow channel",
        challenge="the wind pushed it into the reeds",
        helper_needed="a patient crew",
    ),
    "raft": VesselSpec(
        id="raft",
        label="a dumb raft",
        phrase="a dumb raft lashed from thick logs and rough reeds",
        flaw="slow and wobbly",
        challenge="it drifted whenever one hand let go",
        helper_needed="shared balance and careful feet",
    ),
}

ROLES = [
    CrewRole("elder", "elder", "knows old ways", "the elder"),
    CrewRole("sailor", "sailor", "ties strong knots", "the sailor"),
    CrewRole("smith", "smith", "makes iron rings", "the smith"),
    CrewRole("child", "child", "spots the shore", "the child"),
]

NAMES = ["Ari", "Mira", "Talen", "Sora", "Ivo", "Nila", "Joren", "Lena"]


class WorldReasoning:
    @staticmethod
    def reasonableness_gate(place: Place, vessel: VesselSpec, crew_size: int) -> None:
        if crew_size < 2:
            raise StoryError("The myth needs teamwork: one person is not enough to move the vessel.")
        if not place.water:
            raise StoryError("This story world needs water, because the vessel must face a crossing.")
        if vessel.id == "raft" and place.id == "harbor" and crew_size < 3:
            raise StoryError("The dumb raft in the harbor needs a larger crew to feel like a real teamwork tale.")

    @staticmethod
    def teamwork_needed(vessel: VesselSpec) -> bool:
        return True

    @staticmethod
    def can_resolve(crew_size: int, vessel: VesselSpec) -> bool:
        return crew_size >= 2 and bool(vessel.helper_needed)


def _init_vessel(world: World, vessel: VesselSpec) -> Entity:
    ent = world.add(Entity(
        id="vessel",
        kind="thing",
        type="vessel",
        label=vessel.label,
        phrase=vessel.phrase,
        meters={"weight": 3.0, "strain": 0.0, "drift": 0.0, "progress": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "hope": 0.0, "relief": 0.0},
    ))
    return ent


def _init_crew(world: World, crew_size: int) -> list[Entity]:
    crew: list[Entity] = []
    for i in range(crew_size):
        role = ROLES[i % len(ROLES)]
        name = NAMES[i % len(NAMES)] + (str(i + 1) if i >= len(NAMES) else "")
        crew.append(world.add(Entity(
            id=name,
            kind="character",
            type=role.id,
            label=role.mythic_title,
            phrase=f"{role.mythic_title} {name}",
            meters={"strength": 1.0, "balance": 1.0},
            memes={"hope": 1.0, "trust": 0.0, "pride": 0.0, "worry": 0.0, "relief": 0.0},
        )))
    return crew


def _turn_world(world: World, vessel: Entity, crew: list[Entity], vessel_spec: VesselSpec) -> None:
    vessel.meters["drift"] += 1.0
    vessel.meters["strain"] += 1.0
    for c in crew:
        c.memes["worry"] += 0.5
        c.memes["hope"] += 0.25
    world.say(f"The {vessel_spec.label} was a dumb vessel, broad and stubborn, and the {world.place.label} made it seem even heavier.")
    world.say(f"When they pushed, the current answered with a rough shove; the vessel answered by sliding sideways.")

    if len(crew) >= 2:
        for c in crew:
            c.memes["trust"] += 0.75
            c.memes["hope"] += 0.5
        vessel.meters["progress"] += 1.0
        vessel.meters["drift"] = max(0.0, vessel.meters["drift"] - 0.5)
        world.say("Then they stopped pushing alone and moved together, shoulder to shoulder, each hand taking a rope or an edge.")
        world.say("Their teamwork found the trick of it: one steadied, one pulled, one called the rhythm, and the vessel began to listen.")

    if len(crew) >= 3:
        vessel.meters["progress"] += 1.0
        vessel.meters["strain"] = max(0.0, vessel.meters["strain"] - 0.5)
        for c in crew:
            c.memes["pride"] += 0.5
        world.say("A third voice kept time like a drum, and the whole crew became one moving thing.")
    vessel.memes["hope"] += 1.0


def _resolve_world(world: World, vessel: Entity, crew: list[Entity], vessel_spec: VesselSpec) -> None:
    vessel.meters["progress"] += 1.0
    vessel.memes["relief"] += 1.0
    for c in crew:
        c.memes["relief"] += 1.0
        c.memes["worry"] = max(0.0, c.memes["worry"] - 0.75)
        c.memes["trust"] += 0.5
    world.say(f"At last the dumb vessel crossed the water, not because it had become wise, but because the crew had become one.")
    world.say(f"They reached the far shore with wet feet and bright faces, and even the old hull seemed to stand a little taller in the sunlight.")


def tell(place: Place, vessel_spec: VesselSpec, crew_size: int, names: Optional[list[str]] = None) -> World:
    WorldReasoning.reasonableness_gate(place, vessel_spec, crew_size)
    world = World(place)
    vessel = _init_vessel(world, vessel_spec)
    crew = _init_crew(world, crew_size)

    world.say(f"Long ago, by {place.label}, there was {vessel_spec.phrase}.")
    world.say(f"It was called dumb not because it was cruel, but because it could not solve its own troubles.")
    world.say(f"{crew[0].phrase.capitalize()} and the others came to the shore and saw the vessel {vessel_spec.flaw}.")

    world.para()
    world.say(f"The task was hard, for {vessel_spec.challenge}.")
    for c in crew:
        c.memes["worry"] += 0.5
    world.say(f"Still, each one felt a little spark of hope, because {vessel_spec.helper_needed} can move what pride cannot.")

    world.para()
    _turn_world(world, vessel, crew, vessel_spec)
    _resolve_world(world, vessel, crew, vessel_spec)

    world.facts.update(
        place=place,
        vessel=vessel_spec,
        crew=crew,
        vessel_entity=vessel,
        crew_size=crew_size,
        resolved=vessel.meters["progress"] >= 2.0,
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: a dumb vessel and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--crew-size", type=int, choices=range(2, 6), dest="crew_size")
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    vessel = args.vessel or rng.choice(list(VESSELS))
    crew_size = args.crew_size or rng.randint(2, 4)
    WorldReasoning.reasonableness_gate(PLACES[place], VESSELS[vessel], crew_size)
    return StoryParams(place=place, vessel=vessel, crew_size=crew_size)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"].label
    v = world.facts["vessel"].label
    return [
        f'Write a short myth about a dumb vessel at {p} that can only cross with teamwork.',
        f"Tell a child-friendly legend where {v} is stuck until the crew works together.",
        f"Write a mythic story about how teamwork helps a clumsy vessel reach the far shore.",
    ]


def story_qa(world: World) -> list[QAItem]:
    vessel = world.facts["vessel"]
    place = world.facts["place"]
    crew = world.facts["crew"]
    names = ", ".join(c.id for c in crew)
    return [
        QAItem(
            question=f"What was the dumb vessel in the story?",
            answer=f"It was {vessel.phrase}, sitting by {place.label} until the crew helped it move.",
        ),
        QAItem(
            question=f"Who helped the vessel cross the water?",
            answer=f"The crew helped. The story named {names}, and they worked together instead of trying to do it alone.",
        ),
        QAItem(
            question=f"Why did the vessel finally move?",
            answer="It finally moved because the crew used teamwork: one steadied, one pulled, and the others kept the rhythm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    place = world.facts["place"].label
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people join their efforts and help one another so a hard job becomes possible.",
        ),
        QAItem(
            question="Why do vessels need balance on water?",
            answer="A vessel needs balance because water can push it sideways, and steady hands help keep it on course.",
        ),
        QAItem(
            question=f"What is {place} like in the story?",
            answer=f"{place.capitalize()} is a watery place where a vessel can try to cross with the help of a crew.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
crew_ok(N) :- crew_size(N), N >= 2.
teamwork_needed(V) :- vessel(V).
can_resolve(P,V,N) :- place(P), vessel(V), crew_ok(N).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.water:
            lines.append(asp.fact("water_place", pid))
    for vid in VESSELS:
        lines.append(asp.fact("vessel", vid))
    for n in range(2, 6):
        lines.append(asp.fact("crew_size", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_resolve/3."))
    combos = set(asp.atoms(model, "can_resolve"))
    py = {(p, v, n) for p in PLACES for v in VESSELS for n in range(2, 6)}
    if combos == py:
        print(f"OK: clingo parity matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], VESSELS[params.vessel], params.crew_size)
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
    StoryParams(place="harbor", vessel="barge", crew_size=3),
    StoryParams(place="river", vessel="boat", crew_size=2),
    StoryParams(place="bay", vessel="raft", crew_size=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_resolve/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_resolve/3."))
        print(sorted(set(asp.atoms(model, "can_resolve"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
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
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.vessel} / crew={p.crew_size}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
