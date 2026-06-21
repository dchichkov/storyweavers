#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/abdc_conflict_bad_ending_detective_story.py
======================================================================

A standalone storyworld for a child-scale detective story built around the clue
word "abdc". In this tiny domain, a young detective and a helper investigate a
missing object near a row of labeled storage spaces. A clue reading "abdc"
appears because two labels were swapped. The helper wants to inspect the spaces
carefully; the lead detective may instead accuse the helper too soon. That
creates the central conflict, and in the bad ending the accusation hurts the
friendship while the case stays unsolved until a grown-up finds the object
later.

The model keeps a small world state with physical meters and emotional memes,
uses a reasonableness gate plus an inline ASP twin, and can generate both
careful and unhappy variants.

Run it
------
    python storyworlds/worlds/gpt-5.4/abdc_conflict_bad_ending_detective_story.py
    python storyworlds/worlds/gpt-5.4/abdc_conflict_bad_ending_detective_story.py --decision accuse
    python storyworlds/worlds/gpt-5.4/abdc_conflict_bad_ending_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/abdc_conflict_bad_ending_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/abdc_conflict_bad_ending_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/abdc_conflict_bad_ending_detective_story.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so three dirname() calls
# reach the storyworlds/ package directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "librarian": "librarian",
            "teacher": "teacher",
            "aunt": "aunt",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    adult_type: str
    adult_label: str
    storage_kind: str
    storage_phrase: str
    supports: set[str] = field(default_factory=set)
    tone: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    size: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    medium: str
    needs_labels: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hider:
    id: str
    label: str
    relation: str
    method: str
    hides_in: str
    fits_in: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Decision:
    id: str
    sense: int
    careful: bool
    line: str
    tags: set[str] = field(default_factory=set)


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


