#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/major_happy_ending_bad_ending_superhero_story.py
============================================================================

A standalone story world for a child-facing superhero tale with both happy and
bad endings.

Premise
-------
A cape-wearing child playing superhero sees a wind-blown festival item get stuck
up high. The child calls it a "major problem" and asks a calm grown-up helper to
save the day with some tool. The world model decides whether the chosen plan is
reasonable, and whether it works in time.

Core constraints
----------------
A rescue plan is only valid when:
- the method is sensible enough for a children's story,
- the helper is someone who can use that method,
- the method can physically reach the stuck item.

After that, the ending depends on whether the rescue power beats the danger:
- higher place + stronger wind + more delay = harder rescue
- sturdier item + stronger method + steadier helper = better rescue odds

This yields both:
- Happy endings: the item is brought down safely and the festival can begin.
- Bad endings: the item tears or blows away before it can be saved, though
  everyone remains safe and the characters learn to ask for the safe plan early.

Run it
------
    python storyworlds/worlds/gpt-5.4/major_happy_ending_bad_ending_superhero_story.py
    python storyworlds/worlds/gpt-5.4/major_happy_ending_bad_ending_superhero_story.py --item banner --perch roof --helper custodian --method ladder
    python storyworlds/worlds/gpt-5.4/major_happy_ending_bad_ending_superhero_story.py --method trampoline
    python storyworlds/worlds/gpt-5.4/major_happy_ending_bad_ending_superhero_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/major_happy_ending_bad_ending_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    traits: list[str] = field(default_factory=list)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man", "custodian", "firefighter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher": "teacher",
            "custodian": "custodian",
            "firefighter": "firefighter",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class FestivalItem:
    id: str
    label: str
    phrase: str
    color: str
    sturdiness: int
    ending_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    height: int
    exposure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    skill: int
    methods: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    reach: int
    power: int
    sense: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "sidekick"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stuck_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["stuck"] < THRESHOLD:
        return []
    sig = ("worry", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
        kid.memes["brave"] += 1
    if "sky" in world.entities:
        world.get("sky").meters["danger"] += world.facts["perch"].exposure
    return []


def _r_rescue_relief(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["rescued"] < THRESHOLD:
        return []
    sig = ("relief", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    helper = world.entities.get("helper")
    if helper is not None:
        helper.memes["care"] += 1
    return []


def _r_loss_sadness(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["lost"] < THRESHOLD:
        return []
    sig = ("sad", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["sad"] += 1
    helper = world.entities.get("helper")
    if helper is not None:
        helper.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stuck_worry", tag="emotion", apply=_r_stuck_worry),
    Rule(name="rescue_relief", tag="emotion", apply=_r_rescue_relief),
    Rule(name="loss_sadness", tag="emotion", apply=_r_loss_sadness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ITEMS = {
    "banner": FestivalItem(
        id="banner",
        label="banner",
        phrase="the big blue hero banner",
        color="blue",
        sturdiness=2,
        ending_name="banner",
        tags={"banner", "festival"},
    ),
    "cape": FestivalItem(
        id="cape",
        label="cape",
        phrase="the bright red parade cape",
        color="red",
        sturdiness=1,
        ending_name="cape",
        tags={"cape", "festival"},
    ),
    "kite": FestivalItem(
        id="kite",
        label="kite",
        phrase="the silver star kite",
        color="silver",
        sturdiness=1,
        ending_name="kite",
        tags={"kite", "wind"},
    ),
}

PERCHES = {
    "bush": Perch(
        id="bush",
        label="bush",
        phrase="the top of a round hedge",
        height=1,
        exposure=0,
        tags={"bush"},
    ),
    "tree": Perch(
        id="tree",
        label="tree",
        phrase="a high tree branch",
        height=2,
        exposure=1,
        tags={"tree", "wind"},
    ),
    "roof": Perch(
        id="roof",
        label="roof",
        phrase="the edge of the gym roof",
        height=3,
        exposure=2,
        tags={"roof", "wind"},
    ),
}

HELPERS = {
    "teacher": Helper(
        id="teacher",
        type="teacher",
        label="the teacher",
        skill=1,
        methods={"grabber", "ladder"},
        tags={"teacher", "adult_help"},
    ),
    "custodian": Helper(
        id="custodian",
        type="custodian",
        label="the custodian",
        skill=2,
        methods={"grabber", "ladder"},
        tags={"custodian", "adult_help", "ladder"},
    ),
    "firefighter": Helper(
        id="firefighter",
        type="firefighter",
        label="the firefighter",
        skill=2,
        methods={"grabber", "ladder", "hook_pole"},
        tags={"firefighter", "adult_help", "ladder"},
    ),
}

METHODS = {
    "grabber": Method(
        id="grabber",
        label="grabber pole",
        phrase="a long grabber pole",
        reach=2,
        power=1,
        sense=3,
        tags={"grabber"},
    ),
    "ladder": Method(
        id="ladder",
        label="ladder",
        phrase="a tall ladder",
        reach=3,
        power=2,
        sense=3,
        tags={"ladder"},
    ),
    "hook_pole": Method(
        id="hook_pole",
        label="rescue hook",
        phrase="a rescue hook on a strong pole",
        reach=3,
        power=3,
        sense=4,
        tags={"hook", "firefighter"},
    ),
    "trampoline": Method(
        id="trampoline",
        label="trampoline jump",
        phrase="a bouncy trampoline jump",
        reach=1,
        power=0,
        sense=1,
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Lucy", "Rose", "Ella"]
BOY_NAMES = ["Max", "Leo", "Finn", "Eli", "Jack", "Theo", "Sam", "Noah"]
ALIASES = ["Major Meteor", "Major Moon", "Major Spark", "Major Star", "Major Thunder"]
SIDEKICKS = ["Comet Kid", "Nova Pal", "Sky Scout", "Flash Friend", "Rocket Buddy"]
TRAITS = ["brave", "hopeful", "quick", "kind", "careful", "cheerful"]


def helper_can_use(helper: Helper, method: Method) -> bool:
    return method.id in helper.methods


def method_reaches(method: Method, perch: Perch) -> bool:
    return method.reach >= perch.height


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_plan(item: FestivalItem, perch: Perch, helper: Helper, method: Method) -> bool:
    return method.sense >= SENSE_MIN and helper_can_use(helper, method) and method_reaches(method, perch)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for perch_id, perch in PERCHES.items():
            for helper_id, helper in HELPERS.items():
                for method_id, method in METHODS.items():
                    if valid_plan(item, perch, helper, method):
                        combos.append((item_id, perch_id, helper_id, method_id))
    return combos


def severity(perch: Perch, delay: int) -> int:
    return perch.height + perch.exposure + delay


def rescue_power(item: FestivalItem, helper: Helper, method: Method) -> int:
    return item.sturdiness + helper.skill + method.power


def outcome_for(item: FestivalItem, perch: Perch, helper: Helper, method: Method, delay: int) -> str:
    if not valid_plan(item, perch, helper, method):
        raise StoryError(explain_rejection(item, perch, helper, method))
    return "saved" if rescue_power(item, helper, method) >= severity(perch, delay) else "lost"


@dataclass
class StoryParams:
    item: str
    perch: str
    helper: str
    method: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    alias: str
    sidekick_alias: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def intro(world: World, hero: Entity, sidekick: Entity, item: FestivalItem) -> None:
    world.say(
        f"On the morning of the school hero festival, {hero.id} tied on a cape and whispered that today {hero.pronoun()} was {hero.attrs['alias']}."
    )
    world.say(
        f"{sidekick.id} grinned and said {sidekick.pronoun()} would be {sidekick.attrs['alias']}. Together they marched across the playground as if the whole day were waiting for superheroes."
    )
    world.say(
        f"Near the gate, {item.phrase} fluttered over the walk, ready to make the festival shine."
    )


def gust(world: World, hero: Entity, sidekick: Entity, item_ent: Entity, perch: Perch) -> None:
    item_ent.meters["stuck"] += 1
    item_ent.meters["height"] = float(perch.height)
    propagate(world, narrate=False)
    world.say(
        f"Then a gust of wind swooped through the yard. It snatched the {item_ent.label} and tossed it onto {perch.phrase}."
    )
    world.say(
        f'"That is a major problem!" {hero.id} cried. {sidekick.id} looked up until {sidekick.pronoun("possessive")} eyes went wide.'
    )


def ask_for_help(world: World, hero: Entity, sidekick: Entity, helper: Entity, method: Method, perch: Perch) -> None:
    hero.memes["hope"] += 1
    sidekick.memes["hope"] += 1
    world.say(
        f'{hero.id} straightened {hero.pronoun("possessive")} shoulders. "A real hero gets help the safe way," {hero.pronoun()} said.'
    )
    world.say(
        f"They ran to {helper.label} and pointed up at {perch.phrase}. {helper.label.capitalize()} listened, nodded, and brought {method.phrase}."
    )


def rescue_success(world: World, helper: Entity, item_ent: Entity, item: FestivalItem, perch: Perch, method: Method) -> None:
    item_ent.meters["rescued"] += 1
    item_ent.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.label.capitalize()} set {method.phrase} just right, reached up toward {perch.phrase}, and eased the {item.label} down before the wind could tug again."
    )
    world.say(
        f"The {item.label} was wrinkled, but safe. {item.phrase.capitalize()} soon fluttered in its place again."
    )


def celebrate(world: World, hero: Entity, sidekick: Entity, helper: Entity, item: FestivalItem) -> None:
    world.say(
        f'{hero.id} threw both hands into the air. "{hero.attrs["alias"]} reports a happy ending!" {hero.pronoun()} cheered.'
    )
    world.say(
        f"{sidekick.id} laughed, and {helper.label} gave them a warm smile. When the festival music started, the {item.ending_name} waved above everyone like a superhero flag."
    )


def rescue_fail(world: World, helper: Entity, item_ent: Entity, item: FestivalItem, perch: Perch, method: Method) -> None:
    item_ent.meters["lost"] += 1
    item_ent.meters["stuck"] = 0.0
    item_ent.meters["torn"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label.capitalize()} hurried over with {method.phrase}, but the wind kept pulling and snapping at the {item.label}."
    )
    world.say(
        f"Just as {helper.pronoun()} reached toward {perch.phrase}, the {item.label} tore free and sailed away across the far fence."
    )


def comfort_and_lesson(world: World, hero: Entity, sidekick: Entity, helper: Entity, item: FestivalItem) -> None:
    world.say(
        f"For a moment, the playground felt smaller and sadder. {hero.id} swallowed hard, and {sidekick.id} leaned close beside {hero.pronoun('object')}."
    )
    world.say(
        f'{helper.label.capitalize()} knelt down and said, "This one had a bad ending for the {item.label}, but not for you. You did the right thing by asking for a grown-up instead of trying something risky."'
    )
    world.say(
        f"Later, the children made paper stars and taped them by the gate, and the festival began in a quieter, kinder way."
    )


def tell(
    item: FestivalItem,
    perch: Perch,
    helper_cfg: Helper,
    method: Method,
    hero_name: str,
    hero_gender: str,
    sidekick_name: str,
    sidekick_gender: str,
    alias: str,
    sidekick_alias: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait],
        attrs={"alias": alias},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type=sidekick_gender,
        role="sidekick",
        traits=["loyal"],
        attrs={"alias": sidekick_alias},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        traits=["calm"],
    ))
    item_ent = world.add(Entity(
        id="item",
        type="item",
        label=item.label,
        phrase=item.phrase,
        tags=set(item.tags),
    ))
    world.add(Entity(id="sky", type="sky", label="the sky"))
    intro(world, hero, sidekick, item)

    world.para()
    gust(world, hero, sidekick, item_ent, perch)
    ask_for_help(world, hero, sidekick, helper, method, perch)

    world.para()
    world.facts["severity"] = severity(perch, delay)
    world.facts["power"] = rescue_power(item, helper_cfg, method)
    if outcome_for(item, perch, helper_cfg, method, delay) == "saved":
        rescue_success(world, helper, item_ent, item, perch, method)
        celebrate(world, hero, sidekick, helper, item)
        ending = "happy"
    else:
        rescue_fail(world, helper, item_ent, item, perch, method)
        comfort_and_lesson(world, hero, sidekick, helper, item)
        ending = "bad"

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        helper=helper,
        item_cfg=item,
        perch=perch,
        method=method,
        item=item_ent,
        ending=ending,
        rescued=item_ent.meters["rescued"] >= THRESHOLD,
        lost=item_ent.meters["lost"] >= THRESHOLD,
        delay=delay,
    )
    return world


KNOWLEDGE = {
    "wind": [(
        "What does a strong gust of wind do?",
        "A strong gust of wind is a quick, hard push of air. It can lift light things, flap cloth, and blow toys or banners into high places."
    )],
    "ladder": [(
        "What is a ladder for?",
        "A ladder helps a grown-up reach something high in a safer way. You hold it steady and climb carefully."
    )],
    "grabber": [(
        "What is a grabber pole?",
        "A grabber pole is a long tool with a little gripper on the end. It helps you pick up or pull down things that are just out of reach."
    )],
    "firefighter": [(
        "Why do firefighters have rescue tools?",
        "Firefighters use rescue tools to reach high or hard places safely. They are trained to help when ordinary reaching is not enough."
    )],
    "banner": [(
        "What is a banner?",
        "A banner is a long piece of cloth or paper with words or pictures on it. People hang banners up to decorate a place or celebrate something."
    )],
    "cape": [(
        "What is a cape?",
        "A cape is a cloth that hangs from your shoulders. In pretend play, children often wear one to feel like a superhero."
    )],
    "kite": [(
        "Why can a kite get stuck in a tree?",
        "A kite is light and catches the wind easily. If the wind pulls it the wrong way, it can snag on branches."
    )],
    "adult_help": [(
        "Why should children ask a grown-up for help with high things?",
        "High places can be dangerous to reach alone. A grown-up can choose the right tool and keep everyone safe."
    )],
}
KNOWLEDGE_ORDER = ["wind", "banner", "cape", "kite", "grabber", "ladder", "firefighter", "adult_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    perch = f["perch"]
    method = f["method"]
    ending = f["ending"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "major". '
        f"The hero should face a windy rescue problem involving a {item.label} stuck on {perch.phrase}."
    )
    if ending == "happy":
        return [
            base,
            f"Tell a superhero story where {hero.id}, also called {hero.attrs['alias']}, asks for safe help and gets a happy ending.",
            f"Write a gentle rescue tale where a child hero uses {method.label} the safe way with a grown-up and the day ends with cheering.",
        ]
    return [
        base,
        f"Tell a superhero story where {hero.id}, also called {hero.attrs['alias']}, does the safe thing by asking for help, but the wind is too strong and the ending is sad.",
        f"Write a child-facing bad-ending rescue story where nobody gets hurt, but the lost {item.label} teaches the heroes to ask for the safe plan early.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    helper = f["helper"]
    item = f["item_cfg"]
    perch = f["perch"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who pretended to be {hero.attrs['alias']}, and {sidekick.id}, the sidekick. {helper.label.capitalize()} also helped when the problem became too big for children alone."
        ),
        (
            f"What was the major problem?",
            f"A gust of wind blew the {item.label} onto {perch.phrase}. That mattered because the {item.label} was part of the festival and it was stuck up high."
        ),
        (
            f"Why did {hero.id} go to {helper.label}?",
            f"{hero.id} wanted to save the day, but knew the safe way was to ask a grown-up for help. The {item.label} was too high for children to reach by themselves."
        ),
        (
            f"How did {helper.label} try to help?",
            f"{helper.label.capitalize()} brought {method.phrase} and tried to bring the {item.label} down from {perch.phrase}. That plan matched the rescue instead of turning it into a dangerous climb."
        ),
    ]
    if f["ending"] == "happy":
        qa.append((
            "How did the story end?",
            f"It ended happily because the {item.label} came down safely and the festival could begin. The last change you can see is the {item.ending_name} waving again while everyone cheers."
        ))
        qa.append((
            f"Why did the rescue work?",
            f"The helper used a tool that could really reach the high place. They also moved in time, before the wind could pull the {item.label} away."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It had a bad ending for the {item.label} because the wind tore it free and carried it away. But it was not a bad ending for the children, because everyone stayed safe and learned from it."
        ))
        qa.append((
            f"What did {hero.id} learn?",
            f"{hero.id} learned that asking early for the safe plan matters. Even though the ending was sad, the children still acted like real heroes by not trying a risky climb."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["item_cfg"].tags) | set(f["perch"].tags) | set(f["method"].tags) | set(HELPERS[f["helper"].type if False else "teacher"].tags if False else set())
    tags |= set(HELPERS[f["helper"].type if False else "teacher"].tags if False else set())
    helper_cfg = HELPERS[f["helper"].type] if f["helper"].type in HELPERS else None
    if helper_cfg is not None:
        tags |= set(helper_cfg.tags)
    tags.add("adult_help")
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
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
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="banner",
        perch="tree",
        helper="custodian",
        method="ladder",
        hero_name="Max",
        hero_gender="boy",
        sidekick_name="Lily",
        sidekick_gender="girl",
        alias="Major Meteor",
        sidekick_alias="Nova Pal",
        trait="brave",
        delay=0,
    ),
    StoryParams(
        item="kite",
        perch="roof",
        helper="teacher",
        method="ladder",
        hero_name="Mia",
        hero_gender="girl",
        sidekick_name="Finn",
        sidekick_gender="boy",
        alias="Major Moon",
        sidekick_alias="Sky Scout",
        trait="hopeful",
        delay=2,
    ),
    StoryParams(
        item="cape",
        perch="bush",
        helper="teacher",
        method="grabber",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Zoe",
        sidekick_gender="girl",
        alias="Major Spark",
        sidekick_alias="Rocket Buddy",
        trait="quick",
        delay=0,
    ),
    StoryParams(
        item="banner",
        perch="roof",
        helper="firefighter",
        method="hook_pole",
        hero_name="Ava",
        hero_gender="girl",
        sidekick_name="Noah",
        sidekick_gender="boy",
        alias="Major Star",
        sidekick_alias="Flash Friend",
        trait="kind",
        delay=0,
    ),
    StoryParams(
        item="cape",
        perch="roof",
        helper="custodian",
        method="ladder",
        hero_name="Nora",
        hero_gender="girl",
        sidekick_name="Sam",
        sidekick_gender="boy",
        alias="Major Thunder",
        sidekick_alias="Comet Kid",
        trait="careful",
        delay=2,
    ),
]


def explain_rejection(item: FestivalItem, perch: Perch, helper: Helper, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: '{method.id}' is too unsafe for this world. A superhero story for little children should prefer safe plans with grown-up help.)"
        )
    if not helper_can_use(helper, method):
        return (
            f"(No story: {helper.label.capitalize()} would not use {method.label}. Pick a helper who really uses that tool.)"
        )
    if not method_reaches(method, perch):
        return (
            f"(No story: {method.label.capitalize()} cannot reach {perch.phrase}. Pick a taller tool or a lower perch.)"
        )
    return (
        f"(No story: this rescue plan does not make sense for the {item.label} on {perch.phrase}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return outcome_for(
        ITEMS[params.item],
        PERCHES[params.perch],
        HELPERS[params.helper],
        METHODS[params.method],
        params.delay,
    )


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
reachable(M, P) :- method(M), perch(P), reach(M, R), height(P, H), R >= H.
helper_can(H, M) :- helper(H), allows(H, M).
valid(I, P, H, M) :- item(I), perch(P), helper(H), method(M),
                     sensible(M), reachable(M, P), helper_can(H, M).

severity(P, D, V) :- height(P, H), exposure(P, E), delay(D), V = H + E + D.
power(I, H, M, V) :- sturdiness(I, S), skill(H, K), force(M, F), V = S + K + F.

saved :- chosen(I, P, H, M), delay(D), valid(I, P, H, M),
         severity(P, D, Sv), power(I, H, M, Pw), Pw >= Sv.
lost  :- chosen(I, P, H, M), delay(D), valid(I, P, H, M),
         severity(P, D, Sv), power(I, H, M, Pw), Pw < Sv.

outcome(saved) :- saved.
outcome(lost) :- lost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("sturdiness", item_id, item.sturdiness))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("height", perch_id, perch.height))
        lines.append(asp.fact("exposure", perch_id, perch.exposure))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("skill", helper_id, helper.skill))
        for method_id in sorted(helper.methods):
            lines.append(asp.fact("allows", helper_id, method_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("reach", method_id, method.reach))
        lines.append(asp.fact("force", method_id, method.power))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen", params.item, params.perch, params.helper, params.method),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for seed in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

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
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="")
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child superhero, a windy rescue, and either a happy or bad ending."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the wind gets to tug before the rescue")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible rescue plans derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item is not None and args.item not in ITEMS:
        raise StoryError("(No story: unknown item.)")
    if args.perch is not None and args.perch not in PERCHES:
        raise StoryError("(No story: unknown perch.)")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError("(No story: unknown helper.)")
    if args.method is not None and args.method not in METHODS:
        raise StoryError("(No story: unknown method.)")

    if args.item and args.perch and args.helper and args.method:
        item = ITEMS[args.item]
        perch = PERCHES[args.perch]
        helper = HELPERS[args.helper]
        method = METHODS[args.method]
        if not valid_plan(item, perch, helper, method):
            raise StoryError(explain_rejection(item, perch, helper, method))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.perch is None or combo[1] == args.perch)
        and (args.helper is None or combo[2] == args.helper)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid rescue plan matches the given options.)")

    item_id, perch_id, helper_id, method_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    sidekick_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    sidekick_name = _pick_name(rng, sidekick_gender, avoid=hero_name)
    alias = rng.choice(ALIASES)
    sidekick_alias = rng.choice(SIDEKICKS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        item=item_id,
        perch=perch_id,
        helper=helper_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        alias=alias,
        sidekick_alias=sidekick_alias,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError("(No story: invalid item in params.)")
    if params.perch not in PERCHES:
        raise StoryError("(No story: invalid perch in params.)")
    if params.helper not in HELPERS:
        raise StoryError("(No story: invalid helper in params.)")
    if params.method not in METHODS:
        raise StoryError("(No story: invalid method in params.)")

    item = ITEMS[params.item]
    perch = PERCHES[params.perch]
    helper = HELPERS[params.helper]
    method = METHODS[params.method]
    if not valid_plan(item, perch, helper, method):
        raise StoryError(explain_rejection(item, perch, helper, method))

    world = tell(
        item=item,
        perch=perch,
        helper_cfg=helper,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        alias=params.alias,
        sidekick_alias=params.sidekick_alias,
        trait=params.trait,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (item, perch, helper, method) combos:\n")
        for item, perch, helper, method in combos:
            print(f"  {item:7} {perch:5} {helper:11} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} as {p.alias}: {p.item} on {p.perch} ({outcome_of(p)})"
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
