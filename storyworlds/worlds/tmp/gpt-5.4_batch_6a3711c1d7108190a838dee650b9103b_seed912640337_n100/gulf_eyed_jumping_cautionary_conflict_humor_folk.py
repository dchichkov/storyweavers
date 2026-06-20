#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gulf_eyed_jumping_cautionary_conflict_humor_folk.py
===============================================================================

A standalone story world for a small folk-tale-like domain built from the seed
words "gulf, eyed, jumping" with Cautionary, Conflict, and Humor.

Premise
-------
In a village near a little gulf or gully, a boastful child sees a tempting prize
on the far side. A cautious companion warns against jumping across. The child
must choose between pride and sense. If the gulf is small enough, a safe crossing
aid lets the pair reach the prize properly. If pride wins, the child may end up
in reeds, mud, or shallow water in a comic but cautionary tumble. The ending
proves what changed: the child either learns to use the safe way, or learns the
hard way that "quick" is not the same as "wise."

Run it
------
    python storyworlds/worlds/gpt-5.4/gulf_eyed_jumping_cautionary_conflict_humor_folk.py
    python storyworlds/worlds/gpt-5.4/gulf_eyed_jumping_cautionary_conflict_humor_folk.py --gulf reedside --prize figs
    python storyworlds/worlds/gpt-5.4/gulf_eyed_jumping_cautionary_conflict_humor_folk.py --gulf sea_cleft --aid stepping_stones
    python storyworlds/worlds/gpt-5.4/gulf_eyed_jumping_cautionary_conflict_humor_folk.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Gulf:
    id: str
    label: str
    phrase: str
    width: int
    surface: str
    safe_landing: str
    comic: str
    can_stones: bool
    can_plank: bool
    can_bridge: bool
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.phrase[0].upper() + self.phrase[1:]


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    scent: str
    hook: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    sense: int
    max_width: int
    usable_on: set[str]
    action: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    sound: str
    antic: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tumble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    gulf = world.get("gulf")
    if child.meters["failed_jump"] < THRESHOLD:
        return out
    sig = ("tumble", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["messy"] += 1
    child.memes["embarrassed"] += 1
    gulf.meters["splashed"] += 1
    out.append("__tumble__")
    return out


def _r_safe_cross(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["crossed_safely"] < THRESHOLD:
        return out
    sig = ("safe_cross", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    out.append("__safe__")
    return out


CAUSAL_RULES = [
    Rule("tumble", "physical", _r_tumble),
    Rule("safe_cross", "social", _r_safe_cross),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def aid_works(aid: Aid, gulf: Gulf) -> bool:
    return aid.sense >= SENSE_MIN and gulf.width <= aid.max_width and gulf.id in aid.usable_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for g in GULFS:
        for p in PRIZES:
            for a in AIDS:
                if aid_works(AIDS[a], GULFS[g]):
                    combos.append((g, p, a))
    return combos


def leap_succeeds(child_stride: int, gulf: Gulf, pride: int) -> bool:
    return child_stride + (1 if pride >= 4 else 0) >= gulf.width


def predicted_outcome(gulf: Gulf, aid: Aid, child_stride: int, pride: int, heed_warning: bool) -> str:
    if heed_warning:
        return "safe"
    return "clean_jump" if leap_succeeds(child_stride, gulf, pride) else "tumble"


def predict_jump(world: World, gulf: Gulf) -> dict:
    sim = world.copy()
    child = sim.get("child")
    pride = int(child.memes["pride"])
    stride = int(child.attrs.get("stride", 1))
    if leap_succeeds(stride, gulf, pride):
        child.meters["crossed_by_jump"] += 1
    else:
        child.meters["failed_jump"] += 1
        propagate(sim, narrate=False)
    return {
        "would_clear": child.meters["crossed_by_jump"] >= THRESHOLD,
        "would_tumble": child.meters["failed_jump"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, elder: Entity, gulf: Gulf, companion: Companion) -> None:
    world.say(
        f"In a village where reeds bowed to the wind, {child.id} and {elder.id} walked one morning beside {gulf.phrase}."
    )
    world.say(
        f"The child had bright, wondering eyes, and even {companion.label} trotted after them, {companion.sound} at every shiny pebble."
    )


def tempt(world: World, child: Entity, prize: Prize, gulf: Gulf) -> None:
    child.memes["desire"] += 1
    child.memes["pride"] += 1
    world.say(
        f"Across the gulf, {prize.phrase} waited among the grass. {child.id} eyed it at once, for {prize.scent}, and said, "
        f'"If I am quick as a swallow, I can be there before the breeze changes."'
    )
    world.say(prize.hook)


def warn(world: World, elder: Entity, child: Entity, gulf: Gulf, companion: Companion) -> None:
    pred = predict_jump(world, gulf)
    world.facts["predicted_tumble"] = pred["would_tumble"]
    elder.memes["caution"] += 1
    if pred["would_tumble"]:
        warning = (
            f'"Feet that boast louder than heads often visit {gulf.surface}. '
            f'Use the safe way, little one."'
        )
    else:
        warning = (
            f'"Even when a jump looks possible, pride likes to nudge an ankle. '
            f'Use the safe way, little one."'
        )
    world.say(
        f"{elder.id} narrowed {elder.pronoun('possessive')} eyes at the gulf and answered, {warning}"
    )
    world.say(
        f"At that, {companion.label} sat down, then looked from the gulf to {child.id} as if even a small beast could smell trouble."
    )


def defy(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} tossed back {child.pronoun("possessive")} head and said, "A long path is for slow geese. I shall cross in one brave spring."'
    )


def choose_aid(world: World, elder: Entity, aid: Aid, gulf: Gulf) -> None:
    world.say(
        f'{elder.id} only tapped the safe way and said, "A wise traveler lets {aid.label} do the boasting."'
    )
    world.say(
        f"Beside {gulf.phrase}, the old village trick was plain enough to see."
    )


def safe_cross(world: World, child: Entity, elder: Entity, aid: Aid, prize: Prize, companion: Companion) -> None:
    child.meters["crossed_safely"] += 1
    propagate(world, narrate=False)
    child.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"So {child.id} stopped talking, took a breath, and {aid.action}."
    )
    world.say(
        f"Soon the child stood on the far side with {prize.label} in hand, while {companion.label} tried to look solemn and failed, for {companion.antic}."
    )
    world.say(
        f"From then on, {child.id} liked to say that the prize tasted better when fetched by sense than by swagger."
    )


def jump_attempt(world: World, child: Entity, gulf: Gulf) -> None:
    stride = int(child.attrs.get("stride", 1))
    pride = int(child.memes["pride"])
    if leap_succeeds(stride, gulf, pride):
        child.meters["crossed_by_jump"] += 1
        child.memes["shock"] += 1
        world.say(
            f"Then, before another word could catch hold of {child.pronoun('object')}, {child.id} came jumping toward the edge, leaped, windmilled both arms, and somehow landed on the far side."
        )
        world.say(
            f"For one blink {child.id} stood very still, as surprised as a rooster that has laid an egg."
        )
    else:
        child.meters["failed_jump"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Then, before another word could catch hold of {child.pronoun('object')}, {child.id} came jumping toward the edge and sprang."
        )
        world.say(
            f"But the gulf kept its own measure. Down went one foot, then the other, and with a grand flap and a startled yelp the child vanished into {gulf.surface}."
        )


def comic_tumble(world: World, child: Entity, elder: Entity, gulf: Gulf, companion: Companion) -> None:
    child.memes["lesson"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"When {child.id} popped up again, {child.pronoun()} was safe, only messy, with {gulf.comic} hanging from {child.pronoun('possessive')} hair."
    )
    world.say(
        f"{companion.label.capitalize()} made such a fuss that it sounded like laughter, and even {elder.id} had to hide a smile behind one hand."
    )
    world.say(
        f'"Now you have crossed exactly nowhere," said {elder.id}. "Will you take the proper way?"'
    )


def after_tumble_safe_way(world: World, child: Entity, elder: Entity, aid: Aid, prize: Prize) -> None:
    child.meters["crossed_safely"] += 1
    propagate(world, narrate=False)
    child.memes["joy"] += 1
    world.say(
        f"Red-faced but wiser, {child.id} nodded, {aid.action}, and crossed without another splash."
    )
    world.say(
        f"On the far side the child gathered {prize.label}, and on the way home not a single boast escaped {child.pronoun('possessive')} mouth."
    )
    world.say(
        f"That evening the village children heard the tale and laughed kindly, and from then on they called the safe route {aid.ending}."
    )


def clean_jump_ending(world: World, child: Entity, elder: Entity, aid: Aid, prize: Prize, companion: Companion) -> None:
    child.memes["lesson"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"{elder.id} crossed after {child.id} by the proper way and said, "
        f'"A lucky jump is not the same as a wise one."'
    )
    world.say(
        f"{child.id} looked back at the gulf, then at {companion.label}, who refused to copy the leap and instead chose the safe route with great dignity."
    )
    world.say(
        f"So the prize came home with them, but the bragging did not. {child.id} never again called wisdom slow."
    )


def tell(gulf: Gulf, prize: Prize, aid: Aid, companion: Companion,
         child_name: str = "Mira", child_gender: str = "girl",
         elder_name: str = "Old Nuri", elder_type: str = "grandmother",
         child_stride: int = 1, pride: int = 3, heed_warning: bool = True) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child",
                             attrs={"stride": child_stride}))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    gulf_ent = world.add(Entity(id="gulf", kind="thing", type="gulf", label=gulf.label))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="prize", label=prize.label))
    world.add(Entity(id="companion", kind="thing", type=companion.id, label=companion.label))

    child.memes["pride"] = float(pride)
    world.facts["heeded"] = heed_warning

    introduce(world, child, elder, gulf, companion)
    world.para()
    tempt(world, child, prize, gulf)
    warn(world, elder, child, gulf, companion)

    world.para()
    if heed_warning:
        choose_aid(world, elder, aid, gulf)
        safe_cross(world, child, elder, aid, prize, companion)
        outcome = "safe"
    else:
        defy(world, child)
        world.para()
        jump_attempt(world, child, gulf)
        if child.meters["failed_jump"] >= THRESHOLD:
            world.para()
            comic_tumble(world, child, elder, gulf, companion)
            after_tumble_safe_way(world, child, elder, aid, prize)
            outcome = "tumble"
        else:
            world.para()
            clean_jump_ending(world, child, elder, aid, prize, companion)
            outcome = "clean_jump"

    world.facts.update(
        gulf=gulf,
        prize_cfg=prize,
        aid=aid,
        companion=companion,
        child=child,
        elder=elder,
        outcome=outcome,
        safe_crossed=child.meters["crossed_safely"] >= THRESHOLD,
        jumped=child.meters["crossed_by_jump"] >= THRESHOLD or child.meters["failed_jump"] >= THRESHOLD,
        messy=child.meters["messy"] >= THRESHOLD,
        lesson=child.memes["lesson"] >= THRESHOLD,
    )
    return world