def _r_conflict(world: World) -> list[str]:
    lead = world.entities.get("lead")
    helper = world.entities.get("helper")
    if not lead or not helper:
        return []
    if lead.memes["accusing"] < THRESHOLD or helper.memes["hurt"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    return ["__conflict__"]


def _r_bad_ending(world: World) -> list[str]:
    casefile = world.entities.get("casefile")
    lead = world.entities.get("lead")
    helper = world.entities.get("helper")
    item = world.entities.get("item")
    if not casefile or not lead or not helper or not item:
        return []
    if lead.memes["conflict"] < THRESHOLD or item.meters["found"] >= THRESHOLD:
        return []
    sig = ("bad_ending",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    casefile.meters["cold"] += 1
    lead.memes["regret"] += 1
    helper.memes["distance"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="bad_ending", tag="social", apply=_r_bad_ending),
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


def valid_combo(setting: Setting, item: MissingItem, clue: Clue, hider: Hider) -> bool:
    return (
        item.size in setting.supports
        and item.size in hider.fits_in
        and (not clue.needs_labels or setting.storage_kind in {"cubbies", "drawers", "mail slots"})
        and hider.hides_in == "c"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for cid, clue in CLUES.items():
                for hid, hider in HIDERS.items():
                    if valid_combo(setting, item, clue, hider):
                        combos.append((sid, iid, cid, hid))
    return combos


def sensible_decisions() -> list[Decision]:
    return [d for d in DECISIONS.values() if d.sense >= SENSE_MIN]


def explain_rejection(setting: Setting, item: MissingItem, clue: Clue, hider: Hider) -> str:
    if item.size not in setting.supports:
        return (
            f"(No story: {item.phrase} is too large for {setting.storage_phrase}. "
            f"The detective clue only makes sense when the missing thing could really fit there.)"
        )
    if item.size not in hider.fits_in:
        return (
            f"(No story: {hider.label} would not sensibly hide {item.phrase} in the {setting.storage_kind}. "
            f"Pick a smaller object or a hider who plays small tricks.)"
        )
    if clue.needs_labels and setting.storage_kind not in {"cubbies", "drawers", "mail slots"}:
        return (
            f"(No story: the clue '{clue.text}' only makes sense where labeled spaces can be swapped.)"
        )
    if hider.hides_in != "c":
        return "(No story: this world expects the clue to point toward the real C compartment.)"
    return "(No story: this combination does not make a reasonable detective setup.)"


def explain_decision(decision_id: str) -> str:
    decision = DECISIONS[decision_id]
    better = ", ".join(sorted(d.id for d in sensible_decisions()))
    return (
        f"(Refusing decision '{decision_id}': it scores too low on detective sense "
        f"(sense={decision.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_branch(world: World, decision: Decision) -> dict:
    sim = world.copy()
    lead = sim.get("lead")
    helper = sim.get("helper")
    item = sim.get("item")
    if decision.id == "accuse":
        lead.memes["accusing"] += 1
        helper.memes["hurt"] += 1
        propagate(sim, narrate=False)
        return {
            "found": item.meters["found"] >= THRESHOLD,
            "hurt": helper.memes["hurt"] >= THRESHOLD,
            "cold_case": sim.get("casefile").meters["cold"] >= THRESHOLD,
        }
    _inspect_storage(sim, narrate=False)
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "hurt": helper.memes["hurt"] >= THRESHOLD,
        "cold_case": sim.get("casefile").meters["cold"] >= THRESHOLD,
    }


def _inspect_storage(world: World, narrate: bool = True) -> None:
    item = world.get("item")
    lead = world.get("lead")
    helper = world.get("helper")
    if narrate:
        world.say(
            f"Together they checked the labeled spaces in the odd order from the clue: A, B, D, then C."
        )
    lead.memes["patience"] += 1
    helper.memes["hope"] += 1
    if world.facts.get("true_spot") == "c":
        item.meters["found"] += 1
        item.meters["hidden"] = 0.0
        lead.memes["relief"] += 1
        helper.memes["relief"] += 1
        helper.memes["trust"] += 1


def introduce(world: World, lead: Entity, helper: Entity, adult: Entity, item: MissingItem) -> None:
    world.say(
        f"{lead.id} liked calling {lead.pronoun('possessive')} notebook a detective book, "
        f"because every blank page looked ready for a mystery."
    )
    world.say(
        f"That afternoon, {lead.id} and {helper.id} were in {world.setting.place}. "
        f"{world.setting.tone}"
    )
    world.say(
        f"When they reached for {item.phrase}, it was gone."
    )
    world.say(
        f'"Case of the missing {item.label}," {lead.id} whispered, and {helper.id} nodded at once.'
    )
    world.facts["adult_name"] = adult.label_word


def discover_clue(world: World, lead: Entity, helper: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["seen"] += 1
    lead.memes["curious"] += 1
    helper.memes["curious"] += 1
    world.say(
        f"Beside {world.setting.storage_phrase} lay {clue.medium} with the letters "
        f'"{clue.text}" on it.'
    )
    world.say(
        f'{helper.id} frowned. "That looks mixed up. C and D might have traded places."'
    )


def suspect_hider(world: World, lead: Entity, helper: Entity, hider: Hider) -> None:
    world.say(
        f"{lead.id} looked toward the door and remembered {hider.label}, who had {hider.method} earlier."
    )
    world.say(
        f'"Or maybe {helper.id} moved the labels by mistake," {lead.pronoun()} said, a little too fast.'
    )
    lead.memes["suspicion"] += 1
    helper.memes["uneasy"] += 1


def helper_warning(world: World, lead: Entity, helper: Entity, decision: Decision) -> None:
    pred = predict_branch(world, decision)
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_cold"] = pred["cold_case"]
    if decision.id == "accuse":
        helper.memes["caution"] += 1
        world.say(
            f'"Please do not pin it on me before we check," {helper.id} said. '
            f'"A real detective looks first and blames last."'
        )
    else:
        world.say(
            f'"The clue is telling us where to look," {helper.id} said. '
            f'"Let the letters lead us before our tempers do."'
        )


def accuse_branch(world: World, lead: Entity, helper: Entity, adult: Entity, item: MissingItem) -> None:
    lead.memes["accusing"] += 1
    helper.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{lead.id} shut the notebook with a snap. "You touched the labels this morning," '
        f'{lead.pronoun()} said. "You must have hidden the {item.label}."'
    )
    world.say(
        f"{helper.id}'s face went hot and still. {helper.pronoun().capitalize()} took one step back and "
        f"did not answer right away."
    )
    world.say(
        f'"I was helping, not stealing," {helper.id} said at last.'
    )
    world.say(
        f"{adult.label_word.capitalize()} looked over from across {world.setting.place}, but the sharp little silence "
        f"had already filled the room."
    )


def unresolved_ending(world: World, lead: Entity, helper: Entity, adult: Entity, item: MissingItem) -> None:
    casefile = world.get("casefile")
    casefile.meters["closed"] = 0.0
    item.meters["found"] = 0.0
    item.meters["hidden"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"No one checked the {world.setting.storage_kind} in the clue order after that. "
        f"The case simply cooled where it stood."
    )
    world.say(
        f"Later, {adult.label_word} found {item.phrase} tucked inside the C space, exactly where the mixed-up "
        f'letters had pointed all along.'
    )
    world.say(
        f"But by then {helper.id} had gone home early, and {lead.id}'s detective book felt heavy in "
        f"{lead.pronoun('possessive')} hands."
    )
    world.say(
        f"The mystery was solved too late to feel bright. What stayed with {lead.id} was the look on "
        f"{helper.id}'s face when trust had been treated like a clue to push aside."
    )
    world.facts["outcome"] = "bad"
    world.facts["solved_in_time"] = False


def inspect_branch(world: World, lead: Entity, helper: Entity, adult: Entity, item: MissingItem) -> None:
    _inspect_storage(world, narrate=True)
    world.say(
        f"Inside the C space sat {item.phrase}, hidden under a folded paper star."
    )
    world.say(
        f'{lead.id} let out a breath. "The clue was a map, not a name," {lead.pronoun()} said.'
    )
    world.say(
        f"{helper.id} smiled, though only after a moment. The case was small, but the lesson in it was not."
    )
    world.say(
        f"Together they carried the {item.label} back through {world.setting.place}, and the detective book felt light again."
    )
    world.get("casefile").meters["closed"] += 1
    world.facts["outcome"] = "good"
    world.facts["solved_in_time"] = True


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    clue_cfg: Clue,
    hider_cfg: Hider,
    decision_cfg: Decision,
    lead_name: str = "Nora",
    lead_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    adult_type: str = "teacher",
) -> World:
    world = World(setting)
    lead = world.add(Entity(id="lead", kind="character", type=lead_gender, label=lead_name, phrase=lead_name, role="lead"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, phrase=helper_name, role="helper"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=setting.adult_label, role="adult"))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, role="missing"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=clue_cfg.text, phrase=clue_cfg.medium, tags=set(clue_cfg.tags)))
    world.add(Entity(id="casefile", kind="thing", type="notebook", label="case file", phrase="the little case file"))

    lead.attrs["name"] = lead_name
    helper.attrs["name"] = helper_name
    adult.attrs["setting"] = setting.id

    item.meters["hidden"] += 1
    world.facts["true_spot"] = hider_cfg.hides_in
    world.facts["lead_name"] = lead_name
    world.facts["helper_name"] = helper_name
    world.facts["item_cfg"] = item_cfg
    world.facts["clue_cfg"] = clue_cfg
    world.facts["hider_cfg"] = hider_cfg
    world.facts["decision_cfg"] = decision_cfg

    introduce(world, lead, helper, adult, item_cfg)
    world.para()
    discover_clue(world, lead, helper, clue_cfg)
    suspect_hider(world, lead, helper, hider_cfg)
    helper_warning(world, lead, helper, decision_cfg)
    world.para()

    if decision_cfg.id == "accuse":
        accuse_branch(world, lead, helper, adult, item_cfg)
        world.para()
        unresolved_ending(world, lead, helper, adult, item_cfg)
    else:
        inspect_branch(world, lead, helper, adult, item_cfg)

    world.facts.update(
        lead=lead,
        helper=helper,
        adult=adult,
        item=item,
        clue=clue,
        setting=setting,
        item_found=item.meters["found"] >= THRESHOLD,
        conflict=lead.memes["conflict"] >= THRESHOLD or helper.memes["hurt"] >= THRESHOLD,
        case_closed=world.get("casefile").meters["closed"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    item: str
    clue: str
    hider: str
    decision: str
    lead_name: str
    lead_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        adult_type="teacher",
        adult_label="the teacher",
        storage_kind="cubbies",
        storage_phrase="the row of lettered cubbies",
        supports={"small", "flat"},
        tone="Sunlight lay across the reading rug, and the cubby labels shone like tiny brass clues.",
        tags={"school", "cubbies"},
    ),
    "library": Setting(
        id="library",
        place="the library corner",
        adult_type="librarian",
        adult_label="the librarian",
        storage_kind="mail slots",
        storage_phrase="the neat mail slots by the window",
        supports={"small", "flat"},
        tone="Everything was hushed except the soft shiver of pages turning.",
        tags={"library", "slots"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the attic clubhouse",
        adult_type="aunt",
        adult_label="their aunt",
        storage_kind="drawers",
        storage_phrase="the painted drawers under the sloping roof",
        supports={"small", "flat"},
        tone="Dusty light came through the round window and made the attic feel full of secrets.",
        tags={"clubhouse", "drawers"},
    ),
}

ITEMS = {
    "badge": MissingItem(
        id="badge",
        label="badge",
        phrase="the brass detective badge",
        size="small",
        use="for pinning to a detective coat",
        tags={"detective", "badge"},
    ),
    "notebook": MissingItem(
        id="notebook",
        label="notebook",
        phrase="the blue clue notebook",
        size="flat",
        use="for writing down clues",
        tags={"detective", "notebook"},
    ),
    "magnifier": MissingItem(
        id="magnifier",
        label="magnifying glass",
        phrase="the round magnifying glass",
        size="small",
        use="for looking at tiny clues",
        tags={"detective", "magnifying"},
    ),
    "map": MissingItem(
        id="map",
        label="map",
        phrase="the folded treasure map",
        size="flat",
        use="for following secret paths",
        tags={"map", "detective"},
    ),
}

CLUES = {
    "paper": Clue(
        id="paper",
        text="abdc",
        medium="a paper slip",
        needs_labels=True,
        tags={"clue", "letters", "abdc"},
    ),
    "chalk": Clue(
        id="chalk",
        text="abdc",
        medium="a chalk scrawl",
        needs_labels=True,
        tags={"clue", "letters", "abdc"},
    ),
}

HIDERS = {
    "class_clown": Hider(
        id="class_clown",
        label="Milo from the next table",
        relation="peer",
        method="been grinning over a paper star craft",
        hides_in="c",
        fits_in={"small", "flat"},
        tags={"prank", "child"},
    ),
    "cousin": Hider(
        id="cousin",
        label="Rae, the older cousin",
        relation="family",
        method="been boasting about making the best riddles",
        hides_in="c",
        fits_in={"small", "flat"},
        tags={"prank", "family"},
    ),
    "neighbor": Hider(
        id="neighbor",
        label="the neighbor girl Tessa",
        relation="friend",
        method="been laughing over a secret game",
        hides_in="c",
        fits_in={"small", "flat"},
        tags={"prank", "friend"},
    ),
}

DECISIONS = {
    "inspect": Decision(
        id="inspect",
        sense=3,
        careful=True,
        line="check the clue before blaming anyone",
        tags={"evidence", "careful"},
    ),
    "accuse": Decision(
        id="accuse",
        sense=2,
        careful=False,
        line="accuse the helper too soon",
        tags={"conflict", "bad_ending"},
    ),
    "storm_off": Decision(
        id="storm_off",
        sense=1,
        careful=False,
        line="refuse to investigate and storm off",
        tags={"conflict"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Anna", "Rose", "Clara"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Jack", "Eli"]


CURATED = [
    StoryParams(
        setting="classroom",
        item="badge",
        clue="paper",
        hider="class_clown",
        decision="accuse",
        lead_name="Nora",
        lead_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
    ),
    StoryParams(
        setting="library",
        item="notebook",
        clue="chalk",
        hider="neighbor",
        decision="inspect",
        lead_name="Max",
        lead_gender="boy",
        helper_name="Lily",
        helper_gender="girl",
    ),
    StoryParams(
        setting="clubhouse",
        item="map",
        clue="paper",
        hider="cousin",
        decision="accuse",
        lead_name="Ava",
        lead_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
    ),
    StoryParams(
        setting="classroom",
        item="magnifier",
        clue="paper",
        hider="class_clown",
        decision="inspect",
        lead_name="Leo",
        lead_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
    ),
]


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks careful questions, and checks what is true before making a guess."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that points toward an answer. A good detective does not grab the first idea and stop there."
        )
    ],
    "letters": [
        (
            "Why does the order of letters matter?",
            "The order matters because changing letters around can change what they mean. In a mystery, one mixed-up order can point to the right place or the wrong idea."
        )
    ],
    "abdc": [
        (
            "Why is 'abdc' unusual?",
            "It looks unusual because many children expect A, B, C, D in that order. When the C and D are swapped, it can be a clue that something has been moved."
        )
    ],
    "cubbies": [
        (
            "What is a cubby?",
            "A cubby is a small open storage space where you can keep little things like notebooks or badges."
        )
    ],
    "drawers": [
        (
            "What is a drawer?",
            "A drawer is a box-shaped space you pull open to keep things inside."
        )
    ],
    "slots": [
        (
            "What is a mail slot shelf?",
            "It is a little shelf with separate spaces, so each paper or notebook has its own place."
        )
    ],
    "evidence": [
        (
            "Why should you check evidence before blaming someone?",
            "Because blaming first can hurt feelings and still leave the real problem unsolved. Evidence helps you be fair."
        )
    ],
    "bad_ending": [
        (
            "Why can a quick accusation make things worse?",
            "A quick accusation can break trust before the truth is known. Even if the mystery is solved later, the hurt can stay."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "letters", "abdc", "cubbies", "drawers", "slots", "evidence", "bad_ending"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    setting = f["setting"]
    decision = f["decision_cfg"]
    if decision.id == "accuse":
        return [
            'Write a short detective story for a 3-to-5-year-old that includes the word "abdc" and ends sadly.',
            f"Tell a child-friendly mystery in {setting.place} where two young detectives argue over the clue 'abdc' and one of them accuses the other too soon.",
            f"Write a gentle bad-ending detective story about a missing {item.label}, a conflict between friends, and a clue that was misunderstood.",
        ]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the word "abdc".',
        f"Tell a child-friendly mystery in {setting.place} where two young detectives disagree at first but solve the missing {item.label} by following the clue carefully.",
        f"Write a simple detective story about a clue that looks mixed up, a brief conflict, and a careful search that fixes the mistake.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    setting = f["setting"]
    item_cfg = f["item_cfg"]
    decision = f["decision_cfg"]
    clue_cfg = f["clue_cfg"]
    adult = f["adult"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.label} and {helper.label}, two children pretending to be detectives in {setting.place}. A grown-up nearby watched the mystery unfold."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item_cfg.phrase}. It mattered because the children used it for their detective game."
        ),
        (
            "What clue did they find?",
            f"They found {clue_cfg.medium} with the letters '{clue_cfg.text}' on it. The clue looked strange because the letters did not follow the usual order."
        ),
    ]
    if decision.id == "accuse":
        qa.extend(
            [
                (
                    f"Why did {lead.label} and {helper.label} argue?",
                    f"They argued because {lead.label} treated the clue like a reason to blame {helper.label} before checking the storage spaces. {helper.label} wanted to look for evidence first, so the mystery turned into a hurtful conflict."
                ),
                (
                    "How did the story end?",
                    f"It ended sadly. The missing {item_cfg.label} was found later in the C space, but by then {helper.label}'s feelings had already been hurt and the friendship felt shaky."
                ),
                (
                    f"What should {lead.label} have done instead?",
                    f"{lead.label} should have followed the clue and checked the labeled spaces before making an accusation. The letters were pointing toward the hiding place, not proving that a friend was guilty."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    "How did they solve the mystery?",
                    f"They followed the odd order from the clue and checked A, B, D, and then C. That careful search led them to the missing {item_cfg.label}."
                ),
                (
                    f"Did {lead.label} and {helper.label} stay upset?",
                    f"No. They had a brief disagreement, but solving the mystery together helped the sharp feeling melt away."
                ),
                (
                    "What changed by the end?",
                    f"At the end, the clue made sense and the missing thing was back where the children could use it again. The story shows that patience can turn a tense moment into a solved case."
                ),
            ]
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["item_cfg"].tags) | set(world.facts["clue_cfg"].tags)
    tags |= set(world.facts["decision_cfg"].tags)
    tags.add("detective")
    tags.add("clue")
    tags.add("letters")
    storage_kind = world.facts["setting"].storage_kind
    if storage_kind == "cubbies":
        tags.add("cubbies")
    elif storage_kind == "drawers":
        tags.add("drawers")
    else:
        tags.add("slots")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def outcome_of(params: StoryParams) -> str:
    decision = DECISIONS[params.decision]
    return "bad" if decision.id == "accuse" else "good"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S, I, C, H) :- setting(S), item(I), clue(C), hider(H),
                     supports(S, Size), item_size(I, Size),
                     fits(H, Size), hides_in(H, c),
                     needs_labels(C), labeled_storage(S).

