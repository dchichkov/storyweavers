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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "clerk"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the post office"


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    clue: str
    hidden_in: str


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    object_id: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


OBJECTS = {
    "parcel": ObjectItem(
        id="parcel",
        label="parcel",
        phrase="a brown parcel with a blue ribbon",
        clue="blue ribbon",
        hidden_in="the sorting cart",
    ),
    "letter": ObjectItem(
        id="letter",
        label="letter",
        phrase="a small letter in a red envelope",
        clue="red envelope",
        hidden_in="the mail tray",
    ),
    "stamp_book": ObjectItem(
        id="stamp_book",
        label="stamp book",
        phrase="a tiny stamp book with a gold star",
        clue="gold star",
        hidden_in="the stamp drawer",
    ),
}

NAMES = ["Mina", "Owen", "Tia", "Noah", "Iris", "Leo", "Ruby", "Eli"]
TRAITS = ["curious", "careful", "brave", "quiet", "patient", "alert"]


def _hero_name(params: StoryParams) -> str:
    return params.name


def tell(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    clerk = world.add(Entity(id="Clerk", kind="character", type="clerk"))
    item = world.add(Entity(id=params.object_id, type=params.object_id, label=OBJECTS[params.object_id].label))
    hero.memes["curiosity"] = 1.0
    parent.memes["worry"] = 1.0
    clerk.memes["calm"] = 1.0

    world.say(
        f"On a gray morning, {_hero_name(params)} and {parent.pronoun('possessive')} {parent.type} went to {world.setting.place} to get a {item.label}."
    )
    world.say(
        f"{_hero_name(params)} had noticed a strange clue there before: {OBJECTS[params.object_id].clue}."
    )
    world.say(
        f'"Did you get the package?" {_hero_name(params)} asked.'
    )
    world.say(
        f'"Not yet," said the clerk. "Something small was mixed up, and now we need to find it."'
    )

    world.para()
    parent.memes["tension"] = 1.0
    world.say(
        f"The rows of mail trays looked like a tidy maze. {_hero_name(params)} whispered, "
        f'"It feels like someone hid the answer on purpose."'
    )
    world.say(
        f'The clerk shook {clerk.pronoun("possessive")} head. "I only saw the clue vanish near {OBJECTS[params.object_id].hidden_in}."'
    )
    world.say(
        f'{_hero_name(params)} and the clerk searched together, opening drawers and peeking behind labels.'
    )

    world.para()
    world.say(
        f"Then came the twist: the missing thing was not the parcel at all."
    )
    world.say(
        f'It was a note inside {OBJECTS[params.object_id].hidden_in}, and the note said, "Sorry for the mix-up. I took the parcel by mistake and put it back."'
    )
    parent.memes["surprise"] = 1.0
    clerk.memes["relief"] = 1.0
    world.say(
        f'"So it was an honest mistake," said {_hero_name(params)} softly.'
    )
    world.say(
        f'"Yes," said the clerk. "And mistakes can be fixed when people talk."'
    )

    world.para()
    hero.memes["understanding"] = 1.0
    parent.memes["softness"] = 1.0
    world.say(
        f'{_hero_name(params)} nodded, then turned to the clerk. "I am sorry I blamed you so fast."'
    )
    world.say(
        f'"And I am sorry I sounded grumpy," said the clerk. "Thank you for helping."'
    )
    world.say(
        f'At last, the {item.label} was handed over, and the little mystery ended with warm smiles beside the counter.'
    )

    world.facts.update(hero=hero, parent=parent, clerk=clerk, item=item, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short mystery story for a child about a trip to the post office that includes the word "get".',
        f"Tell a gentle dialogue mystery where {p.name} goes to the post office to get a {world.facts['item'].label} and a mix-up gets solved.",
        f"Write a story with a twist, a reconciliation, and a few lines of dialogue in a post office.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    item = world.facts["item"]
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    clerk = world.facts["clerk"]
    return [
        QAItem(
            question=f"Why did {hero.id} go to the post office?",
            answer=f"{hero.id} went there to get a {item.label} and find out why it seemed to be missing."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the missing thing was not the parcel itself; it was a note hidden with the mail that explained the mix-up."
        ),
        QAItem(
            question=f"How did {hero.id}, {parent.pronoun('possessive')} {parent.type}, and the clerk reconcile?",
            answer=f"They apologized to one another, spoke kindly, and worked together until the mistake was fixed."
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was the {OBJECTS[p.object_id].clue}, which led them to the hidden item."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a post office for?",
            answer="A post office is a place where people send and receive mail, letters, and parcels."
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery."
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make up after a disagreement and feel friendly again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("\n== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


ASP_RULES = r"""
% Facts:
% setting(post_office).
% clue(Item, Clue).
% hidden_in(Item, Place).
% get_goal(Hero, Item).
% talk(Hero, Clerk).

mystery(Item) :- clue(Item, _), hidden_in(Item, _).
solved(Item) :- clue(Item, C), found(C), mystery(Item).
reconcile(Hero, Clerk) :- apologize(Hero, Clerk), apologize(Clerk, Hero).
twist(Item) :- solved(Item), note_inside(Item).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "post_office")]
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("item", oid))
        lines.append(asp.fact("clue", oid, obj.clue))
        lines.append(asp.fact("hidden_in", oid, obj.hidden_in))
    lines.append(asp.fact("get_goal", "hero", "parcel"))
    lines.append(asp.fact("talk", "hero", "clerk"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    program = asp_program("#show mystery/1.\n#show solved/1.\n#show reconcile/2.\n#show twist/1.")
    model = asp.one_model(program)
    if not model:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP rules parse and produce a model.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A post-office mystery storyworld with dialogue, a twist, and reconciliation.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "mother", "father"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--trait", choices=TRAITS, default=None)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    object_id = args.object_id or rng.choice(list(OBJECTS))
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, object_id=object_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery/1.\n#show solved/1.\n#show reconcile/2.\n#show twist/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    if args.all:
        params_list = [
            StoryParams(name="Mina", gender="girl", parent="mother", trait="curious", object_id="parcel"),
            StoryParams(name="Leo", gender="boy", parent="father", trait="alert", object_id="letter"),
            StoryParams(name="Iris", gender="girl", parent="mother", trait="patient", object_id="stamp_book"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
