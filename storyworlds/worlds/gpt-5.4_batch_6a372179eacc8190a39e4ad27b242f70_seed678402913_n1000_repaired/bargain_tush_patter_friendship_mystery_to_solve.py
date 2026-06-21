#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bargain_tush_patter_friendship_mystery_to_solve.py
==============================================================================

A standalone story world for a tall-tale friendship mystery.

Premise
-------
Two friends in an exaggerated, larger-than-life place hear a strange patter and
set out to solve the mystery together. They make a bargain to stay side by side,
follow a sensible clue, have a small comic stumble on a tush, and discover that
the scary sound came from something harmless after all.

Run it
------
    python storyworlds/worlds/gpt-5.4/bargain_tush_patter_friendship_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/bargain_tush_patter_friendship_mystery_to_solve.py --place giant_barn --source roof_ducks --method peek_high
    python storyworlds/worlds/gpt-5.4/bargain_tush_patter_friendship_mystery_to_solve.py --source cellar_mice --method peek_high
    python storyworlds/worlds/gpt-5.4/bargain_tush_patter_friendship_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/bargain_tush_patter_friendship_mystery_to_solve.py --qa --json
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str = ""
    label: str = ""
    brag: str = ""
    hide_spot: str = ""
    offers: set[str] = field(default_factory=set)
    climbable: bool = False
    landing: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str = ""
    label: str = ""
    phrase: str = ""
    sound: str = ""
    clue_kind: str = ""
    habitat: str = ""
    reveal: str = ""
    snack: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str = ""
    label: str = ""
    clue_kind: str = ""
    action: str = ""
    question_text: str = ""
    needs_climb: bool = False
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"friend_a", "friend_b"}]

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


