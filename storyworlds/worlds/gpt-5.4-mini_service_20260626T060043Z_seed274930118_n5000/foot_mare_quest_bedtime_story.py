#!/usr/bin/env python3
"""
Story world: foot, mare, and a tiny bedtime Quest.

A child and a gentle mare go on a small Quest before sleep. The child has a
sleepy foot that needs warming, and the mare helps by leading them to a cozy
place, finding a soft wrap, and returning home in the moonlight.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "mare"}
        male = {"boy", "father", "dad", "man", "stallion"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    need: str
    reward: str
    danger: str
    keyword: str = "Quest"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Help:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place("the moonlit meadow", affords={"quest", "walk"}),
    "barn": Place("the quiet barn", affords={"quest", "rest"}),
    "garden": Place("the sleepy garden", affords={"quest", "walk"}),
}

QUESTS = {
    "footwarm": Quest(
        id="footwarm",
        verb="find a warm wrap for the little foot",
        gerund="searching for a warm wrap",
        rush="trot toward the lantern glow",
        need="warmth",
        reward="a cozy bedtime feeling",
        danger="the cold night air",
        keyword="Quest",
    ),
    "hoofsong": Quest(
        id="hoofsong",
        verb="bring back the soft bell",
        gerund="following the soft ringing",
        rush="canter toward the sound",
        need="music",
        reward="a gentle lullaby",
        danger="the dark brush",
        keyword="Quest",
    ),
    "stardust": Quest(
        id="stardust",
        verb="find a handful of stardust leaves",
        gerund="collecting shining leaves",
        rush="hurry along the path",
        need="wonder",
        reward="a dreamy bedtime glow",
        danger="the windy hill",
        keyword="Quest",
    ),
}

ITEMS = {
    "wrap": Item(
        id="wrap",
        label="soft wrap",
        phrase="a soft wool wrap",
        type="wrap",
        region="foot",
    ),
    "blanket": Item(
        id="blanket",
        label="blanket",
        phrase="a small blanket",
        type="blanket",
        region="body",
    ),
    "ribbon": Item(
        id="ribbon",
        label="ribbon",
        phrase="a silver ribbon",
        type="ribbon",
        region="mane",
    ),
}

HELPERS = {
    "lantern": Help(
        id="lantern",
        label="lantern light",
        prep="carry the lantern together",
        tail="came home by lantern light",
        covers={"foot", "body", "mane"},
    ),
    "blanket_help": Help(
        id="blanket_help",
        label="bedtime blanket",
        prep="tuck the blanket around the little foot",
        tail="walked home under the blanket",
        covers={"foot", "body"},
    ),
    "saddlecloth": Help(
        id="saddlecloth",
        label="a warm saddlecloth",
        prep="place a warm saddlecloth over the mare's back",
        tail="returned with the saddlecloth snug and warm",
        covers={"body", "mane"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Noah", "Eli"]
HORSE_NAMES = ["Daisy", "Rose", "Pearl", "Misty"]

TRAITS = ["sleepy", "curious", "gentle", "brave", "small", "soft"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    mare: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_valid(P,Q,I) :- place(P), quest(Q), item(I), needs(Q,N), item_region(I,R), quest_risk(Q,R), has_help(Q,I).
has_help(Q,I) :- help(H), covers(H,R), item_region(I,R), needs(Q,N), helps(H,N).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs", qid, q.need))
        lines.append(asp.fact("quest_risk", qid, "foot"))
        lines.append(asp.fact("quest_risk", qid, "body"))
        lines.append(asp.fact("quest_risk", qid, "mane"))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_region", iid, i.region))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("help", hid))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", hid, c))
        if hid == "lantern":
            lines.append(asp.fact("helps", hid, "warmth"))
            lines.append(asp.fact("helps", hid, "music"))
            lines.append(asp.fact("helps", hid, "wonder"))
        elif hid == "blanket_help":
            lines.append(asp.fact("helps", hid, "warmth"))
        elif hid == "saddlecloth":
            lines.append(asp.fact("helps", hid, "warmth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show quest_valid/3."))
    return sorted(set(asp.atoms(model, "quest_valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for qid, q in QUESTS.items():
            for iid, item in ITEMS.items():
                if item.region in {"foot", "body", "mane"}:
                    if q.need == "warmth" and iid in {"wrap", "blanket"}:
                        combos.append((place, qid, iid))
                    if q.need in {"music", "wonder"} and iid == "ribbon":
                        combos.append((place, qid, iid))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def choose_help(quest: Quest, item: Item) -> Optional[Help]:
    if quest.need == "warmth" and item.id == "wrap":
        return HELPERS["blanket_help"]
    if quest.need in {"music", "wonder"} and item.id == "ribbon":
        return HELPERS["lantern"]
    return None


def tell(place: Place, quest: Quest, item_cfg: Item, hero_name: str, gender: str, mare_name: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", trait, "sleepy"]))
    mare = world.add(Entity(id=mare_name, kind="character", type="mare", traits=["gentle", "patient"]))
    item = world.add(Entity(
        id=item_cfg.id,
        type=item_cfg.type,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=child.id,
        region=item_cfg.region,
        plural=item_cfg.plural,
    ))

    world.say(f"{child.id} was a little {trait} child who loved a bedtime {quest.keyword}.")
    world.say(f"{mare.id} was a gentle mare with soft eyes and a warm step.")
    world.say(f"One night, {child.id} needed {item.phrase} for the little foot before sleep.")
    world.say(f"So {child.id} and {mare.id} set out on a tiny {quest.keyword} by moonlight.")

    world.lines.append("")

    world.say(f"They went to {place.name}, where the air was cool and the stars looked near.")
    world.say(f"{child.id} wanted to {quest.verb}, but the night air could make a foot chilly.")
    world.say(f"{mare.id} listened, then nudged a lantern toward the path and kept close.")
    world.say(f"Together they began {quest.gerund}, while the mare stayed beside the child.")

    world.lines.append("")

    helper = choose_help(quest, item)
    if helper is None:
        raise StoryError("No gentle bedtime help matches this quest and item.")

    world.say(f"At last, they found the answer: {helper.label}.")
    world.say(f"{mare.id} helped by {helper.prep}.")
    world.say(f"{child.id} smiled, because the little foot felt safe and warm again.")
    world.say(f"Then they {helper.tail}, and the Quest turned into a sleepy walk home.")
    world.say(f"Back at home, {child.id} tucked in, and {mare.id} stood under the moon like a quiet guardian.")

    world.facts.update(
        child=child,
        mare=mare,
        item=item,
        quest=quest,
        helper=helper,
        place=place,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    return [
        f'Write a gentle bedtime story about a child named {child.id} and a mare on a tiny {quest.keyword}.',
        f'Tell a short cozy story where {child.id} and a mare search for something that keeps a foot warm at night.',
        f'Write a child-friendly tale with the words "foot", "mare", and "{quest.keyword}" that ends with a safe, sleepy return home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mare = f["mare"]
    item = f["item"]
    quest = f["quest"]
    helper = f["helper"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who went on the bedtime {quest.keyword}?",
            answer=f"{child.id} and {mare.id} went together on the bedtime {quest.keyword}.",
        ),
        QAItem(
            question=f"What did {child.id} need for the little foot?",
            answer=f"{child.id} needed {item.phrase} for the little foot before sleep.",
        ),
        QAItem(
            question=f"Why did the Quest feel important?",
            answer=f"It mattered because the foot was chilly, and the story needed something warm and safe before bedtime.",
        ),
        QAItem(
            question=f"What helped them finish the quest at {place.name}?",
            answer=f"{helper.label} helped them finish the quest, because it made the way warm and cozy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} tucked in safely and {mare.id} keeping a quiet watch under the moon.",
        ),
    ]


WORLD_QA = {
    "foot": [
        QAItem(
            question="What is a foot for?",
            answer="A foot helps you stand, walk, run, and dance.",
        )
    ],
    "mare": [
        QAItem(
            question="What is a mare?",
            answer="A mare is a grown female horse.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something important or solve a small problem.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why do bedtime stories feel calm?",
            answer="Bedtime stories feel calm because they usually have soft sounds, kind helpers, and a peaceful ending.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_QA["foot"])
    out.extend(WORLD_QA["mare"])
    out.extend(WORLD_QA["quest"])
    out.extend(WORLD_QA["bedtime"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} traits={e.traits}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime Quest storyworld with a mare and a foot.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mare")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("No valid bedtime Quest fits those choices.")
    place, qid, iid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mare = args.mare or rng.choice(HORSE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=qid, name=name, gender=gender, mare=mare, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], ITEMS["wrap" if QUESTS[params.quest].need == "warmth" else "ribbon" if QUESTS[params.quest].need in {"music", "wonder"} else "wrap"], params.name, params.gender, params.mare, params.trait)
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


def asp_verify() -> int:
    import asp

    a = set(asp_valid())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print("\n".join(str(c) for c in combos))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="meadow", quest="footwarm", name="Mia", gender="girl", mare="Daisy", trait="curious"),
            StoryParams(place="barn", quest="hoofsong", name="Leo", gender="boy", mare="Rose", trait="gentle"),
            StoryParams(place="garden", quest="stardust", name="Nora", gender="girl", mare="Pearl", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
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