GULFS = {
    "reedside": Gulf(
        "reedside", "reedy gulf", "the reedy gulf", 2, "the reeds and soft mud",
        "a strip of dry stones", "two green reeds", True, True, False,
        tags={"gulf", "mud", "reeds"},
    ),
    "orchard_rift": Gulf(
        "orchard_rift", "orchard gulf", "the orchard gulf", 3, "the dusty ditch",
        "the old footbridge", "a yellow leaf", False, True, True,
        tags={"gulf", "ditch", "bridge"},
    ),
    "sea_cleft": Gulf(
        "sea_cleft", "sea gulf", "the sea-wind gulf", 4, "the shallow tide pool",
        "the rope bridge", "three silver drops", False, False, True,
        tags={"gulf", "sea", "water"},
    ),
}

PRIZES = {
    "figs": Prize(
        "figs", "figs", "a fat cluster of purple figs", "sweet enough to tease a nose across a field",
        "The leaves twitched as if the figs themselves were whispering, Come and take us if you dare.",
        tags={"fig", "fruit"},
    ),
    "shell": Prize(
        "shell", "a shell", "a spiral shell bright as moon-milk", "salty and curious in the sea air",
        "It gleamed so brightly that it seemed to wink at any child foolish enough to hurry.",
        tags={"shell", "sea"},
    ),
    "dates": Prize(
        "dates", "dates", "a small hanging bunch of dates", "warm and sugary in the noon sun",
        "Even the crows eyed it from the palm and seemed to mutter that patience was cheaper than falling.",
        tags={"date", "fruit"},
    ),
}

