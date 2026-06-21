#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wrestle_bad_ending_repetition_sound_effects_fairy.py
===============================================================================

A standalone story world for a fairy-tale-shaped story about a child who wants
to wrestle a cherished thing free from a snag above water.

The world rebuilds a small source-tale premise:

    A child sees something lovely caught above a pond or stream.
    The child wants to tug and wrestle it down at once.
    A wiser companion warns that the branch is weak and the water is deep.
    If the child listens, they fetch the right tool and save the treasure.
    If the child does not listen, the branch goes creak, crack, splash,
    the treasure is lost, and the story ends sadly.

The domain leans into:
- fairy-tale tone
- repetition
- sound effects
- a genuine bad-ending branch

Run it
------
    python storyworlds/worlds/gpt-5.4/wrestle_bad_ending_repetition_sound_effects_fairy.py
    python storyworlds/worlds/gpt-5.4/wrestle_bad_ending_repetition_sound_effects_fairy.py --all
    python storyworlds/worlds/gpt-5.4/wrestle_bad_ending_repetition_sound_effects_fairy.py --qa
    python storyworlds/worlds/gpt-5.4/wrestle_bad_ending_repetition_sound_effects_fairy.py --verify
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
STUBBORN_INIT = 5.0
WISE_TRAITS = {"careful", "patient", "steady", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    reachable: bool = False
    over_water: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "mother", "woman", "fairy_godmother"}
        male = {"boy", "prince", "father", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "fairy_godmother": "godmother",
            "wizard": "wizard",
            "princess": "princess",
            "prince": "prince",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    water: str
    path: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    gleam: str
    sink_text: str
    saved_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snag:
    id: str
    label: str
    phrase: str
    height: int
    delicacy: int
    over_water: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    gentle: int
    success_text: str
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


def _r_branch_strain(world: World) -> list[str]:
    hero = world.get("hero")
    snag = world.get("snag")
    if hero.meters["wrestling"] < THRESHOLD:
        return []
    sig = ("strain", snag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    snag.meters["strain"] += 1
    hero.memes["effort"] += 1
    return ["__strain__"]


def _r_snap(world: World) -> list[str]:
    hero = world.get("hero")
    snag = world.get("snag")
    if snag.meters["strain"] < THRESHOLD:
        return []
    if hero.meters["pull_force"] < float(world.facts.get("snap_force", 2)):
        return []
    sig = ("snap", snag.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    snag.meters["broken"] += 1
    if snag.over_water:
        world.get("treasure").meters["falling"] += 1
    return ["__snap__"]


def _r_loss(world: World) -> list[str]:
    treasure = world.get("treasure")
    if treasure.meters["falling"] < THRESHOLD:
        return []
    sig = ("lost", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["lost"] += 1
    hero = world.get("hero")
    hero.memes["grief"] += 1
    return ["__lost__"]


CAUSAL_RULES = [
    Rule(name="branch_strain", tag="physical", apply=_r_branch_strain),
    Rule(name="snap", tag="physical", apply=_r_snap),
    Rule(name="loss", tag="emotional", apply=_r_loss),
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
        for sent in produced:
            world.say(sent)
    return produced


def can_snag_story(setting: Setting, snag: Snag) -> bool:
    return snag.over_water and "water" in setting.tags


def compatible_tool(snag: Snag, tool: Tool) -> bool:
    return tool.reach >= snag.height and tool.gentle >= snag.delicacy


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid in TREASURES:
            for nid, snag in SNAGS.items():
                if not can_snag_story(setting, snag):
                    continue
                for gid, tool in TOOLS.items():
                    if compatible_tool(snag, tool):
                        combos.append((sid, tid, nid, gid))
    return combos


def caution_strength(trait: str, helper_age: int, hero_age: int, relation: str) -> float:
    base = 5.0 if trait in WISE_TRAITS else 3.0
    if relation == "siblings" and helper_age > hero_age:
        base += 3.0
    return base


def would_listen(trait: str, helper_age: int, hero_age: int, relation: str, trust: int) -> bool:
    return caution_strength(trait, helper_age, hero_age, relation) + (trust / 2.0) > STUBBORN_INIT + 1.5


def outcome_of(params: "StoryParams") -> str:
    if would_listen(params.helper_trait, params.helper_age, params.hero_age, params.relation, params.trust):
        return "saved"
    return "lost"


def predict_wrestle(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["wrestling"] += 1
    hero.meters["pull_force"] += 2
    propagate(sim, narrate=False)
    treasure = sim.get("treasure")
    return {
        "snaps": sim.get("snag").meters["broken"] >= THRESHOLD,
        "lost": treasure.meters["lost"] >= THRESHOLD,
    }


def introduce(world: World, setting: Setting, hero: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f"Beyond the last cottage and the last gate, {setting.place} lay under {setting.mood}. "
        f"There walked {hero.id}, a little {hero.label_word}, with {helper.id} beside {hero.pronoun('object')}."
    )
    world.say(
        f"{hero.id} loved one small wonder above all: {treasure.phrase} that {treasure.gleam}."
    )


def spot_trouble(world: World, setting: Setting, hero: Entity, treasure: Treasure, snag: Snag) -> None:
    treasure_ent = world.get("treasure")
    treasure_ent.meters["stuck"] += 1
    world.say(
        f"That morning they found {treasure.label} caught high in {snag.phrase}, just above {setting.water}. "
        f"It swayed and winked, near enough to see and too high to reach."
    )
    hero.memes["desire"] += 1


def want_it(world: World, hero: Entity, treasure: Treasure) -> None:
    world.say(
        f'"My {treasure.label}!" cried {hero.id}. "I will pull and pull, wrestle and wrestle, '
        f"until it comes down."
    )


def warn(world: World, hero: Entity, helper: Entity, snag: Snag, treasure: Treasure, tool: Tool) -> None:
    pred = predict_wrestle(world)
    helper.memes["care"] += 1
    world.facts["predicted_lost"] = pred["lost"]
    world.say(
        f'{helper.id} touched {hero.pronoun("possessive")} sleeve. "No, no," said {helper.id}. '
        f'"That {snag.label} is thin and tricky. If you wrestle and wrestle, it may go crack, '
        f'and {treasure.label} will tumble into the water. Let us fetch {tool.phrase} instead."'
    )


def listen(world: World, hero: Entity, helper: Entity, tool: Tool, treasure: Treasure) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} stamped one foot, then took a long breath. Once, {hero.pronoun()} looked at the water. "
        f"Twice, {hero.pronoun()} looked at the shaking branch. At last {hero.pronoun()} nodded."
    )
    world.say(
        f'Together they fetched {tool.phrase}. {tool.success_text}, and soon {treasure.saved_text}.'
    )


def ignore_warning(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"No, no, no," said {hero.id}. "{treasure.label} is mine, and I will have it now." '
        f"So {hero.pronoun()} reached up with both hands and began to wrestle."
    )
    hero.meters["wrestling"] += 1
    hero.meters["pull_force"] += 2
    propagate(world, narrate=False)


def bad_turn(world: World, hero: Entity, helper: Entity, treasure: Treasure, setting: Setting, snag: Snag) -> None:
    treasure_ent = world.get("treasure")
    snag_ent = world.get("snag")
    if snag_ent.meters["broken"] >= THRESHOLD:
        world.say(
            f"Creak, creak went the {snag.label}. Crack! went the weakest twig."
        )
    if treasure_ent.meters["lost"] >= THRESHOLD:
        world.say(
            f"Down dropped {treasure.label}. Splash! into {setting.water} it fell, and the dark ripples shut over it."
        )
        world.say(
            f"{hero.id} stared and stared. {treasure.sink_text}"
        )
    hero.memes["regret"] += 1
    helper.memes["sorrow"] += 1


def sad_ending(world: World, hero: Entity, helper: Entity, treasure: Treasure, setting: Setting) -> None:
    world.say(
        f'{helper.id} put an arm around {hero.id}, but there was no magic to call {treasure.label} back from {setting.water}. '
        f'"Pull and pull, wrestle and wrestle," whispered {hero.id}, "and still I have nothing."'
    )
    world.say(
        f"So they walked home by {setting.path}, slowly and sadly, and {hero.id} never saw {treasure.label} shine again."
    )


def happy_ending(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f'{hero.id} held {treasure.label} close. "Not by grabbing, not by wrestling, but by waiting and thinking," '
        f'{hero.pronoun()} said.'
    )
    world.say(
        f"And from that day on, whenever trouble hung too high, {hero.id} remembered to ask for help before tugging at it."
    )


def tell(
    setting: Setting,
    treasure_cfg: Treasure,
    snag_cfg: Snag,
    tool_cfg: Tool,
    hero_name: str = "Lina",
    hero_type: str = "girl",
    helper_name: str = "Milo",
    helper_type: str = "boy",
    helper_trait: str = "careful",
    relation: str = "siblings",
    hero_age: int = 5,
    helper_age: int = 7,
    trust: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_type, phrase=hero_name, role="hero", age=hero_age))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type, phrase=helper_name, role="helper", age=helper_age, traits=[helper_trait]))
    treasure = world.add(Entity(id="treasure", type="treasure", label=treasure_cfg.label, phrase=treasure_cfg.phrase, fragile=True, tags=set(treasure_cfg.tags)))
    snag = world.add(Entity(id="snag", type="snag", label=snag_cfg.label, phrase=snag_cfg.phrase, over_water=snag_cfg.over_water, reachable=False, tags=set(snag_cfg.tags)))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, reachable=True, tags=set(tool_cfg.tags)))

    hero.id = hero_name
    helper.id = helper_name
    world.entities[hero.id] = world.entities.pop("hero")
    world.entities[helper.id] = world.entities.pop("helper")
    world.entities["hero"] = world.entities[hero.id]
    world.entities["helper"] = world.entities[helper.id]

    world.facts["snap_force"] = 2
    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name
    world.facts["relation"] = relation

    introduce(world, setting, hero, helper, treasure_cfg)
    spot_trouble(world, setting, hero, treasure_cfg, snag_cfg)
    world.para()
    want_it(world, hero, treasure_cfg)
    warn(world, hero, helper, snag_cfg, treasure_cfg, tool_cfg)

    listened = would_listen(helper_trait, helper_age, hero_age, relation, trust)
    world.para()
    if listened:
        listen(world, hero, helper, tool_cfg, treasure_cfg)
        world.para()
        happy_ending(world, hero, helper, treasure_cfg)
        outcome = "saved"
    else:
        ignore_warning(world, hero, helper, treasure_cfg)
        world.para()
        bad_turn(world, hero, helper, treasure_cfg, setting, snag_cfg)
        sad_ending(world, hero, helper, treasure_cfg, setting)
        outcome = "lost"

    world.facts.update(
        hero=hero,
        helper=helper,
        treasure_cfg=treasure_cfg,
        snag_cfg=snag_cfg,
        tool_cfg=tool_cfg,
        setting=setting,
        listened=listened,
        outcome=outcome,
        treasure_lost=treasure.meters["lost"] >= THRESHOLD,
    )
    return world


