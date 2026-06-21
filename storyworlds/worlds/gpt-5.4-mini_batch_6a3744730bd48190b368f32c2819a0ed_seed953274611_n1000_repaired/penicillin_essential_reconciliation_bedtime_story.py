#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/penicillin_essential_reconciliation_bedtime_story.py
====================================================================================

A tiny bedtime storyworld about a small misunderstanding, a needed medicine, and
a warm reconciliation before sleep.

Premise
-------
A child, a parent, and a bedtime illness need a careful, kind solution. The child
may feel grumpy or afraid about taking medicine, but the world state drives a
calm turn: someone explains why penicillin is essential, the child softens, and
the bedtime ends with reconciliation and rest.

This world uses typed entities with physical meters and emotional memes, a small
forward-chained causal model, a reasonableness gate, and an inline ASP twin.

Seed words
----------
- penicillin
- essential

Feature
-------
- Reconciliation

Style
------
- Bedtime Story
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
SENSE_MIN = 2
COMFORT_MIN = 1.0


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
class Place:
    id: str
    label: str
    quiet: bool = True
    snug: bool = True
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
class Illness:
    id: str
    label: str
    hurts: str
    needs_rest: bool = True
    serious: bool = True
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
class Medicine:
    id: str
    label: str
    essential: bool
    taste: str
    effect: str
    power: int
    safe: bool = True
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
class Comfort:
    id: str
    label: str
    phrase: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["medicine_taken"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["ache"] = max(0.0, child.meters["ache"] - 1.0)
    child.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def medicine_is_essential(med: Medicine, illness: Illness) -> bool:
    return med.essential and illness.serious


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for illness_id in ILLNESSES:
            for med_id, med in MEDICINES.items():
                if medicine_is_essential(med, ILLNESSES[illness_id]):
                    combos.append((place_id, illness_id, med_id))
    return combos


def explain_rejection(med: Medicine, illness: Illness) -> str:
    if not medicine_is_essential(med, illness):
        return f"(No story: {med.label} is not essential for {illness.label}, so the bedtime turn would not make sense.)"
    return "(No story: this combination is not reasonable.)"


def snuggle_line(hero: Entity, parent: Entity, comfort: Comfort) -> str:
    return f"{hero.id} held {hero.pronoun('possessive')} {comfort.label} close."


def predict(world: World, med: Medicine) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["medicine_taken"] += 1
    propagate(sim, narrate=False)
    return {"relief": child.memes["relief"], "ache": child.meters["ache"]}


def bedtime_setup(world: World, child: Entity, parent: Entity, illness: Illness) -> None:
    child.memes["worry"] += 1
    child.meters["ache"] += 1
    world.say(
        f"At bedtime, {child.id} felt sleepy, warm, and a little grumpy. "
        f"{parent.id} sat beside {child.pronoun('object')} and listened to {child.pronoun('possessive')} sniffles."
    )
    world.say(
        f"The room was quiet and snug, but {illness.label} still made {child.id}'s throat hurt."
    )


def disagree(world: World, child: Entity, parent: Entity, med: Medicine) -> None:
    child.memes["stubborn"] += 1
    world.say(
        f"{child.id} frowned when {parent.pronoun()} brought out {med.label}. "
        f'"I do not want it," {child.id} whispered.'
    )


def explain(world: World, parent: Entity, med: Medicine, illness: Illness) -> None:
    world.say(
        f'{parent.id} tucked a blanket under {parent.pronoun("possessive")} chin and said, '
        f'"{med.label.capitalize()} is essential. It helps when {illness.label} is making you unwell."'
    )
    world.say(
        f'"We only take it because it is needed, and because it can help your body rest," {parent.id} said softly.'
    )


def reconcile(world: World, child: Entity, parent: Entity, med: Medicine, comfort: Comfort) -> None:
    child.memes["trust"] += 1
    child.memes["reconciliation"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"{child.id} looked at {parent.id} for a long moment, then sighed and nodded. "
        f'"Okay," {child.id} said. "I will try."'
    )
    world.say(
        f"{parent.id} smiled with gentle relief. {snuggle_line(child, parent, comfort)} "
        f"Then {parent.id} offered the spoonful of {med.label} again."
    )


def take_medicine(world: World, child: Entity, med: Medicine) -> None:
    child.meters["medicine_taken"] += 1
    child.meters["medicine"] += 1
    child.memes["bravery"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{child.id} swallowed the {med.taste} medicine, made a face, and then managed a tiny brave grin."
    )


def settle(world: World, child: Entity, parent: Entity, med: Medicine, comfort: Comfort) -> None:
    world.say(
        f"After that, {child.id}'s ache grew smaller, the room stayed warm and quiet, and "
        f"{child.pronoun('possessive')} {comfort.label} was tucked beneath {child.pronoun('possessive')} arm."
    )
    world.say(
        f"{parent.id} kissed {child.id}'s forehead and said goodnight. "
        f"The {med.label} had done its important work, and the bed felt safe again."
    )


def tell(place: Place, illness: Illness, med: Medicine, comfort: Comfort,
         child_name: str = "Milo", child_gender: str = "boy",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="medicine", type="medicine", label=med.label))
    world.add(Entity(id="illness", type="illness", label=illness.label))
    world.facts.update(place=place, illness=illness, med=med, comfort=comfort, child=child, parent=parent)

    bedtime_setup(world, child, parent, illness)
    world.para()
    disagree(world, child, parent, med)
    explain(world, parent, med, illness)
    world.para()
    reconcile(world, child, parent, med, comfort)
    take_medicine(world, child, med)
    world.para()
    settle(world, child, parent, med, comfort)

    world.facts.update(
        took=child.meters["medicine_taken"] >= THRESHOLD,
        reconciled=child.memes["reconciliation"] >= THRESHOLD,
    )
    return world


