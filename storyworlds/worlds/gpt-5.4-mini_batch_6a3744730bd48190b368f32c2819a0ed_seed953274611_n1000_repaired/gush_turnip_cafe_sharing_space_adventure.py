#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gush_turnip_cafe_sharing_space_adventure.py
===========================================================================

A small standalone storyworld for a Space Adventure flavored sharing tale:
children aboard a little star-cafe discover a turnip-powered drink gush,
and learn to share it so everyone gets a turn.

This world is built around a simple causal model:
- a cafe runs out of a special ship-grown turnip treat,
- a sudden gush spills or bursts the shared serving station,
- the crew must decide whether to hoard or share,
- a helper repairs the station and the story ends with everyone sharing
  something warm, safe, and spacey.

The required seed words are present in the world model and may appear in prose:
gush, turnip, cafe.
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
SHARING_MIN = 2
CAREFUL_MIN = 2


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
    shareable: bool = False
    fixable: bool = False
    tasty: bool = False
    special: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    mood: str
    detail: str
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


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    share_phrase: str
    spill_phrase: str
    tasty: bool = True
    shareable: bool = True
    special: bool = False
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    risk: int
    fix_phrase: str
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


@dataclass
class Fix:
    id: str
    label: str
    power: int
    text: str
    success_text: str
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
            raise StoryError(f"missing world entity: {eid}")
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


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared"):
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["joy"] += 0.5
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("fixed"):
        if "station" in world.entities:
            world.get("station").meters["drip"] = 0.0
    return out


CAUSAL_RULES = [Rule("share", _r_share), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reason_ok(problem: Problem, treat: Treat, fix: Fix) -> bool:
    return problem.risk >= SHARING_MIN and treat.shareable and fix.power >= problem.risk


def apply_gush(world: World, treat: Treat, problem: Problem) -> None:
    station = world.get("station")
    station.meters["drip"] += 1
    station.meters["mess"] += 1
    world.facts["gushed"] = True
    world.say(
        f"Then a sudden gush splashed from the serving tube, silver and sweet, "
        f"and the little cafe went quiet."
    )
    if problem.cause == "broken_siphon":
        world.say(
            f"It all happened because the siphon had a crack, so the stream of "
            f"{treat.label} rushed everywhere at once."
        )


def setup_scene(world: World, kids: tuple[Entity, Entity], setting: Setting) -> None:
    a, b = kids
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"Out past the moon-rim, {a.id} and {b.id} floated into the {setting.place}, "
        f"a tiny cafe with a round window and a {setting.sky} sky outside."
    )
    world.say(
        f"{setting.detail} {a.id} pointed at the counter while {b.id} peered at the "
        f"shining cups."
    )


def introduce_treat(world: World, treat: Treat) -> None:
    world.say(
        f"The cook showed them a {treat.phrase}, made from a brave little turnip "
        f"grown in a station garden."
    )


def want_share(world: World, a: Entity, b: Entity, treat: Treat) -> None:
    a.memes["want"] += 1
    b.memes["want"] += 1
    world.say(
        f'"Can we have some?" {a.id} asked. "{treat.label} smells amazing," '
        f"{b.id} said, and both children leaned closer."
    )


def warn(world: World, helper: Entity, treat: Treat, problem: Problem) -> None:
    helper.memes["careful"] += 1
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. '
        f'"If we grab it the wrong way, the {problem.label} will make a mess. '
        f"We should share it one bowl at a time."'
    )


def choose_share(world: World, a: Entity, b: Entity, treat: Treat) -> None:
    a.memes["sharing"] += 1
    b.memes["sharing"] += 1
    world.facts["shared"] = True
    world.say(
        f"The two children looked at each other, then nodded. "
        f'"We can share," {a.id} said. "{treat.label} tastes better when everyone gets some."'
    )


def take_treat(world: World, a: Entity, b: Entity, treat: Treat) -> None:
    world.say(
        f"So they took turns with little spoons, and the warm {treat.label} "
        f"glowed orange in the cafe lights."
    )


def repair(world: World, helper: Entity, fix: Fix, problem: Problem, treat: Treat) -> None:
    world.facts["fixed"] = True
    station = world.get("station")
    station.meters["drip"] = 0.0
    world.say(
        f"{helper.id} hurried over with {fix.label}. {helper.pronoun().capitalize()} "
        f"{fix.text}."
    )
    world.say(
        f"The {problem.label} stopped at once, and the last of the turnip juice "
        f"settled back into the bowl."
    )


def ending(world: World, a: Entity, b: Entity, treat: Treat, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In the end, the {setting.id} cafe smelled cozy and sweet. "
        f"{a.id} and {b.id} shared the last spoonful, and the little spaceship booth "
        f"shone like a warm orange star."
    )


