#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/plan_care_repetition_fable.py
=============================================================

A small fable-like storyworld about a careful plan, repeated acts of care, and a
simple lesson learned by animals in a quiet garden.

The seed words are "plan" and "care".  The story pattern leans fable-like:
someone makes a plan, care is repeated, a problem grows, and a wiser ending
proves what changed.

This file is standalone and uses only the standard library plus the shared
result containers and lazy ASP helper from storyworlds/.
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
CARE_MIN = 2
PLAN_MIN = 1


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox"}
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
    detail: str
    shelter: str
    help_spot: str
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
class Concern:
    id: str
    label: str
    reason: str
    spreads: bool = True
    can_hold: bool = True
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
class Plan:
    id: str
    wording: str
    repeats: str
    safer: str
    lesson: str
    gain: int
    care_need: int
    problem: str
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
class Remedy:
    id: str
    wording: str
    action: str
    effect: str
    power: int
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
class StoryParams:
    setting: str
    concern: str
    plan: str
    remedy: str
    doer: str
    doer_type: str
    helper: str
    helper_type: str
    elder: str
    elder_type: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["helped"] < THRESHOLD:
            continue
        sig = ("repeat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] += 1
        out.append("__repeat__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["trouble"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def plan_at_risk(plan: Plan, concern: Concern) -> bool:
    return concern.spreads and plan.care_need >= CARE_MIN


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.power >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, c in CONCERNS.items():
            for pid, p in PLANS.items():
                if plan_at_risk(p, c):
                    combos.append((sid, cid, pid))
    return combos


def tell(world: World, setting: Setting, concern: Concern, plan: Plan, remedy: Remedy,
         doer: Entity, helper: Entity, elder: Entity) -> None:
    doer.memes["hope"] += 1
    helper.memes["care"] += 1
    elder.memes["care"] += 1
    world.say(
        f"In {setting.place}, {doer.id} and {helper.id} lived by a small fable: "
        f"{setting.detail}"
    )
    world.say(
        f"{doer.id} made a plan. {plan.wording} {plan.repeats}."
    )
    world.say(
        f"{helper.id} listened with care and said, '{plan.safer}'"
    )
    world.para()
    world.say(
        f"But the trouble was {concern.label}: {concern.reason}."
    )
    world.say(
        f"So {doer.id} tried to help at once, and then care had to be repeated."
    )

    for _ in range(2):
        doer.meters["helped"] += 1
        helper.meters["helped"] += 1
    propagate(world, narrate=False)

    if concern.spreads and plan.care_need >= CARE_MIN:
        world.say(
            f"{elder.id} came with a wiser plan. {remedy.wording}."
        )
        if remedy.power >= plan.care_need:
            world.say(
                f"{remedy.action.capitalize()} {remedy.effect}, and the trouble grew small."
            )
            doer.memes["lesson"] += 1
            helper.memes["lesson"] += 1
            elder.memes["lesson"] += 1
            world.para()
            world.say(
                f"By sunset, they were careful twice over: they had their plan, "
                f"they had their care, and they remembered both."
            )
            world.say(
                f"The little garden was calm again, and even the stones seemed to rest."
            )
            outcome = "wise"
        else:
            world.say(
                f"{remedy.action.capitalize()} did not quite stop it, so they called for more care."
            )
            outcome = "too_weak"
    else:
        world.say(
            f"Nothing grew worse, and the plan stayed gentle because care stayed near."
        )
        world.para()
        world.say(
            f"At the end, they kept the same plan, but they kept a closer care."
        )
        outcome = "soft"

    world.facts.update(
        setting=setting,
        concern=concern,
        plan=plan,
        remedy=remedy,
        doer=doer,
        helper=helper,
        elder=elder,
        outcome=outcome,
    )


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        detail="the beans needed water, the path needed sweeping, and the herbs leaned toward the sun",
        shelter="the little shed",
        help_spot="the watering can",
    ),
    "yard": Setting(
        id="yard",
        place="the yard",
        detail="the apple tree dropped leaves, the fence was askew, and the kittens liked the warm stones",
        shelter="the porch",
        help_spot="the broom",
    ),
}

CONCERNS = {
    "thirst": Concern(
        id="thirst",
        label="thirst",
        reason="the beans were drooping and the soil was dry",
        spreads=True,
        can_hold=True,
    ),
    "mess": Concern(
        id="mess",
        label="a mess",
        reason="the path was cluttered with leaves and twigs",
        spreads=True,
        can_hold=True,
    ),
}

PLANS = {
    "water": Plan(
        id="water",
        wording="They would bring water in a small can and water the beans row by row",
        repeats="Then they would do it again and again, because care is strongest when it is repeated",
        safer="We can begin at the front and return for the back, so nothing is missed",
        lesson="care grows when it is steady",
        gain=2,
        care_need=2,
        problem="dry soil",
        tags={"water", "care", "plan"},
    ),
    "sweep": Plan(
        id="sweep",
        wording="They would sweep the path in short, careful strokes",
        repeats="Then they would sweep once more, because one kind act can be made better by another",
        safer="We can start near the stones and keep going until the path is clear",
        lesson="a tidy path comes from patient care",
        gain=2,
        care_need=2,
        problem="fallen leaves",
        tags={"sweep", "care", "plan"},
    ),
}

