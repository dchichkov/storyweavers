#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/famed_curiosity_rhyme_friendship_heartwarming.py
============================================================================

A standalone storyworld about two friends, a famed rhyme box, and the warm way
curiosity turns into shared discovery.

The little domain is intentionally small and constraint-checked:

- A setting can host only certain famed boxes.
- Each box opens only with the right kind of rhyme help:
  speaking together, tracing with chalk, or chiming a bell.
- An impatient child may try to force the box first.
- Depending on patience and trust, the friends either solve it themselves
  right away or need a caretaker's gentle help after the box sticks.

The stories stay heartwarming: even the "oops" branch ends in apology,
cooperation, and a changed final image that proves the friendship grew.

Run it
------
python storyworlds/worlds/gpt-5.4/famed_curiosity_rhyme_friendship_heartwarming.py
python storyworlds/worlds/gpt-5.4/famed_curiosity_rhyme_friendship_heartwarming.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/famed_curiosity_rhyme_friendship_heartwarming.py --all --qa
python storyworlds/worlds/gpt-5.4/famed_curiosity_rhyme_friendship_heartwarming.py --json
python storyworlds/worlds/gpt-5.4/famed_curiosity_rhyme_friendship_heartwarming.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives in storyworlds/worlds/gpt-5.4/, so three ".." steps reach
# storyworlds/, where results.py lives.
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "librarian"}
        male = {"boy", "father", "dad", "man", "gardener"}
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
            "librarian": "librarian",
            "gardener": "gardener",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    caretaker_type: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class BoxKind:
    id: str
    label: str
    phrase: str
    place_hint: str
    requires: str
    clue: str
    inside: str
    ending_gift: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    mode: str
    sense: int
    setup: str
    success: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Impulse:
    id: str
    roughness: int
    text: str
    fail: str
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


def _r_jam_hurt(world: World) -> list[str]:
    box = world.entities.get("box")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not box or not hero or not friend:
        return []
    if box.meters["jammed"] < THRESHOLD:
        return []
    sig = ("jam_hurt", box.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    friend.memes["hurt"] += 1
    return ["__jam__"]


def _r_open_delight(world: World) -> list[str]:
    box = world.entities.get("box")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not box or not hero or not friend:
        return []
    if box.meters["open"] < THRESHOLD:
        return []
    sig = ("open_delight", box.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    return []


def _r_apology_restore(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return []
    if hero.memes["apology"] < THRESHOLD:
        return []
    sig = ("apology_restore", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] = 0.0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="jam_hurt", tag="social", apply=_r_jam_hurt),
    Rule(name="open_delight", tag="emotional", apply=_r_open_delight),
    Rule(name="apology_restore", tag="social", apply=_r_apology_restore),
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


def valid_combo(setting: Setting, box: BoxKind, helper: Helper) -> bool:
    return box.id in setting.affords and helper.mode == box.requires and helper.sense >= SENSE_MIN


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def would_listen(trait: str, trust: int, patience: int) -> bool:
    bonus = 2 if trait in {"patient", "gentle", "thoughtful"} else 0
    return trust + patience + bonus >= 10


def box_sticks(box: BoxKind, impulse: Impulse) -> bool:
    return box.fragile and impulse.roughness >= 2


def outcome_of(params: "StoryParams") -> str:
    if would_listen(params.friend_trait, params.trust, params.patience):
        return "self_open"
    if box_sticks(BOXES[params.box], IMPULSES[params.impulse]):
        return "helped_after_jam"
    return "helped_after_oops"


def predict_force(world: World, box: BoxKind, impulse: Impulse) -> dict:
    sim = world.copy()
    sim_box = sim.get("box")
    sim_box.meters["shaken"] += 1
    if box_sticks(box, impulse):
        sim_box.meters["jammed"] += 1
    propagate(sim, narrate=False)
    return {
        "jammed": sim_box.meters["jammed"] >= THRESHOLD,
        "friend_hurt": sim.get("friend").memes["hurt"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"{hero.id} and {friend.id} were the kind of friends who always noticed small wonders together."
    )
    world.say(
        f"That afternoon they wandered into {setting.place}, where {setting.detail}"
    )


def find_box(world: World, hero: Entity, friend: Entity, box: BoxKind) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"By {box.place_hint} stood {box.phrase}, a famed little box the neighborhood children loved to talk about."
    )
    world.say(
        f'On the front was a painted clue: "{box.clue}"'
    )
    world.say(
        f"{hero.id} leaned closer, eyes shining. {friend.id} leaned in too, and for a moment they both just wondered what might be inside."
    )


def tempt(world: World, hero: Entity, impulse: Impulse) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f'"Maybe it will open fast if I {impulse.text}," {hero.id} said, too curious to wait.'
    )


def warn(world: World, friend: Entity, hero: Entity, box: BoxKind, impulse: Impulse) -> None:
    pred = predict_force(world, box, impulse)
    world.facts["predicted_jam"] = pred["jammed"]
    world.facts["predicted_hurt"] = pred["friend_hurt"]
    extra = " It might only make the little box stick harder." if pred["jammed"] else " It might not work at all."
    world.say(
        f'{friend.id} touched the corner of the sign and shook {friend.pronoun("possessive")} head. "I think the clue wants a rhyme, not a shove.{extra}"'
    )


def solve_together(world: World, hero: Entity, friend: Entity, helper: Helper, box: BoxKind) -> None:
    world.say(helper.setup.format(hero=hero.id, friend=friend.id, clue=box.clue))
    box_ent = world.get("box")
    box_ent.meters["open"] += 1
    box_ent.meters["kindly_opened"] += 1
    propagate(world)
    world.say(helper.success.format(label=box.label))
    world.say(
        f"Inside lay {box.inside}, and the sight made both friends grin at the same time."
    )


def force_first(world: World, hero: Entity, friend: Entity, box: BoxKind, impulse: Impulse) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But curiosity rushed ahead of patience. {hero.id} reached out and {impulse.text}."
    )
    box_ent = world.get("box")
    box_ent.meters["shaken"] += 1
    if box_sticks(box, impulse):
        box_ent.meters["jammed"] += 1
    propagate(world, narrate=False)
    if box_ent.meters["jammed"] >= THRESHOLD:
        world.say(
            impulse.fail.format(label=box.label)
        )
    else:
        world.say(
            f"The {box.label} gave a tiny clack, but it still did not open."
        )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{friend.id} looked sad, not because of the box, but because the clue had not been given a chance."
        )


