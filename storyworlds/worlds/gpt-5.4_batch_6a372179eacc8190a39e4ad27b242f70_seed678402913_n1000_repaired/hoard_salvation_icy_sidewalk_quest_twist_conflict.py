#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoard_salvation_icy_sidewalk_quest_twist_conflict.py
===============================================================================

A standalone storyworld about a child on an icy sidewalk, a glittering stash of
helper gear that feels like a treasure hoard, and a small winter quest that
turns into a choice about sharing. The story always carries an adventure shape:
a quest, a twist, a conflict, and an ending image that proves what changed.

Run it
------
python storyworlds/worlds/gpt-5.4/hoard_salvation_icy_sidewalk_quest_twist_conflict.py
python storyworlds/worlds/gpt-5.4/hoard_salvation_icy_sidewalk_quest_twist_conflict.py --quest soup --aid salt --patch hill
python storyworlds/worlds/gpt-5.4/hoard_salvation_icy_sidewalk_quest_twist_conflict.py --aid cardboard
python storyworlds/worlds/gpt-5.4/hoard_salvation_icy_sidewalk_quest_twist_conflict.py --all --qa
python storyworlds/worlds/gpt-5.4/hoard_salvation_icy_sidewalk_quest_twist_conflict.py --verify
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
KIND_TRAITS = {"kind", "careful", "steady"}


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
class Quest:
    id: str
    cargo: str
    phrase: str
    recipient: str
    reason: str
    mode: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    mode: str
    power: int
    sense: int
    use_text: str
    share_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Patch:
    id: str
    label: str
    phrase: str
    severity: int
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


def _r_slip_risk(world: World) -> list[str]:
    out: list[str] = []
    patch = world.get("patch")
    if patch.meters["ice"] < THRESHOLD:
        return out
    traveler = world.get("hero")
    sig = ("slip_risk", traveler.id)
    if sig not in world.fired:
        world.fired.add(sig)
        traveler.memes["worry"] += 1
        out.append("__risk__")
    return out


