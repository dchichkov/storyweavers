#!/usr/bin/env python3
"""
audience_flashback_detective_story.py
=====================================

A small storyworld for a detective-story premise with an audience and a
flashback-shaped turn.

Premise:
- A careful detective is asked to find something missing while an audience waits.
- The case turns on a remembered flashback that reveals a clue.
- The ending proves the detective's model of the world changed: the truth is
  found, the audience learns what happened, and the missing thing returns.

The world is intentionally small and constraint-checked: only a few plausible
cases are allowed, and the flashback must actually explain the solved mystery.
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "detective"}
        female = {"girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Venue:
    place: str
    audience_kind: str
    noise: str
    good_for: set[str] = field(default_factory=set)


@dataclass
class Case:
    mystery: str
    missing_label: str
    missing_phrase: str
    missing_type: str
    clue_place: str
    clue_phrase: str
    flashback_phrase: str
    resolved_phrase: str
    risk: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_seen = False

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

    def copy(self) -> "World":
        import copy
        clone = World(self.venue)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_seen = self.flashback_seen
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VENUES = {
    "the town hall": Venue("the town hall", audience_kind="crowd", noise="murmurs", good_for={"announcement", "search"}),
    "the school stage": Venue("the school stage", audience_kind="classroom crowd", noise="whispers", good_for={"announcement", "search"}),
    "the little theater": Venue("the little theater", audience_kind="ticket line", noise="footsteps", good_for={"announcement", "search"}),
}

CASES = {
    "blue_book": Case(
        mystery="the missing blue book",
        missing_label="blue book",
        missing_phrase="a blue book with a silver sticker",
        missing_type="book",
        clue_place="the curtain pocket",
        clue_phrase="a ribbon bookmark",
        flashback_phrase="the usher had tucked the bookmark into the curtain pocket after the last show",
        resolved_phrase="the blue book was resting safely on the stage table",
        risk="the audience would think someone had stolen it",
        tags={"book", "curtain", "stage"},
    ),
    "toy_key": Case(
        mystery="the missing brass key toy",
        missing_label="brass key toy",
        missing_phrase="a brass key toy on a string",
        missing_type="toy",
        clue_place="the coat rack",
        clue_phrase="a frayed string loop",
        flashback_phrase="the helper had hooked the string on the coat rack while carrying chairs",
        resolved_phrase="the brass key toy was hanging from the coat rack, easy to reach",
        risk="the performance could not begin without it",
        tags={"key", "coat", "rack"},
    ),
    "red_glove": Case(
        mystery="the missing red glove",
        missing_label="red glove",
        missing_phrase="one red glove with a button cuff",
        missing_type="glove",
        clue_place="the lamp base",
        clue_phrase="a red thread",
        flashback_phrase="the janitor had brushed the glove against the lamp base while turning off the lights",
        resolved_phrase="the red glove was wrapped around the lamp base, bright as a berry",
        risk="the owner would be cold and upset",
        tags={"glove", "lamp", "thread"},
    ),
}

DETECTIVES = [
    ("Iris", "girl"),
    ("Noah", "boy"),
    ("Mina", "girl"),
    ("Eli", "boy"),
    ("Ada", "girl"),
]

ACTIONS = [
    "looked closely at the stage",
    "studied the audience seats",
    "checked the corners",
    "followed the small clue",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A case is solvable if there is a clue place and a flashback that explains it.
solvable(C) :- case(C), clue(C, _), flashback(C, _).

% A resolved case is one whose clue and flashback match the same case.
resolved(C) :- solvable(C).

#show resolved/1.
#show solvable/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        lines.append(asp.fact("audience_kind", venue_id, venue.audience_kind))
        for g in sorted(venue.good_for):
            lines.append(asp.fact("good_for", venue_id, g))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("clue", case_id, case.clue_place))
        lines.append(asp.fact("flashback", case_id, case.flashback_phrase))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show solvable/1."))
    symbols = set((sym.name, tuple(arg.string if arg.type == arg.type.String else getattr(arg, "number", arg.name) for arg in sym.arguments)) for sym in model)
    expected = {("solvable", (cid,)) for cid in CASES} | {("resolved", (cid,)) for cid in CASES}
    if symbols == expected:
        print(f"OK: ASP parity check passed for {len(CASES)} cases.")
        return 0
    print("MISMATCH between ASP and Python gating.")
    print("ASP:", sorted(symbols))
    print("Expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    venue: str
    case: str
    detective_name: str
    detective_type: str
    audience: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(venue: Venue, case: Case) -> bool:
    return "search" in venue.good_for and bool(case.clue_place) and bool(case.flashback_phrase)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for venue_id, venue in VENUES.items():
        for case_id, case in CASES.items():
            if valid_combo(venue, case):
                combos.append((venue_id, case_id))
    return combos


def explain_rejection(venue: Venue, case: Case) -> str:
    return (
        f"(No story: the case '{case.mystery}' does not fit well at {venue.place}. "
        f"The detective needs a place where the audience can wait and the clue can be found.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, detective: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} was a careful little detective who liked solving problems before the audience grew restless."
    )
    world.say(
        f"That night, the audience was in {world.venue.place}, and everyone was waiting for {case.mystery} to be explained."
    )


def setup_case(world: World, detective: Entity, case: Case) -> None:
    case_obj = world.add(Entity(
        id="missing", kind="thing", label=case.missing_label, type=case.missing_type,
        location=world.venue.place, owner="owner"
    ))
    world.facts["case_obj"] = case_obj
    world.facts["case"] = case
    world.say(
        f"The missing thing was {case.missing_phrase}, and its owner kept looking toward the stage."
    )
    world.say(
        f"{case.risk.capitalize()}, so {detective.id} promised to check every corner."
    )


def search(world: World, detective: Entity, case: Case) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0.0) + 1
    world.say(
        f"{detective.id} {random.choice(ACTIONS)} while the audience stayed very quiet."
    )
    world.say(
        f"Near {case.clue_place}, {detective.id} noticed {case.clue_phrase}."
    )


def flashback(world: World, detective: Entity, case: Case) -> None:
    detective.memes["memory"] = detective.memes.get("memory", 0.0) + 1
    world.flashback_seen = True
    world.para()
    world.say(
        f"Then {detective.id} remembered a flashback: {case.flashback_phrase}."
    )
    world.say(
        f"That memory changed everything, because the clue suddenly made sense."
    )


def solve(world: World, detective: Entity, case: Case) -> None:
    world.facts["solved"] = True
    case_obj: Entity = world.facts["case_obj"]
    case_obj.location = world.venue.place
    case_obj.carried_by = None
    world.say(
        f"{detective.id} followed the clue and found it: {case.resolved_phrase}."
    )
    world.say(
        f"The owner smiled, the audience clapped, and the room felt calm again."
    )


def tell_story(params: StoryParams) -> World:
    venue = VENUES[params.venue]
    case = CASES[params.case]
    world = World(venue)
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
    ))
    world.add(Entity(
        id="audience",
        kind="group",
        type="crowd",
        label=params.audience,
        location=venue.place,
    ))
    world.facts["detective"] = detective
    world.facts["audience"] = params.audience

    intro(world, detective, case)
    world.para()
    setup_case(world, detective, case)
    search(world, detective, case)
    flashback(world, detective, case)
    solve(world, detective, case)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective: Entity = f["detective"]
    case: Case = f["case"]
    return [
        f'Write a short detective story for children that includes an audience and the word "audience".',
        f"Tell a mystery story where {detective.id} searches for {case.mystery} in front of an audience and remembers a flashback clue.",
        f"Write a gentle detective story with a clear clue, a flashback, and an ending where the audience learns what happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    case: Case = f["case"]
    qa = [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{detective.id} solved the mystery by following the clue and remembering the flashback.",
        ),
        QAItem(
            question=f"What was the missing thing?",
            answer=f"It was {case.missing_phrase}.",
        ),
        QAItem(
            question=f"Why did the audience wait quietly?",
            answer=f"The audience waited quietly because everyone was waiting to learn what had happened to {case.missing_label}.",
        ),
        QAItem(
            question=f"What clue did {detective.id} notice?",
            answer=f"{detective.id} noticed {case.clue_phrase} near {case.clue_place}.",
        ),
        QAItem(
            question=f"What did the flashback help explain?",
            answer=f"The flashback helped explain {case.flashback_phrase}, which showed where the missing thing had ended up.",
        ),
    ]
    if world.facts.get("solved"):
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with {case.resolved_phrase}, and the audience clapped when the mystery was solved.",
        ))
    return qa


WORLD_QA = [
    QAItem(
        question="What is a detective for?",
        answer="A detective looks for clues and uses careful thinking to figure out what happened.",
    ),
    QAItem(
        question="What is a flashback?",
        answer="A flashback is a remembered scene from before that helps explain the present.",
    ),
    QAItem(
        question="Why do audiences stay quiet during a mystery?",
        answer="An audience stays quiet so they can hear the clues and understand the story.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Generation prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld with an audience and a flashback.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--detective-type", choices=["girl", "boy"], dest="detective_type")
    ap.add_argument("--audience")
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
    combos = valid_combos()
    if args.venue and args.case:
        if not valid_combo(VENUES[args.venue], CASES[args.case]):
            raise StoryError(explain_rejection(VENUES[args.venue], CASES[args.case]))
    valid = [c for c in combos if (args.venue is None or c[0] == args.venue) and (args.case is None or c[1] == args.case)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    venue, case = rng.choice(valid)
    name, dtype = rng.choice(DETECTIVES)
    if args.name:
        name = args.name
    if args.detective_type:
        dtype = args.detective_type
    audience = args.audience or VENUES[venue].audience_kind
    return StoryParams(venue=venue, case=case, detective_name=name, detective_type=dtype, audience=audience)


def generate(params: StoryParams) -> StorySample:
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
    lines.append(f"flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


CURATED = [
    StoryParams(venue="the town hall", case="blue_book", detective_name="Iris", detective_type="girl", audience="crowd"),
    StoryParams(venue="the school stage", case="toy_key", detective_name="Noah", detective_type="boy", audience="classroom crowd"),
    StoryParams(venue="the little theater", case="red_glove", detective_name="Mina", detective_type="girl", audience="ticket line"),
]


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show solvable/1."))
    return sorted(set(asp.atoms(model, "resolved")) | set(asp.atoms(model, "solvable")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1.\n#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1.\n#show solvable/1."))
        print(asp.atoms(model, "solvable"))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} at {p.venue} ({p.case})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
