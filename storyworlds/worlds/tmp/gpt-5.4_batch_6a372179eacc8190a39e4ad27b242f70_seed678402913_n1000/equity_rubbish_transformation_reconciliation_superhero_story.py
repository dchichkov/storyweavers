#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/equity_rubbish_transformation_reconciliation_superhero_story.py
================================================================================================

A standalone storyworld about two children who pretend to be superheroes, face a
small fairness problem around cleaning up rubbish, learn the difference between
"equal" and "equity", transform the cleanup into a heroic mission, and reconcile.

The core world logic is intentionally small and classical:

- typed entities with physical meters and emotional memes
- a forward-chaining causal layer for dirt, burden, and reconciliation
- an explicit reasonableness gate over cleanup plans
- a state-driven renderer and QA sets grounded in simulated facts
- an inline ASP twin for the compatibility gate

Run it
------
    python storyworlds/worlds/gpt-5.4/equity_rubbish_transformation_reconciliation_superhero_story.py
    python storyworlds/worlds/gpt-5.4/equity_rubbish_transformation_reconciliation_superhero_story.py --place courtyard --rubbish wrappers --plan cart_sort
    python storyworlds/worlds/gpt-5.4/equity_rubbish_transformation_reconciliation_superhero_story.py --rubbish peels --plan hand_scoop
    python storyworlds/worlds/gpt-5.4/equity_rubbish_transformation_reconciliation_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/equity_rubbish_transformation_reconciliation_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/equity_rubbish_transformation_reconciliation_superhero_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher", "aunt": "aunt"}.get(
            self.type, self.type
        )


