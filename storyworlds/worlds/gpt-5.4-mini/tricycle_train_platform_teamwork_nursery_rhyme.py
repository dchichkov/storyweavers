#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tricycle_train_platform_teamwork_nursery_rhyme.py
=================================================================================

A tiny standalone story world for a nursery-rhyme style tale set on a train
platform, built around a tricycle and teamwork.

Premise:
- A child wants to ride a tricycle on a train platform.
- The platform is crowded and the tricycle is stuck in a wobble or a jam.
- Friends/family team up to make the ride safe and cheerful.
- The ending image proves the tricycle moved with teamwork, and the train did
  not get in the way.

This script follows the shared Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify,
  --show-asp
- includes a Python gate and an inline ASP twin
- generates story-grounded QA and world-knowledge QA from simulated state
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
RHYME_MIN = 1.0


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
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    crowded: bool = False
    paved: bool = True
    has_benches: bool = False
    has_clock: bool = False

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
class RideToy:
    id: str
    label: str
    phrase: str
    wobbly: bool = False
    small_wheels: bool = True

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
class HelperAction:
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    if toy.meters["rolling"] < THRESHOLD:
        return out
    sig = ("wobble", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in list(world.entities.values()):
        if kid.role in {"rider", "helper"}:
            kid.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_teamwork(world: World) -> list[str]:
    if world.get("rider").memes["teamwork"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("toy").meters["steady"] += 1
    world.get("rider").memes["joy"] += 1
    world.get("helper").memes["joy"] += 1
    return ["__steady__"]


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def toy_at_risk(place: Place, toy: RideToy) -> bool:
    return place.paved and toy.small_wheels


def act_will_help(action: HelperAction, toy: RideToy) -> bool:
    return action.power >= (2 if toy.wobbly else 1)


def sensible_actions() -> list[HelperAction]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def _do_try(world: World, toy: Entity, narrate: bool = True) -> None:
    toy.meters["rolling"] += 1
    if toy.meters["rolling"] >= THRESHOLD:
        world.get("rider").memes["hope"] += 1
    propagate(world, narrate=narrate)


def predict(world: World) -> dict:
    sim = world.copy()
    _do_try(sim, sim.get("toy"), narrate=False)
    return {
        "wobbled": sim.get("rider").memes["worry"] >= THRESHOLD,
        "steady": sim.get("toy").meters["steady"] >= THRESHOLD,
    }


def setup(world: World, rider: Entity, helper: Entity, toy: Entity) -> None:
    rider.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"On a train platform bright and neat, {rider.id} and {helper.id} met "
        f"beside the bench and the ticking feet of the clock."
    )
    world.say(
        f"They shared a little tricycle, red and round, with shiny bars and "
        f"tiny wheels all bound for a gentle spin."
    )


def problem(world: World, rider: Entity, helper: Entity, toy: Entity) -> None:
    world.say(
        f"But the platform was busy, with boots and bags and a puffing train, "
        f"and the tricycle wanted to roll, but it wobbled in place again."
    )
    world.say(
        f'"It wants to go," said {rider.id}, "but the little wheels do not know the way."'
    )


def warn(world: World, helper: Entity, rider: Entity, toy: Entity) -> None:
    pred = predict(world)
    helper.memes["care"] += 1
    world.facts["pred"] = pred
    world.say(
        f'{helper.id} touched the handlebar and nodded slow. '
        f'"If we rush, it may tip and sway. Let us help it steady, '
        f'and then it can ride the happy way."'
    )


def teamwork(world: World, rider: Entity, helper: Entity, toy: Entity) -> None:
    rider.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    toy.meters["steady"] += 1
    world.say(
        f'{rider.id} held the handlebars, and {helper.id} walked beside. '
        f'One pushed softly, one guided true, and the tricycle learned to glide.'
    )


def resolution(world: World, rider: Entity, helper: Entity, toy: Entity, action: HelperAction) -> None:
    toy.meters["rolling"] = 0.0
    world.say(
        f'With a little teamwork and a patient tune, the {toy.label} rolled '
        f'smooth as a nursery rhyme moon.'
    )
    world.say(
        f"{action.text} {rider.id} laughed, {helper.id} clapped, and the train "
        f"sat still while the tricycle went by."
    )


def fail_resolution(world: World, rider: Entity, helper: Entity, toy: Entity, action: HelperAction) -> None:
    world.say(
        f"{action.fail}. So they stepped aside, took a breath, and tried another plan."
    )
    world.say(
        f"They steadied the tricycle with patient hands, and the little ride "
        f"could begin again."
    )
    world.get("toy").meters["steady"] += 1
    world.get("toy").meters["rolling"] = 0.0
    world.get("rider").memes["joy"] += 1
    world.get("helper").memes["joy"] += 1


def tell(place: Place, toy_cfg: RideToy, action: HelperAction,
         rider_name: str = "Mia", rider_gender: str = "girl",
         helper_name: str = "Noah", helper_gender: str = "boy") -> World:
    world = World(place)
    rider = world.add(Entity(id=rider_name, kind="character", type=rider_gender, role="rider"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label=toy_cfg.label))
    toy.meters["wobble"] = 1.0 if toy_cfg.wobbly else 0.0

    setup(world, rider, helper, toy)
    world.para()
    problem(world, rider, helper, toy)
    warn(world, helper, rider, toy)

    if not toy_at_risk(place, toy_cfg):
        raise StoryError("This platform scene needs a ride toy that can realistically wobble.")
    if not act_will_help(action, toy_cfg):
        raise StoryError("This helper action is too weak for the tricycle scene.")

    world.para()
    teamwork(world, rider, helper, toy)
    _do_try(world, toy)
    if world.get("toy").meters["steady"] >= THRESHOLD:
        resolution(world, rider, helper, toy, action)
    else:
        fail_resolution(world, rider, helper, toy, action)

    world.facts.update(
        rider=rider, helper=helper, toy=toy, place=place, action=action,
        steady=world.get("toy").meters["steady"] >= THRESHOLD,
        wobbled=world.get("rider").memes["worry"] >= THRESHOLD,
    )
    return world


PLACES = {
    "train_platform": Place(
        "train_platform", "the train platform", crowded=True, paved=True, has_benches=True, has_clock=True
    ),
}

TOYS = {
    "tricycle": RideToy("tricycle", "tricycle", "a little tricycle", wobbly=True, small_wheels=True),
}

ACTIONS = {
    "guide": HelperAction(
        "guide", 3, 2, "They guided the tricycle with calm hands and a cheerful grin.",
        "The quick shove did not help, and the tricycle wobbled harder.",
        "They guided the tricycle with calm hands and a cheerful grin.",
        tags={"teamwork", "tricycle"},
    ),
    "push": HelperAction(
        "push", 2, 2, "Together they gave it a careful push, then a gentle walk.",
        "The push was too hurried, and the tricycle wiggled like a twirl.",
        "Together they gave it a careful push, then a gentle walk.",
        tags={"teamwork", "tricycle"},
    ),
    "steady": HelperAction(
        "steady", 3, 3, "Then the little tricycle went straight as a song.",
        "It still leaned and nearly tipped, so they had to slow down.",
        "Then the little tricycle went straight as a song.",
        tags={"teamwork", "tricycle"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Theo", "Ben", "Max"]
TRAITS = ["gentle", "cheerful", "careful", "brave", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TOYS:
            for a in ACTIONS:
                if toy_at_risk(PLACES[p], TOYS[t]) and act_will_help(ACTIONS[a], TOYS[t]):
                    combos.append((p, t, a))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    toy: str
    action: str
    rider: str
    rider_gender: str
    helper: str
    helper_gender: str
    trait: str
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


KNOWLEDGE = {
    "tricycle": [("What is a tricycle?", "A tricycle is a small ride toy with three wheels. It is steadier than a bicycle because it has an extra wheel.")],
    "train_platform": [("What is a train platform?", "A train platform is the place where people wait for a train. It can be busy, so people need to stay careful there.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other and work together to do something well.")],
    "steady": [("What does it mean to steady something?", "To steady something means to hold it so it does not wobble or tip over.")],
    "crowded": [("Why should you be careful in a crowded place?", "When a place is crowded, there are many people nearby, so it is safer to move slowly and pay attention.")],
}
KNOWLEDGE_ORDER = ["train_platform", "crowded", "tricycle", "teamwork", "steady"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a nursery-rhyme style story set on a train platform that includes the word "tricycle" and shows teamwork.',
        f"Tell a gentle story about {f['rider'].id} and {f['helper'].id} helping a tricycle move safely on a train platform.",
        "Write a short rhyming story where two children work together to steady a wobbly tricycle near a train platform bench.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider, helper, place, toy = f["rider"], f["helper"], f["place"], f["toy"]
    qa = [
        ("Where is the story set?", f"It is set on {place.label}. The bench, the clock, and the train platform make the scene feel like a little rhyme."),
        ("What were the children trying to do?", f"They were trying to help the tricycle roll safely. They wanted it to move without wobbling on the busy platform."),
        ("How did they solve the problem?", f"They used teamwork and moved slowly together. One guided while the other steadied the tricycle, so it stopped wobbling and went straight."),
        ("How did the ending show that things changed?", f"At the end, the tricycle rolled smoothly and the children were happy. That proves the teamwork worked and the ride became safe."),
    ]
    if f.get("wobbled"):
        qa.append((
            f"Why did {rider.id} need help?",
            f"{rider.id} needed help because the tricycle wobbled on the crowded platform. The extra hands kept it steady near the train."
        ))
    if f.get("steady"):
        qa.append((
            "What changed after the teamwork?",
            f"The tricycle became steady, and the children could ride with smiles. The wobble was gone, so the scene ended in a calm, bright way."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tricycle", "train_platform", "teamwork", "steady", "crowded"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the requested train-platform tricycle scene needs teamwork that actually steadies a wobbly little ride.)"


ASP_RULES = r"""
risk(P, T) :- place(P), toy(T), paved(P), small_wheels(T).
helpful(A, T) :- action(A), toy(T), power(A, PWR), PWR >= 2.
steady(T) :- teamwork, toy(T).
valid(P, T, A) :- risk(P, T), helpful(A, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].paved:
            lines.append(asp.fact("paved", pid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
        if TOYS[tid].small_wheels:
            lines.append(asp.fact("small_wheels", tid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("teamwork", 1))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        _ = format_qa(sample)
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme train-platform tricycle teamwork story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--rider")
    ap.add_argument("--rider-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.toy is None or c[1] == args.toy)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError(explain_rejection())
    place, toy, action = rng.choice(sorted(combos))
    rider_gender = args.rider_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if rider_gender == "girl" else "girl")
    rider = args.rider or rng.choice(GIRL_NAMES if rider_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != rider])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, toy, action, rider, rider_gender, helper, helper_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    rider = world.add(Entity(id=params.rider, kind="character", type=params.rider_gender, role="rider", traits=[params.trait]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["kind"]))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label=TOYS[params.toy].label))
    toy.meters["rolling"] = 0.0
    toy.meters["steady"] = 0.0
    world.facts.update(rider=rider, helper=helper, toy=toy, place=world.place, action=ACTIONS[params.action])

    world.say(
        f"On a train platform bright and neat, {rider.id} and {helper.id} met beside the bench and the ticking feet of the clock. "
        f"They shared a little tricycle, red and round, with shiny bars and tiny wheels all bound for a gentle spin."
    )
    world.para()
    problem(world, rider, helper, toy)
    warn(world, helper, rider, toy)
    teamwork(world, rider, helper, toy)
    _do_try(world, toy)
    action = ACTIONS[params.action]
    resolution(world, rider, helper, toy, action)
    world.facts["wobbled"] = world.get("rider").memes["worry"] >= THRESHOLD
    world.facts["steady"] = world.get("toy").meters["steady"] >= THRESHOLD
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


CURATED = [
    StoryParams("train_platform", "tricycle", "guide", "Mia", "girl", "Noah", "boy", "gentle"),
    StoryParams("train_platform", "tricycle", "push", "Leo", "boy", "Ava", "girl", "careful"),
    StoryParams("train_platform", "tricycle", "steady", "Nora", "girl", "Ben", "boy", "brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
