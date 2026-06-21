#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/smush_dash_destructor_reconciliation_suspense_dialogue_folk.py
=========================================================================================

A small folk-tale storyworld about two children sent along a risky path with a
fragile gift. They quarrel over who should lead, hear that the village beast
called Destructor is near, and must reconcile in time to keep the gift from
being ruined.

The seed words are built into the domain itself:
- "smush" appears when a fragile gift is threatened or damaged.
- "dash" appears when a child rushes ahead in fear or pride.
- "Destructor" is the nickname of the village ram, famous for smashing dropped food.

The world model tracks:
- physical state: fragile gifts, risky paths, dropped crumbs, pursuit
- emotional state: pride, fear, trust, apology, relief

The domain prefers a small set of plausible combinations:
a route only matters when it genuinely threatens the chosen gift, and a plan is
only accepted when it actually protects the relevant risk.

Run it
------
python storyworlds/worlds/gpt-5.4/smush_dash_destructor_reconciliation_suspense_dialogue_folk.py
python storyworlds/worlds/gpt-5.4/smush_dash_destructor_reconciliation_suspense_dialogue_folk.py --all
python storyworlds/worlds/gpt-5.4/smush_dash_destructor_reconciliation_suspense_dialogue_folk.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/smush_dash_destructor_reconciliation_suspense_dialogue_folk.py --verify
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
GENTLE_TRAITS = {"patient", "kind", "steady", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    hazards: set[str] = field(default_factory=set)
    severity: int = 1
    omen: str = ""
    crossing: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    weaknesses: set[str] = field(default_factory=set)
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Plan:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    power: int = 1
    prep: str = ""
    carry: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "helper"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def risk_tags(route: Route, gift: Gift) -> set[str]:
    return set(route.hazards) & set(gift.weaknesses)


def valid_combo(route: Route, gift: Gift, plan: Plan) -> bool:
    risks = risk_tags(route, gift)
    return bool(risks) and risks.issubset(plan.protects)


def trip_severity(route: Route, delay: int) -> int:
    return route.severity + delay


def is_early_reconcile(relation: str, leader_age: int, helper_age: int, trait: str) -> bool:
    return relation == "siblings" and helper_age > leader_age and trait in GENTLE_TRAITS


def can_save(plan: Plan, route: Route, delay: int) -> bool:
    return plan.power >= trip_severity(route, delay)


def _r_spill(world: World) -> list[str]:
    gift = world.get("gift")
    beast = world.get("destructor")
    if gift.meters["damaged"] < THRESHOLD:
        return []
    sig = ("spill", gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gift.meters["crumbs"] += 1
    beast.meters["alert"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__danger__"]


def _r_chase(world: World) -> list[str]:
    beast = world.get("destructor")
    if beast.meters["alert"] < THRESHOLD:
        return []
    sig = ("chase", beast.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    beast.meters["pursuit"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__chase__"]


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="chase", tag="physical", apply=_r_chase),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(x for x in produced if not x.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


ROUTES = {
    "reed_bridge": Route(
        id="reed_bridge",
        label="reed bridge",
        phrase="a narrow bridge of reeds over the mill stream",
        hazards={"tilt", "drop"},
        severity=2,
        omen="The planks whispered and bowed over the water.",
        crossing="the bridge swayed under quick feet",
        ending="They crossed the whispering bridge without losing a crumb.",
        tags={"bridge", "water"},
    ),
    "moss_steps": Route(
        id="moss_steps",
        label="moss steps",
        phrase="the old mossy steps cut into the hill",
        hazards={"slip", "smush"},
        severity=1,
        omen="Each stone wore a green, sleepy coat of moss.",
        crossing="the moss tried to send careless feet sliding",
        ending="They came down the green steps as careful as a song.",
        tags={"hill", "moss"},
    ),
    "mist_ford": Route(
        id="mist_ford",
        label="misty ford",
        phrase="a shallow ford where cold water lapped at the stones",
        hazards={"wet", "slip"},
        severity=2,
        omen="Mist curled over the water and hid the smaller stones.",
        crossing="the ford splashed at every hurried ankle",
        ending="They stepped through the ford and the gift stayed dry.",
        tags={"ford", "water"},
    ),
}

GIFTS = {
    "seed_cake": Gift(
        id="seed_cake",
        label="seed cake",
        phrase="a round seed cake for the widow at the hill shrine",
        weaknesses={"smush", "wet"},
        tags={"cake", "gift"},
    ),
    "egg_basket": Gift(
        id="egg_basket",
        label="basket of eggs",
        phrase="a willow basket of brown eggs for the baker",
        weaknesses={"tilt", "smush"},
        plural=True,
        tags={"eggs", "gift"},
    ),
    "honey_jar": Gift(
        id="honey_jar",
        label="jar of honey",
        phrase="a bright jar of honey for the winter table",
        weaknesses={"drop", "wet"},
        tags={"honey", "gift"},
    ),
    "berry_tarts": Gift(
        id="berry_tarts",
        label="berry tarts",
        phrase="two little berry tarts for the old ferryman",
        weaknesses={"tilt", "smush"},
        plural=True,
        tags={"tarts", "gift"},
    ),
}

PLANS = {
    "shared_tray": Plan(
        id="shared_tray",
        label="shared tray",
        phrase="a broad ash tray with a handle at each side",
        protects={"tilt", "smush", "drop"},
        power=3,
        prep="set the gift on a broad ash tray and take one handle each",
        carry="one at each handle, with matching steps",
        ending="The tray stayed level between them like a small wooden moon.",
        tags={"tray", "cooperate"},
    ),
    "waxed_cloth": Plan(
        id="waxed_cloth",
        label="waxed cloth",
        phrase="a waxed cloth tied close around the gift",
        protects={"wet", "smush"},
        power=2,
        prep="wrap the gift in waxed cloth and hold it together",
        carry="both hands close together under the waxed cloth",
        ending="The cloth shone with drops, but the gift beneath it stayed safe.",
        tags={"cloth", "cooperate"},
    ),
    "yoke_pole": Plan(
        id="yoke_pole",
        label="yoke pole",
        phrase="a light carrying pole cut from hazel wood",
        protects={"tilt", "drop", "wet"},
        power=3,
        prep="hang the gift from a hazel pole and shoulder it together",
        carry="under a hazel pole, shoulder to shoulder",
        ending="The pole bent a little, yet the gift rode steady as a bell.",
        tags={"pole", "cooperate"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Sela", "Tavi", "Nora", "Ava"]
BOY_NAMES = ["Ivo", "Marek", "Tomas", "Pavel", "Eli", "Jon"]
TRAITS = ["patient", "kind", "steady", "gentle", "proud", "hasty"]
RELATIONS = ["siblings", "cousins"]

KNOWLEDGE = {
    "bridge": [("Why must people walk carefully on a narrow bridge?",
                "A narrow bridge can sway and tip under quick steps. Careful feet help you keep your balance and keep what you carry from falling.")],
    "ford": [("What is a ford?",
              "A ford is a shallow place where people can cross a stream on foot. The stones can be wet and slippery.")],
    "moss": [("Why is moss slippery?",
              "Moss holds water and makes stone feel slick. That is why careful steps matter on mossy places.")],
    "cake": [("Why can a cake smush easily?",
              "A soft cake can flatten if it is squeezed or dropped. Once it is smushed, it does not look the same again.")],
    "eggs": [("Why must eggs be carried gently?",
              "Eggs have thin shells that crack when they are jolted or pressed. A level basket helps keep them safe.")],
    "honey": [("Why is a glass jar easy to break when dropped?",
               "Glass is hard but brittle, so a fall can crack it. Carrying a jar steadily helps keep it whole.")],
    "tray": [("Why does carrying together help with a tray?",
              "Two people can share the weight and keep both sides level. Matching steps make the tray steadier.")],
    "cloth": [("What does waxed cloth do?",
               "Waxed cloth helps keep rain and splashes out. It also holds a soft thing together so it does not get smushed as easily.")],
    "pole": [("Why is a carrying pole useful?",
              "A carrying pole shares weight between two shoulders. That makes a load steadier on a long or tricky path.")],
    "ram": [("Why would a hungry ram chase spilled food?",
             "Animals notice smells and crumbs very quickly. If food drops on the road, a hungry ram may come charging toward it.")],
    "apology": [("What is an apology?",
                 "An apology is when you say you were wrong and try to mend hurt feelings. A true apology helps people trust each other again.")],
}
KNOWLEDGE_ORDER = ["bridge", "ford", "moss", "cake", "eggs", "honey", "tray", "cloth", "pole", "ram", "apology"]


@dataclass
class StoryParams:
    route: str
    gift: str
    plan: str
    leader_name: str
    leader_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    parent: str
    relation: str = "siblings"
    leader_age: int = 7
    helper_age: int = 5
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid, route in ROUTES.items():
        for gid, gift in GIFTS.items():
            for pid, plan in PLANS.items():
                if valid_combo(route, gift, plan):
                    combos.append((rid, gid, pid))
    return combos


def explain_rejection(route: Route, gift: Gift, plan: Plan) -> str:
    risks = risk_tags(route, gift)
    if not risks:
        return (
            f"(No story: {route.label} does not threaten the {gift.label} in a way this world knows. "
            f"The path must put the gift at real risk.)"
        )
    missing = sorted(risks - plan.protects)
    return (
        f"(No story: the {plan.label} does not really protect the {gift.label} on the {route.label}. "
        f"It misses these risks: {', '.join(missing)}.)"
    )


def predict_trouble(world: World, route: Route, gift: Gift) -> dict:
    sim = world.copy()
    dash_and_damage(sim, route, gift, narrate=False)
    return {
        "damaged": sim.get("gift").meters["damaged"] >= THRESHOLD,
        "pursuit": sim.get("destructor").meters["pursuit"] >= THRESHOLD,
    }


def introduce(world: World, leader: Entity, helper: Entity, parent: Entity, gift: Gift, route: Route) -> None:
    world.say(
        f"In a valley of mills and willow smoke, {leader.id} and {helper.id} lived in one small house with their {parent.label_word}."
    )
    world.say(
        f"One pale morning, their {parent.label_word} placed {gift.phrase} in their care and pointed toward {route.phrase}."
    )


def charge_with_gift(world: World, parent: Entity, leader: Entity, helper: Entity, route: Route, gift: Gift) -> None:
    world.say(
        f'"Take it together," their {parent.label_word} said. "The road by {route.label} has a sly trick in it."'
    )
    world.say(route.omen)


def quarrel(world: World, leader: Entity, helper: Entity, gift: Gift) -> None:
    leader.memes["pride"] += 1
    helper.memes["pride"] += 1
    leader.memes["trust"] += 2
    helper.memes["trust"] += 2
    world.say(
        f'But before they had gone ten steps, {leader.id} said, "I should carry the {gift.label} in front. I know the road best."'
    )
    world.say(
        f'"And I have the steadier hands," said {helper.id}. Each reached for the better place, and their steps fell out of time.'
    )


def whisper_about_destructor(world: World) -> None:
    world.say(
        'From beyond the hedges came a hard clack of horns on wood. Someone in the lane whispered, "Destructor is loose again."'
    )
    world.say(
        'That was the village name for the black ram who loved dropped food and bad manners in equal measure.'
    )


def warning(world: World, leader: Entity, helper: Entity, route: Route, gift: Gift) -> None:
    pred = predict_trouble(world, route, gift)
    helper.memes["caution"] += 1
    world.facts["predicted_damage"] = pred["damaged"]
    world.facts["predicted_pursuit"] = pred["pursuit"]
    extra = " and Destructor will hear the mess before we do" if pred["pursuit"] else ""
    world.say(
        f'{helper.id} lowered {helper.pronoun("possessive")} voice. "Do not dash like this. On {route.label}, the {gift.label} will smush{extra}."'
    )


def back_down(world: World, leader: Entity, helper: Entity, plan: Plan) -> None:
    leader.memes["apology"] += 1
    helper.memes["trust"] += 1
    leader.memes["trust"] += 1
    world.say(
        f'{leader.id} looked at the crooked gift between them and let out a small breath. "You are right," {leader.pronoun()} said. "I was pulling against you."'
    )
    world.say(
        f'"Then let us mend it before the road grows mean," said {helper.id}. They chose {plan.phrase}.'
    )


def prepare_plan(world: World, leader: Entity, helper: Entity, plan: Plan) -> None:
    world.say(
        f'Together they {plan.prep}, and soon they moved {plan.carry}.'
    )


def safe_crossing(world: World, route: Route, gift: Gift, plan: Plan) -> None:
    world.say(
        f"{route.crossing}, but the {gift.label} did not tilt or tear. {plan.ending}"
    )
    world.say(route.ending)


def dash_and_damage(world: World, route: Route, gift: Gift, narrate: bool = True) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    gift_ent = world.get("gift")
    leader.memes["defiance"] += 1
    leader.memes["fear"] += 1
    helper.memes["fear"] += 1
    risks = risk_tags(route, gift)
    if risks:
        gift_ent.meters["damaged"] += 1
        for tag in risks:
            gift_ent.meters[tag] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f'"Then follow if you trust me!" cried {leader.id}, and made a dash for {route.label}.'
        )
        world.say(
            f'{route.crossing}. The {gift.label} gave a soft, sorry sound, and {helper.id} gasped, "It will smush!"'
        )


def destructor_appears(world: World) -> None:
    beast = world.get("destructor")
    if beast.meters["pursuit"] >= THRESHOLD:
        world.say(
            'Behind them came the thunder of hooves. Out of the lane burst Destructor, horned head low and hungry nose lifted to the crumbs.'
        )


def reconcile_in_chase(world: World, leader: Entity, helper: Entity, plan: Plan) -> None:
    leader.memes["apology"] += 1
    helper.memes["apology"] += 1
    leader.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'{leader.id} stopped short. "No more pulling apart," {leader.pronoun()} said. "Forgive me, and take the other side."'
    )
    world.say(
        f'"I forgive you," said {helper.id}. "But speak with your feet as kindly as your mouth." In one breath they turned to {plan.prep}.'
    )


def save_gift(world: World, route: Route, gift: Gift, plan: Plan) -> None:
    gift_ent = world.get("gift")
    beast = world.get("destructor")
    beast.meters["pursuit"] = 0.0
    gift_ent.meters["safe"] += 1
    world.say(
        f'They held fast {plan.carry}, and the old ram found no loose feast to seize. Snorting once, Destructor swerved into the weeds.'
    )
    world.say(
        f'By the time they reached the far side, the {gift.label} was rumpled but whole. {route.ending}'
    )


def lose_gift(world: World, gift: Gift) -> None:
    beast = world.get("destructor")
    gift_ent = world.get("gift")
    beast.meters["fed"] += 1
    gift_ent.meters["lost"] += 1
    world.say(
        f'They tried to gather the {gift.label} together, but they had quarreled a breath too long. Destructor struck the road between them, and the gift was gone in one wild smush of hooves and crumbs.'
    )


def ending_reconciliation(world: World, leader: Entity, helper: Entity, parent: Entity, gift: Gift, saved: bool) -> None:
    leader.memes["relief"] += 1
    helper.memes["relief"] += 1
    if saved:
        world.say(
            f'When they reached home, their {parent.label_word} saw the two children walking in one rhythm and smiled before a word was spoken.'
        )
        world.say(
            f'From that day on, when one was tempted to dash ahead, the other only had to say, "Remember Destructor," and both would laugh and walk together.'
        )
    else:
        world.say(
            f'When they reached home empty-handed, their {parent.label_word} listened to the whole tale and said, "A lost gift is lighter to bear than a hard heart."'
        )
        world.say(
            f'So {leader.id} and {helper.id} went the next week with another humble offering, this time side by side, for reconciliation was the truer gift than the first one had been.'
        )


def tell(
    route: Route,
    gift: Gift,
    plan: Plan,
    leader_name: str,
    leader_gender: str,
    helper_name: str,
    helper_gender: str,
    helper_trait: str,
    parent_type: str,
    relation: str,
    leader_age: int,
    helper_age: int,
    delay: int,
) -> World:
    world = World()
    leader = world.add(Entity(id="leader", kind="character", type=leader_gender, label=leader_name, role="leader", age=leader_age))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper", age=helper_age, attrs={"trait": helper_trait}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    gift_ent = world.add(Entity(id="gift", kind="thing", type="gift", label=gift.label, phrase=gift.phrase, owner="parent"))
    destructor = world.add(Entity(id="destructor", kind="thing", type="ram", label="Destructor", tags={"ram"}))

    introduce(world, leader, helper, parent, gift, route)
    charge_with_gift(world, parent, leader, helper, route, gift)

    world.para()
    quarrel(world, leader, helper, gift)
    whisper_about_destructor(world)
    warning(world, leader, helper, route, gift)

    early = is_early_reconcile(relation, leader_age, helper_age, helper_trait)
    if early:
        world.para()
        back_down(world, leader, helper, plan)
        prepare_plan(world, leader, helper, plan)
        safe_crossing(world, route, gift, plan)
        saved = True
        outcome = "early_reconcile"
    else:
        world.para()
        dash_and_damage(world, route, gift, narrate=True)
        destructor_appears(world)
        world.para()
        reconcile_in_chase(world, leader, helper, plan)
        prepare_plan(world, leader, helper, plan)
        saved = can_save(plan, route, delay)
        if saved:
            save_gift(world, route, gift, plan)
            outcome = "saved_after_chase"
        else:
            lose_gift(world, gift)
            outcome = "lost_after_chase"

    world.para()
    ending_reconciliation(world, leader, helper, parent, gift, saved)
    world.facts.update(
        route=route,
        gift_cfg=gift,
        plan=plan,
        leader=leader,
        helper=helper,
        parent=parent,
        gift=gift_ent,
        destructor=destructor,
        relation=relation,
        delay=delay,
        outcome=outcome,
        saved=saved,
        early=early,
    )
    return world


def pair_noun(leader: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and helper.type == "boy":
            return "two brothers"
        if leader.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two cousins"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route = f["route"]
    gift = f["gift_cfg"]
    leader = f["leader"]
    helper = f["helper"]
    outcome = f["outcome"]
    base = (
        f'Write a short folk tale for a young child that includes the words "smush", "dash", and "Destructor". '
        f'It should involve {pair_noun(leader, helper, f["relation"])} carrying a {gift.label} across {route.label}.'
    )
    if outcome == "early_reconcile":
        return [
            base,
            f"Tell a suspenseful but gentle folk tale where {helper.label} warns {leader.label} not to dash, and the children reconcile before any harm is done.",
            f"Write a dialogue-rich tale in which children mend a quarrel, carry a gift together, and outwit a beast called Destructor simply by acting in time.",
        ]
    if outcome == "saved_after_chase":
        return [
            base,
            f"Tell a folk tale where pride leads to a dangerous dash, the gift is nearly ruined, and reconciliation in the middle of the suspense saves the day.",
            f"Write a story with dialogue, suspense, and a warm ending where Destructor chases spilled crumbs but the children work together in time.",
        ]
    return [
        base,
        f"Tell a cautionary folk tale where the children quarrel too long, Destructor wins the gift, but reconciliation still heals the children at the end.",
        f"Write a sad-but-gentle village tale about pride, apology, and learning to carry burdens together after a gift is lost.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    parent = f["parent"]
    route = f["route"]
    gift = f["gift_cfg"]
    plan = f["plan"]
    relation = f["relation"]
    pair = pair_noun(leader, helper, relation)
    out: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {pair}, {leader.label} and {helper.label}. Their {parent.label_word} trusted them with {gift.phrase}, and that trust starts the tale."),
        ("What problem began their trouble?",
         f"They quarreled over who should lead and nearly stopped listening to each other. That made the risky road more dangerous than it needed to be."),
        (f"Why was {route.label} a dangerous place for the {gift.label}?",
         f"The {route.label} carried the risk of {', '.join(sorted(risk_tags(route, gift)))} for the {gift.label}. If they hurried or pulled against each other there, the gift could be spoiled."),
    ]
    if f["early"]:
        out.append((
            f"How did {helper.label} stop the trouble before it began?",
            f"{helper.label} warned that a dash on {route.label} would make the {gift.label} smush and might bring Destructor running. Because {leader.label} listened in time, they could change course before anything was lost."
        ))
        out.append((
            "How did the children reconcile?",
            f"{leader.label} admitted fault, and {helper.label} answered with help instead of anger. Then they used {plan.phrase} and walked in one rhythm, which proved their peace was real."
        ))
    elif f["saved"]:
        out.append((
            "What happened when one child made a dash?",
            f"The hurried crossing damaged the {gift.label} and dropped crumbs on the road. That is what brought Destructor charging after them and turned the quarrel into real suspense."
        ))
        out.append((
            "How was the gift saved?",
            f"They apologized, forgave each other, and used {plan.phrase}. Working together gave them enough steadiness to keep the rest of the gift away from Destructor."
        ))
    else:
        out.append((
            "Did the children save the gift?",
            f"No. They reconciled, but they had quarreled too long and Destructor reached the spilled food first. The loss became part of the lesson that burdens must be carried together."
        ))
        out.append((
            "Was the ending still about reconciliation?",
            f"Yes. Even though the gift was lost, the children repaired their friendship and told the truth at home. The tale ends by showing that a mended heart matters more than pride."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["route"].tags) | set(f["gift_cfg"].tags) | set(f["plan"].tags) | {"ram", "apology"}
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label and e.label != e.id:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(R, G, T) :- route(R), gift(G), hazard(R, T), weak(G, T).
has_risk(R, G) :- risk(R, G, _).
valid(R, G, P) :- route(R), gift(G), plan(P), has_risk(R, G),
                  not missing_cover(R, G, P).
missing_cover(R, G, P) :- risk(R, G, T), not protects(P, T).

gentle(T) :- trait(T), gentle_trait(T).
older_helper :- relation(siblings), helper_age(HA), leader_age(LA), HA > LA.
early_reconcile :- gentle(T), older_helper.

severity(S + D) :- chosen_route(R), route_severity(R, S), delay(D).
strong_enough :- chosen_plan(P), plan_power(P, Pow), severity(V), Pow >= V.

outcome(early_reconcile) :- early_reconcile.
outcome(saved_after_chase) :- not early_reconcile, strong_enough.
outcome(lost_after_chase) :- not early_reconcile, not strong_enough.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_severity", rid, route.severity))
        for h in sorted(route.hazards):
            lines.append(asp.fact("hazard", rid, h))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for w in sorted(gift.weaknesses):
            lines.append(asp.fact("weak", gid, w))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("plan_power", pid, plan.power))
        for t in sorted(plan.protects):
            lines.append(asp.fact("protects", pid, t))
    for trait in sorted(GENTLE_TRAITS):
        lines.append(asp.fact("gentle_trait", trait))
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
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_plan", params.plan),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("leader_age", params.leader_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.helper_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if is_early_reconcile(params.relation, params.leader_age, params.helper_age, params.helper_trait):
        return "early_reconcile"
    return "saved_after_chase" if can_save(PLANS[params.plan], ROUTES[params.route], params.delay) else "lost_after_chase"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated empty story.)")


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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        route="mist_ford",
        gift="seed_cake",
        plan="waxed_cloth",
        leader_name="Lina",
        leader_gender="girl",
        helper_name="Ivo",
        helper_gender="boy",
        helper_trait="patient",
        parent="mother",
        relation="siblings",
        leader_age=5,
        helper_age=7,
        delay=0,
    ),
    StoryParams(
        route="reed_bridge",
        gift="egg_basket",
        plan="shared_tray",
        leader_name="Marek",
        leader_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        helper_trait="proud",
        parent="father",
        relation="cousins",
        leader_age=7,
        helper_age=7,
        delay=0,
    ),
    StoryParams(
        route="moss_steps",
        gift="berry_tarts",
        plan="shared_tray",
        leader_name="Sela",
        leader_gender="girl",
        helper_name="Jon",
        helper_gender="boy",
        helper_trait="hasty",
        parent="mother",
        relation="siblings",
        leader_age=7,
        helper_age=5,
        delay=2,
    ),
    StoryParams(
        route="reed_bridge",
        gift="honey_jar",
        plan="yoke_pole",
        leader_name="Tomas",
        leader_gender="boy",
        helper_name="Mira",
        helper_gender="girl",
        helper_trait="steady",
        parent="father",
        relation="siblings",
        leader_age=4,
        helper_age=6,
        delay=0,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: two children, a fragile gift, a risky road, and the ram called Destructor."
    )
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--gift", choices=sorted(GIFTS))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=sorted(RELATIONS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the quarrel lasts once trouble begins")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.gift and args.plan:
        route = ROUTES[args.route]
        gift = GIFTS[args.gift]
        plan = PLANS[args.plan]
        if not valid_combo(route, gift, plan):
            raise StoryError(explain_rejection(route, gift, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.gift is None or combo[1] == args.gift)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, gift_id, plan_id = rng.choice(sorted(combos))
    leader_name, leader_gender = pick_child(rng)
    helper_name, helper_gender = pick_child(rng, avoid=leader_name)
    helper_trait = rng.choice(TRAITS)
    relation = args.relation or rng.choice(RELATIONS)
    ages = rng.sample([4, 5, 6, 7, 8], 2)
    leader_age, helper_age = ages[0], ages[1]
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        route=route_id,
        gift=gift_id,
        plan=plan_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        parent=parent,
        relation=relation,
        leader_age=leader_age,
        helper_age=helper_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")

    route = ROUTES[params.route]
    gift = GIFTS[params.gift]
    plan = PLANS[params.plan]
    if not valid_combo(route, gift, plan):
        raise StoryError(explain_rejection(route, gift, plan))

    world = tell(
        route=route,
        gift=gift,
        plan=plan,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        parent_type=params.parent,
        relation=params.relation,
        leader_age=params.leader_age,
        helper_age=params.helper_age,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render().replace("leader", params.leader_name).replace("helper", params.helper_name),
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
        print(f"{len(combos)} compatible (route, gift, plan) combos:\n")
        for route, gift, plan in combos:
            print(f"  {route:11} {gift:11} {plan}")
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
            header = f"### {p.leader_name} & {p.helper_name}: {p.gift} over {p.route} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
