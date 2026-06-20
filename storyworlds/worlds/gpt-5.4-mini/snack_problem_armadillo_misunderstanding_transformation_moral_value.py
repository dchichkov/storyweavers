#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snack_problem_armadillo_misunderstanding_transformation_moral_value.py
====================================================================================================

A standalone story world for a tiny space-adventure tale about a snack,
a misunderstanding, an armadillo, a transformation, and a moral value.

Premise:
- Two small explorers on a moon base share a snack.
- One explorer misunderstands a strange armadillo-shaped visitor.
- The visitor's shell can transform when it absorbs light and dust.
- The misunderstanding creates a small problem, then a calm fix.
- The ending leaves a clear moral value: ask first, share kindly, and do not
  judge by looks alone.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly for QAItem, StoryError, StorySample
- includes build_parser, resolve_params, generate, emit, main
- supports --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness checks and an inline ASP twin
- grounded QA from world state, not from parsing rendered prose
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
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class World:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)

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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    zone: set[str]
    mess: str
    weather: str
    keyword: str
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
class Snack:
    id: str
    label: str
    phrase: str
    smell: str
    fragile: bool = False
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
class Problem:
    id: str
    label: str
    phrase: str
    cause: str
    fix: str
    power: int
    sense: int
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
class Armadillo:
    id: str
    label: str
    phrase: str
    shell: str
    transform: str
    transforms_from: str
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


