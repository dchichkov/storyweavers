#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gospel_spot_segmentation_bad_ending_folk_tale.py
============================================================================

A standalone storyworld for a small folk-tale domain built from the seed words
"gospel", "spot", and "segmentation", with a deliberately bad ending.

Premise
-------
A child in an old village is carrying something important to an evening gospel
gathering. An elder has laid out a visible segmentation of the ground with
stones, stakes, or ash marks, showing which strips are safe and which are soft.
The child wants the brightest spot and takes a shortcut off the marked way.
The earth gives way. A grown-up may pull the child back, but the thing being
carried is ruined or lost, and the gathering ends in sorrow.

The world model prefers only grounded combinations:
- the setting must truly contain dangerous soft ground,
- the cargo must be the kind of thing water or mud would spoil,
- the marker must actually fit the chosen setting,
- the rescue method must meet a minimum common-sense threshold.

Run it
------
python storyworlds/worlds/gpt-5.4/gospel_spot_segmentation_bad_ending_folk_tale.py
python storyworlds/worlds/gpt-5.4/gospel_spot_segmentation_bad_ending_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/gospel_spot_segmentation_bad_ending_folk_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/gospel_spot_segmentation_bad_ending_folk_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    gathering: str
    meeting_place: str
    bright_spot: str
    safe_path: str
    dangerous_patch: str
    texture: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    spoil_text: str
    loss_text: str
    event_need: str
    plural: bool = False
    spoilable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Marker:
    id: str
    label: str
    phrase: str
    works_in: set[str] = field(default_factory=set)
    segmentation_text: str = ""
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


