#!/usr/bin/env python3
"""
Standalone storyworld: shark enclave suspense repetition transformation mystery.

A child-facing mystery in a sheltered sea enclave where repeated clues build
suspense and a transformation reveals the hidden truth.
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

LOCATIONS = {
    "tidal_cove": "the tidal cove",
    "coral_gate": "the coral gate",
    "moon_pier": "the moonlit pier",
    "shell_enclave": "the shell enclave",
}

HEROES = [
    ("Mira", "girl"),
    ("Tobin", "boy"),
    ("Nia", "girl"),
    ("Perry", "boy"),
    ("Sora", "girl"),
]

HELPERS = [
    ("Aunt Nettle", "aunt"),
    ("Captain Reed", "captain"),
    ("Grandpa Moss", "grandpa"),
    ("Keeper Luna", "keeper"),
]

MYSTERY_SIGNS = [
    "a wet silver scale",
    "a trail of tiny bubbles",
    "a broken pearl loop",
    "a shadow under the dock",
    "a soft tapping sound in the reeds",
]

TRANSFORMATIONS = {
    "net": "a net of woven kelp",
    "shell": "a shell lamp",
    "cloak": "a cloak of bright seaweed",
    "lantern": "a lantern with a pearl glass",
}

SHARK_FORMS = {
    "small": "a small reef shark",
    "old": "an old friendly shark",
    "young": "a young sand shark",
}

SEED_WORDS = ["shark", "enclave"]


# ---------------------------------------------------------------------------
# Shared result helpers
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    shark_form: str
    transformation: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Entities / world model
# ---------------------------------------------------------------------------

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
        if self.type in {"girl", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandpa", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Reasonableness / mystery gate
# ---------------------------------------------------------------------------

def valid_combo(params: StoryParams) -> bool:
    return params.place in LOCATIONS and params.transformation in TRANSFORMATIONS


def explain_rejection() -> str:
    return "(No story: the enclave needs a valid place and a real transformation clue.)"


# ---------------------------------------------------------------------------
# Narrative utilities
# ---------------------------------------------------------------------------

def clue_sentence(sign: str, repetition: int) -> str:
    if repetition == 1:
        return f"Again and again, they noticed {sign}."
    if repetition == 2:
        return f"Once more, {sign} appeared near the water."
    return f"The same sign kept returning: {sign}."


def mystery_opening(hero: Entity, helper: Entity, place: str) -> str:
    return (
        f"{hero.id} lived near {place}, inside a quiet little enclave by the sea. "
        f"{hero.pronoun().capitalize()} and {helper.id} liked the hush there, because quiet places made secrets easier to hear."
    )


def reveal_text(shark_form: str, transformation: str, hero: Entity, helper: Entity) -> tuple[str, str]:
    shark_phrase = SHARK_FORMS[shark_form]
    transformed = TRANSFORMATIONS[transformation]
    first = (
        f"At last, the ripples opened, and the mystery was not a dangerous scare at all. "
        f"It was {shark_phrase}, wearing {transformed} like a costume."
    )
    second = (
        f"When {hero.id} looked closer, {hero.pronoun()} saw the creature was helping carry lost shells back to the enclave. "
        f"{helper.id} smiled, and the strange visitor swam away gently, leaving the water calm again."
    )
    return first, second


# ---------------------------------------------------------------------------
# Story generator
# ---------------------------------------------------------------------------

def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["curious", "careful"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, traits=["patient"]))
    shark_name = "Shimmer"
    shark = world.add(Entity(id=shark_name, kind="character", type="shark", traits=[params.shark_form, "quiet"]))

    world.facts.update(
        hero=hero,
        helper=helper,
        shark=shark,
        sign=random.choice(MYSTERY_SIGNS),
        transformation=params.transformation,
        place=params.place,
    )

    # Act 1: setup
    world.say(mystery_opening(hero, helper, params.place))
    world.say(
        f"One evening, {hero.id} found a clue: {world.facts['sign']}. "
        f"{hero.pronoun().capitalize()} did not say it was nothing, because mysteries grow when people rush past them."
    )

    # Act 2: suspense and repetition
    world.para()
    world.say(
        f"Then the same clue came back. {clue_sentence(world.facts['sign'], 1)} "
        f"{hero.id} and {helper.id} followed the wet track toward the water."
    )
    world.say(
        f"A little later, {clue_sentence('the sound of something brushing the rocks', 2)} "
        f"{hero.id} held still and listened. The enclave felt smaller, and the dark water felt larger."
    )
    world.say(
        f"{helper.id} whispered that they should watch carefully, not shout, and not frighten whatever was hiding below."
    )

    # Act 3: transformation reveal
    world.para()
    first, second = reveal_text(params.shark_form, params.transformation, hero, helper)
    world.say(first)
    world.say(second)
    world.say(
        f"That night, the enclave did not feel spooky anymore. It felt clever, because the clues had turned into an answer."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a child-friendly mystery story about a curious {hero.type} who lives in an enclave by the sea and notices a shark clue.',
        f'Tell a suspenseful story that repeats clues, then reveals that the shark was not a threat but a transformed helper.',
        f'Write a short story with the words "shark" and "enclave" where repeated signs lead to a surprising transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    sign = f["sign"]
    transformation = f["transformation"]
    shark: Entity = f["shark"]  # type: ignore[assignment]
    place = f["place"]

    return [
        QAItem(
            question=f"Where did {hero.id} live in the story?",
            answer=f"{hero.id} lived near {place}, inside a quiet little enclave by the sea.",
        ),
        QAItem(
            question=f"What clue kept showing up and making the story feel suspenseful?",
            answer=f"The clue was {sign}, and it appeared more than once so the mystery would feel suspenseful.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} think the strange shark story might mean at first?",
            answer=f"They thought something secret and possibly worrying was hiding in the water, because the repeated signs kept leading them toward the shore.",
        ),
        QAItem(
            question=f"What was the shark really like at the end?",
            answer=f"The shark was not a danger. It was {SHARK_FORMS[shark.type if shark.type in SHARK_FORMS else 'small']} wearing {TRANSFORMATIONS[transformation]}, and it was helping bring shells back.",
        ),
        QAItem(
            question=f"How did the mystery change by the end?",
            answer="The mystery changed from a spooky question into a calm answer, because the repeated clues finally made sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shark?",
            answer="A shark is a fish that lives in the sea. Some sharks are large, and some are small.",
        ),
        QAItem(
            question="What is an enclave?",
            answer="An enclave is a small place that is surrounded by something larger. In a story, it can feel like a tucked-away little home.",
        ),
        QAItem(
            question="Why does repetition matter in a mystery?",
            answer="Repetition matters because when the same clue appears again, it helps a reader notice that the clue is important.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or becomes different from what it was before.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(tidal_cove).
place(coral_gate).
place(moon_pier).
place(shell_enclave).

hero(mira; tobin; nia; perry; sora).
helper(aunt_nettle; captain_reed; grandpa_moss; keeper_luna).
shark_form(small; old; young).
transformation(net; shell; cloak; lantern).

valid(P, H, S, T) :- place(P), hero(H), shark_form(S), transformation(T).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in LOCATIONS:
        lines.append(asp.fact("place", key))
    for name, _ in HEROES:
        lines.append(asp.fact("hero", name.lower()))
    for name, _ in HELPERS:
        lines.append(asp.fact("helper", name.lower().replace(" ", "_")))
    for key in SHARK_FORMS:
        lines.append(asp.fact("shark_form", key))
    for key in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid/4.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set((p, h.lower(), s, t) for p in LOCATIONS for h, _ in HEROES for s in SHARK_FORMS for t in TRANSFORMATIONS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo-only:", sorted(clingo_set - python_set))
    print("python-only:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a shark in an enclave.")
    ap.add_argument("--place", choices=LOCATIONS.keys())
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
    place = args.place or rng.choice(list(LOCATIONS.keys()))
    hero_name, hero_type = rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)
    shark_form = rng.choice(list(SHARK_FORMS.keys()))
    transformation = rng.choice(list(TRANSFORMATIONS.keys()))
    params = StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        shark_form=shark_form,
        transformation=transformation,
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError(explain_rejection())
    return params


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params):
        raise StoryError(explain_rejection())
    world = World(params.place)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  place={world.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        atoms = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(atoms)} compatible combos:")
        for a in atoms:
            print(" ", a)
        return

    if args.all:
        seeds = [101, 202, 303, 404, 505]
        samples = []
        for i, s in enumerate(seeds):
            params = resolve_params(argparse.Namespace(place=None, seed=s), random.Random(s))
            samples.append(generate(params))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        for i in range(max(args.n, 1) * 50):
            if len(samples) >= max(args.n, 1):
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
