#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py
======================================================================

A standalone storyworld for a small adventure tale built around a notice, a raft,
and a badminton game. Two children are playing near the water when a badminton
item drifts to a tiny island. A posted notice warns against the tempting shortcut,
and the world decides whether the warning is heeded in time or whether a grown-up
must step in with the raft.

Run it
------
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py --place pond --notice deep_water
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py --notice broken_bridge
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py --all
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py --json
    python storyworlds/worlds/gpt-5.4/notice_raft_badminton_dialogue_adventure.py --verify
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
CAUTIOUS_TRAITS = {"careful", "patient", "sensible", "steady"}
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    island: str
    water: str
    edge: str
    raft_phrase: str
    helper_place: str
    hazards: set[str] = field(default_factory=set)
    risky_methods: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class NoticeSpec:
    id: str
    sign_text: str
    hazard: str
    forbids: set[str] = field(default_factory=set)
    reason: str = ""
    safe_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    item: str
    phrase: str
    drift_text: str
    recover_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RiskyMethod:
    id: str
    idea: str
    step_text: str
    fail_text: str
    danger: str
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


def _r_wet_to_cold(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["wet"] < THRESHOLD:
            continue
        sig = ("cold", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["cold"] += 1
        out.append("__cold__")
    return out


def _r_scare_from_slip(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["slip"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wet_to_cold", tag="physical", apply=_r_wet_to_cold),
    Rule(name="scare_from_slip", tag="emotional", apply=_r_scare_from_slip),
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
    "pond": Setting(
        id="pond",
        place="the old park pond",
        island="a round patch of reeds in the middle",
        water="green pond water",
        edge="a wooden landing by the cattails",
        raft_phrase="a flat little rope raft",
        helper_place="a shed beside the pond",
        hazards={"deep_water", "soft_mud"},
        risky_methods={"wade", "jump_stones"},
        tags={"water", "raft", "park"},
    ),
    "river": Setting(
        id="river",
        place="the camp river bend",
        island="a pebbly islet just off the bank",
        water="fast brown river water",
        edge="a creaky old landing near the willows",
        raft_phrase="a narrow guide-rope raft",
        helper_place="the ranger post",
        hazards={"deep_water", "broken_bridge"},
        risky_methods={"wade", "broken_bridge"},
        tags={"water", "raft", "camp"},
    ),
    "marsh": Setting(
        id="marsh",
        place="the boardwalk marsh",
        island="a tufted grassy hummock beyond the rushes",
        water="dark marsh water",
        edge="a low dock under the reeds",
        raft_phrase="a broad hand-pulled raft",
        helper_place="a bird-watching hut",
        hazards={"soft_mud", "broken_bridge"},
        risky_methods={"jump_stones", "broken_bridge"},
        tags={"water", "raft", "marsh"},
    ),
}

NOTICES = {
    "deep_water": NoticeSpec(
        id="deep_water",
        sign_text="NOTICE: Deep water. No wading. Use the raft.",
        hazard="deep_water",
        forbids={"wade"},
        reason="the water dropped away faster than it looked",
        safe_line="The notice made it plain that feet were not the right tool for this crossing.",
        tags={"notice", "water", "deep"},
    ),
    "soft_mud": NoticeSpec(
        id="soft_mud",
        sign_text="NOTICE: Soft mud by the edge. Do not hop across. Use the raft.",
        hazard="soft_mud",
        forbids={"jump_stones"},
        reason="the shiny stones sat in sucking mud",
        safe_line="The notice warned that the easy-looking path was not really solid at all.",
        tags={"notice", "mud", "water"},
    ),
    "broken_bridge": NoticeSpec(
        id="broken_bridge",
        sign_text="NOTICE: Footbridge closed. Planks broken. Take the raft.",
        hazard="broken_bridge",
        forbids={"broken_bridge"},
        reason="the old bridge had missing boards and a tilted rail",
        safe_line="The notice turned a brave-looking shortcut into a plainly foolish one.",
        tags={"notice", "bridge", "water"},
    ),
}

GOALS = {
    "shuttlecock": Goal(
        id="shuttlecock",
        item="shuttlecock",
        phrase="their white badminton shuttlecock",
        drift_text="A gust picked up their badminton shuttlecock and carried it out to the little island.",
        recover_text="lifted the shuttlecock high like a treasure feather",
        tags={"badminton", "shuttlecock"},
    ),
    "racket": Goal(
        id="racket",
        item="badminton racket",
        phrase="a light badminton racket with blue strings",
        drift_text="A silly bounce sent a badminton racket skidding onto the raft rope and then onto the little island bank.",
        recover_text="held the racket over their head like an explorer's flag",
        tags={"badminton", "racket"},
    ),
    "birdie_tube": Goal(
        id="birdie_tube",
        item="tube of birdies",
        phrase="their tube of badminton birdies",
        drift_text="The cap popped loose, and their tube of badminton birdies rolled until it came to rest on the little island.",
        recover_text="hugged the tube of birdies against their chest",
        tags={"badminton", "birdie"},
    ),
}

RISKY_METHODS = {
    "wade": RiskyMethod(
        id="wade",
        idea="wade straight through",
        step_text="stepped one sneaker into the water and tried to wade straight through",
        fail_text="The cold water rose higher than expected, and the bottom fell away under one startled step.",
        danger="deep water can surprise you",
        tags={"water", "wade"},
    ),
    "jump_stones": RiskyMethod(
        id="jump_stones",
        idea="hop across the shiny stones",
        step_text="put a foot on the first shiny stone and tried to hop across",
        fail_text="The stone rocked in soft mud, and one leg slid with a muddy splash.",
        danger="mud can move when it looks still",
        tags={"water", "mud"},
    ),
    "broken_bridge": RiskyMethod(
        id="broken_bridge",
        idea="tiptoe across the old bridge",
        step_text="crept onto the old bridge and tried to tiptoe across",
        fail_text="One loose plank clacked sideways, and the rail gave a worrying wobble.",
        danger="broken boards cannot be trusted",
        tags={"bridge", "water"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella", "Ruby", "June"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Finn", "Eli", "Sam", "Theo"]
TRAITS = ["careful", "patient", "sensible", "steady", "curious", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for notice_id, notice in NOTICES.items():
            if notice.hazard not in setting.hazards:
                continue
            if not (notice.forbids & setting.risky_methods):
                continue
            for goal_id in GOALS:
                combos.append((place_id, notice_id, goal_id))
    return combos


def hazard_matches(setting: Setting, notice: NoticeSpec) -> bool:
    return notice.hazard in setting.hazards and bool(notice.forbids & setting.risky_methods)


def chosen_risky_method(setting: Setting, notice: NoticeSpec) -> str:
    options = sorted(notice.forbids & setting.risky_methods)
    if not options:
        raise StoryError("(No story: this notice does not forbid any tempting shortcut in that place.)")
    return options[0]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + (3.0 if older else 0.0) + 1.0
    return older and authority > BRAVERY_INIT


def explain_rejection(setting: Setting, notice: NoticeSpec) -> str:
    if notice.hazard not in setting.hazards:
        return (
            f"(No story: the notice about {notice.hazard.replace('_', ' ')} does not fit {setting.place}. "
            f"The posted warning should match the real hazard there.)"
        )
    return (
        f"(No story: {setting.place} has no tempting shortcut that this notice would forbid. "
        f"A warning sign needs a real risky choice to push against.)"
    )


@dataclass
class StoryParams:
    place: str
    notice: str
    goal: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    helper_type: str
    trait: str
    relation: str = "friends"
    instigator_age: int = 6
    cautioner_age: int = 6
    seed: Optional[int] = None


def predict_trouble(world: World, method_id: str) -> dict:
    sim = world.copy()
    child = sim.get("instigator")
    attempt_shortcut(sim, child, RISKY_METHODS[method_id], narrate=False)
    return {
        "wet": child.meters["wet"] >= THRESHOLD,
        "slip": child.meters["slip"] >= THRESHOLD,
        "fear": child.memes["fear"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting, goal: Goal) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["adventure"] += 1
    world.say(
        f"One bright afternoon, {a.id} and {b.id} carried their badminton things to {setting.place}. "
        f"To them, {setting.edge} was the start of a grand adventure."
    )
    world.say(
        f'They took turns batting the birdie back and forth and shouting, "Explorer point!" whenever someone made a lucky hit.'
    )
    world.say(goal.drift_text)
    world.say(
        f'"There it is!" {a.id} said, pointing at {setting.island}.'
    )


def notice_scene(world: World, a: Entity, b: Entity, notice: NoticeSpec) -> None:
    world.say(
        f"At the landing stood a painted notice board. {b.id} stopped first and read aloud, "
        f'"{notice.sign_text}"'
    )
    world.say(notice.safe_line)


def temptation(world: World, a: Entity, method: RiskyMethod) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} leaned forward with bright eyes. "We do not need to wait," {a.pronoun()} said. '
        f'"I can just {method.idea}."'
    )


def warning(world: World, a: Entity, b: Entity, helper: Entity, notice: NoticeSpec, method_id: str) -> None:
    pred = predict_trouble(world, method_id)
    b.memes["caution"] += 1
    world.facts["predicted"] = pred
    second = ""
    if pred["slip"] or pred["wet"]:
        second = f" {b.id} pointed at the water and said, \"That notice is there because {notice.reason}.\""
    world.say(
        f'"No," said {b.id}. "We should notice the notice. {helper.label_word.capitalize()} would want us to use the raft."'
        f"{second}"
    )


def back_down(world: World, a: Entity, b: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} mouth to argue, then looked again at the sign. '
        f'"All right," {a.pronoun()} said. "Adventure heroes can read directions too."'
    )


def attempt_shortcut(world: World, a: Entity, method: RiskyMethod, narrate: bool = True) -> None:
    a.meters["slip"] += 1
    if method.id == "wade":
        a.meters["wet"] += 1
    elif method.id == "jump_stones":
        a.meters["muddy"] += 1
        a.meters["wet"] += 1
    else:
        a.meters["wobble"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"But {a.id} {method.step_text}.")
        world.say(method.fail_text)


def helper_arrives(world: World, helper: Entity, a: Entity, method: RiskyMethod) -> None:
    a.memes["fear"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'"Back to the landing," called {helper.id} from {world.setting.helper_place}. '
        f'{helper.pronoun().capitalize()} had already seen what was happening.'
    )
    world.say(
        f'{helper.id} kept {helper.pronoun("possessive")} voice calm. "That shortcut is not brave," {helper.pronoun()} said. '
        f'"It is risky, and {method.danger}."'
    )


def raft_crossing(world: World, helper: Entity, a: Entity, b: Entity, goal: Goal) -> None:
    for ent in (a, b):
        ent.memes["trust"] += 1
        ent.memes["joy"] += 1
        ent.memes["fear"] = 0.0
    world.say(
        f'Soon {helper.id} pulled {world.setting.raft_phrase} to the dock and held the rope steady. '
        f'"Feet inside, hands on the line," {helper.pronoun()} said.'
    )
    world.say(
        f'The raft slid over the water with a hushy scrape. Halfway across, {b.id} whispered, '
        f'"Now this feels like a real expedition."'
    )
    world.say(
        f'On the little island, {a.id} {goal.recover_text}, and {b.id} laughed. '
        f'"We saved the badminton game!" {b.id} said.'
    )


def lesson(world: World, helper: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
    world.say(
        f'When they floated back, {helper.id} tied the raft and knelt so {a.id} and {b.id} could see {helper.pronoun("object")} eye to eye.'
    )
    world.say(
        f'"A notice is a tiny grown-up voice left behind to keep people safe," {helper.pronoun()} said. '
        f'"The clever part of adventure is noticing it before trouble starts."'
    )
    world.say(
        f'"Next time," said {a.id}, "I will read first and rush second."'
    )


def ending(world: World, a: Entity, b: Entity, goal: Goal) -> None:
    world.say(
        f'They played badminton until the sun turned gold on the water, and every time the birdie flew high, '
        f'{b.id} called, "Notice first!" and {a.id} answered, "Raft if needed!"'
    )
    world.say(
        f'The little island no longer looked like a dare. It looked like part of a good adventure, because now they knew the safe way across.'
    )


def tell(
    setting: Setting,
    notice: NoticeSpec,
    goal: Goal,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    helper_name: str = "Aunt May",
    helper_type: str = "aunt",
    trait: str = "careful",
    relation: str = "friends",
    instigator_age: int = 6,
    cautioner_age: int = 6,
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        age=cautioner_age,
        attrs={"name": cautioner, "relation": relation},
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_name,
        phrase=helper_name,
        role="helper",
    ))
    world.add(Entity(id="raft", type="raft", label="raft", phrase=setting.raft_phrase))
    world.add(Entity(id="goal", type="game_item", label=goal.item, phrase=goal.phrase))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    method_id = chosen_risky_method(setting, notice)
    method = RISKY_METHODS[method_id]

    introduce(world, a, b, setting, goal)
    world.para()
    notice_scene(world, a, b, notice)
    temptation(world, a, method)
    warning(world, a, b, helper, notice, method_id)

    if would_avert(relation, instigator_age, cautioner_age, trait):
        world.facts["outcome"] = "averted"
        back_down(world, a, b)
        world.para()
        raft_crossing(world, helper, a, b, goal)
        lesson(world, helper, a, b)
        world.para()
        ending(world, a, b, goal)
    else:
        world.facts["outcome"] = "rescued"
        world.para()
        attempt_shortcut(world, a, method, narrate=True)
        helper_arrives(world, helper, a, method)
        world.para()
        raft_crossing(world, helper, a, b, goal)
        lesson(world, helper, a, b)
        world.para()
        ending(world, a, b, goal)

    world.facts.update(
        setting=setting,
        notice=notice,
        goal_cfg=goal,
        risky_method=method,
        instigator=a,
        cautioner=b,
        helper=helper,
        relation=relation,
        tried_shortcut=world.facts["outcome"] == "rescued",
        slipped=a.meters["slip"] >= THRESHOLD,
        wet=a.meters["wet"] >= THRESHOLD,
    )
    return world


def story_names(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = story_names(f["instigator"])
    b = story_names(f["cautioner"])
    goal = f["goal_cfg"]
    notice = f["notice"]
    place = f["setting"].place
    outcome = f["outcome"]
    base = (
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "notice", '
        f'"raft", and "badminton", with plenty of dialogue.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle adventure where {a} and {b} spot a warning notice at {place}, choose the raft instead of a shortcut, and save {goal.phrase}.",
            f'Write a child-facing story where the line "We should notice the notice" helps stop a risky idea before anyone gets wet.',
        ]
    return [
        base,
        f"Tell an adventure where {a} wants to ignore a notice while chasing {goal.phrase}, but a calm grown-up brings the raft and turns the scare into a lesson.",
        f"Write a story with a small water mishap, clear dialogue, and a safe ending that proves reading signs matters.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    goal = f["goal_cfg"]
    notice = f["notice"]
    method = f["risky_method"]
    relation = f["relation"]
    an = story_names(a)
    bn = story_names(b)
    hn = story_names(helper)
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {an} and {bn}, and {hn}, the calm grown-up near the water. "
            f"They were trying to get back {goal.phrase}."
        ),
        (
            "What started the adventure?",
            f"Their badminton game sent {goal.phrase} out to {f['setting'].island}. "
            f"That turned an ordinary game into a little rescue mission."
        ),
        (
            "What did the notice say?",
            f"The notice said, \"{notice.sign_text}\" It mattered because the sign matched the real danger at that crossing."
        ),
        (
            f"Why did {bn} tell {an} to stop?",
            f"{bn} saw that the notice warned against exactly the shortcut {an} wanted to try. "
            f"{bn} understood that {notice.reason}, so the risky idea could go wrong fast."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"Did {an} ignore the notice?",
            f"No. {an} looked again, listened, and backed down before any trouble started. "
            f"That changed the adventure from a dare into a careful plan."
        ))
    else:
        qa.append((
            f"What happened when {an} tried the shortcut?",
            f"{an} tried to {method.idea}, and it went wrong right away. "
            f"{method.fail_text} That quick scare is why the helper stepped in."
        ))
        qa.append((
            f"How did {hn} solve the problem?",
            f"{hn} brought the raft and showed the children how to cross safely. "
            f"Using the raft fit the notice, the place, and the real danger better than rushing on foot."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the badminton game going on safely beside the water. "
        f"The children treated the notice like part of the adventure, not something to ignore."
    ))
    return qa


KNOWLEDGE = {
    "notice": [
        (
            "What is a notice?",
            "A notice is a sign that tells people important information. It can warn you about danger or tell you the safe thing to do."
        )
    ],
    "raft": [
        (
            "What is a raft?",
            "A raft is a flat boat that can carry people or things across water. Some rafts are pulled by a rope so they stay on a safe path."
        )
    ],
    "badminton": [
        (
            "What is badminton?",
            "Badminton is a game where players hit a shuttlecock back and forth with rackets. The shuttlecock is light, so wind can push it around."
        )
    ],
    "deep": [
        (
            "Why is deep water dangerous?",
            "Deep water can drop away suddenly under your feet. A place that looks easy to cross can become too deep in just a step or two."
        )
    ],
    "mud": [
        (
            "Why is soft mud tricky near water?",
            "Soft mud can look still and solid even when it is slippery underneath. When you step on it, your foot can slide or sink."
        )
    ],
    "bridge": [
        (
            "Why should you stay off a broken bridge?",
            "A broken bridge cannot hold people safely. Loose boards and weak rails can move when you step on them."
        )
    ],
}
KNOWLEDGE_ORDER = ["notice", "raft", "badminton", "deep", "mud", "bridge"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"notice", "raft", "badminton"} | set(world.facts["notice"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond",
        notice="deep_water",
        goal="shuttlecock",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="Aunt May",
        helper_type="aunt",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        place="river",
        notice="broken_bridge",
        goal="racket",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        helper="Ranger Luis",
        helper_type="uncle",
        trait="steady",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        place="marsh",
        notice="soft_mud",
        goal="birdie_tube",
        instigator="Zoe",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        helper="Uncle Ray",
        helper_type="uncle",
        trait="patient",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
]


ASP_RULES = r"""
valid(Place, Notice, Goal) :-
    setting(Place), notice(Notice), goal(Goal),
    hazard_of(Notice, Hazard), has_hazard(Place, Hazard),
    forbids(Notice, Method), risky(Place, Method).

older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
cautious_now  :- trait(T), is_cautious(T).
init_caution(5) :- cautious_now.
init_caution(3) :- not cautious_now.
authority(C + 1 + B) :- init_caution(C), bonus(B).
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.

averted :- older_sibling, authority(A), bravery_init(B), A > B.
outcome(averted) :- averted.
outcome(rescued) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for hazard in sorted(setting.hazards):
            lines.append(asp.fact("has_hazard", place_id, hazard))
        for method in sorted(setting.risky_methods):
            lines.append(asp.fact("risky", place_id, method))
    for notice_id, notice in NOTICES.items():
        lines.append(asp.fact("notice", notice_id))
        lines.append(asp.fact("hazard_of", notice_id, notice.hazard))
        for method in sorted(notice.forbids):
            lines.append(asp.fact("forbids", notice_id, method))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait) else "rescued"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a notice, a raft, and a badminton adventure. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--notice", choices=NOTICES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def _pick_helper(rng: random.Random, helper_type: str) -> str:
    names = {
        "mother": ["Mom", "Mama"],
        "father": ["Dad", "Papa"],
        "aunt": ["Aunt May", "Aunt Rosa"],
        "uncle": ["Uncle Ray", "Uncle Ben", "Ranger Luis"],
    }
    return rng.choice(names[helper_type])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.notice:
        setting = SETTINGS[args.place]
        notice = NOTICES[args.notice]
        if not hazard_matches(setting, notice):
            raise StoryError(explain_rejection(setting, notice))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.notice is None or combo[1] == args.notice)
        and (args.goal is None or combo[2] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, notice, goal = rng.choice(sorted(combos))
    instigator_gender = rng.choice(["girl", "boy"])
    cautioner_gender = rng.choice(["girl", "boy"])
    instigator = _pick_name(rng, instigator_gender)
    cautioner = _pick_name(rng, cautioner_gender, avoid=instigator)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    helper = _pick_helper(rng, helper_type)
    relation = args.relation or rng.choice(["friends", "siblings"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        notice=notice,
        goal=goal,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        helper=helper,
        helper_type=helper_type,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.notice not in NOTICES:
        raise StoryError(f"(Unknown notice: {params.notice})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    setting = SETTINGS[params.place]
    notice = NOTICES[params.notice]
    if not hazard_matches(setting, notice):
        raise StoryError(explain_rejection(setting, notice))
    world = tell(
        setting=setting,
        notice=notice,
        goal=GOALS[params.goal],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, notice, goal) combos:\n")
        for place, notice, goal in combos:
            print(f"  {place:8} {notice:14} {goal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.notice} at {p.place} (goal: {p.goal}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
