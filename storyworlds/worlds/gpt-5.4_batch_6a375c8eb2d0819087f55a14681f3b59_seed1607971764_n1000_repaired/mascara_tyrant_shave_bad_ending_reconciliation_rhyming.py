#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mascara_tyrant_shave_bad_ending_reconciliation_rhyming.py
====================================================================================

A standalone story world about two children preparing a little rhyming play.
One child wants to look like a pretend tyrant and reaches for a grown-up's
mascara to draw the costume onto a real face. A wiser child warns about the
smear and the sting. Depending on who listens, how fast help comes, and which
cleanup method is chosen, the story can end in an averted near-miss, a rescued
performance, or a sad missed show. In every branch, reconciliation matters.

The style stays close to a rhyming story: the prose is written in short,
musical lines, but the story still comes from simulated state instead of a
single frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/mascara_tyrant_shave_bad_ending_reconciliation_rhyming.py
    python storyworlds/worlds/gpt-5.4/mascara_tyrant_shave_bad_ending_reconciliation_rhyming.py --need beard --safe-prop sticker_brows
    python storyworlds/worlds/gpt-5.4/mascara_tyrant_shave_bad_ending_reconciliation_rhyming.py --cleanup tissue
    python storyworlds/worlds/gpt-5.4/mascara_tyrant_shave_bad_ending_reconciliation_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/mascara_tyrant_shave_bad_ending_reconciliation_rhyming.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "gentle", "patient", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Stage:
    id: str
    place: str
    scene_line: str
    chorus_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Need:
    id: str
    desire: str
    mark_text: str
    rhyme_line: str
    severity: int
    near_eyes: bool
    covered_by: set[str]
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class SafeProp:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fit_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Cleanup:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    costume = world.get("costume")
    need = world.facts["need_cfg"]
    if child.meters["mascara"] < THRESHOLD:
        return out
    sig = ("smear", need.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    costume.meters["smudged"] += 1
    child.memes["embarrassment"] += 1
    world.get("cautioner").memes["worry"] += 1
    if need.near_eyes:
        child.meters["sting"] += 1
    out.append("__smear__")
    return out


def _r_workload(world: World) -> list[str]:
    costume = world.get("costume")
    parent = world.get("parent")
    if costume.meters["smudged"] < THRESHOLD:
        return []
    sig = ("workload", costume.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parent.meters["workload"] += 1
    return ["__work__"]


CAUSAL_RULES = [
    Rule(name="smear", tag="physical", apply=_r_smear),
    Rule(name="workload", tag="physical", apply=_r_workload),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_combo(need: Need, safe_prop: SafeProp) -> bool:
    return need.id in safe_prop.covers


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for need_id, need in NEEDS.items():
        for prop_id, prop in SAFE_PROPS.items():
            if valid_combo(need, prop):
                combos.append((need_id, prop_id))
    return combos


def sensible_cleanups() -> list[Cleanup]:
    return [c for c in CLEANUPS.values() if c.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def mess_severity(need: Need, delay: int) -> int:
    return need.severity + delay


def is_cleaned(cleanup: Cleanup, need: Need, delay: int) -> bool:
    return cleanup.power >= mess_severity(need, delay)


def explain_rejection(need: Need, safe_prop: SafeProp) -> str:
    covers = ", ".join(sorted(safe_prop.covers))
    return (
        f"(No story: {safe_prop.label} does not solve the costume need '{need.id}'. "
        f"It works for {covers}, but this child wants {need.desire}. "
        f"Pick a prop that truly matches the pretend tyrant look.)"
    )


def explain_cleanup(cid: str) -> str:
    cleanup = CLEANUPS[cid]
    better = ", ".join(sorted(c.id for c in sensible_cleanups()))
    return (
        f"(Refusing cleanup '{cid}': it scores too low on common sense "
        f"(sense={cleanup.sense} < {SENSE_MIN}). Try a calmer, more effective "
        f"cleanup like {better}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    cleaned = is_cleaned(CLEANUPS[params.cleanup], NEEDS[params.need], params.delay)
    return "cleaned" if cleaned else "missed"


def predict_smear(world: World) -> dict:
    sim = world.copy()
    _do_mascara(sim, narrate=False)
    child = sim.get("instigator")
    costume = sim.get("costume")
    parent = sim.get("parent")
    return {
        "smudged": costume.meters["smudged"] >= THRESHOLD,
        "sting": child.meters["sting"] >= THRESHOLD,
        "workload": parent.meters["workload"],
    }


def play_setup(world: World, stage: Stage, a: Entity, b: Entity, need: Need) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In {stage.place}, where soft words loved to sing, "
        f"{a.id} and {b.id} built a stage for a cardboard king."
    )
    world.say(stage.scene_line)
    world.say(
        f'"I will be the tyrant tonight," laughed {a.id}, "with a rumble and a ring. '
        f'I need {need.desire}, the boldest thing!"'
    )
    world.say(
        "They had a paper crown, a cape to swish, and boots made from a boxy thing; "
        "for a make-believe beard, no child should scrub or shave a thing."
    )


def temptation(world: World, a: Entity) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"Then {a.id} saw mascara on the dresser ledge, black as a rook's wing. "
        f'"Just one quick swipe," {a.pronoun()} said, "and I shall look fierce enough to sting."'
    )


def warning(world: World, b: Entity, a: Entity, parent: Entity, need: Need, safe_prop: SafeProp) -> None:
    pred = predict_smear(world)
    b.memes["caution"] += 1
    world.facts["predicted_smudged"] = pred["smudged"]
    world.facts["predicted_sting"] = pred["sting"]
    world.facts["predicted_workload"] = pred["workload"]
    sting_line = " It might creep too near your eyes and sting." if pred["sting"] else ""
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "Mascara is for grown-up faces, not our playtime fling. '
        f'If you draw with it, it can smear on your collar and make a sorry ring.{sting_line} '
        f'Let us use {safe_prop.phrase} instead and keep the rhyme-play bright as spring."'
    )
    world.say(
        f'{parent.label_word.capitalize()} had said that costume fun should use safe things, '
        f'not borrowed makeup that brings a cling.'
    )


def back_down(world: World, a: Entity, b: Entity, safe_prop: SafeProp, stage: Stage) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["apology"] += 1
    b.memes["forgiveness"] += 1
    world.say(
        f'{a.id} looked at the mascara, then at {b.id}, and the boast grew small and thin. '
        f'"You are right," {a.pronoun()} sighed. "A tyrant on stage should not begin with borrowed grown-up skin."'
    )
    world.say(
        f"They clipped on {safe_prop.phrase} instead, and the pretend tyrant wore a safer grin. "
        f'{stage.chorus_line}'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Only a tiny line," said {a.id}, though {b.id} had pleaded not to begin. '
        f'Quick as a wink, {a.pronoun()} reached for the wand with a mischievous chin.'
    )


def _do_mascara(world: World, narrate: bool = True) -> None:
    child = world.get("instigator")
    need = world.facts["need_cfg"]
    child.meters["mascara"] += 1
    child.meters["look_done"] += 1
    if need.near_eyes:
        child.meters["near_eyes"] += 1
    propagate(world, narrate=narrate)


def apply_mascara(world: World, a: Entity, need: Need) -> None:
    _do_mascara(world, narrate=False)
    costume = world.get("costume")
    sting_line = " The black bit crept too close, and one eye gave a watery blink." if a.meters["sting"] >= THRESHOLD else ""
    smear_line = (
        f" A dark thumb brushed the collar too, and the clean cloth took a gloomy ink."
        if costume.meters["smudged"] >= THRESHOLD
        else ""
    )
    world.say(
        f"{a.id} painted {need.mark_text} with mascara, proud for half a blink.{sting_line}{smear_line}"
    )


def alarm(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    if a.meters["sting"] >= THRESHOLD:
        world.say(
            f'"Ow!" cried {a.id}. "{b.id}, it stings!" and all the brave drums shrank to a clink.'
        )
    else:
        world.say(
            f'{b.id} stared at the smudge and cried, "Call {parent.label_word}! This is worse than you think!"'
        )


def cleanup_success(world: World, parent: Entity, cleanup: Cleanup, need: Need) -> None:
    child = world.get("instigator")
    costume = world.get("costume")
    child.meters["mascara"] = 0.0
    child.meters["sting"] = 0.0
    costume.meters["smudged"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came with a calm warm voice and {cleanup.text}. "
        "Bit by bit the black came away, not with a scrape, not with a shave, but with patient care."
    )


def cleanup_fail(world: World, parent: Entity, cleanup: Cleanup) -> None:
    child = world.get("instigator")
    costume = world.get("costume")
    child.memes["sadness"] += 1
    child.memes["embarrassment"] += 1
    costume.meters["stained"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {cleanup.fail}. "
        "But the mark had sat too long, and the rhyme-time bell would not wait there."
    )


def missed_show(world: World, stage: Stage, a: Entity, b: Entity) -> None:
    a.memes["loss"] += 1
    b.memes["loss"] += 1
    world.say(
        f"The little show began without them. In {stage.place}, the empty crown looked small and bare. "
        f"{a.id} sat in socks by the doorway, and even the cape forgot to flare."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, safe_prop: SafeProp) -> None:
    a.memes["apology"] += 1
    b.memes["forgiveness"] += 1
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt between them. "Costumes are for play," '
        f'{parent.pronoun()} said, "but mascara is not a toy to wear. '
        f'If you want a beard or tyrant glare, we choose a safe prop and we share."'
    )
    world.say(
        f'{a.id} whispered, "I should have listened." {b.id} answered, "Come stand by me there." '
        f'Together they reached for {safe_prop.phrase}, gentle and fair.'
    )


def reconciliation(world: World, a: Entity, b: Entity, safe_prop: SafeProp, stage: Stage, made_show: bool) -> None:
    a.memes["reconciled"] += 1
    b.memes["reconciled"] += 1
    if made_show:
        world.say(
            f"Then hand found hand, and frown found cheer. {a.id} let {b.id} straighten the crown with care. "
            f'Wearing {safe_prop.phrase}, the would-be tyrant stomped on stage in silly air. '
            f"{safe_prop.ending_line} {stage.ending_image}"
        )
    else:
        world.say(
            f"Though the show was gone, the storm was not. {b.id} sat close, and {a.id} scooted there. "
            f'They made a new soft rhyme at home with {safe_prop.phrase}, and no one tried to shave or glare. '
            f"{stage.ending_image}"
        )


def tell(
    stage: Stage,
    need: Need,
    safe_prop: SafeProp,
    cleanup: Cleanup,
    *,
    instigator: str = "Tess",
    instigator_gender: str = "girl",
    cautioner: str = "Ned",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    costume = world.add(Entity(
        id="costume",
        kind="thing",
        type="costume",
        label="cape collar",
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    world.facts.update(
        stage_cfg=stage,
        need_cfg=need,
        safe_prop_cfg=safe_prop,
        cleanup_cfg=cleanup,
        instigator=a,
        cautioner=b,
        parent=parent,
        costume=costume,
        relation=relation,
        delay=delay,
    )

    play_setup(world, stage, a, b, need)
    world.para()
    temptation(world, a)
    warning(world, b, a, parent, need, safe_prop)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, safe_prop, stage)
        outcome = "averted"
        cleaned = True
        made_show = True
    else:
        defy(world, a, b)
        world.para()
        apply_mascara(world, a, need)
        alarm(world, a, b, parent)
        cleaned = is_cleaned(cleanup, need, delay)
        world.para()
        if cleaned:
            cleanup_success(world, parent, cleanup, need)
            lesson(world, parent, a, b, safe_prop)
            world.para()
            reconciliation(world, a, b, safe_prop, stage, made_show=True)
            outcome = "cleaned"
            made_show = True
        else:
            cleanup_fail(world, parent, cleanup)
            missed_show(world, stage, a, b)
            lesson(world, parent, a, b, safe_prop)
            world.para()
            reconciliation(world, a, b, safe_prop, stage, made_show=False)
            outcome = "missed"
            made_show = False

    world.facts.update(
        averted=averted,
        cleaned=cleaned,
        made_show=made_show,
        outcome=outcome,
        severity=mess_severity(need, delay) if not averted else 0,
        promised=True,
    )
    return world


STAGES = {
    "bedroom": Stage(
        id="bedroom",
        place="the bedroom",
        scene_line="A blanket became a red road, a stool became a throne, and a spoon tapped time like a little bell's ring.",
        chorus_line="Soon the throne was ready, the rhyme was steady, and the room felt light as spring.",
        ending_image="At the end, the blanket throne looked less like a bully's chair and more like a place for sharing.",
        tags={"bedroom", "play"},
    ),
    "hall": Stage(
        id="hall",
        place="the front hall",
        scene_line="A shoe rack became a castle gate, and the mirror flashed back every practicing swing.",
        chorus_line="Soon the hallway hummed with tapping feet and a brave pretend king.",
        ending_image="At the end, the mirror showed two smiling faces where one had wanted to rule everything.",
        tags={"hall", "play"},
    ),
    "kitchen": Stage(
        id="kitchen",
        place="the kitchen",
        scene_line="A chair wore a tea towel banner, and a wooden spoon drummed a pudding-bowl ring.",
        chorus_line="Soon even the kettle seemed to listen for the children's rhyme to sing.",
        ending_image="At the end, the tea towel banner hung crooked but cheerful above their sharing.",
        tags={"kitchen", "play"},
    ),
}

NEEDS = {
    "beard": Need(
        id="beard",
        desire="a dark beard for the tyrant",
        mark_text="a curling beard over lip and chin",
        rhyme_line="beard",
        severity=2,
        near_eyes=False,
        covered_by={"felt_beard", "tyrant_mask"},
        tags={"beard"},
    ),
    "brows": Need(
        id="brows",
        desire="fierce brows for the tyrant",
        mark_text="two stormy brows above the eyes",
        rhyme_line="brows",
        severity=2,
        near_eyes=True,
        covered_by={"sticker_brows", "tyrant_mask"},
        tags={"brows"},
    ),
    "both": Need(
        id="both",
        desire="a beard and fierce brows for the tyrant",
        mark_text="a beard and two stormy brows all at once",
        rhyme_line="beard and brows",
        severity=3,
        near_eyes=True,
        covered_by={"tyrant_mask"},
        tags={"beard", "brows"},
    ),
}

SAFE_PROPS = {
    "felt_beard": SafeProp(
        id="felt_beard",
        label="felt beard",
        phrase="a felt beard on an elastic string",
        covers={"beard"},
        fit_line="It gives the chin a beard without borrowing a grown-up thing.",
        ending_line="The felt beard bobbed when the child spoke, turning the tyrant grandly silly.",
        tags={"felt_beard", "costume"},
    ),
    "sticker_brows": SafeProp(
        id="sticker_brows",
        label="sticker brows",
        phrase="two peel-and-stick eyebrows",
        covers={"brows"},
        fit_line="They make a grumpy look without smearing the skin.",
        ending_line="The sticker brows sat crooked and funny, and even the tyrant could not stay chilly.",
        tags={"sticker_brows", "costume"},
    ),
    "tyrant_mask": SafeProp(
        id="tyrant_mask",
        label="tyrant mask",
        phrase="a paper tyrant mask with yarn beard and thick drawn brows",
        covers={"beard", "brows", "both"},
        fit_line="It covers the whole pretend look from a safe paper grin.",
        ending_line="The paper tyrant mask bounced with each rhyme, more clown than chilly.",
        tags={"tyrant_mask", "costume"},
    ),
}

CLEANUPS = {
    "wipes": Cleanup(
        id="wipes",
        sense=3,
        power=4,
        text="used soft makeup wipes and a warm cloth until the smudge grew faint and then disappeared",
        fail="used soft makeup wipes and a warm cloth, but the mascara had already spread and stained the collar",
        qa_text="used soft makeup wipes and a warm cloth to clean the mascara away",
        tags={"cleanup", "wipes"},
    ),
    "soap_cloth": Cleanup(
        id="soap_cloth",
        sense=3,
        power=3,
        text="used a little soap on a warm washcloth and dabbed instead of rubbing",
        fail="used a warm soapy cloth, but the mark had dried and the cleanup took too long",
        qa_text="dabbed the mascara away with a warm soapy cloth",
        tags={"cleanup", "soap"},
    ),
    "tissue": Cleanup(
        id="tissue",
        sense=1,
        power=1,
        text="rubbed with a dry tissue",
        fail="rubbed with a dry tissue, which only smeared the black farther",
        qa_text="rubbed at it with a dry tissue",
        tags={"cleanup", "tissue"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Tess", "Ava", "Nora", "June", "Ella", "Poppy"]
BOY_NAMES = ["Ben", "Max", "Ned", "Leo", "Finn", "Theo", "Sam", "Eli"]
TRAITS = ["careful", "gentle", "patient", "sensible", "curious", "bright"]


@dataclass
class StoryParams:
    stage: str
    need: str
    safe_prop: str
    cleanup: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "mascara": [(
        "What is mascara?",
        "Mascara is a grown-up makeup used on eyelashes. It is not for pretend play, because it can smear and bother eyes."
    )],
    "tyrant": [(
        "What is a tyrant in a pretend story?",
        "A tyrant is a bossy ruler who wants to control everyone. In pretend play, children can act one out safely without copying mean behavior for real."
    )],
    "shave": [(
        "What does shave mean?",
        "To shave means to cut hair very close to the skin with a razor. Razors are grown-up tools and should not be used for costume games."
    )],
    "wipes": [(
        "What are makeup wipes for?",
        "Makeup wipes help lift makeup off skin gently. A grown-up can use them carefully so rubbing does not spread the mess."
    )],
    "soap": [(
        "Why can a warm washcloth help with a smear?",
        "Warm water and a little soap can loosen a sticky mark. Gentle dabbing works better than hard rubbing."
    )],
    "costume": [(
        "Why are costume pieces safer than real makeup for little kids?",
        "A costume piece sits on top of clothes or skin instead of soaking in. That makes it easier to remove and less likely to sting or smear."
    )],
    "apology": [(
        "What does an apology do?",
        "An apology shows that someone knows they made a hurtful or unsafe choice. It helps people begin to trust each other again."
    )],
}
KNOWLEDGE_ORDER = ["mascara", "tyrant", "shave", "wipes", "soap", "costume", "apology"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def child_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = child_name(f["instigator"])
    b = child_name(f["cautioner"])
    stage = f["stage_cfg"]
    need = f["need_cfg"]
    prop = f["safe_prop_cfg"]
    outcome = f["outcome"]
    base = (
        'Write a rhyming story for a 3-to-5-year-old that includes the words '
        '"mascara", "tyrant", and "shave".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story in {stage.place} where {a} wants {need.desire}, "
            f"but {b} talks {f['instigator'].pronoun('object')} out of using mascara and they choose {prop.phrase} instead.",
            "Write a child-facing rhyming story where a costume problem is solved before anything messy happens, and the ending shows the children sharing safely.",
        ]
    if outcome == "missed":
        return [
            base,
            f"Tell a sad rhyming story where {a} ignores a warning, uses mascara for a pretend tyrant look, misses the little show, and then reconciles with {b}.",
            "Write a cautionary rhyming story with a bad ending that still includes apology and reconciliation.",
        ]
    return [
        base,
        f"Tell a rhyming story where {a} uses mascara for a pretend tyrant look, a calm grown-up cleans it up, and the children reconcile before the show.",
        f"Write a musical story that turns a messy costume mistake into a safer ending with {prop.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    stage = f["stage_cfg"]
    need = f["need_cfg"]
    prop = f["safe_prop_cfg"]
    cleanup = f["cleanup_cfg"]
    pair = pair_noun(a, b, f["relation"])
    an = child_name(a)
    bn = child_name(b)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {an} and {bn}, making a little rhyming show in {stage.place}. "
            f"Their {pw} matters too, because a grown-up helps when the costume trouble begins."
        ),
        (
            f"Why did {an} want mascara?",
            f"{an} wanted to look like a pretend tyrant and thought mascara would quickly make {need.desire}. "
            f"The wish came from the costume plan, not from needing real makeup."
        ),
        (
            f"What warning did {bn} give?",
            f"{bn} warned that mascara was a grown-up thing that could smear and make the costume messy. "
            f"When the need was near the eyes, the warning also mattered because the black mark could sting."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What changed {an}'s mind?",
            f"{bn} spoke firmly, and {an} listened before using the mascara. "
            f"Because the warning was heard in time, they switched to {prop.phrase} and no mess began."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with the children doing their rhyme-play using {prop.phrase}. "
            f"The ending image shows they learned a costume can look bold without needing mascara or a hurried shave."
        ))
    elif f["outcome"] == "cleaned":
        qa.append((
            f"How did {pw} fix the problem?",
            f"{pw.capitalize()} {cleanup.qa_text}. "
            f"The calm cleanup worked because help came before the smear grew worse and before the show was lost."
        ))
        qa.append((
            f"How did {an} and {bn} reconcile?",
            f"{an} admitted the mistake, and {bn} answered with forgiveness instead of more scolding. "
            f"That apology let them share {prop.phrase} and step back into the game together."
        ))
        qa.append((
            "How did the story end?",
            f"They still made the little show, but with a safer costume piece instead of mascara. "
            f"The ending proves the change by showing a silly pretend tyrant who is sharing rather than bossing."
        ))
    else:
        qa.append((
            "Why was the ending sad?",
            f"The cleanup took too long, so the children missed their little show. "
            f"The bad ending came from using mascara for a costume and then needing help after the smear had already spread."
        ))
        qa.append((
            f"Did {an} and {bn} stay upset with each other?",
            f"No. They were sad, but they reconciled after {an} apologized and {bn} came close again. "
            f"Even though the show was gone, the relationship was repaired with gentle words and a safer game."
        ))
        qa.append((
            "What did they learn?",
            f"They learned that grown-up makeup is not the right tool for a child's costume. "
            f"They also learned that saying sorry and forgiving each other can mend hearts after a bad choice."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mascara", "tyrant", "shave", "costume", "apology"}
    cleanup = f["cleanup_cfg"]
    if cleanup.id == "wipes":
        tags.add("wipes")
    if cleanup.id == "soap_cloth":
        tags.add("soap")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        stage="bedroom",
        need="beard",
        safe_prop="felt_beard",
        cleanup="wipes",
        instigator="Tess",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        stage="hall",
        need="brows",
        safe_prop="sticker_brows",
        cleanup="soap_cloth",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="father",
        trait="gentle",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=6,
    ),
    StoryParams(
        stage="kitchen",
        need="both",
        safe_prop="tyrant_mask",
        cleanup="soap_cloth",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Eli",
        cautioner_gender="boy",
        parent="mother",
        trait="patient",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=4,
    ),
]


ASP_RULES = r"""
need_covered(N, P) :- need(N), safe_prop(P), covers(P, N).
valid(N, P) :- need(N), safe_prop(P), need_covered(N, P).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(S + D) :- chosen_need(N), need_severity(N, S), delay(D).
cleanup_power(P) :- chosen_cleanup(C), power(C, P).
cleaned :- cleanup_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(cleaned) :- not averted, cleaned.
outcome(missed) :- not averted, not cleaned.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in STAGES:
        lines.append(asp.fact("stage", sid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_severity", nid, need.severity))
    for pid, prop in SAFE_PROPS.items():
        lines.append(asp.fact("safe_prop", pid))
        for need_id in sorted(prop.covers):
            lines.append(asp.fact("covers", pid, need_id))
    for cid, cleanup in CLEANUPS.items():
        lines.append(asp.fact("cleanup", cid))
        lines.append(asp.fact("sense", cid, cleanup.sense))
        lines.append(asp.fact("power", cid, cleanup.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_cleanups() -> list[str]:
    import asp

    model = asp.one_model(asp_program("sensible(C) :- cleanup(C), sense(C, S), sense_min(M), S >= M.", "#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_need", params.need),
        asp.fact("chosen_cleanup", params.cleanup),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid_combos() matches ASP ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible_cleanups())
    p_sens = {c.id for c in sensible_cleanups()}
    if c_sens == p_sens:
        print(f"OK: sensible cleanups match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible cleanups: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(7))
        smoke_params.seed = 7
        smoke_sample = generate(smoke_params)
        emit(smoke_sample, trace=False, qa=False)
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a pretend tyrant, mascara trouble, and reconciliation."
    )
    ap.add_argument("--stage", choices=STAGES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--safe-prop", choices=SAFE_PROPS, dest="safe_prop")
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="show valid need/safe-prop pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.need and args.safe_prop:
        need = NEEDS[args.need]
        prop = SAFE_PROPS[args.safe_prop]
        if not valid_combo(need, prop):
            raise StoryError(explain_rejection(need, prop))
    if args.cleanup and CLEANUPS[args.cleanup].sense < SENSE_MIN:
        raise StoryError(explain_cleanup(args.cleanup))

    combos = [
        c for c in valid_combos()
        if (args.need is None or c[0] == args.need)
        and (args.safe_prop is None or c[1] == args.safe_prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    need_id, prop_id = rng.choice(sorted(combos))
    stage = args.stage or rng.choice(sorted(STAGES))
    cleanup = args.cleanup or rng.choice(sorted(c.id for c in sensible_cleanups()))
    instigator, ig = _pick_child(rng)
    cautioner, cg = _pick_child(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        stage=stage,
        need=need_id,
        safe_prop=prop_id,
        cleanup=cleanup,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.stage not in STAGES:
        raise StoryError(f"(Unknown stage: {params.stage})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.safe_prop not in SAFE_PROPS:
        raise StoryError(f"(Unknown safe prop: {params.safe_prop})")
    if params.cleanup not in CLEANUPS:
        raise StoryError(f"(Unknown cleanup: {params.cleanup})")
    if not valid_combo(NEEDS[params.need], SAFE_PROPS[params.safe_prop]):
        raise StoryError(explain_rejection(NEEDS[params.need], SAFE_PROPS[params.safe_prop]))
    if CLEANUPS[params.cleanup].sense < SENSE_MIN:
        raise StoryError(explain_cleanup(params.cleanup))

    world = tell(
        STAGES[params.stage],
        NEEDS[params.need],
        SAFE_PROPS[params.safe_prop],
        CLEANUPS[params.cleanup],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
    )

    story = world.render()
    story = story.replace("instigator", child_name(world.get("instigator")))
    story = story.replace("cautioner", child_name(world.get("cautioner")))
    story = story.replace("parent", world.get("parent").label_word)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible cleanups: {', '.join(asp_sensible_cleanups())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (need, safe_prop) pairs:\n")
        for need, prop in combos:
            print(f"  {need:6} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.instigator} & {p.cautioner}: {p.need} at {p.stage} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
