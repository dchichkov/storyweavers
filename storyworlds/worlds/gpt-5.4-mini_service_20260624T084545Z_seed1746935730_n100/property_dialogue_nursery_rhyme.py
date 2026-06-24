#!/usr/bin/env python3
"""
storyworlds/worlds/property_dialogue_nursery_rhyme.py
======================================================

A small story world about property, gentle dialogue, and a nursery-rhyme voice.

Seed tale used to build the world:
---
In a little yard by the lane, Pip had a tiny blue cart that was his property.
He loved it very much and rolled it back and forth while he sang. One morning,
his friend Dot asked, "May I ride in your cart?" Pip wanted to say no, because
it was his property and he feared it might get scratched.

Dot looked sad. Pip's mum heard the talk and said, "What is yours is yours, but
kind words can make a plan." Pip thought for a moment. He told Dot they could
take turns, and Dot could hold the ribbon while Pip pulled the cart. Dot smiled,
and soon the two of them sang and played together, keeping the cart safe.
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
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
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
    place: str
    indoor: bool = False
    sparkle: str = ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    can_share: bool
    can_touch: bool = True
    can_borrow: bool = True


@dataclass
class Topic:
    id: str
    verb: str
    action: str
    risk: str
    repair: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def rhyme(line: str) -> str:
    return line


def launch_doubt(world: World, child: Entity, item: Entity, topic: Topic) -> None:
    child.memes["want_keep"] = child.memes.get("want_keep", 0) + 1
    world.say(
        f"{child.id} had {item.phrase}, snug and neat, "
        f"and loved to keep it close and sweet."
    )
    world.say(
        f"{child.id} wanted to {topic.verb}, but {item.label} was {child.pronoun('possessive')} property."
    )


def ask(world: World, visitor: Entity, child: Entity, topic: Topic, item: Entity) -> None:
    visitor.memes["curious"] = visitor.memes.get("curious", 0) + 1
    world.say(
        f'"May I {topic.action} your {item.label}?" asked {visitor.id} in a little sing-song way.'
    )
    world.say(
        f'"Maybe," said {child.id}, "but I must think. It is my property today."'
    )


def worry(world: World, child: Entity, visitor: Entity, item: Entity, topic: Topic) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    child.meters["care"] = child.meters.get("care", 0) + 1
    world.say(
        f"{child.id} worried it might get {topic.risk}, and that would not be merry."
    )
    world.say(
        f"{visitor.id} went quiet and stood still like a mouse by a tree."
    )


def parent_sings(world: World, parent: Entity, child: Entity, visitor: Entity, item: Entity) -> None:
    parent.memes["wise"] = parent.memes.get("wise", 0) + 1
    world.say(
        f'"What is yours is yours," said {parent.id}, "and kind words help us share."'
    )
    world.say(
        f'"No one need grab or glare; we can make a careful pair."'
    )


def fix(world: World, child: Entity, visitor: Entity, item: Entity, topic: Topic) -> None:
    child.memes["kind"] = child.memes.get("kind", 0) + 1
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    visitor.memes["joy"] = visitor.memes.get("joy", 0) + 1
    child.memes["worry"] = 0
    world.say(
        f'{child.id} thought a bit and then said, "We can take turns with care."'
    )
    world.say(
        f'"You may {topic.action} while I hold the ribbon, and we will keep it fair."'
    )
    world.say(
        f"So {visitor.id} {topic.action}ed a little while {child.id} stayed near."
    )
    world.say(
        f"The {item.label} stayed safe and bright, and both children cheered."
    )


def tell(setting: Setting, topic: Topic, item_cfg: Item, child_name: str, child_type: str,
         visitor_name: str, visitor_type: str, parent_name: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    visitor = world.add(Entity(id=visitor_name, kind="character", type=visitor_type))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.type, label=item_cfg.label,
                            phrase=item_cfg.phrase, owner=child.id, caretaker=parent.id))

    launch_doubt(world, child, item, topic)
    world.para()
    ask(world, visitor, child, topic, item)
    worry(world, child, visitor, item, topic)
    parent_sings(world, parent, child, visitor, item)
    world.para()
    fix(world, child, visitor, item, topic)

    world.facts.update(
        child=child, visitor=visitor, parent=parent, item=item,
        setting=setting, topic=topic, item_cfg=item_cfg,
        resolved=True,
    )
    return world


SETTINGS = {
    "yard": Setting(place="the little yard", indoor=False, sparkle="sunlight"),
    "porch": Setting(place="the front porch", indoor=False, sparkle="morning light"),
    "playroom": Setting(place="the playroom", indoor=True, sparkle="lamp glow"),
}

TOPICS = {
    "wagon": Topic(
        id="wagon",
        verb="roll the wagon",
        action="ride in",
        risk="scratched",
        repair="take turns",
        tags={"toy", "ride"},
    ),
    "kite": Topic(
        id="kite",
        verb="fly the kite",
        action="hold up",
        risk="tangled",
        repair="share the string",
        tags={"air", "string"},
    ),
    "book": Topic(
        id="book",
        verb="read the book",
        action="look at",
        risk="creased",
        repair="turn pages gently",
        tags={"reading", "paper"},
    ),
    "ball": Topic(
        id="ball",
        verb="bounce the ball",
        action="bounce",
        risk="bumped",
        repair="pass it softly",
        tags={"play", "round"},
    ),
}

ITEMS = {
    "wagon": Item(id="wagon", label="wagon", phrase="a tiny blue wagon", type="wagon", can_share=True),
    "kite": Item(id="kite", label="kite", phrase="a bright paper kite", type="kite", can_share=True),
    "book": Item(id="book", label="book", phrase="a small picture book", type="book", can_share=True),
    "ball": Item(id="ball", label="ball", phrase="a shiny red ball", type="ball", can_share=True),
}

GIRL_NAMES = ["Nell", "Mia", "Pip", "Rose", "Luna", "Ada", "Ivy", "Belle"]
BOY_NAMES = ["Tom", "Ben", "Sam", "Max", "Eli", "Noah", "Finn", "Theo"]
TRAITS = ["tiny", "cheery", "curious", "gentle", "brave", "spry"]


@dataclass
class StoryParams:
    place: str
    topic: str
    item: str
    child_name: str
    child_type: str
    visitor_name: str
    visitor_type: str
    parent_name: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, i) for s in SETTINGS for t in TOPICS for i in ITEMS if t == i]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOPICS.items():
        lines.append(asp.fact("topic", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tagged", tid, tag))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.can_share:
            lines.append(asp.fact("shareable", iid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Topic, Item) :- setting(Place), topic(Topic), item(Item), Topic = Item.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story about property and polite dialogue in {f["setting"].place}.',
        f"Tell a gentle story where {f['child'].id} and {f['visitor'].id} speak kindly about {f['item'].label} being {f['child'].pronoun('possessive')} property.",
        f'Write a short rhyme that includes the word "property" and ends with a happy shared plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, visitor, parent = f["child"], f["visitor"], f["parent"]
    item, topic = f["item"], f["topic"]
    return [
        QAItem(
            question=f"What did {child.id} own in {f['setting'].place}?",
            answer=f"{child.id} owned {child.pronoun('possessive')} {item.label}. It was {child.pronoun('possessive')} property."
        ),
        QAItem(
            question=f"What did {visitor.id} ask to do with the {item.label}?",
            answer=f"{visitor.id} asked if they could {topic.action} it."
        ),
        QAItem(
            question=f"How did the story end for the {item.label}?",
            answer=f"{child.id} chose a kind plan, so they could use the {item.label} carefully and keep it safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is property?",
            answer="Property is something that belongs to someone, like a toy, book, or wagon that they own."
        ),
        QAItem(
            question="Why do people use polite words in a dialogue?",
            answer="Polite words help people ask, listen, and solve problems without being mean."
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id}: meters={meters} memes={memes}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Property, dialogue, and a nursery-rhyme story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--visitor")
    ap.add_argument("--parent")
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
    if args.topic and args.item and args.topic != args.item:
        raise StoryError("In this tiny world, the topic and the item must match.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.topic:
        combos = [c for c in combos if c[1] == args.topic]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, topic, item = rng.choice(sorted(combos))
    gender = "girl" if rng.random() < 0.5 else "boy"
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    visitor_name = args.visitor or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    parent_name = args.parent or rng.choice(["Mum", "Dad", "Mom", "Papa"])
    return StoryParams(
        place=place,
        topic=topic,
        item=item,
        child_name=child_name,
        child_type=gender,
        visitor_name=visitor_name,
        visitor_type="girl" if visitor_name in GIRL_NAMES else "boy",
        parent_name=parent_name,
        parent_type="mother" if parent_name in {"Mum", "Mom"} else "father",
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TOPICS[params.topic],
        ITEMS[params.item],
        params.child_name,
        params.child_type,
        params.visitor_name,
        params.visitor_type,
        params.parent_name,
        params.parent_type,
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


CURATED = [
    StoryParams("yard", "wagon", "wagon", "Nell", "girl", "Dot", "girl", "Mum", "mother", "tiny"),
    StoryParams("porch", "kite", "kite", "Tom", "boy", "June", "girl", "Dad", "father", "curious"),
    StoryParams("playroom", "book", "book", "Mia", "girl", "Ben", "boy", "Mom", "mother", "gentle"),
    StoryParams("yard", "ball", "ball", "Eli", "boy", "Ivy", "girl", "Papa", "father", "spry"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