REMEDIES = {
    "bucket": Remedy(
        id="bucket",
        wording="Their elder brought a bucket and asked them to take turns",
        action="One bucket at a time",
        effect="filled the dry places and kept the beans from drooping",
        power=3,
        tags={"water", "care"},
    ),
    "broom": Remedy(
        id="broom",
        wording="Their elder brought a broom and showed them how to make one clean line after another",
        action="One slow sweep after another",
        effect="cleared the leaves and made the path bright again",
        power=3,
        tags={"sweep", "care"},
    ),
}

NAMES = ["Pip", "Nia", "Tess", "Milo", "Jin", "Luna", "Rowan", "Bea"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about plan, care, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--concern", choices=CONCERNS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--doer")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    if args.remedy and args.plan:
        remedy = REMEDIES[args.remedy]
        plan = PLANS[args.plan]
        if remedy.power < plan.care_need:
            raise StoryError("That remedy is too weak for the plan's trouble.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.concern is None or c[1] == args.concern)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, concern, plan = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    doer = args.doer or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != doer])
    elder = args.elder or rng.choice([n for n in NAMES if n not in {doer, helper}])
    doer_type = rng.choice(["fox", "hen", "rabbit"])
    helper_type = rng.choice(["fox", "hen", "rabbit"])
    elder_type = "owl"
    return StoryParams(
        setting=setting, concern=concern, plan=plan, remedy=remedy,
        doer=doer, doer_type=doer_type, helper=helper, helper_type=helper_type,
        elder=elder, elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.concern not in CONCERNS:
        raise StoryError("Unknown concern.")
    if params.plan not in PLANS:
        raise StoryError("Unknown plan.")
    if params.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    world = World()
    setting = SETTINGS[params.setting]
    concern = CONCERNS[params.concern]
    plan = PLANS[params.plan]
    remedy = REMEDIES[params.remedy]
    doer = world.add(Entity(id=params.doer, kind="character", type=params.doer_type, role="doer"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_type, role="elder"))
    tell(world, setting, concern, plan, remedy, doer, helper, elder)
    prompts = [
        f"Write a fable with the words plan and care in which {params.doer} makes a plan and {params.helper} answers with care.",
        f"Tell a short animal fable about repeated care, a wiser elder, and a simple plan in {setting.place}.",
        f"Write a gentle story where care is repeated until the trouble is solved, and the ending teaches a lesson.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.doer} make?",
            answer=f"{params.doer} made a plan, and the story keeps returning to that plan because care had to be repeated."
        ),
        QAItem(
            question=f"How did {params.helper} help?",
            answer=f"{params.helper} listened with care and kept helping. That repeated care made the plan work in the end."
        ),
        QAItem(
            question=f"What changed by the end?",
            answer="The trouble became small, and the little place grew calm again. The story ends by showing that steady care can turn a plan into a wise result."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is care?",
            answer="Care is kind attention that helps keep something safe, clean, or well. In this world, care is repeated so it can do its work."
        ),
        QAItem(
            question="Why do fables repeat ideas?",
            answer="Fables often repeat a simple idea so the lesson is easy to remember. Repetition also makes the change feel steady and clear."
        ),
        QAItem(
            question="What makes a plan good in this world?",
            answer="A plan is good when it is simple, careful, and repeated in the right way. The best plan fits the trouble and grows better with care."
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        concern="thirst",
        plan="water",
        remedy="bucket",
        doer="Pip",
        doer_type="fox",
        helper="Nia",
        helper_type="hen",
        elder="Owl",
        elder_type="owl",
    ),
    StoryParams(
        setting="yard",
        concern="mess",
        plan="sweep",
        remedy="broom",
        doer="Luna",
        doer_type="rabbit",
        helper="Milo",
        helper_type="fox",
        elder="Bea",
        elder_type="owl",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "wise" if REMEDIES[params.remedy].power >= PLANS[params.plan].care_need else "too_weak"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CONCERNS.items():
        lines.append(asp.fact("concern", cid))
        if c.spreads:
            lines.append(asp.fact("spreads", cid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("care_need", pid, p.care_need))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,P) :- setting(S), concern(C), plan(P), spreads(C), care_need(P,N), N >= 2.
wise(P,R) :- plan(P), remedy(R), care_need(P,N), power(R,X), X >= N.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python disagree.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection(plan: Plan, concern: Concern) -> str:
    return f"(No story: {plan.id} does not fit {concern.label} well enough for a fable-like turn.)"


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show wise/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = build_story_params_from_args(args, random.Random(seed))
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
            header = f"### {p.doer} and {p.helper}: {p.plan} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
