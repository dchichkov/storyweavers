#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lack_what_magic_tall_tale.py
===========================================================================================================

A small tall-tale storyworld about a village that runs short on magic, then
finds a brave, practical way to bring wonder back.

The seed suggests the words "lack", "what", and "Magic", so the storyworld keeps
those as central vocabulary and theme. The prose is exaggerated and child-facing
in a tall-tale style, but the simulation remains small and concrete: a place can
lack magic, a helper can fetch a missing charm, and a spell can fail or succeed
depending on a simple physical condition.

Core premise:
- A village well, lantern, or field has lost its magic.
- A child or keeper asks what to do.
- A companion notices the lack and tries a plan.
- The ending proves the magic returned in the world state, not just in the words.
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

MAGIC_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    wonders: set[str] = field(default_factory=set)
    lacks_magic_until: int = 0


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    restores: int = 1


@dataclass
class StoryParams:
    place: str
    charm: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.place_magic: float = 0.0
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        c = World(copy.deepcopy(self.place))
        c.entities = copy.deepcopy(self.entities)
        c.place_magic = self.place_magic
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


PLACE_REGISTRY = {
    "lantern_field": Place(id="lantern_field", label="the Lantern Field", wonders={"lanterns", "fireflies"}),
    "moon_well": Place(id="moon_well", label="the Moon Well", wonders={"water", "reflections"}),
    "windmill_hill": Place(id="windmill_hill", label="the Windmill Hill", wonders={"wind", "spinning"}),
}

CHARM_REGISTRY = {
    "golden_key": Charm(id="golden_key", label="a golden key", phrase="a shiny golden key", restores=1),
    "blue_bell": Charm(id="blue_bell", label="a blue bell", phrase="a tiny blue bell", restores=1),
    "star_map": Charm(id="star_map", label="a star map", phrase="a folded star map", restores=2),
}

HERO_NAMES = ["Milo", "Nora", "Pip", "Tessa", "Owen", "Lia", "Jun", "Maisie"]
TRAITS = ["bright-eyed", "curious", "bold", "cheerful", "steady", "spirited"]


def place_needs_magic(place: Place) -> bool:
    return True


def charm_works(place: Place, charm: Charm) -> bool:
    if place.id == "lantern_field":
        return charm.id in {"golden_key", "blue_bell", "star_map"}
    if place.id == "moon_well":
        return charm.id in {"blue_bell", "star_map"}
    if place.id == "windmill_hill":
        return charm.id in {"golden_key", "star_map"}
    return False


def reasonableness_gate(place: Place, charm: Charm) -> bool:
    return place_needs_magic(place) and charm_works(place, charm)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for w in sorted(place.wonders):
            lines.append(asp.fact("wonders", pid, w))
    for cid, charm in CHARM_REGISTRY.items():
        lines.append(asp.fact("charm", cid))
        if cid == "star_map":
            lines.append(asp.fact("restores", cid, 2))
        else:
            lines.append(asp.fact("restores", cid, 1))
    return "\n".join(lines)


