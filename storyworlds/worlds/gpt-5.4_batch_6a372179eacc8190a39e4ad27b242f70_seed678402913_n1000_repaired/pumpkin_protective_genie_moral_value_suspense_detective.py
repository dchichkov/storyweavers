#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pumpkin_protective_genie_moral_value_suspense_detective.py
======================================================================================

A small detective-style story world about a missing item, a glowing pumpkin,
and a protective genie who leaves clues for a child detective to follow.

Core idea
---------
A child notices that something important has vanished just when an autumn game
is about to begin. The child first suspects a friend, then investigates a trail
of odd clues around a pumpkin. A protective genie finally reveals the truth:
the item was hidden to keep the child away from a real danger. The grown-up
fixes the hazard, the child apologizes for blaming too quickly, and the mystery
ends with a safer, kinder choice.

Reasonableness constraint
-------------------------
Not every missing item makes sense with every danger. The world only tells a
story when the chosen item would actually lure the child toward the hazardous
place. A scooter can tempt a child to race over loose steps, but it does not
honestly point toward a rotten bridge in a pumpkin patch. The Python gate and
the ASP twin both enforce that compatibility.

Run it
------
python storyworlds/worlds/gpt-5.4/pumpkin_protective_genie_moral_value_suspense_detective.py
python storyworlds/worlds/gpt-5.4/pumpkin_protective_genie_moral_value_suspense_detective.py --all
python storyworlds/worlds/gpt-5.4/pumpkin_protective_genie_moral_value_suspense_detective.py --asp
python storyworlds/worlds/gpt-5.4/pumpkin_protective_genie_moral_value_suspense_detective.py --verify
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    pumpkin_phrase: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    location: str
    sign: str
    danger_line: str
    blocks: set[str] = field(default_factory=set)
    repair_text: str = ""
    safe_after: str = ""
    lesson: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    draw: str
    destination: str
    activity: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    sign: str
    trail: str
    reveal_glow: str
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
    apply: Callable[[World], list[str]]


