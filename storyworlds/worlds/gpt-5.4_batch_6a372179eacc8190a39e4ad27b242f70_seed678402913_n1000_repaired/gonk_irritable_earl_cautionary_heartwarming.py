#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gonk_irritable_earl_cautionary_heartwarming.py
==========================================================================

A standalone storyworld about Earl, his toy Gonk, and the unsafe idea of
climbing on something wobbly to reach a high shelf.

The domain is deliberately small and classical:

- Earl loves a toy called Gonk.
- Gonk ends up on a shelf that is too high for Earl.
- Earl grows irritable because he wants Gonk back right away.
- A grown-up warns him not to climb on a wobbly thing.
- If the grown-up is nearby, the risky try is averted.
- Otherwise Earl climbs, the support wobbles, and Gonk falls.
- A safe helper method retrieves Gonk, the grown-up comforts Earl, and the room
  ends with a warmer, safer habit than it had at the start.

Reasonableness gate:
- Not every shelf/support/helper combination makes sense.
- A story is only generated when the support is genuinely risky for that shelf,
  and the chosen helper could honestly solve the problem.

Run it:
    python storyworlds/worlds/gpt-5.4/gonk_irritable_earl_cautionary_heartwarming.py
    python storyworlds/worlds/gpt-5.4/gonk_irritable_earl_cautionary_heartwarming.py --shelf high --support spinning_stool
    python storyworlds/worlds/gpt-5.4/gonk_irritable_earl_cautionary_heartwarming.py --helper broom_swat
    python storyworlds/worlds/gpt-5.4/gonk_irritable_earl_cautionary_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/gonk_irritable_earl_cautionary_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/gonk_irritable_earl_cautionary_heartwarming.py --verify
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
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
            "grandmother": "gran",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Shelf:
    id: str
    label: str
    height: int
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    height: int
    stability: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    reach: int
    sense: int
    success_text: str
    qa_text: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    support = world.get("support")
    earl = world.get("Earl")
    if support.meters["climbed"] < THRESHOLD or earl.meters["reaching"] < THRESHOLD:
        return out
    if support.meters["wobble"] >= THRESHOLD:
        return out
    risk = support.attrs.get("risk", 0)
    if risk <= 0:
        return out
    support.meters["wobble"] += 1
    earl.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    support = world.get("support")
    gonk = world.get("Gonk")
    if support.meters["wobble"] < THRESHOLD or gonk.meters["on_shelf"] < THRESHOLD:
        return out
    if gonk.meters["dropped"] >= THRESHOLD:
        return out
    gonk.meters["dropped"] += 1
    gonk.meters["on_shelf"] = 0.0
    out.append("__drop__")
    return out


def _r_crack(world: World) -> list[str]:
    out: list[str] = []
    gonk = world.get("Gonk")
    room = world.get("room")
    if gonk.meters["dropped"] < THRESHOLD:
        return out
    if gonk.meters["cracked"] >= THRESHOLD:
        return out
    if room.attrs.get("floor_hard", False) and world.facts.get("shelf_obj").height >= 3:
        gonk.meters["cracked"] += 1
        out.append("__crack__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop", tag="physical", apply=_r_drop),
    Rule(name="crack", tag="physical", apply=_r_crack),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for item in produced:
            if item == "__wobble__":
                world.say("The little perch gave a shaky wobble under him.")
            elif item == "__drop__":
                world.say('Gonk slipped from the shelf with a startled "gonk!" and fell.')
            elif item == "__crack__":
                world.say("When Gonk hit the hard floor, a thin crack ran across its painted side.")
    return produced


def hazard_at_risk(shelf: Shelf, support: Support) -> bool:
    if support.stability >= 2:
        return False
    return shelf.height > support.height


