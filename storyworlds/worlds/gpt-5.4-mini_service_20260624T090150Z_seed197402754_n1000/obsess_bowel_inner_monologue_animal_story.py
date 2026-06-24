#!/usr/bin/env python3
"""
A small storyworld about an animal who obsesses over a tummy/bowel worry,
hears an inner monologue, and finds a calm, kind solution.

The domain is intentionally tiny:
- one animal protagonist
- one helper parent/caregiver animal
- one bodily worry ("bowel" discomfort, rumble, or nervousness)
- one soft choice that resolves the worry

The prose engine simulates emotional and physical state changes, then narrates
them as a complete Animal Story-style tale with inner monologue.
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
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label(self) -> str:
        return self.name or self.species


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    calmness: float = 0.0


@dataclass
class Worry:
    id: str
    label: str
    verb: str
    source: str
    inner_voice: str
    risk_word: str = "bowel"


@dataclass
class Comfort:
    id: str
    label: str
    action: str
    helps: set[str] = field(default_factory=set)
    calm_bonus: float = 1.0


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "burrow": Place(id="burrow", label="the burrow", indoors=True, calmness=1.0),
    "meadow": Place(id="meadow", label="the meadow", indoors=False, calmness=0.3),
    "treehouse": Place(id="treehouse", label="the treehouse", indoors=True, calmness=0.7),
}

ANIMALS = {
    "rabbit": "rabbit",
    "fox": "fox",
    "badger": "badger",
    "hedgehog": "hedgehog",
    "squirrel": "squirrel",
}

WORRIES = {
    "rumble": Worry(
        id="rumble",
        label="a tummy rumble",
        verb="rumble",
        source="too much hurry",
        inner_voice="My bowel is making funny noises.",
        risk_word="bowel",
    ),
    "nerves": Worry(
        id="nerves",
        label="a nervous belly",
        verb="flutter",
        source="worry and rushing",
        inner_voice="What if my bowel feels strange at the wrong time?",
        risk_word="bowel",
    ),
    "ache": Worry(
        id="ache",
        label="a grumbly belly",
        verb="ache",
        source="a heavy snack",
        inner_voice="I hope my bowel settles down soon.",
        risk_word="bowel",
    ),
}

COMFORTS = {
    "slow_breath": Comfort(
        id="slow_breath",
        label="slow breaths",
        action="take three slow breaths",
        helps={"rumble", "nerves"},
        calm_bonus=1.0,
    ),
    "water": Comfort(
        id="water",
        label="a cup of water",
        action="sip a little water",
        helps={"rumble", "ache", "nerves"},
        calm_bonus=1.0,
    ),
    "rest": Comfort(
        id="rest",
        label="a quiet rest",
        action="sit in a quiet corner",
        helps={"rumble", "nerves", "ache"},
        calm_bonus=1.5,
    ),
    "warm_wrap": Comfort(
        id="warm_wrap",
        label="a warm wrap",
        action="press a warm wrap on their belly",
        helps={"ache", "nerves"},
        calm_bonus=1.5,
    ),
}

ACTIONS = {
    "eat_too_fast": {
        "label": "eat too fast",
        "effect": {"obsess": 1.0, "bowel": 1.0, "calm": -0.2},
        "tension_line": "The faster they ate, the more their bowel seemed to speak up.",
    },
    "rush_home": {
        "label": "rush home",
        "effect": {"obsess": 0.5, "bowel": 0.5, "calm": -0.1},
        "tension_line": "Rushing only made the worry grow bigger in their mind.",
    },
    "hide_under_leaf": {
        "label": "hide under a leaf",
        "effect": {"obsess": 0.8, "bowel": 0.2, "calm": -0.2},
        "tension_line": "Hiding did not make the bowl of worry any smaller.",
    },
}

CURATED = [
    ("rabbit", "burrow", "rumble", "slow_breath"),
    ("squirrel", "treehouse", "nerves", "water"),
    ("badger", "meadow", "ache", "rest"),
]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    species: str
    place: str
    worry: str
    comfort: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def inner_monologue(world: World, animal: Entity, worry: Worry) -> None:
    animal.memes["obsess"] = animal.memes.get("obsess", 0.0) + 1.0
    world.say(
        f"{animal.name} kept thinking, \"{worry.inner_voice}\""
    )


def trigger_worry(world: World, animal: Entity, worry: Worry) -> None:
    animal.meters["bowel"] = animal.meters.get("bowel", 0.0) + 1.0
    animal.memes["worry"] = animal.memes.get("worry", 0.0) + 1.0
    world.say(
        f"At {world.place.label}, {animal.name} felt {worry.label} after {worry.source}."
    )


def narrate_obsession(world: World, animal: Entity) -> None:
    level = animal.memes.get("obsess", 0.0)
    if level >= THRESHOLD:
        world.say(
            f"{animal.name} could not stop worrying about it, and the thought kept circling back."
        )


def offer_comfort(world: World, helper: Entity, animal: Entity, comfort: Comfort) -> bool:
    worry_state = world.facts["worry"]
    if worry_state.id not in comfort.helps:
        return False
    world.say(
        f"{helper.name} gently said, \"Let's {comfort.action}.\""
    )
    animal.memes["safe"] = animal.memes.get("safe", 0.0) + comfort.calm_bonus
    return True


def accept_comfort(world: World, animal: Entity, comfort: Comfort) -> None:
    animal.memes["worry"] = max(0.0, animal.memes.get("worry", 0.0) - 1.0)
    animal.memes["obsess"] = 0.0
    animal.meters["bowel"] = max(0.0, animal.meters.get("bowel", 0.0) - 0.5)
    world.say(
        f"{animal.name} tried it, and their belly began to feel easier."
    )
    world.say(
        f"Before long, the worry faded, and {animal.name} could smile again."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    worry = WORRIES[params.worry]
    comfort = COMFORTS[params.comfort]
    world = World(place)

    hero = world.add(Entity(
        id="hero",
        species=params.species,
        name=params.name,
        role="child",
    ))
    helper = world.add(Entity(
        id="helper",
        species="parent",
        name=f"{params.name}'s mama" if params.species != "badger" else f"{params.name}'s papa",
        role="helper",
    ))

    world.facts.update(hero=hero, helper=helper, worry=worry, comfort=comfort, place=place)

    world.say(
        f"{hero.name} was a little {params.species} who loved quiet places and tiny snacks."
    )
    world.say(
        f"One day, {hero.name} noticed {worry.label}, and their mind began to obsess over it."
    )
    inner_monologue(world, hero, worry)

    world.para()
    trigger_worry(world, hero, worry)
    narrate_obsession(world, hero)
    world.say(
        f"{hero.name} thought, \"What if my {worry.risk_word} keeps bothering me all day?\""
    )

    world.para()
    world.say(
        f"{helper.name} saw the worried face and came over with a gentle smile."
    )
    if offer_comfort(world, helper, hero, comfort):
        accept_comfort(world, hero, comfort)
    else:
        raise StoryError("No reasonable comfort matches this worry.")

    world.para()
    world.say(
        f"In the end, {hero.name} sat peacefully in {place.label}, feeling calm and brave."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    worry = f["worry"]
    comfort = f["comfort"]
    return [
        f"Write a gentle Animal Story about {hero.name}, an animal who obsessively worries about {worry.risk_word} feelings.",
        f"Tell a short story with inner monologue where {hero.name} thinks about {worry.label} and learns to calm down with {comfort.label}.",
        f"Write a child-friendly story about a little {hero.species} who says, \"I keep thinking about my {worry.risk_word}.\"",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    worry = f["worry"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"What did {hero.name} keep thinking about?",
            answer=f"{hero.name} kept thinking about {worry.label}, and the worry made them obsess for a while.",
        ),
        QAItem(
            question=f"Who helped {hero.name} feel better?",
            answer=f"{helper.name} helped by offering {comfort.label} and speaking in a gentle voice.",
        ),
        QAItem(
            question=f"How did {hero.name} feel at the end?",
            answer=f"At the end, {hero.name} felt calm and brave instead of stuck worrying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to obsess over something?",
            answer="To obsess over something means to keep thinking about it again and again, even when you want to think about something else.",
        ),
        QAItem(
            question="What is a bowel?",
            answer="A bowel is part of the body inside the belly that helps move food through the body. People may also say belly or tummy when they are talking in a gentle way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story q&a ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
animal(hero).
helper(helper).

worry(rumble).
worry(nerves).
worry(ache).

comfort(slow_breath).
comfort(water).
comfort(rest).
comfort(warm_wrap).

helps(slow_breath, rumble).
helps(slow_breath, nerves).
helps(water, rumble).
helps(water, nerves).
helps(water, ache).
helps(rest, rumble).
helps(rest, nerves).
helps(rest, ache).
helps(warm_wrap, nerves).
helps(warm_wrap, ache).

compatible(W, C) :- worry(W), comfort(C), helps(C, W).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("animal", "hero"), asp.fact("helper", "helper")]
    for w in WORRIES:
        lines.append(asp.fact("worry", w))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c))
    for c in COMFORTS.values():
        for w in c.helps:
            lines.append(asp.fact("helps", c.id, w))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    clingo_pairs = sorted(set(asp.atoms(model, "compatible")))
    python_pairs = sorted((w, c) for w in WORRIES for c, comp in COMFORTS.items() if w in comp.helps)
    if clingo_pairs != python_pairs:
        print("MISMATCH between clingo and Python compatibility.")
        print("clingo:", clingo_pairs)
        print("python:", python_pairs)
        return 1

    for w_id in WORRIES:
        for c_id in COMFORTS:
            params = StoryParams(
                species="rabbit",
                place="burrow",
                worry=w_id,
                comfort=c_id,
                name="Pip",
            )
            try:
                sample = generate(params) if c_id in COMFORTS and w_id in WORRIES and w_id in COMFORTS[c_id].helps else None
            except StoryError:
                if c_id in COMFORTS and w_id in COMFORTS[c_id].helps:
                    print("Unexpected StoryError for valid combo", w_id, c_id)
                    return 1
                continue
            if sample is not None and sample.story == "":
                print("Generated empty story for valid combo")
                return 1

    print(f"OK: ASP matches Python on {len(python_pairs)} compatible worry/comfort pairs.")
    return 0


# ---------------------------------------------------------------------------
# Parameters, generation, CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with inner monologue and a bowel worry.")
    ap.add_argument("--species", choices=sorted(ANIMALS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--worry", choices=sorted(WORRIES))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for worry_id in WORRIES:
            for comfort_id, comfort in COMFORTS.items():
                if worry_id in comfort.helps:
                    out.append((place, worry_id, comfort_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.worry is None or c[1] == args.worry)
        and (args.comfort is None or c[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, worry, comfort = rng.choice(sorted(combos))
    species = args.species or rng.choice(sorted(ANIMALS))
    name = args.name or rng.choice(["Pip", "Milo", "Nibbles", "Toby", "Mina", "Pebble"])
    return StoryParams(species=species, place=place, worry=worry, comfort=comfort, name=name)


def generate(params: StoryParams) -> StorySample:
    if params.worry not in WORRIES:
        raise StoryError("Unknown worry.")
    if params.comfort not in COMFORTS:
        raise StoryError("Unknown comfort.")
    if params.worry not in COMFORTS[params.comfort].helps:
        raise StoryError("That comfort does not fit this worry.")

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
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"place={world.place.label}")
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


def curated_samples() -> list[StoryParams]:
    return [
        StoryParams(species=s, place=p, worry=w, comfort=c, name=n)
        for (s, (p, w, c), n) in zip(
            ["rabbit", "squirrel", "badger"],
            CURATED,
            ["Pip", "Luna", "Bruno"],
        )
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        pairs = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(pairs)} compatible worry/comfort pairs:\n")
        for w, c in pairs:
            print(f"  {w:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = curated_samples()
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.species} in {p.place} with {p.worry}/{p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
