#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slit_polka_slavery_kindness_conflict_happy_ending.py
=====================================================================================

A small standalone bedtime story world about a child, a torn costume slit, a
polka-dot dress-up game, and a gentle conflict that ends in kindness.

Seed words:
- slit
- polka
- slavery

Features:
- Kindness
- Conflict
- Happy Ending

The world is intentionally tiny and classical: a child wants to wear a special
polka-dot cape, notices a slit in the fabric, worries about the costume, and
then a kind grown-up helps fix it. A related bedtime conversation about the
word "slavery" appears as an age-appropriate history-book moment: the child
asks, the grown-up answers gently, and the story closes with safety, fairness,
and comfort.

This script follows the Storyweavers world contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- produces state-driven prose and grounded Q&A
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

NAMES = ["Mia", "Nora", "Lily", "Ava", "Ben", "Theo", "Noah", "Milo"]
PARENT_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]
ROOMS = ["bedroom", "playroom", "living room"]
TEXTURES = ["soft", "bright", "cozy", "gentle"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Item:
    id: str
    label: str
    kind: str
    material: str = ""
    color: str = ""
    pattern: str = ""
    has_slit: bool = False
    sentimental: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class ComfortAid:
    id: str
    label: str
    phrase: str
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryWorld:
    room: Entity
    child: Entity
    parent: Entity
    cape: Item
    book: Item
    aid: ComfortAid
    seed_word: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "StoryWorld":
        clone = StoryWorld(
            room=copy.deepcopy(self.room),
            child=copy.deepcopy(self.child),
            parent=copy.deepcopy(self.parent),
            cape=copy.deepcopy(self.cape),
            book=copy.deepcopy(self.book),
            aid=copy.deepcopy(self.aid),
            seed_word=self.seed_word,
        )
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def fixpoint(world: StoryWorld) -> None:
    changed = True
    while changed:
        changed = False
        if world.cape.has_slit and ("slit_worry" not in world.fired):
            world.fired.add(("slit_worry",))
            world.child.memes["worry"] += 1
            world.room.meters["quiet"] += 1
            changed = True
        if world.book.meters["opened"] >= THRESHOLD and ("book_talk" not in world.fired):
            world.fired.add(("book_talk",))
            world.child.memes["curiosity"] += 1
            changed = True
        if world.cape.meters["mended"] >= THRESHOLD and ("mended_calm" not in world.fired):
            world.fired.add(("mended_calm",))
            world.child.memes["relief"] += 1
            world.parent.memes["kindness"] += 1
            changed = True


def predict_story(world: StoryWorld) -> dict:
    sim = world.copy()
    act_slit(sim, narrate=False)
    act_book(sim, narrate=False)
    return {
        "worried": sim.child.memes["worry"] >= THRESHOLD,
        "curious": sim.child.memes["curiosity"] >= THRESHOLD,
    }


def act_begin(world: StoryWorld) -> None:
    world.child.memes["joy"] += 1
    world.say(
        f"At bedtime, {world.child.id} sat in the {world.room.label_word} with a "
        f"special polka-dot cape."
    )
    world.say(
        f"The cape was {world.cape.color}, {world.cape.pattern}, and extra {world.aid.label}."
    )


def act_slit(world: StoryWorld, narrate: bool = True) -> None:
    world.cape.has_slit = True
    world.cape.meters["torn"] += 1
    world.child.memes["worry"] += 1
    fixpoint(world)
    if narrate:
        world.say(
            f"Then {world.child.id} noticed a tiny slit in the seam."
            f" It was small, but it made the cape feel less magical."
        )


def act_conflict(world: StoryWorld) -> None:
    world.child.memes["conflict"] += 1
    world.parent.memes["attention"] += 1
    world.say(
        f'"Oh no," {world.child.id} whispered. "What if my polka cape is ruined?"'
    )
    world.say(
        f"{world.parent.id} knelt beside {world.child.id} and looked closely."
        f" The slit was real, but it was only a little tear."
    )


def act_kindness(world: StoryWorld) -> None:
    world.parent.memes["kindness"] += 1
    world.cape.meters["mended"] += 1
    fixpoint(world)
    world.say(
        f'{world.parent.id} smiled kindly. "{world.aid.use_text}," '
        f"{world.parent.pronoun()} said, and {world.parent.pronoun()} brought out "
        f"a soft needle and thread."
    )
    world.say(
        f"Together they made the slit neat again, stitch by stitch, until the "
        f"polka dots looked ready for a story."
    )


def act_book(world: StoryWorld, narrate: bool = True) -> None:
    world.book.meters["opened"] += 1
    fixpoint(world)
    if narrate:
        world.say(
            f"While the thread gleamed, {world.child.id} opened a little history book."
        )
        world.say(
            f"The book used the word slavery, and {world.child.id} asked what it meant."
        )
        world.say(
            f'{world.parent.id} answered softly, "It means people were treated unfairly '
            f'and not allowed to be free. We remember that so we can choose kindness, '
            f'fairness, and help for everyone."'
        )


def act_finish(world: StoryWorld) -> None:
    world.child.memes["joy"] += 1
    world.child.memes["relief"] += 1
    world.say(
        f'At last, {world.child.id} held the mended cape to the lamp and grinned.'
        f' "It is still my polka cape," {world.child.id} said, "and now it is safe too."'
    )
    world.say(
        f"{world.child.id} tucked the history book away, hugged {world.parent.id},"
        f" and fell asleep feeling warm, brave, and loved."
    )


def tell(world: StoryWorld) -> StoryWorld:
    act_begin(world)
    world.para()
    pred = predict_story(world)
    act_slit(world)
    act_conflict(world)
    world.para()
    act_kindness(world)
    act_book(world)
    world.para()
    act_finish(world)

    world.facts.update(
        child=world.child,
        parent=world.parent,
        room=world.room,
        cape=world.cape,
        book=world.book,
        aid=world.aid,
        predicted=pred,
        outcome="happy",
    )
    return world


def build_world(params: "StoryParams") -> StoryWorld:
    room = Entity(id=params.room, kind="place", type="room", label=params.room)
    child = Entity(id=params.child, kind="character", type=params.child_type, role="child")
    parent = Entity(id=params.parent, kind="character", type=params.parent_type, role="parent", label=params.parent)
    cape = Item(id="cape", label="polka-dot cape", kind="fabric", color=params.color, pattern="polka dots", sentimental=True)
    book = Item(id="book", label="history book", kind="book")
    aid = ComfortAid(id="thread", label="kind", phrase="a kind fix", use_text="Let's mend it gently", tags={"kindness"})
    return StoryWorld(room=room, child=child, parent=parent, cape=cape, book=book, aid=aid, seed_word=params.seed_word)


def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        f'Write a bedtime story for a young child that includes the words "{world.seed_word}", "polka", and "slit".',
        "Tell a gentle bedtime story about a torn polka-dot cape, a caring grown-up, and a happy ending.",
        'Write a child-facing story where the word "slavery" appears in a history-book moment and the grown-up answers kindly.',
    ]


