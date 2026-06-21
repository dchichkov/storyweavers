#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/election_eleventh_lesson_learned_friendship_animal_story.py
======================================================================================

A small storyworld about a woodland school election on the eleventh morning of
Blossom Week. Two animal friends both care about the same little job. One of
them gets too busy trying to win, hurts the other friend's feelings, and then
must choose between chasing votes and helping when a practical problem interrupts
the election. The lesson is that friendship and useful kindness matter more than
showy winning.

Run it
------
    python storyworlds/worlds/gpt-5.4/election_eleventh_lesson_learned_friendship_animal_story.py
    python storyworlds/worlds/gpt-5.4/election_eleventh_lesson_learned_friendship_animal_story.py --office acorn_counter
    python storyworlds/worlds/gpt-5.4/election_eleventh_lesson_learned_friendship_animal_story.py --obstacle lost_arrows
    python storyworlds/worlds/gpt-5.4/election_eleventh_lesson_learned_friendship_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/election_eleventh_lesson_learned_friendship_animal_story.py --verify
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
        female = {"girl", "hen", "duck", "goose"}
        male = {"boy", "fox", "bear", "frog", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Office:
    id: str
    label: str
    event: str
    duty: str
    skill: str
    badge: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    problem: str
    need: str
    mishap_text: str
    friend_start: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    skill: str
    fixes: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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
        return clone


def _r_confusion(world: World) -> list[str]:
    room = world.entities.get("room")
    obstacle = world.entities.get("obstacle")
    if room is None or obstacle is None:
        return []
    if obstacle.meters["active"] < THRESHOLD:
        return []
    sig = ("confusion", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["confusion"] += 1
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return []


def _r_friendship_repair(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return []
    if hero.meters["helping"] < THRESHOLD:
        return []
    sig = ("friendship_repair", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["care"] += 1
    hero.memes["regret"] += 1
    friend.memes["trust"] += 1
    friend.memes["warmth"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="confusion", tag="physical", apply=_r_confusion),
    Rule(name="friendship_repair", tag="social", apply=_r_friendship_repair),
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
                # Rule may have changed state without yielding text.
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


OFFICES = {
    "acorn_counter": Office(
        id="acorn_counter",
        label="Acorn Counter",
        event="the nut picnic",
        duty="count the acorn votes and later count the acorn cookies for everyone",
        skill="counting",
        badge="a little bark badge with painted numbers",
        ending_image="counting acorn cookies into neat little rows together",
        tags={"election", "counting", "acorn"},
    ),
    "parade_guide": Office(
        id="parade_guide",
        label="Parade Guide",
        event="the blossom parade",
        duty="lead the little animals along the trail to the singing hill",
        skill="direction",
        badge="a green leaf sash",
        ending_image="leading the blossom parade shoulder to shoulder along the trail",
        tags={"election", "direction", "parade"},
    ),
    "morning_caller": Office(
        id="morning_caller",
        label="Morning Caller",
        event="the breakfast gathering",
        duty="call everyone together with a clear voice when breakfast starts",
        skill="calling",
        badge="a shiny bell on a ribbon",
        ending_image="ringing the bell and calling the sleepy animals together side by side",
        tags={"election", "voice", "bell"},
    ),
}

OBSTACLES = {
    "mixed_ballots": Obstacle(
        id="mixed_ballots",
        label="mixed ballots",
        problem="a gust of wind tumbles the leaf ballots into one whirling pile",
        need="counting",
        mishap_text="Just then a breeze skipped through the open school window and stirred the leaf ballots into one whirling pile on the floor.",
        friend_start="knelt down to sort the ballots by shape and number",
        tags={"ballot", "wind", "counting"},
    ),
    "lost_arrows": Obstacle(
        id="lost_arrows",
        label="lost arrows",
        problem="the chalk arrows to the singing hill wash away in a splash from the brook",
        need="direction",
        mishap_text="Just then a splash from the brook smeared the chalk arrows, and the trail to the singing hill stopped making sense.",
        friend_start="began laying fresh pebble arrows so nobody would get lost",
        tags={"trail", "direction", "brook"},
    ),
    "sleepy_crowd": Obstacle(
        id="sleepy_crowd",
        label="sleepy crowd",
        problem="the youngest animals cannot hear where to gather",
        need="calling",
        mishap_text="Just then the youngest animals drifted the wrong way, blinking and sleepy, because they could not hear where breakfast was meant to begin.",
        friend_start="climbed onto a stump and tried to call the little ones back",
        tags={"voice", "breakfast", "crowd"},
    ),
}

REPAIRS = {
    "sort_ballots": Repair(
        id="sort_ballots",
        label="sort ballots",
        skill="counting",
        fixes={"mixed_ballots"},
        action_text="sat beside {friend} and sorted the leaf ballots into tidy counting piles",
        qa_text="sorted the leaf ballots into tidy counting piles",
        tags={"counting", "ballot"},
    ),
    "pebble_path": Repair(
        id="pebble_path",
        label="pebble path",
        skill="direction",
        fixes={"lost_arrows"},
        action_text="hurried over to help {friend} lay bright pebble arrows from the school door to the singing hill",
        qa_text="laid bright pebble arrows so the parade trail was clear again",
        tags={"direction", "trail"},
    ),
    "stump_call": Repair(
        id="stump_call",
        label="stump call",
        skill="calling",
        fixes={"sleepy_crowd"},
        action_text="jumped onto the stump beside {friend} and gave a warm, ringing call that reached the sleepy little ones",
        qa_text="called the youngest animals back in a warm, ringing voice",
        tags={"calling", "voice"},
    ),
}


@dataclass
class StoryParams:
    office: str
    obstacle: str
    repair: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    teacher_name: str
    teacher_type: str
    delay: int = 0
    seed: Optional[int] = None


ANIMALS = [
    ("Moss", "frog"),
    ("Pip", "fox"),
    ("Hazel", "duck"),
    ("Nibbles", "rabbit"),
    ("Bramble", "badger"),
    ("Sunny", "hen"),
    ("Otis", "bear"),
    ("Dot", "goose"),
]

TEACHERS = [
    ("Owl", "teacher"),
    ("Badger", "teacher"),
    ("Mole", "teacher"),
]


CURATED = [
    StoryParams(
        office="acorn_counter",
        obstacle="mixed_ballots",
        repair="sort_ballots",
        hero_name="Moss",
        hero_type="frog",
        friend_name="Hazel",
        friend_type="duck",
        teacher_name="Owl",
        teacher_type="teacher",
        delay=0,
    ),
    StoryParams(
        office="parade_guide",
        obstacle="lost_arrows",
        repair="pebble_path",
        hero_name="Pip",
        hero_type="fox",
        friend_name="Dot",
        friend_type="goose",
        teacher_name="Badger",
        teacher_type="teacher",
        delay=1,
    ),
    StoryParams(
        office="morning_caller",
        obstacle="sleepy_crowd",
        repair="stump_call",
        hero_name="Nibbles",
        hero_type="rabbit",
        friend_name="Sunny",
        friend_type="hen",
        teacher_name="Mole",
        teacher_type="teacher",
        delay=0,
    ),
]


def valid_combo(office: Office, obstacle: Obstacle, repair: Repair) -> bool:
    return office.skill == obstacle.need == repair.skill and obstacle.id in repair.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for office_id, office in OFFICES.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for repair_id, repair in REPAIRS.items():
                if valid_combo(office, obstacle, repair):
                    combos.append((office_id, obstacle_id, repair_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    return "hero_wins" if params.delay == 0 else "friend_wins"


def explain_rejection(office: Office, obstacle: Obstacle, repair: Repair) -> str:
    return (
        f"(No story: the office '{office.label}' depends on {office.skill}, but the "
        f"obstacle '{obstacle.label}' needs {obstacle.need} and the repair "
        f"'{repair.label}' uses {repair.skill}. This world only tells elections where "
        f"the interrupted problem truly tests the same skill the office is meant for.)"
    )


def predict_help(world: World, repair: Repair) -> dict:
    sim = world.copy()
    sim.get("hero").meters["helping"] += 1
    sim.get("obstacle").meters["active"] = 0.0
    sim.get("room").meters["confusion"] = 0.0
    propagate(sim, narrate=False)
    return {
        "friendship": sim.get("friend").memes["trust"] + sim.get("friend").memes["warmth"],
        "confusion": sim.get("room").meters["confusion"],
        "repair": repair.label,
    }


def introduce(world: World, hero: Entity, friend: Entity, teacher: Entity, office: Office) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"On the eleventh morning of Blossom Week, {teacher.id}'s little woodland school was buzzing. "
        f"It was election day for the job of {office.label}, the animal who would {office.duty} during {office.event}."
    )
    world.say(
        f"{hero.id} the {hero.type} and {friend.id} the {friend.type} were best friends, and both of them thought the tiny job looked very important."
    )


def prepare(world: World, hero: Entity, friend: Entity, office: Office) -> None:
    world.say(
        f"Before class, they painted leaf signs together and practiced what they would say. "
        f"{hero.id} dreamed about wearing {office.badge}, while {friend.id} smiled and said the best part would be helping everyone."
    )


def campaign(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["pride"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"When the other little animals began to gather, {hero.id} felt a hot flutter in {hero.pronoun('possessive')} chest. "
        f'"Please look at my sign first," {hero.pronoun()} blurted. "I need every vote."'
    )
    world.say(
        f"{friend.id} still held the paintbrush they had shared. The words were not very mean, but they made {friend.pronoun('object')} feel pushed aside."
    )


def mishap(world: World, obstacle: Obstacle, friend: Entity) -> None:
    world.get("obstacle").meters["active"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.mishap_text)
    world.say(
        f"{friend.id} did not stop to pout. {friend.pronoun().capitalize()} {obstacle.friend_start}."
    )


def delay_beat(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"For one more moment, {hero.id} kept pointing at the sign and asking for votes. "
        f"Then {hero.pronoun()} heard the wobble in the room and saw that winning would not help anybody if the job itself was being left undone."
    )


def apology_and_join(world: World, hero: Entity, friend: Entity, repair: Repair) -> None:
    hero.meters["helping"] += 1
    hero.memes["regret"] += 1
    world.get("obstacle").meters["active"] = 0.0
    world.get("room").meters["confusion"] = 0.0
    propagate(world, narrate=False)
    action = repair.action_text.format(friend=friend.id)
    world.say(
        f'"{friend.id}, I am sorry," {hero.id} said. "Our friendship matters more than my sign."'
    )
    world.say(
        f"Then {hero.id} {action}."
    )


def teacher_judges(world: World, teacher: Entity, hero: Entity, friend: Entity, office: Office, outcome: str) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    if outcome == "hero_wins":
        hero.meters["votes"] += 6
        friend.meters["votes"] += 5
        winner = hero
        loser = friend
        world.say(
            f'{teacher.id} blinked kindly behind wide spectacles. "An election is not only about being noticed," {teacher.pronoun()} said. '
            f'"It is about doing the work when the work appears."'
        )
        world.say(
            f"The class dropped acorn votes into the basket, and {hero.id} won by one tiny vote. "
            f"{friend.id} clapped first."
        )
    else:
        hero.meters["votes"] += 4
        friend.meters["votes"] += 6
        winner = friend
        loser = hero
        world.say(
            f'{teacher.id} looked at the now-orderly room and nodded. "An election is not only about a pretty sign," {teacher.pronoun()} said. '
            f'"It is about staying useful and kind all the way through."'
        )
        world.say(
            f"When the votes were counted, {friend.id} won the badge. {hero.id}'s ears drooped for one breath, and then {hero.pronoun()} smiled for real."
        )
    loser.memes["grace"] += 1
    winner.memes["joy"] += 1
    world.facts["winner"] = winner
    world.facts["loser"] = loser
    world.say(
        f'"Will you still help me?" {winner.id} asked softly.'
    )
    world.say(
        f'"Of course," {loser.id} answered. "Friends first."'
    )
    world.say(
        f"By afternoon, they were {office.ending_image}, and nobody looking at them could tell where the election ended and the friendship began."
    )


def tell(
    office: Office,
    obstacle: Obstacle,
    repair: Repair,
    hero_name: str,
    hero_type: str,
    friend_name: str,
    friend_type: str,
    teacher_name: str,
    teacher_type: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, phrase=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, phrase=friend_name, role="friend"))
    teacher = world.add(Entity(id="teacher", kind="character", type=teacher_type, label=teacher_name, phrase=teacher_name, role="teacher"))
    room = world.add(Entity(id="room", type="room", label="schoolroom"))
    world.add(Entity(id="obstacle", type="problem", label=obstacle.label))

    introduce(world, hero=hero_named(hero), friend=hero_named(friend), teacher=hero_named(teacher), office=office)
    prepare(world, hero=hero_named(hero), friend=hero_named(friend), office=office)

    world.para()
    campaign(world, hero=hero_named(hero), friend=hero_named(friend))
    mishap(world, obstacle=obstacle, friend=hero_named(friend))

    world.para()
    prediction = predict_help(world, repair)
    world.facts["predicted_friendship_gain"] = prediction["friendship"]
    if delay == 1:
        delay_beat(world, hero=hero_named(hero))
    apology_and_join(world, hero=hero_named(hero), friend=hero_named(friend), repair=repair)

    world.para()
    teacher_judges(
        world,
        teacher=hero_named(teacher),
        hero=hero_named(hero),
        friend=hero_named(friend),
        office=office,
        outcome=outcome_of(
            StoryParams(
                office=office.id,
                obstacle=obstacle.id,
                repair=repair.id,
                hero_name=hero_name,
                hero_type=hero_type,
                friend_name=friend_name,
                friend_type=friend_type,
                teacher_name=teacher_name,
                teacher_type=teacher_type,
                delay=delay,
            )
        ),
    )
    world.facts.update(
        office=office,
        obstacle_cfg=obstacle,
        repair=repair,
        hero=hero_named(hero),
        friend=hero_named(friend),
        teacher=hero_named(teacher),
        outcome=outcome_of(
            StoryParams(
                office=office.id,
                obstacle=obstacle.id,
                repair=repair.id,
                hero_name=hero_name,
                hero_type=hero_type,
                friend_name=friend_name,
                friend_type=friend_type,
                teacher_name=teacher_name,
                teacher_type=teacher_type,
                delay=delay,
            )
        ),
        delayed=delay == 1,
        fixed=True,
        friendship_repaired=friend.memes["trust"] + friend.memes["warmth"] >= THRESHOLD,
    )
    return world


def hero_named(ent: Entity) -> Entity:
    shown = copy.deepcopy(ent)
    shown.id = ent.label
    return shown


KNOWLEDGE = {
    "election": [
        (
            "What is an election?",
            "An election is when a group chooses someone for a job by voting. Each vote helps show whom the group trusts for that work.",
        )
    ],
    "friendship": [
        (
            "What makes a good friendship?",
            "A good friendship means being kind, telling the truth, and helping each other when something goes wrong. Friends can still feel upset sometimes, but they try to make things right.",
        )
    ],
    "counting": [
        (
            "Why is careful counting important in voting?",
            "Careful counting matters because each vote should be counted fairly. If the count gets mixed up, the class cannot know the true result.",
        )
    ],
    "direction": [
        (
            "Why do paths need clear signs?",
            "Clear signs help everyone know where to go together. Without them, a group can wander the wrong way and get confused.",
        )
    ],
    "calling": [
        (
            "Why does a clear voice help a group?",
            "A clear voice helps everyone hear the same message at the same time. That makes it easier for a group to gather and move together.",
        )
    ],
    "ballot": [
        (
            "What is a ballot?",
            "A ballot is the thing you use to show your vote in an election. It might be a slip of paper, a leaf, or another small token in a pretend game.",
        )
    ],
}
KNOWLEDGE_ORDER = ["election", "friendship", "counting", "direction", "calling", "ballot"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    office = f["office"]
    return [
        'Write a gentle animal story for a 3-to-5-year-old that includes the words "election" and "eleventh".',
        f"Tell a woodland school story where {hero.id} and {friend.id} are friends during an election for {office.label}, and a lesson about friendship matters more than winning.",
        f"Write a TinyStories-style animal tale where an interrupted election shows that doing the helpful work is more important than showing off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    teacher = f["teacher"]
    office = f["office"]
    obstacle = f["obstacle_cfg"]
    repair = f["repair"]
    winner = f["winner"]
    loser = f["loser"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id} the {friend.type}, two friends at woodland school. Their teacher, {teacher.id}, watches over the election.",
        ),
        (
            "What was the election for?",
            f"The election was for the job of {office.label}. That job meant {office.duty}.",
        ),
        (
            f"Why did {friend.id}'s feelings get hurt?",
            f"{hero.id} became so eager to win that {hero.pronoun()} asked everyone to look at {hero.pronoun('possessive')} sign first and pushed the shared work aside. The words were small, but they made {friend.id} feel unimportant.",
        ),
        (
            f"What problem interrupted the election?",
            f"The problem was {obstacle.problem}. It mattered because the office of {office.label} is supposed to use {office.skill}, and the class suddenly needed exactly that skill.",
        ),
        (
            f"How did {hero.id} try to make things right?",
            f"{hero.pronoun().capitalize()} apologized to {friend.id} and {repair.qa_text}. That helped the room calm down and showed that {hero.pronoun()} cared more about helping than showing off.",
        ),
    ]
    if f["outcome"] == "hero_wins":
        qa.append(
            (
                f"Who won the election, and why?",
                f"{winner.id} won the election by one vote. {teacher.id} noticed that {hero.id} stopped chasing attention and did the real work when the problem appeared.",
            )
        )
    else:
        qa.append(
            (
                f"Who won the election, and why?",
                f"{winner.id} won the election. {teacher.id} saw that {friend.id} stayed useful and kind from the very start, and that mattered more than a pretty campaign sign.",
            )
        )
    qa.append(
        (
            "What lesson did the friends learn?",
            f"They learned that friendship and helpful work matter more than winning. The ending proves it because {winner.id} and {loser.id} still worked together after the votes were finished.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"election", "friendship", f["office"].skill}
    if f["obstacle_cfg"].id == "mixed_ballots":
        tags.add("ballot")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label and ent.label != ent.id:
            bits.append(f"label={ent.label}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(O, Ob, R) :- office(O), obstacle(Ob), repair(R),
                   office_skill(O, S), obstacle_need(Ob, S), repair_skill(R, S),
                   fixes(R, Ob).

hero_wins   :- delay(0).
friend_wins :- delay(1).

outcome(hero_wins)   :- hero_wins.
outcome(friend_wins) :- friend_wins.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for office_id, office in OFFICES.items():
        lines.append(asp.fact("office", office_id))
        lines.append(asp.fact("office_skill", office_id, office.skill))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_need", obstacle_id, obstacle.need))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_skill", repair_id, repair.skill))
        for fixed in sorted(repair.fixes):
            lines.append(asp.fact("fixes", repair_id, fixed))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("delay", params.delay)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story election world. Unspecified choices are randomized with a seed."
    )
    ap.add_argument("--office", choices=sorted(OFFICES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = hero helps right away; 1 = hero hesitates and the friend wins")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_animals(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    a, b = rng.sample(ANIMALS, 2)
    return a, b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.office and args.obstacle and args.repair:
        office = OFFICES[args.office]
        obstacle = OBSTACLES[args.obstacle]
        repair = REPAIRS[args.repair]
        if not valid_combo(office, obstacle, repair):
            raise StoryError(explain_rejection(office, obstacle, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.office is None or combo[0] == args.office)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    office_id, obstacle_id, repair_id = rng.choice(sorted(combos))
    (hero_name, hero_type), (friend_name, friend_type) = pick_animals(rng)
    teacher_name, teacher_type = rng.choice(TEACHERS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        office=office_id,
        obstacle=obstacle_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        teacher_name=teacher_name,
        teacher_type=teacher_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.office not in OFFICES:
        raise StoryError(f"(Unknown office: {params.office})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.delay not in {0, 1}:
        raise StoryError("(Delay must be 0 or 1.)")

    office = OFFICES[params.office]
    obstacle = OBSTACLES[params.obstacle]
    repair = REPAIRS[params.repair]
    if not valid_combo(office, obstacle, repair):
        raise StoryError(explain_rejection(office, obstacle, repair))

    world = tell(
        office=office,
        obstacle=obstacle,
        repair=repair,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        teacher_name=params.teacher_name,
        teacher_type=params.teacher_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (office, obstacle, repair) combos:\n")
        for office, obstacle, repair in combos:
            print(f"  {office:14} {obstacle:14} {repair}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.office} / {p.obstacle} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
