#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/change_cautionary_pirate_tale.py
===============================================================

A standalone story world sketch for a cautionary pirate tale about change:
two young pirates want to change how they explore at night, reach for an unsafe
flame, get warned in time, and end with a safer lantern and a changed plan.

This world keeps the story small, concrete, and state-driven:
- physical meters track danger, smoke, scorch, and cleanup
- emotional memes track curiosity, fear, relief, pride, and lesson
- a simple forward rule engine turns fire into danger and fear
- an ASP twin mirrors the reasonableness gate and outcome logic

Run it:
    python storyworlds/worlds/gpt-5.4-mini/change_cautionary_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/change_cautionary_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/change_cautionary_pirate_tale.py --verify
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
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    makes_flame: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "captain": "captain"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    leader_title: str
    mate_title: str
    goal: str
    dark_spot: str
    place_word: str
    crew_word: str
    ending: str


@dataclass
class Forbidden:
    id: str
    cry: str
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
class Hazard:
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
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_fire(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("fire", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for ch in world.characters():
            ch.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("fire", "physical", _r_fire)]


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


def hazard_at_risk(forbidden: Forbidden, hazard: Hazard) -> bool:
    return forbidden.makes_flame and hazard.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def fire_severity(hazard: Hazard, delay: int) -> int:
    return hazard.spread + delay


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= fire_severity(hazard, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(hazard_id), narrate=False)
    return {
        "ignites": sim.get(hazard_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a windy evening, {a.id} and {b.id} turned the ship's deck into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.leader_title} {a.id} and {theme.mate_title} {b.id}!" {a.id} shouted. '
        f'"Let\'s find {theme.goal}!"'
    )


def need_light(world: World, b: Entity, theme: Theme, hazard: Hazard) -> None:
    world.say(
        f"But the {theme.place_word} under the stairs was dark -- {hazard.drape}. "
        f'{b.id} peered inside and whispered, "We need a light."'
    )


def tempt(world: World, a: Entity, forbidden: Forbidden) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id}\'s eyes lit up. "I know! {forbidden.cry} I saw {forbidden.phrase} '
        f'{forbidden.where}."'
    )
    world.say("For one breath, the idea sounded clever.")


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden, hazard: Hazard, parent: Entity) -> None:
    pred = predict_fire(world, "hazard")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f' {b.pronoun().capitalize()} was sure it would go wrong.'
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. "{a.id}, we are not allowed to touch '
        f'{forbidden.label}. {parent.label_word.capitalize()} said. It can make a real flame, '
        f"and {hazard.the} could catch."{extra}"
    )


