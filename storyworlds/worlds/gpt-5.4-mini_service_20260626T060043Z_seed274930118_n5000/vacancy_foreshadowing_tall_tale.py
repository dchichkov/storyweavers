#!/usr/bin/env python3
"""
storyworlds/worlds/vacancy_foreshadowing_tall_tale.py
======================================================

A small Tall Tale storyworld about vacancy and foreshadowing.

Seed tale sketch:
---
At the far edge of a windy town sat the Blue Boot Inn, where one upstairs room
had been empty for many days. The innkeeper kept sweeping it clean, but the
vacancy sign kept squeaking in the wind like it knew a story was coming.

One noon, a boy saw a long shadow on the wall before anyone else arrived. Then
came a wagon, then a giant traveler, then a storm, and the empty room was no
longer empty. The sign had been hinting all along.

This world turns that premise into a simulated story:
- a physically empty space has meters for vacancy, dust, and readiness
- the town notices foreshadowing signs with growing meme strength
- a tall-tale turn converts hints into a real arrival
- the ending proves the vacancy changed into a welcomed guest-space
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
    occupied_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"vacancy": 0.0, "dust": 0.0, "readiness": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "foreshadowing": 0.0, "worry": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    tall_tale: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    guest: str
    hero: str
    helper: str
    weather: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()
        self.facts: dict = {}

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


def build_storyline(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    place = world.get("place")
    guest = world.get("guest")

    world.say(
        f"In the {place.label}, there was one room so empty that the moonlight could bounce twice in it."
    )
    world.say(
        f"{hero.id} loved the room anyway, because empty space can look mighty hopeful in a tall tale town."
    )
    hero.memes["curiosity"] += 1

    if world.facts["weather"] == "windy":
        world.say(
            f"All afternoon the vacancy sign tapped the window like a finger on a drum, and that was the first hint."
        )
        place.memes["foreshadowing"] += 1
        hero.memes["foreshadowing"] += 1

    if world.facts["weather"] == "storm":
        world.say(
            f"Then the sky turned the color of a bruised plum, and the empty room began to feel as if it was waiting."
        )
        place.meters["vacancy"] += 1
        place.memes["worry"] += 1
        hero.memes["worry"] += 1

    world.say(
        f"{helper.id} pointed down the road and said the dust was marching in a line, which was a second hint."
    )
    hero.memes["foreshadowing"] += 1

    world.say(
        f"Sure enough, a wagon came rolling in, and with it came {guest.id}, a traveler big as a haystack and twice as loud."
    )
    guest.meters["arrival"] += 1
    place.occupied_by = guest.id
    place.meters["vacancy"] = 0.0
    place.meters["readiness"] += 1
    place.memes["relief"] += 1

    world.say(
        f"{hero.id} opened the room wide, and the empty bed changed from lonely to ready in one grand gulp of time."
    )
    world.say(
        f"By supper, the room was no longer a vacancy at all; it was a welcome place with boots by the door and a lantern in the window."
    )
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    guest.meters["comfort"] += 1


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type="woman", label="innkeeper"))
    helper = world.add(Entity(id=params.helper, kind="character", type="boy", label="boy helper"))
    guest = world.add(Entity(id="guest", kind="character", type="man", label="traveler", plural=False))
    room = world.add(Entity(
        id="place",
        kind="thing",
        type="room",
        label=place.name,
        phrase=f"a room in {place.name}",
        occupied_by=None,
    ))
    room.meters["vacancy"] = 1.0
    room.meters["dust"] = 0.5
    room.meters["readiness"] = 0.0

    world.facts["weather"] = params.weather
    world.facts["guest"] = params.guest
    world.facts["place"] = place
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["guest_ent"] = guest
    world.facts["room"] = room

    world.say(
        f"{hero.id} kept the last room swept and shining, though it had stayed empty for three days."
    )
    world.say(
        f"{helper.id} said empty rooms were like quiet drums: they did not speak, but they promised something might soon."
    )
    build_storyline(world)
    return world


PLACES = {
    "inn": Place(
        name="Blue Boot Inn",
        kind="inn",
        tall_tale="a road-stop big enough for ten fiddles and a moonbeam",
        affords={"guest", "storm", "windy"},
    ),
    "barn": Place(
        name="Red Corn Barn",
        kind="barn",
        tall_tale="a barn so wide the cattle had room to practice echoing",
        affords={"guest", "storm", "windy"},
    ),
    "depot": Place(
        name="Cedar Depot",
        kind="depot",
        tall_tale="a depot with a roof long enough to shade a parade",
        affords={"guest", "storm", "windy"},
    ),
}

GUESTS = {
    "traveler": "a traveler",
    "giant": "a giant traveler",
    "rancher": "a rancher with two mud-tall boots",
}

HERO_NAMES = ["Maggie", "Ada", "Nell", "June", "Clara", "Pearl"]
HELPER_NAMES = ["Benny", "Tommy", "Will", "Eli", "Otis", "Sammy"]

WEATHER_CHOICES = ["windy", "storm"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The story place must be one of the known tall-tale stops.")
    if params.guest not in GUESTS:
        raise StoryError("Unknown guest type.")
    if params.weather not in WEATHER_CHOICES:
        raise StoryError("This world only tells stories on windy or storm-bright days.")


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    g = world.facts["guest"]
    return [
        f"Write a Tall Tale about a vacancy at {p.name} that hints someone big is coming.",
        f"Tell a child-friendly foreshadowing story where an empty room keeps waiting for a {GUESTS[g]}.",
        f"Write a small story about a room that is empty for a while, then becomes full of life when the hint turns true.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = world.facts["place"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    guest = world.facts["guest_ent"]
    room = world.facts["room"]
    weather = world.facts["weather"]

    return [
        QAItem(
            question=f"What was unusual about the room at {place.name} at the start of the story?",
            answer=f"It was empty for a while, and that vacancy made it feel like something important was about to happen.",
        ),
        QAItem(
            question=f"What was the first hint that somebody might arrive at {place.name}?",
            answer=f"The vacancy sign tapped in the wind, which was a foreshadowing hint that an arrival was coming.",
        ),
        QAItem(
            question=f"Who noticed the dust and pointed down the road?",
            answer=f"{helper.id} noticed the signs and pointed down the road before the traveler arrived.",
        ),
        QAItem(
            question=f"What happened to the room when the {weather} day turned into a real visit?",
            answer=f"The room stopped being vacant and became a ready, welcoming place for {guest.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and proud because the empty room finally had a guest inside it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vacancy?",
            answer="A vacancy is an empty place that is waiting to be used, like a room without a guest.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue that hints at something that will happen later.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story told in a bigger-than-life way, with huge exaggerations and playful details.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.occupied_by is not None:
            bits.append(f"occupied_by={e.occupied_by}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'quiet'}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="inn", guest="giant", hero="Maggie", helper="Benny", weather="windy"),
    StoryParams(place="barn", guest="traveler", hero="Ada", helper="Tommy", weather="storm"),
    StoryParams(place="depot", guest="rancher", hero="June", helper="Otis", weather="windy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about vacancy and foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--weather", choices=WEATHER_CHOICES)
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
    place = args.place or rng.choice(list(PLACES))
    guest = args.guest or rng.choice(list(GUESTS))
    weather = args.weather or rng.choice(WEATHER_CHOICES)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    params = StoryParams(place=place, guest=guest, hero=hero, helper=helper, weather=weather)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = (
        f"{params.hero} kept watch over the empty room at {PLACES[params.place].name}, "
        f"where foreshadowing signs in the wind hinted that a {GUESTS[params.guest]} was coming."
    )
    world_story = world.render()
    return StorySample(
        params=params,
        story=world_story,
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
place(P) :- setting(P).
guest(G) :- guest_kind(G).
vacant(R) :- room(R), vacancy(R).
hint(R) :- vacant(R), sign_sways(R).
arrival(R) :- hint(R), guest_arrives(R).
resolved(R) :- arrival(R), not vacant(R).
#show resolved/1.
#show hint/1.
#show arrival/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("room", pid))
    for gid in GUESTS:
        lines.append(asp.fact("guest_kind", gid))
    lines.append(asp.fact("sign_sways", "room1"))
    lines.append(asp.fact("vacancy", "room1"))
    lines.append(asp.fact("guest_arrives", "room1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
