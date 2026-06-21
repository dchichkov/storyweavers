#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tattle_toss_reconciliation_folk_tale.py
==================================================================

A small folk-tale storyworld about two village children, a moment of tattling,
an angry toss, and a true reconciliation made visible through shared repair.

The world model keeps one simple common-sense constraint at its center:
not every tossed treasure can be mended in every way. The item's material,
the place it lands, and the chosen repair must fit together. Stories only
generate when the recovery is plausible.

Run it
------
    python storyworlds/worlds/gpt-5.4/tattle_toss_reconciliation_folk_tale.py
    python storyworlds/worlds/gpt-5.4/tattle_toss_reconciliation_folk_tale.py --item flower_crown --landing thorn_bush
    python storyworlds/worlds/gpt-5.4/tattle_toss_reconciliation_folk_tale.py --item reed_flute --landing dusty_path --repair stitch
    python storyworlds/worlds/gpt-5.4/tattle_toss_reconciliation_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/tattle_toss_reconciliation_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tattle_toss_reconciliation_folk_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    scene: str
    elder_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    material: str
    festival_use: str
    care_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Landing:
    id: str
    label: str
    phrase: str
    effect: str
    mark_word: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    materials: set[str]
    fixes: set[str]
    power: int
    text: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


PLACES = {
    "village_green": Place(
        id="village_green",
        scene="a green ringed by willow trees and small clay houses",
        elder_spot="the old bench beneath the willow",
        ending_image="the willow leaves whispering above them",
        tags={"village", "willow"},
    ),
    "orchard_lane": Place(
        id="orchard_lane",
        scene="a lane beside the orchard where bees hummed in the clover",
        elder_spot="the flat stone by the orchard gate",
        ending_image="pear blossoms drifting like white snow",
        tags={"orchard", "blossom"},
    ),
    "mill_bridge": Place(
        id="mill_bridge",
        scene="the bridge near the village mill where water clicked on the wheel",
        elder_spot="the sun-warmed step near the mill door",
        ending_image="the turning mill wheel shining in the late light",
        tags={"bridge", "mill"},
    ),
}

ITEMS = {
    "flower_crown": ItemCfg(
        id="flower_crown",
        label="flower crown",
        phrase="a flower crown woven from marigolds and clover",
        material="plant",
        festival_use="to wear at the evening dance",
        care_line="Flowers bend easily, so gentle hands matter.",
        ending_line="They set the crown together on the child's head, and it sat bright and round again.",
        tags={"flowers", "crown"},
    ),
    "reed_flute": ItemCfg(
        id="reed_flute",
        label="reed flute",
        phrase="a little reed flute tied with red thread",
        material="reed",
        festival_use="to play for the lantern walk",
        care_line="Reeds must be kept straight and dry if they are to sing.",
        ending_line="They lifted the flute together, and its next note came out clear and sweet.",
        tags={"flute", "music"},
    ),
    "cloth_banner": ItemCfg(
        id="cloth_banner",
        label="cloth banner",
        phrase="a cloth banner painted with a golden sun",
        material="cloth",
        festival_use="to carry at the front of the feast parade",
        care_line="Cloth can be cleaned and mended when patience sits beside skill.",
        ending_line="They held the banner between them, and the painted sun shone over both their hands.",
        tags={"banner", "cloth"},
    ),
}

LANDINGS = {
    "thorn_bush": Landing(
        id="thorn_bush",
        label="thorn bush",
        phrase="into a thorn bush by the path",
        effect="torn",
        mark_word="thorn-caught",
        severity=2,
        tags={"thorns"},
    ),
    "shallow_stream": Landing(
        id="shallow_stream",
        label="shallow stream",
        phrase="into the shallow stream",
        effect="wet",
        mark_word="water-soaked",
        severity=2,
        tags={"stream", "water"},
    ),
    "dusty_path": Landing(
        id="dusty_path",
        label="dusty path",
        phrase="onto the dusty path",
        effect="dusty",
        mark_word="dust-gray",
        severity=1,
        tags={"dust"},
    ),
}

