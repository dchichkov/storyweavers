#!/usr/bin/env python3
"""
storyworlds/worlds/book_dim_conflict_dialogue_kindness_detective_story.py
=========================================================================

A small detective-story world set in a book-dim room where a child sleuth
solves a gentle conflict with dialogue and kindness.

The world is built around one compact premise:
- a book-dim reading room
- a missing book with a torn corner and a mistaken suspicion
- a detective child who asks careful questions
- a kind resolution that repairs both the book and the friendship
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    dim: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "book_dim_room": Setting(place="the book-dim room", dim=True, affords={"search"}),
    "library_corner": Setting(place="the library corner", dim=True, affords={"search"}),
    "quiet_bookshop": Setting(place="the quiet bookshop", dim=True, affords={"search"}),
}

CLUES = {
    "red_book": Clue(
        id="red_book",
        label="red book",
        phrase="a bright red book with a gold spine",
        risk="torn",
        keyword="book-dim",
        tags={"book", "library"},
    ),
    "missing_page": Clue(
        id="missing_page",
        label="missing page",
        phrase="a page that had slipped out of a mystery book",
        risk="creased",
        keyword="book-dim",
        tags={"book", "page"},
    ),
    "bookmark": Clue(
        id="bookmark",
        label="bookmark",
        phrase="a blue ribbon bookmark",
        risk="faded",
        keyword="book-dim",
        tags={"book", "bookmark"},
    ),
}

HERO_NAMES = ["Mina", "Noah", "Iris", "Theo", "Lina", "Eli"]
HELPER_NAMES = ["June", "Owen", "Pia", "Sam", "Ada", "Finn"]


@dataclass
class StoryState:
    suspicion: float = 0.0
    conflict: float = 0.0
    kindness: float = 0.0
    relief: float = 0.0
    solved: bool = False


def introduce(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a small detective with a sharp eye for clues. "
        f"One dim afternoon, {hero.pronoun('subject')} found {clue.phrase} waiting in the {world.setting.place}."
    )
    world.say(
        f"The room felt book-dim and still, as if the shelves were holding their breath."
    )


def raise_conflict(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    helper.memes["hurt"] = helper.memes.get("hurt", 0.0) + 1
    world.say(
        f"{hero.id} looked at {helper.id} and said, \"Did you touch the {clue.label}?\""
    )
    world.say(
        f"{helper.id} frowned. \"I did not,\" {helper.pronoun('subject')} said, "
        f"\"but I was near the shelf when it fell.\""
    )
    hero.memes["conflict"] = 1.0


def investigate(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} took a slow breath and asked, \"What did you see?\""
    )
    world.say(
        f"{helper.id} pointed to a low chair. \"The chair was wobbling,\" {helper.pronoun('subject')} said. "
        f"\"The book slid off when the floor shook.\""
    )


def resolve(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} smiled and said, \"I'm sorry I rushed to blame you.\""
    )
    world.say(
        f"{helper.id} smiled back. \"Let's fix it together,\" {helper.pronoun('subject')} said."
    )
    world.say(
        f"They straightened the chair, smoothed the {clue.label}, and set it safely back on the shelf."
    )
    world.say(
        f"In the warm end of the book-dim room, the clue was found, the worry was gone, and the two friends walked home side by side."
    )


def tell(setting: Setting, clue: Clue, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "detective"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["quiet", "kind"]))
    book = world.add(Entity(id=clue.id, kind="thing", type="book", label=clue.label, phrase=clue.phrase))

    state = StoryState()
    world.facts.update(hero=hero, helper=helper, clue=book, clue_cfg=clue, state=state)

    introduce(world, hero, clue)
    world.para()
    raise_conflict(world, hero, helper, clue)
    investigate(world, hero, helper, clue)
    world.para()
    resolve(world, hero, helper, clue)

    state.solved = True
    world.facts["state"] = state
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue_cfg"]
    return [
        f'Write a short detective story for a young child set in a "{world.setting.place}" with the word "{clue.keyword}".',
        f"Tell a gentle mystery where {hero.id} suspects {helper.id}, but careful dialogue uncovers what really happened.",
        f"Write a book-dim detective story that begins with a clue, turns on a misunderstanding, and ends with kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue_cfg"]
    state: StoryState = f["state"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little detective who solved a mystery in {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem caused the conflict?",
            answer=f"At first, {hero.id} thought {helper.id} might have caused trouble near the {clue.label}, so they had a tense moment.",
        ),
        QAItem(
            question=f"How did the detective solve the problem?",
            answer=f"{hero.id} asked careful questions, listened to {helper.id}, and chose kindness instead of blame. That helped them find the real cause and fix it together.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The conflict went away, the {clue.label} was put back safely, and {hero.id} and {helper.id} ended the story feeling relieved and friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues, asks questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring with someone, especially when they feel upset.",
        ),
        QAItem(
            question="Why can talking help during a conflict?",
            answer="Talking can help because people can explain what happened, clear up confusion, and find a fair answer together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:7}) meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


@dataclass
class AspChoice:
    setting: str
    clue: str


ASP_RULES = r"""
selected(S,C) :- setting(S), clue(C), valid(S,C).
valid(S,C) :- affords(S, search), clue(C).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dim:
            lines.append(asp.fact("dim", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((sid, cid) for sid, s in SETTINGS.items() if "search" in s.affords for cid in CLUES)


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Book-dim detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("No valid story matches the requested options.")
    setting, clue = rng.choice(combos)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
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


CURATED = [
    StoryParams(setting="book_dim_room", clue="red_book", hero_name="Mina", hero_type="girl", helper_name="June", helper_type="girl"),
    StoryParams(setting="library_corner", clue="missing_page", hero_name="Theo", hero_type="boy", helper_name="Owen", helper_type="boy"),
    StoryParams(setting="quiet_bookshop", clue="bookmark", hero_name="Iris", hero_type="girl", helper_name="Pia", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, clue) combos:")
        for s, c in combos:
            print(f"  {s:16} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
