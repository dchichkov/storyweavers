#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pilgrim_shy_chihuahua_surprise_slice_of_life.py
============================================================================

A standalone story world for a gentle slice-of-life tale about a shy child, a
school pilgrim event, and a surprising little chihuahua who helps at just the
right moment.

Premise
-------
A child is getting ready for a small school "pilgrim" event. The child is shy,
and one needed costume piece has gone missing. A caring grown-up offers a kind
support that actually fits the kind of social worry the child has. Then, in a
small surprise, the family chihuahua sniffs out the missing piece from a place
low enough to reach. The child goes to school feeling steadier and more ready.

Reasonableness constraints
--------------------------
This world refuses weak or unreasonable combinations.

* The support must fit the event's emotional need:
    - a line-speaking event needs practice support
    - a crowd-facing event needs a visible reassurance like a pocket wave
    - a waiting-in-line event needs a closeness support like a lap hug

* The chihuahua surprise only works when the missing item is in a reachable,
  low place. A tiny dog cannot pull something from a high shelf.

Run it
------
    python storyworlds/worlds/gpt-5.4/pilgrim_shy_chihuahua_surprise_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/pilgrim_shy_chihuahua_surprise_slice_of_life.py --event poem --support practice
    python storyworlds/worlds/gpt-5.4/pilgrim_shy_chihuahua_surprise_slice_of_life.py --place high_shelf
    python storyworlds/worlds/gpt-5.4/pilgrim_shy_chihuahua_surprise_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/pilgrim_shy_chihuahua_surprise_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4/pilgrim_shy_chihuahua_surprise_slice_of_life.py --verify
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
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
class Event:
    id: str
    label: str
    phrase: str
    need: str
    room: str
    act: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    use: str
    article: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    level: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    addresses: set[str]
    offer: str
    effect: str
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


def _r_missing_worry(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["shy"] += 1
    return []


def _r_support_steady(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["supported"] < THRESHOLD:
        return []
    sig = ("support_steady",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["steady"] += 1
    if child.memes["worry"] >= THRESHOLD:
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    return []


def _r_found_relief(world: World) -> list[str]:
    child = world.get("child")
    dog = world.get("dog")
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["surprise"] += 1
    dog.memes["proud"] += 1
    if child.memes["worry"] >= THRESHOLD:
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="support_steady", tag="emotion", apply=_r_support_steady),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def support_fits(event: Event, support: Support) -> bool:
    return event.need in support.addresses


def dog_can_reach(place: HidingPlace) -> bool:
    return place.level == "low"


def valid_combo(event: Event, item: MissingItem, place: HidingPlace, support: Support) -> bool:
    return support_fits(event, support) and dog_can_reach(place)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for event_id, event in EVENTS.items():
        for item_id, item in ITEMS.items():
            for place_id, place in PLACES.items():
                for support_id, support in SUPPORTS.items():
                    if valid_combo(event, item, place, support):
                        combos.append((event_id, item_id, place_id, support_id))
    return combos


def predict_ready(world: World, event: Event, support: Support, place: HidingPlace) -> dict:
    sim = world.copy()
    child = sim.get("child")
    item = sim.get("item")
    item.meters["missing"] += 1
    propagate(sim, narrate=False)
    if support_fits(event, support):
        child.memes["supported"] += 1
        propagate(sim, narrate=False)
    if dog_can_reach(place):
        item.meters["found"] += 1
        item.meters["missing"] = 0.0
        propagate(sim, narrate=False)
    ready = item.meters["found"] >= THRESHOLD and child.memes["steady"] + child.memes["relief"] >= THRESHOLD
    return {
        "ready": ready,
        "worry": child.memes["worry"],
        "surprise": child.memes["surprise"],
    }


def morning_setup(world: World, child: Entity, adult: Entity, dog: Entity, event: Event) -> None:
    child.memes["shy"] += 1
    child.memes["love"] += 1
    dog.memes["love"] += 1
    world.say(
        f"On a cool morning, {child.id} stood in the kitchen while {adult.label_word} straightened a plain dark skirt and a white apron for {event.phrase} at school."
    )
    world.say(
        f"{dog.id}, the family's little chihuahua, pattered in tiny circles near the table, nails clicking like soft rain on the floor."
    )
    world.say(
        f"{child.id} was shy, and the thought of {event.act} in {event.room} made {child.pronoun('object')} hold very still."
    )


def mention_pilgrim(world: World, child: Entity, event: Event) -> None:
    world.say(
        f"On the chair waited the rest of the pilgrim outfit, neat and quiet, as if it were trying not to make a fuss either."
    )
    if event.need == "line":
        world.say(
            f"{child.id} had already practiced the words once under {child.pronoun('possessive')} breath, but saying them in front of everyone felt much bigger."
        )
    elif event.need == "crowd":
        world.say(
            f"{child.id} did not mind the clothes so much. It was all the eyes in one room that felt hard."
        )
    else:
        world.say(
            f"{child.id} worried most about standing there with everyone waiting, even for one small minute."
        )


def discover_missing(world: World, child: Entity, item: Entity, cfg: MissingItem) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} looked for {cfg.article} {cfg.label} and blinked. {cfg.article.capitalize()} {cfg.label} was not on the chair."
    )
    world.say(
        f"Without it, {cfg.use} would not be ready, and the morning suddenly felt much tighter in {child.pronoun('possessive')} chest."
    )


