#!/usr/bin/env python3
"""
storyworlds/worlds/grip_dim_visual_bravery_twist_rhyming_story.py
=================================================================

A small standalone storyworld in a rhyming-story style.

Seed tale:
---
A child named Pip wants to climb a wobbly hill at dusk to hang a bright paper star.
The rope is slack, the light is dim, and the wind makes the path twist.
Pip feels a little scared, but wants to be brave.

A careful helper notices the grip is getting weak on a small ladder hook.
They warn Pip, suggest a safer knot and a steadier hold, and Pip chooses bravery:
not the risky kind, but the kind that pauses, fixes the problem, and tries again.

A small twist changes the ending: the star was never for the hill at all.
It was for a neighbor's dark window, and Pip's bravery helps brighten it.

This script models:
- physical meters: grip, dim, bright, sway, height, steadiness
- emotional memes: fear, bravery, joy, trust, surprise
- a predict-then-warn beat
- a turn driven by a twist in the visual plan
- a rhyming prose voice with child-friendly concrete details
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    worn_by: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    light: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    want: str
    do: str
    twist_hint: str
    risk: str
    visual: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    fix: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    if child.meters["grip"] >= THRESHOLD:
        return out
    sig = ("slip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.meters["sway"] += 1
    out.append("The hold grew slick and the path began to sway.")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    if world.facts.get("twist_seen"):
        return out
    if child.memes["surprise"] < THRESHOLD:
        return out
    world.facts["twist_seen"] = True
    child.meters["bright"] += 1
    world.entities["sign"].meters["bright"] += 1
    out.append("A twinkle of truth changed the scene.")
    return out


CAUSAL_RULES = [Rule("slip", "physical", _r_slip), Rule("twist", "physical", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_hold(world: World, child: Entity, task: Task) -> dict:
    sim = world.copy()
    sim.get("child").meters["grip"] -= 1.5
    _ = task
    propagate(sim, narrate=False)
    return {"slip": sim.get("child").memes["fear"] > 0, "sway": sim.get("child").meters["sway"]}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for task_id in place.affords:
            task = TASKS[task_id]
            for aid_id, aid in AIDS.items():
                if task_id in aid.supports:
                    combos.append((place.id, task_id, aid_id))
    return combos


@dataclass
class StoryParams:
    place: str = "lane"
    task: str = "star"
    aid: str = "knot"
    child_name: str = "Pip"
    child_gender: str = "boy"
    helper_name: str = "Mina"
    helper_gender: str = "girl"
    seed: Optional[int] = None


PLACES = [
    Place(id="lane", label="the lane", light="dim", affords={"star", "rope"}),
    Place(id="roof", label="the roof", light="dim", affords={"star"}),
    Place(id="porch", label="the porch", light="soft", affords={"star"}),
]

TASKS = {
    "star": Task(
        id="star",
        want="hang a paper star",
        do="hang the paper star",
        twist_hint="the star was meant for a window, not the hill",
        risk="the loose grip could make the child slip",
        visual="a bright star hanging in dim dusk",
        tags={"visual", "twist"},
    ),
    "rope": Task(
        id="rope",
        want="tie the rope to the hook",
        do="tie the rope to the hook",
        twist_hint="the rope was only a test line, not the final one",
        risk="the knot could slide in the grip-dim air",
        visual="a rope line against a dim sky",
        tags={"grip-dim"},
    ),
}

AIDS = {
    "knot": Aid(id="knot", label="a snug knot", fix="tie a snug knot", supports={"star", "rope"}, tags={"grip-dim"}),
    "lamp": Aid(id="lamp", label="a little lamp", fix="turn on a little lamp", supports={"star"}, tags={"visual"}),
    "hook": Aid(id="hook", label="a steadier hook", fix="clip to a steadier hook", supports={"rope"}, tags={"grip-dim"}),
}

WORLD_KNOWLEDGE = {
    "visual": [("What does visual mean?", "Visual means something you can see with your eyes, like a bright picture or a shining star.")],
    "grip-dim": [("What does grip-dim suggest in a story?", "It suggests a weak hold in dim light, where it is harder to see and easier to slip.")],
    "twist": [("What is a twist in a story?", "A twist is a surprise that changes what you thought was happening.")],
    "bravery": [("What is bravery?", "Bravery means doing what is right or needed even when you feel scared.")],
}


def tell(place: Place, task: Task, aid: Aid, child_name: str = "Pip", child_gender: str = "boy",
         helper_name: str = "Mina", helper_gender: str = "girl") -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="hero", traits=["small", "brave"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper", traits=["careful"]))
    star = world.add(Entity(id="star", type="thing", label="paper star"))
    sign = world.add(Entity(id="sign", type="thing", label="window sign"))
    world.facts["task"] = task
    world.facts["aid"] = aid
    world.facts["place"] = place
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["star"] = star
    world.facts["sign"] = sign

    child.meters["grip"] = 1.0
    child.meters["bright"] = 0.0
    child.meters["sway"] = 0.0
    child.meters["height"] = 1.0
    child.memes["fear"] = 0.0
    child.memes["bravery"] = 1.0
    child.memes["surprise"] = 0.0
    helper.memes["trust"] = 1.0
    helper.meters["steady"] = 1.0
    star.meters["bright"] = 0.0
    sign.meters["bright"] = 0.0
    world.facts["twist_seen"] = False

    world.say(f"{child_name} went out at dusk, in the lane so dim,")
    world.say(f"To hang a bright paper star, a little and slim.")
    world.say(f"The air was {place.light}, and the hill looked tall,")
    world.say(f"But {child_name} still smiled and would not let fear fall.")
    world.para()
    world.say(f'"I can do it," {child_name} said, with a brave little grin,')
    world.say(f"Though the hold was a grip-dim one, and the wind blew thin.")
    world.say(f"The star was visual, shining in mind,")
    world.say(f"Yet the hook kept wobbling, not snug and not kind.")
    world.para()

    child.memes["surprise"] += 1
    propagate(world, narrate=True)
    pred = predict_hold(world, child, task)
    world.facts["pred"] = pred

    world.say(f"{helper_name} saw the sway and spoke soft and low,")
    world.say(f'"A safer way now will help that star glow."')
    world.say(f'"Use {aid.fix}, and let your brave heart show."')
    child.memes["trust"] += 1
    child.meters["grip"] += 0.7
    world.say(f"{child_name} took a breath, then nodded right there,")
    world.say(f"Brave not by rushing, but by choosing with care.")
    world.para()

    world.say(f"The twist was this: the star was meant for a window nearby,")
    world.say(f"Not the hill at all, but a dark little eye in the sky.")
    world.say(f"So they carried it over, with a soft careful song,")
    world.say(f"And the window grew twinkly where it had been wrong.")
    world.say(f"The lane looked brighter, the dusk turned sweet,")
    world.say(f"And {child_name}'s brave step felt steady and neat.")
    world.say(f"The helper smiled, and the star shone above,")
    world.say(f"A visual glow full of courage and love.")
    world.say(f"In dim little evening, with trouble gone by,")
    world.say(f"{child_name} learned that brave hearts can still pause and try.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    aid = f["aid"]
    return [
        'Write a rhyming story for a young child that includes the words "grip-dim" and "visual".',
        f"Tell a brave little rhyming tale where {child.label} tries to {task.want} in dim light, then learns a safer way.",
        f"Write a rhyme with a twist: a child named {child.label} wants to {task.do}, but the ending reveals the true target and a brighter scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    task = f["task"]
    aid = f["aid"]
    pred = f["pred"]
    return [
        QAItem(
            question=f"What did {child.label} want to do in the dim lane?",
            answer=f"{child.label} wanted to {task.want}. The story starts with that wish and the dim light makes the job feel tricky.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {child.label} about the hold?",
            answer=f"{helper.label} warned because the grip was weak and the path was swaying. That mattered because a slip could spoil the brave little plan.",
        ),
        QAItem(
            question=f"How did bravery show up in the story?",
            answer=f"Bravery showed up when {child.label} listened, paused, and chose the safer way. The brave choice was to fix the problem instead of rushing past it.",
        ),
        QAItem(
            question="What was the twist in the ending?",
            answer=f"The twist was that the star was never meant for the hill at all. It was meant for a window nearby, so the same star became a bright surprise instead of a risky one.",
        ),
        QAItem(
            question="Was the hold likely to slip before help came?",
            answer=f"Yes. The prediction said a slip was likely, and the sway would grow if the grip stayed weak. That is why the helper spoke up right away.",
        ),
        QAItem(
            question=f"What did {child.label} use to make the task safer?",
            answer=f"{child.label} used {aid.label} and a steadier hold. That helped the work stay calm and kept the ending bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["task"].id, world.facts["aid"].id, "bravery", "twist", "visual", "grip-dim"}
    out: list[QAItem] = []
    for key, items in WORLD_KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_possible(P,T) :- place(P), task(T), affords(P,T).
aid_fits(A,T) :- aid(A), task(T), supports(A,T).
valid(P,T,A) :- task_possible(P,T), aid_fits(A,T).
visual_twist :- task(star), task(rope).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        for t in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, t))
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", t.id, tag))
    for a in AIDS.values():
        lines.append(asp.fact("aid", a.id))
        for s in sorted(a.supports):
            lines.append(asp.fact("supports", a.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in ASP parity.")
        print(" only python:", sorted(py - cl))
        print(" only asp:", sorted(cl - py))
        rc = 1

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            print("Smoke test failed: empty story.")
            rc = 1
        else:
            print("OK: generate() smoke test produced a story.")
    except Exception as err:  # pragma: no cover
        print(f"Smoke test failed: {err}")
        return 1

    try:
        _ = sample.to_json()
        print("OK: serialization smoke test passed.")
    except Exception as err:  # pragma: no cover
        print(f"Serialization failed: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: bravery, a visual twist, and a dim grip.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--task", choices=list(TASKS))
    ap.add_argument("--aid", choices=list(AIDS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, aid = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        task=task,
        aid=aid,
        child_name=args.name or rng.choice(["Pip", "Dot", "Bea", "Milo", "Ivy"]),
        child_gender="boy" if (args.name or "Pip") in {"Pip", "Milo"} else "girl",
        helper_name=args.helper or rng.choice(["Mina", "Nell", "Sage", "Luna", "Tess"]),
        helper_gender="girl",
        seed=None,
    )


def valid_story_reason(params: StoryParams) -> bool:
    return any(c == (params.place, params.task, params.aid) for c in valid_combos())


def generate(params: StoryParams) -> StorySample:
    if params.place not in {p.id for p in PLACES}:
        raise StoryError("Unknown place.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if params.aid not in AIDS:
        raise StoryError("Unknown aid.")
    if not valid_story_reason(params):
        raise StoryError("This combination is not reasonable for the storyworld.")
    world = tell(next(p for p in PLACES if p.id == params.place), TASKS[params.task], AIDS[params.aid], params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
    StoryParams(place="lane", task="star", aid="knot", child_name="Pip", child_gender="boy", helper_name="Mina", helper_gender="girl", seed=1),
    StoryParams(place="porch", task="star", aid="lamp", child_name="Ivy", child_gender="girl", helper_name="Nell", helper_gender="girl", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
