#!/usr/bin/env python3
"""
trend_repetition_inner_monologue_mystery.py
==========================================

A small, standalone story world about a child noticing a strange trend,
repeating clues, and following an inner monologue toward a gentle mystery
resolution.

The seed idea:
- a child notices a pattern that keeps showing up
- the pattern feels suspicious at first
- the child thinks through the clues in their head
- the mystery turns out to have a simple, satisfying cause
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "brother", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = False
    details: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    physical: str
    repeating: bool = True
    kind: str = "trace"


@dataclass
class Cause:
    id: str
    label: str
    reveal: str
    solves: str
    mood_shift: str


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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hallway": Place(
        name="the hallway",
        indoors=True,
        details=["a row of lockers", "a squeaky floor tile", "a bulletin board"],
    ),
    "kitchen": Place(
        name="the kitchen",
        indoors=True,
        details=["a bright window", "a humming fridge", "a bowl on the table"],
    ),
    "garden": Place(
        name="the garden",
        indoors=False,
        details=["a stone path", "a little bench", "a watering can"],
    ),
}

HEROES = {
    "mila": ("Mila", "girl"),
    "noah": ("Noah", "boy"),
    "ada": ("Ada", "girl"),
    "ben": ("Ben", "boy"),
}

TRUTHS = {
    "keys": Cause(
        id="keys",
        label="a set of lost keys",
        reveal="the keys had been hanging on a nail all along",
        solves="the missing clink in the hallway",
        mood_shift="relief",
    ),
    "cat": Cause(
        id="cat",
        label="a sleepy cat",
        reveal="the cat had been knocking the spoon over with a sleepy paw",
        solves="the repeated clatter in the kitchen",
        mood_shift="laughter",
    ),
    "sprinkler": Cause(
        id="sprinkler",
        label="a garden sprinkler",
        reveal="the sprinkler timer had turned on at the same minute each day",
        solves="the repeating spray in the garden",
        mood_shift="wonder",
    ),
}

CLUES = {
    "hallway": [
        Clue(
            id="tink",
            label="a tiny tink",
            detail="The sound came again and again from near the lockers.",
            physical="tink",
        ),
        Clue(
            id="cold_brass",
            label="cold brass",
            detail="A cold brass shape flashed near a coat hook.",
            physical="brass",
        ),
    ],
    "kitchen": [
        Clue(
            id="clatter",
            label="a soft clatter",
            detail="The same little clatter happened three times in a row.",
            physical="clatter",
        ),
        Clue(
            id="crumbs",
            label="a trail of crumbs",
            detail="Tiny crumbs kept showing up beside the bowl.",
            physical="crumbs",
        ),
    ],
    "garden": [
        Clue(
            id="spray",
            label="a silver spray",
            detail="A silver spray kept flicking the same patch of dirt.",
            physical="spray",
        ),
        Clue(
            id="wet_steps",
            label="wet steps",
            detail="Wet steps kept appearing in the same neat line.",
            physical="wet",
        ),
    ],
}

TREND_WORDS = {
    "hallway": "trend",
    "kitchen": "pattern",
    "garden": "pattern",
}


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    clue: str
    cause: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def _monologue(world: World, hero: Entity, line: str) -> None:
    hero.memes["thinking"] = hero.memes.get("thinking", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} thought, \"{line}\"")


def _see_clue(world: World, hero: Entity, clue: Clue, count: int) -> None:
    world.say(
        f"{hero.id} noticed {clue.label} {count} time{'s' if count != 1 else ''}."
    )
    world.say(clue.detail)
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0.0) + 1
    hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1


def _repeat_trend(world: World, hero: Entity, clue: Clue, place: Place) -> None:
    trend_word = TREND_WORDS[place.name.split()[-1]] if place.name.split()[-1] in TREND_WORDS else "trend"
    world.say(
        f"The little {trend_word} kept repeating, and that made {hero.id} look twice."
    )


def _resolve(world: World, hero: Entity, cause: Cause) -> None:
    hero.memes["unease"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"Then {hero.id} found out {cause.reveal}."
    )
    world.say(
        f"That explained {cause.solves}, and the mystery felt smaller at once."
    )
    world.say(
        f"{hero.id} smiled in {cause.mood_shift} and walked away with a clear head."
    )


def tell(place: Place, hero_name: str, clue_id: str, cause_id: str) -> World:
    world = World(place)
    hero_label, hero_type = HEROES[hero_name]
    hero = world.add(Entity(id=hero_label, kind="character", type=hero_type))
    clue = CLUES[place.name.split()[-1]][0] if clue_id not in {c.id for c in CLUES[place.name.split()[-1]]} else next(c for c in CLUES[place.name.split()[-1]] if c.id == clue_id)
    cause = TRUTHS[cause_id]

    world.facts.update(hero=hero, clue=clue, cause=cause, place=place)

    # Act 1: the repeated clue.
    world.say(f"{hero.id} was in {place.name} when something odd caught {hero.pronoun('possessive')} eye.")
    world.say(
        f"It was not just once. It happened again, and again, like a tiny {TREND_WORDS.get(place.name.split()[-1], 'trend')}."
    )
    _see_clue(world, hero, clue, 1)
    world.say(
        f"{hero.id} watched for the same sign a second time, because the first time could have been nothing."
    )
    _see_clue(world, hero, clue, 2)

    # Act 2: inner monologue and suspicion.
    world.para()
    _monologue(world, hero, "Something is repeating. That means it has a reason.")
    _monologue(world, hero, "A clue that comes back twice is not an accident anymore.")
    world.say(
        f"{hero.id} looked around {place.name} and tried to match the clue with the details there."
    )
    world.say(f"The {', '.join(place.details[:-1])} and the {place.details[-1]} did not explain it yet.")

    # Act 3: the reveal.
    world.para()
    _resolve(world, hero, cause)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    cause: Cause = f["cause"]
    place: Place = f["place"]
    return [
        f'Write a short mystery story for a child where a clue keeps repeating in {place.name}.',
        f"Tell a gentle story about {hero.id} noticing {clue.label} more than once and thinking it through.",
        f"Write a simple story with an inner monologue, a repeated clue, and a surprising but ordinary explanation.",
        f"Make the word trend feel like part of a small mystery in {place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    cause: Cause = f["cause"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} notice repeating in {place.name}?",
            answer=f"{hero.id} noticed {clue.label} repeating in {place.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} think in {hero.pronoun('possessive')} head about the repeating clue?",
            answer="The inner monologue said that the clue must have a reason, and that it was probably not an accident.",
        ),
        QAItem(
            question=f"What turned out to be the cause of the mystery?",
            answer=f"It turned out to be {cause.label}.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended when {cause.reveal}, which explained the repeated clue and brought relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    clue: Clue = f["clue"]
    qa = [
        QAItem(
            question="What is a trend?",
            answer="A trend is something that keeps showing up again and again for a while.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a small piece of information that can help someone figure out what happened.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of a person's thoughts in their own head.",
        ),
    ]
    if place.name == "the kitchen":
        qa.append(
            QAItem(
                question="What is a clatter?",
                answer="A clatter is a sharp, noisy sound made by things hitting or falling together.",
            )
        )
    elif place.name == "the garden":
        qa.append(
            QAItem(
                question="What is a sprinkler?",
                answer="A sprinkler is a tool that sprays water over grass or plants.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What are keys for?",
                answer="Keys are used to lock and unlock things like doors or boxes.",
            )
        )
    return qa


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

repeat(clue) :- clue(_).

valid(Place, Clue, Cause) :- place(Place), clue_in(Place, Clue), cause_for(Place, Cause).

valid_story(Place, Clue, Cause, Hero) :- valid(Place, Clue, Cause), hero(Hero).

mystery_like(Place, Clue) :- clue_in(Place, Clue), repeats(Clue).
trend_like(Place) :- place(Place), clue_in(Place, _), repeats(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
    for hid, (label, _gender) in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("hero_label", hid, label))
    for pid, clues in CLUES.items():
        for clue in clues:
            lines.append(asp.fact("clue", clue.id))
            lines.append(asp.fact("clue_in", pid, clue.id))
            if clue.repeating:
                lines.append(asp.fact("repeats", clue.id))
    for cid in TRUTHS:
        lines.append(asp.fact("cause", cid))
        for pid in PLACES:
            lines.append(asp.fact("cause_for", pid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Constraint gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for hid in HEROES:
            for cid in TRUTHS:
                # One clue per place, one cause per place; all combos valid here.
                combos.append((pid, hid, cid))
    return combos


def explain_rejection() -> str:
    return "(No story: the options do not form a coherent mystery.)"


# ---------------------------------------------------------------------------
# Params resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery story world: a child notices a repeating trend, thinks it through, and finds the cause."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--clue")
    ap.add_argument("--cause", choices=TRUTHS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.hero is None or c[1] == args.hero)
        and (args.cause is None or c[2] == args.cause)
    ]
    if not filtered:
        raise StoryError(explain_rejection())
    place, hero, cause = rng.choice(sorted(filtered))
    clue_choices = CLUES[place]
    clue = args.clue if args.clue in {c.id for c in clue_choices} else rng.choice(clue_choices).id
    return StoryParams(place=place, hero=hero, clue=clue, cause=cause)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero, params.clue, params.cause)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hallway", hero="mila", clue="tink", cause="keys"),
    StoryParams(place="kitchen", hero="noah", clue="clatter", cause="cat"),
    StoryParams(place="garden", hero="ada", clue="spray", cause="sprinkler"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible (place, hero, cause) combos ({len(stories)} with hero):\n")
        for place, hero, cause in combos:
            print(f"  {place:8} {hero:8} {cause:10}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.hero} / {p.cause}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
