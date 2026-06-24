#!/usr/bin/env python3
"""
A small fable-style story world about literacy, sharing, and a foolish slap.

A rabbit and a crow find a picture book under a tree. Both want the book.
When one tries to snatch it, a slap starts a quarrel. A wise friend helps them
share the book, and the ending proves that reading together is sweeter than
fighting over pages.
"""

from __future__ import annotations

import argparse
import copy
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "rabbit", "hare"}
        male = {"boy", "father", "dad", "man", "crow", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    shade: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Book:
    label: str
    phrase: str
    pages: int
    kind: str = "book"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Companion:
    id: str
    label: str
    help_line: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    book: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow", shade="under a wide oak", affords={"read"}),
    "orchard": Setting(place="the orchard", shade="under the apple trees", affords={"read"}),
    "library_tree": Setting(place="the library tree", shade="in the hush of branches", affords={"read"}),
}

ACTIVITIES = {
    "read": Activity(
        id="read",
        verb="read the book",
        gerund="reading the book",
        rush="snatch the book away",
        keyword="literacy",
        tags={"literacy", "sharing"},
    ),
}

BOOKS = {
    "storybook": Book(
        label="storybook",
        phrase="a bright picture book",
        pages=16,
    ),
    "fablebook": Book(
        label="fablebook",
        phrase="a little book of fables",
        pages=12,
    ),
}

