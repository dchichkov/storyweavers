#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/focus_marina_bravery_happy_ending_fairy_tale.py
============================================================================

A small fairy-tale storyworld set at a marina. A child must use focus and
bravery to help a drifting festival lantern before the harbor goes dark.

The world is state-driven: fear rises from the obstacle, a helper and a charm
increase focus and courage, and the ending depends on whether the child succeeds
boldly alone or with a steadying bit of help. All valid stories end happily,
but only combinations that make common-sense sense in this little domain are
allowed.

Run it
------
    python storyworlds/worlds/gpt-5.4/focus_marina_bravery_happy_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/focus_marina_bravery_happy_ending_fairy_tale.py --obstacle wobbly_plank --charm guide_rope
    python storyworlds/worlds/gpt-5.4/focus_marina_bravery_happy_ending_fairy_tale.py --obstacle high_ladder --charm star_lantern
    python storyworlds/worlds/gpt-5.4/focus_marina_bravery_happy_ending_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/focus_marina_bravery_happy_ending_fairy_tale.py --verify
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
        female = {"girl", "woman", "grandmother"}
        male = {"boy", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Obstacle:
    id: str
    label: str
    scene: str
    danger: str
    action: str
    success: str
    assist: str
    risk: int
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    offer: str
    glow: str
    focus_boost: int
    courage_boost: int
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    type: str
    entrance: str
    line: str
    focus_boost: int
    courage_boost: int
    method: str
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


def _r_focus_to_courage(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["focus"] < THRESHOLD:
        return []
    sig = ("focus_to_courage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    return []


def _r_courage_calm(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["courage"] < THRESHOLD:
        return []
    sig = ("courage_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hero.memes["fear"] > 0:
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    return []


CAUSAL_RULES = [
    Rule(name="focus_to_courage", tag="emotional", apply=_r_focus_to_courage),
    Rule(name="courage_calm", tag="emotional", apply=_r_courage_calm),
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
                changed = True if False else changed
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


OBSTACLES = {
    "wobbly_plank": Obstacle(
        id="wobbly_plank",
        label="wobbly plank",
        scene="a narrow plank that bounced above the water between the dock and the little lantern skiff",
        danger="The dark water slapped softly under the boards, and every tiny wobble made the marina seem bigger.",
        action="cross the plank and catch the loose skiff rope",
        success="With small brave steps, {name} crossed the plank, caught the silver rope, and drew the lantern skiff back to the dock.",
        assist="{helper} kept hold of the far end of the rope while {name} crossed, and together they brought the lantern skiff safely home.",
        risk=4,
        needs={"balance"},
        tags={"water", "balance"},
    ),
    "misty_pier": Obstacle(
        id="misty_pier",
        label="misty pier",
        scene="a long pier wrapped in pearl-colored mist, where the bell rope hung near the very end",
        danger="The mist made the old boards look lonely, and the lamp at the end was only a pale speck.",
        action="walk through the mist and ring the harbor bell so the skiff would turn back",
        success="Step by step, {name} followed the dim boards through the mist and rang the harbor bell. Its clear note curled over the water, and the lantern skiff drifted back.",
        assist="{helper} walked close beside {name}, and together they found the bell rope and rang it until the lantern skiff turned home.",
        risk=3,
        needs={"dark"},
        tags={"dark", "mist"},
    ),
    "high_ladder": Obstacle(
        id="high_ladder",
        label="high ladder",
        scene="a tall signal ladder beside the watch hut, with moonlight on every rung",
        danger="The ladder rose above the roofs of the boats, and looking up made even a brave heart feel small.",
        action="climb the signal ladder and wave the blue harbor flag to call the breeze sprite",
        success="{name} climbed the ladder, lifted the blue harbor flag, and the breeze sprite came dancing. It nudged the drifting skiff gently back into its slip.",
        assist="{helper} steadied the ladder from below and called each next step, so {name} could climb high enough to wave the blue harbor flag and call the breeze sprite.",
        risk=4,
        needs={"height"},
        tags={"height"},
    ),
}

CHARMS = {
    "guide_rope": Charm(
        id="guide_rope",
        label="guide rope",
        phrase="a braided guide rope with tiny blue knots",
        offer="Take this guide rope. It will teach your hands where to hold.",
        glow="The blue knots felt firm and sure in small fingers.",
        focus_boost=2,
        courage_boost=1,
        helps={"balance", "height"},
        tags={"rope"},
    ),
    "star_lantern": Charm(
        id="star_lantern",
        label="star lantern",
        phrase="a star lantern no bigger than a pear",
        offer="Carry this star lantern. Its little light is for careful eyes, not hurried feet.",
        glow="Its gold light made one clear path through the dark.",
        focus_boost=2,
        courage_boost=1,
        helps={"dark"},
        tags={"lantern", "light"},
    ),
    "harbor_song": Charm(
        id="harbor_song",
        label="harbor song",
        phrase="a harbor song taught in four slow lines",
        offer="Sing the harbor song and let each line match one steady breath.",
        glow="The song made the world feel smaller and easier to hold in mind.",
        focus_boost=1,
        courage_boost=1,
        helps={"balance", "dark", "height"},
        tags={"song", "breathing"},
    ),
    "moon_boots": Charm(
        id="moon_boots",
        label="moon boots",
        phrase="a pair of moon boots with silver stitching",
        offer="Put on these moon boots. They grip the boards like two little moons.",
        glow="The soles hugged each board instead of slipping from it.",
        focus_boost=1,
        courage_boost=2,
        helps={"balance"},
        tags={"boots"},
    ),
}

COMPANIONS = {
    "harbor_fairy": Companion(
        id="harbor_fairy",
        label="the harbor fairy",
        type="fairy",
        entrance="Out of the mast shadows fluttered the harbor fairy, no larger than a gull's feather and bright as a bead of moonlight.",
        line='"Bravery is not a loud thing," whispered the harbor fairy. "Sometimes it is just one careful step after another."',
        focus_boost=1,
        courage_boost=1,
        method="hovered nearby like a patient little star",
        tags={"fairy", "magic"},
    ),
    "grandmother_keeper": Companion(
        id="grandmother_keeper",
        label="Grandmother Marina",
        type="grandmother",
        entrance="From the lantern shed came Grandmother Marina, keeper of the evening lights, with salt on her shawl and kindness in her eyes.",
        line='"Find your focus first," said Grandmother Marina. "A steady heart can do what a rushing heart cannot."',
        focus_boost=1,
        courage_boost=2,
        method="stood close enough for {name} to hear each calm word",
        tags={"grandmother", "keeper"},
    ),
    "talking_gull": Companion(
        id="talking_gull",
        label="a talking gull",
        type="bird",
        entrance="A white gull landed on a post, tipped its head, and spoke in a neat harbor voice as if that were the most ordinary thing in the world.",
        line='"Do not stare at the whole trouble," said the gull. "Choose the next true thing and do only that."',
        focus_boost=2,
        courage_boost=0,
        method="called out the next true thing from the nearest post",
        tags={"gull", "magic"},
    ),
}

GIRL_NAMES = ["Maris", "Lina", "Tessa", "Mira", "Nora", "Elsie", "Wren", "Ava"]
BOY_NAMES = ["Rowan", "Finn", "Theo", "Milo", "Eli", "Jonah", "Nico", "Tobin"]
TRAITS = ["careful", "kind", "quiet", "curious", "gentle", "thoughtful"]


def charm_fits(obstacle: Obstacle, charm: Charm) -> bool:
    return bool(obstacle.needs & charm.helps)


def support_score(obstacle: Obstacle, charm: Charm, companion: Companion) -> int:
    return charm.focus_boost + charm.courage_boost + companion.focus_boost + companion.courage_boost


def valid_combo(obstacle: Obstacle, charm: Charm, companion: Companion) -> bool:
    return charm_fits(obstacle, charm) and support_score(obstacle, charm, companion) >= obstacle.risk


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for oid, obstacle in OBSTACLES.items():
        for cid, charm in CHARMS.items():
            for pid, companion in COMPANIONS.items():
                if valid_combo(obstacle, charm, companion):
                    out.append((oid, cid, pid))
    return out


@dataclass
class StoryParams:
    obstacle: str
    charm: str
    companion: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        obstacle="wobbly_plank",
        charm="guide_rope",
        companion="grandmother_keeper",
        name="Mira",
        gender="girl",
        trait="careful",
    ),
    StoryParams(
        obstacle="misty_pier",
        charm="star_lantern",
        companion="harbor_fairy",
        name="Rowan",
        gender="boy",
        trait="quiet",
    ),
    StoryParams(
        obstacle="high_ladder",
        charm="guide_rope",
        companion="grandmother_keeper",
        name="Elsie",
        gender="girl",
        trait="thoughtful",
    ),
    StoryParams(
        obstacle="wobbly_plank",
        charm="moon_boots",
        companion="talking_gull",
        name="Finn",
        gender="boy",
        trait="kind",
    ),
    StoryParams(
        obstacle="misty_pier",
        charm="harbor_song",
        companion="talking_gull",
        name="Lina",
        gender="girl",
        trait="gentle",
    ),
]


def initial_fear(obstacle: Obstacle) -> float:
    return float(max(1, obstacle.risk - 1))


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    charm = CHARMS[params.charm]
    companion = COMPANIONS[params.companion]
    if not valid_combo(obstacle, charm, companion):
        return "invalid"
    score = support_score(obstacle, charm, companion)
    return "bold" if score >= obstacle.risk + 2 else "guided"


def predict_success(world: World, obstacle: Obstacle, charm: Charm, companion: Companion) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["focus"] += charm.focus_boost + companion.focus_boost
    hero.memes["courage"] += charm.courage_boost + companion.courage_boost
    hero.memes["fear"] = initial_fear(obstacle)
    propagate(sim, narrate=False)
    brave_enough = hero.memes["focus"] + hero.memes["courage"] >= obstacle.risk + 1
    return {
        "focus": hero.memes["focus"],
        "courage": hero.memes["courage"],
        "fear": hero.memes["fear"],
        "success": brave_enough,
    }


def opening(world: World, hero: Entity) -> None:
    world.say(
        f"At the edge of the marina, where masts clicked softly like knitting needles in the wind, there lived a {hero.traits[0]} child named {hero.id}."
    )
    world.say(
        f"{hero.id} loved the evening lights, because each lamp on the water looked like a tiny promise floating home."
    )


def festival_setup(world: World) -> None:
    world.say(
        "On the Night of Safe Harbors, the people of the town set one wish-lantern in a little skiff and let it shine for every boat still out on the sea."
    )


def trouble(world: World, hero: Entity, obstacle: Obstacle) -> None:
    lantern = world.get("lantern")
    skiff = world.get("skiff")
    skiff.meters["drift"] += 1
    lantern.meters["glow"] += 1
    hero.memes["fear"] = initial_fear(obstacle)
    world.say(
        f"But just as the bell gave its first silver note, a naughty puff of wind loosened the skiff rope."
    )
    world.say(
        f"The little lantern skiff drifted away from the dock toward the reeds. Soon the whole marina could see {obstacle.scene} between {hero.id} and the wandering light."
    )
    world.say(obstacle.danger)


def companion_arrives(world: World, companion: Companion) -> None:
    world.say(companion.entrance)
    world.say(companion.line)


def offer_charm(world: World, charm: Charm) -> None:
    world.say(
        f"The helper placed {charm.phrase} in the child's hands. \"{charm.offer}\""
    )
    world.say(charm.glow)


def warning_and_focus(world: World, hero: Entity, obstacle: Obstacle, charm: Charm, companion: Companion) -> None:
    pred = predict_success(world, obstacle, charm, companion)
    world.facts["predicted_focus"] = pred["focus"]
    world.facts["predicted_courage"] = pred["courage"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"{hero.id}'s heart beat fast enough to feel like a trapped fish. Yet {hero.pronoun()} remembered the word focus and held to it like a railing."
    )


def gather_courage(world: World, hero: Entity, charm: Charm, companion: Companion) -> None:
    hero.memes["focus"] += charm.focus_boost + companion.focus_boost
    hero.memes["courage"] += charm.courage_boost + companion.courage_boost
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took one slow breath, then another. The fear did not vanish, but it stopped pushing so hard."
    )
    world.say(
        f"With each careful breath, {hero.pronoun('possessive')} focus grew steadier than the ripples under the dock."
    )


def brave_act(world: World, hero: Entity, obstacle: Obstacle, companion: Companion, outcome: str) -> None:
    helper = COMPANIONS[world.facts["companion_cfg"].id].label
    if outcome == "bold":
        hero.meters["task_done"] += 1
        hero.memes["pride"] += 1
        world.say(obstacle.success.format(name=hero.id))
    else:
        hero.meters["task_done"] += 1
        hero.memes["trust"] += 1
        world.say(obstacle.assist.format(name=hero.id, helper=helper))
        world.say(
            f"{hero.id} still did the brave part. {companion.label.capitalize()} only made the next step easier to see."
        )


def happy_end(world: World, hero: Entity, companion: Companion) -> None:
    lantern = world.get("lantern")
    lantern.meters["safe"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        "When the skiff was tied fast again, the wish-lantern burned in a bright, round flame instead of a worried flicker."
    )
    world.say(
        f"The people along the marina clapped, and the boats answered with gentle taps against their ropes."
    )
    world.say(
        f"{hero.id} looked at the water, which no longer seemed huge and frightening, only deep and shining. Even the night felt friendlier now."
    )
    if companion.id == "harbor_fairy":
        world.say(
            "The harbor fairy dipped in the air like a falling star and laughed a bell-small laugh."
        )
    elif companion.id == "grandmother_keeper":
        world.say(
            "Grandmother Marina kissed the top of the child's head and said the harbor had gained one more keeper that night."
        )
    else:
        world.say(
            'The talking gull bowed so solemnly that everyone laughed, even the fishermen mending their nets.'
        )
    world.say(
        f"And from then on, whenever a task looked too large, {hero.id} remembered that bravery could begin with focus, one true step, and a kind light at the marina."
    )


def tell(obstacle: Obstacle, charm: Charm, companion_cfg: Companion, name: str, gender: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, role="hero", traits=[trait]))
    hero.id = name
    helper = world.add(Entity(id="helper", kind="character", type=companion_cfg.type, label=companion_cfg.label, role="helper"))
    skiff = world.add(Entity(id="skiff", kind="thing", type="boat", label="lantern skiff"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="wish-lantern"))
    marina = world.add(Entity(id="marina", kind="thing", type="place", label="marina"))
    world.facts["companion_cfg"] = companion_cfg

    opening(world, hero)
    festival_setup(world)

    world.para()
    trouble(world, hero, obstacle)

    world.para()
    companion_arrives(world, companion_cfg)
    offer_charm(world, charm)
    warning_and_focus(world, hero, obstacle, charm, companion_cfg)
    gather_courage(world, hero, charm, companion_cfg)

    outcome = "bold" if hero.memes["focus"] + hero.memes["courage"] >= obstacle.risk + 2 else "guided"
    world.para()
    brave_act(world, hero, obstacle, companion_cfg, outcome)
    happy_end(world, hero, companion_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        skiff=skiff,
        lantern=lantern,
        marina=marina,
        obstacle=obstacle,
        charm=charm,
        companion=companion_cfg,
        outcome=outcome,
        rescued=skiff.meters["drift"] >= THRESHOLD and hero.meters["task_done"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "marina": [
        (
            "What is a marina?",
            "A marina is a place by the water where small boats are kept. It often has docks, ropes, and little lamps or posts along the shore.",
        )
    ],
    "focus": [
        (
            "What does focus mean?",
            "Focus means paying careful attention to what you are doing. It helps you notice the next step instead of getting lost in worry.",
        )
    ],
    "bravery": [
        (
            "Does bravery mean you are never scared?",
            "No. Bravery means doing the right careful thing even when you feel scared. A brave person can have shaky knees and still keep going.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp with a cover around the light. It helps people see and keeps the flame or glow safer in the wind.",
        )
    ],
    "rope": [
        (
            "Why do boats need ropes at a dock?",
            "Ropes keep boats from drifting away when the water moves or the wind blows. A good rope helps a boat stay where it belongs.",
        )
    ],
    "mist": [
        (
            "Why is mist hard to walk through?",
            "Mist makes faraway things look faint and blurry. That can make a path feel longer and more confusing than it really is.",
        )
    ],
    "height": [
        (
            "Why can high places feel scary?",
            "High places can make your body feel small and wobbly. Looking at one safe step at a time can help.",
        )
    ],
    "fairy": [
        (
            "What does a fairy do in a fairy tale?",
            "A fairy often brings help, guidance, or a bit of magic. In many fairy tales, the fairy does not do everything for the hero but helps the hero act bravely.",
        )
    ],
    "song": [
        (
            "How can a song help someone feel calm?",
            "A slow song can match slow breathing. That gives your body a rhythm and makes it easier to think clearly.",
        )
    ],
    "boots": [
        (
            "Why do good boots help on boards or docks?",
            "Good boots can grip the ground better so feet do not slip as easily. Feeling steady underfoot can make a person braver too.",
        )
    ],
}
KNOWLEDGE_ORDER = ["marina", "focus", "bravery", "lantern", "rope", "mist", "height", "fairy", "song", "boots"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle"]
    charm = f["charm"]
    companion = f["companion"]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the words "focus" and "marina" and ends happily.',
        f"Tell a gentle fairy tale where a child named {hero.id} must {obstacle.action} at a marina, and {companion.label} offers {charm.phrase}.",
        f"Write a bravery story in a fairy-tale voice where fear is eased by focus, careful help, and one true step at a time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle"]
    charm = f["charm"]
    companion = f["companion"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child at a marina, and {companion.label} who came to help. Together they tried to save the drifting wish-lantern skiff.",
        ),
        (
            "What problem began the story?",
            f"A puff of wind loosened the skiff rope, so the little lantern boat drifted away from the dock. That mattered because the wish-lantern was meant to shine safely for the harbor that night.",
        ),
        (
            f"What made the task hard for {hero.id}?",
            f"The hard part was {obstacle.label}. {obstacle.danger}",
        ),
        (
            f"How did {hero.id} use focus?",
            f"{hero.id} slowed down, breathed carefully, and paid attention to the next step instead of the whole scary problem. That focus helped fear stop pushing so hard.",
        ),
        (
            f"What help did {companion.label} give?",
            f"{companion.label.capitalize()} offered {charm.phrase} and gentle advice. The help did not replace bravery, but it made the brave choice easier to carry through.",
        ),
    ]
    if outcome == "bold":
        qa.append(
            (
                f"Did {hero.id} do the brave task alone?",
                f"{hero.id} did the hard part with {companion.label} encouraging nearby, and then succeeded with steady courage. The helper offered support, but the brave action itself came from the child.",
            )
        )
    else:
        qa.append(
            (
                f"How did {companion.label} and {hero.id} solve the problem together?",
                f"They worked together to finish the task safely. {companion.label.capitalize()} made the next step easier to see, and {hero.id} still chose to keep going.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            "The lantern skiff was brought safely back, the marina lights shone warmly, and everyone was glad. The ending proves that the child's fear changed into calm bravery.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"marina", "focus", "bravery", "lantern"}
    tags |= set(f["obstacle"].tags)
    tags |= set(f["charm"].tags)
    tags |= set(f["companion"].tags)
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
        bits = [f"type={e.type}"]
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obstacle: Obstacle, charm: Charm, companion: Companion) -> str:
    if not charm_fits(obstacle, charm):
        need = " or ".join(sorted(obstacle.needs))
        helpbits = " / ".join(sorted(charm.helps))
        return (
            f"(No story: {charm.label} helps with {helpbits}, but {obstacle.label} needs help with {need}. "
            f"The fix should match the trouble.)"
        )
    score = support_score(obstacle, charm, companion)
    return (
        f"(No story: {charm.label} with {companion.label} is too weak for {obstacle.label} "
        f"(support={score}, risk={obstacle.risk}). Pick steadier help.)"
    )


ASP_RULES = r"""
fits(O,C) :- obstacle(O), charm(C), need(O,N), helps(C,N).
support(O,C,P,S) :- obstacle(O), charm(C), companion(P),
                    charm_focus(C,CF), charm_courage(C,CC),
                    comp_focus(P,PF), comp_courage(P,PC),
                    S = CF + CC + PF + PC.
valid(O,C,P) :- fits(O,C), support(O,C,P,S), risk(O,R), S >= R.
outcome(O,C,P,bold) :- valid(O,C,P), support(O,C,P,S), risk(O,R), S >= R + 2.
outcome(O,C,P,guided) :- valid(O,C,P), support(O,C,P,S), risk(O,R), S < R + 2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("risk", oid, obstacle.risk))
        for need in sorted(obstacle.needs):
            lines.append(asp.fact("need", oid, need))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("charm_focus", cid, charm.focus_boost))
        lines.append(asp.fact("charm_courage", cid, charm.courage_boost))
        for need in sorted(charm.helps):
            lines.append(asp.fact("helps", cid, need))
    for pid, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", pid))
        lines.append(asp.fact("comp_focus", pid, companion.focus_boost))
        lines.append(asp.fact("comp_courage", pid, companion.courage_boost))
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
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_charm", params.charm),
            asp.fact("chosen_companion", params.companion),
            "picked_outcome(X) :- outcome(O,C,P,X), chosen_obstacle(O), chosen_charm(C), chosen_companion(P).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld at a marina: a child uses focus and bravery to save a drifting lantern skiff."
    )
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.charm and args.companion:
        obstacle = OBSTACLES[args.obstacle]
        charm = CHARMS[args.charm]
        companion = COMPANIONS[args.companion]
        if not valid_combo(obstacle, charm, companion):
            raise StoryError(explain_rejection(obstacle, charm, companion))

    combos = [
        c for c in valid_combos()
        if (args.obstacle is None or c[0] == args.obstacle)
        and (args.charm is None or c[1] == args.charm)
        and (args.companion is None or c[2] == args.companion)
    ]
    if not combos:
        if args.obstacle and args.charm and args.companion:
            raise StoryError(
                explain_rejection(OBSTACLES[args.obstacle], CHARMS[args.charm], COMPANIONS[args.companion])
            )
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, charm_id, companion_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        obstacle=obstacle_id,
        charm=charm_id,
        companion=companion_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.charm not in CHARMS:
        raise StoryError(f"(Unknown charm: {params.charm})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Unknown companion: {params.companion})")
    obstacle = OBSTACLES[params.obstacle]
    charm = CHARMS[params.charm]
    companion = COMPANIONS[params.companion]
    if not valid_combo(obstacle, charm, companion):
        raise StoryError(explain_rejection(obstacle, charm, companion))

    world = tell(obstacle, charm, companion, params.name, params.gender, params.trait)
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)

    bad = []
    for p in cases:
        po = outcome_of(p)
        ao = asp_outcome(p)
        if po != ao:
            bad.append((p, po, ao))
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes: {len(bad)} cases.")
        for p, po, ao in bad[:5]:
            print(" ", p, po, ao)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (obstacle, charm, companion) combos:\n")
        for obstacle, charm, companion in combos:
            score = support_score(OBSTACLES[obstacle], CHARMS[charm], COMPANIONS[companion])
            out = outcome_of(
                StoryParams(
                    obstacle=obstacle,
                    charm=charm,
                    companion=companion,
                    name="Test",
                    gender="girl",
                    trait="careful",
                )
            )
            print(f"  {obstacle:13} {charm:12} {companion:18} support={score} outcome={out}")
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
            header = f"### {p.name}: {p.obstacle} with {p.charm} and {p.companion} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
