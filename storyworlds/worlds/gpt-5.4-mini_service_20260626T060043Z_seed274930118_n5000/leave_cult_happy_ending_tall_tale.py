#!/usr/bin/env python3
"""
storyworlds/worlds/leave_cult_happy_ending_tall_tale.py
=======================================================

A small standalone story world about leaving a bossy cult and finding a happy
ending, told in a tall-tale style with exaggerated, concrete world state.

Seed tale:
---
A child was stuck in a far-off cult that made everyone march, hush, and obey
the Tall Bell. One windy day, the child noticed a lantern, a kindly aunt, and a
little road that curled away past the pines. The child left the cult, followed
the aunt, and ended the night warm, safe, and laughing under a sky full of
stars.

This script turns that seed into a simulated domain:
- physical state: distance walked, storm, warmth, lantern light, packed bundle
- emotional state: fear, hope, loyalty, relief, belonging
- conflict: whether the child can leave the cult without losing everything
- ending: a genuine happy ending where the child reaches safety and a new home
"""

from __future__ import annotations

import argparse
import dataclasses
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "aunt", "grandmother", "mom"}
        male = {"boy", "man", "uncle", "grandfather", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    sky: str
    road: str
    comforts: list[str] = field(default_factory=list)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    kind: str
    helpful: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    cult_name: str
    storm: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_artifact(self, a: Artifact) -> Artifact:
        self.artifacts[a.id] = a
        return a

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def hero_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    if gender == "boy":
        return "he", "him", "his"
    return "they", "them", "their"


def setting_detail(place: Place, storm: str) -> str:
    if place.kind == "woods":
        return f"The pines stood tall as fence posts, and {storm} rode over the trees."
    if place.kind == "valley":
        return f"The valley spread out like a giant wooden spoon, and {storm} rolled through it."
    return f"The road curled past the {place.label}, while {storm} shook the windows and the weeds."


def tall_tale_opening(hero: Entity, cult_name: str) -> str:
    return (
        f"{hero.id} was a little {hero.type} with a big heart and a bigger wish: "
        f"to stop bowing to the {cult_name} and its Tall Bell."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add_entity(Entity(
        id=params.hero_name, kind="character", type=params.hero_gender,
        meters={"distance": 0.0, "warmth": 1.0},
        memes={"fear": 1.0, "hope": 0.5, "loyalty": 1.0, "relief": 0.0, "belonging": 0.0},
    ))
    helper = world.add_entity(Entity(
        id=params.helper_name, kind="character", type=params.helper_gender,
        meters={"distance": 0.0, "warmth": 2.0},
        memes={"kindness": 2.0, "hope": 1.0},
    ))
    leader = world.add_entity(Entity(
        id="leader", kind="character", type="man",
        label=f"the leader of the {params.cult_name}",
        meters={"distance": 0.0},
        memes={"control": 2.0, "pride": 1.0},
    ))

    lantern = world.add_artifact(Artifact(
        id="lantern", label="lantern", phrase="a small brass lantern", kind="light", helpful=True
    ))
    bundle = world.add_artifact(Artifact(
        id="bundle", label="bundle", phrase="a little cloth bundle with bread and socks", kind="comfort", helpful=True
    ))
    map_item = world.add_artifact(Artifact(
        id="map", label="map", phrase="a folded map with a pencil mark for home", kind="guide", helpful=True
    ))

    world.facts.update(hero=hero, helper=helper, leader=leader, lantern=lantern, bundle=bundle, map=map_item, place=place, params=params)
    return world


def move_toward_safety(world: World, hero: Entity, helper: Entity, storm: str) -> None:
    hero.meters["distance"] += 4.0
    helper.meters["distance"] += 4.0
    hero.memes["fear"] += 0.2
    hero.memes["hope"] += 0.8
    hero.memes["loyalty"] -= 0.8
    hero.memes["relief"] += 0.4
    hero.meters["warmth"] += 0.3
    helper.meters["warmth"] += 0.1
    world.say(
        f"So {hero.id} left the cult at dusk, with {helper.id} beside {hero.pronoun('object')}, "
        f"and they took the little road past the pines."
    )
    world.say(setting_detail(world.place, storm))


def leave_beat(world: World, hero: Entity, leader: Entity, helper: Entity) -> None:
    hero.memes["fear"] += 0.4
    hero.memes["loyalty"] -= 1.0
    leader.memes["control"] += 0.2
    world.say(
        f"The leader tried to thunder like a runaway drum, but {hero.id} had already "
        f"set {hero.pronoun('possessive')} heels on freedom."
    )
    world.say(
        f"{hero.id} did not shout back. {hero.pronoun().capitalize()} simply turned toward "
        f"{helper.id} and the open road."
    )


def shelter_and_feeding(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["warmth"] += 1.5
    hero.memes["relief"] += 1.3
    hero.memes["belonging"] += 1.0
    world.say(
        f"{helper.id} lit the lantern and handed over the bundle, and {hero.id} found bread, "
        f"socks, and a kind hand all at once."
    )


def resolution(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["hope"] += 0.5
    hero.memes["belonging"] += 2.0
    world.say(
        f"By the time the stars came out over the {place.label}, {hero.id} was warm, fed, and safe."
    )
    world.say(
        f"{hero.id} tucked the old cult rules behind the last tree and laughed as if the moon itself had "
        f"opened a front door."
    )
    world.say(
        f"That was the happiest kind of leaving: not lost, but found."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    leader: Entity = world.facts["leader"]

    world.say(tall_tale_opening(hero, params.cult_name))
    world.say(
        f"Every morning in the cult, the people had to march in a ring and nod at the Tall Bell "
        f"until their necks grew sore."
    )
    world.para()
    world.say(
        f"Then one windy evening, {helper.id} arrived with a lantern, a map, and a voice as gentle as rain on a tin roof."
    )
    world.say(
        f"{helper.id} told {hero.id} there was a better home beyond the hill, where no bell would boss anybody around."
    )
    world.para()
    leave_beat(world, hero, leader, helper)
    move_toward_safety(world, hero, helper, params.storm)
    shelter_and_feeding(world, hero, helper)
    world.para()
    resolution(world, hero, helper, world.place)

    world.facts["escaped"] = True
    world.facts["happy_ending"] = True
    return world


PLACES = {
    "woods": Place(
        id="woods",
        label="woods",
        kind="woods",
        sky="starry",
        road="a narrow dirt road",
        comforts=["pine needles", "moss", "a cabin light"],
    ),
    "valley": Place(
        id="valley",
        label="valley",
        kind="valley",
        sky="windy",
        road="a crooked wagon road",
        comforts=["warm bread", "a spring", "a quilted chair"],
    ),
    "riverbank": Place(
        id="riverbank",
        label="riverbank",
        kind="riverbank",
        sky="silver",
        road="a sandy path",
        comforts=["smooth stones", "fish soup", "reeds"],
    ),
}

CULT_NAMES = ["Moon Hymn Cult", "Tall Bell Cult", "River Whisper Cult", "Sun-Oath Cult"]
HERO_NAMES = ["Mira", "Jesse", "Nell", "Otis", "Poppy", "Rue"]
HELPER_NAMES = ["Aunt June", "Uncle Bram", "Grandma Tess", "Aunt Ivy"]
STORMS = ["a windy storm", "a silver rain", "a hard blowing night", "a sky-scraping gust"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, h) for p in PLACES for c in CULT_NAMES for h in HELPER_NAMES]


@dataclass
class ASPModel:
    pass


ASP_RULES = r"""
place(woods;valley;riverbank).
helper(aunt_june;uncle_bram;grandma_tess;aunt_ivy).
cult(moon_hymn_cult;tall_bell_cult;river_whisper_cult;sun_oath_cult).

happy_ending(P,C,H) :- place(P), cult(C), helper(H).

#show happy_ending/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CULT_NAMES:
        lines.append(asp.fact("cult", c))
    for h in HELPER_NAMES:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/3."))
    return sorted(set(asp.atoms(model, "happy_ending")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if len(py) == len(cl):
        print(f"OK: ASP and Python agree on {len(py)} happy-ending combinations.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: leave the cult and reach a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--cult", choices=CULT_NAMES)
    ap.add_argument("--storm", choices=STORMS)
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
    cult = args.cult or rng.choice(CULT_NAMES)
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    storm = args.storm or rng.choice(STORMS)
    return StoryParams(
        place=place,
        hero_name=hero,
        hero_gender="girl" if hero in {"Mira", "Nell", "Poppy", "Rue"} else "boy",
        helper_name=helper,
        helper_gender="woman" if "Aunt" in helper or "Grandma" in helper else "man",
        cult_name=cult,
        storm=storm,
    )


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short tall tale for a child about leaving the {p.cult_name} and finding a happy ending.',
        f"Tell a gentle story set in the {world.place.label} where {p.hero_name} follows {p.helper_name} away from a bossy cult.",
        f'Write a big-hearted story that uses the words "leave" and "cult" and ends in safety and warmth.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who left the {p.cult_name}?",
            answer=f"{hero.id} left the {p.cult_name} with {helper.id} beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"Why did {hero.id} leave the cult?",
            answer=f"{hero.id} left because the cult was bossy and the Tall Bell made everyone obey, but {helper.id} promised a safer home.",
        ),
        QAItem(
            question=f"What was the happy ending in the {place.label}?",
            answer=f"The happy ending was that {hero.id} reached safety, got warm food and a lantern, and was laughing under the stars.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern holds light so people can see the path in the dark.",
        ),
        QAItem(
            question="What is a cult?",
            answer="A cult is a group that uses strong pressure and odd rules to make people obey, which is not kind or fair.",
        ),
        QAItem(
            question="What does a map do?",
            answer="A map helps people find their way from one place to another.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(place="woods", hero_name="Mira", hero_gender="girl", helper_name="Aunt June", helper_gender="woman", cult_name="Tall Bell Cult", storm="a windy storm"),
    StoryParams(place="valley", hero_name="Otis", hero_gender="boy", helper_name="Grandma Tess", helper_gender="woman", cult_name="Moon Hymn Cult", storm="a silver rain"),
    StoryParams(place="riverbank", hero_name="Poppy", hero_gender="girl", helper_name="Aunt Ivy", helper_gender="woman", cult_name="River Whisper Cult", storm="a hard blowing night"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} happy-ending combinations:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
