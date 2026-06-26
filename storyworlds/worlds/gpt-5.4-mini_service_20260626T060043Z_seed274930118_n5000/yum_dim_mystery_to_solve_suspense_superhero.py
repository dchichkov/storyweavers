#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero mystery with suspense and a gentle
yum-dim clue.

Premise:
- A kid hero notices a strange yum-dim smell drifting through the city.
- Something sweet is missing, and the hero must solve the mystery before the
  town's big sunset parade starts.
- Suspense comes from clues, timing, and a risky search.

World model:
- Physical meters: scent, mess, glow, speed, tiredness, relief.
- Emotional memes: worry, courage, hope, pride, surprise.
- The story is driven by a short simulated chain:
  clue -> suspicion -> search -> reveal -> fix -> celebration.

The word "yum-dim" is used as a faint, mixed smell: yummy but dim, like a clue
that is almost, but not quite, obvious.
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
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Place:
    id: str
    name: str
    clue_source: str
    atmosphere: str
    affordance: str


@dataclass(frozen=True)
class HeroSpec:
    name: str
    role: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    costume: str


@dataclass(frozen=True)
class MysterySpec:
    id: str
    missing_item: str
    scent: str
    culprit: str
    hide_place: str
    fix: str
    result_image: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class World:
    place: Place
    hero: Entity
    sidekick: Entity
    mystery: MysterySpec
    culprit: Entity
    clue: Entity
    final_reveal: Optional[str] = None
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace_lines(self) -> list[str]:
        lines = []
        for ent in [self.hero, self.sidekick, self.culprit, self.clue]:
            m = {k: v for k, v in ent.meters.items() if v}
            e = {k: v for k, v in ent.memes.items() if v}
            lines.append(f"{ent.id}: kind={ent.kind} label={ent.label} meters={m} memes={e}")
        lines.append(f"final_reveal={self.final_reveal}")
        return lines


PLACES = {
    "rooftop": Place(
        id="rooftop",
        name="the moonlit rooftop",
        clue_source="a bakery vent beside the water tower",
        atmosphere="The night breeze slid over the rooftops like a quiet cape.",
        affordance="watch the whole city",
    ),
    "museum": Place(
        id="museum",
        name="the city museum",
        clue_source="a snack cart near the marble steps",
        atmosphere="The museum halls were hush-quiet, with shiny floors and big echoing rooms.",
        affordance="hide behind displays",
    ),
    "bridge": Place(
        id="bridge",
        name="the river bridge",
        clue_source="a lunch stand under the lamps",
        atmosphere="The bridge hummed with traffic, and the river glittered underneath.",
        affordance="see both banks",
    ),
}

HEROES = [
    HeroSpec("Nova", "hero", "she", "her", "her", "a bright red cape"),
    HeroSpec("Jet", "hero", "he", "him", "his", "a blue mask"),
    HeroSpec("Pip", "hero", "they", "them", "their", "a tiny silver hood"),
]

SIDEKICKS = [
    HeroSpec("Dot", "sidekick", "she", "her", "her", "a yellow backpack"),
    HeroSpec("Moss", "sidekick", "he", "him", "his", "green gloves"),
    HeroSpec("Blink", "sidekick", "they", "them", "their", "round goggles"),
]

MYSTERIES = {
    "missing_cake": MysterySpec(
        id="missing_cake",
        missing_item="the bakery's star cake",
        scent="yum-dim",
        culprit="a hungry raccoon",
        hide_place="behind the old chimney",
        fix="share the cake crumbs with the raccoon and return the rest",
        result_image="the cake box stood open and safe again beside the smiling baker",
    ),
    "missing_pies": MysterySpec(
        id="missing_pies",
        missing_item="three shiny berry pies",
        scent="yum-dim",
        culprit="a gusty little robot",
        hide_place="under a metal sign",
        fix="wind the robot's loose spring and carry the pies back in a tray",
        result_image="the pies were lined up like bright moons in the shop window",
    ),
    "missing_sandwiches": MysterySpec(
        id="missing_sandwiches",
        missing_item="the lunch cart's sandwiches",
        scent="yum-dim",
        culprit="a shy squirrel with sticky paws",
        hide_place="inside a leaf crate",
        fix="set out acorns for the squirrel and pack the sandwiches neatly again",
        result_image="the lunch cart looked full and cheerful under the lamps",
    ),
}

