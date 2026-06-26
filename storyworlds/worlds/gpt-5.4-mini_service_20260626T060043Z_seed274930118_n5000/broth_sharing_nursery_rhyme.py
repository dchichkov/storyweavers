#!/usr/bin/env python3
"""
A small Storyweavers world: broth sharing in a nursery-rhyme style.

Seed tale premise:
A little friend makes a warm pot of broth, but there is only one bowl.
The friends each want some, and the answer is not grabbing or hoarding,
but sharing the spoon, the bowl, and the smiles.

The simulated world tracks:
- physical meters: full / hot / clean / empty / spilled
- emotional memes: want / worry / kindness / gladness / fairness

The story is generated from world state, not from a fixed paragraph.
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
    plural: bool = False
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"full": 0.0, "hot": 0.0, "clean": 0.0, "empty": 0.0, "spilled": 0.0}
        if not self.memes:
            self.memes = {"want": 0.0, "worry": 0.0, "kindness": 0.0, "gladness": 0.0, "fairness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the little kitchen"
    affords: set[str] = field(default_factory=lambda: {"make_broth", "share_broth"})


@dataclass
class StoryParams:
    place: str = "kitchen"
    hero: str = "Mimi"
    friend: str = "Pip"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def pronounce_name(name: str) -> str:
    return name


def is_valid_pair(hero: str, friend: str) -> bool:
    return hero != friend


def valid_combos() -> list[tuple[str, str, str]]:
    places = ["kitchen", "cottage"]
    names = [("Mimi", "Pip"), ("Nora", "Toby"), ("Ruby", "Milo"), ("Lulu", "Benny")]
    return [(place, hero, friend) for place in places for hero, friend in names if is_valid_pair(hero, friend)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if not combos:
        raise StoryError("No valid story fits the given choices.")
    place, hero, friend = rng.choice(combos)
    if args.hero:
        hero = args.hero
    if args.friend:
        friend = args.friend
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(place=place, hero=hero, friend=friend)


def setup_world(params: StoryParams) -> World:
    place = Place(name=f"the {params.place}")
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    pot = world.add(Entity(id="pot", type="pot", label="pot", phrase="a little pot of broth"))
    bowl = world.add(Entity(id="bowl", type="bowl", label="bowl", phrase="one small bowl", plural=False))
    spoon = world.add(Entity(id="spoon", type="spoon", label="spoon", phrase="a tiny spoon"))
    world.facts.update(hero=hero, friend=friend, pot=pot, bowl=bowl, spoon=spoon, place=place)
    return world


def warm_broth(world: World) -> None:
    pot = world.get("pot")
    pot.meters["hot"] = 1.0
    pot.meters["full"] = 1.0
    world.say("In the little kitchen, a pot of broth began to hum and glow.")
    world.say("It sat warm on the stove and smelled sweet and kind.")


def want_broth(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["want"] += 1
    friend.memes["want"] += 1
    world.say(f"{hero.id} looked at the pot and wanted a sip.")
    world.say(f"{friend.id} looked too, and wanted some as well.")


def worry_about_sharing(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say("But there was only one bowl, so the room grew small with worry.")
    world.say("Each one wondered if there would be enough.")


def share_broth(world: World, hero: Entity, friend: Entity) -> None:
    pot = world.get("pot")
    bowl = world.get("bowl")
    spoon = world.get("spoon")
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    hero.memes["fairness"] += 1
    friend.memes["fairness"] += 1
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    hero.memes["gladness"] += 1
    friend.memes["gladness"] += 1
    bowl.shared_with = {hero.id, friend.id}
    bowl.meters["clean"] = 1.0
    pot.meters["full"] = 0.0
    pot.meters["empty"] = 1.0
    world.say(
        f"Then {hero.id} said, 'You may have the first sip.' "
        f"{friend.id} smiled and said, 'And you may have the next.'"
    )
    world.say(
        f"They shared the spoon, and they shared the bowl, and the broth went round and round like a happy song."
    )
    world.say(
        f"In the end, both children had warm broth, and the little spoon did not mind at all."
    )


def generate_story(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    friend = world.get(world.facts["friend"].id)
    warm_broth(world)
    world.para()
    want_broth(world, hero, friend)
    worry_about_sharing(world, hero, friend)
    world.para()
    share_broth(world, hero, friend)


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"Who wanted broth in the story?",
            answer=f"{hero.id} and {friend.id} both wanted broth."
        ),
        QAItem(
            question=f"What did they share?",
            answer="They shared the spoon, the bowl, and the broth."
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with both children happy and warmed by shared broth."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is broth?",
            answer="Broth is a warm, thin soup made by simmering food in water."
        ),
        QAItem(
            question="Why do people share food?",
            answer="People share food so everyone can have some and feel cared for."
        ),
    ]


ASP_RULES = r"""
hero(H). friend(F) :- hero_name(H), friend_name(F).
wants_broth(H) :- hero(H).
wants_broth(F) :- friend(F).
fair_share(H,F) :- wants_broth(H), wants_broth(F), hero(H), friend(F), H != F.
shared_broth(H,F) :- fair_share(H,F).
#show fair_share/2.
#show shared_broth/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "Mimi"),
        asp.fact("friend_name", "Pip"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fair_share/2."))
    return sorted(set(asp.atoms(model, "fair_share")))


def asp_verify() -> int:
    py = {(a, b) for _, a, b in valid_combos()}
    asp_set = set(asp_valid_combos())
    if asp_set == py:
        print(f"OK: ASP matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH")
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    return 1


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
        if e.shared_with:
            parts.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"].id
    friend = world.facts["friend"].id
    place = world.facts["place"].name
    return [
        f"Write a tiny nursery rhyme about {hero} and {friend} sharing broth in {place}.",
        f"Tell a gentle story where two children learn to share a warm bowl of broth.",
        f"Write a rhyming story about broth, one bowl, and a happy sharing moment.",
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about sharing broth.")
    ap.add_argument("--place", choices=["kitchen", "cottage"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show fair_share/2.\n#show shared_broth/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show fair_share/2.\n#show shared_broth/2."))
        print(asp.atoms(model, "fair_share"))
        print(asp.atoms(model, "shared_broth"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, hero, friend in valid_combos():
            samples.append(generate(StoryParams(place=place, hero=hero, friend=friend, seed=base_seed)))
    else:
        seen = set()
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
            header = f"### {p.hero} and {p.friend} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
