#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/tale_shawl_craft_workshop_surprise_repetition_quest.py
==============================================================================================================================

A small slice-of-life storyworld set in a craft workshop.

Seed tale:
- A child comes to a craft workshop with a shawl.
- The shawl needs finishing, but a surprise detail changes the plan.
- The child repeats a careful step while on a small quest to find the right trim.
- The ending proves the shawl is finished, useful, and beloved.

The world models:
- physical meters: cloth, thread, neatness, color, comfort, found, finished, time
- emotional memes: curiosity, worry, delight, pride, patience, surprise, resolve

The prose is authored from world state, not a frozen template: the same action can
change the workshop, the shawl, and the child's feelings.
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
class Person:
    id: str
    type: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    place: str = "table"
    finished: bool = False


@dataclass
class Workshop:
    place: str = "the craft workshop"
    entities: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, obj):
        self.entities[obj.id] = obj
        return obj

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "Workshop":
        import copy
        w = Workshop(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    name: str
    age: int
    companion: str
    shawl_color: str
    trim_color: str
    surprise: str
    quest_item: str
    seed: Optional[int] = None


NAMES = ["Maya", "Nora", "Lina", "Iris", "Tess", "Ava", "Mina", "Zoe"]
COMPANIONS = ["a parent", "an aunt", "a grandparent", "a kind teacher"]
COLORS = ["blue", "gold", "green", "red", "plum", "silver"]
TRIMS = ["buttons", "fringe", "tiny stars", "a soft border", "little shells"]
QUEST_ITEMS = ["the scissors", "the ribbon box", "the button tin", "the thread drawer"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a shawl, a craft workshop, and a small quest.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--age", type=int, choices=range(4, 11))
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--shawl-color", dest="shawl_color", choices=COLORS)
    ap.add_argument("--trim-color", dest="trim_color", choices=COLORS)
    ap.add_argument("--surprise", choices=["a missing spool", "a spilled cup of tea", "an extra bright trim", "a crooked stitch"])
    ap.add_argument("--quest-item", dest="quest_item", choices=QUEST_ITEMS)
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
    name = args.name or rng.choice(NAMES)
    age = args.age or rng.randint(5, 9)
    companion = args.companion or rng.choice(COMPANIONS)
    shawl_color = args.shawl_color or rng.choice(COLORS)
    trim_color = args.trim_color or rng.choice([c for c in COLORS if c != shawl_color])
    surprise = args.surprise or rng.choice(["a missing spool", "a spilled cup of tea", "an extra bright trim", "a crooked stitch"])
    quest_item = args.quest_item or rng.choice(QUEST_ITEMS)
    return StoryParams(name=name, age=age, companion=companion, shawl_color=shawl_color, trim_color=trim_color, surprise=surprise, quest_item=quest_item)


def build_world(params: StoryParams) -> Workshop:
    w = Workshop()
    child = w.add(Person(id="child", type="girl" if params.name not in {"Noah"} else "boy", name=params.name, role="child"))
    helper = w.add(Person(id="helper", type="adult", name=params.companion, role="helper"))
    shawl = w.add(ObjectThing(id="shawl", label="shawl", phrase=f"a {params.shawl_color} shawl with room for a trim", owner=child.id, place="worktable"))
    shawl.meters.update({"cloth": 1.0, "thread": 0.5, "neatness": 0.2, "finished": 0.0})
    shawl.memes.update({"comfort": 0.3})
    child.memes.update({"curiosity": 1.0, "worry": 0.1, "delight": 0.0, "pride": 0.0, "patience": 0.2, "surprise": 0.0, "resolve": 0.0})
    helper.memes.update({"patience": 1.0})
    w.facts.update(params=params, child=child, helper=helper, shawl=shawl)
    return w


def _repeat_stitch(w: Workshop) -> None:
    child: Person = w.get("child")
    shawl: ObjectThing = w.get("shawl")
    child.memes["patience"] += 0.3
    shawl.meters["neatness"] += 0.35
    shawl.meters["thread"] += 0.2
    child.say = None
    w.say(f"{child.name} stitched one careful edge, then stitched it again until the line looked steady.")


def maybe_surprise(w: Workshop, params: StoryParams) -> None:
    child: Person = w.get("child")
    helper: Person = w.get("helper")
    shawl: ObjectThing = w.get("shawl")
    child.memes["surprise"] += 1.0
    child.memes["worry"] += 0.4
    if params.surprise == "a missing spool":
        w.say(f"Then there was a surprise: the spool of {params.trim_color} thread was missing from the table.")
    elif params.surprise == "a spilled cup of tea":
        w.say("Then there was a surprise: a cup of tea tipped a little and made everyone pause.")
    elif params.surprise == "an extra bright trim":
        w.say(f"Then there was a surprise: a box of {params.trim_color} trim gleamed brighter than expected.")
    else:
        w.say("Then there was a surprise: one tiny stitch had curled crooked at the corner.")
    helper.memes["patience"] += 0.3
    shawl.meters["neatness"] -= 0.1


def quest_for_trim(w: Workshop, params: StoryParams) -> None:
    child: Person = w.get("child")
    shawl: ObjectThing = w.get("shawl")
    child.memes["resolve"] += 1.0
    child.memes["curiosity"] += 0.4
    w.say(f"{child.name} started a little quest through the craft workshop to find {params.quest_item}.")
    w.say("The child checked under folded fabric, beside jars of buttons, and near the bright ribbon box.")
    shawl.meters["time"] = shawl.meters.get("time", 0.0) + 1.0
    shawl.meters["found"] = 1.0


def finish_shawl(w: Workshop, params: StoryParams) -> None:
    child: Person = w.get("child")
    helper: Person = w.get("helper")
    shawl: ObjectThing = w.get("shawl")
    child.memes["delight"] += 1.0
    child.memes["pride"] += 1.0
    shawl.finished = True
    shawl.meters["finished"] = 1.0
    shawl.meters["neatness"] = max(shawl.meters["neatness"], 1.0)
    w.say(f"At last, {child.name} found {params.quest_item}, and {helper.name} helped set the final piece in place.")
    w.say(f"The {params.shawl_color} shawl finally held its {params.trim_color} trim, neat and warm and ready to wear.")


def tell_story(params: StoryParams) -> Workshop:
    w = build_world(params)
    child: Person = w.get("child")
    helper: Person = w.get("helper")
    shawl: ObjectThing = w.get("shawl")
    w.say(f"{child.name} went into {w.place} with {params.companion} for a quiet afternoon of making.")
    w.say(f"{child.name} was working on {shawl.phrase}, and {helper.name} said the little tale could wait while the stitches lined up.")
    w.para()
    _repeat_stitch(w)
    maybe_surprise(w, params)
    w.say(f"{child.name} looked at the shawl, took a breath, and kept going instead of giving up.")
    w.para()
    quest_for_trim(w, params)
    finish_shawl(w, params)
    w.say(f"By the end, {child.name} wore the shawl around {child.pronoun('possessive')} shoulders and smiled at the soft color.")
    w.facts.update(child=child, helper=helper, shawl=shawl)
    return w


def generation_prompts(world: Workshop) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a slice-of-life tale set in a craft workshop about {p.name} and a shawl.",
        f"Tell a gentle story with repetition, surprise, and a small quest to find {p.quest_item}.",
        f"Write a child-facing workshop story where a {p.shawl_color} shawl gets finished after a surprise.",
    ]


def story_qa(world: Workshop) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Person = world.facts["child"]
    shawl: ObjectThing = world.facts["shawl"]
    return [
        QAItem(question=f"Where did {child.name} work on the shawl?", answer=f"{child.name} worked on it in the craft workshop with {p.companion}."),
        QAItem(question=f"What was the shawl like at the start?", answer=f"It was a {p.shawl_color} shawl that still needed its trim and careful finishing."),
        QAItem(question=f"What surprise changed the afternoon?", answer=f"The surprise was {p.surprise}, so the child had to pause and keep going carefully."),
        QAItem(question=f"What was the quest in the story?", answer=f"The quest was to find {p.quest_item} so the shawl could be finished nicely."),
        QAItem(question=f"How did the story end?", answer=f"The shawl was finished, neat, and ready to wear, and {child.name} felt proud."),
    ]


def world_qa(world: Workshop) -> list[QAItem]:
    return [
        QAItem(question="What is a shawl?", answer="A shawl is a soft piece of cloth people can wear over their shoulders for warmth or style."),
        QAItem(question="What is a craft workshop?", answer="A craft workshop is a place where people make things with tools, thread, paper, fabric, or glue."),
        QAItem(question="Why do people repeat a careful stitch?", answer="They repeat a careful stitch to make the line neat and strong."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: Workshop) -> str:
    lines = ["--- trace ---"]
    for obj in world.entities.values():
        if isinstance(obj, Person):
            lines.append(f"{obj.id}: memes={dict(obj.memes)}")
        else:
            lines.append(f"{obj.id}: meters={dict(obj.meters)} finished={obj.finished}")
    return "\n".join(lines)


ASP_RULES = r"""
reachable_finish :- found_trim, repeated_stitch, surprise_handled.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "craft_workshop"),
        asp.fact("feature", "surprise"),
        asp.fact("feature", "repetition"),
        asp.fact("feature", "quest"),
        asp.fact("seed_word", "tale"),
        asp.fact("seed_word", "shawl"),
    ])


def build_asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n#show reachable_finish/0.\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(build_asp_program())
    ok = any(sym.name == "reachable_finish" for sym in model)
    if ok:
        print("OK: ASP rule emits a reachable finish.")
        return 0
    print("MISMATCH: ASP rule did not derive reachable_finish.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Maya", 7, "a parent", "blue", "gold", "a missing spool", "the ribbon box"),
            StoryParams("Nora", 6, "a kind teacher", "green", "silver", "an extra bright trim", "the button tin"),
            StoryParams("Lina", 8, "an aunt", "plum", "red", "a crooked stitch", "the thread drawer"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
