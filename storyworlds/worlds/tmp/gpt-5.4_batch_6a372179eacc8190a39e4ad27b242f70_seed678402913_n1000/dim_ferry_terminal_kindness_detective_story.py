#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dim_ferry_terminal_kindness_detective_story.py
========================================================================

A standalone storyworld for a tiny detective story set in a ferry terminal.

Premise
-------
A child in a dim ferry terminal notices a worried traveler who has misplaced
something important. The child plays detective: follows a clue, asks a worker
for help, and solves the case through kindness rather than bossiness.

World logic
-----------
This world prefers a narrow band of plausible little mysteries:

* each missing item has a clue that honestly points to one search location
* each worker can help only at locations they can really see or open
* the child must choose a kind approach before the worker offers useful help

So the "detective story" turn is not just decorative vocabulary. The state of
the clue, the worker's trust, and the item's location drive what gets narrated.

Run it
------
python storyworlds/worlds/gpt-5.4/dim_ferry_terminal_kindness_detective_story.py
python storyworlds/worlds/gpt-5.4/dim_ferry_terminal_kindness_detective_story.py --case ticket_wallet --helper ticket_clerk
python storyworlds/worlds/gpt-5.4/dim_ferry_terminal_kindness_detective_story.py --location vending_nook
python storyworlds/worlds/gpt-5.4/dim_ferry_terminal_kindness_detective_story.py --all
python storyworlds/worlds/gpt-5.4/dim_ferry_terminal_kindness_detective_story.py --qa --json
python storyworlds/worlds/gpt-5.4/dim_ferry_terminal_kindness_detective_story.py --verify
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
TRUST_NEEDED = 1.0


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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class CaseFile:
    id: str
    missing_label: str
    missing_phrase: str
    owner_role: str
    owner_phrase: str
    clue: str
    clue_phrase: str
    location: str
    location_phrase: str
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    type: str
    can_open: set[str] = field(default_factory=set)
    can_spot: set[str] = field(default_factory=set)
    advice: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class KindAct:
    id: str
    text: str
    effect: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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
        clone = World()
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    owner = world.get("owner")
    item = world.get("missing")
    if item.attrs.get("lost") and owner.memes["worry"] < THRESHOLD:
        owner.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["kindness"] >= THRESHOLD and helper.memes["trust"] < THRESHOLD:
        helper.memes["trust"] += 1
        out.append("__trust__")
    return out


def _r_recover(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    item = world.get("missing")
    if helper.memes["trust"] < TRUST_NEEDED:
        return out
    if item.attrs.get("found"):
        return out
    case = world.facts["case_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    if case.location in helper_cfg.can_open or case.location in helper_cfg.can_spot:
        item.attrs["found"] = True
        item.attrs["lost"] = False
        owner = world.get("owner")
        owner.memes["relief"] += 1
        hero.memes["pride"] += 1
        out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="trust", tag="social", apply=_r_trust),
    Rule(name="recover", tag="physical", apply=_r_recover),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
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
            if not s.startswith("__"):
                world.say(s)
    return produced


def helper_can_reach(helper: HelperKind, location: str) -> bool:
    return location in helper.can_open or location in helper.can_spot


def kind_fit(helper_id: str, act: KindAct) -> bool:
    return helper_id in act.fits


def valid_combo(case_id: str, helper_id: str, kind_id: str) -> bool:
    case = CASES[case_id]
    helper = HELPERS[helper_id]
    act = KIND_ACTS[kind_id]
    return helper_can_reach(helper, case.location) and kind_fit(helper_id, act)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for case_id in CASES:
        for helper_id in HELPERS:
            for kind_id in KIND_ACTS:
                if valid_combo(case_id, helper_id, kind_id):
                    out.append((case_id, helper_id, kind_id))
    return out


def predict_recovery(case_id: str, helper_id: str, kind_id: str) -> bool:
    return valid_combo(case_id, helper_id, kind_id)


def introduce(world: World, hero: Entity, owner: Entity) -> None:
    world.say(
        f"The ferry terminal was dim with early-evening shadows, and every sound "
        f"seemed to bounce off the high windows. {hero.id} liked places like that, "
        f"because small clues stood out when the rest of the room went soft and gray."
    )
    world.say(
        f"Near a row of plastic seats, {hero.id} noticed {owner.phrase} looking all around "
        f"with worried eyes."
    )


def establish_case(world: World, hero: Entity, owner: Entity, case: CaseFile) -> None:
    missing = world.get("missing")
    missing.attrs["lost"] = True
    propagate(world)
    world.say(
        f'"Oh dear," said {owner.id}. "I cannot find {case.missing_phrase}."'
    )
    world.say(
        f"{hero.id} felt a little detective spark wake up. On the floor lay {case.clue_phrase}."
    )


def inspect_clue(world: World, hero: Entity, case: CaseFile) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} crouched down and studied the clue instead of rushing in circles. "
        f'"This looks important," {hero.pronoun()} murmured. "{case.reason}"'
    )
    world.say(
        f"That made {hero.id} suspect {case.location_phrase}."
    )


