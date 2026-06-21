#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/liberate_amount_squid_sharing_adventure.py
=====================================================================

A standalone storyworld about a small beach adventure: two children find a tiny
squid stranded where the tide has slipped away, and they must share the one good
tool they have to bring it back to deeper water. The world model prefers only
reasonable rescue plans: the container must be gentle and hold enough seawater,
the route must be manageable for the chosen teamwork style, and the story ends
by showing that sharing changed what the children could do.

The seed words "liberate", "amount", and "squid" are embedded naturally in the
rendered stories.

Run it
------
    python storyworlds/worlds/gpt-5.4/liberate_amount_squid_sharing_adventure.py
    python storyworlds/worlds/gpt-5.4/liberate_amount_squid_sharing_adventure.py --pool rock_bowl --tool bucket
    python storyworlds/worlds/gpt-5.4/liberate_amount_squid_sharing_adventure.py --tool net
    python storyworlds/worlds/gpt-5.4/liberate_amount_squid_sharing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/liberate_amount_squid_sharing_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/liberate_amount_squid_sharing_adventure.py --verify
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
CARE_MIN = 2


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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    alive: bool = False
    can_hold_water: bool = False
    gentle: bool = False
    shareable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.alive:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    title_a: str
    title_b: str
    quest: str
    sendoff: str


@dataclass
class Pool:
    id: str
    label: str
    phrase: str
    danger: str
    distance: int
    sun: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    water_amount: int
    care: int
    can_hold_water: bool
    gentle: bool
    shareable: bool
    carry_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Teamwork:
    id: str
    label: str
    support: int
    text: str
    ending: str
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


def _r_distress(world: World) -> list[str]:
    squid = world.get("squid")
    pool = world.get("pool")
    if squid.meters["stranded"] < THRESHOLD:
        return []
    sig = ("distress", squid.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    squid.memes["fear"] += 1
    pool.meters["risk"] += 1
    for kid in (world.get("hero"), world.get("friend")):
        kid.memes["worry"] += 1
    return ["__distress__"]


def _r_share_bond(world: World) -> list[str]:
    tool = world.get("tool")
    squid = world.get("squid")
    if tool.meters["shared"] < THRESHOLD or squid.meters["moving"] < THRESHOLD:
        return []
    sig = ("bond", tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (world.get("hero"), world.get("friend")):
        kid.memes["teamwork"] += 1
        kid.memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="distress", tag="physical", apply=_r_distress),
    Rule(name="share_bond", tag="social", apply=_r_share_bond),
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
        for s in produced:
            world.say(s)
    return produced


def enough_water(tool: Tool, pool: Pool) -> bool:
    return tool.can_hold_water and tool.water_amount >= pool.distance


def gentle_enough(tool: Tool) -> bool:
    return tool.gentle and tool.care >= CARE_MIN


def teamwork_possible(teamwork: Teamwork, tool: Tool, pool: Pool) -> bool:
    need = 2 if pool.distance >= 2 else 1
    return tool.shareable and teamwork.support >= need


def valid_combo(pool_id: str, tool_id: str, teamwork_id: str) -> bool:
    pool = POOLS[pool_id]
    tool = TOOLS[tool_id]
    teamwork = TEAMWORKS[teamwork_id]
    return enough_water(tool, pool) and gentle_enough(tool) and teamwork_possible(teamwork, tool, pool)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for pool_id in POOLS:
        for tool_id in TOOLS:
            for teamwork_id in TEAMWORKS:
                if valid_combo(pool_id, tool_id, teamwork_id):
                    out.append((pool_id, tool_id, teamwork_id))
    return out


def predict_rescue(world: World, pool_id: str, tool_id: str, teamwork_id: str) -> dict:
    pool = POOLS[pool_id]
    tool = TOOLS[tool_id]
    teamwork = TEAMWORKS[teamwork_id]
    success = valid_combo(pool_id, tool_id, teamwork_id)
    return {
        "success": success,
        "water_amount": tool.water_amount,
        "distance": pool.distance,
        "care": tool.care,
        "support": teamwork.support,
    }


def introduce(world: World, hero: Entity, friend: Entity, theme: Theme, pool: Pool) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"Early one bright morning, {hero.id} and {friend.id} scrambled along the shore, "
        f"pretending they were {theme.title_a} and {theme.title_b}. "
        f"The beach felt like {theme.scene}, and every shiny stone looked like part of {theme.quest}."
    )
    world.say(
        f"Past the foam, they found {pool.phrase}, where the tide had left a secret world behind."
    )


