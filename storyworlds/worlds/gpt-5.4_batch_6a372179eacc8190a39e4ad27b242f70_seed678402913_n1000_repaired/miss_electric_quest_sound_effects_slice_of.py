#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/miss_electric_quest_sound_effects_slice_of.py
=========================================================================

A standalone storyworld for a small slice-of-life quest: a child wants to show
an electric toy to Miss June next door, but the battery pack has gone missing.
The child and a helper search the home, follow a little sound clue, and bring
the toy back to life.

The world model is intentionally small and concrete:
- one child hero
- one helper
- one electric device
- one missing battery pack
- one real hiding place and one wrong lead
- one retrieval method that must suit the hiding place

The simulation tracks simple physical meters ("missing", "found", "ready",
"running") and emotional memes ("worry", "hope", "joy"). Prose is rendered
from those state changes rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/miss_electric_quest_sound_effects_slice_of.py
    python storyworlds/worlds/gpt-5.4/miss_electric_quest_sound_effects_slice_of.py --device train
    python storyworlds/worlds/gpt-5.4/miss_electric_quest_sound_effects_slice_of.py --place top_shelf --method broom
    python storyworlds/worlds/gpt-5.4/miss_electric_quest_sound_effects_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/miss_electric_quest_sound_effects_slice_of.py --qa --json
    python storyworlds/worlds/gpt-5.4/miss_electric_quest_sound_effects_slice_of.py --verify
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

# Make the shared result containers importable when this script is run directly
# from its nested directory (.../storyworlds/worlds/gpt-5.4/).
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
        female = {"girl", "mother", "sister", "woman"}
        male = {"boy", "father", "brother", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "sister": "sister", "brother": "brother"}.get(
            self.type, self.label or self.type
        )


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    demo_line: str
    start_sound: str
    move_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    access: str
    search_sound: str
    clue_sound: str
    text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    works_on: set[str]
    action_text: str
    retrieve_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_missing_worry(world: World) -> list[str]:
    hero = world.entities.get("hero")
    device = world.entities.get("device")
    part = world.entities.get("battery")
    if hero is None or device is None or part is None:
        return []
    if device.meters["needs_power"] < THRESHOLD or part.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["hope"] += 1
    return []


def _r_ready(world: World) -> list[str]:
    device = world.entities.get("device")
    part = world.entities.get("battery")
    if device is None or part is None:
        return []
    if part.meters["inserted"] < THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["ready"] += 1
    device.meters["needs_power"] = 0.0
    return []