@dataclass
class Place:
    id: str
    label: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RubbishKind:
    id: str
    label: str
    phrase: str
    plural_label: str
    count: int
    tricky: int
    danger_word: str
    cleanup_verb: str
    after_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    gear_text: str = ""
    action_text: str = ""
    apology_text: str = ""
    equity_text: str = ""
    tags: set[str] = field(default_factory=set)


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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dirty_place(world: World) -> list[str]:
    place = world.get("place")
    rubbish = world.get("rubbish")
    if rubbish.meters["ground_pieces"] < THRESHOLD:
        return []
    sig = ("dirty_place",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["dirty"] += 1
    return []


def _r_unfair_burden(world: World) -> list[str]:
    burdened = world.get("burdened")
    if burdened.meters["load"] < 2:
        return []
    sig = ("unfair_burden", burdened.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    burdened.memes["hurt"] += 1
    burdened.memes["resentment"] += 1
    return []


def _r_shared_help(world: World) -> list[str]:
    leader = world.get("leader")
    partner = world.get("partner")
    if leader.meters["shared_work"] < THRESHOLD or partner.meters["shared_work"] < THRESHOLD:
        return []
    sig = ("shared_help",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    leader.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    leader.memes["hurt"] = 0.0
    partner.memes["hurt"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="dirty_place", tag="physical", apply=_r_dirty_place),
    Rule(name="unfair_burden", tag="social", apply=_r_unfair_burden),
    Rule(name="shared_help", tag="social", apply=_r_shared_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def handles_rubbish(plan: Plan, rubbish: RubbishKind) -> bool:
    return rubbish.id in plan.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for rubbish_id, rubbish in RUBBISH.items():
            for plan_id, plan in PLANS.items():
                if handles_rubbish(plan, rubbish):
                    combos.append((place_id, rubbish_id, plan_id))
    return combos


def explain_rejection(plan: Plan, rubbish: RubbishKind) -> str:
    return (
        f"(No story: {plan.label} is not a sensible way to clean up {rubbish.plural_label}. "
        f"Pick a plan that really handles that kind of rubbish.)"
    )


def predict_hurt(world: World) -> bool:
    sim = world.copy()
    burdened = sim.get("burdened")
    burdened.meters["load"] += 2
    propagate(sim, narrate=False)
    return burdened.memes["hurt"] >= THRESHOLD


def introduce(world: World, leader: Entity, partner: Entity, place: Place) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
        kid.memes["imagination"] += 1
    world.say(
        f"After school, {leader.id} and {partner.id} raced to {place.label} with towels tied around "
        f"their shoulders like capes. In their game, {place.opening} was the roof of a secret hero city."
    )
    world.say(
        f'"Captain Comet!" {leader.id} shouted. "{partner.id}, today we save the neighborhood!"'
    )


def make_mess(world: World, leader: Entity, partner: Entity, rubbish: RubbishKind) -> None:
    rubbish_ent = world.get("rubbish")
    rubbish_ent.meters["ground_pieces"] = float(rubbish.count)
    rubbish_ent.meters["tricky"] = float(rubbish.tricky)
    propagate(world, narrate=False)
    world.say(
        f"But by the bench and the path, {rubbish.phrase} had blown together into a little storm of "
        f"rubbish. It did not look like a hero city at all."
    )
    world.say(
        f'{partner.id} stopped short. "Oh. Somebody should clean that up before anyone {rubbish.danger_word}," '
        f"{partner.pronoun()} said."
    )


def unfair_assignment(world: World, leader: Entity, burdened: Entity, rubbish: RubbishKind) -> None:
    burdened.meters["load"] += 2
    leader.meters["load"] += 1
    world.facts["initial_unfair_speaker"] = leader.id
    world.facts["burdened_name"] = burdened.id
    propagate(world, narrate=False)
    world.say(
        f'{leader.id} pointed at the biggest drift of {rubbish.plural_label}. '
        f'"You pick up that whole side, and I\'ll just get the easy pieces," {leader.pronoun()} said.'
    )
    if burdened.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{burdened.id}'s shoulders drooped. That did not feel fair at all, because the harder part "
            f"had been dropped into {burdened.pronoun('possessive')} hands."
        )


def mentor_steps_in(world: World, mentor: Entity, leader: Entity, burdened: Entity, rubbish: RubbishKind) -> None:
    hurt_pred = predict_hurt(world)
    world.facts["predicted_hurt"] = hurt_pred
    mentor.memes["care"] += 1
    world.say(
        f"{mentor.label_word.capitalize()} came over with a calm voice and looked at the windy pile of "
        f"{rubbish.plural_label}."
    )
    world.say(
        f'"Heroes do not just split work the same way," {mentor.pronoun()} said. '
        f'"They think about equity. Equity means each person gets the help they need so the job is truly fair."'
    )


def transform_team(
    world: World,
    mentor: Entity,
    leader: Entity,
    partner: Entity,
    burdened: Entity,
    plan: Plan,
) -> None:
    leader.attrs["hero_name"] = "Captain Comet"
    partner.attrs["hero_name"] = "Bright Bolt"
    world.facts["team_name"] = "The Equity Squad"
    world.say(
        f'Then {mentor.pronoun()} clapped once and grinned. "New mission for {world.facts["team_name"]}!"'
    )
    world.say(
        f"{plan.gear_text} In one small breath, the plain cleanup changed into a rescue mission with "
        f"jobs that fit each hero."
    )
    world.say(plan.equity_text)
    leader.memes["wonder"] += 1
    partner.memes["wonder"] += 1
    burdened.memes["hope"] += 1


def do_cleanup(
    world: World,
    leader: Entity,
    partner: Entity,
    burdened: Entity,
    mentor: Entity,
    plan: Plan,
    rubbish: RubbishKind,
    place: Place,
) -> None:
    leader.meters["shared_work"] += 1
    partner.meters["shared_work"] += 1
    leader.meters["load"] = 1
    partner.meters["load"] = 1
    world.get("rubbish").meters["ground_pieces"] = 0.0
    world.get("place").meters["dirty"] = 0.0
    propagate(world, narrate=False)
    world.say(plan.action_text)
    world.say(
        f"Soon the last of the {rubbish.plural_label} was gone. {place.ending} looked "
        f"{rubbish.after_image}, as if the heroes had polished it with light."
    )
    leader.memes["remorse"] += 1
    leader.memes["care"] += 1
    burdened.memes["relief"] += 1
    mentor.memes["pride"] += 1


def reconcile(world: World, leader: Entity, burdened: Entity, plan: Plan) -> None:
    burdened.memes["trust"] += 1
    leader.memes["trust"] += 1
    leader.memes["friendship"] += 1
    burdened.memes["friendship"] += 1
    world.say(
        f'{leader.id} looked at {burdened.id} and spoke more softly. "{plan.apology_text}"'
    )
    world.say(
        f'{burdened.id} smiled and bumped {leader.id}\'s shoulder with {burdened.pronoun("possessive")} cape. '
        f'"It is better when we save things together," {burdened.pronoun()} said.'
    )
    world.say(
        f"They raised their hands over the clean ground and shouted, "
        f'"{world.facts["team_name"]}!"'
    )


def closing(world: World, leader: Entity, partner: Entity, mentor: Entity, place: Place) -> None:
    world.say(
        f"As the sun slid lower, a breeze lifted the two capes and made them flutter for real. "
        f"{mentor.label_word.capitalize()} watched the friends grin at each other, and {place.label} no longer "
        f"looked like a problem. It looked like a headquarters worth protecting."
    )
    world.facts["reconciled"] = True


def tell(
    place: Place,
    rubbish: RubbishKind,
    plan: Plan,
    leader_name: str = "Nova",
    leader_type: str = "girl",
    partner_name: str = "Jax",
    partner_type: str = "boy",
    mentor_type: str = "teacher",
) -> World:
    world = World()
    leader = world.add(Entity(id="leader", kind="character", type=leader_type, label=leader_name, role="leader"))
    partner = world.add(
        Entity(id="partner", kind="character", type=partner_type, label=partner_name, role="partner")
    )
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, label="the mentor", role="mentor"))
    burdened = partner
    world.add(Entity(id="burdened", kind="character", type=partner_type, label=partner_name, role="burdened"))
    world.entities["burdened"] = burdened
    place_ent = world.add(Entity(id="place", type="place", label=place.label, phrase=place.label, tags=set(place.tags)))
    rubbish_ent = world.add(
        Entity(id="rubbish", type="rubbish", label=rubbish.label, phrase=rubbish.phrase, tags=set(rubbish.tags))
    )

    introduce(world, leader, partner, place)
    world.para()
    make_mess(world, leader, partner, rubbish)
    unfair_assignment(world, leader, burdened, rubbish)
    world.para()
    mentor_steps_in(world, mentor, leader, burdened, rubbish)
    transform_team(world, mentor, leader, partner, burdened, plan)
    world.para()
    do_cleanup(world, leader, partner, burdened, mentor, plan, rubbish, place)
    reconcile(world, leader, burdened, plan)
    world.para()
    closing(world, leader, partner, mentor, place)

    world.facts.update(
        place_cfg=place,
        rubbish_cfg=rubbish,
        plan_cfg=plan,
        leader=leader,
        partner=partner,
        mentor=mentor,
        burdened=burdened,
        place=place_ent,
        rubbish=rubbish_ent,
        transformed=True,
        cleaned=place_ent.meters["dirty"] < THRESHOLD and rubbish_ent.meters["ground_pieces"] < THRESHOLD,
    )
    return world


PLACES = {
    "courtyard": Place(
        id="courtyard",
        label="the apartment courtyard",
        opening="the apartment courtyard",
        ending="The paving stones and flower pots",
        tags={"outside", "community"},
    ),
    "playground": Place(
        id="playground",
        label="the playground",
        opening="the playground",
        ending="The slide, bench, and climbing bars",
        tags={"outside", "community"},
    ),
    "hallway": Place(
        id="hallway",
        label="the school hallway",
        opening="the school hallway",
        ending="The bright floor and cubby wall",
        tags={"school", "community"},
    ),
}

RUBBISH = {
    "wrappers": RubbishKind(
        id="wrappers",
        label="wrapper",
        phrase="crinkly snack wrappers",
        plural_label="wrappers",
        count=7,
        tricky=1,
        danger_word="trip",
        cleanup_verb="scooped",
        after_image="bright and open again",
        tags={"rubbish", "recycling", "paper"},
    ),
    "caps": RubbishKind(
        id="caps",
        label="bottle cap",
        phrase="little bottle caps and shiny tabs",
        plural_label="bottle caps",
        count=8,
        tricky=2,
        danger_word="step on something sharp",
        cleanup_verb="grabbed",
        after_image="neat and safe again",
        tags={"rubbish", "recycling", "metal"},
    ),
    "peels": RubbishKind(
        id="peels",
        label="peel",
        phrase="sticky banana peels and soft napkins",
        plural_label="peels",
        count=5,
        tricky=2,
        danger_word="slip",
        cleanup_verb="lifted",
        after_image="fresh and clear again",
        tags={"rubbish", "compost", "slippery"},
    ),
}

PLANS = {
    "cart_sort": Plan(
        id="cart_sort",
        label="a rolling recycling cart and sorter trays",
        handles={"wrappers", "caps"},
        gear_text="Teacher rolled over a small recycling cart and set out two sorter trays",
        action_text="Captain Comet pushed the cart while Bright Bolt sorted the pieces into the right trays, and together they swept the rest in before the wind could steal them back.",
        apology_text="I was acting like the boss instead of a teammate. I am sorry. Next time I will make the hard part lighter, not heavier.",
        equity_text="The cart took the heavy part, and the trays made the tiny pieces easier to sort, so nobody got stuck with all the hardest work.",
        tags={"recycling", "equity"},
    ),
    "grabber_team": Plan(
        id="grabber_team",
        label="long grabbers and a bright bucket",
        handles={"caps", "wrappers"},
        gear_text="Teacher handed them long grabbers and clipped a bright bucket between them",
        action_text="The two heroes clicked their grabbers like secret tools and plucked the rubbish from the ground, one catching the tiny pieces while the other steadied the bucket.",
        apology_text="I should not have left you with the trickiest side. I am sorry. We are stronger when we share the hard parts too.",
        equity_text="The grabbers helped with the hardest pieces, and sharing one bucket made the job feel like one mission instead of two lonely chores.",
        tags={"tool", "equity"},
    ),
    "glove_compost": Plan(
        id="glove_compost",
        label="garden gloves and a compost tub",
        handles={"peels"},
        gear_text="Teacher brought garden gloves and a little compost tub with a lid",
        action_text="One hero held the tub steady while the other lifted the slippery peels with gloved hands, and then they switched jobs so each one carried only part of the messy work.",
        apology_text="I was not thinking about how hard your side was. I am sorry. Thank you for helping me make it fair.",
        equity_text="The gloves protected the sticky part, and switching jobs halfway meant each child got support with the messiest work.",
        tags={"compost", "equity"},
    ),
    "hand_scoop": Plan(
        id="hand_scoop",
        label="bare hands and a tiny paper cup",
        handles={"wrappers"},
        gear_text="Teacher found only a tiny paper cup",
        action_text="They pinched up the light wrappers one by one and tucked them into the cup.",
        apology_text="I am sorry for making it feel unfair. Next time I will ask what help you need.",
        equity_text="Because the wrappers were light and dry, even a tiny cup was enough when they worked side by side.",
        tags={"simple", "equity"},
    ),
}


@dataclass
class StoryParams:
    place: str
    rubbish: str
    plan: str
    leader_name: str
    leader_type: str
    partner_name: str
    partner_type: str
    mentor_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="playground",
        rubbish="wrappers",
        plan="cart_sort",
        leader_name="Nova",
        leader_type="girl",
        partner_name="Jax",
        partner_type="boy",
        mentor_type="teacher",
    ),
    StoryParams(
        place="courtyard",
        rubbish="caps",
        plan="grabber_team",
        leader_name="Milo",
        leader_type="boy",
        partner_name="Asha",
        partner_type="girl",
        mentor_type="aunt",
    ),
    StoryParams(
        place="hallway",
        rubbish="peels",
        plan="glove_compost",
        leader_name="Lena",
        leader_type="girl",
        partner_name="Owen",
        partner_type="boy",
        mentor_type="teacher",
    ),
    StoryParams(
        place="playground",
        rubbish="wrappers",
        plan="hand_scoop",
        leader_name="Rae",
        leader_type="girl",
        partner_name="Ben",
        partner_type="boy",
        mentor_type="father",
    ),
]


