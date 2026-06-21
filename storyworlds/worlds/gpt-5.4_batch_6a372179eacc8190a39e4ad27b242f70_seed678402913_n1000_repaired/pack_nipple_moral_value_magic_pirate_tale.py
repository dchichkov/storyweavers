#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pack_nipple_moral_value_magic_pirate_tale.py
=======================================================================

A standalone story world about little pirate adventurers who set out to find a
magic treasure, then discover that the truest treasure comes from helping a
smaller creature first.

This domain keeps the swashbuckling, child-facing feeling of a pirate tale while
making the moral turn state-driven: the children carry a supply pack, meet a
hungry baby sea creature, and must choose a fitting fix for its bottle. The key
seed words appear naturally in the story:

* "pack" as the little pirates' supply pack
* "nipple" as the soft bottle nipple the baby creature needs in order to drink

The world model enforces a small common-sense constraint: not every object can
solve the feeding problem. A bottle needs the right kind of nipple, matched to
the creature's bottle. Invalid explicit choices raise StoryError with a legible
reason.

Run it
------
    python storyworlds/worlds/gpt-5.4/pack_nipple_moral_value_magic_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/pack_nipple_moral_value_magic_pirate_tale.py --creature seal_pup --tool spare_nipple
    python storyworlds/worlds/gpt-5.4/pack_nipple_moral_value_magic_pirate_tale.py --tool rope
    python storyworlds/worlds/gpt-5.4/pack_nipple_moral_value_magic_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/pack_nipple_moral_value_magic_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pack_nipple_moral_value_magic_pirate_tale.py --verify
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
KINDNESS_MIN = 1


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Quest:
    id: str
    scene: str
    goal: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    bottle: str
    milk: str
    cry: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicGuide:
    id: str
    label: str
    phrase: str
    glow: str
    advice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind_tag: str
    fit_bottles: set[str] = field(default_factory=set)
    use_text: str = ""
    qa_text: str = ""
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


