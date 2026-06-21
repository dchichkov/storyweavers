#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/star_beverage_bureaucracy_moral_value_surprise_transformation.py
================================================================================================

A standalone storyworld for a tiny space adventure about a child courier, a
special drink for a little star, and a piece of space-station bureaucracy that
turns into a lesson about honesty, patience, and kindness.

The domain is deliberately small and constraint-checked:

- A destination star has a specific need: warmth, wakefulness, or soothing.
- A beverage must actually fit that need.
- A bureaucratic obstacle must be handled by a sensible response.
- Known bad shortcuts like fake stamps exist in the world model but are refused.

Every valid story has:
- a clear mission,
- a delay or snag inside the beverage bureaucracy,
- a moral choice,
- a surprise stamp-and-glow transformation,
- and an ending image showing the star physically changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/star_beverage_bureaucracy_moral_value_surprise_transformation.py
    python storyworlds/worlds/gpt-5.4/star_beverage_bureaucracy_moral_value_surprise_transformation.py --all
    python storyworlds/worlds/gpt-5.4/star_beverage_bureaucracy_moral_value_surprise_transformation.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/star_beverage_bureaucracy_moral_value_surprise_transformation.py --qa
    python storyworlds/worlds/gpt-5.4/star_beverage_bureaucracy_moral_value_surprise_transformation.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        robot = {"robot", "drone"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in robot:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StarCfg:
    id: str
    label: str
    phrase: str
    need: str
    symptom: str
    place: str
    request: str
    healed: str
    ending_image: str
    transformed_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BeverageCfg:
    id: str
    label: str
    phrase: str
    effect: str
    color: str
    aroma: str
    pour: str
    transformed_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObstacleCfg:
    id: str
    label: str
    phrase: str
    issue: str
    severity: int
    problem_text: str
    temptation_text: str
    solved_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ResponseCfg:
    id: str
    label: str
    virtue: str
    sense: int
    power: int
    handles: set[str] = field(default_factory=set)
    act_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    star: str
    beverage: str
    obstacle: str
    response: str
    hero_name: str
    hero_gender: str
    seed: Optional[int] = None


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clerk_trust(world: World) -> list[str]:
    hero = world.get("hero")
    clerk = world.get("clerk")
    if hero.memes["virtue"] < THRESHOLD or world.facts.get("obstacle_resolved") is not True:
        return []
    sig = ("trust",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clerk.memes["trust"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    beverage = world.get("beverage")
    star = world.get("star")
    clerk = world.get("clerk")
    if beverage.meters["stamped"] < THRESHOLD:
        return []
    if clerk.memes["trust"] < THRESHOLD:
        return []
    if beverage.attrs.get("effect") != star.attrs.get("need"):
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    beverage.meters["transformed"] += 1
    beverage.meters["glow"] += 1
    clerk.memes["wonder"] += 1
    return ["__transform__"]


def _r_heal_star(world: World) -> list[str]:
    beverage = world.get("beverage")
    star = world.get("star")
    hero = world.get("hero")
    if star.meters["drank"] < THRESHOLD:
        return []
    if beverage.attrs.get("effect") != star.attrs.get("need"):
        return []
    sig = ("heal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    star.meters["bright"] += 1
    star.meters["steady"] += 1
    star.meters["trouble"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    return ["__healed__"]


CAUSAL_RULES = [
    Rule(name="clerk_trust", tag="social", apply=_r_clerk_trust),
    Rule(name="transform", tag="magic", apply=_r_transform),
    Rule(name="heal_star", tag="physical", apply=_r_heal_star),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for _ in range(len(CAUSAL_RULES) + 4):
        before = set(world.fired)
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
        if world.fired == before:
            break
    if narrate:
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


def beverage_matches_star(beverage: BeverageCfg, star: StarCfg) -> bool:
    return beverage.effect == star.need


def response_handles_obstacle(response: ResponseCfg, obstacle: ObstacleCfg) -> bool:
    return obstacle.id in response.handles and response.power >= obstacle.severity


def sensible_responses() -> list[ResponseCfg]:
    return [cfg for cfg in RESPONSES.values() if cfg.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for star_id, star in STARS.items():
        for bev_id, bev in BEVERAGES.items():
            if not beverage_matches_star(bev, star):
                continue
            for obs_id, obs in OBSTACLES.items():
                for resp_id, resp in RESPONSES.items():
                    if resp.sense >= SENSE_MIN and response_handles_obstacle(resp, obs):
                        combos.append((star_id, bev_id, obs_id, resp_id))
    return combos


def explain_beverage_mismatch(star: StarCfg, beverage: BeverageCfg) -> str:
    return (
        f"(No story: {star.label} needs a drink that brings {star.need}, but "
        f"{beverage.label} brings {beverage.effect}. The beverage must honestly fit "
        f"the star's problem.)"
    )


def explain_response_rejection(response: ResponseCfg) -> str:
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response.id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). In this world, the child must solve "
        f"bureaucracy with honesty, patience, or kindness. Try: {better}.)"
    )


def explain_response_mismatch(obstacle: ObstacleCfg, response: ResponseCfg) -> str:
    return (
        f"(No story: {response.label} does not sensibly solve {obstacle.label}. "
        f"The response must actually handle the bureaucratic problem.)"
    )


def predict_success(star: StarCfg, beverage: BeverageCfg, obstacle: ObstacleCfg, response: ResponseCfg) -> bool:
    return beverage_matches_star(beverage, star) and response_handles_obstacle(response, obstacle)


def introduce(world: World, hero: Entity, helper: Entity, star: Entity, beverage: Entity,
              star_cfg: StarCfg, beverage_cfg: BeverageCfg) -> None:
    hero.memes["care"] += 1
    world.say(
        f"Far above the sleeping blue world, {hero.id} zipped through the glass halls of Orbit Lantern with "
        f"{helper.id}, a little drone that whirred like a happy cricket."
    )
    world.say(
        f"In {hero.pronoun('possessive')} careful hands was {beverage_cfg.phrase}, "
        f"a {beverage_cfg.color} star beverage that smelled of {beverage_cfg.aroma}."
    )
    world.say(
        f"It was for {star_cfg.phrase} in {star_cfg.place}, who had sent a message saying "
        f"{star_cfg.request} because {star_cfg.symptom}."
    )


def arrive_at_bureau(world: World, hero: Entity, obstacle_cfg: ObstacleCfg) -> None:
    office = world.get("office")
    office.meters["busy"] += 1
    world.say(
        f"But before any ship, tube, or lift could cross the station core, everyone had to stop at "
        f"the Star Beverage Bureaucracy, a round office full of windows, stamps, tiny bells, and floating forms."
    )
    world.say(
        f"At Window Seven, a sign blinked: {obstacle_cfg.phrase}. {obstacle_cfg.problem_text}"
    )
    hero.memes["worry"] += 1


def temptation(world: World, hero: Entity, obstacle_cfg: ObstacleCfg) -> None:
    hero.memes["tempted"] += 1
    world.say(obstacle_cfg.temptation_text.replace("{hero}", hero.id))


def choose_virtue(world: World, hero: Entity, clerk: Entity, obstacle_cfg: ObstacleCfg,
                  response_cfg: ResponseCfg) -> None:
    world.facts["obstacle_resolved"] = True
    hero.memes["virtue"] += 1
    hero.memes[response_cfg.virtue] += 1
    clerk.memes["noticed"] += 1
    world.say(response_cfg.act_text.replace("{hero}", hero.id).replace("{clerk}", clerk.id))
    world.say(obstacle_cfg.solved_text)
    propagate(world, narrate=False)


def stamp_beverage(world: World, clerk: Entity, beverage: Entity,
                   beverage_cfg: BeverageCfg) -> None:
    beverage.meters["stamped"] += 1
    world.say(
        f"{clerk.id} opened a hidden drawer and took out a moon-silver stamp shaped like a tiny spiral star. "
        f'"For travelers who tell the truth and keep their hearts steady," {clerk.pronoun()} said.'
    )
    markers = propagate(world, narrate=False)
    if "__transform__" in markers:
        world.say(
            f"When the stamp kissed the lid, {beverage_cfg.phrase} gave a soft hum. "
            f"It changed into {beverage_cfg.transformed_phrase}, and even the queue lights winked brighter in surprise."
        )
    else:
        world.say(
            f"When the stamp kissed the lid, the cup shone for a moment and then settled down again."
        )


def travel_and_serve(world: World, hero: Entity, helper: Entity, star: Entity,
                     star_cfg: StarCfg, beverage_cfg: BeverageCfg) -> None:
    if world.get("beverage").meters["transformed"] >= THRESHOLD:
        travel_line = (
            f"{hero.id} and {helper.id} rode the ring lift past portholes full of stars, guarding the glowing cup all the way to "
            f"{star_cfg.place}."
        )
    else:
        travel_line = (
            f"{hero.id} and {helper.id} rode the ring lift past portholes full of stars, hurrying the cup to {star_cfg.place}."
        )
    world.say(travel_line)
    world.say(
        f"There they found {star_cfg.phrase}. {star_cfg.symptom.capitalize()}."
    )
    star.meters["drank"] += 1
    markers = propagate(world, narrate=False)
    if "__healed__" in markers:
        world.say(
            f"{hero.id} tipped the cup. {beverage_cfg.pour.capitalize()} into the little star, and {star_cfg.healed}"
        )
    else:
        world.say(
            f"{hero.id} tipped the cup, and the star sipped politely, but not much changed."
        )


def ending(world: World, hero: Entity, clerk: Entity, star_cfg: StarCfg) -> None:
    star = world.get("star")
    if star.meters["bright"] >= THRESHOLD:
        world.say(
            f"Soon {star_cfg.ending_image}."
        )
        world.say(
            f"{hero.id} smiled so hard {hero.pronoun()} almost floated, and {hero.pronoun('possessive')} mind kept circling back to the same surprise: "
            f"the quickest way through space bureaucracy had not been a trick at all. It had been the good choice."
        )
    else:
        world.say(
            f"{hero.id} promised to keep trying, because even in a station full of forms and stamps, care still mattered."
        )
    if clerk.memes["trust"] >= THRESHOLD:
        world.say(
            f"Back at Window Seven, {clerk.id} hung a new sign that read: KIND HEARTS, EXACT FORMS, BRIGHT STARS."
        )


def tell(star_cfg: StarCfg, beverage_cfg: BeverageCfg, obstacle_cfg: ObstacleCfg,
         response_cfg: ResponseCfg, hero_name: str = "Nova",
         hero_gender: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type="drone", label="Pip", role="helper"))
    clerk = world.add(Entity(id="clerk", kind="character", type="robot", label="Clerk Orbi", role="clerk"))
    office = world.add(Entity(id="office", kind="thing", type="office", label="the bureau", role="office"))
    star = world.add(
        Entity(
            id="star",
            kind="character",
            type="star",
            label=star_cfg.label,
            phrase=star_cfg.phrase,
            role="star",
            attrs={"need": star_cfg.need},
            tags=set(star_cfg.tags),
        )
    )
    beverage = world.add(
        Entity(
            id="beverage",
            kind="thing",
            type="drink",
            label=beverage_cfg.label,
            phrase=beverage_cfg.phrase,
            role="beverage",
            attrs={"effect": beverage_cfg.effect},
            tags=set(beverage_cfg.tags),
        )
    )
    star.meters["trouble"] += 1

    introduce(world, hero, helper, star, beverage, star_cfg, beverage_cfg)
    world.para()
    arrive_at_bureau(world, hero, obstacle_cfg)
    temptation(world, hero, obstacle_cfg)
    choose_virtue(world, hero, clerk, obstacle_cfg, response_cfg)
    world.para()
    stamp_beverage(world, clerk, beverage, beverage_cfg)
    travel_and_serve(world, hero, helper, star, star_cfg, beverage_cfg)
    world.para()
    ending(world, hero, clerk, star_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        clerk=clerk,
        office=office,
        star=star,
        beverage=beverage,
        star_cfg=star_cfg,
        beverage_cfg=beverage_cfg,
        obstacle_cfg=obstacle_cfg,
        response_cfg=response_cfg,
        transformed=beverage.meters["transformed"] >= THRESHOLD,
        healed=star.meters["bright"] >= THRESHOLD,
        outcome="transformed" if beverage.meters["transformed"] >= THRESHOLD and star.meters["bright"] >= THRESHOLD else "plain",
    )
    return world


STARS = {
    "shivery": StarCfg(
        id="shivery",
        label="the Shivery Star",
        phrase="the Shivery Star",
        need="warm",
        symptom="its points were tucked in close and blue with cold",
        place="the outer beacon nest",
        request="its lantern lane was going dim",
        healed="its points unfolded, gold warmth ran through every arm, and the whole little star stopped shivering",
        ending_image="the Shivery Star was sailing slow circles above the beacon nest, glowing like a spoonful of sunrise",
        transformed_name="Sun-Crowned Cocoa",
        tags={"star", "warmth"},
    ),
    "sleepy": StarCfg(
        id="sleepy",
        label="the Sleepy Star",
        phrase="the Sleepy Star",
        need="wake",
        symptom="its light kept blinking shut in the middle of each twinkle",
        place="the dawn dock",
        request="morning ships needed a bright guide",
        healed="its eyes popped wide, its rays stretched long, and bright silver sparks skipped from point to point",
        ending_image="the Sleepy Star was hopping over the dock rails, bright enough to paint the air with morning stripes",
        transformed_name="Comet-Ring Fizz",
        tags={"star", "morning"},
    ),
    "scratchy": StarCfg(
        id="scratchy",
        label="the Scratchy Star",
        phrase="the Scratchy Star",
        need="soothe",
        symptom="its glow rasped and fluttered as if every sparkle had a hiccup",
        place="the hush garden dome",
        request="it could not sing the bedtime tune for the moon moths",
        healed="its glow smoothed out into a soft steady song, and the shaky hiccup-sparks faded away",
        ending_image="the Scratchy Star was floating above the moon moths, singing a gentle silver note that made the whole dome feel calm",
        transformed_name="Lullaby Milk",
        tags={"star", "calm"},
    ),
}

BEVERAGES = {
    "sun_cocoa": BeverageCfg(
        id="sun_cocoa",
        label="sun cocoa",
        phrase="a thermos of sun cocoa",
        effect="warm",
        color="golden-brown",
        aroma="cinnamon clouds",
        pour="a ribbon of warm gold",
        transformed_phrase="Sun-Crowned Cocoa, glowing with tiny warm rings",
        tags={"beverage", "cocoa"},
    ),
    "comet_fizz": BeverageCfg(
        id="comet_fizz",
        label="comet fizz",
        phrase="a sealed cup of comet fizz",
        effect="wake",
        color="silver-blue",
        aroma="lime sparks",
        pour="a stream of bright bubbles",
        transformed_phrase="Comet-Ring Fizz, sparkling with little racing tails",
        tags={"beverage", "fizz"},
    ),
    "nebula_milk": BeverageCfg(
        id="nebula_milk",
        label="nebula milk",
        phrase="a warm flask of nebula milk",
        effect="soothe",
        color="pearl-white",
        aroma="vanilla mist",
        pour="a slow silver-white swirl",
        transformed_phrase="Lullaby Milk, shining with quiet moon dots",
        tags={"beverage", "milk"},
    ),
}

OBSTACLES = {
    "long_line": ObstacleCfg(
        id="long_line",
        label="a long line",
        phrase="PLEASE TAKE A STAR-SHAPED NUMBER",
        issue="line",
        severity=1,
        problem_text="A line of couriers curled around the room like a sleepy comet tail.",
        temptation_text="{hero} saw a gap near the front and almost darted into it.",
        solved_text="Nobody glared, because there was nothing to glare at. Good patience fit the room better than pushing ever could.",
        tags={"bureaucracy", "line"},
    ),
    "smudged_form": ObstacleCfg(
        id="smudged_form",
        label="a smudged form",
        phrase="SMUDGED FORMS MUST BE SPOKEN ABOUT, NOT HIDDEN",
        issue="form",
        severity=1,
        problem_text="A drip from the cooling pipes had blurred one important square on the delivery slip.",
        temptation_text="{hero} could have folded the blurry corner under a thumb and pretended not to notice.",
        solved_text="The bureau printer chirped, a fresh form slid out, and the little mission could be honest again from top to bottom.",
        tags={"bureaucracy", "form"},
    ),
    "lost_token": ObstacleCfg(
        id="lost_token",
        label="a lost token",
        phrase="MISSING TOKENS REQUIRE A SEARCH",
        issue="token",
        severity=2,
        problem_text="The silver queue token had rolled under three wobbling trays of paperwork.",
        temptation_text="{hero} spotted an old stamp pad nearby and for one tiny second wondered if a pretend mark might be faster.",
        solved_text="Papers were stacked, the real token was found, and the whole window seemed to breathe easier once the right thing was in the right place.",
        tags={"bureaucracy", "token"},
    ),
}

RESPONSES = {
    "wait_politely": ResponseCfg(
        id="wait_politely",
        label="wait politely",
        virtue="patience",
        sense=3,
        power=1,
        handles={"long_line"},
        act_text=(
            '{hero} took a slow breath, stood in line, and even let a wobbling old moon miner go ahead first. '
            '{clerk} watched that with quiet robot eyes.'
        ),
        qa_text="waited politely instead of pushing ahead",
        tags={"patience", "kindness"},
    ),
    "tell_truth": ResponseCfg(
        id="tell_truth",
        label="tell the truth",
        virtue="honesty",
        sense=3,
        power=1,
        handles={"smudged_form"},
        act_text=(
            '{hero} stepped right up to the window and said, "My form got smudged. I do not want to sneak a messy paper past you." '
            '{clerk} gave one surprised little beep.'
        ),
        qa_text="told the truth about the smudged form",
        tags={"honesty"},
    ),
    "help_sort_forms": ResponseCfg(
        id="help_sort_forms",
        label="help sort the forms",
        virtue="kindness",
        sense=4,
        power=2,
        handles={"lost_token"},
        act_text=(
            '{hero} knelt beside the desk, helped {clerk} stack the drifting forms by color and size, and searched carefully until the real token showed up. '
            'That made the whole counter neater than before.'
        ),
        qa_text="helped sort the forms and search for the real token",
        tags={"kindness", "helping"},
    ),
    "fake_stamp": ResponseCfg(
        id="fake_stamp",
        label="make a fake stamp",
        virtue="trick",
        sense=1,
        power=2,
        handles={"lost_token", "smudged_form"},
        act_text="{hero} tried to make a fake stamp.",
        qa_text="made a fake stamp",
        tags={"dishonest"},
    ),
    "shove_ahead": ResponseCfg(
        id="shove_ahead",
        label="shove ahead",
        virtue="rush",
        sense=1,
        power=1,
        handles={"long_line"},
        act_text="{hero} shoved ahead in line.",
        qa_text="shoved ahead in line",
        tags={"rude"},
    ),
}

GIRL_NAMES = ["Nova", "Lyra", "Mira", "Tali", "Suri", "Vega", "Iris", "Luma"]
BOY_NAMES = ["Orion", "Milo", "Nico", "Taro", "Jett", "Sol", "Arin", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    star_cfg = f["star_cfg"]
    beverage_cfg = f["beverage_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    response_cfg = f["response_cfg"]
    hero = f["hero"]
    return [
        (
            f'Write a short space-adventure story for a 3-to-5-year-old that includes the words '
            f'"star", "beverage", and "bureaucracy". A child must carry {beverage_cfg.label} through a small space office to help {star_cfg.label}.'
        ),
        (
            f"Tell a gentle story where {hero.label} meets {obstacle_cfg.label} inside a station bureaucracy, chooses {response_cfg.label}, "
            f"and is rewarded with a surprising transformation."
        ),
        (
            f"Write a child-facing moral story set on a space station where the good choice is not a shortcut. "
            f"The ending should show a little star physically changed for the better."
        ),
    ]


KNOWLEDGE = {
    "star": [
        (
            "What is a star?",
            "A star is a huge glowing ball of hot gas in space. In stories, stars can also be tiny friendly characters with feelings and jobs."
        )
    ],
    "bureaucracy": [
        (
            "What is bureaucracy?",
            "Bureaucracy is a system of rules, forms, lines, and stamps that people use to keep things organized. It can feel slow, so honesty and patience matter."
        )
    ],
    "beverage": [
        (
            "What is a beverage?",
            "A beverage is a drink, like milk, tea, cocoa, or juice. In stories, a special beverage can help someone feel better."
        )
    ],
    "honesty": [
        (
            "Why is honesty important?",
            "Honesty helps people trust you. Telling the truth can solve a problem the right way, even when a trick looks faster."
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means staying calm while you wait or work through something slowly. It helps you make a good choice instead of a rushed one."
        )
    ],
    "kindness": [
        (
            "How can kindness help solve a problem?",
            "Kindness can calm people down and make it easier to work together. Sometimes helping first is what opens the door to the real solution."
        )
    ],
    "cocoa": [
        (
            "What is cocoa?",
            "Cocoa is a warm chocolate drink. In a story, a warm drink can help someone who feels cold."
        )
    ],
    "fizz": [
        (
            "What is fizz?",
            "Fizz is a drink with tiny bubbles that pop and sparkle. Bubbly drinks feel lively and energetic."
        )
    ],
    "milk": [
        (
            "Why can warm milk feel soothing?",
            "Warm milk feels gentle and calm. In stories, it is often used to help someone settle down."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "star",
    "beverage",
    "bureaucracy",
    "honesty",
    "patience",
    "kindness",
    "cocoa",
    "fizz",
    "milk",
]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    clerk = f["clerk"]
    star_cfg = f["star_cfg"]
    beverage_cfg = f["beverage_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    response_cfg = f["response_cfg"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child space courier, a helper drone named Pip, and {star_cfg.phrase} who needed help. The story also includes {clerk.label} at the bureau window."
        ),
        (
            "What was the mission?",
            f"{hero.label} had to carry {beverage_cfg.phrase} through the station and bring it to {star_cfg.phrase}. The drink matched what the star needed, so the mission mattered."
        ),
        (
            "What problem did the child meet at the bureau?",
            f"The problem was {obstacle_cfg.label} inside the station bureaucracy. That delay mattered because the drink had to be properly cleared before it could go on to the little star."
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} chose to {response_cfg.qa_text}. That worked because it solved the real bureau problem instead of trying a dishonest shortcut."
        ),
    ]
    if f["transformed"]:
        items.append(
            (
                "What was the surprise transformation?",
                f"After {hero.label} made the good choice, {clerk.label} used a hidden silver stamp and the ordinary drink changed into {beverage_cfg.transformed_phrase}. The surprise came because the bureau rewarded virtue, not tricks."
            )
        )
    if f["healed"]:
        items.append(
            (
                f"How did the star change at the end?",
                f"At the end, {star_cfg.healed}. The final image proves the mission worked because the star looked and acted different afterward."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"star", "beverage", "bureaucracy", f["response_cfg"].virtue}
    beverage_id = f["beverage_cfg"].id
    if beverage_id == "sun_cocoa":
        tags.add("cocoa")
    elif beverage_id == "comet_fizz":
        tags.add("fizz")
    elif beverage_id == "nebula_milk":
        tags.add("milk")
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired if x))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        star="shivery",
        beverage="sun_cocoa",
        obstacle="smudged_form",
        response="tell_truth",
        hero_name="Nova",
        hero_gender="girl",
    ),
    StoryParams(
        star="sleepy",
        beverage="comet_fizz",
        obstacle="long_line",
        response="wait_politely",
        hero_name="Orion",
        hero_gender="boy",
    ),
    StoryParams(
        star="scratchy",
        beverage="nebula_milk",
        obstacle="lost_token",
        response="help_sort_forms",
        hero_name="Lyra",
        hero_gender="girl",
    ),
]


ASP_RULES = r"""
matches(S, B) :- star_needs(S, N), beverage_effect(B, N).
sensible(R) :- response(R), response_sense(R, S), sense_min(M), S >= M.
handles(R, O) :- response_handles(R, O), response_power(R, P), obstacle_severity(O, K), P >= K.
valid(S, B, O, R) :- star(S), beverage(B), obstacle(O), response(R), matches(S, B), sensible(R), handles(R, O).
outcome(S, B, O, R, transformed) :- valid(S, B, O, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for star_id, star in STARS.items():
        lines.append(asp.fact("star", star_id))
        lines.append(asp.fact("star_needs", star_id, star.need))
    for bev_id, bev in BEVERAGES.items():
        lines.append(asp.fact("beverage", bev_id))
        lines.append(asp.fact("beverage_effect", bev_id, bev.effect))
    for obs_id, obs in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obs_id))
        lines.append(asp.fact("obstacle_severity", obs_id, obs.severity))
    for resp_id, resp in RESPONSES.items():
        lines.append(asp.fact("response", resp_id))
        lines.append(asp.fact("response_sense", resp_id, resp.sense))
        lines.append(asp.fact("response_power", resp_id, resp.power))
        for handled in sorted(resp.handles):
            lines.append(asp.fact("response_handles", resp_id, handled))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcomes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show outcome/5."))
    return sorted(set(asp.atoms(model, "outcome")))


def outcome_of(params: StoryParams) -> str:
    star = STARS[params.star]
    beverage = BEVERAGES[params.beverage]
    obstacle = OBSTACLES[params.obstacle]
    response = RESPONSES[params.response]
    if predict_success(star, beverage, obstacle, response) and response.sense >= SENSE_MIN:
        return "transformed"
    return "plain"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    py_outcomes = {
        (p.star, p.beverage, p.obstacle, p.response, outcome_of(p))
        for p in CURATED
    }
    asp_out = set(asp_outcomes())
    for item in py_outcomes:
        if item not in asp_out:
            rc = 1
            print("MISMATCH in outcome:", item)

    try:
        sample = generate(CURATED[0])
        if not sample.story or "star" not in sample.story.lower():
            raise StoryError("smoke test generated an empty or malformed story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a child courier, a star beverage, and a little piece of space bureaucracy."
    )
    ap.add_argument("--star", choices=STARS)
    ap.add_argument("--beverage", choices=BEVERAGES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.star and args.beverage:
        if not beverage_matches_star(BEVERAGES[args.beverage], STARS[args.star]):
            raise StoryError(explain_beverage_mismatch(STARS[args.star], BEVERAGES[args.beverage]))
    if args.response:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            raise StoryError(explain_response_rejection(response))
        if args.obstacle and not response_handles_obstacle(response, OBSTACLES[args.obstacle]):
            raise StoryError(explain_response_mismatch(OBSTACLES[args.obstacle], response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.star is None or combo[0] == args.star)
        and (args.beverage is None or combo[1] == args.beverage)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    star_id, beverage_id, obstacle_id, response_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    return StoryParams(
        star=star_id,
        beverage=beverage_id,
        obstacle=obstacle_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        star_cfg = STARS[params.star]
        beverage_cfg = BEVERAGES[params.beverage]
        obstacle_cfg = OBSTACLES[params.obstacle]
        response_cfg = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not beverage_matches_star(beverage_cfg, star_cfg):
        raise StoryError(explain_beverage_mismatch(star_cfg, beverage_cfg))
    if response_cfg.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(response_cfg))
    if not response_handles_obstacle(response_cfg, obstacle_cfg):
        raise StoryError(explain_response_mismatch(obstacle_cfg, response_cfg))

    world = tell(
        star_cfg=star_cfg,
        beverage_cfg=beverage_cfg,
        obstacle_cfg=obstacle_cfg,
        response_cfg=response_cfg,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (star, beverage, obstacle, response) combos:\n")
        for star_id, bev_id, obs_id, resp_id in combos:
            print(f"  {star_id:8} {bev_id:11} {obs_id:12} {resp_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.hero_name}: {p.beverage} for {p.star} via {p.obstacle} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
