#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dirt_dim_gauge_tomahawk_lesson_learned_surprise.py
===================================================================================

A small standalone story world built from the seed words:

- dirt-dim
- gauge
- tomahawk

The domain is a child in a dusty shed who wants to use a tomahawk-shaped tool
for a task that needs careful measuring. A surprising helper and an inner
monologue lead to a safer choice, and the ending proves the lesson learned.

Style goal: rhyming, child-facing storybook prose with a clear beginning,
state-driven turn, and a finish image that shows what changed.

Contract notes:
- stdlib only
- imports storyworlds/results.py eagerly
- lazy-imports storyworlds/asp.py inside ASP helpers
- supports the standard Storyweavers CLI options
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    dim: str
    shelter: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gauge:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    line: str
    reveal: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                out.extend(bits)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_dirt(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    shed = world.entities.get("shed")
    gauge = world.entities.get("gauge")
    if not kid or not shed or not gauge:
        return out
    if kid.meters["dusty"] < THRESHOLD:
        return out
    sig = ("dirt", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shed.meters["mess"] += 1
    gauge.meters["smudged"] += 1
    kid.memes["embarrassed"] += 1
    out.append("The gauge got smudged, and the shed felt a little grim.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    kid = world.entities.get("kid")
    if not helper or not kid:
        return out
    if helper.meters["surprise"] < THRESHOLD:
        return out
    sig = ("surprise", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["wonder"] += 1
    out.append("__surprise__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    if not kid or kid.memes["lesson"] < THRESHOLD:
        return out
    sig = ("lesson", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["calm"] += 1
    out.append("The lesson settled in like rain on a roof.")
    return out


CAUSAL_RULES = [Rule("dirt", _r_dirt), Rule("surprise", _r_surprise), Rule("lesson", _r_lesson)]


def reasonableness_ok(place: Place, gauge: Gauge, tool: Tool) -> bool:
    return place.dim == "dim" and gauge.id == "gauge" and tool.risky


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for gid, gauge in GAUGES.items():
            for tid, tool in TOOLS.items():
                if reasonableness_ok(place, gauge, tool):
                    combos.append((pid, gid, tid))
    return combos


def choose_response() -> str:
    return "set the tomahawk aside and measure with care"


def _do_scene(world: World, kid: Entity, place: Place, gauge: Gauge, tool: Tool, helper: Entity, lesson: Lesson) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"In a dirt-dim shed where old boards leaned and boxes were spread, "
        f"{kid.id} found a gauge that could help things stay true instead."
    )
    world.say(
        f"Beside the gauge lay {tool.phrase}, a tomahawk-looking thing, "
        f"and {kid.id} thought, \"I can use that for my measuring!\""
    )
    world.say(
        f"But {kid.id}'s mind made a small private rhyme: "
        f"\"That tool looks grand, but this job needs time.\""
    )
    world.para()
    helper.meters["surprise"] += 1
    world.say(
        f"Then {helper.id} gave a surprise with a sunny grin: "
        f"{helper.pronoun().capitalize()} brought a chalk line and a tin."
    )
    world.say(
        f"\"Use the gauge,\" {helper.id} said, \"and keep the shed neat; "
        f"a careful little measure is a safer beat.\""
    )
    kid.memes["lesson"] += 1
    kid.meters["dusty"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"So {kid.id} laid down the tomahawk and worked with a smile, "
        f"measuring by the gauge one line at a time, in style."
    )
    world.say(
        f"The shed stayed tidy, the gauge shone clear, and the little helper's "
        f"surprise turned into cheer."
    )
    world.say(
        f"And {kid.id} learned the lesson, deep and bright: "
        f"the safest tool is the one that's right."
    )


def tell(place: Place, gauge: Gauge, tool: Tool, lesson: Lesson, kid_name: str = "Milo",
         kid_gender: str = "boy", helper_name: str = "Pip", helper_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="kid"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    shed = world.add(Entity(id="shed", type="place", label=place.label))
    gauge_ent = world.add(Entity(id="gauge", type="thing", label=gauge.label))
    tool_ent = world.add(Entity(id="tomahawk", type="thing", label=tool.label))
    world.facts.update(place=place, gauge=gauge, tool=tool, lesson=lesson, parent=parent)
    _do_scene(world, kid, place, gauge, tool_ent, helper, lesson)
    world.facts.update(
        kid=kid,
        helper=helper,
        shed=shed,
        gauge_ent=gauge_ent,
        tool_ent=tool_ent,
        outcome="lesson",
        lesson_learned=True,
    )
    return world


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "dirt-dim", "gauge", and "tomahawk".',
        f"Tell a story where {f['kid'].id} wants to use a tomahawk-like tool in a dirt-dim shed, but learns to use a gauge instead.",
        f"Write a gentle surprise story with an inner monologue and a lesson learned ending in rhyme.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    place = f["place"]
    lesson = f["lesson"]
    return [
        ("Who is the story about?",
         f"It is about {kid.id}, who was working in a {place.dim} shed. {helper.id} also helped with a surprise."),
        ("What did the child want to use?",
         f"{kid.id} wanted to use the tomahawk-looking tool, but then {kid.pronoun()} chose the gauge instead. That kept the task careful and calm."),
        ("What did the surprise helper bring?",
         f"{helper.id} brought a chalk line and a tin, which made the job easier. The surprise helped turn the moment from tempting to thoughtful."),
        ("What lesson did the child learn?",
         f"{kid.id} learned that the safest tool is the one that's right. The ending shows {kid.id} using the gauge and leaving the tomahawk aside."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a gauge?",
         "A gauge is a tool that helps you measure or check sizes carefully."),
        ("What is a tomahawk?",
         "A tomahawk is a kind of small axe. It is a tool, not a toy."),
        ("What does dirt-dim mean?",
         "It means the place is a little dark and dusty, with dirt making the light seem faint."),
    ]


@dataclass
class StoryParams:
    place: str
    gauge: str
    tool: str
    kid: str
    kid_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


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


PLACES = {
    "shed": Place("shed", "a dirt-dim shed", "dim", "a safe shelf", "a surprise"),
    "barn": Place("barn", "a dirt-dim barn", "dim", "a soft bench", "a surprise"),
    "workshop": Place("workshop", "a dirt-dim workshop", "dim", "a tidy corner", "a surprise"),
}

GAUGES = {
    "gauge": Gauge("gauge", "gauge", "the gauge", "measure the line"),
}

TOOLS = {
    "tomahawk": Tool("tomahawk", "tomahawk", "the tomahawk", risky=True),
}

LESSONS = {
    "lesson": Lesson("lesson", "safest tool is the one that's right", "measure with care"),
}


CURATED = [
    StoryParams("shed", "gauge", "tomahawk", "Milo", "boy", "Pip", "girl", "mother"),
    StoryParams("barn", "gauge", "tomahawk", "Nia", "girl", "Tess", "girl", "father"),
]


def explain_rejection(place: Place, gauge: Gauge, tool: Tool) -> str:
    return "(No story: this world needs a dirt-dim place, a gauge, and a risky tomahawk so the surprise can turn into a lesson.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("dim", pid, p.dim))
    for gid in GAUGES:
        lines.append(asp.fact("gauge", gid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("risky", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G, T) :- place(P), gauge(G), tool(T), dim(P, dim), risky(T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1

    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: story generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: dirt-dim, gauge, tomahawk, surprise, and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gauge", choices=GAUGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.gauge and args.tool:
        if not reasonableness_ok(PLACES[args.place], GAUGES[args.gauge], TOOLS[args.tool]):
            raise StoryError(explain_rejection(PLACES[args.place], GAUGES[args.gauge], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.gauge is None or c[1] == args.gauge)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, gauge, tool = rng.choice(sorted(combos))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("girl" if kid_gender == "boy" else "boy")
    kid_pool = ["Milo", "Noah", "Finn", "Theo"] if kid_gender == "boy" else ["Nia", "Ivy", "Zoe", "Mina"]
    helper_pool = ["Pip", "Tess", "June", "Sage"] if helper_gender == "girl" else ["Ben", "Kai", "Owen", "Jules"]
    kid = args.kid or rng.choice(kid_pool)
    helper = args.helper or rng.choice(helper_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, gauge, tool, kid, kid_gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], GAUGES[params.gauge], TOOLS[params.tool], LESSONS["lesson"],
                 params.kid, params.kid_gender, params.helper, params.helper_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
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