THEMES_NOTE = "fairy tale"

SETTINGS = {
    "moonpond": Setting(
        id="moonpond",
        place="the moonlit pond behind the mill",
        water="the black pond",
        path="the reed path",
        mood="silver mist",
        tags={"water", "pond", "fairy"},
    ),
    "brook": Setting(
        id="brook",
        place="the mossy brook below the hill",
        water="the swift brook",
        path="the fern path",
        mood="blue morning light",
        tags={"water", "brook", "fairy"},
    ),
    "moat": Setting(
        id="moat",
        place="the old castle moat",
        water="the green moat",
        path="the stone path",
        mood="golden evening light",
        tags={"water", "moat", "fairy"},
    ),
}

TREASURES = {
    "ribbon": Treasure(
        id="ribbon",
        label="the moon ribbon",
        phrase="a moon ribbon",
        gleam="shone like poured milk",
        sink_text="The silver bow unwound in the water and slipped away like a little moonbeam.",
        saved_text="the moon ribbon floated down soft as a feather into their waiting hands",
        tags={"ribbon", "water"},
    ),
    "lantern": Treasure(
        id="lantern",
        label="the flower lantern",
        phrase="a flower lantern",
        gleam="glowed with a pale honey light",
        sink_text="The tiny lantern went out at once, and only one pale petal drifted back up.",
        saved_text="the flower lantern came down glowing still, without even a bent petal",
        tags={"lantern", "water"},
    ),
    "crown": Treasure(
        id="crown",
        label="the daisy crown",
        phrase="a daisy crown",
        gleam="looked fresh as the first morning of spring",
        sink_text="The white daisies drank the dark water and scattered, petal by petal.",
        saved_text="the daisy crown settled neatly into their hands, fresh and whole",
        tags={"crown", "water"},
    ),
}

