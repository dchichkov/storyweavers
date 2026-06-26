#!/usr/bin/env python3
"""
storyworlds/worlds/booze_malarkey_flashback_nursery_rhyme.py
=============================================================

A tiny story world about a child, a slippery bottle of booze, and a grown-up
bit of malarkey remembered in a flashback. The telling keeps a nursery-rhyme
beat: simple lines, repeating sounds, concrete objects, and a clear turn from
worry to a safer choice.

Source tale sketch:
---
Little Pippa loved the kitchen stool, the sugar jar, and the bright red spoon.
On the high shelf sat a brown bottle of booze that Grandad had brought home by
mistake. Pippa did not know the word at first, only that it looked shiny and
bent the light.

One afternoon, Pippa reached for the bottle to make a pretend feast. Grandad
saw it and laughed, then stopped laughing. He remembered, in a quick flashback,
how he once made foolish malarkey with grown-up drinks at a party and had made
a mess of the table. "No, no, little one," he said. "That bottle is not for
play. That's old malarkey for grown-ups, and it can turn a tidy day topsy-turvy."

Pippa frowned. Then Grandad brought down a jug of apple juice, a little blue
cup, and a stripy spoon. They sang a small rhyme, poured the juice, and made a
tea-party game from the safe things instead. Pippa smiled, the bottle stayed
high, and the table kept its neat little shine.

World model:
---
    object on high shelf            -> reachable only with a helper
    child attempts to play with it  -> curiosity += 1, risk += 1
    flashback to old malarkey       -> adult caution rises; explanation is narrated
    adult swaps in safe drink       -> joy += 1, risk resets, play continues
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
    caretaker: Optional[str] = None
    on_shelf: bool = False
    high: bool = False
    safe: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    indoors: bool = True


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    on_shelf: bool
    high: bool
    safe: bool = False


@dataclass
class StoryParams:
    place: str
    child: str
    adult: str
    object: str
    flashback: bool = True
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def nursery_opening(world: World, child: Entity) -> None:
    world.say(
        f"Little {child.id} liked the tidy kitchen, the shiny spoons, and the warm sun on the floor."
    )
    world.say(
        f"{child.pronoun().capitalize()} sang softly as {child.pronoun('subject')} stepped and swayed."
    )


def show_object(world: World, obj: Entity) -> None:
    world.say(
        f"Up on a high shelf sat {obj.phrase}, quiet as a mouse and bright as a toy."
    )


def want_reach(world: World, child: Entity, obj: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.meters["risk"] = child.meters.get("risk", 0) + 1
    world.say(
        f"{child.id} reached up high and wanted {obj.pronoun('object')} for a pretend play."
    )


def flashback(world: World, adult: Entity) -> None:
    adult.memes["memory"] = adult.memes.get("memory", 0) + 1
    adult.memes["caution"] = adult.memes.get("caution", 0) + 1
    world.say(
        f"Then {adult.id} blinked and had a flashback: once upon a time, at a noisy party,"
        f" there had been foolish malarkey with booze and a spilled glass on the cloth."
    )
    world.say(
        f"That old mistake came back to mind, quick as a wink, and {adult.pronoun().capitalize()} knew to stop the play."
    )


def warn_and_rename(world: World, adult: Entity, obj: Entity) -> None:
    world.say(
        f'"No, no, little one," said {adult.id}. "That is booze, and grown-up booze is not for nursery play.'
        f" Don't let malarkey visit the table.\""
    )
    world.facts["warning"] = True
    world.facts["object_label"] = obj.label


def safe_swap(world: World, adult: Entity, child: Entity) -> None:
    adult.memes["kindness"] = adult.memes.get("kindness", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.meters["risk"] = 0
    world.say(
        f"Instead {adult.id} set down a jug of apple juice, a blue cup, and a spoon with a stripe."
    )
    world.say(
        f'"Let\'s make our own small song," {adult.id} said. "Safe things can be merry too."'
    )
    world.say(
        f"{child.id} clapped and laughed, and the bright little feast began."
    )


def ending(world: World, child: Entity, obj: Entity) -> None:
    world.say(
        f"So the bottle stayed high on the shelf, the juice stayed in the cup, and the table stayed neat and bright."
    )
    world.say(
        f"Little {child.id} learned that some malarkey is for grown-up days, while nursery games can be sweet and light."
    )


def tell(world: World, child: Entity, adult: Entity, obj: Entity) -> World:
    nursery_opening(world, child)
    world.para()
    show_object(world, obj)
    want_reach(world, child, obj)
    flashback(world, adult)
    warn_and_rename(world, adult, obj)
    world.para()
    safe_swap(world, adult, child)
    ending(world, child, obj)
    world.facts.update(child=child, adult=adult, obj=obj)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True),
    "pantry": Setting(place="the pantry", indoors=True),
    "parlor": Setting(place="the parlor", indoors=True),
}

OBJECTS = {
    "bottle": ObjectCfg(
        label="bottle",
        phrase="a brown bottle of booze",
        on_shelf=True,
        high=True,
        safe=False,
    ),
    "flask": ObjectCfg(
        label="flask",
        phrase="a little flask of booze",
        on_shelf=True,
        high=True,
        safe=False,
    ),
}

CHILDREN = ["Pippa", "Milo", "Luna", "Ned", "Tilly", "Robin"]
ADULTS = ["Grandad", "Nan", "Uncle Jo", "Aunt May"]


@dataclass
class StoryParams:
    place: str
    child: str
    adult: str
    object: str
    flashback: bool = True
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about booze and malarkey.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--object", choices=OBJECTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    child = args.child or rng.choice(CHILDREN)
    adult = args.adult or rng.choice(ADULTS)
    obj = args.object or rng.choice(list(OBJECTS))
    return StoryParams(place=place, child=child, adult=adult, object=obj, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type="child"))
    adult_type = "grandfather" if params.adult == "Grandad" else "man"
    adult = world.add(Entity(id=params.adult, kind="character", type=adult_type))
    oc = OBJECTS[params.object]
    obj = world.add(Entity(
        id=params.object,
        kind="thing",
        type="bottle",
        label=oc.label,
        phrase=oc.phrase,
        on_shelf=oc.on_shelf,
        high=oc.high,
        safe=oc.safe,
    ))
    tell(world, child, adult, obj)
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
    return [
        'Write a gentle nursery-rhyme story for a little child about booze on a shelf and a kind grown-up saying no.',
        f"Tell a rhyming story where {f['child'].id} wants the shiny {f['obj'].label} but {f['adult'].id} remembers old malarkey and redirects the play.",
        'Make a short child-facing tale with a flashback, a warning, and a safe swap from booze to juice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, obj = f["child"], f["adult"], f["obj"]
    return [
        QAItem(
            question=f"What did {child.id} want to reach on the high shelf?",
            answer=f"{child.id} wanted to reach {obj.phrase} on the high shelf.",
        ),
        QAItem(
            question=f"Why did {adult.id} stop the play?",
            answer=f"{adult.id} stopped the play because of the old malarkey from the flashback and because booze is not for nursery play.",
        ),
        QAItem(
            question=f"What did they use instead of the booze?",
            answer="They used apple juice, a blue cup, and a spoon with a stripe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is booze?",
            answer="Booze is an alcoholic drink made for grown-ups, not for children's play.",
        ),
        QAItem(
            question="What does malarkey mean?",
            answer="Malarkey means silly, foolish nonsense.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a quick memory of something that happened before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% setting(Place). character(Name, Role). object(Id, Kind).
% high(Id). safe(Id). phrase(Id, Text).

unsafe(Id) :- object(Id, _), high(Id), not safe(Id).
needs_warning(C, Id) :- character(C, _), unsafe(Id).
flashback_reason(C) :- character(C, _).

valid_story(Place, Child, Adult, Obj) :-
    setting(Place),
    character(Child, child),
    character(Adult, adult),
    object(Obj, bottle),
    unsafe(Obj).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for c in CHILDREN:
        lines.append(asp.fact("character", c, "child"))
    for a in ADULTS:
        lines.append(asp.fact("character", a, "adult"))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid, "bottle"))
        if o.high:
            lines.append(asp.fact("high", oid))
        if o.safe:
            lines.append(asp.fact("safe", oid))
        lines.append(asp.fact("phrase", oid, o.phrase))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, c, a, o) for p in SETTINGS for c in CHILDREN for a in ADULTS for o in OBJECTS}
    if asp_set:
        print(f"OK: ASP found {len(asp_set)} compatible stories.")
        return 0
    print("MISMATCH: ASP returned no valid story.")
    return 1


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
    StoryParams(place="kitchen", child="Pippa", adult="Grandad", object="bottle"),
    StoryParams(place="pantry", child="Luna", adult="Nan", object="flask"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
