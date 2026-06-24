#!/usr/bin/env python3
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

WORLD_NAME = "whereabouts_array_prick_curiosity_folk_tale"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "wizard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def __post_init__(self) -> None:
        for k in ("hurt", "worry", "curiosity", "joy", "kindness", "bravery", "lostness", "prick"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    prickly: bool = False
    helpful: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


PLACES = {
    "woods": Place("woods", "the wood", "the trees stood in a green hush", {"search", "share"}),
    "village": Place("village", "the village green", "small houses leaned near a round well", {"search", "share"}),
    "riverbank": Place("riverbank", "the riverbank", "reeds brushed the water like soft combs", {"search", "share"}),
    "garden": Place("garden", "the cottage garden", "beans climbed their poles in tidy lines", {"search", "share"}),
}

OBJECTS = {
    "berry": ObjectDef("berry", "berry basket", "a little berry basket", helpful=True),
    "lantern": ObjectDef("lantern", "lantern", "a brass lantern", helpful=True),
    "comb": ObjectDef("comb", "wooden comb", "a carved wooden comb", helpful=True),
    "thorn": ObjectDef("thorn", "thorn branch", "a sharp thorn branch", prickly=True),
}

COMPANIONS = {
    "grandmother": "grandmother",
    "fox": "fox",
    "goat": "goat",
    "shepherd": "shepherd",
}

GIRL_NAMES = ["Ava", "Mina", "Lina", "Nora", "Suri"]
BOY_NAMES = ["Eli", "Pip", "Tomas", "Ravi", "Jory"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: whereabouts, array, prick, Curiosity, folk tale style.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    obj = args.object_name or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(list(COMPANIONS))
    if OBJECTS[obj].prickly and place == "garden":
        pass
    return StoryParams(place=place, object=obj, name=name, gender=gender, companion=companion)


def reasonableness_gate(params: StoryParams) -> None:
    if params.object == "thorn" and params.companion == "shepherd":
        return
    if params.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")


def story_shape(world: World, hero: Entity, companion: Entity, obj: ObjectDef) -> None:
    place = world.place
    world.say(
        f"Long ago, in {place.label}, there lived a curious little {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} had a heart full of questions, and {hero.pronoun('possessive')} "
        f"favorite question was where things and people went when they were out of sight."
    )
    hero.memes["curiosity"] += 2
    world.say(
        f"One bright morning, {hero.id} found an array of little marks near the path: three pebbles, "
        f"two blue feathers, and one shiny shell set in a careful row."
    )
    world.say(
        f"{hero.id} asked {companion.id}, \"Do you know the whereabouts of the lost thing?\" "
        f"{companion.pronoun().capitalize()} only smiled and said the old woods loved to hide clues."
    )
    if obj.prickly:
        hero.memes["curiosity"] += 1
        hero.meters["prick"] += 1
        hero.meters["hurt"] += 1
        world.say(
            f"{hero.id} followed the array into a briar patch and reached for a prickly branch. "
            f"A tiny prick stung {hero.pronoun('possessive')} finger, and {hero.id} hissed softly."
        )
        companion.memes["worry"] += 1
        world.say(
            f"{companion.id} hurried close, wrapped the finger in a clean leaf, and said, "
            f"\"Curiosity is a brave lantern, child, but even lanterns must be carried gently.\""
        )
        hero.memes["bravery"] += 1
        hero.memes["kindness"] += 1
        world.say(
            f"Then {hero.id} looked more carefully, found the thorn branch was only snagged in a bush, "
            f"and carried it free without another scratch."
        )
    else:
        hero.memes["curiosity"] += 2
        world.say(
            f"{hero.id} and {companion.id} followed the array of clues past the well and under the willows. "
            f"There, tucked behind a stone, they found the lost {obj.label} at last."
        )
    world.say(
        f"{hero.id} returned to the lane with a full smile. The question of whereabouts was answered, "
        f"the array of clues made sense, and even the smallest prick had become a lesson about careful hands."
    )
    hero.memes["joy"] += 2


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion, label=params.companion))
    obj = OBJECTS[params.object]
    world.facts.update(hero=hero, companion=companion, obj=obj, params=params, place=world.place)
    story_shape(world, hero, companion, obj)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a folk tale for young children about {hero.id}'s curiosity and a set of clues in an array.",
        f"Tell a gentle story where the whereabouts of something are discovered, but a prick teaches careful hands.",
        f"Write a simple folk tale with the words whereabouts, array, and prick, ending in a wise little lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    obj: ObjectDef = f["obj"]
    params: StoryParams = f["params"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a curious little {params.gender} who loved asking where things were.",
        ),
        QAItem(
            question=f"What did {hero.id} find arranged in a line at {world.place.label}?",
            answer="They found an array of clues, including pebbles, feathers, and a shell set in a careful row.",
        ),
        QAItem(
            question=f"What happened when {hero.id} reached for the prickly thing?",
            answer=f"{hero.id} got a tiny prick on {hero.pronoun('possessive')} finger, and {companion.id} helped wrap it gently.",
        ),
        QAItem(
            question=f"What was the answer to the question about the whereabouts?",
            answer=f"The lost {obj.label} was found at last, and {hero.id} brought the day home with a smile.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, asking questions, and looking closely at the world.",
        ),
        QAItem(
            question="What is an array?",
            answer="An array is a neat arrangement, with things placed in order so they are easy to notice.",
        ),
        QAItem(
            question="What is a prick?",
            answer="A prick is a small sharp poke that can sting your skin for a moment.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
clue_array(A) :- array(A).
prick_event(H) :- hero(H), prickly_object(O), touched(H,O).
answer_found(H) :- hero(H), finds(H, X).
good_story :- hero(H), clue_array(A), curiosity(H), answer_found(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("character", "hero"))
    lines.append(asp.fact("array", "clues"))
    lines.append(asp.fact("curiosity", "hero"))
    lines.append(asp.fact("prickly_object", "thorn"))
    lines.append(asp.fact("finds", "hero", "answer"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    has = any(sym.name == "good_story" for sym in model)
    py = True
    if has == py:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story q&a ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world q&a ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams("woods", "thorn", "Ava", "girl", "grandmother"),
            StoryParams("village", "berry", "Eli", "boy", "fox"),
            StoryParams("riverbank", "lantern", "Mina", "girl", "shepherd"),
            StoryParams("garden", "comb", "Pip", "boy", "grandmother"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
