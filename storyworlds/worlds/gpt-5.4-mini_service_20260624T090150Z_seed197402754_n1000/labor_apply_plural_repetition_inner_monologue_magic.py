#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/labor_apply_plural_repetition_inner_monologue_magic.py
================================================================================================

A small animal-story world about careful labor, repeated applying, plural things,
and a little bit of magic.

Seed tale idea:
---
A young mouse wanted to help at the lantern workshop. The mouse had to apply
glow-paint to many paper lanterns, one by one, while repeating the same careful
steps. At first the job felt long and tiring, but an inner monologue helped the
mouse keep going. Then a small bit of magic made the work bright and joyful.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("labor", 0.0)
        self.meters.setdefault("applied", 0.0)
        self.meters.setdefault("gleam", 0.0)
        self.memes.setdefault("tired", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("pride", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "cat", "fox", "squirrel", "bear", "bird"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case] if self.type in {"bear"} else {"subject": "she", "object": "her", "possessive": "her"}[case] if self.type in {"rabbit"} else {"subject": "it", "object": "it", "possessive": "its"}[case] if self.type in {"bird"} else {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lantern workshop"
    affords: set[str] = field(default_factory=lambda: {"apply", "magic"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    plural: bool = False
    magical: bool = False
    applies_to: str = "lantern"
    boost: float = 1.0


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    tools: dict[str, Tool] = field(default_factory=dict)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.tools = copy.deepcopy(self.tools)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    animal: str
    helper: str
    tool: str
    count: int
    seed: Optional[int] = None


ANIMALS = {
    "mouse": {"names": ["Milo", "Mina", "Timo", "Luna"], "traits": ["tiny", "busy", "curious"]},
    "rabbit": {"names": ["Pip", "Poppy", "Tilly", "Nora"], "traits": ["gentle", "quick", "bright"]},
    "fox": {"names": ["Finn", "Fira", "Rolo", "Saffy"], "traits": ["clever", "spry", "lively"]},
    "squirrel": {"names": ["Nip", "Nina", "Moss", "Toby"], "traits": ["peppy", "small", "neat"]},
}

HELPERS = {
    "owl": {"names": ["Olwen", "Ollie"], "traits": ["wise", "patient"]},
    "hedgehog": {"names": ["Hana", "Hugo"], "traits": ["kind", "steady"]},
    "cat": {"names": ["Cleo", "Mittens"], "traits": ["calm", "watchful"]},
}

TOOLS = {
    "glow_paint": Tool(
        id="glow_paint",
        label="glow paint",
        phrase="a little pot of glow paint",
        plural=False,
        magical=True,
        applies_to="lanterns",
        boost=1.0,
    ),
    "sparkle_brush": Tool(
        id="sparkle_brush",
        label="sparkle brush",
        phrase="a soft sparkle brush",
        plural=False,
        magical=True,
        applies_to="lanterns",
        boost=1.0,
    ),
    "shine_balm": Tool(
        id="shine_balm",
        label="shine balm",
        phrase="a small tin of shine balm",
        plural=False,
        magical=True,
        applies_to="bells",
        boost=1.0,
    ),
}

TARGETS = {
    "lanterns": {"label": "paper lanterns", "plural": True, "count_min": 3, "count_max": 8},
    "bells": {"label": "tiny bells", "plural": True, "count_min": 2, "count_max": 6},
    "cups": {"label": "wooden cups", "plural": True, "count_min": 3, "count_max": 7},
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_apply(world: World) -> list[str]:
    out = []
    worker = world.get("worker")
    target = world.get("target")
    tool = world.get("tool")
    if worker.meters["labor"] < THRESHOLD:
        return out
    sig = ("apply",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["applied"] += 1
    worker.meters["applied"] += 1
    worker.meters["labor"] += tool.meters.get("boost", 1.0)
    worker.memes["hope"] += 0.5
    out.append(f"{worker.label} carefully applied {tool.label} to the {target.label}.")
    return out


def _r_magic(world: World) -> list[str]:
    out = []
    worker = world.get("worker")
    target = world.get("target")
    tool = world.get("tool")
    if tool.type != "tool" or not tool.memes.get("magical", 0):
        return out
    sig = ("magic",)
    if sig in world.fired:
        return out
    if target.meters["applied"] < THRESHOLD:
        return out
    world.fired.add(sig)
    target.meters["gleam"] += 1
    worker.meters["gleam"] += 1
    worker.memes["pride"] += 1
    out.append("A tiny magical sparkle hopped from the brush to the work and made it shine.")
    return out


CAUSAL_RULES = [Rule("apply", _r_apply), Rule("magic", _r_magic)]


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


def build_world(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    animal = ANIMALS[params.animal]
    helper = HELPERS[params.helper]
    tool = TOOLS[params.tool]
    target_info = TARGETS[tool.applies_to]

    worker = world.add(Entity(
        id="worker",
        kind="character",
        type=params.animal,
        label=params.name,
        traits=[animal["traits"][0], "helpful", "patient"],
    ))
    assistant = world.add(Entity(
        id="assistant",
        kind="character",
        type=params.helper,
        label=random.choice(helper["names"]),
        traits=[helper["traits"][0], "gentle"],
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        plural=False,
    ))
    tool_ent.memes["magical"] = 1.0 if tool.magical else 0.0
    target = world.add(Entity(
        id="target",
        kind="thing",
        type=tool.applies_to[:-1],
        label=target_info["label"],
        phrase=f"a set of {target_info['label']}",
        plural=True,
    ))

    world.tools[tool.id] = tool

    worker.meters["labor"] += 1
    worker.memes["hope"] += 0.5

    world.say(f"{worker.label} was a {animal['traits'][0]} little {params.animal} who loved to help in {world.setting.place}.")
    world.say(f"One day, {worker.label} and {assistant.label} found {tool.phrase} beside {target.label}.")
    world.say(f"{worker.label} wanted to do the job well, because the work was important and the {target.label} needed careful hands.")
    world.para()

    world.say(f"The task was simple, but long: apply the {tool.label} to each of the plural {target.label}, one by one.")
    world.say(f"{worker.label} looked at the row of {target.label} and thought, 'One, then two, then three. I can keep going.'")
    worker.meters["labor"] += float(params.count)

    if params.count >= 4:
        world.say(f"Again and again, {worker.label} lifted the brush, applied a neat little stroke, and set the piece aside.")
        worker.memes["tired"] += 1.0

    if worker.memes["tired"] >= THRESHOLD:
        world.say(f"{worker.label} felt a bit worn out, but the quiet inner voice said, 'Small steps still finish big work.'")
        world.say(f"So {worker.label} breathed in and kept the same rhythm: apply, pause, apply, pause.")

    propagate(world, narrate=True)
    world.para()

    if target.meters["gleam"] >= THRESHOLD:
        world.say(f"At last, the plural {target.label} glowed softly, and the whole workshop looked cheerful.")
        world.say(f"{worker.label} smiled, because the labor was done and the magic made the careful work feel grand.")
    else:
        world.say(f"At last, {worker.label} finished the last piece, and the row of plural {target.label} was ready for the next day.")
        world.say(f"{worker.label} stood tall, happy that the labor was finished well.")

    world.facts.update(
        worker=worker,
        assistant=assistant,
        tool=tool_ent,
        target=target,
        target_label=target.label,
        tool_cfg=tool,
        count=params.count,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short animal story about {f['worker'].label}, who must apply {f['tool_cfg'].label} to plural {f['target_label']}.",
        f"Tell a gentle story where a {f['worker'].type} does careful labor again and again and keeps going with an inner monologue.",
        f"Write a child-friendly animal story that includes magic and the repeated action of applying something one by one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    worker: Entity = f["worker"]
    assistant: Entity = f["assistant"]
    target: Entity = f["target"]
    tool_cfg: Tool = f["tool_cfg"]
    count = f["count"]
    return [
        QAItem(
            question=f"What job was {worker.label} doing in the workshop?",
            answer=f"{worker.label} was doing careful labor: {worker.pronoun('subject').capitalize()} was applying {tool_cfg.label} to the {target.label} one by one.",
        ),
        QAItem(
            question=f"Why did {worker.label} keep repeating the same little step?",
            answer=f"{worker.label} kept repeating it because there were plural {target.label}, and each one needed a careful application.",
        ),
        QAItem(
            question=f"What did {worker.label} think to {worker.pronoun('possessive')}self when the work felt long?",
            answer=f"{worker.label} thought, 'One, then two, then three. I can keep going.' That inner monologue helped {worker.label} keep working.",
        ),
        QAItem(
            question=f"How did magic help the job turn out?",
            answer=f"The magic made the finished work gleam, so the plural {target.label} looked bright and happy when the labor was done.",
        ),
        QAItem(
            question=f"How many times did the story say the task was done?",
            answer=f"The story described a row of {count} pieces and showed the work being applied again and again until it was finished.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "labor": (
        "What is labor?",
        "Labor is work that takes effort and time, like carrying, cleaning, building, or carefully finishing a job.",
    ),
    "apply": (
        "What does apply mean?",
        "To apply something means to put it on carefully, like brushing paint on paper or spreading balm on wood.",
    ),
    "plural": (
        "What does plural mean?",
        "Plural means more than one thing, like two apples, three chairs, or many lanterns.",
    ),
    "magic": (
        "What is magic in a story?",
        "Magic in a story is a special power that can make unusual things happen, like sparkling light or a tiny helpful glow.",
    ),
    "repetition": (
        "Why do stories repeat words sometimes?",
        "Stories repeat words to help children feel the rhythm, remember the steps, and hear how a character keeps trying.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for _, (q, a) in WORLD_KNOWLEDGE.items()]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: labor, apply, plural, repetition, inner monologue, and magic.")
    ap.add_argument("--name", choices=["Milo", "Mina", "Timo", "Luna", "Pip", "Poppy", "Tilly", "Nora", "Finn", "Fira", "Rolo", "Saffy", "Nip", "Nina", "Moss", "Toby"])
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--count", type=int)
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
    animal = args.animal or rng.choice(sorted(ANIMALS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    if tool == "shine_balm":
        helper = args.helper or "hedgehog"
    count = args.count if args.count is not None else rng.randint(3, 6)
    if count < 1:
        raise StoryError("count must be at least 1")
    names = ANIMALS[animal]["names"]
    name = args.name or rng.choice(names)
    return StoryParams(name=name, animal=animal, helper=helper, tool=tool, count=count)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
worker(X) :- animal(X).
tool(T) :- magical_tool(T).
target(P) :- plural_target(P).

needs_applied(T, P) :- tool(T), target(P).
done(T, P) :- needs_applied(T, P), applied(T, P).
shines(P) :- done(_, P), magic(T), applied(T, P).

#show needs_applied/2.
#show done/2.
#show shines/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for tid, tool in TOOLS.items():
        if tool.magical:
            lines.append(asp.fact("magical_tool", tid))
            lines.append(asp.fact("magic", tid))
    for tid, info in TARGETS.items():
        if info["plural"]:
            lines.append(asp.fact("plural_target", tid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    atoms = sorted(str(a) for a in model)
    ok = bool(atoms)
    if ok:
        print("OK: ASP rules loaded and produced a model.")
        return 0
    print("MISMATCH: ASP model was empty.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for animal in sorted(ANIMALS):
            for helper in sorted(HELPERS):
                for tool in sorted(TOOLS):
                    p = StoryParams(
                        name=ANIMALS[animal]["names"][0],
                        animal=animal,
                        helper=helper,
                        tool=tool,
                        count=4,
                        seed=base_seed,
                    )
                    samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
