#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sneak_dummy_moral_value_tall_tale.py
===============================================================

A standalone storyworld for a child-facing tall tale about sneaking, a dummy in
the bed, and the moral value of honesty. The world rebuilds one tiny premise:

A child in an exaggerated frontier town longs to see a marvelous giant event
before dawn, secretly leaves a dummy under the quilt, gets into a heap of
trouble, tells the truth, and learns that asking honestly works better than
sneaking.

Run it
------
    python storyworlds/worlds/gpt-5.4/sneak_dummy_moral_value_tall_tale.py
    python storyworlds/worlds/gpt-5.4/sneak_dummy_moral_value_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/sneak_dummy_moral_value_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/sneak_dummy_moral_value_tall_tale.py --trace --qa
    python storyworlds/worlds/gpt-5.4/sneak_dummy_moral_value_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/sneak_dummy_moral_value_tall_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so go up three levels.
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HONESTY_MIN = 2


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
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Wonder:
    id: str
    label: str
    place: str
    image: str
    sound: str
    benefit: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DummyPlan:
    id: str
    label: str
    phrase: str
    material: str
    look: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    path: str
    risk: str
    trouble: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GuardianResponse:
    id: str
    sense: int
    action: str
    invite: str
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


def _r_cold_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.meters["outside_before_dawn"] < THRESHOLD:
        return out
    sig = ("cold_fear", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["awe"] += 1
    hero.memes["worry"] += 1
    out.append("__dawn__")
    return out


def _r_dummy_discovered(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    guardian = world.entities.get("guardian")
    bed = world.entities.get("bed")
    if hero is None or guardian is None or bed is None:
        return out
    if bed.meters["dummy_in_bed"] < THRESHOLD or hero.meters["outside_before_dawn"] < THRESHOLD:
        return out
    sig = ("dummy_discovered", "bed")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guardian.memes["concern"] += 1
    hero.memes["guilt"] += 1
    out.append("__discovered__")
    return out


def _r_truth_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    guardian = world.entities.get("guardian")
    if hero is None or guardian is None:
        return out
    if hero.memes["truth_told"] < THRESHOLD:
        return out
    sig = ("truth_relief", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["guilt"] = 0.0
    hero.memes["relief"] += 1
    guardian.memes["trust"] += 1
    out.append("__truth__")
    return out


CAUSAL_RULES = [
    Rule(name="cold_fear", tag="emotion", apply=_r_cold_fear),
    Rule(name="dummy_discovered", tag="social", apply=_r_dummy_discovered),
    Rule(name="truth_relief", tag="social", apply=_r_truth_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def sensible_responses() -> list[GuardianResponse]:
    return [r for r in RESPONSES.values() if r.sense >= HONESTY_MIN]


def valid_combo(wonder: Wonder, dummy: DummyPlan, route: Route, response: GuardianResponse) -> bool:
    return response.sense >= HONESTY_MIN and dummy.id in DUMMY_BY_WONDER[wonder.id] and route.id in ROUTE_BY_WONDER[wonder.id]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for wonder_id, wonder in WONDERS.items():
        for dummy_id, dummy in DUMMIES.items():
            for route_id, route in ROUTES.items():
                for response_id, response in RESPONSES.items():
                    if valid_combo(wonder, dummy, route, response):
                        combos.append((wonder_id, dummy_id, route_id, response_id))
    return combos


def predict_trouble(world: World, route_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["outside_before_dawn"] += 1
    sim.facts["route_id"] = route_id
    propagate(sim, narrate=False)
    return {
        "worry": hero.memes["worry"],
        "guilt": hero.memes["guilt"],
    }


def opening(world: World, hero: Entity, guardian: Entity, wonder: Wonder) -> None:
    hero.memes["longing"] += 1
    world.say(
        f"In a town where the fence posts were said to grow an inch whenever somebody bragged, "
        f"{hero.id} had the biggest wish on the street."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to see {wonder.label} at {wonder.place}, "
        f"the marvel that {wonder.image} and {wonder.sound}."
    )
    world.say(
        f"Folks said the sight could make a sleepy child feel tall as a pine tree all day."
    )
    world.say(
        f'But {hero.id}\'s {guardian.label_word} had already said, "Before dawn is too early to go alone."'
    )


def plan_sneak(world: World, hero: Entity, dummy: DummyPlan) -> None:
    hero.memes["defiance"] += 1
    bed = world.add(Entity(id="bed", type="bed", label="bed"))
    bed.meters["dummy_in_bed"] += 1
    world.say(
        f"That night, when the moon looked like a silver biscuit, {hero.id} decided to sneak out anyway."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tucked {dummy.phrase} under the quilt, making a dummy that {dummy.look}."
    )
    world.say(
        f"For a minute, the bed fooled even the shadows."
    )
    world.facts["used_dummy"] = True


def leave_home(world: World, hero: Entity, route: Route) -> None:
    hero.meters["outside_before_dawn"] += 1
    hero.meters["distance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Out went {hero.id} through {route.path}, quiet as a cat in felt slippers."
    )
    world.say(
        f"But tall tales always make trouble just as large as the wish, and {route.risk}."
    )
    hero.meters["trouble"] += 1
    world.facts["route_id"] = route.id


def trouble(world: World, hero: Entity, route: Route, wonder: Wonder) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Soon {route.trouble}, and all at once {wonder.label} did not feel like a game anymore."
    )
    world.say(
        f"{hero.id}'s heart thumped so hard it could have knocked apples from a tree."
    )


def reunion(world: World, hero: Entity, guardian: Entity, wonder: Wonder) -> None:
    guardian.meters["searching"] += 1
    world.say(
        f"Then across the dark came {guardian.label_word}'s lantern, bobbing like a little star on legs."
    )
    world.say(
        f'"{hero.id}!" {guardian.label_word.capitalize()} called. "I found your bed dummy and knew something was wrong."'
    )
    world.say(
        f"The grand wonder was still there at {wonder.place}, but now the truest thing in the morning was the worried voice."
    )


def tell_truth(world: World, hero: Entity, guardian: Entity) -> None:
    hero.memes["truth_told"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} stopped, swallowed hard, and told the truth. '
        f'"I wanted to go so badly that I sneaked away and left a dummy in my bed."'
    )
    world.say(
        f'Saying it felt like setting down a sack of rocks from {hero.pronoun("possessive")} shoulders.'
    )


def lesson(world: World, hero: Entity, guardian: Entity, response: GuardianResponse, wonder: Wonder) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    guardian.memes["love"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} knelt beside {hero.id} and {response.action}."
    )
    world.say(
        f'"Next time, ask me plain and true," {guardian.pronoun()} said. '
        f'"A wonder is sweeter when no one has to worry their boots thin looking for you."'
    )
    world.say(
        f'Together they waited, and soon {wonder.image}. This time {hero.id} enjoyed it with warm hands and an honest heart.'
    )
    world.say(
        f"From that day on, {hero.id} remembered that honesty can carry a child farther than sneaking ever can."
    )
    world.facts["outcome"] = "confessed"


def invitation(world: World, hero: Entity, guardian: Entity, response: GuardianResponse, wonder: Wonder) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    guardian.memes["love"] += 1
    hero.memes["truth_told"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the back door, {hero.id} almost slipped away, but the house felt too full of love to fool."
    )
    world.say(
        f'{hero.pronoun().capitalize()} turned around and blurted out the truth instead. '
        f'"I was going to sneak away with a dummy in my bed because I wanted to see {wonder.label}."'
    )
    world.say(
        f"{guardian.label_word.capitalize()} blinked, then {response.invite}."
    )
    world.say(
        f"Soon they stood together at {wonder.place}, and {wonder.image}. "
        f"{hero.id} felt ten feet taller for having asked honestly."
    )
    world.say(
        f"That was the morning {hero.id} learned a tall-tale truth: straight words make the best path."
    )
    world.facts["outcome"] = "asked_first"


def tell(
    wonder: Wonder,
    dummy: DummyPlan,
    route: Route,
    response: GuardianResponse,
    *,
    hero_name: str = "Mabel",
    hero_type: str = "girl",
    guardian_type: str = "father",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, phrase=hero_name, role="hero"))
    guardian = world.add(
        Entity(id="guardian", kind="character", type=guardian_type, label=guardian_type, phrase=guardian_type, role="guardian")
    )
    hero.attrs["name"] = hero_name
    guardian.attrs["name"] = guardian.label_word
    world.facts.update(
        hero_name=hero_name,
        hero_type=hero_type,
        guardian_type=guardian_type,
        wonder=wonder,
        dummy=dummy,
        route=route,
        response=response,
    )

    opening(world, hero, guardian, wonder)
    world.para()

    if response.id == "invite_first":
        invitation(world, hero, guardian, response, wonder)
    else:
        plan_sneak(world, hero, dummy)
        leave_home(world, hero, route)
        trouble(world, hero, route, wonder)
        world.para()
        reunion(world, hero, guardian, wonder)
        tell_truth(world, hero, guardian)
        lesson(world, hero, guardian, response, wonder)

    world.facts.update(
        hero=hero,
        guardian=guardian,
        confessed=hero.memes["truth_told"] >= THRESHOLD,
        used_dummy=world.facts.get("used_dummy", False),
    )
    return world


WONDERS = {
    "sun_kettle": Wonder(
        id="sun_kettle",
        label="the Sunrise Kettle Whistle",
        place="Whistle Hill",
        image="the first sunlight poured over the copper kettle on the hill and sent a stripe of gold across the whole valley",
        sound="whistled loud enough to shake dew off the clover",
        benefit="left laughter ringing in a child's chest",
        tags={"sunrise", "wonder"},
    ),
    "rooster": Wonder(
        id="rooster",
        label="the Mile-High Rooster Crow",
        place="Rooster Ridge",
        image="the giant red rooster threw back his head and sent a rosy crow rolling from hill to hill",
        sound="crowed so wide the windows winked",
        benefit="made everybody stand straighter",
        tags={"rooster", "wonder"},
    ),
    "milk_geyser": Wonder(
        id="milk_geyser",
        label="the Dawn Milk Geyser",
        place="Buttercup Flats",
        image="the white spring leapt up in the dawn and turned pink at the top like a strawberry cloud",
        sound="hissed and bubbled like ten breakfast pans at once",
        benefit="made the whole meadow smell like warm biscuits",
        tags={"milk", "wonder"},
    ),
}

DUMMIES = {
    "pillow_hat": DummyPlan(
        id="pillow_hat",
        label="pillow dummy",
        phrase="two pillows with a hat on top",
        material="pillows and a hat",
        look="made a hump that looked enough like a sleeping head in the dim room",
        tags={"dummy", "bed"},
    ),
    "broom_dummy": DummyPlan(
        id="broom_dummy",
        label="broom dummy",
        phrase="a broom wrapped in a coat with a flour sack for a face",
        material="broom, coat, and flour sack",
        look="looked lumpy and long, like a child tucked up to the chin",
        tags={"dummy", "bed"},
    ),
    "straw_dummy": DummyPlan(
        id="straw_dummy",
        label="straw dummy",
        phrase="a bundle of straw under the blanket with mittens for hands",
        material="straw and mittens",
        look="made the covers rise and fall whenever the window breathed",
        tags={"dummy", "straw"},
    ),
}

ROUTES = {
    "cellar_door": Route(
        id="cellar_door",
        path="the cellar door and around the syrup barrels",
        risk="the boards were slick with frost",
        trouble="the frost kissed the boards and sent {hero} skidding onto a cold hay bale",
        tags={"frost", "route"},
    ),
    "pasture_gap": Route(
        id="pasture_gap",
        path="the pasture gap behind the woodpile",
        risk="the grass was silver and slippery",
        trouble="a sleepy calf blocked the gap and snorted so suddenly that {hero} nearly sat down in the thistles",
        tags={"calf", "route"},
    ),
    "creek_log": Route(
        id="creek_log",
        path="the creek log below the willow tree",
        risk="the log was wet as a fish's back",
        trouble="the log wobbled underfoot and splashed one shoe right into the black water",
        tags={"creek", "route"},
    ),
}

RESPONSES = {
    "lantern_talk": GuardianResponse(
        id="lantern_talk",
        sense=3,
        action="wrapped a blanket around those small shoulders and kept the lantern high",
        invite="opened the door, took down the lantern, and said they could go together if they dressed warmly and stayed side by side",
        tags={"honesty", "care"},
    ),
    "wagon_ride": GuardianResponse(
        id="wagon_ride",
        sense=3,
        action="lifted {hero} into the wagon, tucked the robe around those chilly knees, and spoke in a steady voice",
        invite="hitched the little wagon and said an honest child could ride along beside the warm biscuit basket",
        tags={"honesty", "care", "wagon"},
    ),
    "porch_scold": GuardianResponse(
        id="porch_scold",
        sense=1,
        action="marched straight home with a scowl and no explanation",
        invite="said no and shut the door tight",
        tags={"scold"},
    ),
}

DUMMY_BY_WONDER = {
    "sun_kettle": {"pillow_hat", "broom_dummy"},
    "rooster": {"pillow_hat", "straw_dummy"},
    "milk_geyser": {"broom_dummy", "straw_dummy"},
}

ROUTE_BY_WONDER = {
    "sun_kettle": {"cellar_door", "creek_log"},
    "rooster": {"pasture_gap", "cellar_door"},
    "milk_geyser": {"creek_log", "pasture_gap"},
}

GIRL_NAMES = ["Mabel", "Tilly", "Nora", "June", "Elsie", "Pearl", "Clara", "Della"]
BOY_NAMES = ["Hank", "Jeb", "Otis", "Eli", "Beau", "Clyde", "Theo", "Cal"]

# Domain-specific params, defined exactly once before CURATED / resolve / generate.
@dataclass
class StoryParams:
    wonder: str
    dummy: str
    route: str
    response: str
    hero_name: str
    hero_type: str
    guardian_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        wonder="sun_kettle",
        dummy="pillow_hat",
        route="cellar_door",
        response="lantern_talk",
        hero_name="Mabel",
        hero_type="girl",
        guardian_type="father",
    ),
    StoryParams(
        wonder="rooster",
        dummy="straw_dummy",
        route="pasture_gap",
        response="wagon_ride",
        hero_name="Hank",
        hero_type="boy",
        guardian_type="mother",
    ),
    StoryParams(
        wonder="milk_geyser",
        dummy="broom_dummy",
        route="creek_log",
        response="invite_first",
        hero_name="Pearl",
        hero_type="girl",
        guardian_type="aunt",
    ),
]


