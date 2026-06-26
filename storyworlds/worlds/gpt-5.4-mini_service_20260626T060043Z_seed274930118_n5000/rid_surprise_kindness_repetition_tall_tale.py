#!/usr/bin/env python3
"""
Tall-tale story world: rid a homestead of a nuisance with surprise, kindness,
and repetition.

Premise seed:
A tiny town is bothered by a rid of crows? Better: a "rid" word is kept as the
core prompt and becomes the repeated action of ridding a barn of a lively,
sticky troublemaker. The hero tries clever tricks, but the real turn comes from
surprise kindness and repeated, patient effort.

This world models:
- physical meters: clutter, distance, carried stuff, neatness, weight
- emotional memes: worry, courage, surprise, kindness, delight, trust

The story reads like a tall tale with big, concrete images and a strong ending.
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

TALL_TALE_OPENERS = [
    "mighty",
    "lanky",
    "legendary",
    "dusty",
    "sun-bright",
    "whistling",
]

PLACES = {
    "barn": "a red barn with a roof that clattered in the wind",
    "shed": "a little shed with a leaning door and a squeaky latch",
    "orchard": "an orchard with apple trees as crooked as old fingers",
}

NUSANCES = {
    "goose": "a goose with a long neck and a louder-than-thunder honk",
    "goat": "a goat with whiskers like broom straw and a talent for trouble",
    "raccoon": "a raccoon with masked eyes and sticky paws",
}

TOOLS = {
    "bucket": "a tin bucket that rang like a bell",
    "lantern": "a lantern that glowed like a jar of trapped moonlight",
    "rope": "a rope as long as a train of laundry",
}

# ---------------------------------------------------------------------------
# Shared entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.meters.get("gender_code", 0.0)
        if gender == 1.0:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == 2.0:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    place_desc: str
    nuisance: str
    nuisance_desc: str
    tool: str
    tool_desc: str
    hero: Entity
    helper: Entity
    nuisance_ent: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        return copy.deepcopy(self)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    nuisance: str
    tool: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about rid, surprise, kindness, and repetition.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--nuisance", choices=sorted(NUSANCES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n in NUSANCES:
        lines.append(asp.fact("nuisance", n))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    # compatibility facts: every nuisance can be rid with the right kind of help
    lines.append(asp.fact("can_rid", "barn", "goose", "bucket"))
    lines.append(asp.fact("can_rid", "shed", "raccoon", "lantern"))
    lines.append(asp.fact("can_rid", "orchard", "goat", "rope"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,N,T) :- can_rid(P,N,T).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python only:", sorted(py - cl))
    print(" asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("barn", "goose", "bucket"),
        ("shed", "raccoon", "lantern"),
        ("orchard", "goat", "rope"),
    ]


def explain_rejection(place: str, nuisance: str, tool: str) -> str:
    return (
        f"(No story: a {tool} does not honestly help rid {PLACES[place]} of "
        f"{NUSANCES[nuisance]}. Try a compatible pair from the world's little catalog.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    if (params.place, params.nuisance, params.tool) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.nuisance, params.tool))

    hero = Entity(
        id=params.hero_name,
        kind="character",
        label=params.hero_name,
        meters={"gender_code": 0.0, "clutter": 0.0, "distance": 0.0, "carried": 0.0},
        memes={"worry": 1.0, "courage": 0.0, "surprise": 0.0, "kindness": 0.0, "delight": 0.0, "trust": 0.0},
    )
    helper = Entity(
        id=params.helper_name,
        kind="character",
        label=params.helper_name,
        meters={"gender_code": 0.0, "clutter": 0.0, "distance": 0.0, "carried": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "surprise": 0.0, "kindness": 1.0, "delight": 0.0, "trust": 0.0},
    )
    nuisance_ent = Entity(
        id=params.nuisance,
        kind="thing",
        label=params.nuisance,
        phrase=NUSANCES[params.nuisance],
        meters={"restless": 1.0, "clutter": 2.0, "weight": 1.0},
        memes={"mischief": 2.0},
    )
    return World(
        place=params.place,
        place_desc=PLACES[params.place],
        nuisance=params.nuisance,
        nuisance_desc=NUSANCES[params.nuisance],
        tool=params.tool,
        tool_desc=TOOLS[params.tool],
        hero=hero,
        helper=helper,
        nuisance_ent=nuisance_ent,
    )


def narrate(world: World) -> None:
    hero, helper, nuisance = world.hero, world.helper, world.nuisance_ent
    opener = random.choice(TALL_TALE_OPENERS)

    world.say(
        f"{hero.label} was a {opener} sort of soul who could spot trouble from across {world.place}."
    )
    world.say(
        f"One morning in {world.place_desc}, {hero.label} and {helper.label} found {world.nuisance_desc} causing a rumpus."
    )
    world.say(
        f"{hero.label} declared it was time to rid the place of the {nuisance.label}, and {helper.label} nodded kindly."
    )

    # Surprise: the nuisance responds in an unexpected way.
    world.para()
    hero.memes["surprise"] += 1
    nuisance.meters["clutter"] += 1
    world.say(
        f"But just then, the {nuisance.label} tipped the {world.tool_desc} over with a sneeze-big bounce, "
        f"and {hero.label} gave a great blink of surprise."
    )

    # Repetition: repeated attempts, each one smaller and gentler.
    world.say(
        f"{helper.label} did not scold. Instead, {helper.label} offered a kind hand and said, "
        f'"Let us try again, nice and slow."'
    )
    world.facts["tries"] = 0
    for i in range(3):
        world.facts["tries"] += 1
        hero.meters["distance"] += 1
        hero.memes["kindness"] += 1
        helper.memes["kindness"] += 1
        nuisance.meters["clutter"] = max(0.0, nuisance.meters["clutter"] - 1.0)
        nuisance.meters["weight"] = max(0.0, nuisance.meters["weight"] - 0.3)
        if i == 0:
            world.say(
                f"First {hero.label} lifted the {world.tool} and the {nuisance.label} scampered away like a bad joke."
            )
        elif i == 1:
            world.say(
                f"Then {helper.label} brought the {world.tool} back, and together they tried again, steady as porch boards."
            )
        else:
            world.say(
                f"At last they repeated the trick one more time, and the {nuisance.label} stopped its rumpus and sat still."
            )

    # Resolution through kindness, not force.
    world.para()
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    hero.memes["delight"] += 1
    helper.memes["delight"] += 1
    nuisance.meters["clutter"] = 0.0
    nuisance.memes["mischief"] = 0.0
    world.say(
        f"In the end, {hero.label} did rid {world.place} of the trouble, not by being fierce, but by being kind enough to keep trying."
    )
    world.say(
        f"The {world.tool} stood by the door, the {nuisance.label} was gone, and {world.place} looked neat as a button in a king's coat."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        nuisance=nuisance,
        place=world.place,
        tool=world.tool,
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Registries and selection
# ---------------------------------------------------------------------------
HEROES = ["Mabel", "Hank", "Ivy", "Jasper", "Pearl", "Cleo"]
HELPERS = ["Nell", "Otis", "June", "Walt", "Mina", "Ruth"]


def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.nuisance is None or c[1] == args.nuisance)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, nuisance, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        nuisance=nuisance,
        tool=tool,
        hero_name=args.hero_name or rng.choice(HEROES),
        helper_name=args.helper_name or rng.choice(HELPERS),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a tall tale for young children about a hero trying to rid {world.place} of a troublesome {world.nuisance}, using the word "rid".',
        f"Tell a funny, gentle story where {world.hero.label} and {world.helper.label} keep trying again until the {world.nuisance} is gone.",
        f"Write a story with surprise, kindness, and repetition that ends with {world.place} all neat and calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who tried to rid {world.place} of the {world.nuisance}?",
            answer=f"{world.hero.label} tried to rid {world.place} of the {world.nuisance}, and {world.helper.label} helped kindly.",
        ),
        QAItem(
            question=f"What surprised {world.hero.label} during the story?",
            answer=f"The {world.nuisance} surprised {world.hero.label} by tipping over the {world.tool} and making a bigger fuss than expected.",
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer=f"It got solved through kindness and repetition: they kept trying again with the {world.tool} until the {world.nuisance} stopped causing trouble.",
        ),
        QAItem(
            question=f"What did the place look like at the end?",
            answer=f"At the end, {world.place} was neat and calm, with the nuisance gone and the {world.tool} resting by the door.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to rid something of a problem?",
            answer="To rid something of a problem means to remove it so the trouble is gone.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, and being gentle instead of hurtful.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing something again and again, often to learn or finish a job.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story with big, playful exaggeration that still makes sense and is fun to hear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = [
        "--- world trace ---",
        f"place: {world.place}",
        f"nuisance: {world.nuisance}",
        f"tool: {world.tool}",
    ]
    for e in [world.hero, world.helper, world.nuisance_ent]:
        bits.append(
            f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(bits)


CURATED = [
    StoryParams("barn", "goose", "bucket", "Mabel", "Nell"),
    StoryParams("shed", "raccoon", "lantern", "Hank", "Otis"),
    StoryParams("orchard", "goat", "rope", "Ivy", "June"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    narrate(world)
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_program_text(show: str) -> str:
    return f"{asp_facts_text()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_text("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_asp_valid_combos() -> list[tuple]:
    return asp_valid_combos()


def asp_show_program() -> str:
    return asp_program_text("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
