#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/miserable_evil_grate_gerund_mystery_to_solve.py
================================================================================================

A tiny fairy-tale storyworld about a miserable hero, an evil problem, and a
mystery to solve around a grate. The domain supports rhyme, a transformation,
and a child-friendly resolution.

The source tale imagined for this world:
---
In a little kingdom by a silver stream, a miserable mouse named Miri lived near
an old iron grate. Each night the evil grate groaned and hummed. Every morning,
the town's pear keeps vanished from the market basket, and no one knew why.

One day, Miri found a tiny clue: a pale feather caught on the grate. She
followed the clue to a damp tunnel, where a lonely crow had been hiding shiny
things because it missed having a friend. Miri spoke kindly, the crow softened,
and the evil grate was not evil at all: it only rang when the tunnel wind passed
through it.

Miri and the crow became friends, the pears were returned, and Miri's miserable
heart turned bright.

The domain turns on:
- a mystery to solve: what is taking the pears?
- rhyme: the story includes a little rhyme or chant
- transformation: misery turns to joy, and suspicion turns to friendship

This file is self-contained and follows the storyworld contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "princess", "mother", "mouse"}
        male = {"boy", "man", "king", "prince", "father", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str


@dataclass
class Mystery:
    id: str
    clue: str
    truth: str
    culprit: str
    solved_by_kindness: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "streamside": Place(id="streamside", label="the streamside village", mood="silver and soft"),
    "market": Place(id="market", label="the market square", mood="bright and busy"),
    "tower": Place(id="tower", label="the old watchtower", mood="high and windy"),
}

HEROES = {
    "miri": dict(type="mouse", label="Miri", phrase="a small mouse with brave eyes"),
    "lina": dict(type="girl", label="Lina", phrase="a little girl with a red ribbon"),
    "pax": dict(type="boy", label="Pax", phrase="a small boy with dusty boots"),
}

COMPANIONS = {
    "crow": dict(type="crow", label="Corvin", phrase="a lonely crow with glossy wings"),
    "cat": dict(type="cat", label="Tibby", phrase="a sleepy cat with a soft tail"),
    "dog": dict(type="dog", label="Bram", phrase="a friendly dog with a wagging tail"),
}

MYSTERIES = {
    "pears": Mystery(
        id="pears",
        clue="a pale feather caught on the grate",
        truth="a lonely crow had been taking the pears to a nest and hiding them there",
        culprit="crow",
    ),
    "bells": Mystery(
        id="bells",
        clue="a loop of blue string on the iron grate",
        truth="the wind made the grate sing, and the missing bells were tangled in ivy nearby",
        culprit="wind",
    ),
    "keys": Mystery(
        id="keys",
        clue="muddy paw prints beside the grate",
        truth="a worried dog carried the keys to keep them safe from a storm",
        culprit="dog",
    ),
}

