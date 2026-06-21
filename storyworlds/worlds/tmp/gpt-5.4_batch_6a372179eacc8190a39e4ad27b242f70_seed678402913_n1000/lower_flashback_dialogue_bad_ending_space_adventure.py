#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lower_flashback_dialogue_bad_ending_space_adventure.py
==================================================================================

A standalone story world for a small child-facing space adventure with dialogue,
a flashback warning, and sometimes a bad ending.

Premise
-------
Two young space explorers at a moon base want to reach a glowing lookout before
a meteor shower. One route is the quick lower tunnel. The lower tunnel is only
reasonable when the explorers have enough power and the weather is calm enough
for the tunnel lights and doors to keep working. A remembered lesson from a
grown-up creates the flashback beat, and the choice drives either a safe rescue
or a sad ending where the goal is missed and the little rover is lost.

The world model tracks simple physical meters like power, darkness, danger, and
jammed wheels, plus emotional memes like excitement, caution, fear, regret, and
relief. Prose is rendered from stateful beats rather than fixed templates.

Run it
------
python storyworlds/worlds/gpt-5.4/lower_flashback_dialogue_bad_ending_space_adventure.py
python storyworlds/worlds/gpt-5.4/lower_flashback_dialogue_bad_ending_space_adventure.py --route lower_tunnel --weather stormy
python storyworlds/worlds/gpt-5.4/lower_flashback_dialogue_bad_ending_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/lower_flashback_dialogue_bad_ending_space_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/lower_flashback_dialogue_bad_ending_space_adventure.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pilot_female", "captain_female"}
        male = {"boy", "father", "man", "pilot_male", "captain_male"}
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
            "captain_female": "captain",
            "captain_male": "captain",
        }.get(self.type, self.type)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    sight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    speed: int
    risk: int
    dark: bool
    lower: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    label: str
    phrase: str
    strain: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    power: int
    grip: int
    sense: int
    rescue_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MentorLesson:
    id: str
    speaker: str
    quote: str
    memory_intro: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_low_power(world: World) -> list[str]:
    rover = world.get("rover")
    if rover.meters["power"] > 1:
        return []
    sig = ("low_power", "rover")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("tunnel").meters["danger"] += 1
    return ["The rover's power bar dipped into its last blinking square."]


def _r_stuck(world: World) -> list[str]:
    rover = world.get("rover")
    tunnel = world.get("tunnel")
    if rover.meters["jammed"] < THRESHOLD:
        return []
    sig = ("stuck", "rover")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tunnel.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["The rover lurched, tilted, and got stuck between two broken floor rails."]


def _r_dark_tunnel(world: World) -> list[str]:
    tunnel = world.get("tunnel")
    if tunnel.meters["darkness"] < THRESHOLD:
        return []
    sig = ("dark_tunnel", "tunnel")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tunnel.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["The tunnel lights flickered lower and lower until the walls turned shadowy and strange."]


CAUSAL_RULES = [
    Rule(name="low_power", tag="physical", apply=_r_low_power),
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="dark_tunnel", tag="physical", apply=_r_dark_tunnel),
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


DESTINATIONS = {
    "crystal_cave": Destination(
        id="crystal_cave",
        label="Crystal Cave",
        phrase="the Crystal Cave lookout",
        sight="blue crystals that gleamed like stars under the rock",
        tags={"cave", "space"},
    ),
    "meteor_window": Destination(
        id="meteor_window",
        label="Meteor Window",
        phrase="the Meteor Window",
        sight="the long silver rain of a meteor shower across the dark sky",
        tags={"meteor", "space"},
    ),
    "ring_hill": Destination(
        id="ring_hill",
        label="Ring Hill",
        phrase="the top of Ring Hill",
        sight="Saturn's pale rings shining above the little moon base",
        tags={"planet", "space"},
    ),
}

ROUTES = {
    "lower_tunnel": Route(
        id="lower_tunnel",
        label="lower tunnel",
        phrase="the lower tunnel under the base",
        speed=2,
        risk=2,
        dark=True,
        lower=True,
        tags={"lower", "tunnel"},
    ),
    "ridge_path": Route(
        id="ridge_path",
        label="ridge path",
        phrase="the bright ridge path outside the dome",
        speed=1,
        risk=0,
        dark=False,
        lower=False,
        tags={"path", "space"},
    ),
}

