#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cypress_bravery_fairy_tale.py
========================================================

A small fairy-tale storyworld about bravery in a cypress grove.

A child is given a gentle quest that leads through a cypress grove. The grove
holds one specific trouble: a dark patch under the trees, a silver mist that
splits the path, or a little stream that must be crossed. The elder gives a
fitting helper, and the child must feel afraid, choose to go on anyway, and use
the helper in a sensible way.

The world model tracks physical meters (distance, darkness, mist, balance,
crossed, delivered) and emotional memes (fear, courage, trust, relief, pride).
The prose is rendered from that changing state rather than from one frozen
template.

Run it
------
    python storyworlds/worlds/gpt-5.4/cypress_bravery_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/cypress_bravery_fairy_tale.py --quest bell --obstacle mist --helper thread
    python storyworlds/worlds/gpt-5.4/cypress_bravery_fairy_tale.py --obstacle stream --helper lantern
    python storyworlds/worlds/gpt-5.4/cypress_bravery_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/cypress_bravery_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/cypress_bravery_fairy_tale.py --verify
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
        female = {"girl", "mother", "aunt", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "aunt": "aunt",
            "queen": "queen",
        }.get(self.type, self.label or self.type)


@dataclass
class Quest:
    id: str
    errand: str = ""
    gift: str = ""
    destination: str = ""
    image: str = ""
    thanks: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str = ""
    need: str = ""
    fear_text: str = ""
    turn_text: str = ""
    solved_text: str = ""
    scare: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str = ""
    phrase: str = ""
    provides: str = ""
    use_text: str = ""
    proof_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Grove:
    id: str
    label: str = ""
    opening: str = ""
    whisper: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    grove: str
    quest: str
    obstacle: str
    helper: str
    hero_name: str
    hero_gender: str
    elder_type: str
    heart: str
    seed: Optional[int] = None


GROVES = {
    "cypress": Grove(
        id="cypress",
        label="the cypress grove",
        opening="Beyond the last cottage stood a cypress grove, dark-green and tall, with trunks like quiet pillars.",
        whisper="The cypress boughs spoke in a soft hiss above the path, as if the trees were trading old secrets.",
        ending="At the end, the cypress branches no longer sounded like warnings. They sounded like applause.",
        tags={"cypress", "grove"},
    ),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        errand="carry the little silver bell",
        gift="a little silver bell",
        destination="the hill shrine beyond the grove",
        image="hang the bell where the dawn wind could ring it",
        thanks="the first note of morning flew across the hills like a bright bird",
        tags={"bell", "shrine"},
    ),
    "bread": Quest(
        id="bread",
        errand="bring a round loaf of honey bread",
        gift="a round loaf of honey bread wrapped in cloth",
        destination="Grandmother's lamp-lit cottage beyond the grove",
        image="set the warm loaf on Grandmother's blue table",
        thanks="the cottage smelled of honey and cedar, and the old woman smiled as if winter itself had stepped back",
        tags={"bread", "grandmother"},
    ),
    "ribbon": Quest(
        id="ribbon",
        errand="return the moon ribbon",
        gift="the pale moon ribbon",
        destination="the stone well beyond the grove",
        image="lay the ribbon on the well rim where moonlight could drink from it",
        thanks="the water shone silver, and even the stars seemed to lean closer",
        tags={"ribbon", "well"},
    ),
}

OBSTACLES = {
    "dark": Obstacle(
        id="dark",
        label="the darkest bend",
        need="light",
        fear_text="Soon the path bent under the thickest cypress branches, and the world went dim as a shut box.",
        turn_text="For a moment, fear fluttered in the child's chest like a trapped sparrow.",
        solved_text="Light spilled over the roots, and the dark bend became only a path again.",
        scare=2,
        tags={"dark", "light"},
    ),
    "mist": Obstacle(
        id="mist",
        label="the silver mist fork",
        need="guide",
        fear_text="Soon a silver mist slipped between the cypress trunks and copied the path into two pale roads.",
        turn_text="The two roads looked so alike that the child's knees felt watery.",
        solved_text="The true path showed itself, thin and honest beneath the trees.",
        scare=3,
        tags={"mist", "path"},
    ),
    "stream": Obstacle(
        id="stream",
        label="the singing stream",
        need="balance",
        fear_text="Soon the child reached a narrow stream where the stepping stones shone slick as fish scales.",
        turn_text="The little water laughed around the stones, and the child's heart beat fast at the thought of slipping.",
        solved_text="Step by careful step, the crossing held firm, and the stream was behind.",
        scare=3,
        tags={"stream", "crossing"},
    ),
}

