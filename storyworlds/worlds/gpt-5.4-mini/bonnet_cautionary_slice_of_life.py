#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bonnet_cautionary_slice_of_life.py
===================================================================

A small standalone story world about a child, a bonnet, a windy outing, a
warning, and a calm fix. The tone stays close to slice-of-life: ordinary places,
family routines, small feelings, and a gentle cautionary turn.

The world models one compact premise:
- a child loves wearing a bonnet outside,
- a breeze or small mishap threatens it,
- a caregiver notices the risk and warns early,
- the child either listens right away or learns through a small scare,
- the ending proves what changed: the bonnet is tied properly, tucked away,
  dried off, or replaced with a safer routine.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports results eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes Python validity checks and inline ASP twin
- generates three QA sets from world state, not by parsing rendered prose
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
SAFE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)



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
    detail: str
    weather: str
    outdoor: bool = True

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
class Bonnet:
    id: str
    label: str
    phrase: str
    ties: bool
    brim: str
    can_blow_off: bool = True
    can_get_wet: bool = True
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
    risk: int
    prevent: int
    text: str
    warning: str
    fix: str
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


def _r_wind(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["wind"] < THRESHOLD:
            continue
        sig = ("wind", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.attrs.get("bonnet_worn"):
            bonnet = world.get(ent.attrs["bonnet_worn"])
            if bonnet.meters["tied"] < THRESHOLD:
                bonnet.meters["blown"] += 1
                ent.memes["surprise"] += 1
                out.append("__bonnet_slip__")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["blown"] < THRESHOLD and ent.meters["wet"] < THRESHOLD:
            continue
        sig = ("spoil", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["mussed"] += 1
        out.append("__bonnet_mussed__")
    return out


CAUSAL_RULES = [Rule("wind", "physical", _r_wind), Rule("spoil", "physical", _r_spoil)]


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


def risk_at_hand(problem: Problem, bonnet: Bonnet) -> bool:
    return problem.risk > 0 and bonnet.can_blow_off


def sensible_fixes() -> list[Problem]:
    return [p for p in PROBLEMS.values() if p.prevent >= SAFE_MIN]


def best_fix() -> Problem:
    return max(PROBLEMS.values(), key=lambda p: p.prevent)


def predict(world: World, child_id: str) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    child.meters["wind"] += 1
    propagate(sim, narrate=False)
    bonnet_id = child.attrs.get("bonnet_worn")
    bonnet = sim.get(bonnet_id) if bonnet_id else None
    return {
        "slips": bool(bonnet and bonnet.meters["blown"] >= THRESHOLD),
        "mussed": bool(bonnet and bonnet.meters["mussed"] >= THRESHOLD),
    }


def gust(world: World, child: Entity, bonnet: Entity) -> None:
    child.meters["wind"] += 1
    propagate(world, narrate=False)
    if bonnet.meters["blown"] >= THRESHOLD:
        world.say("A little gust tugged at the ribbon and nearly lifted the bonnet away.")
    else:
        world.say("A little gust rattled the ribbon, but the bonnet stayed in place.")


def introduce(world: World, child: Entity, parent: Entity, setting: Setting, bonnet: Bonnet) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a quiet morning, {child.id} and {parent.label_word} went to {setting.place}. "
        f"{setting.detail} {child.id} wore {bonnet.phrase} because it felt neat and warm."
    )
    world.say(
        f"{child.id} liked the way {bonnet.label} sat under {child.pronoun('possessive')} chin and made the day feel special."
    )


def warn(world: World, parent: Entity, child: Entity, bonnet: Bonnet, problem: Problem) -> None:
    pred = predict(world, child.id)
    parent.memes["care"] += 1
    world.facts["pred"] = pred
    line = f'"{problem.warning}," {parent.id} said.'
    if pred["slips"]:
        line += f' "{bonnet.label} could blow off if the wind picks up."'
    world.say(line)


def ignore(world: World, child: Entity, bonnet: Bonnet, problem: Problem) -> None:
    child.memes["stubborn"] += 1
    world.say(
        f'{child.id} touched the ribbon and frowned. "{problem.text}," {child.pronoun()} said, '
        f"and kept walking anyway."
    )
    bonnet.meters["tied"] += 0.2


def listen(world: World, child: Entity, parent: Entity, bonnet: Bonnet, problem: Problem) -> None:
    child.memes["trust"] += 1
    bonnet.meters["tied"] += 1
    child.attrs["bonnet_worn"] = bonnet.id
    world.say(
        f'{child.id} nodded and let {parent.pronoun("object")} tie the ribbon more snugly. '
        f'"{problem.fix}," {parent.pronoun()} said, and {child.id} smiled.'
    )


def mishap(world: World, child: Entity, bonnet: Entity, problem: Problem) -> None:
    gust(world, child, bonnet)
    if bonnet.meters["blown"] >= THRESHOLD:
        world.say(
            f"The ribbon slipped, the brim tipped sideways, and for a moment {child.id} had to catch it with both hands."
        )
    else:
        world.say(
            f"The bonnet bobbed once in the wind, but the small scare passed quickly."
        )


def repair(world: World, parent: Entity, child: Entity, bonnet: Bonnet) -> None:
    bonnet.meters["tied"] += 1
    bonnet.meters["blown"] = 0
    child.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} stopped by a bench, fixed the ribbon, and tucked the bonnet under {child.pronoun('possessive')} chin."
    )
    world.say(
        f"This time the bonnet stayed neat, and {child.id} could keep walking without holding onto it."
    )


