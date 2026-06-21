#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kiddo_market_inner_monologue_sound_effects_adventure.py
==================================================================================

A standalone story world about a brave kiddo on a tiny market errand that feels
like an adventure. The child must carry a market item through a busy lane while
choosing a sensible way to hold it. The world model tracks physical wobble and
drops, plus courage, worry, and pride, so the prose follows what actually
happens.

Features required by the seed:
- the words "kiddo" and "market"
- inner monologue
- sound effects
- an adventure flavor

Run it
------
    python storyworlds/worlds/gpt-5.4/kiddo_market_inner_monologue_sound_effects_adventure.py
    python storyworlds/worlds/gpt-5.4/kiddo_market_inner_monologue_sound_effects_adventure.py --item eggs --carrier basket
    python storyworlds/worlds/gpt-5.4/kiddo_market_inner_monologue_sound_effects_adventure.py --item eggs --carrier pocket
    python storyworlds/worlds/gpt-5.4/kiddo_market_inner_monologue_sound_effects_adventure.py --all
    python storyworlds/worlds/gpt-5.4/kiddo_market_inner_monologue_sound_effects_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/kiddo_market_inner_monologue_sound_effects_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    plural: bool = False
    risk: int = 1
    needs: set[str] = field(default_factory=set)
    lesson: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    stability: int = 1
    features: set[str] = field(default_factory=set)
    sense: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    bump: int = 1
    sound: str = ""
    motion: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    reach: int = 1
    rescue_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    item: str
    carrier: str
    obstacle: str
    helper: str
    pace: str
    kid_name: str
    kid_gender: str
    grownup: str
    mood: str
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