WEATHERS = {
    "clear": Weather(
        id="clear",
        label="clear",
        phrase="Outside, the moon dust lay still and the stars looked close enough to touch.",
        strain=0,
        tags={"space"},
    ),
    "windy": Weather(
        id="windy",
        label="windy",
        phrase="Outside, a thin dust wind whispered against the base walls.",
        strain=1,
        tags={"wind", "space"},
    ),
    "stormy": Weather(
        id="stormy",
        label="stormy",
        phrase="Outside, a dust storm scraped across the moon base and made every old bolt groan.",
        strain=2,
        tags={"storm", "space"},
    ),
}

GEAR = {
    "booster_pack": Gear(
        id="booster_pack",
        label="booster battery pack",
        phrase="a booster battery pack",
        power=2,
        grip=0,
        sense=3,
        rescue_text="clicked the booster battery pack into the rover and gave the little engine enough power to crawl free",
        fail_text="clicked in the booster battery pack, but even the extra power could not move the rover",
        qa_text="used the booster battery pack to give the rover enough power to crawl free",
        tags={"battery", "power"},
    ),
    "tow_line": Gear(
        id="tow_line",
        label="magnetic tow line",
        phrase="a magnetic tow line",
        power=0,
        grip=2,
        sense=3,
        rescue_text="threw a magnetic tow line from the service cart and pulled the rover back onto the guide track",
        fail_text="threw the magnetic tow line, but the rover only scraped sideways and stayed trapped",
        qa_text="used a magnetic tow line to pull the rover back onto the guide track",
        tags={"rope", "rescue"},
    ),
    "beacon_only": Gear(
        id="beacon_only",
        label="tiny help beacon",
        phrase="a tiny help beacon",
        power=0,
        grip=0,
        sense=1,
        rescue_text="pressed the tiny help beacon and waited while its weak blink echoed in the dark",
        fail_text="pressed the tiny help beacon, but its weak signal was swallowed by the storm and the thick rock",
        qa_text="pressed a tiny help beacon for help",
        tags={"beacon", "signal"},
    ),
}

