#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/extinguish_beat_bravery_cautionary_foreshadowing_fairy_tale.py
==============================================================================================

A standalone fairy-tale storyworld about a brave child, a cautionary warning,
and a foreshadowed fire that must be extinguished before it beats the whole
village.

Premise
-------
A small child explores a storybook castle with a kindly elder. A spark of
bravery tempts them to try a forbidden lantern trick. The tale foreshadows the
danger, the warning is ignored or heeded, and a grown-up or helper extinguishes
the fire in time -- or not -- depending on the fire's head start.

The world is tiny and classical:
- typed entities with physical meters and emotional memes,
- state-driven narration,
- a reasonableness gate,
- a Python validity checker,
- an inline ASP twin for parity verification,
- three QA sets grounded in the simulated world.

The required story words are included via the generated prose and prompts:
"extinguish" and "beat".
The required narrative instruments are embodied as:
Bravery, Cautionary, Foreshadowing.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "wise", "serious"}
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
    flammable: bool = False
    makes_flame: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    quest: str
    dark_place: str
    word_for_dark: str
    ending_image: str


@dataclass
class Forbidden:
    id: str
    label: str
    phrase: str
    where: str
    unit: str
    strike: str
    not_toy: str
    makes_flame: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    near: str
    drape: str
    spread: int
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    glow: str
    gives_light: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    forbidden: str
    target: str
    helper1: str
    helper2: str
    response: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    elder_role: str
    trait: str
    delay: int = 0
    child_age: int = 6
    elder_age: int = 10
    relation: str = "siblings"
    trust: int = 6
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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for kid in world.characters():
            if kid.role in {"child", "cautioner"}:
                kid.memes["fear"] += 1
        out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread)]


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


def hazard_at_risk(forbidden: Forbidden, target: Target) -> bool:
    return forbidden.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def would_avert(relation: str, child_age: int, elder_age: int, trait: str) -> bool:
    caution = 5.0 if trait in CAUTIOUS_TRAITS else 3.0
    authority = caution + 1.0 + (4.0 if relation == "siblings" and elder_age > child_age else 0.0)
    return relation == "siblings" and elder_age > child_age and authority > BRAVERY_INIT


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {
        "burning": sim.get(target_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def tale_setup(world: World, child: Entity, elder: Entity, theme: Theme) -> None:
    child.memes["joy"] += 1
    elder.memes["care"] += 1
    world.say(
        f"Once upon a soft evening, {child.id} and {elder.id} wandered through {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {child.id} and {theme.title_b} {elder.id}!" {child.id} cried. '
        f'"Let us seek {theme.quest}!"'
    )


def need_light(world: World, child: Entity, theme: Theme, target: Target) -> None:
    world.say(
        f"But {theme.dark_place} -- {target.drape} -- held a hush so deep that even the crickets seemed to beat more softly."
    )
    world.say(f'{child.id} peered into the dark place. "We need a light," {child.pronoun()} said.')


def foreshadow(world: World, elder: Entity, child: Entity, forbidden: Forbidden, target: Target) -> None:
    elder.memes["caution"] += 1
    pred = predict_fire(world, "target")
    world.facts["predicted_danger"] = pred["danger"]
    extra = " The candle-shadow on the wall seemed to warn them already." if pred["danger"] else ""
    world.say(
        f'{elder.id} bit {elder.pronoun("possessive")} lip and spoke in a cautionary voice. '
        f'"Do not touch {forbidden.label}, {child.id}. {forbidden.not_toy}. '
        f'It can start a real flame near {target.the}."{extra}'
    )


def tempt(world: World, child: Entity, forbidden: Forbidden) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} lifted {child.pronoun("possessive")} chin. "I know a brave trick," {child.id} said. '
        f'"{forbidden.label.capitalize()}!"'
    )
    world.say("For one bright breath, the idea felt like destiny.")


def defy(world: World, child: Entity, forbidden: Forbidden) -> None:
    child.memes["defiance"] += 1
    them = "them" if forbidden.plural else "it"
    world.say(
        f'"Do not be so timid," {child.id} said, and ran to fetch {them} from {forbidden.where}.'
    )