HELPERS = {
    "lantern": Helper(
        id="lantern",
        label="lantern",
        phrase="a star-glass lantern",
        provides="light",
        use_text="The child lifted the star-glass lantern, and its warm gold light opened a small brave room in the dark.",
        proof_text="Its shine turned the black roots into ordinary roots and the shadows into only shadows.",
        tags={"lantern", "light"},
    ),
    "fireflies": Helper(
        id="fireflies",
        label="firefly jar",
        phrase="a jar of sleepy fireflies",
        provides="light",
        use_text="The child cupped the jar of sleepy fireflies, and little green lights woke and floated against the glass.",
        proof_text="Their glow stitched the path together so the feet could trust it.",
        tags={"fireflies", "light"},
    ),
    "thread": Helper(
        id="thread",
        label="red thread",
        phrase="a red thread on a wooden spool",
        provides="guide",
        use_text="The child unwound the red thread, and it lay straight along the true path like a brave little promise.",
        proof_text="It would not wander into the false road, not even when the mist tried to hide the way.",
        tags={"thread", "guide"},
    ),
    "lark": Helper(
        id="lark",
        label="white lark feather",
        phrase="a white lark feather",
        provides="guide",
        use_text="The child held up the white lark feather, and it trembled toward the honest road as if it could feel morning.",
        proof_text="The feather pointed ahead each time the mist tried to trick the eyes.",
        tags={"feather", "guide"},
    ),
    "staff": Helper(
        id="staff",
        label="willow staff",
        phrase="a willow staff smooth as milk",
        provides="balance",
        use_text="The child set the willow staff before each step and let it test the stones first.",
        proof_text="With every careful tap, the crossing felt steadier and less wild.",
        tags={"staff", "balance"},
    ),
    "shoes": Helper(
        id="shoes",
        label="moss shoes",
        phrase="moss-soft crossing shoes",
        provides="balance",
        use_text="The child tied on the moss-soft crossing shoes, and the soles held the stones gently instead of sliding.",
        proof_text="The wet rocks still gleamed, but they no longer seemed eager to throw small feet into the stream.",
        tags={"shoes", "balance"},
    ),
}

HEARTS = {
    "gentle": 2,
    "steady": 3,
    "bold": 4,
}

GIRL_NAMES = ["Elin", "Mira", "Tessa", "Nora", "Lina", "Sera"]
BOY_NAMES = ["Tobin", "Rowan", "Finn", "Alder", "Milo", "Perrin"]
ELDERS = ["mother", "father", "aunt"]


def helper_fits(obstacle: Obstacle, helper: Helper) -> bool:
    return obstacle.need == helper.provides


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for grove_id in GROVES:
        for quest_id in QUESTS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for helper_id, helper in HELPERS.items():
                    if helper_fits(obstacle, helper):
                        combos.append((grove_id, quest_id, obstacle_id, helper_id))
    return combos


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


