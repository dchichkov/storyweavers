#!/usr/bin/env python3
"""
storyworlds/worlds/duck_dim_twist_surprise_mystery_to_solve.py
===============================================================

A small pirate-tale story world about a duck-dim twist, a surprise, and a
mystery to solve.

The simulated premise:
- A young pirate wants to sail, but something odd happens with a tiny duck-sized
  clue called "duck-dim".
- The crew finds a mystery that can only be solved by checking a map, a key, and
  a hidden cove.
- The turn comes from a surprise twist: the clue is not a monster at all, but a
  signal that points to the treasure chest.
- The ending proves the change in the world state: the mystery is solved, the
  treasure is opened, and the crew celebrates.

This world keeps the prose authored and state-driven, with meters and memes
tracked on entities, plus an inline ASP twin for parity checks.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain"}
        male = {"boy", "man", "pirate", "mate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the deck of the little ship"
    indoors: bool = False
    winds: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hint: str
    size: str
    location: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    question: str
    solved_by: str
    requires: set[str]
    surprise: str
    twist: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        return World(
            setting=self.setting,
            entities=_copy.deepcopy(self.entities),
            facts=_copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "deck": Setting(place="the deck of the little ship", winds={"sea", "salt"}),
    "cove": Setting(place="the hidden cove", winds={"sea", "salt"}),
    "harbor": Setting(place="the busy harbor", winds={"sea", "rope", "salt"}),
}

CREW = {
    "captain": {"type": "captain", "label": "Captain Mira", "trait": "brave"},
    "mate": {"type": "mate", "label": "First Mate Joss", "trait": "quick"},
    "sailor": {"type": "sailor", "label": "Sailor Pip", "trait": "curious"},
}

CLUES = {
    "duck_dim": Clue(
        id="duck_dim",
        label="duck-dim clue",
        phrase="a duck-dim clue with a tiny brass shine",
        hint="it was small as a duck and shaped like a map hook",
        size="duck-dim",
        location="under a loose plank",
        kind="clue",
        tags={"duck-dim", "tiny", "brass", "map"},
    ),
    "feather_note": Clue(
        id="feather_note",
        label="feather note",
        phrase="a feather note tied with blue string",
        hint="it was soft and light, fluttering like a secret",
        size="small",
        location="inside a bottle",
        kind="clue",
        tags={"note", "secret", "map"},
    ),
    "shell_key": Clue(
        id="shell_key",
        label="shell key",
        phrase="a shell-shaped key",
        hint="it looked like a shell but fit a tiny lock",
        size="small",
        location="in the sand",
        kind="key",
        tags={"key", "shell", "metal"},
    ),
}

MYSTERIES = {
    "treasure": Mystery(
        id="treasure",
        label="treasure chest mystery",
        question="who hid the treasure chest",
        solved_by="opening the chest with the shell key",
        requires={"duck-dim", "key", "map"},
        surprise="the duck-dim clue was really a map mark",
        twist="the tiny clue pointed to the hidden cove, not a monster",
    )
}

GOLD = Entity(
    id="gold",
    kind="thing",
    type="treasure",
    label="gold coins",
    phrase="a stack of gold coins",
    plural=True,
)

NAMES = ["Mira", "Joss", "Pip", "Nell", "Bo", "Tamsin", "Reed", "Kite"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "deck"
    clue: str = "duck_dim"
    mystery: str = "treasure"
    crew: str = "captain"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is valid if its tags include duck-dim and it belongs to a navigable setting.
duck_clue(C) :- clue(C), tag(C, duck_dim).

% A mystery can be solved if the required pieces are present.
has_piece(M, P) :- mystery(M), requires(M, P), piece(P).
solved(M) :- mystery(M), has_piece(M, duck_dim), has_piece(M, key), has_piece(M, map).

valid_story(S, C, M) :- setting(S), clue(C), mystery(M),
                        duck_clue(C), valid_setting(S), solvable(M).

valid_setting(deck).
valid_setting(cove).
valid_setting(harbor).

solvable(treasure).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for w in sorted(SETTINGS[sid].winds):
            lines.append(asp.fact("wind", sid, w))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("piece", clue.kind))
        for t in sorted(clue.tags):
            lines.append(asp.fact("tag", cid, t.replace("-", "_")))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for req in sorted(m.requires):
            lines.append(asp.fact("requires", mid, req.replace("-", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def reason_check(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.crew not in CREW:
        raise StoryError(f"Unknown crew role: {params.crew}")
    clue = CLUES[params.clue]
    mystery = MYSTERIES[params.mystery]
    if "duck-dim" not in clue.tags:
        raise StoryError("This story needs the duck-dim clue to drive the twist.")
    if not mystery.requires.issubset(clue.tags | {"key", "map"}):
        raise StoryError("The mystery needs a clue that can plausibly point to the key and map.")


def all_valid() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for mid, mys in MYSTERIES.items():
                if "duck-dim" in clue.tags and mys.requires.issubset(clue.tags | {"key", "map"}):
                    out.append((sid, cid, mid))
    return out


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _do_search(world: World, crew: Entity, clue: Clue) -> None:
    crew.memes["curiosity"] = crew.memes.get("curiosity", 0) + 1
    crew.meters["search"] = crew.meters.get("search", 0) + 1
    world.say(
        f"{crew.label} searched {world.setting.place} and found {clue.phrase} "
        f"{clue.hint}."
    )


def _do_twist(world: World, crew: Entity, clue: Clue, mystery: Mystery) -> None:
    crew.memes["surprise"] = crew.memes.get("surprise", 0) + 1
    world.say(
        f"Then came the twist: {mystery.surprise}. "
        f"{crew.label} blinked, because the duck-dim clue was not a trick at all."
    )
    world.say(
        f"It was a surprise that pointed straight to the {mystery.label}."
    )


def _do_solve(world: World, crew: Entity, clue: Clue, mystery: Mystery) -> None:
    crew.memes["confidence"] = crew.memes.get("confidence", 0) + 1
    crew.meters["solve"] = crew.meters.get("solve", 0) + 1
    world.facts["solved"] = True
    world.facts["twist"] = mystery.twist
    world.say(
        f"{crew.label} followed the clue to the hidden cove, found the shell key, "
        f"and opened the chest. The mystery was solved."
    )
    world.say(
        f"Inside were gold coins, and the crew laughed as the sea wind rattled the mast."
    )


def tell(params: StoryParams) -> World:
    reason_check(params)
    world = World(setting=SETTINGS[params.setting])
    crew_cfg = CREW[params.crew]
    crew = world.add(Entity(
        id=params.crew,
        kind="character",
        type=crew_cfg["type"],
        label=crew_cfg["label"],
    ))
    clue = CLUES[params.clue]
    mystery = MYSTERIES[params.mystery]
    world.add(Entity(
        id=clue.id,
        kind="thing",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
    ))
    world.add(Entity(
        id=mystery.id,
        kind="thing",
        type="mystery",
        label=mystery.label,
        phrase=mystery.question,
    ))
    world.add(GOLD)

    world.say(
        f"On {world.setting.place}, {crew.label} watched the waves and felt a strange tug of curiosity."
    )
    world.say(
        f"{crew.label} had heard of a mystery to solve, and the only hint was a duck-dim clue."
    )
    world.para()
    _do_search(world, crew, clue)
    world.say(
        f"The crew thought at first it might mean a bird or a prank, but the clue kept pointing deeper."
    )
    world.para()
    _do_twist(world, crew, clue, mystery)
    _do_solve(world, crew, clue, mystery)

    world.facts.update(
        setting=params.setting,
        clue=params.clue,
        mystery=params.mystery,
        crew=params.crew,
        clue_obj=clue,
        mystery_obj=mystery,
        crew_obj=crew,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale with a duck-dim clue, a twist, a surprise, and a mystery to solve.',
        f"Tell a child-friendly story where {f['crew_obj'].label} searches {world.setting.place} and discovers why the duck-dim clue matters.",
        "Write a simple sea adventure that ends with a chest opening and the mystery being solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    crew = world.facts["crew_obj"]
    clue = world.facts["clue_obj"]
    mystery = world.facts["mystery_obj"]
    return [
        QAItem(
            question=f"What did {crew.label} find while searching {world.setting.place}?",
            answer=f"{crew.label} found {clue.phrase}. It was the duck-dim clue that started the mystery.",
        ),
        QAItem(
            question="What was the surprise twist in the story?",
            answer=f"The surprise was that {mystery.surprise}. That changed the crew's idea of what the clue meant.",
        ),
        QAItem(
            question="How was the mystery solved at the end?",
            answer=f"It was solved by following the clue to the hidden cove, finding the shell key, and opening the chest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does a twist do in a story?",
            answer="A twist changes what the characters thought was happening and makes the story surprising.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that sails the sea and carries pirates and their gear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {e.type:10} {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a duck-dim twist and mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--crew", choices=CREW)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {args.setting}")
    if args.clue and args.clue not in CLUES:
        raise StoryError(f"Unknown clue: {args.clue}")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {args.mystery}")
    if args.crew and args.crew not in CREW:
        raise StoryError(f"Unknown crew: {args.crew}")

    valid = all_valid()
    valid = [v for v in valid
             if (args.setting is None or v[0] == args.setting)
             and (args.clue is None or v[1] == args.clue)
             and (args.mystery is None or v[2] == args.mystery)]
    if not valid:
        raise StoryError("No valid pirate story matches those choices.")
    setting, clue, mystery = rng.choice(valid)
    crew = args.crew or rng.choice(list(CREW))
    return StoryParams(setting=setting, clue=clue, mystery=mystery, crew=crew)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    py = set(all_valid())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for sid, cid, mid in all_valid():
            params = StoryParams(setting=sid, clue=cid, mystery=mid, crew="captain")
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
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
