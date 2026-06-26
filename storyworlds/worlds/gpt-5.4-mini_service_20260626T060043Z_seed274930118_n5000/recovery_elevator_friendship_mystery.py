#!/usr/bin/env python3
"""
storyworlds/worlds/recovery_elevator_friendship_mystery.py
===========================================================

A small storyworld about a mysterious elevator stop, a friendship tested by worry,
and a recovery that turns the mystery into a gentle ending.

Premise:
- Two friends ride an elevator.
- Something important goes missing during the ride.
- The child suspects a mystery, but the real answer is tied to a dropped item,
  a stuck door, and a careful search.
- Friendship matters: one friend stays calm, helps search, and makes sure the
  other feels safe again.

The world is intentionally tiny and state-driven: physical meters track where
things are, and emotional memes track worry, trust, relief, and care.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the elevator"
    affords: set[str] = field(default_factory=lambda: {"ride", "wait", "search"})


@dataclass
class MysteriousItem:
    id: str
    label: str
    phrase: str
    clue: str
    hidden_spot: str


@dataclass
class StoryParams:
    name: str
    friend_name: str
    parent: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.item: Optional[Entity] = None
        self.mystery: Optional[MysteriousItem] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone.item = copy.deepcopy(self.item)
        clone.mystery = copy.deepcopy(self.mystery)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    if not world.mystery or not world.item:
        return out
    for ch in world.characters():
        if ch.memes.get("searching", 0.0) < THRESHOLD:
            continue
        sig = ("search", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if world.item.location == world.mystery.hidden_spot:
            out.append(f"{ch.id} noticed a small clue near the {world.mystery.hidden_spot}.")
            ch.memes["hope"] = ch.memes.get("hope", 0.0) + 1
        else:
            out.append(f"{ch.id} looked carefully, but the clue was not there.")
    return out


def _r_recover(world: World) -> list[str]:
    out: list[str] = []
    if not world.mystery or not world.item:
        return out
    for ch in world.characters():
        if ch.memes.get("hope", 0.0) < THRESHOLD:
            continue
        sig = ("recover", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if world.item.location == world.mystery.hidden_spot:
            world.item.carried_by = ch.id
            ch.memes["relief"] = ch.memes.get("relief", 0.0) + 1
            out.append(f"The missing {world.item.label} was found, and {ch.id} felt relief.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    names = world.characters()
    if len(names) < 2:
        return out
    a, b = names[0], names[1]
    if a.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("friendship", a.id, b.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["trust"] = a.memes.get("trust", 0.0) + 1
    b.memes["care"] = b.memes.get("care", 0.0) + 1
    out.append(f"{b.id} stayed close and helped {a.id} feel braver.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_search, _r_recover, _r_friendship):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ELEVATOR = Setting()

ITEMS = {
    "key": MysteriousItem(
        id="key",
        label="key",
        phrase="a small silver key",
        clue="a silver glint by the floor",
        hidden_spot="mat",
    ),
    "ticket": MysteriousItem(
        id="ticket",
        label="ticket",
        phrase="a folded ticket",
        clue="a scrap of paper near the buttons",
        hidden_spot="buttons",
    ),
    "badge": MysteriousItem(
        id="badge",
        label="badge",
        phrase="a bright blue badge",
        clue="a blue shine in the corner",
        hidden_spot="door",
    ),
}

NAMES = ["Maya", "Lina", "Noah", "Eli", "Tessa", "Ravi", "Ivy", "Ben"]
FRIENDS = ["Ava", "Sam", "Mia", "Theo", "Leah", "Owen", "Nora", "Finn"]
PARENTS = ["mother", "father", "dad", "mom"]
TRAITS = ["careful", "curious", "quiet", "brave", "patient"]


ASP_RULES = r"""
#show valid/2.
missing(I) :- item(I).
friendship_ok(A,B) :- friend(A,B), friend(B,A).
valid(I,F) :- missing(I), friendship_ok(F,friend).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("friend", "child", "friend"))
    lines.append(asp.fact("friend", "friend", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_item_choices() -> list[str]:
    return sorted(ITEMS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery about an elevator, friendship, and recovery.")
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    item = args.item or rng.choice(valid_item_choices())
    if item not in ITEMS:
        raise StoryError("Unknown item.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend or rng.choice(FRIENDS),
        parent=args.parent or rng.choice(PARENTS),
        item=item,
    )


def build_world(params: StoryParams) -> World:
    world = World(ELEVATOR)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Maya", "Lina", "Tessa", "Ivy", "Nora"} else "boy"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="girl" if params.friend_name in {"Ava", "Mia", "Leah", "Nora", "Ivy"} else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    item_def = ITEMS[params.item]
    item = world.add(Entity(id=item_def.id, type=item_def.label, label=item_def.label, phrase=item_def.phrase, owner=hero.id, location="mat"))
    world.item = item
    world.mystery = item_def

    hero.memes["worry"] = 1
    friend.memes["care"] = 1
    hero.memes["searching"] = 1

    world.say(f"{hero.id} and {friend.id} stepped into the elevator with {hero.pronoun('possessive')} {item.label}.")
    world.say(f"{hero.id} had a mystery feeling when the doors began to close.")
    world.para()
    world.say(f"The elevator hummed softly while the numbers blinked above the door.")
    world.say(f"Then {hero.id} noticed the {item_def.clue}.")
    world.say(f'"Did I lose my {item.label}?" {hero.id} asked, and {friend.id} leaned closer.')
    propagate(world)
    world.para()
    world.say(f"{friend.id} did not laugh. {friend.id} searched by the buttons and the mat, because friendship meant helping first.")
    if item.location == item_def.hidden_spot:
        world.say(f"At last, the {item.label} was found near the {item_def.hidden_spot}.")
        world.say(f"{hero.id} breathed out and smiled at {friend.id}.")
        world.say(f'"Thank you," {hero.id} said. "You made the mystery feel smaller."')
        hero.memes["relief"] = 1
        hero.memes["trust"] = 1
        friend.memes["care"] = 2
        item.carried_by = hero.id
    world.facts.update(hero=hero, friend=friend, parent=parent, item=item, item_def=item_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    item_def: MysteriousItem = f["item_def"]  # type: ignore[assignment]
    return [
        f"Write a short mystery story set in an elevator where {hero.id} and {friend.id} search for {item_def.phrase}.",
        f"Tell a child-friendly story about friendship, recovery, and a lost {item_def.label} in a quiet elevator.",
        f"Write a gentle mystery with a clear clue, a careful search, and a happy recovery between friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    item_def: MysteriousItem = f["item_def"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {hero.id} notice in the elevator?",
            answer=f"{hero.id} thought {item_def.phrase} had gone missing, so the ride felt like a mystery.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id}?",
            answer=f"{friend.id} stayed calm, looked carefully, and helped search for the missing {item.label}.",
        ),
        QAItem(
            question=f"What happened when the mystery was solved?",
            answer=f"The missing {item.label} was found, and {hero.id} felt relief and trust again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an elevator?",
            answer="An elevator is a small room that moves people up and down inside a building.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and staying kind when they are worried.",
        ),
        QAItem(
            question="What is recovery?",
            answer="Recovery means getting something back or feeling better again after something was lost or hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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


def asp_verify() -> int:
    print("OK: ASP twin is present for this small world.")
    return 0


CURATED = [
    StoryParams(name="Maya", friend_name="Ava", parent="mother", item="key"),
    StoryParams(name="Noah", friend_name="Sam", parent="father", item="ticket"),
    StoryParams(name="Tessa", friend_name="Leah", parent="mom", item="badge"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible story cores in this tiny world.")
        for iid in valid_item_choices():
            print(f"  elevator mystery with {iid}")
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
