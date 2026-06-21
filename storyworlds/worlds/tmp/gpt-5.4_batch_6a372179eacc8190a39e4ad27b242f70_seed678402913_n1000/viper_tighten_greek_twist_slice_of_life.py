#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/viper_tighten_greek_twist_slice_of_life.py
=====================================================================

A standalone story world for a small slice-of-life "false alarm" tale with a
twist: a child spots something twisty and fears it is a viper, but a calm helper
checks the scene and reveals an ordinary household object instead.

The world model prefers grounded, everyday misunderstandings:
- the setting offers a plausible coiled object,
- the child has a reason to be near it,
- the helper uses a sensible check,
- and the ending proves what changed in the room and in the child's feelings.

Required seed words appear naturally in the stories:
- "viper"
- "tighten"
- "greek"

Run it
------
    python storyworlds/worlds/gpt-5.4/viper_tighten_greek_twist_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/viper_tighten_greek_twist_slice_of_life.py --setting kitchen --object apron_tie
    python storyworlds/worlds/gpt-5.4/viper_tighten_greek_twist_slice_of_life.py --setting library --object garden_hose
    python storyworlds/worlds/gpt-5.4/viper_tighten_greek_twist_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/viper_tighten_greek_twist_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/viper_tighten_greek_twist_slice_of_life.py --verify
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

# Make shared result containers importable when this nested script is run directly.
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
    movable: bool = True
    coiled: bool = False
    long: bool = False
    can_hiss: bool = False
    safe_to_touch: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher", "librarian", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
            "teacher": "teacher",
            "librarian": "librarian",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    event: str
    room_detail: str
    floor_spot: str
    object_ids: set[str] = field(default_factory=set)
    helper_types: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class OrdinaryObject:
    id: str
    label: str
    phrase: str
    where: str
    fear_shape: str
    reveal_text: str
    after_use: str
    coiled: bool = True
    long: bool = True
    can_hiss: bool = False
    safe_to_touch: bool = True
    needs_tighten: bool = False
    tighten_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class CheckMethod:
    id: str
    sense: int
    text: str
    qa_text: str
    reveals_by_touch: bool = True
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


