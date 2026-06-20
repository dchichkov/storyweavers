#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/diffuse_procrastinator_cautionary_fable.py
==========================================================================

A standalone story world for a small cautionary fable built from the seed words
"diffuse" and "procrastinator".

Premise
-------
A procrastinating young animal keeps putting off a simple safety task in a tiny
village or garden. A wise elder notices that a danger can *diffuse* quickly
through the scene -- smoke, scent, seeds, or worry spreading farther and farther
if no one acts. The story turns when the protagonist stops delaying, gets help,
and learns that small tasks should not be left for later.

The world is designed to read like a fable: concrete animals, a clear warning,
a brief consequence, a turn to action, and a closing moral image that shows the
change in habit.

The standard interface:
- build_parser()
- resolve_params()
- generate()
- emit()
- main()

And the requested modes:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sheep", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    scene: str
    exposes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Task:
    id: str
    label: str
    verb: str
    delay_line: str
    warning: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Risk:
    id: str
    label: str
    phrase: str
    spread_word: str
    danger_word: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["hazard"] < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if ent.role in {"protagonist", "elder"}:
                ent.memes["alarm"] += 1
        out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread)]


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


def hazard_at_risk(task: Task, risk: Risk) -> bool:
    return task.id in TASK_TO_RISK and TASK_TO_RISK[task.id] == risk.id


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def is_contained(remedy: Remedy, risk: Risk, delay: int) -> bool:
    return remedy.power >= RISK_SEVERITY[risk.id] + delay


def consequence_level(risk: Risk, delay: int) -> int:
    return RISK_SEVERITY[risk.id] + delay


def predict(world: World, risk_id: str) -> dict:
    sim = world.copy()
    sim.get(risk_id).meters["hazard"] += 1
    propagate(sim, narrate=False)
    return {"alarm": sum(e.memes["alarm"] for e in sim.entities.values())}


def do_task(world: World, protagonist: Entity, task: Task, risk: Risk, narrate: bool = True) -> None:
    protagonist.memes["deferral"] += 1
    protagonist.meters["done"] += 1
    risk_ent = world.get("risk")
    risk_ent.meters["hazard"] += 1
    risk_ent.meters["spread"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, protagonist: Entity, elder: Entity, place: Place, task: Task, risk: Risk) -> None:
    protagonist.memes["hope"] += 1
    elder.memes["care"] += 1
    world.say(
        f"Once in {place.label}, {protagonist.id} the procrastinator loved to say, "
        f'"Later, later," even when the day was busy.'
    )
    world.say(
        f"{elder.id} watched quietly while {place.scene}. {protagonist.id} was supposed "
        f"to {task.verb}, but kept putting it off."
    )


def warn(world: World, elder: Entity, protagonist: Entity, task: Task, risk: Risk) -> None:
    pred = predict(world, "risk")
    world.facts["pred_alarm"] = pred["alarm"]
    world.say(
        f'"If you wait," said {elder.id}, "the {risk.label} can {risk.spread_word} '
        f"through {place_name(world)}."
    )
    world.say(
        f'"{task.warning}," {elder.id} said, "and that is how little troubles become big ones."'
    )


def defy(world: World, protagonist: Entity, task: Task) -> None:
    protagonist.memes["defiance"] += 1
    world.say(
        f"{protagonist.id} heard the warning and still said, "
        f'"I will do it soon." But soon stretched and stretched.'
    )
    world.say(f"{protagonist.id} kept {task.delay_line}.")


def crisis(world: World, protagonist: Entity, risk: Risk) -> None:
    world.say(
        f"Then the {risk.label} began to {risk.spread_word}, and the problem started to "
        f"{risk.danger_word} everywhere at once."
    )
    world.say(
        f"{protagonist.id} jumped up, because even a small delay can turn a tiny matter into a mess."
    )


def resolve(world: World, elder: Entity, remedy: Remedy, risk: Risk) -> None:
    world.get("risk").meters["hazard"] = 0.0
    body = remedy.text.replace("{risk}", risk.label)
    world.say(
        f"{elder.id} came at once and {body}."
    )
    world.say(
        f"The {risk.label} settled, and the air became calm again."
    )


