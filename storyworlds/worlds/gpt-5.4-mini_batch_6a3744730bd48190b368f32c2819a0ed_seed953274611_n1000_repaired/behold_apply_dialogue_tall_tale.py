#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/behold_apply_dialogue_tall_tale.py
===================================================================

A small tall-tale storyworld about a mighty little repair, with dialogue,
the words "behold" and "apply", and a state-driven ending image.

Premise:
- A child and an elder find a stubborn leak in a boat or wagon.
- They argue briefly, then choose a grand-but-sensible repair.
- The repair changes the world state: leak stops, worry falls, pride rises.

The world is deliberately compact but still uses:
- typed entities with meters and memes,
- a causal forward model,
- QA generated from world state rather than rendered text,
- a Python reasonableness gate and inline ASP twin,
- standard Storyweavers CLI flags.

The prose aims for a tall-tale feel: lively dialogue, a boast, a test,
and a satisfying image of the repaired thing riding on.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "gran", "grandfather": "grandpa"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    phrase: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Problem:
    id: str
    label: str
    leak: str
    test: str
    at_risk: str
    danger: str
    tag: str
    makes_leak: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_leak(world: World) -> list[str]:
    out: list[str] = []
    vessel = world.get("vessel")
    if vessel.meters["leaking"] >= THRESHOLD and ("leak", vessel.id) not in world.fired:
        world.fired.add(("leak", vessel.id))
        vessel.meters["soaked"] += 1
        world.get("ground").meters["mud"] += 1
        for eid in ("hero", "elder"):
            world.get(eid).memes["worry"] += 1
        out.append("__leak__")
    return out


def _r_pride(world: World) -> list[str]:
    out: list[str] = []
    vessel = world.get("vessel")
    if vessel.meters["repaired"] >= THRESHOLD and ("pride", vessel.id) not in world.fired:
        world.fired.add(("pride", vessel.id))
        world.get("hero").memes["pride"] += 1
        world.get("elder").memes["pride"] += 1
        out.append("__pride__")
    return out


