#!/usr/bin/env python3
"""
A small myth-style storyworld about a feast interrupted by a swoop,
where a plate, a twist, and a transformation change what the hero becomes.

The domain premise:
- A child or young helper carries a special plate to a feast.
- A swift swoop interrupts the journey.
- The twist is that the plate is not just a dish: it can hold a blessing, a loss, or a new shape.
- The transformation is the ending: the hero, the plate, or the offering changes in a way that proves the lesson.

This script keeps the story grounded in a live world model with physical meters
and emotional memes, plus a declarative ASP twin for reasonableness checks.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    enchanted: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "queen", "priestess"}
        masculine = {"boy", "man", "father", "king", "priest"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)
    sacred: bool = False


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str = "hands"
    fragile: bool = True
    blessed: bool = False


@dataclass
class Creature:
    id: str
    label: str
    swoop_strength: float = 1.0
    curious: bool = False


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_kind: str
    hero_name: str
    keeper_kind: str
    keeper_name: str
    relic: str
    creature: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hall": Place(id="hall", label="the feast hall", affords={"carry", "sing"}, sacred=True),
    "courtyard": Place(id="courtyard", label="the courtyard", affords={"carry", "sing", "run"}, sacred=False),
    "temple_steps": Place(id="temple_steps", label="the temple steps", affords={"carry", "sing"}, sacred=True),
}

RELICS = {
    "plate": Relic(id="plate", label="plate", phrase="a bright ceremonial plate", region="hands", fragile=True, blessed=False),
    "offering_plate": Relic(id="offering_plate", label="offering plate", phrase="a wide offering plate", region="hands", fragile=True, blessed=True),
    "gold_plate": Relic(id="gold_plate", label="gold plate", phrase="a gold-edged plate", region="hands", fragile=True, blessed=True),
}

CREATURES = {
    "hawk": Creature(id="hawk", label="hawk", swoop_strength=1.0, curious=True),
    "windbird": Creature(id="windbird", label="windbird", swoop_strength=1.2, curious=True),
    "nightkite": Creature(id="nightkite", label="night kite", swoop_strength=0.9, curious=False),
}

HERO_NAMES = ["Ari", "Nia", "Taro", "Mina", "Lio", "Sana", "Kato", "Ira"]
KEEPER_NAMES = ["Elder", "Mother", "Father", "Priest", "Priestess", "Guardian"]
HERO_KINDS = ["boy", "girl"]
KEEPER_KINDS = ["mother", "father", "priest", "priestess"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _meter(x: float) -> float:
    return x


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _has(ent: Entity, key: str) -> bool:
    return ent.meters.get(key, 0.0) >= 1.0 or ent.memes.get(key, 0.0) >= 1.0


def _choice(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES.values():
        for relic in RELICS.values():
            if relic.region != "hands":
                continue
            for creature in CREATURES.values():
                # All registered combos are valid; reasonableness gate will still
                # reject explicit nonsense elsewhere if needed.
                combos.append((place.id, relic.id, creature.id))
    return combos


def reasonableness_gate(place: Place, relic: Relic, creature: Creature) -> None:
    if "carry" not in place.affords:
        raise StoryError("This place does not support the carrying ritual.")
    if not relic.fragile:
        raise StoryError("The relic must be fragile enough to matter in a swoop.")
    if creature.swoop_strength < 0.5:
        raise StoryError("The creature is too weak to produce a meaningful swoop.")


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def set_initial_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    relic = RELICS[params.relic]
    creature = CREATURES[params.creature]
    reasonableness_gate(place, relic, creature)

    world = World(place=place)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_kind,
        label=params.hero_name,
        phrase=f"a {params.hero_kind} named {params.hero_name}",
        carried_by=None,
    ))
    keeper = world.add(Entity(
        id=params.keeper_name,
        kind="character",
        type=params.keeper_kind,
        label=params.keeper_name,
        phrase=f"{params.keeper_kind} {params.keeper_name}",
    ))
    plate = world.add(Entity(
        id=relic.id,
        kind="thing",
        type="plate",
        label=relic.label,
        phrase=relic.phrase,
        owner=hero.id,
        carried_by=hero.id,
        enchanted=relic.blessed,
    ))
    beast = world.add(Entity(
        id=creature.id,
        kind="creature",
        type=creature.id,
        label=creature.label,
        phrase=f"a swift {creature.label}",
    ))
    world.facts.update(
        hero=hero, keeper=keeper, plate=plate, beast=beast,
        place=place, relic=relic, creature=creature,
    )
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    keeper: Entity = f["keeper"]
    plate: Entity = f["plate"]
    place: Place = f["place"]
    relic: Relic = f["relic"]

    _add_meme(hero, "wonder", 1)
    _add_meme(keeper, "care", 1)
    world.say(
        f"Long ago, in {place.label}, {hero.phrase} served at the old feast."
    )
    world.say(
        f"{keeper.label} gave {hero.pronoun('object')} {plate.phrase} and said it must arrive clean."
    )
    world.say(
        f"{hero.label} loved the shining plate, because it looked like moonlight held in two hands."
    )


def predict_swoop(world: World) -> bool:
    f = world.facts
    plate: Entity = f["plate"]
    beast: Entity = f["beast"]
    # If the plate is carried in the open, the swoop can interrupt it.
    return plate.carried_by is not None and beast.swoop_strength >= 1.0


def swoop_interrupts(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    keeper: Entity = f["keeper"]
    plate: Entity = f["plate"]
    beast: Entity = f["beast"]

    if ("swoop", beast.id) in world.fired:
        return
    world.fired.add(("swoop", beast.id))
    _add_meter(hero, "startle", 1)
    _add_meme(hero, "fear", 1)
    _add_meme(keeper, "alarm", 1)
    plate.carried_by = None
    _add_meter(plate, "tilt", 1)
    world.say(
        f"Then the {beast.label} came in a sudden swoop, and the procession broke at once."
    )
    world.say(
        f"The plate slipped from {hero.label}'s hands and spun like a silver leaf in the air."
    )


def twist(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    keeper: Entity = f["keeper"]
    plate: Entity = f["plate"]
    beast: Entity = f["beast"]

    if ("twist", plate.id) in world.fired:
        return
    world.fired.add(("twist", plate.id))
    _add_meme(hero, "surprise", 1)
    _add_meme(keeper, "knowledge", 1)
    _add_meter(plate, "bend", 1)
    plate.enchanted = True
    world.say(
        f"But the twist was this: the plate did not shatter."
    )
    world.say(
        f"It turned once in the sunlight, and a hidden mark woke inside it like a sleeping star."
    )


def transformation(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    keeper: Entity = f["keeper"]
    plate: Entity = f["plate"]
    beast: Entity = f["beast"]

    if ("transform", hero.id) in world.fired:
        return
    world.fired.add(("transform", hero.id))
    _add_meme(hero, "courage", 2)
    _add_meme(keeper, "joy", 1)
    _add_meter(hero, "steadiness", 1)
    plate.carried_by = hero.id
    plate.meters["glow"] = 1
    world.say(
        f"At last came the transformation: {hero.label} lifted the plate again, and this time did not tremble."
    )
    world.say(
        f"The marked plate became a sign of safe passage, and the {beast.label} rose away as if the air itself had decided the lesson was learned."
    )


def tell(params: StoryParams) -> World:
    world = set_initial_world(params)
    narrate_setup(world)
    world.para()
    if predict_swoop(world):
        swoop_interrupts(world)
        twist(world)
        transformation(world)
    else:
        world.say("Nothing interrupted the road, and so no myth could be born.")
    world.para()
    hero: Entity = world.facts["hero"]
    plate: Entity = world.facts["plate"]
    keeper: Entity = world.facts["keeper"]
    world.say(
        f"In the end, {hero.label} carried the plate with calm hands, and {keeper.label} smiled at the new quiet shine."
    )
    world.say(
        f"That was how the feast remembered the swoop: not as ruin, but as the moment the plate taught a child to become steadfast."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    keeper: Entity = f["keeper"]
    plate: Entity = f["plate"]
    beast: Entity = f["beast"]
    place: Place = f["place"]
    return [
        f'Write a short myth for children about {hero.label}, {plate.label}, and a sudden swoop in {place.label}.',
        f"Tell a story where {keeper.label} gives a sacred plate to {hero.label}, then a {beast.label} interrupts the ceremony.",
        "Write a mythic tale with a twist and a transformation after a flying creature startles a child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    keeper: Entity = f["keeper"]
    plate: Entity = f["plate"]
    beast: Entity = f["beast"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"Who was carrying the {plate.label} at first?",
            answer=f"{hero.label} was carrying the {plate.label} at first, while {keeper.label} watched the path."
        ),
        QAItem(
            question=f"What interrupted the feast path in {place.label}?",
            answer=f"A swift {beast.label} made a swoop and interrupted the procession."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the plate did not break. Instead, it revealed a hidden sign and changed the meaning of the moment."
        ),
        QAItem(
            question="What was transformed by the end?",
            answer=f"{hero.label} was transformed into someone steadier and braver, and the plate became a shining sign of safe passage."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a plate for?",
            answer="A plate is a flat dish used to hold food or offerings."
        ),
        QAItem(
            question="What does swoop mean?",
            answer="A swoop is a fast, sweeping movement through the air, like a bird dropping down suddenly."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what you expected."
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change in shape, state, or feeling."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

place(P) :- setting(P).
relic(R) :- plate(R).
creature(C) :- beast(C).

valid(P, R, C) :- setting(P), plate(R), beast(C), carries_possible(P), swoop_possible(C).
valid_story(P, R, C, H) :- valid(P, R, C), hero(H).

carries_possible(P) :- affords(P, carry).
swoop_possible(C) :- swoop_strength(C, S), S >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
        if place.sacred:
            lines.append(asp.fact("sacred", pid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("plate", rid))
        lines.append(asp.fact("region", rid, relic.region))
        if relic.blessed:
            lines.append(asp.fact("blessed", rid))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("beast", cid))
        lines.append(asp.fact("swoop_strength", cid, int(creature.swoop_strength * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Curated story set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="hall", hero_kind="girl", hero_name="Nia", keeper_kind="priestess", keeper_name="Mara", relic="plate", creature="hawk"),
    StoryParams(place="courtyard", hero_kind="boy", hero_name="Ari", keeper_kind="priest", keeper_name="Sol", relic="offering_plate", creature="windbird"),
    StoryParams(place="temple_steps", hero_kind="girl", hero_name="Mina", keeper_kind="mother", keeper_name="Ila", relic="gold_plate", creature="nightkite"),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: interruption, plate, swoop, twist, transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-kind", choices=HERO_KINDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--keeper-kind", choices=KEEPER_KINDS)
    ap.add_argument("--keeper-name")
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--creature", choices=CREATURES)
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
    place = args.place or _choice(rng, list(PLACES))
    relic = args.relic or _choice(rng, list(RELICS))
    creature = args.creature or _choice(rng, list(CREATURES))
    hero_kind = args.hero_kind or _choice(rng, HERO_KINDS)
    keeper_kind = args.keeper_kind or _choice(rng, KEEPER_KINDS)
    hero_name = args.hero_name or _choice(rng, HERO_NAMES)
    keeper_name = args.keeper_name or _choice(rng, KEEPER_NAMES)
    return StoryParams(
        place=place,
        hero_kind=hero_kind,
        hero_name=hero_name,
        keeper_kind=keeper_kind,
        keeper_name=keeper_name,
        relic=relic,
        creature=creature,
    )


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"place={world.place.label}")
    lines.extend(world.trace_log)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible (place, relic, creature) combos ({len(stories)} with hero facts):\n")
        for p, r, c in combos:
            print(f"  {p:12} {r:16} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.relic} in {p.place} against {p.creature}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
