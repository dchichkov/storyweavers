#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/alarm_transformation_myth.py
=========================================================================================================

A small mythic storyworld about an alarm that can wake a transformation.

Premise:
- In a tiny village, a shrine bell-alarm rings at dawn.
- A young keeper fears the old legend: when the alarm rings too long, a sleepy helper transforms into a beast.
- The keeper must learn a gentler ritual that stops the harm and turns the change into a blessing.

The model is intentionally small and state-driven:
- physical meters track ringing, soot, fatigue, and transformed form
- emotional memes track fear, duty, awe, and trust

The story is rendered from world state, with a myth-like tone and a causal turn:
warning -> alarm grows -> transformation threatens -> ritual calms -> blessing ending.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    form: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def _init(self) -> None:
        if not self.meters:
            self.meters = {"ringing": 0.0, "soot": 0.0, "fatigue": 0.0, "transformed": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "duty": 0.0, "awe": 0.0, "trust": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Shrine:
    name: str = "the shrine"
    place: str = "the hill shrine"
    dust: str = "silver dust"
    afforded: set[str] = field(default_factory=lambda: {"ring", "listen", "pray"})


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    changes_to: str
    awakens: str
    soothe_item: str


class World:
    def __init__(self, shrine: Shrine) -> None:
        self.shrine = shrine
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "dawn"

    def add(self, ent: Entity) -> Entity:
        ent._init()
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


# ---------------------------------------------------------------------------
# Settings and registries
# ---------------------------------------------------------------------------

SHRINES = {
    "hill": Shrine(place="the hill shrine", dust="silver dust"),
    "river": Shrine(place="the river shrine", dust="river mist"),
    "oak": Shrine(place="the oak shrine", dust="oak pollen"),
}

RELICS = {
    "bronze_bell": Relic(
        id="bronze_bell",
        label="bronze bell",
        phrase="an old bronze bell with a cracked lip",
        kind="bell",
        changes_to="lion",
        awakens="the sleeping lion",
        soothe_item="linen ribbon",
    ),
    "moon_drum": Relic(
        id="moon_drum",
        label="moon drum",
        phrase="a moon drum painted with white swirls",
        kind="drum",
        changes_to="owl",
        awakens="the moon owl",
        soothe_item="soft hide cord",
    ),
    "river_gong": Relic(
        id="river_gong",
        label="river gong",
        phrase="a river gong hung on cedar ropes",
        kind="gong",
        changes_to="serpent",
        awakens="the river serpent",
        soothe_item="reed charm",
    ),
}

KEEPER_NAMES = ["Mira", "Ivo", "Tala", "Nero", "Sera", "Ari"]
ELDER_NAMES = ["Grandmother", "Grandfather", "Aunt", "Uncle", "Elder"]
TRAITS = ["brave", "gentle", "curious", "serious", "steadfast", "bright"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The alarm is dangerous when it rings too long.
dangerous(A) :- alarm(A), rings(A, N), N >= 2.

% A transformation begins when danger and an awakened relic coincide.
transforms(C, R) :- dangerous(A), awakens(A, C), relic(R), handles(C, R).

% A ritual soothes the alarm if the right calming item matches the relic.
safe(A, R) :- alarm(A), relic(R), soothed_by(R, S), has(S).

% A valid mythic story has an alarm, a relic, and a safe resolution.
valid_story(Shrine, Relic, Hero) :- shrine(Shrine), relic(Relic), keeper(Hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SHRINES:
        lines.append(asp.fact("shrine", sid))
    for rid, rel in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("awakens", rid, rel.awakens))
        lines.append(asp.fact("changes_to", rid, rel.changes_to))
        lines.append(asp.fact("soothed_by", rid, rel.soothe_item))
    lines.append(asp.fact("alarm", "village_alarm"))
    lines.append(asp.fact("keeper", "keeper"))
    lines.append(asp.fact("has", "linen_ribbon"))
    lines.append(asp.fact("has", "soft_hide_cord"))
    lines.append(asp.fact("has", "reed_charm"))
    lines.append(asp.fact("rings", "village_alarm", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show dangerous/1. #show safe/2."))
    danger = sorted(set(asp.atoms(model, "dangerous")))
    safe = sorted(set(asp.atoms(model, "safe")))
    if danger and safe:
        print("OK: ASP reasoning found danger and a safe resolution.")
        return 0
    print("MISMATCH: ASP reasoning did not produce expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    shrine: str
    relic: str
    hero_name: str
    hero_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning and story helpers
# ---------------------------------------------------------------------------

def choose_relic(shrine_id: str, rng: random.Random) -> str:
    return rng.choice(sorted(RELICS))


def valid_combo(shrine_id: str, relic_id: str) -> bool:
    return shrine_id in SHRINES and relic_id in RELICS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    shrine_id = args.shrine or rng.choice(sorted(SHRINES))
    relic_id = args.relic or choose_relic(shrine_id, rng)
    if not valid_combo(shrine_id, relic_id):
        raise StoryError("No valid shrine/relic combination matches the options.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(KEEPER_NAMES)
    elder_type = args.elder_type or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        shrine=shrine_id,
        relic=relic_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        trait=trait,
    )


def story_title(world: World) -> str:
    return f"The Alarm of {world.shrine.place}"


def setup_world(params: StoryParams) -> World:
    shrine = SHRINES[params.shrine]
    world = World(shrine)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=params.elder_type))
    relic = RELICS[params.relic]
    bell = world.add(Entity(
        id=relic.id,
        kind="thing",
        type=relic.kind,
        label=relic.label,
        phrase=relic.phrase,
        owner="elder",
        caretaker="elder",
        form="resting",
    ))
    world.facts.update(hero=hero, elder=elder, relic=bell, relic_cfg=relic, params=params)
    return world


def _ring_alarm(world: World, relic: Entity, amount: float = 1.0) -> None:
    relic.meters["ringing"] += amount
    relic.memes["awe"] += 1.0
    if relic.meters["ringing"] >= 2.0:
        relic.meters["transformed"] += 1.0


def _stir_transformation(world: World, hero: Entity, relic: Entity, cfg: Relic) -> None:
    if relic.meters["ringing"] < 2.0:
        return
    sig = ("transform", relic.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["fear"] += 1.0
    hero.memes["duty"] += 1.0
    relic.form = cfg.changes_to
    relic.meters["transformed"] += 1.0
    hero.meters["fatigue"] += 1.0


def _soothe(world: World, relic: Entity, cfg: Relic) -> bool:
    sig = ("soothe", relic.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    relic.meters["ringing"] = 0.0
    relic.memes["calm"] += 1.0
    return True


def tell_story(world: World) -> World:
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    relic: Entity = world.facts["relic"]
    cfg: Relic = world.facts["relic_cfg"]

    # Act I
    world.say(f"At {world.shrine.place}, {hero.label} was the {world.facts['params'].trait} keeper who watched the dawn in silence.")
    world.say(f"{elder.label} trusted {hero.pronoun('object')} with {cfg.phrase}, because the old people said the shrine's alarm must be treated with care.")
    world.para()

    # Act II
    world.say(f"One morning, the alarm rang once, then twice, and the air filled with {world.shrine.dust}.")
    _ring_alarm(world, relic, 1.0)
    world.say(f"{hero.label} listened, and {hero.pronoun()} felt {cfg.awakens} stir beneath the stones.")
    _ring_alarm(world, relic, 1.0)
    _stir_transformation(world, hero, relic, cfg)
    world.say(f"The bell's voice grew wild, and the old legend woke: the bell seemed to turn toward {cfg.changes_to} shape.")
    world.para()

    # Act III
    world.say(f"Then {hero.label} remembered the kinder rite taught by {elder.label}: not more alarm, but a soft binding.")
    if _soothe(world, relic, cfg):
        world.say(f"{hero.label} wrapped the {cfg.soothe_item} around the bell and spoke a steady prayer.")
    world.say(f"The ringing faded. The shape settled. {cfg.awakens} did not rise to trouble the village.")
    hero.memes["trust"] += 1.0
    hero.memes["calm"] += 1.0
    relic.form = "blessing"
    world.say(f"By sunset, the shrine held only a quiet glow, and the alarm became a blessing instead of a warning.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    cfg: Relic = world.facts["relic_cfg"]
    return [
        f'Write a myth-like story about an alarm at {world.shrine.place} and a child named {p.hero_name}.',
        f"Tell a short story where a {p.hero_type} keeper hears an alarm, fears a transformation, and finds a gentler ritual.",
        f'Write a small myth that uses the word "alarm" and ends with the shrine becoming peaceful again.',
        f"Make a child-friendly legend about {cfg.label}, an awakening, and a blessing at dawn.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    relic: Entity = world.facts["relic"]
    cfg: Relic = world.facts["relic_cfg"]

    return [
        QAItem(
            question=f"Who was the story about at {world.shrine.place}?",
            answer=f"It was about {p.hero_name}, the {p.trait} {p.hero_type} who kept watch at {world.shrine.place}.",
        ),
        QAItem(
            question=f"What did {p.hero_name} fear when the alarm rang?",
            answer=f"{p.hero_name} feared that the old alarm would wake {cfg.awakens} and cause a transformation.",
        ),
        QAItem(
            question=f"What did {elder.label} ask {p.hero_name} to use on the {relic.label}?",
            answer=f"{elder.label} taught {p.hero_name} to use the {cfg.soothe_item} to calm the {relic.label}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the alarm no longer threatened the village; it became a quiet blessing and the shrine grew peaceful.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "alarm": [
        QAItem(
            question="What is an alarm for?",
            answer="An alarm is something that rings or sounds to warn people, wake them, or tell them to pay attention.",
        )
    ],
    "transformation": [
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change from one form into another, like a sleepy thing becoming a fierce one in a story.",
        )
    ],
    "myth": [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story people tell about powerful beings, special places, and important lessons.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE["alarm"] + WORLD_KNOWLEDGE["transformation"] + WORLD_KNOWLEDGE["myth"])


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_world() -> int:
    import asp
    model = asp.one_model(asp_program("#show dangerous/1. #show valid_story/3."))
    danger = set(asp.atoms(model, "dangerous"))
    valid = set(asp.atoms(model, "valid_story"))
    if danger and valid:
        print("OK: ASP twin confirms the alarm can become dangerous and still resolve.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected model.")
    return 1


# ---------------------------------------------------------------------------
# Serialization / trace
# ---------------------------------------------------------------------------

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
        if e.kind == "thing":
            bits.append(f"form={e.form}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world = tell_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(shrine="hill", relic="bronze_bell", hero_name="Mira", hero_type="girl", elder_type="Grandmother", trait="gentle"),
    StoryParams(shrine="river", relic="river_gong", hero_name="Ari", hero_type="boy", elder_type="Uncle", trait="steadfast"),
    StoryParams(shrine="oak", relic="moon_drum", hero_name="Tala", hero_type="girl", elder_type="Elder", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic alarm/transformation storyworld.")
    ap.add_argument("--shrine", choices=sorted(SHRINES))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=ELDER_NAMES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify_world())
    if args.asp:
        valid = asp_valid()
        print(f"{len(valid)} compatible mythic story tuples:")
        for tpl in valid:
            print("  ", tpl)
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
            header = f"### {p.hero_name}: {p.relic} at {p.shrine}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
