#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pencil_train_pebble_humor_transformation_mystery.py
==============================================================================

A small storyworld about a child, a toy train, a pencil, and a pebble that seems
to change by itself. The tale is shaped like a gentle mystery with a humorous
reveal: the "strange little passenger" is not magic after all, but the result of
a train carrying a smooth pebble under a low pencil gate until the pencil rubs a
funny face onto it.

The world model keeps the mystery honest:

* A pebble must be smooth enough to take visible pencil marks.
* The train must carry the pebble on an open flatcar.
* The hanging pencil gate must sit low enough for the moving pebble to brush it.

If an explicit choice cannot produce the transformation, the world refuses the
story with a clear StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/pencil_train_pebble_humor_transformation_mystery.py
    python storyworlds/worlds/gpt-5.4/pencil_train_pebble_humor_transformation_mystery.py --train freight --pencil soft --pebble smooth
    python storyworlds/worlds/gpt-5.4/pencil_train_pebble_humor_transformation_mystery.py --train passenger
    python storyworlds/worlds/gpt-5.4/pencil_train_pebble_humor_transformation_mystery.py --all
    python storyworlds/worlds/gpt-5.4/pencil_train_pebble_humor_transformation_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/pencil_train_pebble_humor_transformation_mystery.py --verify
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
        female = {"girl", "mother", "aunt", "woman", "sister"}
        male = {"boy", "father", "uncle", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
            "sister": "sister",
            "brother": "brother",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    hour: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TrainCfg:
    id: str
    label: str
    phrase: str
    color: str
    open_car: bool
    clearance: int
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PencilCfg:
    id: str
    label: str
    phrase: str
    softness: int
    color_word: str
    shaves_curly: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class PebbleCfg:
    id: str
    label: str
    phrase: str
    smoothness: int
    size: int
    speckles: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rub_mark(world: World) -> list[str]:
    pebble = world.get("pebble")
    pencil = world.get("pencil")
    train = world.get("train")
    if train.meters["laps"] < THRESHOLD:
        return []
    if not world.facts.get("fit"):
        return []
    sig = ("rub_mark", int(train.meters["laps"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pebble.meters["marked"] += 1
    pencil.meters["used"] += 1
    pebble.attrs["face_stage"] = int(pebble.meters["marked"])
    if pebble.meters["marked"] >= 2:
        pebble.attrs["looks_funny"] = True
    return ["__mark__"]


def _r_ticket_stick(world: World) -> list[str]:
    pebble = world.get("pebble")
    if pebble.meters["marked"] < 2:
        return []
    sig = ("ticket_stick",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pebble.meters["decorated"] += 1
    pebble.attrs["wears_ticket"] = True
    return ["__ticket__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="rub_mark", tag="physical", apply=_r_rub_mark),
    Rule(name="ticket_stick", tag="physical", apply=_r_ticket_stick),
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


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic play corner",
        detail="Rain tapped the roof, and every toy seemed to be keeping a secret.",
        hour="late afternoon",
        tags={"mystery", "indoors"},
    ),
    "hall": Setting(
        id="hall",
        place="the long front hall",
        detail="The hallway was dim and polished, with doors that made little shadows.",
        hour="after supper",
        tags={"mystery", "indoors"},
    ),
    "porch": Setting(
        id="porch",
        place="the screened porch",
        detail="The evening light was soft, and the boards hummed when small wheels rolled over them.",
        hour="evening",
        tags={"mystery", "porch"},
    ),
}

TRAINS = {
    "freight": TrainCfg(
        id="freight",
        label="freight train",
        phrase="a little green freight train with an open flatcar",
        color="green",
        open_car=True,
        clearance=2,
        sound="clack-clack",
        tags={"train", "flatcar"},
    ),
    "mail": TrainCfg(
        id="mail",
        label="mail train",
        phrase="a bright red mail train with a low wagon behind it",
        color="red",
        open_car=True,
        clearance=1,
        sound="trit-trit",
        tags={"train", "flatcar"},
    ),
    "passenger": TrainCfg(
        id="passenger",
        label="passenger train",
        phrase="a shiny blue passenger train with closed windows",
        color="blue",
        open_car=False,
        clearance=0,
        sound="hummm",
        tags={"train", "closed_car"},
    ),
}

PENCILS = {
    "soft": PencilCfg(
        id="soft",
        label="soft pencil",
        phrase="a soft yellow pencil with a pink eraser",
        softness=3,
        color_word="dark gray",
        shaves_curly=True,
        tags={"pencil", "graphite"},
    ),
    "school": PencilCfg(
        id="school",
        label="school pencil",
        phrase="a striped school pencil",
        softness=2,
        color_word="gray",
        shaves_curly=True,
        tags={"pencil", "graphite"},
    ),
    "hard": PencilCfg(
        id="hard",
        label="hard pencil",
        phrase="a hard little drafting pencil",
        softness=1,
        color_word="pale gray",
        shaves_curly=False,
        tags={"pencil", "graphite"},
    ),
}

PEBBLES = {
    "smooth": PebbleCfg(
        id="smooth",
        label="smooth pebble",
        phrase="a smooth round pebble",
        smoothness=3,
        size=1,
        speckles="tiny silver speckles",
        tags={"pebble", "smooth"},
    ),
    "striped": PebbleCfg(
        id="striped",
        label="striped pebble",
        phrase="a flat striped pebble",
        smoothness=2,
        size=1,
        speckles="pale cream stripes",
        tags={"pebble", "smooth"},
    ),
    "rough": PebbleCfg(
        id="rough",
        label="rough pebble",
        phrase="a rough bumpy pebble",
        smoothness=1,
        size=2,
        speckles="crumbly dark dots",
        tags={"pebble", "rough"},
    ),
}

CHILD_NAMES = {
    "girl": ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Tessa", "Ivy"],
    "boy": ["Ben", "Max", "Leo", "Sam", "Theo", "Finn", "Noah", "Eli"],
}

HELPERS = {
    "mother": ["Mom", "mother"],
    "father": ["Dad", "father"],
    "sister": ["big sister", "sister"],
    "brother": ["big brother", "brother"],
}


def can_transform(train: TrainCfg, pencil: PencilCfg, pebble: PebbleCfg) -> bool:
    return train.open_car and pencil.softness >= 2 and pebble.smoothness >= 2 and pebble.size <= train.clearance


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for train_id, train in TRAINS.items():
        for pencil_id, pencil in PENCILS.items():
            for pebble_id, pebble in PEBBLES.items():
                if can_transform(train, pencil, pebble):
                    combos.append((train_id, pencil_id, pebble_id))
    return combos


def explain_rejection(train: TrainCfg, pencil: PencilCfg, pebble: PebbleCfg) -> str:
    if not train.open_car:
        return (
            f"(No story: the {train.label} keeps its cargo inside, so the pebble cannot brush the pencil gate. "
            f"Pick a train with an open car.)"
        )
    if pencil.softness < 2:
        return (
            f"(No story: the {pencil.label} is too hard to leave a clear funny face on the pebble. "
            f"Pick a softer pencil.)"
        )
    if pebble.smoothness < 2:
        return (
            f"(No story: the {pebble.label} is too rough to take neat pencil marks, so the mystery face would not appear. "
            f"Pick a smoother pebble.)"
        )
    if pebble.size > train.clearance:
        return (
            f"(No story: the {pebble.label} rides too high on the train to slip under the pencil gate. "
            f"Pick a smaller pebble or a train with more clearance.)"
        )
    return "(No story: that combination cannot produce the transformation.)"


def predict_transformation(world: World) -> dict:
    sim = world.copy()
    train = sim.get("train")
    for _ in range(2):
        train.meters["laps"] += 1
        propagate(sim, narrate=False)
    pebble = sim.get("pebble")
    return {
        "marked": pebble.meters["marked"],
        "decorated": pebble.meters["decorated"],
        "funny": bool(pebble.attrs.get("looks_funny")),
    }


def introduce(world: World, child: Entity, helper: Entity, train: TrainCfg, pencil: PencilCfg, pebble: PebbleCfg) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On {world.setting.hour} in {world.setting.place}, {child.id} was busy making a tiny railway mystery. "
        f"{world.setting.detail}"
    )
    world.say(
        f"On the floor waited {train.phrase}, {pencil.phrase}, and {pebble.phrase} with {pebble.speckles}."
    )
    world.say(
        f"{child.id} used the pencil to draw station signs and called the pebble the Quiet Passenger, because it never answered back."
    )
    if helper.type in {"mother", "father"}:
        world.say(
            f'{helper.label_word.capitalize()} smiled from nearby. "A good mystery needs clues," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} leaned over the tracks and whispered, "If anything odd happens, detective, I want to see it."'
        )


def build_gate(world: World, child: Entity, pencil: PencilCfg) -> None:
    world.get("pencil").attrs["is_gate"] = True
    world.say(
        f"To make a station gate, {child.id} balanced the pencil across two blocks above the track, low enough to look grand and silly at the same time."
    )


def first_lap(world: World, child: Entity, train: TrainCfg) -> None:
    train_ent = world.get("train")
    train_ent.meters["laps"] += 1
    world.get("pebble").attrs["on_train"] = True
    propagate(world, narrate=False)
    world.say(
        f'Then {child.id} gave the {train.label} a push. "{train.sound}!" went the wheels as the little train rolled under the pencil gate.'
    )


def notice_clue(world: World, child: Entity, pencil: PencilCfg, pebble: PebbleCfg) -> None:
    pebble_ent = world.get("pebble")
    child.memes["curiosity"] += 1
    stage = int(pebble_ent.meters["marked"])
    if stage >= 1:
        world.say(
            f"When the train came back, the pebble did not look quite the same. A {pencil.color_word} dot and a crooked line had appeared on it, like one eyebrow trying to ask a question."
        )
    else:
        world.say(
            f"When the train came back, nothing looked strange at all, and the case went cold before it even began."
        )
    world.facts["clue_seen"] = stage >= 1


def suspect_list(world: World, child: Entity, helper: Entity) -> None:
    child.memes["suspicion"] += 1
    world.say(
        f"{child.id} narrowed {child.pronoun('possessive')} eyes. Was the pebble changing by itself? Was the train hiding a secret? Was {helper.label_word} playing a trick?"
    )


def test_again(world: World, child: Entity, train: TrainCfg) -> None:
    train_ent = world.get("train")
    train_ent.meters["laps"] += 1
    propagate(world, narrate=False)
    world.say(
        f"To test the case, {child.id} set the pebble on the flatcar once more and sent the train around again, slower this time, with detective eyes wide open."
    )


def reveal(world: World, child: Entity, helper: Entity, pencil: PencilCfg) -> None:
    pebble = world.get("pebble")
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["pride"] += 1
    if pebble.attrs.get("wears_ticket"):
        world.say(
            f"This time {child.id} saw it happen: the pebble brushed the hanging pencil, which sketched two eyes and a droll mouth, and then a tiny round paper ticket stuck to the top like a hat."
        )
        world.say(
            f"The Quiet Passenger had not turned alive at all. It had turned into the funniest mayor a train line ever carried."
        )
    else:
        world.say(
            f"This time {child.id} saw the truth: the hanging pencil had rubbed the pebble on each pass. The mystery was only track, graphite, and good luck."
        )
    if helper.type in {"sister", "brother"}:
        world.say(
            f'{helper.label_word.capitalize()} laughed so hard {helper.pronoun()} had to sit on the rug. "Mayor Pebble wants a ticket inspector," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} laughed softly. "So that is your culprit," {helper.pronoun()} said. "A pencil with too much imagination."'
        )


def ending(world: World, child: Entity, train: TrainCfg) -> None:
    pebble = world.get("pebble")
    child.memes["satisfaction"] += 1
    pebble.attrs["title"] = "Mayor Pebble"
    world.say(
        f"After that, every ride on the {train.label} had one honored passenger: Mayor Pebble, wearing a penciled grin and a paper hat."
    )
    world.say(
        f"{child.id} still called it a mystery, but now it was the kind that made everyone giggle whenever the train came by."
    )


def tell(setting: Setting, train_cfg: TrainCfg, pencil_cfg: PencilCfg, pebble_cfg: PebbleCfg,
         child_name: str = "Nora", child_gender: str = "girl",
         helper_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["curious", "careful"],
    ))
    helper_label = HELPERS[helper_type][0]
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=helper_label,
        role="helper",
    ))
    train = world.add(Entity(
        id="train",
        type="train",
        label=train_cfg.label,
        phrase=train_cfg.phrase,
        tags=set(train_cfg.tags),
    ))
    pencil = world.add(Entity(
        id="pencil",
        type="pencil",
        label=pencil_cfg.label,
        phrase=pencil_cfg.phrase,
        tags=set(pencil_cfg.tags),
    ))
    pebble = world.add(Entity(
        id="pebble",
        type="pebble",
        label=pebble_cfg.label,
        phrase=pebble_cfg.phrase,
        tags=set(pebble_cfg.tags),
    ))

    fit = can_transform(train_cfg, pencil_cfg, pebble_cfg)
    world.facts["fit"] = fit
    if not fit:
        raise StoryError(explain_rejection(train_cfg, pencil_cfg, pebble_cfg))

    introduce(world, child, helper, train_cfg, pencil_cfg, pebble_cfg)
    world.para()
    build_gate(world, child, pencil_cfg)
    first_lap(world, child, train_cfg)
    notice_clue(world, child, pencil_cfg, pebble_cfg)

    world.para()
    suspect_list(world, child, helper)
    pred = predict_transformation(world)
    world.facts["predicted_marked"] = pred["marked"]
    world.facts["predicted_funny"] = pred["funny"]
    test_again(world, child, train_cfg)

    world.para()
    reveal(world, child, helper, pencil_cfg)
    ending(world, child, train_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        train_cfg=train_cfg,
        pencil_cfg=pencil_cfg,
        pebble_cfg=pebble_cfg,
        train=train,
        pencil=pencil,
        pebble=pebble,
        transformed=pebble.meters["decorated"] >= THRESHOLD or pebble.attrs.get("looks_funny", False),
        mystery_solved=True,
    )
    return world


