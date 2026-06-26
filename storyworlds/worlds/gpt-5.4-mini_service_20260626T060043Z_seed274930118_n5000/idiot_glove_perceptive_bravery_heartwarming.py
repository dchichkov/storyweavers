#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/idiot_glove_perceptive_bravery_heartwarming.py
===============================================================================================================

A small heartwarming story world about a child who is misunderstood, a lost glove,
and the brave moment when a perceptive helper notices what really matters.

Premise:
- A child is called an idiot for dropping or misplacing a glove.
- The child feels hurt and wants to hide.
- A perceptive friend notices the glove is important because it keeps a tiny bird,
  kitten, or cold hand safe.
- Bravery appears when someone speaks kindly, returns the glove, and stands up to
  the mean word.
- The ending proves the change by showing the glove where it belongs and the child
  feeling seen.

This file is standalone: it defines the world model, registries, story generation,
QA, CLI, and an inline ASP twin for the reasonableness gate.
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
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    supports: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    protects: set[str] = field(default_factory=set)
    warms: set[str] = field(default_factory=set)
    plural: bool = False
    worn_part: str = ""
    empathy_note: str = ""


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    risk: str
    harms: str
    prompt_word: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "schoolyard": Place("schoolyard", "the schoolyard", indoors=False, supports={"play", "walk", "share"}),
    "bus_stop": Place("bus_stop", "the bus stop", indoors=False, supports={"wait", "share"}),
    "porch": Place("porch", "the porch", indoors=False, supports={"wait", "share"}),
    "library": Place("library", "the library corner", indoors=True, supports={"read", "share"}),
}

PROBLEMS = {
    "wind": Problem(
        id="wind",
        verb="reach for the fluttering paper",
        gerund="chasing the fluttering paper",
        risk="the cold breeze",
        harms="the little hand would get chilled",
        prompt_word="wind",
        tags={"cold", "breeze"},
    ),
    "rain": Problem(
        id="rain",
        verb="run after the puddle-splashing leaf",
        gerund="splashing through the rain",
        risk="the wet weather",
        harms="the hand would get soaked",
        prompt_word="rain",
        tags={"wet", "weather"},
    ),
    "bite": Problem(
        id="bite",
        verb="carefully pet the shy kitten",
        gerund="petting the shy kitten",
        risk="the kitten's tiny scratch",
        harms="the little hand would need a soft shield",
        prompt_word="kitten",
        tags={"animal", "gentle"},
    ),
}

ITEMS = {
    "mitten": Item(
        id="mitten",
        label="glove",
        phrase="a warm red glove",
        type="glove",
        protects={"cold", "wind"},
        warms={"hand"},
        empathy_note="a warm glove for the cold little hand",
        worn_part="hand",
    ),
    "mittens": Item(
        id="mittens",
        label="gloves",
        phrase="a pair of wool mittens",
        type="gloves",
        plural=True,
        protects={"cold", "wind"},
        warms={"hand"},
        empathy_note="a pair of gloves that keep both hands warm",
        worn_part="hands",
    ),
    "rain_glove": Item(
        id="rain_glove",
        label="rain glove",
        phrase="a bright rain glove",
        type="glove",
        protects={"wet"},
        warms={"hand"},
        empathy_note="a glove that helps when the day is wet",
        worn_part="hand",
    ),
    "kitten_mitt": Item(
        id="kitten_mitt",
        label="soft glove",
        phrase="a soft little glove",
        type="glove",
        protects={"gentle"},
        warms={"hand"},
        empathy_note="a soft glove for careful petting",
        worn_part="hand",
    ),
}

# Bravery is not loud; it is a small but real choice.
BRAVERY_LEVEL = 1.0

