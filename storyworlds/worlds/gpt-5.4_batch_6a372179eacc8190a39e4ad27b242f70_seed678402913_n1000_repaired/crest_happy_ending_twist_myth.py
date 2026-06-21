#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crest_happy_ending_twist_myth.py
===========================================================

A standalone storyworld for a small mythic domain built from the seed word
"crest" with a happy-ending twist: a child climbs to a windy crest to face a
creature blamed for the valley's trouble, only to discover that the feared being
is wounded and trapped. By bringing the right offering and the right freeing
tool, the child helps the creature, and the valley receives the blessing it was
missing.

Run it
------
    python storyworlds/worlds/gpt-5.4/crest_happy_ending_twist_myth.py
    python storyworlds/worlds/gpt-5.4/crest_happy_ending_twist_myth.py --need orchard --creature cloud_ram
    python storyworlds/worlds/gpt-5.4/crest_happy_ending_twist_myth.py --creature dawn_hawk --tool shears
    python storyworlds/worlds/gpt-5.4/crest_happy_ending_twist_myth.py --all
    python storyworlds/worlds/gpt-5.4/crest_happy_ending_twist_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crest_happy_ending_twist_myth.py --verify
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
# from the repo root or from this nested subdirectory.
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
        female = {"girl", "woman", "mother", "goddess"}
        male = {"boy", "man", "father", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title(self) -> str:
        return self.label or self.id


@dataclass
class Need:
    id: str
    place: str = ""
    opening: str = ""
    lack: str = ""
    plea: str = ""
    solved_by: str = ""
    blessing_text: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str = ""
    epithet: str = ""
    rumor: str = ""
    truth: str = ""
    snag: str = ""
    crest_place: str = ""
    offering_ids: set[str] = field(default_factory=set)
    solves: str = ""
    blessing_line: str = ""
    release_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str = ""
    phrase: str = ""
    effect_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str = ""
    phrase: str = ""
    handles: set[str] = field(default_factory=set)
    action_line: str = ""
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


def _r_reveal_truth(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if creature is None:
        return []
    if creature.meters["offered"] < THRESHOLD or creature.meters["fearsome"] < THRESHOLD:
        return []
    sig = ("truth", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["trusted"] += 1
    creature.meters["fearsome"] = 0.0
    hero = world.entities.get("hero")
    if hero is not None:
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
        hero.memes["wonder"] += 1
    return ["__truth__"]


def _r_free_blessing(world: World) -> list[str]:
    creature = world.entities.get("creature")
    valley = world.entities.get("valley")
    if creature is None or valley is None:
        return []
    if creature.meters["freed"] < THRESHOLD or valley.meters["troubled"] < THRESHOLD:
        return []
    sig = ("blessing", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    valley.meters["troubled"] = 0.0
    valley.meters["healed"] += 1
    creature.meters["blessing_given"] += 1
    hero = world.entities.get("hero")
    if hero is not None:
        hero.memes["hope"] += 1
        hero.memes["joy"] += 1
    return ["__blessing__"]


CAUSAL_RULES = [
    Rule(name="reveal_truth", tag="social", apply=_r_reveal_truth),
    Rule(name="free_blessing", tag="physical", apply=_r_free_blessing),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


NEEDS = {
    "orchard": Need(
        id="orchard",
        place="the fig orchard below the hill",
        opening="All through the valley, the fig leaves had curled like little fists.",
        lack="The earth under the trees had gone pale and cracked, and the fruit stayed small and hard.",
        plea="rain",
        solved_by="cloud_ram",
        blessing_text="Rain poured over the orchard in a silver curtain, and the thirsty roots drank deeply.",
        ending_image="By evening the leaves shone green again, and figs hung round and sweet in the cool air.",
        tags={"rain", "orchard"},
    ),
    "dawn": Need(
        id="dawn",
        place="the valley roofs and fields",
        opening="For three mornings in a row, the valley had woken under a dim gray hush.",
        lack="Roosters crowed into the dark, and even the river looked sleepy without the sun on it.",
        plea="sunrise",
        solved_by="dawn_hawk",
        blessing_text="The eastern sky opened like a golden door, and warm light spilled across the valley.",
        ending_image="Soon every roof gleamed, and the children chased their shadows over the bright grass.",
        tags={"sun", "light"},
    ),
    "spring": Need(
        id="spring",
        place="the old mill stream",
        opening="At the old mill, the wheel had almost stopped.",
        lack="Only a thin ribbon of water slipped past the mossy stones, and the buckets came back light.",
        plea="water",
        solved_by="river_serpent",
        blessing_text="Clear water burst laughing from the stones and ran strong beneath the mill wheel.",
        ending_image="The wheel turned again, the buckets brimmed, and the whole bank glittered with spray.",
        tags={"river", "water"},
    ),
}

CREATURES = {
    "cloud_ram": CreatureCfg(
        id="cloud_ram",
        label="Cloud Ram",
        epithet="the horned keeper of rain",
        rumor="The old people said the Cloud Ram stamped on the high crest and locked the storm behind its curled horns.",
        truth="Yet on the crest the child found not anger but pain: silver wool was snarled in a crown of black thorns around an ancient stone.",
        snag="thorns",
        crest_place="the storm crest above the orchard",
        offering_ids={"clover_cake", "reed_flute"},
        solves="orchard",
        blessing_line="With a joyful toss of its head, the Cloud Ram shook rain from its fleece.",
        release_line="Freed at last, the ram bounded across the sky like a small white cloud come alive.",
        tags={"rain", "ram", "cloud"},
    ),
    "dawn_hawk": CreatureCfg(
        id="dawn_hawk",
        label="Dawn Hawk",
        epithet="the bright-winged opener of morning",
        rumor="The elders whispered that the Dawn Hawk had folded the morning under its wings and refused to let day begin.",
        truth="But on the crest the child saw that its fiery feathers were tangled in a net of night-reeds stretched between two standing stones.",
        snag="night_net",
        crest_place="the eastern crest above the valley",
        offering_ids={"sun_song", "reed_flute"},
        solves="dawn",
        blessing_line="The Dawn Hawk beat its wings once, and the horizon broke into gold.",
        release_line="Freed from the dark net, the hawk rose so high that even the cold clouds blushed.",
        tags={"sun", "hawk", "light"},
    ),
    "river_serpent": CreatureCfg(
        id="river_serpent",
        label="River Serpent",
        epithet="the long guardian of springs",
        rumor="Fisherfolk said the River Serpent had coiled around the mountain spring and swallowed the valley's water in its shining throat.",
        truth="But on the crest the child found the serpent pinned beneath a fallen ring of sacred stone, its scales bright with trapped water.",
        snag="stone_ring",
        crest_place="the wet crest above the mill stream",
        offering_ids={"shell_bowl", "sun_song"},
        solves="spring",
        blessing_line="The River Serpent arched free, and fresh water came dancing after it.",
        release_line="Freed from the stone, the serpent slipped through the spring like a ribbon of green glass.",
        tags={"river", "water", "serpent"},
    ),
}

OFFERINGS = {
    "clover_cake": Offering(
        id="clover_cake",
        label="clover cake",
        phrase="a round clover cake wrapped in leaves",
        effect_line="The sweet smell drifted upward, and the creature's wild eyes softened.",
        tags={"gift", "food"},
    ),
    "sun_song": Offering(
        id="sun_song",
        label="sun song",
        phrase="a little sun song remembered from the grandmothers",
        effect_line="The small song rose into the wind, and the creature grew still to listen.",
        tags={"gift", "song"},
    ),
    "shell_bowl": Offering(
        id="shell_bowl",
        label="shell bowl",
        phrase="a shell bowl full of clear spring water",
        effect_line="The bowl shone like a tiny moon, and the creature bent close with a grateful breath.",
        tags={"gift", "water"},
    ),
    "reed_flute": Offering(
        id="reed_flute",
        label="reed flute tune",
        phrase="a soft tune played on a reed flute",
        effect_line="The tune floated around the stones, and the creature answered with a quieter sound of its own.",
        tags={"gift", "music"},
    ),
}

TOOLS = {
    "shears": ToolCfg(
        id="shears",
        label="bronze shears",
        phrase="a pair of bronze shears from the shepherd's wall",
        handles={"thorns"},
        action_line="With steady hands, the child clipped the black thorns one by one.",
        tags={"tool", "cut"},
    ),
    "moon_knife": ToolCfg(
        id="moon_knife",
        label="moon-knife",
        phrase="a moon-bright knife from the shrine chest",
        handles={"night_net"},
        action_line="The child sliced the dark reeds apart, and the net loosened with a sigh.",
        tags={"tool", "cut"},
    ),
    "ash_staff": ToolCfg(
        id="ash_staff",
        label="ash staff",
        phrase="a forked ash staff smoothed by river water",
        handles={"stone_ring"},
        action_line="Bracing feet on the rock, the child levered the heavy stone ring inch by inch.",
        tags={"tool", "lift"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for need_id, need in NEEDS.items():
        for creature_id, creature in CREATURES.items():
            if creature.solves != need_id:
                continue
            for offering_id in creature.offering_ids:
                for tool_id, tool in TOOLS.items():
                    if creature.snag in tool.handles:
                        combos.append((need_id, creature_id, offering_id, tool_id))
    return sorted(combos)


@dataclass
class StoryParams:
    need: str
    creature: str
    offering: str
    tool: str
    hero_name: str
    hero_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        need="orchard",
        creature="cloud_ram",
        offering="clover_cake",
        tool="shears",
        hero_name="Tala",
        hero_gender="girl",
        elder_name="Grandmother Ione",
        elder_gender="woman",
    ),
    StoryParams(
        need="dawn",
        creature="dawn_hawk",
        offering="sun_song",
        tool="moon_knife",
        hero_name="Niko",
        hero_gender="boy",
        elder_name="Old Mara",
        elder_gender="woman",
    ),
    StoryParams(
        need="spring",
        creature="river_serpent",
        offering="shell_bowl",
        tool="ash_staff",
        hero_name="Eren",
        hero_gender="boy",
        elder_name="Grandfather Sen",
        elder_gender="man",
    ),
]

GIRL_NAMES = ["Tala", "Mira", "Lina", "Aya", "Rhea", "Sela", "Nora", "Iris"]
BOY_NAMES = ["Niko", "Eren", "Tomas", "Ivo", "Daro", "Lio", "Pavel", "Aren"]
ELDER_NAMES = {
    "woman": ["Grandmother Ione", "Old Mara", "Aunt Thale", "Wise Ena"],
    "man": ["Grandfather Sen", "Old Teren", "Uncle Damas", "Wise Orin"],
}


def tool_fits(creature: CreatureCfg, tool: ToolCfg) -> bool:
    return creature.snag in tool.handles


def offering_fits(creature: CreatureCfg, offering: Offering) -> bool:
    return offering.id in creature.offering_ids


def need_fits(need: Need, creature: CreatureCfg) -> bool:
    return creature.solves == need.id


def explain_rejection(need: Need, creature: CreatureCfg, offering: Offering, tool: ToolCfg) -> str:
    if not need_fits(need, creature):
        return (
            f"(No story: {creature.label} does not answer the valley's need for {need.plea}. "
            f"In this world, {creature.label} heals a different trouble.)"
        )
    if not offering_fits(creature, offering):
        return (
            f"(No story: {offering.label} would not calm {creature.label}. "
            f"The child needs an offering that the creature will trust.)"
        )
    if not tool_fits(creature, tool):
        return (
            f"(No story: {tool.label} cannot free {creature.label} from {creature.snag}. "
            f"The helping tool must match the trap.)"
        )
    return "(No story: this combination does not fit the mythic logic of the world.)"


def intro(world: World, hero: Entity, elder: Entity, need: Need, creature: CreatureCfg) -> None:
    valley = world.get("valley")
    hero.memes["care"] += 1
    hero.memes["hope"] += 1
    world.say(f"{need.opening} {need.lack}")
    world.say(
        f"In the evenings, {hero.id} sat beside {elder.id} and listened to the wind speak of "
        f"{creature.crest_place}."
    )
    world.say(creature.rumor)
    valley.meters["troubled"] += 1


def choose_quest(world: World, hero: Entity, elder: Entity, need: Need, offering: Offering, tool: ToolCfg) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f'"If the valley is waiting for {need.plea}," {hero.id} said, "then I will climb to the crest and ask for it."'
    )
    world.say(
        f"{elder.id} nodded and gave {hero.pronoun('object')} {offering.phrase} and {tool.phrase}. "
        f'"Go gently," {elder.pronoun()} said. "Many things that sound fierce are only hurting."'
    )


def climb(world: World, hero: Entity, creature: CreatureCfg) -> None:
    hero.meters["climbed"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"Up the path {hero.id} went, past bent pines and loose white stones, until the world narrowed to wind and sky."
    )
    world.say(
        f"At last {hero.pronoun()} reached the crest. There, against the clouds, a great shape moved, and {hero.pronoun()} nearly turned back."
    )
    creature_ent = world.get("creature")
    creature_ent.meters["fearsome"] += 1


def offer(world: World, hero: Entity, offering: Offering) -> None:
    creature = world.get("creature")
    creature.meters["offered"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"But {hero.id} remembered the elder's words, stepped forward, and offered {offering.phrase}."
    )
    world.say(offering.effect_line)
    propagate(world, narrate=False)


def reveal(world: World, creature: CreatureCfg) -> None:
    hero = world.get("hero")
    world.say(
        f"Then the truth came clear. {creature.truth}"
    )
    world.say(
        f"The creature was not guarding the blessing out of spite at all. It was trapped, and every harsh sound on the wind had been a cry for help."
    )
    hero.memes["fear"] = 0.0
    hero.memes["compassion"] += 1


def free_creature(world: World, hero: Entity, creature: CreatureCfg, tool: ToolCfg) -> None:
    creature_ent = world.get("creature")
    creature_ent.meters["snagged"] += 1
    world.say(
        f"{hero.id} set down the gift, took up the {tool.label}, and went close enough to feel the creature's breath."
    )
    world.say(tool.action_line)
    creature_ent.meters["snagged"] = 0.0
    creature_ent.meters["freed"] += 1
    hero.memes["wonder"] += 1
    propagate(world, narrate=False)


def bless(world: World, need: Need, creature: CreatureCfg) -> None:
    valley = world.get("valley")
    world.say(creature.release_line)
    world.say(creature.blessing_line)
    world.say(need.blessing_text)
    valley.meters["healed"] += 0  # touched by rule; keeps the physical state readable


def ending(world: World, hero: Entity, need: Need, creature: CreatureCfg) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"When {hero.id} came down from the crest, the valley people looked up in wonder."
    )
    world.say(
        f"They had expected a battle, but {hero.id} brought back a better tale: {creature.label} had never been their enemy."
    )
    world.say(need.ending_image)
    world.say(
        f"And from that day on, when thunder or shadow passed over the hills, the valley remembered that mercy had opened what fear could not."
    )


def tell(params: StoryParams) -> World:
    need = NEEDS[params.need]
    creature = CREATURES[params.creature]
    offering = OFFERINGS[params.offering]
    tool = TOOLS[params.tool]

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_gender, label=params.elder_name, role="elder"))
    valley = world.add(Entity(id="valley", kind="thing", type="valley", label="the valley", role="valley"))
    creature_ent = world.add(
        Entity(
            id="creature",
            kind="character",
            type="creature",
            label=creature.label,
            phrase=creature.epithet,
            role="creature",
            tags=set(creature.tags),
        )
    )
    creature_ent.meters["snagged"] += 1
    world.facts.update(
        need=need,
        creature_cfg=creature,
        offering=offering,
        tool=tool,
        hero=hero,
        elder=elder,
    )

    intro(world, hero, elder, need, creature)
    world.para()
    choose_quest(world, hero, elder, need, offering, tool)
    climb(world, hero, creature)
    world.para()
    offer(world, hero, offering)
    reveal(world, creature)
    free_creature(world, hero, creature, tool)
    world.para()
    bless(world, need, creature)
    ending(world, hero, need, creature)

    world.facts.update(
        healed=valley.meters["healed"] >= THRESHOLD,
        twist_revealed=creature_ent.meters["trusted"] >= THRESHOLD,
        freed=creature_ent.meters["freed"] >= THRESHOLD,
        blessing_given=creature_ent.meters["blessing_given"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    need = world.facts["need"]
    creature = world.facts["creature_cfg"]
    hero = world.facts["hero"]
    offering = world.facts["offering"]
    tool = world.facts["tool"]
    return [
        'Write a short myth for a 3-to-5-year-old that uses the word "crest" and ends happily after a twist.',
        f"Tell a mythic story where {hero.title} climbs a windy crest to face the {creature.label}, carrying {offering.label} and {tool.label}.",
        f"Write a gentle legend in which a valley blames a creature for missing {need.plea}, but the twist is that the creature needs help, not punishment.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    need = world.facts["need"]
    creature = world.facts["creature_cfg"]
    offering = world.facts["offering"]
    tool = world.facts["tool"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.title}, who climbed to the crest, and {elder.title}, who sent the child with a gentle warning. It is also about the {creature.label}, which looked frightening but was really in trouble.",
        ),
        (
            f"Why did {hero.title} climb to the crest?",
            f"{hero.title} climbed because the valley still needed {need.plea}. The people blamed the {creature.label}, so the child went to ask for help at the crest.",
        ),
        (
            f"What did {hero.title} bring?",
            f"{hero.title} brought {offering.phrase} and {tool.phrase}. The offering helped the creature trust the child, and the tool helped free it from the trap.",
        ),
    ]
    if world.facts.get("twist_revealed"):
        qa.append(
            (
                "What was the twist in the story?",
                f"The twist was that the {creature.label} was not causing the valley's trouble on purpose. It was trapped, and the scary sounds from the crest were really cries for help.",
            )
        )
    if world.facts.get("freed"):
        qa.append(
            (
                f"How did {hero.title} help the {creature.label}?",
                f"{hero.title} went close with the {tool.label} and freed the creature from {creature.snag}. That act changed the whole story, because once the creature was free it could give the valley the blessing it had been holding back by accident.",
            )
        )
    if world.facts.get("healed"):
        qa.append(
            (
                "How did the story end?",
                f"It ended happily: the valley received {need.plea}, and everyone learned that mercy was wiser than fear. The ending image proves the change, because {need.ending_image.lower()}",
            )
        )
    return qa


KNOWLEDGE = {
    "crest": [
        (
            "What is a crest on a hill or mountain?",
            "A crest is the top edge or highest line of a hill or mountain. When you stand on a crest, you can often see far in every direction.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that uses wonder, big natural powers, and memorable creatures to explain the world. Myths often teach something about courage, kindness, or wisdom.",
        )
    ],
    "offering": [
        (
            "What is an offering in a story?",
            "An offering is a gift given with respect. In many old tales, people bring an offering to show peace or ask for help.",
        )
    ],
    "mercy": [
        (
            "Why can kindness solve a problem better than fear?",
            "Kindness can help you see what is really wrong. When fear makes a mistake about someone, mercy can uncover the truth and lead to a better ending.",
        )
    ],
    "rain": [
        (
            "Why is rain important for trees?",
            "Rain soaks into the soil and gives roots the water they need. Without enough rain, leaves droop and fruit cannot grow well.",
        )
    ],
    "sun": [
        (
            "Why does sunlight matter in the morning?",
            "Sunlight warms the ground and helps the day begin. Morning light also helps people, birds, and plants know it is time to wake up.",
        )
    ],
    "river": [
        (
            "Why is flowing river water useful?",
            "Flowing water can fill buckets, feed plants, and turn a mill wheel. When a stream runs low, many parts of village life become harder.",
        )
    ],
}
KNOWLEDGE_ORDER = ["crest", "myth", "offering", "mercy", "rain", "sun", "river"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"crest", "myth", "offering", "mercy"}
    need = world.facts["need"]
    tags |= set(need.tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% need-creature fit
need_match(N, C) :- need(N), creature(C), solves(C, N).

% offering and tool fit
offering_match(C, O) :- creature(C), offering(O), likes(C, O).
tool_match(C, T) :- creature(C), tool(T), snag_of(C, S), handles(T, S).

valid(N, C, O, T) :- need_match(N, C), offering_match(C, O), tool_match(C, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("solves", creature_id, creature.solves))
        lines.append(asp.fact("snag_of", creature_id, creature.snag))
        for offering_id in sorted(creature.offering_ids):
            lines.append(asp.fact("likes", creature_id, offering_id))
    for offering_id in OFFERINGS:
        lines.append(asp.fact("offering", offering_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for snag in sorted(tool.handles):
            lines.append(asp.fact("handles", tool_id, snag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic crest storyworld with a happy-ending twist. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.need and args.creature and args.offering and args.tool:
        need = NEEDS[args.need]
        creature = CREATURES[args.creature]
        offering = OFFERINGS[args.offering]
        tool = TOOLS[args.tool]
        if not (need_fits(need, creature) and offering_fits(creature, offering) and tool_fits(creature, tool)):
            raise StoryError(explain_rejection(need, creature, offering, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.need is None or combo[0] == args.need)
        and (args.creature is None or combo[1] == args.creature)
        and (args.offering is None or combo[2] == args.offering)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        if args.need and args.creature and args.offering and args.tool:
            raise StoryError(explain_rejection(NEEDS[args.need], CREATURES[args.creature], OFFERINGS[args.offering], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    need_id, creature_id, offering_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES[elder_gender])

    return StoryParams(
        need=need_id,
        creature=creature_id,
        offering=offering_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_name=elder_name,
        elder_gender=elder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.need not in NEEDS:
        raise StoryError(f"(Invalid need: {params.need})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Invalid creature: {params.creature})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Invalid offering: {params.offering})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")

    need = NEEDS[params.need]
    creature = CREATURES[params.creature]
    offering = OFFERINGS[params.offering]
    tool = TOOLS[params.tool]
    if not (need_fits(need, creature) and offering_fits(creature, offering) and tool_fits(creature, tool)):
        raise StoryError(explain_rejection(need, creature, offering, tool))

    world = tell(params)
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        sample_params = resolve_params(default_args, random.Random(0))
        sample_params.seed = 0
        smoke_cases.append(sample_params)
    except Exception as err:
        rc = 1
        print(f"SMOKE setup failed: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header=f"smoke {i}")
            if not sample.story.strip():
                raise StoryError("empty story")
        except Exception as err:
            rc = 1
            print(f"SMOKE generation failed for case {i}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (need, creature, offering, tool) combos:\n")
        for need_id, creature_id, offering_id, tool_id in combos:
            print(f"  {need_id:8} {creature_id:14} {offering_id:12} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: {p.creature} for {p.need}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
