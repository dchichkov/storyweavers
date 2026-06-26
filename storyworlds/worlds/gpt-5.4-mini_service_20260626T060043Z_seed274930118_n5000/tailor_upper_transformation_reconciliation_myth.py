#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tailor_upper_transformation_reconciliation_myth.py
==================================================================================================

A small mythic storyworld about a tailor, an upper garment, transformation, and reconciliation.

Premise:
- A gifted tailor prepares an upper robe for a young hero.
- The robe begins plain and tense with old marks of pride and rivalry.
- A transformation ritual remakes the robe, and the people attached to it must reconcile.

The story is intentionally small and constraint-checked:
- physical state: cloth, dye, shine, tear, fit, and work meters
- emotional state: pride, worry, wonder, hurt, and peace memes
- a mythic turn: the upper garment changes in a visible, narrated way
- a reconciliation turn: two people resolve a quarrel through the tailor's work

The world is not a frozen paragraph; prose is driven by the simulated state.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    maker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "queen", "sister"}
        male = {"man", "boy", "father", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the loom-house"
    wonders: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    tailor_name: str
    hero_name: str
    rival_name: str
    garment: str
    seed: Optional[int] = None


@dataclass
class GarmentSpec:
    label: str
    phrase: str
    region: str
    before: str
    after: str
    ritual: str
    symbolic: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "loom-house": Setting(place="the loom-house", wonders=["threads", "dyes", "spindles"]),
    "river-shrine": Setting(place="the river shrine", wonders=["water", "mist", "stones"]),
    "hill-market": Setting(place="the hill market", wonders=["bells", "bright cloth", "dust"]),
}

GARMENTS = {
    "upper-cloak": GarmentSpec(
        label="upper cloak",
        phrase="a plain upper cloak",
        region="upper",
        before="plain and stiff",
        after="bright and flowing",
        ritual="lifted to the dawn flame",
        symbolic="shone like a dawn-banner",
    ),
    "upper-robe": GarmentSpec(
        label="upper robe",
        phrase="a gray upper robe",
        region="upper",
        before="gray and weary",
        after="golden and soft",
        ritual="washed in silver water",
        symbolic="glowed like a summer cloud",
    ),
    "upper-tunic": GarmentSpec(
        label="upper tunic",
        phrase="an old upper tunic",
        region="upper",
        before="frayed at the seams",
        after="mended and radiant",
        ritual="singed with warm incense",
        symbolic="looked reborn",
    ),
}

TALES = {
    "upper-cloak": {"change": "cloak", "gift": "protection"},
    "upper-robe": {"change": "robe", "gift": "honor"},
    "upper-tunic": {"change": "tunic", "gift": "peace"},
}

TAILOR_NAMES = ["Ari", "Mira", "Ilan", "Sera", "Niko", "Tala", "Rin", "Lior"]
HERO_NAMES = ["Elin", "Orin", "Ada", "Kiran", "Lea", "Borin", "Noa", "Jori"]
RIVAL_NAMES = ["Sorin", "Mena", "Pavel", "Tiva", "Eran", "Luma", "Naren", "Iris"]
TRAITS = ["patient", "bright", "wary", "stubborn", "gentle", "earnest"]


