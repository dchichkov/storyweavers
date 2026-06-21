#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/paddy_know_humor_quest_happy_ending_adventure.py
============================================================================

A standalone story world for a tiny adventure quest with gentle humor and a
happy ending.

Core tale shape
---------------
A child sees a treasured thing blown or bobbed away across a rice paddy.
The child wants to charge straight in, but does not quite know the safe way
across. A nearby farm helper offers a sensible crossing method that fits the
terrain. The quest turns funny in the middle with plops, croaks, and wobbling,
then ends happily when the child reaches the prize and comes back wiser:
when you do not know the safe way, you ask.

This world keeps its coverage narrow on purpose:
- the place is always a rice paddy, so the seed word "paddy" belongs naturally.
- the story always includes "know" in the key lesson beat.
- only reasonable obstacle/method pairs are allowed.
- every valid story ends happily, but some end neat while others end splashy.

Run it
------
python storyworlds/worlds/gpt-5.4/paddy_know_humor_quest_happy_ending_adventure.py
python storyworlds/worlds/gpt-5.4/paddy_know_humor_quest_happy_ending_adventure.py --obstacle shallow_muck --method boots
python storyworlds/worlds/gpt-5.4/paddy_know_humor_quest_happy_ending_adventure.py --obstacle deep_water --method stepping_stones
python storyworlds/worlds/gpt-5.4/paddy_know_humor_quest_happy_ending_adventure.py --all
python storyworlds/worlds/gpt-5.4/paddy_know_humor_quest_happy_ending_adventure.py --qa --json
python storyworlds/worlds/gpt-5.4/paddy_know_humor_quest_happy_ending_adventure.py --verify
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle", "farmer"}
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
            "farmer": "farmer",
        }.get(self.type, self.type)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    drift: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    danger: str
    depth: int
    wobble: int
    mud: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    handles_depth: int
    handles_wobble: int
    keeps_dry: bool
    comic: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    kind: str
    label: str
    phrase: str
    tip: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    prize = world.get("prize")
    if hero.meters["crossing"] < THRESHOLD:
        return out
    sig = ("progress", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["progress"] += 1
    prize.meters["reached"] += 1
    hero.memes["hope"] += 1
    return out


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    method = world.get("method")
    if hero.meters["crossing"] < THRESHOLD:
        return out
    sig = ("splash", obstacle.id, method.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if obstacle.meters["mud_risk"] >= THRESHOLD and not method.attrs.get("keeps_dry", False):
        hero.meters["muddy"] += 1
        hero.memes["embarrassment"] += 1
        hero.memes["laughter"] += 1
        out.append("__splash__")
    return out


def _r_recovery_joy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    prize = world.get("prize")
    if prize.meters["reached"] < THRESHOLD:
        return out
    sig = ("joy", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="progress", tag="physical", apply=_r_progress),
    Rule(name="splash", tag="physical", apply=_r_splash),
    Rule(name="recovery_joy", tag="emotional", apply=_r_recovery_joy),
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


PRIZES = {
    "kite": Prize(
        id="kite",
        label="kite",
        phrase="a bright red kite with a tail full of ribbons",
        drift="skipped over the water like a naughty fish",
        sound="its paper tail whispered in the breeze",
        tags={"kite", "wind"},
    ),
    "drum": Prize(
        id="drum",
        label="little drum",
        phrase="a little drum with a painted tiger on the side",
        drift="bobbed away on a clump of reeds",
        sound="it gave one soft bonk each time the reeds bumped it",
        tags={"drum", "music"},
    ),
    "map": Prize(
        id="map",
        label="treasure map",
        phrase="a treasure map drawn in blue crayon",
        drift="sailed off on the wind and landed by the far bank",
        sound="its corners fluttered like tiny flags",
        tags={"map", "quest"},
    ),
}

OBSTACLES = {
    "shallow_muck": Obstacle(
        id="shallow_muck",
        label="shallow muck",
        phrase="a wide strip of warm, squishy mud",
        danger="your feet would sink and slurp",
        depth=1,
        wobble=0,
        mud=1,
        tags={"mud", "paddy"},
    ),
    "reed_ridge": Obstacle(
        id="reed_ridge",
        label="reed ridge",
        phrase="a narrow ridge between the flooded rows",
        danger="it wiggled under every careful step",
        depth=1,
        wobble=1,
        mud=0,
        tags={"reeds", "paddy"},
    ),
    "deep_water": Obstacle(
        id="deep_water",
        label="deep water channel",
        phrase="a deep water channel where the green rice bowed at the edges",
        danger="the water was too deep for a child to splash through safely",
        depth=2,
        wobble=1,
        mud=0,
        tags={"water", "paddy"},
    ),
}

METHODS = {
    "boots": Method(
        id="boots",
        label="rain boots",
        phrase="a pair of tall yellow rain boots",
        handles_depth=1,
        handles_wobble=0,
        keeps_dry=True,
        comic="The boots made funny bloop-bloop sounds with every step.",
        tags={"boots"},
    ),
    "stepping_stones": Method(
        id="stepping_stones",
        label="stepping stones",
        phrase="three flat stepping stones tucked beside the paddy path",
        handles_depth=1,
        handles_wobble=1,
        keeps_dry=True,
        comic="Each step made the hero windmill both arms like a surprised scarecrow.",
        tags={"stones"},
    ),
    "plank_bridge": Method(
        id="plank_bridge",
        label="plank bridge",
        phrase="a little plank bridge laid across the water",
        handles_depth=2,
        handles_wobble=1,
        keeps_dry=True,
        comic="The plank gave one squeaky eeek, as if it wanted to be part of the adventure too.",
        tags={"bridge"},
    ),
    "basket_boat": Method(
        id="basket_boat",
        label="basket boat",
        phrase="a round basket boat tied to a bamboo pole",
        handles_depth=2,
        handles_wobble=0,
        keeps_dry=False,
        comic="The basket boat spun in one slow silly circle before it agreed to go straight.",
        tags={"boat"},
    ),
}

GUIDES = {
    "farmer": Guide(
        id="farmer",
        kind="farmer",
        label="Farmer Binh",
        phrase="Farmer Binh, who was tying up bean vines nearby",
        tip="If you do not know the safe way, ask before you leap.",
        tags={"farmer", "ask"},
    ),
    "sister": Guide(
        id="sister",
        kind="girl",
        label="Mai",
        phrase="Mai, the hero's older sister, with a straw hat tipped over one eye",
        tip="You do not have to know everything first; you can ask and still be brave.",
        tags={"sibling", "ask"},
    ),
    "grandpa": Guide(
        id="grandpa",
        kind="man",
        label="Grandpa Tuan",
        phrase="Grandpa Tuan, who always noticed trouble before it became a splash",
        tip="The boldest adventurer is the one who knows when to ask.",
        tags={"grandpa", "ask"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Tess", "Ava", "Mina"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Finn", "Milo", "Theo"]
TRAITS = ["eager", "curious", "cheerful", "brave", "bouncy"]


def method_fits(obstacle: Obstacle, method: Method) -> bool:
    return method.handles_depth >= obstacle.depth and method.handles_wobble >= obstacle.wobble


def outcome_kind(obstacle: Obstacle, method: Method) -> str:
    if not method_fits(obstacle, method):
        return "invalid"
    if obstacle.mud and not method.keeps_dry:
        return "splashy_success"
    return "neat_success"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for prize_id in PRIZES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for method_id, method in METHODS.items():
                if method_fits(obstacle, method):
                    combos.append((prize_id, obstacle_id, method_id))
    return combos


def explain_rejection(obstacle: Obstacle, method: Method) -> str:
    parts: list[str] = []
    if method.handles_depth < obstacle.depth:
        parts.append("it does not handle water that deep")
    if method.handles_wobble < obstacle.wobble:
        parts.append("it is too unsteady for that narrow crossing")
    if not parts:
        parts.append("it does not fit this obstacle")
    return (
        f"(No story: {method.label} is not a reasonable way across {obstacle.label} because "
        + " and ".join(parts)
        + ".)"
    )


@dataclass
class StoryParams:
    prize: str
    obstacle: str
    method: str
    guide: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    seed: Optional[int] = None


def predict_crossing(world: World, obstacle_id: str, method_id: str) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    method = sim.get("method")
    obstacle.attrs["config_id"] = obstacle_id
    method.attrs["config_id"] = method_id
    obstacle.meters["mud_risk"] = float(OBSTACLES[obstacle_id].mud)
    method.attrs["keeps_dry"] = METHODS[method_id].keeps_dry
    sim.get("hero").meters["crossing"] += 1
    propagate(sim, narrate=False)
    return {
        "reached": sim.get("prize").meters["reached"] >= THRESHOLD,
        "muddy": sim.get("hero").meters["muddy"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, prize: Prize) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who liked to pretend every ordinary morning was the start of an expedition."
    )
    world.say(
        f"That day, {hero.pronoun('possessive')} favorite treasure was {prize.phrase}."
    )


def loss(world: World, hero: Entity, prize: Prize) -> None:
    hero.memes["alarm"] += 1
    world.say(
        f"A teasing gust snatched it away. It {prize.drift}, out across the rice paddy, while {prize.sound}."
    )
    world.say(
        f'"My quest has begun!" {hero.id} gasped, and then, in a smaller voice, "{hero.pronoun().capitalize()}... I do not know the best way to get it back."'
    )


def survey(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["uncertainty"] += 1
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["mud_risk"] = float(obstacle.mud)
    world.say(
        f"Between {hero.id} and the far bank lay {obstacle.phrase}. {obstacle.danger}."
    )


def consult(world: World, hero: Entity, guide_ent: Entity, guide: Guide, obstacle: Obstacle, method: Method) -> None:
    pred = predict_crossing(world, obstacle.id, method.id)
    hero.memes["trust"] += 1
    hero.memes["humility"] += 1
    world.facts["predicted_muddy"] = pred["muddy"]
    world.say(
        f"Just then {guide.phrase} looked up and smiled. {guide_ent.pronoun().capitalize()} said, "
        f'"{guide.tip}"'
    )
    world.say(
        f'{hero.id} pointed across the paddy. "Then what should I use?"'
    )
    answer = f'"Use {method.phrase}," {guide_ent.pronoun()} said.'
    if pred["muddy"]:
        answer += f' "You may still get one muddy surprise, but you will reach it."'
    else:
        answer += ' "That will carry you across clean and safe."'
    world.say(answer)


def choose(world: World, hero: Entity, method: Method) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"So the quest truly began. {hero.id} took {method.phrase}, drew a deep breath, and marched toward the shining rows."
    )


def cross(world: World, hero: Entity, obstacle: Obstacle, method: Method) -> None:
    hero.meters["crossing"] += 1
    method_ent = world.get("method")
    method_ent.attrs["keeps_dry"] = method.keeps_dry
    propagate(world, narrate=False)
    world.say(method.comic)
    if obstacle.wobble:
        hero.memes["focus"] += 1
        world.say(
            f"{hero.id} bent {hero.pronoun('possessive')} knees and moved slowly while the world seemed to wobble under {hero.pronoun('object')}."
        )
    if hero.meters["muddy"] >= THRESHOLD:
        world.say(
            f"At the very middle, one foot slipped with a glorious sploof, and muddy water dotted {hero.pronoun('possessive')} legs. Even {hero.id} had to laugh."
        )
    else:
        world.say(
            f"Step by step, {hero.id} crossed without a splash."
        )


def recover(world: World, hero: Entity, prize: Prize) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["held"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"At last {hero.id} reached the far bank and scooped up the {prize.label}. It felt even better in {hero.pronoun('possessive')} hands because the quest had almost taken it away."
    )


def return_home(world: World, hero: Entity, guide_ent: Entity, method: Method) -> None:
    hero.memes["gratitude"] += 1
    world.say(
        f"On the way back, {hero.id} called, \"Now I know!\" and {guide_ent.label} laughed from the path."
    )
    if hero.meters["muddy"] >= THRESHOLD:
        world.say(
            f"The muddy spots looked like adventure medals, and nobody minded them at all."
        )
    else:
        world.say(
            f"{hero.id}'s feet stayed neat, but {hero.pronoun('possessive')} grin was gloriously untidy."
        )
    world.say(
        f"By the time the sun tipped low, the quest was over, the treasure was safe, and the whole paddy seemed to wink back at the brave little traveler."
    )


def tell(
    prize: Prize,
    obstacle: Obstacle,
    method: Method,
    guide: Guide,
    hero_name: str,
    hero_gender: str,
    hero_trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, traits=[hero_trait], role="hero"))
    hero.attrs["name"] = hero_name
    guide_ent = world.add(Entity(id="guide", kind="character", type=guide.kind, label=guide.label, role="guide"))
    obstacle_ent = world.add(Entity(id="obstacle", kind="thing", type="obstacle", label=obstacle.label))
    method_ent = world.add(Entity(id="method", kind="thing", type="method", label=method.label))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="prize", label=prize.label))
    obstacle_ent.meters["mud_risk"] = float(obstacle.mud)
    method_ent.attrs["keeps_dry"] = method.keeps_dry

    introduce(world, hero, prize)
    survey(world, hero, obstacle)

    world.para()
    loss(world, hero, prize)
    consult(world, hero, guide_ent, guide, obstacle, method)

    world.para()
    choose(world, hero, method)
    cross(world, hero, obstacle, method)
    recover(world, hero, prize)

    world.para()
    return_home(world, hero, guide_ent, method)

    world.facts.update(
        hero=hero,
        guide=guide_ent,
        guide_cfg=guide,
        prize_cfg=prize,
        obstacle_cfg=obstacle,
        method_cfg=method,
        prize=prize_ent,
        obstacle=obstacle_ent,
        method=method_ent,
        outcome=outcome_kind(obstacle, method),
        reached=prize_ent.meters["reached"] >= THRESHOLD,
        muddy=hero.meters["muddy"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "paddy": [
        (
            "What is a rice paddy?",
            "A rice paddy is a field where rice grows in shallow water. People make flat rows and little banks so the water stays where the rice needs it.",
        )
    ],
    "mud": [
        (
            "Why is mud slippery?",
            "Mud is wet soil, so your feet can slide on it more easily than on dry ground. That is why people step carefully in muddy places.",
        )
    ],
    "boots": [
        (
            "Why do rain boots help in mud?",
            "Rain boots keep water and mud off your feet and give you a stronger step. They do not fix every problem, but they help in shallow wet ground.",
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge lets you go over water or soft ground without stepping straight into it. A small bridge can be the safest way across a tricky place.",
        )
    ],
    "boat": [
        (
            "What is a boat for?",
            "A boat floats on water so people or things can move across without walking through the water. Some boats still splash a little if they wobble.",
        )
    ],
    "ask": [
        (
            "Why is it smart to ask when you do not know something?",
            "Asking helps you learn the safe and sensible thing to do. It is not less brave; it is how careful adventurers avoid foolish mistakes.",
        )
    ],
    "kite": [
        (
            "Why can wind carry a kite away?",
            "A kite is light and wide, so a gust of wind can tug it hard and send it drifting. That is why people hold the string carefully.",
        )
    ],
    "map": [
        (
            "What is a treasure map?",
            "A treasure map is a picture that shows where to go to find something hidden or important. In stories, maps often start adventures.",
        )
    ],
    "drum": [
        (
            "How does a little drum make sound?",
            "A drum makes sound when its top is tapped and starts to vibrate. The vibration moves the air, and your ears hear the beat.",
        )
    ],
}
KNOWLEDGE_ORDER = ["paddy", "mud", "boots", "bridge", "boat", "ask", "kite", "map", "drum"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize_cfg"]
    obstacle = f["obstacle_cfg"]
    method = f["method_cfg"]
    return [
        f'Write a child-friendly adventure story set by a rice paddy that includes the word "paddy" and the word "know".',
        f"Tell a humorous quest where a {hero.type} must get back a {prize.label} from across {obstacle.phrase} and succeeds by asking how to cross safely.",
        f"Write a happy-ending adventure in which the hero learns, \"I do not have to know everything before I ask,\" and uses {method.label} to finish the quest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    prize = f["prize_cfg"]
    obstacle = f["obstacle_cfg"]
    method = f["method_cfg"]
    hero_name = hero.attrs.get("name", hero.label or hero.id)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a little adventurer, and {guide.label}, who helps with the quest. The lost treasure is {prize.phrase}.",
        ),
        (
            "What started the quest?",
            f"A gust carried the {prize.label} away across the rice paddy. That sudden loss turned an ordinary morning into an adventure.",
        ),
        (
            f"Why did {hero_name} stop and ask for help instead of rushing in?",
            f"{hero_name} could see {obstacle.phrase} in the way and did not know the safest path across. Asking first mattered because the crossing needed the right method, not just brave feet.",
        ),
        (
            f"How did {guide.label} help?",
            f"{guide.label} told {hero_name} to use {method.phrase}. The advice fit the obstacle, so the quest could go forward safely.",
        ),
    ]
    if f["muddy"]:
        qa.append(
            (
                f"Did the crossing stay perfectly neat?",
                f"No. {hero_name} had one muddy slip in the middle and laughed about it. The quest still ended well because the hero reached the prize safely anyway.",
            )
        )
    else:
        qa.append(
            (
                f"What happened during the crossing?",
                f"{hero_name} crossed step by careful step without a splash. The funny part came from the wobble and the silly sounds, not from a real mishap.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily: {hero_name} got the {prize.label} back and returned across the paddy feeling wiser. The ending shows a real change because the hero now knows to ask when the safe way is unclear.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"paddy", "ask"}
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["method_cfg"].tags)
    tags |= set(f["prize_cfg"].tags)
    out: list[tuple[str, str]] = []
    tag_map = {
        "mud": "mud",
        "paddy": "paddy",
        "boots": "boots",
        "bridge": "bridge",
        "boat": "boat",
        "ask": "ask",
        "kite": "kite",
        "map": "map",
        "drum": "drum",
        "stones": "bridge",
        "water": "boat",
    }
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    for raw in sorted(tags):
        mapped = tag_map.get(raw)
        if mapped and mapped not in KNOWLEDGE_ORDER and mapped in KNOWLEDGE:
            out.extend(KNOWLEDGE[mapped])
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        prize="kite",
        obstacle="shallow_muck",
        method="boots",
        guide="farmer",
        hero_name="Lina",
        hero_gender="girl",
        hero_trait="eager",
    ),
    StoryParams(
        prize="map",
        obstacle="reed_ridge",
        method="stepping_stones",
        guide="sister",
        hero_name="Leo",
        hero_gender="boy",
        hero_trait="curious",
    ),
    StoryParams(
        prize="drum",
        obstacle="deep_water",
        method="plank_bridge",
        guide="grandpa",
        hero_name="Mina",
        hero_gender="girl",
        hero_trait="brave",
    ),
    StoryParams(
        prize="kite",
        obstacle="deep_water",
        method="basket_boat",
        guide="farmer",
        hero_name="Owen",
        hero_gender="boy",
        hero_trait="cheerful",
    ),
]


ASP_RULES = r"""
fits(O, M) :- obstacle(O), method(M),
              obstacle_depth(O, D), method_depth(M, MD), MD >= D,
              obstacle_wobble(O, W), method_wobble(M, MW), MW >= W.

valid(P, O, M) :- prize(P), fits(O, M).

muddy_success(O, M) :- fits(O, M), obstacle_mud(O), not keeps_dry(M).
neat_success(O, M)  :- fits(O, M), not muddy_success(O, M).

outcome(splashy_success) :- chosen_obstacle(O), chosen_method(M), muddy_success(O, M).
outcome(neat_success)    :- chosen_obstacle(O), chosen_method(M), neat_success(O, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_depth", obstacle_id, obstacle.depth))
        lines.append(asp.fact("obstacle_wobble", obstacle_id, obstacle.wobble))
        if obstacle.mud:
            lines.append(asp.fact("obstacle_mud", obstacle_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("method_depth", method_id, method.handles_depth))
        lines.append(asp.fact("method_wobble", method_id, method.handles_wobble))
        if method.keeps_dry:
            lines.append(asp.fact("keeps_dry", method_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a humorous quest across a rice paddy. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.method:
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if not method_fits(obstacle, method):
            raise StoryError(explain_rejection(obstacle, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.prize is None or combo[0] == args.prize)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    prize_id, obstacle_id, method_id = rng.choice(sorted(combos))
    guide_id = args.guide or rng.choice(sorted(GUIDES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        prize=prize_id,
        obstacle=obstacle_id,
        method=method_id,
        guide=guide_id,
        hero_name=name,
        hero_gender=gender,
        hero_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        prize = PRIZES[params.prize]
        obstacle = OBSTACLES[params.obstacle]
        method = METHODS[params.method]
        guide = GUIDES[params.guide]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]!r}.)") from None
    if not method_fits(obstacle, method):
        raise StoryError(explain_rejection(obstacle, method))

    world = tell(
        prize=prize,
        obstacle=obstacle,
        method=method,
        guide=guide,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.hero_trait,
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
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    mismatches = []
    for params in cases:
        py = outcome_kind(OBSTACLES[params.obstacle], METHODS[params.method])
        asp = asp_outcome(params)
        if py != asp:
            mismatches.append((params, py, asp))
    if not mismatches:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py, asp in mismatches[:5]:
            print(" ", params, py, asp)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
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
        print(f"{len(combos)} compatible (prize, obstacle, method) combos:\n")
        for prize, obstacle, method in combos:
            print(f"  {prize:6} {obstacle:13} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name}: {p.prize} across {p.obstacle} by {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
