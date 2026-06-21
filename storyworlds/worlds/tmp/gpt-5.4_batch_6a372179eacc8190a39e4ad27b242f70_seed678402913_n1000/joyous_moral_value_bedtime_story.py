#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/joyous_moral_value_bedtime_story.py
==============================================================

A standalone storyworld for gentle, joyous bedtime stories where a small conflict
over one cozy bedtime treasure is resolved through a clear moral value:
honesty, kindness, or patience.

The world model is classical and state-driven:
- two children both want the same bedtime treasure,
- one child grabs it first,
- feelings change in response to that physical state,
- a chosen moral value shapes the turning point,
- a compatible bedtime resolution lets both children rest happily.

The domain is intentionally small and constrained. Not every moral value fits
every bedtime object or every repair. A music box can be used in turns; a story
book is best shared together; a paper star can become a pair if a grown-up makes
another one. The reasonableness gate enforces that fit in Python and in an ASP
twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/joyous_moral_value_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/joyous_moral_value_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/joyous_moral_value_bedtime_story.py --qa
    python storyworlds/worlds/gpt-5.4/joyous_moral_value_bedtime_story.py --json
    python storyworlds/worlds/gpt-5.4/joyous_moral_value_bedtime_story.py --verify
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
    hush: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    label: str
    lesson: str
    opening: str
    pivot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BedtimeItem:
    id: str
    label: str
    phrase: str
    article: str
    methods: set[str]
    sensory: str
    use_word: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    method: str
    label: str
    values: set[str]
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"finder", "waiter"}]

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