def _r_noise_worry(world: World) -> list[str]:
    shed = world.entities.get("mystery")
    if shed is None or shed.meters["noise"] < THRESHOLD:
        return []
    sig = ("noise_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
        kid.memes["curiosity"] += 1
    return []


def _r_bargain_bold(world: World) -> list[str]:
    promise = world.entities.get("promise")
    if promise is None or promise.meters["made"] < THRESHOLD:
        return []
    sig = ("bargain_bold",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["trust"] += 1
        kid.memes["courage"] += 1
    return []


def _r_solve_relief(world: World) -> list[str]:
    mystery = world.entities.get("mystery")
    if mystery is None or mystery.meters["solved"] < THRESHOLD:
        return []
    sig = ("solve_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1
        kid.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_worry", tag="emotional", apply=_r_noise_worry),
    Rule(name="bargain_bold", tag="emotional", apply=_r_bargain_bold),
    Rule(name="solve_relief", tag="emotional", apply=_r_solve_relief),
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
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "giant_barn": Place(
        id="giant_barn",
        label="the giant red barn",
        brag="The barn was so tall that its weather vane seemed to scratch the clouds.",
        hide_spot="the highest hayloft beam",
        offers={"roof", "loft", "crumbs"},
        climbable=True,
        landing="a warm hay bale",
        tags={"barn", "farm"},
    ),
    "thunder_boardwalk": Place(
        id="thunder_boardwalk",
        label="the thunder boardwalk",
        brag="The boardwalk stretched so far that a child could start at one end at breakfast and reach the other by supper.",
        hide_spot="the striped awning above the lemonade stand",
        offers={"roof", "crumbs"},
        climbable=True,
        landing="a pile of sailcloth",
        tags={"boardwalk", "shore"},
    ),
    "whistle_mill": Place(
        id="whistle_mill",
        label="the old whistle mill",
        brag="The mill wheel was so broad that moonlight could nap on one spoke while dawn climbed onto the next.",
        hide_spot="the flour cellar beside the grain bins",
        offers={"tracks", "cellar"},
        climbable=False,
        landing="a sack of soft flour",
        tags={"mill", "grain"},
    ),
}

SOURCES = {
    "roof_ducks": Source(
        id="roof_ducks",
        label="ducks",
        phrase="three rain-fat ducks in shiny boots",
        sound="pitter-patter-plop",
        clue_kind="high",
        habitat="roof",
        reveal="Three rain-fat ducks were waddling across the roof in tiny shiny boots, tapping out the grandest patter in the county.",
        snack="pepper biscuits",
        tags={"duck", "roof", "patter"},
    ),
    "cellar_mice": Source(
        id="cellar_mice",
        label="mice",
        phrase="a string of flour-dusted mice",
        sound="pit-pat skitter",
        clue_kind="tracks",
        habitat="cellar",
        reveal="A string of flour-dusted mice was hurrying between the grain bins, and their little feet were making a busy patter on the wooden floor.",
        snack="oat crumbs",
        tags={"mouse", "tracks", "patter"},
    ),
    "jam_beetles": Source(
        id="jam_beetles",
        label="beetles",
        phrase="jam-slick beetles",
        sound="tik-tik patter",
        clue_kind="crumbs",
        habitat="crumbs",
        reveal="A parade of jam-slick beetles had followed the sweet smell of crumbs, and their tiny shells were drumming a cheerful patter wherever they marched.",
        snack="strawberry crumbs",
        tags={"beetle", "crumbs", "patter"},
    ),
}

METHODS = {
    "peek_high": Method(
        id="peek_high",
        label="peek up high",
        clue_kind="high",
        action="climb up and peek at the high place where the sound was landing",
        question_text="They solved the mystery by climbing high enough to see what was making the noise.",
        needs_climb=True,
        tags={"look_up", "climb"},
    ),
    "follow_tracks": Method(
        id="follow_tracks",
        label="follow the tracks",
        clue_kind="tracks",
        action="follow the dusty little tracks across the floor",
        question_text="They solved the mystery by following the tiny tracks left by the noisemaker.",
        needs_climb=False,
        tags={"tracks"},
    ),
    "crumb_bargain": Method(
        id="crumb_bargain",
        label="set a crumb bargain",
        clue_kind="crumbs",
        action="set out a small bargain of sweet crumbs and wait as still as fence posts",
        question_text="They solved the mystery by leaving a sweet crumb bargain and waiting for the sound-maker to come out.",
        needs_climb=False,
        tags={"crumbs", "bargain"},
    ),
}


def source_fits_place(place: Place, source: Source) -> bool:
    return source.habitat in place.offers


def method_fits(place: Place, source: Source, method: Method) -> bool:
    if method.clue_kind != source.clue_kind:
        return False
    if method.needs_climb and not place.climbable:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for sid, source in SOURCES.items():
            if not source_fits_place(place, source):
                continue
            for mid, method in METHODS.items():
                if method_fits(place, source, method):
                    combos.append((pid, sid, mid))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    source: str
    method: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    parent: str
    mood: str
    seed: Optional[int] = None


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"{a.id} and {b.id} were the sort of friends who could turn one afternoon into a whole legend. "
        f"They met at {place.label}, and {place.brag}"
    )
    world.say(
        f"Nobody in town could ever tell which of the two had the bigger grin, only that they shared it."
    )


def stir_mystery(world: World, a: Entity, b: Entity, place: Place, source: Source) -> None:
    mystery = world.get("mystery")
    mystery.meters["noise"] += 1
    propagate(world, narrate=False)
    worried = "their knees gave one polite wobble" if a.memes["worry"] >= THRESHOLD else "they listened hard"
    world.say(
        f"Then the air filled with a strange patter from somewhere near {place.label} -- "
        f'"{source.sound}! {source.sound}!" -- and {worried}.'
    )
    world.say(
        f'"That sounds bigger than a wagon and sneakier than a squirrel," {b.id} whispered.'
    )


def make_bargain(world: World, a: Entity, b: Entity) -> None:
    promise = world.get("promise")
    promise.meters["made"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Let us make a bargain," said {a.id}. "No matter how jumpy the mystery sounds, '
        f'we stay together till we know the truth."'
    )
    world.say(f'"Bargain," said {b.id}, and they slapped palms so briskly that even the dust seemed to cheer.')


def choose_plan(world: World, a: Entity, b: Entity, method: Method) -> None:
    trusty = "Because the bargain had put starch in their courage" if a.memes["trust"] >= THRESHOLD else "After a breath"
    world.say(
        f"{trusty}, the two friends decided to {method.action}."
    )


def comic_tumble(world: World, a: Entity, place: Place) -> None:
    a.meters["bump"] += 1
    world.say(
        f"On the way, {a.id} slipped on a proud little drift of dust and sat down on {a.pronoun('possessive')} tush with a soft whump on {place.landing}."
    )
    world.say(
        f'{a.pronoun().capitalize()} blinked once, then laughed. "Well, now my tush knows this mystery is real."'
    )


def investigate(world: World, a: Entity, b: Entity, place: Place, source: Source, method: Method) -> None:
    clue = world.get("clue")
    clue.meters["found"] += 1
    world.facts["used_method_text"] = method.question_text
    if method.id == "peek_high":
        world.say(
            f"They climbed carefully, rung by rung, until the rafters seemed to float as high as clouds."
        )
    elif method.id == "follow_tracks":
        world.say(
            f"They bent low and found a line of tiny marks, each one neat as a pencil comma in the dust."
        )
    else:
        world.say(
            f"They sprinkled out {source.snack} on an upside-down crate and stood so still that even their freckles seemed to hold their breath."
        )
    mystery = world.get("mystery")
    mystery.meters["solved"] += 1
    world.get("source").meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(source.reveal)


def resolve(world: World, a: Entity, b: Entity, place: Place, source: Source) -> None:
    relieved = "light as feathers" if a.memes["relief"] >= THRESHOLD else "much steadier"
    world.say(
        f"{a.id} and {b.id} looked at one another, {relieved} now that the mystery had a friendly face."
    )
    world.say(
        f'"So that was the mighty racket," said {b.id}. "Not a monster at all -- just {source.label} with busy feet."'
    )
    world.say(
        f"They left the little visitors a bit more {source.snack}, and as the evening settled over {place.label}, the old scary patter turned into the happiest sound in town."
    )


def tell(
    place: Place,
    source: Source,
    method: Method,
    friend1: str,
    friend1_gender: str,
    friend2: str,
    friend2_gender: str,
    parent_type: str,
    mood: str,
) -> World:
    world = World()
    a = world.add(Entity(id=friend1, kind="character", type=friend1_gender, role="friend_a", traits=[mood], label=friend1))
    b = world.add(Entity(id=friend2, kind="character", type=friend2_gender, role="friend_b", traits=["loyal"], label=friend2))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="mystery", type="mystery", label="the mystery"))
    world.add(Entity(id="promise", type="promise", label="the bargain"))
    world.add(Entity(id="clue", type="clue", label="the clue"))
    world.add(Entity(id="source", type="source", label=source.label, phrase=source.phrase))
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1

    introduce(world, a, b, place)
    world.para()
    stir_mystery(world, a, b, place, source)
    make_bargain(world, a, b)
    choose_plan(world, a, b, method)
    world.para()
    comic_tumble(world, a, place)
    investigate(world, a, b, place, source, method)
    world.para()
    resolve(world, a, b, place, source)

    world.facts.update(
        place=place,
        source_cfg=source,
        method_cfg=method,
        friend1=a,
        friend2=b,
        parent=parent,
        solved=world.get("mystery").meters["solved"] >= THRESHOLD,
        clue_found=world.get("clue").meters["found"] >= THRESHOLD,
    )
    return world


