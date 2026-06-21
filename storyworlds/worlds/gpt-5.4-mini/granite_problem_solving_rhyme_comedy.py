#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/granite_problem_solving_rhyme_comedy.py
=======================================================================

A tiny comedy storyworld about kids, a stubborn granite block, and a silly
problem-solving plan with a rhyme-based nudge.

The world is intentionally small:
- a child wants to do something fun;
- a heavy granite object blocks the way;
- a helper suggests a rhyme to keep the plan in mind;
- the children solve the problem with a tool, teamwork, and a funny ending.

The story is built from simulated world state, not from one frozen paragraph.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    task: str
    sound: str
    finish: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    heavy: int
    stubborn: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rhyme:
    id: str
    line1: str
    line2: str
    line3: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    rock = world.get("granite")
    if hero.memes["effort"] < THRESHOLD:
        return out
    if rock.meters["moved"] >= THRESHOLD:
        return out
    sig = ("stuck",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rock.meters["stuck"] += 1
    hero.memes["frustration"] += 1
    out.append("__stuck__")
    return out


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    rock = world.get("granite")
    tool = world.get("tool")
    if tool.meters["used"] < THRESHOLD or rock.meters["moved"] >= THRESHOLD:
        return out
    sig = ("progress",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rock.meters["moved"] += 1
    rock.meters["cracked"] += 1
    hero.memes["hope"] += 1
    out.append("__progress__")
    return out


CAUSAL_RULES = [
    Rule("stuck", "physical", _r_stuck),
    Rule("progress", "physical", _r_progress),
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


def sufficient(tool: Tool, obstacle: Obstacle) -> bool:
    return tool.power >= obstacle.heavy


def problem_is_reasonable(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.label == "granite block" and tool.power > 0


@dataclass
@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    rhyme: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "yard": Setting("yard", "the backyard", "open the gate", "thunk-thunk", "the gate swings free"),
    "shed": Setting("shed", "the shed", "reach the ladder", "clink-clank", "the ladder comes loose"),
    "patio": Setting("patio", "the patio", "move the flower cart", "scritch-scrape", "the path clears"),
}

OBSTACLES = {
    "granite": Obstacle(
        "granite",
        "granite block",
        "a big granite block",
        heavy=3,
        stubborn="it sat like a sleepy mountain",
        tags={"granite", "problem"},
    )
}

TOOLS = {
    "lever": Tool(
        "lever",
        "wooden lever",
        "a long wooden lever",
        "pry",
        power=3,
        tags={"tool", "problem"},
    ),
    "rollers": Tool(
        "rollers",
        "rollers and a rope",
        "rollers and a rope",
        "roll",
        power=4,
        tags={"tool", "problem"},
    ),
    "cart": Tool(
        "cart",
        "a little cart",
        "a little cart",
        "push",
        power=2,
        tags={"tool", "problem"},
    ),
}

RHYMES = {
    "push": Rhyme(
        "push",
        "Push and hush, don't rush-rush-rush.",
        "Tip and grip, then take a tiny trip.",
        "One more shove and off it goes, as easy as a giggle.",
        tags={"rhyme", "comedy"},
    ),
    "roll": Rhyme(
        "roll",
        "Roll and stroll, let the stone unroll.",
        "One, two, three, the granite starts to flee.",
        "The block goes bump, then gives a comic little thump.",
        tags={"rhyme", "comedy"},
    ),
    "pry": Rhyme(
        "pry",
        "Pry and sigh, but try-try-try.",
        "Tap and gap, then clap for that.",
        "A wobbly wiggle, followed by a silly jiggle.",
        tags={"rhyme", "comedy"},
    ),
}


class _RngNames:
    GIRLS = ["Mia", "Lily", "Nora", "Zoe", "Ava", "June"]
    BOYS = ["Tom", "Ben", "Max", "Leo", "Eli", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obstacle in OBSTACLES.items():
            for tid, tool in TOOLS.items():
                if problem_is_reasonable(obstacle, tool):
                    combos.append((sid, oid, tid))
    return combos


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    s, o, t, r = f["setting"], f["obstacle"], f["tool"], f["rhyme"]
    return [
        f'Write a funny problem-solving story for a young child that includes the word "{o.label}" and a rhyme.',
        f"Tell a comedy story where {f['hero'].id} and {f['helper'].id} try to move {o.phrase} with {t.phrase}.",
        f'Write a short story with rhyme, teamwork, and a granite obstacle in {s.place}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    rhyme = f["rhyme"]
    qa = [
        (
            "What problem did the characters have?",
            f"They needed to move {obstacle.phrase}, but it was too heavy to budge by hand. {obstacle.stubborn.capitalize()}, so they had to think up a better plan.",
        ),
        (
            "How did they solve the problem?",
            f"They used {tool.phrase} and followed the rhyme to work together. That gave them a steady plan instead of a silly tug-of-war.",
        ),
        (
            "How did the ending feel?",
            f"It felt funny and happy. The granite moved at last, and the children laughed because their big tough problem turned into a small clink and a grin.",
        ),
    ]
    if f.get("moved"):
        qa.append((
            f"What happened when {hero.id} and {helper.id} used the tool?",
            f"The granite block slid at last, and {f['setting'].finish} {world.setting.task} was possible again. The rhyme kept them in step while they pushed.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["obstacle"].tags) | set(world.facts["tool"].tags) | set(world.facts["rhyme"].tags)
    out = []
    if "granite" in tags:
        out.append(("What is granite?", "Granite is a very hard rock. People use it for counters, steps, and strong blocks because it does not break easily."))
    if "tool" in tags:
        out.append(("Why do people use tools?", "People use tools to make hard jobs easier. A tool can help lift, pry, push, or move something that is too hard to move by hand."))
    if "rhyme" in tags:
        out.append(("What is a rhyme?", "A rhyme is a little song-like pattern where words sound alike. Rhymes can help you remember a plan, and they can sound funny too."))
    if "problem" in tags:
        out.append(("What should you do when something is stuck?", "Stop and think of a safer plan. Try teamwork, use the right tool, and ask a grown-up if the job is too big."))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(setting: Setting, obstacle: Obstacle, tool: Tool, rhyme: Rhyme,
         hero: str, hero_gender: str, helper: str, helper_gender: str,
         parent: str) -> World:
    world = World(setting)
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    helper_ent = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    parent_ent = world.add(Entity(id=parent, kind="character", type="parent", label="the parent"))
    rock = world.add(Entity(id="granite", type="stone", label=obstacle.label))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label))
    world.facts.update(setting=setting, obstacle=obstacle, tool=tool, rhyme=rhyme, hero=h, helper=helper_ent, parent=parent_ent)

    h.memes["curiosity"] += 1
    helper_ent.memes["humor"] += 1
    world.say(
        f"On a bright day in {setting.place}, {h.id} and {helper_ent.id} found {obstacle.phrase} blocking {setting.task}."
    )
    world.say(
        f"{obstacle.stubborn.capitalize()} {h.id} frowned, and {helper_ent.id} said, "
        f'"Hmm, that rock is a regular pebble of trouble."'
    )
    world.para()
    world.say(
        f'{helper_ent.id} sang, "{rhyme.line1} {rhyme.line2}" '
        f"and both of them chuckled at the silly tune."
    )
    h.memes["effort"] += 1
    helper_ent.memes["effort"] += 1
    world.say(
        f'Then {h.id} and {helper_ent.id} got {tool.phrase}, took a breath, and tried to {tool.action} the granite.'
    )
    if sufficient(tool, obstacle):
        rock.meters["moved"] += 1
        tool_ent.meters["used"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"The plan worked with a scrape and a squeak. {rhyme.line3} {setting.finish.capitalize()}."
        )
        world.say(
            f"{h.id} did a tiny victory dance, and {helper_ent.id} bowed like a very serious comedian."
        )
        world.say(
            f"The granite was still granite, of course, but now it sat in the right place, out of the way."
        )
        moved = True
    else:
        tool_ent.meters["used"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"The {tool.label} only made a funny wobble. {h.id} nearly toppled sideways, and {helper_ent.id} said, "
            f'"That plan was heavy on hope and light on muscle."'
        )
        world.say(
            f"So they waved for {parent_ent.label_word}, who came with a better idea and a bigger grin."
        )
        moved = False

    world.facts["moved"] = moved
    return world


CURATED = [
    StoryParams("yard", "granite", "rollers", "roll", "Mia", "girl", "Tom", "boy", "mother"),
    StoryParams("patio", "granite", "lever", "pry", "Leo", "boy", "Nora", "girl", "father"),
    StoryParams("shed", "granite", "cart", "push", "Ava", "girl", "Sam", "boy", "mother"),
]


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return f"(No story: this world only tells granite-move stories, and the chosen tool must be a real problem-solving tool.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: granite, problem solving, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting or args.obstacle or args.tool:
        combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.obstacle is None or c[1] == args.obstacle) and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid granite story matches the given options.)")
    setting, obstacle, tool = rng.choice(combos)
    rhyme = args.rhyme or rng.choice(sorted(RHYMES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(_RngNames.GIRLS if gender == "girl" else _RngNames.BOYS)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper = args.helper or rng.choice(_RngNames.BOYS if helper_gender == "boy" else _RngNames.GIRLS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, obstacle, tool, rhyme, name, gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        OBSTACLES[params.obstacle],
        TOOLS[params.tool],
        RHYMES[params.rhyme],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


ASP_RULES = r"""
problem(Setting, Obstacle, Tool) :- setting(Setting), obstacle(Obstacle), tool(Tool), granite_problem(Obstacle), solves(Tool, Obstacle).
granite_problem(granite).
solves(rollers, granite).
solves(lever, granite).
solves(cart, granite).
valid(Setting, Obstacle, Tool) :- problem(Setting, Obstacle, Tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("granite_problem", oid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("solves", tid, "granite"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible granite story combos.")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.setting}, {p.tool}, {p.rhyme}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