def _r_hungry_fussy(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    bottle = world.entities.get("bottle")
    if creature is None or bottle is None:
        return out
    if creature.meters["hungry"] < THRESHOLD:
        return out
    if bottle.meters["can_drink"] >= THRESHOLD:
        return out
    sig = ("fussy", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["distress"] += 1
    out.append("__fussy__")
    return out


def _r_feed_relief(world: World) -> list[str]:
    out: list[str] = []
    creature = world.entities.get("creature")
    bottle = world.entities.get("bottle")
    if creature is None or bottle is None:
        return out
    if creature.meters["hungry"] < THRESHOLD or bottle.meters["can_drink"] < THRESHOLD:
        return out
    sig = ("fed", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["hungry"] = 0.0
    creature.memes["distress"] = 0.0
    creature.memes["comfort"] += 1
    out.append("__fed__")
    return out


def _r_kindness_magic(world: World) -> list[str]:
    out: list[str] = []
    crew = world.entities.get("crew")
    guide = world.entities.get("guide")
    creature = world.entities.get("creature")
    if crew is None or guide is None or creature is None:
        return out
    if crew.memes["kindness"] < KINDNESS_MIN or creature.meters["hungry"] >= THRESHOLD:
        return out
    sig = ("magic_reward", guide.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guide.meters["glowing"] += 1
    crew.memes["wonder"] += 1
    out.append("__reward__")
    return out


CAUSAL_RULES = [
    Rule(name="hungry_fussy", tag="physical", apply=_r_hungry_fussy),
    Rule(name="feed_relief", tag="physical", apply=_r_feed_relief),
    Rule(name="kindness_magic", tag="moral", apply=_r_kindness_magic),
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
        for s in produced:
            world.say(s)
    return produced


def tool_fits(tool: Tool, creature: CreatureCfg) -> bool:
    return creature.bottle in tool.fit_bottles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for quest_id in QUESTS:
        for creature_id, creature in CREATURES.items():
            for guide_id in GUIDES:
                if any(tool_fits(tool, creature) for tool in TOOLS.values()):
                    combos.append((quest_id, creature_id, guide_id))
    return combos


def sensible_tools_for(creature: CreatureCfg) -> list[str]:
    return sorted(tid for tid, tool in TOOLS.items() if tool_fits(tool, creature))


def predict_fix(world: World, tool: Tool) -> dict:
    sim = world.copy()
    _use_tool(sim, tool, narrate=False)
    creature = sim.get("creature")
    guide = sim.get("guide")
    return {
        "fed": creature.meters["hungry"] < THRESHOLD,
        "comfort": creature.memes["comfort"],
        "glowing": guide.meters["glowing"],
    }


def introduce(world: World, hero: Entity, mate: Entity, quest: Quest) -> None:
    world.say(
        f"On a bright blue morning, {hero.id} and {mate.id} played at being little pirates in {quest.scene}. "
        f"{quest.opening}"
    )
    world.say(
        f'{hero.id} thumped the little supply pack on {hero.pronoun("possessive")} shoulder and grinned. '
        f'"Today we find {quest.goal}!"'
    )


def reveal_guide(world: World, guide_cfg: MagicGuide, hero: Entity, mate: Entity) -> None:
    guide = world.get("guide")
    guide.meters["glowing"] += 1
    hero.memes["wonder"] += 1
    mate.memes["wonder"] += 1
    world.say(
        f"From the pack, {hero.id} lifted {guide_cfg.phrase}. At once it {guide_cfg.glow}, "
        f"and a silver shimmer danced over the sand."
    )
    world.say(
        f'"Follow me kindly," whispered the {guide_cfg.label}. "{guide_cfg.advice}"'
    )


def discover_creature(world: World, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    bottle = world.get("bottle")
    creature.meters["hungry"] += 1
    bottle.meters["can_drink"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Near a tide pool, the children found {creature_cfg.phrase} beside {creature_cfg.bottle}. "
        f"The bottle was full of {creature_cfg.milk}, but its soft nipple was missing."
    )
    world.say(
        f"{creature_cfg.cry.capitalize()} The little one nosed the bottle and could not drink."
    )


def temptation(world: World, hero: Entity, mate: Entity, quest: Quest) -> None:
    hero.memes["greed"] += 1
    world.say(
        f'Just then, a thin beam of magic light skipped farther down the shore, as if {quest.goal} were waiting. '
        f'"We could keep going," {hero.id} whispered.'
    )
    world.say(
        f'{mate.id} looked at the treasure-light, then back at the hungry creature. '
        f'"A real pirate does not leave a baby crying," {mate.pronoun()} said.'
    )


def choose_kindness(world: World, guide_cfg: MagicGuide, hero: Entity, mate: Entity) -> None:
    world.get("crew").memes["kindness"] += 1
    hero.memes["greed"] = 0.0
    hero.memes["kindness"] += 1
    mate.memes["kindness"] += 1
    world.say(
        f"The {guide_cfg.label} glimmered again, not toward gold this time, but toward the little supply pack. "
        f"{hero.id} nodded. Helping first felt braver than hurrying on."
    )


def _use_tool(world: World, tool: Tool, narrate: bool = True) -> None:
    bottle = world.get("bottle")
    creature = world.get("creature")
    creature_cfg = world.facts["creature_cfg"]
    if not tool_fits(tool, creature_cfg):
        return
    bottle.attrs["nipple"] = tool.label
    bottle.meters["can_drink"] += 1
    world.get("crew").memes["skill"] += 1
    propagate(world, narrate=narrate)


def fix_bottle(world: World, tool: Tool, creature_cfg: CreatureCfg) -> None:
    _use_tool(world, tool, narrate=False)
    bottle = world.get("bottle")
    creature = world.get("creature")
    world.say(tool.use_text.format(
        bottle=creature_cfg.bottle,
        milk=creature_cfg.milk,
        creature=creature_cfg.label,
    ))
    if bottle.meters["can_drink"] >= THRESHOLD:
        world.say(
            f"The new nipple fit snugly on {creature.pronoun('possessive')} bottle, and the little {creature_cfg.label} drank the {creature_cfg.milk} in soft, happy gulps."
        )


def reward(world: World, guide_cfg: MagicGuide, creature_cfg: CreatureCfg, quest: Quest) -> None:
    propagate(world, narrate=False)
    world.say(
        f"When the crying stopped, the {guide_cfg.label} blazed bright as a star. The tide pool rippled open, "
        f"and {creature_cfg.reward} shone inside."
    )
    world.say(
        f'"Kind hands find the truest treasure," whispered the {guide_cfg.label}.'
    )
    world.say(
        f"{hero_and_mate(world)} took only one glowing prize and left the rest sparkling under the water. {quest.ending}"
    )


def hero_and_mate(world: World) -> str:
    return f'{world.facts["hero"].id} and {world.facts["mate"].id}'


def ending_image(world: World, creature_cfg: CreatureCfg) -> None:
    world.say(
        f"Behind them, the little {creature_cfg.label} bobbed by the tide pool, full and calm, while the pirates walked home with lighter steps and kinder hearts."
    )


def tell(
    quest: Quest,
    creature_cfg: CreatureCfg,
    guide_cfg: MagicGuide,
    tool: Tool,
    hero_name: str = "Nell",
    hero_gender: str = "girl",
    mate_name: str = "Tom",
    mate_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    world.add(Entity(id="crew", kind="thing", type="crew", label="the pirate crew"))
    world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    world.add(Entity(id="guide", kind="thing", type="magic", label=guide_cfg.label, phrase=guide_cfg.phrase))
    world.add(Entity(id="creature", kind="thing", type="animal", label=creature_cfg.label))
    world.add(Entity(
        id="bottle",
        kind="thing",
        type="bottle",
        label="bottle",
        phrase=creature_cfg.bottle,
        attrs={"nipple": ""},
    ))

    world.facts.update(
        hero=hero,
        mate=mate,
        quest=quest,
        creature_cfg=creature_cfg,
        guide_cfg=guide_cfg,
        tool=tool,
    )

    introduce(world, hero, mate, quest)
    reveal_guide(world, guide_cfg, hero, mate)

    world.para()
    discover_creature(world, creature_cfg)
    temptation(world, hero, mate, quest)
    choose_kindness(world, guide_cfg, hero, mate)

    world.para()
    fix_bottle(world, tool, creature_cfg)
    reward(world, guide_cfg, creature_cfg, quest)
    ending_image(world, creature_cfg)

    world.facts.update(
        fed=world.get("creature").meters["hungry"] < THRESHOLD,
        bottle_fixed=world.get("bottle").meters["can_drink"] >= THRESHOLD,
        glowing=world.get("guide").meters["glowing"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "moon_pearl": Quest(
        id="moon_pearl",
        scene="a small cove full of driftwood and secret-looking rocks",
        goal="the Moon Pearl",
        opening="A striped cloth served as their sail, a stick served as their mast, and the old pack held all the tools a brave crew might need.",
        ending="They knew the sea had given them a better prize than bragging rights.",
        tags={"pirate", "treasure"},
    ),
    "star_shell": Quest(
        id="star_shell",
        scene="a windy beach with a cave shaped like a giant mouth",
        goal="the Star Shell",
        opening="A tub became their ship, a broom became a mast, and the pack bumped against their backs with every excited step.",
        ending="The treasure felt bright, but the good deed felt brighter.",
        tags={"pirate", "treasure"},
    ),
    "tide_ruby": Quest(
        id="tide_ruby",
        scene="a quiet inlet where little waves licked the stones",
        goal="the Tide Ruby",
        opening="A laundry basket was their deck, a spoon was their spyglass, and the pack carried snacks, string, and other pirate supplies.",
        ending="They had found something worth more than a shout of 'Mine!'",
        tags={"pirate", "treasure"},
    ),
}

CREATURES = {
    "seal_pup": CreatureCfg(
        id="seal_pup",
        label="seal pup",
        phrase="a round-eyed seal pup",
        bottle="a glass feeding bottle",
        milk="warm milk",
        cry="eep, eep",
        reward="a moon-bright pearl",
        tags={"seal", "kindness", "bottle"},
    ),
    "otter_kit": CreatureCfg(
        id="otter_kit",
        label="otter kit",
        phrase="a damp little otter kit",
        bottle="a short baby bottle",
        milk="sweet cream",
        cry="peep-peep",
        reward="a starry shell",
        tags={"otter", "kindness", "bottle"},
    ),
    "sea_dragon": CreatureCfg(
        id="sea_dragon",
        label="sea dragon",
        phrase="a tiny sea dragon with pearl-blue fins",
        bottle="a curled moon bottle",
        milk="silver milk",
        cry="trill-trill",
        reward="a glowing tide ruby",
        tags={"dragon", "magic", "bottle"},
    ),
}

GUIDES = {
    "moon_compass": MagicGuide(
        id="moon_compass",
        label="moon compass",
        phrase="a moon compass no bigger than a cookie",
        glow="glowed with a pale blue ring",
        advice="kindness first, treasure after",
        tags={"magic", "compass"},
    ),
    "whisper_map": MagicGuide(
        id="whisper_map",
        label="whisper map",
        phrase="a whisper map sewn on silver cloth",
        glow="shivered with tiny golden stars",
        advice="the best gold is the good you do",
        tags={"magic", "map"},
    ),
    "singing_shell": MagicGuide(
        id="singing_shell",
        label="singing shell",
        phrase="a singing shell with a pink curl",
        glow="hummed and shone like a lantern under water",
        advice="helping hearts steer straight",
        tags={"magic", "shell"},
    ),
}

TOOLS = {
    "spare_nipple": Tool(
        id="spare_nipple",
        label="spare nipple",
        phrase="a spare bottle nipple",
        kind_tag="nipple",
        fit_bottles={"a glass feeding bottle", "a short baby bottle", "a curled moon bottle"},
        use_text="{hero} dug into the pack and found a clean spare nipple wrapped in cloth. Very gently, the children pressed it onto the top of the bottle.",
        qa_text="They used a clean spare nipple from their pack to fix the bottle.",
        tags={"nipple", "pack", "care"},
    ),
    "tiny_nipple": Tool(
        id="tiny_nipple",
        label="tiny nipple",
        phrase="a tiny rubber nipple",
        kind_tag="nipple",
        fit_bottles={"a short baby bottle", "a curled moon bottle"},
        use_text="From the pack, they found a tiny rubber nipple tucked in a tin. {hero} held the bottle steady while the new piece clicked neatly into place.",
        qa_text="They used a tiny rubber nipple that fit the bottle.",
        tags={"nipple", "pack", "care"},
    ),
    "golden_nipple": Tool(
        id="golden_nipple",
        label="golden nipple",
        phrase="a soft golden nipple from the ship's baby kit",
        kind_tag="nipple",
        fit_bottles={"a curled moon bottle"},
        use_text="At the very bottom of the pack lay a soft golden nipple from the ship's baby kit. It shimmered once, then settled onto the bottle as if it had been waiting there.",
        qa_text="They used the golden nipple from the ship's baby kit.",
        tags={"nipple", "magic", "pack"},
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a coil of rope",
        kind_tag="rope",
        fit_bottles=set(),
        use_text="",
        qa_text="",
        tags={"rope"},
    ),
    "feather": Tool(
        id="feather",
        label="feather",
        phrase="a bright parrot feather",
        kind_tag="feather",
        fit_bottles=set(),
        use_text="",
        qa_text="",
        tags={"feather"},
    ),
}

GIRL_NAMES = ["Nell", "Mina", "Lila", "Ava", "Ruby", "Tess", "Maya", "Poppy"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Max", "Finn", "Eli", "Sam", "Jack"]


@dataclass
class StoryParams:
    quest: str
    creature: str
    guide: str
    tool: str
    hero_name: str
    hero_gender: str
    mate_name: str
    mate_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        quest="moon_pearl",
        creature="seal_pup",
        guide="moon_compass",
        tool="spare_nipple",
        hero_name="Nell",
        hero_gender="girl",
        mate_name="Tom",
        mate_gender="boy",
        parent="mother",
    ),
    StoryParams(
        quest="star_shell",
        creature="otter_kit",
        guide="whisper_map",
        tool="tiny_nipple",
        hero_name="Max",
        hero_gender="boy",
        mate_name="Lila",
        mate_gender="girl",
        parent="father",
    ),
    StoryParams(
        quest="tide_ruby",
        creature="sea_dragon",
        guide="singing_shell",
        tool="golden_nipple",
        hero_name="Ruby",
        hero_gender="girl",
        mate_name="Finn",
        mate_gender="boy",
        parent="mother",
    ),
    StoryParams(
        quest="moon_pearl",
        creature="sea_dragon",
        guide="moon_compass",
        tool="spare_nipple",
        hero_name="Eli",
        hero_gender="boy",
        mate_name="Mina",
        mate_gender="girl",
        parent="father",
    ),
]


KNOWLEDGE = {
    "pack": [
        (
            "What is a pack?",
            "A pack is a bag you carry on your back or shoulder to hold useful things. Adventurers keep supplies in a pack so they are ready to help when something goes wrong.",
        )
    ],
    "nipple": [
        (
            "What is a bottle nipple?",
            "A bottle nipple is the soft top part of a baby bottle that a baby can suck on to drink milk. If it is missing, the baby may not be able to drink.",
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means noticing when someone needs help and choosing to care for them. A kind choice can matter more than getting what you wanted first.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is something wondrous that cannot happen in ordinary life, like a glowing shell that whispers advice. In stories, magic often helps show what a character has learned.",
        )
    ],
    "pirate": [
        (
            "What is a pirate tale?",
            "A pirate tale is a story about sailors, treasure, maps, and brave choices on the sea. In a child-friendly pirate tale, the biggest adventure can be learning to be brave and good.",
        )
    ],
    "seal": [
        (
            "What is a seal pup?",
            "A seal pup is a baby seal. It is small, soft, and needs gentle care.",
        )
    ],
    "otter": [
        (
            "What is an otter kit?",
            "An otter kit is a baby otter. Baby otters are little and playful, and they need food and care.",
        )
    ],
    "dragon": [
        (
            "What is a sea dragon in a story?",
            "A sea dragon is a made-up magical creature for a story. It can be tiny and gentle instead of scary.",
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass helps travelers find a direction. In stories, a magic compass can also point toward the right choice.",
        )
    ],
    "map": [
        (
            "What is a treasure map?",
            "A treasure map is a drawing that shows where to go to find something hidden. In pirate stories, maps lead adventurers on a quest.",
        )
    ],
    "shell": [
        (
            "Why do shells matter in sea stories?",
            "Shells come from the sea, so they make beach and pirate stories feel magical and real. A special shell can become a clue or a treasure.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "pirate",
    "pack",
    "nipple",
    "kindness",
    "magic",
    "seal",
    "otter",
    "dragon",
    "compass",
    "map",
    "shell",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    quest = f["quest"]
    creature = f["creature_cfg"]
    guide = f["guide_cfg"]
    tool = f["tool"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "pack" and "nipple", and where magic helps two children choose kindness over treasure.',
        f"Tell a gentle story where {hero.id} and {mate.id} go looking for {quest.goal}, but stop to help a {creature.label} using {tool.phrase} from their pack.",
        f'Write a magical pirate story where a {guide.label} teaches that helping first is better than grabbing treasure first.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    quest = f["quest"]
    creature = f["creature_cfg"]
    guide = f["guide_cfg"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two little pirate friends, {hero.id} and {mate.id}, who go looking for {quest.goal}. On the way, they meet a hungry {creature.label} and have to decide what kind of pirates they want to be.",
        ),
        (
            "What was in the pack?",
            f"The pack held pirate supplies and, most importantly, {tool.phrase}. That mattered because the baby creature's bottle was missing its nipple.",
        ),
        (
            f"Why was the {creature.label} crying?",
            f"The little {creature.label} was hungry, but it could not drink from its bottle because the soft nipple was missing. The milk was there, yet the bottle still could not help until the children fixed it.",
        ),
        (
            "What did the magic guide tell them?",
            f"The {guide.label} told them to put kindness first. Its magic pointed them away from rushing after treasure and toward helping the hungry little creature.",
        ),
        (
            "How did they solve the problem?",
            f"{tool.qa_text} Once the nipple fit the bottle, the baby could drink and calm down.",
        ),
        (
            "What is the moral of the story?",
            f"The story teaches that kindness is worth more than grabbing treasure first. The magic reward comes only after the children stop and help someone smaller than themselves.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pirate", "pack", "nipple", "kindness", "magic"}
    creature = f["creature_cfg"]
    guide = f["guide_cfg"]
    tool = f["tool"]
    if "seal" in creature.id:
        tags.add("seal")
    if "otter" in creature.id:
        tags.add("otter")
    if "dragon" in creature.id:
        tags.add("dragon")
    if guide.id == "moon_compass":
        tags.add("compass")
    if guide.id == "whisper_map":
        tags.add("map")
    if guide.id == "singing_shell":
        tags.add("shell")
    if "pack" in tool.tags:
        tags.add("pack")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_tool(creature: CreatureCfg, tool: Tool) -> str:
    good = ", ".join(sensible_tools_for(creature))
    return (
        f"(No story: {tool.label} cannot fix {creature.bottle}. "
        f"The baby needs a bottle nipple that actually fits, so try one of: {good}.)"
    )


ASP_RULES = r"""
usable_tool(C, T) :- creature(C), tool(T), fits(T, B), bottle_of(C, B).
valid(Q, C, G) :- quest(Q), creature(C), guide(G), usable_tool(C, _).

% A story ends well only if the chosen tool actually fits the creature's bottle.
bottle_fixed :- chosen_creature(C), chosen_tool(T), usable_tool(C, T).
fed :- bottle_fixed.
kindness_done.
magic_reward :- kindness_done, fed.
outcome(helped) :- magic_reward.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("bottle_of", cid, creature.bottle))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for bottle in sorted(tool.fit_bottles):
            lines.append(asp.fact("fits", tid, bottle))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_creature", params.creature),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    for params in CURATED[:2]:
        py = "helped" if tool_fits(TOOLS[params.tool], CREATURES[params.creature]) else "?"
        cl = asp_outcome(params)
        if py != cl:
            rc = 1
            print(f"MISMATCH in outcome for {params}: python={py} clingo={cl}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a magical pirate quest where kindness comes before treasure."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.tool:
        creature = CREATURES[args.creature]
        tool = TOOLS[args.tool]
        if not tool_fits(tool, creature):
            raise StoryError(explain_tool(creature, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.creature is None or combo[1] == args.creature)
        and (args.guide is None or combo[2] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, creature_id, guide_id = rng.choice(sorted(combos))
    creature = CREATURES[creature_id]
    if args.tool is not None:
        tool_id = args.tool
    else:
        tool_id = rng.choice(sensible_tools_for(creature))
    hero_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    mate_name = _pick_name(rng, mate_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        quest=quest_id,
        creature=creature_id,
        guide=guide_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")
    if params.creature not in CREATURES:
        raise StoryError(f"Unknown creature: {params.creature}")
    if params.guide not in GUIDES:
        raise StoryError(f"Unknown guide: {params.guide}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if not tool_fits(TOOLS[params.tool], CREATURES[params.creature]):
        raise StoryError(explain_tool(CREATURES[params.creature], TOOLS[params.tool]))

    world = tell(
        quest=QUESTS[params.quest],
        creature_cfg=CREATURES[params.creature],
        guide_cfg=GUIDES[params.guide],
        tool=TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, creature, guide) combos:\n")
        for quest, creature, guide in combos:
            print(f"  {quest:10} {creature:12} {guide}")
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
            header = f"### {p.hero_name} & {p.mate_name}: {p.creature} with {p.tool} ({p.quest})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