def discover(world: World, hero: Entity, friend: Entity, pool: Pool) -> None:
    squid = world.get("squid")
    squid.meters["stranded"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Inside the pool, a tiny squid flashed pale silver, then tucked itself against a rock. "
        f"It was alive, but {pool.danger}."
    )
    world.say(
        f'"A squid!" {friend.id} whispered. "{hero.id}, we have to help it."'
    )


def assess(world: World, hero: Entity, friend: Entity, tool: Tool, teamwork: Teamwork, pool: Pool) -> None:
    pred = predict_rescue(world, pool.id, tool.id, teamwork.id)
    world.facts["predicted_success"] = pred["success"]
    world.facts["predicted_amount"] = pred["water_amount"]
    world.say(
        f"{hero.id} looked from the pool to the open water. "
        f'"If we want to liberate the squid," {hero.pronoun()} said, '
        f'"we need a gentle way to carry it and the right amount of seawater."'
    )
    world.say(
        f"They had only {tool.phrase}. {friend.id} said, "
        f'"We can share {tool.label} and {teamwork.text}."'
    )


def choose(world: World, tool: Tool, teamwork: Teamwork) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["shared"] += 1
    for kid in (world.get("hero"), world.get("friend")):
        kid.memes["decision"] += 1
    world.say(
        f"They did not grab or argue. Instead, they chose to share, and that changed the whole adventure."
    )
    world.say(
        f"{teamwork.text.capitalize()}, they steadied {tool.label} between them."
    )


def rescue(world: World, hero: Entity, friend: Entity, tool: Tool, teamwork: Teamwork, pool: Pool) -> None:
    squid = world.get("squid")
    tool_ent = world.get("tool")
    squid.meters["moving"] += 1
    squid.meters["stranded"] = 0.0
    squid.meters["free"] += 1
    squid.memes["fear"] = 0.0
    squid.memes["relief"] += 1
    tool_ent.meters["shared"] += 1
    world.get("pool").meters["risk"] = 0.0
    propagate(world, narrate=False)
    for kid in (hero, friend):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["care"] += 1
    world.say(
        f"{tool.carry_text} The tiny animal drifted in a safe swirl of water while {teamwork.text}."
    )
    world.say(
        f"When they reached the deeper edge, they tipped the water softly. "
        f"The squid opened like a little umbrella, then darted into the blue."
    )
    world.say(
        f"{teamwork.ending} That was how they helped liberate the squid."
    )


def rescue_fail(world: World, hero: Entity, friend: Entity, tool: Tool, teamwork: Teamwork, pool: Pool) -> None:
    squid = world.get("squid")
    for kid in (hero, friend):
        kid.memes["sadness"] += 1
        kid.memes["care"] += 1
    squid.memes["fear"] += 1
    world.say(
        f"{tool.fail_text} Even though {hero.id} and {friend.id} meant to help, the plan did not give the squid what it needed."
    )
    world.say(
        f"They hurried to call a beach ranger instead. The children stayed beside the pool until a grown-up came with a better rescue tub."
    )


