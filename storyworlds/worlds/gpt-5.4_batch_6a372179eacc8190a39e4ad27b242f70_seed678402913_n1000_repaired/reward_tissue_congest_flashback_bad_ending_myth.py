#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reward_tissue_congest_flashback_bad_ending_myth.py
==============================================================================

A standalone story world for a small mythic tale about a child, a promised
reward, and a sky spirit with a congested nose. The world model tracks whether
the child helps quickly with a soothing tissue or lingers over the reward long
enough for the spirit's sickness to turn into a disaster.

The story shape is deliberately narrow:

- a village posts a reward for help
- a child learns that a spirit is congested
- an elder tells a flashback about an earlier season of trouble
- the child chooses whether to help first or think about the reward first
- the tissue either soothes the spirit in time or fails, causing a bad ending

Run it
------
    python storyworlds/worlds/gpt-5.4/reward_tissue_congest_flashback_bad_ending_myth.py
    python storyworlds/worlds/gpt-5.4/reward_tissue_congest_flashback_bad_ending_myth.py --spirit cloud_stag --irritant ash --tissue moonlinen --choice help_first
    python storyworlds/worlds/gpt-5.4/reward_tissue_congest_flashback_bad_ending_myth.py --tissue rough_bark --choice claim_reward_first
    python storyworlds/worlds/gpt-5.4/reward_tissue_congest_flashback_bad_ending_myth.py --all
    python storyworlds/worlds/gpt-5.4/reward_tissue_congest_flashback_bad_ending_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/reward_tissue_congest_flashback_bad_ending_myth.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
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
        }.get(self.type, self.type)


@dataclass
class Spirit:
    id: str
    name: str
    title: str
    home: str
    body: str
    breath: str
    sneeze: str
    base_severity: int
    flashback: str
    sensitivities: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Irritant:
    id: str
    label: str
    phrase: str
    source: str
    strength: int
    tags: set[str] = field(default_factory=set)


@dataclass
class TissueCfg:
    id: str
    label: str
    phrase: str
    softness: int
    coolness: int
    blessed: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class RewardCfg:
    id: str
    label: str
    phrase: str
    shine: str
    desire: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ChoiceCfg:
    id: str
    label: str
    delay: int
    greedy: bool
    line: str
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


