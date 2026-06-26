#!/usr/bin/env python3
"""
storyworlds/worlds/miracle_rhyme_fairy_tale.py
==============================================

A small fairy-tale storyworld about a child, a hush of doubt, and a miracle
that arrives when a true rhyme is spoken with a kind heart.

Seed tale:
---
In a little kingdom, a child found a tired, dry garden where the roses had
gone gray and the fountain had gone still. The child loved stories and songs,
and the old grandmother said that once, long ago, a miracle rhyme could wake
sleeping places. A windy night came, and the child wanted to sing the rhyme at
the fountain. The grandmother worried the child would make a fuss, or that
nothing magical would happen at all. But the child listened, spoke the rhyme
with care, and a silver drop of light fell into the basin. The fountain sang
again, the roses brightened, and the whole garden looked as if it had just
been dreamed awake.

World model:
---
Physical meters:
    - dryness, bloom, glow, echo
Emotional memes:
    - hope, worry, wonder, joy, trust

Narrative instruments:
    - fairy-tale framing
    - a spoken rhyme that can cause a miracle
    - a clear turn from doubt to wonder
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class VerseCharm:
    id: str
    label: str
    rhyme: str
    spark: str
    cure: str
    needed_place: str
    needed_weather: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    charm: str
    hero_name: str
    hero_type: str
    guardian_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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


SETTINGS = {
    "rose_garden": Place(id="rose_garden", label="the rose garden", kind="garden"),
    "moon_well": Place(id="moon_well", label="the moon well", kind="well"),
    "castle_courtyard": Place(id="castle_courtyard", label="the castle courtyard", kind="courtyard"),
}

CHARMISTRY = {
    "wake_garden": VerseCharm(
        id="wake_garden",
        label="the waking rhyme",
        rhyme="Bloom, bright bloom, and lift your crown;  \nDry old dust, please settle down.",
        spark="silver light",
        cure="the garden woke",
        needed_place="rose_garden",
        tags={"garden", "bloom", "miracle"},
    ),
    "wake_well": VerseCharm(
        id="wake_well",
        label="the well-song rhyme",
        rhyme="Well of night, begin to shine;  \nGive us water, line by line.",
        spark="moon-water",
        cure="the well sang",
        needed_place="moon_well",
        tags={"well", "water", "miracle"},
    ),
    "wake_courtyard": VerseCharm(
        id="wake_courtyard",
        label="the courtyard rhyme",
        rhyme="Stone awake, and echo clear;  \nKind old walls, draw magic near.",
        spark="golden echo",
        cure="the stones shivered with life",
        needed_place="castle_courtyard",
        tags={"castle", "echo", "miracle"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Elena", "Rose", "Tessa"]
BOY_NAMES = ["Alden", "Finn", "Theo", "Robin", "Perrin", "Jasper"]
TRAITS = ["gentle", "curious", "brave", "patient", "soft-spoken", "earnest"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with rhyme and miracle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMISTRY)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["grandmother", "grandfather"])
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


def _random_choice(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and args.place and CHARMISTRY[args.charm].needed_place != args.place:
        raise StoryError("That charm does not belong in that place.")
    place = args.place or _random_choice(rng, list(SETTINGS))
    charm = args.charm or _random_choice(rng, [k for k, v in CHARMISTRY.items() if v.needed_place == place])
    gender = args.gender or _random_choice(rng, ["girl", "boy"])
    name = args.name or _random_choice(rng, GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or _random_choice(rng, ["grandmother", "grandfather"])
    return StoryParams(place=place, charm=charm, hero_name=name, hero_type=gender, guardian_type=guardian)


def _hero_title(hero: Entity) -> str:
    return "girl" if hero.type == "girl" else "boy"


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        memes={"hope": 0.0, "wonder": 0.0, "joy": 0.0, "trust": 0.0, "worry": 0.0},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=params.guardian_type,
        label=f"the {params.guardian_type}",
        memes={"hope": 0.0, "wonder": 0.0, "joy": 0.0, "trust": 0.0, "worry": 0.0},
    ))
    place = world.place
    if place.id == "rose_garden":
        place.meters = {"dryness": 1.0, "bloom": 0.1, "glow": 0.0, "echo": 0.0}
    elif place.id == "moon_well":
        place.meters = {"dryness": 1.0, "bloom": 0.0, "glow": 0.1, "echo": 0.0}
    else:
        place.meters = {"dryness": 0.7, "bloom": 0.2, "glow": 0.0, "echo": 0.2}
    world.facts.update(hero=hero, guardian=guardian, charm=CHARMISTRY[params.charm], params=params)
    return world


def _miracle_possible(world: World, charm: VerseCharm) -> bool:
    return world.place.id == charm.needed_place


def _perform_charm(world: World, hero: Entity, guardian: Entity, charm: VerseCharm) -> None:
    place = world.place
    place.memes["worry"] = place.memes.get("worry", 0.0) + 1.0
    hero.memes["hope"] += 1.0
    hero.memes["worry"] += 0.2
    world.say(f"In {place.label}, the air felt old and still, and even the petals seemed to wait.")
    world.say(f"{hero.id} loved rhymes, yet {hero.pronoun('possessive')} heart beat fast with hope.")
    world.say(f"{guardian.pronoun().capitalize()} warned, 'A small song can be a big thing, and not every wish will ring.'")
    world.say(f"But {hero.id} lifted {hero.pronoun('possessive')} chin and whispered the verse:")
    world.say(f"“{charm.rhyme}”")
    hero.memes["trust"] += 1.0
    guardian.memes["worry"] += 0.5
    if _miracle_possible(world, charm):
        place.meters["dryness"] = 0.0
        place.meters["bloom"] = 1.0
        place.meters["glow"] = 1.0
        place.meters["echo"] = 1.0
        hero.memes["wonder"] += 1.0
        hero.memes["joy"] += 1.0
        guardian.memes["wonder"] += 1.0
        guardian.memes["joy"] += 1.0
        guardian.memes["worry"] = 0.0
        world.facts["miracle"] = True
        world.say(f"A silver drop of light fell softly down, and {charm.cure}.")
        world.say(f"The roses rose red, the stones grew warm, and the whole place sounded like a lullaby.")
        world.say(f"{guardian.pronoun().capitalize()} smiled through shining eyes and said, 'That was the sort of miracle that listens back.'")
    else:
        world.facts["miracle"] = False
        world.say("The rhyme was lovely, but the world gave only a quiet sigh.")
        world.say(f"{hero.id} did not lose {hero.pronoun('possessive')} courage; {hero.pronoun().capitalize()} learned that some wonders need the right home.")
    world.para()
    if world.facts["miracle"]:
        world.say(f"By moonrise, {place.label} was bright and breathing again, as if it had just remembered how to hope.")
        world.say(f"{hero.id} and {guardian.pronoun('subject')} walked home with light in their pockets and song in their steps.")
    else:
        world.say(f"{hero.id} tucked the rhyme away like a seed, certain it would bloom in the right place one day.")
        world.say(f"{guardian.pronoun().capitalize()} held {hero.pronoun('possessive')} hand, and the two of them went home under the stars.")


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    hero = world.facts["hero"]
    guardian = world.facts["guardian"]
    charm = world.facts["charm"]

    world.say(f"Once in a little kingdom, there lived a {_hero_title(hero)} named {hero.id}.")
    world.say(f"{hero.id} was {random.choice(TRAITS)} and loved stories, especially ones that rhymed.")
    world.say(f"The {params.guardian_type} knew an old tale: if a true rhyme met a willing heart, a miracle might wake where it was needed most.")
    world.para()
    world.say(f"One dusk, {hero.id} went with {guardian.pronoun('possessive')} {params.guardian_type} to {world.place.label}.")
    world.say(f"Long before, that place had been bright; now it was dry, dim, and a little forlorn.")
    _perform_charm(world, hero, guardian, charm)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    c = world.facts["charm"]
    return [
        f"Write a short fairy tale where {p.hero_name} speaks a rhyme and a miracle wakes {world.place.label}.",
        f"Tell a child-friendly story about a {p.hero_type} who tries a magical rhyme called {c.label}.",
        f"Write a gentle fairy tale with rhyme, wonder, and a clear miracle in {world.place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    guardian = world.facts["guardian"]
    charm = world.facts["charm"]
    if world.facts.get("miracle"):
        answer = f"The rhyme worked, and {charm.cure}; the place changed from dry and dim to bright and alive."
    else:
        answer = "The rhyme was beautiful, but the miracle did not wake there; the child saved the song for a better time."
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.hero_name}, a {p.hero_type} child, and {guardian.pronoun('possessive')} {p.guardian_type}, in a fairy-tale garden of wonder.",
        ),
        QAItem(
            question=f"What did {p.hero_name} speak in the story?",
            answer=f"{p.hero_name} spoke a rhyme called {charm.label}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=answer,
        ),
    ]


WORLD_KNOWLEDGE = {
    "miracle": QAItem(
        question="What is a miracle in a fairy tale?",
        answer="A miracle is a wonderful event that seems impossible but happens anyway, often in a magical story.",
    ),
    "rhyme": QAItem(
        question="What is a rhyme?",
        answer="A rhyme is a sound pattern where words end with matching or nearly matching sounds, like 'light' and 'night'.",
    ),
    "garden": QAItem(
        question="What is a garden?",
        answer="A garden is a place where flowers, plants, and trees are grown and cared for.",
    ),
    "well": QAItem(
        question="What is a well?",
        answer="A well is a deep hole or shaft that people use to get water from underground.",
    ),
    "bloom": QAItem(
        question="What does bloom mean?",
        answer="To bloom means to open into a flower or become fresh, bright, and full of life.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["charm"].tags)
    out = [WORLD_KNOWLEDGE["miracle"], WORLD_KNOWLEDGE["rhyme"]]
    if "garden" in tags:
        out.append(WORLD_KNOWLEDGE["garden"])
    if "well" in tags:
        out.append(WORLD_KNOWLEDGE["well"])
    if "bloom" in tags:
        out.append(WORLD_KNOWLEDGE["bloom"])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place.label} meters={world.place.meters} memes={world.place.memes}")
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(place).
charm(charm).

miracle_possible(C) :- charm(C), needed_place(C, P), current_place(P).
resolved(C) :- miracle_possible(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("current_place", SETTINGS[next(iter(SETTINGS))].id)]
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
    for cid, charm in CHARMISTRY.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("needed_place", cid, charm.needed_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {p for p in SETTINGS if any(c.needed_place == p for c in CHARMISTRY.values())}
    model = asp.one_model(asp_program("#show miracle_possible/1."))
    atoms = set(asp.atoms(model, "miracle_possible"))
    asp_set = {a[0] for a in atoms}
    if asp_set == py:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python reasonableness:")
    print("python:", sorted(py))
    print("asp:", sorted(asp_set))
    return 1


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
    StoryParams(place="rose_garden", charm="wake_garden", hero_name="Mira", hero_type="girl", guardian_type="grandmother"),
    StoryParams(place="moon_well", charm="wake_well", hero_name="Alden", hero_type="boy", guardian_type="grandfather"),
    StoryParams(place="castle_courtyard", charm="wake_courtyard", hero_name="Nora", hero_type="girl", guardian_type="grandmother"),
]


def resolve_random(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or random.choice(list(SETTINGS)),
        charm=args.charm or random.choice([k for k, v in CHARMISTRY.items() if v.needed_place == (args.place or next(iter(SETTINGS)))]),
        hero_name=args.name or _random_choice(rng, GIRL_NAMES if (args.gender or _random_choice(rng, ["girl", "boy"])) == "girl" else BOY_NAMES),
        hero_type=args.gender or _random_choice(rng, ["girl", "boy"]),
        guardian_type=args.guardian or _random_choice(rng, ["grandmother", "grandfather"]),
    )


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        return [generate(p) for p in CURATED]
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 50):
        seed = base_seed + i
        i += 1
        rng = random.Random(seed)
        try:
            params = resolve_params(args, rng)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show miracle_possible/1."))
        return
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show miracle_possible/1."))
        print(sorted(asp.atoms(model, "miracle_possible")))
        return

    samples = generate_many(args)
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
