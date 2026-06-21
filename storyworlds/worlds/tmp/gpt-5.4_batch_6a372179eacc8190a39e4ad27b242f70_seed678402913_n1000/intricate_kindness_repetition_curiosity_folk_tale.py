#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/intricate_kindness_repetition_curiosity_folk_tale.py
================================================================================

A standalone story world for a gentle folk-tale pattern: a curious child notices
an intricate trail, follows it, repeats a small act of kindness three times, and
finds that kindness returned at the end.

The simulation is intentionally small and constraint-checked:

* A child carries a gift bundle with a fixed number of shareable pieces.
* Along the path, the child meets three hungry helpers of the same kind.
* Sharing the right gift lowers hunger and raises trust.
* After the third kind act, the hidden wonder is revealed.
* The ending image shows the wonder and the elder's lesson that kindness comes back.

Reasonableness gate:
* A valid story needs a helper/gift pair that actually fits.
* The bundle must have at least three pieces, because the tale repeats the act
  of kindness three times.
* A setting must plausibly contain the chosen hidden wonder.

Run it
------
    python storyworlds/worlds/gpt-5.4/intricate_kindness_repetition_curiosity_folk_tale.py
    python storyworlds/worlds/gpt-5.4/intricate_kindness_repetition_curiosity_folk_tale.py --helper sparrows --gift seeds
    python storyworlds/worlds/gpt-5.4/intricate_kindness_repetition_curiosity_folk_tale.py --gift ribbon
    python storyworlds/worlds/gpt-5.4/intricate_kindness_repetition_curiosity_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/intricate_kindness_repetition_curiosity_folk_tale.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.attrs.get("plural", False):
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    id: str
    place: str
    path: str
    sound: str
    wonders: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    plural_label: str
    one_label: str
    phrase: str
    motion: str
    voice: str
    food_need: str
    clue: str
    final_help: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    pieces: int = 0
    suits: set[str] = field(default_factory=set)
    share_verb: str = "shared"
    tags: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    label: str
    phrase: str
    approach: str
    image: str
    lesson: str
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