LESSONS = {
    "captain": MentorLesson(
        id="captain",
        speaker="Captain Mira",
        quote='"If the lights go lower in the old tunnel, turn back while your power is still high," Captain Mira had told them during safety drill.',
        memory_intro="At that thought, a memory flashed through both children like a little star inside their helmets.",
        tags={"safety", "memory"},
    ),
    "engineer": MentorLesson(
        id="engineer",
        speaker="Engineer Sol",
        quote='"Shortcuts are only smart when your batteries are full and the weather is kind," Engineer Sol had said beside the rover rack.',
        memory_intro="Then a clear old memory came back from training hour.",
        tags={"safety", "memory"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Nova", "Ivy", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Max", "Eli", "Sam", "Theo", "Ben"]
TRAITS = ["careful", "curious", "bold", "thoughtful", "eager"]


def route_reasonable(route: Route, weather: Weather, gear: Gear) -> bool:
    if route.id == "ridge_path":
        return True
    if gear.sense < SENSE_MIN:
        return False
    return route.risk + weather.strain <= gear.power + gear.grip + 1


def sensible_gear() -> list[Gear]:
    return [g for g in GEAR.values() if g.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for dest_id in DESTINATIONS:
        for route_id, route in ROUTES.items():
            for weather_id, weather in WEATHERS.items():
                for gear_id, gear in GEAR.items():
                    if route_reasonable(route, weather, gear):
                        out.append((dest_id, route_id, weather_id, gear_id))
    return out


def difficulty(route: Route, weather: Weather) -> int:
    return route.risk + weather.strain


def can_rescue(route: Route, weather: Weather, gear: Gear) -> bool:
    if route.id != "lower_tunnel":
        return True
    return gear.power + gear.grip >= difficulty(route, weather)


def predict_trip(world: World, route: Route, weather: Weather) -> dict:
    sim = world.copy()
    rover = sim.get("rover")
    tunnel = sim.get("tunnel")
    rover.meters["power"] -= float(route.speed + weather.strain)
    if route.dark and weather.strain >= 1:
        tunnel.meters["darkness"] += 1
    if route.id == "lower_tunnel" and difficulty(route, weather) >= 3:
        rover.meters["jammed"] += 1
    propagate(sim, narrate=False)
    return {
        "low_power": rover.meters["power"] <= 1,
        "jammed": rover.meters["jammed"] >= THRESHOLD,
        "danger": tunnel.meters["danger"],
    }


@dataclass
class StoryParams:
    destination: str
    route: str
    weather: str
    gear: str
    lesson: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def setup_world(
    destination: Destination,
    route: Route,
    weather: Weather,
    gear: Gear,
    lesson: MentorLesson,
    leader: str,
    leader_gender: str,
    partner: str,
    partner_gender: str,
    parent: str,
    trait: str,
) -> World:
    world = World()
    a = world.add(Entity(id=leader, kind="character", type=leader_gender, role="leader", traits=[trait]))
    b = world.add(Entity(id=partner, kind="character", type=partner_gender, role="partner", traits=["careful"]))
    grown = world.add(Entity(id="Captain", kind="character", type=parent, role="grownup", label="the captain"))
    rover = world.add(Entity(id="rover", kind="thing", type="rover", label="little moon rover"))
    tunnel = world.add(Entity(id="tunnel", kind="thing", type="tunnel", label=route.label))
    rover.meters["power"] = 4.0
    a.memes["wonder"] = 1
    b.memes["wonder"] = 1
    world.facts.update(
        leader=a,
        partner=b,
        grownup=grown,
        rover=rover,
        tunnel=tunnel,
        destination=destination,
        route=route,
        weather=weather,
        gear=gear,
        lesson=lesson,
    )
    return world


def introduce(world: World) -> None:
    a = world.facts["leader"]
    b = world.facts["partner"]
    destination = world.facts["destination"]
    weather = world.facts["weather"]
    world.say(
        f"{a.id} and {b.id} were junior explorers at Moonbright Base, and tonight they had one shining goal: reach {destination.phrase} before bedtime."
    )
    world.say(weather.phrase)
    world.say(
        f'Their little rover waited by the air-lock with two silver helmets hooked to its side. "{destination.label} first!" {a.id} said.'
    )


def mission_need(world: World) -> None:
    destination = world.facts["destination"]
    a = world.facts["leader"]
    b = world.facts["partner"]
    world.say(
        f"If they got there in time, they would see {destination.sight}."
    )
    world.say(
        f'"Then let\'s not be slow," {b.id} said, climbing into the rover beside {a.id}.'
    )


def temptation(world: World) -> None:
    a = world.facts["leader"]
    route = world.facts["route"]
    world.say(
        f"{a.id} pointed to the map screen. The fastest line was {route.phrase}."
    )
    if route.lower:
        world.say(
            f'"We can take the lower tunnel and get there before the first streak even starts," {a.id} whispered.'
        )
    else:
        world.say(
            f'"The ridge path is longer, but we can still make it," {a.id} said.'
        )


def flashback_warning(world: World) -> None:
    a = world.facts["leader"]
    b = world.facts["partner"]
    route = world.facts["route"]
    weather = world.facts["weather"]
    lesson = world.facts["lesson"]
    pred = predict_trip(world, route, weather)
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    if route.lower:
        world.say(lesson.memory_intro)
        world.say(lesson.quote)
        world.say(
            f'{b.id} touched the edge of the map. "I remember," {b.pronoun()} said. "If we go that way and the lights drop lower, we should turn back."'
        )
        if pred["danger"] >= 1:
            world.say(
                f'"The storm could make the old tunnel mean," {b.id} added.'
            )
    else:
        world.say(
            f'{b.id} studied the weather screen and nodded. "The bright way feels slower," {b.pronoun()} said, "but it feels wiser too."'
        )
    a.memes["desire"] += 1


def choose_route(world: World) -> None:
    a = world.facts["leader"]
    b = world.facts["partner"]
    route = world.facts["route"]
    if route.id == "ridge_path":
        a.memes["trust"] += 1
        world.say(
            f'{a.id} took a breath. "Okay," {a.pronoun()} said. "No shortcut tonight."'
        )
        return
    a.memes["defiance"] += 1
    world.say(
        f'"Just this once," {a.id} said. "We\'ll be quick."'
    )
    world.say(f"{b.id} did not like it, but the rover door had already slid shut.")


def travel(world: World) -> None:
    route = world.facts["route"]
    weather = world.facts["weather"]
    rover = world.get("rover")
    tunnel = world.get("tunnel")
    rover.meters["power"] -= float(route.speed + weather.strain)
    if route.dark and weather.strain >= 1:
        tunnel.meters["darkness"] += 1
    if route.id == "lower_tunnel" and difficulty(route, weather) >= 3:
        rover.meters["jammed"] += 1
    for kid in world.kids():
        kid.memes["wonder"] += 1
    world.say(
        f"The rover hummed forward into {route.phrase}."
    )
    if route.id == "lower_tunnel":
        world.say(
            "At first the walls shone with old blue guide lights, and the ride felt like flying through a secret river of stars."
        )
    else:
        world.say(
            "Above them, the dark sky opened wide, and tiny stars winked over the ridge."
        )
    propagate(world, narrate=True)


def safe_arrival(world: World) -> None:
    destination = world.facts["destination"]
    a = world.facts["leader"]
    b = world.facts["partner"]
    world.say(
        f"Soon the rover rolled out safely, and {destination.phrase} opened before them."
    )
    world.say(
        f"They saw {destination.sight}, and the long trip felt worth every careful choice."
    )
    world.say(
        f'"We made it the smart way," {b.id} said. {a.id} smiled and leaned shoulder to shoulder with {b.id} under the shining sky.'
    )


def rescue_attempt(world: World) -> None:
    grown = world.facts["grownup"]
    gear = world.facts["gear"]
    route = world.facts["route"]
    weather = world.facts["weather"]
    a = world.facts["leader"]
    b = world.facts["partner"]
    world.say(
        f'"Captain!" {a.id} shouted into the radio. "{world.get("rover").label} is stuck!"'
    )
    world.say(
        f'Static cracked, and then {grown.label_word} answered, "Stay together. I am coming."'
    )
    if can_rescue(route, weather, gear):
        world.say(
            f"Soon the service cart reached them, and {grown.label_word} {gear.rescue_text}."
        )
        world.get("rover").meters["jammed"] = 0.0
        world.get("tunnel").meters["danger"] = 0.0
        for kid in world.kids():
            kid.memes["relief"] += 1
            kid.memes["fear"] = 0.0
        world.say(
            f'{b.id} let out a shaky breath. "{gear.label.capitalize()} for the win," {b.pronoun()} said.'
        )
        world.say(
            "They did not reach the lookout in time, but they reached home safely, and that mattered more."
        )
        world.facts["outcome"] = "rescued"
    else:
        for kid in world.kids():
            kid.memes["regret"] += 1
        world.say(
            f"The radio hissed again, but {gear.fail_text}."
        )
        world.say(
            "The storm kept the captain away until morning. By then the meteor shower was over, and the little rover had to be left in the tunnel for parts."
        )
        world.say(
            f'{a.id} pressed {a.pronoun("possessive")} helmet against the cold window. "I should have listened," {a.pronoun()} whispered.'
        )
        world.say(
            f"{b.id} nodded sadly. They were safe, but the adventure ended in darkness, a missed wonder, and one empty place in the rover bay."
        )
        world.facts["outcome"] = "bad"


def lesson_end(world: World) -> None:
    a = world.facts["leader"]
    b = world.facts["partner"]
    grown = world.facts["grownup"]
    route = world.facts["route"]
    outcome = world.facts["outcome"]
    if outcome == "safe":
        world.say(
            f'Back at the base, {grown.label_word} ruffled both helmets and said, "Good explorers do not have to be the fastest. They have to come back."'
        )
    elif outcome == "rescued":
        world.say(
            f'Back at the base, {grown.label_word} knelt beside them. "A shortcut can grow into a trap," {grown.pronoun()} said. "Next time, when a tunnel looks lower and older, choose the brighter way."'
        )
    else:
        world.say(
            f'When morning came, {grown.label_word} held them close and said, "You came back safe, and I am glad. But the lower tunnel was not worth the risk."'
        )
    if outcome == "bad":
        world.say(
            "After that, the map screen still showed the shortcut, but neither child reached for it first."
        )
    elif route.id == "ridge_path":
        world.say(
            "After that, the bright ridge path felt less like the slow way and more like the brave way."
        )
    else:
        world.say(
            "After that, every blinking warning light meant something real to them."
        )


def tell(
    destination: Destination,
    route: Route,
    weather: Weather,
    gear: Gear,
    lesson: MentorLesson,
    leader: str,
    leader_gender: str,
    partner: str,
    partner_gender: str,
    parent: str,
    trait: str,
) -> World:
    world = setup_world(
        destination=destination,
        route=route,
        weather=weather,
        gear=gear,
        lesson=lesson,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
    )

    introduce(world)
    mission_need(world)

    world.para()
    temptation(world)
    flashback_warning(world)
    choose_route(world)

    world.para()
    travel(world)

    if route.id == "ridge_path":
        world.facts["outcome"] = "safe"
        world.para()
        safe_arrival(world)
    else:
        world.para()
        rescue_attempt(world)

    world.para()
    lesson_end(world)
    world.facts["goal_seen"] = world.facts["outcome"] == "safe"
    return world


KNOWLEDGE = {
    "lower": [(
        "What does lower mean?",
        "Lower means farther down. In a tunnel or a building, a lower place is beneath a higher one."
    )],
    "tunnel": [(
        "What is a tunnel?",
        "A tunnel is a passage that goes under or through something. It can feel dark because the walls are close around you."
    )],
    "meteor": [(
        "What is a meteor shower?",
        "A meteor shower is when many tiny space rocks burn bright as they race through the sky. From the ground, they look like quick streaks of light."
    )],
    "battery": [(
        "What does a battery pack do?",
        "A battery pack stores power for a machine. If a rover is low on power, a fresh battery pack can help it move again."
    )],
    "rope": [(
        "What is a tow line for?",
        "A tow line is used to pull something that is stuck. It helps another vehicle tug it back to a safer place."
    )],
    "beacon": [(
        "What is a beacon?",
        "A beacon is a signal light or signal tool used to call attention. A weak beacon is not always enough in a storm or behind thick walls."
    )],
    "storm": [(
        "Why can a storm make travel harder?",
        "A storm can make it hard to see and can push dust or wind into the way. That can make machines lose power faster or get stuck."
    )],
    "safety": [(
        "Why do explorers turn back when something feels unsafe?",
        "Good explorers turn back because getting home safely matters more than winning a race. A careful choice can stop a small problem from becoming a big one."
    )],
}
KNOWLEDGE_ORDER = ["lower", "tunnel", "meteor", "battery", "rope", "beacon", "storm", "safety"]


def generation_prompts(world: World) -> list[str]:
    a = world.facts["leader"]
    b = world.facts["partner"]
    destination = world.facts["destination"]
    route = world.facts["route"]
    outcome = world.facts["outcome"]
    base = (
        f'Write a space adventure for a 3-to-5-year-old that includes the word "lower", uses dialogue, and contains a flashback.'
    )
    if outcome == "bad":
        return [
            base,
            f"Tell a sad but child-safe story where {a.id} chooses the {route.label}, ignores a remembered warning, and misses {destination.phrase}.",
            "Write a story with a bad ending where the heroes are safe but lose their chance to see something wonderful because they took the risky shortcut.",
        ]
    if outcome == "rescued":
        return [
            base,
            f"Tell a moon-base story where {a.id} and {b.id} take the lower tunnel, get into trouble, and must call a captain for help.",
            "Write a gentle cautionary space story where dialogue and a remembered lesson help explain why shortcuts can become traps.",
        ]
    return [
        base,
        f"Tell a space story where {a.id} and {b.id} want to reach {destination.phrase}, remember a safety lesson, and choose the wiser path.",
        "Write a simple story that uses a flashback warning and ends with a bright view that proves careful choices were worth it.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    a = world.facts["leader"]
    b = world.facts["partner"]
    destination = world.facts["destination"]
    route = world.facts["route"]
    weather = world.facts["weather"]
    gear = world.facts["gear"]
    lesson = world.facts["lesson"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two junior explorers, {a.id} and {b.id}, riding a little moon rover. They want to reach {destination.phrase} before bedtime."
        ),
        (
            "What did they want to see?",
            f"They hoped to see {destination.sight}. That goal is why the fast route felt tempting."
        ),
        (
            "What was the flashback about?",
            f"The flashback was a remembered safety lesson from {lesson.speaker}. It warned them to turn back if the old tunnel lights went lower or the trip stopped feeling safe."
        ),
    ]
    if route.id == "lower_tunnel":
        qa.append((
            f"Why did {a.id} want the lower tunnel?",
            f"{a.id} wanted the lower tunnel because it was the fastest shortcut. The children thought speed might help them reach the lookout before the sky show began."
        ))
    else:
        qa.append((
            "Which route did they choose?",
            f"They chose the ridge path instead of the lower tunnel. That choice matched the warning they had remembered."
        ))
    if outcome == "safe":
        qa.append((
            "How did the story end?",
            f"It ended happily and safely. They reached {destination.phrase} and saw {destination.sight} because they chose the wiser route."
        ))
    elif outcome == "rescued":
        qa.append((
            "How were they helped?",
            f"The captain came with {gear.phrase} and {gear.qa_text}. That rescue got them home safely, even though they missed the lookout."
        ))
        qa.append((
            "What did they learn?",
            "They learned that a shortcut can turn into a trap when power, weather, and old equipment all go wrong together. The rescue mattered more than being fast."
        ))
    else:
        qa.append((
            "Why is this a bad ending?",
            f"It is a bad ending because they missed {destination.phrase} and even lost their little rover. They were safe, but the risky choice cost them the wonder they had wanted."
        ))
        qa.append((
            f"What did {a.id} say at the end?",
            f'{a.id} admitted, "I should have listened." That line shows {a.pronoun("possessive")} regret after the remembered warning proved true.'
        ))
        qa.append((
            "How did the weather matter?",
            f"The {weather.label} weather made the old lower tunnel harder and meaner. It helped drain power and made rescue harder too."
        ))
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"safety"}
    route = world.facts["route"]
    destination = world.facts["destination"]
    weather = world.facts["weather"]
    gear = world.facts["gear"]
    lesson = world.facts["lesson"]
    tags |= route.tags | destination.tags | weather.tags | gear.tags | lesson.tags
    if route.lower:
        tags.add("lower")
        tags.add("tunnel")
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} destination={world.facts.get('destination').id}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        destination="meteor_window",
        route="ridge_path",
        weather="stormy",
        gear="tow_line",
        lesson="captain",
        leader="Luna",
        leader_gender="girl",
        partner="Leo",
        partner_gender="boy",
        parent="captain_female",
        trait="careful",
    ),
    StoryParams(
        destination="crystal_cave",
        route="lower_tunnel",
        weather="windy",
        gear="tow_line",
        lesson="engineer",
        leader="Max",
        leader_gender="boy",
        partner="Nova",
        partner_gender="girl",
        parent="captain_male",
        trait="eager",
    ),
    StoryParams(
        destination="ring_hill",
        route="lower_tunnel",
        weather="stormy",
        gear="beacon_only",
        lesson="captain",
        leader="Mia",
        leader_gender="girl",
        partner="Finn",
        partner_gender="boy",
        parent="captain_female",
        trait="bold",
    ),
]


