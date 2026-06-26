#!/usr/bin/env python3
"""
A standalone story world: stag, spirit, magic, myth.

The world is a small mythic grove where a child or hunter follows a stag,
meets a spirit, and must use a piece of magic wisely. The tension is that a
powerful wish can either bless the grove or disturb it; the turn is learning
the old rule of giving before taking; the ending proves the grove changed.
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


@dataclass
class Place:
    name: str
    ancient: bool = False
    has_spring: bool = True
    has_oak: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    verb: str
    gift: str
    cost: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Stag:
    label: str
    antlers: str
    age: str = "old"
    tags: set[str] = field(default_factory=lambda: {"stag", "wild"})


@dataclass
class Spirit:
    label: str
    domain: str
    mood: str = "watchful"
    tags: set[str] = field(default_factory=lambda: {"spirit", "myth"})


@dataclass
class StoryParams:
    place: str
    power: str
    name: str
    gender: str
    guide: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = {
    "grove": Place("the old grove", ancient=True, has_spring=True, has_oak=True, affords={"seek", "offer", "bless"}),
    "spring": Place("the moon-spring", ancient=True, has_spring=True, has_oak=False, affords={"seek", "offer", "bless"}),
    "hill": Place("the hollow hill", ancient=True, has_spring=False, has_oak=True, affords={"seek", "offer", "bless"}),
}

POWERS = {
    "light": Power(
        id="light",
        label="lantern-light magic",
        verb="light the path",
        gift="a warm path through the dark",
        cost="it can reveal what was hidden",
        kind="light",
        tags={"magic", "light"},
    ),
    "healing": Power(
        id="healing",
        label="healing magic",
        verb="heal the wound",
        gift="a gentle closing of the hurt",
        cost="it asks for patience and care",
        kind="healing",
        tags={"magic", "healing"},
    ),
    "rain": Power(
        id="rain",
        label="rain-calling magic",
        verb="call rain",
        gift="soft water for roots and leaves",
        cost="it can make the trail slippery",
        kind="rain",
        tags={"magic", "rain"},
    ),
}

NAMES = {
    "girl": ["Mira", "Asha", "Lina", "Sera", "Nina"],
    "boy": ["Taro", "Eli", "Jon", "Noel", "Ravi"],
}

GENDERS = ["girl", "boy"]
GUIDES = ["elder", "mother", "father", "grandmother"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, power) for place in PLACES for power in POWERS]


def explain_invalid(place: str, power: str) -> str:
    return f"(No story: the old mythic grove must allow both the quest and the magic, but {place} and {power} do not fit.)"


ASP_RULES = r"""
place(P) :- setting(P).
power(X) :- spell(X).
valid(P,X) :- place(P), power(X).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for x in POWERS:
        lines.append(asp.fact("spell", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic story world with a stag, a spirit, and a piece of magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDES)
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
    combos = valid_combos()
    if args.place and args.power and (args.place, args.power) not in combos:
        raise StoryError(explain_invalid(args.place, args.power))
    place = args.place or rng.choice(sorted(PLACES))
    power = args.power or rng.choice(sorted(POWERS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(place=place, power=power, name=name, gender=gender, guide=guide)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    power = POWERS[params.power]
    w = World(place)
    hero = w.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    guide = w.add(Entity(id="guide", kind="character", type=params.guide, label=f"the {params.guide}"))
    stag = w.add(Entity(id="stag", kind="character", type="stag", label="the stag", phrase="an ash-gray stag"))
    spirit = w.add(Entity(id="spirit", kind="character", type="spirit", label="the spirit", phrase="a pale spirit of the grove"))
    charm = w.add(Entity(id="charm", type="thing", label=power.label, phrase=power.label, owner=hero.id))
    w.facts.update(hero=hero, guide=guide, stag=stag, spirit=spirit, charm=charm, power=power, params=params)
    return w


def tell_story(w: World) -> None:
    f = w.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    stag: Entity = f["stag"]
    spirit: Entity = f["spirit"]
    power: Power = f["power"]
    place: Place = w.place

    w.say(f"In {place.name}, {hero.pronoun('possessive')} {guide.label} told {hero.pronoun('object')} an old tale about a stag who never ran from kindness.")
    w.say(f"They found {stag.label} at the edge of the trees, and beside him stood {spirit.label}, quiet as mist.")
    w.say(f"{hero.label} carried {power.label}, a little magic that could {power.verb}, but the old stories said magic should be used with a pure heart.")
    w.say(f"{hero.label} wanted to help the grove, yet the spirit said, “First, listen. A blessing taken too quickly becomes a thorn.”")

    w.say(f"So {hero.label} knelt and offered water at the roots of the oak, and {guide.label} smiled as the spirit grew brighter.")
    if power.kind == "light":
        w.say(f"Then {hero.label} used the lantern-light to {power.verb}, and the path showed where the deer had been trampled by careless boots.")
    elif power.kind == "healing":
        w.say(f"Then {hero.label} used the healing charm to {power.verb}, and the torn bark on the oak closed like a sleeping eye.")
    else:
        w.say(f"Then {hero.label} used the rain-calling charm to {power.verb}, and the thirsty leaves drank the silver drops at once.")
    w.say(f"The stag lowered his head, touched the charm with his antlers, and the spirit breathed, “Now the gift is shared, not stolen.”")
    w.say(f"When {hero.label} went home, the grove was changed: the air felt gentler, the stag watched in peace, and {power.gift} seemed to linger between the trees.")


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    power: Power = f["power"]
    return [
        QAItem(
            question=f"Who went into {w.place.name} with the {guide.label}?",
            answer=f"{hero.label} went into {w.place.name} with {guide.label}.",
        ),
        QAItem(
            question=f"What kind of magic did {hero.label} carry?",
            answer=f"{hero.label} carried {power.label}.",
        ),
        QAItem(
            question=f"Who did {hero.label} meet in the grove?",
            answer=f"{hero.label} met the stag and the spirit.",
        ),
        QAItem(
            question=f"Why did the spirit wait before giving a blessing?",
            answer="The spirit wanted the child to listen first and offer something back, so the magic would be shared wisely.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The grove became gentler, the stag was calm, and the magic stayed as a blessing instead of a taking.",
        ),
    ]


WORLD_QA = [
    QAItem(question="What is a stag?", answer="A stag is a male deer with antlers."),
    QAItem(question="What is a spirit in a myth?", answer="A spirit is a mysterious being in a story, often tied to a place, a season, or a feeling."),
    QAItem(question="What is magic in a mythic story?", answer="Magic is a special power that can change the world in ways ordinary actions cannot."),
]


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    hero: Entity = f["hero"]
    power: Power = f["power"]
    return [
        f'Write a short myth about {hero.label}, a stag, and a spirit in {w.place.name}, using the word "{power.kind}".',
        f"Tell a child-friendly legend where {hero.label} uses {power.label} to help a stag and earn the trust of a spirit.",
        f"Write a gentle myth with an old grove, a speaking spirit, and a stag that ends with a blessing from magic.",
    ]


def dump_trace(w: World) -> str:
    out = ["--- world model state ---"]
    for e in w.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id}: " + ", ".join(bits))
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    w = build_world(params)
    tell_story(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=WORLD_QA,
        world=w,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="grove", power="light", name="Mira", gender="girl", guide="elder"),
    StoryParams(place="spring", power="healing", name="Taro", gender="boy", guide="mother"),
    StoryParams(place="hill", power="rain", name="Asha", gender="girl", guide="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, x in combos:
            print(f"  {p:8} {x}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.power} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