def _r_gratitude(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    for ent in world.entities.values():
        if ent.role != "helper":
            continue
        if ent.meters["fed"] < THRESHOLD:
            continue
        sig = ("gratitude", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["trust"] += 1
        path.meters["kindness"] += 1
        out.append("__kindness__")
    return out


def _r_reveal(world: World) -> list[str]:
    path = world.get("path")
    wonder = world.get("wonder")
    child = world.get("child")
    if path.meters["kindness"] < 3 or wonder.meters["revealed"] >= THRESHOLD:
        return []
    sig = ("reveal", wonder.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wonder.meters["revealed"] += 1
    child.memes["wonder"] += 1
    world.get("elder").memes["welcome"] += 1
    return ["__revealed__"]


CAUSAL_RULES = [
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
    Rule(name="reveal", tag="physical", apply=_r_reveal),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def gift_fits(helper: HelperKind, gift: Gift) -> bool:
    return helper.id in gift.suits


def enough_pieces(gift: Gift) -> bool:
    return gift.pieces >= 3


def wonder_in_setting(setting: Setting, wonder: Wonder) -> bool:
    return wonder.id in setting.wonders


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for hid, helper in HELPERS.items():
            for gid, gift in GIFTS.items():
                for wid, wonder in WONDERS.items():
                    if gift_fits(helper, gift) and enough_pieces(gift) and wonder_in_setting(setting, wonder):
                        combos.append((sid, hid, gid, wid))
    return combos


def explain_gift(helper: HelperKind, gift: Gift) -> str:
    if not enough_pieces(gift):
        return (
            f"(No story: {gift.phrase} only gives {gift.pieces} shareable piece"
            f"{'' if gift.pieces == 1 else 's'}, but this tale repeats kindness three times. "
            f"Pick a bundle with at least three pieces.)"
        )
    return (
        f"(No story: {helper.plural_label} would not want {gift.label}. "
        f"This folk tale needs a gift that the helper can truly use.)"
    )


def explain_wonder(setting: Setting, wonder: Wonder) -> str:
    return (
        f"(No story: {wonder.label} does not belong naturally in {setting.place}. "
        f"Choose a wonder that fits the setting's path and old lore.)"
    )


def predict_reveal(world: World, helper: HelperKind, gift: Gift) -> dict:
    sim = world.copy()
    for i in range(1, 4):
        helper_ent = sim.get(f"helper{i}")
        helper_ent.meters["fed"] += 1
        helper_ent.meters["hunger"] = 0
        sim.get("basket").meters["pieces"] -= 1
        propagate(sim, narrate=False)
    return {
        "revealed": sim.get("wonder").meters["revealed"] >= THRESHOLD,
        "kindness": sim.get("path").meters["kindness"],
        "remaining": sim.get("basket").meters["pieces"],
    }


def opening(world: World, child: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, where {setting.sound}, there lived a child named {child.id}."
    )
    world.say(
        f"One morning {child.pronoun()} noticed {setting.path}, so neatly wound and folded "
        f"that it looked like an intricate secret laid across the ground."
    )
    world.say(
        f"Curiosity tugged at {child.pronoun('object')}, and {child.pronoun()} followed the trail to see where it went."
    )


def prepare(world: World, child: Entity, gift: Gift) -> None:
    basket = world.get("basket")
    child.meters["carrying"] += 1
    basket.meters["pieces"] = float(gift.pieces)
    world.say(
        f"{child.id} had {gift.phrase} in a small basket, enough to share if sharing was needed."
    )


def first_hint(world: World, helper: HelperKind) -> None:
    world.say(
        f"From the roadside came a soft {helper.voice}. A hungry {helper.one_label} {helper.motion} into view."
    )


def repeated_encounter(
    world: World,
    child: Entity,
    helper_cfg: HelperKind,
    gift: Gift,
    helper_ent: Entity,
    ordinal: str,
) -> None:
    helper_ent.meters["hunger"] += 1
    child.memes["care"] += 1
    basket = world.get("basket")
    before = int(basket.meters["pieces"])
    if ordinal == "first":
        opener = "The first bend of the path brought "
    elif ordinal == "second":
        opener = "At the second bend there was "
    else:
        opener = "At the third bend, waiting beside a stone, there was "
    world.say(
        f"{opener}{helper_cfg.phrase}. \"{helper_cfg.clue}\" {helper_ent.pronoun()} seemed to say."
    )
    world.say(
        f"{child.id} did not hurry past. {child.pronoun().capitalize()} {gift.share_verb} one piece of {gift.label}, "
        f"and {helper_ent.label} ate with grateful little sounds."
    )
    helper_ent.meters["fed"] += 1
    helper_ent.meters["hunger"] = 0
    basket.meters["pieces"] = max(0.0, basket.meters["pieces"] - 1.0)
    propagate(world, narrate=False)
    after = int(basket.meters["pieces"])
    child.memes["kindness"] += 1
    helper_ent.memes["trust"] += 0
    world.facts["encounters"].append(
        {
            "ordinal": ordinal,
            "helper_label": helper_ent.label,
            "pieces_before": before,
            "pieces_after": after,
        }
    )
    if ordinal != "third":
        world.say(
            f"Then the little creature slipped ahead, and the path seemed easier to read than before."
        )


def wonder_revealed(world: World, child: Entity, helper: HelperKind, wonder: Wonder) -> None:
    world.say(
        f"Then all at once the three {helper.plural_label} appeared together. {helper.final_help}"
    )
    world.say(
        f"They led {child.id} to {wonder.approach}, and there {child.pronoun()} found {wonder.phrase}."
    )
    world.say(wonder.image)


def elder_welcome(world: World, child: Entity, elder: Entity, wonder: Wonder) -> None:
    child.memes["wonder"] += 1
    elder.memes["kindness"] += 1
    world.say(
        f"Beside it stood {elder.phrase}, smiling as if {elder.pronoun()} had been expecting footsteps all morning."
    )
    world.say(
        f'"You were curious enough to follow, and kind enough to stop three times," {elder.pronoun()} said. '
        f'"That is why {wonder.label} opened for you."'
    )


def ending(world: World, child: Entity, wonder: Wonder, gift: Gift) -> None:
    basket = world.get("basket")
    child.memes["peace"] += 1
    world.say(
        f"{wonder.lesson} {child.id} looked into the basket and saw that {child.pronoun('possessive')} "
        f"{gift.label} were gone, yet the day felt fuller, not smaller."
    )
    world.say(
        f"When {child.pronoun()} walked home again, the once-hidden trail no longer seemed secret at all. "
        f"It looked like a friendly path, remembering each kind stop."
    )
    world.facts["remaining_pieces"] = int(basket.meters["pieces"])


def tell(
    setting: Setting,
    helper: HelperKind,
    gift: Gift,
    wonder: Wonder,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            role="child",
            attrs={"trait": trait},
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label="the elder",
            phrase=f"an old {elder_type}",
            role="elder",
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            kind="thing",
            type="basket",
            label="basket",
            phrase="a small basket",
            role="basket",
        )
    )
    path = world.add(
        Entity(
            id="path",
            kind="thing",
            type="path",
            label="path",
            phrase=setting.path,
            role="path",
        )
    )
    world.add(
        Entity(
            id="wonder",
            kind="thing",
            type="wonder",
            label=wonder.label,
            phrase=wonder.phrase,
            role="wonder",
        )
    )
    for i in range(1, 4):
        world.add(
            Entity(
                id=f"helper{i}",
                kind="character",
                type="helper",
                label=helper.one_label,
                phrase=helper.one_label,
                role="helper",
                attrs={"plural": False, "index": i, "kind": helper.id},
            )
        )

    prediction = predict_reveal(world, helper, gift)
    world.facts["predicted_reveal"] = prediction["revealed"]
    world.facts["predicted_kindness"] = prediction["kindness"]

    opening(world, child, setting)
    prepare(world, child, gift)

    world.para()
    first_hint(world, helper)
    repeated_encounter(world, child, helper, gift, world.get("helper1"), "first")
    repeated_encounter(world, child, helper, gift, world.get("helper2"), "second")
    repeated_encounter(world, child, helper, gift, world.get("helper3"), "third")

    world.para()
    wonder_revealed(world, child, helper, wonder)
    elder_welcome(world, child, elder, wonder)

    world.para()
    ending(world, child, wonder, gift)

    world.facts.update(
        child=child,
        elder=elder,
        basket=basket,
        setting=setting,
        helper_cfg=helper,
        gift_cfg=gift,
        wonder_cfg=wonder,
        kindness_count=int(world.get("path").meters["kindness"]),
        revealed=world.get("wonder").meters["revealed"] >= THRESHOLD,
        encounters=[] if "encounters" not in world.facts else world.facts["encounters"],
    )
    return world


SETTINGS = {
    "forest_edge": Setting(
        id="forest_edge",
        place="a village at the forest edge",
        path="a narrow trail of fern stems and smooth pebbles",
        sound="the pines whispered even when the wind was small",
        wonders={"moon_well", "reed_gate"},
        tags={"forest"},
    ),
    "river_meadow": Setting(
        id="river_meadow",
        place="a riverside meadow",
        path="a line of flat stones stitched through the grass",
        sound="the water kept a silver murmur all day long",
        wonders={"moon_well", "bell_arbor"},
        tags={"river"},
    ),
    "hill_orchard": Setting(
        id="hill_orchard",
        place="an orchard on a round green hill",
        path="a curling track of fallen leaves and twigs",
        sound="bees hummed between the trees",
        wonders={"bell_arbor", "reed_gate"},
        tags={"orchard"},
    ),
}

HELPERS = {
    "sparrows": HelperKind(
        id="sparrows",
        plural_label="sparrows",
        one_label="sparrow",
        phrase="another hungry sparrow, then another after that",
        motion="hopped",
        voice="chirping",
        food_need="seeds",
        clue="Chi-ri, chi-ri",
        final_help="They darted from branch to branch, showing the true turns of the hidden path.",
        tags={"bird", "seed"},
    ),
    "mice": HelperKind(
        id="mice",
        plural_label="field mice",
        one_label="field mouse",
        phrase="a field mouse with bright, watchful eyes",
        motion="peeked",
        voice="squeak",
        food_need="crumbs",
        clue="This way, this way",
        final_help="They whisked through the grass and paused at each right turning until the secret place stood clear.",
        tags={"mouse", "crumb"},
    ),
    "hedgehogs": HelperKind(
        id="hedgehogs",
        plural_label="hedgehogs",
        one_label="hedgehog",
        phrase="a round little hedgehog nosing among the roots",
        motion="snuffled",
        voice="snuffly rustle",
        food_need="berries",
        clue="Huff-huff, follow close",
        final_help="They padded ahead in a solemn little row, and even the brambles bent aside for them.",
        tags={"hedgehog", "berry"},
    ),
}

GIFTS = {
    "seeds": Gift(
        id="seeds",
        label="seeds",
        phrase="three handfuls of seeds",
        pieces=3,
        suits={"sparrows"},
        share_verb="shared",
        tags={"seed"},
    ),
    "crumbs": Gift(
        id="crumbs",
        label="crumbs",
        phrase="three sweet crumbs from a honey cake",
        pieces=3,
        suits={"mice"},
        share_verb="shared",
        tags={"crumb"},
    ),
    "berries": Gift(
        id="berries",
        label="berries",
        phrase="three ripe berries wrapped in a leaf",
        pieces=3,
        suits={"hedgehogs"},
        share_verb="offered",
        tags={"berry"},
    ),
    "ribbon": Gift(
        id="ribbon",
        label="ribbon",
        phrase="one bright ribbon",
        pieces=1,
        suits=set(),
        share_verb="held out",
        tags={"ribbon"},
    ),
}

WONDERS = {
    "moon_well": Wonder(
        id="moon_well",
        label="the Moon Well",
        phrase="the Moon Well, ringed with pale stones and clear water",
        approach="a hollow where white flowers nodded around old stones",
        image="The water held the sky so still that even in daylight it seemed to keep a little piece of moonlight at the bottom.",
        lesson="The elder said that wells keep water, and good hearts keep kindness, and both give back what is lowered into them.",
        tags={"well"},
    ),
    "bell_arbor": Wonder(
        id="bell_arbor",
        label="the Bell Arbor",
        phrase="the Bell Arbor, where tiny silver bells hung under woven branches",
        approach="an arbor hidden behind drooping willow leaves",
        image="Whenever a soft breeze passed through, the bells answered one another in a bright, careful song.",
        lesson="The elder said that each kind deed is like a bell note: one is small, but three together can wake a whole garden.",
        tags={"bell"},
    ),
    "reed_gate": Wonder(
        id="reed_gate",
        label="the Reed Gate",
        phrase="the Reed Gate, a doorway braided from reeds and willow switches",
        approach="a bend where the grass opened before an old woven gate",
        image="Its careful twists crossed and recrossed until the whole gate looked like a basket large enough for a dream to pass through.",
        lesson="The elder said that a true path is woven from many small choices, and the kind ones hold fastest.",
        tags={"gate"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    helper: str
    gift: str
    wonder: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mira", "Lina", "Tali", "Nora", "Suri", "Ayla", "Mina", "Rosa"]
BOY_NAMES = ["Toma", "Niko", "Ilan", "Sami", "Arin", "Pavel", "Milo", "Rafi"]
TRAITS = ["curious", "gentle", "bright-eyed", "thoughtful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper_cfg"]
    wonder = f["wonder_cfg"]
    gift = f["gift_cfg"]
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the word "intricate" and features kindness, repetition, and curiosity.',
        f"Tell a gentle folk tale where a {child.type} named {child.id} follows a mysterious path, shares {gift.label} three times with {helper.plural_label}, and finds {wonder.label}.",
        f"Write a story in an old tale style where curiosity leads a child forward and repeated kindness opens a hidden wonder.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper_cfg"]
    gift = f["gift_cfg"]
    wonder = f["wonder_cfg"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child who followed a secret-looking path. It is also about the hungry {helper.plural_label} and the old {elder.label_word} waiting at the end.",
        ),
        (
            f"Why did {child.id} follow the path?",
            f"{child.id} followed it because curiosity tugged at {child.pronoun('object')}. The path looked intricate and secret, so {child.pronoun()} wanted to know where it led.",
        ),
        (
            f"What did {child.id} give away three times?",
            f"{child.pronoun().capitalize()} gave away pieces of {gift.label} three times, once at each bend in the path. Those repeated gifts are how kindness changes the story.",
        ),
        (
            "How was kindness repeated in the story?",
            f"The child stopped three separate times for hungry little creatures instead of hurrying on. Each kind stop added up, and after the third one the hidden wonder was revealed.",
        ),
        (
            f"What happened after the third kind act?",
            f"After the third act of kindness, the {helper.plural_label} gathered together and showed the true way. That led {child.id} to {wonder.label}, which opened only after kindness had been repeated.",
        ),
        (
            f"What lesson did the elder teach {child.id}?",
            f"The elder taught that kindness does not vanish when it is given away. In this tale, the child's small gifts came back as help, welcome, and wonder.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "bird": [
        (
            "Why might a sparrow want seeds?",
            "Sparrows eat seeds, so seeds are a natural food for them. A hungry bird would be glad to find a few."
        )
    ],
    "mouse": [
        (
            "What do mice nibble?",
            "Mice often nibble tiny bits of food like crumbs and grains. Small pieces are easy for them to carry and eat."
        )
    ],
    "hedgehog": [
        (
            "What is a hedgehog?",
            "A hedgehog is a small animal with spines on its back. It snuffles close to the ground while it looks for food."
        )
    ],
    "well": [
        (
            "What is a well?",
            "A well is a deep place where people draw up water. In folk tales, wells often feel old, quiet, and magical."
        )
    ],
    "bell": [
        (
            "What happens when bells ring in the wind?",
            "A moving breeze can shake little bells and make them sing. That is why wind bells sound bright and tinkly."
        )
    ],
    "gate": [
        (
            "What is a gate for?",
            "A gate marks the way into or out of a place. In stories, opening a gate often means entering something new."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, share, or be gentle with someone else. Small kind actions can matter a great deal."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It can lead you to ask questions and look closely."
        )
    ],
    "repetition": [
        (
            "What does repetition mean in a story?",
            "Repetition means something happens again and again in a clear pattern. It helps a story feel memorable and a little magical."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "kindness",
    "curiosity",
    "repetition",
    "bird",
    "mouse",
    "hedgehog",
    "well",
    "bell",
    "gate",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"kindness", "curiosity", "repetition"}
    helper = f["helper_cfg"]
    wonder = f["wonder_cfg"]
    tags |= set(helper.tags)
    tags |= set(wonder.tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v or k == "index"}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="forest_edge",
        helper="sparrows",
        gift="seeds",
        wonder="moon_well",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        trait="curious",
    ),
    StoryParams(
        setting="river_meadow",
        helper="mice",
        gift="crumbs",
        wonder="bell_arbor",
        child_name="Niko",
        child_gender="boy",
        elder_type="grandfather",
        trait="thoughtful",
    ),
    StoryParams(
        setting="hill_orchard",
        helper="hedgehogs",
        gift="berries",
        wonder="reed_gate",
        child_name="Suri",
        child_gender="girl",
        elder_type="grandmother",
        trait="gentle",
    ),
]


ASP_RULES = r"""
fits(H, G)      :- helper(H), gift(G), suits(G, H).
enough(G)       :- gift(G), pieces(G, P), P >= 3.
belongs(S, W)   :- setting(S), wonder(W), allowed(S, W).
valid(S, H, G, W) :- setting(S), helper(H), gift(G), wonder(W),
                     fits(H, G), enough(G), belongs(S, W).

kindness_count(3) :- chosen_gift(G), enough(G), chosen_helper(H), fits(H, G).
revealed          :- chosen_setting(S), chosen_wonder(W), belongs(S, W),
                     kindness_count(3).
outcome(revealed) :- revealed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for wid in sorted(setting.wonders):
            lines.append(asp.fact("allowed", sid, wid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("pieces", gid, gift.pieces))
        for hid in sorted(gift.suits):
            lines.append(asp.fact("suits", gid, hid))
    for wid in WONDERS:
        lines.append(asp.fact("wonder", wid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_gift", params.gift),
            asp.fact("chosen_wonder", params.wonder),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    ok = (
        params.setting in SETTINGS
        and params.helper in HELPERS
        and params.gift in GIFTS
        and params.wonder in WONDERS
        and gift_fits(HELPERS[params.helper], GIFTS[params.gift])
        and enough_pieces(GIFTS[params.gift])
        and wonder_in_setting(SETTINGS[params.setting], WONDERS[params.wonder])
    )
    return "revealed" if ok else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome:", params)
            break
    if rc == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious child repeats a kind act three times and finds a hidden folk-tale wonder."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, helper, gift, wonder) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.gift:
        helper = HELPERS[args.helper]
        gift = GIFTS[args.gift]
        if not gift_fits(helper, gift) or not enough_pieces(gift):
            raise StoryError(explain_gift(helper, gift))
    if args.setting and args.wonder:
        setting = SETTINGS[args.setting]
        wonder = WONDERS[args.wonder]
        if not wonder_in_setting(setting, wonder):
            raise StoryError(explain_wonder(setting, wonder))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.helper is None or combo[1] == args.helper)
        and (args.gift is None or combo[2] == args.gift)
        and (args.wonder is None or combo[3] == args.wonder)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, helper, gift, wonder = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        helper=helper,
        gift=gift,
        wonder=wonder,
        child_name=name,
        child_gender=gender,
        elder_type=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("setting", SETTINGS),
        ("helper", HELPERS),
        ("gift", GIFTS),
        ("wonder", WONDERS),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid {field_name}: {value})")
    if not gift_fits(HELPERS[params.helper], GIFTS[params.gift]) or not enough_pieces(GIFTS[params.gift]):
        raise StoryError(explain_gift(HELPERS[params.helper], GIFTS[params.gift]))
    if not wonder_in_setting(SETTINGS[params.setting], WONDERS[params.wonder]):
        raise StoryError(explain_wonder(SETTINGS[params.setting], WONDERS[params.wonder]))

    world = tell(
        setting=SETTINGS[params.setting],
        helper=HELPERS[params.helper],
        gift=GIFTS[params.gift],
        wonder=WONDERS[params.wonder],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, helper, gift, wonder) combos:\n")
        for setting, helper, gift, wonder in combos:
            print(f"  {setting:12} {helper:10} {gift:8} {wonder}")
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
            header = f"### {p.child_name}: {p.helper} / {p.gift} / {p.wonder}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
