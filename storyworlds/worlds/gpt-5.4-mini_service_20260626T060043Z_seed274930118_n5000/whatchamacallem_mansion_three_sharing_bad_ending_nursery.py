#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about three small characters, a mansion, and
a whatchamacallem that does not get shared very well.

Premise:
- Three little characters explore a grand mansion.
- They find one curious object, the whatchamacallem.
- They try to share it.

Turn:
- Sharing is hard because the object is only comfortable for one at a time.
- The first attempt goes badly and leaves everyone cross, crowded, or sad.

Ending:
- The bad ending is gentle and child-facing: the object breaks, the room is
  messy, and the three must settle for a sad quiet rather than a tidy fix.

This script keeps the prose in a nursery-rhyme cadence while still driving it
from a simulated world model with meters and memes.
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
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tired", "sad", "crowded", "mess", "broken", "care", "joy", "greed", "share"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name1: str
    name2: str
    name3: str
    mansion: str = "the mansion"
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.lines = list(self.lines)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def name_pool() -> list[str]:
    return ["Milo", "Nina", "Toby", "Luna", "Pip", "Cora", "Otto", "Daisy"]


def build_nursery_names(rng: random.Random) -> tuple[str, str, str]:
    names = rng.sample(name_pool(), 3)
    return names[0], names[1], names[2]


def bad_share_penalty(world: World) -> None:
    for e in world.entities.values():
        if e.kind == "character" and e.memes["share"] < 1:
            e.meters["sad"] += 1
            e.meters["crowded"] += 1


def maybe_break_whatchamacallem(world: World) -> None:
    obj = world.get("whatchamacallem")
    holders = [e for e in world.entities.values() if e.kind == "character" and e.held_by == e.id]
    if len(holders) >= 2:
        obj.meters["broken"] += 1
        obj.meters["mess"] += 1
        for h in holders:
            h.meters["sad"] += 1
            h.memes["greed"] += 1
        world.say("The whatchamacallem gave a tiny crack and made a sorry little clatter.")


def setup_world(params: StoryParams) -> World:
    w = World(params)
    w.add(Entity(id=params.name1, kind="character", type="child", label=params.name1, location=params.mansion))
    w.add(Entity(id=params.name2, kind="character", type="child", label=params.name2, location=params.mansion))
    w.add(Entity(id=params.name3, kind="character", type="child", label=params.name3, location=params.mansion))
    w.add(Entity(
        id="whatchamacallem",
        kind="thing",
        type="thing",
        label="whatchamacallem",
        phrase="a shiny whatchamacallem",
        location=params.mansion,
        plural=False,
    ))
    return w


def tell_story(w: World) -> None:
    a, b, c = w.get(w.params.name1), w.get(w.params.name2), w.get(w.params.name3)
    obj = w.get("whatchamacallem")
    mansion = w.params.mansion

    w.say(f"Once in {mansion} so tall, there were three small friends in a hall.")
    w.say(f"{a.id}, {b.id}, and {c.id} had bright eyes and feet that liked to patter.")
    w.say(f"They found a whatchamacallem, shiny and round, lying quiet on a carpeted stair.")
    w.say(f"\"Let's share it,\" said {a.id}, sweet as pie.")
    w.say(f"\"Yes, let's share it,\" said {b.id}.")
    w.say(f"\"Yes, let's share it,\" said {c.id}.")

    w.para()
    obj.held_by = a.id
    a.memes["share"] += 1
    w.say(f"But {a.id} held it first, because {a.id}'s hands were quick.")
    w.say(f"Then {b.id} reached for the whatchamacallem too, and {c.id} reached in after that.")
    b.held_by = b.id
    c.held_by = c.id
    b.memes["share"] += 0.5
    c.memes["share"] += 0.5
    a.meters["crowded"] += 1
    b.meters["crowded"] += 1
    c.meters["crowded"] += 1
    w.say("Three little hands around one little thing made a tight, tight knot.")
    maybe_break_whatchamacallem(w)

    w.para()
    bad_share_penalty(w)
    if obj.meters["broken"] >= 1:
        w.say("Alas and alack, the whatchamacallem could not bear the squeeze.")
        w.say(f"It cracked, then wobbled, then toppled with a pitiful plink.")
    else:
        obj.meters["broken"] += 1
        w.say("Alas and alack, the sharing was still too rough.")
        w.say("The little thing slipped and fell, and nobody was glad.")

    w.say(f"{a.id} looked at the mess and felt the joy go dim.")
    w.say(f"{b.id} sniffled.")
    w.say(f"{c.id} went quiet as a mouse in a sock.")
    w.say("So the three friends learned a sad small lesson in the mansion hall:")
    w.say("when three want one thing all at once, the ending can turn bad for all.")

    w.facts.update(
        a=a, b=b, c=c, obj=obj, mansion=mansion,
        broken=obj.meters["broken"] >= 1,
    )


def story_qa(world: World) -> list[QAItem]:
    a, b, c = world.facts["a"], world.facts["b"], world.facts["c"]
    return [
        QAItem(
            question="Who were the three friends in the mansion?",
            answer=f"The three friends were {a.id}, {b.id}, and {c.id}.",
        ),
        QAItem(
            question="What did they find?",
            answer="They found a shiny whatchamacallem.",
        ),
        QAItem(
            question="What went wrong when they tried to share it?",
            answer="They all grabbed at once, and the whatchamacallem cracked in the crowded scramble.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended sadly, with the little object broken and the three friends quiet and disappointed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mansion?",
            answer="A mansion is a very big house with many rooms.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy the same thing too.",
        ),
        QAItem(
            question="What is a whatchamacallem?",
            answer="A whatchamacallem is a playful word for an object when someone does not want to name it exactly.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        'Write a short nursery-rhyme story about three friends in a mansion who find a whatchamacallem and try to share it.',
        'Tell a child-facing story with three small characters, a grand mansion, and a bad ending caused by poor sharing.',
        'Write a simple rhyming tale using the words whatchamacallem, mansion, and three.',
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: three, mansion, whatchamacallem, and a bad ending.")
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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
    n1, n2, n3 = args.name1, args.name2, args.name3
    if len({x for x in [n1, n2, n3] if x}) != len([x for x in [n1, n2, n3] if x]):
        raise StoryError("Please choose three different names.")
    if not n1 or not n2 or not n3:
        n1, n2, n3 = build_nursery_names(rng)
    return StoryParams(name1=n1, name2=n2, name3=n3, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    w = setup_world(params)
    tell_story(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(E) :- child(E).
entity(whatchamacallem).

three_children(A,B,C) :- child(A), child(B), child(C), A != B, A != C, B != C.

shared_bad_end(A,B,C) :- three_children(A,B,C), takes(A), takes(B), takes(C).
broken_object :- shared_bad_end(_,_,_).

#show shared_bad_end/3.
#show broken_object/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "alpha"),
        asp.fact("child", "beta"),
        asp.fact("child", "gamma"),
        asp.fact("object", "whatchamacallem"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show broken_object/0."))
    ok = any(sym.name == "broken_object" for sym in model)
    if ok:
        print("OK: ASP twin produces a bad ending model.")
        return 0
    print("MISMATCH: ASP twin did not produce expected model.")
    return 1


CURATED = [
    StoryParams("Milo", "Nina", "Toby"),
    StoryParams("Luna", "Pip", "Cora"),
    StoryParams("Otto", "Daisy", "Mia"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show broken_object/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
