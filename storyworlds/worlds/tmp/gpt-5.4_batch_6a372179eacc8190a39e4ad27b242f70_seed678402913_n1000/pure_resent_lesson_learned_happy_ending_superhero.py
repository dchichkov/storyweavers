#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py
===============================================================================

A standalone story world for a tiny superhero-story domain: two children play
heroes, one child begins to resent the other's special role, that selfish feeling
causes a small setback, and the child learns that a pure hero helps instead of
hoarding glory. The ending is always warm and happy, but only if the chosen
mission and gear make common sense.

Run it
------
    python storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py
    python storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py --mission kite_tree --gear grabber
    python storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py --mission roof_streamer --gear step_stool
    python storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py --gear whistle
    python storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py --all
    python storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py --qa
    python storyworlds/worlds/gpt-5.4/pure_resent_lesson_learned_happy_ending_superhero.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    hero_base: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    object_label: str
    object_phrase: str
    stuck_place: str
    need: str
    problem_line: str
    success_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    use_line: str
    reaches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RankItem:
    id: str
    label: str
    phrase: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_blocked_mission(world: World) -> list[str]:
    gear = world.get("gear")
    if gear.meters["hidden"] < THRESHOLD:
        return []
    sig = ("blocked", gear.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mission_item = world.get("mission_item")
    mission_item.meters["stuck"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_repair(world: World) -> list[str]:
    gear = world.get("gear")
    if gear.meters["shared"] < THRESHOLD:
        return []
    sig = ("repair", gear.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gear.meters["hidden"] = 0.0
    mission_item = world.get("mission_item")
    mission_item.meters["rescued"] += 1
    mission_item.meters["stuck"] = 0.0
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
        kid.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="blocked_mission", tag="physical", apply=_r_blocked_mission),
    Rule(name="repair", tag="social", apply=_r_repair),
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
        for s in produced:
            world.say(s)
    return produced


def mission_works(place: Place, mission: Mission, gear: Gear) -> bool:
    return mission.id in place.affords and mission.need == gear.id and mission.id in gear.reaches


def sensible_fixes() -> list[Fix]:
    return [fx for fx in FIXES.values() if fx.sense >= SENSE_MIN]


def predict_setback(world: World) -> dict:
    sim = world.copy()
    gear = sim.get("gear")
    gear.meters["hidden"] += 1
    propagate(sim, narrate=False)
    item = sim.get("mission_item")
    return {
        "blocked": item.meters["stuck"] >= THRESHOLD,
        "worry": sum(k.memes["worry"] for k in sim.kids()),
    }


def introduce(world: World, lead: Entity, partner: Entity, place: Place, rank: RankItem) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
    world.say(
        f"After school, {lead.id} and {partner.id} turned {place.label} into {place.scene}. "
        f"{place.hero_base}."
    )
    world.say(
        f"Today the captain's prize was {rank.phrase}. It shone so brightly that it looked almost magical."
    )
    world.say(
        f'"Super team, ready!" {lead.id} shouted, while {partner.id} spun in a circle and pretended the wind itself was cheering.'
    )


def mission_arrives(world: World, mission: Mission) -> None:
    item = world.get("mission_item")
    item.meters["stuck"] += 1
    world.say(mission.problem_line)


def assign_rank(world: World, lead: Entity, partner: Entity, rank: RankItem) -> None:
    world.say(
        f"The grown-up running the game gently draped {rank.phrase} over {lead.id}'s shoulders. "
        f"{lead.id} stood a little taller."
    )
    partner.memes["envy"] += 1
    partner.memes["resentment"] += 1
    world.say(
        f"For one small minute, {partner.id} began to resent the way {rank.label} flashed on {lead.id}. "
        f"It was not a loud feeling, but it was there."
    )


def tempt_selfishness(world: World, partner: Entity, gear: Gear, mission: Mission, adult: Entity) -> None:
    pred = predict_setback(world)
    world.facts["predicted_blocked"] = pred["blocked"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{partner.id} looked at {gear.phrase}, then at {adult.label_word}, and said very softly, '
        f'"Why does {lead_name(world)} get the shining part?"'
    )
    world.say(
        f'{adult.label_word.capitalize()} heard the hurt in that question and answered, '
        f'"Because this mission needs both brave hands, not one bigger spotlight."'
    )
    if pred["blocked"]:
        world.say(
            f"{partner.id} knew that if {partner.pronoun()} hid the {gear.label}, the team would not be able to reach the {mission.object_label}."
        )


def hide_gear(world: World, partner: Entity, gear: Gear) -> None:
    gear.meters["hidden"] += 1
    partner.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the hot feeling won for a moment. {partner.id} slipped the {gear.label} behind a bench and folded "
        f"{partner.pronoun('possessive')} arms."
    )
    world.say(
        f'"If I do not get the shiny turn, maybe nobody does," {partner.pronoun()} muttered.'
    )


def failed_attempt(world: World, lead: Entity, mission: Mission, gear: Gear) -> None:
    lead.memes["disappointment"] += 1
    world.say(
        f"{lead.id} hurried to the rescue point, reached for the {gear.label}, and found empty air."
    )
    world.say(
        f'"Oh no," {lead.pronoun()} said. "Without it, we cannot help the {mission.object_label}."'
    )


def lesson(world: World, adult: Entity, lead: Entity, partner: Entity, rank: RankItem) -> None:
    partner.memes["shame"] += 1
    partner.memes["resentment"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} knelt beside both children so no one had to look up."
    )
    world.say(
        f'"A real hero keeps a pure heart," {adult.pronoun()} said. '
        f'"The cape and the badge are only cloth and tin. When you resent a friend, the mission gets smaller. '
        f"When you help, everybody grows bigger."'
    )
    world.say(
        f"{partner.id} looked down at {partner.pronoun('possessive')} shoes. The mean feeling suddenly felt much smaller than the job."
    )