AIDS = {
    "stepping_stones": Aid(
        "stepping_stones", "stepping stones", "the stepping stones", 2, 2, {"reedside"},
        "stepped from stone to stone until the far bank held still beneath the child's feet",
        "the Stone-To-Stone Way",
        tags={"stones", "crossing"},
    ),
    "plank": Aid(
        "plank", "a plank", "the old plank", 2, 3, {"reedside", "orchard_rift"},
        "laid the plank straight, tested it with one cautious toe, and walked across",
        "the Quiet Plank",
        tags={"plank", "crossing"},
    ),
    "rope_bridge": Aid(
        "rope_bridge", "the rope bridge", "the rope bridge", 3, 4, {"orchard_rift", "sea_cleft"},
        "took the rope bridge slowly, hand over hand, while the boards creaked like sleepy crows",
        "the Wise Bridge",
        tags={"bridge", "crossing"},
    ),
    "jump": Aid(
        "jump", "a jump", "a jump", 0, 9, {"reedside", "orchard_rift", "sea_cleft"},
        "jumped",
        "the Fool's Shortcut",
        tags={"jump"},
    ),
}

COMPANIONS = {
    "goat": Companion("goat", "the goat", "bleating softly", "it was chewing the elder's scarf tassel"),
    "duck": Companion("duck", "the duck", "quacking under its breath", "it waddled in a circle as if announcing a parade"),
    "monkey": Companion("monkey", "the monkey", "chittering sharply", "it clapped both tiny hands at the wrong moment"),
}

