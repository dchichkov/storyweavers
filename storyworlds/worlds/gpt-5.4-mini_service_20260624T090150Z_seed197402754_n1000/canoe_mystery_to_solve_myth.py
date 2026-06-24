#!/usr/bin/env python3
"""
storyworlds/worlds/canoe_mystery_to_solve_myth.py
=================================================

A small mythic storyworld about a canoe mystery to solve.

Seed image:
- canoe
- mystery to solve
- style: myth

Core premise:
A child or young hero finds a strange canoe problem in a river place. The
people of the story must figure out why the canoe will not move, what hidden
thing is wrong, and how a careful, brave fix restores the journey.

The world is modeled with physical meters and emotional memes. A mystery is
not just a frozen paragraph: clues, suspicion, and discovery are driven by the
state of the river, canoe, cargo, and helper.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    river: bool = True
    reeds: bool = False
    stones: bool = False
    mist: bool = False
    deep: bool = False


@dataclass
class Mystery:
    id: str
    clue: str
    culprit: str
    fix: str
    requires: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    method: str
    result: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mystery_clue_found = False
        self.mystery_solved = False

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.mystery_clue_found = self.mystery_clue_found
        c.mystery_solved = self.mystery_solved
        return c


def pronounce_name(hero: Entity) -> str:
    return hero.id


PLACES = {
    "riverbank": Place(id="riverbank", label="the riverbank", river=True, reeds=True, stones=True, mist=False, deep=False),
    "foggy_ford": Place(id="foggy_ford", label="the foggy ford", river=True, reeds=True, stones=True, mist=True, deep=False),
    "deep_bend": Place(id="deep_bend", label="the deep bend", river=True, reeds=False, stones=True, mist=True, deep=True),
}

MYSTERIES = {
    "stuck_canoe": Mystery(
        id="stuck_canoe",
        clue="a dark rope around the canoe's stern",
        culprit="rope snag",
        fix="cutting the rope free",
        requires={"knife", "care"},
    ),
    "leaky_canoe": Mystery(
        id="leaky_canoe",
        clue="a small crack under the canoe's seat",
        culprit="hidden crack",
        fix="patching the crack with pitch",
        requires={"pitch", "warmth"},
    ),
    "silent_canoe": Mystery(
        id="silent_canoe",
        clue="the paddle had been left on the wrong shore",
        culprit="missing paddle",
        fix="finding the paddle by the reeds",
        requires={"paddle", "search"},
    ),
}

GUIDES = {
    "old_heron": Guide(id="old_heron", label="an old heron", method="watching the water", result="notice the hidden trouble"),
    "river_mother": Guide(id="river_mother", label="the river mother", method="listening to the ripples", result="hear where the canoe was trapped"),
    "stone_boy": Guide(id="stone_boy", label="a stone-hearted boy", method="following the tracks", result="find the lost thing"),
}

NAMES = ["Ari", "Mira", "Soren", "Lina", "Tao", "Nia", "Eli", "Zora"]
KINDS = ["boy", "girl"]
TRAITS = ["curious", "brave", "patient", "gentle", "wary", "clever"]


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def observe_mystery(world: World, hero: Entity, canoe: Entity, mystery: Mystery) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(
        f"{hero.id} found a canoe resting at {world.place.label}, and something about it felt wrong. "
        f"{mystery.clue.capitalize()} made {hero.pronoun('object')} think a secret was hiding nearby."
    )
    world.mystery_clue_found = True
    world.facts["clue"] = mystery.clue
    world.facts["mystery"] = mystery


def test_canoe(world: World, hero: Entity, canoe: Entity, mystery: Mystery) -> None:
    if mystery.id == "stuck_canoe":
        canoe.meters["stuck"] = 1.0
    elif mystery.id == "leaky_canoe":
        canoe.meters["wet"] = 1.0
        canoe.meters["leak"] = 1.0
    elif mystery.id == "silent_canoe":
        canoe.meters["paddle_missing"] = 1.0
    hero.memes["puzzled"] = hero.memes.get("puzzled", 0.0) + 1
    world.say(f"{hero.id} pushed the canoe, but it would not answer as it should.")


def ask_guide(world: World, hero: Entity, guide: Guide, mystery: Mystery) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} went to {guide.label}, who knew {guide.method}. "
        f"{guide.label.capitalize()} said that careful eyes could {guide.result}."
    )


def solve(world: World, hero: Entity, canoe: Entity, mystery: Mystery) -> None:
    if mystery.id == "stuck_canoe":
        canoe.meters["stuck"] = 0.0
        canoe.meters["free"] = 1.0
        world.say(
            f"At last {hero.id} found the dark rope wrapped around the stern, and {hero.pronoun('subject')} "
            f"cut it free. The canoe slid into the water as if it had been waiting for that mercy."
        )
    elif mystery.id == "leaky_canoe":
        canoe.meters["leak"] = 0.0
        canoe.meters["patched"] = 1.0
        canoe.meters["dry"] = 1.0
        world.say(
            f"{hero.id} warmed pitch by the fire, smoothed it over the crack, and pressed until it held. "
            f"The little leak disappeared, and the canoe stayed dry and strong."
        )
    elif mystery.id == "silent_canoe":
        canoe.meters["paddle_missing"] = 0.0
        canoe.meters["ready"] = 1.0
        world.say(
            f"{hero.id} searched by the reeds until the missing paddle was found beside a mossy stone. "
            f"With the paddle back in hand, the canoe could travel again."
        )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.mystery_solved = True
    world.facts["solved"] = mystery.fix


def ending_image(world: World, hero: Entity, canoe: Entity) -> None:
    if world.mystery_solved:
        world.say(
            f"Before sunset, {hero.id} rode in the canoe across the shining river. "
            f"The water moved softly under the hull, and the old mystery was gone."
        )
    else:
        world.say(f"{hero.id} stood beside the canoe, still wondering what secret it held.")


def tell(place: Place, mystery: Mystery, hero_name: str, hero_type: str, trait: str, guide: Guide) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"walk": 0.0}, memes={"wonder": 0.0}))
    canoe = world.add(Entity(id="canoe", type="canoe", label="canoe", phrase="a small cedar canoe", meters={"stuck": 0.0, "wet": 0.0}))
    river = world.add(Entity(id="river", type="river", label="river"))
    world.facts.update(hero=hero, canoe=canoe, river=river, guide=guide, trait=trait, place=place, mystery=mystery)

    world.say(
        f"In old times, {hero.id} was a {trait} {hero.type} who loved the river near {place.label}. "
        f"The people said the water remembered every boat that crossed it."
    )
    world.say(
        f"One morning, {hero.id} saw {canoe.phrase}, and the canoe seemed to wait like a creature with a missing thought."
    )

    world.para()
    observe_mystery(world, hero, canoe, mystery)
    test_canoe(world, hero, canoe, mystery)
    ask_guide(world, hero, guide, mystery)

    world.para()
    solve(world, hero, canoe, mystery)
    ending_image(world, hero, canoe)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    return [
        f"Write a short mythic story for a child about {hero.id} and a canoe mystery at {place.label}.",
        f"Tell a gentle myth where a canoe is troubled by {mystery.culprit} and a brave child helps solve it.",
        f"Write a story about a canoe, a secret clue, and a wise helper near the river.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    guide: Guide = f["guide"]
    place: Place = f["place"]
    canoe: Entity = f["canoe"]
    return [
        QAItem(
            question=f"What did {hero.id} find near {place.label}?",
            answer=f"{hero.id} found a canoe resting near {place.label}, and it seemed to be hiding a mystery.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} understand the trouble with the canoe?",
            answer=f"The clue was {mystery.clue}, which pointed toward {mystery.culprit}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think about the mystery?",
            answer=f"{guide.label.capitalize()} helped by {guide.method}, so {hero.id} could understand what was wrong.",
        ),
        QAItem(
            question=f"What changed for the canoe at the end?",
            answer=f"The canoe was fixed by {mystery.fix}, and then it could move on the river again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canoe?",
            answer="A canoe is a small boat that people paddle on rivers and lakes.",
        ),
        QAItem(
            question="Why do people solve mysteries in stories?",
            answer="People solve mysteries in stories to find out what caused a problem and how to make things right again.",
        ),
        QAItem(
            question="What does a river do?",
            answer="A river is flowing water that moves across the land and can carry boats along.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  mystery_clue_found={world.mystery_clue_found}")
    lines.append(f"  mystery_solved={world.mystery_solved}")
    return "\n".join(lines)


CURATED = [
    ("riverbank", "stuck_canoe", "Ari", "boy", "curious", "old_heron"),
    ("foggy_ford", "leaky_canoe", "Mira", "girl", "brave", "river_mother"),
    ("deep_bend", "silent_canoe", "Tao", "boy", "clever", "stone_boy"),
]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    trait: str
    guide: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic canoe mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    guide = args.guide or rng.choice(list(GUIDES))
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, trait=trait, guide=guide)


ASP_RULES = r"""
% A canoe mystery is solvable when the clue matches a known fix path.
solvable(M) :- mystery(M), clue_for(M, _), fix_for(M, _).

% Story-valid means the place has a river, the mystery is solvable, and a guide exists.
valid_story(P, M, G) :- place(P), river_place(P), mystery(M), solvable(M), guide(G).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.river:
            lines.append(asp.fact("river_place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_for", mid, m.culprit))
        lines.append(asp.fact("fix_for", mid, m.fix))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {
        (p, m, g)
        for p, m, _, _, _, g in CURATED
    }
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: ASP gate matches curated story set ({len(got)} stories).")
        return 0
    print("MISMATCH between ASP and curated stories:")
    print("  only in ASP:", sorted(got - expected))
    print("  only in curated:", sorted(expected - got))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MYSTERIES[params.mystery],
        params.name,
        params.gender,
        params.trait,
        GUIDES[params.guide],
    )
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story triples:\n")
        for p, m, g in stories:
            print(f"  {p:12} {m:14} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, mystery, name, gender, trait, guide in CURATED:
            params = StoryParams(place=place, mystery=mystery, name=name, gender=gender, trait=trait, guide=guide, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
