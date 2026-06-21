#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/electrolyte_hearth_rhyme_tall_tale.py
=====================================================================

A small standalone storyworld for a tall-tale rhyme about a child, a long ride,
and a warming drink by the hearth. The seed words are "electrolyte" and
"hearth"; the story keeps a child-facing, rhythmic tone while remaining a
state-driven simulation rather than a frozen paragraph swap.

Domain sketch:
- A child comes in dusty and thirsty after a big prairie errand.
- A grown-up wants to warm an electrolyte drink near the hearth.
- The tension is whether the drink is heated gently and safely, or overheated
  and ruined.
- The turn is a sensible method: warm it just enough, not too hot.
- The ending image proves what changed: thirst eased, cheeks warmed, and the
  hearth became a cozy place instead of a risky one.

The prose aims for a tall-tale lilt with light rhyme and concrete images.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    warmable: bool = False
    safe_hearth: bool = False

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
class Vessel:
    id: str
    label: str
    safe_heat: bool
    heats_fast: bool
    plural: bool = False

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
class Drink:
    id: str
    label: str
    phrase: str
    hot_phrase: str
    too_hot_phrase: str
    bitter_phrase: str
    flavor: str
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
class Hearth:
    id: str
    label: str
    glow: str
    warmth: int
    scorch: int

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
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    cup = world.entities.get("cup")
    drink = world.entities.get("drink")
    hearth = world.entities.get("hearth")
    if not cup or not drink or not hearth:
        return out
    if cup.meters["on_hearth"] < THRESHOLD:
        return out
    sig = ("heat", cup.id, drink.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if cup.attrs.get("safe_heat"):
        drink.meters["warm"] += 1
        out.append("__warm__")
    else:
        drink.meters["warm"] += 2
        drink.meters["too_hot"] += 1
        cup.meters["soot"] += 1
        out.append("__too_hot__")
    return out


def _r_thirst(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    drink = world.entities.get("drink")
    if not child or not drink:
        return out
    sig = ("thirst", child.id, drink.id)
    if sig in world.fired:
        return out
    if drink.meters["sipped"] >= THRESHOLD:
        world.fired.add(sig)
        child.meters["thirst"] = max(0.0, child.meters["thirst"] - 1.0)
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        out.append("__sipped__")
    return out


def _r_soot(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["soot"] < THRESHOLD:
            continue
        sig = ("soot", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__soot__")
    return out


CAUSAL_RULES = [Rule("heat", "physical", _r_heat), Rule("thirst", "physical", _r_thirst), Rule("soot", "physical", _r_soot)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def safe_response(vessel: Vessel, drink: Drink) -> bool:
    return vessel.safe_heat and not vessel.heats_fast and drink.id in {"electrolyte", "lemonade"}


def reasonable_combo(vessel: Vessel, drink: Drink) -> bool:
    return safe_response(vessel, drink)


@dataclass
@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    drink: str
    vessel: str
    hearth: str
    delay: int = 0
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


CHILD_NAMES = ["Mabel", "Jasper", "June", "Milo", "Ada", "Benny", "Pearl", "Otis"]
PARENT_NAMES = ["Ma", "Pa", "Aunt Nell", "Uncle Jed"]
TRAITS = ["bright", "bold", "steady", "cheery", "curious"]


DRINKS = {
    "electrolyte": Drink(
        "electrolyte",
        "electrolyte drink",
        "a bottle of electrolyte drink",
        "warm and bright",
        "too hot to sip",
        "bitter on the tongue",
        "salty-sweet",
        tags={"electrolyte", "drink"},
    ),
    "cocoa": Drink(
        "cocoa",
        "cocoa",
        "a mug of cocoa",
        "warm and brown",
        "too hot to sip",
        "bitter on the tongue",
        "chocolatey",
        tags={"drink"},
    ),
}


VESSELS = {
    "kettle": Vessel("kettle", "iron kettle", safe_heat=True, heats_fast=False),
    "tin": Vessel("tin", "tin cup", safe_heat=False, heats_fast=True),
    "stone_mug": Vessel("stone_mug", "stone mug", safe_heat=True, heats_fast=True),
}


HEARTHS = {
    "oak": Hearth("oak", "oak hearth", "a soft gold glow", warmth=1, scorch=1),
    "brick": Hearth("brick", "brick hearth", "a red ember glow", warmth=2, scorch=2),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for d in DRINKS.values():
        for v in VESSELS.values():
            if reasonable_combo(v, d):
                for h in HEARTHS:
                    out.append((d.id, v.id, h))
    return out


def predict(world: World) -> dict:
    sim = world.copy()
    _do_warm(sim, narrate=False)
    return {
        "warm": sim.get("drink").meters["warm"] >= THRESHOLD,
        "too_hot": sim.get("drink").meters["too_hot"] >= THRESHOLD,
        "soot": sim.get("cup").meters["soot"] >= THRESHOLD,
    }


def _do_warm(world: World, narrate: bool = True) -> None:
    world.get("cup").meters["on_hearth"] = 1.0
    propagate(world, narrate=narrate)


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, label=params.parent_name, role="guide"))
    drink = world.add(Entity(id="drink", type="thing", label=DRINKS[params.drink].label))
    cup = world.add(Entity(id="cup", type="thing", label=VESSELS[params.vessel].label, safe_hearth=VESSELS[params.vessel].safe_heat))
    hearth = world.add(Entity(id="hearth", type="thing", label=HEARTHS[params.hearth].label))
    child.meters["thirst"] = 2.0
    child.memes["hope"] = 1.0
    drink.meters["warm"] = 0.0

    world.say(
        f"On a windy trail with a tumble and sway, {child.label} came home from a dusty day."
    )
    world.say(
        f"{parent.label} smiled by the {hearth.label}, low and bright, for a tall-tale tune in the evening light."
    )
    world.say(
        f'"We have {drink.phrase}," {parent.label} said with cheer, "and a little warm help will make it good to hear."'
    )
    world.para()

    world.say(
        f"{child.label} was dry as a whistle, tired as a mule, and thirst rode in hard like a stubborn fool."
    )
    world.say(
        f"{child.label} peered at the {cup.label} and the {hearth.label} glow, then asked if the drink could warm slow."
    )
    world.say(
        f'If it warmed too fast, it might turn "too hot to sip," and spoil the sweet salt on each little lip.'
    )

    if params.delay > 0:
        world.say(
            f"{parent.label} waited a spell, then moved with care, because rushing a hearth can singe the air."
        )

    world.para()
    if VESSELS[params.vessel].safe_heat:
        world.say(
            f"{parent.label} set the {cup.label} near the hearth and nudged it close, not near the sparks, but near the rose."
        )
    else:
        world.say(
            f"{parent.label} set the {cup.label} near the hearth, but the cup was thin, and that was a perilous whim."
        )

    _do_warm(world, narrate=False)
    if drink.meters["too_hot"] >= THRESHOLD:
        world.say(
            f"The drink went brawny and blazing bright, then came up bitter instead of right."
        )
        world.say(
            f"{child.label} puckered up; the sip was a blip, and even the hearth gave a worried flip."
        )
        world.say(
            f"But {parent.label} did not frown or scold the child; {parent.label} just chose again, calm and mild."
        )
        world.say(
            f"Next they used a safer mug and warmed it slow, till the steam came sweet in a gentle row."
        )
        drink.meters["too_hot"] = 0.0
        drink.meters["warm"] = 1.0
        cup.meters["soot"] = 0.0
    else:
        world.say(
            f"The drink warmed kindly, a gold-kissed gloss, and the hearth kept its manners like a true-blue boss."
        )

    drink.meters["sipped"] = 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{child.label} sipped the {DRINKS[params.drink].label}, and the weary old thirst took wing and quit."
    )
    world.say(
        f"{child.label} grinned at the {hearth.label} shine; the room felt snug, and the night felt fine."
    )
    world.say(
        f"With a warm little drink and a fire kept neat, the tall tale ended on a cozy beat."
    )

    world.facts.update(
        child=child,
        parent=parent,
        drink=drink,
        cup=cup,
        hearth=hearth,
        params=params,
        outcome="too_hot" if drink.meters["too_hot"] >= THRESHOLD else "warm",
        predicted=predict(world),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a tall-tale story in rhyme that includes the words "electrolyte" and "hearth".',
        f"Tell a child-friendly rhyme where {p.child_name} comes in dusty and thirsty, and a grown-up warms an electrolyte drink by the hearth.",
        f"Write a funny, cozy western-style story with a little rhythm and a safe ending, using the word electrolyte.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    drink = f["drink"]
    cup = f["cup"]
    qas = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.label}, who comes home thirsty, and {parent.label}, who helps with the drink by the hearth.",
        ),
        QAItem(
            question=f"What did {parent.label} want to do with the electrolyte drink?",
            answer=f"{parent.label} wanted to warm the electrolyte drink near the hearth. The goal was to make it cozy and easy to sip, not to let it get too hot.",
        ),
    ]
    if f["outcome"] == "too_hot":
        qas.append(
            QAItem(
                question="What went wrong before the grown-up fixed it?",
                answer=f"The drink got too hot in the {cup.label}, so the first sip was bitter instead of sweet. Then the grown-up switched to a safer way and warmed it more gently.",
            )
        )
    else:
        qas.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with {child.label} sipping the warm electrolyte drink and smiling by the hearth. The careful heat made the drink cozy and safe.",
            )
        )
    qas.append(
        QAItem(
            question=f"Why did {child.label} feel better at the end?",
            answer=f"{child.label} felt better because the thirst went away after the drink was warmed and sipped. The cozy hearth and the safe drink made the room feel calm and snug.",
        )
    )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an electrolyte drink?",
            answer="An electrolyte drink is a drink with minerals and water that can help someone who is tired or thirsty feel better.",
        ),
        QAItem(
            question="What is a hearth?",
            answer="A hearth is the place by a fire where people can keep warm. It can be cozy, but it must be used carefully.",
        ),
        QAItem(
            question="Why should a cup near a hearth be watched closely?",
            answer="A cup near a hearth can get too hot if it sits by the fire too long. Careful grown-ups move slowly so the drink stays safe and pleasant.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for did in DRINKS:
        lines.append(asp.fact("drink", did))
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        if v.safe_heat:
            lines.append(asp.fact("safe_heat", vid))
        if v.heats_fast:
            lines.append(asp.fact("heats_fast", vid))
    for hid, h in HEARTHS.items():
        lines.append(asp.fact("hearth", hid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
ok_combo(D,V,H) :- drink(D), vessel(V), hearth(H), safe_heat(V), not heats_fast(V), D = electrolyte.
"""

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show ok_combo/3."))
    return sorted(set(asp.atoms(model, "ok_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combos differ.")
        rc = 1
    else:
        print(f"OK: {len(valid_combos())} compatible combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-tested normal story generation.")
    except Exception as exc:
        print(f"FAILED smoke test: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale rhyme world: electrolyte and hearth.")
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--hearth", choices=HEARTHS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy", "aunt", "uncle", "mother", "father"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, default=0)
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
    if args.vessel and args.drink and not reasonable_combo(VESSELS[args.vessel], DRINKS[args.drink]):
        raise StoryError("That vessel and drink do not make a safe, sensible hearth story.")
    combos = valid_combos()
    if args.drink:
        combos = [c for c in combos if c[0] == args.drink]
    if args.vessel:
        combos = [c for c in combos if c[1] == args.vessel]
    if args.hearth:
        combos = [c for c in combos if c[2] == args.hearth]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    drink, vessel, hearth = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    delay = args.delay
    return StoryParams(child_name, child_gender, parent_name, parent_gender, drink, vessel, hearth, delay)


CURATED = [
    StoryParams("June", "girl", "Ma", "mother", "electrolyte", "kettle", "oak", 0),
    StoryParams("Milo", "boy", "Pa", "father", "electrolyte", "stone_mug", "brick", 0),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show ok_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