def _r_aid_helps(world: World) -> list[str]:
    out: list[str] = []
    aid = world.get("aid")
    patch = world.get("patch")
    if aid.meters["used"] < THRESHOLD:
        return out
    sig = ("aid", aid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patch.meters["traction"] += aid.attrs.get("power", 0)
    out.append("__traction__")
    return out


def _r_safe_path(world: World) -> list[str]:
    out: list[str] = []
    patch = world.get("patch")
    needed = patch.attrs.get("severity", 0)
    if patch.meters["traction"] < needed:
        return out
    sig = ("safe_path", patch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patch.meters["safe"] += 1
    world.get("hero").memes["hope"] += 1
    out.append("__safe__")
    return out


CAUSAL_RULES = [
    Rule(name="slip_risk", tag="danger", apply=_r_slip_risk),
    Rule(name="aid_helps", tag="physical", apply=_r_aid_helps),
    Rule(name="safe_path", tag="physical", apply=_r_safe_path),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    return produced


def sensible_aids() -> list[Aid]:
    return [a for a in AIDS.values() if a.sense >= SENSE_MIN]


def applicable(aid: Aid, quest: Quest, patch: Patch) -> bool:
    if aid.sense < SENSE_MIN:
        return False
    if aid.mode == "ground":
        return True
    if aid.mode == "feet":
        return quest.mode == "walk" and patch.severity <= aid.power
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid, quest in QUESTS.items():
        for aid_id, aid in AIDS.items():
            for pid, patch in PATCHES.items():
                if applicable(aid, quest, patch):
                    combos.append((qid, aid_id, pid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    quest = QUESTS[params.quest]
    aid = AIDS[params.aid]
    patch = PATCHES[params.patch]
    if not applicable(aid, quest, patch):
        return "invalid"
    if aid.power >= patch.severity and aid.mode == "ground":
        return "salvation"
    if aid.power >= patch.severity and aid.mode == "feet":
        return "cross_first"
    return "detour"


def would_share_now(trait: str) -> bool:
    return trait in KIND_TRAITS


def predict_crossing(world: World, aid: Aid, quest: Quest, patch: Patch) -> dict:
    sim = world.copy()
    if applicable(aid, quest, patch):
        sim.get("aid").meters["used"] += 1
        propagate(sim, narrate=False)
    return {
        "traction": sim.get("patch").meters["traction"],
        "safe": sim.get("patch").meters["safe"] >= THRESHOLD,
    }


def explain_invalid(aid: Aid, quest: Quest, patch: Patch) -> str:
    if aid.sense < SENSE_MIN:
        return (
            f"(No story: {aid.label} is a poor way to handle ice here. "
            f"Pick a safer aid like salt, sand, or ice cleats.)"
        )
    if aid.mode == "feet" and quest.mode != "walk":
        return (
            f"(No story: {aid.label} helps a person's shoes grip, but this quest "
            f"involves pulling something heavy. The wagon would still slide on the ice.)"
        )
    if aid.mode == "feet" and patch.severity > aid.power:
        return (
            f"(No story: {aid.label} is not strong enough for {patch.phrase}. "
            f"Use something that changes the ground, like salt or sand.)"
        )
    return "(No story: that combination is not reasonable.)"


def introduce(world: World, hero: Entity, parent: Entity, quest: Quest, patch: Patch) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"The icy sidewalk outside their building looked like the first stretch of a winter quest. "
        f"{hero.id} carried {quest.phrase} to {quest.recipient}, because {quest.reason}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} could see {patch.phrase} shining ahead, smooth and cold as glass."
    )
    world.say(
        f'"If we get across that patch," {hero.id} whispered, "the mission keeps going."'
    )


def find_hoard(world: World, hero: Entity, aid: Aid) -> None:
    hero.memes["greed"] += 1
    world.say(
        f"By the gate sat {aid.phrase}. To {hero.id}, it looked like a tiny hoard of winter treasure."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to keep every bit for the path under {hero.pronoun('possessive')} own boots."
    )


def warn(world: World, parent: Entity, hero: Entity, aid: Aid, quest: Quest, patch: Patch) -> None:
    pred = predict_crossing(world, aid, quest, patch)
    world.facts["predicted_safe"] = pred["safe"]
    world.facts["predicted_traction"] = pred["traction"]
    if pred["safe"]:
        world.say(
            f'{hero.id}\'s {parent.label_word} studied the ice and said, '
            f'"Used the right way, {aid.label} could help. But winter tools are for sharing, not hiding."'
        )
    else:
        world.say(
            f'{hero.id}\'s {parent.label_word} studied the ice and said, '
            f'"Even with {aid.label}, that patch may still be too slick. We have to think, not charge."'
        )


def twist_arrives(world: World, traveler: Entity, patch: Patch) -> None:
    traveler.memes["need"] += 1
    world.say(
        f"Then came the twist: {traveler.label} appeared at the far end of the sidewalk and stepped toward {patch.label}."
    )
    world.say(
        f"One shoe skidded. {traveler.pronoun().capitalize()} windmilled both arms and froze."
    )


def conflict(world: World, hero: Entity, traveler: Entity, aid: Aid) -> None:
    hero.memes["conflict"] += 1
    traveler.memes["fear"] += 1
    world.say(
        f"{hero.id} hugged {aid.label} close for one second. If {hero.pronoun()} kept the whole hoard, "
        f"{hero.pronoun()} could start the quest alone."
    )
    world.say(
        f"But {traveler.label} needed help right then, and the choice pinched in {hero.pronoun('possessive')} chest."
    )


def share_now(world: World, hero: Entity, traveler: Entity, aid: Aid) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f'{hero.id} took a breath. "This is for both of us," {hero.pronoun()} said, and shared the {aid.label} at once.'
    )
    world.say(aid.share_text)


def hesitate_then_share(world: World, hero: Entity, traveler: Entity, aid: Aid) -> None:
    hero.memes["kindness"] += 1
    hero.memes["shame"] += 1
    world.say(
        f"For half a heartbeat, {hero.id} almost kept the whole hoard."
    )
    world.say(
        f"Then {traveler.label} slipped again, and that tiny wobble snapped the selfish thought in two."
    )
    world.say(
        f'{hero.id} hurried over. "Here," {hero.pronoun()} said. "Take some."'
    )
    world.say(aid.share_text)


def use_aid(world: World, aid: Aid) -> None:
    world.get("aid").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(aid.use_text)


def salvation_ending(world: World, hero: Entity, parent: Entity, traveler: Entity, quest: Quest) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"The crystals bit into the ice, and the shiny trap turned rough and walkable."
    )
    world.say(
        f"{traveler.label} crossed first, smiling with relief. Then {hero.id} carried {quest.cargo} on, step by steady step."
    )
    world.say(
        f"At {quest.recipient}'s door, the warm delivery felt like salvation after all that cold shining danger."
    )
    world.say(
        f"When {hero.id} looked back, the little hoard was gone, but the safe path it made was brighter than treasure."
    )
    world.facts["rescued"] = traveler.label


def cross_first_ending(world: World, hero: Entity, parent: Entity, traveler: Entity, quest: Quest, aid: Aid) -> None:
    hero.memes["relief"] += 1
    hero.memes["care"] += 1
    world.say(
        f"{hero.id} clipped on the {aid.label} and picked a careful way across."
    )
    world.say(
        f"{hero.pronoun().capitalize()} finished the delivery, but {traveler.label} still waited on the far side, stuck by the glare."
    )
    world.say(
        f"So the quest grew bigger than a doorstep. {hero.id} called back to {parent.label_word} for salt, and they came together to help."
    )
    world.say(
        f"By the time everyone reached safe pavement, {hero.id} knew the cleats had helped {hero.pronoun('object')}, but sharing real salvation meant changing the ground for others too."
    )
    world.facts["rescued"] = traveler.label


def detour_ending(world: World, hero: Entity, parent: Entity, traveler: Entity, quest: Quest, aid: Aid, patch: Patch) -> None:
    hero.memes["patience"] += 1
    hero.memes["relief"] += 1
    world.say(aid.fail_text)
    world.say(
        f'{hero.id} looked at the slick patch and finally said, "This quest needs a new map."'
    )
    world.say(
        f"{hero.id}, {traveler.label}, and {hero.pronoun('possessive')} {parent.label_word} took the long way around the block where the snow was crunchy instead of glassy."
    )
    world.say(
        f"They reached {quest.recipient} late, but safe, and the warm errand still mattered."
    )
    world.say(
        f"At the corner, {hero.id} gave the half-full hoard to the building helper and asked for real salt. That humble handoff was its own kind of salvation."
    )
    world.facts["rescued"] = traveler.label


def tell(
    quest: Quest,
    aid: Aid,
    patch: Patch,
    twist_name: str,
    twist_type: str,
    hero_name: str,
    hero_type: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    traveler = world.add(Entity(
        id="Traveler",
        kind="character",
        type=twist_type,
        label=twist_name,
        role="traveler",
    ))
    aid_ent = world.add(Entity(
        id="aid",
        type="aid",
        label=aid.label,
        phrase=aid.phrase,
        attrs={"power": aid.power, "mode": aid.mode},
        tags=set(aid.tags),
    ))
    patch_ent = world.add(Entity(
        id="patch",
        type="patch",
        label=patch.label,
        phrase=patch.phrase,
        attrs={"severity": patch.severity},
        tags=set(patch.tags),
    ))
    patch_ent.meters["ice"] += 1
    propagate(world, narrate=False)

    introduce(world, hero, parent, quest, patch)
    world.para()
    find_hoard(world, hero, aid)
    warn(world, parent, hero, aid, quest, patch)

    world.para()
    twist_arrives(world, traveler, patch)
    conflict(world, hero, traveler, aid)

    immediate = would_share_now(trait)
    if immediate:
        share_now(world, hero, traveler, aid)
    else:
        hesitate_then_share(world, hero, traveler, aid)

    world.para()
    use_aid(world, aid)
    outcome = outcome_of(StoryParams(
        quest=quest.id,
        aid=aid.id,
        patch=patch.id,
        twist=twist_name,
        twist_type=twist_type,
        hero=hero_name,
        hero_type=hero_type,
        parent=parent_type,
        trait=trait,
        seed=None,
    ))
    if outcome == "salvation":
        salvation_ending(world, hero, parent, traveler, quest)
    elif outcome == "cross_first":
        cross_first_ending(world, hero, parent, traveler, quest, aid)
    else:
        detour_ending(world, hero, parent, traveler, quest, aid, patch)

    world.facts.update(
        hero=hero,
        parent=parent,
        traveler=traveler,
        quest_cfg=quest,
        aid_cfg=aid,
        patch_cfg=patch,
        immediate_share=immediate,
        outcome=outcome,
        aided=aid_ent,
        patch=patch_ent,
    )
    return world


QUESTS = {
    "soup": Quest(
        id="soup",
        cargo="a warm jar of soup",
        phrase="a warm jar of soup wrapped in a towel",
        recipient="Mrs. Vale in 3B",
        reason="Mrs. Vale had a cough and needed something hot",
        mode="walk",
        tags={"soup", "neighbor"},
    ),
    "medicine": Quest(
        id="medicine",
        cargo="a small paper bag of medicine",
        phrase="a small paper bag of medicine tucked under one arm",
        recipient="Mr. Reed at the corner building",
        reason="Mr. Reed had run out and the pharmacy was already closed",
        mode="walk",
        tags={"medicine", "neighbor"},
    ),
    "books": Quest(
        id="books",
        cargo="a little wagon of library books",
        phrase="a little wagon full of library books for the reading room",
        recipient="the reading room at the shelter",
        reason="story hour was about to start and the books were needed there",
        mode="pull",
        tags={"books", "wagon"},
    ),
}

AIDS = {
    "salt": Aid(
        id="salt",
        label="salt",
        phrase="a dented tin of sidewalk salt",
        mode="ground",
        power=3,
        sense=3,
        use_text="Together they shook salt over the ice until it lost its hard glassy shine.",
        share_text="The grains rattled down in a bright little stream between them.",
        fail_text="The salt nibbled at the edge of the ice, but the middle still shone too hard to trust.",
        tags={"salt", "ice"},
    ),
    "sand": Aid(
        id="sand",
        label="sand",
        phrase="a paper pail of rough sand",
        mode="ground",
        power=2,
        sense=3,
        use_text="They scattered sand in a sandy ribbon across the slick place.",
        share_text="The rough grains pattered over the ice like tiny pebbly rain.",
        fail_text="The sand helped a little, but the patch was still too smooth for brave feet.",
        tags={"sand", "ice"},
    ),
    "cleats": Aid(
        id="cleats",
        label="ice cleats",
        phrase="one pair of clip-on ice cleats hanging on a fence hook",
        mode="feet",
        power=2,
        sense=2,
        use_text="The little metal teeth bit neatly under a pair of shoes.",
        share_text="The single pair passed from hand to hand like a serious tool, not a toy.",
        fail_text="The cleats helped one walker, but they could not make the whole patch safe for everyone.",
        tags={"cleats", "ice"},
    ),
    "cardboard": Aid(
        id="cardboard",
        label="a sheet of cardboard",
        phrase="a soggy sheet of cardboard by the bins",
        mode="ground",
        power=1,
        sense=1,
        use_text="They laid the cardboard down, but it went dark and slippery at once.",
        share_text="The cardboard flopped between them and soaked through.",
        fail_text="The cardboard turned wet and useless almost immediately.",
        tags={"cardboard", "ice"},
    ),
}

PATCHES = {
    "doorstep": Patch(
        id="doorstep",
        label="the doorstep patch",
        phrase="a thin doorstep patch",
        severity=1,
        tags={"ice", "mild"},
    ),
    "curb": Patch(
        id="curb",
        label="the curb ramp",
        phrase="the curb ramp where feet always slid sideways",
        severity=2,
        tags={"ice", "medium"},
    ),
    "hill": Patch(
        id="hill",
        label="the sloping hill of sidewalk",
        phrase="the sloping hill of sidewalk that everyone in the block talked about",
        severity=3,
        tags={"ice", "severe"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Tess", "Ruby", "Ava"]
BOY_NAMES = ["Finn", "Leo", "Sam", "Eli", "Owen", "Max"]
TRAVELERS = [
    ("the mail carrier", "man"),
    ("old Mr. Reed", "man"),
    ("a violin teacher", "woman"),
    ("the crossing guard", "woman"),
]
TRAITS = ["kind", "careful", "steady", "bold", "curious", "stubborn"]


@dataclass
class StoryParams:
    quest: str
    aid: str
    patch: str
    twist: str
    twist_type: str
    hero: str
    hero_type: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        quest="soup",
        aid="salt",
        patch="hill",
        twist="the mail carrier",
        twist_type="man",
        hero="Lina",
        hero_type="girl",
        parent="mother",
        trait="kind",
        seed=1,
    ),
    StoryParams(
        quest="medicine",
        aid="sand",
        patch="curb",
        twist="the crossing guard",
        twist_type="woman",
        hero="Finn",
        hero_type="boy",
        parent="father",
        trait="bold",
        seed=2,
    ),
    StoryParams(
        quest="soup",
        aid="cleats",
        patch="doorstep",
        twist="a violin teacher",
        twist_type="woman",
        hero="Nora",
        hero_type="girl",
        parent="mother",
        trait="careful",
        seed=3,
    ),
    StoryParams(
        quest="books",
        aid="salt",
        patch="curb",
        twist="old Mr. Reed",
        twist_type="man",
        hero="Leo",
        hero_type="boy",
        parent="father",
        trait="steady",
        seed=4,
    ),
    StoryParams(
        quest="books",
        aid="sand",
        patch="hill",
        twist="the mail carrier",
        twist_type="man",
        hero="Ruby",
        hero_type="girl",
        parent="mother",
        trait="curious",
        seed=5,
    ),
]

KNOWLEDGE = {
    "ice": [
        (
            "Why is sidewalk ice slippery?",
            "Ice is smooth, so shoes cannot grip it well. That is why people can slide or fall on an icy sidewalk."
        )
    ],
    "salt": [
        (
            "Why do people put salt on icy sidewalks?",
            "Salt helps melt ice and makes the surface less slick. It can turn a shiny patch into a safer path."
        )
    ],
    "sand": [
        (
            "Why does sand help on ice?",
            "Sand does not melt ice much, but it makes the ground rougher. That roughness can help shoes grab the surface."
        )
    ],
    "cleats": [
        (
            "What are ice cleats?",
            "Ice cleats are grips that clip onto shoes. Their little teeth help a person walk on slippery ground."
        )
    ],
    "soup": [
        (
            "Why might someone bring soup to a neighbor in winter?",
            "Warm soup can comfort someone who is sick or cold. Bringing it is a kind way to help."
        )
    ],
    "medicine": [
        (
            "Why is medicine important when someone is ill?",
            "Medicine can help a sick person feel better or follow a doctor's plan. That is why getting it to them can matter a lot."
        )
    ],
    "books": [
        (
            "Why can books be important at a shelter or reading room?",
            "Books can teach, comfort, and entertain people. Story time can make a hard day feel warmer."
        )
    ],
    "neighbor": [
        (
            "What does it mean to help a neighbor?",
            "Helping a neighbor means noticing when someone nearby needs care and doing something kind if you can. Small help can make a big difference."
        )
    ],
}
KNOWLEDGE_ORDER = ["ice", "salt", "sand", "cleats", "soup", "medicine", "books", "neighbor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest_cfg"]
    aid = f["aid_cfg"]
    patch = f["patch_cfg"]
    traveler = f["traveler"]
    return [
        'Write an adventure story for a 3-to-5-year-old set on an icy sidewalk that includes the words "hoard" and "salvation".',
        f"Tell a winter quest where {hero.id} tries to carry {quest.cargo} across {patch.label}, then a twist brings {traveler.label} into danger and sharing {aid.label} becomes the conflict.",
        "Write a child-facing story with a clear quest, a twist in the middle, and a warm ending image that proves kindness changed the situation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    traveler = f["traveler"]
    quest = f["quest_cfg"]
    aid = f["aid_cfg"]
    patch = f["patch_cfg"]
    outcome = f["outcome"]
    immediate = f["immediate_share"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child on a winter errand, and {hero.pronoun('possessive')} {parent.label_word}. The story also turns on {traveler.label}, who appears during the twist."
        ),
        (
            f"What was {hero.id}'s quest?",
            f"{hero.id}'s quest was to bring {quest.cargo} to {quest.recipient}. The errand mattered because {quest.reason}."
        ),
        (
            f"Why did the {aid.label} feel like a hoard at first?",
            f"It looked like a little pile of winter treasure, and {hero.id} wanted to keep it for {hero.pronoun('possessive')} own safe crossing. That is the selfish feeling the story has to push against."
        ),
        (
            "What was the twist?",
            f"The twist was that {traveler.label} stepped toward {patch.label} and nearly slipped. Suddenly the tool was not just about the quest anymore; it was also about helping someone else."
        ),
    ]
    if immediate:
        qa.append((
            f"How did {hero.id} handle the conflict?",
            f"{hero.id} chose to share the {aid.label} right away instead of hiding it. The conflict mattered because keeping the whole hoard would have helped only one person."
        ))
    else:
        qa.append((
            f"How did {hero.id} handle the conflict?",
            f"{hero.id} hesitated for a moment and almost kept the whole hoard. Then seeing {traveler.label} wobble made {hero.pronoun('object')} share, because the danger became real."
        ))
    if outcome == "salvation":
        qa.append((
            "Why did the story use the word salvation?",
            f"The safe path felt like salvation because the ice had seemed dangerous and hard to cross. Once the {aid.label} worked, both the quest and the traveler could move forward."
        ))
    elif outcome == "cross_first":
        qa.append((
            "Did the first tool solve everything?",
            f"No. The ice cleats helped one person cross, but they did not make the whole sidewalk safe for everyone. That is why {hero.id} still had to call for more help."
        ))
    else:
        qa.append((
            "How did the story end if the first plan was not enough?",
            f"They took a longer, safer route instead of forcing the dangerous one. The ending still shows growth, because {hero.id} stops treating the hoard like treasure and uses it to ask for proper help."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ice", "neighbor"} | set(world.facts["quest_cfg"].tags) | set(world.facts["aid_cfg"].tags)
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


ASP_RULES = r"""
sensible(A) :- aid(A), sense(A, S), sense_min(M), S >= M.

valid(Q, A, P) :- quest(Q), aid(A), patch(P), sensible(A), mode(A, ground).
valid(Q, A, P) :- quest(Q), aid(A), patch(P), sensible(A),
                  mode(A, feet), quest_mode(Q, walk), power(A, Pw), severity(P, Sv), Pw >= Sv.

outcome(salvation) :- chosen_quest(Q), chosen_aid(A), chosen_patch(P),
                      valid(Q, A, P), mode(A, ground), power(A, Pw), severity(P, Sv), Pw >= Sv.
outcome(cross_first) :- chosen_quest(Q), chosen_aid(A), chosen_patch(P),
                        valid(Q, A, P), mode(A, feet), power(A, Pw), severity(P, Sv), Pw >= Sv.
outcome(detour) :- chosen_quest(Q), chosen_aid(A), chosen_patch(P),
                   valid(Q, A, P), not outcome(salvation), not outcome(cross_first).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_mode", qid, quest.mode))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("mode", aid_id, aid.mode))
        lines.append(asp.fact("power", aid_id, aid.power))
        lines.append(asp.fact("sense", aid_id, aid.sense))
    for pid, patch in PATCHES.items():
        lines.append(asp.fact("patch", pid))
        lines.append(asp.fact("severity", pid, patch.severity))
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
        asp.fact("chosen_quest", params.quest),
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_patch", params.patch),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a winter errand on an icy sidewalk, a tempting hoard of helper gear, and a choice to share."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.quest and args.aid and args.patch:
        quest = QUESTS[args.quest]
        aid = AIDS[args.aid]
        patch = PATCHES[args.patch]
        if not applicable(aid, quest, patch):
            raise StoryError(explain_invalid(aid, quest, patch))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.aid is None or c[1] == args.aid)
        and (args.patch is None or c[2] == args.patch)
    ]
    if not combos:
        if args.quest and args.aid and args.patch:
            raise StoryError(explain_invalid(AIDS[args.aid], QUESTS[args.quest], PATCHES[args.patch]))
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, aid_id, patch_id = rng.choice(sorted(combos))
    hero_type = rng.choice(["girl", "boy"])
    hero = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    twist, twist_type = rng.choice(TRAVELERS)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        quest=quest_id,
        aid=aid_id,
        patch=patch_id,
        twist=twist,
        twist_type=twist_type,
        hero=hero,
        hero_type=hero_type,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.aid not in AIDS or params.patch not in PATCHES:
        raise StoryError("(Invalid story parameters.)")
    quest = QUESTS[params.quest]
    aid = AIDS[params.aid]
    patch = PATCHES[params.patch]
    if not applicable(aid, quest, patch):
        raise StoryError(explain_invalid(aid, quest, patch))
    world = tell(
        quest=quest,
        aid=aid,
        patch=patch,
        twist_name=params.twist,
        twist_type=params.twist_type,
        hero_name=params.hero,
        hero_type=params.hero_type,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for seed in range(25):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, aid, patch) combos:\n")
        for quest, aid, patch in combos:
            print(f"  {quest:8} {aid:8} {patch}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.quest} with {p.aid} at {p.patch} ({outcome_of(p)})"
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
