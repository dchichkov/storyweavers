#!/usr/bin/env python3
"""
storyworlds/worlds/counter_twist_kindness_adventure.py
======================================================

A small adventure storyworld about a counter, a twist, and a kind rescue.

Premise:
- A child explorer wants something from a counter.
- A twist makes the first plan fail.
- Kindness turns the problem into a better adventure.

This world keeps the setting small and the state causal: the counter is a
physical place with objects on and behind it, and the characters have emotional
states that change when the plan changes.
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
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoors: bool = True
    holds: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    title: str
    cause: str
    effect: str
    obstacle: str
    clue: str


@dataclass
class Kindness:
    id: str
    title: str
    action: str
    result: str
    gift: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    prize: str
    twist: str
    kindness: str
    seed: Optional[int] = None


PLACES = {
    "harbor": Place(name="the harbor counter", indoors=False, holds={"map", "shell", "lantern"}),
    "shop": Place(name="the old shop counter", indoors=True, holds={"map", "key", "lantern"}),
    "station": Place(name="the station counter", indoors=True, holds={"ticket", "map", "lantern"}),
}

TWISTS = {
    "hidden_map": Twist(
        id="hidden_map",
        title="the hidden map twist",
        cause="a gust of wind",
        effect="the map slid behind the counter",
        obstacle="the explorer could not reach it alone",
        clue="a small corner of paper was still showing",
    ),
    "mixed_up_key": Twist(
        id="mixed_up_key",
        title="the mixed-up key twist",
        cause="a clatter of buckets",
        effect="the key fell into the wrong tray",
        obstacle="the tray was too high for little hands",
        clue="the key tag was still tied to a string",
    ),
    "shy_ticket": Twist(
        id="shy_ticket",
        title="the shy ticket twist",
        cause="a bump from the line",
        effect="the ticket slipped under the counter",
        obstacle="the explorer could not see where it went",
        clue="one bright corner peeked out near the leg of the counter",
    ),
}

KINDNESSES = {
    "lift_stool": Kindness(
        id="lift_stool",
        title="the stool kindness",
        action="pulled over a little stool and lifted the explorer up",
        result="the explorer could reach the lost thing safely",
        gift="a sturdy little stool",
        tail="Together they set the stool back after the search",
    ),
    "ask_clerk": Kindness(
        id="ask_clerk",
        title="the asking kindness",
        action="called the clerk and asked for help with a gentle voice",
        result="the clerk smiled and opened the right drawer",
        gift="a calm, careful answer",
        tail="The kind words made the room feel less worried",
    ),
    "share_light": Kindness(
        id="share_light",
        title="the lantern kindness",
        action="held up a lantern so both could look underneath",
        result="the hidden corner shone bright and easy to spot",
        gift="a warm glow of light",
        tail="The glow helped everyone see the small clue",
    ),
}

PRIZES = {
    "map": Entity(id="map", type="thing", label="map", phrase="a folded paper map", location="counter"),
    "key": Entity(id="key", type="thing", label="key", phrase="a brass key on a string", location="counter"),
    "ticket": Entity(id="ticket", type="thing", label="ticket", phrase="a thin blue ticket", location="counter"),
}

HERO_NAMES = ["Nia", "Toby", "Mira", "Arlo", "Lina", "Finn", "Rosa", "Jules"]
HELPER_NAMES = ["Bram", "Etta", "Suri", "Hale", "Mona", "Pip", "Dara", "Oren"]
TRAITS = ["curious", "brave", "gentle", "spirited", "quick", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a counter, a twist, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    twist = args.twist or rng.choice(list(TWISTS))
    kindness = args.kindness or rng.choice(list(KINDNESSES))
    prize = args.prize or rng.choice(list(PRIZES))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_type = "boy" if hero_type == "girl" and rng.random() < 0.5 else "girl"
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    if args.gender and args.prize and args.prize == "ticket" and args.gender == "boy" and args.parent == "mother":
        pass
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        prize=prize,
        twist=twist,
        kindness=kindness,
    )


def _set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def _set_meme(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    twist = TWISTS[params.twist]
    kindness = KINDNESSES[params.kindness]
    prize = PRIZES[params.prize]

    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    prize_ent = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=helper.id,
        location="counter",
    ))
    counter = world.add(Entity(
        id="counter",
        kind="thing",
        type="counter",
        label="counter",
        phrase=f"the {place.name}",
        location=place.name,
    ))

    _set_meme(hero, "curiosity", 1)
    _set_meme(hero, "hope", 1)
    _set_meme(helper, "care", 1)

    world.say(f"{hero.label} was a little {params.hero_type} with a curious heart who loved adventure.")
    world.say(f"At {place.name}, {hero.label} found {prize_ent.phrase} waiting by the counter.")
    world.say(f"{hero.label} wanted to take {prize_ent.it()} on a small journey.")

    world.para()
    world.say(f"Then came {twist.title}. {twist.cause} meant that {twist.effect}.")
    _set_meme(hero, "worry", 1)
    _set_meter(prize_ent, "stuck", 1)
    counter.meters["busy"] = 1

    if twist.id == "hidden_map":
        world.say(f"That left the explorer peeking at {twist.clue}.")
    elif twist.id == "mixed_up_key":
        world.say(f"Even so, {twist.clue} showed the key was close by.")
    else:
        world.say(f"Still, {twist.clue} gave a tiny hint under the counter.")

    world.para()
    world.say(f"That was when {params.helper_name} showed kindness.")
    world.say(f"{params.helper_name} {kindness.action}.")
    _set_meme(helper, "kindness", 1)
    _set_meme(hero, "relief", 1)
    _set_meter(prize_ent, "found", 1)

    if kindness.id == "lift_stool":
        world.say(f"With {kindness.gift}, {hero.label} could reach the prize without climbing.")
    elif kindness.id == "ask_clerk":
        world.say(f"{kindness.result}.")
    else:
        world.say(f"{kindness.result}.")

    world.say(f"{kindness.tail}.")
    world.say(f"In the end, {hero.label} held {prize_ent.it()} carefully and smiled at the counter, which had helped turn a twist into a kinder adventure.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize_ent,
        counter=counter,
        twist=twist,
        kindness=kindness,
        place=place,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a young child about {f['hero'].label}, a counter, and a surprising twist.",
        f"Tell a gentle story where {f['hero'].label} wants the prize at the counter, then kindness helps solve the problem.",
        "Write a simple, child-friendly adventure with a counter, a twist, and a kind helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    twist: Twist = f["twist"]  # type: ignore[assignment]
    kindness: Kindness = f["kindness"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"It was mostly about {hero.label}, a little {hero.type} who wanted the prize from {place.name}.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the counter?",
            answer=f"{twist.effect.capitalize()}, so the prize got stuck until {helper.label} helped.",
        ),
        QAItem(
            question=f"How did {helper.label} show kindness?",
            answer=f"{helper.label} showed kindness by {kindness.action}, which let {hero.label} get the prize safely.",
        ),
        QAItem(
            question="How did the adventure end?",
            answer=f"It ended with {hero.label} holding the {prize.label} carefully and smiling at the counter after the twist was solved kindly.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "counter": QAItem(
        question="What is a counter?",
        answer="A counter is a flat surface or ledge where people put things down, pay for things, or wait for help.",
    ),
    "twist": QAItem(
        question="What is a twist in a story?",
        answer="A twist is a surprising change that makes the story take a new turn.",
    ),
    "kindness": QAItem(
        question="What does kindness mean?",
        answer="Kindness means being helpful, gentle, and caring toward someone else.",
    ),
    "adventure": QAItem(
        question="What is an adventure?",
        answer="An adventure is an exciting trip or experience where something interesting and new happens.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    return [
        WORLD_KNOWLEDGE["counter"],
        WORLD_KNOWLEDGE["twist"],
        WORLD_KNOWLEDGE["kindness"],
        WORLD_KNOWLEDGE["adventure"],
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
        parts = [f"type={e.type}"]
        if e.label:
            parts.append(f"label={e.label}")
        if e.location:
            parts.append(f"location={e.location}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append("  " + e.id + " " + " ".join(parts))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", hero_name="Nia", hero_type="girl", helper_name="Bram", helper_type="boy", prize="map", twist="hidden_map", kindness="lift_stool"),
    StoryParams(place="shop", hero_name="Toby", hero_type="boy", helper_name="Etta", helper_type="girl", prize="key", twist="mixed_up_key", kindness="ask_clerk"),
    StoryParams(place="station", hero_name="Mira", hero_type="girl", helper_name="Hale", helper_type="boy", prize="ticket", twist="shy_ticket", kindness="share_light"),
]


ASP_RULES = r"""
% A prize is at the counter when it starts there.
at_counter(P) :- prize(P), start_location(P, counter).

