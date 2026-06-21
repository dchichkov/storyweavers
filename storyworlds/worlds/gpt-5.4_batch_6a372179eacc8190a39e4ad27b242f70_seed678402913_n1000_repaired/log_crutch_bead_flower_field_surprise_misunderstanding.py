#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/log_crutch_bead_flower_field_surprise_misunderstanding.py
=====================================================================================

A standalone storyworld for a tiny rhyming domain:

- a child plays in a flower field
- a bead rolls into trouble by a log
- a helper arrives with a crutch
- the child misunderstands what the helper will do
- repetition and a small surprise carry the turn
- the ending proves what changed

The world prefers only recovery plans that actually fit the kind of log. A
hollow log can be tapped so a bead rolls out; a forked log can be hooked; a log
with one lifted side can be gently tilted. A sealed log is refused because the
story would promise a fix the world cannot honestly provide.

Run it
------
    python storyworlds/worlds/gpt-5.4/log_crutch_bead_flower_field_surprise_misunderstanding.py
    python storyworlds/worlds/gpt-5.4/log_crutch_bead_flower_field_surprise_misunderstanding.py --log sealed
    python storyworlds/worlds/gpt-5.4/log_crutch_bead_flower_field_surprise_misunderstanding.py --all
    python storyworlds/worlds/gpt-5.4/log_crutch_bead_flower_field_surprise_misunderstanding.py --qa --json
    python storyworlds/worlds/gpt-5.4/log_crutch_bead_flower_field_surprise_misunderstanding.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root, even though this file lives in storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
ASK_FIRST_TRAITS = {"curious", "bold", "cheerful"}


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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class FieldCfg:
    id: str
    phrase: str
    flowers: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LogCfg:
    id: str
    phrase: str
    interior: str
    methods: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class BeadCfg:
    id: str
    color: str
    phrase: str
    from_item: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    phrase: str
    warm_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PlanCfg:
    id: str
    phrase: str
    verb: str
    chant: str
    success_text: str
    qa_text: str
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


def _r_found_brings_relief(world: World) -> list[str]:
    bead = world.entities.get("bead")
    child = world.entities.get("child")
    if bead is None or child is None:
        return []
    if bead.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", "bead")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    return []


def _r_worry_fades_after_truth(world: World) -> list[str]:
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if child is None or helper is None:
        return []
    if child.memes["worry"] < THRESHOLD:
        return []
    if helper.memes["understood"] < THRESHOLD and helper.memes["explained"] < THRESHOLD:
        return []
    sig = ("worry_fades", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="found_brings_relief", tag="emotional", apply=_r_found_brings_relief),
    Rule(name="worry_fades_after_truth", tag="social", apply=_r_worry_fades_after_truth),
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
        for sent in produced:
            world.say(sent)
    return produced


FIELDS = {
    "daisies": FieldCfg(
        id="daisies",
        phrase="a flower field full of daisies",
        flowers="white daisies nodding in the breeze",
        path="a narrow path between the flowers",
        tags={"flowers", "field", "daisies"},
    ),
    "poppies": FieldCfg(
        id="poppies",
        phrase="a flower field bright with poppies",
        flowers="red poppies lifting their paper-soft heads",
        path="a sandy path through the blossoms",
        tags={"flowers", "field", "poppies"},
    ),
    "buttercups": FieldCfg(
        id="buttercups",
        phrase="a flower field glowing with buttercups",
        flowers="gold buttercups shining low and slow",
        path="a soft path by the yellow blooms",
        tags={"flowers", "field", "buttercups"},
    ),
}

LOGS = {
    "hollow": LogCfg(
        id="hollow",
        phrase="a hollow log with a round little tunnel",
        interior="inside the dark little tunnel of the log",
        methods={"tap"},
        tags={"log", "hollow"},
    ),
    "forked": LogCfg(
        id="forked",
        phrase="a forked log with a crooked opening",
        interior="in the crooked opening of the log",
        methods={"hook"},
        tags={"log", "forked"},
    ),
    "mossy": LogCfg(
        id="mossy",
        phrase="a mossy log with one side resting high",
        interior="under the lifted side of the log",
        methods={"tilt"},
        tags={"log", "mossy"},
    ),
    "sealed": LogCfg(
        id="sealed",
        phrase="a heavy log with bark pressed tight",
        interior="behind bark pressed too tight to reach",
        methods=set(),
        tags={"log", "sealed"},
    ),
}