def _r_spirit_pressure(world: World) -> list[str]:
    spirit = world.get("spirit")
    if spirit.meters["congested"] < THRESHOLD or spirit.meters["soothed"] >= THRESHOLD:
        return []
    sig = ("pressure", int(spirit.meters["congested"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sky = world.get("sky")
    river = world.get("river")
    sky.meters["danger"] += 1
    river.meters["blocked"] += 1
    hero = world.get("hero")
    hero.memes["fear"] += 1
    return ["__pressure__"]


def _r_clearing(world: World) -> list[str]:
    spirit = world.get("spirit")
    if spirit.meters["soothed"] < THRESHOLD:
        return []
    sig = ("clearing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("sky").meters["danger"] = 0.0
    world.get("river").meters["blocked"] = 0.0
    hero = world.get("hero")
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spirit_pressure", tag="physical", apply=_r_spirit_pressure),
    Rule(name="clearing", tag="physical", apply=_r_clearing),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SPIRITS = {
    "cloud_stag": Spirit(
        id="cloud_stag",
        name="the Cloud Stag",
        title="horned keeper of high rain",
        home="the stone hill above the village",
        body="muzzle",
        breath="misty breath",
        sneeze="hurled cold rain and loose reeds down the valley",
        base_severity=2,
        flashback="When I was small, the Cloud Stag sneezed for three nights, and the footbridge floated away before dawn.",
        sensitivities={"pollen", "ash"},
        tags={"spirit", "rain", "myth"},
    ),
    "river_lion": Spirit(
        id="river_lion",
        name="the River Lion",
        title="gold-maned watcher of the ford",
        home="the cave beside the ford",
        body="nose",
        breath="wet river breath",
        sneeze="kicked mud into the current and rolled logs across the ford",
        base_severity=1,
        flashback="I remember the year the River Lion could not breathe well; the boats waited in a sad line because no one could cross.",
        sensitivities={"reed_fluff", "ash"},
        tags={"spirit", "river", "myth"},
    ),
    "dawn_crane": Spirit(
        id="dawn_crane",
        name="the Dawn Crane",
        title="long-beaked herald of morning light",
        home="the cedar shrine on the eastern ridge",
        body="beak",
        breath="thin silver breath",
        sneeze="shook seeds and twigs into the water channels below",
        base_severity=2,
        flashback="Long ago, when the Dawn Crane sneezed at sunrise, the fields stayed dim and hungry for a whole week.",
        sensitivities={"pollen", "dust"},
        tags={"spirit", "sunrise", "myth"},
    ),
}

IRRITANTS = {
    "pollen": Irritant(
        id="pollen",
        label="pollen",
        phrase="gold pollen",
        source="the blown crowns of hillside flowers",
        strength=1,
        tags={"pollen", "spring"},
    ),
    "ash": Irritant(
        id="ash",
        label="ash",
        phrase="gray ash",
        source="the cooking fires of the festival night",
        strength=2,
        tags={"ash", "smoke"},
    ),
    "reed_fluff": Irritant(
        id="reed_fluff",
        label="reed fluff",
        phrase="reed fluff",
        source="the dry reed beds beside the water",
        strength=1,
        tags={"reed", "river"},
    ),
    "dust": Irritant(
        id="dust",
        label="dust",
        phrase="cedar dust",
        source="the old cedar steps up the ridge",
        strength=1,
        tags={"dust", "shrine"},
    ),
}

TISSUES = {
    "moonlinen": TissueCfg(
        id="moonlinen",
        label="moonlinen tissue",
        phrase="a fold of moonlinen tissue",
        softness=2,
        coolness=2,
        blessed=True,
        tags={"tissue", "cloth", "blessing"},
    ),
    "reed_silk": TissueCfg(
        id="reed_silk",
        label="reed-silk tissue",
        phrase="a reed-silk tissue",
        softness=1,
        coolness=1,
        blessed=False,
        tags={"tissue", "cloth"},
    ),
    "snow_herb": TissueCfg(
        id="snow_herb",
        label="snow-herb tissue",
        phrase="a snow-herb tissue",
        softness=1,
        coolness=2,
        blessed=True,
        tags={"tissue", "herb"},
    ),
    "rough_bark": TissueCfg(
        id="rough_bark",
        label="rough bark tissue",
        phrase="a rough bark tissue",
        softness=0,
        coolness=1,
        blessed=False,
        tags={"tissue", "bark"},
    ),
}

REWARDS = {
    "bell": RewardCfg(
        id="bell",
        label="copper bell",
        phrase="a copper bell from the shrine door",
        shine="it flashed like a little sunset",
        desire=2,
        tags={"reward", "bell"},
    ),
    "honey_cake": RewardCfg(
        id="honey_cake",
        label="honey cake",
        phrase="a round honey cake wrapped in leaves",
        shine="it smelled warm and sweet",
        desire=1,
        tags={"reward", "food"},
    ),
    "ribbon": RewardCfg(
        id="ribbon",
        label="sun ribbon",
        phrase="a sun-yellow ribbon braided with beads",
        shine="it glittered whenever it moved",
        desire=2,
        tags={"reward", "gift"},
    ),
}

CHOICES = {
    "help_first": ChoiceCfg(
        id="help_first",
        label="help first",
        delay=0,
        greedy=False,
        line="The child tucked the thought of the reward behind one brave breath and climbed at once.",
        tags={"kindness"},
    ),
    "claim_reward_first": ChoiceCfg(
        id="claim_reward_first",
        label="claim reward first",
        delay=1,
        greedy=True,
        line="The child stopped at the reward table and asked who would count the gift before any climbing was done.",
        tags={"greed"},
    ),
}


def spirit_can_congest(spirit: Spirit, irritant: Irritant) -> bool:
    return irritant.id in spirit.sensitivities


def tissue_is_reasonable(tissue: TissueCfg) -> bool:
    return tissue.softness + tissue.coolness > 0


def relief_power(tissue: TissueCfg) -> int:
    return tissue.softness + tissue.coolness


def congestion_severity(spirit: Spirit, irritant: Irritant) -> int:
    return spirit.base_severity + irritant.strength


def outcome_from_choice(spirit: Spirit, irritant: Irritant,
                        tissue: TissueCfg, choice: ChoiceCfg) -> str:
    if choice.delay > 0:
        return "bad"
    return "soothed" if relief_power(tissue) >= congestion_severity(spirit, irritant) else "bad"


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for spirit_id, spirit in SPIRITS.items():
        for irritant_id, irritant in IRRITANTS.items():
            if not spirit_can_congest(spirit, irritant):
                continue
            for tissue_id, tissue in TISSUES.items():
                if not tissue_is_reasonable(tissue):
                    continue
                for reward_id in REWARDS:
                    out.append((spirit_id, irritant_id, tissue_id, reward_id))
    return out


def predict_outcome(world: World, tissue: TissueCfg, choice: ChoiceCfg) -> dict:
    sim = world.copy()
    spirit = sim.get("spirit")
    if choice.delay > 0:
        spirit.meters["congested"] += 1
        propagate(sim, narrate=False)
    if relief_power(tissue) >= sim.facts["severity"]:
        spirit.meters["soothed"] += 1
        propagate(sim, narrate=False)
    return {
        "danger": sim.get("sky").meters["danger"],
        "blocked": sim.get("river").meters["blocked"],
        "safe": sim.get("sky").meters["danger"] < THRESHOLD and sim.get("river").meters["blocked"] < THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, spirit: Spirit, reward: RewardCfg) -> None:
    world.say(
        f"Long ago, when hills still listened and water still answered songs, {hero.id} lived in a valley watched by {spirit.name}, the {spirit.title}."
    )
    world.say(
        f"One market morning, a crier tied a notice to the fig tree and promised a reward: {reward.phrase}. {reward.shine}, and every child in the square looked twice."
    )
    hero.memes["wonder"] += 1
    hero.memes["desire"] += float(reward.desire)
    elder.memes["care"] += 1


def signs_of_trouble(world: World, hero: Entity, spirit: Spirit, irritant: Irritant) -> None:
    spirit_ent = world.get("spirit")
    spirit_ent.meters["congested"] = float(world.facts["severity"])
    propagate(world, narrate=False)
    world.say(
        f"By noon, word came from {spirit.home}: {spirit.name} had breathed in {irritant.phrase} from {irritant.source}, and now {spirit.pronoun('possessive')} {spirit.body} was so congest that {spirit.pronoun()} could hardly send out {spirit.breath}."
    )
    world.say(
        f"When {hero.id} looked up, the clouds above the ridge sat low and uneasy, as if the whole sky were holding a sneeze."
    )
    hero.memes["pity"] += 1


def tell_flashback(world: World, elder: Entity, spirit: Spirit) -> None:
    elder.memes["memory"] += 1
    world.say(
        f"{elder.id} touched {elder.pronoun('possessive')} walking stick and spoke in the old village voice. \"{spirit.flashback}\""
    )
    world.say(
        "The words felt like a flashback laid over the afternoon, and even the goats near the well stood still."
    )


def choose_path(world: World, hero: Entity, choice: ChoiceCfg, reward: RewardCfg) -> None:
    if choice.greedy:
        hero.memes["greed"] += 1
    else:
        hero.memes["resolve"] += 1
    world.say(choice.line)
    if choice.greedy:
        world.say(
            f"{hero.id}'s eyes slipped once more to the promised reward, and that small pause made the air feel tighter."
        )


def offer_tissue(world: World, hero: Entity, spirit: Spirit, tissue: TissueCfg) -> None:
    world.say(
        f"At the ridge, {hero.id} knelt beside {spirit.name} and lifted {tissue.phrase}. \"Here,\" {hero.pronoun()} whispered, \"let this cool your poor {spirit.body}.\""
    )


def soothe(world: World, hero: Entity, spirit: Spirit, tissue: TissueCfg) -> None:
    spirit_ent = world.get("spirit")
    spirit_ent.meters["soothed"] += 1
    spirit_ent.meters["congested"] = 0.0
    propagate(world, narrate=False)
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"The tissue was soft and cool. {spirit.name} pressed it to {spirit.pronoun('possessive')} {spirit.body}, drew one long breath, and the hard sound inside {spirit.pronoun('possessive')} chest melted away."
    )
    world.say(
        f"Then {spirit.pronoun().capitalize()} shook {spirit.pronoun('possessive')} head, sent a clean bright wind over the valley, and the river ran clear again."
    )
    world.say(
        f"The promised reward still waited in the square, but now it felt smaller than the sight of light returning to the fields."
    )


def fail_delay(world: World, hero: Entity, spirit: Spirit, reward: RewardCfg) -> None:
    spirit_ent = world.get("spirit")
    spirit_ent.meters["congested"] += 1
    propagate(world, narrate=False)
    hero.memes["fear"] += 1
    world.say(
        f"But while {hero.id} lingered over {reward.phrase}, {spirit.name}'s breathing worsened."
    )


def fail_weak_tissue(world: World, hero: Entity, spirit: Spirit, tissue: TissueCfg) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} did reach the ridge at last, yet {tissue.phrase} was too rough and too thin for so sick a spirit."
    )


def bad_ending(world: World, hero: Entity, spirit: Spirit) -> None:
    spirit_ent = world.get("spirit")
    sky = world.get("sky")
    river = world.get("river")
    spirit_ent.meters["storm"] += 1
    sky.meters["danger"] += 1
    river.meters["blocked"] += 1
    hero.memes["sorrow"] += 1
    world.say(
        f"Then {spirit.name} sneezed. The blast {spirit.sneeze}, and broken reeds jammed the narrow mouth of the river until boats, baskets, and driftwood began to congest the water there."
    )
    world.say(
        "The fields below stayed thirsty, the market songs went quiet, and the reward was never given. That night the village ate plain broth and listened to the blocked water knock sadly against the bank."
    )
    world.say(
        f"{hero.id} lay awake and understood too late that a shining gift is a poor guide when someone needs help first."
    )


def tell_story(spirit: Spirit, irritant: Irritant, tissue: TissueCfg, reward: RewardCfg,
               choice: ChoiceCfg, hero_name: str, hero_gender: str,
               elder_name: str, elder_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    spirit_ent = world.add(Entity(id="spirit", kind="character", type="spirit", label=spirit.name, role="spirit"))
    world.add(Entity(id="sky", type="sky", label="the sky"))
    world.add(Entity(id="river", type="river", label="the river"))
    world.add(Entity(id="reward", type="reward", label=reward.label))
    world.add(Entity(id="tissue", type="tissue", label=tissue.label))

    severity = congestion_severity(spirit, irritant)
    predicted = outcome_from_choice(spirit, irritant, tissue, choice)
    world.facts["severity"] = severity
    world.facts["predicted_outcome"] = predicted

    introduce(world, hero, elder, spirit, reward)
    world.para()
    signs_of_trouble(world, hero, spirit, irritant)
    tell_flashback(world, elder, spirit)

    world.para()
    predict = predict_outcome(world, tissue, choice)
    world.facts["predicted_danger"] = predict["danger"]
    world.facts["predicted_blocked"] = predict["blocked"]
    choose_path(world, hero, choice, reward)
    offer_tissue(world, hero, spirit, tissue)

    world.para()
    if choice.delay > 0:
        fail_delay(world, hero, spirit, reward)
        bad_ending(world, hero, spirit)
        outcome = "bad"
    elif relief_power(tissue) < severity:
        fail_weak_tissue(world, hero, spirit, tissue)
        bad_ending(world, hero, spirit)
        outcome = "bad"
    else:
        soothe(world, hero, spirit, tissue)
        outcome = "soothed"

    world.facts.update(
        hero=hero,
        elder=elder,
        spirit_cfg=spirit,
        irritant=irritant,
        tissue_cfg=tissue,
        reward_cfg=reward,
        choice_cfg=choice,
        outcome=outcome,
        spirit_entity=spirit_ent,
        reward_seen=hero.memes["desire"] >= THRESHOLD,
        greedy=choice.greedy,
        flashback=True,
        river_blocked=world.get("river").meters["blocked"] >= THRESHOLD,
        sky_danger=world.get("sky").meters["danger"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    spirit: str
    irritant: str
    tissue: str
    reward: str
    choice: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        spirit="cloud_stag",
        irritant="pollen",
        tissue="moonlinen",
        reward="bell",
        choice="help_first",
        hero_name="Nila",
        hero_gender="girl",
        elder_name="Grandmother Sera",
        elder_type="grandmother",
    ),
    StoryParams(
        spirit="river_lion",
        irritant="reed_fluff",
        tissue="reed_silk",
        reward="honey_cake",
        choice="help_first",
        hero_name="Tarin",
        hero_gender="boy",
        elder_name="Grandfather Om",
        elder_type="grandfather",
    ),
    StoryParams(
        spirit="dawn_crane",
        irritant="ash",
        tissue="snow_herb",
        reward="ribbon",
        choice="claim_reward_first",
        hero_name="Mira",
        hero_gender="girl",
        elder_name="Grandmother Evi",
        elder_type="grandmother",
    ),
    StoryParams(
        spirit="cloud_stag",
        irritant="ash",
        tissue="rough_bark",
        reward="bell",
        choice="help_first",
        hero_name="Ivo",
        hero_gender="boy",
        elder_name="Grandfather Sen",
        elder_type="grandfather",
    ),
    StoryParams(
        spirit="dawn_crane",
        irritant="pollen",
        tissue="snow_herb",
        reward="honey_cake",
        choice="help_first",
        hero_name="Luma",
        hero_gender="girl",
        elder_name="Grandmother Nera",
        elder_type="grandmother",
    ),
]

GIRL_NAMES = ["Nila", "Mira", "Luma", "Ari", "Sela", "Tavi", "Rina", "Yara"]
BOY_NAMES = ["Tarin", "Ivo", "Pavel", "Noren", "Sami", "Darin", "Kio", "Milo"]
ELDER_GIRLISH = ["Grandmother Sera", "Grandmother Evi", "Grandmother Nera", "Grandmother Tala"]
ELDER_BOYISH = ["Grandfather Om", "Grandfather Sen", "Grandfather Iri", "Grandfather Vale"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    spirit = f["spirit_cfg"]
    irritant = f["irritant"]
    tissue = f["tissue_cfg"]
    reward = f["reward_cfg"]
    choice = f["choice_cfg"]
    if f["outcome"] == "bad":
        return [
            f'Write a short child-facing myth that includes the words "reward", "tissue", and "congest".',
            f"Tell a myth where {hero.id} hears a flashback warning about {spirit.name}, but trouble grows after a promised reward pulls at the child's attention.",
            f"Write a sad myth in which {irritant.label} leaves a spirit congested, {tissue.label} does not help in time, and the ending shows the cost of delay.",
        ]
    return [
        f'Write a short child-facing myth that includes the words "reward", "tissue", and "congest".',
        f"Tell a myth where {hero.id} hurries past a promised reward to carry a tissue up to {spirit.name}, after hearing an elder's flashback.",
        f"Write a gentle myth in which {irritant.label} leaves a spirit congested, but kindness comes before treasure and the valley is saved.",
    ]


def pair_title(hero: Entity, elder: Entity) -> str:
    return f"{hero.id} and {elder.id}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    spirit = f["spirit_cfg"]
    irritant = f["irritant"]
    tissue = f["tissue_cfg"]
    reward = f["reward_cfg"]
    choice = f["choice_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {elder.id}, and {spirit.name}. The village is waiting to see whether {hero.id} will chase the reward or help the spirit first.",
        ),
        (
            f"Why was {spirit.name} in trouble?",
            f"{spirit.name} breathed in {irritant.phrase} from {irritant.source}, and that left {spirit.pronoun('possessive')} {spirit.body} badly congested. Because the spirit guided weather and water, the whole valley felt the sickness too.",
        ),
        (
            "What was the flashback for?",
            f"{elder.id} remembered an older season when the same spirit's sickness hurt the village. The flashback warned {hero.id} that this trouble was not small and could grow if help came late.",
        ),
        (
            f"What choice stood before {hero.id}?",
            f"{hero.id} could think first about {reward.phrase} or hurry up the ridge with {tissue.phrase}. That choice mattered because even a short delay let the danger grow.",
        ),
    ]
    if f["outcome"] == "soothed":
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.id} brought {tissue.phrase} to {spirit.name} right away, and the soft cool cloth soothed the spirit enough to clear {spirit.pronoun('possessive')} breath. Helping first mattered more than the reward, so the river and sky calmed again.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with clear water, bright fields, and a village that could sing again. The ending proves that kindness came before treasure and changed the whole valley.",
            )
        )
    else:
        reason = "the child delayed over the reward" if choice.delay > 0 else "the tissue was too rough and weak"
        qa.append(
            (
                "Why did the ending turn bad?",
                f"The ending turned bad because {reason}. That failure left the spirit congested long enough for the sneeze to strike the valley.",
            )
        )
        qa.append(
            (
                "What happened after the spirit sneezed?",
                f"Reeds and broken things clogged the river mouth, and boats, baskets, and driftwood began to congest the water. The market fell quiet because the blocked river and thirsty fields showed the cost of the mistake.",
            )
        )
    return qa