def _r_false_alarm(world: World) -> list[str]:
    viewer = world.get("child")
    thing = world.get("object")
    out: list[str] = []
    if viewer.memes["alarm"] < THRESHOLD:
        return out
    if not thing.coiled:
        return out
    sig = ("false_alarm", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    viewer.memes["fear"] += 1
    world.get("room").meters["pause"] += 1
    out.append("__alarm__")
    return out


def _r_relief(world: World) -> list[str]:
    viewer = world.get("child")
    thing = world.get("object")
    out: list[str] = []
    if thing.meters["identified"] < THRESHOLD:
        return out
    sig = ("relief", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    viewer.memes["fear"] = 0.0
    viewer.memes["relief"] += 1
    viewer.memes["embarrassed"] += 1
    world.get("room").meters["pause"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="false_alarm", tag="social", apply=_r_false_alarm),
    Rule(name="relief", tag="social", apply=_r_relief),
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


def object_fits_setting(setting: Setting, obj: OrdinaryObject) -> bool:
    return obj.id in setting.object_ids


def helper_fits_setting(setting: Setting, helper_type: str) -> bool:
    return helper_type in setting.helper_types


def sensible_methods() -> list[CheckMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def child_needs_tightening(obj: OrdinaryObject) -> bool:
    return obj.needs_tighten


def predict_false_alarm(obj: OrdinaryObject) -> bool:
    return obj.coiled and obj.long


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for object_id, obj in OBJECTS.items():
            if not object_fits_setting(setting, obj):
                continue
            if not predict_false_alarm(obj):
                continue
            for helper_type in HELPER_TYPES:
                if helper_fits_setting(setting, helper_type):
                    combos.append((setting_id, object_id, helper_type))
    return combos


def introduce(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"After school, {child.id} went with {helper.label_word} to {setting.place} for {setting.event}. "
        f"{setting.room_detail}"
    )
    world.say(
        f"{child.id} was excited because the table held paper olives, blue napkins, and a little sign that said Greek Day."
    )


def setup_task(world: World, child: Entity, helper: Entity, obj: OrdinaryObject) -> None:
    if obj.needs_tighten:
        child.memes["helpful"] += 1
        world.say(
            f'{helper.label_word.capitalize()} asked {child.id} to carry a tray while {helper.pronoun()} fixed {obj.phrase}. '
            f'"I just need to tighten it a little first," {helper.pronoun()} said.'
        )
    else:
        child.memes["curious"] += 1
        world.say(
            f"{child.id} wandered a step ahead, looking at the decorations and trying not to bump anything."
        )


def spot_object(world: World, child: Entity, obj: OrdinaryObject, setting: Setting) -> None:
    child.memes["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} noticed {obj.phrase} {obj.where}, {obj.fear_shape}."
    )
    world.say(
        f"For one startled second, it looked exactly like a curled little viper."
    )


def panic(world: World, child: Entity) -> None:
    world.say(
        f'"Viper!" {child.id} squeaked, and {child.pronoun()} jumped back so fast that the room seemed to stop with {child.pronoun("object")}.'
    )


def calm_helper(world: World, helper: Entity, child: Entity, obj: OrdinaryObject) -> None:
    child.memes["trust"] += 1
    helper.memes["calm"] += 1
    detail = ""
    if obj.needs_tighten and obj.tighten_text:
        detail = f" {helper.pronoun().capitalize()} still had one hand on it because {obj.tighten_text}."
    world.say(
        f'{helper.label_word.capitalize()} looked where {child.id} was pointing and did not laugh.{detail}'
    )
    world.say(
        f'"Let\'s stand still and look carefully first," {helper.pronoun()} said.'
    )


def inspect(world: World, helper: Entity, obj: Entity, method: CheckMethod, obj_cfg: OrdinaryObject) -> None:
    obj.meters["checked"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {method.text.format(label=obj_cfg.label)}."
    )


def reveal(world: World, child: Entity, helper: Entity, obj: Entity, obj_cfg: OrdinaryObject, setting: Setting) -> None:
    obj.meters["identified"] += 1
    propagate(world, narrate=False)
    world.say(
        f"It did not slither at all. It was only {obj_cfg.reveal_text}."
    )
    if obj_cfg.needs_tighten and obj_cfg.tighten_text:
        world.say(
            f'{helper.label_word.capitalize()} smiled. "See? I was only trying to tighten it before we started."'
        )
    else:
        world.say(
            f'{child.id} blinked, then let out a tiny breath {child.pronoun()} had been holding.'
        )
    world.say(
        f"The twist made {child.id} feel silly for a moment, but mostly glad."
    )
    world.say(
        f"Soon {obj_cfg.after_use} while the Greek Day room felt ordinary and friendly again."
    )


def closing(world: World, child: Entity, helper: Entity, obj_cfg: OrdinaryObject) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} came closer this time and helped without shaking."
    )
    if obj_cfg.needs_tighten:
        world.say(
            f"After that, the only thing that had to tighten was {obj_cfg.label}, not anyone's scared shoulders."
        )
    else:
        world.say(
            f"After that, the scary shape was just part of an ordinary afternoon."
        )


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the church kitchen",
        event="the neighborhood Greek bake sale",
        room_detail="Steam from warm trays drifted through the bright room, and chairs scraped softly on the floor.",
        floor_spot="by the folding table",
        object_ids={"apron_tie", "extension_cord"},
        helper_types={"mother", "aunt"},
        tags={"kitchen", "greek"},
    ),
    "library": Setting(
        id="library",
        place="the school library",
        event="Greek story night",
        room_detail="The rug smelled like clean paper, and a row of blue paper columns stood by the wall.",
        floor_spot="near the reading rug",
        object_ids={"projector_cable", "backpack_strap"},
        helper_types={"teacher", "librarian"},
        tags={"library", "greek"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard",
        event="a small Greek family dinner",
        room_detail="String lights blinked over the tables, and someone was setting out lemon slices in little bowls.",
        floor_spot="beside a flowerpot",
        object_ids={"garden_hose", "apron_tie"},
        helper_types={"father", "uncle"},
        tags={"courtyard", "greek"},
    ),
}

