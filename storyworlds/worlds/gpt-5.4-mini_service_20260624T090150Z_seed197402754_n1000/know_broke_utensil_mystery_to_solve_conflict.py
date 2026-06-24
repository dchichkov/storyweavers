#!/usr/bin/env python3
"""
storyworlds/worlds/know_broke_utensil_mystery_to_solve_conflict.py
===================================================================

A small nursery-rhyme story world about a broken utensil, a little mystery,
and a gentle conflict that turns into problem solving.

Premise:
- A child knows their favorite utensil has broke.
- Nobody knows how it happened at first.
- The child and a helper look for clues.
- A conflict flares when someone feels blamed.
- The story ends with a careful repair and a clear answer.

The world is intentionally tiny and constraint-checked:
- The mystery must concern a utensil that can plausibly break.
- The chosen repair must fit the utensil type.
- The conflict must be resolved by an actual finding, not a frozen moral.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    broken: bool = False
    found: bool = False
    repaired: bool = False
    blamed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    table: str = "the table"


@dataclass
class Utensil:
    id: str
    label: str
    phrase: str
    kind: str
    breakable: bool
    fix: str
    clue: str
    sings: str


@dataclass
class StoryParams:
    utensil: str
    culprit: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
# Content registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the kitchen", table="the little table")

UTENSILS = {
    "spoon": Utensil(
        id="spoon",
        label="spoon",
        phrase="a shiny little spoon",
        kind="spoon",
        breakable=True,
        fix="tape",
        clue="a tiny crack",
        sings="plink",
    ),
    "fork": Utensil(
        id="fork",
        label="fork",
        phrase="a bright tin fork",
        kind="fork",
        breakable=True,
        fix="straighten",
        clue="a bent tines",
        sings="clink",
    ),
    "ladle": Utensil(
        id="ladle",
        label="ladle",
        phrase="a round soup ladle",
        kind="ladle",
        breakable=True,
        fix="glue",
        clue="a loose handle",
        sings="clong",
    ),
}

GENDER_NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ada", "Zoe"],
    "boy": ["Leo", "Finn", "Ben", "Max", "Owen"],
}
HELPERS = ["mother", "father", "grandma", "grandpa"]
CULPRITS = ["cat", "dog", "brother", "sister", "wind"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
utensil(spoon).
utensil(fork).
utensil(ladle).

breakable(spoon).
breakable(fork).
breakable(ladle).

fix(spoon,tape).
fix(fork,straighten).
fix(ladle,glue).

can_break(U) :- utensil(U), breakable(U).
can_fix(U,F) :- fix(U,F).
valid(U,F) :- can_break(U), can_fix(U,F).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "kitchen"), asp.fact("table", "little_table")]
    for uid, u in UTENSILS.items():
        lines.append(asp.fact("utensil", uid))
        if u.breakable:
            lines.append(asp.fact("breakable", uid))
        lines.append(asp.fact("fix", uid, u.fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(u, UTENSILS[u].fix) for u in UTENSILS if UTENSILS[u].breakable}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness(params: StoryParams) -> None:
    if params.utensil not in UTENSILS:
        raise StoryError("Unknown utensil choice.")
    if params.culprit not in CULPRITS:
        raise StoryError("Unknown mystery culprit.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper choice.")


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GENDER_NAMES[gender])


def make_world(params: StoryParams) -> World:
    utensil = UTENSILS[params.utensil]
    world = World(SETTING)

    child = world.add(Entity(
        id=params.name, kind="character", type=params.gender, label=params.name,
        owner=None, caretaker=params.helper,
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=params.helper, label=params.helper,
    ))
    mystery = world.add(Entity(
        id="Mystery", kind="thing", type="mystery", label="mystery",
    ))
    tool = world.add(Entity(
        id=utensil.id, kind="thing", type=utensil.kind, label=utensil.label,
        phrase=utensil.phrase, owner=child.id, caretaker=helper.id,
        broken=True,
    ))
    culprit = world.add(Entity(
        id=params.culprit, kind="thing", type=params.culprit, label=params.culprit,
    ))

    # Act 1: setup
    world.say(
        f"At {world.setting.place}, {child.id} did know a little thing: "
        f"{child.pronoun('possessive').capitalize()} {tool.label} was broke."
    )
    world.say(
        f"It was {tool.phrase}, and it had made a sad little {utensil.sings} on the table."
    )
    world.say(
        f"{child.id} looked and looked, and said, "
        f'"Who can know how this broke?"'
    )

    # Act 2: mystery and conflict
    world.para()
    world.say(
        f"{helper.label.capitalize()} came by and knelt beside the crumbs and the cup."
    )
    world.say(
        f"They found {utensil.clue} near {world.setting.table}, but no one knew the whole tale."
    )
    world.say(
        f"Then {params.culprit} scurried in, and {child.id} frowned right so."
    )
    world.say(
        f'"Did you broke my {tool.label}?" {child.id} asked, and the room felt woe.'
    )
    culprit.blamed = True
    child.memes["cross"] = 1
    helper.memes["worry"] = 1
    world.say(
        f"{params.culprit.capitalize()} shook its head, and the blaming made a small conflict grow."
    )

    # Act 3: problem solving and resolution
    world.para()
    if params.culprit == "wind":
        world.say(
            f"Then the window was seen ajar; the wind had nudged the cloth and made the spoon fall."
        )
    elif params.culprit == "cat":
        world.say(
            f"A soft paw-print on the chair showed the cat had leapt too tall."
        )
    elif params.culprit == "dog":
        world.say(
            f"A wagging tail had bumped the table leg; that was the mystery after all."
        )
    elif params.culprit == "brother":
        world.say(
            f"A brother's toy truck was nearby, and its bump made the utensil slip and fall."
        )
    else:
        world.say(
            f"A sister had reached for a cookie jar, and the jar's tap made the utensil roll."
        )

    world.say(
        f"{helper.label.capitalize()} said, 'Let's solve this kindly, one clue at a time.'"
    )
    world.say(
        f"Together they learned the true cause, and the blaming stopped in time."
    )
    world.say(
        f"{child.id} said, 'Now I know,' and their face grew bright as day."
    )

    tool.repaired = True
    tool.broken = False
    world.say(
        f"They {utensil.fix}ed the {tool.label}, and it was good as new by day."
    )
    world.say(
        f"At last {child.id} smiled at {tool.phrase}, safe on {world.setting.table} to stay."
    )

    world.facts.update(
        child=child,
        helper=helper,
        utensil=tool,
        utensil_cfg=utensil,
        culprit=culprit,
        mystery=mystery,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    utensil = f["utensil_cfg"]
    return [
        f'Write a nursery-rhyme story about a child named {child.id} who knows a {utensil.label} has broke.',
        f"Tell a gentle mystery where {child.id} and a helper solve why the {utensil.label} broke, then fix it.",
        f"Write a short child-friendly story with a conflict about a broken {utensil.label} and a calm answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    utensil = f["utensil"]
    culprit = f["culprit"]

    return [
        QAItem(
            question=f"What did {child.id} know about {child.pronoun('possessive')} {utensil.label} at the start?",
            answer=f"{child.id} knew that {child.pronoun('possessive')} {utensil.label} was broke.",
        ),
        QAItem(
            question=f"What clue did {helper.label} find to help solve the mystery?",
            answer=f"{helper.label.capitalize()} found {UTENSILS[utensil.id].clue} near the table.",
        ),
        QAItem(
            question=f"Why did the room feel tense when {child.id} asked about the broken {utensil.label}?",
            answer=f"The room felt tense because {child.id} wondered if {culprit.id} had caused the break, and that made a small conflict.",
        ),
        QAItem(
            question=f"How did they solve the problem with the {utensil.label}?",
            answer=f"They looked at clues, learned what really happened, and {UTENSILS[utensil.id].fix}ed the {utensil.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    utensil = f["utensil_cfg"]
    return [
        QAItem(
            question="What is a utensil?",
            answer="A utensil is a tool used for eating or cooking, like a spoon, fork, or ladle.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not clear at first, so people look for clues to understand it.",
        ),
        QAItem(
            question=f"Why can a {utensil.label} be useful?",
            answer=f"A {utensil.label} is useful because people can use it when they eat or cook.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a helpful answer or fix after thinking and trying clues.",
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.broken:
            bits.append("broken=True")
        if e.found:
            bits.append("found=True")
        if e.repaired:
            bits.append("repaired=True")
        if e.blamed:
            bits.append("blamed=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme mystery about a broken utensil.")
    ap.add_argument("--utensil", choices=sorted(UTENSILS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(u.id, c) for u in UTENSILS.values() for c in CULPRITS if u.breakable]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.utensil and args.culprit and args.utensil not in UTENSILS:
        raise StoryError("Unknown utensil.")
    combos = valid_combos()
    if args.utensil:
        combos = [c for c in combos if c[0] == args.utensil]
    if args.culprit:
        combos = [c for c in combos if c[1] == args.culprit]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    utensil, culprit = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(utensil=utensil, culprit=culprit, helper=helper, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    reasonableness(params)
    world = make_world(params)
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


def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program_text("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for u in UTENSILS:
            for c in CULPRITS:
                p = StoryParams(
                    utensil=u,
                    culprit=c,
                    helper="mother",
                    name="Mia",
                    gender="girl",
                )
                samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
