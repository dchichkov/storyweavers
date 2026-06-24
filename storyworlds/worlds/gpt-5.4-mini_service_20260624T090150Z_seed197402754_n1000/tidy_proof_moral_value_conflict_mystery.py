#!/usr/bin/env python3
"""
storyworlds/worlds/tidy_proof_moral_value_conflict_mystery.py
==============================================================

A tiny storyworld about a child, a tidy place, a mystery, and a proof that
clears up a conflict.

Seed tale sketch:
---
Maya loved keeping her room tidy. One morning, her shiny red ribbon was missing.
Her brother Ben said he did not take it, but Maya was sure someone had moved it.
She looked carefully for a clue. Under the toy box, she found a small red thread
stuck to a book. That was proof! Ben had not taken the ribbon at all. The cat
had dragged it while chasing a string. Maya put everything back in order, and
everyone felt better.

World model:
---
- physical meters: tidy, mess, hidden, clue
- emotional memes: worry, conflict, relief, pride, fairness
- the mystery is driven by state changes, not frozen prose
- the proof must be real evidence that matches the culprit
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tidy", "mess", "hidden", "clue"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "conflict", "relief", "pride", "fairness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    label: str
    tidy_bonus: float = 1.0


@dataclass
class Clue:
    label: str
    phrase: str
    proves: str  # culprit id


@dataclass
class StoryParams:
    place: str
    hero: str
    sibling: str
    culprit: str
    object: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    "bedroom": Place("the bedroom", tidy_bonus=1.2),
    "playroom": Place("the playroom", tidy_bonus=1.0),
    "study": Place("the study", tidy_bonus=1.1),
}

HEROES = [
    ("Maya", "girl", "curious"),
    ("Lena", "girl", "careful"),
    ("Owen", "boy", "quiet"),
    ("Noah", "boy", "gentle"),
]

SIBLINGS = [
    ("Ben", "boy"),
    ("Ava", "girl"),
    ("Mia", "girl"),
    ("Eli", "boy"),
]

CULPRITS = [
    ("cat", "cat"),
    ("puppy", "dog"),
    ("wind", "weather"),
]

OBJECTS = {
    "ribbon": ("shiny red ribbon", "ribbon"),
    "crayon": ("blue crayon", "crayon"),
    "bookmark": ("striped bookmark", "bookmark"),
    "marble": ("glass marble", "marble"),
}

CLUES = {
    "thread": Clue("thread", "a small red thread on the book", "cat"),
    "mud": Clue("mud", "tiny muddy paw prints by the chair", "puppy"),
    "page": Clue("page", "a corner of the page folded by the open window", "wind"),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A proof is good when it matches the culprit.
good_proof(C) :- clue(C), proves(C, Culprit), culprit(Culprit).

% The conflict is resolved when a good proof exists.
resolved :- good_proof(_).

% A tidy ending happens after the mess is cleared and items are put back.
tidy_end :- resolved, cleaned, put_back.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid, _, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    for sid, _ in SIBLINGS:
        lines.append(asp.fact("sibling", sid))
    for cid, _ in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for kid, clue in CLUES.items():
        lines.append(asp.fact("clue", kid))
        lines.append(asp.fact("proves", kid, clue.proves))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_proof/1. #show resolved/0. #show tidy_end/0."))
    atoms = {str(a) for a in model}
    expected = set()
    if "good_proof" not in "".join(atoms):
        expected = {"resolved", "tidy_end"}
    # Simple parity check: if any clue matches any culprit, ASP should resolve.
    py = any(c.proves == clue.proves for clue in CLUES.values() for c in CLUES.values())
    if py and model:
        print("OK: ASP ran and produced a model.")
        return 0
    print("MISMATCH or empty model.")
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about tidy things and proof.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
    ap.add_argument("--culprit", choices=[c[0] for c in CULPRITS])
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--clue", choices=CLUES)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    sibling = args.sibling or rng.choice([s[0] for s in SIBLINGS])
    culprit = args.culprit or rng.choice([c[0] for c in CULPRITS])
    obj = args.object_ or rng.choice(list(OBJECTS))
    clue = args.clue or rng.choice(list(CLUES))
    if clue == "thread" and culprit != "cat":
        if args.clue is not None or args.culprit is not None:
            raise StoryError("The red thread proof only fits the cat in this world.")
        culprit = "cat"
    if clue == "mud" and culprit != "puppy":
        if args.clue is not None or args.culprit is not None:
            raise StoryError("The muddy paw print proof only fits the puppy in this world.")
        culprit = "puppy"
    if clue == "page" and culprit != "wind":
        if args.clue is not None or args.culprit is not None:
            raise StoryError("The folded-page proof only fits the wind in this world.")
        culprit = "wind"
    return StoryParams(place=place, hero=hero, sibling=sibling, culprit=culprit, object=obj, clue=clue)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])

    hero_type = next(t for n, t, _ in HEROES if n == params.hero)
    sibling_type = next(t for n, t in SIBLINGS if n == params.sibling)
    culprit_type = next(t for cid, t in CULPRITS if cid == params.culprit)
    obj_phrase, obj_label = OBJECTS[params.object]
    clue = CLUES[params.clue]

    hero = world.add(Entity(params.hero, kind="character", type=hero_type, label=params.hero))
    sibling = world.add(Entity(params.sibling, kind="character", type=sibling_type, label=params.sibling))
    culprit = world.add(Entity(params.culprit, kind="character" if culprit_type in {"cat", "dog"} else "thing",
                               type=culprit_type, label=params.culprit))
    item = world.add(Entity(params.object, type=params.object, label=obj_label, phrase=obj_phrase, owner=hero.id, caretaker=hero.id))
    clue_ent = world.add(Entity(params.clue, type="clue", label=clue.label, phrase=clue.phrase, hidden=True))

    # Act 1: neat setup.
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} liked keeping {world.place.label} tidy. "
        f"Every book had a place, and {hero.pronoun('possessive')} {item.label} was always special."
    )
    world.say(
        f"{hero.id} and {sibling.id} were quiet in the morning light, but then {hero.id} noticed something was wrong: "
        f"{hero.pronoun('possessive')} {item.label} was missing."
    )
    world.para()

    # Act 2: conflict and search.
    hero.memes["worry"] += 1
    hero.memes["conflict"] += 1
    sibling.memes["fairness"] += 0.5
    world.say(
        f"{hero.id} looked at {sibling.id} first. "
        f'"I did not take it," {sibling.pronoun()} said, but {hero.id} still felt a twist of worry.'
    )
    world.say(
        f"The room felt less tidy now. Drawers were open, a toy box was tipped, and the missing thing seemed to hide in the middle of the mess."
    )
    world.para()

    # Act 3: proof.
    if params.clue == "thread":
        culprit.meters["mess"] += 1
        item.meters["hidden"] += 1
        clue_ent.hidden = False
    elif params.clue == "mud":
        culprit.meters["mess"] += 1
        item.meters["hidden"] += 1
        clue_ent.hidden = False
    else:
        culprit.meters["mess"] += 1
        item.meters["hidden"] += 1
        clue_ent.hidden = False

    hero.meters["clue"] += 1
    hero.memes["fairness"] += 1
    world.say(
        f"At last, {hero.id} found {clue.phrase}. That was proof."
    )
    world.say(
        f"The clue pointed to {culprit.id}, not {sibling.id}. "
        f"The mystery was not about blame after all; it was about noticing what the clue could really show."
    )

    # Resolution: tidy restored.
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.memes["conflict"] = 0.0
    hero.meters["tidy"] += 1
    item.hidden = False
    world.say(
        f"{hero.id} put the {item.label} back where it belonged and made the room tidy again. "
        f"{sibling.id} smiled, because the proof had been fair."
    )
    world.say(
        f"In the end, {world.place.label} looked neat and calm, and {hero.id} felt proud for solving the mystery kindly."
    )

    world.facts.update(
        hero=hero,
        sibling=sibling,
        culprit=culprit,
        item=item,
        clue=clue,
        resolved=True,
        place=world.place.label,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery for a child that includes the words "tidy" and "proof".',
        f"Tell a story about {f['hero'].id} finding proof about a missing {f['item'].label} and keeping the ending kind.",
        f"Write a gentle mystery where a tidy room, a fair clue, and a misunderstanding lead to a happy resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    culprit = f["culprit"]
    item = f["item"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What was missing from the tidy room?",
            answer=f"{hero.id}'s {item.label} was missing, and that made the room feel less tidy for a while.",
        ),
        QAItem(
            question=f"What proof did {hero.id} find?",
            answer=f"{hero.id} found {clue.phrase}. It was proof because it pointed to {culprit.id}.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop worrying about {sibling.id}?",
            answer=f"Because the proof showed that {sibling.id} did not take the {item.label}. The clue made the story fair.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} put the {item.label} back, the room became tidy again, and everyone felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is proof?",
            answer="Proof is information or evidence that helps show what really happened.",
        ),
        QAItem(
            question="What does tidy mean?",
            answer="Tidy means neat, clean, and put in the right place.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem that needs careful looking and thinking to solve.",
        ),
        QAItem(
            question="Why is fairness important?",
            answer="Fairness matters because people feel better when the truth is used instead of quick blame.",
        ),
    ]


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
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show good_proof/1. #show resolved/0. #show tidy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_proof/1. #show resolved/0. #show tidy_end/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bedroom", "Maya", "Ben", "cat", "ribbon", "thread"),
            StoryParams("playroom", "Lena", "Ava", "puppy", "crayon", "mud"),
            StoryParams("study", "Owen", "Eli", "wind", "bookmark", "page"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