BEADS = {
    "blue": BeadCfg(
        id="blue",
        color="blue",
        phrase="a blue bead",
        from_item="a little bracelet string",
        tags={"bead", "blue"},
    ),
    "gold": BeadCfg(
        id="gold",
        color="gold",
        phrase="a gold bead",
        from_item="a sunny necklace cord",
        tags={"bead", "gold"},
    ),
    "pearl": BeadCfg(
        id="pearl",
        color="pearl",
        phrase="a pearl bead",
        from_item="a ribbon loop",
        tags={"bead", "pearl"},
    ),
}

HELPERS = {
    "grandpa": HelperCfg(
        id="grandpa",
        type="grandfather",
        phrase="Grandpa came along with his crutch",
        warm_name="Grandpa",
        tags={"grandpa", "crutch"},
    ),
    "grandma": HelperCfg(
        id="grandma",
        type="grandmother",
        phrase="Grandma came along with her crutch",
        warm_name="Grandma",
        tags={"grandma", "crutch"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        phrase="Aunt Bea came along with her crutch",
        warm_name="Aunt Bea",
        tags={"aunt", "crutch"},
    ),
}

PLANS = {
    "tap": PlanCfg(
        id="tap",
        phrase="tap the log",
        verb="tapped",
        chant="Tap, tap, tap",
        success_text="The crutch went tap, tap, tap on the side of the hollow wood, and the bead rolled out with a tiny click.",
        qa_text="tapped the hollow log with the crutch so the bead rolled out",
        tags={"tap", "crutch", "log"},
    ),
    "hook": PlanCfg(
        id="hook",
        phrase="hook the bead",
        verb="hooked",
        chant="Hook, look, hook",
        success_text="The crutch tip slid in with a gentle hook, hook, hook, and the bead slipped back into the light.",
        qa_text="used the crutch tip like a hook to draw the bead out",
        tags={"hook", "crutch", "log"},
    ),
    "tilt": PlanCfg(
        id="tilt",
        phrase="tilt the log",
        verb="tilted",
        chant="Lift, tilt, drift",
        success_text="The crutch nudged the lifted edge, the log gave a tiny tilt, and the bead drifted free through the grass.",
        qa_text="used the crutch to tilt the log just enough for the bead to drift free",
        tags={"tilt", "crutch", "log"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tessa", "Nora", "Pia", "Ruby", "Ivy", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Nico", "Eli", "Finn", "Arlo", "Ben"]
TRAITS = ["curious", "shy", "careful", "bold", "cheerful", "thoughtful"]


def valid_plan(log_id: str, plan_id: str) -> bool:
    return plan_id in LOGS[log_id].methods


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for field_id in FIELDS:
        for log_id, log_cfg in LOGS.items():
            for bead_id in BEADS:
                for plan_id in PLANS:
                    if valid_plan(log_id, plan_id):
                        combos.append((field_id, log_id, bead_id, plan_id))
    return combos


def would_ask_first(trait: str) -> bool:
    return trait in ASK_FIRST_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "explained" if would_ask_first(params.trait) else "surprised"


def predict_recovery(log_id: str, plan_id: str) -> bool:
    return valid_plan(log_id, plan_id)


def introduce(world: World, child: Entity, friend: Entity, field_cfg: FieldCfg, bead_cfg: BeadCfg) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {field_cfg.phrase}, where {field_cfg.flowers} swayed, "
        f"{child.id} and {friend.id} sat to play."
    )
    world.say(
        f"They threaded petals and stems all day, and on {bead_cfg.from_item} shone {bead_cfg.phrase}, bright as a drop of day."
    )


def lose_bead(world: World, child: Entity, log_cfg: LogCfg, bead_cfg: BeadCfg) -> None:
    bead = world.get("bead")
    bead.meters["lost"] += 1
    child.memes["worry"] += 1
    world.say(
        f"But plink went the bead, and away it flew. It bounced by {log_cfg.phrase} and hid {log_cfg.interior}."
    )
    world.say(
        f'"My {bead_cfg.color} bead, my bead, my bead!" {child.id} cried. "It was right here, and now it has slid."'
    )


def helper_arrives(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    world.say(f"Just then, {helper_cfg.phrase} along {world.facts['field_cfg'].path}.")
    helper.meters["using_crutch"] += 1
    world.say(
        f"The crutch made a soft clack, clack, clack, and {helper_cfg.warm_name} smiled and said, "
        f'"Let me see that log."'
    )


def misunderstand(world: World, child: Entity, helper: Entity, plan_cfg: PlanCfg) -> None:
    child.memes["worry"] += 1
    helper.memes["misread"] += 1
    world.say(
        f"{child.id} heard the crutch and thought of a hard knock instead of a careful knock."
    )
    world.say(
        f'"Oh no," {child.pronoun()} whispered. "Will {helper.label_word} {plan_cfg.phrase} and send my bead away, away, away?"'
    )


def ask_and_explain(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg, plan_cfg: PlanCfg) -> None:
    helper.memes["explained"] += 1
    helper.memes["understood"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Please do not make it worse," {child.id} said. "{helper_cfg.warm_name}, I thought the crutch would thump too hard."'
    )
    world.say(
        f'{helper_cfg.warm_name} knelt as well as {helper.pronoun()} could and said, '
        f'"Not a bang, not a fling. Just {plan_cfg.chant.lower()}, gentle as a wing."'
    )


def silent_worry(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} stayed quiet, with a small tight sigh, and watched with wide and worried eye."
    )


def recover_bead(world: World, child: Entity, helper: Entity, plan_cfg: PlanCfg) -> None:
    bead = world.get("bead")
    bead.meters["lost"] = 0.0
    bead.meters["found"] += 1
    helper.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(plan_cfg.success_text)
    world.say(
        f"There it was in the grass at last, no smash, no crash, no trouble cast."
    )


def surprise_resolution(world: World, child: Entity, helper_cfg: HelperCfg) -> None:
    helper = world.get("helper")
    helper.memes["understood"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} blinked in surprise. The crutch had not been rough at all. It had been a bridge, not a bump."
    )
    world.say(
        f'"Oh!" {child.pronoun()} said. "I misunderstood. {helper_cfg.warm_name} did not scare the bead away. {helper.pronoun().capitalize()} brought it back to me."'
    )


def grateful_end(world: World, child: Entity, friend: Entity, bead_cfg: BeadCfg, helper_cfg: HelperCfg) -> None:
    child.memes["gratitude"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{child.id} held up {bead_cfg.phrase}, clean and small, and laughed a laugh that rang through all the field."
    )
    world.say(
        f'Soon the bead was on the string again, and {child.id}, {friend.id}, and {helper_cfg.warm_name} walked on between the flowers, '
        f'saying, "Bead found, fear gone, song on."'
    )


def tell(
    field_cfg: FieldCfg,
    log_cfg: LogCfg,
    bead_cfg: BeadCfg,
    helper_cfg: HelperCfg,
    plan_cfg: PlanCfg,
    child_name: str,
    child_gender: str,
    friend_name: str,
    friend_gender: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        label=child_name,
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["kind"],
        label=friend_name,
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.warm_name,
        tags=set(helper_cfg.tags),
    ))
    bead = world.add(Entity(
        id="bead",
        kind="thing",
        type="bead",
        label=bead_cfg.phrase,
        tags=set(bead_cfg.tags),
    ))
    log = world.add(Entity(
        id="log",
        kind="thing",
        type="log",
        label=log_cfg.phrase,
        tags=set(log_cfg.tags),
    ))
    field_ent = world.add(Entity(
        id="field",
        kind="thing",
        type="place",
        label=field_cfg.phrase,
        tags=set(field_cfg.tags),
    ))

    world.facts.update(
        field_cfg=field_cfg,
        log_cfg=log_cfg,
        bead_cfg=bead_cfg,
        helper_cfg=helper_cfg,
        plan_cfg=plan_cfg,
        child=child,
        friend=friend,
        helper=helper,
        bead=bead,
        log=log,
        field=field_ent,
        outcome="",
    )

    introduce(world, child, friend, field_cfg, bead_cfg)
    lose_bead(world, child, log_cfg, bead_cfg)

    world.para()
    helper_arrives(world, helper, helper_cfg)
    misunderstand(world, child, helper, plan_cfg)

    world.para()
    if would_ask_first(trait):
        ask_and_explain(world, child, helper, helper_cfg, plan_cfg)
        recover_bead(world, child, helper, plan_cfg)
        world.facts["outcome"] = "explained"
    else:
        silent_worry(world, child)
        recover_bead(world, child, helper, plan_cfg)
        surprise_resolution(world, child, helper_cfg)
        world.facts["outcome"] = "surprised"

    world.para()
    grateful_end(world, child, friend, bead_cfg, helper_cfg)
    world.facts["found"] = bead.meters["found"] >= THRESHOLD
    world.facts["asked_first"] = would_ask_first(trait)
    return world


