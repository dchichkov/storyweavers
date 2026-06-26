#!/usr/bin/env python3
"""
A small tall-tale storyworld about magic, a twist, and a deceased old trickster
whose finest secret still changes the day.
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
class Person:
    id: str
    type: str
    label: str
    trait: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    enchanted: bool = False


@dataclass
class Place:
    name: str
    feature: str
    weather: str
    magic_kind: str
    twist_kind: str


@dataclass
class StoryParams:
    place: str
    relic: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.people: dict[str, Person] = {}
        self.relics: dict[str, Relic] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_relic(self, r: Relic) -> Relic:
        self.relics[r.id] = r
        return r

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

        w = World(self.place)
        w.people = _copy.deepcopy(self.people)
        w.relics = _copy.deepcopy(self.relics)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "barn": Place("the red barn", "hay loft", "windy", "glow", "surprise"),
    "fair": Place("the county fair", "ferris wheel", "sunny", "spark", "mix-up"),
    "river": Place("the riverbank", "old bridge", "misty", "shine", "turn"),
    "canyon": Place("the canyon rim", "wide sky", "dry", "whirl", "echo"),
}

RELICS = {
    "lantern": {"label": "lantern", "phrase": "a brass lantern with a moonlit latch", "kind": "light"},
    "hat": {"label": "hat", "phrase": "a tall black hat with a secret lining", "kind": "cloth"},
    "fiddle": {"label": "fiddle", "phrase": "a fiddle that sang like a sparrow", "kind": "music"},
    "kite": {"label": "kite", "phrase": "a bright kite stitched with silver thread", "kind": "air"},
}

TRAITS = ["cheerful", "curious", "brave", "spry", "wonder-eyed", "bushy-tailed"]
GIRLS = ["Mina", "Ruby", "Ada", "Nell", "Lottie", "June"]
BOYS = ["Ollie", "Tom", "Benn", "Hank", "Milo", "Ezra"]
ELDERS = ["Grandpa Jeb", "Uncle Roan", "Old Mose", "Papa Finn"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add_person(Person(id=params.hero_name, type=params.hero_type, label=params.hero_name, trait=params.trait))
    elder = world.add_person(Person(id=params.elder_name, type=params.elder_type, label=params.elder_name, trait="deceased"))
    relic_cfg = RELICS[params.relic]
    relic = world.add_relic(
        Relic(
            id=params.relic,
            label=relic_cfg["label"],
            phrase=relic_cfg["phrase"],
            kind=relic_cfg["kind"],
            owner=elder.id,
            carried_by=hero.id,
            enchanted=True,
        )
    )

    hero.memes["wonder"] = 1.0
    hero.memes["loss"] = 1.0
    elder.meters["deceased"] = 1.0
    relic.memes["memory"] = 1.0

    world.facts.update(hero=hero, elder=elder, relic=relic, place=place)
    return world


def start_story(world: World) -> None:
    hero: Person = world.facts["hero"]  # type: ignore[assignment]
    elder: Person = world.facts["elder"]  # type: ignore[assignment]
    relic: Relic = world.facts["relic"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]

    world.say(
        f"At {place.name}, {hero.id} was a {hero.trait} little {hero.type} with wide eyes and quick feet."
    )
    world.say(
        f"{hero.id} had found {relic.phrase}, and everybody in town said it once belonged to {elder.id}, "
        f"the deceased old magician who could pull lightning out of a teacup and tuck it back before supper."
    )
    world.say(
        f"{hero.id} loved the relic because it glittered like a promise, and because {elder.id} had left it behind "
        f"with a wink that seemed to live longer than any church bell."
    )


def raise_tension(world: World) -> None:
    hero: Person = world.facts["hero"]  # type: ignore[assignment]
    elder: Person = world.facts["elder"]  # type: ignore[assignment]
    relic: Relic = world.facts["relic"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"One bright morning, {hero.id} carried the relic to {place.feature}, where the air was full of squeaks and swirls."
    )
    world.say(
        f"{hero.id} wanted to make one tiny trick happen, just to see if the old magic still had any hops left in it."
    )
    world.say(
        f"But the moment {hero.id} whispered the first word, the whole world gave a tall-tale twist: "
        f"the lantern dimmed, the hat brim shivered, and a silvery note floated up like it had been waiting all along."
    )


def resolve_story(world: World) -> None:
    hero: Person = world.facts["hero"]  # type: ignore[assignment]
    elder: Person = world.facts["elder"]  # type: ignore[assignment]
    relic: Relic = world.facts["relic"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]

    world.say(
        f"Then came the twist: the relic was not meant to bring {elder.id} back, but to pass along {elder.id}'s last joke."
    )
    world.say(
        f"When {hero.id} tipped the {relic.label}, out rolled a flock of paper stars, each one carrying a tiny lesson: "
        f"'{hero.id}, magic is not for undoing goodbye; magic is for making goodbye shine.'"
    )
    hero.memes["wonder"] += 2.0
    hero.memes["peace"] = 1.0
    relic.meters["glow"] = 1.0
    world.para()
    world.say(
        f"{hero.id} laughed through a sniffle, and the sound was so bright that even the wind leaned in to listen."
    )
    world.say(
        f"By the end of the day, {hero.id} set the relic on a fencepost at {place.name}, where it glowed softly in the dusk "
        f"like a little lantern for remembering."
    )


def tell_story(world: World) -> World:
    start_story(world)
    raise_tension(world)
    resolve_story(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Person = f["hero"]  # type: ignore[assignment]
    relic: Relic = f["relic"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a tall tale for a young child about {hero.id}, a deceased magician, and {relic.label} at {place.name}.',
        f"Tell a magical story with a twist where {hero.id} learns what {relic.label} is really for.",
        f"Write a child-friendly tall tale set at {place.name} with glitter, memory, and a surprising ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Person = f["hero"]  # type: ignore[assignment]
    elder: Person = f["elder"]  # type: ignore[assignment]
    relic: Relic = f["relic"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who found the {relic.label} in the story?",
            answer=f"{hero.id} found the {relic.label} and carried it to {place.name}.",
        ),
        QAItem(
            question=f"Who had owned the {relic.label} before {hero.id}?",
            answer=f"It had belonged to {elder.id}, the deceased old magician.",
        ),
        QAItem(
            question=f"What happened when {hero.id} tried the magic at {place.name}?",
            answer=(
                f"The magic made a twist: it did not bring anyone back, but it turned into a gentle lesson "
                f"about remembering {elder.id} with wonder."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {hero.id} placing the {relic.label} on a fencepost at {place.name}, where it glowed "
                f"like a little lantern for remembering."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "deceased": (
        "What does deceased mean?",
        "Deceased means that a person has died. It is a respectful word adults use when they talk about someone who is no longer alive.",
    ),
    "magic": (
        "What is magic in a story?",
        "Magic is something wondrous that can seem impossible, like making lights appear, moving objects, or creating a surprise no one expected.",
    ),
    "twist": (
        "What is a twist in a story?",
        "A twist is a surprising turn that changes what you thought would happen next.",
    ),
    "tale": (
        "What is a tall tale?",
        "A tall tale is a story that exaggerates things in a fun way, with big characters, big events, and playful surprises.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        lines.append(f"  {p.id:12} type={p.type:7} meters={dict(p.meters)} memes={dict(p.memes)}")
    for r in world.relics.values():
        lines.append(
            f"  {r.id:12} kind={r.kind:7} owner={r.owner} carried_by={r.carried_by} "
            f"meters={dict(r.meters)} memes={dict(r.memes)}"
        )
    lines.append(f"  place={world.place.name} feature={world.place.feature} magic={world.place.magic_kind} twist={world.place.twist_kind}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.
place(P) :- place_fact(P).
relic(R) :- relic_fact(R).
person(X) :- person_fact(X).
deceased(X) :- deceased_fact(X).
twist(T) :- twist_fact(T).
magic(M) :- magic_fact(M).

valid_story(P, R, H, E) :- place(P), relic(R), person(H), deceased(E), H != E, magic(_), twist(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for rid in RELICS:
        lines.append(asp.fact("relic_fact", rid))
    for name in GIRLS + BOYS + ELDERS:
        lines.append(asp.fact("person_fact", name))
    for name in ELDERS:
        lines.append(asp.fact("deceased_fact", name))
    lines.append(asp.fact("magic_fact", "magic"))
    lines.append(asp.fact("twist_fact", "twist"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_stories_python())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_stories_python() -> list[tuple]:
    out = []
    for p in PLACES:
        for r in RELICS:
            for h in GIRLS + BOYS:
                for e in ELDERS:
                    if h != e:
                        out.append((p, r, h, e))
    return out


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    relic: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with magic, a twist, and a deceased old magician.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder-name", choices=ELDERS)
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
    relic = args.relic or rng.choice(list(RELICS))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRLS if hero_type == "girl" else BOYS)
    elder_name = args.elder_name or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        relic=relic,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_name=elder_name,
        elder_type="man" if "Grandpa" in elder_name or "Uncle" in elder_name or "Papa" in elder_name or "Mose" in elder_name else "man",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


CURATED = [
    StoryParams(place="barn", relic="hat", hero_name="Mina", hero_type="girl", elder_name="Grandpa Jeb", elder_type="man", trait="wonder-eyed"),
    StoryParams(place="fair", relic="fiddle", hero_name="Ollie", hero_type="boy", elder_name="Old Mose", elder_type="man", trait="curious"),
    StoryParams(place="river", relic="lantern", hero_name="Ruby", hero_type="girl", elder_name="Uncle Roan", elder_type="man", trait="brave"),
    StoryParams(place="canyon", relic="kite", hero_name="Ezra", hero_type="boy", elder_name="Papa Finn", elder_type="man", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, r, h, e in stories:
            print(f"  {p:10} {r:8} {h:10} {e}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
