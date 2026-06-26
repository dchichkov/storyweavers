#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teepee_sophomore_comedy_bad_ending_misunderstanding_curiosity.py
==============================================================================================================

A small animal-story world with a teepee, a sophomore, comedy, curiosity, and
a deliberately bad ending that comes from a misunderstanding.

The world is built around a simple premise:
an inquisitive sophomore raccoon wants to peek into a teepee before a comedy
show. The peek changes what the animals think they are seeing, which leads to
a muddled joke, a hurt feeling, and an ending that is a little sad rather than
tidy and triumphant.

The narration is driven by simulated state:
- curiosity rises when the hero notices something new
- misunderstanding rises when a message is seen out of context
- comedy can brighten the moment, but only if the audience understands it
- a bad ending happens when the misunderstanding is not repaired in time

This file is self-contained and uses only the stdlib plus the shared results
container; ASP helpers are imported lazily when needed.
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

CURIOUS_THRESHOLD = 1.0
MISUNDERSTANDING_THRESHOLD = 1.0
COMEDY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "animal"
    species: str = "animal"
    label: str = ""
    name: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"raccoon", "fox", "wolf", "bear", "goat", "cat", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.species in {"rabbit", "owl", "deer", "mouse", "hedgehog"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Teepee:
    id: str = "teepee"
    label: str = "the teepee"
    decorated: bool = False
    inside: str = "quiet shadows"
    top_open: bool = True
    owner: str = "camp"


@dataclass
class StoryParams:
    hero_name: str
    hero_species: str
    observer_name: str
    observer_species: str
    seed: Optional[int] = None


@dataclass
class World:
    teepee: Teepee = field(default_factory=Teepee)
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(teepee=copy.deepcopy(self.teepee))
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def species_article(species: str) -> str:
    return {"raccoon": "a", "fox": "a", "wolf": "a", "bear": "a", "goat": "a",
            "cat": "a", "dog": "a", "rabbit": "a", "owl": "an", "deer": "a",
            "mouse": "a", "hedgehog": "a"}.get(species, "a")


def species_title(species: str) -> str:
    return species


def curious_event(world: World, hero: Entity) -> None:
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.name}, a sophomore {hero.species}, noticed the teepee flap wobbling "
        f"and leaned closer just to see what was inside."
    )


def setup(world: World, hero: Entity, observer: Entity) -> None:
    world.say(
        f"At the edge of the school field stood a small teepee with painted poles and "
        f"soft blankets inside."
    )
    world.say(
        f"{hero.name} loved jokes, and {hero.pronoun('subject')} was proud to be a "
        f"sophomore who could make younger animals giggle."
    )
    world.say(
        f"{observer.name} was the kind of animal who watched first and asked questions later."
    )


def trigger_misunderstanding(world: World, hero: Entity, observer: Entity) -> None:
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0.0) + 1
    observer.memes["unease"] = observer.memes.get("unease", 0.0) + 1
    observer.memes["misunderstanding"] = observer.memes.get("misunderstanding", 0.0) + 1
    world.say(
        f"{hero.name} peeked through the flap and saw a funny mask, but "
        f"{observer.name} only saw a shadow bobbing in the doorway."
    )
    world.say(
        f"{observer.name} thought the teepee was being teased, not prepared for a show."
    )


def attempt_comedy(world: World, hero: Entity, observer: Entity) -> None:
    hero.memes["comedy"] = hero.memes.get("comedy", 0.0) + 1
    if observer.memes.get("misunderstanding", 0.0) >= MISUNDERSTANDING_THRESHOLD:
        observer.memes["hurt"] = observer.memes.get("hurt", 0.0) + 1
        world.say(
            f"{hero.name} tried to crack a comedy joke, but it landed like a pebble in mud "
            f"because nobody had the same idea about what was funny."
        )
    else:
        world.say(
            f"{hero.name} told a tiny comedy joke, and the teepee wobbled with quiet laughter."
        )


def bad_ending(world: World, hero: Entity, observer: Entity) -> None:
    if observer.memes.get("hurt", 0.0) >= 1.0:
        world.say(
            f"When {hero.name} finally stepped back, the mask had fallen into the dust and "
            f"{observer.name} had already walked away."
        )
        world.say(
            f"The comedy show never really began, and the teepee stayed still and lonely in the fading light."
        )
    else:
        world.say(
            f"Even so, the joke went flat, and the evening ended with a small, awkward silence."
        )


