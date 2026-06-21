#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/intensive_flitter_true_repetition_bad_ending_fairy.py
================================================================================

A small fairy-tale storyworld about a young fairy who is told to stay on the
true path, sees something beautiful flitter in the dusk, and makes a bad choice.
The world model tracks path-safety, lateness, fear, and the loss caused by
wandering. Every generated story has a clear warning, a repeated temptation, a
turn driven by simulated state, and a bad ending that proves what changed.

Run it
------
python storyworlds/worlds/gpt-5.4/intensive_flitter_true_repetition_bad_ending_fairy.py
python storyworlds/worlds/gpt-5.4/intensive_flitter_true_repetition_bad_ending_fairy.py --all
python storyworlds/worlds/gpt-5.4/intensive_flitter_true_repetition_bad_ending_fairy.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/intensive_flitter_true_repetition_bad_ending_fairy.py --qa --json
python storyworlds/worlds/gpt-5.4/intensive_flitter_true_repetition_bad_ending_fairy.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "mother", "queen", "grandmother", "aunt"}
        male = {"boy", "fairy_boy", "father", "king", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")


@dataclass
class Setting:
    id: str
    place: str
    path_name: str
    marker: str
    wrong_place: str
    hazard: str
    loss_text: str
    late_image: str
    worse_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    motion: str
    shine: str
    strength: int
    call_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    reveals: set[str] = field(default_factory=set)
    power: int = 0
    rescue_text: str = ""
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stray(world: World) -> list[str]:
    child = world.get("child")
    out: list[str] = []
    if child.meters["off_path"] >= THRESHOLD:
        sig = ("stray",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            world.get("task").meters["late"] += 1
            out.append("__stray__")
    return out


def _r_loss(world: World) -> list[str]:
    child = world.get("child")
    bundle = world.get("bundle")
    setting = world.facts["setting_cfg"]
    out: list[str] = []
    if child.meters["off_path"] >= THRESHOLD and bundle.meters["safe"] < THRESHOLD:
        sig = ("loss", setting.id)
        if sig not in world.fired:
            world.fired.add(sig)
            bundle.meters["lost"] += 1
            world.get("task").meters["failed"] += 1
            out.append("__loss__")
    return out


def _r_night(world: World) -> list[str]:
    child = world.get("child")
    task = world.get("task")
    out: list[str] = []
    if task.meters["late"] >= THRESHOLD:
        sig = ("night",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["cold"] += 1
            child.memes["sadness"] += 1
            out.append("__night__")
    return out


CAUSAL_RULES = [
    Rule(name="stray", tag="danger", apply=_r_stray),
    Rule(name="loss", tag="physical", apply=_r_loss),
    Rule(name="night", tag="ending", apply=_r_night),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    return produced


SETTINGS = {
    "moonwood": Setting(
        id="moonwood",
        place="the Moonwood",
        path_name="the silver-fern path",
        marker="silver_fern",
        wrong_place="a ring of whispering thorns",
        hazard="thorns",
        loss_text="The thorns tugged the ribbon loose, and the moon-pears rolled away into the roots.",
        late_image="By the time she found the path again, the moon gate had already swung shut.",
        worse_image="When dawn came, she was still outside the gate, hungry and ashamed beneath a wet fern.",
        tags={"forest", "path"},
    ),
    "reedmere": Setting(
        id="reedmere",
        place="the Reedmere Marsh",
        path_name="the shell-bright causeway",
        marker="shell",
        wrong_place="the soft black edge of the marsh",
        hazard="mud",
        loss_text="The soft mud swallowed one satin shoe, and the dew-cake box slipped from her hand into the reeds.",
        late_image="She limped back too late, and the lantern feast was already over.",
        worse_image="The marsh mist thickened around her, and she spent the whole night shivering on a hummock.",
        tags={"marsh", "path"},
    ),
    "starbank": Setting(
        id="starbank",
        place="the Starbank Meadow",
        path_name="the true ribbon path",
        marker="ribbon",
        wrong_place="a patch of nettles under tall grass",
        hazard="nettles",
        loss_text="The nettles stung her ankles, and the star-seed pouch tore open, spilling every bright seed.",
        late_image="When she reached home at last, the star planting had already begun without her.",
        worse_image="No one found her before moonset, and she cried herself to sleep beside the cold grass.",
        tags={"meadow", "path"},
    ),
}

LURES = {
    "moths": Lure(
        id="moths",
        label="moths",
        motion="began to flitter in little silver loops",
        shine="soft as powdered moonlight",
        strength=1,
        call_line='“Just one step,” the moths seemed to whisper. “Just one step.”',
        tags={"moths", "flitter"},
    ),
    "sparks": Lure(
        id="sparks",
        label="star-sparks",
        motion="began to flitter and wink between the leaves",
        shine="sharp and lively",
        strength=2,
        call_line='“Follow, follow,” the sparks seemed to sing. “Follow, follow.”',
        tags={"lights", "flitter"},
    ),
    "petals": Lure(
        id="petals",
        label="glow-petals",
        motion="began to flitter on the air like tiny lamps",
        shine="golden and sweet",
        strength=2,
        call_line='“Nearer, nearer,” the petals seemed to hum. “Nearer, nearer.”',
        tags={"petals", "flitter"},
    ),
}

GUIDES = {
    "bell": Guide(
        id="bell",
        label="truth-bell",
        phrase="a little truth-bell of moon brass",
        reveals={"silver_fern", "shell"},
        power=1,
        rescue_text="She shook the truth-bell, and its clear note pointed once toward the true path.",
        tags={"bell", "true_path"},
    ),
    "thread": Guide(
        id="thread",
        label="true-thread",
        phrase="a spool of true-thread",
        reveals={"silver_fern", "shell", "ribbon"},
        power=2,
        rescue_text="She unwound the true-thread, and it drew a pale line home through the dark.",
        tags={"thread", "true_path"},
    ),
    "lantern": Guide(
        id="lantern",
        label="dew-lantern",
        phrase="a blue dew-lantern",
        reveals={"ribbon"},
        power=1,
        rescue_text="She lifted the dew-lantern, and its light found one strip of the true ribbon path.",
        tags={"lantern", "true_path"},
    ),
}

FAIRY_NAMES = ["Lina", "Mira", "Tansy", "Pippa", "Wren", "Nia", "Robin", "Bram", "Tobin", "Ash"]
FAIRY_TYPES = {
    "girl": "fairy_girl",
    "boy": "fairy_boy",
}
ELDERS = [
    ("Grandmother Thistle", "grandmother"),
    ("Aunt Willow", "aunt"),
    ("Grandfather Moss", "grandfather"),
]


def guide_fits(setting: Setting, guide: Guide) -> bool:
    return setting.marker in guide.reveals


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for lure_id in LURES:
            for guide_id, guide in GUIDES.items():
                if guide_fits(setting, guide):
                    combos.append((setting_id, lure_id, guide_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    lure: str
    guide: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
    caution: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="moonwood",
        lure="sparks",
        guide="bell",
        child_name="Lina",
        child_gender="girl",
        elder_name="Grandmother Thistle",
        elder_type="grandmother",
        caution="careful",
        delay=1,
    ),
    StoryParams(
        setting="reedmere",
        lure="moths",
        guide="thread",
        child_name="Robin",
        child_gender="boy",
        elder_name="Grandfather Moss",
        elder_type="grandfather",
        caution="curious",
        delay=0,
    ),
    StoryParams(
        setting="starbank",
        lure="petals",
        guide="lantern",
        child_name="Mira",
        child_gender="girl",
        elder_name="Aunt Willow",
        elder_type="aunt",
        caution="eager",
        delay=1,
    ),
    StoryParams(
        setting="moonwood",
        lure="petals",
        guide="thread",
        child_name="Bram",
        child_gender="boy",
        elder_name="Grandmother Thistle",
        elder_type="grandmother",
        caution="restless",
        delay=0,
    ),
]


def explain_rejection(setting: Setting, guide: Guide) -> str:
    return (
        f"(No story: {guide.phrase} cannot reveal the marker for {setting.path_name}. "
        f"In this world, a guide must actually find the true path in {setting.place}.)"
    )


def severity_of(params: StoryParams) -> int:
    return LURES[params.lure].strength + params.delay


def outcome_of(params: StoryParams) -> str:
    guide = GUIDES[params.guide]
    return "late" if guide.power >= severity_of(params) else "lost"


def predict_wandering(setting: Setting, lure: Lure) -> dict:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="fairy_girl"))
    world.add(Entity(id="task", kind="thing", type="task"))
    world.add(Entity(id="bundle", kind="thing", type="bundle"))
    world.facts["setting_cfg"] = setting
    child.meters["off_path"] = 1
    propagate(world, narrate=False)
    return {
        "late": world.get("task").meters["late"] >= THRESHOLD,
        "fear": child.memes["fear"] >= THRESHOLD,
        "hazard": setting.hazard,
        "lure_strength": lure.strength,
    }


def introduce(world: World, child: Entity, elder: Entity, setting: Setting, bundle: Entity) -> None:
    child.memes["duty"] += 1
    world.say(
        f"In {setting.place}, where dusk hung like a violet ribbon, lived a little fairy named {child.id}."
    )
    world.say(
        f"One evening {elder.id} placed {bundle.phrase} in {child.pronoun('possessive')} hands and sent "
        f"{child.pronoun('object')} along {setting.path_name}."
    )


def warning(world: World, child: Entity, elder: Entity, setting: Setting, guide: Guide) -> None:
    child.memes["warned"] += 1
    world.say(
        f'{elder.id} gave {child.pronoun("object")} an intensive warning and {guide.phrase}. '
        f'“Stay on the true path,” {elder.pronoun()} said. '
        f'“True path, true path, true path. Do not chase what shines away from it.”'
    )


def temptation(world: World, child: Entity, setting: Setting, lure: Lure) -> None:
    pred = predict_wandering(setting, lure)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_late"] = pred["late"]
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} promised to be true, and for a while {child.pronoun()} was. "
        f"Then, beside the path, {lure.label} {lure.motion}, {lure.shine}."
    )
    world.say(lure.call_line)


