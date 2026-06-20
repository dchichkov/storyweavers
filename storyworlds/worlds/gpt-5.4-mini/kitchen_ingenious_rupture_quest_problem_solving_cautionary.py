#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kitchen_ingenious_rupture_quest_problem_solving_cautionary.py
==============================================================================================

A standalone story world for a tall-tale kitchen quest: a child spots a problem,
tries an ingenious fix, faces a rupture hazard, and learns a cautionary lesson
while still ending with a bright solved image.

The domain is small on purpose:
- a kitchen with a quest-like goal
- a fragile object that may rupture
- an ingenious child repair or detour
- a calm grown-up caution that changes the outcome

The words kitchen, ingenious, and rupture are woven into the simulation and prose.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    sharp: bool = False
    hot: bool = False
    useful: bool = False
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
    scene: str
    quest: str
    clue: str
    ending: str
    affords: set[str] = field(default_factory=set)

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
    sign: str
    danger: str
    cause: str
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
class IngeniousFix:
    id: str
    label: str
    tool: str
    action: str
    result: str
    power: int
    sense: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["rupture"] < THRESHOLD:
            continue
        sig = ("alarm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["fear"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def valid_combo(problem: Problem, fix: IngeniousFix, setting: Setting) -> bool:
    return problem.id in setting.affords and fix.sense >= SENSE_MIN and fix.power >= 1


SENSE_MIN = 2


def reasonableness_gate(problem: Problem, fix: IngeniousFix) -> bool:
    return problem.id in PROBLEMS and fix.id in FIXES and fix.sense >= SENSE_MIN


def severity(problem: Problem, delay: int) -> int:
    return 1 + delay if problem.id == "leak" else 2 + delay


def contained(fix: IngeniousFix, problem: Problem, delay: int) -> bool:
    return fix.power >= severity(problem, delay)


def predict_rupture(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _trigger_problem(sim, sim.get(problem_id), narrate=False)
    return {
        "ruptured": sim.get(problem_id).meters["rupture"] >= THRESHOLD,
        "fear": sum(ch.memes["fear"] for ch in sim.characters()),
    }


def _trigger_problem(world: World, ent: Entity, narrate: bool = True) -> None:
    ent.meters["rupture"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a windy afternoon, {child.id} and {helper.label_word} were in the kitchen, "
        f"where the cupboards stood like old barn doors and the light shone like a lantern."
    )
    world.say(
        f"They had a quest: find the missing supper fix hidden by {setting.clue} and bring the meal back to town."
    )


def problem(world: World, child: Entity, prob: Problem) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"Then came the problem: {prob.sign}. {prob.cause} {prob.danger}."
    )


def idea(world: World, child: Entity, fix: IngeniousFix) -> None:
    child.memes["ingenuity"] += 1
    world.say(
        f"{child.id}'s eyes flashed bright. \"I know,\" {child.pronoun()} said. "
        f"\"An ingenious plan! We can use {fix.tool}.\""
    )


def warn(world: World, helper: Entity, child: Entity, prob: Problem) -> None:
    helper.memes["caution"] += 1
    world.say(
        f"{helper.label_word.capitalize()} put up a hand. \"Careful now,\" {helper.pronoun()} said. "
        f"\"If we rush, that {prob.label} could get worse.\""
    )


def repair(world: World, child: Entity, fix: IngeniousFix, prob: Problem, delay: int) -> bool:
    if not contained(fix, prob, delay):
        return False
    world.say(
        f"So {child.id} used {fix.tool}, {fix.action}, and soon {fix.result}."
    )
    return True


def rupture_scene(world: World, child: Entity, prob: Problem) -> None:
    _trigger_problem(world, world.get("problem"))
    world.say(
        f"But the {prob.label} gave a little rupture first, with a pop like a drum in a thunderstorm."
    )
    world.say(
        f"{child.id} yelped, and the kitchen held its breath as the trouble began to spread."
    )


def cautionary_lesson(world: World, helper: Entity, child: Entity, prob: Problem) -> None:
    for ch in world.characters():
        ch.memes["fear"] = 0
        ch.memes["relief"] += 1
        ch.memes["lesson"] += 1
    world.say(
        f"{helper.label_word.capitalize()} knelt down and said, "
        f"\"That's why we go slow. A rupture can turn a small bother into a big mess before you can blink.\""
    )
    world.say(
        f"{child.id} nodded, wiser for the warning and glad the kitchen was still standing."
    )


def ending(world: World, child: Entity, helper: Entity, setting: Setting, fix: IngeniousFix) -> None:
    world.say(
        f"By sunset, the {setting.id} was neat again, the supper was saved, and "
        f"{child.id} was grinning like a fox that had solved a riddle."
    )
    world.say(
        f"They left the kitchen with {fix.label} in hand, ready for the next quest, "
        f"and the old room glowed warm behind them."
    )


def tell(setting: Setting, prob: Problem, fix: IngeniousFix, child_name: str = "Nora",
         child_gender: str = "girl", helper_gender: str = "mother", delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_gender, role="helper", label="the helper"))
    world.add(Entity(id="problem", type="thing", label=prob.label, fragile=True))
    intro(world, child, helper, setting)
    world.para()
    problem(world, child, prob)
    warn(world, helper, child, prob)
    idea(world, child, fix)
    world.para()
    rupture_scene(world, child, prob)
    if repair(world, child, fix, prob, delay):
        cautionary_lesson(world, helper, child, prob)
        world.para()
        ending(world, child, helper, setting, fix)
    else:
        world.say(
            f"The fix was too weak, and the kitchen lesson turned into a bigger scramble."
        )
        cautionary_lesson(world, helper, child, prob)
        world.para()
        ending(world, child, helper, setting, fix)
    world.facts.update(setting=setting, problem=prob, fix=fix, child=child, helper=helper, delay=delay)
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "a kitchen as wide as a wagon yard", "a missing supper recipe", "a secret crack behind the cupboard", "the kitchen door",
                       affords={"leak", "spill", "jar"}),
    "pantry": Setting("pantry", "a pantry with shelves like castle walls", "a hidden snack map", "a tiny drip under the shelf", "the pantry door",
                      affords={"leak", "jar"}),
}