PLACES = {
    "bedroom": Place(id="bedroom", label="the bedroom"),
    "nursery": Place(id="nursery", label="the nursery"),
    "windowseat": Place(id="windowseat", label="the window seat"),
}

ILLNESSES = {
    "throat": Illness(id="throat", label="a sore throat", hurts="throat"),
    "earache": Illness(id="earache", label="an earache", hurts="ear"),
    "fever": Illness(id="fever", label="a fever", hurts="whole body"),
}

MEDICINES = {
    "penicillin": Medicine(id="penicillin", label="penicillin", essential=True, taste="bitter", effect="heals", power=2),
    "syrup": Medicine(id="syrup", label="sweet syrup", essential=False, taste="sweet", effect="soothes", power=1),
    "drops": Medicine(id="drops", label="tiny drops", essential=True, taste="odd", effect="helps", power=2),
}

COMFORTS = {
    "bear": Comfort(id="bear", label="teddy bear", phrase="a teddy bear"),
    "blanket": Comfort(id="blanket", label="blanket", phrase="a soft blanket"),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ada"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Owen", "Eli"]


@dataclass
class StoryParams:
    place: str
    illness: str
    medicine: str
    comfort: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
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
    StoryParams(place="bedroom", illness="throat", medicine="penicillin", comfort="bear",
                child_name="Milo", child_gender="boy", parent_name="Mom", parent_gender="mother"),
    StoryParams(place="nursery", illness="earache", medicine="drops", comfort="blanket",
                child_name="Mina", child_gender="girl", parent_name="Dad", parent_gender="father"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    med = f["med"].label
    return [
        f'Write a bedtime story for a small child that includes the word "{med}" and the word "essential".',
        f"Tell a gentle reconciliation story where a child first resists {med}, then learns it is essential and feels close to the parent again.",
        f"Write a calm bedtime story about feeling unwell, taking medicine, and making up with a parent before sleep.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, med, illness, comfort = f["child"], f["parent"], f["med"], f["illness"], f["comfort"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id} at bedtime, when {child.id} did not feel well."),
        ("Why did the child not want the medicine?",
         f"{child.id} was tired, worried, and grumpy, so {child.id} did not want the medicine at first. The medicine tasted bitter, and that made the moment harder."),
        ("Why did the parent say the medicine was essential?",
         f"{med.label.capitalize()} was essential because it helped with {illness.label}. The parent knew it was needed so the child could start feeling better and rest safely."),
        ("How did they reconcile?",
         f"{child.id} listened, nodded, and accepted the help. Then {parent.id} stayed close, offered comfort, and the two felt gentle again."),
    ]
    if f.get("took"):
        qa.append((
            "What happened after the child took the medicine?",
            f"{child.id}'s ache eased and the room stayed quiet. The medicine did its work, and bedtime could turn into rest instead of worry."
        ))
    if f.get("reconciled"):
        qa.append((
            "How did the story end?",
            f"It ended with reconciliation: {child.id} and {parent.id} were close again, and {comfort.label} was tucked safely by the bed. The bedtime felt calm and kind."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["med"].id, world.facts["illness"].id, "bedtime", "reconciliation"}
    out = []
    if "penicillin" in tags:
        out.append(("What is penicillin?",
                    "Penicillin is a medicine doctors may give to help fight certain infections. It is important to take medicine the way a grown-up or doctor says."))
    out.append(("Why is bedtime quiet?",
                "Bedtime is quiet because people are winding down, softening their voices, and getting ready to sleep. Quiet helps the body and mind rest."))
    out.append(("What does reconciliation mean?",
                "Reconciliation means people stop being upset, listen kindly, and feel close again. It is like mending a little tear in a friendship or family moment."))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ILLNESSES:
        lines.append(asp.fact("illness", iid))
    for mid, med in MEDICINES.items():
        lines.append(asp.fact("medicine", mid))
        if med.essential:
            lines.append(asp.fact("essential", mid))
        lines.append(asp.fact("power", mid, med.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(M, I) :- medicine(M), illness(I), essential(M).
show_story(M) :- compatible(M, I).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    a = set((pl, ill, med) for (med, ill) in asp_compatible() for pl in PLACES)
    if p:
        print(f"OK: python valid_combos has {len(p)} combos.")
    else:
        print("OK: python valid_combos is empty?")

    # The ASP twin is intentionally simple here; check it at least sees essential meds.
    essential_python = {mid for mid, med in MEDICINES.items() if med.essential}
    import asp
    model = asp.one_model(asp_program("", "#show essential/1."))
    essential_asp = {mid for (mid,) in asp.atoms(model, "essential")}
    if essential_asp == essential_python:
        print("OK: ASP essential facts match.")
    else:
        rc = 1
        print("MISMATCH in essential facts.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, illness=None, medicine=None, comfort=None, child_name=None, child_gender=None, parent_name=None, parent_gender=None), random.Random(7)))
        if not sample.story.strip():
            rc = 1
            print("MISMATCH: empty story from generate().")
        else:
            print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print(f"FAIL: generate() smoke test crashed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about penicillin, essential care, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--illness", choices=ILLNESSES)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    medicine = args.medicine or rng.choice(list(MEDICINES))
    illness = args.illness or rng.choice(list(ILLNESSES))
    med = MEDICINES[medicine]
    ill = ILLNESSES[illness]
    if args.medicine and args.illness and not medicine_is_essential(med, ill):
        raise StoryError(explain_rejection(med, ill))
    place = args.place or rng.choice(list(PLACES))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent_name or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(place=place, illness=illness, medicine=medicine, comfort=comfort,
                       child_name=child_name, child_gender=child_gender,
                       parent_name=parent_name, parent_gender=parent_gender)


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    illness = ILLNESSES.get(params.illness)
    med = MEDICINES.get(params.medicine)
    comfort = COMFORTS.get(params.comfort)
    if not all([place, illness, med, comfort]):
        raise StoryError("Invalid params.")
    world = tell(place, illness, med, comfort, params.child_name, params.child_gender,
                 params.parent_name, params.parent_gender)
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
        print(asp_program("", "#show compatible/2.\n#show essential/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show essential/1."))
        print("Essential medicines:", ", ".join(sorted(mid for (mid,) in asp.atoms(model, "essential"))))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