REPAIRS = {
    "reweave": Repair(
        id="reweave",
        label="reweave",
        materials={"plant", "cloth"},
        fixes={"torn"},
        power=2,
        text="sat knee to knee and reworked the loose parts with patient fingers",
        lesson="Things pulled apart can be woven whole again when two people choose gentleness.",
        tags={"mend", "weave"},
    ),
    "rinse_and_dry": Repair(
        id="rinse_and_dry",
        label="rinse and dry",
        materials={"plant", "cloth", "reed"},
        fixes={"wet", "dusty"},
        power=2,
        text="rinsed the piece clean, laid it in the sun, and waited together until it was ready again",
        lesson="Some harm is healed not by hurry, but by cleaning, waiting, and staying near.",
        tags={"wash", "sun"},
    ),
    "bind_and_straighten": Repair(
        id="bind_and_straighten",
        label="bind and straighten",
        materials={"reed"},
        fixes={"torn", "wet"},
        power=2,
        text="pressed the reeds straight, bound them neatly with fresh thread, and tested them with calm breaths",
        lesson="A bent song can return when careful hands stop quarreling and work as one.",
        tags={"thread", "repair"},
    ),
    "stitch": Repair(
        id="stitch",
        label="stitch",
        materials={"cloth"},
        fixes={"torn"},
        power=2,
        text="smoothed the cloth across their knees and stitched the hurt place with small even loops",
        lesson="A torn edge need not stay torn when people admit hurt and mend it together.",
        tags={"needle", "repair"},
    ),
}

GIRL_NAMES = ["Mira", "Tala", "Nina", "Sura", "Lina", "Anya"]
BOY_NAMES = ["Ivo", "Pavel", "Milo", "Tarin", "Nico", "Oren"]
TRAITS = ["quick", "proud", "eager", "careful", "bright", "restless"]