def adult_search(world: World, child: Entity, adult: Entity, item_cfg: MissingItem, place: HidingPlace) -> None:
    world.say(
        f'"We just had it," {adult.label_word} said, opening one drawer and then another. {child.id} checked the table edge and the couch cushion.'
    )
    world.say(
        f"But the {item_cfg.label} was still missing, and {dog_can_reach(place) and 'even the little chihuahua tilted his head as if he knew the room had changed' or 'even the little chihuahua only watched from the rug'}."
    )


def offer_support(world: World, child: Entity, adult: Entity, support: Support, event: Event) -> None:
    child.memes["supported"] += 1
    world.facts["predicted_ready"] = predict_ready(world, event, support, PLACES[world.facts["place_id"]])["ready"]
    propagate(world, narrate=False)
    world.say(
        f'{adult.label_word.capitalize()} came back to {child.id}' + "'s side and said, "
        f'"{support.offer}"'
    )
    world.say(
        f"{support.effect} The kind plan did not make the whole morning easy, but it gave {child.id} one small steady place to stand."
    )


def dog_surprise(world: World, child: Entity, adult: Entity, dog: Entity,
                 item: Entity, item_cfg: MissingItem, place: HidingPlace) -> None:
    item.meters["found"] += 1
    item.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Just then {dog.id} stopped, nose twitching. The tiny dog trotted to {place.phrase}, sniffed hard, and began to scratch."
    )
    world.say(
        f'{adult.label_word.capitalize()} bent down. "What is it, {dog.id}?"'
    )
    world.say(
        f"Out came {item_cfg.article} {item_cfg.label}. It had slipped {place.clue}, and now the chihuahua had found it first."
    )
    world.say(
        f"{child.id} stared, then laughed in surprise. The sound was small, but it changed the whole room."
    )


def ready_up(world: World, child: Entity, adult: Entity, dog: Entity,
             item_cfg: MissingItem, event: Event, support: Support) -> None:
    child.memes["brave"] += 1
    child.memes["joy"] += 1
    world.say(
        f'{adult.label_word.capitalize()} fastened the {item_cfg.label} into place, and {child.id} touched it once just to be sure it was really there.'
    )
    world.say(
        f"{dog.id} sat on the mat looking pleased with himself, ears up like two little question marks that had finally turned into an answer."
    )
    world.say(
        f"When they left for school, {child.id} was still shy, but no longer alone inside the feeling. {support.effect.lower()}."
    )
    world.say(
        f"By the time {child.pronoun()} stepped into {event.room}, {child.pronoun()} could manage {event.ending}, and that felt like enough for one morning."
    )


