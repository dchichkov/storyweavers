#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/worship_elapse_conflict_rhyme_rhyming_story.py
==========================================================================

A standalone story world for gentle rhyming stories about children preparing
flowers for morning worship. The tension is small and child-sized: one child is
too eager and wants the buds open right away, while another child understands
that some things need time to wake. A few minutes elapse, the right kind of
care is given, and the ending image shows what patience changed.

Run it
------
python storyworlds/worlds/gpt-5.4/worship_elapse_conflict_rhyme_rhyming_story.py
python storyworlds/worlds/gpt-5.4/worship_elapse_conflict_rhyme_rhyming_story.py --place courtyard --bloom daisy --method sun_tray
python storyworlds/worlds/gpt-5.4/worship_elapse_conflict_rhyme_rhyming_story.py --method pull_petals
python storyworlds/worlds/gpt-5.4/worship_elapse_conflict_rhyme_rhyming_story.py --all --qa
python storyworlds/worlds/gpt-5.4/worship_elapse_conflict_rhyme_rhyming_story.py --verify
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
HASTE_INIT = 6.0
PATIENT_TRAITS = {"patient", "careful", "gentle", "thoughtful"}


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
class Place:
    id: str
    label: str
    scene: str
    altar: str
    dawn_line: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Bloom:
    id: str
    label: str
    phrase: str
    plural_label: str
    need: str
    open_line: str
    scent_line: str
    worship_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    supports: set[str] = field(default_factory=set)
    setup_line: str = ""
    wait_line: str = ""
    qa_line: str = ""
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"eager", "steady"}]

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


def _r_bruise_sadness(world: World) -> list[str]:
    blooms = world.get("blooms")
    eager = world.get("eager")
    if blooms.meters["bruised"] < THRESHOLD:
        return []
    sig = ("bruise_sadness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    eager.memes["regret"] += 1
    return []


def _r_open_fragrance(world: World) -> list[str]:
    blooms = world.get("blooms")
    if blooms.meters["open"] < THRESHOLD:
        return []
    sig = ("open_fragrance",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    blooms.meters["fragrance"] += 1
    for child in world.children():
        child.memes["wonder"] += 1
        child.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="bruise_sadness", tag="emotional", apply=_r_bruise_sadness),
    Rule(name="open_fragrance", tag="physical", apply=_r_open_fragrance),
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
        if any(rule.apply(world) for rule in []):
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def bloom_ready(place: Place, bloom: Bloom, method: Method) -> bool:
    return bloom.need in place.affords and bloom.need in method.supports


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def explain_rejection(place: Place, bloom: Bloom, method: Method) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it is too rough for this storyworld "
            f"(sense={method.sense} < {SENSE_MIN}). Try a gentler method such as {better}.)"
        )
    if bloom.need not in place.affords:
        return (
            f"(No story: {place.label} does not offer the {bloom.need} this {bloom.label} needs "
            f"to open, so the children have no honest fix there.)"
        )
    return (
        f"(No story: {method.label} does not match what {bloom.phrase} need. "
        f"This bloom opens with {bloom.need}, not with {method.label}.)"
    )


def initial_patience(trait: str) -> float:
    return 5.0 if trait in PATIENT_TRAITS else 3.0


def would_wait(relation: str, eager_age: int, steady_age: int, steady_trait: str) -> bool:
    steady_older = relation == "siblings" and steady_age > eager_age
    authority = initial_patience(steady_trait) + 1.0 + (4.0 if steady_older else 0.0)
    return steady_older and authority > HASTE_INIT


def predict_pinch(world: World) -> dict:
    sim = world.copy()
    blooms = sim.get("blooms")
    blooms.meters["bruised"] += 1
    propagate(sim, narrate=False)
    return {
        "bruised": blooms.meters["bruised"] >= THRESHOLD,
        "open": blooms.meters["open"] >= THRESHOLD,
    }


def introduce(world: World, eager: Entity, steady: Entity, place: Place, bloom: Bloom) -> None:
    for child in (eager, steady):
        child.memes["joy"] += 1
        child.memes["reverence"] += 1
    world.say(
        f"In {place.scene}, soft and gray, {eager.id} and {steady.id} began the day. "
        f"They carried {bloom.phrase} for morning worship to {place.altar}."
    )
    world.say(place.dawn_line)


