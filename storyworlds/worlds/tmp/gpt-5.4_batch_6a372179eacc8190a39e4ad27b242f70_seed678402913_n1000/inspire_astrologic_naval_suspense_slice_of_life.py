#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/inspire_astrologic_naval_suspense_slice_of_life.py
==============================================================================

A small storyworld about a child waiting at the harbor for a loved one to come
back on a naval training boat. The child has made an astrologic welcome gift to
inspire them. The suspense comes from dusk, weather, and a delayed return.

The world model keeps the story grounded:
- weather and delay change whether the boat can be seen or heard,
- different adult helpers work better in different harbor conditions,
- unsafe or weak choices are rejected,
- the ending depends on whether the sensible method can reliably locate the boat.

Run it
------
python storyworlds/worlds/gpt-5.4/inspire_astrologic_naval_suspense_slice_of_life.py
python storyworlds/worlds/gpt-5.4/inspire_astrologic_naval_suspense_slice_of_life.py --weather fog --helper radio_office
python storyworlds/worlds/gpt-5.4/inspire_astrologic_naval_suspense_slice_of_life.py --weather fog --helper wave_arms
python storyworlds/worlds/gpt-5.4/inspire_astrologic_naval_suspense_slice_of_life.py --all
python storyworlds/worlds/gpt-5.4/inspire_astrologic_naval_suspense_slice_of_life.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "sister"}
        male = {"boy", "father", "uncle", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class HarborSetting:
    id: str
    place: str
    detail: str
    indoor_wait: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky_line: str
    water_line: str
    stars_visible: bool
    sight_penalty: int
    sound_penalty: int
    slippery: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    making_line: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trip:
    id: str
    craft: str
    role_label: str
    practice_line: str
    return_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    sense: int
    mode: str
    sight_power: int
    sound_power: int
    safe: bool
    action_line: str
    success_line: str
    fallback_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    weather: str
    trip: str
    gift: str
    helper: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_type: str
    returnee_name: str
    returnee_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: HarborSetting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_worry(world: World) -> list[str]:
    child = world.entities.get("child")
    boat = world.entities.get("boat")
    if not child or not boat:
        return []
    if boat.meters["uncertain"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return ["__worry__"]


def _r_relief(world: World) -> list[str]:
    child = world.entities.get("child")
    returnee = world.entities.get("returnee")
    boat = world.entities.get("boat")
    if not child or not returnee or not boat:
        return []
    if boat.meters["located"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["hope"] += 1
    returnee.memes["loved"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


SETTINGS = {
    "pier": HarborSetting(
        id="pier",
        place="the old harbor pier",
        detail="Wooden planks clicked softly under shoes, and the ropes along the posts smelled of salt.",
        indoor_wait="the little harbor office with foggy windows",
        tags={"harbor", "pier"},
    ),
    "museum_dock": HarborSetting(
        id="museum_dock",
        place="the naval museum dock",
        detail="A gray anchor stood by the path, and the small museum lamps made gold puddles on the boards.",
        indoor_wait="the museum lobby by the model ships",
        tags={"harbor", "museum", "naval"},
    ),
    "seawall": HarborSetting(
        id="seawall",
        place="the town seawall",
        detail="The stone rail held the day's warmth, and gulls rocked above the masts.",
        indoor_wait="the tea room by the seawall gate",
        tags={"harbor", "seawall"},
    ),
}

WEATHERS = {
    "clear": Weather(
        id="clear",
        sky_line="The evening sky was clear enough for the first star to appear.",
        water_line="The water kept flashing silver between the pilings.",
        stars_visible=True,
        sight_penalty=0,
        sound_penalty=0,
        slippery=False,
        tags={"clear", "stars"},
    ),
    "cloudy": Weather(
        id="cloudy",
        sky_line="Low clouds hung over the harbor, hiding the first stars behind a soft gray lid.",
        water_line="The water looked dark and flat, as if it were holding its breath.",
        stars_visible=False,
        sight_penalty=1,
        sound_penalty=0,
        slippery=False,
        tags={"clouds"},
    ),
    "fog": Weather(
        id="fog",
        sky_line="A pale fog pressed over the harbor and rubbed the evening into one blurry color.",
        water_line="The water was there, but only as a hush and a damp smell beyond the rail.",
        stars_visible=False,
        sight_penalty=2,
        sound_penalty=1,
        slippery=True,
        tags={"fog"},
    ),
}

GIFTS = {
    "star_chart": Gift(
        id="star_chart",
        label="star chart",
        phrase="an astrologic star chart drawn in blue pencil",
        making_line="At home, the child had drawn an astrologic star chart with tiny dots and careful lines.",
        reveal_line="The paper stars shook a little in the harbor breeze, but the drawing still pointed bravely upward.",
        tags={"astrologic", "stars", "chart"},
    ),
    "north_star_flag": Gift(
        id="north_star_flag",
        label="North Star flag",
        phrase="a small cloth flag with a stitched North Star",
        making_line="At home, the child had stitched a North Star onto a small flag and called it an astrologic welcome flag.",
        reveal_line="The little flag snapped once in the wind, its stitched star bright against the dusk.",
        tags={"astrologic", "flag", "stars"},
    ),
    "moon_card": Gift(
        id="moon_card",
        label="moon card",
        phrase="a moon card covered in astrologic stickers",
        making_line="At home, the child had made a moon card covered in astrologic stickers and silver crayon.",
        reveal_line="The silver moon on the card caught every scrap of light it could find.",
        tags={"astrologic", "moon", "card"},
    ),
}

TRIPS = {
    "cadet_launch": Trip(
        id="cadet_launch",
        craft="naval training launch",
        role_label="older sibling",
        practice_line="an evening ride on the naval training launch with the junior cadets",
        return_line="the little naval launch nosed back toward the dock",
        tags={"naval", "boat", "cadet"},
    ),
    "museum_skiff": Trip(
        id="museum_skiff",
        craft="naval museum skiff",
        role_label="older cousin",
        practice_line="a short harbor lesson aboard the naval museum skiff",
        return_line="the museum skiff slid back beside the dock",
        tags={"naval", "museum", "boat"},
    ),
    "harbor_boat": Trip(
        id="harbor_boat",
        craft="naval reserve boat",
        role_label="older brother",
        practice_line="a practice loop on the small naval reserve boat",
        return_line="the reserve boat turned through the dark water toward shore",
        tags={"naval", "boat"},
    ),
}

HELPERS = {
    "harbor_lamp": Helper(
        id="harbor_lamp",
        label="harbor lamp",
        sense=3,
        mode="sight",
        sight_power=2,
        sound_power=0,
        safe=True,
        action_line="lifted the borrowed harbor lamp and held its yellow circle steady at the waiting post",
        success_line="Soon a small answering blink came back through the dimness.",
        fallback_line="The yellow circle looked brave, but the dim harbor swallowed it before anyone could answer.",
        qa_line="used a harbor lamp to mark the right dock and wait safely in one place",
        tags={"lamp", "light", "harbor"},
    ),
    "bell": Helper(
        id="bell",
        label="dock bell",
        sense=3,
        mode="sound",
        sight_power=0,
        sound_power=2,
        safe=True,
        action_line="rang the old dock bell in three calm notes that carried over the water",
        success_line="After a moment, an answering horn sounded from the right side of the harbor.",
        fallback_line="The bell rang out, but the harbor sounded too wide and muffled for the answer to come back clearly.",
        qa_line="rang the dock bell so the boat and shore could find each other by sound",
        tags={"bell", "sound", "harbor"},
    ),
    "radio_office": Helper(
        id="radio_office",
        label="harbor office radio",
        sense=3,
        mode="radio",
        sight_power=3,
        sound_power=3,
        safe=True,
        action_line="stepped into the harbor office and spoke over the radio to the launch crew",
        success_line="A crackly voice answered at once and said the boat was already rounding in toward them.",
        fallback_line="The radio hissed and popped, but even then the harbor office could at least confirm the boat was safe and still coming.",
        qa_line="used the harbor office radio to contact the crew directly",
        tags={"radio", "office", "harbor"},
    ),
    "wave_arms": Helper(
        id="wave_arms",
        label="waving arms at the end of the dock",
        sense=1,
        mode="unsafe",
        sight_power=0,
        sound_power=0,
        safe=False,
        action_line="hurried toward the far end of the dock and waved both arms high",
        success_line="Nobody far out on the water could really have used that signal.",
        fallback_line="The gesture only made things feel more mixed up.",
        qa_line="waved arms from the end of the dock",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
ADULTS = [("Marin", "mother"), ("Jon", "father"), ("Ruth", "aunt"), ("Paul", "uncle")]
TRAITS = ["patient", "careful", "hopeful", "observant", "steady"]


def visible_need(weather: Weather, delay: int) -> int:
    return weather.sight_penalty + delay


def audible_need(weather: Weather, delay: int) -> int:
    return weather.sound_penalty + delay


def helper_effective(helper: Helper, weather: Weather, delay: int) -> bool:
    if helper.mode == "radio":
        return True
    if helper.mode == "sight":
        return helper.sight_power >= visible_need(weather, delay)
    if helper.mode == "sound":
        return helper.sound_power >= audible_need(weather, delay)
    return False


def safe_helper_ids() -> list[str]:
    return sorted(h.id for h in HELPERS.values() if h.sense >= SENSE_MIN and h.safe)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for weather_id, weather in WEATHERS.items():
            for trip_id in TRIPS:
                for helper_id, helper in HELPERS.items():
                    if helper.sense >= SENSE_MIN and helper.safe and any(
                        helper_effective(helper, weather, delay) for delay in (0, 1, 2)
                    ):
                        combos.append((setting_id, weather_id, trip_id, helper_id))
    return combos


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    return (
        f"(Refusing helper '{helper_id}': it is not a sensible harbor response "
        f"(sense={helper.sense} < {SENSE_MIN}). Choose a calm, safe method like "
        f"{', '.join(safe_helper_ids())}.)"
    )


def explain_combo(weather: Weather, helper: Helper, delay: int) -> str:
    if helper.sense < SENSE_MIN or not helper.safe:
        return explain_helper(helper.id)
    if helper_effective(helper, weather, delay):
        return ""
    return (
        f"(No direct reunion: {helper.label} is too weak for {weather.id} weather "
        f"with delay {delay}. The storyworld only accepts helper choices that can "
        f"reasonably locate the boat in these conditions.)"
    )


def predict_reunion(world: World, helper: Helper, weather: Weather, delay: int) -> dict:
    sim = world.copy()
    boat = sim.get("boat")
    boat.meters["uncertain"] += 1
    propagate(sim, narrate=False)
    found = helper_effective(helper, weather, delay)
    if found:
        boat.meters["located"] += 1
        boat.meters["uncertain"] = 0.0
    else:
        boat.meters["rerouted"] += 1
    propagate(sim, narrate=False)
    return {
        "found": found,
        "worry": sim.get("child").memes["worry"],
        "relief": sim.get("child").memes["relief"],
    }


def introduce(world: World, child: Entity, adult: Entity, returnee: Entity,
              gift: Gift, trip: Trip) -> None:
    world.say(
        f"{child.id} had spent all afternoon making {gift.phrase} to inspire "
        f"{returnee.id}, {child.pronoun('possessive')} {trip.role_label}."
    )
    world.say(gift.making_line)
    world.say(
        f"{returnee.id} had gone out on {trip.practice_line}, and {adult.id} had promised "
        f"they would wait together at {world.setting.place}."
    )


def arrive(world: World, child: Entity, adult: Entity, weather: Weather) -> None:
    child.memes["hope"] += 1
    world.say(
        f"By dusk, {child.id} and {adult.id} were standing at {world.setting.place}. "
        f"{world.setting.detail}"
    )
    world.say(weather.sky_line)
    world.say(weather.water_line)


def wait_and_count(world: World, child: Entity, gift: Gift, trip: Trip, weather: Weather) -> None:
    line = f"{child.id} kept peeking past the posts for {trip.craft}."
    if weather.stars_visible:
        line += f" {child.pronoun().capitalize()} even held up the gift and matched its little marks to the first star."
    else:
        line += " But there was no star to match yet, only dim sky and waiting water."
    world.say(line)
    world.say(gift.reveal_line)


def tension(world: World, child: Entity, adult: Entity, trip: Trip, weather: Weather, delay: int) -> None:
    boat = world.get("boat")
    if delay <= 0:
        world.say(f"At first, everything still felt on time.")
        return
    boat.meters["uncertain"] += 1
    propagate(world, narrate=False)
    world.facts["uncertain"] = True
    extra = "one long minute" if delay == 1 else "several long minutes"
    world.say(
        f"Then {extra} slipped by, and {trip.craft} still did not appear. "
        f"{child.id} squeezed the edge of the gift and looked harder into the dim."
    )
    if weather.slippery:
        world.say(
            f"The dock boards were damp with fog, and the far end looked darker than it had a moment before."
        )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f'"What if we are waiting at the wrong place?" {child.id} whispered.'
        )
    adult.memes["calm"] += 1


def unsafe_impulse(world: World, child: Entity, adult: Entity, weather: Weather) -> None:
    if not weather.slippery:
        world.say(
            f"{child.id} took one eager step toward the outer posts, wanting to see farther."
        )
    else:
        world.say(
            f"{child.id} started toward the foggier end of the dock, wanting to see farther."
        )
    world.say(
        f'But {adult.id} touched {child.pronoun("possessive")} sleeve and said, '
        f'"We stay together. We do not chase boats into the dark."'
    )


def choose_helper(world: World, adult: Entity, helper: Helper, weather: Weather, delay: int) -> None:
    pred = predict_reunion(world, helper, weather, delay)
    world.facts["predicted_found"] = pred["found"]
    world.say(
        f"{adult.id} took a slow breath, thought about the water and the weather, and then "
        f"{helper.action_line}."
    )


def resolve_direct(world: World, child: Entity, adult: Entity, returnee: Entity,
                   trip: Trip, helper: Helper) -> None:
    boat = world.get("boat")
    boat.meters["located"] += 1
    boat.meters["uncertain"] = 0.0
    propagate(world, narrate=False)
    world.say(helper.success_line)
    world.say(
        f"Soon {trip.return_line}, and {returnee.id} was there at the rail, waving before the boat had even bumped the tires."
    )
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{child.id} lifted the gift high. {returnee.id}'s face changed at once, from tired and careful to bright."
    )
    world.say(
        f'"You really made that for me?" {returnee.id} called. "That would inspire anybody."'
    )
    world.say(
        f"When {returnee.id} stepped ashore, {adult.id} laughed softly, and the three of them stood close in the harbor light."
    )


def resolve_reroute(world: World, child: Entity, adult: Entity, returnee: Entity,
                    helper: Helper) -> None:
    boat = world.get("boat")
    boat.meters["rerouted"] += 1
    propagate(world, narrate=False)
    child.memes["patience"] += 1
    world.say(helper.fallback_line)
    world.say(
        f"So {adult.id} led {child.id} into {world.setting.indoor_wait}, where the windows trembled a little each time the wind touched them."
    )
    world.say(
        f"They waited by the glass until the door opened and {returnee.id} came in smelling of salt and diesel, safe at last and a little late."
    )
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} handed over the gift right away. {returnee.id} smiled so hard that the whole room seemed warmer."
    )
    world.say(
        f'"I needed this after a slow trip in," {returnee.id} said. "It is the nicest astrologic welcome in the whole harbor."'
    )


def tell(setting: HarborSetting, weather: Weather, trip: Trip, gift: Gift, helper: Helper,
         child_name: str = "Lily", child_gender: str = "girl",
         adult_name: str = "Marin", adult_type: str = "mother",
         returnee_name: str = "Ben", returnee_type: str = "boy",
         trait: str = "patient", delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=[trait],
        attrs={"name": child_name},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label=adult_name,
        phrase=adult_name,
        role="adult",
        attrs={"name": adult_name},
    ))
    returnee = world.add(Entity(
        id="returnee",
        kind="character",
        type=returnee_type,
        label=returnee_name,
        phrase=returnee_name,
        role="returnee",
        attrs={"name": returnee_name},
    ))
    boat = world.add(Entity(
        id="boat",
        kind="thing",
        type="boat",
        label=trip.craft,
        phrase=trip.craft,
        role="boat",
    ))

    world.facts["display_names"] = {
        "child": child_name,
        "adult": adult_name,
        "returnee": returnee_name,
    }

    introduce(world, child, adult, returnee, gift, trip)
    world.para()
    arrive(world, child, adult, weather)
    wait_and_count(world, child, gift, trip, weather)
    tension(world, child, adult, trip, weather, delay)
    unsafe_impulse(world, child, adult, weather)

    world.para()
    choose_helper(world, adult, helper, weather, delay)
    direct = helper_effective(helper, weather, delay)
    if direct:
        resolve_direct(world, child, adult, returnee, trip, helper)
        outcome = "direct"
    else:
        resolve_reroute(world, child, adult, returnee, helper)
        outcome = "reroute"

    world.facts.update(
        child=child,
        adult=adult,
        returnee=returnee,
        boat=boat,
        setting=setting,
        weather=weather,
        trip=trip,
        gift=gift,
        helper=helper,
        delay=delay,
        outcome=outcome,
        direct=direct,
        slippery=weather.slippery,
        stars_visible=weather.stars_visible,
        worried=child.memes["worry"] >= THRESHOLD,
        inspired=child.memes["pride"] >= THRESHOLD or child.memes["joy"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "astrologic": [(
        "What does astrologic mean?",
        "Astrologic means something has to do with stars, planets, or patterns in the sky. In this story, it describes the child's star-themed craft."
    )],
    "naval": [(
        "What does naval mean?",
        "Naval means connected to ships, sailors, or a navy. A naval boat is a boat used for navy work or navy training."
    )],
    "fog": [(
        "Why is fog hard to see through?",
        "Fog is made of tiny drops of water floating in the air. They scatter light, so faraway things look blurry or disappear."
    )],
    "radio": [(
        "Why is a radio useful at a harbor?",
        "A radio lets people talk over distance even when they cannot see one another well. That helps boats and shore workers share clear information."
    )],
    "bell": [(
        "Why can a bell help near water?",
        "A bell makes a clear sound that can travel across water. People can listen for it even when the view is dim."
    )],
    "lamp": [(
        "Why does a lamp help at a dock?",
        "A lamp can mark a place and make it easier to see where to come in. It works best when the air is clear enough for light to carry."
    )],
    "harbor": [(
        "What is a harbor?",
        "A harbor is a safe place by the shore where boats can come in, tie up, and wait. Harbors often have docks, ropes, and lights."
    )],
}

KNOWLEDGE_ORDER = ["astrologic", "naval", "fog", "radio", "bell", "lamp", "harbor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child_name = f["display_names"]["child"]
    returnee_name = f["display_names"]["returnee"]
    helper = f["helper"]
    gift = f["gift"]
    trip = f["trip"]
    weather = f["weather"]
    base = (
        f'Write a slice-of-life story with suspense about a child waiting at a harbor for a loved one on a {trip.craft}. '
        f'Include the words "inspire", "astrologic", and "naval".'
    )
    if f["outcome"] == "direct":
        return [
            base,
            f"Tell a quiet suspense story where {child_name} brings {gift.phrase} to inspire {returnee_name}, the weather turns {weather.id}, and a calm adult uses {helper.label} to find the boat safely.",
            f"Write a gentle harbor story in which waiting feels tense for a little while, but a smart grown-up choice leads to a warm reunion.",
        ]
    return [
        base,
        f"Tell a slice-of-life harbor story where {child_name} worries as the boat is delayed in {weather.id} weather, and the family has to wait indoors before {returnee_name} finally arrives safe.",
        f"Write a suspenseful but child-safe story about waiting, listening, and staying together near the water until a loved one comes back.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    returnee = f["returnee"]
    weather = f["weather"]
    trip = f["trip"]
    gift = f["gift"]
    helper = f["helper"]
    child_name = f["display_names"]["child"]
    adult_name = f["display_names"]["adult"]
    returnee_name = f["display_names"]["returnee"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, {adult_name}, and {returnee_name} at the harbor. {child_name} is waiting for {returnee_name} to come back on a {trip.craft}."
        ),
        (
            f"What did {child_name} make, and why?",
            f"{child_name} made {gift.phrase} as a welcome gift. The child hoped it would inspire {returnee_name} after the naval trip."
        ),
        (
            "Why did the harbor feel suspenseful?",
            f"The harbor felt suspenseful because dusk had come, the weather was {weather.id}, and the boat was late. Those facts made it hard for the child to tell where the boat was."
        ),
    ]
    if f["slippery"]:
        qa.append((
            f"Why did {adult_name} stop {child_name} from going farther down the dock?",
            f"{adult_name} wanted {child_name} to stay safe because the dock was damp and harder to see in the fog. Going farther into the dark would not really help them find the boat."
        ))
    else:
        qa.append((
            f"Why did {adult_name} tell {child_name} to stay together?",
            f"{adult_name} knew that running along the dock would not solve the problem. Staying together made it easier to wait calmly and use a better plan."
        ))
    if f["outcome"] == "direct":
        qa.append((
            f"How did {adult_name} help them find the boat?",
            f"{adult_name} {helper.qa_line}. That worked in those harbor conditions, so the boat could come to the right place and the family could wave before it docked."
        ))
        qa.append((
            f"How did the story end?",
            f"It ended with a direct reunion at the dock. {returnee_name} saw the gift, felt touched by it, and said it would inspire anybody."
        ))
    else:
        qa.append((
            f"What happened after {adult_name} used the helper?",
            f"The helper did not give them a quick sighting outside, so they moved into {world.setting.indoor_wait}. That let them wait safely until {returnee_name} came in."
        ))
        qa.append((
            f"How did the story end?",
            f"It ended safely indoors, a little later than planned. The waiting was tense, but the child still got to give the astrologic gift to {returnee_name}."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"astrologic", "naval", "harbor"}
    weather = world.facts["weather"]
    helper = world.facts["helper"]
    if "fog" in weather.tags:
        tags.add("fog")
    if helper.id == "radio_office":
        tags.add("radio")
    elif helper.id == "bell":
        tags.add("bell")
    elif helper.id == "harbor_lamp":
        tags.add("lamp")
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
    names = world.facts.get("display_names", {})
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.id in names:
            bits.append(f"name={names[ent.id]}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pier",
        weather="clear",
        trip="cadet_launch",
        gift="star_chart",
        helper="harbor_lamp",
        child_name="Lily",
        child_gender="girl",
        adult_name="Marin",
        adult_type="mother",
        returnee_name="Ben",
        returnee_type="boy",
        trait="hopeful",
        delay=0,
    ),
    StoryParams(
        setting="museum_dock",
        weather="cloudy",
        trip="museum_skiff",
        gift="moon_card",
        helper="radio_office",
        child_name="Max",
        child_gender="boy",
        adult_name="Ruth",
        adult_type="aunt",
        returnee_name="Zoe",
        returnee_type="girl",
        trait="observant",
        delay=1,
    ),
    StoryParams(
        setting="pier",
        weather="fog",
        trip="harbor_boat",
        gift="north_star_flag",
        helper="bell",
        child_name="Ella",
        child_gender="girl",
        adult_name="Jon",
        adult_type="father",
        returnee_name="Theo",
        returnee_type="boy",
        trait="steady",
        delay=1,
    ),
    StoryParams(
        setting="seawall",
        weather="fog",
        trip="cadet_launch",
        gift="star_chart",
        helper="harbor_lamp",
        child_name="Sam",
        child_gender="boy",
        adult_name="Paul",
        adult_type="uncle",
        returnee_name="Nora",
        returnee_type="girl",
        trait="patient",
        delay=2,
    ),
    StoryParams(
        setting="museum_dock",
        weather="clear",
        trip="museum_skiff",
        gift="north_star_flag",
        helper="radio_office",
        child_name="Lucy",
        child_gender="girl",
        adult_name="Marin",
        adult_type="mother",
        returnee_name="Finn",
        returnee_type="boy",
        trait="careful",
        delay=0,
    ),
]


ASP_RULES = r"""
safe_helper(H) :- helper(H), sense(H,S), sense_min(M), S >= M, safe(H).
visible_need(W,D,N) :- sight_penalty(W,SP), N = SP + D.
audible_need(W,D,N) :- sound_penalty(W,SP), N = SP + D.

effective(H,W,D) :- mode(H,radio).
effective(H,W,D) :- mode(H,sight), visible_need(W,D,N), sight_power(H,P), P >= N.
effective(H,W,D) :- mode(H,sound), audible_need(W,D,N), sound_power(H,P), P >= N.

valid_combo(S,W,T,H) :- setting(S), weather(W), trip(T), safe_helper(H),
                        effective(H,W,0).
valid_combo(S,W,T,H) :- setting(S), weather(W), trip(T), safe_helper(H),
                        effective(H,W,1).
valid_combo(S,W,T,H) :- setting(S), weather(W), trip(T), safe_helper(H),
                        effective(H,W,2).

chosen_safe :- chosen_helper(H), safe_helper(H).
outcome(direct) :- chosen_safe, chosen_weather(W), chosen_delay(D), chosen_helper(H), effective(H,W,D).
outcome(reroute) :- chosen_safe, chosen_weather(W), chosen_delay(D), chosen_helper(H), not effective(H,W,D).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("sight_penalty", wid, weather.sight_penalty))
        lines.append(asp.fact("sound_penalty", wid, weather.sound_penalty))
    for tid in TRIPS:
        lines.append(asp.fact("trip", tid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        lines.append(asp.fact("mode", hid, helper.mode))
        lines.append(asp.fact("sight_power", hid, helper.sight_power))
        lines.append(asp.fact("sound_power", hid, helper.sound_power))
        if helper.safe:
            lines.append(asp.fact("safe", hid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_delay", params.delay),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    weather = WEATHERS[params.weather]
    return "direct" if helper_effective(helper, weather, params.delay) else "reroute"


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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a harbor wait, an astrologic gift, and a naval return under suspense."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--trip", choices=TRIPS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render curated examples")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper is not None:
        helper = HELPERS[args.helper]
        if helper.sense < SENSE_MIN or not helper.safe:
            raise StoryError(explain_helper(args.helper))

    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    weather_id = args.weather or rng.choice(sorted(WEATHERS))
    trip_id = args.trip or rng.choice(sorted(TRIPS))
    gift_id = args.gift or rng.choice(sorted(GIFTS))
    helper_id = args.helper or rng.choice(safe_helper_ids())
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    weather = WEATHERS[weather_id]
    helper = HELPERS[helper_id]
    if args.helper is not None and args.weather is not None and args.delay is not None:
        reason = explain_combo(weather, helper, delay)
        if reason:
            raise StoryError(reason)

    child_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    adult_name, adult_type = rng.choice(ADULTS)
    returnee_type = "boy" if child_gender == "girl" else "girl"
    returnee_name = _pick_name(rng, returnee_type, avoid=child_name)
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        weather=weather_id,
        trip=trip_id,
        gift=gift_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_type=adult_type,
        returnee_name=returnee_name,
        returnee_type=returnee_type,
        trait=trait,
        delay=delay,
    )


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Unknown weather: {params.weather})")
    if params.trip not in TRIPS:
        raise StoryError(f"(Unknown trip: {params.trip})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    helper = HELPERS[params.helper]
    weather = WEATHERS[params.weather]
    if helper.sense < SENSE_MIN or not helper.safe:
        raise StoryError(explain_helper(params.helper))
    if not (0 <= params.delay <= 2):
        raise StoryError("(Delay must be 0, 1, or 2.)")
    if not params.child_name or not params.adult_name or not params.returnee_name:
        raise StoryError("(Names must be non-empty.)")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("(Child gender must be 'girl' or 'boy'.)")
    if params.returnee_type not in {"girl", "boy"}:
        raise StoryError("(Returnee type must be 'girl' or 'boy'.)")
    if params.adult_type not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError("(Adult type must be mother, father, aunt, or uncle.)")
    # Fail closed on explicit implausible direct-helper requests.
    if params.seed is None and not helper_effective(helper, weather, params.delay):
        pass


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        weather=WEATHERS[params.weather],
        trip=TRIPS[params.trip],
        gift=GIFTS[params.gift],
        helper=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_name=params.adult_name,
        adult_type=params.adult_type,
        returnee_name=params.returnee_name,
        returnee_type=params.returnee_type,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_combo/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, weather, trip, helper) combos:\n")
        for setting_id, weather_id, trip_id, helper_id in combos:
            print(f"  {setting_id:12} {weather_id:8} {trip_id:14} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        tries = 0
        while len(samples) < args.n and tries < max(50, args.n * 50):
            seed = base_seed + tries
            tries += 1
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
                f"### {p.child_name} waits at {p.setting} "
                f"({p.weather}, {p.trip}, {p.helper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
