#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/birth_quest_happy_ending_transformation_mystery.py
==============================================================================

A small storyworld about a child solving a gentle mystery on the morning of a
new baby's birth. A strange sealed bundle appears with a clue. The child follows
a little quest, discovers the right gentle method, and watches the bundle
transform into a welcome gift for the baby.

The domain is constrained on purpose: each mystery bundle has exactly one
reasonable reveal method. The child-facing tension comes from not knowing what
the bundle is or how to open it, not from danger. The ending is always happy,
with a physical transformation and an emotional change in the seeker: from
worried and left out to proud and included.
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
# from its nested directory: storyworlds/worlds/gpt-5.4/<file>.py
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
        female = {"girl", "mother", "grandmother", "woman", "baby_girl"}
        male = {"boy", "father", "grandfather", "man", "baby_boy"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    hiding_spot: str
    path_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    shell_word: str
    clue_mark: str
    accepts: str
    transform_text: str
    gift_label: str
    gift_phrase: str
    finish_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action_text: str
    clue_text: str
    reveal_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    kind: str
    entry_text: str
    follow_text: str
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


def _r_reveal(world: World) -> list[str]:
    vessel = world.get("vessel")
    gift = world.get("gift")
    seeker = world.get("seeker")
    if vessel.meters["activated"] < THRESHOLD:
        return []
    if vessel.meters["opened"] >= THRESHOLD:
        return []
    sig = ("reveal", vessel.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    vessel.meters["opened"] += 1
    vessel.meters["sealed"] = 0.0
    vessel.meters["mystery"] = 0.0
    gift.meters["revealed"] += 1
    gift.meters["shine"] += 1
    seeker.memes["wonder"] += 1
    seeker.memes["relief"] += 1
    return []


def _r_change(world: World) -> list[str]:
    gift = world.get("gift")
    seeker = world.get("seeker")
    if gift.meters["revealed"] < THRESHOLD:
        return []
    sig = ("change", seeker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["left_out"] = 0.0
    seeker.memes["pride"] += 1
    seeker.memes["belonging"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="reveal", tag="physical", apply=_r_reveal),
    Rule(name="change", tag="emotional", apply=_r_change),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reveal_matches(vessel: Vessel, method: Method) -> bool:
    return vessel.accepts == method.id


def predict_reveal(world: World, method: Method) -> dict:
    sim = world.copy()
    vessel_cfg = sim.facts["vessel_cfg"]
    if reveal_matches(vessel_cfg, method):
        sim.get("vessel").meters["activated"] += 1
        propagate(sim, narrate=False)
    return {
        "opens": sim.get("vessel").meters["opened"] >= THRESHOLD,
        "gift_revealed": sim.get("gift").meters["revealed"] >= THRESHOLD,
    }


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        hiding_spot="under the old rose bench",
        path_text="past the mint patch and the little stone birdbath",
        ending_image="Outside, the roses looked less secret now and more like they were smiling too.",
        tags={"garden"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the greenhouse",
        hiding_spot="behind a row of sleepy tomato pots",
        path_text="between warm glass walls and trays of seedlings",
        ending_image="The glass panes held the last gold of morning, and every leaf seemed to glow back.",
        tags={"greenhouse"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        hiding_spot="inside the wicker chest by the swing",
        path_text="past the rain boots and the creaky white railing",
        ending_image="The porch boards creaked softly, and even the swing looked ready to rock in a slower, gentler way.",
        tags={"porch"},
    ),
}

VESSELS = {
    "dew_pod": Vessel(
        id="dew_pod",
        label="dew pod",
        phrase="a pale green pod tied with silver thread",
        shell_word="pod",
        clue_mark="a tiny sun painted on the thread",
        accepts="sunshine",
        transform_text="The pod loosened, stretched, and opened like a sleepy flower.",
        gift_label="welcome blossom chain",
        gift_phrase="a chain of soft cloth blossoms",
        finish_text="It was the kind of gift that could hang near a cradle and dance when the air moved.",
        tags={"pod", "flower", "sun"},
    ),
    "clay_egg": Vessel(
        id="clay_egg",
        label="clay egg",
        phrase="a smooth brown egg made of soft clay",
        shell_word="egg",
        clue_mark="a tiny blue drop pressed into the side",
        accepts="warm_water",
        transform_text="The clay shell softened, thinned, and melted away in swirls.",
        gift_label="star rattle",
        gift_phrase="a little star-shaped rattle",
        finish_text="When it moved, it made the gentlest silver chime, as if it knew a new baby should hear soft sounds first.",
        tags={"egg", "water", "rattle"},
    ),
    "paper_chrysalis": Vessel(
        id="paper_chrysalis",
        label="paper chrysalis",
        phrase="a folded paper chrysalis wrapped with a satin bow",
        shell_word="chrysalis",
        clue_mark="a neat knot with a tiny arrow tucked under it",
        accepts="untie_ribbon",
        transform_text="The folds slipped free, spread wide, and turned themselves inside out.",
        gift_label="butterfly mobile",
        gift_phrase="a mobile of paper butterflies",
        finish_text="The butterflies spun on bright threads, and each one was painted a different happy color.",
        tags={"paper", "butterfly", "ribbon"},
    ),
}

METHODS = {
    "sunshine": Method(
        id="sunshine",
        label="sunshine",
        action_text="carried the little mystery into a warm patch of sunlight on the floor",
        clue_text="A bright beam lay across the boards like a golden finger pointing the way.",
        reveal_text="As the light touched it, the shell changed.",
        tags={"sun", "light"},
    ),
    "warm_water": Method(
        id="warm_water",
        label="warm water",
        action_text="set the mystery in a shallow bowl of warm water",
        clue_text="Near the sink, a waiting bowl shone with a little curl of steam above it.",
        reveal_text="The warm water kissed the shell, and the shell changed.",
        tags={"water"},
    ),
    "untie_ribbon": Method(
        id="untie_ribbon",
        label="untie the ribbon",
        action_text="sat very still and loosened the bow one careful loop at a time",
        clue_text="On the table lay a card that said, GENTLE HANDS OPEN GENTLE THINGS.",
        reveal_text="When the knot gave a tiny sigh, the shape changed.",
        tags={"ribbon", "gentle"},
    ),
}

GUIDES = {
    "robin": Guide(
        id="robin",
        label="robin",
        kind="bird",
        entry_text="A robin on the railing tipped its head as if it knew more than it was saying.",
        follow_text="The robin fluttered ahead in short, secret jumps, pausing each time the child almost chose the wrong direction.",
        tags={"bird"},
    ),
    "cat": Guide(
        id="cat",
        label="cat",
        kind="animal",
        entry_text="The house cat slipped by with its tail up, looking much too pleased with itself.",
        follow_text="The cat padded ahead and glanced back, as if to ask whether a proper detective was still following.",
        tags={"cat"},
    ),
    "grandma": Guide(
        id="grandma",
        label="grandma",
        kind="person",
        entry_text="Grandma was already awake, smiling in the quiet way grown-ups do after a long, important night.",
        follow_text="Grandma did not give the answer away. She only walked beside the child and nodded toward each clue.",
        tags={"grandma"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for vessel_id, vessel in VESSELS.items():
            for method_id, method in METHODS.items():
                if reveal_matches(vessel, method):
                    combos.append((setting_id, vessel_id, method_id))
    return combos


def explain_rejection(vessel: Vessel, method: Method) -> str:
    return (
        f"(No story: {vessel.phrase} is not the kind of mystery opened by {method.label}. "
        f"This world only allows gentle reveals that fit the clue on the bundle.)"
    )


@dataclass
class StoryParams:
    setting: str
    vessel: str
    method: str
    guide: str
    seeker: str
    seeker_gender: str
    baby_name: str
    baby_gender: str
    elder: str
    trait: str
    relation: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lina", "Mia", "Nora", "Ivy", "June", "Ella", "Ruby", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Finn", "Leo", "Jude", "Sam", "Theo"]
BABY_NAMES = ["Pip", "Wren", "Toby", "Maisie", "Nell", "Kit", "Lulu", "Beau"]
TRAITS = ["careful", "curious", "gentle", "bright-eyed", "patient", "thoughtful"]
RELATIONS = ["sister", "brother", "cousin"]

CURATED = [
    StoryParams(
        setting="garden",
        vessel="dew_pod",
        method="sunshine",
        guide="robin",
        seeker="Lina",
        seeker_gender="girl",
        baby_name="Pip",
        baby_gender="baby_boy",
        elder="mother",
        trait="curious",
        relation="sister",
    ),
    StoryParams(
        setting="greenhouse",
        vessel="clay_egg",
        method="warm_water",
        guide="grandma",
        seeker="Owen",
        seeker_gender="boy",
        baby_name="Maisie",
        baby_gender="baby_girl",
        elder="father",
        trait="thoughtful",
        relation="brother",
    ),
    StoryParams(
        setting="porch",
        vessel="paper_chrysalis",
        method="untie_ribbon",
        guide="cat",
        seeker="Ruby",
        seeker_gender="girl",
        baby_name="Kit",
        baby_gender="baby_boy",
        elder="mother",
        trait="gentle",
        relation="cousin",
    ),
]


def introduce(world: World, seeker: Entity, elder: Entity, baby: Entity) -> None:
    seeker.memes["curiosity"] += 1
    seeker.memes["left_out"] += 1
    world.say(
        f"On the morning of {baby.id}'s birth, {seeker.id} woke before the house was fully bright."
    )
    world.say(
        f"The rooms were hushed and warm, and {seeker.id}'s {elder.label_word} moved about in soft steps, smiling the tired smile of someone guarding a happy secret."
    )
    world.say(
        f"{seeker.id} was a {seeker.attrs.get('trait', 'curious')} {seeker.type} who loved puzzles, but this new quiet felt bigger than an ordinary puzzle."
    )


def find_first_clue(world: World, seeker: Entity, baby: Entity, vessel: Vessel) -> None:
    world.say(
        f"Beside {baby.id}'s cradle lay a card that said, For the one who welcomes a new life, follow the first clue."
    )
    world.say(
        f"Under the card was {vessel.phrase}. It felt light in {seeker.pronoun('possessive')} hands, and on it was {vessel.clue_mark}."
    )
    world.get("vessel").meters["sealed"] += 1
    world.get("vessel").meters["mystery"] += 1
    seeker.memes["wonder"] += 1


def introduce_guide(world: World, guide: Guide) -> None:
    world.say(guide.entry_text)


def quest_walk(world: World, seeker: Entity, guide: Guide, setting: Setting) -> None:
    seeker.memes["determination"] += 1
    world.say(
        f"So the quest began in {setting.place}, {setting.path_text}."
    )
    world.say(guide.follow_text)
    world.get("seeker").meters["steps"] += 1
    world.get("vessel").meters["carried"] += 1


def worry_and_hint(world: World, seeker: Entity, elder: Entity, method: Method) -> None:
    seeker.memes["worry"] += 1
    world.say(
        f'For a moment, {seeker.id} wondered if the mystery had been left for someone bigger. "{elder.label_word.capitalize()}, what if I do it wrong?" {seeker.pronoun()} whispered.'
    )
    world.say(
        f'{elder.label_word.capitalize()} crouched close and answered, "Real welcome gifts are gentle. Look at the clue, and it will tell you what kindness to use."'
    )
    world.say(method.clue_text)


def reveal(world: World, seeker: Entity, vessel_cfg: Vessel, method: Method) -> None:
    vessel = world.get("vessel")
    gift = world.get("gift")
    pred = predict_reveal(world, method)
    world.facts["predicted_open"] = pred["opens"]
    if not pred["opens"]:
        raise StoryError(explain_rejection(vessel_cfg, method))
    world.say(
        f"{seeker.id} {method.action_text}. {method.reveal_text}"
    )
    vessel.meters["activated"] += 1
    propagate(world, narrate=False)
    world.say(vessel_cfg.transform_text)
    world.say(
        f"Inside was {vessel_cfg.gift_phrase}. {vessel_cfg.finish_text}"
    )
    world.facts["transformed"] = gift.meters["revealed"] >= THRESHOLD


def return_to_baby(world: World, seeker: Entity, baby: Entity, elder: Entity, vessel_cfg: Vessel) -> None:
    seeker.memes["love"] += 1
    world.say(
        f"{seeker.id} carried the {vessel_cfg.gift_label} back inside as carefully as if carrying a secret star."
    )
    world.say(
        f"When {baby.id} made a tiny sleepy sound, {seeker.id}'s heart changed shape inside {seeker.pronoun('object')}. The mystery was not about being left out after the birth at all."
    )
    world.say(
        f"It was about helping welcome {baby.id}."
    )
    world.say(
        f'{elder.label_word.capitalize()} helped hang the gift near the cradle, and everyone stood still for one happy breath while it moved softly in the air.'
    )


def ending(world: World, seeker: Entity, baby: Entity, setting: Setting, vessel_cfg: Vessel) -> None:
    world.say(
        f"{baby.id}'s eyes blinked open for a moment, following the {vessel_cfg.gift_label}, and {seeker.id} smiled like a real keeper of small wonders."
    )
    world.say(setting.ending_image)


def tell(
    setting: Setting,
    vessel_cfg: Vessel,
    method: Method,
    guide_cfg: Guide,
    seeker_name: str,
    seeker_gender: str,
    baby_name: str,
    baby_gender: str,
    elder_type: str,
    trait: str,
    relation: str,
) -> World:
    world = World(setting=setting)
    seeker = world.add(
        Entity(
            id=seeker_name,
            kind="character",
            type=seeker_gender,
            role="seeker",
            attrs={"trait": trait, "relation": relation},
        )
    )
    baby = world.add(
        Entity(
            id=baby_name,
            kind="character",
            type=baby_gender,
            role="baby",
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    world.add(
        Entity(
            id="guide",
            kind="character" if guide_cfg.kind == "person" else "thing",
            type=guide_cfg.kind,
            role="guide",
            label=guide_cfg.label,
            tags=set(guide_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="vessel",
            type="bundle",
            label=vessel_cfg.label,
            phrase=vessel_cfg.phrase,
            tags=set(vessel_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="gift",
            type="gift",
            label=vessel_cfg.gift_label,
            phrase=vessel_cfg.gift_phrase,
            tags=set(vessel_cfg.tags),
        )
    )

    world.facts.update(
        setting_cfg=setting,
        vessel_cfg=vessel_cfg,
        method_cfg=method,
        guide_cfg=guide_cfg,
        seeker=seeker,
        baby=baby,
        elder=elder,
        relation=relation,
    )

    introduce(world, seeker, elder, baby)
    world.para()
    find_first_clue(world, seeker, baby, vessel_cfg)
    introduce_guide(world, guide_cfg)
    quest_walk(world, seeker, guide_cfg, setting)
    world.para()
    worry_and_hint(world, seeker, elder, method)
    reveal(world, seeker, vessel_cfg, method)
    world.para()
    return_to_baby(world, seeker, baby, elder, vessel_cfg)
    ending(world, seeker, baby, setting, vessel_cfg)

    world.facts.update(
        solved=world.get("gift").meters["revealed"] >= THRESHOLD,
        happy=seeker.memes["pride"] >= THRESHOLD and seeker.memes["belonging"] >= THRESHOLD,
        vessel_opened=world.get("vessel").meters["opened"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "birth": [
        (
            "What does birth mean?",
            "Birth is when a baby comes into the world. It is the beginning of a new life.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet, so you look for clues to solve it.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. You keep going step by step until you find what you are looking for.",
        )
    ],
    "sun": [
        (
            "What can sunshine do to a plant bud?",
            "Sunshine gives warmth and light. Some buds open wider in warmth and light.",
        )
    ],
    "water": [
        (
            "Why does warm water soften some things?",
            "Warm water can make dry or soft materials loosen. That can help them open gently.",
        )
    ],
    "ribbon": [
        (
            "Why do you untie a ribbon instead of pulling hard?",
            "A ribbon is meant to be loosened gently. Pulling hard can crumple what it is holding together.",
        )
    ],
    "butterfly": [
        (
            "Why do butterflies remind people of change?",
            "Butterflies begin in one form and later look very different. That makes them a good sign for transformation.",
        )
    ],
    "rattle": [
        (
            "What is a baby rattle?",
            "A baby rattle is a small toy that makes a soft sound when it moves. Grown-ups choose ones that are safe for babies.",
        )
    ],
    "flower": [
        (
            "What happens when a flower bud opens?",
            "The petals unfold and spread out. A tight bud changes into a flower you can see clearly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["birth", "mystery", "quest", "sun", "water", "ribbon", "butterfly", "rattle", "flower"]


def generation_prompts(world: World) -> list[str]:
    seeker = world.facts["seeker"]
    baby = world.facts["baby"]
    vessel_cfg = world.facts["vessel_cfg"]
    method_cfg = world.facts["method_cfg"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "birth" and follows a child on a quest.',
        f"Tell a happy mystery where {seeker.id} solves a clue left on the morning of {baby.id}'s birth and discovers how to open {vessel_cfg.phrase}.",
        f"Write a transformation story where a small hidden object changes when a child uses {method_cfg.label} kindly, and the ending shows the child feeling included at last.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    seeker = world.facts["seeker"]
    baby = world.facts["baby"]
    elder = world.facts["elder"]
    vessel_cfg = world.facts["vessel_cfg"]
    method_cfg = world.facts["method_cfg"]
    guide_cfg = world.facts["guide_cfg"]
    setting = world.facts["setting_cfg"]
    relation = world.facts["relation"]
    elder_word = elder.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id}, a child welcoming {relation} {baby.id} on the morning of the baby's birth. It is also about the gentle guide through the mystery and {seeker.id}'s {elder_word}, who helps without giving the answer away.",
        ),
        (
            "What was the mystery at the start?",
            f"The mystery was {vessel_cfg.phrase} left beside {baby.id}'s cradle with a clue on it. {seeker.id} did not know what it held or how it was meant to open.",
        ),
        (
            f"Why did {seeker.id} go on a quest?",
            f"{seeker.id} wanted to solve the clue and welcome the new baby properly. The quest gave {seeker.pronoun('object')} a way to join the happy day instead of standing at the edge of it.",
        ),
        (
            f"How did the guide help {seeker.id}?",
            f"The {guide_cfg.label} did not solve the mystery directly. It helped {seeker.id} keep moving toward the next clue in {setting.place}.",
        ),
        (
            f"What clue showed {seeker.id} what to do?",
            f"The clue pointed to {method_cfg.label}. {seeker.id} listened to the clue because the gift had to be treated gently, not forced open.",
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            (
                f"What transformation happened?",
                f"The sealed {vessel_cfg.shell_word} changed and opened, and inside was {vessel_cfg.gift_phrase}. The transformation solved the mystery and turned a plain little bundle into a welcome gift.",
            )
        )
        qa.append(
            (
                f"How did {seeker.id} change by the end?",
                f"At first {seeker.id} felt unsure and a little left out after the birth. By the end, {seeker.pronoun()} felt proud and included because {seeker.pronoun()} had helped welcome {baby.id}.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the gift hanging near the cradle and everyone quietly admiring it. The ending image shows that the mystery is over and the family has made room for both the new baby and {seeker.id}'s kindness.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"birth", "mystery", "quest"}
    vessel_cfg = world.facts["vessel_cfg"]
    method_cfg = world.facts["method_cfg"]
    tags |= set(vessel_cfg.tags)
    tags |= set(method_cfg.tags)
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
matches(V, M) :- accepts(V, M).
valid(S, V, M) :- setting(S), vessel(V), method(M), matches(V, M).

opened :- chosen_vessel(V), chosen_method(M), matches(V, M).
solved :- opened.
happy  :- solved.

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("accepts", vid, vessel.accepts))
    for mid in METHODS:
        lines.append(asp.fact("method", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> tuple[bool, bool]:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_vessel", params.vessel),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show opened/0.\n#show happy/0."))
    opened = bool(asp.atoms(model, "opened"))
    happy = bool(asp.atoms(model, "happy"))
    return opened, happy


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a birth-day mystery quest with a gentle transformation and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--elder", choices=["mother", "father", "grandmother"])
    ap.add_argument("--seeker")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel and args.method:
        vessel = VESSELS[args.vessel]
        method = METHODS[args.method]
        if not reveal_matches(vessel, method):
            raise StoryError(explain_rejection(vessel, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, vessel_id, method_id = rng.choice(sorted(combos))
    guide = args.guide or rng.choice(sorted(GUIDES))
    seeker_gender = args.gender or rng.choice(["girl", "boy"])
    seeker = args.seeker or rng.choice(GIRL_NAMES if seeker_gender == "girl" else BOY_NAMES)
    baby_gender = rng.choice(["baby_girl", "baby_boy"])
    baby_name = rng.choice([n for n in BABY_NAMES if n != seeker])
    elder = args.elder or rng.choice(["mother", "father", "grandmother"])
    trait = rng.choice(TRAITS)
    relation = "sister" if seeker_gender == "girl" else "brother"
    if elder == "grandmother":
        relation = "cousin" if rng.random() < 0.5 else relation
    return StoryParams(
        setting=setting_id,
        vessel=vessel_id,
        method=method_id,
        guide=guide,
        seeker=seeker,
        seeker_gender=seeker_gender,
        baby_name=baby_name,
        baby_gender=baby_gender,
        elder=elder,
        trait=trait,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.elder not in {"mother", "father", "grandmother"}:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if not reveal_matches(VESSELS[params.vessel], METHODS[params.method]):
        raise StoryError(explain_rejection(VESSELS[params.vessel], METHODS[params.method]))

    world = tell(
        setting=SETTINGS[params.setting],
        vessel_cfg=VESSELS[params.vessel],
        method=METHODS[params.method],
        guide_cfg=GUIDES[params.guide],
        seeker_name=params.seeker,
        seeker_gender=params.seeker_gender,
        baby_name=params.baby_name,
        baby_gender=params.baby_gender,
        elder_type=params.elder,
        trait=params.trait,
        relation=params.relation,
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

    for params in CURATED:
        opened, happy = asp_outcome(params)
        expected = reveal_matches(VESSELS[params.vessel], METHODS[params.method])
        if opened != expected or happy != expected:
            rc = 1
            print(
                "MISMATCH in outcome:",
                params,
                "asp=",
                (opened, happy),
                "python=",
                (expected, expected),
            )
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show opened/0.\n#show happy/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, vessel, method) combos:\n")
        for setting_id, vessel_id, method_id in combos:
            print(f"  {setting_id:10} {vessel_id:16} {method_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker}: {p.vessel} in {p.setting} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
