#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py
=======================================================================

A small detective-story world about a child sleuth, a worrying disappearance,
and a happy ending. Every valid story includes "tan" as a concrete clue or
object detail. The world model tracks physical state (where things are, whether
they are hidden, repaired, or found) and emotional state (worry, suspicion,
relief, pride). Prose is rendered from simulated state rather than from one
frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py --case missing_kite
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py --clue tan_thread
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py --hideout pond
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py --qa
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/tan_happy_ending_suspense_detective_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "sister"}
        male = {"boy", "father", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class CaseFile:
    id: str
    title: str
    missing_label: str
    missing_phrase: str
    owner_role: str
    reason_gone: str
    problem: str
    repair_word: str
    finish_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    texture: str
    points_to: set[str] = field(default_factory=set)
    fits_cases: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    mood: str
    holds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperPlan:
    id: str
    helper_type: str
    helper_label: str
    action: str
    fixes: set[str] = field(default_factory=set)
    used_at: set[str] = field(default_factory=set)
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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

    def note(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        other.history = list(self.history)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_discovery(world: World) -> list[str]:
    out: list[str] = []
    if "missing" not in world.entities or "detective" not in world.entities:
        return out
    missing = world.get("missing")
    detective = world.get("detective")
    if missing.meters["found"] < THRESHOLD:
        return out
    sig = ("discovery", "missing")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    out.append("__found__")
    return out


def _r_reunion(world: World) -> list[str]:
    out: list[str] = []
    if "owner" not in world.entities or "missing" not in world.entities:
        return out
    owner = world.get("owner")
    missing = world.get("missing")
    if missing.meters["returned"] < THRESHOLD:
        return out
    sig = ("reunion", "owner")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["relief"] += 1
    owner.memes["gratitude"] += 1
    out.append("__returned__")
    return out


CAUSAL_RULES = [
    Rule(name="discovery", tag="social", apply=_r_discovery),
    Rule(name="reunion", tag="social", apply=_r_reunion),
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
        for sent in produced:
            world.say(sent)
    return produced


CASES = {
    "missing_kite": CaseFile(
        id="missing_kite",
        title="The Case of the Vanished Kite",
        missing_label="kite",
        missing_phrase="a bright red kite with a paper tail",
        owner_role="neighbor",
        reason_gone="The wind had snapped one tail loop, so someone hid it away to mend it.",
        problem="torn_tail",
        repair_word="tail loop",
        finish_image="Soon the kite was dancing above the grass again.",
        tags={"kite", "repair"},
    ),
    "missing_dragon": CaseFile(
        id="missing_dragon",
        title="The Case of the Missing Dragon",
        missing_label="toy dragon",
        missing_phrase="a little green toy dragon with one loose wing",
        owner_role="cousin",
        reason_gone="Its wing had come loose, so someone tucked it away to glue it safely.",
        problem="loose_wing",
        repair_word="wing",
        finish_image="By sunset the toy dragon was perched on the windowsill, ready for new adventures.",
        tags={"toy", "repair"},
    ),
    "missing_banner": CaseFile(
        id="missing_banner",
        title="The Case of the Hidden Banner",
        missing_label="welcome banner",
        missing_phrase="a long paper welcome banner with one bent corner",
        owner_role="club",
        reason_gone="A bent corner had to be flattened before the party, so someone hid it while fixing it.",
        problem="bent_corner",
        repair_word="corner",
        finish_image="At last the banner stretched across the doorway, neat and proud.",
        tags={"banner", "party"},
    ),
}

CLUES = {
    "tan_thread": Clue(
        id="tan_thread",
        label="tan thread",
        phrase="a curl of tan thread",
        texture="soft and fuzzy",
        points_to={"shed", "porch"},
        fits_cases={"missing_kite", "missing_banner"},
        tags={"tan", "thread"},
    ),
    "tan_tape": Clue(
        id="tan_tape",
        label="tan tape",
        phrase="a little strip of tan tape",
        texture="flat and papery",
        points_to={"shed", "hall_table"},
        fits_cases={"missing_banner", "missing_dragon"},
        tags={"tan", "tape"},
    ),
    "tan_fur": Clue(
        id="tan_fur",
        label="tan fur",
        phrase="one tiny wisp of tan fur from the old repair blanket",
        texture="light as dust",
        points_to={"porch", "window_seat"},
        fits_cases={"missing_dragon"},
        tags={"tan", "fur"},
    ),
}

HIDEOUTS = {
    "shed": Hideout(
        id="shed",
        label="shed",
        phrase="the little garden shed",
        mood="The door stood almost closed, and the inside smelled of wood and string.",
        holds={"missing_kite", "missing_banner"},
        tags={"shed"},
    ),
    "porch": Hideout(
        id="porch",
        label="porch",
        phrase="the shadowy back porch",
        mood="The porch boards creaked, and a tan blanket covered a low basket in the corner.",
        holds={"missing_kite", "missing_dragon"},
        tags={"porch"},
    ),
    "hall_table": Hideout(
        id="hall_table",
        label="hall table",
        phrase="the narrow hall table with its long cloth hanging down",
        mood="Under the cloth, the table looked like a secret cave.",
        holds={"missing_banner"},
        tags={"hall"},
    ),
    "window_seat": Hideout(
        id="window_seat",
        label="window seat",
        phrase="the window seat with the lift-up lid",
        mood="The lid was not shut all the way, as if someone had hurried.",
        holds={"missing_dragon"},
        tags={"window"},
    ),
    "pond": Hideout(
        id="pond",
        label="pond",
        phrase="the duck pond by the willow tree",
        mood="The water rippled softly, but there was nowhere dry enough to mend anything.",
        holds=set(),
        tags={"pond"},
    ),
}

PLANS = {
    "grandpa_string": HelperPlan(
        id="grandpa_string",
        helper_type="man",
        helper_label="Grandpa",
        action="was tying on fresh string with careful old fingers",
        fixes={"torn_tail"},
        used_at={"shed", "porch"},
        reveal="Grandpa had hidden it only so the repair could be a surprise.",
        tags={"grandpa", "repair"},
    ),
    "aunt_glue": HelperPlan(
        id="aunt_glue",
        helper_type="woman",
        helper_label="Aunt Mira",
        action="was holding the loose piece in place while the glue set",
        fixes={"loose_wing"},
        used_at={"porch", "window_seat", "hall_table"},
        reveal="Aunt Mira had moved it somewhere quiet so nobody would bump the glue.",
        tags={"aunt", "repair"},
    ),
    "dad_tape": HelperPlan(
        id="dad_tape",
        helper_type="father",
        helper_label="Dad",
        action="was smoothing the wrinkle with a strip of tape and a ruler",
        fixes={"bent_corner"},
        used_at={"shed", "hall_table"},
        reveal="Dad had hidden it for one minute so it could look perfect at the party.",
        tags={"dad", "repair"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Eli", "Jack"]
OWNER_NAMES = ["Ruby", "Owen", "Pia", "Noah", "June", "Tess"]
TRAITS = ["sharp-eyed", "careful", "brave", "quiet", "patient", "clever"]


def clue_fits_case(clue: Clue, case_file: CaseFile) -> bool:
    return case_file.id in clue.fits_cases


def hideout_fits_case(hideout: Hideout, case_file: CaseFile) -> bool:
    return case_file.id in hideout.holds


def plan_fixes_case(plan: HelperPlan, case_file: CaseFile) -> bool:
    return case_file.problem in plan.fixes


def clue_points_to_hideout(clue: Clue, hideout: Hideout) -> bool:
    return hideout.id in clue.points_to


def plan_works_at_hideout(plan: HelperPlan, hideout: Hideout) -> bool:
    return hideout.id in plan.used_at


def valid_story(case_file: CaseFile, clue: Clue, hideout: Hideout, plan: HelperPlan) -> bool:
    return (
        clue_fits_case(clue, case_file)
        and hideout_fits_case(hideout, case_file)
        and plan_fixes_case(plan, case_file)
        and clue_points_to_hideout(clue, hideout)
        and plan_works_at_hideout(plan, hideout)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for case_id, case_file in CASES.items():
        for clue_id, clue in CLUES.items():
            for hideout_id, hideout in HIDEOUTS.items():
                for plan_id, plan in PLANS.items():
                    if valid_story(case_file, clue, hideout, plan):
                        combos.append((case_id, clue_id, hideout_id, plan_id))
    return combos


@dataclass
class StoryParams:
    case: str
    clue: str
    hideout: str
    plan: str
    detective_name: str
    detective_gender: str
    owner_name: str
    owner_gender: str
    parent_type: str
    trait: str
    urgency: str = "before_supper"
    seed: Optional[int] = None


def explain_rejection(case_file: CaseFile, clue: Clue, hideout: Hideout, plan: HelperPlan) -> str:
    reasons: list[str] = []
    if not clue_fits_case(clue, case_file):
        reasons.append(f"{clue.label} does not fit the missing {case_file.missing_label}")
    if not clue_points_to_hideout(clue, hideout):
        reasons.append(f"{clue.label} would not honestly point toward the {hideout.label}")
    if not hideout_fits_case(hideout, case_file):
        reasons.append(f"the {hideout.label} is not a plausible place to hide the {case_file.missing_label}")
    if not plan_fixes_case(plan, case_file):
        reasons.append(f"{plan.helper_label}'s plan does not fix the {case_file.problem.replace('_', ' ')}")
    if not plan_works_at_hideout(plan, hideout):
        reasons.append(f"{plan.helper_label} would not be using that plan in the {hideout.label}")
    if not reasons:
        reasons.append("the combination is not a valid detective case")
    return "(No story: " + "; ".join(reasons) + ".)"


def urgency_line(urgency: str) -> str:
    return {
        "before_supper": "and supper would begin before long",
        "before_guests": "and guests were expected any minute",
        "before_wind_died": "and the evening wind would not last forever",
    }[urgency]


def predict_hideout(world: World, hideout_id: str) -> dict:
    sim = world.copy()
    if "missing" not in sim.entities:
        return {"found": False}
    missing = sim.get("missing")
    if missing.attrs.get("hidden_at") == hideout_id:
        missing.meters["found"] += 1
    propagate(sim, narrate=False)
    return {"found": missing.meters["found"] >= THRESHOLD}


def open_case(world: World, detective: Entity, owner: Entity, case_file: CaseFile, urgency: str) -> None:
    detective.memes["curiosity"] += 1
    owner.memes["worry"] += 1
    world.say(
        f"{detective.id} liked to call {detective.pronoun('possessive')} small notebook a detective book, "
        f"even though it was only a folded pad tied with string."
    )
    world.say(
        f"That afternoon began with a gasp from {owner.id}. "
        f'"My {case_file.missing_label} is gone!" {owner.pronoun()} cried.'
    )
    world.say(
        f"It was {case_file.missing_phrase}, and it mattered because {urgency_line(urgency)}."
    )
    world.say(
        f'{detective.id} straightened up at once. "{case_file.title}," '
        f'{detective.pronoun()} whispered, already feeling the case begin.'
    )
    world.note("case_opened")


def inspect_scene(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"The yard suddenly felt full of secrets. A breeze rattled leaves. A gate clicked. "
        f"{detective.id} crouched low and searched for anything out of place."
    )
    world.say(
        f"Near the step, {detective.pronoun()} spotted {clue.phrase}. It looked {clue.texture}, "
        f"and its tan color stood out against the dark boards."
    )
    world.note("clue_found")


def suspect_and_reason(world: World, detective: Entity, clue: Clue, hideout: Hideout) -> None:
    pred = predict_hideout(world, hideout.id)
    world.facts["predicted_found"] = pred["found"]
    detective.memes["suspense"] += 1
    world.say(
        f'"A clue never wiggles here for no reason," {detective.id} murmured. '
        f'{detective.pronoun().capitalize()} followed where the clue seemed to point.'
    )
    world.say(hideout.mood)
    world.note("hideout_predicted")


def approach_hideout(world: World, detective: Entity, hideout: Hideout) -> None:
    detective.memes["fear"] += 1
    world.say(
        f"{detective.id} walked to {hideout.phrase} slowly, one careful step at a time. "
        f"For a moment, even the ordinary sounds around the place seemed suspicious."
    )
    world.say(
        f"{detective.pronoun().capitalize()} took a breath, reached out, and looked inside."
    )
    world.note("approach_hideout")


def discover(world: World, detective: Entity, owner: Entity, helper: Entity, case_file: CaseFile) -> None:
    missing = world.get("missing")
    missing.meters["found"] += 1
    missing.meters["visible"] += 1
    detective.memes["fear"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"There was the missing {case_file.missing_label} after all — not stolen, not ruined, just hidden beside "
        f"{helper.label}. {helper.label} {helper.attrs['action']}."
    )
    world.say(
        f'{detective.id} let out the breath {detective.pronoun()} had been holding. '
        f'"I found it!" {detective.pronoun()} said, though now the mystery felt softer than before.'
    )
    world.note("object_found")


def reveal_truth(world: World, detective: Entity, owner: Entity, helper: Entity, case_file: CaseFile, plan: HelperPlan) -> None:
    missing = world.get("missing")
    owner.memes["worry"] = 0.0
    helper.memes["care"] += 1
    world.say(
        f'{helper.label} looked up kindly. "{plan.reveal} '
        f'The {case_file.missing_label} had a {case_file.repair_word} problem, and I wanted to fix it first."'
    )
    world.say(
        f"The dark, suspicious feeling melted away. The case had not been about a thief at all. "
        f"It had been about a secret act of care."
    )
    missing.meters["repaired"] += 1
    world.note("truth_revealed")


def return_item(world: World, owner: Entity, missing: Entity, case_file: CaseFile) -> None:
    missing.meters["returned"] += 1
    missing.attrs["hidden_at"] = ""
    propagate(world, narrate=False)
    world.say(
        f"When the fixing was done, {owner.id} got the {case_file.missing_label} back with a shining smile."
    )
    world.say(case_file.finish_image)
    world.note("item_returned")


def close_case(world: World, detective: Entity, owner: Entity, helper: Entity, clue: Clue) -> None:
    detective.memes["suspense"] = 0.0
    detective.memes["joy"] += 1
    owner.memes["joy"] += 1
    world.say(
        f'{owner.id} hugged the mended treasure and said, "You really are a fine detective, {detective.id}."'
    )
    world.say(
        f"{detective.id} tucked {clue.phrase} into {detective.pronoun('possessive')} notebook as the last piece of evidence. "
        f"This time the tan clue led not to trouble, but to a happy answer."
    )
    world.note("case_closed")


def tell(
    case_file: CaseFile,
    clue: Clue,
    hideout: Hideout,
    plan: HelperPlan,
    detective_name: str,
    detective_gender: str,
    owner_name: str,
    owner_gender: str,
    parent_type: str,
    trait: str,
    urgency: str,
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            label=detective_name,
            role="detective",
            attrs={"trait": trait},
        )
    )
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            label=owner_name,
            role="owner",
            attrs={"role_name": case_file.owner_role},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=plan.helper_type,
            label=plan.helper_label,
            role="helper",
            attrs={"action": plan.action},
        )
    )
    missing = world.add(
        Entity(
            id="missing",
            type="missing_object",
            label=case_file.missing_label,
            phrase=case_file.missing_phrase,
            attrs={"hidden_at": hideout.id, "problem": case_file.problem},
        )
    )
    scene = world.add(
        Entity(
            id="scene",
            type="place",
            label=hideout.label,
            phrase=hideout.phrase,
        )
    )

    detective.memes["care"] += 1
    detective.memes["focus"] += 1
    owner.memes["trust"] += 1
    parent.memes["calm"] += 1

    open_case(world, detective, owner, case_file, urgency)
    world.para()
    inspect_scene(world, detective, clue)
    suspect_and_reason(world, detective, clue, hideout)
    world.para()
    approach_hideout(world, detective, hideout)
    discover(world, detective, owner, helper, case_file)
    reveal_truth(world, detective, owner, helper, case_file, plan)
    world.para()
    return_item(world, owner, missing, case_file)
    close_case(world, detective, owner, helper, clue)

    world.facts.update(
        detective=detective,
        owner=owner,
        parent=parent,
        helper=helper,
        missing=missing,
        case_file=case_file,
        clue=clue,
        hideout=hideout,
        plan=plan,
        urgency=urgency,
        solved=missing.meters["found"] >= THRESHOLD,
        repaired=missing.meters["repaired"] >= THRESHOLD,
        returned=missing.meters["returned"] >= THRESHOLD,
        happy=True,
        trace_history=list(world.history),
    )
    return world


KNOWLEDGE = {
    "tan": [
        (
            "What does tan mean?",
            "Tan is a light brown color, a bit like sand or some dry leaves. It is easy to notice when it shows up on something dark."
        )
    ],
    "thread": [
        (
            "What is thread?",
            "Thread is a thin string used for sewing or tying things together. A loose piece of thread can be a clue if it came from something nearby."
        )
    ],
    "tape": [
        (
            "What is tape used for?",
            "Tape is used to hold things together or smooth down paper. Grown-ups often use it for quick fixes."
        )
    ],
    "fur": [
        (
            "What is fur?",
            "Fur is the soft hair that covers some animals, and furry blankets can shed tiny bits too. A little wisp can stick to cloth or toys."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to figure out what happened. Good detectives pay attention before they guess."
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something means to fix it when it is torn, bent, or broken. After a repair, the thing can be used again."
        )
    ],
    "shed": [
        (
            "What is a shed?",
            "A shed is a small building where people keep tools, string, or garden things. It can feel mysterious because it is often dim inside."
        )
    ],
    "porch": [
        (
            "What is a porch?",
            "A porch is a covered place by a house where people can sit or leave things for a little while. Shadows on a porch can make ordinary objects look secret."
        )
    ],
    "hall": [
        (
            "What is a hall table?",
            "A hall table is a small table set along a hallway wall. If a cloth hangs over it, the space underneath can become a hiding spot."
        )
    ],
    "window": [
        (
            "What is a window seat?",
            "A window seat is a bench by a window, and some have lids that open for storage. Hidden spaces like that can hold blankets or toys."
        )
    ],
}
KNOWLEDGE_ORDER = ["tan", "detective", "repair", "thread", "tape", "fur", "shed", "porch", "hall", "window"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    case_file = f["case_file"]
    clue = f["clue"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the word "{clue.label.split()[0]}" and ends happily.',
        f"Tell a suspenseful but comforting mystery where {detective.id} investigates a missing {case_file.missing_label}, follows {clue.phrase}, and learns that the frightening guess was wrong.",
        f'Write a child-facing detective tale with a tan clue, a hidden object, a careful search, and a happy ending that proves kindness was behind the mystery.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    owner = f["owner"]
    helper = f["helper"]
    case_file = f["case_file"]
    clue = f["clue"]
    hideout = f["hideout"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, and {owner.id}, who could not find the {case_file.missing_label}. {helper.label} turns out to be part of the answer too."
        ),
        (
            f"What was missing?",
            f"The missing thing was {case_file.missing_phrase}. It felt urgent because {urgency_line(f['urgency'])}."
        ),
        (
            f"What clue did {detective.id} find?",
            f"{detective.id} found {clue.phrase}. The tan clue mattered because it pointed {detective.pronoun('object')} toward the right place to look next."
        ),
        (
            f"Why did the story feel suspenseful?",
            f"It felt suspenseful because the {case_file.missing_label} was gone and ordinary places suddenly seemed secret. As {detective.id} crept toward {hideout.phrase}, {detective.pronoun()} did not yet know whether the mystery meant trouble."
        ),
        (
            f"Where was the {case_file.missing_label}?",
            f"It was hidden at {hideout.phrase}. The clue led there, and that is where {detective.id} finally found it."
        ),
        (
            f"Why had the {case_file.missing_label} been hidden?",
            f"It had been hidden so {helper.label} could fix it. The mystery looked scary at first, but really it was a secret repair."
        ),
        (
            "How did the story end?",
            f"It ended happily because the {case_file.missing_label} was repaired and returned. The final clue showed kindness instead of danger, and everyone felt relieved."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue = f["clue"]
    hideout = f["hideout"]
    tags = {"detective", "repair"} | set(clue.tags) | set(hideout.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  history={world.history}")
    lines.append(f"  fired rules={sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_case(C, Cl)     :- clue(Cl), case(C), clue_case(Cl, C).
fits_hideout(C, H)   :- hideout(H), case(C), hideout_case(H, C).
fixes_case(C, P)     :- plan(P), case(C), case_problem(C, Prob), plan_fix(P, Prob).
points(Cl, H)        :- clue_points(Cl, H).
works_at(P, H)       :- plan_place(P, H).

valid(C, Cl, H, P) :- case(C), clue(Cl), hideout(H), plan(P),
                      fits_case(C, Cl),
                      fits_hideout(C, H),
                      fixes_case(C, P),
                      points(Cl, H),
                      works_at(P, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id, case_file in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("case_problem", case_id, case_file.problem))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for case_id in sorted(clue.fits_cases):
            lines.append(asp.fact("clue_case", clue_id, case_id))
        for hideout_id in sorted(clue.points_to):
            lines.append(asp.fact("clue_points", clue_id, hideout_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        for case_id in sorted(hideout.holds):
            lines.append(asp.fact("hideout_case", hideout_id, case_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        for problem in sorted(plan.fixes):
            lines.append(asp.fact("plan_fix", plan_id, problem))
        for place in sorted(plan.used_at):
            lines.append(asp.fact("plan_place", plan_id, place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        case="missing_kite",
        clue="tan_thread",
        hideout="shed",
        plan="grandpa_string",
        detective_name="Mia",
        detective_gender="girl",
        owner_name="Owen",
        owner_gender="boy",
        parent_type="mother",
        trait="careful",
        urgency="before_wind_died",
    ),
    StoryParams(
        case="missing_dragon",
        clue="tan_fur",
        hideout="window_seat",
        plan="aunt_glue",
        detective_name="Ben",
        detective_gender="boy",
        owner_name="Ruby",
        owner_gender="girl",
        parent_type="father",
        trait="sharp-eyed",
        urgency="before_supper",
    ),
    StoryParams(
        case="missing_banner",
        clue="tan_tape",
        hideout="hall_table",
        plan="dad_tape",
        detective_name="Lila",
        detective_gender="girl",
        owner_name="Noah",
        owner_gender="boy",
        parent_type="mother",
        trait="brave",
        urgency="before_guests",
    ),
    StoryParams(
        case="missing_kite",
        clue="tan_thread",
        hideout="porch",
        plan="grandpa_string",
        detective_name="Theo",
        detective_gender="boy",
        owner_name="June",
        owner_gender="girl",
        parent_type="father",
        trait="patient",
        urgency="before_wind_died",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-story world: a tan clue, a hidden object, suspense, and a happy ending."
    )
    ap.add_argument("--case", choices=sorted(CASES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-name")
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--urgency", choices=["before_supper", "before_guests", "before_wind_died"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid detective combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.clue and args.hideout and args.plan:
        case_file = CASES[args.case]
        clue = CLUES[args.clue]
        hideout = HIDEOUTS[args.hideout]
        plan = PLANS[args.plan]
        if not valid_story(case_file, clue, hideout, plan):
            raise StoryError(explain_rejection(case_file, clue, hideout, plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.clue is None or combo[1] == args.clue)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        case_file = CASES[args.case] if args.case else next(iter(CASES.values()))
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        hideout = HIDEOUTS[args.hideout] if args.hideout else next(iter(HIDEOUTS.values()))
        plan = PLANS[args.plan] if args.plan else next(iter(PLANS.values()))
        raise StoryError(explain_rejection(case_file, clue, hideout, plan))

    case_id, clue_id, hideout_id, plan_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    owner_pool = [n for n in OWNER_NAMES if n != detective_name]
    owner_name = args.owner_name or rng.choice(owner_pool)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    urgency = args.urgency or rng.choice(["before_supper", "before_guests", "before_wind_died"])
    return StoryParams(
        case=case_id,
        clue=clue_id,
        hideout=hideout_id,
        plan=plan_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        parent_type=parent_type,
        trait=trait,
        urgency=urgency,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        case_file = CASES[params.case]
        clue = CLUES[params.clue]
        hideout = HIDEOUTS[params.hideout]
        plan = PLANS[params.plan]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err}.)") from err
    if not valid_story(case_file, clue, hideout, plan):
        raise StoryError(explain_rejection(case_file, clue, hideout, plan))

    world = tell(
        case_file=case_file,
        clue=clue,
        hideout=hideout,
        plan=plan,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        parent_type=params.parent_type,
        trait=params.trait,
        urgency=params.urgency,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if "tan" not in sample.story.lower():
            raise StoryError("Story did not include the required seed word 'tan'.")
        print("OK: default randomized generation succeeded and included 'tan'.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, clue, hideout, plan) combos:\n")
        for case_id, clue_id, hideout_id, plan_id in combos:
            print(f"  {case_id:16} {clue_id:11} {hideout_id:11} {plan_id}")
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
            header = f"### {p.case} / {p.clue} / {p.hideout} / {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
