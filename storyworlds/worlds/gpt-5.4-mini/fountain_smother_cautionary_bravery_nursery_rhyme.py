#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fountain_smother_cautionary_bravery_nursery_rhyme.py
=====================================================================================

A small standalone story world for a nursery-rhyme cautionary tale about a child,
a fountain, a risky spark, and a brave, calm adult who smothers the little flame
before it can spread.

The world is intentionally tiny:
- one child is tempted by a bright, forbidden spark near a garden fountain
- a cautioning sibling or friend warns first
- if the child ignores the warning, a small mishap can happen
- a grown-up uses a sensible smothering response
- the ending proves bravery can mean calling for help and choosing safety

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
- generates three Q&A sets from world state
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 6.0
CAUTION_TRAITS = {"careful", "cautious", "watchful", "sensible"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
    go_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    label: str
    phrase: str
    danger_line: str
    makes_flame: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    near: str
    flammable: bool = True
    spread: int = 2
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "garden": Setting("garden", "the garden", "a moonlit garden", "the dark hedge", "through the gate", {"garden"}),
    "courtyard": Setting("courtyard", "the courtyard", "a quiet courtyard", "the stone corner", "through the arch", {"courtyard"}),
    "park": Setting("park", "the park", "a sleepy park", "the shadow under the trees", "down the path", {"park"}),
}

TEMPTATIONS = {
    "sparkler": Temptation("sparkler", "sparkler", "a sparking sparkler", "tiny silver sparks danced near the fountain", True, {"spark"}),
    "match": Temptation("match", "match", "a single match", "a tiny flame leaned toward the fountain reeds", True, {"fire"}),
    "lantern": Temptation("lantern", "lantern", "a little lantern", "its little flame shone by the fountain", True, {"fire"}),
}

HAZARDS = {
    "fountain": Hazard("fountain", "fountain", "the fountain", "the fountain rim", True, 2, {"fountain", "water"}),
    "paperboat": Hazard("paperboat", "paper boat", "the paper boat", "the paper boat by the water", True, 1, {"paper"}),
    "reeds": Hazard("reeds", "reeds", "the reeds", "the reeds beside the fountain", True, 3, {"reeds", "dry"}),
}

