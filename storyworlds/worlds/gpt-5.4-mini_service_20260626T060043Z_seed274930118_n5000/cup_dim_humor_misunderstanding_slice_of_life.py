#!/usr/bin/env python3
"""
storyworlds/worlds/cup_dim_humor_misunderstanding_slice_of_life.py
==================================================================

A small slice-of-life story world about a child, a cup, a dim room, and a
humorous misunderstanding.

Seed idea:
---
A child notices that a favorite cup looks dim and cloudy on the kitchen shelf.
A parent misunderstands the complaint and thinks the child is talking about the
lamp being too dim. After a few funny back-and-forth lines, they discover the
child just wants the cup cleaned and ready for cocoa.

World model:
---
- The child has desires, embarrassment, and delight.
- The cup has physical cleanliness, brightness, and ownership.
- The room has light and a cozy feeling.
- The parent has attention, concern, and a tendency to misread the first clue.

This script keeps the stories small and grounded in ordinary home life.
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
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    light: str
    cozy: bool = True


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    mess: str
    condition: str
    cleanup: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    object: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "kitchen": Setting(place="the kitchen", light="dim"),
    "dining_room": Setting(place="the dining room", light="soft"),
    "sunroom": Setting(place="the sunroom", light="bright"),
}

OBJECTS = {
    "cup": ObjectConfig(
        id="cup",
        label="cup",
        phrase="a favorite little cup with a blue rim",
        mess="cloudy",
        condition="dim and cloudy",
        cleanup="wipe and polish",
        tags={"cup", "clean", "glass"},
    ),
    "mug": ObjectConfig(
        id="mug",
        label="mug",
        phrase="a cheerful mug with a painted fox",
        mess="smudged",
        condition="smudged and dull",
        cleanup="rinse and dry",
        tags={"cup", "mug", "dish"},
    ),
    "glass": ObjectConfig(
        id="glass",
        label="glass",
        phrase="a small glass with a wavy line",
        mess="fingerprinted",
        condition="fingerprinted",
        cleanup="wash and shine",
        tags={"glass", "clean"},
    ),
}

CHILDREN = [
    ("Mia", "girl"),
    ("Leo", "boy"),
    ("Nina", "girl"),
    ("Finn", "boy"),
    ("Ava", "girl"),
    ("Owen", "boy"),
]

PARENTS = ["mother", "father"]

TRAITS = ["curious", "gentle", "cheerful", "impatient", "thoughtful"]

ASP_RULES = r"""
% The object is at risk when the room is dim and the child wants it cleaned for use.
at_risk(O) :- object(O), room_dim, needs_use(O).

% A useful fix is any cleanup plan that actually matches the object's kind of mess.
fixable(O) :- at_risk(O), cleanup_for(O,_).

% A valid story needs a misunderstanding, an at-risk object, and a real fix.
valid_story(S, O) :- setting(S), object(O), at_risk(O), fixable(O), misunderstanding.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.light == "dim":
            lines.append(asp.fact("room_dim"))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("needs_use", oid))
        lines.append(asp.fact("cleanup_for", oid, o.cleanup.replace(" ", "_")))
    lines.append(asp.fact("misunderstanding"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_stories() ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a dim cup and a funny misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.name is None:
        pass
    name = args.name or rng.choice([n for n, g in CHILDREN if g == gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(setting=setting, object=obj, child_name=name, child_gender=gender, parent_type=parent)


def _do_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    obj_cfg = OBJECTS[params.object]
    cup = world.add(
        Entity(
            id=obj_cfg.id,
            type=obj_cfg.id,
            label=obj_cfg.label,
            phrase=obj_cfg.phrase,
            owner=child.id,
            caretaker=parent.id,
        )
    )
    child.memes["curiosity"] = 1
    cup.meters["clean"] = 0.2
    cup.meters["dimness"] = 1.0 if world.setting.light == "dim" else 0.3

    world.say(f"{child.id} was a {random.choice(TRAITS)} little {child.pronoun('possessive')} parent liked to call careful with things.")
    world.say(f"In {world.setting.place}, {cup.phrase} sat on the shelf and looked {obj_cfg.condition}.")
    world.say(f"{child.id} wanted to use {cup.label} for cocoa, but the cup looked almost lost in the {world.setting.light} light.")
    world.para()
    world.say(f'“The cup is dim,” {child.id} said, peering up at the shelf.')
    world.say(f'{parent.id} looked around at the lamp and blinked. “The room is dim?” {parent.pronoun("subject").capitalize()} asked.')
    parent.memes["confusion"] = 1
    child.memes["embarrassment"] = 1
    world.say(f'{child.id} shook {child.pronoun("possessive")} head. “No, not the room. The cup.”')
    world.say(f'That made {parent.id} laugh, because for one tiny second {parent.pronoun("subject")} had started hunting for a light switch instead of a towel.')
    world.para()
    cup.meters["clean"] = 1.0
    cup.meters["shiny"] = 1.0
    child.memes["joy"] = 1
    parent.memes["warmth"] = 1
    world.say(f'{parent.id} found a soft cloth, and together they {obj_cfg.cleanup} {cup.label}.')
    world.say(f'When the cup came back bright, {child.id} smiled and poured cocoa into it.')
    world.say(f'In the cozy kitchen, the little {cup.label} looked ready for an ordinary, happy evening.')
    world.facts.update(child=child, parent=parent, cup=cup, obj_cfg=obj_cfg)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cup = f["cup"]
    return [
        f'Write a short slice-of-life story for a child named {child.id} about a dim {cup.label} and a funny misunderstanding.',
        f'Tell a gentle home story where {child.id} says the {cup.label} is dim and {child.id.lower() if False else "a parent"} misunderstands at first.',
        f'Write a cozy story about cleaning {cup.label} after someone mistakes "dim" for the whole room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cup = f["cup"]
    obj_cfg = f["obj_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} notice in the kitchen?",
            answer=f"{child.id} noticed that the {cup.label} looked {obj_cfg.condition} on the shelf.",
        ),
        QAItem(
            question=f"Why did {parent.id} laugh?",
            answer=f"{parent.id} laughed because {child.id} meant the {cup.label} was dim, but the first clue sounded like the whole room needed fixing.",
        ),
        QAItem(
            question=f"What did they do to the {cup.label} in the end?",
            answer=f"They {obj_cfg.cleanup} it until it was bright again, and then {child.id} could use it for cocoa.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dim light mean?",
            answer="Dim light is soft, low light that is not very bright.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people first think someone means one thing, but the person means something else.",
        ),
        QAItem(
            question="Why do people clean cups?",
            answer="People clean cups so they can use them safely for drinks and so they look nice again.",
        ),
    ]


def valid_stories() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        for o in OBJECTS:
            out.append((s, o))
    return out


def generate(params: StoryParams) -> StorySample:
    world = _do_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
    return "\n".join(lines)


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
    StoryParams(setting="kitchen", object="cup", child_name="Mia", child_gender="girl", parent_type="mother"),
    StoryParams(setting="dining_room", object="mug", child_name="Leo", child_gender="boy", parent_type="father"),
    StoryParams(setting="sunroom", object="glass", child_name="Ava", child_gender="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s, o in stories:
            print(f"  {s:12} {o}")
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
            header = f"### {p.child_name}: {p.object} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