GIRL_NAMES = ["Mira", "Laleh", "Suri", "Nima", "Tala", "Rana"]
BOY_NAMES = ["Amin", "Yusuf", "Tarin", "Sami", "Basil", "Rafi"]
ELDERS = [
    ("Old Nuri", "grandmother"),
    ("Grandfather Kem", "grandfather"),
]
PRIDE_LEVELS = [2, 3, 4]
STRIDES = [1, 2, 3]


@dataclass
class StoryParams:
    gulf: str
    prize: str
    aid: str
    companion: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
    child_stride: int
    pride: int
    heed_warning: bool
    seed: Optional[int] = None


KNOWLEDGE = {
    "gulf": [
        ("What is a gulf in this story?",
         "Here, a gulf is a gap in the ground or shore that is hard to cross in one step. A small gulf can still be dangerous when the landing is muddy or slippery."),
    ],
    "reeds": [
        ("What are reeds?",
         "Reeds are tall, thin plants that grow near water or wet ground. They bend in the wind and can hide mud underneath them."),
    ],
    "bridge": [
        ("Why is a bridge safer than a jump?",
         "A bridge gives your feet a path to follow instead of asking your body to fly. When the ground is tricky, a steady path is wiser than a brave guess."),
    ],
    "plank": [
        ("What does a plank do?",
         "A plank is a long flat board that can make a simple path over a small gap. It only helps when the gap is short enough and the board can lie steady."),
    ],
    "stones": [
        ("What are stepping stones for?",
         "Stepping stones give you little places to put your feet across wet ground or water. They help you cross slowly and safely, one step at a time."),
    ],
    "sea": [
        ("Why can sea edges be slippery?",
         "Sea spray and smooth stones can make the edge wet and slick. That means a person can lose footing even if the distance does not look frightening."),
    ],
    "fruit": [
        ("Why can fruit tempt someone to hurry?",
         "Good fruit smells sweet and promises an easy reward. Sometimes wanting something quickly makes people forget to think carefully."),
    ],
    "crossing": [
        ("Why is slow crossing sometimes better?",
         "Slow crossing lets you test each step and keep your balance. A careful path can save you from a fast mistake."),
    ],
    "jump": [
        ("Is a lucky jump the same as a wise choice?",
         "No. A lucky jump only means nothing bad happened that time. A wise choice is safe on purpose, not by accident."),
    ],
}
KNOWLEDGE_ORDER = ["gulf", "reeds", "sea", "fruit", "stones", "plank", "bridge", "crossing", "jump"]


