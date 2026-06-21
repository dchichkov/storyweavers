#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/eighty_mystery_teamwork_conflict_misunderstanding_nursery_rhyme.py
===============================================================================================

A small storyworld about a nursery-rhyme mystery: two little friends count to
eighty, think one has taken the missing piece, quarrel over a misunderstanding,
then work together to find it and finish their pretty row.

The world model is intentionally small and concrete:

- a pair of childlike animal friends gathers exactly eighty tiny things
- one thing goes missing because it has slipped into a plausible hiding place
- the friends misunderstand what happened and briefly blame each other
- a grown-up or elder voice nudges them toward teamwork
- the right search helper reveals the truth
- the ending image proves the change: the count reaches eighty again

Run it
------
    python storyworlds/worlds/gpt-5.4/eighty_mystery_teamwork_conflict_misunderstanding_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/eighty_mystery_teamwork_conflict_misunderstanding_nursery_rhyme.py --troupe mice --item buttons --hiding rug_fold --helper broom
    python storyworlds/worlds/gpt-5.4/eighty_mystery_teamwork_conflict_misunderstanding_nursery_rhyme.py --item berries --hiding rain_boot
    python storyworlds/worlds/gpt-5.4/eighty_mystery_teamwork_conflict_misunderstanding_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/eighty_mystery_teamwork_conflict_misunderstanding_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/eighty_mystery_teamwork_conflict_misunderstanding_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "hen", "duck", "goose", "mouse_girl", "rabbit_girl"}
        male = {"boy", "drake", "mouse_boy", "rabbit_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Troupe:
    id: str
    place: str
    pair_kind: str
    child1_name: str
    child1_type: str
    child2_name: str
    child2_type: str
    elder_name: str
    elder_type: str
    elder_label: str
    opening_line: str
    march_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemKind:
    id: str
    many: str
    one: str
    craft: str
    count_line: str
    sound_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    place_line: str
    reveal_line: str
    accepts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    action_line: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_missing_makes_worry(world: World) -> list[str]:
    bag = world.get("bag")
    out: list[str] = []
    if bag.meters["missing"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        for eid in ("child1", "child2"):
            world.get(eid).memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_blame_hurts(world: World) -> list[str]:
    a = world.get("child1")
    b = world.get("child2")
    out: list[str] = []
    if a.memes["blame"] >= THRESHOLD and ("hurt", "child2") not in world.fired:
        world.fired.add(("hurt", "child2"))
        b.memes["hurt"] += 1
        out.append("__hurt__")
    if b.memes["blame"] >= THRESHOLD and ("hurt", "child1") not in world.fired:
        world.fired.add(("hurt", "child1"))
        a.memes["hurt"] += 1
        out.append("__hurt__")
    return out


def _r_teamwork_heals(world: World) -> list[str]:
    a = world.get("child1")
    b = world.get("child2")
    out: list[str] = []
    if a.memes["teamwork"] >= THRESHOLD and b.memes["teamwork"] >= THRESHOLD and ("heal",) not in world.fired:
        world.fired.add(("heal",))
        a.memes["hurt"] = 0.0
        b.memes["hurt"] = 0.0
        a.memes["trust"] += 1
        b.memes["trust"] += 1
        out.append("__heal__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_makes_worry", apply=_r_missing_makes_worry),
    Rule(name="blame_hurts", apply=_r_blame_hurts),
    Rule(name="teamwork_heals", apply=_r_teamwork_heals),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


TROUPES = {
    "mice": Troupe(
        id="mice",
        place="a warm pantry shelf",
        pair_kind="two little mice",
        child1_name="Pip",
        child1_type="mouse_boy",
        child2_name="Poppy",
        child2_type="mouse_girl",
        elder_name="Mother Mouse",
        elder_type="hen",
        elder_label="mother mouse",
        opening_line="In a pantry snug and spry, two little mice were skipping by.",
        march_line="They hummed a tiny counting tune and hoped their row would gleam by noon.",
        ending_line="So Pip and Poppy, nose to nose, set eighty bright things in a row.",
        tags={"mice", "counting"},
    ),
    "ducklings": Troupe(
        id="ducklings",
        place="the rushes by the pond",
        pair_kind="two ducklings",
        child1_name="Dot",
        child1_type="duck",
        child2_name="Dab",
        child2_type="drake",
        elder_name="Mother Duck",
        elder_type="duck",
        elder_label="mother duck",
        opening_line="By the pond where reeds leaned low, two ducklings made a counting show.",
        march_line="They waddled while the water gleamed and counted all their shining dreams.",
        ending_line="So Dot and Dab, with settled hearts, laid eighty neat and twinkling parts.",
        tags={"duck", "pond"},
    ),
    "rabbits": Troupe(
        id="rabbits",
        place="a mossy garden wall",
        pair_kind="two small rabbits",
        child1_name="Nip",
        child1_type="rabbit_boy",
        child2_name="Nell",
        child2_type="rabbit_girl",
        elder_name="Aunt Rabbit",
        elder_type="rabbit_girl",
        elder_label="aunt rabbit",
        opening_line="Beside the wall so green and sweet, two small rabbits pattered feet.",
        march_line="They sang of rows and little things and all the joy that counting brings.",
        ending_line="So Nip and Nell, with ears held high, made eighty glimmer in a line.",
        tags={"rabbit", "garden"},
    ),
}

ITEMS = {
    "buttons": ItemKind(
        id="buttons",
        many="buttons",
        one="button",
        craft="a counting chain",
        count_line="Eighty buttons, bright and round, clicked like raindrops on the ground.",
        sound_line="Each button made a gentle tick as nimble paws and feathers picked.",
        tags={"button", "counting"},
    ),
    "berries": ItemKind(
        id="berries",
        many="berries",
        one="berry",
        craft="a berry garland",
        count_line="Eighty berries, ruby red, bobbed like beads on green thread.",
        sound_line="Their little pile looked soft and sweet, a nursery treasure nice to meet.",
        tags={"berry", "garden"},
    ),
    "bells": ItemKind(
        id="bells",
        many="bells",
        one="bell",
        craft="a jingling row",
        count_line="Eighty bells, so small and gold, waited to be looped and rolled.",
        sound_line="Each tiny bell gave one faint ring, as if it liked the song they sing.",
        tags={"bell", "sound"},
    ),
}

HIDING_PLACES = {
    "rug_fold": HidingPlace(
        id="rug_fold",
        label="the fold of the rug",
        place_line="One slipped and skittered with a hop, then tucked itself where rugs may flop.",
        reveal_line="There, in the fold of the rug, the missing piece had been quietly hiding all along.",
        accepts={"buttons", "bells"},
        tags={"rug"},
    ),
    "basket_straw": HidingPlace(
        id="basket_straw",
        label="the straw in the basket",
        place_line="One rolled beside the basket brim and nestled down where straw was dim.",
        reveal_line="There, in the basket straw, the missing piece was resting where small hands had not looked yet.",
        accepts={"buttons", "berries"},
        tags={"basket"},
    ),
    "rain_boot": HidingPlace(
        id="rain_boot",
        label="the toe of a rain boot",
        place_line="One bounced beside a boot in play and hid inside the toe away.",
        reveal_line="There, in the rain boot toe, the missing piece had been waiting, not stolen at all.",
        accepts={"buttons", "bells"},
        tags={"boot"},
    ),
}

HELPERS = {
    "broom": Helper(
        id="broom",
        label="a little broom",
        action_line="Together they swept softly-soft, and out the missing piece came off.",
        fixes={"rug_fold"},
        tags={"broom"},
    ),
    "lift_basket": Helper(
        id="lift_basket",
        label="careful paws to lift the basket",
        action_line="Together they lifted the basket high and peeped where straw lay warm and dry.",
        fixes={"basket_straw"},
        tags={"basket"},
    ),
    "tip_boot": Helper(
        id="tip_boot",
        label="a careful tip of the rain boot",
        action_line="Together they tipped the boot just so, and heard a tiny clink below.",
        fixes={"rain_boot"},
        tags={"boot"},
    ),
}


def missing_can_hide(item_id: str, hiding_id: str) -> bool:
    return item_id in HIDING_PLACES[hiding_id].accepts


def helper_can_find(hiding_id: str, helper_id: str) -> bool:
    return hiding_id in HELPERS[helper_id].fixes


def valid_combo(item_id: str, hiding_id: str, helper_id: str) -> bool:
    return missing_can_hide(item_id, hiding_id) and helper_can_find(hiding_id, helper_id)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for troupe_id in sorted(TROUPES):
        for item_id in sorted(ITEMS):
            for hiding_id in sorted(HIDING_PLACES):
                for helper_id in sorted(HELPERS):
                    if valid_combo(item_id, hiding_id, helper_id):
                        out.append((troupe_id, item_id, hiding_id, helper_id))
    return out


@dataclass
class StoryParams:
    troupe: str
    item: str
    hiding: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(troupe="mice", item="buttons", hiding="rug_fold", helper="broom"),
    StoryParams(troupe="ducklings", item="bells", hiding="rain_boot", helper="tip_boot"),
    StoryParams(troupe="rabbits", item="berries", hiding="basket_straw", helper="lift_basket"),
    StoryParams(troupe="mice", item="bells", hiding="rug_fold", helper="broom"),
    StoryParams(troupe="ducklings", item="buttons", hiding="basket_straw", helper="lift_basket"),
]


def explain_rejection(item_id: str, hiding_id: str, helper_id: Optional[str] = None) -> str:
    item = ITEMS[item_id]
    hiding = HIDING_PLACES[hiding_id]
    if not missing_can_hide(item_id, hiding_id):
        return (
            f"(No story: a missing {item.one} would not plausibly vanish into {hiding.label}. "
            f"Pick a hiding place that suits a little {item.one}.)"
        )
    if helper_id is not None and not helper_can_find(hiding_id, helper_id):
        helper = HELPERS[helper_id]
        return (
            f"(No story: {helper.label} would not sensibly find something hidden in {hiding.label}. "
            f"Choose the helper that matches the hiding place.)"
        )
    return "(No story: this combination does not make a clear little mystery.)"


def setup_world(troupe: Troupe, item: ItemKind, hiding: HidingPlace, helper: Helper) -> World:
    world = World()
    child1 = world.add(Entity(
        id="child1",
        kind="character",
        type=troupe.child1_type,
        label=troupe.child1_name,
        role="child1",
    ))
    child2 = world.add(Entity(
        id="child2",
        kind="character",
        type=troupe.child2_type,
        label=troupe.child2_name,
        role="child2",
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=troupe.elder_type,
        label=troupe.elder_label,
        phrase=troupe.elder_name,
        role="elder",
    ))
    bag = world.add(Entity(
        id="bag",
        kind="thing",
        type="pile",
        label=item.many,
        phrase=item.craft,
        attrs={"full_count": 80, "seen_count": 80},
    ))
    hidden = world.add(Entity(
        id="hidden",
        kind="thing",
        type=item.one,
        label=item.one,
        phrase=item.one,
        attrs={"hiding": hiding.id},
    ))
    child1.memes["trust"] = 2
    child2.memes["trust"] = 2
    bag.meters["count"] = 80
    world.facts.update(
        troupe=troupe,
        item=item,
        hiding=hiding,
        helper=helper,
        child1=child1,
        child2=child2,
        elder=elder,
        bag=bag,
        hidden=hidden,
    )
    return world


def opening(world: World) -> None:
    troupe = world.facts["troupe"]
    item = world.facts["item"]
    a = world.facts["child1"]
    b = world.facts["child2"]
    world.say(troupe.opening_line)
    world.say(f"In {troupe.place}, {a.label} and {b.label} meant to make {item.craft}.")
    world.say(item.count_line)
    world.say(item.sound_line)
    world.say(troupe.march_line)


def lose_one(world: World) -> None:
    item = world.facts["item"]
    hiding = world.facts["hiding"]
    bag = world.facts["bag"]
    bag.meters["count"] = 79
    bag.meters["missing"] = 1
    bag.attrs["seen_count"] = 79
    propagate(world)
    world.para()
    world.say(f"But hush! A nursery mystery came to life before their eyes.")
    world.say(hiding.place_line)
    world.say(f'"Seventy-nine!" cried one small voice. "But we had eighty {item.many} to choice and count!"')


def misunderstand(world: World) -> None:
    a = world.facts["child1"]
    b = world.facts["child2"]
    item = world.facts["item"]
    a.memes["blame"] += 1
    b.memes["defend"] += 1
    propagate(world)
    world.say(f'{a.label} frowned and stamped one foot. "Did you tuck the {item.one} away?"')
    world.say(f'{b.label} blinked hard. "No, not I. You think I took it, and that is not kind."')
    world.say("The room felt tight with cross little looks, for worry can make the wrong story in our minds.")


def elder_nudges(world: World) -> None:
    elder = world.facts["elder"]
    world.para()
    world.say(
        f"{elder.phrase} heard the fuss and came with a soft, unhurried step."
    )
    world.say(
        f'"If you chase blame, the mystery grows," said {elder.label}. '
        f'"If you search together, the truth may show."'
    )


def search_together(world: World) -> None:
    a = world.facts["child1"]
    b = world.facts["child2"]
    helper = world.facts["helper"]
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    a.memes["blame"] = 0.0
    b.memes["blame"] = 0.0
    propagate(world)
    world.say(f"So {a.label} took one side, and {b.label} took the other.")
    world.say(f"They used {helper.label} and searched in a patient, sing-song way.")
    world.say(helper.action_line)


def reveal(world: World) -> None:
    bag = world.facts["bag"]
    hiding = world.facts["hiding"]
    item = world.facts["item"]
    a = world.facts["child1"]
    b = world.facts["child2"]
    bag.meters["count"] = 80
    bag.meters["missing"] = 0
    bag.meters["found"] = 1
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(hiding.reveal_line)
    world.say(
        f"It had not been stolen. It had only slipped away, and the misunderstanding melted at once."
    )
    world.say(
        f'"Oh!" said {a.label}. "I was wrong to blame." "{b.label}," whispered the other, '
        f'"I am sorry too for snapping back."'
    )
    world.say(
        f"They smiled, set the little {item.one} back, and counted once more: eighty."
    )


def ending(world: World) -> None:
    troupe = world.facts["troupe"]
    elder = world.facts["elder"]
    item = world.facts["item"]
    world.para()
    world.say(
        f'{elder.phrase} nodded. "A mystery shrinks when kind hearts look together."'
    )
    world.say(troupe.ending_line)
    world.say(
        f"And from that day, when a count went wrong, they searched with care before they sang a blameful song."
    )
    world.say(
        f"So ended the mystery of the eighty {item.many}: not with a quarrel, but with teamwork."
    )


def tell(troupe: Troupe, item: ItemKind, hiding: HidingPlace, helper: Helper) -> World:
    world = setup_world(troupe, item, hiding, helper)
    opening(world)
    lose_one(world)
    misunderstand(world)
    elder_nudges(world)
    search_together(world)
    reveal(world)
    ending(world)
    world.facts.update(
        misunderstanding=True,
        teamwork=True,
        resolved=True,
        final_count=int(world.get("bag").meters["count"]),
    )
    return world


KNOWLEDGE = {
    "counting": [
        (
            "What does eighty mean?",
            "Eighty means eight groups of ten. It is a big counting number that comes after seventy-nine and before eighty-one."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet. You look for clues, and then the truth becomes clear."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people helping one another on the same job. Working together can solve a problem faster and more kindly."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks the wrong thing about what happened. Talking calmly and checking the facts can fix it."
        )
    ],
    "buttons": [
        (
            "Why can a button be easy to lose?",
            "A small button can roll or slip into cracks and folds. Tiny things are easy to miss unless you search carefully."
        )
    ],
    "berries": [
        (
            "Why should berries be handled gently?",
            "Berries are soft and can squish. Gentle hands help keep them whole."
        )
    ],
    "bells": [
        (
            "How can a tiny bell help you find it?",
            "A tiny bell can make a little ring when it moves. That sound can help someone notice where it has gone."
        )
    ],
    "broom": [
        (
            "What does a broom do?",
            "A broom brushes dust and little things out into the open. It helps you reach what is hiding under an edge."
        )
    ],
    "basket": [
        (
            "Why should you look under and inside a basket carefully?",
            "A basket can hide small things under its rim or in its straw. Lifting it slowly helps you see what was tucked away."
        )
    ],
    "boot": [
        (
            "Why can a boot hide a small object?",
            "The toe of a boot is hollow, so a little thing can bounce or roll inside. Tipping the boot can bring it out again."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "counting",
    "mystery",
    "teamwork",
    "misunderstanding",
    "buttons",
    "berries",
    "bells",
    "broom",
    "basket",
    "boot",
]


def generation_prompts(world: World) -> list[str]:
    troupe = world.facts["troupe"]
    item = world.facts["item"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "eighty" and "mystery".',
        f"Tell a bouncing little rhyme-story about {troupe.pair_kind} who count eighty {item.many}, have a misunderstanding, and solve the mystery through teamwork.",
        f"Write a gentle conflict story in nursery-rhyme style where friends almost blame each other for a missing {item.one}, then find the truth together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    troupe = world.facts["troupe"]
    item = world.facts["item"]
    hiding = world.facts["hiding"]
    helper = world.facts["helper"]
    a = world.facts["child1"]
    b = world.facts["child2"]
    elder = world.facts["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {troupe.pair_kind}, {a.label} and {b.label}. They were trying to arrange eighty {item.many} together."
        ),
        (
            f"What was the mystery?",
            f"One {item.one} seemed to be gone, so the count dropped from eighty to seventy-nine. That missing piece made the little mystery begin."
        ),
        (
            f"Why did {a.label} and {b.label} start to quarrel?",
            f"They worried when the count was wrong and one of them guessed the other had tucked the missing {item.one} away. The quarrel came from a misunderstanding, not from anyone truly stealing it."
        ),
        (
            f"How did {elder.phrase} help?",
            f"{elder.phrase} told them to stop chasing blame and search together instead. That advice turned the conflict into teamwork."
        ),
        (
            f"How did they solve the mystery?",
            f"They worked together and used {helper.label}. Because they searched the right place, they found the missing {item.one} in {hiding.label}."
        ),
        (
            "How did the story end?",
            f"It ended with the count back at eighty and both friends feeling relieved. The ending proves they trusted each other again and finished the job together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item = world.facts["item"]
    helper = world.facts["helper"]
    hiding = world.facts["hiding"]
    tags = {"counting", "mystery", "teamwork", "misunderstanding", item.id}
    if helper.id == "broom":
        tags.add("broom")
    if hiding.id == "basket_straw" or helper.id == "lift_basket":
        tags.add("basket")
    if hiding.id == "rain_boot" or helper.id == "tip_boot":
        tags.add("boot")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_hide(I, H) :- item(I), hiding(H), accepts(H, I).
can_find(H, Hp) :- hiding(H), helper(Hp), fixes(Hp, H).
valid(T, I, H, Hp) :- troupe(T), can_hide(I, H), can_find(H, Hp).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for troupe_id in sorted(TROUPES):
        lines.append(asp.fact("troupe", troupe_id))
    for item_id in sorted(ITEMS):
        lines.append(asp.fact("item", item_id))
    for hiding_id, hiding in sorted(HIDING_PLACES.items()):
        lines.append(asp.fact("hiding", hiding_id))
        for item_id in sorted(hiding.accepts):
            lines.append(asp.fact("accepts", hiding_id, item_id))
    for helper_id, helper in sorted(HELPERS.items()):
        lines.append(asp.fact("helper", helper_id))
        for hiding_id in sorted(helper.fixes):
            lines.append(asp.fact("fixes", helper_id, hiding_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "eighty" not in sample.story.lower() or "mystery" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missed required words or came out empty.)")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(7))
        sample = generate(params)
        if not sample.story:
            raise StoryError("(Random smoke test failed: empty story.)")
        print("OK: random generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"RANDOM GENERATION FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: eighty little things, a mystery, a misunderstanding, and teamwork."
    )
    ap.add_argument("--troupe", choices=sorted(TROUPES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hiding", choices=sorted(HIDING_PLACES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.hiding and not missing_can_hide(args.item, args.hiding):
        raise StoryError(explain_rejection(args.item, args.hiding, args.helper))
    if args.hiding and args.helper and not helper_can_find(args.hiding, args.helper):
        item_id = args.item or sorted(ITEMS)[0]
        raise StoryError(explain_rejection(item_id, args.hiding, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.troupe is None or combo[0] == args.troupe)
        and (args.item is None or combo[1] == args.item)
        and (args.hiding is None or combo[2] == args.hiding)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    troupe_id, item_id, hiding_id, helper_id = rng.choice(sorted(combos))
    return StoryParams(
        troupe=troupe_id,
        item=item_id,
        hiding=hiding_id,
        helper=helper_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.troupe not in TROUPES:
        raise StoryError(f"(Unknown troupe: {params.troupe})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not valid_combo(params.item, params.hiding, params.helper):
        raise StoryError(explain_rejection(params.item, params.hiding, params.helper))

    world = tell(
        troupe=TROUPES[params.troupe],
        item=ITEMS[params.item],
        hiding=HIDING_PLACES[params.hiding],
        helper=HELPERS[params.helper],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (troupe, item, hiding, helper) combos:\n")
        for troupe_id, item_id, hiding_id, helper_id in combos:
            print(f"  {troupe_id:10} {item_id:8} {hiding_id:12} {helper_id}")
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
            header = f"### {p.troupe}: {p.item} / {p.hiding} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
