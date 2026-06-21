#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py
==============================================================================

A standalone story world for a child-facing tall tale about a quest that can
only be finished through teamwork. The seed words "faint" and "mercury" are
woven into the simulated world itself: the dawn can begin as a faint stripe of
light, and the porch thermometer's mercury helps explain the weather.

The domain:
    Two children in an oversized tall-tale landscape set out on a quest to
    carry an important object somewhere before the day changes. One child starts
    off trying to manage the job alone, but the world pushes back: the object is
    too heavy for one child, the path is too rough, or the wind is too strong.
    When the pair shares the work with a sensible tool, the quest succeeds and
    the ending image proves the lesson learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py
    python storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py --quest lantern --route ridge
    python storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py --burden bell --tool basket
    python storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py --all
    python storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/faint_mercury_teamwork_lesson_learned_quest_tall.py --verify
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
_THIS = os.path.abspath(__file__)
_WORLD_DIR = os.path.dirname(_THIS)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(_WORLD_DIR))
sys.path.insert(0, _STORYWORLDS_DIR)
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


@dataclass
class Setting:
    id: str = ""
    place: str = ""
    opener: str = ""
    horizon: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str = ""
    call: str = ""
    goal_place: str = ""
    finish_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Burden:
    id: str = ""
    label: str = ""
    phrase: str = ""
    weight: int = 1
    wobble: int = 0
    needed_for: str = ""
    success_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str = ""
    label: str = ""
    phrase: str = ""
    roughness: int = 1
    gust: int = 0
    image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str = ""
    label: str = ""
    phrase: str = ""
    support: int = 1
    steady: int = 0
    pair_only: bool = True
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def difficulty_of(burden: Burden, route: Route) -> int:
    return burden.weight + burden.wobble + route.roughness + route.gust


def capacity_of(tool: Tool, teamwork: bool) -> int:
    if tool.pair_only and not teamwork:
        return 0
    return tool.support + (tool.steady if teamwork else 0)


def can_finish(burden: Burden, route: Route, tool: Tool, teamwork: bool) -> bool:
    return capacity_of(tool, teamwork) >= difficulty_of(burden, route)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for quest_id in QUESTS:
            for burden_id, burden in BURDENS.items():
                if burden.needed_for != quest_id:
                    continue
                for route_id, route in ROUTES.items():
                    for tool_id, tool in TOOLS.items():
                        if can_finish(burden, route, tool, teamwork=True):
                            out.append((setting_id, quest_id, burden_id, route_id, tool_id))
    return out


def predict_attempt(world: World, burden: Burden, route: Route, tool: Tool, teamwork: bool) -> dict:
    sim = world.copy()
    load = sim.get("load")
    if can_finish(burden, route, tool, teamwork):
        load.meters["delivered"] += 1
    else:
        load.meters["stuck"] += 1
    if not teamwork:
        sim.get("lead").memes["pride"] += 1
    else:
        for who in ("lead", "partner"):
            sim.get(who).memes["trust"] += 1
    propagate(sim, narrate=False)
    return {
        "delivered": load.meters["delivered"] >= THRESHOLD,
        "stuck": load.meters["stuck"] >= THRESHOLD,
        "lesson": sim.get("lead").memes["lesson"] >= THRESHOLD,
    }