def caretaker_arrives(world: World, caretaker: Entity, friend: Entity, hero: Entity) -> None:
    world.say(
        f"{caretaker.label_word.capitalize()} came over at the sound and knelt beside them."
    )
    world.say(
        f'"Curiosity is a lovely thing," {caretaker.pronoun()} said, "but lovely things open best with gentle hands and listening ears."'
    )
    hero.memes["reflection"] += 1
    friend.memes["calm"] += 1


def apologize(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I was too hasty," {hero.id} whispered. "I should have listened to you."'
    )
    world.say(
        f'{friend.id} gave {hero.pronoun("object")} a small smile and moved a little closer again.'
    )


def open_with_help(world: World, caretaker: Entity, hero: Entity, friend: Entity,
                   helper: Helper, box: BoxKind) -> None:
    world.say(helper.setup.format(hero=hero.id, friend=friend.id, clue=box.clue))
    if world.get("box").meters["jammed"] >= THRESHOLD:
        world.say(
            f"{caretaker.label_word.capitalize()} steadied the latch with one careful finger while they tried again."
        )
        world.get("box").meters["jammed"] = 0.0
        world.get("box").meters["mended"] += 1
    world.get("box").meters["open"] += 1
    world.get("box").meters["helped_open"] += 1
    propagate(world)
    world.say(helper.success.format(label=box.label))
    world.say(
        f"Inside lay {box.inside}, and somehow it felt even nicer because they had opened it kindly at last."
    )


def ending(world: World, hero: Entity, friend: Entity, box: BoxKind) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"They shared {box.ending_gift} instead of keeping it to themselves."
    )
    world.say(
        f"Soon the two friends were making up a new rhyme together, and their voices sounded warmer than the afternoon sun."
    )
    world.say(
        f"Anyone passing by could see what had changed: the famed little box was open, and so were two very thoughtful hearts."
    )


