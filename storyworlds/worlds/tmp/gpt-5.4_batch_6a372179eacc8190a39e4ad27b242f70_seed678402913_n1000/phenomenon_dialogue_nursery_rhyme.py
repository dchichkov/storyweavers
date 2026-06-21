#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/phenomenon_dialogue_nursery_rhyme.py
===============================================================

A small storyworld about a child who sees a bright natural phenomenon and
wants to rush closer, stare too hard, or stay outside too long. A calm helper
turns that risky impulse into a safe way to look and wonder.

The prose aims for a child-facing nursery-rhyme flavor with repeated sounds and
lots of dialogue, while still being driven by simulated state:
- physical meters track puddles, glare, cold, safety, and tiny near-misses
- emotional memes track wonder, impatience, fear, relief, and trust

Run it
------
    python storyworlds/worlds/gpt-5.4/phenomenon_dialogue_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/phenomenon_dialogue_nursery_rhyme.py --phenomenon rainbow
    python storyworlds/worlds/gpt-5.4/phenomenon_dialogue_nursery_rhyme.py --place hill --phenomenon rainbow
    python storyworlds/worlds/gpt-5.4/phenomenon_dialogue_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/phenomenon_dialogue_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/phenomenon_dialogue_nursery_rhyme.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
            "grandmother": "gran",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)
    refrain: str = ""
    puddly: bool = False
    chilly: bool = False
    wide_view: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Phenomenon:
    id: str
    label: str
    sky_line: str
    call_line: str
    hazard: str
    lesson: str
    need_place_tag: str
    rhythm: str
    visible_from_window: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    sense: int = 0
    calm_line: str = ""
    action_line: str = ""
    ending_line: str = ""
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rainbow_dash(world: World) -> list[str]:
    child = world.get("child")
    place = world.facts["place"]
    if world.facts["phenomenon"].hazard != "slip":
        return []
    if child.meters["dashing"] < THRESHOLD or not place.puddly:
        return []
    sig = ("rainbow_slip", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["slip_risk"] += 1
    child.memes["worry"] += 1
    return ["__risk__"]


def _r_sundog_stare(world: World) -> list[str]:
    child = world.get("child")
    if world.facts["phenomenon"].hazard != "glare":
        return []
    if child.meters["staring"] < THRESHOLD:
        return []
    sig = ("sundog_glare",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["glare_risk"] += 1
    child.memes["worry"] += 1
    return ["__risk__"]


def _r_halo_linger(world: World) -> list[str]:
    child = world.get("child")
    place = world.facts["place"]
    if world.facts["phenomenon"].hazard != "cold":
        return []
    if child.meters["lingering"] < THRESHOLD or not place.chilly:
        return []
    sig = ("halo_cold", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["cold_risk"] += 1
    child.memes["worry"] += 1
    return ["__risk__"]


CAUSAL_RULES = [
    Rule(name="rainbow_dash", tag="physical", apply=_r_rainbow_dash),
    Rule(name="sundog_stare", tag="physical", apply=_r_sundog_stare),
    Rule(name="halo_linger", tag="physical", apply=_r_halo_linger),
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


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        affords={"rainbow", "sundog"},
        refrain="Drip-drop, tip-top, the mint leaves shook.",
        puddly=True,
        chilly=False,
        wide_view=True,
        tags={"garden"},
    ),
    "hill": Place(
        id="hill",
        label="the little hill",
        affords={"rainbow", "sundog", "moon_halo"},
        refrain="Up-high, sky-high, the long grass swayed.",
        puddly=False,
        chilly=True,
        wide_view=True,
        tags={"hill"},
    ),
    "doorstep": Place(
        id="doorstep",
        label="the front doorstep",
        affords={"rainbow", "moon_halo"},
        refrain="Tap-tap, soft-clap, the old door sang.",
        puddly=True,
        chilly=True,
        wide_view=True,
        tags={"doorstep", "window"},
    ),
}

PHENOMENA = {
    "rainbow": Phenomenon(
        id="rainbow",
        label="rainbow",
        sky_line="After a quick silver shower, a bright rainbow arched over the sky.",
        call_line='"A ribbon in the blue! A ribbon in the blue!"',
        hazard="slip",
        lesson="A rainbow is a weather phenomenon you can watch, but you cannot catch it by running.",
        need_place_tag="garden",
        rhythm="Bow of red, bow of gold, shy and bright and never sold.",
        visible_from_window=True,
        tags={"rainbow", "phenomenon", "weather"},
    ),
    "sundog": Phenomenon(
        id="sundog",
        label="sundog",
        sky_line="Beside the sun sat a bright sundog, a tiny patch of fire-colored light.",
        call_line='"Two suns! Two suns! Oh, what a shining sight!"',
        hazard="glare",
        lesson="A sundog is a sky phenomenon, but kind eyes do not stare right at the sun.",
        need_place_tag="hill",
        rhythm="Bright by day, away, away; look with care and do not gaze.",
        visible_from_window=False,
        tags={"sundog", "phenomenon", "sun"},
    ),
    "moon_halo": Phenomenon(
        id="moon_halo",
        label="moon halo",
        sky_line="Around the moon shone a pale moon halo, a silver ring in the evening hush.",
        call_line='"Round moon, round light, who drew that ring tonight?"',
        hazard="cold",
        lesson="A moon halo is a night-sky phenomenon, lovely to see, but small cheeks should not shiver for it.",
        need_place_tag="window",
        rhythm="Moon so high, ring so slow, silver circle, gentle glow.",
        visible_from_window=True,
        tags={"moon", "halo", "phenomenon", "night"},
    ),
}

RESPONSES = {
    "hold_and_watch": Response(
        id="hold_and_watch",
        label="hold hands and watch from one dry spot",
        handles={"slip"},
        sense=3,
        calm_line='"Hush now," said {helper_name}. "Rainbows dance away when feet dash after them."',
        action_line="{helper_name_cap} took {child_name}'s hand and kept both shoes on one dry stone by the path.",
        ending_line='Together they counted colors instead: "Red, orange, yellow..."',
        tags={"watch_safely", "hands"},
    ),
    "shade_and_glance": Response(
        id="shade_and_glance",
        label="stand in shade and glance beside the sun",
        handles={"glare"},
        sense=3,
        calm_line='"Soft eyes," said {helper_name}. "We look near the sun, not right into its bright face."',
        action_line="{helper_name_cap} moved {child_name} under the pear tree and made a little roof of a broad hat.",
        ending_line='From the shade they peeked beside the sun and saw the bright patch sparkle politely.',
        tags={"shade", "sun_safety"},
    ),
    "blanket_window": Response(
        id="blanket_window",
        label="wrap up and watch from the window",
        handles={"cold"},
        sense=3,
        calm_line='"Brrr is not for little noses," said {helper_name}. "Moon rings can be admired from warmth."',
        action_line="{helper_name_cap} wrapped a soft blanket around {child_name} and opened the curtain wide.",
        ending_line='At the window they watched the silver ring while the kettle hummed a sleepy tune.',
        tags={"blanket", "window"},
    ),
    "rush_closer": Response(
        id="rush_closer",
        label="rush closer",
        handles=set(),
        sense=0,
        calm_line="",
        action_line="",
        ending_line="",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Tess", "Daisy"]
BOY_NAMES = ["Ollie", "Benji", "Milo", "Toby", "Finn", "Theo"]
HELPER_TYPES = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["curious", "bouncy", "bright-eyed", "eager", "gentle"]


def place_supports(place: Place, phenomenon: Phenomenon) -> bool:
    if phenomenon.id not in place.affords:
        return False
    if phenomenon.need_place_tag == "garden":
        return place.wide_view
    if phenomenon.need_place_tag == "hill":
        return "hill" in place.tags or place.wide_view
    if phenomenon.need_place_tag == "window":
        return "window" in place.tags
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(place_id: str, phenomenon_id: str, response_id: str) -> bool:
    if place_id not in PLACES or phenomenon_id not in PHENOMENA or response_id not in RESPONSES:
        return False
    place = PLACES[place_id]
    phenomenon = PHENOMENA[phenomenon_id]
    response = RESPONSES[response_id]
    if not place_supports(place, phenomenon):
        return False
    if response.sense < SENSE_MIN:
        return False
    return phenomenon.hazard in response.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for phenomenon_id in sorted(PHENOMENA):
            for response_id in sorted(RESPONSES):
                if valid_combo(place_id, phenomenon_id, response_id):
                    combos.append((place_id, phenomenon_id, response_id))
    return combos


def predict_risk(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    hazard = sim.facts["phenomenon"].hazard
    if hazard == "slip":
        child.meters["dashing"] += 1
    elif hazard == "glare":
        child.meters["staring"] += 1
    elif hazard == "cold":
        child.meters["lingering"] += 1
    propagate(sim, narrate=False)
    return {
        "slip_risk": child.meters["slip_risk"],
        "glare_risk": child.meters["glare_risk"],
        "cold_risk": child.meters["cold_risk"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"{place.refrain} In {place.label}, {child.id} skipped with a {child.traits[0]} heart beside "
        f"{child.pronoun('possessive')} {helper.label_word}."
    )
    world.say(
        f'"Skip and sing, swing and sway," said {child.id}. "{place.label.capitalize()} is for play!"'
    )


def appear(world: World, child: Entity, phenomenon: Phenomenon) -> None:
    child.memes["wonder"] += 1
    world.say(phenomenon.sky_line)
    world.say(f"{child.id} clapped and cried, {phenomenon.call_line}")
    world.say(
        f'"What a phenomenon!" {child.pronoun()} whispered, as if the sky had started speaking in rhyme.'
    )


def urge(world: World, child: Entity, phenomenon: Phenomenon) -> None:
    child.memes["impatience"] += 1
    if phenomenon.hazard == "slip":
        child.meters["dashing"] += 1
        world.say(
            f'"I can catch the {phenomenon.label}!" said {child.id}. '
            f'{child.pronoun().capitalize()} leaned toward the wet path with quick little feet.'
        )
    elif phenomenon.hazard == "glare":
        child.meters["staring"] += 1
        world.say(
            f'"I must look and look!" said {child.id}. '
            f'{child.pronoun().capitalize()} tipped {child.pronoun("possessive")} chin up toward the bright sky.'
        )
    else:
        child.meters["lingering"] += 1
        world.say(
            f'"I will stay outside till the ring goes to bed," said {child.id}. '
            f'{child.pronoun().capitalize()} stood very still in the evening air.'
        )
    propagate(world, narrate=False)


def warn(world: World, child: Entity, helper: Entity, phenomenon: Phenomenon) -> None:
    pred = predict_risk(world)
    world.facts["predicted_risk"] = pred
    helper.memes["care"] += 1
    if phenomenon.hazard == "slip" and pred["slip_risk"] >= THRESHOLD:
        world.say(
            f'"Slow toes, slow toes," said {helper.label_word}. "The stones are slick, and the {phenomenon.label} '
            f'will still be lovely if we do not tumble."'
        )
    elif phenomenon.hazard == "glare" and pred["glare_risk"] >= THRESHOLD:
        world.say(
            f'"Blink, little starling," said {helper.label_word}. "Too much bright can sting your eyes, '
            f'even for a beautiful sky wonder."'
        )
    elif phenomenon.hazard == "cold" and pred["cold_risk"] >= THRESHOLD:
        world.say(
            f'"Sniffles sneak in on chilly feet," said {helper.label_word}. "We can admire the ring without '
            f'letting the night nip your nose."'
        )


def near_miss(world: World, child: Entity, phenomenon: Phenomenon, delay: int) -> None:
    if delay <= 0:
        return
    child.memes["fear"] += 1
    if phenomenon.hazard == "slip":
        child.meters["almost_slipped"] += 1
        world.say(
            f"But patter-skip, clatter-slip -- {child.id}'s shoe skidded on the shiny path, and "
            f'{child.pronoun()} gave one startled gasp.'
        )
    elif phenomenon.hazard == "glare":
        child.meters["eyes_water"] += 1
        world.say(
            f"But blink-blink, quick as wink -- {child.id}'s eyes watered, and {child.pronoun()} looked away at once.'
        )
    else:
        child.meters["shiver"] += 1
        world.say(
            f"But brrr-brrr, tiny burr -- a shiver ran through {child.id}, and {child.pronoun()} tucked '
            f'{child.pronoun("possessive")} chin down.'
        )


def soothe_and_fix(world: World, child: Entity, helper: Entity, response: Response) -> None:
    child.memes["trust"] += 1
    child.memes["relief"] += 1
    child.meters["safe"] += 1
    helper_name = helper.label_word
    world.say(
        response.calm_line.format(
            helper_name=helper_name,
            helper_name_cap=helper_name.capitalize(),
            child_name=child.id,
        )
    )
    world.say(
        response.action_line.format(
            helper_name=helper_name,
            helper_name_cap=helper_name.capitalize(),
            child_name=child.id,
        )
    )


def ending(world: World, child: Entity, helper: Entity, phenomenon: Phenomenon, response: Response) -> None:
    child.memes["wonder"] += 1
    child.memes["joy"] += 1
    world.say(response.ending_line)
    world.say(
        f'{child.id} leaned close to {helper.label_word} and said, "I do not have to grab a wonder to love it."'
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled. "{phenomenon.lesson}"'
    )
    world.say(
        f'{phenomenon.rhythm} So they watched and watched until the sky grew soft, and the safe small moment '
        f'felt bigger than a song.'
    )


def tell(
    place: Place,
    phenomenon: Phenomenon,
    response: Response,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_type: str = "grandmother",
    trait: str = "curious",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait],
        tags={"child"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        tags={"adult"},
    ))
    sky = world.add(Entity(
        id="sky",
        kind="thing",
        type="sky",
        label="sky",
        tags=set(phenomenon.tags),
    ))
    ground = world.add(Entity(
        id="ground",
        kind="thing",
        type="ground",
        label=place.label,
        tags=set(place.tags),
    ))
    world.facts.update(
        place=place,
        phenomenon=phenomenon,
        response=response,
        child=child,
        helper=helper,
        delay=delay,
        sky=sky,
        ground=ground,
    )

    introduce(world, child, helper, place)
    world.para()
    appear(world, child, phenomenon)
    urge(world, child, phenomenon)
    warn(world, child, helper, phenomenon)
    if delay > 0:
        near_miss(world, child, phenomenon, delay)
    world.para()
    soothe_and_fix(world, child, helper, response)
    ending(world, child, helper, phenomenon, response)

    world.facts["outcome"] = "near_miss" if delay > 0 else "calm"
    return world


@dataclass
class StoryParams:
    place: str
    phenomenon: str
    response: str
    child_name: str
    child_type: str
    helper_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        phenomenon="rainbow",
        response="hold_and_watch",
        child_name="Mina",
        child_type="girl",
        helper_type="grandmother",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        place="hill",
        phenomenon="sundog",
        response="shade_and_glance",
        child_name="Ollie",
        child_type="boy",
        helper_type="father",
        trait="bright-eyed",
        delay=0,
    ),
    StoryParams(
        place="doorstep",
        phenomenon="moon_halo",
        response="blanket_window",
        child_name="Nora",
        child_type="girl",
        helper_type="mother",
        trait="gentle",
        delay=1,
    ),
]


KNOWLEDGE = {
    "phenomenon": [
        (
            "What does the word phenomenon mean?",
            "A phenomenon is something that happens in the world and makes people stop and notice it. "
            "It can be surprising, beautiful, or unusual."
        )
    ],
    "rainbow": [
        (
            "What makes a rainbow?",
            "A rainbow appears when sunlight shines through tiny drops of water in the air. "
            "The light bends and spreads into many colors."
        )
    ],
    "sun": [
        (
            "Why should children avoid staring right at the sun?",
            "The sun is much too bright to stare at. "
            "Looking right at it can hurt your eyes, so it is safer to look away or stay in shade."
        )
    ],
    "moon": [
        (
            "What is a moon halo?",
            "A moon halo is a pale ring around the moon. "
            "It happens when moonlight passes through tiny ice crystals high in the sky."
        )
    ],
    "weather": [
        (
            "Why can a wet path be slippery?",
            "Water makes some stones and paths slick. "
            "When your shoe cannot grip well, your foot can slide."
        )
    ],
    "shade": [
        (
            "What does shade do on a bright day?",
            "Shade blocks some of the sunlight so a place feels cooler and gentler on your eyes. "
            "That is why standing in shade can help on a bright day."
        )
    ],
    "window": [
        (
            "Why can a window be a good place to look at the sky?",
            "A window lets you see outside while you stay warm and dry inside. "
            "It is a good way to enjoy something lovely without getting too cold or wet."
        )
    ],
    "blanket": [
        (
            "What is a blanket for?",
            "A blanket helps keep your body warm. "
            "It holds in heat so you feel snug instead of chilly."
        )
    ],
}
KNOWLEDGE_ORDER = ["phenomenon", "rainbow", "weather", "sun", "shade", "moon", "window", "blanket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    phenomenon = f["phenomenon"]
    place = f["place"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes dialogue and the word "phenomenon". '
        f'The story should show a child seeing a {phenomenon.label} at {place.label}.',
        f"Tell a gentle rhyming story where {child.id} wants to hurry toward a sky wonder, but {helper.label_word} "
        f"helps {child.pronoun('object')} enjoy it safely.",
        f'Write a short lyrical story with repeated sounds, spoken lines, and a calm ending that teaches children '
        f'they do not need to grab every beautiful thing they see.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    phenomenon = f["phenomenon"]
    place = f["place"]
    response = f["response"]
    pred = f.get("predicted_risk", {})
    outcome = f.get("outcome", "calm")
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {child.pronoun('possessive')} {helper.label_word}. "
            f"Together they notice a {phenomenon.label} at {place.label}."
        ),
        (
            f"What did {child.id} see?",
            f"{child.id} saw a {phenomenon.label} in the sky and called it a phenomenon. "
            f"The sight filled {child.pronoun('object')} with wonder and made {child.pronoun('object')} want to act quickly."
        ),
    ]
    if phenomenon.hazard == "slip":
        items.append((
            f"Why did {helper.label_word} tell {child.id} to slow down?",
            f"{helper.label_word.capitalize()} knew the wet path could make little feet slip. "
            f"In the world model, chasing the rainbow raised slip risk to {int(pred.get('slip_risk', 0))}, so slowing down kept the moment safe."
        ))
    elif phenomenon.hazard == "glare":
        items.append((
            f"Why did {helper.label_word} move {child.id} into shade?",
            f"{helper.label_word.capitalize()} wanted to protect {child.id}'s eyes from the hard brightness near the sun. "
            f"In the simulation, staring raised glare risk to {int(pred.get('glare_risk', 0))}, so shade and careful glancing were the safe fix."
        ))
    else:
        items.append((
            f"Why did {helper.label_word} bring {child.id} to the window?",
            f"{helper.label_word.capitalize()} did not want the evening chill to make {child.id} shiver. "
            f"In the simulation, lingering outdoors raised cold risk to {int(pred.get('cold_risk', 0))}, so warmth let them keep watching safely."
        ))
    if outcome == "near_miss":
        items.append((
            "Did anything almost go wrong?",
            f"Yes. There was a small near-miss before the safe plan was fully followed. "
            f"That tiny scare helped {child.id} understand why {response.label} was wiser."
        ))
    else:
        items.append((
            "How did the problem get solved?",
            f"The problem was solved before anything scary happened. "
            f"{helper.label_word.capitalize()} used {response.label}, and that turned rushing into calm watching."
        ))
    items.append((
        "How did the story end?",
        f"It ended with {child.id} and {helper.label_word} safely admiring the {phenomenon.label} together. "
        f"The ending image proves what changed: wonder stayed, but the unsafe impulse was gone."
    ))
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"phenomenon"}
    tags |= set(world.facts["phenomenon"].tags)
    tags |= set(world.facts["response"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_place(place: Place, phenomenon: Phenomenon) -> str:
    return (
        f"(No story: {place.label} is not a good fit for seeing a {phenomenon.label} in this tiny world. "
        f"Pick a place that supports that sky sight.)"
    )


def explain_response(response: Response, phenomenon: Phenomenon) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Choose a safer way to admire the {phenomenon.label}.)"
        )
    return (
        f"(No story: response '{response.id}' does not solve the {phenomenon.hazard} risk of a {phenomenon.label}. "
        f"Pick a response that actually handles that risk.)"
    )


ASP_RULES = r"""
supports(P, Ph) :- place(P), phenomenon(Ph), affords(P, Ph), need_tag(Ph, none).
supports(P, Ph) :- place(P), phenomenon(Ph), affords(P, Ph), need_tag(Ph, Tag), has_tag(P, Tag).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
handles_hazard(Ph, R) :- phenomenon(Ph), hazard(Ph, H), response(R), handles(R, H).

valid(P, Ph, R) :- supports(P, Ph), sensible(R), handles_hazard(Ph, R).

near_miss :- delay(D), D > 0.
outcome(near_miss) :- near_miss.
outcome(calm) :- not near_miss.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for phenomenon_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, phenomenon_id))
        for tag in sorted(place.tags):
            lines.append(asp.fact("has_tag", place_id, tag))
    for phenomenon_id, phenomenon in PHENOMENA.items():
        lines.append(asp.fact("phenomenon", phenomenon_id))
        lines.append(asp.fact("hazard", phenomenon_id, phenomenon.hazard))
        need_tag = phenomenon.need_place_tag if phenomenon.need_place_tag in {"garden", "hill", "window"} else "none"
        lines.append(asp.fact("need_tag", phenomenon_id, need_tag))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for hazard in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, hazard))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("delay", params.delay)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "near_miss" if params.delay > 0 else "calm"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child sees a sky phenomenon, feels a risky impulse, and learns a safe way to wonder."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--phenomenon", choices=PHENOMENA)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="1 adds a tiny near-miss before the safe fix")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check Python and ASP parity, plus smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.phenomenon:
        if not place_supports(PLACES[args.place], PHENOMENA[args.phenomenon]):
            raise StoryError(explain_place(PLACES[args.place], PHENOMENA[args.phenomenon]))
    if args.response and args.phenomenon:
        if not valid_combo(
            args.place or next(iter(PLACES)),
            args.phenomenon,
            args.response,
        ) and PHENOMENA[args.phenomenon].hazard not in RESPONSES[args.response].handles:
            raise StoryError(explain_response(RESPONSES[args.response], PHENOMENA[args.phenomenon]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        ph = PHENOMENA[args.phenomenon] if args.phenomenon else next(iter(PHENOMENA.values()))
        raise StoryError(explain_response(RESPONSES[args.response], ph))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.phenomenon is None or combo[1] == args.phenomenon)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, phenomenon_id, response_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        place=place_id,
        phenomenon=phenomenon_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.phenomenon not in PHENOMENA:
        raise StoryError(f"(Unknown phenomenon: {params.phenomenon})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not valid_combo(params.place, params.phenomenon, params.response):
        place = PLACES[params.place]
        phenomenon = PHENOMENA[params.phenomenon]
        response = RESPONSES[params.response]
        if not place_supports(place, phenomenon):
            raise StoryError(explain_place(place, phenomenon))
        raise StoryError(explain_response(response, phenomenon))

    world = tell(
        PLACES[params.place],
        PHENOMENA[params.phenomenon],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
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

    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: valid combos match ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in ASP:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in Python:", sorted(py_combos - asp_combos))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  python:", sorted(py_sensible))
        print("  asp   :", sorted(asp_sense))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if outcome_of(p) != asp_outcome(p)]
    if not mismatches:
        print(f"OK: outcomes match on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, phenomenon, response) combos:\n")
        for place_id, phenomenon_id, response_id in combos:
            print(f"  {place_id:10} {phenomenon_id:10} {response_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.phenomenon} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
