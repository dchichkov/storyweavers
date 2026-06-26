#!/usr/bin/env python3
"""
storyworlds/worlds/seek_bookstore_sound_effects_teamwork_problem_solving.py
===========================================================================

A small bedtime-story world set in a bookstore.

Premise:
- A child wants to seek a special book before bedtime.
- The bookstore is quiet and full of sound effects: soft steps, page rustles,
  cart wheels, shelf bumps, and whispered shh.
- A small problem appears: the sought book is not on the shelf where it should
  be.

Turn:
- The child, a bookseller, and a helper work together.
- They use clues, careful listening, and a gentle plan to find the book.

Resolution:
- The missing book is found in a cozy hiding place, and the child leaves calm
  and happy with a bedtime story in hand.

This world is intentionally narrow and constraint-checked so stories stay
plausible, child-facing, and authored.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bookstore"
    closing: bool = True


@dataclass
class Quest:
    item: str
    label: str
    search_verb: str
    sound_on_search: str
    sound_when_found: str
    clue: str
    hiding_place: str
    problem: str
    fix: str


@dataclass
class Helper:
    id: str
    label: str
    type: str
    special: str
    sound: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


@dataclass
class StoryParams:
    quest: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


QUESTS = {
    "bedtime_book": Quest(
        item="book",
        label="a bedtime storybook",
        search_verb="seek the bedtime storybook",
        sound_on_search="soft footsteps",
        sound_when_found="a happy flutter of pages",
        clue="a tiny library card peeking out from under a reading rug",
        hiding_place="the reading nook under a beanbag",
        problem="the bedtime storybook is missing from the front shelf",
        fix="everyone listens for the page-flutter and checks the cozy corners together",
    ),
    "picture_book": Quest(
        item="book",
        label="a picture book with moon drawings",
        search_verb="seek the moon picture book",
        sound_on_search="gentle tip-taps",
        sound_when_found="a tiny rustle",
        clue="silver paper dust near the children’s shelf",
        hiding_place="behind a basket of bookmarks",
        problem="the moon picture book is not where it should be",
        fix="the helper points to the clue and the child checks the right shelf with care",
    ),
    "story_card": Quest(
        item="card",
        label="a library story card",
        search_verb="seek the story card",
        sound_on_search="quiet shuffles",
        sound_when_found="a cheerful clink",
        clue="a stamped receipt on the counter",
        hiding_place="inside the checkout drawer",
        problem="the story card slipped out of sight",
        fix="the bookseller and child look together, one shelf at a time",
    ),
}

HELPERS = {
    "bookseller": Helper(
        id="bookseller",
        label="the bookseller",
        type="adult",
        special="knows the shelves best",
        sound="a soft shh",
    ),
    "parent": Helper(
        id="parent",
        label="the parent",
        type="adult",
        special="remembers the last place they looked",
        sound="a calming whisper",
    ),
    "cat": Helper(
        id="cat",
        label="the sleepy cat",
        type="cat",
        special="spots small hiding places",
        sound="a tiny purr",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Theo", "Ava", "Ben", "Luna", "Eli"]
TRAITS = ["curious", "gentle", "sleepy", "brave", "quiet", "hopeful"]


def reasonableness_gate(quest: Quest, helper: Helper) -> None:
    if quest.item == "card" and helper.id == "cat":
        raise StoryError("The sleepy cat cannot reliably help find a small checkout card.")
    if quest.item == "book" and helper.id == "cat" and quest.label.startswith("a bedtime"):
        return
    if not quest.clue or not quest.hiding_place:
        raise StoryError("This story needs a clue and a hiding place to support a real search.")


def tell(quest: Quest, child: Entity, helper: Entity, parent: Entity) -> World:
    world = World(Setting())
    book = world.add(Entity(
        id="quest_item",
        kind="thing",
        type=quest.item,
        label=quest.item,
        phrase=quest.label,
        owner=child.id,
        hidden_in=quest.hiding_place,
    ))
    child.memes["hope"] = 1.0
    child.memes["calm"] = 0.0
    child.memes["worry"] = 0.0
    helper.memes["calm"] = 1.0
    parent.memes["calm"] = 1.0

    # Act 1: the seek.
    world.say(
        f"At the bookstore, {child.id} was getting sleepy and still wanted to {quest.search_verb}."
    )
    world.say(
        f"The shelves were warm and quiet, and every little sound felt like a bedtime whisper."
    )
    world.say(
        f"Then {child.id} noticed a problem: {quest.problem}."
    )

    # Act 2: the search and tension.
    world.para()
    child.memes["worry"] += 1.0
    world.say(
        f"{child.id} listened closely. {quest.sound_on_search} came from the aisles, but not from the front shelf."
    )
    world.say(
        f"{helper.label} heard it too and said, \"Let's solve it together.\""
    )
    world.say(
        f"{parent.id} pointed out the clue: {quest.clue}."
    )
    world.say(
        f"So they searched one cozy spot at a time, with careful eyes and gentle hands."
    )

    # Act 3: teamwork and problem solving.
    world.para()
    book.hidden_in = quest.hiding_place
    child.memes["worry"] = 0.0
    child.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    parent.memes["joy"] = 1.0
    world.say(
        f"At last, {helper.label} looked in {quest.hiding_place}."
    )
    world.say(
        f"There it was: {quest.sound_when_found} as {child.id} found {quest.label} tucked away there."
    )
    world.say(
        f"With teamwork and a simple plan, they fixed the problem: {quest.fix}."
    )
    world.say(
        f"{child.id} hugged the book close, and the bookstore felt peaceful again."
    )

    world.facts = {
        "child": child,
        "helper": helper,
        "parent": parent,
        "quest": quest,
        "item": book,
    }
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for qid, quest in QUESTS.items():
        for hid, helper in HELPERS.items():
            try:
                reasonableness_gate(quest, helper)
            except StoryError:
                continue
            combos.append((qid, hid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    helper = f["helper"]
    return [
        f"Write a bedtime story set in a bookstore where {child.id} tries to seek {quest.label} with help from {helper.label}.",
        f"Tell a gentle story that includes soft sound effects, teamwork, and problem solving while {child.id} searches for {quest.label}.",
        f"Write a short child-friendly story about a missing book in a bookstore and how {child.id} and {helper.label} find it together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at the bookstore?",
            answer=f"{child.id} wanted to {quest.search_verb} because bedtime was near and the story mattered.",
        ),
        QAItem(
            question=f"What problem made the search important?",
            answer=f"The problem was that {quest.problem}. That meant they had to look carefully instead of just guessing.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the problem?",
            answer=f"{helper.label} helped, and {parent.id} joined in too. They worked together to find the missing book.",
        ),
        QAItem(
            question=f"Where was the book found?",
            answer=f"It was found in {quest.hiding_place}, which was a cozy hiding place inside the bookstore.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} ended up calm and happy, holding {quest.label} after the team found it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bookstore?",
            answer="A bookstore is a shop where people can browse, buy, and read books.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help a reader hear the scene, like rustle, tap, or whisper.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together to do something more easily than one person could alone.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a good way to fix a problem by thinking, trying clues, and choosing a plan.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(quest="bedtime_book", name="Mia", gender="girl", helper="bookseller"),
    StoryParams(quest="picture_book", name="Leo", gender="boy", helper="parent"),
    StoryParams(quest="story_card", name="Nora", gender="girl", helper="bookseller"),
]


ASP_RULES = r"""
entity(child; helper; parent; item).
quest( bedtime_book; picture_book; story_card ).
good_combo(Q,H) :- quest(Q), entity(H), not bad_combo(Q,H).
bad_combo(story_card,cat).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/2."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world set in a bookstore.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.quest and args.helper and (args.quest, args.helper) not in combos:
        raise StoryError("That helper cannot reasonably solve that bookstore search.")
    filtered = [
        c for c in combos
        if (args.quest is None or c[0] == args.quest)
        and (args.helper is None or c[1] == args.helper)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    qid, hid = rng.choice(sorted(filtered))
    quest = QUESTS[qid]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(quest=qid, name=name, gender=gender, helper=hid)


def generate(params: StoryParams) -> StorySample:
    quest = QUESTS[params.quest]
    helper_def = HELPERS[params.helper]
    reasonableness_gate(quest, helper_def)

    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[random.choice(TRAITS)]))
    helper = world.add(Entity(id=helper_def.label, kind="character", type=helper_def.type, label=helper_def.label))
    parent = world.add(Entity(id="parent", kind="character", type="adult", label="the parent"))

    world.say(f"{child.id} was a {child.traits[0]} child who loved quiet stories and soft pages.")
    world.say(f"One evening, {child.id} went to the bookstore and wanted to seek {quest.label}.")
    world.para()
    world.say(f"The aisles were calm. {helper_def.sound} drifted through the shelves.")
    world.say(f"Then came the problem: {quest.problem}.")
    world.para()
    world.say(f"{helper.label} and the parent said, \"Let's use teamwork and solve this together.\"")
    world.say(f"They followed a clue, listened for {quest.sound_on_search}, and checked the cozy corners.")
    world.say(f"At last, they found the book in {quest.hiding_place}.")
    world.say(f"It gave off {quest.sound_when_found}, and {child.id} smiled with sleepy joy.")
    world.say(f"Before bedtime, the problem was fixed, and the bookstore felt peaceful again.")

    world.facts = {
        "child": child,
        "helper": helper,
        "parent": parent,
        "quest": quest,
    }

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
        print(asp_program("#show good_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combo(s):")
        for qid, hid in combos:
            print(f"  {qid:15} {hid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.quest} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