def avert(world: World, child: Entity, elder: Entity, forbidden: Forbidden, theme: Theme) -> None:
    child.memes["relief"] += 1
    elder.memes["relief"] += 1
    world.say(
        f'{child.id} looked at {elder.id}, then at the waiting dark, and chose the wiser road. '
        f'They left {forbidden.label} untouched and searched for a safer wonder instead.'
    )
    world.say(
        f"By dusk they found {theme.ending_image}, and the night kept all its promises."
    )


def ignite(world: World, target_ent: Entity, forbidden: Forbidden, target: Target) -> None:
    _do_forbidden(world, target_ent)
    world.say(
        f"{forbidden.strike} {forbidden.unit} flared to life. For one heartbeat it was lovely, like a tiny star. "
        f"Then the flame leaned, kissed {target.near}, and a line of orange began to climb."
    )


def alarm(world: World, child: Entity, elder: Entity, target: Target) -> None:
    world.say(f'"{child.id}! Fire! {target.The}!" {elder.id} cried.')
    world.say(f'"Help!"')


def rescue(world: World, elder: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["burning"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(f"{elder.id} came running and in a flash {elder.pronoun()} {body}.")
    world.say(
        f"The flame vanished, leaving only a smoky smell, a warm hush, and two very frightened hearts."
    )


def lesson(world: World, elder: Entity, child: Entity, forbidden: Forbidden) -> None:
    child.memes["lesson"] += 1
    elder.memes["love"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {elder.id} knelt and gathered {child.id} close. "
        f'"I am glad you called," {elder.pronoun()} said. '
        f'"But remember: {forbidden.not_toy}. Fire can beat faster than a child can run."'
    )
    world.say(f'"We promise," whispered {child.id} and {elder.id} together.')


def safe_gift(world: World, elder: Entity, child: Entity, h1: Helper, h2: Helper, theme: Theme) -> None:
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    world.say(
        f"The next day, {elder.id} had a gift. {elder.pronoun().capitalize()} gave them {h1.phrase} that {h1.glow}, "
        f"and {h2.phrase} that {h2.glow}."
    )
    world.say(
        f'"Now," {elder.pronoun()} smiled, "what does a brave child use to explore {theme.word_for_dark}?"'
    )
    world.say(f"{child.id} held up the {h2.label}. {child.id} clicked on the {h1.label}.")
    world.say(
        f'"Safe light!" they cheered, and the fairy-tale castle shimmered without a single risky spark.'
    )


def rescue_fail(world: World, elder: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["burning"] += 1
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{target}", target.label)
    world.say(f"{elder.id} came running and {body}.")
    world.say("The fire beat through the curtains and raced along the rafters.")


def escape_and_loss(world: World, elder: Entity, child: Entity, theme: Theme) -> None:
    child.memes["fear"] += 1
    world.say(
        f"There was no time for jewels or toys. {elder.id} grabbed {child.id}'s hand and rushed outside into the cold night."
    )
    world.say(
        "From the garden they watched the windows glow orange, and soon the little castle was full of smoke."
    )
    world.say(
        f"Their game -- the cloaks, the maps, the whole bright hall -- was gone, though they themselves were safe."
    )


def grim_lesson(world: World, elder: Entity, child: Entity, forbidden: Forbidden) -> None:
    child.memes["lesson"] += 1
    elder.memes["lesson"] += 1
    world.say(
        f"{elder.id} held {child.id} tightly on the grass and whispered, "
        f'"You are safe. That is what matters most."'
    )
    world.say(
        f"After that, {child.id} never forgot that {forbidden.not_toy}, and that a little spark can grow into something far bigger than a game."
    )


def tell(theme: Theme, forbidden: Forbidden, target: Target, helpers: tuple[Helper, Helper],
         response: Response, child: str = "Elsie", child_gender: str = "girl",
         elder: str = "Grandmother", elder_gender: str = "woman", elder_role: str = "grandmother",
         trait: str = "careful", delay: int = 0, child_age: int = 6, elder_age: int = 10,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    child_ent = world.add(Entity(id=child, kind="character", type=child_gender, role="child", traits=["brave"], age=child_age))
    elder_ent = world.add(Entity(id=elder, kind="character", type=elder_gender, role="elder", traits=[trait], age=elder_age, attrs={"role": elder_role}))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="target", type="target", label=target.label, flammable=target.flammable))
    world.facts["relation"] = relation
    world.facts["trust"] = trust
    theme_name = theme

    child_ent.memes["bravery"] = BRAVERY_INIT
    elder_ent.memes["trust"] = float(trust)
    elder_ent.memes["caution"] = 5.0 if trait in CAUTIOUS_TRAITS else 3.0

    tale_setup(world, child_ent, elder_ent, theme)
    need_light(world, child_ent, theme, target)
    world.para()
    foreshadow(world, elder_ent, child_ent, forbidden, target)
    tempt(world, child_ent, forbidden)
    averted = would_avert(relation, child_age, elder_age, trait)

    if averted:
        avert(world, child_ent, elder_ent, forbidden, theme)
        contained = True
        severity = 0
    else:
        defy(world, child_ent, forbidden)
        world.para()
        ignite(world, world.get("target"), forbidden, target)
        alarm(world, child_ent, elder_ent, target)
        severity = fire_severity(target, delay)
        contained = is_contained(response, target, delay)
        world.facts["severity"] = severity
        world.para()
        if contained:
            rescue(world, elder_ent, response, world.get("target"), target)
            lesson(world, elder_ent, child_ent, forbidden)
            world.para()
            safe_gift(world, elder_ent, child_ent, helpers[0], helpers[1], theme)
        else:
            rescue_fail(world, elder_ent, response, world.get("target"), target)
            escape_and_loss(world, elder_ent, child_ent, theme)
            grim_lesson(world, elder_ent, child_ent, forbidden)

    world.facts.update(
        child=child_ent, elder=elder_ent, forbidden=forbidden, target_cfg=target,
        target=world.get("target"), helpers=helpers, response=response,
        theme=theme, averted=averted, contained=contained, severity=severity,
        ignited=not averted, promised=child_ent.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "fairy_tale": Theme(
        id="fairy_tale",
        scene="a storybook castle with silver towers and a mossy bridge",
        rig="The hall was draped with lanterns, a toy crown gleamed on the table, and a painted map showed the way to the moonwell.",
        title_a="Brave",
        title_b="Clever",
        quest="the moonwell",
        dark_place="the tower stair",
        word_for_dark="the moonwell path",
        ending_image="a lantern-lit path under apple blossoms",
    ),
    "forest_tale": Theme(
        id="forest_tale",
        scene="an old forest with whispering trees and a tiny road of stones",
        rig="The cart stood like a tiny stage, a cloak hung on the peg, and a sketchy map pointed toward the hidden spring.",
        title_a="Brave",
        title_b="Gentle",
        quest="the hidden spring",
        dark_place="the hollow between the roots",
        word_for_dark="the root-path",
        ending_image="a soft glade with fireflies and a clear stream",
    ),
    "seaside_tale": Theme(
        id="seaside_tale",
        scene="a little harbor where gulls circled above the salt wind",
        rig="The cottage porch held a blue bucket, a shell necklace shone in the dusk, and a chalk map pointed toward the lantern rock.",
        title_a="Bold",
        title_b="Wise",
        quest="the lantern rock",
        dark_place="the cave mouth",
        word_for_dark="the tide cave",
        ending_image="a moonlit beach with shells glowing like pearls",
    ),
}

FORBIDDEN = {
    "lantern_matches": Forbidden(
        id="lantern_matches",
        label="the matchbox",
        phrase="a little matchbox",
        where="in the kitchen nook",
        unit="the first match",
        strike="Flick!",
        not_toy="matches are not toys",
        makes_flame=True,
        plural=False,
        tags={"fire", "matches", "cautionary"},
    ),
    "spark_candle": Forbidden(
        id="spark_candle",
        label="the candle",
        phrase="a stubby candle",
        where="on the mantel",
        unit="the candle flame",
        strike="Pop!",
        not_toy="candles are not toys",
        makes_flame=True,
        plural=False,
        tags={"fire", "candle", "cautionary"},
    ),
    "ember_lighter": Forbidden(
        id="ember_lighter",
        label="the lighter",
        phrase="a tiny lighter",
        where="on the shelf",
        unit="the tiny flame",
        strike="Click!",
        not_toy="lighters are not toys",
        makes_flame=True,
        plural=False,
        tags={"fire", "lighter", "cautionary"},
    ),
}

TARGETS = {
    "curtain": Target("curtain", "curtain", "the curtain", "the hem of the curtain", "hung with velvet curtains", 3, True, {"curtain"}),
    "banner": Target("banner", "banner", "the banner", "the edge of the banner", "hung with bright banners", 2, True, {"cloth"}),
    "straw": Target("straw", "straw broom", "the straw broom", "the broom end", "bound with straw", 2, True, {"straw"}),
    "tapestry": Target("tapestry", "tapestry", "the tapestry", "the lower thread", "hung with a wool tapestry", 3, True, {"cloth"}),
    "stone": Target("stone", "stone wall", "the stone wall", "the cool stone", "built of old stone", 0, False, {"stone"}),
}

HELPERS = {
    "flashlight": Helper("flashlight", "flashlight", "a little flashlight", "shone like a star"),
    "lantern": Helper("lantern", "lantern", "a warm lantern", "glowed gold and safe"),
    "glowstone": Helper("glowstone", "glow stone", "a moon-glow stone", "shimmered with pale light"),
    "torchless": Helper("torchless", "glass orb", "a glass orb of light", "glowed without any flame"),
}

RESPONSES = {
    "extinguish": Response(
        "extinguish", 4, 4,
        "seized the bucket by the door and extinguished the flames with a swift splash",
        "hurried for water, but the flames were already too wild to extinguish",
        "extinguished the flames with a swift splash",
        tags={"water", "extinguish"},
    ),
    "smother": Response(
        "smother", 3, 3,
        "pulled the curtain down and smothered the spark under a thick rug",
        "tried to smother the spark, but it danced out of reach",
        "smothered the spark under a thick rug",
        tags={"smother", "extinguish"},
    ),
    "stomp": Response(
        "stomp", 2, 2,
        "stamped hard on the sparks until they beat no more",
        "stamped at the sparks, but they beat higher instead",
        "stamped the sparks out",
        tags={"stomp", "extinguish"},
    ),
    "water_pail": Response(
        "water_pail", 1, 1,
        "grabbed a small pail and splashed a little water, too little to beat the flames",
        "splashed a small pail of water, but the fire beat the effort",
        "splashed water on the flames",
        tags={"water", "extinguish"},
    ),
}

GIRL_NAMES = ["Elsie", "Mira", "Nora", "Lina", "Iris", "Tilda"]
BOY_NAMES = ["Pip", "Hugo", "Bram", "Owen", "Theo", "Finn"]
TRAITS = ["careful", "cautious", "wise", "gentle", "serious", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for theme in THEMES:
        for fid, fb in FORBIDDEN.items():
            for tid, tg in TARGETS.items():
                if hazard_at_risk(fb, tg):
                    combos.append((theme, fid, tid))
    return combos


def explain_rejection(fb: Forbidden, tg: Target) -> str:
    if not tg.flammable:
        return f"(No story: {tg.the} will not catch fire, so there is no cautionary beat to tell.)"
    if not fb.makes_flame:
        return f"(No story: {fb.label} does not make a flame, so nothing dangerous happens.)"
    return "(No story: this combination has no fire hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    options = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it is too weak or too reckless for a fairy-tale rescue. Try {options}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    fb = f["forbidden"]
    tg = f["target_cfg"]
    theme = f["theme"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "extinguish" and "beat".',
        f"Tell a cautionary fairy tale where {child.id} wants to use {fb.label} near {tg.the}, but an elder gives a foreshadowing warning and the fire is extinguished.",
        f'Write a short story with bravery, cautionary advice, and foreshadowing, ending with a safe lantern image instead of a fire.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    fb: Forbidden = f["forbidden"]
    tg: Target = f["target_cfg"]
    theme: Theme = f["theme"]
    resp: Response = f["response"]
    qa: list[tuple[str, str]] = []
    qa.append((
        "Who is the story about?",
        f"It is about {child.id} and {elder.id}, who wandered through a fairy-tale castle and faced a small but dangerous spark."
    ))
    qa.append((
        "What made the tale cautionary?",
        f"{elder.id} warned that {fb.not_toy}, and that the flame could start near {tg.the}. The warning mattered because the story had already foreshadowed danger in the dark place."
    ))
    if f.get("averted"):
        qa.append((
            "What did the child do instead of touching the forbidden thing?",
            f"{child.id} listened, gave up the idea, and chose the safer road. That kept the fire from starting at all."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {theme.ending_image}. The fairy-tale world stayed bright because bravery was guided by caution."
        ))
    else:
        qa.append((
            "What happened when the forbidden thing was used?",
            f"The {tg.label} caught fire, and the flames began to climb. The danger beat faster after the spark touched it."
        ))
        if f.get("contained"):
            body = resp.qa_text.replace("{target}", tg.label)
            qa.append((
                "How was the fire handled?",
                f"{elder.id} came running and {body}. That quick move stopped the flames before they could spread through the whole castle."
            ))
            qa.append((
                "How did the characters feel at the end?",
                f"They felt shaken, then relieved, because the fire was gone and the lesson was clear. The brave part was asking for help."
            ))
        else:
            fail = resp.fail.replace("{target}", tg.label)
            qa.append((
                "Could the fire be stopped in time?",
                f"No. {elder.id} {fail}, and the fire beat the rescue before it could succeed."
            ))
            qa.append((
                "What was the ending image?",
                f"They escaped safely, but the hall was lost. Afterward, they remembered that {fb.not_toy}."
            ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["forbidden"].tags) | set(f["target_cfg"].tags) | set(f["response"].tags)
    if f.get("averted") or f.get("contained"):
        tags |= {"extinguish"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


KNOWLEDGE = {
    "fire": [("Why is fire dangerous?", "Fire is hot and can grow fast. It can burn things and hurt people if nobody stops it.")],
    "matches": [("What are matches?", "Matches are tiny tools that can make flame when a grown-up uses them carefully.")],
    "candle": [("Why can a candle be dangerous?", "A candle has a real flame, and it can light cloth on fire if it gets too close.")],
    "lighter": [("What is a lighter?", "A lighter is a small tool that makes a flame. Children should never play with it.")],
    "curtain": [("Why are curtains risky near flame?", "Curtains are cloth and can catch fire very quickly.")],
    "cloth": [("Can cloth burn?", "Yes. Cloth can burn, so flames should stay far away from it.")],
    "water": [("What does water do to a small fire?", "Water can help extinguish a small fire by taking away the heat the flames need.")],
    "extinguish": [("What does extinguish mean?", "To extinguish a fire means to put it out so it stops burning.")],
    "smother": [("What does smother mean?", "To smother a flame means to cover it so it cannot get enough air.")],
    "stomp": [("What does stomp mean?", "To stomp means to step down hard. In a story, stomping can help crush tiny sparks if the fire is very small.")],
}
KNOWLEDGE_ORDER = ["fire", "matches", "candle", "lighter", "curtain", "cloth", "water", "extinguish", "smother", "stomp"]


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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, fb in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if fb.makes_flame:
            lines.append(asp.fact("makes_flame", fid))
    for tid, tg in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if tg.flammable:
            lines.append(asp.fact("flammable", tid))
        lines.append(asp.fact("spread", tid, tg.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F, T) :- makes_flame(F), flammable(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), trait(T), not cautious_now(T).
authority(C + 1 + B) :- init_caution(C), bonus(B).
bonus(4) :- relation(siblings), elder_older.
bonus(0) :- not elder_older.
elder_older :- relation(siblings), child_age(C), elder_age(E), E > C.
averted :- elder_older, authority(A), bravery_init(B), A > B.

severity(V) :- chosen_target(T), spread(T, S), delay(D), V = S + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


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
    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("child_age", params.child_age),
        asp.fact("elder_age", params.elder_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in gate")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    cases = [CURATED[0]]
    for seed in range(10):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(seed)))
        except StoryError:
            pass
    mismatch = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatch:
        rc = 1
        print(f"MISMATCH in outcomes: {mismatch}")
    else:
        print("OK: ASP and Python parity verified, and a smoke-test story generated.")
    return rc


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.elder_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: bravery, cautionary warning, and foreshadowed fire.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["grandmother", "grandfather"])
    ap.add_argument("--child", choices=None)
    ap.add_argument("--elder", choices=None)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid] or pool
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.forbidden and args.target:
        fb, tg = FORBIDDEN[args.forbidden], TARGETS[args.target]
        if not hazard_at_risk(fb, tg):
            raise StoryError(explain_rejection(fb, tg))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    helper1, helper2 = rng.sample(sorted(HELPERS), 2)
    child_gender = rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, child_gender)
    elder_gender = rng.choice(["woman", "man"])
    elder = args.elder or ("Grandmother" if elder_gender == "woman" else "Grandfather")
    elder_role = args.parent or ("grandmother" if elder_gender == "woman" else "grandfather")
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    child_age = rng.randint(4, 7)
    elder_age = rng.randint(9, 14)
    trust = rng.randint(0, 10)
    relation = rng.choice(["siblings", "grandparent"])
    return StoryParams(
        theme=theme, forbidden=forbidden, target=target, helper1=helper1, helper2=helper2,
        response=response, child=child, child_gender=child_gender, elder=elder, elder_gender=elder_gender,
        elder_role=elder_role, trait=trait, delay=delay, child_age=child_age, elder_age=elder_age,
        relation=relation, trust=trust
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.forbidden not in FORBIDDEN or params.target not in TARGETS or params.response not in RESPONSES:
        raise StoryError("Invalid StoryParams: unknown key.")
    world = tell(THEMES[params.theme], FORBIDDEN[params.forbidden], TARGETS[params.target],
                 (HELPERS[params.helper1], HELPERS[params.helper2]), RESPONSES[params.response],
                 child=params.child, child_gender=params.child_gender, elder=params.elder,
                 elder_gender=params.elder_gender, elder_role=params.elder_role,
                 trait=params.trait, delay=params.delay, child_age=params.child_age,
                 elder_age=params.elder_age, relation=params.relation, trust=params.trust)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams(theme="fairy_tale", forbidden="lantern_matches", target="curtain", helper1="flashlight", helper2="lantern", response="extinguish", child="Elsie", child_gender="girl", elder="Grandmother", elder_gender="woman", elder_role="grandmother", trait="careful", delay=0, child_age=6, elder_age=11, relation="grandparent", trust=7),
    StoryParams(theme="forest_tale", forbidden="spark_candle", target="tapestry", helper1="glowstone", helper2="torchless", response="smother", child="Bram", child_gender="boy", elder="Grandfather", elder_gender="man", elder_role="grandfather", trait="wise", delay=1, child_age=5, elder_age=12, relation="grandparent", trust=5),
    StoryParams(theme="seaside_tale", forbidden="ember_lighter", target="banner", helper1="lantern", helper2="flashlight", response="stomp", child="Mira", child_gender="girl", elder="Grandmother", elder_gender="woman", elder_role="grandmother", trait="cautious", delay=0, child_age=7, elder_age=13, relation="grandparent", trust=8),
]


def valid_story_exists() -> bool:
    return bool(valid_combos()) and bool(sensible_responses())


def asp_valid_combos_text() -> str:
    return "\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos())


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for t, f, x in asp_valid_combos():
            print(f"{t:12} {f:16} {x}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all and sample.params:
            p = sample.params
            header = f"### {p.child} & {p.elder}: {p.forbidden} near {p.target} ({outcome_of(p)})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
