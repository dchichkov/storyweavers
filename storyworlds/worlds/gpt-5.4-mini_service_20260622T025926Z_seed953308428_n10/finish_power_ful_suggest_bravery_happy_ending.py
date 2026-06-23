#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T025926Z_seed953308428_n10/finish_power_ful_suggest_bravery_happy_ending.py
===============================================================================================================

A small bedtime-story world about a child finishing one last cozy task, a
careful suggestion, and a brave choice that leads to a happy ending.

Seed premise:
- Use the words: finish, power-ful, suggest
- Features: Bravery, Happy Ending
- Style: Bedtime Story

The world centers on a child who wants to finish a bedtime project before sleep.
A gentle helper notices a problem, suggests a safer and more power-ful way, and
the child acts bravely to complete the task. The story varies by who the child
is, what the task is, what object is hard to reach or use, and which helpful
tool makes the finishing possible.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Goal:
    id: str
    label: str
    action: str
    finish_clause: str
    risk: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperTool:
    id: str
    label: str
    phrase: str
    power_word: str
    makes_possible: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    goal: str
    tool: str
    name: str
    child_type: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


GOALS = {
    "puzzle": Goal(
        id="puzzle",
        label="a moon puzzle",
        action="finish the moon puzzle",
        finish_clause="the last shining piece clicked into place",
        risk="the top corner was too high to reach",
        need="a careful lift",
        tags={"moon", "puzzle", "night"},
    ),
    "fort": Goal(
        id="fort",
        label="a blanket fort",
        action="finish the blanket fort",
        finish_clause="the last blanket draped down like a sleepy curtain",
        risk="the roof sagged without one more pillow",
        need="a steady hold",
        tags={"fort", "blanket", "bedtime"},
    ),
    "picture": Goal(
        id="picture",
        label="a picture of stars",
        action="finish the star picture",
        finish_clause="the final star sparkled right in the middle",
        risk="the crayons kept rolling away",
        need="a bright idea",
        tags={"picture", "stars", "art"},
    ),
    "song": Goal(
        id="song",
        label="a bedtime song card",
        action="finish the bedtime song card",
        finish_clause="the last line fit in neatly at the bottom",
        risk="the words kept getting mixed up",
        need="a calm voice",
        tags={"song", "words", "bedtime"},
    ),
}

TOOLS = {
    "stepstool": HelperTool(
        id="stepstool",
        label="a little step stool",
        phrase="a little step stool",
        power_word="power-ful",
        makes_possible={"puzzle", "fort"},
        tags={"stool", "climb", "brave"},
    ),
    "lamp": HelperTool(
        id="lamp",
        label="a soft lamp",
        phrase="a soft lamp",
        power_word="power-ful",
        makes_possible={"picture", "song"},
        tags={"light", "calm", "night"},
    ),
    "pillowstack": HelperTool(
        id="pillowstack",
        label="a pillow stack",
        phrase="a pillow stack",
        power_word="power-ful",
        makes_possible={"fort", "song"},
        tags={"pillow", "support", "bedtime"},
    ),
    "tray": HelperTool(
        id="tray",
        label="a sturdy tray",
        phrase="a sturdy tray",
        power_word="power-ful",
        makes_possible={"puzzle", "picture"},
        tags={"tray", "steady", "careful"},
    ),
}

