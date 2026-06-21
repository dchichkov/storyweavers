#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/outlet_tobacco_rogue_rhyme_moral_value_nursery.py
==============================================================================

A standalone storyworld for a nursery-rhyme-flavored safety tale built from the
seed words: outlet, tobacco, rogue.

Tiny domain:
- A little rogue pet bats or rolls a grown-up's tobacco item near a wall outlet.
- A child is tempted to fetch it with a metal object.
- A wiser child warns about the outlet and the tobacco.
- Either the warning works (averted ending) or a tiny spark pops and a grown-up
  makes the scene safe.
- The ending turns the danger into a rhyme and a moral value: ask for help,
  and leave grown-up tobacco and wall outlets alone.

Run it
------
    python storyworlds/worlds/gpt-5.4/outlet_tobacco_rogue_rhyme_moral_value_nursery.py
    python storyworlds/worlds/gpt-5.4/outlet_tobacco_rogue_rhyme_moral_value_nursery.py --all
    python storyworlds/worlds/gpt-5.4/outlet_tobacco_rogue_rhyme_moral_value_nursery.py --trace
    python storyworlds/worlds/gpt-5.4/outlet_tobacco_rogue_rhyme_moral_value_nursery.py --qa --json
    python storyworlds/worlds/gpt-5.4/outlet_tobacco_rogue_rhyme_moral_value_nursery.py --verify
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    metal: bool = False
    tobacco: bool = False
    plugged: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal = {"kitten", "cat", "puppy", "dog", "magpie"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Rogue:
    id: str
    label: str
    phrase: str
    sound: str
    trail: str
    type: str = "kitten"
    tags: set[str] = field(default_factory=set)


@dataclass
class TobaccoItem:
    id: str
    label: str
    phrase: str
    roll_verb: str
    note: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Probe:
    id: str
    label: str
    phrase: str
    metallic: bool
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeFix:
    id: str
    label: str
    phrase: str
    sense: int
    steps: list[str] = field(default_factory=list)
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class VerseFrame:
    id: str
    opening: str
    ending: str
    moral_line: str


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
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]

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