def ending(world: World, child: Entity, parent: Entity, bonnet: Bonnet, setting: Setting) -> None:
    if bonnet.meters["mussed"] >= THRESHOLD:
        world.say(
            f"By the time they reached home, the bonnet was a little rumpled, but it was dry again on the hook by the door."
        )
    else:
        world.say(
            f"At the end of the walk, the bonnet sat straight and tidy, and {child.id} skipped beside {parent.id} feeling proud."
        )


def tell(setting: Setting, bonnet: Bonnet, problem: Problem,
         child_name: str = "Mia", child_type: str = "girl",
         parent_name: str = "Mom", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent"))
    b = world.add(Entity(id=bonnet.id, type="bonnet", label=bonnet.label))
    child.attrs["bonnet_worn"] = b.id

    introduce(world, child, parent, setting, bonnet)
    world.para()
    warn(world, parent, child, bonnet, problem)

    if world.facts["pred"]["slips"]:
        if problem.prevent >= SAFE_MIN:
            listen(world, child, parent, bonnet, problem)
            repair(world, parent, child, bonnet)
        else:
            ignore(world, child, bonnet, problem)
            world.para()
            mishap(world, child, b, problem)
            repair(world, parent, child, bonnet)
    else:
        listen(world, child, parent, bonnet, problem)
        world.para()
        ending(world, child, parent, bonnet, setting)

    world.facts.update(
        child=child,
        parent=parent,
        bonnet=b,
        setting=setting,
        bonnet_cfg=bonnet,
        problem=problem,
        outcome="protected" if bonnet.meters["tied"] >= THRESHOLD else "slipped",
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "The path had soft grass and a bright row of flowers.", "breezy", True),
    "market": Setting("market", "the market", "The stalls were busy, and people carried baskets past the bread cart.", "breezy", True),
    "walk": Setting("walk", "the sidewalk", "The neighborhood felt calm, with porches and slow bicycles nearby.", "breezy", True),
    "porch": Setting("porch", "the porch", "The porch was shaded and still, with a little chair by the steps.", "calm", True),
}

BONNETS = {
    "blue": Bonnet("bonnet", "blue bonnet", "a blue bonnet", True, "soft"),
    "floral": Bonnet("bonnet", "floral bonnet", "a floral bonnet", True, "wide"),
    "sun": Bonnet("bonnet", "sun bonnet", "a sun bonnet", True, "light"),
}

PROBLEMS = {
    "wind": Problem("wind", risk=1, prevent=3, text="I can keep it on", warning="The wind may tug your bonnet loose", fix="Let's tie the ribbon snugly", tags={"wind", "bonnet"}),
    "rain": Problem("rain", risk=1, prevent=3, text="It is only a drizzle", warning="The drizzle can dampen the brim", fix="Let's tuck the bonnet inside until the rain passes", tags={"rain", "bonnet"}),
    "bench": Problem("bench", risk=0, prevent=1, text="I want to sit a minute", warning="The bench is fine", fix="We can sit and rest", tags={"slice_of_life"}),
}

