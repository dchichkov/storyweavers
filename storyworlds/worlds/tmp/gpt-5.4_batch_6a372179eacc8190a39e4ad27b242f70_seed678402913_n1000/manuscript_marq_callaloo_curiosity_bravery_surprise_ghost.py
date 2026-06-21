#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/manuscript_marq_callaloo_curiosity_bravery_surprise_ghost.py
========================================================================================

A small standalone storyworld in a gentle ghost-story style.

Premise:
    Marq helps make callaloo on a windy evening. An old manuscript recipe has a
    missing last line, and something important for the pot is gone. Strange
    noises and pale light seem ghostly at first. Curiosity pulls Marq forward,
    bravery gets tested, and the surprise is that the ghost is kindly: an
    ancestor guiding the meal toward home.

Run it:
    python storyworlds/worlds/gpt-5.4/manuscript_marq_callaloo_curiosity_bravery_surprise_ghost.py
    python storyworlds/worlds/gpt-5.4/manuscript_marq_callaloo_curiosity_bravery_surprise_ghost.py --all
    python storyworlds/worlds/gpt-5.4/manuscript_marq_callaloo_curiosity_bravery_surprise_ghost.py --trace --qa
    python storyworlds/worlds/gpt-5.4/manuscript_marq_callaloo_curiosity_bravery_surprise_ghost.py --verify
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
# from the repo root. This file lives under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    label: str
    kitchen: str
    dark_place: str
    warm_place: str
    weather: str
    allows_spots: set[str] = field(default_factory=set)
    detail: str = ""


