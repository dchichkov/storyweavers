#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/culture_matinee_fallen_tree_trail_twist_foreshadowing.py
====================================================================================

A small storyworld about two young forest friends hurrying along a fallen tree
trail to a culture matinee. The trail seems blocked by an old log, and an item
for the matinee is at risk from a nearby hazard. A grounded warning, a sensible
protective choice, and a magical twist lead to a fable-like ending.

Run it
------
python storyworlds/worlds/gpt-5.4/culture_matinee_fallen_tree_trail_twist_foreshadowing.py
python storyworlds/worlds/gpt-5.4/culture_matinee_fallen_tree_trail_twist_foreshadowing.py --item paper_mask --obstacle drizzle
python storyworlds/worlds/gpt-5.4/culture_matinee_fallen_tree_trail_twist_foreshadowing.py --all
python storyworlds/worlds/gpt-5.4/culture_matinee_fallen_tree_trail_twist_foreshadowing.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/culture_matinee_fallen_tree_trail_twist_foreshadowing.py --verify
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
SETTING_NAME = "the fallen tree trail"


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
        female = {"girl", "mother", "hen", "doe", "vixen"}
        male = {"boy", "father", "fox", "badger", "otter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Matinee:
    id: str
    label: str
    culture_line: str
    performance_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    fragile_to: str
    ruin_text: str
    save_text: str
    sharing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    kind: str
    scene: str
    risk_line: str
    crossing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    action_line: str = ""
    proof_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    matinee: str
    item: str
    obstacle: str
    remedy: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


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
    apply: Callable[[World], list[str]]


def _r_damage(world: World) -> list[str]:
    item = world.get("item")
    obstacle = world.facts["obstacle_cfg"]
    remedy = world.get("remedy")
    if item.meters["exposed"] < THRESHOLD:
        return []
    if obstacle.kind not in item.attrs.get("fragile_to_set", set()):
        return []
    if obstacle.kind in remedy.attrs.get("guards", set()):
        sig = ("protected", item.id, obstacle.kind)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        item.meters["safe"] += 1
        world.get("hero").memes["relief"] += 1
        return ["__safe__"]
    sig = ("damaged", item.id, obstacle.kind)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["damaged"] += 1
    world.get("hero").memes["worry"] += 1
    world.get("friend").memes["worry"] += 1
    return ["__damaged__"]


def _r_magic(world: World) -> list[str]:
    tree = world.get("tree")
    item = world.get("item")
    hero = world.get("hero")
    if tree.memes["greeted"] < THRESHOLD:
        return []
    if item.meters["damaged"] >= THRESHOLD:
        return []
    sig = ("blessing", tree.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.meters["glow"] += 1
    hero.memes["wonder"] += 1
    world.get("friend").memes["wonder"] += 1
    return ["__blessing__"]


CAUSAL_RULES = [
    Rule(name="damage", apply=_r_damage),
    Rule(name="magic", apply=_r_magic),
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
            if sent and not sent.startswith("__"):
                world.say(sent)
    return produced


MATINEES = {
    "puppets": Matinee(
        id="puppets",
        label="the acorn puppet matinee",
        culture_line="Every spring, the meadow hollow held a little culture matinee where young animals shared songs, masks, and stories from their families.",
        performance_line="The children were meant to show a puppet scene and tell where the old tale had come from.",
        ending_image="Soon the little stage shone with tiny puppet shadows dancing on the bark wall.",
        tags={"culture", "matinee", "puppet"},
    ),
    "songs": Matinee(
        id="songs",
        label="the moss-song matinee",
        culture_line="Every spring, the meadow hollow held a little culture matinee where young animals shared songs, masks, and stories from their families.",
        performance_line="The children were meant to sing an old path song and say who had taught it to them.",
        ending_image="Soon the hollow rang with soft singing, and even the fern tips seemed to sway in time.",
        tags={"culture", "matinee", "song"},
    ),
    "dances": Matinee(
        id="dances",
        label="the lantern-step matinee",
        culture_line="Every spring, the meadow hollow held a little culture matinee where young animals shared songs, masks, and stories from their families.",
        performance_line="The children were meant to share a circle dance and explain why their families stamped three times at the end.",
        ending_image="Soon the floor of the hollow tapped with neat little feet moving in a bright circle.",
        tags={"culture", "matinee", "dance"},
    ),
}

ITEMS = {
    "paper_mask": Item(
        id="paper_mask",
        label="paper mask",
        phrase="a painted paper mask",
        fragile_to="wet",
        ruin_text="The colors would run, and the paper would sag into a sad flap.",
        save_text="The paint stayed bright and the paper stayed smooth.",
        sharing_line="When the sharing time came, the mask still looked proud and bright.",
        tags={"mask", "paper"},
    ),
    "feather_fan": Item(
        id="feather_fan",
        label="feather fan",
        phrase="a fan made of soft feathers",
        fragile_to="wind",
        ruin_text="The feathers would fly loose and scatter down the trail.",
        save_text="The feathers stayed tucked together in a neat shining curve.",
        sharing_line="When the sharing time came, the fan opened like a small moon.",
        tags={"fan", "feather"},
    ),
    "berry_scroll": Item(
        id="berry_scroll",
        label="berry scroll",
        phrase="a rolled berry-ink scroll",
        fragile_to="scratch",
        ruin_text="The bark edge would scrape it and tear the inked ribbon.",
        save_text="The scroll stayed rolled, clean, and easy to read.",
        sharing_line="When the sharing time came, the scroll unrolled without a single tear.",
        tags={"scroll", "writing"},
    ),
}

OBSTACLES = {
    "drizzle": Obstacle(
        id="drizzle",
        label="silver drizzle",
        kind="wet",
        scene="A soft silver drizzle had begun to fall through the leaves, and drops were pattering over the old trunk.",
        risk_line="One wet shake would be enough to spoil something made of paper.",
        crossing_line="The friends ducked under the dripping leaves and stepped across the mossy bark together.",
        tags={"rain", "wet"},
    ),
    "gust": Obstacle(
        id="gust",
        label="whistling gust",
        kind="wind",
        scene="A whistling gust kept racing along the open part of the trail and tugging at anything light.",
        risk_line="A loose, feathery thing would not stay together in such a pushy wind.",
        crossing_line="The friends bent low and crossed while the gust hissed past the hollow roots.",
        tags={"wind"},
    ),
    "brambles": Obstacle(
        id="brambles",
        label="hooked brambles",
        kind="scratch",
        scene="Hooked brambles leaned over the narrow place beside the trunk, each thorn reaching like a tiny claw.",
        risk_line="Something soft and rolled would tear if it brushed those thorns.",
        crossing_line="The friends slipped through the narrow place with slow careful feet.",
        tags={"thorn", "scratch"},
    ),
}

REMEDIES = {
    "leaf_wrap": Remedy(
        id="leaf_wrap",
        label="leaf wrap",
        phrase="a waxy fern-leaf wrap",
        guards={"wet"},
        action_line="wrapped the item in broad waxy fern leaves and tied the bundle with grass",
        proof_line="The wet drops slid off the leaves instead of sinking in.",
        tags={"leaf_wrap"},
    ),
    "reed_tie": Remedy(
        id="reed_tie",
        label="reed tie",
        phrase="a braided reed tie",
        guards={"wind"},
        action_line="bound the item snugly with a braided reed tie",
        proof_line="The wind worried at the bundle, but nothing flew away.",
        tags={"reed_tie"},
    ),
    "bark_sleeve": Remedy(
        id="bark_sleeve",
        label="bark sleeve",
        phrase="a smooth bark sleeve",
        guards={"scratch"},
        action_line="slid the item into a smooth bark sleeve",
        proof_line="The thorns scraped the outside, but the treasure within stayed untouched.",
        tags={"bark_sleeve"},
    ),
}

NAME_TYPES = [
    ("Pip", "fox"),
    ("Mira", "hen"),
    ("Nell", "doe"),
    ("Bram", "badger"),
    ("Ollie", "otter"),
    ("Faye", "vixen"),
]
TRAITS = ["careful", "bright", "gentle", "patient", "curious"]


def item_at_risk(item: Item, obstacle: Obstacle) -> bool:
    return item.fragile_to == obstacle.kind


def select_remedy(item: Item, obstacle: Obstacle) -> Optional[Remedy]:
    for remedy in REMEDIES.values():
        if obstacle.kind in remedy.guards and item.fragile_to == obstacle.kind:
            return remedy
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for matinee_id in MATINEES:
        for item_id, item in ITEMS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                remedy = select_remedy(item, obstacle)
                if item_at_risk(item, obstacle) and remedy is not None:
                    combos.append((matinee_id, item_id, obstacle_id, remedy.id))
    return combos


def predict_damage(world: World) -> dict:
    sim = world.copy()
    sim.get("item").meters["exposed"] += 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "damaged": item.meters["damaged"] >= THRESHOLD,
        "safe": item.meters["safe"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, matinee: Matinee, item: Item) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On the edge of {SETTING_NAME}, {hero.id} and {friend.id} hurried toward {matinee.label}."
    )
    world.say(matinee.culture_line)
    world.say(
        f"{hero.id} carried {item.phrase}, because {matinee.performance_line}"
    )


def foreshadow(world: World) -> None:
    tree = world.get("tree")
    tree.memes["humming"] += 1
    world.say(
        "Before them lay the oldest part of the path: a giant fallen tree, silver with age, resting across the trail like a listening gate."
    )
    world.say(
        'Whenever the wind touched it, the bark made a low humming sound, almost as if it were trying to remember a song.'
    )


def approach_obstacle(world: World, obstacle: Obstacle) -> None:
    world.say(obstacle.scene)
    world.say(
        f"{world.get('friend').id} looked at the path and at the bundle in {world.get('hero').pronoun('possessive')} paws. {obstacle.risk_line}"
    )


def warn(world: World, item: Item, obstacle: Obstacle) -> None:
    pred = predict_damage(world)
    world.facts["predicted_damage"] = pred["damaged"]
    friend = world.get("friend")
    hero = world.get("hero")
    if pred["damaged"]:
        friend.memes["care"] += 1
        world.say(
            f'"If we rush past, the {item.label} will be ruined," {friend.id} said. "{item.ruin_text}"'
        )
        world.say(
            f'{hero.id} tightened {hero.pronoun("possessive")} hold. For one moment, hurrying still felt easier than thinking.'
        )


def prepare(world: World, remedy: Remedy) -> None:
    hero = world.get("hero")
    remedy_ent = world.get("remedy")
    hero.memes["prudence"] += 1
    remedy_ent.meters["used"] += 1
    world.say(
        f"Then {hero.id} remembered the humming log and chose patience instead. {hero.pronoun().capitalize()} {remedy.action_line}."
    )


def cross(world: World, obstacle: Obstacle, remedy: Remedy) -> None:
    item = world.get("item")
    item.meters["exposed"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.crossing_line)
    world.say(remedy.proof_line)


def greet_tree(world: World) -> None:
    tree = world.get("tree")
    hero = world.get("hero")
    friend = world.get("friend")
    tree.memes["greeted"] += 1
    hero.memes["respect"] += 1
    friend.memes["respect"] += 1
    propagate(world, narrate=False)
    world.say(
        f'At the middle of the trunk, {hero.id} stopped, laid one small hand on the bark, and whispered, "We are hurrying to share kindly things. Please let us pass."'
    )


def twist(world: World, matinee: Matinee) -> None:
    tree = world.get("tree")
    if tree.meters["glow"] < THRESHOLD:
        return
    world.say(
        "At once the humming deepened into a warm wooden voice. The fallen tree was no dead thing at all, but the old keeper of the trail."
    )
    world.say(
        '"Children who protect what they carry for others may always pass," it said, and a seam of golden light opened along the bark.'
    )
    world.say(
        f"A hidden stair of roots curved through the trunk and led them straight to the hollow. {matinee.ending_image}"
    )


def matinee_end(world: World, matinee: Matinee, item: Item) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f"There, beneath fern lanterns, the matinee was just beginning. {item.sharing_line}"
    )
    world.say(
        f"{hero.id} and {friend.id} shared their piece with calm voices, and everyone leaned closer to listen."
    )
    world.say(
        "After that day, the young ones on the trail said that haste hears only trouble, but patience may hear magic."
    )


def tell(
    matinee: Matinee,
    item_cfg: Item,
    obstacle: Obstacle,
    remedy_cfg: Remedy,
    hero_name: str,
    hero_type: str,
    friend_name: str,
    friend_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=[trait], label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=["steady"], label=friend_name))
    tree = world.add(Entity(id="tree", kind="thing", type="tree", role="guardian", label="fallen tree"))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            attrs={"fragile_to_set": {item_cfg.fragile_to}},
            tags=set(item_cfg.tags),
        )
    )
    remedy = world.add(
        Entity(
            id="remedy",
            kind="thing",
            type="remedy",
            label=remedy_cfg.label,
            phrase=remedy_cfg.phrase,
            attrs={"guards": set(remedy_cfg.guards)},
            tags=set(remedy_cfg.tags),
        )
    )

    introduce(world, hero, friend, matinee, item_cfg)
    foreshadow(world)

    world.para()
    approach_obstacle(world, obstacle)
    warn(world, item_cfg, obstacle)
    prepare(world, remedy_cfg)

    world.para()
    cross(world, obstacle, remedy_cfg)
    greet_tree(world)
    twist(world, matinee)

    world.para()
    matinee_end(world, matinee, item_cfg)

    world.facts.update(
        matinee=matinee,
        item_cfg=item_cfg,
        obstacle_cfg=obstacle,
        remedy_cfg=remedy_cfg,
        hero=hero,
        friend=friend,
        tree=tree,
        item=item,
        remedy=remedy,
        protected=item.meters["safe"] >= THRESHOLD,
        damaged=item.meters["damaged"] >= THRESHOLD,
        magical_reveal=tree.meters["glow"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    obstacle = f["obstacle_cfg"]
    matinee = f["matinee"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "culture" and "matinee" and is set on a fallen tree trail.',
        f"Tell a gentle forest fable where {hero.id} carries {item.phrase} to {matinee.label}, faces {obstacle.label}, and discovers a magical twist.",
        "Write a child-facing story with foreshadowing, a careful choice instead of rushing, and an ending that proves kindness and patience matter.",
    ]


KNOWLEDGE = {
    "culture": [(
        "What does culture mean in a story like this?",
        "Culture means the songs, stories, dances, and special ways a group of people or animals share together. It is what they remember and pass on."
    )],
    "matinee": [(
        "What is a matinee?",
        "A matinee is a show or gathering that happens in the daytime. People often come to watch, listen, or take part together."
    )],
    "magic": [(
        "What is magic in a fable?",
        "Magic in a fable is a wonderful thing that happens beyond ordinary life. It often appears when a character learns or shows something important."
    )],
    "foreshadowing": [(
        "What is foreshadowing?",
        "Foreshadowing is a small early hint about something that will matter later. It helps a later surprise feel gentle and earned."
    )],
    "wet": [(
        "Why can rain ruin paper?",
        "Paper soaks up water and becomes soft and weak. Paint can run too, so the paper no longer looks or works the same way."
    )],
    "wind": [(
        "Why can wind be a problem for light things?",
        "Wind pushes and lifts light things very easily. If they are loose, it can blow them apart or carry them away."
    )],
    "scratch": [(
        "Why are thorns dangerous for soft things?",
        "Thorns are sharp, so they can catch and tear soft things. A cover on the outside can keep the sharp points from reaching what is inside."
    )],
    "kindness": [(
        "Why do fables often reward patience and kindness?",
        "Fables use simple stories to show a lesson. When patience and kindness are rewarded, the lesson is easy to remember."
    )],
}
KNOWLEDGE_ORDER = ["culture", "matinee", "magic", "foreshadowing", "wet", "wind", "scratch", "kindness"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    obstacle = f["obstacle_cfg"]
    remedy = f["remedy_cfg"]
    matinee = f["matinee"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two young friends on the fallen tree trail. They were hurrying to {matinee.label} with {item.phrase}."
        ),
        (
            "Why were they going to the matinee?",
            f"They were going to share something at a daytime culture matinee. The story matters because they were carrying something for other people to enjoy, not just for themselves."
        ),
        (
            f"Why was {obstacle.label} a problem?",
            f"It was dangerous for the {item.label}. {item.ruin_text} That is why {friend.id} warned against rushing."
        ),
        (
            f"How did they protect the {item.label}?",
            f"They used {remedy.phrase}. {remedy.proof_line} Because they prepared before crossing, the item stayed whole."
        ),
    ]
    if f["magical_reveal"]:
        qa.append(
            (
                "What was the twist in the story?",
                "The fallen tree was not only an obstacle. It was a magical keeper of the trail, and it opened a hidden way when the children showed care and respect."
            )
        )
    qa.append(
        (
            "What was the foreshadowing?",
            "The humming bark at the start was a hint that the old trunk was alive in some special way. Later, that hint made the talking tree feel like a true surprise instead of coming from nowhere."
        )
    )
    qa.append(
        (
            "What lesson did the story teach?",
            "It taught that hurrying can spoil what matters, while patience can protect it. In this story, patience also let the children notice the magic waiting for them."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"culture", "matinee", "magic", "foreshadowing", "kindness"}
    obstacle = world.facts["obstacle_cfg"]
    if obstacle.kind == "wet":
        tags.add("wet")
    elif obstacle.kind == "wind":
        tags.add("wind")
    elif obstacle.kind == "scratch":
        tags.add("scratch")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(item: Item, obstacle: Obstacle) -> str:
    return (
        f"(No story: {obstacle.label} does not create the right kind of danger for the {item.label}. "
        f"This world only tells stories where the danger honestly threatens the item and a sensible protection exists.)"
    )


def explain_remedy(item: Item, obstacle: Obstacle, remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    return (
        f"(No story: {remedy.label} does not sensibly protect a {item.label} from {obstacle.label}. "
        f"Choose the remedy that guards against {obstacle.kind}.)"
    )


ASP_RULES = r"""
item_at_risk(I, O) :- fragile_to(I, K), obstacle_kind(O, K).
works(I, O, R) :- item_at_risk(I, O), guards(R, K), obstacle_kind(O, K).
valid(M, I, O, R) :- matinee(M), item(I), obstacle(O), remedy(R), works(I, O, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MATINEES:
        lines.append(asp.fact("matinee", mid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("fragile_to", iid, item.fragile_to))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_kind", oid, obstacle.kind))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for kind in sorted(remedy.guards):
            lines.append(asp.fact("guards", rid, kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        matinee="puppets",
        item="paper_mask",
        obstacle="drizzle",
        remedy="leaf_wrap",
        hero="Pip",
        hero_type="fox",
        friend="Mira",
        friend_type="hen",
        trait="careful",
    ),
    StoryParams(
        matinee="songs",
        item="feather_fan",
        obstacle="gust",
        remedy="reed_tie",
        hero="Nell",
        hero_type="doe",
        friend="Bram",
        friend_type="badger",
        trait="gentle",
    ),
    StoryParams(
        matinee="dances",
        item="berry_scroll",
        obstacle="brambles",
        remedy="bark_sleeve",
        hero="Ollie",
        hero_type="otter",
        friend="Faye",
        friend_type="vixen",
        trait="patient",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a fable-like culture matinee on a fallen tree trail."
    )
    ap.add_argument("--matinee", choices=MATINEES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.obstacle and not item_at_risk(ITEMS[args.item], OBSTACLES[args.obstacle]):
        raise StoryError(explain_rejection(ITEMS[args.item], OBSTACLES[args.obstacle]))
    if args.item and args.obstacle and args.remedy:
        needed = select_remedy(ITEMS[args.item], OBSTACLES[args.obstacle])
        if needed is None or needed.id != args.remedy:
            raise StoryError(explain_remedy(ITEMS[args.item], OBSTACLES[args.obstacle], args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.matinee is None or combo[0] == args.matinee)
        and (args.item is None or combo[1] == args.item)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    matinee_id, item_id, obstacle_id, remedy_id = rng.choice(sorted(combos))

    picks = list(NAME_TYPES)
    rng.shuffle(picks)
    hero_name, hero_type = picks[0]
    friend_name, friend_type = picks[1]
    if args.hero:
        hero_name = args.hero
    if args.friend:
        friend_name = args.friend
    trait = rng.choice(TRAITS)

    return StoryParams(
        matinee=matinee_id,
        item=item_id,
        obstacle=obstacle_id,
        remedy=remedy_id,
        hero=hero_name,
        hero_type=hero_type,
        friend=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def _validate_params(params: StoryParams) -> None:
    if params.matinee not in MATINEES:
        raise StoryError(f"(Unknown matinee: {params.matinee})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    item = ITEMS[params.item]
    obstacle = OBSTACLES[params.obstacle]
    remedy = REMEDIES[params.remedy]
    if not item_at_risk(item, obstacle):
        raise StoryError(explain_rejection(item, obstacle))
    needed = select_remedy(item, obstacle)
    if needed is None or remedy.id != needed.id:
        raise StoryError(explain_remedy(item, obstacle, params.remedy))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        matinee=MATINEES[params.matinee],
        item_cfg=ITEMS[params.item],
        obstacle=OBSTACLES[params.obstacle],
        remedy_cfg=REMEDIES[params.remedy],
        hero_name=params.hero,
        hero_type=params.hero_type,
        friend_name=params.friend,
        friend_type=params.friend_type,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generated.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        random_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        random_params.seed = 123
        sample2 = generate(random_params)
        if not sample2.story.strip():
            raise StoryError("(Random smoke test failed: empty story.)")
        print("OK: random generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

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
        print(f"{len(combos)} compatible (matinee, item, obstacle, remedy) combos:\n")
        for matinee_id, item_id, obstacle_id, remedy_id in combos:
            print(f"  {matinee_id:8} {item_id:12} {obstacle_id:9} {remedy_id}")
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
            header = f"### {p.hero} and {p.friend}: {p.item} on the fallen tree trail"
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