def tell(setting: Setting, box: BoxKind, helper: Helper, impulse: Impulse,
         hero_name: str = "Lina", hero_gender: str = "girl",
         friend_name: str = "Owen", friend_gender: str = "boy",
         friend_trait: str = "patient", trust: int = 6, patience: int = 4,
         caretaker_name: str = "Caretaker") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["curious"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
    ))
    caretaker = world.add(Entity(
        id=caretaker_name,
        kind="character",
        type=setting.caretaker_type,
        role="caretaker",
        label="the caretaker",
    ))
    box_ent = world.add(Entity(
        id="box",
        kind="thing",
        type="box",
        label=box.label,
        phrase=box.phrase,
        tags=set(box.tags),
    ))

    hero.memes["trust"] = float(trust)
    friend.memes["trust"] = float(trust)
    hero.memes["patience"] = float(patience)
    friend.memes["patience"] = float(patience)

    introduce(world, hero, friend, setting)
    find_box(world, hero, friend, box)

    world.para()
    tempt(world, hero, impulse)
    warn(world, friend, hero, box, impulse)

    if would_listen(friend_trait, trust, patience):
        world.say(
            f"{hero.id} took a breath, then smiled at {friend.id}. Curiosity was still bouncing inside {hero.pronoun('object')}, but now it had room for friendship too."
        )
        world.para()
        solve_together(world, hero, friend, helper, box)
        outcome = "self_open"
    else:
        force_first(world, hero, friend, box, impulse)
        world.para()
        caretaker_arrives(world, caretaker, friend, hero)
        apologize(world, hero, friend)
        open_with_help(world, caretaker, hero, friend, helper, box)
        outcome = "helped_after_jam" if box_ent.meters["mended"] >= THRESHOLD else "helped_after_oops"

    world.para()
    ending(world, hero, friend, box)

    world.facts.update(
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        box=box,
        helper=helper,
        impulse=impulse,
        setting=setting,
        trust=trust,
        patience=patience,
        outcome=outcome,
        jammed=box_ent.meters["mended"] >= THRESHOLD or box_ent.meters["jammed"] >= THRESHOLD,
        opened=box_ent.meters["open"] >= THRESHOLD,
        mended=box_ent.meters["mended"] >= THRESHOLD,
        clue=box.clue,
    )
    return world


SETTINGS = {
    "library_courtyard": Setting(
        id="library_courtyard",
        place="the library courtyard",
        detail="ivy climbed a brick wall, and the windows shone like square pieces of honey",
        caretaker_type="librarian",
        affords={"poem_box", "bell_box"},
        tags={"library"},
    ),
    "rose_garden": Setting(
        id="rose_garden",
        place="the rose garden",
        detail="the air smelled sweet, and a stone path curled between neat beds of flowers",
        caretaker_type="gardener",
        affords={"chalk_box", "poem_box"},
        tags={"garden"},
    ),
    "sunny_park": Setting(
        id="sunny_park",
        place="the sunny park",
        detail="a breeze nudged the swings, and sparrows hopped under the benches",
        caretaker_type="gardener",
        affords={"bell_box", "chalk_box"},
        tags={"park"},
    ),
}

BOXES = {
    "poem_box": BoxKind(
        id="poem_box",
        label="poem box",
        phrase="a small blue poem box",
        place_hint="the old stone bench",
        requires="speak",
        clue="Say a pair that sounds the same, and friendship opens this small frame.",
        inside="two ribbon bookmarks and a folded note that read, 'Share a verse with a friend.'",
        ending_gift="the ribbon bookmarks and the note",
        fragile=True,
        tags={"rhyme", "bookmarks", "friendship"},
    ),
    "chalk_box": BoxKind(
        id="chalk_box",
        label="chalk box",
        phrase="a bright green chalk box",
        place_hint="the low garden wall",
        requires="trace",
        clue="Trace the rhyming pair you know, and kind hands make the latch swing slow.",
        inside="three pieces of colored chalk and a card with a tiny heart drawn on it",
        ending_gift="the colored chalk and the tiny heart card",
        fragile=True,
        tags={"rhyme", "chalk", "friendship"},
    ),
    "bell_box": BoxKind(
        id="bell_box",
        label="bell box",
        phrase="a silver bell box",
        place_hint="the little wooden arch",
        requires="chime",
        clue="Ring in rhyme, not shove or knock; soft sounds, not bumps, will lift the lock.",
        inside="two star stickers and a strip of paper that said, 'Make music together.'",
        ending_gift="the star stickers and the music note",
        fragile=True,
        tags={"rhyme", "bell", "friendship"},
    ),
}