def tell(setting: Setting, treat: Treat, problem: Problem, fix: Fix,
         kid1: str = "Nova", kid1_gender: str = "girl",
         kid2: str = "Pip", kid2_gender: str = "boy",
         helper_name: str = "Mira", helper_gender: str = "girl") -> World:
    if not reason_ok(problem, treat, fix):
        raise StoryError("this combination is too weak or not shareable enough for a story")

    world = World()
    a = world.add(Entity(id=kid1, kind="character", type=kid1_gender, role="visitor"))
    b = world.add(Entity(id=kid2, kind="character", type=kid2_gender, role="visitor"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="station", type="thing", label="serving station"))
    world.add(Entity(id="turnip", type="thing", label="turnip", shareable=True, tasty=True, special=True))

    setup_scene(world, (a, b), setting)
    world.para()
    introduce_treat(world, treat)
    want_share(world, a, b, treat)
    warn(world, helper, treat, problem)
    choose_share(world, a, b, treat)
    apply_gush(world, treat, problem)
    world.para()
    take_treat(world, a, b, treat)
    repair(world, helper, fix, problem, treat)
    ending(world, a, b, treat, setting)

    world.facts.update(
        setting=setting,
        treat=treat,
        problem=problem,
        fix=fix,
        helper=helper,
        kids=(a, b),
        shared=True,
        fixed=True,
        gushed=True,
    )
    return world


SETTINGS = {
    "orbit_cafe": Setting(
        id="orbit_cafe",
        place="orbit cafe",
        sky="starry",
        mood="cozy",
        detail="A silver table floated by the window, and a tiny menu blinked green.",
        tags={"space", "cafe"},
    ),
    "lunar_cafe": Setting(
        id="lunar_cafe",
        place="lunar cafe",
        sky="moonlit",
        mood="bright",
        detail="A ring of cushions kept cups from drifting away.",
        tags={"space", "cafe"},
    ),
    "comet_cafe": Setting(
        id="comet_cafe",
        place="comet cafe",
        sky="sparkling",
        mood="cheerful",
        detail="The floor hummed softly like a sleepy engine.",
        tags={"space", "cafe"},
    ),
}

TREATS = {
    "turnip_soup": Treat(
        id="turnip_soup",
        label="turnip soup",
        phrase="a steaming turnip soup",
        share_phrase="share the turnip soup",
        spill_phrase="gush out of the bowl",
        tags={"turnip"},
    ),
    "turnip_juice": Treat(
        id="turnip_juice",
        label="turnip juice",
        phrase="a cold turnip juice",
        share_phrase="share the turnip juice",
        spill_phrase="gush from the pipe",
        tags={"turnip", "gush"},
    ),
    "turnip_pie": Treat(
        id="turnip_pie",
        label="turnip pie",
        phrase="a warm turnip pie",
        share_phrase="share the turnip pie",
        spill_phrase="gush onto the tray",
        tags={"turnip"},
    ),
}

PROBLEMS = {
    "broken_siphon": Problem(
        id="broken_siphon",
        label="broken siphon",
        cause="broken_siphon",
        risk=2,
        fix_phrase="tighten the clamp",
        tags={"gush"},
    ),
    "loose_valve": Problem(
        id="loose_valve",
        label="loose valve",
        cause="loose_valve",
        risk=2,
        fix_phrase="close the valve",
        tags={"gush"},
    ),
}