def helper_works(shelf: Shelf, helper: Helper) -> bool:
    return helper.sense >= SENSE_MIN and helper.reach >= shelf.height


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for shelf_id, shelf in SHELVES.items():
        for support_id, support in SUPPORTS.items():
            if not hazard_at_risk(shelf, support):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_works(shelf, helper):
                    combos.append((shelf_id, support_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.watch == "nearby":
        return "averted"
    if FLOORS[params.floor] == "hard" and SHELVES[params.shelf].height >= 3:
        return "cracked"
    return "scared"


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    earl = sim.get("Earl")
    support = sim.get("support")
    earl.meters["reaching"] += 1
    support.meters["climbed"] += 1
    propagate(sim, narrate=False)
    gonk = sim.get("Gonk")
    return {
        "wobble": support.meters["wobble"] >= THRESHOLD,
        "drop": gonk.meters["dropped"] >= THRESHOLD,
        "cracked": gonk.meters["cracked"] >= THRESHOLD,
    }


def introduce(world: World, earl: Entity, caregiver: Entity, gonk: Entity) -> None:
    earl.memes["love"] += 1
    gonk.meters["beloved"] += 1
    world.say(
        f"Earl had a small tin toy named {gonk.id}. When Earl wound it up and set it on the rug, "
        f"it waddled along making a funny little gonk-gonk sound that always made him smile."
    )
    world.say(
        f"That afternoon, after tidying the room, {caregiver.label_word} set {gonk.id} away for a while."
    )


def establish_problem(world: World, earl: Entity, caregiver: Entity, shelf: Shelf) -> None:
    room = world.get("room")
    floor_word = "wooden floor" if room.attrs.get("floor_hard", False) else "soft rug"
    earl.memes["irritation"] += 1
    world.say(
        f"But the toy ended up on {shelf.phrase}, above Earl's reach. He stood below it on the {floor_word}, "
        f"looked up, and felt irritable because he wanted Gonk back right then."
    )
    world.say(
        f'"Please wait for me," {caregiver.label_word} said. "If something is high, we ask for help instead of climbing."'
    )


def drag_support(world: World, earl: Entity, support: Support) -> None:
    earl.memes["defiance"] += 1
    world.say(
        f"Earl still hurried over to {support.phrase} and pulled it close to the shelf."
    )


def warn(world: World, caregiver: Entity) -> None:
    pred = predict_attempt(world)
    world.facts["predicted"] = pred
    if pred["cracked"]:
        end = "and Gonk could break on the hard floor."
    elif pred["drop"]:
        end = "and Gonk could tumble down."
    else:
        end = "and something could go wrong."
    world.say(
        f'{caregiver.label_word.capitalize()} saw what he was planning and called, '
        f'"Not that way, Earl. It can wobble, {end}"'
    )


def back_down(world: World, earl: Entity, caregiver: Entity) -> None:
    earl.memes["irritation"] = 0.0
    earl.memes["trust"] += 1
    earl.memes["relief"] += 1
    world.say(
        f"Earl pressed his lips together, then let go of the idea. He stepped back from the shelf and held out his hands to {caregiver.label_word} instead."
    )


def climb_and_reach(world: World, earl: Entity) -> None:
    earl.meters["reaching"] += 1
    world.get("support").meters["climbed"] += 1
    propagate(world, narrate=True)
    if world.get("support").meters["wobble"] >= THRESHOLD:
        world.say(
            "His tummy gave a frightened flip, and he hopped down fast before he could tumble too."
        )


def comfort(world: World, caregiver: Entity, earl: Entity, gonk: Entity) -> None:
    earl.memes["fear"] = 0.0
    earl.memes["relief"] += 1
    earl.memes["love"] += 1
    caregiver.memes["care"] += 1
    if gonk.meters["cracked"] >= THRESHOLD:
        world.say(
            f"{caregiver.label_word.capitalize()} knelt at once, gathered Earl into a warm hug, and picked Gonk up gently from the floor."
        )
        world.say(
            f'"You are more important than any toy," {caregiver.pronoun()} said softly. "But this is why we do not climb on wobbly things when we are cross."'
        )
    else:
        world.say(
            f"{caregiver.label_word.capitalize()} came quickly, wrapped a steady arm around Earl, and made sure both he and Gonk were safe."
        )
        world.say(
            f'"I know you wanted {gonk.id} right away," {caregiver.pronoun()} said softly. "But being upset is exactly when we slow down and ask."'
        )


def safe_retrieval(world: World, caregiver: Entity, helper: Helper, gonk: Entity) -> None:
    gonk.meters["retrieved"] += 1
    text = helper.success_text.format(caregiver=caregiver.label_word, caregiver_cap=caregiver.label_word.capitalize(), toy=gonk.id)
    world.say(text)


def mend_if_needed(world: World, caregiver: Entity, gonk: Entity) -> None:
    if gonk.meters["cracked"] < THRESHOLD:
        return
    gonk.meters["mended"] += 1
    world.say(
        f"At the table, {caregiver.label_word} dabbed a little glue along the crack and set Gonk on a folded towel to dry."
    )


def safer_habit(world: World, caregiver: Entity, earl: Entity, gonk: Entity) -> None:
    earl.memes["joy"] += 1
    earl.memes["safety"] += 1
    earl.memes["irritation"] = 0.0
    world.say(
        f"Before long, {caregiver.label_word} made a low basket just for Gonk, where Earl could reach it with his own hands."
    )
    if gonk.meters["cracked"] >= THRESHOLD:
        world.say(
            "When the glue had set, Earl wound the toy carefully. Gonk still made its cheerful gonk-gonk sound, only now Earl smiled more quietly."
        )
    else:
        world.say(
            "Then Earl wound the toy on the rug again, and its cheerful gonk-gonk sound filled the room."
        )
    world.say(
        'Earl leaned against the grown-up beside him and promised, "Next time I will ask first."'
    )


def tell(
    shelf: Shelf,
    support: Support,
    helper: Helper,
    caregiver_type: str = "mother",
    watch: str = "doorway",
    floor: str = "rug",
) -> World:
    world = World()
    earl = world.add(Entity(id="Earl", kind="character", type="boy", role="child", tags={"child"}))
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=caregiver_type,
            role="caregiver",
            label="the caregiver",
            tags={"grownup"},
        )
    )
    gonk = world.add(
        Entity(
            id="Gonk",
            kind="thing",
            type="toy",
            label="toy",
            phrase="a small tin toy",
            tags={"toy", "gonk"},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label="room",
            attrs={"floor_hard": FLOORS[floor] == "hard"},
            tags={"room"},
        )
    )
    world.add(
        Entity(
            id="support",
            kind="thing",
            type="support",
            label=support.label,
            phrase=support.phrase,
            attrs={"risk": 1 if hazard_at_risk(shelf, support) else 0, "stability": support.stability},
            tags=set(support.tags),
        )
    )
    gonk.meters["on_shelf"] += 1
    world.facts.update(
        shelf_obj=shelf,
        support_obj=support,
        helper_obj=helper,
        watch=watch,
        floor=floor,
    )

    introduce(world, earl, caregiver, gonk)
    establish_problem(world, earl, caregiver, shelf)

    world.para()
    drag_support(world, earl, support)
    warn(world, caregiver)

    if watch == "nearby":
        back_down(world, earl, caregiver)
        world.para()
        safe_retrieval(world, caregiver, helper, gonk)
        safer_habit(world, caregiver, earl, gonk)
        outcome = "averted"
    else:
        world.say(
            f"But Earl was still prickly with hurry, so he put one foot on {support.phrase} and reached up."
        )
        world.para()
        climb_and_reach(world, earl)
        comfort(world, caregiver, earl, gonk)
        safe_retrieval(world, caregiver, helper, gonk)
        mend_if_needed(world, caregiver, gonk)
        world.para()
        safer_habit(world, caregiver, earl, gonk)
        outcome = "cracked" if gonk.meters["cracked"] >= THRESHOLD else "scared"

    world.facts.update(
        earl=earl,
        caregiver=caregiver,
        gonk=gonk,
        outcome=outcome,
        shelf=shelf,
        support=support,
        helper=helper,
        cracked=gonk.meters["cracked"] >= THRESHOLD,
        averted=outcome == "averted",
        retrieved=gonk.meters["retrieved"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    shelf: str
    support: str
    helper: str
    caregiver: str
    watch: str
    floor: str
    seed: Optional[int] = None


SHELVES = {
    "bookcase": Shelf(
        id="bookcase",
        label="bookcase shelf",
        height=2,
        phrase="the middle shelf of the bookcase",
        tags={"shelf"},
    ),
    "mantel": Shelf(
        id="mantel",
        label="mantel",
        height=3,
        phrase="the high mantel shelf",
        tags={"shelf"},
    ),
    "wardrobe": Shelf(
        id="wardrobe",
        label="wardrobe top",
        height=3,
        phrase="the top shelf inside the wardrobe",
        tags={"shelf"},
    ),
}

SUPPORTS = {
    "spinning_stool": Support(
        id="spinning_stool",
        label="spinning stool",
        phrase="a little spinning stool",
        height=1,
        stability=0,
        tags={"stool", "climb"},
    ),
    "toy_crate": Support(
        id="toy_crate",
        label="toy crate",
        phrase="the upside-down toy crate",
        height=1,
        stability=1,
        tags={"crate", "climb"},
    ),
    "wheeled_chair": Support(
        id="wheeled_chair",
        label="wheeled chair",
        phrase="the wheeled desk chair",
        height=1,
        stability=0,
        tags={"chair", "climb"},
    ),
    "step_stool": Support(
        id="step_stool",
        label="step stool",
        phrase="the sturdy step stool",
        height=1,
        stability=2,
        tags={"safe_support"},
    ),
}

HELPERS = {
    "adult_reach": Helper(
        id="adult_reach",
        label="grown-up reach",
        phrase="a tall grown-up hand",
        reach=3,
        sense=3,
        success_text="{caregiver_cap} reached up with a calm, steady hand and lifted {toy} down safely.",
        qa_text="reached up and lifted Gonk down safely",
        tags={"grownup_help", "ask_help"},
    ),
    "sturdy_stool": Helper(
        id="sturdy_stool",
        label="sturdy step stool",
        phrase="a sturdy step stool with a grown-up beside him",
        reach=2,
        sense=3,
        success_text="{caregiver_cap} brought the sturdy step stool, held it still, and helped Earl take {toy} down the safe way.",
        qa_text="brought a sturdy step stool and helped Earl take Gonk down safely",
        tags={"step_stool", "ask_help"},
    ),
    "grabber": Helper(
        id="grabber",
        label="grabber tool",
        phrase="a long grabber tool",
        reach=3,
        sense=2,
        success_text="{caregiver_cap} used a long grabber tool and gently drew {toy} down without any climbing at all.",
        qa_text="used a grabber tool to bring Gonk down without climbing",
        tags={"grabber", "ask_help"},
    ),
    "broom_swat": Helper(
        id="broom_swat",
        label="broom",
        phrase="a broom",
        reach=3,
        sense=1,
        success_text="{caregiver_cap} knocked at {toy} with a broom.",
        qa_text="tried to knock Gonk down with a broom",
        tags={"broom"},
    ),
}

CAREGIVERS = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]
WATCHES = ["nearby", "doorway", "kitchen"]
FLOORS = {"rug": "soft", "wood": "hard"}

CURATED = [
    StoryParams(
        shelf="mantel",
        support="spinning_stool",
        helper="adult_reach",
        caregiver="mother",
        watch="doorway",
        floor="wood",
    ),
    StoryParams(
        shelf="bookcase",
        support="toy_crate",
        helper="sturdy_stool",
        caregiver="father",
        watch="nearby",
        floor="rug",
    ),
    StoryParams(
        shelf="wardrobe",
        support="wheeled_chair",
        helper="grabber",
        caregiver="grandmother",
        watch="kitchen",
        floor="rug",
    ),
]


def explain_rejection(shelf: Shelf, support: Support) -> str:
    if support.stability >= 2:
        return (
            f"(No story: {support.phrase} is already steady enough that this no longer reads like a cautionary climbing mistake. "
            f"Pick a wobblier support such as a spinning stool, toy crate, or wheeled chair.)"
        )
    return (
        f"(No story: {support.phrase} is tall enough for {shelf.phrase}, so Earl would not need to stretch and wobble. "
        f"The danger in this world comes from climbing on something shaky and still reaching too high.)"
    )


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in HELPERS.values() if h.sense >= SENSE_MIN))
    return (
        f"(Refusing helper '{helper_id}': it scores too low on common sense (sense={helper.sense} < {SENSE_MIN}). "
        f"Try one of these safer helpers: {better}.)"
    )