def _r_wobble_from_risk(world: World) -> list[str]:
    kid = world.entities.get("kid")
    cargo = world.entities.get("cargo")
    if not kid or not cargo:
        return []
    risk = world.facts.get("risk_score", 0)
    stability = world.facts.get("stability", 0)
    if risk <= stability:
        return []
    sig = ("wobble", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["wobble"] += 1
    kid.memes["worry"] += 1
    return []


def _r_drop_from_wobble(world: World) -> list[str]:
    kid = world.entities.get("kid")
    cargo = world.entities.get("cargo")
    if not kid or not cargo:
        return []
    risk = world.facts.get("risk_score", 0)
    stability = world.facts.get("stability", 0)
    reach = world.facts.get("reach", 0)
    if cargo.meters["wobble"] < THRESHOLD:
        return []
    if risk <= stability + reach:
        return []
    sig = ("drop", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["dropped"] += 1
    kid.memes["fear"] += 1
    kid.memes["pride"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="wobble_from_risk", tag="physical", apply=_r_wobble_from_risk),
    Rule(name="drop_from_wobble", tag="physical", apply=_r_drop_from_wobble),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name.split("_")[0] for sig in world.fired):
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def compatible(item: Item, carrier: Carrier) -> bool:
    return item.needs.issubset(carrier.features)


def sensible_carriers(item: Item) -> list[Carrier]:
    return [
        carrier for carrier in CARRIERS.values()
        if carrier.sense >= SENSE_MIN and compatible(item, carrier)
    ]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for carrier_id, carrier in CARRIERS.items():
            if not compatible(item, carrier) or carrier.sense < SENSE_MIN:
                continue
            for obstacle_id in OBSTACLES:
                for helper_id in HELPERS:
                    for pace in PACES:
                        combos.append((item_id, carrier_id, obstacle_id, helper_id, pace))
    return combos


def risk_score(item: Item, obstacle: Obstacle, pace: str) -> int:
    return item.risk + obstacle.bump + (1 if pace == "rush" else 0)


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    carrier = CARRIERS[params.carrier]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    risk = risk_score(item, obstacle, params.pace)
    if risk <= carrier.stability:
        return "smooth"
    if risk <= carrier.stability + helper.reach:
        return "saved"
    return "lost"


def explain_rejection(item: Item, carrier: Carrier) -> str:
    needed = ", ".join(sorted(item.needs))
    have = ", ".join(sorted(carrier.features)) or "nothing that steadies the item"
    return (
        f"(No story: {carrier.phrase} is not a sensible way to carry {item.phrase}. "
        f"{item.label.capitalize()} need support for {needed}, but this carrier offers {have}. "
        f"Pick a steadier choice such as {', '.join(sorted(c.id for c in sensible_carriers(item)))}.)"
    )


def pace_text(pace: str) -> str:
    return {
        "careful": "slow and steady",
        "rush": "fast as a tiny comet",
    }[pace]


def inner_line(kind: str, kid: Entity, item: Item, obstacle: Obstacle) -> str:
    if kind == "quest":
        return (
            f'{kid.id} told {kid.pronoun("object")}self, "I am not just shopping. '
            f'I am a kiddo on a market mission."'
        )
    if kind == "worry":
        return (
            f'Inside {kid.pronoun("possessive")} head, a small thought whispered, '
            f'"Easy now. {obstacle.label.capitalize()} can jolt {item.label}."'
        )
    if kind == "brave":
        return (
            f'Then another thought stood up straighter: "I can fix this if I keep my eyes open."'
        )
    return (
        f'{kid.id} thought, "Adventure feet first, and careful hands too."'
    )


def introduce(world: World, kid: Entity, grown: Entity, item: Item) -> None:
    world.say(
        f"Morning bells were waking the market when {kid.id}, a brave little kiddo, "
        f"walked beside {grown.label_word}. Stalls shimmered with oranges, ribbons, and copper pans, "
        f"and the whole place felt like the start of an adventure."
    )
    world.say(
        f"{grown.label_word.capitalize()} stopped at the soup stall and pointed to {item.phrase}. "
        f'"Can you carry this back to me?" {grown.pronoun()} asked. "It is a small job, but it needs careful hands."'
    )
    kid.memes["courage"] += 1
    world.say(inner_line("quest", kid, item, OBSTACLES["pigeons"]))


def choose_carrier(world: World, kid: Entity, carrier: Carrier, mood: str) -> None:
    kid.attrs["mood"] = mood
    if mood == "bold":
        kid.memes["pride"] += 1
        world.say(
            f"{kid.id} reached for {carrier.phrase} and lifted {kid.pronoun('possessive')} chin. "
            f'{kid.pronoun("subject").capitalize()} thought, "This looks right for a hero."'
        )
    else:
        kid.memes["care"] += 1
        world.say(
            f"{kid.id} tested {carrier.phrase} with both hands first. "
            f'{kid.pronoun("subject").capitalize()} thought, "Better to start steady than sorry."'
        )


def set_out(world: World, kid: Entity, item: Item, carrier: Carrier, pace: str) -> None:
    cargo = world.get("cargo")
    cargo.attrs["carrier"] = carrier.id
    world.say(
        f"{kid.id} tucked {item.phrase} into {carrier.phrase} and set off through the market, "
        f"moving {pace_text(pace)}."
    )
    if pace == "rush":
        kid.memes["haste"] += 1
        world.say(
            f'{kid.pronoun("subject").capitalize()} could almost hear a drum in {kid.pronoun("possessive")} chest: '
            f'"Go, go, go!"'
        )
    else:
        kid.memes["care"] += 1
        world.say(
            f'{kid.pronoun("subject").capitalize()} counted steps in {kid.pronoun("possessive")} head: '
            f'"One crate, two crates, three crates. No wobbling."'
        )


def obstacle_hit(world: World, kid: Entity, item: Item, obstacle: Obstacle) -> None:
    world.say(
        f"Then the turn came. {obstacle.sound} {obstacle.motion} through the market lane."
    )
    world.say(
        f"{kid.id} felt {item.label} shift for one scary second."
    )
    world.say(inner_line("worry", kid, item, obstacle))
    propagate(world, narrate=False)


def smooth_finish(world: World, kid: Entity, grown: Entity, item: Item) -> None:
    kid.memes["pride"] += 1
    kid.memes["relief"] += 1
    world.say(
        f"But {kid.id} tightened {kid.pronoun('possessive')} grip, kept walking, and the wobble never won. "
        f"Step by step, the little quest reached the soup stall."
    )
    world.say(
        f'{grown.label_word.capitalize()} smiled when {kid.pronoun("subject")} arrived with {item.phrase} safe. '
        f'"You carried it like a true market explorer," {grown.pronoun()} said.'
    )
    world.say(
        f"{kid.id} grinned at the steam curling from the pot and felt taller than before."
    )


def saved_finish(world: World, kid: Entity, grown: Entity, item: Item, helper: Helper) -> None:
    cargo = world.get("cargo")
    cargo.meters["caught"] += 1
    kid.memes["relief"] += 1
    kid.memes["pride"] += 1
    world.say(
        f"The load tipped. {helper.rescue_text} and caught the trouble before it touched the stones."
    )
    world.say(inner_line("brave", kid, item, OBSTACLES["cart"]))
    world.say(
        f"{kid.id} took a deep breath, held {item.phrase} much more carefully, and finished the trip at a slower pace."
    )
    world.say(
        f'{grown.label_word.capitalize()} thanked {helper.label} and then squeezed {kid.id}\'s shoulder. '
        f'"Adventurers do not have to be perfect," {grown.pronoun()} said. "They just have to learn fast."'
    )
    world.say(
        f"At the end, the market did not feel too big anymore. It felt like a place where careful courage worked."
    )


def lost_finish(world: World, kid: Entity, grown: Entity, item: Item, helper: Helper) -> None:
    cargo = world.get("cargo")
    cargo.meters["broken"] += 1
    kid.memes["sadness"] += 1
    kid.memes["lesson"] += 1
    world.say(
        f"The wobble became a drop. {item.phrase.capitalize()} slipped free and was lost on the market stones."
    )
    world.say(
        f"{helper.label.capitalize()} hurried over, but this time there was nothing to catch in time."
    )
    world.say(
        f"{kid.id}'s cheeks went hot. Inside, {kid.pronoun('subject')} thought, "
        f'"I wanted to be fast. I should have been steadier."'
    )
    world.say(
        f"But {grown.label_word} knelt beside {kid.pronoun('object')} and spoke gently. "
        f'"A hard moment can still teach us something," {grown.pronoun()} said.'
    )
    world.say(
        f"Together they chose a better carrier and tried again. When they returned to the stall, "
        f"the market bells were still ringing, but now {kid.id} walked like someone who knew how to listen to them."
    )


def tell(
    item: Item,
    carrier: Carrier,
    obstacle: Obstacle,
    helper: Helper,
    pace: str,
    kid_name: str,
    kid_gender: str,
    grownup: str,
    mood: str,
) -> World:
    world = World()
    kid = world.add(Entity(
        id="kid",
        kind="character",
        type=kid_gender,
        label=kid_name,
        role="kid",
        traits=[mood],
    ))
    grown = world.add(Entity(
        id="grown",
        kind="character",
        type=grownup,
        label="the grown-up",
        role="grown",
    ))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type="item",
        label=item.label,
        phrase=item.phrase,
        role="cargo",
        tags=set(item.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type="seller",
        label=helper.label,
        phrase=helper.phrase,
        role="helper",
        tags=set(helper.tags),
    ))

    world.facts["stability"] = carrier.stability
    world.facts["risk_score"] = risk_score(item, obstacle, pace)
    world.facts["reach"] = helper.reach

    introduce(world, kid, grown, item)

    world.para()
    choose_carrier(world, kid, carrier, mood)
    set_out(world, kid, item, carrier, pace)

    world.para()
    obstacle_hit(world, kid, item, obstacle)

    outcome = outcome_of(StoryParams(
        item=item.id,
        carrier=carrier.id,
        obstacle=obstacle.id,
        helper=helper.id,
        pace=pace,
        kid_name=kid_name,
        kid_gender=kid_gender,
        grownup=grownup,
        mood=mood,
    ))

    if outcome == "smooth":
        smooth_finish(world, kid, grown, item)
    elif outcome == "saved":
        saved_finish(world, kid, grown, item, helper)
    else:
        lost_finish(world, kid, grown, item, helper)

    world.facts.update(
        kid=kid,
        grown=grown,
        cargo=cargo,
        helper=helper_ent,
        item_cfg=item,
        carrier_cfg=carrier,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        pace=pace,
        mood=mood,
        outcome=outcome,
        risk=world.facts["risk_score"],
        stability=carrier.stability,
        reach=helper.reach,
        wobble=cargo.meters["wobble"] >= THRESHOLD,
        dropped=cargo.meters["dropped"] >= THRESHOLD,
        saved=cargo.meters["caught"] >= THRESHOLD,
    )
    return world


