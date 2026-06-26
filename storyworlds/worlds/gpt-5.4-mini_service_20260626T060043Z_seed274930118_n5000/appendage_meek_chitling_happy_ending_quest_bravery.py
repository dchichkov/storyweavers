#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a meek chitling, an important appendage,
and a gentle quest that ends in bravery and a happy ending.
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


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"safe": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "bravery": 0.0, "meek": 0.0})


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestDef:
    id: str
    verb: str
    goal: str
    concern: str
    remedy: str
    ending: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Thing] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, thing: Thing) -> Thing:
        self.entities[thing.id] = thing
        return thing

    def get(self, eid: str) -> Thing:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", indoors=True, affords={"snack", "tidy"}),
    "garden": Place("garden", "the garden", indoors=False, affords={"snack", "fetch", "tidy"}),
    "library": Place("library", "the little library", indoors=True, affords={"read", "fetch"}),
    "porch": Place("porch", "the porch", indoors=False, affords={"snack", "fetch"}),
}

QUESTS = {
    "snack": QuestDef(
        id="snack",
        verb="carry snacks",
        goal="bring a warm snack to a friend",
        concern="the snack could spill from the little tray",
        remedy="hold the tray with both hands and walk slowly",
        ending="the snack stayed neat and everyone smiled",
        keyword="snack",
        tags={"snack", "care"},
    ),
    "fetch": QuestDef(
        id="fetch",
        verb="fetch a lost button",
        goal="find a tiny button behind the bench",
        concern="the button was easy to miss in the grass",
        remedy="look carefully, one step at a time",
        ending="the button was found and tucked safely away",
        keyword="button",
        tags={"seek", "small", "care"},
    ),
    "tidy": QuestDef(
        id="tidy",
        verb="tidy the play corner",
        goal="put the blocks back in their basket",
        concern="the blocks might tumble out again",
        remedy="sort them by color and use a steady stack",
        ending="the corner looked calm and bright",
        keyword="blocks",
        tags={"tidy", "care"},
    ),
    "read": QuestDef(
        id="read",
        verb="read a picture book",
        goal="finish a quiet story on the rug",
        concern="a page might fold the wrong way",
        remedy="turn each page gently with one finger",
        ending="the book closed softly and the room felt peaceful",
        keyword="book",
        tags={"quiet", "care"},
    ),
}