@dataclass
class ManuscriptCfg:
    id: str
    label: str
    phrase: str
    flaw: str
    hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    phrase: str
    room: str
    keeps: set[str] = field(default_factory=set)
    spooky: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    need: str
    fix: str
    qa_fix: str
    stored_in: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    text: str
    scariness: int
    reveal: str
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_eerie_sign(world: World) -> list[str]:
    house = world.get("house")
    marq = world.get("marq")
    if house.meters["sign_active"] < THRESHOLD:
        return []
    sig = ("eerie_sign",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    marq.memes["fear"] += 1
    marq.memes["curiosity"] += 1
    return []


def _r_found_item(world: World) -> list[str]:
    item = world.get("missing")
    pot = world.get("pot")
    marq = world.get("marq")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_item",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pot.meters["ready"] += 1
    pot.meters["problem"] = 0.0
    marq.memes["surprise"] += 1
    marq.memes["fear"] = max(0.0, marq.memes["fear"] - 1.0)
    return []


def _r_friendly_ghost(world: World) -> list[str]:
    ghost = world.get("ghost")
    item = world.get("missing")
    marq = world.get("marq")
    if ghost.meters["seen"] < THRESHOLD or item.meters["found"] < THRESHOLD:
        return []
    sig = ("friendly_ghost",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["kindness"] += 1
    marq.memes["wonder"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="eerie_sign", tag="emotion", apply=_r_eerie_sign),
    Rule(name="found_item", tag="physical", apply=_r_found_item),
    Rule(name="friendly_ghost", tag="emotion", apply=_r_friendly_ghost),
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
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def item_in_spot(item: MissingItem, spot: HidingSpot) -> bool:
    return item.id in spot.keeps and spot.id in item.stored_in


def valid_combo(setting_id: str, spot_id: str, item_id: str) -> bool:
    return (
        spot_id in SETTINGS[setting_id].allows_spots
        and item_in_spot(MISSING_ITEMS[item_id], HIDING_SPOTS[spot_id])
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for spot_id in sorted(setting.allows_spots):
            for item_id in MISSING_ITEMS:
                if item_in_spot(MISSING_ITEMS[item_id], HIDING_SPOTS[spot_id]):
                    combos.append((setting_id, spot_id, item_id))
    return sorted(combos)


def bravery_points(trait: str) -> int:
    return TRAIT_BRAVERY[trait]


def explore_alone(trait: str, sign_id: str) -> bool:
    return bravery_points(trait) >= SIGNS[sign_id].scariness


def predict_search(world: World, trait: str, sign_id: str) -> dict:
    sim = world.copy()
    sim.get("house").meters["sign_active"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("marq").memes["fear"],
        "curiosity": sim.get("marq").memes["curiosity"],
        "alone": explore_alone(trait, sign_id),
    }


def introduce(world: World, marq: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"On a {setting.weather} evening, Marq stood in {setting.kitchen} with "
        f"{marq.pronoun('possessive')} {elder.label_word}. {setting.detail}"
    )
    world.say(
        f"A pot of callaloo whispered on the stove, and the whole {setting.label} "
        f"smelled green and warm."
    )


def show_manuscript(world: World, elder: Entity, manuscript: ManuscriptCfg) -> None:
    world.say(
        f"{elder.label_word.capitalize()} opened {manuscript.phrase}, an old manuscript "
        f"used only on special nights."
    )
    world.say(
        f"But {manuscript.flaw}, so the last part of the recipe felt like a small "
        f"hole in the middle of a song."
    )


def discover_problem(world: World, item: MissingItem) -> None:
    pot = world.get("pot")
    pot.meters["problem"] += 1
    world.say(
        f'"We still need {item.need}," Marq said. Without it, the callaloo could not be finished.'
    )


def activate_sign(world: World, sign: Sign, spot: HidingSpot) -> None:
    world.get("house").meters["sign_active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, {sign.text} near {spot.phrase}. The sound was soft, but in the dim house it felt wonderfully strange."
    )


def warning(world: World, elder: Entity, trait: str, sign_id: str) -> None:
    pred = predict_search(world, trait, sign_id)
    alone = pred["alone"]
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_curiosity"] = pred["curiosity"]
    if alone:
        world.say(
            f'Marq felt a cold tickle of fear and a bigger tug of curiosity. "{elder.label_word.capitalize()}, I think something is trying to show us something," {world.get("marq").pronoun()} whispered.'
        )
    else:
        world.say(
            f'Marq shivered and stepped closer to {elder.label_word}. "{elder.label_word.capitalize()}, will you come with me?" {world.get("marq").pronoun()} asked.'
        )


def go_search(world: World, setting: Setting, elder: Entity, spot: HidingSpot, alone: bool) -> None:
    marq = world.get("marq")
    if alone:
        marq.memes["bravery"] += 1
        world.say(
            f"With one hand on the wall and one brave breath in {marq.pronoun('possessive')} chest, Marq walked toward {spot.phrase} by {marq.pronoun('object')}self."
        )
    else:
        marq.memes["bravery"] += 1
        elder.memes["care"] += 1
        world.say(
            f"{elder.label_word.capitalize()} took Marq's hand, and together they crossed the creaky hall toward {spot.phrase}."
        )
    world.say(
        f"The boards sighed, the shadows stretched long, and {setting.dark_place} did not feel quite so frightening once they kept moving."
    )


def find_item(world: World, spot: HidingSpot, item: MissingItem, manuscript: ManuscriptCfg) -> None:
    found = world.get("missing")
    ghost = world.get("ghost")
    found.meters["found"] += 1
    ghost.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Inside {spot.phrase}, Marq found {item.phrase} tucked beside a curled scrap from the manuscript."
    )
    world.say(
        f"On the scrap were the missing words: {manuscript.hint}"
    )


def reveal_ghost(world: World, sign: Sign, elder: Entity) -> None:
    ghost = world.get("ghost")
    marq = world.get("marq")
    if ghost.memes["kindness"] >= THRESHOLD:
        world.say(
            f"Then {sign.reveal} A pale grandmother-shape smiled from the doorway for one blink, more kind than scary."
        )
        world.say(
            f'"That was your great-gran helping," {elder.label_word} said softly. Marq was startled, but the surprise felt warm instead of mean.'
        )


def finish_callaloo(world: World, item: MissingItem, elder: Entity, setting: Setting) -> None:
    marq = world.get("marq")
    pot = world.get("pot")
    if pot.meters["ready"] >= THRESHOLD:
        marq.memes["joy"] += 1
        world.say(
            f"Back in {setting.warm_place}, they used {item.phrase} and {item.fix}."
        )
        world.say(
            f"Soon the callaloo smelled rich and deep, and the kitchen windows shone as if the house were smiling too."
        )
        world.say(
            f"Marq tasted the spoonful, grinned at {elder.label_word}, and felt braver than before."
        )


def ending_image(world: World, setting: Setting) -> None:
    marq = world.get("marq")
    world.say(
        f"Later, while bowls of callaloo warmed small hands at the table, Marq looked once toward {setting.dark_place}."
    )
    world.say(
        f"The shadows were still there, but now {marq.pronoun()} thought of them as secret-keepers, not enemies."
    )


def tell(
    setting: Setting,
    manuscript: ManuscriptCfg,
    spot: HidingSpot,
    item: MissingItem,
    sign: Sign,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    marq = world.add(Entity(id="marq", kind="character", type="boy", label="Marq", role="child"))
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
        )
    )
    world.add(Entity(id="house", kind="place", type="house", label=setting.label))
    world.add(Entity(id="pot", kind="thing", type="pot", label="callaloo pot"))
    world.add(Entity(id="missing", kind="thing", type="ingredient", label=item.label))
    world.add(Entity(id="ghost", kind="character", type="woman", label="the ghost"))

    marq.attrs["trait"] = trait
    marq.memes["curiosity"] += 1

    introduce(world, marq, elder, setting)
    show_manuscript(world, elder, manuscript)
    discover_problem(world, item)

    world.para()
    activate_sign(world, sign, spot)
    warning(world, elder, trait, sign.id)

    alone = explore_alone(trait, sign.id)
    world.facts["searched_alone"] = alone
    world.para()
    go_search(world, setting, elder, spot, alone)
    find_item(world, spot, item, manuscript)
    reveal_ghost(world, sign, elder)

    world.para()
    finish_callaloo(world, item, elder, setting)
    ending_image(world, setting)

    world.facts.update(
        marq=marq,
        elder=elder,
        setting=setting,
        manuscript=manuscript,
        spot=spot,
        item=item,
        sign=sign,
        trait=trait,
        outcome="alone" if alone else "together",
        ghost_seen=world.get("ghost").meters["seen"] >= THRESHOLD,
        callaloo_ready=world.get("pot").meters["ready"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "veranda_house": Setting(
        id="veranda_house",
        label="the old veranda house",
        kitchen="the narrow kitchen of the old veranda house",
        dark_place="the back corridor under the rafters",
        warm_place="the stove corner",
        weather="windy",
        allows_spots={"bread_chest", "pantry_shelf"},
        detail="Rain tapped the shutters, and the lamp made a gold puddle on the table.",
    ),
    "seaside_cottage": Setting(
        id="seaside_cottage",
        label="the seaside cottage",
        kitchen="the blue kitchen of the seaside cottage",
        dark_place="the shell-cool hallway by the back room",
        warm_place="the bright stove nook",
        weather="salt-wet",
        allows_spots={"window_trunk", "pantry_shelf"},
        detail="Outside, waves thumped softly, and inside the floorboards held old stories.",
    ),
    "hill_house": Setting(
        id="hill_house",
        label="the hill house",
        kitchen="the stone kitchen of the hill house",
        dark_place="the stair bend where the lamp could not quite reach",
        warm_place="the firelit table",
        weather="misty",
        allows_spots={"bread_chest", "window_trunk"},
        detail="Mist curled at the windows, and the spoons hanging by the door barely moved.",
    ),
}

MANUSCRIPTS = {
    "recipe_page": ManuscriptCfg(
        id="recipe_page",
        label="recipe page",
        phrase="a flour-dusted recipe page",
        flaw="the bottom line had faded into a gray blur",
        hint='"Stir gently, then add the last green handful with love."',
        tags={"manuscript", "recipe"},
    ),
    "folded_note": ManuscriptCfg(
        id="folded_note",
        label="folded note",
        phrase="a folded manuscript note tied with thread",
        flaw="one corner was torn away",
        hint='"The quiet hand knows where the pot is waiting."',
        tags={"manuscript", "note"},
    ),
    "cookbook_leaf": ManuscriptCfg(
        id="cookbook_leaf",
        label="cookbook leaf",
        phrase="a loose manuscript leaf from a family cookbook",
        flaw="steam stains had hidden the last sentence",
        hint='"Do not forget the final touch, or the soup will stay sleepy."',
        tags={"manuscript", "cookbook"},
    ),
}

HIDING_SPOTS = {
    "bread_chest": HidingSpot(
        id="bread_chest",
        label="bread chest",
        phrase="the old bread chest",
        room="hall",
        keeps={"wooden_spoon", "callaloo_bundle"},
        spooky="The lid always knocked once before it opened.",
        tags={"chest"},
    ),
    "pantry_shelf": HidingSpot(
        id="pantry_shelf",
        label="pantry shelf",
        phrase="the highest pantry shelf",
        room="pantry",
        keeps={"coconut_milk", "callaloo_bundle"},
        spooky="Glass jars clicked there on windy nights.",
        tags={"pantry"},
    ),
    "window_trunk": HidingSpot(
        id="window_trunk",
        label="window trunk",
        phrase="the cedar trunk under the window",
        room="back room",
        keeps={"wooden_spoon", "coconut_milk"},
        spooky="It smelled of rain and cedar whenever the house grew quiet.",
        tags={"trunk"},
    ),
}

MISSING_ITEMS = {
    "wooden_spoon": MissingItem(
        id="wooden_spoon",
        label="wooden spoon",
        phrase="the long wooden spoon",
        need="the long wooden spoon to stir the thick pot properly",
        fix="stirred the callaloo until the greens relaxed into the broth",
        qa_fix="used the wooden spoon to stir the thick callaloo properly",
        stored_in={"bread_chest", "window_trunk"},
        tags={"spoon", "cooking"},
    ),
    "callaloo_bundle": MissingItem(
        id="callaloo_bundle",
        label="callaloo leaves",
        phrase="a fresh bundle of callaloo leaves",
        need="one last fresh bundle of callaloo leaves",
        fix="tore in the shining leaves, and the soup woke up at once",
        qa_fix="added the last fresh callaloo leaves",
        stored_in={"bread_chest", "pantry_shelf"},
        tags={"callaloo", "greens"},
    ),
    "coconut_milk": MissingItem(
        id="coconut_milk",
        label="coconut milk",
        phrase="a small tin of coconut milk",
        need="the small tin of coconut milk for the last smooth swirl",
        fix="poured in the coconut milk, and the broth turned silky",
        qa_fix="added the coconut milk for the last smooth swirl",
        stored_in={"pantry_shelf", "window_trunk"},
        tags={"coconut", "cooking"},
    ),
}

SIGNS = {
    "whisper": Sign(
        id="whisper",
        label="whisper",
        text="a whisper said Marq's name twice",
        scariness=3,
        reveal="the whisper changed into a tiny humming laugh.",
        tags={"ghost", "sound"},
    ),
    "blue_glow": Sign(
        id="blue_glow",
        label="blue glow",
        text="a blue glow trembled in the dark",
        scariness=2,
        reveal="the blue glow folded itself into the shape of a shawl and then faded.",
        tags={"ghost", "light"},
    ),
    "tapping_ladle": Sign(
        id="tapping_ladle",
        label="tapping ladle",
        text="a hanging ladle tapped the wall three times all by itself",
        scariness=2,
        reveal="the tapping became a cheerful kitchen rhythm, like someone pleased to be heard.",
        tags={"ghost", "kitchen"},
    ),
}

ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]
TRAITS = ["bold", "steady", "careful", "curious"]
TRAIT_BRAVERY = {
    "bold": 3,
    "steady": 3,
    "careful": 2,
    "curious": 2,
}


@dataclass
class StoryParams:
    setting: str
    manuscript: str
    spot: str
    item: str
    sign: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "manuscript": [
        (
            "What is a manuscript?",
            "A manuscript is a piece of writing kept on paper, often by hand. Old family recipes and notes can be manuscripts too.",
        )
    ],
    "callaloo": [
        (
            "What is callaloo?",
            "Callaloo is a warm dish made with leafy greens and other ingredients. People often cook it in a pot and share it at the table.",
        )
    ],
    "ghost": [
        (
            "Do all ghost stories have mean ghosts?",
            "No. Some ghost stories have gentle ghosts who warn, guide, or protect people. A spooky feeling can still lead to something kind.",
        )
    ],
    "spoon": [
        (
            "Why do people use a wooden spoon in cooking?",
            "A wooden spoon is good for stirring warm food in a pot. It helps mix thick soup gently.",
        )
    ],
    "coconut": [
        (
            "What is coconut milk used for in cooking?",
            "Coconut milk can make food smooth and rich. It is often poured into soups and stews.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the next right thing even when you feel afraid. It does not mean you never feel scared.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to learn or look closer. It helps people notice clues and ask questions.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you did not expect. It can feel sharp for a moment and then turn happy.",
        )
    ],
}
KNOWLEDGE_ORDER = ["manuscript", "callaloo", "ghost", "spoon", "coconut", "bravery", "curiosity", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    item = f["item"]
    sign = f["sign"]
    outcome = f["outcome"]
    if outcome == "alone":
        return [
            'Write a gentle ghost story for a 3-to-5-year-old that includes the words "manuscript", "Marq", and "callaloo".',
            f"Tell a story where Marq follows a spooky {sign.label} through {setting.label} and bravely finds {item.phrase} to save the callaloo.",
            "Write a child-facing ghost story with Curiosity, Bravery, and a warm Surprise ending.",
        ]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "manuscript", "Marq", and "callaloo".',
        f"Tell a story where Marq gets frightened by a spooky sign, asks an elder for help, and together they find {item.phrase}.",
        "Write a child-facing ghost story with Curiosity, Bravery, and a friendly Surprise at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    elder = f["elder"]
    item = f["item"]
    sign = f["sign"]
    manuscript = f["manuscript"]
    setting = f["setting"]
    marq = f["marq"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Marq and {elder.label_word}. They were trying to finish a pot of callaloo in {setting.label}.",
        ),
        (
            "What was wrong with the recipe?",
            f"The old manuscript was missing its last line because {manuscript.flaw}. That made the recipe feel unfinished.",
        ),
        (
            "Why did Marq go into the dark part of the house?",
            f"Marq heard or saw {sign.text} near {f['spot'].phrase}. Curiosity tugged at Marq even though the house felt spooky.",
        ),
    ]
    if f["outcome"] == "alone":
        qa.append(
            (
                "How was Marq brave?",
                f"Marq felt scared, but still walked to {f['spot'].phrase} alone and kept looking carefully. That bravery helped Marq find {item.phrase}.",
            )
        )
    else:
        qa.append(
            (
                "How was Marq brave if Marq did not go alone?",
                f"Marq was brave because Marq told {elder.label_word} the truth about being scared and still went to look. Asking for help can be brave too.",
            )
        )
    if f["ghost_seen"]:
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that the ghost was friendly and seemed to belong to Marq's family. It guided them to {item.phrase} instead of trying to hurt anyone.",
            )
        )
    if f["callaloo_ready"]:
        qa.append(
            (
                "How did they finish the callaloo?",
                f"They found {item.phrase} and then {item.qa_fix}. That solved the missing part of the recipe and made the pot ready for supper.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"manuscript", "callaloo", "ghost", "bravery", "curiosity", "surprise"}
    item = world.facts["item"]
    if item.id == "wooden_spoon":
        tags.add("spoon")
    if item.id == "coconut_milk":
        tags.add("coconut")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="veranda_house",
        manuscript="recipe_page",
        spot="bread_chest",
        item="wooden_spoon",
        sign="whisper",
        elder="grandmother",
        trait="bold",
    ),
    StoryParams(
        setting="seaside_cottage",
        manuscript="cookbook_leaf",
        spot="pantry_shelf",
        item="callaloo_bundle",
        sign="blue_glow",
        elder="aunt",
        trait="careful",
    ),
    StoryParams(
        setting="hill_house",
        manuscript="folded_note",
        spot="window_trunk",
        item="coconut_milk",
        sign="tapping_ladle",
        elder="grandfather",
        trait="steady",
    ),
    StoryParams(
        setting="veranda_house",
        manuscript="cookbook_leaf",
        spot="pantry_shelf",
        item="coconut_milk",
        sign="blue_glow",
        elder="uncle",
        trait="curious",
    ),
]


