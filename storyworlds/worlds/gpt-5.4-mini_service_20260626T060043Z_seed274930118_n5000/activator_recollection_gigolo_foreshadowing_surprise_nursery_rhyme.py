#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/activator_recollection_gigolo_foreshadowing_surprise_nursery_rhyme.py
==============================================================================================

A tiny nursery-rhyme story world about a curious child, a noisy activator,
a half-remembered recollection, and a cheeky little gigolo puppet.

The premise is built from the seed words:
- activator
- recollection
- gigolo

Story instruments:
- Foreshadowing
- Surprise

Style:
- Nursery rhyme / child-facing, with a sing-song turn and a bright ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class NurseryPlace:
    place: str = "the nursery"
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryThing:
    id: str
    label: str
    phrase: str
    type: str
    cue: str
    reveals: str
    foreshadow: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    activator: str
    recollection: str
    gigolo: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: NurseryPlace) -> None:
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("foreshadow", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["unease"] = ent.memes.get("unease", 0.0) + 1.0
        out.append("A little hint hid in the air like a spoon behind a bowl.")
    return out


def _r_recollection(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("memory", 0.0) < THRESHOLD:
            continue
        sig = ("recollection", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["remembered"] = ent.memes.get("remembered", 0.0) + 1.0
        out.append("A recollection came back, soft as a feather on a spoon.")
    return out


CAUSAL_RULES = [
    Rule("foreshadow", "social", _r_foreshadow),
    Rule("recollection", "social", _r_recollection),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "nursery": NurseryPlace(place="the nursery", quiet=True, affords={"listen", "sing"}),
    "playroom": NurseryPlace(place="the playroom", quiet=True, affords={"listen", "sing"}),
}

ACTIVATORS = {
    "bellpull": StoryThing(
        id="bellpull",
        label="bell pull",
        phrase="a ribbon bell pull",
        type="activator",
        cue="pull the ribbon",
        reveals="rings a tiny bell",
        foreshadow="a ribbon loop hung down from the shelf",
        surprise="out popped a bright note",
        tags={"activator", "sound", "bell"},
    ),
    "musicboxkey": StoryThing(
        id="musicboxkey",
        label="music box key",
        phrase="a little winding key",
        type="activator",
        cue="turn the key",
        reveals="tuned the music box",
        foreshadow="a small keyhole shone under dust",
        surprise="the box began to hum",
        tags={"activator", "music", "key"},
    ),
}

RECOLLECTIONS = {
    "lullabycard": StoryThing(
        id="lullabycard",
        label="lullaby card",
        phrase="a card with a half-remembered lullaby",
        type="recollection",
        cue="read the card",
        reveals="brought back the tune",
        foreshadow="one line was written in pale blue ink",
        surprise="the missing line was tucked behind the picture",
        tags={"recollection", "memory", "song"},
    ),
    "teddymemory": StoryThing(
        id="teddymemory",
        label="teddy memory",
        phrase="a tiny teddy note about bedtime",
        type="recollection",
        cue="peek under the teddy",
        reveals="made the rhyme come back",
        foreshadow="the teddy sat with one paw lifted",
        surprise="a folded note was hiding in the paw",
        tags={"recollection", "memory", "teddy"},
    ),
}

GIGOLOS = {
    "gigolo": StoryThing(
        id="gigolo",
        label="Gigolo",
        phrase="Gigolo, a little puppet with a gold hat",
        type="gigolo",
        cue="dance and bow",
        reveals="waved the story open",
        foreshadow="a gold hat peeped from behind the curtain",
        surprise="Gigolo was already there, waiting to bow",
        tags={"gigolo", "puppet", "dance"},
    ),
    "gigolobird": StoryThing(
        id="gigolobird",
        label="Gigolo Bird",
        phrase="Gigolo Bird, a stuffed bird with bright shoes",
        type="gigolo",
        cue="hop on one foot",
        reveals="flipped the rhyme into place",
        foreshadow="bright shoes peeked from a basket",
        surprise="the bird hopped out with a twirl",
        tags={"gigolo", "bird", "dance"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Pia", "Zoe", "Maya"]
BOY_NAMES = ["Theo", "Pip", "Finn", "Noah", "Eli", "Max"]
TRAITS = ["curious", "gentle", "cheerful", "lively", "dreamy"]


def choose_combo(rng: random.Random) -> tuple[str, str, str, str]:
    return (
        rng.choice(list(SETTINGS)),
        rng.choice(list(ACTIVATORS)),
        rng.choice(list(RECOLLECTIONS)),
        rng.choice(list(GIGOLOS)),
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(place, a, r, g) for place in SETTINGS for a in ACTIVATORS for r in RECOLLECTIONS for g in GIGOLOS]


def explain_rejection() -> str:
    return "(No story: the requested combination is not available in this nursery world.)"


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    act = ACTIVATORS[params.activator]
    rec = RECOLLECTIONS[params.recollection]
    gig = GIGOLOS[params.gigolo]

    world.facts.update(hero=hero, parent=parent, activator=act, recollection=rec, gigolo=gig)

    hero.memes["curiosity"] = 1.0
    world.say(f"{hero.id} was a little {random.choice(TRAITS)} {hero.type} who liked the quiet room.")
    world.say(f"One day, {hero.id} saw {act.foreshadow}; it made {hero.pronoun('object')} wonder.")
    world.say(f"Near the pillow sat {rec.foreshadow}, and behind the curtain was {gig.foreshadow}.")

    world.para()
    world.say(f"{hero.id} wanted to {act.cue}, {rec.cue}, and let {gig.label} {gig.cue}.")
    hero.memes["memory"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"When {hero.id} did it, {act.reveals}.")
    world.say(f"Then {rec.reveals}, and {gig.reveals}.")
    world.say(f"All at once, {act.surprise}, {rec.surprise}, and {gig.surprise}.")

    world.para()
    hero.memes["joy"] = 1.0
    world.say(f"{hero.id} laughed a soft little laugh and sang, “Tra-la-la, what a happy day!”")
    world.say(f"The room grew bright and small and snug, with the song tucked safely in place.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about {f["hero"].id}, a {f["hero"].type}, '
        f'a {f["activator"].label}, a {f["recollection"].label}, and {f["gigolo"].label}.',
        f"Tell a sing-song story where a child notices a hint, remembers a tune, "
        f"and discovers {f['gigolo'].label} in a quiet room.",
        f'Write a gentle rhyme with foreshadowing and surprise that includes the words '
        f'"activator", "recollection", and "gigolo".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    act, rec, gig = f["activator"], f["recollection"], f["gigolo"]
    return [
        QAItem(
            question=f"What did {hero.id} notice first in the room?",
            answer=f"{hero.id} noticed {act.foreshadow} and felt curious right away.",
        ),
        QAItem(
            question=f"What did the recollection do in the story?",
            answer=f"The recollection came back and helped {hero.id} remember the tune again.",
        ),
        QAItem(
            question=f"Who was waiting with a bow at the end?",
            answer=f"{gig.label} was waiting with a bow, and that was the surprise.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when everything came together?",
            answer=f"{hero.id} felt happy and safe, and the parent was nearby in the quiet nursery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an activator in this story?",
            answer="An activator is a thing that makes something happen, like a pull, key, or switch.",
        ),
        QAItem(
            question="What is a recollection?",
            answer="A recollection is a memory that comes back to mind.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you say, 'Oh!'",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, sing-song poem or story for children.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts: place(P), activator(A), recollection(R), gigolo(G)
% A valid nursery story contains all three instruments together.
valid_story(P, A, R, G) :- place(P), activator(A), recollection(R), gigolo(G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVATORS:
        lines.append(asp.fact("activator", a))
    for r in RECOLLECTIONS:
        lines.append(asp.fact("recollection", r))
    for g in GIGOLOS:
        lines.append(asp.fact("gigolo", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with foreshadowing and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activator", choices=ACTIVATORS)
    ap.add_argument("--recollection", choices=RECOLLECTIONS)
    ap.add_argument("--gigolo", choices=GIGOLOS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, act, rec, gig = args.place, args.activator, args.recollection, args.gigolo
    if place and act and rec and gig:
        return StoryParams(
            place=place, hero_name=args.name or "Mina", hero_type=args.gender or "girl",
            parent_type=args.parent or "mother", activator=act, recollection=rec, gigolo=gig
        )
    place, act, rec, gig = choose_combo(rng)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, hero_name=name, hero_type=gender, parent_type=parent,
                       activator=act, recollection=rec, gigolo=gig)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for c in combos[:50]:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p, a, r, g in valid_combos():
            params = StoryParams(
                place=p,
                hero_name="Mina",
                hero_type="girl",
                parent_type="mother",
                activator=a,
                recollection=r,
                gigolo=g,
                seed=None,
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
