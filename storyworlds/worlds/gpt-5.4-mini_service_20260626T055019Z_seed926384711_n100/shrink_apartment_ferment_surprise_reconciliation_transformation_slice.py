#!/usr/bin/env python3
"""
Storyworld: shrink, apartment, ferment.

A small slice-of-life storyworld about a child in an apartment where a quiet
day turns surprising when something small shrinks, something in the kitchen
ferments, and the people in the apartment find a kind, practical way through it.

The simulated world tracks physical meters and emotional memes. The story is
not a frozen template: the apartment, the surprise, the tension, and the
reconciliation all arise from the world state.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Apartment:
    name: str = "the apartment"
    has_balcony: bool = True
    rooms: tuple[str, ...] = ("kitchen", "living room", "hallway")


@dataclass
class SurpriseItem:
    label: str
    phrase: str
    kind: str
    risk: str
    transform: str


@dataclass
class StoryParams:
    apartment: str
    surprise: str
    transform: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, apartment: Apartment):
        self.apartment = apartment
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

        w = World(self.apartment)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _storyline_hint(item: SurpriseItem) -> str:
    return {
        "jar": "the kitchen smelled warm and a little sweet",
        "sweater": "the laundry basket had a sad, tiny feel to it",
        "plant": "the windowsill looked bright and patient",
        "dough": "the counter held a bowl that was quietly waking up",
    }.get(item.kind, "the apartment felt calm and ordinary")


ITEMS = {
    "jar": SurpriseItem(
        label="jar",
        phrase="a jar of bubbling kimchi",
        kind="jar",
        risk="spilled and sour",
        transform="ferment into something bigger and livelier",
    ),
    "sweater": SurpriseItem(
        label="sweater",
        phrase="a favorite wool sweater",
        kind="sweater",
        risk="shrunken",
        transform="shrink in the wash",
    ),
    "plant": SurpriseItem(
        label="plant",
        phrase="a little basil plant",
        kind="plant",
        risk="bent and thirsty",
        transform="grow from a tiny sprig",
    ),
    "dough": SurpriseItem(
        label="dough",
        phrase="a bowl of bread dough",
        kind="dough",
        risk="overflowed",
        transform="ferment into soft bread",
    ),
}

APARTMENTS = {
    "cozy": Apartment(name="the apartment", has_balcony=True),
    "sunny": Apartment(name="the apartment", has_balcony=False),
    "quiet": Apartment(name="the apartment", has_balcony=True),
}


def _pronoun_pair(gender: str) -> tuple[str, str]:
    if gender == "girl":
        return "she", "her"
    return "he", "him"


def _action_verb(item: SurpriseItem) -> str:
    return {
        "jar": "check on the jar",
        "sweater": "do the laundry",
        "plant": "water the plant",
        "dough": "knead the dough",
    }[item.kind]


def _resolution_gear(item: SurpriseItem) -> str:
    return {
        "jar": "a clean lid and a bigger bowl",
        "sweater": "warm water and a little patience",
        "plant": "fresh soil and a sunny spot",
        "dough": "a towel over the bowl and more time",
    }[item.kind]


def _surprise_turn(item: SurpriseItem) -> str:
    return {
        "jar": "the lid popped softly and everyone blinked at the smell",
        "sweater": "the sweater came out of the wash much smaller than before",
        "plant": "a tiny new leaf was hiding near the stem",
        "dough": "the dough had puffed up and reached the edge of the bowl",
    }[item.kind]


def tell(apartment: Apartment, item: SurpriseItem, hero_name: str, gender: str, parent_type: str) -> World:
    world = World(apartment)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    obj = world.add(Entity(
        id="item",
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    sub, objp = _pronoun_pair(gender)
    world.say(f"{hero_name} lived in {apartment.name} with {parent.label}.")
    world.say(f"{sub.capitalize()} liked the quiet little routines that made the rooms feel safe.")
    world.say(f"On that day, there was {item.phrase} on the counter, and it looked ready to {item.transform}.")
    world.say(_storyline_hint(item))

    world.para()
    world.say(f"In the kitchen, {hero_name} wanted to {_action_verb(item)}.")
    if item.kind == "sweater":
        world.say(f"But the laundry had already been warm, and the sweater had begun to {item.risk}.")
        hero.memes["surprise"] = 1.0
        hero.memes["worry"] = 1.0
        parent.memes["surprise"] = 1.0
        parent.memes["worry"] = 1.0
    elif item.kind == "jar":
        world.say(f"The jar was fermenting, and bubbles kept nudging the lid from below.")
        hero.memes["surprise"] = 1.0
        hero.memes["curiosity"] = 1.0
        parent.memes["concern"] = 1.0
    elif item.kind == "plant":
        world.say(f"The little plant was growing slowly, but it had looked droopy in the morning.")
        hero.memes["hope"] = 1.0
        parent.memes["concern"] = 1.0
    else:
        world.say(f"The dough was fermenting, and the bowl had a round, living look.")
        hero.memes["curiosity"] = 1.0
        parent.memes["alert"] = 1.0

    world.say(f"Then came a surprise: {_surprise_turn(item)}.")
    world.facts["item"] = obj
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["item_cfg"] = item

    world.para()
    if item.kind == "sweater":
        world.say(f"{parent.label.capitalize()} held up the tiny sweater and sighed.")
        world.say(f"\"It shrank,\" {parent.pronoun('subject')} said gently. \"But we can still make this okay.\"")
        hero.memes["sad"] = 1.0
        parent.memes["sad"] = 1.0
        parent.memes["reassure"] = 1.0
    elif item.kind == "jar":
        world.say(f"{parent.label.capitalize()} laughed first, then covered the jar before it bubbled over.")
        world.say(f"\"The ferment is doing its job,\" {parent.pronoun('subject')} said. \"We just need a bigger bowl.\"")
        hero.memes["surprise"] = 2.0
        parent.memes["reassure"] = 1.0
    elif item.kind == "plant":
        world.say(f"{parent.label.capitalize()} smiled at the little leaf.")
        world.say(f"\"It needed better care,\" {parent.pronoun('subject')} said. \"Let's give it a brighter spot.\"")
        hero.memes["hope"] = 2.0
        parent.memes["reassure"] = 1.0
    else:
        world.say(f"{parent.label.capitalize()} peeked under the towel and smiled at the puffy dough.")
        world.say(f"\"It is fermenting nicely,\" {parent.pronoun('subject')} said. \"We just need to wait.\"")
        hero.memes["calm"] = 1.0
        parent.memes["calm"] = 1.0

    world.say(f"So they chose {_resolution_gear(item)}.")
    if item.kind == "sweater":
        world.say(f"{hero_name} folded the shrunken sweater into a soft doll-size bundle, and {parent.label} found a way to wash the next one more carefully.")
        world.say(f"The surprise turned into a quiet lesson about heat, water, and paying attention.")
        hero.memes["reconciliation"] = 1.0
        parent.memes["reconciliation"] = 1.0
        hero.memes["transformation"] = 1.0
    elif item.kind == "jar":
        world.say(f"They moved the jar to a larger bowl, wiped the counter, and watched the ferment settle into steady bubbles.")
        world.say(f"By dinner, the apartment smelled warm instead of worried.")
        hero.memes["reconciliation"] = 1.0
        parent.memes["reconciliation"] = 1.0
        hero.memes["transformation"] = 1.0
    elif item.kind == "plant":
        world.say(f"They repotted the plant together and set it where the light was kind.")
        world.say(f"By the end of the afternoon, the little green sprig looked like it belonged there.")
        hero.memes["reconciliation"] = 1.0
        parent.memes["reconciliation"] = 1.0
        hero.memes["transformation"] = 1.0
    else:
        world.say(f"They left the dough covered and came back later to find it puffed into something ready to bake.")
        world.say(f"The apartment filled with a cozy smell, and the waiting felt worth it.")
        hero.memes["reconciliation"] = 1.0
        parent.memes["reconciliation"] = 1.0
        hero.memes["transformation"] = 1.0

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    item = world.facts["item_cfg"]
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        f'Write a slice-of-life story for a child in an apartment where something can {item.label} and something can {item.transform}.',
        f"Tell a gentle story about {hero.id} and {parent.label} in {world.apartment.name} with {item.phrase}.",
        f'Write a calm, child-facing story that includes the words "shrink", "apartment", and "ferment".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    item = world.facts["item_cfg"]
    name = hero.id
    p = parent.label
    qa = [
        QAItem(
            question=f"Where did {name} live with {p}?",
            answer=f"{name} lived in {world.apartment.name} with {p}.",
        ),
        QAItem(
            question=f"What surprise happened with {item.phrase}?",
            answer=f"The surprise was that {item.phrase} changed in a way that made the day feel different and important.",
        ),
        QAItem(
            question=f"How did {name} and {p} solve the problem?",
            answer=f"They solved it by staying calm, talking kindly, and using {_resolution_gear(item)}.",
        ),
    ]
    if item.kind == "sweater":
        qa.append(QAItem(
            question=f"What happened to the sweater?",
            answer="It shrank in the wash, so they handled it gently and learned to be more careful next time.",
        ))
    elif item.kind == "jar":
        qa.append(QAItem(
            question=f"Why did the jar need attention?",
            answer="It was fermenting and bubbling, so they moved it before it spilled over.",
        ))
    elif item.kind == "plant":
        qa.append(QAItem(
            question=f"What changed about the plant?",
            answer="A tiny new leaf appeared, which turned the worry into a happy surprise.",
        ))
    else:
        qa.append(QAItem(
            question=f"What did the dough do?",
            answer="The dough fermented and puffed up, so they let it keep rising until it was ready.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item_cfg"]
    qa = []
    if item.kind == "jar":
        qa.append(QAItem(
            question="What does ferment mean?",
            answer="Ferment means to slowly change, often with bubbles or a new smell, like when food gets made in a jar or bowl over time.",
        ))
    if item.kind == "sweater":
        qa.append(QAItem(
            question="Why can a sweater shrink?",
            answer="A sweater can shrink if it gets washed or dried with too much heat.",
        ))
    if item.kind == "plant":
        qa.append(QAItem(
            question="What does a plant need to grow?",
            answer="Most plants need light, water, air, and time to grow.",
        ))
    if item.kind == "dough":
        qa.append(QAItem(
            question="Why does dough rise?",
            answer="Dough rises because tiny living things or gas bubbles make it grow bigger and softer.",
        ))
    qa.append(QAItem(
        question="What is an apartment?",
        answer="An apartment is a home in a bigger building, often with rooms like a kitchen and a living room.",
    ))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(apartment="cozy", surprise="jar", transform="ferment", name="Mina", gender="girl", parent="mother"),
    StoryParams(apartment="quiet", surprise="sweater", transform="shrink", name="Eli", gender="boy", parent="father"),
    StoryParams(apartment="sunny", surprise="dough", transform="ferment", name="Noa", gender="girl", parent="mother"),
    StoryParams(apartment="cozy", surprise="plant", transform="grow", name="Owen", gender="boy", parent="father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: shrink, apartment, ferment.")
    ap.add_argument("--apartment", choices=APARTMENTS)
    ap.add_argument("--surprise", choices=ITEMS)
    ap.add_argument("--transform", choices=["shrink", "ferment", "grow"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    apartment = args.apartment or rng.choice(list(APARTMENTS))
    surprise = args.surprise or rng.choice(list(ITEMS))
    transform = args.transform or ITEMS[surprise].transform
    if args.transform and args.transform != ITEMS[surprise].transform and args.transform != "grow":
        raise StoryError("The chosen surprise does not fit that transformation.")
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or ("mother" if gender == "girl" else "father")
    name = args.name or rng.choice(["Mina", "Eli", "Noa", "June", "Theo", "Iris"])
    return StoryParams(apartment=apartment, surprise=surprise, transform=transform, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(APARTMENTS[params.apartment], ITEMS[params.surprise], params.name, params.gender, params.parent)
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


ASP_RULES = r"""
item(item).
apartment(home).
surprise(s).
transform(t).

valid_story(A, I, T) :- apartment(A), item(I), transform(T), fits(I, T).

fits(jar, ferment).
fits(sweater, shrink).
fits(plant, grow).
fits(dough, ferment).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for aid in APARTMENTS:
        lines.append(asp.fact("apartment", aid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("surprise", iid))
        lines.append(asp.fact("kind", iid, item.kind))
        lines.append(asp.fact("transforms", iid, item.transform))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(a, i, t) for a in APARTMENTS for i, item in ITEMS.items() for t in ["shrink", "ferment", "grow"] if t == item.transform or (i == "plant" and t == "grow")}
    clingo_set = set(asp_valid())
    if clingo_set != python_set:
        print("MISMATCH between ASP and Python:")
        print("only in ASP:", sorted(clingo_set - python_set))
        print("only in Python:", sorted(python_set - clingo_set))
        return 1
    print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print("\n".join(map(str, combos)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        if idx:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