def discover_closed_buds(world: World, bloom: Bloom) -> None:
    blooms = world.get("blooms")
    blooms.meters["closed"] = 1
    world.say(
        f"But the {bloom.plural_label} were folded tight, still shy of gold and sleepy light. "
        f"They were lovely to hold, but not yet wide."
    )


def tempt(world: World, eager: Entity, bloom: Bloom) -> None:
    eager.memes["haste"] += 1
    world.say(
        f'"Let us open them now somehow," said {eager.id}. '
        f'"If we press them wide, they can sit with pride."'
    )


def warn(world: World, steady: Entity, eager: Entity, bloom: Bloom) -> None:
    pred = predict_pinch(world)
    steady.memes["patience"] += 1
    world.facts["predicted_bruise"] = pred["bruised"]
    world.say(
        f'{steady.id} shook {steady.pronoun("possessive")} head and spoke instead: '
        f'"Do not tug and do not shove. Buds wake best with time and love."'
    )
    if pred["bruised"]:
        world.say(
            f'"If you pry them in a hurry, petals may bend and beauty worry. '
            f'Let a few small minutes elapse, and the blossoms will make their own perhaps."'
        )


def back_down(world: World, eager: Entity, steady: Entity) -> None:
    eager.memes["haste"] = 0.0
    eager.memes["relief"] += 1
    steady.memes["relief"] += 1
    world.say(
        f'{eager.id} looked, then took a slower view. '
        f'"You are right. I will wait with you."'
    )


def pinch(world: World, eager: Entity, bloom: Bloom) -> None:
    blooms = world.get("blooms")
    blooms.meters["bruised"] += 1
    blooms.meters["closed"] = 1
    propagate(world, narrate=False)
    eager.memes["haste"] += 1
    world.say(
        f"But {eager.id} gave one bud a tiny pry, and one soft edge bent with a sigh. "
        f"The hurt was small, yet plain to see, and {eager.id} went quiet as could be."
    )


def elder_arrives(world: World, elder: Entity) -> None:
    elder.memes["calm"] += 1
    world.say(
        f"Just then {elder.label_word} came near with patient hands and a listening ear."
    )


def guide(world: World, elder: Entity, method: Method) -> None:
    world.say(
        f'"Flowers need the help they know," said {elder.label_word}. '
        f'"{method.setup_line}"'
    )


def wait_and_open(world: World, bloom: Bloom, method: Method) -> None:
    blooms = world.get("blooms")
    blooms.meters["open"] += 1
    blooms.meters["closed"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"They followed the plan both mild and slow. {method.wait_line}."
    )
    world.say(
        f"A few warm minutes did elapse, and then {bloom.open_line}. "
        f"{bloom.scent_line}."
    )


def repair_feelings(world: World, eager: Entity, steady: Entity, elder: Entity) -> None:
    eager.memes["regret"] = max(0.0, eager.memes["regret"])
    eager.memes["relief"] += 1
    eager.memes["lesson"] += 1
    steady.memes["love"] += 1
    elder.memes["love"] += 1
    if eager.memes["regret"] >= THRESHOLD:
        world.say(
            f'{elder.label_word.capitalize()} touched {eager.id} on the shoulder and said, '
            f'"One bent petal is a gentle sign. Next time, let waiting do the fine."'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} smiled and softly said, '
            f'"Kind hands and calm hearts help flowers shine ahead."'
        )


def offer(world: World, eager: Entity, steady: Entity, place: Place, bloom: Bloom) -> None:
    blooms = world.get("blooms")
    blooms.meters["offered"] += 1
    for child in (eager, steady):
        child.memes["joy"] += 1
        child.memes["reverence"] += 1
    world.say(
        f"Soon the children set the flowers down, {bloom.worship_line} at {place.altar}. "
        f"They sang a tiny rhyme in time: 'Wait with care, and beauty will be there.'"
    )
    if blooms.meters["bruised"] >= THRESHOLD:
        world.say(
            "Even the bent little bud seemed to say that hurried hands should learn to sway."
        )
    else:
        world.say(
            "The blossoms opened bright and deep, like dawn itself had woken from sleep."
        )


