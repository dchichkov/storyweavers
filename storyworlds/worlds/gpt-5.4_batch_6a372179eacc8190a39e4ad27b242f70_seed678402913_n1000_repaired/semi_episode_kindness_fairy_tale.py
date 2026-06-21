#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/semi_episode_kindness_fairy_tale.py
==============================================================

A small fairy-tale storyworld about a child who pauses on the way to a feast to
help a creature in need. The stories are grounded in simulated state: a trouble
(cold, hunger, or fear of the dark) creates distress, a matching gift or tool
relieves it, and the ending shows how one kind choice changes the morning for
everyone.

The seed words are carried naturally in the prose:
- "semi" appears in the fairy-tale setting image.
- "episode" appears in the reflective closing image.

Run it
------
    python storyworlds/worlds/gpt-5.4/semi_episode_kindness_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/semi_episode_kindness_fairy_tale.py --trouble cold --gift scarf
    python storyworlds/worlds/gpt-5.4/semi_episode_kindness_fairy_tale.py --trouble hungry --gift lantern
    python storyworlds/worlds/gpt-5.4/semi_episode_kindness_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/semi_episode_kindness_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/semi_episode_kindness_fairy_tale.py --verify
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
# from its nested directory under storyworlds/worlds/<model>/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"        # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.label or self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    opening: str
    path_detail: str
    feast: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    symptom: str
    request: str
    need: str
    result: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    share_verb: str = ""
    result: str = ""
    magical_return: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    phrase: str
    type: str
    title: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    if creature is None:
        return out
    for meter, feeling in (("cold", "misery"), ("hunger", "misery"), ("fear_dark", "fear")):
        if creature.meters[meter] < THRESHOLD:
            continue
        sig = ("distress", meter)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        creature.meters["tears"] += 1
        creature.memes[feeling] += 1
        out.append("__distress__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    hero = world.entities.get("hero")
    if creature is None or hero is None:
        return out
    helped = any(creature.meters[key] <= 0 for key in ("cold", "hunger", "fear_dark"))
    if not helped:
        return out
    sig = ("relief", creature.id)
    if sig in world.fired:
        return out
    if creature.meters["comfort"] < THRESHOLD and creature.meters["full"] < THRESHOLD and creature.meters["safe"] < THRESHOLD:
        return out
    world.fired.add(sig)
    creature.memes["gratitude"] += 1
    creature.memes["trust"] += 1
    hero.memes["joy"] += 1
    hero.memes["kindness"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="distress", tag="physical", apply=_r_distress),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def can_help(trouble: Trouble, gift: Gift) -> bool:
    return trouble.need in gift.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for creature_id in CREATURES:
            for trouble_id, trouble in TROUBLES.items():
                for gift_id, gift in GIFTS.items():
                    if can_help(trouble, gift):
                        combos.append((setting_id, creature_id, trouble_id, gift_id))
    return combos


def explain_rejection(trouble: Trouble, gift: Gift) -> str:
    return (
        f"(No story: {gift.phrase} does not solve {trouble.label}. "
        f"This world only tells kindness stories where the offered gift truly fits the need.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_relief(world: World, trouble_id: str, gift_id: str) -> dict:
    sim = world.copy()
    trouble = TROUBLES[trouble_id]
    gift = GIFTS[gift_id]
    creature = sim.get("creature")
    if not can_help(trouble, gift):
        return {"works": False, "feeling_better": False}
    apply_help_state(sim, creature, trouble, gift)
    return {
        "works": True,
        "feeling_better": (
            creature.meters["comfort"] >= THRESHOLD
            or creature.meters["full"] >= THRESHOLD
            or creature.meters["safe"] >= THRESHOLD
        ),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def set_trouble_state(creature: Entity, trouble: Trouble) -> None:
    if trouble.id == "cold":
        creature.meters["cold"] += 1
    elif trouble.id == "hungry":
        creature.meters["hunger"] += 1
    elif trouble.id == "dark":
        creature.meters["fear_dark"] += 1


def apply_help_state(world: World, creature: Entity, trouble: Trouble, gift: Gift) -> None:
    if trouble.id == "cold":
        creature.meters["cold"] = 0.0
        creature.meters["comfort"] += 1
    elif trouble.id == "hungry":
        creature.meters["hunger"] = 0.0
        creature.meters["full"] += 1
    elif trouble.id == "dark":
        creature.meters["fear_dark"] = 0.0
        creature.meters["safe"] += 1
    creature.meters["tears"] = 0.0
    propagate(world, narrate=False)


def opening(world: World, hero: Entity, setting: Setting, gift: Gift) -> None:
    hero.memes["anticipation"] += 1
    world.say(
        f"Once, in {setting.place}, {hero.id} walked at dawn toward {setting.feast} "
        f"with {gift.phrase} in {hero.pronoun('possessive')} hands."
    )
    world.say(setting.opening)
    world.say(setting.path_detail)


def encounter(world: World, hero: Entity, creature: Entity, trouble: Trouble) -> None:
    set_trouble_state(creature, trouble)
    propagate(world, narrate=False)
    hero.memes["concern"] += 1
    world.say(
        f"Beside the path, {hero.id} found {creature.phrase} who looked miserable. "
        f"{trouble.symptom}"
    )
    world.say(f'"Please," said {creature.title}, "{trouble.request}"')


def pause_and_notice(world: World, hero: Entity, trouble: Trouble, gift: Gift) -> None:
    pred = predict_relief(world, trouble.id, gift.id)
    world.facts["predicted_works"] = pred["works"]
    if pred["works"]:
        world.say(
            f"{hero.id} thought of the feast for only a moment, then looked back at the small face by the path. "
            f"{hero.pronoun().capitalize()} knew {gift.label} might help."
        )
    else:
        world.say(
            f"{hero.id} wished to help at once, but {hero.pronoun('possessive')} gift was wrong for the trouble."
        )


def share(world: World, hero: Entity, creature: Entity, trouble: Trouble, gift: Gift) -> None:
    hero.memes["kindness"] += 1
    hero.meters["gift_shared"] += 1
    world.get("gift").meters["used"] += 1
    world.say(
        f"So {hero.id} {gift.share_verb}. {gift.result}"
    )
    apply_help_state(world, creature, trouble, gift)
    world.say(trouble.result)


def return_kindness(world: World, hero: Entity, creature: Entity, setting: Setting, gift: Gift) -> None:
    creature.memes["gratitude"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"{creature.title.capitalize()} smiled so brightly that the morning itself seemed to lean closer. "
        f"{gift.magical_return}"
    )
    world.say(
        f"Together they went on to {setting.feast}, and the doors did not close on them at all."
    )


def feast_ending(world: World, hero: Entity, creature: Entity, setting: Setting) -> None:
    hero.memes["belonging"] += 1
    creature.memes["belonging"] += 1
    world.say(
        f"There, under lamps shaped like dew drops, the guests made room for {hero.id} and {creature.title}."
    )
    world.say(setting.ending)
    world.say(
        "Later, everyone spoke of that gentle episode and said the finest magic in the world was simple kindness."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    creature_cfg: CreatureCfg,
    trouble: Trouble,
    gift: Gift,
    hero_name: str = "Elin",
    hero_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    if not can_help(trouble, gift):
        raise StoryError(explain_rejection(trouble, gift))

    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        tags={"hero"},
    ))
    creature = world.add(Entity(
        id="creature",
        kind="character",
        type=creature_cfg.type,
        label=creature_cfg.title,
        phrase=creature_cfg.phrase,
        role="creature",
        tags=set(creature_cfg.tags),
    ))
    world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift.label,
        phrase=gift.phrase,
        role="gift",
        tags=set(gift.tags),
    ))
    world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label=parent_type,
        role="parent",
    ))

    opening(world, hero, setting, gift)
    world.para()
    encounter(world, hero, creature, trouble)
    pause_and_notice(world, hero, trouble, gift)
    world.para()
    share(world, hero, creature, trouble, gift)
    return_kindness(world, hero, creature, setting, gift)
    world.para()
    feast_ending(world, hero, creature, setting)

    world.facts.update(
        setting=setting,
        creature_cfg=creature_cfg,
        trouble=trouble,
        gift_cfg=gift,
        hero=hero,
        creature=creature,
        helped=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "moon_meadow": Setting(
        id="moon_meadow",
        place="the Moon Meadow",
        opening="A semi-circle of pearl-white mushrooms shone around the meadow like a tiny crown.",
        path_detail="On the silver path, even the grass seemed to whisper that a feast of good hearts would soon begin.",
        feast="the Dewdrop Feast",
        ending="Before the sun rose high, they were laughing together on a mossy bench, and the whole meadow glowed warmer than gold.",
        tags={"meadow", "fairy"},
    ),
    "willow_gate": Setting(
        id="willow_gate",
        place="the Willow Gate",
        opening="A semi ring of old willow roots curved beside the lane, making a little doorway for the dawn.",
        path_detail="Blue moths drifted over the stream, and every leaf looked polished by moonlight.",
        feast="the Lantern Breakfast",
        ending="By the willow roots, the stream reflected two smiling faces and a sky growing pink with morning.",
        tags={"willow", "fairy"},
    ),
    "rose_hill": Setting(
        id="rose_hill",
        place="Rose Hill",
        opening="A semi-circle of roses nodded around the hilltop, each one carrying a bead of light like a secret jewel.",
        path_detail="The stone road wound upward to the hill hall where sweet music was already beginning.",
        feast="the Honey Hall Feast",
        ending="At the hilltop table, even the roses seemed to lean nearer, pleased by the kindness they had seen.",
        tags={"roses", "fairy"},
    ),
}