@dataclass
class StoryParams:
    field: str
    log: str
    bead: str
    helper: str
    plan: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        field="daisies",
        log="hollow",
        bead="blue",
        helper="grandpa",
        plan="tap",
        child_name="Lila",
        child_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        trait="shy",
    ),
    StoryParams(
        field="poppies",
        log="forked",
        bead="gold",
        helper="grandma",
        plan="hook",
        child_name="Nora",
        child_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        trait="curious",
    ),
    StoryParams(
        field="buttercups",
        log="mossy",
        bead="pearl",
        helper="aunt",
        plan="tilt",
        child_name="Theo",
        child_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        trait="bold",
    ),
]


KNOWLEDGE = {
    "flowers": [
        (
            "What is a flower field?",
            "A flower field is a big open place where many flowers grow close together. Bees, butterflies, and children notice lots of color there.",
        )
    ],
    "log": [
        (
            "What is a log?",
            "A log is a thick piece of wood from a tree trunk. Some logs are hollow or lifted a little, so tiny things can roll under or into them.",
        )
    ],
    "bead": [
        (
            "What is a bead?",
            "A bead is a small piece with a hole through it, so you can thread it on string. People use beads to make bracelets and necklaces.",
        )
    ],
    "crutch": [
        (
            "What is a crutch for?",
            "A crutch helps a person walk by giving support and balance. A crutch can also gently reach something nearby, but it is not for rough swinging.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses the wrong meaning of words or actions. Asking a calm question can help the true meaning come out.",
        )
    ],
    "tap": [
        (
            "Why can tapping help a bead come out of a hollow space?",
            "A gentle tap can make a small round bead start moving. Once it rolls, it may come back into the open where someone can pick it up.",
        )
    ],
    "hook": [
        (
            "How can a hooked tool help with a small lost object?",
            "A hooked tip can catch behind a little object and draw it closer. It works best when there is an opening to reach through.",
        )
    ],
    "tilt": [
        (
            "Why does tilting a log sometimes help?",
            "Tilting changes which way the ground slopes under the object. Then the object can drift or roll out instead of staying stuck.",
        )
    ],
}

