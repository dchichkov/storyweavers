#!/usr/bin/env python3
"""
Storyworld: salute_transformation_problem_solving_kindness_ghost_story

A small child-facing ghost story about a salute, a spooky misunderstanding, a
kind act, and a transformation that turns fear into friendship.
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
    kind: str = "thing"  # "character" | "ghost" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed: bool = False
    visible: bool = True

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the old hall"
    weather: str = "foggy"
    echoing: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hall": Setting(place="the old hall", weather="foggy", echoing=True),
    "library": Setting(place="the moonlit library", weather="quiet", echoing=False),
    "garden": Setting(place="the misty garden", weather="foggy", echoing=True),
}

HERO_TYPES = ["girl", "boy"]
HERO_NAMES_GIRL = ["Mina", "Lina", "Tessa", "Nora", "Ivy"]
HERO_NAMES_BOY = ["Eli", "Pip", "Rory", "Theo", "Finn"]
GHOST_NAMES = ["Murmur", "Pale Jack", "Mossy Nell", "Whisper", "Boo"]
TRAITS = ["brave", "curious", "gentle", "careful", "kind"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def salute_phrase(hero: Entity, ghost: Entity) -> str:
    return f'{hero.id} gave a small salute to {ghost.id}, trying to be polite'


def transformation_phrase(ghost: Entity) -> str:
    if ghost.transformed:
        return f"{ghost.id} no longer looked frightening; the soft light had changed {ghost.pronoun('object')} into a friendly guide"
    return f"{ghost.id} still looked like a spooky shadow"


def predict_spookiness(world: World, hero: Entity, ghost: Entity) -> bool:
    sim = world.copy()
    simulate_encounter(sim, hero.id, ghost.id, narrate=False)
    return sim.get(ghost.id).memes.get("fear", 0.0) >= THRESHOLD


def simulate_encounter(world: World, hero_id: str, ghost_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    ghost = world.get(ghost_id)

    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    ghost.memes["fear"] = ghost.memes.get("fear", 0.0) + 1

    if narrate:
        world.say(
            f"In {world.setting.place}, the air felt chilly and the shadows made little swirls."
        )
        world.say(f"{hero.id} noticed {ghost.id} near the wall and froze.")
        world.say(f"{hero.id} gave a small salute to {ghost.id}, trying to be polite.")

    if hero.memes.get("kindness", 0.0) >= THRESHOLD:
        ghost.memes["fear"] = max(0.0, ghost.memes["fear"] - 1)
        ghost.memes["hope"] = ghost.memes.get("hope", 0.0) + 1
        if narrate:
            world.say(
                f"Instead of running away, {hero.id} asked, 'Are you lost?' and offered a warm hand."
            )
    else:
        if narrate:
            world.say(f"The ghost drifted back, and the room stayed shivery.")

    if hero.memes.get("problem_solving", 0.0) >= THRESHOLD and not ghost.transformed:
        ghost.transformed = True
        ghost.kind = "friend"
        ghost.type = "ghost"
        ghost.label = "friend ghost"
        ghost.memes["calm"] = ghost.memes.get("calm", 0.0) + 1
        if narrate:
            world.say(
                f"{hero.id} noticed a lantern on the floor and held it up so the room could see clearly."
            )
            world.say(
                f"The light made {ghost.id} shimmer and change. The spooky shape became a gentle glow."
            )
            world.say(
                f"{ghost.id} smiled at once, because the problem had been solved and the dark corner was gone."
            )

    if ghost.transformed and narrate:
        world.say(
            f"At last, {ghost.id} bowed back, and the little salute turned into a hello."
        )


def build_story(world: World, hero: Entity, ghost: Entity) -> None:
    world.say(
        f"One quiet evening in {world.setting.place}, {hero.id} heard a tiny rustle near the stairs."
    )
    world.say(
        f"It was {ghost.id}, a pale little ghost with a trembling voice and a lantern that had gone dim."
    )
    world.say(
        f"{hero.id} wanted to be kind, even if the room felt spooky."
    )
    world.para()

    world.say(
        f"{hero.id} gave a small salute to {ghost.id}, trying to be brave."
    )
    world.say(
        f"The ghost blinked in surprise, because nobody had ever greeted {ghost.id} that way before."
    )

    hero.memes["kindness"] = 1.0
    hero.memes["problem_solving"] = 1.0
    simulate_encounter(world, hero.id, ghost.id, narrate=True)
    world.para()

    if ghost.transformed:
        world.say(
            f"In the end, the lantern glowed bright, the shadows shrank, and {ghost.id} was not scary anymore."
        )
        world.say(
            f"{hero.id} and {ghost.id} shared a tiny smile, and the salute became the start of a friendship."
        )
    else:
        world.say(
            f"The hall stayed dark for a moment, but {hero.id} kept calm and looked for another way to help."
        )
        world.say(
            f"With patience and kindness, the spooky night felt smaller by the minute."
        )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a young child that includes a salute in {f["place"]}.',
        f'Tell a spooky-but-kind story where {f["hero_name"]} meets {f["ghost_name"]} and solves a problem with a lantern.',
        f'Write a short story in which a salute, kindness, and a transformation turn a ghostly mistake into friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who gave the salute in {place}?",
            answer=f"{hero.id} gave the salute to {ghost.id} because {hero.id} wanted to be polite and brave.",
        ),
        QAItem(
            question=f"What made {ghost.id} stop seeming so spooky?",
            answer=f"{hero.id}'s kindness and problem solving helped. The lantern was lifted, the dark corner was solved, and {ghost.id} transformed into a friendly presence.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {ghost.id}?",
            answer=f"They ended as friendly companions. The salute turned into a hello, and the ghost was no longer frightening.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salute?",
            answer="A salute is a small respectful gesture, often done with the hand, to greet someone politely.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, care, or speak gently so someone else feels safe and welcomed.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different form or becomes noticeably different.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a smart way to fix a difficulty or make a tricky situation better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(X) :- hero_name(X).
ghost(G) :- ghost_name(G).
salute_event(X,G) :- hero(X), ghost(G), kindness(X), problem_solving(X).
transforms(G) :- ghost(G), salute_event(_,G), lantern_fixed(G).
friendly(G) :- ghost(G), transforms(G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("ghost_name", "ghost"))
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("problem_solving", "hero"))
    lines.append(asp.fact("lantern_fixed", "ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show friendly/1. #show transforms/1."))
    atoms = set((s.name, tuple(arg.string if arg.type == 3 else arg.number for arg in s.arguments)) for s in model)
    expected = {("friendly", ("ghost",)), ("transforms", ("ghost",))}
    if atoms == expected:
        print("OK: ASP twin matches Python story logic.")
        return 0
    print("MISMATCH between ASP and Python logic.")
    print("ASP:", atoms)
    print("Expected:", expected)
    return 1


# ---------------------------------------------------------------------------
# Generation / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with salute, kindness, and transformation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--ghost-name")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES_GIRL if hero_type == "girl" else HERO_NAMES_BOY)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["kind", "curious"]))
    ghost = world.add(Entity(id=params.ghost_name, kind="ghost", type="ghost", label="little ghost", visible=True))

    world.facts.update(
        place=params.place,
        hero=hero,
        ghost=ghost,
        hero_name=params.hero_name,
        ghost_name=params.ghost_name,
    )

    build_story(world, hero, ghost)

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
        print(asp_program("#show friendly/1. #show transforms/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show friendly/1. #show transforms/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="hall", hero_name="Mina", hero_type="girl", ghost_name="Whisper"),
            StoryParams(place="library", hero_name="Eli", hero_type="boy", ghost_name="Murmur"),
            StoryParams(place="garden", hero_name="Nora", hero_type="girl", ghost_name="Mossy Nell"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