TROUBLES = {
    "cold": Trouble(
        id="cold",
        label="the cold",
        symptom="Its little shoulders shook, and the morning dew had soaked right through its fur.",
        request="I cannot stop shivering. Is there anything warm in the world for me?",
        need="warmth",
        result="Soon the shivering slowed, and the creature could breathe without trembling.",
        risk="Without warmth, the creature would have stayed miserable in the chill dawn.",
        tags={"cold", "warmth"},
    ),
    "hungry": Trouble(
        id="hungry",
        label="hunger",
        symptom="Its basket was empty, and its voice came out small and hollow.",
        request="I have walked all night and have not had a bite. Is there anything to eat?",
        need="food",
        result="Soon the creature's eyes brightened, and its weak little steps turned springy again.",
        risk="Without food, the creature would have reached the feast tired and unhappy.",
        tags={"hungry", "food"},
    ),
    "dark": Trouble(
        id="dark",
        label="fear of the dark path",
        symptom="It kept staring into the fir trees, where the shadows looked deep and unfriendly.",
        request="I am afraid to cross the dark part of the wood alone. Is there a light for the way?",
        need="light",
        result="Soon the shadows no longer felt cruel, and the path ahead looked small enough to cross.",
        risk="Without light, the creature would have stayed frozen by the dark wood.",
        tags={"dark", "light"},
    ),
}