CURATED = [
    ("rooftop", "missing_cake"),
    ("museum", "missing_pies"),
    ("bridge", "missing_sandwiches"),
]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is valid when the place has a clue source and the mystery has a
% useful fix that resolves the missing item.

valid_story(P, M) :- place(P), mystery(M), clue_source(P), fixable(M).
"""  # The Python gate is authoritative; ASP mirrors the allowed registry pairs.


def asp_facts() -> str:
    import asp

    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("clue_source", pid))
        lines.append(asp.fact("affords", pid, p.affordance))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("fixable", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def python_valid_pairs() -> list[tuple[str, str]]:
    return sorted((p, m) for p in PLACES for m in MYSTERIES)


def asp_verify() -> int:
    py = set(python_valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("only in Python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")

    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]

    hero_spec = next((h for h in HEROES if h.name == params.name), None)
    if hero_spec is None:
        hero_spec = HEROES[0]
    sidekick = SIDEKICKS[0]

    hero = Entity(
        id=hero_spec.name,
        kind="character",
        label=hero_spec.role,
        meters={"speed": 1.0, "relief": 0.0},
        memes={"worry": 0.0, "courage": 1.0, "hope": 1.0, "pride": 0.0, "surprise": 0.0},
        flags={hero_spec.costume},
    )
    helper = Entity(
        id=sidekick.name,
        kind="character",
        label="sidekick",
        meters={"speed": 1.0},
        memes={"worry": 0.0, "hope": 1.0},
        flags={sidekick.costume},
    )
    culprit = Entity(
        id="culprit",
        kind="character",
        label=mystery.culprit,
        meters={"speed": 0.6, "mess": 0.0},
        memes={"worry": 0.8, "surprise": 0.0},
    )
    clue = Entity(
        id="clue",
        kind="thing",
        label=mystery.scent,
        meters={"scent": 0.2, "brightness": 0.1},
        memes={"mystery": 1.0},
    )

    world = World(place=place, hero=hero, sidekick=helper, mystery=mystery, culprit=culprit, clue=clue)
    return world


def _increase(entity: Entity, meter: str, amount: float) -> None:
    entity.meters[meter] = entity.meters.get(meter, 0.0) + amount


def _increase_mood(entity: Entity, meme: str, amount: float) -> None:
    entity.memes[meme] = entity.memes.get(meme, 0.0) + amount


def simulate(world: World) -> None:
    h = world.hero
    s = world.sidekick
    c = world.culprit
    m = world.mystery
    p = world.place

    world.say(f"{h.id} was a small superhero who loved solving city puzzles.")
    world.say(f"One evening, {p.name} waited under a quiet sky, and {p.atmosphere.lower()}")
    world.say(
        f"Then {h.id} caught a strange {m.scent} smell drifting by: "
        f"not quite sweet, not quite plain, just {m.scent} enough to make a mystery feel close."
    )
    _increase_mood(h, "worry", 1.0)
    _increase_mood(h, "hope", 0.5)
    world.facts["clue"] = m.scent

    world.para()
    world.say(
        f"At first, {h.id} thought the missing thing might be near the {p.clue_source}, "
        f"so {h.id} and {s.id} hurried there with careful steps."
    )
    _increase(h, "speed", 0.3)
    _increase(s, "speed", 0.2)
    _increase_mood(s, "hope", 0.3)
    world.say(
        f"The air felt suspenseful, because every corner could hide a clue, and every clue could lead to {m.missing_item}."
    )

    world.para()
    world.say(
        f"Behind a stack of boxes, they found tiny crumbs and a little bent label. "
        f"The crumbs smelled {m.scent}, which meant the mystery was real."
    )
    _increase(clue := world.clue, "brightness", 0.4)
    _increase_mood(h, "surprise", 0.5)
    _increase_mood(c, "worry", 0.2)
    world.facts["first_clue"] = "crumbs"

    world.say(
        f"{h.id} followed the crumbs slowly, because a good hero knows that rushing can hide the truth."
    )
    _increase(h, "speed", -0.1)
    _increase_mood(h, "courage", 0.4)

    world.para()
    world.say(
        f"The trail led to {m.hide_place}, where {c.label} was trying to tuck the missing {m.missing_item} away."
    )
    _increase_mood(c, "surprise", 1.0)
    _increase_mood(h, "pride", 0.5)
    world.facts["culprit_spotted"] = True

    world.say(
        f"{h.id} did not shout. Instead, {h.id} asked the right question and held up the clue like a tiny flashlight."
    )
    _increase(clue, "brightness", 0.3)
    _increase_mood(c, "worry", 0.5)

    world.para()
    world.say(
        f"The answer came fast: {c.label} had taken {m.missing_item} because it smelled too good to ignore."
    )
    world.say(
        f"But {h.id} saw the trembling paws and knew this was not a bad-villain story at all."
    )
    world.say(
        f"It was a hungry-and-hasty story, and that meant the fix could be kind."
    )

    world.para()
    world.say(
        f"So {h.id} chose {m.fix}. {s.id} helped hold the box steady while the city watched in suspense."
    )
    _increase_mood(h, "pride", 1.0)
    _increase_mood(s, "pride", 0.7)
    _increase(h, "relief", 1.0)
    _increase(s, "relief", 1.0)
    _increase(c, "worry", -0.6)
    world.final_reveal = m.result_image

    world.para()
    world.say(
        f"By the end, {m.result_image}, and the yum-dim mystery turned into a happy city grin."
    )
    world.say(
        f"{h.id} stood a little taller, because the best superhero endings are the ones that leave everyone safer and kinder."
    )
    _increase_mood(h, "pride", 0.5)
    _increase_mood(h, "hope", 0.5)
    world.facts.update(
        place=p.id,
        mystery=m.id,
        missing_item=m.missing_item,
        culprit=m.culprit,
        hide_place=m.hide_place,
        fix=m.fix,
        result_image=m.result_image,
        hero=h.id,
        sidekick=s.id,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero mystery story for a child where a hero notices a "{world.mystery.scent}" clue.',
        f"Tell a suspenseful but gentle story in {world.place.name} about {f['hero']} and {f['sidekick']} solving a missing {world.mystery.missing_item}.",
        f"Write a tiny story where the mystery clue smells {world.mystery.scent} and the ending is kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What strange clue did {f['hero']} notice first?",
            answer=f"{f['hero']} noticed a {world.mystery.scent} smell first. It felt only half-clear, which made the mystery suspenseful.",
        ),
        QAItem(
            question=f"Where did the clue lead {f['hero']} and {f['sidekick']}?",
            answer=f"It led them to {f['hide_place']}, where the missing {f['missing_item']} was being hidden.",
        ),
        QAItem(
            question=f"Who had taken the missing {f['missing_item']}?",
            answer=f"It was taken by {f['culprit']}, but the story showed that the reason was hunger, not cruelty.",
        ),
        QAItem(
            question=f"How did the heroes solve the mystery?",
            answer=f"They used the clue, asked careful questions, and chose {f['fix']}. That solved the mystery without turning it into a fight.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, {f['result_image']}, and the city felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small bit of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why can suspense make a story exciting?",
            answer="Suspense makes a story exciting because you wonder what will happen next.",
        ),
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero tries to help people, solve problems, and keep others safe.",
        ),
        QAItem(
            question="What does the word yum usually make people think of?",
            answer="Yum usually makes people think of tasty food or a nice smell from something delicious.",
        ),
        QAItem(
            question="Why might a mystery need a careful hero?",
            answer="A careful hero notices details, follows clues, and does not jump to the wrong answer too fast.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in PLACES for m in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid story matches the selected options.")

    place, mystery = rng.choice(combos)
    name = args.name or rng.choice([h.name for h in HEROES])
    return StoryParams(place=place, mystery=mystery, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
        print("\n--- trace ---")
        for line in sample.world.trace_lines():
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery story world with suspense and a yum-dim clue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name", choices=sorted({h.name for h in HEROES}))
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


def emit_json(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
    else:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))


def asp_verify_cli() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_cli())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (place, mystery) pairs:\n")
        for p, m in pairs:
            print(f"  {p:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, (place, mystery) in enumerate(CURATED):
            params = StoryParams(
                place=place,
                mystery=mystery,
                name=HEROES[i % len(HEROES)].name,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + attempts))
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story in seen:
                attempts += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            attempts += 1

    if args.json:
        emit_json(samples)
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