def defy(world: World, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    a.memes["defiance"] += 1
    world.say(f'"Don\'t be such a scaredy-cat," {a.id} said, and ran to get {forbidden.label}.')


def back_down(world: World, a: Entity, b: Entity, forbidden: Forbidden, parent: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'"Don\'t be such a scaredy-cat," {a.id} said. But {b.id} was {a.pronoun("possessive")} '
        f"older sibling, so {a.id} looked at {b.pronoun('object')}, thought better of it, and gave up."
    )
    world.say(
        f"They left {forbidden.label} where it was and went to tell {parent.label_word.capitalize()} "
        f"how dark the {theme.place_word} had been."
    )


def ignite(world: World, hazard_ent: Entity, forbidden: Forbidden, hazard: Hazard) -> None:
    _do_forbidden(world, hazard_ent)
    world.say(
        f"{forbidden.strike} {forbidden.unit.capitalize()} flared to life. For one second it was wonderful, "
        f"a tiny golden flame pretending to be a lantern. Then the flame leaned, kissed {hazard.near}, "
        f"and orange climbed upward."
    )


def alarm(world: World, b: Entity, a: Entity, hazard: Hazard, parent: Entity) -> None:
    world.say(f'"{a.id}! Fire! {hazard.The}!" {b.id} screamed.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, hazard_ent: Entity, hazard: Hazard, theme: Theme) -> None:
    hazard_ent.meters["burning"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running. In a flash {parent.pronoun()} {response.text.replace('{hazard}', hazard.label)}."
    )
    world.say(
        f"The flame hissed and died, leaving only a smoky smell and two very frightened {theme.crew_word}."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"I am not angry that you are scared," {parent.pronoun()} said softly. '
        f'"I am glad you called me. But you must always remember: {forbidden.not_toy}. '
        f"Fire can grow faster than you can run. Promise me -- never, ever again."
    )
    world.say(f'"We promise," whispered {b.id} and {a.id} together.')


def safe_change(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, l1: SafeLight, l2: SafeLight) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next morning, {parent.label_word.capitalize()} had a surprise. {parent.pronoun().capitalize()} handed them "
        f"{l1.phrase} that {l1.glow}, and {l2.phrase} that {l2.glow}."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "what does a pirate need to explore a dark {theme.place_word}?"'
    )
    world.say(f"{a.id} held up the {l2.label}. {b.id} clicked on the {l1.label}.")
    world.say('"Safe light!" they cheered.')
    world.say(
        f"This time, the {theme.crew_word} sailed on with a changed plan -- bright, brave, and safe."
    )


def rescue_fail(world: World, parent: Entity, response: Response, hazard_ent: Entity, hazard: Hazard) -> None:
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
    hazard_ent.meters["burning"] += 1
    propagate(world, narrate=False)
    world.say(f"{parent.label_word.capitalize()} came running and {response.fail.replace('{hazard}', hazard.label)}.")
    world.say(f"The flames leapt from {hazard.the} to the sailcloth and raced across the deck.")


def escape_and_loss(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f"There was no time to be brave. {parent.label_word.capitalize()} grabbed {a.id} and {b.id} by the hand "
        f"and rushed them outside into the cold night air."
    )
    world.say(
        f"From the shore they watched the ship glow orange, and by the time the fire brigade arrived, "
        f"the little game was gone."
    )
    world.say(
        f"The deck, the treasure map, and the pretend pirate fort were all lost, but the crew got out safely."
    )


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'"You are safe. That is what matters," {parent.label_word.capitalize()} whispered while holding them tight.'
    )
    world.say(
        f"After that night, {a.id} and {b.id} never forgot: {forbidden.not_toy}, and fire can grow faster than anyone can run."
    )


def tell(theme: Theme, forbidden: Forbidden, hazard: Hazard, lights: tuple[SafeLight, SafeLight], response: Response,
         instigator: str = "Finn", instigator_gender: str = "boy", cautioner: str = "Mira", cautioner_gender: str = "girl",
         parent_type: str = "captain", trait: str = "careful", delay: int = 0,
         instigator_age: int = 6, cautioner_age: int = 8, relation: str = "siblings", trust: int = 7,
         pet: str = "") -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator", age=instigator_age, attrs={"relation": relation}))
    b = world.add(Entity(id=cautioner, kind="character", type=cautioner_gender, role="cautioner", age=cautioner_age, traits=[trait], attrs={"relation": relation}))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, role="parent", label="the captain"))
    world.add(Entity(id="room", type="room", label="the dark hold"))
    target = world.add(Entity(id="hazard", type="thing", label=hazard.label, flammable=hazard.flammable))
    tool = world.add(Entity(id="tool", type="thing", label=forbidden.label, makes_flame=True))
    world.facts["pet"] = pet

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    setup(world, a, b, theme)
    need_light(world, b, theme, hazard)
    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, hazard, parent)

    averted = would_avert(relation, a.age, b.age, trait)
    if averted:
        back_down(world, a, b, forbidden, parent, theme)
        world.para()
        safe_change(world, parent, a, b, theme, lights[0], lights[1])
        severity = 0
        contained = True
    else:
        defy(world, a, b, forbidden)
        world.para()
        ignite(world, target, forbidden, hazard)
        alarm(world, b, a, hazard, parent)
        severity = fire_severity(hazard, delay)
        contained = is_contained(response, hazard, delay)
        target.meters["severity"] = float(severity)
        world.para()
        if contained:
            rescue(world, parent, response, target, hazard, theme)
            lesson(world, parent, a, b, forbidden)
            world.para()
            safe_change(world, parent, a, b, theme, lights[0], lights[1])
        else:
            rescue_fail(world, parent, response, target, hazard)
            escape_and_loss(world, parent, a, b, theme)
            grim_lesson(world, parent, a, b, forbidden)

    outcome = "averted" if averted else ("contained" if contained else "burned")
    world.facts.update(
        instigator=a, cautioner=b, parent=parent, theme=theme, forbidden=forbidden,
        hazard_cfg=hazard, hazard=target, tool=tool, lights=lights, response=response,
        outcome=outcome, rescued=contained, severity=severity, delay=delay,
        ignited=target.meters["scorched"] >= THRESHOLD,
        relation=relation, trait=trait, pet=pet,
    )
    return world