def explain_rejection(setting_id: str, spot_id: str, item_id: str) -> str:
    setting = SETTINGS[setting_id]
    spot = HIDING_SPOTS[spot_id]
    item = MISSING_ITEMS[item_id]
    if spot_id not in setting.allows_spots:
        allowed = ", ".join(sorted(setting.allows_spots))
        return (
            f"(No story: {spot.phrase} is not part of {setting.label}. "
            f"Try one of these spots: {allowed}.)"
        )
    return (
        f"(No story: {item.phrase} does not belong in {spot.phrase} in this world. "
        f"Pick a spot that could honestly hide it.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "alone" if explore_alone(params.trait, params.sign) else "together"


ASP_RULES = r"""
in_setting(S, P) :- allows_spot(S, P).
stores(P, I) :- spot_keeps(P, I), item_stored_in(I, P).
valid(S, P, I) :- in_setting(S, P), stores(P, I).

bravery(B) :- trait(T), trait_bravery(T, B).
search_alone :- bravery(B), sign_scariness(S), B >= S.
outcome(alone) :- search_alone.
outcome(together) :- not search_alone.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for spot_id in sorted(setting.allows_spots):
            lines.append(asp.fact("allows_spot", setting_id, spot_id))
    for spot_id, spot in HIDING_SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for item_id in sorted(spot.keeps):
            lines.append(asp.fact("spot_keeps", spot_id, item_id))
    for item_id, item in MISSING_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for spot_id in sorted(item.stored_in):
            lines.append(asp.fact("item_stored_in", item_id, spot_id))
    for trait, score in TRAIT_BRAVERY.items():
        lines.append(asp.fact("trait_bravery", trait, score))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("sign_rank", sign_id, sign.scariness))
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
            asp.fact("trait", params.trait),
            asp.fact("chosen_sign", params.sign),
            asp.fact("sign_scariness", SIGNS[params.sign].scariness),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test story generation worked.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: Marq, a manuscript, callaloo, and a gentle ghostly surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--manuscript", choices=MANUSCRIPTS)
    ap.add_argument("--spot", choices=HIDING_SPOTS)
    ap.add_argument("--item", choices=MISSING_ITEMS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.spot and args.item:
        if not valid_combo(args.setting, args.spot, args.item):
            raise StoryError(explain_rejection(args.setting, args.spot, args.item))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.spot is None or combo[1] == args.spot)
        and (args.item is None or combo[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, spot_id, item_id = rng.choice(combos)
    manuscript_id = args.manuscript or rng.choice(sorted(MANUSCRIPTS))
    sign_id = args.sign or rng.choice(sorted(SIGNS))
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        manuscript=manuscript_id,
        spot=spot_id,
        item=item_id,
        sign=sign_id,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.manuscript not in MANUSCRIPTS:
        raise StoryError(f"(Unknown manuscript: {params.manuscript})")
    if params.spot not in HIDING_SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.item not in MISSING_ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.elder not in ELDERS:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if not valid_combo(params.setting, params.spot, params.item):
        raise StoryError(explain_rejection(params.setting, params.spot, params.item))

    world = tell(
        setting=SETTINGS[params.setting],
        manuscript=MANUSCRIPTS[params.manuscript],
        spot=HIDING_SPOTS[params.spot],
        item=MISSING_ITEMS[params.item],
        sign=SIGNS[params.sign],
        elder_type=params.elder,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, spot, item) combos:\n")
        for setting_id, spot_id, item_id in combos:
            print(f"  {setting_id:16} {spot_id:13} {item_id}")
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
            header = f"### Marq at {p.setting}: {p.item} in {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
