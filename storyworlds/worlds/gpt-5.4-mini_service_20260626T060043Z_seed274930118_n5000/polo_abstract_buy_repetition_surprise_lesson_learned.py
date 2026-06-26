#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/polo_abstract_buy_repetition_surprise_lesson_learned.py
====================================================================================================

A compact superhero storyworld about a young hero, a repeated mistake, a surprising
turn, and a lesson learned.

Seed idea:
---
A kid hero keeps trying to buy an abstract "polo" poster for the team hideout, but
the abstract design is too confusing. After a repeat attempt and a surprising clue,
the hero learns to ask better questions and finds the right item.

World shape:
---
- A hero with a cape and a mission
- A shopkeeper with a special item on display
- An abstract object that is hard to understand at first glance
- Repetition: the hero repeats the same mistaken assumption
- Surprise: a hidden clue changes the plan
- Lesson learned: the hero asks carefully and buys the right thing

The story remains child-facing and concrete, while state changes in the world drive
the narration.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    keyword: str
    abstract: bool = False
    buyable: bool = True


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    obj = world.get("target")
    if hero.memes.get("repetition", 0.0) < THRESHOLD:
        return out
    sig = ("repetition",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    out.append(f"{hero.pronoun().capitalize()} tried the same guess again, but {obj.label} still did not make sense.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clue = world.entities.get("clue")
    if not clue or clue.meters.get("revealed", 0.0) < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    out.append("Then a hidden note slipped out from behind the display and changed everything.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    shop = world.get("shopkeeper")
    obj = world.get("target")
    if hero.memes.get("lesson", 0.0) < THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    out.append(f"{hero.id} listened closely, asked carefully, and found the right thing to buy.")
    out.append(f"{shop.label} smiled because {hero.id} had finally understood {obj.label}.")
    return out


RULES = [Rule("repetition", _r_repetition), Rule("surprise", _r_surprise), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "museum": Place("the museum", indoor=True),
    "shop": Place("the corner shop", indoor=True),
    "studio": Place("the art studio", indoor=True),
}

OBJECTS = {
    "polo": ObjectSpec(
        id="polo",
        label="polo",
        phrase="an abstract polo poster",
        keyword="polo",
        abstract=True,
        buyable=True,
    ),
    "abstract": ObjectSpec(
        id="abstract",
        label="abstract print",
        phrase="an abstract print with swirl lines",
        keyword="abstract",
        abstract=True,
        buyable=True,
    ),
    "buy": ObjectSpec(
        id="buy",
        label="ticket",
        phrase="a ticket to buy supplies",
        keyword="buy",
        abstract=False,
        buyable=True,
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Luna", "Zoe", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Eli", "Theo", "Finn"]
TRAITS = ["brave", "curious", "kind", "quick-thinking", "spirited"]
SIDEKICKS = ["robot bat", "tiny drone", "helper cat", "pocket lantern"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for obj in OBJECTS:
            combos.append((place, obj))
    return combos


def describe_object(obj: ObjectSpec) -> str:
    if obj.id == "polo":
        return "an abstract polo poster"
    if obj.id == "abstract":
        return "an abstract print with swirl lines"
    return "a ticket to buy supplies"


def tell(place: Place, obj: ObjectSpec, hero_name: str, gender: str, sidekick: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=hero_name))
    shop = world.add(Entity(id="shopkeeper", kind="character", type="adult", label="the shopkeeper"))
    target = world.add(Entity(id="target", type=obj.id, label=obj.label, phrase=obj.phrase))
    clue = world.add(Entity(id="clue", type="note", label="a hidden note", phrase="a tiny hidden note"))
    clue.meters["revealed"] = 0.0

    hero.memes["want"] = 1
    hero.memes["repetition"] = 1
    hero.memes["lesson"] = 0

    world.say(
        f"On a bright day, {hero_name} was a {trait} little hero with a shiny cape and a {sidekick} sidekick."
    )
    world.say(
        f"{hero.pronoun().capitalize()} came to {place.name} because {hero.pronoun('possessive')} team hideout needed {describe_object(obj)}."
    )
    world.say(
        f"{hero_name} really wanted to buy it, even though the abstract shape looked puzzling at first."
    )

    world.para()
    world.say(
        f"At the counter, {hero.pronoun('subject')} pointed at the display and asked for the {obj.keyword} thing."
    )
    world.say(
        f"The shopkeeper showed the same shelf again, but the answer stayed unclear, so {hero_name} repeated the guess."
    )
    propagate(world)

    world.para()
    clue.meters["revealed"] = 1.0
    world.say(
        f"Just then, a surprise happened: the hidden note fell into {hero.pronoun('possessive')} hand."
    )
    world.say(
        f"It said the abstract design was not the item itself; it was only a clue to the right shelf."
    )
    hero.memes["lesson"] = 1.0
    propagate(world)

    world.para()
    world.say(
        f"{hero_name} laughed, thanked the shopkeeper, and bought the right thing at last."
    )
    world.say(
        f"That day, {hero_name} learned that when something looks abstract, it helps to ask a careful question instead of guessing twice."
    )

    world.facts.update(
        hero=hero,
        shopkeeper=shop,
        target=target,
        clue=clue,
        place=place,
        obj=obj,
        sidekick=sidekick,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    return [
        f'Write a short superhero story for a child about {hero.label} trying to buy something called "{obj.keyword}".',
        f"Tell a story where a small hero repeats a mistake, gets a surprise clue, and learns a lesson before buying the right thing.",
        f"Write a gentle superhero tale that includes the words polo, abstract, and buy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a little superhero who went to {place.name} to buy {obj.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.label} keep doing before the surprise?",
            answer=f"{hero.label} kept making the same guess again, which showed repetition and made the problem feel stuck.",
        ),
        QAItem(
            question="What changed the story?",
            answer="A hidden note slipped out as a surprise and helped the hero understand what to do next.",
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer=f"{hero.label} learned to ask careful questions and not just guess when something looked abstract.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does abstract mean?",
            answer="Abstract means something is shaped in a way that does not look exactly like a real object, so you may need to look carefully to understand it.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying the same thing again more than once.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly happens and changes what people think or do.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone understands after making a mistake or seeing what works better.",
        ),
    ]


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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shop", object="polo", name="Maya", gender="girl", sidekick="tiny drone", trait="brave"),
    StoryParams(place="museum", object="abstract", name="Leo", gender="boy", sidekick="helper cat", trait="curious"),
    StoryParams(place="studio", object="buy", name="Ivy", gender="girl", sidekick="robot bat", trait="kind"),
]


KNOWLEDGE_ORDER = ["polo", "abstract", "buy"]


ASP_RULES = r"""
% A story is valid when the hero can buy an object in the selected place.
valid(Place, Object) :- place(Place), target(Object).

% Repetition, surprise, and lesson learned must all be available in the world.
has_feature(repetition).
has_feature(surprise).
has_feature(lesson_learned).

% A valid story needs the full feature set.
story_ok(Place, Object) :- valid(Place, Object), has_feature(repetition),
                           has_feature(surprise), has_feature(lesson_learned).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("target", oid))
    lines.append(asp.fact("feature", "repetition"))
    lines.append(asp.fact("feature", "surprise"))
    lines.append(asp.fact("feature", "lesson_learned"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with repetition, surprise, and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, name=name, gender=gender, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], OBJECTS[params.object], params.name, params.gender, params.sidekick, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible place/object combos:")
        for p, o in asp_valid_combos():
            print(f"  {p:8} {o}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
