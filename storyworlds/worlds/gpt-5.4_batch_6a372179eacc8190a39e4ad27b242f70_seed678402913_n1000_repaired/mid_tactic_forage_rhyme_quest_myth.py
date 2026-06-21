#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mid_tactic_forage_rhyme_quest_myth.py
================================================================

A standalone storyworld about a child on a small mythic quest through the
middle wood. A rhyming guide gives a tactic, the child must forage the right
gift, and a keeper tests whether the chosen approach is wise.

The world model prefers a few strong, coherent quest variants over broad
coverage. A valid story needs all three of these to line up:

* the quest must truly be helped by the chosen forage item
* the obstacle must plausibly accept that gift
* the tactic must fit the obstacle's nature

The rendered story is driven by the simulated state: hope rises on the quest,
fear rises at the obstacle, and relief/blessing arrive only after the right
gift and tactic change the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/mid_tactic_forage_rhyme_quest_myth.py
    python storyworlds/worlds/gpt-5.4/mid_tactic_forage_rhyme_quest_myth.py --all
    python storyworlds/worlds/gpt-5.4/mid_tactic_forage_rhyme_quest_myth.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/mid_tactic_forage_rhyme_quest_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/mid_tactic_forage_rhyme_quest_myth.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Quest:
    id: str
    title: str = ""
    need: str = ""
    trouble: str = ""
    call_place: str = ""
    goal_place: str = ""
    fix_line: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str = ""
    keeper: str = ""
    scene: str = ""
    allowed_tactics: set[str] = field(default_factory=set)
    accepted_tags: set[str] = field(default_factory=set)
    threat: str = ""
    opening: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class TacticCfg:
    id: str
    label: str = ""
    verb: str = ""
    action_text: str = ""
    rhyme_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ForageCfg:
    id: str
    label: str = ""
    phrase: str = ""
    habitat: str = ""
    find_text: str = ""
    remedy_tags: set[str] = field(default_factory=set)
    gift_tags: set[str] = field(default_factory=set)
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