ITEMS = {
    "eggs": Item(
        id="eggs",
        label="eggs",
        phrase="a paper-wrapped dozen eggs",
        plural=True,
        risk=3,
        needs={"flat", "steady"},
        lesson="Eggs crack when they are bumped, so they need a flat, steady ride.",
        tags={"eggs", "fragile"},
    ),
    "peaches": Item(
        id="peaches",
        label="peaches",
        phrase="three sun-soft peaches",
        plural=True,
        risk=2,
        needs={"steady"},
        lesson="Soft fruit bruises when it bumps around.",
        tags={"fruit", "fragile"},
    ),
    "honey": Item(
        id="honey",
        label="honey jar",
        phrase="a round jar of honey",
        plural=False,
        risk=2,
        needs={"grip", "steady"},
        lesson="A smooth jar can slip if you rush.",
        tags={"jar", "sticky"},
    ),
    "herbs": Item(
        id="herbs",
        label="herb bundle",
        phrase="a green bundle of herbs",
        plural=False,
        risk=1,
        needs={"light"},
        lesson="Herbs are light, but you can still drop them if you stop paying attention.",
        tags={"herbs"},
    ),
}

CARRIERS = {
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a willow basket",
        stability=3,
        features={"flat", "steady", "grip", "light"},
        sense=2,
        tags={"basket"},
    ),
    "cloth_bag": Carrier(
        id="cloth_bag",
        label="cloth bag",
        phrase="a cloth bag",
        stability=2,
        features={"steady", "grip", "light"},
        sense=2,
        tags={"bag"},
    ),
    "two_hands": Carrier(
        id="two_hands",
        label="two hands",
        phrase="both hands",
        stability=2,
        features={"flat", "grip", "light"},
        sense=2,
        tags={"hands"},
    ),
    "pocket": Carrier(
        id="pocket",
        label="pocket",
        phrase="an apron pocket",
        stability=0,
        features={"light"},
        sense=1,
        tags={"pocket"},
    ),
}

