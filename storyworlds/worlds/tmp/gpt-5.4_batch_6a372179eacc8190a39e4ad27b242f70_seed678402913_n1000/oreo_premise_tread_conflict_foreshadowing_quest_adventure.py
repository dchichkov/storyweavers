#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/oreo_premise_tread_conflict_foreshadowing_quest_adventure.py
=========================================================================================

A standalone story world about two children on a small adventure quest. The
Adventure Club starts with a simple premise, carries an oreo as a victory snack,
meets a risky trail obstacle, notices foreshadowing signs, argues about whether
to rush, and succeeds by learning how to tread the safe way.

The world model keeps track of:
- typed entities with physical meters and emotional memes
- a reasonableness gate for compatible obstacle/aid pairs
- a small outcome model: either the hero listens in time, or rushes and slips
  before being helped
- child-facing prose rendered from simulated state, not from frozen templates

Run it
------
    python storyworlds/worlds/gpt-5.4/oreo_premise_tread_conflict_foreshadowing_quest_adventure.py
    python storyworlds/worlds/gpt-5.4/oreo_premise_tread_conflict_foreshadowing_quest_adventure.py --place forest --obstacle stones --aid stick
    python storyworlds/worlds/gpt-5.4/oreo_premise_tread_conflict_foreshadowing_quest_adventure.py --obstacle bridge --aid boots
    python storyworlds/worlds/gpt-5.4/oreo_premise_tread_conflict_foreshadowing_quest_adventure.py --all
    python storyworlds/worlds/gpt-5.4/oreo_premise_tread_conflict_foreshadowing_quest_adventure.py --verify
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
STEADY_TRAITS = {"careful", "patient", "steady", "thoughtful"}


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
class Place:
    id: str
    label: str
    opening: str
    path: str
    goal: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    sign: str
    risk: int
    safe_verb: str
    slip_text: str
    recover_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    works_for: set[str] = field(default_factory=set)
    method: str = ""
    rescue: str = ""
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_shake(world: World) -> list[str]:
    leader = world.get("leader")
    if leader.meters["slip"] < THRESHOLD:
        return []
    sig = ("shake", "leader")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("trail").meters["danger"] += 1
    return []


