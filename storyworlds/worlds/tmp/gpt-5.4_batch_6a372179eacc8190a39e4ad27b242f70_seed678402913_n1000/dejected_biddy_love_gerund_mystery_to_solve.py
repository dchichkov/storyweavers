#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dejected_biddy_love_gerund_mystery_to_solve.py
=========================================================================

A standalone storyworld about a child noticing that an old hen named Biddy looks
dejected, then solving the small everyday mystery by following a concrete clue.

Seed requirements carried into the world:
- the story text naturally includes "dejected", "biddy", and "love-gerund"
- the shape includes a small Mystery to Solve and clear Inner Monologue
- the tone stays close to slice-of-life domestic storytelling

Run it
------
    python storyworlds/worlds/gpt-5.4/dejected_biddy_love_gerund_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/dejected_biddy_love_gerund_mystery_to_solve.py --cause thirsty
    python storyworlds/worlds/gpt-5.4/dejected_biddy_love_gerund_mystery_to_solve.py --cause chilly --fix untangle
    python storyworlds/worlds/gpt-5.4/dejected_biddy_love_gerund_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/dejected_biddy_love_gerund_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/dejected_biddy_love_gerund_mystery_to_solve.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    coop_phrase: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hobby:
    id: str
    gerund: str
    phrase: str
    detail: str
    clue_touch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    symptom: str
    clue: str
    clue_tag: str
    problem_text: str
    fix: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_dejection(world: World) -> list[str]:
    hen = world.get("biddy")
    if hen.meters["problem"] < THRESHOLD:
        return []
    sig = ("dejected",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hen.memes["dejected"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    return ["__dejected__"]


def _r_relief(world: World) -> list[str]:
    hen = world.get("biddy")
    if hen.meters["problem"] >= THRESHOLD:
        return []
    if hen.meters["comfort"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hen.memes["calm"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="dejection", tag="emotional", apply=_r_dejection),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_skill(hobby: Hobby, cause: Cause) -> bool:
    return cause.clue_tag in hobby.tags


def supports(place: Place, cause: Cause) -> bool:
    return cause.id in place.affords


def correct_fix(cause: Cause, fix: Fix) -> bool:
    return cause.fix == fix.id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for hobby_id in HOBBIES:
            for cause_id, cause in CAUSES.items():
                for fix_id, fix in FIXES.items():
                    if supports(place, cause) and correct_fix(cause, fix):
                        combos.append((place_id, hobby_id, cause_id, fix_id))
    return combos


def explain_place(place: Place, cause: Cause) -> str:
    return (
        f"(No story: {place.label} doesn't fit the clue path for '{cause.id}'. "
        f"This small mystery only works where that problem could happen in a simple, everyday way.)"
    )


def explain_fix(cause: Cause, fix: Fix) -> str:
    return (
        f"(No story: '{fix.id}' would not solve why Biddy looks dejected. "
        f"For cause '{cause.id}', the reasonable fix is '{cause.fix}'.)"
    )


def predict_mystery(world: World, cause: Cause) -> dict:
    sim = world.copy()
    hen = sim.get("biddy")
    hen.meters["problem"] += 1
    propagate(sim, narrate=False)
    return {
        "dejected": hen.memes["dejected"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
        "problem_text": cause.problem_text,
    }


def introduce(world: World, child: Entity, adult: Entity, hobby: Hobby) -> None:
    world.say(
        f"{child.id} spent many calm mornings with {adult.label_word} in {world.place.label}. "
        f"{world.place.opening}"
    )
    world.say(
        f"{child.pronoun().capitalize()} loved {hobby.gerund}, and {hobby.detail}."
    )
    world.say(
        f"In a little notebook, {child.pronoun()} kept a silly 'love-gerund' list: "
        f'"I love {hobby.gerund}," "I love warm eggs," and "I love listening to Biddy scratch."'
    )


def meet_biddy(world: World, child: Entity) -> None:
    hen = world.get("biddy")
    child.memes["love"] += 1
    hen.memes["trust"] += 1
    world.say(
        f"The oldest hen there was a soft brown biddy named Biddy. "
        f"Usually she bustled around the yard like a tiny queen in feather slippers."
    )


def notice_change(world: World, child: Entity, cause: Cause) -> None:
    hen = world.get("biddy")
    hen.meters["problem"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"But that morning Biddy looked dejected. {cause.symptom}"
    )
    world.say(
        f"{child.id} stopped short. Inside {child.pronoun('possessive')} head came a small, busy thought: "
        f'"That is not Biddy\'s usual face. What happened?"'
    )


def wonder(world: World, child: Entity, adult: Entity, cause: Cause) -> None:
    pred = predict_mystery(world, cause)
    world.facts["predicted_problem"] = pred["problem_text"]
    world.say(
        f'{child.pronoun().capitalize()} glanced at {adult.label_word} and whispered, '
        f'"I think Biddy is trying to tell us a mystery."'
    )
    world.say(
        f'{adult.label_word.capitalize()} smiled and answered, "Then let\'s look slowly."'
    )


def search(world: World, child: Entity, hobby: Hobby, cause: Cause) -> None:
    child.memes["focus"] += 1
    extra = hobby.clue_touch
    if clue_skill(hobby, cause):
        world.say(
            f"As {child.pronoun()} looked around, {extra}. That helped {child.pronoun('object')} notice {cause.clue}."
        )
    else:
        world.say(
            f"{child.id} knelt by the coop and looked carefully under, around, and beside everything. "
            f"After a moment, {child.pronoun()} noticed {cause.clue}."
        )
    world.say(
        f'In {child.pronoun("possessive")} head, the pieces clicked together: '
        f'"Oh. That must be why she feels so droopy."'
    )


def solve(world: World, child: Entity, adult: Entity, cause: Cause, fix: Fix) -> None:
    hen = world.get("biddy")
    child.memes["care"] += 1
    world.para()
    world.say(
        f"Together, {child.id} and {adult.label_word} {fix.action}."
    )
    hen.meters["problem"] = 0.0
    hen.meters["comfort"] += 1
    propagate(world, narrate=False)
    hen.memes["dejected"] = 0.0
    world.say(
        f"{cause.result}"
    )


def ending(world: World, child: Entity, hobby: Hobby) -> None:
    hen = world.get("biddy")
    world.say(
        f"Biddy gave a pleased little cluck and went back to her ordinary busy self."
    )
    world.say(
        f"{child.id} let out the breath {child.pronoun()} had been holding. "
        f'"Mystery solved," {child.pronoun()} thought, feeling warm all over.'
    )
    world.say(
        f"Then the morning slipped back into its quiet rhythm: {child.id} went on {hobby.gerund}, "
        f"and Biddy scratched nearby as if the whole yard had settled into the right place again."
    )
    world.facts["solved"] = hen.memes["calm"] >= THRESHOLD or hen.meters["comfort"] >= THRESHOLD


def tell(
    place: Place,
    hobby: Hobby,
    cause: Cause,
    fix: Fix,
    child_name: str = "Nina",
    child_type: str = "girl",
    adult_type: str = "grandmother",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        label=child_name,
        traits=["gentle"],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    hen = world.add(Entity(
        id="biddy",
        kind="character",
        type="hen",
        role="hen",
        label="Biddy",
        phrase="the old brown hen",
    ))

    introduce(world, child, adult, hobby)
    meet_biddy(world, child)
    notice_change(world, child, cause)
    wonder(world, child, adult, cause)
    search(world, child, hobby, cause)
    solve(world, child, adult, cause, fix)
    ending(world, child, hobby)

    world.facts.update(
        child=child,
        adult=adult,
        hen=hen,
        place=place,
        hobby=hobby,
        cause=cause,
        fix=fix,
        clue_found=True,
        solved=world.facts.get("solved", True),
    )
    return world


PLACES = {
    "backyard": Place(
        id="backyard",
        label="the backyard",
        opening="The bean poles leaned in one corner, and the chicken coop sat under a pear tree.",
        coop_phrase="under the pear tree",
        affords={"thirsty", "tangled", "chilly"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        opening="Rows of basil and marigolds edged the path, and the coop stood by the fence.",
        coop_phrase="by the fence",
        affords={"thirsty", "chilly"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the little courtyard",
        opening="A broom rested by the steps, laundry moved on the line, and a neat coop tucked beside the shed.",
        coop_phrase="beside the shed",
        affords={"tangled", "chilly"},
    ),
}

HOBBIES = {
    "gardening": Hobby(
        id="gardening",
        gerund="gardening",
        phrase="garden",
        detail="She liked to press dirt around tiny roots and count new leaves as if they were green treasures",
        clue_touch="the dry earth by the coop door reminded her to look for what was missing",
        tags={"dry", "straw", "garden"},
    ),
    "sketching": Hobby(
        id="sketching",
        gerund="sketching",
        phrase="sketch",
        detail="A stubby pencil was almost always tucked behind one ear because lines and shapes felt important to her",
        clue_touch="the habit of noticing bent lines and crooked corners made one odd detail stand out",
        tags={"open", "string", "shape"},
    ),
    "sweeping": Hobby(
        id="sweeping",
        gerund="sweeping",
        phrase="sweep",
        detail="She enjoyed making little half-moons in the dust and leaving the stones clean enough to shine",
        clue_touch="the wish to put things back where they belonged made the mess near the coop easy to spot",
        tags={"string", "dry", "tidy"},
    ),
}

CAUSES = {
    "thirsty": Cause(
        id="thirsty",
        symptom="She stood beside her water dish without taking a sip, and her beak opened in a tired little pant.",
        clue="the water pan tipped on its side and the dirt underneath gone dark only in a small, already-dry ring",
        clue_tag="dry",
        problem_text="Biddy has no water because the pan tipped over",
        fix="refill",
        result="Fresh water glimmered in the bowl, and Biddy hurried over to drink, drink, drink.",
        tags={"hen", "water"},
    ),
    "chilly": Cause(
        id="chilly",
        symptom="Instead of stepping out proudly, she stayed puffed up in the doorway with her feathers ruffled by the breeze.",
        clue="the little coop window standing open and the straw inside shifting every time the wind slipped through",
        clue_tag="open",
        problem_text="A cold draft is blowing through the coop",
        fix="close_window",
        result="Once the draft was shut out and the straw fluffed, Biddy settled down and let her feathers smooth flat again.",
        tags={"hen", "wind", "straw"},
    ),
    "tangled": Cause(
        id="tangled",
        symptom="She tried to take two quick steps and then stopped, lifting one foot in a fussy, unhappy hop.",
        clue="a length of red yarn looped around one scaly leg and trailing under the nesting box",
        clue_tag="string",
        problem_text="Something is tangled around Biddy's leg",
        fix="untangle",
        result="When the loose yarn came away, Biddy set her foot down carefully and walked across the yard with a grand old-hen sway.",
        tags={"hen", "string"},
    ),
}

FIXES = {
    "refill": Fix(
        id="refill",
        action="set the pan upright, filled it with cool water, and tucked a flat stone beside it so it would not tip again",
        qa_text="set the water pan upright and refilled it",
        tags={"water"},
    ),
    "close_window": Fix(
        id="close_window",
        action="closed the little coop window, pushed fresh straw into the corner, and checked the latch with careful fingers",
        qa_text="closed the coop window and fixed the draft",
        tags={"wind", "straw"},
    ),
    "untangle": Fix(
        id="untangle",
        action="held Biddy gently, loosened the red yarn from her foot, and wound the string into a small safe ball",
        qa_text="gently untangled the yarn from Biddy's foot",
        tags={"string"},
    ),
}

GIRL_NAMES = ["Nina", "Mila", "Tess", "Ruby", "June", "Lena", "Ivy", "Cora"]
BOY_NAMES = ["Owen", "Eli", "Sam", "Noah", "Ben", "Theo", "Milo", "Jack"]


@dataclass
class StoryParams:
    place: str
    hobby: str
    cause: str
    fix: str
    child_name: str
    child_type: str
    adult_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "hen": [(
        "What is a hen?",
        "A hen is a grown-up female chicken. Hens peck, scratch in the dirt, and often lay eggs in a coop or nest."
    )],
    "water": [(
        "Why does a chicken need fresh water?",
        "A chicken needs fresh water every day to stay healthy and comfortable. If its water tips over, it can quickly feel weak and unhappy."
    )],
    "wind": [(
        "Why can a draft make an animal uncomfortable?",
        "A draft is moving cold air. If it blows into a resting place, it can make an animal feel chilly and keep it from settling down."
    )],
    "straw": [(
        "Why do people put straw in a coop?",
        "Straw helps make a coop soft, warm, and dry. It gives a hen a comfortable place to stand or rest."
    )],
    "string": [(
        "Why is loose string dangerous for animals?",
        "Loose string can wrap around feet or legs and make it hard to move. It can hurt an animal, so grown-ups clean it up or keep it put away."
    )],
}

KNOWLEDGE_ORDER = ["hen", "water", "wind", "straw", "string"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, hobby, cause = f["child"], f["hobby"], f["cause"]
    return [
        'Write a slice-of-life story for a 3-to-5-year-old that includes the words "dejected", "biddy", and "love-gerund".',
        f"Tell a gentle mystery-to-solve story where {child.id} notices that Biddy seems dejected, then uses careful looking and inner monologue to figure out what is wrong.",
        f"Write a quiet backyard story where a child who loves {hobby.gerund} follows a clue and discovers that {cause.problem_text.lower()}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, cause, fix, hobby = f["child"], f["adult"], f["cause"], f["fix"], f["hobby"]
    aw = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {aw}, and an old hen named Biddy. The story begins with an ordinary morning and turns into a small mystery."
        ),
        (
            f"What did {child.id} love doing?",
            f"{child.id} loved {hobby.gerund}. The story even says {child.pronoun()} kept a silly 'love-gerund' list about the things {child.pronoun()} loved."
        ),
        (
            "What was the mystery?",
            f"The mystery was why Biddy suddenly looked dejected instead of brisk and busy. {child.id} could tell something in the yard was wrong and wanted to find the cause."
        ),
        (
            f"What clue helped {child.id} solve the mystery?",
            f"The clue was {cause.clue}. That detail matched the way Biddy was acting, so it helped {child.id} understand the real problem."
        ),
        (
            f"How did they help Biddy?",
            f"They {fix.qa_text}. That solved the trouble, and Biddy's body language changed right away."
        ),
        (
            "How did the story end?",
            f"It ended quietly and happily, with Biddy back to her ordinary self and the morning feeling right again. After the mystery was solved, {child.id} went on {hobby.gerund} while Biddy scratched nearby."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cause"].tags) | set(world.facts["fix"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="backyard",
        hobby="gardening",
        cause="thirsty",
        fix="refill",
        child_name="Nina",
        child_type="girl",
        adult_type="grandmother",
    ),
    StoryParams(
        place="garden",
        hobby="sketching",
        cause="chilly",
        fix="close_window",
        child_name="Owen",
        child_type="boy",
        adult_type="grandfather",
    ),
    StoryParams(
        place="courtyard",
        hobby="sweeping",
        cause="tangled",
        fix="untangle",
        child_name="Ruby",
        child_type="girl",
        adult_type="aunt",
    ),
]


def outcome_of(params: StoryParams) -> str:
    if (
        params.place in PLACES
        and params.cause in CAUSES
        and params.fix in FIXES
        and supports(PLACES[params.place], CAUSES[params.cause])
        and correct_fix(CAUSES[params.cause], FIXES[params.fix])
    ):
        return "solved"
    return "unsolved"


ASP_RULES = r"""
valid(P,H,C,F) :- place(P), hobby(H), cause(C), fix(F), supports(P,C), correct_fix(C,F).
solved :- chosen_place(P), chosen_hobby(H), chosen_cause(C), chosen_fix(F), valid(P,H,C,F).
outcome(solved) :- solved.
outcome(unsolved) :- not solved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for cid in sorted(place.affords):
            lines.append(asp.fact("supports", pid, cid))
    for hid in HOBBIES:
        lines.append(asp.fact("hobby", hid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("needs_fix", cid, cause.fix))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("correct_fix", cid, cause.fix))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_hobby", params.hobby),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP valid set matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(77)
    for _ in range(12):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, rng)
            cases.append(p)
        except StoryError:
            pass
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child notices why Biddy looks dejected and solves a tiny mystery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hobby", choices=HOBBIES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if not supports(place, cause):
            raise StoryError(explain_place(place, cause))
    if args.cause and args.fix:
        cause = CAUSES[args.cause]
        fix = FIXES[args.fix]
        if not correct_fix(cause, fix):
            raise StoryError(explain_fix(cause, fix))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.hobby is None or c[1] == args.hobby)
        and (args.cause is None or c[2] == args.cause)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, hobby, cause, fix = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_type = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather", "aunt"])
    return StoryParams(
        place=place,
        hobby=hobby,
        cause=cause,
        fix=fix,
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.hobby not in HOBBIES:
        raise StoryError(f"(Unknown hobby '{params.hobby}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause '{params.cause}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}'.)")

    place = PLACES[params.place]
    hobby = HOBBIES[params.hobby]
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]

    if not supports(place, cause):
        raise StoryError(explain_place(place, cause))
    if not correct_fix(cause, fix):
        raise StoryError(explain_fix(cause, fix))

    world = tell(
        place=place,
        hobby=hobby,
        cause=cause,
        fix=fix,
        child_name=params.child_name,
        child_type=params.child_type,
        adult_type=params.adult_type,
    )
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hobby, cause, fix) combos:\n")
        for place, hobby, cause, fix in combos:
            print(f"  {place:10} {hobby:10} {cause:8} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.cause} at {p.place} ({p.hobby}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
