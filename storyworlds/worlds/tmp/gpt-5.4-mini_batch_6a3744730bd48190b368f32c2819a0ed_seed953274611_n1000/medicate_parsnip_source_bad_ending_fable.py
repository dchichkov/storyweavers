#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/medicate_parsnip_source_bad_ending_fable.py
============================================================================

A small standalone storyworld in a fable style.

Premise:
- A young animal gets a cough.
- They try to medicate themselves with a parsnip remedy made from a spring source.
- The source is unsafe or the remedy is too weak.
- The illness grows worse, and the ending is bad.

The story keeps the seed words in play: medicate, parsnip, source.
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
SICK_MIN = 1.0


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
        female = {"girl", "mother", "woman", "doe", "ewe", "hen"}
        male = {"boy", "father", "man", "buck", "ram", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Source:
    id: str
    label: str
    safe: bool
    cloudy: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Parsnip:
    id: str
    label: str
    phrase: str
    strength: int
    tags: set[str] = field(default_factory=set)


@dataclass
class MedicatePlan:
    id: str
    method: str
    potence: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    patient = world.get("patient")
    if patient.meters["ill"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.meters["ill"] += 1
    patient.memes["worry"] += 1
    out.append("__illness__")
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


def hazard(plan: MedicatePlan, source: Source, parsnip: Parsnip) -> bool:
    return plan.potence >= 1 and parsnip.strength >= 1 and source.safe is False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for plan in PLANS:
        for sid, source in SOURCES.items():
            for pid, parsnip in PARSNIPS.items():
                if hazard(plan, source, parsnip):
                    out.append((plan.id, sid, pid))
    return out


@dataclass
class StoryParams:
    plan: str
    source: str
    parsnip: str
    patient_name: str
    patient_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


ANIMALS = [
    ("hare", "boy", "Hare"),
    ("lamb", "girl", "Lamb"),
    ("kitten", "girl", "Kitten"),
    ("foal", "boy", "Foal"),
]
HELPERS = [
    ("owl", "girl", "Owl"),
    ("goat", "boy", "Goat"),
    ("crow", "girl", "Crow"),
]
PLANS = [
    MedicatePlan("swallow", "swallow the remedy", 1, "carefully swallowed the parsnip medicine", "swallowed the parsnip medicine, but the sickness only soured", tags={"medicate"}),
    MedicatePlan("sip", "sip the remedy", 1, "sipped the parsnip tea", "sipped the parsnip tea, but it did not help", tags={"medicate"}),
]
SOURCES = {
    "spring": Source("spring", "the spring source", safe=False, cloudy=True, tags={"source"}),
    "well": Source("well", "the old well source", safe=False, cloudy=True, tags={"source"}),
    "brook": Source("brook", "the brook source", safe=False, cloudy=True, tags={"source"}),
}
PARSNIPS = {
    "parsnip": Parsnip("parsnip", "parsnip", "a chopped parsnip", 1, tags={"parsnip"}),
    "root": Parsnip("root", "parsnip root", "a bitter parsnip root", 1, tags={"parsnip"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style bad-ending storyworld about a cure that goes wrong.")
    ap.add_argument("--plan", choices=sorted(p.id for p in PLANS))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--parsnip", choices=sorted(PARSNIPS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def explain_rejection() -> str:
    return "(No story: the requested ingredients do not make a believable bad-ending fable.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and args.plan not in {p.id for p in PLANS}:
        raise StoryError(explain_rejection())
    combos = valid_combos()
    if args.plan:
        combos = [c for c in combos if c[0] == args.plan]
    if args.source:
        combos = [c for c in combos if c[1] == args.source]
    if args.parsnip:
        combos = [c for c in combos if c[2] == args.parsnip]
    if not combos:
        raise StoryError(explain_rejection())
    plan, source, parsnip = rng.choice(sorted(combos))
    patient_name, patient_gender, _ = rng.choice(ANIMALS)
    helper_name, helper_gender, _ = rng.choice(HELPERS)
    if args.gender:
        patient_gender = args.gender
    if args.name:
        patient_name = args.name
    if args.helper:
        helper_name = args.helper
    return StoryParams(
        plan=plan,
        source=source,
        parsnip=parsnip,
        patient_name=patient_name,
        patient_gender=patient_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def tell(plan: MedicatePlan, source: Source, parsnip: Parsnip, patient_name: str, patient_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World()
    patient = world.add(Entity(id=patient_name, kind="character", type=patient_gender, role="patient", label=patient_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label=helper_name))
    spring = world.add(Entity(id="source", kind="thing", type="source", label=source.label))
    root = world.add(Entity(id="parsnip", kind="thing", type="food", label=parsnip.label))
    patient.meters["ill"] = 1.0
    helper.memes["concern"] = 1.0
    world.say(
        f"Once in a small field fable, {patient.id} felt a cough shaking in {patient.pronoun('possessive')} chest."
    )
    world.say(
        f"{helper.id} brought {parsnip.phrase} from {source.label_word if hasattr(source, 'label_word') else source.label} and said it would medicate the sickness."
    )
    world.para()
    world.say(
        f"{patient.id} listened, and {patient.pronoun().capitalize()} {plan.text}."
    )
    if source.cloudy:
        patient.meters["ill"] += 1
        patient.memes["worry"] += 1
        world.say(
            f"But the water from {source.label} was cloudy, and the parsnip medicine turned sour on the tongue."
        )
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"By evening, the cough was worse instead of better."
    )
    world.say(
        f"{helper.id} called for help, yet the remedy had already failed."
    )
    world.say(
        f"The little fable ended sadly: {patient.id} stayed weak, and the bad choice became the lesson."
    )
    world.facts.update(
        patient=patient,
        helper=helper,
        source=source,
        parsnip=parsnip,
        plan=plan,
        outcome="bad",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.plan not in {p.id for p in PLANS}:
        raise StoryError(explain_rejection())
    if params.source not in SOURCES or params.parsnip not in PARSNIPS:
        raise StoryError(explain_rejection())
    world = tell(
        PLANS[[p.id for p in PLANS].index(params.plan)],
        SOURCES[params.source],
        PARSNIPS[params.parsnip],
        params.patient_name,
        params.patient_gender,
        params.helper_name,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story that uses the words "medicate", "parsnip", and "source".',
        f"Tell a sad little animal tale where {f['patient'].id} tries to medicate a cough with parsnip water from a source, but it goes wrong.",
        "Write a short bad-ending fable about a cure that fails because the source is unsafe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    patient, helper, source, parsnip = f["patient"], f["helper"], f["source"], f["parsnip"]
    return [
        ("Who is the story about?", f"It is about {patient.id}, who got sick, and {helper.id}, who tried to help."),
        ("What did they try to do?", f"They tried to medicate the cough with parsnip medicine from the source. The idea sounded clever, but it was not safe."),
        ("Why did the ending go badly?", f"The source water was cloudy, so the parsnip remedy turned sour and did not heal the cough. Because of that, the sickness grew worse instead of better."),
        ("How did the story end?", f"It ended sadly, with {patient.id} still weak. The bad choice became the lesson of the fable."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a parsnip?", "A parsnip is a pale root vegetable that grows underground. People can cook it, but it is not a magic medicine."),
        ("What is a source in a story like this?", "A source is where water comes from, like a spring or well. If the source is dirty or cloudy, the water may not be safe."),
        ("What does it mean to medicate?", "To medicate means to give medicine or treat an illness. Medicine is supposed to help a sick body recover."),
    ]


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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P,S,R) :- plan(P), source(S), parsnip(R), unsafe(S), medicate_plan(P).
valid(P,S,R) :- hazard(P,S,R).
outcome(bad) :- chosen_plan(P), chosen_source(S), chosen_parsnip(R), hazard(P,S,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLANS:
        lines.append(asp.fact("plan", p.id))
        lines.append(asp.fact("medicate_plan", p.id))
    for sid, s in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if not s.safe:
            lines.append(asp.fact("unsafe", sid))
    for pid, p in PARSNIPS.items():
        lines.append(asp.fact("parsnip", pid))
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
        print("MISMATCH: ASP and Python valid_combos disagree.")
        return 1
    sample = generate(resolve_params(argparse.Namespace(plan=None, source=None, parsnip=None, name=None, helper=None, gender=None), random.Random(7)))
    if not sample.story:
        print("MISMATCH: story generation failed.")
        return 1
    print(f"OK: {len(valid_combos())} combos and story generation smoke test passed.")
    return 0


def build_parser_wrapper() -> argparse.ArgumentParser:
    return build_parser()


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
        print(f"{len(asp_valid_combos())} compatible (plan, source, parsnip) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(plan="swallow", source="spring", parsnip="parsnip", patient_name="Hare", patient_gender="boy", helper_name="Owl", helper_gender="girl"),
            StoryParams(plan="sip", source="well", parsnip="root", patient_name="Lamb", patient_gender="girl", helper_name="Goat", helper_gender="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fable that includes the words "medicate", "parsnip", and "source".',
        f"Tell a bad-ending animal fable about {f['patient'].id} trying to medicate a cough with parsnip water from a source.",
        "Write a short moral tale where a remedy fails because the source is unsafe.",
    ]


if __name__ == "__main__":
    main()