NAMES = ["Mina", "Owen", "Lila", "Noah", "Iris", "Theo", "Ruby", "Eli"]
FRIEND_NAMES = ["Pip", "June", "Toby", "Nia", "Mara", "Ben"]
TRAITS = ["kind", "curious", "quiet", "careful", "bright", "gentle"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    item: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------
def reasonableness_gate(problem: Problem, item: Item, place: Place) -> bool:
    if "glove" not in item.type:
        return False
    if problem.id == "wind" and "cold" in item.protects:
        return True
    if problem.id == "rain" and "wet" in item.protects:
        return True
    if problem.id == "bite" and "gentle" in item.protects:
        return True
    return False


def explain_rejection(problem: Problem, item: Item) -> str:
    return (
        f"(No story: {item.label} does not honestly fit {problem.gerund}. "
        f"The brave fix must actually protect the thing at risk.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for pid, problem in PROBLEMS.items():
            for iid, item in ITEMS.items():
                if reasonableness_gate(problem, item, place):
                    combos.append((place_id, pid, iid))
    return combos


def choose_item(problem: Problem) -> Item:
    for item in ITEMS.values():
        if reasonableness_gate(problem, item, PLACES["schoolyard"]):
            return item
    raise StoryError("No compatible item exists for this problem.")


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    item_def = ITEMS[params.item]

    world = World(place)
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["item_def"] = item_def

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Lila", "Iris", "Ruby"} else "boy",
        meters={"heart": 0.0},
        memes={"hurt": 0.0, "bravery": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="girl" if params.friend in {"June", "Nia", "Mara"} else "boy",
        meters={"heart": 0.0},
        memes={"care": 0.0, "bravery": 0.0, "perceptive": 0.0},
    ))
    item = world.add(Entity(
        id="glove",
        kind="thing",
        type=item_def.type,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=hero.id,
        plural=item_def.plural,
    ))

    # Setup
    world.say(
        f"{hero.id} was a {params.trait} child who loved carrying {item.phrase} everywhere."
    )
    world.say(
        f"{hero.id} thought the glove was small, but it made the day feel safer."
    )
    world.para()

    # Conflict
    world.say(
        f"At {place.label}, {hero.id} tried to {problem.verb}, but the glove slipped from {hero.pronoun('possessive')} hand."
    )
    hero.memes["hurt"] += 1.0
    world.say(
        f"A mean voice called {hero.id} an idiot, and that word landed hard."
    )
    hero.memes["hurt"] += 1.0
    world.say(
        f"{hero.id} looked down, wishing the ground could swallow the mistake."
    )
    world.para()

    # Perceptive turn
    friend.memes["perceptive"] += 1.0
    world.say(
        f"But {friend.id} was perceptive and noticed something important right away."
    )
    world.say(
        f"The glove was not just a glove; it matched {problem.risk} and kept the little hand from getting hurt."
    )
    world.say(
        f"{friend.id} picked it up before it could blow away and said, \"That glove matters.\""
    )
    world.para()

    # Bravery and resolution
    friend.memes["bravery"] += 1.0
    hero.memes["bravery"] += 1.0
    hero.memes["relief"] += 1.0
    world.say(
        f"Then {friend.id} showed bravery and answered the mean word with a calm, steady voice."
    )
    world.say(
        f"\"You don't have to be cruel,\" {friend.id} said. \"{hero.id} just lost a glove, and anyone could make that mistake.\""
    )
    world.say(
        f"{hero.id} blinked, then took the glove back with a small smile."
    )
    world.say(
        f"By the end, {hero.id} was wearing {item.phrase} again, the wind felt less sharp, and the schoolyard seemed kinder."
    )
    world.say(
        f"The glove stayed where it belonged, and {hero.id} walked home feeling seen instead of silly."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        place_id=params.place,
        problem_id=params.problem,
        item_id=params.item,
        brave=True,
        perceptive=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    item = f["item_def"]
    place = f["place"]
    return [
        f'Write a heartwarming story for a young child that includes the word "glove" and the feeling of bravery.',
        f"Tell a gentle story where {hero.id} loses {item.label} at {place.label}, a perceptive friend notices why it matters, and the hurt is repaired.",
        f"Write a short story about someone being called an idiot, but the ending should be warm, kind, and brave.",
        f"Tell a story where {friend.id} is perceptive enough to notice how {problem.prompt_word} changes the meaning of {item.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    item = f["item"]
    place = f["place"]

    return [
        QAItem(
            question=f"Who lost the glove at {place.label}?",
            answer=f"{hero.id} lost the glove while trying to {problem.verb}.",
        ),
        QAItem(
            question=f"Why was {friend.id} called perceptive in the story?",
            answer=f"{friend.id} was perceptive because {friend.id} noticed right away that the glove really mattered for {problem.harms}.",
        ),
        QAItem(
            question="How did the story show bravery?",
            answer=f"It showed bravery when {friend.id} stood up to the mean word and spoke kindly for {hero.id}.",
        ),
        QAItem(
            question=f"What happened to the glove by the end?",
            answer=f"By the end, the glove was back on {hero.id}'s hand, and it helped the day feel safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem = f["problem"]
    item = f["item_def"]
    out = [
        QAItem(
            question="What is a glove for?",
            answer="A glove helps keep a hand warm or protected from cold, wet weather, or rough things.",
        ),
        QAItem(
            question="What does it mean to be perceptive?",
            answer="To be perceptive means to notice important things quickly and clearly.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel nervous or afraid.",
        ),
    ]
    if problem.id == "wind":
        out.append(QAItem(
            question="Why do gloves help on a windy day?",
            answer="Gloves help on a windy day because they keep hands warmer when cold air blows around.",
        ))
    elif problem.id == "rain":
        out.append(QAItem(
            question="Why do gloves help in wet weather?",
            answer="Gloves can help in wet weather because they keep hands from getting soaked and chilly.",
        ))
    else:
        out.append(QAItem(
            question="Why do gentle gloves matter with a shy kitten?",
            answer="Gentle gloves matter because they help a hand stay soft and careful instead of scratchy.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A glove is a compatible fix only if it protects the kind of risk the problem creates.
compatible(P, I) :- problem(P), item(I), problem_risk(P, R), item_protects(I, R).

valid_story(Place, P, I) :- place(Place), problem(P), item(I), supports(Place, P), compatible(P, I).

#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(place.supports):
            lines.append(asp.fact("supports", pid, s))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_risk", pid, prob.id if prob.id != "bite" else "gentle"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for p in sorted(item.protects):
            lines.append(asp.fact("item_protects", iid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    item: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming glove story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.problem and args.item:
        if not reasonableness_gate(PROBLEMS[args.problem], ITEMS[args.item], PLACES[args.place or "schoolyard"]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], ITEMS[args.item]))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.item is None or c[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, item = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        item=item,
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {', '.join(bits) if bits else '(empty)'}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="schoolyard", problem="wind", item="mitten", name="Mina", friend="Pip", trait="kind"),
    StoryParams(place="bus_stop", problem="rain", item="rain_glove", name="Owen", friend="June", trait="quiet"),
    StoryParams(place="porch", problem="bite", item="kitten_mitt", name="Iris", friend="Nia", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.problem} with {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
