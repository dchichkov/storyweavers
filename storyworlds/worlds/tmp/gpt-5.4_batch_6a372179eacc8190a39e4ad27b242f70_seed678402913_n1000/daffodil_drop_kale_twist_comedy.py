#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py
=============================================================

A small comedy storyworld about a child carrying a bowl of kale and a bright
daffodil, making an accidental drop, and discovering a silly twist: the spill
lands on a friendly garden prop and turns it into an accidental joke.

The world model keeps the logic narrow and child-facing:

- A leafy kind of kale can drape like funny hair or a mane.
- A receiver must actually be able to catch the dropped leaves.
- The daffodil only makes the twist bigger when the receiver can hold it too.
- Food that touched the floor is not eaten; a grown-up makes a clean fresh batch.

Run it
------
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py --all
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py --qa
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py --json
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py --asp
    python storyworlds/worlds/gpt-5.4/daffodil_drop_kale_twist_comedy.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from a nested world directory under storyworlds/worlds/<model>/.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    can_catch_kale: bool = False
    can_hold_flower: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    intro: str
    lunch_spot: str
    receivers: set[str] = field(default_factory=set)


@dataclass
class KaleForm:
    id: str
    label: str
    phrase: str
    taste: str
    drapes: bool = True
    crisp: bool = False
    safe_after_drop: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ReceiverCfg:
    id: str
    label: str
    phrase: str
    kind: str
    wig_line: str
    flower_line: str
    can_catch_kale: bool = False
    can_hold_flower: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    setup: str
    bump: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_kale_wig(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("kale")
    receiver = world.get("receiver")
    if bowl.meters["dropped"] < THRESHOLD or not receiver.can_catch_kale:
        return out
    sig = ("kale_wig", receiver.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    receiver.meters["wearing_kale"] += 1
    world.get("hero").memes["surprise"] += 1
    for eid, ent in world.entities.items():
        if ent.kind == "character":
            ent.memes["amusement"] += 1
    out.append("__wig__")
    return out


def _r_flower_finish(world: World) -> list[str]:
    out: list[str] = []
    flower = world.get("flower")
    receiver = world.get("receiver")
    if flower.meters["dropped"] < THRESHOLD:
        return out
    if receiver.meters["wearing_kale"] < THRESHOLD or not receiver.can_hold_flower:
        return out
    sig = ("flower_finish", receiver.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    receiver.meters["wearing_flower"] += 1
    for eid, ent in world.entities.items():
        if ent.kind == "character":
            ent.memes["laughter"] += 1
    out.append("__flower__")
    return out


def _r_floor_food(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("kale")
    if bowl.meters["dropped"] < THRESHOLD:
        return out
    sig = ("floor_food", bowl.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["messy"] += 1
    bowl.meters["inedible"] += 1
    world.get("helper").meters["work"] += 1
    world.get("hero").memes["embarrassment"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES = [
    Rule(name="kale_wig", tag="physical", apply=_r_kale_wig),
    Rule(name="flower_finish", tag="physical", apply=_r_flower_finish),
    Rule(name="floor_food", tag="physical", apply=_r_floor_food),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                changed = True
                produced.extend(s for s in result if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_receiver(setting: Setting, receiver: ReceiverCfg) -> bool:
    return receiver.id in setting.receivers


def valid_combo(setting: Setting, kale: KaleForm, receiver: ReceiverCfg) -> bool:
    return valid_receiver(setting, receiver) and kale.drapes and receiver.can_catch_kale


def outcome_of(params: "StoryParams") -> str:
    setting = SETTINGS[params.setting]
    kale = KALE_FORMS[params.kale]
    receiver = RECEIVERS[params.receiver]
    if not valid_combo(setting, kale, receiver):
        return "invalid"
    return "grand_twist" if receiver.can_hold_flower else "twist"


def predict_drop(setting: Setting, kale: KaleForm, receiver: ReceiverCfg) -> dict:
    return {
        "twist": valid_combo(setting, kale, receiver),
        "grand": valid_combo(setting, kale, receiver) and receiver.can_hold_flower,
        "fresh_batch_needed": True,
    }


def introduce(world: World, hero: Entity, helper: Entity, kale: KaleForm) -> None:
    world.say(
        f"{hero.id} was helping {hero.pronoun('possessive')} {helper.label_word} carry lunch to "
        f"{world.setting.lunch_spot}. On the counter waited {kale.phrase} and one sunny daffodil "
        f"in a little cup."
    )
    world.say(world.setting.intro)
    hero.memes["helpful"] += 1
    hero.memes["worry"] += 1


def assign_jobs(world: World, hero: Entity, helper: Entity, receiver: ReceiverCfg) -> None:
    world.say(
        f'"Can you take the bowl and the flower outside?" asked {helper.label_word}. '
        f'{hero.id} nodded, but the bowl looked wobbly and the path passed right by {receiver.phrase}.'
    )
    pred = predict_drop(world.setting, world.facts["kale_cfg"], world.facts["receiver_cfg"])
    world.facts["predicted_twist"] = pred["twist"]
    world.facts["predicted_grand"] = pred["grand"]


def warning_beat(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f'{hero.id} took tiny careful steps. {hero.pronoun().capitalize()} wanted to be helpful, '
        f'not the child who turned lunch into a comedy show.'
    )
    helper.memes["trust"] += 1


def do_drop(world: World, hero: Entity, cause: Cause) -> None:
    bowl = world.get("kale")
    flower = world.get("flower")
    hero.memes["alarm"] += 1
    bowl.meters["dropped"] += 1
    flower.meters["dropped"] += 1
    world.say(cause.setup)
    world.say(
        f"{cause.bump} The bowl tipped, the kale made one greeny swirly drop through the air, "
        f"and the daffodil bounced after it."
    )
    propagate(world, narrate=False)


def narrate_twist(world: World, receiver: Entity, receiver_cfg: ReceiverCfg, helper: Entity) -> None:
    hero = world.get("hero")
    if receiver.meters["wearing_kale"] >= THRESHOLD:
        world.say(
            f"For one shocked second, nobody moved. Then the kale landed all over {receiver_cfg.phrase}, "
            f"and suddenly {receiver_cfg.wig_line}."
        )
    if receiver.meters["wearing_flower"] >= THRESHOLD:
        world.say(
            f"The daffodil stuck in place too, so {receiver_cfg.flower_line}."
        )
        world.facts["outcome"] = "grand_twist"
    else:
        world.facts["outcome"] = "twist"
    hero.memes["embarrassment"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["laughter"] += 1
    world.say(
        f'{helper.label_word.capitalize()} laughed first, but it was a warm laugh. '
        f'Soon {hero.id} was laughing too, because the accident looked far too silly to stay scary.'
    )


def remake(world: World, helper: Entity, hero: Entity, kale: KaleForm) -> None:
    bowl = world.get("kale")
    bowl.meters["fresh_batch"] += 1
    hero.memes["pride"] += 1
    hero.memes["brave_taste"] += 1
    world.say(
        f'"We do not eat floor kale," said {helper.label_word}, still smiling. '
        f'{helper.pronoun().capitalize()} made a clean fresh bowl while {hero.id} washed {hero.pronoun("possessive")} hands and fetched a new plate.'
    )
    world.say(
        f"When the fresh {kale.label} came out, {hero.id} tried one piece. "
        f"It tasted {kale.taste}, and somehow the laugh from the silly drop made the first bite feel easy."
    )


def ending_image(world: World, hero: Entity, receiver_cfg: ReceiverCfg) -> None:
    outcome = world.facts.get("outcome", "twist")
    if outcome == "grand_twist":
        world.say(
            f"At lunch, everyone kept glancing at {receiver_cfg.phrase}, still wearing its green joke and yellow daffodil. "
            f"{hero.id} nearly giggled into every bite."
        )
    else:
        world.say(
            f"At lunch, everyone kept glancing at {receiver_cfg.phrase}, still wearing its green joke. "
            f"Every time {hero.id} looked up, another grin popped out."
        )
    world.say(
        "The accident had started as a mess, but it ended as the funniest decoration in the yard."
    )


def tell(
    setting: Setting,
    kale_cfg: KaleForm,
    receiver_cfg: ReceiverCfg,
    cause: Cause,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        phrase="the helper",
        role="helper",
    ))
    kale = world.add(Entity(
        id="kale",
        kind="thing",
        type="food",
        label=kale_cfg.label,
        phrase=kale_cfg.phrase,
        edible=True,
        tags=set(kale_cfg.tags),
    ))
    flower = world.add(Entity(
        id="flower",
        kind="thing",
        type="flower",
        label="daffodil",
        phrase="a daffodil",
        tags={"flower", "daffodil"},
    ))
    receiver = world.add(Entity(
        id="receiver",
        kind="thing",
        type=receiver_cfg.kind,
        label=receiver_cfg.label,
        phrase=receiver_cfg.phrase,
        can_catch_kale=receiver_cfg.can_catch_kale,
        can_hold_flower=receiver_cfg.can_hold_flower,
        tags=set(receiver_cfg.tags),
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        kale_cfg=kale_cfg,
        receiver_cfg=receiver_cfg,
        cause=cause,
        setting=setting,
    )

    introduce(world, hero, helper, kale_cfg)
    assign_jobs(world, hero, helper, receiver_cfg)
    world.para()
    warning_beat(world, hero, helper)
    do_drop(world, hero, cause)
    world.para()
    narrate_twist(world, receiver, receiver_cfg, helper)
    remake(world, helper, hero, kale_cfg)
    world.para()
    ending_image(world, hero, receiver_cfg)

    world.facts.update(
        hero_name=hero_name,
        helper_name=helper.label_word,
        floor_food=world.get("kale").meters["inedible"] >= THRESHOLD,
        flower_stuck=world.get("receiver").meters["wearing_flower"] >= THRESHOLD,
        laugh_level="grand" if world.facts.get("outcome") == "grand_twist" else "big",
        tasted_kale=hero.memes["brave_taste"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "porch": Setting(
        id="porch",
        place="the porch",
        intro="Sunlight fell across the porch steps, and the chairs were waiting for lunch.",
        lunch_spot="the porch table",
        receivers={"gnome", "pumpkin"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden",
        intro="Bees hummed over the beds, and the garden path curved past the decorations.",
        lunch_spot="the garden bench",
        receivers={"gnome", "lion"},
    ),
    "patio": Setting(
        id="patio",
        place="the patio",
        intro="The patio stones were warm, and a striped cloth was already spread for lunch.",
        lunch_spot="the patio table",
        receivers={"pumpkin", "lion"},
    ),
}

KALE_FORMS = {
    "curly": KaleForm(
        id="curly",
        label="curly kale",
        phrase="a big bowl of curly kale leaves",
        taste="crisp and salty",
        drapes=True,
        crisp=False,
        safe_after_drop=False,
        tags={"kale", "leafy"},
    ),
    "ribbons": KaleForm(
        id="ribbons",
        label="kale ribbons",
        phrase="a bowl of shiny kale ribbons",
        taste="buttery and a little sweet",
        drapes=True,
        crisp=False,
        safe_after_drop=False,
        tags={"kale", "leafy"},
    ),
    "chips": KaleForm(
        id="chips",
        label="kale chips",
        phrase="a tray piled with curly kale chips",
        taste="light and crackly",
        drapes=True,
        crisp=True,
        safe_after_drop=False,
        tags={"kale", "chips"},
    ),
    "soup": KaleForm(
        id="soup",
        label="kale soup",
        phrase="a warm bowl of kale soup",
        taste="savory",
        drapes=False,
        crisp=False,
        safe_after_drop=False,
        tags={"kale", "soup"},
    ),
}

RECEIVERS = {
    "gnome": ReceiverCfg(
        id="gnome",
        label="garden gnome",
        phrase="the garden gnome by the path",
        kind="gnome",
        wig_line="it looked as if the gnome had suddenly grown a curly green wig",
        flower_line="the gnome looked dressed for a parade with one proud yellow daffodil tucked above the wig",
        can_catch_kale=True,
        can_hold_flower=True,
        tags={"gnome", "garden"},
    ),
    "pumpkin": ReceiverCfg(
        id="pumpkin",
        label="painted pumpkin",
        phrase="the painted pumpkin on the stool",
        kind="pumpkin",
        wig_line="it looked as if the pumpkin had borrowed a wild green hairdo",
        flower_line="the pumpkin now looked like a grand vegetable queen with a daffodil crown",
        can_catch_kale=True,
        can_hold_flower=True,
        tags={"pumpkin", "garden"},
    ),
    "lion": ReceiverCfg(
        id="lion",
        label="toy lion",
        phrase="the toy lion near the bench",
        kind="toy",
        wig_line="it looked as if the lion had finally grown the leafiest mane in the world",
        flower_line="the lion looked extra fancy",
        can_catch_kale=True,
        can_hold_flower=False,
        tags={"lion", "toy"},
    ),
    "watering_can": ReceiverCfg(
        id="watering_can",
        label="watering can",
        phrase="the metal watering can by the wall",
        kind="can",
        wig_line="it looked silly",
        flower_line="it looked silly",
        can_catch_kale=False,
        can_hold_flower=False,
        tags={"garden"},
    ),
}

CAUSES = {
    "sneeze": Cause(
        id="sneeze",
        setup="Just then, a speck of pepper from the kitchen drifted out and tickled Mia's nose.",
        bump="Aaa-choo",
        tags={"sneeze"},
    ),
    "bumblebee": Cause(
        id="bumblebee",
        setup="Just then, a bumbly bee looped past the daffodil as if it wanted a closer look.",
        bump="Mia gave one startled hop",
        tags={"bee"},
    ),
    "hiccup": Cause(
        id="hiccup",
        setup="Just then, a surprise hiccup popped out of nowhere.",
        bump="Hic",
        tags={"hiccup"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Sam", "Finn", "Eli", "Jack"]
TRAITS = ["careful", "busy", "hopeful", "earnest", "wobbly"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    setting: str
    kale: str
    receiver: str
    cause: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="porch",
        kale="curly",
        receiver="gnome",
        cause="sneeze",
        name="Mia",
        gender="girl",
        helper="mother",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        setting="garden",
        kale="ribbons",
        receiver="lion",
        cause="bumblebee",
        name="Ben",
        gender="boy",
        helper="grandfather",
        trait="earnest",
        seed=2,
    ),
    StoryParams(
        setting="patio",
        kale="chips",
        receiver="pumpkin",
        cause="hiccup",
        name="Ella",
        gender="girl",
        helper="father",
        trait="hopeful",
        seed=3,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for kid, kale in KALE_FORMS.items():
            for rid, receiver in RECEIVERS.items():
                if valid_combo(setting, kale, receiver):
                    combos.append((sid, kid, rid))
    return combos


def explain_rejection(setting: Setting, kale: KaleForm, receiver: ReceiverCfg) -> str:
    if not valid_receiver(setting, receiver):
        return (
            f"(No story: {receiver.phrase} is not part of the scene at {setting.place}, "
            f"so nothing is there to catch the funny drop.)"
        )
    if not kale.drapes:
        return (
            f"(No story: {kale.label} would splash instead of drape, so it cannot make the leafy twist. "
            f"Pick curly kale, kale ribbons, or kale chips.)"
        )
    if not receiver.can_catch_kale:
        return (
            f"(No story: {receiver.phrase} cannot really catch a falling pile of kale in a funny visible way.)"
        )
    return "(No story: this combination cannot make the twist.)"


KNOWLEDGE = {
    "daffodil": [
        (
            "What is a daffodil?",
            "A daffodil is a bright spring flower, often yellow, with petals around a trumpet-shaped middle."
        )
    ],
    "kale": [
        (
            "What is kale?",
            "Kale is a leafy green vegetable. People can cook it into chips, ribbons, soups, and other dishes."
        )
    ],
    "flower_food": [
        (
            "Can you eat food that fell on the floor outside?",
            "No. Food that falls on the floor outside should be thrown away, and you should get a clean fresh serving instead."
        )
    ],
    "gnome": [
        (
            "What is a garden gnome?",
            "A garden gnome is a small decoration people put outside in gardens. It does not move, but it can look funny when dressed up."
        )
    ],
    "pumpkin": [
        (
            "What is a pumpkin?",
            "A pumpkin is a round squash. People sometimes paint or decorate pumpkins for fun."
        )
    ],
    "lion": [
        (
            "What is a mane?",
            "A mane is the longer hair around a lion's neck. It makes the lion's head look big and grand."
        )
    ],
    "laugh_kindly": [
        (
            "What is a kind laugh?",
            "A kind laugh is a laugh that shares the joke without being mean. It helps someone feel safe instead of ashamed."
        )
    ],
}
KNOWLEDGE_ORDER = ["daffodil", "kale", "flower_food", "gnome", "pumpkin", "lion", "laugh_kindly"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    kale = world.facts["kale_cfg"]
    receiver = world.facts["receiver_cfg"]
    return [
        f'Write a short comedy for ages 3 to 5 that includes the words "daffodil", "drop", and "kale".',
        f"Tell a funny story where a child named {hero.label} carries {kale.phrase}, makes an accidental drop, and the spill lands on {receiver.phrase}.",
        f"Write a gentle Twist story where {hero.label} worries about making a mess, but {hero.pronoun('possessive')} {helper.label_word} helps the accident turn into a joke and then makes a clean fresh lunch.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    kale = world.facts["kale_cfg"]
    receiver = world.facts["receiver_cfg"]
    cause = world.facts["cause"]
    outcome = world.facts.get("outcome", "twist")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who was helping {hero.pronoun('possessive')} {helper.label_word} carry lunch outside. The lunch included {kale.phrase} and a bright daffodil."
        ),
        (
            "What went wrong on the way to lunch?",
            f"{cause.setup} Then {cause.bump.lower()} and the bowl tipped, so the kale made a silly drop through the air and the daffodil bounced after it. That turned the careful walk into an accident."
        ),
        (
            "Why did nobody eat the spilled kale?",
            f"They did not eat it because it had fallen during the drop and touched the outside path. {helper.label_word.capitalize()} made a clean fresh batch instead, which is the safe thing to do."
        ),
    ]
    if outcome == "grand_twist":
        qa.append(
            (
                "What was the twist?",
                f"The twist was that the spilled kale and the daffodil landed on {receiver.phrase} and made it look dressed up instead of ruined. The accident changed from embarrassing to funny because the decoration looked so grand."
            )
        )
    else:
        qa.append(
            (
                "What was the twist?",
                f"The twist was that the spilled kale landed on {receiver.phrase} and made it look ridiculous in a funny way. Everyone laughed kindly, so the mess stopped feeling scary."
            )
        )
    qa.append(
        (
            f"How did {hero.label} feel at the end?",
            f"{hero.label} felt relieved and proud. After the warm laughter and the clean fresh bowl, {hero.pronoun()} was even brave enough to taste the kale."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    receiver = world.facts["receiver_cfg"]
    tags = {"daffodil", "kale", "flower_food", "laugh_kindly"}
    if receiver.id == "gnome":
        tags.add("gnome")
    if receiver.id == "pumpkin":
        tags.add("pumpkin")
    if receiver.id == "lion":
        tags.add("lion")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.can_catch_kale:
            flags.append("can_catch_kale")
        if ent.can_hold_flower:
            flags.append("can_hold_flower")
        if ent.edible:
            flags.append("edible")
        if flags:
            bits.append(f"flags={flags}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome', '?')}")
    return "\n".join(lines)


ASP_RULES = r"""
present(S, R) :- setting(S), receiver(R), appears(S, R).
valid(S, K, R) :- present(S, R), drapes(K), catches_kale(R).

grand_twist(S, K, R) :- valid(S, K, R), holds_flower(R).
twist(S, K, R) :- valid(S, K, R), not holds_flower(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for kid, kale in KALE_FORMS.items():
        lines.append(asp.fact("kale", kid))
        if kale.drapes:
            lines.append(asp.fact("drapes", kid))
    for rid, receiver in RECEIVERS.items():
        lines.append(asp.fact("receiver", rid))
        if receiver.can_catch_kale:
            lines.append(asp.fact("catches_kale", rid))
        if receiver.can_hold_flower:
            lines.append(asp.fact("holds_flower", rid))
    for sid, setting in SETTINGS.items():
        for rid in sorted(setting.receivers):
            lines.append(asp.fact("appears", sid, rid))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_kale", params.kale),
            asp.fact("chosen_receiver", params.receiver),
            "selected_valid :- valid(S, K, R), chosen_setting(S), chosen_kale(K), chosen_receiver(R).",
            "selected_grand :- grand_twist(S, K, R), chosen_setting(S), chosen_kale(K), chosen_receiver(R).",
            "selected_twist :- twist(S, K, R), chosen_setting(S), chosen_kale(K), chosen_receiver(R).",
        ]
    )
    model = asp.one_model(
        asp_program(
            scenario,
            "#show selected_valid/0.\n#show selected_grand/0.\n#show selected_twist/0.",
        )
    )
    atoms = set(str(a) for a in model.symbols(shown=True))
    if "selected_grand" in atoms:
        return "grand_twist"
    if "selected_twist" in atoms:
        return "twist"
    return "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld: an accidental drop, a daffodil, kale, and a garden twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--kale", choices=KALE_FORMS)
    ap.add_argument("--receiver", choices=RECEIVERS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.receiver:
        setting = SETTINGS[args.setting]
        receiver = RECEIVERS[args.receiver]
        if not valid_receiver(setting, receiver):
            kale = KALE_FORMS[args.kale] if args.kale else next(iter(KALE_FORMS.values()))
            raise StoryError(explain_rejection(setting, kale, receiver))
    if args.setting and args.kale and args.receiver:
        setting = SETTINGS[args.setting]
        kale = KALE_FORMS[args.kale]
        receiver = RECEIVERS[args.receiver]
        if not valid_combo(setting, kale, receiver):
            raise StoryError(explain_rejection(setting, kale, receiver))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.kale is None or combo[1] == args.kale)
        and (args.receiver is None or combo[2] == args.receiver)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, kale_id, receiver_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    cause = args.cause or rng.choice(sorted(CAUSES))
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        kale=kale_id,
        receiver=receiver_id,
        cause=cause,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.kale not in KALE_FORMS:
        raise StoryError(f"(Unknown kale form: {params.kale})")
    if params.receiver not in RECEIVERS:
        raise StoryError(f"(Unknown receiver: {params.receiver})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    setting = SETTINGS[params.setting]
    kale = KALE_FORMS[params.kale]
    receiver = RECEIVERS[params.receiver]
    if not valid_combo(setting, kale, receiver):
        raise StoryError(explain_rejection(setting, kale, receiver))

    world = tell(
        setting=setting,
        kale_cfg=kale,
        receiver_cfg=receiver,
        cause=CAUSES[params.cause],
        hero_name=params.name,
        hero_gender=params.gender,
        helper_type=params.helper,
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


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "daffodil" not in sample.story or "kale" not in sample.story:
        raise StoryError("(Smoke test failed: generated story is missing core content.)")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True, header="### smoke")
    if "smoke" not in buf.getvalue():
        raise StoryError("(Smoke test failed: emit() produced unexpected output.)")


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
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test passed for generate() and emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show grand_twist/3.\n#show twist/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, kale, receiver) combos:\n")
        for setting, kale, receiver in combos:
            print(f"  {setting:8} {kale:8} {receiver}")
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
            header = f"### {p.name}: {p.kale} at {p.setting} onto {p.receiver} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
