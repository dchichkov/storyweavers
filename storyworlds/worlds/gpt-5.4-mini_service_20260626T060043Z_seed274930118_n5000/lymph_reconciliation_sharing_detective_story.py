#!/usr/bin/env python3
"""
storyworlds/worlds/lymph_reconciliation_sharing_detective_story.py
===================================================================

A small detective-story world about a careful child detective, a missing shared
item, and a reconciliation that makes the ending feel warm again.

Seed premise:
- A child detective notices something strange at home or at a tiny clinic.
- A friend or sibling thinks someone took a shared item.
- The detective follows clues, discovers the real cause, and helps everyone
  reconcile and share again.
- The seed word "lymph" is used as a world element and as a child-friendly
  clue in the medical-mystery branch: the detective learns that lymph nodes can
  swell when the body is fighting germs.

The world is intentionally small and constraint-checked. It supports both a
domestic mystery and a gentle clinic mystery, but every generated story must
have a clear clue trail, an accusation or misunderstanding, and a reconciliation
ending with sharing restored.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
    kind: str  # home | clinic
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    title: str
    clue_word: str
    misunderstanding: str
    reveal: str
    resolution: str
    setting_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    location: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    case: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    shared_item: str
    seed: Optional[int] = None


SETTINGS = {
    "home": Setting(place="the kitchen", kind="home", affords={"sharing", "reconcile"}),
    "clinic": Setting(place="the small clinic", kind="clinic", affords={"sharing", "reconcile"}),
}

CASES = {
    "lost_cracker": Case(
        id="lost_cracker",
        title="The Case of the Missing Crackers",
        clue_word="sharing",
        misunderstanding="thought someone took the last crackers",
        reveal="the crackers were hidden behind a cereal box for later sharing",
        resolution="the friends shared the crackers evenly and laughed",
        setting_kind="home",
        tags={"sharing"},
    ),
    "swollen_lymph": Case(
        id="swollen_lymph",
        title="The Case of the Tired Neck",
        clue_word="lymph",
        misunderstanding="worried that something scary was wrong",
        reveal="the detective learned that a lymph node can swell when the body is fighting germs",
        resolution="everyone breathed easier and shared a cup of warm tea",
        setting_kind="clinic",
        tags={"lymph"},
    ),
    "borrowed_marker": Case(
        id="borrowed_marker",
        title="The Case of the Blue Marker",
        clue_word="sharing",
        misunderstanding="thought a marker had been stolen",
        reveal="the marker had been borrowed and left in the art basket",
        resolution="the children agreed to share art supplies and tell the truth",
        setting_kind="home",
        tags={"sharing"},
    ),
}

ITEMS = {
    "crackers": SharedItem("crackers", "crackers", "a small plate of crackers", "pantry", True),
    "marker": SharedItem("marker", "marker", "a blue marker", "art_box"),
    "tea": SharedItem("tea", "tea", "a warm cup of tea", "table"),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Max", "Theo", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle detective story world with sharing and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--friend-type", choices=["girl", "boy"], dest="friend_type")
    ap.add_argument("--shared-item", choices=ITEMS, dest="shared_item")
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


def reasonableness_gate(case: Case, setting: Setting, shared_item: SharedItem) -> bool:
    if case.setting_kind != setting.kind:
        return False
    if case.id == "swollen_lymph":
        return setting.kind == "clinic"
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(list(SETTINGS))
    case_key = args.case or rng.choice([k for k, c in CASES.items() if c.setting_kind == SETTINGS[setting_key].kind])

    setting = SETTINGS[setting_key]
    case = CASES[case_key]
    shared_item = ITEMS[args.shared_item] if args.shared_item else ITEMS["tea" if case.id == "swollen_lymph" else ("crackers" if case.id == "lost_cracker" else "marker")]

    if not reasonableness_gate(case, setting, shared_item):
        raise StoryError("This case does not fit the chosen setting.")

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend_name = args.friend or rng.choice(BOY_NAMES if friend_type == "boy" else GIRL_NAMES)

    return StoryParams(
        setting=setting_key,
        case=case_key,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        shared_item=shared_item.id,
    )


def introduce(world: World, hero: Entity, friend: Entity, item: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} was a little detective who noticed tiny clues that other kids missed."
    )
    world.say(
        f"{hero.id} and {friend.id} liked sharing {item.label} and solving little problems together."
    )
    if case.id == "swollen_lymph":
        world.say(
            f"One day, {hero.id} heard the strange word lymph in the clinic and wondered what it meant."
        )
    else:
        world.say(
            f"One day, something went missing, and the case began."
        )


def begin_case(world: World, hero: Entity, friend: Entity, item: Entity, case: Case) -> None:
    place = world.setting.place
    world.para()
    world.say(
        f"At {place}, {hero.id} looked at the clues and saw that {friend.id} was frowning."
    )
    world.say(
        f"{friend.id} {case.misunderstanding}, so the room felt tense and quiet."
    )


def clue_scene(world: World, hero: Entity, friend: Entity, item: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} searched carefully and found a small clue."
    )
    if case.id == "lost_cracker":
        world.say(
            f"The clue was a crumb trail near the pantry, which meant the crackers had not been stolen at all."
        )
    elif case.id == "borrowed_marker":
        world.say(
            f"The clue was a blue smudge in the art basket, which meant the marker had been borrowed and returned."
        )
    else:
        world.say(
            f"The clue was a gentle doctor's note about a lymph node, which meant the body was doing its job."
        )


def reveal_scene(world: World, hero: Entity, friend: Entity, item: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} followed the clue and figured it out: {case.reveal}."
    )
    if case.id == "swollen_lymph":
        world.say(
            f"That made the worry smaller, because lymph helps the body notice germs and fight them off."
        )


def reconcile_scene(world: World, hero: Entity, friend: Entity, item: Entity, case: Case) -> None:
    world.para()
    world.say(
        f"{hero.id} turned to {friend.id} and said that nobody had been tricking anyone."
    )
    world.say(
        f"Then the two friends made up."
    )
    world.say(
        f"{case.resolution.capitalize()}."
    )


def tell_story(world: World, hero: Entity, friend: Entity, item: Entity, case: Case) -> None:
    introduce(world, hero, friend, item, case)
    begin_case(world, hero, friend, item, case)
    clue_scene(world, hero, friend, item, case)
    reveal_scene(world, hero, friend, item, case)
    reconcile_scene(world, hero, friend, item, case)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    case = CASES[params.case]
    item_cfg = ITEMS[params.shared_item]

    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type=item_cfg.label,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        plural=item_cfg.plural,
        owner=hero.id,
        caretaker=friend.id,
    ))

    if case.id == "swollen_lymph":
        hero.memes["curiosity"] = 1.0
        friend.memes["worry"] = 1.0
    else:
        friend.memes["worry"] = 1.0
        hero.memes["curiosity"] = 1.0

    tell_story(world, hero, friend, item, case)

    world.facts.update(hero=hero, friend=friend, item=item, case=case, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        f"Write a short detective story for a child about {hero.id}, {friend.id}, and a clue about {case.clue_word}.",
        f"Tell a gentle mystery where {hero.id} helps {friend.id} solve a misunderstanding and end with reconciliation.",
        f"Write a story that includes sharing and the word lymph, then ends with the friends making up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"{hero.id} was the detective who looked for clues and helped solve the problem.",
        ),
        QAItem(
            question=f"What was {friend.id} worried about?",
            answer=f"{friend.id} was worried because {case.misunderstanding}.",
        ),
        QAItem(
            question=f"What clue helped solve the case?",
            answer=f"The clue was about {case.clue_word}, and it led to the truth about {item.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended when the friends reconciled and shared again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    if case.id != "swollen_lymph":
        return [
            QAItem(
                question="What does sharing mean?",
                answer="Sharing means letting other people use or enjoy something too.",
            ),
            QAItem(
                question="What does it mean to reconcile?",
                answer="To reconcile means to make up after a disagreement and feel friendly again.",
            ),
        ]
    return [
        QAItem(
            question="What is a lymph node?",
            answer="A lymph node is a tiny part of the body that helps protect you from germs.",
        ),
        QAItem(
            question="Why might a lymph node swell?",
            answer="A lymph node can swell when the body is fighting germs and doing extra work.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too.",
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make up after a disagreement and feel friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(home).
setting(clinic).
case(lost_cracker,home).
case(swollen_lymph,clinic).
case(borrowed_marker,home).

compatible(Case,Setting) :- case(Case,Setting).
valid_story(Setting,Case) :- compatible(Case,Setting).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CASES.values():
        lines.append(asp.fact("case", c.id, c.setting_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(c.id, s.kind) for c in CASES.values() for s in SETTINGS.values() if reasonableness_gate(c, s, ITEMS["tea"])}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} valid combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="home", case="lost_cracker", hero_name="Mia", hero_type="girl", friend_name="Leo", friend_type="boy", shared_item="crackers"),
    StoryParams(setting="clinic", case="swollen_lymph", hero_name="Nora", hero_type="girl", friend_name="Ben", friend_type="boy", shared_item="tea"),
    StoryParams(setting="home", case="borrowed_marker", hero_name="Ava", hero_type="girl", friend_name="Max", friend_type="boy", shared_item="marker"),
]


def resolve_gendered_name(rng: random.Random, kind: str) -> str:
    return rng.choice(GIRL_NAMES if kind == "girl" else BOY_NAMES)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid story combinations:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            p = sample.params
            print(f"### {i + 1}: {p.setting} / {p.case}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