GIFTS = {
    "scarf": Gift(
        id="scarf",
        label="a red scarf",
        phrase="a red scarf folded soft as a poppy petal",
        helps={"warmth"},
        share_verb="wrapped the red scarf around the creature's shoulders",
        result="The scarf held the dawn wind back at once.",
        magical_return="In thanks, a wind no colder than a sigh pushed them along the quickest path, so they lost no time at all.",
        tags={"scarf", "warmth"},
    ),
    "cake": Gift(
        id="cake",
        label="a honey cake",
        phrase="a honey cake on a leaf-green plate",
        helps={"food"},
        share_verb="broke the honey cake in half and gave the sweeter half away",
        result="The honey smelled of clover and sun, and not a crumb was wasted.",
        magical_return="In thanks, the sparrows dropped shining berries into the empty plate until it looked festive again.",
        tags={"cake", "food"},
    ),
    "lantern": Gift(
        id="lantern",
        label="a firefly lantern",
        phrase="a firefly lantern with a moon-bright handle",
        helps={"light"},
        share_verb="lifted the firefly lantern high and offered to walk beside the creature",
        result="The lantern painted a soft gold road between the trees.",
        magical_return="In thanks, the fireflies gathered into an even brighter ribbon and guided them straight to the feast doors.",
        tags={"lantern", "light"},
    ),
}