def _r_shock_risk(world: World) -> list[str]:
    outlet = world.get("outlet")
    item = world.get("probe")
    tobacco = world.get("tobacco")
    if outlet.meters["tempted"] < THRESHOLD or not item.metallic or tobacco.meters["near_outlet"] < THRESHOLD:
        return []
    sig = ("shock_risk", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    outlet.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__risk__"]


def _r_spark(world: World) -> list[str]:
    outlet = world.get("outlet")
    if outlet.meters["contact"] < THRESHOLD or outlet.meters["powered"] < THRESHOLD <= 0:
        return []
    sig = ("spark", "outlet")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    outlet.meters["sparked"] += 1
    outlet.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__spark__"]


CAUSAL_RULES = [
    Rule(name="shock_risk", tag="physical", apply=_r_shock_risk),
    Rule(name="spark", tag="physical", apply=_r_spark),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(probe: Probe, tobacco: TobaccoItem) -> bool:
    return probe.metallic and "tobacco" in tobacco.tags


def sensible_fixes() -> list[SafeFix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > BRAVERY_INIT


def predict_spark(world: World) -> dict:
    sim = world.copy()
    _tempt_with_probe(sim, narrate=False)
    _touch_outlet(sim, narrate=False)
    return {
        "sparked": sim.get("outlet").meters["sparked"] >= THRESHOLD,
        "risk": sim.get("outlet").meters["risk"],
    }


def _tempt_with_probe(world: World, narrate: bool = True) -> None:
    outlet = world.get("outlet")
    outlet.meters["tempted"] += 1
    propagate(world, narrate=narrate)


def _touch_outlet(world: World, narrate: bool = True) -> None:
    outlet = world.get("outlet")
    outlet.meters["contact"] += 1
    propagate(world, narrate=narrate)


def couplet(a: str, b: str) -> str:
    return f"{a} {b}"


def setup_scene(world: World, verse: VerseFrame, instigator: Entity, helper: Entity,
                rogue: Rogue, tobacco: TobaccoItem) -> None:
    pet = world.get("rogue")
    tobacco_ent = world.get("tobacco")
    instigator.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(couplet(
        verse.opening,
        f"In a snug little room played {instigator.id} and {helper.id} together."
    ))
    world.say(couplet(
        f"By the chair sat {tobacco.phrase}, meant for grown-up hands alone.",
        f"Then {pet.phrase}, a rogue little rascal, came frisking with a pounce and a groan."
    ))
    tobacco_ent.meters["rolling"] += 1
    world.say(couplet(
        f'With a {rogue.sound}, it nudged the {tobacco.label} till it {tobacco.roll_verb}.',
        f"Soon it rested by the outlet, tucked where the shadows twirl and curl."
    ))
    tobacco_ent.meters["near_outlet"] += 1
    world.facts["moved_by_rogue"] = True


def notice_trouble(world: World, instigator: Entity, helper: Entity, probe: Probe,
                   tobacco: TobaccoItem) -> None:
    instigator.memes["desire"] += 1
    world.say(couplet(
        f'"Oh look," said {instigator.id}, "the {tobacco.label} is stuck by the wall so tight."',
        f'"I can fetch it with {probe.phrase} and make it come out into the light."'
    ))
    _tempt_with_probe(world)


def warning(world: World, helper: Entity, instigator: Entity, probe: Probe,
            tobacco: TobaccoItem, parent: Entity) -> None:
    pred = predict_spark(world)
    helper.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(couplet(
        f'{helper.id} shook {helper.pronoun("possessive")} head and spoke in a steady note,',
        f'"No, no, not by the outlet, and not with {probe.label}. That could make a spark and a frightful float."'
    ))
    world.say(couplet(
        f'"And {tobacco.note}," {helper.pronoun()} added, still gentle and clear.',
        f'"Let {parent.label_word} help us fetch it. A grown-up can do it from here."'
    ))


def defy(world: World, instigator: Entity, helper: Entity, probe: Probe) -> None:
    instigator.memes["defiance"] += 1
    world.say(couplet(
        f'"Just one poke," said {instigator.id}, brave and a little too quick.',
        f'{helper.id} reached out, but {instigator.id} still stepped toward the socket and stick.'
    ))


def back_down(world: World, instigator: Entity, helper: Entity, parent: Entity,
              verse: VerseFrame) -> None:
    instigator.memes["relief"] += 1
    helper.memes["relief"] += 1
    instigator.memes["lesson"] += 1
    world.say(couplet(
        f"Then {instigator.id} looked at {helper.id}, and the boldness slipped away.",
        f'"You are right," {instigator.pronoun()} whispered. "I will not poke there today."'
    ))
    world.say(couplet(
        f"They called for {parent.label_word}, who smiled and came at once with care.",
        verse.moral_line
    ))


def spark_event(world: World, instigator: Entity, probe: Probe) -> None:
    _touch_outlet(world)
    world.say(couplet(
        f"The {probe.label} gave one tiny tap, and pop! went a sharp blue spark.",
        f"{instigator.id} jumped back with a squeak, and the snug little room felt dark."
    ))


def adult_fix(world: World, parent: Entity, fix: SafeFix, verse: VerseFrame) -> None:
    outlet = world.get("outlet")
    tobacco = world.get("tobacco")
    for step in fix.steps:
        world.say(step.format(parent=parent.label_word.capitalize(), tobacco=tobacco.label))
    outlet.meters["powered"] = 0.0
    outlet.meters["risk"] = 0.0
    tobacco.meters["near_outlet"] = 0.0
    tobacco.meters["safe"] += 1
    world.say(couplet(
        f"Then {parent.label_word.capitalize()} set the {tobacco.label} high where little hands could not roam.",
        verse.ending
    ))


def lesson(world: World, parent: Entity, instigator: Entity, helper: Entity,
           tobacco: TobaccoItem, verse: VerseFrame) -> None:
    for kid in (instigator, helper):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(couplet(
        f'{parent.label_word.capitalize()} knelt and held them close, all warm from cheek to chin.',
        f'"An outlet is not for poking, and tobacco is not for children."'
    ))
    world.say(couplet(
        '"When something unsafe rolls where little fingers should not be,"',
        verse.moral_line
    ))


def closing_image(world: World, instigator: Entity, helper: Entity, rogue: Rogue) -> None:
    rogue_ent = world.get("rogue")
    rogue_ent.memes["calm"] += 1
    world.say(couplet(
        f"Later the rogue little {rogue.label} chased a spool instead of trouble by the wall.",
        f"{instigator.id} and {helper.id} sang a safer rhyme, and that was best of all."
    ))


def tell(verse: VerseFrame, rogue: Rogue, tobacco: TobaccoItem, probe: Probe, fix: SafeFix,
         instigator_name: str = "Molly", instigator_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         parent_type: str = "mother", trait: str = "careful",
         relation: str = "siblings", instigator_age: int = 4, helper_age: int = 6) -> World:
    world = World()
    instigator = world.add(Entity(
        id=instigator_name,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[trait],
        age=helper_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="rogue",
        type=rogue.type,
        label=rogue.label,
        phrase=rogue.phrase,
        role="rogue",
        tags=set(rogue.tags),
    ))
    world.add(Entity(
        id="tobacco",
        type="tobacco_item",
        label=tobacco.label,
        phrase=tobacco.phrase,
        role="tobacco",
        tobacco=True,
        tags=set(tobacco.tags),
    ))
    world.add(Entity(
        id="probe",
        type="tool",
        label=probe.label,
        phrase=probe.phrase,
        metal=probe.metallic,
        tags=set(probe.tags),
    ))
    world.add(Entity(
        id="outlet",
        type="outlet",
        label="outlet",
        phrase="the wall outlet",
        role="hazard",
        plugged=True,
    ))
    world.get("outlet").meters["powered"] = 1.0

    setup_scene(world, verse, instigator, helper, rogue, tobacco)

    world.para()
    notice_trouble(world, instigator, helper, probe, tobacco)
    warning(world, helper, instigator, probe, tobacco, parent)

    averted = would_avert(relation, instigator_age, helper_age, trait)
    if averted:
        back_down(world, instigator, helper, parent, verse)
        world.para()
        closing_image(world, instigator, helper, rogue)
        outcome = "averted"
    else:
        defy(world, instigator, helper, probe)
        world.para()
        spark_event(world, instigator, probe)
        world.para()
        adult_fix(world, parent, fix, verse)
        lesson(world, parent, instigator, helper, tobacco, verse)
        world.para()
        closing_image(world, instigator, helper, rogue)
        outcome = "sparked"

    world.facts.update(
        verse=verse,
        rogue_cfg=rogue,
        tobacco_cfg=tobacco,
        probe_cfg=probe,
        fix_cfg=fix,
        instigator=instigator,
        helper=helper,
        parent=parent,
        relation=relation,
        outcome=outcome,
        sparked=world.get("outlet").meters["sparked"] >= THRESHOLD,
        averted=averted,
    )
    return world


ROGUES = {
    "kitten": Rogue(
        id="kitten",
        label="kitten",
        phrase="a rogue gray kitten",
        sound="pitter-pat",
        trail="tail high and whiskers wide",
        type="kitten",
        tags={"pet", "rogue"},
    ),
    "puppy": Rogue(
        id="puppy",
        label="puppy",
        phrase="a rogue brown puppy",
        sound="skitter-scrabble",
        trail="ears flopping side to side",
        type="puppy",
        tags={"pet", "rogue"},
    ),
    "magpie": Rogue(
        id="magpie",
        label="magpie",
        phrase="a rogue black-and-white magpie",
        sound="clack-clack",
        trail="wings tucked in a shiny glide",
        type="magpie",
        tags={"bird", "rogue"},
    ),
}

TOBACCO_ITEMS = {
    "tin": TobaccoItem(
        id="tin",
        label="tobacco tin",
        phrase="a round tobacco tin",
        roll_verb="rolled with a bright little ring",
        note="tobacco belongs to grown-ups and should never be touched for play",
        tags={"tobacco"},
    ),
    "pouch": TobaccoItem(
        id="pouch",
        label="tobacco pouch",
        phrase="a soft tobacco pouch",
        roll_verb="slid and bumped with a wrinkly swing",
        note="tobacco belongs to grown-ups and should never be touched for play",
        tags={"tobacco"},
    ),
    "case": TobaccoItem(
        id="case",
        label="tobacco case",
        phrase="a small tobacco case",
        roll_verb="clinked and skated with a silvery ring",
        note="tobacco belongs to grown-ups and should never be touched for play",
        tags={"tobacco"},
    ),
}

PROBES = {
    "fork": Probe(
        id="fork",
        label="a fork",
        phrase="a shiny fork",
        metallic=True,
        sense=1,
        tags={"metal", "outlet"},
    ),
    "spoon": Probe(
        id="spoon",
        label="a spoon",
        phrase="a long metal spoon",
        metallic=True,
        sense=1,
        tags={"metal", "outlet"},
    ),
    "key": Probe(
        id="key",
        label="a key",
        phrase="a little brass key",
        metallic=True,
        sense=1,
        tags={"metal", "outlet"},
    ),
    "wooden_spoon": Probe(
        id="wooden_spoon",
        label="a wooden spoon",
        phrase="a wooden spoon",
        metallic=False,
        sense=3,
        tags={"wood"},
    ),
}

FIXES = {
    "unplug_and_lift": SafeFix(
        id="unplug_and_lift",
        label="unplug and lift",
        phrase="unplug the lamp and lift the item safely away",
        sense=3,
        steps=[
            "{parent} first unplugged the lamp beside the outlet, calm and slow as a song.",
            "{parent} used dry wooden tongs to lift the {tobacco} free and carry it along.",
        ],
        qa_text="unplugged the nearby lamp first and used dry wooden tongs to lift the item away",
        tags={"outlet", "adult_help"},
    ),
    "switch_and_sweep": SafeFix(
        id="switch_and_sweep",
        label="switch off and sweep",
        phrase="switch off the power and sweep the item away with a broom",
        sense=3,
        steps=[
            "{parent} switched off the power for that little corner before anyone went near.",
            "{parent} used a dry broom to sweep the {tobacco} out, steady and clear.",
        ],
        qa_text="switched off the power first and swept the item away with a dry broom",
        tags={"outlet", "adult_help"},
    ),
    "call_only": SafeFix(
        id="call_only",
        label="call for help",
        phrase="call a grown-up and wait",
        sense=2,
        steps=[
            "{parent} came at once, kept little feet back, and made the corner safe before touching a thing.",
            "{parent} moved the {tobacco} away only after the power there was safely managed.",
        ],
        qa_text="came quickly, kept the children back, and made the corner safe before moving the item",
        tags={"adult_help"},
    ),
}

VERSES = {
    "cottage": VerseFrame(
        id="cottage",
        opening="Hush-a-bye, bright little day, with a hum in the window weather.",
        ending="Then laughter came back to the room, soft and sweet as home.",
        moral_line="So call a grown-up, wait your turn, and let safe hands set things right.",
    ),
    "lamplight": VerseFrame(
        id="lamplight",
        opening="Tinkle, twinkle, lamplight mild, warm upon the floor.",
        ending="The room felt kind again at last, and no one feared the wall.",
        moral_line="Ask for help and step away; that is the brave thing, after all.",
    ),
}

GIRL_NAMES = ["Molly", "Lily", "Nora", "Ada", "Elsie", "Poppy", "May"]
BOY_NAMES = ["Ben", "Tom", "Owen", "Leo", "Finn", "Jack", "Theo"]
TRAITS = ["careful", "cautious", "sensible", "gentle", "curious", "bold"]


@dataclass
class StoryParams:
    verse: str
    rogue: str
    tobacco_item: str
    probe: str
    fix: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 4
    helper_age: int = 6
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for verse_id in VERSES:
        for rogue_id in ROGUES:
            for tobacco_id, tobacco in TOBACCO_ITEMS.items():
                for probe_id, probe in PROBES.items():
                    for fix_id, fix in FIXES.items():
                        if hazard_at_risk(probe, tobacco) and fix.sense >= SENSE_MIN:
                            combos.append((verse_id, rogue_id, tobacco_id, probe_id, fix_id))
    return combos


KNOWLEDGE = {
    "outlet": [
        (
            "What is an outlet?",
            "An outlet is the place in a wall where plugs go to get electricity. Children should never poke fingers or tools into it."
        )
    ],
    "tobacco": [
        (
            "What is tobacco?",
            "Tobacco is a grown-up substance that children should not touch or use. If a child finds some, the safe choice is to tell a grown-up."
        )
    ],
    "rogue": [
        (
            "What does rogue mean in this story?",
            "Here rogue means playful and mischievous, like a pet that causes trouble without meaning to. It does not mean the pet is bad at heart."
        )
    ],
    "electricity": [
        (
            "Why is it dangerous to put metal near an outlet?",
            "Metal can carry electricity. That can cause a shock or a spark very quickly."
        )
    ],
    "adult_help": [
        (
            "What should a child do if something unsafe is near an outlet?",
            "Step back and call a grown-up. Waiting for safe help is the brave choice."
        )
    ],
}


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    instigator = f["instigator"]
    helper = f["helper"]
    tobacco = f["tobacco_cfg"]
    probe = f["probe_cfg"]
    outcome = f["outcome"]
    prompts = [
        'Write a nursery-rhyme style safety story for a 3-to-5-year-old that includes the words "outlet", "tobacco", and "rogue".',
        f"Tell a rhyming moral tale where a rogue pet sends a {tobacco.label} near an outlet and {helper.id} warns {instigator.id} not to use {probe.label}.",
    ]
    if outcome == "averted":
        prompts.append(
            "Write a gentle rhyming story where the wiser child stops the unsafe plan before anything touches the outlet, and end with a clear moral value about asking for help."
        )
    else:
        prompts.append(
            "Write a nursery rhyme with a tiny spark, a calm grown-up rescue, and a moral ending that teaches children to leave outlets and tobacco alone."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    instigator = f["instigator"]
    helper = f["helper"]
    parent = f["parent"]
    tobacco = f["tobacco_cfg"]
    probe = f["probe_cfg"]
    fix = f["fix_cfg"]
    relation = f["relation"]
    pair = pair_noun(instigator, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {instigator.id} and {helper.id}, a rogue little {f['rogue_cfg'].label}, and their {parent.label_word}. The trouble begins when the pet moves a {tobacco.label} near an outlet."
        ),
        (
            "What did the rogue pet do?",
            f"The rogue little {f['rogue_cfg'].label} knocked the {tobacco.label} until it ended up by the outlet. That turn in the world is what made the children notice the danger."
        ),
        (
            f"Why did {helper.id} tell {instigator.id} to stop?",
            f"{helper.id} knew the outlet was dangerous and that {probe.label} was metal. {helper.pronoun().capitalize()} also knew the {tobacco.label} was not for children to play with."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {helper.id} warned {instigator.id}?",
                f"{instigator.id} listened and stepped back, so no spark happened at all. Then they called {parent.label_word} to handle the trouble safely."
            )
        )
    else:
        qa.append(
            (
                "What happened when the probe touched near the outlet?",
                f"A tiny spark popped, and {instigator.id} jumped back. The spark showed how quickly an unsafe idea can turn scary."
            )
        )
        qa.append(
            (
                f"How did the grown-up fix the problem?",
                f"{parent.label_word.capitalize()} {fix.qa_text}. The calm method made the corner safe before the children went near again."
            )
        )
    qa.append(
        (
            "What is the moral value of the story?",
            "The moral is to step back from danger and ask a grown-up for help. It also teaches that tobacco and outlets are not things for children to touch."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = {"outlet", "tobacco", "rogue", "electricity", "adult_help"}
    for tag in ["outlet", "tobacco", "rogue", "electricity", "adult_help"]:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("metal", e.metal), ("tobacco", e.tobacco), ("plugged", e.plugged)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        verse="cottage",
        rogue="kitten",
        tobacco_item="tin",
        probe="fork",
        fix="unplug_and_lift",
        instigator="Molly",
        instigator_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=4,
        helper_age=6,
    ),
    StoryParams(
        verse="lamplight",
        rogue="puppy",
        tobacco_item="pouch",
        probe="spoon",
        fix="switch_and_sweep",
        instigator="Tom",
        instigator_gender="boy",
        helper="Lily",
        helper_gender="girl",
        parent="father",
        trait="cautious",
        relation="friends",
        instigator_age=5,
        helper_age=5,
    ),
    StoryParams(
        verse="cottage",
        rogue="magpie",
        tobacco_item="case",
        probe="key",
        fix="call_only",
        instigator="Ada",
        instigator_gender="girl",
        helper="Nora",
        helper_gender="girl",
        parent="mother",
        trait="gentle",
        relation="siblings",
        instigator_age=4,
        helper_age=7,
    ),
]


def explain_rejection(probe: Probe, tobacco: TobaccoItem, fix: Optional[SafeFix] = None) -> str:
    if not probe.metallic:
        return (
            f"(No story: {probe.label} is not a metal tool, so the outlet danger is too weak for this world. "
            f"Pick a metal object like a fork, spoon, or key.)"
        )
    if "tobacco" not in tobacco.tags:
        return "(No story: this item is not modeled as tobacco, so the seed premise is missing.)"
    if fix is not None and fix.sense < SENSE_MIN:
        return (
            f"(No story: the fix '{fix.id}' is below the common-sense threshold for this world. "
            f"Pick a calmer grown-up safety method.)"
        )
    return "(No story: this combination does not make the intended outlet-and-tobacco hazard.)"


ASP_RULES = r"""
hazard(P, T) :- probe(P), metallic(P), tobacco_item(T), is_tobacco(T).
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(V, R, T, P, F) :- verse(V), rogue(R), tobacco_item(T), probe(P), fix(F),
                        hazard(P, T), sensible_fix(F).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
helper_older :- relation(siblings), instigator_age(IA), helper_age(HA), HA > IA.
bonus(3) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(sparked) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for verse_id in VERSES:
        lines.append(asp.fact("verse", verse_id))
    for rogue_id in ROGUES:
        lines.append(asp.fact("rogue", rogue_id))
    for tobacco_id in TOBACCO_ITEMS:
        lines.append(asp.fact("tobacco_item", tobacco_id))
        lines.append(asp.fact("is_tobacco", tobacco_id))
    for probe_id, probe in PROBES.items():
        lines.append(asp.fact("probe", probe_id))
        if probe.metallic:
            lines.append(asp.fact("metallic", probe_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.helper_age, params.trait):
        return "averted"
    return "sparked"


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected parameter resolution failure at seed {seed}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome cases differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme safety world: a rogue pet, a tobacco item, an outlet, and a moral ending."
    )
    ap.add_argument("--verse", choices=VERSES)
    ap.add_argument("--rogue", choices=ROGUES)
    ap.add_argument("--tobacco-item", dest="tobacco_item", choices=TOBACCO_ITEMS)
    ap.add_argument("--probe", choices=PROBES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.probe is not None and not PROBES[args.probe].metallic:
        raise StoryError(explain_rejection(PROBES[args.probe], next(iter(TOBACCO_ITEMS.values()))))
    if args.fix is not None and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(next(iter(PROBES.values())), next(iter(TOBACCO_ITEMS.values())), FIXES[args.fix]))
    if args.probe is not None and args.tobacco_item is not None:
        probe = PROBES[args.probe]
        tobacco = TOBACCO_ITEMS[args.tobacco_item]
        if not hazard_at_risk(probe, tobacco):
            raise StoryError(explain_rejection(probe, tobacco))

    combos = [
        combo for combo in valid_combos()
        if (args.verse is None or combo[0] == args.verse)
        and (args.rogue is None or combo[1] == args.rogue)
        and (args.tobacco_item is None or combo[2] == args.tobacco_item)
        and (args.probe is None or combo[3] == args.probe)
        and (args.fix is None or combo[4] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    verse_id, rogue_id, tobacco_id, probe_id, fix_id = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=instigator)
    relation = args.relation or rng.choice(["siblings", "friends"])
    instigator_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        verse=verse_id,
        rogue=rogue_id,
        tobacco_item=tobacco_id,
        probe=probe_id,
        fix=fix_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        verse = VERSES[params.verse]
        rogue = ROGUES[params.rogue]
        tobacco = TOBACCO_ITEMS[params.tobacco_item]
        probe = PROBES[params.probe]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not hazard_at_risk(probe, tobacco):
        raise StoryError(explain_rejection(probe, tobacco))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_rejection(probe, tobacco, fix))

    world = tell(
        verse=verse,
        rogue=rogue,
        tobacco=tobacco,
        probe=probe,
        fix=fix,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        helper_age=params.helper_age,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (verse, rogue, tobacco_item, probe, fix) combos:\n")
        for verse_id, rogue_id, tobacco_id, probe_id, fix_id in combos:
            print(f"  {verse_id:10} {rogue_id:8} {tobacco_id:8} {probe_id:8} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.helper}: {p.rogue}, {p.tobacco_item}, {p.probe} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