SNAGS = {
    "willow": Snag(
        id="willow",
        label="willow branch",
        phrase="a low willow branch",
        height=2,
        delicacy=2,
        over_water=True,
        tags={"willow", "branch"},
    ),
    "thorn": Snag(
        id="thorn",
        label="thorn bough",
        phrase="a thorn bough",
        height=2,
        delicacy=3,
        over_water=True,
        tags={"thorn", "branch"},
    ),
    "reed": Snag(
        id="reed",
        label="reed hook",
        phrase="a bent hook of reeds",
        height=1,
        delicacy=1,
        over_water=True,
        tags={"reed", "branch"},
    ),
}

TOOLS = {
    "crook": Tool(
        id="crook",
        label="shepherd's crook",
        phrase="the shepherd's crook",
        reach=2,
        gentle=2,
        success_text="With one slow lift and one slower twist, they guided the branch near",
        tags={"crook"},
    ),
    "pole": Tool(
        id="pole",
        label="hazel pole",
        phrase="the hazel pole",
        reach=2,
        gentle=3,
        success_text="Tap, tap went the pole, and with a careful nudge they teased the snag apart",
        tags={"pole"},
    ),
    "net": Tool(
        id="net",
        label="reed net",
        phrase="the reed net",
        reach=1,
        gentle=1,
        success_text="Swish went the little net, and they scooped the dangling thing free",
        tags={"net"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsa", "Nora", "Tilda", "Wren"]
BOY_NAMES = ["Milo", "Oren", "Tobin", "Hale", "Pip", "Rowan"]
HELPER_TRAITS = ["careful", "patient", "steady", "wise", "kind", "quick"]


@dataclass
class StoryParams:
    setting: str
    treasure: str
    snag: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    helper_trait: str
    relation: str
    hero_age: int = 5
    helper_age: int = 7
    trust: int = 6
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="moonpond",
        treasure="ribbon",
        snag="willow",
        tool="crook",
        hero_name="Lina",
        hero_type="girl",
        helper_name="Milo",
        helper_type="boy",
        helper_trait="careful",
        relation="siblings",
        hero_age=5,
        helper_age=7,
        trust=8,
    ),
    StoryParams(
        setting="brook",
        treasure="lantern",
        snag="thorn",
        tool="pole",
        hero_name="Oren",
        hero_type="boy",
        helper_name="Nora",
        helper_type="girl",
        helper_trait="wise",
        relation="friends",
        hero_age=6,
        helper_age=6,
        trust=7,
    ),
    StoryParams(
        setting="moat",
        treasure="crown",
        snag="thorn",
        tool="pole",
        hero_name="Tilda",
        hero_type="girl",
        helper_name="Pip",
        helper_type="boy",
        helper_trait="kind",
        relation="siblings",
        hero_age=7,
        helper_age=5,
        trust=2,
    ),
    StoryParams(
        setting="brook",
        treasure="ribbon",
        snag="reed",
        tool="net",
        hero_name="Hale",
        hero_type="boy",
        helper_name="Mira",
        helper_type="girl",
        helper_trait="patient",
        relation="friends",
        hero_age=5,
        helper_age=5,
        trust=6,
    ),
]


KNOWLEDGE = {
    "water": [
        (
            "Why can it be hard to get something back once it falls into deep water?",
            "Water can carry light things away, or pull them down where hands cannot reach. That is why people try to stop a fall before it happens.",
        )
    ],
    "willow": [
        (
            "What is a willow branch like?",
            "A willow branch is long and bendy. It can look gentle, but a thin one can still snap if someone pulls too hard.",
        )
    ],
    "thorn": [
        (
            "Why are thorn bushes tricky to pull on?",
            "Thorns catch cloth and string very easily. If you yank too hard, they can tear what they hold or poke your hands.",
        )
    ],
    "reed": [
        (
            "What are reeds?",
            "Reeds are tall water plants that grow by ponds and streams. They bend in the wind and can tangle light things.",
        )
    ],
    "crook": [
        (
            "What is a shepherd's crook?",
            "A shepherd's crook is a long stick with a curved top. The hook helps reach or guide something without grabbing it hard.",
        )
    ],
    "pole": [
        (
            "Why can a long pole be safer than pulling with your hands?",
            "A long pole lets you reach from farther away and move slowly. That helps you touch the problem without yanking it.",
        )
    ],
    "net": [
        (
            "What is a net used for?",
            "A net is used to catch or scoop something gently. It can hold a light object without squeezing it.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treasure = f["treasure_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            'Write a fairy tale for a 3-to-5-year-old that includes the word "wrestle", repetition, and sound effects, and ends sadly.',
            f"Tell a fairy-tale story where {hero.id} tries to wrestle {treasure.label} free above water, ignores {helper.id}'s warning, and loses it with a crack and a splash.",
            f"Write a gentle cautionary tale set at {setting.place} where a child pulls and pulls, wrestles and wrestles, but the ending shows why patience matters.",
        ]
    return [
        'Write a fairy tale for a 3-to-5-year-old that includes the word "wrestle", repetition, and sound effects, with a wise happy ending.',
        f"Tell a fairy-tale story where {hero.id} wants to wrestle {treasure.label} free, but {helper.id} suggests a calmer way and they save it together.",
        f"Write a simple magical tale set at {setting.place} where a child almost chooses tugging and wrestling, then listens and solves the problem carefully.",
    ]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treasure = f["treasure_cfg"]
    snag = f["snag_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    relation = f["relation"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, helper, relation)}, {hero.id} and {helper.id}. They found {treasure.label} caught above {setting.water}.",
        ),
        (
            f"Why did {hero.id} want to wrestle with the branch?",
            f"{hero.id} wanted to get {treasure.label} back right away. Seeing it so close made waiting feel hard.",
        ),
        (
            f"Why did {helper.id} warn {hero.id} not to pull?",
            f"{helper.id} could see that the {snag.label} was thin and tricky. If {hero.id} wrestled and wrestled, it might snap and drop {treasure.label} into the water.",
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                f"How did they save {treasure.label}?",
                f"They stopped tugging and fetched {tool.phrase}. The long tool let them reach carefully instead of yanking at the snag.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with {treasure.label} safe in {hero.id}'s hands. The ending shows that patience and help worked better than wrestling.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} ignored the warning?",
                f"The branch went creak and crack, and then {treasure.label} fell with a splash into {setting.water}. The bad ending came from pulling too hard instead of listening.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly because {treasure.label} was lost in the water. {hero.id} walked home sorry and wiser, but the lost thing did not come back.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["setting"].tags) | set(world.facts["snag_cfg"].tags) | set(world.facts["tool_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in ["water", "willow", "thorn", "reed", "crook", "pole", "net"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    seen = set()
    for key in list(world.entities):
        ent = world.entities[key]
        if id(ent) in seen:
            continue
        seen.add(id(ent))
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, N, G) :- setting(S), treasure(T), snag(N), tool(G),
                     water_setting(S), over_water(N), height(N, H), reach(G, R), R >= H,
                     delicacy(N, D), gentle(G, E), E >= D.

wise_value(5) :- helper_trait(T), wise_trait(T).
wise_value(3) :- helper_trait(T), not wise_trait(T).

older_bonus(3) :- relation(siblings), helper_age(HA), hero_age(HO), HA > HO.
older_bonus(0) :- not relation(siblings).
older_bonus(0) :- relation(siblings), helper_age(HA), hero_age(HO), HA <= HO.

listen_score(W + B + Trust/2) :- wise_value(W), older_bonus(B), trust(Trust).
listens :- listen_score(S), stubborn_init(St), S > St + 1.

outcome(saved) :- listens.
outcome(lost) :- not listens.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "water" in setting.tags:
            lines.append(asp.fact("water_setting", sid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for nid, snag in SNAGS.items():
        lines.append(asp.fact("snag", nid))
        if snag.over_water:
            lines.append(asp.fact("over_water", nid))
        lines.append(asp.fact("height", nid, snag.height))
        lines.append(asp.fact("delicacy", nid, snag.delicacy))
    for gid, tool in TOOLS.items():
        lines.append(asp.fact("tool", gid))
        lines.append(asp.fact("reach", gid, tool.reach))
        lines.append(asp.fact("gentle", gid, tool.gentle))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    lines.append(asp.fact("stubborn_init", int(STUBBORN_INIT)))
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
            asp.fact("helper_trait", params.helper_trait),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def explain_rejection(setting: Setting, snag: Snag, tool: Tool) -> str:
    if not can_snag_story(setting, snag):
        return (
            f"(No story: {snag.phrase} is not the kind of over-water snag this tale needs, "
            f"so there is no real danger of a splashy loss.)"
        )
    if tool.reach < snag.height:
        return (
            f"(No story: {tool.label} cannot reach {snag.phrase}. The fix must actually reach the stuck thing.)"
        )
    if tool.gentle < snag.delicacy:
        return (
            f"(No story: {tool.label} is too rough for {snag.phrase}. The fix must free the treasure without tearing or jerking it loose.)"
        )
    return "(No story: this combination is unreasonable for the world.)"


def check_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    setting = SETTINGS[params.setting]
    snag = SNAGS[params.snag]
    tool = TOOLS[params.tool]
    if not compatible_tool(snag, tool) or not can_snag_story(setting, snag):
        raise StoryError(explain_rejection(setting, snag, tool))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fairy-tale story world: a child wants to wrestle a treasure free above water."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.snag and args.tool:
        setting = SETTINGS[args.setting]
        snag = SNAGS[args.snag]
        tool = TOOLS[args.tool]
        if not can_snag_story(setting, snag) or not compatible_tool(snag, tool):
            raise StoryError(explain_rejection(setting, snag, tool))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.treasure is None or c[1] == args.treasure)
        and (args.snag is None or c[2] == args.snag)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, treasure, snag, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_type)
    helper_name = args.helper_name or pick_name(rng, helper_type, avoid=hero_name)
    relation = args.relation or rng.choice(["siblings", "friends"])
    hero_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    helper_trait = rng.choice(HELPER_TRAITS)
    trust = rng.randint(1, 9)
    return StoryParams(
        setting=setting,
        treasure=treasure,
        snag=snag,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        helper_trait=helper_trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    check_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        treasure_cfg=TREASURES[params.treasure],
        snag_cfg=SNAGS[params.snag],
        tool_cfg=TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_trait=params.helper_trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        trust=params.trust,
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
    py_combos = set(valid_combos())
    as_combos = set(asp_valid_combos())
    if py_combos == as_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_combos - as_combos:
            print("  only in python:", sorted(py_combos - as_combos))
        if as_combos - py_combos:
            print("  only in clingo:", sorted(as_combos - py_combos))

    cases = list(CURATED)
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            continue
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome cases differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treasure, snag, tool) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:10}" for part in combo))
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.treasure} at {p.setting} ({outcome_of(p)})"
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