COMPANIONS = {
    "fox": Companion(
        id="fox",
        label="Fox",
        help_line="Let's take turns with the pages.",
        tail="sat shoulder to shoulder and took turns reading aloud",
    ),
    "turtle": Companion(
        id="turtle",
        label="Turtle",
        help_line="A book grows kinder when it is shared.",
        tail="read slowly together and pointed at each picture in turn",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Zoe", "Nora", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Noah", "Ben"]
TRAITS = ["curious", "gentle", "quick", "bright", "restless", "proud"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for book in BOOKS:
                combos.append((place, act, book))
    return combos


def prize_at_risk(activity: Activity, book: Book) -> bool:
    return activity.id == "read" and book.pages > 0


def select_companion(activity: Activity, book: Book) -> Optional[Companion]:
    if not prize_at_risk(activity, book):
        return None
    return COMPANIONS["fox"] if book.label == "storybook" else COMPANIONS["turtle"]


def explain_rejection(activity: Activity, book: Book) -> str:
    return (
        f"(No story: this world needs a book worth sharing, and {activity.gerund} "
        f"must lead to a real quarrel and repair. The chosen book does not fit.)"
    )


def explain_gender(book_id: str, gender: str) -> str:
    ok = " / ".join(sorted(BOOKS[book_id].genders))
    return f"(No story: this book does not suit a {gender} here; try --gender {ok}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    book = f["book_cfg"]
    act = f["activity"]
    return [
        f'Write a short fable for a small child about literacy and sharing that includes the word "{act.keyword}".',
        f"Tell a gentle fable where {hero.id} wants to {act.verb} but must learn to share {book.phrase}.",
        f"Write a child-friendly animal fable in which a slap leads to a lesson about sharing a book.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    peer: Entity = f["peer"]
    book: Entity = f["book"]
    act: Activity = f["activity"]
    companion: Companion = f["companion"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    out = [
        QAItem(
            question=f"Who wanted to {act.verb} at {world.setting.place}?",
            answer=f"A little {trait} {hero.type} named {hero.id} wanted to {act.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {book.label}?",
            answer=f"{hero.id} wanted to keep the {book.label} all to {hero.pronoun('possessive')}self and read it first.",
        ),
        QAItem(
            question=f"Why did the quarrel begin when both animals saw the book?",
            answer=(
                f"The quarrel began because {hero.id} and {peer.id} both wanted the same book. "
                f"When {peer.id} reached for it, a slap made the moment turn sour."
            ),
        ),
        QAItem(
            question=f"How did the wise helper fix the problem?",
            answer=(
                f"{companion.label} reminded them to share. Then they took turns, and the reading became calm again."
            ),
        ),
    ]
    if f.get("resolved"):
        out.append(
            QAItem(
                question=f"What changed by the end of the fable?",
                answer=(
                    f"By the end, the two friends were not fighting over the book anymore. "
                    f"They were sharing it and reading together."
                ),
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is literacy?",
            answer="Literacy means being able to read and write words.",
        ),
        QAItem(
            question="Why is sharing a book a kind choice?",
            answer="Sharing a book is kind because both friends get to enjoy the story and learn from it.",
        ),
        QAItem(
            question="Why should children keep their hands gentle?",
            answer="Children should keep their hands gentle because slapping can hurt and can make a happy moment turn into a sad one.",
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


def _share_turn(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        for book in world.entities.values():
            if book.type != "book":
                continue
            if hero.memes.get("greed", 0) >= THRESHOLD and book.held_by == hero.id:
                sig = ("share", hero.id, book.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
                    hero.memes["greed"] = 0
                    out.append("Sharing made the hard feeling smaller.")
    return out


ASP_RULES = r"""
greedy(H) :- wants_book(H), holds(H,B), not shared(B).
shared(B) :- turn_taken(B).
kind(H) :- greedy(H), turn_taken(B), holds(H,B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword_of", aid, a.keyword))
    for bid, b in BOOKS.items():
        lines.append(asp.fact("book", bid))
        lines.append(asp.fact("pages", bid, b.pages))
        if b.plural:
            lines.append(asp.fact("book_plural", bid))
        for g in sorted(b.genders):
            lines.append(asp.fact("wears", g, bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show affords/2."))
    _ = model
    print(f"OK: ASP facts compiled for {len(SETTINGS)} settings.")
    return 0


def choose_peer(rng: random.Random, hero_gender: str) -> Entity:
    peer_type = "crow" if hero_gender == "girl" else "rabbit"
    return Entity(
        id="Peer",
        kind="character",
        type=peer_type,
        traits=["eager", "impatient"],
        meters={},
        memes={},
    )


def tell(setting: Setting, activity: Activity, book_cfg: Book,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait, "stubborn"],
    ))
    peer = world.add(choose_peer(random.Random(0), "girl" if hero_type == "rabbit" else "boy"))
    peer.id = "MerryPeer"
    world.entities[peer.id] = world.entities.pop("Peer")
    book = world.add(Entity(
        id="book",
        type="book",
        label=book_cfg.label,
        phrase=book_cfg.phrase,
        caretaker=hero.id,
        held_by=hero.id,
    ))
    helper_cfg = select_companion(activity, book_cfg)
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type="fox" if helper_cfg.id == "fox" else "turtle",
                              label=helper_cfg.label)) if helper_cfg else None

    hero.memes["greed"] = 1
    world.say(
        f"Under {setting.shade}, {hero.id} found {book_cfg.phrase} and loved its bright pages."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {hero.id} was learning literacy and wanted the words all to {hero.pronoun('possessive')}self."
    )
    world.para()
    world.say(
        f"Then {peer.id} came close and reached for the book too."
    )
    peer.memes["want"] = 1
    hero.memes["fear"] = 1
    hero.memes["anger"] = 1
    peer.memes["slapped"] = 1
    world.say(
        f"{peer.id} gave {hero.pronoun('object')} a quick slap on the paw, and the meadow went quiet."
    )
    world.para()
    if helper:
        world.say(
            f"{helper.label} stepped between them and said, \"{helper.help_line}\""
        )
        hero.memes["shame"] = 1
        peer.memes["shame"] = 1
        hero.memes["greed"] = 0
        world.say(
            f"{hero.id} looked at the book, then at {peer.id}, and slowly let go."
        )
        world.say(
            f"At last they shared the {book.label}; {helper.tail}, and the pages seemed brighter for it."
        )
        hero.memes["joy"] = 1
        peer.memes["joy"] = 1
        world.facts["resolved"] = True
    world.facts.update(
        hero=hero, peer=peer, book=book, book_cfg=book_cfg, activity=activity, helper=helper,
        companion=helper_cfg, setting=setting,
    )
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.book:
        act = ACTIVITIES[args.activity]
        bk = BOOKS[args.book]
        if not prize_at_risk(act, bk):
            raise StoryError(explain_rejection(act, bk))
    if args.gender and args.book and args.gender not in BOOKS[args.book].genders:
        raise StoryError(explain_gender(args.book, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.book is None or c[2] == args.book)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, book = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, book=book, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], BOOKS[params.book],
                 params.name, "rabbit" if params.gender == "girl" else "crow",
                 params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable story world about literacy, sharing, and a slap.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--book", choices=BOOKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for p in [StoryParams(place=p, activity=a, book=b, name="Lily", gender="girl", parent="mother", trait="curious")
                  for p, a, b in valid_combos()]:
            samples.append(generate(p))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