% A twist causes the prize to become hidden or hard to reach.
twisted(P, T) :- prize(P), twist(T), twist_applies(T, P).

% Kindness resolves a twist if it provides a helpful action.
resolved(P, K) :- twisted(P, T), kindness(K), kindness_fits(K, T).

#show at_counter/1.
#show twisted/2.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("start_location", pid, "counter"))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness", kid))
    for tid, tw in TWISTS.items():
        for pid in PRIZES:
            if pid in {"map", "key", "ticket"}:
                lines.append(asp.fact("twist_applies", tid, pid))
    for kid, kn in KINDNESSES.items():
        for tid in TWISTS:
            if (kid == "lift_stool" and tid in {"hidden_map", "shy_ticket"}) or \
               (kid == "ask_clerk" and tid == "mixed_up_key") or \
               (kid == "share_light" and tid in {"hidden_map", "shy_ticket"}):
                lines.append(asp.fact("kindness_fits", kid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show resolved/2."))
    resolved = sorted(set(asp.atoms(model, "resolved")))
    if resolved:
        print("OK: ASP rules produced resolved pairs:", resolved)
        return 0
    print("ASP verification failed: no resolved pairs found.")
    return 1


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/2.\n#show twisted/2.\n#show at_counter/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prize and args.twist:
        if args.prize == "key" and args.twist == "hidden_map":
            pass
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            params = resolve_combo(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.twist} / {p.kindness} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
