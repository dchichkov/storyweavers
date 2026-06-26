#!/usr/bin/env python3
"""
A tiny detective-story world with rye, crusted clues, a Twist, and a Happy Ending.

Premise:
A child detective follows a trail of crusted rye crumbs through a small setting,
asks who took the bread, discovers a surprising twist, and ends with a happy
ending that proves the case was solved.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    clues: set[str] = field(default_factory=set)
    suspects: set[str] = field(default_factory=set)


@dataclass
class CaseFile:
    id: str
    label: str
    phrase: str
    clue: str
    twist: str
    ending: str
    suspicious: set[str] = field(default_factory=set)
    locations: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    casefile: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.truths: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.truths = set(self.truths)
        return w


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, clues={"crumbs", "smell", "jar"}, suspects={"cat", "child", "neighbor"}),
    "bakery": Setting(place="the bakery", indoors=True, clues={"crumbs", "tray", "receipt"}, suspects={"baker", "customer", "cat"}),
    "garden": Setting(place="the garden", indoors=False, clues={"crumbs", "pawprints", "leaf"}, suspects={"bird", "dog", "neighbor"}),
}

CASEFILES = {
    "missing_rye": CaseFile(
        id="missing_rye",
        label="a missing rye loaf",
        phrase="a crusted rye loaf",
        clue="crusted rye crumbs",
        twist="The Twist was that the missing loaf had not been stolen at all.",
        ending="The Happy Ending was that the loaf was found warm in the oven, waiting for breakfast.",
        suspicious={"cat", "neighbor"},
        locations={"kitchen", "bakery"},
    ),
    "broken_tin": CaseFile(
        id="broken_tin",
        label="a broken cookie tin",
        phrase="a dusty tin of treats",
        clue="crumbs on the floor",
        twist="The Twist was that the tin had fallen when the shelf shook, not because a thief came.",
        ending="The Happy Ending was that everyone shared the saved treats and laughed together.",
        suspicious={"child", "neighbor"},
        locations={"kitchen", "garden"},
    ),
    "stolen_note": CaseFile(
        id="stolen_note",
        label="a missing note",
        phrase="a folded note with a ribbon",
        clue="a small trail of crumbs",
        twist="The Twist was that the note had been tucked into a bread basket by mistake.",
        ending="The Happy Ending was that the note was returned in time for the surprise party.",
        suspicious={"cat", "baker"},
        locations={"bakery", "kitchen"},
    ),
}

NAMES = ["Mina", "Theo", "Lina", "Pip", "Nora", "Ezra", "Ada", "Finn"]
TYPES = ["girl", "boy"]
HELPERS = ["cat", "dog", "bird", "neighbor"]
HELPER_TYPES = {"cat": "cat", "dog": "dog", "bird": "bird", "neighbor": "neighbor"}
DETECTIVE_TRAITS = ["curious", "careful", "brave", "sharp-eyed"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for case_id, case in CASEFILES.items():
            if place in case.locations:
                out.append((place, case_id))
    return out


def explain_rejection(place: str, casefile: str) -> str:
    case = CASEFILES[casefile]
    return f"(No story: {case.label} does not fit naturally in {SETTINGS[place].place}; try a matching place and clue.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with rye, crusted clues, a twist, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--casefile", choices=CASEFILES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--helper")
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
    if args.place and args.casefile and (args.place, args.casefile) not in valid_combos():
        raise StoryError(explain_rejection(args.place, args.casefile))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.casefile is None or c[1] == args.casefile)]
    if not combos:
        raise StoryError("(No valid detective case matches the given options.)")
    place, casefile = rng.choice(sorted(combos))
    case = CASEFILES[casefile]
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(sorted(case.suspicious))
    if helper not in HELPERS:
        helper = rng.choice(HELPERS)
    return StoryParams(
        place=place,
        casefile=casefile,
        detective_name=name,
        detective_type=gender,
        helper_name=helper.capitalize(),
        helper_type=HELPER_TYPES[helper],
    )


def setting_sentence(setting: Setting) -> str:
    if setting.indoors:
        return f"{setting.place.capitalize()} was quiet, except for the soft shuffle of shoes and the smell of bread."
    return f"{setting.place.capitalize()} was bright, with little hiding spots and a few clues waiting to be noticed."


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    case = CASEFILES[params.casefile]
    world = World(setting)
    detective = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    case_item = world.add(Entity(id="case_item", type="thing", label=case.label, phrase=case.phrase))
    crumbs = world.add(Entity(id="crumbs", type="thing", label="crumbs", phrase=case.clue))
    world.facts.update(detective=detective, helper=helper, case_item=case_item, crumbs=crumbs, case=case, params=params)
    detective.memes["interest"] = 1
    helper.memes["nervous"] = 1 if helper.type in case.suspicious else 0
    world.say(f"{detective.id} was a {rng_trait := random.choice(DETECTIVE_TRAITS)} {detective.type} who loved solving little mysteries.")
    world.say(f"One day, {detective.id} found {case.clue} near {setting.place} and knew something had happened.")
    world.say(setting_sentence(setting))
    return world


def clue_action(world: World) -> None:
    case = world.facts["case"]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    detective.memes["focus"] = detective.memes.get("focus", 0) + 1
    world.say(f"{detective.id} followed the {case.clue} carefully, one tiny step at a time.")
    if helper.type in case.suspicious:
        helper.memes["worry"] = helper.memes.get("worry", 0) + 1
        world.say(f"{helper.id} looked suspicious, but {detective.id} asked gentle questions instead of making a quick guess.")
    else:
        world.say(f"{helper.id} pointed to a small trail of crumbs and helped {detective.id} look closer.")


def reveal_twist(world: World) -> None:
    case = world.facts["case"]
    detective = world.facts["detective"]
    world.truths.add("twist")
    world.say(case.twist)
    if case.id == "missing_rye":
        world.say(f"The crusted rye smell came from the oven, where a loaf had been left to bake a little longer.")
    elif case.id == "broken_tin":
        world.say(f"The tin had tipped over when the shelf shook, and the crumbs made a misleading trail.")
    else:
        world.say(f"The ribboned note had slipped into the bread basket, hiding in plain sight among the crusts.")


def happy_ending(world: World) -> None:
    case = world.facts["case"]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    detective.memes["joy"] = detective.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(case.ending)
    world.say(f"{detective.id} smiled, {helper.id} smiled, and the little mystery was finally at peace.")


def tell(params: StoryParams) -> World:
    world = make_world(params)
    world.say(f"{params.detective_name} liked detective stories, especially the kind with rye crumbs and careful clues.")
    world.say(f"But this case was tricky, because the clues were crusted and the first guess could have been wrong.")
    world.say(f"{params.detective_name} and {params.helper_name} started at {world.setting.place} and looked for the truth.")
    world.say("")
    clue_action(world)
    world.say("")
    reveal_twist(world)
    world.say("")
    happy_ending(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a short detective story for a young child about {p.detective_name} and {case.label} with rye crumbs.",
        f"Tell a gentle mystery story set in {world.setting.place} that uses the words rye and crusted and ends with a happy ending.",
        f"Write a child-facing detective story with a twist where {p.helper_name} helps solve the clue trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    case = world.facts["case"]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {p.detective_name}, a {p.detective_type} who liked careful clues.",
        ),
        QAItem(
            question=f"What clue did {p.detective_name} follow?",
            answer=f"{p.detective_name} followed {case.clue}, which led through the story like a tiny trail.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=case.twist,
        ),
        QAItem(
            question=f"How did the story end?",
            answer=case.ending,
        ),
        QAItem(
            question=f"Who helped {p.detective_name} in the case?",
            answer=f"{helper.id} helped {p.detective_name}, and that made the mystery easier to solve.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rye?",
            answer="Rye is a kind of grain used to make bread with a sturdy, tasty crust.",
        ),
        QAItem(
            question="What does crusted mean?",
            answer="Crusted means something has a hard outer layer, like bread with a baked crust.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising new fact that changes what you thought was happening.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem is solved and the characters feel glad and safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"truths={sorted(world.truths)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", casefile="missing_rye", detective_name="Mina", detective_type="girl", helper_name="Cat", helper_type="cat"),
    StoryParams(place="bakery", casefile="stolen_note", detective_name="Theo", detective_type="boy", helper_name="Bird", helper_type="bird"),
    StoryParams(place="garden", casefile="broken_tin", detective_name="Lina", detective_type="girl", helper_name="Neighbor", helper_type="neighbor"),
]


ASP_RULES = r"""
place(P) :- setting(P).
case(C) :- casefile(C).
valid(P,C) :- setting(P), casefile(C), allowed(P,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for c, case in CASEFILES.items():
        lines.append(asp.fact("casefile", c))
        for p in sorted(case.locations):
            lines.append(asp.fact("allowed", p, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid detective cases:")
        for place, case in vals:
            print(f"  {place} / {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