CAUSAL_RULES = [Rule("leak", "physical", _r_leak), Rule("pride", "social", _r_pride)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard(problem: Problem, vessel: Setting) -> bool:
    return problem.makes_leak and "wet" in problem.tag


def valid_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def leak_severity(problem: Problem, delay: int) -> int:
    return 1 + delay


def contains(fix: Fix, problem: Problem, delay: int) -> bool:
    return fix.power >= leak_severity(problem, delay)


def predict_leak(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _apply_problem(sim, sim.get("vessel"), PROBLEMS[problem_id], narrate=False)
    return {
        "leaking": sim.get("vessel").meters["leaking"] >= THRESHOLD,
        "mud": sim.get("ground").meters["mud"],
    }


def _apply_problem(world: World, vessel: Entity, problem: Problem, narrate: bool = True) -> None:
    vessel.meters["leaking"] += 1
    vessel.meters["soaked"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"On a day broad as a barn door, {hero.id} and {elder.id} stood in {setting.place}. "
        f"{setting.phrase}"
    )
    world.say(f'"Behold," said {elder.id}, "this old boat will sing before supper."')
    world.say(f'"I can almost hear it," said {hero.id}, "and I can help it along."')


def need(world: World, vessel: Entity, problem: Problem) -> None:
    world.say(
        f"But the {vessel.label} had a stubborn {problem.leak}, and the blue sky above looked as if it were waiting to laugh."
    )


def boast(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'"{problem.test}?" {hero.id} said. "That is smaller than a grasshopper\'s sneeze. I could fix it with one hand tied to a fence post."'
    )


def warn(world: World, elder: Entity, hero: Entity, problem: Problem, vessel: Entity) -> None:
    pred = predict_leak(world, problem.id)
    elder.memes["care"] += 1
    world.facts["predicted_mud"] = pred["mud"]
    world.say(
        f'"Now, {hero.id}," said {elder.id}, "if we do not repair this {vessel.label}, the floor will be wet and the yard will turn to mud."'
    )


def decide(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["resolve"] += 1
    world.say(f'"Then let us apply the fix proper," said {hero.id}, and {elder.id} nodded like a rooster on a rail.')


def repair(world: World, hero: Entity, vessel: Entity, fix: Fix, problem: Problem) -> None:
    vessel.meters["repaired"] += 1
    vessel.meters["leaking"] = 0.0
    repair_text = fix.text[0].upper() + fix.text[1:]
    world.say(f'"{repair_text}," cried {hero.id}, and together they set to work.')
    world.say(
        f"They {fix.qa_text.replace('{target}', 'the ' + vessel.label)}. The {vessel.label} stopped dripping, and the old boards held their water like a strong promise."
    )


def failure(world: World, elder: Entity, vessel: Entity, fix: Fix, problem: Problem) -> None:
    vessel.meters["leaking"] += 1
    propagate(world, narrate=False)
    failed = fix.fail.replace("{target}", problem.label)
    if "{target}" not in fix.fail and problem.label not in failed:
        failed = f"{failed} the {vessel.label}"
    world.say(f'"{failed}," muttered {elder.id}.')
    world.say("The leak kept hissing, and the puddle on the boards grew wider than a wagon wheel.")


def ending(world: World, hero: Entity, elder: Entity, vessel: Entity) -> None:
    hero.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"At last the sun leaned low, and the {vessel.label} rode proud and dry. "
        f"{hero.id} grinned so hard it nearly split the horizon, and {elder.id} laughed till the crows bobbed on the fence."
    )


def curtained_ending(world: World, hero: Entity, elder: Entity, vessel: Entity) -> None:
    hero.memes["fear"] += 0
    elder.memes["fear"] += 0
    world.say(
        f"By and by, the {vessel.label} sat under the porch roof, still dripping but no longer flooding the yard, and {hero.id} promised to try a wiser fix tomorrow."
    )


def tell(setting: Setting, problem: Problem, fix: Fix, delay: int, hero_name: str, elder_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type="grandfather", role="elder"))
    vessel = world.add(Entity(id="vessel", kind="thing", type="boat", label=problem.label))
    world.add(Entity(id="ground", kind="thing", type="ground", label="ground"))

    intro(world, hero, elder, setting)
    world.para()
    need(world, vessel, problem)
    boast(world, hero, problem)
    warn(world, elder, hero, problem, vessel)
    decide(world, hero, elder)

    if contains(fix, problem, delay):
        world.para()
        repair(world, hero, vessel, fix, problem)
        ending(world, hero, elder, vessel)
    else:
        world.para()
        failure(world, elder, vessel, fix, problem)
        curtained_ending(world, hero, elder, vessel)

    world.facts.update(hero=hero, elder=elder, vessel=vessel, setting=setting, problem=problem, fix=fix, delay=delay,
                       outcome="contained" if contains(fix, problem, delay) else "failed")
    return world


SETTINGS = {
    "river": Setting(id="river", place="the riverbank", sky="wide", phrase="The river glittered like a silver ribbon, and the wind whistled over the reeds."),
    "dock": Setting(id="dock", place="the old dock", sky="open", phrase="The boards creaked and the gulls hollered as if they knew a secret."),
    "yard": Setting(id="yard", place="the back yard", sky="sunny", phrase="A barn leaned nearby, and the fence cast long stripes of shade."),
}

PROBLEMS = {
    "boat": Problem(id="boat", label="boat", leak="tiny hull leak", test="Can a thimble fill a pond", at_risk="the boat", danger="sinking", tag="wet"),
    "barrel": Problem(id="barrel", label="barrel", leak="crack in the barrel", test="Can a mouse pull a moon", at_risk="the barrel", danger="sloshing", tag="wet"),
    "tub": Problem(id="tub", label="tub", leak="hole in the washtub", test="Can a broom whistle in a storm", at_risk="the tub", danger="dripping", tag="wet"),
}

FIXES = {
    "tar": Fix(id="tar", label="tar patch", sense=3, power=3, text="fetch the tar patch and slap it on the leak",
               fail="the tar patch was not enough to muffle the leak in", qa_text="applied the tar patch to {target}", tags={"patch"}),
    "plank": Fix(id="plank", label="wooden plank", sense=3, power=2, text="set a wooden plank over the crack and hammered it tight",
                 fail="the wooden plank only clattered against", qa_text="applied the wooden plank over {target}", tags={"plank"}),
    "clay": Fix(id="clay", label="river clay", sense=2, power=1, text="pressed river clay into the seam with both thumbs",
                fail="the river clay slid right back out of", qa_text="applied the river clay to {target}", tags={"clay"}),
    "water": Fix(id="water", label="bucket of water", sense=1, power=1, text="threw a bucket of water at the leak",
                 fail="the bucket of water only made more splashing around", qa_text="applied the bucket of water to {target}", tags={"water"}),
}

HERO_NAMES = ["Jeb", "Mabel", "Kit", "Annie", "Hank", "Josie", "Ned", "Ruth"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    hero_name: str
    elder_name: str
    delay: int = 0
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            if not hazard(PROBLEMS[p], SETTINGS[s]):
                continue
            for f in valid_fixes():
                if contains(f, PROBLEMS[p], 0):
                    combos.append((s, p, f.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about behold/apply and a stubborn repair.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--elder")
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(f"(Refusing fix '{args.fix}': it is too weak for a tall tale.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, p, f = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(["Uncle Amos", "Gran", "Old Silas", "Aunt Pearl"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting=s, problem=p, fix=f, hero_name=hero, elder_name=elder, delay=delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for children that uses the words "behold" and "apply" and includes dialogue about fixing a {f["problem"].label}.',
        f'Tell a lively old-time story where {f["hero"].id} and {f["elder"].id} discover a leak and apply a smart repair.',
        f'Write a short story with a boast, a warning, and a repair, in a tall-tale voice, and use the word "behold".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, vessel, problem, fix = f["hero"], f["elder"], f["vessel"], f["problem"], f["fix"]
    if f["outcome"] == "contained":
        ans = (
            f"{hero.id} and {elder.id} saw that the {vessel.label} had a {problem.leak}. "
            f"{elder.id} warned that it would make the ground wet, and then they {fix.qa_text.replace('{target}', vessel.label)}. "
            f"That is why the leak stopped and the ending image is dry and proud."
        )
    else:
        ans = (
            f"{hero.id} and {elder.id} tried to fix the {vessel.label}, but the chosen repair was too weak. "
            f"The leak kept going, so the puddle grew and the boat stayed in trouble."
        )
    return [
        QAItem(question=f"Why did the elder speak so seriously about the {vessel.label}?", answer=ans),
        QAItem(question="What changed by the end of the story?", answer=(
            f"The wetness changed. Before the repair, the {vessel.label} was leaking; after the repair, it was dry enough to ride proud."
        )),
        QAItem(question=f"What did {hero.id} say that showed the tall-tale style?", answer=(
            f'{hero.id} boasted with a huge comparison, saying the problem was so small it was smaller than a grasshopper\'s sneeze.'
        )),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does behold mean?", answer="It is a way to say, 'Look here!' or 'Take a good look at this!'"),
        QAItem(question="What does apply mean?", answer="It means to put something on carefully, like applying a patch, glue, or paint."),
        QAItem(question="Why can a leak be a problem?", answer="A leak lets water escape where it should stay, and that can make a mess or spoil a ride."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="river", problem="boat", fix="tar", hero_name="Jeb", elder_name="Uncle Amos", delay=0),
    StoryParams(setting="dock", problem="barrel", fix="plank", hero_name="Mabel", elder_name="Gran", delay=1),
    StoryParams(setting="yard", problem="tub", fix="clay", hero_name="Kit", elder_name="Old Silas", delay=0),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("invalid setting")
    if params.problem not in PROBLEMS:
        raise StoryError("invalid problem")
    if params.fix not in FIXES:
        raise StoryError("invalid fix")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix], params.delay, params.hero_name, params.elder_name)
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


ASP_RULES = r"""
hazard(P) :- problem(P), wet(P).
sensible(F) :- fix(F), sense(F,S), min_sense(M), S >= M.
valid(S,P,F) :- setting(S), problem(P), fix(F), hazard(P), sensible(F).
contained(F,P,D) :- power(F, Pow), severity(P,D, Sev), Pow >= Sev.
outcome(contained) :- contained(F,P,D).
outcome(failed) :- not contained(F,P,D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS.values():
        lines.append(asp.fact("problem", p.id))
        lines.append(asp.fact("wet", p.id))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
        lines.append(asp.fact("sense", f.id, f.sense))
        lines.append(asp.fact("power", f.id, f.power))
    lines.append(asp.fact("min_sense", SENSE_MIN))
    for p in PROBLEMS.values():
        for d in [0, 1, 2]:
            lines.append(asp.fact("severity", p.id, d, leak_severity(p, d)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, fix=None, hero=None, elder=None, delay=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"FAIL: smoke test crashed: {e}")
        return 1
    return rc


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
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
