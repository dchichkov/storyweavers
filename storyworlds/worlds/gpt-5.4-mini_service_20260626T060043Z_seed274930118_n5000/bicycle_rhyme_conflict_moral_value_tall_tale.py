#!/usr/bin/env python3
"""
storyworlds/worlds/bicycle_rhyme_conflict_moral_value_tall_tale.py
===================================================================

A small storyworld about a bicycle, a conflict over wanting a ride, a tall-tale
turn, and a moral ending with a rhyme.

The world is intentionally narrow: a child loves a shiny bicycle, another child
wants a turn, and the grown-up solves the squabble by turning the moment into a
big, funny, truth-stretching tale that ends in a moral about sharing.

The story is driven by simulated state:
- physical meters: speed, dust, wear, distance, gleam
- emotional memes: joy, jealousy, pride, patience, relief, honesty

The narrative instrument is a tall tale: the conflict gets exaggerated into a
ridiculous hill, a giant breeze, and a bicycle that seems almost magical.
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
    ridden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    slope: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Bicycle:
    label: str
    phrase: str
    color: str = "red"
    gear: str = "shiny bell"
    speediness: str = "quick as a cricket"
    can_share: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


@dataclass
class StoryParams:
    place: str
    hero: str
    rival: str
    hero_kind: str
    rival_kind: str
    seed: Optional[int] = None


PLACES = {
    "hill": Place(name="the hill", slope="steep and windy", afford={"ride", "race", "coast"}),
    "yard": Place(name="the yard", slope="wide and grassy", afford={"ride", "race"}),
    "lane": Place(name="the lane", slope="long and dusty", afford={"ride", "coast"}),
}

HERO_NAMES = ["Mabel", "Otis", "Nora", "Jasper", "Ada", "Silas"]
RIVAL_NAMES = ["Junie", "Benny", "Poppy", "Theo", "Lula", "Milo"]

BICYCLES = {
    "bicycle": Bicycle(label="bicycle", phrase="a bright blue bicycle", color="blue", gear="silver bell"),
}

MORALS = [
    "Sharing makes the ride feel lighter.",
    "A truthful tale can calm a rocky spat.",
    "Taking turns is a kinder way to roll.",
]


class StoryWorld(World):
    pass


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = _meter(ent, key) + value


def _add_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = _meme(ent, key) + value


def _narrate_setup(world: World, hero: Entity, rival: Entity, bike: Entity) -> None:
    world.say(
        f"{hero.id} had a {bike.phrase} that gleamed like a coin in the sun."
    )
    world.say(
        f"{hero.id} loved {bike.it()} so much that even the bell seemed to wink when {hero.pronoun('subject')} smiled."
    )
    world.say(
        f"But {rival.id} wanted a turn too, and that is where the trouble began."
    )
    _add_meme(hero, "pride", 1)
    _add_meme(rival, "wanting", 1)


def _spark_conflict(world: World, hero: Entity, rival: Entity, bike: Entity) -> None:
    _add_meme(rival, "jealousy", 1)
    _add_meme(hero, "defiance", 1)
    _add_meme(hero, "conflict", 1)
    _add_meme(rival, "conflict", 1)
    world.say(
        f"{rival.id} said, \"Mine now!\" and {hero.id} said, \"No, not yet!\""
    )
    world.say(
        f"Their words bounced back and forth like peas in a tin pan."
    )


def _tall_tale_turn(world: World, hero: Entity, rival: Entity, bike: Entity) -> None:
    place = world.place
    _add_meter(bike, "dust", 1)
    _add_meter(bike, "wear", 1)
    _add_meme(hero, "surprise", 1)
    world.say(
        f"Then the grown-up pointed to {place.name} and told a tall tale."
    )
    world.say(
        f"\"This hill is so steep,\" they said, \"that a fly must lean forward to stay in the air.\""
    )
    world.say(
        f"\"And this bicycle is so quick that it could chase a giggle around a corner and catch it by the tail.\""
    )
    world.say(
        f"{hero.id} blinked. {rival.id} blinked harder."
    )
    _add_meme(hero, "curiosity", 1)
    _add_meme(rival, "curiosity", 1)


def _resolve(world: World, hero: Entity, rival: Entity, bike: Entity, moral: str) -> None:
    _add_meme(hero, "patience", 1)
    _add_meme(rival, "patience", 1)
    _add_meme(hero, "relief", 1)
    _add_meme(rival, "relief", 1)
    _add_meme(hero, "joy", 1)
    _add_meme(rival, "joy", 1)
    bike.ridden_by = hero.id
    world.say(
        f"{hero.id} took the first turn, then {hero.id} gave {bike.it()} to {rival.id} without a grumble."
    )
    world.say(
        f"{rival.id} laughed, pedaled off, and the bell rang like a tiny silver song."
    )
    world.say(
        f"When the bicycle came back, both children rode it together as the wind whooshed and whistled."
    )
    world.say(
        f"In the end, the grown-up smiled and said, \"{moral}\""
    )


def tell(place: Place, params: StoryParams) -> StoryWorld:
    world = StoryWorld(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_kind, label=params.hero))
    rival = world.add(Entity(id=params.rival, kind="character", type=params.rival_kind, label=params.rival))
    bike_cfg = BICYCLES["bicycle"]
    bike = world.add(Entity(
        id="bike",
        type="bicycle",
        label=bike_cfg.label,
        phrase=bike_cfg.phrase,
        owner=hero.id,
        ridden_by=hero.id,
    ))
    _set_meter(bike, "gleam", 2)
    _set_meter(bike, "distance", 0)
    _set_meter(bike, "wear", 0)
    _set_meter(bike, "dust", 0)
    _add_meme(hero, "joy", 1)
    _add_meme(hero, "love", 1)

    _narrate_setup(world, hero, rival, bike)
    world.para()
    world.say(
        f"One day at {place.name}, the air was {place.slope} and ready for a ride."
    )
    world.say(
        f"{rival.id} reached for the handlebars, and that was enough to stir up a quarrel."
    )
    _spark_conflict(world, hero, rival, bike)
    world.para()
    _tall_tale_turn(world, hero, rival, bike)
    _resolve(world, hero, rival, bike, MORALS[1])

    world.facts.update(
        hero=hero,
        rival=rival,
        bike=bike,
        moral=MORALS[1],
        place=place,
    )
    return world


def prize_at_risk(place: Place) -> bool:
    return "ride" in place.afford or "coast" in place.afford


def valid_story(place_key: str) -> bool:
    return place_key in PLACES and prize_at_risk(PLACES[place_key])


def valid_combos() -> list[tuple[str]]:
    return [(k,) for k in PLACES if valid_story(k)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tall-tale storyworld about a bicycle, a conflict, and a moral value."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--rival")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--rival-kind", choices=["girl", "boy"])
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
    if not valid_story(place):
        raise StoryError("That place cannot support the bicycle ride.")
    hero_kind = args.hero_kind or rng.choice(["girl", "boy"])
    rival_kind = args.rival_kind or ("boy" if hero_kind == "girl" else "girl")
    hero_pool = HERO_NAMES if hero_kind == "girl" else HERO_NAMES + ["Eli", "Tobin"]
    rival_pool = RIVAL_NAMES if rival_kind == "girl" else RIVAL_NAMES + ["Cal", "Finn"]
    hero = args.name or rng.choice(hero_pool)
    rival = args.rival or rng.choice([n for n in rival_pool if n != hero])
    if hero == rival:
        raise StoryError("The hero and rival must be different people.")
    return StoryParams(place=place, hero=hero, rival=rival, hero_kind=hero_kind, rival_kind=rival_kind)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall-tale style story about {f['hero'].id}, a bicycle, and a quarrel at {f['place'].name}.",
        f"Tell a child-friendly rhyme-filled story where {f['rival'].id} wants a turn on the bicycle.",
        "Make the ending carry a moral about sharing or taking turns.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    bike = f["bike"]
    place = f["place"]
    moral = f["moral"]
    return [
        QAItem(
            question=f"Who had the shiny bicycle in the story?",
            answer=f"{hero.id} had the shiny bicycle at first.",
        ),
        QAItem(
            question=f"Why did {rival.id} get into a conflict with {hero.id}?",
            answer=f"{rival.id} wanted a turn on the bicycle, and {hero.id} did not want to share right away.",
        ),
        QAItem(
            question=f"What tall-tale thing did the grown-up say about {place.name}?",
            answer=f"The grown-up said {place.name} was so steep that even a fly would have to lean forward to stay in the air.",
        ),
        QAItem(
            question=f"What happened at the end with the bicycle?",
            answer=f"The children took turns and even rode together, so the bicycle became a shared joy instead of a fight.",
        ),
        QAItem(
            question=f"What moral was spoken at the end?",
            answer=moral,
        ),
        QAItem(
            question=f"What sound did the bicycle make when {rival.id} rode it?",
            answer=f"The bell rang like a tiny silver song.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bicycle for?",
            answer="A bicycle is for riding by turning the pedals and rolling on two wheels.",
        ),
        QAItem(
            question="Why do people share turns on toys or bikes?",
            answer="People share turns so everyone can have a chance and so the play stays kind.",
        ),
        QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson a story teaches about how to act wisely or kindly.",
        ),
        QAItem(
            question="What makes a tall tale funny?",
            answer="A tall tale is funny because it stretches the truth in a huge, playful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.ridden_by:
            bits.append(f"ridden_by={e.ridden_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_valid(P) :- place(P).
valid(P) :- place_valid(P).
#show valid/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", p) for p in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="hill", hero="Mabel", rival="Junie", hero_kind="girl", rival_kind="girl"),
    StoryParams(place="yard", hero="Otis", rival="Milo", hero_kind="boy", rival_kind="boy"),
    StoryParams(place="lane", hero="Nora", rival="Theo", hero_kind="girl", rival_kind="boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} ASP-valid places:")
        for (p,) in asp_valid_combos():
            print(f"  {p}")
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
            except StoryError as e:
                print(e)
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