def tell_story(world: World, hero: Entity, observer: Entity) -> None:
    setup(world, hero, observer)
    world.para()
    curious_event(world, hero)
    trigger_misunderstanding(world, hero, observer)
    world.para()
    attempt_comedy(world, hero, observer)
    bad_ending(world, hero, observer)

    world.facts.update(
        hero=hero,
        observer=observer,
        teepee=world.teepee,
    )


def build_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(
        id=params.hero_name,
        species=params.hero_species,
        role="sophomore",
        name=params.hero_name,
        meters={"curiosity": 0.0},
        memes={"comedy": 0.0},
    ))
    observer = w.add(Entity(
        id=params.observer_name,
        species=params.observer_species,
        role="listener",
        name=params.observer_name,
        meters={},
        memes={"misunderstanding": 0.0, "unease": 0.0, "hurt": 0.0},
    ))
    tell_story(w, hero, observer)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    observer = f["observer"]
    return [
        "Write a short animal story with a teepee, a sophomore, comedy, and a misunderstanding.",
        f"Tell a gentle story about {hero.name}, a sophomore {hero.species}, who gets curious about a teepee and causes confusion.",
        f"Write a simple story where {observer.name} misreads a joke near a teepee and the ending is sad rather than happy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    observer = f["observer"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.name}, a sophomore {hero.species} who gets too curious near the teepee.",
        ),
        QAItem(
            question=f"What did {hero.name} look at too closely?",
            answer=f"{hero.name} looked too closely at the teepee flap and the funny mask inside it.",
        ),
        QAItem(
            question=f"Why did {observer.name} feel upset?",
            answer=f"{observer.name} felt upset because the peek into the teepee looked like teasing instead of a joke being prepared.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly, with the joke falling flat and the animals separating in an awkward silence.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a teepee?",
            answer="A teepee is a small cone-shaped shelter or tent, often made with poles and a covering.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, learn, or ask questions about something new.",
        ),
        QAItem(
            question="What is comedy?",
            answer="Comedy is making people laugh with jokes, silly actions, or funny ideas.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]]
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"teepee.decorated={world.teepee.decorated}")
    lines.append(f"teepee.top_open={world.teepee.top_open}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: species={e.species} meters={meters} memes={memes}")
    return "\n".join(lines)


GIRL_NAMES = ["Mina", "Luna", "Nora", "Pippa", "Wren"]
BOY_NAMES = ["Milo", "Otis", "Finn", "Jasper", "Toby"]
SPECIES = ["raccoon", "fox", "rabbit", "owl", "cat", "dog"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = args.hero_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    hero_species = args.hero_species or rng.choice(SPECIES)
    observer_name = args.observer_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    observer_species = args.observer_species or rng.choice([s for s in SPECIES if s != hero_species])
    if hero_name == observer_name:
        raise StoryError("hero and observer must be different animals")
    return StoryParams(
        hero_name=hero_name,
        hero_species=hero_species,
        observer_name=observer_name,
        observer_species=observer_species,
    )


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


ASP_RULES = r"""
#show curious/1.
#show misunderstanding/1.
#show bad_ending/1.

curious(H) :- curiosity(H), curiosity_level(H,N), N >= 1.
misunderstanding(O) :- misread(O), confusion(O), confusion_level(O,N), N >= 1.
bad_ending(W) :- curious(H), misunderstanding(O), clash(H,O), no_repair(W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("curiosity_level", "hero", 1))
    lines.append(asp.fact("confusion_level", "observer", 1))
    lines.append(asp.fact("clash", "hero", "observer"))
    lines.append(asp.fact("no_repair", "world"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show misunderstanding/1.\n#show bad_ending/1."))
    seen = {
        "curious": set(asp.atoms(model, "curious")),
        "misunderstanding": set(asp.atoms(model, "misunderstanding")),
        "bad_ending": set(asp.atoms(model, "bad_ending")),
    }
    ok = seen["curious"] == {("hero",)} and seen["misunderstanding"] == {("observer",)} and seen["bad_ending"] == {("world",)}
    if ok:
        print("OK: ASP twin matches the intended bad-ending misunderstanding pattern.")
        return 0
    print("MISMATCH in ASP verification:", seen)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world with a teepee, a sophomore, comedy, curiosity, and a bad ending."
    )
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-species", choices=SPECIES)
    ap.add_argument("--observer-name")
    ap.add_argument("--observer-species", choices=SPECIES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious/1.\n#show misunderstanding/1.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        curated = [
            StoryParams("Milo", "raccoon", "Wren", "owl"),
            StoryParams("Nora", "rabbit", "Otis", "fox"),
            StoryParams("Jasper", "cat", "Luna", "dog"),
        ]
        samples = [generate(p) for p in curated]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
