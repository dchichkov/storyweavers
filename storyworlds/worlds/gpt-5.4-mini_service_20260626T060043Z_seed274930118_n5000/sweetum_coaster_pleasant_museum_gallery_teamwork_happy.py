#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sweetum_coaster_pleasant_museum_gallery_teamwork_happy.py
================================================================================================

A small fairy-tale storyworld set in a museum gallery.

Seed tale used to build the world:
---
In a pleasant museum gallery, a tiny sweetum named Pip wanted to help with the
moon-window display. Pip found a little coaster that could safely carry a shiny
glass cup from one room to another, but the coaster was too small for one helper
to manage alone. A kind guide noticed Pip's worry and invited another helper to
join in. Together they shared the coaster, lifted carefully, and moved the cup
without a single wobble. The gallery stayed pleasant, the sweetum felt proud,
and everyone ended with a happy smile.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the museum gallery"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    support_needed: int
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    supports: set[str]
    fits: set[str]
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_drop_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("wobble", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.caretaker != actor.id:
                continue
            sig = ("risk", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["risk"] = item.meters.get("risk", 0.0) + 1
            out.append(f"The {item.label} trembled in the {actor.id}'s hands.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("joined") and not world.facts.get("shared_tool") in world.fired:
        sig = ("shared_tool",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The helpers worked as one, and the shared tool felt easy to hold.")
    return out


CAUSAL_RULES = [
    Rule("drop_risk", _r_drop_risk),
    Rule("teamwork", _r_teamwork),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="the museum gallery", affords={"carry", "share", "clean"})

TASKS = {
    "carry": Task(
        id="carry",
        verb="carry the glass cup",
        gerund="carrying the glass cup",
        rush="hurry to lift the glass cup",
        risk="a wobble could send the cup sliding",
        support_needed=2,
        keyword="coaster",
        tags={"coaster", "share"},
    ),
    "share": Task(
        id="share",
        verb="share the coaster",
        gerund="sharing the coaster",
        rush="reach for the coaster alone",
        risk="one helper cannot balance it well",
        support_needed=2,
        keyword="sharing",
        tags={"sharing"},
    ),
    "clean": Task(
        id="clean",
        verb="clean the display",
        gerund="cleaning the display",
        rush="rush to wipe the frame",
        risk="a careless swipe could smear the shine",
        support_needed=2,
        keyword="pleasant",
        tags={"pleasant"},
    ),
}

PRIZES = {
    "cup": Prize(
        label="glass cup",
        phrase="a shiny glass cup",
        type="cup",
        fragile=True,
        tags={"glass", "cup"},
    ),
    "lantern": Prize(
        label="moon lantern",
        phrase="a pale moon lantern",
        type="lantern",
        fragile=True,
        tags={"light", "moon"},
    ),
    "vase": Prize(
        label="blue vase",
        phrase="a blue vase with gold vines",
        type="vase",
        fragile=True,
        tags={"vase", "blue"},
    ),
}

TOOLS = [
    Tool(
        id="coaster",
        label="coaster",
        phrase="a little coaster",
        supports={"carry", "share", "clean"},
        fits={"cup", "lantern", "vase"},
    ),
    Tool(
        id="cloth",
        label="soft cloth",
        phrase="a soft cloth",
        supports={"clean"},
        fits={"cup", "lantern", "vase"},
    ),
    Tool(
        id="tray",
        label="silver tray",
        phrase="a silver tray",
        supports={"carry", "share"},
        fits={"cup", "lantern", "vase"},
    ),
]

HERO_NAMES = ["Pip", "Mira", "Lumi", "Nell", "Toby", "Clover"]
HELPER_NAMES = ["Jun", "Bee", "Wren", "Faye", "Dawn", "Ivo"]


@dataclass
class StoryParams:
    task: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def task_needs_teamwork(task: Task, prize: Prize) -> bool:
    return task.support_needed >= 2 and prize.fragile


def select_tool(task: Task, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.supports and prize.type in tool.fits:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for t in TASKS.values():
        for p in PRIZES.values():
            if task_needs_teamwork(t, p) and select_tool(t, p):
                combos.append((t.id, p.type))
    return combos


def explain_rejection(task: Task, prize: Prize) -> str:
    if not task_needs_teamwork(task, prize):
        return "(No story: this task does not need teamwork, so the fairy-tale turn would be too thin.)"
    return f"(No story: no tool in the gallery can fairly support {task.gerund} with {prize.phrase}.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Entity, task: Task, prize: Prize) -> None:
    world.say(
        f"In {world.setting.place}, a tiny sweetum named {hero.id} walked softly beneath the painted arches."
    )
    world.say(
        f"{hero.id} loved {task.gerund}, and the gallery looked very pleasant that morning."
    )
    world.say(
        f"Near a moonlit case, {hero.id} noticed {prize.phrase} waiting like a treasure from an old fairy tale."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1


def trouble(world: World, hero: Entity, helper: Entity, task: Task, prize: Prize) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.para()
    world.say(
        f"{hero.id} wanted to {task.verb}, but {task.risk}."
    )
    world.say(
        f"When {hero.id} tried to {task.rush}, the little coaster wobbled and the cup began to slip."
    )
    hero.meters["wobble"] = hero.meters.get("wobble", 0.0) + 1
    propagate(world)


def offer(world: World, helper: Entity, hero: Entity, task: Task, prize: Prize, tool: Tool) -> None:
    world.say(
        f"Then {helper.id} came with a kind smile and said, \"Let us share the {tool.label}.\""
    )
    world.say(
        f"Their teamwork made the plan feel gentle instead of hard."
    )
    world.facts["joined"] = True
    world.facts["shared_tool"] = tool.id


def finish(world: World, hero: Entity, helper: Entity, task: Task, prize: Prize, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    helper.memes["sharing"] = helper.memes.get("sharing", 0.0) + 1
    world.para()
    world.say(
        f"Side by side, {hero.id} and {helper.id} lifted together, shared the {tool.label}, and steadied {prize.phrase}."
    )
    world.say(
        f"The cup reached its new place without a wobble, and the pleasant gallery grew quiet with relief."
    )
    world.say(
        f"{hero.id} beamed like a little star, {helper.id} laughed, and the day ended with a happy ending."
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero, kind="character", type="sweetum", label="sweetum"))
    helper = world.add(Entity(id=params.helper, kind="character", type="guide", label="helper"))
    prize = PRIZES[params.prize]
    task = TASKS[params.task]
    tool = select_tool(task, prize)
    if tool is None:
        raise StoryError(explain_rejection(task, prize))

    world.facts.update(hero=hero, helper=helper, prize=prize, task=task, tool=tool)

    intro(world, hero, helper, task, prize)
    trouble(world, hero, helper, task, prize)
    offer(world, helper, hero, task, prize, tool)
    finish(world, hero, helper, task, prize, tool)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    prize: Prize = f["prize"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a fairy-tale story set in a museum gallery about a sweetum named {hero.id} and the word "coaster".',
        f"Tell a gentle story where {hero.id} wants to {task.verb} with {prize.phrase}, and {helper.id} helps by sharing.",
        f'Write a child-friendly happy ending story that includes Teamwork and Sharing in {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Prize = f["prize"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the sweetum in the museum gallery story?",
            answer=f"The sweetum was {hero.id}, and {helper.id} helped with the work.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with {prize.phrase}?",
            answer=f"{hero.id} wanted to {task.verb}. That was tricky because the cup was fragile.",
        ),
        QAItem(
            question=f"How did the two helpers solve the problem?",
            answer=f"They shared the {tool.label} and used teamwork so {prize.phrase} could move safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with the gallery calm and the helpers proud of what they did together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help each other reach the same goal.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use the same thing in a fair way.",
        ),
        QAItem(
            question="Why is a museum gallery usually quiet?",
            answer="A museum gallery is usually quiet so people can look carefully at the art and objects.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_needs_teamwork(T,P) :- task(T), prize(P), support_needed(T,2), fragile(P).
tool_fits(TL,T,P) :- task(T), prize(P), tool(TL), supports(TL,T), fits(TL,P), task_needs_teamwork(T,P).
valid_story(T,P) :- task_needs_teamwork(T,P), tool_fits(_,T,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("support_needed", tid, t.support_needed))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.supports):
            lines.append(asp.fact("supports", tool.id, t))
        for p in sorted(tool.fits):
            lines.append(asp.fact("fits", tool.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld in a museum gallery about teamwork and sharing.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
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
    if args.task and args.prize:
        if (args.task, args.prize) not in valid_combos():
            raise StoryError(explain_rejection(TASKS[args.task], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.task is None or c[0] == args.task)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    task, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if helper == hero:
        helper = rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(task=task, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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
    StoryParams(task="carry", prize="cup", hero="Pip", helper="Mira"),
    StoryParams(task="share", prize="lantern", hero="Lumi", helper="Wren"),
    StoryParams(task="clean", prize="vase", hero="Nell", helper="Faye"),
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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible task/prize combos:")
        for t, p in combos:
            print(f"  {t} {p}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.task} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
