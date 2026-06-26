#!/usr/bin/env python3
"""
A tiny whodunit story world set in a post office.

Premise:
- Someone at the post office loses a parcel.
- A strange, hideous-looking clue appears.
- The case turns on a twist: the clue was not a threat, but a note about sharing.
- The ending is happy because the missing item is returned and the helpers share the credit.

The world is simulated through typed entities with physical meters and emotional memes,
and the prose is driven by the evolving state rather than a frozen template.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"woman", "girl", "clerk"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "mailman"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    investigator: str
    helper: str
    clerk: str
    missing_item: str
    clue_name: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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

INVESTIGATORS = [
    ("Mira", "girl"),
    ("Jules", "boy"),
    ("Nina", "girl"),
    ("Owen", "boy"),
]

HELPERS = [
    ("Pip", "child"),
    ("Tess", "child"),
    ("Rory", "child"),
    ("June", "child"),
]

CLERKS = [
    ("Grant", "clerk"),
    ("Harper", "clerk"),
]

MISSING_ITEMS = {
    "parcel": {
        "label": "parcel",
        "phrase": "a small parcel with a blue string",
        "tags": {"post office", "sharing"},
    },
    "stamp_book": {
        "label": "stamp book",
        "phrase": "a little stamp book with bright corners",
        "tags": {"post office", "sharing"},
    },
    "letter": {
        "label": "letter",
        "phrase": "a sealed letter in a yellow envelope",
        "tags": {"post office"},
    },
}

CLUES = {
    "hideous_smudge": {
        "label": "hideous smudge",
        "phrase": "a hideous, lopsided smudge on the counter",
        "reveal": "ink",
        "tags": {"hideous", "twist"},
    },
    "wont_note": {
        "label": "wont note",
        "phrase": "a tiny note that said 'wont'",
        "reveal": "sharing",
        "tags": {"wont", "sharing", "twist"},
    },
    "paper_flower": {
        "label": "paper flower",
        "phrase": "a paper flower folded from a receipt",
        "reveal": "sharing",
        "tags": {"sharing", "twist"},
    },
}

POST_OFFICE_DETAIL = [
    "The post office smelled like paper, ink, and warm dust.",
    "Rows of little boxes lined the wall, and a brass bell waited by the door.",
    "The parcel shelf was neat, except for one crooked space where something should have been.",
]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def validate_params(params: StoryParams) -> None:
    if params.investigator == params.helper:
        raise StoryError("investigator and helper must be different characters.")
    if params.clue_name not in CLUES:
        raise StoryError("unknown clue.")
    if params.missing_item not in MISSING_ITEMS:
        raise StoryError("unknown missing item.")


def infer_twist(clue_name: str) -> str:
    if clue_name == "wont_note":
        return "sharing"
    if clue_name == "hideous_smudge":
        return "ink"
    return "sharing"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World()

    investigator_name, investigator_type = next((n, t) for n, t in INVESTIGATORS if n == params.investigator)
    helper_name, _ = next((n, t) for n, t in HELPERS if n == params.helper)
    clerk_name, clerk_type = next((n, t) for n, t in CLERKS if n == params.clerk)

    investigator = world.add(Entity(
        id="investigator",
        kind="character",
        type=investigator_type,
        label=investigator_name,
        memes={"curious": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="child",
        label=helper_name,
        memes={"curious": 1.0, "helpful": 1.0, "joy": 0.0},
    ))
    clerk = world.add(Entity(
        id="clerk",
        kind="character",
        type=clerk_type,
        label=clerk_name,
        memes={"calm": 1.0, "pride": 0.0},
    ))
    missing = MISSING_ITEMS[params.missing_item]
    item = world.add(Entity(
        id="missing_item",
        kind="thing",
        type=params.missing_item,
        label=missing["label"],
        phrase=missing["phrase"],
        owner=investigator.id,
        held_by=None,
        meters={"lost": 1.0},
        tags=set(missing["tags"]),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=CLUES[params.clue_name]["label"],
        phrase=CLUES[params.clue_name]["phrase"],
        meters={"noticed": 0.0},
        tags=set(CLUES[params.clue_name]["tags"]),
    ))
    world.facts.update(
        investigator=investigator,
        helper=helper,
        clerk=clerk,
        item=item,
        clue=clue,
        twist=infer_twist(params.clue_name),
        place="post office",
    )
    return world


def tell_story(world: World) -> None:
    iv = world.facts["investigator"]
    hlp = world.facts["helper"]
    cl = world.facts["clerk"]
    item = world.facts["item"]
    clue = world.facts["clue"]
    twist = world.facts["twist"]

    world.say(f"{iv.label} went to the post office because {iv.pronoun('possessive')} {item.label} was missing.")
    world.say(POST_OFFICE_DETAIL[0] + " " + POST_OFFICE_DETAIL[1])

    world.para()
    world.say(f"{iv.label} noticed {clue.phrase}.")
    world.say(f"{iv.pronoun().capitalize()} thought it looked hideous, but {cl.label} frowned and said it might matter.")
    world.say(f"{hlp.label} leaned closer, because {hlp.pronoun('subject')} liked sharing clues and solving puzzles together.")

    # State updates: suspicion, attention, and the twist.
    iv.memes["worry"] = 1.0
    clue.meters["noticed"] = 1.0
    if twist == "ink":
        clue.meters["ink"] = 1.0
        world.say(f"The clue turned out to be only old ink, and the hideous look was a trick of the light.")
    else:
        clue.meters["sharing"] = 1.0
        world.say(f"The clue was a twist: it pointed to sharing, not stealing.")
        world.say(f"It meant someone had moved the {item.label} so both counters could use the same table.")

    world.para()
    if twist == "sharing":
        item.held_by = cl.id
        item.meters["lost"] = 0.0
        cl.memes["pride"] = 1.0
        hlp.memes["joy"] = 1.0
        iv.memes["relief"] = 1.0
        world.say(f"{cl.label} gave back the {item.label} with an apology and a smile.")
        world.say(f"{iv.label}, {hlp.label}, and {cl.label} shared the blame, then shared the laugh.")
        world.say(f"In the end, the missing {item.label} was on the counter again, and the three of them stood together in a happy ending.")
    else:
        item.held_by = iv.id
        item.meters["lost"] = 0.0
        iv.memes["relief"] = 1.0
        world.say(f"{cl.label} found the {item.label} behind a stack of forms and handed it back at once.")
        world.say(f"{iv.label} smiled, {hlp.label} clapped, and the case was over before the bell could ring again.")
        world.say(f"It was a happy ending: the hideous clue had only been old ink, and the post office was peaceful again.")

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    iv = world.facts["investigator"]
    item = world.facts["item"]
    clue = world.facts["clue"]
    return [
        f"Write a short whodunit story set in a post office where {iv.label} must solve a missing {item.label}.",
        f"Tell a child-friendly mystery with a hideous-looking clue, a twist, and a happy ending.",
        f"Write a story about sharing in a post office, where a strange clue changes who seems guilty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    iv = world.facts["investigator"]
    hlp = world.facts["helper"]
    cl = world.facts["clerk"]
    item = world.facts["item"]
    clue = world.facts["clue"]
    twist = world.facts["twist"]

    return [
        QAItem(
            question=f"Who was trying to solve the mystery at the post office?",
            answer=f"{iv.label} was the investigator in the story, and {iv.pronoun('subject')} tried to find the missing {item.label}.",
        ),
        QAItem(
            question=f"What strange clue did {iv.label} notice?",
            answer=f"{iv.label} noticed {clue.phrase}. It looked hideous at first, so everyone paused to think.",
        ),
        QAItem(
            question=f"How did the story turn into a twist?",
            answer=f"The twist was about {twist}. What looked suspicious at first ended up helping the characters understand what really happened.",
        ),
        QAItem(
            question=f"Who helped share the clue-solving?",
            answer=f"{hlp.label} helped by looking closely and sharing ideas, while {cl.label} explained what was going on at the counter.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, because the missing {item.label} came back and everyone shared the relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a post office for?",
            answer="A post office is a place where people send letters and packages, buy stamps, and get help with mail.",
        ),
        QAItem(
            question="Why do people share clues in a mystery?",
            answer="People share clues so everyone can think together and figure out what really happened.",
        ),
        QAItem(
            question="What does a happy ending mean?",
            answer="A happy ending means the trouble gets fixed and the characters feel safe, calm, or joyful again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/4.

valid_story(I,H,C,Item) :- investigator(I), helper(H), clerk(C), missing_item(Item),
                           I != H, I != C, H != C.

twist_from_clue(wont_note, sharing).
twist_from_clue(hideous_smudge, ink).
twist_from_clue(paper_flower, sharing).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines = []
    for name, _typ in INVESTIGATORS:
        lines.append(asp.fact("investigator", name))
    for name, _typ in HELPERS:
        lines.append(asp.fact("helper", name))
    for name, _typ in CLERKS:
        lines.append(asp.fact("clerk", name))
    for key in MISSING_ITEMS:
        lines.append(asp.fact("missing_item", key))
    for key in CLUES:
        lines.append(asp.fact("clue", key))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    valid = sorted(set(asp.atoms(model, "valid_story")))
    expected = []
    for i, _ in INVESTIGATORS:
        for h, _ in HELPERS:
            for c, _ in CLERKS:
                for item in MISSING_ITEMS:
                    if len({i, h, c}) == 3:
                        expected.append((i, h, c, item))
    expected = sorted(expected)
    if valid != expected:
        print("MISMATCH between ASP and Python constraints.")
        print("ASP:", valid)
        print("PY :", expected)
        return 1
    print(f"OK: ASP parity verified ({len(valid)} combinations).")
    return 0


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world set in a post office.")
    ap.add_argument("--investigator", choices=[n for n, _ in INVESTIGATORS])
    ap.add_argument("--helper", choices=[n for n, _ in HELPERS])
    ap.add_argument("--clerk", choices=[n for n, _ in CLERKS])
    ap.add_argument("--missing-item", choices=list(MISSING_ITEMS))
    ap.add_argument("--clue", dest="clue_name", choices=list(CLUES))
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
    investigator = args.investigator or rng.choice([n for n, _ in INVESTIGATORS])
    helper_choices = [n for n, _ in HELPERS if n != investigator]
    helper = args.helper or rng.choice(helper_choices)
    clerk = args.clerk or rng.choice([n for n, _ in CLERKS])
    missing_item = args.missing_item or rng.choice(list(MISSING_ITEMS))
    clue_name = args.clue_name or rng.choice(list(CLUES))
    return StoryParams(
        investigator=investigator,
        helper=helper,
        clerk=clerk,
        missing_item=missing_item,
        clue_name=clue_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, ent in world.entities.items():
        bits = []
        if ent.label:
            bits.append(f"label={ent.label}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.held_by:
            bits.append(f"held_by={ent.held_by}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"{eid}: {ent.kind}/{ent.type} " + " ".join(bits))
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


CURATED = [
    StoryParams(investigator="Mira", helper="Pip", clerk="Grant", missing_item="parcel", clue_name="wont_note"),
    StoryParams(investigator="Jules", helper="Tess", clerk="Harper", missing_item="stamp_book", clue_name="hideous_smudge"),
    StoryParams(investigator="Nina", helper="Rory", clerk="Grant", missing_item="letter", clue_name="paper_flower"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid story combinations")
        for a in atoms:
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.investigator} / {p.helper} / {p.clerk} / {p.missing_item} / {p.clue_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
