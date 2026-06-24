#!/usr/bin/env python3
"""
storyworlds/worlds/barricade_mark_gerund_misunderstanding_happy_ending_nursery.py
=================================================================================

A small standalone storyworld in a Nursery Rhyme style: a child notices a mark,
misunderstands it as a barrier, and the misunderstanding is cleared with a happy
ending. Typed entities carry physical meters and emotional memes, state drives the
prose, and an inline ASP twin mirrors the Python reasonableness gate.

Seed idea:
---
A little child sees a mark on the nursery gate and thinks it means "keep out."
The child stacks blocks to make a barricade, which confuses a friend. A grown-up
explains that the mark was only a note saying "keep the toys tidy," not a secret
warning. The barricade comes down, the toys get sorted, and everyone laughs in a
soft, rhyming ending.

Contract targets:
- include the seed words "barricade" and "mark-gerund"
- setting is a nursery / playroom
- features: misunderstanding, happy ending
- style: nursery rhyme
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

TITLE = "Nursery Rhyme Storyworld: The Mark-Gerend Barricade Misunderstanding"

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Nursery:
    id: str
    name: str
    place: str
    rhyme: str
    tidying_word: str
    note_word: str
    barrier_word: str
    toy_word: str


@dataclass
class Mark:
    id: str
    label: str
    meaning: str
    looks_like: str
    is_note: bool = True
    is_warning: bool = False
    is_barrier: bool = False


@dataclass
class Barricade:
    id: str
    label: str
    made_of: str
    blocks: str
    heavy: bool = True


@dataclass
class Adult:
    id: str
    label: str
    tone: str
    explanation: str
    tidy_help: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NURSERIES = {
    "sunroom": Nursery(
        id="sunroom",
        name="the bright nursery",
        place="by the little toy shelf",
        rhyme="soft and bright",
        tidying_word="tidy",
        note_word="mark",
        barrier_word="barricade",
        toy_word="blocks",
    ),
    "playroom": Nursery(
        id="playroom",
        name="the merry playroom",
        place="near the window seat",
        rhyme="sing-song and light",
        tidying_word="sort",
        note_word="mark",
        barrier_word="barricade",
        toy_word="wooden bricks",
    ),
}

MARKS = {
    "tidy_note": Mark(
        id="tidy_note",
        label="a little mark-gerund note",
        meaning="keep the toys tidy",
        looks_like="a tiny ribboned note",
        is_note=True,
        is_warning=False,
        is_barrier=False,
    ),
    "do_not_touch": Mark(
        id="do_not_touch",
        label="a mark-gerund sign",
        meaning="do not touch the paint",
        looks_like="a red paper tag",
        is_note=True,
        is_warning=True,
        is_barrier=False,
    ),
}

BARRICADES = {
    "blocks": Barricade(
        id="blocks",
        label="a block barricade",
        made_of="toy blocks",
        blocks="the little path",
    ),
    "chairs": Barricade(
        id="chairs",
        label="a chair barricade",
        made_of="small chairs",
        blocks="the doorway",
    ),
}

ADULTS = {
    "parent": Adult(
        id="parent",
        label="the parent",
        tone="gentle",
        explanation="the mark was only a note about tidying toys",
        tidy_help="showed how to sort the toys back into neat rows",
    ),
}

KIDS = ["Nina", "Milo", "Pip", "Lily", "Toby", "Ruby", "Ada", "Finn"]


@dataclass
class StoryParams:
    nursery: str
    mark: str
    barricade: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str = "parent"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a mark and a barricade misunderstanding.")
    ap.add_argument("--nursery", choices=NURSERIES)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--barricade", choices=BARRICADES)
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
    nursery = args.nursery or rng.choice(list(NURSERIES))
    mark = args.mark or rng.choice(list(MARKS))
    barricade = args.barricade or rng.choice(list(BARRICADES))
    c1 = rng.choice(KIDS)
    c2 = rng.choice([k for k in KIDS if k != c1])
    g1 = rng.choice(["girl", "boy"])
    g2 = rng.choice(["girl", "boy"])
    return StoryParams(nursery=nursery, mark=mark, barricade=barricade,
                       child1=c1, child1_gender=g1, child2=c2, child2_gender=g2)


def _build_world(params: StoryParams) -> World:
    n = NURSERIES[params.nursery]
    m = MARKS[params.mark]
    b = BARRICADES[params.barricade]
    adult = ADULTS["parent"]
    w = World()
    c1 = w.add(Entity(params.child1, kind="character", type=params.child1_gender))
    c2 = w.add(Entity(params.child2, kind="character", type=params.child2_gender))
    parent = w.add(Entity(adult.id, kind="character", type="parent", label=adult.label))
    nursery = w.add(Entity(n.id, type="room", label=n.name, attrs={"place": n.place}))
    note = w.add(Entity(m.id, type="thing", label=m.label, attrs={"meaning": m.meaning}))
    barricade = w.add(Entity(b.id, type="thing", label=b.label, attrs={"made_of": b.made_of}))
    w.facts.update(
        nursery=n, mark=m, barricade=b, adult=adult,
        child1=c1, child2=c2, parent=parent,
        room=nursery, note=note, barrier=barricade,
        misunderstanding=True, resolved=True, happy_ending=True,
    )
    c1.memes["curiosity"] = 2.0
    c2.memes["worry"] = 1.0
    parent.memes["warmth"] = 2.0
    nursery.meters["tidy"] = 0.0
    note.meters["seen"] = 1.0
    barricade.meters["blocking"] = 1.0
    return w


def tell(world: World) -> None:
    n: Nursery = world.facts["nursery"]
    m: Mark = world.facts["mark"]
    b: Barricade = world.facts["barricade"]
    a: Adult = world.facts["adult"]
    c1: Entity = world.facts["child1"]
    c2: Entity = world.facts["child2"]

    world.say(f"In {n.name}, so soft and bright, {c1.id} and {c2.id} played just right.")
    world.say(f"By the shelf there lay {m.label}, like {m.looks_like}.")
    world.say(
        f"{c1.id} thought, 'Oh dear, that means stop!' and built {b.label} to block the top."
    )
    world.say(
        f"{c2.id} peeped round the side and gave a little startled sigh; "
        f"the toy path hid, the dolls were shy."
    )
    c1.memes["anxious"] = c1.memes.get("anxious", 0.0) + 1.0
    c2.memes["confused"] = c2.memes.get("confused", 0.0) + 1.0
    world.facts["misunderstanding"] = True
    world.para()
    world.say(
        f"Then {a.label} came with a smile so mild and said, "
        f"'{m.meaning}.'"
    )
    world.say(
        f"'{m.label}' was only a {n.note_word}, not a barrier bold and grim; "
        f"it helped the toys stay neat and trim."
    )
    world.say(
        f"So down came the {n.barrier_word}, block by block, with clatter, tap, and cheer; "
        f"the path went free, the room grew neat, and laughter filled the air."
    )
    b.meters["blocking"] = 0.0
    n.meters["tidy"] = 1.0
    c1.memes["relief"] = c1.memes.get("relief", 0.0) + 2.0
    c2.memes["relief"] = c2.memes.get("relief", 0.0) + 2.0
    c1.memes["joy"] = c1.memes.get("joy", 0.0) + 2.0
    c2.memes["joy"] = c2.memes.get("joy", 0.0) + 2.0
    world.para()
    world.say(
        f"'{m.meaning},' said {a.label}, and {a.tidy_help}; "
        f"then all the toys sat neat again, in rows of rainbow grace."
    )
    world.say(
        f"And that is how the mark-gerund mystery ended -- sweet and clear -- "
        f"with one brave note, one small mistake, and a happy ending here."
    )


def generation_prompts(world: World) -> list[str]:
    n: Nursery = world.facts["nursery"]
    m: Mark = world.facts["mark"]
    b: Barricade = world.facts["barricade"]
    c1: Entity = world.facts["child1"]
    c2: Entity = world.facts["child2"]
    return [
        f"Write a nursery-rhyme style story set in {n.name} where {c1.id} misreads {m.label} and makes {b.label}.",
        f"Tell a gentle misunderstanding story: {c1.id} thinks {m.label} means danger, but it really means {m.meaning}.",
        f"Create a happy ending tale in rhyme where a barricade is taken apart after a grown-up explains the mark-gerund note.",
    ]


def story_qa(world: World) -> list[QAItem]:
    n: Nursery = world.facts["nursery"]
    m: Mark = world.facts["mark"]
    b: Barricade = world.facts["barricade"]
    c1: Entity = world.facts["child1"]
    c2: Entity = world.facts["child2"]
    a: Adult = world.facts["adult"]
    return [
        QAItem(
            question=f"What did {c1.id} think the mark meant?",
            answer=f"{c1.id} thought it meant to stop or keep out, so {c1.id} built {b.label}.",
        ),
        QAItem(
            question=f"What did the grown-up say about {m.label}?",
            answer=f"{a.label} said it was only there to show that {m.meaning}.",
        ),
        QAItem(
            question=f"What happened to the {b.label} at the end?",
            answer=f"It came down block by block, and the path opened again in {n.name}.",
        ),
        QAItem(
            question=f"How did {c2.id} feel when the misunderstanding was fixed?",
            answer=f"{c2.id} went from confused to relieved, then joined the happy play again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barricade?",
            answer="A barricade is a barrier made to block a path or doorway.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means another.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets fixed and everyone is safe or smiling at the end.",
        ),
        QAItem(
            question="What does a nursery rhyme usually sound like?",
            answer="It often sounds soft, bouncy, and sing-song, with simple words and a gentle rhythm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
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


ASP_RULES = r"""
misunderstanding :- mark(note), child(misread), barricade(made).
happy_ending :- misunderstanding, adult(explain), barricade_removed, toys_tidy.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for nid in NURSERIES:
        lines.append(asp.fact("nursery", nid))
    for mid, m in MARKS.items():
        lines.append(asp.fact("mark", mid))
        if m.is_note:
            lines.append(asp.fact("note", mid))
        if m.is_warning:
            lines.append(asp.fact("warning", mid))
    for bid in BARRICADES:
        lines.append(asp.fact("barricade", bid))
        lines.append(asp.fact("made", bid))
    lines.append(asp.fact("adult", "parent"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams("sunroom", "tidy_note", "blocks", "Nina", "girl", "Milo", "boy"),
    StoryParams("playroom", "do_not_touch", "chairs", "Lily", "girl", "Toby", "boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        nursery=args.nursery or rng.choice(list(NURSERIES)),
        mark=args.mark or rng.choice(list(MARKS)),
        barricade=args.barricade or rng.choice(list(BARRICADES)),
        child1=rng.choice(KIDS),
        child1_gender=rng.choice(["girl", "boy"]),
        child2=rng.choice(KIDS),
        child2_gender=rng.choice(["girl", "boy"]),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show misunderstanding/0.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
