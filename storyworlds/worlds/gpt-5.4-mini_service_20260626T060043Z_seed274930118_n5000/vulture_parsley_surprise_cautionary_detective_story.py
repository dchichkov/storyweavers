#!/usr/bin/env python3
"""
storyworlds/worlds/vulture_parsley_surprise_cautionary_detective_story.py
========================================================================

A small detective-story world about a curious missing herb, a surprised clue,
and a cautionary lesson involving a vulture.

Premise:
- A child detective notices that a basket of parsley has gone missing.
- Strange traces lead through a garden, a roof, and a tall tree.
- The culprit is not a thief in the usual sense, but a vulture trying to build
  a nest with soft green sprigs.
- The surprise turn reveals the missing parsley is still in the neighborhood.
- The cautionary ending teaches that wild birds should not be chased or fed
  careless scraps near people.

The simulation tracks:
- physical meters: carried weight, trail freshness, nest softness, messiness
- emotional memes: surprise, caution, relief, curiosity, worry

The story is rendered from the simulated state rather than as a fixed paragraph.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    phrase: str
    location: str
    smell: str
    hint: str


@dataclass
class Bird:
    label: str
    type: str
    nest_need: str
    risky: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        other = World(self.setting)
        other.entities = dataclasses.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", weather="windy", affords={"search", "chase", "observe"}),
    "yard": Setting(place="the backyard", weather="bright", affords={"search", "observe"}),
    "market": Setting(place="the little market lane", weather="breezy", affords={"search", "observe"}),
}

HEROES = {
    "mira": ("Mira", "girl"),
    "noah": ("Noah", "boy"),
    "lena": ("Lena", "girl"),
    "eli": ("Eli", "boy"),
}

BIRD = Bird(label="vulture", type="vulture", nest_need="soft green nest lining")

CLUES = {
    "leafy": Clue(
        label="leafy shred",
        phrase="a leafy green shred",
        location="under the bench",
        smell="fresh and grassy",
        hint="something was carried away gently, not torn apart",
    ),
    "feather": Clue(
        label="broad feather",
        phrase="a broad feather",
        location="beside the stone path",
        smell="dusty and wild",
        hint="a bird with a big shadow had been here",
    ),
    "parsley": Clue(
        label="parsley sprig",
        phrase="a parsley sprig",
        location="in the nest",
        smell="clean and bright",
        hint="the missing herb was still nearby",
    ),
}

TRAITS = ["curious", "careful", "bright-eyed", "patient", "sharp"]


@dataclass
class StoryParams:
    place: str
    hero: str
    herb: str = "parsley"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero_name, hero_type = HEROES[params.hero]
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=f"a {random.choice(TRAITS)} child detective",
        location=setting.place,
        meters={"curiosity": 1.0, "worry": 0.0, "relief": 0.0},
        memes={"surprise": 0.0, "caution": 0.0, "hope": 0.0},
        traits=["little", random.choice(TRAITS)],
    ))

    gardener = world.add(Entity(
        id="gardener",
        kind="character",
        type="adult",
        label="Mrs. Pine",
        location=setting.place,
        meters={"patience": 1.0},
        memes={"worry": 0.0, "relief": 0.0},
    ))

    herb = world.add(Entity(
        id="parsley",
        kind="thing",
        type="herb",
        label="parsley",
        phrase="a small basket of parsley",
        owner="gardener",
        location=setting.place,
        meters={"missing": 1.0, "freshness": 1.0},
        memes={"value": 1.0},
    ))

    bird = world.add(Entity(
        id="vulture",
        kind="character",
        type="vulture",
        label="the vulture",
        location="tall tree",
        meters={"hunger": 1.0, "nest_need": 1.0, "weight": 1.0},
        memes={"surprise": 0.0, "caution": 0.0},
    ))

    nest = world.add(Entity(
        id="nest",
        kind="thing",
        type="nest",
        label="nest",
        phrase="a rough nest high in a tree",
        location="tall tree",
        meters={"softness": 0.3},
        memes={"safe": 0.0},
    ))

    world.facts.update(hero=hero, gardener=gardener, herb=herb, bird=bird, nest=nest)
    return world


def notice_missing(world: World) -> None:
    hero = world.get("hero")
    gardener = world.get("gardener")
    herb = world.get("parsley")
    world.say(
        f"{hero.label} was a small detective who noticed details that other people missed."
    )
    world.say(
        f"One breezy morning, {gardener.label} frowned at the herb basket and found that "
        f"the {herb.label} was gone."
    )
    hero.memes["surprise"] += 0.5
    hero.meters["curiosity"] += 1.0
    world.say(
        f"{hero.label} blinked in surprise and promised to follow the clues without making a fuss."
    )


def follow_clues(world: World) -> None:
    hero = world.get("hero")
    bird = world.get("vulture")
    world.para()
    world.say(
        f"{hero.label} looked near the stone path and found {CLUES['feather'].phrase}."
    )
    world.say(
        f"The feather smelled {CLUES['feather'].smell}, which made {hero.label} more careful."
    )
    hero.memes["caution"] += 0.5
    world.say(
        f"Then {hero.label} found {CLUES['leafy'].phrase} {CLUES['leafy'].location}."
    )
    world.say(
        f"That clue hinted that something had been carried away gently, and it pointed toward {bird.label}."
    )


def observe_bird(world: World) -> None:
    hero = world.get("hero")
    bird = world.get("vulture")
    nest = world.get("nest")
    world.para()
    world.say(
        f"At the tall tree, {hero.label} saw {bird.label} tugging soft green bits into {nest.label}."
    )
    bird.memes["surprise"] += 0.5
    hero.memes["surprise"] += 0.5
    hero.meters["worry"] += 0.5
    world.say(
        f"The sight was a surprise: the missing parsley had not been stolen for no reason at all."
    )
    world.say(
        f"It was being used to line a nest, because the bird wanted something soft and safe for its eggs."
    )


def cautionary_turn(world: World) -> None:
    hero = world.get("hero")
    gardener = world.get("gardener")
    bird = world.get("vulture")
    nest = world.get("nest")
    herb = world.get("parsley")

    world.para()
    world.say(
        f"{hero.label} wanted to rush closer, but remembered that wild birds can be nervous and strong."
    )
    hero.memes["caution"] += 1.0
    world.say(
        f"Instead, {hero.label} waved to {gardener.label} from far away and called out the clue."
    )
    world.say(
        f"{gardener.label} explained that people should not chase a wild bird or reach into its nest."
    )
    world.say(
        f"That was the cautionary lesson: even a strange problem should be handled gently."
    )

    # Resolution state
    herb.location = "the herb basket"
    herb.meters["missing"] = 0.0
    herb.meters["freshness"] = 0.8
    nest.meters["softness"] = 0.8
    bird.memes["caution"] += 0.5
    world.get("gardener").memes["relief"] = 1.0
    hero.meters["relief"] = 1.0
    world.say(
        f"{gardener.label} left a little dish of water far from the tree and gathered more parsley from the garden bed."
    )
    world.say(
        f"Soon the basket was full again, and the vulture stayed in the tree instead of being frightened away."
    )
    world.say(
        f"{hero.label} smiled, because the mystery had an answer and the garden stayed safe."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    notice_missing(world)
    follow_clues(world)
    observe_bird(world)
    cautionary_turn(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- protagonist(H).
bird(B) :- species(B, vulture).
herb(P) :- herb_name(P, parsley).

missing(Herb) :- item(Herb), status(Herb, missing).
clue_points_to_bird(C) :- clue(C), indicates(C, bird).
surprise_turn(H) :- sees(H, unexpected_bird_behavior).
cautionary_lesson(H) :- learns(H, avoid_chasing_wild_birds).

solution_found :- missing(parsley), clue_points_to_bird(feather), item(parsley), status(parsley, recovered).

safe_resolution :- solution_found, cautionary_lesson(hero).
#show solution_found/0.
#show safe_resolution/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("protagonist", "hero"))
    lines.append(asp.fact("species", "vulture", "vulture"))
    lines.append(asp.fact("herb_name", "parsley", "parsley"))
    lines.append(asp.fact("item", "parsley"))
    lines.append(asp.fact("status", "parsley", "missing"))
    lines.append(asp.fact("clue", "feather"))
    lines.append(asp.fact("indicates", "feather", "bird"))
    lines.append(asp.fact("sees", "hero", "unexpected_bird_behavior"))
    lines.append(asp.fact("learns", "hero", "avoid_chasing_wild_birds"))
    lines.append(asp.fact("status", "parsley", "recovered"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_resolution/0.\n#show solution_found/0."))
    atoms = {sym.name for sym in model}
    expected = {"solution_found", "safe_resolution"}
    if atoms == expected:
        print("OK: ASP twin matches the intended solution.")
        return 0
    print(f"MISMATCH: got {sorted(atoms)}, expected {sorted(expected)}")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short detective story for a young child about a missing parsley basket and a surprising clue.',
        f"Tell a cautionary mystery about {world.get('hero').label}, a vulture, and the missing parsley.",
        "Create a simple detective tale where the answer is found through gentle observation instead of chasing a wild bird.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    gardener = world.get("gardener")
    herb = world.get("parsley")
    bird = world.get("vulture")
    nest = world.get("nest")
    return [
        QAItem(
            question=f"Who solved the mystery about the missing {herb.label}?",
            answer=f"{hero.label}, the child detective, solved it by following clues and staying calm.",
        ),
        QAItem(
            question="What surprising thing did the detective learn about the vulture?",
            answer=f"The detective learned that the {bird.label} was using the parsley to soften its nest in the tree.",
        ),
        QAItem(
            question=f"Why did {gardener.label} feel relieved at the end?",
            answer=f"{gardener.label} felt relieved because the {herb.label} was found, the basket was filled again, and the bird was left alone safely.",
        ),
        QAItem(
            question="What cautionary lesson did the story teach?",
            answer="It taught that wild birds should not be chased or disturbed, and that a mystery should be handled gently.",
        ),
        QAItem(
            question="Where was the parsley found?",
            answer=f"It was found high in the {nest.label}, where the vulture had taken it for nesting material.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is parsley?",
            answer="Parsley is a green herb used to flavor food, and it can also be a soft plant that birds might gather for nesting.",
        ),
        QAItem(
            question="What is a vulture?",
            answer="A vulture is a large wild bird with a strong beak and a big wingspan.",
        ),
        QAItem(
            question="Why should people not chase wild birds?",
            answer="People should not chase wild birds because it can frighten them, make them dangerous, or disturb their nests.",
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
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    herb: str = "parsley"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld about vulture, parsley, surprise, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    return StoryParams(place=place, hero=hero, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = tell_story(params)
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


def asp_story_ok() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_resolution/0.\n#show solution_found/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for hero in HEROES:
                params = StoryParams(place=place, hero=hero, seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
