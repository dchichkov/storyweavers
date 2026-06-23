#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/defective_trigger_puff_problem_solving_kindness_myth.py
==============================================================================================================

A standalone storyworld for a small mythic tale about a broken trigger,
a puff of breath or smoke, and a kind problem-solving ending.

This world keeps the simulation small:
- a hero tries to wake or move something by using a trigger object,
- the trigger is defective,
- a puff event makes the situation change,
- a helper responds with kindness and practical problem solving,
- the ending proves what changed in the world.

The prose is driven from state, not from a fixed paragraph template.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helper_for: Optional[str] = None
    defective: bool = False
    trigger: bool = False
    puffable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "goddess"}
        male = {"boy", "man", "father", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Realm:
    name: str
    setting: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class TriggerThing:
    id: str
    label: str
    phrase: str
    action: str
    use_word: str
    affects: str
    sense: bool = True


@dataclass
class PuffThing:
    id: str
    label: str
    phrase: str
    effect: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpAction:
    id: str
    label: str
    text: str
    fix: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.realm)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_puff(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["puff"] < THRESHOLD:
            continue
        sig = ("puff", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "sleeping_wind" in world.entities:
            world.get("sleeping_wind").meters["stirred"] += 1
        for ent in world.characters():
            if ent.id != actor.id:
                ent.memes["worry"] += 1
        out.append(f"A small puff moved through the hall.")
    return out


def _r_heal(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["kindness"] < THRESHOLD:
            continue
        if ent.meters["problem"] < THRESHOLD:
            continue
        sig = ("heal", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["solution"] += 1
        ent.memes["calm"] += 1
        out.append(f"{ent.id} found a gentler way.")
    return out


CAUSAL_RULES = [
    Rule("puff", "motion", _r_puff),
    Rule("heal", "social", _r_heal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def trigger_works(trigger: TriggerThing, realm: Realm) -> bool:
    action_key = trigger.action.replace(" the ", "_").replace(" ", "_")
    return trigger.sense and (
        action_key in realm.affordances
        or any(part in trigger.action for part in realm.affordances)
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for realm in REALMS:
        for trig_id, trig in TRIGGERS.items():
            for puff_id, puff in PUFFS.items():
                if trigger_works(trig, REALMS[realm]) and puff.cause in realm:
                    combos.append((realm, trig_id, puff_id))
    return combos


@dataclass
class StoryParams:
    realm: str
    trigger: str
    puff: str
    hero: str
    helper: str
    hero_kind: str
    helper_kind: str
    seed: Optional[int] = None


def make_story(world: World, params: StoryParams) -> World:
    realm = world.realm
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_kind, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_kind, role="helper"))
    trigger = TRIGGERS[params.trigger]
    puff = PUFFS[params.puff]
    helpact = HELPERS[pick_help(params.trigger, params.puff)]

    world.facts.update(hero=hero, helper=helper, trigger=trigger, puff=puff, helpact=helpact)

    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    helper.memes["calm"] += 1

    world.say(f"In {realm.name}, {hero.id} found {trigger.phrase}, a tool with a {trigger.label} that should have answered at once.")
    world.say(f"But the {trigger.label} was defective, and when {hero.id} tried to use it, nothing came the way it should.")
    hero.meters["problem"] += 1

    world.para()
    world.say(f"Then {hero.id} gave a careful puff toward {puff.phrase}.")
    hero.meters["puff"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{helper.id} did not laugh. {helper.id} came close, spoke kindly, and chose a clearer plan.")
    world.say(f"With {helpact.text}, {helper.id} used {helpact.fix} instead of pushing the broken trigger harder.")
    helper.meters["solution"] += 1
    hero.memes["relief"] += 1
    hero.meters["problem"] = 0
    world.say(f"At last, the little task worked, and the puff became a gentle sign instead of a troublemaker.")

    world.facts["resolved"] = True
    return world


def pick_help(trigger_id: str, puff_id: str) -> str:
    if trigger_id == "reed": return "knot"
    if puff_id == "torch_smoke": return "fan"
    return "knot"


REALMS = {
    "hill_shrine": Realm("the hill shrine", "a shrine path", {"ring", "open_gate", "call"}),
    "river_temple": Realm("the river temple", "a temple hall", {"lift", "call", "open_gate"}),
    "orchard_ruin": Realm("the orchard ruin", "an old orchard", {"ring", "call", "open_gate"}),
}

TRIGGERS = {
    "bell": TriggerThing("bell", "bell rope", "a brass bell rope", "ring the bell", "trigger", "the gate", True),
    "gate_lever": TriggerThing("gate_lever", "lever", "an old gate lever", "open the gate", "trigger", "the gate", True),
    "reed": TriggerThing("reed", "reed latch", "a bent reed latch", "open the gate", "trigger", "the gate", False),
}

PUFFS = {
    "breath_puff": PuffThing("breath_puff", "breath puff", "a warm puff of breath", "the dust moved", "hill", {"wind"}),
    "torch_smoke": PuffThing("torch_smoke", "smoke puff", "a puff of torch smoke", "the embers stirred", "river", {"smoke"}),
    "incense_puff": PuffThing("incense_puff", "incense puff", "a soft puff of incense", "the air turned sweet", "orchard", {"incense"}),
}

HELPERS = {
    "knot": HelpAction("knot", "knot", "with a kinder knot", "the broken cord", 1, {"kindness"}),
    "fan": HelpAction("fan", "fan", "with a palm fan", "the smoke away", 2, {"kindness", "problem_solving"}),
}

GIRL_NAMES = ["Asha", "Mira", "Iri", "Nara", "Suri", "Lina"]
BOY_NAMES = ["Kian", "Ravi", "Taro", "Daro", "Milo", "Oren"]
TRAITS = ["gentle", "curious", "patient", "brave"]


def realm_by_key(key: str) -> Realm:
    return REALMS[key]


def valid_trigger_for_realm(realm: Realm, trig: TriggerThing) -> bool:
    return trigger_works(trig, realm)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.puff is None or c[2] == args.puff)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, trigger, puff = rng.choice(list(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = "girl" if gender == "boy" else "boy"
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(
        realm=realm,
        trigger=trigger,
        puff=puff,
        hero=hero,
        helper=helper,
        hero_kind=gender,
        helper_kind=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic child-friendly story that includes the words "{f["trigger"].label}", "{f["puff"].label}", and "defective".',
        f"Tell a myth-style tale where {f['hero'].id} faces a broken trigger, but {f['helper'].id} answers with kindness and a practical plan.",
        f"Write a short legend about a defective trigger and a puff that leads to problem solving instead of anger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trig = f["trigger"]
    puff = f["puff"]
    return [
        QAItem(
            question=f"What was defective in the story?",
            answer=f"The {trig.label} was defective. It did not work the way {hero.id} needed, so the first plan failed.",
        ),
        QAItem(
            question=f"What did {hero.id} do that made the situation change?",
            answer=f"{hero.id} gave a careful puff toward {puff.phrase}. That puff made the problem visible and gave {helper.id} a chance to solve it kindly.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} stayed kind and chose a practical fix. Instead of forcing the broken trigger, {helper.id} used a gentler plan that made the task work.",
        ),
        QAItem(
            question=f"What proved the ending changed?",
            answer=f"By the end, the problem meter went back to zero and the solution meter rose. The task worked, and the puff had become a harmless sign instead of a snag.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does defective mean?",
            answer="Defective means something is broken or not working the way it should. A defective thing needs a fix before it can do its job well.",
        ),
        QAItem(
            question="What is a trigger in a tool or story?",
            answer="A trigger is the part that makes something start or happen. When a trigger works, it can open, ring, or begin the action.",
        ),
        QAItem(
            question="What is a puff?",
            answer="A puff is a small burst of air, smoke, or breath. It is usually little, but it can still make things move or change.",
        ),
        QAItem(
            question="Why is kindness useful in a problem?",
            answer="Kindness helps people stay calm and listen to each other. That makes it easier to find a fix that does not hurt anyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.defective:
            bits.append("defective=True")
        out.append(f"{e.id}: {e.type} " + " ".join(bits))
    out.append(f"fired={sorted({x[0] for x in world.fired})}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rk, realm in REALMS.items():
        lines.append(asp.fact("realm", rk))
        for a in sorted(realm.affordances):
            lines.append(asp.fact("affords", rk, a))
    for tk, trig in TRIGGERS.items():
        lines.append(asp.fact("trigger", tk))
        if trig.sense:
            lines.append(asp.fact("works", tk))
        lines.append(asp.fact("action", tk, trig.action))
    for pk, puff in PUFFS.items():
        lines.append(asp.fact("puff", pk))
        lines.append(asp.fact("cause", pk, puff.cause))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,T,P) :- realm(R), trigger(T), puff(P), works(T), affordances(R,_), cause(P,_).
defective(T) :- trigger(T), not works(T).
problem(R,T) :- realm(R), trigger(T), defective(T), affords(R, _).
kind_help(H) :- helper(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        clingo_set = set(asp_valid_combos())
        py_set = set(valid_combos())
        ok = clingo_set == py_set
        sample = generate(resolve_params(argparse.Namespace(realm=None, trigger=None, puff=None, gender=None, hero=None, helper=None), random.Random(7)))
        smoke = bool(sample.story)
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    if not ok:
        print("MISMATCH between ASP and Python combos")
        print("only in asp:", sorted(clingo_set - py_set))
        print("only in python:", sorted(py_set - clingo_set))
        return 1
    if not smoke:
        print("ERROR: smoke test failed")
        return 1
    print(f"OK: ASP matches Python for {len(py_set)} combos and story generation works.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: a defective trigger, a puff, kindness, and problem solving.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--puff", choices=PUFFS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def generate(params: StoryParams) -> StorySample:
    realm = REALMS[params.realm]
    if params.trigger not in TRIGGERS or params.puff not in PUFFS:
        raise StoryError("Invalid story params.")
    world = World(realm)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_kind, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_kind, role="helper"))
    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    helper.memes["problem_solving"] += 1
    world.facts.update(hero=hero, helper=helper, trigger=TRIGGERS[params.trigger], puff=PUFFS[params.puff])

    world.say(f"In {realm.name}, {hero.id} found a {TRIGGERS[params.trigger].label}, and it was defective.")
    world.say(f"The old tool should have answered right away, but the broken trigger stayed stubborn and still.")
    hero.meters["problem"] += 1
    world.para()
    world.say(f"Then {hero.id} sent out a soft puff toward {PUFFS[params.puff].phrase}.")
    hero.meters["puff"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{helper.id} came with kindness, not blame.")
    world.say(f"{helper.id} looked closely, named the problem, and chose a small fix that could actually work.")
    helper.memes["kindness"] += 1
    helper.memes["problem_solving"] += 1
    helper.meters["solution"] += 1
    hero.meters["problem"] = 0
    world.say(f"At last, the task moved as it should, and the little puff became part of the answer.")
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


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.puff is None or c[2] == args.puff)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, trigger, puff = rng.choice(list(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(BOY_NAMES if gender == "girl" else GIRL_NAMES)
    return StoryParams(realm=realm, trigger=trigger, puff=puff, hero=hero, helper=helper, hero_kind=gender, helper_kind=("boy" if gender == "girl" else "girl"))


CURATED = [
    StoryParams(realm="hill_shrine", trigger="bell", puff="breath_puff", hero="Asha", helper="Kian", hero_kind="girl", helper_kind="boy"),
    StoryParams(realm="river_temple", trigger="gate_lever", puff="torch_smoke", hero="Mira", helper="Oren", hero_kind="girl", helper_kind="boy"),
]


def valid_combo_gate(params: StoryParams) -> bool:
    return params.realm in REALMS and params.trigger in TRIGGERS and params.puff in PUFFS and trigger_works(TRIGGERS[params.trigger], REALMS[params.realm])


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_args(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