def _r_clutch_hurts(world: World) -> list[str]:
    out: list[str] = []
    holder = world.entities.get("item")
    if holder is None:
        return out
    if holder.meters["held"] < THRESHOLD:
        return out
    finder = world.get("finder")
    waiter = world.get("waiter")
    sig = ("clutch_hurts",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    waiter.memes["sadness"] += 1
    waiter.memes["left_out"] += 1
    finder.memes["guilt"] += 1
    out.append("__left_out__")
    return out


def _r_truth_softens(world: World) -> list[str]:
    out: list[str] = []
    if world.get("finder").memes["truth"] < THRESHOLD:
        return out
    sig = ("truth_softens",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("waiter").memes["trust"] += 1
    world.get("finder").memes["relief"] += 1
    out.append("__truth__")
    return out


def _r_kind_offer_softens(world: World) -> list[str]:
    out: list[str] = []
    if world.get("finder").memes["generosity"] < THRESHOLD:
        return out
    sig = ("kind_softens",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("waiter").memes["hope"] += 1
    world.get("finder").memes["warmth"] += 1
    out.append("__kind__")
    return out


def _r_waiting_calms(world: World) -> list[str]:
    out: list[str] = []
    if world.get("waiter").memes["patience"] < THRESHOLD and world.get("finder").memes["patience"] < THRESHOLD:
        return out
    sig = ("waiting_calms",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for child in world.children():
        child.memes["calm"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="clutch_hurts", tag="social", apply=_r_clutch_hurts),
    Rule(name="truth_softens", tag="social", apply=_r_truth_softens),
    Rule(name="kind_softens", tag="social", apply=_r_kind_offer_softens),
    Rule(name="waiting_calms", tag="social", apply=_r_waiting_calms),
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


SETTINGS = {
    "window_nook": Setting(
        id="window_nook",
        place="a little bedroom by the window",
        hush="The curtains barely moved, and the house sounded soft and sleepy.",
        glow="Moonlight laid a pale square on the rug.",
        tags={"bedroom", "bedtime"},
    ),
    "bunk_room": Setting(
        id="bunk_room",
        place="a cozy bunk room",
        hush="The blankets were puffed up like clouds, and the hallway had gone quiet.",
        glow="A small night bulb made the ladder shine honey-gold.",
        tags={"bedroom", "bedtime"},
    ),
    "attic_nest": Setting(
        id="attic_nest",
        place="a snug attic room under the roof",
        hush="Rain whispered far above, too gentle to be scary.",
        glow="A lamplight puddle rested by the pillows.",
        tags={"bedroom", "bedtime"},
    ),
}

VALUES = {
    "honesty": MoralValue(
        id="honesty",
        label="honesty",
        lesson="telling the truth helps hearts settle",
        opening="A true voice can make a hard moment softer.",
        pivot="The child admits what happened instead of hiding behind the prize.",
        tags={"honesty", "moral"},
    ),
    "kindness": MoralValue(
        id="kindness",
        label="kindness",
        lesson="noticing another person's feelings makes room for joy",
        opening="A kind heart notices the sigh before it grows into tears.",
        pivot="The child looks closely at the other face and chooses to make room.",
        tags={"kindness", "moral"},
    ),
    "patience": MoralValue(
        id="patience",
        label="patience",
        lesson="waiting calmly can turn one small problem into a peaceful plan",
        opening="Slow breaths make bedtime troubles smaller.",
        pivot="The children stop tugging and let the calm plan arrive.",
        tags={"patience", "moral"},
    ),
}

ITEMS = {
    "moon_book": BedtimeItem(
        id="moon_book",
        label="moon book",
        phrase="a moon book with silver rabbits on the cover",
        article="the moon book",
        methods={"together"},
        sensory="Its pages made a tiny shush sound each time they turned.",
        use_word="story",
        ending_image="the silver rabbits seemed to hop across both laps",
        tags={"book", "reading", "share"},
    ),
    "music_box": BedtimeItem(
        id="music_box",
        label="music box",
        phrase="a tiny music box painted with stars",
        article="the music box",
        methods={"turns"},
        sensory="When wound, it sang a soft round tune like a sleepy bird.",
        use_word="song",
        ending_image="the tune circled the room once for one child and once for the other",
        tags={"music", "taking_turns", "share"},
    ),
    "paper_star": BedtimeItem(
        id="paper_star",
        label="paper star",
        phrase="a glowing paper star for the wall above the bed",
        article="the paper star",
        methods={"copy"},
        sensory="Its yellow paper held the last warm shine from the lamp.",
        use_word="star",
        ending_image="two bright paper stars watched over the room together",
        tags={"craft", "decoration", "sharing"},
    ),
}

RESOLUTIONS = {
    "read_together": Resolution(
        id="read_together",
        method="together",
        label="read together",
        values={"honesty", "kindness"},
        tags={"book", "sharing"},
    ),
    "song_turns": Resolution(
        id="song_turns",
        method="turns",
        label="take turns",
        values={"patience", "kindness"},
        tags={"taking_turns", "fairness"},
    ),
    "make_twin": Resolution(
        id="make_twin",
        method="copy",
        label="make another one",
        values={"honesty", "kindness"},
        tags={"craft", "fairness"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Ruby", "Ella", "Maya", "Ivy"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Noah", "Eli", "Jude", "Theo", "Max"]
TRAITS = ["sleepy", "gentle", "bright-eyed", "soft-voiced", "curious", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    value: str
    item: str
    resolution: str
    finder_name: str
    finder_gender: str
    waiter_name: str
    waiter_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="window_nook",
        value="honesty",
        item="moon_book",
        resolution="read_together",
        finder_name="Lila",
        finder_gender="girl",
        waiter_name="Owen",
        waiter_gender="boy",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        setting="bunk_room",
        value="kindness",
        item="paper_star",
        resolution="make_twin",
        finder_name="Finn",
        finder_gender="boy",
        waiter_name="Mina",
        waiter_gender="girl",
        parent="father",
        trait="gentle",
    ),
    StoryParams(
        setting="attic_nest",
        value="patience",
        item="music_box",
        resolution="song_turns",
        finder_name="Noah",
        finder_gender="boy",
        waiter_name="Ruby",
        waiter_gender="girl",
        parent="mother",
        trait="soft-voiced",
    ),
    StoryParams(
        setting="bunk_room",
        value="kindness",
        item="moon_book",
        resolution="read_together",
        finder_name="Ella",
        finder_gender="girl",
        waiter_name="Theo",
        waiter_gender="boy",
        parent="father",
        trait="bright-eyed",
    ),
    StoryParams(
        setting="window_nook",
        value="honesty",
        item="paper_star",
        resolution="make_twin",
        finder_name="Max",
        finder_gender="boy",
        waiter_name="Ivy",
        waiter_gender="girl",
        parent="mother",
        trait="curious",
    ),
]


def valid_combo(value_id: str, item_id: str, resolution_id: str) -> bool:
    value = VALUES[value_id]
    item = ITEMS[item_id]
    resolution = RESOLUTIONS[resolution_id]
    return resolution.method in item.methods and value.id in resolution.values


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for value_id in VALUES:
            for item_id in ITEMS:
                for resolution_id in RESOLUTIONS:
                    if valid_combo(value_id, item_id, resolution_id):
                        combos.append((setting_id, value_id, item_id, resolution_id))
    return combos


def explain_rejection(value_id: str, item_id: str, resolution_id: str) -> str:
    value = VALUES[value_id]
    item = ITEMS[item_id]
    resolution = RESOLUTIONS[resolution_id]
    if resolution.method not in item.methods:
        return (
            f"(No story: {item.article.capitalize()} does not fit the repair "
            f"'{resolution.label}'. This bedtime object works with "
            f"{', '.join(sorted(item.methods))}, not {resolution.method}.)"
        )
    return (
        f"(No story: the moral value {value.label} does not naturally lead to "
        f"'{resolution.label}' here. Try one of: "
        f"{', '.join(sorted(rid for rid, r in RESOLUTIONS.items() if value_id in r.values and r.method in item.methods))}.)"
    )


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def _story_pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two children"
    if a.type == "boy" and b.type == "boy":
        return "two children"
    return "two children"


def predict_feelings(item: BedtimeItem) -> dict:
    sim = World(SETTINGS["window_nook"])
    finder = sim.add(Entity(id="finder", kind="character", type="girl", role="finder"))
    waiter = sim.add(Entity(id="waiter", kind="character", type="boy", role="waiter"))
    prize = sim.add(Entity(id="item", kind="thing", type="item", label=item.label))
    prize.meters["held"] += 1
    finder.attrs["holds"] = item.id
    propagate(sim, narrate=False)
    return {
        "sadness": waiter.memes["sadness"],
        "guilt": finder.memes["guilt"],
    }


def introduce(world: World, finder: Entity, waiter: Entity, item: BedtimeItem, value: MoralValue) -> None:
    world.say(
        f"In {world.setting.place}, {finder.id} and {waiter.id} were meant to be getting sleepy."
    )
    world.say(world.setting.hush)
    world.say(world.setting.glow)
    world.say(
        f"{finder.id} was a {world.facts['trait']} {finder.type}, and {waiter.id} had already tucked warm feet under the blanket."
    )
    world.say(
        f"On the stool beside the bed rested {item.phrase}. {item.sensory}"
    )
    world.say(value.opening)


def want_same_thing(world: World, finder: Entity, waiter: Entity, item: BedtimeItem) -> None:
    finder.memes["desire"] += 1
    waiter.memes["desire"] += 1
    world.say(
        f"Both children had been hoping for {item.article} tonight."
    )
    world.say(
        f"{finder.id} reached first, and {waiter.id}'s smile paused right in the middle."
    )


def clutch_item(world: World, finder: Entity, waiter: Entity, item_ent: Entity, item: BedtimeItem) -> None:
    item_ent.meters["held"] += 1
    finder.attrs["holds"] = item.id
    finder.memes["possessive"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{finder.id} gathered {item.article} close and whispered, \"I found it first.\""
    )
    if waiter.memes["sadness"] >= THRESHOLD:
        world.say(
            f"{waiter.id} did not fuss, but the room no longer felt as soft. {waiter.pronoun().capitalize()} looked at the blanket and gave a little sigh."
        )


def honesty_turn(world: World, finder: Entity, waiter: Entity, parent: Entity, item: BedtimeItem) -> None:
    finder.memes["truth"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {finder.id} felt a wobble in {finder.pronoun('possessive')} chest. "
        f"{finder.pronoun().capitalize()} looked at {waiter.id}, then at {parent.label_word}, and said, "
        f"\"We both wanted {item.article}, and I grabbed it without thinking.\""
    )
    world.say(
        f"The truthful words made the room feel easier to breathe in."
    )


def kindness_turn(world: World, finder: Entity, waiter: Entity, parent: Entity, item: BedtimeItem) -> None:
    finder.memes["generosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{finder.id} saw the small sigh on {waiter.id}'s face and held still."
    )
    world.say(
        f"\"I do want {item.article},\" {finder.pronoun()} said, \"but I do not want {waiter.id} to feel left out. Can we find a way for both of us?\""
    )


def patience_turn(world: World, finder: Entity, waiter: Entity, parent: Entity) -> None:
    finder.memes["patience"] += 1
    waiter.memes["patience"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} sat on the edge of the bed and said, "
        f"\"No tugging. Let us take three slow bedtime breaths first.\""
    )
    world.say(
        f"So {finder.id} and {waiter.id} breathed in, breathed out, and let their hands grow quiet."
    )


def resolve_together(world: World, finder: Entity, waiter: Entity, parent: Entity, item_ent: Entity, item: BedtimeItem) -> None:
    item_ent.meters["shared"] += 1
    finder.memes["joy"] += 1
    waiter.memes["joy"] += 1
    finder.memes["calm"] += 1
    waiter.memes["calm"] += 1
    waiter.memes["sadness"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} smiled and opened {item.article} right between them."
    )
    world.say(
        f"Soon {finder.id} was tucked against one shoulder and {waiter.id} against the other, following the same {item.use_word} together."
    )
    world.say(
        f"Page by page, {item.ending_image}, and the whole room grew wonderfully quiet and joyous."
    )


def resolve_turns(world: World, finder: Entity, waiter: Entity, parent: Entity, item_ent: Entity, item: BedtimeItem) -> None:
    item_ent.meters["shared"] += 1
    item_ent.meters["passed"] += 1
    finder.memes["joy"] += 1
    waiter.memes["joy"] += 1
    finder.memes["fairness"] += 1
    waiter.memes["fairness"] += 1
    waiter.memes["sadness"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} wound {item.article} and said, "
        f"\"One turn for {finder.id}, and then one just as lovely for {waiter.id}.\""
    )
    world.say(
        f"The first soft tune curled into {finder.id}'s pillow. Then {finder.id} passed {item.article} carefully across the blanket."
    )
    world.say(
        f"The second tune curled into {waiter.id}'s pillow, and {item.ending_image}. By then, the children were smiling instead of hurrying."
    )


def resolve_copy(world: World, finder: Entity, waiter: Entity, parent: Entity, item_ent: Entity, item: BedtimeItem) -> None:
    item_ent.meters["shared"] += 1
    item_ent.meters["copied"] += 1
    twin = world.add(Entity(id="twin_star", kind="thing", type="item", label="second paper star"))
    twin.meters["made"] += 1
    finder.memes["joy"] += 1
    waiter.memes["joy"] += 1
    finder.memes["relief"] += 1
    waiter.memes["relief"] += 1
    waiter.memes["sadness"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} reached into the drawer for golden paper and a small pair of safe scissors."
    )
    world.say(
        f"\"If one {item.label} can brighten the room,\" {parent.pronoun()} said, "
        f"\"two can brighten two hearts.\""
    )
    world.say(
        f"In a minute there was a twin beside the first, and {item.ending_image}. The children looked up and gave the same happy, joyous grin."
    )


def close_lesson(world: World, finder: Entity, waiter: Entity, parent: Entity, value: MoralValue) -> None:
    for child in (finder, waiter):
        child.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} kissed both foreheads and whispered that {value.lesson}."
    )
    world.say(
        f"Under the blankets, {finder.id} and {waiter.id} felt sleepy, peaceful, and close again."
    )


