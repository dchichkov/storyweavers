#!/usr/bin/env python3
"""
storyworlds/worlds/pixie_horoscope_bus_depot_reconciliation_myth.py
====================================================================

A small mythic storyworld about a pixie, a horoscope, and reconciliation at a
bus depot.

Premise:
- A pixie reads a horoscope before a trip.
- The horoscope warns of delay, but pride or hurt causes tension.
- A missed bus creates the turn.
- A humble reconciliation changes the ending image.

The world is intentionally tiny and state-driven:
- meters track physical things like time missed, dust, and carried scrolls
- memes track emotional states like pride, hurt, and reconciliation

The tone aims for myth: concrete, ceremonial, and gentle.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["weight", "dust", "delay", "carried", "stopped"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "hurt", "hope", "regret", "reconciliation", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"pixie", "girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bus depot"
    afford_trip: bool = True


@dataclass
class Omen:
    id: str
    sign: str
    meaning: str
    delay: float
    advice: str
    mood: str
    keyword: str = "horoscope"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bus_depot": Setting(place="the bus depot", afford_trip=True),
}

OMENS = {
    "delay": Omen(
        id="delay",
        sign="a quiet clock and a late tire track",
        meaning="the road will ask for patience",
        delay=1.0,
        advice="wait for the right bus",
        mood="solemn",
    ),
    "kindness": Omen(
        id="kindness",
        sign="a lamp shining on a shared bench",
        meaning="a small apology can open a wide gate",
        delay=0.0,
        advice="speak gently and share the seat",
        mood="warm",
    ),
    "storm": Omen(
        id="storm",
        sign="a cloud-shaped stain above the depot roof",
        meaning="hurt words gather like rain unless they are named",
        delay=2.0,
        advice="pause before speaking",
        mood="grave",
    ),
}

PIXIE_NAMES = ["Pippa", "Miri", "Luma", "Tilly", "Fae"]
COMPANION_NAMES = ["Bram", "Nell", "Orin", "Sera", "Rook"]

TRAITS = ["curious", "bright", "stubborn", "gentle", "brave"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "bus_depot"
    omen: str = "delay"
    name: str = "Pippa"
    companion: str = "Bram"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for omen_id in OMENS:
            combos.append((place, omen_id))
    return combos


def explain_rejection(place: str, omen_id: str) -> str:
    return f"(No story: the omen '{omen_id}' cannot be staged at {SETTINGS[place].place}.)"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def introduce(world: World, pixie: Entity, companion: Entity, omen: Omen) -> None:
    world.say(
        f"Long ago at {world.setting.place}, a little {pixie.trait} pixie named {pixie.id} "
        f"kept a folded horoscope close to {pixie.pronoun('possessive')} heart."
    )
    world.say(
        f"The sign on the page was {omen.sign}, and its meaning said that {omen.meaning}."
    )
    pixie.memes["hope"] += 1
    pixie.meters["carried"] += 1


def read_horoscope(world: World, pixie: Entity, omen: Omen) -> None:
    pixie.memes["pride"] += 1
    world.say(
        f"{pixie.id} read the horoscope and frowned. "
        f'\"It says I should {omen.advice},\" {pixie.pronoun()} whispered, '
        f"\"but I want to leave at once.\""
    )


def gather_at_depot(world: World, pixie: Entity, companion: Entity) -> None:
    world.say(
        f"Beside the sleeping buses, {pixie.id} met {companion.id}, "
        f"who waited under the depot clock."
    )
    companion.memes["hope"] += 1


def miss_bus(world: World, pixie: Entity, companion: Entity, omen: Omen) -> None:
    pixie.meters["delay"] += omen.delay
    if omen.delay > 0:
        pixie.memes["hurt"] += 1
        companion.memes["hurt"] += 1
        world.say(
            f"{pixie.id} rushed too soon, and the silver bus whispered past like a fish in moonlight. "
            f"Their chance was gone."
        )


def quarrel(world: World, pixie: Entity, companion: Entity, omen: Omen) -> None:
    if pixie.memes["hurt"] >= THRESHOLD:
        pixie.memes["pride"] += 1
        companion.memes["hurt"] += 1
        world.say(
            f"{pixie.id} blamed the horoscope. {companion.id} blamed the haste. "
            f"The depot felt suddenly cold."
        )


def reconcile(world: World, pixie: Entity, companion: Entity, omen: Omen) -> None:
    pixie.memes["reconciliation"] += 1
    companion.memes["reconciliation"] += 1
    pixie.memes["hurt"] = 0.0
    companion.memes["hurt"] = 0.0
    pixie.memes["pride"] = max(0.0, pixie.memes["pride"] - 1.0)
    world.say(
        f"Then {pixie.id} looked back at the folded horoscope and bowed {pixie.pronoun('possessive')} head. "
        f'\"The sign was trying to help me,\" {pixie.pronoun()} said. '
        f'\"I am sorry.\"'
    )
    world.say(
        f"{companion.id} smiled, and the two of them shared the bench while they waited for the next bus. "
        f"Their words grew soft again, like wool around a candle."
    )


def arrive_next_bus(world: World, pixie: Entity, companion: Entity) -> None:
    world.say(
        f"When the next bus came, it was not a triumphing thunder-beast but a patient blue giant. "
        f"{pixie.id} and {companion.id} boarded together, side by side."
    )
    pixie.memes["calm"] += 1
    companion.memes["calm"] += 1


def ending_image(world: World, pixie: Entity, companion: Entity, omen: Omen) -> None:
    world.say(
        f"At sunset, the horoscope still rested in {pixie.pronoun('possessive')} hands, "
        f"but now it felt like a lantern instead of a warning. "
        f"At the bus depot, {pixie.id} and {companion.id} sat peaceful as the wheels hummed away."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(bus_depot).

omen(delay).
omen(kindness).
omen(storm).

compat(P,O) :- place(P), omen(O), P = bus_depot.

#show compat/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for omen in OMENS:
        lines.append(asp.fact("omen", omen))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compat/2."))
    return sorted(set(asp.atoms(model, "compat")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    ax2 = {(p, o) for (p, o) in ax}
    if py == ax2:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if ax2 - py:
        print("  only in clingo:", sorted(ax2 - py))
    if py - ax2:
        print("  only in python:", sorted(py - ax2))
    return 1


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------

def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story set at {f["place_text"]} about a pixie and a horoscope.',
        f'Tell a gentle myth where {f["name"]} reads a horoscope, makes a mistake, and then reconciles with {f["companion"]}.',
        f'Write a child-friendly legend that includes the word "{f["omen"].keyword}" and ends in reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pixie: Entity = f["pixie"]
    companion: Entity = f["companion"]
    omen: Omen = f["omen"]
    return [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {pixie.id}, a {pixie.trait} pixie, and {companion.id}, who waited with {pixie.pronoun('object')} at the depot.",
        ),
        QAItem(
            question=f"What did {pixie.id} read before the trouble began?",
            answer=f"{pixie.id} read a horoscope that said {omen.meaning}.",
        ),
        QAItem(
            question=f"Why did {pixie.id} and {companion.id} miss the first bus?",
            answer=f"They missed it because {pixie.id} rushed before {omen.advice} could be followed.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{pixie.id} and {companion.id} apologized, shared the bench, and reconciled before the next bus came.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    omen: Omen = f["omen"]
    return [
        QAItem(
            question="What is a horoscope?",
            answer="A horoscope is a message about what may happen, often read from stars or signs.",
        ),
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses wait, rest, and begin their routes.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace and become friendly again.",
        ),
        QAItem(
            question="Why can waiting be wise in a story?",
            answer=f"Waiting can be wise when the sign says to {omen.advice}, because haste can cause trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        bits.append(f"type={e.type}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    omen = OMENS[params.omen]
    world = World(setting)

    pixie = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="pixie",
            traits=[params.trait],
        )
    )
    pixie.trait = params.trait  # for direct narration convenience
    companion = world.add(
        Entity(
            id=params.companion,
            kind="character",
            type="companion",
            traits=["patient", "kind"],
        )
    )
    scroll = world.add(
        Entity(
            id="horoscope",
            kind="thing",
            type="scroll",
            label="horoscope",
            phrase="a folded horoscope",
            owner=pixie.id,
            caretaker=pixie.id,
        )
    )
    bus = world.add(
        Entity(
            id="bus",
            kind="thing",
            type="bus",
            label="bus",
            phrase="a blue bus",
        )
    )

    world.facts.update(
        place=params.place,
        place_text=setting.place,
        omen=omen,
        pixie=pixie,
        companion=companion,
        scroll=scroll,
        bus=bus,
        name=pixie.id,
    )

    # Act I: the omen is read.
    introduce(world, pixie, companion, omen)
    world.para()
    read_horoscope(world, pixie, omen)
    gather_at_depot(world, pixie, companion)

    # Act II: the failure and the hurt.
    world.para()
    miss_bus(world, pixie, companion, omen)
    quarrel(world, pixie, companion, omen)

    # Act III: reconciliation and a gentler departure.
    world.para()
    reconcile(world, pixie, companion, omen)
    arrive_next_bus(world, pixie, companion)
    ending_image(world, pixie, companion, omen)

    world.facts["resolved"] = True
    return world


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(f"Unknown place: {args.place}")
    if args.omen and args.omen not in OMENS:
        raise StoryError(f"Unknown omen: {args.omen}")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.omen is None or c[1] == args.omen)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, omen = rng.choice(sorted(combos))
    name = args.name or rng.choice(PIXIE_NAMES)
    companion = args.companion or rng.choice(COMPANION_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, omen=omen, name=name, companion=companion, trait=trait)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return valid_story_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=story_text(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="bus_depot", omen="delay", name="Pippa", companion="Bram", trait="curious"),
    StoryParams(place="bus_depot", omen="kindness", name="Luma", companion="Sera", trait="gentle"),
    StoryParams(place="bus_depot", omen="storm", name="Miri", companion="Orin", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a pixie, a horoscope, and reconciliation at a bus depot."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compat/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            header = f"### {p.name}: {p.omen} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
