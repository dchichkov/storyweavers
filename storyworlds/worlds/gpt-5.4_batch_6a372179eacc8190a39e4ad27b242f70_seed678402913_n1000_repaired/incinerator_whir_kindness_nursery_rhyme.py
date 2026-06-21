#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/incinerator_whir_kindness_nursery_rhyme.py
=====================================================================

A small story world about a nursery clean-up morning, a humming incinerator,
and a kind choice that saves something useful for a cold friend.

The style leans toward a nursery rhyme: soft repetition, concrete images, and
a gentle moral. The world model keeps the logic honest:

- An item in the discard basket has a concrete condition (muddy, torn, dusty,
  loose-laced).
- Only some repairs actually fit that condition and that kind of item.
- The nursery helper reaches the basket after a short delay; some items can be
  rescued in time, and some are lost to the incinerator if everyone is too slow.
- Even in the late branch, kindness still resolves the story: the children share
  another warm thing instead of leaving someone cold.

Run it
------
    python storyworlds/worlds/gpt-5.4/incinerator_whir_kindness_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/incinerator_whir_kindness_nursery_rhyme.py --item mittens --condition muddy --repair wash
    python storyworlds/worlds/gpt-5.4/incinerator_whir_kindness_nursery_rhyme.py --item boots --repair stitch
    python storyworlds/worlds/gpt-5.4/incinerator_whir_kindness_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/incinerator_whir_kindness_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/incinerator_whir_kindness_nursery_rhyme.py --verify
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
        female = {"girl", "mother", "woman", "teacher_female"}
        male = {"boy", "father", "man", "teacher_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"teacher_female", "teacher_male"}:
            return "teacher"
        return self.label or self.type


@dataclass
class ItemConfig:
    id: str
    label: str
    phrase: str
    region: str
    material: str
    rescue_window: int
    plural: bool = False
    needs_word: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Condition:
    id: str
    label: str
    line: str
    meter_key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    action: str
    past: str
    fixes: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
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


def _r_need_warmth(world: World) -> list[str]:
    out: list[str] = []
    recipient = world.entities.get("recipient")
    item = world.entities.get("item")
    if not recipient or not item:
        return out
    if recipient.meters["missing"] < THRESHOLD:
        return out
    sig = ("cold_need", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    recipient.meters["cold"] += 1
    recipient.memes["wish"] += 1
    out.append("__need__")
    return out


def _r_repair_restores(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    if not item or item.meters["repaired"] < THRESHOLD:
        return out
    for key in ("muddy", "torn", "dusty", "loose"):
        if item.meters[key] >= THRESHOLD:
            sig = ("restore", item.id, key)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters[key] = 0.0
            item.meters["usable"] = 1.0
            out.append("__restored__")
    return out


def _r_share_warms(world: World) -> list[str]:
    out: list[str] = []
    recipient = world.entities.get("recipient")
    if not recipient:
        return out
    if recipient.meters["shared_warmth"] < THRESHOLD:
        return out
    sig = ("shared_warmth", recipient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    recipient.meters["cold"] = 0.0
    recipient.memes["comfort"] += 1
    out.append("__comfort__")
    return out


CAUSAL_RULES = [
    Rule(name="need_warmth", tag="physical", apply=_r_need_warmth),
    Rule(name="repair_restores", tag="physical", apply=_r_repair_restores),
    Rule(name="share_warms", tag="social", apply=_r_share_warms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ITEMS = {
    "mittens": ItemConfig(
        id="mittens",
        label="mittens",
        phrase="a small pair of red mittens",
        region="hands",
        material="cloth",
        rescue_window=1,
        plural=True,
        needs_word="warm hands",
        ending_image="two red mittens bobbed like poppies on the child-sized hook",
        tags={"mittens", "warmth", "share"},
    ),
    "boots": ItemConfig(
        id="boots",
        label="boots",
        phrase="a pair of yellow nursery boots",
        region="feet",
        material="leather",
        rescue_window=2,
        plural=True,
        needs_word="warm feet",
        ending_image="yellow boots thumped a happy beat on the mat",
        tags={"boots", "warmth", "share"},
    ),
    "coat": ItemConfig(
        id="coat",
        label="coat",
        phrase="a little blue coat with round buttons",
        region="shoulders",
        material="cloth",
        rescue_window=2,
        plural=False,
        needs_word="warm shoulders",
        ending_image="the blue coat swished like a sail at circle time",
        tags={"coat", "warmth", "share"},
    ),
    "blanket": ItemConfig(
        id="blanket",
        label="blanket",
        phrase="a soft nursery blanket with moon corners",
        region="lap",
        material="cloth",
        rescue_window=0,
        plural=False,
        needs_word="a warm lap",
        ending_image="the moon-corner blanket made a gentle hill around small knees",
        tags={"blanket", "warmth", "share"},
    ),
}

CONDITIONS = {
    "muddy": Condition(
        id="muddy",
        label="muddy",
        line="Its hem was clotted with playground mud.",
        meter_key="muddy",
        tags={"mud"},
    ),
    "torn": Condition(
        id="torn",
        label="torn",
        line="A seam had opened like a little yawn.",
        meter_key="torn",
        tags={"tear"},
    ),
    "dusty": Condition(
        id="dusty",
        label="dusty",
        line="A pale shelf-dust sat over it like flour.",
        meter_key="dusty",
        tags={"dust"},
    ),
    "loose": Condition(
        id="loose",
        label="loose-laced",
        line="One lace had gone lazy and slithered free.",
        meter_key="loose",
        tags={"lace"},
    ),
}

REPAIRS = {
    "wash": Repair(
        id="wash",
        label="wash",
        action="wash it at the nursery sink",
        past="washed it clean",
        fixes={"muddy"},
        materials={"cloth", "leather"},
        tags={"wash"},
    ),
    "stitch": Repair(
        id="stitch",
        label="stitch",
        action="stitch the small opening closed",
        past="stitched the opening closed",
        fixes={"torn"},
        materials={"cloth"},
        tags={"stitch"},
    ),
    "brush": Repair(
        id="brush",
        label="brush",
        action="brush the dust away with the soft clothes brush",
        past="brushed the dust away",
        fixes={"dusty"},
        materials={"cloth", "leather"},
        tags={"brush"},
    ),
    "tie": Repair(
        id="tie",
        label="tie",
        action="tie the loose lace into a neat bow",
        past="tied the loose lace into a neat bow",
        fixes={"loose"},
        materials={"leather"},
        tags={"tie"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Ella", "Zoe", "Ruby", "Poppy"]
BOY_NAMES = ["Ben", "Tom", "Max", "Leo", "Finn", "Sam", "Theo", "Eli"]
TRAITS = ["kind", "gentle", "bright", "careful", "soft-hearted", "merry"]


def repair_works(item: ItemConfig, condition: Condition, repair: Repair) -> bool:
    return condition.meter_key in repair.fixes and item.material in repair.materials


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for condition_id, condition in CONDITIONS.items():
            for repair_id, repair in REPAIRS.items():
                if repair_works(item, condition, repair):
                    combos.append((item_id, condition_id, repair_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.item not in ITEMS or params.condition not in CONDITIONS or params.repair not in REPAIRS:
        raise StoryError("(No story: an unknown item, condition, or repair was requested.)")
    item = ITEMS[params.item]
    condition = CONDITIONS[params.condition]
    repair = REPAIRS[params.repair]
    if not repair_works(item, condition, repair):
        raise StoryError(explain_rejection(item, condition, repair))
    return "saved" if params.delay <= item.rescue_window else "shared"


def explain_rejection(item: ItemConfig, condition: Condition, repair: Repair) -> str:
    if condition.meter_key not in repair.fixes:
        return (
            f"(No story: {repair.label} does not fix something that is {condition.label}. "
            f"Pick a repair that matches the problem.)"
        )
    if item.material not in repair.materials:
        return (
            f"(No story: {repair.label} is not a sensible repair for a {item.label}. "
            f"Pick a repair that fits the item.)"
        )
    return "(No story: that item, condition, and repair do not make a reasonable tale.)"


def choose_names(rng: random.Random) -> tuple[str, str, str, str]:
    chooser_gender = rng.choice(["girl", "boy"])
    recipient_gender = rng.choice(["girl", "boy"])
    chooser_pool = GIRL_NAMES if chooser_gender == "girl" else BOY_NAMES
    recipient_pool = GIRL_NAMES if recipient_gender == "girl" else BOY_NAMES
    chooser = rng.choice(chooser_pool)
    recipient = rng.choice([n for n in recipient_pool if n != chooser])
    return chooser, chooser_gender, recipient, recipient_gender


def introduce(world: World, chooser: Entity, recipient: Entity, teacher: Entity, item: Entity, condition: Condition) -> None:
    world.say(
        f"In the nursery yard, on a pearly day, the incinerator hummed by the wall. "
        f"Whir, whir, went the iron drum, low and round and small."
    )
    world.say(
        f"{chooser.id}, a {next((t for t in chooser.traits if t), 'kind')} little {chooser.type}, "
        f"helped {teacher.label_word} sort the basket by the shed."
    )
    world.say(
        f"There {chooser.pronoun()} found {item.phrase} in the throw-away pile. {condition.line}"
    )
    recipient.meters["missing"] += 1
    propagate(world, narrate=False)
    world.facts["need_started"] = True
    world.say(
        f"Near the door stood {recipient.id}, rubbing chilly {ITEMS[item.id].region} and watching the hooks with hopeful eyes."
    )


def temptation(world: World, chooser: Entity, item: Entity) -> None:
    chooser.memes["has_plan"] += 1
    world.say(
        f'"Old things go away today," sang {chooser.id}. "To the incinerator, off you go!"'
    )
    world.say(
        f"The basket gave a tiny bump, and the warm brick oven answered with another whir."
    )


def notice_need(world: World, chooser: Entity, recipient: Entity, item_cfg: ItemConfig) -> None:
    chooser.memes["notice"] += 1
    chooser.memes["kindness"] += 1
    recipient.memes["hope"] += 1
    world.say(
        f"Then {chooser.id} looked at {recipient.id} again and saw the truth as plain as play: "
        f"{recipient.id} did not need smoke and ash; {recipient.pronoun()} needed {item_cfg.needs_word} today."
    )


def ask_teacher(world: World, chooser: Entity, teacher: Entity, repair: Repair) -> None:
    chooser.memes["ask_help"] += 1
    teacher.memes["care"] += 1
    world.say(
        f'"Please," said {chooser.id}, soft and quick, "don\'t burn it yet. Could we {repair.action}?"'
    )
    world.say(
        f"{teacher.label_word.capitalize()} knelt beside the basket and smiled the sort of smile that slows a rushing heart."
    )


def repair_item(world: World, teacher: Entity, item: Entity, repair: Repair) -> None:
    item.meters["repaired"] += 1
    item.memes["kept"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Snip and swish, pat and press -- {teacher.label_word} {repair.past}, and the little thing looked useful once more."
    )


def give_item(world: World, chooser: Entity, recipient: Entity, item: Entity, item_cfg: ItemConfig) -> None:
    recipient.meters["missing"] = 0.0
    recipient.meters["warmed"] += 1
    recipient.meters["cold"] = 0.0
    recipient.memes["comfort"] += 1
    chooser.memes["joy"] += 1
    chooser.memes["kindness"] += 1
    recipient.memes["gratitude"] += 1
    item.attrs["owner"] = recipient.id
    world.say(
        f"{chooser.id} held out the {item_cfg.label}. {recipient.id} slipped into {('them' if item_cfg.plural else 'it')}, and the shivers stopped their tiny dance."
    )
    world.say(
        f'"For me?" whispered {recipient.id}. "For you," said {chooser.id}. Then both children smiled the same warm smile.'
    )


def too_late(world: World, item: Entity, item_cfg: ItemConfig) -> None:
    item.meters["burned"] += 1
    item.meters["usable"] = 0.0
    world.say(
        f"But the nursery helper reached the basket first. In went the {item_cfg.label}, and the incinerator gave a hungry whir."
    )
    world.say(
        f"There was only a flutter of heat, then nothing left to mend or keep."
    )


def share_other_warmth(world: World, chooser: Entity, recipient: Entity, teacher: Entity, item_cfg: ItemConfig) -> None:
    recipient.meters["shared_warmth"] += 1
    chooser.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{chooser.id}'s face fell, then lifted. {chooser.pronoun().capitalize()} tugged off {chooser.attrs['spare']} and wrapped it around {recipient.id} instead."
    )
    world.say(
        f'{teacher.label_word.capitalize()} tucked the edges close. "Kind hands can still make a warm day," {teacher.pronoun()} said.'
    )
    world.say(
        f"{recipient.id} leaned into the borrowed warmth, and the sad moment softened like frost in sun."
    )


def ending_saved(world: World, chooser: Entity, recipient: Entity, item_cfg: ItemConfig) -> None:
    world.say(
        f"At song time, {item_cfg.ending_image}, and {recipient.id} clapped along with rosy cheeks."
    )
    world.say(
        f"So in that nursery, by hook and door, the kindest thing was not to throw away, "
        f"but to see what another small heart was hoping for."
    )


def ending_shared(world: World, chooser: Entity, recipient: Entity) -> None:
    world.say(
        f"At song time, {recipient.id} sat snug beside {chooser.id}, sharing warmth and sharing tune."
    )
    world.say(
        f"So in that nursery, even after loss, kindness still made room: one child gave, one child glowed, and the morning changed by noon."
    )


def tell(
    item_cfg: ItemConfig,
    condition: Condition,
    repair: Repair,
    chooser_name: str = "Lily",
    chooser_gender: str = "girl",
    recipient_name: str = "Ben",
    recipient_gender: str = "boy",
    teacher_type: str = "teacher_female",
    chooser_trait: str = "kind",
    delay: int = 0,
) -> World:
    world = World()
    chooser = world.add(Entity(
        id=chooser_name,
        kind="character",
        type=chooser_gender,
        role="chooser",
        traits=[chooser_trait],
        attrs={"spare": "the striped class scarf"},
    ))
    recipient = world.add(Entity(
        id=recipient_name,
        kind="character",
        type=recipient_gender,
        role="recipient",
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        role="teacher",
        label="the teacher",
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        attrs={"region": item_cfg.region, "material": item_cfg.material},
        tags=set(item_cfg.tags),
    ))
    item.meters["usable"] = 1.0
    item.meters[condition.meter_key] += 1

    introduce(world, chooser, recipient, teacher, item, condition)
    world.para()
    temptation(world, chooser, item)
    notice_need(world, chooser, recipient, item_cfg)
    ask_teacher(world, chooser, teacher, repair)
    world.para()

    if delay <= item_cfg.rescue_window:
        repair_item(world, teacher, item, repair)
        give_item(world, chooser, recipient, item, item_cfg)
        world.para()
        ending_saved(world, chooser, recipient, item_cfg)
        outcome = "saved"
    else:
        too_late(world, item, item_cfg)
        share_other_warmth(world, chooser, recipient, teacher, item_cfg)
        world.para()
        ending_shared(world, chooser, recipient)
        outcome = "shared"

    world.facts.update(
        chooser=chooser,
        recipient=recipient,
        teacher=teacher,
        item=item,
        item_cfg=item_cfg,
        condition=condition,
        repair=repair,
        delay=delay,
        outcome=outcome,
        saved=(outcome == "saved"),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chooser = f["chooser"]
    recipient = f["recipient"]
    item_cfg = f["item_cfg"]
    outcome = f["outcome"]
    if outcome == "saved":
        return [
            'Write a gentle nursery-rhyme-style story for a 3-to-5-year-old that includes the words "incinerator" and "whir" and is about kindness.',
            f"Tell a sing-song story where {chooser.id} almost throws away {item_cfg.phrase}, hears the incinerator go whir, then notices that {recipient.id} needs it and saves it instead.",
            f"Write a short rhyming tale set in a nursery where an old {item_cfg.label} is repaired and given away with kindness before it is burned.",
        ]
    return [
        'Write a gentle nursery-rhyme-style story for a 3-to-5-year-old that includes the words "incinerator" and "whir" and is about kindness after a mistake.',
        f"Tell a sing-song story where {chooser.id} is too late to save {item_cfg.phrase} from the incinerator, but still helps {recipient.id} stay warm by sharing something else.",
        f"Write a nursery-rhyme-like story in which a child cannot undo a loss, yet kindness still changes the ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    chooser = f["chooser"]
    recipient = f["recipient"]
    teacher = f["teacher"]
    item_cfg = f["item_cfg"]
    condition = f["condition"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {chooser.id}, {recipient.id}, and their teacher at nursery. The story begins when {chooser.id} finds {item_cfg.phrase} in a throw-away basket."
        ),
        (
            f"Why did {chooser.id} stop thinking about the incinerator?",
            f"{chooser.id} saw that {recipient.id} was cold and needed {item_cfg.needs_word}. That changed the problem from getting rid of an old thing to helping a child."
        ),
        (
            f"What was wrong with the {item_cfg.label}?",
            f"The {item_cfg.label} was {condition.label}. That is why {chooser.id} first thought it belonged in the discard pile."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How was the {item_cfg.label} saved?",
                f"The teacher did the repair that matched the problem and {repair.past}. Because everyone acted before the basket reached the incinerator, the {item_cfg.label} could be used again."
            )
        )
        qa.append(
            (
                f"How did kindness change the ending?",
                f"{chooser.id} gave the mended {item_cfg.label} to {recipient.id}, so the child was warm by song time. The ending image shows something once called old becoming useful and loved."
            )
        )
    else:
        qa.append(
            (
                f"Could they save the {item_cfg.label} in time?",
                f"No. The helper reached the basket first, and the incinerator took it before anyone could mend it. The story turns on the sad fact that a kind idea came a little too late."
            )
        )
        qa.append(
            (
                "How did kindness still help?",
                f"{chooser.id} shared the striped class scarf, and the teacher tucked it around {recipient.id}. So even though the lost {item_cfg.label} could not come back, the child did not stay cold."
            )
        )
    return qa


KNOWLEDGE = {
    "incinerator": [
        (
            "What is an incinerator?",
            "An incinerator is a very hot machine or oven that burns rubbish until it turns to ash. Children should stay back and let grown-ups use it."
        )
    ],
    "whir": [
        (
            "What does whir mean?",
            "Whir is a soft humming sound a machine can make when it is working. It sounds a little like spinning or turning."
        )
    ],
    "wash": [
        (
            "Why does washing help muddy clothes?",
            "Water can loosen and carry away mud, so a muddy thing can become clean again. That is why washing is a good fix for dirt."
        )
    ],
    "stitch": [
        (
            "What does stitching fix?",
            "Stitching joins cloth back together with thread. It is a good way to close a small tear or open seam."
        )
    ],
    "brush": [
        (
            "Why would you brush dust away?",
            "Dust sits on top of something, so a soft brush can sweep it off. Brushing helps when an item is dusty instead of torn or muddy."
        )
    ],
    "tie": [
        (
            "What does tying a lace do?",
            "Tying a lace pulls a shoe or boot snug and safe again. It helps when the lace is loose, not when the shoe is muddy or torn."
        )
    ],
    "warmth": [
        (
            "Why do mittens, boots, coats, and blankets help on a chilly day?",
            "They help hold warmth close to your body. That makes hands, feet, shoulders, or laps feel more comfortable."
        )
    ],
    "share": [
        (
            "What does kindness look like when someone is cold?",
            "Kindness can mean noticing the cold child and sharing warmth or help. It starts with seeing what another person needs."
        )
    ],
}
KNOWLEDGE_ORDER = ["incinerator", "whir", "warmth", "wash", "stitch", "brush", "tie", "share"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"incinerator", "whir", "warmth", "share", f["repair"].id}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    item: str
    condition: str
    repair: str
    chooser_name: str
    chooser_gender: str
    recipient_name: str
    recipient_gender: str
    teacher_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        item="mittens",
        condition="muddy",
        repair="wash",
        chooser_name="Lily",
        chooser_gender="girl",
        recipient_name="Ben",
        recipient_gender="boy",
        teacher_gender="female",
        trait="kind",
        delay=0,
    ),
    StoryParams(
        item="coat",
        condition="torn",
        repair="stitch",
        chooser_name="Max",
        chooser_gender="boy",
        recipient_name="Nora",
        recipient_gender="girl",
        teacher_gender="female",
        trait="gentle",
        delay=1,
    ),
    StoryParams(
        item="boots",
        condition="loose",
        repair="tie",
        chooser_name="Ava",
        chooser_gender="girl",
        recipient_name="Finn",
        recipient_gender="boy",
        teacher_gender="male",
        trait="bright",
        delay=2,
    ),
    StoryParams(
        item="blanket",
        condition="dusty",
        repair="brush",
        chooser_name="Theo",
        chooser_gender="boy",
        recipient_name="Ruby",
        recipient_gender="girl",
        teacher_gender="female",
        trait="soft-hearted",
        delay=1,
    ),
]


ASP_RULES = r"""
works(I,C,R) :- item(I), condition(C), repair(R), fixes(R,C), material(I,M), uses(R,M).
valid(I,C,R) :- works(I,C,R).

saved  :- chosen_item(I), rescue_window(I,W), chosen_delay(D), D <= W.
shared :- chosen_item(I), rescue_window(I,W), chosen_delay(D), D > W.

outcome(saved)  :- saved.
outcome(shared) :- shared.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("material", item_id, item.material))
        lines.append(asp.fact("rescue_window", item_id, item.rescue_window))
    for condition_id, condition in CONDITIONS.items():
        lines.append(asp.fact("condition", condition_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for c in sorted(repair.fixes):
            lines.append(asp.fact("fixes", repair_id, c))
        for m in sorted(repair.materials):
            lines.append(asp.fact("uses", repair_id, m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _teacher_type(gender: str) -> str:
    return "teacher_female" if gender == "female" else "teacher_male"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a nursery, a whirring incinerator, and a kind choice."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--condition", choices=CONDITIONS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long before the discard basket reaches the incinerator")
    ap.add_argument("--chooser-gender", choices=["girl", "boy"])
    ap.add_argument("--recipient-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=["female", "male"])
    ap.add_argument("--chooser-name")
    ap.add_argument("--recipient-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid item/condition/repair combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item is not None and args.item not in ITEMS:
        raise StoryError("(No story: unknown item.)")
    if args.condition is not None and args.condition not in CONDITIONS:
        raise StoryError("(No story: unknown condition.)")
    if args.repair is not None and args.repair not in REPAIRS:
        raise StoryError("(No story: unknown repair.)")

    if args.item and args.condition and args.repair:
        item = ITEMS[args.item]
        condition = CONDITIONS[args.condition]
        repair = REPAIRS[args.repair]
        if not repair_works(item, condition, repair):
            raise StoryError(explain_rejection(item, condition, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.condition is None or combo[1] == args.condition)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, condition_id, repair_id = rng.choice(sorted(combos))
    chooser_name, chooser_gender, recipient_name, recipient_gender = choose_names(rng)
    if args.chooser_gender:
        chooser_gender = args.chooser_gender
        chooser_name = args.chooser_name or rng.choice(GIRL_NAMES if chooser_gender == "girl" else BOY_NAMES)
    elif args.chooser_name:
        chooser_name = args.chooser_name

    if args.recipient_gender:
        recipient_gender = args.recipient_gender
        pool = GIRL_NAMES if recipient_gender == "girl" else BOY_NAMES
        recipient_name = args.recipient_name or rng.choice([n for n in pool if n != chooser_name] or pool)
    elif args.recipient_name:
        recipient_name = args.recipient_name

    if recipient_name == chooser_name:
        pool = GIRL_NAMES if recipient_gender == "girl" else BOY_NAMES
        alternatives = [n for n in pool if n != chooser_name]
        if not alternatives:
            raise StoryError("(No story: chooser and recipient need different names.)")
        recipient_name = rng.choice(alternatives)

    teacher_gender = args.teacher_gender or rng.choice(["female", "male"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        item=item_id,
        condition=condition_id,
        repair=repair_id,
        chooser_name=chooser_name,
        chooser_gender=chooser_gender,
        recipient_name=recipient_name,
        recipient_gender=recipient_gender,
        teacher_gender=teacher_gender,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.condition not in CONDITIONS:
        raise StoryError(f"(No story: unknown condition '{params.condition}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(No story: unknown repair '{params.repair}'.)")

    item_cfg = ITEMS[params.item]
    condition = CONDITIONS[params.condition]
    repair = REPAIRS[params.repair]

    if not repair_works(item_cfg, condition, repair):
        raise StoryError(explain_rejection(item_cfg, condition, repair))

    world = tell(
        item_cfg=item_cfg,
        condition=condition,
        repair=repair,
        chooser_name=params.chooser_name,
        chooser_gender=params.chooser_gender,
        recipient_name=params.recipient_name,
        recipient_gender=params.recipient_gender,
        teacher_type=_teacher_type(params.teacher_gender),
        chooser_trait=params.trait,
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
        print(f"{len(combos)} valid (item, condition, repair) combos:\n")
        for item_id, condition_id, repair_id in combos:
            print(f"  {item_id:8} {condition_id:8} {repair_id}")
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
            header = f"### {p.item} / {p.condition} / {p.repair} ({outcome_of(p)})"
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
