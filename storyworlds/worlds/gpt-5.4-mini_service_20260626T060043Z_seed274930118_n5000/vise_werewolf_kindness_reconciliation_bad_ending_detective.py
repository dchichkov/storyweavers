#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/vise_werewolf_kindness_reconciliation_bad_ending_detective.py
================================================================================================================

A small detective-story world built from the seed words "vise" and "werewolf".

Premise:
- A careful child detective notices a workshop mystery.
- A vise is damaged or misused.
- A werewolf is present, but the story is not about a monster attack; it is about clues,
  mistaken blame, kindness, and a reconciliation that may or may not succeed.
- The domain intentionally supports a "bad ending" branch when the detective is too harsh
  or too suspicious.

The world model tracks:
- meters: physical state such as damage, tightness, scraps, and evidence
- memes: emotional/social state such as suspicion, kindness, guilt, trust, and reconciliation

The prose is driven by simulated state, not by a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label_or_type(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    clue: str
    trouble: str
    turn: str
    ending: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps_with: set[str]
    action: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _narrate_meter(state: float, word: str) -> str:
    return f"{word}" if state >= THRESHOLD else ""


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        # suspicion can harden into bad judgment
        for detective in world.characters():
            if detective.type != "girl" and detective.type != "boy":
                continue
            if detective.memes.get("suspicion", 0) < THRESHOLD:
                continue
            sig = ("bad_judgment", detective.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if detective.memes.get("kindness", 0) < THRESHOLD:
                detective.memes["coldness"] = detective.memes.get("coldness", 0) + 1
                out.append("The clues started to feel smaller than the detective's worry.")
                changed = True

        # kindness can open the door to trust
        for a in world.characters():
            for b in world.characters():
                if a.id == b.id:
                    continue
                if a.memes.get("kindness", 0) < THRESHOLD:
                    continue
                if b.memes.get("hurt", 0) < THRESHOLD and b.memes.get("fear", 0) < THRESHOLD:
                    continue
                sig = ("soften", a.id, b.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                b.memes["trust"] = b.memes.get("trust", 0) + 1
                b.memes["hurt"] = max(0.0, b.memes.get("hurt", 0) - 1)
                out.append("A kinder voice made the room feel less sharp.")
                changed = True

        # damaged vise leads to evidence of the real cause
        vise = world.entities.get("vise")
        if vise and vise.meters.get("damage", 0) >= THRESHOLD:
            sig = ("evidence", "vise")
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("The cracked vise pointed to a heavier, stranger force than anyone first guessed.")
                changed = True

    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(case: Case, tool: Tool) -> bool:
    return case.id in tool.helps_with


@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    detective_type: str
    suspect_name: str
    suspect_type: str
    seed: Optional[int] = None


SETTINGS = {
    "workshop": Setting(place="the little workshop", indoor=True, affords={"vise"}),
    "shed": Setting(place="the backyard shed", indoor=True, affords={"vise"}),
    "barn": Setting(place="the old barn", indoor=True, affords={"vise"}),
}

CASES = {
    "vise": Case(
        id="vise",
        clue="a bent metal jaw",
        trouble="the vise would not close right",
        turn="the detective found tiny scratches on the screw",
        ending="the vise was still broken by the end",
        keyword="vise",
        tags={"metal", "tool", "clue"},
    ),
    "werewolf": Case(
        id="werewolf",
        clue="a tuft of gray fur by the workbench",
        trouble="someone blamed the werewolf too quickly",
        turn="the detective noticed muddy pawprints and a torn sleeve together",
        ending="the werewolf was not the villain after all",
        keyword="werewolf",
        tags={"werewolf", "moon", "fur"},
    ),
}

TOOLS = [
    Tool(
        id="flashlight",
        label="a small flashlight",
        helps_with={"werewolf"},
        action="shine light along the floor",
    ),
    Tool(
        id="note",
        label="a careful notebook",
        helps_with={"vise", "werewolf"},
        action="write down the clues",
    ),
    Tool(
        id="kind_words",
        label="kind words",
        helps_with={"werewolf"},
        action="speak gently before judging",
    ),
]

GIRL_NAMES = ["Maya", "Nora", "Lila", "June", "Ivy", "Elsa", "Ruby"]
BOY_NAMES = ["Theo", "Evan", "Noah", "Milo", "Finn", "Owen", "Leo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, case) for place, setting in SETTINGS.items() for case in setting.affords]


def tell(setting: Setting, case: Case, detective_name: str, detective_type: str,
         suspect_name: str, suspect_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label="the detective",
        traits=["careful", "curious"],
        memes={"suspicion": 0.0, "kindness": 1.0},
    ))
    suspect = world.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_type,
        label="the suspect",
        traits=["quiet", "nervous"],
        memes={"fear": 1.0, "hurt": 0.0, "trust": 0.0},
    ))
    vise = world.add(Entity(
        id="vise",
        type="tool",
        label="vise",
        phrase="an old iron vise",
        owner="workbench",
        meters={"damage": 0.0, "tightness": 0.0},
    ))
    world.facts.update(case=case, detective=detective, suspect=suspect, vise=vise)

    # Act 1
    world.say(f"{detective.id} was a little detective who loved clues, neat marks, and quiet corners.")
    world.say(f"One morning, {detective.id} found {case.clue} in {setting.place}.")
    world.say(f"The problem was simple to see: {case.trouble}.")
    world.para()

    # Act 2
    world.say(f"{detective.id} looked from the vise to {suspect.id} and felt a quick jump of suspicion.")
    detective.memes["suspicion"] += 1
    vise.meters["damage"] += 1
    if case.id == "werewolf":
        world.say(f"There was even a werewolf-shaped shadow near the wall, and that made the room feel jumpy.")
    else:
        world.say(f"Even a werewolf rumor seemed to hang in the air, though the real clue stayed on the workbench.")
    world.say(case.turn + ".")
    propagate(world)

    if case.id == "werewolf":
        suspect.memes["hurt"] += 1
        world.say(f"{suspect.id} lowered {suspect.pronoun('possessive')} eyes, because being blamed hurt more than the noise.")
    else:
        world.say(f"{suspect.id} kept quiet, because the broken vise made everyone tense.")
    world.para()

    # Act 3: kindness or bad ending branch
    if detective.memes.get("kindness", 0) >= THRESHOLD:
        world.say(f"Then {detective.id} stopped and used kind words instead of sharp ones.")
        detective.memes["kindness"] += 1
        suspect.memes["trust"] += 1
        suspect.memes["hurt"] = max(0.0, suspect.memes.get("hurt", 0) - 1)
        world.say(f"{suspect.id} showed the detective what {suspect.id} had seen near the vise.")
        world.say(f"That was the moment of reconciliation: the two of them began to work together.")
        world.facts["ending_kind"] = True
        world.facts["reconciled"] = True
        if case.id == "werewolf":
            world.say(f"The werewolf was not the villain after all; it only wanted to keep the workshop safe.")
            world.say(f"By the end, the detective and the werewolf nodded to each other like old neighbors.")
        else:
            world.say(f"The detective wrote the final notes, and the suspect finally looked relieved.")
            world.say(f"But the vise stayed bent, which made the ending feel a little sad.")
            world.facts["bad_ending"] = True
    else:
        world.say(f"{detective.id} never softened, and the room stayed cold.")
        world.say(f"The clues were there, but nobody trusted the detective enough to help.")
        world.say(f"That was a bad ending: the truth stayed stuck, just like the broken vise.")
        world.facts["ending_kind"] = False
        world.facts["reconciled"] = False
        world.facts["bad_ending"] = True

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    return [
        f'Write a short detective story for young children that includes "{case.keyword}" and a vise.',
        f"Tell a mystery about {detective.id}, a careful detective, and {suspect.id}, where kindness leads to reconciliation.",
        f"Write a child-friendly detective story with a bad ending branch, a werewolf clue, and a broken vise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    qa = [
        QAItem(
            question=f"What mystery did {detective.id} find in {world.setting.place}?",
            answer=f"{detective.id} found a mystery about {case.trouble}. The main clue was {case.clue}.",
        ),
        QAItem(
            question=f"Who first seemed suspicious when the vise was damaged?",
            answer=f"{detective.id} first felt suspicious of {suspect.id}, because the broken vise made the room feel strange.",
        ),
        QAItem(
            question="What kind of story ending did the world choose?",
            answer=(
                "The story ended with reconciliation if the detective stayed kind, "
                "but it could also end badly if nobody softened or trusted each other."
            ),
        ),
    ]
    if f.get("reconciled"):
        qa.append(QAItem(
            question="How did kindness help in the story?",
            answer=(
                f"Kindness helped when {detective.id} used gentle words instead of blaming. "
                f"That let {suspect.id} share the clues and made reconciliation possible."
            ),
        ))
    if f.get("bad_ending"):
        qa.append(QAItem(
            question="Why was the ending bad?",
            answer=(
                "The ending was bad because the truth stayed stuck, and the broken vise "
                "was never truly made right in a peaceful way."
            ),
        ))
    if case.id == "werewolf":
        qa.append(QAItem(
            question="What did the werewolf have to do with the mystery?",
            answer=(
                "The werewolf was part of the clue trail, but it was not the villain. "
                "The detective had to look past fear and see what really happened."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    out = [
        QAItem(
            question="What is a vise?",
            answer="A vise is a tool that holds something tightly so you can work on it.",
        ),
        QAItem(
            question="What is a werewolf?",
            answer="A werewolf is a story creature that is part person and part wolf.",
        ),
    ]
    if "kindness" in case.tags or f.get("reconciled"):
        out.append(QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring with other people.",
        ))
        out.append(QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means fixing hurt feelings and becoming friendly again.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A case is valid in ASP when the setting affords it.
valid(Place, Case) :- affords(Place, Case).

% Kindness and reconciliation are story outcomes, represented in the same model.
kind_story(Place, Case) :- valid(Place, Case), case_kind(Case).
bad_story(Place, Case) :- valid(Place, Case), case_bad(Case).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        for c in sorted(setting.affords):
            lines.append(asp.fact("affords", place, c))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        if cid == "werewolf":
            lines.append(asp.fact("case_kind", cid))
        if cid == "vise":
            lines.append(asp.fact("case_bad", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with vise, werewolf, kindness, reconciliation, and bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--suspect-name")
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.case is None or c[1] == args.case)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, case = rng.choice(sorted(combos))
    detective_gender = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    suspect_gender = args.suspect_gender or rng.choice(["girl", "boy"])
    suspect_name = args.suspect_name or rng.choice(GIRL_NAMES if suspect_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        case=case,
        detective_name=detective_name,
        detective_type=detective_gender,
        suspect_name=suspect_name,
        suspect_type=suspect_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CASES[params.case],
        params.detective_name,
        params.detective_type,
        params.suspect_name,
        params.suspect_type,
    )
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
    StoryParams(place="workshop", case="werewolf", detective_name="Maya", detective_type="girl", suspect_name="Owen", suspect_type="boy"),
    StoryParams(place="shed", case="vise", detective_name="Theo", detective_type="boy", suspect_name="Nora", suspect_type="girl"),
    StoryParams(place="barn", case="werewolf", detective_name="Ivy", detective_type="girl", suspect_name="Leo", suspect_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, case in combos:
            print(f"  {place:10} {case}")
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