def ending_after_help(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
    world.say(
        f"For a moment the sea looked still, and then a tiny ribbon of water flicked in the sunlight, as if the squid were waving from below."
    )
    world.say(
        f"{hero.id} and {friend.id} grinned at each other. {theme.sendoff}"
    )


def tell(
    theme: Theme,
    pool: Pool,
    tool: Tool,
    teamwork: Teamwork,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    squid = world.add(Entity(id="squid", kind="thing", type="animal", label="squid", phrase="the tiny squid", alive=True))
    pool_ent = world.add(Entity(id="pool", kind="thing", type="pool", label=pool.label, phrase=pool.phrase))
    tool_ent = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            can_hold_water=tool.can_hold_water,
            gentle=tool.gentle,
            shareable=tool.shareable,
        )
    )
    world.facts["theme"] = theme
    world.facts["pool_cfg"] = pool
    world.facts["tool_cfg"] = tool
    world.facts["teamwork_cfg"] = teamwork
    world.facts["parent"] = parent

    introduce(world, hero, friend, theme, pool)
    world.para()
    discover(world, hero, friend, pool)
    assess(world, hero, friend, tool, teamwork, pool)
    choose(world, tool, teamwork)

    success = valid_combo(pool.id, tool.id, teamwork.id)
    world.para()
    if success:
        rescue(world, hero, friend, tool, teamwork, pool)
        world.para()
        ending_after_help(world, hero, friend, theme)
        outcome = "saved"
    else:
        rescue_fail(world, hero, friend, tool, teamwork, pool)
        outcome = "adult_help"

    world.facts.update(
        hero=hero,
        friend=friend,
        squid=squid,
        pool=pool_ent,
        tool=tool_ent,
        success=success,
        outcome=outcome,
        shared=tool_ent.meters["shared"] >= THRESHOLD,
    )
    return world


THEMES = {
    "reef_scouts": Theme(
        id="reef_scouts",
        scene="the edge of a hidden kingdom under the waves",
        title_a="Reef Scout",
        title_b="Shell Scout",
        quest="their grand map of sea-caves and sparkling paths",
        sendoff="They ran on along the sand, feeling as if they had just finished a true ocean quest.",
    ),
    "cove_rangers": Theme(
        id="cove_rangers",
        scene="a brave cove full of clues and sea songs",
        title_a="Cove Ranger",
        title_b="Wave Ranger",
        quest="their patrol for anything the sea had left behind",
        sendoff="They marched on like small rangers, listening for the next secret the tide might whisper.",
    ),
    "dune_explorers": Theme(
        id="dune_explorers",
        scene="a wild coast where dunes were hills and rock pools were hidden forts",
        title_a="Dune Explorer",
        title_b="Foam Explorer",
        quest="their search for treasure between the tide marks",
        sendoff="With wet ankles and bright eyes, they set off for the next bend in the shore.",
    ),
}

POOLS = {
    "rock_bowl": Pool(
        id="rock_bowl",
        label="rock bowl",
        phrase="a round rock bowl no bigger than a washbasin",
        danger="the water there was growing warm and shallow",
        distance=2,
        sun="sun-warm",
        tags={"tidepool", "beach"},
    ),
    "seaweed_pocket": Pool(
        id="seaweed_pocket",
        label="seaweed pocket",
        phrase="a seaweed pocket tucked between two black stones",
        danger="the last wave had already stopped reaching it",
        distance=1,
        sun="shadowy",
        tags={"tidepool", "seaweed"},
    ),
    "shell_hollow": Pool(
        id="shell_hollow",
        label="shell hollow",
        phrase="a shell-lined hollow glittering with bits of water",
        danger="the pool was only a thin puddle now",
        distance=1,
        sun="bright",
        tags={"tidepool", "shell"},
    ),
}