def tell(setting: Setting, value: MoralValue, item: BedtimeItem, resolution: Resolution,
         finder_name: str, finder_gender: str, waiter_name: str, waiter_gender: str,
         parent_type: str, trait: str) -> World:
    world = World(setting)
    finder = world.add(Entity(id=finder_name, kind="character", type=finder_gender, role="finder"))
    waiter = world.add(Entity(id=waiter_name, kind="character", type=waiter_gender, role="waiter"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item_ent = world.add(Entity(id="item", kind="thing", type="item", label=item.label, phrase=item.phrase))
    world.facts["trait"] = trait

    introduce(world, finder, waiter, item, value)
    world.para()
    want_same_thing(world, finder, waiter, item)
    clutch_item(world, finder, waiter, item_ent, item)

    world.para()
    if value.id == "honesty":
        honesty_turn(world, finder, waiter, parent, item)
    elif value.id == "kindness":
        kindness_turn(world, finder, waiter, parent, item)
    else:
        patience_turn(world, finder, waiter, parent)

    world.para()
    if resolution.method == "together":
        resolve_together(world, finder, waiter, parent, item_ent, item)
    elif resolution.method == "turns":
        resolve_turns(world, finder, waiter, parent, item_ent, item)
    else:
        resolve_copy(world, finder, waiter, parent, item_ent, item)
    close_lesson(world, finder, waiter, parent, value)

    world.facts.update(
        setting=setting,
        value=value,
        item_cfg=item,
        resolution=resolution,
        finder=finder,
        waiter=waiter,
        parent=parent,
        item=item_ent,
        pair_noun=_story_pair_noun(finder, waiter),
        left_out=waiter.memes["left_out"] >= THRESHOLD,
        truthful=finder.memes["truth"] >= THRESHOLD,
        generous=finder.memes["generosity"] >= THRESHOLD,
        patient=finder.memes["patience"] >= THRESHOLD or waiter.memes["patience"] >= THRESHOLD,
        shared=item_ent.meters["shared"] >= THRESHOLD,
        predicted=predict_feelings(item),
    )
    return world


KNOWLEDGE = {
    "honesty": [
        (
            "What does honesty mean?",
            "Honesty means telling what is true, even when it feels a little hard. Truth helps other people trust you and understand what really happened.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is noticing how someone else feels and choosing to help or comfort them. Small kind choices can change the whole mood of a room.",
        )
    ],
    "patience": [
        (
            "What is patience?",
            "Patience means waiting calmly instead of grabbing or rushing. Slow waiting can help people make a fair plan.",
        )
    ],
    "book": [
        (
            "Why is it nice to read a bedtime book together?",
            "Reading together lets two people enjoy the same story at the same time. It can make bedtime feel cozy and close.",
        )
    ],
    "music": [
        (
            "Why can taking turns be fair?",
            "Taking turns is fair because each person gets a chance. Waiting for your turn shows respect for the other person too.",
        )
    ],
    "craft": [
        (
            "How can making another one solve a problem?",
            "Sometimes a problem comes from there being only one of something. Making another one can turn a fight into sharing.",
        )
    ],
    "bedtime": [
        (
            "Why do quiet bedtime routines help children?",
            "Quiet routines help bodies slow down and feel safe. When everyone grows calm, it is easier to rest.",
        )
    ],
    "sharing": [
        (
            "What does sharing do?",
            "Sharing makes room for more than one person's happiness. It can turn a lonely feeling into a warm one.",
        )
    ],
}

KNOWLEDGE_ORDER = ["bedtime", "honesty", "kindness", "patience", "book", "music", "craft", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    value = f["value"]
    item = f["item_cfg"]
    setting = f["setting"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "joyous" and teaches {value.label}.',
        f"Tell a gentle story set in {setting.place} where two children both want {item.article}, and a calm grown-up helps them end the night peacefully.",
        f'Write a soft bedtime tale with a clear moral value, a small conflict over {item.phrase}, and an ending image that feels sleepy, safe, and joyous.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    waiter = f["waiter"]
    parent = f["parent"]
    item = f["item_cfg"]
    value = f["value"]
    resolution = f["resolution"]
    predicted = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['pair_noun']}, {finder.id} and {waiter.id}, at bedtime with their {parent.label_word}. They both cared about the same cozy thing, which is what started the trouble.",
        ),
        (
            f"What problem began the story?",
            f"Both children wanted {item.article}, but {finder.id} reached it first and held it close. That left {waiter.id} feeling left out, so the room stopped feeling easy and calm.",
        ),
        (
            f"Why did the room feel sad for a moment?",
            f"It felt sad because only one child had the bedtime treasure while the other had to watch. In the world model, holding it alone raised {waiter.id}'s sadness and gave {finder.id} a little guilt too.",
        ),
    ]
    if f["truthful"]:
        qa.append(
            (
                f"How did {finder.id} show honesty?",
                f"{finder.id} admitted that both children wanted {item.article} and said {finder.pronoun()} had grabbed it too quickly. Telling the truth made it easier for everyone to solve the problem gently.",
            )
        )
    if f["generous"]:
        qa.append(
            (
                f"How did {finder.id} show kindness?",
                f"{finder.id} noticed {waiter.id}'s sigh and cared about that feeling instead of only about winning. Then {finder.pronoun()} asked for a way both children could be included.",
            )
        )
    if f["patient"]:
        qa.append(
            (
                "How did patience help?",
                f"Patience helped because the children stopped tugging and took slow breaths first. Once their bodies were calmer, they could accept a fair plan and enjoy bedtime again.",
            )
        )
    if resolution.method == "together":
        qa.append(
            (
                "How was the problem solved?",
                f"{parent.label_word.capitalize()} opened {item.article} between them so both children could enjoy it together. The shared story changed the feeling from left out to cozy and joyous.",
            )
        )
    elif resolution.method == "turns":
        qa.append(
            (
                "How was the problem solved?",
                f"{parent.label_word.capitalize()} made a turn for each child with {item.article}. Because each child knew a turn was coming, the hurry and sadness melted away.",
            )
        )
    else:
        qa.append(
            (
                "How was the problem solved?",
                f"{parent.label_word.capitalize()} made a second {item.label}, so there was one for each child. The repair worked because the problem had been that there was only one.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is about {value.label}: {value.lesson}. The ending proves it by showing the children close, peaceful, and happy instead of clutching and sighing.",
        )
    )
    if predicted["sadness"] >= THRESHOLD:
        qa.append(
            (
                "What did the first unfair moment cause?",
                f"It caused {waiter.id} to feel sad and left out. It also gave {finder.id} a guilty feeling, which helped make the turning point possible.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bedtime", "sharing", world.facts["value"].id}
    item = world.facts["item_cfg"]
    if "book" in item.tags:
        tags.add("book")
    if "music" in item.tags:
        tags.add("music")
    if "craft" in item.tags:
        tags.add("craft")
    out: list[tuple[str, str]] = []
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, V, I, R) :- setting(S), value(V), item(I), resolution(R),
                     supports(I, M), method(R, M), allows(R, V).

outcome(shared) :- chosen_value(V), chosen_item(I), chosen_resolution(R),
                   valid(dummy, V, I, R).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "dummy"))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for method in sorted(item.methods):
            lines.append(asp.fact("supports", iid, method))
    for rid, resolution in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("method", rid, resolution.method))
        for value_id in sorted(resolution.values):
            lines.append(asp.fact("allows", rid, value_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    atoms = set(asp.atoms(model, "valid"))
    cleaned = {(s, v, i, r) for (s, v, i, r) in atoms if s != "dummy"}
    return sorted(cleaned)


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_value", params.value),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_resolution", params.resolution),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Joyous bedtime storyworld about honesty, kindness, patience, and a fair sleepy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.value and args.item and args.resolution:
        if not valid_combo(args.value, args.item, args.resolution):
            raise StoryError(explain_rejection(args.value, args.item, args.resolution))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.value is None or combo[1] == args.value)
        and (args.item is None or combo[2] == args.item)
        and (args.resolution is None or combo[3] == args.resolution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, value_id, item_id, resolution_id = rng.choice(sorted(combos))
    finder_gender = rng.choice(["girl", "boy"])
    waiter_gender = rng.choice(["girl", "boy"])
    finder_name = _pick_name(rng, finder_gender)
    waiter_name = _pick_name(rng, waiter_gender, avoid=finder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        value=value_id,
        item=item_id,
        resolution=resolution_id,
        finder_name=finder_name,
        finder_gender=finder_gender,
        waiter_name=waiter_name,
        waiter_gender=waiter_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.value not in VALUES:
        raise StoryError(f"(Unknown moral value: {params.value})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"(Unknown resolution: {params.resolution})")
    if not valid_combo(params.value, params.item, params.resolution):
        raise StoryError(explain_rejection(params.value, params.item, params.resolution))

    world = tell(
        setting=SETTINGS[params.setting],
        value=VALUES[params.value],
        item=ITEMS[params.item],
        resolution=RESOLUTIONS[params.resolution],
        finder_name=params.finder_name,
        finder_gender=params.finder_gender,
        waiter_name=params.waiter_name,
        waiter_gender=params.waiter_gender,
        parent_type=params.parent,
        trait=params.trait,
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


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP valid combos match Python ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    outcome_bad = 0
    checked = 0
    for params in CURATED:
        checked += 1
        if asp_outcome(params) != "shared":
            outcome_bad += 1
    if outcome_bad == 0:
        print(f"OK: ASP outcome model returns shared for {checked} curated stories.")
    else:
        rc = 1
        print(f"MISMATCH: {outcome_bad}/{checked} curated outcomes were not shared.")

    smoke_cases: list[StoryParams] = [CURATED[0]]
    parser = build_parser()
    for seed in range(5):
        try:
            ns = parser.parse_args([])
            params = resolve_params(ns, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"SMOKE FAIL: resolve_params failed at seed {seed}.")
            break

    for idx, params in enumerate(smoke_cases):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            sink = io.StringIO()
            with redirect_stdout(sink):
                emit(sample, trace=False, qa=(idx == 0), header="### smoke")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL: generation or emit crashed for case {idx}: {err}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, value, item, resolution) combos:\n")
        for setting_id, value_id, item_id, resolution_id in combos:
            print(f"  {setting_id:12} {value_id:8} {item_id:10} {resolution_id}")
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
            header = (
                f"### {p.finder_name} & {p.waiter_name}: {p.value} with {p.item} "
                f"({p.setting}, {p.resolution})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