def _r_sink(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cargo = world.get("cargo")
    patch = world.get("patch")
    if child.meters["off_path"] >= THRESHOLD and patch.meters["trod_on"] >= THRESHOLD:
        sig = ("sink",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["sinking"] += 1
            child.meters["muddy"] += 1
            cargo.meters["wet"] += 1
            cargo.meters["muddy"] += 1
            world.get("meeting").meters["risk"] += 1
            world.get("watcher").memes["fear"] += 1
            out.append("__sink__")
    return out


def _r_ruin(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["wet"] >= THRESHOLD:
        sig = ("ruin",)
        if sig not in world.fired:
            world.fired.add(sig)
            cargo.meters["ruined"] += 1
            world.get("meeting").meters["silence"] += 1
            world.get("child").memes["shame"] += 1
            world.get("elder").memes["sorrow"] += 1
            out.append("__ruin__")
    return out


CAUSAL_RULES = [
    Rule(name="sink", tag="physical", apply=_r_sink),
    Rule(name="ruin", tag="social", apply=_r_ruin),
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


def marker_fits(setting_id: str, marker: Marker) -> bool:
    return setting_id in marker.works_in


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for cargo_id, cargo in CARGOES.items():
            for marker_id, marker in MARKERS.items():
                if setting.severity > 0 and cargo.spoilable and marker_fits(setting_id, marker):
                    combos.append((setting_id, cargo_id, marker_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def danger_severity(setting: Setting, haste: int) -> int:
    return setting.severity + haste


def child_saved(response: Response, setting: Setting, haste: int) -> bool:
    return response.power >= danger_severity(setting, haste)


def predict_shortcut(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    patch = sim.get("patch")
    child.meters["off_path"] += 1
    patch.meters["trod_on"] += 1
    propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    return {
        "sinking": child.meters["sinking"] >= THRESHOLD,
        "ruined": cargo.meters["ruined"] >= THRESHOLD,
        "risk": sim.get("meeting").meters["risk"],
    }


def introduce(world: World, child: Entity, watcher: Entity, elder: Entity, cargo: Cargo) -> None:
    world.say(
        f"In the days when every lane in the village remembered old songs, {child.id} "
        f"set out with {cargo.phrase} for {world.setting.gathering}."
    )
    world.say(
        f"{watcher.id} walked beside {child.pronoun('object')}, and {elder.id}, "
        f"the village {elder.label_word}, waited ahead at {world.setting.meeting_place}."
    )


def place_scene(world: World, marker: Marker) -> None:
    world.say(
        f"The path crossed {world.setting.label}, where {world.setting.texture}. "
        f"There, a bright spot of late sun lay beyond the marked way."
    )
    world.say(
        f"To guide the travelers, the elder had made {marker.phrase}, a segmentation "
        f"that showed which strips were firm and which would not bear a careless foot."
    )


def desire(world: World, child: Entity, cargo: Cargo) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} looked at the golden place and said, "
        f'"If I stand in that spot, everyone will see {cargo.label} first."'
    )


def warn(world: World, watcher: Entity, child: Entity, marker: Marker, cargo: Cargo) -> None:
    pred = predict_shortcut(world)
    watcher.memes["caution"] += 1
    world.facts["predicted_ruin"] = pred["ruined"]
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{watcher.id} touched {child.pronoun("possessive")} sleeve. "Stay inside the '
        f'{marker.label}," {watcher.pronoun()} said. "That bright place is over '
        f'{world.setting.dangerous_patch}, and {cargo.label} will be lost if you go there."'
    )


def refuse(world: World, child: Entity, watcher: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f'But pride had climbed into {child.id}\'s heart. "A song belongs in the best spot," '
        f'{child.pronoun()} said, and {child.pronoun()} slipped away from {watcher.id}.'
    )


def shortcut(world: World, child: Entity) -> None:
    child.meters["off_path"] += 1
    world.get("patch").meters["trod_on"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The ground shivered under {child.pronoun('possessive')} foot. In one breath "
        f"{child.pronoun()} was ankle-deep, and in the next the mud had hold of "
        f"{child.pronoun('object')}."
    )


def spill(world: World, child: Entity, cargo: Cargo) -> None:
    if world.get("cargo").meters["ruined"] >= THRESHOLD:
        world.say(
            f"{cargo.phrase.capitalize()} slipped from {child.pronoun('possessive')} hands "
            f"and fell into the dark mire, where it turned {cargo.spoil_text}."
        )


def alarm(world: World, watcher: Entity, elder: Entity) -> None:
    world.say(f'"{elder.id}!" {watcher.id} cried. "The ground is taking {world.get("child").id}!"')


def rescue(world: World, elder: Entity, response: Response) -> None:
    child = world.get("child")
    child.meters["sinking"] = 0.0
    body = response.text
    world.say(f"{elder.id} came with all the speed {elder.pronoun()} had and {body}.")
    child.memes["fear"] += 1
    child.memes["shame"] += 1


def rescue_fail(world: World, elder: Entity, response: Response) -> None:
    child = world.get("child")
    child.meters["sinking"] += 1
    child.meters["lost_shoe"] += 1
    world.get("meeting").meters["silence"] += 1
    world.say(f"{elder.id} ran to help, but {elder.pronoun()} {response.fail}.")
    world.say(
        f"The child was dragged out at last, sobbing and one shoe lighter, while the mire kept what it had taken."
    )
    child.memes["fear"] += 1
    child.memes["shame"] += 1


def bad_ending_ruined(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["grief"] += 1
    elder.memes["sorrow"] += 1
    world.say(
        f"They reached {world.setting.meeting_place}, but no one set the gathering right again. "
        f"{cargo.phrase.capitalize()} was ruined, and the evening gospel began with a hush instead of a joyful voice."
    )
    world.say(
        f"{elder.id} said nothing harsh. That was worse. {child.id} could only stare at the spoiled gift "
        f"and wish {child.pronoun()} had trusted the segmentation on the ground."
    )
    world.say(
        "So the tale was told afterward in low voices: the child had found the bright spot, "
        "and lost the song that was meant for everyone."
    )


def bad_ending_lost(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["grief"] += 1
    elder.memes["sorrow"] += 1
    world.say(
        f"When they came at last to {world.setting.meeting_place}, there was nothing left to offer. "
        f"The mire had swallowed {cargo.label}, and the people stood with empty hands and lowered heads."
    )
    world.say(
        f"Even the first gospel line broke apart before it was half begun, for the village remembered the loss "
        f"more loudly than the tune."
    )
    world.say(
        f"From then on, whenever children boasted about finding the finest spot, the elders pointed toward "
        f"{world.setting.label} and said that pride walks where warning stones do not."
    )


def tell(
    setting: Setting,
    cargo_cfg: Cargo,
    marker: Marker,
    response: Response,
    *,
    child_name: str = "Mara",
    child_gender: str = "girl",
    watcher_name: str = "Ivo",
    watcher_gender: str = "boy",
    elder_type: str = "grandmother",
    haste: int = 0,
    child_trait: str = "proud",
    watcher_trait: str = "careful",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[child_trait]))
    watcher = world.add(Entity(id=watcher_name, kind="character", type=watcher_gender, role="watcher", traits=[watcher_trait]))
    elder = world.add(Entity(id="Old Mara", kind="character", type=elder_type, role="elder", label=elder_type))
    cargo = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo_cfg.label,
            phrase=cargo_cfg.phrase,
            plural=cargo_cfg.plural,
            tags=set(cargo_cfg.tags),
        )
    )
    patch = world.add(Entity(id="patch", type="ground", label=setting.dangerous_patch))
    world.add(Entity(id="meeting", type="meeting", label=setting.gathering))

    introduce(world, child, watcher, elder, cargo_cfg)
    place_scene(world, marker)

    world.para()
    desire(world, child, cargo_cfg)
    warn(world, watcher, child, marker, cargo_cfg)
    refuse(world, child, watcher)

    world.para()
    shortcut(world, child)
    spill(world, child, cargo_cfg)
    alarm(world, watcher, elder)

    saved = child_saved(response, setting, haste)
    world.para()
    if saved:
        rescue(world, elder, response)
        bad_ending_ruined(world, child, elder, cargo_cfg)
        outcome = "ruined"
    else:
        rescue_fail(world, elder, response)
        bad_ending_lost(world, child, elder, cargo_cfg)
        outcome = "lost"

    world.facts.update(
        setting=setting,
        cargo_cfg=cargo_cfg,
        marker=marker,
        response=response,
        child=child,
        watcher=watcher,
        elder=elder,
        cargo=world.get("cargo"),
        haste=haste,
        outcome=outcome,
        saved=saved,
        ruined=world.get("cargo").meters["ruined"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "gospel": [
        (
            "What is a gospel song?",
            "A gospel song is a song of praise and hope that people sing together. It is often warm, strong, and meant to be shared with a whole group."
        )
    ],
    "spot": [
        (
            "What is a spot?",
            "A spot is a particular place, even if it is only a small one. People often choose a spot because it is bright, safe, or easy to see."
        )
    ],
    "segmentation": [
        (
            "What does segmentation mean?",
            "Segmentation means dividing something into parts or sections. In a path or field, a segmentation can show where one part ends and another begins."
        )
    ],
    "mud": [
        (
            "Why can mud be dangerous?",
            "Mud can be slippery and deep, and sometimes the ground under it is soft. That means a foot can sink instead of staying on firm earth."
        )
    ],
    "rope": [
        (
            "What can a rope do in a rescue?",
            "A rope can give someone something strong to hold. A grown-up can pull from firm ground while the stuck person holds on."
        )
    ],
    "pole": [
        (
            "Why would someone use a pole to help a stuck person?",
            "A long pole lets a helper reach from safe ground without stepping into danger. The stuck person can grab the pole and be pulled back."
        )
    ],
    "plank": [
        (
            "Why can a plank help on soft ground?",
            "A plank spreads weight over a wider place. That can make a safer surface than one small foot pressing into mud."
        )
    ],
}
KNOWLEDGE_ORDER = ["gospel", "spot", "segmentation", "mud", "rope", "pole", "plank"]


SETTINGS = {
    "reed_meadow": Setting(
        id="reed_meadow",
        label="the reed meadow",
        gathering="the evening gospel on the hill",
        meeting_place="the hill chapel yard",
        bright_spot="a patch of sun among the reeds",
        safe_path="a line of flat stones",
        dangerous_patch="the black reed-mud",
        texture="water shone between the reeds and the earth looked firmer than it was",
        severity=2,
        tags={"mud", "gospel", "spot"},
    ),
    "river_ford": Setting(
        id="river_ford",
        label="the ford by the willow bridge",
        gathering="the gospel singing by the mill",
        meeting_place="the mill porch",
        bright_spot="a pale strip of light near the bridge-post",
        safe_path="the raised gravel crossing",
        dangerous_patch="the sucking riverbank clay",
        texture="the ford gleamed softly, and the bank hid deep clay beneath a skin of water",
        severity=3,
        tags={"mud", "gospel", "spot"},
    ),
    "marsh_lane": Setting(
        id="marsh_lane",
        label="the marsh lane below the bell hill",
        gathering="the twilight gospel under the bell",
        meeting_place="the bell hill steps",
        bright_spot="a warm place where the west light touched the grass",
        safe_path="the packed cart-track",
        dangerous_patch="the green-brown bog edge",
        texture="rushes nodded on both sides and the lane looked gentle, though the edges were treacherous",
        severity=2,
        tags={"mud", "gospel", "spot"},
    ),
}

CARGOES = {
    "hymn_book": Cargo(
        id="hymn_book",
        label="the hymn book",
        phrase="the old hymn book wrapped in linen",
        spoil_text="soggy and streaked with mud",
        loss_text="the book sank where no hand could reach it",
        event_need="the people needed it to follow the verses",
        tags={"gospel"},
    ),
    "sweet_buns": Cargo(
        id="sweet_buns",
        label="the basket of sweet buns",
        phrase="a basket of sweet buns for the singers",
        spoil_text="sodden and brown with mire",
        loss_text="the buns slid away into the mire",
        event_need="the singers were meant to share them after the last verse",
        tags={"gospel"},
        plural=True,
    ),
    "bell_ribbon": Cargo(
        id="bell_ribbon",
        label="the bell ribbon",
        phrase="the red ribbon meant for the chapel bell",
        spoil_text="dark, dripping, and spoiled",
        loss_text="the ribbon vanished into the muck",
        event_need="it was to be tied before the first song",
        tags={"gospel"},
    ),
}

MARKERS = {
    "white_stones": Marker(
        id="white_stones",
        label="white stones",
        phrase="a row of white stones laid from tuft to tuft",
        works_in={"reed_meadow", "marsh_lane"},
        segmentation_text="stones",
        tags={"segmentation"},
    ),
    "willow_stakes": Marker(
        id="willow_stakes",
        label="willow stakes",
        phrase="a segmentation of willow stakes and bits of string",
        works_in={"river_ford", "reed_meadow"},
        segmentation_text="stakes",
        tags={"segmentation"},
    ),
    "ash_lines": Marker(
        id="ash_lines",
        label="ash lines",
        phrase="thin ash lines brushed across the safer ground",
        works_in={"marsh_lane"},
        segmentation_text="ash",
        tags={"segmentation"},
    ),
}

RESPONSES = {
    "rope": Response(
        id="rope",
        sense=3,
        power=2,
        text="cast a rope from the safe path and hauled the child back by slow, steady pulls",
        fail="threw a rope, but the mud held fast and the pull came too late",
        qa_text="used a rope from firm ground to pull the child back",
        tags={"rope"},
    ),
    "pole": Response(
        id="pole",
        sense=3,
        power=3,
        text="laid flat on the safe path, thrust a long pole forward, and dragged the child back hand over hand",
        fail="reached with a pole, but the bank kept crumbling under the struggle",
        qa_text="reached with a long pole and pulled the child back from firm ground",
        tags={"pole"},
    ),
    "plank": Response(
        id="plank",
        sense=2,
        power=2,
        text="pushed a plank over the soft place and crawled forward just far enough to drag the child onto it",
        fail="pushed a plank out, but the plank tipped and the mire had already swallowed the cargo",
        qa_text="slid a plank over the soft ground and pulled the child back across it",
        tags={"plank"},
    ),
    "bare_hands": Response(
        id="bare_hands",
        sense=1,
        power=1,
        text="ran straight into the mud and tugged with bare hands until the child was free",
        fail="charged in with bare hands, only making the soft ground break wider",
        qa_text="pulled with bare hands",
        tags=set(),
    ),
}

GIRL_NAMES = ["Mara", "Elsa", "Toma", "Lina", "Rada", "Vera", "Nina", "Mila"]
BOY_NAMES = ["Ivo", "Petar", "Miro", "Stefan", "Luka", "Borin", "Toma", "Niko"]
TRAITS = ["proud", "eager", "vain", "restless", "bold"]
WATCHER_TRAITS = ["careful", "steady", "thoughtful", "gentle"]


@dataclass
class StoryParams:
    setting: str
    cargo: str
    marker: str
    response: str
    child_name: str
    child_gender: str
    watcher_name: str
    watcher_gender: str
    elder_type: str
    child_trait: str
    watcher_trait: str
    haste: int = 0
    seed: Optional[int] = None


def pair_word(child: Entity, watcher: Entity) -> str:
    if child.type == "girl" and watcher.type == "girl":
        return "two village girls"
    if child.type == "boy" and watcher.type == "boy":
        return "two village boys"
    return "two village children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cargo = f["cargo_cfg"]
    setting = f["setting"]
    marker = f["marker"]
    return [
        f'Write a short folk tale for a young child that includes the words "gospel", "spot", and "segmentation".',
        f"Tell a cautionary village tale where {child.id} leaves the marked path at {setting.label} to reach a brighter spot and ruins {cargo.label}.",
        f"Write a sad folk-style story in which a visible segmentation made with {marker.label} is ignored, and the ending teaches that pride can spoil a good errand.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    watcher = f["watcher"]
    elder = f["elder"]
    cargo = f["cargo_cfg"]
    setting = f["setting"]
    marker = f["marker"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_word(child, watcher)}, {child.id} and {watcher.id}, and the elder called {elder.id}. They were on their way to {setting.gathering}."
        ),
        (
            "What was the child trying to do?",
            f"{child.id} wanted to stand in the brightest spot and arrive looking important with {cargo.label}. That proud wish is what pulled {child.pronoun('object')} off the safe path."
        ),
        (
            "What did the segmentation mean in the story?",
            f"The segmentation was the visible dividing of the ground with {marker.label}. It showed where the earth was firm and where the dangerous patch would not hold a person's weight."
        ),
        (
            f"Why did {watcher.id} warn {child.id}?",
            f"{watcher.id} warned {child.id} because the bright place lay beyond {setting.dangerous_patch}. If {child.id} stepped outside the marked way, both the child and {cargo.label} would be in danger."
        ),
    ]
    if f["outcome"] == "ruined":
        qa.append(
            (
                f"How did the elder save {child.id}, and why was the ending still bad?",
                f"{elder.id} {response.qa_text}. But {cargo.label} had already fallen into the mire and was spoiled, so the gathering began sadly instead of joyfully."
            )
        )
    else:
        qa.append(
            (
                f"What happened when the rescue came too late?",
                f"The elder tried to help, but the mud had already taken too much. {child.id} was dragged out alive, yet {cargo.label} was lost and the whole meeting was left empty and ashamed."
            )
        )
    qa.append(
        (
            "How did the story end?",
            "It ended badly. The child reached for the finest place and lost the good thing meant for everyone, so the last image is not a feast or a song, but a village remembering a foolish choice."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["setting"].tags)
    tags |= set(world.facts["marker"].tags)
    tags |= set(world.facts["response"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="reed_meadow",
        cargo="hymn_book",
        marker="white_stones",
        response="rope",
        child_name="Mara",
        child_gender="girl",
        watcher_name="Ivo",
        watcher_gender="boy",
        elder_type="grandmother",
        child_trait="proud",
        watcher_trait="careful",
        haste=0,
    ),
    StoryParams(
        setting="river_ford",
        cargo="sweet_buns",
        marker="willow_stakes",
        response="rope",
        child_name="Luka",
        child_gender="boy",
        watcher_name="Vera",
        watcher_gender="girl",
        elder_type="grandfather",
        child_trait="bold",
        watcher_trait="steady",
        haste=1,
    ),
    StoryParams(
        setting="marsh_lane",
        cargo="bell_ribbon",
        marker="ash_lines",
        response="plank",
        child_name="Elsa",
        child_gender="girl",
        watcher_name="Niko",
        watcher_gender="boy",
        elder_type="grandmother",
        child_trait="vain",
        watcher_trait="thoughtful",
        haste=2,
    ),
    StoryParams(
        setting="river_ford",
        cargo="hymn_book",
        marker="willow_stakes",
        response="pole",
        child_name="Petar",
        child_gender="boy",
        watcher_name="Mila",
        watcher_gender="girl",
        elder_type="grandfather",
        child_trait="eager",
        watcher_trait="gentle",
        haste=0,
    ),
]


def explain_rejection(setting_id: str, cargo_id: str, marker_id: str) -> str:
    setting = SETTINGS[setting_id]
    cargo = CARGOES[cargo_id]
    marker = MARKERS[marker_id]
    if not cargo.spoilable:
        return f"(No story: {cargo.label} would not be spoiled by mud or water, so the warning loses its force.)"
    if setting.severity <= 0:
        return f"(No story: {setting.label} has no dangerous soft ground, so there is nothing for the segmentation to protect against.)"
    if not marker_fits(setting_id, marker):
        return f"(No story: {marker.label} does not fit {setting.label}, so the segmentation would not make sense there.)"
    return "(No story: this combination does not form a grounded cautionary tale.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{response_id}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"


def outcome_of(params: StoryParams) -> str:
    if params.setting not in SETTINGS or params.response not in RESPONSES:
        raise StoryError("(No story: invalid params for outcome.)")
    return "ruined" if child_saved(RESPONSES[params.response], SETTINGS[params.setting], params.haste) else "lost"


ASP_RULES = r"""
spoil_risk(S, C) :- setting(S), cargo(C), severity(S, V), V > 0, spoilable(C).
marker_fits(S, M) :- marker_works(M, S).
valid(S, C, M) :- spoil_risk(S, C), marker_fits(S, M).

sensible(R) :- response(R), sense(R, V), sense_min(Min), V >= Min.

danger(V + H) :- chosen_setting(S), severity(S, V), haste(H).
saved :- chosen_response(R), power(R, P), danger(D), P >= D.
outcome(ruined) :- saved.
outcome(lost) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("severity", sid, setting.severity))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        if cargo.spoilable:
            lines.append(asp.fact("spoilable", cid))
    for mid, marker in MARKERS.items():
        lines.append(asp.fact("marker", mid))
        for sid in sorted(marker.works_in):
            lines.append(asp.fact("marker_works", mid, sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_response", params.response),
            asp.fact("haste", params.haste),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: valid combo gate matches ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  python only:", sorted(set(valid_combos()) - set(asp_valid_combos())))
        print("  clingo only:", sorted(set(asp_valid_combos()) - set(valid_combos())))

    p_sens = {r.id for r in sensible_responses()}
    a_sens = set(asp_sensible())
    if p_sens == a_sens:
        print(f"OK: sensible responses match ({sorted(p_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(p_sens)} clingo={sorted(a_sens)}")

    cases = list(CURATED)
    for s in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a child ignores a segmentation and ruins a gospel errand."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--haste", type=int, choices=[0, 1, 2], help="how much head start the danger gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cargo and args.marker:
        if (args.setting, args.cargo, args.marker) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.setting, args.cargo, args.marker))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.marker is None or combo[2] == args.marker)
    ]
    if not combos:
        if args.setting and args.cargo and args.marker:
            raise StoryError(explain_rejection(args.setting, args.cargo, args.marker))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cargo_id, marker_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = rng.choice(["girl", "boy"])
    watcher_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    watcher_name = _pick_name(rng, watcher_gender, avoid=child_name)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    child_trait = rng.choice(TRAITS)
    watcher_trait = rng.choice(WATCHER_TRAITS)
    haste = args.haste if args.haste is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        cargo=cargo_id,
        marker=marker_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        watcher_name=watcher_name,
        watcher_gender=watcher_gender,
        elder_type=elder_type,
        child_trait=child_trait,
        watcher_trait=watcher_trait,
        haste=haste,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.cargo not in CARGOES:
        raise StoryError(f"(No story: unknown cargo '{params.cargo}'.)")
    if params.marker not in MARKERS:
        raise StoryError(f"(No story: unknown marker '{params.marker}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if (params.setting, params.cargo, params.marker) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.setting, params.cargo, params.marker))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        SETTINGS[params.setting],
        CARGOES[params.cargo],
        MARKERS[params.marker],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        watcher_name=params.watcher_name,
        watcher_gender=params.watcher_gender,
        elder_type=params.elder_type,
        haste=params.haste,
        child_trait=params.child_trait,
        watcher_trait=params.watcher_trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, cargo, marker) combos:\n")
        for setting_id, cargo_id, marker_id in combos:
            print(f"  {setting_id:12} {cargo_id:12} {marker_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.cargo} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