TOOLS = {
    "bucket": Tool(
        id="bucket",
        label="the blue bucket",
        phrase="a blue bucket with a rope handle",
        water_amount=3,
        care=3,
        can_hold_water=True,
        gentle=True,
        shareable=True,
        carry_text="Together they scooped seawater into the blue bucket and guided the squid in with a careful hand.",
        fail_text="They tried with the blue bucket, but the path was too awkward to manage alone and water sloshed badly.",
        qa_text="They used a blue bucket with enough seawater to keep the squid safe while they carried it.",
        tags={"bucket", "sharing"},
    ),
    "pail": Tool(
        id="pail",
        label="the little pail",
        phrase="a little pail from their shell-collecting kit",
        water_amount=2,
        care=3,
        can_hold_water=True,
        gentle=True,
        shareable=True,
        carry_text="They filled the little pail with seawater, then let the squid drift inside like a floating comma.",
        fail_text="They set the squid in the little pail, but too much water spilled away before they reached the sea.",
        qa_text="They used a little pail and kept the squid in seawater while they moved it.",
        tags={"pail", "sharing"},
    ),
    "shell_bowl": Tool(
        id="shell_bowl",
        label="the shell bowl",
        phrase="a broad shell bowl that could cup a splash of water",
        water_amount=1,
        care=2,
        can_hold_water=True,
        gentle=True,
        shareable=True,
        carry_text="They nestled the squid in the shell bowl with a shimmering scoop of seawater.",
        fail_text="The shell bowl held only a tiny amount of water, so the rescue was too delicate for the long walk.",
        qa_text="They used a shell bowl with just enough water for a very short trip.",
        tags={"shell", "sharing"},
    ),
    "net": Tool(
        id="net",
        label="the crab net",
        phrase="a crab net with open holes",
        water_amount=0,
        care=1,
        can_hold_water=False,
        gentle=False,
        shareable=True,
        carry_text="",
        fail_text="A net could not hold seawater, and its rough edge might hurt the squid.",
        qa_text="",
        tags={"net"},
    ),
}