def _r_carry_blessing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["carrying_gift"] < THRESHOLD:
        return out
    sig = ("carry_blessing",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 1
    out.append("__gift__")
    return out


def _r_obstacle_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    wood = world.entities.get("wood")
    keeper = world.entities.get("keeper")
    if not hero or not wood or not keeper:
        return out
    if keeper.meters["blocking"] < THRESHOLD:
        return out
    sig = ("obstacle_fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    wood.meters["danger"] += 1
    out.append("__fear__")
    return out


def _r_resolved_path(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    keeper = world.entities.get("keeper")
    wood = world.entities.get("wood")
    if not hero or not keeper or not wood:
        return out
    if hero.meters["passage"] < THRESHOLD:
        return out
    sig = ("resolved_path",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.meters["blocking"] = 0.0
    hero.memes["relief"] += 1
    wood.meters["danger"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="carry_blessing", tag="emotional", apply=_r_carry_blessing),
    Rule(name="obstacle_fear", tag="emotional", apply=_r_obstacle_fear),
    Rule(name="resolved_path", tag="physical", apply=_r_resolved_path),
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


QUESTS = {
    "dawn_well": Quest(
        id="dawn_well",
        title="Wake the Dawn Well",
        need="bright",
        trouble="the village jars held only dim water",
        call_place="the mossy stepping stone by the stream",
        goal_place="the Dawn Well in the hill's mid hollow",
        fix_line="Only a bright woodland gift will wake the sleeping water.",
        ending_image="gold light trembled on the water and every pail shone like a tiny sunrise",
        tags={"quest", "water", "myth"},
    ),
    "rain_harp": Quest(
        id="rain_harp",
        title="Wake the Rain Harp",
        need="water",
        trouble="the thirsty beans in the garden bowed their heads",
        call_place="the old ash root beside the brook",
        goal_place="the Rain Harp strung under the cliff's mid arch",
        fix_line="Only a gift full of dew and living wetness will make the silver strings sing.",
        ending_image="cool drops rang from the strings and the thirsty leaves lifted again",
        tags={"quest", "rain", "myth"},
    ),
    "bee_lamp": Quest(
        id="bee_lamp",
        title="Mend the Bee Lamp",
        need="sweet",
        trouble="the evening path had gone dull and the hive lantern would not glow",
        call_place="the ring of thyme near the lane",
        goal_place="the Bee Lamp in the orchard's mid bower",
        fix_line="Only a sweet woodland gift will coax the lamp back to golden hum.",
        ending_image="the lamp glowed amber over the path and even the moths seemed to smile",
        tags={"quest", "light", "myth"},
    ),
}

OBSTACLES = {
    "briar_queen": Obstacle(
        id="briar_queen",
        label="briar gate",
        keeper="the Briar Queen",
        scene="At the mid path, thorn arches leaned together until the trail became a green wall.",
        allowed_tactics={"patient", "rhyme"},
        accepted_tags={"fragrant", "cool"},
        threat="the thorns kept knitting shut whenever anyone hurried at them",
        opening="the briars loosened and folded aside like sleepy fingers",
        tags={"briar", "thorns"},
    ),
    "bridge_troll": Obstacle(
        id="bridge_troll",
        label="stone bridge",
        keeper="the Bridge Troll",
        scene="At the mid stream, a stone bridge curved over black water, and a broad troll sat on its crown.",
        allowed_tactics={"trade", "rhyme"},
        accepted_tags={"sweet", "golden"},
        threat="the troll thumped the bridge with a fist and would not let strangers pass for free",
        opening="the troll grinned, slid aside, and tapped the bridge to say the way was open",
        tags={"bridge", "troll"},
    ),
    "lion_circle": Obstacle(
        id="lion_circle",
        label="standing stones",
        keeper="the Stone Lion",
        scene="At the mid clearing, standing stones ringed the path, and a lion of carved chalk stepped down among them.",
        allowed_tactics={"circle", "rhyme"},
        accepted_tags={"bright", "gleaming"},
        threat="the lion paced in a slow ring, testing whether the traveler knew the old manners",
        opening="the lion bowed its pale head and the stones made a doorway of light",
        tags={"lion", "stones"},
    ),
}

TACTICS = {
    "rhyme": TacticCfg(
        id="rhyme",
        label="rhyme",
        verb="answer in rhyme",
        action_text="spoke in a small brave couplet instead of pushing ahead",
        rhyme_text='"Gift for gate, and heart for guide; kindly roots make thorns divide."',
        tags={"rhyme", "gentle"},
    ),
    "trade": TacticCfg(
        id="trade",
        label="trade",
        verb="offer a fair trade",
        action_text="opened a careful palm and offered a fair trade before taking a step",
        rhyme_text='"Bridge keep, bridge keep, take this sweet share; leave me a path through the silver air."',
        tags={"trade", "fair"},
    ),
    "patient": TacticCfg(
        id="patient",
        label="patience",
        verb="wait and listen",
        action_text="stood still, listened to the leaves, and let the wood finish its first thought",
        rhyme_text='"Hush for the leaf and hush for the vine; open, old doorway, in your own time."',
        tags={"patient", "gentle"},
    ),
    "circle": TacticCfg(
        id="circle",
        label="sunwise circle",
        verb="walk a sunwise circle",
        action_text="walked a sunwise circle, heel after toe, to show respect to the old stones",
        rhyme_text='"Stone to sun and step to sky; wise feet pass and do not pry."',
        tags={"ritual", "bright"},
    ),
}

FORAGES = {
    "moonmint": ForageCfg(
        id="moonmint",
        label="moonmint",
        phrase="a sprig of moonmint",
        habitat="under cool stones near the ferny bank",
        find_text="Its leaves were silver on one side and green on the other, and they smelled like night rain.",
        remedy_tags={"bright"},
        gift_tags={"fragrant", "cool"},
        tags={"forage", "plant", "mint"},
    ),
    "dewplums": ForageCfg(
        id="dewplums",
        label="dewplums",
        phrase="three dewplums",
        habitat="from the reed patch where the mist lingers",
        find_text="Each plum held a bead of water in its skin, as if dawn had hidden there and forgotten to leave.",
        remedy_tags={"water", "sweet"},
        gift_tags={"sweet", "cool"},
        tags={"forage", "fruit", "dew"},
    ),
    "sunberries": ForageCfg(
        id="sunberries",
        label="sunberries",
        phrase="a handful of sunberries",
        habitat="from the sunny rise above the stream",
        find_text="The little berries shone warm as sparks and left a gold stain on the fingers.",
        remedy_tags={"bright", "sweet"},
        gift_tags={"bright", "golden", "sweet", "gleaming"},
        tags={"forage", "fruit", "berries"},
    ),
    "reed_honey": ForageCfg(
        id="reed_honey",
        label="reed honey",
        phrase="a shell of reed honey",
        habitat="from a hollow reed by the pond edge",
        find_text="The honey smelled of clover and river wind, and it glowed deep amber in the shell.",
        remedy_tags={"sweet"},
        gift_tags={"sweet", "golden"},
        tags={"forage", "honey", "amber"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Ava", "Tessa", "Elin", "Rosa", "Maya"]
BOY_NAMES = ["Tarin", "Leo", "Milo", "Oren", "Finn", "Aren", "Theo", "Nico"]
GUIDES = ["brook sprite", "small owl", "moss fox", "reed wren"]

KNOWLEDGE = {
    "quest": [
        (
            "What is a quest?",
            "A quest is a special journey with a purpose. Someone travels to help, find, or fix something important."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme happens when words end with the same or a very similar sound. Rhymes can make a line feel musical and easier to remember."
        )
    ],
    "forage": [
        (
            "What does forage mean?",
            "To forage means to go out and carefully look for useful things from nature, like berries or herbs. You only take what is safe and what you truly need."
        )
    ],
    "briar": [
        (
            "What are briars?",
            "Briars are thorny plants with sharp little points. They can catch on clothes and block a path."
        )
    ],
    "troll": [
        (
            "What is a troll in a myth?",
            "A troll in a myth is a magical creature, often big and strong. In stories, trolls sometimes guard bridges or other important places."
        )
    ],
    "lion": [
        (
            "Why might a stone lion matter in a myth?",
            "A stone lion can be a guardian that tests whether someone is brave and respectful. Myths often give statues a spirit and a duty."
        )
    ],
    "mint": [
        (
            "What is mint?",
            "Mint is a fragrant plant with cool-smelling leaves. People use it for smell, flavor, and sometimes gentle remedies."
        )
    ],
    "berries": [
        (
            "What are berries?",
            "Berries are small fruits that grow on plants. Some are sweet enough to eat, and some can be food for birds and animals too."
        )
    ],
    "honey": [
        (
            "What is honey?",
            "Honey is a sweet golden food made by bees from flower nectar. It is sticky, rich, and smells a little like blossoms."
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is tiny drops of water that gather on leaves and grass when the air cools. In stories, dew often feels fresh and magical."
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "rhyme", "forage", "briar", "troll", "lion", "mint", "berries", "honey", "dew"]


def forage_helps(quest: Quest, forage: ForageCfg) -> bool:
    return quest.need in forage.remedy_tags


def gift_suits(obstacle: Obstacle, forage: ForageCfg) -> bool:
    return bool(obstacle.accepted_tags & forage.gift_tags)


def tactic_suits(obstacle: Obstacle, tactic: TacticCfg) -> bool:
    return tactic.id in obstacle.allowed_tactics


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for qid, quest in QUESTS.items():
        for oid, obstacle in OBSTACLES.items():
            for tid, tactic in TACTICS.items():
                for fid, forage in FORAGES.items():
                    if forage_helps(quest, forage) and gift_suits(obstacle, forage) and tactic_suits(obstacle, tactic):
                        combos.append((qid, oid, tid, fid))
    return combos


@dataclass
class StoryParams:
    quest: str
    obstacle: str
    tactic: str
    forage: str
    hero_name: str
    hero_gender: str
    guide_kind: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        quest="dawn_well",
        obstacle="briar_queen",
        tactic="patient",
        forage="moonmint",
        hero_name="Mira",
        hero_gender="girl",
        guide_kind="brook sprite",
    ),
    StoryParams(
        quest="bee_lamp",
        obstacle="bridge_troll",
        tactic="trade",
        forage="reed_honey",
        hero_name="Tarin",
        hero_gender="boy",
        guide_kind="moss fox",
    ),
    StoryParams(
        quest="dawn_well",
        obstacle="lion_circle",
        tactic="circle",
        forage="sunberries",
        hero_name="Nora",
        hero_gender="girl",
        guide_kind="small owl",
    ),
    StoryParams(
        quest="rain_harp",
        obstacle="bridge_troll",
        tactic="rhyme",
        forage="dewplums",
        hero_name="Oren",
        hero_gender="boy",
        guide_kind="reed wren",
    ),
    StoryParams(
        quest="bee_lamp",
        obstacle="lion_circle",
        tactic="rhyme",
        forage="sunberries",
        hero_name="Ava",
        hero_gender="girl",
        guide_kind="brook sprite",
    ),
]


def explain_rejection(quest: Quest, obstacle: Obstacle, tactic: TacticCfg, forage: ForageCfg) -> str:
    if not forage_helps(quest, forage):
        return (
            f"(No story: {forage.phrase} would not solve this quest. "
            f"{quest.fix_line})"
        )
    if not gift_suits(obstacle, forage):
        return (
            f"(No story: {obstacle.keeper} would not be moved by {forage.phrase}. "
            f"Pick a gift with the right feel for that keeper.)"
        )
    if not tactic_suits(obstacle, tactic):
        allowed = ", ".join(sorted(obstacle.allowed_tactics))
        return (
            f"(No story: the tactic '{tactic.id}' does not fit {obstacle.keeper}. "
            f"Try one of: {allowed}.)"
        )
    return "(No story: this combination does not make a reasonable quest.)"


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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def guide_couplet(quest: Quest, hero: Entity, guide: Entity, forage: ForageCfg, tactic: TacticCfg) -> tuple[str, str]:
    first = (
        f'"{hero.id}, {hero.id}, heed the wood," sang the {guide.label}. '
        f'"{quest.fix_line}"'
    )
    second = (
        f'"{tactic.rhyme_text[1:-1]} Gather {forage.phrase} {forage.habitat}, '
        f'and carry it kindly."'
    )
    return first, second


def receive_quest(world: World, hero: Entity, guide: Entity, quest: Quest) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"At {quest.call_place}, {hero.id} met a {guide.label} with bright eyes and a voice like water over pebbles."
    )
    world.say(
        f"The {guide.label} told {hero.pronoun('object')} that {quest.trouble}. "
        f"If no one helped before sunset, the trouble would spread through the valley."
    )


def vow(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'"Then I will go," said {hero.id}. The quest was small enough for little hands, but important enough to make {hero.pronoun("possessive")} heart beat hard.'
    )
    world.say(
        f"So {hero.id} set out to {quest.title.lower()} at {quest.goal_place}."
    )


def enter_mid_wood(world: World, hero: Entity) -> None:
    wood = world.get("wood")
    wood.meters["distance"] += 1
    world.say(
        f"The child followed the mid path into the hush of the old wood, where the air smelled of bark and rain."
    )


def forage_scene(world: World, hero: Entity, forage: ForageCfg) -> None:
    hero.meters["carrying_gift"] += 1
    hero.attrs["forage_item"] = forage.label
    propagate(world, narrate=False)
    world.say(
        f"To keep the promise, {hero.id} had to forage carefully. {hero.pronoun().capitalize()} searched {forage.habitat} and found {forage.phrase}."
    )
    world.say(forage.find_text)
    world.say(
        f"{hero.id} tucked the gift close and walked on with more hope than before."
    )


def face_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    keeper = world.get("keeper")
    keeper.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.scene)
    world.say(
        f"There sat {obstacle.keeper}, and {obstacle.threat}. {hero.id} stopped so quickly that even the leaves seemed to hold still."
    )


def use_tactic(world: World, hero: Entity, obstacle: Obstacle, tactic: TacticCfg, forage: ForageCfg) -> None:
    keeper = world.get("keeper")
    hero.memes["courage"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.meters["passage"] += 1
    if tactic.id == "rhyme":
        keeper.memes["delight"] += 1
    elif tactic.id == "trade":
        keeper.memes["fairness"] += 1
    elif tactic.id == "patient":
        keeper.memes["calm"] += 1
    elif tactic.id == "circle":
        keeper.memes["respect"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} did not rush. {hero.pronoun().capitalize()} {tactic.action_text}."
    )
    if tactic.id == "rhyme":
        world.say(
            f'{hero.pronoun().capitalize()} lifted {forage.phrase} and said {tactic.rhyme_text}'
        )
    else:
        world.say(
            f"Then {hero.pronoun()} offered {forage.phrase} to {obstacle.keeper}."
        )
    world.say(
        f"For one breath the wood waited. Then {obstacle.opening}."
    )


def complete_quest(world: World, hero: Entity, quest: Quest, forage: ForageCfg, tactic: TacticCfg, obstacle: Obstacle) -> None:
    shrine = world.get("shrine")
    shrine.meters["healed"] += 1
    hero.memes["joy"] += 1
    hero.memes["blessing"] += 1
    world.say(
        f"Beyond the keeper stood {quest.goal_place}. {hero.id} laid {forage.phrase} in its proper place and whispered thanks."
    )
    if tactic.id == "rhyme":
        world.say(
            f"The old magic seemed to like the rhyme as much as the gift. At once, {quest.ending_image}."
        )
    else:
        world.say(
            f"At once, {quest.ending_image}. The quest had been mended by wise feet and a well-chosen gift."
        )
    if obstacle.id == "bridge_troll":
        world.say(
            "Far behind, the troll gave the bridge a happy thump, as if fair dealing had pleased him."
        )
    elif obstacle.id == "briar_queen":
        world.say(
            "Far behind, the thorns opened tiny star-shaped flowers, as if the wood itself had softened."
        )
    else:
        world.say(
            "Far behind, the stone lion returned to its ring and watched over the clearing with a gentler face."
        )


def tell(quest: Quest, obstacle: Obstacle, tactic: TacticCfg, forage: ForageCfg, hero_name: str, hero_gender: str, guide_kind: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    guide = world.add(Entity(id="guide", kind="character", type="spirit", label=guide_kind, role="guide"))
    keeper = world.add(Entity(id="keeper", kind="character", type="guardian", label=obstacle.keeper, role="keeper", tags=set(obstacle.tags)))
    wood = world.add(Entity(id="wood", kind="thing", type="forest", label="the wood"))
    shrine = world.add(Entity(id="shrine", kind="thing", type="shrine", label=quest.goal_place))
    world.facts["hero_name"] = hero_name

    receive_quest(world, hero, guide, quest)
    c1, c2 = guide_couplet(quest, hero, guide, forage, tactic)
    world.say(c1)
    world.say(c2)
    vow(world, hero, quest)

    world.para()
    enter_mid_wood(world, hero)
    forage_scene(world, hero, forage)

    world.para()
    face_obstacle(world, hero, obstacle)
    use_tactic(world, hero, obstacle, tactic, forage)

    world.para()
    complete_quest(world, hero, quest, forage, tactic, obstacle)

    world.facts.update(
        hero=hero,
        guide=guide,
        keeper=keeper,
        wood=wood,
        shrine=shrine,
        quest=quest,
        obstacle=obstacle,
        tactic=tactic,
        forage=forage,
        solved=shrine.meters["healed"] >= THRESHOLD,
        rhymed=tactic.id == "rhyme",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    quest = world.facts["quest"]
    obstacle = world.facts["obstacle"]
    tactic = world.facts["tactic"]
    forage = world.facts["forage"]
    hero = world.facts["hero"]
    return [
        f'Write a short mythic quest story for a 3-to-5-year-old that includes the words "mid", "tactic", and "forage".',
        f"Tell a gentle myth where {hero.label} must forage {forage.phrase} and use a wise tactic to pass {obstacle.keeper} on the way to {quest.title.lower()}.",
        f'Write a child-facing story with rhyme in it, a small quest in the middle wood, and an ending image that shows the world healed.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    quest = world.facts["quest"]
    obstacle = world.facts["obstacle"]
    tactic = world.facts["tactic"]
    forage = world.facts["forage"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child who went on a quest through the old wood. A {guide.label} sent {hero.pronoun('object')} to help fix a real problem."
        ),
        (
            f"What was the quest?",
            f"The quest was to {quest.title.lower()}. It mattered because {quest.trouble} and the valley needed help before sunset."
        ),
        (
            f"What did {hero.label} have to forage?",
            f"{hero.label} had to forage {forage.phrase} {forage.habitat}. That gift was the right kind of thing to help the quest itself."
        ),
        (
            f"What blocked the path in the middle of the wood?",
            f"{obstacle.keeper} blocked the way at {obstacle.label}. The obstacle felt dangerous because {obstacle.threat}."
        ),
        (
            f"What tactic did {hero.label} use, and why did it work?",
            f"{hero.label} chose to {tactic.verb}. It worked because that was a respectful way to deal with {obstacle.keeper}, and the offered gift suited the keeper too."
        ),
        (
            "How did the story end?",
            f"The quest was healed at last: {quest.ending_image}. The ending proves the world changed because the child's careful choice brought back blessing."
        ),
    ]
    if world.facts.get("rhymed"):
        qa.append(
            (
                "Where was the rhyme in the story?",
                f"The rhyme came when the guide gave advice and when {hero.label} answered with a couplet at the obstacle. The rhyme made the magic feel old, musical, and brave."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    obstacle = world.facts["obstacle"]
    forage = world.facts["forage"]
    tags = {"quest", "rhyme", "forage"}
    if obstacle.id == "briar_queen":
        tags.add("briar")
    elif obstacle.id == "bridge_troll":
        tags.add("troll")
    else:
        tags.add("lion")
    if forage.id == "moonmint":
        tags.add("mint")
    elif forage.id == "sunberries":
        tags.add("berries")
    elif forage.id == "reed_honey":
        tags.add("honey")
    elif forage.id == "dewplums":
        tags.update({"dew", "berries"})
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


ASP_RULES = r"""
helps(Q, F) :- quest_need(Q, Need), forage_remedy(F, Need).
gift_suits(O, F) :- obstacle_accepts(O, Tag), forage_gift(F, Tag).
tactic_suits(O, T) :- obstacle_allows(O, T).
valid(Q, O, T, F) :- quest(Q), obstacle(O), tactic(T), forage(F),
                     helps(Q, F), gift_suits(O, F), tactic_suits(O, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_need", qid, quest.need))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for tactic in sorted(obstacle.allowed_tactics):
            lines.append(asp.fact("obstacle_allows", oid, tactic))
        for tag in sorted(obstacle.accepted_tags):
            lines.append(asp.fact("obstacle_accepts", oid, tag))
    for tid in TACTICS:
        lines.append(asp.fact("tactic", tid))
    for fid, forage in FORAGES.items():
        lines.append(asp.fact("forage", fid))
        for tag in sorted(forage.remedy_tags):
            lines.append(asp.fact("forage_remedy", fid, tag))
        for tag in sorted(forage.gift_tags):
            lines.append(asp.fact("forage_gift", fid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        smoke_cases.append(params)

    try:
        for params in smoke_cases:
            sample = generate(params)
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=False, header="")
            if not sample.story.strip():
                raise StoryError("Generated an empty story during smoke test.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    else:
        print(f"OK: smoke-tested generate()/emit() on {len(smoke_cases)} stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic quest storyworld: a child must forage the right gift and use the right tactic."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tactic", choices=TACTICS)
    ap.add_argument("--forage", choices=FORAGES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.forage and not forage_helps(QUESTS[args.quest], FORAGES[args.forage]):
        quest = QUESTS[args.quest]
        obstacle = OBSTACLES[args.obstacle] if args.obstacle else next(iter(OBSTACLES.values()))
        tactic = TACTICS[args.tactic] if args.tactic else next(iter(TACTICS.values()))
        raise StoryError(explain_rejection(quest, obstacle, tactic, FORAGES[args.forage]))
    if args.obstacle and args.forage and not gift_suits(OBSTACLES[args.obstacle], FORAGES[args.forage]):
        quest = QUESTS[args.quest] if args.quest else next(iter(QUESTS.values()))
        tactic = TACTICS[args.tactic] if args.tactic else next(iter(TACTICS.values()))
        raise StoryError(explain_rejection(quest, OBSTACLES[args.obstacle], tactic, FORAGES[args.forage]))
    if args.obstacle and args.tactic and not tactic_suits(OBSTACLES[args.obstacle], TACTICS[args.tactic]):
        quest = QUESTS[args.quest] if args.quest else next(iter(QUESTS.values()))
        forage = FORAGES[args.forage] if args.forage else next(iter(FORAGES.values()))
        raise StoryError(explain_rejection(quest, OBSTACLES[args.obstacle], TACTICS[args.tactic], forage))

    combos = [
        combo for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tactic is None or combo[2] == args.tactic)
        and (args.forage is None or combo[3] == args.forage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, obstacle, tactic, forage = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide_kind = args.guide or rng.choice(GUIDES)
    return StoryParams(
        quest=quest,
        obstacle=obstacle,
        tactic=tactic,
        forage=forage,
        hero_name=name,
        hero_gender=gender,
        guide_kind=guide_kind,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tactic not in TACTICS:
        raise StoryError(f"(Unknown tactic: {params.tactic})")
    if params.forage not in FORAGES:
        raise StoryError(f"(Unknown forage: {params.forage})")

    quest = QUESTS[params.quest]
    obstacle = OBSTACLES[params.obstacle]
    tactic = TACTICS[params.tactic]
    forage = FORAGES[params.forage]
    if not (forage_helps(quest, forage) and gift_suits(obstacle, forage) and tactic_suits(obstacle, tactic)):
        raise StoryError(explain_rejection(quest, obstacle, tactic, forage))

    world = tell(
        quest=quest,
        obstacle=obstacle,
        tactic=tactic,
        forage=forage,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guide_kind=params.guide_kind,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (quest, obstacle, tactic, forage) combos:\n")
        for quest, obstacle, tactic, forage in combos:
            print(f"  {quest:10} {obstacle:12} {tactic:8} {forage}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} via {p.obstacle} ({p.tactic}, {p.forage})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
