#!/usr/bin/env python3
"""
A small whodunit-style storyworld with an inner monologue and a happy ending.

Seed tale:
- Tonight, Don notices that a tiny keepsake is missing.
- He thinks through clues in his head, questions a few people, and notices a detail.
- The culprit is not cruel; they were borrowing the item for a kind reason.
- Don gets the keepsake back, and the story ends warmly.

This world keeps the domain small and constraint-checked:
- typed entities with meters and memes
- a simple simulated investigation
- a gentle resolution that always ends in a happy ending
- an ASP twin for the same reasonableness gate
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fame": 0.0, "moved": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0, "guilt": 0.0, "kindness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "boy", "detective"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    indoors: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    label: str
    found_at: str
    points_to: str  # person id or location id
    kind: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    culprit: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.time = "tonight"

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "study": Place(id="study", label="the study", mood="quiet", indoors=True, clues=["ink", "books", "lamp"]),
    "hall": Place(id="hall", label="the hall", mood="echoing", indoors=True, clues=["coat", "footsteps", "door"]),
    "kitchen": Place(id="kitchen", label="the kitchen", mood="warm", indoors=True, clues=["crumbs", "cup", "sink"]),
}

MYSTERIES = {
    "missing_note": {
        "thing": "a folded note",
        "phrase": "a small folded note with blue ink",
        "home": "desk",
        "reason": "it was borrowed to copy a recipe",
        "kind": "paper",
        "search_spot": "the lamp table",
    },
    "missing_key": {
        "thing": "a brass key",
        "phrase": "a little brass key on a red string",
        "home": "hook",
        "reason": "it was moved to open the attic for a surprise",
        "kind": "metal",
        "search_spot": "the coat pocket",
    },
    "missing_cookie": {
        "thing": "a jam cookie",
        "phrase": "one last jam cookie on a plate",
        "home": "plate",
        "reason": "it was saved for a tired helper",
        "kind": "food",
        "search_spot": "the tea tray",
    },
}

CHARACTERS = {
    "don": {"id": "Don", "type": "man", "label": "Don"},
    "mira": {"id": "Mira", "type": "woman", "label": "Mira"},
    "pip": {"id": "Pip", "type": "boy", "label": "Pip"},
    "rose": {"id": "Rose", "type": "girl", "label": "Rose"},
}

HELPER_KINDS = ["neighbor", "little sibling", "friend"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            for culprit_id in CHARACTERS:
                if culprit_id == "don":
                    continue
                if mystery["kind"] == "food" and place_id == "study":
                    continue
                combos.append((place_id, mystery_id, culprit_id))
    return combos


def explain_rejection(place: str, mystery: str, culprit: str) -> str:
    return (
        f"(No story: the chosen setup does not make a tidy whodunit. "
        f"Try a different place, mystery, or culprit.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A valid mystery is one where someone other than Don can be the culprit.
valid_combo(Place, Mystery, Culprit) :- place(Place), mystery(Mystery), character(Culprit), Culprit != don,
                                        compatible(Place, Mystery, Culprit).

#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_kind", mid, m["kind"]))
        for spot in [m["home"], m["search_spot"]]:
            lines.append(asp.fact("appears_in", mid, spot))
    for cid in CHARACTERS:
        lines.append(asp.fact("character", cid))
    for place_id in PLACES:
        for mystery_id, mystery in MYSTERIES.items():
            for culprit_id in CHARACTERS:
                if culprit_id != "don":
                    lines.append(asp.fact("compatible", place_id, mystery_id, culprit_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - asp_set))
    print(" only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def introduce(world: World, don: Entity, helper: Entity) -> None:
    world.say(
        f"Tonight, Don was in {world.place.label}, and the room felt quiet enough to hear a thought."
    )
    world.say(
        f"He had a habit of noticing small things, and {helper.label} was the kind of person who could keep a secret."
    )


def missing_discovery(world: World, don: Entity, mystery: dict) -> None:
    don.memes["worry"] += 1
    don.memes["curiosity"] += 1
    world.say(
        f"Then Don looked for {mystery['thing']}, but it was gone."
    )
    world.say(
        f"In his head, Don asked the first whodunit question: who would move something so small, and why?"
    )


def gather_clues(world: World, don: Entity, culprit: Entity, helper: Entity, mystery: dict) -> None:
    clue1 = Clue(id="clue1", label="a faint trail of crumbs", found_at="kitchen", points_to=helper.id, kind="food")
    clue2 = Clue(id="clue2", label="blue ink on a fingertip", found_at="study", points_to=culprit.id, kind="ink")
    world.clues.extend([clue1, clue2])
    don.memes["curiosity"] += 1
    world.say(
        f"He checked the little signs around the room: {clue1.label}, then {clue2.label}."
    )
    world.say(
        f"His inner monologue kept nudging him forward: if there were crumbs, the missing thing had been taken for a kind reason, not a mean one."
    )


def question_and_answer(world: World, don: Entity, culprit: Entity, helper: Entity, mystery: dict) -> None:
    helper.memes["guilt"] += 1
    culprit.memes["guilt"] += 1
    world.say(
        f"Don followed the trail to {helper.label}, and {helper.label} finally admitted the truth."
    )
    world.say(
        f"{helper.label} had moved {mystery['thing']} because {mystery['reason']}."
    )
    world.say(
        f"The real mistake was not asking first, and Don could see that nobody meant harm."
    )


def resolve(world: World, don: Entity, culprit: Entity, helper: Entity, mystery: dict) -> None:
    don.memes["worry"] = 0
    don.memes["relief"] += 2
    culprit.memes["kindness"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"With a tiny laugh, {helper.label} brought the missing {mystery['thing']} back where it belonged."
    )
    world.say(
        f"Don set it down in its proper place and smiled, because the answer had been a kind one all along."
    )
    world.say(
        f"By the end of the night, the room felt peaceful again, and the little mystery had turned into a happy ending."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)

    don = world.add(Entity(id="Don", kind="character", type="man", label="Don"))
    culprit_cfg = CHARACTERS[params.culprit]
    culprit = world.add(Entity(id=culprit_cfg["id"], kind="character", type=culprit_cfg["type"], label=culprit_cfg["label"]))
    helper_cfg = CHARACTERS[params.helper]
    helper = world.add(Entity(id=helper_cfg["id"], kind="character", type=helper_cfg["type"], label=helper_cfg["label"]))

    missing = world.add(Entity(id="missing", kind="thing", type=mystery["kind"], label=mystery["thing"], phrase=mystery["phrase"], owner="Don", location=mystery["home"]))
    world.facts.update(place=place, mystery=mystery, culprit=culprit, helper=helper, don=don, missing=missing)

    introduce(world, don, helper)
    world.para()
    missing_discovery(world, don, mystery)
    gather_clues(world, don, culprit, helper, mystery)
    world.para()
    question_and_answer(world, don, culprit, helper, mystery)
    resolve(world, don, culprit, helper, mystery)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    return [
        f"Write a short whodunit story for young children where Don solves the mystery of {m['thing']} tonight.",
        f"Tell a gentle detective story with an inner monologue, clues, and a happy ending in {world.place.label}.",
        f"Write a small mystery story that starts with Don noticing something missing and ends with the item returned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    helper = world.facts["helper"]
    culprit = world.facts["culprit"]
    return [
        QAItem(
            question=f"What was missing tonight in {world.place.label}?",
            answer=f"{m['thing'].capitalize()} was missing, and Don noticed right away because he was paying close attention.",
        ),
        QAItem(
            question="How did Don figure out what happened?",
            answer="He followed the clues in his head, looked for small signs, and listened carefully until the truth made sense.",
        ),
        QAItem(
            question=f"Why had {helper.label} moved the missing thing?",
            answer=f"{helper.label} moved it because {m['reason']}. It was a mistake made for a kind reason.",
        ),
        QAItem(
            question="What kind of ending did the story have?",
            answer="It had a happy ending, because the missing thing came back and everyone felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where the reader follows clues to figure out who caused the problem.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thinking a character does in their own head.",
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer="Detectives look at clues because small details can help explain what happened.",
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
        lines.append(f"  {e.id:8} ({e.kind:8}) type={e.type:8} meters={e.meters} memes={e.memes}")
    lines.append(f"  clues: {[c.label for c in world.clues]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with Don and a gentle happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--culprit", choices=[k for k in CHARACTERS if k != "don"])
    ap.add_argument("--helper", choices=[k for k in CHARACTERS if k != "don"])
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
    if args.place or args.mystery or args.culprit or args.helper:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.mystery is None or c[1] == args.mystery)
            and (args.culprit is None or c[2] == args.culprit)
        ]
    if not combos:
        raise StoryError(explain_rejection(args.place, args.mystery, args.culprit))
    place, mystery, culprit = rng.choice(sorted(combos))
    helper = args.helper or rng.choice([k for k in CHARACTERS if k not in {"don", culprit}])
    if helper == culprit:
        helper = "mira" if culprit != "mira" else "pip"
    return StoryParams(place=place, mystery=mystery, culprit=culprit, helper=helper)


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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible (place, mystery, culprit) combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="study", mystery="missing_note", culprit="mira", helper="pip"),
            StoryParams(place="hall", mystery="missing_key", culprit="rose", helper="mira"),
            StoryParams(place="kitchen", mystery="missing_cookie", culprit="pip", helper="rose"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