OBSTACLES = {
    "pigeons": Obstacle(
        id="pigeons",
        label="fluttering pigeons",
        phrase="a burst of pigeons",
        bump=1,
        sound="WHIRR-FLAP!",
        motion="Pigeons burst up from under a grain cart",
        tags={"pigeons", "market"},
    ),
    "cart": Obstacle(
        id="cart",
        label="a rattling cart",
        phrase="a rattling cart",
        bump=2,
        sound="RUMBLE-clack! CLATTER!",
        motion="A vegetable cart rolled over the cobbles",
        tags={"cart", "market"},
    ),
    "bell": Obstacle(
        id="bell",
        label="the bell rush",
        phrase="a bell rush",
        bump=1,
        sound="DING-DING! Shuffle, shuffle!",
        motion="The bread bell rang and shoppers swayed across the lane",
        tags={"bell", "crowd"},
    ),
}

HELPERS = {
    "baker": Helper(
        id="baker",
        label="the baker",
        phrase="the baker with flour on both sleeves",
        reach=2,
        rescue_text="The baker darted out with quick, floury hands",
        tags={"baker"},
    ),
    "fruit_seller": Helper(
        id="fruit_seller",
        label="the fruit seller",
        phrase="the fruit seller under the striped awning",
        reach=1,
        rescue_text="The fruit seller lunged from behind the peaches",
        tags={"fruit_seller"},
    ),
    "porter": Helper(
        id="porter",
        label="the market porter",
        phrase="the market porter with the broad cart strap",
        reach=3,
        rescue_text="The market porter swung around like a gate and caught the slipping bundle",
        tags={"porter"},
    ),
}