def choice(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} heard the warning once, and twice, and three times in memory. "
        f"Still {child.pronoun()} whispered, “Just one look. Just one look.”"
    )


def stray(world: World, child: Entity, bundle: Entity) -> None:
    child.meters["off_path"] += 1
    bundle.meters["safe"] = 0
    propagate(world, narrate=False)


def loss(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"So off the true path {child.pronoun()} stepped, into {setting.wrong_place}. {setting.loss_text}"
    )


def search(world: World, child: Entity, guide: Guide) -> None:
    child.memes["fear"] += 1
    world.say(
        f"At once the pretty lights flew farther away, and the dark grew bigger. "
        f"{guide.rescue_text}"
    )


def ending_late(world: World, child: Entity, setting: Setting) -> None:
    child.memes["sadness"] += 1
    world.say(
        f"It was enough to bring {child.pronoun('object')} back, but not enough to mend what had been lost. "
        f"{setting.late_image}"
    )
    world.say(
        f"{child.id} stood with empty hands outside the bright windows and understood, too late, why the true path had been called true."
    )


def ending_lost(world: World, child: Entity, setting: Setting) -> None:
    child.meters["cold"] += 1
    child.memes["sadness"] += 1
    world.say(
        f"But the guide could only show a little, and the night had grown too deep. {setting.worse_image}"
    )
    world.say(
        f"No feast-song reached {child.id} there, only the small sound of {child.pronoun('possessive')} own crying and the leaves answering back."
    )


