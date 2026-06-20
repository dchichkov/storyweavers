#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/apron_swim_school_problem_solving_pirate_tale.py
=================================================================================

A standalone storyworld for a small pirate-themed problem-solving tale set at
swim school, built around an apron that helps solve a soggy mess.

The world is intentionally tiny:
- Two children are in swim school.
- One child plays pirate captain and wants to find a missing pool token / dry
  whistle card / snack flag.
- A wet apron, a towel, and a clever fix are the important objects.
- The story can end in a safe rescue and a calmer, happier pool time.

This script follows the shared Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
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
    wet: bool = False
    dry: bool = False
    usable: bool = False

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
    scene: str
    safe_corner: str
    pirate_frame: str
    sound: str

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
    clue: str
    risk: str
    ask: str
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
class Item:
    id: str
    label: str
    phrase: str
    helps: set[str]
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return c


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


def _r_wet_apron(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    apron = world.get("apron")
    if child.meters["splash"] >= THRESHOLD and not apron.usable:
        sig = ("wet_apron",)
        if sig not in world.fired:
            world.fired.add(sig)
            apron.wet = True
            apron.meters["soaked"] += 1
            out.append("__wet__")
    return out


def _r_conflict(world: World) -> list[str]:
    if world.get("child").memes["stuck"] >= THRESHOLD and ("conflict",) not in world.fired:
        world.fired.add(("conflict",))
        world.get("child").memes["frustration"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("wet_apron", "physical", _r_wet_apron),
    Rule("conflict", "social", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend([r for r in res if not r.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_risk(problem: Problem, setting: Setting) -> bool:
    return problem.id in setting.id or True


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def is_valid(problem: Problem, fix: Fix, item: Item) -> bool:
    return problem.id in fix.tags and problem.id in item.tags


def fix_works(fix: Fix, problem: Problem, delay: int) -> bool:
    return fix.power >= (1 + delay)


def tell(setting: Setting, problem: Problem, item: Item, fix: Fix,
         child_name: str = "Mia", child_gender: str = "girl",
         friend_name: str = "Tom", friend_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="captain"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="helper", label="the coach"))
    apron = world.add(Entity(id="apron", type="thing", label=item.label))
    apron.usable = True
    apron.dry = True
    world.add(Entity(id="bench", type="thing", label="the bench"))
    world.facts["setting"] = setting
    world.facts["problem"] = problem
    world.facts["item"] = item
    world.facts["fix"] = fix
    world.facts["delay"] = delay
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.facts["parent"] = parent

    child.memes["love_play"] += 1
    friend.memes["love_play"] += 1
    world.say(
        f"At {setting.place}, {child.id} and {friend.id} turned swim school into {setting.scene}. "
        f"{setting.pirate_frame}"
    )
    world.say(
        f'"Arrr!" {child.id} cried. "{problem.ask} in the {setting.safe_corner}?" '
        f'The splashy water had made everything feel like a little sea voyage.'
    )

    world.para()
    child.memes["stuck"] += 1
    world.say(
        f"But the {problem.label} kept getting in the way. {problem.clue} {problem.risk}. "
        f'{friend.id} frowned and pointed at {item.phrase}.'
    )
    world.say(f'"Maybe the {item.label} can help," {friend.id} said, thinking hard.')

    if fix.id == "apron_dry":
        world.say(
            f'{child.id} tucked the {item.label} on and used it like a captain’s satchel. '
            f'It kept the little cards dry and held the lost token.'
        )
    elif fix.id == "apron_catch":
        world.say(
            f'{child.id} fastened the {item.label} to catch the dripping whistle card, '
            f'and the wet mess stopped sliding away.'
        )

    if delay:
        child.meters["splash"] += delay

    world.para()
    if fix_works(fix, problem, delay):
        child.memes["joy"] += 1
        child.memes["stuck"] = 0
        child.memes["relief"] += 1
        world.say(
            f"{parent.label_word.capitalize()} came over and nodded. In a flash {parent.pronoun()} "
            f"{fix.text}."
        )
        world.say(
            f"The little trouble was solved, and the {setting.pirate_frame.lower()} turned cheerful again."
        )
        world.para()
        world.say(
            f"At the end, {child.id} wore the {item.label} proudly, the token was safe, "
            f"and the crew splashed on with bright brave grins."
        )
        outcome = "solved"
    else:
        world.say(
            f"{parent.label_word.capitalize()} came over and tried to help, but {parent.pronoun()} "
            f"{fix.fail}."
        )
        world.say(
            f"So they had to stop the game, wring out the wet things, and begin again more slowly."
        )
        outcome = "stopped"

    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "swim_school": Setting(
        "swim_school",
        "swim school",
        "The pool deck felt like a blue harbor, the lesson line was a tiny dock, and the lane rope shone like a pirate rail.",
        "A tidy apron hung by the side table, ready for maps, stickers, and snack notes.",
        "The children pretended the shallow end was a secret cove.",
        "Water splashed and slapped softly against the tiles.",
    ),
    "shallow_pool": Setting(
        "shallow_pool",
        "the shallow pool",
        "The water sparkled like treasure, and every kick made a small silver wake.",
        "A waterproof apron rested near the bench for keeping lesson cards dry.",
        "Everyone spoke in pirate whispers so the fishy game would feel real.",
        "Water tapped the edge of the pool in tiny drumbeats.",
    ),
}

PROBLEMS = {
    "missing_token": Problem("missing_token", "missing token", "A little pool token had slipped under a chair", "and it was hard to reach in the wet floor", "Who can help us get it?", tags={"token", "problem"}),
    "drip_cards": Problem("drip_cards", "dripping cards", "The lesson cards were getting soggy", "so the class could not read the next turn", "How do we keep them dry?", tags={"cards", "problem"}),
    "lost_whistle_card": Problem("lost_whistle_card", "lost whistle card", "The whistle card kept sliding away on the wet bench", "and nobody could keep it in place", "What should we use to hold it?", tags={"whistle", "problem"}),
}

ITEMS = {
    "apron": Item("apron", "apron", "the apron", {"token", "cards", "whistle", "problem"}, tags={"apron", "tool"}),
    "towel": Item("towel", "towel", "the towel", {"cards", "problem"}, tags={"towel", "tool"}),
    "net_bag": Item("net_bag", "net bag", "the net bag", {"token", "problem"}, tags={"bag", "tool"}),
}

FIXES = {
    "apron_dry": Fix("apron_dry", 3, 2, "dried the apron on the line and clipped the cards right into its pocket", "could not help because the apron was too damp and limp", "solved it with the apron and kept the cards dry", tags={"apron", "problem"}),
    "apron_catch": Fix("apron_catch", 2, 1, "used the apron pocket to catch the slipping card and held it still", "could not catch the card before it slid away", "caught the card in the apron pocket", tags={"apron", "problem"}),
    "towel_wrap": Fix("towel_wrap", 2, 1, "wrapped the towel around the slippery card stack and held it tight", "could not hold the wet cards tightly enough", "wrapped the cards in a towel", tags={"towel", "problem"}),
}



@dataclass
class StoryParams:
    setting: str
    problem: str
    item: str
    fix: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
    delay: int = 0
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

CURATED = [
    StoryParams("swim_school", "missing_token", "apron", "apron_dry", "Mia", "girl", "Tom", "boy", "mother", 0),
    StoryParams("swim_school", "drip_cards", "apron", "apron_catch", "Leo", "boy", "Ava", "girl", "father", 0),
    StoryParams("shallow_pool", "lost_whistle_card", "apron", "towel_wrap", "Nora", "girl", "Max", "boy", "mother", 1),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for iid, item in ITEMS.items():
                if is_valid(problem, FIXES["apron_dry"] if iid == "apron" else FIXES["towel_wrap"], item):
                    combos.append((sid, pid, iid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    s: Setting = f["setting"]
    return [
        f'Write a pirate-style swim-school story that includes the word "apron" and solves a small problem.',
        f"Tell a story set at {s.place} where two children in pirate mode notice {p.label} and use an apron to solve it.",
        f'Write a child-friendly problem-solving tale about {p.label} with a boat-like, treasure-hunt feeling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    parent = f["parent"]
    problem: Problem = f["problem"]
    item: Item = f["item"]
    fix: Fix = f["fix"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer=f"It was set at {setting.place}, where the pool deck felt like a little harbor. That made the swim lesson feel like a pirate adventure."
        ),
        QAItem(
            question=f"What problem did {child.id} notice?",
            answer=f"{child.id} noticed {problem.clue.lower()}. That meant the {problem.label} needed a clever fix before the game could continue."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {item.phrase} and {fix.qa_text}. That kept the important things safe and let the children keep playing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an apron for?",
            answer="An apron is something you wear to keep your clothes neat or dry while you work or help with a task."
        ),
        QAItem(
            question="Why can a wet towel help?",
            answer="A towel can soak up water and help hold or dry something, which makes it useful around a pool."
        ),
        QAItem(
            question="What is swim school?",
            answer="Swim school is a place where children learn how to be safe and strong in the water."
        ),
    ]


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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, I) :- setting(S), problem(P), item(I), item_help(I, P), valid_fix(P, I).
solved(P) :- fix(F), fix_ok(F, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_help", iid, tag))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_ok", fid, next(iter(fix.tags)) if fix.tags else "problem"))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"FAIL: generate() smoke test crashed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style swim school problem-solving storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.problem and args.item:
        prob = PROBLEMS[args.problem]
        item = ITEMS[args.item]
        fix = FIXES[args.fix] if args.fix else FIXES["apron_dry"]
        if not is_valid(prob, fix, item):
            raise StoryError("This story needs an item and fix that truly solve the problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, item = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    return StoryParams(
        setting=setting,
        problem=problem,
        item=item,
        fix=fix,
        child=args.child or rng.choice(["Mia", "Leo", "Nora", "Max"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        friend=args.friend or rng.choice(["Tom", "Ava", "Ben", "Zoe"]),
        friend_gender=args.friend_gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
        delay=args.delay if args.delay is not None else rng.randint(0, 1),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        ITEMS[params.item],
        FIXES[params.fix],
        params.child,
        params.child_gender,
        params.friend,
        params.friend_gender,
        params.parent,
        params.delay,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