FIXES = {
    "clamp": Fix(
        id="clamp",
        label="a silver clamp",
        power=2,
        text="tightened the clamp until the dripping stopped",
        success_text="tightened the clamp and stopped the drip",
        tags={"repair"},
    ),
    "valve": Fix(
        id="valve",
        label="a small valve wheel",
        power=3,
        text="turned the valve wheel until not a drop escaped",
        success_text="turned the valve wheel and stopped the gush",
        tags={"repair"},
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Tia", "Zuri", "Rae"]
BOY_NAMES = ["Pip", "Orin", "Jett", "Milo", "Kai", "Beck"]
HELPER_NAMES = ["Mira", "Zuri", "Orin", "Kai"]
TRAITS = ["careful", "curious", "brave", "kind", "patient"]


@dataclass
class StoryParams:
    setting: str
    treat: str
    problem: str
    fix: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    helper: str
    helper_gender: str
    trait: str = "kind"
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


CURATED = [
    StoryParams(
        setting="orbit_cafe",
        treat="turnip_juice",
        problem="broken_siphon",
        fix="valve",
        kid1="Nova",
        kid1_gender="girl",
        kid2="Pip",
        kid2_gender="boy",
        helper="Mira",
        helper_gender="girl",
        trait="careful",
    ),
    StoryParams(
        setting="lunar_cafe",
        treat="turnip_soup",
        problem="loose_valve",
        fix="clamp",
        kid1="Luna",
        kid1_gender="girl",
        kid2="Kai",
        kid2_gender="boy",
        helper="Orin",
        helper_gender="boy",
        trait="kind",
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, treat in TREATS.items():
            for pid, problem in PROBLEMS.items():
                for fid, fix in FIXES.items():
                    if treat.shareable and fix.power >= problem.risk:
                        combos.append((sid, tid, pid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure sharing storyworld with a turnip cafe.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--kid1")
    ap.add_argument("--kid1-gender", choices=["girl", "boy"])
    ap.add_argument("--kid2")
    ap.add_argument("--kid2-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.treat is None or c[1] == args.treat)
        and (args.problem is None or c[2] == args.problem)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("no valid space-cafe sharing story matches those choices")
    setting, treat, problem, fix = rng.choice(sorted(combos))
    t = TREATS[treat]
    p = PROBLEMS[problem]
    f = FIXES[fix]
    kid1_gender = args.kid1_gender or rng.choice(["girl", "boy"])
    kid2_gender = args.kid2_gender or ("boy" if kid1_gender == "girl" else "girl")
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    kid1 = args.kid1 or rng.choice(GIRL_NAMES if kid1_gender == "girl" else BOY_NAMES)
    kid2_pool = [n for n in (GIRL_NAMES if kid2_gender == "girl" else BOY_NAMES) if n != kid1]
    kid2 = args.kid2 or rng.choice(kid2_pool)
    helper_pool = [n for n in HELPER_NAMES if n not in {kid1, kid2}]
    helper = args.helper or rng.choice(helper_pool)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        treat=treat,
        problem=problem,
        fix=fix,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        helper=helper,
        helper_gender=helper_gender,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    treat: Treat = f["treat"]
    return [
        f'Write a Space Adventure story for a child in the {setting.place} that includes the words "gush", "turnip", and "cafe".',
        f"Tell a story where two kids in a {setting.place} learn to share {treat.label} after a sudden gush.",
        f"Write a gentle space-cafe story about sharing a turnip treat and fixing a small problem together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["kids"]
    setting: Setting = f["setting"]
    treat: Treat = f["treat"]
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    helper: Entity = f["helper"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {a.id}, {b.id}, and {helper.id} in the {setting.place}. They are the small crew who turn a cafe problem into a sharing adventure.",
        ),
        (
            "What did the children want?",
            f"They wanted to taste {treat.phrase} and enjoy the little cafe together. They were excited because the treat was made from a turnip grown on the ship.",
        ),
        (
            "What happened when the problem started?",
            f"A {problem.label} caused a sudden gush, so the serving station began to drip and make a mess. That made the children stop and choose a careful plan.",
        ),
        (
            "How did they solve it?",
            f"They shared the treat one bowl at a time while {helper.id} used {fix.label} to stop the drip. The fix kept the cafe neat and let everyone get a turn.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "turnip": [(
        "What is a turnip?",
        "A turnip is a round root vegetable that grows under the ground. People can cook it in soups, pies, and other foods.",
    )],
    "gush": [(
        "What does gush mean?",
        "If something gushes, it comes out quickly in a strong flow. A gush can make a big splash or a big mess.",
    )],
    "cafe": [(
        "What is a cafe?",
        "A cafe is a small place where people sit and get food or drinks. In a story, it can be a cozy place to meet and share.",
    )],
    "sharing": [(
        "Why is sharing nice?",
        "Sharing means letting other people have some too. It helps everyone feel included and can make play or snack time more friendly.",
    )],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for tag in ["turnip", "gush", "cafe", "sharing"]:
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
shared :- wants_share, treat_shareable.
fixed :- fix_power(P), risk(R), P >= R.
outcome(shared, fixed).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.shareable:
            lines.append(asp.fact("treat_shareable", tid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("risk", pid, p.risk))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_power", fid, f.power))
    lines.append(asp.fact("wants_share"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/2."))
    return sorted(set(asp.atoms(model, "outcome")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) != set((a, b, c, d) for a, b, c, d in valid_combos()):
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"story generation failed: {e}")
        return 1
    print("OK: normal generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        treat = TREATS[params.treat]
        problem = PROBLEMS[params.problem]
        fix = FIXES[params.fix]
    except KeyError as exc:
        raise StoryError(f"invalid parameter: {exc.args[0]}") from exc
    world = tell(
        setting=setting,
        treat=treat,
        problem=problem,
        fix=fix,
        kid1=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2=params.kid2,
        kid2_gender=params.kid2_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
    )
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
        print(asp_program("", "#show outcome/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available.")
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
            header = f"### {p.setting} / {p.treat} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
