#!/usr/bin/env python3
"""
storyworlds/worlds/oat_conflict_rhyme_curiosity_fairy_tale.py
==============================================================

A small fairy-tale storyworld about a curious child, a conflict over oats,
and a rhyme that turns trouble into sharing.

The seed image:
---
In a little kingdom at the edge of a silver wood, a curious child found a bowl
of golden oat porridge meant for the morning feast. The child wanted to peek,
taste, and maybe keep the spoon, but the pantry fairy warned that the porridge
belonged to the whole cottage. The child grew cross. Then a gentle rhyme helped
everyone pause, laugh, and share the oats before the porridge cooled.

This world turns that seed into a tiny simulation:
- curiosity raises the wish to explore
- conflict rises when a rule is ignored
- rhyme lowers conflict and opens a fair compromise
- the ending proves the oats were shared and the mood changed
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "fairy", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "wizard", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage kitchen"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class OatThing:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    tale_effect: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class RhymeCharm:
    id: str
    label: str
    rhyme: str
    effect: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _story_seed() -> str:
    return "oat"


def _raise_if_invalid(activity: str, prize: str) -> None:
    if activity != "peek" and prize != "oat":
        raise StoryError("This world is built around oat-based curiosity and a rhyme-driven conflict.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about oat, conflict, rhyme, and curiosity.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "cottage": Setting(place="the cottage kitchen", indoors=True, affords={"peeking", "sharing"}),
    "bakery": Setting(place="the bakery hearth", indoors=True, affords={"peeking", "sharing"}),
    "wood": Setting(place="the silver wood glade", indoors=False, affords={"peeking", "sharing"}),
}

NAMES = {
    "girl": ["Mina", "Luna", "Tess", "Nora", "Faye", "Ivy"],
    "boy": ["Theo", "Robin", "Eli", "Pip", "Finn", "Niko"],
}
PARENTS = ["mother", "father", "grandmother", "grandfather"]


OAT = OatThing(
    id="oat",
    label="oat porridge",
    phrase="a bowl of golden oat porridge",
    region="table",
    mess="spilled oat",
    tale_effect="the spoon left a tiny trail of warm oats",
)

RHYME = RhymeCharm(
    id="rhyme",
    label="a little rhyme",
    rhyme="Oats are warm, and oats are kind; share the spoon and ease the mind.",
    effect="the rhyme softened the sharp feeling in the room",
    tail="the cottage felt gentle again",
)


CURATED = [
    StoryParams(place="cottage", name="Mina", gender="girl", parent="grandmother"),
    StoryParams(place="bakery", name="Theo", gender="boy", parent="mother"),
    StoryParams(place="wood", name="Ivy", gender="girl", parent="father"),
]


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("seed_word", _story_seed()))
    lines.append(asp.fact("mess", "oat"))
    lines.append(asp.fact("theme", "conflict"))
    lines.append(asp.fact("theme", "rhyme"))
    lines.append(asp.fact("theme", "curiosity"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S) :- setting(S), seed_word(oat), theme(conflict), theme(rhyme), theme(curiosity).
#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the oat conflict rhyme curiosity world.")
        return 0
    print("MISMATCH: ASP twin did not validate the world.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def _curiosity_step(hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0


def _conflict_step(hero: Entity, parent: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1.0


def _rhyme_step(hero: Entity, parent: Entity) -> None:
    hero.memes["conflict"] = max(0.0, hero.memes.get("conflict", 0.0) - 1.0)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    parent.memes["joy"] = parent.memes.get("joy", 0.0) + 1.0


def tell(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"Once in {world.setting.place}, there lived a curious little {hero.type} named {hero.id}.")
    world.say(f"{hero.pronoun().capitalize()} loved to ask questions, especially about warm things, sweet things, and oat porridge.")
    world.say(f"One morning, {parent.pronoun('possessive')} {parent.noun()} set out {OAT.phrase} for the feast.")
    hero.meters["hunger"] = 1.0
    hero.memes["curiosity"] = 1.0
    world.say(f"{hero.id} leaned close and stared at the oats. {hero.pronoun().capitalize()} wanted to peek, taste, and know every secret of the bowl.")
    world.para()
    world.say(f"But the {parent.noun()} lifted a finger and said, \"No nibbling yet. The bowl is for everyone.\"")
    _conflict_step(hero, parent)
    world.say(f"{hero.id} felt the wish to reach for the spoon, and a little storm of { 'conflict' } stirred in {hero.pronoun('possessive')} chest.")
    world.say(f"{hero.id} frowned. \"I only wanted one tiny taste,\" {hero.pronoun()} said, and {parent.pronoun()} looked worried.")
    world.para()
    world.say(f"Then a small rhyme came floating in, as if the cottage itself had learned it:")
    world.say(f"“{RHYME.rhyme}”")
    _rhyme_step(hero, parent)
    world.say(f"The words were soft and bright. They slowed the hurry in the room and made room for a kinder thought.")
    world.say(f"{hero.id} blinked, then asked to stir the oats instead of sneaking a bite.")
    hero.memes["curiosity"] += 0.5
    world.say(f"That was a better question than a grab. Together they sprinkled cinnamon, shared the spoon, and served the porridge in small shining bowls.")
    world.say(f"{RHYME.tail}. {hero.id} tasted the last spoonful and smiled because {hero.pronoun('possessive')} curiosity had found a fair answer.")
    world.facts.update(hero=hero, parent=parent, oat=OAT, rhyme=RHYME, setting=world.setting)


def generate_story_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, meters={}, memes={}))
    tell(world, hero, parent)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    return [
        f"Write a fairy tale about a curious {hero.type} who almost makes a conflict over oat porridge, then resolves it with a rhyme.",
        f"Tell a child-friendly story where {hero.id} asks too many questions about {OAT.label} and {parent.noun()} answers with kindness.",
        f"Make a short fairy tale with oat, curiosity, and rhyme, ending in a calm sharing scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    qa = [
        QAItem(
            question=f"Why was {hero.id} curious about the bowl in the cottage?",
            answer=f"{hero.id} was curious because {hero.pronoun()} loved asking questions, and the golden oat porridge looked warm and special.",
        ),
        QAItem(
            question=f"What caused the conflict between {hero.id} and the {parent.noun()}?",
            answer=f"The conflict started when {hero.id} wanted to peek and taste the oat porridge before it was time to share it.",
        ),
        QAItem(
            question="How did the conflict become peaceful again?",
            answer=f"A gentle rhyme softened the room, and then they shared the oats instead of fighting over the spoon.",
        ),
    ]
    if hero.memes.get("conflict", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel after being told not to nibble?",
                answer=f"{hero.id} felt cross at first, because the wish to taste the oats turned into a small storm of conflict.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is oat porridge?",
            answer="Oat porridge is a warm food made by cooking oats in water or milk until it turns soft and creamy.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little poem or song where the sounds at the ends of words match or feel musical.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, ask questions, and look closely at how things work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = CURATED
    else:
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            key = (p.place, p.name, p.gender, p.parent)
            i += 1
            if key in seen:
                continue
            seen.add(key)
            params_list.append(p)

    for p in params_list:
        samples.append(generate(p))

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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
