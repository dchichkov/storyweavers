#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slow_cortisone_fur_teamwork_mystery_to_solve.py
===============================================================================

A small comedic storyworld about a slow pet mystery, teamwork, and a helpful
grown-up remedy. A kid and a friend search for the cause of a strange itchy
problem, discover it is fur-related, and work together with a calm adult to fix
it in a gentle, funny way.

The world keeps typed entities with physical meters and emotional memes, drives
prose from simulated state, provides three QA sets, and includes an inline ASP
twin for parity checks.
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    label: str
    mood: str
    places: list[str] = field(default_factory=list)
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
class Mystery:
    id: str
    clue: str
    source: str
    symptom: str
    weird: str
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
class Helper:
    id: str
    label: str
    kind: str
    action: str
    result: str
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
    label: str
    sense: int
    effect: int
    text: str
    fail_text: str
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


def _r_slow(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["searching"] < THRESHOLD:
            continue
        if e.meters["progress"] >= THRESHOLD:
            continue
        sig = ("slow", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["progress"] += 1
        out.append("")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    patient = world.entities.get("pet")
    if not patient:
        return out
    if patient.meters["itch"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.meters["itch"] = 0.0
    patient.meters["calm"] += 1
    out.append("")
    return out


CAUSAL_RULES = [Rule("slow_progress", _r_slow), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if b)
    if narrate:
        for s in produced:
            world.say(s)


def reasonableness_gate(mystery: Mystery, helper: Helper, remedy: Remedy) -> bool:
    return mystery.source == "fur" and remedy.sense >= 2 and helper.kind == "teamwork"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for rid in REMEDIES:
                if reasonableness_gate(MYSTERIES[mid], HELPERS["teamwork"], REMEDIES[rid]):
                    combos.append((sid, mid, rid))
    return combos


def _predict(world: World, remedy_id: str) -> dict:
    sim = world.copy()
    _help_fix(sim, sim.get("adult"), HELPERS["teamwork"], REMEDIES[remedy_id], narrate=False)
    pet = sim.get("pet")
    return {"itch": pet.meters["itch"], "calm": pet.meters["calm"]}


def _introduce(world: World, kid: Entity, pal: Entity, setting: Setting) -> None:
    world.say(
        f"{kid.id} and {pal.id} were in {setting.label}, where everything felt "
        f"a little funny and a little too slow."
    )
    world.say(
        f"They were trying to solve a mystery with teamwork, because the day had "
        f"an odd little itch about it."
    )


def _describe_problem(world: World, pet: Entity, mystery: Mystery) -> None:
    pet.memes["worry"] += 1
    world.say(
        f"The clue was simple: {mystery.clue}. {pet.id} kept sneezing and making "
        f"a face that said, 'I did not agree to this.'"
    )
    world.say(
        f"Something about {mystery.symptom} was spreading through {mystery.weird}."
    )


def _search(world: World, kid: Entity, pal: Entity, mystery: Mystery) -> None:
    kid.memes["searching"] += 1
    pal.memes["searching"] += 1
    world.say(
        f"{kid.id} checked the couch, {pal.id} checked under the table, and both "
        f"of them checked the pet bed at the same time."
    )
    world.say(
        f"At last, they found the odd truth: tiny bits of {mystery.source} were "
        f"the trouble."
    )


def _help_fix(world: World, adult: Entity, helper: Helper, remedy: Remedy, narrate: bool = True) -> None:
    pet = world.get("pet")
    pet.memes["relief"] += 1
    adult.memes["calm"] += 1
    body = remedy.text.format(source="fur")
    if narrate:
        world.say(
            f"{adult.label_word.capitalize()} came over with a calm smile and "
            f"used teamwork to {helper.action}. Then {adult.pronoun()} {body}."
        )
        world.say(
            f"{pet.id} stopped twitching, and the whole room seemed to exhale."
        )
    pet.meters["itch"] = 0.0
    pet.meters["clean"] += 1
    propagate(world, narrate=False)


def _lesson(world: World, kid: Entity, pal: Entity, adult: Entity, mystery: Mystery) -> None:
    kid.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"{adult.label_word.capitalize()} chuckled, because mysteries can be rude "
        f"little comedians."
    )
    world.say(
        f'"When something looks strange," {adult.pronoun()} said, "we slow down, '
        f'look together, and fix the real cause."'
    )
    world.say(
        f"{kid.id} and {pal.id} nodded. The mystery had been solved, and the fur "
        f"was no longer the villain."
    )


def tell(setting: Setting, mystery: Mystery, helper: Helper, remedy: Remedy,
         kid_name: str = "Mina", pal_name: str = "Bo", adult_name: str = "Mom") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type="girl", role="kid"))
    pal = world.add(Entity(id=pal_name, kind="character", type="boy", role="pal"))
    adult = world.add(Entity(id=adult_name, kind="character", type="mother", role="adult", label="the grown-up"))
    pet = world.add(Entity(id="pet", kind="character", type="thing", label="the fluffy pet"))
    pet.meters["itch"] = 1.0
    pet.memes["worry"] = 1.0

    _introduce(world, kid, pal, setting)
    world.para()
    _describe_problem(world, pet, mystery)
    _search(world, kid, pal, mystery)
    world.para()
    _help_fix(world, adult, helper, remedy)
    _lesson(world, kid, pal, adult, mystery)

    world.facts.update(
        setting=setting, mystery=mystery, helper=helper, remedy=remedy,
        kid=kid, pal=pal, adult=adult, pet=pet,
        solved=True, source=mystery.source,
    )
    return world


SETTINGS = {
    "laundry_room": Setting(id="laundry_room", label="the laundry room", mood="comically busy",
                            places=["basket", "dryer", "soap shelf"]),
    "hallway": Setting(id="hallway", label="the hallway", mood="echoey", places=["rug", "coat rack"]),
    "porch": Setting(id="porch", label="the porch", mood="windy", places=["bench", "doormat"]),
}