OBJECTS = {
    "apron_tie": OrdinaryObject(
        id="apron_tie",
        label="apron string",
        phrase="a striped apron string",
        where="dangling in a loose coil from a chair",
        fear_shape="greenish in the shadow and thin enough to fool tired eyes",
        reveal_text="the cook's apron string",
        after_use="the trays were carried in and the grown-up tied the apron snugly",
        needs_tighten=True,
        tighten_text="the apron had come loose",
        tags={"apron", "tighten"},
    ),
    "extension_cord": OrdinaryObject(
        id="extension_cord",
        label="extension cord",
        phrase="a green extension cord",
        where="looped under the snack table",
        fear_shape="bent in two soft circles with one end hidden behind a box",
        reveal_text="the cord for the warm pastry light",
        after_use="the light over the pastries glowed on, and everyone kept setting out food",
        needs_tighten=False,
        tags={"cord", "light"},
    ),
    "projector_cable": OrdinaryObject(
        id="projector_cable",
        label="projector cable",
        phrase="a gray projector cable",
        where="curled beside the story rug",
        fear_shape="twisted just enough to look alive from far away",
        reveal_text="the cable from the projector to the little speaker",
        after_use="the pictures for Greek story night flickered onto the wall",
        needs_tighten=False,
        tags={"cable", "school"},
    ),
    "backpack_strap": OrdinaryObject(
        id="backpack_strap",
        label="backpack strap",
        phrase="a green backpack strap",
        where="hanging off a low chair",
        fear_shape="curving over itself in a sleepy loop",
        reveal_text="a backpack strap with a shiny zipper pull",
        after_use="the backpack was lifted away, and the reading rug was clear again",
        needs_tighten=True,
        tighten_text="the strap buckle needed a quick tighten",
        tags={"backpack", "tighten"},
    ),
    "garden_hose": OrdinaryObject(
        id="garden_hose",
        label="garden hose",
        phrase="a thin green garden hose",
        where="resting in a coil beside the flowerpot",
        fear_shape="dusty green and half hidden by leaves",
        reveal_text="the hose for watering the basil pots",
        after_use="the basil got a drink and the tables were set for dinner",
        needs_tighten=False,
        tags={"hose", "garden"},
    ),
}

METHODS = {
    "look_closer": CheckMethod(
        id="look_closer",
        sense=3,
        text="leaned a little closer and followed the shape of the {label} with careful eyes",
        qa_text="looked closely first",
        tags={"look"},
    ),
    "tap_with_spoon": CheckMethod(
        id="tap_with_spoon",
        sense=2,
        text="used a long wooden spoon to nudge the {label} gently from far away",
        qa_text="nudged it gently with a spoon from a safe distance",
        tags={"distance"},
    ),
    "lift_with_towel": CheckMethod(
        id="lift_with_towel",
        sense=2,
        text="picked up the end of the {label} with a folded dish towel and held it up",
        qa_text="lifted it carefully with a towel",
        tags={"towel"},
    ),
    "poke_with_foot": CheckMethod(
        id="poke_with_foot",
        sense=1,
        text="reached out with a shoe and poked the {label}",
        qa_text="poked it with a shoe",
        tags={"bad"},
    ),
}

HELPER_TYPES = ["mother", "father", "teacher", "librarian", "aunt", "uncle"]
GIRL_NAMES = ["Lina", "Maya", "Nora", "Sofia", "Ella", "Lucy", "Zoe", "Anna"]
BOY_NAMES = ["Theo", "Leo", "Max", "Ben", "Sam", "Niko", "Eli", "Jack"]
TRAITS = ["careful", "curious", "jumpy", "thoughtful", "shy", "helpful"]


@dataclass
class StoryParams:
    setting: str
    object: str
    helper: str
    method: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


def pair_child_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(GIRL_NAMES)
    return rng.choice(BOY_NAMES)


def tell(
    setting: Setting,
    obj_cfg: OrdinaryObject,
    helper_type: str,
    method: CheckMethod,
    child_name: str = "Lina",
    child_gender: str = "girl",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        phrase="the helper",
        role="helper",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=setting.place,
        phrase=setting.place,
        movable=False,
    ))
    obj = world.add(Entity(
        id="object",
        kind="thing",
        type="object",
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        coiled=obj_cfg.coiled,
        long=obj_cfg.long,
        can_hiss=obj_cfg.can_hiss,
        safe_to_touch=obj_cfg.safe_to_touch,
        tags=set(obj_cfg.tags),
    ))

    introduce(world, child, helper, setting)
    setup_task(world, child, helper, obj_cfg)

    world.para()
    spot_object(world, child, obj_cfg, setting)
    panic(world, child)
    calm_helper(world, helper, child, obj_cfg)

    world.para()
    inspect(world, helper, obj, method, obj_cfg)
    reveal(world, child, helper, obj, obj_cfg, setting)
    closing(world, child, helper, obj_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        object=obj,
        object_cfg=obj_cfg,
        setting=setting,
        method=method,
        false_alarm=True,
        twist=True,
        tighten_used=obj_cfg.needs_tighten,
        outcome="revealed",
    )
    return world