def _r_resolve(world: World) -> list[str]:
    leader = world.get("leader")
    if leader.meters["saved"] < THRESHOLD:
        return []
    sig = ("resolve", "leader")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    leader.meters["slip"] = 0.0
    world.get("trail").meters["danger"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="shake", tag="physical", apply=_r_shake),
    Rule(name="resolve", tag="emotional", apply=_r_resolve),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def obstacle_supported(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.id in aid.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for aid_id, aid in AIDS.items():
                if obstacle_supported(obstacle, aid):
                    combos.append((place_id, obstacle_id, aid_id))
    return combos


def initial_care(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def will_listen(relation: str, leader_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > leader_age
    authority = initial_care(trait) + (2.0 if partner_older else 0.0)
    return authority >= 6.0


def predict_slip(obstacle: Obstacle, trait: str, relation: str,
                 leader_age: int, partner_age: int) -> bool:
    return not will_listen(relation, leader_age, partner_age, trait)


def outcome_of(params: "StoryParams") -> str:
    if will_listen(params.relation, params.leader_age, params.partner_age, params.trait):
        return "steady"
    return "slip"


def introduce(world: World, leader: Entity, partner: Entity, place: Place) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
    world.say(
        f"{leader.id} and {partner.id} belonged to the Backyard Adventure Club. "
        f"Their premise was simple: reach {place.goal} before sunset and bring back one bright leaf as proof."
    )
    world.say(
        f"In {leader.id}'s pocket waited a round oreo for the victory snack, and in {partner.id}'s hand bobbed their paper map."
    )
    world.say(place.opening)


def set_quest(world: World, place: Place, leader: Entity, partner: Entity) -> None:
    world.say(
        f"They followed {place.path} toward {place.goal}. Every few steps, {partner.id} checked the map while {leader.id} hunted for the next arrow of chalk."
    )


def foreshadow(world: World, obstacle: Obstacle, partner: Entity) -> None:
    partner.memes["caution"] += 1
    world.say(
        f"Soon they reached {obstacle.phrase}. {obstacle.sign}"
    )
    world.say(
        f'{partner.id} slowed down. "That feels like a warning," {partner.pronoun()} said.'
    )


def argue(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, aid: Aid) -> None:
    leader.memes["defiance"] += 1
    partner.memes["concern"] += 1
    world.say(
        f'"We will miss the leaf if we stop now," {leader.id} said. "{leader.pronoun().capitalize()} can cross first."'
    )
    world.say(
        f'{partner.id} shook {partner.pronoun("possessive")} head. "Not like that. We should use {aid.phrase} and {obstacle.safe_verb}."'
    )


def choose_steady(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, aid: Aid) -> None:
    leader.memes["trust"] += 1
    leader.memes["lesson"] += 1
    world.say(
        f"{leader.id} looked again at {obstacle.label} and finally nodded. The warning had sounded bossy at first, but now it sounded wise."
    )
    world.say(
        f"Together they used {aid.phrase} and {aid.method}. {leader.id} did not rush. {leader.pronoun().capitalize()} chose where to tread, one careful step at a time."
    )


def choose_slip(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, aid: Aid) -> None:
    leader.meters["slip"] += 1
    leader.memes["shock"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {leader.id} hurried ahead before {partner.id} could stop {leader.pronoun('object')}. {obstacle.slip_text}"
    )
    world.say(
        f'{partner.id} gasped, then moved fast. Using {aid.phrase}, {partner.pronoun()} {aid.rescue}.'
    )
    leader.meters["saved"] += 1
    leader.memes["lesson"] += 1
    partner.memes["brave"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.recover_text)


def finish_quest(world: World, place: Place, leader: Entity, partner: Entity) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"Past the obstacle, the trail widened and the rest of the quest felt possible again. They reached {place.goal}, chose the brightest leaf they could find, and tucked it into the map."
    )
    world.say(
        f"At the end, {leader.id} broke the oreo in half and shared it with {partner.id}. {place.ending}"
    )


def tell(place: Place, obstacle: Obstacle, aid: Aid,
         leader_name: str, leader_gender: str,
         partner_name: str, partner_gender: str,
         trait: str, parent_type: str,
         relation: str, leader_age: int, partner_age: int) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=["bold"],
        age=leader_age,
        attrs={"relation": relation},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=[trait],
        age=partner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    trail = world.add(Entity(id="trail", kind="thing", type="trail", label="trail"))
    token = world.add(Entity(id="leaf", kind="thing", type="leaf", label="leaf"))
    snack = world.add(Entity(id="snack", kind="thing", type="oreo", label="oreo"))
    tool = world.add(Entity(id="aid", kind="thing", type="aid", label=aid.label))
    trail.tags.update(place.tags | obstacle.tags)
    snack.tags.add("oreo")
    tool.tags.update(aid.tags)

    introduce(world, leader, partner, place)
    set_quest(world, place, leader, partner)

    world.para()
    foreshadow(world, obstacle, partner)
    argue(world, leader, partner, obstacle, aid)

    world.para()
    if will_listen(relation, leader_age, partner_age, trait):
        choose_steady(world, leader, partner, obstacle, aid)
        outcome = "steady"
    else:
        choose_slip(world, leader, partner, obstacle, aid)
        outcome = "slip"

    world.para()
    finish_quest(world, place, leader, partner)

    world.facts.update(
        place=place,
        obstacle=obstacle,
        aid=aid,
        leader=leader,
        partner=partner,
        parent=parent,
        trail=trail,
        token=token,
        snack=snack,
        outcome=outcome,
        relation=relation,
        predicted_slip=predict_slip(obstacle, trait, relation, leader_age, partner_age),
        crossed=True,
        found_leaf=True,
    )
    return world


PLACES = {
    "forest": Place(
        id="forest",
        label="forest path",
        opening="The forest trail curled under ferns and low branches, as if it were hiding a treasure at the end.",
        path="a mossy path",
        goal="the old stump lookout",
        ending="Behind them, the trees glowed gold, and the club's first real quest felt wonderfully true.",
        tags={"forest", "quest"},
    ),
    "cliff": Place(
        id="cliff",
        label="cliff path",
        opening="The cliff path leaned over the sea, where gulls wheeled like white kites over the water.",
        path="a windy path",
        goal="the shell marker on the bluff",
        ending="Below them, the waves boomed and sparkled, and both children stood taller than before.",
        tags={"sea", "quest"},
    ),
    "meadow": Place(
        id="meadow",
        label="meadow trail",
        opening="The meadow trail ran between tall grass and humming bees, bright and wide like a green ribbon.",
        path="a sunny track",
        goal="the willow arch at the hilltop",
        ending="The grass whispered around their ankles, and the hill no longer felt far away at all.",
        tags={"meadow", "quest"},
    ),
}

OBSTACLES = {
    "stones": Obstacle(
        id="stones",
        label="the stepping stones",
        phrase="a line of stepping stones across a quick stream",
        sign="The middle stone gave a tiny wobble, and the water below slapped at it like impatient hands.",
        risk=2,
        safe_verb="tread from the wide stone to the next one",
        slip_text="One shoe skidded on the wet edge, and {leader} windmilled both arms.".replace("{leader}", "the leader"),
        recover_text="For one scary breath the stream tugged at a shoe, but the grip held and the fall stopped before it became a splash.",
        tags={"stream", "stones"},
    ),
    "bridge": Obstacle(
        id="bridge",
        label="the rope bridge",
        phrase="a rope bridge stretched between two banks",
        sign="One plank answered with a long creak, and the ropes gave a slow little shiver in the wind.",
        risk=3,
        safe_verb="tread along the middle boards",
        slip_text="A foot landed on the edge of a plank, and the whole bridge bounced with a sickening jerk.",
        recover_text="The bridge swayed hard once, then settled. After that, every step was smaller and smarter.",
        tags={"bridge", "heights"},
    ),
    "slope": Obstacle(
        id="slope",
        label="the muddy slope",
        phrase="a muddy slope climbing toward the last part of the trail",
        sign="The mud shone too smoothly, and little pebbles kept sliding down by themselves.",
        risk=2,
        safe_verb="tread in the grassy side marks",
        slip_text="A heel slid backward, and a spray of mud shot out from under one foot.",
        recover_text="Hands grabbed, boots dug in, and the slide slowed to a stop. Even the mud seemed less tricky once they respected it.",
        tags={"mud", "slope"},
    ),
}

AIDS = {
    "stick": Aid(
        id="stick",
        label="walking stick",
        phrase="a walking stick",
        works_for={"stones", "slope"},
        method="testing each step before putting full weight down",
        rescue="hooked the stick against a safe edge and steadied the wobbling child",
        tags={"stick", "careful"},
    ),
    "rope": Aid(
        id="rope",
        label="guide rope",
        phrase="the guide rope from their pack",
        works_for={"bridge", "slope"},
        method="keeping the rope tight between them like a helpful line",
        rescue="snapped the rope tight and pulled the stumbling child back toward the center",
        tags={"rope", "careful"},
    ),
    "boots": Aid(
        id="boots",
        label="grip boots",
        phrase="their grip boots",
        works_for={"stones", "slope"},
        method="pressing the rough soles down slowly before the next move",
        rescue="planted both rough soles and caught the slipping child by the sleeve",
        tags={"boots", "careful"},
    ),
    "rail": Aid(
        id="rail",
        label="bridge hand-rope",
        phrase="the bridge hand-rope",
        works_for={"bridge"},
        method="keeping both hands on the side ropes and eyes on the center planks",
        rescue="caught the child's arm while the other hand held fast to the rope",
        tags={"bridge", "careful"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "patient", "steady", "thoughtful", "curious", "quick"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    aid: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    parent: str
    trait: str
    relation: str = "friends"
    leader_age: int = 6
    partner_age: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "oreo": [
        (
            "What is an oreo?",
            "An oreo is a sweet sandwich cookie with cream in the middle. It is a snack, not a trail tool, so in the story it works as a small reward at the end."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a clear goal, like reaching a special place or bringing something back. Adventures feel exciting because the travelers are trying to do something on purpose."
        )
    ],
    "foreshadow": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is an early clue that hints something important may happen later. A creak, a wobble, or a warning can make readers expect trouble before it comes."
        )
    ],
    "bridge": [
        (
            "Why should you cross a rope bridge carefully?",
            "A rope bridge can sway and bounce under your feet. Small, slow steps help you keep your balance."
        )
    ],
    "stones": [
        (
            "Why can stepping stones be slippery?",
            "Water can make stone smooth and slick. That is why people tread carefully on wet stones."
        )
    ],
    "mud": [
        (
            "Why is mud hard to walk on?",
            "Mud can slide under your shoes because it is soft and wet. That makes it easy to lose your footing."
        )
    ],
    "rope": [
        (
            "How can a rope help on a trail?",
            "A rope gives you something steady to hold or pull against. It can help people keep balance when the ground feels tricky."
        )
    ],
    "stick": [
        (
            "Why do hikers use a walking stick?",
            "A walking stick can test the ground before a full step and help a person balance. It is useful on uneven places."
        )
    ],
    "boots": [
        (
            "What do grip boots do?",
            "Grip boots have rough soles that hold the ground better. They help people stand more safely on slippery places."
        )
    ],
}
KNOWLEDGE_ORDER = ["oreo", "quest", "foreshadow", "bridge", "stones", "mud", "rope", "stick", "boots"]


def pair_noun(leader: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and partner.type == "boy":
            return "two brothers"
        if leader.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    place = f["place"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    outcome = f["outcome"]
    base = (
        f'Write a short Adventure story for a 3-to-5-year-old that includes the words "oreo", "premise", and "tread". '
        f"Use Conflict, Foreshadowing, and Quest while two children travel toward {place.goal}."
    )
    if outcome == "steady":
        return [
            base,
            f"Tell an adventure where {leader.id} wants to hurry across {obstacle.label}, but {partner.id} notices the danger first and teaches {leader.pronoun('object')} to tread safely with {aid.phrase}.",
            f"Write a gentle quest story where the club's simple premise leads to a small argument, a warning sign, and a smart crossing that ends with the children sharing an oreo.",
        ]
    return [
        base,
        f"Tell an adventure where {leader.id} rushes at {obstacle.label} after foreshadowing warns of trouble, and {partner.id} uses {aid.phrase} to help when the crossing goes wrong.",
        f"Write a quest story with a real conflict between rushing and being careful, where a child slips, learns to tread wisely, and still reaches the goal in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    place = f["place"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    relation = f["relation"]
    pair = pair_noun(leader, partner, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {partner.id}, on a small adventure quest. They want to reach {place.goal} and bring back a bright leaf."
        ),
        (
            "What was the club's premise?",
            f"Their premise was that they would follow the trail, reach {place.goal}, and return with one bright leaf. That simple plan turned an ordinary walk into a quest."
        ),
        (
            "Why was the obstacle a warning sign?",
            f"{obstacle.sign} That clue foreshadowed trouble and told the children the crossing could go wrong if they rushed."
        ),
        (
            "What was the conflict?",
            f"The conflict was between hurrying and being careful. {leader.id} wanted to press on fast, but {partner.id} wanted to use {aid.label} and tread the safe way."
        ),
    ]
    if f["outcome"] == "steady":
        qa.append(
            (
                f"How did {leader.id} cross safely?",
                f"{leader.id} listened before anything bad happened. Together the children used {aid.phrase} and crossed with slow, careful steps, which solved the problem before a fall began."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {leader.id} rushed?",
                f"{leader.id} slipped during the crossing and frightened both children. Then {partner.id} used {aid.phrase} to steady the danger, and that quick help turned the mistake into a lesson."
            )
        )
    qa.append(
        (
            "How did the quest end?",
            f"They reached {place.goal}, picked a bright leaf, and shared the oreo as a victory snack. The ending shows they finished the quest more wisely than they began it."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"oreo", "quest", "foreshadow"}
    obstacle = f["obstacle"]
    aid = f["aid"]
    if obstacle.id == "bridge":
        tags.add("bridge")
    if obstacle.id == "stones":
        tags.add("stones")
    if obstacle.id == "slope":
        tags.add("mud")
    if aid.id == "rope" or aid.id == "rail":
        tags.add("rope")
    if aid.id == "stick":
        tags.add("stick")
    if aid.id == "boots":
        tags.add("boots")
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
    for ent in world.entities.values():
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="forest",
        obstacle="stones",
        aid="stick",
        leader_name="Tom",
        leader_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        leader_age=5,
        partner_age=7,
    ),
    StoryParams(
        place="cliff",
        obstacle="bridge",
        aid="rail",
        leader_name="Mia",
        leader_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        parent="father",
        trait="quick",
        relation="friends",
        leader_age=6,
        partner_age=6,
    ),
    StoryParams(
        place="meadow",
        obstacle="slope",
        aid="boots",
        leader_name="Zoe",
        leader_gender="girl",
        partner_name="Nora",
        partner_gender="girl",
        parent="mother",
        trait="steady",
        relation="siblings",
        leader_age=4,
        partner_age=6,
    ),
    StoryParams(
        place="forest",
        obstacle="bridge",
        aid="rail",
        leader_name="Sam",
        leader_gender="boy",
        partner_name="Eli",
        partner_gender="boy",
        parent="father",
        trait="thoughtful",
        relation="friends",
        leader_age=6,
        partner_age=6,
    ),
]


def explain_rejection(obstacle: Obstacle, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} is not a good fix for {obstacle.label}. "
        f"The crossing needs a tool that really fits the obstacle, so pick one of: "
        f"{', '.join(sorted(a.id for a in AIDS.values() if obstacle.id in a.works_for))}.)"
    )


ASP_RULES = r"""
compatible(O, A) :- obstacle(O), aid(A), works_for(A, O).
valid(P, O, A) :- place(P), obstacle(O), aid(A), compatible(O, A).

steady_trait(T) :- trait(T), careful_trait(T).
care(5) :- trait(T), steady_trait(T).
care(3) :- trait(T), not steady_trait(T).

older_partner :- relation(siblings), leader_age(LA), partner_age(PA), PA > LA.
bonus(2) :- older_partner.
bonus(0) :- not older_partner.
authority(C + B) :- care(C), bonus(B).

outcome(steady) :- authority(A), A >= 6.
outcome(slip) :- authority(A), A < 6.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for oid in sorted(aid.works_for):
            lines.append(asp.fact("works_for", aid_id, oid))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("leader_age", params.leader_age),
            asp.fact("partner_age", params.partner_age),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    cases = list(CURATED)
    for seed in range(80):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an oreo quest, a warning on the trail, and learning how to tread safely."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.aid:
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not obstacle_supported(obstacle, aid):
            raise StoryError(explain_rejection(obstacle, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, aid = rng.choice(sorted(combos))
    leader_name, leader_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["friends", "siblings"])
    leader_age, partner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        place=place,
        obstacle=obstacle,
        aid=aid,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        leader_age=leader_age,
        partner_age=partner_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        obstacle = OBSTACLES[params.obstacle]
        aid = AIDS[params.aid]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]})") from exc

    if not obstacle_supported(obstacle, aid):
        raise StoryError(explain_rejection(obstacle, aid))

    world = tell(
        place=place,
        obstacle=obstacle,
        aid=aid,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        trait=params.trait,
        parent_type=params.parent,
        relation=params.relation,
        leader_age=params.leader_age,
        partner_age=params.partner_age,
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
        print(f"{len(combos)} compatible (place, obstacle, aid) combos:\n")
        for place, obstacle, aid in combos:
            print(f"  {place:8} {obstacle:8} {aid}")
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
            header = f"### {p.leader_name} & {p.partner_name}: {p.place} / {p.obstacle} / {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
