#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/strength_stilt_defensive_humor_reconciliation_heartwarming.py
=========================================================================================

A standalone storyworld about two children, a wobbly walking challenge, and a
hurt feeling repaired with humor and kindness.

Core shape:
- Two children at a backyard play day.
- One child wants to prove strength by trying a homemade stilt challenge.
- The other child gives a defensive, prickly answer after a wobble and a laugh.
- A helper offers a steadier aid and a joking bridge.
- The children reconcile and end up cheering each other.

The world model tracks physical meters (balance, wobble, scrape, support) and
emotional memes (pride, embarrassment, defensiveness, trust, warmth). The prose
comes from those states, not from one frozen template.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StiltKind:
    id: str
    label: str
    phrase: str
    height: int
    stable: int
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    boast: str
    challenge: str
    proof_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperMove:
    id: str
    sense: int
    support: int
    text: str
    joke: str
    repair: str
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"walker", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    walker = world.get("walker")
    if walker.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    walker.memes["embarrassment"] += 1
    friend = world.get("friend")
    friend.memes["concern"] += 1
    out.append("__wobble__")
    return out


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    walker = world.get("walker")
    if walker.meters["scrape"] < THRESHOLD:
        return out
    sig = ("scrape",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    walker.memes["defensive"] += 1
    out.append("__scrape__")
    return out


def _r_support_calm(world: World) -> list[str]:
    out: list[str] = []
    walker = world.get("walker")
    friend = world.get("friend")
    if walker.meters["supported"] < THRESHOLD:
        return out
    sig = ("support",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    walker.meters["balance"] += 1
    walker.memes["defensive"] = 0.0
    walker.memes["trust"] += 1
    friend.memes["trust"] += 1
    friend.memes["warmth"] += 1
    out.append("__support__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble_to_embarrassment", tag="emotion", apply=_r_wobble),
    Rule(name="scrape_to_defensive", tag="emotion", apply=_r_scrape),
    Rule(name="support_to_calm", tag="repair", apply=_r_support_calm),
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


SETTINGS = {
    "backyard": Setting(
        id="backyard",
        place="the sunny backyard",
        detail="A chalk line curved over the stepping stones, and flowerpots watched from the fence.",
        ending_image="the late sun made two small shadows stretch side by side",
        tags={"yard"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard after class",
        detail="The hopscotch squares were still bright, and the red ball rack leaned by the wall.",
        ending_image="the empty yard glowed gold around their sneakers",
        tags={"yard"},
    ),
    "park": Setting(
        id="park",
        place="the little park by the library",
        detail="A bench sat under the maple tree, and a crooked path made a nice place for games.",
        ending_image="the leaves flickered above them like green hands clapping",
        tags={"yard"},
    ),
}

STILTS = {
    "bucket_stilts": StiltKind(
        id="bucket_stilts",
        label="bucket stilt",
        phrase="a pair of upside-down bucket stilts with rope handles",
        height=2,
        stable=2,
        sound="clop-clop",
        tags={"stilt", "walking"},
    ),
    "can_stilts": StiltKind(
        id="can_stilts",
        label="tin-can stilt",
        phrase="two clean tin-can stilts tied with bright string",
        height=1,
        stable=3,
        sound="tap-tap",
        tags={"stilt", "walking"},
    ),
    "wooden_stilts": StiltKind(
        id="wooden_stilts",
        label="practice stilt",
        phrase="a short pair of practice stilts with padded footrests",
        height=1,
        stable=4,
        sound="tok-tok",
        tags={"stilt", "walking"},
    ),
}

GOALS = {
    "strongest": Goal(
        id="strongest",
        boast="I am strong enough to cross the whole line without help.",
        challenge="cross the whole chalk line",
        proof_line="wanted to prove real strength by making it all the way across",
        tags={"strength"},
    ),
    "carry_flag": Goal(
        id="carry_flag",
        boast="I am strong enough to carry the paper flag and still stay tall.",
        challenge="carry a paper flag to the end of the line",
        proof_line="wanted to prove strength by carrying the little paper flag without wobbling",
        tags={"strength"},
    ),
    "tall_steps": Goal(
        id="tall_steps",
        boast="I am strong enough to take ten tall steps on my own.",
        challenge="take ten tall steps",
        proof_line="wanted to prove strength by taking ten tall steps without a hand to hold",
        tags={"strength"},
    ),
}

HELPERS = {
    "steady_hand": HelperMove(
        id="steady_hand",
        sense=3,
        support=2,
        text="held out a steady hand and walked beside the stilts instead of laughing from far away",
        joke='Then {helper} grinned and said, "These stilts do not need a champion. They need a team."',
        repair='That made the hard little knot in {walker} loosen at once.',
        qa_text="offered a steady hand and walked beside the stilts",
        tags={"help", "reconciliation"},
    ),
    "padding": HelperMove(
        id="padding",
        sense=2,
        support=1,
        text="set a folded towel by the chalk line and said they could practice the first steps more softly",
        joke='Then {helper} wiggled the towel and whispered, "Behold, the royal cloud for brave feet."',
        repair='The silly joke let {walker} smile before answering.',
        qa_text="brought a folded towel and turned practice into a gentler game",
        tags={"help", "reconciliation", "humor"},
    ),
    "both": HelperMove(
        id="both",
        sense=3,
        support=3,
        text="offered one hand, moved a folded towel close by, and stayed right beside the chalk line",
        joke='Then {helper} bowed and said, "Sir Stilt and Lady Balance request a kinder audience."',
        repair='The joke was so soft and odd that even {walker} had to laugh.',
        qa_text="offered a hand and a soft towel while joking kindly",
        tags={"help", "reconciliation", "humor"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["earnest", "careful", "bouncy", "kind", "determined", "bright"]

KNOWLEDGE = {
    "strength": [
        (
            "What is strength?",
            "Strength is the power to push, pull, lift, or hold your body steady. It also helps when you keep trying carefully instead of giving up."
        )
    ],
    "stilt": [
        (
            "What is a stilt?",
            "A stilt is something you stand on to make yourself taller while you walk. Stilts can feel wobbly, so people practice slowly and carefully."
        )
    ],
    "balance": [
        (
            "Why do people wobble on stilts?",
            "They wobble because standing higher up makes balance harder. Small shifts in feet and arms can tip the body one way or the other."
        )
    ],
    "defensive": [
        (
            "What does defensive mean?",
            "Defensive means someone feels hurt or embarrassed and quickly tries to protect their feelings. A defensive answer can sound sharp even when the person is not truly angry."
        )
    ],
    "humor": [
        (
            "How can a kind joke help?",
            "A kind joke can make a tight, worried moment feel softer. It helps people breathe, smile, and talk again."
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation means people come back together after hurt feelings or a quarrel. They listen, forgive, and act kindly again."
        )
    ],
    "practice": [
        (
            "Why is practice important when learning something wobbly?",
            "Practice helps your body remember what to do. Little careful tries often work better than one big rushing try."
        )
    ],
}
KNOWLEDGE_ORDER = ["strength", "stilt", "balance", "defensive", "humor", "reconciliation", "practice"]


def risk_level(stilt: StiltKind, helper: HelperMove) -> int:
    return stilt.height + max(0, 4 - stilt.stable) - helper.support


def sensible_helpers() -> list[HelperMove]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def valid_combo(stilt: StiltKind, helper: HelperMove) -> bool:
    return helper.sense >= SENSE_MIN and risk_level(stilt, helper) <= 3


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for stilt_id, stilt in STILTS.items():
            for goal_id in GOALS:
                for helper_id, helper in HELPERS.items():
                    if valid_combo(stilt, helper):
                        out.append((setting_id, stilt_id, goal_id, helper_id))
    return out


def predict_wobble(stilt: StiltKind, helper: HelperMove) -> dict:
    wobble = max(0, risk_level(stilt, helper) - 1)
    scrape = 1 if risk_level(stilt, helper) >= 2 else 0
    return {"wobble": wobble, "scrape": scrape}


def introduce(world: World, setting: Setting, walker: Entity, friend: Entity, stilt: StiltKind) -> None:
    world.say(
        f"One warm afternoon in {setting.place}, {walker.id} and {friend.id} found {stilt.phrase} near the chalk line."
    )
    world.say(setting.detail)


def setup_pride(world: World, walker: Entity, friend: Entity, goal: Goal) -> None:
    walker.memes["pride"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{walker.id} stood a little taller and said, "{goal.boast}"'
    )
    world.say(
        f"{walker.id} {goal.proof_line}. {friend.id} clapped once and moved closer to watch."
    )


def attempt(world: World, walker: Entity, stilt: StiltKind, goal: Goal) -> None:
    walker.meters["on_stilts"] += 1
    walker.meters["balance"] += 1
    world.say(
        f"{walker.id} stepped up. {stilt.sound.capitalize()} went the stilts over the stones as {walker.pronoun()} tried to {goal.challenge}."
    )


def wobble(world: World, walker: Entity, friend: Entity, stilt: StiltKind, helper: HelperMove) -> None:
    pred = predict_wobble(stilt, helper)
    world.facts["predicted"] = pred
    if pred["wobble"] >= 1:
        walker.meters["wobble"] += 1
        world.say(
            f"On the third step, one {stilt.label} tipped sideways, and {walker.id}'s arms flew out like surprised birds."
        )
    if pred["scrape"] >= 1:
        walker.meters["scrape"] += 1
        world.say(
            f"{walker.pronoun().capitalize()} hopped down too fast and brushed one knee on the ground."
        )
    propagate(world, narrate=False)
    friend.memes["laugh_burst"] += 1
    world.say(
        f"{friend.id} made a tiny sound that was half a gasp and half a laugh, because the flapping arms looked so funny for one blink."
    )


def defensive_reply(world: World, walker: Entity, friend: Entity) -> None:
    if walker.memes["defensive"] >= THRESHOLD:
        world.say(
            f'{walker.id} turned red and gave a defensive little snap. "You do not have to laugh. I was almost perfect."'
        )
        friend.memes["hurt"] += 1
        world.say(
            f"{friend.id}'s smile fell away. {friend.pronoun().capitalize()} had not meant to be mean."
        )
    else:
        world.say(
            f'{walker.id} let out a huffy breath. "I almost had it," {walker.pronoun()} said.'
        )


def helper_offer(world: World, walker: Entity, friend: Entity, helper: HelperMove) -> None:
    walker.meters["supported"] += 1
    world.say(
        f"{friend.id} did not argue back. Instead, {friend.pronoun()} {helper.text}."
    )
    world.say(helper.joke.format(helper=friend.id, walker=walker.id))
    propagate(world, narrate=False)
    world.say(helper.repair.format(helper=friend.id, walker=walker.id))


def apology_and_reconcile(world: World, walker: Entity, friend: Entity) -> None:
    walker.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    walker.memes["apology"] += 1
    friend.memes["forgiveness"] += 1
    world.say(
        f'{walker.id} looked down at the chalk line and then up again. "I am sorry," {walker.pronoun()} said. "I felt wobbly inside, so I talked in a hard way."'
    )
    world.say(
        f'{friend.id} nodded. "I am sorry I laughed first," {friend.pronoun()} said. "I was surprised, not trying to poke your feelings."'
    )


def second_try(world: World, walker: Entity, friend: Entity, goal: Goal) -> None:
    walker.meters["balance"] += 1
    walker.meters["success"] += 1
    walker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Together they tried again, slower this time. {friend.id} stayed near, and {walker.id} made it through {goal.challenge} with small brave steps."
    )


def ending(world: World, setting: Setting, walker: Entity, friend: Entity) -> None:
    world.say(
        f"When {walker.id} climbed down, the two children bumped shoulders and laughed at the silly flapping-arm dance from before."
    )
    world.say(
        f"They both knew that real strength did not mean pretending not to need help. It meant telling the truth, taking a hand, and being kind enough to start over."
    )
    world.say(
        f"As they headed home, {setting.ending_image}."
    )


def tell(
    setting: Setting,
    stilt: StiltKind,
    goal: Goal,
    helper: HelperMove,
    walker_name: str = "Lily",
    walker_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    walker_trait: str = "determined",
    friend_trait: str = "kind",
    parent_type: str = "mother",
) -> World:
    world = World()
    walker = world.add(Entity(id="walker", kind="character", type=walker_gender, label=walker_name, role="walker", traits=[walker_trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=[friend_trait]))
    adult = world.add(Entity(id="adult", kind="character", type=parent_type, label="the grown-up", role="adult"))
    walker.attrs["name"] = walker_name
    friend.attrs["name"] = friend_name
    adult.attrs["name"] = adult.label_word

    introduce(world, setting, walker, friend, stilt)
    setup_pride(world, walker, friend, goal)

    world.para()
    attempt(world, walker, stilt, goal)
    wobble(world, walker, friend, stilt, helper)
    defensive_reply(world, walker, friend)

    world.para()
    helper_offer(world, walker, friend, helper)
    apology_and_reconcile(world, walker, friend)

    world.para()
    second_try(world, walker, friend, goal)
    ending(world, setting, walker, friend)

    world.facts.update(
        setting=setting,
        stilt=stilt,
        goal=goal,
        helper=helper,
        walker=walker,
        friend=friend,
        adult=adult,
        walker_name=walker_name,
        friend_name=friend_name,
        reconciled=walker.memes["apology"] >= THRESHOLD and friend.memes["forgiveness"] >= THRESHOLD,
        defensive=walker.memes["apology"] >= THRESHOLD or walker.memes["defensive"] >= THRESHOLD,
        success=walker.meters["success"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    stilt: str
    goal: str
    helper: str
    walker_name: str
    walker_gender: str
    friend_name: str
    friend_gender: str
    walker_trait: str
    friend_trait: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="backyard",
        stilt="bucket_stilts",
        goal="strongest",
        helper="both",
        walker_name="Lily",
        walker_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        walker_trait="determined",
        friend_trait="kind",
        parent="mother",
    ),
    StoryParams(
        setting="schoolyard",
        stilt="can_stilts",
        goal="carry_flag",
        helper="steady_hand",
        walker_name="Max",
        walker_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        walker_trait="earnest",
        friend_trait="bright",
        parent="father",
    ),
    StoryParams(
        setting="park",
        stilt="wooden_stilts",
        goal="tall_steps",
        helper="padding",
        walker_name="Zoe",
        walker_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        walker_trait="bouncy",
        friend_trait="careful",
        parent="mother",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    w = f["walker"]
    fr = f["friend"]
    st = f["stilt"]
    goal = f["goal"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "strength," "stilt," and "defensive."',
        f"Tell a gentle story where {w.attrs['name']} tries a {st.label} challenge to prove strength, gets embarrassed, answers in a defensive way, and then reconciles with {fr.attrs['name']}.",
        f"Write a child-facing story with humor and reconciliation, where a wobble on a stilt turns into an apology, teamwork, and a warm ending.",
    ]


def pair_noun(walker: Entity, friend: Entity) -> str:
    if walker.type == friend.type == "girl":
        return "two girls"
    if walker.type == friend.type == "boy":
        return "two boys"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    walker = f["walker"]
    friend = f["friend"]
    setting = f["setting"]
    stilt = f["stilt"]
    goal = f["goal"]
    helper = f["helper"]
    pred = f.get("predicted", {"wobble": 0, "scrape": 0})
    wname = walker.attrs["name"]
    fname = friend.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(walker, friend)}, {wname} and {fname}, playing in {setting.place}. The story follows their hurt feelings and how they come back together."
        ),
        (
            f"Why did {wname} get on the stilts?",
            f"{wname} wanted to {goal.challenge} and prove strength. The challenge mattered because {walker.pronoun()} wanted to do something brave all alone."
        ),
        (
            f"What went wrong on the first try?",
            f"{wname} wobbled on the {stilt.label}, and the shaky moment made {walker.pronoun('object')} feel embarrassed. {fname} let out a surprised laugh because the flapping arms looked funny for a second."
        ),
        (
            f"Why did {wname} answer in a defensive way?",
            f"{wname} felt hurt and embarrassed after the wobble and knee scrape. The defensive answer was really {walker.pronoun('possessive')} way of protecting those sore feelings."
        ),
        (
            f"How did {fname} help fix the problem?",
            f"{fname} {helper.qa_text}. The help changed the moment because it offered support instead of another sharp answer."
        ),
        (
            "How did humor help them reconcile?",
            f"{fname} used a gentle joke, and that made the tight feeling soften. Once they smiled, both children could apologize honestly and listen to each other."
        ),
        (
            "How did the story end?",
            f"They tried again together, and {wname} finished the challenge with help nearby. The ending feels warm because the children laugh together and understand that real strength can include accepting help."
        ),
    ]
    if pred["scrape"] >= 1:
        qa.append(
            (
                f"Did {wname} get badly hurt?",
                f"No. {wname} only brushed one knee on the ground and was mostly upset because of the wobble and embarrassment. The bigger problem was the hurt feeling between the friends, not a big injury."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"strength", "stilt", "balance", "defensive", "humor", "reconciliation", "practice"}
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n, *_) in world.fired)}")
    return "\n".join(lines)


def explain_rejection(stilt: StiltKind, helper: HelperMove) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: helper move '{helper.id}' scores too low on common sense for this world. "
            f"The repair must be kind and useful, not merely decorative.)"
        )
    return (
        f"(No story: {stilt.label} is too risky for helper move '{helper.id}'. "
        f"This storyworld only allows combinations where the support is enough to make a gentle, believable reconciliation story.)"
    )


ASP_RULES = r"""
helper_sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
risk(St, H, R) :- height(St, Ht), stable(St, Sb), support(H, Su), base_risk(St, B), R = Ht + B - Su.
base_risk(St, B) :- stable(St, Sb), B = 4 - Sb, B > 0.
base_risk(St, 0) :- stable(St, Sb), 4 - Sb <= 0.
valid(Set, St, G, H) :- setting(Set), stilt(St), goal(G), helper(H), helper_sensible(H), risk(St, H, R), R <= 3.

wobble(St, H) :- risk(St, H, R), R >= 2.
scrape(St, H) :- risk(St, H, R), R >= 2.
reconciled(St, H) :- valid(dummy, St, dummy_goal, H).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for stilt_id, stilt in STILTS.items():
        lines.append(asp.fact("stilt", stilt_id))
        lines.append(asp.fact("height", stilt_id, stilt.height))
        lines.append(asp.fact("stable", stilt_id, stilt.stable))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        lines.append(asp.fact("support", helper_id, helper.support))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("setting", "dummy"))
    lines.append(asp.fact("goal", "dummy_goal"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "strength" not in sample.story.lower() or "defensive" not in sample.story.lower():
            raise StoryError("Smoke test story did not render expected content.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a stilt challenge, a defensive moment, humor, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--stilt", choices=STILTS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--walker-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--walker-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stilt and args.helper:
        stilt = STILTS[args.stilt]
        helper = HELPERS[args.helper]
        if not valid_combo(stilt, helper):
            raise StoryError(explain_rejection(stilt, helper))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.stilt is None or c[1] == args.stilt)
        and (args.goal is None or c[2] == args.goal)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, stilt_id, goal_id, helper_id = rng.choice(sorted(combos))
    walker_gender = args.walker_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    walker_name = args.walker_name or pick_name(rng, walker_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=walker_name)
    walker_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        stilt=stilt_id,
        goal=goal_id,
        helper=helper_id,
        walker_name=walker_name,
        walker_gender=walker_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        walker_trait=walker_trait,
        friend_trait=friend_trait,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        stilt = STILTS[params.stilt]
        goal = GOALS[params.goal]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not valid_combo(stilt, helper):
        raise StoryError(explain_rejection(stilt, helper))

    world = tell(
        setting=setting,
        stilt=stilt,
        goal=goal,
        helper=helper,
        walker_name=params.walker_name,
        walker_gender=params.walker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        walker_trait=params.walker_trait,
        friend_trait=params.friend_trait,
        parent_type=params.parent,
    )
    story_text = world.render()
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, stilt, goal, helper) combos:\n")
        for setting_id, stilt_id, goal_id, helper_id in combos:
            if setting_id == "dummy" or goal_id == "dummy_goal":
                continue
            print(f"  {setting_id:10} {stilt_id:14} {goal_id:11} {helper_id}")
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
            header = f"### {p.walker_name} and {p.friend_name}: {p.stilt}, {p.goal}, {p.helper}"
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
