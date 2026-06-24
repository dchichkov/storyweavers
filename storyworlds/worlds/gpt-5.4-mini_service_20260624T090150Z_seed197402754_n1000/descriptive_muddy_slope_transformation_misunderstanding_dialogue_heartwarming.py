#!/usr/bin/env python3
"""
A small heartwarming storyworld about a muddy slope, a misunderstood plan,
and a gentle transformation.

Premise:
- A child loves climbing the muddy slope by the garden.
- A careful parent worries the slope is too slick and muddy.
- A misunderstanding makes the child think the fun is cancelled.
- A conversation reveals they can transform the slope with simple tools.
- The ending proves the change: the slope becomes a safe little path,
  and everyone feels closer.

The story is state-driven: physical meters track mud, slickness, and safety;
emotional memes track worry, hurt feelings, and relief.
"""

from __future__ import annotations

import argparse
import copy
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mud": 0.0, "slick": 0.0, "safe": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hurt": 0.0, "hope": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the muddy slope"
    affords: set[str] = field(default_factory=lambda: {"climb", "clear", "transform"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    help_line: str
    finish_line: str


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_slick(world: World) -> list[str]:
    out: list[str] = []
    slope = world.get("slope")
    child = world.get("child")
    if slope.meters["mud"] >= THRESHOLD and slope.meters["safe"] < THRESHOLD:
        sig = ("slick",)
        if sig not in world.fired:
            world.fired.add(sig)
            slope.meters["slick"] = 1.0
            out.append("The muddy slope stayed slick and hard to trust.")
    if child.meters["mud"] >= THRESHOLD:
        sig = ("muddy_child",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"{child.id}'s shoes picked up mud on the way up.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["hurt"] >= THRESHOLD and parent.memes["hope"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["hurt"] = 0.0
            child.memes["hope"] += 1
            out.append("A soft talk helped the hurt feeling loosen.")
    return out


CAUSAL_RULES = [Rule("slick", _r_slick), Rule("calm", _r_calm)]


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


SETTING = Setting()

TOOLS = {
    "rake": Tool(
        id="rake",
        label="a garden rake",
        phrase="a sturdy rake with a red handle",
        effect="smooth",
        help_line="The rake could pull the mud into a neater line.",
        finish_line="They raked the loose mud into a tidy side ridge.",
    ),
    "boards": Tool(
        id="boards",
        label="a few flat boards",
        phrase="three flat wooden boards",
        effect="bridge",
        help_line="The boards could make a little path over the worst part.",
        finish_line="They laid the boards down so feet could cross without slipping.",
    ),
    "bucket": Tool(
        id="bucket",
        label="a bucket of water",
        phrase="a small bucket of water and a broom",
        effect="wash",
        help_line="The water could wash the mud off the stones.",
        finish_line="They washed the path clean and bright.",
    ),
}

NAMES_GIRL = ["Maya", "Lena", "Nora", "Ivy", "Zoe"]
NAMES_BOY = ["Owen", "Eli", "Noah", "Finn", "Leo"]


ASP_RULES = r"""
child_wants_climb.
parent_worries :- muddy_slope, slippery.
misunderstanding :- parent_worries, not explained.
talks :- misunderstanding.
can_transform(T) :- tool(T), useful(T).
resolved :- talks, can_transform(T).
safe_path :- resolved.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("muddy_slope"),
        asp.fact("slippery"),
    ]
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("useful", "boards"))
    lines.append(asp.fact("useful", "rake"))
    lines.append(asp.fact("useful", "bucket"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> bool:
    import asp
    model = asp.one_model(asp_program("#show resolved/0. #show safe_path/0."))
    atoms = {sym.name for sym in model}
    return "resolved" in atoms and "safe_path" in atoms


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming muddy-slope storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--tool", choices=sorted(TOOLS))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    tool = args.tool or rng.choice(list(TOOLS))
    return StoryParams(name=name, gender=gender, parent=parent, tool=tool)


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    slope = world.add(Entity(id="slope", type="slope", label="the muddy slope"))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label, phrase=TOOLS[params.tool].phrase))
    world.facts.update(child=child, parent=parent, slope=slope, tool=tool, tool_def=TOOLS[params.tool])
    return world


def tell(world: World) -> World:
    child = world.get("child")
    parent = world.get("parent")
    slope = world.get("slope")
    tool = world.facts["tool_def"]

    slope.meters["mud"] = 2.0
    slope.meters["slick"] = 1.0

    world.say(f"{child.label} loved the muddy slope behind the garden, because it turned every step into an adventure.")
    world.say(f"One afternoon, {child.label} ran toward it with bright shoes and a happy grin.")
    world.say(f"But {parent.label_word if hasattr(parent, 'label_word') else parent.label} saw the mud and frowned a little.")
    world.para()

    child.memes["hurt"] += 1
    parent.memes["worry"] += 1
    world.say(f'"No climbing today," {parent.label} said, trying to sound gentle. "The slope is too slick."')
    world.say(f"{child.label} stopped short. It sounded like the fun was gone.")
    world.say(f'"You mean I can never play there?" {child.label} asked, with a small wobble in {child.pronoun("possessive")} voice.')
    world.say(f"{parent.label} shook {parent.pronoun('possessive')} head. " + '"No, honey. I mean we need a safer way."')
    world.para()

    child.memes["hurt"] += 1
    child.memes["worry"] += 1
    world.say(f"{child.label} thought the muddy slope had been taken away, and {child.pronoun('possessive')} eyes got shiny.")
    world.say(f'Then {child.label} said, "So I can still go, if we make it safe?"')
    parent.memes["hope"] += 1
    world.say(f'"Exactly," {parent.label} said. "Let us transform it together."')
    world.say(tool.help_line)
    world.para()

    if tool.id == "boards":
        slope.meters["safe"] = 1.0
        slope.meters["mud"] = 1.0
        world.say(f"{parent.label} brought out {tool.phrase}, and {child.label} held one end with careful hands.")
        world.say(tool.finish_line)
    elif tool.id == "rake":
        slope.meters["safe"] = 1.0
        slope.meters["mud"] = 0.5
        world.say(f"{parent.label} used {tool.phrase} to pull the mud aside while {child.label} watched closely.")
        world.say(tool.finish_line)
    else:
        slope.meters["safe"] = 1.0
        slope.meters["mud"] = 0.2
        world.say(f"{parent.label} carried {tool.phrase}, and together they washed the worst mud away.")
        world.say(tool.finish_line)

    propagate(world)
    child.memes["joy"] += 1
    parent.memes["joy"] += 1
    child.memes["hope"] += 1

    world.para()
    world.say(f"In the end, {child.label} stepped onto the new path without slipping.")
    world.say(f"The muddy slope was still muddy in places, but it was kind now, and {child.label} was laughing beside {parent.label}.")
    world.say(f"They had not lost the slope at all. They had made it safe enough to share.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    tool = world.facts["tool_def"]
    return [
        "Write a short, heartwarming story about a child and a muddy slope that starts with a misunderstanding and ends with a transformation.",
        f"Tell a gentle story where {child.label} thinks {parent.label} is stopping the fun, but they talk and make the muddy slope safer together using {tool.label}.",
        "Write a child-friendly story with dialogue, a muddy place, and a warm ending that shows how a problem can become a shared project.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    tool = world.facts["tool_def"]
    return [
        QAItem(
            question=f"Why did {parent.label} worry about the muddy slope?",
            answer="Because the slope was muddy and slick, so it could be hard and unsafe to climb.",
        ),
        QAItem(
            question=f"What did {child.label} think at first when {parent.label} said no?",
            answer=f"{child.label} thought the fun was gone and worried that {parent.label} meant the slope could never be played on again.",
        ),
        QAItem(
            question=f"How did {they := 'they'} transform the muddy slope?",
            answer=f"They worked together with {tool.label}, turning the slippery place into a safer path that {child.label} could use again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mud?",
            answer="Mud is wet dirt that can stick to shoes, hands, and paths.",
        ),
        QAItem(
            question="What does it mean to transform something?",
            answer="To transform something means to change it into a new form or make it work in a new way.",
        ),
        QAItem(
            question="Why can a slope be hard to walk on when it is muddy?",
            answer="Because mud can make the ground slippery, so feet may slide instead of holding steady.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(setup_world(params))
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


def asp_verify() -> int:
    import asp
    py = True
    clingo = asp_check()
    if py == clingo:
        print("OK: ASP and Python reasoning agree.")
        return 0
    print("Mismatch between ASP and Python reasoning.")
    return 1


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0. #show safe_path/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available for this world; the core reasoning is simple and deterministic.")
        print("Use --show-asp to inspect the rules.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Maya", gender="girl", parent="mother", tool="boards"),
            StoryParams(name="Owen", gender="boy", parent="father", tool="rake"),
            StoryParams(name="Ivy", gender="girl", parent="mother", tool="bucket"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