KNOWLEDGE = {
    "equity": [
        (
            "What does equity mean?",
            "Equity means giving people the help they need so things can be truly fair. It is not always the same as giving everyone exactly the same thing."
        )
    ],
    "rubbish": [
        (
            "What is rubbish?",
            "Rubbish is trash or litter that has been left where it should not be. It can make a place messy or unsafe until someone cleans it up."
        )
    ],
    "recycling": [
        (
            "Why do people sort recycling?",
            "People sort recycling so paper, metal, and other useful materials can be used again. That keeps rubbish out of the ground and helps the community stay cleaner."
        )
    ],
    "compost": [
        (
            "What is compost?",
            "Compost is a place for old fruit peels and other food scraps to break down into rich soil. It turns some kinds of rubbish into something useful for plants."
        )
    ],
    "superhero": [
        (
            "Do superheroes always need powers to help?",
            "No. A superhero can be someone who notices a problem, helps others, and acts bravely and kindly. Real helping can be heroic even without flying."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    rubbish = f["rubbish_cfg"]
    leader = f["leader"]
    partner = f["partner"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "equity" and "{rubbish.label if rubbish.label != "wrapper" else "rubbish"}".',
        f"Tell a gentle story where {leader.label} and {partner.label} see {rubbish.phrase} at {place.label}, argue about cleanup, and learn that equity can make teamwork fair.",
        "Write a short story with transformation and reconciliation, where pretend heroes turn a cleanup problem into a shared mission and end as friends again.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    mentor = f["mentor"]
    place = f["place_cfg"]
    rubbish = f["rubbish_cfg"]
    plan = f["plan_cfg"]
    burdened = f["burdened"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.label} and {partner.label}, two children pretending to be superheroes, and {mentor.label_word} who helps them think more fairly."
        ),
        (
            f"What problem did they find at {place.label}?",
            f"They found {rubbish.phrase} blowing around and making the place look messy and unsafe. The rubbish turned their pretend hero city into a problem that needed real help."
        ),
        (
            f"Why did {burdened.label} feel hurt?",
            f"{leader.label} tried to leave the hardest side of the cleanup to {burdened.label}. That felt unfair because {burdened.label} was being given more of the difficult rubbish instead of equal support."
        ),
        (
            "What did the mentor say equity meant?",
            f"{mentor.label_word.capitalize()} said equity means giving each person the help they need so the job is truly fair. In the story, that meant changing the tools and the jobs instead of pretending the hard side and easy side were the same."
        ),
        (
            "How did the story use transformation?",
            f"The cleanup changed from an unhappy chore into a superhero mission for The Equity Squad. The new gear and new jobs made the children feel like helpers again, not opponents."
        ),
        (
            "How did they reconcile?",
            f"{leader.label} apologized for making the work unfair, and {burdened.label} accepted the apology. They finished the cleanup together, which turned the hurt feeling into teamwork again."
        ),
        (
            "How did the story end?",
            f"It ended with {place.label} clean again and the two friends raising their hands like a real team. The clean ground showed that both the place and the friendship had been repaired."
        ),
    ]
    if plan.id == "glove_compost":
        items.append(
            (
                "Why were gloves important in this story?",
                "The gloves helped with the sticky, slippery peels. They made the mess safer to handle, which is part of why the work could be shared fairly."
            )
        )
    elif plan.id in {"cart_sort", "grabber_team"}:
        items.append(
            (
                "Why did the tools matter?",
                f"The tools matched the rubbish they had to clean. That mattered because fair teamwork is easier when the hardest part of the job gets real help."
            )
        )
    return items


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"equity", "rubbish", "superhero"} | set(f["rubbish_cfg"].tags) | set(f["plan_cfg"].tags)
    out: list[tuple[str, str]] = []
    if "equity" in tags:
        out.extend(KNOWLEDGE["equity"])
    if "rubbish" in tags:
        out.extend(KNOWLEDGE["rubbish"])
    if "recycling" in tags:
        out.extend(KNOWLEDGE["recycling"])
    if "compost" in tags:
        out.extend(KNOWLEDGE["compost"])
    if "superhero" in tags or "equity" in tags:
        out.extend(KNOWLEDGE["superhero"])
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
        if ent.label and ent.label != ent.id:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
handles_plan(P, R) :- handles(P, R).
valid(Place, R, P) :- place(Place), rubbish(R), plan(P), handles_plan(P, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for rubbish_id in RUBBISH:
        lines.append(asp.fact("rubbish", rubbish_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        for rid in sorted(plan.handles):
            lines.append(asp.fact("handles", plan_id, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero cleanup storyworld: rubbish, equity, transformation, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rubbish", choices=RUBBISH)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--leader-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--leader-type", choices=["girl", "boy"])
    ap.add_argument("--partner-type", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["teacher", "mother", "father", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nova", "Lena", "Asha", "Rae", "Mina", "Zoe", "Kira", "Nia"]
BOY_NAMES = ["Jax", "Milo", "Owen", "Ben", "Theo", "Finn", "Eli", "Noah"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rubbish and args.plan:
        rubbish = RUBBISH[args.rubbish]
        plan = PLANS[args.plan]
        if not handles_rubbish(plan, rubbish):
            raise StoryError(explain_rejection(plan, rubbish))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.rubbish is None or combo[1] == args.rubbish)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, rubbish, plan = rng.choice(sorted(combos))
    leader_type = args.leader_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or rng.choice(["girl", "boy"])
    leader_name = args.leader_name or _pick_name(rng, leader_type)
    partner_name = args.partner_name or _pick_name(rng, partner_type, avoid=leader_name)
    mentor_type = args.mentor or rng.choice(["teacher", "mother", "father", "aunt"])
    return StoryParams(
        place=place,
        rubbish=rubbish,
        plan=plan,
        leader_name=leader_name,
        leader_type=leader_type,
        partner_name=partner_name,
        partner_type=partner_type,
        mentor_type=mentor_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.rubbish not in RUBBISH:
        raise StoryError(f"(Unknown rubbish type: {params.rubbish})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if not handles_rubbish(PLANS[params.plan], RUBBISH[params.rubbish]):
        raise StoryError(explain_rejection(PLANS[params.plan], RUBBISH[params.rubbish]))

    world = tell(
        place=PLACES[params.place],
        rubbish=RUBBISH[params.rubbish],
        plan=PLANS[params.plan],
        leader_name=params.leader_name,
        leader_type=params.leader_type,
        partner_name=params.partner_name,
        partner_type=params.partner_type,
        mentor_type=params.mentor_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "equity" not in sample.story.lower() or "rubbish" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missed a required seed word.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("(Smoke test failed: QA generation was empty.)")
        print("OK: random generation + QA succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, rubbish, plan) combos:\n")
        for place, rubbish, plan in combos:
            print(f"  {place:10} {rubbish:9} {plan}")
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
            header = f"### {p.leader_name} & {p.partner_name}: {p.rubbish} at {p.place} ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
