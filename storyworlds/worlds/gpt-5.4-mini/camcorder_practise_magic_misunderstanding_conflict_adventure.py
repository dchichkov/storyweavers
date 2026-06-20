#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/camcorder_practise_magic_misunderstanding_conflict_adventure.py
===============================================================================================

A small standalone storyworld for a TinyStories-style adventure about a
camcorder, a practise plan, a little magic trick, and a misunderstanding that
causes a conflict before everything is set right.

The domain is built around two children and a trusted grown-up in a simple
adventure frame: they want to record a pretend magic scene with a camcorder,
but one child misunderstands the practice, the other gets upset, and a calm
helper turns the confusion into a better plan. The world model tracks physical
state in meters and emotional state in memes, and the prose is driven by those
changes rather than by a fixed paragraph template.

This file is self-contained and stdlib-only.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not isinstance(self.meters, dict):
            self.meters = dict(self.meters)
        if not isinstance(self.memes, dict):
            self.memes = dict(self.memes)

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
class Theme:
    id: str
    scene: str
    rig: str
    title1: str
    title2: str
    goal: str
    hideout: str
    ending: str

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
class Prop:
    id: str
    label: str
    phrase: str
    glow: str = ""
    makes_magic: bool = False
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
class Problem:
    id: str
    label: str
    phrase: str
    effect: str
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
@dataclass
class StoryParams:
    theme: str
    prop: str
    problem: str
    fix: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    helper: str
    helper_gender: str
    trait: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _rule_conflict(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("misunderstood", 0.0) >= THRESHOLD and friend.memes.get("hurt", 0.0) >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
            friend.memes["conflict"] = friend.memes.get("conflict", 0.0) + 1
            out.append("__conflict__")
    return out


def _rule_still(world: World) -> list[str]:
    out = []
    helper = world.entities.get("helper")
    if helper and helper.memes.get("calm", 0.0) >= THRESHOLD:
        sig = ("still",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").meters["quiet"] = 1.0
            out.append("__still__")
    return out


CAUSAL_RULES = [_rule_conflict, _rule_still]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            msgs = rule(world)
            if msgs:
                changed = True
                produced.extend([m for m in msgs if not m.startswith("__")])
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reasonableness_ok(prop: Prop, problem: Problem, fix: Fix) -> bool:
    return prop.makes_magic and "conflict" in problem.tags and fix.sense >= 2 and fix.power >= 1


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def outcome_of(params: StoryParams) -> str:
    if params.fix not in FIXES:
        return "?"
    fix = FIXES[params.fix]
    if fix.power >= 2:
        return "resolved"
    return "strained"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.makes_magic:
            lines.append(asp.fact("makes_magic", pid))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
        lines.append(asp.fact("power", fid, fx.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
magic_hazard(P) :- prop(P), makes_magic(P).
valid(T, P, R, F) :- theme(T), prop(P), problem(R), fix(F), magic_hazard(P), sensible(F).
"""

def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(v[0] for v in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


THEMES = {
    "adventure": Theme(
        "adventure",
        "a moonlit clearing near an old hill fort",
        "The blanket fort became a little base camp, a cardboard cave hid treasure maps, and a painted star marked the path.",
        "Captain",
        "Scout",
        "the secret gate",
        "the shadowy tunnel under the fort",
        "They went on with a new, safer plan.",
    ),
    "island": Theme(
        "island",
        "a windy island camp",
        "The tents stood like tiny towers, a rope marked the trail, and a crate held pretend supplies.",
        "Explorer",
        "Guide",
        "the hidden cove",
        "the rocky path below the lookout",
        "They sailed on with a calmer plan.",
    ),
    "cave": Theme(
        "cave",
        "a torchlit cave camp",
        "A pillow pile became a ridge, a blanket tunnel curled into a passage, and a paper moon glowed overhead.",
        "Leader",
        "Trailmate",
        "the crystal chamber",
        "the dark arch behind the curtains",
        "They kept exploring the safe way.",
    ),
}

PROPS = {
    "camcorder": Prop("camcorder", "camcorder", "a camcorder", glow="", makes_magic=False, tags={"camcorder"}),
    "sparkle_camcorder": Prop("sparkle_camcorder", "camcorder", "a camcorder with a blinking light", glow="blinked blue and gold", makes_magic=True, tags={"camcorder", "magic"}),
    "wand": Prop("wand", "wand", "a silver wand", glow="shone like a star", makes_magic=True, tags={"magic"}),
}

PROBLEMS = {
    "misunderstanding": Problem("misunderstanding", "misunderstanding", "a misunderstanding", "thought the practice was real", tags={"misunderstanding"}),
    "conflict": Problem("conflict", "conflict", "a conflict", "got upset and argued", tags={"conflict"}),
    "mixup": Problem("mixup", "mix-up", "a mix-up", "took the wrong way", tags={"misunderstanding"}),
}

FIXES = {
    "explain": Fix("explain", 3, 2, "explained the practice plan and showed the real magic step by step", "tried to explain, but the confusion stayed too big", "explained the practice plan clearly", tags={"talk"}),
    "reset": Fix("reset", 2, 2, "counted to three, reset the scene, and practised the trick again slowly", "tried to reset the scene, but the upset had grown too big", "counted to three and practised the trick again slowly", tags={"practice"}),
    "flashlight": Fix("flashlight", 1, 1, "turned on a flashlight and hoped the bright beam would solve everything", "switched on a flashlight, but it did not fix the mix-up", "turned on a flashlight", tags={"weak"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Ben", "Theo", "Leo", "Finn", "Max"]
TRAITS = ["curious", "brave", "careful", "sensible", "quick", "dreamy"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for t in THEMES:
        for p in PROPS:
            for r in PROBLEMS:
                for f in FIXES:
                    if reasonableness_ok(PROPS[p], PROBLEMS[r], FIXES[f]):
                        out.append((t, p, r, f))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: camcorder, practise, magic, misunderstanding, conflict, adventure.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.theme is None or c[0] == args.theme)
              and (args.prop is None or c[1] == args.prop)
              and (args.problem is None or c[2] == args.problem)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, prop, problem, fix = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero])
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n not in {hero, friend}])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(theme, prop, problem, fix, hero, hero_gender, friend, friend_gender, helper, helper_gender, trait)


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity("hero", "character", params.hero_gender, label=params.hero, role="hero", traits=[params.trait]))
    friend = world.add(Entity("friend", "character", params.friend_gender, label=params.friend, role="friend"))
    helper = world.add(Entity("helper", "character", params.helper_gender, label=params.helper, role="helper"))
    room = world.add(Entity("room", "thing", "room", label="the camp", meters={"quiet": 0.0}, memes={}))
    prop = world.add(Entity("prop", "thing", "prop", label=PROPS[params.prop].label, attrs={"phrase": PROPS[params.prop].phrase}))
    world.facts.update(hero=hero, friend=friend, helper=helper, room=room, prop=prop)


def _do_practise(world: World, params: StoryParams, narrate: bool = True) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    prop = PROPS[params.prop]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    theme = THEMES[params.theme]
    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    world.say(f"At {theme.scene}, {hero.id} and {friend.id} turned the place into {theme.rig}")
    world.say(f'{hero.id} lifted the {prop.label} and said, "Let\'s practise before we show anyone."')
    world.say(f"{friend.id} smiled at first, because the idea sounded like an adventure.")
    world.para()
    if prop.makes_magic:
        hero.memes["magic"] = 1
        world.say(f"The {prop.label} {prop.glow}, and that made the little scene feel truly magical.")
    else:
        world.say(f"The {prop.label} was ordinary, but it still felt exciting to hold.")
    world.say(f"But then {friend.id} had {problem.label} and thought the practise was real.")
    friend.memes["misunderstood"] = 1
    hero.memes["hurt"] = 1
    world.say(f'"Wait," {friend.id} said. "{problem.effect}!"')
    propagate(world, narrate=False)
    world.say(f"{hero.id} frowned. " + f'"I only meant to practise," {hero.pronoun()} said.')
    world.say(f"{friend.id} crossed {friend.pronoun('possessive')} arms, and a small conflict filled the camp.")
    world.para()
    helper.memes["calm"] = 1
    world.say(f"Then {params.helper} came over like a steady guide and listened to both sides.")
    if fix.sense >= 2:
        world.say(f"{helper.id} {fix.text}.")
    else:
        world.say(f"{helper.id} {fix.fail}.")
    if fix.power >= 2:
        hero.memes["relief"] = 1
        friend.memes["relief"] = 1
        friend.memes["misunderstood"] = 0
        hero.memes["hurt"] = 0
        world.say(f"Their faces softened, and they practised again, this time with clear turns and no guessing.")
        world.say(f"After that, the camcorder caught the scene neatly, and the adventure looked bright instead of tangled.")
    else:
        world.say(f"The confusion stayed for a while, but the bright beam made everyone pause and think.")
    world.say(f"In the end, they recorded the quest and kept {theme.ending.lower()}")


def generate(params: StoryParams) -> StorySample:
    world = World()
    _setup(world, params)
    _do_practise(world, params)
    world.facts.update(params=params, theme=THEMES[params.theme], prop=PROPS[params.prop], problem=PROBLEMS[params.problem], fix=FIXES[params.fix], outcome=outcome_of(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story that includes the words camcorder and practise, and features a magic misunderstanding.",
        f"Tell a child-friendly tale where {f['hero'].id} wants to practise a magic scene with a camcorder, but a friend misreads it and conflict follows.",
        f"Write a short adventure about a camcorder recording a practise run that turns into a misunderstanding, then gets fixed by a calm helper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    theme = f["theme"]
    prop = f["prop"]
    problem = f["problem"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, {friend.id}, and {helper.id}, who were acting out a little adventure together."),
        ("What were they trying to do?", f"They were trying to practise a magic scene and record it with a camcorder. They wanted the pretend adventure to look exciting and clear."),
        ("What went wrong?", f"{friend.id} had a misunderstanding and thought the practise was real. That mistake turned the scene into a conflict."),
        ("How did the helper fix it?", f"{helper.id} {fix.qa_text}. That helped everyone understand the plan again."),
        ("What changed at the end?", f"The confusion settled down, and they kept {theme.ending.lower()}. The camcorder captured a safer, happier adventure after the talk."),
    ]
    return qa


KNOWLEDGE = {
    "camcorder": [("What is a camcorder?", "A camcorder is a camera that can record moving pictures and sound. People use it to save a memory or make a movie."),
    ],
    "practise": [("Why do people practise?", "People practise so they can do something better later. Practise helps a trick, song, or game feel smoother and safer.")],
    "magic": [("What is magic in a story?", "Magic in a story is something wonderful or surprising that seems impossible in real life. It makes the adventure feel extra exciting.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when someone thinks the wrong thing about what is going on. Talking can clear it up."),
    ],
    "conflict": [("What is conflict in a story?", "Conflict is a problem or disagreement that makes the characters upset for a while. Stories often use it to show how people solve trouble.")],
    "adventure": [("What makes a story an adventure?", "An adventure story has a goal, a challenge, and a feeling of exploring something new. The characters keep going even when things get tricky.")],
}
KNOWLEDGE_ORDER = ["camcorder", "practise", "magic", "misunderstanding", "conflict", "adventure"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = set(world.facts["prop"].tags) | set(world.facts["problem"].tags) | set(world.facts["theme"].id.split())
    tags |= {"practise", "adventure"}
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("adventure", "sparkle_camcorder", "misunderstanding", "explain", "Mia", "girl", "Ben", "boy", "Nora", "girl", "curious"),
    StoryParams("island", "camcorder", "conflict", "reset", "Leo", "boy", "Ava", "girl", "Maya", "girl", "brave"),
    StoryParams("cave", "wand", "mixup", "explain", "Zoe", "girl", "Finn", "boy", "Theo", "boy", "careful"),
]


def explain_rejection(prop: Prop, problem: Problem, fix: Fix) -> str:
    if not prop.makes_magic:
        return "(No story: this prop is not magical enough for the adventure idea. Choose a camcorder variant that can glow or blink.)"
    if "conflict" not in problem.tags:
        return "(No story: the problem needs to create conflict or misunderstanding for this world.)"
    if fix.sense < 2:
        return "(No story: that fix is too weak for a believable child story.)"
    return "(No story: the combination is not reasonable.)"


def valid_story(params: StoryParams) -> bool:
    return reasonableness_ok(PROPS[params.prop], PROBLEMS[params.problem], FIXES[params.fix])


def asp_verify_smoke() -> int:
    return asp_verify()


def asp_program_text() -> str:
    return asp_program("", "#show valid/4.\n#show sensible/1.")


def asp_valid_combos_full() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        sens = asp_sensible()
        print(f"sensible fixes: {', '.join(sens)}")
        for t, p, r, f in asp_valid_combos():
            print(f"{t:10} {p:15} {r:16} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}, {p.friend}, and {p.helper}: {p.prop} / {p.problem} / {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
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
