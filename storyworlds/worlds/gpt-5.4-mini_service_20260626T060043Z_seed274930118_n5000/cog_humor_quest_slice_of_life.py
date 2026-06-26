#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, a missing cog, a humorous quest,
and a gentle fix that makes the day feel complete.

The seed image behind this world:
- A child notices one tiny cog is missing from a little machine.
- The search becomes a funny, household quest.
- The ending proves the missing piece was found and the machine works again.

This script follows the Storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    search_places: list[str]
    clue: str
    funny_obstacle: str
    resolution: str
    keyword: str = "cog"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    offer: str
    line: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    hero_name: str
    hero_gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, {"search", "snack"}),
    "workbench": Place("workbench", "the workbench", True, {"search", "repair"}),
    "living_room": Place("living_room", "the living room", True, {"search", "rest"}),
    "laundry_room": Place("laundry_room", "the laundry room", True, {"search"}),
}

QUESTS = {
    "missing_cog": Quest(
        id="missing_cog",
        goal="find the missing cog",
        search_places=["kitchen", "living_room", "laundry_room", "workbench"],
        clue="a small silver click came from somewhere under a chair",
        funny_obstacle="the cat sat on the instruction sheet like it was the most important throne in town",
        resolution="the cog had rolled into a teacup and was hiding under a cookie crumb",
        keyword="cog",
        tags={"cog", "machine", "humor"},
    ),
    "jammed_toy": Quest(
        id="jammed_toy",
        goal="fix the wind-up toy",
        search_places=["workbench", "living_room", "kitchen"],
        clue="the toy gave one brave whirr and then stopped with a sigh",
        funny_obstacle="the little screws kept sliding toward the edge like they wanted to go on their own quest",
        resolution="the right cog was tucked inside the toy's back cover",
        keyword="cog",
        tags={"cog", "toy", "humor"},
    ),
    "clock_tick": Quest(
        id="clock_tick",
        goal="make the shelf clock tick again",
        search_places=["living_room", "workbench", "kitchen"],
        clue="the clock made a tiny thunk instead of a tick",
        funny_obstacle="grandpa tried to look serious, but his glasses slipped and made everyone giggle",
        resolution="one brass cog had popped loose and landed behind the clock stand",
        keyword="cog",
        tags={"cog", "clock", "humor"},
    ),
}

PRIZES = {
    "small_cog": Prize("cog", "a tiny brass cog", "cog", "pocket"),
    "toolbox_cog": Prize("cog", "a silver cog from the toolbox", "cog", "workbench"),
    "clock_cog": Prize("cog", "a round clock cog", "cog", "clock"),
}

HELPERS = {
    "grandma": Helper("grandma", "grandma", "bring a bowl and a flashlight", "Let’s not panic; little things like to hide in plain sight."),
    "grandpa": Helper("grandpa", "grandpa", "kneel down and look under the table", "A good search starts with a calm back and a careful hand."),
    "neighbor": Helper("neighbor", "the neighbor", "check the floor mats and the chair legs", "Tiny parts love to travel when nobody is watching."),
}

HERO_NAMES = ["Mina", "Jules", "Nora", "Theo", "Pip", "Ivy", "Owen", "Lena"]
TRAITS = ["curious", "cheerful", "thoughtful", "silly", "patient", "playful"]


def _story_bits() -> list[tuple[str, str]]:
    return [
        ("cog", "What is a cog?", "A cog is a small round gear with teeth that helps a machine move."),
        ("machine", "What does a machine do?", "A machine is something with parts that work together to help do a job."),
        ("tool", "Why are tools useful?", "Tools help people fix, build, and open things more carefully."),
        ("search", "What does it mean to search?", "To search means to look carefully for something that is missing."),
        ("humor", "Why do funny mistakes help a story?", "Funny mistakes can make a story feel light, lively, and easy to smile at."),
    ]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for qid in place.affords | {"search"}:
            for pid in PRIZES:
                if qid in {"search", "repair"}:
                    combos.append((place_id, qid if qid in QUESTS else "missing_cog", pid))
    # slim down to the real valid choices that match the quest logic
    res = []
    for place_id in PLACES:
        for quest_id in QUESTS:
            for prize_id in PRIZES:
                if place_id in {"kitchen", "workbench", "living_room", "laundry_room"}:
                    res.append((place_id, quest_id, prize_id))
    return sorted(set(res))