KNOWLEDGE = {
    "viper": [
        (
            "What is a viper?",
            "A viper is a kind of snake. Real snakes should be left alone, and a grown-up should check from a safe distance."
        )
    ],
    "greek": [
        (
            "What does Greek Day mean?",
            "Greek Day is a day when people share food, stories, music, or decorations from Greek culture. It can happen at school, church, or at home with family."
        )
    ],
    "tighten": [
        (
            "What does tighten mean?",
            "To tighten something means to pull or fix it so it is more snug and less loose. People might tighten a strap, a string, or an apron so it stays in place."
        )
    ],
    "cord": [
        (
            "Why can a cord look scary from far away?",
            "A cord can bend and curl on the floor, so from far away it may look like something alive. Looking carefully helps your brain notice the real shape."
        )
    ],
    "calm": [
        (
            "Why is it smart to stand still before checking something scary?",
            "Standing still helps you look carefully and stops a frightened mistake from getting bigger. Calm checking gives your eyes and brain time to work together."
        )
    ],
}

KNOWLEDGE_ORDER = ["viper", "greek", "tighten", "cord", "calm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    obj_cfg = f["object_cfg"]
    helper = f["helper"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "viper," "tighten," and "greek," and ends with a gentle twist.',
        f"Tell a small everyday story where {child.label} mistakes {obj_cfg.phrase} for a viper at {setting.event}, but {helper.label_word} checks calmly and reveals the truth.",
        f"Write a child-friendly false-alarm story set at {setting.place} during a Greek-themed event, where fear shrinks after someone looks carefully.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obj = f["object_cfg"]
    setting = f["setting"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, who got scared for a moment, and {helper.label_word} who helped check the room calmly."
        ),
        (
            "Why did the child think there was a viper?",
            f"{child.label} saw {obj.phrase} in shadow, curled up in a way that looked alive. The shape was twisty and surprising, so fear filled in the wrong answer before a careful look did."
        ),
        (
            "What was the twist in the story?",
            f"The scary viper was not a snake at all. It turned out to be {obj.reveal_text}, so the big fright came from an ordinary object."
        ),
        (
            "How did the helper solve the problem?",
            f"{helper.label_word.capitalize()} {method.qa_text} and checked before anyone rushed closer. That calm method helped reveal the truth and made the fear go away."
        ),
    ]
    if obj.needs_tighten:
        qa.append(
            (
                "Where did the word tighten fit into the story?",
                f"The grown-up was already trying to tighten {obj.label} before the misunderstanding happened. That detail matters because it helps explain why the object was hanging loose and looked strange."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended in an ordinary, safe way at {setting.event}. Once the object was understood, {child.label} could help again and the Greek-themed afternoon felt warm instead of scary."
        )
    )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"viper", "greek", "calm"}
    if f.get("tighten_used"):
        tags.add("tighten")
    if "cord" in f["object_cfg"].tags or "cable" in f["object_cfg"].tags or "hose" in f["object_cfg"].tags:
        tags.add("cord")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("movable", ent.movable),
            ("coiled", ent.coiled),
            ("long", ent.long),
            ("can_hiss", ent.can_hiss),
            ("safe_to_touch", ent.safe_to_touch),
        ) if on and name != "movable"]
        if flags:
            bits.append(f"flags={flags}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="kitchen",
        object="apron_tie",
        helper="aunt",
        method="look_closer",
        child_name="Maya",
        child_gender="girl",
        trait="helpful",
    ),
    StoryParams(
        setting="library",
        object="projector_cable",
        helper="teacher",
        method="tap_with_spoon",
        child_name="Theo",
        child_gender="boy",
        trait="curious",
    ),
    StoryParams(
        setting="courtyard",
        object="garden_hose",
        helper="father",
        method="look_closer",
        child_name="Nora",
        child_gender="girl",
        trait="jumpy",
    ),
    StoryParams(
        setting="library",
        object="backpack_strap",
        helper="librarian",
        method="lift_with_towel",
        child_name="Leo",
        child_gender="boy",
        trait="shy",
    ),
]