def lesson(world: World, protagonist: Entity, elder: Entity, task: Task) -> None:
    protagonist.memes["wise"] += 1
    protagonist.memes["alarm"] = 0.0
    world.say("For a moment, they were both silent.")
    world.say(
        f"Then {elder.id} said, 'A task delayed is often a trouble multiplied.' "
        f"{protagonist.id} nodded and promised not to be a procrastinator tomorrow."
    )
    world.say(
        f"After that, {protagonist.id} worked first and rested later, which made the day easier."
    )


def ending(world: World, protagonist: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"In the last light of the day, {protagonist.id} finished the chore, swept the path, "
        f"and watched the {place.label} stay neat and still."
    )
    world.say(
        f"{elder.id} smiled, because now {protagonist.id} knew that prompt hands keep small dangers from growing."
    )


def tell(place: Place, task: Task, risk: Risk, remedy: Remedy, protagonist_name: str = "Milo",
         protagonist_type: str = "mouse", elder_name: str = "Tessa",
         elder_type: str = "tortoise", delay: int = 0) -> World:
    world = World()
    protagonist = world.add(Entity(id=protagonist_name, kind="character", type=protagonist_type, role="protagonist"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    risk_ent = world.add(Entity(id="risk", kind="thing", type=risk.id, label=risk.label))
    world.facts["place"] = place
    world.facts["task"] = task
    world.facts["risk_cfg"] = risk
    world.facts["remedy"] = remedy

    setup(world, protagonist, elder, place, task, risk)
    world.para()
    warn(world, elder, protagonist, task, risk)
    defy(world, protagonist, task)
    world.para()
    if is_contained(remedy, risk, delay):
        crisis(world, protagonist, risk)
        resolve(world, elder, remedy, risk)
        lesson(world, protagonist, elder, task)
    else:
        crisis(world, protagonist, risk)
        world.say(
            f"The little trouble spread faster than {protagonist.id} could fix it, though everyone stayed safe."
        )
        world.say(
            f"{elder.id} still taught the same lesson: when the hour is right, do not let it pass you by."
        )
    world.para()
    ending(world, protagonist, elder, place)
    world.facts["outcome"] = "contained" if is_contained(remedy, risk, delay) else "scattered"
    world.facts["delay"] = delay
    return world


@dataclass
@dataclass
class StoryParams:
    place: str
    task: str
    risk: str
    remedy: str
    protagonist_name: str
    protagonist_type: str
    elder_name: str
    elder_type: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


PLACES = {
    "meadow": Place("meadow", "the meadow", "the clover was bright and the path was short", {"seeds", "smoke"}, {"meadow"}),
    "village": Place("village", "the village lane", "the shop windows glowed and the bread smell drifted out", {"smoke", "seeds"}, {"village"}),
}
TASKS = {
    "close_gate": Task("close_gate", "close the garden gate", "close the garden gate", "leaving the gate open", "The wind can slip through and scatter the grain", {"gate"}),
    "cover_honey": Task("cover_honey", "cover the honey jar", "cover the honey jar", "forgetting the lid", "The scent can spread and bring buzzing guests", {"honey"}),
}
RISKS = {
    "bees": Risk("bees", "bee scent", "the bee scent", "diffuse", "attract more bees", True, {"bees"}),
    "smoke": Risk("smoke", "smoke", "the smoke", "diffuse", "fill the lane", True, {"smoke"}),
}
REMEDIES = {
    "lid": Remedy("lid", 3, 4, "put a tight lid on the jar and whisked it away", "tried to help, but the little problem had already grown too large", "put a tight lid on the jar", {"honey"}),
    "net": Remedy("net", 2, 2, "pulled a net over the gate and tied it firm", "pulled at the gate, but the trouble had already spread too far", "pulled a net over the gate", {"gate"}),
}
TASK_TO_RISK = {"cover_honey": "bees", "close_gate": "smoke"}
RISK_SEVERITY = {"bees": 1, "smoke": 2}
SENSE_MIN = 2

GIRL_NAMES = ["Tessa", "Nina", "Iris", "Mira", "Lena"]
BOY_NAMES = ["Milo", "Pip", "Arlo", "Jon", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for t in TASKS:
            for r in RISKS:
                if hazard_at_risk(TASKS[t], RISKS[r]):
                    for rm in REMEDIES:
                        if is_contained(REMEDIES[rm], RISKS[r], 0):
                            out.append((p, t, r))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about procrastination and things that diffuse.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--elder")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.risk is None or c[2] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, risk = rng.choice(sorted(combos))
    remedy = args.remedy or ("lid" if risk == "bees" else "net")
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    if not is_contained(REMEDIES[remedy], RISKS[risk], delay):
        raise StoryError("The chosen remedy is too weak for this cautionary fable.")
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    elder = args.elder or rng.choice(["Tessa", "Otto", "June"])
    return StoryParams(place, task, risk, remedy, name, "mouse", elder, "tortoise", delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary fable for a child that includes the words "diffuse" and "procrastinator".',
        f"Tell a short fable about {f['place'].label} where {f['protagonist'].id} keeps delaying a task and a wise elder warns about what can diffuse.",
        f"Write a moral story where a procrastinator learns that small dangers can spread quickly if nobody acts.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p, e, t, r = f["protagonist"], f["elder"], f["task"], f["risk_cfg"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.id}, a procrastinator, and {e.id}, the wise elder who kept watching over the village. The two of them showed why a small task should not be delayed."
        ),
        QAItem(
            question=f"What did {p.id} keep putting off?",
            answer=f"{p.id} kept putting off the task to {t.label}. That delay mattered because the {r.label} could diffuse and become a bigger problem."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the task finished and the place calm again. {p.id} stopped delaying, which kept the trouble from spreading farther."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does diffuse mean?", "To diffuse means to spread out and move through a place little by little. Smoke, smell, light, or worry can diffuse."),
        QAItem("What is a procrastinator?", "A procrastinator is someone who keeps putting off a task instead of doing it right away. That can turn a small job into a bigger worry."),
        QAItem("Why is it wise to do a small task early?", "Doing a small task early keeps it from growing into a bigger problem later. The sooner you act, the easier it is to keep things calm."),
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "cover_honey", "bees", "lid", "Milo", "mouse", "Tessa", "tortoise", 0),
    StoryParams("village", "close_gate", "smoke", "net", "Iris", "mouse", "June", "tortoise", 1),
]


def explain_rejection(task: Task, risk: Risk) -> str:
    return f"(No story: {task.label} does not honestly lead to a danger involving {risk.label}.)"


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(REMEDIES[params.remedy], RISKS[params.risk], params.delay) else "scattered"


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("sense_min", SENSE_MIN)]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for rid in RISKS:
        lines.append(asp.fact("risk", rid))
    for mid, m in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    for t, r in TASK_TO_RISK.items():
        lines.append(asp.fact("task_risk", t, r))
    for rid, sev in RISK_SEVERITY.items():
        lines.append(asp.fact("severity", rid, sev))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(T,R) :- task_risk(T,R).
