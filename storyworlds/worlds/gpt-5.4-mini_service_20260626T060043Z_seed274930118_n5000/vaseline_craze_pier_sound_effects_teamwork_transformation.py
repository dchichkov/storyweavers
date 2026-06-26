#!/usr/bin/env python3
"""
A tiny storyworld about a pier, a silly vaseline craze, sound effects,
teamwork, and a transformation.
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


@dataclass
class Setting:
    place: str = "the pier"
    scent: str = "salt"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTING = Setting(place="the pier", scent="salt")

ITEMS = {
    "hat": Item(id="hat", label="hat", phrase="a blue little hat", region="head"),
    "shoes": Item(id="shoes", label="shoes", phrase="tiny shiny shoes", region="feet", plural=True),
}

NAMES = ["Mia", "Leo", "Nina", "Owen", "Luna", "Theo"]
HELPERS = ["Old Jack", "Merry May", "Tiny Tom", "Nora the Knitter"]

ASP_RULES = r"""
#show valid/2.
valid(Name, Item) :- child(Name), prize(Item).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "pier")]
    for n in NAMES:
        lines.append(asp.fact("child", n))
    for item in ITEMS:
        lines.append(asp.fact("prize", item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(n, i) for n in NAMES for i in ITEMS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme pier storyworld.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--item", choices=ITEMS)
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
    name = args.name or rng.choice(NAMES)
    gender = args.gender or ("girl" if name in {"Mia", "Nina", "Luna"} else "boy")
    helper = args.helper or rng.choice(HELPERS)
    item = args.item or rng.choice(list(ITEMS))
    return StoryParams(name=name, gender=gender, helper=helper, item=item)


def sound(line: str) -> str:
    return line


def generate_story(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["curious"] = 1
    hero.memes["delight"] = 1
    item_owner = hero.id
    item.owner = item_owner
    item.worn_by = hero.id

    world.say(
        f"On the pier so neat, with waves below, little {hero.id} went tip-tap-toe."
        f" The boards went creak and the gulls went caw, and the salt wind gave a shiny awe."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the vaseline craze that sparkled bright; "
        f"everybody said it was silky and light."
    )
    world.say(
        f"{hero.id} wanted to smear a dab and grin, but {helper.label} said, "
        f"\"Oh dear, let's think what it means to win.\""
    )
    world.para()

    hero.memes["worry"] = 1
    world.say(
        f"At the edge of the pier, with clip-clap sound, {hero.id} saw the gulls "
        f"and the bobbing round. \"If the vaseline slips, if the wind blows spry, "
        f"my pretty {item.label} may slide-der-by!\""
    )
    world.say(
        f"Then {helper.label} came near with a kinder tone: "
        f"\"Let's do this together; you're not alone.\""
    )

    world.para()
    hero.memes["teamwork"] = 1
    helper.memes["teamwork"] = 1
    hero.meters["vaseline"] = 1
    world.say(
        f"So they worked in a pair with a careful song, "
        f"\"Pat and smooth, pat and smooth, nice and strong!\""
    )
    world.say(
        f"{helper.id} held the jar, and {hero.id} spread the cream; "
        f"the pier went swish, like a moonbeam dream."
    )
    world.say(
        f"Then something quite funny and lovely took place: "
        f"the shiny little mess became a glowing new face."
    )
    hero.memes["transformed"] = 1
    item.label = f"glossy {item.label}"
    world.say(
        f"The old craze turned gentle, and bright, and neat; "
        f"{hero.id} danced softly, clap-clap, on happy feet."
    )

    world.facts.update(hero=hero, helper=helper, item=item, setting=world.setting)


def make_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", type="helper", label=params.helper))
    item = world.add(Entity(id=params.item, type=params.item, label=params.item, phrase=ITEMS[params.item].phrase))
    generate_story(world, hero, helper, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    return [
        "Write a short nursery-rhyme story about a pier, a vaseline craze, teamwork, and a change that feels magical.",
        f"Tell a gentle story where {hero.id} and {helper.id} work together on the pier and the {item.label} ends up transformed.",
        "Make the story sound sing-song, with little sound effects like creak, swish, and clap-clap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    return [
        QAItem(
            question=f"Where did {hero.id} play in the story?",
            answer="They played on the pier by the water, where the boards creaked and the gulls cried.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} do together?",
            answer=f"They worked together carefully, patting and smoothing the vaseline so the plan would turn out well.",
        ),
        QAItem(
            question=f"What changed about the {item.label} by the end?",
            answer=f"It became a glossy little {item.label}, showing the story's bright transformation.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pier?",
            answer="A pier is a long structure that stretches out over water, with boards under your feet.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects like creak, swish, and clap-clap help the story feel lively and playful.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and share the work so they can do something together.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state into another, like plain becoming glossy or dull becoming bright.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


CURATED = [
    StoryParams(name="Mia", gender="girl", helper="Old Jack", item="hat"),
    StoryParams(name="Leo", gender="boy", helper="Merry May", item="shoes"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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