CREATURES = {
    "rabbit": CreatureCfg(
        id="rabbit",
        phrase="a rabbit in a little fern cloak",
        type="rabbit",
        title="the rabbit",
        tags={"rabbit"},
    ),
    "hedgehog": CreatureCfg(
        id="hedgehog",
        phrase="a hedgehog no taller than a teapot",
        type="hedgehog",
        title="the hedgehog",
        tags={"hedgehog"},
    ),
    "fawn": CreatureCfg(
        id="fawn",
        phrase="a young fawn with silver spots",
        type="fawn",
        title="the fawn",
        tags={"fawn"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Tansy", "Lila", "Nora", "Wren", "Iris", "Poppy"]
BOY_NAMES = ["Aren", "Tobin", "Rowan", "Finn", "Milo", "Bram", "Ellis", "Oren"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    creature: str
    trouble: str
    gift: str
    hero_name: str
    hero_gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="moon_meadow",
        creature="rabbit",
        trouble="cold",
        gift="scarf",
        hero_name="Elin",
        hero_gender="girl",
        parent="mother",
    ),
    StoryParams(
        setting="willow_gate",
        creature="hedgehog",
        trouble="hungry",
        gift="cake",
        hero_name="Rowan",
        hero_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="rose_hill",
        creature="fawn",
        trouble="dark",
        gift="lantern",
        hero_name="Mira",
        hero_gender="girl",
        parent="mother",
    ),
    StoryParams(
        setting="moon_meadow",
        creature="hedgehog",
        trouble="dark",
        gift="lantern",
        hero_name="Oren",
        hero_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="rose_hill",
        creature="rabbit",
        trouble="hungry",
        gift="cake",
        hero_name="Poppy",
        hero_gender="girl",
        parent="mother",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "warmth": [
        (
            "Why does a scarf help when someone is cold?",
            "A scarf helps because it holds warm air close to the body and keeps chilly wind away. That makes it easier to stop shivering.",
        )
    ],
    "food": [
        (
            "Why does food help a tired traveler?",
            "Food gives the body energy to move and think. After eating, a tired traveler usually feels stronger and steadier.",
        )
    ],
    "light": [
        (
            "Why can a lantern make a dark path feel safer?",
            "A lantern lets you see where the path goes and what is around you. When you can see, the dark feels less mysterious and less scary.",
        )
    ],
    "scarf": [
        (
            "What is a scarf?",
            "A scarf is a long piece of cloth you wrap around your neck or shoulders for warmth. It can help block cold wind.",
        )
    ],
    "cake": [
        (
            "What is a honey cake?",
            "A honey cake is a sweet baked treat made with honey. In a fairy tale, it often feels like a small gift of comfort.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light you carry with you. It helps people see in dark places.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help or comfort someone, even when you do not have to. A kind act can make another person's hard moment easier.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kindness", "warmth", "food", "light", "scarf", "cake", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    gift = f["gift_cfg"]
    setting = f["setting"]
    creature = f["creature_cfg"]
    return [
        'Write a short fairy tale for a 3-to-5-year-old that includes the words "semi" and "episode" and centers on kindness.',
        f"Tell a gentle fairy tale where {hero.id} is on the way to {setting.feast} in {setting.place} and stops to help {creature.title} with {trouble.label}.",
        f"Write a simple story in which {gift.label} becomes a tool of kindness, and the ending proves that helping first was the right choice.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    creature = f["creature"]
    trouble = f["trouble"]
    gift = f["gift_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was walking to {setting.feast}, and {creature.label}, who needed help on the path.",
        ),
        (
            "What problem did the creature have?",
            f"{creature.label.capitalize()} was struggling with {trouble.label}. {trouble.risk}",
        ),
        (
            f"How did {hero.id} help?",
            f"{hero.id} used {gift.label} to help. {gift.result} {trouble.result}",
        ),
        (
            "Why was that a kind thing to do?",
            f"It was kind because {hero.id} stopped on the way to something special and paid attention to someone else's trouble. The help matched the need, so the creature truly felt better.",
        ),
        (
            "How did the story end?",
            f"It ended with both of them reaching {setting.feast} together. The closing image shows that kindness made the morning brighter for more than one person.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"kindness"}
    trouble = f["trouble"]
    gift = f["gift_cfg"]
    if trouble.need == "warmth":
        tags.add("warmth")
    elif trouble.need == "food":
        tags.add("food")
    elif trouble.need == "light":
        tags.add("light")
    tags |= set(gift.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(T, G) :- needs(T, N), helps(G, N).
valid(S, C, T, G) :- setting(S), creature(C), trouble(T), gift(G), fits(T, G).
happy(T, G) :- fits(T, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for creature_id in CREATURES:
        lines.append(asp.fact("creature", creature_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("needs", trouble_id, trouble.need))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for need in sorted(gift.helps):
            lines.append(asp.fact("helps", gift_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    # Smoke-test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story or "{" in sample.story or "}" in sample.story:
            raise StoryError("Generated story is empty or contains unresolved braces.")
        print("OK: smoke-test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld of kindness: a child helps a creature with the right gift."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.gift:
        trouble = TROUBLES[args.trouble]
        gift = GIFTS[args.gift]
        if not can_help(trouble, gift):
            raise StoryError(explain_rejection(trouble, gift))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.creature is None or combo[1] == args.creature)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.gift is None or combo[3] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, creature_id, trouble_id, gift_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        creature=creature_id,
        trouble=trouble_id,
        gift=gift_id,
        hero_name=hero_name,
        hero_gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")

    trouble = TROUBLES[params.trouble]
    gift = GIFTS[params.gift]
    if not can_help(trouble, gift):
        raise StoryError(explain_rejection(trouble, gift))

    world = tell(
        setting=SETTINGS[params.setting],
        creature_cfg=CREATURES[params.creature],
        trouble=trouble,
        gift=gift,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, creature, trouble, gift) combos:\n")
        for setting_id, creature_id, trouble_id, gift_id in combos:
            print(f"  {setting_id:12} {creature_id:10} {trouble_id:8} {gift_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name}: {p.trouble} helped by {p.gift} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