def tell(
    place: Place,
    bloom: Bloom,
    method: Method,
    eager_name: str = "Mina",
    eager_gender: str = "girl",
    steady_name: str = "Ravi",
    steady_gender: str = "boy",
    steady_trait: str = "patient",
    elder_type: str = "grandmother",
    relation: str = "siblings",
    eager_age: int = 5,
    steady_age: int = 7,
) -> World:
    world = World()
    eager = world.add(
        Entity(
            id=eager_name,
            kind="character",
            type=eager_gender,
            role="eager",
            age=eager_age,
            attrs={"relation": relation},
            traits=["eager"],
        )
    )
    steady = world.add(
        Entity(
            id=steady_name,
            kind="character",
            type=steady_gender,
            role="steady",
            age=steady_age,
            attrs={"relation": relation},
            traits=[steady_trait],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    blooms = world.add(
        Entity(
            id="blooms",
            kind="thing",
            type="flowers",
            label=bloom.plural_label,
            phrase=bloom.phrase,
            tags=set(bloom.tags),
        )
    )
    eager.memes["haste"] = HASTE_INIT
    steady.memes["patience"] = initial_patience(steady_trait)

    introduce(world, eager, steady, place, bloom)
    discover_closed_buds(world, bloom)

    world.para()
    tempt(world, eager, bloom)
    warn(world, steady, eager, bloom)

    averted = would_wait(relation, eager_age, steady_age, steady_trait)
    if averted:
        back_down(world, eager, steady)
    else:
        pinch(world, eager, bloom)

    world.para()
    elder_arrives(world, elder)
    guide(world, elder, method)
    wait_and_open(world, bloom, method)
    repair_feelings(world, eager, steady, elder)

    world.para()
    offer(world, eager, steady, place, bloom)

    outcome = "waited" if averted else "bruised_then_bloomed"
    world.facts.update(
        place=place,
        bloom_cfg=bloom,
        method=method,
        eager=eager,
        steady=steady,
        elder=elder,
        blooms=blooms,
        relation=relation,
        outcome=outcome,
        averted=averted,
        bruised=blooms.meters["bruised"] >= THRESHOLD,
        opened=blooms.meters["open"] >= THRESHOLD,
        offered=blooms.meters["offered"] >= THRESHOLD,
    )
    return world


PLACES = {
    "courtyard": Place(
        id="courtyard",
        label="courtyard",
        scene="the little courtyard",
        altar="the stone altar by the neem tree",
        dawn_line="A pale bird called from the wall, and the sky looked ready to wake them all",
        affords={"sun", "warmth"},
        tags={"dawn", "courtyard"},
    ),
    "riverside": Place(
        id="riverside",
        label="riverside shrine",
        scene="the riverside shrine",
        altar="the smooth shrine step beside the water",
        dawn_line="The river made a silver sweep, and the reeds were whispering out of sleep",
        affords={"sun", "water"},
        tags={"river", "dawn"},
    ),
    "window_nook": Place(
        id="window_nook",
        label="window nook",
        scene="the quiet window nook",
        altar="the small shelf under the bright window",
        dawn_line="The glass held dawn in a gentle gleam, like warm milk poured into a dream",
        affords={"sun", "warmth"},
        tags={"window", "home"},
    ),
    "kitchen_shrine": Place(
        id="kitchen_shrine",
        label="kitchen shrine",
        scene="the cozy kitchen shrine",
        altar="the brass shelf near the clay lamp",
        dawn_line="The room still hummed with sleepy heat, and the floor felt warm beneath their feet",
        affords={"warmth", "water"},
        tags={"kitchen", "home"},
    ),
}

BLOOMS = {
    "daisy": Bloom(
        id="daisy",
        label="daisy",
        phrase="a small bundle of daisy buds",
        plural_label="daisy buds",
        need="sun",
        open_line="the daisy faces turned to the light, white and merry and newly bright",
        scent_line="A clean sweet smell began to play, as if the morning had learned to stay",
        worship_line="in a neat white ring",
        tags={"flower", "sun"},
    ),
    "lotus": Bloom(
        id="lotus",
        label="lotus",
        phrase="a shallow basket of lotus buds",
        plural_label="lotus buds",
        need="water",
        open_line="the lotus petals loosened and spread, pink at the tips with a glowing bed",
        scent_line="A cool soft fragrance rose in the air, gentle enough to feel like prayer",
        worship_line="in a calm pink row",
        tags={"flower", "water"},
    ),
    "jasmine": Bloom(
        id="jasmine",
        label="jasmine",
        phrase="a palm tray of jasmine buds",
        plural_label="jasmine buds",
        need="warmth",
        open_line="the jasmine stars came out one by one, small white lanterns greeting the sun",
        scent_line="Their sweet smell floated, light and deep, and even the room forgot to sleep",
        worship_line="in a little moon-white line",
        tags={"flower", "warmth"},
    ),
}

METHODS = {
    "sun_tray": Method(
        id="sun_tray",
        label="sun on a bright tray",
        sense=3,
        supports={"sun"},
        setup_line="Set them on a bright tray where the first sun can play",
        wait_line="They set the tray by the light and whispered a rhyme while the sky grew bright",
        qa_line="set the buds on a bright tray in the first sunlight",
        tags={"sun", "waiting"},
    ),
    "water_bowl": Method(
        id="water_bowl",
        label="a shallow bowl of water",
        sense=3,
        supports={"water"},
        setup_line="Float them in a shallow bowl, and let cool water do its role",
        wait_line="They floated the buds in a shallow bowl and counted ripples, one by one, whole",
        qa_line="floated the buds in a shallow bowl of water",
        tags={"water", "waiting"},
    ),
    "warm_cloth": Method(
        id="warm_cloth",
        label="a warm damp cloth",
        sense=3,
        supports={"warmth"},
        setup_line="Wrap them in a warm damp cloth, and let the hidden petals uncurl soft",
        wait_line="They wrapped the buds with careful care and hummed a rhyme in the warming air",
        qa_line="wrapped the buds in a warm damp cloth",
        tags={"warmth", "waiting"},
    ),
    "pull_petals": Method(
        id="pull_petals",
        label="pulling petals apart",
        sense=1,
        supports=set(),
        setup_line="Pull every petal wide by hand",
        wait_line="They tugged and tugged",
        qa_line="pulled the petals apart",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Asha", "Tara", "Nila", "Rani", "Sumi", "Anya"]
BOY_NAMES = ["Ravi", "Kiran", "Arun", "Nikhil", "Om", "Hari", "Dev", "Milan"]
TRAITS = ["patient", "careful", "gentle", "thoughtful", "quiet", "kind"]


@dataclass
class StoryParams:
    place: str
    bloom: str
    method: str
    eager_name: str
    eager_gender: str
    steady_name: str
    steady_gender: str
    steady_trait: str
    elder: str
    relation: str = "siblings"
    eager_age: int = 5
    steady_age: int = 7
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="courtyard",
        bloom="daisy",
        method="sun_tray",
        eager_name="Mina",
        eager_gender="girl",
        steady_name="Ravi",
        steady_gender="boy",
        steady_trait="patient",
        elder="grandmother",
        relation="siblings",
        eager_age=5,
        steady_age=7,
    ),
    StoryParams(
        place="riverside",
        bloom="lotus",
        method="water_bowl",
        eager_name="Arun",
        eager_gender="boy",
        steady_name="Lila",
        steady_gender="girl",
        steady_trait="careful",
        elder="grandfather",
        relation="friends",
        eager_age=6,
        steady_age=6,
    ),
    StoryParams(
        place="kitchen_shrine",
        bloom="jasmine",
        method="warm_cloth",
        eager_name="Tara",
        eager_gender="girl",
        steady_name="Om",
        steady_gender="boy",
        steady_trait="gentle",
        elder="grandmother",
        relation="siblings",
        eager_age=4,
        steady_age=8,
    ),
    StoryParams(
        place="window_nook",
        bloom="daisy",
        method="sun_tray",
        eager_name="Dev",
        eager_gender="boy",
        steady_name="Sumi",
        steady_gender="girl",
        steady_trait="thoughtful",
        elder="father",
        relation="friends",
        eager_age=5,
        steady_age=5,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for bloom_id, bloom in BLOOMS.items():
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and bloom_ready(place, bloom, method):
                    combos.append((place_id, bloom_id, method_id))
    return combos


KNOWLEDGE = {
    "worship": [
        (
            "What is worship?",
            "Worship is a gentle way of showing love, thanks, or respect. People may sing, pray, bow, or place flowers to show what is in their hearts.",
        )
    ],
    "elapse": [
        (
            "What does elapse mean?",
            "Elapse means that time passes. If a few minutes elapse, those minutes go by while you wait.",
        )
    ],
    "flower": [
        (
            "Why do some flower buds open slowly?",
            "Some buds open little by little when the light, warmth, or water is right. Their petals need time to loosen, so rushing can bend them.",
        )
    ],
    "sun": [
        (
            "How can sunlight help flowers?",
            "Sunlight warms many flowers and tells them it is daytime. That helps some blossoms open and face the light.",
        )
    ],
    "water": [
        (
            "Why does water help some flowers stay fresh?",
            "Water helps flowers drink and stay full instead of droopy. Some water-loving blossoms open better when they can rest in it.",
        )
    ],
    "warmth": [
        (
            "How can warmth help a bud open?",
            "Gentle warmth can help a tight bud relax and loosen. It is like helping the flower wake up slowly.",
        )
    ],
    "waiting": [
        (
            "Why can waiting be better than forcing?",
            "Waiting can be kinder because some things are not ready yet. When you force them, you may hurt them, but patience lets them change the safe way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["worship", "elapse", "flower", "sun", "water", "warmth", "waiting"]


def pair_noun(eager: Entity, steady: Entity, relation: str) -> str:
    if relation == "siblings":
        if eager.type == "girl" and steady.type == "girl":
            return "two sisters"
        if eager.type == "boy" and steady.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    eager = f["eager"]
    steady = f["steady"]
    place = f["place"]
    bloom = f["bloom_cfg"]
    method = f["method"]
    if f["averted"]:
        return [
            f'Write a short rhyming story for a 3-to-5-year-old that includes the words "worship" and "elapse". Two children are carrying {bloom.plural_label} for morning worship at {place.label}, and an older child teaches patient waiting.',
            f"Tell a gentle conflict story in rhyme where {eager.id} wants to hurry the flowers open, but {steady.id} stops the mistake and the buds open after a few minutes elapse.",
            f'Write a child-facing rhyming story about patience, morning worship, and buds that open with time instead of force. The ending should show the flowers open at last.',
        ]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "worship" and "elapse". Two children bring {bloom.plural_label} for worship, one child hurries, and an elder teaches a gentler way.',
        f"Tell a rhyme-filled story where {eager.id} tries to open a flower bud too soon, feels sorry, and then learns to wait while a few minutes elapse and the blossoms open.",
        f"Write a gentle conflict story in rhyme with a small mistake, a calm elder, and {method.label} helping the flowers get ready in time for worship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    eager = f["eager"]
    steady = f["steady"]
    elder = f["elder"]
    place = f["place"]
    bloom = f["bloom_cfg"]
    method = f["method"]
    pair = pair_noun(eager, steady, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {eager.id} and {steady.id}, and {elder.label_word} who helps them. They are getting flowers ready for morning worship.",
        ),
        (
            "Why were the children carrying the flowers?",
            f"They were taking {bloom.plural_label} to {place.altar} for worship. The flowers were part of a quiet, thankful morning offering.",
        ),
        (
            f"Why was there a conflict between {eager.id} and {steady.id}?",
            f"{eager.id} wanted the buds open right away, but {steady.id} knew rushing could bend the petals. The conflict came from hurry on one side and patience on the other.",
        ),
    ]
    if f["averted"]:
        qa.append(
            (
                f"What did {steady.id} do that changed the story?",
                f"{steady.id} warned {eager.id} before any bud was hurt, and {eager.id} listened. Because they waited, the flowers could open the gentle way instead of being forced.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {eager.id} tried to pry a bud open?",
                f"One bud was bent and bruised a little, and {eager.id} felt sorry right away. That small mistake showed why the flowers needed time instead of rough hands.",
            )
        )
    qa.append(
        (
            "How did the elder help solve the problem?",
            f"{elder.label_word.capitalize()} told them to {method.qa_line}. Then they waited while a few minutes elapse into bloom-time, and the flowers opened on their own.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the flowers ready for worship and the children speaking a little rhyme together. The final image shows that patience changed the buds from closed and worried to open and bright.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"worship", "elapse", "flower", "waiting"}
    bloom = world.facts["bloom_cfg"]
    method = world.facts["method"]
    tags |= set(bloom.tags)
    tags |= set(method.tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.age:
            parts.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, B, M) :- place(P), bloom(B), method(M), sense(M, S), sense_min(Min), S >= Min,
                  need(B, N), affords(P, N), supports(M, N).

% --- outcome model ---------------------------------------------------------
patient_now(T) :- trait(T), is_patient(T).
init_patience(5) :- trait(T), patient_now(T).
init_patience(3) :- trait(T), not patient_now(T).
steady_older :- relation(siblings), eager_age(EA), steady_age(SA), SA > EA.
bonus(4) :- steady_older.
bonus(0) :- not steady_older.
authority(P + 1 + B) :- init_patience(P), bonus(B).
waited :- steady_older, authority(A), haste_init(H), A > H.

outcome(waited) :- waited.
outcome(bruised_then_bloomed) :- not waited.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for afford in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, afford))
    for bloom_id, bloom in BLOOMS.items():
        lines.append(asp.fact("bloom", bloom_id))
        lines.append(asp.fact("need", bloom_id, bloom.need))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for support in sorted(method.supports):
            lines.append(asp.fact("supports", method_id, support))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("is_patient", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("haste_init", int(HASTE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("eager_age", params.eager_age),
            asp.fact("steady_age", params.steady_age),
            asp.fact("trait", params.steady_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "waited" if would_wait(params.relation, params.eager_age, params.steady_age, params.steady_trait) else "bruised_then_bloomed"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            args = build_parser().parse_args([])
            cases.append(resolve_params(args, random.Random(seed)))
        except StoryError:
            continue
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: children wait for flower buds to open for morning worship."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bloom", choices=BLOOMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_rejection(PLACES[next(iter(PLACES))], BLOOMS[next(iter(BLOOMS))], method))
    if args.place and args.bloom and args.method:
        place = PLACES[args.place]
        bloom = BLOOMS[args.bloom]
        method = METHODS[args.method]
        if not bloom_ready(place, bloom, method) or method.sense < SENSE_MIN:
            raise StoryError(explain_rejection(place, bloom, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.bloom is None or combo[1] == args.bloom)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, bloom_id, method_id = rng.choice(sorted(combos))
    eager_name, eager_gender = _pick_name(rng)
    steady_name, steady_gender = _pick_name(rng, avoid=eager_name)
    steady_trait = rng.choice(TRAITS)
    elder = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather"])
    relation = rng.choice(["siblings", "friends"])
    eager_age, steady_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        place=place_id,
        bloom=bloom_id,
        method=method_id,
        eager_name=eager_name,
        eager_gender=eager_gender,
        steady_name=steady_name,
        steady_gender=steady_gender,
        steady_trait=steady_trait,
        elder=elder,
        relation=relation,
        eager_age=eager_age,
        steady_age=steady_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        bloom = BLOOMS[params.bloom]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if method.sense < SENSE_MIN or not bloom_ready(place, bloom, method):
        raise StoryError(explain_rejection(place, bloom, method))

    world = tell(
        place=place,
        bloom=bloom,
        method=method,
        eager_name=params.eager_name,
        eager_gender=params.eager_gender,
        steady_name=params.steady_name,
        steady_gender=params.steady_gender,
        steady_trait=params.steady_trait,
        elder_type=params.elder,
        relation=params.relation,
        eager_age=params.eager_age,
        steady_age=params.steady_age,
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
        print(f"{len(combos)} compatible (place, bloom, method) combos:\n")
        for place, bloom, method in combos:
            print(f"  {place:14} {bloom:8} {method}")
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
            header = f"### {p.eager_name} & {p.steady_name}: {p.bloom} at {p.place} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