PROBLEMS = {
    "leak": Problem("leak", "leaky pipe", "A pipe was leaking under the sink", "water could spread fast", "a tiny washer had worn thin", tags={"water", "kitchen", "rupture"}),
    "jar": Problem("jar", "glass jar", "A glass jar had a hairline crack", "it could rupture if squeezed", "someone had set it too close to the edge", tags={"glass", "rupture"}),
    "spill": Problem("spill", "saucy spill", "A bowl had tipped over", "it could slide across the floor", "the counter was crowded", tags={"spill", "kitchen"}),
}

FIXES = {
    "towel": IngeniousFix("towel", "a towel dam", "rolled towels", "packed the towels into a little wall", "the water stayed put", 2, 2, tags={"water"}),
    "crate": IngeniousFix("crate", "a crate brace", "a wooden crate", "propped the jar safely with a crate brace", "the crack stopped worrying everyone", 3, 3, tags={"glass"}),
    "bowl": IngeniousFix("bowl", "a wide bowl", "a wide bowl", "caught the spill before it ran away", "the mess was gathered up neat as a ribbon", 1, 2, tags={"spill"}),
}



@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    child: str
    child_gender: str
    helper_gender: str
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
    ("kitchen", "leak", "towel", "Nora", "girl", "mother", 0),
    ("kitchen", "jar", "crate", "Milo", "boy", "father", 0),
    ("pantry", "leak", "bowl", "June", "girl", "mother", 1),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid in setting.affords:
            for fid in FIXES:
                if valid_combo(PROBLEMS[pid], FIXES[fid], setting):
                    combos.append((sid, pid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale kitchen quest with an ingenious repair and a cautionary turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.problem and args.fix and not valid_combo(PROBLEMS[args.problem], FIXES[args.fix], SETTINGS[args.setting or "kitchen"]):
        raise StoryError("That fix does not fit that problem in this kitchen world.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(["Nora", "Milo", "Ivy", "Otis", "June", "Pip"])
    return StoryParams(setting, problem, fix, child, child_gender, helper_gender, args.delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story set in a kitchen that includes the words "kitchen", "ingenious", and "rupture".',
        f"Tell a cautionary quest where {f['child'].id} meets {f['problem'].label} and tries an ingenious fix with help from a grown-up.",
        f"Write a problem-solving story where a kitchen problem almost ruptures, but a careful helper and a clever child save the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, prob, fix = f["child"], f["helper"], f["problem"], f["fix"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {helper.label_word}, who were working in the {world.setting.id}."),
        ("What problem did they face?", f"They faced {prob.label}, and it was dangerous because {prob.danger}."),
        ("How did they solve it?", f"They used {fix.label}. That was the ingenious part of the story, because it fit the problem and helped put things right."),
        ("What warning did the helper give?", f"{helper.label_word.capitalize()} warned them to go slow, because a rupture can make a small trouble grow fast."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a kitchen?", "A kitchen is the room where people cook, wash dishes, and make food."),
        ("What does ingenious mean?", "Ingenious means clever, smart, and full of a good new idea."),
        ("What is a rupture?", "A rupture is a sudden break or burst, like when something cracks or splits open."),
        ("Why should you be cautious with breakable things?", "Breakable things can crack or burst, so careful hands and slow movements help keep everyone safe."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,F) :- setting(S), problem(P), fix(F), afforded(S,P), sense(F,SN), sense_min(M), SN >= M.
outcome(safe) :- chosen_fix(F), chosen_problem(P), power(F, PW), need(P, N), PW >= N.
outcome(rupture) :- chosen_fix(F), chosen_problem(P), power(F, PW), need(P, N), PW < N.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("need", pid, 1 if pid == "spill" else 2))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for sid, s in SETTINGS.items():
        for pid in s.affords:
            lines.append(asp.fact("afforded", sid, pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, fix=None, child=None, child_gender=None, helper_gender=None, delay=0, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity and story generation succeeded ({len(valid_combos())} combos).")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix],
                 params.child, params.child_gender, params.helper_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