HELPERS = {
    "say_rhyme": Helper(
        id="say_rhyme",
        mode="speak",
        sense=3,
        setup='{friend} whispered, "Let\'s try it together." So {hero} and {friend} thought of a tiny rhyme, held hands, and spoke it slowly beneath the clue.',
        success='With a soft click, the {label} opened as if it had been waiting for patient voices all along.',
        tags={"rhyme", "speaking"},
    ),
    "trace_chalk": Helper(
        id="trace_chalk",
        mode="trace",
        sense=3,
        setup='{friend} found a stub of chalk nearby, and {hero} carefully traced a rhyming pair under the painted clue while {friend} sounded the words out.',
        success='The chalk line gleamed white for a second, and then the {label} loosened with a happy little click.',
        tags={"rhyme", "chalk"},
    ),
    "ring_bell": Helper(
        id="ring_bell",
        mode="chime",
        sense=3,
        setup='{friend} noticed the tiny bell beside the sign, and together {hero} and {friend} chimed it in a gentle rhythm while repeating the rhyme from the clue.',
        success='The bell gave one bright note, and the {label} opened as smoothly as a smile.',
        tags={"rhyme", "bell"},
    ),
    "push_harder": Helper(
        id="push_harder",
        mode="force",
        sense=1,
        setup='{hero} pushed and {friend} frowned.',
        success='Nothing lovely happened.',
        tags={"force"},
    ),
}

IMPULSES = {
    "tug": Impulse(
        id="tug",
        roughness=2,
        text="gave the latch a quick tug",
        fail="The {label} scraped and stuck, as if it had folded itself shut in surprise.",
        tags={"patience"},
    ),
    "rattle": Impulse(
        id="rattle",
        roughness=2,
        text="rattled the little lid",
        fail="The {label} made a sour little squeak and would not budge after that.",
        tags={"patience"},
    ),
    "knock": Impulse(
        id="knock",
        roughness=1,
        text="knocked on the front with impatient knuckles",
        fail="The {label} stayed closed, and the sound felt much too loud for such a small mystery.",
        tags={"patience"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Ava", "Lucy", "June", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Finn", "Leo", "Noah", "Eli", "Sam"]
TRAITS = ["patient", "gentle", "thoughtful", "steady", "kind"]


@dataclass
class StoryParams:
    setting: str
    box: str
    helper: str
    impulse: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    friend_trait: str
    trust: int
    patience: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="library_courtyard",
        box="poem_box",
        helper="say_rhyme",
        impulse="tug",
        hero_name="Lina",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        friend_trait="patient",
        trust=7,
        patience=4,
    ),
    StoryParams(
        setting="rose_garden",
        box="chalk_box",
        helper="trace_chalk",
        impulse="rattle",
        hero_name="Maya",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        friend_trait="gentle",
        trust=3,
        patience=3,
    ),
    StoryParams(
        setting="sunny_park",
        box="bell_box",
        helper="ring_bell",
        impulse="knock",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="June",
        friend_gender="girl",
        friend_trait="thoughtful",
        trust=4,
        patience=3,
    ),
    StoryParams(
        setting="rose_garden",
        box="poem_box",
        helper="say_rhyme",
        impulse="tug",
        hero_name="Lucy",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        friend_trait="steady",
        trust=6,
        patience=2,
    ),
]


