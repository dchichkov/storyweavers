#!/usr/bin/env python3
"""
romp_muggy_hungry_moral_value_happy_ending.py

A tiny storyworld for a tall-tale style romp on a muggy day.
The core premise is simple: somebody is hungry, wants to romp, and learns
a moral lesson about sharing, patience, or kindness before the happy ending.

This script is standalone and follows the Storyweavers contract.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    muggy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    name: str
    hunger_word: str
    urge: str
    delightful: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    plural: bool = False
    kind: str = "food"
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralChoice:
    id: str
    offer: str
    lesson: str
    action: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "muggy"

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the meadow", muggy=True, affords={"romp"}),
    "orchard": Setting(place="the orchard", muggy=True, affords={"romp"}),
    "lane": Setting(place="the lantern lane", muggy=True, affords={"romp"}),
}

NEEDS = {
    "hungry": Need(
        id="hungry",
        name="hungry",
        hunger_word="hungry",
        urge="romp toward the picnic basket",
        delightful="the smell of warm bread",
        consequence="a rumbling tummy",
        tags={"hungry", "food"},
    ),
    "thirsty": Need(
        id="thirsty",
        name="thirsty",
        hunger_word="thirsty",
        urge="dash for the water jug",
        delightful="the cool splash of cider",
        consequence="a dry mouth",
        tags={"thirsty"},
    ),
}

TREATS = {
    "bread": Treat(
        id="bread",
        label="bread loaf",
        phrase="a warm bread loaf",
        tags={"food", "bread"},
    ),
    "pie": Treat(
        id="pie",
        label="berry pie",
        phrase="a berry pie with a shiny crust",
        tags={"food", "pie"},
    ),
    "corncake": Treat(
        id="corncake",
        label="corn cake",
        phrase="a sweet corn cake",
        tags={"food", "cake"},
    ),
}

MORALS = {
    "share": MoralChoice(
        id="share",
        offer="share the picnic food with a friend",
        lesson="kindness grows bigger when it is shared",
        action="shared the food",
        ending="the table felt twice as merry",
        tags={"moral", "share"},
    ),
    "wait": MoralChoice(
        id="wait",
        offer="wait for the grown-up to finish setting the picnic cloth",
        lesson="patience keeps trouble from spilling over",
        action="waited patiently",
        ending="the day stayed neat and cheerful",
        tags={"moral", "wait"},
    ),
    "help": MoralChoice(
        id="help",
        offer="help carry the basket instead of snatching it",
        lesson="helping hands make room for everyone",
        action="helped with the basket",
        ending="the basket came along safely",
        tags={"moral", "help"},
    ),
}

GIRL_NAMES = ["Mabel", "Nora", "Lila", "June", "Penny"]
BOY_NAMES = ["Bram", "Otis", "Theo", "Cal", "Jeb"]
TRAITS = ["bold", "cheerful", "curious", "lively", "stubborn"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    need: str
    treat: str
    choice: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "romp" not in setting.affords:
            continue
        for need_id in NEEDS:
            for treat_id in TREATS:
                for choice_id in MORALS:
                    if need_id == "hungry" and treat_id in {"bread", "pie", "corncake"}:
                        combos.append((place, need_id, treat_id, choice_id))
    return combos


def explain_rejection() -> str:
    return "(No story: this tall tale needs a hungry romp with a clear moral and a happy ending.)"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"energy": 2.0, "hunger": 2.0},
        memes={"joy": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"patience": 1.0},
        memes={"care": 2.0},
    ))
    treat = world.add(Entity(
        id=params.treat,
        type="food",
        label=TREATS[params.treat].label,
        phrase=TREATS[params.treat].phrase,
        owner=parent.id,
    ))
    world.facts.update(hero=hero, parent=parent, treat=treat, need=NEEDS[params.need], moral=MORALS[params.choice])
    return world


def narrate_opening(world: World) -> None:
    hero: Entity = world.facts["hero"]
    need: Need = world.facts["need"]
    treat: Entity = world.facts["treat"]
    moral: MoralChoice = world.facts["moral"]

    world.say(
        f"Long ago, in {world.setting.place}, there lived a {hero.pronoun('subject')} tall enough for a fence but young enough to believe every crow was a cousin."
    )
    world.say(
        f"{hero.id} was {world.facts['hero'].pronoun('subject').capitalize()}? No, {hero.id} was a {world.facts['hero'].type} who felt {need.hunger_word} whenever {need.delightful.lower()} drifted by."
    )
    world.say(
        f"That day a picnic basket held {treat.phrase}, and the bright thought of it made {hero.id}'s tummy thump like a drum."
    )
    world.say(
        f"{hero.id} wanted to {need.urge}, but the grown-up had a gentler plan: {moral.offer}."
    )


def narrate_middles(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    need: Need = world.facts["need"]
    moral: MoralChoice = world.facts["moral"]
    treat: Entity = world.facts["treat"]

    hero.meters["hunger"] += 1.0
    hero.memes["impatience"] = hero.memes.get("impatience", 0.0) + 1.0

    world.para()
    world.say(
        f"The day was muggy, the grass was soft, and the air sat on the lane like a wool blanket."
    )
    world.say(
        f"{hero.id} tried to romp anyway, but a hungry belly can make even a merry skip wobble."
    )

    if world.setting.muggy:
        hero.meters["sweat"] = hero.meters.get("sweat", 0.0) + 1.0
        world.say(
            f"With the muggy air clinging close, {hero.id} slowed down and listened to {parent.pronoun('possessive')} voice."
        )

    world.say(
        f'"{moral.lesson}," said {parent.pronoun("possessive")} {parent.label if parent.label else "parent"}, and {hero.id} could see the sense in it.'
    )

    if world.facts["need"].id == "hungry":
        hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
        world.say(
            f"So instead of snatching {treat.label}, {hero.id} chose to {moral.action}."
        )
        hero.meters["hunger"] -= 1.0
        parent.memes["pride"] = parent.memes.get("pride", 0.0) + 1.0
        world.say(
            f"{parent.pronoun('subject').capitalize()} smiled, because sharing made the food taste better before the first bite."
        )
    else:
        world.say(f"But the lesson still held: {moral.lesson}.")


def narrate_ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    treat: Entity = world.facts["treat"]
    moral: MoralChoice = world.facts["moral"]

    world.para()
    hero.meters["hunger"] = max(0.0, hero.meters["hunger"] - 2.0)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2.0
    parent.memes["joy"] = parent.memes.get("joy", 0.0) + 1.0

    world.say(
        f"At last {hero.id} ate the {treat.label}, and the muggy air felt less heavy, as if the clouds had stepped aside to watch."
    )
    world.say(
        f"{moral.ending.capitalize()}, and {hero.id} finished the day with a full belly, a bright grin, and a story to brag about for a week."
    )
    world.say(
        f"That is how {hero.id} learned that a hungry heart can still choose a kind path, and the path will often lead to a happier supper."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    narrate_opening(world)
    narrate_middles(world)
    narrate_ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    need: Need = world.facts["need"]
    moral: MoralChoice = world.facts["moral"]
    return [
        f"Write a tall tale for children about {hero.id}, who is {need.hunger_word} and wants to romp on a muggy day.",
        f"Tell a short story where a young hero learns that {moral.lesson.lower()} while waiting for a picnic treat.",
        f"Create a happy ending about a {hero.type} in {world.setting.place} who stays kind instead of grabbing food.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    treat: Entity = world.facts["treat"]
    need: Need = world.facts["need"]
    moral: MoralChoice = world.facts["moral"]

    return [
        QAItem(
            question=f"Why did {hero.id} want to romp so badly?",
            answer=f"{hero.id} was {need.hunger_word}, and the smell of {treat.phrase} made {hero.id} want to romp toward the picnic basket right away.",
        ),
        QAItem(
            question=f"What did the grown-up want {hero.id} to do instead of grabbing the food?",
            answer=f"The grown-up wanted {hero.id} to {moral.offer.lower()}. That was the kinder and safer choice on the muggy day.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} had a full belly, a happier mood, and a better lesson about kindness and patience.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "hungry": [
        QAItem(
            question="What does hungry mean?",
            answer="Hungry means your body wants food because it needs energy.",
        )
    ],
    "muggy": [
        QAItem(
            question="What is muggy weather?",
            answer="Muggy weather feels warm and damp, like the air is sticky and heavy.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral lesson?",
            answer="A moral lesson is a kind rule the story teaches, like sharing, patience, or helping others.",
        )
    ],
    "happy ending": [
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets better and the story closes with a good feeling.",
        )
    ],
    "romp": [
        QAItem(
            question="What is a romp?",
            answer="A romp is a playful run or skip done with lots of energy and fun.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["hungry"])
    out.extend(WORLD_KNOWLEDGE["muggy"])
    out.extend(WORLD_KNOWLEDGE["moral"])
    out.extend(WORLD_KNOWLEDGE["happy ending"])
    out.extend(WORLD_KNOWLEDGE["romp"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A simple declarative twin for the reasonableness gate.
need(hungry).
need_ok(hungry).

setting(meadow).
setting(orchard).
setting(lane).

affords(meadow, romp).
affords(orchard, romp).
affords(lane, romp).

treat(bread).
treat(pie).
treat(corncake).

moral(share).
moral(wait).
moral(help).

valid(Place, Need, Treat, Moral) :-
    setting(Place), affords(Place, romp),
    need(Need), need_ok(Need),
    treat(Treat), moral(Moral).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.muggy:
            lines.append(asp.fact("muggy", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: romp, muggy, hungry, moral value, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--choice", choices=MORALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.need and args.need != "hungry":
        raise StoryError("This storyworld is built around a hungry hero.")
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.need is None or c[1] == args.need)
        and (args.treat is None or c[2] == args.treat)
        and (args.choice is None or c[3] == args.choice)
    ]
    if not combos:
        raise StoryError(explain_rejection())
    place, need, treat, choice = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, need=need, treat=treat, choice=choice, name=name, gender=gender, parent=parent, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="meadow", need="hungry", treat="bread", choice="share", name="Mabel", gender="girl", parent="mother", trait="cheerful"),
            StoryParams(place="orchard", need="hungry", treat="pie", choice="wait", name="Bram", gender="boy", parent="father", trait="bold"),
            StoryParams(place="lane", need="hungry", treat="corncake", choice="help", name="Nora", gender="girl", parent="mother", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