KNOWLEDGE = {
    "pencil": [
        (
            "What does a pencil leave behind when it rubs on paper or a smooth thing?",
            "A pencil leaves graphite, which looks gray or dark on the surface. On something smooth, that rubbing can make a visible mark."
        )
    ],
    "train": [
        (
            "Why can a toy train make the same thing happen again and again?",
            "A toy train follows the same track each lap, so if something brushes it in one place, that brushing can happen every time it goes by."
        )
    ],
    "pebble": [
        (
            "Why do smooth pebbles show marks better than rough pebbles?",
            "Smooth pebbles have flatter surfaces, so pencil marks sit on top where you can see them. Rough pebbles break the line up and make the marks harder to notice."
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. Good detectives look for clues before they guess."
        )
    ],
    "friction": [
        (
            "What is friction?",
            "Friction is the rubbing that happens when two things touch and move against each other. That rubbing can slow things down or leave marks."
        )
    ],
    "ticket": [
        (
            "What is a ticket on a train for?",
            "A ticket is a small piece of paper that shows a rider belongs on the train. In pretend play, a ticket can also become a funny costume."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "pencil", "train", "pebble", "friction", "ticket"]


@dataclass
class StoryParams:
    setting: str
    train: str
    pencil: str
    pebble: str
    child_name: str
    child_gender: str
    helper_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    train = f["train_cfg"]
    pencil = f["pencil_cfg"]
    pebble = f["pebble_cfg"]
    return [
        (
            f'Write a short mystery story for a 3-to-5-year-old that includes the words '
            f'"pencil," "train," and "pebble," and ends with a funny transformation.'
        ),
        (
            f"Tell a gentle mystery where {child.id} sees a {pebble.label} change during a ride on a {train.label}, "
            f"then discovers that a {pencil.label} caused the silly new look."
        ),
        (
            f"Write a playful detective story where {helper.label_word} helps a child solve why a pebble on a toy train comes back looking different each time."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    train_cfg = f["train_cfg"]
    pencil_cfg = f["pencil_cfg"]
    pebble_cfg = f["pebble_cfg"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {helper_word}, who listens to the mystery. The story also follows a toy train, a pencil gate, and one very interesting pebble."
        ),
        (
            "What made the story feel like a mystery at first?",
            f"The pebble came back from its train ride looking different, with new pencil marks on it. That made {child.id} wonder whether something secret was happening on the track."
        ),
        (
            f"Why did {child.id} test the train a second time?",
            f"{child.id} wanted more clues before making a guess. Sending the train around again let {child.pronoun('object')} watch the exact place where the change happened."
        ),
        (
            "How did the pebble transform?",
            f"The open train car carried the smooth pebble under the low pencil gate, and the rubbing drew a face onto it. Then a tiny paper ticket stuck on top, so the pebble looked like a funny little mayor."
        ),
        (
            "Was the pebble really magic?",
            f"No. The change came from rubbing and pretend-play objects, not from real magic. The mystery felt spooky only until {child.id} saw the pencil touch the pebble."
        ),
        (
            "How did the story end?",
            f"It ended with laughter and a solved mystery. After that, Mayor Pebble rode the train on purpose, proving that the strange change had become part of the game."
        ),
    ]
    if helper.type in {"sister", "brother"}:
        qa.append(
            (
                f"What did {helper_word} do when the mystery was solved?",
                f"{helper_word.capitalize()} laughed and joined the joke about Mayor Pebble. That happy reaction turned the solved clue into a new game instead of ending the fun."
            )
        )
    else:
        qa.append(
            (
                f"How did {helper_word} help?",
                f"{helper_word.capitalize()} did not solve the case first. {helper.pronoun().capitalize()} stayed close, encouraged careful looking, and let {child.id} discover the answer."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "pencil", "train", "pebble", "friction"}
    if world.get("pebble").attrs.get("wears_ticket"):
        tags.add("ticket")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic",
        train="freight",
        pencil="soft",
        pebble="smooth",
        child_name="Nora",
        child_gender="girl",
        helper_type="mother",
    ),
    StoryParams(
        setting="hall",
        train="mail",
        pencil="school",
        pebble="striped",
        child_name="Ben",
        child_gender="boy",
        helper_type="brother",
    ),
    StoryParams(
        setting="porch",
        train="freight",
        pencil="school",
        pebble="smooth",
        child_name="Lucy",
        child_gender="girl",
        helper_type="father",
    ),
    StoryParams(
        setting="attic",
        train="mail",
        pencil="soft",
        pebble="striped",
        child_name="Theo",
        child_gender="boy",
        helper_type="sister",
    ),
]


ASP_RULES = r"""
valid(T, Pn, Pb) :- train(T), pencil(Pn), pebble(Pb),
                    open_car(T), soft_enough(Pn), smooth_enough(Pb),
                    size(Pb, S), clearance(T, C), S <= C.

soft_enough(Pn)   :- softness(Pn, S), S >= 2.
smooth_enough(Pb) :- smoothness(Pb, S), S >= 2.

transforms :- chosen_train(T), chosen_pencil(Pn), chosen_pebble(Pb), valid(T, Pn, Pb).
outcome(funny_mayor) :- transforms.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in TRAINS.items():
        lines.append(asp.fact("train", tid))
        lines.append(asp.fact("clearance", tid, t.clearance))
        if t.open_car:
            lines.append(asp.fact("open_car", tid))
    for pid, p in PENCILS.items():
        lines.append(asp.fact("pencil", pid))
        lines.append(asp.fact("softness", pid, p.softness))
    for pid, p in PEBBLES.items():
        lines.append(asp.fact("pebble", pid))
        lines.append(asp.fact("smoothness", pid, p.smoothness))
        lines.append(asp.fact("size", pid, p.size))
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
            asp.fact("chosen_train", params.train),
            asp.fact("chosen_pencil", params.pencil),
            asp.fact("chosen_pebble", params.pebble),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "none"


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

    for params in CURATED:
        expected = "funny_mayor"
        got = asp_outcome(params)
        if got != expected:
            rc = 1
            print(f"MISMATCH in outcome for {params}: expected {expected}, got {got}")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mystery about a pencil, a train, and a pebble."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--train", choices=TRAINS)
    ap.add_argument("--pencil", choices=PENCILS)
    ap.add_argument("--pebble", choices=PEBBLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.train and args.pencil and args.pebble:
        train = TRAINS[args.train]
        pencil = PENCILS[args.pencil]
        pebble = PEBBLES[args.pebble]
        if not can_transform(train, pencil, pebble):
            raise StoryError(explain_rejection(train, pencil, pebble))

    combos = [
        c for c in valid_combos()
        if (args.train is None or c[0] == args.train)
        and (args.pencil is None or c[1] == args.pencil)
        and (args.pebble is None or c[2] == args.pebble)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    train_id, pencil_id, pebble_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES[gender])
    helper_type = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        setting=setting_id,
        train=train_id,
        pencil=pencil_id,
        pebble=pebble_id,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.train not in TRAINS:
        raise StoryError(f"(Unknown train: {params.train})")
    if params.pencil not in PENCILS:
        raise StoryError(f"(Unknown pencil: {params.pencil})")
    if params.pebble not in PEBBLES:
        raise StoryError(f"(Unknown pebble: {params.pebble})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper_type})")

    world = tell(
        setting=SETTINGS[params.setting],
        train_cfg=TRAINS[params.train],
        pencil_cfg=PENCILS[params.pencil],
        pebble_cfg=PEBBLES[params.pebble],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (train, pencil, pebble) combos:\n")
        for train, pencil, pebble in combos:
            print(f"  {train:10} {pencil:8} {pebble}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.train} / {p.pencil} / {p.pebble} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
