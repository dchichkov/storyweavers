#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yarmulke_conflict_reconciliation_superhero_story.py
=============================================================================

A standalone storyworld about two children playing superheroes when a conflict
forms around one child's yarmulke, and the story only proceeds when the repair
is respectful enough to heal the hurt. The domain is intentionally small and
constraint-checked: fewer plausible stories are better than many weak ones.

Run it
------
    python storyworlds/worlds/gpt-5.4/yarmulke_conflict_reconciliation_superhero_story.py
    python storyworlds/worlds/gpt-5.4/yarmulke_conflict_reconciliation_superhero_story.py --conflict grabbing
    python storyworlds/worlds/gpt-5.4/yarmulke_conflict_reconciliation_superhero_story.py --repair shrug
    python storyworlds/worlds/gpt-5.4/yarmulke_conflict_reconciliation_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/yarmulke_conflict_reconciliation_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/yarmulke_conflict_reconciliation_superhero_story.py --verify
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
SENSE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    call: str
    trouble: str
    target_label: str
    success: str
    needs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    severity: int
    line: str
    action: str
    consequence: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    power: int
    line: str
    action: str
    promise: str
    heals: set[str] = field(default_factory=set)
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


def _r_hurt_breaks_team(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    target = world.get("target")
    out: list[str] = []
    if hero.memes["hurt"] >= THRESHOLD and target.meters["stuck"] >= THRESHOLD:
        sig = ("team_pause",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["worry"] += 1
            world.get("team").meters["paused"] += 1
            out.append("__pause__")
    return out


def _r_repair_restores_trust(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["heard_apology"] >= THRESHOLD and friend.memes["respect"] >= THRESHOLD:
        sig = ("trust_back",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] += 1
            hero.memes["relief"] += 1
            friend.memes["relief"] += 1
            out = []
            if world.get("team").meters["paused"] >= THRESHOLD:
                world.get("team").meters["paused"] = 0.0
                world.get("team").meters["ready"] += 1
            else:
                world.get("team").meters["ready"] += 1
            return out
    return []


CAUSAL_RULES = [
    Rule(name="hurt_breaks_team", tag="social", apply=_r_hurt_breaks_team),
    Rule(name="repair_restores_trust", tag="social", apply=_r_repair_restores_trust),
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
            if not s.startswith("__"):
                world.say(s)
    return produced


PLACES = {
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        scene="The blacktop shone in the sun, and the jungle gym looked tall enough for heroes.",
        affords={"kite", "kitten", "ball"},
    ),
    "park": Place(
        id="park",
        label="the park",
        scene="The slide, the bench, and the low trees made the park feel like a whole hero city.",
        affords={"kite", "kitten", "ball"},
    ),
    "community_hall": Place(
        id="community_hall",
        label="the community hall",
        scene="Folded chairs made canyons, and the little stage looked like a tower in danger.",
        affords={"ball", "cape"},
    ),
}

MISSIONS = {
    "kite": Mission(
        id="kite",
        call="a red kite was stuck in a tree branch",
        trouble="The string fluttered high above their heads, too far for one child to reach alone.",
        target_label="kite",
        success="Together they shook the branch with a jump rope pole until the kite swooped down into waiting hands.",
        needs="one child to steady, one child to reach",
        tags={"kite", "teamwork"},
    ),
    "kitten": Mission(
        id="kitten",
        call="a tiny toy kitten had tipped into the tall tube of the slide",
        trouble="The toy was wedged in the dark bend where an arm alone could not quite get it.",
        target_label="toy kitten",
        success="One child held the flashlight and one child reached in with a grabber, and the toy kitten popped free.",
        needs="one child to light the way, one child to reach carefully",
        tags={"kitten", "teamwork", "flashlight"},
    ),
    "ball": Mission(
        id="ball",
        call="a bright ball had rolled under the stage steps",
        trouble="It sat behind the first beam where it was easy to see and hard to pull out.",
        target_label="ball",
        success="One child lay flat to guide the ruler while the other nudged the ball until it rolled back into the light.",
        needs="one child to guide, one child to push it loose",
        tags={"ball", "teamwork"},
    ),
    "cape": Mission(
        id="cape",
        call="their paper hero cape had blown onto the high curtain rod",
        trouble="The cape hung there like a flag, fluttering where small hands could not reach.",
        target_label="cape",
        success="They worked together with a cardboard tube and a careful chair spotter until the cape drifted down like a banner.",
        needs="one child to hold steady, one child to lift the tube",
        tags={"cape", "teamwork"},
    ),
}

CONFLICTS = {
    "costume_rule": Conflict(
        id="costume_rule",
        severity=2,
        line='"Real heroes wear matching helmets," the friend blurted. "Maybe you should hide your yarmulke for this mission."',
        action="The words landed with a thud, because they treated the yarmulke like something that did not belong in the game.",
        consequence="The hero stepped back instead of running toward the rescue.",
        needs={"respect", "inclusion"},
        tags={"respect", "inclusion", "yarmulke"},
    ),
    "teasing_name": Conflict(
        id="teasing_name",
        severity=1,
        line='"Your yarmulke looks like a tiny hero button," the friend said with a silly laugh.',
        action="The joke was meant to be funny, but it made the yarmulke feel like a costume piece instead of something important.",
        consequence="The hero's smile folded up, and the game stopped feeling bright.",
        needs={"respect", "apology"},
        tags={"respect", "apology", "yarmulke"},
    ),
    "grabbing": Conflict(
        id="grabbing",
        severity=3,
        line='The friend reached toward the yarmulke and said, "We can use it like our team badge!"',
        action="A hand should never grab at something worn with care, and the hero jerked back at once.",
        consequence="Now the rescue stopped completely, because hurt and surprise had knocked the team apart.",
        needs={"respect", "apology", "space"},
        tags={"respect", "apology", "space", "yarmulke"},
    ),
}

REPAIRS = {
    "listen_and_apologize": Repair(
        id="listen_and_apologize",
        sense=2,
        power=2,
        line='"I am sorry," the friend said. "I spoke without thinking. Your yarmulke matters, and I want to understand."',
        action="The friend went quiet long enough to listen instead of rushing the game.",
        promise="Then the friend said the yarmulke could stay exactly where it was, because a real teammate does not ask someone to hide what matters to them.",
        heals={"respect", "apology"},
        tags={"apology", "respect"},
    ),
    "invite_and_adapt": Repair(
        id="invite_and_adapt",
        sense=2,
        power=2,
        line='"I am sorry," the friend said. "Can we make our hero team fit both of us?"',
        action="The friend changed the plan so the hero could keep the yarmulke and still have the starring role in the mission.",
        promise="They decided every hero on the team could look different and still belong.",
        heals={"respect", "inclusion", "apology"},
        tags={"apology", "respect", "inclusion"},
    ),
    "return_space_and_apologize": Repair(
        id="return_space_and_apologize",
        sense=3,
        power=3,
        line='"I am really sorry," the friend said, stepping back with both hands at the sides. "I should not have reached for your yarmulke."',
        action="The friend gave space, named the mistake clearly, and waited for an answer.",
        promise="When the hero nodded, the friend asked before coming close again and said the yarmulke was part of the hero, not a prop for anybody else.",
        heals={"respect", "apology", "space", "inclusion"},
        tags={"apology", "respect", "space", "inclusion"},
    ),
    "shrug": Repair(
        id="shrug",
        sense=0,
        power=0,
        line='"Come on," the friend said with a shrug. "It was just a joke."',
        action="The friend tried to hurry past the hurt instead of mending it.",
        promise="Nothing in the plan changed.",
        heals=set(),
        tags=set(),
    ),
}

GIRL_NAMES = ["Maya", "Rina", "Leah", "Ava", "Zoe", "Nora"]
BOY_NAMES = ["Avi", "Noam", "Eli", "Ben", "Sam", "Leo"]
TRAITS = ["quick", "kind", "brave", "careful", "sparky", "thoughtful"]


def mission_supported(place_id: str, mission_id: str) -> bool:
    return mission_id in PLACES[place_id].affords


def repair_works(conflict_id: str, repair_id: str) -> bool:
    conflict = CONFLICTS[conflict_id]
    repair = REPAIRS[repair_id]
    return repair.sense >= SENSE_MIN and repair.power >= conflict.severity and conflict.needs.issubset(repair.heals)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for mission_id in MISSIONS:
            if not mission_supported(place_id, mission_id):
                continue
            for conflict_id in CONFLICTS:
                for repair_id in REPAIRS:
                    if repair_works(conflict_id, repair_id):
                        combos.append((place_id, mission_id, conflict_id, repair_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mission: str
    conflict: str
    repair: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


def play_setup(world: World, hero: Entity, friend: Entity, mission: Mission) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} raced into {world.place.label} as if it were a city waiting for rescue. "
        f"{world.place.scene}"
    )
    world.say(
        f"{hero.id} wore a cape made from a towel and a blue yarmulke that sat neat and steady on {hero.pronoun('possessive')} head. "
        f"{friend.id} thumped a hand onto a cardboard chest badge and shouted, "
        f'"Super rescue team, ready!"'
    )
    world.say(
        f"Then they spotted trouble: {mission.call}."
    )
    world.say(mission.trouble)


def conflict_beat(world: World, hero: Entity, friend: Entity, conflict: Conflict) -> None:
    hero.memes["hurt"] += 1
    friend.memes["rushed"] += 1
    world.say(conflict.line)
    world.say(conflict.action)
    world.say(conflict.consequence)
    propagate(world, narrate=False)


def predict_repair(world: World, conflict: Conflict, repair: Repair) -> dict:
    sim = world.copy()
    sim_hero = sim.get("hero")
    sim_friend = sim.get("friend")
    if repair_works(conflict.id, repair.id):
        sim_hero.memes["heard_apology"] += 1
        sim_friend.memes["respect"] += 1
        propagate(sim, narrate=False)
    return {
        "trust": sim_hero.memes["trust"],
        "ready": sim.get("team").meters["ready"],
    }


def repair_beat(world: World, hero: Entity, friend: Entity, conflict: Conflict, repair: Repair) -> None:
    pred = predict_repair(world, conflict, repair)
    world.facts["predicted_trust"] = pred["trust"]
    friend.memes["respect"] += 1
    hero.memes["heard_apology"] += 1
    friend.memes["apologized"] += 1
    if "space" in repair.heals:
        hero.memes["safe"] += 1
    if "inclusion" in repair.heals:
        hero.memes["belonging"] += 1
    world.say(repair.line)
    world.say(repair.action)
    world.say(repair.promise)
    propagate(world, narrate=False)


def accept_repair(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"{hero.id} touched the edge of the yarmulke, took a breath, and nodded. "
        f'"Okay," {hero.pronoun()} said. "Let\'s be the kind of heroes who help and listen."'
    )
    world.say(
        f"{friend.id}'s shoulders dropped with relief, and the two of them stood side by side again."
    )


def rescue(world: World, hero: Entity, friend: Entity, mission: Mission) -> None:
    target = world.get("target")
    target.meters["stuck"] = 0.0
    target.meters["rescued"] += 1
    world.say(
        f"They hurried back to the mission, remembering that this rescue needed {mission.needs}."
    )
    world.say(mission.success)
    world.say(
        f"When it was done, {friend.id} grinned at {hero.id}. "
        f'"Captain {hero.id}," {friend.pronoun()} said, "good catch."'
    )
    world.say(
        f"The blue yarmulke did not have to be hidden or changed. It stayed right where it belonged while the team saved the day."
    )


def closing_image(world: World, hero: Entity, friend: Entity, mission: Mission) -> None:
    world.say(
        f"On the way home, they made up a new team rule: every hero gets to come as themself."
    )
    world.say(
        f"With the rescued {mission.target_label} between them, the two friends marched across {world.place.label} in their flapping capes, "
        f"and the yarmulke flashed blue in the sun like a brave little piece of sky."
    )


def tell(
    place: Place,
    mission: Mission,
    conflict: Conflict,
    repair: Repair,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
    trait: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the adult", role="adult"))
    team = world.add(Entity(id="team", type="team", label="team"))
    target = world.add(Entity(id="target", type=mission.target_label, label=mission.target_label))
    yarmulke = world.add(Entity(id="yarmulke", type="clothing", label="yarmulke"))

    hero.id = hero_name
    friend.id = friend_name
    world.entities[hero.id] = world.entities.pop("hero")
    world.entities[friend.id] = world.entities.pop("friend")
    hero = world.get(hero_name)
    friend = world.get(friend_name)

    hero.attrs["trait"] = trait
    hero.attrs["wears"] = "yarmulke"
    target.meters["stuck"] += 1
    yarmulke.meters["secure"] += 1
    world.get("team").meters["ready"] += 1

    play_setup(world, hero, friend, mission)

    world.para()
    conflict_beat(world, hero, friend, conflict)

    world.para()
    repair_beat(world, hero, friend, conflict, repair)
    accept_repair(world, hero, friend)

    world.para()
    rescue(world, hero, friend, mission)
    closing_image(world, hero, friend, mission)

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        target=target,
        yarmulke=yarmulke,
        place=place,
        mission=mission,
        conflict=conflict,
        repair=repair,
        healed=hero.memes["trust"] >= THRESHOLD,
        rescued=target.meters["rescued"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "yarmulke": [
        (
            "What is a yarmulke?",
            "A yarmulke is a small head covering that some Jewish people wear. It can be part of everyday life, prayer, or family tradition."
        )
    ],
    "respect": [
        (
            "What does respect mean?",
            "Respect means treating people and the things that matter to them with care. It also means listening when someone says something is important."
        )
    ],
    "apology": [
        (
            "What makes an apology real?",
            "A real apology names the mistake, shows care for the hurt, and changes what happens next. It is more than just trying to hurry past the problem."
        )
    ],
    "space": [
        (
            "Why is it important not to grab something a person is wearing?",
            "Things people wear belong on their body and should not be grabbed. You should ask first and give space, especially if the item is important to them."
        )
    ],
    "inclusion": [
        (
            "Can superheroes look different from one another?",
            "Yes. Heroes can wear different clothes, have different bodies, and still work as a team. Being different does not stop anyone from being brave."
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help on a rescue?",
            "Teamwork helps because one person can do part of the job while another does a different part. Working together can solve a problem that is too hard for one child alone."
        )
    ],
    "kite": [
        (
            "Why does a kite get stuck in a tree?",
            "A kite can get caught when wind blows it into branches. The string and the light paper make it easy for the tree to trap."
        )
    ],
    "kitten": [
        (
            "Why do people use a flashlight to look into dark places?",
            "A flashlight helps you see where your hands are going. That makes careful rescue work safer and easier."
        )
    ],
    "ball": [
        (
            "Why is it hard to reach a ball under something?",
            "A ball can roll to a place where your arm will not fit well. Then you may need a tool or another person to guide you."
        )
    ],
    "cape": [
        (
            "Why does a cape flap in the wind?",
            "A cape is light cloth or paper, so air can push it around easily. That is why it can lift and flutter."
        )
    ],
}
KNOWLEDGE_ORDER = ["yarmulke", "respect", "apology", "space", "inclusion", "teamwork", "kite", "kitten", "ball", "cape"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mission = f["mission"]
    conflict = f["conflict"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "yarmulke" and has both conflict and reconciliation.',
        f"Tell a gentle superhero story where {hero.id} and {friend.id} are in the middle of a rescue when a hurtful mistake about a yarmulke stops the team, and the children make things right before finishing the mission.",
        f"Write a child-facing story with a clear conflict, a sincere repair, and a happy ending image, using a superhero rescue involving a {mission.target_label} and a mistake like {conflict.id.replace('_', ' ')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mission = f["mission"]
    conflict = f["conflict"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children pretending to be superheroes together. {hero.id} is wearing a blue yarmulke during their rescue game."
        ),
        (
            "What problem did the children notice at the beginning?",
            f"They noticed that {mission.call}. The problem needed teamwork, because the rescue took more than one job at once."
        ),
        (
            f"What was the conflict between {hero.id} and {friend.id}?",
            f"The conflict began when {friend.id} made a hurtful mistake about {hero.id}'s yarmulke. {conflict.action} That is why the team stopped instead of rushing into the rescue."
        ),
        (
            f"How did {friend.id} fix the mistake?",
            f"{friend.id} gave a real repair instead of pretending nothing happened. {repair.action} Then {friend.pronoun()} made it clear that {hero.id}'s yarmulke belonged in the game exactly as it was."
        ),
        (
            "How did the children reconcile?",
            f"They reconciled when {friend.id} apologized and changed the plan, and {hero.id} chose to trust the team again. After that, they stood side by side and finished the rescue together."
        ),
        (
            "How do you know the ending changed from the middle?",
            f"In the middle, the team was paused because feelings were hurt. At the end, they were moving together again with the rescued {mission.target_label} between them, which shows the friendship had been repaired."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"yarmulke", "teamwork"} | set(f["conflict"].tags) | set(f["repair"].tags) | set(f["mission"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="park",
        mission="kite",
        conflict="costume_rule",
        repair="invite_and_adapt",
        hero_name="Avi",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        adult_type="mother",
        trait="brave",
        seed=101,
    ),
    StoryParams(
        place="schoolyard",
        mission="kitten",
        conflict="teasing_name",
        repair="listen_and_apologize",
        hero_name="Noam",
        hero_gender="boy",
        friend_name="Leah",
        friend_gender="girl",
        adult_type="teacher",
        trait="careful",
        seed=102,
    ),
    StoryParams(
        place="community_hall",
        mission="cape",
        conflict="grabbing",
        repair="return_space_and_apologize",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Rina",
        friend_gender="girl",
        adult_type="father",
        trait="quick",
        seed=103,
    ),
]


def explain_rejection(place_id: str, mission_id: str, conflict_id: str, repair_id: str) -> str:
    if not mission_supported(place_id, mission_id):
        return (
            f"(No story: {PLACES[place_id].label} does not support the mission '{mission_id}'. "
            f"Pick a mission that fits the place.)"
        )
    if REPAIRS[repair_id].sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair_id}': it is not a sincere or sensible way to heal hurt. "
            f"Choose a repair that apologizes and changes the plan.)"
        )
    return (
        f"(No story: the repair '{repair_id}' is too weak for the conflict '{conflict_id}'. "
        f"The reconciliation must actually meet the hurt with respect.)"
    )


ASP_RULES = r"""
supported(P, M) :- place(P), mission(M), affords(P, M).

strong_enough(C, R) :- conflict(C), repair(R),
                       severity(C, CS), power(R, RP), RP >= CS.
sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
covers_need(C, R) :- need(C, N), heal(R, N).
all_needs_met(C, R) :- conflict(C), repair(R),
                       not missing_need(C, R).
missing_need(C, R) :- need(C, N), not heal(R, N).

valid(P, M, C, R) :- supported(P, M), sensible(R), strong_enough(C, R), all_needs_met(C, R).

outcome(reconciled) :- valid(_, _, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for mission_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, mission_id))
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for conflict_id, conflict in CONFLICTS.items():
        lines.append(asp.fact("conflict", conflict_id))
        lines.append(asp.fact("severity", conflict_id, conflict.severity))
        for need in sorted(conflict.needs):
            lines.append(asp.fact("need", conflict_id, need))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
        for heal in sorted(repair.heals):
            lines.append(asp.fact("heal", repair_id, heal))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story or "yarmulke" not in sample.story:
            raise StoryError("smoke test story missing required content")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a superhero game, a yarmulke-centered conflict, and a respectful reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--adult", choices=["mother", "father", "teacher"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_choices = list(PLACES.keys())
    mission_choices = list(MISSIONS.keys())
    conflict_choices = list(CONFLICTS.keys())
    repair_choices = list(REPAIRS.keys())

    if args.place and args.mission and not mission_supported(args.place, args.mission):
        raise StoryError(explain_rejection(args.place, args.mission, args.conflict or "costume_rule", args.repair or "listen_and_apologize"))
    if args.conflict and args.repair and not repair_works(args.conflict, args.repair):
        place_hint = args.place or "park"
        mission_hint = args.mission or next(iter(sorted(PLACES[place_hint].affords)))
        raise StoryError(explain_rejection(place_hint, mission_hint, args.conflict, args.repair))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        place_hint = args.place or "park"
        mission_hint = args.mission or next(iter(sorted(PLACES[place_hint].affords)))
        conflict_hint = args.conflict or "teasing_name"
        raise StoryError(explain_rejection(place_hint, mission_hint, conflict_hint, args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mission is None or combo[1] == args.mission)
        and (args.conflict is None or combo[2] == args.conflict)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mission_id, conflict_id, repair_id = rng.choice(sorted(combos))
    hero_gender = "boy"
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    adult_type = args.adult or rng.choice(["mother", "father", "teacher"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        mission=mission_id,
        conflict=conflict_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if params.conflict not in CONFLICTS:
        raise StoryError(f"Unknown conflict: {params.conflict}")
    if params.repair not in REPAIRS:
        raise StoryError(f"Unknown repair: {params.repair}")
    if not mission_supported(params.place, params.mission):
        raise StoryError(explain_rejection(params.place, params.mission, params.conflict, params.repair))
    if not repair_works(params.conflict, params.repair):
        raise StoryError(explain_rejection(params.place, params.mission, params.conflict, params.repair))

    world = tell(
        place=PLACES[params.place],
        mission=MISSIONS[params.mission],
        conflict=CONFLICTS[params.conflict],
        repair=REPAIRS[params.repair],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mission, conflict, repair) combos:\n")
        for place_id, mission_id, conflict_id, repair_id in combos:
            print(f"  {place_id:15} {mission_id:8} {conflict_id:14} {repair_id}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.conflict} -> {p.repair} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