sensible(M) :- remedy(M), sense(M,S), sense_min(N), S >= N.
contained(M,R,D) :- power(M,P), severity(R,S), delay(D), P >= S + D.
valid(P,T,R) :- place(P), task(T), risk(R), hazard(T,R).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show contained/3."))
    return "contained" if asp.atoms(model, "contained") else "scattered"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r for r, v in REMEDIES.items() if v.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible remedies")
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome_of()", p)
            break
    try:
        generate(CURATED[0])
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], RISKS[params.risk], REMEDIES[params.remedy],
                 params.protagonist_name, params.protagonist_type, params.elder_name, params.elder_type, params.delay)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary fable storyworld about a procrastinator and things that diffuse.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--elder")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.risk is None or c[2] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, risk = rng.choice(sorted(combos))
    remedy = args.remedy or ("lid" if risk == "bees" else "net")
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    if not is_contained(REMEDIES[remedy], RISKS[risk], delay):
        raise StoryError("The chosen remedy is too weak for this story.")
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    elder = args.elder or rng.choice(["Tessa", "June", "Otto"])
    return StoryParams(place, task, risk, remedy, name, "mouse", elder, "tortoise", delay)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show contained/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        for p, t, r in asp_valid_combos():
            print(f"{p:8} {t:12} {r}")
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
            header = f"### {p.protagonist_name}: {p.task} in {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
