#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/institute_boondocks_sire_bravery_space_adventure.py
===============================================================================

A standalone storyworld about a child cadet at a tiny space institute in the
boondocks, facing one scary obstacle on a training mission and learning that
bravery can mean steady steps or asking a sire for help.

This world rebuilds a simple TinyStories-style shape as a small simulation:

    setup at a remote institute
    -> a clear mission
    -> one obstacle creates fear
    -> the sire offers the right tool
    -> the child either finishes alone or bravely asks for help
    -> the ending image proves the mission is complete

The words "institute", "boondocks", and "sire" are included naturally in the
rendered stories.

Run it
------
    python storyworlds/worlds/gpt-5.4/institute_boondocks_sire_bravery_space_adventure.py
    python storyworlds/worlds/gpt-5.4/institute_boondocks_sire_bravery_space_adventure.py --setting mars --obstacle shadow_tunnel --aid star_lantern
    python storyworlds/worlds/gpt-5.4/institute_boondocks_sire_bravery_space_adventure.py --obstacle shadow_tunnel --aid echo_flag
    python storyworlds/worlds/gpt-5.4/institute_boondocks_sire_bravery_space_adventure.py --all --qa
    python storyworlds/worlds/gpt-5.4/institute_boondocks_sire_bravery_space_adventure.py --verify
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
        male = {"boy", "father", "man", "sire"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"father": "father", "sire": "sire"}.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    institute: str
    world_name: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    article: str
    risk: str
    severity: int
    appear_text: str
    danger_text: str
    pass_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    power: int = 0
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    aid: str
    hero_name: str
    hero_gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_obstacle_fear(world: World) -> list[str]:
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    aid = world.entities.get("aid")
    if hero is None or obstacle is None:
        return []
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    if aid is not None and aid.meters["active"] >= THRESHOLD and obstacle.attrs.get("risk") in aid.attrs.get("guards", set()):
        return []
    sig = ("fear", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return ["__fear__"]


def _r_aid_helps(world: World) -> list[str]:
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    aid = world.entities.get("aid")
    if hero is None or obstacle is None or aid is None:
        return []
    if aid.meters["active"] < THRESHOLD:
        return []
    if obstacle.attrs.get("risk") not in aid.attrs.get("guards", set()):
        return []
    sig = ("aid_helps", aid.id, obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["safe"] += 1
    if hero.memes["fear"] > 0:
        hero.memes["fear"] -= 1
    hero.memes["bravery"] += 1
    return ["__helped__"]


def _r_support_steady(world: World) -> list[str]:
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    if hero is None or obstacle is None:
        return []
    if hero.memes["supported"] < THRESHOLD or obstacle.meters["safe"] < THRESHOLD:
        return []
    sig = ("support", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    return ["__support__"]


def _r_finish(world: World) -> list[str]:
    hero = world.entities.get("hero")
    beacon = world.entities.get("beacon")
    obstacle = world.entities.get("obstacle")
    if hero is None or beacon is None or obstacle is None:
        return []
    if beacon.meters["carried"] < THRESHOLD:
        return []
    if obstacle.meters["safe"] < THRESHOLD:
        return []
    sig = ("finish", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    beacon.meters["planted"] += 1
    hero.memes["joy"] += 1
    return ["__finish__"]


CAUSAL_RULES = [
    Rule(name="obstacle_fear", tag="emotional", apply=_r_obstacle_fear),
    Rule(name="aid_helps", tag="physical", apply=_r_aid_helps),
    Rule(name="support_steady", tag="emotional", apply=_r_support_steady),
    Rule(name="finish", tag="physical", apply=_r_finish),
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
    "mars": Setting(
        id="mars",
        institute="Lantern Ring Institute",
        world_name="the red boondocks of Mars",
        scene="rust-red flats with small blue stars waking above them",
        affords={"shadow_tunnel", "gust_bridge"},
        tags={"institute", "mars", "boondocks"},
    ),
    "moon": Setting(
        id="moon",
        institute="Pebble Sky Institute",
        world_name="the silver boondocks of the Moon",
        scene="quiet craters and a black sky full of bright pinprick stars",
        affords={"shadow_tunnel", "crumbly_steps"},
        tags={"institute", "moon", "boondocks"},
    ),
    "comet": Setting(
        id="comet",
        institute="Starstep Institute",
        world_name="the icy boondocks of Comet Nilo",
        scene="glittering frost and a tail of light sweeping behind the camp",
        affords={"gust_bridge", "crumbly_steps"},
        tags={"institute", "comet", "boondocks"},
    ),
}

OBSTACLES = {
    "shadow_tunnel": Obstacle(
        id="shadow_tunnel",
        label="shadow tunnel",
        article="a shadow tunnel",
        risk="dark",
        severity=3,
        appear_text="Ahead of the path waited a long shadow tunnel cut through a mound of black rock.",
        danger_text="Inside, the floor lights were dim, and every little pebble looked like a deep hole.",
        pass_text="The dark passage stopped feeling like a swallowing mouth and started feeling like a hallway with stars in it.",
        tags={"dark", "tunnel"},
    ),
    "gust_bridge": Obstacle(
        id="gust_bridge",
        label="gust bridge",
        article="a gust bridge",
        risk="wind",
        severity=2,
        appear_text="The trail climbed to a narrow gust bridge stretched over a crack in the ground.",
        danger_text="Cold wind pushed at sleeves and knees, trying to make every step wobble.",
        pass_text="The bridge still hummed in the wind, but now each step had a safe place to land.",
        tags={"wind", "bridge"},
    ),
    "crumbly_steps": Obstacle(
        id="crumbly_steps",
        label="crumbly steps",
        article="crumbly steps",
        risk="footing",
        severity=3,
        appear_text="At the hill, a line of crumbly steps zigzagged up toward the beacon post.",
        danger_text="Each dusty edge looked ready to slide if someone rushed.",
        pass_text="The steps felt less like a tumble waiting to happen and more like a puzzle of careful feet.",
        tags={"footing", "hill"},
    ),
}

AIDS = {
    "star_lantern": Aid(
        id="star_lantern",
        label="star lantern",
        phrase="a star lantern",
        guards={"dark"},
        power=2,
        use_text="clicked on the star lantern, and a soft ring of gold light rolled over the ground",
        tags={"lantern", "light"},
    ),
    "guide_line": Aid(
        id="guide_line",
        label="guide line",
        phrase="a guide line",
        guards={"wind", "footing"},
        power=1,
        use_text="clipped the guide line to the rail so each step had something steady to answer back to",
        tags={"rope", "safety"},
    ),
    "grip_boots": Aid(
        id="grip_boots",
        label="grip boots",
        phrase="grip boots",
        guards={"footing"},
        power=2,
        use_text="pulled on the grip boots, and their soles bit the dusty ground instead of slipping over it",
        tags={"boots", "safety"},
    ),
    "echo_flag": Aid(
        id="echo_flag",
        label="echo flag",
        phrase="an echo flag",
        guards=set(),
        power=0,
        use_text="waved the echo flag, which looked brave but did not solve the problem in front of them",
        tags={"flag"},
    ),
}

TRAIT_BRAVERY = {
    "bold": 2,
    "steady": 2,
    "careful": 1,
    "curious": 1,
    "gentle": 1,
    "patient": 1,
}
TRAITS = sorted(TRAIT_BRAVERY)

GIRL_NAMES = ["Nia", "Luma", "Tess", "Mira", "Ava", "Zoe", "Pia", "Nova"]
BOY_NAMES = ["Leo", "Orin", "Tao", "Milo", "Finn", "Eli", "Jax", "Noor"]


def aid_works(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.risk in aid.guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid in sorted(setting.affords):
            obstacle = OBSTACLES[oid]
            for aid_id, aid in AIDS.items():
                if aid_works(obstacle, aid):
                    combos.append((sid, oid, aid_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    base = TRAIT_BRAVERY[params.trait]
    if not aid_works(obstacle, aid):
        raise StoryError(explain_rejection(obstacle, aid))
    return "solo" if base + aid.power >= obstacle.severity + 1 else "with_help"


def explain_rejection(obstacle: Obstacle, aid: Aid) -> str:
    return (
        f"(No story: {aid.phrase} does not really solve {obstacle.article}. "
        f"The obstacle needs help with {obstacle.risk}, so pick an aid that handles that problem.)"
    )


def predict_without_aid(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    return {
        "fear": hero.memes["fear"],
        "risk": sim.get("obstacle").attrs.get("risk", ""),
    }


def introduce(world: World, hero: Entity, sire: Entity, beacon: Entity) -> None:
    world.say(
        f"Far out in {world.setting.world_name} stood the little {world.setting.institute}, "
        f"a tiny institute with one round dome, one practice field, and {world.setting.scene}."
    )
    world.say(
        f"{hero.id} was a little {hero.type} cadet who dreamed of earning the First Brave Walk badge."
    )
    world.say(
        f"That evening, {sire.label_word.capitalize()} handed {hero.pronoun('object')} {beacon.phrase} "
        f"and pointed toward the far beacon post."
    )
    world.say(
        f'"Ready, Cadet?" {sire.pronoun()} asked. {hero.id} grinned, gave a playful bow, '
        f'and whispered, "Yes, sire."'
    )


def mission(world: World, hero: Entity, beacon: Entity) -> None:
    beacon.meters["carried"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"The mission was simple: carry the bright beacon to the hill post and make it shine over the camp."
    )


def obstacle_appears(world: World, hero: Entity, obstacle: Entity, obstacle_cfg: Obstacle) -> None:
    obstacle.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(obstacle_cfg.appear_text)
    world.say(obstacle_cfg.danger_text)
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"{hero.id} stopped so fast that the beacon's little handle knocked against {hero.pronoun('possessive')} glove."
        )


def warn(world: World, hero: Entity, sire: Entity, obstacle_cfg: Obstacle, aid_cfg: Aid) -> None:
    pred = predict_without_aid(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{sire.label_word.capitalize()} knelt beside {hero.id}. "Bravery is not blasting ahead with a shaky plan," '
        f'{sire.pronoun()} said. "That path is hard because of the {obstacle_cfg.risk}. '
        f'We brought {aid_cfg.phrase} for a reason."'
    )


def choose_tool(world: World, hero: Entity, aid: Entity, aid_cfg: Aid) -> None:
    aid.meters["active"] += 1
    propagate(world, narrate=False)
    hero.memes["choice"] += 1
    world.say(
        f"{hero.id} took a slow breath, {aid_cfg.use_text}, and held the beacon a little tighter."
    )


def finish_solo(world: World, hero: Entity, obstacle_cfg: Obstacle, sire: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{obstacle_cfg.pass_text} {hero.id} walked on alone, one brave step and then another, while "
        f"{sire.label_word} watched with a proud smile from the safe marker stones."
    )
    world.say(
        f"At the top, {hero.pronoun()} set the beacon into the post. A clear blue light blinked on and poured over the sleeping camp."
    )


def ask_for_help(world: World, hero: Entity, sire: Entity) -> None:
    hero.memes["supported"] += 1
    hero.memes["honesty"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"My knees still feel wiggly," {hero.id} admitted. That was brave too. '
        f'"Will you come beside me, sire?"'
    )
    world.say(
        f'"Gladly," {sire.pronoun()} said, laying a warm hand on {hero.pronoun("possessive")} shoulder.'
    )


def finish_together(world: World, hero: Entity, obstacle_cfg: Obstacle, sire: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{obstacle_cfg.pass_text} Together they crossed the hard part, matching their steps until the scary place shrank behind them."
    )
    world.say(
        f"At the top, {hero.id} planted the beacon by {hero.pronoun('self') if False else hero.pronoun('possessive')} own hands while "
        f"{sire.label_word} stood close by."
    )
    world.say(
        "A clear blue light blinked on and spread over the little roofs of the institute, all the way out into the boondocks."
    )


def closing(world: World, hero: Entity, sire: Entity, outcome: str) -> None:
    if outcome == "solo":
        world.say(
            f'"You were brave," {sire.label_word} said. "{hero.id} nodded. "I was scared first," '
            f'{hero.pronoun()} answered, "but I kept going the right way."'
        )
    else:
        world.say(
            f'"You were brave," {sire.label_word} said. "{hero.id} looked up at him and smiled. '
            f'"I thought bravery meant doing it all alone," {hero.pronoun()} said. '
            f'"Now I know it can mean asking for help and still finishing."'
        )
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Back at the dome, the new badge shone on {hero.pronoun('possessive')} jacket like a tiny second moon."
    )


def tell(
    setting: Setting,
    obstacle_cfg: Obstacle,
    aid_cfg: Aid,
    hero_name: str,
    hero_gender: str,
    trait: str,
) -> World:
    world = World(setting=setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            tags={"cadet"},
        )
    )
    sire = world.add(
        Entity(
            id="sire",
            kind="character",
            type="sire",
            label="father",
            role="sire",
            tags={"family", "sire"},
        )
    )
    beacon = world.add(
        Entity(
            id="beacon",
            type="beacon",
            label="beacon",
            phrase="a bright practice beacon",
            role="goal",
            tags={"beacon"},
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle_cfg.label,
            role="obstacle",
            attrs={"risk": obstacle_cfg.risk, "severity": obstacle_cfg.severity},
            tags=set(obstacle_cfg.tags),
        )
    )
    aid = world.add(
        Entity(
            id="aid",
            type="tool",
            label=aid_cfg.label,
            phrase=aid_cfg.phrase,
            role="aid",
            attrs={"guards": set(aid_cfg.guards), "power": aid_cfg.power},
            tags=set(aid_cfg.tags),
        )
    )

    hero.memes["bravery"] = float(TRAIT_BRAVERY[trait])
    world.facts["hero_display"] = hero_name
    world.facts["sire_word"] = "sire"

    introduce(world, hero, sire, beacon)
    mission(world, hero, beacon)

    world.para()
    obstacle_appears(world, hero, obstacle, obstacle_cfg)
    warn(world, hero, sire, obstacle_cfg, aid_cfg)

    world.para()
    choose_tool(world, hero, aid, aid_cfg)
    outcome = "solo" if hero.memes["bravery"] + aid_cfg.power >= obstacle_cfg.severity + 1 else "with_help"
    if outcome == "solo":
        finish_solo(world, hero, obstacle_cfg, sire)
    else:
        ask_for_help(world, hero, sire)
        finish_together(world, hero, obstacle_cfg, sire)

    world.para()
    closing(world, hero, sire, outcome)

    world.facts.update(
        hero=hero,
        sire=sire,
        beacon=beacon,
        obstacle=obstacle,
        obstacle_cfg=obstacle_cfg,
        aid=aid,
        aid_cfg=aid_cfg,
        setting=setting,
        outcome=outcome,
        mission_done=beacon.meters["planted"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "institute": [
        (
            "What is an institute?",
            "An institute is a place where people study, learn, or practice something together. In a story, it can be as small as one little school building."
        )
    ],
    "boondocks": [
        (
            "What does boondocks mean?",
            "Boondocks means a place far away from busy towns and crowds. It feels remote and quiet."
        )
    ],
    "sire": [
        (
            "What does sire mean?",
            "Sire is an old word for a father or a king. In this story, the child uses it as a warm, playful name for a father during a space mission game."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so you can see in the dark. A safe lantern helps you notice where to step."
        )
    ],
    "rope": [
        (
            "Why does a guide line help?",
            "A guide line gives your hands or body something steady to follow. That helps on windy or tricky paths."
        )
    ],
    "boots": [
        (
            "Why do grip boots help on loose ground?",
            "Grip boots have soles that hold the ground better. They can stop little slips on dusty or crumbly places."
        )
    ],
    "dark": [
        (
            "Why can darkness feel scary?",
            "Darkness can hide where things are, so your brain feels less sure. That uncertainty can make a place seem bigger or stranger than it really is."
        )
    ],
    "wind": [
        (
            "Why is strong wind hard to walk in?",
            "Strong wind pushes on your body and can wobble your balance. That is why people take smaller, steadier steps in it."
        )
    ],
    "footing": [
        (
            "What does careful footing mean?",
            "Careful footing means placing your feet where the ground is safe and steady. It matters on steps, rocks, and loose dirt."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel scared. Sometimes bravery means asking for help instead of pretending you are not afraid."
        )
    ],
}
KNOWLEDGE_ORDER = ["institute", "boondocks", "sire", "dark", "wind", "footing", "lantern", "rope", "boots", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    outcome = f["outcome"]
    if outcome == "solo":
        return [
            f'Write a short space adventure for a 3-to-5-year-old set at an institute in the boondocks, and include the word "sire".',
            f"Tell a gentle story where a little {hero.type} cadet faces {obstacle.article} and uses {aid.phrase} to finish a brave mission.",
            f"Write a story about bravery where a child carries a beacon across a scary path and ends with a light shining over a remote camp.",
        ]
    return [
        f'Write a short space adventure for a 3-to-5-year-old set at an institute in the boondocks, and include the word "sire".',
        f"Tell a gentle story where a little {hero.type} cadet feels scared by {obstacle.article}, uses {aid.phrase}, and bravely asks a father for help.",
        f"Write a story about bravery where the child learns that finishing together can still count as being brave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sire = f["sire"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    hero_name = world.facts["hero_display"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a little cadet at {setting.institute}, and {hero.pronoun('possessive')} father, whom {hero.pronoun()} playfully calls sire."
        ),
        (
            "Where does the story happen?",
            f"It happens at {setting.institute} in {setting.world_name}. That remote place is why the story calls it the boondocks."
        ),
        (
            "What was the mission?",
            "The mission was to carry a bright practice beacon to the hill post and switch on its light. The glowing beacon would show that the child finished the brave walk."
        ),
        (
            f"What scary thing blocked the path?",
            f"{obstacle.article.capitalize()} blocked the path. It was scary because {obstacle.danger_text.lower()}"
        ),
        (
            f"How did {hero_name} get ready to face the obstacle?",
            f"{hero_name} used {aid.phrase}. That tool matched the problem because it helped with the {obstacle.risk} on the path."
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How was {hero_name} brave?",
                f"{hero_name} felt scared, but still used the right tool and kept taking careful steps. The child did not charge ahead wildly; the bravery came from doing the mission the safe way."
            )
        )
    else:
        qa.append(
            (
                f"How was {hero_name} brave even before the mission ended?",
                f"{hero_name} was brave by telling the truth about feeling shaky and asking sire to come along. That mattered because asking for help was the step that let the mission continue safely."
            )
        )
    qa.append(
        (
            "How did the story end?",
            "The beacon shone over the little institute and out into the boondocks. That glowing light proved the mission was finished and that the child had changed from fearful to truly brave."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"institute", "boondocks", "sire", "bravery"}
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["aid_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="mars",
        obstacle="shadow_tunnel",
        aid="star_lantern",
        hero_name="Nia",
        hero_gender="girl",
        trait="bold",
    ),
    StoryParams(
        setting="mars",
        obstacle="gust_bridge",
        aid="guide_line",
        hero_name="Leo",
        hero_gender="boy",
        trait="careful",
    ),
    StoryParams(
        setting="moon",
        obstacle="crumbly_steps",
        aid="grip_boots",
        hero_name="Mira",
        hero_gender="girl",
        trait="steady",
    ),
    StoryParams(
        setting="comet",
        obstacle="crumbly_steps",
        aid="guide_line",
        hero_name="Orin",
        hero_gender="boy",
        trait="gentle",
    ),
]


ASP_RULES = r"""
works(O, A) :- obstacle(O), aid(A), guards(A, R), risk(O, R).
valid(S, O, A) :- setting(S), affords(S, O), works(O, A).

base_bravery(T, B) :- trait(T), bravery(T, B).
solo(T, O, A) :- chosen_trait(T), chosen_obstacle(O), chosen_aid(A),
                 bravery(T, B), power(A, P), severity(O, S), B + P >= S + 1.
outcome(solo) :- solo(T, O, A).
outcome(with_help) :- chosen_trait(T), chosen_obstacle(O), chosen_aid(A),
                      valid(S, O, A), chosen_setting(S), not solo(T, O, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for oid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, oid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("risk", oid, obstacle.risk))
        lines.append(asp.fact("severity", oid, obstacle.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
        for guard in sorted(aid.guards):
            lines.append(asp.fact("guards", aid_id, guard))
    for trait, score in TRAIT_BRAVERY.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("bravery", trait, score))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_aid", params.aid),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story or "institute" not in sample.story.lower():
        raise StoryError("Smoke test failed: story text missing or malformed.")
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
    out = buf.getvalue()
    if "### smoke" not in out or "Q:" not in out:
        raise StoryError("Smoke test failed: emit() did not produce expected text.")


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_val = asp_outcome(params)
        if py != asp_val:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} asp={asp_val}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke_test()
        print("OK: smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small space adventure about bravery at a remote institute."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.aid:
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not aid_works(obstacle, aid):
            raise StoryError(explain_rejection(obstacle, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, obstacle, aid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        obstacle=obstacle,
        aid=aid,
        hero_name=name,
        hero_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.trait not in TRAIT_BRAVERY:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.hero_gender})")
    if not aid_works(OBSTACLES[params.obstacle], AIDS[params.aid]):
        raise StoryError(explain_rejection(OBSTACLES[params.obstacle], AIDS[params.aid]))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle_cfg=OBSTACLES[params.obstacle],
        aid_cfg=AIDS[params.aid],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("  ", " "),
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
        print(f"{len(combos)} compatible (setting, obstacle, aid) combos:\n")
        for setting, obstacle, aid in combos:
            print(f"  {setting:7} {obstacle:14} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.setting}, {p.obstacle}, {p.aid}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