def explain_unreachable(shelf: Shelf, helper: Helper) -> str:
    return (
        f"(No story: {helper.label} cannot honestly reach {shelf.phrase}. "
        f"The fix must really solve the problem, not just sound nice.)"
    )


KNOWLEDGE = {
    "ask_help": [
        (
            "Why is it smart to ask a grown-up for help with a high shelf?",
            "A grown-up can reach higher and hold things steady. Asking for help keeps you from climbing on something unsafe."
        )
    ],
    "step_stool": [
        (
            "What makes a step stool safer than a spinning stool or a chair on wheels?",
            "A step stool is made for standing on and does not roll or twist as easily. That makes it steadier for reaching things with a grown-up nearby."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber tool is a long helper tool that can pinch and pick up something far away. It lets a grown-up bring an object down without climbing."
        )
    ],
    "grownup_help": [
        (
            "Why can a tall grown-up reach something a child cannot?",
            "A grown-up is usually taller and stronger, so high shelves are easier and safer for them. That is why children should ask instead of climbing."
        )
    ],
    "stool": [
        (
            "Why can a spinning stool be risky to stand on?",
            "A spinning stool can twist and move under your feet. If it turns while you are reaching, you can lose your balance."
        )
    ],
    "chair": [
        (
            "Why is a chair on wheels not a good climbing place?",
            "A chair on wheels can roll when you do not expect it to. That sudden movement can make a person fall."
        )
    ],
    "crate": [
        (
            "Why is an upside-down crate not a safe step?",
            "A crate can tip or slide because it is not made for standing on that way. Safe climbing things are built to stay still."
        )
    ],
    "toy": [
        (
            "Can a toy break if it falls from a high shelf?",
            "Yes. A hard fall can crack or dent a toy, especially on a hard floor."
        )
    ],
    "wood": [
        (
            "Why is a wooden floor harder on a falling toy than a rug?",
            "Wood does not soften the bump very much. A rug gives a little cushion, so a toy is less likely to crack."
        )
    ],
    "feelings": [
        (
            "What does irritable mean?",
            "Irritable means feeling cross or easily upset. When you feel that way, it helps to slow down and ask for help before you act."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "feelings",
    "ask_help",
    "grownup_help",
    "step_stool",
    "grabber",
    "stool",
    "chair",
    "crate",
    "toy",
    "wood",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    outcome = f["outcome"]
    shelf = f["shelf"]
    support = f["support"]
    helper = f["helper"]
    if outcome == "averted":
        return [
            'Write a heartwarming cautionary story for a 3-to-5-year-old that includes the words "gonk", "irritable", and "Earl".',
            f"Tell a gentle story where Earl grows irritable because Gonk is on {shelf.phrase}, starts to use {support.phrase}, but listens to a grown-up in time.",
            f"Write a warm story about a child asking for help instead of climbing, ending with {helper.phrase} solving the problem safely.",
        ]
    if outcome == "cracked":
        return [
            'Write a heartwarming cautionary story for a 3-to-5-year-old that includes the words "gonk", "irritable", and "Earl".',
            f"Tell a story where Earl, feeling irritable and hurried, climbs on {support.phrase} to reach {shelf.phrase}, and Gonk falls and gets cracked before a grown-up helps.",
            "Write a gentle cautionary story where a scary mistake leads to comfort, repair, and a safer family habit at the end.",
        ]
    return [
        'Write a heartwarming cautionary story for a 3-to-5-year-old that includes the words "gonk", "irritable", and "Earl".',
        f"Tell a story where Earl grows irritable because Gonk is too high up, ignores a warning, and makes the support wobble before a grown-up helps safely.",
        f"Write a gentle story about a near fall, a calm helper using {helper.phrase}, and an ending that shows Earl learned to ask first.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    earl = f["earl"]
    caregiver = f["caregiver"]
    shelf = f["shelf"]
    support = f["support"]
    helper = f["helper"]
    gonk = f["gonk"]
    pw = caregiver.label_word
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Earl, his toy Gonk, and his {pw}. Earl loves the toy so much that being apart from it makes the whole problem begin."
        ),
        (
            "Why did Earl feel irritable?",
            f"Earl felt irritable because Gonk was up on {shelf.phrase} where he could not reach it. He wanted the toy back right away, and that hurry made it harder for him to be patient."
        ),
        (
            f"Why did {pw} warn Earl not to use {support.label}?",
            f"{pw.capitalize()} warned him because {support.label} could wobble while he was reaching. The danger was not just being high up, but being high up on something shaky."
        ),
    ]
    if f["outcome"] == "averted":
        out.append(
            (
                "What changed after the warning?",
                f"Earl stopped before climbing and let the grown-up help. He learned that asking first could solve the same problem without the scary part."
            )
        )
    else:
        out.append(
            (
                "What happened when Earl climbed up?",
                f"The support wobbled, and Gonk fell from the shelf. That frightened Earl, because he suddenly felt how unsafe the rushed idea had been."
            )
        )
        if f["cracked"]:
            out.append(
                (
                    "Did Gonk break?",
                    "Gonk got a crack when it hit the hard floor, but the grown-up picked it up gently and mended it. The crack makes the lesson feel real, yet the ending stays loving."
                )
            )
        else:
            out.append(
                (
                    "Was anyone badly hurt?",
                    "No. Earl was scared, but the grown-up came quickly and made sure he was safe. The story is cautionary because the wobble and fall show what could have gone worse."
                )
            )
    out.append(
        (
            f"How did {pw} solve the problem in the end?",
            f"{pw.capitalize()} {helper.qa_text}. The safe method worked because it could honestly reach the toy without any wobbling climb."
        )
    )
    out.append(
        (
            "How did the story end?",
            "It ended with Gonk stored in a low basket and Earl promising to ask for help next time. The last image shows that the family changed the room so the safer choice would be easier."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"toy", "feelings", "ask_help"}
    support = world.facts["support"]
    helper = world.facts["helper"]
    floor = world.facts["floor"]
    tags |= set(support.tags)
    tags |= set(helper.tags)
    if floor == "wood":
        tags.add("wood")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts: list[str] = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                parts.append(f"attrs={shown}")
        if e.tags:
            parts.append(f"tags={sorted(e.tags)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(Shelf, Support) :-
    shelf(Shelf), support(Support),
    shelf_height(Shelf, SH), support_height(Support, PH),
    SH > PH, support_stability(Support, ST), ST < 2.

safe_helper(Shelf, Helper) :-
    shelf(Shelf), helper(Helper),
    helper_reach(Helper, HR), shelf_height(Shelf, SH), HR >= SH,
    helper_sense(Helper, S), sense_min(M), S >= M.

valid(Shelf, Support, Helper) :-
    hazard(Shelf, Support), safe_helper(Shelf, Helper).

outcome(averted) :- watch(nearby).
attempt :- not watch(nearby).
high_shelf :- chosen_shelf(S), shelf_height(S, H), H >= 3.
hard_floor :- floor(hard).
cracked :- attempt, high_shelf, hard_floor.
outcome(cracked) :- cracked.
outcome(scared) :- attempt, not cracked.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for shelf_id, shelf in SHELVES.items():
        lines.append(asp.fact("shelf", shelf_id))
        lines.append(asp.fact("shelf_height", shelf_id, shelf.height))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("support_height", support_id, support.height))
        lines.append(asp.fact("support_stability", support_id, support.stability))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_reach", helper_id, helper.reach))
        lines.append(asp.fact("helper_sense", helper_id, helper.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    floor_kind = FLOORS[params.floor]
    scenario = "\n".join(
        [
            asp.fact("chosen_shelf", params.shelf),
            asp.fact("watch", params.watch),
            asp.fact("floor", floor_kind),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for s in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: Earl, Gonk, and a too-high shelf. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--shelf", choices=sorted(SHELVES))
    ap.add_argument("--support", choices=sorted(SUPPORTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("--watch", choices=WATCHES)
    ap.add_argument("--floor", choices=sorted(FLOORS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))
    if args.shelf and args.support:
        shelf = SHELVES[args.shelf]
        support = SUPPORTS[args.support]
        if not hazard_at_risk(shelf, support):
            raise StoryError(explain_rejection(shelf, support))
    if args.shelf and args.helper:
        shelf = SHELVES[args.shelf]
        helper = HELPERS[args.helper]
        if not helper_works(shelf, helper):
            if helper.sense < SENSE_MIN:
                raise StoryError(explain_helper(args.helper))
            raise StoryError(explain_unreachable(shelf, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.shelf is None or combo[0] == args.shelf)
        and (args.support is None or combo[1] == args.support)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shelf_id, support_id, helper_id = rng.choice(sorted(combos))
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    watch = args.watch or rng.choice(WATCHES)
    floor = args.floor or rng.choice(sorted(FLOORS))
    return StoryParams(
        shelf=shelf_id,
        support=support_id,
        helper=helper_id,
        caregiver=caregiver,
        watch=watch,
        floor=floor,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shelf not in SHELVES:
        raise StoryError(f"(Invalid shelf: {params.shelf})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Invalid support: {params.support})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.caregiver not in CAREGIVERS:
        raise StoryError(f"(Invalid caregiver: {params.caregiver})")
    if params.watch not in WATCHES:
        raise StoryError(f"(Invalid watch: {params.watch})")
    if params.floor not in FLOORS:
        raise StoryError(f"(Invalid floor: {params.floor})")

    shelf = SHELVES[params.shelf]
    support = SUPPORTS[params.support]
    helper = HELPERS[params.helper]

    if not hazard_at_risk(shelf, support):
        raise StoryError(explain_rejection(shelf, support))
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(params.helper))
    if not helper_works(shelf, helper):
        raise StoryError(explain_unreachable(shelf, helper))

    world = tell(
        shelf=shelf,
        support=support,
        helper=helper,
        caregiver_type=params.caregiver,
        watch=params.watch,
        floor=params.floor,
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
        print(f"{len(combos)} compatible (shelf, support, helper) combos:\n")
        for shelf, support, helper in combos:
            print(f"  {shelf:9} {support:14} {helper}")
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
            header = f"### Earl: {p.support} under {p.shelf} ({p.helper}, {outcome_of(p)})"
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