def explain_invalid(place: str, quest: str, prize: str) -> str:
    return f"(No story: the combination {place!r}, {quest!r}, {prize!r} does not fit a small, plausible cog-search.)"


def choose_name(gender: str, rng: random.Random) -> str:
    if gender == "girl":
        return rng.choice(["Mina", "Nora", "Ivy", "Lena", "Pip"])
    return rng.choice(["Jules", "Theo", "Owen", "Max", "Eli"])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life humor quest storyworld about a missing cog.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    prize = args.prize or rng.choice(list(PRIZES))
    if args.place and args.quest and args.prize and (args.place, args.quest, args.prize) not in valid_combos():
        raise StoryError(explain_invalid(args.place, args.quest, args.prize))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or choose_name(gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, hero_name=name, hero_gender=gender, helper=helper, trait=trait)


def _gesture(world: World, actor: Entity, thing: str, amount: float = 1.0) -> None:
    actor.meters[thing] = actor.meters.get(thing, 0.0) + amount


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]
    helper = HELPERS[params.helper]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, traits=["little", params.trait]))
    adult = world.add(Entity(id=helper.id, kind="character", type="grandmother" if helper.id == "grandma" else "grandfather" if helper.id == "grandpa" else "adult", label=helper.label))
    cog = world.add(Entity(id="cog", type="cog", label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=adult.id, plural=prize.plural))
    world.facts.update(hero=hero, adult=adult, cog=cog, quest=quest, prize=prize, helper=helper, place=place)

    world.say(f"{hero.id} was a {params.trait} little {params.hero_gender} who liked quiet afternoons and tiny, useful things.")
    world.say(f"One day, {hero.id} noticed a {quest.keyword} was missing from the little machine on {place.label}.")
    world.say(f"That made the whole room feel a bit funny, because {quest.goal} had suddenly become a very important quest.")

    world.para()
    world.say(f"{hero.id} and {helper.label} started looking around together.")
    world.say(f"{quest.clue.capitalize()}.")
    world.say(f"Then came the funniest part: {quest.funny_obstacle}.")
    _gesture(world, hero, "joy", 1.0)
    _gesture(world, hero, "curiosity", 1.0)

    world.para()
    world.say(f"{hero.id} checked under a chair, then by the window, then beside the snack bowl.")
    world.say(f"{helper.line} {helper.offer.capitalize()}.")
    world.say(f"At last, they found that {quest.resolution}.")
    _gesture(world, hero, "relief", 1.0)
    _gesture(world, adult, "warmth", 1.0)

    world.para()
    world.say(f"{hero.id} fit the {quest.keyword} back where it belonged, and the little machine woke up with a happy click.")
    world.say(f"{hero.id} grinned at {helper.label} and said the day had turned into the best kind of small quest.")
    world.say(f"By the end, the room was calm again, the {quest.keyword} was back in place, and even the cat looked impressed.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short slice-of-life story for a child where {hero.id} has a humorous quest to {quest.goal}.',
        f"Tell a gentle story about a missing cog, a careful search, and a funny household surprise.",
        f"Write a story with the word '{quest.keyword}' that ends with a child smiling because the little machine works again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    quest = f["quest"]
    place = f["place"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {place.label}?",
            answer=f"{hero.id} was trying to {quest.goal}. The missing {quest.keyword} had turned the day into a small quest.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the {quest.keyword}?",
            answer=f"{adult.label.capitalize()} helped {hero.id} look for it. They searched together and kept the mood light and funny.",
        ),
        QAItem(
            question=f"What did they find when the search ended?",
            answer=f"They found {quest.resolution}. After that, the {quest.keyword} could go back into the little machine.",
        ),
        QAItem(
            question=f"Why was the room funny while they searched?",
            answer=f"The room felt funny because {quest.funny_obstacle}. That made the search feel like a small, silly adventure.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {quest.keyword} was back in place, the machine worked again, and {hero.id} felt proud and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for _, q, a in _story_bits()]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
valid(P,Q,R) :- place(P), quest(Q), prize(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams("kitchen", "missing_cog", "small_cog", "Mina", "girl", "grandma", "curious"),
    StoryParams("workbench", "jammed_toy", "toolbox_cog", "Theo", "boy", "grandpa", "silly"),
    StoryParams("living_room", "clock_tick", "clock_cog", "Nora", "girl", "neighbor", "thoughtful"),
]


def _asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, prize) combos:")
        for row in combos:
            print(" ", row)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
