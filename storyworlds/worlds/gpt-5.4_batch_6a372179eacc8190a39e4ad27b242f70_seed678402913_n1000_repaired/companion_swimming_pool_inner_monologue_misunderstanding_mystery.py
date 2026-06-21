#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/companion_swimming_pool_inner_monologue_misunderstanding_mystery.py
================================================================================================

A standalone storyworld about a child at a swimming pool who notices a small
mystery, worries about it through inner monologue, misunderstands what is
happening, and then learns the gentler truth with help from a companion and a
grown-up.

The world model tracks:
- typed entities with physical meters and emotional memes
- a hidden-object poolside mystery
- an inner-monologue beat driven by partial evidence
- a misunderstanding that may grow or be resolved
- a safe, concrete ending that proves what changed

Run it
------
python storyworlds/worlds/gpt-5.4/companion_swimming_pool_inner_monologue_misunderstanding_mystery.py
python storyworlds/worlds/gpt-5.4/companion_swimming_pool_inner_monologue_misunderstanding_mystery.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/companion_swimming_pool_inner_monologue_misunderstanding_mystery.py --all --qa
python storyworlds/worlds/gpt-5.4/companion_swimming_pool_inner_monologue_misunderstanding_mystery.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/companion_swimming_pool_inner_monologue_misunderstanding_mystery.py --verify
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
CLUE_MIN = 1.0
TRUST_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lifeguard_woman"}
        male = {"boy", "father", "dad", "man", "lifeguard_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "lifeguard_woman": "lifeguard",
            "lifeguard_man": "lifeguard",
        }.get(self.type, self.label or self.type)


@dataclass
class PoolSetting:
    id: str
    place: str
    water: str
    sound: str
    hiding_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    owner_line: str
    clue: str
    found_in: str
    sound: str
    found_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CompanionStyle:
    id: str
    label: str
    comfort_line: str
    search_line: str
    insight_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misread:
    id: str
    wrong_guess: str
    inner_question: str
    worry_line: str
    correction_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Finder:
    id: str
    label: str
    role_type: str
    entrance: str
    explain: str
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


def _r_notice_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["heard_clue"] >= THRESHOLD and hero.meters["clue_count"] < CLUE_MIN:
        sig = ("clue", "heard")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["clue_count"] += 1
            out.append("__clue__")
    if hero.meters["saw_ripple"] >= THRESHOLD and hero.meters["clue_count"] < 2:
        sig = ("clue", "ripple")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["clue_count"] += 1
            out.append("__clue__")
    return out