class Rule:
    def __init__(self, name: str, apply: Callable[[World], list[str]]) -> None:
        self.name = name
        self.apply = apply


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    explorer = world.get("explorer")
    if explorer.meters["confusion"] < THRESHOLD:
        return out
    sig = ("confusion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character" and ent.id != "explorer":
            ent.memes["worry"] += 1
    out.append("__confusion__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    arm = world.get("armadillo")
    if arm.meters["sparkle"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    arm.meters["transformed"] = 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion), Rule("transform", _r_transformation)]


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


def reasonableness_ok(setting: Setting, activity: Activity, snack: Snack, problem: Problem) -> bool:
    return activity.id in setting.affords and problem.sense >= 2 and snack.id == "snack"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            for snid, snack in SNACKS.items():
                for pid, prob in PROBLEMS.items():
                    if reasonableness_ok(setting, act, snack, prob) and act.keyword in prob.tags:
                        combos.append((sid, aid, snid, pid))
    return combos


def predict_problem(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_misunderstanding(sim, narrate=False)
    return {"confused": sim.get("explorer").meters["confusion"] >= THRESHOLD,
            "worry": sim.get("pilot").memes["worry"]}


def _do_misunderstanding(world: World, narrate: bool = True) -> None:
    explorer = world.get("explorer")
    pilot = world.get("pilot")
    arm = world.get("armadillo")
    snack = world.get("snack")
    explorer.meters["confusion"] += 1
    explorer.memes["alarm"] += 1
    arm.meters["sparkle"] += 1
    world.say(
        f"{explorer.id} stared at the {arm.label} and thought the shiny shell meant trouble."
    )
    world.say(
        f"{pilot.id} noticed the {snack.label} in {explorer.id}'s hand and moved closer."
    )
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, snack: Snack, problem: Problem, armadillo: Armadillo,
         explorer_name: str = "Mina", explorer_gender: str = "girl",
         pilot_name: str = "Rex", pilot_gender: str = "boy") -> World:
    world = World()
    explorer = world.add(Entity(id="explorer", kind="character", type=explorer_gender, label=explorer_name, role="explorer"))
    pilot = world.add(Entity(id="pilot", kind="character", type=pilot_gender, label=pilot_name, role="pilot"))
    arm = world.add(Entity(id="armadillo", kind="character", type="thing", label=armadillo.label, role="visitor"))
    s = world.add(Entity(id="snack", kind="thing", type="thing", label=snack.label))
    p = world.add(Entity(id="problem", kind="thing", type="thing", label=problem.label))
    world.facts.update(setting=setting, activity=activity, snack=snack, problem=problem, armadillo=armadillo,
                       explorer=explorer, pilot=pilot, arm=arm, snack_ent=s, problem_ent=p)

    explorer.memes["curiosity"] += 1
    pilot.memes["care"] += 1
    arm.meters["shell"] += 1

    world.say(
        f"At {setting.place}, {explorer.label} and {pilot.label} were on a quiet space walk."
    )
    world.say(
        f"They carried {snack.phrase}, and the {snack.smell} smell made the cabin feel cheerful."
    )
    world.say(
        f"Near the airlock, an {armadillo.label} appeared with {armadillo.phrase} and a {armadillo.shell}."
    )
    world.say(
        f"{explorer.label} wanted to {activity.verb}, but the moon dust around the hatch made the problem feel bigger."
    )

    world.para()
    world.say(
        f"Then a misunderstanding began: {explorer.label} thought the shining shell hid a problem, but it was only the {armadillo.label} transforming under the stars."
    )
    world.say(
        f"{pilot.label} saw that the {armadillo.label} was not a threat at all, just a visitor with a bright little change."
    )

    _do_misunderstanding(world, narrate=False)
    world.para()
    world.say(
        f"{pilot.label} smiled and offered the {snack.label} instead of hiding from the {armadillo.label}."
    )
    world.say(
        f"The {armadillo.label} calmed down, took a careful bite, and its shell settled into a soft, glowing shape."
    )
    explorer.memes["understanding"] += 1
    pilot.memes["kindness"] += 1
    arm.memes["trust"] += 1
    world.say(
        f"{explorer.label} apologized for guessing too fast and learned the moral value of asking first."
    )
    world.say(
        f"By the time they floated back to the ship, the {snack.label} was shared, the problem was gone, and the {armadillo.label} looked like a tiny star with a new name."
    )

    world.facts.update(outcome="resolved", lesson="ask_first", transformed=True, shared=True)
    return world


SETTINGS = {
    "moonbase": Setting("moonbase", "the moon base", "silver walls and tiny portholes", {"walk", "watch"}),
    "orbit": Setting("orbit", "the orbiting station", "a round window over the blue planet", {"walk", "watch"}),
    "starport": Setting("starport", "the starport", "bright docks and humming lights", {"walk", "watch"}),
}

ACTIVITIES = {
    "watch": Activity("watch", "watch the stars", "watching the stars", "float closer to the window", {"torso"}, "dusty", "", "stars", {"space", "quiet"}),
    "walk": Activity("walk", "take a moon walk", "taking a moon walk", "drift toward the hatch", {"feet", "torso"}, "dusty", "clear", "moon", {"space", "moon"}),
}

SNACKS = {
    "snack": Snack("snack", "snack", "a warm snack pack", "sweet", tags={"snack"}),
    "crackers": Snack("crackers", "crackers", "a tin of star crackers", "salty", tags={"snack"}),
    "berries": Snack("berries", "berries", "a pouch of berry bits", "fruity", tags={"snack"}),
}

PROBLEMS = {
    "problem": Problem("problem", "problem", "a little problem", "confusion", "ask kindly", 3, 3, tags={"problem", "misunderstanding"}),
    "alarm": Problem("alarm", "alarm", "a false alarm", "confusion", "check first", 2, 2, tags={"problem", "misunderstanding"}),
}

ARMADILLOS = {
    "armadillo": Armadillo("armadillo", "armadillo", "a round pack and a tiny helmet", "shell of silver dust", "glowing brighter", "quiet and plain", tags={"armadillo"}),
    "stararmadillo": Armadillo("stararmadillo", "armadillo", "a tiny map pouch and a scarf", "shell of starlight", "turning gold", "dusty and dim", tags={"armadillo", "transformation"}),
}

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nia", "Zara"]
BOY_NAMES = ["Rex", "Nova", "Kai", "Jett", "Pax"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the words "snack", "problem", and "armadillo".',
        f"Tell a gentle story where {f['explorer'].label} misunderstands an {f['arm'].label}, then learns the truth and shares a snack.",
        f"Write a story with a misunderstanding, a transformation, and a moral value about asking first, set on a moon base.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    explorer: Entity = f["explorer"]
    pilot: Entity = f["pilot"]
    arm: Entity = f["arm"]
    snack: Snack = f["snack"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {explorer.label}, {pilot.label}, and the {arm.label}. They are on a small space trip where a snack and a misunderstanding matter."
        ),
        QAItem(
            question="What was the misunderstanding?",
            answer=f"{explorer.label} thought the {arm.label}'s bright shell meant there was a problem. It was really just a transformation under the moon lights."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"{pilot.label} offered {snack.phrase} and spoke calmly. That helped everyone see the {arm.label} was friendly, so the problem faded."
        ),
        QAItem(
            question="What moral value did {0} learn?".format(explorer.label),
            answer="They learned to ask first and not judge by looks alone. Kind questions fixed the worry better than guessing."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    snack: Snack = f["snack"]
    armadillo: Armadillo = f["armadillo"]
    return [
        QAItem(
            question="What is a snack?",
            answer="A snack is a small bit of food you eat between bigger meals. It can help you feel happy and not hungry."
        ),
        QAItem(
            question="What is an armadillo?",
            answer="An armadillo is an animal with a hard shell on its back. It can curl up and looks a little like a tiny armored ball."
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new shape or look. In stories, a transformation can make a character seem surprising."
        ),
        QAItem(
            question="Why should you ask first?",
            answer="Asking first helps you learn the truth before you decide what something means. That keeps small misunderstandings from becoming bigger problems."
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {e.label:12} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)




def explain_rejection(setting: Setting, activity: Activity, snack: Snack, problem: Problem) -> str:
    if not reasonableness_ok(setting, activity, snack, problem):
        return "(No story: this combination does not make a clear space problem that can turn into a gentle misunderstanding and fix.)"
    return "(No story: this combination is too thin for the intended space-adventure plot.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for snid in SNACKS:
        lines.append(asp.fact("snack", snid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for aid, act in ACTIVITIES.items():
        for t in act.tags:
            lines.append(asp.fact("act_tag", aid, t))
    for pid, p in PROBLEMS.items():
        for t in p.tags:
            lines.append(asp.fact("prob_tag", pid, t))
        lines.append(asp.fact("sense", pid, p.sense))
    return "\n".join(lines)


ASP_RULES = r"""
ok(S,A,Sn,P) :- setting(S), activity(A), snack(Sn), problem(P), sense(P, Sen), Sen >= 2, act_tag(A, space), prob_tag(P, misunderstanding).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show ok/4."))
    return sorted(set(asp.atoms(model, "ok")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid combos")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
        rc = 1
    sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(777)))
    if not sample.story.strip():
        print("MISMATCH: generate produced empty story")
        rc = 1
    else:
        print("OK: generate smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a snack, a problem, an armadillo, and a lesson in kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--explorer")
    ap.add_argument("--pilot")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random):
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combinations available.")
    filtered = [c for c in combos if (args.setting is None or c[0] == args.setting)
                and (args.activity is None or c[1] == args.activity)
                and (args.snack is None or c[2] == args.snack)
                and (args.problem is None or c[3] == args.problem)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    sid, aid, snid, pid = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    explorer = args.explorer or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    pilot = args.pilot or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != explorer])
    return StoryParams(sid, aid, snid, pid, explorer, pilot, gender)


@dataclass
class StoryParams:
    setting: str
    activity: str
    snack: str
    problem: str
    explorer: str
    pilot: str
    gender: str
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

CURATED = [
    ("moonbase", "watch", "snack", "armadillo"),
    ("orbit", "walk", "crackers", "stararmadillo"),
    ("starport", "watch", "berries", "armadillo"),
]



def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], SNACKS[params.snack], PROBLEMS[params.problem], ARMADILLOS["armadillo"], params.explorer, params.gender, params.pilot, "boy")
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
        print(asp_program("", "#show ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, a, sn, p, "Mina", "Rex", "girl")) for s, a, sn, p in CURATED]
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
            header = f"### {p.explorer}: {p.setting}, {p.activity}, {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
