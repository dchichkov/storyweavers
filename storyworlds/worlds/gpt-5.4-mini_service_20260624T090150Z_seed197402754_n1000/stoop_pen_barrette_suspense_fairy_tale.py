#!/usr/bin/env python3
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


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    object_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    mood: str
    shadows: str


@dataclass(frozen=True)
class Item:
    id: str
    label: str
    phrase: str
    hidden: bool = False


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    trait: str


PLACES = {
    "stoop": Place(id="stoop", label="the stoop", mood="quiet", shadows="long"),
    "garden_gate": Place(id="garden_gate", label="the garden gate", mood="still", shadows="thin"),
    "moonwell": Place(id="moonwell", label="the moonwell", mood="hushed", shadows="silver"),
}

OBJECTS = {
    "pen": Item(id="pen", label="pen", phrase="a small black pen"),
    "barrette": Item(id="barrette", label="barrette", phrase="a pearl barrette"),
    "key": Item(id="key", label="key", phrase="a tiny brass key"),
}

HEROES = [
    CharacterSpec("Mira", "brave"),
    CharacterSpec("Nell", "gentle"),
    CharacterSpec("Toby", "curious"),
    CharacterSpec("Elias", "small"),
]

HELPERS = [
    CharacterSpec("grandmother", "wise"),
    CharacterSpec("mother", "kind"),
    CharacterSpec("uncle", "patient"),
    CharacterSpec("fairy", "quiet"),
]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        clone = World(self.params)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale suspense story world with a stoop, a pen, and a barrette.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--object", dest="object_name", choices=sorted(OBJECTS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice([h.name for h in HEROES])
    helper = args.helper or rng.choice([h.name for h in HELPERS])
    object_name = args.object_name or rng.choice(list(OBJECTS))
    return StoryParams(place=place, hero=hero, helper=helper, object_name=object_name)


def _set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def tell(params: StoryParams) -> World:
    world = World(params)
    place = PLACES[params.place]
    obj = OBJECTS[params.object_name]
    hero_spec = next((h for h in HEROES if h.name == params.hero), HEROES[0])
    helper_spec = next((h for h in HELPERS if h.name == params.helper), HELPERS[0])

    hero = world.add(Entity(id="hero", kind="character", label=hero_spec.name))
    helper = world.add(Entity(id="helper", kind="character", label=helper_spec.name))
    item = world.add(Entity(id=obj.id, label=obj.label, phrase=obj.phrase, owner=hero.id))

    world.facts.update(place=place, hero=hero, helper=helper, item=item)

    world.say(
        f"Once upon a dusk, {hero.label} lived by {place.label}, where the air was quiet and the shadows stayed long."
    )
    world.say(
        f"{hero.label} loved a little {obj.label}, for it held secret lines and tiny wishes."
    )
    world.para()
    world.say(
        f"One evening, while {place.label} grew still, {hero.label} found {obj.phrase} on the cold stoop."
    )
    _set_meme(hero, "unease", 1)
    _set_meme(hero, "curiosity", 1)
    _set_meter(item, "lost", 1)
    world.say(
        f"It looked harmless, yet the way it gleamed in the fading light made {hero.label} hold their breath."
    )
    world.para()
    world.say(
        f"Then a hush moved behind the gate, and {helper_spec.name} appeared with a {OBJECTS['barrette'].phrase} tucked in a pocket."
    )
    _set_meme(helper, "mystery", 1)
    _set_meme(hero, "hope", 1)
    world.say(
        f"{helper_spec.name} warned that if the missing thing was not found before moonrise, the little story would end in sorrow."
    )
    _set_meme(hero, "suspense", 2)
    _set_meter(hero, "searching", 1)
    world.para()
    world.say(
        f"{hero.label} searched the stoop, the seam of the step, and the dark crack beneath it, while the night listened."
    )
    _set_meter(hero, "searching", 1)
    if obj.id == "pen":
        world.say(
            f"At last, the pen clicked against the stone, half hidden under a leaf, as if it had been waiting for a brave hand."
        )
    elif obj.id == "barrette":
        world.say(
            f"At last, the barrette flashed like a star beside the step, caught in a thread of silver dust."
        )
    else:
        world.say(
            f"At last, the key lay under the edge of the stoop, tiny as a beetle and just as secret."
        )
    _set_meter(item, "found", 1)
    _set_meme(hero, "relief", 2)
    _set_meme(helper, "relief", 1)
    world.say(
        f"{hero.label} picked it up carefully, and the night felt less like a riddle."
    )
    world.para()
    world.say(
        f"{helper_spec.name} smiled, and together they set the {obj.label} beside the {OBJECTS['barrette'].label} so nothing would vanish again."
    )
    _set_meter(item, "safe", 1)
    world.say(
        f"By the time moonlight rested on {place.label}, {hero.label} was calm, the stoop was peaceful, and the small treasure was home."
    )

    world.facts.update(resolved=True)
    return world


def generate_prompts(world: World) -> list[str]:
    p: Place = world.facts["place"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        f"Write a short fairy tale with suspense about {hero.label} and {item.label} on the stoop.",
        f"Tell a gentle story where {helper.label} helps {hero.label} find {item.phrase} before night falls at {p.label}.",
        f"Create a child-friendly suspense story about a stoop, a pen, and a barrette.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.label} find the missing {item.label}?",
            answer=f"{hero.label} found the {item.label} on the stoop, where the night had made everything feel hushed and mysterious.",
        ),
        QAItem(
            question=f"Who helped {hero.label} during the scary search?",
            answer=f"{helper.label} helped {hero.label} look for the missing {item.label} and stay brave until it was found.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful at {place.label}?",
            answer=f"It felt suspenseful because the {item.label} was lost at dusk, and {hero.label} had to search before moonrise.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stoop?",
            answer="A stoop is the small set of steps or flat landing just outside a door.",
        ),
        QAItem(
            question="What is a pen for?",
            answer="A pen is used for writing words and drawing lines on paper.",
        ),
        QAItem(
            question="What is a barrette for?",
            answer="A barrette is a small hair clip that helps hold hair in place.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if ent.owner:
            bits.append(f"owner={ent.owner!r}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by!r}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id}: {', '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(stoop).
place(garden_gate).
place(moonwell).

hero(mira).
hero(nell).
hero(toby).
hero(elias).

item(pen).
item(barrette).
item(key).

suspense_story(P,H,I) :- place(P), hero(H), item(I), H != I.
#show suspense_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h.name.lower()))
    for i in OBJECTS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show suspense_story/3."))
    atoms = set(asp.atoms(model, "suspense_story"))
    py = {(p, h.name.lower(), i) for p in PLACES for h in HEROES for i in OBJECTS}
    if atoms == py:
        print(f"OK: clingo gate matches python combinatorics ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(atoms - py))
    print("only in python:", sorted(py - atoms))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        print("== Prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== Story Q&A ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print()
        print("== World Q&A ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


CURATED = [
    StoryParams(place="stoop", hero="Mira", helper="grandmother", object_name="pen"),
    StoryParams(place="garden_gate", hero="Nell", helper="fairy", object_name="barrette"),
    StoryParams(place="moonwell", hero="Toby", helper="mother", object_name="key"),
]


def resolve_story_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show suspense_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show suspense_story/3."))
        print(sorted(asp.atoms(model, "suspense_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_story_args(args, random.Random(seed))
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
            header = f"### {p.hero} at {p.place} with {p.object_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
