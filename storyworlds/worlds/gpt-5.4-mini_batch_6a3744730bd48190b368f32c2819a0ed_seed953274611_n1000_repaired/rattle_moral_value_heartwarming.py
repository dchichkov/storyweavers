#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rattle_moral_value_heartwarming.py
===================================================================

A small heartwarming storyworld about a child, a treasured rattle, a worried
grown-up, and a moral-value choice: tell the truth, make amends, and share
kindness. The model is intentionally tiny and state-driven. The world keeps
physical meters and emotional memes, the prose follows simulation, and the
ending proves what changed.

The core premise is simple:
- a child wants to keep a shiny rattle
- a mistake happens
- someone is honest
- kindness repairs the moment
- the rattle becomes part of a warm, shared ending

This file is self-contained and uses only stdlib plus the shared result
containers and optional ASP helper.
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
    tags: set[str] = field(default_factory=set)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    shine: str
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
class Mishap:
    id: str
    label: str
    verb: str
    mess: str
    hurt: str
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
class Repair:
    id: str
    label: str
    text: str
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


@dataclass
class StoryParams:
    gift: str
    mishap: str
    repair: str
    child: str
    child_gender: str
    grownup: str
    grownup_gender: str
    setting: str
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


def _r_sad(world: World) -> list[str]:
    out = []
    if world.get("gift").meters["missing"] >= THRESHOLD and ("sad", "child") not in world.fired:
        world.fired.add(("sad", "child"))
        world.get("child").memes["worry"] += 1
        out.append("")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.get("gift").meters["found"] >= THRESHOLD and ("relief", "child") not in world.fired:
        world.fired.add(("relief", "child"))
        world.get("child").memes["relief"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("sad", _r_sad), Rule("relief", _r_relief)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def setting_line(setting: str) -> str:
    return {
        "nursery": "the nursery was warm and bright, with a little rug and a toy shelf.",
        "kitchen": "the kitchen smelled like warm toast, and sunlight lay on the table.",
        "bedroom": "the bedroom was small and cozy, with a blanket nest by the bed.",
    }[setting]


def predict_mishap(world: World, gift: Gift, mishap: Mishap) -> bool:
    sim = world.copy()
    sim.get("gift").meters["missing"] += 1
    sim.get("child").meters["mess"] += 1
    return True


def do_mishap(world: World, child: Entity, gift: Entity, mishap: Mishap) -> None:
    gift.meters["missing"] += 1
    child.meters["mess"] += 1
    child.memes["shame"] += 1
    propagate(world)


def make_amends(world: World, child: Entity, grownup: Entity, gift: Entity, repair: Repair) -> None:
    child.memes["honesty"] += 1
    child.memes["love"] += 1
    grownup.memes["gentleness"] += 1
    gift.meters["found"] += 1
    gift.meters["missing"] = 0
    world.say(f'{grownup.id} came closer, and {repair.text}.')
    world.say("The room felt softer at once, like a blanket had been laid over the worry.")


def tell(world: World, child_name: str, child_gender: str, grownup_name: str, grownup_gender: str,
         setting: str, gift: Gift, mishap: Mishap, repair: Repair) -> World:
    world.add(Entity(id="child", kind="character", type=child_gender, role="child", label=child_name))
    world.add(Entity(id="grownup", kind="character", type=grownup_gender, role="grownup", label=grownup_name))
    gift_ent = world.add(Entity(id="gift", kind="thing", type="toy", label=gift.label, tags=set(gift.tags)))
    child = world.get("child")
    grownup = world.get("grownup")

    child.memes["desire"] += 1
    child.memes["love"] += 1
    world.say(f"On a cozy afternoon, {child.id} found {gift.phrase} in {setting}.")
    world.say(f'{child.id} shook it, and it made a little rattle that sounded like a tiny rain of pebbles.')
    world.say(setting_line(setting))
    world.para()
    world.say(f'{child.id} wanted to keep the {gift.label} all to {child.pronoun("possessive")}self, but the shiny thing looked easy to drop.')
    world.say(f'Then the mishap happened: {child.id} {mishap.verb} {gift.label}, and it was gone from sight.')
    do_mishap(world, child, gift_ent, mishap)
    world.para()
    world.say(f'{child.id} got very quiet. Then {child.id} told {grownup.id} the truth right away.')
    make_amends(world, child, grownup, gift_ent, repair)
    world.para()
    world.say(f'{grownup.id} smiled and said, "Thank you for being honest. That was the brave thing to do."')
    world.say(f'Together they found the {gift.label} again and put it in a safe little bowl by the lamp.')
    world.say(f'At the end, {child.id} held the rattle carefully and smiled because the worry had turned into trust.')
    world.facts.update(
        child=child, grownup=grownup, gift=gift, mishap=mishap, repair=repair,
        setting=setting, outcome="repaired"
    )
    return world


GIFTS = {
    "rattle": Gift(id="rattle", label="rattle", phrase="a bright red rattle", shine="glinted like candy", tags={"rattle", "toy"}),
    "bell": Gift(id="bell", label="bell", phrase="a tiny silver bell", shine="glowed like a moon", tags={"bell", "toy"}),
    "maraca": Gift(id="maraca", label="maraca", phrase="a painted maraca", shine="looked cheerful and bright", tags={"maraca", "toy"}),
}

MISHAPS = {
    "drop": Mishap(id="drop", label="drop", verb="dropped", mess="lost", hurt="felt awful", tags={"drop"}),
    "hide": Mishap(id="hide", label="hide", verb="hid", mess="missing", hurt="felt worried", tags={"hide"}),
    "spill": Mishap(id="spill", label="spill", verb="spilled", mess="far away", hurt="felt bad", tags={"spill"}),
}

REPAIRS = {
    "tell_truth": Repair(id="tell_truth", label="tell the truth", text="they looked under the chair together and found it because the child had been honest", qa_text="found it together after the child told the truth", tags={"truth", "kindness"}),
    "apology": Repair(id="apology", label="apologize", text="they said sorry, looked carefully, and found it tucked beside the pillow", qa_text="said sorry and found it tucked beside the pillow", tags={"sorry", "kindness"}),
    "share": Repair(id="share", label="share kindly", text="they agreed to share it with a turn for each of them, and the sadness melted away", qa_text="shared it kindly and let the sadness melt away", tags={"share", "kindness"}),
}

SETTINGS = {
    "nursery": "the nursery",
    "kitchen": "the kitchen",
    "bedroom": "the bedroom",
}

NAMES = {
    "girl": ["Maya", "Luna", "Ivy", "Nina", "Ella"],
    "boy": ["Noah", "Eli", "Milo", "Theo", "Finn"],
}

CURATED = [
    StoryParams(gift="rattle", mishap="drop", repair="tell_truth", child="Maya", child_gender="girl", grownup="Mom", grownup_gender="mother", setting="nursery", seed=1),
    StoryParams(gift="bell", mishap="hide", repair="apology", child="Noah", child_gender="boy", grownup="Dad", grownup_gender="father", setting="bedroom", seed=2),
    StoryParams(gift="maraca", mishap="spill", repair="share", child="Ivy", child_gender="girl", grownup="Mom", grownup_gender="mother", setting="kitchen", seed=3),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for g in GIFTS:
        for m in MISHAPS:
            for r in REPAIRS:
                out.append((g, m, r))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming moral-value storyworld with a rattle.")
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-gender", choices=["mother", "father"])
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
    if args.gift and args.gift not in GIFTS:
        raise StoryError("unknown gift")
    if args.mishap and args.mishap not in MISHAPS:
        raise StoryError("unknown mishap")
    if args.repair and args.repair not in REPAIRS:
        raise StoryError("unknown repair")
    gift = args.gift or rng.choice(list(GIFTS))
    mishap = args.mishap or rng.choice(list(MISHAPS))
    repair = args.repair or rng.choice(list(REPAIRS))
    setting = args.setting or rng.choice(list(SETTINGS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES[child_gender])
    grownup_gender = args.grownup_gender or rng.choice(["mother", "father"])
    grownup = args.grownup or (("Mom" if grownup_gender == "mother" else "Dad"))
    return StoryParams(gift=gift, mishap=mishap, repair=repair, child=child, child_gender=child_gender, grownup=grownup, grownup_gender=grownup_gender, setting=setting)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a child named {f["child"].id} about a {f["gift"].label} and a kind choice.',
        f"Tell a moral-value story where {f['child'].id} makes a mistake with a {f['gift'].label}, then tells the truth and feels better.",
        f'Write a gentle story that includes the word "rattle" and ends with honesty, kindness, and trust.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    g = world.facts["grownup"]
    gift = world.facts["gift"]
    repair = world.facts["repair"]
    return [
        QAItem(question="What did the child find?", answer=f"{c.id} found {gift.phrase}."),
        QAItem(question="What made the story heartwarming?", answer=f"The child told {g.id} the truth, and {g.id} answered with kindness instead of anger."),
        QAItem(question="How did the story end?", answer=f"It ended with {c.id} holding the {gift.label} safely after everyone made things right."),
        QAItem(question="What moral choice did the child make?", answer=f"{c.id} chose honesty, which helped repair the mistake and turned the moment into trust."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a rattle?", answer="A rattle is a toy that makes a shaking sound when you move it."),
        QAItem(question="Why is telling the truth important?", answer="Telling the truth helps people fix mistakes and trust each other again."),
        QAItem(question="What does it mean to make amends?", answer="To make amends means to help fix a mistake and show that you care."),
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
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if n:
            bits.append(f"memes={dict(n)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("gift", GIFTS), ("mishap", MISHAPS), ("repair", REPAIRS), ("setting", SETTINGS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    gift = GIFTS[params.gift]
    mishap = MISHAPS[params.mishap]
    repair = REPAIRS[params.repair]
    w = World()
    child = w.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", label=params.child))
    grownup = w.add(Entity(id=params.grownup, kind="character", type=params.grownup_gender, role="grownup", label=params.grownup))
    gift_ent = w.add(Entity(id="gift", kind="thing", type="toy", label=gift.label, tags=set(gift.tags)))
    child.memes["love"] += 1
    w.say(f"{child.id} was in {SETTINGS[params.setting]} on a cozy day.")
    w.say(f"{child.id} found {gift.phrase}, and when it shook, it made a little rattle.")
    w.para()
    w.say(f"Then {child.id} made a mistake and {mishap.verb} the {gift.label}.")
    do_mishap(w, child, gift_ent, mishap)
    w.para()
    w.say(f"After a pause, {child.id} told {grownup.id} the truth.")
    make_amends(w, child, grownup, gift_ent, repair)
    w.say(f"{grownup.id} smiled, and the two of them kept the {gift.label} safe together.")
    w.facts.update(child=child, grownup=grownup, gift=gift, mishap=mishap, repair=repair, setting=params.setting)
    return StorySample(params=params, story=w.render(), prompts=generation_prompts(w), story_qa=story_qa(w), world_qa=world_knowledge_qa(w), world=w)


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
valid(G,M,R) :- gift(G), mishap(M), repair(R).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for m in MISHAPS:
        lines.append(asp.fact("mishap", m))
    for r in REPAIRS:
        lines.append(asp.fact("repair", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
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
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