# ---------------------------------------------------------------------------
# Rule system
# ---------------------------------------------------------------------------
def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    garment = world.get("garment")
    tailor = world.get("tailor")
    if garment.meters.get("prepared", 0) >= 1 and not garment.meters.get("transformed", 0):
        sig = ("transform", garment.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        garment.meters["transformed"] = 1
        garment.meters["shine"] = garment.meters.get("shine", 0) + 1
        tailor.memes["awe"] = tailor.memes.get("awe", 0) + 1
        out.append(f"The upper garment changed as if a hidden star had awakened inside it.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    rival = world.get("rival")
    garment = world.get("garment")
    if garment.meters.get("transformed", 0) and hero.memes.get("hurt", 0) and rival.memes.get("hurt", 0):
        sig = ("reconcile", hero.id, rival.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["peace"] = hero.memes.get("peace", 0) + 1
        rival.memes["peace"] = rival.memes.get("peace", 0) + 1
        hero.memes["hurt"] = 0
        rival.memes["hurt"] = 0
        out.append("Seeing the new splendor, the two old rivals lowered their voices and forgave each other.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_transform, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    tailor = world.add(Entity(id="tailor", kind="character", type="tailor", label=params.tailor_name, traits=["gifted", "patient"]))
    hero = world.add(Entity(id="hero", kind="character", type="person", label=params.hero_name, traits=["young", "hopeful"]))
    rival = world.add(Entity(id="rival", kind="character", type="person", label=params.rival_name, traits=["proud", "hurt"]))
    garment_cfg = GARMENTS[params.garment]
    garment = world.add(Entity(
        id="garment",
        kind="thing",
        type="garment",
        label=garment_cfg.label,
        phrase=garment_cfg.phrase,
        owner=hero.id,
        maker=tailor.id,
        worn_by=hero.id,
        region="upper",
        meters={"prepared": 0, "shine": 0, "transformed": 0},
        memes={"pride": 1, "worry": 1},
    ))
    world.facts.update(tailor=tailor, hero=hero, rival=rival, garment=garment, garment_cfg=garment_cfg)
    return world


def tell(world: World) -> World:
    f = world.facts
    tailor: Entity = f["tailor"]
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    garment: Entity = f["garment"]
    gspec: GarmentSpec = f["garment_cfg"]

    world.say(
        f"In {world.setting.place}, {tailor.label} was a tailor who listened to the murmur of thread and moonlight."
    )
    world.say(
        f"{hero.label} had been given {garment.phrase}, but it was still {gspec.before}, and {rival.label} said it could never become {gspec.after}."
    )

    world.para()
    hero.memes["hurt"] = 1
    rival.memes["hurt"] = 1
    tailor.meters["work"] = tailor.meters.get("work", 0) + 1
    world.say(
        f"That morning, the tailor took the {garment.label} to the sacred place and began the old craft."
    )
    world.say(
        f"{tailor.label} {gspec.ritual}, while {hero.label} watched with hope and {rival.label} watched with folded arms."
    )
    garment.meters["prepared"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"When the change was complete, the {garment.label} was no longer {gspec.before}; it was {gspec.after}, and it {gspec.symbolic}."
    )
    world.say(
        f"{hero.label} touched {garment.label} gently, and {rival.label} saw that the work had not stolen pride but made room for grace."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last {hero.label} and {rival.label} stood side by side beneath the transformed upper garment, and their quarrel loosened like a knot in warm hands."
    )
    world.say(
        f"The tailor smiled, because the upper thing had been remade, and the people around it had been remade too."
    )
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    gspec: GarmentSpec = f["garment_cfg"]
    return [
        f'Write a short mythic story about a tailor transforming an {gspec.label} and bringing reconciliation.',
        f"Tell a child-friendly myth where {f['tailor'].label} changes {f['hero'].label}'s {gspec.label} and helps two proud people make peace.",
        f'Write a small legend that includes a tailor, an upper garment, and a peaceful ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tailor: Entity = f["tailor"]
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    garment: Entity = f["garment"]
    gspec: GarmentSpec = f["garment_cfg"]
    return [
        QAItem(
            question=f"Who was the tailor in the story?",
            answer=f"The tailor was {tailor.label}, who worked in {world.setting.place} and shaped the upper garment with careful hands.",
        ),
        QAItem(
            question=f"What happened to the {gspec.label}?",
            answer=f"It changed from being {gspec.before} to being {gspec.after}. That transformation made it feel special and new.",
        ),
        QAItem(
            question=f"Why did {hero.label} and {rival.label} become peaceful again?",
            answer=f"They saw the transformed {gspec.label}, and the new beauty helped them lower their pride and reconcile.",
        ),
        QAItem(
            question=f"What did the upper garment prove at the end?",
            answer=f"It proved that something plain could become radiant, and that a quarrel could end in reconciliation.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does a tailor do?",
        answer="A tailor makes, alters, and repairs clothes so they fit well and look nice.",
    ),
    QAItem(
        question="What is transformation?",
        answer="Transformation means something changes into a new form or becomes very different from what it was before.",
    ),
    QAItem(
        question="What is reconciliation?",
        answer="Reconciliation is when people stop fighting and make peace again.",
    ),
    QAItem(
        question="What is the upper part of a garment?",
        answer="The upper part of a garment is the part that covers the chest, shoulders, and back.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
entity(tailor). entity(hero). entity(rival). entity(garment).
kind(tailor,character). kind(hero,character). kind(rival,character). kind(garment,thing).
region(garment,upper).

prepared(garment) :- fact_prepared(garment).
transformed(garment) :- prepared(garment).
reconciled(hero,rival) :- transformed(garment), hurt(hero), hurt(rival).

#show transformed/1.
#show reconciled/2.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("fact_prepared", "garment"),
        asp.fact("hurt", "hero"),
        asp.fact("hurt", "rival"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show transformed/1. #show reconciled/2."))
    transformed = set(asp.atoms(model, "transformed"))
    reconciled = set(asp.atoms(model, "reconciled"))
    ok = transformed == {("garment",)} and reconciled == {("hero", "rival")}
    if ok:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH: ASP twin does not match the Python story logic.")
    print("transformed:", sorted(transformed))
    print("reconciled:", sorted(reconciled))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(place, garment) for place in SETTINGS for garment in GARMENTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(f"Unknown place: {args.place}")
    if args.garment and args.garment not in GARMENTS:
        raise StoryError(f"Unknown garment: {args.garment}")

    place = args.place or rng.choice(list(SETTINGS))
    garment = args.garment or rng.choice(list(GARMENTS))
    tailor_name = args.tailor or rng.choice(TAILOR_NAMES)
    hero_name = args.hero or rng.choice(HERO_NAMES)
    rival_name = args.rival or rng.choice(RIVAL_NAMES)

    if hero_name == rival_name:
        raise StoryError("Hero and rival must be different people.")

    return StoryParams(
        place=place,
        tailor_name=tailor_name,
        hero_name=hero_name,
        rival_name=rival_name,
        garment=garment,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about a tailor, an upper garment, transformation, and reconciliation.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--garment", choices=list(GARMENTS))
    ap.add_argument("--tailor")
    ap.add_argument("--hero")
    ap.add_argument("--rival")
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
    StoryParams(place="river-shrine", tailor_name="Mira", hero_name="Elin", rival_name="Sorin", garment="upper-cloak"),
    StoryParams(place="loom-house", tailor_name="Ari", hero_name="Ada", rival_name="Iris", garment="upper-robe"),
    StoryParams(place="hill-market", tailor_name="Tala", hero_name="Kiran", rival_name="Naren", garment="upper-tunic"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show transformed/1. #show reconciled/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show transformed/1. #show reconciled/2."))
        print("transformed:", sorted(set(asp.atoms(model, "transformed"))))
        print("reconciled:", sorted(set(asp.atoms(model, "reconciled"))))
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
            header = f"### {p.tailor_name}: {p.garment} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