def _r_fear(world: World) -> list[str]:
    hero = world.get("hero")
    grove = world.get("grove")
    obstacle = world.get("obstacle")
    if obstacle.meters["active"] < THRESHOLD:
        return []
    sig = ("fear", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += float(world.facts["obstacle_cfg"].scare)
    grove.meters["hush"] += 1
    return []


def _r_help(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    obstacle = world.get("obstacle")
    if helper.meters["used"] < THRESHOLD or obstacle.meters["active"] < THRESHOLD:
        return []
    sig = ("help", helper.id, obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 2
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    obstacle.meters["softened"] += 1
    return []


def _r_cross(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    if obstacle.meters["softened"] < THRESHOLD:
        return []
    sig = ("cross", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["progress"] += 1
    hero.meters["crossed"] += 1
    obstacle.meters["active"] = 0.0
    hero.memes["relief"] += 1
    return []


def _r_deliver(world: World) -> list[str]:
    hero = world.get("hero")
    quest_item = world.get("gift")
    if hero.meters["crossed"] < THRESHOLD:
        return []
    sig = ("deliver", quest_item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["arrived"] += 1
    quest_item.meters["delivered"] += 1
    hero.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="help", tag="emotional", apply=_r_help),
    Rule(name="cross", tag="physical", apply=_r_cross),
    Rule(name="deliver", tag="physical", apply=_r_deliver),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        if not changed:
            break
        changed = any(True for _ in [1] if False) or False
        for rule in CAUSAL_RULES:
            if any(sig[0] == rule.name for sig in world.fired):
                continue
        # The rules themselves mutate state; loop again until no new firing occurs.
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            lines = rule.apply(world)
            if lines:
                produced.extend(lines)
            if len(world.fired) > before:
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def courage_total(heart: str, obstacle: Obstacle) -> int:
    return HEARTS[heart] + 1 + 2


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    if not helper_fits(obstacle, helper):
        return "invalid"
    return "brave" if courage_total(params.heart, obstacle) >= obstacle.scare + 1 else "turn_back"


def predict_crossing(hero_heart: str, obstacle: Obstacle, helper: Helper) -> dict:
    fits = helper_fits(obstacle, helper)
    courage = HEARTS[hero_heart] + 1 + (2 if fits else 0)
    return {
        "fits": fits,
        "courage": courage,
        "success": courage >= obstacle.scare + 1,
    }


def introduce(world: World, grove: Grove, hero: Entity, elder: Entity, quest: Quest) -> None:
    world.say(f"Once, at the edge of {grove.label}, there lived a child named {hero.id}.")
    world.say(grove.opening)
    world.say(
        f"One evening, {hero.id}'s {elder.label_word} placed {quest.gift} in {hero.pronoun('possessive')} hands and asked {hero.pronoun('object')} to {quest.errand} to {quest.destination}."
    )
    world.say(
        f'"The road is not wicked," said the {elder.label_word}, "but it asks for a brave heart."'
    )


def gift_helper(world: World, hero: Entity, elder: Entity, helper: Helper, obstacle: Obstacle, heart: str) -> None:
    pred = predict_crossing(heart, obstacle, helper)
    world.facts["predicted_courage"] = pred["courage"]
    world.say(
        f'Then the {elder.label_word} gave {hero.pronoun("object")} {helper.phrase}. "{helper.label.capitalize()} for the hard part," {elder.pronoun()} said.'
    )
    world.say(
        f'"Bravery is not having no fear. Bravery is carrying your fear and walking kindly anyway."'
    )
    hero.memes["trust"] += 1


def enter_grove(world: World, grove: Grove, hero: Entity, quest: Quest) -> None:
    world.say(
        f"So {hero.id} set out beneath the cypress trees, meaning to {quest.image}."
    )
    world.say(grove.whisper)
    hero.meters["distance"] += 1


def face_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.get("obstacle").meters["active"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.fear_text)
    if hero.memes["fear"] >= THRESHOLD:
        world.say(obstacle.turn_text)


def choose_bravery(world: World, hero: Entity, helper: Helper) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} wanted to run back to the cottage door. Instead, {hero.pronoun()} took one slow breath and remembered every word."
    )
    world.say(helper.use_text)
    world.get("helper").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(helper.proof_text)
    world.say(world.facts["obstacle_cfg"].solved_text)


def deliver(world: World, hero: Entity, quest: Quest) -> None:
    propagate(world, narrate=False)
    world.say(
        f"At last {hero.id} came to {quest.destination} and did exactly what {hero.pronoun('possessive')} promise had asked."
    )
    world.say(
        f"{hero.pronoun().capitalize()} {quest.image}, and {quest.thanks}."
    )


def close_story(world: World, grove: Grove, hero: Entity, elder: Entity) -> None:
    world.say(
        f"When {hero.id} came home again, the {elder.label_word} saw at once that something small and shining had changed."
    )
    world.say(
        f'{hero.id} was still the same child, but now {hero.pronoun("possessive")} steps knew what they could do.'
    )
    world.say(grove.ending)


def tell(
    grove: Grove,
    quest: Quest,
    obstacle: Obstacle,
    helper: Helper,
    hero_name: str,
    hero_gender: str,
    elder_type: str,
    heart: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    grove_ent = world.add(Entity(id="grove", type="grove", label=grove.label, role="place", tags=set(grove.tags)))
    gift = world.add(Entity(id="gift", type="gift", label=quest.gift, phrase=quest.gift, role="gift", tags=set(quest.tags)))
    obstacle_ent = world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label, role="obstacle", tags=set(obstacle.tags)))
    helper_ent = world.add(Entity(id="helper", type="helper", label=helper.label, phrase=helper.phrase, role="helper", tags=set(helper.tags)))

    hero.attrs["name"] = hero_name
    hero.attrs["heart"] = heart
    hero.memes["courage"] = float(HEARTS[heart])

    world.facts.update(
        grove_cfg=grove,
        quest_cfg=quest,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        hero=hero,
        elder=elder,
        gift=gift,
        outcome="brave",
    )

    introduce(world, grove, hero, elder, quest)
    world.para()
    gift_helper(world, hero, elder, helper, obstacle, heart)
    enter_grove(world, grove, hero, quest)
    world.para()
    face_obstacle(world, hero, obstacle)
    choose_bravery(world, hero, helper)
    world.para()
    deliver(world, hero, quest)
    close_story(world, grove, hero, elder)
    world.facts["crossed"] = hero.meters["crossed"] >= THRESHOLD
    world.facts["fear"] = hero.memes["fear"]
    world.facts["courage"] = hero.memes["courage"]
    world.facts["pride"] = hero.memes["pride"]
    return world


KNOWLEDGE = {
    "cypress": [
        (
            "What is a cypress tree?",
            "A cypress is a tall evergreen tree with soft, feathery branches. Many cypress trees stay green all year.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light you can carry with you. It helps people see when a place is dark.",
        )
    ],
    "fireflies": [
        (
            "What are fireflies?",
            "Fireflies are tiny insects that can glow in the dark. Their little lights can look like floating stars.",
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a very thin cloud close to the ground. It can make it hard to see the path ahead.",
        )
    ],
    "stream": [
        (
            "What is a stream?",
            "A stream is a small moving flow of water. Stones in a stream can be slippery.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery does not mean you never feel scared. It means you choose the good and careful thing even while you are scared.",
        )
    ],
    "staff": [
        (
            "What can a walking staff do?",
            "A walking staff can help you balance and test the ground in front of you. That makes careful steps safer.",
        )
    ],
    "thread": [
        (
            "Why might a thread help someone find a path?",
            "A bright thread can mark the true way so you do not get lost. It gives your eyes something simple to follow.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cypress", "bravery", "mist", "stream", "lantern", "fireflies", "staff", "thread"]


def generation_prompts(world: World) -> list[str]:
    quest = world.facts["quest_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper_cfg"]
    hero = world.facts["hero"]
    name = hero.attrs["name"]
    return [
        'Write a short fairy tale for a 3-to-5-year-old that includes the word "cypress" and centers on bravery.',
        f"Tell a fairy tale where a child named {name} must {quest.errand} through a cypress grove, feels afraid at {obstacle.label}, and uses {helper.label} to go on.",
        f"Write a gentle story in fairy-tale style showing that bravery is not the same as having no fear, and end with the child changed by the journey.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    quest = world.facts["quest_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper_cfg"]
    name = hero.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a child named {name} who had to walk through a cypress grove. {elder.label_word.capitalize()} sent {hero.pronoun('object')} on a small but important errand.",
        ),
        (
            f"What was {name} asked to do?",
            f"{name} was asked to {quest.errand} to {quest.destination}. The journey mattered because {hero.pronoun()} had given a promise.",
        ),
        (
            f"What scared {name} in the grove?",
            f"{obstacle.fear_text} That moment made {name} feel afraid, because the grove suddenly seemed larger and more uncertain.",
        ),
        (
            f"How did {name} show bravery?",
            f"{name} did not stop being scared. Instead, {hero.pronoun()} remembered the elder's words, used {helper.label}, and kept going carefully.",
        ),
        (
            f"How did {helper.label} help?",
            f"{helper.proof_text} Because the helper matched the trouble in the grove, it turned a frightening moment into one the child could manage.",
        ),
        (
            "How did the story end?",
            f"{name} reached {quest.destination} and kept the promise. When {hero.pronoun()} came home, the child felt prouder and surer than before.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"cypress", "bravery"}
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label and ent.id == "hero":
            bits.append(f"name={ent.label}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        grove="cypress",
        quest="bell",
        obstacle="dark",
        helper="lantern",
        hero_name="Elin",
        hero_gender="girl",
        elder_type="aunt",
        heart="gentle",
    ),
    StoryParams(
        grove="cypress",
        quest="bread",
        obstacle="mist",
        helper="thread",
        hero_name="Tobin",
        hero_gender="boy",
        elder_type="mother",
        heart="steady",
    ),
    StoryParams(
        grove="cypress",
        quest="ribbon",
        obstacle="stream",
        helper="staff",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="father",
        heart="bold",
    ),
    StoryParams(
        grove="cypress",
        quest="bell",
        obstacle="mist",
        helper="lark",
        hero_name="Rowan",
        hero_gender="boy",
        elder_type="aunt",
        heart="steady",
    ),
]


def explain_rejection(obstacle: Obstacle, helper: Helper) -> str:
    return (
        f"(No story: {helper.label} does not sensibly solve {obstacle.label}. "
        f"This obstacle needs help with {obstacle.need}, so choose a helper that provides {obstacle.need}.)"
    )


ASP_RULES = r"""
valid(G, Q, O, H) :- grove(G), quest(Q), obstacle(O), helper(H), needs(O, N), provides(H, N).

heart_value(gentle, 2).
heart_value(steady, 3).
heart_value(bold, 4).

base_bonus(3).
courage_total(Ht, O, T) :- heart_value(Ht, V), base_bonus(B), T = V + B, obstacle(O).
brave(Ht, O, H) :- needs(O, N), provides(H, N), courage_total(Ht, O, T), scare(O, S), T >= S + 1.

outcome(brave) :- chosen_heart(Ht), chosen_obstacle(O), chosen_helper(H), brave(Ht, O, H).
outcome(turn_back) :- chosen_heart(Ht), chosen_obstacle(O), chosen_helper(H), not brave(Ht, O, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for grove_id in GROVES:
        lines.append(asp.fact("grove", grove_id))
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
        lines.append(asp.fact("scare", obstacle_id, obstacle.scare))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("provides", helper_id, helper.provides))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_heart", params.heart),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = []
    for params in cases:
        a = asp_outcome(params)
        b = outcome_of(params)
        if a != b:
            mismatches.append((params, a, b))
    if not mismatches:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, a, b in mismatches[:5]:
            print(f"  {params} -> asp={a} python={b}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld about bravery in a cypress grove."
    )
    ap.add_argument("--grove", choices=GROVES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--heart", choices=sorted(HEARTS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if not helper_fits(obstacle, helper):
            raise StoryError(explain_rejection(obstacle, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.grove is None or combo[0] == args.grove)
        and (args.quest is None or combo[1] == args.quest)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    grove_id, quest_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(ELDERS)
    heart = args.heart or rng.choice(sorted(HEARTS))
    params = StoryParams(
        grove=grove_id,
        quest=quest_id,
        obstacle=obstacle_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        heart=heart,
    )
    if outcome_of(params) != "brave":
        raise StoryError("(No story: this child would not plausibly cross the grove in this telling.)")
    return params


def generate(params: StoryParams) -> StorySample:
    if params.grove not in GROVES:
        raise StoryError(f"(Invalid grove: {params.grove})")
    if params.quest not in QUESTS:
        raise StoryError(f"(Invalid quest: {params.quest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.elder_type not in ELDERS:
        raise StoryError(f"(Invalid elder type: {params.elder_type})")
    if params.heart not in HEARTS:
        raise StoryError(f"(Invalid heart: {params.heart})")

    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    if not helper_fits(obstacle, helper):
        raise StoryError(explain_rejection(obstacle, helper))

    world = tell(
        grove=GROVES[params.grove],
        quest=QUESTS[params.quest],
        obstacle=obstacle,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        heart=params.heart,
    )

    story_text = world.render().replace("hero", params.hero_name)
    story_text = story_text.replace("elder", params.elder_type)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (grove, quest, obstacle, helper) combos:\n")
        for grove_id, quest_id, obstacle_id, helper_id in combos:
            print(f"  {grove_id:8} {quest_id:8} {obstacle_id:8} {helper_id}")
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
            header = f"### {p.hero_name}: {p.quest} through {p.obstacle} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
