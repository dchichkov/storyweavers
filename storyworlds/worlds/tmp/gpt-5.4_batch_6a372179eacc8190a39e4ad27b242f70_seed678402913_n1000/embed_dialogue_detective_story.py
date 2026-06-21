#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/embed_dialogue_detective_story.py
============================================================

A tiny detective-story world with dialogue: a child notices a missing object,
studies one grounded clue, infers a likely culprit, and finds the object in a
plausible hiding place. The stories stay small and concrete on purpose.

The seed asked for:
- word: "embed"
- feature: Dialogue
- style: Detective Story

So every sample includes spoken lines and a little casebook moment using the
word "embed" naturally in dialogue.

Run it
------
    python storyworlds/worlds/gpt-5.4/embed_dialogue_detective_story.py
    python storyworlds/worlds/gpt-5.4/embed_dialogue_detective_story.py --case garden --culprit puppy
    python storyworlds/worlds/gpt-5.4/embed_dialogue_detective_story.py --item badge --culprit magpie
    python storyworlds/worlds/gpt-5.4/embed_dialogue_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/embed_dialogue_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/embed_dialogue_detective_story.py --verify
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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        animal = {"puppy", "dog", "magpie", "bird"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class CaseFile:
    id: str
    place: str
    opening: str
    lost_site: str
    search_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    adjective: str
    portable: bool = True
    shiny: bool = False
    soft: bool = False
    pretend_use: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    type: str
    motive: str
    prefers: set[str] = field(default_factory=set)
    clue: str = ""
    clue_text: str = ""
    hideout: str = ""
    hideout_text: str = ""
    evidence: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperTool:
    id: str
    label: str
    phrase: str
    action_text: str
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
    apply: Callable[[World], list[str]]


def _r_worry_to_case(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    if hero is None or item is None:
        return out
    if hero.memes["worry"] >= THRESHOLD and item.meters["missing"] >= THRESHOLD:
        sig = ("case_open",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["curiosity"] += 1
            out.append("__case_open__")
    return out


def _r_clue_to_suspicion(world: World) -> list[str]:
    out: list[str] = []
    clue_kind = world.facts.get("clue_kind")
    culprit = world.entities.get("culprit")
    hero = world.entities.get("hero")
    if not clue_kind or culprit is None or hero is None:
        return out
    if clue_kind == culprit.attrs.get("clue"):
        sig = ("suspicion", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["confidence"] += 1
            culprit.meters["suspected"] += 1
            out.append("__suspicion__")
    return out


def _r_found_to_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("item")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if item is None or hero is None or helper is None:
        return out
    if item.meters["found"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            helper.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="worry_to_case", apply=_r_worry_to_case),
    Rule(name="clue_to_suspicion", apply=_r_clue_to_suspicion),
    Rule(name="found_to_relief", apply=_r_found_to_relief),
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


CASES = {
    "garden": CaseFile(
        id="garden",
        place="the garden",
        opening="The afternoon garden smelled like mint and wet dirt.",
        lost_site="the little table by the back steps",
        search_line="They followed the clue past the watering can and the bean poles.",
        ending_image="The leaves trembled softly as the case closed.",
        tags={"garden"},
    ),
    "playroom": CaseFile(
        id="playroom",
        place="the playroom",
        opening="The playroom was warm with lamp light and blocks stacked like towers.",
        lost_site="the toy shelf by the rug",
        search_line="They searched between the book basket and the cardboard castle.",
        ending_image="The toy lamp made a bright yellow circle on the rug.",
        tags={"playroom"},
    ),
    "porch": CaseFile(
        id="porch",
        place="the front porch",
        opening="The porch boards creaked, and the afternoon sun made long stripes across the mat.",
        lost_site="the bench beside the flowerpot",
        search_line="They moved carefully past the rain boots and the old umbrella stand.",
        ending_image="A breeze tapped the wind chime as the mystery ended.",
        tags={"porch"},
    ),
}

ITEMS = {
    "badge": MissingItem(
        id="badge",
        label="badge",
        phrase="a shiny paper detective badge",
        adjective="shiny",
        portable=True,
        shiny=True,
        soft=False,
        pretend_use="pin to a sweater for detective work",
        tags={"badge", "detective"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        phrase="a soft blue ribbon",
        adjective="soft",
        portable=True,
        shiny=False,
        soft=True,
        pretend_use="tie around a toy bear's neck",
        tags={"ribbon"},
    ),
    "spoon": MissingItem(
        id="spoon",
        label="spoon",
        phrase="a little silver spoon",
        adjective="silver",
        portable=True,
        shiny=True,
        soft=False,
        pretend_use="stir pretend soup in a play kitchen",
        tags={"spoon", "kitchen"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="the puppy",
        type="puppy",
        motive="liked to carry interesting things in its mouth",
        prefers={"soft", "small"},
        clue="pawprint",
        clue_text="Four muddy pawprints dotted the floor like tiny stamps.",
        hideout="bush",
        hideout_text="under the rosemary bush",
        evidence="a chewed leaf and one small tuft of fur",
        tags={"puppy", "pawprint"},
    ),
    "magpie": Culprit(
        id="magpie",
        label="the magpie",
        type="magpie",
        motive="could not resist shiny things",
        prefers={"shiny", "small"},
        clue="feather",
        clue_text="A black-and-blue feather lay caught beside the missing spot.",
        hideout="nest",
        hideout_text="inside a low basket nest on the fence shelf",
        evidence="two bright bottle caps tucked beside the prize",
        tags={"magpie", "feather"},
    ),
    "brother": Culprit(
        id="brother",
        label="little Ben",
        type="brother",
        motive="wanted it for a pretend game and forgot to ask first",
        prefers={"costume", "small"},
        clue="crayon_note",
        clue_text='A crayon note on scrap paper read, "For my secret fort."',
        hideout="fort",
        hideout_text="inside the blanket fort behind the sofa",
        evidence="a pillow guard and a cardboard sign that said CASTLE",
        tags={"brother", "note", "fort"},
    ),
}

HELPERS = {
    "magnifier": HelperTool(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass",
        action_text="held the clue under the magnifying glass until its edges looked huge",
        tags={"magnifier"},
    ),
    "flashlight": HelperTool(
        id="flashlight",
        label="flashlight",
        phrase="a stubby flashlight",
        action_text="shone the flashlight into dim corners and under benches",
        tags={"flashlight"},
    ),
    "notebook": HelperTool(
        id="notebook",
        label="casebook",
        phrase="a striped detective notebook",
        action_text="opened the casebook and copied the clue in careful block letters",
        tags={"notebook"},
    ),
}

GIRL_NAMES = ["Nina", "Lila", "Maya", "Rosa", "Tess", "Eva"]
BOY_NAMES = ["Owen", "Max", "Leo", "Finn", "Eli", "Sam"]
HELPER_NAMES = ["June", "Milo", "Ivy", "Theo", "Pia", "Ned"]


def preferred_tags_for_item(item: MissingItem) -> set[str]:
    tags = {"small"}
    if item.shiny:
        tags.add("shiny")
    if item.soft:
        tags.add("soft")
    if item.id in {"badge", "ribbon"}:
        tags.add("costume")
    return tags


def valid_combo(case_id: str, item_id: str, culprit_id: str) -> bool:
    if case_id not in CASES or item_id not in ITEMS or culprit_id not in CULPRITS:
        return False
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    item_tags = preferred_tags_for_item(item)
    return bool(item_tags & culprit.prefers)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for case_id in CASES:
        for item_id in ITEMS:
            for culprit_id in CULPRITS:
                if valid_combo(case_id, item_id, culprit_id):
                    combos.append((case_id, item_id, culprit_id))
    return combos


def likely_culprit_for_clue(clue_kind: str) -> Optional[str]:
    for culprit_id, culprit in CULPRITS.items():
        if culprit.clue == clue_kind:
            return culprit_id
    return None


def predict_solution(item: MissingItem, clue_kind: str) -> dict:
    culprit_id = likely_culprit_for_clue(clue_kind)
    if culprit_id is None:
        return {"solvable": False, "culprit": None}
    culprit = CULPRITS[culprit_id]
    return {
        "solvable": bool(preferred_tags_for_item(item) & culprit.prefers),
        "culprit": culprit_id,
    }


@dataclass
class StoryParams:
    case: str
    item: str
    culprit: str
    helper_tool: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        case="garden",
        item="ribbon",
        culprit="puppy",
        helper_tool="magnifier",
        hero_name="Nina",
        hero_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        parent="mother",
        seed=101,
    ),
    StoryParams(
        case="porch",
        item="spoon",
        culprit="magpie",
        helper_tool="flashlight",
        hero_name="Owen",
        hero_gender="boy",
        helper_name="Ivy",
        helper_gender="girl",
        parent="father",
        seed=102,
    ),
    StoryParams(
        case="playroom",
        item="badge",
        culprit="brother",
        helper_tool="notebook",
        hero_name="Lila",
        hero_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        parent="mother",
        seed=103,
    ),
]


def choose_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def choose_helper_name(rng: random.Random, avoid: str = "") -> str:
    choices = [name for name in HELPER_NAMES if name != avoid]
    return rng.choice(choices)


def explain_rejection(item_id: str, culprit_id: str) -> str:
    if item_id not in ITEMS or culprit_id not in CULPRITS:
        return "(No story: unknown item or culprit.)"
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    item_tags = sorted(preferred_tags_for_item(item))
    likes = sorted(culprit.prefers)
    return (
        f"(No story: {culprit.label} would not reasonably take {item.phrase}. "
        f"The item suggests {item_tags}, but the culprit is only drawn to {likes}.)"
    )


def opening_scene(world: World, case_cfg: CaseFile, hero: Entity, helper: Entity, parent: Entity, item_ent: Entity, item_cfg: MissingItem) -> None:
    world.say(case_cfg.opening)
    world.say(
        f"{hero.id} liked pretending to be a detective, and today {helper.id} was {hero.pronoun('possessive')} assistant."
    )
    world.say(
        f"On {case_cfg.lost_site}, {hero.id} had left {item_cfg.phrase} that {hero.pronoun()} loved to {item_cfg.pretend_use}."
    )
    world.say(
        f'When {hero.pronoun()} came back, the {item_cfg.label} was gone. "{parent.label_word.capitalize()}, my {item_cfg.label} is missing!" {hero.id} cried.'
    )
    item_ent.meters["missing"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=False)


def case_talk(world: World, hero: Entity, helper: Entity, tool: HelperTool, culprit_cfg: Culprit) -> None:
    world.say(
        f'"Do not worry," said {helper.id}. "Real detectives look slowly first."'
    )
    world.say(
        f'{hero.id} nodded and pulled out {tool.phrase}. "I like to embed a tiny clue page under clear tape in my casebook," {hero.pronoun()} said. "Then the case does not wiggle away in my notebook."'
    )
    world.say(
        f"{helper.id} {tool.action_text}."
    )
    world.say(culprit_cfg.clue_text)
    world.facts["clue_kind"] = culprit_cfg.clue
    propagate(world, narrate=False)


def infer(world: World, hero: Entity, helper: Entity, culprit_cfg: Culprit, item_cfg: MissingItem) -> None:
    guess = likely_culprit_for_clue(world.facts.get("clue_kind", ""))
    if guess != culprit_cfg.id:
        raise StoryError("(Story logic broke: the clue did not point to the chosen culprit.)")
    world.say(
        f'"That clue means {culprit_cfg.label} was here," whispered {hero.id}.'
    )
    world.say(
        f'"Why {culprit_cfg.label}?" asked {helper.id}.'
    )
    world.say(
        f'"Because it {culprit_cfg.motive}, and {item_cfg.phrase} was exactly the kind of thing it would notice," said {hero.id}.'
    )


def search(world: World, case_cfg: CaseFile, hero: Entity, helper: Entity, culprit_cfg: Culprit) -> None:
    world.para()
    world.say(case_cfg.search_line)
    world.say(
        f'"Look near {culprit_cfg.hideout_text}," said {hero.id}. "{culprit_cfg.label.capitalize()} would hide it there."'
    )
    helper.memes["trust"] += 1
    hero.memes["focus"] += 1


def recover(world: World, hero: Entity, helper: Entity, item_ent: Entity, culprit_cfg: Culprit, item_cfg: MissingItem) -> None:
    item_ent.meters["found"] += 1
    item_ent.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"There, {helper.id} spotted {item_cfg.phrase} {culprit_cfg.hideout_text}, right beside {culprit_cfg.evidence}."
    )
    world.say(
        f'"Case solved!" said {helper.id}.'
    )
    world.say(
        f'{hero.id} lifted the {item_cfg.label} carefully. "Nobody was trying to be mean," {hero.pronoun()} said. "The clue told us what happened."'
    )


def resolution(world: World, case_cfg: CaseFile, hero: Entity, helper: Entity, parent: Entity, culprit_cfg: Culprit, item_cfg: MissingItem) -> None:
    world.para()
    if culprit_cfg.id == "brother":
        world.say(
            f"Little Ben popped out of the fort with pink cheeks. \"I only wanted the {item_cfg.label} for my castle guard,\" he said."
        )
        world.say(
            f'"Next time, please ask first," said {hero.id}.'
        )
    elif culprit_cfg.id == "puppy":
        world.say(
            f"The puppy wagged so hard that its tail tapped the floor. \"I think that answer is yes,\" laughed {parent.label_word}."
        )
    else:
        world.say(
            f"The magpie clacked its beak from the fence shelf and tilted its head as if the bright little collection still belonged to it."
        )
    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "You two were gentle detectives. You watched, thought, and then helped."'
    )
    world.say(
        f"{hero.id} pinned the {item_cfg.label} back in place, and {case_cfg.ending_image}"
    )


def tell(
    case_cfg: CaseFile,
    item_cfg: MissingItem,
    culprit_cfg: Culprit,
    helper_tool: HelperTool,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    item_ent = world.add(Entity(id="item", kind="thing", type=item_cfg.id, label=item_cfg.label, phrase=item_cfg.phrase, role="missing_item"))
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character" if culprit_cfg.id == "brother" else "thing",
            type=culprit_cfg.type,
            label=culprit_cfg.label,
            role="culprit",
            attrs={"clue": culprit_cfg.clue, "hideout": culprit_cfg.hideout},
        )
    )

    opening_scene(world, case_cfg, hero, helper, parent, item_ent, item_cfg)
    world.para()
    case_talk(world, hero, helper, helper_tool, culprit_cfg)
    infer(world, hero, helper, culprit_cfg, item_cfg)
    search(world, case_cfg, hero, helper, culprit_cfg)
    recover(world, hero, helper, item_ent, culprit_cfg, item_cfg)
    resolution(world, case_cfg, hero, helper, parent, culprit_cfg, item_cfg)

    world.facts.update(
        case=case_cfg,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        helper_tool=helper_tool,
        hero_name=hero_name,
        helper_name=helper_name,
        parent_type=parent_type,
        clue_kind=culprit_cfg.clue,
        solved=item_ent.meters["found"] >= THRESHOLD,
        culprit=culprit_cfg.id,
        hideout=culprit_cfg.hideout,
    )
    return world


KNOWLEDGE = {
    "pawprint": [
        (
            "What is a pawprint?",
            "A pawprint is the mark an animal foot leaves on mud, dust, or another soft place. It can help you tell where an animal walked.",
        )
    ],
    "feather": [
        (
            "What can a feather tell you?",
            "A feather can show that a bird was nearby. Detectives look at clues like that because small signs can tell a bigger story.",
        )
    ],
    "note": [
        (
            "Why is a note a clue?",
            "A note is a clue because it tells you what someone was thinking or planning. Written words can help explain what happened.",
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes tiny things look bigger. That helps you study little clues more carefully.",
        )
    ],
    "flashlight": [
        (
            "Why do detectives use a flashlight?",
            "A flashlight helps you see into dim corners and under furniture. Good light makes clues easier to notice.",
        )
    ],
    "notebook": [
        (
            "Why keep a detective notebook?",
            "A detective notebook helps you remember clues in the right order. Writing things down keeps a mystery from getting mixed up.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, asks questions, and thinks carefully about what they mean. Then the detective uses those clues to solve a mystery.",
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "pawprint", "feather", "note", "magnifier", "flashlight", "notebook"]


def generation_prompts(world: World) -> list[str]:
    case_cfg = world.facts["case"]
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes dialogue and the word "embed".',
        f"Tell a gentle mystery set in {case_cfg.place} where a child searches for {item_cfg.phrase} and solves the case by following one clear clue.",
        f"Write a child-facing detective story where the clue points to {culprit_cfg.label}, and the ending shows the lost {item_cfg.label} found again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    case_cfg = world.facts["case"]
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    hero_name = world.facts["hero_name"]
    helper_name = world.facts["helper_name"]
    parent_type = world.facts["parent_type"]
    parent_word = {"mother": "mom", "father": "dad"}.get(parent_type, parent_type)
    tool = world.facts["helper_tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child detective, and {helper_name}, the helper. They work together when {item_cfg.phrase} goes missing.",
        ),
        (
            f"What was missing in {case_cfg.place}?",
            f"The missing thing was {item_cfg.phrase}. {hero_name} had left it near {case_cfg.lost_site}, and then it was gone.",
        ),
        (
            f"How did {hero_name} start solving the mystery?",
            f"{hero_name} slowed down and looked for a clue instead of guessing wildly. {helper_name} helped by using {tool.phrase} so they could study the scene carefully.",
        ),
        (
            f"Which clue solved the case, and what did it mean?",
            f"The clue was {culprit_cfg.clue_text.lower()} That clue pointed to {culprit_cfg.label} because it matched the kind of visitor that had been near the missing {item_cfg.label}.",
        ),
        (
            f"Where did they find the {item_cfg.label}?",
            f"They found it {culprit_cfg.hideout_text}. The place fit the clue, so the search felt like a real detective ending instead of a lucky guess.",
        ),
    ]
    if culprit_cfg.id == "brother":
        qa.append(
            (
                "Was the culprit trying to be mean?",
                f"No. Little Ben wanted the {item_cfg.label} for his game and forgot to ask first. The ending matters because the children solve the problem with words, not anger.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {culprit_cfg.label} take the {item_cfg.label}?",
                f"{culprit_cfg.label.capitalize()} took it because it was drawn to that kind of object. The clue and hiding place both showed the same cause, so the mystery made sense once the children looked closely.",
            )
        )
    qa.append(
        (
            f"What did {hero_name}'s {parent_word} like about the way they solved it?",
            f"{parent_word.capitalize()} liked that the children were gentle detectives. They watched first, thought carefully, and then helped instead of making a big fuss.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective"}
    culprit_cfg = world.facts["culprit_cfg"]
    tool = world.facts["helper_tool"]
    if culprit_cfg.clue == "pawprint":
        tags.add("pawprint")
    if culprit_cfg.clue == "feather":
        tags.add("feather")
    if culprit_cfg.clue == "crayon_note":
        tags.add("note")
    tags |= set(tool.tags)
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
        shown_meters = {k: v for k, v in ent.meters.items() if v}
        shown_memes = {k: v for k, v in ent.memes.items() if v}
        bits = [ent.label or ent.id]
        if ent.role:
            bits.append(f"role={ent.role}")
        if shown_meters:
            bits.append(f"meters={dict(shown_meters)}")
        if shown_memes:
            bits.append(f"memes={dict(shown_memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for (name, *_) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
item_has(I, small)   :- item(I).
item_has(I, shiny)   :- shiny(I).
item_has(I, soft)    :- soft(I).
item_has(I, costume) :- costume(I).

compatible(Case, Item, Culprit) :-
    story_case(Case), item(Item), culprit(Culprit),
    item_has(Item, Tag), prefers(Culprit, Tag).

points_to(Clue, Culprit) :- culprit(Culprit), clue_of(Culprit, Clue).

solvable(Item, Clue) :-
    item(Item), clue(Clue), points_to(Clue, Culprit), compatible(_, Item, Culprit).

#defined compatible/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id in CASES:
        lines.append(asp.fact("story_case", case_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.shiny:
            lines.append(asp.fact("shiny", item_id))
        if item.soft:
            lines.append(asp.fact("soft", item_id))
        if item_id in {"badge", "ribbon", "spoon"}:
            lines.append(asp.fact("small", item_id))
        if item_id in {"badge", "ribbon"}:
            lines.append(asp.fact("costume", item_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("clue", culprit.clue))
        lines.append(asp.fact("clue_of", culprit_id, culprit.clue))
        for tag in sorted(culprit.prefers):
            lines.append(asp.fact("prefers", culprit_id, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_points_to() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show points_to/2."))
    return sorted(set(asp.atoms(model, "points_to")))


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in asp:", sorted(asp_set - py))

    py_points = sorted((culprit.clue, culprit_id) for culprit_id, culprit in CULPRITS.items())
    asp_pts = sorted((clue, culprit) for clue, culprit in asp_points_to())
    if py_points == asp_pts:
        print(f"OK: clue mapping matches ({len(py_points)} clue links).")
    else:
        rc = 1
        print("MISMATCH in clue mapping:")
        print("  python:", py_points)
        print("  asp:", asp_pts)

    for params in CURATED:
        try:
            sample = generate(params)
            buf = io.StringIO()
            with redirect_stdout(buf):
                emit(sample, trace=False, qa=False, header="smoke")
            if "embed" not in sample.story:
                raise StoryError("(Smoke test failed: story did not include 'embed'.)")
        except Exception as exc:
            rc = 1
            print(f"SMOKE TEST FAILED for {params}: {exc}")
            break
    else:
        print(f"OK: smoke-tested {len(CURATED)} generated stories.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small detective-story world with dialogue, clues, and a gentle solution."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--helper-tool", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.culprit and not valid_combo(args.case or next(iter(CASES)), args.item, args.culprit):
        raise StoryError(explain_rejection(args.item, args.culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, item_id, culprit_id = rng.choice(sorted(combos))
    helper_tool = args.helper_tool or rng.choice(sorted(HELPERS))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = choose_name(rng, hero_gender)
    helper_name = choose_helper_name(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        case=case_id,
        item=item_id,
        culprit=culprit_id,
        helper_tool=helper_tool,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Unknown case setting: {params.case})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.helper_tool not in HELPERS:
        raise StoryError(f"(Unknown helper tool: {params.helper_tool})")
    if not valid_combo(params.case, params.item, params.culprit):
        raise StoryError(explain_rejection(params.item, params.culprit))

    world = tell(
        case_cfg=CASES[params.case],
        item_cfg=ITEMS[params.item],
        culprit_cfg=CULPRITS[params.culprit],
        helper_tool=HELPERS[params.helper_tool],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show compatible/3.\n#show points_to/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, item, culprit) combos:\n")
        for case_id, item_id, culprit_id in combos:
            print(f"  {case_id:9} {item_id:8} {culprit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        tries = 0
        while len(samples) < args.n and tries < max(args.n * 50, 50):
            seed = base_seed + tries
            tries += 1
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
            header = f"### {p.hero_name}: {p.item} in {p.case} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