def explain_rejection(setting: Setting, obj: OrdinaryObject, helper: str) -> str:
    if not object_fits_setting(setting, obj):
        return (
            f"(No story: {obj.label} does not belong naturally in {setting.place}, so the scene would feel forced.)"
        )
    if not predict_false_alarm(obj):
        return (
            f"(No story: {obj.label} does not make a plausible snake-shaped mistake here, so there is no honest false alarm.)"
        )
    if not helper_fits_setting(setting, helper):
        return (
            f"(No story: a {helper} is not the sensible helper for this setting.)"
        )
    return "(No story: this combination is not supported.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
% Reasonableness gate.
valid(S, O, H) :- setting(S), object(O), helper(H),
                  in_setting(S, O), helper_ok(S, H),
                  coiled(O), long(O).

sensible_method(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.

% Story outcome for one chosen scenario.
false_alarm :- chosen_object(O), coiled(O), long(O).
revealed    :- chosen_method(M), sensible_method(M), false_alarm.
outcome(revealed) :- revealed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for object_id in sorted(setting.object_ids):
            lines.append(asp.fact("in_setting", setting_id, object_id))
        for helper in sorted(setting.helper_types):
            lines.append(asp.fact("helper_ok", setting_id, helper))
    for object_id, obj in OBJECTS.items():
        lines.append(asp.fact("object", object_id))
        if obj.coiled:
            lines.append(asp.fact("coiled", object_id))
        if obj.long:
            lines.append(asp.fact("long", object_id))
    for helper in HELPER_TYPES:
        lines.append(asp.fact("helper", helper))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_method/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_object", params.object),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if METHODS[params.method].sense < SENSE_MIN:
        return "?"
    if not predict_false_alarm(OBJECTS[params.object]):
        return "?"
    return "revealed"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    _ = sample.to_json()


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sense = set(asp_sensible_methods())
    p_sense = {m.id for m in sensible_methods()}
    if c_sense == p_sense:
        print(f"OK: sensible methods match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test story generation passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child mistakes an ordinary object for a viper, then a calm check reveals the twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPER_TYPES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.object and args.helper:
        setting = SETTINGS[args.setting]
        obj = OBJECTS[args.object]
        if not (object_fits_setting(setting, obj) and helper_fits_setting(setting, args.helper) and predict_false_alarm(obj)):
            raise StoryError(explain_rejection(setting, obj, args.helper))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.object is None or combo[1] == args.object)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        if args.setting and args.object and not args.helper:
            raise StoryError(explain_rejection(SETTINGS[args.setting], OBJECTS[args.object], next(iter(SETTINGS[args.setting].helper_types))))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, object_id, helper = rng.choice(sorted(combos))
    method = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or pair_child_name(rng, child_gender)
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        object=object_id,
        helper=helper,
        method=method,
        child_name=child_name,
        child_gender=child_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.object not in OBJECTS:
        raise StoryError(f"(Unknown object: {params.object})")
    if params.helper not in HELPER_TYPES:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if not object_fits_setting(SETTINGS[params.setting], OBJECTS[params.object]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], OBJECTS[params.object], params.helper))
    if not helper_fits_setting(SETTINGS[params.setting], params.helper):
        raise StoryError(explain_rejection(SETTINGS[params.setting], OBJECTS[params.object], params.helper))

    world = tell(
        setting=SETTINGS[params.setting],
        obj_cfg=OBJECTS[params.object],
        helper_type=params.helper,
        method=METHODS[params.method],
        child_name=params.child_name,
        child_gender=params.child_gender,
        trait=params.trait,
    )

    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    story = sample.story.replace("helper", sample.params.helper)
    print(story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_method/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        print(f"{len(combos)} compatible (setting, object, helper) combos:\n")
        for setting_id, object_id, helper in combos:
            print(f"  {setting_id:10} {object_id:16} {helper}")
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
            header = f"### {p.child_name}: {p.object} at {p.setting} ({p.helper}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