def approach_helper(world: World, hero: Entity, helper: Entity, helper_cfg: HelperKind) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f"At the edge of the hall stood {helper.phrase}. {helper.pronoun().capitalize()} "
        f"was busy, but {hero.id} walked over anyway."
    )
    world.say(
        f'"Excuse me," said {hero.id}. "I am working on a little ferry-terminal mystery."'
    )


def do_kindness(world: World, hero: Entity, helper: Entity, act: KindAct) -> None:
    hero.memes["kindness"] += 1
    propagate(world)
    world.say(
        f"Before asking for anything, {hero.id} {act.text}. "
        f"{helper.id} blinked in surprise, and then smiled."
    )
    world.say(
        f"{act.effect} The mystery no longer felt like a bother shared with a stranger. "
        f"It felt like a case two people could solve together."
    )


def share_hint(world: World, hero: Entity, helper: Entity, case: CaseFile, helper_cfg: HelperKind) -> None:
    world.say(
        f'{hero.id} pointed to the clue and explained the guess about {case.location_phrase}. '
        f'{helper.id} listened carefully instead of hurrying {hero.pronoun("object")} away.'
    )
    world.say(
        f'"Good noticing," said {helper.id}. "{helper_cfg.advice}"'
    )


def search_and_find(world: World, hero: Entity, owner: Entity, case: CaseFile, helper: Entity) -> None:
    helper_cfg = world.facts["helper_cfg"]
    if case.location in helper_cfg.can_open:
        world.say(
            f"Together they went to {case.location_phrase}. {helper.id} opened it, and there, tucked "
            f"where no one had first thought to look, was {case.missing_phrase}."
        )
    else:
        world.say(
            f"Together they went to {case.location_phrase}. In the dim corner, {helper.id} spotted "
            f"{case.missing_phrase} before anyone else did."
        )
    world.say(
        f"{owner.id} pressed both hands to {owner.pronoun('possessive')} cheeks and laughed with relief."
    )
    world.say(
        f'"Case solved," said {hero.id}, though very softly, because the best part was not sounding grand. '
        f"It was seeing {owner.id} smile again."
    )


def ending_image(world: World, hero: Entity, owner: Entity, case: CaseFile) -> None:
    world.say(
        f"A minute later, the boarding bell rang. {owner.id} held {case.missing_phrase} safely, "
        f"and the dim terminal no longer felt gloomy. It felt warm, as if one kind choice had "
        f"turned on an extra light."
    )


def tell(
    case: CaseFile,
    helper_cfg: HelperKind,
    kind_cfg: KindAct,
    hero_name: str = "Nina",
    hero_gender: str = "girl",
    owner_name: str = "Mrs. Vale",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    owner_type = "woman" if owner_name.startswith("Mrs.") or owner_name.startswith("Ms.") else "man"
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_type,
            label=owner_name,
            phrase=case.owner_phrase,
            role="owner",
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.label,
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            phrase=f"the {helper_cfg.label}",
            role="helper",
        )
    )
    world.add(
        Entity(
            id="missing",
            kind="thing",
            type="item",
            label=case.missing_label,
            phrase=case.missing_phrase,
            role="missing",
            attrs={"lost": False, "found": False, "location": case.location},
            tags=set(case.tags),
        )
    )
    world.add(
        Entity(
            id="terminal",
            kind="thing",
            type="place",
            label="ferry terminal",
            phrase="the ferry terminal",
            role="setting",
            attrs={"light": "dim"},
            tags={"terminal", "ferry"},
        )
    )

    world.facts.update(case_cfg=case, helper_cfg=helper_cfg, kindness_cfg=kind_cfg)

    introduce(world, hero, owner)
    establish_case(world, hero, owner, case)

    world.para()
    inspect_clue(world, hero, case)
    approach_helper(world, hero, helper, helper_cfg)
    do_kindness(world, hero, helper, kind_cfg)
    share_hint(world, hero, helper, case, helper_cfg)

    world.para()
    propagate(world)
    search_and_find(world, hero, owner, case, helper)
    ending_image(world, hero, owner, case)

    world.facts.update(
        hero=hero,
        owner=owner,
        helper=helper,
        solved=world.get("missing").attrs.get("found", False),
        location=case.location,
    )
    return world


