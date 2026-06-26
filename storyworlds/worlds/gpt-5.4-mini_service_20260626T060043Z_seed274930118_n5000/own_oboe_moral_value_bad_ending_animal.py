#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/own_oboe_moral_value_bad_ending_animal.py
===============================================================================================================

A small animal story world with a moral-value turn and a bad ending.

Premise:
- A clever animal wants to play a shiny oboe that belongs to someone else.
- The owner says no and asks for care and permission.

Tension:
- The wanting animal tries to take the oboe anyway.
- The instrument is fragile, loud, and easy to crack.

Turn:
- A gentle helper suggests using the animal's own practice stick first.
- But the main character chooses pride over patience.

Resolution:
- The oboe gets damaged.
- The friendship does not fully recover, so the ending is sad and the moral is explicit.

The world is intentionally narrow: only a few plausible story variants exist,
and invalid combinations are rejected with clear reasons.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    borrowed_from: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen", "duck"}
        male = {"boy", "father", "man", "rooster", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    noisy: bool = False


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    harm: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    animal: str
    animal_type: str
    owner: str
    owner_type: str
    object_id: str
    seed: Optional[int] = None


SETTINGS = {
    "barn": Setting(place="the barn", affords={"own", "oboe"}),
    "meadow": Setting(place="the meadow", affords={"own"}),
    "music_room": Setting(place="the music room", affords={"oboe"}),
}

ANIMALS = {
    "fox": ("fox", "clever", "sly"),
    "rabbit": ("rabbit", "quick", "restless"),
    "crow": ("crow", "curious", "glossy"),
    "cat": ("cat", "proud", "careful"),
    "dog": ("dog", "eager", "bouncy"),
}

OBJECTS = {
    "oboe": ObjectItem(
        id="oboe",
        label="oboe",
        phrase="a shiny wooden oboe with silver keys",
        fragile=True,
        noisy=True,
    ),
    "own_toy": ObjectItem(
        id="own_toy",
        label="own toy",
        phrase="an own practice reed",
        fragile=False,
        noisy=False,
    ),
}

ACTIONS = {
    "own": Action(
        id="own",
        verb="keep it for themself",
        gerund="keeping it close",
        rush="snatch it first",
        risk="greedy and unfair",
        harm="lost trust",
        keyword="own",
        tags={"moral", "own"},
    ),
    "oboe": Action(
        id="oboe",
        verb="play the oboe",
        gerund="blowing the oboe",
        rush="grab the oboe",
        risk="too loud and too rough",
        harm="cracked the oboe",
        keyword="oboe",
        tags={"moral", "oboe"},
    ),
}

CURATED = [
    StoryParams(place="barn", animal="fox", animal_type="fox", owner="cat", owner_type="cat", object_id="oboe"),
    StoryParams(place="music_room", animal="crow", animal_type="crow", owner="dog", owner_type="dog", object_id="oboe"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal moral-value story world with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--owner", choices=ANIMALS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.animal == params.owner:
        raise StoryError("The story needs two different animals: one who wants, and one who owns the oboe.")
    if params.object_id != "oboe":
        raise StoryError("This world only supports the oboe as the fragile borrowed object.")
    if params.place not in {"barn", "music_room"}:
        raise StoryError("The story needs a place where the oboe can be present.")
    if params.place == "meadow":
        raise StoryError("The meadow is too empty for an oboe story; there is nothing to borrow there.")


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for animal in ANIMALS:
            for owner in ANIMALS:
                if animal == owner:
                    continue
                if place in {"barn", "music_room"}:
                    out.append((place, animal, owner))
    return out


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.place]
    world = World(setting)

    animal_type, animal_trait, animal_style = ANIMALS[params.animal]
    owner_type, owner_trait, owner_style = ANIMALS[params.owner]
    hero = world.add(Entity(id=params.animal, kind="character", type=animal_type))
    owner = world.add(Entity(id=params.owner, kind="character", type=owner_type))
    oboe = world.add(Entity(
        id="oboe",
        type="oboe",
        label="oboe",
        phrase=OBJECTS["oboe"].phrase,
        owner=owner.id,
    ))
    own_item = world.add(Entity(
        id="own_reed",
        type="reed",
        label="own reed",
        phrase=OBJECTS["own_toy"].phrase,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, owner=owner, oboe=oboe, own_item=own_item, setting=setting)

    world.say(f"At {setting.place}, a {animal_trait} {hero.type} named {hero.id} watched {owner.id} polish an oboe.")
    world.say(f"{hero.id} liked {hero.pronoun('possessive')} own reed, but {hero.id} wanted the bright oboe too.")
    world.say(f"{owner.id} said the oboe was fragile and had to stay safe unless it was shared kindly.")

    world.para()
    hero.meme["desire"] = 1.0
    owner.meme["care"] = 1.0
    world.say(f"One day, {hero.id} heard music drift through {setting.place} and wanted to {ACTIONS['oboe'].verb}.")
    world.say(f"{owner.id} warned that the oboe could crack if someone was {ACTIONS['oboe'].risk}.")
    world.say(f"{hero.id} reached anyway, because {hero.id} was feeling proud and did not want to wait.")

    world.para()
    hero.meme["defiance"] = 1.0
    oboe.meter["stress"] = 1.0
    oboe.meter["damage"] = 1.0
    owner.meme["hurt"] = 1.0
    world.say(f"{hero.id} tried to {ACTIONS['oboe'].rush}, and the oboe slipped and gave a sharp squeak.")
    world.say(f"The tiny jolt left a crack in the oboe and a sad look on {owner.id}'s face.")
    world.say(f"Now {hero.id} had {ACTIONS['own'].harm}, because {hero.id} had not asked first.")

    world.para()
    world.say(f"A small helper said the moral: take care of your own things, and ask before touching someone else's.")
    world.say(f"But the day still ended badly: {owner.id} took the cracked oboe away, and {hero.id} went home quiet.")
    world.say(f"{hero.id}'s own reed was still safe, but the trust between them was not.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    owner = f["owner"]
    return [
        f"Write an animal story with a moral value lesson about {hero.id} wanting an oboe that belongs to {owner.id}.",
        "Tell a short story where an animal wants someone else's instrument, makes a bad choice, and learns too late.",
        "Write a child-facing animal story that includes the words own and oboe and ends sadly with a clear moral.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    owner = f["owner"]
    oboe = f["oboe"]
    return [
        QAItem(
            question=f"Who wanted the oboe in the story?",
            answer=f"{hero.id} wanted the oboe even though it belonged to {owner.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} already have that stayed safe?",
            answer=f"{hero.id} had an own reed, and it stayed safe even when the oboe was damaged.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer="The ending was bad because the animal took the oboe without asking, cracked it, and hurt the owner's trust.",
        ),
        QAItem(
            question=f"What happened to the oboe?",
            answer=f"The oboe got a crack after {hero.id} grabbed it too quickly.",
        ),
        QAItem(
            question="What moral did the helper say?",
            answer="The helper said to take care of your own things and ask before touching someone else's.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an oboe?",
            answer="An oboe is a woodwind instrument that you play by blowing into it, and it can make a clear, reedy sound.",
        ),
        QAItem(
            question="Why should you ask before using someone else's things?",
            answer="You should ask because the other person owns them, may not want them touched, and may worry about them getting broken.",
        ),
        QAItem(
            question="What does own mean?",
            answer="Own means something belongs to you.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meter={dict(e.meter)} meme={dict(e.meme)} owner={e.owner}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,O) :- place(P), animal(A), animal(O), A != O, place_ok(P).
place_ok(barn).
place_ok(music_room).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for o in ANIMALS:
        lines.append(asp.fact("animal", o))
    for p in {"barn", "music_room"}:
        lines.append(asp.fact("place_ok", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print("only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("only in asp:", sorted(asp_set - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object_id and args.object_id != "oboe":
        raise StoryError("This world only supports the oboe.")
    if args.place == "meadow" and not args.all:
        raise StoryError("The meadow cannot host this oboe conflict.")
    combos = valid_combos()
    combos = [c for c in combos if args.place is None or c[0] == args.place]
    combos = [c for c in combos if args.animal is None or c[1] == args.animal]
    combos = [c for c in combos if args.owner is None or c[2] == args.owner]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, animal, owner = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        animal=animal,
        animal_type=ANIMALS[animal][0],
        owner=owner,
        owner_type=ANIMALS[owner][0],
        object_id="oboe",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        if args.all:
            p = sample.params
            header = f"### {p.animal} vs {p.owner} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