KNOWLEDGE_ORDER = ["flowers", "log", "bead", "crutch", "misunderstanding", "tap", "hook", "tilt"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper_cfg = f["helper_cfg"]
    bead_cfg = f["bead_cfg"]
    log_cfg = f["log_cfg"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short rhyming story for a 3-to-5-year-old set in a flower field that includes the words "log", "crutch", and "bead".',
        f"Tell a gentle story where {child.id} loses {bead_cfg.phrase} by {log_cfg.phrase} and misunderstands what {helper_cfg.warm_name} will do with a crutch.",
    ]
    if outcome == "explained":
        prompts.append(
            "Write a rhyming story with a misunderstanding that gets cleared by a brave question before the surprise fix happens."
        )
    else:
        prompts.append(
            "Write a rhyming story with repetition and a small surprise, where a child stays worried until the helper's gentle action proves the misunderstanding wrong."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    bead_cfg = f["bead_cfg"]
    helper_cfg = f["helper_cfg"]
    log_cfg = f["log_cfg"]
    plan_cfg = f["plan_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id} in a flower field, and {helper_cfg.warm_name} who came to help. The trouble began when {bead_cfg.phrase} rolled by {log_cfg.phrase}.",
        ),
        (
            f"What problem did {child.id} have?",
            f"{child.id} lost {bead_cfg.phrase} when it bounced away and hid by the log. That made {child.pronoun()} worried because the bead had been part of the little string they were making.",
        ),
        (
            f"Why did {child.id} feel worried when {helper_cfg.warm_name} came with a crutch?",
            f"{child.id} heard the crutch and imagined a hard knock instead of a careful touch. The misunderstanding made {child.pronoun()} fear the bead might be knocked farther away.",
        ),
    ]
    if outcome == "explained":
        qa.append(
            (
                f"How was the misunderstanding cleared?",
                f"{child.id} asked {helper_cfg.warm_name} not to make things worse, and the helper explained the plan in a gentle way. Because {child.pronoun()} asked first, the worry faded before the bead came out.",
            )
        )
    else:
        qa.append(
            (
                "What was the surprise in the story?",
                f"The surprise was that the crutch did not make the trouble bigger at all. Instead, {helper_cfg.warm_name} used it gently, and the bead came back out.",
            )
        )
    qa.append(
        (
            f"How did {helper_cfg.warm_name} get the bead back?",
            f"{helper_cfg.warm_name} {plan_cfg.qa_text}. The plan fit that kind of log, so the bead could move safely into the open again.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the bead back on the string and the children walking between the flowers with lighter hearts. The ending shows that the misunderstanding is gone because fear changed into thanks and song.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"flowers", "log", "bead", "crutch", "misunderstanding"}
    tags |= set(world.facts["plan_cfg"].tags)
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(log_cfg: LogCfg, plan_cfg: PlanCfg) -> str:
    if not log_cfg.methods:
        return (
            f"(No story: {log_cfg.phrase} gives no honest way to reach the bead. "
            f"The world refuses to promise a rescue through bark pressed tight.)"
        )
    return (
        f"(No story: the plan '{plan_cfg.id}' does not fit {log_cfg.phrase}. "
        f"Pick one of: {', '.join(sorted(log_cfg.methods))}.)"
    )


ASP_RULES = r"""
valid_plan(L, P) :- log(L), plan(P), works_with(L, P).

ask_first(T) :- trait(T), asks_first_trait(T).

outcome(explained) :- chosen_trait(T), ask_first(T).
outcome(surprised) :- chosen_trait(T), not ask_first(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for field_id in FIELDS:
        lines.append(asp.fact("field", field_id))
    for log_id, log_cfg in LOGS.items():
        lines.append(asp.fact("log", log_id))
        for method in sorted(log_cfg.methods):
            lines.append(asp.fact("works_with", log_id, method))
    for bead_id in BEADS:
        lines.append(asp.fact("bead", bead_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(ASK_FIRST_TRAITS):
        lines.append(asp.fact("asks_first_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_plan/2."))
    return sorted(set(asp.atoms(model, "valid_plan")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_trait", params.trait)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = {(log_id, plan_id) for _, log_id, _, plan_id in valid_combos()}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: plan gate matches ({len(clingo_set)} valid log/plan pairs).")
    else:
        rc = 1
        print("MISMATCH in valid log/plan pairs:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        args = build_parser().parse_args([])
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a lost bead, a log, a crutch, and a misunderstanding in a flower field."
    )
    ap.add_argument("--field", choices=FIELDS)
    ap.add_argument("--log", choices=LOGS)
    ap.add_argument("--bead", choices=BEADS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid log/plan pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.log and args.plan:
        log_cfg = LOGS[args.log]
        plan_cfg = PLANS[args.plan]
        if not valid_plan(args.log, args.plan):
            raise StoryError(explain_rejection(log_cfg, plan_cfg))
    if args.log and not LOGS[args.log].methods:
        log_cfg = LOGS[args.log]
        fallback = args.plan or next(iter(PLANS))
        raise StoryError(explain_rejection(log_cfg, PLANS[fallback]))

    combos = [
        combo for combo in valid_combos()
        if (args.field is None or combo[0] == args.field)
        and (args.log is None or combo[1] == args.log)
        and (args.bead is None or combo[2] == args.bead)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    field_id, log_id, bead_id, plan_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        field=field_id,
        log=log_id,
        bead=bead_id,
        helper=helper_id,
        plan=plan_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.field not in FIELDS:
        raise StoryError(f"(Unknown field: {params.field})")
    if params.log not in LOGS:
        raise StoryError(f"(Unknown log: {params.log})")
    if params.bead not in BEADS:
        raise StoryError(f"(Unknown bead: {params.bead})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if not valid_plan(params.log, params.plan):
        raise StoryError(explain_rejection(LOGS[params.log], PLANS[params.plan]))

    world = tell(
        field_cfg=FIELDS[params.field],
        log_cfg=LOGS[params.log],
        bead_cfg=BEADS[params.bead],
        helper_cfg=HELPERS[params.helper],
        plan_cfg=PLANS[params.plan],
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
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
        print(asp_program("", "#show valid_plan/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} valid (log, plan) pairs:\n")
        for log_id, plan_id in pairs:
            print(f"  {log_id:8} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.bead} bead by {p.log} log ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
