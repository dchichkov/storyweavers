#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/army_diameter_bookstore_sharing_myth.py
=======================================================================

A standalone story world for a tiny mythic bookstore domain: a child finds a
stack of picture-books with an "army" theme, a strange talk about "diameter,"
and learns that sharing a rare book helps everyone enjoy the same story.

The story is built as a small simulation with typed entities, physical meters,
and emotional memes. The world is kept child-facing and concrete: a short
opening at a bookstore, a tension beat over one scarce book, a sharing turn,
and an ending image where the shelf feels calmer and the children have both
read.

This world is intentionally compact and classical: one setting, one scarce
object, one helper, one resolution.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    shelves: str
    air: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Book:
    id: str
    label: str
    phrase: str
    theme: str
    shared: bool = False
    rare: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharePlan:
    id: str
    method: str
    effect: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["want"] < THRESHOLD:
            continue
        sig = ("lonely", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["restless"] += 1
        out.append("")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    book = world.entities.get("book")
    if not book or book.meters["held"] < THRESHOLD:
        return out
    readers = [e for e in world.entities.values() if e.role in {"child_a", "child_b"}]
    if len(readers) < 2:
        return out
    if book.meters["shared"] >= THRESHOLD:
        return out
    if all(r.memes["kind"] >= THRESHOLD for r in readers):
        sig = ("share", book.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        book.meters["shared"] += 1
        for r in readers:
            r.memes["joy"] += 1
            r.memes["calm"] += 1
        out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("lonely", "social", _r_lonely), Rule("share", "social", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_need(need: Need) -> str:
    return f"{need.label} because {need.reason}"


def can_share(book: Book, plan: SharePlan) -> bool:
    return book.shared and plan.id in {"pass_along", "read_together", "divide_time"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for need_id in NEEDS:
            for book_id, book in BOOKS.items():
                if book.shared and need_id in {"crowd", "quiet"}:
                    combos.append((setting_id, need_id, book_id))
    return combos


def tell(setting: Setting, book: Book, need: Need, plan: SharePlan,
         child_a: str = "Mira", child_a_type: str = "girl",
         child_b: str = "Niko", child_b_type: str = "boy",
         keeper: str = "Librarian", keeper_type: str = "woman") -> World:
    world = World(setting)
    a = world.add(Entity(id=child_a, kind="character", type=child_a_type, role="child_a"))
    b = world.add(Entity(id=child_b, kind="character", type=child_b_type, role="child_b"))
    adult = world.add(Entity(id=keeper, kind="character", type=keeper_type, role="keeper", label="the librarian"))
    story_book = world.add(Entity(id="book", kind="thing", type="book", label=book.label,
                                  traits=["rare"]))
    a.memes["want"] = 1.0
    b.memes["want"] = 1.0
    a.memes["kind"] = 1.0
    b.memes["kind"] = 1.0
    story_book.meters["held"] = 1.0

    world.say(
        f"In a bookstore with {setting.shelves}, {a.id} and {b.id} wandered under "
        f"{setting.air}. On a high table sat {book.phrase}, and the cover showed an army "
        f"marching in a circle the size of a great diameter."
    )
    world.say(
        f'"Look," said {a.id}, "the army in the tale is tiny, but the circle is huge." '
        f'{b.id} nodded. "It feels like a myth book," {b.pronoun()} said, and both children '
        f'leaned closer.'
    )

    world.para()
    a.memes["want"] += 1
    b.memes["want"] += 1
    world.say(
        f"But only one copy was there. {a.id} reached first, and {b.id} wanted {need.phrase}. '
        f'The room felt a little tight, like a crowded story."
    )
    if need.id == "crowd":
        world.say("The army story seemed to call for many eyes, not only one pair.")
    else:
        world.say("Both children wanted the same quiet page at the same time.")

    world.para()
    world.say(
        f'{b.id} took a breath and said, "{plan.method}." {a.id} listened, '
        f'and {adult.id} smiled from behind the desk.'
    )
    a.memes["kind"] += 1
    b.memes["kind"] += 1
    if can_share(book, plan):
        book.meters["shared"] += 1
        world.say(
            f"They {plan.effect}. First one child read, then the other, and the librarian '
            f'turned the page slowly so nobody missed the pictures."
        )
        world.say(
            f"By the end, the book felt lighter in their hands, and the army in the myth "
            f"seemed less lonely because it had two readers at once."
        )
        world.say(
            f'{plan.ending}. {a.id} and {b.id} left the bookstore with the same bright grin, '
            f'and the shelf was calm again.'
        )
    else:
        world.say(
            f"But the plan did not fit the book, so the children had to keep waiting."
        )

    world.facts.update(
        child_a=a,
        child_b=b,
        adult=adult,
        book=story_book,
        setting=setting,
        book_cfg=book,
        need=need,
        plan=plan,
        shared=book.shared,
    )
    return world


SETTINGS = {
    "bookstore": Setting("bookstore", "a cozy bookstore", "rows of tall shelves", "warm lamp-light",
                         tags={"bookstore"}),
}

BOOKS = {
    "myth_atlas": Book("myth_atlas", "a myth book", "a thick myth book with gold edges",
                       theme="myth", shared=True, rare=True, tags={"myth", "book"}),
    "army_story": Book("army_story", "an army picture-book", "a picture-book about an army of ants",
                       theme="myth", shared=True, rare=False, tags={"army", "book"}),
    "circle_book": Book("circle_book", "a round-shelf legend", "a legend book about a circle and its diameter",
                        theme="myth", shared=True, rare=True, tags={"diameter", "myth"}),
}

NEEDS = {
    "crowd": Need("crowd", "a turn for both children", "the next turn",
                  "the book had only one copy, but both wanted the story",
                  tags={"sharing"}),
    "quiet": Need("quiet", "a calmer moment", "the calm page",
                  "the pictures were easiest to enjoy one page at a time",
                  tags={"sharing"}),
}

PLANS = {
    "read_together": SharePlan("read_together", "read it together", "sat side by side and shared the pages",
                               "That was a fair way to share"),
    "pass_along": SharePlan("pass_along", "take turns with it", "passed the book back and forth",
                            "Taking turns made room for both"),
    "divide_time": SharePlan("divide_time", "share the time", "used a little timer and swapped turns",
                             "Sharing time kept the peace"),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    book = f["book_cfg"]
    need = f["need"]
    return [
        f'Write a myth-like story for a small child set in a bookstore that uses the words "army" and "diameter" and includes sharing.',
        f"Tell a gentle bookstore story where two children discover {book.phrase} and learn to share it.",
        f"Write a short mythic tale in a bookstore about one rare book, two children, and a fair sharing plan.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["child_a"], f["child_b"]
    book = f["book_cfg"]
    need = f["need"]
    plan = f["plan"]
    qa = [
        ("Where does the story happen?",
         f"It happens in a bookstore with tall shelves and warm lamp-light. That setting makes the rare book feel special, like something worth sharing carefully."),
        ("What kind of book did the children find?",
         f"They found {book.phrase}. The pictures showed an army, and the shape in the story hinted at a diameter in a big circle."),
        ("Why did the children need to share?",
         f"They needed to share because there was only one copy and both children wanted the story. {need.reason.capitalize()}, so taking turns or reading together was the kind choice."),
    ]
    if f.get("shared"):
        qa.append((
            "How did they solve the problem?",
            f"They chose to {plan.method}. That let both children enjoy the same book, and the librarian could help them go page by page."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with both children smiling and leaving the bookstore together. The shelf was calm again because the book had been shared instead of grabbed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["book_cfg"].tags) | set(f["need"].tags) | {"sharing"}
    out = []
    if "army" in tags:
        out.append(("What is an army?", "An army is a large group of soldiers working together. In stories, it can mean many tiny or brave characters moving as one group."))
    if "diameter" in tags:
        out.append(("What is a diameter?", "A diameter is a straight line that goes across a circle through the middle. It is the longest line you can draw inside the circle."))
    out.append(("What does sharing mean?", "Sharing means letting someone else use or enjoy the same thing too. It is kind because everyone gets a turn or a chance to enjoy it."))
    out.append(("What is a bookstore?", "A bookstore is a shop where people can buy and read books. Bookstores are often quiet places with many shelves full of stories."))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this bookstore tale needs a shareable rare book and a fair sharing turn.)"


ASP_RULES = r"""
shareable(B) :- book(B), shared(B).
fair_plan(P) :- plan(P), ptype(P, read_together).
fair_plan(P) :- plan(P), ptype(P, pass_along).
fair_plan(P) :- plan(P), ptype(P, divide_time).
valid(S, N, B) :- setting(S), need(N), book(B), shareable(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BOOKS.items():
        lines.append(asp.fact("book", bid))
        if b.shared:
            lines.append(asp.fact("shared", bid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("ptype", pid, p.method.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny mythic bookstore story world about sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--book", choices=BOOKS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--adult")
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


def resolve_params(args: argparse.Namespace, rng: random.Random):
    setting = args.setting or "bookstore"
    book = args.book or rng.choice(list(BOOKS))
    need = args.need or rng.choice(list(NEEDS))
    plan = args.plan or rng.choice(list(PLANS))
    return StoryParams(setting, book, need, plan, args.name1 or "Mira", args.name2 or "Niko", args.adult or "Librarian")


@dataclass
class StoryParams:
    setting: str
    book: str
    need: str
    plan: str
    name1: str
    name2: str
    adult: str
    seed: Optional[int] = None


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BOOKS[params.book], NEEDS[params.need], PLANS[params.plan],
                 params.name1, "girl", params.name2, "boy", params.adult, "woman")
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


CURATED = [
    StoryParams("bookstore", "army_story", "crowd", "read_together", "Mira", "Niko", "Librarian"),
    StoryParams("bookstore", "myth_atlas", "quiet", "pass_along", "Ava", "Leo", "Librarian"),
    StoryParams("bookstore", "circle_book", "crowd", "divide_time", "Mina", "Omar", "Librarian"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print("  ", t)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
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