KNOWLEDGE = {
    "tissue": [
        (
            "What is a tissue?",
            "A tissue is a soft piece of cloth or paper used to wipe tears or a runny nose. A gentle tissue can help someone feel cleaner and more comfortable.",
        )
    ],
    "pollen": [
        (
            "What is pollen?",
            "Pollen is fine dust made by flowers. Wind can carry it through the air, and sometimes it tickles noses and makes breathing harder.",
        )
    ],
    "ash": [
        (
            "What is ash?",
            "Ash is the soft gray powder left after something burns. It can float in the air and bother eyes, noses, and throats.",
        )
    ],
    "reed": [
        (
            "What are reeds?",
            "Reeds are tall water plants that grow beside rivers and ponds. When they break loose, they can gather in thick clumps.",
        )
    ],
    "river": [
        (
            "Why is a blocked river a problem?",
            "A blocked river cannot carry water along properly. Boats may get stuck, and the land below may not get the water it needs.",
        )
    ],
    "reward": [
        (
            "What is a reward?",
            "A reward is a gift or prize given after someone does something helpful or brave. It should never matter more than helping someone who needs care right away.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story people tell to explain the world, teach a lesson, or remember something important. Myths often use spirits, signs, and big feelings to show their meaning.",
        )
    ],
    "blessing": [
        (
            "What does blessed mean in a story?",
            "In a story, something blessed is believed to carry special goodness or help from a holy place or kind power. It often means the object is meant to heal, protect, or guide.",
        )
    ],
}
KNOWLEDGE_ORDER = ["myth", "reward", "tissue", "pollen", "ash", "reed", "river", "blessing"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"myth", "reward", "tissue"}
    tags |= set(f["irritant"].tags)
    tags |= set(f["tissue_cfg"].tags)
    tags |= set(f["spirit_cfg"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(spirit: Spirit, irritant: Irritant) -> str:
    return (
        f"(No story: {irritant.label} is not a believable thing to leave {spirit.name} congested in this little myth. Pick an irritant the spirit is sensitive to.)"
    )


def explain_tissue(tissue: TissueCfg) -> str:
    return (
        f"(No story: {tissue.label} is not really a usable tissue here. Pick a cloth or herb tissue with at least some softness or coolness.)"
    )


ASP_RULES = r"""
hazard(S, I) :- sensitive(S, I).
usable_tissue(T) :- tissue(T), softness(T, Sf), coolness(T, Cl), Sf + Cl > 0.
valid(S, I, T, R) :- spirit(S), irritant(I), tissue(T), reward(R), hazard(S, I), usable_tissue(T).

severity(V) :- chosen_spirit(S), base_severity(S, B), chosen_irritant(I), strength(I, K), V = B + K.
relief(V) :- chosen_tissue(T), softness(T, S), coolness(T, C), V = S + C.
delayed :- chosen_choice(C), delay(C, D), D > 0.
bad :- delayed.
bad :- severity(V), relief(R), not delayed, R < V.
outcome(bad) :- bad.
outcome(soothed) :- not bad.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, spirit in SPIRITS.items():
        lines.append(asp.fact("spirit", sid))
        lines.append(asp.fact("base_severity", sid, spirit.base_severity))
        for irr in sorted(spirit.sensitivities):
            lines.append(asp.fact("sensitive", sid, irr))
    for iid, irritant in IRRITANTS.items():
        lines.append(asp.fact("irritant", iid))
        lines.append(asp.fact("strength", iid, irritant.strength))
    for tid, tissue in TISSUES.items():
        lines.append(asp.fact("tissue", tid))
        lines.append(asp.fact("softness", tid, tissue.softness))
        lines.append(asp.fact("coolness", tid, tissue.coolness))
    for rid in REWARDS:
        lines.append(asp.fact("reward", rid))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("delay", cid, choice.delay))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_spirit", params.spirit),
            asp.fact("chosen_irritant", params.irritant),
            asp.fact("chosen_tissue", params.tissue),
            asp.fact("chosen_choice", params.choice),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for s in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)

    mismatches = 0
    for params in cases:
        py = outcome_from_choice(
            SPIRITS[params.spirit],
            IRRITANTS[params.irritant],
            TISSUES[params.tissue],
            CHOICES[params.choice],
        )
        cl = asp_outcome(params)
        if py != cl:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a mythic child, a promised reward, and a congested spirit."
    )
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--irritant", choices=IRRITANTS)
    ap.add_argument("--tissue", choices=TISSUES)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spirit and args.irritant:
        spirit = SPIRITS[args.spirit]
        irritant = IRRITANTS[args.irritant]
        if not spirit_can_congest(spirit, irritant):
            raise StoryError(explain_rejection(spirit, irritant))
    if args.tissue:
        tissue = TISSUES[args.tissue]
        if not tissue_is_reasonable(tissue):
            raise StoryError(explain_tissue(tissue))

    combos = [
        combo for combo in valid_combos()
        if (args.spirit is None or combo[0] == args.spirit)
        and (args.irritant is None or combo[1] == args.irritant)
        and (args.tissue is None or combo[2] == args.tissue)
        and (args.reward is None or combo[3] == args.reward)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spirit_id, irritant_id, tissue_id, reward_id = rng.choice(sorted(combos))
    choice_id = args.choice or rng.choice(sorted(CHOICES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    elder_name_pool = ELDER_GIRLISH if elder_type == "grandmother" else ELDER_BOYISH
    elder_name = args.elder_name or rng.choice(elder_name_pool)

    return StoryParams(
        spirit=spirit_id,
        irritant=irritant_id,
        tissue=tissue_id,
        reward=reward_id,
        choice=choice_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spirit not in SPIRITS:
        raise StoryError(f"(Unknown spirit '{params.spirit}')")
    if params.irritant not in IRRITANTS:
        raise StoryError(f"(Unknown irritant '{params.irritant}')")
    if params.tissue not in TISSUES:
        raise StoryError(f"(Unknown tissue '{params.tissue}')")
    if params.reward not in REWARDS:
        raise StoryError(f"(Unknown reward '{params.reward}')")
    if params.choice not in CHOICES:
        raise StoryError(f"(Unknown choice '{params.choice}')")

    spirit = SPIRITS[params.spirit]
    irritant = IRRITANTS[params.irritant]
    tissue = TISSUES[params.tissue]
    reward = REWARDS[params.reward]
    choice = CHOICES[params.choice]

    if not spirit_can_congest(spirit, irritant):
        raise StoryError(explain_rejection(spirit, irritant))
    if not tissue_is_reasonable(tissue):
        raise StoryError(explain_tissue(tissue))

    world = tell_story(
        spirit=spirit,
        irritant=irritant,
        tissue=tissue,
        reward=reward,
        choice=choice,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} compatible (spirit, irritant, tissue, reward) combos:\n")
        for spirit_id, irritant_id, tissue_id, reward_id in combos:
            print(f"  {spirit_id:12} {irritant_id:10} {tissue_id:11} {reward_id}")
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
            outcome = outcome_from_choice(SPIRITS[p.spirit], IRRITANTS[p.irritant], TISSUES[p.tissue], CHOICES[p.choice])
            header = f"### {pair_title(sample.world.facts['hero'], sample.world.facts['elder'])}: {p.spirit}, {p.irritant}, {p.tissue}, {p.choice} ({outcome})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