CASES = {
    "ticket_wallet": CaseFile(
        id="ticket_wallet",
        missing_label="ticket wallet",
        missing_phrase="a little blue ticket wallet",
        owner_role="grandmother",
        owner_phrase="an elderly woman in a green coat",
        clue="blue paper stub",
        clue_phrase="a torn blue ticket stub by the timetable stand",
        location="timetable_shelf",
        location_phrase="the shelf under the big timetable board",
        reason="If the stub tore there, the wallet may have slipped down nearby when the schedule was checked",
        tags={"ticket", "travel"},
    ),
    "red_scarf": CaseFile(
        id="red_scarf",
        missing_label="red scarf",
        missing_phrase="a red wool scarf",
        owner_role="father",
        owner_phrase="a father carrying a sleepy child",
        clue="red thread",
        clue_phrase="a bright red thread caught on a crate label",
        location="cargo_crate",
        location_phrase="the stack of cargo crates by the side door",
        reason="A loose thread can catch where cloth brushed against rough wood",
        tags={"scarf", "cloth"},
    ),
    "toy_seal": CaseFile(
        id="toy_seal",
        missing_label="toy seal",
        missing_phrase="a small gray toy seal",
        owner_role="child",
        owner_phrase="a little boy with wet boots",
        clue="cracker crumbs",
        clue_phrase="a line of cracker crumbs leading away from the seats",
        location="vending_nook",
        location_phrase="the vending-machine nook",
        reason="A child snacking while walking might set a toy down near the snack machines without noticing",
        tags={"toy", "snack"},
    ),
}

HELPERS = {
    "ticket_clerk": HelperKind(
        id="ticket_clerk",
        label="ticket clerk",
        type="woman",
        can_open={"timetable_shelf"},
        can_spot={"timetable_shelf"},
        advice="People tuck papers on that shelf while comparing times. Let us check there first",
        tags={"worker", "tickets"},
    ),
    "deckhand": HelperKind(
        id="deckhand",
        label="deckhand",
        type="man",
        can_open={"cargo_crate"},
        can_spot={"cargo_crate"},
        advice="I was moving supplies by that door. Something small could have rested on those crates",
        tags={"worker", "boat"},
    ),
    "snack_vendor": HelperKind(
        id="snack_vendor",
        label="snack vendor",
        type="woman",
        can_open={"vending_nook"},
        can_spot={"vending_nook"},
        advice="Children stop there for crackers all the time. Let us peek by the machine legs",
        tags={"worker", "snack"},
    ),
}

KIND_ACTS = {
    "pick_up_schedule": KindAct(
        id="pick_up_schedule",
        text="picked up a fallen stack of ferry schedules and handed them back neatly",
        effect="The small helpful act made the worker slow down and pay real attention",
        fits={"ticket_clerk"},
        tags={"kindness", "helping"},
    ),
    "hold_door": KindAct(
        id="hold_door",
        text="held the windy side door steady while the worker guided a cart through",
        effect="That simple bit of care turned the worker's hurry into gratitude",
        fits={"deckhand"},
        tags={"kindness", "helping"},
    ),
    "return_crayons": KindAct(
        id="return_crayons",
        text="gathered some crayons that had rolled under a bench and returned them to the coloring table",
        effect="The worker saw that {hero} cared about other people's troubles too".replace("{hero}", "the child detective"),
        fits={"snack_vendor"},
        tags={"kindness", "helping"},
    ),
}


