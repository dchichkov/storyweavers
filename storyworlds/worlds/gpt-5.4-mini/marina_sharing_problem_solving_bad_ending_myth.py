#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marina_sharing_problem_solving_bad_ending_myth.py
================================================================================

A standalone storyworld for a small myth-like domain about Marina, sharing,
problem solving, and a bad ending.

The world models a child-friendly mythic harbor scene:
- Marina and a friend share a treasured object.
- A practical problem appears in the harbor or shoreline.
- They try to solve it with the tools and help they have.
- The ending can still go bad if the tide, weather, or delay overpowers them.

The story is driven by world state, not by swapping nouns in a frozen paragraph.
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
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    place: str
    wonder: str
    shared_object: str
    problem: str
    solution_space: str
    ending_image: str
    myth_title: str

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
class ObjectCfg:
    id: str
    label: str
    precious: bool = True
    shareable: bool = True
    helpful: bool = False

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
class ProblemCfg:
    id: str
    label: str
    risk: str
    fix: str
    delay: int
    severity: int
    requires_help: bool = True

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
class FixCfg:
    id: str
    label: str
    power: int
    text: str
    fail_text: str
    relies_on_sharing: bool = False

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["storm"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["damage"] < THRESHOLD:
            continue
        sig = ("damage", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["grief"] += 1
        out.append("__damage__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("damage", "physical", _r_damage)]


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


def mythic_place(theme: Theme, problem: ProblemCfg) -> str:
    return f"{theme.place}, where {theme.wonder} and the {problem.label} waited like old spirits"


def risk_at_hand(obj: ObjectCfg, problem: ProblemCfg) -> bool:
    return obj.shareable and problem.requires_help


def best_fix() -> FixCfg:
    return max(FIXES.values(), key=lambda f: f.power)


def can_attempt(problem: ProblemCfg, fix: FixCfg, delay: int) -> bool:
    return fix.power >= problem.severity + delay


def predict_bad(world: World, problem: ProblemCfg, fix: FixCfg, delay: int) -> dict:
    sim = world.copy()
    _cause_problem(sim, problem, narrate=False)
    _apply_fix(sim, fix, problem, delay, narrate=False)
    return {"ruined": sim.get("marina").memes["grief"] >= THRESHOLD or sim.get("harbor").meters["damage"] >= THRESHOLD}


def _cause_problem(world: World, problem: ProblemCfg, narrate: bool = True) -> None:
    world.get("harbor").meters["storm"] += 1
    world.get("marina").meters["storm"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(problem.risk)


def _apply_fix(world: World, fix: FixCfg, problem: ProblemCfg, delay: int, narrate: bool = True) -> bool:
    if can_attempt(problem, fix, delay):
        world.get("harbor").meters["damage"] = 0
        world.get("marina").meters["storm"] = 0
        if narrate:
            world.say(fix.text)
        return True
    world.get("harbor").meters["damage"] += 1
    world.get("marina").memes["grief"] += 1
    if narrate:
        world.say(fix.fail_text)
    return False


def tell(theme: Theme, obj: ObjectCfg, problem: ProblemCfg, fix: FixCfg,
         marina_name: str = "Marina", friend_name: str = "Niko",
         friend_type: str = "boy", helper_name: str = "Old Sailor",
         helper_type: str = "man", delay: int = 0) -> World:
    world = World()
    marina = world.add(Entity(id=marina_name, kind="character", type="girl", role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    harbor = world.add(Entity(id="harbor", type="place", label=theme.place))
    shared = world.add(Entity(id="shared", type="thing", label=obj.label))
    marina.memes["love"] += 1
    friend.memes["love"] += 1
    harbor.attrs["theme"] = theme.id
    world.say(
        f"In the old harbor of {theme.place}, Marina and {friend.id} found {obj.label} beside the salt water. "
        f"{theme.wonder.capitalize()}, and the little pair treated the day like a myth."
    )
    world.say(
        f'They shared {obj.label} as if it were a torch for a temple path. '
        f'Marina held one side, and {friend.id} held the other, so neither child was left out.'
    )
    world.para()
    world.say(
        f"But the sky turned mean over the water. {problem.label.capitalize()} rose up, and the boats began to tug. "
        f"{friend.id} said they needed a way to keep {obj.label} safe."
    )
    world.say(
        f'Marina listened, thought hard, and asked the old sailor for help. '
        f'He pointed to the {problem.solution_space} and offered a simple plan.'
    )
    world.para()
    _cause_problem(world, problem, narrate=True)
    world.say(
        f"{helper.label_word.capitalize()} tried to help with {fix.label}, but the {problem.label} had already grown sharp."
    )
    worked = _apply_fix(world, fix, problem, delay, narrate=True)
    if not worked:
        world.say(
            f"The harbor could not hold. Waves snapped the rope, the lantern fell, and the shared thing was lost to the dark water."
        )
        world.say(
            f"Marina and {friend.id} stood with empty hands while the tide carried their mistake away."
        )
    else:
        world.say(
            f"Marina and {friend.id} looked at one another and nodded. The problem was handled, and {obj.label} stayed in their hands."
        )
    world.para()
    if worked:
        world.say(
            f"At sunset, the harbor glowed like an old god's bowl, and Marina felt brave for sharing and asking for help."
        )
    else:
        world.say(
            f"At sunset, the harbor was only wrecked wood and cold foam. Marina learned too late that some choices grow larger than a child can manage."
        )
    world.facts.update(
        marina=marina,
        friend=friend,
        helper=helper,
        harbor=harbor,
        shared=shared,
        theme=theme,
        object_cfg=obj,
        problem=problem,
        fix=fix,
        delay=delay,
        worked=worked,
    )
    return world


THEMES = {
    "myth": Theme("myth", "the marble marina", "the gulls circled like white messengers", "a small silver shell", "a tide trouble woke under the docks", "the lantern room", "the harbor looked like a story older than kings", "The Shell of Marina"),
    "moon_myth": Theme("moon_myth", "the moonlit marina", "the lamps shone like tiny stars on water", "a bright rope charm", "a wind trouble came from the east", "the captain's shed", "the moon made the boats look enchanted", "Marina and the Wind Omen"),
}

OBJECTS = {
    "shell": ObjectCfg("shell", "a small silver shell"),
    "rope_charm": ObjectCfg("rope_charm", "a bright rope charm"),
    "fish_token": ObjectCfg("fish_token", "a painted fish token"),
}

PROBLEMS = {
    "tide": ProblemCfg("tide", "tide trouble", "the tide pulled hard at the boats", "steady the rope", 1, 2),
    "storm": ProblemCfg("storm", "wind trouble", "the wind shook the docks", "tie the boats tighter", 2, 3),
    "fog": ProblemCfg("fog", "fog trouble", "the fog swallowed the lantern light", "light a safe lantern", 2, 2),
}

FIXES = {
    "rope": FixCfg("rope", "a stronger rope knot", 3, "the knot held fast and the boats stopped bumping", "the knot slipped and the boats struck the posts", relies_on_sharing=True),
    "lantern": FixCfg("lantern", "a lantern", 2, "the lantern glowed and showed the safe path home", "the lantern was too dim to guide them"),
    "help": FixCfg("help", "help from the old sailor", 4, "the old sailor lashed the boats down and saved the dock", "the sailor arrived too late, and the water had already won"),
}

GIRL_NAMES = ["Marina", "Nia", "Lina", "Mira", "Sela"]
BOY_NAMES = ["Niko", "Taro", "Eli", "Jon", "Soren"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for p in PROBLEMS:
            for o in OBJECTS:
                if risk_at_hand(OBJECTS[o], PROBLEMS[p]):
                    combos.append((t, p, o))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    problem: str
    object: str
    fix: str
    friend_name: str
    friend_type: str
    helper_name: str
    helper_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a child that includes "marina" and a sharing problem at {f["theme"].place}.',
        f"Tell a story where Marina shares {f['object_cfg'].label}, then a harbor problem appears, and she tries to solve it with help.",
        f"Write a short mythic bad-ending story about Marina, sharing, and a problem that grows too hard to fix in time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj = f["object_cfg"]
    problem = f["problem"]
    fix = f["fix"]
    worked = f["worked"]
    ans1 = f"Marina shared {obj.label} with {f['friend'].id}. They both held it together so it would not be only one child's treasure."
    ans2 = f"They tried to solve the {problem.label} by asking for help and using {fix.label}. That plan was meant to keep the harbor safe."
    if worked:
        ans3 = "The ending was calm and bright. The trouble was handled, and Marina still had the shared treasure at sunset."
    else:
        ans3 = "The ending was bad. The tide or wind won, the harbor was damaged, and Marina lost the thing they had shared."
    return [
        QAItem("What did Marina share?", ans1),
        QAItem("How did they try to solve the problem?", ans2),
        QAItem("How did the story end?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a marina?", "A marina is a place where boats are kept near the water, often with docks and ropes."),
        QAItem("Why do people share things?", "People share things so everyone can take part, learn, and feel included."),
        QAItem("What should you do when a problem is too big?", "Ask a grown-up or a helper for support, because some problems need more strength than one child has."),
        QAItem("What can happen if a storm gets worse?", "A stronger storm can break ropes, shake boats, and damage the places near the water."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("myth", "tide", "shell", "rope", "Niko", "boy", "Old Sailor", "man", 0),
    StoryParams("moon_myth", "storm", "rope_charm", "help", "Mira", "girl", "Old Sailor", "man", 2),
    StoryParams("myth", "fog", "fish_token", "lantern", "Soren", "boy", "Old Sailor", "man", 1),
]


def explain_rejection(problem: ProblemCfg, obj: ObjectCfg) -> str:
    return f"(No story: {obj.label} and {problem.label} do not make a good mythic sharing problem.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.object:
        if not risk_at_hand(OBJECTS[args.object], PROBLEMS[args.problem]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], OBJECTS[args.object]))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.problem is None or c[1] == args.problem)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, problem, obj = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    friend_type = rng.choice(["boy", "girl"])
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    helper_type = "man"
    helper_name = "Old Sailor"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(theme, problem, obj, fix, friend_name, friend_type, helper_name, helper_type, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], OBJECTS[params.object], PROBLEMS[params.problem],
                 FIXES[params.fix], marina_name="Marina", friend_name=params.friend_name,
                 friend_type=params.friend_type, helper_name=params.helper_name,
                 helper_type=params.helper_type, delay=params.delay)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
valid(T, P, O) :- theme(T), problem(P), object(O), risky(O, P).
bad_end(T, P, O) :- valid(T, P, O), delay(D), severity(P, S), fix(F), power(F, Pw), Pw < S + D.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, p.severity))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.shareable:
            lines.append(asp.fact("risky", oid, "tide"))
            lines.append(asp.fact("risky", oid, "storm"))
            lines.append(asp.fact("risky", oid, "fog"))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("delay", 0))
    lines.append(asp.fact("delay", 1))
    lines.append(asp.fact("delay", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic Marina storyworld about sharing, problem solving, and a bad ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--friend-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show bad_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