def repair(world: World, partner: Entity, gear: Gear, fix: Fix, mission: Mission) -> None:
    gear.meters["shared"] += 1
    partner.memes["care"] += 1
    partner.memes["shame"] = 0.0
    propagate(world, narrate=False)
    world.say(fix.text.format(name=partner.id, gear=gear.label))
    world.say(
        f"Together the two heroes used the {gear.label}. {gear.use_line}."
    )
    world.say(mission.success_line)


def happy_end(world: World, adult: Entity, lead: Entity, partner: Entity, rank: RankItem, mission: Mission) -> None:
    lead.memes["love"] += 1
    partner.memes["love"] += 1
    partner.memes["lesson"] += 1
    lead.memes["lesson"] += 1
    world.say(
        f"Then {lead.id} did something that made the whole game brighter. {lead.pronoun().capitalize()} took off {rank.phrase} and placed it between them."
    )
    world.say(
        f'"Next mission, we share the shining part," {lead.pronoun()} said.'
    )
    world.say(
        f"{partner.id}'s eyes warmed at once. {partner.pronoun().capitalize()} did not need to win alone anymore."
    )
    world.say(
        f"{mission.ending_image} Even the wind seemed to clap for the team."
    )


def tell(
    place: Place,
    mission: Mission,
    gear_cfg: Gear,
    rank: RankItem,
    fix: Fix,
    lead_name_value: str = "Nova",
    lead_gender: str = "girl",
    partner_name_value: str = "Kai",
    partner_gender: str = "boy",
    adult_type: str = "mother",
) -> World:
    world = World(place)
    lead = world.add(Entity(id=lead_name_value, kind="character", type=lead_gender, role="lead"))
    partner = world.add(Entity(id=partner_name_value, kind="character", type=partner_gender, role="partner"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    mission_item = world.add(
        Entity(
            id="mission_item",
            type="thing",
            label=mission.object_label,
            phrase=mission.object_phrase,
            portable=True,
            tags=set(mission.tags),
        )
    )
    gear = world.add(
        Entity(
            id="gear",
            type="gear",
            label=gear_cfg.label,
            phrase=gear_cfg.phrase,
            portable=True,
            tags=set(gear_cfg.tags),
        )
    )

    introduce(world, lead, partner, place, rank)
    mission_arrives(world, mission)

    world.para()
    assign_rank(world, lead, partner, rank)
    tempt_selfishness(world, partner, gear_cfg, mission, adult)
    hide_gear(world, partner, gear)
    failed_attempt(world, lead, mission, gear_cfg)

    world.para()
    lesson(world, adult, lead, partner, rank)
    repair(world, partner, gear, fix, mission)

    world.para()
    happy_end(world, adult, lead, partner, rank, mission)

    world.facts.update(
        place=place,
        mission=mission,
        gear_cfg=gear_cfg,
        rank=rank,
        fix=fix,
        lead=lead,
        partner=partner,
        adult=adult,
        mission_item=mission_item,
        gear=gear,
        rescued=mission_item.meters["rescued"] >= THRESHOLD,
        learned=partner.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "park": Place(
        id="park",
        label="the park",
        scene="a bright superhero city",
        hero_base="The slide was a launch tower, the sandbox was a secret lab, and the benches became rooftops",
        affords={"kite_tree", "roof_streamer"},
    ),
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        scene="a little rescue city",
        hero_base="The painted hopscotch squares became landing pads, and the fence became a city wall",
        affords={"kite_tree", "shed_flag"},
    ),
    "backyard": Place(
        id="backyard",
        label="the backyard",
        scene="a training city for brave helpers",
        hero_base="A cardboard box became command center, and the picnic table became the tallest tower in town",
        affords={"shed_flag", "roof_streamer"},
    ),
}

MISSIONS = {
    "kite_tree": Mission(
        id="kite_tree",
        object_label="kite",
        object_phrase="a red kite",
        stuck_place="high in the tree",
        need="grabber",
        problem_line="A gust of wind tossed a red kite high into the tree, where it fluttered and snapped like a tiny trapped flag.",
        success_line="The hook caught the kite string, and down it came in one proud, swooping slide.",
        ending_image="Soon the kite was sailing again above their heads, making a red streak in the gold afternoon light",
        tags={"kite", "teamwork"},
    ),
    "roof_streamer": Mission(
        id="roof_streamer",
        object_label="streamer",
        object_phrase="a long blue streamer",
        stuck_place="on the low roof edge",
        need="grabber",
        problem_line="A long blue streamer had blown onto the low roof edge above the playhouse, where it twitched like a signal waiting for heroes.",
        success_line="The grabber pinched the loose end, and the streamer floated down as gently as a ribbon in a dance.",
        ending_image="Soon the blue streamer was tied safely to the gate, fluttering like a thank-you banner for the heroes below",
        tags={"streamer", "teamwork"},
    ),
    "shed_flag": Mission(
        id="shed_flag",
        object_label="paper flag",
        object_phrase="a paper flag with a star on it",
        stuck_place="on top of the garden shed",
        need="step_stool",
        problem_line="A paper flag with a painted star had blown onto the top of the little shed, too high for small hands to reach from the ground.",
        success_line="With the step stool steady and the team careful, the flag was lifted down without a single crumple.",
        ending_image="Soon the star flag was flying from their fort again, bright and straight against the evening sky",
        tags={"flag", "teamwork"},
    ),
}

GEAR = {
    "grabber": Gear(
        id="grabber",
        label="reacher-grabber",
        phrase="the reacher-grabber",
        use_line="Lead held the pole steady while partner guided the hook with patient fingers".replace("Lead", "One hero").replace("partner", "the other"),
        reaches={"kite_tree", "roof_streamer"},
        tags={"grabber", "helping"},
    ),
    "step_stool": Gear(
        id="step_stool",
        label="step stool",
        phrase="the little step stool",
        use_line="One hero stood safely on the stool while the other braced it with both hands",
        reaches={"shed_flag"},
        tags={"stool", "helping"},
    ),
    "whistle": Gear(
        id="whistle",
        label="captain whistle",
        phrase="the captain whistle",
        use_line="It made a loud peep but could not lift anything down",
        reaches=set(),
        tags={"whistle"},
    ),
}

RANK_ITEMS = {
    "cape": RankItem(
        id="cape",
        label="silver cape",
        phrase="the silver cape",
        shine="silver",
        tags={"cape", "hero"},
    ),
    "badge": RankItem(
        id="badge",
        label="star badge",
        phrase="the star badge",
        shine="gold",
        tags={"badge", "hero"},
    ),
}

FIXES = {
    "apologize_share": Fix(
        id="apologize_share",
        sense=3,
        text='{name} ran back to the bench, pulled out the {gear}, and said, "I am sorry. I let a sore feeling boss me around. Let us save it together."',
        qa_text="apologized, brought back the gear, and shared the rescue",
        tags={"apology", "teamwork"},
    ),
    "trade_turns": Fix(
        id="trade_turns",
        sense=2,
        text='{name} fetched the {gear} and said, "You can wear the shine first, and I can take the next hero turn. But right now we help together."',
        qa_text="returned the gear and agreed to trade turns kindly",
        tags={"sharing", "teamwork"},
    ),
    "keep_sulking": Fix(
        id="keep_sulking",
        sense=1,
        text='{name} kept the {gear} tucked away and waited for someone else to fix the trouble',
        qa_text="kept sulking instead of helping",
        tags={"sulking"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mia", "Zoe", "Ava", "Nora", "Ruby", "Ivy"]
BOY_NAMES = ["Kai", "Max", "Leo", "Eli", "Finn", "Noah", "Theo", "Ben"]
TRAITS = ["kind", "quick", "eager", "thoughtful", "sparky", "steady"]


@dataclass
class StoryParams:
    place: str
    mission: str
    gear: str
    rank_item: str
    fix: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="park",
        mission="kite_tree",
        gear="grabber",
        rank_item="cape",
        fix="apologize_share",
        lead_name="Nova",
        lead_gender="girl",
        partner_name="Kai",
        partner_gender="boy",
        adult="mother",
        trait="kind",
    ),
    StoryParams(
        place="schoolyard",
        mission="shed_flag",
        gear="step_stool",
        rank_item="badge",
        fix="trade_turns",
        lead_name="Leo",
        lead_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        adult="father",
        trait="steady",
    ),
    StoryParams(
        place="backyard",
        mission="roof_streamer",
        gear="grabber",
        rank_item="cape",
        fix="apologize_share",
        lead_name="Ruby",
        lead_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        adult="mother",
        trait="thoughtful",
    ),
]


KNOWLEDGE = {
    "hero": [
        (
            "What makes someone a real hero?",
            "A real hero helps when there is a problem and cares about other people. Being kind and brave matters more than looking special."
        )
    ],
    "resent": [
        (
            "What does resent mean?",
            "To resent someone means you feel sore or unhappy because they got something you wanted. That feeling can shrink when you talk honestly and choose kindness."
        )
    ],
    "pure": [
        (
            "What is a pure heart in a story like this?",
            "A pure heart means you are trying to be honest, kind, and helpful. It does not mean perfect; it means you choose the good thing once you understand."
        )
    ],
    "kite": [
        (
            "Why can a kite get stuck in a tree?",
            "Wind can blow a kite into branches, and the string can catch there. Then it needs careful hands to bring it down."
        )
    ],
    "grabber": [
        (
            "What is a reacher-grabber?",
            "A reacher-grabber is a long tool that helps you hook or pinch something from farther away. It can help you reach safely without climbing."
        )
    ],
    "stool": [
        (
            "Why should a step stool be used carefully?",
            "A step stool makes you a little taller, but it must stand flat and steady. A grown-up or helper should make sure it does not wobble."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful?",
            "Teamwork lets two people share jobs that are easier together than alone. One person can steady, guide, watch, or comfort while the other reaches."
        )
    ],
    "apology": [
        (
            "Why does saying sorry help?",
            "A real sorry tells the truth about what went wrong and opens the door to fixing it. It helps people trust each other again."
        )
    ],
}
KNOWLEDGE_ORDER = ["hero", "resent", "pure", "kite", "grabber", "stool", "teamwork", "apology"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mission_id, mission in MISSIONS.items():
            for gear_id, gear in GEAR.items():
                if mission_works(place, mission, gear):
                    combos.append((place_id, mission_id, gear_id))
    return combos


def lead_name(world: World) -> str:
    lead = world.facts.get("lead")
    if isinstance(lead, Entity):
        return lead.id
    for ent in world.entities.values():
        if ent.role == "lead":
            return ent.id
    return "the leader"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    mission = f["mission"]
    gear = f["gear_cfg"]
    rank = f["rank"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that uses the words "pure" and "resent".',
        f"Tell a gentle hero story where {partner.id} begins to resent {lead.id}'s {rank.label}, hides {gear.phrase}, learns a lesson, and helps rescue the {mission.object_label}.",
        f"Write a happy ending story where two pretend superheroes solve a problem together after one child chooses kindness over jealousy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    adult = f["adult"]
    mission = f["mission"]
    gear = f["gear_cfg"]
    rank = f["rank"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children playing superheroes, {lead.id} and {partner.id}, and the {adult.label_word} guiding them. Their game feels real because they care about the mission and about each other."
        ),
        (
            "What problem needed to be solved?",
            f"The {mission.object_label} was stuck {mission.stuck_place}, so the children wanted to rescue it. They needed the {gear.label} because small hands alone could not reach safely."
        ),
        (
            f"Why did {partner.id} hide the {gear.label}?",
            f"{partner.id} began to resent {lead.id} for getting the {rank.label}. That sore feeling made {partner.pronoun('object')} want to stop the rescue instead of helping."
        ),
        (
            "What lesson did the grown-up teach?",
            f'The {adult.label_word} said that a real hero keeps a pure heart and helps the team. The lesson was that shiny things matter less than kindness and teamwork.'
        ),
        (
            f"How did {partner.id} fix the problem?",
            f"{partner.id} {fix.qa_text}. That changed the mission because the team could finally use the right tool together."
        ),
        (
            "How did the story end?",
            f"It ended happily: the {mission.object_label} was rescued, the children worked as a team, and the shining role was shared instead of fought over. The ending proves the friendship grew stronger than the jealous feeling."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"hero", "resent", "pure", "teamwork"}
    mission = world.facts["mission"]
    gear = world.facts["gear_cfg"]
    fix = world.facts["fix"]
    if "kite" in mission.tags:
        tags.add("kite")
    if gear.id == "grabber":
        tags.add("grabber")
    if gear.id == "step_stool":
        tags.add("stool")
    if "apology" in fix.tags:
        tags.add("apology")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, mission: Mission, gear: Gear) -> str:
    if mission.id not in place.affords:
        return (
            f"(No story: {place.label.capitalize()} does not fit the mission '{mission.id}'. "
            f"Pick a mission the place can honestly support.)"
        )
    if mission.need != gear.id or mission.id not in gear.reaches:
        return (
            f"(No story: a {gear.label} will not solve the '{mission.id}' mission. "
            f"This rescue needs {MISSIONS[mission.id].need.replace('_', ' ')} so the problem can change for a real reason.)"
        )
    return "(No story: that mission and gear do not make sense together.)"


def explain_fix(fid: str) -> str:
    fx = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fx.sense} < {SENSE_MIN}). A happy lesson story needs a real repair, such as: {better}.)"
    )


