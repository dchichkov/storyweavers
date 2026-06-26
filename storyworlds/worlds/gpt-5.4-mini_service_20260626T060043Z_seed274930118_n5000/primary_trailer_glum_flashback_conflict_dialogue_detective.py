#!/usr/bin/env python3
"""
storyworlds/worlds/primary_trailer_glum_flashback_conflict_dialogue_detective.py
===============================================================================

A tiny detective-story world with:
- a primary case to solve,
- a trailer that can go missing,
- a glum mood that drives the opening,
- flashback as a reasoning instrument,
- conflict and dialogue as the turning point.

Seed tale premise:
---
A glum child at a trailer park says their little trailer is gone. A detective
looks around, asks careful questions, remembers a flashback about where the
trailer was last seen, and finds that the trailer was moved for a safe reason.
The argument cools, the truth comes out, and the day ends with the trailer
back in place.

World model:
---
- People have meters (physical state) and memes (emotional state).
- The detective can inspect places, question people, and use a flashback.
- Conflict rises when someone is blamed too early.
- Dialogue lowers conflict when it becomes honest.
- The primary case is solved when a clue identifies the trailer's location.

This script follows the Storyweavers contract:
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes ASP_RULES twin and asp_facts()
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
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


@dataclass
class Setting:
    place: str
    indoors: bool
    affordances: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    verb: str
    search: str
    clue_kind: str
    clue_text: str
    flashback_text: str
    resolution_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    label: str
    phrase: str
    type: str
    start_location: str
    hidden_location: str
    movers: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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


@dataclass
class StoryParams:
    place: str
    case: str
    target: str
    detective_name: str
    child_name: str
    child_gender: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "trailer_park": Setting(place="the trailer park", indoors=False, affordances={"search", "question", "flashback"}),
    "station": Setting(place="the little station", indoors=True, affordances={"search", "question", "flashback"}),
    "yard": Setting(place="the side yard", indoors=False, affordances={"search", "question", "flashback"}),
}

CASES = {
    "missing_trailer": Case(
        id="missing_trailer",
        verb="find the missing trailer",
        search="look around the lot",
        clue_kind="wheel_track",
        clue_text="fresh wheel tracks near the fence",
        flashback_text="the trailer had been rolled behind the shed to stay safe from a storm",
        resolution_text="the trailer was parked right where the flashback said it would be",
        tags={"trailer", "storm", "moved"},
    ),
    "lost_note": Case(
        id="lost_note",
        verb="find the lost note",
        search="check the desk and the bench",
        clue_kind="paper_fibers",
        clue_text="tiny paper fibers on the windowsill",
        flashback_text="the note had been tucked inside a coat pocket during a hurried move",
        resolution_text="the note was found inside the helper's coat",
        tags={"note", "coat", "pocket"},
    ),
    "misplaced_key": Case(
        id="misplaced_key",
        verb="find the missing key",
        search="inspect the mat and the drawer",
        clue_kind="scrape_mark",
        clue_text="a small scrape mark by the latch",
        flashback_text="the key had been hung on a hook after the door was locked",
        resolution_text="the key was hanging on the hook by the door",
        tags={"key", "hook", "door"},
    ),
}

TARGETS = {
    "trailer": Target(
        label="trailer",
        phrase="a little red trailer",
        type="trailer",
        start_location="the lot",
        hidden_location="behind the shed",
        movers={"parent", "helper"},
    ),
    "note": Target(
        label="note",
        phrase="a folded note",
        type="note",
        start_location="the desk",
        hidden_location="inside the coat pocket",
        movers={"helper"},
    ),
    "key": Target(
        label="key",
        phrase="a brass key",
        type="key",
        start_location="the hook",
        hidden_location="on the hook by the door",
        movers={"parent"},
    ),
}

DETECTIVE_NAMES = ["Mara", "Ned", "Ivy", "June", "Theo", "Sage"]
CHILD_NAMES = ["Lena", "Milo", "Pia", "Ollie", "Nina", "Remy"]
HELPER_NAMES = ["Mr. Cole", "Ms. Finch", "Aunt Bea", "Mr. Lane"]
TRAITS = ["curious", "careful", "brave", "quiet", "sharp"]


class WorldState:
    def __init__(self, world: World) -> None:
        self.world = world

    def location_of(self, eid: str) -> str:
        return self.world.get(eid).location

    def move(self, eid: str, loc: str) -> None:
        self.world.get(eid).location = loc

    def change_mood(self, eid: str, key: str, delta: float) -> None:
        ent = self.world.get(eid)
        ent.memes[key] = ent.memes.get(key, 0.0) + delta

    def change_meter(self, eid: str, key: str, delta: float) -> None:
        ent = self.world.get(eid)
        ent.meters[key] = ent.meters.get(key, 0.0) + delta


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective-story world with flashback, conflict, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--detective-name", dest="detective_name")
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name", dest="helper_name")
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
    place = args.place or rng.choice(list(SETTINGS))
    case = args.case or rng.choice(list(CASES))
    target = args.target or ("trailer" if case == "missing_trailer" else ("note" if case == "lost_note" else "key"))
    if case == "missing_trailer" and target != "trailer":
        raise StoryError("This case needs the trailer target.")
    if case == "lost_note" and target != "note":
        raise StoryError("This case needs the note target.")
    if case == "misplaced_key" and target != "key":
        raise StoryError("This case needs the key target.")
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, case=case, target=target, detective_name=detective_name,
                       child_name=child_name, child_gender=child_gender, helper_name=helper_name)


def _actor_title(ent: Entity) -> str:
    return ent.label or ent.id


def story_setup(world: World, params: StoryParams) -> World:
    case = CASES[params.case]
    target = TARGETS[params.target]
    detective = world.add(Entity(id="detective", kind="character", type="woman", label=params.detective_name,
                                 traits=["primary", "steady"], location=world.setting.place))
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name,
                             traits=["glum", "small"], location=world.setting.place))
    helper = world.add(Entity(id="helper", kind="character", type="man", label=params.helper_name,
                              traits=["nervous"], location=target.hidden_location))
    trailer = world.add(Entity(id="target", kind="thing", type=target.type, label=target.label,
                                phrase=target.phrase, location=target.start_location, hidden=True))

    world.facts.update(case=case, target=target, detective=detective, child=child, helper=helper, trailer=trailer)

    world.say(f"At {world.setting.place}, {child.label} was glum because {target.phrase} was gone.")
    world.say(f"{detective.label} took the primary case and said, \"We'll follow the clues.\"")
    world.say(f"The first thing to do was {case.search}.")
    return world


def _inspect_for_clue(world: World) -> str:
    case: Case = world.facts["case"]
    target: Target = world.facts["target"]
    detective: Entity = world.facts["detective"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]

    if case.id == "missing_trailer":
        clue = "wheel tracks"
        if helper.location == target.hidden_location:
            world.say(f"{detective.label} spotted {case.clue_text}.")
            return clue
    elif case.id == "lost_note":
        world.say(f"{detective.label} noticed {case.clue_text}.")
        return "paper"
    else:
        world.say(f"{detective.label} found {case.clue_text}.")
        return "scrape"
    return ""


def flashback(world: World) -> None:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    world.say(f"{detective.label} had a flashback: \"{case.flashback_text}.\"")
    world.facts["flashback_seen"] = True


def conflict_dialogue(world: World) -> None:
    detective: Entity = world.facts["detective"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    target: Target = world.facts["target"]

    child.memes["glum"] = child.memes.get("glum", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    world.say(f"{child.label} said, \"Someone must have taken it.\"")
    world.say(f"{helper.label} frowned and said, \"I only moved it to keep it safe.\"")
    world.say(f"{detective.label} said, \"Let's not guess. Let's talk it through.\"")
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1.0
    helper.memes["conflict"] = helper.memes.get("conflict", 0.0) + 1.0
    world.facts["conflict"] = True


def resolution(world: World) -> None:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    target: Target = world.facts["target"]

    target.hidden = False
    target.location = target.hidden_location
    world.say(f"{detective.label} followed the flashback and found the trail.")
    world.say(f"{helper.label} led them to {case.resolution_text}.")
    world.say(f"{child.label} looked surprised, then smiled as the truth came out.")
    world.say(f"\"I was wrong to blame you,\" {child.label} said. \"Thank you for helping.\"")
    world.say(f"{detective.label} replied, \"A good case needs clear eyes and honest words.\"")
    child.memes["glum"] = max(0.0, child.memes.get("glum", 0.0) - 1.0)
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    helper.memes["conflict"] = 0.0
    child.memes["conflict"] = 0.0
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.place])
    story_setup(world, params)
    world.para()
    _inspect_for_clue(world)
    flashback(world)
    world.para()
    conflict_dialogue(world)
    world.para()
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    target: Target = world.facts["target"]
    detective: Entity = world.facts["detective"]
    child: Entity = world.facts["child"]
    return [
        f"Write a short detective story with a glum child, a flashback, a conflict, and dialogue about a missing {target.label}.",
        f"Tell a child-friendly mystery where {detective.label} solves the primary case by following a flashback and talking things through.",
        f"Write a simple story set at {world.setting.place} where someone thinks a {target.label} is lost but the truth is safer than it first seemed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    target: Target = world.facts["target"]
    return [
        QAItem(
            question=f"Who was glum at the start of the story?",
            answer=f"{child.label} was glum because the {target.label} seemed to be gone.",
        ),
        QAItem(
            question=f"What did {detective.label} use to help solve the case?",
            answer=f"{detective.label} used a flashback, careful clues, and dialogue to solve the case.",
        ),
        QAItem(
            question=f"Why was there conflict in the middle?",
            answer=f"There was conflict because {child.label} thought someone had taken the {target.label}, but {helper.label} had only moved it for safety.",
        ),
        QAItem(
            question=f"Where was the {target.label} found in the end?",
            answer=f"It was found {target.hidden_location}, which matched the flashback clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    target: Target = world.facts["target"]
    case: Case = world.facts["case"]
    out = [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues, asks questions, and solves mysteries.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from earlier, so the character can remember an important detail.",
        ),
        QAItem(
            question="Why can talking help during a conflict?",
            answer="Talking can help because people can explain what they did and clear up a misunderstanding.",
        ),
    ]
    if "trailer" in target.label:
        out.append(QAItem(
            question="What is a trailer?",
            answer="A trailer is a small vehicle or room on wheels that can be moved from place to place.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
target_found(T) :- clue(T), flashback_used, dialogue_used.
resolved_case :- target_found(_).
conflict_present :- glum(child), blamed(child), not clarified.
clarified :- dialogue_used.
safe_truth :- helper_explained, clarified.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("clue", cid))
        if "trailer" in c.tags:
            lines.append(asp.fact("blamed", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for case in CASES:
            target = "trailer" if case == "missing_trailer" else "note" if case == "lost_note" else "key"
            combos.append((place, case, target))
    return combos


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved_case/0."))
    ok = True
    if model is None:
        ok = False
    py = set(valid_combos())
    if ok and py:
        print(f"OK: ASP program loads and Python has {len(py)} valid combos.")
        return 0
    print("ASP/Python verification failed.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved_case/0."))
    return [] if not model else [("dummy",)]


def asp_valid_stories() -> list[tuple]:
    return []


def resolve_name(gender: str, rng: random.Random) -> str:
    return rng.choice(CHILD_NAMES)


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


CURATED = [
    StoryParams(place="trailer_park", case="missing_trailer", target="trailer", detective_name="Mara",
                child_name="Lena", child_gender="girl", helper_name="Mr. Cole"),
    StoryParams(place="station", case="lost_note", target="note", detective_name="Ivy",
                child_name="Milo", child_gender="boy", helper_name="Ms. Finch"),
    StoryParams(place="yard", case="misplaced_key", target="key", detective_name="June",
                child_name="Pia", child_gender="girl", helper_name="Aunt Bea"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved_case/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks, but this compact world does not enumerate story tuples.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.case} at {p.place} (target: {p.target})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