PACES = ["careful", "rush"]
MOODS = ["bold", "thoughtful"]
GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Zoe", "Tess"]
BOY_NAMES = ["Nico", "Ben", "Owen", "Finn", "Eli", "Theo"]


CURATED = [
    StoryParams(
        item="eggs",
        carrier="basket",
        obstacle="cart",
        helper="baker",
        pace="careful",
        kid_name="Mina",
        kid_gender="girl",
        grownup="aunt",
        mood="thoughtful",
    ),
    StoryParams(
        item="peaches",
        carrier="cloth_bag",
        obstacle="pigeons",
        helper="fruit_seller",
        pace="rush",
        kid_name="Nico",
        kid_gender="boy",
        grownup="mother",
        mood="bold",
    ),
    StoryParams(
        item="honey",
        carrier="two_hands",
        obstacle="cart",
        helper="porter",
        pace="rush",
        kid_name="Lila",
        kid_gender="girl",
        grownup="father",
        mood="bold",
    ),
    StoryParams(
        item="herbs",
        carrier="pocket",
        obstacle="bell",
        helper="fruit_seller",
        pace="careful",
        kid_name="Ben",
        kid_gender="boy",
        grownup="uncle",
        mood="thoughtful",
    ),
    StoryParams(
        item="eggs",
        carrier="two_hands",
        obstacle="cart",
        helper="fruit_seller",
        pace="rush",
        kid_name="Tess",
        kid_gender="girl",
        grownup="mother",
        mood="bold",
    ),
]