def explain_rejection(route: Route, weather: Weather, gear: Gear) -> str:
    if route.id == "ridge_path":
        return "(No story: the bright ridge path does not need rescue gear; choose a sensible gear or let it be randomized.)"
    if gear.sense < SENSE_MIN:
        return (
            f"(No story: {gear.label} is known in the world, but it is too weak to trust in the old lower tunnel. Pick stronger help like booster_pack or tow_line.)"
        )
    return (
        f"(No story: {gear.label} does not cover the danger of the {route.label} in {weather.label} weather. The shortcut would be unreasonable.)"
    )


ASP_RULES = r"""
sensible_gear(G) :- gear(G), sense(G, S), sense_min(M), S >= M.

reasonable(lower_tunnel, W, G) :- weather(W), gear(G), sensible_gear(G),
                                  route_risk(lower_tunnel, R), strain(W, S),
                                  power(G, P), grip(G, Gr), R + S <= P + Gr + 1.
reasonable(ridge_path, W, G)   :- weather(W), gear(G).

valid(D, R, W, G) :- destination(D), route(R), weather(W), gear(G), reasonable(R, W, G).

rescuable(R, W, G) :- route(R), weather(W), gear(G),
                      route_risk(R, RR), strain(W, S),
                      power(G, P), grip(G, Gr), P + Gr >= RR + S.

outcome(safe)    :- chosen_route(ridge_path).
outcome(rescued) :- chosen_route(lower_tunnel), chosen_weather(W), chosen_gear(G), rescuable(lower_tunnel, W, G).
outcome(bad)     :- chosen_route(lower_tunnel), chosen_weather(W), chosen_gear(G), not rescuable(lower_tunnel, W, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for did in DESTINATIONS:
        lines.append(asp.fact("destination", did))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_risk", rid, route.risk))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("strain", wid, weather.strain))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("sense", gid, gear.sense))
        lines.append(asp.fact("power", gid, gear.power))
        lines.append(asp.fact("grip", gid, gear.grip))
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
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_gear", params.gear),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    route = ROUTES[params.route]
    weather = WEATHERS[params.weather]
    gear = GEAR[params.gear]
    if route.id == "ridge_path":
        return "safe"
    return "rescued" if can_rescue(route, weather, gear) else "bad"


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a - p:
            print("  only in ASP:", sorted(a - p))
        if p - a:
            print("  only in Python:", sorted(p - a))

    checks = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            checks.append(params)
        except StoryError:
            pass
    diff = [(params, asp_outcome(params), outcome_of(params)) for params in checks if asp_outcome(params) != outcome_of(params)]
    if not diff:
        print(f"OK: ASP outcome matches Python on {len(checks)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(diff)} outcome differences.")
        for params, a_out, p_out in diff[:5]:
            print(" ", params, a_out, p_out)

    try:
        sample = generate(CURATED[0])
        if not sample.story or not isinstance(sample.story, str):
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verification
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a moon-base shortcut, a remembered warning, and a risky lower tunnel."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--parent", choices=["captain_female", "captain_male"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.weather and args.gear:
        route = ROUTES[args.route]
        weather = WEATHERS[args.weather]
        gear = GEAR[args.gear]
        if not route_reasonable(route, weather, gear):
            raise StoryError(explain_rejection(route, weather, gear))

    combos = [
        combo for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.route is None or combo[1] == args.route)
        and (args.weather is None or combo[2] == args.weather)
        and (args.gear is None or combo[3] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, route, weather, gear = rng.choice(sorted(combos))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    leader, leader_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=leader)
    parent = args.parent or rng.choice(["captain_female", "captain_male"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        destination=destination,
        route=route,
        weather=weather,
        gear=gear,
        lesson=lesson,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        destination = DESTINATIONS[params.destination]
        route = ROUTES[params.route]
        weather = WEATHERS[params.weather]
        gear = GEAR[params.gear]
        lesson = LESSONS[params.lesson]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if not route_reasonable(route, weather, gear):
        raise StoryError(explain_rejection(route, weather, gear))

    world = tell(
        destination=destination,
        route=route,
        weather=weather,
        gear=gear,
        lesson=lesson,
        leader=params.leader,
        leader_gender=params.leader_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        parent=params.parent,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(f"{len(combos)} compatible (destination, route, weather, gear) combos:\n")
        for destination, route, weather, gear in combos:
            print(f"  {destination:14} {route:12} {weather:7} {gear}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = (
                f"### {p.leader} & {p.partner}: {p.route} in {p.weather} weather "
                f"toward {p.destination} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
