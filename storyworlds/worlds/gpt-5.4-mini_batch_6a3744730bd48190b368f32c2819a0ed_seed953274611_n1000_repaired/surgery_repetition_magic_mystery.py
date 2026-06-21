#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/surgery_repetition_magic_mystery.py
====================================================================

A small storyworld for a child's mystery about a repeated clue, a tiny bit of
magic, and a surgery that solves the problem.

Premise:
- A child notices the same odd sign again and again.
- A helper with a gentle magic trick makes a hidden pattern visible.
- The mystery leads to a surgery, and the story ends with the repaired thing
  working again.

The world is deliberately compact:
- typed entities with physical meters and emotional memes
- forward-chained state changes
- reasonableness gates for valid story combinations
- inline ASP twin for parity checks
- three QA sets grounded in the simulated world
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
MAGIC_MIN = 1
SURGERY_RISK_MIN = 1.0


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse", "doctor"}
        male = {"boy", "father", "dad", "man", "doctor"}
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


@dataclass
class Place:
    id: str
    label: str
    dim: str
    mystery: str
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
class MysteryClue:
    id: str
    label: str
    repetition: str
    reveal: str
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
class MagicAid:
    id: str
    label: str
    trick: str
    effect: str
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
class SurgeryPlan:
    id: str
    label: str
    repair: str
    risk: float
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
        c.facts = copy.deepcopy(self.facts)
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for clue in list(world.entities.values()):
        if clue.kind != "clue":
            continue
        if clue.meters["seen"] < THRESHOLD:
            continue
        sig = ("repeat", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        clue.memes["unease"] += 1
        out.append("__repeat__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for aid in list(world.entities.values()):
        if aid.kind != "magic":
            continue
        if aid.meters["used"] < THRESHOLD:
            continue
        sig = ("magic", aid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        target = world.get("patient")
        target.meters["revealed"] += 1
        out.append("__magic__")
    return out


def _r_surgery(world: World) -> list[str]:
    patient = world.entities.get("patient")
    doctor = world.entities.get("doctor")
    if not patient or not doctor:
        return []
    if patient.meters["revealed"] < THRESHOLD:
        return []
    if patient.meters["fixed"] >= THRESHOLD:
        return []
    sig = ("surgery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patient.meters["fixed"] += 1
    patient.memes["relief"] += 2
    doctor.memes["focus"] += 1
    return ["__surgery__"]


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("magic", _r_magic), Rule("surgery", _r_surgery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_ok(place: Place, clue: MysteryClue, magic: MagicAid, plan: SurgeryPlan) -> bool:
    return "medical" in place.tags and "repeatable" in clue.tags and "magic" in magic.tags and plan.risk >= SURGERY_RISK_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for mid, magic in MAGIC.items():
                for sid, plan in SURGERY.items():
                    if reasonableness_ok(place, clue, magic, plan):
                        combos.append((pid, cid, mid, sid))
    return combos


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["seen"] += 1
    sim.get("magic").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "revealed": sim.get("patient").meters["revealed"],
        "fixed": sim.get("patient").meters["fixed"],
    }


def _setup(world: World, child: Entity, helper: Entity, doctor: Entity, place: Place, clue: MysteryClue, magic: MagicAid, plan: SurgeryPlan) -> None:
    world.say(
        f"{child.id} and {helper.id} went to {place.label}, where a little mystery hung in the air. "
        f"Every day, the same clue came back: {clue.repetition}"
    )
    world.say(
        f"{child.id} kept noticing it, and each time the feeling grew stranger, as if the clue wanted to be seen again."
    )
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    doctor.memes["steady"] += 1
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["magic"] = magic
    world.facts["plan"] = plan
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["doctor"] = doctor


def _nudge(world: World, child: Entity, helper: Entity, clue: MysteryClue, magic: MagicAid) -> None:
    world.say(
        f'"That same thing again?" {child.id} whispered. {helper.id} nodded and lifted {magic.label}, '
        f"using {magic.trick}."
    )
    world.say(
        f"The little trick made the hidden detail shine, and at last the puzzle could be read clearly: {clue.reveal}"
    )
    world.get("clue").meters["seen"] += 1
    world.get("magic").meters["used"] += 1
    propagate(world)


def _surgery_scene(world: World, doctor: Entity, plan: SurgeryPlan) -> None:
    patient = world.get("patient")
    world.para()
    world.say(
        f'{doctor.id} checked the problem twice, then led the careful surgery. '
        f"{plan.repair}."
    )
    if patient.meters["fixed"] >= THRESHOLD:
        world.say(
            f"The patient grew quiet and safe. After the surgery, the strange sign was gone, and the place felt whole again."
        )
    else:
        world.say(
            f"The doctor worked carefully, but the mystery was still too deep. The clues were not enough yet."
        )


def tell(place: Place, clue: MysteryClue, magic: MagicAid, plan: SurgeryPlan,
         child_name: str = "Mina", helper_name: str = "Ivo", doctor_name: str = "Dr. Vale") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy", role="helper"))
    doctor = world.add(Entity(id=doctor_name, kind="character", type="doctor", role="doctor"))
    patient = world.add(Entity(id="patient", kind="patient", type="thing", label="the patient"))
    world.add(Entity(id="clue", kind="clue", type="thing", label=clue.label, tags=set(clue.tags)))
    world.add(Entity(id="magic", kind="magic", type="thing", label=magic.label, tags=set(magic.tags)))
    world.facts["patient"] = patient

    _setup(world, child, helper, doctor, place, clue, magic, plan)
    world.para()
    _nudge(world, child, helper, clue, magic)
    _surgery_scene(world, doctor, plan)
    world.facts["outcome"] = "fixed" if patient.meters["fixed"] >= THRESHOLD else "unsolved"
    world.facts["resolved"] = patient.meters["fixed"] >= THRESHOLD
    return world


PLACES = {
    "clinic": Place(id="clinic", label="the clinic", dim="white hall", mystery="quiet hallway", tags={"medical"}),
    "ward": Place(id="ward", label="the ward", dim="soft room", mystery="silent room", tags={"medical"}),
}

CLUES = {
    "echo": MysteryClue(id="echo", label="the echo clue", repetition="the same soft tap, tap, tap", reveal="the sound came from behind the curtain", tags={"repeatable"}),
    "note": MysteryClue(id="note", label="the folded note", repetition="the same note, left twice on the table", reveal="the note pointed to the hidden room", tags={"repeatable"}),
}

MAGIC = {
    "lantern": MagicAid(id="lantern", label="a glow lantern", trick="a tiny magic shine", effect="show hidden marks", tags={"magic"}),
    "chalk": MagicAid(id="chalk", label="silver chalk", trick="one magical circle", effect="show hidden marks", tags={"magic"}),
}

SURGERY = {
    "repair": SurgeryPlan(id="repair", label="repair plan", repair="The doctor fixed the tiny problem with steady hands and a neat stitch", risk=1.0, tags={"surgery"}),
    "check": SurgeryPlan(id="check", label="check plan", repair="The doctor found the bad spot and mended it before it could bother the patient again", risk=2.0, tags={"surgery"}),
}

GIRL_NAMES = ["Mina", "Tess", "Nora", "Lia", "Ada"]
BOY_NAMES = ["Ivo", "Noel", "Jules", "Oren", "Paz"]


@dataclass
class StoryParams:
    place: str
    clue: str
    magic: str
    surgery: str
    child_name: str
    helper_name: str
    doctor_name: str
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


def _pick_name(rng: random.Random, names: list[str], avoid: str = "") -> str:
    pool = [n for n in names if n != avoid]
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with repetition, magic, and surgery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--surgery", choices=SURGERY)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--doctor-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.magic is None or c[2] == args.magic)
              and (args.surgery is None or c[3] == args.surgery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, magic, surgery = rng.choice(sorted(combos))
    child = args.child_name or _pick_name(rng, GIRL_NAMES)
    helper = args.helper_name or _pick_name(rng, BOY_NAMES)
    doctor = args.doctor_name or "Dr. Vale"
    return StoryParams(place=place, clue=clue, magic=magic, surgery=surgery, child_name=child, helper_name=helper, doctor_name=doctor)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.magic not in MAGIC or params.surgery not in SURGERY:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], CLUES[params.clue], MAGIC[params.magic], SURGERY[params.surgery],
                 child_name=params.child_name, helper_name=params.helper_name, doctor_name=params.doctor_name)
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
        f'Write a child-friendly mystery story that includes the word "{f["clue"].label}" and the word surgery.',
        f"Tell a story where {f['child'].id} keeps seeing the same clue, {f['helper'].id} uses a little magic to reveal it, and Dr. Vale does surgery.",
        f"Write a gentle mystery where repetition matters, magic reveals the hidden pattern, and surgery fixes the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    patient = f["patient"]
    clue = f["clue"]
    magic = f["magic"]
    doctor = f["doctor"]
    child = f["child"]
    helper = f["helper"]
    ans = [
        ("What was the mystery about?",
         f"It was about the same clue showing up again and again, which made {child.id} wonder what it meant. The repeated sign pointed the children toward the hidden problem."),
        ("What did the magic do?",
         f"{helper.id} used {magic.label} to make the hidden detail easy to see. That mattered because the clue had to be revealed before the surgery could make sense."),
        ("What happened during the surgery?",
         f"{doctor.id} did the surgery carefully and repaired the patient. After that, the strange problem was gone and the story could end safely."),
    ]
    if f.get("resolved"):
        ans.append(("How did the story end?",
                    f"It ended with the patient fixed and the mystery solved. The repeated clue had turned into a clear answer, and the magic helped lead the way."))
    else:
        ans.append(("How did the story end?",
                    f"It ended with the mystery still open, so the surgery was not enough yet. The child would need more clues next."))
    return ans


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is surgery?",
         "Surgery is a medical operation where a doctor carefully fixes a problem inside or on the body. It is done with attention and clean tools."),
        ("Why can repetition matter in a mystery?",
         "When the same clue repeats, it can show that the clue is important. Repetition helps you notice a pattern that you might miss the first time."),
        ("What is magic in a story?",
         "Magic in a story is something special that cannot happen in ordinary life. It can reveal hidden things, but it still has to fit the story's world."),
    ]
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(P,C,M,S) :- place(P), clue(C), magic(M), surgery(S), medical(P), repeatable(C), magic_kind(M), surgery_risk(S,R), R >= 1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "medical" in p.tags:
            lines.append(asp.fact("medical", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if "repeatable" in c.tags:
            lines.append(asp.fact("repeatable", cid))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic_kind", mid))
    for sid, s in SURGERY.items():
        lines.append(asp.fact("surgery", sid))
        lines.append(asp.fact("surgery_risk", sid, int(s.risk)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, magic=None, surgery=None, child_name=None, helper_name=None, doctor_name=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generate smoke test passed.")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _all_samples() -> list[StoryParams]:
    out = []
    for combo in valid_combos():
        out.append(StoryParams(place=combo[0], clue=combo[1], magic=combo[2], surgery=combo[3], child_name="Mina", helper_name="Ivo", doctor_name="Dr. Vale"))
    return out[:4]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in _all_samples()]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
