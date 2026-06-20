#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reversible_assistant_penicillin_flashback_moral_value_heartwarming.py
======================================================================================================

A tiny heartwarming storyworld about a child, a helpful assistant, a reversible
coat, and penicillin at a small clinic.

The model keeps the story grounded in simulated state:
- a child arrives worried about a pet or helper animal,
- a clinic assistant explains the plan and fetches penicillin,
- a flashback reminder shows why the child already knows the moral value of
  following care instructions,
- the ending proves what changed by showing calm, comfort, and recovery.

The world is intentionally small and child-facing. It generates a complete
beginning-middle-end story, plus three Q&A sets derived from the simulated
state rather than by parsing rendered prose.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man", "doctor", "assistant"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Setting:
    id: str
    place: str
    mood: str


@dataclass
class Case:
    id: str
    label: str
    reversible: bool
    phrase: str
    comfort: str


@dataclass
class Medicine:
    id: str
    label: str
    use_line: str
    caution: str
    help_line: str
    safe: bool = True


@dataclass
class StoryParams:
    setting: str
    case: str
    medicine: str
    child_name: str
    child_gender: str
    assistant_name: str
    assistant_gender: str
    parent_name: str
    parent_gender: str
    patient_name: str
    patient_kind: str
    seed: Optional[int] = None


SETTINGS = {
    "clinic": Setting("clinic", "a small clinic", "bright and gentle"),
    "home_visit": Setting("home_visit", "a cozy living room", "soft and calm"),
}

CASES = {
    "jacket": Case("jacket", "reversible jacket", True, "a red-and-blue reversible jacket", "soft and warm"),
    "blanket": Case("blanket", "reversible blanket", True, "a reversible blanket with stars on one side", "snug and safe"),
    "bag": Case("bag", "reversible bag", True, "a little reversible bag", "light and tidy"),
}

