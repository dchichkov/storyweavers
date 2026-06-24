#!/usr/bin/env python3
"""
A small detective-story world about a missing cheque, a pursuit, and a Latin clue.

Premise:
- A careful child detective notices that a cheque has gone missing.
- The trail leads through a short pursuit.
- A Latin phrase becomes the key clue.
- The ending proves a lesson learned: kindness and careful listening solve the case.

The world is intentionally tiny and classical: a few entities, a few state changes,
and a clear beginning / turn / resolution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the quiet office"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    clue_word: str
    chase_word: str
    verb: str
    gerund: str
    trail: str
    tension: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    owner_role: str = "adult"
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("worry", 0.0) >= THRESHOLD and ("anxiety", ent.id) not in world.fired:
            world.fired.add(("anxiety", ent.id))
            ent.memes["focus"] = ent.memes.get("focus", 0.0) + 1
            out.append(f"{ent.id} kept thinking hard and paid closer attention.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("kindness", 0.0) >= THRESHOLD and ("kindness", ent.id) not in world.fired:
            world.fired.add(("kindness", ent.id))
            ent.memes["trust"] = ent.memes.get("trust", 0.0) + 1
            out.append(f"That kind move made the room feel safer.")
    return out


CAUSAL_RULES = [
    Rule("anxiety", "social", _r_anxiety),
    Rule("kindness", "social", _r_kindness),
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


def setting_detail(setting: Setting, case: Case) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, with paper stacked neatly on the desk."
    return f"{setting.place.capitalize()} looked calm, but even a calm place can hide a trail."


def predict_case(world: World, detective: Entity, case: Case, cheque: Entity) -> dict:
    sim = world.copy()
    sim.get(detective.id).memes["worry"] = sim.get(detective.id).memes.get("worry", 0.0) + 1
    sim.get(cheque.id).meters["missing"] = 1
    propagate(sim, narrate=False)
    return {
        "found_clue": bool(sim.facts.get("latin_clue")),
        "lesson": bool(sim.facts.get("lesson")),
    }


def start_case(world: World, detective: Entity, adult: Entity, cheque: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} was a small detective who loved neat notes, careful looking, and quiet puzzles."
    )
    world.say(
        f"{detective.pronoun().capitalize()} noticed a missing cheque and promised to find out where it went."
    )
    world.say(
        f"The clue on the desk mentioned {case.clue_word}, and that made {detective.id} think of old school lessons."
    )
    cheque.meters["missing"] = 1


def inner_monologue(world: World, detective: Entity, case: Case) -> None:
    detective.memes["worry"] = detective.memes.get("worry", 0.0) + 1
    world.say(
        f'{detective.id} thought, "If I stay calm, I can follow the {case.chase_word} without losing the clue."'
    )


def explain(problem: World, detective: Entity, adult: Entity, cheque: Entity, case: Case) -> None:
    world = problem
    world.say(
        f"{detective.id} looked at the desk again and saw a scrap with the words {case.clue_word} written in Latin."
    )
    world.say(
        f'That little phrase felt like a map: {detective.id} knew it was time for a gentle pursuit.'
    )


def pursue(world: World, detective: Entity, suspect: Entity, case: Case, cheque: Entity) -> None:
    detective.meters["distance"] = detective.meters.get("distance", 0.0) + 1
    suspect.meters["distance"] = suspect.meters.get("distance", 0.0) + 1
    detective.memes["focus"] = detective.memes.get("focus", 0.0) + 1
    world.facts["pursuit"] = True
    world.say(
        f"{detective.id} followed the trail slowly, because a good pursuit is careful, not wild."
    )
    world.say(
        f"At the corner, {detective.id} spotted {suspect.id}, who had been carrying the cheque in a folded pocket."
    )


def kindness_move(world: World, detective: Entity, suspect: Entity, adult: Entity, cheque: Entity) -> None:
    detective.memes["kindness"] = detective.memes.get("kindness", 0.0) + 1
    suspect.memes["kindness"] = suspect.memes.get("kindness", 0.0) + 1
    world.facts["kindness"] = True
    world.say(
        f'Instead of scolding anyone, {detective.id} said, "It is okay. Let us talk first."'
    )
    world.say(
        f"That kind voice helped {suspect.id} relax, and {suspect.id} handed back the cheque."
    )
    cheque.carried_by = adult.id


def lesson(world: World, detective: Entity, adult: Entity, case: Case, cheque: Entity) -> None:
    detective.memes["lesson"] = detective.memes.get("lesson", 0.0) + 1
    world.facts["lesson"] = True
    world.say(
        f'{detective.id} learned that clues make more sense when you listen closely and stay kind.'
    )
    world.say(
        f"By the end, the cheque was safe again, the Latin clue made sense, and {detective.id} walked home feeling proud."
    )


SETTINGS = {
    "office": Setting(place="the quiet office", indoor=True, affords={"case"}),
    "hall": Setting(place="the long hall", indoor=True, affords={"case"}),
    "library": Setting(place="the library", indoor=True, affords={"case"}),
}

CASES = {
    "latin": Case(
        id="latin",
        clue_word="carpe diem",
        chase_word="pursuit",
        verb="pursue the trail",
        gerund="pursuing the trail",
        trail="a folded note",
        tension="a missing cheque",
        tags={"latin", "cheque", "pursuit"},
    ),
}

OBJECTS = {
    "cheque": ObjectCfg(
        label="cheque",
        phrase="a folded cheque in a bright envelope",
        type="paper",
    ),
}

NAMES = ["Maya", "Noah", "Tess", "Eli", "Ivy", "Finn"]
ADULTS = ["mother", "father", "aunt", "uncle"]
SUSPECTS = ["Milo", "Nina", "Oscar", "Pia"]


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    adult: str
    suspect: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for case_id in CASES:
            if "case" in setting.affords:
                combos.append((place, case_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about a cheque and a Latin clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
        raise StoryError("(No valid detective story matches the given options.)")
    place, case = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        case=case,
        name=args.name or rng.choice(NAMES),
        adult=args.adult or rng.choice(ADULTS),
        suspect=args.suspect or rng.choice(SUSPECTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    detective = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Maya", "Tess", "Ivy"} else "boy"))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult))
    suspect = world.add(Entity(id=params.suspect, kind="character", type="boy"))
    cheque = world.add(Entity(id="cheque", type="thing", label="cheque", phrase="a folded cheque"))
    case = CASES[params.case]

    start_case(world, detective, adult, cheque, case)
    world.para()
    world.say(setting_detail(world.setting, case))
    inner_monologue(world, detective, case)
    explain(world, detective, adult, cheque, case)
    pursue(world, detective, suspect, case, cheque)
    world.para()
    kindness_move(world, detective, suspect, adult, cheque)
    lesson(world, detective, adult, case, cheque)
    world.facts.update(detective=detective, adult=adult, suspect=suspect, cheque=cheque, case=case)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short detective story for a young child about a missing cheque and a Latin clue.',
        f"Tell a gentle pursuit story where {f['detective'].id} uses a Latin hint to find the cheque.",
        "Write a story with inner monologue, kindness, and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, a, s, c = f["detective"], f["adult"], f["suspect"], f["case"]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer="A cheque was missing, and that made the detective start the case.",
        ),
        QAItem(
            question=f"What Latin clue helped {d.id} think about the pursuit?",
            answer=f"The clue was “{c.clue_word}”, and it helped {d.id} follow the trail.",
        ),
        QAItem(
            question=f"How did {d.id} solve the problem without making things worse?",
            answer=f"{d.id} used kindness, talked calmly, and got the cheque back instead of shouting.",
        ),
        QAItem(
            question=f"What lesson did {d.id} learn at the end?",
            answer="The detective learned that listening closely and being kind can help solve a problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cheque?",
            answer="A cheque is a paper note used to ask a bank to move money from one account to another.",
        ),
        QAItem(
            question="What does pursuit mean?",
            answer="A pursuit is the act of following someone or something in order to catch up or find out more.",
        ),
        QAItem(
            question="What is Latin?",
            answer="Latin is an old language that many modern words and phrases come from.",
        ),
        QAItem(
            question="Why is kindness helpful in a hard moment?",
            answer="Kindness helps people feel safe enough to talk, listen, and solve the problem together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
           "== Story QA =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(office).
setting(hall).
setting(library).
affords(office,case).
affords(hall,case).
affords(library,case).

clue(latin, "carpe diem").
case_kind(latin).
valid_story(P,C) :- setting(P), case_kind(C), affords(P,case).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case_kind", cid))
        lines.append(asp.fact("latin_clue", cid))
        lines.append(asp.fact("clue_word", cid, c.clue_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [StoryParams(place="office", case="latin", name="Maya", adult="mother", suspect="Milo")]


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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


if __name__ == "__main__":
    main()
