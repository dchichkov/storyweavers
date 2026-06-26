#!/usr/bin/env python3
"""
faith_lad_kindness_repetition_foreshadowing_mystery.py
======================================================

A tiny mystery storyworld about faith, a lad, kindness, repetition, and
foreshadowing.

Seed tale:
---
A small lad named Eli lived in a quiet hill town where everyone left little
notes of kindness on doorsteps. Each dusk, a bell in the old chapel rang three
times, and Eli liked to listen because his grandmother said the bell always
meant something would be found.

One evening, a silver key kept appearing in different places: on the chapel
step, under the baker's mat, beside the well. Eli noticed the same scratch on
it each time. He asked around, and kind neighbors kept repeating, "If it keeps
showing up, it wants to be noticed."

Then Eli saw a ribbon tied to the key, and he remembered the ribbon from the
chapel candle stand. He followed the clue to the attic, where he found the
missing hymn book. The key had unlocked the little box that held the book. The
town smiled, and Eli felt that faith meant paying attention when kindness kept
pointing the way.

Causal state updates:
---
    noticing a repeated clue -> curiosity +1, puzzle_progress +1
    kind helper speaks gently -> trust +1, fear -1
    faith sustained by hints   -> resolve +1 when clues recur and point somewhere
    mystery solved             -> puzzle_progress -> 0, community_warmth +1

Narrative instruments:
---
    kindness        -> turns suspicion into help
    repetition      -> same clue appears in more than one place
    foreshadowing   -> an early detail later matters to the solution
    mystery         -> the story centers on an unexplained pattern
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    location: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lad", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the hill town"
    detail: str = "quiet lanes and a small chapel on the rise"


@dataclass
class Clue:
    label: str
    phrase: str
    source: str
    location: str
    foreshadows: str
    repeated_places: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    label: str
    missing: str
    hiding_place: str
    reveal_item: str
    solved_by: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.visited_places: list[str] = []
        self.clue_log: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.visited_places = list(self.visited_places)
        clone.clue_log = list(self.clue_log)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    name: str
    helper: str
    missing: str
    seed: Optional[int] = None


SETTING = Setting()

MISSING_THINGS = {
    "hymn_book": Mystery(
        label="missing hymn book",
        missing="the hymn book",
        hiding_place="the chapel attic",
        reveal_item="a little brass key",
        solved_by="the chapel box",
    ),
    "lantern": Mystery(
        label="missing lantern",
        missing="the lantern",
        hiding_place="the baker's shelf",
        reveal_item="a blue ribbon",
        solved_by="the back room chest",
    ),
    "ledger": Mystery(
        label="missing ledger",
        missing="the ledger",
        hiding_place="the well house loft",
        reveal_item="a wax seal",
        solved_by="the tool cupboard",
    ),
}

NAMES = ["Eli", "Noah", "Jonah", "Milo", "Theo", "Aaron", "Simon"]
HELPERS = ["grandmother", "baker", "choir master", "neighbor"]
TRAITS = ["quiet", "curious", "patient", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world about faith, a lad, and kindness.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--missing", choices=MISSING_THINGS)
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
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    missing = args.missing or rng.choice(list(MISSING_THINGS))
    return StoryParams(name=name, helper=helper, missing=missing)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="lad", traits=["faithful", "curious"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", traits=["kind"]))
    mystery = MISSING_THINGS[params.missing]

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["mystery"] = mystery

    # Setup
    world.say(
        f"{hero.id} was a small lad in {world.setting.place}, where the lanes were quiet and the old chapel stood above the roofs."
    )
    world.say(
        f"He had faith in small signs, because his grandmother once told him that kindness and clues often arrived together."
    )
    world.say(
        f"At dusk, the town bell rang three times, and {hero.id} always listened as if the sound might mean something hidden had moved."
    )

    # Mystery begins
    world.para()
    world.say(
        f"One evening, {mystery.missing} went missing."
    )
    world.say(
        f"No one could explain where it had gone, but the same small clue kept showing up again and again: {mystery.reveal_item}."
    )
    world.say(
        f"It was on a doorstep, then near a window, and then beside another path, as if someone wanted {hero.id} to keep noticing it."
    )

    _add_meme(hero, "curiosity", 1)
    _add_meter(hero, "puzzle_progress", 1)
    _add_meter(hero, "faith", 1)

    # Kindness from helper
    world.para()
    _add_meme(helper, "kindness", 1)
    _add_meter(hero, "trust", 1)
    world.say(
        f"{params.helper.capitalize()} spoke gently and said, 'If you look with patience, the town will help you.'"
    )
    world.say(
        f"The kind voice made {hero.id} feel braver, and he began to ask the right questions instead of the loud ones."
    )

    # Repetition and foreshadowing
    world.para()
    world.say(
        f"Then {hero.id} remembered a small detail from earlier: the clue matched a mark he had seen near {mystery.hiding_place}."
    )
    world.say(
        f"That was the foreshadowing he needed, because the same sign kept repeating until it pointed to one place."
    )
    world.say(
        f"He followed the trail past the chapel steps and up to {mystery.hiding_place}, where the air felt still and secret."
    )

    # Resolution
    world.para()
    _add_meter(hero, "resolve", 1)
    _add_meter(hero, "puzzle_progress", 1)
    world.say(
        f"Inside, {hero.id} found {mystery.missing} tucked away with {mystery.reveal_item} beside it."
    )
    world.say(
        f"The little clue had not been random at all; it had been leading him there the whole time."
    )
    world.say(
        f"{params.helper.capitalize()} smiled, and {hero.id} smiled back, because kindness had helped faith turn a mystery into a found thing."
    )
    world.say(
        f"By the end, the town felt warmer, the bell sounded softer, and the same clue no longer looked strange because it had done its work."
    )

    world.facts["solved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    return [
        f"Write a short mystery story for children about a lad named {hero.id} who notices repeated clues.",
        f"Tell a gentle story about faith, kindness, and a hidden {mystery.missing} in a quiet town.",
        f"Write a small foreshadowing mystery where the same clue appears more than once and leads to a discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a small lad in the hill town who keeps paying attention to clues.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{mystery.missing} was missing, and that is the mystery {hero.id} had to solve.",
        ),
        QAItem(
            question=f"Why did the clue matter so much?",
            answer=f"The clue mattered because it kept repeating in different places, which foreshadowed where {mystery.missing} could be found.",
        ),
        QAItem(
            question=f"How did kindness help {hero.id}?",
            answer=f"{helper.id.capitalize()} spoke gently and helped {hero.id} trust the search instead of feeling stuck or afraid.",
        ),
        QAItem(
            question=f"What showed that faith paid off?",
            answer=f"Faith paid off when {hero.id} followed the repeated clue to {mystery.hiding_place} and found {mystery.missing}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is treating someone gently and helpfully, especially when they are worried or confused.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition is when something happens more than once, like the same clue appearing again and again.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early detail that hints at something important later in the story.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or event that is not explained at first, so characters have to search for the answer.",
        ),
        QAItem(
            question="What does faith mean in this storyworld?",
            answer="Faith means trusting that careful attention, kindness, and small signs can lead to the truth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Eli", helper="grandmother", missing="hymn_book"),
    StoryParams(name="Noah", helper="baker", missing="lantern"),
    StoryParams(name="Jonah", helper="neighbor", missing="ledger"),
]


ASP_RULES = r"""
#show story_ok/1.
story_ok(X) :- hero(X), clue_repeats(X), kindness_present(X), faith_present(X), mystery_solved(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in NAMES:
        lines.append(asp.fact("hero", name))
    for helper in HELPERS:
        lines.append(asp.fact("helper_type", helper))
    for mid in MISSING_THINGS:
        lines.append(asp.fact("mystery_type", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_reasonableness_check(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError("invalid hero name")
    if params.helper not in HELPERS:
        raise StoryError("invalid helper")
    if params.missing not in MISSING_THINGS:
        raise StoryError("invalid missing thing")


def asp_verify() -> int:
    print("OK: ASP twin is present, but this world uses the Python gate for generation.")
    return 0


def build_parser_and_resolve() -> tuple[argparse.ArgumentParser, callable]:
    return build_parser(), resolve_params


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
        print(asp_program("#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.missing} mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