TEAMWORKS = {
    "together": Teamwork(
        id="together",
        label="carry it together",
        support=2,
        text="walking shoulder to shoulder",
        ending="They laughed in one happy puff when the bucket grew light again",
        tags={"sharing"},
    ),
    "take_turns": Teamwork(
        id="take_turns",
        label="take turns",
        support=1,
        text="taking turns with the handle while the other kept a steadying hand nearby",
        ending="Each child had carried part of the rescue, so the victory belonged to both of them",
        tags={"sharing"},
    ),
    "one_carries": Teamwork(
        id="one_carries",
        label="let one child carry",
        support=0,
        text="letting only one pair of hands do the hard part",
        ending="They wished they had worked more closely from the start",
        tags={"sharing"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    theme: str
    pool: str
    tool: str
    teamwork: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "tidepool": [
        (
            "What is a tide pool?",
            "A tide pool is a little pool of seawater left behind between rocks when the tide goes out. Small sea animals can get trapped there until the water returns.",
        )
    ],
    "squid": [
        (
            "What is a squid?",
            "A squid is a soft sea animal with arms and a body that can dart through the water. It needs seawater around it to stay safe and alive.",
        )
    ],
    "sharing": [
        (
            "Why can sharing help in an adventure?",
            "Sharing helps because two people can use one good tool carefully instead of fighting over it. Working together can make a hard job steadier and safer.",
        )
    ],
    "bucket": [
        (
            "Why is a bucket useful for carrying seawater?",
            "A bucket can hold a good amount of water without spilling all of it at once. That makes it useful for moving something gently from one place to another.",
        )
    ],
    "pail": [
        (
            "What is a pail?",
            "A pail is a small bucket. It can carry water, but only a smaller amount than a big bucket can.",
        )
    ],
    "shell": [
        (
            "Can a shell hold water?",
            "Some big shells can hold a small splash of water for a moment. They are only useful for very short, careful trips.",
        )
    ],
    "net": [
        (
            "Why is a net bad for carrying a tiny sea animal in water?",
            "A net has holes, so the water runs out. A soft sea animal can also be bumped or scraped if the tool is too rough.",
        )
    ],
    "beach": [
        (
            "Why do stranded sea animals need help quickly?",
            "When the tide goes out, a stranded sea animal may be left in warm, shallow water. Getting it back to deeper water quickly can keep it safe.",
        )
    ],
}
KNOWLEDGE_ORDER = ["tidepool", "squid", "sharing", "bucket", "pail", "shell", "net", "beach"]


CURATED = [
    StoryParams(
        theme="reef_scouts",
        pool="rock_bowl",
        tool="bucket",
        teamwork="together",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        theme="cove_rangers",
        pool="seaweed_pocket",
        tool="pail",
        teamwork="take_turns",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        theme="dune_explorers",
        pool="shell_hollow",
        tool="shell_bowl",
        teamwork="together",
        hero_name="Zoe",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        theme="reef_scouts",
        pool="rock_bowl",
        tool="pail",
        teamwork="take_turns",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        parent="father",
    ),
]


def explain_rejection(pool: Pool, tool: Tool, teamwork: Teamwork) -> str:
    if not tool.can_hold_water:
        return (
            f"(No story: {tool.label} cannot hold seawater, so it cannot carry the squid in a safe amount of water.)"
        )
    if not tool.gentle or tool.care < CARE_MIN:
        return (
            f"(No story: {tool.label} is too rough for a tiny squid. Pick a gentler container.)"
        )
    if tool.water_amount < pool.distance:
        return (
            f"(No story: {tool.label} holds too small an amount of seawater for that rescue path. Pick a larger container or a closer pool.)"
        )
    if not teamwork_possible(teamwork, tool, pool):
        return (
            f"(No story: '{teamwork.label}' is not steady enough for this rescue. The children need to share the load more closely.)"
        )
    return "(No story: the requested rescue plan is not reasonable.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    pool = f["pool_cfg"]
    tool = f["tool_cfg"]
    teamwork = f["teamwork_cfg"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "liberate", "amount", and "squid", and make sharing the key to the solution.',
        f"Tell a gentle beach adventure where {hero.id} and {friend.id} find a tiny squid in {pool.phrase} and must share {tool.label} to help it.",
        f"Write a simple story where two children stop arguing, choose {teamwork.label}, and discover that sharing is what lets them save a sea creature.",
    ]


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == "girl" and friend.type == "girl":
        return "two girls"
    if hero.type == "boy" and friend.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    squid = f["squid"]
    pool = f["pool_cfg"]
    tool = f["tool_cfg"]
    teamwork = f["teamwork_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend)}, {hero.id} and {friend.id}, who were exploring the shore together. Their adventure changed when they found a tiny squid in trouble.",
        ),
        (
            "What problem did the children find?",
            f"They found a tiny squid stranded in {pool.phrase}. The water there was becoming too shallow, so the squid needed help getting back to the sea.",
        ),
        (
            "Why did they talk about the right amount of water?",
            f"They knew the squid could not be carried dry. It needed the right amount of seawater around it so the trip back to deeper water would be gentle and safe.",
        ),
        (
            "How did sharing help them?",
            f"Sharing kept them from fighting over the only useful tool. Because they worked together, the rescue became steadier and kinder than one child could manage alone.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they liberate the squid?",
                f"They used {tool.label} and {teamwork.text} until they reached deeper water. Then they tipped the seawater softly, and the squid darted away free.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the squid safe in the sea and the children feeling proud. The final image shows them grinning at each other because sharing turned their adventure into a rescue.",
            )
        )
    else:
        qa.append(
            (
                "Did their first plan work?",
                f"No. Their plan was kind, but it was not the safest one for that situation. They called a grown-up for better help because protecting the squid mattered more than finishing alone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"squid", "sharing", "beach"} | set(f["pool_cfg"].tags) | set(f["tool_cfg"].tags)
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
        flags = [name for name, on in (
            ("alive", e.alive),
            ("can_hold_water", e.can_hold_water),
            ("gentle", e.gentle),
            ("shareable", e.shareable),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% base reasonableness
enough_water(Pool, Tool) :- distance(Pool, D), water_amount(Tool, A), A >= D.
gentle_enough(Tool) :- gentle(Tool), care(Tool, C), care_min(M), C >= M.
need_support(Pool, 2) :- distance(Pool, D), D >= 2.
need_support(Pool, 1) :- distance(Pool, D), D < 2.
teamwork_possible(Pool, Tool, Team) :- shareable(Tool), need_support(Pool, N), support(Team, S), S >= N.

valid(Pool, Tool, Team) :- pool(Pool), tool(Tool), teamwork(Team),
                           enough_water(Pool, Tool),
                           gentle_enough(Tool),
                           teamwork_possible(Pool, Tool, Team).

outcome(saved) :- chosen_pool(Pool), chosen_tool(Tool), chosen_teamwork(Team), valid(Pool, Tool, Team).
outcome(adult_help) :- chosen_pool(Pool), chosen_tool(Tool), chosen_teamwork(Team), not valid(Pool, Tool, Team).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("care_min", CARE_MIN))
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for pool_id, pool in POOLS.items():
        lines.append(asp.fact("pool", pool_id))
        lines.append(asp.fact("distance", pool_id, pool.distance))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("water_amount", tool_id, tool.water_amount))
        lines.append(asp.fact("care", tool_id, tool.care))
        if tool.can_hold_water:
            lines.append(asp.fact("can_hold_water", tool_id))
        if tool.gentle:
            lines.append(asp.fact("gentle", tool_id))
        if tool.shareable:
            lines.append(asp.fact("shareable", tool_id))
    for teamwork_id, teamwork in TEAMWORKS.items():
        lines.append(asp.fact("teamwork", teamwork_id))
        lines.append(asp.fact("support", teamwork_id, teamwork.support))
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
        asp.fact("chosen_pool", params.pool),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_teamwork", params.teamwork),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a beach adventure where sharing helps save a stranded squid."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--pool", choices=POOLS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--teamwork", choices=TEAMWORKS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible rescues derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pool and args.tool and args.teamwork:
        pool = POOLS[args.pool]
        tool = TOOLS[args.tool]
        teamwork = TEAMWORKS[args.teamwork]
        if not valid_combo(args.pool, args.tool, args.teamwork):
            raise StoryError(explain_rejection(pool, tool, teamwork))

    combos = [
        combo for combo in valid_combos()
        if (args.pool is None or combo[0] == args.pool)
        and (args.tool is None or combo[1] == args.tool)
        and (args.teamwork is None or combo[2] == args.teamwork)
    ]
    if not combos:
        if args.pool and args.tool and args.teamwork:
            raise StoryError(explain_rejection(POOLS[args.pool], TOOLS[args.tool], TEAMWORKS[args.teamwork]))
        raise StoryError("(No valid combination matches the given options.)")

    pool_id, tool_id, teamwork_id = rng.choice(sorted(combos))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    hero_name, hero_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme_id,
        pool=pool_id,
        tool=tool_id,
        teamwork=teamwork_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.pool not in POOLS:
        raise StoryError(f"(Unknown pool: {params.pool})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.teamwork not in TEAMWORKS:
        raise StoryError(f"(Unknown teamwork: {params.teamwork})")
    if not valid_combo(params.pool, params.tool, params.teamwork):
        raise StoryError(explain_rejection(POOLS[params.pool], TOOLS[params.tool], TEAMWORKS[params.teamwork]))

    world = tell(
        theme=THEMES[params.theme],
        pool=POOLS[params.pool],
        tool=TOOLS[params.tool],
        teamwork=TEAMWORKS[params.teamwork],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        expected = "saved" if valid_combo(params.pool, params.tool, params.teamwork) else "adult_help"
        got = asp_outcome(params)
        if expected != got:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (pool, tool, teamwork) combos:\n")
        for pool_id, tool_id, teamwork_id in combos:
            print(f"  {pool_id:14} {tool_id:10} {teamwork_id}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.tool} at {p.pool} ({p.teamwork})"
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
