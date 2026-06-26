#!/usr/bin/env python3
"""
storyworlds/worlds/working_sound_effects_bravery_foreshadowing_animal_story.py
===============================================================================

A small animal-story world about a creature doing real work, hearing a few
sound effects, showing bravery, and paying off a bit of foreshadowing.

Premise used to build the world:
---
A little animal wants to help with a job that is bigger than it looks. Along
the way, small sounds hint that something is stuck, and the hero must be brave
enough to keep working until the job is done.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "mouse", "bird", "duck", "cat", "dog", "squirrel"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    path: str
    job: str
    sound: str
    stuck_thing: str
    hidden_hint: str
    weather: str = ""


@dataclass
class StoryParams:
    place: str
    hero_type: str
    hero_name: str
    helper_type: str
    helper_name: str
    job: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def copy(self) -> "World":
        other = World(self.place)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "barn": Place(
        name="the barn",
        path="the hay path",
        job="move hay bales",
        sound="thump-thump",
        stuck_thing="a wheelbarrow stuck in soft mud",
        hidden_hint="the mud made the path slick near the gate",
        weather="",
    ),
    "riverbank": Place(
        name="the riverbank",
        path="the stone path",
        job="pull in a little net",
        sound="splash-splash",
        stuck_thing="a tiny boat tugged sideways by reeds",
        hidden_hint="the reeds whispered before the tug became a pull",
        weather="",
    ),
    "orchard": Place(
        name="the orchard",
        path="the leaf path",
        job="carry apples in baskets",
        sound="rustle-rustle",
        stuck_thing="a basket snagged on a low branch",
        hidden_hint="one branch looked bent down, as if it had been waiting there",
        weather="",
    ),
    "hill": Place(
        name="the hill",
        path="the grass path",
        job="push a seed cart",
        sound="creak-creak",
        stuck_thing="a cart that would not roll up the slope",
        hidden_hint="the slope looked steeper near the top",
        weather="",
    ),
}

HERO_TYPES = ["rabbit", "fox", "mouse", "squirrel", "duck"]
HELPER_TYPES = ["mouse", "bird", "rabbit", "fox", "duck"]
NAMES = ["Milo", "Ruby", "Toby", "Pip", "Hazel", "Poppy", "Otis", "Nina", "Bram", "Luna"]
TRAITS = ["small", "curious", "gentle", "bright", "quick", "kind"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def opening_line(hero: Entity, place: Place, job: str) -> str:
    return f"{hero.id} was a little {hero.type} who loved to help at {place.name} and do the {job}."


def sound_effect_line(place: Place) -> str:
    return {
        "thump-thump": "Thump-thump went the heavy work.",
        "splash-splash": "Splash-splash went the water by the bank.",
        "rustle-rustle": "Rustle-rustle went the leaves overhead.",
        "creak-creak": "Creak-creak went the tired little wheels.",
    }[place.sound]


def foreshadow_line(place: Place) -> str:
    return f"Something about {place.hidden_hint} made the air feel a little serious."


def bravery_line(hero: Entity) -> str:
    return f"{hero.id} took a brave breath and kept going even when the job looked hard."


def resolution_line(hero: Entity, helper: Entity, place: Place, job: str) -> str:
    return (
        f"Together, {hero.id} and {helper.id} finished the {job} at {place.name}, "
        f"and the hard thing finally moved."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(place: Place, hero_type: str, hero_name: str, helper_type: str, helper_name: str, job: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"work": 0.0}, memes={"bravery": 0.0, "hope": 0.0}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, meters={"work": 0.0}, memes={"bravery": 0.0, "hope": 0.0}))
    obstacle = world.add(Entity(id="Obstacle", kind="thing", type="thing", label=place.stuck_thing))

    world.say(opening_line(hero, place, job))
    world.say(f"{hero.id} knew the path to {job} well, and {helper.id} came along to lend a paw.")
    world.say(sound_effect_line(place))
    world.say(foreshadow_line(place))

    world.para()
    world.say(f"When they reached {place.name}, they found {obstacle.label}.")
    world.say(f"{hero.id} frowned, because the job could not be done while that was in the way.")
    world.say(f"{helper.id} hesitated, but {hero.id} stepped closer anyway.")
    world.say(bravery_line(hero))
    world.say(f"{hero.id} pushed, pulled, and worked and worked while {helper.id} held the other side.")

    hero.meters["work"] += 1
    helper.meters["work"] += 1
    hero.memes["bravery"] += 1
    helper.memes["hope"] += 1
    world.facts["obstacle_seen"] = True
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["job"] = job

    world.para()
    world.say(f"At last, with a loud {place.sound}, the obstacle moved.")
    world.say(resolution_line(hero, helper, place, job))
    world.say(f"{hero.id} smiled, because being brave had helped the whole job get finished.")
    return world


# ---------------------------------------------------------------------------
# Parameter registries and resolution
# ---------------------------------------------------------------------------
def choose_names(rng: random.Random, hero_type: str, helper_type: str) -> tuple[str, str]:
    hero_name = rng.choice(NAMES)
    helper_name = rng.choice([n for n in NAMES if n != hero_name])
    return hero_name, helper_name


def valid_pairs() -> list[tuple[str, str]]:
    return [(place_id, PLACES[place_id].job) for place_id in PLACES]


@dataclass
class Selection:
    place: str
    hero_type: str
    hero_name: str
    helper_type: str
    helper_name: str
    job: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with working, sound effects, bravery, and foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--job")
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
    place_id = args.place or rng.choice(list(PLACES))
    place = PLACES[place_id]
    job = args.job or place.job
    if args.job and args.job != place.job:
        raise StoryError("This place does not support that job in this world.")
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    hero_name = args.hero_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != hero_name])
    if hero_name == helper_name:
        raise StoryError("The hero and helper need different names.")
    return StoryParams(
        place=place_id,
        hero_type=hero_type,
        hero_name=hero_name,
        helper_type=helper_type,
        helper_name=helper_name,
        job=job,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        params.hero_type,
        params.hero_name,
        params.helper_type,
        params.helper_name,
        params.job,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = world.place
    return [
        f'Write a short animal story for a young child about "{hero.id}" working at {place.name}.',
        f"Tell a gentle story where {hero.id} hears a sound like {place.sound} and finds a hard job to finish with {helper.id}.",
        f"Write a small bravery story that includes a sound effect, a hint that something is wrong, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = world.place
    job = f["job"]
    return [
        QAItem(
            question=f"What kind of animal is {hero.id}?",
            answer=f"{hero.id} is a little {hero.type} who likes to help and work hard.",
        ),
        QAItem(
            question=f"What job were {hero.id} and {helper.id} trying to do at {place.name}?",
            answer=f"They were trying to {job}.",
        ),
        QAItem(
            question=f"What sound effect did the story mention at {place.name}?",
            answer=f"The story said, '{place.sound.replace('-', ' ').capitalize()}.'",
        ),
        QAItem(
            question=f"Why did {hero.id} need to be brave?",
            answer=f"{hero.id} needed to be brave because the job was blocked by {place.stuck_thing}, and it looked hard to move.",
        ),
        QAItem(
            question=f"What happened after {hero.id} kept working?",
            answer=f"{hero.id} kept working with {helper.id} until the obstacle moved and the job was finished.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does working mean?",
            answer="Working means doing a task or job and using effort to help something get finished.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word or phrase that helps you imagine a noise, like thump-thump or splash-splash.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous or the task looks hard.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little hint early in a story that tells you something important may happen later.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind == "character":
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
        else:
            if e.label:
                bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
place(P) :- place_name(P).
job(J) :- job_name(J).

compat(P, J) :- place_job(P, J).
story(P, H, K, J) :- place_job(P, J), hero_kind(H), helper_kind(K).

#show story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        lines.append(asp.fact("place_job", pid, place.job))
    for t in HERO_TYPES:
        lines.append(asp.fact("hero_kind", t))
    for t in HELPER_TYPES:
        lines.append(asp.fact("helper_kind", t))
    for n in NAMES:
        lines.append(asp.fact("hero_name", n))
        lines.append(asp.fact("helper_name", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show story/4.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "story"))
    py_set = set((p, h, k, j) for p, j in valid_pairs() for h in HERO_TYPES for k in HELPER_TYPES)
    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} stories).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="barn", hero_type="rabbit", hero_name="Milo", helper_type="mouse", helper_name="Pip", job=PLACES["barn"].job),
    StoryParams(place="riverbank", hero_type="fox", hero_name="Ruby", helper_type="bird", helper_name="Luna", job=PLACES["riverbank"].job),
    StoryParams(place="orchard", hero_type="squirrel", hero_name="Hazel", helper_type="rabbit", helper_name="Otis", job=PLACES["orchard"].job),
    StoryParams(place="hill", hero_type="duck", hero_name="Nina", helper_type="fox", helper_name="Bram", job=PLACES["hill"].job),
]


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: the chosen options do not make a simple, child-friendly animal-work story.)"


def build_story_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
        return samples
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        seed = base_seed + i
        i += 1
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError as err:
            print(err)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story/4."))
        combos = sorted(set(asp.atoms(model, "story")))
        print(f"{len(combos)} compatible story patterns:")
        for item in combos:
            print(" ", item)
        return

    samples = build_story_samples(args)
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
            header = f"### {p.hero_name} at {p.place} ({p.job})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
