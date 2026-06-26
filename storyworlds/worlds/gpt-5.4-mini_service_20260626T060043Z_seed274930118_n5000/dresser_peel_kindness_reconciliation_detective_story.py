#!/usr/bin/env python3
"""
storyworlds/worlds/dresser_peel_kindness_reconciliation_detective_story.py
===========================================================================

A small detective-story world about a child sleuth, a peeling dresser, and the
gentle turn from suspicion to kindness and reconciliation.

Premise:
- In a bedroom or dressing nook, a dresser has a peeling patch.
- The child detective notices the clue and tries to solve the mystery.
- The apparent culprit is not the true one.
- A misunderstanding is repaired through kindness, apology, and a careful fix.

This world is intentionally compact and constraint-checked:
- the dresser must truly be at risk from peeling;
- the detective's investigation must produce a plausible turn;
- the ending must show a changed emotional state and a repaired object.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["damage", "dust", "order"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "suspicion", "kindness", "reconciliation", "fear", "joy", "guilt", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    verb: str
    gerund: str
    damage_word: str
    risk_region: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"peel"}),
    "dressing_room": Setting(place="the dressing room", indoor=True, affords={"peel"}),
}

MYSTERIES = {
    "peel": Mystery(
        id="peel",
        clue="a curling strip of finish",
        verb="peel",
        gerund="peeling",
        damage_word="scraped and dull",
        risk_region="surface",
        keyword="peel",
        tags={"dresser", "peel"},
    )
}

FIXES = {
    "wax": Fix(
        id="wax",
        label="a tin of wood wax",
        phrase="a small tin of wood wax",
        prep="carefully rub the dresser with wood wax",
        tail="carefully rubbed the dresser with wood wax",
    ),
    "cloth": Fix(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth and a little polish",
        prep="polish the dresser with a soft cloth",
        tail="polished the dresser with a soft cloth",
    ),
}

NAMES = ["Mina", "Eli", "June", "Noah", "Tara", "Owen", "Lena", "Iris"]
TRAITS = ["curious", "careful", "brave", "patient", "sharp-eyed", "gentle"]
HELPER_TYPES = ["sister", "brother"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    fix: str
    name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def clue_is_real(mystery: Mystery) -> bool:
    return mystery.id == "peel"


def fix_is_reasonable(mystery: Mystery, fix: Fix) -> bool:
    return mystery.id == "peel" and fix.id in {"wax", "cloth"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            for fid in FIXES:
                if fix_is_reasonable(MYSTERIES[mid], FIXES[fid]):
                    out.append((place, mid, fid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about a peeling dresser, kindness, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.mystery and args.fix:
        if not fix_is_reasonable(MYSTERIES[args.mystery], FIXES[args.fix]):
            raise StoryError("That fix would not really solve the peeling dresser mystery.")

    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.mystery is None or c[1] == args.mystery
              if args.fix is None or c[2] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        fix=fix,
        name=args.name or rng.choice(NAMES),
        helper_type=args.helper_type or rng.choice(HELPER_TYPES),
        trait=args.trait or rng.choice(TRAITS),
    )


def _investigate(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["curiosity"] += 1
    detective.memes["suspicion"] += 1
    world.say(f"{detective.id} noticed a curly little strip on the dresser. It looked like a clue.")
    world.say(f"{detective.pronoun().capitalize()} knelt down, squinted, and began to investigate the peeling edge.")


def _accuse(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    detective.memes["fear"] += 1
    helper.memes["fear"] += 1
    helper.memes["guilt"] += 1
    world.say(f"At first, {detective.id} thought {helper.id} must have done it.")
    world.say(f"But {helper.id} looked worried, not sneaky, and {helper.pronoun()} whispered that {helper.pronoun('subject')} had only been trying to help.")


def _reveal(world: World, detective: Entity, helper: Entity, dresser: Entity, fix: Fix) -> None:
    detective.memes["suspicion"] = 0.0
    detective.memes["kindness"] += 1
    detective.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    helper.memes["relief"] += 1
    world.say(f"Then {detective.id} saw the truth: a stuck sticker had been tugging at the dresser's finish all along.")
    world.say(f"{helper.id} had peeled the sticker off the wrong way while trying to be helpful, and the dresser got scraped.")
    world.say(f"{detective.id} took a breath, spoke kindly, and said, \"We can fix it together.\"")
    world.say(f"Together they {fix.tail} until the dull patch looked smooth again.")


def _ending(world: World, detective: Entity, helper: Entity, dresser: Entity) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    dresser.meters["damage"] = 0.0
    world.say(f"In the end, {detective.id} and {helper.id} were laughing side by side.")
    world.say(f"The dresser stood tidy and bright again, and the room felt peaceful instead of tense.")


def tell(setting: Setting, mystery: Mystery, fix: Fix, name: str, helper_type: str, trait: str) -> World:
    if not clue_is_real(mystery) or not fix_is_reasonable(mystery, fix):
        raise StoryError("This world only supports a real peeling dresser mystery with a workable repair.")

    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type="girl" if name in {"Mina", "June", "Tara", "Lena", "Iris"} else "boy"))
    detective.memes["curiosity"] = 1.0
    detective.memes["kindness"] = 0.0
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    dresser = world.add(Entity(
        id="dresser",
        type="dresser",
        label="dresser",
        phrase="an old wooden dresser",
        caretaker=helper.id,
        region="surface",
    ))
    dresser.meters["damage"] = 1.0

    world.say(f"{detective.id} was a {trait} little detective in {setting.place}.")
    world.say(f"{detective.id} loved solving tiny mysteries, especially ones with clues like {mystery.clue}.")
    world.say(f"In the corner stood {dresser.phrase}, and one shiny place was starting to {mystery.verb}.")

    world.para()
    _investigate(world, detective, mystery)
    _accuse(world, detective, helper, mystery)

    world.para()
    _reveal(world, detective, helper, dresser, fix)
    _ending(world, detective, helper, dresser)

    world.facts.update(
        detective=detective,
        helper=helper,
        dresser=dresser,
        mystery=mystery,
        fix=fix,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d, h, m = f["detective"], f["helper"], f["mystery"]
    return [
        f'Write a gentle detective story for young children about {d.id} solving a mystery with the word "{m.keyword}".',
        f"Tell a short story where {d.id} notices a peeling dresser, first suspects {h.id}, and then chooses kindness.",
        f'Write a simple detective tale that ends with reconciliation and a dresser being fixed carefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, h, dresser, m, fix = f["detective"], f["helper"], f["dresser"], f["mystery"], f["fix"]
    return [
        QAItem(
            question=f"What mystery did {d.id} notice in {world.setting.place}?",
            answer=f"{d.id} noticed that the dresser was peeling and used the clue to investigate.",
        ),
        QAItem(
            question=f"Who did {d.id} first think had caused the trouble?",
            answer=f"At first, {d.id} thought {h.id} had done it, but that was only a guess.",
        ),
        QAItem(
            question=f"How did {d.id} and {h.id} fix the dresser?",
            answer=f"They fixed it by working together with {fix.label}, which made the dresser look smooth again.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The misunderstanding turned into reconciliation, and the room became calm and happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dresser?",
            answer="A dresser is a piece of furniture with drawers where people can keep clothes and small things.",
        ),
        QAItem(
            question="What does it mean when paint or wood is peeling?",
            answer="Peeling means a thin top layer is coming loose or curling up from the surface.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people make up after a problem and feel friendly again.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A dresser is at risk when a peeling mystery targets its surface.
at_risk(D) :- dresser(D), peeling(D).

% A fix is reasonable only when it can actually mend the peeling surface.
reasonable_fix(F) :- fix(F), can_fix_peel(F).

valid_story(P, M, F) :- place(P), mystery(M), fix(F), at_risk(dresser), reasonable_fix(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("peeling", "dresser"))
        lines.append(asp.fact("can_fix_peel", "wax"))
        lines.append(asp.fact("can_fix_peel", "cloth"))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    lines.append(asp.fact("dresser", "dresser"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="bedroom", mystery="peel", fix="wax", name="Mina", helper_type="sister", trait="curious"),
    StoryParams(place="dressing_room", mystery="peel", fix="cloth", name="Owen", helper_type="brother", trait="sharp-eyed"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.mystery is None or c[1] == args.mystery
              if args.fix is None or c[2] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        fix=fix,
        name=args.name or rng.choice(NAMES),
        helper_type=args.helper_type or rng.choice(HELPER_TYPES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], FIXES[params.fix], params.name, params.helper_type, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print("  ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.place} (fix: {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