def _r_misunderstand(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["clue_count"] >= CLUE_MIN and hero.memes["uncertain"] >= THRESHOLD:
        sig = ("misunderstand",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["suspicion"] += 1
            hero.memes["worry"] += 1
            world.facts["misunderstood"] = True
            return ["__misunderstood__"]
    return []


def _r_companion_steady(world: World) -> list[str]:
    hero = world.get("hero")
    companion = world.get("companion")
    if companion.memes["comforting"] >= THRESHOLD:
        sig = ("comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] += 1
            hero.memes["panic"] = 0.0
            return ["__comfort__"]
    return []


def _r_resolution(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["found"] >= THRESHOLD and hero.memes["trust"] >= TRUST_MIN:
        sig = ("resolved",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["worry"] = 0.0
            hero.memes["suspicion"] = 0.0
            hero.memes["understanding"] += 1
            world.facts["resolved"] = True
            return ["__resolved__"]
    return []


CAUSAL_RULES = [
    Rule(name="notice_clue", tag="physical", apply=_r_notice_clue),
    Rule(name="misunderstand", tag="social", apply=_r_misunderstand),
    Rule(name="companion_steady", tag="social", apply=_r_companion_steady),
    Rule(name="resolution", tag="social", apply=_r_resolution),
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
    "indoor": PoolSetting(
        id="indoor",
        place="the indoor swimming pool",
        water="The blue water held the ceiling lights like wiggly coins.",
        sound="Every splash bounced softly off the walls.",
        hiding_spot="the skimmer basket by the shallow-end wall",
        ending_image="The pool no longer felt full of secrets. It just looked bright and friendly again.",
        tags={"pool", "indoor_pool"},
    ),
    "outdoor": PoolSetting(
        id="outdoor",
        place="the outdoor swimming pool",
        water="The water flashed under the sun like moving glass.",
        sound="Small splashes mixed with the rustle of summer leaves.",
        hiding_spot="the drain cover near the warm steps",
        ending_image="The pool no longer felt full of secrets. It sparkled like a place for games again.",
        tags={"pool", "outdoor_pool"},
    ),
}

ITEMS = {
    "goggles": MissingItem(
        id="goggles",
        label="goggles",
        phrase="a pair of green goggles",
        owner_line="Before swim time began, the hero set a pair of green goggles beside a folded towel.",
        clue="a thin green strap sliding in the water",
        found_in="caught under the skimmer lip",
        sound="a tiny tap-tap against the wall",
        found_line="The missing goggles had not been stolen at all. They were only caught under the skimmer lip where the water kept nudging them.",
        tags={"goggles", "pool_gear"},
    ),
    "ring": MissingItem(
        id="ring",
        label="dive ring",
        phrase="a bright orange dive ring",
        owner_line="Before the game started, the hero balanced a bright orange dive ring on the edge of a chair.",
        clue="a round orange flash under the water",
        found_in="resting behind the shallow-end steps",
        sound="a light clink against the steps",
        found_line="The dive ring had not vanished into a secret hiding place. It was resting behind the shallow-end steps where the water had rolled it.",
        tags={"dive_ring", "pool_toy"},
    ),
    "whistle": MissingItem(
        id="whistle",
        label="toy whistle",
        phrase="a little red toy whistle",
        owner_line="Before splashing began, the hero tucked a little red toy whistle near the flip-flops and towel.",
        clue="a brief red blink under the water",
        found_in="nestled in the corner grate",
        sound="a faint tick-tick in the grate",
        found_line="The toy whistle had not been taken by anybody. It was nestled in the corner grate where the moving water had carried it.",
        tags={"toy", "whistle"},
    ),
}

COMPANIONS = {
    "friend": CompanionStyle(
        id="friend",
        label="best friend",
        comfort_line="The companion leaned close and spoke in a small, steady voice.",
        search_line="The companion crouched beside the wet tiles and followed the clue instead of the fear.",
        insight_line="Maybe the water moved it, the companion said, and that simple thought made the mystery feel smaller.",
        tags={"friend", "companion"},
    ),
    "cousin": CompanionStyle(
        id="cousin",
        label="cousin",
        comfort_line="The companion touched the hero's elbow and stayed right there.",
        search_line="The companion peered along the pool edge, careful not to miss a thing.",
        insight_line="Maybe it slipped and drifted, the companion said, and the guess sounded gentle instead of scary.",
        tags={"cousin", "companion"},
    ),
    "sibling": CompanionStyle(
        id="sibling",
        label="older sister",
        comfort_line="The companion wrapped an arm around the hero's shoulders for a moment.",
        search_line="The companion looked where the ripples pointed instead of where the worry pointed.",
        insight_line="Pools move things, the companion said, and the words felt wiser than the hero's first guess.",
        tags={"sibling", "companion"},
    ),
}

MISREADS = {
    "taken": Misread(
        id="taken",
        wrong_guess="someone had taken it",
        inner_question="Had somebody taken it while nobody was looking?",
        worry_line="The thought made the cheerful pool seem full of sneaky corners.",
        correction_line="It only looked like a mystery about a thief because the hero had seen half a clue and guessed the rest.",
        tags={"misunderstanding", "theft_guess"},
    ),
    "sunk_forever": Misread(
        id="sunk_forever",
        wrong_guess="it had sunk forever into a dark crack",
        inner_question="Had it sunk forever into some dark crack under the water?",
        worry_line="The thought made the clear blue water seem deeper and stranger than before.",
        correction_line="It only felt like a forever-lost mystery because the hero had let one worried thought grow bigger than the evidence.",
        tags={"misunderstanding", "loss_guess"},
    ),
    "creature": Misread(
        id="creature",
        wrong_guess="a hidden pool creature had tugged it away",
        inner_question="Had a hidden pool creature tugged it away from the towel?",
        worry_line="The thought made every ripple look like a secret moving under the surface.",
        correction_line="It only seemed like a creature mystery because the hero's imagination ran ahead of the small, ordinary clues.",
        tags={"misunderstanding", "imagined_creature"},
    ),
}

FINDERS = {
    "lifeguard": Finder(
        id="lifeguard",
        label="lifeguard",
        role_type="lifeguard_woman",
        entrance="Just then the lifeguard walked over, calm and dry, with a long pool hook in one hand.",
        explain="The lifeguard had noticed the little sound by the wall and knew where floating things often drifted.",
        tags={"lifeguard", "helper"},
    ),
    "parent": Finder(
        id="parent",
        label="mom",
        role_type="mother",
        entrance="Just then the hero's mom came back from the bench with careful, quick steps.",
        explain="Mom had seen the clue sliding along the edge and knew the water sometimes carried small things to the same spots.",
        tags={"parent", "helper"},
    ),
    "coach": Finder(
        id="coach",
        label="coach",
        role_type="woman",
        entrance="Just then the swim coach came over with a towel over one shoulder and kind eyes.",
        explain="The coach had heard the tiny sound near the steps and knew toys and gear often drifted there.",
        tags={"coach", "helper"},
    ),
}


def hazard_free(item: MissingItem, setting: PoolSetting) -> bool:
    return bool(item.id and setting.id)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for misread_id in MISREADS:
                for finder_id in FINDERS:
                    if hazard_free(item, setting):
                        combos.append((setting_id, item_id, misread_id, finder_id))
    return combos


def predict_guess(item: MissingItem, misread: Misread) -> dict:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type="girl", role="hero"))
    w.add(Entity(id="item", kind="thing", type="item", label=item.label))
    hero.meters["heard_clue"] += 1
    hero.memes["uncertain"] += 1
    propagate(w, narrate=False)
    return {
        "misunderstood": bool(w.facts.get("misunderstood")),
        "guess": misread.wrong_guess,
    }


def introduce(world: World, setting: PoolSetting, hero: Entity, companion: Entity, item: MissingItem) -> None:
    hero.memes["joy"] += 1
    companion.memes["bond"] += 1
    world.say(
        f"On a bright afternoon at {setting.place}, {hero.id} and {companion.id}, {hero.pronoun('possessive')} {companion.attrs.get('relation_word', 'companion')}, padded across the wet tiles."
    )
    world.say(setting.water)
    world.say(setting.sound)
    world.say(item.owner_line)


def vanish(world: World, hero: Entity, item: Entity, item_cfg: MissingItem) -> None:
    item.meters["misplaced"] += 1
    hero.memes["uncertain"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"But when {hero.id} reached back for the {item_cfg.label}, it was gone. Only a damp outline was left beside the towel."
    )


def notice_clue(world: World, hero: Entity, item_cfg: MissingItem) -> None:
    hero.meters["heard_clue"] += 1
    hero.meters["saw_ripple"] += 1
    world.say(
        f"From the water came {item_cfg.sound}, and {hero.id} caught sight of {item_cfg.clue} for just a blink."
    )
    propagate(world, narrate=False)


def inner_monologue(world: World, hero: Entity, misread: Misread) -> None:
    hero.memes["inner_voice"] += 1
    world.say(
        f"{hero.id} did not say the first thought out loud. Inside, {hero.pronoun()} wondered, {misread.inner_question}"
    )
    world.say(misread.worry_line)


def speak_worry(world: World, hero: Entity, companion: Entity, misread: Misread) -> None:
    world.say(
        f'"I think {misread.wrong_guess}," {hero.id} whispered to {companion.id}.'
    )


def companion_response(world: World, companion: Entity, style: CompanionStyle) -> None:
    companion.memes["comforting"] += 1
    world.say(style.comfort_line)
    world.say(style.insight_line)
    world.say(style.search_line)
    propagate(world, narrate=False)


def finder_arrives(world: World, finder: Entity, finder_cfg: Finder, setting: PoolSetting, item_cfg: MissingItem) -> None:
    world.say(finder_cfg.entrance)
    world.say(
        f"{finder_cfg.explain} {finder.pronoun().capitalize()} looked toward {setting.hiding_spot}."
    )


def recover_item(world: World, hero: Entity, item: Entity, finder: Entity, item_cfg: MissingItem) -> None:
    item.meters["found"] += 1
    world.say(
        f"A moment later, {finder.label_word} pointed and reached. There, {item_cfg.found_in}, was the missing {item_cfg.label}."
    )
    world.say(item_cfg.found_line)
    propagate(world, narrate=False)


def explain_truth(world: World, hero: Entity, companion: Entity, misread: Misread, setting: PoolSetting) -> None:
    world.say(
        f"{misread.correction_line} {companion.id} smiled when {hero.id} let out a long breath."
    )
    world.say(
        f'"So the pool was making clues, not keeping secrets," {hero.id} said.'
    )
    world.say(setting.ending_image)


def closing_image(world: World, hero: Entity, companion: Entity, item_cfg: MissingItem) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"Soon the two companions were back at the edge together, and the {item_cfg.label} no longer felt like part of a mystery. It felt like part of the game again."
    )


def tell(
    setting: PoolSetting,
    item_cfg: MissingItem,
    companion_cfg: CompanionStyle,
    misread: Misread,
    finder_cfg: Finder,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    companion_name: str = "Tess",
    companion_type: str = "girl",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    hero.id = hero_name
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type=companion_type,
            label=companion_name,
            role="companion",
            attrs={"relation_word": companion_cfg.label},
        )
    )
    companion.id = companion_name
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase))
    finder = world.add(
        Entity(
            id="finder",
            kind="character",
            type=finder_cfg.role_type,
            label=finder_cfg.label,
            role="finder",
        )
    )

    introduce(world, setting, hero, companion, item_cfg)
    world.para()
    vanish(world, hero, item, item_cfg)
    notice_clue(world, hero, item_cfg)
    inner_monologue(world, hero, misread)
    speak_worry(world, hero, companion, misread)
    world.para()
    companion_response(world, companion, companion_cfg)
    finder_arrives(world, finder, finder_cfg, setting, item_cfg)
    recover_item(world, hero, item, finder, item_cfg)
    world.para()
    explain_truth(world, hero, companion, misread, setting)
    closing_image(world, hero, companion, item_cfg)

    world.facts.update(
        hero=hero,
        companion=companion,
        item=item,
        item_cfg=item_cfg,
        setting=setting,
        companion_cfg=companion_cfg,
        misread=misread,
        finder=finder,
        finder_cfg=finder_cfg,
        misunderstood=bool(world.facts.get("misunderstood")),
        resolved=bool(world.facts.get("resolved")),
    )
    return world


