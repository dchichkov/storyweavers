#!/usr/bin/env python3
"""
A tiny storyworld for a rhyming tale with a flashback, bravery, and a bad ending.

Premise:
- A small hero remembers a past fear when a ferocious creature appears.
- The hero tries to be brave, but the world model can still end in failure.
- The prose is driven by simulated state, not by a frozen paragraph swap.

This world intentionally supports a sad/bad ending: bravery may be real, but it
is not always enough.
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

# Story tone knobs
RHYMING_END = "The night grew long, and the hero's song went wrong."
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    dark: bool = False
    echoes: bool = False
    can_flashback: bool = True


@dataclass
class Threat:
    name: str
    phrase: str
    ferocity: float
    noise: str
    danger: float
    flashback_trigger: str


@dataclass
class StoryParams:
    place: str
    threat: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "wood": Place(name="the wood", dark=True, echoes=True),
    "hill": Place(name="the hill", dark=False, echoes=True),
    "yard": Place(name="the yard", dark=False, echoes=False),
}

THREATS = {
    "wolf": Threat(
        name="wolf",
        phrase="a ferocious wolf",
        ferocity=2.0,
        noise="howl",
        danger=2.0,
        flashback_trigger="an old trail and a torn red coat",
    ),
    "storm": Threat(
        name="storm",
        phrase="a ferocious storm",
        ferocity=1.7,
        noise="roar",
        danger=1.8,
        flashback_trigger="the last time lightning cracked the sky",
    ),
    "dog": Threat(
        name="dog",
        phrase="a ferocious dog",
        ferocity=1.5,
        noise="bark",
        danger=1.2,
        flashback_trigger="a snap of teeth by the gate",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Noah", "Pip", "Ivy", "Owen", "Jade"]
TRAITS = ["small", "bold", "curious", "nervous", "gentle", "spry"]


class World:
    def __init__(self, place: Place, threat: Threat):
        self.place = place
        self.threat = threat
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _m(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _v(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _mm(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} little {hero.type}, light on a toe and ready to grow.")


def setup_flashback(world: World, hero: Entity) -> None:
    _mm(hero, "memory", 1.0)
    world.say(
        f"{hero.pronoun().capitalize()} remembered {world.threat.flashback_trigger}, "
        f"and the old fear began to show."
    )
    world.para()


def threat_arrives(world: World, hero: Entity) -> None:
    _v(hero, "startle", 1.0)
    _mm(hero, "fear", 1.0)
    world.say(
        f"In {world.place.name}, there came {world.threat.phrase}, with a {world.threat.noise} that was low."
    )
    world.say(
        f"The air felt tight and cold, and {hero.id}'s brave heart slowed to a wobble below."
    )


def bravery_attempt(world: World, hero: Entity) -> None:
    _mm(hero, "bravery", 1.0)
    world.say(
        f"{hero.id} took one step, then two, and whispered, 'I can stand my ground and be strong.'"
    )
    world.say(
        f"{hero.pronoun().capitalize()} lifted {hero.pronoun('possessive')} chin to the tune of a shaky song."
    )


def fail_turn(world: World, hero: Entity) -> None:
    # The bad ending is real: the situation overwhelms the hero.
    _v(hero, "hurt", 1.0)
    _mm(hero, "fear", 1.0)
    world.say(
        f"But the {world.threat.name} came nearer and nearer, and bravery alone was not enough."
    )
    world.say(
        f"{hero.id} fell back in the grass, and the moment turned hard and rough."
    )


def bad_ending(world: World, hero: Entity) -> None:
    _mm(hero, "sad", 1.0)
    world.say(
        f"{hero.id} did not win that night, and the dark kept its solemn glow."
    )
    world.say(
        f"{RHYMING_END}"
    )


def tell(place: Place, threat: Threat, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(place, threat)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "brave"]))

    introduce(world, hero)
    setup_flashback(world, hero)
    threat_arrives(world, hero)
    bravery_attempt(world, hero)
    fail_turn(world, hero)
    world.para()
    bad_ending(world, hero)

    world.facts.update(
        hero=hero,
        place=place,
        threat=threat,
        bravery=float(hero.memes.get("bravery", 0.0)),
        fear=float(hero.memes.get("fear", 0.0)),
        ending="bad",
    )
    return world


def rhyme_prompt(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short rhyming story for a child about {hero.id}, a flashback, bravery, and a bad ending.',
        f'Write a gentle poem-story where {hero.id} remembers an old fear in {f["place"].name} and meets {f["threat"].phrase}.',
        f"Tell a rhyming story that includes a flashback, a brave try, and a sad ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    threat: Threat = f["threat"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Where did {hero.id} meet {threat.phrase}?",
            answer=f"{hero.id} met {threat.phrase} in {place.name}, where the air felt tight and still.",
        ),
        QAItem(
            question=f"What did {hero.id} remember before the scary part began?",
            answer=f"{hero.id} remembered {threat.flashback_trigger}, and that old memory made the fear grow.",
        ),
        QAItem(
            question=f"Was {hero.id} brave in the story?",
            answer=f"Yes, {hero.id} tried to be brave and stepped forward, even though the fear was too strong.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: {hero.id} did not win that night, and the last image was sad and dark.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story shows an old memory from before the present moment.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means trying to do something hard or scary even when you feel afraid.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the main problem is not solved and the story closes in a sad or unhappy way.",
        ),
        QAItem(
            question="What does ferocious mean?",
            answer="Ferocious means very fierce, wild, or scary.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld with flashback, bravery, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])  # accepted for contract symmetry
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    threat = args.threat or rng.choice(list(THREATS))
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.threat and args.threat not in THREATS:
        raise StoryError("Unknown threat.")
    hero_type = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, threat=threat, hero_name=name, hero_type=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], THREATS[params.threat], params.hero_name, params.hero_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=rhyme_prompt(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% Declarative twin for the reasonableness gate.
place(P) :- setting(P).
threat(T) :- danger(T,_).
brave_story(P,T) :- place(P), threat(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("danger", tid, int(t.danger * 10)))
        lines.append(asp.fact("ferocious", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show brave_story/2."))
    atoms = set(asp.atoms(model, "brave_story"))
    expected = {(p, t) for p in PLACES for t in THREATS}
    if atoms == expected:
        print(f"OK: clingo gate matches expected combinations ({len(atoms)} combos).")
        return 0
    print("MISMATCH between clingo and expected combinations.")
    print("only in clingo:", sorted(atoms - expected))
    print("only in python:", sorted(expected - atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as e:
            raise SystemExit(str(e))
        model = asp.one_model(asp_program("#show brave_story/2."))
        combos = sorted(set(asp.atoms(model, "brave_story")))
        print(f"{len(combos)} compatible combinations:")
        for p, t in combos:
            print(f"  {p} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("wood", "wolf", "Mina", "girl", "curious"),
            StoryParams("hill", "storm", "Toby", "boy", "bold"),
            StoryParams("yard", "dog", "Ivy", "girl", "nervous"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
        if args.all:
            p = sample.params
            print(f"### {p.hero_name}: {p.threat} in {p.place}")
        elif len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