def pair_kind(child: Entity, elder: Entity) -> str:
    return f"{child.id} and {elder.id}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    gulf = f["gulf"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    if outcome == "tumble":
        return [
            f'Write a humorous folk tale for a 3-to-5-year-old that includes the words "gulf", "eyed", and "jumping". A child wants {prize.label} across {gulf.phrase}, ignores an elder, tumbles safely, and learns a cautionary lesson.',
            f"Tell a folk-style cautionary story where {child.id} eyed {prize.label} across {gulf.phrase}, tried jumping over it, and ended up embarrassed but wiser.",
            f"Write a conflict story with gentle humor: a proud child argues with an elder about the quickest way across a gulf, then learns to choose the safe way.",
        ]
    if outcome == "clean_jump":
        return [
            f'Write a folk tale that includes "gulf", "eyed", and "jumping", where a child makes a dangerous leap across {gulf.phrase} but still learns that luck is not wisdom.',
            f"Tell a cautionary story where {child.id} disobeys {elder.id}, reaches {prize.label} by jumping, and is told that a lucky jump is not a wise choice.",
            f"Write a child-facing folk story with conflict and a humorous animal companion, ending in a lesson about pride.",
        ]
    return [
        f'Write a gentle folk tale for a 3-to-5-year-old that includes the words "gulf", "eyed", and "jumping", where an elder talks a child out of a dangerous leap and guides the child across safely.',
        f"Tell a cautionary folk story where {child.id} eyed {prize.label} across {gulf.phrase}, but chose the safe crossing instead of jumping.",
        f"Write a small humorous conflict story in which a child wants the quick way across a gulf and learns that wisdom can walk slowly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    gulf = f["gulf"]
    prize = f["prize_cfg"]
    aid = f["aid"]
    companion = f["companion"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {pair_kind(child, elder)} near {gulf.phrase}, with {companion.label} tagging along. The child wanted something tempting on the far side."),
        (f"What did {child.id} want?",
         f"{child.id} wanted {prize.label} from the far side of {gulf.phrase}. The prize looked close enough to tempt a quick, proud choice."),
        (f"Why did {elder.id} warn {child.id}?",
         f"{elder.id} warned {child.id} because the gulf was risky to cross by a leap. The warning came from seeing that pride and slippery ground can turn a quick plan into a bad tumble."),
    ]
    if outcome == "safe":
        qa.append((
            f"What happened after {child.id} listened?",
            f"{child.id} stopped boasting and used {aid.label} to cross safely. The story ends happily because the child chose a careful path instead of showing off."
        ))
        qa.append((
            f"How did the story show the lesson?",
            f"The lesson showed in the ending image: {child.id} reached the prize without falling and admitted that sense was better than swagger. The change is that the child began the story hungry for a quick leap and ended it respecting the safe way."
        ))
    elif outcome == "tumble":
        qa.append((
            f"What happened when {child.id} tried jumping?",
            f"{child.id} failed to clear the gulf and tumbled into {gulf.surface}, though the child was still safe. The fall was funny to hear about, but it also proved the elder's warning was true."
        ))
        qa.append((
            f"How was the ending both funny and cautionary?",
            f"It was funny because {child.id} came up messy with {gulf.comic} stuck in {child.pronoun('possessive')} hair while {companion.label} made a noisy fuss. It was cautionary because after the tumble the child used {aid.label} and stopped boasting."
        ))
    else:
        qa.append((
            f"Did jumping work for {child.id}?",
            f"Yes, the leap happened to work that time, and {child.id} landed on the far side. But the story still calls it unwise, because luck is not the same as a safe plan."
        ))
        qa.append((
            f"What lesson did {elder.id} give after the jump?",
            f"{elder.id} said that a lucky jump is not the same as a wise one. The child reached the prize, but the real change was learning not to brag about a dangerous shortcut."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["gulf"].tags) | set(f["prize_cfg"].tags) | set(f["aid"].tags)
    tags.add("gulf")
    if "ditch" in tags or "reeds" in tags:
        tags.add("reeds")
    if "sea" in tags or f["gulf"].id == "sea_cleft":
        tags.add("sea")
    if "fig" in tags or "date" in tags or "fruit" in tags:
        tags.add("fruit")
    if "stones" in tags:
        tags.add("stones")
    if "plank" in tags:
        tags.add("plank")
    if "bridge" in tags:
        tags.add("bridge")
    if "crossing" in tags:
        tags.add("crossing")
    if f["outcome"] in {"tumble", "clean_jump"} or f["aid"].id == "jump":
        tags.add("jump")
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


CURATED = [
    StoryParams("reedside", "figs", "stepping_stones", "goat", "Mira", "girl",
                "Old Nuri", "grandmother", 1, 3, True),
    StoryParams("orchard_rift", "dates", "plank", "duck", "Rafi", "boy",
                "Grandfather Kem", "grandfather", 2, 4, False),
    StoryParams("sea_cleft", "shell", "rope_bridge", "monkey", "Tala", "girl",
                "Old Nuri", "grandmother", 3, 4, False),
    StoryParams("sea_cleft", "shell", "rope_bridge", "duck", "Amin", "boy",
                "Grandfather Kem", "grandfather", 2, 2, True),
]


def explain_rejection(gulf: Gulf, aid: Aid) -> str:
    if aid.sense < SENSE_MIN:
        return (
            f"(No story: '{aid.id}' is the foolish shortcut, not the sensible crossing. "
            f"Pick a real aid such as stepping_stones, plank, or rope_bridge.)"
        )
    if gulf.width > aid.max_width:
        return (
            f"(No story: {aid.label} is too slight for {gulf.phrase}. "
            f"The gulf is wider than that aid can reasonably cover.)"
        )
    if gulf.id not in aid.usable_on:
        return (
            f"(No story: {aid.label} does not fit {gulf.phrase}. "
            f"Choose an aid that villagers would really use there.)"
        )
    return "(No story: this combination is not a reasonable crossing.)"


def outcome_of(params: StoryParams) -> str:
    if params.heed_warning:
        return "safe"
    return "clean_jump" if leap_succeeds(params.child_stride, GULFS[params.gulf], params.pride) else "tumble"


ASP_RULES = r"""
valid(G, P, A) :- gulf(G), prize(P), aid(A), sensible(A), usable_on(A, G),
                  gulf_width(G, W), aid_max(A, M), W <= M.

outcome(safe) :- heed_warning.
jump_bonus(1) :- pride(P), P >= 4.
jump_bonus(0) :- pride(P), P < 4.
jump_power(S + B) :- stride(S), jump_bonus(B).
clean_jump :- not heed_warning, chosen_gulf(G), gulf_width(G, W), jump_power(P), P >= W.
outcome(clean_jump) :- clean_jump.
outcome(tumble) :- not heed_warning, not clean_jump.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid, gulf in GULFS.items():
        lines.append(asp.fact("gulf", gid))
        lines.append(asp.fact("gulf_width", gid, gulf.width))
        if gulf.can_stones:
            lines.append(asp.fact("supports", gid, "stones"))
        if gulf.can_plank:
            lines.append(asp.fact("supports", gid, "plank"))
        if gulf.can_bridge:
            lines.append(asp.fact("supports", gid, "bridge"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("aid_max", aid_id, aid.max_width))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        if aid.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", aid_id))
        for gid in sorted(aid.usable_on):
            lines.append(asp.fact("usable_on", aid_id, gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra_lines = [
        asp.fact("chosen_gulf", params.gulf),
        asp.fact("stride", params.child_stride),
        asp.fact("pride", params.pride),
    ]
    if params.heed_warning:
        extra_lines.append("heed_warning.")
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a folk-tale child, a tempting gulf, a warning, and the safe way.")
    ap.add_argument("--gulf", choices=GULFS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--heed-warning", dest="heed_warning", action="store_true",
                    help="force the child to listen to the elder")
    ap.add_argument("--ignore-warning", dest="heed_warning", action="store_false",
                    help="force the child to ignore the elder")
    ap.set_defaults(heed_warning=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid and args.aid == "jump":
        raise StoryError(explain_rejection(GULFS[args.gulf] if args.gulf else next(iter(GULFS.values())), AIDS["jump"]))
    if args.gulf and args.aid and not aid_works(AIDS[args.aid], GULFS[args.gulf]):
        raise StoryError(explain_rejection(GULFS[args.gulf], AIDS[args.aid]))

    combos = [
        c for c in valid_combos()
        if (args.gulf is None or c[0] == args.gulf)
        and (args.prize is None or c[1] == args.prize)
        and (args.aid is None or c[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    gulf_id, prize_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_name, elder_type = rng.choice(ELDERS)
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    heed_warning = args.heed_warning if args.heed_warning is not None else rng.choice([True, False])
    gulf = GULFS[gulf_id]
    stride = rng.choice([s for s in STRIDES if s <= gulf.width or s == gulf.width - 1 or s == gulf.width - 2] or STRIDES)
    pride = rng.choice(PRIDE_LEVELS)
    return StoryParams(
        gulf=gulf_id,
        prize=prize_id,
        aid=aid_id,
        companion=companion,
        child_name=child_name,
        child_gender=gender,
        elder_name=elder_name,
        elder_type=elder_type,
        child_stride=max(1, min(3, stride)),
        pride=pride,
        heed_warning=heed_warning,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        GULFS[params.gulf],
        PRIZES[params.prize],
        AIDS[params.aid],
        COMPANIONS[params.companion],
        params.child_name,
        params.child_gender,
        params.elder_name,
        params.elder_type,
        params.child_stride,
        params.pride,
        params.heed_warning,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            continue

    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (gulf, prize, aid) combos:\n")
        for gulf, prize, aid in combos:
            print(f"  {gulf:12} {prize:8} {aid}")
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
            header = f"### {p.child_name}: {p.gulf}, {p.prize}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