@dataclass
class StoryParams:
    setting: str
    item: str
    companion_style: str
    misread: str
    finder: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Noah", "Eli", "Theo", "Sam"]

CURATED = [
    StoryParams(
        setting="indoor",
        item="goggles",
        companion_style="friend",
        misread="taken",
        finder="lifeguard",
        hero_name="Mina",
        hero_type="girl",
        companion_name="Tess",
        companion_type="girl",
    ),
    StoryParams(
        setting="outdoor",
        item="ring",
        companion_style="cousin",
        misread="creature",
        finder="parent",
        hero_name="Ben",
        hero_type="boy",
        companion_name="Nora",
        companion_type="girl",
    ),
    StoryParams(
        setting="indoor",
        item="whistle",
        companion_style="sibling",
        misread="sunk_forever",
        finder="coach",
        hero_name="Lucy",
        hero_type="girl",
        companion_name="Maya",
        companion_type="girl",
    ),
]


KNOWLEDGE = {
    "pool": [
        (
            "Why do small things drift in a swimming pool?",
            "Moving water can gently push light objects along the edge or toward a grate. That is why pool toys or gear can end up in the same corners again and again."
        )
    ],
    "goggles": [
        (
            "What are goggles for at the pool?",
            "Goggles help protect your eyes from splashes and pool water. They also help you see more clearly underwater."
        )
    ],
    "dive_ring": [
        (
            "What is a dive ring?",
            "A dive ring is a pool toy shaped like a ring that children can toss and fetch in the water. It is made for games, not for wearing."
        )
    ],
    "lifeguard": [
        (
            "What does a lifeguard do?",
            "A lifeguard watches the pool to help keep everyone safe. Lifeguards also notice problems quickly and help when something goes wrong."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses the wrong meaning of what they saw or heard. It can feel very real until the missing piece is found."
        )
    ],
    "helper": [
        (
            "Why is it good to ask a grown-up for help when something is missing?",
            "A grown-up can stay calm and look carefully at the clues. Calm thinking often solves a mystery faster than worried guessing."
        )
    ],
    "companion": [
        (
            "What is a companion?",
            "A companion is someone who stays with you and shares what you are doing. A good companion can make a scary moment feel smaller."
        )
    ],
    "pool_toy": [
        (
            "Why can pool toys be hard to spot in the water?",
            "Water bends light and keeps moving, so toys can look wavy or hidden for a moment. That can make them seem lost even when they are nearby."
        )
    ],
    "pool_gear": [
        (
            "Why can clues look strange in water?",
            "Ripples and reflections change how things look. A small object can flash, wobble, or disappear from sight for a second."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "companion",
    "pool",
    "goggles",
    "dive_ring",
    "pool_toy",
    "pool_gear",
    "misunderstanding",
    "lifeguard",
    "helper",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    item = f["item_cfg"]
    setting = f["setting"]
    misread = f["misread"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old set at {setting.place} that includes the word "companion".',
        f"Tell a gentle poolside mystery where {hero.id} loses {item.phrase}, has a worried inner monologue, and first thinks {misread.wrong_guess}.",
        f"Write a story where {companion.id}, a steady companion, helps {hero.id} solve a misunderstanding at the swimming pool and ends with relief instead of fear.",
    ]


def pair_phrase(hero: Entity, companion: Entity) -> str:
    return f"{hero.id} and {companion.id}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    item_cfg = f["item_cfg"]
    misread = f["misread"]
    finder = f["finder"]
    setting = f["setting"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_phrase(hero, companion)} at {setting.place}. {companion.id} is {hero.id}'s {companion.attrs.get('relation_word', 'companion')} and stays close when the mystery begins."
        ),
        (
            f"What went missing?",
            f"The missing thing was {item_cfg.phrase}. It disappeared from beside the towel and started the whole mystery."
        ),
        (
            f"What did {hero.id} think had happened at first?",
            f"{hero.id} first thought {misread.wrong_guess}. That was the misunderstanding, because {hero.pronoun()} only had a small clue and not the whole truth."
        ),
        (
            f"How do we know the story includes inner monologue?",
            f"The story tells us what {hero.id} wondered silently inside {hero.pronoun('possessive')} head. That private worried question is the inner monologue part."
        ),
        (
            f"How did {companion.id} help?",
            f"{companion.id} stayed calm and helped look at the clues instead of feeding the fear. That steadiness helped {hero.id} slow down and think more carefully."
        ),
        (
            f"How was the mystery solved?",
            f"{finder.label_word.capitalize()} found the {item_cfg.label} after noticing where small things drift at the pool. The answer came from following the clue, not from the first worried guess."
        ),
        (
            "How did the story end?",
            f"It ended gently, with the misunderstanding cleared up and the pool feeling friendly again. The lost {item_cfg.label} became part of play instead of part of a scary mystery."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["item_cfg"].tags) | set(f["companion_cfg"].tags) | set(f["misread"].tags) | set(f["finder_cfg"].tags)
    tags.add("misunderstanding")
    tags.add("helper")
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: str, item: str, misread: str, finder: str) -> str:
    return (
        f"(No story: the combination setting={setting}, item={item}, misread={misread}, finder={finder} is not in the valid pool-mystery set.)"
    )


ASP_RULES = r"""
valid(S, I, M, F) :- setting(S), item(I), misread(M), finder(F).

clue_seen.
uncertain.

misunderstood :- clue_seen, uncertain.
resolved :- misunderstood, comforted, found.

#show valid/4.
#show misunderstood/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in ITEMS:
        lines.append(asp.fact("item", key))
    for key in MISREADS:
        lines.append(asp.fact("misread", key))
    for key in FINDERS:
        lines.append(asp.fact("finder", key))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_state() -> tuple[bool, bool]:
    import asp
    model = asp.one_model(asp_program("comforted.\nfound.\n", "#show misunderstood/0.\n#show resolved/0."))
    misunderstood = bool(asp.atoms(model, "misunderstood"))
    resolved = bool(asp.atoms(model, "resolved"))
    return misunderstood, resolved


def outcome_flags(world: World) -> tuple[bool, bool]:
    return bool(world.facts.get("misunderstood")), bool(world.facts.get("resolved"))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    asp_mis, asp_res = asp_story_state()
    sample = generate(CURATED[0])
    py_mis, py_res = outcome_flags(sample.world)
    if (asp_mis, asp_res) == (py_mis, py_res):
        print("OK: ASP state agrees with Python misunderstanding/resolution flags.")
    else:
        rc = 1
        print(f"MISMATCH in state flags: asp={(asp_mis, asp_res)} python={(py_mis, py_res)}")

    try:
        smoke = generate(resolve_params(build_parser().parse_args([]), random.Random(123)))
        if not smoke.story.strip():
            raise StoryError("Generated empty story.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a swimming-pool mystery with a companion, inner monologue, and misunderstanding."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--companion-style", choices=COMPANIONS, dest="companion_style")
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--finder", choices=FINDERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.misread is None or combo[2] == args.misread)
        and (args.finder is None or combo[3] == args.finder)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.setting or "*",
                args.item or "*",
                args.misread or "*",
                args.finder or "*",
            )
        )

    setting_id, item_id, misread_id, finder_id = rng.choice(sorted(combos))
    companion_style = args.companion_style or rng.choice(sorted(COMPANIONS.keys()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_type)
    companion_name = args.companion_name or pick_name(rng, companion_type, avoid=hero_name)

    return StoryParams(
        setting=setting_id,
        item=item_id,
        companion_style=companion_style,
        misread=misread_id,
        finder=finder_id,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.companion_style not in COMPANIONS:
        raise StoryError(f"(Invalid companion style: {params.companion_style})")
    if params.misread not in MISREADS:
        raise StoryError(f"(Invalid misread: {params.misread})")
    if params.finder not in FINDERS:
        raise StoryError(f"(Invalid finder: {params.finder})")

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        companion_cfg=COMPANIONS[params.companion_style],
        misread=MISREADS[params.misread],
        finder_cfg=FINDERS[params.finder],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        companion_name=params.companion_name,
        companion_type=params.companion_type,
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
        print(asp_program("", "#show valid/4.\n#show misunderstood/0.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, misread, finder) combos:\n")
        for setting_id, item_id, misread_id, finder_id in combos:
            print(f"  {setting_id:8} {item_id:8} {misread_id:12} {finder_id}")
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
            header = f"### {p.hero_name} at the pool: {p.item}, {p.misread}, {p.finder}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
