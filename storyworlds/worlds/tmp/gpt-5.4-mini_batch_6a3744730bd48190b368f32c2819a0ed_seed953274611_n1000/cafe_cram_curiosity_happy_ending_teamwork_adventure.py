#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cafe_cram_curiosity_happy_ending_teamwork_adventure.py
=======================================================================================

A standalone storyworld about a curious trip through a cafe, a quick cram of
supplies, teamwork, and a happy adventure ending.

Seed words and features:
- Words: cafe, cram
- Features: Curiosity, Happy Ending, Teamwork
- Style: Adventure

The world is built around a small, child-facing premise:
two kids visit a cafe, notice a mysterious problem, cram a few useful things
into a bag, work together to solve it, and finish with a warm, bright ending
that proves what changed.

The story model uses typed entities with physical meters and emotional memes,
state-driven causality, and an inline ASP twin for parity checks.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Cafe:
    id: str
    place: str
    noise: str
    smell: str
    nook: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CuriositySeed:
    id: str
    clue: str
    pull: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    location: str
    trouble: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    cafe: str
    curiosity: str
    need: str
    tool_a: str
    tool_b: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"explorer", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["worry"] < THRESHOLD:
            continue
        sig = ("alarm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.kids():
            kid.memes["focus"] += 1
        out.append("__alarm__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("worked_together") and not world.facts.get("shared_win"):
        world.facts["shared_win"] = True
        for kid in world.kids():
            kid.memes["joy"] += 1
            kid.memes["pride"] += 1
        out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("alarm", "social", _r_alarm),
    Rule("teamwork", "social", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAFE_REGISTRY = {
    "corner": Cafe("corner", "the cafe", "soft clinks and low chatter", "fresh bread and cocoa", "the back nook", {"cafe"}),
    "window": Cafe("window", "the window seat cafe", "rain taps and warm cups", "butter and cinnamon", "the window booth", {"cafe"}),
}

CURIOSITY_REGISTRY = {
    "whistle": CuriositySeed("whistle", "a tiny whistle behind the pastry case", "too curious to ignore", {"curiosity"}),
    "map": CuriositySeed("map", "a folded map tucked under a sugar jar", "too curious to leave alone", {"curiosity"}),
}

NEED_REGISTRY = {
    "lost_cat": Need("lost_cat", "a little cat", "under the pastry case", "stuck and scared", {"animal", "rescue"}),
    "jammed_tray": Need("jammed_tray", "a tray", "behind the counter", "stuck behind a stack of cups", {"help", "cleanup"}),
}

TOOL_REGISTRY = {
    "napkins": Tool("napkins", "a stack of napkins", "wipe drips and make a trail", {"soft", "help"}),
    "spoon": Tool("spoon", "a long spoon", "reach under the low shelf", {"reach", "help"}),
    "chair": Tool("chair", "a small chair", "stand on safely", {"reach", "help"}),
    "tray": Tool("tray", "a serving tray", "slide things out carefully", {"help", "slide"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Ben", "Sam"]
HELPERS = ["barista", "cafe owner", "older cousin"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cafe in CAFE_REGISTRY:
        for curiosity in CURIOSITY_REGISTRY:
            for need in NEED_REGISTRY:
                if curiosity == "whistle" and need != "lost_cat":
                    continue
                combos.append((cafe, curiosity, need))
    return combos


def clue_pull(cur: CuriositySeed) -> str:
    return cur.pull


def setup(world: World, a: Entity, b: Entity, cafe: Cafe) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"{a.id} and {b.id} stepped into {cafe.place}, where {cafe.noise} and the smell of {cafe.smell} made the room feel like the start of an adventure."
    )
    world.say(
        f"They settled near {cafe.nook}, looking around with bright eyes for the next clue."
    )


def notice(world: World, a: Entity, b: Entity, cur: CuriositySeed) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"Then {a.id} noticed {cur.clue}, and both children felt {cur.pull}."
    )
    world.say(
        f'"Look!" {a.id} said. "Something small is hiding here."'
    )


def cram_supplies(world: World, a: Entity, b: Entity, t1: Tool, t2: Tool) -> None:
    a.meters["bag_weight"] += 1
    b.meters["bag_weight"] += 1
    world.say(
        f"They hurried to cram {t1.label} and {t2.label} into a bag so they could help fast."
    )


def discover_need(world: World, need: Need) -> None:
    world.say(
        f"Near {need.location}, they found {need.label} in trouble: it was {need.trouble}."
    )


def teamwork_plan(world: World, a: Entity, b: Entity, t1: Tool, t2: Tool, helper: str) -> None:
    world.facts["worked_together"] = True
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"{helper.capitalize()} nodded and gave them a simple plan: {a.id} would use {t1.label}, {b.id} would use {t2.label}, and together they could fix it."
    )


def rescue(world: World, need: Need) -> None:
    need_entity = world.get("need")
    need_entity.meters["stuck"] = 0
    need_entity.meters["safe"] = 1
    world.say(
        f"Together they followed the plan, and soon {need.label} was free."
    )
    world.say(
        f"The whole cafe seemed to breathe out as the worry faded away."
    )


def ending(world: World, a: Entity, b: Entity, cafe: Cafe) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At last, {a.id} and {b.id} shared a proud grin at {cafe.place}, happy that their curiosity had helped instead of caused trouble."
    )
    world.say(
        f"They left the cafe with light steps, side by side, ready for the next adventure."
    )


def tell(cafe: Cafe, curiosity: CuriositySeed, need: Need, tool_a: Tool, tool_b: Tool,
         child_a: str = "Mia", child_a_gender: str = "girl",
         child_b: str = "Leo", child_b_gender: str = "boy",
         helper: str = "barista") -> World:
    world = World()
    a = world.add(Entity(id=child_a, kind="character", type=child_a_gender, role="explorer"))
    b = world.add(Entity(id=child_b, kind="character", type=child_b_gender, role="helper"))
    world.add(Entity(id="cafe", type="place", label=cafe.place, tags=set(cafe.tags)))
    world.add(Entity(id="need", type="need", label=need.label, tags=set(need.tags)))
    setup(world, a, b, cafe)
    world.para()
    notice(world, a, b, curiosity)
    cram_supplies(world, a, b, tool_a, tool_b)
    discover_need(world, need)
    world.para()
    teamwork_plan(world, a, b, tool_a, tool_b, helper)
    propagate(world, narrate=False)
    rescue(world, need)
    world.para()
    ending(world, a, b, cafe)
    world.facts.update(
        cafe=cafe, curiosity=curiosity, need=need, tool_a=tool_a, tool_b=tool_b,
        child_a=a, child_b=b, helper=helper, outcome="happy", teamwork=True
    )
    return world


@dataclass
class StoryParams:
    cafe: str
    curiosity: str
    need: str
    tool_a: str
    tool_b: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly adventure story that includes the words "{f["cafe"].place}" and "cram".',
        f"Tell a happy story where {f['child_a'].id} and {f['child_b'].id} explore a cafe, notice a problem, and work together to fix it.",
        f"Write a curious teamwork adventure with a warm cafe ending and a clear rescue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["child_a"], f["child_b"]
    need = f["need"]
    cafe = f["cafe"]
    return [
        ("Where does the story take place?",
         f"It takes place at {cafe.place}. The cafe is warm and busy, which makes the adventure feel cozy and exciting at the same time."),
        ("Why did the children cram the tools into a bag?",
         f"They were curious and wanted to help right away. Cramming the tools into a bag let them move fast once they found the problem."),
        ("What problem did they find?",
         f"They found {need.label} near {need.location}, and it was {need.trouble}."),
        ("How did they solve the problem?",
         f"{a.id} and {b.id} worked together with the helper's plan. One child used {f['tool_a'].label}, the other used {f['tool_b'].label}, and that teamwork freed the problem safely."),
        ("How did the story end?",
         f"It ended happily at {cafe.place}. The children left proud because their curiosity and teamwork helped someone instead of causing trouble."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a cafe?",
         "A cafe is a place where people can sit, drink, and eat snacks. It often feels warm and friendly."),
        ("What does it mean to cram something into a bag?",
         "To cram something into a bag means to pack it in quickly and tightly. People do that when they need to hurry."),
        ("What is teamwork?",
         "Teamwork is when people help each other and do different jobs together. It works best when everyone shares the plan."),
        ("Why is curiosity useful?",
         "Curiosity helps you notice clues and ask questions. It can lead to helpful discoveries when you stay kind and careful."),
    ]
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(_: str) -> str:
    return "(No story: the chosen options do not fit this small cafe adventure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combinations exist.)")
    cafe = args.cafe or rng.choice(sorted(CAFE_REGISTRY))
    curiosity = args.curiosity or rng.choice(sorted(CURIOSITY_REGISTRY))
    need = args.need or rng.choice(sorted(NEED_REGISTRY))
    tool_a = args.tool_a or rng.choice(sorted(TOOL_REGISTRY))
    tool_b = args.tool_b or rng.choice(sorted([k for k in TOOL_REGISTRY if k != tool_a]))
    child_a_gender = args.child_a_gender or rng.choice(["girl", "boy"])
    child_b_gender = args.child_b_gender or ("boy" if child_a_gender == "girl" else "girl")
    child_a = args.child_a or (rng.choice(GIRL_NAMES if child_a_gender == "girl" else BOY_NAMES))
    child_b = args.child_b or (rng.choice([n for n in (GIRL_NAMES if child_b_gender == "girl" else BOY_NAMES) if n != child_a]))
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        cafe=cafe,
        curiosity=curiosity,
        need=need,
        tool_a=tool_a,
        tool_b=tool_b,
        child_a=child_a,
        child_a_gender=child_a_gender,
        child_b=child_b,
        child_b_gender=child_b_gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        cafe = CAFE_REGISTRY[params.cafe]
        curiosity = CURIOSITY_REGISTRY[params.curiosity]
        need = NEED_REGISTRY[params.need]
        tool_a = TOOL_REGISTRY[params.tool_a]
        tool_b = TOOL_REGISTRY[params.tool_b]
    except KeyError as exc:
        raise StoryError(f"Unknown story parameter: {exc.args[0]}") from exc

    world = tell(
        cafe=cafe,
        curiosity=curiosity,
        need=need,
        tool_a=tool_a,
        tool_b=tool_b,
        child_a=params.child_a,
        child_a_gender=params.child_a_gender,
        child_b=params.child_b,
        child_b_gender=params.child_b_gender,
        helper=params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cafe adventure about curiosity, teamwork, and a happy ending.")
    ap.add_argument("--cafe", choices=CAFE_REGISTRY)
    ap.add_argument("--curiosity", choices=CURIOSITY_REGISTRY)
    ap.add_argument("--need", choices=NEED_REGISTRY)
    ap.add_argument("--tool-a", dest="tool_a", choices=TOOL_REGISTRY)
    ap.add_argument("--tool-b", dest="tool_b", choices=TOOL_REGISTRY)
    ap.add_argument("--child-a", dest="child_a")
    ap.add_argument("--child-a-gender", dest="child_a_gender", choices=["girl", "boy"])
    ap.add_argument("--child-b", dest="child_b")
    ap.add_argument("--child-b-gender", dest="child_b_gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CAFE_REGISTRY:
        lines.append(asp.fact("cafe", cid))
    for cid in CURIOSITY_REGISTRY:
        lines.append(asp.fact("curiosity", cid))
    for nid in NEED_REGISTRY:
        lines.append(asp.fact("need", nid))
    for tid in TOOL_REGISTRY:
        lines.append(asp.fact("tool", tid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("requires_teamwork", "cafe_adventure"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, U, N) :- cafe(C), curiosity(U), need(N).
teamwork_story :- requires_teamwork(cafe_adventure).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import tempfile

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP combos differ from Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        emit(sample, trace=False, qa=False)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams(
        cafe="corner",
        curiosity="whistle",
        need="lost_cat",
        tool_a="napkins",
        tool_b="spoon",
        child_a="Mia",
        child_a_gender="girl",
        child_b="Leo",
        child_b_gender="boy",
        helper="barista",
    ),
    StoryParams(
        cafe="window",
        curiosity="map",
        need="jammed_tray",
        tool_a="chair",
        tool_b="tray",
        child_a="Nora",
        child_a_gender="girl",
        child_b="Sam",
        child_b_gender="boy",
        helper="older cousin",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CAFE_REGISTRY:
        for u in CURIOSITY_REGISTRY:
            for n in NEED_REGISTRY:
                combos.append((c, u, n))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