NAMES = ["Mina", "Pip", "Toby", "Luna", "Nell", "Rory", "Iris", "Otto"]
FRIEND_NAMES = ["Bram", "Suki", "Milo", "June", "Ada", "Nico", "Pearl", "Tess"]
ADJECTIVES = ["meek", "gentle", "shy", "kind", "soft-spoken"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a meek chitling on a small quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    if quest not in PLACES[place].affords:
        raise StoryError(f"(No story: {QUESTS[quest].verb} does not fit at {PLACES[place].label}.)")
    return StoryParams(
        place=place,
        quest=quest,
        hero_name=args.name or rng.choice(NAMES),
        friend_name=args.friend or rng.choice(FRIEND_NAMES),
    )


def tell(place: Place, quest: QuestDef, hero_name: str, friend_name: str) -> World:
    world = World(place)
    hero = world.add(Thing(id=hero_name, kind="character", label=hero_name))
    friend = world.add(Thing(id=friend_name, kind="character", label=friend_name))
    appendage = world.add(Thing(
        id="appendage",
        kind="thing",
        label="appendage",
        phrase="a small ribbon-tied appendage",
        owner=hero.id,
        protective=False,
        meters={"safe": 1.0},
    ))
    hero.memes["meek"] = 1.0
    hero.memes["joy"] = 0.5

    world.say(
        f"{hero_name} was a meek little chitling who lived near {place.label}. "
        f"{hero_name} had a special appendage, a small ribbon-tied appendage, and tried to keep it neat."
    )
    world.say(
        f"One morning, {hero_name} wanted to {quest.verb}. "
        f"{friend_name} smiled and said the day could be a tiny quest, nothing too grand, just enough for brave practice."
    )

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["appendage"] = appendage
    world.facts["quest"] = quest

    if quest.id == "snack":
        world.say(
            f"They went to {place.label} with a warm snack on a little tray. "
            f"{quest.concern.capitalize()}, so {hero_name} took a breath and held still."
        )
        hero.memes["worry"] += 0.3
        hero.memes["bravery"] += 1.0
        world.say(
            f"Even though {hero_name} felt meek, {hero_name} kept both hands steady. "
            f"{quest.remedy.capitalize()}."
        )
    elif quest.id == "fetch":
        world.say(
            f"They searched {place.label} for the lost button. "
            f"{quest.concern.capitalize()}, and {hero_name} almost gave up after the first look."
        )
        hero.memes["worry"] += 0.4
        world.say(
            f"Then {friend_name} knelt beside {hero_name} and said the tiniest searches still counted as bravery. "
            f"{quest.remedy.capitalize()}."
        )
        hero.memes["bravery"] += 1.0
    elif quest.id == "tidy":
        world.say(
            f"The play corner was messy, with blocks in a little heap. "
            f"{hero_name} did not like loud, busy jobs, but wanted to help."
        )
        hero.memes["bravery"] += 0.8
        world.say(
            f"{friend_name} sorted the colors first, and {hero_name} followed along. "
            f"{quest.remedy.capitalize()}."
        )
    else:
        world.say(
            f"{place.label} was quiet, and {hero_name} chose a picture book with bright animals inside. "
            f"{quest.concern.capitalize()}, so {hero_name} turned pages with care."
        )
        hero.memes["bravery"] += 0.6
        world.say(
            f"{friend_name} sat nearby like a soft shadow while {hero_name} read. "
            f"{quest.remedy.capitalize()}."
        )

    hero.meters["safe"] = 1.0
    appendage.meters["safe"] = 1.0
    hero.memes["joy"] += 1.2
    hero.memes["meek"] = 1.0

    world.say(
        f"In the end, {quest.ending}. {hero_name}'s appendage stayed neat, "
        f"{hero_name} felt a little braver, and the day ended in a happy ending."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    hero = world.facts["hero"]
    return [
        f"Write a gentle slice-of-life story about a meek chitling named {hero.id} and a small quest.",
        f"Tell a short story where {hero.id} must {q.verb} and learns bravery without changing the calm mood.",
        f"Write a kid-friendly happy ending story that includes an appendage, a quest, and bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    quest = world.facts["quest"]
    place = world.place.label
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a meek little chitling with a special appendage, and {friend.id}, who helps during a small quest at {place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.verb}. It was a small, everyday quest, but it still took bravery.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {quest.ending}. {hero.id} felt braver, and the appendage stayed neat and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does meek mean?",
            answer="Meek means quiet, gentle, and not pushy.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or errand someone sets out to complete, even if it is small and simple.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something hard or new even when you feel nervous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} meters={e.meters} memes={e.memes}")
    lines.append(f"place={world.place.id}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
place(kitchen;garden;library;porch).
quest(snack;fetch;tidy;read).

affords(kitchen,snack). affords(kitchen,tidy).
affords(garden,snack). affords(garden,fetch). affords(garden,tidy).
affords(library,read). affords(library,fetch).
affords(porch,snack). affords(porch,fetch).

reasonable(P,Q) :- affords(P,Q).
#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for q in sorted(place.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for qid in place.affords:
            out.append((pid, qid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_reasonable())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print("only in clingo:", sorted(a - b))
    if b - a:
        print("only in python:", sorted(b - a))
    return 1


def explain_rejection(place: str, quest: str) -> str:
    return f"(No story: {QUESTS[quest].verb} does not fit at {PLACES[place].label}.)"


def resolve_reasonable(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest and (args.place, args.quest) not in valid_combos():
        raise StoryError(explain_rejection(args.place, args.quest))
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(combos)
    return StoryParams(place=place, quest=quest, hero_name=args.name or rng.choice(NAMES), friend_name=args.friend or rng.choice(FRIEND_NAMES))


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], params.hero_name, params.friend_name)
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
    StoryParams(place="kitchen", quest="snack", hero_name="Mina", friend_name="Bram"),
    StoryParams(place="garden", quest="fetch", hero_name="Pip", friend_name="Suki"),
    StoryParams(place="library", quest="read", hero_name="Luna", friend_name="Nico"),
    StoryParams(place="garden", quest="tidy", hero_name="Toby", friend_name="June"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_reasonable()
        print(f"{len(combos)} reasonable combos:")
        for c in combos:
            print(" ", c)
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
                params = resolve_reasonable(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
