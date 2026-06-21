#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py
==============================================================

A standalone story world about a child tempted to sneak a special treat before
it is time. The stories are written as gentle comedy with bits of inner
monologue: the child imagines a grand secret mission, chooses a silly plan, and
then learns that asking is easier than balancing like a noodle on wheels.

The world model keeps a few physical meters (wobble, noise, mess, spill) and a
few emotional memes (hunger, mischief, embarrassment, relief, pride). Story
beats read that state back instead of swapping nouns into one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py
    python storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py --treat cream_puff --plan toy_wagon
    python storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py --plan broom
    python storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py --all
    python storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/scallywag_inner_monologue_comedy.py --verify
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
MIN_SAFE_STABILITY = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    texture: str
    filling: str
    crumbly: bool = False
    drippy: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def slip(self) -> int:
        return 1 if (self.crumbly or self.drippy) else 0

    @property
    def mess_word(self) -> str:
        if self.drippy:
            return self.filling
        if self.crumbly:
            return "crumbs"
        return "smears"


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    reason: str
    balance_need: int
    clangs: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    phrase: str
    style: str
    reach: int
    stability: int
    rolling: bool = False
    too_silly: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    treat: str
    perch: str
    plan: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_wobble(world: World) -> list[str]:
    child = world.entities.get("child")
    plan = world.entities.get("plan")
    perch = world.entities.get("perch")
    if not child or not plan or not perch:
        return []
    if child.meters["climbing"] < THRESHOLD:
        return []
    if plan.attrs.get("stability", 0) >= perch.attrs.get("balance_need", 0):
        return []
    sig = ("wobble", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["wobble"] += 1
    plan.meters["wobble"] += 1
    child.memes["alarm"] += 1
    return ["__wobble__"]


def _r_noise(world: World) -> list[str]:
    child = world.entities.get("child")
    plan = world.entities.get("plan")
    perch = world.entities.get("perch")
    room = world.entities.get("room")
    adult = world.entities.get("adult")
    if not child or not plan or not perch or not room or not adult:
        return []
    noisy = False
    if child.meters["wobble"] >= THRESHOLD:
        noisy = True
    if plan.attrs.get("rolling") and child.meters["climbing"] >= THRESHOLD:
        noisy = True
    if perch.attrs.get("clangs") and child.meters["reaching"] >= THRESHOLD:
        noisy = True
    if not noisy:
        return []
    sig = ("noise", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["noise"] += 1
    adult.memes["alert"] += 1
    return ["__noise__"]


def _r_spill(world: World) -> list[str]:
    child = world.entities.get("child")
    treat = world.entities.get("treat")
    floor = world.entities.get("floor")
    if not child or not treat or not floor:
        return []
    if child.meters["holding_treat"] < THRESHOLD:
        return []
    risk = treat.attrs.get("slip", 0)
    if child.meters["wobble"] < THRESHOLD or risk <= 0:
        return []
    sig = ("spill", treat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treat.meters["spilled"] += 1
    floor.meters["messy"] += 1
    child.meters["messy"] += 1
    child.memes["embarrassment"] += 1
    return ["__spill__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
        world.facts.setdefault("markers", []).extend(produced)
    return produced


TREATS = {
    "cream_puff": Treat(
        id="cream_puff",
        label="cream puff",
        phrase="a tall cream puff with a wobble of vanilla cream",
        texture="soft",
        filling="cream",
        drippy=True,
        tags={"bakery", "cream", "dessert"},
    ),
    "jam_tart": Treat(
        id="jam_tart",
        label="jam tart",
        phrase="a shiny jam tart with a red center",
        texture="buttery",
        filling="jam",
        crumbly=True,
        drippy=True,
        tags={"bakery", "jam", "dessert"},
    ),
    "sugar_bun": Treat(
        id="sugar_bun",
        label="sugar bun",
        phrase="a warm sugar bun with a snowy top",
        texture="fluffy",
        filling="sugar",
        crumbly=True,
        tags={"bakery", "crumbs", "dessert"},
    ),
}

PERCHES = {
    "high_shelf": Perch(
        id="high_shelf",
        label="high shelf",
        phrase="the high kitchen shelf",
        reason="to cool where little hands could not nibble first",
        balance_need=2,
        clangs=False,
        tags={"shelf", "kitchen"},
    ),
    "cake_stand": Perch(
        id="cake_stand",
        label="cake stand",
        phrase="the tall cake stand on the counter",
        reason="so the glaze could shine without being bumped",
        balance_need=1,
        clangs=True,
        tags={"counter", "cake_stand"},
    ),
    "window_rack": Perch(
        id="window_rack",
        label="window rack",
        phrase="the wire cooling rack by the sunny window",
        reason="so the tops could set in the breeze",
        balance_need=1,
        clangs=True,
        tags={"window", "rack"},
    ),
}

PLANS = {
    "toy_wagon": Plan(
        id="toy_wagon",
        label="toy wagon",
        phrase="the little red toy wagon",
        style="rolled",
        reach=1,
        stability=1,
        rolling=True,
        tags={"wagon", "wheels"},
    ),
    "spinning_chair": Plan(
        id="spinning_chair",
        label="spinning chair",
        phrase="the spinning desk chair",
        style="swiveled",
        reach=2,
        stability=1,
        rolling=True,
        tags={"chair", "wheels"},
    ),
    "wooden_crate": Plan(
        id="wooden_crate",
        label="wooden crate",
        phrase="the upside-down wooden crate",
        style="thumped",
        reach=1,
        stability=2,
        rolling=False,
        tags={"crate", "steady"},
    ),
    "broom": Plan(
        id="broom",
        label="broom",
        phrase="the long broom",
        style="poked",
        reach=2,
        stability=0,
        rolling=False,
        too_silly=True,
        tags={"broom", "unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["hungry", "curious", "sparky", "dramatic", "cheeky", "eager"]

KNOWLEDGE = {
    "bakery": [
        (
            "Why do baked treats sometimes need to cool first?",
            "Hot treats can be too soft to hold and too hot to eat. Letting them cool helps them keep their shape and keeps mouths safe.",
        )
    ],
    "cream": [
        (
            "Why can cream treats be messy?",
            "Cream is soft and slippery, so it can squish out when you squeeze or wobble it. That is why cream treats need gentle hands.",
        )
    ],
    "jam": [
        (
            "Why does jam make sticky messes?",
            "Jam is sweet and thick, so when it spills it clings to fingers, plates, and floors. Sticky things spread unless you wipe them up.",
        )
    ],
    "crumbs": [
        (
            "Why do buns and tarts leave crumbs?",
            "Crumbs break off from flaky or soft baked food. Little pieces scatter easily when someone nibbles or jostles it.",
        )
    ],
    "wheels": [
        (
            "Why is it hard to stand on something with wheels?",
            "Wheels are made to roll. If you stand on them, the thing under you can move when you do not expect it.",
        )
    ],
    "steady": [
        (
            "What makes a step or platform steady?",
            "A steady platform has a flat top and does not slide or roll away. It stays under your feet while you climb carefully.",
        )
    ],
    "unsafe": [
        (
            "Why should you not poke food down with a broom?",
            "A broom is for sweeping, not for serving food. Poking food with it can knock the food down and make a big mess.",
        )
    ],
    "ask": [
        (
            "What can you do if something tasty is up high?",
            "You can ask a grown-up for help. Asking is safer and usually faster than making a wobbly plan by yourself.",
        )
    ],
    "wait": [
        (
            "Why is waiting for your turn hard?",
            "Waiting can feel hard because your body is excited now. A small job or a game can help the waiting feel shorter.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bakery", "cream", "jam", "crumbs", "wheels", "steady", "unsafe", "ask", "wait"]


def plan_reaches(plan: Plan, perch: Perch) -> bool:
    return plan.reach >= 1


def plan_reasonable(plan: Plan) -> bool:
    return not plan.too_silly and plan.stability >= MIN_SAFE_STABILITY


def valid_combo(treat: Treat, perch: Perch, plan: Plan) -> bool:
    return plan_reaches(plan, perch) and plan_reasonable(plan)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for treat_id, treat in TREATS.items():
        for perch_id, perch in PERCHES.items():
            for plan_id, plan in PLANS.items():
                if valid_combo(treat, perch, plan):
                    out.append((treat_id, perch_id, plan_id))
    return out


def outcome_of(params: StoryParams) -> str:
    treat = TREATS[params.treat]
    perch = PERCHES[params.perch]
    plan = PLANS[params.plan]
    wobble = plan.stability < perch.balance_need
    spill = wobble and treat.slip > 0
    return "spill" if spill else "caught"


def explain_plan_rejection(plan: Plan) -> str:
    if plan.too_silly:
        return (
            f"(No story: using {plan.phrase} to get a treat is too unsafe and absurd for this world. "
            "Pick a platform a child might honestly try, like a toy wagon, spinning chair, or wooden crate.)"
        )
    if plan.stability < MIN_SAFE_STABILITY:
        return (
            f"(No story: {plan.phrase} is too unstable for even a comic near-miss here. "
            "This world allows wobbly plans, not impossible ones.)"
        )
    return "(No story: that plan does not fit this world.)"


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["climbing"] += 1
    child.meters["reaching"] += 1
    propagate(sim, narrate=False)
    child.meters["holding_treat"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": child.meters["wobble"] >= THRESHOLD,
        "spill": sim.get("treat").meters["spilled"] >= THRESHOLD,
        "noise": sim.get("room").meters["noise"] >= THRESHOLD,
    }


def setup_scene(world: World, child: Entity, adult: Entity, treat: Treat, perch: Perch) -> None:
    child.memes["hunger"] += 1
    world.say(
        f"Late in the afternoon, the kitchen smelled like butter and sugar. "
        f"{adult.label_word.capitalize()} had set {treat.phrase} on {perch.phrase}, {perch.reason}."
    )
    world.say(
        f'"These are for after tea," {adult.label_word} said. "{child.id}, wait just a little while."'
    )


def temptation(world: World, child: Entity, treat: Treat) -> None:
    child.memes["mischief"] += 1
    world.say(
        f"{child.id} looked up at the {treat.label} and swallowed. "
        f'Inside {child.pronoun("possessive")} head, a tiny voice whispered, '
        f'"I could be patient."'
    )
    world.say(
        f'Another, much louder voice answered, "Or I could be a scallywag with excellent taste."'
    )


def scheme(world: World, child: Entity, plan: Plan, perch: Perch) -> None:
    pred = predict_attempt(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_noise"] = pred["noise"]
    child.memes["confidence"] += 1
    world.say(
        f"{child.id}'s eyes landed on {plan.phrase}. "
        f'Inside {child.pronoun("possessive")} head, the loud voice announced, '
        f'"Perfect. Operation Treat Rescue begins now."'
    )
    if plan.rolling:
        world.say(
            f"{child.pronoun().capitalize()} dragged it under {perch.phrase} with all the ceremony of a parade float."
        )
    else:
        world.say(
            f"{child.pronoun().capitalize()} nudged it into place and gave it a hopeful little pat."
        )


def climb(world: World, child: Entity, plan: Entity) -> None:
    child.meters["climbing"] += 1
    child.meters["reaching"] += 1
    propagate(world, narrate=False)
    if child.meters["wobble"] >= THRESHOLD:
        world.say(
            f"The moment {child.pronoun()} climbed up, {plan.label} gave a sneaky little wiggle."
        )
        world.say(
            f'Inside {child.pronoun("possessive")} head, the brave voice squeaked, "Remain calm." '
            f'The sensible voice replied, "We are not, in fact, calm."'
        )
    else:
        world.say(
            f"{child.id} climbed up and stretched on tiptoe, trying to look as tall as a lamppost."
        )
    if world.get("room").meters["noise"] >= THRESHOLD:
        world.say("Something bumped and rattled far louder than a secret mission ought to.")


def grab_treat(world: World, child: Entity, treat_ent: Entity, treat: Treat) -> None:
    child.meters["holding_treat"] += 1
    propagate(world, narrate=False)
    if treat_ent.meters["spilled"] >= THRESHOLD:
        world.say(
            f"{child.pronoun().capitalize()} got both hands on the {treat.label} for exactly one proud second."
        )
        if treat.drippy:
            world.say(
                f"Then {treat.mess_word} slid out, kissed {child.pronoun('possessive')} sleeve, and dropped to the floor with a comic splat."
            )
        else:
            world.say(
                f"Then a merry rain of {treat.mess_word} showered down over {child.pronoun('possessive')} shirt and the tiles below."
            )
    else:
        world.say(
            f"{child.pronoun().capitalize()} just brushed the edge of the {treat.label} when the plate clinked like a tiny bell."
        )
        world.say(
            f'Inside {child.pronoun("possessive")} head, the loud voice muttered, "Perhaps the mission has become public."'
        )


def adult_arrives(world: World, child: Entity, adult: Entity, treat: Treat) -> None:
    adult.memes["patience"] += 1
    if world.get("treat").meters["spilled"] >= THRESHOLD:
        world.say(
            f"{adult.label_word.capitalize()} came around the corner, stopped, and took in the cream on the sleeve, the crumbs on the floor, and the guilty face in the middle."
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} came around the corner just as the plate gave one last clink."
        )
    world.say(
        f'"Well, well," {adult.label_word} said, with one eyebrow up. "What have we here?"'
    )
    child.memes["embarrassment"] += 1
    world.say(
        f'{child.id} looked down. Inside {child.pronoun("possessive")} head, the loud voice coughed and said, "A scallywag, apparently."'
    )


def resolution(world: World, child: Entity, adult: Entity, treat: Treat) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    child.memes["mischief"] = 0.0
    world.say(
        f'"Next time," {adult.label_word} said, "use words, not wheels."'
    )
    if world.get("treat").meters["spilled"] >= THRESHOLD:
        world.say(
            f'{adult.pronoun().capitalize()} handed {child.pronoun("object")} a damp cloth. "A real helper cleans the jam and then gets a proper plate."'
        )
        world.say(
            f"{child.id} wiped the floor, the chair leg, and even a dot from {child.pronoun('possessive')} own nose."
        )
    else:
        world.say(
            f'{adult.pronoun().capitalize()} lifted {child.pronoun("object")} down, set the plate safely on the table, and said, "A real helper asks first and carries the napkins."'
        )
        world.say(
            f"{child.id} hurried off with the napkins, walking very straight, like a tiny waiter in an important restaurant."
        )
    world.say(
        f"When tea was ready, {adult.label_word} put one {treat.label} on a small plate and slid it over. "
        f'"Helpers eat first-class snacks too," {adult.pronoun()} said.'
    )
    world.say(
        f"{child.id} laughed so hard that the whole secret-mission feeling melted away."
    )


def ending_image(world: World, child: Entity, treat: Treat) -> None:
    world.say(
        f"After that, whenever something delicious sat up high, {child.id} still heard the silly voice in {child.pronoun('possessive')} head."
    )
    world.say(
        f"But now it usually said, \"Ask nicely, hold the plate steady, and save the scallywag tricks for pirate games.\" "
        f"And {child.pronoun()} did, with both feet on the floor and powdered sugar on a proper napkin instead of {child.pronoun('possessive')} elbow."
    )


def tell(treat: Treat, perch: Perch, plan: Plan, child_name: str, child_gender: str,
         adult_type: str, trait: str) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            traits=[trait],
            role="child",
            attrs={"display_name": child_name},
        )
    )
    adult = world.add(
        Entity(
            id="adult",
            kind="character",
            type=adult_type,
            label="the grown-up",
            phrase="the grown-up",
            role="adult",
        )
    )
    world.add(Entity(id="room", type="room", label="kitchen"))
    world.add(Entity(id="floor", type="floor", label="tiles"))
    world.add(
        Entity(
            id="plan",
            type="plan",
            label=plan.label,
            phrase=plan.phrase,
            attrs={"reach": plan.reach, "stability": plan.stability, "rolling": plan.rolling},
            tags=set(plan.tags),
        )
    )
    world.add(
        Entity(
            id="perch",
            type="perch",
            label=perch.label,
            phrase=perch.phrase,
            attrs={"balance_need": perch.balance_need, "clangs": perch.clangs},
            tags=set(perch.tags),
        )
    )
    world.add(
        Entity(
            id="treat",
            type="treat",
            label=treat.label,
            phrase=treat.phrase,
            attrs={"slip": treat.slip, "mess_word": treat.mess_word},
            tags=set(treat.tags),
        )
    )

    setup_scene(world, child, adult, treat, perch)
    world.para()
    temptation(world, child, treat)
    scheme(world, child, plan, perch)
    world.para()
    climb(world, child, world.get("plan"))
    grab_treat(world, child, world.get("treat"), treat)
    adult_arrives(world, child, adult, treat)
    world.para()
    resolution(world, child, adult, treat)
    ending_image(world, child, treat)

    world.facts.update(
        child=child,
        adult=adult,
        treat_cfg=treat,
        perch_cfg=perch,
        plan_cfg=plan,
        display_name=child_name,
        outcome="spill" if world.get("treat").meters["spilled"] >= THRESHOLD else "caught",
        used_words={"scallywag"},
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    treat = f["treat_cfg"]
    perch = f["perch_cfg"]
    plan = f["plan_cfg"]
    outcome = f["outcome"]
    name = f["display_name"]
    return [
        (
            f'Write a funny story for a 3-to-5-year-old that includes the word "scallywag" '
            f'and uses inner monologue. A child named {name} tries to sneak a {treat.label} from {perch.phrase}.'
        ),
        (
            f"Tell a kitchen comedy where {name}'s thoughts argue with each other while "
            f"{child.pronoun('subject')} uses {plan.phrase} to reach a treat, and a kind grown-up turns the trouble into a lesson."
        ),
        (
            f"Write a gentle inner-monologue story with a {'messy' if outcome == 'spill' else 'caught-in-time'} turn, "
            f"ending with the child asking for help instead of balancing on a silly plan."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    treat = f["treat_cfg"]
    perch = f["perch_cfg"]
    plan = f["plan_cfg"]
    name = f["display_name"]
    child_word = "girl" if child.type == "girl" else "boy"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a {child_word} named {name} who wants a special {treat.label}, and {adult.label_word} who catches the sneaking plan. The whole story happens in the kitchen while the treat is waiting up high.",
        ),
        (
            f"Why was the {treat.label} up on {perch.phrase}?",
            f"It was there to cool and wait for tea instead of being eaten right away. That made it tempting because {name} could see it but was supposed to wait.",
        ),
        (
            f"What plan did {name} use to reach the treat?",
            f"{name} tried to use {plan.phrase} as a secret climbing plan. The child thought it looked clever, but it made the mission noisy and wobbly.",
        ),
        (
            "How do we know this story uses inner monologue?",
            f"The story lets us hear the voices inside {name}'s head talking back and forth. Those thoughts turn the sneaking into a joke because the brave voice keeps arguing with the sensible one.",
        ),
    ]
    if f["outcome"] == "spill":
        qa.append(
            (
                f"What went wrong when {name} grabbed the {treat.label}?",
                f"The plan wobbled, and the {treat.label} spilled {treat.mess_word} onto {name} and the floor. The mess happened because the platform was not steady enough for a slippery treat.",
            )
        )
    else:
        qa.append(
            (
                f"Did {name} eat the {treat.label} in secret?",
                f"No. The plate clinked and {adult.label_word} arrived before any sneaky bite happened. The child was caught because the reaching plan made enough noise to give the secret away.",
            )
        )
    qa.append(
        (
            f"How did {adult.label_word} solve the problem?",
            f"{adult.label_word.capitalize()} did not shout; {adult.pronoun()} turned the moment into a helper job and then gave {name} a proper plate at tea time. That changed the ending from sneaking to helping, so the child still got the treat the honest way.",
        )
    )
    qa.append(
        (
            f"What did {name} learn by the end?",
            f"{name} learned that asking for help works better than balancing on a rolling plan. The final image shows a child with both feet on the floor, which proves the sneaky idea has changed into a safer habit.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["treat_cfg"].tags) | set(f["plan_cfg"].tags) | {"ask", "wait"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        name = world.facts.get("display_name", e.label or e.id) if e.id == "child" else (e.label or e.id)
        lines.append(f"  {name:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        treat="cream_puff",
        perch="high_shelf",
        plan="spinning_chair",
        child_name="Lily",
        child_gender="girl",
        adult_type="grandmother",
        trait="dramatic",
        seed=1,
    ),
    StoryParams(
        treat="jam_tart",
        perch="cake_stand",
        plan="toy_wagon",
        child_name="Ben",
        child_gender="boy",
        adult_type="father",
        trait="cheeky",
        seed=2,
    ),
    StoryParams(
        treat="sugar_bun",
        perch="window_rack",
        plan="wooden_crate",
        child_name="Maya",
        child_gender="girl",
        adult_type="mother",
        trait="curious",
        seed=3,
    ),
]


ASP_RULES = r"""
% plan validity
valid(T, P, Pl) :- treat(T), perch(P), plan(Pl), reaches(Pl), reasonable(Pl).

reaches(Pl) :- reach(Pl, R), R >= 1.
reasonable(Pl) :- stability(Pl, S), min_safe_stability(M), S >= M, not too_silly(Pl).

% outcome: wobble if the plan is less stable than the perch needs.
wobble :- chosen_plan(Pl), chosen_perch(P), stability(Pl, S), balance_need(P, B), S < B.
slippery_treat :- chosen_treat(T), slip(T, V), V > 0.

outcome(spill) :- wobble, slippery_treat.
outcome(caught) :- not outcome(spill).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        lines.append(asp.fact("slip", treat_id, treat.slip))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("balance_need", perch_id, perch.balance_need))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("reach", plan_id, plan.reach))
        lines.append(asp.fact("stability", plan_id, plan.stability))
        if plan.too_silly:
            lines.append(asp.fact("too_silly", plan_id))
    lines.append(asp.fact("min_safe_stability", MIN_SAFE_STABILITY))
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
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_plan", params.plan),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: story was empty.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Smoke test failed: unresolved template braces in story.")
    if "scallywag" not in sample.story.lower():
        raise StoryError('Smoke test failed: required word "scallywag" missing.')
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child plots a comic treat heist with inner monologue."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan is not None:
        plan = PLANS[args.plan]
        if not plan_reasonable(plan):
            raise StoryError(explain_plan_rejection(plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.treat is None or combo[0] == args.treat)
        and (args.perch is None or combo[1] == args.perch)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, perch_id, plan_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_type = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        treat=treat_id,
        perch=perch_id,
        plan=plan_id,
        child_name=name,
        child_gender=gender,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"(Invalid treat: {params.treat})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Invalid perch: {params.perch})")
    if params.plan not in PLANS:
        raise StoryError(f"(Invalid plan: {params.plan})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid gender: {params.child_gender})")
    if params.adult_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Invalid adult type: {params.adult_type})")
    if not valid_combo(TREATS[params.treat], PERCHES[params.perch], PLANS[params.plan]):
        raise StoryError(explain_plan_rejection(PLANS[params.plan]))

    world = tell(
        treat=TREATS[params.treat],
        perch=PERCHES[params.perch],
        plan=PLANS[params.plan],
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (treat, perch, plan) combos:\n")
        for treat, perch, plan in combos:
            print(f"  {treat:11} {perch:11} {plan}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.treat} from {p.perch} using {p.plan} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