@dataclass
class StoryParams:
    case: str
    helper: str
    kindness: str
    hero_name: str
    hero_gender: str
    owner_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ferry": [
        (
            "What is a ferry?",
            "A ferry is a boat that carries people, and sometimes cars, across water from one place to another."
        )
    ],
    "terminal": [
        (
            "What is a ferry terminal?",
            "A ferry terminal is the building or waiting area where people buy tickets, wait, and board a ferry."
        )
    ],
    "ticket": [
        (
            "Why is a ticket important at a ferry terminal?",
            "A ticket shows that you are allowed to ride. Workers use it to help people board the right ferry."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives look for clues to solve mysteries."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing what someone needs and choosing to help in a gentle way. Even a small helpful act can change how people feel."
        )
    ],
    "worker": [
        (
            "Why can workers help solve a lost-item problem?",
            "Workers know the building well and often see where things are placed or dropped. They can open places or point people in the right direction."
        )
    ],
    "snack": [
        (
            "Why do crumbs matter in a mystery?",
            "Crumbs can show where someone walked or stopped. A tiny trail can help a detective guess where to look next."
        )
    ],
    "cloth": [
        (
            "Why would a scarf leave a thread behind?",
            "Soft cloth can catch on rough wood or metal. When it snags, a tiny thread may stay behind as a clue."
        )
    ],
}
KNOWLEDGE_ORDER = ["ferry", "terminal", "ticket", "clue", "kindness", "worker", "snack", "cloth"]