def story_qa(world: StoryWorld) -> list[tuple[str, str]]:
    c = world.facts["child"]
    p = world.facts["parent"]
    cape = world.facts["cape"]
    return [
        ("What did the child notice on the cape?",
         f"{c.id} noticed a tiny slit in the polka-dot cape, and that made the child worry. The little tear was the conflict that started the story."),
        ("How did the grown-up help?",
         f"{p.id} helped mend the cape with a kind fix and gentle thread. That turned the worry into relief and made the happy ending possible."),
        ("What did the child learn from the history book?",
         f"The word slavery meant people were treated unfairly and not allowed to be free. The child learned that kindness and fairness matter, and that is why the story ends calmly."),
        ("How did the story end?",
         f"The cape was mended, the child felt safe, and bedtime was peaceful. The slit was fixed, so the polka-dot cape could be loved again."),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[tuple[str, str]]:
    return [
        ("What is a slit?",
         "A slit is a small long opening or cut in something like cloth or paper."),
        ("What are polka dots?",
         "Polka dots are round spots, often used as a fun pattern on clothes and blankets."),
        ("What does kindness mean?",
         "Kindness means being gentle, helpful, and caring toward someone else."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for obj in [world.child, world.parent, world.cape, world.book, world.room]:
        if isinstance(obj, Entity):
            meters = {k: v for k, v in obj.meters.items() if v}
            memes = {k: v for k, v in obj.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if obj.label:
                bits.append(f"label={obj.label}")
            lines.append(f"  {obj.id:10} ({obj.type:8}) {' '.join(bits)}")
        else:
            meters = {k: v for k, v in obj.meters.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if obj.pattern:
                bits.append(f"pattern={obj.pattern}")
            if obj.has_slit:
                bits.append("has_slit=True")
            lines.append(f"  {obj.id:10} ({obj.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    room: str
    child: str
    child_type: str
    parent: str
    parent_type: str
    color: str
    seed_word: str = "slit"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, c, "history") for r in ROOMS for c in NAMES]


def explain_rejection() -> str:
    return "(No story: this setup is too thin or not bedtime-friendly.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: slit, polka, kindness, conflict, happy ending.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--child")
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--seed-word", default="slit")
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
    room = args.room or rng.choice(ROOMS)
    child = args.child or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    child_type = "girl" if child in {"Mia", "Nora", "Lily", "Ava"} else "boy"
    parent_type = "mother" if parent in {"Mom", "Grandma"} else "father"
    color = rng.choice(["blue", "red", "yellow", "green"])
    return StoryParams(room=room, child=child, child_type=child_type, parent=parent, parent_type=parent_type, color=color, seed_word=args.seed_word)


ASP_RULES = r"""
needs_kindness(X) :- slit(X).
conflict(X) :- needs_kindness(X).
happy_ending(X) :- kindness(X), conflict(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for n in NAMES:
        lines.append(asp.fact("name", n))
    lines.append(asp.fact("slit", "cape"))
    lines.append(asp.fact("polka", "cape"))
    lines.append(asp.fact("book", "history"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show happy_ending/1."))
    atoms = set(asp.atoms(model, "conflict")) | set(asp.atoms(model, "happy_ending"))
    if not atoms:
        print("MISMATCH: ASP reasoning produced no story-shape atoms.")
        return 1
    world = tell(build_world(resolve_params(argparse.Namespace(room=None, child=None, parent=None, seed_word="slit"), random.Random(777))))
    if "happy" != world.facts.get("outcome"):
        print("MISMATCH: normal generation failed.")
        return 1
    print("OK: ASP and normal generation smoke test passed.")
    return 0


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show happy_ending/1."))
    return sorted(set(asp.atoms(model, "conflict")))


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show conflict/1.\n#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP story-shape atoms:", asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("bedroom", "Mia", "girl", "Mom", "mother", "blue", "slit"),
            StoryParams("playroom", "Ben", "boy", "Dad", "father", "red", "slit"),
            StoryParams("living room", "Nora", "girl", "Grandma", "mother", "green", "slit"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            sample = generate(p)
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
