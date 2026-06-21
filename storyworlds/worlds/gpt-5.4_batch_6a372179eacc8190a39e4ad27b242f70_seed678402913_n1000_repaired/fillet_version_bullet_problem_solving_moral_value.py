#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fillet_version_bullet_problem_solving_moral_value.py
================================================================================

A standalone storyworld for a gentle detective-story domain: two child sleuths
help solve a small mystery in a busy food stall. A needed paper goes missing
just before lunch, the children gather clues, and the "culprit" turns out to be
a worried helper who was trying to improve the paper, not steal it.

This world is built around three seed words that always appear naturally in the
story:

* fillet  -- the special lunch dish at the stall
* version -- the helper is making a neater or corrected version of the paper
* bullet  -- one branch involves turning notes into a bullet list

The world emphasizes problem solving, moral value, and teamwork in a child-safe
detective style.
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

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
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


# ---------------------------------------------------------------------------
# Domain configs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    stall_name: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Document:
    id: str
    label: str
    phrase: str
    purpose: str
    line: str
    doc_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    want: str
    version_line: str
    admission: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    clue: str
    clue_detail: str
    found_line: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    style: str
    start_line: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
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

    def detectives(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "detective"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_causes_delay(world: World) -> list[str]:
    doc = world.entities.get("document")
    cook = world.entities.get("Cook")
    if doc is None or cook is None:
        return []
    if doc.meters["missing"] < THRESHOLD:
        return []
    sig = ("delay", doc.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cook.meters["delayed"] += 1
    cook.memes["worry"] += 1
    for det in world.detectives():
        det.memes["alert"] += 1
    return ["__delay__"]


def _r_kindness_opens_honesty(world: World) -> list[str]:
    helper = world.entities.get("Helper")
    if helper is None:
        return []
    if helper.memes["asked_kindly"] < THRESHOLD or helper.memes["worry"] < THRESHOLD:
        return []
    sig = ("honesty", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["honesty"] += 1
    helper.memes["relief"] += 1
    return ["__honesty__"]


CAUSAL_RULES = [
    Rule(name="missing_delay", tag="physical", apply=_r_missing_causes_delay),
    Rule(name="kindness_honesty", tag="social", apply=_r_kindness_opens_honesty),
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


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def document_supports_motive(document: Document, motive: Motive) -> bool:
    return motive.id in DOCUMENT_MOTIVES[document.id]


def place_supports_document(place: Place, document: Document) -> bool:
    return document.id in place.supports


def valid_combo(document: Document, motive: Motive, place: Place) -> bool:
    return document_supports_motive(document, motive) and place_supports_document(place, document)


def sensible_responses() -> list[Response]:
    return [resp for resp in RESPONSES.values() if resp.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    if params.response == "ask_kindly" and params.motive == "fix_spelling":
        return "quick_confession"
    return "clue_then_confession"


def explain_combo_rejection(document: Document, motive: Motive, place: Place) -> str:
    if not document_supports_motive(document, motive):
        return (
            f"(No story: {document.phrase} does not fit the motive '{motive.id}'. "
            f"The helper needs a believable reason to borrow that paper.)"
        )
    return (
        f"(No story: {place.phrase} is not a plausible place to work on {document.phrase}. "
        f"Pick a place that fits the paper and the clue trail.)"
    )


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on kindness and common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for document_id, document in DOCUMENTS.items():
            for motive_id, motive in MOTIVES.items():
                for place_id, place in PLACES.items():
                    if valid_combo(document, motive, place):
                        combos.append((setting_id, document_id, motive_id, place_id))
    return combos


# ---------------------------------------------------------------------------
# Story actions.
# ---------------------------------------------------------------------------
def introduce(world: World, setting: Setting, det_a: Entity, det_b: Entity, cook: Entity,
              helper: Entity, document: Document) -> None:
    for child in (det_a, det_b):
        child.memes["curiosity"] += 1
        child.memes["teamwork"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"At {setting.stall_name} in {setting.place}, {setting.scene}. "
        f"{det_a.id} and {det_b.id} liked to pretend they were detectives, and {cook.label_word} "
        f"let them help set up the lunch rush."
    )
    world.say(
        f"Today's special was crispy lemon fillet, and {cook.label_word} needed {document.phrase} "
        f"because {document.purpose}."
    )


def discover_missing(world: World, cook: Entity, document: Entity, document_cfg: Document) -> None:
    document.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {cook.label_word} reached for {document_cfg.phrase}, it was gone. "
        f'"My best {document_cfg.doc_word} has disappeared," {cook.pronoun()} said. '
        f'"Without it, the lunch line may slow down."'
    )


def inspect_start(world: World, det_a: Entity, det_b: Entity, response: Response) -> None:
    if response.id == "ask_kindly":
        world.say(
            f'{det_a.id} tapped a pretend magnifying glass against {det_b.id}\'s sleeve. '
            f'"Detective case," {det_a.pronoun()} whispered. {response.start_line}'
        )
    else:
        world.say(
            f'{det_a.id} crouched low and {det_b.id} leaned close beside {det_a.pronoun("object")}. '
            f'"Detective case," {det_b.pronoun()} whispered. {response.start_line}'
        )


def find_clue(world: World, det_a: Entity, det_b: Entity, place: Place) -> None:
    for child in (det_a, det_b):
        child.memes["focus"] += 1
    world.facts["clue_text"] = place.clue
    world.say(
        f"Soon they noticed {place.clue}. {det_a.id} saw one part of it, and {det_b.id} spotted "
        f"the rest, so together they understood {place.clue_detail}."
    )


def infer_place(world: World, det_a: Entity, det_b: Entity, place: Place) -> None:
    world.say(
        f'"That points to {place.label}," {det_a.id} said. '
        f'"Then let\'s look there together," {det_b.id} replied.'
    )


def meet_helper(world: World, helper: Entity, place: Place, document_cfg: Document, motive: Motive) -> None:
    world.say(
        f"They hurried to {place.phrase}. {place.found_line}. "
        f"{helper.id} was there with {document_cfg.phrase} spread open, trying to {motive.want}."
    )


def kind_question(world: World, det_a: Entity, det_b: Entity, helper: Entity, response: Response) -> None:
    helper.memes["asked_kindly"] += 1
    for child in (det_a, det_b):
        child.memes["kindness"] += 1
    propagate(world, narrate=False)
    if response.id == "ask_kindly":
        world.say(
            f'{det_b.id} did not point or accuse. "{helper.id}, were you trying to help?" '
            f'{det_b.pronoun()} asked softly.'
        )
    else:
        world.say(
            f'After following the clue, {det_a.id} still kept {det_a.pronoun("possessive")} voice gentle. '
            f'"{helper.id}, please tell us what happened," {det_a.pronoun()} said.'
        )


def confession(world: World, helper: Entity, motive: Motive, document_cfg: Document) -> None:
    world.say(
        f"{helper.id}'s shoulders dropped. {motive.admission} "
        f'"I wanted to make a better version before anyone saw the messy one," '
        f"{helper.pronoun()} admitted."
    )
    if motive.id == "add_bullet_points":
        world.say(
            f'"I even started a bullet list so the steps would be easy to read," {helper.pronoun()} added.'
        )
    else:
        world.say(
            f"{helper.pronoun().capitalize()} held up the page, now cleaner and easier to read."
        )


def solve_together(world: World, cook: Entity, det_a: Entity, det_b: Entity, helper: Entity,
                   document: Entity, document_cfg: Document, motive: Motive) -> None:
    document.meters["missing"] = 0.0
    cook.meters["delayed"] = 0.0
    cook.memes["worry"] = 0.0
    for child in (det_a, det_b, helper):
        child.memes["relief"] += 1
        child.memes["trust"] += 1
        child.memes["teamwork"] += 1
    world.say(
        f"{cook.label_word.capitalize()} looked at the page, then at {helper.id}. "
        f'"Next time, ask first," {cook.pronoun()} said, "but thank you for caring enough to help."'
    )
    world.say(
        f"Then the four of them finished the work together. {det_a.id} straightened the papers, "
        f"{det_b.id} read the steps aloud, {helper.id} fixed the last line, and {cook.label_word} "
        f"pinned up the final {document_cfg.doc_word}."
    )
    world.say(
        f"Soon the lunch line moved again, the crispy lemon fillet was ready, and everyone could see "
        f"that teamwork and truth had solved the case."
    )
    world.say(
        f"On the counter, the neat page rested in plain sight, proving that a mystery can end kindly "
        f"when people listen, think, and tell the truth."
    )
    world.facts["lesson_text"] = motive.lesson


def tell(setting: Setting, document_cfg: Document, motive: Motive, place: Place, response: Response,
         detective_a_name: str = "June", detective_a_gender: str = "girl",
         detective_b_name: str = "Milo", detective_b_gender: str = "boy",
         helper_name: str = "Pip", helper_gender: str = "boy",
         cook_type: str = "mother") -> World:
    world = World()
    det_a = world.add(Entity(
        id=detective_a_name, kind="character", type=detective_a_gender, role="detective",
        traits=["careful", "observant"], label=detective_a_name,
    ))
    det_b = world.add(Entity(
        id=detective_b_name, kind="character", type=detective_b_gender, role="detective",
        traits=["steady", "thoughtful"], label=detective_b_name,
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        traits=["eager", "worried"], label=helper_name,
    ))
    cook = world.add(Entity(
        id="Cook", kind="character", type=cook_type, role="cook", label="the cook",
    ))
    document = world.add(Entity(
        id="document", kind="thing", type="paper", role="document",
        label=document_cfg.label, phrase=document_cfg.phrase,
    ))

    introduce(world, setting, det_a, det_b, cook, helper, document_cfg)
    world.para()
    discover_missing(world, cook, document, document_cfg)
    inspect_start(world, det_a, det_b, response)
    find_clue(world, det_a, det_b, place)

    if outcome_of(StoryParams(
        setting=setting.id,
        document=document_cfg.id,
        motive=motive.id,
        place=place.id,
        response=response.id,
        detective_a=detective_a_name,
        detective_a_gender=detective_a_gender,
        detective_b=detective_b_name,
        detective_b_gender=detective_b_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        cook=cook_type,
        seed=None,
    )) == "clue_then_confession":
        infer_place(world, det_a, det_b, place)

    world.para()
    meet_helper(world, helper, place, document_cfg, motive)
    kind_question(world, det_a, det_b, helper, response)
    confession(world, helper, motive, document_cfg)

    world.para()
    solve_together(world, cook, det_a, det_b, helper, document, document_cfg, motive)

    world.facts.update(
        setting=setting,
        document_cfg=document_cfg,
        motive=motive,
        place=place,
        response=response,
        detective_a=det_a,
        detective_b=det_b,
        helper=helper,
        cook=cook,
        document=document,
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            document=document_cfg.id,
            motive=motive.id,
            place=place.id,
            response=response.id,
            detective_a=detective_a_name,
            detective_a_gender=detective_a_gender,
            detective_b=detective_b_name,
            detective_b_gender=detective_b_gender,
            helper=helper_name,
            helper_gender=helper_gender,
            cook=cook_type,
            seed=None,
        )),
        solved=document.meters["missing"] < THRESHOLD,
        kindness_opened_honesty=helper.memes["honesty"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor_stall": Setting(
        id="harbor_stall",
        place="the harbor market",
        stall_name="Nana Fern's Lunch Stall",
        scene="salt air fluttered the striped awning and gulls called above the boats",
        tags={"market", "harbor"},
    ),
    "river_cart": Setting(
        id="river_cart",
        place="the river walk",
        stall_name="Willow Cart",
        scene="bright river light danced on the water and little bells chimed on the cart roof",
        tags={"river", "cart"},
    ),
    "pier_kiosk": Setting(
        id="pier_kiosk",
        place="the old pier",
        stall_name="Pier Lantern Kitchen",
        scene="wooden boards creaked softly while a breeze whisked the smell of lunch down the pier",
        tags={"pier", "kiosk"},
    ),
}

DOCUMENTS = {
    "recipe_card": Document(
        id="recipe_card",
        label="recipe card",
        phrase="the recipe card",
        purpose="the cook followed its steps for the special lunch",
        line="the steps mattered",
        doc_word="recipe card",
        tags={"recipe"},
    ),
    "menu_sheet": Document(
        id="menu_sheet",
        label="menu sheet",
        phrase="the menu sheet",
        purpose="it showed customers the clean version of the day's special",
        line="the menu mattered",
        doc_word="menu sheet",
        tags={"menu"},
    ),
    "task_page": Document(
        id="task_page",
        label="task page",
        phrase="the task page",
        purpose="it kept the helpers' jobs in order before the rush began",
        line="the jobs mattered",
        doc_word="task page",
        tags={"tasks"},
    ),
}

MOTIVES = {
    "rewrite_neatly": Motive(
        id="rewrite_neatly",
        want="copy the words more neatly",
        version_line="a neat version",
        admission='"I only borrowed it because the writing looked messy." ',
        lesson="Helping is good, but it is better to ask before taking someone else's paper.",
        tags={"neat", "helping"},
    ),
    "fix_spelling": Motive(
        id="fix_spelling",
        want="fix a spelling mistake",
        version_line="a corrected version",
        admission='"I saw a word that looked wrong and wanted to fix it." ',
        lesson="Telling the truth quickly makes it easier for everyone to solve the problem.",
        tags={"spelling", "truth"},
    ),
    "add_bullet_points": Motive(
        id="add_bullet_points",
        want="turn the notes into a bullet list",
        version_line="a bullet-list version",
        admission='"I thought bullet points would help everyone read faster." ',
        lesson="A smart idea works best when you share it openly and let the team help.",
        tags={"bullet", "planning"},
    ),
}

PLACES = {
    "office_desk": Place(
        id="office_desk",
        label="the little office desk",
        phrase="the little office desk behind the curtain",
        clue="a trail of pencil shavings beside a blue stubby pencil",
        clue_detail="someone had been writing in a hurry",
        found_line="On the desk sat a half-used eraser and one careful page after another",
        supports={"recipe_card", "menu_sheet", "task_page"},
        tags={"desk", "pencil"},
    ),
    "supply_shelf": Place(
        id="supply_shelf",
        label="the supply shelf",
        phrase="the supply shelf near the stack of signs",
        clue="a strip of fresh tape stuck to the floor",
        clue_detail="someone had carried paper near the signs and labels",
        found_line="Between boxes of napkins and string, a page was being lined up very carefully",
        supports={"menu_sheet", "task_page"},
        tags={"shelf", "tape"},
    ),
    "window_crate": Place(
        id="window_crate",
        label="the sunny window crate",
        phrase="the sunny window crate beside the herb pots",
        clue="a lonely pink eraser crumb and a page corner fluttering in the light",
        clue_detail="someone wanted a quiet place to read and correct words",
        found_line="By the crate, in the calm patch of sunlight, a paper lay beside a careful little stack of notes",
        supports={"recipe_card", "task_page"},
        tags={"window", "eraser"},
    ),
}

DOCUMENT_MOTIVES = {
    "recipe_card": {"rewrite_neatly", "fix_spelling"},
    "menu_sheet": {"rewrite_neatly", "fix_spelling", "add_bullet_points"},
    "task_page": {"rewrite_neatly", "add_bullet_points"},
}

RESPONSES = {
    "ask_kindly": Response(
        id="ask_kindly",
        sense=3,
        style="kind",
        start_line='Instead of blaming anyone, they decided to ask calm questions and look for careful clues.',
        qa_text="They asked gentle questions first and kept the search kind.",
        tags={"kindness", "honesty"},
    ),
    "follow_clues": Response(
        id="follow_clues",
        sense=3,
        style="detective",
        start_line='They agreed to follow the smallest clue first, then speak kindly when they found the person.',
        qa_text="They followed the clue trail together and then spoke gently.",
        tags={"clues", "teamwork"},
    ),
    "blame_loudly": Response(
        id="blame_loudly",
        sense=1,
        style="rough",
        start_line='They stomped around ready to blame the first person they saw.',
        qa_text="They shouted accusations.",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["June", "Nora", "Mia", "Ava", "Lila", "Ruby", "Tess", "Ivy"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Finn", "Leo", "Sam", "Eli", "Otto"]


# ---------------------------------------------------------------------------
# Per-world params.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    document: str
    motive: str
    place: str
    response: str
    detective_a: str
    detective_a_gender: str
    detective_b: str
    detective_b_gender: str
    helper: str
    helper_gender: str
    cook: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective pays close attention, asks careful questions, and uses clues to understand what happened."
    )],
    "fillet": [(
        "What is a fillet?",
        "A fillet is a piece of fish or meat with the bones removed, so it is easier to cook and eat."
    )],
    "version": [(
        "What does version mean?",
        "A version is one form of something. You can make a new version if you fix mistakes or make it neater."
    )],
    "bullet": [(
        "What is a bullet list?",
        "A bullet list is a set of short points, each marked with a dot or symbol, so the ideas are easy to read."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out, like a footprint, a note, or a pencil shaving."
    )],
    "teamwork": [(
        "Why is teamwork helpful in solving a problem?",
        "Teamwork helps because one person may notice something another person misses. When people share ideas, they solve problems faster and more fairly."
    )],
    "honesty": [(
        "Why is honesty important when there is a mistake?",
        "Honesty helps people fix the problem quickly. Telling the truth also helps others trust you."
    )],
}
KNOWLEDGE_ORDER = ["detective", "fillet", "version", "bullet", "clue", "teamwork", "honesty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det_a = f["detective_a"]
    det_b = f["detective_b"]
    document = f["document_cfg"]
    motive = f["motive"]
    return [
        'Write a gentle detective story for a 3-to-5-year-old that includes the words "fillet", "version", and "bullet".',
        f"Tell a child-friendly mystery where {det_a.id} and {det_b.id} solve the case of a missing {document.label} through teamwork and kind thinking.",
        f"Write a short story in which a worried helper borrows a paper to make {motive.version_line}, and the ending teaches honesty and teamwork.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det_a = f["detective_a"]
    det_b = f["detective_b"]
    helper = f["helper"]
    cook = f["cook"]
    document = f["document_cfg"]
    motive = f["motive"]
    place = f["place"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two child detectives, {det_a.id} and {det_b.id}, a worried helper named {helper.id}, and {cook.label_word} at the lunch stall."
        ),
        (
            f"What was missing at the stall?",
            f"The missing thing was {document.phrase}. It mattered because {document.purpose}."
        ),
        (
            "What clues helped solve the mystery?",
            f"The detectives noticed {place.clue}. Each child spotted part of the clue, and together they understood what it meant."
        ),
        (
            f"How did {det_a.id} and {det_b.id} solve the problem?",
            f"{response.qa_text} That helped them reach {place.label}, where they found {helper.id} with the paper."
        ),
        (
            f"Why did {helper.id} take the paper?",
            f"{helper.id} was not trying to be mean. {helper.pronoun().capitalize()} had borrowed it to {motive.want} and make {motive.version_line}."
        ),
    ]
    if outcome == "quick_confession":
        qa.append((
            f"Why did {helper.id} tell the truth so quickly?",
            f"{helper.id} told the truth quickly because the detectives asked in a gentle way instead of accusing {helper.pronoun('object')}. Kind words made it feel safe to be honest."
        ))
    else:
        qa.append((
            "Why was teamwork important in this mystery?",
            f"Teamwork mattered because one detective noticed the small clue and the other understood where it pointed. They solved the case faster by thinking together."
        ))
    qa.append((
        "What lesson did everyone learn at the end?",
        f"They learned that helping is best when you ask first and tell the truth. Because they worked together kindly, the problem was fixed and the stall could open on time."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "fillet", "version", "clue", "teamwork", "honesty"}
    if world.facts["motive"].id == "add_bullet_points":
        tags.add("bullet")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {entity.id:10} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supports_motive(D, M) :- document_motive(D, M).
supports_place(P, D)  :- place_document(P, D).

valid(S, D, M, P) :- setting(S), document(D), motive(M), place(P),
                      supports_motive(D, M), supports_place(P, D).

sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.

quick_confession :- chosen_response(ask_kindly), chosen_motive(fix_spelling).
clue_then_confession :- chosen_response(follow_clues).
clue_then_confession :- chosen_response(ask_kindly), chosen_motive(M), M != fix_spelling.

outcome(quick_confession) :- quick_confession.
outcome(clue_then_confession) :- clue_then_confession, not quick_confession.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for document_id in DOCUMENTS:
        lines.append(asp.fact("document", document_id))
    for motive_id in MOTIVES:
        lines.append(asp.fact("motive", motive_id))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    for document_id, motives in DOCUMENT_MOTIVES.items():
        for motive_id in sorted(motives):
            lines.append(asp.fact("document_motive", document_id, motive_id))
    for place_id, place in PLACES.items():
        for document_id in sorted(place.supports):
            lines.append(asp.fact("place_document", place_id, document_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(atom[0] for atom in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_motive", params.motive),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sens = set(asp_sensible())
    python_sens = {resp.id for resp in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke test ordinary generation.
    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a gentle detective mystery at a food stall. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--document", choices=DOCUMENTS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--cook", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(args.response))
    if args.document and args.motive and args.place:
        if not valid_combo(DOCUMENTS[args.document], MOTIVES[args.motive], PLACES[args.place]):
            raise StoryError(explain_combo_rejection(DOCUMENTS[args.document], MOTIVES[args.motive], PLACES[args.place]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.document is None or combo[1] == args.document)
        and (args.motive is None or combo[2] == args.motive)
        and (args.place is None or combo[3] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, document_id, motive_id, place_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(resp.id for resp in sensible_responses()))
    cook_type = args.cook or rng.choice(["mother", "father"])

    detective_a_gender = rng.choice(["girl", "boy"])
    detective_b_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])

    detective_a = _pick_name(rng, detective_a_gender)
    detective_b = _pick_name(rng, detective_b_gender, avoid=detective_a)
    helper = _pick_name(rng, helper_gender, avoid=detective_a if detective_a_gender == helper_gender else "")

    return StoryParams(
        setting=setting_id,
        document=document_id,
        motive=motive_id,
        place=place_id,
        response=response_id,
        detective_a=detective_a,
        detective_a_gender=detective_a_gender,
        detective_b=detective_b,
        detective_b_gender=detective_b_gender,
        helper=helper,
        helper_gender=helper_gender,
        cook=cook_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        document = DOCUMENTS[params.document]
        motive = MOTIVES[params.motive]
        place = PLACES[params.place]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]}.)") from exc

    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))
    if not valid_combo(document, motive, place):
        raise StoryError(explain_combo_rejection(document, motive, place))

    world = tell(
        setting=setting,
        document_cfg=document,
        motive=motive,
        place=place,
        response=response,
        detective_a_name=params.detective_a,
        detective_a_gender=params.detective_a_gender,
        detective_b_name=params.detective_b,
        detective_b_gender=params.detective_b_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        cook_type=params.cook,
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


CURATED = [
    StoryParams(
        setting="harbor_stall",
        document="recipe_card",
        motive="fix_spelling",
        place="window_crate",
        response="ask_kindly",
        detective_a="June",
        detective_a_gender="girl",
        detective_b="Milo",
        detective_b_gender="boy",
        helper="Pip",
        helper_gender="boy",
        cook="mother",
        seed=None,
    ),
    StoryParams(
        setting="river_cart",
        document="menu_sheet",
        motive="rewrite_neatly",
        place="office_desk",
        response="follow_clues",
        detective_a="Ruby",
        detective_a_gender="girl",
        detective_b="Theo",
        detective_b_gender="boy",
        helper="Ivy",
        helper_gender="girl",
        cook="father",
        seed=None,
    ),
    StoryParams(
        setting="pier_kiosk",
        document="task_page",
        motive="add_bullet_points",
        place="supply_shelf",
        response="follow_clues",
        detective_a="Nora",
        detective_a_gender="girl",
        detective_b="Finn",
        detective_b_gender="boy",
        helper="Otto",
        helper_gender="boy",
        cook="mother",
        seed=None,
    ),
    StoryParams(
        setting="harbor_stall",
        document="menu_sheet",
        motive="add_bullet_points",
        place="office_desk",
        response="ask_kindly",
        detective_a="Ava",
        detective_a_gender="girl",
        detective_b="Eli",
        detective_b_gender="boy",
        helper="Lila",
        helper_gender="girl",
        cook="father",
        seed=None,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, document, motive, place) combos:\n")
        for setting_id, document_id, motive_id, place_id in combos:
            print(f"  {setting_id:12} {document_id:11} {motive_id:17} {place_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        tries = 0
        while len(samples) < args.n and tries < max(50, args.n * 50):
            seed = base_seed + tries
            tries += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.detective_a} & {p.detective_b}: {p.document} / {p.motive} "
                f"at {p.setting} ({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
