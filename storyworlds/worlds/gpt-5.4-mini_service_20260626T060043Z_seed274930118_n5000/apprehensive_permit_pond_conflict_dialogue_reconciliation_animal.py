#!/usr/bin/env python3
"""
A tiny animal-story world set at the pond.

Premise:
- An animal child wants to enjoy the pond.
- A cautious caretaker worries about a permit and pond rules.
- Dialogue creates conflict.
- A small reconciliation makes the ending gentle and complete.

Seed words requested by the generator:
- apprehensive
- permit

This file is self-contained and follows the Storyweavers storyworld contract.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "animal"
    role: str = ""
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        # Animal story style: mostly "they" for simplicity and warmth.
        forms = {"subject": "they", "object": "them", "possessive": "their"}
        return forms[case]


@dataclass
class Pond:
    name: str = "the pond"
    has_lilypads: bool = True
    has_reeds: bool = True
    requires_permit: bool = True
    quiet: bool = True


@dataclass
class Offer:
    id: str
    label: str
    helps_with: set[str] = field(default_factory=set)
    phrase: str = ""
    plural: bool = False


@dataclass
class StoryParams:
    pond: str = "pond"
    hero: str = "raccoon"
    caretaker: str = "beaver"
    offer: str = "permit"
    seed: Optional[int] = None


@dataclass
class World:
    pond: Pond
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
POND = Pond()

HEROES = {
    "raccoon": {"name": "Rory", "traits": ["curious", "brave"]},
    "otter": {"name": "Milo", "traits": ["playful", "bouncy"]},
    "duck": {"name": "Pippa", "traits": ["cheerful", "quick"]},
    "frog": {"name": "Nico", "traits": ["small", "spry"]},
}

CARETAKERS = {
    "beaver": {"name": "Bram", "traits": ["careful", "steady"]},
    "turtle": {"name": "Tessa", "traits": ["calm", "watchful"]},
    "heron": {"name": "Hale", "traits": ["tall", "patient"]},
}

OFFERS = {
    "permit": Offer(
        id="permit",
        label="permit",
        helps_with={"entry"},
        phrase="a little permit from the pond keeper",
    ),
    "badge": Offer(
        id="badge",
        label="badge",
        helps_with={"entry"},
        phrase="a bright badge showing they had permission",
    ),
    "leaf_pass": Offer(
        id="leaf_pass",
        label="leaf pass",
        helps_with={"entry"},
        phrase="a soft leaf pass with a stamped mark",
    ),
}

HERO_ORDER = ["raccoon", "otter", "duck", "frog"]
CARETAKER_ORDER = ["beaver", "turtle", "heron"]
OFFER_ORDER = ["permit", "badge", "leaf_pass"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A pond story is valid when the hero wants to enter the pond area,
% the caretaker is apprehensive about safety or rules,
% and the offered item can resolve the conflict.
conflict(H, C, O) :- hero(H), caretaker(C), offer(O), apprehensive(C), wants_entry(H), requires_permission.
resolution(O) :- offer(O), permits_entry(O).
valid_story(H, C, O) :- conflict(H, C, O), resolution(O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("requires_permission"))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
        lines.append(asp.fact("wants_entry", h))
    for c in CARETAKERS:
        lines.append(asp.fact("caretaker", c))
        lines.append(asp.fact("apprehensive", c))
    for o in OFFERS:
        lines.append(asp.fact("offer", o))
        if o == "permit":
            lines.append(asp.fact("permits_entry", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_story_triples() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set()
    for h in HEROES:
        for c in CARETAKERS:
            for o in OFFERS:
                if o == "permit":
                    expected.add((h, c, o))
    actual = set(asp_valid_story_triples())
    if actual == expected:
        print(f"OK: clingo gate matches Python gate ({len(actual)} combinations).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if actual - expected:
        print("  only in clingo:", sorted(actual - expected))
    if expected - actual:
        print("  only in python:", sorted(expected - actual))
    return 1


# ---------------------------------------------------------------------------
# Core world logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero species: {params.hero}")
    if params.caretaker not in CARETAKERS:
        raise StoryError(f"Unknown caretaker species: {params.caretaker}")
    if params.offer not in OFFERS:
        raise StoryError(f"Unknown offer: {params.offer}")

    world = World(pond=POND)
    hero_def = HEROES[params.hero]
    caretaker_def = CARETAKERS[params.caretaker]
    offer_def = OFFERS[params.offer]

    hero = world.add(
        Entity(
            id="Hero",
            kind="character",
            species=params.hero,
            role="child",
            label=hero_def["name"],
            traits=list(hero_def["traits"]),
            meters={"joy": 0.0, "tension": 0.0},
            memes={"apprehension": 0.0},
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            species=params.caretaker,
            role="caretaker",
            label=caretaker_def["name"],
            traits=list(caretaker_def["traits"]),
            meters={"calm": 0.0},
            memes={"apprehension": 1.0},
        )
    )
    permit = world.add(
        Entity(
            id="Permit",
            kind="thing",
            species="paper",
            role="permission",
            label=offer_def.label,
            traits=["small", "important"],
            owner=caretaker.id,
            worn_by=None,
            caretaker=caretaker.id,
            meters={"clean": 1.0},
            memes={"value": 1.0},
        )
    )

    world.facts.update(hero=hero, caretaker=caretaker, permit=permit, offer=offer_def)
    return world


def resolve_stay_safe(world: World) -> bool:
    hero = world.get("Hero")
    caretaker = world.get("Caretaker")
    permit = world.get("Permit")

    if not world.pond.requires_permit:
        return False

    hero.memes["apprehension"] += 0.2
    caretaker.memes["apprehension"] += 0.3
    hero.meters["tension"] += 1.0
    caretaker.meters["calm"] += 0.0

    world.say(
        f"At {world.pond.name}, {hero.label} the {hero.species} wanted to splash by the reeds, "
        f"but {caretaker.label} the {caretaker.species} looked apprehensive and held up the little permit."
    )
    world.say(
        f'"We need a permit first," {caretaker.label} said. '
        f'"The pond stays peaceful when everyone follows the rules."'
    )
    world.say(
        f'{hero.label} frowned and whispered, "I only wanted to watch the lily pads."'
    )

    world.facts["conflict"] = True
    world.facts["permit_needed"] = True
    return permit is not None


def reconcile(world: World) -> None:
    hero = world.get("Hero")
    caretaker = world.get("Caretaker")
    permit = world.get("Permit")

    world.say(
        f"{hero.label} took a slow breath, and {caretaker.label} softened their voice."
    )
    world.say(
        f'"How about this?" {caretaker.label} said. '
        f'"I can sign the permit, and you can stay close to the shore."'
    )
    world.say(
        f'{hero.label} nodded. "That sounds fair," {hero.label} said, '
        f"and the worry between them grew smaller."
    )

    hero.meters["tension"] = max(0.0, hero.meters["tension"] - 1.0)
    hero.memes["apprehension"] = max(0.0, hero.memes["apprehension"] - 0.7)
    caretaker.memes["apprehension"] = max(0.0, caretaker.memes["apprehension"] - 0.8)
    hero.meters["joy"] += 1.0
    caretaker.meters["calm"] += 1.0
    permit.memes["value"] += 0.5
    world.facts["resolved"] = True
    world.facts["conflict"] = False

    world.say(
        f"With the permit signed, {hero.label} watched dragonflies skim the water while {caretaker.label} smiled beside them."
    )


def close_story(world: World) -> None:
    hero = world.get("Hero")
    caretaker = world.get("Caretaker")
    world.say(
        f"By the end, the pond was still quiet, the permit was tucked safely away, and {hero.label} and {caretaker.label} felt proud of their careful promise."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def choose_name(species: str, rng: random.Random) -> str:
    base = HEROES.get(species) or CARETAKERS.get(species)
    return base["name"] if base else rng.choice(["Rory", "Milo", "Pippa"])


def generate_story(world: World) -> None:
    hero = world.get("Hero")
    caretaker = world.get("Caretaker")

    world.say(
        f"{hero.label} was a {hero.traits[0]} {hero.species} who loved the pond."
    )
    world.say(
        f"{caretaker.label} was a {caretaker.traits[0]} {caretaker.species} who kept an eye on the water and the little rules."
    )
    world.say(
        f"One morning, {hero.label} noticed the reeds swaying and felt very apprehensive about waiting."
    )
    resolve_stay_safe(world)
    reconcile(world)
    close_story(world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    return [
        f"Write a short animal story set at the pond where {hero.label} wants to go closer to the water but {caretaker.label} is apprehensive about a permit.",
        f"Tell a gentle dialogue story about a pond, a permit, conflict, and reconciliation between a {hero.species} and a {caretaker.species}.",
        f"Write a child-friendly animal story that includes the words apprehensive and permit and ends with everyone feeling safe by the pond.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("Hero")
    caretaker = world.get("Caretaker")
    permit = world.get("Permit")
    return [
        QAItem(
            question=f"Who was apprehensive at the pond?",
            answer=f"{caretaker.label} was apprehensive because they wanted the pond to stay safe and peaceful."
        ),
        QAItem(
            question=f"What did the animals need before going closer to the pond?",
            answer=f"They needed a permit, and {caretaker.label} signed it before {hero.label} stayed near the shore."
        ),
        QAItem(
            question=f"How did the conflict get solved?",
            answer=f"They talked it through, agreed to use the permit, and chose a safe way for {hero.label} to enjoy the pond."
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.label} watched the water happily while {caretaker.label} smiled, and the pond felt calm again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a permit?",
            answer="A permit is permission on paper or from an authority that says it is okay to do something."
        ),
        QAItem(
            question="What is a pond?",
            answer="A pond is a small body of still water, often home to reeds, frogs, ducks, and other little animals."
        ),
        QAItem(
            question="Why can a caretaker feel apprehensive?",
            answer="A caretaker can feel apprehensive when they worry that a choice might be unsafe or break a rule."
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} species={e.species} role={e.role} label={e.label} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def asp_program_text() -> str:
    return asp_program("#show valid_story/3.")


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    _ = rng  # reserved for future variation; story remains deterministic by params
    world = build_world(params)
    generate_story(world)
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
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world set at the pond: apprehensive, permit, conflict, dialogue, reconciliation."
    )
    ap.add_argument("--pond", choices=["pond"], default="pond")
    ap.add_argument("--hero", choices=sorted(HEROES), default=None)
    ap.add_argument("--caretaker", choices=sorted(CARETAKERS), default=None)
    ap.add_argument("--offer", choices=sorted(OFFERS), default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_ORDER)
    caretaker = args.caretaker or rng.choice(CARETAKER_ORDER)
    offer = args.offer or "permit"
    if offer != "permit":
        raise StoryError("This world only supports the permit resolution.")
    return StoryParams(pond="pond", hero=hero, caretaker=caretaker, offer=offer)


CURATED = [
    StoryParams(pond="pond", hero="raccoon", caretaker="beaver", offer="permit", seed=1),
    StoryParams(pond="pond", hero="otter", caretaker="turtle", offer="permit", seed=2),
    StoryParams(pond="pond", hero="duck", caretaker="heron", offer="permit", seed=3),
    StoryParams(pond="pond", hero="frog", caretaker="beaver", offer="permit", seed=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} valid stories:")
        for t in triples:
            print(" ", t)
        return

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} with {p.caretaker} at the pond"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