def tell(event: Event, item_cfg: MissingItem, place: HidingPlace, support: Support,
         child_name: str = "Lina", child_type: str = "girl",
         adult_type: str = "grandmother", dog_name: str = "Pip") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, phrase=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_type, phrase=adult_type, role="adult"))
    dog = world.add(Entity(id="dog", kind="character", type="dog", label=dog_name, phrase=dog_name, role="dog"))
    item = world.add(Entity(id="item", kind="thing", type="costume_piece", label=item_cfg.label, phrase=item_cfg.phrase, role="item"))

    world.facts["event"] = event
    world.facts["item_cfg"] = item_cfg
    world.facts["place"] = place
    world.facts["support"] = support
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["dog"] = dog
    world.facts["item"] = item
    world.facts["place_id"] = place.id

    morning_setup(world, child, adult, dog, event)
    mention_pilgrim(world, child, event)

    world.para()
    discover_missing(world, child, item, item_cfg)
    adult_search(world, child, adult, item_cfg, place)
    offer_support(world, child, adult, support, event)

    world.para()
    dog_surprise(world, child, adult, dog, item, item_cfg, place)
    ready_up(world, child, adult, dog, item_cfg, event, support)

    world.facts["ready"] = item.meters["found"] >= THRESHOLD
    world.facts["surprised"] = child.memes["surprise"] >= THRESHOLD
    world.facts["steady"] = child.memes["steady"] + child.memes["relief"] >= THRESHOLD
    return world


EVENTS = {
    "poem": Event(
        id="poem",
        label="thank-you poem",
        phrase="the class pilgrim poem",
        need="line",
        room="the classroom rug",
        act="saying one line when the teacher pointed to her",
        ending="one clear line and a tiny smile afterward",
        tags={"school", "poem", "pilgrim"},
    ),
    "parade": Event(
        id="parade",
        label="hallway parade",
        phrase="the school pilgrim parade",
        need="crowd",
        room="the bright hallway",
        act="walking past all the doors while families waved",
        ending="one steady walk past the doors",
        tags={"school", "crowd", "pilgrim"},
    ),
    "photo": Event(
        id="photo",
        label="class photo",
        phrase="the pilgrim class picture",
        need="wait",
        room="the library corner",
        act="standing still while everyone found their places",
        ending="standing still long enough for the picture",
        tags={"school", "photo", "pilgrim"},
    ),
}

ITEMS = {
    "collar": MissingItem(
        id="collar",
        label="white collar",
        phrase="a white paper collar",
        use="the pilgrim costume",
        article="the",
        tags={"costume", "paper"},
    ),
    "hat": MissingItem(
        id="hat",
        label="paper hat",
        phrase="a black paper hat",
        use="the pilgrim outfit",
        article="the",
        tags={"costume", "hat"},
    ),
    "buckle": MissingItem(
        id="buckle",
        label="shoe buckle",
        phrase="a silver paper shoe buckle",
        use="the costume shoes",
        article="the",
        tags={"costume", "shoes"},
    ),
    "card": MissingItem(
        id="card",
        label="name card",
        phrase="a little name card",
        use="the front of the costume",
        article="the",
        tags={"school", "card"},
    ),
}

PLACES = {
    "under_sofa": HidingPlace(
        id="under_sofa",
        label="under the sofa",
        phrase="the dim space under the sofa",
        level="low",
        clue="under the sofa with a dust bunny beside it",
        tags={"home", "low"},
    ),
    "laundry_basket": HidingPlace(
        id="laundry_basket",
        label="in the laundry basket",
        phrase="the laundry basket by the hall",
        level="low",
        clue="inside the laundry basket between two tea towels",
        tags={"home", "low"},
    ),
    "backpack_pocket": HidingPlace(
        id="backpack_pocket",
        label="in the backpack pocket",
        phrase="the open pocket of the school backpack",
        level="low",
        clue="half tucked into the backpack pocket",
        tags={"school", "low"},
    ),
    "high_shelf": HidingPlace(
        id="high_shelf",
        label="on the high shelf",
        phrase="the high shelf by the pantry",
        level="high",
        clue="on the high shelf behind a stack of bowls",
        tags={"home", "high"},
    ),
}

