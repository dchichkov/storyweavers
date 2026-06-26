#!/usr/bin/env python3
"""
storyworlds/worlds/amount_happy_ending_quest_comedy.py
=======================================================

A tiny comedy-leaning quest world about a child trying to gather the right
amount of something, getting into a few silly snags, and ending with a happy
fix.

Premise:
- A child wants to collect an amount of bright tokens for a cheerful goal.
- A helper keeps counting wrong in a funny way.
- The child learns the exact amount matters, not just "lots."
- The ending lands on a warm, successful, happy note.

This world is small on purpose:
- one quest target amount
- one location
- one helper
- one comic obstacle
- one resolution
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    thing: str
    noun: str
    verb: str
    amount_target: int
    danger: str
    obstacle: str
    comic_miscount: str
    helper_fix: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    gender: str
    helper_name: str
    helper_type: str
    target_amount: int
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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


def _say_amount(n: int) -> str:
    words = {
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
    }
    return words.get(n, str(n))


PLACES = {
    "market": Place("the market", indoors=False, affords={"berries", "buttons"}),
    "garden": Place("the garden", indoors=False, affords={"flowers", "berries"}),
    "kitchen": Place("the kitchen", indoors=True, affords={"cookies", "spoons"}),
    "attic": Place("the attic", indoors=True, affords={"buttons", "coins"}),
}

QUESTS = {
    "berries": Quest(
        id="berries",
        thing="berries",
        noun="berry",
        verb="pick",
        amount_target=7,
        danger="the basket might topple if it gets too full",
        obstacle="a squirrel kept showing up and stealing the bright ones",
        comic_miscount="the helper counted a strawberry as two berries because it was 'extra juicy'",
        helper_fix="they used tiny scoops and counted out loud one by one",
        sparkle="the basket ended up full of red dots like happy buttons",
        tags={"fruit", "counting", "garden"},
    ),
    "buttons": Quest(
        id="buttons",
        thing="buttons",
        noun="button",
        verb="gather",
        amount_target=6,
        danger="the jar could get mixed up with the loose thread",
        obstacle="the helper kept trying to sort the buttons by color and made a silly rainbow pile",
        comic_miscount="one shiny button rolled under the chair and everyone counted it twice by mistake",
        helper_fix="they lined the buttons up in a neat row and counted again",
        sparkle="the jar finally held exactly the right number, and it looked like a pocket of tiny moons",
        tags={"counting", "sewing"},
    ),
    "cookies": Quest(
        id="cookies",
        thing="cookies",
        noun="cookie",
        verb="carry",
        amount_target=5,
        danger="the plate might wobble if it got overloaded",
        obstacle="the helper kept sniffing the cookies and saying they looked 'too brave to count'",
        comic_miscount="a crumb fell off and the helper insisted it was a 'half-cookie,' which made everyone laugh",
        helper_fix="they used a tray and counted each cookie after it landed safely",
        sparkle="the tray arrived with the right amount and everybody got a grin with their snack",
        tags={"baking", "counting", "kitchen"},
    ),
    "coins": Quest(
        id="coins",
        thing="coins",
        noun="coin",
        verb="collect",
        amount_target=8,
        danger="the pouch could jingle so loudly it made pigeons stare",
        obstacle="the helper kept tipping the pouch upside down to hear the clink-clink joke again",
        comic_miscount="one coin slipped into the helper's sleeve, so the count became a tiny mystery",
        helper_fix="they emptied the pouch onto the table and counted from the start",
        sparkle="the pouch ended with the exact amount, and the coins sounded like a cheerful rain",
        tags={"money", "counting", "shiny"},
    ),
}


GIRL_NAMES = ["Mina", "Lily", "Zoe", "Nora", "Pia", "Ivy"]
BOY_NAMES = ["Leo", "Ben", "Toby", "Eli", "Max", "Noah"]
HELPERS = {
    "cat": "cat",
    "dog": "dog",
    "sibling": "sibling",
    "neighbor": "neighbor",
}

TRAITS = ["curious", "cheerful", "silly", "spirited", "patient"]


ASP_RULES = r"""
quest_ready(P, Q, N) :- place(P), quest(Q), amount(Q, N), affords(P, Q).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("amount", qid, q.amount_target))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show quest_ready/3."))
    asp_set = set(asp.atoms(model, "quest_ready"))
    py_set = {(p, q, n) for p, place in PLACES.items() for q, quest in QUESTS.items() if q in place.affords for n in [quest.amount_target]}
    if asp_set == py_set:
        print(f"OK: clingo matches Python ({len(py_set)} facts).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in py:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy quest storyworld about a funny amount to gather.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("--target-amount", type=int)
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


def valid_combo(place: str, quest: str) -> bool:
    return quest in PLACES[place].affords


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest and not valid_combo(args.place, args.quest):
        raise StoryError(f"(No story: {args.quest} does not fit in {args.place}.)")
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice([q for q in QUESTS if valid_combo(place, q)])
    if not valid_combo(place, quest):
        raise StoryError("(No story: no valid quest for the chosen place.)")
    q = QUESTS[quest]
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(list(HELPERS))
    helper_name = args.helper_name or rng.choice(["Pip", "Momo", "Taz", "Dede"])
    target_amount = args.target_amount or q.amount_target
    if target_amount != q.amount_target:
        raise StoryError(f"(No story: this quest needs exactly {_say_amount(q.amount_target)} {q.noun}s.)")
    return StoryParams(place=place, quest=quest, hero_name=hero_name, gender=gender,
                       helper_name=helper_name, helper_type=helper_type, target_amount=target_amount)


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    world = World(place)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    goal = world.add(Entity(id="goal", type=quest.noun, label=quest.thing, owner=hero.id, plural=True))
    hero.memes["hope"] = 1
    helper.memes["silliness"] = 1

    # Setup
    world.say(f"{hero.id} had a very important quest: {_say_amount(quest.amount_target)} {quest.thing}.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {quest.verb} them at {place.name}, because the result would be for a happy surprise.")
    world.say(f"{helper.id} came along, ready to help, but also ready to make things funny.")

    # Middle
    world.para()
    world.say(f"At {place.name}, {hero.id} began to {quest.verb} one by one.")
    hero.meters["collected"] = 0
    while hero.meters["collected"] < quest.amount_target:
        hero.meters["collected"] += 1
        collected = int(hero.meters["collected"])
        if collected == 2:
            world.say(f"{helper.id} pointed at a shiny one and said, '{quest.comic_miscount}'")
            helper.memes["comic_confusion"] = helper.memes.get("comic_confusion", 0) + 1
        elif collected == quest.amount_target - 2:
            world.say(f"Then a silly little wobble nearly spoiled the count, because {quest.obstacle}.")
            hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        elif collected == quest.amount_target - 1:
            world.say(f"{hero.id} laughed anyway and kept going, because the quest still needed just one more.")
    world.say(f"At last, {hero.id} stopped and checked the pile very carefully.")

    # Resolution
    world.para()
    world.say(f"They used a calm trick: {quest.helper_fix}.")
    world.say(f"That worked, and the final amount was exactly {_say_amount(quest.amount_target)}.")
    world.say(f"{quest.sparkle.capitalize()}.")
    world.say(f"{hero.id} smiled so wide that even {helper.id} stopped joking for a second and grinned back.")
    hero.memes["joy"] = 2
    hero.memes["relief"] = 1
    helper.memes["joy"] = 1
    world.facts = {
        "hero": hero,
        "helper": helper,
        "goal": goal,
        "quest": quest,
        "place": place,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    place = f["place"]
    return [
        f'Write a short funny story for a child about {hero.id} trying to gather {_say_amount(quest.amount_target)} {quest.thing} at {place.name}.',
        f"Tell a comedy-leaning quest where a small character needs exactly {_say_amount(quest.amount_target)} {quest.noun}s and a helper keeps making counting mistakes.",
        f"Write a happy-ending story that includes the word 'amount' and ends with the right amount finally counted.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {hero.id}'s quest?",
            answer=f"{hero.id} needed to get exactly {_say_amount(quest.amount_target)} {quest.thing} at {place.name}.",
        ),
        QAItem(
            question=f"Who helped make the quest funny?",
            answer=f"{helper.id} helped, but {helper.id} also made silly counting mistakes along the way.",
        ),
        QAItem(
            question=f"Why did the story need an exact amount?",
            answer=f"It needed the exact amount because the goal only worked when there were exactly {_say_amount(quest.amount_target)} {quest.noun}s.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when the group counted carefully and got the exact amount they needed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    if q.id == "coins":
        return [QAItem(question="What are coins?", answer="Coins are small pieces of money made of metal.")]
    if q.id == "cookies":
        return [QAItem(question="Why do cookies smell good?", answer="Cookies can smell good because they are baked with sweet ingredients like sugar and butter.")]
    if q.id == "berries":
        return [QAItem(question="What is a berry?", answer="A berry is a small, juicy fruit, and many berries can be eaten as snacks or in desserts.")]
    return [QAItem(question="What is counting?", answer="Counting is saying numbers in order to know how many things there are.")]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_ready/3."))
    return sorted(set(asp.atoms(model, "quest_ready")))


def asp_verify_wrapper() -> int:
    return asp_verify()


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(place="garden", quest="berries", hero_name="Mina", gender="girl", helper_name="Pip", helper_type="cat", target_amount=7),
    StoryParams(place="kitchen", quest="cookies", hero_name="Leo", gender="boy", helper_name="Momo", helper_type="sibling", target_amount=5),
    StoryParams(place="attic", quest="coins", hero_name="Nora", gender="girl", helper_name="Taz", helper_type="neighbor", target_amount=8),
    StoryParams(place="market", quest="buttons", hero_name="Eli", gender="boy", helper_name="Dede", helper_type="dog", target_amount=6),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show quest_ready/3."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_ready/3."))
        facts = asp.atoms(model, "quest_ready")
        print(f"{len(facts)} quest-ready combos:")
        for p, q, n in facts:
            print(f"  {p} {q} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