MEDICINES = {
    "penicillin": Medicine(
        "penicillin",
        "penicillin",
        "told them the medicine would help the fever go down",
        "reminded them that medicine must be taken exactly as the doctor says",
        "poured the measured penicillin into a little cup and handed it over",
    ),
    "syrup": Medicine(
        "syrup",
        "cough syrup",
        "said the syrup would soothe the cough",
        "reminded them to sip it slowly and only the right amount",
        "measured the syrup carefully and held the cup steady",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Noah", "Ben", "Leo", "Eli", "Theo", "Max", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CASES:
            for m in MEDICINES:
                combos.append((s, c, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming clinic storyworld with a reversible item, an assistant, and penicillin."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--assistant")
    ap.add_argument("--assistant-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["girl", "boy"])
    ap.add_argument("--patient")
    ap.add_argument("--patient-kind", choices=["bunny", "puppy", "kitten"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.case is None or c[1] == args.case)
              and (args.medicine is None or c[2] == args.medicine)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case, medicine = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    assistant_gender = args.assistant_gender or "girl"
    assistant_name = args.assistant or ("Nia" if assistant_gender == "girl" else "Owen")
    parent_gender = args.parent_gender or "girl"
    parent_name = args.parent or ("Mom" if parent_gender == "girl" else "Dad")
    patient_kind = args.patient_kind or rng.choice(["bunny", "puppy", "kitten"])
    patient = args.patient or ("Milo" if patient_kind == "bunny" else "Pip")
    return StoryParams(setting, case, medicine, child_name, gender, assistant_name,
                       assistant_gender, parent_name, parent_gender, patient, patient_kind)


def reasonableness_gate(params: StoryParams) -> None:
    if params.medicine not in MEDICINES:
        raise StoryError("Unknown medicine.")
    if params.case not in CASES:
        raise StoryError("Unknown case.")
    if not CASES[params.case].reversible:
        raise StoryError("This world expects a reversible comfort item.")


ASP_RULES = r"""
valid(S,C,M) :- setting(S), case(C), medicine(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        if c.reversible:
            lines.append(asp.fact("reversible", cid))
    for mid in MEDICINES:
        lines.append(asp.fact("medicine", mid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    from results import StorySample as _StorySample  # eager-ish smoke use
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: ASP parity verified.")
    return 0


def _story_state(world: World, child: Entity, assistant: Entity, parent: Entity, patient: Entity, case: Case, medicine: Medicine) -> None:
    child.memes["worry"] += 2
    assistant.memes["calm"] += 2
    parent.memes["care"] += 2
    patient.meters["fever"] += 1
    world.say(
        f"On a bright morning, {child.id} came to {SETTINGS[world.facts['setting']].place} with "
        f"{parent.id} and {patient.id}. {child.id} wore {case.phrase}, and it felt "
        f"{case.comfort} against {child.pronoun('possessive')} arms."
    )
    world.say(
        f"{assistant.id}, the assistant, smiled kindly and said that {medicine.label} could help {patient.id} feel better."
    )


def _flashback(world: World, child: Entity, parent: Entity, medicine: Medicine) -> None:
    child.memes["memory"] += 1
    world.say(
        f"That reminded {child.id} of an older day, when {parent.id} had paused beside the kitchen table and explained a small truth: "
        f"{medicine.caution}. {child.id} had listened then, and the lesson stayed tucked safely in {child.pronoun('possessive')} heart."
    )


def _assistant_action(world: World, assistant: Entity, parent: Entity, medicine: Medicine, patient: Entity) -> None:
    patient.meters["medicine"] += 1
    patient.meters["fever"] = max(0.0, patient.meters["fever"] - 1.0)
    world.say(
        f"{assistant.id} carefully {medicine.help_line} while {parent.id} held {patient.id} close and stroked {patient.id}'s ears."
    )


def _moral_value(world: World, child: Entity, parent: Entity) -> None:
    child.memes["kindness"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} learned the moral value of that quiet room: when someone is sick, listening and helping are kinder than rushing or guessing."
    )
    world.say(
        f"{parent.id} nodded and said that gentle care is its own kind of bravery."
    )


def _ending(world: World, child: Entity, case: Case, patient: Entity) -> None:
    child.memes["relief"] += 2
    patient.meters["fever"] = 0.0
    world.say(
        f"By the end, {patient.id} was resting softly, and {child.id} zipped {child.pronoun('possessive')} {case.label} the other way round to show the reversible colors."
    )
    world.say(
        f"{child.id} smiled at the two bright sides and hugged {patient.id} gently, glad the day had turned warm again."
    )


def tell(params: StoryParams) -> World:
    world = World()
    world.facts["setting"] = params.setting
    setting = SETTINGS[params.setting]
    case = CASES[params.case]
    medicine = MEDICINES[params.medicine]

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    assistant = world.add(Entity(id=params.assistant_name, kind="character", type=params.assistant_gender, role="assistant"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_gender, role="parent"))
    patient = world.add(Entity(id=params.patient, kind="character", type="thing", role="patient"))
    world.add(Entity(id="coat", type="thing", label=case.label, role="comfort", traits=["reversible"]))
    _story_state(world, child, assistant, parent, patient, case, medicine)
    world.para()
    _flashback(world, child, parent, medicine)
    world.para()
    _assistant_action(world, assistant, parent, medicine, patient)
    _moral_value(world, child, parent)
    world.para()
    _ending(world, child, case, patient)

    world.facts.update(
        child=child, assistant=assistant, parent=parent, patient=patient,
        case=case, medicine=medicine, setting=setting,
        ended_calm=patient.meters["fever"] <= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the words "{f["case"].label}", "{f["assistant"].role}", and "{f["medicine"].label}".',
        f"Tell a gentle clinic story where {f['child'].id} feels worried, but a helpful assistant explains {f['medicine'].label} and everyone ends the day calm.",
        "Write a story with a flashback to a remembered lesson and a moral value about caring for someone who is sick.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    assistant = f["assistant"]
    parent = f["parent"]
    patient = f["patient"]
    case = f["case"]
    medicine = f["medicine"]
    return [
        QAItem(
            question=f"Why did {child.id} feel better after the flashback?",
            answer=f"{child.id} remembered {parent.id}'s gentle lesson about {medicine.label}, so the worry became smaller. That memory helped {child.id} trust the assistant and stay calm.",
        ),
        QAItem(
            question=f"What did the assistant do to help {patient.id}?",
            answer=f"{assistant.id} carefully measured the {medicine.label} and gave it the way the doctor said. The medicine helped bring the fever down, so {patient.id} could rest.",
        ),
        QAItem(
            question=f"How did the story show the moral value?",
            answer=f"It showed that listening, helping, and being gentle matter when someone is sick. {child.id} learned that kindness can be brave and useful at the same time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items = [
        QAItem(
            question="What is a reversible jacket?",
            answer="A reversible jacket can be worn two ways, so you can turn it inside out and see a different side. It is like having two looks in one warm coat.",
        ),
        QAItem(
            question="What is penicillin?",
            answer="Penicillin is a medicine that can help treat some infections. Grown-ups and doctors use it carefully so it helps the body get well.",
        ),
        QAItem(
            question="What is an assistant at a clinic?",
            answer="An assistant helps keep things calm and organized. The assistant can bring supplies, explain steps, and make sure care is gentle.",
        ),
    ]
    return items


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


CURATED = [
    StoryParams("clinic", "jacket", "penicillin", "Mia", "girl", "Nia", "girl", "Mom", "girl", "Pip", "puppy"),
    StoryParams("home_visit", "blanket", "penicillin", "Noah", "boy", "Owen", "boy", "Dad", "boy", "Milo", "bunny"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.case is None or c[1] == args.case)
              and (args.medicine is None or c[2] == args.medicine)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case, medicine = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    assistant_gender = args.assistant_gender or "girl"
    assistant_name = args.assistant or ("Nia" if assistant_gender == "girl" else "Owen")
    parent_gender = args.parent_gender or "girl"
    parent_name = args.parent or ("Mom" if parent_gender == "girl" else "Dad")
    patient_kind = args.patient_kind or rng.choice(["bunny", "puppy", "kitten"])
    patient = args.patient or rng.choice(["Pip", "Milo", "Sunny"])
    return StoryParams(setting, case, medicine, child_name, child_gender, assistant_name,
                       assistant_gender, parent_name, parent_gender, patient, patient_kind)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for item in asp_valid_combos():
            print(item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