GIRL_NAMES = ["Mabel", "June", "Tess", "Nell", "Daisy", "Ruth", "Hattie", "Cora"]
BOY_NAMES = ["Jed", "Beau", "Eli", "Wade", "Finn", "Cal", "Otis", "Ned"]
MOODS = ["brave", "curious", "sunny", "steady"]

KNOWLEDGE = {
    "barn": [
        (
            "What is a hayloft?",
            "A hayloft is the high part of a barn where hay is stored. It sits above the ground, so people often need to climb to reach it.",
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show that something walked through a place before you saw it. They help you follow where it went or guess what size it was.",
        )
    ],
    "duck": [
        (
            "Why do ducks make little tapping sounds when they walk?",
            "Ducks have small feet that slap and tap on hard surfaces. When several ducks walk together, their steps can sound like a quick patter.",
        )
    ],
    "mouse": [
        (
            "Why can mice sound bigger than they are?",
            "Small feet can make surprisingly loud sounds in a quiet room. When the sound bounces off wood or walls, it can seem larger than the animal.",
        )
    ],
    "beetle": [
        (
            "What is a beetle?",
            "A beetle is a small insect with a hard shell on its back. Some beetles tap lightly as they crawl over wood or paper.",
        )
    ],
    "crumbs": [
        (
            "Why might tiny animals or bugs come to crumbs?",
            "Crumbs smell like food, so small hungry creatures may come to nibble them. Leaving crumbs can help you notice who has been visiting.",
        )
    ],
    "patter": [
        (
            "What does patter mean?",
            "Patter is a light, quick sound made by many small taps, like feet, raindrops, or tiny knocks close together.",
        )
    ],
    "friendship": [
        (
            "How can friends help with a mystery?",
            "Friends can stay brave together and notice different clues. Working together often makes a hard problem easier to solve.",
        )
    ],
    "bargain": [
        (
            "What is a bargain between friends?",
            "A bargain between friends is a promise or agreement they both mean to keep. It helps them know they are on the same side.",
        )
    ],
}
KNOWLEDGE_ORDER = ["patter", "friendship", "bargain", "barn", "tracks", "duck", "mouse", "beetle", "crumbs"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    place = f["place"]
    source = f["source_cfg"]
    method = f["method_cfg"]
    return [
        'Write a tall-tale story for a 3-to-5-year-old that includes the words "bargain," "tush," and "patter."',
        f"Tell a friendship mystery where {a.id} and {b.id} hear a strange patter at {place.label} and solve it by deciding to {method.action}.",
        f"Write a playful tall tale in which a scary-sounding mystery turns out to be harmless {source.label}, and the ending shows the friends are braver together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    place = f["place"]
    source = f["source_cfg"]
    method = f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}. They are close friends who choose to solve the mystery together.",
        ),
        (
            "What mystery did they hear?",
            f"They heard a strange patter near {place.label}. At first the sound seemed big and spooky because they did not know what was making it.",
        ),
        (
            "What bargain did the friends make?",
            f"They made a bargain to stay together until they found the truth. The promise gave them extra courage because neither friend had to face the mystery alone.",
        ),
        (
            f"Why does the story mention {a.id}'s tush?",
            f"{a.id} slipped and landed on {a.pronoun('possessive')} tush while they were investigating. The funny fall breaks the tension and shows the mystery is turning from scary into manageable.",
        ),
        (
            "How did they solve the mystery?",
            f"{method.question_text} That worked because this mystery left the kind of clue their plan could actually use.",
        ),
        (
            "What was making the patter in the end?",
            f"It was {source.phrase}. Once the friends saw the real cause, the noise stopped feeling frightening and started sounding friendly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"patter", "friendship", "bargain"} | set(f["source_cfg"].tags)
    if f["method_cfg"].id == "follow_tracks":
        tags.add("tracks")
    if f["method_cfg"].id == "crumb_bargain":
        tags.add("crumbs")
    tags |= set(f["place"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="giant_barn",
        source="roof_ducks",
        method="peek_high",
        friend1="Mabel",
        friend1_gender="girl",
        friend2="Jed",
        friend2_gender="boy",
        parent="mother",
        mood="brave",
    ),
    StoryParams(
        place="whistle_mill",
        source="cellar_mice",
        method="follow_tracks",
        friend1="Eli",
        friend1_gender="boy",
        friend2="June",
        friend2_gender="girl",
        parent="father",
        mood="curious",
    ),
    StoryParams(
        place="thunder_boardwalk",
        source="jam_beetles",
        method="crumb_bargain",
        friend1="Tess",
        friend1_gender="girl",
        friend2="Cal",
        friend2_gender="boy",
        parent="mother",
        mood="sunny",
    ),
]


def explain_rejection(place: Place, source: Source, method: Method) -> str:
    if not source_fits_place(place, source):
        return (
            f"(No story: {source.label} do not belong in {place.label} in this world, so there would be no honest mystery to solve there.)"
        )
    if method.clue_kind != source.clue_kind:
        return (
            f"(No story: the method '{method.id}' uses {method.clue_kind} clues, but this mystery leaves {source.clue_kind} clues. Pick a method that matches the mystery.)"
        )
    if method.needs_climb and not place.climbable:
        return (
            f"(No story: {place.label} has no sensible climbing route for '{method.id}', so the plan would be unreasonable.)"
        )
    return "(No story: this combination does not make sense in the world.)"


ASP_RULES = r"""
fits_place(P, S) :- place(P), source(S), habitat(S, H), offers(P, H).
fits_method(P, S, M) :- method(M), clue(S, C), method_clue(M, C), fits_place(P, S),
                        not needs_climb(M).
fits_method(P, S, M) :- method(M), clue(S, C), method_clue(M, C), fits_place(P, S),
                        needs_climb(M), climbable(P).
valid(P, S, M) :- fits_method(P, S, M).

solved :- chosen_place(P), chosen_source(S), chosen_method(M), valid(P, S, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.climbable:
            lines.append(asp.fact("climbable", pid))
        for offer in sorted(place.offers):
            lines.append(asp.fact("offers", pid, offer))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("habitat", sid, source.habitat))
        lines.append(asp.fact("clue", sid, source.clue_kind))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_clue", mid, method.clue_kind))
        if method.needs_climb:
            lines.append(asp.fact("needs_climb", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show solved/0."))
    return bool(asp.atoms(model, "solved"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale friendship mystery world. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.method:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        method = METHODS[args.method]
        if not (source_fits_place(place, source) and method_fits(place, source, method)):
            raise StoryError(explain_rejection(place, source, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        if args.place and args.source and args.method:
            raise StoryError(explain_rejection(PLACES[args.place], SOURCES[args.source], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, method_id = rng.choice(sorted(combos))
    friend1, friend1_gender = _pick_name(rng)
    friend2, friend2_gender = _pick_name(rng, avoid=friend1)
    return StoryParams(
        place=place_id,
        source=source_id,
        method=method_id,
        friend1=friend1,
        friend1_gender=friend1_gender,
        friend2=friend2,
        friend2_gender=friend2_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        mood=rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    place = PLACES[params.place]
    source = SOURCES[params.source]
    method = METHODS[params.method]
    if not (source_fits_place(place, source) and method_fits(place, source, method)):
        raise StoryError(explain_rejection(place, source, method))

    world = tell(
        place=place,
        source=source,
        method=method,
        friend1=params.friend1,
        friend1_gender=params.friend1_gender,
        friend2=params.friend2,
        friend2_gender=params.friend2_gender,
        parent_type=params.parent,
        mood=params.mood,
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if not asp_solved(params):
                raise StoryError("ASP failed to mark curated story as solved")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE TEST FAILED for curated params {params}: {err}")
            break
    else:
        print(f"OK: smoke-tested {len(CURATED)} curated stories.")

    parser = build_parser()
    try:
        random_params = resolve_params(parser.parse_args([]), random.Random(7))
        sample = generate(random_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: default generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, method) combos:\n")
        for place, source, method in combos:
            print(f"  {place:18} {source:14} {method}")
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
            header = f"### {p.friend1} & {p.friend2}: {p.source} at {p.place} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