MYSTERIES = {
    "fur": Mystery(id="fur", clue="there was fur on the blanket", source="fur",
                   symptom="the itchy sneezes", weird="the pet's favorite blanket",
                   tags={"fur", "mystery"}),
    "slow": Mystery(id="slow", clue="the footsteps sounded slow and sleepy", source="fur",
                    symptom="the sleepy shuffle", weird="the hallway rug",
                    tags={"slow", "mystery"}),
    "cortisone": Mystery(id="cortisone", clue="a little tube said cortisone and everyone looked puzzled",
                         source="fur", symptom="the itchy spot", weird="the pet's collar",
                         tags={"cortisone", "mystery"}),
}

HELPERS = {
    "teamwork": Helper(id="teamwork", label="teamwork", kind="teamwork",
                       action="brush the fur away together", result="the fur got brushed away",
                       tags={"teamwork"}),
}

REMEDIES = {
    "gentle_brush": Remedy(id="gentle_brush", label="a gentle brush", sense=3, effect=2,
                           text="brushed the fur off the blanket with a gentle brush",
                           fail_text="tried brushing, but the fur was still everywhere",
                           tags={"fur"}),
    "cortisone_cream": Remedy(id="cortisone_cream", label="cortisone cream", sense=3, effect=3,
                              text="put a tiny dab of cortisone cream where the itch was",
                              fail_text="used the cortisone cream too soon, before finding the fur",
                              tags={"cortisone"}),
    "vacuum": Remedy(id="vacuum", label="the vacuum", sense=2, effect=4,
                     text="vacuumed the rug until the fur vanished like a tiny sneezy ghost",
                     fail_text="vacuumed slowly, but the fur clung on for dear life",
                     tags={"fur"}),
}

CURATED = [
    StorySample,  # placeholder to be replaced below
]

CURATED = [
    # populate with params after StoryParams defined
]

@dataclass
class StoryParams:
    setting: str
    mystery: str
    helper: str
    remedy: str
    kid_name: str = "Mina"
    pal_name: str = "Bo"
    adult_name: str = "Mom"
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "slow", "cortisone", and "fur".',
        f"Tell a comedy story where {f['kid'].id} and {f['pal'].id} solve a mystery together and a grown-up helps with the fur problem.",
        f'Write a teamwork mystery story with a gentle ending where the clue leads to fur and someone mentions cortisone.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, pal, adult, pet = f["kid"], f["pal"], f["adult"], f["pet"]
    mystery, remedy = f["mystery"], f["remedy"]
    return [
        ("Who solved the mystery?",
         f"{kid.id} and {pal.id} solved it together, with the grown-up helping at the end. They worked as a team instead of trying to guess alone."),
        ("What was the mystery about?",
         f"It turned out to be fur. That explained the sneezing and the strange itchy trouble."),
        ("What did the grown-up do?",
         f"{adult.label_word.capitalize()} came over, helped brush or treat the problem, and used {remedy.label} if needed. The help was calm and practical, which made the pet feel better."),
        ("Why was the story funny?",
         f"The clues kept sounding serious, but the answer was just a fluffy mess. The grown-up and the children had to take the tiny problem very seriously, which made it amusing."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is fur?",
         "Fur is the soft hair that covers some animals. It can shed and get on blankets, clothes, and rugs."),
        ("What is teamwork?",
         "Teamwork means people help each other and do a job together. It can make a hard job easier and faster."),
        ("What is cortisone?",
         "Cortisone is medicine some grown-ups use to help calm itchy skin. A grown-up should choose and use it carefully."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
source(fur).
sense(gentle_brush,3).
sense(cortisone_cream,3).
sense(vacuum,2).
teamwork(teamwork).
reasonably_valid(S,M,R) :- source(M), sense(R,N), N >= 2, teamwork(T), setting(S), mystery(M), remedy(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("teamwork", hid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("source", "fur"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/3."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, helper=None, remedy=None, kid_name=None, pal_name=None, adult_name=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: slow mystery, cortisone, fur, teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--pal")
    ap.add_argument("--adult")
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
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError("That remedy is too silly for this storyworld.")
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    helper = args.helper or "teamwork"
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if not reasonableness_gate(MYSTERIES[mystery], HELPERS[helper], REMEDIES[remedy]):
        raise StoryError("No valid combination matches the given options.")
    return StoryParams(
        setting=setting, mystery=mystery, helper=helper, remedy=remedy,
        kid_name=args.name or rng.choice(["Mina", "Tia", "Nia", "Lena"]),
        pal_name=args.pal or rng.choice(["Bo", "Jax", "Ollie", "Pip"]),
        adult_name=args.adult or rng.choice(["Mom", "Dad", "Aunt Jo"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.helper not in HELPERS or params.remedy not in REMEDIES:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], HELPERS[params.helper], REMEDIES[params.remedy], params.kid_name, params.pal_name, params.adult_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show reasonably_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a[0]} {a[1]} {a[2]}" for a in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated_params = [
            StoryParams(setting="laundry_room", mystery="fur", helper="teamwork", remedy="gentle_brush", kid_name="Mina", pal_name="Bo", adult_name="Mom"),
            StoryParams(setting="hallway", mystery="cortisone", helper="teamwork", remedy="cortisone_cream", kid_name="Tia", pal_name="Pip", adult_name="Dad"),
            StoryParams(setting="porch", mystery="slow", helper="teamwork", remedy="vacuum", kid_name="Nia", pal_name="Jax", adult_name="Aunt Jo"),
        ]
        samples = [generate(p) for p in curated_params]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
