#!/usr/bin/env python3
"""
Standalone storyworld: a small deli suspense-sharing rhyming story.

A child visits a deli with a snack, notices something pesky, feels a little
suspense, and learns to share in a kind, rhyming ending.
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    scent: str
    afford: set[str] = field(default_factory=set)
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
class Snack:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    crumbs: bool = False
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
class PeskyThing:
    id: str
    label: str
    phrase: str
    sneaky: str
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
class SharePlan:
    id: str
    kind: str
    line: str
    reward: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["worry"] >= THRESHOLD and ("suspense", e.id) not in world.fired:
            world.fired.add(("suspense", e.id))
            out.append("__suspense__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    pesky = world.entities.get("pesky")
    snack = world.entities.get("snack")
    if not kid or not pesky or not snack:
        return out
    if kid.memes["share"] >= THRESHOLD and snack.meters["shared"] < THRESHOLD:
        sig = ("share", snack.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        snack.meters["shared"] += 1
        kid.memes["calm"] += 1
        pesky.memes["happy"] += 1
        out.append("__share__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("share", _r_share)]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    for s in out:
        world.say(s)
    return out


def rhyme(a: str, b: str) -> str:
    return f"{a}, {b}"


def predict_share(world: World) -> dict:
    sim = world.copy()
    sim.get("kid").memes["worry"] += 1
    sim.get("kid").memes["share"] += 1
    propagate(sim)
    return {"shared": sim.get("snack").meters["shared"] >= THRESHOLD}


def tell(setting: Setting, snack: Snack, pesky: PeskyThing, plan: SharePlan,
         kid_name: str, kid_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    kid = world.add(Entity(id="kid", kind="character", type=kid_gender, label=kid_name, role="kid"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    pest = world.add(Entity(id="pesky", kind="character", type="thing", label=pesky.label, role="pesky"))
    item = world.add(Entity(id="snack", kind="thing", type="thing", label=snack.label, role="snack"))
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{kid_name} went to the deli, where warm smells swirled like a song.")
    world.say(f"{helper_name} came too, and the counter was bright with {snack.phrase}.")
    world.say(f"But {pesky.label} was there, all sneaky and sly, a pesky little shadow by.")
    world.para()
    world.say(f"{kid_name} held {snack.label}, then froze in a hush; the deli felt still, with a curious rush.")
    world.say(f'{helper_name} whispered, "{plan.line}"')
    kid.memes["worry"] += 1
    if not predict_share(world)["shared"]:
        raise StoryError("sharing plan failed the reasonableness gate")
    world.say(f"{kid_name} looked once more, then smiled so wide, and chose to share the treat inside.")
    kid.memes["share"] += 1
    propagate(world)
    world.para()
    world.say(f"{kid_name} broke the snack in two, so {helper_name} and {pesky.label} could nibble too.")
    world.say(f"The pesky wait was over at last; the deli grew gentle, and the worry passed.")
    world.say(f"{plan.reward.capitalize()} was the tune, and the ending did chime: share a little, and all feel fine.")
    world.facts.update(
        kid=kid, helper=helper, pesky=pesky, snack=item, setting=setting, plan=plan,
        shared=item.meters["shared"] >= THRESHOLD
    )
    return world


SETTINGS = {
    "corner_deli": Setting(id="corner_deli", place="a corner deli", scent="fresh bread", afford={"sharing"}),
    "busy_deli": Setting(id="busy_deli", place="a busy deli", scent="pickles and soup", afford={"sharing"}),
}

SNACKS = {
    "bagel": Snack(id="bagel", label="bagel", phrase="a warm sesame bagel", shareable=True, crumbs=True, tags={"food", "share"}),
    "sandwich": Snack(id="sandwich", label="sandwich", phrase="a stacked deli sandwich", shareable=True, crumbs=True, tags={"food", "share"}),
}

PESKIES = {
    "mouse": PeskyThing(id="mouse", label="mouse", phrase="a tiny mouse", sneaky="scurried", tags={"pesky"}),
    "sparrow": PeskyThing(id="sparrow", label="sparrow", phrase="a little sparrow", sneaky="fluttered", tags={"pesky"}),
}

PLANS = {
    "kind_share": SharePlan(id="kind_share", kind="sharing", line="Let's share a bite, and be sweet and polite.", reward="kindness can shine", tags={"sharing"}),
    "calm_share": SharePlan(id="calm_share", kind="sharing", line="Let's split it in two, and one will be for you.", reward="sharing feels bright", tags={"sharing"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Max", "Sam"]
HELPER_NAMES = ["Pip", "Mina", "Jo", "Rue", "Kai"]


@dataclass
class StoryParams:
    setting: str
    snack: str
    pesky: str
    plan: str
    kid_name: str
    kid_gender: str
    helper_name: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for snack_id in SNACKS:
            for pesky_id in PESKIES:
                for plan_id in PLANS:
                    if "sharing" in s.afford and SNACKS[snack_id].shareable:
                        combos.append((sid, snack_id, pesky_id, plan_id))
    return combos


def explain_rejection() -> str:
    return "(No story: this deli scene needs a shareable snack and a sharing plan.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: deli suspense and sharing in rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--pesky", choices=PESKIES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.pesky is None or c[2] == args.pesky)
              and (args.plan is None or c[3] == args.plan)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, snack, pesky, plan = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    kid_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = rng.choice(["girl", "boy"])
    helper_name = rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, snack=snack, pesky=pesky, plan=plan,
                       kid_name=kid_name, kid_gender=gender,
                       helper_name=helper_name, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child set in {f["setting"].place} with the words "pesky" and "deli".',
        f"Tell a suspenseful, gentle rhyming story where {f['kid'].label} learns to share food in the deli.",
        f"Write a short rhyme about a pesky little visitor, a deli snack, and a kind sharing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, helper, pesky, snack = f["kid"], f["helper"], f["pesky"], f["snack"]
    return [
        QAItem(question="Where did the story happen?",
               answer=f"It happened in {f['setting'].place}, where the air smelled like {f['setting'].scent}."),
        QAItem(question="What made the moment suspenseful?",
               answer=f"The pesky {pesky.label} made everyone pause and wonder what would happen next. That little pause gave the deli scene a gentle suspense."),
        QAItem(question="How was the problem solved?",
               answer=f"{kid.label} shared the {snack.label} with help from {helper.label}. Sharing turned the tense moment into a happy ending."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a deli?",
               answer="A deli is a shop that sells ready-to-eat food like sandwiches, bagels, and soup."),
        QAItem(question="What does pesky mean?",
               answer="Pesky means annoying in a small, playful way. A pesky thing can be hard to ignore."),
        QAItem(question="Why is sharing a kind choice?",
               answer="Sharing helps more than one person enjoy something. It shows care and makes a moment feel fair."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.snack not in SNACKS or params.pesky not in PESKIES or params.plan not in PLANS:
        raise StoryError("invalid story parameters")
    world = tell(SETTINGS[params.setting], SNACKS[params.snack], PESKIES[params.pesky], PLANS[params.plan],
                 params.kid_name, params.kid_gender, params.helper_name, params.helper_gender)
    return StorySample(params=params, story=world.render(),
                       prompts=generation_prompts(world),
                       story_qa=story_qa(world),
                       world_qa=world_knowledge_qa(world),
                       world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="corner_deli", snack="bagel", pesky="mouse", plan="kind_share",
                kid_name="Mia", kid_gender="girl", helper_name="Pip", helper_gender="boy"),
    StoryParams(setting="busy_deli", snack="sandwich", pesky="sparrow", plan="calm_share",
                kid_name="Theo", kid_gender="boy", helper_name="Mina", helper_gender="girl"),
]


ASP_RULES = r"""
valid(SN, PK, PL) :- setting(S), snack(SN), pesky(PK), plan(PL), shareable(SN), afford(S, sharing).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("afford", sid, "sharing"))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("shareable", sid))
    for pid in PESKIES:
        lines.append(asp.fact("pesky", pid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _r
    rc = 0
    if set(asp_valid_combos()) == set((a, b, c) for a, b, c, _ in valid_combos()):
        print("OK: ASP gate matches Python gate.")
    else:
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, snack=None, pesky=None, plan=None), _r.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations")
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
