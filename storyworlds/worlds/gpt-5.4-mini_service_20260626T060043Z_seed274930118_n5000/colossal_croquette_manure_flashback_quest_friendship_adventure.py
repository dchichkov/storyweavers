#!/usr/bin/env python3
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    companion: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "brother", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    features: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    risk: str
    flashback_trigger: str
    fix: str


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Thing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.flashback_seen = False

    def add(self, e: Thing) -> Thing:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Thing:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _story_setup(world: World, hero: Thing, friend: Thing, snack: Thing, manure: Thing) -> None:
    world.say(
        f"{hero.id} and {friend.id} were on a quest in {world.place.label}, "
        f"looking for a colossal croquette for their picnic."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had promised not to let the snack get lost, "
        f"because the croquette was big enough to share."
    )
    world.say(
        f"Near the barn gate, a lump of manure sat like a dark hill beside the path."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    friend.memes["hope"] = friend.memes.get("hope", 0) + 1
    snack.meters["colossal"] = 1
    manure.meters["messy"] = 1


def _flashback(world: World, hero: Thing, friend: Thing, snack: Thing) -> None:
    if world.flashback_seen:
        return
    world.flashback_seen = True
    world.say(
        f"As {hero.id} stared at the path, a flashback came back."
    )
    world.say(
        f"Last autumn, {friend.id} had shared the last bite of a croquette when {hero.id} "
        f"was sad, and that small kindness had turned them into true friends."
    )
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    snack.memes["memory"] = snack.memes.get("memory", 0) + 1


def _risk(world: World, hero: Thing, snack: Thing, manure: Thing) -> None:
    if "risk" in world.fired:
        return
    world.fired.add("risk")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    snack.meters["at_risk"] = 1
    world.say(
        f"Then the wind nudged the colossal croquette toward the manure, and {hero.id}'s heart skipped."
    )
    world.say(
        f"If the croquette landed there, the snack would be ruined before the quest was done."
    )


def _turn(world: World, hero: Thing, friend: Thing, snack: Thing) -> None:
    if "turn" in world.fired:
        return
    world.fired.add("turn")
    world.say(
        f"{friend.id} pointed to an old crate and said they could use it like a bridge."
    )
    world.say(
        f"{hero.id} nodded, and together they edged forward with slow, careful steps."
    )
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    friend.memes["brave"] = friend.memes.get("brave", 0) + 1
    snack.meters["moved"] = 1


def _resolution(world: World, hero: Thing, friend: Thing, snack: Thing, manure: Thing) -> None:
    if "resolve" in world.fired:
        return
    world.fired.add("resolve")
    snack.meters["saved"] = 1
    manure.meters["avoided"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"They lifted the colossal croquette away from the manure and set it safely on a clean cloth."
    )
    world.say(
        f"{hero.id} laughed with relief, and {friend.id} laughed too, because the quest had worked."
    )
    world.say(
        f"By the time they ate, the croquette was still warm, and their friendship felt even warmer."
    )


def tell(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    snack = world.get("snack")
    manure = world.get("manure")
    _story_setup(world, hero, friend, snack, manure)
    world.para()
    _flashback(world, hero, friend, snack)
    _risk(world, hero, snack, manure)
    world.para()
    _turn(world, hero, friend, snack)
    _resolution(world, hero, friend, snack, manure)


SETTINGS = {
    "barnyard": Place("barnyard", "the barnyard", indoors=False, features={"barn", "path", "crate"}),
    "market": Place("market", "the market square", indoors=False, features={"stall", "cart", "cloth"}),
    "garden": Place("garden", "the kitchen garden", indoors=False, features={"bed", "basket", "path"}),
}

QUESTS = {
    "picnic": Quest(
        id="picnic",
        title="Picnic Quest",
        goal="bring home a colossal croquette",
        risk="the croquette might fall into manure",
        flashback_trigger="a remembered shared snack",
        fix="use a crate like a bridge and carry it on a cloth",
    ),
    "delivery": Quest(
        id="delivery",
        title="Delivery Quest",
        goal="deliver a colossal croquette to a neighbor",
        risk="the croquette might tumble into manure on the way",
        flashback_trigger="a remembered promise",
        fix="balance it carefully on a tray",
    ),
    "rescue": Quest(
        id="rescue",
        title="Rescue Quest",
        goal="save a colossal croquette from the muck",
        risk="the croquette might land in manure and be spoiled",
        flashback_trigger="a remembered friendship",
        fix="lift it together with a clean board",
    ),
}

NAME_POOL = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Lily", "Owen"]
BOY = ["boy", "father", "brother"]
GIRL = ["girl", "mother", "sister"]


ASP_RULES = r"""
place(barnyard;market;garden).
quest(picnic;delivery;rescue).
risk(picnic,manure_fall).
risk(delivery,manure_fall).
risk(rescue,manure_fall).
flashback(picnic,shared_snack).
flashback(delivery,promise).
flashback(rescue,friendship).
fix(picnic,crate_bridge).
fix(delivery,careful_tray).
fix(rescue,clean_board).

valid(P,Q) :- place(P), quest(Q), risk(Q,manure_fall), flashback(Q,_), fix(Q,_).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, q) for p in SETTINGS for q in QUESTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about a colossal croquette, manure, flashback, quest, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        pool = NAME_POOL
        name = rng.choice(pool)
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend_name = args.friend_name or rng.choice([n for n in NAME_POOL if n != name])

    return StoryParams(
        place=place,
        quest=quest,
        hero_name=name,
        hero_type=gender,
        friend_name=friend_name,
        friend_type=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    quest = QUESTS[params.quest]
    world = World(place, quest)
    hero = world.add(Thing("hero", kind="character", type=params.hero_type, id=params.hero_name))
    friend = world.add(Thing("friend", kind="character", type=params.friend_type, id=params.friend_name))
    snack = world.add(Thing("snack", type="food", label="croquette", phrase="a colossal croquette", plural=False))
    manure = world.add(Thing("manure", type="stuff", label="manure"))

    tell(world)
    world.facts.update(place=place, quest=quest, hero=hero, friend=friend, snack=snack, manure=manure)

    prompts = [
        f"Write an adventurous story about {params.hero_name} and {params.friend_name} on a quest in {place.label}.",
        f"Tell a child-friendly tale that includes a colossal croquette, manure, a flashback, and friendship.",
        f"Write a short adventure where two friends solve a problem with a croquette near manure.",
    ]

    story_qa = [
        QAItem(
            question=f"What were {params.hero_name} and {params.friend_name} looking for?",
            answer="They were looking for a colossal croquette for their picnic quest.",
        ),
        QAItem(
            question=f"What did the flashback remind {params.hero_name} of?",
            answer=f"It reminded {params.hero_name} that {params.friend_name} had once shared a croquette and been a kind friend.",
        ),
        QAItem(
            question="Why did they have to be careful near the manure?",
            answer="They had to be careful because the croquette could have fallen into the manure and been ruined.",
        ),
        QAItem(
            question="How did the quest end?",
            answer="They used a careful plan, saved the croquette, and shared it together at the end.",
        ),
    ]

    world_qa = [
        QAItem(question="What is a croquette?", answer="A croquette is a small, crispy food, often made from mashed potatoes or meat and then fried."),
        QAItem(question="What is manure?", answer="Manure is animal waste that can help plants grow when it is used as fertilizer."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is a part of a story that shows something that happened earlier."),
        QAItem(question="What is a quest?", answer="A quest is a special trip or mission to find, fix, or bring something important."),
        QAItem(question="What is friendship?", answer="Friendship is when people care about each other, help each other, and enjoy being together."),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, {k: v for k, v in e.meters.items() if v}, {k: v for k, v in e.memes.items() if v})
    if qa:
        print()
        for section, items in [("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)]:
            print(f"== {section} ==")
            if section == "Prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(len(valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for quest in QUESTS:
                p = StoryParams(place=place, quest=quest, hero_name="Mia", hero_type="girl", friend_name="Leo", friend_type="boy")
                samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