ASP_RULES = r"""
needs_magic(P) :- place(P).
compatible(P,C) :- needs_magic(P), charm(C), good_for(P,C).
valid(P,C) :- compatible(P,C).

good_for(lantern_field,golden_key).
good_for(lantern_field,blue_bell).
good_for(lantern_field,star_map).
good_for(moon_well,blue_bell).
good_for(moon_well,star_map).
good_for(windmill_hill,golden_key).
good_for(windmill_hill,star_map).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid_pairs() -> list[tuple]:
    return sorted((p, c) for p in PLACE_REGISTRY for c in CHARM_REGISTRY if reasonableness_gate(PLACE_REGISTRY[p], CHARM_REGISTRY[c]))


def asp_verify() -> int:
    a, b = set(asp_valid_pairs()), set(python_valid_pairs())
    if a == b:
        print(f"OK: clingo gate matches python gate ({len(a)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale magic storyworld: a place lacks magic until a charm helps.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--charm", choices=CHARM_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["girl", "boy"])
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
    pairs = python_valid_pairs()
    if args.place and args.charm:
        if (args.place, args.charm) not in pairs:
            raise StoryError("(No valid magical fix matches the given place and charm.)")
    pairs = [(p, c) for p, c in pairs if (not args.place or p == args.place) and (not args.charm or c == args.charm)]
    if not pairs:
        raise StoryError("(No valid combination matches the given options.)")
    place, charm = rng.choice(sorted(pairs))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(place=place, charm=charm, hero_name=name, hero_type=gender, helper_type=helper)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def generate(params: StoryParams) -> StorySample:
    place = PLACE_REGISTRY[params.place]
    charm = CHARM_REGISTRY[params.charm]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label="the helper"))
    item = world.add(Entity(id=charm.id, type="charm", label=charm.label, phrase=charm.phrase, owner=hero.id, caretaker=helper.id))
    place_magic = 0.0

    world.say(f"Folks said the {place.label.removeprefix('the ')} was so old it could remember when the moon wore boots.")
    world.say(f"But on that day, the place lacked magic, and everybody in sight could feel the lack in their toes.")
    world.say(f"{hero.id} was a {_article(params.hero_type)} {random.choice(TRAITS)} {params.hero_type} who asked, 'What happened to the magic?'")
    world.para()
    world.say(f"{hero.id} wanted the {place.label.removeprefix('the ')} to sparkle again, so {hero.pronoun()} searched for {item.phrase}.")
    world.say(f"The helper pointed to {item.phrase} and said, 'What if we carry it to the right place and let it do its work?'")
    world.para()
    if not reasonableness_gate(place, charm):
        raise StoryError("(This tale cannot resolve: the chosen charm does not fit the place.)")
    world.place_magic += charm.restores
    if world.place_magic >= MAGIC_THRESHOLD:
        world.say(f"They carried {item.phrase} to {place.label}, and the air gave a bright little shiver.")
        world.say(f"At once, the place had magic again; even the shadows danced like kittens on a fence.")
    else:
        world.say(f"They carried {item.phrase} to {place.label}, but the magic only woke halfway and blinked like a sleepy star.")
    world.facts.update(place=place, charm=charm, hero=hero, helper=helper, resolved=world.place_magic >= MAGIC_THRESHOLD)
    story = world.render()
    prompts = [
        f'Write a tall-tale for children about a place that has a "lack" of Magic and someone asking "what" to do.',
        f"Tell a magical story where {hero.id} asks what happened when {place.label} lacks magic.",
        f'Write a short story that uses the words "lack" and "what" and ends with magic returning.',
    ]
    story_qa = [
        QAItem(
            question=f"What did {hero.id} ask about the place?",
            answer=f"{hero.id} asked what happened to the magic, because the {place.label.removeprefix('the ')} lacked magic and felt plain and quiet.",
        ),
        QAItem(
            question=f"Why did the helper carry {item.label} to {place.label}?",
            answer=f"The helper carried {item.phrase} there because it was the charm that could bring back the missing magic for this place.",
        ),
    ]
    if world.place_magic >= MAGIC_THRESHOLD:
        story_qa.append(QAItem(
            question=f"What changed after they used the charm?",
            answer=f"The place had magic again, and the whole {place.label.removeprefix('the ')} seemed to wake up and sparkle.",
        ))
    world_qa = [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special kind of wonder that can make impossible things happen, like a dull place sparkling or a quiet object waking up.",
        ),
        QAItem(
            question="What does it mean when something lacks something?",
            answer="If something lacks something, it does not have enough of it, so it feels empty or missing that part.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        print(f"place_magic={sample.world.place_magic}")
    if qa:
        print()
        for section, items in [("prompts", sample.prompts), ("story_qa", sample.story_qa), ("world_qa", sample.world_qa)]:
            print(section + ":")
            if section == "prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible (place, charm) pairs:\n")
        for p, c in pairs:
            print(f"  {p:14} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in PLACE_REGISTRY:
            for c in CHARM_REGISTRY:
                if (p, c) in python_valid_pairs():
                    params = StoryParams(place=p, charm=c, hero_name="Milo", hero_type="boy", helper_type="girl", seed=base_seed)
                    samples.append(generate(params))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