TRAITS = ["brave", "gentle", "curious", "sleepy", "steady"]
GIRL_NAMES = ["Mia", "Luna", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Ben", "Finn", "Theo", "Max"]


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


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    goal = world.get("goal")
    tool = world.get("tool")
    if child.memes["determination"] < THRESHOLD:
        return out
    if goal.meters["progress"] < 2:
        return out
    sig = ("finish", goal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goal.meters["finished"] = 1.0
    child.memes["pride"] += 1
    out.append("__finished__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["tired"] < THRESHOLD:
        return out
    sig = ("settle", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sleepy"] += 1
    out.append("__settled__")
    return out


RULES = [Rule("finish", _r_finish), Rule("settle", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_finish(goal: Goal, tool: HelperTool) -> bool:
    return goal.id in tool.makes_possible


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for gid, goal in GOALS.items():
        for tid, tool in TOOLS.items():
            if can_finish(goal, tool):
                out.append((gid, tid))
    return out


def explain_rejection(goal: Goal, tool: HelperTool) -> str:
    return (
        f"(No story: {tool.label} is not a good fit for {goal.label}. "
        f"Try a tool that can really help with that task.)"
    )


def setup_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, role="helper"))
    goal = world.add(Entity(id="goal", kind="thing", type="goal", label=GOALS[params.goal].label, phrase=GOALS[params.goal].action))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=TOOLS[params.tool].label, phrase=TOOLS[params.tool].phrase, tags=set(TOOLS[params.tool].tags)))
    child.memes["bravery"] = 1.0 if params.trait == "brave" else 0.0
    child.memes["determination"] = 0.0
    child.meters["tired"] = 0.0
    goal.meters["progress"] = 0.0
    world.facts["goal_cfg"] = GOALS[params.goal]
    world.facts["tool_cfg"] = TOOLS[params.tool]
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["goal"] = goal
    world.facts["tool"] = tool
    return world


def tell(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    goal = world.get("goal")
    tool = world.get("tool")
    goal_cfg: Goal = world.facts["goal_cfg"]
    tool_cfg: HelperTool = world.facts["tool_cfg"]

    child.memes["joy"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"{child.label} was a little {child.type} with a brave heart, and at bedtime {child.pronoun()} wanted to {goal_cfg.action}."
    )
    world.say(
        f"{goal_cfg.finish_clause}, but {goal_cfg.risk}. {child.label_word if child.id == 'child' else child.label} sat very still and thought about how to make it to the end."
    )

    world.para()
    child.memes["worry"] += 1
    world.say(
        f"Then {helper.label} came near and gave a gentle {tool_cfg.power_word} {tool_cfg.label} to help."
    )
    world.say(
        f'"I can {tool_cfg.power_word.lower()}ly {goal_cfg.need}," {helper.label_word} {helper.pronoun()} said. "Let\'s use {tool_cfg.phrase} and finish together."'
    )

    child.memes["determination"] += 1
    goal.meters["progress"] += 1
    world.say(
        f"{child.label} nodded, took a brave breath, and held on. With {tool_cfg.phrase}, {goal_cfg.finish_clause}."
    )
    goal.meters["progress"] += 1
    propagate(world, narrate=False)
    if goal.meters["finished"] >= THRESHOLD:
        world.say(
            f"The child smiled at the finished {goal_cfg.label}, and the room felt soft and safe."
        )
        child.meters["tired"] += 1
        propagate(world, narrate=False)
        if child.memes["sleepy"] >= THRESHOLD:
            world.para()
            world.say(
                f"At last, {helper.label} tucked the little one in, and the tiny day ended with a happy ending."
            )

    world.facts["finished"] = goal.meters["finished"] >= THRESHOLD
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["goal"] = goal
    world.facts["tool"] = tool


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goal_cfg: Goal = f["goal_cfg"]
    tool_cfg: HelperTool = f["tool_cfg"]
    return [
        f'Write a bedtime story for a small child who wants to finish {goal_cfg.label} with help from {tool_cfg.phrase}. Include the word "finish".',
        f'Tell a gentle story where {child.label} is brave, a helper suggests a {tool_cfg.power_word} way to keep going, and the ending is happy.',
        f'Write a cozy bedtime story that includes the words "power-ful" and "suggest" and ends with something finished.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    goal_cfg: Goal = f["goal_cfg"]
    tool_cfg: HelperTool = f["tool_cfg"]
    goal = f["goal"]
    qa = [
        QAItem(
            question=f"What did {child.label} want to finish before bedtime?",
            answer=f"{child.label} wanted to {goal_cfg.action}. It was a cozy bedtime task, and the child kept thinking about the last step needed to reach the end.",
        ),
        QAItem(
            question=f"What did {helper.label} suggest to help?",
            answer=f"{helper.label} suggested using {tool_cfg.phrase}. It was a {tool_cfg.power_word} idea because it made the hard part safe and easy to manage.",
        ),
        QAItem(
            question=f"Why did {child.label} need a brave heart?",
            answer=f"{goal_cfg.risk.capitalize()}. {child.label} had to be brave enough to try the helpful plan and keep going instead of giving up.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{goal_cfg.finish_clause}, so the goal was finished. The room ended calm and cozy, which makes the ending feel happy and complete.",
        ),
    ]
    if f.get("finished"):
        qa.append(
            QAItem(
                question=f"How did {tool_cfg.label} help {child.label} finish the job?",
                answer=f"{tool_cfg.phrase} gave {child.label} the extra reach and steadiness needed to finish. Because of that, the child could keep going bravely and see the last piece through.",
            )
        )
    return qa


KNOWLEDGE = {
    "brave": [
        QAItem(
            question="What does it mean to be brave?",
            answer="Being brave means doing something hard or a little scary even when your heart is beating fast. A brave child keeps going and asks for help when needed.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why do bedtime stories feel calm?",
            answer="Bedtime stories feel calm because they are soft, quiet, and safe. They help a child slow down and get ready for sleep.",
        )
    ],
    "pillow": [
        QAItem(
            question="What is a pillow for?",
            answer="A pillow is soft and helps your head rest comfortably. It makes a bed feel cozy and warm.",
        )
    ],
    "light": [
        QAItem(
            question="What is a lamp for?",
            answer="A lamp gives light so you can see in a dark room. A soft lamp can make a bedtime corner feel peaceful.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["tool_cfg"].tags) | set(f["goal_cfg"].tags)
    tags.add("brave")
    tags.add("bedtime")
    if "pillow" in tags:
        pass
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_invalid(goal: Goal, tool: HelperTool) -> str:
    return f"(No story: {tool.label} cannot really help with {goal.label}, so the bedtime turn would not make sense.)"


ASP_RULES = r"""
valid(G, T) :- goal(G), tool(T), helps(T, G).
finished(G) :- progress(G, P), P >= 2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        for tg in sorted(goal.tags):
            lines.append(asp.fact("goal_tag", gid, tg))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(tool.makes_possible):
            lines.append(asp.fact("helps", tid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set != clingo_set:
        rc = 1
        print("MISMATCH between Python and ASP valid combos")
        print(" python only:", sorted(python_set - clingo_set))
        print(" asp only:", sorted(clingo_set - python_set))
    else:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")

    # Real smoke tests required by the contract.
    test_args = build_parser().parse_args([])
    seeds = [777, 778, 779]
    seen_texts: set[str] = set()
    for sd in seeds:
        params = resolve_params(test_args, random.Random(sd))
        params.seed = sd
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        seen_texts.add(sample.story)
    if len(seen_texts) < 2:
        raise StoryError("smoke test produced duplicate stories")

    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    _ = sample.to_json()
    print("OK: default-generation smoke tests, QA-ready generation, and JSON serialization passed.")

    # -n 3 --seed 777 --qa path
    args = build_parser().parse_args(["-n", "3", "--seed", "777", "--qa"])
    base = args.seed or 0
    triples = []
    for i in range(args.n):
        p = resolve_params(args, random.Random(base + i))
        triples.append(generate(p))
    qa_hashes = set()
    for s in triples:
        qa_hashes.add(tuple((q.question, q.answer) for q in s.story_qa[:2]))
    if len(qa_hashes) < 2:
        raise StoryError("duplicate QA across generated samples")
    print("OK: multi-sample QA smoke test passed.")

    # --all when the combo count is small, but still exercise it lightly.
    if len(valid_combos()) <= 20:
        all_samples = [generate(StoryParams(goal=g, tool=t, name="Mia", child_type="girl", helper="Mom", helper_type="mother", trait="brave")) for g, t in valid_combos()[:3]]
        if not all_samples:
            raise StoryError("--all smoke test failed")
        print("OK: curated/--all-style smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a child finishes a cozy task with brave help.")
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.goal is None or c[0] == args.goal)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    goal, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    child_type = args.child_type or ("girl" if name in GIRL_NAMES else "boy")
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    helper = args.helper or ("Mom" if helper_type == "mother" else "Dad")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(goal=goal, tool=tool, name=name, child_type=child_type, helper=helper, helper_type=helper_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.goal not in GOALS or params.tool not in TOOLS:
        raise StoryError("invalid StoryParams")
    goal_cfg = GOALS[params.goal]
    tool_cfg = TOOLS[params.tool]
    if not can_finish(goal_cfg, tool_cfg):
        raise StoryError(explain_invalid(goal_cfg, tool_cfg))
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper, role="helper"))
    goal = world.add(Entity(id="goal", kind="thing", type="goal", label=goal_cfg.label, phrase=goal_cfg.action))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, tags=set(tool_cfg.tags)))
    child.memes["bravery"] = 1.0 if params.trait == "brave" else 0.0
    child.memes["determination"] = 0.0
    child.memes["pride"] = 0.0
    goal.meters["progress"] = 0.0
    goal.meters["finished"] = 0.0
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["goal"] = goal
    world.facts["tool"] = tool
    world.facts["goal_cfg"] = goal_cfg
    world.facts["tool_cfg"] = tool_cfg
    tell(world)
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
    StoryParams(goal="fort", tool="stepstool", name="Mia", child_type="girl", helper="Mom", helper_type="mother", trait="brave"),
    StoryParams(goal="picture", tool="lamp", name="Noah", child_type="boy", helper="Dad", helper_type="father", trait="gentle"),
    StoryParams(goal="song", tool="pillowstack", name="Luna", child_type="girl", helper="Mom", helper_type="mother", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (goal, tool) combos:")
        for g, t in asp_valid_combos():
            print(f"  {g:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.goal} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
