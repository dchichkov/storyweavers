#!/usr/bin/env python3
"""
A small fable-style storyworld about haggling over a brush, learning to discern
its use, and resolving a surprise through repetition and patience.

The world models a child-facing classic fable domain:
- a small animal protagonist
- a practical brush
- a seller or helper who haggles
- repeated attempts that reveal the brush's real use
- a surprise turn followed by a moral-style ending
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        animal = {"fox", "rabbit", "mouse", "owl", "crow", "cat", "dog", "hare"}
        if self.type in animal:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    setting: str
    brush_use: str
    surprise: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Brush:
    label: str
    phrase: str
    use: str
    surprise_use: str
    can_discern: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    brush: str
    surprise: str
    repetition: int
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "lane": Place(
        name="the lane",
        setting="by a little market lane",
        brush_use="brush the crumbs from the table",
        surprise="a kitten in the basket",
        affords={"haggle", "brush", "discern", "surprise"},
    ),
    "barn": Place(
        name="the barn",
        setting="near a quiet barn",
        brush_use="brush straw from the pony",
        surprise="a nest of sleepy chicks",
        affords={"haggle", "brush", "discern", "surprise"},
    ),
    "garden": Place(
        name="the garden",
        setting="behind a small garden wall",
        brush_use="brush the dust from the statue",
        surprise="a tiny bee house",
        affords={"haggle", "brush", "discern", "surprise"},
    ),
}

BRUSHES = {
    "table": Brush(
        label="scrub brush",
        phrase="a short scrub brush with a wooden handle",
        use="brush crumbs from the table",
        surprise_use="brush the dust from the surprise gift",
    ),
    "straw": Brush(
        label="soft brush",
        phrase="a soft brush with a round back",
        use="brush straw from the pony",
        surprise_use="brush the feathers from the nest box",
    ),
    "dust": Brush(
        label="fine brush",
        phrase="a fine brush wrapped in blue twine",
        use="brush dust from the statue",
        surprise_use="brush the pollen from the little hive",
    ),
}

HEROES = [
    ("fox", "fox", "swift", "curious"),
    ("hare", "hare", "small", "careful"),
    ("mouse", "mouse", "tiny", "busy"),
    ("crow", "crow", "black", "sharp-eyed"),
    ("cat", "cat", "striped", "proud"),
]

HELPERS = [
    ("merchant", "merchant", "patient"),
    ("grandmother", "grandmother", "kind"),
    ("farmer", "farmer", "steady"),
    ("owl", "owl", "wise"),
]

REPETITION_COUNTS = [2, 3, 4]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def introduce(world: World, hero: Entity, helper: Entity, brush: Entity) -> None:
    world.say(
        f"Once, in {world.place.setting}, there lived {hero.label}, "
        f"{_article(hero.type)} {hero.type} who tried to understand everything by watching it twice."
    )
    world.say(
        f"{helper.label} kept {brush.phrase}, and {hero.label} liked the way it looked in the sunlight."
    )


def haggle(world: World, hero: Entity, helper: Entity, brush: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.label} wanted the {brush.label}, but {helper.label} asked for a fair share first."
    )
    world.say(
        f"So {hero.label} and {helper.label} haggled kindly, back and forth, until the price felt small and fair."
    )


def discern(world: World, hero: Entity, brush: Entity, place: Place) -> None:
    hero.memes["discern"] = hero.memes.get("discern", 0) + 1
    world.say(
        f"{hero.label} looked again and tried to discern what the {brush.label} was really for."
    )
    world.say(
        f"At first, {hero.pronoun()} guessed wrong, because the brush looked useful for many small jobs."
    )


def repeat_attempts(world: World, hero: Entity, brush: Entity, place: Place, count: int) -> None:
    for i in range(count):
        hero.memes["repetition"] = hero.memes.get("repetition", 0) + 1
        if i == 0:
            world.say(
                f"Again {hero.label} tried to use the {brush.label} for {place.brush_use}, and again it seemed to fit."
            )
        else:
            world.say(
                f"Again and again {hero.label} tested the brush, because repeated tries helped {hero.pronoun()} notice the pattern."
            )


def surprise_turn(world: World, hero: Entity, helper: Entity, brush: Entity, place: Place) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    world.say(
        f"Then came a surprise: behind the basket, there was {place.surprise}."
    )
    world.say(
        f"{helper.label} laughed softly and said the brush was meant for that little surprise, not for the first thing {hero.label} had guessed."
    )


def resolution(world: World, hero: Entity, helper: Entity, brush: Entity, place: Place) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.label} brushed the surprise clean and smiled, because now {hero.pronoun()} could see the brush's true use."
    )
    world.say(
        f"And so {hero.label} learned a fable's lesson: a fair bargain helps, but patience and repetition help the eye discern the truth."
    )


# ---------------------------------------------------------------------------
# Q&A helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about {f["hero_name"]} who haggles for {f["brush_label"]} and learns to discern its use.',
        f"Tell a gentle story with repetition and surprise where {f['helper_name']} sells a brush and {f['hero_name']} discovers what it really does.",
        f'Write a child-friendly fable set {f["place_name"]} that includes haggle, discern, and brush.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who haggled for the brush in the story?",
            answer=f"{f['hero_name']} haggled with {f['helper_name']} until they agreed on a fair price.",
        ),
        QAItem(
            question=f"What did {f['hero_name']} need to discern about the brush?",
            answer=f"{f['hero_name']} needed to discern its true use, because it could do one small job at first and then reveal a better purpose.",
        ),
        QAItem(
            question=f"What surprise changed the story near the end?",
            answer=f"The surprise was {f['surprise_text']}, which showed that the brush had been waiting for that special job.",
        ),
        QAItem(
            question=f"How did repetition help {f['hero_name']}?",
            answer=f"By trying again and again, {f['hero_name']} noticed the pattern and learned what the brush was really for.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brush?",
            answer="A brush is a tool with bristles or hairs used for sweeping, cleaning, grooming, or painting small surfaces.",
        ),
        QAItem(
            question="What does it mean to haggle?",
            answer="To haggle means to talk about a price and try to agree on something fair.",
        ),
        QAItem(
            question="What does discern mean?",
            answer="To discern means to notice or understand something clearly after looking carefully.",
        ),
        QAItem(
            question="Why can repetition help someone learn?",
            answer="Repetition gives the mind another chance to notice patterns, remember details, and understand a task.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes a person stop, look closely, and react with curiosity or delight.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_fact(H).
helper(K) :- helper_fact(K).
brush(B) :- brush_fact(B).
place(P) :- place_fact(P).

can_haggle(H, K, B, P) :- hero(H), helper(K), brush(B), place(P),
                          available(P, haggle), available(P, brush), available(P, discern).

good_story(H, K, B, P) :- can_haggle(H, K, B, P), surprise_at(P, S), surprise_possible(B, S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        for feat in sorted(p.affords):
            lines.append(asp.fact("available", pid, feat))
        lines.append(asp.fact("surprise_at", pid, p.surprise))
    for bid, b in BRUSHES.items():
        lines.append(asp.fact("brush_fact", bid))
        lines.append(asp.fact("surprise_possible", bid, b.surprise_use))
    for hid, htype, _, _ in HEROES:
        lines.append(asp.fact("hero_fact", hid))
    for kid, _, _ in HELPERS:
        lines.append(asp.fact("helper_fact", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    asp_set = sorted(set(asp.atoms(model, "good_story")))
    py_set = sorted(set(valid_combos()))
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("clingo:", asp_set)
    print("python:", py_set)
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for hid, _, _, _ in HEROES:
            for kid, _, _ in HELPERS:
                for bid in BRUSHES:
                    combos.append((place, hid, kid, bid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld: haggle, discern, brush, surprise, repetition.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--brush", choices=BRUSHES.keys())
    ap.add_argument("--surprise", choices=["surprise"], default="surprise")
    ap.add_argument("--repetition", type=int, choices=REPETITION_COUNTS)
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
    place = args.place or rng.choice(list(PLACES.keys()))
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    brush = args.brush or rng.choice(list(BRUSHES.keys()))
    repetition = args.repetition or rng.choice(REPETITION_COUNTS)
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(place=place, hero=hero, helper=helper, brush=brush, surprise="surprise", repetition=repetition)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    brush_def = BRUSHES[params.brush]
    hero_type = next(t for i, t, _, _ in HEROES if i == params.hero)
    helper_type = next(t for i, t, _ in HELPERS if i == params.helper)
    hero = params.hero.capitalize()
    helper = params.helper.capitalize()
    world = World(place)
    world.add(Entity(id=params.hero, kind="character", type=hero_type, label=hero))
    world.add(Entity(id=params.helper, kind="character", type=helper_type, label=helper))
    world.add(Entity(id=params.brush, kind="thing", type="brush", label=brush_def.label, phrase=brush_def.phrase))
    world.facts = {
        "hero_name": hero,
        "helper_name": helper,
        "brush_label": brush_def.label,
        "place_name": place.name,
        "surprise_text": place.surprise,
    }

    introduce(world, world.get(params.hero), world.get(params.helper), world.get(params.brush))
    haggle(world, world.get(params.hero), world.get(params.helper), world.get(params.brush))
    discern(world, world.get(params.hero), world.get(params.brush), place)
    repeat_attempts(world, world.get(params.hero), world.get(params.brush), place, params.repetition)
    surprise_turn(world, world.get(params.hero), world.get(params.helper), world.get(params.brush), place)
    resolution(world, world.get(params.hero), world.get(params.helper), world.get(params.brush), place)

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
        print("\n--- world trace ---")
        for eid, ent in sample.world.entities.items():
            print(f"{eid}: type={ent.type} label={ent.label}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/4."))
        combos = sorted(set(asp.atoms(model, "good_story")))
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        seeds = [
            StoryParams(place=p, hero=h, helper=k, brush=b, surprise="surprise", repetition=r)
            for p in PLACES
            for h, _, _, _ in HEROES
            for k, _, _ in HELPERS
            for b in BRUSHES
            for r in REPETITION_COUNTS
            if h != k
        ]
        samples = [generate(p) for p in seeds]
    else:
        samples = []
        seen = set()
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