# Add the synthetic response used by the "ask honestly first" branch.
RESPONSES["invite_first"] = GuardianResponse(
    id="invite_first",
    sense=3,
    action="smiled because the truth had arrived before the trouble did",
    invite="smiled, set out warm boots, and said honesty had already earned half the trip",
    tags={"honesty", "care"},
)


KNOWLEDGE = {
    "dummy": [
        (
            "What is a dummy in a story like this?",
            "A dummy is a pretend person-shape made from things like pillows or straw. It can fool someone for a moment, but it is not real.",
        )
    ],
    "honesty": [
        (
            "Why is honesty important?",
            "Honesty helps people trust each other. Telling the truth can solve a problem faster than hiding it.",
        )
    ],
    "sunrise": [
        (
            "What happens at sunrise?",
            "Sunrise is when the sun first comes up and lights the sky. The world often looks pink or gold for a little while.",
        )
    ],
    "rooster": [
        (
            "Why do roosters crow?",
            "Roosters often crow when morning is coming. Their loud call lets everyone know the day is starting.",
        )
    ],
    "milk": [
        (
            "What is a geyser?",
            "A geyser is a spring that shoots water up from the ground. In a tall tale, people may imagine it shooting something even sillier, like milk.",
        )
    ],
    "care": [
        (
            "What does a caring grown-up do when a child is in trouble?",
            "A caring grown-up keeps the child safe first. Then they teach the lesson in a calm way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["dummy", "honesty", "sunrise", "rooster", "milk", "care"]


def trouble_text(route: Route, hero_name: str) -> str:
    return route.trouble.replace("{hero}", hero_name)


def generation_prompts(world: World) -> list[str]:
    wonder = world.facts["wonder"]
    hero_name = world.facts["hero_name"]
    guardian_type = world.facts["guardian_type"]
    outcome = world.facts.get("outcome")
    if outcome == "asked_first":
        return [
            f'Write a child-facing tall tale that includes the words "sneak" and "dummy" but ends with the child choosing honesty before leaving home.',
            f"Tell a warm moral story about {hero_name}, who wants to see {wonder.label} and almost sneaks away, then tells {guardian_type} the truth instead.",
            f"Write a tall-tale story where a child learns that asking honestly is better than sneaking off to a wonder before dawn.",
        ]
    return [
        f'Write a child-facing tall tale that includes the words "sneak" and "dummy" and teaches honesty.',
        f"Tell a moral story about {hero_name}, who sneaks out before dawn to see {wonder.label}, leaves a dummy in bed, and learns a lesson.",
        f"Write a simple tall tale where a marvelous sight tempts a child into secrecy, but the ending proves that truth is stronger than tricks.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    guardian = world.facts["guardian"]
    wonder = world.facts["wonder"]
    dummy = world.facts["dummy"]
    route = world.facts["route"]
    outcome = world.facts.get("outcome")
    hero_name = world.facts["hero_name"]
    guardian_word = guardian.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child who longed to see {wonder.label}, and {hero_name}'s {guardian_word}. The story follows how that wish turned into a lesson about honesty.",
        ),
        (
            f"What did {hero_name} want to see?",
            f"{hero_name} wanted to see {wonder.label} at {wonder.place}. In this tall tale, it sounded so grand that the wish felt bigger than bedtime.",
        ),
    ]
    if outcome != "asked_first":
        qa.extend(
            [
                (
                    f"What dummy did {hero_name} make?",
                    f"{hero_name} made {dummy.phrase} and tucked it into bed. The dummy looked real enough in the dim room to fool someone for a little while.",
                ),
                (
                    f"Why did sneaking away stop feeling exciting?",
                    f"Sneaking stopped feeling exciting when {trouble_text(route, hero_name)}. The cold dark route made {hero_name} realize the trip was not as safe or easy as it had sounded in bed.",
                ),
                (
                    f"How did {hero_name}'s {guardian_word} know something was wrong?",
                    f"{guardian_word.capitalize()} found the dummy in the bed and came looking with a lantern. That showed the trick had caused worry instead of freedom.",
                ),
                (
                    "What lesson did the child learn?",
                    f"{hero_name} learned that honesty works better than sneaking. Telling the truth brought help, warmth, and the wonder itself without more fear.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Did {hero_name} really sneak away?",
                    f"No. {hero_name} almost did, but told the truth before leaving home. That changed the story from a secret escape into an honest adventure.",
                ),
                (
                    "What lesson did the child learn?",
                    f"{hero_name} learned that straight words make the best path. Because the truth came first, nobody had to worry or search in the dark.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"dummy", "honesty", "care"}
    wonder = world.facts["wonder"]
    tags |= set(wonder.tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_dummy(wonder_id: str, dummy_id: str) -> str:
    return (
        f"(No story: {DUMMIES[dummy_id].label} is not one of the plausible dummy plans for "
        f"{WONDERS[wonder_id].label}. Pick one that fits this tall-tale trip.)"
    )


def explain_route(wonder_id: str, route_id: str) -> str:
    return (
        f"(No story: {ROUTES[route_id].path} does not sensibly lead toward {WONDERS[wonder_id].place}. "
        f"Pick a route tied to that wonder.)"
    )


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too low on common sense for this moral story "
        f"(sense={r.sense} < {HONESTY_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
plausible_dummy(W, D) :- wonder_dummy(W, D).
plausible_route(W, R) :- wonder_route(W, R).
sensible_response(R) :- response(R), sense(R, S), honesty_min(M), S >= M.
valid(W, D, R, Resp) :- wonder(W), dummy(D), route(R), response(Resp),
                        plausible_dummy(W, D), plausible_route(W, R), sensible_response(Resp).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid in WONDERS:
        lines.append(asp.fact("wonder", wid))
    for did in DUMMIES:
        lines.append(asp.fact("dummy", did))
    for rid in ROUTES:
        lines.append(asp.fact("route", rid))
    for resp_id, resp in RESPONSES.items():
        lines.append(asp.fact("response", resp_id))
        lines.append(asp.fact("sense", resp_id, resp.sense))
    for wonder_id, dummy_ids in DUMMY_BY_WONDER.items():
        for dummy_id in sorted(dummy_ids):
            lines.append(asp.fact("wonder_dummy", wonder_id, dummy_id))
    for wonder_id, route_ids in ROUTE_BY_WONDER.items():
        for route_id in sorted(route_ids):
            lines.append(asp.fact("wonder_route", wonder_id, route_id))
    lines.append(asp.fact("honesty_min", HONESTY_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Random generated story was empty during smoke test.")
        print("OK: random resolve/generate smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child, a dummy in bed, a tempting wonder, and the moral value of honesty."
    )
    ap.add_argument("--wonder", choices=sorted(WONDERS))
    ap.add_argument("--dummy", choices=sorted(DUMMIES))
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < HONESTY_MIN:
        raise StoryError(explain_response(args.response))
    if args.wonder and args.dummy and args.dummy not in DUMMY_BY_WONDER[args.wonder]:
        raise StoryError(explain_dummy(args.wonder, args.dummy))
    if args.wonder and args.route and args.route not in ROUTE_BY_WONDER[args.wonder]:
        raise StoryError(explain_route(args.wonder, args.route))

    combos = [
        combo
        for combo in valid_combos()
        if (args.wonder is None or combo[0] == args.wonder)
        and (args.dummy is None or combo[1] == args.dummy)
        and (args.route is None or combo[2] == args.route)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    wonder_id, dummy_id, route_id, response_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    guardian_type = args.guardian or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        wonder=wonder_id,
        dummy=dummy_id,
        route=route_id,
        response=response_id,
        hero_name=hero_name,
        hero_type=hero_type,
        guardian_type=guardian_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.wonder not in WONDERS:
        raise StoryError(f"(Unknown wonder: {params.wonder})")
    if params.dummy not in DUMMIES:
        raise StoryError(f"(Unknown dummy: {params.dummy})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    wonder = WONDERS[params.wonder]
    dummy = DUMMIES[params.dummy]
    route = ROUTES[params.route]
    response = RESPONSES[params.response]

    if not valid_combo(wonder, dummy, route, response):
        if response.sense < HONESTY_MIN:
            raise StoryError(explain_response(params.response))
        if params.dummy not in DUMMY_BY_WONDER[params.wonder]:
            raise StoryError(explain_dummy(params.wonder, params.dummy))
        raise StoryError(explain_route(params.wonder, params.route))

    world = tell(
        wonder=wonder,
        dummy=dummy,
        route=route,
        response=response,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        guardian_type=params.guardian_type,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
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
        print(f"{len(combos)} compatible (wonder, dummy, route, response) combos:\n")
        for wonder, dummy, route, response in combos:
            print(f"  {wonder:11} {dummy:12} {route:11} {response}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: {p.wonder} via {p.route} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