def _r_stuck_tires(world: World) -> list[str]:
    load = world.get("load")
    if load.meters["stuck"] < THRESHOLD:
        return []
    sig = ("stuck",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("lead").memes["frustration"] += 1
    world.get("partner").memes["concern"] += 1
    return ["__stuck__"]


def _r_share_work(world: World) -> list[str]:
    load = world.get("load")
    if load.meters["delivered"] < THRESHOLD:
        return []
    sig = ("delivered",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for who in ("lead", "partner"):
        world.get(who).memes["joy"] += 1
        world.get(who).memes["trust"] += 1
    return ["__delivered__"]


def _r_humble(world: World) -> list[str]:
    lead = world.get("lead")
    if lead.memes["asked_help"] < THRESHOLD:
        return []
    sig = ("lesson",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["lesson"] += 1
    lead.memes["pride"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck", tag="physical", apply=_r_stuck_tires),
    Rule(name="delivered", tag="social", apply=_r_share_work),
    Rule(name="lesson", tag="social", apply=_r_humble),
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


def dawn_line(setting: Setting) -> str:
    return f"A faint stripe of dawn lay along {setting.horizon}."


def thermometer_line(parent: Entity) -> str:
    return (
        f"On the porch, the mercury in the old thermometer had slipped low enough "
        f"to make the boards creak under {parent.label_word}'s boots."
    )


def introduce(world: World, setting: Setting, lead: Entity, partner: Entity, parent: Entity) -> None:
    world.say(setting.opener)
    world.say(dawn_line(setting))
    world.say(thermometer_line(parent))
    world.say(
        f"In that grand place lived {lead.id} and {partner.id}, two youngsters so eager for a quest "
        f"that even breakfast had to wait for the adventure to begin."
    )


def call_to_quest(world: World, lead: Entity, partner: Entity, quest: Quest, burden: Burden, parent: Entity) -> None:
    world.say(
        f"That morning, {parent.label_word.capitalize()} pointed toward {quest.goal_place} and said, "
        f'"If {burden.phrase} reaches {quest.goal_place} before the day grows busy, {burden.needed_for} can begin the right way."'
    )
    world.say(
        f'"Then that is our quest," cried {lead.id}. "{partner.id}, come along!"'
    )
    world.say(
        f"{partner.id} nodded at once, because the job sounded important and because a friend makes a long road shorter."
    )


def boast(world: World, lead: Entity, burden: Burden) -> None:
    lead.memes["pride"] += 1
    world.say(
        f'When {lead.id} saw {burden.the_phrase if "the_phrase" in burden.__dict__ else burden.phrase}, '
        f'{lead.pronoun("subject")} puffed up like a parade drum and said, '
        f'"I can manage {burden.label} myself."'
    )


def first_lift(world: World, lead: Entity, partner: Entity, burden: Burden, route: Route, tool: Tool) -> None:
    pred = predict_attempt(world, burden, route, tool, teamwork=False)
    world.facts["solo_prediction"] = pred
    world.say(
        f"But {route.phrase} was no polite little path. {route.image}"
    )
    if pred["stuck"]:
        world.say(
            f"{lead.id} tugged with both hands and one brave huff, yet {burden.label} only rocked, wobbled, "
            f"and stayed put as if it had grown roots clear to supper."
        )
    else:
        world.say(
            f"{lead.id} gave the load a mighty pull. It budged, but not in any way that promised a smooth journey."
        )
    partner.memes["concern"] += 1


def partner_warns(world: World, partner: Entity, lead: Entity, burden: Burden, tool: Tool) -> None:
    world.say(
        f'"{lead.id}," said {partner.id}, "that {burden.label} is asking for two pairs of hands and {tool.phrase}. '
        f'Big jobs grow kinder when friends share them."'
    )


def ask_for_help(world: World, lead: Entity, partner: Entity) -> None:
    lead.memes["asked_help"] += 1
    partner.memes["helping"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{lead.id} stopped pulling long enough to listen. Then {lead.pronoun('subject')} scratched "
        f"{lead.pronoun('possessive')} head and gave a sheepish grin."
    )
    world.say(
        f'"You were right," {lead.pronoun()} said. "This is a two-person kind of quest. Will you help me?"'
    )
    world.say(f'"Gladly," said {partner.id}. "That is what partners are for."')


def team_up(world: World, lead: Entity, partner: Entity, burden: Burden, tool: Tool) -> None:
    world.say(
        f"Together they fetched {tool.phrase}, set {burden.label} into place, and counted, "
        f'"One, two, three, heave!"'
    )


def final_push(world: World, lead: Entity, partner: Entity, burden: Burden, route: Route, tool: Tool, quest: Quest) -> None:
    load = world.get("load")
    if can_finish(burden, route, tool, teamwork=True):
        load.meters["delivered"] += 1
    else:
        load.meters["stuck"] += 1
    propagate(world, narrate=False)
    if load.meters["delivered"] >= THRESHOLD:
        world.say(
            f"With {lead.id} pulling one side and {partner.id} steering the other, they crossed {route.phrase} "
            f"so steadily that even the wind had to step aside and watch."
        )
        world.say(
            f"Before long they reached {quest.goal_place}, and {burden.success_line}"
        )
    else:
        raise StoryError("The chosen teamwork plan still could not finish the quest.")


def closing_lesson(world: World, lead: Entity, partner: Entity, parent: Entity, quest: Quest) -> None:
    world.say(
        f"{parent.label_word.capitalize()} tipped a hat to them and laughed a warm laugh that could have rolled a cart downhill."
    )
    world.say(
        f'"Well now," {parent.label_word} said, "that was real strength. Not the huffing kind. '
        f'The sharing kind."'
    )
    world.say(
        f"{lead.id} looked at {partner.id} and nodded. {lead.pronoun('subject').capitalize()} had started the morning "
        f"wanting to be the whole hero, but now {lead.pronoun('subject')} knew a quest is bigger and better when friends pull together."
    )
    world.say(quest.finish_image)


def tell(
    setting: Setting,
    quest: Quest,
    burden: Burden,
    route: Route,
    tool: Tool,
    lead_name: str = "June",
    lead_gender: str = "girl",
    partner_name: str = "Bo",
    partner_gender: str = "boy",
    parent_type: str = "father",
    trait: str = "bold",
) -> World:
    world = World()
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead", traits=[trait]))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner", traits=["steady"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    load = world.add(Entity(id="load", type="burden", label=burden.label, phrase=burden.phrase, role="load"))

    introduce(world, setting, lead, partner, parent)
    call_to_quest(world, lead, partner, quest, burden, parent)

    world.para()
    boast(world, lead, burden)
    first_lift(world, lead, partner, burden, route, tool)
    partner_warns(world, partner, lead, burden, tool)

    world.para()
    ask_for_help(world, lead, partner)
    team_up(world, lead, partner, burden, tool)
    final_push(world, lead, partner, burden, route, tool, quest)

    world.para()
    closing_lesson(world, lead, partner, parent, quest)

    world.facts.update(
        setting=setting,
        quest=quest,
        burden_cfg=burden,
        route=route,
        tool=tool,
        lead=lead,
        partner=partner,
        parent=parent,
        load=load,
        lesson_learned=lead.memes["lesson"] >= THRESHOLD,
        teamwork=True,
        delivered=load.meters["delivered"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the high prairie",
        opener="On the high prairie, even the fence posts were said to grow an inch taller whenever anybody bragged.",
        horizon="the pancake-flat prairie edge",
        tags={"prairie", "dawn"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the red canyon",
        opener="In the red canyon, echoes were so large they had to duck under doorways.",
        horizon="the far red rim",
        tags={"canyon", "dawn"},
    ),
    "marsh": Setting(
        id="marsh",
        place="the silver marsh",
        opener="By the silver marsh, reeds whispered stories tall enough to tickle the moon.",
        horizon="the misty marsh grass",
        tags={"marsh", "dawn"},
    ),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        call="hang the morning lantern",
        goal_place="the sky-hill gate",
        finish_image="Soon the morning lantern burned over the hill, and the whole countryside shone as if the sun had been polished for company.",
        tags={"lantern", "quest"},
    ),
    "bell": Quest(
        id="bell",
        call="ring the supper bell at noon",
        goal_place="the cloud-barn loft",
        finish_image="A minute later the great bell boomed across the fields, and every chicken stood up straighter to listen.",
        tags={"bell", "quest"},
    ),
    "seed": Quest(
        id="seed",
        call="plant the giant seed before breakfast",
        goal_place="the windmill patch",
        finish_image="By the time they stepped back, the seed sat snug in its hill of soil, looking ready to grow a beanstalk clear into next Tuesday.",
        tags={"seed", "quest"},
    ),
}

BURDENS = {
    "lantern": Burden(
        id="lantern",
        label="the brass lantern",
        phrase="a brass lantern as big as a washtub",
        weight=2,
        wobble=1,
        needed_for="lantern",
        success_line="they hoisted the lantern onto its hook, and its wide gold glow spilled across the waking fields",
        tags={"lantern"},
    ),
    "bell": Burden(
        id="bell",
        label="the copper bell",
        phrase="a copper bell round as a rain barrel",
        weight=3,
        wobble=1,
        needed_for="bell",
        success_line="they set the bell rope straight, and the first grand clang rolled out over the barns",
        tags={"bell"},
    ),
    "seed": Burden(
        id="seed",
        label="the giant seed",
        phrase="a giant seed in a sack the size of a pillowcase",
        weight=2,
        wobble=0,
        needed_for="seed",
        success_line="they tucked the seed into the earth, and the dirt patted itself down as neat as a blanket",
        tags={"seed"},
    ),
}

ROUTES = {
    "ridge": Route(
        id="ridge",
        label="the ridge road",
        phrase="the ridge road",
        roughness=2,
        gust=1,
        image="Its stones were as knuckly as giant thumbs, and the wind came striding over the top with both elbows out.",
        tags={"ridge", "wind"},
    ),
    "creek": Route(
        id="creek",
        label="the creek ford",
        phrase="the creek ford",
        roughness=1,
        gust=0,
        image="Its stepping stones were slick as fish backs, and the water kept trying to giggle around their ankles.",
        tags={"creek"},
    ),
    "switchback": Route(
        id="switchback",
        label="the switchback trail",
        phrase="the switchback trail",
        roughness=2,
        gust=0,
        image="It twisted left and right so often that a squirrel could get dizzy just watching.",
        tags={"trail"},
    ),
}

TOOLS = {
    "sled": Tool(
        id="sled",
        label="rope sled",
        phrase="a rope sled polished smooth by a hundred chores",
        support=3,
        steady=1,
        pair_only=True,
        tags={"sled"},
    ),
    "wagon": Tool(
        id="wagon",
        label="red wagon",
        phrase="the red wagon with hickory handles",
        support=4,
        steady=1,
        pair_only=True,
        tags={"wagon"},
    ),
    "yoke": Tool(
        id="yoke",
        label="carrying yoke",
        phrase="a carrying yoke cut from ash wood",
        support=2,
        steady=2,
        pair_only=True,
        tags={"yoke"},
    ),
    "basket": Tool(
        id="basket",
        label="reed basket",
        phrase="a reed basket with a brave-looking handle",
        support=2,
        steady=0,
        pair_only=True,
        tags={"basket"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    quest: str
    burden: str
    route: str
    tool: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["June", "Mabel", "Tess", "Clara", "Nell", "Ruby", "Sadie", "Ivy"]
BOY_NAMES = ["Bo", "Eli", "Wade", "Jasper", "Finn", "Hank", "Otis", "Roy"]
TRAITS = ["bold", "eager", "stout-hearted", "quick", "brave", "bouncy"]

KNOWLEDGE = {
    "mercury": [
        (
            "What is mercury in an old thermometer?",
            "Mercury is a shiny liquid metal that people used in some old thermometers. When the air gets colder or warmer, the silver line moves to show the temperature.",
        )
    ],
    "dawn": [
        (
            "What does faint mean when people talk about a faint line of dawn?",
            "Faint means light or hard to see. A faint line of dawn is the first soft little bit of morning light.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help one another do a job together. A hard job often becomes easier when each person shares part of the work.",
        )
    ],
    "wagon": [
        (
            "Why does a wagon help with a heavy load?",
            "A wagon lets wheels carry the weight instead of arms carrying all of it. That makes it easier to move something big from one place to another.",
        )
    ],
    "sled": [
        (
            "What does a sled do on rough ground?",
            "A sled lets a heavy thing slide along the ground. It can help when a load is awkward or too big to lift neatly.",
        )
    ],
    "bell": [
        (
            "Why are bells used to call people?",
            "A bell makes a loud sound that can travel far. That is why people use bells to announce something important.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light you can carry or hang up. People use it when they need to brighten a dark place.",
        )
    ],
    "seed": [
        (
            "What does a seed need to start growing?",
            "A seed needs the right place, water, and time. Once it is planted in soil, it can begin to sprout.",
        )
    ],
}
KNOWLEDGE_ORDER = ["dawn", "mercury", "teamwork", "wagon", "sled", "bell", "lantern", "seed"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    burden = f["burden_cfg"]
    quest = f["quest"]
    route = f["route"]
    return [
        'Write a child-facing Tall Tale that includes the words "faint" and "mercury" and centers on a quest solved through teamwork.',
        f"Tell a tall tale where {lead.id} first tries to move {burden.phrase} alone across {route.phrase}, then learns to work with {partner.id}.",
        f"Write a story with a clear lesson learned: a big quest to {quest.call} succeeds only when two children share the work.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    parent = f["parent"]
    burden = f["burden_cfg"]
    quest = f["quest"]
    route = f["route"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {partner.id}, two children on a quest, and {lead.id}'s {parent.label_word} who gave them the job.",
        ),
        (
            "What was their quest?",
            f"Their quest was to carry {burden.label} to {quest.goal_place}. It mattered because that was how they could {quest.call}.",
        ),
        (
            "What do the words faint and mercury mean in this story?",
            f"Faint describes the soft little stripe of dawn at the start of the adventure. Mercury is the silver liquid in the old thermometer that showed the morning was cold.",
        ),
        (
            f"Why could {lead.id} not do the job alone?",
            f"{burden.label.capitalize()} was too hard to manage alone on {route.phrase}. The load was heavy and awkward, and the road itself made the task even tougher.",
        ),
        (
            f"How did {partner.id} help?",
            f"{partner.id} told {lead.id} to stop trying to be the whole hero and to share the work. Then the two of them used {tool.phrase} together so the burden could move safely.",
        ),
        (
            "What lesson was learned?",
            f"The lesson was that real strength is not just pushing hard by yourself. It is listening, asking for help, and working together when a quest is too big for one person.",
        ),
    ]
    if f.get("delivered"):
        qa.append(
            (
                "How did the story end?",
                f"They finished the quest together and reached {quest.goal_place}. The ending proves what changed because the big job was done only after {lead.id} accepted help from {partner.id}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"teamwork", "mercury", "dawn"} | set(f["burden_cfg"].tags) | set(f["tool"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="prairie",
        quest="lantern",
        burden="lantern",
        route="ridge",
        tool="wagon",
        lead_name="June",
        lead_gender="girl",
        partner_name="Bo",
        partner_gender="boy",
        parent="father",
        trait="bold",
    ),
    StoryParams(
        setting="canyon",
        quest="bell",
        burden="bell",
        route="switchback",
        tool="wagon",
        lead_name="Mabel",
        lead_gender="girl",
        partner_name="Eli",
        partner_gender="boy",
        parent="mother",
        trait="eager",
    ),
    StoryParams(
        setting="marsh",
        quest="seed",
        burden="seed",
        route="creek",
        tool="sled",
        lead_name="Roy",
        lead_gender="boy",
        partner_name="Tess",
        partner_gender="girl",
        parent="father",
        trait="quick",
    ),
    StoryParams(
        setting="prairie",
        quest="seed",
        burden="seed",
        route="ridge",
        tool="wagon",
        lead_name="Clara",
        lead_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        parent="mother",
        trait="brave",
    ),
]


def explain_rejection(quest_id: str, burden_id: str, route_id: str, tool_id: str) -> str:
    burden = BURDENS[burden_id]
    route = ROUTES[route_id]
    tool = TOOLS[tool_id]
    if burden.needed_for != quest_id:
        return (
            f"(No story: {burden.label} belongs to the {burden.needed_for} quest, not the {quest_id} quest. "
            f"The burden must match the quest it is meant to complete.)"
        )
    need = difficulty_of(burden, route)
    have = capacity_of(tool, teamwork=True)
    return (
        f"(No story: {tool.phrase} is not enough for {burden.label} on {route.phrase}. "
        f"This quest needs teamwork with stronger support: capacity {have} is below difficulty {need}.)"
    )


ASP_RULES = r"""
matches(B, Q) :- burden(B), quest(Q), needed_for(B, Q).
works(B, R, T) :- burden(B), route(R), tool(T),
                  weight(B, W), wobble(B, Z), roughness(R, H), gust(R, G),
                  support(T, S), steady(T, D), pair_only(T),
                  S + D >= W + Z + H + G.
valid(S, Q, B, R, T) :- setting(S), quest(Q), burden(B), route(R), tool(T),
                        matches(B, Q), works(B, R, T).
# single-attempt model for the story turn
solo_capacity(T, S) :- tool(T), support(T, S), not pair_only(T).
solo_capacity(T, 0) :- tool(T), pair_only(T).
team_capacity(T, S + D) :- tool(T), support(T, S), steady(T, D).
difficulty(B, R, W + Z + H + G) :- burden(B), route(R),
                                   weight(B, W), wobble(B, Z), roughness(R, H), gust(R, G).
solo_stuck :- chosen_burden(B), chosen_route(R), chosen_tool(T),
              difficulty(B, R, Need), solo_capacity(T, Have), Have < Need.
team_ok :- chosen_burden(B), chosen_route(R), chosen_tool(T),
           difficulty(B, R, Need), team_capacity(T, Have), Have >= Need.
outcome(delivered) :- solo_stuck, team_ok.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for bid, burden in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        lines.append(asp.fact("needed_for", bid, burden.needed_for))
        lines.append(asp.fact("weight", bid, burden.weight))
        lines.append(asp.fact("wobble", bid, burden.wobble))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("roughness", rid, route.roughness))
        lines.append(asp.fact("gust", rid, route.gust))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("support", tid, tool.support))
        lines.append(asp.fact("steady", tid, tool.steady))
        if tool.pair_only:
            lines.append(asp.fact("pair_only", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_burden", params.burden),
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "faint" not in sample.story or "mercury" not in sample.story:
        raise StoryError("Smoke test failed: required seed words missing from story.")


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
    for idx in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(idx))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        py = "delivered" if can_finish(BURDENS[params.burden], ROUTES[params.route], TOOLS[params.tool], teamwork=True) else "?"
        asp_val = asp_outcome(params)
        if py != asp_val:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome checks differed.")

    try:
        smoke_test_generate()
        print("OK: smoke test generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale teamwork quest storyworld. Unspecified choices are seeded and randomized."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.burden and BURDENS[args.burden].needed_for != args.quest:
        raise StoryError(explain_rejection(args.quest, args.burden, args.route or "ridge", args.tool or "wagon"))

    if args.quest and args.burden and args.route and args.tool:
        if not can_finish(BURDENS[args.burden], ROUTES[args.route], TOOLS[args.tool], teamwork=True):
            raise StoryError(explain_rejection(args.quest, args.burden, args.route, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.quest is None or combo[1] == args.quest)
        and (args.burden is None or combo[2] == args.burden)
        and (args.route is None or combo[3] == args.route)
        and (args.tool is None or combo[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, quest_id, burden_id, route_id, tool_id = rng.choice(sorted(combos))
    lead_name, lead_gender = _pick_name(rng)
    partner_name, partner_gender = _pick_name(rng, avoid=lead_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        quest=quest_id,
        burden=burden_id,
        route=route_id,
        tool=tool_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        quest = QUESTS[params.quest]
        burden = BURDENS[params.burden]
        route = ROUTES[params.route]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"Unknown parameter choice: {err}") from None

    if burden.needed_for != params.quest:
        raise StoryError(explain_rejection(params.quest, params.burden, params.route, params.tool))
    if not can_finish(burden, route, tool, teamwork=True):
        raise StoryError(explain_rejection(params.quest, params.burden, params.route, params.tool))

    world = tell(
        setting=setting,
        quest=quest,
        burden=burden,
        route=route,
        tool=tool,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, quest, burden, route, tool) combos:\n")
        for setting_id, quest_id, burden_id, route_id, tool_id in combos:
            print(f"  {setting_id:8} {quest_id:7} {burden_id:7} {route_id:10} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lead_name} & {p.partner_name}: {p.quest} via {p.route} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
