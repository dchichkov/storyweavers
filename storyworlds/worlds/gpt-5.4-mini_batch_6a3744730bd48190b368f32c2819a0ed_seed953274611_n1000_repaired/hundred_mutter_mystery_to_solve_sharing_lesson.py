#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hundred_mutter_mystery_to_solve_sharing_lesson.py
==================================================================================

A small whodunit-style storyworld for a kid-sized mystery about something gone
missing, a careful search, a sharing moment, and a lesson learned.

Seed words: hundred, mutter
Story instruments: Mystery to Solve, Sharing, Lesson Learned
Style: Whodunit
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Character:
    id: str
    type: str
    role: str
    label: str
    warmth: str
    verb: str
    clue_style: str
    shares: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Mystery:
    id: str
    missing: str
    place: str
    hiding_spot: str
    suspicious: str
    clue: str
    number_word: str = "hundred"
    mutter_phrase: str = "muttered"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SharingItem:
    id: str
    label: str
    phrase: str
    hidden_by: str
    share_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Lesson:
    id: str
    statement: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    detective: str
    helper: str
    witness: str
    detective_gender: str
    helper_gender: str
    witness_gender: str
    parent: str
    mystery: str
    shared_item: str
    lesson: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_unfolded") and "parent" in world.entities:
        parent = world.get("parent")
        if parent.memes["worry"] < THRESHOLD:
            parent.memes["worry"] += 1
            out.append("__silent__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__silent__":
                        world.say(s)


CAUSAL_RULES = [Rule("worry", _r_worry)]


def make_cast(
    detective: str,
    detective_gender: str,
    helper: str,
    helper_gender: str,
    witness: str,
    witness_gender: str,
    parent: str,
) -> dict[str, Entity]:
    return {
        "detective": Entity(id=detective, kind="character", type=detective_gender, role="detective", label="the detective"),
        "helper": Entity(id=helper, kind="character", type=helper_gender, role="helper", label="the helper"),
        "witness": Entity(id=witness, kind="character", type=witness_gender, role="witness", label="the witness"),
        "parent": Entity(id="parent", kind="character", type=parent, role="parent", label="the parent"),
    }


MYSTERIES = {
    "missing_cookies": Mystery(
        id="missing_cookies",
        missing="the cookie plate",
        place="the kitchen",
        hiding_spot="behind the bread box",
        suspicious="crumbs",
        clue="a tiny trail of crumbs and one sticky thumbprint",
    ),
    "missing_stickers": Mystery(
        id="missing_stickers",
        missing="the sticker sheet",
        place="the craft table",
        hiding_spot="under the paint cup",
        suspicious="glitter",
        clue="a trail of glitter and a corner bent into a little square",
    ),
    "missing_marbles": Mystery(
        id="missing_marbles",
        missing="the marble tin",
        place="the playroom",
        hiding_spot="inside a toy drum",
        suspicious="clinks",
        clue="a soft clink, clink, clink from the drum and a dusty footprint",
    ),
}

SHARED_ITEMS = {
    "cookies": SharingItem(
        id="cookies",
        label="cookies",
        phrase="a small plate of cookies",
        hidden_by="a napkin",
        share_text="spooned the extra cookies onto two clean plates and shared them out fairly",
        tags={"share", "food"},
    ),
    "crayons": SharingItem(
        id="crayons",
        label="crayons",
        phrase="a bright box of crayons",
        hidden_by="the lid",
        share_text="opened the crayon box wide and gave everyone an even turn",
        tags={"share", "art"},
    ),
    "stickers": SharingItem(
        id="stickers",
        label="stickers",
        phrase="a shiny sticker sheet",
        hidden_by="a folder",
        share_text="peeled the sticker sheet into careful pieces so each child could pick one",
        tags={"share", "art"},
    ),
}

LESSONS = {
    "share_kindly": Lesson(
        id="share_kindly",
        statement="If you share what you have, the whole room feels less suspicious and much kinder.",
        ending_image="the table looked neat again, with three happy kids and no one left out",
        tags={"share"},
    ),
    "ask_first": Lesson(
        id="ask_first",
        statement="If something goes missing, it helps to ask calmly before you blame anyone.",
        ending_image="the clue sat in plain sight, waiting for someone patient enough to notice it",
        tags={"mystery"},
    ),
    "count_and_compare": Lesson(
        id="count_and_compare",
        statement="Counting carefully can solve a mystery, and sharing can fix a hurt feeling afterward.",
        ending_image="the last piece was counted, shared, and smiled over at the same time",
        tags={"mystery", "share"},
    ),
}

CHARACTER_REGISTRY = {
    "detective": [
        Character("detective", "boy", "detective", "the detective", "careful", "looked closely", "whispered", "shared", "learned"),
        Character("detective", "girl", "detective", "the detective", "careful", "looked closely", "whispered", "shared", "learned"),
    ],
    "helper": [
        Character("helper", "boy", "helper", "the helper", "quiet", "muttered", "noticed", "shared", "learned"),
        Character("helper", "girl", "helper", "the helper", "quiet", "muttered", "noticed", "shared", "learned"),
    ],
    "witness": [
        Character("witness", "boy", "witness", "the witness", "nervous", "peeked", "muttered", "shared", "learned"),
        Character("witness", "girl", "witness", "the witness", "nervous", "peeked", "muttered", "shared", "learned"),
    ],
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ivy", "Maya"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Eli", "Theo", "Max", "Sam"]
PARENTS = ["mother", "father"]
PAIRINGS = [
    ("detective", "helper", "witness"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid, mystery in MYSTERIES.items():
        for sid, item in SHARED_ITEMS.items():
            for lid, lesson in LESSONS.items():
                if "mystery" in lesson.tags and "mystery" in item.tags:
                    combos.append((mid, sid, lid))
                elif "share" in lesson.tags and "share" in item.tags:
                    combos.append((mid, sid, lid))
                elif lesson.tags == {"mystery", "share"}:
                    combos.append((mid, sid, lid))
    return combos


def explain_rejection(mystery: Mystery, item: SharingItem, lesson: Lesson) -> str:
    return (
        f"(No story: this combination cannot support a clear whodunit turn. "
        f"Try a missing object, a shareable item, and a lesson that matches the scene.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit storyworld about a missing thing, a shared thing, and a lesson.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--shared-item", choices=SHARED_ITEMS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--witness")
    ap.add_argument("--detective-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--witness-gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if not combos:
        raise StoryError("No valid mystery stories are available.")

    if args.mystery and args.shared_item and args.lesson:
        m = MYSTERIES[args.mystery]
        item = SHARED_ITEMS[args.shared_item]
        lesson = LESSONS[args.lesson]
        if (args.lesson == "count_and_compare") or ("mystery" in lesson.tags and "mystery" in item.tags) or ("share" in lesson.tags and "share" in item.tags):
            pass
        else:
            raise StoryError(explain_rejection(m, item, lesson))

    choices = [c for c in combos if (args.mystery is None or c[0] == args.mystery) and (args.shared_item is None or c[1] == args.shared_item) and (args.lesson is None or c[2] == args.lesson)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")

    mid, sid, lid = rng.choice(sorted(choices))
    m = MYSTERIES[mid]
    item = SHARED_ITEMS[sid]
    lesson = LESSONS[lid]
    d_gender = args.detective_gender or rng.choice(["boy", "girl"])
    h_gender = args.helper_gender or rng.choice(["boy", "girl"])
    w_gender = args.witness_gender or rng.choice(["boy", "girl"])
    detective = args.detective or rng.choice(GIRL_NAMES if d_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if h_gender == "girl" else BOY_NAMES)
    witness = args.witness or rng.choice(GIRL_NAMES if w_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    if len({detective, helper, witness}) < 3:
        raise StoryError("Pick distinct names so the whodunit stays clear.")
    return StoryParams(
        detective=detective,
        helper=helper,
        witness=witness,
        detective_gender=d_gender,
        helper_gender=h_gender,
        witness_gender=w_gender,
        parent=parent,
        mystery=mid,
        shared_item=sid,
        lesson=lid,
    )


def tell(params: StoryParams) -> World:
    world = World()
    m = MYSTERIES[params.mystery]
    item = SHARED_ITEMS[params.shared_item]
    lesson = LESSONS[params.lesson]
    cast = make_cast(params.detective, params.detective_gender, params.helper, params.helper_gender, params.witness, params.witness_gender, params.parent)
    detective = world.add(cast["detective"])
    helper = world.add(cast["helper"])
    witness = world.add(cast["witness"])
    parent = world.add(cast["parent"])
    world.facts["mystery"] = m
    world.facts["shared_item"] = item
    world.facts["lesson"] = lesson
    world.facts["detective"] = detective
    world.facts["helper"] = helper
    world.facts["witness"] = witness
    world.facts["parent"] = parent

    detective.memes["curiosity"] += 1
    helper.memes["mutter"] += 1
    witness.memes["nervous"] += 1

    world.say(
        f"On a quiet afternoon, {detective.id} frowned at {m.missing}. "
        f"{helper.id} stood nearby and {helper.pronoun()} muttered about {m.suspicious}."
    )
    world.say(
        f"{witness.id} said there had been {m.clue}, and that was the first clue."
    )

    world.para()
    world.say(
        f"{detective.id} inspected {m.place} like a proper little detective. "
        f"{helper.id} peered {m.hiding_spot} while {witness.id} watched both of them."
    )
    world.say(
        f"At last, {detective.id} noticed the trail and asked the right question."
    )

    # Resolution: uncover the hidden thing, then share something else fairly.
    world.para()
    item_hidden = f"Because {item.phrase} had been tucked {item.hidden_by}, the clue made sense."
    world.say(
        f"The mystery was solved when {detective.id} found the answer: {m.missing} was hidden {m.hiding_spot}. "
        f"{item_hidden}"
    )
    world.say(
        f"Then {helper.id} chose to be kind and {item.share_text}."
    )
    world.say(
        f"{witness.id} stopped looking worried and smiled when everyone got a fair turn."
    )

    world.para()
    world.say(
        f"In the end, {lesson.ending_image}. {lesson.statement} "
        f"That was the lesson they remembered."
    )

    world.facts.update(
        solved=True,
        shared=True,
        lesson_id=lesson.id,
        clue=m.clue,
        hiding_spot=m.hiding_spot,
        mutter="muttered",
        hundred="hundred",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    item: SharingItem = f["shared_item"]
    lesson: Lesson = f["lesson"]
    return [
        f'Write a whodunit for a 3-to-5-year-old where something goes missing in {m.place}, and one character mutters about the clue.',
        f"Tell a mystery story that includes the word 'hundred' and the word 'mutter', then ends with sharing and a lesson learned.",
        f"Write a kid-friendly whodunit where a clue solves the mystery, and afterward the characters share {item.label} fairly and remember {lesson.statement.lower()}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    item: SharingItem = f["shared_item"]
    lesson: Lesson = f["lesson"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    witness: Entity = f["witness"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"The mystery was where {m.missing} went. The clue was {m.clue}, which pointed to {m.hiding_spot}.",
        ),
        QAItem(
            question=f"Why did {helper.id} mutter?",
            answer=f"{helper.id} muttered because the clue looked strange and important. That quiet worry helped the detective notice the answer.",
        ),
        QAItem(
            question="What happened after the mystery was solved?",
            answer=f"{helper.id} shared {item.label} fairly, so everyone got a turn and the room felt kinder. {witness.id} stopped worrying when the sharing began.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=f"They learned that {lesson.statement.lower()} The ending showed that solving the mystery and sharing were both part of the same good day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure out an answer. In a mystery, clues point you toward what really happened.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use or have some of what you have. Sharing helps everyone feel included.",
        ),
        QAItem(
            question="Why do people mutter?",
            answer="People mutter when they speak in a very quiet voice, often because they are thinking hard or feeling unsure. In a mystery story, muttering can show a character is puzzling over a clue.",
        ),
        QAItem(
            question="Why can counting help?",
            answer="Counting helps because it shows how many things there are and whether one is missing. Careful counting is a good way to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:6}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, S, L) :- mystery(M), shared_item(S), lesson(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for sid in SHARED_ITEMS:
        lines.append(asp.fact("shared_item", sid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation produced a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    for key in ("mystery", "shared_item", "lesson"):
        if getattr(params, key) not in globals()[key.upper() + "S"]:
            raise StoryError(f"Invalid {key}: {getattr(params, key)!r}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = valid_combos()
    if args.mystery and args.shared_item and args.lesson:
        if (args.mystery, args.shared_item, args.lesson) not in choices:
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], SHARED_ITEMS[args.shared_item], LESSONS[args.lesson]))
    filtered = [
        c for c in choices
        if (args.mystery is None or c[0] == args.mystery)
        and (args.shared_item is None or c[1] == args.shared_item)
        and (args.lesson is None or c[2] == args.lesson)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    mid, sid, lid = rng.choice(sorted(filtered))
    dg = args.detective_gender or rng.choice(["boy", "girl"])
    hg = args.helper_gender or rng.choice(["boy", "girl"])
    wg = args.witness_gender or rng.choice(["boy", "girl"])
    detective = args.detective or rng.choice(GIRL_NAMES if dg == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    witness = args.witness or rng.choice(GIRL_NAMES if wg == "girl" else BOY_NAMES)
    if len({detective, helper, witness}) < 3:
        raise StoryError("Pick distinct names so the mystery stays clear.")
    return StoryParams(
        detective=detective,
        helper=helper,
        witness=witness,
        detective_gender=dg,
        helper_gender=hg,
        witness_gender=wg,
        parent=args.parent or rng.choice(PARENTS),
        mystery=mid,
        shared_item=sid,
        lesson=lid,
    )


CURATED = [
    StoryParams(
        detective="Mia",
        helper="Noah",
        witness="Lily",
        detective_gender="girl",
        helper_gender="boy",
        witness_gender="girl",
        parent="mother",
        mystery="missing_cookies",
        shared_item="cookies",
        lesson="count_and_compare",
    ),
    StoryParams(
        detective="Theo",
        helper="Ava",
        witness="Finn",
        detective_gender="boy",
        helper_gender="girl",
        witness_gender="boy",
        parent="father",
        mystery="missing_stickers",
        shared_item="stickers",
        lesson="ask_first",
    ),
    StoryParams(
        detective="Zoe",
        helper="Leo",
        witness="Maya",
        detective_gender="girl",
        helper_gender="boy",
        witness_gender="girl",
        parent="mother",
        mystery="missing_marbles",
        shared_item="crayons",
        lesson="share_kindly",
    ),
]


def build_storyworld(sample: StorySample) -> StorySample:
    return sample


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible mystery stories:\n")
        for mid, sid, lid in asp_valid_combos():
            print(f"  {mid:16} {sid:12} {lid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}, {p.helper}, {p.witness} — {p.mystery} / {p.shared_item} / {p.lesson}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
