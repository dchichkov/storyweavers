#!/usr/bin/env python3
"""
A small fable-style storyworld about friendship, misunderstanding, and an
antihistamine that is misunderstood as a snub until the truth is spoken.

Premise:
A fox-like viceroy enjoys morning walks with a friend. When sneezes begin, the
friend brings an antihistamine. The viceroy first thinks the friend is trying to
make them sleepy or send them away, but the real intent is care.

World model:
- Characters have meters for tiredness, allergy, and closeness.
- A misunderstanding raises worry and lowers closeness.
- A clear explanation and accepted medicine restore closeness.
- The ending proves the change with a shared walk and calmer breathing.

The story is intended to feel like a short moral tale: small cast, concrete
actions, a social mistake, then a gentle correction.
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
    kind: str = "character"
    type: str = "creature"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["allergy", "tired", "comfort", "closeness", "worry", "understanding"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the oak lane"
    weather: str = "mild morning"


@dataclass
class Medicine:
    id: str
    label: str
    phrase: str
    effect: str
    caution: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTING_REGISTRY = {
    "oak_lane": Setting(place="the oak lane", weather="soft morning"),
    "river_path": Setting(place="the river path", weather="bright morning"),
    "garden_walk": Setting(place="the garden walk", weather="windy morning"),
}

NAME_REGISTRY = {
    "fox": ["Fenn", "Milo", "Tala", "Wren"],
    "hare": ["Pip", "Luna", "Sage", "Nori"],
    "badger": ["Bram", "Hilda", "Orin", "Mira"],
    "deer": ["Iris", "Beck", "Ena", "Pere"],
}

MEDICINE_REGISTRY = {
    "antihistamine": Medicine(
        id="antihistamine",
        label="antihistamine",
        phrase="a small antihistamine tablet",
        effect="calm_sneezes",
        caution="can make a tired creature feel sleepy",
    )
}

TRAITS = ["kind", "patient", "proud", "gentle", "brave"]


ASP_RULES = r"""
% An antihistamine is a care-act when a friend is sneezing from allergies.
needs_help(H) :- allergy(H), sneeze(H).
kind_move(G, H) :- friendship(G,H), medicine(antihistamine), needs_help(H).
misunderstood(H) :- worry(H), care_offer(_,H), not trust(H).
resolved(H) :- explained(_,H), care_offer(_,H), accept(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, setting.place))
    for mid in MEDICINE_REGISTRY:
        lines.append(asp.fact("medicine", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.friend_name:
        raise StoryError("the viceroy and the friend must be different characters")
    if params.hero_type == params.friend_type and params.hero_name == params.friend_name:
        raise StoryError("the story needs two distinct roles for friendship and misunderstanding")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld about a viceroy, an antihistamine, friendship, and misunderstanding.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["fox", "hare", "badger", "deer"])
    ap.add_argument("--friend-type", choices=["fox", "hare", "badger", "deer"])
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
    place = args.place or rng.choice(sorted(SETTING_REGISTRY))
    hero_type = args.hero_type or rng.choice(sorted(NAME_REGISTRY))
    friend_type = args.friend_type or rng.choice(sorted([k for k in NAME_REGISTRY if k != hero_type]))
    hero_name = args.hero_name or rng.choice(NAME_REGISTRY[hero_type])
    friend_name = args.friend_name or rng.choice(NAME_REGISTRY[friend_type])
    params = StoryParams(place=place, hero_name=hero_name, friend_name=friend_name, hero_type=hero_type, friend_type=friend_type)
    reasonableness_gate(params)
    return params


def mood_intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"On {world.setting.place}, a wise viceroy named {hero.id} liked to walk at a careful pace, "
        f"and {friend.id}, a {friend.type}, liked to keep near."
    )
    hero.memes["closeness"] += 1
    friend.memes["closeness"] += 1


def sneeze_turn(world: World, hero: Entity) -> None:
    hero.meters["allergy"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"Then {hero.id} sniffed, sneezed, and rubbed {hero.pronoun('possessive')} nose. "
        f"The pretty path was making the viceroy feel miserable."
    )