CHILDREN = [("Mia", "girl"), ("Nora", "girl"), ("Eli", "boy"), ("Theo", "boy")]
PARENTS = [("Mom", "mother"), ("Dad", "father")]
TRAITS = ["careful", "curious", "cheerful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for bid, bonnet in BONNETS.items():
                if risk_at_hand(problem, bonnet):
                    combos.append((sid, pid, bid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    bonnet: str
    child: str
    child_type: str
    parent: str
    parent_type: str
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


KNOWLEDGE = {
    "bonnet": [("What is a bonnet?", "A bonnet is a hat that covers a child's head and often ties under the chin. It helps keep the sun off and can stay in place when tied well.")],
    "wind": [("Why can wind be tricky for hats?", "Wind can push and pull at loose things, so a hat or bonnet may slip off if it is not tied securely.")],
    "rain": [("Why is a bonnet not the best thing for rain?", "A bonnet can get damp and rumpled in rain, so a rain hat or hood may be better when the weather is wet.")],
    "garden": [("What do people do in a garden?", "People may water flowers, trim plants, or walk along the path and enjoy a quiet moment.")],
    "market": [("What is a market?", "A market is a place where people buy and sell food and other things, often from small stalls.")],
    "slice_of_life": [("What does slice of life mean?", "Slice of life means a story about ordinary, everyday moments that feel real and gentle.")],
    "call_adult": [("What should you do if something seems unsafe?", "Stop, stay calm, and call a grown-up right away. It is smart to ask for help before a small problem grows bigger.")],
}
KNOWLEDGE_ORDER = ["slice_of_life", "bonnet", "wind", "rain", "garden", "market", "call_adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, problem, bonnet, setting = f["child"], f["parent"], f["problem"], f["bonnet_cfg"], f["setting"]
    return [
        f'Write a gentle cautionary story for a young child that takes place at {setting.place} and includes the word "{bonnet.label}".',
        f"Tell a slice-of-life story where {child.id} wears {bonnet.phrase}, {parent.id} notices a small risk, and they fix it kindly.",
        f'Write a short story about an everyday outing where a bonnet and a little warning lead to a safer choice.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, bonnet, problem = f["child"], f["parent"], f["bonnet_cfg"], f["problem"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {parent.id}, during an ordinary outing that turns into a small bonnet worry."),
        ("What did {0} wear?".format(child.id), f"{child.id} wore {bonnet.phrase}. It made the day feel special and tidy at first."),
        ("Why did {0} warn {1}?".format(parent.id, child.id), f"{parent.id} warned {child.id} because {problem.warning.lower()}. The warning was about keeping the bonnet from slipping or getting messy."),
    ]
    if f.get("outcome") == "protected":
        qa.append((
            "What changed by the end?",
            f"The bonnet stayed secure because {parent.id} helped tie it snugly and {child.id} listened. The child kept the bonnet on without having to chase it."
        ))
    else:
        qa.append((
            "What happened after the small scare?",
            f"The bonnet slipped a little, but {parent.id} fixed it and the day went on safely. That made the outing feel calm again."
        ))
    qa.append((
        "How did the child feel at the end?",
        f"{child.id} felt relieved and proud. The bonnet was still part of the outfit, but now it was worn safely."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["problem"].tags) | set(f["bonnet_cfg"].tags)
    out = []
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "wind", "blue", "Mia", "girl", "Mom", "mother", "careful"),
    StoryParams("walk", "wind", "floral", "Nora", "girl", "Dad", "father", "patient"),
    StoryParams("market", "rain", "sun", "Eli", "boy", "Mom", "mother", "curious"),
    StoryParams("porch", "wind", "blue", "Theo", "boy", "Dad", "father", "cheerful"),
]


def explain_rejection(problem: Problem, bonnet: Bonnet) -> str:
    if not risk_at_hand(problem, bonnet):
        return "(No story: that bonnet problem does not create a real risk, so there is nothing honest to warn about.)"
    return "(No story: this combination is too weak for the cautionary turn.)"


def outcome_of(params: StoryParams) -> str:
    return "protected" if PROBLEMS[params.problem].prevent >= SAFE_MIN else "slipped"


ASP_RULES = r"""
risk(P, B) :- problem(P), bonnet(B), can_blown_off(B).
sensible(P) :- problem(P), prevent(P, N), safe_min(M), N >= M.
protected :- chosen_problem(P), chosen_bonnet(B), prevent(P, N), wind_risk(B), N >= 2.
outcome(protected) :- protected.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid, b in BONNETS.items():
        lines.append(asp.fact("bonnet", bid))
        if b.can_blow_off:
            lines.append(asp.fact("can_blown_off", bid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("prevent", pid, p.prevent))
    lines.append(asp.fact("safe_min", SAFE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    pset = set(valid_combos())
    aset = set(asp_valid_combos())
    if pset == aset:
        print(f"OK: gate matches valid_combos() ({len(pset)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in python:", sorted(pset - aset))
        print("  only in asp:", sorted(aset - pset))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, bonnet=None, child=None, child_type=None, parent=None, parent_type=None, trait=None), random.Random(777)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a bonnet, a small warning, and a safe slice-of-life ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--bonnet", choices=BONNETS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.bonnet is None or c[2] == args.bonnet)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, bonnet = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    child = args.child or rng.choice([n for n, t in CHILDREN if t == child_type])
    parent = args.parent or rng.choice([n for n, t in PARENTS if t == parent_type])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, problem, bonnet, child, child_type, parent, parent_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BONNETS[params.bonnet], PROBLEMS[params.problem],
                 params.child, params.child_type, params.parent, params.parent_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