def tell(
    setting: Setting,
    lure: Lure,
    guide: Guide,
    *,
    child_name: str,
    child_gender: str,
    elder_name: str,
    elder_type: str,
    caution: str,
    delay: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=FAIRY_TYPES[child_gender],
            label=child_name,
            role="child",
            attrs={"caution": caution},
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            label=elder_name,
            role="elder",
        )
    )
    bundle_label = {
        "moonwood": "a willow basket of moon-pears",
        "reedmere": "a little box of dew-cakes",
        "starbank": "a stitched pouch of star-seeds",
    }[setting.id]
    bundle = world.add(
        Entity(
            id="bundle",
            kind="thing",
            type="bundle",
            label="bundle",
            phrase=bundle_label,
            role="bundle",
        )
    )
    bundle.meters["safe"] = 1
    task = world.add(Entity(id="task", kind="thing", type="task", label="errand"))
    world.facts["setting_cfg"] = setting
    world.facts["lure_cfg"] = lure
    world.facts["guide_cfg"] = guide

    introduce(world, child, elder, setting, bundle)
    warning(world, child, elder, setting, guide)

    world.para()
    temptation(world, child, setting, lure)
    choice(world, child)
    stray(world, child, bundle)
    loss(world, child, setting)

    task.meters["late"] += delay
    propagate(world, narrate=False)

    world.para()
    search(world, child, guide)
    if outcome_of(
        StoryParams(
            setting=setting.id,
            lure=lure.id,
            guide=guide.id,
            child_name=child_name,
            child_gender=child_gender,
            elder_name=elder_name,
            elder_type=elder_type,
            caution=caution,
            delay=delay,
        )
    ) == "late":
        ending_late(world, child, setting)
    else:
        ending_lost(world, child, setting)

    world.facts.update(
        child=child,
        elder=elder,
        bundle=bundle,
        task=task,
        setting=setting,
        lure=lure,
        guide=guide,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                lure=lure.id,
                guide=guide.id,
                child_name=child_name,
                child_gender=child_gender,
                elder_name=elder_name,
                elder_type=elder_type,
                caution=caution,
                delay=delay,
            )
        ),
        repeated_warning="True path, true path, true path.",
        stepped_off=child.meters["off_path"] >= THRESHOLD,
        loss=bundle.meters["lost"] >= THRESHOLD,
        late=task.meters["late"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "true_path": [
        (
            "What does a true path mean in a fairy tale?",
            "A true path is the safe and right way to go. In a fairy tale, leaving it often means trouble begins.",
        )
    ],
    "flitter": [
        (
            "What does flitter mean?",
            "Flitter means to move lightly and quickly, with little fluttering turns. Tiny wings, leaves, or glowing things can flitter in the air.",
        )
    ],
    "moths": [
        (
            "Why do moths fly toward light?",
            "Moths use light to help them move through the dark. Bright light can confuse them and make them circle close to it.",
        )
    ],
    "lights": [
        (
            "Why can mysterious lights be dangerous in stories?",
            "They can tempt someone to leave a safe place and go somewhere confusing. The danger comes from following them instead of following good advice.",
        )
    ],
    "thread": [
        (
            "What can a thread help someone do?",
            "A thread can mark a way so someone can find the path again. In stories, it often stands for memory and careful thinking.",
        )
    ],
    "bell": [
        (
            "Why might a bell be useful in the dark?",
            "A clear bell sound can help someone notice direction when they cannot see well. It is a simple signal to follow.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so people can see where they are going. Good light helps you stay on the safe path.",
        )
    ],
    "forest": [
        (
            "Why is it easy to get lost in the woods at dusk?",
            "As the light fades, trees and paths start to look the same. That makes it hard to tell which way is safe.",
        )
    ],
    "marsh": [
        (
            "Why is a marsh a hard place to walk in?",
            "A marsh has soft wet ground that can pull at shoes and slow you down. Reeds and mist can also hide the path.",
        )
    ],
    "meadow": [
        (
            "Why can tall grass hide a path?",
            "Tall grass bends over the ground and covers what is underneath. A narrow path can disappear if you stop watching for it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["true_path", "flitter", "moths", "lights", "thread", "bell", "lantern", "forest", "marsh", "meadow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    lure = f["lure"]
    guide = f["guide"]
    return [
        'Write a fairy tale for a 3-to-5-year-old that uses the words "intensive", "flitter", and "true", and ends badly.',
        f"Tell a fairy-tale story where {child.id} is warned by {elder.id} to stay on {setting.path_name}, but {lure.label} flitter in the dusk and lure {child.pronoun('object')} away.",
        f"Write a repetitive cautionary tale where the warning 'True path, true path, true path' is repeated, a child ignores it, and {guide.label} helps only a little in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    lure = f["lure"]
    guide = f["guide"]
    bundle = f["bundle"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little fairy named {child.id}. {elder.id} sends {child.pronoun('object')} along {setting.path_name} with {bundle.phrase}.",
        ),
        (
            f"What warning did {elder.id} give {child.id}?",
            f"{elder.id} told {child.id} to stay on the true path and not chase shining things away from it. The warning was repeated again and again so it would stay in {child.pronoun('possessive')} mind.",
        ),
        (
            f"What tempted {child.id} off the path?",
            f"{lure.label.capitalize()} began to flitter beside the path and looked beautiful in the dusk. Their pretty motion made the wrong way seem exciting for a moment.",
        ),
    ]
    if f.get("loss"):
        qa.append(
            (
                f"What went wrong when {child.id} stepped away from the path?",
                f"{child.id} wandered into {setting.wrong_place}, and the errand bundle was lost. That happened because {child.pronoun()} chose the shining lure instead of the safe road.",
            )
        )
    if f["outcome"] == "late":
        qa.append(
            (
                "Did the guide fix everything?",
                f"No. {guide.label.capitalize()} helped {child.id} get back, but not in time to save the errand or the evening. The path was found again, yet the lost moment stayed lost.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly with {child.id} arriving too late. Standing outside the bright place showed exactly what {child.pronoun()} had missed by leaving the true path.",
            )
        )
    else:
        qa.append(
            (
                "Did the guide fix everything?",
                f"No. {guide.label.capitalize()} could help only a little, and the night had already grown too deep. Because the wandering lasted too long, {child.id} stayed out in the dark until dawn.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended badly, with {child.id} cold, lost, and ashamed instead of safe at the feast. The ending proves how a small wrong step became a much bigger trouble.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["guide"].tags) | set(f["lure"].tags) | set(f["setting"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:16} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(S, G) :- setting(S), guide(G), marker_of(S, M), reveals(G, M).
valid(S, L, G) :- setting(S), lure(L), fits(S, G).

severity(V) :- chosen_lure(L), strength(L, LS), delay(D), V = LS + D.
late :- chosen_guide(G), power(G, P), severity(V), P >= V.
lost :- chosen_guide(G), power(G, P), severity(V), P < V.

outcome(late) :- late.
outcome(lost) :- lost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("marker_of", sid, setting.marker))
    for lid, lure in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("strength", lid, lure.strength))
    for gid, guide in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("power", gid, guide.power))
        for marker in sorted(guide.reveals):
            lines.append(asp.fact("reveals", gid, marker))
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
            asp.fact("chosen_lure", params.lure),
            asp.fact("chosen_guide", params.guide),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke = generate(CURATED[0])
        if not smoke.story or "true path" not in smoke.story.lower():
            raise StoryError("smoke test story missing expected content")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a young fairy leaves the true path after a repeated warning."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra lateness after wandering")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.guide:
        setting = SETTINGS[args.setting]
        guide = GUIDES[args.guide]
        if not guide_fits(setting, guide):
            raise StoryError(explain_rejection(setting, guide))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.lure is None or combo[1] == args.lure)
        and (args.guide is None or combo[2] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, lure_id, guide_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(FAIRY_NAMES)
    elder_name, elder_type = rng.choice(ELDERS)
    if args.elder:
        elder_name = args.elder
        elder_type = "grandmother"
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    caution = rng.choice(["careful", "restless", "curious", "eager"])
    return StoryParams(
        setting=setting_id,
        lure=lure_id,
        guide=guide_id,
        child_name=child_name,
        child_gender=gender,
        elder_name=elder_name,
        elder_type=elder_type,
        caution=caution,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.child_gender not in FAIRY_TYPES:
        raise StoryError(f"(Unknown gender: {params.child_gender})")

    setting = SETTINGS[params.setting]
    guide = GUIDES[params.guide]
    if not guide_fits(setting, guide):
        raise StoryError(explain_rejection(setting, guide))

    world = tell(
        setting,
        LURES[params.lure],
        guide,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        caution=params.caution,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (setting, lure, guide) combos:\n")
        for setting, lure, guide in combos:
            print(f"  {setting:10} {lure:8} {guide}")
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
            header = f"### {p.child_name}: {p.setting}, {p.lure}, {p.guide} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