THEMES = {
    "night_watch": Theme("night_watch", "a cozy pirate camp", "The sofa was the ship, a blanket became the sail, an old crate held treasure, and a paper map showed the way.", "Captain", "Mate", "the treasure chest", "the dark hold", "the hold", "crew", "changed and bright"),
    "island": Theme("island", "a windy island camp", "A chair became the lookout, a scarf became the flag, an empty box held the jewels, and a chalk map showed the route.", "Captain", "Scout", "the hidden cave", "the cave under the hatch", "the hatch", "pirates", "sailing on"),
    "harbor": Theme("harbor", "a little harbor fort", "The bench was the ship, a towel became the sail, an old tin held the coins, and a crayon map pointed to the dock.", "Captain", "Lookout", "the buried chest", "the dark storage room", "the storage room", "pirate crew", "set off safely"),
}

FORBIDDEN = {
    "matches": Forbidden("matches", "Matches!", "matches", "a box of matches", "in the captain's drawer", "the first match", "Scritch!", "matches are not toys", tags={"matches", "fire"}),
    "lighter": Forbidden("lighter", "A lighter!", "the lighter", "a lighter", "on the worktable", "the tiny flame", "Click!", "a lighter is not a toy", tags={"lighter", "fire"}),
    "candle": Forbidden("candle", "A candle!", "the candle", "a candle and long wicks", "on the shelf", "the candle flame", "Flick!", "candles are not toys", tags={"candle", "fire"}),
}

HAZARDS = {
    "sailcloth": Hazard("sailcloth", "sailcloth", "the sailcloth", "the edge of the sailcloth", "hung with dry sailcloth", 3, tags={"sailcloth", "cloth"}),
    "curtain": Hazard("curtain", "curtain", "the curtain", "the hem of the curtain", "hung with long canvas curtains", 2, tags={"curtain", "cloth"}),
    "rope": Hazard("rope", "rope coil", "the rope coil", "the rope fibers", "piled with dry rope", 2, tags={"rope", "cloth"}),
}

SAFE_LIGHTS = {
    "lantern": SafeLight("lantern", "lantern", "a little lantern", "glowed warm and safe", tags={"lantern"}),
    "flashlight": SafeLight("flashlight", "flashlight", "a bright flashlight", "shone like a star", tags={"flashlight"}),
    "glowsticks": SafeLight("glowsticks", "glow sticks", "two bendy glow sticks", "glimmered green in the dark", tags={"glowsticks"}),
}

RESPONSES = {
    "extinguisher": Response("extinguisher", 3, 4, "grabbed the fire extinguisher from the wall and sprayed the flames until every spark was gone", "reached for the extinguisher, but the flames were already too big to stop", "put the flames out with the fire extinguisher", tags={"extinguisher"}),
    "smother": Response("smother", 3, 3, "pulled the {hazard} down, wrapped it in a heavy blanket, and pressed the flames out", "tried to pull the {hazard} down, but the fire was climbing too fast to smother", "pulled the {hazard} down and smothered the flames", tags={"smother"}),
    "stomp": Response("stomp", 2, 2, "pulled the {hazard} down and stamped on the flames, hard and fast, until they were out", "stamped at the flames, but they only leapt higher", "pulled the {hazard} down and stamped the flames out", tags={"smother"}),
    "water_bucket": Response("water_bucket", 1, 1, "filled a bucket at the sink and threw the water over the {hazard}", "threw a bucket of water over the {hazard}, but it was far too little", "threw a bucket of water over the {hazard}", tags={"water"}),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Ava", "Zoe", "Ella", "Maya", "Ruby"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Sam", "Jude", "Noah", "Eli"]
TRAITS = ["careful", "cautious", "thoughtful", "sensible", "curious"]
PETS = ["the cat", "the puppy", "their little dog", "the kitten"]