RESPONSES = {
    "smother_cloth": Response(
        "smother_cloth", 3, 4,
        "lifted a damp cloth and smothered the little flame until it sighed away",
        "lifted a damp cloth, but the flame was already too lively to smother",
        "lifted a damp cloth and smothered the little flame",
        {"smother", "cloth"},
    ),
    "smother_basket": Response(
        "smother_basket", 3, 3,
        "covered the spark with a wet basket and smothered it before it could leap",
        "covered the spark with a wet basket, but the flames danced out again",
        "covered the spark with a wet basket and smothered it",
        {"smother", "basket"},
    ),
    "smother_towel": Response(
        "smother_towel", 2, 2,
        "pressed a wet towel over the ember and smothered it fast",
        "pressed a wet towel over the ember, but it was too small a fix",
        "pressed a wet towel over the ember and smothered it",
        {"smother", "towel"},
    ),
    "water_cup": Response(
        "water_cup", 1, 1,
        "splashed a little cup of water on the ember",
        "splashed a little cup of water on the ember, but that was not enough",
        "splashed a little cup of water on the ember",
        {"water"},
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Zoe", "Ella", "Rose", "Mia", "Ava"]
BOY_NAMES = ["Tom", "Finn", "Eli", "Sam", "Leo", "Max", "Noah", "Jack"]
TRAITS = ["careful", "cautious", "watchful", "curious", "gentle", "sensible"]


@dataclass
class StoryParams:
    setting: str
    temptation: str
    hazard: str
    response: str
    child: str
    child_gender: str
    sibling: str
    sibling_gender: str
    parent: str
    trait: str
    delay: int = 0
    child_age: int = 6
    sibling_age: int = 8
    relation: str = "siblings"
    seed: Optional[int] = None


def hazard_at_risk(temptation: Temptation, hazard: Hazard) -> bool:
    return temptation.makes_flame and hazard.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for tid, temp in TEMPTATIONS.items():
            for hid, haz in HAZARDS.items():
                if hazard_at_risk(temp, haz):
                    out.append((sid, tid, hid))
    return out


def fire_severity(hazard: Hazard, delay: int) -> int:
    return hazard.spread + delay


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= fire_severity(hazard, delay)


def would_avert(relation: str, child_age: int, sibling_age: int, trait: str) -> bool:
    older = relation == "siblings" and sibling_age > child_age
    caution = 5.0 if trait in CAUTION_TRAITS else 3.0
    authority = caution + 1.0 + (4.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def _fire_rule(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("fire", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.entities.values():
            if kid.role in {"child", "cautioner"}:
                kid.memes["fear"] += 1
        out.append("__fire__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for sent in _fire_rule(world):
            changed = True
            if not sent.startswith("__"):
                produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_fire(world: World, hazard_id: str, response_id: str) -> dict:
    sim = world.copy()
    h = sim.get(hazard_id)
    h.meters["burning"] += 1
    propagate(sim, narrate=False)
    return {
        "burning": h.meters["burning"] >= THRESHOLD,
        "danger": sum(e.memes.get("fear", 0) for e in sim.entities.values()),
    }


def setup(world: World, child: Entity, sibling: Entity, setting: Setting) -> None:
    child.memes["bravery"] = BRAVERY_INIT
    sibling.memes["caution"] = 5.0
    child.memes["joy"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"On a hush-hush evening in {setting.place}, {child.id} and {sibling.id} made a nursery game of the moonlit garden. "
        f"The {setting.scene} looked like a silver bowl, and the {setting.dark_spot} waited quiet and cool."
    )
    world.say(
        f'"Let us tiptoe and sing," said {child.id}, "for the fountain glimmered and sang."'
    )


def temptation_beat(world: World, child: Entity, temp: Temptation, haz: Hazard) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} spied {temp.phrase}. " 
        f'"I could make it dance," {child.pronoun()} said, for brave hearts sometimes leap before they look.'
    )
    world.say(f"But {temp.danger_line}, and the {haz.label} was no place for tricks.")


def warn(world: World, sibling: Entity, child: Entity, temp: Temptation, haz: Hazard, parent: Entity) -> None:
    pred = predict_fire(world, haz.id, temp.id)
    sibling.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"{sibling.id} bit {sibling.pronoun('possessive')} lip. "
        f'"No, {child.id}," {sibling.pronoun()} said. '
        f'"The {haz.label} can catch, and {temp.label} is not a toy. Call {parent.label_word}."'
    )


def back_down(world: World, child: Entity, sibling: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["relief"] += 1
    sibling.memes["relief"] += 1
    world.say(
        f"{child.id} held still, then nodded. " 
        f'"You are right," {child.pronoun()} said. "Brave means listening too."'
    )
    world.say(
        f"So they left the spark where it was and went to tell {parent.label_word} about the dark {setting.go_word} and the silver fountain."
    )


def defy(world: World, child: Entity, sibling: Entity, temp: Temptation) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Not me, not today," said {child.id}, and {child.pronoun()} reached for {temp.label} anyway.'
    )


def ignite(world: World, hazard_ent: Entity, temp: Temptation, haz: Hazard) -> None:
    hazard_ent.meters["burning"] += 1
    hazard_ent.meters["scorched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The spark went flicker, the {haz.label} went hiss, and a little flame leaned toward the reeds."
    )


def alarm(world: World, sibling: Entity, child: Entity, haz: Hazard, parent: Entity) -> None:
    world.say(f'"{child.id}! Fire by the {haz.label}!" cried {sibling.id}.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, hazard_ent: Entity, haz: Hazard) -> None:
    hazard_ent.meters["burning"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running. In one brave breath, {parent.pronoun()} {response.text}."
    )
    world.say(
        f"The flame gave a tiny sigh and was gone, leaving only a wet smell and a dark little patch by the fountain."
    )


def lesson(world: World, parent: Entity, child: Entity, sibling: Entity, temp: Temptation) -> None:
    for kid in (child, sibling):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"Bravery is fine," {parent.pronoun()} said softly, "but bravery listens first. '
        f'{temp.label.capitalize()} is not a plaything, and fire can grow too fast."'
    )
    world.say(f'"We promise," whispered {sibling.id} and {child.id}.')
    world.say("The moon kept shining on the fountain, quiet and safe.")


def safe_end(world: World, parent: Entity, child: Entity, sibling: Entity) -> None:
    child.memes["joy"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} showed them a safe lantern and a storybook with a brave, careful knight. "
        f"{child.id} held the lantern, {sibling.id} turned the pages, and the fountain sparkled without any sparks at all."
    )
    world.say("So the children sang their little song and played on, bright and sound, with safety all around.")


def tell(setting: Setting, temp: Temptation, haz: Hazard, resp: Response,
         child_name: str = "Lily", child_gender: str = "girl",
         sibling_name: str = "Tom", sibling_gender: str = "boy",
         parent_type: str = "mother", trait: str = "cautious",
         delay: int = 0, child_age: int = 6, sibling_age: int = 8,
         relation: str = "siblings") -> World:
    world = World(setting)
    child = world.add(Entity(child_name, "character", child_gender, role="child", age=child_age, traits=[trait]))
    sibling = world.add(Entity(sibling_name, "character", sibling_gender, role="cautioner", age=sibling_age, traits=[trait]))
    parent = world.add(Entity("Parent", "character", parent_type, role="parent", label="the parent"))
    hazard_ent = world.add(Entity("hazard", "thing", haz.id, label=haz.label))
    world.facts.update(setting=setting, temp=temp, haz=haz, resp=resp)

    setup(world, child, sibling, setting)
    world.para()
    temptation_beat(world, child, temp, haz)
    warn(world, sibling, child, temp, haz, parent)

    averted = would_avert(relation, child_age, sibling_age, trait)
    if averted:
        back_down(world, child, sibling, parent, setting)
        world.para()
        safe_end(world, parent, child, sibling)
        outcome = "averted"
        contained = True
        severity = 0
    else:
        defy(world, child, sibling, temp)
        world.para()
        ignite(world, hazard_ent, temp, haz)
        alarm(world, sibling, child, haz, parent)
        severity = fire_severity(haz, delay)
        contained = is_contained(resp, haz, delay)
        world.para()
        if contained:
            rescue(world, parent, resp, hazard_ent, haz)
            lesson(world, parent, child, sibling, temp)
            world.para()
            safe_end(world, parent, child, sibling)
            outcome = "contained"
        else:
            world.say(
                f"{parent.label_word.capitalize()} came running, but {resp.fail}."
            )
            world.say("The little fire grew big enough to frighten the whole garden, and everyone ran to safety.")
            world.say("By morning, the fountain stood wet and blackened, and the children remembered the lesson.")
            outcome = "burned"
    world.facts.update(child=child, sibling=sibling, parent=parent, hazard_ent=hazard_ent,
                       outcome=outcome, contained=contained, severity=severity, delay=delay)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, sibling, temp, haz = f["child"], f["sibling"], f["temp"], f["haz"]
    return [
        f'Write a nursery-rhyme style cautionary story with the words "{haz.label}" and "{temp.label}".',
        f"Tell a gentle story where {child.id} wants to use {temp.label} near the {haz.label}, but {sibling.id} warns first.",
        f'Write a child-friendly story about bravery that ends with a grown-up using "{RESPONSES["smother_cloth"].qa_text}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, sibling, parent = f["child"], f["sibling"], f["parent"]
    temp, haz, resp = f["temp"], f["haz"], f["resp"]
    qas = [
        QAItem(
            question="Why did the cautioning child speak up?",
            answer=f"{sibling.id} spoke up because the {haz.label} was a risky place for {temp.label}. {sibling.id} wanted a grown-up called before anything could catch.",
        ),
        QAItem(
            question="What did the brave grown-up do?",
            answer=f"{parent.label_word.capitalize()} used a careful smothering move to stop the tiny flame. That kept the fire from growing and showed that bravery can be calm and quick.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended safely, with the fountain quiet again and the children using a safer kind of bravery. The last picture is of them together, calm and proud, with no fire left at all.",
        ),
    ]
    if f["outcome"] == "averted":
        qas.append(QAItem(
            question="What happened when the warning was obeyed?",
            answer=f"{child.id} listened, put the risky idea aside, and went to tell {parent.label_word} instead. No fire started, so the night stayed peaceful.",
        ))
    elif f["outcome"] == "contained":
        qas.append(QAItem(
            question="What happened when the spark caused trouble?",
            answer=f"The little flame touched the {haz.label}, but {parent.label_word} arrived in time and {resp.qa_text}. The fire stopped before it could spread.",
        ))
    else:
        qas.append(QAItem(
            question="Could the first rescue fix the fire?",
            answer=f"No, because {resp.fail}. The family still got out safely, but the garden needed the next day to mend the damage.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["temp"].tags) | set(world.facts["haz"].tags) | set(world.facts["resp"].tags)
    bank = {
        "fountain": QAItem("What is a fountain?", "A fountain is a place where water sprays up or flows gently for people to look at and enjoy."),
        "smother": QAItem("What does it mean to smother a small flame?", "To smother a flame means to cover it so it cannot get the air it needs. Then the flame goes out."),
        "bravery": QAItem("What is brave in a fire-safety story?", "Brave can mean calling for help right away and following a grown-up's safe directions."),
        "fire": QAItem("Why can fire be dangerous?", "Fire can grow quickly and hurt people or damage things, so it should be treated with care."),
    }
    out = []
    if "fountain" in tags:
        out.append(bank["fountain"])
    if "smother" in tags:
        out.append(bank["smother"])
    out.append(bank["bravery"])
    out.append(bank["fire"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
             "== (2) Story questions ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World-knowledge questions =="])
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "sparkler", "reeds", "smother_cloth", "Lily", "girl", "Tom", "boy", "mother", "cautious", 0, 6, 8, "siblings"),
    StoryParams("courtyard", "match", "paperboat", "smother_basket", "Mia", "girl", "Noah", "boy", "father", "careful", 0, 5, 7, "siblings"),
    StoryParams("park", "lantern", "fountain", "smother_towel", "Eli", "boy", "Ava", "girl", "mother", "watchful", 1, 6, 4, "friends"),
]


def explain_rejection(temp: Temptation, haz: Hazard) -> str:
    return f"(No story: {temp.label} near {haz.label} would not make a real danger here.)"


def valid_outcome(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.sibling_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay) else "burned"


def ASP_RULES = None