ASP_RULES = r"""
works(P, M, G) :- affords(P, M), needs(M, G), reaches(G, M).
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(P, M, G) :- place(P), mission(M), gear(G), works(P, M, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for mission_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, mission_id))
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("needs", mission_id, mission.need))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        for mission_id in sorted(gear.reaches):
            lines.append(asp.fact("reaches", gear_id, mission_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_fix"))


def asp_verify() -> int:
    rc = 0
    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_fixes = {f.id for f in sensible_fixes()}
    clingo_fixes = set(asp_sensible_fixes())
    if python_fixes == clingo_fixes:
        print(f"OK: sensible fixes match ({sorted(python_fixes)}).")
    else:
        rc = 1
        print("MISMATCH in sensible fixes:")
        print("  python:", sorted(python_fixes))
        print("  clingo:", sorted(clingo_fixes))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        print(f"SMOKE FAIL in resolve_params(): {err}")
        return 1

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            print(f"OK: smoke story {idx} generated ({len(sample.story.split())} words).")
        except Exception as err:
            print(f"SMOKE FAIL on case {idx}: {err}")
            return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero game, a resentful moment, a lesson, and a happy repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--rank-item", choices=RANK_ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mission/gear combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.gear:
        mission = MISSIONS[args.mission]
        gear = GEAR[args.gear]
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        if args.place and not mission_works(place, mission, gear):
            raise StoryError(explain_rejection(place, mission, gear))
        if not args.place:
            possible = [p for p in PLACES.values() if mission_works(p, mission, gear)]
            if not possible:
                raise StoryError(explain_rejection(next(iter(PLACES.values())), mission, gear))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mission is None or combo[1] == args.mission)
        and (args.gear is None or combo[2] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mission_id, gear_id = rng.choice(sorted(combos))
    rank_item = args.rank_item or rng.choice(sorted(RANK_ITEMS))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    lead_name_value, lead_gender = _pick_child(rng)
    partner_name_value, partner_gender = _pick_child(rng, avoid=lead_name_value)
    adult_type = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        mission=mission_id,
        gear=gear_id,
        rank_item=rank_item,
        fix=fix_id,
        lead_name=lead_name_value,
        lead_gender=lead_gender,
        partner_name=partner_name_value,
        partner_gender=partner_gender,
        adult=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.gear not in GEAR:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.rank_item not in RANK_ITEMS:
        raise StoryError(f"(Unknown rank item: {params.rank_item})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    place = PLACES[params.place]
    mission = MISSIONS[params.mission]
    gear = GEAR[params.gear]
    fix = FIXES[params.fix]
    if not mission_works(place, mission, gear):
        raise StoryError(explain_rejection(place, mission, gear))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        place=place,
        mission=mission,
        gear_cfg=gear,
        rank=RANK_ITEMS[params.rank_item],
        fix=fix,
        lead_name_value=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name_value=params.partner_name,
        partner_gender=params.partner_gender,
        adult_type=params.adult,
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
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mission, gear) combos:\n")
        for place_id, mission_id, gear_id in combos:
            print(f"  {place_id:10} {mission_id:14} {gear_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lead_name} & {p.partner_name}: {p.mission} at {p.place} ({p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
