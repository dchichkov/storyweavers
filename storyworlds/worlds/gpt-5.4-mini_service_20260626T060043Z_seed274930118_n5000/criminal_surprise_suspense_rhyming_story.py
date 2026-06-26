#!/usr/bin/env python3
"""
A compact rhyming storyworld about a child who notices a small crime, feels
suspense, and is surprised by the gentle resolution.

Domain premise:
- A little helper sees a missing shiny item in a playful town.
- Suspense builds as clues appear one by one.
- Surprise lands when the "criminal" turns out to be a sneaky raccoon, and the
  helper recovers the item with a clever, kind plan.

The world model tracks physical meters and emotional memes:
- meters: cluefulness, hiddenness, distance, carried, recovered
- memes: curiosity, suspense, surprise, worry, relief, pride

The story is intentionally child-facing, concrete, and rhyming in a few places,
with a full beginning-middle-turn-ending shape.
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
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the market lane"
    affords: set[str] = field(default_factory=lambda: {"search", "hide", "recover"})


@dataclass
class Clue:
    id: str
    phrase: str
    reveal: str
    adds_suspense: float = 1.0
    adds_cluefulness: float = 1.0


@dataclass
class Perpetrator:
    id: str
    label: str
    type: str
    surprise_line: str
    hiding_place: str
    gives_back: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    clue_order: list[str] = field(default_factory=list)
    clue_index: int = 0
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "market": Setting(place="the market lane", affords={"search", "hide", "recover"}),
    "fair": Setting(place="the little fair", affords={"search", "hide", "recover"}),
    "dock": Setting(place="the quiet dock", affords={"search", "hide", "recover"}),
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Theo", "Ava", "Ben"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["girl", "boy"]

PERPETRATORS = {
    "raccoon": Perpetrator(
        id="raccoon",
        label="a sneaky raccoon",
        type="raccoon",
        surprise_line="It was only a raccoon with a shiny tail and a nimble trot.",
        hiding_place="under a blue crate",
        gives_back="rolled the item out with a playful pat",
    ),
    "cat": Perpetrator(
        id="cat",
        label="a curious cat",
        type="cat",
        surprise_line="It was only a cat with bright eyes and a quiet pounce.",
        hiding_place="behind a stack of baskets",
        gives_back="nudged the item forward with a soft little meow",
    ),
}

TREASURES = {
    "bell": Entity(id="bell", type="thing", label="bell", phrase="a bright silver bell"),
    "cookie_tin": Entity(id="tin", type="thing", label="tin", phrase="a round cookie tin"),
    "kite": Entity(id="kite", type="thing", label="kite", phrase="a red kite with a ribbon tail"),
}

CLUES = {
    "tiny_tracks": Clue(
        id="tiny_tracks",
        phrase="tiny tracks in the dust",
        reveal="Small tracks pointed to the right hiding spot.",
    ),
    "gleam": Clue(
        id="gleam",
        phrase="a little gleam near a crate",
        reveal="A shiny glimmer winked from under a crate.",
    ),
    "crumbs": Clue(
        id="crumbs",
        phrase="crumbs and a rustle",
        reveal="Crumbs and rustles gave away the sneaky thief.",
    ),
}

CLUE_ORDER = ["tiny_tracks", "gleam", "crumbs"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    treasure: str
    perp: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(place: str, treasure: str, perp: str) -> bool:
    return place in SETTINGS and treasure in TREASURES and perp in PERPETRATORS


def explain_invalid(place: str, treasure: str, perp: str) -> str:
    return f"(No story: {place!r}, {treasure!r}, and {perp!r} do not form a small, playful criminal surprise tale.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not valid_story(params.place, params.treasure, params.perp):
        raise StoryError(explain_invalid(params.place, params.treasure, params.perp))

    world = World(setting=SETTINGS[params.place])
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"cluefulness": 0.0, "distance": 0.0},
        memes={"curiosity": 1.0, "suspense": 0.0, "surprise": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type="mother",
        label="the grown-up",
        meters={"cluefulness": 0.0},
        memes={"worry": 0.0, "relief": 0.0},
    ))
    treasure_proto = TREASURES[params.treasure]
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_proto.type,
        label=treasure_proto.label,
        phrase=treasure_proto.phrase,
        owner="town",
        location="hidden",
        meters={"hiddenness": 1.0, "recovered": 0.0},
    ))
    perp = world.add(Entity(
        id="perp",
        kind="character",
        type=PERPETRATORS[params.perp].type,
        label=PERPETRATORS[params.perp].label,
        meters={"hiddenness": 1.0, "carried": 1.0},
        memes={"mischief": 1.0},
    ))

    world.facts.update(hero=hero, adult=adult, treasure=treasure, perp=perp, clue_order=CLUE_ORDER)

    # Act 1: setup
    world.say(f"{hero.label} went to {world.setting.place} on a bright, breezy day.")
    world.say(f"{hero.label} loved to roam and look around, with curious eyes that liked to play.")
    world.say(f"Then {hero.label} noticed {treasure.phrase} was gone from the shelf away.")

    # Act 2: suspense
    world.para()
    world.say(f"The grown-up frowned and said, \"Let's look and think; we'll find a clue today.\"")
    hero.memes["worry"] += 0.5
    hero.memes["suspense"] += 1.0
    adult.memes["worry"] += 0.5
    world.say(f"{hero.label} peered for signs in a hush-hush way, and the air felt tight with suspense and sway.")

    # Clues revealed one by one
    for clue_id in world.clue_order:
        clue = CLUES[clue_id]
        world.clue_index += 1
        hero.meters["cluefulness"] += clue.adds_cluefulness
        hero.memes["suspense"] += clue.adds_suspense
        world.say(f"First came {clue.phrase}; {clue.reveal}")
        if clue_id == "tiny_tracks":
            world.say("The little steps went tap-tap-tap, like a rhythm in a rhyme at play.")
        elif clue_id == "gleam":
            world.say("The gleam said, \"Peek and seek,\" so they searched the stacks in a careful, quiet way.")
        else:
            world.say("A crumb trail curled like a funny swirl, and the mystery grew more tricky and gray.")

    # Surprise reveal
    world.para()
    perp_ent = world.get("perp")
    treasure_ent = world.get("treasure")
    world.say(PERPETRATORS[params.perp].surprise_line)
    hero.memes["surprise"] += 2.0
    hero.memes["suspense"] = 0.0
    adult.memes["worry"] = 0.2
    world.say(f"Under {PERPETRATORS[params.perp].hiding_place}, they found the lost {treasure_ent.label}, all safe and bright.")
    world.say(f"The sneaky thief {PERPETRATORS[params.perp].gives_back}, and the chase turned into a giggle-light.")

    # Resolution
    world.para()
    treasure_ent.location = "returned"
    treasure_ent.meters["recovered"] = 1.0
    treasure_ent.meters["hiddenness"] = 0.0
    perp_ent.meters["hiddenness"] = 0.0
    hero.memes["relief"] += 2.0
    hero.memes["pride"] += 1.0
    adult.memes["relief"] += 2.0
    world.say(f"The grown-up smiled and said, \"A surprise like that can make a day feel bright.\"")
    world.say(f"{hero.label} waved goodbye to the thief and carried {treasure_ent.phrase} home with joy in sight.")
    world.say(f"So the missing thing came back again, and the town felt merry and tidy by night.")

    return world


# ---------------------------------------------------------------------------
# Story / QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    perp = f["perp"]
    return [
        f"Write a short rhyming story about {hero.label}, a missing {treasure.label}, and a surprising thief.",
        f"Tell a suspenseful but gentle story where {hero.label} finds clues and learns who took the {treasure.label}.",
        f"Write a child-friendly criminal surprise tale with a rhyming ending and a returned {treasure.label}.",
        f"Make the story feel like a little mystery song with clues, suspense, and a happy surprise.",
        f"Use the word \"criminal\" in a harmless, playful way while {hero.label} solves the mystery at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    perp = f["perp"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who found out that the {treasure.label} was missing at {place}?",
            answer=f"{hero.label} noticed the missing {treasure.label} first and started the search.",
        ),
        QAItem(
            question="What made the story feel suspenseful?",
            answer="The missing treasure, the clues, and the careful searching made the story feel suspenseful.",
        ),
        QAItem(
            question=f"Who was the surprising criminal in the story?",
            answer=f"The surprising criminal was {PERPETRATORS[perp.type].label}, even though it turned out to be playful rather than scary.",
        ),
        QAItem(
            question=f"What happened to the {treasure.label} at the end?",
            answer=f"The {treasure.label} was found and brought back home safely.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the missing thing returned and everyone feeling relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of not knowing what will happen next, so you keep wondering and watching.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does criminal mean?",
            answer="A criminal is someone who breaks the rules or the law, but in a child-safe story we keep the trouble small and gentle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(parts)}")
    lines.append(f"clue_order={world.clue_order}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

valid(Place,Treasure,Perp) :- setting(Place), treasure(Treasure), perpetrator(Perp).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for pid in PERPETRATORS:
        lines.append(asp.fact("perpetrator", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted((place, treasure, perp) for place in SETTINGS for treasure in TREASURES for perp in PERPETRATORS)


def asp_verify() -> int:
    p = set(python_valid())
    a = set(asp_valid())
    if p == a:
        print(f"OK: ASP and Python agree on {len(a)} combinations.")
        return 0
    print("MISMATCH:")
    if p - a:
        print(" only in Python:", sorted(p - a))
    if a - p:
        print(" only in ASP:", sorted(a - p))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming mystery storyworld with suspense and a playful criminal surprise.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--treasure", choices=list(TREASURES))
    ap.add_argument("--perp", choices=list(PERPETRATORS))
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
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    treasure = args.treasure or rng.choice(list(TREASURES))
    perp = args.perp or rng.choice(list(PERPETRATORS))
    if not valid_story(place, treasure, perp):
        raise StoryError(explain_invalid(place, treasure, perp))
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, treasure=treasure, perp=perp)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combinations")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for treasure in TREASURES:
                for perp in PERPETRATORS:
                    params = StoryParams(
                        place=place,
                        hero_name=HERO_NAMES[0],
                        hero_type="girl",
                        treasure=treasure,
                        perp=perp,
                        seed=base_seed,
                    )
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