def _r_running(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    device = world.entities.get("device")
    if hero is None or helper is None or device is None:
        return []
    if device.meters["ready"] < THRESHOLD or device.meters["switched_on"] < THRESHOLD:
        return []
    sig = ("running",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["running"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="running", tag="physical", apply=_r_running),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


DEVICES = {
    "train": Device(
        id="train",
        label="electric train",
        phrase="a little electric train with a silver roof",
        demo_line="wanted to send the train around the rug like a tiny parade",
        start_sound="Whirr-whirr! Clickety-click!",
        move_line="The train zipped around the rug in a bright oval track",
        tags={"train", "electric", "battery"},
    ),
    "keyboard": Device(
        id="keyboard",
        label="electric keyboard",
        phrase="a small electric keyboard with rainbow buttons",
        demo_line="wanted to play a short hello song on the keyboard",
        start_sound="Plink-plink! Bwee-bwee!",
        move_line="The keyboard sang a happy tune across the room",
        tags={"keyboard", "electric", "battery"},
    ),
    "dinosaur": Device(
        id="dinosaur",
        label="electric dinosaur",
        phrase="a waddly electric dinosaur with blinking eyes",
        demo_line="wanted to make the dinosaur stomp across the floor",
        start_sound="Brrr-roar! Tap-tap!",
        move_line="The dinosaur stomped in a proud circle near the table legs",
        tags={"dinosaur", "electric", "battery"},
    ),
}

PLACES = {
    "toy_bin": Place(
        id="toy_bin",
        label="toy bin",
        phrase="the deep toy bin",
        access="pile",
        search_sound="swish-swish",
        clue_sound="clink",
        text="between soft blocks and a red plastic shovel",
        tags={"toy_bin", "search"},
    ),
    "coat_pocket": Place(
        id="coat_pocket",
        label="coat pocket",
        phrase="the pocket of the hallway coat",
        access="pocket",
        search_sound="pat-pat",
        clue_sound="tik-tik",
        text="inside a warm blue coat hanging by the door",
        tags={"coat", "pocket", "search"},
    ),
    "top_shelf": Place(
        id="top_shelf",
        label="top shelf",
        phrase="the high top shelf in the hall closet",
        access="high",
        search_sound="tap-tap",
        clue_sound="rattle",
        text="inside a little box on the top shelf",
        tags={"shelf", "search"},
    ),
    "under_sofa": Place(
        id="under_sofa",
        label="under the sofa",
        phrase="the shadow under the sofa",
        access="deep",
        search_sound="thump-thump",
        clue_sound="ting",
        text="just past the dust bunnies under the sofa",
        tags={"sofa", "search"},
    ),
}

METHODS = {
    "careful_sort": Method(
        id="careful_sort",
        label="careful sorting",
        works_on={"pile"},
        action_text="sorted slowly with both hands",
        retrieve_text="lifted one toy after another until the battery pack showed itself",
        tags={"careful_search"},
    ),
    "pat_pockets": Method(
        id="pat_pockets",
        label="patting pockets",
        works_on={"pocket"},
        action_text="patted the pocket from the outside first",
        retrieve_text="slipped a hand inside and found the battery pack",
        tags={"pocket"},
    ),
    "step_stool": Method(
        id="step_stool",
        label="a step stool",
        works_on={"high"},
        action_text="brought over the step stool and climbed one safe step",
        retrieve_text="reached the little box and picked up the battery pack",
        tags={"stool"},
    ),
    "broom": Method(
        id="broom",
        label="a broom",
        works_on={"deep"},
        action_text="lay flat and reached in with the broom handle",
        retrieve_text="drew the battery pack out from the shadow",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
SIBLING_GIRL_NAMES = ["Lina", "Nina", "Ruby", "Tess", "Molly", "Ivy"]
SIBLING_BOY_NAMES = ["Milo", "Arlo", "Ned", "Pip", "Toby", "Gus"]


def valid_combo(device_id: str, place_id: str, method_id: str) -> bool:
    if device_id not in DEVICES or place_id not in PLACES or method_id not in METHODS:
        return False
    place = PLACES[place_id]
    method = METHODS[method_id]
    return place.access in method.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for device_id in sorted(DEVICES):
        for place_id in sorted(PLACES):
            for method_id in sorted(METHODS):
                if valid_combo(device_id, place_id, method_id):
                    combos.append((device_id, place_id, method_id))
    return combos


@dataclass
class StoryParams:
    device: str
    place: str
    method: str
    hero_name: str
    hero_gender: str
    helper_role: str
    helper_name: str
    seed: Optional[int] = None


def helper_type_name(helper_role: str, rng: random.Random) -> tuple[str, str]:
    if helper_role == "mother":
        return "mother", "Mom"
    if helper_role == "father":
        return "father", "Dad"
    if helper_role == "sister":
        return "sister", rng.choice(SIBLING_GIRL_NAMES)
    if helper_role == "brother":
        return "brother", rng.choice(SIBLING_BOY_NAMES)
    raise StoryError(f"(Unknown helper role: {helper_role})")


def false_lead_for(place_id: str) -> str:
    order = ["toy_bin", "coat_pocket", "top_shelf", "under_sofa"]
    for pid in order:
        if pid != place_id:
            return pid
    return "toy_bin"


def predict_running(world: World) -> bool:
    sim = world.copy()
    if "battery" not in sim.entities or "device" not in sim.entities:
        return False
    sim.get("battery").meters["inserted"] += 1
    sim.get("device").meters["switched_on"] += 1
    propagate(sim, narrate=False)
    return sim.get("device").meters["running"] >= THRESHOLD


def introduce(world: World, hero: Entity, helper: Entity, device_cfg: Device) -> None:
    world.say(
        f"After school, {hero.id} waited in the living room for Miss June from next door. "
        f"On the rug sat {device_cfg.phrase}, and {hero.id} {device_cfg.demo_line}."
    )
    if helper.type in {"mother", "father"}:
        world.say(
            f"{helper.label_word.capitalize()} was folding towels nearby and listening with a smile "
            f"to the little pretend sound effects {hero.id} made under {hero.pronoun('possessive')} breath."
        )
    else:
        world.say(
            f"{helper.id}, {hero.pronoun('possessive')} {helper.label_word}, sat nearby and answered "
            f"every pretend sound with another one."
        )


def discover_missing(world: World, hero: Entity, helper: Entity, device_cfg: Device) -> None:
    device = world.get("device")
    battery = world.get("battery")
    device.meters["needs_power"] += 1
    battery.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} pressed the start button. Nothing happened. Not even a tiny buzz. '
        f'"Oh no," {hero.pronoun()} whispered. "The battery pack is gone."'
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f'"If I do not find it, I might miss Miss June\'s hello before supper," '
            f'{hero.id} said. The room suddenly felt much too quiet.'
        )
    world.facts["predicted_running"] = predict_running(world)


def begin_quest(world: World, hero: Entity, helper: Entity) -> None:
    helper_name = helper.label_word.capitalize() if helper.type in {"mother", "father"} else helper.id
    world.say(
        f'{helper_name} did not laugh. "{hero.id}," {helper.pronoun()} said, '
        f'"let\'s make it a quest. We will look slowly and listen carefully."'
    )
    hero.memes["hope"] += 1
    helper.memes["care"] += 1


def search_wrong_place(world: World, hero: Entity, helper: Entity, wrong_place: Place) -> None:
    hero.memes["effort"] += 1
    world.say(
        f"They tried {wrong_place.phrase} first. {wrong_place.search_sound}! went the search as "
        f"{hero.id} and {helper.pronoun('object')} looked around."
    )
    world.say(
        f"But there was no battery pack there, only ordinary things waiting in the wrong place."
    )


def search_right_place(
    world: World,
    hero: Entity,
    helper: Entity,
    place: Place,
    method: Method,
) -> None:
    helper_name = helper.label_word.capitalize() if helper.type in {"mother", "father"} else helper.id
    world.say(
        f"Then {hero.id} looked toward {place.phrase}. "
        f'"Wait," {hero.pronoun()} said. "{place.search_sound} was not the right sound before."'
    )
    world.say(
        f"{helper_name} nodded and {method.action_text}. {place.clue_sound}! Something small answered from "
        f"{place.text}."
    )
    world.say(
        f"They both froze, then smiled. The clue had made a real sound."
    )


def retrieve(world: World, hero: Entity, helper: Entity, place: Place, method: Method) -> None:
    battery = world.get("battery")
    battery.meters["missing"] = 0.0
    battery.meters["found"] += 1
    hero.memes["joy"] += 0.5
    world.say(
        f"{helper.pronoun().capitalize()} {method.retrieve_text}. It was dusty at one corner, but it was safe."
    )
    world.say(
        f'"Found it!" {hero.id} said, holding up the battery pack as if the quest had ended with a tiny treasure.'
    )


def insert_and_start(world: World, hero: Entity, helper: Entity, device_cfg: Device) -> None:
    battery = world.get("battery")
    device = world.get("device")
    battery.meters["inserted"] += 1
    device.meters["switched_on"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} slid the battery pack into the {device_cfg.label} and pressed the button again."
    )
    if device.meters["running"] >= THRESHOLD:
        world.say(
            f"{device_cfg.start_sound} {device_cfg.move_line}."
        )


def ending(world: World, hero: Entity, helper: Entity, device_cfg: Device) -> None:
    helper_name = helper.label_word.capitalize() if helper.type in {"mother", "father"} else helper.id
    world.say(
        "A soft knock came at the door just then, and Miss June peeked in with her kind smile."
    )
    world.say(
        f'{hero.id} did not miss the moment after all. {hero.pronoun().capitalize()} showed Miss June the '
        f'{device_cfg.label}, and even {helper_name} added a quiet little "{device_cfg.start_sound}" of '
        f'victory from the doorway.'
    )
    world.say(
        "The room no longer felt worried and still. It felt busy, bright, and nicely alive."
    )


def tell(
    device_cfg: Device,
    place_cfg: Place,
    method_cfg: Method,
    hero_name: str,
    hero_gender: str,
    helper_role: str,
    helper_name: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper_type = helper_role
    helper = world.add(
        Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper")
    )
    device = world.add(
        Entity(id="device", kind="thing", type="device", label=device_cfg.label, phrase=device_cfg.phrase, tags=set(device_cfg.tags))
    )
    battery = world.add(
        Entity(id="battery", kind="thing", type="battery", label="battery pack", phrase="the little battery pack", tags={"battery"})
    )

    wrong_place_id = false_lead_for(place_cfg.id)
    wrong_place_cfg = PLACES[wrong_place_id]

    world.facts["device_cfg"] = device_cfg
    world.facts["place_cfg"] = place_cfg
    world.facts["method_cfg"] = method_cfg
    world.facts["wrong_place_cfg"] = wrong_place_cfg

    introduce(world, hero, helper, device_cfg)

    world.para()
    discover_missing(world, hero, helper, device_cfg)
    begin_quest(world, hero, helper)
    search_wrong_place(world, hero, helper, wrong_place_cfg)

    world.para()
    search_right_place(world, hero, helper, place_cfg, method_cfg)
    retrieve(world, hero, helper, place_cfg, method_cfg)

    world.para()
    insert_and_start(world, hero, helper, device_cfg)
    ending(world, hero, helper, device_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        device=device,
        battery=battery,
        found=battery.meters["found"] >= THRESHOLD,
        running=device.meters["running"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "battery": [
        (
            "What does a battery do?",
            "A battery stores energy and gives it to a toy or a tool. Without a battery, many electric things cannot start."
        )
    ],
    "electric": [
        (
            "What does electric mean?",
            "Electric means something works using electricity. That power can make lights shine, buttons sing, or little motors move."
        )
    ],
    "train": [
        (
            "What is an electric train toy?",
            "An electric train toy is a toy train with a tiny motor inside. When it has power, it can move with a whirr or a click."
        )
    ],
    "keyboard": [
        (
            "What is an electric keyboard?",
            "An electric keyboard is a music toy or instrument with buttons or keys. Electricity helps it make sounds."
        )
    ],
    "dinosaur": [
        (
            "Why does a toy dinosaur make sounds?",
            "Some toy dinosaurs have a tiny speaker or motor inside. When they get power, they can stomp, blink, or roar."
        )
    ],
    "broom": [
        (
            "Why can a broom help reach something?",
            "A broom has a long handle, so it can help pull a small thing closer from under furniture. A grown-up should help if the space is tight."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps a person reach something a little higher. It should be used carefully on a steady floor."
        )
    ],
    "pocket": [
        (
            "Why do people pat pockets when they look for something?",
            "Patting a pocket lets you feel whether a small object is inside before you reach in. It is a quick way to check for missing things."
        )
    ],
    "careful_search": [
        (
            "Why is it good to search slowly?",
            "Searching slowly helps you notice little clues like shape, color, or sound. When you rush, it is easy to miss small things."
        )
    ],
    "search": [
        (
            "How can sound help in a search?",
            "A tiny rattle, clink, or ting can tell you where a hidden object is. Listening carefully is part of good searching."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "electric",
    "battery",
    "train",
    "keyboard",
    "dinosaur",
    "search",
    "broom",
    "stool",
    "pocket",
    "careful_search",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    device_cfg = world.facts["device_cfg"]
    place_cfg = world.facts["place_cfg"]
    return [
        f'Write a slice-of-life quest story for a 3-to-5-year-old that includes the words "miss" and "electric".',
        f"Tell a gentle home story where {hero.label} cannot start {device_cfg.phrase} because the battery pack is missing, and a careful search leads to {place_cfg.phrase}.",
        f'Write a short story with playful sound effects where a child worries about missing a visit from Miss June, then solves the problem by listening for a tiny clue.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    device_cfg = world.facts["device_cfg"]
    place_cfg = world.facts["place_cfg"]
    method_cfg = world.facts["method_cfg"]
    wrong_place_cfg = world.facts["wrong_place_cfg"]
    helper_name = helper.label_word if helper.type in {"mother", "father"} else helper.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child who wanted to show an {device_cfg.label} to Miss June, and {helper_name} who helped with the search."
        ),
        (
            f"Why was {hero.label} worried at first?",
            f"{hero.label} was worried because the battery pack was missing, so the {device_cfg.label} would not start. {hero.pronoun('subject').capitalize()} thought {hero.pronoun('subject')} might miss Miss June's visit if it stayed quiet."
        ),
        (
            "What made the story feel like a quest?",
            f"They did not give up after one try. First they searched {wrong_place_cfg.phrase}, and then they followed a better clue to {place_cfg.phrase}."
        ),
        (
            f"How did sound help them find the battery pack?",
            f"While they searched, they listened carefully instead of rushing. The little {place_cfg.clue_sound} from {place_cfg.text} told them the battery pack was hiding there."
        ),
        (
            f"How did they get the battery pack back?",
            f"They used {method_cfg.label}. That method fit the hiding place, so they could reach the battery pack safely and bring it back."
        ),
    ]
    if world.facts.get("running"):
        qa.append(
            (
                "What changed at the end?",
                f"At the end, the quiet room turned lively because the {device_cfg.label} finally started. Its {device_cfg.start_sound} proved the quest had worked."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"electric", "battery", "search"}
    device_cfg = world.facts["device_cfg"]
    method_cfg = world.facts["method_cfg"]
    tags |= set(device_cfg.tags)
    tags |= set(method_cfg.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        device="train",
        place="under_sofa",
        method="broom",
        hero_name="Lily",
        hero_gender="girl",
        helper_role="mother",
        helper_name="Mom",
    ),
    StoryParams(
        device="keyboard",
        place="top_shelf",
        method="step_stool",
        hero_name="Leo",
        hero_gender="boy",
        helper_role="father",
        helper_name="Dad",
    ),
    StoryParams(
        device="dinosaur",
        place="coat_pocket",
        method="pat_pockets",
        hero_name="Mia",
        hero_gender="girl",
        helper_role="brother",
        helper_name="Milo",
    ),
    StoryParams(
        device="train",
        place="toy_bin",
        method="careful_sort",
        hero_name="Ben",
        hero_gender="boy",
        helper_role="sister",
        helper_name="Ruby",
    ),
]


def explain_rejection(place_id: str, method_id: str) -> str:
    if place_id not in PLACES:
        return f"(Unknown place: {place_id})"
    if method_id not in METHODS:
        return f"(Unknown method: {method_id})"
    place = PLACES[place_id]
    method = METHODS[method_id]
    return (
        f"(No story: {method.label} does not fit {place.phrase}. "
        f"That place needs a method that works on {place.access} access.)"
    )


ASP_RULES = r"""
valid(D, P, M) :- device(D), place(P), method(M), access(P, A), works(M, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for device_id in sorted(DEVICES):
        lines.append(asp.fact("device", device_id))
    for place_id, place in sorted(PLACES.items()):
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("access", place_id, place.access))
    for method_id, method in sorted(METHODS.items()):
        lines.append(asp.fact("method", method_id))
        for access in sorted(method.works_on):
            lines.append(asp.fact("works", method_id, access))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: empty story.)")
        print("OK: random seeded generation works.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child searches for a missing battery pack before Miss June arrives."
    )
    ap.add_argument("--device", choices=sorted(DEVICES))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "sister", "brother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.method and not valid_combo(args.device or next(iter(DEVICES)), args.place, args.method):
        raise StoryError(explain_rejection(args.place, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.device is None or combo[0] == args.device)
        and (args.place is None or combo[1] == args.place)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    device_id, place_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_role = args.helper or rng.choice(["mother", "father", "sister", "brother"])
    _helper_type, helper_name = helper_type_name(helper_role, rng)
    return StoryParams(
        device=device_id,
        place=place_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_role=helper_role,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.device not in DEVICES:
        raise StoryError(f"(Unknown device: {params.device})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if not valid_combo(params.device, params.place, params.method):
        raise StoryError(explain_rejection(params.place, params.method))
    if params.helper_role not in {"mother", "father", "sister", "brother"}:
        raise StoryError(f"(Unknown helper role: {params.helper_role})")

    world = tell(
        device_cfg=DEVICES[params.device],
        place_cfg=PLACES[params.place],
        method_cfg=METHODS[params.method],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_role=params.helper_role,
        helper_name=params.helper_name,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (device, place, method) combos:\n")
        for device_id, place_id, method_id in combos:
            print(f"  {device_id:10} {place_id:12} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.device} / {p.place} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