def works_for(item: ItemCfg, landing: Landing, repair: Repair) -> bool:
    return (
        item.material in repair.materials
        and landing.effect in repair.fixes
        and repair.power >= landing.severity
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for item_id, item in ITEMS.items():
            for landing_id, landing in LANDINGS.items():
                for repair_id, repair in REPAIRS.items():
                    if works_for(item, landing, repair):
                        combos.append((place_id, item_id, landing_id, repair_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    landing: str
    repair: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    elder: str
    elder_type: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="village_green",
        item="flower_crown",
        landing="thorn_bush",
        repair="reweave",
        child1="Mira",
        child1_gender="girl",
        child2="Ivo",
        child2_gender="boy",
        elder="Grandmother Vesna",
        elder_type="grandmother",
        trait1="proud",
        trait2="careful",
    ),
    StoryParams(
        place="orchard_lane",
        item="reed_flute",
        landing="shallow_stream",
        repair="bind_and_straighten",
        child1="Tala",
        child1_gender="girl",
        child2="Milo",
        child2_gender="boy",
        elder="Grandfather Petar",
        elder_type="grandfather",
        trait1="quick",
        trait2="bright",
    ),
    StoryParams(
        place="mill_bridge",
        item="cloth_banner",
        landing="dusty_path",
        repair="rinse_and_dry",
        child1="Nina",
        child1_gender="girl",
        child2="Oren",
        child2_gender="boy",
        elder="Grandmother Stana",
        elder_type="grandmother",
        trait1="eager",
        trait2="restless",
    ),
    StoryParams(
        place="orchard_lane",
        item="cloth_banner",
        landing="thorn_bush",
        repair="stitch",
        child1="Pavel",
        child1_gender="boy",
        child2="Lina",
        child2_gender="girl",
        elder="Grandfather Ilian",
        elder_type="grandfather",
        trait1="proud",
        trait2="careful",
    ),
]


def explain_rejection(item: ItemCfg, landing: Landing, repair: Repair) -> str:
    if item.material not in repair.materials:
        return (
            f"(No story: {repair.label} does not fit a {item.label}. "
            f"The item's material is {item.material}, so choose a repair made for that kind of thing.)"
        )
    if landing.effect not in repair.fixes:
        return (
            f"(No story: {repair.label} does not fix something made {landing.mark_word} by the {landing.label}. "
            f"Choose a repair that can handle {landing.effect} damage.)"
        )
    if repair.power < landing.severity:
        return (
            f"(No story: the {landing.label} harms the {item.label} too much for {repair.label} to mend.)"
        )
    return "(No story: this item, landing, and repair do not make a sensible folktale problem and fix.)"


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
        lines.append(f"  {ent.id:14} ({ent.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(
    place: Place,
    item_cfg: ItemCfg,
    landing_cfg: Landing,
    repair_cfg: Repair,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    elder_name: str,
    elder_type: str,
    trait1: str,
    trait2: str,
) -> World:
    world = World(place)
    child1 = world.add(
        Entity(
            id=child1_name,
            kind="character",
            type=child1_gender,
            role="maker",
            attrs={"trait": trait1},
        )
    )
    child2 = world.add(
        Entity(
            id=child2_name,
            kind="character",
            type=child2_gender,
            role="maker",
            attrs={"trait": trait2},
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    item = world.add(
        Entity(
            id="item",
            type=item_cfg.material,
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            owner="shared",
            attrs={"festival_use": item_cfg.festival_use},
            tags=set(item_cfg.tags),
        )
    )

    child1.memes["joy"] += 1
    child2.memes["joy"] += 1
    child1.memes["pride"] += 1

    world.say(
        f"In the old days, when even small villages kept their own songs, {place.scene} was full of festival talk."
    )
    world.say(
        f"There {child1.id} and {child2.id} worked side by side on {item_cfg.phrase} {item_cfg.festival_use}."
    )
    world.say(item_cfg.care_line)

    world.para()
    world.say(
        f"When the work was nearly done, {child1.id} reached first for the prettiest part, and {child2.id} felt a hard little knot of hurt."
    )
    child2.memes["hurt"] += 1
    world.say(
        f"{child2.id} ran to {elder.id} at {place.elder_spot} and said, \"{elder.label_word.capitalize()}, I do not mean to tattle, but {child1.id} is taking the best for {child1.pronoun('object')}self.\""
    )
    child2.memes["guilt"] += 1
    world.say(
        f"{elder.id} looked up, hearing both the complaint and the sadness tucked inside it."
    )

    world.para()
    world.say(
        f"When {child1.id} learned of the tattle, shame and anger rose together, quick as a spark in dry straw."
    )
    child1.memes["anger"] += 1
    child1.memes["shame"] += 1
    world.say(
        f'"If the work is to be measured like that," said {child1.id}, "then let the wind judge it."'
    )
    world.say(
        f"In a hot foolish moment, {child1.id} made a sharp toss and flung the {item_cfg.label} {landing_cfg.phrase}."
    )
    item.meters[landing_cfg.effect] += 1
    item.meters["damaged"] += 1
    child2.memes["fear"] += 1
    child1.memes["regret"] += 1
    world.say(
        f"It landed {landing_cfg.mark_word}, and both children fell still at once."
    )

    world.para()
    world.say(
        f"{elder.id} walked to them slowly and said, \"A quick tongue can sting, and a quick hand can wound. Yet neither must have the last word.\""
    )
    world.say(
        f"{elder.id} lifted the {item_cfg.label} carefully and set it between the children."
    )
    world.say(
        f"Then {elder.pronoun()} said, \"First speak true. Then mend true.\""
    )
    world.say(
        f"{child2.id} bowed {child2.pronoun('possessive')} head. \"I did tattle instead of speaking kindly to you.\""
    )
    child2.memes["guilt"] += 1
    child2.memes["trust"] -= 1
    world.say(
        f"{child1.id} answered, \"And I let anger lead my hand when I made that toss. I hurt our work and your heart together.\""
    )
    child1.memes["anger"] = 0.0
    child1.memes["regret"] += 1
    child1.memes["trust"] -= 1

    world.para()
    world.say(
        f"So the two children {repair_cfg.text}."
    )
    item.meters[landing_cfg.effect] = 0.0
    item.meters["damaged"] = 0.0
    item.meters["mended"] += 1
    child1.memes["peace"] += 1
    child2.memes["peace"] += 1
    child1.memes["trust"] += 2
    child2.memes["trust"] += 2
    world.say(repair_cfg.lesson)
    world.say(
        f"As they worked, the hard knot inside the quarrel loosened and slipped away."
    )

    world.para()
    world.say(item_cfg.ending_line)
    world.say(
        f"That evening they went to the feast side by side, and no one could tell which hand had once accused and which had once thrown."
    )
    world.say(
        f"People remembered only that the children had learned to speak before hurt grew sharp, and to mend before evening came, with {place.ending_image}."
    )

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        landing_cfg=landing_cfg,
        repair_cfg=repair_cfg,
        child1=child1,
        child2=child2,
        elder=elder,
        item=item,
        reconciled=child1.memes["peace"] >= THRESHOLD and child2.memes["peace"] >= THRESHOLD,
        tattled=child2.memes["guilt"] >= THRESHOLD,
        tossed=True,
        damage=landing_cfg.effect,
    )
    return world


KNOWLEDGE = {
    "tattle": [
        (
            "What does it mean to tattle?",
            "To tattle means to run and report someone's small wrong in a blaming way instead of first trying to speak kindly to them. It can make hurt feelings bigger."
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation means people who were hurt or angry make peace again. They tell the truth, ask forgiveness, and choose to be close in a kinder way."
        )
    ],
    "flowers": [
        (
            "Why does a flower crown need gentle hands?",
            "Flowers are soft and bend easily. If you pull them too hard, the woven parts come loose."
        )
    ],
    "flute": [
        (
            "Why must a reed flute be kept straight and dry?",
            "A reed flute sings through small hollow parts. If the reeds bend or stay wet, the sound can turn weak or crooked."
        )
    ],
    "cloth": [
        (
            "Why can cloth be mended with stitches?",
            "Cloth is made of threads crossing together. A stitch joins loose parts so the fabric can hold firm again."
        )
    ],
    "thorns": [
        (
            "Why do thorns damage soft things?",
            "Thorns are sharp points on a plant. They can catch and tear things that brush against them."
        )
    ],
    "stream": [
        (
            "What happens when something falls in a shallow stream?",
            "It gets wet, and the water may carry away dirt while also soaking the thing. Some objects must then be dried carefully."
        )
    ],
    "dust": [
        (
            "Why does dust cling to things on a path?",
            "Dust is made of tiny dry bits of earth. It sticks to damp or rough surfaces and makes them look gray and dull."
        )
    ],
    "mend": [
        (
            "Why is mending together a good sign after a quarrel?",
            "Working together asks both people to slow down and care for the same thing. The shared work can help trust return."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "tattle",
    "reconciliation",
    "flowers",
    "flute",
    "cloth",
    "thorns",
    "stream",
    "dust",
    "mend",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c1 = f["child1"]
    c2 = f["child2"]
    item_cfg = f["item_cfg"]
    landing_cfg = f["landing_cfg"]
    return [
        f'Write a short folk tale for a young child that includes the words "tattle" and "toss" and ends in reconciliation.',
        f"Tell a village tale where {c2.id} tattles, {c1.id} angrily tosses a shared {item_cfg.label} {landing_cfg.phrase}, and an elder guides both children back to peace.",
        f"Write a gentle old-fashioned story about hurt feelings, truthful apologies, and two children mending the same thing together before a feast.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1 = f["child1"]
    c2 = f["child2"]
    elder = f["elder"]
    item_cfg = f["item_cfg"]
    landing_cfg = f["landing_cfg"]
    repair_cfg = f["repair_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {c1.id} and {c2.id}, two children making a shared {item_cfg.label}, and {elder.id}, the elder who helped them make peace."
        ),
        (
            f"Why did {c2.id} go to {elder.id}?",
            f"{c2.id} felt hurt when {c1.id} reached for the prettiest part of the work. Instead of speaking kindly to {c1.pronoun('object')} first, {c2.pronoun()} went to {elder.id} to tattle."
        ),
        (
            f"Why did {c1.id} make the toss?",
            f"{c1.id} felt both shame and anger after hearing about the tattle. In that hot moment, {c1.pronoun()} threw the {item_cfg.label} and hurt the shared work."
        ),
        (
            f"What happened to the {item_cfg.label} after it landed in the {landing_cfg.label}?",
            f"It became {landing_cfg.mark_word}. The damage mattered because that was the very thing the children had hoped to carry or use at the feast."
        ),
        (
            "How did the elder help them reconcile?",
            f"{elder.id} told them to speak true and mend true, so each child admitted a wrong. Then the children {repair_cfg.text}, and the shared repair helped peace return."
        ),
        (
            "How did the story end?",
            f"It ended with reconciliation: the children went to the feast side by side after mending the {item_cfg.label}. The ending image shows that their friendship, like the object, had been repaired."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tattle", "reconciliation", "mend"}
    item_cfg = world.facts["item_cfg"]
    landing_cfg = world.facts["landing_cfg"]
    tags |= set(item_cfg.tags)
    tags |= set(landing_cfg.tags)
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


ASP_RULES = r"""
works_for(I, L, R) :-
    item(I), landing(L), repair(R),
    item_material(I, M), repair_material(R, M),
    landing_effect(L, E), repair_fixes(R, E),
    landing_severity(L, S), repair_power(R, P), P >= S.

valid(Pc, I, L, R) :- place(Pc), works_for(I, L, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_material", item_id, item.material))
    for landing_id, landing in LANDINGS.items():
        lines.append(asp.fact("landing", landing_id))
        lines.append(asp.fact("landing_effect", landing_id, landing.effect))
        lines.append(asp.fact("landing_severity", landing_id, landing.severity))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
        for mat in sorted(repair.materials):
            lines.append(asp.fact("repair_material", repair_id, mat))
        for fx in sorted(repair.fixes):
            lines.append(asp.fact("repair_fixes", repair_id, fx))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "tattle" not in sample.story or "toss" not in sample.story:
            raise StoryError("Smoke test failed: generated story is missing required seed words or empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a tattle, a toss, and reconciliation through shared mending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--landing", choices=LANDINGS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def _pick_elder(rng: random.Random, elder_type: str) -> str:
    if elder_type == "grandmother":
        return rng.choice(["Grandmother Vesna", "Grandmother Stana", "Grandmother Darya"])
    return rng.choice(["Grandfather Petar", "Grandfather Ilian", "Grandfather Marko"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.landing and args.repair:
        item = ITEMS[args.item]
        landing = LANDINGS[args.landing]
        repair = REPAIRS[args.repair]
        if not works_for(item, landing, repair):
            raise StoryError(explain_rejection(item, landing, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.landing is None or combo[2] == args.landing)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, landing_id, repair_id = rng.choice(sorted(combos))
    child1, gender1 = _pick_child(rng)
    child2, gender2 = _pick_child(rng, avoid=child1)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    elder = _pick_elder(rng, elder_type)
    return StoryParams(
        place=place_id,
        item=item_id,
        landing=landing_id,
        repair=repair_id,
        child1=child1,
        child1_gender=gender1,
        child2=child2,
        child2_gender=gender2,
        elder=elder,
        elder_type=elder_type,
        trait1=rng.choice(TRAITS),
        trait2=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.landing not in LANDINGS:
        raise StoryError(f"(Invalid landing: {params.landing})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Invalid repair: {params.repair})")

    item_cfg = ITEMS[params.item]
    landing_cfg = LANDINGS[params.landing]
    repair_cfg = REPAIRS[params.repair]
    if not works_for(item_cfg, landing_cfg, repair_cfg):
        raise StoryError(explain_rejection(item_cfg, landing_cfg, repair_cfg))

    world = tell(
        place=PLACES[params.place],
        item_cfg=item_cfg,
        landing_cfg=landing_cfg,
        repair_cfg=repair_cfg,
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        elder_name=params.elder,
        elder_type=params.elder_type,
        trait1=params.trait1,
        trait2=params.trait2,
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
        print(f"{len(combos)} compatible (place, item, landing, repair) combos:\n")
        for place_id, item_id, landing_id, repair_id in combos:
            print(f"  {place_id:13} {item_id:13} {landing_id:15} {repair_id}")
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
            header = f"### {p.child1} and {p.child2}: {p.item} -> {p.landing} -> {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