% --- decision reasonableness ----------------------------------------------
sensible_decision(D) :- decision(D), sense(D, V), sense_min(M), V >= M.

% --- outcome model ---------------------------------------------------------
outcome(bad)  :- chosen_decision(accuse).
outcome(good) :- chosen_decision(D), decision(D), D != accuse.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.storage_kind in {"cubbies", "drawers", "mail slots"}:
            lines.append(asp.fact("labeled_storage", sid))
        for size in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, size))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_size", iid, item.size))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.needs_labels:
            lines.append(asp.fact("needs_labels", cid))
    for hid, hider in HIDERS.items():
        lines.append(asp.fact("hider", hid))
        lines.append(asp.fact("hides_in", hid, hider.hides_in))
        for size in sorted(hider.fits_in):
            lines.append(asp.fact("fits", hid, size))
    for did, decision in DECISIONS.items():
        lines.append(asp.fact("decision", did))
        lines.append(asp.fact("sense", did, decision.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_decisions() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_decision/1."))
    return sorted(d for (d,) in asp.atoms(model, "sensible_decision"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_decision", params.decision)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child detective, a mixed-up clue, and a choice between evidence and accusation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hider", choices=HIDERS)
    ap.add_argument("--decision", choices=DECISIONS)
    ap.add_argument("--lead-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.decision and DECISIONS[args.decision].sense < SENSE_MIN and args.decision != "accuse":
        raise StoryError(explain_decision(args.decision))

    if args.setting and args.item and args.clue and args.hider:
        setting = SETTINGS[args.setting]
        item = ITEMS[args.item]
        clue = CLUES[args.clue]
        hider = HIDERS[args.hider]
        if not valid_combo(setting, item, clue, hider):
            raise StoryError(explain_rejection(setting, item, clue, hider))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
        and (args.hider is None or combo[3] == args.hider)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, clue_id, hider_id = rng.choice(sorted(combos))
    decision_id = args.decision or rng.choice(sorted(d.id for d in DECISIONS.values() if d.id in {"inspect", "accuse"}))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or _pick_name(rng, lead_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=lead_name)

    return StoryParams(
        setting=setting_id,
        item=item_id,
        clue=clue_id,
        hider=hider_id,
        decision=decision_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hider not in HIDERS:
        raise StoryError(f"(Unknown hider: {params.hider})")
    if params.decision not in DECISIONS:
        raise StoryError(f"(Unknown decision: {params.decision})")

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    clue = CLUES[params.clue]
    hider = HIDERS[params.hider]
    decision = DECISIONS[params.decision]

    if not valid_combo(setting, item, clue, hider):
        raise StoryError(explain_rejection(setting, item, clue, hider))
    if decision.sense < SENSE_MIN and decision.id != "accuse":
        raise StoryError(explain_decision(decision.id))

    world = tell(
        setting=setting,
        item_cfg=item,
        clue_cfg=clue,
        hider_cfg=hider,
        decision_cfg=decision,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=setting.adult_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))

    py_sensible = {d.id for d in sensible_decisions()}
    asp_sensible = set(asp_sensible_decisions())
    if py_sensible == asp_sensible:
        print(f"OK: sensible decisions match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible decisions: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible_decision/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible decisions: {', '.join(asp_sensible_decisions())}\n")
        print(f"{len(combos)} compatible (setting, item, clue, hider) combos:\n")
        for setting, item, clue, hider in combos:
            print(f"  {setting:10} {item:10} {clue:8} {hider}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lead_name} & {p.helper_name}: {p.item} in {p.setting} ({p.decision}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
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