KNOWLEDGE = {
    "eggs": [(
        "Why do eggs need careful carrying?",
        "Eggs have thin shells, so a hard bump can crack them. That is why people carry them flat and gently."
    )],
    "fruit": [(
        "Why can soft peaches get bruised?",
        "Soft fruit presses and dents when it bumps into things. Even if it does not split open, rough carrying can still hurt it."
    )],
    "jar": [(
        "Why can a jar slip from your hands?",
        "A round, smooth jar can slide if your hands are busy or if you hurry. Holding it steadily gives you more control."
    )],
    "basket": [(
        "Why is a basket good for carrying market things?",
        "A basket gives things a steady place to sit. It helps keep them from rolling and bumping into each other."
    )],
    "bag": [(
        "What is a cloth bag good for?",
        "A cloth bag is good for carrying many market things, especially items that are not too easy to crush. It is softer than a basket, so you still have to be careful."
    )],
    "hands": [(
        "Why does using both hands help?",
        "Using both hands can make an object steadier because each hand helps balance the other. It also reminds you to slow down."
    )],
    "pocket": [(
        "Why is a pocket not good for many market things?",
        "A pocket can swing, squash, or tip what is inside. It is only good for very light things that do not need much support."
    )],
    "market": [(
        "Why can a market feel busy?",
        "A market is full of voices, carts, bells, and people walking in many directions. That busy motion means you have to watch where you step."
    )],
    "fragile": [(
        "What does fragile mean?",
        "Fragile means something can break or bruise easily. Fragile things need extra care."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    item = f["item_cfg"]
    obstacle = f["obstacle_cfg"]
    return [
        f'Write an adventure-style story for a 3-to-5-year-old about a kiddo in a market carrying {item.phrase}. Include inner monologue and sound effects.',
        f"Tell a gentle market adventure where {kid.label} tries to bring {item.phrase} through a busy lane and meets {obstacle.label}.",
        'Write a simple story that uses the word "market", includes a child thinking to themself, and turns a small errand into a brave little quest.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    grown = f["grown"]
    item = f["item_cfg"]
    carrier = f["carrier_cfg"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid.label}, a brave little kiddo at the market, and {grown.label_word} who trusted {kid.pronoun('object')} with a careful job."
        ),
        (
            "What was the kid's mission?",
            f"{kid.label} had to carry {item.phrase} through the market and bring it back safely. The errand felt like an adventure because the market was busy and full of surprises."
        ),
        (
            f"Why did {kid.label} need to be careful?",
            f"{item.lesson} The lane was also busy with {obstacle.label}, so one bump could make the trip harder."
        ),
        (
            "How did inner monologue appear in the story?",
            f"The child talked silently inside {kid.pronoun('possessive')} own head, calling the errand a mission and reminding {kid.pronoun('object')}self to stay careful. Those thoughts show the story from the inside, not only from the outside."
        ),
        (
            "What sound effect changed the story's action?",
            f'The turn came with the sound "{obstacle.sound}" when {obstacle.motion.lower()}. That noisy moment is what made the carrying feel risky.'
        ),
    ]

    if outcome == "smooth":
        qa.append((
            f"How did {kid.label} solve the problem?",
            f"{kid.label} kept hold of {item.phrase} in {carrier.phrase} and did not let the wobble grow into a drop. The safe ending came from steadiness before the trouble got bigger."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily with {kid.label} reaching the stall and feeling proud. The last image shows that a small market job helped the kid feel bigger and braver."
        ))
    elif outcome == "saved":
        qa.append((
            f"Who helped when things almost went wrong?",
            f"{helper.label.capitalize()} helped catch the trouble before {item.phrase} hit the stones. After that, {kid.label} slowed down and finished the trip more carefully."
        ))
        qa.append((
            f"What did {kid.label} learn?",
            f"{kid.label} learned that courage is not only about hurrying ahead. It is also about noticing danger, accepting help, and changing how you move."
        ))
    else:
        qa.append((
            f"Did {kid.label} lose the item?",
            f"Yes. {item.phrase.capitalize()} was lost when the wobble became a drop and nobody could catch it in time."
        ))
        qa.append((
            f"What happened after the mistake?",
            f"{grown.label_word.capitalize()} stayed gentle and helped {kid.label} try again with a better plan. The ending still feels hopeful because the child leaves wiser, not ashamed."
        ))

    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    item = f["item_cfg"]
    carrier = f["carrier_cfg"]
    obstacle = f["obstacle_cfg"]

    tags |= item.tags
    tags |= carrier.tags
    tags |= obstacle.tags
    tags.add("market")

    ordered = ["eggs", "fruit", "jar", "fragile", "basket", "bag", "hands", "pocket", "market"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
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
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    lines.append(
        f"  risk={world.facts.get('risk_score', world.facts.get('risk'))} "
        f"stability={world.facts.get('stability')} reach={world.facts.get('reach')}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
compatible(I, C) :- item(I), carrier(C),
                    need(I, F), not feature(C, F), false.
compatible(I, C) :- item(I), carrier(C),
                    not missing_need(I, C).
missing_need(I, C) :- need(I, F), not feature(C, F).

sensible(C) :- carrier(C), sense(C, S), sense_min(M), S >= M.
valid(I, C, O, H, P) :- item(I), obstacle(O), helper(H), pace(P),
                        compatible(I, C), sensible(C).

% --- outcome ---------------------------------------------------------------
risk(V) :- chosen_item(I), chosen_obstacle(O), chosen_pace(P),
           item_risk(I, IR), bump(O, B), rush_bonus(P, RB), V = IR + B + RB.
smooth :- chosen_carrier(C), risk(V), stability(C, S), V <= S.
saved  :- chosen_carrier(C), chosen_helper(H), risk(V), stability(C, S), reach(H, R),
          V > S, V <= S + R.
lost   :- chosen_carrier(C), chosen_helper(H), risk(V), stability(C, S), reach(H, R),
          V > S + R.

outcome(smooth) :- smooth.
outcome(saved)  :- saved.
outcome(lost)   :- lost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for pace in PACES:
        lines.append(asp.fact("pace", pace))
        lines.append(asp.fact("rush_bonus", pace, 1 if pace == "rush" else 0))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_risk", item_id, item.risk))
        for need in sorted(item.needs):
            lines.append(asp.fact("need", item_id, need))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        lines.append(asp.fact("sense", carrier_id, carrier.sense))
        lines.append(asp.fact("stability", carrier_id, carrier.stability))
        for feature in sorted(carrier.features):
            lines.append(asp.fact("feature", carrier_id, feature))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("bump", obstacle_id, obstacle.bump))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("reach", helper_id, helper.reach))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_carrier", params.carrier),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_pace", params.pace),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid_combos parity holds ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sensible = sorted(c.id for c in CARRIERS.values() if c.sense >= SENSE_MIN)
    clingo_sensible = asp_sensible()
    if python_sensible == clingo_sensible:
        print(f"OK: sensible carriers match ({python_sensible}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible carriers: clingo={clingo_sensible} python={python_sensible}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure on seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = CURATED[0]
        smoke = generate(smoke_params)
        if not smoke.story.strip():
            raise StoryError("Generated story was empty.")
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny market adventure storyworld. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--pace", choices=PACES)
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.carrier:
        item = ITEMS[args.item]
        carrier = CARRIERS[args.carrier]
        if not compatible(item, carrier) or carrier.sense < SENSE_MIN:
            raise StoryError(explain_rejection(item, carrier))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.carrier is None or combo[1] == args.carrier)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper is None or combo[3] == args.helper)
        and (args.pace is None or combo[4] == args.pace)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, carrier_id, obstacle_id, helper_id, pace = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    kid_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    mood = args.mood or rng.choice(MOODS)

    return StoryParams(
        item=item_id,
        carrier=carrier_id,
        obstacle=obstacle_id,
        helper=helper_id,
        pace=pace,
        kid_name=kid_name,
        kid_gender=gender,
        grownup=grownup,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        item = ITEMS[params.item]
        carrier = CARRIERS[params.carrier]
        obstacle = OBSTACLES[params.obstacle]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]!r})") from err

    if not compatible(item, carrier) or carrier.sense < SENSE_MIN:
        raise StoryError(explain_rejection(item, carrier))
    if params.pace not in PACES:
        raise StoryError(f"(Invalid pace: {params.pace!r})")
    if params.kid_gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid gender: {params.kid_gender!r})")
    if params.grownup not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Invalid grownup: {params.grownup!r})")
    if params.mood not in MOODS:
        raise StoryError(f"(Invalid mood: {params.mood!r})")

    world = tell(
        item=item,
        carrier=carrier,
        obstacle=obstacle,
        helper=helper,
        pace=params.pace,
        kid_name=params.kid_name,
        kid_gender=params.kid_gender,
        grownup=params.grownup,
        mood=params.mood,
    )
    world_story = world.render().replace(" kid ", " child ")
    return StorySample(
        params=params,
        story=world_story,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible carriers: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, carrier, obstacle, helper, pace) combos:\n")
        for item, carrier, obstacle, helper, pace in combos:
            print(f"  {item:8} {carrier:10} {obstacle:8} {helper:12} {pace}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            p = StoryParams(**{**params.__dict__})
            samples.append(generate(p))
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
            header = (
                f"### {p.kid_name}: {p.item} by {p.carrier} past {p.obstacle} "
                f"({p.pace}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