CURATED = [
    StoryParams(
        case="ticket_wallet",
        helper="ticket_clerk",
        kindness="pick_up_schedule",
        hero_name="Nina",
        hero_gender="girl",
        owner_name="Mrs. Vale",
    ),
    StoryParams(
        case="red_scarf",
        helper="deckhand",
        kindness="hold_door",
        hero_name="Eli",
        hero_gender="boy",
        owner_name="Mr. Rowan",
    ),
    StoryParams(
        case="toy_seal",
        helper="snack_vendor",
        kindness="return_crayons",
        hero_name="Mara",
        hero_gender="girl",
        owner_name="Theo",
    ),
]


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case_cfg"]
    helper = world.facts["helper_cfg"]
    hero = world.facts["hero"]
    return [
        'Write a gentle detective story for a 3-to-5-year-old that includes the word "dim" and takes place in a ferry terminal.',
        f"Tell a ferry-terminal mystery where {hero.id} notices a worried traveler, follows a clue, and solves the case with kindness instead of bossiness.",
        f"Write a small detective story in which a {helper.label} helps find {case.missing_phrase} after one kind act opens the way."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    owner = world.facts["owner"]
    helper = world.facts["helper"]
    case = world.facts["case_cfg"]
    kind = world.facts["kindness_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who acts like a detective in a dim ferry terminal. {hero.id} helps {owner.id} after noticing that {case.missing_phrase} is missing."
        ),
        (
            f"What clue did {hero.id} notice?",
            f"{hero.id} noticed {case.clue_phrase}. That clue suggested where the missing thing might have been left behind."
        ),
        (
            f"Why did {hero.id} think to look near {case.location_phrase}?",
            f"{hero.id} connected the clue to that place. {case.reason}."
        ),
        (
            f"How did kindness help solve the mystery?",
            f"Before asking for help, {hero.id} {kind.text}. That made {helper.id} trust {hero.pronoun('object')} and listen carefully, so the search became a team effort."
        ),
        (
            f"How was the mystery solved?",
            f"{hero.id} and the {helper.label} checked {case.location_phrase} and found {case.missing_phrase}. The case ended happily because a clue pointed the way and kindness brought the right helper in."
        ),
        (
            "How did the story end?",
            f"It ended with the missing item safe again and the boarding bell ringing. The dim terminal felt warmer because worry had turned into relief."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    case = world.facts["case_cfg"]
    tags = {"ferry", "terminal", "clue", "kindness", "worker"}
    if "ticket" in case.tags:
        tags.add("ticket")
    if "snack" in case.tags:
        tags.add("snack")
    if "cloth" in case.tags or "scarf" in case.tags:
        tags.add("cloth")
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:16} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(case_id: str, helper_id: str, kind_id: str) -> str:
    case = CASES[case_id]
    helper = HELPERS[helper_id]
    act = KIND_ACTS[kind_id]
    if not helper_can_reach(helper, case.location):
        return (
            f"(No story: the {helper.label} would not normally reach {case.location_phrase}, "
            f"so this helper cannot honestly solve that case.)"
        )
    if not kind_fit(helper_id, act):
        return (
            f"(No story: the kindness act '{kind_id}' does not fit the {helper.label}'s situation, "
            f"so it would not naturally earn useful help.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
reachable(H, C) :- helper(H), case(C), location_of(C, L), opens(H, L).
reachable(H, C) :- helper(H), case(C), location_of(C, L), spots(H, L).
fits_kind(H, K) :- helper(H), kindness(K), fit(K, H).

valid(C, H, K) :- case(C), helper(H), kindness(K), reachable(H, C), fits_kind(H, K).

solved(C, H, K) :- valid(C, H, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("location_of", case_id, case.location))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for loc in sorted(helper.can_open):
            lines.append(asp.fact("opens", helper_id, loc))
        for loc in sorted(helper.can_spot):
            lines.append(asp.fact("spots", helper_id, loc))
    for kind_id, act in KIND_ACTS.items():
        lines.append(asp.fact("kindness", kind_id))
        for helper_id in sorted(act.fits):
            lines.append(asp.fact("fit", kind_id, helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(case_id: str, helper_id: str, kind_id: str) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_case", case_id),
        asp.fact("chosen_helper", helper_id),
        asp.fact("chosen_kindness", kind_id),
        "chosen_solved :- valid(C,H,K), chosen_case(C), chosen_helper(H), chosen_kindness(K).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_solved/0."))
    return bool(asp.atoms(model, "chosen_solved"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective story in a dim ferry terminal, solved through kindness."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--kindness", choices=KIND_ACTS)
    ap.add_argument("--location", choices=sorted({c.location for c in CASES.values()}))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nina", "Mara", "Lila", "Eva", "June", "Tess"]
BOY_NAMES = ["Eli", "Owen", "Finn", "Theo", "Milo", "Ben"]
OWNER_NAMES = ["Mrs. Vale", "Mr. Rowan", "Mrs. Pike", "Mr. Doran", "Ms. Bell"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.location and args.case:
        if CASES[args.case].location != args.location:
            raise StoryError(
                f"(No story: case '{args.case}' belongs at {CASES[args.case].location_phrase}, not '{args.location}'.)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.helper is None or combo[1] == args.helper)
        and (args.kindness is None or combo[2] == args.kindness)
        and (args.location is None or CASES[combo[0]].location == args.location)
    ]
    if args.case and args.helper and args.kindness and not valid_combo(args.case, args.helper, args.kindness):
        raise StoryError(explain_combo(args.case, args.helper, args.kindness))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, helper_id, kind_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    owner_name = args.owner_name or rng.choice(OWNER_NAMES)
    return StoryParams(
        case=case_id,
        helper=helper_id,
        kindness=kind_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        owner_name=owner_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Unknown case: {params.case})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.kindness not in KIND_ACTS:
        raise StoryError(f"(Unknown kindness act: {params.kindness})")
    if not valid_combo(params.case, params.helper, params.kindness):
        raise StoryError(explain_combo(params.case, params.helper, params.kindness))

    world = tell(
        case=CASES[params.case],
        helper_cfg=HELPERS[params.helper],
        kind_cfg=KIND_ACTS[params.kindness],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        owner_name=params.owner_name,
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

    for params in CURATED:
        py = predict_recovery(params.case, params.helper, params.kindness)
        asp_ok = asp_solved(params.case, params.helper, params.kindness)
        if py != asp_ok:
            rc = 1
            print(f"MISMATCH in solved parity for {params.case}/{params.helper}/{params.kindness}")
            break
    else:
        print(f"OK: solved parity matches on {len(CURATED)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (case, helper, kindness) combinations:\n")
        for case_id, helper_id, kind_id in combos:
            print(f"  {case_id:14} {helper_id:13} {kind_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.case} with {p.helper} ({p.kindness})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
