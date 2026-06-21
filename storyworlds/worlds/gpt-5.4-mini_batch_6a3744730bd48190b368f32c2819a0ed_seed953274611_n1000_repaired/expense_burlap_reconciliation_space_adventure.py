#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/expense_burlap_reconciliation_space_adventure.py
=================================================================================

A standalone story world for a small Space-Adventure-style reconciliation tale:
two young shipmates haul a precious burlap cargo through a cramped starship,
make an expensive mistake, and then repair both the bundle and their friendship.

Core idea
---------
- Space-adventure setting: a little ship, a moon stop, a glowing station, a cargo
  run, a star map, and a return flight.
- Required seed words: "expense" and "burlap".
- Required feature: reconciliation.
- Simulation-driven prose: the cargo can spill, the crew can argue, a helper can
  fix the mess, and the ending image proves that the friendship changed.

The world is intentionally small and classical:
- typed entities
- physical meters and emotional memes
- forward-chained causal rules
- Python gate + inline ASP twin
- prompts / story QA / world knowledge QA built from world state
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
RECONCILE_MIN = 1.0
SPILL_MIN = 1.0


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
    is_brittle: bool = False
    is_tool: bool = False
    is_burlap: bool = False
    is_repair_gear: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
class StoryParams:
    ship: str
    port: str
    cargo: str
    cargo_label: str
    problem: str
    fix: str
    lead: str
    lead_gender: str
    partner: str
    partner_gender: str
    captain: str
    captain_gender: str
    trait: str
    delay: int = 0
    lead_age: int = 7
    partner_age: int = 7
    relation: str = "crew"
    expense_level: int = 2
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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    exit_image: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    fragile: bool
    spill_name: str
    value: int
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
    prompt: str
    mistake: str
    consequence: str
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
    sense: int
    power: int
    text: str
    fail: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["open"] < SPILL_MIN:
        return out
    sig = ("spill", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["spilled"] += 1
    world.get("deck").meters["mess"] += 1
    for e in world.characters():
        e.memes["stress"] += 1
    out.append("__spill__")
    return out


def _r_resentment(world: World) -> list[str]:
    out: list[str] = []
    if world.get("crew_a").memes["hurt"] < THRESHOLD:
        return out
    sig = ("hurt", "crew_a")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("crew_b").memes["guilt"] += 1
    out.append("")
    return out


def _r_reconcile(world: World) -> list[str]:
    a, b = world.get("crew_a"), world.get("crew_b")
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    if a.memes["hurt"] >= THRESHOLD and b.memes["guilt"] >= THRESHOLD:
        world.fired.add(sig)
        a.memes["peace"] += 1
        b.memes["peace"] += 1
        return ["__reconcile__"]
    return []


CAUSAL_RULES = [
    Rule("spill", "physical", _r_spill),
    Rule("resentment", "social", _r_resentment),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def expense_cost(problem: Problem, cargo: Cargo, delay: int) -> int:
    return problem.value + cargo.value + delay


def is_reasonable_fix(fix: Fix, problem: Problem, cargo: Cargo, delay: int) -> bool:
    return fix.sense >= SENSE_MIN and fix.power >= expense_cost(problem, cargo, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            for cid, cargo in CARGOS.items():
                if cargo.fragile and is_reasonable_fix(FIXES["patch"], prob, cargo, 0):
                    combos.append((sid, pid, cid))
    return combos


def predict_spill(world: World, cargo_id: str) -> dict:
    sim = world.copy()
    sim.get(cargo_id).meters["open"] += 1
    propagate(sim, narrate=False)
    return {
        "spilled": sim.get(cargo_id).meters["spilled"] >= THRESHOLD,
        "mess": sim.get("deck").meters["mess"],
    }


def intro(world: World, lead: Entity, partner: Entity, setting: Setting) -> None:
    world.say(
        f"On a quiet stretch of black sky, {lead.id} and {partner.id} drifted "
        f"through {setting.place}. {setting.scene}"
    )
    world.say(
        f"They were carrying a {CARGOS['seeds'].phrase} wrapped in {CARGOS['seeds'].label}."
    )


def want_help(world: World, lead: Entity, partner: Entity, problem: Problem) -> None:
    world.say(
        f'{partner.id} peered at the bundle and said, "We need to solve the {problem.id} '
        f'before the station docking fee turns into an {problem.id}."'
    )


def mistake(world: World, lead: Entity, problem: Problem, cargo: Cargo) -> None:
    lead.memes["impulse"] += 1
    world.say(
        f'{lead.id} saw a quick way and reached for the latch. '
        f'"I can fix it fast," {lead.id} said, but the {cargo.label} was not meant for a hurry.'
    )
    world.say(
        f"The {problem.prompt} tempted {lead.id} to be careless, and the old {cargo.label} shifted."
    )


def open_cargo(world: World, cargo: Entity) -> None:
    cargo.meters["open"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {cargo.label} flap came loose, and the burlap split with a soft tear."
    )


def warn(world: World, partner: Entity, lead: Entity, problem: Problem, cargo: Cargo) -> None:
    pred = predict_spill(world, "cargo")
    partner.memes["concern"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{partner.id} grabbed {lead.pronoun("possessive")} sleeve. '
        f'"Wait," {partner.id} said. "That would be an {problem.id}, and it would cost us too much to lose the cargo."'
    )


def spill(world: World, cargo: Entity, problem: Problem) -> None:
    world.say(
        f"{problem.mistake} The bundle burst open, and tiny moon-seeds sprinkled across the deck."
    )
    cargo.meters["spilled"] += 1


def alarm(world: World, captain: Entity) -> None:
    world.say(f'"{captain.id}!" both shipmates called. "We need help in the cargo bay!"')


def repair(world: World, captain: Entity, fix: Fix, cargo: Cargo, problem: Problem) -> None:
    body = fix.text
    world.say(
        f"{captain.label_word.capitalize()} came at once and {body}."
    )
    world.say(
        f"The ship steadied. The {cargo.label} was safe again, and the {problem.consequence} was finally over."
    )


def reconcile(world: World, lead: Entity, partner: Entity, captain: Entity) -> None:
    lead.memes["hurt"] += 1
    partner.memes["guilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For a moment, {lead.id} stared at the deck in silence. Then {partner.id} said, "
        f'"I was scared too. I am sorry."'
    )
    world.say(
        f"{lead.id} looked up, still embarrassed, but {lead.id} nodded. "
        f'"I should have listened," {lead.id} said. "Let\'s make it right."'
    )
    world.say(
        f"{captain.id} smiled at both of them. " + '"That is how a crew mends things."'
    )


def ending(world: World, lead: Entity, partner: Entity, setting: Setting, cargo: Cargo) -> None:
    lead.memes["peace"] += 1
    partner.memes["peace"] += 1
    world.say(
        f"They used a fresh strip of burlap and a neat knot, then sat shoulder to shoulder at the window."
    )
    world.say(
        f"Below them, {setting.exit_image}, and the repaired bundle glowed beside the map."
    )


def tell(setting: Setting, cargo: Cargo, problem: Problem, fix: Fix,
         lead_name: str = "Mira", lead_gender: str = "girl",
         partner_name: str = "Jae", partner_gender: str = "boy",
         captain_name: str = "Captain Sol", captain_gender: str = "captain",
         trait: str = "careful", delay: int = 0,
         lead_age: int = 7, partner_age: int = 7, relation: str = "crew",
         expense_level: int = 2) -> World:
    world = World()
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead", traits=[trait], attrs={"relation": relation}))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner", traits=["steady"], attrs={"relation": relation}))
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain", label="the captain"))
    deck = world.add(Entity(id="deck", type="deck", label="the deck"))
    burlap = world.add(Entity(id="cargo", type="cargo", label="burlap", is_burlap=True))
    intro(world, lead, partner, setting)
    world.para()
    want_help(world, lead, partner, problem)
    mistake(world, lead, problem, cargo)
    warn(world, partner, lead, problem, cargo)
    open_cargo(world, burlap)
    spill(world, burlap, problem)
    alarm(world, captain)
    world.para()
    repair(world, captain, fix, cargo, problem)
    lead.memes["hurt"] += 1
    reconcile(world, lead, partner, captain)
    world.para()
    ending(world, lead, partner, setting, cargo)
    world.facts.update(
        lead=lead, partner=partner, captain=captain, setting=setting, cargo=cargo,
        problem=problem, fix=fix, spilled=burlap.meters["spilled"] >= THRESHOLD,
        reconciled=lead.memes["peace"] >= THRESHOLD and partner.memes["peace"] >= THRESHOLD,
        delay=delay, expense_level=expense_level, outcome="reconciled",
    )
    return world


SETTINGS = {
    "orbit": Setting(id="orbit", place="a small repair ship in orbit", scene="The cabin windows showed a ring of stars, and the engine hummed like a sleepy bee.", exit_image="the station lights shone like tiny pearls"),
    "moonport": Setting(id="moonport", place="the moonport cargo bay", scene="A silver hatch blinked open and closed while distant cranes moved slow as turtles.", exit_image="the moon dust sparkled outside the airlock"),
    "asteroid": Setting(id="asteroid", place="a station beside the asteroid dock", scene="Outside, the rock glittered with frost, and the docking clamps held tight.", exit_image="the asteroid field drifted by like a handful of dark marbles"),
}

CARGOS = {
    "seeds": Cargo(id="seeds", label="burlap", phrase="burlap seed-sack", fragile=True, spill_name="moon-seeds", value=1, tags={"burlap"}),
    "maps": Cargo(id="maps", label="burlap", phrase="burlap map-bundle", fragile=True, spill_name="star-maps", value=2, tags={"burlap"}),
}

PROBLEMS = {
    "expense": Problem(id="expense", prompt="expense note", mistake="The expense was bigger than they expected.", consequence="the repair fee had climbed", tags={"expense"}),
    "tear": Problem(id="tear", prompt="tear in the seam", mistake="The seam had a tiny tear already.", consequence="the cargo needed patching", tags={"expense"}),
}

FIXES = {
    "patch": Fix(id="patch", sense=3, power=4, text="patched the split with a careful stitch and a clean clip", fail="patched the wrong seam and only made the tear wider", qa_text="patched the split with a careful stitch and a clean clip", tags={"burlap"}),
    "wrap": Fix(id="wrap", sense=2, power=3, text="wrapped the bundle tight with a second layer of burlap and tied it off", fail="wrapped it too loosely, so the seeds still slipped out", qa_text="wrapped the bundle tight with a second layer of burlap and tied it off", tags={"burlap"}),
}

TRAITS = ["careful", "steady", "curious", "patient"]
GIRL_NAMES = ["Mira", "Nova", "Luna", "Ari", "Zia"]
BOY_NAMES = ["Jae", "Pax", "Theo", "Rin", "Sol"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure reconciliation story world with expense and burlap.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--lead")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", default="Captain Sol")
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


def explain_rejection(problem: Problem, cargo: Cargo) -> str:
    return f"(No story: the {problem.id} story needs a fragile burlap cargo that can actually spill.)"


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < 2:
        raise StoryError("That fix is too weak for a believable reconciliation story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.cargo is None or c[2] == args.cargo)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, pid, cid = rng.choice(sorted(combos))
    setting, problem, cargo = SETTINGS[sid], PROBLEMS[pid], CARGOS[cid]
    fix = args.fix or rng.choice([f.id for f in sensible_fixes()])
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if lead_gender == "girl" else "girl")
    lead = args.lead or rng.choice(GIRL_NAMES if lead_gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice([n for n in (GIRL_NAMES if partner_gender == "girl" else BOY_NAMES) if n != lead])
    return StoryParams(
        ship=setting.place, port=setting.id, cargo=cid, cargo_label=cargo.label,
        problem=pid, fix=fix, lead=lead, lead_gender=lead_gender,
        partner=partner, partner_gender=partner_gender,
        captain=args.captain, captain_gender="captain", trait=args.trait or rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure for a 3-to-5-year-old that includes the words "expense" and "burlap".',
        f"Tell a reconciliation story where {f['lead'].id} and {f['partner'].id} haul a burlap cargo through {f['setting'].place} and fix an expense mistake together.",
        "Write a small, child-facing starship story where an argument gets repaired as carefully as the cargo.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead, partner, captain = f["lead"], f["partner"], f["captain"]
    cargo, problem, fix = f["cargo"], f["problem"], f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {lead.id} and {partner.id} on a small ship, with {captain.id} helping after the trouble. The story follows how their work and feelings change together."),
        ("Why was the cargo a problem?",
         f"The cargo was wrapped in burlap and the bundle was fragile, so one quick mistake opened it. That made the expense worse because the crew had to repair both the cargo and the mess."),
        ("How did the two shipmates make up?",
         f"They apologized, listened, and then fixed the burlap bundle together. By the end they were sitting side by side, which shows they had reconciled."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is burlap?",
         "Burlap is a rough cloth that is often used for sacks and bundles. It is sturdy, but a careless tug can tear it."),
        ("What does expense mean?",
         "Expense means something costs money or takes effort and resources. A bigger expense can make a job harder to finish."),
        ("What is reconciliation?",
         "Reconciliation is when people stop arguing, apologize, and make peace again. It often happens after both sides listen and try to fix what went wrong."),
        ("What kind of story is this?",
         "It is a space adventure with a gentle friendship problem and a happy repair. The ship, the cargo, and the stars all help the story feel small and exciting."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(ship="a small repair ship in orbit", port="orbit", cargo="seeds", cargo_label="burlap", problem="expense", fix="patch",
                lead="Mira", lead_gender="girl", partner="Jae", partner_gender="boy",
                captain="Captain Sol", captain_gender="captain", trait="careful"),
    StoryParams(ship="the moonport cargo bay", port="moonport", cargo="maps", cargo_label="burlap", problem="tear", fix="wrap",
                lead="Nova", lead_gender="girl", partner="Pax", partner_gender="boy",
                captain="Captain Sol", captain_gender="captain", trait="patient"),
]


def valid_story(params: StoryParams) -> bool:
    if params.cargo not in CARGOS or params.problem not in PROBLEMS or params.fix not in FIXES:
        return False
    return is_reasonable_fix(FIXES[params.fix], PROBLEMS[params.problem], CARGOS[params.cargo], params.delay)


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOS or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    if not valid_story(params):
        raise StoryError("The chosen fix cannot reasonably solve the cargo problem.")
    setting = next(v for v in SETTINGS.values() if v.place == params.ship or v.id == params.port)
    world = tell(setting, CARGOS[params.cargo], PROBLEMS[params.problem], FIXES[params.fix],
                 params.lead, params.lead_gender, params.partner, params.partner_gender,
                 params.captain, params.captain_gender, params.trait, params.delay,
                 params.lead_age, params.partner_age, params.relation, params.expense_level)
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


ASP_RULES = r"""
reasonably_valid(S,P,C) :- setting(S), problem(P), cargo(C), fragile(C), fix(F), sense(F,SN), sense_min(M), SN >= M.
reconciled :- hurt, guilt.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        if c.fragile:
            lines.append(asp.fact("fragile", cid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", 2))
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
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: generate smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure reconciliation story world with expense and burlap.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--lead")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", default="Captain Sol")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonably_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show reasonably_valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