RHYMES = {
    "pears": "Peep and peep, the pears are near; clue by clue, the path grows clear.",
    "bells": "Ring and sing, the night grows bright; a kind eye finds the hidden light.",
    "keys": "Tick and tack, the keys come home; no need to fear the dark or roam.",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Mystery is solved when the clue points to the truth and kindness is chosen.
solved(M) :- mystery(M), clue_shows(M), kindness_chosen(M).

% A transformation happens when misery becomes joy.
transformed(H) :- hero(H), misery(H), solved(_), joy(H).

% The grate may sound evil, but if wind passes through it, it is only noisy.
not_evil(G) :- grate(G), wind_through(G).

#show solved/1.
#show transformed/1.
#show not_evil/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
    for cid, c in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_shows", mid))
        lines.append(asp.fact("kindness_chosen", mid))
    lines.append(asp.fact("grate", "iron_grate"))
    lines.append(asp.fact("wind_through", "iron_grate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1.\n#show transformed/1.\n#show not_evil/1."))
    atoms = set((s.name, tuple(a.number if a.type.name == "Number" else a.string if a.type.name == "String" else a.name for a in s.arguments)) for s in model)
    expected = {("solved", ("pears",)), ("transformed", ("miri",)), ("not_evil", ("iron_grate",))}
    if atoms == expected:
        print("OK: ASP twin matches Python story model.")
        return 0
    print("MISMATCH:")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.hero and args.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if args.companion and args.companion not in COMPANIONS:
        raise StoryError("Unknown companion.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(list(HEROES))
    companion = args.companion or rng.choice(list(COMPANIONS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    return StoryParams(place=place, hero=hero, companion=companion, mystery=mystery)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero_cfg = HEROES[params.hero]
    comp_cfg = COMPANIONS[params.companion]
    mystery = MYSTERIES[params.mystery]

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        phrase=hero_cfg["phrase"],
        meters={"joy": 0.0},
        memes={"miserable": 1.0, "curiosity": 1.0, "joy": 0.0},
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type=comp_cfg["type"],
        label=comp_cfg["label"],
        phrase=comp_cfg["phrase"],
        meters={"nest": 0.0},
        memes={"lonely": 1.0, "softness": 1.0},
    ))
    grate = world.add(Entity(
        id="iron_grate",
        kind="thing",
        type="grate",
        label="iron grate",
        phrase="an old iron grate that hummed in the night",
        location=params.place,
        meters={"noise": 1.0},
        memes={"evil": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="feather clue",
        phrase=mystery.clue,
        location=params.place,
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type="fruit",
        label="pear basket",
        phrase="a basket of pears",
        owner=params.place,
        location=params.place,
        plural=True,
    ))

    world.facts.update(hero=hero, companion=companion, grate=grate, clue=clue, prize=prize, mystery=mystery)
    return world


def rhyme_line(mystery: Mystery) -> str:
    return RHYMES[mystery.id]


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    grate: Entity = world.facts["grate"]
    prize: Entity = world.facts["prize"]
    mystery: Mystery = world.facts["mystery"]

    world.say(
        f"In {world.place.label}, {hero.phrase} lived beside {grate.label}, "
        f"and {hero.pronoun('subject')} felt miserable because the village baskets kept coming up empty."
    )
    world.say(
        f"Each night, the {grate.label} made an evil little sound, and each dawn the {prize.label} was gone."
    )
    world.say(
        f"{hero.label} whispered, '{rhyme_line(mystery)}' and listened for a clue."
    )
    world.para()
    world.say(
        f"At last, {hero.label} found {mystery.clue}. {hero.pronoun('subject').capitalize()} followed it to a damp tunnel, "
        f"where {companion.phrase} was hiding the pears."
    )
    world.say(
        f"{companion.label} had not meant to be cruel; {companion.pronoun('subject')} was only lonely and wanted shiny things for a nest."
    )
    world.para()
    world.say(
        f"{hero.label} did not shout. {hero.pronoun('subject').capitalize()} spoke kindly, shared a pear, and asked {companion.pronoun('object')} to come back to the market."
    )
    world.say(
        f"Then the wind passed through the grate, and everyone learned the truth: the evil grate was only a noisy grate, not an evil one."
    )
    world.say(
        f"The crow returned the pears, and the miserable heart of {hero.label} became bright and warm."
    )
    world.say(
        f"By the end, {hero.label} and {companion.label} walked home together, and the village sang the rhyme again: '{rhyme_line(mystery)}'"
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a fairy tale about {hero.label}, a miserable hero, who solves a mystery near a grate.",
        f"Tell a rhyming story where {mystery.clue} leads to a transformation from sorrow to joy.",
        f"Write a child-friendly mystery to solve with a noisy grate, a hidden truth, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"Why was {hero.label} miserable at the start?",
            answer=f"{hero.label} was miserable because the village kept losing the pears, and the evil-sounding grate made the mystery feel scary.",
        ),
        QAItem(
            question=f"What clue helped {hero.label} solve the mystery?",
            answer=f"The clue was {mystery.clue}. It led {hero.label} to the damp tunnel where the truth was waiting.",
        ),
        QAItem(
            question=f"Who was really taking the pears?",
            answer=f"{companion.label} was taking the pears, but only because {companion.pronoun('subject')} was lonely and hiding them in a nest.",
        ),
        QAItem(
            question=f"How did {hero.label} change by the end?",
            answer=f"{hero.label} changed from miserable to bright and warm, because kindness turned the mystery into a friendship.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzle with missing facts. Someone must notice clues, ask careful questions, and learn the truth.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little pattern of sounds at the ends of words, like 'near' and 'clear' or 'bright' and 'light'.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state to another, like fear changing into courage or sadness changing into joy.",
        ),
        QAItem(
            question=f"What did the clue in this story help reveal?",
            answer=f"The clue helped reveal that {mystery.truth}.",
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
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale mystery storyworld with rhyme and transformation.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--hero", choices=list(HEROES))
    ap.add_argument("--companion", choices=list(COMPANIONS))
    ap.add_argument("--mystery", choices=list(MYSTERIES))
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


CURATED = [
    StoryParams(place="streamside", hero="miri", companion="crow", mystery="pears"),
    StoryParams(place="market", hero="lina", companion="dog", mystery="keys"),
    StoryParams(place="tower", hero="pax", companion="cat", mystery="bells"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1.\n#show transformed/1.\n#show not_evil/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        rng = random.Random(base_seed)
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