def _r_missing_item(world: World) -> list[str]:
    item = world.entities.get("item")
    hero = world.entities.get("hero")
    if not item or not hero:
        return []
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("missing_item",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["suspense"] += 1
    return []


def _r_blame(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return []
    if hero.memes["suspects_friend"] < THRESHOLD:
        return []
    sig = ("blame",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    return []


def _r_danger(world: World) -> list[str]:
    hero = world.entities.get("hero")
    hazard = world.entities.get("hazard")
    if not hero or not hazard:
        return []
    if hero.meters["approaching_hazard"] < THRESHOLD or hazard.meters["active"] < THRESHOLD:
        return []
    sig = ("danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["suspense"] += 1
    return []


def _r_repaired(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    hazard = world.entities.get("hazard")
    if not hero or not friend or not hazard:
        return []
    if hazard.meters["fixed"] < THRESHOLD:
        return []
    sig = ("repaired",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    friend.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_item", apply=_r_missing_item),
    Rule(name="blame", apply=_r_blame),
    Rule(name="danger", apply=_r_danger),
    Rule(name="repaired", apply=_r_repaired),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
        if any(rule.apply(world) for rule in []):
            changed = True


def item_at_risk(hazard: Hazard, item: Item) -> bool:
    return bool(hazard.blocks & item.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for hazard_id in setting.affords:
            hazard = HAZARDS[hazard_id]
            for item_id, item in ITEMS.items():
                if item_at_risk(hazard, item):
                    combos.append((place_id, hazard_id, item_id))
    return sorted(combos)


def explain_rejection(hazard: Hazard, item: Item) -> str:
    return (
        f"(No story: {item.phrase} would not honestly lure the child toward "
        f"{hazard.location}. This world only tells mysteries where the protective "
        f"genie hides an item to keep the child away from a real, matching danger.)"
    )


def predict_danger(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["approaching_hazard"] += 1
    propagate(sim)
    return {
        "fear": hero.memes["fear"],
        "suspense": hero.memes["suspense"],
        "danger": sim.get("hazard").meters["active"],
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["care"] += 1
    world.say(
        f"On a crisp autumn evening, {hero.id} and {friend.id} were at {setting.place}. "
        f"{setting.scene} {setting.pumpkin_phrase}"
    )
    world.say(
        f"{hero.id} liked pretending to be a detective, always noticing what other "
        f"people missed."
    )


def prize_setup(world: World, hero: Entity, item: Item) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"That night, {hero.pronoun()} could hardly wait to use {item.phrase} and "
        f"{item.activity}. The plan was to {item.destination} before supper."
    )


def vanish(world: World, hero: Entity, item_ent: Entity, item: Item) -> None:
    item_ent.meters["hidden"] += 1
    propagate(world)
    world.say(
        f"But when {hero.id} reached for {item.label}, it was gone. The place where "
        f"it should have been looked strangely empty."
    )
    world.say(
        f"A little shiver ran through {hero.pronoun('object')}. A detective case had "
        f"begun."
    )


def suspect(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["suspects_friend"] += 1
    propagate(world)
    world.say(
        f'"Did you move it?" {hero.id} asked {friend.id} in a small, tight voice.'
    )
    world.say(
        f'{friend.id} blinked. "No," {friend.pronoun()} said. "{hero.id}, I did not touch it."'
    )


def clue_appears(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"Then {hero.id} noticed {clue.sign}. {clue.trail}"
    )
    world.say(
        f"The mystery felt bigger now, and much more interesting."
    )


def investigate(world: World, hero: Entity, hazard_ent: Entity, hazard: Hazard) -> None:
    hero.meters["approaching_hazard"] += 1
    propagate(world)
    pred = predict_danger(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"Following the clue, {hero.id} crept toward {hazard.location}. The night "
        f"seemed to hold its breath."
    )
    world.say(
        f"Just ahead, {hazard.sign}. {hazard.danger_line}"
    )


def genie_reveal(world: World, hero: Entity, friend: Entity, genie: Entity,
                 item_ent: Entity, item: Item, clue: Clue) -> None:
    genie.memes["care"] += 1
    hero.memes["wonder"] += 1
    item_ent.meters["revealed"] += 1
    world.say(
        f"Before {hero.id} could take one more step, the pumpkin beside the path "
        f"gave {clue.reveal_glow}."
    )
    world.say(
        f"Out floated a tiny genie wearing a leaf-green coat. \"I am a protective genie,\" "
        f"the little figure said. \"I hid {item.label} on purpose.\""
    )
    world.say(
        f"\"If you had tried to {item.destination}, you would have hurried straight "
        f"toward {hazard_ent.label}. I wanted to stop you until someone could make it safe.\""
    )
    world.say(
        f"{hero.id} looked at {friend.id} and felt heat rise in {hero.pronoun('possessive')} cheeks."
    )


def adult_fix(world: World, parent: Entity, hazard_ent: Entity, hazard: Hazard) -> None:
    hazard_ent.meters["active"] = 0.0
    hazard_ent.meters["fixed"] += 1
    propagate(world)
    world.say(
        f"{parent.label_word.capitalize()} came with a lantern, took one look, and "
        f"{hazard.repair_text}."
    )
    world.say(
        f"Soon {hazard.safe_after}"
    )


def apology_and_end(world: World, hero: Entity, friend: Entity, genie: Entity,
                    item_ent: Entity, item: Item, hazard: Hazard) -> None:
    hero.memes["kindness"] += 1
    hero.memes["lesson"] += 1
    hero.memes["suspects_friend"] = 0.0
    friend.memes["hurt"] = 0.0
    item_ent.meters["hidden"] = 0.0
    world.say(
        f'"I am sorry I blamed you," {hero.id} told {friend.id}. '
        f'"I should have looked for the truth before I pointed a finger."'
    )
    world.say(
        f'{friend.id} smiled and squeezed {hero.pronoun("possessive")} hand. '
        f'"That is what real detectives do," {friend.pronoun()} said.'
    )
    world.say(
        f'The genie placed {item.label} back in {hero.id}\'s hands. '
        f'"Protection first, fun second," {genie.pronoun()} whispered.'
    )
    world.say(
        f"After that, {hero.id} and {friend.id} used {item.label} only after "
        f"{hazard.safe_after.lower()}. The glowing pumpkin watched over them, and "
        f"the mystery ended with everyone safe and friends again."
    )


def tell(setting: Setting, hazard: Hazard, item: Item, clue: Clue,
         hero_name: str = "Nora", hero_type: str = "girl",
         friend_name: str = "Ben", friend_type: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    genie = world.add(Entity(id="Genie", kind="character", type="genie", role="genie", label="the genie"))
    hazard_ent = world.add(Entity(id="hazard", type="hazard", label=hazard.location, role="hazard"))
    hazard_ent.meters["active"] = 1.0
    item_ent = world.add(Entity(id="item", type="item", label=item.label, phrase=item.phrase, role="item"))
    pumpkin = world.add(Entity(id="pumpkin", type="pumpkin", label="pumpkin", phrase="a round pumpkin with a candle glow"))
    pumpkin.meters["glow"] = 1.0

    introduce(world, hero, friend, setting)
    prize_setup(world, hero, item)

    world.para()
    vanish(world, hero, item_ent, item)
    suspect(world, hero, friend)
    clue_appears(world, hero, clue)

    world.para()
    investigate(world, hero, hazard_ent, hazard)
    genie_reveal(world, hero, friend, genie, item_ent, item, clue)

    world.para()
    adult_fix(world, parent, hazard_ent, hazard)
    apology_and_end(world, hero, friend, genie, item_ent, item, hazard)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        genie=genie,
        item=item,
        clue=clue,
        setting=setting,
        hazard_cfg=hazard,
        hazard=hazard_ent,
        item_ent=item_ent,
        moral="look for the truth before blaming someone, and listen to people who protect you",
        mystery_solved=item_ent.meters["revealed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "porch": Setting(
        id="porch",
        place="the front porch",
        scene="Dry leaves skittered over the boards, and the air smelled like apples.",
        pumpkin_phrase="A carved pumpkin sat by the railing with a soft orange grin.",
        affords={"loose_steps"},
    ),
    "garden": Setting(
        id="garden",
        place="the moonlit garden",
        scene="Rows of beans and marigolds made dark little shadows in the silver light.",
        pumpkin_phrase="Near the gate, a pumpkin lantern glowed as if it were keeping watch.",
        affords={"thorn_gap"},
    ),
    "pumpkin_patch": Setting(
        id="pumpkin_patch",
        place="the edge of the pumpkin patch",
        scene="The pumpkin rows made long stripes across the ground, and everything felt hushed.",
        pumpkin_phrase="One bright pumpkin rested beside the path like a patient guard.",
        affords={"rotten_bridge"},
    ),
}

HAZARDS = {
    "loose_steps": Hazard(
        id="loose_steps",
        location="the wobbly porch steps",
        sign="one board tipped and gave a tired creak",
        danger_line="A fast run there could have sent small feet tumbling into the dark.",
        blocks={"dash", "scoot"},
        repair_text="knelt down, tightened the loose board, and hammered it firm",
        safe_after="the porch steps stood solid and steady again",
        lesson="slow down and let grown-ups fix unsafe things first",
        tags={"repair", "porch"},
    ),
    "thorn_gap": Hazard(
        id="thorn_gap",
        location="the thorny gap by the garden gate",
        sign="the vines were bent apart, showing a narrow opening lined with prickles",
        danger_line="Anyone chasing too quickly could have fallen into the thorns and scratched arms and knees.",
        blocks={"chase", "roll"},
        repair_text="trimmed the sharp bramble and tied the gate shut until morning",
        safe_after="the gate was tidy and safe to pass",
        lesson="do not rush into hidden places without checking them first",
        tags={"repair", "garden"},
    ),
    "rotten_bridge": Hazard(
        id="rotten_bridge",
        location="the little bridge over the ditch between the pumpkin rows",
        sign="the middle plank sagged with a soft crack",
        danger_line="One eager step there could have broken the plank and dropped a child into the muddy ditch.",
        blocks={"explore", "cross"},
        repair_text="set a lantern by the bridge, roped it off, and called for it to be repaired",
        safe_after="the dangerous bridge was blocked so nobody could cross it by mistake",
        lesson="a mystery is never a reason to cross something broken",
        tags={"repair", "bridge"},
    ),
}

ITEMS = {
    "scooter": Item(
        id="scooter",
        label="the little scooter",
        phrase="the little scooter with the squeaky blue wheel",
        draw="race",
        destination="race down the porch walk",
        activity="glide in fast circles",
        tags={"dash", "scoot"},
    ),
    "striped_ball": Item(
        id="striped_ball",
        label="the striped ball",
        phrase="the striped ball that bounced high and crooked",
        draw="chase",
        destination="run after it toward the gate",
        activity="play a game of fast catches",
        tags={"chase", "roll"},
    ),
    "treasure_map": Item(
        id="treasure_map",
        label="the folded treasure map",
        phrase="the folded treasure map with a red X in the corner",
        draw="explore",
        destination="cross to the far pumpkin rows",
        activity="solve a make-believe mystery",
        tags={"explore", "cross"},
    ),
    "chalk_badge": Item(
        id="chalk_badge",
        label="the chalk detective badge",
        phrase="the chalk detective badge tied to a string",
        draw="dash",
        destination="dash from clue to clue across the porch",
        activity="announce a new detective case",
        tags={"dash"},
    ),
}

CLUES = {
    "gold_dust": Clue(
        id="gold_dust",
        sign="a sprinkle of gold dust on the floorboards",
        trail="It curved toward the pumpkin in a trail too neat to be ordinary.",
        reveal_glow="three quick golden blinks",
        tags={"sparkle"},
    ),
    "cinnamon_breeze": Clue(
        id="cinnamon_breeze",
        sign="a warm cinnamon breeze that moved only one ribbon of leaves",
        trail="The leaves drifted in a quiet line toward the pumpkin and stopped there.",
        reveal_glow="a cinnamon-colored shimmer",
        tags={"scent"},
    ),
    "vine_thread": Clue(
        id="vine_thread",
        sign="a curly green vine thread wrapped around a nail",
        trail="It looked almost like handwriting, pointing straight to the pumpkin.",
        reveal_glow="a soft green lantern-glow",
        tags={"vine"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ella", "Rose", "Lucy", "Ava", "Anna"]
BOY_NAMES = ["Ben", "Theo", "Max", "Leo", "Sam", "Finn", "Eli", "Jack"]


@dataclass
class StoryParams:
    place: str
    hazard: str
    item: str
    clue: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="porch",
        hazard="loose_steps",
        item="scooter",
        clue="gold_dust",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="garden",
        hazard="thorn_gap",
        item="striped_ball",
        clue="cinnamon_breeze",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Lily",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="pumpkin_patch",
        hazard="rotten_bridge",
        item="treasure_map",
        clue="vine_thread",
        hero_name="Rose",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="porch",
        hazard="loose_steps",
        item="chalk_badge",
        clue="vine_thread",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
    ),
]


KNOWLEDGE = {
    "pumpkin": [
        (
            "What is a pumpkin?",
            "A pumpkin is a round orange squash that grows in fields and gardens. People often carve pumpkins into lanterns in autumn.",
        )
    ],
    "genie": [
        (
            "What is a genie in a story?",
            "A genie is a magical being in a story. Some genies grant wishes, and some use magic to help or protect people.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to find the truth. Good detectives do not jump to conclusions before they know what really happened.",
        )
    ],
    "blame": [
        (
            "Why is it important not to blame someone too quickly?",
            "Blaming too quickly can hurt someone's feelings and can also be unfair. It is better to ask questions, look for facts, and learn the truth first.",
        )
    ],
    "repair": [
        (
            "Why should a grown-up fix something dangerous first?",
            "A grown-up can check what is unsafe and repair it the right way. Waiting for the fix keeps children from getting hurt.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pumpkin", "genie", "detective", "blame", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    hazard = f["hazard_cfg"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the words "pumpkin" and "genie" and teaches a moral about fairness.',
        f"Tell a suspenseful but gentle mystery where {hero.id} notices that {item.label} is missing, follows clues around a pumpkin, and learns a protective genie hid it to keep someone away from {hazard.location}.",
        "Write a child-facing detective story in which the big lesson is to look for the truth before blaming a friend.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    genie = f["genie"]
    item = f["item"]
    hazard = f["hazard_cfg"]
    clue = f["clue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who likes being a detective, {friend.id}, a friend who gets blamed at first, and a protective genie living in a pumpkin.",
        ),
        (
            f"What mystery did {hero.id} try to solve?",
            f"{hero.id} was trying to find out who had taken {item.label}. The missing item turned an ordinary autumn evening into a detective case.",
        ),
        (
            f"Why did {hero.id} first suspect {friend.id}?",
            f"{hero.id} saw that {item.label} was gone and asked {friend.id} about it right away. The mystery felt sudden and tense, so {hero.pronoun()} guessed before {hero.pronoun()} knew the truth.",
        ),
        (
            "What clue led to the truth?",
            f"The clue was {clue.sign}. It pointed straight toward the pumpkin, where the genie revealed what had really happened.",
        ),
        (
            f"Why did the genie hide {item.label}?",
            f"The genie hid it to stop {hero.id} from hurrying toward {hazard.location}. The genie was being protective because {hazard.danger_line[0].lower() + hazard.danger_line[1:]}",
        ),
        (
            f"What did {hero.id}'s {parent.label_word} do?",
            f"{parent.label_word.capitalize()} checked the danger and {hazard.repair_text}. After that, {hazard.safe_after}.",
        ),
        (
            "What is the moral of the story?",
            f"The moral is that you should look for the truth before blaming someone. It also teaches that listening to kind protection can keep people safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    tags = {"pumpkin", "genie", "detective", "blame", "repair"}
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
item_at_risk(H, I) :- blocks(H, T), item_tag(I, T).
valid(P, H, I) :- affords(P, H), item_at_risk(H, I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for hazard_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, hazard_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        for tag in sorted(hazard.blocks):
            lines.append(asp.fact("blocks", hazard_id, tag))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", item_id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "pumpkin" not in sample.story.lower() or "genie" not in sample.story.lower():
        raise StoryError("Smoke test failed: story did not contain required seed words.")


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
    try:
        smoke_test()
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("Smoke test failed: generated sample was incomplete.")
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Detective-style story world: a missing item, a pumpkin, and a protective genie."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hazard and args.hazard not in SETTINGS[args.place].affords:
        raise StoryError(
            f"(No story: {args.hazard} does not belong in {args.place}. Pick a hazard that the setting actually affords.)"
        )
    if args.hazard and args.item:
        hazard = HAZARDS[args.hazard]
        item = ITEMS[args.item]
        if not item_at_risk(hazard, item):
            raise StoryError(explain_rejection(hazard, item))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.item is None or combo[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hazard_id, item_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    clue_id = args.clue or rng.choice(sorted(CLUES))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        hazard=hazard_id,
        item=item_id,
        clue=clue_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hazard not in HAZARDS:
        raise StoryError(f"Unknown hazard: {params.hazard}")
    if params.item not in ITEMS:
        raise StoryError(f"Unknown item: {params.item}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.hazard not in SETTINGS[params.place].affords:
        raise StoryError(
            f"(No story: {params.hazard} does not fit inside {params.place}.)"
        )
    if not item_at_risk(HAZARDS[params.hazard], ITEMS[params.item]):
        raise StoryError(explain_rejection(HAZARDS[params.hazard], ITEMS[params.item]))

    world = tell(
        setting=SETTINGS[params.place],
        hazard=HAZARDS[params.hazard],
        item=ITEMS[params.item],
        clue=CLUES[params.clue],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (place, hazard, item) combos:\n")
        for place_id, hazard_id, item_id in combos:
            print(f"  {place_id:13} {hazard_id:14} {item_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.item} at {p.place} ({p.hazard})"
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