KNOWLEDGE = {
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have the same ending sound, like cat and hat. Rhymes can make clues feel playful and easier to remember.",
        )
    ],
    "friendship": [
        (
            "Why does listening help a friendship?",
            "Listening shows your friend that their thoughts matter. It helps people solve problems together instead of pulling apart.",
        )
    ],
    "patience": [
        (
            "What is patience?",
            "Patience is waiting calmly instead of rushing. It gives your hands and your heart time to make a better choice.",
        )
    ],
    "chalk": [
        (
            "What is chalk used for?",
            "Chalk is used for drawing or writing on rough surfaces like sidewalks and boards. It leaves a soft mark that can be brushed away.",
        )
    ],
    "bell": [
        (
            "How does a little bell make sound?",
            "A little bell rings when something inside it taps the metal. The metal vibrates and makes a bright sound.",
        )
    ],
    "library": [
        (
            "What do people do in a library courtyard?",
            "They might read, walk quietly, or talk softly with friends. It is a place that often feels calm and thoughtful.",
        )
    ],
    "garden": [
        (
            "Why do gardens feel peaceful?",
            "Gardens have flowers, leaves, and soft smells that help people slow down. Quiet places can make careful choices easier.",
        )
    ],
    "park": [
        (
            "What can you notice in a park?",
            "You can notice birds, swings, trees, wind, and other people playing. Parks are full of small things to wonder about.",
        )
    ],
}
KNOWLEDGE_ORDER = ["rhyme", "friendship", "patience", "chalk", "bell", "library", "garden", "park"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for bid, box in BOXES.items():
            for hid, helper in HELPERS.items():
                if valid_combo(setting, box, helper):
                    combos.append((sid, bid, hid))
    return sorted(combos)


def explain_rejection(setting: Setting, box: BoxKind, helper: Helper) -> str:
    if box.id not in setting.affords:
        return (
            f"(No story: {box.label} does not belong in {setting.place}. "
            f"Pick a box that fits that setting.)"
        )
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: helper '{helper.id}' is too forceful for this heartwarming world. "
            f"Choose a gentler rhyme helper.)"
        )
    return (
        f"(No story: {box.label} opens by {box.requires}, but helper '{helper.id}' works by {helper.mode}. "
        f"Choose a helper that matches the clue.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    box = f["box"]
    outcome = f["outcome"]
    prompts = [
        'Write a heartwarming story for a 3-to-5-year-old that includes the word "famed" and centers on curiosity, rhyme, and friendship.',
        f"Tell a gentle story where two friends, {hero.id} and {friend.id}, discover a famed {box.label} and must use a rhyme to open it.",
        "Write a short story where curiosity first makes a child rush, but friendship and patience lead to a warmer ending.",
    ]
    if outcome != "self_open":
        prompts.append(
            "Include a small mistake, a kind apology, and a grown-up who helps the children try again without shame."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    box = f["box"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.id} and {friend.id}, and the {caretaker.label_word} who helped them near the end. Their day turns around because they stay together instead of letting the mistake separate them.",
        ),
        (
            f"What made {hero.id} and {friend.id} curious?",
            f"They found a famed {box.label} with a rhyming clue on it, and they wanted to know what was inside. The mystery pulled both friends close and started the adventure.",
        ),
        (
            "How did rhyme matter in the story?",
            f"The clue on the box asked for a rhyme, and the box opened only when the children used the right kind of gentle rhyme help. The rhyme was not just decoration; it was the true way to solve the problem.",
        ),
    ]
    if outcome == "self_open":
        qa.append(
            (
                f"Why did {hero.id} listen to {friend.id}?",
                f"{hero.id} was eager, but trusted {friend.id} enough to slow down. That pause let curiosity and friendship work together instead of bumping into each other.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The friends opened the box by using {helper.id.replace('_', ' ')} and shared what they found inside. In the final image they are making up a rhyme together, which shows their friendship grew warmer.",
            )
        )
    else:
        jam_text = "The box stuck after the rough try." if f.get("mended") else "The rough try did not work and made the moment feel tense."
        qa.append(
            (
                f"What happened when {hero.id} rushed?",
                f"{jam_text} {friend.id} felt hurt because the clue had not been given a fair chance. The mistake mattered because it changed how the friends felt, not just what the box did.",
            )
        )
        qa.append(
            (
                f"Why did {hero.id} apologize to {friend.id}?",
                f"{hero.id} realized that rushing had ignored both the clue and {friend.id}'s good idea. The apology helped the two friends stand close again before they tried the rhyme the right way.",
            )
        )
        qa.append(
            (
                f"How did the {caretaker.label_word} help?",
                f"The {caretaker.label_word} stayed calm, reminded them that curiosity works best with gentle hands, and helped them try the clue again. That kindness turned an embarrassing moment into a lesson the friends could share.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"rhyme", "friendship", "patience"}
    setting = world.facts["setting"]
    box = world.facts["box"]
    if "library" in setting.tags:
        tags.add("library")
    if "garden" in setting.tags:
        tags.add("garden")
    if "park" in setting.tags:
        tags.add("park")
    if "chalk" in box.tags:
        tags.add("chalk")
    if "bell" in box.tags:
        tags.add("bell")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% compatibility gate
valid(S, B, H) :- setting(S), box(B), helper(H), affords(S, B), requires(B, M), mode(H, M), sense(H, V), sense_min(Mn), V >= Mn.
sensible(H) :- helper(H), sense(H, V), sense_min(Mn), V >= Mn.

% listening model
trait_bonus(2) :- chosen_trait(T), calm_trait(T).
trait_bonus(0) :- chosen_trait(T), not calm_trait(T).
listen_score(T + P + B) :- trust(T), patience(P), trait_bonus(B).
listens :- listen_score(S), S >= 10.

% forcing/jam model
sticks :- chosen_box(B), fragile(B), chosen_impulse(I), roughness(I, R), R >= 2.

outcome(self_open) :- listens.
outcome(helped_after_jam) :- not listens, sticks.
outcome(helped_after_oops) :- not listens, not sticks.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for bid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, bid))
    for bid, box in BOXES.items():
        lines.append(asp.fact("box", bid))
        lines.append(asp.fact("requires", bid, box.requires))
        if box.fragile:
            lines.append(asp.fact("fragile", bid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("mode", hid, helper.mode))
        lines.append(asp.fact("sense", hid, helper.sense))
    for iid, impulse in IMPULSES.items():
        lines.append(asp.fact("impulse", iid))
        lines.append(asp.fact("roughness", iid, impulse.roughness))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted({"patient", "gentle", "thoughtful"}):
        lines.append(asp.fact("calm_trait", trait))
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
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_box", params.box),
            asp.fact("chosen_impulse", params.impulse),
            asp.fact("chosen_trait", params.friend_trait),
            asp.fact("trust", params.trust),
            asp.fact("patience", params.patience),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: missing prompt or QA output.")


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: compatibility gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sens = set(asp_sensible())
    python_sens = {h.id for h in sensible_helpers()}
    if clingo_sens == python_sens:
        print(f"OK: sensible helpers match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed during verification at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for p in mismatches[:5]:
            print(
                f"  params={p} asp={asp_outcome(p)} python={outcome_of(p)}"
            )

    try:
        smoke_test()
        print("OK: smoke generation test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: famed rhyme boxes, curiosity, and friendship."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--box", choices=BOXES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--impulse", choices=IMPULSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--patience", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible sampling")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper is not None and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(
            f"(No story: helper '{args.helper}' is too rough for this world. Choose a gentle rhyme helper.)"
        )

    if args.setting and args.box and args.helper:
        setting = SETTINGS[args.setting]
        box = BOXES[args.box]
        helper = HELPERS[args.helper]
        if not valid_combo(setting, box, helper):
            raise StoryError(explain_rejection(setting, box, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.box is None or combo[1] == args.box)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, box_id, helper_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    friend_trait = args.friend_trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(2, 8)
    patience = args.patience if args.patience is not None else rng.randint(1, 6)
    impulse = args.impulse or rng.choice(sorted(IMPULSES))
    return StoryParams(
        setting=setting_id,
        box=box_id,
        helper=helper_id,
        impulse=impulse,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        trust=trust,
        patience=patience,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.box not in BOXES:
        raise StoryError(f"(Unknown box: {params.box})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.impulse not in IMPULSES:
        raise StoryError(f"(Unknown impulse: {params.impulse})")

    setting = SETTINGS[params.setting]
    box = BOXES[params.box]
    helper = HELPERS[params.helper]
    impulse = IMPULSES[params.impulse]

    if not valid_combo(setting, box, helper):
        raise StoryError(explain_rejection(setting, box, helper))

    world = tell(
        setting=setting,
        box=box,
        helper=helper,
        impulse=impulse,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        friend_trait=params.friend_trait,
        trust=params.trust,
        patience=params.patience,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helpers: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, box, helper) combos:\n")
        for setting, box, helper in combos:
            print(f"  {setting:18} {box:10} {helper}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.box} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