@dataclass
class StoryParams:
    theme: str
    forbidden: str
    hazard: str
    light1: str
    light2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 8
    relation: str = "siblings"
    trust: int = 7
    pet: str = ""
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for theme in THEMES:
        for forbidden in FORBIDDEN:
            for hazard in HAZARDS:
                if hazard_at_risk(FORBIDDEN[forbidden], HAZARDS[hazard]):
                    combos.append((theme, forbidden, hazard))
    return combos


KNOWLEDGE = {
    "matches": [("What are matches?", "Matches are tiny sticks that make a flame when you scratch them. They are a grown-up tool, not a toy.")],
    "lighter": [("What is a lighter?", "A lighter is a small tool grown-ups use to make a flame. Children should never touch one.")],
    "candle": [("Why can a candle be dangerous?", "A candle has a real flame, and if it tips over or touches something it can start a fire.")],
    "fire": [("Why is fire dangerous?", "Fire is very hot and it can grow faster than you can run, so it can burn things and hurt people quickly.")],
    "lantern": [("What is a lantern?", "A lantern is a light that can glow safely, often with batteries or a safe fuel, so you can see in the dark.")],
    "flashlight": [("What is a flashlight?", "A flashlight is a battery light you turn on with a button. It is bright and safe with no flame.")],
    "glowsticks": [("What are glow sticks?", "Glow sticks are bendy sticks that shine with a soft light after you snap them. They are cool and safe to hold.")],
    "extinguisher": [("What does a fire extinguisher do?", "A fire extinguisher sprays out stuff that smothers a fire and helps put it out quickly.")],
    "smother": [("How can you put out a small fire by smothering it?", "You take away the air the fire needs, like with a thick blanket, and the flames go out.")],
    "call_adult": [("What should you do if something catches fire?", "Get away from the fire and shout for a grown-up right away. Calling for help fast is the bravest thing to do.")],
}
KNOWLEDGE_ORDER = ["matches", "lighter", "candle", "fire", "lantern", "flashlight", "glowsticks", "extinguisher", "smother", "call_adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, fb, th, hz = f["instigator"], f["cautioner"], f["forbidden"], f["theme"], f["hazard_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate story for a 3-to-5-year-old where {a.id} wants to use {fb.label} in a dark {th.place_word}, but {b.id} changes the plan before any fire starts.',
            f'Tell a cautionary pirate tale where an older sibling warns a younger one not to touch {fb.label}, and the crew ends with safe light instead.',
            f'Write a simple story that includes the word "change" and ends with pirates choosing a safer way to explore the dark {th.place_word}.',
        ]
    if outcome == "burned":
        return [
            f'Write a pirate cautionary story where {a.id} ignores a warning and uses {fb.label} near {hz.the}, and the fire becomes too big to fix in time.',
            f'Tell a sad but safe pirate tale about a bad choice with {fb.label}, a quick escape, and a changed lesson for the crew.',
            f'Write a story that includes "change" and shows why children should never use {fb.label} around dry cloth.',
        ]
    return [
        f'Write a pirate cautionary story where {a.id} reaches for {fb.label}, but a calm grown-up puts out the fire and the crew uses safe light after that.',
        f'Tell a story where pirates learn that {fb.not_toy} and then change to a safer way to explore the dark {th.place_word}.',
        f'Write a simple story that includes "change", {fb.label}, and {hz.label}, with a safe ending for young children.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    fb, th, hz, resp = f["forbidden"], f["theme"], f["hazard_cfg"], f["response"]
    l1, l2 = f["lights"]
    qa = [
        QAItem("Who is the story about?", f"It is about {a.id} and {b.id}, two young pirates who were exploring a pretend ship. Their captain came in to help when the choice got dangerous."),
        QAItem("Why did they need a light?", f"They wanted to explore {th.dark_spot}, but that place was dark and hidden from the lantern glow. That darkness is what made the unsafe flame idea tempting."),
        QAItem(f"What did {a.id} want to use?", f"{a.id} wanted to use {fb.label}, but {b.id} warned that it was not allowed. {b.id} knew it could make a real flame near {hz.the}."),
    ]
    if f["outcome"] == "averted":
        qa.append(QAItem(f"What changed after the warning?", f"{a.id} changed the plan, left {fb.label} alone, and chose safer light instead. No fire started at all, so the crew could keep playing safely."))
        qa.append(QAItem("How did the story end?", f"It ended with {l1.phrase} and {l2.phrase} lighting the way. The pirates kept their adventure, but they used a safer tool and the dark stayed harmless."))
    elif f["outcome"] == "contained":
        body = resp.qa_text.replace("{hazard}", hz.label)
        qa.append(QAItem("What happened when the flame started?", f"{hz.The} caught fire and the children got very scared. The danger came from using {fb.label} near dry cloth."))
        qa.append(QAItem("How was the fire put out?", f"{parent.label_word.capitalize()} came running and {body}. That stopped the fire before it could spread through the ship."))
        qa.append(QAItem("How did the story end?", f"It ended safely, with the captain hugging them and then giving them {l1.phrase} and {l2.phrase}. The crew learned to change to safer light after the scare."))
    else:
        fail = resp.fail.replace("{hazard}", hz.label)
        qa.append(QAItem("Could the grown-up stop the fire in time?", f"No. {parent.label_word.capitalize()} {fail}, and the flames raced across the deck. The family had to escape because the fire was already too big."))
        qa.append(QAItem("How did the story end?", f"Everyone got out safely, but the ship game was lost. The crew learned that one unsafe choice can change everything very quickly."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["forbidden"].tags) | set(world.facts["hazard_cfg"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("night_watch", "matches", "sailcloth", "lantern", "flashlight", "extinguisher",
                "Finn", "boy", "Mira", "girl", "captain", "careful", 0, 6, 8, "siblings", 8, "the cat"),
    StoryParams("island", "lighter", "curtain", "glowsticks", "lantern", "smother",
                "Leo", "boy", "Nora", "girl", "captain", "thoughtful", 0, 5, 7, "siblings", 5, ""),
    StoryParams("harbor", "candle", "rope", "flashlight", "lantern", "stomp",
                "Ava", "girl", "Eli", "boy", "captain", "cautious", 1, 6, 9, "siblings", 4, "the puppy"),
]


def explain_rejection(forbidden: Forbidden, hazard: Hazard) -> str:
    if not hazard.flammable:
        return f"(No story: {forbidden.label} can make a flame, but {hazard.the} would not catch fire.)"
    if not forbidden.makes_flame:
        return f"(No story: {hazard.the} is flammable, but {forbidden.label} makes no flame.)"
    return "(No story: this combination has no fire hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < 2). Try: {good}.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay) else "burned"


ASP_RULES = r"""
hazard(F, H) :- makes_flame(F), flammable(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, F, H) :- theme(T), forbidden(F), hazard(H), hazard(F, H).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older.
bonus(0) :- not older.
authority(A) :- init_caution(C), bonus(B), A = C + 1 + B.
averted :- older, authority(A), bravery_init(B), A > B.

severity(V) :- chosen_hazard(H), spread(H, S), delay(D), V = S + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, f in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if f.makes_flame:
            lines.append(asp.fact("makes_flame", fid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.flammable:
            lines.append(asp.fact("flammable", hid))
        lines.append(asp.fact("spread", hid, h.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for t in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", t))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:", sorted(c_sens), sorted(p_sens))

    # Smoke test a real generation path.
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke generation produced empty story.")
    else:
        print("OK: smoke generation succeeded.")

    cases = list(CURATED)
    for s in range(50):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale about change and safer choices.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["captain"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.forbidden and args.hazard and not hazard_at_risk(FORBIDDEN[args.forbidden], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(FORBIDDEN[args.forbidden], HAZARDS[args.hazard]))
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, forbidden, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(theme, forbidden, hazard, light1, light2, response,
                       instigator, ig, cautioner, cg, "captain", trait, delay,
                       instigator_age, cautioner_age, relation, trust, pet)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], FORBIDDEN[params.forbidden], HAZARDS[params.hazard],
                 (SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]),
                 RESPONSES[params.response], params.instigator, params.instigator_gender,
                 params.cautioner, params.cautioner_gender, params.parent, params.trait,
                 params.delay, params.instigator_age, params.cautioner_age, params.relation,
                 params.trust, params.pet)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, forbidden, hazard) combos:\n")
        for theme, forbidden, hazard in combos:
            print(f"  {theme:12} {forbidden:10} {hazard}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.forbidden} near {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