def offer_medicine(world: World, friend: Entity, hero: Entity, med: Medicine) -> None:
    world.facts["medicine"] = med
    world.facts["offered"] = True
    hero.memes["worry"] += 1
    world.say(
        f"{friend.id} brought {hero.id} {med.phrase} and said it could help the sneezes."
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, med: Medicine) -> None:
    hero.memes["understanding"] += 0.0
    hero.memes["worry"] += 1
    hero.memes["closeness"] -= 1
    world.say(
        f"But {hero.id} frowned. {hero.id} thought {friend.id} was trying to make {hero.pronoun('object')} sleepy "
        f"and send {hero.pronoun('object')} home."
    )
    world.say(
        f"The viceroy's heart felt stung, because friendship can wobble when kind help is not understood."
    )


def explain_and_accept(world: World, hero: Entity, friend: Entity, med: Medicine) -> None:
    hero.memes["understanding"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    hero.memes["closeness"] += 2
    world.say(
        f"Then {friend.id} explained that the {med.label} was only there to quiet the sneezing, "
        f"not to push {hero.id} away."
    )
    world.say(
        f"{hero.id} listened, took the {med.label}, and soon breathed easier."
    )
    world.say(
        f"The two friends walked on together under the soft morning, and the viceroy knew care had been hiding inside the gift."
    )


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.hero_name, type=params.hero_type, traits=["viceroy", "wise", "careful"]))
    friend = world.add(Entity(id=params.friend_name, type=params.friend_type, traits=["friend", "gentle"]))
    med = MEDICINE_REGISTRY["antihistamine"]

    hero.memes["closeness"] = 1
    friend.memes["closeness"] = 1

    mood_intro(world, hero, friend)
    world.para()
    sneeze_turn(world, hero)
    offer_medicine(world, friend, hero, med)
    misunderstanding(world, hero, friend, med)
    world.para()
    explain_and_accept(world, hero, friend, med)

    world.facts.update(hero=hero, friend=friend, setting=world.setting, med=med)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    med: Medicine = f["med"]
    return [
        f'Write a short fable about {hero.id}, a viceroy, and {friend.id}, where an "{med.label}" is misunderstood before it helps.',
        f"Tell a gentle story about friendship and misunderstanding in {world.setting.place} that ends with {hero.id} feeling better.",
        f'Write a child-friendly fable that includes the word "{med.label}" and shows how a kind gift can be mistaken at first.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        QAItem(
            question=f"Who was the viceroy in the story?",
            answer=f"The viceroy was {hero.id}, a {hero.type} who liked to walk carefully and listen.",
        ),
        QAItem(
            question=f"Why did {hero.id} first misunderstand {friend.id}'s gift?",
            answer=f"{hero.id} thought the antihistamine meant {friend.id} wanted to make {hero.id} sleepy or send {hero.id} away, when it was really a caring help for the sneezes.",
        ),
        QAItem(
            question=f"What changed after {friend.id} explained the antihistamine?",
            answer=f"{hero.id} understood the gift, took the antihistamine, breathed easier, and the friends walked on together in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an antihistamine?",
            answer="An antihistamine is a medicine that can help with allergy symptoms like sneezing and a runny nose.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm bond between people or creatures who care about each other, help each other, and spend time together.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a kind action means something else, usually before the truth is explained.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING_REGISTRY[params.place])
    generate_story(world, params)
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
    StoryParams(place="oak_lane", hero_name="Fenn", friend_name="Pip", hero_type="fox", friend_type="hare"),
    StoryParams(place="river_path", hero_name="Tala", friend_name="Bram", hero_type="fox", friend_type="badger"),
    StoryParams(place="garden_walk", hero_name="Iris", friend_name="Milo", hero_type="deer", friend_type="fox"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place_name/2."))
    if asp.atoms(model, "place_name"):
        print("OK: ASP twin emits registry facts.")
        return 0
    print("MISMATCH: ASP twin did not emit facts.")
    return 1


def build_asp_listing() -> str:
    import asp
    model = asp.one_model(asp_program("#show place_name/2."))
    atoms = asp.atoms(model, "place_name")
    return "\n".join(f"{a[0]} -> {a[1]}" for a in atoms)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show place_name/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(build_asp_listing())
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