SUPPORTS = {
    "practice": Support(
        id="practice",
        label="practice together",
        addresses={"line"},
        offer="Let's say the line together once in the kitchen, and then you can borrow my brave face until your own catches up.",
        effect="They practiced the words once, slowly and softly",
        tags={"practice", "support"},
    ),
    "pocket_wave": Support(
        id="pocket_wave",
        label="pocket wave",
        addresses={"crowd"},
        offer="When you look up, I will give you our tiny pocket wave so you know exactly where to look.",
        effect="The promise of one familiar wave gave the crowd a smaller shape",
        tags={"wave", "support"},
    ),
    "lap_hug": Support(
        id="lap_hug",
        label="lap hug",
        addresses={"wait"},
        offer="Before the picture, come sit with me for one warm lap hug, and then we will walk in together.",
        effect="The thought of a warm lap hug made the waiting part feel shorter",
        tags={"hug", "support"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Lucy", "Rose", "Anna", "Mia"]
BOY_NAMES = ["Eli", "Theo", "Sam", "Noah", "Ben", "Finn", "Max", "Leo"]
DOG_NAMES = ["Pip", "Taco", "Peanut", "Bean", "Chico", "Momo"]
ADULT_TYPES = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    event: str
    item: str
    place: str
    support: str
    child_name: str
    child_gender: str
    adult: str
    dog_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "pilgrim": [(
        "What is a pilgrim costume in a school play?",
        "A pilgrim costume is dress-up clothing children might wear for a Thanksgiving lesson or class play. It is just a costume for learning and pretending."
    )],
    "chihuahua": [(
        "What is a chihuahua?",
        "A chihuahua is a very small dog. Even though it is tiny, it can be alert, quick, and full of personality."
    )],
    "shy": [(
        "What does shy mean?",
        "Shy means you feel quiet or nervous around other people or when many eyes are on you. A shy person can still do brave things, just more gently."
    )],
    "practice": [(
        "Why does practice help when you feel nervous?",
        "Practice helps because your mouth and body get used to what comes next. Then the hard thing feels a little more familiar."
    )],
    "wave": [(
        "Why can a familiar wave help in a crowd?",
        "A familiar wave gives you one safe thing to look for. It can make a big room feel smaller and kinder."
    )],
    "hug": [(
        "Why can a hug help before something hard?",
        "A hug can help your body calm down. Feeling close to someone you trust can make waiting easier."
    )],
    "surprise": [(
        "What is a surprise?",
        "A surprise is something you did not expect. It can change the way a moment feels very quickly."
    )],
}
KNOWLEDGE_ORDER = ["pilgrim", "chihuahua", "shy", "practice", "wave", "hug", "surprise"]


def explain_place_rejection(place: HidingPlace) -> str:
    return (
        f"(No story: the missing piece is {place.label}, and a tiny chihuahua cannot reach a {place.level} place. "
        f"Pick a low place so the dog can reasonably find it.)"
    )


def explain_support_rejection(event: Event, support: Support) -> str:
    need_map = {
        "line": "saying a line out loud",
        "crowd": "facing lots of watching people",
        "wait": "waiting calmly for a turn",
    }
    return (
        f"(No story: support '{support.id}' does not fit {event.phrase}. "
        f"This event is mostly about {need_map.get(event.need, event.need)}, so the comfort move should match that need.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    dog = f["dog"]
    event = f["event"]
    item_cfg = f["item_cfg"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "pilgrim", "shy", and "chihuahua".',
        f"Tell a small home-and-school story where a shy child named {child.label} is getting ready for {event.phrase}, loses {item_cfg.article} {item_cfg.label}, and gets an unexpected surprise from {dog.label}, the chihuahua.",
        f"Write a quiet family story where {adult.label_word} helps a nervous child through one ordinary morning, and the ending feels better because of a small surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    dog = f["dog"]
    event = f["event"]
    item_cfg = f["item_cfg"]
    place = f["place"]
    support = f["support"]
    adult_word = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a shy child named {child.label}, {child.pronoun('possessive')} {adult_word}, and {dog.label}, the little chihuahua. They are all part of one busy morning at home."
        ),
        (
            f"Why was {child.label} feeling shy?",
            f"{child.label} felt shy because {child.pronoun()} was getting ready for {event.phrase} at school. The event meant other people would be looking and waiting, which made the morning feel big."
        ),
        (
            f"What went missing?",
            f"The missing thing was {item_cfg.article} {item_cfg.label}. Without it, {item_cfg.use} would not be ready."
        ),
        (
            f"How did {adult_word} try to help before the surprise?",
            f"{adult_word.capitalize()} offered {support.label}. {support.effect}, which gave {child.label} a calmer way to think about the hard part."
        ),
        (
            f"What was the surprise?",
            f"The surprise was that {dog.label}, the chihuahua, found the missing {item_cfg.label}. The tiny dog sniffed at {place.phrase}, and that changed the whole mood of the room."
        ),
        (
            f"How did the story end?",
            f"The missing piece was back, and {child.label} went to school more steadily. {child.pronoun().capitalize()} was still shy, but now the shyness sat beside relief instead of fear."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pilgrim", "chihuahua", "shy", "surprise"}
    support = world.facts["support"]
    if support.id == "practice":
        tags.add("practice")
    elif support.id == "pocket_wave":
        tags.add("wave")
    elif support.id == "lap_hug":
        tags.add("hug")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        event="poem",
        item="collar",
        place="under_sofa",
        support="practice",
        child_name="Lina",
        child_gender="girl",
        adult="grandmother",
        dog_name="Pip",
    ),
    StoryParams(
        event="parade",
        item="hat",
        place="backpack_pocket",
        support="pocket_wave",
        child_name="Eli",
        child_gender="boy",
        adult="mother",
        dog_name="Peanut",
    ),
    StoryParams(
        event="photo",
        item="buckle",
        place="laundry_basket",
        support="lap_hug",
        child_name="Maya",
        child_gender="girl",
        adult="father",
        dog_name="Bean",
    ),
]


ASP_RULES = r"""
reachable_place(P) :- place(P), level(P, low).
fit(E, S) :- event(E), need(E, N), support(S), addresses(S, N).
findable(I, P) :- item(I), portable(I), reachable_place(P).
valid(E, I, P, S) :- event(E), item(I), place(P), support(S), fit(E, S), findable(I, P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for event_id, event in EVENTS.items():
        lines.append(asp.fact("event", event_id))
        lines.append(asp.fact("need", event_id, event.need))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("portable", item_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("level", place_id, place.level))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        for need in sorted(support.addresses):
            lines.append(asp.fact("addresses", support_id, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "chihuahua" not in sample.story.lower() or "pilgrim" not in sample.story.lower():
            raise StoryError("smoke test story missing required content")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a shy child, a pilgrim school morning, and a surprising chihuahua."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--dog-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place:
        place = PLACES[args.place]
        if not dog_can_reach(place):
            raise StoryError(explain_place_rejection(place))
    if args.event and args.support:
        event = EVENTS[args.event]
        support = SUPPORTS[args.support]
        if not support_fits(event, support):
            raise StoryError(explain_support_rejection(event, support))

    combos = [
        combo for combo in valid_combos()
        if (args.event is None or combo[0] == args.event)
        and (args.item is None or combo[1] == args.item)
        and (args.place is None or combo[2] == args.place)
        and (args.support is None or combo[3] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    event_id, item_id, place_id, support_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    adult = args.adult or rng.choice(ADULT_TYPES)
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    return StoryParams(
        event=event_id,
        item=item_id,
        place=place_id,
        support=support_id,
        child_name=child_name,
        child_gender=gender,
        adult=adult,
        dog_name=dog_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")

    event = EVENTS[params.event]
    item_cfg = ITEMS[params.item]
    place = PLACES[params.place]
    support = SUPPORTS[params.support]

    if not dog_can_reach(place):
        raise StoryError(explain_place_rejection(place))
    if not support_fits(event, support):
        raise StoryError(explain_support_rejection(event, support))

    world = tell(
        event=event,
        item_cfg=item_cfg,
        place=place,
        support=support,
        child_name=params.child_name,
        child_type=params.child_gender,
        adult_type=params.adult,
        dog_name=params.dog_name,
    )

    child = world.facts["child"]
    child.label = params.child_name
    dog = world.facts["dog"]
    dog.label = params.dog_name

    story = world.render().replace("child", params.child_name).replace("adult", world.get("adult").label_word.capitalize())
    story = story.replace("Pip", params.dog_name) if params.dog_name != "Pip" else story

    story = story.replace("child", params.child_name)
    story = story.replace("adult", world.get("adult").label_word)

    story = story.replace("child", params.child_name)

    # Re-render cleanly with display names rather than internal ids.
    story = (
        world.render()
        .replace("child", params.child_name)
        .replace("adult", world.get("adult").label_word)
        .replace("dog", params.dog_name)
    )
    story = story.replace(f"{world.get('adult').label_word}'s side", f"{world.get('adult').label_word}'s side")
    story = story.replace(f"{world.get('adult').label_word} came back to {params.child_name}'s side and said,", f"{world.get('adult').label_word.capitalize()} came back to {params.child_name}'s side and said,")

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, item, place, support) combos:\n")
        for event, item, place, support in combos:
            print(f"  {event:7} {item:8} {place:15} {support}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
            header = f"### {p.child_name}: {p.event}, missing {p.item}, surprise at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
